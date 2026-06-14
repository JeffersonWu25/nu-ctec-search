import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { isNorthwesternEmail } from '@/app/lib/auth';
import { getSupabaseEnv, isAuthServiceError, isSupabaseConfigured } from '@/app/lib/supabase/env';

export async function POST(request: NextRequest) {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: 'config_error' }, { status: 503 });
  }

  let body: { email?: string; redirect?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  }

  const email = body.email?.trim().toLowerCase();
  if (!email || !isNorthwesternEmail(email)) {
    return NextResponse.json({ error: 'invalid_email' }, { status: 400 });
  }

  try {
    const { url, anonKey } = getSupabaseEnv();
    const supabase = createClient(url!, anonKey!);

    const origin = request.headers.get('origin') ?? request.nextUrl.origin;
    const callbackUrl = new URL('/auth/callback', origin);
    if (body.redirect && body.redirect !== '/') {
      callbackUrl.searchParams.set('redirect', body.redirect);
    }

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: callbackUrl.toString(),
      },
    });

    if (error) {
      console.error('Supabase sign-in error:', error);
      return NextResponse.json({ error: 'service_unavailable' }, { status: 503 });
    }

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Sign-in route error:', error);
    if (isAuthServiceError(error)) {
      return NextResponse.json({ error: 'service_unavailable' }, { status: 503 });
    }
    return NextResponse.json({ error: 'auth_failed' }, { status: 500 });
  }
}
