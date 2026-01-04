import { Requirement } from '@/app/types/course';
import { CheckCircleIcon } from '@heroicons/react/24/solid';

interface RequirementsFulfilledProps {
  requirements: Requirement[];
}

export default function RequirementsFulfilled({ requirements }: RequirementsFulfilledProps) {
  return (
    <div className="bg-neutral-50 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-4">
        <CheckCircleIcon className="h-5 w-5 text-primary-600" />
        <h3 className="font-semibold text-neutral-900">Requirements Fulfilled</h3>
      </div>
      
      <div className="space-y-2">
        {requirements.map((requirement) => (
          <div
            key={requirement.id}
            className="flex items-center space-x-3 p-3 bg-primary-50 border border-primary-200 rounded-lg"
          >
            <CheckCircleIcon className="h-5 w-5 text-primary-600 flex-shrink-0" />
            <span className="text-primary-800 font-medium">{requirement.name}</span>
          </div>
        ))}
        
        {requirements.length === 0 && (
          <div className="text-neutral-500 text-sm italic">
            No requirements data available
          </div>
        )}
      </div>
    </div>
  );
}