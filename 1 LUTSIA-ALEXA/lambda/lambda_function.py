"""Puente Alexa -> MAX. Configurar trigger Alexa Skills Kit restringido al Skill ID.

El modelo, la memoria y las acciones viven en la laptop Linux. No necesita API key
de OpenAI. Este archivo se puede desplegar solo en AWS Lambda con Python 3.12+.
SPDX-License-Identifier: MIT
"""
import json
import os
from datetime import datetime, timezone
from html import escape
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def say(text):
    return {"version": "1.0", "response": {
        "outputSpeech": {"type": "SSML", "ssml": "<speak>" + escape(text) + "</speak>"},
        "shouldEndSession": False,
        "reprompt": {"outputSpeech": {"type": "PlainText", "text": "Inténtalo de nuevo en unos segundos."}},
    }}


def lambda_handler(event, context):
    skill = os.environ.get("ALEXA_SKILL_ID", "")
    app = event.get("context", {}).get("System", {}).get("application", {}).get("applicationId")
    if not skill or app != skill:
        raise ValueError("Skill no autorizado")
    stamp = event.get("request", {}).get("timestamp", "")
    try:
        age = abs((datetime.now(timezone.utc) - datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds())
    except (ValueError, TypeError):
        raise ValueError("Timestamp inválido") from None
    if age > 150:
        raise ValueError("Petición expirada")
    base = os.environ.get("MAX_BASE_URL", "").rstrip("/")
    token = os.environ.get("MAX_BRIDGE_TOKEN", "")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or not token:
        return say("Falta configurar la conexión segura con MAX.")
    req = Request(base + "/v1/voice", data=json.dumps(event).encode(), headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json",
    }, method="POST")
    try:
        # Solo se espera el acuse de recibo; Codex trabaja fuera del plazo de Alexa.
        with build_opener(NoRedirect()).open(req, timeout=3.0) as result:
            return json.load(result)
    except (HTTPError, URLError, TimeoutError, OSError):
        return say("No logré comunicarme con MAX. Revisa que la laptop esté conectada.")
