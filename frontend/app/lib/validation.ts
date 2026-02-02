/**
 * Input validation helpers for API routes.
 * Each function throws badRequest() on invalid input.
 */

import { NextRequest } from 'next/server';
import { badRequest } from '@/app/lib/errors';

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Validate that a value is a well-formed UUID.
 * Throws 400 if the format doesn't match.
 */
export function validateUUID(value: string, field: string): string {
  if (!UUID_REGEX.test(value)) {
    throw badRequest(`Invalid ${field}: must be a valid UUID`);
  }
  return value;
}

/**
 * Validate an array of UUIDs (e.g. from comma-separated query params).
 * Throws 400 on the first invalid entry.
 */
export function validateUUIDArray(values: string[], field: string): string[] {
  for (let i = 0; i < values.length; i++) {
    if (!UUID_REGEX.test(values[i])) {
      throw badRequest(`Invalid ${field}[${i}]: must be a valid UUID`);
    }
  }
  return values;
}

/**
 * Validate and parse pagination params from query strings.
 * Throws 400 if values are non-numeric or out of range.
 */
export function validatePagination(
  limitParam: string | null,
  offsetParam: string | null,
  defaults: { limit: number; offset: number },
): { limit: number; offset: number } {
  let limit = defaults.limit;
  let offset = defaults.offset;

  if (limitParam !== null) {
    limit = parseInt(limitParam, 10);
    if (isNaN(limit)) {
      throw badRequest('limit must be a number');
    }
    if (limit < 1 || limit > 100) {
      throw badRequest('limit must be between 1 and 100');
    }
  }

  if (offsetParam !== null) {
    offset = parseInt(offsetParam, 10);
    if (isNaN(offset)) {
      throw badRequest('offset must be a number');
    }
    if (offset < 0) {
      throw badRequest('offset must be non-negative');
    }
  }

  return { limit, offset };
}

/**
 * Validate a numeric limit from a JSON body (as opposed to a query string).
 * Throws 400 if the value is not a valid number or out of range.
 */
export function validateLimit(
  value: unknown,
  defaultLimit: number,
  max: number = 100,
): number {
  if (value === undefined || value === null) {
    return defaultLimit;
  }
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw badRequest('limit must be a number');
  }
  const limit = Math.floor(value);
  if (limit < 1 || limit > max) {
    throw badRequest(`limit must be between 1 and ${max}`);
  }
  return limit;
}

/**
 * Validate that a value is a non-empty string. Returns the trimmed value.
 * Throws 400 if missing, not a string, or exceeds maxLength.
 */
export function validateRequiredString(
  value: unknown,
  field: string,
  opts?: { maxLength?: number },
): string {
  if (typeof value !== 'string' || value.trim().length === 0) {
    throw badRequest(`${field} is required`);
  }
  const trimmed = value.trim();
  if (opts?.maxLength && trimmed.length > opts.maxLength) {
    throw badRequest(`${field} must be at most ${opts.maxLength} characters`);
  }
  return trimmed;
}

/**
 * Validate an optional string. Returns the trimmed value or undefined.
 * Throws 400 only if provided but exceeds maxLength.
 */
export function validateOptionalString(
  value: unknown,
  field: string,
  opts?: { maxLength?: number },
): string | undefined {
  if (value === undefined || value === null || value === '') {
    return undefined;
  }
  if (typeof value !== 'string') {
    throw badRequest(`${field} must be a string`);
  }
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return undefined;
  }
  if (opts?.maxLength && trimmed.length > opts.maxLength) {
    throw badRequest(`${field} must be at most ${opts.maxLength} characters`);
  }
  return trimmed;
}

/**
 * Parse a JSON request body. Throws 400 if the body is not valid JSON.
 */
export async function parseJsonBody<T>(request: NextRequest): Promise<T> {
  try {
    return await request.json() as T;
  } catch {
    throw badRequest('Invalid JSON body');
  }
}
