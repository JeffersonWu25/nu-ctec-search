'use client';

import { useSearchFilters } from '../../hooks/useSearchFilters';
import { useSearchResults } from '../../hooks/useSearchResults';
import CourseCard from './CourseCard';

export default function SearchResults() {
  const { filters, hasActiveFilters } = useSearchFilters();
  const {
    results,
    totalCount,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    resultsEndRef,
  } = useSearchResults({ filters, hasActiveFilters });

  return (
    <div className="flex-1">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Search Results {hasActiveFilters && `(${results.length} of ${totalCount})`}
        </h1>

        {!hasActiveFilters && (
          <div className="text-center py-16">
            <div className="text-gray-400 text-lg mb-2">No filters applied</div>
            <div className="text-gray-500">
              Select courses or instructors to see CTEC reviews and ratings.
            </div>
          </div>
        )}

        {hasActiveFilters && error && (
          <div className="text-center py-16">
            <div className="text-red-500 text-lg mb-2">Error loading results</div>
            <div className="text-gray-500">{error}</div>
          </div>
        )}
      </div>

      {hasActiveFilters && !error && (
        <>
          {/* Initial loading state */}
          {isLoading && results.length === 0 && (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-4 animate-pulse">
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
                  <div className="h-8 bg-gray-100 rounded w-32 mb-3"></div>
                  <div className="h-4 bg-gray-100 rounded w-1/4 mb-2"></div>
                  <div className="h-4 bg-gray-100 rounded w-1/5 mb-4"></div>
                  <div className="flex justify-between">
                    <div className="h-10 bg-gray-100 rounded w-16"></div>
                    <div className="h-10 bg-gray-100 rounded w-16"></div>
                    <div className="h-10 bg-gray-100 rounded w-16"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Results */}
          {results.length > 0 && (
            <div className="space-y-4">
              {results.map((result) => (
                <CourseCard
                  key={result.id}
                  id={result.id}
                  courseCode={result.courseCode}
                  courseName={result.courseName}
                  instructor={result.instructor}
                  quarter={result.quarter}
                  year={result.year}
                  overallRating={result.overallRating}
                  hoursPerWeek={result.hoursPerWeek}
                  teachingRating={result.teachingRating}
                />
              ))}
            </div>
          )}

          {/* No results */}
          {!isLoading && results.length === 0 && (
            <div className="text-center py-16">
              <div className="text-gray-400 text-lg mb-2">No results found</div>
              <div className="text-gray-500">
                Try adjusting your filters to find more courses.
              </div>
            </div>
          )}

          {/* Loading more indicator */}
          {isLoadingMore && (
            <div className="flex justify-center py-8">
              <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full"></div>
            </div>
          )}

          {/* Intersection observer target */}
          <div ref={resultsEndRef} className="h-4"></div>

          {/* End of results indicator */}
          {!hasMore && results.length > 0 && totalCount > 10 && (
            <div className="text-center py-8 text-gray-500">
              You&apos;ve reached the end of the results
            </div>
          )}
        </>
      )}
    </div>
  );
}
