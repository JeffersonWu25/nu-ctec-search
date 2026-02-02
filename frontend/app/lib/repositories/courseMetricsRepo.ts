import { supabase } from '@/app/lib/supabase';

export interface CandidateFilters {
  minCourseRating?: number;
  maxCourseRating?: number;
  minInstructionRating?: number;
  maxInstructionRating?: number;
  hoursBuckets?: string[];
}

/**
 * Get course metrics with course details, filtered by rating/hours criteria.
 * From: /api/discover
 */
export function getCandidates(filters: CandidateFilters, limit: number) {
  let query = supabase
    .from('course_metrics')
    .select(`
      course_id,
      course_rating_avg,
      instruction_rating_avg,
      hours_per_week_mode,
      courses!inner (
        id,
        code,
        title,
        description
      )
    `)
    .limit(limit);

  if (filters.minCourseRating !== undefined) {
    query = query.gte('course_rating_avg', filters.minCourseRating);
  }
  if (filters.maxCourseRating !== undefined) {
    query = query.lte('course_rating_avg', filters.maxCourseRating);
  }
  if (filters.minInstructionRating !== undefined) {
    query = query.gte('instruction_rating_avg', filters.minInstructionRating);
  }
  if (filters.maxInstructionRating !== undefined) {
    query = query.lte('instruction_rating_avg', filters.maxInstructionRating);
  }
  if (filters.hoursBuckets && filters.hoursBuckets.length > 0) {
    query = query.in('hours_per_week_mode', filters.hoursBuckets);
  }

  return query;
}
