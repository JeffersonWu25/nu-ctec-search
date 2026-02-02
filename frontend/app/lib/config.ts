/**
 * Centralized configuration constants.
 * All hardcoded values from API routes are consolidated here.
 */

// AI Models
export const EMBEDDING_MODEL = 'text-embedding-3-small';
export const CHAT_MODEL = 'gpt-4o-mini';
export const CHAT_TEMPERATURE = 0.3;
export const CHAT_MAX_TOKENS = 500;

// Similarity Thresholds
export const ASK_SIMILARITY_THRESHOLD = 0.3;
export const DISCOVER_CHUNK_SIMILARITY_THRESHOLD = 0.45;
export const DISCOVER_COURSE_SCORE_THRESHOLD = 0.5;

// Result Limits
export const ASK_MAX_RESULTS = 8;
export const DISCOVER_MAX_CHUNKS = 100;
export const DISCOVER_MAX_CANDIDATES = 500;
export const DISCOVER_TOP_COURSES_WITH_QUERY = 3;
export const DISCOVER_TOP_COURSES_NO_QUERY = 0;
export const DISCOVER_TOP_CHUNKS_PER_COURSE = 5;

// Pagination Defaults
export const DEFAULT_PAGE_LIMIT = 20;
export const DEFAULT_LIST_LIMIT = 50;
export const DEFAULT_SEARCH_LIMIT = 10;
