import os

from agent.graph import disable_tracing_outside_demo_mode


def test_tracing_forced_off_outside_demo_mode(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    disable_tracing_outside_demo_mode()
    assert os.environ["LANGSMITH_TRACING"] == "false"


def test_tracing_allowed_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    disable_tracing_outside_demo_mode()
    assert os.environ["LANGSMITH_TRACING"] == "true"
