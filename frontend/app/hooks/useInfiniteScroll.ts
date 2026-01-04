'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { Course } from '../types/course';

interface UseInfiniteScrollProps {
  allCourses: Course[];
  hasActiveFilters: boolean;
  resultsPerPage?: number;
}

interface UseInfiniteScrollReturn {
  visibleCourses: Course[];
  totalResults: number;
  displayedCount: number;
  isLoading: boolean;
  hasMoreResults: boolean;
  resultsEndRef: React.RefObject<HTMLDivElement | null>;
}

export function useInfiniteScroll({ 
  allCourses, 
  hasActiveFilters, 
  resultsPerPage = 10 
}: UseInfiniteScrollProps): UseInfiniteScrollReturn {
  const [isLoading, setIsLoading] = useState(false);
  const resultsEndRef = useRef<HTMLDivElement>(null);

  // Filter courses based on whether filters are active
  const filteredCourses = useMemo(() => 
    hasActiveFilters ? allCourses : [], 
    [allCourses, hasActiveFilters]
  );

  // Use a key that changes when filters change to reset pagination
  const filterKey = `${hasActiveFilters}-${filteredCourses.length}`;
  const [currentFilterKey, setCurrentFilterKey] = useState(filterKey);
  const [additionalPages, setAdditionalPages] = useState(0);

  // Reset when filter key changes
  if (currentFilterKey !== filterKey) {
    setCurrentFilterKey(filterKey);
    setAdditionalPages(0);
  }

  const totalResults = filteredCourses.length;
  const displayedCount = resultsPerPage + (additionalPages * resultsPerPage);
  const visibleCourses = filteredCourses.slice(0, displayedCount);
  const hasMoreResults = displayedCount < totalResults;

  // Intersection Observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && hasMoreResults && !isLoading) {
          setIsLoading(true);
          setTimeout(() => {
            setAdditionalPages(prev => prev + 1);
            setIsLoading(false);
          }, 500);
        }
      },
      { threshold: 1.0 }
    );

    if (resultsEndRef.current) {
      observer.observe(resultsEndRef.current);
    }

    return () => observer.disconnect();
  }, [hasMoreResults, isLoading, totalResults, resultsPerPage]);

  return {
    visibleCourses,
    totalResults,
    displayedCount,
    isLoading,
    hasMoreResults,
    resultsEndRef
  };
}