import { Rating } from '@/app/types/course';

interface RatingCardProps {
  rating: Rating;
}

export default function RatingCard({ rating }: RatingCardProps) {
  const { surveyQuestion, distribution, mean, responseCount } = rating;

  const getBarColor = (ratingValue: number) => {
    if (ratingValue <= 2) return 'bg-red-400';
    if (ratingValue <= 3) return 'bg-orange-400';
    if (ratingValue <= 4) return 'bg-yellow-400';
    if (ratingValue <= 5) return 'bg-green-400';
    return 'bg-primary-400';
  };

  const maxCount = Math.max(...distribution.map(d => d.count));

  return (
    <div className="border border-neutral-200 rounded-lg p-4">
      <div className="mb-4">
        <h3 className="font-semibold text-neutral-900 text-sm mb-2">
          {surveyQuestion.question}
        </h3>
        <div className="flex items-center justify-between text-sm text-neutral-600">
          <span>Response Count: {responseCount}</span>
          <span className="font-semibold">Mean: {mean.toFixed(2)}</span>
        </div>
      </div>

      <div className="space-y-2">
        {distribution.map(({ ratingValue, count, percentage }) => (
          <div key={ratingValue} className="flex items-center space-x-3">
            <div className="w-8 text-sm font-medium text-neutral-700">
              {ratingValue}
            </div>
            <div className="flex-1 bg-neutral-100 rounded-full h-6 relative overflow-hidden">
              <div 
                className={`h-full ${getBarColor(ratingValue)} transition-all duration-300 ease-in-out`}
                style={{ width: `${(count / maxCount) * 100}%` }}
              />
            </div>
            <div className="w-12 text-sm text-neutral-600 text-right">
              {percentage.toFixed(1)}%
            </div>
            <div className="w-8 text-sm text-neutral-600 text-right">
              ({count})
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}