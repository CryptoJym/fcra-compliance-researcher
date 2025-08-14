from __future__ import annotations

from typing import TypedDict, List, Dict, Any
import os
import time


class ResearchState(TypedDict, total=False):
    query: str
    sub_queries: List[str]
    docs: List[Dict[str, Any]]
    facts: List[Dict[str, Any]]
    validated_facts: List[Dict[str, Any]]
    output: str
    citations: List[Dict[str, Any]]
    needs_refine: bool
    jurisdiction_path: str
    hop: int


def _try_import_langgraph():
    try:
        from langgraph.graph import StateGraph, END  # type: ignore
        return StateGraph, END
    except Exception:
        return None, None


def _try_import_llms():
    try:
        from langchain_ollama import OllamaLLM  # type: ignore

        return OllamaLLM
    except Exception:
        return None


def build_agent():
    StateGraph, END = _try_import_langgraph()
    if StateGraph is None:
        return None  # Optional dependency not available

    OllamaLLM = _try_import_llms()

    from .search import get_default_search_provider
    from .crawl import fetch_and_extract
    from .retrieval import upsert_docs

    llm_small = None
    llm_large = None
    if OllamaLLM is not None:
        try:
            llm_small = OllamaLLM(model="phi3:latest")
            llm_large = OllamaLLM(model="oss-120b")
        except Exception:
            llm_small = None
            llm_large = None

    def plan_node(state: ResearchState) -> ResearchState:
        query = state.get("query", "")
        if llm_small is not None:
            try:
                plan_text = llm_small.invoke(f"Decompose query into 2-3 FCRA sub-queries: {query}")
                sub_queries = [s.strip("- ") for s in str(plan_text).splitlines() if s.strip()][:3]
            except Exception:
                sub_queries = [query]
        else:
            sub_queries = [query]
        return {"sub_queries": sub_queries}

    def search_node(state: ResearchState) -> ResearchState:
        provider = get_default_search_provider()
        docs: List[Dict[str, Any]] = []
        start = time.monotonic()
        try:
            timeout_s = float(os.getenv("DEEP_SEARCH_TIMEOUT_S", os.getenv("DEEP_NODE_TIMEOUT_S", "20")))
        except Exception:
            timeout_s = 20.0
        for q in (state.get("sub_queries", []) or []):
            if time.monotonic() - start > timeout_s:
                break
            try:
                for r in provider.search(q, num_results=5):
                    if time.monotonic() - start > timeout_s:
                        break
                    docs.append({"url": r.url, "title": r.title, "snippet": r.snippet})
            except Exception:
                # Best-effort: continue to next query on provider errors
                continue
        return {"docs": docs}

    _crawl_cache: Dict[str, Dict[str, Any]] = {}

    def crawl_node(state: ResearchState) -> ResearchState:
        extracted: List[Dict[str, Any]] = []
        for d in state.get("docs", []) or []:
            url = d.get("url") or ""
            try:
                if url in _crawl_cache:
                    extracted.append(_crawl_cache[url])
                else:
                    start = time.monotonic()
                    timeout_s = float(os.getenv("DEEP_NODE_TIMEOUT_S", "20"))
                    res = fetch_and_extract(url)
                    if time.monotonic() - start <= timeout_s:
                        _crawl_cache[url] = res
                        extracted.append(res)
                    else:
                        # Timeout guard: skip
                        continue
            except Exception:
                continue
        return {"docs": extracted}

    def extract_node(state: ResearchState) -> ResearchState:
        # Placeholder extraction; integrate schema-driven prompts later
        facts: List[Dict[str, Any]] = []
        start = time.monotonic()
        try:
            timeout_s = float(os.getenv("DEEP_EXTRACT_TIMEOUT_S", os.getenv("DEEP_NODE_TIMEOUT_S", "20")))
        except Exception:
            timeout_s = 20.0
        for d in state.get("docs", []) or []:
            if time.monotonic() - start > timeout_s:
                break
            facts.append({"source": d.get("source"), "claim": "extracted_field_placeholder"})
        return {"facts": facts}

    def _conflicts(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        # Simple placeholder: different claim strings considered conflict
        return a.get("claim") and b.get("claim") and a["claim"] != b["claim"]

    def validate_node(state: ResearchState) -> ResearchState:
        facts = state.get("facts", []) or []
        validated: List[Dict[str, Any]] = []
        start = time.monotonic()
        try:
            timeout_s = float(os.getenv("DEEP_VALIDATE_TIMEOUT_S", os.getenv("DEEP_NODE_TIMEOUT_S", "20")))
        except Exception:
            timeout_s = 20.0
        for f in facts:
            if time.monotonic() - start > timeout_s:
                break
            if not any(_conflicts(f, other) for other in facts if other is not f):
                validated.append(f)
        threshold = float(os.getenv("DEEP_COVERAGE_THRESHOLD", "0.8"))
        needs_refine = len(validated) < max(1, int(threshold * (len(facts) or 1)))
        # Hop counting logic with cap
        try:
            max_hops = int(os.getenv("DEEP_MAX_HOPS", "3"))
        except Exception:
            max_hops = 3
        current_hop = int(state.get("hop", 0) or 0)
        if needs_refine and current_hop < max_hops:
            # Increment only when we actually intend to refine/loop
            next_hop = current_hop + 1
        else:
            # Reached coverage or hop limit; do not loop further
            needs_refine = False
            next_hop = current_hop
        return {"validated_facts": validated, "needs_refine": needs_refine, "hop": next_hop}

    def synthesize_node(state: ResearchState) -> ResearchState:
        start = time.monotonic()
        try:
            timeout_s = float(os.getenv("DEEP_SYNTH_TIMEOUT_S", os.getenv("DEEP_NODE_TIMEOUT_S", "20")))
        except Exception:
            timeout_s = 20.0
        if llm_large is not None:
            try:
                text = llm_large.invoke(f"Synthesize FCRA compliance from facts: {state.get('validated_facts', [])}")
                # Soft timeout check; if exceeded, fall back
                if time.monotonic() - start > timeout_s:
                    return {"output": "synthesis_placeholder"}
                return {"output": str(text)}
            except Exception:
                pass
        return {"output": "synthesis_placeholder"}

    def cite_node(state: ResearchState) -> ResearchState:
        docs = state.get("docs", []) or []
        citations = []
        for d in docs[:5]:
            citations.append({"claim": "placeholder", "source": d.get("source"), "confidence": 0.9})
        # Upsert evidence docs to Qdrant if available
        try:
            upsert_docs(docs)
        except Exception:
            pass
        # Persist basic provenance best-effort
        try:
            from .provenance import record_provenance  # lazy import
            jpath = state.get("jurisdiction_path") or ""
            for c in citations:
                src = c.get("source")
                if isinstance(src, str) and jpath:
                    record_provenance(jpath, "unknown", src, c.get("claim") or "")
        except Exception:
            pass
        # Best-effort confidence metrics
        try:
            from .cross_validation import confidence_from_citations  # lazy import

            urls = [c.get("source") for c in citations if isinstance(c, dict)]
            conf = confidence_from_citations([u for u in urls if isinstance(u, str)])
        except Exception:
            conf = {"score": 0.0}
        return {"citations": citations, "confidence": conf}

    def decide_to_loop(source_node: str, state: ResearchState) -> str:
        try:
            max_hops = int(os.getenv("DEEP_MAX_HOPS", "3"))
        except Exception:
            max_hops = 3
        current_hop = int(state.get("hop", 0) or 0)
        if state.get("needs_refine") and current_hop < max_hops:
            return "plan"
        return "synthesize"

    graph = StateGraph(ResearchState)
    graph.add_node("plan", plan_node)
    graph.add_node("search", search_node)
    graph.add_node("crawl", crawl_node)
    graph.add_node("extract", extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("cite", cite_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "crawl")
    graph.add_edge("crawl", "extract")
    graph.add_edge("extract", "validate")
    def _increment_hops(state: ResearchState) -> ResearchState:
        state = dict(state)
        state["hops"] = int(state.get("hops", 0)) + 1
        return state  # type: ignore[return-value]

    graph.add_conditional_edges("validate", decide_to_loop, {"plan": "plan", "synthesize": "synthesize"})
    # On re-plan path, increment hop counter via a lambda-node shim if supported
    graph.add_edge("synthesize", "cite")
    graph.add_edge("cite", END)

    return graph.compile()


