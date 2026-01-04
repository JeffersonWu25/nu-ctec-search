'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import RatingSummary from '@/app/components/CourseDetail/RatingSummary';
import AISummary from '@/app/components/CourseDetail/AISummary';
import CourseCard from '@/app/components/SearchPage/CourseCard';

export default function CourseProfile() {
  const params = useParams();
  const courseId = params.courseId as string;

  // Hard-coded course data
  const course = {
    id: courseId,
    code: "COMP_SCI_214",
    title: "Data Structures and Algorithms",
    description: "This course introduces fundamental data structures and algorithms for organizing and processing information. Topics include arrays, lists, stacks, queues, trees, graphs, and algorithmic techniques including divide-and-conquer, dynamic programming, and greedy algorithms.",
    university: "Northwestern University",
    universityUrl: "https://www.northwestern.edu/academics/courses/data-structures-algorithms.html"
  };

  // Mock overall rating data for the course across all offerings
  const mockRatings = [
    {
      id: "1",
      surveyQuestion: { id: "1", question: "overall rating of the instruction" },
      distribution: [],
      mean: 4.5,
      responseCount: 250
    },
    {
      id: "2", 
      surveyQuestion: { id: "2", question: "overall rating of the course" },
      distribution: [],
      mean: 4.3,
      responseCount: 250
    },
    {
      id: "3",
      surveyQuestion: { id: "3", question: "how much you learned" },
      distribution: [],
      mean: 4.7,
      responseCount: 250
    },
    {
      id: "4",
      surveyQuestion: { id: "4", question: "challenging you intellectually" },
      distribution: [],
      mean: 4.8,
      responseCount: 250
    },
    {
      id: "5",
      surveyQuestion: { id: "5", question: "stimulating your interest" },
      distribution: [],
      mean: 4.2,
      responseCount: 250
    }
  ];

  const aiSummary = `Data Structures and Algorithms is consistently rated as a challenging but rewarding course that builds essential programming foundations. Students appreciate the comprehensive coverage of fundamental concepts like trees, graphs, and algorithmic thinking. The course is praised for its practical applications and strong preparation for technical interviews. While the workload is significant, students find the material engaging and well-structured. Many note that the course significantly improves their problem-solving abilities and coding skills. The variety of instructors brings different teaching styles, but the core curriculum remains consistently high-quality across all sections.`;

  // Course offerings (different instructors/terms)
  const courseOfferings = [
    {
      courseCode: "COMP_SCI_214-0",
      courseName: "Data Structures & Algorithms", 
      instructor: "Sruti Bhagavatula",
      term: "WINTER 2025",
      overallRating: 4.5,
      workloadRating: 4.0,
      teachingRating: 4.5,
      courseOfferingId: "offering-1"
    },
    {
      courseCode: "COMP_SCI_214-0",
      courseName: "Data Structures & Algorithms",
      instructor: "Vincent St-Amour", 
      term: "WINTER 2025",
      overallRating: 4.5,
      workloadRating: 4.0,
      teachingRating: 4.5,
      courseOfferingId: "offering-2"
    },
    {
      courseCode: "COMP_SCI_214-0",
      courseName: "Data Structures & Algorithms",
      instructor: "Sruti Bhagavatula", 
      term: "FALL 2024",
      overallRating: 4.5,
      workloadRating: 4.0,
      teachingRating: 4.5,
      courseOfferingId: "offering-3"
    }
  ];

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
                  href={course.universityUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 bg-white border border-white text-primary-600 hover:bg-primary-50 hover:text-primary-700 transition-colors px-4 py-2 rounded-lg font-medium text-sm"
                >
                  <span>University Course Page</span>
                </a>
              </div>

              {/* Course Description */}
              <div className="text-white opacity-80 text-sm leading-relaxed max-w-4xl">
                {course.description}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column - Ratings and AI Summary */}
          <div className="lg:col-span-1 space-y-8">
            
            {/* Overall Course Ratings */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <h2 className="font-semibold text-neutral-900 mb-4">Overall Course Ratings</h2>
              <RatingSummary ratings={mockRatings} />
            </div>

            {/* AI Summary */}
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <AISummary summary={aiSummary} />
            </div>
          </div>

          {/* Right Column - Course Offerings */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold text-neutral-900">Course Offerings</h2>
                <span className="text-sm text-neutral-500">{courseOfferings.length} courses</span>
              </div>

              <div className="space-y-4">
                {courseOfferings.map((offering, index) => (
                  <CourseCard
                    key={index}
                    courseCode={offering.courseCode}
                    courseName={offering.courseName}
                    instructor={offering.instructor}
                    term={offering.term}
                    overallRating={offering.overallRating}
                    workloadRating={offering.workloadRating}
                    teachingRating={offering.teachingRating}
                    courseOfferingId={offering.courseOfferingId}
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