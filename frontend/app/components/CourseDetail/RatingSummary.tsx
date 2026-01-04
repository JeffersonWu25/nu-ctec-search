import { Rating } from '@/app/types/course';
import { ChartBarIcon } from '@heroicons/react/24/outline';

interface RatingSummaryProps {
  ratings: Rating[];
}

export default function RatingSummary({ ratings }: RatingSummaryProps) {
  // Get specific ratings for the summary
  const instructionRating = ratings.find(r => 
    r.surveyQuestion.question.includes('overall rating of the instruction')
  )?.mean || 0;

  const courseRating = ratings.find(r => 
    r.surveyQuestion.question.includes('overall rating of the course')
  )?.mean || 0;

  const learningRating = ratings.find(r => 
    r.surveyQuestion.question.includes('how much you learned')
  )?.mean || 0;

  const challengeRating = ratings.find(r => 
    r.surveyQuestion.question.includes('challenging you intellectually')
  )?.mean || 0;

  const stimulatingRating = ratings.find(r => 
    r.surveyQuestion.question.includes('stimulating your interest')
  )?.mean || 0;

  // Mock hours per week data (would come from time survey question)
  const hoursPerWeek = '4 - 7';

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-600';
    if (rating >= 3.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatRating = (rating: number) => `${rating.toFixed(1)}/6`;

  return (
    <div className="bg-neutral-50 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-4">
        <ChartBarIcon className="h-5 w-5 text-neutral-600" />
        <h3 className="font-semibold text-neutral-900">Rating Summary</h3>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        {/* Top Row */}
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">
            Rating of Instruction
          </div>
          <div className={`text-lg font-bold ${getRatingColor(instructionRating)}`}>
            {formatRating(instructionRating)}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">
            Rating of Course
          </div>
          <div className={`text-lg font-bold ${getRatingColor(courseRating)}`}>
            {formatRating(courseRating)}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">
            Estimated Learning
          </div>
          <div className={`text-lg font-bold ${getRatingColor(learningRating)}`}>
            {formatRating(learningRating)}
          </div>
        </div>
        
        {/* Bottom Row */}
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">
            Intellectual Challenge
          </div>
          <div className={`text-lg font-bold ${getRatingColor(challengeRating)}`}>
            {formatRating(challengeRating)}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">
            Stimulating Instructor
          </div>
          <div className={`text-lg font-bold ${getRatingColor(stimulatingRating)}`}>
            {formatRating(stimulatingRating)}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-neutral-500 uppercase tracking-wide mb-1">
            Hours Per Week
          </div>
          <div className="text-lg font-bold text-green-600">
            {hoursPerWeek}
          </div>
        </div>
      </div>
    </div>
  );
}