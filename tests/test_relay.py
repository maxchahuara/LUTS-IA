import hashlib
import json

import httpx
import pytest

from max_runtime.relay import RelaySettings, load_settings, quick_origin, register_origin


@pytest.fixture
def relay():
    return RelaySettings(public_url="https://max.example.workers.dev", register_token="x" * 48)


@pytest.mark.parametrize("url", ["http://127.0.0.1", "https://example.org", "https://max.example.workers.dev/path",
                                 "https://max.example.workers.dev?secret=x"])
def test_registration_destination_is_limited_to_workers(url):
    with pytest.raises(ValueError):
        RelaySettings(public_url=url, register_token="x" * 48)


async def test_registration_checks_origin_and_confirms_receipt_without_leaking_token(relay):
    origin = "https://test.trycloudflare.com"
    calls = []

    def backend(request):
        calls.append(str(request.url))
        if request.method == "GET":
            assert str(request.url) == origin + "/health"
            assert "authorization" not in request.headers
            return httpx.Response(200, json={"service": "MAX", "status": "ok"})
        assert str(request.url) == relay.public_url + "/internal/relay"
        assert request.headers["authorization"] == "Bearer " + relay.register_token
        assert json.loads(request.content) == {"origin": origin}
        return httpx.Response(200, json={"status": "registered", "origin_hash": hashlib.sha256(origin.encode()).hexdigest()})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        await register_origin(relay, client, origin)
    assert len(calls) == 2


async def test_registration_refuses_wrong_origin_or_receipt(relay):
    for origin in ["http://127.0.0.1:8787", "https://example.org", "https://a.trycloudflare.com/path"]:
        with pytest.raises(ValueError):
            quick_origin(origin)

    def backend(request):
        if request.method == "GET":
            return httpx.Response(200, json={"service": "MAX", "status": "ok"})
        return httpx.Response(200, json={"status": "registered", "origin_hash": "incorrect"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as client:
        with pytest.raises(ValueError, match="destino esperado"):
            await register_origin(relay, client, "https://test.trycloudflare.com")


def test_connector_config_is_private_and_does_not_inherit_other_tunnels(tmp_path):
    bootstrap = tmp_path / "bootstrap.yml"
    bootstrap.write_text("{}")
    path = tmp_path / "relay.json"
    path.write_text(json.dumps({"public_url": "https://max.example.workers.dev",
                               "register_token": "x" * 48, "bootstrap_config": str(bootstrap)}))
    path.chmod(0o600)
    assert load_settings(path).public_url == "https://max.example.workers.dev"
    path.chmod(0o644)
    with pytest.raises(ValueError, match="0600"):
        load_settings(path)
    path.chmod(0o600)
    bootstrap.write_text("tunnel: another-project")
    with pytest.raises(ValueError, match="bootstrap vacía"):
        load_settings(path)
