## Crawl & Extract Specification

### Purpose
Robust crawling and extraction with OCR to handle PDFs and scanned documents common in legal sources.

### Scope
- Add `app/core/crawl.py` with `fetch_and_extract(url: str, ...) -> dict`.
- Use Trafilatura first; Playwright for JS; Unstructured for PDFs/images.
- Prefer Google OCR when configured: Document AI for PDFs; Vision for images (opt-in via `CRAWL_PREFER_GOOGLE_OCR=1`).
- When OCR runs, annotate `meta.ocr_engine` with the engine used.

### Detailed Requirements
- Lazy-import heavy libraries inside the function.
- Include minimal metadata and source URL in the return value.
- Respect robots.txt and use polite delays.

### Testing Criteria
- Unit tests mock network and assert non-empty text and presence of metadata keys.

