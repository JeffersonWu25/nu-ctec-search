'use client';

import { useState, useEffect } from 'react';
import { Option } from '../types/filters';

interface FilterOptions {
  departments: Option[];
  courses: Option[];
  instructors: Option[];
  requirements: Option[];
  isLoading: boolean;
  error: string | null;
}

// Fetches all filter options from the API
export function useFilterOptions(): FilterOptions {
  const [departments, setDepartments] = useState<Option[]>([]);
  const [courses, setCourses] = useState<Option[]>([]);
  const [instructors, setInstructors] = useState<Option[]>([]);
  const [requirements, setRequirements] = useState<Option[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOptions() {
      setIsLoading(true);
      setError(null);

      try {
        const [deptRes, courseRes, instructorRes, reqRes] = await Promise.all([
          fetch('/api/departments'),
          fetch('/api/courses?limit=500'),
          fetch('/api/instructors?limit=500'),
          fetch('/api/requirements'),
        ]);

        if (!deptRes.ok || !courseRes.ok || !instructorRes.ok || !reqRes.ok) {
          throw new Error('Failed to fetch filter options');
        }

        const [deptData, courseData, instructorData, reqData] = await Promise.all([
          deptRes.json(),
          courseRes.json(),
          instructorRes.json(),
          reqRes.json(),
        ]);

        setDepartments(
          deptData.data?.map((d: { id: string; code: string; name: string }) => ({
            id: d.id,
            label: d.code,
            searchTerms: `${d.code} ${d.name}`,
          })) || []
        );

        setCourses(
          courseData.data?.map((c: { id: string; code: string; title: string }) => ({
            id: c.id,
            label: `${c.code}: ${c.title}`,
            searchTerms: `${c.code} ${c.title}`,
          })) || []
        );

        setInstructors(
          instructorData.data?.map((i: { id: string; name: string }) => ({
            id: i.id,
            label: i.name,
          })) || []
        );

        setRequirements(
          reqData.data?.map((r: { id: string; name: string }) => ({
            id: r.id,
            label: r.name,
          })) || []
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch options');
      } finally {
        setIsLoading(false);
      }
    }

    fetchOptions();
  }, []);

  return { departments, courses, instructors, requirements, isLoading, error };
}
