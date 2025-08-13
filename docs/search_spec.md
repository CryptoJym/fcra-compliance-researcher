## Search Component Specification (SearXNG)

### Purpose
Integrate SearXNG for enhanced sourcing from credible legal sites, with Brave fallback when configured.

### Scope
- Modify `app/core/search.py` to add `SearxngProvider`.
- Keep existing providers; include SearXNG only when `SEARXNG_URL` is set.

### Detailed Requirements
- Query SearXNG `/search?format=json`.
- Default filters: `site:gov filetype:pdf` appended to the query.
- Return list of `{url, title, snippet}` normalized to `SearchResult`.
- Retries and timeouts; handle non-200 responses gracefully.

### Example (pseudo)
```python
results = searx.search("FCRA NYC site:gov filetype:pdf")
```

### Dependencies
- Docker for SearXNG.

### Testing Criteria
- Unit tests mock HTTP responses and assert normalized outputs.


