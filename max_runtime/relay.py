"""Conector saliente para conservar el hostname Workers HTTPS después de reiniciar."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RelaySettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_url: str
    register_token: str = Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$", repr=False)
    cloudflared: Path = Path.home() / ".local/bin/cloudflared"
    bootstrap_config: Path = Path.home() / ".config/max/cloudflared-bootstrap.yml"

    @field_validator("public_url")
    @classmethod
    def validate_public_url(cls, value):
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not re.fullmatch(
                r"[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev", parsed.hostname or "")
                or parsed.username or parsed.password or parsed.port
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            raise ValueError("Se requiere el hostname HTTPS workers.dev de MAX")
        return value.rstrip("/")


def quick_origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not re.fullmatch(
            r"[a-z0-9-]+\.trycloudflare\.com", parsed.hostname or "")
            or parsed.username or parsed.password or parsed.port
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
        raise ValueError("Origen del conector no válido")
    return value.rstrip("/")


def load_settings(path):
    if path.stat().st_mode & 0o077:
        raise ValueError("relay.json debe tener permisos 0600")
    settings = RelaySettings.model_validate(json.loads(path.read_text()))
    if settings.bootstrap_config.read_text().strip() != "{}":
        raise ValueError("El conector requiere una configuración de bootstrap vacía")
    return settings


async def register_origin(settings, client, value):
    origin = quick_origin(value)
    response = await client.get(origin + "/health")
    response.raise_for_status()
    health = response.json()
    if not isinstance(health, dict) or health.get("service") != "MAX" or health.get("status") != "ok":
        raise ValueError("El runtime todavía no está disponible")
    response = await client.put(settings.public_url + "/internal/relay", json={"origin": origin},
                                headers={"Authorization": "Bearer " + settings.register_token})
    response.raise_for_status()
    receipt = response.json()
    expected = hashlib.sha256(origin.encode()).hexdigest()
    if (not isinstance(receipt, dict) or receipt.get("status") != "registered"
            or receipt.get("origin_hash") != expected):
        raise ValueError("El receptor no confirmó el destino esperado")


async def publish(settings, client, origin):
    while True:
        try:
            await register_origin(settings, client, origin)
            print("MAX HTTPS conectado: " + settings.public_url, flush=True)
            return
        except (httpx.HTTPError, ValueError):
            print("MAX espera al enlace HTTPS; volverá a registrar el destino", flush=True)
            await asyncio.sleep(10)


async def supervise(settings):
    environment = {k: v for k, v in os.environ.items() if k not in {
        "TUNNEL_TOKEN", "TUNNEL_TOKEN_FILE", "TUNNEL_CRED_FILE", "TUNNEL_ORIGIN_CERT"}}
    proc = await asyncio.create_subprocess_exec(
        str(settings.cloudflared), "tunnel", "--config", str(settings.bootstrap_config),
        "--no-autoupdate", "--url", "http://127.0.0.1:8788",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env=environment,
    )
    publisher = None
    current = None
    async with httpx.AsyncClient(timeout=8, trust_env=False, follow_redirects=False) as client:
        try:
            while line := await proc.stdout.readline():
                found = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line.decode(errors="replace"))
                if found and found[0] != current:
                    current = found[0]
                    if publisher:
                        publisher.cancel()
                        with suppress(asyncio.CancelledError):
                            await publisher
                    publisher = asyncio.create_task(publish(settings, client, current))
                    print("Conector saliente creado; registrando su destino", flush=True)
            code = await proc.wait()
        finally:
            if publisher:
                publisher.cancel()
                with suppress(asyncio.CancelledError):
                    await publisher
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), 5)
                except TimeoutError:
                    proc.kill()
                    await proc.wait()
    raise RuntimeError(f"El conector terminó con código {code}; systemd debe reiniciarlo")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/max/relay.json")
    args = parser.parse_args()
    try:
        settings = load_settings(args.config)
        asyncio.run(supervise(settings))
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError, RuntimeError) as error:
        # No se muestran configuraciones ni cuerpos de respuesta con posibles secretos.
        parser.exit(1, "No se pudo mantener el conector MAX: " + type(error).__name__ + "\n")


if __name__ == "__main__":
    main()
