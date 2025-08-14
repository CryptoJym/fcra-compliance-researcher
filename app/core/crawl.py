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

    # Robots and delay
    ua = choose_user_agent()
    if not respect_robots(url, ua):
        raise PermissionError("Blocked by robots.txt")
    polite_delay(url)

    # Primary fetch with explicit UA
    downloaded = None
    text = None
    try:
        timeout = float(os.getenv("CRAWL_HTTP_TIMEOUT", "20"))
        resp = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout, follow_redirects=True)
        if resp.status_code == 200:
            downloaded = resp.text
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

    return {"text": text or "", "meta": meta or {}, "source": url}


