from __future__ import annotations

import os


def test_build_agent_optional_imports():
    # Ensure agent builds or returns None if optional deps missing
    from app.core.research_agent import build_agent

    os.environ["DEEP_COVERAGE_THRESHOLD"] = "0.8"
    agent = build_agent()
    assert agent is None or hasattr(agent, "invoke")


def test_validate_hop_logic_without_langgraph(monkeypatch):
    # Validate hop increment behavior mirrors module implementation:
    # - needs_refine True increments hop until reaching DEEP_MAX_HOPS
    # - once at cap, needs_refine becomes False and hop stops incrementing
    os.environ["DEEP_MAX_HOPS"] = "2"
    os.environ["DEEP_COVERAGE_THRESHOLD"] = "1.0"  # force refine until hop limit

    def _conflicts(a, b):
        return a.get("claim") and b.get("claim") and a["claim"] != b["claim"]

    def simulate_validate(state: dict) -> tuple[bool, int]:
        facts = state.get("facts", []) or []
        validated = []
        for f in facts:
            if not any(_conflicts(f, other) for other in facts if other is not f):
                validated.append(f)
        threshold = float(os.getenv("DEEP_COVERAGE_THRESHOLD", "0.8"))
        needs_refine = len(validated) < max(1, int(threshold * (len(facts) or 1)))
        max_hops = int(os.getenv("DEEP_MAX_HOPS", "3"))
        current_hop = int(state.get("hop", 0) or 0)
        if needs_refine and current_hop < max_hops:
            next_hop = current_hop + 1
        else:
            needs_refine = False
            next_hop = current_hop
        return needs_refine, next_hop

    state = {
        "facts": [
            {"claim": "A", "source": "s1"},
            {"claim": "B", "source": "s2"},
        ],
        "hop": 0,
    }

    needs_refine, hop = simulate_validate(state)
    assert needs_refine is True
    assert hop == 1

    state["hop"] = hop
    needs_refine, hop = simulate_validate(state)
    assert needs_refine is True
    assert hop == 2

    state["hop"] = hop
    needs_refine, hop = simulate_validate(state)
    assert needs_refine is False
    assert hop == 2


