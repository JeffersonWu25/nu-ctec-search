/**
 * Business logic for the discover/recommendation feature.
 * Candidate selection -> embedding -> vector search -> scoring.
 */

import OpenAI from 'openai';
import * as courseMetricsRepo from '@/app/lib/repositories/courseMetricsRepo';
import * as requirementRepo from '@/app/lib/repositories/requirementRepo';
import * as commentRepo from '@/app/lib/repositories/commentRepo';
import { getOpenAIClient } from '@/app/lib/openaiClient';
import { handleSupabaseError, externalServiceError } from '@/app/lib/errors';
import {
  EMBEDDING_MODEL,
  DISCOVER_CHUNK_SIMILARITY_THRESHOLD,
  DISCOVER_COURSE_SCORE_THRESHOLD,
  DISCOVER_MAX_CHUNKS,
  DISCOVER_MAX_CANDIDATES,
  DISCOVER_TOP_COURSES_WITH_QUERY,
  DISCOVER_TOP_COURSES_NO_QUERY,
  DISCOVER_TOP_CHUNKS_PER_COURSE,
} from '@/app/lib/config';
import type {
  DiscoverRequestBody,
  DiscoverResponse,
  DiscoverCourse,
  CandidateCourse,
  MatchingSnippet,
} from '@/app/types/discover';

interface SimilarChunk {
  chunk_id: string;
  course_id: string;
  content: string;
  similarity: number;
}

export async function discover(body: DiscoverRequestBody): Promise<DiscoverResponse> {
  const {
    query,
    min_course_rating,
    max_course_rating,
    min_instruction_rating,
    max_instruction_rating,
    hours_buckets,
    requirement_ids,
  } = body;

  try {
    // Step 1: Candidate selection via SQL filters
    const candidates = await getCandidateCourses({
      min_course_rating,
      max_course_rating,
      min_instruction_rating,
      max_instruction_rating,
      hours_buckets,
      requirement_ids,
    });

    if (candidates.length === 0) {
      return { courses: [], total_candidates: 0 };
    }

    // Step 2: If no query, return top courses by rating
    if (!query || query.trim().length === 0) {
      const topCourses = candidates
        .sort((a, b) => (b.course_rating_avg ?? 0) - (a.course_rating_avg ?? 0))
        .slice(0, DISCOVER_TOP_COURSES_NO_QUERY)
        .map((c) => ({
          ...c,
          similarity_score: null,
          matching_snippets: [],
        }));

      return { courses: topCourses, total_candidates: candidates.length };
    }

    // Step 3: Embed query
    const openai = getOpenAIClient();
    const embeddingResponse = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: query.trim(),
    });
    const queryEmbedding = embeddingResponse.data[0].embedding;

    // Step 4: Search for similar chunks within candidate courses
    const candidateIds = candidates.map((c) => c.id);
    const { data: similarChunks, error: searchError } = await commentRepo.searchDiscoverComments({
      embedding: queryEmbedding,
      courseIds: candidateIds,
      similarityThreshold: DISCOVER_CHUNK_SIMILARITY_THRESHOLD,
      maxResults: DISCOVER_MAX_CHUNKS,
    });

    if (searchError) handleSupabaseError(searchError);

    const chunks: SimilarChunk[] = similarChunks || [];

    if (chunks.length === 0) {
      return { courses: [], total_candidates: candidates.length };
    }

    // Step 5: Aggregate chunks by course
    const courseChunksMap = new Map<string, SimilarChunk[]>();
    for (const chunk of chunks) {
      const existing = courseChunksMap.get(chunk.course_id) || [];
      existing.push(chunk);
      courseChunksMap.set(chunk.course_id, existing);
    }

    // Step 6: Compute course scores (avg of top N chunk similarities)
    const courseScores: { courseId: string; score: number; topChunks: SimilarChunk[] }[] = [];

    for (const [courseId, courseChunks] of courseChunksMap) {
      const sortedChunks = courseChunks
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, DISCOVER_TOP_CHUNKS_PER_COURSE);

      const avgScore = sortedChunks.reduce((sum, c) => sum + c.similarity, 0) / sortedChunks.length;

      if (avgScore >= DISCOVER_COURSE_SCORE_THRESHOLD) {
        courseScores.push({ courseId, score: avgScore, topChunks: sortedChunks });
      }
    }

    // Step 7: Sort by score and take top N
    courseScores.sort((a, b) => b.score - a.score);
    const topCourseScores = courseScores.slice(0, DISCOVER_TOP_COURSES_WITH_QUERY);

    // Step 8: Build response with course metadata and snippets
    const candidateMap = new Map(candidates.map((c) => [c.id, c]));

    const discoverCourses: DiscoverCourse[] = topCourseScores.map(({ courseId, score, topChunks }) => {
      const candidate = candidateMap.get(courseId)!;
      const snippets: MatchingSnippet[] = topChunks.map((chunk) => ({
        chunk_id: chunk.chunk_id,
        content: chunk.content,
        similarity: Math.round(chunk.similarity * 1000) / 1000,
      }));

      return {
        id: candidate.id,
        code: candidate.code,
        title: candidate.title,
        description: candidate.description,
        course_rating_avg: candidate.course_rating_avg,
        instruction_rating_avg: candidate.instruction_rating_avg,
        hours_per_week_mode: candidate.hours_per_week_mode,
        similarity_score: Math.round(score * 1000) / 1000,
        matching_snippets: snippets,
      };
    });

    return { courses: discoverCourses, total_candidates: candidates.length };
  } catch (error) {
    if (error instanceof OpenAI.APIError) {
      throw externalServiceError('OpenAI', error.message);
    }
    throw error;
  }
}

// --- Private helpers ---

/**
 * Get candidate courses matching filter criteria.
 * Applies AND-logic for requirements (course must have ALL selected requirements).
 */
async function getCandidateCourses(filters: {
  min_course_rating?: number;
  max_course_rating?: number;
  min_instruction_rating?: number;
  max_instruction_rating?: number;
  hours_buckets?: string[];
  requirement_ids?: string[];
}): Promise<CandidateCourse[]> {
  const {
    min_course_rating,
    max_course_rating,
    min_instruction_rating,
    max_instruction_rating,
    hours_buckets,
    requirement_ids,
  } = filters;

  const { data, error } = await courseMetricsRepo.getCandidates(
    {
      minCourseRating: min_course_rating,
      maxCourseRating: max_course_rating,
      minInstructionRating: min_instruction_rating,
      maxInstructionRating: max_instruction_rating,
      hoursBuckets: hours_buckets,
    },
    DISCOVER_MAX_CANDIDATES,
  );

  if (error) {
    console.error('Candidate query error:', error);
    return [];
  }

  if (!data || data.length === 0) {
    return [];
  }

  // Extract course IDs from metrics join
  let candidateIds = data.map((row) => {
    const course = row.courses as unknown as { id: string };
    return course.id;
  });

  // Requirement filtering: AND logic (course must have ALL selected requirements)
  if (requirement_ids && requirement_ids.length > 0) {
    const { data: reqData, error: reqError } = await requirementRepo.getCourseIdsByRequirements(
      requirement_ids,
      candidateIds,
    );

    if (reqError) {
      console.error('Requirement filter error:', reqError);
    } else if (reqData) {
      const courseReqCount = new Map<string, number>();
      for (const row of reqData) {
        courseReqCount.set(row.course_id, (courseReqCount.get(row.course_id) || 0) + 1);
      }
      candidateIds = candidateIds.filter(
        (id) => courseReqCount.get(id) === requirement_ids.length,
      );
    }
  }

  // Build final candidate list
  const candidateIdSet = new Set(candidateIds);

  return data
    .filter((row) => {
      const course = row.courses as unknown as { id: string };
      return candidateIdSet.has(course.id);
    })
    .map((row) => {
      const course = row.courses as unknown as {
        id: string;
        code: string;
        title: string;
        description: string | null;
      };

      return {
        id: course.id,
        code: course.code,
        title: course.title,
        description: course.description,
        course_rating_avg: row.course_rating_avg,
        instruction_rating_avg: row.instruction_rating_avg,
        hours_per_week_mode: row.hours_per_week_mode,
      };
    });
}
