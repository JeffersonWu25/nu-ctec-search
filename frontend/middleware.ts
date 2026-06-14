import { NextResponse, type NextRequest } from 'next/server';
import { isNorthwesternEmail, isPublicRoute } from '@/app/lib/auth';
import { createClient } from '@/app/lib/supabase/middleware';

function redirectToSignIn(request: NextRequest, error?: string) {
  const url = request.nextUrl.clone();
  url.pathname = '/signin';

  if (error) {
    url.searchParams.set('error', error);
  } else if (request.nextUrl.pathname !== '/') {
    url.searchParams.set('redirect', request.nextUrl.pathname);
  }

  return NextResponse.redirect(url);
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  const clientResult = createClient(request);
  if (!clientResult) {
    return redirectToSignIn(request, 'config_error');
  }

  try {
    const { supabase, supabaseResponse } = clientResult;

    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (user?.email && !isNorthwesternEmail(user.email)) {
      await supabase.auth.signOut();
      return redirectToSignIn(request, 'invalid_domain');
    }

    if (!user) {
      return redirectToSignIn(request);
    }

    if (pathname === '/signin') {
      const redirectTo = request.nextUrl.searchParams.get('redirect') || '/';
      const url = request.nextUrl.clone();
      url.pathname = redirectTo;
      url.search = '';
      return NextResponse.redirect(url);
    }

    return supabaseResponse;
  } catch (error) {
    console.error('Middleware auth error:', error);
    return redirectToSignIn(request, 'auth_failed');
  }
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
