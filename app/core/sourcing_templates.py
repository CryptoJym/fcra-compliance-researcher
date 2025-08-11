from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class QueryTemplate:
    name: str
    patterns: List[str]


DEFAULT_TEMPLATES = {
    "city": QueryTemplate(
        name="city",
        patterns=[
            "{city} municipal code ban the box",
            "{city} fair chance ordinance",
            "{city} human resources criminal history policy",
            "{state} state ban the box preemption",
        ],
    ),
    "county": QueryTemplate(
        name="county",
        patterns=[
            "{county} county code fair chance",
            "{county} ban the box ordinance",
            "{state} state ban the box preemption",
        ],
    ),
    "state": QueryTemplate(
        name="state",
        patterns=[
            "{state} fair chance act",
            "{state} ban the box statute criminal history",
            "{state} administrative code employment background checks",
        ],
    ),
}


def infer_type_and_tokens(jurisdiction_path: str) -> tuple[str, dict]:
    tokens = {}
    if "/city/" in jurisdiction_path:
        jtype = "city"
        tokens["city"] = jurisdiction_path.split("/city/")[-1].replace(".json", "").replace("_", " ")
        # infer state if available in path preceding city
        parts = jurisdiction_path.split("/")
        if "state" in parts:
            idx = parts.index("state")
            if idx + 1 < len(parts):
                tokens["state"] = parts[idx + 1].replace(".json", "").replace("_", " ")
    elif "/county/" in jurisdiction_path:
        jtype = "county"
        tokens["county"] = jurisdiction_path.split("/county/")[-1].replace(".json", "").replace("_", " ")
        # try infer state
        parts = jurisdiction_path.split("/")
        if "state" in parts:
            idx = parts.index("state")
            if idx + 1 < len(parts):
                tokens["state"] = parts[idx + 1].replace(".json", "").replace("_", " ")
    else:
        jtype = "state"
        # if explicit state path
        if "/state/" in jurisdiction_path:
            tokens["state"] = jurisdiction_path.split("/state/")[-1].replace(".json", "").replace("_", " ")
        else:
            tokens["state"] = ""
    return jtype, tokens


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


def generate_queries(jurisdiction_path: str, topics: List[str] | None = None) -> List[str]:
    jtype, tokens = infer_type_and_tokens(jurisdiction_path)
    tmpl = DEFAULT_TEMPLATES.get(jtype) or DEFAULT_TEMPLATES["state"]
    safe_tokens = _SafeDict(tokens)
    base_queries = [p.format_map(safe_tokens) for p in tmpl.patterns]
    if topics:
        for t in topics:
            subject = tokens.get('city') or tokens.get('county') or tokens.get('state') or ""
            base_queries.append(f"{subject} {t}")
    # unique
    seen = set()
    out: List[str] = []
    for q in base_queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


