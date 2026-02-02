import { supabase } from '@/app/lib/supabase';

export function getAll(params: {
  departmentId?: string;
  limit: number;
  offset: number;
}) {
  let query = supabase
    .from('courses')
    .select(`
      id,
      code,
      title,
      description,
      prerequisites_text,
      department:departments(id, code, name)
    `)
    .order('code', { ascending: true })
    .range(params.offset, params.offset + params.limit - 1);

  if (params.departmentId) {
    query = query.eq('department_id', params.departmentId);
  }

  return query;
}

export function getById(id: string) {
  return supabase
    .from('courses')
    .select(`
      id,
      code,
      title,
      description,
      prerequisites_text,
      department:departments(id, code, name),
      course_requirements(
        requirement:requirements(id, name)
      )
    `)
    .eq('id', id)
    .single();
}

export function searchByKeyword(query: string, limit: number) {
  return supabase
    .from('courses')
    .select(`
      id,
      code,
      title,
      description,
      department:departments(id, code, name)
    `)
    .or(`title.ilike.%${query}%,description.ilike.%${query}%,code.ilike.%${query}%`)
    .limit(limit);
}
