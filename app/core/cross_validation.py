from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Dict, List


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


_AUTHORITY_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"\.gov$|\.gov[:/]|\.ca\.us$|\.us$"), 1.0),
    (re.compile(r"(municode\.com|codepublishing\.com|qcode\.us|amlegal\.com)"), 0.9),
    (re.compile(r"(legis|legislature|state|statutes|codes)\."), 0.85),
    (re.compile(r"(law\.cornell\.edu)"), 0.85),
    (re.compile(r"(justia\.com|findlaw\.com)"), 0.75),
    (re.compile(r"(github\.com|gist\.github\.com)"), 0.6),
    (re.compile(r"(medium\.com|wordpress\.com|blogspot\.|substack\.)"), 0.35),
]


def url_authority(url: str) -> float:
    host = _domain(url)
    if not host:
        return 0.3
    for pattern, score in _AUTHORITY_PATTERNS:
        if pattern.search(host):
            return score
    # PDFs on known TLDs often official
    if url.lower().endswith(".pdf") and (host.endswith(".gov") or host.endswith(".us")):
        return 0.9
    # default
    return 0.5


def confidence_from_citations(citations: List[str]) -> Dict[str, float | int]:
    if not citations:
        return {"score": 0.2, "citations_count": 0, "unique_domains": 0}
    domains = [_domain(c) for c in citations if isinstance(c, str) and c]
    unique = list(sorted(set(d for d in domains if d)))
    # average authority across unique domains to avoid overweighting duplicates
    if unique:
        avg = sum(url_authority(f"https://{d}") for d in unique) / len(unique)
    else:
        avg = 0.3
    # diversity boost
    boost = 0.0
    if len(unique) >= 2:
        boost += 0.1
    if len(unique) >= 3:
        boost += 0.1
    score = max(0.0, min(1.0, avg + boost))
    return {"score": round(score, 3), "citations_count": len(citations), "unique_domains": len(unique)}


def confidence_metrics(patch: Dict) -> Dict:
    """Compute overall confidence based on citations and simple heuristics.

    Returns a dictionary with overall score and any per-field hints in future.
    """
    citations = []
    cits_obj = (patch or {}).get("citations") or {}
    if isinstance(cits_obj, dict):
        laws = cits_obj.get("laws")
        if isinstance(laws, list):
            citations = [c for c in laws if isinstance(c, str)]
    overall = confidence_from_citations(citations)
    return {"overall": overall}
