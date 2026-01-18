import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';
import {
  RatingDistributionItem,
  createEmptyAggregatedDistributions,
  createEmptyOfferingRatings,
  processRating,
  buildAggregatedRatings,
} from '@/app/lib/ratings';
import type {
  OfferingWithCourse,
  RatingQueryResult,
} from '@/app/types/api';

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

  const typedOfferings = (offerings || []) as unknown as OfferingWithCourse[];

  // Get AI summary if available
  const { data: aiSummary } = await supabase
    .from('ai_summaries')
    .select('summary')
    .eq('entity_type', 'instructor')
    .eq('entity_id', id)
    .eq('summary_type', 'default')
    .single();

  // If no offerings, return early with empty ratings
  if (typedOfferings.length === 0) {
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
  const offeringIds = typedOfferings.map(o => o.id);

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

  const typedRatings = (ratings || []) as unknown as RatingQueryResult[];

  // Process ratings: per-offering and aggregated
  const offeringRatingsMap: Record<string, ReturnType<typeof createEmptyOfferingRatings>> = {};
  const aggregatedDistributions = createEmptyAggregatedDistributions();

  for (const rating of typedRatings) {
    const offeringId = rating.course_offering_id;
    const question = rating.survey_question?.question || '';
    const distribution = (rating.ratings_distribution || []) as unknown as RatingDistributionItem[];

    // Initialize offering ratings if needed
    if (!offeringRatingsMap[offeringId]) {
      offeringRatingsMap[offeringId] = createEmptyOfferingRatings();
    }

    processRating(question, distribution, offeringRatingsMap[offeringId], aggregatedDistributions);
  }

  // Build aggregated ratings from combined distributions
  const aggregatedRatings = buildAggregatedRatings(aggregatedDistributions);

  // Build offerings with ratings
  const offeringsWithRatings = typedOfferings.map(offering => {
    const course = offering.course;
    const offeringRatings = offeringRatingsMap[offering.id] || createEmptyOfferingRatings();

    return {
      id: offering.id,
      courseCode: course.code,
      courseName: course.title,
      courseId: course.id,
      quarter: offering.quarter,
      year: offering.year,
      section: offering.section,
      overallRating: offeringRatings.overall,
      teachingRating: offeringRatings.teaching,
      hoursPerWeek: offeringRatings.hours,
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
