import SearchSection from './SearchSection';
import DiscoverSection from './DiscoverSection';
import ExploreSection from './ExploreSection';

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <SearchSection />
      <DiscoverSection />
      <ExploreSection />
    </main>
  );
}