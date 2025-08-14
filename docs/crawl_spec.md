## Crawl & Extract Specification

### Purpose
Robust crawling and extraction with OCR to handle PDFs and scanned documents common in legal sources.

### Scope
- Add `app/core/crawl.py` with `fetch_and_extract(url: str, ...) -> dict`.
- Use Trafilatura first; Playwright for JS; Unstructured for PDFs/images.

### Detailed Requirements
- Lazy-import heavy libraries inside the function.
- Include minimal metadata and source URL in the return value.
- Respect robots.txt and use polite delays.

### Testing Criteria
- Unit tests mock network and assert non-empty text and presence of metadata keys.


