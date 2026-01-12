'use client';

import { Suspense } from 'react';
import { SearchFiltersProvider } from '../../hooks/useSearchFilters';
import SearchFilters from './SearchFilters';
import SearchResults from './SearchResults';

function SearchPageContent() {
  return (
    <SearchFiltersProvider>
      <div className="min-h-[200vh] bg-white">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex gap-8">
            <SearchFilters />
            <SearchResults />
          </div>
        </div>
      </div>
    </SearchFiltersProvider>
  );
}

function SearchPageFallback() {
  return (
    <div className="min-h-[200vh] bg-white">
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex gap-8">
          <div className="w-80 flex-shrink-0">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="animate-pulse space-y-6">
                <div className="h-6 w-20 bg-gray-200 rounded"></div>
                {[...Array(4)].map((_, i) => (
                  <div key={i}>
                    <div className="h-4 w-24 bg-gray-200 rounded mb-2"></div>
                    <div className="h-10 bg-gray-100 rounded"></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="flex-1">
            <div className="animate-pulse space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-100 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchPageFallback />}>
      <SearchPageContent />
    </Suspense>
  );
}
