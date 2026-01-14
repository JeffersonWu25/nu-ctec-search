# RAG Module

Vector similarity search for course offering queries.

## Jobs

### 1. Populate comment_chunks

```bash
python -m app.jobs.backfill_comment_chunks --dry-run  # Preview
python -m app.jobs.backfill_comment_chunks            # Run
```

### 2. Generate embeddings

```bash
python -m app.jobs.embed_comment_chunks --dry-run     # Preview
python -m app.jobs.embed_comment_chunks               # Embed all
```

## Usage

```python
from app.rag.retrieval import retrieve_similar_chunks

results = retrieve_similar_chunks(
    query="Is this course difficult?",
    course_offering_id="abc-123-...",
    k=5
)

for r in results:
    print(f"{r['similarity']:.3f}: {r['content'][:50]}...")
    print(f"  comment_id: {r['comment_id']}")  # For citations
```

## How It Works

1. Fetches all chunks + embeddings for the course_offering_id
2. Computes cosine similarity in Python (numpy)
3. Returns top k results sorted by similarity

No SQL setup required. Similarity is computed in Python for easy debugging.

---

## Unified RAG (Discovery Feature)

A separate system for cross-course discovery using `rag_chunks` + `rag_embeddings`.

### Setup: Create SQL Function

Run this SQL in Supabase to enable indexed vector search:

```sql
CREATE OR REPLACE FUNCTION search_rag_chunks(
    query_embedding vector(1536),
    match_entity_type text DEFAULT NULL,
    match_entity_id uuid DEFAULT NULL,
    match_chunk_types text[] DEFAULT NULL,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    chunk_id uuid,
    content text,
    metadata jsonb,
    entity_type text,
    entity_id uuid,
    chunk_type text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        rc.id AS chunk_id,
        rc.content,
        rc.metadata,
        rc.entity_type,
        rc.entity_id,
        rc.chunk_type,
        1 - (re.embedding <=> query_embedding) AS similarity
    FROM rag_chunks rc
    JOIN rag_embeddings re ON re.chunk_id = rc.id
    WHERE
        (match_entity_type IS NULL OR rc.entity_type = match_entity_type)
        AND (match_entity_id IS NULL OR rc.entity_id = match_entity_id)
        AND (match_chunk_types IS NULL OR rc.chunk_type = ANY(match_chunk_types))
    ORDER BY re.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### Jobs

Run these jobs to populate the unified RAG index:

```bash
# 1. Backfill comment chunks (from comments table)
python -m app.jobs.backfill_rag_chunks_comments --dry-run  # Preview
python -m app.jobs.backfill_rag_chunks_comments            # Run

# 2. Backfill catalog chunks (descriptions + prerequisites)
python -m app.jobs.backfill_rag_chunks_catalog --dry-run   # Preview
python -m app.jobs.backfill_rag_chunks_catalog             # Run

# 3. Generate embeddings for all new chunks
python -m app.jobs.embed_rag_chunks --dry-run              # Preview
python -m app.jobs.embed_rag_chunks                        # Embed all
python -m app.jobs.embed_rag_chunks --limit 100            # Embed first 100
```

### Verification Queries

Run these SQL queries to verify the backfill:

```sql
-- Count chunks by type
SELECT chunk_type, COUNT(*)
FROM rag_chunks
GROUP BY chunk_type;

-- Total embeddings
SELECT COUNT(*) FROM rag_embeddings;

-- Chunks missing embeddings
SELECT COUNT(*)
FROM rag_chunks rc
LEFT JOIN rag_embeddings re ON re.chunk_id = rc.id
WHERE re.chunk_id IS NULL;
```

### Usage

```python
from app.rag.unified_retrieval import (
    retrieve_similar_chunks_unified,
    discover_courses
)
from app.rag.embeddings import generate_embeddings

# Discovery: search across all courses
results = discover_courses(
    query_embedding=generate_embeddings(["easy PyTorch class"])[0],
    k=10,
    include_comments=True,
    include_catalog=True
)

# Or use the convenience wrapper
results = retrieve_similar_chunks_unified(
    query="I want an easy class that teaches PyTorch",
    k=10
)

for r in results:
    print(f"{r['similarity']:.3f}: {r['content'][:80]}...")
    print(f"  type: {r['chunk_type']}, course: {r['metadata'].get('course_code')}")
```

### How It Works

1. Uses Postgres `<=>` operator with ivfflat index for efficient vector search
2. Supports filtering by entity_type, entity_id, and chunk_type
3. Returns similarity scores (1 - cosine_distance)
4. Scales to thousands of chunks (unlike Python-side computation)
