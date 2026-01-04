'use client';

import { useRouter } from 'next/navigation';

interface CourseOfferingRecommendationCardProps {
  courseOfferingId: string;
  courseCode: string;
  courseName: string;
  instructor: string;
  term: string;
  overallRating?: number;
  teachingRating?: number;
}

export default function CourseOfferingRecommendationCard({
  courseOfferingId,
  courseCode,
  courseName,
  instructor,
  term,
  overallRating,
  teachingRating
}: CourseOfferingRecommendationCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/course/${courseOfferingId}`);
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
      
      <div className="mb-2">
        <span className="bg-primary-600 text-white px-2 py-1 rounded text-xs font-medium">
          {courseCode}
        </span>
      </div>
      
      <div className="mb-2 text-sm text-gray-600">
        <p>{instructor} • {term}</p>
      </div>

      {(overallRating || teachingRating) && (
        <div className="flex gap-4 text-xs">
          {overallRating && (
            <div>
              <span className="text-gray-500">Overall: </span>
              <span className="font-medium text-orange-500">{overallRating}/6</span>
            </div>
          )}
          {teachingRating && (
            <div>
              <span className="text-gray-500">Teaching: </span>
              <span className="font-medium text-orange-500">{teachingRating}/6</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}