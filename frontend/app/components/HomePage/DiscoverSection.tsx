import DiscoverSearch from '@/app/components/shared/DiscoverSearch';

export default function DiscoverSection() {
  return (
    <section className="bg-gray-50 min-h-screen flex items-center" aria-labelledby="discover-heading">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <DiscoverSearch />
      </div>
    </section>
  );
}