'use client';

import { useParams } from 'next/navigation';
import { AcademicCapIcon, BookOpenIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import RatingSummary from '@/app/components/CourseDetail/RatingSummary';
import AISummary from '@/app/components/CourseDetail/AISummary';
import CourseCard from '@/app/components/SearchPage/CourseCard';
import { useCourse } from '@/app/hooks/useCourse';

// Hardcoded fields to be added to schema later
const HARDCODED_FIELDS = {
  universityUrl: "https://www.northwestern.edu/academics/courses/",
};

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-6xl mx-auto px-4 py-6 lg:px-6 lg:py-8 space-y-8">
        {/* Header Skeleton */}
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
          <div className="bg-primary-600 p-8">
            <div className="space-y-4">
              <div className="h-10 bg-white/30 rounded w-96 animate-pulse" />
              <div className="h-6 bg-white/20 rounded w-32 animate-pulse" />
              <div className="h-10 bg-white/20 rounded w-48 animate-pulse" />
              <div className="h-20 bg-white/20 rounded w-full animate-pulse" />
            </div>
          </div>
        </div>

        {/* Content Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-8">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 h-64 animate-pulse" />
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 h-32 animate-pulse" />
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

function CourseDetails({
  department,
  prerequisitesText,
}: {
  department: { id: string; code: string; name: string } | null;
  prerequisitesText: string | null;
}) {
  const hasContent = department || prerequisitesText;

  if (!hasContent) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
      <h2 className="font-semibold text-neutral-900 mb-4">Course Details</h2>
      <div className="space-y-4">
        {/* Department */}
        {department && (
          <div className="flex items-start space-x-3">
            <AcademicCapIcon className="h-5 w-5 text-neutral-500 mt-0.5 flex-shrink-0" />
            <div>
              <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">Department</div>
              <div className="text-sm text-neutral-900">{department.name}</div>
            </div>
          </div>
        )}

        {/* Prerequisites */}
        {prerequisitesText && (
          <div className="flex items-start space-x-3">
            <BookOpenIcon className="h-5 w-5 text-neutral-500 mt-0.5 flex-shrink-0" />
            <div>
              <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">Prerequisites</div>
              <div className="text-sm text-neutral-700">{prerequisitesText}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function RequirementsFulfilled({
  requirements,
}: {
  requirements: { id: string; name: string }[];
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
      <div className="flex items-center space-x-2 mb-3">
        <CheckCircleIcon className="h-5 w-5 text-primary-600" />
        <h2 className="font-semibold text-neutral-900">Requirements Fulfilled</h2>
      </div>
      {requirements.length === 0 ? (
        <p className="text-neutral-500 text-sm italic">No requirements data available</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {requirements.map((req) => (
            <span
              key={req.id}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
            >
              {req.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CourseProfile() {
  const params = useParams();
  const courseId = params.courseId as string;
  const { course, isLoading, error } = useCourse(courseId);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error || !course) {
    return <ErrorState message={error || 'Course not found'} />;
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-6xl mx-auto px-4 py-6 lg:px-6 lg:py-8 space-y-8">

        {/* Header Section */}
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
          <div className="bg-primary-600 p-8">
            {/* Course Info */}
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold text-white mb-2">
                {course.title}
              </h1>
              <p className="text-white opacity-90 text-lg mb-6">{course.code}</p>

              <div className="mb-6">
                <a
                  href={HARDCODED_FIELDS.universityUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 bg-white border border-white text-primary-600 hover:bg-primary-50 hover:text-primary-700 transition-colors px-4 py-2 rounded-lg font-medium text-sm"
                >
                  <span>University Course Page</span>
                </a>
              </div>

              {/* Course Description */}
              {course.description && (
                <div className="text-white opacity-80 text-sm leading-relaxed max-w-4xl">
                  {course.description}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column - Ratings, Course Details, and AI Summary */}
          <div className="lg:col-span-1 space-y-8">

            {/* Overall Course Ratings */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <h2 className="font-semibold text-neutral-900 mb-4">Overall Course Ratings</h2>
              <RatingSummary ratings={course.aggregatedRatings} />
            </div>

            {/* Course Details */}
            <CourseDetails
              department={course.department}
              prerequisitesText={course.prerequisitesText}
            />

            {/* Requirements Fulfilled */}
            <RequirementsFulfilled requirements={course.requirements} />

            {/* AI Summary */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <AISummary summary={course.aiSummary} />
            </div>
          </div>

          {/* Right Column - Course Offerings */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-neutral-900">Course Offerings</h2>
                <span className="text-sm text-neutral-500">{course.offerings.length} offerings</span>
              </div>

              {course.offerings.length === 0 ? (
                <div className="text-center py-8 text-neutral-500">
                  No course offerings found for this course.
                </div>
              ) : (
                <div className="space-y-4">
                  {course.offerings.map((offering) => (
                    <CourseCard
                      key={offering.id}
                      id={offering.id}
                      courseCode={course.code}
                      courseName={course.title}
                      instructor={offering.instructorName}
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