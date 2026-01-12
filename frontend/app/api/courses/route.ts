import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const departmentId = searchParams.get('departmentId');
  const limit = parseInt(searchParams.get('limit') || '50');
  const offset = parseInt(searchParams.get('offset') || '0');

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
    .range(offset, offset + limit - 1);

  if (departmentId) {
    query = query.eq('department_id', departmentId);
  }

  const { data, error, count } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ data, count });
}
