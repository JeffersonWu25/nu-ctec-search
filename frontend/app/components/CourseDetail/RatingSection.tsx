import { Rating } from '@/app/types/course';
import RatingCard from './RatingCard';

interface RatingSectionProps {
  ratings: Rating[];
}

export default function RatingSection({ ratings }: RatingSectionProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
      <h2 className="text-xl font-bold text-neutral-900 mb-6">CTEC Survey Results</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ratings.map((rating) => (
          <RatingCard key={rating.id} rating={rating} />
        ))}
      </div>
    </div>
  );
}