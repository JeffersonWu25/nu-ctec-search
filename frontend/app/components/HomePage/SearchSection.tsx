'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAutocomplete, AutocompleteItem } from '../../hooks/useAutocomplete';

export default function SearchSection() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { items, isLoading } = useAutocomplete(searchQuery, 5);

  // Group items by type for display
  const courseItems = items.filter(item => item.type === 'course');
  const instructorItems = items.filter(item => item.type === 'instructor');

  const handleInputChange = useCallback((value: string) => {
    setSearchQuery(value);
    setShowDropdown(value.length > 0);
  }, []);

  const handleSearch = useCallback(() => {
    setIsNavigating(true);
    // Navigate to search page with empty filters (no match scenario)
    router.push('/search');
  }, [router]);

  const handleFormSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  }, [handleSearch]);

  const handleItemSelect = useCallback((item: AutocompleteItem) => {
    setShowDropdown(false);
    setIsNavigating(true);

    // Navigate to search page with the selected filter
    if (item.type === 'course') {
      router.push(`/search?courseId=${item.id}&courseName=${encodeURIComponent(item.label)}`);
    } else {
      router.push(`/search?instructorId=${item.id}&instructorName=${encodeURIComponent(item.label)}`);
    }
  }, [router]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  }, []);

  const hasResults = items.length > 0;

  return (
    <section
      className="relative bg-gradient-to-br from-purple-50 via-white to-blue-50 min-h-screen flex items-center overflow-hidden"
      aria-labelledby="search-heading"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full">
        <div className="text-center">
          <h1 id="search-heading" className="text-h1 text-gray-900 mb-4 max-w-[500px] mx-auto">
            Have a <span className="text-purple-600">specific course</span> or instructor in mind?
          </h1>

          <form onSubmit={handleFormSubmit} className="relative max-w-4xl mx-auto" role="search">
            <div className="relative">
              <label htmlFor="course-search" className="sr-only">
                Search for courses or instructors
              </label>
              <input
                ref={searchInputRef}
                id="course-search"
                type="text"
                value={searchQuery}
                onChange={(e) => handleInputChange(e.target.value)}
                onFocus={() => searchQuery.length > 0 && setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                onKeyDown={handleKeyDown}
                placeholder="Search for courses or instructors..."
                className="w-full px-6 py-4 pr-16 text-lg border-2 border-purple-300 rounded-xl focus:outline-none focus:border-purple-500 focus:ring-4 focus:ring-purple-100 shadow-lg"
                aria-haspopup="listbox"
                aria-describedby={showDropdown ? "search-dropdown" : undefined}
              />
              <button
                type="submit"
                disabled={isNavigating}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-md disabled:opacity-50"
                aria-label="Search for courses"
              >
                {isNavigating ? (
                  <div className="animate-spin w-5 h-5 border-2 border-current border-t-transparent rounded-full" />
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                )}
              </button>
            </div>

            {showDropdown && (
              <div
                id="search-dropdown"
                className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl z-20 overflow-hidden"
              >
                {isLoading ? (
                  <div className="px-5 py-4 text-gray-500 text-sm">Searching...</div>
                ) : hasResults ? (
                  <ul role="listbox">
                    {courseItems.length > 0 && (
                      <>
                        <li className="px-5 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                          Courses
                        </li>
                        {courseItems.map((item) => (
                          <li key={item.id} role="option" aria-selected="false">
                            <button
                              type="button"
                              onClick={() => handleItemSelect(item)}
                              className="w-full px-5 py-3 text-left text-gray-700 hover:bg-purple-50 focus:bg-purple-50 border-b border-gray-100 last:border-b-0 transition-all duration-200 text-sm font-medium"
                            >
                              <div className="flex items-center gap-3">
                                <div className="w-2 h-2 bg-purple-400 rounded-full flex-shrink-0"></div>
                                <span className="truncate">{item.label}</span>
                              </div>
                            </button>
                          </li>
                        ))}
                      </>
                    )}
                    {instructorItems.length > 0 && (
                      <>
                        <li className="px-5 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                          Instructors
                        </li>
                        {instructorItems.map((item) => (
                          <li key={item.id} role="option" aria-selected="false">
                            <button
                              type="button"
                              onClick={() => handleItemSelect(item)}
                              className="w-full px-5 py-3 text-left text-gray-700 hover:bg-purple-50 focus:bg-purple-50 border-b border-gray-100 last:border-b-0 transition-all duration-200 text-sm font-medium"
                            >
                              <div className="flex items-center gap-3">
                                <div className="w-2 h-2 bg-blue-400 rounded-full flex-shrink-0"></div>
                                <span className="truncate">{item.label}</span>
                              </div>
                            </button>
                          </li>
                        ))}
                      </>
                    )}
                  </ul>
                ) : searchQuery.length > 0 ? (
                  <div className="px-5 py-4 text-gray-500 text-sm">No results found</div>
                ) : null}
              </div>
            )}
          </form>

          <p className="text-body-lg text-gray-500 mt-8">
            Search through thousands of Northwestern courses and instructor reviews
          </p>
        </div>
      </div>
    </section>
  );
}
