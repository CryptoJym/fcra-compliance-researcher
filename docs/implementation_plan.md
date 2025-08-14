## Implementation Plan (Phased)

### Purpose
Phased rollout minimizing disruption, retaining existing agents and tests while introducing deeper research features.

### Branching
- Create `feature/deep-research-enhancements` for this work.

### Phase 1: Setup & Dependencies (1-2 days)
- Add optional extras for deep research dependencies in packaging.
- Add `.env` keys: `SEARXNG_URL`, `QDRANT_URL`, `OLLAMA_MODEL`, `ENABLE_LIVE_LLM`.
- Extend `docker-compose.yml` with `searxng` and `qdrant` services.
- Update `README.md` with setup instructions.

### Phase 2: Core Components (3-5 days)
- Implement `app/core/search.py` SearXNG provider and wire as optional provider.
- Add `app/core/crawl.py` (Trafilatura + Playwright + OCR via Unstructured) — imports guarded inside functions.
- Add `app/core/retrieval.py` for Qdrant — import guarded; FAISS remains default.
- Add `app/core/research_agent.py` with LangGraph graph; compile guarded with graceful fallback.

### Phase 3: Enhancements & Integration (2-3 days)
- Add contradiction detection in validate node; build provenance mapping in cite node.
- Expose evaluation endpoints in dashboard.

### Phase 4: Evaluation & Testing (1-2 days)
- Add `app/core/eval.py` CLI and test data; run RAGAS metrics.

### Phase 5: Merge & Rollout (1 day)
- Add `--deep-research` to CLI runner to invoke LangGraph pipeline.
- Document migration notes and deprecate FAISS in production.

### Risks & Mitigations
- Latency: cap hops and cache docs; OCR selectively for PDFs.
- Dependency weight: keep imports lazy and optional.

### Timeline
- Estimated 2 weeks total.


