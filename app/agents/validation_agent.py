from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple

from .base import Agent
from ..core.validation_rules import run_internal_checks
<<<<<<< HEAD
=======
from ..core.cross_validation import confidence_metrics
>>>>>>> origin/main


class ValidationAgent(Agent):
    def __init__(self):
        super().__init__("validation_agent")

    def run(self, jurisdiction_file: Path, patch_file: Path) -> Tuple[bool, Dict]:
        # First run internal checks for quick feedback
        ok_internal, details_internal = run_internal_checks(patch_file, str(jurisdiction_file))
        if not ok_internal:
            return False, {"internal": details_internal}
        # Then attempt external schema validator if present
        try:
            proc = subprocess.run([
                "python", "tools/validate_matrix.py", "--file", str(jurisdiction_file), "--input", str(patch_file)
            ], capture_output=True, text=True, check=False)
            success = proc.returncode == 0
            details = {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "internal": details_internal,
            }
            # Add confidence metrics (best-effort)
            try:
                patch_data = json.loads(patch_file.read_text())
                details["confidence"] = confidence_metrics(patch_data)
            except Exception:
                pass
            return success, details
        except FileNotFoundError:
            # If external tool not available, rely on internal checks
<<<<<<< HEAD
            return True, {"internal": details_internal, "warning": "External validator not found"}
=======
            out = {"internal": details_internal, "warning": "External validator not found"}
            try:
                patch_data = json.loads(patch_file.read_text())
                out["confidence"] = confidence_metrics(patch_data)
            except Exception:
                pass
            return True, out
>>>>>>> origin/main
        except Exception as e:
            return False, {"error": str(e)}
