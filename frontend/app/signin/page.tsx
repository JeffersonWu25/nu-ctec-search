import { Suspense } from 'react';
import SignInForm from './SignInForm';

export default function SignInPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-secondary-50">
          <p className="text-gray-500 text-sm">Loading…</p>
        </div>
      }
    >
      <SignInForm />
    </Suspense>
  );
}
