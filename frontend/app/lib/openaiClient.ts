/**
 * Shared OpenAI client factory.
 * Validates the API key and returns a configured client.
 * Used by askService and discoverService.
 */

import OpenAI from 'openai';
import { serviceUnavailable } from '@/app/lib/errors';

/**
 * Returns a configured OpenAI client.
 * Throws 503 ServiceUnavailable if the API key is not set.
 */
export function getOpenAIClient(): OpenAI {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw serviceUnavailable('OpenAI API key not configured');
  }
  return new OpenAI({ apiKey });
}
