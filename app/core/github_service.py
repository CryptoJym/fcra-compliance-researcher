from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from github import Github

from .logger import setup_logger
from ..config.settings import settings


logger = setup_logger("github_service")


@dataclass
class PRResult:
    branch: str
    pr_url: Optional[str]


def _get_repo(client: Github):
    repo_full = settings.github_repo
    if not repo_full:
        raise RuntimeError("GITHUB_REPO not configured")
    return client.get_repo(repo_full)


def create_branch_and_commit_and_pr(
    file_path: Path,
    pr_title: str,
    pr_body: str,
    branch_prefix: str = "research",
) -> PRResult:
    if not settings.github_token or not settings.github_repo:
        logger.info("GitHub automation disabled: missing token or repo")
        return PRResult(branch="", pr_url=None)

    client = Github(settings.github_token)
    repo = _get_repo(client)

    base_branch = settings.github_default_branch or "main"
    base_ref = repo.get_git_ref(f"heads/{base_branch}")
    base_sha = base_ref.object.sha

    branch_name = f"{branch_prefix}/{file_path.stem}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)

    # Read local file content and commit to GitHub on new branch
    content_bytes = file_path.read_bytes()
    content_str = content_bytes.decode("utf-8")

    remote_path = str(file_path)
    if remote_path.startswith(str(Path.cwd())):
        remote_path = str(file_path.relative_to(Path.cwd()))

    try:
        existing = repo.get_contents(remote_path, ref=branch_name)
        repo.update_file(
            path=remote_path,
            message=pr_title,
            content=content_str,
            sha=existing.sha,
            branch=branch_name,
        )
    except Exception:
        repo.create_file(
            path=remote_path,
            message=pr_title,
            content=content_str,
            branch=branch_name,
        )

    pr = repo.create_pull(title=pr_title, body=pr_body, head=branch_name, base=base_branch)
    logger.info(f"Opened PR {pr.html_url}")
    return PRResult(branch=branch_name, pr_url=pr.html_url)
