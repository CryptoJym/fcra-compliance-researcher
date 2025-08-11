from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ResearchTask:
    jurisdiction_path: str
    priority: int
    inserted_at: datetime
    status: str = "pending"  # pending | in_progress | completed | error
    error: Optional[str] = None


class AgentResult(dict):
    pass


class SchemaPatch(Dict[str, Any]):
    """Represents a JSON patch to be applied to a jurisdiction file."""


class Citation(Dict[str, Any]):
    pass
