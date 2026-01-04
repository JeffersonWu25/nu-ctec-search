'use client';

import { SearchFiltersProvider } from '../../hooks/useSearchFilters';
import SearchFilters from './SearchFilters';
import SearchResults from './SearchResults';

export default function SearchPage() {
  return (
    <SearchFiltersProvider>
      <div className="min-h-screen bg-white">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex gap-8">
            <SearchFilters />
            <SearchResults />
          </div>
        </div>
      </div>
    </SearchFiltersProvider>
  );
}