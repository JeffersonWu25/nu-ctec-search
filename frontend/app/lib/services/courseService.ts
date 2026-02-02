/**
 * Business logic for course detail pages.
 * Orchestrates: course + offerings + ratings + AI summary.
 */

import * as courseRepo from '@/app/lib/repositories/courseRepo';
import * as offeringRepo from '@/app/lib/repositories/offeringRepo';
import * as ratingRepo from '@/app/lib/repositories/ratingRepo';
import * as aiSummaryRepo from '@/app/lib/repositories/aiSummaryRepo';
import { handleSupabaseError } from '@/app/lib/errors';
import {
  createEmptyOfferingRatings,
  processOfferingsRatings,
} from '@/app/lib/ratings';
import type { RatingRecord } from '@/app/lib/ratings';
import type {
  CourseDetailQueryResult,
  CourseRequirementJoin,
  CourseDetailResponse,
  OfferingWithInstructor,
  RatingQueryResult,
  InstructorRow,
} from '@/app/types/api';

export async function getCourseDetail(id: string): Promise<CourseDetailResponse> {
  // Fetch course with department and requirements
  const { data: course, error: courseError } = await courseRepo.getById(id);
  if (courseError) handleSupabaseError(courseError, 'Course');

  const typedCourse = course as unknown as CourseDetailQueryResult;

  // Fetch offerings for this course
  const { data: offerings, error: offeringsError } = await offeringRepo.getByCourseId(id);
  if (offeringsError) handleSupabaseError(offeringsError);

  const typedOfferings = (offerings || []) as unknown as OfferingWithInstructor[];

  // Fetch AI summary (optional — ignore errors)
  const { data: aiSummary } = await aiSummaryRepo.getByEntity('course', id);

  // Extract requirements from nested join structure
  const requirements = typedCourse.course_requirements
    ?.map((cr: CourseRequirementJoin) => cr.requirement) || [];

  // Early return if no offerings
  if (typedOfferings.length === 0) {
    return {
      id: typedCourse.id,
      code: typedCourse.code,
      title: typedCourse.title,
      description: typedCourse.description,
      prerequisitesText: typedCourse.prerequisites_text,
      department: typedCourse.department,
      requirements,
      offerings: [],
      aggregatedRatings: [],
      aiSummary: aiSummary?.summary || null,
    };
  }

  // Fetch ratings for all offerings
  const offeringIds = typedOfferings.map(o => o.id);
  const { data: ratings, error: ratingsError } = await ratingRepo.getByOfferingIds(offeringIds);
  if (ratingsError) handleSupabaseError(ratingsError);

  const typedRatings = (ratings || []) as unknown as RatingQueryResult[];

  // Process ratings: per-offering and aggregated
  const ratingRecords: RatingRecord[] = typedRatings.map(r => ({
    course_offering_id: r.course_offering_id,
    survey_question: r.survey_question,
    ratings_distribution: r.ratings_distribution,
  }));

  const { offeringRatingsMap, aggregatedRatings } = processOfferingsRatings(ratingRecords);

  // Build offerings with per-offering ratings
  const offeringsWithRatings = typedOfferings.map(offering => {
    const instructor = offering.instructor as InstructorRow;
    const offeringRatings = offeringRatingsMap[offering.id] || createEmptyOfferingRatings();

    return {
      id: offering.id,
      quarter: offering.quarter,
      year: offering.year,
      section: offering.section,
      instructorId: instructor.id,
      instructorName: instructor.name,
      overallRating: offeringRatings.overall,
      teachingRating: offeringRatings.teaching,
      hoursPerWeek: offeringRatings.hours,
    };
  });

  return {
    id: typedCourse.id,
    code: typedCourse.code,
    title: typedCourse.title,
    description: typedCourse.description,
    prerequisitesText: typedCourse.prerequisites_text,
    department: typedCourse.department,
    requirements,
    offerings: offeringsWithRatings,
    aggregatedRatings,
    aiSummary: aiSummary?.summary || null,
  };
}
