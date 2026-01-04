'use client';

import { useRouter, useSearchParams } from 'next/navigation';

export default function RankingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const category = searchParams.get('category') || 'easy-distros';

  // Mock data for Easiest Distros (will be used for all categories for now)
  const rankingItems = [
    {
      rank: 1,
      courseName: 'Buddhist Psychology',
      courseId: 'course-1'
    },
    {
      rank: 2,
      courseName: 'Introduction to Film Studies',
      courseId: 'course-2'
    },
    {
      rank: 3,
      courseName: 'Creative Writing Workshop',
      courseId: 'course-3'
    },
    {
      rank: 4,
      courseName: 'Environmental Science Basics',
      courseId: 'course-4'
    },
    {
      rank: 5,
      courseName: 'Music Appreciation',
      courseId: 'course-5'
    },
    {
      rank: 6,
      courseName: 'Art History Survey',
      courseId: 'course-6'
    },
    {
      rank: 7,
      courseName: 'Philosophy of Ethics',
      courseId: 'course-7'
    },
    {
      rank: 8,
      courseName: 'Cultural Anthropology',
      courseId: 'course-8'
    },
    {
      rank: 9,
      courseName: 'World Literature',
      courseId: 'course-9'
    },
    {
      rank: 10,
      courseName: 'Social Psychology',
      courseId: 'course-10'
    }
  ];

  const getCategoryTitle = (cat: string) => {
    switch (cat) {
      case 'easy-distros':
        return 'Easiest Distros';
      case 'top-courses':
        return 'Top Courses';
      case 'stem-favorites':
        return 'STEM Favorites';
      case 'high-ratings':
        return 'High Ratings';
      case 'quick-credits':
        return 'Quick Credits';
      case 'professors-choice':
        return 'Professors Choice';
      default:
        return 'Easiest Distros';
    }
  };

  const handleCourseClick = (courseId: string) => {
    router.push(`/course-profile/${courseId}`);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-4xl mx-auto px-4 py-8 lg:px-6 lg:py-12">
        
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {getCategoryTitle(category)}
          </h1>
          <p className="text-lg text-gray-600">
            Discover Northwestern's most popular courses in this category
          </p>
        </div>

        {/* Rankings List */}
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
          <div className="p-6">
            <div className="space-y-4">
              {rankingItems.map((item) => (
                <div
                  key={item.rank}
                  onClick={() => handleCourseClick(item.courseId)}
                  className="flex items-center p-4 border border-gray-200 rounded-lg hover:shadow-md hover:bg-gray-50 transition-all duration-200 cursor-pointer group"
                >
                  <div className="flex items-center justify-center w-12 h-12 bg-primary-600 text-white font-bold text-lg rounded-lg mr-4 flex-shrink-0">
                    {item.rank}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
                      {item.courseName}
                    </h3>
                  </div>
                  <div className="text-gray-400 group-hover:text-gray-600 transition-colors duration-200">
                    →
                  </div>
                </div>
              ))}
            </div>

            {/* Show more indicator */}
            <div className="mt-8 text-center">
              <div className="flex justify-center items-center space-x-2 text-gray-400">
                <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
              </div>
              <p className="text-sm text-gray-500 mt-2">More courses available</p>
            </div>
          </div>
        </div>

        {/* Back to Explore */}
        <div className="mt-8 text-center">
          <button
            onClick={() => router.push('/')}
            className="inline-flex items-center px-6 py-3 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors duration-200"
          >
            ← Back to Explore
          </button>
        </div>
      </div>
    </div>
  );
}