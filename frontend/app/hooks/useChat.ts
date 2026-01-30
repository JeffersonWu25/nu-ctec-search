import { useState, useRef, useCallback, useEffect } from 'react';
import { discover, DiscoverFilters } from '@/app/lib/discoverClient';
import { DiscoverCourse } from '@/app/types/discover';

export interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  cards?: any[];
  cardType?: 'course' | 'professor' | 'offering';
}

export interface CourseCard {
  courseId: string;
  courseCode: string;
  courseName: string;
  description?: string | null;
  courseRating?: number | null;
  instructionRating?: number | null;
  hoursPerWeek?: string | null;
  similarityScore?: number | null;
  matchingSnippets?: string[];
}

interface UseChatProps {
  initialQuery?: string;
  filters?: DiscoverFilters;
}

/**
 * Transform discover API response to chat message format.
 */
function transformDiscoverResponse(
  courses: DiscoverCourse[],
  query: string,
  totalCandidates: number
): Message {
  if (courses.length === 0) {
    return {
      id: `ai-${Date.now()}`,
      type: 'ai',
      content: `I couldn't find any courses matching "${query}" with your current filters. Try adjusting your filters or rephrasing your search.`,
      cards: [],
      cardType: 'course',
    };
  }

  // Keep content concise - details are shown in cards
  const content = `Based on ${totalCandidates.toLocaleString()} courses matching your filters, here are the top ${courses.length} recommendations for "${query}":`;

  const cards: CourseCard[] = courses.map(course => ({
    courseId: course.id,
    courseCode: course.code,
    courseName: course.title,
    description: course.description,
    courseRating: course.course_rating_avg,
    instructionRating: course.instruction_rating_avg,
    hoursPerWeek: course.hours_per_week_mode,
    similarityScore: course.similarity_score,
    matchingSnippets: course.matching_snippets.map(s => s.content),
  }));

  return {
    id: `ai-${Date.now()}`,
    type: 'ai',
    content,
    cards,
    cardType: 'course',
  };
}

export function useChat({ initialQuery, filters }: UseChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const hasInitialized = useRef(false);
  // Store filters in ref to avoid dependency issues
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const fetchDiscoverResponse = useCallback(async (query: string) => {
    try {
      const response = await discover(query, filtersRef.current);
      const aiMessage = transformDiscoverResponse(
        response.courses,
        query,
        response.total_candidates
      );
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: `ai-${Date.now()}`,
        type: 'ai',
        content: `Sorry, I encountered an error while searching for courses. Please try again.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
        cards: [],
        cardType: 'course',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: content.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    await fetchDiscoverResponse(content.trim());
  }, [isLoading, fetchDiscoverResponse]);

  // Initialize with query and auto-fetch on mount
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    if (!initialQuery) return;

    const initialMessage: Message = {
      id: 'initial',
      type: 'user',
      content: initialQuery
    };

    setMessages([initialMessage]);
    setIsLoading(true);
    fetchDiscoverResponse(initialQuery);
  }, [initialQuery, fetchDiscoverResponse]);

  return {
    messages,
    isLoading,
    sendMessage
  };
}
