'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface DiscoverSearchProps {
  showTitle?: boolean;
  placeholder?: string;
  className?: string;
}

const ANIMATED_QUERIES = [
  "easy CS classes",
  "math with good professors", 
  "classes that teach python",
  "high rated EECS courses",
  "interesting humanities",
  "practical engineering",
  "fun electives",
  "low workload courses",
  "machine learning intro",
  "writing intensive",
  "creative workshops",
  "research opportunities",
];

const ROW_1_QUERIES = ANIMATED_QUERIES.slice(0, Math.ceil(ANIMATED_QUERIES.length / 2));
const ROW_2_QUERIES = ANIMATED_QUERIES.slice(Math.ceil(ANIMATED_QUERIES.length / 2));

export default function DiscoverSearch({ 
  showTitle = true, 
  placeholder = "e.g., I want an easy class that teaches me pytorch",
  className = ""
}: DiscoverSearchProps) {
  const router = useRouter();
  const [naturalLanguageQuery, setNaturalLanguageQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const handleSearch = useCallback(async () => {
    if (naturalLanguageQuery.trim()) {
      setIsLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 500));
        // Create a new chat with the query
        const newChatId = `chat-${Date.now()}`;
        router.push(`/discover/chat/${newChatId}?q=${encodeURIComponent(naturalLanguageQuery)}`);
      } catch {
        router.push('/error');
      } finally {
        setIsLoading(false);
      }
    }
  }, [naturalLanguageQuery, router]);

  const handleFormSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  }, [handleSearch]);

  const handleQuerySelect = useCallback((query: string) => {
    setNaturalLanguageQuery(query);
    searchInputRef.current?.focus();
  }, []);

  return (
    <div className={`text-center ${className}`}>
      {showTitle && (
        <h1 className="text-h1 text-gray-900 mb-2 max-w-[500px] mx-auto">
          Trying to find a course that matches your <span className="text-purple-600">interest</span>? Search below using natural language.
        </h1>
      )}
      
      <form onSubmit={handleFormSubmit} className="max-w-4xl mx-auto mt-12 mb-12" role="search">
        <div className="relative">
          <label htmlFor="natural-search" className="sr-only">
            Search using natural language
          </label>
          <input
            ref={searchInputRef}
            id="natural-search"
            type="text"
            value={naturalLanguageQuery}
            onChange={(e) => setNaturalLanguageQuery(e.target.value)}
            placeholder={placeholder}
            className="w-full px-6 py-4 pr-16 text-lg border-2 border-purple-300 rounded-xl focus:outline-none focus:border-purple-500 focus:ring-4 focus:ring-purple-100 shadow-lg"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-md disabled:opacity-50"
            aria-label="Search using natural language"
          >
            {isLoading ? (
              <div className="animate-spin w-5 h-5 border-2 border-current border-t-transparent rounded-full" />
            ) : (
              '✨'
            )}
          </button>
        </div>
      </form>

      <div className="space-y-4" aria-label="Example search queries">
        {/* Row 1 */}
        <div className="overflow-hidden whitespace-nowrap">
          <div className="inline-flex space-x-4 animate-scroll">
            {[...ROW_1_QUERIES, ...ROW_1_QUERIES].map((query, index) => (
              <button
                key={`row1-${index}`}
                onClick={() => handleQuerySelect(query)}
                className="flex-shrink-0 px-5 py-2.5 bg-white rounded-full border border-gray-200 hover:border-blue-300 hover:bg-blue-50 focus:bg-blue-50 focus:border-blue-400 transition-all duration-300 text-gray-700 font-medium text-sm shadow-sm hover:shadow-md"
                aria-label={`Use example query: ${query}`}
              >
                {query}
              </button>
            ))}
          </div>
        </div>
        
        {/* Row 2 */}
        <div className="overflow-hidden whitespace-nowrap">
          <div className="inline-flex space-x-4 animate-scroll">
            {[...ROW_2_QUERIES, ...ROW_2_QUERIES].map((query, index) => (
              <button
                key={`row2-${index}`}
                onClick={() => handleQuerySelect(query)}
                className="flex-shrink-0 px-5 py-2.5 bg-white rounded-full border border-gray-200 hover:border-blue-300 hover:bg-blue-50 focus:bg-blue-50 focus:border-blue-400 transition-all duration-300 text-gray-700 font-medium text-sm shadow-sm hover:shadow-md"
                aria-label={`Use example query: ${query}`}
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-12 flex items-center justify-center gap-2 text-gray-500">
        <div className="w-8 h-px bg-gray-300"></div>
        <span className="text-body-sm">Powered by AI</span>
        <div className="w-8 h-px bg-gray-300"></div>
      </div>
    </div>
  );
}