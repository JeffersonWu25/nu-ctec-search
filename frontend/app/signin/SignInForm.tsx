'use client';

import { FormEvent, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { isNorthwesternEmail } from '@/app/lib/auth';
import { createClient } from '@/app/lib/supabase/client';

const ERROR_MESSAGES: Record<string, string> = {
  invalid_domain:
    'Only Northwestern University email addresses are allowed. Please sign in with your @northwestern.edu or @u.northwestern.edu account.',
  auth_failed: 'Sign in failed. Please try again.',
};

export default function SignInForm() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/';
  const errorKey = searchParams.get('error');

  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(
    errorKey ? ERROR_MESSAGES[errorKey] ?? 'Something went wrong. Please try again.' : null
  );
  const [isEmailSent, setIsEmailSent] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    if (!isNorthwesternEmail(email)) {
      setFormError(
        'Please use your Northwestern email address (@northwestern.edu or @u.northwestern.edu).'
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const supabase = createClient();
      const callbackUrl = new URL('/auth/callback', window.location.origin);
      if (redirectTo !== '/') {
        callbackUrl.searchParams.set('redirect', redirectTo);
      }

      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim().toLowerCase(),
        options: {
          emailRedirectTo: callbackUrl.toString(),
        },
      });

      if (error) {
        setFormError(error.message);
        return;
      }

      setIsEmailSent(true);
    } catch {
      setFormError('Unable to send sign-in link. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-primary-50 via-white to-secondary-50">
      <div className="w-full max-w-md animate-fade-in-up">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
            <span className="text-purple-600">NU</span>CTECS
          </h1>
          <p className="mt-2 text-gray-600 text-sm">Northwestern Course Reviews</p>
        </div>

        <div className="card-base p-8 shadow-lg">
          <h2 className="text-h2 text-gray-900 mb-2">Sign in to continue</h2>
          <p className="text-body-sm text-gray-600 mb-6">
            Access to NUCTECS is restricted to Northwestern University students, faculty, and
            staff. You must sign in with your{' '}
            <span className="font-medium text-gray-800">@northwestern.edu</span> email address.
          </p>

          <div
            className="mb-6 rounded-lg border border-purple-200 bg-purple-50 px-4 py-3 text-sm text-purple-900"
            role="note"
          >
            <p className="font-medium mb-1">Why sign in is required</p>
            <p className="text-purple-800 leading-relaxed">
              Northwestern administration requires that student course evaluation data be kept
              private and accessible only to verified members of the Northwestern community, in
              accordance with university data privacy policies.
            </p>
          </div>

          {isEmailSent ? (
            <div
              className="rounded-lg border border-green-200 bg-green-50 px-4 py-4 text-sm text-green-800"
              role="status"
            >
              <p className="font-medium mb-1">Check your email</p>
              <p>
                We sent a sign-in link to <span className="font-medium">{email}</span>. Click the
                link in the email to access NUCTECS.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Northwestern email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@u.northwestern.edu"
                  className="input-base px-4 py-3 text-sm"
                  disabled={isSubmitting}
                />
              </div>

              {formError && (
                <p className="text-sm text-red-600" role="alert">
                  {formError}
                </p>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-base w-full px-4 py-3 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-60 disabled:cursor-not-allowed shadow-md"
              >
                {isSubmitting ? 'Sending link…' : 'Send sign-in link'}
              </button>
            </form>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-gray-500">
          Having trouble? Make sure you are using your official Northwestern email address.
        </p>
      </div>
    </div>
  );
}
