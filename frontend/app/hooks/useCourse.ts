'use client';

import { useState, useEffect, useRef } from 'react';
import { Rating } from '../types/course';

export interface CourseOffering {
  id: string;
  quarter: string;
  year: number;
  section: number | null;
  instructorId: string;
  instructorName: string;
  overallRating: number | null;
  teachingRating: number | null;
  hoursPerWeek: string | null;
}

export interface CourseRequirement {
  id: string;
  name: string;
}

export interface CourseDepartment {
  id: string;
  code: string;
  name: string;
}

export interface CourseData {
  id: string;
  code: string;
  title: string;
  description: string | null;
  prerequisitesText: string | null;
  department: CourseDepartment | null;
  requirements: CourseRequirement[];
  offerings: CourseOffering[];
  aggregatedRatings: Rating[];
  aiSummary: string | null;
}

interface UseCourseReturn {
  course: CourseData | null;
  isLoading: boolean;
  error: string | null;
}

export function useCourse(courseId: string): UseCourseReturn {
  const [course, setCourse] = useState<CourseData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!courseId) {
      setIsLoading(false);
      setError('No course ID provided');
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const fetchCourse = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/courses/${courseId}`, {
          signal: abortControllerRef.current?.signal,
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Course not found');
          }
          throw new Error('Failed to fetch course');
        }

        const data = await response.json();
        setCourse(data.data);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCourse();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [courseId]);

  return {
    course,
    isLoading,
    error,
  };
}
