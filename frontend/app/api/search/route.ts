import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/app/lib/supabase';

// RAG-powered semantic search endpoint
// This will be expanded to include vector similarity search
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { query, limit = 10 } = body;

  if (!query || typeof query !== 'string') {
    return NextResponse.json(
      { error: 'Query is required and must be a string' },
      { status: 400 }
    );
  }

  // For now, perform text-based search on course titles and descriptions
  // TODO: Implement vector similarity search using embeddings table
  const { data: courses, error: coursesError } = await supabase
    .from('courses')
    .select(`
      id,
      code,
      title,
      description,
      department:departments(id, code, name)
    `)
    .or(`title.ilike.%${query}%,description.ilike.%${query}%,code.ilike.%${query}%`)
    .limit(limit);

  if (coursesError) {
    return NextResponse.json({ error: coursesError.message }, { status: 500 });
  }

  // Search comments for keyword matches
  const { data: matchingComments, error: commentsError } = await supabase
    .from('comments')
    .select(`
      id,
      content,
      course_offering:course_offerings(
        id,
        quarter,
        year,
        course:courses(id, code, title),
        instructor:instructors(id, name)
      )
    `)
    .ilike('content', `%${query}%`)
    .limit(limit);

  if (commentsError) {
    return NextResponse.json({ error: commentsError.message }, { status: 500 });
  }

  return NextResponse.json({
    data: {
      courses: courses || [],
      comments: matchingComments || []
    }
  });
}
