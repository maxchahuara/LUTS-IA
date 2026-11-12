import asyncio
import copy
import json
import time

import httpx
import pytest

from max_runtime.alexa import AlexaDenied, handle, response
from max_runtime.app import create_app
from max_runtime.config import Entity, Settings
from max_runtime.research import read_page
from max_runtime.runtime import Runtime, direct_actions, voice_text
from max_runtime.store import Store


@pytest.fixture
def cfg(tmp_path):
    return Settings(state_dir=tmp_path, api_token="a" * 48, identity_salt="b" * 48,
                    bridge_token="c" * 48, alexa_skill_id="amzn1.ask.skill.test",
                    alexa_users=["user-one", "user-two"], ha_token="test-ha",
                    entities={"tv": Entity(entity_id="media_player.tv",
                              aliases=["la tv de la sala", "tv de la sala"],
                              actions=["turn_on", "turn_off", "volume_set", "select_source"])})


class FakeEngine:
    def __init__(self):
        self.calls = []

    async def complete(self, job, history, notes, sources, capabilities):
        self.calls.append((job, history, notes))
        return {"text": "Respuesta de prueba", "actions": []}, {"completed": True}


def envelope(user="user-one", device="echo-one", request_id="one", intent="GptQueryIntent"):
    return {"context": {"System": {"application": {"applicationId": "amzn1.ask.skill.test"},
            "user": {"userId": user}, "device": {"deviceId": device}}},
            "session": {"sessionId": "session-one"}, "request": {
                "type": "IntentRequest", "requestId": request_id,
                "intent": {"name": intent, "slots": {"query": {"value": "hola"}}}}}


def test_request_deduplication_and_identity_boundaries(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    first, created = store.create("alice", "s1", "d1", "request1", "enciende tv")
    duplicate, again = store.create("alice", "s2", "d2", "request1", "otro texto")
    other, _ = store.create("bob", "s1", "d1", "request1", "hola")
    assert created and not again and first["id"] == duplicate["id"]
    assert first["id"] != other["id"] and store.get(first["id"], "bob") is None
    assert store.latest("alice", "d2") is None
    store.note("alice", "mi información")
    assert store.notes("bob") == []


def test_crash_recovery_does_not_repeat_unknown_action(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    job, _ = store.create("u", "s", "d", "r", "enciende tv")
    store.claim()
    store.action_start(job["id"], 0, {"operation": "turn_on"})
    reopened = Store(tmp_path / "state.sqlite3")
    assert reopened.recover() == 1
    assert reopened.get(job["id"], "u")["status"] == "interrupted"
    assert reopened.claim() is None
    with pytest.raises(RuntimeError):
        reopened.action_start(job["id"], 0, {"operation": "turn_on"})


def test_cancel_cannot_be_overwritten_by_late_completion(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    job, _ = store.create("u", "s", "d", "r", "hola")
    store.claim()
    assert store.cancel(job["id"], "u")
    store.finish(job["id"], "succeeded", {"text": "demasiado tarde"})
    assert store.get(job["id"], "u")["status"] == "canceled"


def test_same_conversation_is_serialized(tmp_path):
    store = Store(tmp_path / "state.sqlite3")
    one, _ = store.create("u", "s", "d", "r1", "uno")
    two, _ = store.create("u", "s", "d", "r2", "dos")
    store.claim()
    assert store.claim() is None
    store.finish(one["id"], "succeeded", {"text": "respuesta uno"})
    assert store.claim()["id"] == two["id"]
    assert store.history("u", "s", two["created"])[0]["assistant"] == "respuesta uno"
    assert store.history("other", "s", two["created"]) == []


def test_voice_enqueue_is_fast_and_deduplicated(cfg):
    engine = FakeEngine()
    rt = Runtime(cfg, engine=engine)
    start = time.monotonic()
    first = handle(envelope(), rt)
    again = handle(envelope(), rt)
    assert time.monotonic() - start < 1
    assert first["sessionAttributes"]["jobId"] == again["sessionAttributes"]["jobId"]
    assert engine.calls == []


@pytest.mark.parametrize("change", ["user", "skill", "device"])
def test_untrusted_alexa_identity_is_rejected(cfg, change):
    e = envelope()
    if change == "user":
        e["context"]["System"]["user"]["userId"] = "intruder"
    elif change == "skill":
        e["context"]["System"]["application"]["applicationId"] = "other-skill"
    else:
        e["context"]["System"].pop("device")
    with pytest.raises(AlexaDenied):
        handle(e, Runtime(cfg, engine=FakeEngine()))


def test_result_is_read_from_exact_echo(cfg):
    rt = Runtime(cfg, engine=FakeEngine())
    handle(envelope(), rt)
    e = envelope(device="echo-two", request_id="result", intent="ResultIntent")
    assert "Todavía no tienes" in handle(e, rt)["response"]["outputSpeech"]["ssml"]


def test_untrusted_ssml_is_escaped():
    ssml = response('<audio src="https://example.org/evil"/> & hola')["response"]["outputSpeech"]["ssml"]
    assert "<audio" not in ssml and "&lt;audio" in ssml and "&amp;" in ssml


@pytest.mark.parametrize("text", ["no enciendas la tv de la sala", "cómo enciende la tv de la sala",
                                 "dime si enciende la tv de la sala", "enciende la tv de otra sala"])
def test_questions_negations_and_unknown_targets_are_not_actions(cfg, text):
    assert direct_actions(text, cfg.entities) is None


def test_multiple_explicit_commands(cfg):
    actions = direct_actions("enciende la tv de la sala y pon el volumen de la tv de la sala al 30", cfg.entities)
    assert [a.operation for a in actions] == ["turn_on", "volume_set"]
    assert actions[1].value == 0.3


async def test_api_tokens_have_distinct_authority(cfg):
    rt = Runtime(cfg, engine=FakeEngine())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(cfg, rt)),
                                 base_url="http://test") as client:
        assert (await client.get("/v1/jobs")).status_code == 401
        assert (await client.get("/v1/jobs", headers={"Authorization": "Bearer " + cfg.bridge_token})).status_code == 401
        assert (await client.post("/v1/voice", json=envelope(), headers={"Authorization": "Bearer " + cfg.api_token})).status_code == 401
        assert (await client.post("/v1/voice", json=envelope(), headers={"Authorization": "Bearer " + cfg.bridge_token})).status_code == 200
        assert (await client.post("/alexa", json=envelope())).status_code == 400
    await rt.close()


async def test_only_verified_home_state_is_reported_as_confirmed(cfg):
    sent = []
    def handler(req):
        if req.method == "POST":
            sent.append(json.loads(req.content))
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"entity_id": "media_player.tv", "state": "on",
                                        "attributes": {"volume_level": 0.3}})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    engine = FakeEngine()
    rt = Runtime(cfg, engine=engine, client=client)
    job = rt.submit("u", "s", "d", "r", "enciende la tv de la sala")
    rt.store.claim()
    await rt.process(job)
    result = rt.store.get(job["id"], "u")
    assert result["result"]["verified"] is True
    assert len(sent) == 1 and engine.calls == []
    assert rt.store.evidence(job["id"])[0]["status"] == "verified"
    await rt.close()


async def test_disallowed_batch_sends_no_partial_actions(cfg):
    sent = []
    def handler(req):
        sent.append(req)
        return httpx.Response(200, json=[])
    rt = Runtime(cfg, engine=FakeEngine(), client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    job = rt.submit("u", "s", "d", "r", "enciende la tv de la sala y pon el volumen de la tv de la sala al 95")
    rt.store.claim()
    await rt.process(job)
    assert sent == [] and rt.store.get(job["id"], "u")["status"] == "failed"
    await rt.close()


async def test_model_actions_are_not_executed_without_approved_command(cfg):
    engine = FakeEngine()
    async def injected(*args):
        return {"text": "ok", "actions": [{"target": "tv", "operation": "turn_on"}]}, {}
    engine.complete = injected
    rt = Runtime(cfg, engine=engine)
    job = rt.submit("u", "s", "d", "r", "qué es un televisor")
    rt.store.claim()
    await rt.process(job)
    assert rt.store.evidence(job["id"]) == []
    assert "No he enviado acciones" in rt.store.get(job["id"], "u")["result"]["text"]
    await rt.close()


@pytest.mark.parametrize("url", ["http://127.0.0.1/config", "http://169.254.169.254/",
                                "http://[::1]/", "file:///etc/passwd", "https://user:pass@example.com/"])
async def test_reader_refuses_private_networks_and_credentials(url):
    async with httpx.AsyncClient(trust_env=False) as client:
        with pytest.raises(ValueError):
            await read_page(client, url)


async def test_reader_rechecks_redirects_and_pins_dns(monkeypatch):
    import max_runtime.research as module
    addresses = []
    async def address(host):
        addresses.append(host)
        if host == "internal.example":
            raise ValueError("private")
        return "93.184.216.34"
    monkeypatch.setattr(module, "public_address", address)
    def handler(req):
        assert req.url.host == "93.184.216.34"
        assert req.headers["host"] == "public.example"
        assert req.extensions["sni_hostname"] == "public.example"
        return httpx.Response(302, headers={"location": "http://internal.example/secret"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError):
            await read_page(client, "https://public.example/")
    assert addresses == ["public.example", "internal.example"]


async def test_recovery_worker_finishes_persistent_queued_job(cfg):
    rt = Runtime(cfg, engine=FakeEngine())
    job = rt.submit("u", "s", "d", "r", "hola")
    await rt.start()
    for _ in range(30):
        if rt.store.get(job["id"], "u")["status"] == "succeeded":
            break
        await asyncio.sleep(0.05)
    assert rt.store.get(job["id"], "u")["status"] == "succeeded"
    await rt.close()


def test_off_by_default_alexa(cfg):
    private = cfg.model_copy(update={"alexa_users": []})
    with pytest.raises(AlexaDenied):
        handle(copy.deepcopy(envelope()), Runtime(private, engine=FakeEngine()))


def test_oauth_state_survives_restart_but_cannot_be_replayed(tmp_path):
    path = tmp_path / "oauth.sqlite3"
    Store(path).oauth_issue("random-state")
    restarted = Store(path)
    assert not restarted.oauth_consume("wrong-state")
    assert restarted.oauth_consume("random-state")
    assert not restarted.oauth_consume("random-state")


async def test_verified_sdk_dispatch_preserves_response_and_job_attributes(cfg, monkeypatch):
    from datetime import datetime, timezone

    from ask_sdk_webservice_support.verifier import RequestVerifier
    # Solo la firma externa se simula; se ejercitan serialización y timestamp del SDK real.
    monkeypatch.setattr(RequestVerifier, "verify", lambda *args, **kwargs: None)
    rt = Runtime(cfg, engine=FakeEngine())
    e = envelope()
    e["version"] = "1.0"
    e["request"]["timestamp"] = datetime.now(timezone.utc).isoformat()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(cfg, rt)),
                                 base_url="http://test") as client:
        r = await client.post("/alexa", json=e)
    assert r.status_code == 200
    data = r.json()
    assert data["sessionAttributes"]["jobId"]
    assert data["response"]["outputSpeech"]["type"] == "SSML"
    await rt.close()


async def test_public_ingress_does_not_publish_administration():
    from max_runtime.edge import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://edge") as client:
        for path in ["/v1/jobs", "/v1/status", "/v1/setup/home-assistant", "/v1/devices", "/docs"]:
            assert (await client.get(path)).status_code == 404
        assert (await client.post("/alexa", json={})).status_code == 400


def test_owner_link_is_explicit_and_other_alexa_users_remain_separate(cfg):
    linked = cfg.model_copy(update={"owner_alexa_user": "user-one"})
    rt = Runtime(linked, engine=FakeEngine())
    rt.store.note(rt.owner, "preferencia compartida")
    assert rt.store.notes(rt.identity("alexa:user-one"))
    assert rt.store.notes(rt.identity("alexa:user-two")) == []
    assert Runtime(cfg, engine=FakeEngine()).owner != rt.owner


def test_voice_result_keeps_sources_in_report_without_reading_raw_urls():
    text = voice_text({"status": "succeeded", "result": {
        "text": "Resumen con [fuente](https://example.org/documento). Más: https://example.org/otra",
        "sources": [{"url": "https://example.org/documento"}],
    }})
    assert "https://" not in text and "fuente" in text and "informe" in text


async def test_voice_ingress_preserves_amazon_sha256_signature_and_exact_body():
    from max_runtime.edge import app
    captured = []
    def backend(req):
        captured.append(req)
        return httpx.Response(200, json={"version": "1.0", "response": {}})
    async with app.router.lifespan_context(app):
        await app.state.client.aclose()
        app.state.client = httpx.AsyncClient(base_url="http://127.0.0.1:8787",
                                            transport=httpx.MockTransport(backend))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://edge") as client:
            raw = b'{ "request": {"type": "LaunchRequest"} }'
            result = await client.post("/alexa", content=raw, headers={
                "Signature-256": "example-amazon-signature",
                "SignatureCertChainUrl": "https://s3.amazonaws.com/echo.api/test.pem",
                "Content-Type": "application/json",
            })
        assert result.status_code == 200 and len(captured) == 1
        assert captured[0].content == raw
        assert captured[0].headers["signature-256"] == "example-amazon-signature"


def test_echo_label_requires_same_user_and_survives_restart(tmp_path):
    path = tmp_path / "devices.sqlite3"
    store = Store(path)
    store.create("alice", "session", "echo-alice", "r1", "hola")
    assert not store.label_device("bob", "echo-alice", "otro nombre")
    assert store.label_device("alice", "echo-alice", "Echo de la sala")
    reopened = Store(path)
    assert reopened.devices("alice")[0]["name"] == "Echo de la sala"
    assert reopened.devices("bob") == []


async def test_echo_can_identify_itself_without_calling_model(cfg):
    engine = FakeEngine()
    rt = Runtime(cfg, engine=engine)
    app = create_app(cfg, rt)
    e = envelope()
    e["request"]["intent"]["slots"]["query"]["value"] = "identifica este dispositivo como Echo sala"
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/v1/voice", json=e, headers={"Authorization": "Bearer " + cfg.bridge_token})
    assert r.status_code == 200 and "Registré este dispositivo" in r.json()["response"]["outputSpeech"]["ssml"]
    assert engine.calls == []


async def test_source_command_uses_available_canonical_name_and_checks_state(cfg):
    sent = []
    def backend(req):
        if req.method == "POST":
            sent.append(json.loads(req.content))
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"entity_id": "media_player.tv", "state": "on",
            "attributes": {"source_list": ["Netflix", "HDMI 1"], "source": "Netflix"}})
    engine = FakeEngine()
    rt = Runtime(cfg, engine=engine, client=httpx.AsyncClient(transport=httpx.MockTransport(backend)))
    job = rt.submit("u", "s", "d", "r", "abre netflix en la tv de la sala")
    rt.store.claim()
    await rt.process(job)
    assert sent == [{"entity_id": "media_player.tv", "source": "Netflix"}]
    assert rt.store.get(job["id"], "u")["result"]["verified"] is True
    assert engine.calls == []
    await rt.close()


async def test_second_runtime_cannot_interrupt_active_jobs(cfg):
    first = Runtime(cfg, engine=FakeEngine())
    second = Runtime(cfg, engine=FakeEngine())
    await first.start()
    job = first.submit("u", "s", "d", "r", "hola")
    first.store.claim()
    with pytest.raises(RuntimeError, match="otro runtime"):
        await second.start()
    assert first.store.get(job["id"], "u")["status"] == "running"
    await first.close()
    await second.close()


async def test_public_health_reports_runtime_state_without_private_data():
    from max_runtime.edge import app
    def backend(req):
        assert req.url.path == "/health" and req.method == "GET"
        return httpx.Response(200, json={"service": "MAX", "status": "ok", "version": "0.1.1",
                                       "api_token": "must-stay-private", "household": "private"})
    async with app.router.lifespan_context(app):
        await app.state.client.aclose()
        app.state.client = httpx.AsyncClient(base_url="http://127.0.0.1:8787",
                                            transport=httpx.MockTransport(backend))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://edge") as client:
            r = await client.get("/", follow_redirects=True)
            assert r.status_code == 200
            assert r.json() == {"service": "MAX", "status": "ok", "version": "0.1.1"}
            assert (await client.get("/v1/status")).status_code == 404


@pytest.mark.parametrize("failure", ["offline", "bad_status", "invalid_json"])
async def test_public_health_is_unavailable_until_runtime_is_ready(failure):
    from max_runtime.edge import app
    def backend(req):
        if failure == "offline":
            raise httpx.ConnectError("private connection detail", request=req)
        if failure == "bad_status":
            return httpx.Response(503, text="private startup detail")
        return httpx.Response(200, text="private invalid response")
    async with app.router.lifespan_context(app):
        await app.state.client.aclose()
        app.state.client = httpx.AsyncClient(base_url="http://127.0.0.1:8787",
                                            transport=httpx.MockTransport(backend))
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://edge") as client:
            r = await client.get("/health")
            assert r.status_code == 503
            assert r.json() == {"service": "MAX", "status": "starting"}
