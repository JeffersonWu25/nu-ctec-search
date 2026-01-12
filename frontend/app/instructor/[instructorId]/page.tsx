'use client';

import { useParams } from 'next/navigation';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import RatingSummary from '@/app/components/CourseDetail/RatingSummary';
import AISummary from '@/app/components/CourseDetail/AISummary';
import CourseCard from '@/app/components/SearchPage/CourseCard';
import { useInstructor } from '@/app/hooks/useInstructor';

// Hardcoded fields to be added to schema later
const HARDCODED_FIELDS = {
  title: "Professor",
  email: "N/A",
  office: "N/A",
  officeHours: "N/A",
  northwesternProfileUrl: "https://www.mccormick.northwestern.edu/research-faculty/directory/profiles/",
};

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-6xl mx-auto px-4 py-6 lg:px-6 lg:py-8 space-y-8">
        {/* Header Skeleton */}
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
          <div className="bg-primary-600 p-8">
            <div className="flex items-center gap-8">
              <div className="w-32 h-32 bg-gray-400 rounded-full animate-pulse" />
              <div className="flex-1 space-y-4">
                <div className="h-10 bg-white/30 rounded w-64 animate-pulse" />
                <div className="h-6 bg-white/20 rounded w-32 animate-pulse" />
                <div className="space-y-2">
                  <div className="h-4 bg-white/20 rounded w-48 animate-pulse" />
                  <div className="h-4 bg-white/20 rounded w-40 animate-pulse" />
                  <div className="h-4 bg-white/20 rounded w-44 animate-pulse" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-8">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 h-64 animate-pulse" />
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 h-48 animate-pulse" />
          </div>
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="border border-gray-200 rounded-lg p-4 animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-3/4 mb-3" />
                    <div className="h-8 bg-gray-100 rounded w-32 mb-3" />
                    <div className="h-4 bg-gray-100 rounded w-1/4 mb-4" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
      <div className="text-center">
        <div className="text-red-500 text-xl mb-2">Error</div>
        <div className="text-gray-600">{message}</div>
      </div>
    </div>
  );
}

export default function InstructorProfile() {
  const params = useParams();
  const instructorId = params.instructorId as string;
  const { instructor, isLoading, error } = useInstructor(instructorId);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !instructor) {
    return <ErrorState message={error || 'Instructor not found'} />;
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-6xl mx-auto px-4 py-6 lg:px-6 lg:py-8 space-y-8">

        {/* Header Section */}
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
          <div className="bg-primary-600 p-8">
            {/* Instructor Info */}
            <div className="flex items-center gap-8">
              <div className="w-32 h-32 relative flex-shrink-0 bg-gray-300 rounded-full flex items-center justify-center overflow-hidden">
                {instructor.profile_photo ? (
                  <img
                    src={instructor.profile_photo}
                    alt={instructor.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <svg className="w-16 h-16 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>
                )}
              </div>

              <div className="flex-1">
                <h1 className="text-3xl lg:text-4xl font-bold text-white mb-2">
                  {instructor.name}
                </h1>
                <p className="text-white opacity-90 text-lg mb-4">{HARDCODED_FIELDS.title}</p>

                <div className="space-y-2 text-white opacity-80 mb-6">
                  <div className="text-sm"><span className="font-medium">Email:</span> {HARDCODED_FIELDS.email}</div>
                  <div className="text-sm"><span className="font-medium">Office:</span> {HARDCODED_FIELDS.office}</div>
                  <div className="text-sm"><span className="font-medium">Office Hours:</span> {HARDCODED_FIELDS.officeHours}</div>
                </div>

                <a
                  href={HARDCODED_FIELDS.northwesternProfileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 bg-white border border-white text-primary-600 hover:bg-primary-50 hover:text-primary-700 transition-colors px-4 py-2 rounded-lg font-medium text-sm"
                >
                  <span>View Northwestern Profile</span>
                  <ArrowLeftIcon className="h-4 w-4 rotate-180" />
                </a>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column - Ratings and AI Summary */}
          <div className="lg:col-span-1 space-y-8">

            {/* Overall Teaching Ratings */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <h2 className="font-semibold text-neutral-900 mb-4">Overall Teaching Ratings</h2>
              <RatingSummary ratings={instructor.aggregatedRatings} />
            </div>

            {/* AI Summary */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <AISummary summary={instructor.aiSummary} />
            </div>
          </div>

          {/* Right Column - Courses Taught */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-neutral-900">Courses Taught</h2>
                <span className="text-sm text-neutral-500">{instructor.offerings.length} courses</span>
              </div>

              {instructor.offerings.length === 0 ? (
                <div className="text-center py-8 text-neutral-500">
                  No course offerings found for this instructor.
                </div>
              ) : (
                <div className="space-y-4">
                  {instructor.offerings.map((offering) => (
                    <CourseCard
                      key={offering.id}
                      id={offering.id}
                      courseCode={offering.courseCode}
                      courseName={offering.courseName}
                      instructor={instructor.name}
                      quarter={offering.quarter}
                      year={offering.year}
                      overallRating={offering.overallRating}
                      hoursPerWeek={offering.hoursPerWeek}
                      teachingRating={offering.teachingRating}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}