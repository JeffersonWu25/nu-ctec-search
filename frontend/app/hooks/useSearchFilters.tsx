'use client';

import { createContext, useContext, useState, useMemo, useCallback, ReactNode } from 'react';
import { useSearchParams } from 'next/navigation';
import { SearchFilters, initialFilters, FilterKey, Option } from '../types/filters';

interface SearchFiltersContextType {
  filters: SearchFilters;
  updateFilter: (key: FilterKey, value: Option[]) => void;
  updateSortBy: (sortBy: string) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
}

const SearchFiltersContext = createContext<SearchFiltersContextType | undefined>(undefined);

function getInitialFiltersFromParams(searchParams: URLSearchParams): SearchFilters {
  const courseId = searchParams.get('courseId');
  const courseName = searchParams.get('courseName');
  const instructorId = searchParams.get('instructorId');
  const instructorName = searchParams.get('instructorName');

  const newFilters: SearchFilters = { ...initialFilters };

  if (courseId && courseName) {
    newFilters.courses = [{ id: courseId, label: decodeURIComponent(courseName) }];
  }

  if (instructorId && instructorName) {
    newFilters.instructors = [{ id: instructorId, label: decodeURIComponent(instructorName) }];
  }

  return newFilters;
}

export function SearchFiltersProvider({ children }: { children: ReactNode }) {
  const searchParams = useSearchParams();

  // Initialize filters from URL params using lazy initialization
  const [filters, setFilters] = useState<SearchFilters>(() =>
    getInitialFiltersFromParams(searchParams)
  );

  const updateFilter = useCallback((key: FilterKey, value: Option[]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const updateSortBy = useCallback((sortBy: string) => {
    setFilters(prev => ({ ...prev, sortBy }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters(initialFilters);
  }, []);

  const hasActiveFilters = useMemo(() => {
    return filters.subjects.length > 0 ||
           filters.courses.length > 0 ||
           filters.instructors.length > 0 ||
           filters.requirements.length > 0;
  }, [filters]);

  const value = useMemo(() => ({
    filters,
    updateFilter,
    updateSortBy,
    clearFilters,
    hasActiveFilters
  }), [filters, updateFilter, updateSortBy, clearFilters, hasActiveFilters]);

  return (
    <SearchFiltersContext.Provider value={value}>
      {children}
    </SearchFiltersContext.Provider>
  );
}

export function useSearchFilters() {
  const context = useContext(SearchFiltersContext);
  if (context === undefined) {
    throw new Error('useSearchFilters must be used within a SearchFiltersProvider');
  }
  return context;
}
