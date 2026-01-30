import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { supabase } from '@/app/lib/supabase';
import {
  DiscoverRequestBody,
  DiscoverResponse,
  DiscoverCourse,
  CandidateCourse,
  MatchingSnippet,
} from '@/app/types/discover';

const EMBEDDING_MODEL = 'text-embedding-3-small';
const CHUNK_SIMILARITY_THRESHOLD = 0.45;
const COURSE_SCORE_THRESHOLD = 0.5;
const MAX_CHUNKS = 100;
const MAX_CANDIDATES = 500;
const TOP_COURSES_WITH_QUERY = 3;
const TOP_COURSES_NO_QUERY = 0;
const TOP_CHUNKS_PER_COURSE = 5;

interface SimilarChunk {
  chunk_id: string;
  course_id: string;
  content: string;
  similarity: number;
}

export async function POST(request: NextRequest) {
  // Parse request body
  let body: DiscoverRequestBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

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
    // Step 1: Candidate selection via SQL
    const candidates = await getCandidateCourses({
      min_course_rating,
      max_course_rating,
      min_instruction_rating,
      max_instruction_rating,
      hours_buckets,
      requirement_ids,
    });

    if (candidates.length === 0) {
      return NextResponse.json({
        courses: [],
        total_candidates: 0,
      } as DiscoverResponse);
    }

    // Step 2: If no query, return top courses by rating
    if (!query || query.trim().length === 0) {
      const topCourses = candidates
        .sort((a, b) => (b.course_rating_avg ?? 0) - (a.course_rating_avg ?? 0))
        .slice(0, TOP_COURSES_NO_QUERY)
        .map((c) => ({
          ...c,
          similarity_score: null,
          matching_snippets: [],
        }));

      return NextResponse.json({
        courses: topCourses,
        total_candidates: candidates.length,
      } as DiscoverResponse);
    }

    // Step 3: Embed query and perform vector search
    const openaiApiKey = process.env.OPENAI_API_KEY;
    if (!openaiApiKey) {
      console.error('OPENAI_API_KEY is not configured');
      return NextResponse.json(
        { error: 'AI service is not configured' },
        { status: 500 }
      );
    }

    const openai = new OpenAI({ apiKey: openaiApiKey });

    const embeddingResponse = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: query.trim(),
    });
    const queryEmbedding = embeddingResponse.data[0].embedding;

    // Step 4: Search for similar chunks within candidate courses
    const candidateIds = candidates.map((c) => c.id);

    const { data: similarChunks, error: searchError } = await supabase.rpc(
      'search_discover_comments',
      {
        query_embedding: queryEmbedding,
        target_course_ids: candidateIds,
        similarity_threshold: CHUNK_SIMILARITY_THRESHOLD,
        max_results: MAX_CHUNKS,
      }
    );

    if (searchError) {
      console.error('Vector search error:', searchError);
      return NextResponse.json(
        { error: 'Failed to search comments' },
        { status: 500 }
      );
    }

    const chunks: SimilarChunk[] = similarChunks || [];

    if (chunks.length === 0) {
      // No matching chunks found - return empty
      return NextResponse.json({
        courses: [],
        total_candidates: candidates.length,
      } as DiscoverResponse);
    }

    // Step 5: Aggregate chunks by course
    const courseChunksMap = new Map<string, SimilarChunk[]>();
    for (const chunk of chunks) {
      const existing = courseChunksMap.get(chunk.course_id) || [];
      existing.push(chunk);
      courseChunksMap.set(chunk.course_id, existing);
    }

    // Step 6: Compute course scores (avg of top 3 chunk similarities)
    const courseScores: { courseId: string; score: number; topChunks: SimilarChunk[] }[] = [];

    for (const [courseId, courseChunks] of courseChunksMap) {
      // Sort by similarity descending and take top 3
      const sortedChunks = courseChunks
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, TOP_CHUNKS_PER_COURSE);

      // Compute average
      const avgScore =
        sortedChunks.reduce((sum, c) => sum + c.similarity, 0) / sortedChunks.length;

      if (avgScore >= COURSE_SCORE_THRESHOLD) {
        courseScores.push({
          courseId,
          score: avgScore,
          topChunks: sortedChunks,
        });
      }
    }

    // Step 7: Sort by score and take top 3
    courseScores.sort((a, b) => b.score - a.score);
    const topCourseScores = courseScores.slice(0, TOP_COURSES_WITH_QUERY);

    // Step 8: Build response with course metadata and snippets
    const candidateMap = new Map(candidates.map((c) => [c.id, c]));

    const discoverCourses: DiscoverCourse[] = topCourseScores.map(
      ({ courseId, score, topChunks }) => {
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
      }
    );

    return NextResponse.json({
      courses: discoverCourses,
      total_candidates: candidates.length,
    } as DiscoverResponse);

  } catch (error) {
    console.error('Discover API error:', error);

    if (error instanceof OpenAI.APIError) {
      return NextResponse.json(
        { error: `OpenAI API error: ${error.message}` },
        { status: 502 }
      );
    }

    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}

/**
 * Get candidate courses that match the filter criteria.
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

  // Build the query
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
    .limit(MAX_CANDIDATES);

  // Apply rating filters
  if (min_course_rating !== undefined) {
    query = query.gte('course_rating_avg', min_course_rating);
  }
  if (max_course_rating !== undefined) {
    query = query.lte('course_rating_avg', max_course_rating);
  }
  if (min_instruction_rating !== undefined) {
    query = query.gte('instruction_rating_avg', min_instruction_rating);
  }
  if (max_instruction_rating !== undefined) {
    query = query.lte('instruction_rating_avg', max_instruction_rating);
  }

  // Apply hours bucket filter (exact match on any selected bucket)
  if (hours_buckets && hours_buckets.length > 0) {
    query = query.in('hours_per_week_mode', hours_buckets);
  }

  const { data, error } = await query;

  if (error) {
    console.error('Candidate query error:', error);
    return [];
  }

  if (!data || data.length === 0) {
    return [];
  }

  // If requirement_ids filter is present, we need to filter by requirements
  let candidateIds = data.map((row) => {
    const course = row.courses as unknown as { id: string };
    return course.id;
  });

  if (requirement_ids && requirement_ids.length > 0) {
    // Get courses that have ALL of the specified requirements (AND logic)
    const { data: reqData, error: reqError } = await supabase
      .from('course_requirements')
      .select('course_id')
      .in('requirement_id', requirement_ids)
      .in('course_id', candidateIds);

    if (reqError) {
      console.error('Requirement filter error:', reqError);
    } else if (reqData) {
      // Count how many of the selected requirements each course has
      const courseReqCount = new Map<string, number>();
      for (const row of reqData) {
        courseReqCount.set(row.course_id, (courseReqCount.get(row.course_id) || 0) + 1);
      }
      // Keep only courses that have ALL selected requirements
      candidateIds = candidateIds.filter(
        (id) => courseReqCount.get(id) === requirement_ids.length
      );
    }
  }

  // Build the final candidate list
  const candidateIdSet = new Set(candidateIds);

  const candidates: CandidateCourse[] = data
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

  return candidates;
}
