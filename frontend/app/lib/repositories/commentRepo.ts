import { supabase } from '@/app/lib/supabase';

/**
 * Get comments for a single course offering.
 * From: /api/course-offerings/[id]
 */
export function getByOfferingId(offeringId: string) {
  return supabase
    .from('comments')
    .select('id, content')
    .eq('course_offering_id', offeringId);
}

/**
 * Search comments by keyword with offering/course/instructor context.
 * From: /api/search
 */
export function searchByKeyword(query: string, limit: number) {
  return supabase
    .from('comments')
    .select(`
      id,
      content,
      course_offering:course_offerings(
        id,
        quarter,
        year,
        course:courses(id, code, title),
        instructor:instructors(id, name)
      )
    `)
    .ilike('content', `%${query}%`)
    .limit(limit);
}

/**
 * Vector similarity search for comments within a single course offering.
 * Wraps the search_similar_comments RPC.
 * From: /api/course-offerings/[id]/ask
 */
export function searchBySimilarity(params: {
  embedding: number[];
  courseOfferingId: string;
  similarityThreshold: number;
  maxResults: number;
}) {
  return supabase.rpc('search_similar_comments', {
    query_embedding: params.embedding,
    target_course_offering_id: params.courseOfferingId,
    similarity_threshold: params.similarityThreshold,
    max_results: params.maxResults,
  });
}

/**
 * Vector similarity search for comments across multiple courses.
 * Wraps the search_discover_comments RPC.
 * From: /api/discover
 */
export function searchDiscoverComments(params: {
  embedding: number[];
  courseIds: string[];
  similarityThreshold: number;
  maxResults: number;
}) {
  return supabase.rpc('search_discover_comments', {
    query_embedding: params.embedding,
    target_course_ids: params.courseIds,
    similarity_threshold: params.similarityThreshold,
    max_results: params.maxResults,
  });
}
