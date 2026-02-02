/**
 * Standardized error handling for API routes.
 *
 * Error flow:
 *   Repository returns { data, error }
 *   → Service calls handleSupabaseError() which throws AppError
 *   → Route catches with handleApiError() which returns NextResponse
 *
 * Response shape: { error: { code: string, message: string } }
 */

import { NextResponse } from 'next/server';

export class AppError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly code: string,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// --- Factory helpers ---

export function notFound(entity: string): AppError {
  return new AppError(`${entity} not found`, 404, 'NOT_FOUND');
}

export function badRequest(message: string): AppError {
  return new AppError(message, 400, 'BAD_REQUEST');
}

export function internal(message: string): AppError {
  return new AppError(message, 500, 'INTERNAL_ERROR');
}

export function serviceUnavailable(message: string): AppError {
  return new AppError(message, 503, 'SERVICE_UNAVAILABLE');
}

export function externalServiceError(service: string, message: string): AppError {
  return new AppError(`${service} error: ${message}`, 502, 'EXTERNAL_SERVICE_ERROR');
}

// --- Supabase error translator ---

/**
 * Translate a Supabase error into an AppError and throw.
 * Detects PGRST116 (row not found from .single()) and maps to 404.
 */
export function handleSupabaseError(
  error: { code?: string; message: string },
  entity?: string,
): never {
  if (error.code === 'PGRST116' && entity) {
    throw notFound(entity);
  }
  throw internal(error.message);
}

// --- Route-level error handler ---

/**
 * Convert a caught error into a structured NextResponse.
 * Use in route catch blocks: `catch (error) { return handleApiError(error); }`
 */
export function handleApiError(error: unknown): NextResponse {
  if (error instanceof AppError) {
    return NextResponse.json(
      { error: { code: error.code, message: error.message } },
      { status: error.statusCode },
    );
  }

  console.error('Unexpected error:', error);
  return NextResponse.json(
    { error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } },
    { status: 500 },
  );
}
