'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface CategoryCard {
  id: string;
  title: string;
  subtitle: string;
  category: string;
  icon: string;
  gradient: string;
  description: string;
}

const CATEGORIES: CategoryCard[] = [
  {
    id: 'easy-distros',
    title: 'Easy',
    subtitle: 'Distros',
    category: 'easy-distros',
    icon: '😌',
    gradient: 'from-emerald-400 to-cyan-400',
    description: 'Light workload distribution requirements'
  },
  {
    id: 'top-courses',
    title: 'Top',
    subtitle: 'Courses',
    category: 'top-courses',
    icon: '⭐',
    gradient: 'from-amber-400 to-orange-400',
    description: 'Highest rated courses at Northwestern'
  },
  {
    id: 'stem-favorites',
    title: 'STEM',
    subtitle: 'Favorites',
    category: 'stem-favorites',
    icon: '🧬',
    gradient: 'from-blue-400 to-indigo-400',
    description: 'Popular science and engineering courses'
  },
  {
    id: 'high-ratings',
    title: 'High',
    subtitle: 'Ratings',
    category: 'high-ratings',
    icon: '📈',
    gradient: 'from-purple-400 to-pink-400',
    description: 'Courses with excellent student reviews'
  },
  {
    id: 'quick-credits',
    title: 'Quick',
    subtitle: 'Credits',
    category: 'quick-credits',
    icon: '⚡',
    gradient: 'from-green-400 to-teal-400',
    description: 'Fast-track credit opportunities'
  },
  {
    id: 'professors-choice',
    title: 'Professors',
    subtitle: 'Choice',
    category: 'professors-choice',
    icon: '🎓',
    gradient: 'from-rose-400 to-red-400',
    description: 'Faculty recommended courses'
  }
];

export default function ExploreSection() {
  const router = useRouter();

  const handleCategoryClick = useCallback((category: string) => {
    try {
      router.push(`/rankings?category=${category}`);
    } catch {
      router.push('/error');
    }
  }, [router]);

  return (
    <section className="bg-white min-h-screen flex items-center" aria-labelledby="explore-heading">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-20">
        <div className="text-center mb-16">
          <h1 id="explore-heading" className="text-h1 text-gray-900 mb-4">
            Explore <span className="text-purple-600">NU&apos;s</span> Best
          </h1>
          <p className="text-body-lg text-gray-600 max-w-2xl mx-auto">
            Discover curated collections of Northwestern&apos;s most popular and highly-rated courses
          </p>
        </div>
        
        <div 
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto"
          role="list"
          aria-label="Course categories"
        >
          {CATEGORIES.map((category) => (
            <div
              key={category.id}
              className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 cursor-pointer group p-6 hover:-translate-y-1"
              onClick={() => handleCategoryClick(category.category)}
              role="listitem"
              aria-label={`Browse ${category.title} ${category.subtitle} courses`}
            >
              {/* Icon and gradient background */}
              <div className="relative mb-4">
                <div className={`absolute inset-0 bg-gradient-to-br ${category.gradient} opacity-10 rounded-2xl group-hover:opacity-20 transition-opacity duration-300`}></div>
                <div className="relative flex items-center justify-center w-16 h-16 mx-auto">
                  <span className="text-3xl" role="img" aria-hidden="true">
                    {category.icon}
                  </span>
                </div>
              </div>

              {/* Content */}
              <div className="text-center">
                <h3 className="text-h3 text-gray-900 mb-1">
                  {category.title}
                </h3>
                <p className="text-h3 text-gray-700 mb-3">
                  {category.subtitle}
                </p>
                <p className="text-body-sm text-gray-500">
                  {category.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full text-body-sm text-gray-600">
            <span className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></span>
            Data updated daily from student reviews
          </div>
        </div>
      </div>
    </section>
  );
}