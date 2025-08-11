from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Tuple

from .base import Agent
from ..core.github_service import create_branch_and_commit_and_pr


class MergeAgent(Agent):
    def __init__(self):
        super().__init__("merge_agent")

    def run(self, jurisdiction_file: Path, patch_file: Path) -> Tuple[bool, Dict]:
        try:
            proc = subprocess.run([
                "python", "tools/apply_research_patch.py", "--file", str(jurisdiction_file), "--input", str(patch_file)
            ], capture_output=True, text=True, check=False)
            success = proc.returncode == 0
            details = {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            if success:
                # Attempt to open a PR with the updated file
                pr = create_branch_and_commit_and_pr(jurisdiction_file, pr_title=f"Update {jurisdiction_file}", pr_body=f"Automated patch applied for {jurisdiction_file}")
                details["pr_url"] = pr.pr_url
            return success, details
        except Exception as e:
            return False, {"error": str(e)}
