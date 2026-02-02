import { NextRequest, NextResponse } from 'next/server';
import { handleApiError } from '@/app/lib/errors';
import { validateUUID, validateRequiredString, parseJsonBody } from '@/app/lib/validation';
import * as askService from '@/app/lib/services/askService';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: courseOfferingId } = await params;
    validateUUID(courseOfferingId, 'id');

    const body = await parseJsonBody<{ question?: string }>(request);
    const question = validateRequiredString(body.question, 'question', { maxLength: 500 });

    const data = await askService.askAboutOffering(courseOfferingId, question);
    return NextResponse.json({ data });
  } catch (error) {
    return handleApiError(error);
  }
}
