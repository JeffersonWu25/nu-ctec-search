import { Message } from '@/app/hooks/useChat';
import CourseRecommendationCard from './CourseRecommendationCard';
import ProfessorRecommendationCard from './ProfessorRecommendationCard';
import CourseOfferingRecommendationCard from './CourseOfferingRecommendationCard';

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const renderCards = () => {
    if (!message.cards || message.cards.length === 0) return null;

    return (
      <div className="flex gap-3 mt-3 flex-wrap">
        {message.cards.map((card, index) => {
          switch (message.cardType) {
            case 'course':
              return (
                <CourseRecommendationCard
                  key={index}
                  courseId={card.courseId}
                  courseName={card.courseName}
                  courseCode={card.courseCode}
                  description={card.description}
                />
              );
            case 'professor':
              return (
                <ProfessorRecommendationCard
                  key={index}
                  instructorId={card.instructorId}
                  professorName={card.professorName}
                  courseName={card.courseName}
                  description={card.description}
                />
              );
            case 'offering':
              return (
                <CourseOfferingRecommendationCard
                  key={index}
                  courseOfferingId={card.courseOfferingId}
                  courseCode={card.courseCode}
                  courseName={card.courseName}
                  instructor={card.instructor}
                  term={card.term}
                  overallRating={card.overallRating}
                  teachingRating={card.teachingRating}
                />
              );
            default:
              return null;
          }
        })}
      </div>
    );
  };

  return (
    <div
      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-lg lg:max-w-2xl px-4 py-3 rounded-lg ${
          message.type === 'user'
            ? 'bg-primary-600 text-white'
            : 'bg-white border border-gray-200 text-gray-900'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.type === 'ai' && renderCards()}
      </div>
    </div>
  );
}