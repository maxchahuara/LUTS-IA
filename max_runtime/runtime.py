from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import re
import unicodedata

import httpx

from .config import Settings
from .engine import Engine
from .home import Action, Home, Plan
from .research import Research
from .store import Store

log = logging.getLogger("max")


def normalize(text):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", text.lower())
                            if not unicodedata.combining(c)).split()).strip(" .!¿?")


def direct_actions(text, entities):
    """Gramática cerrada: solo órdenes completas, nunca subcadenas de una pregunta."""
    text = normalize(text)
    text = re.sub(r"^(?:max[, ]+)?(?:por favor[, ]+)?", "", text)
    clauses = re.split(r"\s+y\s+", text)
    if len(clauses) > 4:
        return None
    actions = []
    verbs = {"enciende": "turn_on", "prende": "turn_on", "activa": "turn_on",
             "apaga": "turn_off", "desactiva": "turn_off", "pausa": "media_pause",
             "reproduce": "media_play"}
    for clause in clauses:
        match = re.fullmatch(r"(enciende|prende|activa|apaga|desactiva|pausa|reproduce) (.+)", clause)
        operation, value, target = None, None, None
        if match:
            operation, target = verbs[match[1]], match[2]
        volume = re.fullmatch(r"(?:pon|ajusta) (?:el )?volumen de (.+) (?:al|a) (\d{1,3})(?: por ciento)?", clause)
        if volume:
            operation, target, value = "volume_set", volume[1], int(volume[2]) / 100
        source = re.fullmatch(r"(?:pon|abre) (.+) en (.+)", clause)
        if source:
            operation, value, target = "select_source", source[1], source[2]
        source = re.fullmatch(r"cambia (?:la )?entrada de (.+) a (.+)", clause)
        if source:
            operation, target, value = "select_source", source[1], source[2]
        if not target:
            return None
        candidates = [key for key, e in entities.items()
                      if normalize(target) in {normalize(a) for a in e.aliases}]
        if len(candidates) != 1:
            return None
        actions.append(Action(target=candidates[0], operation=operation, value=value))
    return actions or None


def voice_text(job):
    if not job:
        return "Todavía no tienes trabajos en este dispositivo."
    if job["status"] == "succeeded":
        result = job["result"]
        text = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", result["text"])
        text = re.sub(r"https?://\S+", "", text)
        if result.get("sources"):
            text = text[:1350] + f". El informe incluye {len(result['sources'])} fuentes para consultar."
        return text[:1600]
    if job["status"] in {"queued", "running"}:
        return "Tu trabajo sigue en proceso. Di: consulta mi resultado, dentro de unos segundos."
    return job.get("error") or "El trabajo no terminó. Revisa su estado en MAX."


class Runtime:
    def __init__(self, settings: Settings, engine=None, client=None):
        self.settings = settings
        self.store = Store(settings.db_path)
        self.client = client or httpx.AsyncClient(trust_env=False, follow_redirects=False)
        self.home = Home(settings, self.store, self.client)
        self.research = Research(settings.searxng_url, self.client)
        self.engine = engine or Engine(settings)
        self.workers = []
        self.running = {}
        self.last_engine_receipt = None
        self._state_lock = None

    def identity(self, raw):
        return hmac.new(self.settings.identity_salt.encode(),
                        (self.settings.household + ":" + raw).encode(), hashlib.sha256).hexdigest()

    @property
    def owner(self):
        return self.identity("alexa:" + self.settings.owner_alexa_user
                             if self.settings.owner_alexa_user else "local-owner")

    def submit(self, principal, session, device, request_id, text):
        return self.store.create(principal, session, device, request_id, text,
                                 self.settings.max_pending)[0]

    async def start(self):
        import fcntl
        if self._state_lock is not None:
            raise RuntimeError("El runtime ya está iniciado")
        fd = os.open(self.settings.state_dir / "runtime.lock", os.O_CREAT | os.O_RDWR, 0o600)
        state_lock = os.fdopen(fd, "a+")
        try:
            fcntl.flock(state_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            state_lock.close()
            raise RuntimeError("Ya hay otro runtime MAX usando este estado") from None
        self._state_lock = state_lock
        self.store.recover()
        self.store.prune(self.settings.retention_days)
        self.workers = [asyncio.create_task(self.worker(), name=f"max-worker-{i}")
                        for i in range(self.settings.worker_count)]

    async def close(self):
        for worker in self.workers:
            worker.cancel()
        for task in list(self.running.values()):
            task.cancel()
        await asyncio.gather(*self.workers, *list(self.running.values()), return_exceptions=True)
        await self.client.aclose()
        if self._state_lock:
            self._state_lock.close()
            self._state_lock = None

    def cancel(self, job_id, principal):
        changed = self.store.cancel(job_id, principal)
        if changed and job_id in self.running:
            self.running[job_id].cancel()
        return changed

    async def worker(self):
        while True:
            job = self.store.claim()
            if not job:
                await asyncio.sleep(0.15)
                continue
            task = asyncio.create_task(self.process(job))
            self.running[job["id"]] = task
            try:
                await task
            except asyncio.CancelledError:
                if asyncio.current_task().cancelling():
                    raise
            finally:
                self.running.pop(job["id"], None)

    async def process(self, job):
        try:
            async with asyncio.timeout(self.settings.engine_timeout + 60):
                result = await self.answer(job)
            self.store.finish(job["id"], "succeeded", result=result)
        except asyncio.CancelledError:
            self.store.finish(job["id"], "interrupted", error="Trabajo detenido; revisa las acciones enviadas.")
            raise
        except Exception as exc:
            # No se almacenan claves, prompts ni trazas de proveedores en la respuesta pública.
            log.warning("job_failed id=%s class=%s", job["id"], type(exc).__name__)
            safe = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else (
                "No pude completar la conexión con una herramienta. Revisa el diagnóstico de MAX.")
            if self.store.evidence(job["id"]):
                safe = "La solicitud terminó incompleta. Algunas órdenes ya fueron enviadas. " + safe
            self.store.finish(job["id"], "failed", error=safe[:400])

    async def answer(self, job):
        text = job["text"].strip()
        simple = normalize(text)
        label = re.match(r"^identifica este dispositivo como\s+(.+)$", text, flags=re.IGNORECASE)
        if label:
            name = " ".join(label[1].split())[:100]
            self.store.label_device(job["principal"], job["device"], name)
            return {"text": f"Registré este dispositivo como {name}. El nombre fue indicado por ti.",
                    "device": job["device"], "name": name, "evidence": "user_provided_label"}
        if simple.startswith("recuerda que "):
            key = self.store.note(job["principal"], text[len("recuerda que "):][:2000])
            return {"text": "He guardado tu nota.", "note_id": key}
        if simple in {"que recuerdas", "mis notas", "que has guardado"}:
            notes = self.store.notes(job["principal"])
            return {"text": "\n".join(f"{i+1}: {n['text']}" for i, n in enumerate(notes))
                    or "No tienes notas.", "notes": notes}
        if simple == "olvida mi ultima nota":
            notes = self.store.notes(job["principal"])
            if notes:
                self.store.forget(job["principal"], notes[-1]["id"])
            return {"text": "He eliminado tu última nota." if notes else "No tienes notas guardadas."}
        forget = re.fullmatch(r"olvida (?:la )?nota ([a-f0-9]{16})", simple)
        if forget:
            deleted = self.store.forget(job["principal"], forget[1])
            return {"text": "Nota eliminada." if deleted else "No encontré esa nota en tu perfil."}
        if simple in {"estado del hogar", "estado de mis dispositivos"}:
            states = await self.home.states()
            return {"text": "; ".join(f"{s['attributes'].get('friendly_name', s['entity_id'])}: "
                                      f"{s['state']}" for s in states) or "No hay dispositivos autorizados.",
                    "states": states}
        actions = direct_actions(text, self.settings.entities)
        if actions:
            # Valida permisos y volumen del lote antes de enviar la primera acción.
            for action in actions:
                e = self.settings.entities[action.target]
                if action.operation not in e.actions:
                    raise ValueError("Una acción del lote no está autorizada")
                if action.operation == "volume_set" and not 0 <= action.value <= 0.6:
                    raise ValueError("El volumen permitido es de 0 a 60 por ciento")
            evidence = []
            for i, action in enumerate(actions):
                current = self.store.get(job["id"], job["principal"])
                if current["status"] == "canceled":
                    raise asyncio.CancelledError
                evidence.append(await self.home.execute(job["id"], i, action))
            confirmed = all(e["verified"] for e in evidence)
            return {"text": ("Listo. Comprobé el estado de los dispositivos." if confirmed else
                             "Envié la orden, pero no pude confirmar todos los estados. Revisa el resultado."),
                    "actions": evidence, "verified": confirmed}
        sources = []
        if re.search(r"\b(busca|investiga|internet|noticias|actualidad|hoy|actuales)\b", simple):
            sources = await self.research.search(text)
        capabilities = {key: {"names": e.aliases, "actions": e.actions}
                        for key, e in self.settings.entities.items()}
        history = self.store.history(job["principal"], job["session"], job["created"])
        proposal, receipt = await self.engine.complete(
            job, history, [n["text"] for n in self.store.notes(job["principal"])][-10:], sources, capabilities)
        plan = Plan.model_validate(proposal)
        if plan.actions:
            return {"text": "Necesito una orden concreta para controlar el hogar. Por ejemplo: "
                            "enciende la TV de la sala. No he enviado acciones."}
        self.last_engine_receipt = receipt
        result = {"text": plan.text, "sources": sources, "engine": receipt}
        if sources:
            artifact = self.settings.state_dir / "reports" / (job["id"] + ".md")
            artifact.parent.mkdir(exist_ok=True, mode=0o700)
            artifact.write_text("# Informe MAX\n\n" + plan.text + "\n\n" + "\n".join(
                f"- [{s['title']}]({s['url']})" for s in sources), encoding="utf-8")
            artifact.chmod(0o600)
            result["report"] = job["id"] + ".md"
        return result
