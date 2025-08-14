## Retrieval & Database Specification (Qdrant)

### Purpose
Migrate production retrieval from FAISS to Qdrant for hybrid search and rich metadata filtering; keep FAISS as dev fallback.

### Scope
- Add `app/core/retrieval.py` to wrap Qdrant operations (upsert and similarity search).
- Defer complete FAISS deprecation until rollout; maintain compatibility.

### Detailed Requirements
- Use `OllamaEmbeddings` or compatible embeddings in production; retain local hash embeddings for tests.
- Upsert docs with metadata: `source`, `jurisdiction`, `citation`.
- Provide `retrieve(query, k, filters)` returning texts and metadata.

### Testing Criteria
- Mock Qdrant client in unit tests; assert filter behavior and return format.


