import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';
import { openai, EMBEDDING_MODEL } from '@/app/lib/openai';
import { buildAskAIUserPrompt } from '@/app/lib/prompts';

interface ChunkWithEmbedding {
  id: string;
  comment_id: string;
  content: string;
  metadata: Record<string, unknown>;
  embedding: number[];
}

interface ScoredChunk extends ChunkWithEmbedding {
  similarity: number;
}

interface EmbeddingRecord {
  embedding: string | number[];
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: EMBEDDING_MODEL,
    input: text,
  });
  return response.data[0].embedding;
}

async function fetchChunksWithEmbeddings(
  courseOfferingId: string
): Promise<ChunkWithEmbedding[]> {
  const { data, error } = await supabase
    .from('comment_chunks')
    .select('id, comment_id, content, metadata, embeddings(embedding)')
    .eq('course_offering_id', courseOfferingId);

  if (error) {
    console.error('Error fetching chunks:', error);
    return [];
  }

  const chunks: ChunkWithEmbedding[] = [];

  for (const row of data || []) {
    const embeddingsData = row.embeddings as EmbeddingRecord | EmbeddingRecord[] | null;
    if (!embeddingsData) continue;

    // Handle both array and object responses from Supabase
    let embedding: number[] | null = null;
    if (Array.isArray(embeddingsData)) {
      if (embeddingsData.length > 0 && embeddingsData[0].embedding) {
        const embStr = embeddingsData[0].embedding;
        embedding = typeof embStr === 'string' ? JSON.parse(embStr) : embStr;
      }
    } else if (embeddingsData.embedding) {
      const embStr = embeddingsData.embedding;
      embedding = typeof embStr === 'string' ? JSON.parse(embStr) : embStr;
    }

    if (embedding) {
      chunks.push({
        id: row.id,
        comment_id: row.comment_id,
        content: row.content,
        metadata: row.metadata as Record<string, unknown>,
        embedding,
      });
    }
  }

  return chunks;
}

function retrieveSimilarChunks(
  queryEmbedding: number[],
  chunks: ChunkWithEmbedding[],
  k: number = 5
): ScoredChunk[] {
  const scored = chunks.map(chunk => ({
    ...chunk,
    similarity: cosineSimilarity(queryEmbedding, chunk.embedding),
  }));

  scored.sort((a, b) => b.similarity - a.similarity);
  return scored.slice(0, k);
}

async function generateAnswer(
  question: string,
  chunks: ScoredChunk[]
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

    // 2. Fetch all chunks with embeddings for this offering
    const chunks = await fetchChunksWithEmbeddings(courseOfferingId);

    if (chunks.length === 0) {
      return NextResponse.json({
        question,
        answer: 'No comments available for this course offering.',
        referencedCommentIds: [],
      });
    }

    // 3. Find most similar chunks
    const topChunks = retrieveSimilarChunks(queryEmbedding, chunks, 8);

    // 4. Generate answer using LLM
    const answer = await generateAnswer(question, topChunks);

    // 5. Return response with referenced comment IDs
    return NextResponse.json({
      question,
      answer,
      referencedCommentIds: topChunks.map(c => c.comment_id),
    });
  } catch (error) {
    console.error('Error in ask-ai:', error);
    return NextResponse.json(
      { error: 'Failed to process question' },
      { status: 500 }
    );
  }
}
