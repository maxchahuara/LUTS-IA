from __future__ import annotations

import asyncio
import time
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .config import Settings
from .store import Store


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str
    operation: Literal["turn_on", "turn_off", "volume_set", "media_play", "media_pause",
                       "select_source"]
    value: float | str | None = None


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(max_length=4000)
    actions: list[Action] = Field(default_factory=list, max_length=4)


class Home:
    def __init__(self, settings: Settings, store: Store, client: httpx.AsyncClient):
        self.settings, self.store, self.client = settings, store, client
        self.access_token = ""
        self.expires = 0
        self.refresh_lock = asyncio.Lock()

    @property
    def configured(self):
        return bool(self.settings.ha_token or self.settings.ha_refresh_token)

    async def headers(self):
        if self.settings.ha_token:
            return {"Authorization": "Bearer " + self.settings.ha_token}
        async with self.refresh_lock:
            if self.settings.ha_refresh_token and time.time() > self.expires - 60:
                r = await self.client.post(self.settings.ha_url + "/auth/token", data={
                    "grant_type": "refresh_token", "refresh_token": self.settings.ha_refresh_token,
                    "client_id": self.settings.ha_client_id,
                }, timeout=5)
                r.raise_for_status()
                data = r.json()
                self.access_token = data["access_token"]
                self.expires = time.time() + data["expires_in"]
        if not self.access_token:
            raise RuntimeError("Falta vincular Home Assistant")
        return {"Authorization": "Bearer " + self.access_token}

    async def request(self, method, path, **kwargs):
        r = await self.client.request(method, self.settings.ha_url.rstrip("/") + path,
                                      headers=await self.headers(), timeout=5, **kwargs)
        r.raise_for_status()
        return r.json()

    async def states(self):
        states = await self.request("GET", "/api/states")
        # No se envía el inventario privado completo al modelo.
        allowed = {v.entity_id for v in self.settings.entities.values()}
        return [s for s in states if s["entity_id"] in allowed]

    async def execute(self, job_id, step, action: Action):
        entity = self.settings.entities.get(action.target)
        if not entity or action.operation not in entity.actions:
            raise ValueError("Dispositivo o acción fuera de los permisos configurados")
        domain = entity.entity_id.split(".")[0]
        if domain == "scene" and action.operation != "turn_on":
            raise ValueError("Una escena solo permite activación")
        if domain != "media_player" and action.operation not in {"turn_on", "turn_off"}:
            raise ValueError("Esta acción requiere un reproductor")
        payload = {"entity_id": entity.entity_id}
        if action.operation == "volume_set":
            if isinstance(action.value, bool) or not isinstance(action.value, (int, float)):
                raise ValueError("Volumen inválido")
            if not 0 <= action.value <= 0.6:
                raise ValueError("El volumen permitido es de 0 a 60 por ciento")
            payload["volume_level"] = action.value
        elif action.operation == "select_source":
            state = await self.request("GET", "/api/states/" + entity.entity_id)
            matches = [source for source in state.get("attributes", {}).get("source_list", [])
                       if str(source).casefold() == str(action.value).casefold()]
            if len(matches) != 1:
                raise ValueError("Fuente no disponible en el dispositivo")
            action = action.model_copy(update={"value": matches[0]})
            payload["source"] = matches[0]
        elif action.value is not None:
            raise ValueError("Esta acción no recibe parámetros")
        self.store.action_start(job_id, step, action.model_dump())
        try:
            await self.request("POST", f"/api/services/{domain}/{action.operation}", json=payload)
            if domain == "scene":
                evidence = {"entity_id": entity.entity_id, "verified": False,
                            "reason": "Servicio aceptado; una escena no confirma el estado final"}
            else:
                evidence = await self.verify(entity.entity_id, action)
            self.store.action_finish(job_id, step, "verified" if evidence["verified"]
                                     else "unconfirmed", evidence)
            return evidence
        except BaseException:
            self.store.action_finish(job_id, step, "uncertain", {
                "verified": False, "reason": "Respuesta incompleta; no se reintenta automáticamente"})
            raise

    async def verify(self, entity_id, action):
        state = {}
        for _ in range(5):
            state = await self.request("GET", "/api/states/" + entity_id)
            value, attrs = state.get("state"), state.get("attributes", {})
            checks = {
                "turn_off": value == "off",
                "turn_on": value not in {None, "off", "unknown", "unavailable"},
                "media_play": value == "playing", "media_pause": value == "paused",
                "select_source": attrs.get("source") == action.value,
            }
            if action.operation == "volume_set":
                checks["volume_set"] = isinstance(attrs.get("volume_level"), (float, int)) and (
                    abs(attrs["volume_level"] - action.value) < 0.025)
            if checks[action.operation]:
                return {"entity_id": entity_id, "state": value, "verified": True,
                        "volume_level": attrs.get("volume_level"), "source": attrs.get("source")}
            await asyncio.sleep(0.4)
        return {"entity_id": entity_id, "state": state.get("state"), "verified": False,
                "reason": "No se observó el estado solicitado"}
