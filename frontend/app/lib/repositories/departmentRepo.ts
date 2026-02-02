import { supabase } from '@/app/lib/supabase';

export function getAll() {
  return supabase
    .from('departments')
    .select('id, code, name')
    .order('name', { ascending: true });
}
