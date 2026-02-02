import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '@/app/lib/errors';
import { validateUUID } from '@/app/lib/validation';
import * as offeringService from '@/app/lib/services/offeringService';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    validateUUID(id, 'id');
    const data = await offeringService.getOfferingDetail(id);
    return NextResponse.json({ data });
  } catch (error) {
    return handleApiError(error);
  }
}
