import { NextResponse } from 'next/server';
import { handleApiError, handleSupabaseError } from '@/app/lib/errors';
import * as requirementRepo from '@/app/lib/repositories/requirementRepo';

export async function GET() {
  try {
    const { data, error } = await requirementRepo.getAll();
    if (error) handleSupabaseError(error);
    return NextResponse.json({ data });
  } catch (error) {
    return handleApiError(error);
  }
}
