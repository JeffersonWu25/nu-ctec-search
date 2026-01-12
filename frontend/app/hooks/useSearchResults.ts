'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { SearchFilters } from '../types/filters';

export interface SearchResult {
  id: string;
  courseCode: string;
  courseName: string;
  instructor: string;
  instructorId: string;
  quarter: string;
  year: number;
  overallRating: number | null;
  teachingRating: number | null;
  hoursPerWeek: string | null;
}

interface UseSearchResultsProps {
  filters: SearchFilters;
  hasActiveFilters: boolean;
}

interface UseSearchResultsReturn {
  results: SearchResult[];
  totalCount: number;
  isLoading: boolean;
  isLoadingMore: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => void;
  resultsEndRef: React.RefObject<HTMLDivElement | null>;
}

const RESULTS_PER_PAGE = 10;

// Map frontend sort options to API sort params
const SORT_MAP: Record<string, { sortBy: string; sortOrder: string }> = {
  'Recency': { sortBy: 'recency', sortOrder: 'desc' },
  'Overall Rating': { sortBy: 'overall', sortOrder: 'desc' },
  'Teaching Rating': { sortBy: 'teaching', sortOrder: 'desc' },
  'Ease': { sortBy: 'ease', sortOrder: 'asc' }, // Lower hours = easier, so asc
};

export function useSearchResults({
  filters,
  hasActiveFilters,
}: UseSearchResultsProps): UseSearchResultsReturn {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const resultsEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const hasMore = results.length < totalCount;

  // Build query params from filters
  const buildQueryParams = useCallback((currentOffset: number): string => {
    const params = new URLSearchParams();

    if (filters.subjects.length > 0) {
      params.set('departmentIds', filters.subjects.map(s => s.id).join(','));
    }
    if (filters.courses.length > 0) {
      params.set('courseIds', filters.courses.map(c => c.id).join(','));
    }
    if (filters.instructors.length > 0) {
      params.set('instructorIds', filters.instructors.map(i => i.id).join(','));
    }
    if (filters.requirements.length > 0) {
      params.set('requirementIds', filters.requirements.map(r => r.id).join(','));
    }

    const sortConfig = SORT_MAP[filters.sortBy] || SORT_MAP['Recency'];
    params.set('sortBy', sortConfig.sortBy);
    params.set('sortOrder', sortConfig.sortOrder);

    params.set('limit', RESULTS_PER_PAGE.toString());
    params.set('offset', currentOffset.toString());

    return params.toString();
  }, [filters]);

  // Fetch results from API
  const fetchResults = useCallback(async (isLoadMore: boolean = false) => {
    if (!hasActiveFilters) {
      setResults([]);
      setTotalCount(0);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const currentOffset = isLoadMore ? offset : 0;

    if (isLoadMore) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
      setOffset(0);
    }
    setError(null);

    try {
      const queryParams = buildQueryParams(currentOffset);
      const response = await fetch(`/api/course-offerings/search?${queryParams}`, {
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }

      const data = await response.json();

      if (isLoadMore) {
        setResults(prev => [...prev, ...(data.data || [])]);
      } else {
        setResults(data.data || []);
      }
      setTotalCount(data.count || 0);

      if (isLoadMore) {
        setOffset(currentOffset + RESULTS_PER_PAGE);
      } else {
        setOffset(RESULTS_PER_PAGE);
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [hasActiveFilters, buildQueryParams, offset]);

  // Load more function for infinite scroll
  const loadMore = useCallback(() => {
    if (!isLoadingMore && hasMore) {
      fetchResults(true);
    }
  }, [isLoadingMore, hasMore, fetchResults]);

  // Fetch when filters change
  useEffect(() => {
    fetchResults(false);

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [filters, hasActiveFilters]); // eslint-disable-line react-hooks/exhaustive-deps

  // Intersection Observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && hasMore && !isLoading && !isLoadingMore) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (resultsEndRef.current) {
      observer.observe(resultsEndRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, isLoading, isLoadingMore, loadMore]);

  return {
    results,
    totalCount,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    loadMore,
    resultsEndRef,
  };
}
