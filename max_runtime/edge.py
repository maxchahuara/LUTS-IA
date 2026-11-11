"""Entrada pública limitada a voz; nunca publica la API de administración."""
import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response


@asynccontextmanager
async def lifespan(app):
    app.state.client = httpx.AsyncClient(base_url="http://127.0.0.1:8787", trust_env=False,
                                        timeout=5, follow_redirects=False)
    app.state.limit = asyncio.Semaphore(4)
    yield
    await app.state.client.aclose()


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.post("/alexa")
@app.post("/v1/voice")
async def voice(request: Request):
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 65536:
            raise HTTPException(413, "Petición demasiado grande")
    if request.url.path == "/alexa" and not (
            (request.headers.get("signature-256") or request.headers.get("signature"))
            and request.headers.get("signaturecertchainurl")):
        raise HTTPException(400, "Falta firma Alexa")
    headers = {k: v for k, v in request.headers.items() if k.lower() in {
        "content-type", "signature", "signature-256", "signaturecertchainurl", "authorization"}}
    try:
        async with app.state.limit:
            r = await app.state.client.post(request.url.path, content=bytes(raw), headers=headers)
        return Response(r.content, status_code=r.status_code, media_type="application/json")
    except httpx.HTTPError:
        raise HTTPException(503, "MAX no está disponible") from None
