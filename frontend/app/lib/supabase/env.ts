export type SupabaseEnv = {
  url: string | undefined;
  anonKey: string | undefined;
  isConfigured: boolean;
};

export function getSupabaseEnv(): SupabaseEnv {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? process.env.SUPABASE_URL;
  const anonKey =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.SUPABASE_ANON_KEY;

  return {
    url,
    anonKey,
    isConfigured: Boolean(url && anonKey),
  };
}

export function isSupabaseConfigured(): boolean {
  return getSupabaseEnv().isConfigured;
}

export function isSupabaseConfiguredForBrowser(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );
}

export function isAuthServiceError(error: unknown): boolean {
  if (!error) return false;

  if (error instanceof TypeError) {
    return true;
  }

  const message =
    error instanceof Error ? error.message.toLowerCase() : String(error).toLowerCase();

  return (
    message.includes('fetch') ||
    message.includes('network') ||
    message.includes('econnrefused') ||
    message.includes('502') ||
    message.includes('503') ||
    message.includes('504') ||
    message.includes('timeout') ||
    message.includes('paused') ||
    message.includes('unavailable')
  );
}
