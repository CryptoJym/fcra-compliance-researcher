from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


class SecretsProvider:
    def __init__(self, json_path: Optional[Path] = None, namespace: Optional[str] = None):
        self.namespace = namespace or "default"
        self.data: dict[str, Any] = {}
        if json_path is None:
            env_path = os.getenv("SECRETS_JSON_PATH")
            if env_path:
                json_path = Path(env_path)
            else:
                json_path = Path.cwd() / ".secrets.json"
        try:
            if json_path.exists():
                raw = json.loads(json_path.read_text())
                if isinstance(raw, dict):
                    self.data = raw
        except Exception:
            # Ignore malformed file
            self.data = {}
        # Try keyring lazily
        try:
            import keyring  # type: ignore
            self._keyring = keyring
        except Exception:
            self._keyring = None

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        # 1) Environment wins
        if name in os.environ and os.environ.get(name):
            return os.environ.get(name)
        # 2) JSON file (namespaced or flat)
        if self.data:
            if name in self.data and self.data.get(name):
                return str(self.data.get(name))
            ns = self.data.get(self.namespace) or {}
            if isinstance(ns, dict) and name in ns and ns.get(name):
                return str(ns.get(name))
        # 3) Keyring (optional)
        if self._keyring is not None:
            try:
                val = self._keyring.get_password(self.namespace, name)
                if val:
                    return val
            except Exception:
                pass
        return default


def get_default_provider() -> SecretsProvider:
    ns = os.getenv("SECRETS_NAMESPACE") or "default"
    path_env = os.getenv("SECRETS_JSON_PATH")
    json_path = Path(path_env) if path_env else None
    return SecretsProvider(json_path=json_path, namespace=ns)
