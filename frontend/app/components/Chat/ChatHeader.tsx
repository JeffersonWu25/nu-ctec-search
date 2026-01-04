import { useRouter } from 'next/navigation';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

interface ChatHeaderProps {
  initialQuery: string;
}

const truncateText = (text: string, maxLength: number = 60): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
};

export default function ChatHeader({ initialQuery }: ChatHeaderProps) {
  const router = useRouter();

  const handleBackClick = () => {
    router.push('/discover');
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 overflow-hidden">
      <div className="bg-primary-600 p-6">
        {/* Back to Discover Button */}
        <div className="mb-6">
          <button
            onClick={handleBackClick}
            className="inline-flex items-center space-x-2 bg-white border border-white text-primary-600 hover:bg-primary-50 hover:text-primary-700 transition-colors px-4 py-2 rounded-lg font-medium"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            <span className="text-sm">Back to Discover</span>
          </button>
        </div>

        {/* Chat Title - Dynamic based on initial query */}
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold text-white">
            {truncateText(initialQuery)}
          </h1>
        </div>
      </div>
    </div>
  );
}