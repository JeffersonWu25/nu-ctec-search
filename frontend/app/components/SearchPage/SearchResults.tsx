'use client';

import { useInfiniteScroll } from '../../hooks/useInfiniteScroll';
import { useSearchFilters } from '../../hooks/useSearchFilters';
import CourseCard from './CourseCard';
import { Course } from '../../types/course';

// Mock data - keeping it hardcoded as requested
const MOCK_COURSES: Course[] = Array.from({ length: 25 }, (_, i) => ({
  id: `course-${i + 1}`,
  courseCode: i % 3 === 0 ? 'COMP_SCI 214' : i % 3 === 1 ? 'MATH 230' : 'EECS 111',
  courseName: i % 3 === 0 ? 'Data Struct & Alg 0' : i % 3 === 1 ? 'Multivariable Calculus' : 'Fundamentals of Programming',
  instructor: i % 4 === 0 ? 'Shruti Barg' : i % 4 === 1 ? 'Vincent St-Amour' : i % 4 === 2 ? 'Jane Smith' : 'John Doe',
  term: i % 2 === 0 ? 'Winter 25' : 'Fall 24',
  overallRating: 4.0 + (i % 10) * 0.1,
  workloadRating: 3.5 + (i % 8) * 0.1,
  teachingRating: 4.2 + (i % 6) * 0.1
}));

export default function SearchResults() {
  const { hasActiveFilters } = useSearchFilters();
  const { 
    visibleCourses, 
    totalResults, 
    displayedCount, 
    isLoading, 
    hasMoreResults, 
    resultsEndRef 
  } = useInfiniteScroll({
    allCourses: MOCK_COURSES,
    hasActiveFilters
  });

  return (
    <div className="flex-1">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Search Results ({Math.min(displayedCount, totalResults)} of {totalResults})
        </h1>
        
        {!hasActiveFilters && (
          <div className="text-center py-16">
            <div className="text-gray-400 text-lg mb-2">No filters applied</div>
            <div className="text-gray-500">
              Select courses or instructors to see CTEC reviews and ratings.
            </div>
          </div>
        )}
      </div>

      {hasActiveFilters && (
        <>
          <div className="space-y-4">
            {visibleCourses.map((course) => (
              <CourseCard
                key={course.id}
                courseCode={course.courseCode}
                courseName={course.courseName}
                instructor={course.instructor}
                term={course.term}
                overallRating={course.overallRating}
                workloadRating={course.workloadRating}
                teachingRating={course.teachingRating}
              />
            ))}
          </div>

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-center py-8">
              <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full"></div>
            </div>
          )}

          {/* Intersection observer target */}
          <div ref={resultsEndRef} className="h-4"></div>

          {/* End of results indicator */}
          {!hasMoreResults && totalResults > 10 && (
            <div className="text-center py-8 text-gray-500">
              You&apos;ve reached the end of the results
            </div>
          )}
        </>
      )}
    </div>
  );
}