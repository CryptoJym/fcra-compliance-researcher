from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..core.logger import setup_logger


class Agent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(name)

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
