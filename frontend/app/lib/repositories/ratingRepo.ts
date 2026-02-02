import { supabase } from '@/app/lib/supabase';

/** Shared select string for ratings with nested distribution data. */
const RATING_SELECT = `
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
`;

/**
 * Select string for the offering detail page, which also needs option id.
 */
const RATING_DETAIL_SELECT = `
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
`;

/**
 * Select string for search page ratings, which needs min_value/max_value.
 */
const RATING_SEARCH_SELECT = `
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
`;

/**
 * Get ratings for a single offering (offering detail page).
 * From: /api/course-offerings/[id]
 */
export function getByOfferingId(offeringId: string) {
  return supabase
    .from('ratings')
    .select(RATING_DETAIL_SELECT)
    .eq('course_offering_id', offeringId);
}

/**
 * Get ratings for multiple offerings (course/instructor aggregation).
 * From: /api/courses/[id], /api/instructors/[id]
 */
export function getByOfferingIds(offeringIds: string[]) {
  return supabase
    .from('ratings')
    .select(RATING_SELECT)
    .in('course_offering_id', offeringIds);
}

/**
 * Get ratings for search results (includes min_value/max_value on options).
 * From: /api/course-offerings/search
 */
export function getByOfferingIdsForSearch(offeringIds: string[]) {
  return supabase
    .from('ratings')
    .select(RATING_SEARCH_SELECT)
    .in('course_offering_id', offeringIds);
}
