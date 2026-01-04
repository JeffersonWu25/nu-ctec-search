import Link from 'next/link';
import { CourseOffering } from '@/app/types/course';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

interface CourseHeaderProps {
  courseOffering: CourseOffering;
}

export default function CourseHeader({ courseOffering }: CourseHeaderProps) {
  const { course, instructor, quarter, year, section } = courseOffering;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
      <div className="bg-primary-600 p-6">
        {/* Back to Search Button */}
        <div className="mb-6">
          <Link
            href="/search"
            className="inline-flex items-center space-x-2 bg-white border border-white text-primary-600 hover:bg-primary-50 hover:text-primary-700 transition-colors px-4 py-2 rounded-lg font-medium"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            <span className="text-sm">Back to Search</span>
          </Link>
        </div>

        {/* Course Title */}
        <div className="mb-4">
          <Link href={`/course-profile/${course.id}`}>
            <h1 className="text-3xl lg:text-4xl font-bold text-white mb-2 hover:underline cursor-pointer transition-all duration-200">
              {course.title}
            </h1>
          </Link>
        </div>

        {/* Course Code and Instructor */}
        <div className="mb-6 flex items-center flex-wrap gap-4">
          <Link href={`/course-profile/${course.id}`}>
            <div className="bg-white bg-opacity-10 backdrop-blur-sm border border-white rounded-lg px-4 py-2 text-primary-600 font-medium hover:bg-opacity-20 transition-all duration-200 cursor-pointer">
              {course.code}
            </div>
          </Link>
          <div className="text-white">
            with <Link 
              href={`/instructor/${instructor.id}`}
              className="font-medium text-white hover:underline transition-all duration-200"
            >
              {instructor.name}
            </Link>
          </div>
        </div>

        {/* Course Details Tags */}
        <div className="flex flex-wrap gap-3">
          <div className="bg-secondary-500 rounded-lg px-4 py-2 text-white font-medium text-sm">
            📚 McCormick
          </div>
          <div className="bg-green-500 rounded-lg px-4 py-2 text-white font-medium text-sm">
            📅 {quarter} {year}
          </div>
          <div className="bg-orange-500 rounded-lg px-4 py-2 text-white font-medium text-sm">
            📝 Section {section}
          </div>
        </div>
      </div>
    </div>
  );
}