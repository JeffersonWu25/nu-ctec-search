import Link from 'next/link';
import { CourseOffering } from '@/app/types/course';
import { AcademicCapIcon } from '@heroicons/react/24/outline';

interface CourseInfoProps {
  courseOffering: CourseOffering;
}

export default function CourseInfo({ courseOffering }: CourseInfoProps) {
  const { instructor, quarter, year, section } = courseOffering;

  return (
    <div className="bg-neutral-50 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-4">
        <AcademicCapIcon className="h-5 w-5 text-neutral-600" />
        <h3 className="font-semibold text-neutral-900">Course Information</h3>
      </div>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center py-2 border-b border-neutral-200">
          <span className="text-neutral-600">Instructor</span>
          <Link 
            href={`/instructor/${instructor.id}`}
            className="font-medium text-primary-600 hover:underline transition-all duration-200"
          >
            {instructor.name}
          </Link>
        </div>
        
        {courseOffering.course.department && (
          <div className="flex justify-between items-center py-2 border-b border-neutral-200">
            <span className="text-neutral-600">Department</span>
            <span className="font-medium text-neutral-900">{courseOffering.course.department.name}</span>
          </div>
        )}
        
        <div className="flex justify-between items-center py-2 border-b border-neutral-200">
          <span className="text-neutral-600">Term</span>
          <span className="font-medium text-neutral-900">{quarter} {year}</span>
        </div>
        
        <div className="flex justify-between items-center py-2">
          <span className="text-neutral-600">Section</span>
          <span className="font-medium text-neutral-900">{section}</span>
        </div>
      </div>
    </div>
  );
}