'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CourseOffering } from '@/app/types/course';
import CourseHeader from '@/app/components/CourseDetail/CourseHeader';
import AtAGlance from '@/app/components/CourseDetail/AtAGlance';
import RatingSection from '@/app/components/CourseDetail/RatingSection';
import StudentComments from '@/app/components/CourseDetail/StudentComments';

export default function CourseDetailPage() {
  const params = useParams();
  const courseOfferingId = params.courseOfferingId as string;
  const [courseOffering, setCourseOffering] = useState<CourseOffering | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCourseOffering = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/course-offerings/${courseOfferingId}`);
        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || 'Failed to fetch course offering');
        }

        setCourseOffering(result.data);
      } catch (err) {
        console.error('Error fetching course offering:', err);
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (courseOfferingId) {
      fetchCourseOffering();
    }
  }, [courseOfferingId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading course details...</div>
      </div>
    );
  }

  if (error || !courseOffering) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">{error || 'Course not found'}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-6xl mx-auto px-4 py-6 lg:px-6 lg:py-8 space-y-8">
        <CourseHeader courseOffering={courseOffering} />
        <AtAGlance courseOffering={courseOffering} />
        <RatingSection ratings={courseOffering.ratings} />
        <StudentComments
          comments={courseOffering.comments}
          courseOfferingId={courseOffering.id}
        />
      </div>
    </div>
  );
}