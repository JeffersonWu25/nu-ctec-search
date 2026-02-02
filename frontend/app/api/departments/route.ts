import { NextResponse } from 'next/server';
import { handleApiError, handleSupabaseError } from '@/app/lib/errors';
import * as departmentRepo from '@/app/lib/repositories/departmentRepo';

export async function GET() {
  try {
    const { data, error } = await departmentRepo.getAll();
    if (error) handleSupabaseError(error);
    return NextResponse.json({ data });
  } catch (error) {
    return handleApiError(error);
  }
}
