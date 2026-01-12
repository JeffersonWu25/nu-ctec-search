'use client';

import { useRouter } from 'next/navigation';

interface CourseCardProps {
  id: string;
  courseCode: string;
  courseName: string;
  instructor: string;
  quarter: string;
  year: number;
  overallRating: number | null;
  hoursPerWeek: string | null;
  teachingRating: number | null;
}

export default function CourseCard({
  id,
  courseCode,
  courseName,
  instructor,
  quarter,
  year,
  overallRating,
  hoursPerWeek,
  teachingRating,
}: CourseCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/course/${id}`);
  };

  const formatRating = (rating: number | null): string => {
    if (rating === null) return 'N/A';
    return rating.toFixed(1);
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
      <p className="text-sm text-gray-600 mb-1">{instructor}</p>
      <p className="text-sm text-gray-500 mb-4">{quarter} {year}</p>

      {/* Rating Metrics */}
      <div className="flex justify-between items-center text-sm">
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase mb-1">Overall</div>
          <div className={`font-semibold ${overallRating !== null ? 'text-orange-500' : 'text-gray-400'}`}>
            {formatRating(overallRating)}{overallRating !== null && '/6'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase mb-1">Hours/Week</div>
          <div className={`font-semibold ${hoursPerWeek ? 'text-teal-500' : 'text-gray-400'}`}>
            {hoursPerWeek || 'N/A'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 uppercase mb-1">Teaching</div>
          <div className={`font-semibold ${teachingRating !== null ? 'text-orange-500' : 'text-gray-400'}`}>
            {formatRating(teachingRating)}{teachingRating !== null && '/6'}
          </div>
        </div>
      </div>
    </div>
  );
}
