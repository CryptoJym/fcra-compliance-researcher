from __future__ import annotations

import os


def test_build_agent_optional_imports():
    # Ensure agent builds or returns None if optional deps missing
    from app.core.research_agent import build_agent

    os.environ["DEEP_COVERAGE_THRESHOLD"] = "0.8"
    os.environ["DEEP_MAX_HOPS"] = "2"
    agent = build_agent()
    assert agent is None or hasattr(agent, "invoke")


