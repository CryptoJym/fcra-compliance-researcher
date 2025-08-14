from __future__ import annotations

from typing import Any, Dict


def fetch_and_extract(url: str, threshold: int = 500, ocr_strategy: str = "ocr_only") -> Dict[str, Any]:
    """
    Best-effort fetch and extract text and metadata from a URL.

    Notes
    - Heavy dependencies (trafilatura, playwright, unstructured) are imported lazily.
    - OCR attempted for PDFs/images via Unstructured when primary extraction is insufficient.
    - Returns a dictionary with keys: text, meta, source.
    """
    try:
        # Lazy import to avoid heavy deps in environments/tests that don't need them
        import trafilatura  # type: ignore
    except Exception as e:  # pragma: no cover - rare: trafilatura unavailable
        raise ValueError(f"Crawl failed (missing trafilatura): {e}")

    try:
        downloaded = trafilatura.fetch_url(url, follow_redirects=True)
        text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
    except Exception as e:
        text = None
        downloaded = None

    # Fallbacks when content is too short or likely PDF/image
    needs_fallback = not text or len(text or "") < threshold
    is_pdf_like = url.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))

    if needs_fallback:
        if is_pdf_like:
            try:
                # Lazy import unstructured only when needed
                from unstructured.partition.auto import partition  # type: ignore

                elements = partition(url=url, strategy=ocr_strategy)  # type: ignore[arg-type]
                text = "\n".join(str(el) for el in elements)
            except Exception:
                # As a last resort, leave text as-is
                pass
        else:
            # Try JS rendering with Playwright
            try:
                from playwright.sync_api import sync_playwright  # type: ignore

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle")
                    html = page.content()
                    try:
                        text = trafilatura.extract(html, include_tables=True, include_links=True)
                    finally:
                        browser.close()
            except Exception:
                # Keep best-effort text if any
                pass

    try:
        meta = trafilatura.metadata_from_text(text or "")
    except Exception:
        meta = {}

    return {"text": text or "", "meta": meta or {}, "source": url}


