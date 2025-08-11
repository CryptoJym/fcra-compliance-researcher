from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple

from .base import Agent


class ValidationAgent(Agent):
    def __init__(self):
        super().__init__("validation_agent")

    def run(self, jurisdiction_file: Path, patch_file: Path) -> Tuple[bool, Dict]:
        try:
            proc = subprocess.run([
                "python", "tools/validate_matrix.py", "--file", str(jurisdiction_file), "--input", str(patch_file)
            ], capture_output=True, text=True, check=False)
            success = proc.returncode == 0
            details = {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            return success, details
        except Exception as e:
            return False, {"error": str(e)}
