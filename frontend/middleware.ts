import { NextResponse, type NextRequest } from 'next/server';
import { isNorthwesternEmail, isPublicRoute } from '@/app/lib/auth';
import { createClient } from '@/app/lib/supabase/middleware';

export async function middleware(request: NextRequest) {
  const { supabase, supabaseResponse } = createClient(request);

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  if (user?.email && !isNorthwesternEmail(user.email)) {
    await supabase.auth.signOut();
    const url = request.nextUrl.clone();
    url.pathname = '/signin';
    url.searchParams.set('error', 'invalid_domain');
    return NextResponse.redirect(url);
  }

  if (!user && !isPublicRoute(pathname)) {
    const url = request.nextUrl.clone();
    url.pathname = '/signin';
    if (pathname !== '/') {
      url.searchParams.set('redirect', pathname);
    }
    return NextResponse.redirect(url);
  }

  if (user && pathname === '/signin') {
    const redirectTo = request.nextUrl.searchParams.get('redirect') || '/';
    const url = request.nextUrl.clone();
    url.pathname = redirectTo;
    url.search = '';
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
