/**
 * Types for the discover/recommendation API.
 */

// Request types

export interface DiscoverRequestBody {
  query?: string;
  min_course_rating?: number;
  max_course_rating?: number;
  min_instruction_rating?: number;
  max_instruction_rating?: number;
  hours_buckets?: string[];
  requirement_ids?: string[];
}

// Response types

export interface MatchingSnippet {
  chunk_id: string;
  content: string;
  similarity: number;
}

export interface DiscoverCourse {
  id: string;
  code: string;
  title: string;
  description: string | null;
  course_rating_avg: number | null;
  instruction_rating_avg: number | null;
  hours_per_week_mode: string | null;
  similarity_score: number | null;
  matching_snippets: MatchingSnippet[];
}

export interface DiscoverResponse {
  courses: DiscoverCourse[];
  total_candidates: number;
}

// Internal types for database queries

export interface CourseMetricsRow {
  course_id: string;
  learned_avg: number | null;
  course_rating_avg: number | null;
  instructor_interest_avg: number | null;
  prior_interest_avg: number | null;
  intellectually_challenging_avg: number | null;
  instruction_rating_avg: number | null;
  hours_per_week_mode: string | null;
}

export interface CandidateCourse {
  id: string;
  code: string;
  title: string;
  description: string | null;
  course_rating_avg: number | null;
  instruction_rating_avg: number | null;
  hours_per_week_mode: string | null;
}

export interface RagChunkWithEmbedding {
  chunk_id: string;
  course_id: string;
  content: string;
  embedding: number[];
}
