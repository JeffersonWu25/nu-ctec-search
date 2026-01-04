'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';

const MOCK_COURSES = [
  "EECS 111 - Fundamentals of Computer Programming I",
  "EECS 211 - Fundamentals of Computer Programming II", 
  "EECS 214 - Data Structures and Data Management",
  "MATH 230 - Multivariable Differential Calculus",
  "STAT 202 - Introduction to Statistics",
  "CHEM 171 - General Chemistry",
  "PHYS 135 - General Physics",
];

export default function SearchSection() {
  const router = useRouter();
  const [specificSearch, setSpecificSearch] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [debounceTimeout, setDebounceTimeout] = useState<NodeJS.Timeout | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const filteredCourses = MOCK_COURSES.filter(course =>
    course.toLowerCase().includes(specificSearch.toLowerCase()) && specificSearch.length > 0
  );

  const handleInputChange = useCallback((value: string) => {
    setSpecificSearch(value);
    
    if (debounceTimeout) {
      clearTimeout(debounceTimeout);
    }
    
    const newTimeout = setTimeout(() => {
      setShowDropdown(value.length > 0);
    }, 250);
    
    setDebounceTimeout(newTimeout);
  }, [debounceTimeout]);

  const handleSearch = useCallback(async () => {
    if (specificSearch.trim()) {
      setIsLoading(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 500));
        router.push(`/search?q=${encodeURIComponent(specificSearch)}`);
      } catch {
        router.push('/error');
      } finally {
        setIsLoading(false);
      }
    }
  }, [specificSearch, router]);

  const handleFormSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  }, [handleSearch]);

  const handleCourseSelect = useCallback((course: string) => {
    setSpecificSearch(course);
    setShowDropdown(false);
    searchInputRef.current?.focus();
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  }, []);

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
                value={specificSearch}
                onChange={(e) => handleInputChange(e.target.value)}
                onFocus={() => specificSearch.length > 0 && setShowDropdown(true)}
                onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                onKeyDown={handleKeyDown}
                placeholder="Search for courses or instructors..."
                className="w-full px-6 py-4 pr-16 text-lg border-2 border-purple-300 rounded-xl focus:outline-none focus:border-purple-500 focus:ring-4 focus:ring-purple-100 shadow-lg"
                aria-haspopup="listbox"
                aria-describedby={showDropdown ? "search-dropdown" : undefined}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors shadow-md disabled:opacity-50"
                aria-label="Search for courses"
              >
                {isLoading ? (
                  <div className="animate-spin w-5 h-5 border-2 border-current border-t-transparent rounded-full" />
                ) : (
                  '🔍'
                )}
              </button>
            </div>
            
            {showDropdown && filteredCourses.length > 0 && (
              <ul
                id="search-dropdown"
                role="listbox"
                className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl z-20 max-h-60 overflow-y-auto"
              >
                {filteredCourses.map((course, index) => (
                  <li key={index} role="option" aria-selected="false">
                    <button
                      type="button"
                      onClick={() => handleCourseSelect(course)}
                      className="w-full px-5 py-3 text-left text-gray-700 hover:bg-purple-50 focus:bg-purple-50 border-b border-gray-100 last:border-b-0 transition-all duration-200 text-sm font-medium"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                        <span>{course}</span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
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