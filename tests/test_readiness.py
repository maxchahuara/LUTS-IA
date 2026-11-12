import httpx
import pytest

from max_runtime import readiness


@pytest.fixture
def virtual_clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(readiness.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(readiness.time, "sleep", lambda delay: now.__setitem__(0, now[0] + delay))
    return now


def test_waits_for_gateway_startup_instead_of_only_process_liveness(virtual_clock):
    replies = [
        (503, {"ok": False, "status": "starting"}),
        (200, {"ok": True, "status": "starting"}),
        (200, {"ok": True, "status": "started"}),
    ]

    def handle(request):
        assert request.url.path == "/startupz"
        status, body = replies.pop(0)
        return httpx.Response(status, json=body)

    with httpx.Client(base_url="http://gateway", transport=httpx.MockTransport(handle)) as client:
        readiness.wait_for_gateway(client, timeout=5)
    assert not replies
    assert virtual_clock[0] == 2


@pytest.mark.parametrize("failure", ["offline", "invalid_json", "wrong_service", "draining"])
def test_does_not_admit_work_when_gateway_is_unavailable(virtual_clock, failure):
    def handle(request):
        if failure == "offline":
            raise httpx.ConnectError("not listening", request=request)
        if failure == "invalid_json":
            return httpx.Response(200, text="not json")
        if failure == "wrong_service":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(503, json={"ok": False, "status": "draining"})

    with httpx.Client(base_url="http://gateway", transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(TimeoutError, match="no completó su arranque"):
            readiness.wait_for_gateway(client, timeout=2.5)
    assert virtual_clock[0] == 2.5
