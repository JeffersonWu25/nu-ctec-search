import { NextRequest, NextResponse } from 'next/server';
import { handleApiError, handleSupabaseError } from '@/app/lib/errors';
import { DEFAULT_LIST_LIMIT } from '@/app/lib/config';
import { validatePagination } from '@/app/lib/validation';
import * as instructorRepo from '@/app/lib/repositories/instructorRepo';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const search = searchParams.get('search') || undefined;

    const { limit, offset } = validatePagination(
      searchParams.get('limit'),
      searchParams.get('offset'),
      { limit: DEFAULT_LIST_LIMIT, offset: 0 },
    );

    const { data, error, count } = await instructorRepo.getAll({ search, limit, offset });
    if (error) handleSupabaseError(error);

    return NextResponse.json({ data, count });
  } catch (error) {
    return handleApiError(error);
  }
}
