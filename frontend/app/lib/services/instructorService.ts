/**
 * Business logic for instructor detail pages.
 * Orchestrates: instructor + offerings + ratings + AI summary.
 */

import * as instructorRepo from '@/app/lib/repositories/instructorRepo';
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
  InstructorDetailResponse,
  OfferingWithCourse,
  RatingQueryResult,
} from '@/app/types/api';

export async function getInstructorDetail(id: string): Promise<InstructorDetailResponse> {
  // Fetch instructor
  const { data: instructor, error: instructorError } = await instructorRepo.getById(id);
  if (instructorError) handleSupabaseError(instructorError, 'Instructor');

  // Fetch offerings for this instructor
  const { data: offerings, error: offeringsError } = await offeringRepo.getByInstructorId(id);
  if (offeringsError) handleSupabaseError(offeringsError);

  const typedOfferings = (offerings || []) as unknown as OfferingWithCourse[];

  // Fetch AI summary (optional — ignore errors)
  const { data: aiSummary } = await aiSummaryRepo.getByEntity('instructor', id);

  // Early return if no offerings
  if (typedOfferings.length === 0) {
    return {
      ...instructor,
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

  return {
    ...instructor,
    offerings: offeringsWithRatings,
    aggregatedRatings,
    aiSummary: aiSummary?.summary || null,
  };
}
