import { supabase } from '@/app/lib/supabase';

export function getAll(params: {
  search?: string;
  limit: number;
  offset: number;
}) {
  let query = supabase
    .from('instructors')
    .select('id, name, profile_photo', { count: 'exact' })
    .order('name', { ascending: true })
    .range(params.offset, params.offset + params.limit - 1);

  if (params.search) {
    query = query.ilike('name', `%${params.search}%`);
  }

  return query;
}

export function getById(id: string) {
  return supabase
    .from('instructors')
    .select('id, name, profile_photo')
    .eq('id', id)
    .single();
}
