import { supabase } from '@/app/lib/supabase';

export interface OfferingListFilters {
  courseId?: string;
  instructorId?: string;
  departmentId?: string;
  quarter?: string;
  year?: number;
}

export interface OfferingListSort {
  sortBy: string;
  ascending: boolean;
}

export interface OfferingSearchFilters {
  courseIds?: string[];
  instructorIds?: string[];
  departmentIds?: string[];
  /** Pre-filtered course IDs from requirement lookup */
  requirementCourseIds?: string[];
}

/**
 * List course offerings with filtering, sorting, and pagination.
 * From: /api/course-offerings
 */
export function getAll(
  filters: OfferingListFilters,
  sort: OfferingListSort,
  pagination: { limit: number; offset: number }
) {
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
    .range(pagination.offset, pagination.offset + pagination.limit - 1);

  if (filters.courseId) {
    query = query.eq('course_id', filters.courseId);
  }
  if (filters.instructorId) {
    query = query.eq('instructor_id', filters.instructorId);
  }
  if (filters.quarter) {
    query = query.eq('quarter', filters.quarter);
  }
  if (filters.year) {
    query = query.eq('year', filters.year);
  }
  if (filters.departmentId) {
    query = query.eq('course.department_id', filters.departmentId);
  }

  if (sort.sortBy === 'year') {
    query = query
      .order('year', { ascending: sort.ascending })
      .order('quarter', { ascending: sort.ascending });
  } else if (sort.sortBy === 'course') {
    query = query.order('course(code)', { ascending: sort.ascending });
  } else if (sort.sortBy === 'instructor') {
    query = query.order('instructor(name)', { ascending: sort.ascending });
  }

  return query;
}

/**
 * Get a single course offering with full nested relations.
 * From: /api/course-offerings/[id]
 */
export function getById(id: string) {
  return supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      audience_size,
      response_count,
      course:courses!inner(
        id,
        code,
        title,
        description,
        prerequisites_text,
        department:departments(id, code, name),
        course_requirements(
          requirement:requirements(id, name)
        )
      ),
      instructor:instructors!inner(id, name, profile_photo)
    `)
    .eq('id', id)
    .single();
}

/**
 * Get offerings for the search page with course+instructor inner joins.
 * From: /api/course-offerings/search
 */
export function search(filters: OfferingSearchFilters) {
  let query = supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      course:courses!inner(
        id,
        code,
        title,
        department_id
      ),
      instructor:instructors!inner(
        id,
        name
      )
    `, { count: 'exact' });

  if (filters.courseIds && filters.courseIds.length > 0) {
    query = query.in('course_id', filters.courseIds);
  }
  if (filters.instructorIds && filters.instructorIds.length > 0) {
    query = query.in('instructor_id', filters.instructorIds);
  }
  if (filters.departmentIds && filters.departmentIds.length > 0) {
    query = query.in('course.department_id', filters.departmentIds);
  }
  if (filters.requirementCourseIds && filters.requirementCourseIds.length > 0) {
    query = query.in('course_id', filters.requirementCourseIds);
  }

  return query;
}

/**
 * Get all offerings for a course (with instructor join).
 * From: /api/courses/[id]
 */
export function getByCourseId(courseId: string) {
  return supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      audience_size,
      response_count,
      instructor:instructors(id, name, profile_photo)
    `)
    .eq('course_id', courseId)
    .order('year', { ascending: false })
    .order('quarter', { ascending: false });
}

/**
 * Get all offerings for an instructor (with course join).
 * From: /api/instructors/[id]
 */
export function getByInstructorId(instructorId: string) {
  return supabase
    .from('course_offerings')
    .select(`
      id,
      quarter,
      year,
      section,
      audience_size,
      response_count,
      course:courses(id, code, title)
    `)
    .eq('instructor_id', instructorId)
    .order('year', { ascending: false })
    .order('quarter', { ascending: false });
}
