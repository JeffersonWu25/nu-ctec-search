'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface AutocompleteItem {
  id: string;
  label: string;
  type: 'course' | 'instructor';
}

interface AutocompleteResult {
  items: AutocompleteItem[];
  isLoading: boolean;
}

// Searches courses and instructors for autocomplete suggestions
// Returns up to `limit` total results, grouped by type
export function useAutocomplete(query: string, limit: number = 5): AutocompleteResult {
  const [items, setItems] = useState<AutocompleteItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const search = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setItems([]);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsLoading(true);

    try {
      // Fetch courses and instructors in parallel
      const [coursesRes, instructorsRes] = await Promise.all([
        fetch(`/api/courses?limit=50`, { signal: abortControllerRef.current.signal }),
        fetch(`/api/instructors?limit=50`, { signal: abortControllerRef.current.signal }),
      ]);

      if (!coursesRes.ok || !instructorsRes.ok) {
        throw new Error('Failed to fetch');
      }

      const [coursesData, instructorsData] = await Promise.all([
        coursesRes.json(),
        instructorsRes.json(),
      ]);

      const normalizedQuery = searchQuery.toLowerCase().replace(/[_-]/g, ' ');

      // Filter courses that match the query
      const matchingCourses: AutocompleteItem[] = (coursesData.data || [])
        .filter((c: { code: string; title: string }) => {
          const normalizedCode = c.code.toLowerCase().replace(/[_-]/g, ' ');
          const title = c.title.toLowerCase();
          return normalizedCode.includes(normalizedQuery) || title.includes(normalizedQuery);
        })
        .map((c: { id: string; code: string; title: string }) => ({
          id: c.id,
          label: `${c.code} - ${c.title}`,
          type: 'course' as const,
        }));

      // Filter instructors that match the query
      const matchingInstructors: AutocompleteItem[] = (instructorsData.data || [])
        .filter((i: { name: string }) =>
          i.name.toLowerCase().includes(normalizedQuery)
        )
        .map((i: { id: string; name: string }) => ({
          id: i.id,
          label: i.name,
          type: 'instructor' as const,
        }));

      // Combine and limit to total of `limit` items
      // Prioritize courses if query looks like a course code, otherwise split evenly
      const looksLikeCourseCode = /^[a-z]{2,}/i.test(searchQuery.trim());

      let combined: AutocompleteItem[] = [];
      if (looksLikeCourseCode) {
        // Prioritize courses
        const coursesToTake = Math.min(matchingCourses.length, limit);
        const instructorsToTake = Math.min(matchingInstructors.length, limit - coursesToTake);
        combined = [
          ...matchingCourses.slice(0, coursesToTake),
          ...matchingInstructors.slice(0, instructorsToTake),
        ];
      } else {
        // Split more evenly
        const half = Math.ceil(limit / 2);
        const coursesToTake = Math.min(matchingCourses.length, half);
        const instructorsToTake = Math.min(matchingInstructors.length, limit - coursesToTake);
        combined = [
          ...matchingCourses.slice(0, coursesToTake),
          ...matchingInstructors.slice(0, instructorsToTake),
        ];
      }

      setItems(combined.slice(0, limit));
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Ignore aborted requests
      }
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      search(query);
    }, 250); // Debounce

    return () => {
      clearTimeout(timeoutId);
    };
  }, [query, search]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { items, isLoading };
}
