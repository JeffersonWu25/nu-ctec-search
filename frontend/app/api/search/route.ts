import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '@/app/lib/errors';
import { DEFAULT_SEARCH_LIMIT } from '@/app/lib/config';
import { parseJsonBody, validateRequiredString, validateLimit } from '@/app/lib/validation';
import * as searchService from '@/app/lib/services/searchService';

export async function POST(request: NextRequest) {
  try {
    const body = await parseJsonBody<{ query?: string; limit?: number }>(request);
    const query = validateRequiredString(body.query, 'query');
    const limit = validateLimit(body.limit, DEFAULT_SEARCH_LIMIT);

    const data = await searchService.search(query, limit);
    return NextResponse.json({ data });
  } catch (error) {
    return handleApiError(error);
  }
}
