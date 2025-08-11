from __future__ import annotations

from app.core.logger import setup_logger, set_trace_id


def test_trace_id_in_logs(tmp_path, monkeypatch):
    # Redirect logs dir
    monkeypatch.chdir(tmp_path)
    logger = setup_logger("test")
    set_trace_id("abc123")
    logger.info("hello")
    text = (tmp_path / "logs" / "test.log").read_text()
    assert "trace_id=abc123" in text
