'use client';

import { useEffect, useRef, useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import { useChat } from '@/app/hooks/useChat';
import { DiscoverFilters } from '@/app/lib/discoverClient';
import ChatHeader from '@/app/components/Chat/ChatHeader';
import ChatMessage from '@/app/components/Chat/ChatMessage';
import ChatInput from '@/app/components/Chat/ChatInput';

export default function ChatPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Parse filters from URL params
  const filters: DiscoverFilters = useMemo(() => {
    const f: DiscoverFilters = {};

    const minCourse = searchParams.get('minCourse');
    if (minCourse) f.minCourseRating = parseFloat(minCourse);

    const minInstruction = searchParams.get('minInstruction');
    if (minInstruction) f.minInstructionRating = parseFloat(minInstruction);

    const hours = searchParams.get('hours');
    if (hours) f.hoursBuckets = hours.split(',');

    const requirements = searchParams.get('requirements');
    if (requirements) f.requirementIds = requirements.split(',');

    return f;
  }, [searchParams]);

  // Build active filters summary for display
  const activeFiltersSummary = useMemo(() => {
    const parts: string[] = [];
    if (filters.minCourseRating) parts.push(`Course ≥${filters.minCourseRating}`);
    if (filters.minInstructionRating) parts.push(`Teaching ≥${filters.minInstructionRating}`);
    if (filters.hoursBuckets?.length) parts.push(`Hours: ${filters.hoursBuckets.join(', ')}`);
    if (filters.requirementIds?.length) parts.push(`${filters.requirementIds.length} requirement(s)`);
    return parts;
  }, [filters]);

  const { messages, isLoading, sendMessage } = useChat({
    initialQuery: initialQuery || undefined,
    filters
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      {/* Header Section */}
      <div className="sticky top-16 z-10 bg-neutral-50 pt-4 pb-2">
        <div className="max-w-4xl mx-auto px-4">
          <ChatHeader initialQuery={initialQuery} />
          {activeFiltersSummary.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {activeFiltersSummary.map((filter, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full"
                >
                  {filter}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto pb-32 pt-7">
        <div className="max-w-4xl mx-auto space-y-6 px-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 text-gray-900 px-4 py-3 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="animate-spin w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
                  <span>Searching courses...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
}