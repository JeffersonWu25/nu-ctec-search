'use client';

import { useRouter } from 'next/navigation';

interface CourseCardProps {
  courseCode: string;
  courseName: string;
  instructor: string;
  term: string;
  overallRating: number;
  workloadRating: number;
  teachingRating: number;
  courseOfferingId?: string;
}

export default function CourseCard({
  courseCode,
  courseName,
  instructor,
  term,
  overallRating,
  teachingRating,
  courseOfferingId = 'offering-123' // Default to mock ID for now
}: CourseCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/course/${courseOfferingId}`);
  };

  return (
    <div 
      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer bg-white"
      onClick={handleClick}
    >
      {/* Course Title */}
      <h3 className="font-semibold text-gray-900 text-lg mb-2">{courseName}</h3>
      
      {/* Course Code */}
      <div className="mb-3">
        <span className="bg-primary-600 text-white px-3 py-1 rounded text-sm font-medium">
          {courseCode}
        </span>
      </div>
      
      {/* Instructor and Term */}
      <p className="text-sm text-gray-600 mb-4">
        {instructor}
      </p>
      <p className="text-sm text-gray-500 mb-4">
        {term}
      </p>
      
      {/* Rating Metrics */}
      <div className="flex justify-between items-center text-sm">
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase mb-1">Overall</div>
          <div className="font-semibold text-orange-500">{overallRating.toFixed(1)}/6</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase mb-1">Hours/Week</div>
          <div className="font-semibold text-teal-500">4 - 7</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase mb-1">Teaching</div>
          <div className="font-semibold text-orange-500">{teachingRating.toFixed(1)}/6</div>
        </div>
      </div>
    </div>
  );
}