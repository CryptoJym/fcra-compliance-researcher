from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from app.core.github_service import create_branch_and_commit_and_pr, PRResult


class DummyRepo:
    def __init__(self):
        self.refs = {}
        self.files = {}
        self.pulls = []
    def get_git_ref(self, name):
        return SimpleNamespace(object=SimpleNamespace(sha="base-sha"))
    def create_git_ref(self, ref, sha):
        self.refs[ref] = sha
    def get_contents(self, path, ref=None):
        class E: pass
        raise Exception("not found")
    def update_file(self, **kwargs):
        self.files[kwargs["path"]] = kwargs["content"]
    def create_file(self, **kwargs):
        self.files[kwargs["path"]] = kwargs["content"]
    def create_pull(self, **kwargs):
        pr = SimpleNamespace(html_url="http://example/pr/1")
        self.pulls.append(pr)
        return pr

class DummyGithub:
    def __init__(self, *args, **kwargs):
        pass
    def get_repo(self, full):
        return DummyRepo()


def test_create_branch_and_commit_and_pr(monkeypatch, tmp_path):
    # Monkeypatch settings
    import app.core.github_service as gh
    from app.config.settings import settings
    monkeypatch.setenv("GITHUB_REPO", "user/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    # Patch module settings to reload with env
    gh.settings.github_repo = "user/repo"
    gh.settings.github_token = "token"

    # Patch Github client
    monkeypatch.setattr(gh, "Github", DummyGithub)

    f = tmp_path / "unified" / "state" / "ca.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("{}")

    res: PRResult = create_branch_and_commit_and_pr(f, "Title", "Body")
    assert isinstance(res, PRResult)
