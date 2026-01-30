'use client';

import { useRouter } from 'next/navigation';

interface CourseRecommendationCardProps {
  courseId: string;
  courseCode?: string;
  courseName: string;
  description?: string;
  courseRating?: number | null;
  instructionRating?: number | null;
  hoursPerWeek?: string | null;
  similarityScore?: number | null;
  matchingSnippets?: string[];
}

export default function CourseRecommendationCard({
  courseId,
  courseCode,
  courseName,
  description,
  courseRating,
  instructionRating,
  hoursPerWeek,
  similarityScore,
  matchingSnippets
}: CourseRecommendationCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/course-profile/${courseId}`);
  };

  return (
    <div
      onClick={handleClick}
      className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-primary-500 hover:shadow-md transition-all duration-200 cursor-pointer group w-full max-w-md"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
          {courseName}
        </h3>
        <div className="text-gray-400 group-hover:text-primary-600 transition-colors duration-200">
          →
        </div>
      </div>

      <div className="flex items-center gap-2 mb-2 flex-wrap">
        {courseCode && (
          <span className="bg-primary-600 text-white px-2 py-1 rounded text-xs font-medium">
            {courseCode}
          </span>
        )}
        {similarityScore && (
          <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
            {Math.round(similarityScore * 100)}% match
          </span>
        )}
      </div>

      {/* Ratings row */}
      {(courseRating || instructionRating || hoursPerWeek) && (
        <div className="flex items-center gap-3 mb-2 text-xs text-gray-600">
          {courseRating && (
            <span title="Course Rating">
              <span className="font-medium">Course:</span> {courseRating.toFixed(1)}/6
            </span>
          )}
          {instructionRating && (
            <span title="Instruction Rating">
              <span className="font-medium">Teaching:</span> {instructionRating.toFixed(1)}/6
            </span>
          )}
          {hoursPerWeek && (
            <span title="Hours per Week">
              <span className="font-medium">Hours:</span> {hoursPerWeek}
            </span>
          )}
        </div>
      )}

      {description && (
        <p className="text-sm text-gray-600 line-clamp-2 mb-2">
          {description}
        </p>
      )}

      {/* Matching snippets */}
      {matchingSnippets && matchingSnippets.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1">What students said:</p>
          <p className="text-xs text-gray-600 italic line-clamp-2">
            &ldquo;{matchingSnippets[0].slice(0, 120)}{matchingSnippets[0].length > 120 ? '...' : ''}&rdquo;
          </p>
        </div>
      )}
    </div>
  );
}