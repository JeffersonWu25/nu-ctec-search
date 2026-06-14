import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { getSupabaseEnv } from '@/app/lib/supabase/env';

let supabaseClient: SupabaseClient | undefined;

function getClient(): SupabaseClient {
  if (!supabaseClient) {
    const { url, anonKey } = getSupabaseEnv();

    if (!url || !anonKey) {
      throw new Error('Missing Supabase environment variables');
    }

    supabaseClient = createClient(url, anonKey);
  }

  return supabaseClient;
}

/**
 * Lazy-initialized Supabase client for server-side data access.
 * Defers env var validation until first use so builds succeed without secrets.
 */
export const supabase: SupabaseClient = new Proxy({} as SupabaseClient, {
  get(_target, prop, receiver) {
    const client = getClient();
    const value = Reflect.get(client, prop, receiver);
    return typeof value === 'function' ? value.bind(client) : value;
  },
});
