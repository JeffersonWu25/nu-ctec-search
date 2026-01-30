/**
 * API client for the discover/recommendation endpoint.
 */

import {
  DiscoverRequestBody,
  DiscoverResponse,
} from '@/app/types/discover';

export interface DiscoverFilters {
  minCourseRating?: number;
  maxCourseRating?: number;
  minInstructionRating?: number;
  maxInstructionRating?: number;
  hoursBuckets?: string[];
  requirementIds?: string[];
}

/**
 * Call the discover API to get course recommendations.
 *
 * @param query - Natural language search query (optional)
 * @param filters - Filter criteria for candidate selection
 * @returns Promise resolving to discover response with courses
 */
export async function discover(
  query?: string,
  filters?: DiscoverFilters
): Promise<DiscoverResponse> {
  const body: DiscoverRequestBody = {};

  if (query && query.trim()) {
    body.query = query.trim();
  }

  if (filters) {
    if (filters.minCourseRating !== undefined) {
      body.min_course_rating = filters.minCourseRating;
    }
    if (filters.maxCourseRating !== undefined) {
      body.max_course_rating = filters.maxCourseRating;
    }
    if (filters.minInstructionRating !== undefined) {
      body.min_instruction_rating = filters.minInstructionRating;
    }
    if (filters.maxInstructionRating !== undefined) {
      body.max_instruction_rating = filters.maxInstructionRating;
    }
    if (filters.hoursBuckets && filters.hoursBuckets.length > 0) {
      body.hours_buckets = filters.hoursBuckets;
    }
    if (filters.requirementIds && filters.requirementIds.length > 0) {
      body.requirement_ids = filters.requirementIds;
    }
  }

  const response = await fetch('/api/discover', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Discover API error: ${response.status}`);
  }

  return response.json();
}
