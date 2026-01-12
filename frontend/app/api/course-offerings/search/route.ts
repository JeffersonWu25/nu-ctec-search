import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

// Question patterns to identify rating types
const QUESTION_PATTERNS = {
  overall: 'overall rating of the course',
  teaching: 'overall rating of the instruction',
  hours: 'average number of hours per week',
};

interface CourseOfferingResult {
  id: string;
  courseCode: string;
  courseName: string;
  instructor: string;
  instructorId: string;
  quarter: string;
  year: number;
  overallRating: number | null;
  teachingRating: number | null;
  hoursPerWeek: string | null;
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  // Filter params (comma-separated IDs for multiple selections)
  const departmentIds = searchParams.get('departmentIds')?.split(',').filter(Boolean) || [];
  const courseIds = searchParams.get('courseIds')?.split(',').filter(Boolean) || [];
  const instructorIds = searchParams.get('instructorIds')?.split(',').filter(Boolean) || [];
  const requirementIds = searchParams.get('requirementIds')?.split(',').filter(Boolean) || [];

  // Sorting
  const sortBy = searchParams.get('sortBy') || 'recency';
  const sortOrder = searchParams.get('sortOrder') || 'desc';

  // Pagination
  const limit = parseInt(searchParams.get('limit') || '20');
  const offset = parseInt(searchParams.get('offset') || '0');

  // Check if any filters are applied
  const hasFilters = departmentIds.length > 0 || courseIds.length > 0 ||
                     instructorIds.length > 0 || requirementIds.length > 0;

  if (!hasFilters) {
    return NextResponse.json({ data: [], count: 0, limit, offset });
  }

  try {
    // Build the query for course offerings
    let query = supabase
      .from('course_offerings')
      .select(`
        id,
        quarter,
        year,
        section,
        course:courses!inner(
          id,
          code,
          title,
          department_id
        ),
        instructor:instructors!inner(
          id,
          name
        )
      `, { count: 'exact' });

    // Apply AND filters
    if (courseIds.length > 0) {
      query = query.in('course_id', courseIds);
    }

    if (instructorIds.length > 0) {
      query = query.in('instructor_id', instructorIds);
    }

    if (departmentIds.length > 0) {
      query = query.in('course.department_id', departmentIds);
    }

    // For requirements, we need to filter offerings whose course has the requirement
    if (requirementIds.length > 0) {
      // Get course IDs that have the required requirements
      const { data: courseReqs } = await supabase
        .from('course_requirements')
        .select('course_id')
        .in('requirement_id', requirementIds);

      if (courseReqs && courseReqs.length > 0) {
        const reqCourseIds = [...new Set(courseReqs.map(cr => cr.course_id))];
        query = query.in('course_id', reqCourseIds);
      } else {
        // No courses match the requirements
        return NextResponse.json({ data: [], count: 0, limit, offset });
      }
    }

    // Execute the query to get offerings
    const { data: offerings, error: offeringsError } = await query;

    if (offeringsError) {
      return NextResponse.json({ error: offeringsError.message }, { status: 500 });
    }

    if (!offerings || offerings.length === 0) {
      return NextResponse.json({ data: [], count: 0, limit, offset });
    }

    // Get all offering IDs
    const offeringIds = offerings.map(o => o.id);

    // Fetch ratings for these offerings with their questions
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
            min_value,
            max_value
          )
        )
      `)
      .in('course_offering_id', offeringIds);

    if (ratingsError) {
      return NextResponse.json({ error: ratingsError.message }, { status: 500 });
    }

    // Calculate averages for each offering
    const offeringRatings: Record<string, {
      overall: number | null;
      teaching: number | null;
      hours: string | null;
    }> = {};

    for (const rating of ratings || []) {
      const offeringId = rating.course_offering_id;
      const question = (rating.survey_question as unknown as { question: string })?.question?.toLowerCase() || '';

      if (!offeringRatings[offeringId]) {
        offeringRatings[offeringId] = { overall: null, teaching: null, hours: null };
      }

      const distribution = rating.ratings_distribution || [];

      // Calculate weighted average for Likert ratings
      if (question.includes(QUESTION_PATTERNS.overall) || question.includes(QUESTION_PATTERNS.teaching)) {
        let totalCount = 0;
        let weightedSum = 0;

        for (const d of distribution) {
          const opt = d.option as unknown as { numeric_value: number | null } | null;
          if (opt?.numeric_value) {
            totalCount += d.count;
            weightedSum += d.count * opt.numeric_value;
          }
        }

        const avg = totalCount > 0 ? Math.round((weightedSum / totalCount) * 100) / 100 : null;

        if (question.includes(QUESTION_PATTERNS.overall)) {
          offeringRatings[offeringId].overall = avg;
        } else if (question.includes(QUESTION_PATTERNS.teaching)) {
          offeringRatings[offeringId].teaching = avg;
        }
      }

      // Calculate hours range (find the bin with highest count)
      if (question.includes(QUESTION_PATTERNS.hours)) {
        let maxCount = 0;
        let maxLabel = null;

        for (const d of distribution) {
          const opt = d.option as unknown as { label: string } | null;
          if (d.count > maxCount && opt?.label) {
            maxCount = d.count;
            maxLabel = opt.label;
          }
        }

        offeringRatings[offeringId].hours = maxLabel;
      }
    }

    // Build result array with ratings
    const results: CourseOfferingResult[] = offerings.map(offering => {
      const course = offering.course as unknown as { id: string; code: string; title: string };
      const instructor = offering.instructor as unknown as { id: string; name: string };
      const ratings = offeringRatings[offering.id] || { overall: null, teaching: null, hours: null };

      return {
        id: offering.id,
        courseCode: course.code,
        courseName: course.title,
        instructor: instructor.name,
        instructorId: instructor.id,
        quarter: offering.quarter,
        year: offering.year,
        overallRating: ratings.overall,
        teachingRating: ratings.teaching,
        hoursPerWeek: ratings.hours,
      };
    });

    // Sort results
    results.sort((a, b) => {
      const asc = sortOrder === 'asc';

      switch (sortBy) {
        case 'overall':
          const aOverall = a.overallRating ?? (asc ? Infinity : -Infinity);
          const bOverall = b.overallRating ?? (asc ? Infinity : -Infinity);
          return asc ? aOverall - bOverall : bOverall - aOverall;

        case 'teaching':
          const aTeaching = a.teachingRating ?? (asc ? Infinity : -Infinity);
          const bTeaching = b.teachingRating ?? (asc ? Infinity : -Infinity);
          return asc ? aTeaching - bTeaching : bTeaching - aTeaching;

        case 'ease':
          // For ease, we parse the hours label and sort by it
          // Lower hours = easier, so ascending = easiest first
          const parseHours = (h: string | null): number => {
            if (!h) return asc ? Infinity : -Infinity;
            // Handle formats like "3 or fewer", "4 - 7", "8 - 11", etc.
            const match = h.match(/(\d+)/);
            return match ? parseInt(match[1]) : (asc ? Infinity : -Infinity);
          };
          const aHours = parseHours(a.hoursPerWeek);
          const bHours = parseHours(b.hoursPerWeek);
          return asc ? aHours - bHours : bHours - aHours;

        case 'recency':
        default:
          // Sort by year desc, then quarter (Fall > Summer > Spring > Winter for same year)
          const quarterOrder: Record<string, number> = { 'Fall': 4, 'Summer': 3, 'Spring': 2, 'Winter': 1 };
          if (a.year !== b.year) {
            return asc ? a.year - b.year : b.year - a.year;
          }
          const aQ = quarterOrder[a.quarter] || 0;
          const bQ = quarterOrder[b.quarter] || 0;
          return asc ? aQ - bQ : bQ - aQ;
      }
    });

    // Apply pagination after sorting
    const paginatedResults = results.slice(offset, offset + limit);

    return NextResponse.json({
      data: paginatedResults,
      count: results.length,
      limit,
      offset,
    });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'Internal server error' },
      { status: 500 }
    );
  }
}
