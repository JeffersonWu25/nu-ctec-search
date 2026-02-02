/**
 * Business logic for course offering pages.
 * - getOfferingDetail: single offering detail page
 * - searchOfferings: filtered/sorted offering search
 */

import * as offeringRepo from '@/app/lib/repositories/offeringRepo';
import * as ratingRepo from '@/app/lib/repositories/ratingRepo';
import * as commentRepo from '@/app/lib/repositories/commentRepo';
import * as aiSummaryRepo from '@/app/lib/repositories/aiSummaryRepo';
import * as requirementRepo from '@/app/lib/repositories/requirementRepo';
import { handleSupabaseError } from '@/app/lib/errors';
import {
  createEmptyOfferingRatings,
  processOfferingsRatings,
} from '@/app/lib/ratings';
import type { RatingRecord } from '@/app/lib/ratings';

// --- Types ---

interface DetailRatingDistributionItem {
  count: number;
  option: {
    id: string;
    label: string;
    ordinal: number;
    numeric_value: number | null;
  } | null;
}

export interface CourseOfferingResult {
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

export interface SearchOfferingsParams {
  departmentIds: string[];
  courseIds: string[];
  instructorIds: string[];
  requirementIds: string[];
  sortBy: string;
  sortOrder: string;
  limit: number;
  offset: number;
}

// --- Detail ---

export async function getOfferingDetail(id: string) {
  // Fetch offering with nested relations
  const { data: offering, error: offeringError } = await offeringRepo.getById(id);
  if (offeringError) handleSupabaseError(offeringError, 'Course offering');

  // Fetch ratings
  const { data: ratings, error: ratingsError } = await ratingRepo.getByOfferingId(id);
  if (ratingsError) handleSupabaseError(ratingsError);

  // Fetch comments
  const { data: comments, error: commentsError } = await commentRepo.getByOfferingId(id);
  if (commentsError) handleSupabaseError(commentsError);

  // Fetch AI summary (optional — ignore errors)
  const { data: aiSummary } = await aiSummaryRepo.getByEntity('course_offering', id);

  // Transform ratings to frontend format
  const transformedRatings = ratings?.map(rating => {
    const distribution = (rating.ratings_distribution || []) as unknown as DetailRatingDistributionItem[];
    const totalCount = distribution.reduce((sum, d) => sum + d.count, 0);

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
          percentage: totalCount > 0 ? (d.count / totalCount) * 100 : 0,
        })),
      mean: Math.round(mean * 100) / 100,
      responseCount: totalCount,
    };
  });

  // Extract nested Supabase relations
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

  return {
    id: offering.id,
    course: {
      id: course.id,
      code: course.code,
      title: course.title,
      description: course.description,
      prerequisitesText: course.prerequisites_text,
      department: course.department,
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
    aiSummary: aiSummary?.summary || null,
  };
}

// --- Search ---

export async function searchOfferings(params: SearchOfferingsParams) {
  const { departmentIds, courseIds, instructorIds, requirementIds, sortBy, sortOrder, limit, offset } = params;

  // Check if any filters are applied
  const hasFilters = departmentIds.length > 0 || courseIds.length > 0 ||
                     instructorIds.length > 0 || requirementIds.length > 0;

  if (!hasFilters) {
    return { data: [], count: 0, limit, offset };
  }

  // Requirement filtering (OR semantics — course matches if it has ANY selected requirement)
  let requirementCourseIds: string[] | undefined;
  if (requirementIds.length > 0) {
    const { data: courseReqs } = await requirementRepo.getCourseIdsByRequirements(requirementIds);

    if (courseReqs && courseReqs.length > 0) {
      requirementCourseIds = [...new Set(courseReqs.map(cr => cr.course_id))];
    } else {
      return { data: [], count: 0, limit, offset };
    }
  }

  // Fetch offerings matching filters
  const { data: offerings, error: offeringsError } = await offeringRepo.search({
    courseIds: courseIds.length > 0 ? courseIds : undefined,
    instructorIds: instructorIds.length > 0 ? instructorIds : undefined,
    departmentIds: departmentIds.length > 0 ? departmentIds : undefined,
    requirementCourseIds,
  });

  if (offeringsError) handleSupabaseError(offeringsError);

  if (!offerings || offerings.length === 0) {
    return { data: [], count: 0, limit, offset };
  }

  // Fetch ratings for all offerings
  const offeringIds = offerings.map(o => o.id);
  const { data: ratings, error: ratingsError } = await ratingRepo.getByOfferingIdsForSearch(offeringIds);
  if (ratingsError) handleSupabaseError(ratingsError);

  // Process ratings using shared utility (replaces inline duplicate)
  const ratingRecords: RatingRecord[] = (ratings || []).map(r => ({
    course_offering_id: r.course_offering_id,
    survey_question: r.survey_question as unknown as { question: string },
    ratings_distribution: r.ratings_distribution as unknown as RatingRecord['ratings_distribution'],
  }));

  const { offeringRatingsMap } = processOfferingsRatings(ratingRecords);

  // Build result array
  const results: CourseOfferingResult[] = offerings.map(offering => {
    const course = offering.course as unknown as { id: string; code: string; title: string };
    const instructor = offering.instructor as unknown as { id: string; name: string };
    const offeringRatings = offeringRatingsMap[offering.id] || createEmptyOfferingRatings();

    return {
      id: offering.id,
      courseCode: course.code,
      courseName: course.title,
      instructor: instructor.name,
      instructorId: instructor.id,
      quarter: offering.quarter,
      year: offering.year,
      overallRating: offeringRatings.overall,
      teachingRating: offeringRatings.teaching,
      hoursPerWeek: offeringRatings.hours,
    };
  });

  // Sort results
  sortResults(results, sortBy, sortOrder);

  // Paginate
  const paginatedResults = results.slice(offset, offset + limit);

  return {
    data: paginatedResults,
    count: results.length,
    limit,
    offset,
  };
}

/** Sort search results in-place by the given criteria. */
function sortResults(results: CourseOfferingResult[], sortBy: string, sortOrder: string): void {
  const asc = sortOrder === 'asc';

  results.sort((a, b) => {
    switch (sortBy) {
      case 'overall': {
        const aVal = a.overallRating ?? (asc ? Infinity : -Infinity);
        const bVal = b.overallRating ?? (asc ? Infinity : -Infinity);
        return asc ? aVal - bVal : bVal - aVal;
      }

      case 'teaching': {
        const aVal = a.teachingRating ?? (asc ? Infinity : -Infinity);
        const bVal = b.teachingRating ?? (asc ? Infinity : -Infinity);
        return asc ? aVal - bVal : bVal - aVal;
      }

      case 'ease': {
        const parseHours = (h: string | null): number => {
          if (!h) return asc ? Infinity : -Infinity;
          const match = h.match(/(\d+)/);
          return match ? parseInt(match[1]) : (asc ? Infinity : -Infinity);
        };
        const aVal = parseHours(a.hoursPerWeek);
        const bVal = parseHours(b.hoursPerWeek);
        return asc ? aVal - bVal : bVal - aVal;
      }

      case 'recency':
      default: {
        const quarterOrder: Record<string, number> = { 'Fall': 4, 'Summer': 3, 'Spring': 2, 'Winter': 1 };
        if (a.year !== b.year) {
          return asc ? a.year - b.year : b.year - a.year;
        }
        const aQ = quarterOrder[a.quarter] || 0;
        const bQ = quarterOrder[b.quarter] || 0;
        return asc ? aQ - bQ : bQ - aQ;
      }
    }
  });
}
