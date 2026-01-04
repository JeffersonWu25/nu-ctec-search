import { SparklesIcon } from '@heroicons/react/24/outline';

interface AISummaryProps {
  summary?: string;
}

export default function AISummary({ summary }: AISummaryProps) {
  if (!summary) {
    return (
      <div className="bg-neutral-50 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <SparklesIcon className="h-5 w-5 text-neutral-400" />
          <h3 className="font-semibold text-neutral-900">AI Summary</h3>
        </div>
        <p className="text-neutral-500 text-sm italic">
          No AI summary available for this course offering.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-neutral-50 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-4">
        <SparklesIcon className="h-5 w-5 text-primary-600" />
        <h3 className="font-semibold text-neutral-900">AI Summary</h3>
      </div>
      
      <div className="border-l-4 border-primary-500 bg-primary-50 p-4 rounded-r-lg">
        <p className="text-primary-900 text-sm leading-relaxed">
          {summary}
        </p>
      </div>
    </div>
  );
}