'use client';

import { useEffect, useRef } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { useChat } from '@/app/hooks/useChat';
import ChatHeader from '@/app/components/Chat/ChatHeader';
import ChatMessage from '@/app/components/Chat/ChatMessage';
import ChatInput from '@/app/components/Chat/ChatInput';

export default function ChatPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const chatId = params.chatId as string;
  const initialQuery = searchParams.get('q');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, isLoading, sendMessage } = useChat({
    chatId,
    initialQuery: initialQuery || undefined
  });

  const getInitialMessage = () => {
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
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      {/* Header Section */}
      <div className="sticky top-16 z-10 bg-neutral-50 pt-4 pb-2">
        <div className="max-w-4xl mx-auto">
          <ChatHeader initialQuery={getInitialMessage()} />
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto pb-32 pt-7">
        <div className="max-w-4xl mx-auto space-y-6 px-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 text-gray-900 px-4 py-3 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="animate-spin w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
                  <span>AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
    </div>
  );
}