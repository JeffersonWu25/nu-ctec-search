'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CourseOffering } from '@/app/types/course';
import CourseHeader from '@/app/components/CourseDetail/CourseHeader';
import AtAGlance from '@/app/components/CourseDetail/AtAGlance';
import RatingSection from '@/app/components/CourseDetail/RatingSection';
import StudentComments from '@/app/components/CourseDetail/StudentComments';
import { mockCourseOffering } from '@/app/data/mockCourseOffering';

export default function CourseDetailPage() {
  const params = useParams();
  const courseOfferingId = params.courseOfferingId as string;
  const [courseOffering, setCourseOffering] = useState<CourseOffering | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCourseOffering = async () => {
      try {
        setLoading(true);
        // In production, this would be an API call
        // const response = await fetch(`/api/course-offerings/${courseOfferingId}`);
        // const data = await response.json();
        setCourseOffering(mockCourseOffering);
      } catch (error) {
        console.error('Error fetching course offering:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCourseOffering();
  }, [courseOfferingId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading course details...</div>
      </div>
    );
  }

  if (!courseOffering) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Course not found</div>
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