import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  // Filter params
  const courseId = searchParams.get('courseId');
  const instructorId = searchParams.get('instructorId');
  const departmentId = searchParams.get('departmentId');
  const quarter = searchParams.get('quarter');
  const year = searchParams.get('year');
  // TODO: Implement requirement filtering (requires join through course_requirements)
  // TODO: Implement text search across course code/title

  // Pagination
  const limit = parseInt(searchParams.get('limit') || '20');
  const offset = parseInt(searchParams.get('offset') || '0');

  // Sorting
  const sortBy = searchParams.get('sortBy') || 'year';
  const sortOrder = searchParams.get('sortOrder') === 'asc' ? true : false;

  let query = supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      audience_size,
      response_count,
      course:courses(
        id,
        code,
        title,
        department:departments(id, code, name)
      ),
      instructor:instructors(id, name, profile_photo)
    `, { count: 'exact' })
    .range(offset, offset + limit - 1);

  // Apply filters
  if (courseId) {
    query = query.eq('course_id', courseId);
  }
  if (instructorId) {
    query = query.eq('instructor_id', instructorId);
  }
  if (quarter) {
    query = query.eq('quarter', quarter);
  }
  if (year) {
    query = query.eq('year', parseInt(year));
  }

  // Filter by department (requires join)
  if (departmentId) {
    query = query.eq('course.department_id', departmentId);
  }

  // Apply sorting
  if (sortBy === 'year') {
    query = query.order('year', { ascending: sortOrder }).order('quarter', { ascending: sortOrder });
  } else if (sortBy === 'course') {
    query = query.order('course(code)', { ascending: sortOrder });
  } else if (sortBy === 'instructor') {
    query = query.order('instructor(name)', { ascending: sortOrder });
  }

  const { data, error, count } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ data, count, limit, offset });
}
