'use client';

import { useRouter } from 'next/navigation';

interface ProfessorRecommendationCardProps {
  instructorId: string;
  professorName: string;
  courseName: string;
  description?: string;
}

export default function ProfessorRecommendationCard({
  instructorId,
  professorName,
  courseName,
  description
}: ProfessorRecommendationCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/instructor/${instructorId}`);
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
        <p className="text-sm text-gray-700">
          <span className="font-medium">Professor:</span> {professorName}
        </p>
      </div>
      
      {description && (
        <p className="text-sm text-gray-600 line-clamp-2">
          {description}
        </p>
      )}
    </div>
  );
}