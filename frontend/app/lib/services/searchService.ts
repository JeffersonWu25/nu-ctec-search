/**
 * Business logic for keyword search across courses and comments.
 */

import * as courseRepo from '@/app/lib/repositories/courseRepo';
import * as commentRepo from '@/app/lib/repositories/commentRepo';
import { handleSupabaseError } from '@/app/lib/errors';

export async function search(query: string, limit: number) {
  const { data: courses, error: coursesError } = await courseRepo.searchByKeyword(query, limit);
  if (coursesError) handleSupabaseError(coursesError);

  const { data: matchingComments, error: commentsError } = await commentRepo.searchByKeyword(query, limit);
  if (commentsError) handleSupabaseError(commentsError);

  return {
    courses: courses || [],
    comments: matchingComments || [],
  };
}
