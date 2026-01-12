import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

// Question patterns to identify rating types
const QUESTION_PATTERNS = {
  overall: 'overall rating of the course',
  teaching: 'overall rating of the instruction',
  learning: 'how much you learned',
  challenge: 'challenging you intellectually',
  stimulating: 'stimulating your interest',
  hours: 'average number of hours per week',
};

interface RatingDistributionOption {
  numeric_value: number | null;
  label: string | null;
  ordinal: number;
}

interface RatingDistributionItem {
  count: number;
  option: RatingDistributionOption | null;
}

interface OfferingRatings {
  overall: number | null;
  teaching: number | null;
  hours: string | null;
}

// Calculate weighted average from distribution
function calculateWeightedAverage(distribution: RatingDistributionItem[]): number | null {
  let totalCount = 0;
  let weightedSum = 0;

  for (const d of distribution) {
    if (d.option?.numeric_value) {
      totalCount += d.count;
      weightedSum += d.count * d.option.numeric_value;
    }
  }

  return totalCount > 0 ? Math.round((weightedSum / totalCount) * 100) / 100 : null;
}

// Find the mode (most common label) from distribution
function calculateMode(distribution: RatingDistributionItem[]): string | null {
  let maxCount = 0;
  let maxLabel: string | null = null;

  for (const d of distribution) {
    if (d.count > maxCount && d.option?.label) {
      maxCount = d.count;
      maxLabel = d.option.label;
    }
  }

  return maxLabel;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // Get instructor details
  const { data: instructor, error: instructorError } = await supabase
    .from('instructors')
    .select('id, name, profile_photo')
    .eq('id', id)
    .single();

  if (instructorError) {
    if (instructorError.code === 'PGRST116') {
      return NextResponse.json({ error: 'Instructor not found' }, { status: 404 });
    }
    return NextResponse.json({ error: instructorError.message }, { status: 500 });
  }

  // Get all course offerings for this instructor
  const { data: offerings, error: offeringsError } = await supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      audience_size,
      response_count,
      course:courses(id, code, title)
    `)
    .eq('instructor_id', id)
    .order('year', { ascending: false })
    .order('quarter', { ascending: false });

  if (offeringsError) {
    return NextResponse.json({ error: offeringsError.message }, { status: 500 });
  }

  // Get AI summary if available
  const { data: aiSummary } = await supabase
    .from('ai_summaries')
    .select('summary')
    .eq('entity_type', 'instructor')
    .eq('entity_id', id)
    .eq('summary_type', 'default')
    .single();

  // If no offerings, return early with empty ratings
  if (!offerings || offerings.length === 0) {
    return NextResponse.json({
      data: {
        ...instructor,
        offerings: [],
        aggregatedRatings: [],
        aiSummary: aiSummary?.summary || null
      }
    });
  }

  // Get all offering IDs
  const offeringIds = offerings.map(o => o.id);

  // Fetch ratings for all offerings
  const { data: ratings, error: ratingsError } = await supabase
    .from('ratings')
    .select(`
      id,
      course_offering_id,
      survey_question:survey_questions!inner(
        id,
        question
      ),
      ratings_distribution(
        count,
        option:survey_question_options!inner(
          numeric_value,
          label,
          ordinal
        )
      )
    `)
    .in('course_offering_id', offeringIds);

  if (ratingsError) {
    return NextResponse.json({ error: ratingsError.message }, { status: 500 });
  }

  // Process ratings: per-offering and aggregated
  const offeringRatingsMap: Record<string, OfferingRatings> = {};

  // For aggregated ratings: accumulate distributions by question pattern
  const aggregatedDistributions: Record<string, RatingDistributionItem[]> = {
    overall: [],
    teaching: [],
    learning: [],
    challenge: [],
    stimulating: [],
    hours: [],
  };

  for (const rating of ratings || []) {
    const offeringId = rating.course_offering_id;
    const question = (rating.survey_question as unknown as { question: string })?.question?.toLowerCase() || '';
    const distribution = (rating.ratings_distribution || []) as unknown as RatingDistributionItem[];

    // Initialize offering ratings if needed
    if (!offeringRatingsMap[offeringId]) {
      offeringRatingsMap[offeringId] = { overall: null, teaching: null, hours: null };
    }

    // Identify question type and process
    if (question.includes(QUESTION_PATTERNS.overall)) {
      offeringRatingsMap[offeringId].overall = calculateWeightedAverage(distribution);
      aggregatedDistributions.overall.push(...distribution);
    } else if (question.includes(QUESTION_PATTERNS.teaching)) {
      offeringRatingsMap[offeringId].teaching = calculateWeightedAverage(distribution);
      aggregatedDistributions.teaching.push(...distribution);
    } else if (question.includes(QUESTION_PATTERNS.hours)) {
      offeringRatingsMap[offeringId].hours = calculateMode(distribution);
      aggregatedDistributions.hours.push(...distribution);
    } else if (question.includes(QUESTION_PATTERNS.learning)) {
      aggregatedDistributions.learning.push(...distribution);
    } else if (question.includes(QUESTION_PATTERNS.challenge)) {
      aggregatedDistributions.challenge.push(...distribution);
    } else if (question.includes(QUESTION_PATTERNS.stimulating)) {
      aggregatedDistributions.stimulating.push(...distribution);
    }
  }

  // Calculate aggregated ratings from combined distributions
  const aggregatedRatings = [
    {
      id: 'agg-teaching',
      surveyQuestion: { id: 'q-teaching', question: 'Provide an overall rating of the instruction' },
      distribution: [],
      mean: calculateWeightedAverage(aggregatedDistributions.teaching) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-overall',
      surveyQuestion: { id: 'q-overall', question: 'Provide an overall rating of the course' },
      distribution: [],
      mean: calculateWeightedAverage(aggregatedDistributions.overall) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-learning',
      surveyQuestion: { id: 'q-learning', question: 'Estimate how much you learned in the course' },
      distribution: [],
      mean: calculateWeightedAverage(aggregatedDistributions.learning) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-challenge',
      surveyQuestion: { id: 'q-challenge', question: 'Rate the effectiveness of the course in challenging you intellectually' },
      distribution: [],
      mean: calculateWeightedAverage(aggregatedDistributions.challenge) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-stimulating',
      surveyQuestion: { id: 'q-stimulating', question: 'Rate the effectiveness of the instructor in stimulating your interest in the subject' },
      distribution: [],
      mean: calculateWeightedAverage(aggregatedDistributions.stimulating) || 0,
      responseCount: 0,
    },
    {
      id: 'agg-hours',
      surveyQuestion: { id: 'q-hours', question: 'Estimate the average number of hours per week you spent on this course outside of class and lab time' },
      distribution: calculateAggregatedHoursDistribution(aggregatedDistributions.hours),
      mean: 0,
      responseCount: 0,
    },
  ];

  // Build offerings with ratings for CourseCard
  const offeringsWithRatings = offerings.map(offering => {
    const course = offering.course as unknown as { id: string; code: string; title: string };
    const ratings = offeringRatingsMap[offering.id] || { overall: null, teaching: null, hours: null };

    return {
      id: offering.id,
      courseCode: course.code,
      courseName: course.title,
      courseId: course.id,
      quarter: offering.quarter,
      year: offering.year,
      section: offering.section,
      overallRating: ratings.overall,
      teachingRating: ratings.teaching,
      hoursPerWeek: ratings.hours,
    };
  });

  return NextResponse.json({
    data: {
      ...instructor,
      offerings: offeringsWithRatings,
      aggregatedRatings,
      aiSummary: aiSummary?.summary || null
    }
  });
}

// Aggregate hours distribution and calculate mode with proper percentage for RatingSummary
function calculateAggregatedHoursDistribution(distributions: RatingDistributionItem[]) {
  // Group by label and sum counts
  const labelCounts: Record<string, { count: number; ordinal: number }> = {};

  for (const d of distributions) {
    if (d.option?.label) {
      const label = d.option.label;
      if (!labelCounts[label]) {
        labelCounts[label] = { count: 0, ordinal: d.option.ordinal };
      }
      labelCounts[label].count += d.count;
    }
  }

  // Convert to distribution format sorted by ordinal
  const totalCount = Object.values(labelCounts).reduce((sum, lc) => sum + lc.count, 0);

  return Object.entries(labelCounts)
    .sort((a, b) => a[1].ordinal - b[1].ordinal)
    .map(([label, data]) => ({
      ratingValue: 0,
      label,
      count: data.count,
      percentage: totalCount > 0 ? (data.count / totalCount) * 100 : 0,
    }));
}
