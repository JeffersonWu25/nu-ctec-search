import { supabase } from '@/app/lib/supabase';

/**
 * Get an AI summary by entity type, entity ID, and summary type.
 * From: /api/course-offerings/[id], /api/courses/[id], /api/instructors/[id]
 */
export function getByEntity(
  entityType: 'course' | 'instructor' | 'course_offering',
  entityId: string,
  summaryType: string = 'default'
) {
  return supabase
    .from('ai_summaries')
    .select('summary')
    .eq('entity_type', entityType)
    .eq('entity_id', entityId)
    .eq('summary_type', summaryType)
    .single();
}
