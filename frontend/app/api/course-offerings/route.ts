import { NextRequest, NextResponse } from 'next/server';
import { handleApiError, handleSupabaseError } from '@/app/lib/errors';
import { DEFAULT_PAGE_LIMIT } from '@/app/lib/config';
import { validatePagination } from '@/app/lib/validation';
import * as offeringRepo from '@/app/lib/repositories/offeringRepo';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    // Filter params
    const courseId = searchParams.get('courseId') || undefined;
    const instructorId = searchParams.get('instructorId') || undefined;
    const departmentId = searchParams.get('departmentId') || undefined;
    const quarter = searchParams.get('quarter') || undefined;
    const yearParam = searchParams.get('year');
    const year = yearParam ? parseInt(yearParam) : undefined;

    // Pagination
    const { limit, offset } = validatePagination(
      searchParams.get('limit'),
      searchParams.get('offset'),
      { limit: DEFAULT_PAGE_LIMIT, offset: 0 },
    );

    // Sorting
    const sortBy = searchParams.get('sortBy') || 'year';
    const ascending = searchParams.get('sortOrder') === 'asc';

    const { data, error, count } = await offeringRepo.getAll(
      { courseId, instructorId, departmentId, quarter, year },
      { sortBy, ascending },
      { limit, offset }
    );

    if (error) handleSupabaseError(error);

    return NextResponse.json({ data, count, limit, offset });
  } catch (error) {
    return handleApiError(error);
  }
}
