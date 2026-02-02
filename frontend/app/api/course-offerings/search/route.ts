import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '@/app/lib/errors';
import { DEFAULT_PAGE_LIMIT } from '@/app/lib/config';
import { validatePagination, validateUUIDArray } from '@/app/lib/validation';
import * as offeringService from '@/app/lib/services/offeringService';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    const departmentIds = searchParams.get('departmentIds')?.split(',').filter(Boolean) || [];
    const courseIds = searchParams.get('courseIds')?.split(',').filter(Boolean) || [];
    const instructorIds = searchParams.get('instructorIds')?.split(',').filter(Boolean) || [];
    const requirementIds = searchParams.get('requirementIds')?.split(',').filter(Boolean) || [];

    if (departmentIds.length > 0) validateUUIDArray(departmentIds, 'departmentIds');
    if (courseIds.length > 0) validateUUIDArray(courseIds, 'courseIds');
    if (instructorIds.length > 0) validateUUIDArray(instructorIds, 'instructorIds');
    if (requirementIds.length > 0) validateUUIDArray(requirementIds, 'requirementIds');

    const sortBy = searchParams.get('sortBy') || 'recency';
    const sortOrder = searchParams.get('sortOrder') || 'desc';

    const { limit, offset } = validatePagination(
      searchParams.get('limit'),
      searchParams.get('offset'),
      { limit: DEFAULT_PAGE_LIMIT, offset: 0 },
    );

    const result = await offeringService.searchOfferings({
      departmentIds,
      courseIds,
      instructorIds,
      requirementIds,
      sortBy,
      sortOrder,
      limit,
      offset,
    });

    return NextResponse.json(result);
  } catch (error) {
    return handleApiError(error);
  }
}
