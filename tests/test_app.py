"""Smoke checks for the consolidated Streamlit entrypoint and its services."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_all_dashboard_views_render(monkeypatch):
    # Keep smoke checks offline even when a developer has configured an API key.
    monkeypatch.setattr("backend.agents.outreach_agent.OPENAI_API_KEY", "")
    app_path = Path(__file__).resolve().parents[1] / "frontend" / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=40).run()
    assert not app.exception
    navigation = app.radio[0]
    for option in navigation.options[1:]:
        app.radio[0].set_value(option).run()
        assert not app.exception
