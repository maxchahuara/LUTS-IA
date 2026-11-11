from __future__ import annotations

import asyncio
import hmac
import json
import secrets
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from . import __version__
from .alexa import AlexaDenied, handle, response
from .config import Settings
from .runtime import Runtime, direct_actions, normalize, voice_text


class Command(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    request_id: str = Field(min_length=1, max_length=200)
    session: str = Field(default="local", min_length=1, max_length=200)


def create_app(settings=None, runtime=None):
    cfg = settings or Settings.load()
    rt = runtime or Runtime(cfg)

    @asynccontextmanager
    async def lifespan(app):
        await rt.start()
        yield
        await rt.close()

    app = FastAPI(title="MAX", version=__version__, lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.runtime = rt

    def owner(authorization: str = Header(default="")):
        if not hmac.compare_digest(authorization, "Bearer " + cfg.api_token):
            raise HTTPException(401, "Autenticación requerida")
        return rt.owner

    @app.get("/health")
    def health():
        return {"service": "MAX", "version": __version__, "status": "ok"}

    @app.get("/v1/status")
    def status(principal=Depends(owner)):
        return {"service": "MAX", "version": __version__,
                "public_url": cfg.public_url,
                "home_assistant": "linked" if rt.home.configured else "setup_required",
                "authorized_entities": list(cfg.entities),
                "alexa": "configured" if cfg.alexa_skill_id and cfg.alexa_users else "setup_required",
                "workers": len(rt.workers), "last_engine_receipt": rt.last_engine_receipt}

    @app.post("/v1/requests", status_code=202)
    def submit(command: Command, principal=Depends(owner)):
        try:
            return rt.submit(principal, rt.identity(command.session), rt.identity("local-device"),
                             command.request_id, command.text)
        except OverflowError:
            raise HTTPException(429, "La cola está llena") from None

    @app.get("/v1/jobs")
    def jobs(principal=Depends(owner)):
        return rt.store.recent(principal)

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: str, principal=Depends(owner)):
        job = rt.store.get(job_id, principal)
        if not job:
            raise HTTPException(404, "Trabajo no encontrado")
        job["evidence"] = rt.store.evidence(job_id)
        return job

    @app.post("/v1/jobs/{job_id}/cancel")
    def cancel(job_id: str, principal=Depends(owner)):
        if not rt.store.get(job_id, principal):
            raise HTTPException(404, "Trabajo no encontrado")
        return {"canceled": rt.cancel(job_id, principal)}

    @app.get("/v1/jobs/{job_id}/report")
    def report(job_id: str, principal=Depends(owner)):
        job = rt.store.get(job_id, principal)
        if not job or not job.get("result") or not job["result"].get("report"):
            raise HTTPException(404, "Informe no disponible")
        return FileResponse(cfg.state_dir / "reports" / (job["id"] + ".md"),
                            media_type="text/markdown", filename="informe-max.md")

    @app.get("/v1/devices")
    async def devices(principal=Depends(owner)):
        if not rt.home.configured:
            raise HTTPException(409, "Vincula Home Assistant primero")
        return await rt.home.states()

    @app.get("/v1/notes")
    def notes(principal=Depends(owner)):
        return rt.store.notes(principal)

    @app.get("/v1/alexa/devices")
    def voice_devices(principal=Depends(owner)):
        return [d for d in rt.store.devices(principal) if d["id"] != rt.identity("local-device")]

    @app.delete("/v1/notes/{note_id}")
    def forget(note_id: str, principal=Depends(owner)):
        return {"deleted": bool(rt.store.forget(principal, note_id))}

    @app.post("/v1/setup/home-assistant")
    def link_home(principal=Depends(owner)):
        state = secrets.token_urlsafe(32)
        rt.store.oauth_issue(state)
        base = (cfg.ha_authorize_url or cfg.ha_url).rstrip("/")
        return {"url": base + "/auth/authorize?" + urlencode({
            "client_id": cfg.ha_client_id, "redirect_uri": cfg.ha_client_id + "setup/ha/callback",
            "state": state,
        })}

    @app.get("/setup/ha/callback", response_class=HTMLResponse)
    async def callback(state: str = "", code: str = ""):
        if not code or not rt.store.oauth_consume(state):
            raise HTTPException(403, "Solicitud de vinculación expirada o inválida")
        r = await rt.client.post(cfg.ha_url.rstrip("/") + "/auth/token", data={
            "grant_type": "authorization_code", "code": code, "client_id": cfg.ha_client_id,
        }, timeout=10)
        if r.status_code != 200 or "refresh_token" not in r.json():
            raise HTTPException(502, "Home Assistant no completó la vinculación")
        cfg.ha_refresh_token = r.json()["refresh_token"]
        cfg.save()
        return "<h1>MAX conectado a Home Assistant</h1><p>Puedes cerrar esta pestaña.</p>"

    async def body(request):
        if int(request.headers.get("content-length", 0)) > 65536:
            raise HTTPException(413, "Petición demasiado grande")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 65536:
                raise HTTPException(413, "Petición demasiado grande")
        return bytes(raw)

    async def alexa_response(envelope):
        try:
            return await settle_reply(handle(envelope, rt), envelope)
        except AlexaDenied as exc:
            raise HTTPException(403, str(exc)) from None
        except OverflowError:
            raise HTTPException(429, "Cola llena") from None

    async def settle_reply(reply, envelope):
        job_id = reply.get("sessionAttributes", {}).get("jobId")
        if not job_id:
            return reply
        system = envelope.get("context", {}).get("System", {})
        user = system.get("user", envelope.get("session", {}).get("user", {})).get("userId", "")
        principal = rt.identity("alexa:" + user)
        job = rt.store.get(job_id, principal)
        if not job:
            return reply
        quick = bool(direct_actions(job["text"], cfg.entities)) or normalize(job["text"]).startswith(
            ("identifica este dispositivo como ", "recuerda que ", "olvida ", "mis notas", "que recuerdas"))
        if not quick:
            return reply
        for _ in range(12):
            job = rt.store.get(job_id, principal)
            if job["status"] not in {"queued", "running"}:
                return response(voice_text(job), attributes={"jobId": job_id})
            await asyncio.sleep(0.1)
        return reply

    @app.post("/v1/voice")
    async def lambda_bridge(request: Request, authorization: str = Header(default="")):
        if not cfg.bridge_token or not hmac.compare_digest(authorization, "Bearer " + cfg.bridge_token):
            raise HTTPException(401, "Puente no autorizado")
        try:
            envelope = json.loads(await body(request))
        except (ValueError, UnicodeError):
            raise HTTPException(400, "JSON inválido") from None
        if not isinstance(envelope, dict):
            raise HTTPException(400, "Sobre Alexa inválido")
        return await alexa_response(envelope)

    @app.post("/alexa")
    async def signed_alexa(request: Request):
        if not cfg.alexa_skill_id or not cfg.alexa_users:
            raise HTTPException(503, "Skill pendiente de vinculación")
        from ask_sdk_core.dispatch_components import AbstractRequestHandler
        from ask_sdk_core.skill_builder import SkillBuilder
        from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler

        class Forward(AbstractRequestHandler):
            def can_handle(self, handler_input):
                return True

            def handle(self, handler_input):
                # Se serializa después de la verificación oficial de firma y timestamp.
                from ask_sdk_core.serialize import DefaultSerializer
                from ask_sdk_model import ResponseEnvelope
                payload = DefaultSerializer().serialize(handler_input.request_envelope)
                response = handle(payload, rt)
                handler_input.attributes_manager.session_attributes = response.get("sessionAttributes", {})
                return DefaultSerializer().deserialize(json.dumps(response), ResponseEnvelope).response

        sb = SkillBuilder()
        sb.skill_id = cfg.alexa_skill_id
        sb.add_request_handler(Forward())
        handler = WebserviceSkillHandler(skill=sb.create(), verify_signature=True,
                                         verify_timestamp=True)
        try:
            # Certificados y SDK síncronos no bloquean el bucle de los workers.
            raw = await body(request)
            result = await asyncio.to_thread(handler.verify_request_and_dispatch,
                http_request_headers=dict(request.headers), http_request_body=raw.decode())
            reply = json.loads(result) if isinstance(result, str) else result
            # El SDK ya verificó el sobre antes de permitir consulta de su trabajo.
            return await settle_reply(reply, json.loads(raw))
        except Exception:
            raise HTTPException(400, "Solicitud Alexa no válida") from None

    return app
