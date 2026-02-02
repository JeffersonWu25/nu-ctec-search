/**
 * Business logic for the "Ask AI" feature on course offering pages.
 * Embeds a question, searches for similar comments, generates an LLM answer.
 */

import OpenAI from 'openai';
import * as commentRepo from '@/app/lib/repositories/commentRepo';
import { getOpenAIClient } from '@/app/lib/openaiClient';
import { handleSupabaseError, externalServiceError } from '@/app/lib/errors';
import {
  EMBEDDING_MODEL,
  CHAT_MODEL,
  CHAT_TEMPERATURE,
  CHAT_MAX_TOKENS,
  ASK_SIMILARITY_THRESHOLD,
  ASK_MAX_RESULTS,
} from '@/app/lib/config';
import { ASK_COMMENTS_SYSTEM_PROMPT, ASK_COMMENTS_USER_PROMPT } from '@/app/prompts/askComments';

interface SimilarComment {
  chunk_id: string;
  entity_id: string;
  content: string;
  similarity: number;
}

export async function askAboutOffering(
  courseOfferingId: string,
  question: string,
): Promise<{
  question: string;
  answer: string;
  referencedCommentIds: string[];
  commentCount: number;
}> {
  const openai = getOpenAIClient();

  try {
    // Generate embedding for the question
    const embeddingResponse = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: question,
    });
    const questionEmbedding = embeddingResponse.data[0].embedding;

    // Search for similar comments via vector search
    const { data: similarComments, error: searchError } = await commentRepo.searchBySimilarity({
      embedding: questionEmbedding,
      courseOfferingId,
      similarityThreshold: ASK_SIMILARITY_THRESHOLD,
      maxResults: ASK_MAX_RESULTS,
    });

    if (searchError) handleSupabaseError(searchError);

    const comments: SimilarComment[] = similarComments || [];

    // Generate answer using LLM
    const commentContents = comments.map((c) => c.content);
    const referencedCommentIds = comments.map((c) => c.entity_id);

    const chatResponse = await openai.chat.completions.create({
      model: CHAT_MODEL,
      messages: [
        { role: 'system', content: ASK_COMMENTS_SYSTEM_PROMPT },
        { role: 'user', content: ASK_COMMENTS_USER_PROMPT(question, commentContents) },
      ],
      temperature: CHAT_TEMPERATURE,
      max_tokens: CHAT_MAX_TOKENS,
    });

    const answer = chatResponse.choices[0]?.message?.content || 'Unable to generate a response.';

    return {
      question,
      answer,
      referencedCommentIds,
      commentCount: comments.length,
    };
  } catch (error) {
    if (error instanceof OpenAI.APIError) {
      throw externalServiceError('OpenAI', error.message);
    }
    throw error;
  }
}
