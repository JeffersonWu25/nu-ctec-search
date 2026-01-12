import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

interface RatingDistributionItem {
  count: number;
  option: {
    id: string;
    label: string;
    ordinal: number;
    numeric_value: number | null;
  } | null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  // Fetch the course offering with nested relations
  const { data: offering, error: offeringError } = await supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      audience_size,
      response_count,
      course:courses!inner(
        id,
        code,
        title,
        description,
        prerequisites_text,
        department:departments(id, code, name),
        course_requirements(
          requirement:requirements(id, name)
        )
      ),
      instructor:instructors!inner(id, name, profile_photo)
    `)
    .eq('id', id)
    .single();

  if (offeringError) {
    if (offeringError.code === 'PGRST116') {
      return NextResponse.json({ error: 'Course offering not found' }, { status: 404 });
    }
    return NextResponse.json({ error: offeringError.message }, { status: 500 });
  }

  // Fetch ratings with distribution
  const { data: ratings, error: ratingsError } = await supabase
    .from('ratings')
    .select(`
      id,
      survey_question:survey_questions!inner(id, question),
      ratings_distribution(
        count,
        option:survey_question_options!inner(
          id,
          label,
          ordinal,
          numeric_value
        )
      )
    `)
    .eq('course_offering_id', id);

  if (ratingsError) {
    return NextResponse.json({ error: ratingsError.message }, { status: 500 });
  }

  // Fetch comments
  const { data: comments, error: commentsError } = await supabase
    .from('comments')
    .select('id, content')
    .eq('course_offering_id', id);

  if (commentsError) {
    return NextResponse.json({ error: commentsError.message }, { status: 500 });
  }

  // Fetch AI summary if available
  const { data: aiSummary } = await supabase
    .from('ai_summaries')
    .select('summary')
    .eq('entity_type', 'course_offering')
    .eq('entity_id', id)
    .eq('summary_type', 'default')
    .single();

  // Transform ratings to match frontend format
  const transformedRatings = ratings?.map(rating => {
    const distribution = (rating.ratings_distribution || []) as unknown as RatingDistributionItem[];
    const totalCount = distribution.reduce((sum, d) => sum + d.count, 0);

    // Calculate mean from distribution
    let weightedSum = 0;
    distribution.forEach((d) => {
      if (d.option?.numeric_value) {
        weightedSum += d.count * d.option.numeric_value;
      }
    });
    const mean = totalCount > 0 ? weightedSum / totalCount : 0;

    return {
      id: rating.id,
      surveyQuestion: rating.survey_question,
      distribution: distribution
        .sort((a, b) => (a.option?.ordinal || 0) - (b.option?.ordinal || 0))
        .map((d) => ({
          ratingValue: d.option?.numeric_value || 0,
          label: d.option?.label || '',
          count: d.count,
          percentage: totalCount > 0 ? (d.count / totalCount) * 100 : 0
        })),
      mean: Math.round(mean * 100) / 100,
      responseCount: totalCount
    };
  });

  // Extract data - Supabase returns single relations as objects when using !inner
  const course = offering.course as unknown as {
    id: string;
    code: string;
    title: string;
    description: string | null;
    prerequisites_text: string | null;
    department: { id: string; code: string; name: string } | null;
    course_requirements: { requirement: { id: string; name: string } }[];
  };

  const instructor = offering.instructor as unknown as {
    id: string;
    name: string;
    profile_photo: string | null;
  };

  const requirements = course.course_requirements?.map(cr => cr.requirement) || [];

  const response = {
    id: offering.id,
    course: {
      id: course.id,
      code: course.code,
      title: course.title,
      description: course.description,
      prerequisitesText: course.prerequisites_text,
      department: course.department
    },
    instructor,
    quarter: offering.quarter,
    year: offering.year,
    section: offering.section,
    audienceSize: offering.audience_size,
    responseCount: offering.response_count,
    ratings: transformedRatings,
    comments: comments || [],
    requirements,
    aiSummary: aiSummary?.summary || null
  };

  return NextResponse.json({ data: response });
}
