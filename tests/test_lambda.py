import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "1 LUTSIA-ALEXA/lambda/lambda_function.py"
spec = importlib.util.spec_from_file_location("max_lambda", PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def event(stamp=None, skill="skill-one"):
    return {"context": {"System": {"application": {"applicationId": skill}}},
            "request": {"timestamp": (stamp or datetime.now(timezone.utc)).isoformat()}}


@pytest.mark.parametrize("minutes", [-5, 5])
def test_lambda_rejects_stale_and_future_requests(monkeypatch, minutes):
    monkeypatch.setenv("ALEXA_SKILL_ID", "skill-one")
    with pytest.raises(ValueError, match="expirada"):
        bridge.lambda_handler(event(datetime.now(timezone.utc) + timedelta(minutes=minutes)), None)


def test_lambda_rejects_other_skill(monkeypatch):
    monkeypatch.setenv("ALEXA_SKILL_ID", "skill-one")
    with pytest.raises(ValueError, match="no autorizado"):
        bridge.lambda_handler(event(skill="skill-two"), None)


def test_lambda_refuses_insecure_backend(monkeypatch):
    monkeypatch.setenv("ALEXA_SKILL_ID", "skill-one")
    monkeypatch.setenv("MAX_BASE_URL", "http://example.org")
    monkeypatch.setenv("MAX_BRIDGE_TOKEN", "secret")
    result = bridge.lambda_handler(event(), None)
    assert "Falta configurar" in result["response"]["outputSpeech"]["ssml"]
