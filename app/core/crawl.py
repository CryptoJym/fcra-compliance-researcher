from __future__ import annotations

from typing import Any, Dict
import time
import random
import urllib.parse
import urllib.robotparser
import httpx
import os

from .logger import setup_logger

logger = setup_logger("crawl")


_LAST_REQUEST_BY_HOST: dict[str, float] = {}


def get_user_agents() -> list[str]:
    ua_fixed = os.getenv("CRAWL_USER_AGENT")
    if ua_fixed:
        return [ua_fixed]
    ua_list = os.getenv("CRAWL_USER_AGENTS", "").strip()
    if ua_list:
        return [u.strip() for u in ua_list.split(",") if u.strip()]
    return [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 FCRA-Researcher/1.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 FCRA-Researcher/1.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0 FCRA-Researcher/1.0",
    ]


def choose_user_agent() -> str:
    agents = get_user_agents()
    if len(agents) == 1:
        return agents[0]
    return random.choice(agents)


def respect_robots(url: str, user_agent: str) -> bool:
    if os.getenv("CRAWL_RESPECT_ROBOTS", "1") in ("0", "false", "False"):
        return True
    try:
        parts = urllib.parse.urlsplit(url)
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # Fail-open if robots cannot be retrieved
        return True


def polite_delay(url: str) -> None:
    try:
        min_delay = float(os.getenv("CRAWL_DELAY_SECONDS", "1.0"))
    except Exception:
        min_delay = 1.0
    if min_delay <= 0:
        return
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc
    now = time.monotonic()
    last = _LAST_REQUEST_BY_HOST.get(host, 0.0)
    wait = (last + min_delay) - now
    if wait > 0:
        time.sleep(wait)
    _LAST_REQUEST_BY_HOST[host] = time.monotonic()


def firecrawl_fetch(url: str) -> Dict[str, Any] | None:
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev").rstrip("/")
    timeout = float(os.getenv("CRAWL_HTTP_TIMEOUT", "20"))
    try:
        resp = httpx.post(
            f"{base_url}/v1/scrape",
            json={"url": url, "formats": ["markdown", "text", "html"]},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    except Exception as e:
        logger.warning(f"firecrawl request failed url={url} err={e}")
        return None
    if resp.status_code != 200:
        logger.warning(f"firecrawl status={resp.status_code} url={url}")
        return None
    try:
        payload = resp.json()
    except Exception:
        return None
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return None
    text = data.get("markdown") or data.get("text") or ""
    return {"text": text, "meta": {"firecrawl": {"job": payload.get("jobId")}}, "source": url}


def is_document_ai_configured() -> bool:
    return bool(
        os.getenv("GOOGLE_CLOUD_PROJECT")
        and os.getenv("GOOGLE_CLOUD_LOCATION")
        and os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_ID")
    )


def extract_with_document_ai(buffer: bytes, mime_type: str) -> str:
    from google.cloud import documentai  # type: ignore

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "").strip()
    processor_id = os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_ID", "").strip()
    processor_version = os.getenv("GOOGLE_DOCUMENT_AI_PROCESSOR_VERSION", "").strip()
    if not project_id or not location or not processor_id:
        raise ValueError("Document AI not configured")

    client = documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": f"{location}-documentai.googleapis.com"}
    )
    if processor_version:
        name = client.processor_version_path(project_id, location, processor_id, processor_version)
    else:
        name = client.processor_path(project_id, location, processor_id)
    raw_document = documentai.RawDocument(content=buffer, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    document = result.document
    return document.text if document and document.text else ""


def is_vision_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT"))


def extract_with_vision(buffer: bytes) -> str:
    from google.cloud import vision  # type: ignore

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=buffer)
    response = client.document_text_detection(image=image)
    annotation = response.full_text_annotation
    return annotation.text if annotation and annotation.text else ""


def fetch_and_extract(url: str, threshold: int = 500, ocr_strategy: str = "ocr_only") -> Dict[str, Any]:
    """
    Best-effort fetch and extract text and metadata from a URL.

    Notes
    - Heavy dependencies (trafilatura, playwright, unstructured) are imported lazily.
    - OCR attempted for PDFs/images via Unstructured when primary extraction is insufficient.
    - Returns a dictionary with keys: text, meta, source.
    """
    if os.getenv("CRAWL_USE_FIRECRAWL", "0") in ("1", "true", "True"):
        firecrawl = firecrawl_fetch(url)
        if firecrawl and len(firecrawl.get("text", "")) >= threshold:
            return firecrawl

    try:
        # Lazy import to avoid heavy deps in environments/tests that don't need them
        import trafilatura  # type: ignore
    except Exception as e:  # pragma: no cover - rare: trafilatura unavailable
        raise ValueError(f"Crawl failed (missing trafilatura): {e}")

    # Robots and delay
    ua = choose_user_agent()
    if not respect_robots(url, ua):
        raise PermissionError("Blocked by robots.txt")
    polite_delay(url)

    # Primary fetch with explicit UA
    downloaded = None
    binary = None
    text = None
    ocr_engine = None
    content_type = None
    try:
        timeout = float(os.getenv("CRAWL_HTTP_TIMEOUT", "20"))
        resp = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout, follow_redirects=True)
        if resp.status_code == 200:
            downloaded = resp.text
            binary = resp.content
            content_type = resp.headers.get("content-type")
            text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
        else:
            logger.warning(f"http status={resp.status_code} url={url}")
    except Exception as e:
        text = None
        downloaded = None

    # Fallbacks when content is too short or likely PDF/image
    needs_fallback = not text or len(text or "") < threshold
    is_pdf_like = url.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))
    # Also detect by content-type when available in headers
    try:
        if downloaded is None:
            ct_resp = None
        else:
            ct_resp = None  # already have body; skip HEAD
    except Exception:
        ct_resp = None

    if needs_fallback:
        if is_pdf_like:
            if binary and is_document_ai_configured():
                try:
                    mime_type = content_type or "application/pdf"
                    text = extract_with_document_ai(binary, mime_type)
                    if text:
                        ocr_engine = "google_document_ai"
                except Exception as e:
                    logger.warning(f"document ai failed url={url} err={e}")
            if not text and binary and is_vision_configured() and url.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    text = extract_with_vision(binary)
                    if text:
                        ocr_engine = "google_vision"
                except Exception as e:
                    logger.warning(f"vision ocr failed url={url} err={e}")
            try:
                # Lazy import unstructured only when needed
                from unstructured.partition.auto import partition  # type: ignore

                elements = partition(url=url, strategy=ocr_strategy)  # type: ignore[arg-type]
                text = "\n".join(str(el) for el in elements)
                if text and not ocr_engine:
                    ocr_engine = f"unstructured:{ocr_strategy}"
            except Exception:
                # As a last resort, leave text as-is
                pass
        else:
            # Try JS rendering with Playwright
            try:
                from playwright.sync_api import sync_playwright  # type: ignore

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(user_agent=ua)
                    page = context.new_page()
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
    if ocr_engine:
        meta = dict(meta or {})
        meta["ocr_engine"] = ocr_engine

    return {"text": text or "", "meta": meta or {}, "source": url}
