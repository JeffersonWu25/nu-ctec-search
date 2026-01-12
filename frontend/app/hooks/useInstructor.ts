'use client';

import { useState, useEffect, useRef } from 'react';
import { Rating } from '../types/course';

export interface InstructorOffering {
  id: string;
  courseCode: string;
  courseName: string;
  courseId: string;
  quarter: string;
  year: number;
  section: number | null;
  overallRating: number | null;
  teachingRating: number | null;
  hoursPerWeek: string | null;
}

export interface InstructorData {
  id: string;
  name: string;
  profile_photo: string | null;
  offerings: InstructorOffering[];
  aggregatedRatings: Rating[];
  aiSummary: string | null;
}

interface UseInstructorReturn {
  instructor: InstructorData | null;
  isLoading: boolean;
  error: string | null;
}

export function useInstructor(instructorId: string): UseInstructorReturn {
  const [instructor, setInstructor] = useState<InstructorData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!instructorId) {
      setIsLoading(false);
      setError('No instructor ID provided');
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const fetchInstructor = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/instructors/${instructorId}`, {
          signal: abortControllerRef.current?.signal,
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Instructor not found');
          }
          throw new Error('Failed to fetch instructor');
        }

        const data = await response.json();
        setInstructor(data.data);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchInstructor();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [instructorId]);

  return {
    instructor,
    isLoading,
    error,
  };
}
