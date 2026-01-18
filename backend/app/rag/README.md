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
