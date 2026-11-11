from __future__ import annotations

from html import escape

from .runtime import Runtime, normalize, voice_text


class AlexaDenied(ValueError):
    pass


def response(text, end=False, attributes=None):
    # El modelo nunca genera SSML ejecutable.
    text = "".join(c for c in str(text) if ord(c) >= 32 or c in "\n\r\t")
    text = " ".join(text.split())[:1600]
    result = {"version": "1.0", "sessionAttributes": attributes or {}, "response": {
        "outputSpeech": {"type": "SSML", "ssml": "<speak>" + escape(text) + "</speak>"},
        "shouldEndSession": end,
    }}
    if not end:
        result["response"]["directives"] = [{"type": "Dialog.ElicitSlot", "slotToElicit": "query",
            "updatedIntent": {"name": "GptQueryIntent", "confirmationStatus": "NONE",
                "slots": {"query": {"name": "query", "confirmationStatus": "NONE"}}}}]
        result["response"]["reprompt"] = {"outputSpeech": {"type": "PlainText", "text":
            "Di: consulta mi resultado; o consulta, seguido de tu pregunta."}}
    return result


def handle(envelope, runtime: Runtime):
    cfg = runtime.settings
    context = envelope.get("context", {}).get("System", {})
    session = envelope.get("session", {})
    app = context.get("application", session.get("application", {})).get("applicationId")
    user = context.get("user", session.get("user", {})).get("userId")
    if not cfg.alexa_skill_id or not cfg.alexa_users:
        raise AlexaDenied("Completa la vinculación de la skill y de los usuarios autorizados")
    if app != cfg.alexa_skill_id or user not in cfg.alexa_users:
        raise AlexaDenied("Skill o usuario no autorizado")
    device = context.get("device", {}).get("deviceId")
    request = envelope.get("request", {})
    if not device or not request.get("requestId"):
        raise AlexaDenied("Falta la identidad del dispositivo o de la petición")
    principal = runtime.identity("alexa:" + user)
    device_key = runtime.identity(user + ":" + device)
    session_key = runtime.identity(user + ":" + session.get("sessionId", request["requestId"]))
    intent = request.get("intent", {}).get("name", "")
    if request.get("type") == "LaunchRequest":
        return response("MAX listo. Di consulta, seguido de tu pregunta. Para el hogar, "
                        "di por ejemplo: enciende la TV de la sala.")
    if request.get("type") == "SessionEndedRequest":
        return {"version": "1.0", "response": {}}
    if intent in {"AMAZON.StopIntent", "AMAZON.NavigateHomeIntent"}:
        return response("Hasta luego. Tus trabajos siguen disponibles en MAX.", end=True)
    if intent in {"AMAZON.CancelIntent", "CancelJobIntent"}:
        job = runtime.store.latest(principal, device_key)
        changed = job and runtime.cancel(job["id"], principal)
        return response("Trabajo cancelado. Las acciones ya enviadas pueden haberse ejecutado."
                        if changed else "No hay un trabajo pendiente para cancelar.")
    if intent == "ResultIntent":
        return response(voice_text(runtime.store.latest(principal, device_key)))
    if intent in {"AMAZON.HelpIntent", "AMAZON.FallbackIntent"}:
        return response("Puedo investigar en Internet, conversar y controlar dispositivos "
                        "autorizados. Di consulta y tu pregunta; o consulta mi resultado.")
    slots = request.get("intent", {}).get("slots", {})
    query = slots.get("query", {}).get("value", "")
    if intent == "SearchIntent" and query:
        query = "busca en internet " + query
    command = slots.get("target", {}).get("value", "")
    if intent in {"TurnOnIntent", "TurnOffIntent"} and command:
        query = ("enciende " if intent == "TurnOnIntent" else "apaga ") + command
    if not query:
        return response("Di consulta, seguido de lo que necesitas.")
    query = query.strip()[:4000]
    if normalize(query) in {"consulta mi resultado", "lee mi resultado", "mi resultado", "como va mi trabajo"}:
        return response(voice_text(runtime.store.latest(principal, device_key)))
    if normalize(query) in {"cancela mi trabajo", "cancela la tarea"}:
        job = runtime.store.latest(principal, device_key)
        changed = job and runtime.cancel(job["id"], principal)
        return response("Trabajo cancelado. Las acciones ya enviadas pueden haberse ejecutado."
                        if changed else "No hay un trabajo pendiente para cancelar.")
    job = runtime.submit(principal, session_key, device_key, request["requestId"], query)
    return response(voice_text(job) if job["status"] == "succeeded" else
                    "Ya recibí tu solicitud. Di consulta mi resultado dentro de unos segundos.",
                    attributes={"jobId": job["id"]})
