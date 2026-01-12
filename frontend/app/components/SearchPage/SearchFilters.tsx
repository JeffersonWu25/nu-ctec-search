'use client';

import { useSearchFilters } from '../../hooks/useSearchFilters';
import { useFilterOptions } from '../../hooks/useFilterOptions';
import MultiSelectDropdown from './MultiSelectDropdown';

const SORT_OPTIONS = [
  'Recency',
  'Overall Rating',
  'Teaching Rating',
  'Ease',
];

export default function SearchFilters() {
  const { filters, updateFilter, updateSortBy, clearFilters } = useSearchFilters();
  const { departments, courses, instructors, requirements, isLoading } = useFilterOptions();

  return (
    <div className="w-80 flex-shrink-0">
      <div className="bg-white border border-gray-200 rounded-lg p-6 sticky top-24">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Filters</h2>

        {isLoading ? (
          <div className="space-y-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 w-24 bg-gray-200 rounded mb-2"></div>
                <div className="h-10 bg-gray-100 rounded"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-6">
            <MultiSelectDropdown
              label="Academic Subject"
              placeholder="Select subjects..."
              options={departments}
              selectedOptions={filters.subjects}
              onSelectionChange={(value) => updateFilter('subjects', value)}
            />

            <MultiSelectDropdown
              label="Course"
              placeholder="Select courses..."
              options={courses}
              selectedOptions={filters.courses}
              onSelectionChange={(value) => updateFilter('courses', value)}
            />

            <MultiSelectDropdown
              label="Instructor"
              placeholder="Select instructors..."
              options={instructors}
              selectedOptions={filters.instructors}
              onSelectionChange={(value) => updateFilter('instructors', value)}
            />

            <MultiSelectDropdown
              label="Course Requirements"
              placeholder="Select requirements..."
              options={requirements}
              selectedOptions={filters.requirements}
              onSelectionChange={(value) => updateFilter('requirements', value)}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort by
              </label>
              <div className="relative">
                <select
                  value={filters.sortBy}
                  onChange={(e) => updateSortBy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white appearance-none text-sm"
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            <button
              onClick={clearFilters}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Clear all filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
