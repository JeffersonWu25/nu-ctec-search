import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import { supabase } from '@/app/lib/supabase';
import { ASK_COMMENTS_SYSTEM_PROMPT, ASK_COMMENTS_USER_PROMPT } from '@/app/prompts/askComments';

const EMBEDDING_MODEL = 'text-embedding-3-small';
const CHAT_MODEL = 'gpt-4o-mini';
const MAX_RESULTS = 8;
const SIMILARITY_THRESHOLD = 0.3; // Minimum cosine similarity score (0-1)

interface SimilarComment {
  chunk_id: string;
  entity_id: string;
  content: string;
  similarity: number;
}

interface AskRequestBody {
  question: string;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: courseOfferingId } = await params;

  // Validate request body
  let body: AskRequestBody;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: 'Invalid JSON body' },
      { status: 400 }
    );
  }

  const { question } = body;

  if (!question || typeof question !== 'string' || question.trim().length === 0) {
    return NextResponse.json(
      { error: 'Question is required' },
      { status: 400 }
    );
  }

  // Check for OpenAI API key
  const openaiApiKey = process.env.OPENAI_API_KEY;
  if (!openaiApiKey) {
    console.error('OPENAI_API_KEY is not configured');
    return NextResponse.json(
      { error: 'AI service is not configured' },
      { status: 500 }
    );
  }

  const openai = new OpenAI({ apiKey: openaiApiKey });

  try {
    // Step 1: Generate embedding for the question
    const embeddingResponse = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: question.trim(),
    });

    const questionEmbedding = embeddingResponse.data[0].embedding;

    // Step 2: Search for similar comments using Supabase RPC
    const { data: similarComments, error: searchError } = await supabase.rpc(
      'search_similar_comments',
      {
        query_embedding: questionEmbedding,
        target_course_offering_id: courseOfferingId,
        similarity_threshold: SIMILARITY_THRESHOLD,
        max_results: MAX_RESULTS,
      }
    );

    if (searchError) {
      console.error('Vector search error:', searchError);
      return NextResponse.json(
        { error: 'Failed to search comments' },
        { status: 500 }
      );
    }

    const comments: SimilarComment[] = similarComments || [];

    // Step 3: Generate answer using LLM
    const commentContents = comments.map((c) => c.content);
    const referencedCommentIds = comments.map((c) => c.entity_id);

    const chatResponse = await openai.chat.completions.create({
      model: CHAT_MODEL,
      messages: [
        { role: 'system', content: ASK_COMMENTS_SYSTEM_PROMPT },
        { role: 'user', content: ASK_COMMENTS_USER_PROMPT(question.trim(), commentContents) },
      ],
      temperature: 0.3,
      max_tokens: 500,
    });

    const answer = chatResponse.choices[0]?.message?.content || 'Unable to generate a response.';

    // Step 4: Return response
    return NextResponse.json({
      data: {
        question: question.trim(),
        answer,
        referencedCommentIds,
        commentCount: comments.length,
      },
    });

  } catch (error) {
    console.error('Ask AI error:', error);

    if (error instanceof OpenAI.APIError) {
      return NextResponse.json(
        { error: `OpenAI API error: ${error.message}` },
        { status: 502 }
      );
    }

    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}
