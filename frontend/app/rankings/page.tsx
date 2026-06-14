import { Suspense } from 'react';
import RankingsContent from './RankingsContent';

export default function RankingsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <p className="text-gray-500 text-sm">Loading rankings…</p>
        </div>
      }
    >
      <RankingsContent />
    </Suspense>
  );
}
