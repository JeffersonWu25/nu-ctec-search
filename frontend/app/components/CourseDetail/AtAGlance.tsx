import { CourseOffering } from '@/app/types/course';
import CourseInfo from './CourseInfo';
import RatingSummary from './RatingSummary';
import RequirementsFulfilled from './RequirementsFulfilled';
import AISummary from './AISummary';

interface AtAGlanceProps {
  courseOffering: CourseOffering;
}

export default function AtAGlance({ courseOffering }: AtAGlanceProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
      <h2 className="text-xl font-bold text-neutral-900 mb-6">At a Glance</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          <CourseInfo courseOffering={courseOffering} />
          <RequirementsFulfilled requirements={courseOffering.requirements} />
        </div>
        
        {/* Right Column */}
        <div className="space-y-6">
          <RatingSummary ratings={courseOffering.ratings} />
          <AISummary summary={courseOffering.aiSummary} />
        </div>
      </div>
    </div>
  );
}