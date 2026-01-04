'use client';

import { useRouter } from 'next/navigation';
import DiscoverSearch from '@/app/components/shared/DiscoverSearch';

export default function DiscoverPage() {
  const router = useRouter();

  // Mock chat history data
  const previousChats = [
    {
      id: 'chat-1',
      preview: 'I want to learn TensorFlow',
      timestamp: '2 hours ago'
    },
    {
      id: 'chat-2', 
      preview: 'I want energetic Professor, less work',
      timestamp: '1 day ago'
    },
    {
      id: 'chat-3',
      preview: 'Easy math courses for non-majors',
      timestamp: '3 days ago'
    },
    {
      id: 'chat-4',
      preview: 'Fun creative writing workshops',
      timestamp: '1 week ago'
    }
  ];

  const handleChatClick = (chatId: string) => {
    router.push(`/discover/chat/${chatId}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Natural Language Search Section */}
      <section className="min-h-screen flex items-center bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <DiscoverSearch />
        </div>
      </section>

      {/* Continue Previous Chats Section */}
      <section className="bg-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Continue Previous Chats
            </h2>
            <p className="text-lg text-gray-600">
              Pick up where you left off with your course discovery conversations
            </p>
          </div>

          <div className="space-y-4">
            {previousChats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => handleChatClick(chat.id)}
                className="flex items-center justify-between p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-purple-300 hover:shadow-lg transition-all duration-200 cursor-pointer group"
              >
                <div className="flex-1">
                  <p className="text-lg font-medium text-gray-900 group-hover:text-purple-600 transition-colors duration-200">
                    {chat.preview}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {chat.timestamp}
                  </p>
                </div>
                <div className="ml-4 text-gray-400 group-hover:text-purple-600 transition-colors duration-200">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            ))}
          </div>

          {previousChats.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No previous chats</h3>
              <p className="text-gray-500">Start a new conversation above to discover courses!</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}