'use client';

import { useState, useMemo } from 'react';
import { Comment } from '@/app/types/course';
import { MagnifyingGlassIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { usePagination } from '@/app/hooks/usePagination';

interface AIResponse {
  question: string;
  answer: string;
  referencedCommentIds: string[];
}

interface StudentCommentsProps {
  comments: Comment[];
  courseOfferingId: string;
}

const COMMENTS_PER_PAGE = 10;

export default function StudentComments({ comments, courseOfferingId }: StudentCommentsProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [isLoadingAI, setIsLoadingAI] = useState(false);

  // Filter comments based on search query or AI response
  const filteredComments = useMemo(() => {
    if (aiResponse) {
      // When AI response is active, show only referenced comments
      // If no comments were referenced, return empty array (not all comments)
      return comments.filter(comment =>
        aiResponse.referencedCommentIds.includes(comment.id)
      );
    }

    if (!searchQuery.trim()) return comments;
    return comments.filter(comment =>
      comment.content.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [comments, searchQuery, aiResponse]);

  const {
    displayedItems: displayedComments,
    hasMore,
    loadMore,
    loading
  } = usePagination({
    items: filteredComments,
    itemsPerPage: COMMENTS_PER_PAGE
  });

  const handleSearch = async () => {
    const query = searchInput.trim();
    if (!query) return;

    setIsLoadingAI(true);
    setAiResponse(null);

    try {
      const response = await fetch('/api/course-comments/ask-ai-unified', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ courseOfferingId, question: query })
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const data = await response.json();
      setAiResponse({
        question: data.question,
        answer: data.answer,
        referencedCommentIds: data.referencedCommentIds || []
      });
    } catch (error) {
      console.error('Error getting AI response:', error);
      setAiResponse({
        question: query,
        answer: 'Sorry, there was an error processing your question. Please try again.',
        referencedCommentIds: []
      });
    } finally {
      setIsLoadingAI(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchInput('');
    setAiResponse(null);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
      <div className="flex flex-col space-y-6 mb-6">
        <h2 className="text-xl font-bold text-neutral-900">Student Comments</h2>

        {/* AI Search */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-neutral-400" />
            <input
              type="text"
              placeholder="Ask AI about this course (e.g., 'Is this course difficult?', 'What's the workload like?')"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoadingAI}
              className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-neutral-50 disabled:cursor-not-allowed"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isLoadingAI || !searchInput.trim()}
            className="px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-neutral-300 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            {isLoadingAI ? 'Searching...' : 'Ask AI'}
          </button>
          {(aiResponse || searchQuery) && (
            <button
              onClick={clearSearch}
              className="px-4 py-3 bg-neutral-100 text-neutral-700 font-medium rounded-lg hover:bg-neutral-200 transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* AI Response */}
        {isLoadingAI && (
          <div className="border border-primary-200 rounded-lg p-4 bg-primary-50">
            <div className="flex items-center space-x-2 mb-3">
              <SparklesIcon className="h-5 w-5 text-primary-600 animate-pulse" />
              <h3 className="font-semibold text-primary-900">AI is analyzing comments...</h3>
            </div>
            <div className="animate-pulse">
              <div className="h-4 bg-primary-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-primary-200 rounded w-1/2"></div>
            </div>
          </div>
        )}

        {aiResponse && !isLoadingAI && (
          <div className="border border-primary-200 rounded-lg p-4 bg-primary-50">
            <div className="flex items-center space-x-2 mb-3">
              <SparklesIcon className="h-5 w-5 text-primary-600" />
              <h3 className="font-semibold text-primary-900">AI Response</h3>
            </div>
            <div className="mb-3">
              <p className="text-sm text-primary-700 font-medium mb-2">
                &ldquo;{aiResponse.question}&rdquo;
              </p>
              <p className="text-primary-900 leading-relaxed">
                {aiResponse.answer}
              </p>
            </div>
            <div className="text-xs text-primary-600">
              Based on {aiResponse.referencedCommentIds.length} student comments
            </div>
          </div>
        )}
      </div>

      {/* Comments Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-neutral-900">
            {aiResponse ? 'Referenced Comments' : 'All Comments'}
            <span className="ml-2 text-sm font-normal text-neutral-600">
              ({filteredComments.length} {filteredComments.length === 1 ? 'comment' : 'comments'})
            </span>
          </h3>
        </div>

        {filteredComments.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-neutral-500">
              {aiResponse
                ? 'No relevant comments found for this question. The AI could not find comments that match your query.'
                : 'No comments available.'}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {displayedComments.map((comment) => (
              <div
                key={comment.id}
                className={`p-4 rounded-lg border ${
                  aiResponse && aiResponse.referencedCommentIds.includes(comment.id)
                    ? 'bg-primary-50 border-primary-200'
                    : 'bg-neutral-50 border-neutral-200'
                }`}
              >
                <div className="text-sm text-neutral-900 leading-relaxed">
                  {comment.content}
                </div>
                {aiResponse && aiResponse.referencedCommentIds.includes(comment.id) && (
                  <div className="mt-2 text-xs text-primary-600 font-medium">
                    Referenced by AI
                  </div>
                )}
              </div>
            ))}

            {/* Load More Button */}
            {hasMore && (
              <div className="flex justify-center pt-6">
                <button
                  onClick={loadMore}
                  disabled={loading}
                  className="px-8 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                  {loading ? 'Loading...' : 'Load More Comments'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}