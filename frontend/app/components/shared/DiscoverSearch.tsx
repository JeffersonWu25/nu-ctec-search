'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import RangeSlider from './RangeSlider';
import MultiSelectDropdown from '../SearchPage/MultiSelectDropdown';

interface DiscoverSearchProps {
  showTitle?: boolean;
  placeholder?: string;
  className?: string;
}

interface RequirementOption {
  id: string;
  label: string;
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

const HOURS_BUCKETS = [
  "3 or fewer",
  "4 - 7",
  "8 - 11",
  "12 - 15",
  "16 - 19",
  "20 or more",
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

  // Filter state
  const [minCourseRating, setMinCourseRating] = useState(1);
  const [minInstructionRating, setMinInstructionRating] = useState(1);
  const [selectedHoursBuckets, setSelectedHoursBuckets] = useState<string[]>([]);
  const [selectedRequirements, setSelectedRequirements] = useState<RequirementOption[]>([]);

  // Requirements from API
  const [requirementOptions, setRequirementOptions] = useState<RequirementOption[]>([]);

  // Fetch requirements on mount
  useEffect(() => {
    async function fetchRequirements() {
      try {
        const response = await fetch('/api/requirements');
        if (!response.ok) return;
        const data = await response.json();
        setRequirementOptions(
          data.data?.map((r: { id: string; name: string }) => ({
            id: r.id,
            label: r.name,
          })) || []
        );
      } catch {
        // Silently fail - requirements filter will just be empty
      }
    }
    fetchRequirements();
  }, []);

  const handleSearch = useCallback(async () => {
    if (naturalLanguageQuery.trim()) {
      setIsLoading(true);
      try {
        // Build filter params
        const filterParams = new URLSearchParams();
        filterParams.set('q', naturalLanguageQuery);

        if (minCourseRating > 1) {
          filterParams.set('minCourse', minCourseRating.toString());
        }
        if (minInstructionRating > 1) {
          filterParams.set('minInstruction', minInstructionRating.toString());
        }
        if (selectedHoursBuckets.length > 0) {
          filterParams.set('hours', selectedHoursBuckets.join(','));
        }
        if (selectedRequirements.length > 0) {
          filterParams.set('requirements', selectedRequirements.map(r => r.id).join(','));
        }

        const newChatId = `chat-${Date.now()}`;
        router.push(`/discover/chat/${newChatId}?${filterParams.toString()}`);
      } catch {
        router.push('/error');
      } finally {
        setIsLoading(false);
      }
    }
  }, [naturalLanguageQuery, minCourseRating, minInstructionRating, selectedHoursBuckets, selectedRequirements, router]);

  const handleFormSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  }, [handleSearch]);

  const handleQuerySelect = useCallback((query: string) => {
    setNaturalLanguageQuery(query);
    searchInputRef.current?.focus();
  }, []);

  const toggleHoursBucket = (bucket: string) => {
    setSelectedHoursBuckets(prev =>
      prev.includes(bucket)
        ? prev.filter(b => b !== bucket)
        : [...prev, bucket]
    );
  };

  const hasActiveFilters = minCourseRating > 1 || minInstructionRating > 1 ||
    selectedHoursBuckets.length > 0 || selectedRequirements.length > 0;

  const clearFilters = () => {
    setMinCourseRating(1);
    setMinInstructionRating(1);
    setSelectedHoursBuckets([]);
    setSelectedRequirements([]);
  };

  return (
    <div className={`text-center ${className}`}>
      {showTitle && (
        <h1 className="text-h1 text-gray-900 mb-2 max-w-[500px] mx-auto">
          Trying to find a course that matches your <span className="text-purple-600">interest</span>? Search below using natural language.
        </h1>
      )}

      {/* Filters Section - Always visible, above search */}
      <div className="max-w-4xl mx-auto mt-8 mb-6">
        <div className="p-6 bg-white border border-gray-200 rounded-xl shadow-sm text-left">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Filters</h2>
            {hasActiveFilters && (
              <button
                type="button"
                onClick={clearFilters}
                className="text-xs text-gray-500 hover:text-purple-600 transition-colors"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Rating Sliders */}
            <RangeSlider
              label="Min Course Rating"
              min={1}
              max={6}
              step={0.5}
              value={minCourseRating}
              onChange={setMinCourseRating}
            />

            <RangeSlider
              label="Min Instruction Rating"
              min={1}
              max={6}
              step={0.5}
              value={minInstructionRating}
              onChange={setMinInstructionRating}
            />

            {/* Hours per Week */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hours per Week
              </label>
              <div className="flex flex-wrap gap-2">
                {HOURS_BUCKETS.map((bucket) => (
                  <button
                    key={bucket}
                    type="button"
                    onClick={() => toggleHoursBucket(bucket)}
                    className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                      selectedHoursBuckets.includes(bucket)
                        ? 'bg-purple-100 border-purple-400 text-purple-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:border-purple-300'
                    }`}
                  >
                    {bucket}
                  </button>
                ))}
              </div>
            </div>

            {/* Requirements - MultiSelectDropdown */}
            <MultiSelectDropdown
              label="Distribution Requirements"
              placeholder="Search requirements..."
              options={requirementOptions}
              selectedOptions={selectedRequirements}
              onSelectionChange={setSelectedRequirements}
              maxResults={6}
            />
          </div>
        </div>
      </div>

      {/* Search Field */}
      <form onSubmit={handleFormSubmit} className="max-w-4xl mx-auto mb-8" role="search">
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

      <div className="space-y-4 mt-4" aria-label="Example search queries">
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