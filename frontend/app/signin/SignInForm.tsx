'use client';

import { FormEvent, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { isNorthwesternEmail } from '@/app/lib/auth';

const ERROR_MESSAGES: Record<string, string> = {
  invalid_domain:
    'Only Northwestern University email addresses are allowed. Please sign in with your @northwestern.edu or @u.northwestern.edu account.',
  auth_failed: 'Sign in failed. Please try again.',
  config_error:
    'Authentication is not configured on this deployment. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Vercel, then redeploy.',
  service_unavailable:
    'The authentication service is temporarily unavailable. If you use a free Supabase project, it may be paused after inactivity — open your Supabase dashboard and resume the project, then try again.',
};

const SERVICE_ERRORS = new Set(['config_error', 'service_unavailable']);

export default function SignInForm() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/';
  const errorKey = searchParams.get('error');

  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(
    errorKey && !SERVICE_ERRORS.has(errorKey)
      ? (ERROR_MESSAGES[errorKey] ?? 'Something went wrong. Please try again.')
      : null
  );
  const [serviceNotice, setServiceNotice] = useState<string | null>(
    errorKey && SERVICE_ERRORS.has(errorKey) ? ERROR_MESSAGES[errorKey] : null
  );
  const [isEmailSent, setIsEmailSent] = useState(false);

  const isServiceBlocked = Boolean(serviceNotice);

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
      const response = await fetch('/api/auth/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase(), redirect: redirectTo }),
      });

      const data = (await response.json()) as { error?: string; ok?: boolean };

      if (!response.ok) {
        const error = data.error ?? 'auth_failed';
        if (SERVICE_ERRORS.has(error)) {
          setServiceNotice(ERROR_MESSAGES[error] ?? ERROR_MESSAGES.service_unavailable);
        } else {
          setFormError(ERROR_MESSAGES[error] ?? 'Something went wrong. Please try again.');
        }
        return;
      }

      setServiceNotice(null);
      setIsEmailSent(true);
    } catch {
      setServiceNotice(ERROR_MESSAGES.service_unavailable);
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

          {serviceNotice && (
            <div
              className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
              role="status"
            >
              <p className="font-medium mb-1">Sign-in temporarily unavailable</p>
              <p className="text-amber-800 leading-relaxed">{serviceNotice}</p>
            </div>
          )}

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
                  disabled={isSubmitting || isServiceBlocked}
                />
              </div>

              {formError && (
                <p className="text-sm text-red-600" role="alert">
                  {formError}
                </p>
              )}

              <button
                type="submit"
                disabled={isSubmitting || isServiceBlocked}
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
