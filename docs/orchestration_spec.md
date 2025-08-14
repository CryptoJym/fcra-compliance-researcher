## Orchestration & Agents Specification (LangGraph)

### Purpose
Replace linear agent execution with a LangGraph state graph enabling multi-hop planning, validation, and provenance.

### Scope
- Add `app/core/research_agent.py` implementing the graph with guarded imports for optional dependencies.
- Keep existing `app/agents/*` for compatibility; add a `--deep-research` flag to route to the graph.

### Nodes
- plan → search → crawl → extract → validate → synthesize → cite → END
- Conditional edge: validate loops back to plan when coverage < threshold.

### Testing Criteria
- Unit test ensures hops ≤ 3, state includes citations, and no infinite loops.


