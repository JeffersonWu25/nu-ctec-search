import { supabase } from '@/app/lib/supabase';

export function getAll() {
  return supabase
    .from('requirements')
    .select('id, name')
    .order('name', { ascending: true });
}

/**
 * Get course IDs that have any of the specified requirements.
 * Optionally scoped to a set of candidate course IDs (used by discover).
 * Returns raw rows — caller is responsible for AND/OR logic
 * (e.g. counting occurrences to enforce "has ALL requirements").
 */
export function getCourseIdsByRequirements(
  requirementIds: string[],
  scopeToCourseIds?: string[]
) {
  let query = supabase
    .from('course_requirements')
    .select('course_id')
    .in('requirement_id', requirementIds);

  if (scopeToCourseIds && scopeToCourseIds.length > 0) {
    query = query.in('course_id', scopeToCourseIds);
  }

  return query;
}
