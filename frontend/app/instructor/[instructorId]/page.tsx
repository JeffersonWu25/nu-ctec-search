'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useParams } from 'next/navigation';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import RatingSummary from '@/app/components/CourseDetail/RatingSummary';
import AISummary from '@/app/components/CourseDetail/AISummary';
import CourseCard from '@/app/components/SearchPage/CourseCard';

export default function InstructorProfile() {
  const params = useParams();
  const instructorId = params.instructorId as string;

  // Hard-coded instructor data
  const instructor = {
    id: instructorId,
    name: "Sruti Bhagavatula",
    title: "Professor",
    email: "N/A",
    office: "N/A",
    officeHours: "N/A",
    profilePhoto: "/next.svg",
    northwesternProfileUrl: "https://www.mccormick.northwestern.edu/research-faculty/directory/profiles/bhagavatula-sruti.html"
  };

  // Mock rating data formatted for RatingSummary component
  const mockRatings = [
    {
      id: "1",
      surveyQuestion: { id: "1", question: "overall rating of the instruction" },
      distribution: [],
      mean: 4.5,
      responseCount: 100
    },
    {
      id: "2", 
      surveyQuestion: { id: "2", question: "overall rating of the course" },
      distribution: [],
      mean: 4.5,
      responseCount: 100
    },
    {
      id: "3",
      surveyQuestion: { id: "3", question: "how much you learned" },
      distribution: [],
      mean: 4.9,
      responseCount: 100
    },
    {
      id: "4",
      surveyQuestion: { id: "4", question: "challenging you intellectually" },
      distribution: [],
      mean: 4.5,
      responseCount: 100
    },
    {
      id: "5",
      surveyQuestion: { id: "5", question: "stimulating your interest" },
      distribution: [],
      mean: 4.4,
      responseCount: 100
    }
  ];

  const aiSummary = `Professor Sruti is widely praised as an amazing, excellent, engaging, clear, and supportive instructor who helps students understand concepts. Her teaching style is largely considered helpful, though some students found her lectures fast or occasionally unclear. Professor Sruti implements a unique "modifier" grading system with multiple resubmissions on assignments. Many students appreciate this system for its leniency, flexibility, and focus on learning, finding that it makes an A achievable. However, some found this grading approach confusing or occasionally punitive for minor errors. Overall, Professor Sruti is highly recommended by students.`;

  const coursesTaught = [
    {
      courseCode: "COMP_SCI_214-0",
      courseName: "Data Structures & Algorithms", 
      instructor: "Unknown Instructor",
      term: "WINTER 2024",
      overallRating: 4.5,
      workloadRating: 4.0,
      teachingRating: 4.8,
      courseOfferingId: "offering-1"
    },
    {
      courseCode: "COMP_SCI_214-0",
      courseName: "Data Structures & Algorithms",
      instructor: "Unknown Instructor", 
      term: "WINTER 2025",
      overallRating: 4.5,
      workloadRating: 4.0,
      teachingRating: 4.5,
      courseOfferingId: "offering-2"
    }
  ];

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-6xl mx-auto px-4 py-6 lg:px-6 lg:py-8 space-y-8">
        
        {/* Header Section */}
        <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
          <div className="bg-primary-600 p-8">
            {/* Instructor Info */}
            <div className="flex items-center gap-8">
              <div className="w-32 h-32 relative flex-shrink-0 bg-gray-300 rounded-full flex items-center justify-center">
                <svg className="w-16 h-16 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
              </div>
              
              <div className="flex-1">
                <h1 className="text-3xl lg:text-4xl font-bold text-white mb-2">
                  {instructor.name}
                </h1>
                <p className="text-white opacity-90 text-lg mb-4">{instructor.title}</p>
                
                <div className="space-y-2 text-white opacity-80 mb-6">
                  <div className="text-sm"><span className="font-medium">Email:</span> {instructor.email}</div>
                  <div className="text-sm"><span className="font-medium">Office:</span> {instructor.office}</div>
                  <div className="text-sm"><span className="font-medium">Office Hours:</span> {instructor.officeHours}</div>
                </div>

                <a
                  href={instructor.northwesternProfileUrl}
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
              <RatingSummary ratings={mockRatings} />
            </div>

            {/* AI Summary */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <AISummary summary={aiSummary} />
            </div>
          </div>

          {/* Right Column - Courses Taught */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-neutral-900">Courses Taught</h2>
                <span className="text-sm text-neutral-500">{coursesTaught.length} courses</span>
              </div>

              <div className="space-y-4">
                {coursesTaught.map((course, index) => (
                  <CourseCard
                    key={index}
                    courseCode={course.courseCode}
                    courseName={course.courseName}
                    instructor={course.instructor}
                    term={course.term}
                    overallRating={course.overallRating}
                    workloadRating={course.workloadRating}
                    teachingRating={course.teachingRating}
                    courseOfferingId={course.courseOfferingId}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}