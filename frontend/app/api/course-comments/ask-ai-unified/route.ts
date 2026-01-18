import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';
import { openai, EMBEDDING_MODEL } from '@/app/lib/openai';
import { buildAskAIUserPrompt } from '@/app/lib/prompts';

/**
 * Unified Ask AI route using rag_chunks + rag_embeddings tables.
 *
 * Uses Postgres-indexed vector search via the search_rag_chunks RPC function
 * for efficient similarity search, filtering by course_offering_id.
 */

interface RagChunkResult {
  chunk_id: string;
  content: string;
  metadata: {
    comment_id?: string;
    course_offering_id?: string;
    course_code?: string;
    [key: string]: unknown;
  };
  entity_type: string;
  entity_id: string;
  chunk_type: string;
  similarity: number;
}

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: text,
  });
  return response.data[0].embedding;
}

async function searchRagChunks(
  queryEmbedding: number[],
  courseOfferingId: string,
  k: number = 8
): Promise<RagChunkResult[]> {
  // Call the search_rag_chunks Postgres function
  // Filters: entity_type='course_offering', entity_id=courseOfferingId, chunk_type='comment'
  const { data, error } = await supabase.rpc('search_rag_chunks', {
    query_embedding: queryEmbedding,
    match_entity_type: 'course_offering',
    match_entity_id: courseOfferingId,
    match_chunk_types: ['comment'],
    match_count: k,
  });

  if (error) {
    console.error('Error searching rag_chunks:', error);
    return [];
  }

  return (data || []) as RagChunkResult[];
}

async function generateAnswer(
  question: string,
  chunks: RagChunkResult[]
): Promise<string> {
  const context = chunks
    .map((c, i) => `[Comment ${i + 1}]: ${c.content}`)
    .join('\n\n');

  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      {
        role: 'user',
        content: buildAskAIUserPrompt(question, context),
      },
    ],
    temperature: 0.3,
    max_tokens: 200,
  });

  return response.choices[0].message.content || 'Unable to generate response.';
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { courseOfferingId, question } = body;

    if (!courseOfferingId || !question) {
      return NextResponse.json(
        { error: 'Missing courseOfferingId or question' },
        { status: 400 }
      );
    }

    // 1. Generate embedding for the question
    const queryEmbedding = await generateEmbedding(question);

    // 2. Search rag_chunks using indexed Postgres vector search
    const chunks = await searchRagChunks(queryEmbedding, courseOfferingId, 8);

    if (chunks.length === 0) {
      return NextResponse.json({
        question,
        answer: 'No comments available for this course offering.',
        referencedCommentIds: [],
      });
    }

    // 3. Generate answer using LLM
    const answer = await generateAnswer(question, chunks);

    // 4. Extract comment IDs from metadata for citations
    const referencedCommentIds = chunks
      .map(c => c.metadata?.comment_id)
      .filter((id): id is string => typeof id === 'string');

    return NextResponse.json({
      question,
      answer,
      referencedCommentIds,
    });
  } catch (error) {
    console.error('Error in ask-ai-unified:', error);
    return NextResponse.json(
      { error: 'Failed to process question' },
      { status: 500 }
    );
  }
}
