import { useState, useRef, useCallback, useEffect } from 'react';

export interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  cards?: any[];
  cardType?: 'course' | 'professor' | 'offering';
}

const AI_RESPONSES = [
  {
    content: "I would recommend COMPSCI-350 intro to AI and COMPSCI-349: Intro to ML. Here's my reasoning:\n\nBoth courses provide excellent foundations in machine learning and artificial intelligence, which are core components of TensorFlow. The AI course will give you theoretical background while the ML course focuses on practical implementation. These courses have strong student reviews and will prepare you well for advanced TensorFlow development.",
    cards: [
      {
        courseId: 'course-ai-intro',
        courseName: 'Intro to AI',
        courseCode: 'COMPSCI-350'
      },
      {
        courseId: 'course-ml-intro', 
        courseName: 'Intro to ML',
        courseCode: 'COMPSCI-349'
      }
    ],
    cardType: 'course' as const
  },
  {
    content: "I would recommend COMPSCI-350 intro to AI with professor Sugandha Z. Here's my reasoning:\n\nProfessor Sugandha is known for her engaging teaching style and practical approach to AI concepts. Students consistently rate her highly for making complex topics accessible and her enthusiasm for the subject matter. She also has industry experience with TensorFlow and often incorporates real-world examples into her lectures.",
    cards: [
      {
        instructorId: 'instructor-sugandha',
        professorName: 'Sugandha Z',
        courseName: 'Intro to AI'
      }
    ],
    cardType: 'professor' as const
  },
  {
    content: "Here are some specific course offerings that might work:\n\nI've found these specific sections that balance strong teaching with manageable workload. Dr. Smith's section has excellent student feedback for clear explanations, while Prof. Johnson is known for hands-on projects that directly apply to TensorFlow development.",
    cards: [
      {
        courseOfferingId: 'offering-tensorflow-1',
        courseCode: 'COMPSCI-350',
        courseName: 'Intro to AI',
        instructor: 'Dr. Smith',
        term: 'Fall 2024',
        overallRating: 4.5,
        teachingRating: 4.8
      },
      {
        courseOfferingId: 'offering-tensorflow-2',
        courseCode: 'COMPSCI-349', 
        courseName: 'Intro to ML',
        instructor: 'Prof. Johnson',
        term: 'Spring 2025',
        overallRating: 4.3,
        teachingRating: 4.6
      }
    ],
    cardType: 'offering' as const
  },
  {
    content: "Yeah, ur asking for too much. No courses exist that perfectly match all your criteria, but these are close alternatives.\n\nMost courses that cover advanced TensorFlow concepts require significant time commitment and have challenging workloads. You might want to consider taking prerequisites first or adjusting your expectations about workload for courses in this area.",
    cards: [],
    cardType: undefined
  }
];

interface UseChatProps {
  chatId: string;
  initialQuery?: string;
}

export function useChat({ chatId, initialQuery }: UseChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const responseIndex = useRef(0);
  const hasAutoResponded = useRef(false);

  const getInitialMessage = useCallback(() => {
    if (initialQuery) {
      return initialQuery;
    }
    
    switch (chatId) {
      case 'chat-1':
        return 'I want to learn TensorFlow';
      case 'chat-2':
        return 'I want energetic Professor, less work';
      default:
        return 'I want to learn TensorFlow';
    }
  }, [chatId, initialQuery]);

  const sendAiResponse = useCallback((responseIdx: number) => {
    const response = AI_RESPONSES[responseIdx % AI_RESPONSES.length];
    const aiMessage: Message = {
      id: `ai-${Date.now()}`,
      type: 'ai',
      content: response.content,
      cards: response.cards,
      cardType: response.cardType
    };

    setMessages(prev => [...prev, aiMessage]);
    responseIndex.current = responseIdx + 1;
    setIsLoading(false);
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: content.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate AI response delay
    setTimeout(() => {
      sendAiResponse(responseIndex.current);
    }, 1000);
  }, [isLoading, sendAiResponse]);

  // Initialize messages
  useEffect(() => {
    const initialMessage: Message = {
      id: 'initial',
      type: 'user',
      content: getInitialMessage()
    };

    setMessages([initialMessage]);

    // Auto-trigger first AI response for search queries (only once)
    if (initialQuery && !hasAutoResponded.current) {
      hasAutoResponded.current = true;
      setIsLoading(true);
      
      setTimeout(() => {
        sendAiResponse(0);
      }, 1000);
    }
  }, [chatId, initialQuery, getInitialMessage, sendAiResponse]);

  return {
    messages,
    isLoading,
    sendMessage
  };
}