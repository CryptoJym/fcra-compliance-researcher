from __future__ import annotations

from app.core.cross_validation import url_authority, confidence_from_citations, confidence_metrics


def test_url_authority_heuristics():
    assert url_authority("https://city.gov/code") >= 0.95
    assert url_authority("https://library.municode.com/ca/sf") >= 0.85
    assert url_authority("https://medium.com/post") <= 0.4


def test_confidence_from_multiple_official_sources():
    cits = [
        "https://city.gov/hr/policy.pdf",
        "https://library.municode.com/ca/sf/codes",
        "https://law.justia.com/codes/ca/",
    ]
    res = confidence_from_citations(cits)
    assert res["unique_domains"] >= 3
    assert res["score"] >= 0.8


def test_confidence_metrics_overall():
    patch = {"citations": {"laws": [
        "https://city.gov/hr/policy.pdf",
        "https://example.com/blog"
    ]}}
    m = confidence_metrics(patch)
    assert 0.0 <= m["overall"]["score"] <= 1.0
