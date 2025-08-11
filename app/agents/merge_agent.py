from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Tuple

from .base import Agent
from ..core.github_service import create_branch_and_commit_and_pr
import runpy, sys, io, contextlib


class MergeAgent(Agent):
    def __init__(self):
        super().__init__("merge_agent")

    def run(self, jurisdiction_file: Path, patch_file: Path) -> Tuple[bool, Dict]:
        try:
            # Ensure we pass absolute paths and set cwd to repo root for reliable script invocation
            repo_root = Path(__file__).resolve().parents[2]
            proc = subprocess.run([
                "python", str(repo_root / "tools" / "apply_research_patch.py"), "--file", str(jurisdiction_file), "--input", str(patch_file)
            ], capture_output=True, text=True, check=False, cwd=repo_root)
            success = proc.returncode == 0
            details = {
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            # Fallback inline execution (helps in test environments where CWD/path handling differs)
            if not success:
                buf_out, buf_err = io.StringIO(), io.StringIO()
                old_argv = list(sys.argv)
                try:
                    sys.argv = [
                        "apply_research_patch.py",
                        "--file",
                        str(jurisdiction_file),
                        "--input",
                        str(patch_file),
                    ]
                    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                        runpy.run_path(str(repo_root / "tools" / "apply_research_patch.py"), run_name="__main__")
                    # If script didn't sys.exit non-zero, treat as success
                    success = True
                except SystemExit as e:  # capture explicit exit codes
                    success = int(getattr(e, "code", 1) or 0) == 0
                except Exception as _:
                    success = False
                finally:
                    sys.argv = old_argv
                details.setdefault("stdout", "")
                details.setdefault("stderr", "")
                details["stdout"] += buf_out.getvalue()
                details["stderr"] += buf_err.getvalue()
            if success:
                # Attempt to open a PR with the updated file, but do not fail the merge if PR automation is disabled
                try:
                    pr = create_branch_and_commit_and_pr(
                        jurisdiction_file,
                        pr_title=f"Update {jurisdiction_file}",
                        pr_body=f"Automated patch applied for {jurisdiction_file}",
                    )
                    details["pr_url"] = pr.pr_url
                except Exception as e:
                    details["pr_error"] = str(e)
            return success, details
        except Exception as e:
            return False, {"error": str(e)}
