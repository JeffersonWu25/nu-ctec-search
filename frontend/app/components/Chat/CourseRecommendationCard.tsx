'use client';

import { useRouter } from 'next/navigation';

interface CourseRecommendationCardProps {
  courseId: string;
  courseCode?: string;
  courseName: string;
  description?: string;
}

export default function CourseRecommendationCard({
  courseId,
  courseCode,
  courseName,
  description
}: CourseRecommendationCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/course-profile/${courseId}`);
  };

  return (
    <div
      onClick={handleClick}
      className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-primary-500 hover:shadow-md transition-all duration-200 cursor-pointer group max-w-sm"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
          {courseName}
        </h3>
        <div className="text-gray-400 group-hover:text-primary-600 transition-colors duration-200">
          →
        </div>
      </div>
      
      {courseCode && (
        <div className="mb-2">
          <span className="bg-primary-600 text-white px-2 py-1 rounded text-xs font-medium">
            {courseCode}
          </span>
        </div>
      )}
      
      {description && (
        <p className="text-sm text-gray-600 line-clamp-2">
          {description}
        </p>
      )}
    </div>
  );
}