import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '@/app/lib/errors';
import { parseJsonBody, validateOptionalString, validateUUIDArray } from '@/app/lib/validation';
import * as discoverService from '@/app/lib/services/discoverService';
import type { DiscoverRequestBody } from '@/app/types/discover';

export async function POST(request: NextRequest) {
  try {
    const body = await parseJsonBody<DiscoverRequestBody>(request);

    validateOptionalString(body.query, 'query', { maxLength: 1000 });
    if (body.requirement_ids && body.requirement_ids.length > 0) {
      validateUUIDArray(body.requirement_ids, 'requirement_ids');
    }

    const result = await discoverService.discover(body);
    return NextResponse.json(result);
  } catch (error) {
    return handleApiError(error);
  }
}
