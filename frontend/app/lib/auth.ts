const NORTHWESTERN_EMAIL_DOMAINS = ['@northwestern.edu', '@u.northwestern.edu'] as const;

export function isNorthwesternEmail(email: string): boolean {
  const normalized = email.trim().toLowerCase();
  return NORTHWESTERN_EMAIL_DOMAINS.some((domain) => normalized.endsWith(domain));
}

export const PUBLIC_ROUTES = ['/signin', '/auth/callback', '/api/auth/signin'] as const;

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}
