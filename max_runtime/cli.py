from __future__ import annotations

import argparse
import json
import secrets
import sys
import tarfile
import time
import uuid
from datetime import datetime
from pathlib import Path

import httpx

from .config import Settings
from .store import Store


def _run():
    parser = argparse.ArgumentParser(description="MAX: administración local sin mostrar secretos")
    parser.add_argument("--url", default="http://127.0.0.1:8787")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["init", "status", "jobs", "devices", "echoes", "discover", "link-ha", "backup"]:
        sub.add_parser(command)
    ask = sub.add_parser("ask")
    ask.add_argument("text")
    ask.add_argument("--session", default="terminal")
    ask.add_argument("--wait", action="store_true")
    for command in ["result", "cancel"]:
        p = sub.add_parser(command)
        p.add_argument("id")
    args = parser.parse_args()
    if args.command == "discover":
        from .discovery import discover
        print(json.dumps(discover(), ensure_ascii=False, indent=2))
        return
    if args.command == "init":
        target = Path.home() / ".config/max/config.json"
        if target.exists():
            parser.exit(0, "La configuración ya existe; no se reemplazó.\n")
        cfg = Settings(api_token=secrets.token_urlsafe(48), identity_salt=secrets.token_hex(32),
                       bridge_token=secrets.token_urlsafe(48))
        cfg.save()
        print("Configuración privada creada en ~/.config/max/config.json")
        return
    cfg = Settings.load()
    if args.command == "backup":
        directory = cfg.state_dir / "backups"
        directory.mkdir(exist_ok=True, mode=0o700)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        database = directory / (stamp + ".sqlite3")
        Store(cfg.db_path).backup(database)
        target = directory / ("max-" + stamp + ".tar.gz")
        import os
        config = Path(os.environ.get("MAX_CONFIG", Path.home() / ".config/max/config.json"))
        with tarfile.open(target, "w:gz") as archive:
            archive.add(database, arcname="max.sqlite3")
            archive.add(config, arcname="config.json")
            reports = cfg.state_dir / "reports"
            if reports.exists():
                archive.add(reports, arcname="reports")
        target.chmod(0o600)
        print(target)
        return
    with httpx.Client(base_url=args.url, headers={"Authorization": "Bearer " + cfg.api_token},
                      timeout=10, trust_env=False) as client:
        paths = {"status": "/v1/status", "jobs": "/v1/jobs", "devices": "/v1/devices",
                 "echoes": "/v1/alexa/devices"}
        if args.command in paths:
            r = client.get(paths[args.command])
        elif args.command == "link-ha":
            r = client.post("/v1/setup/home-assistant")
        elif args.command == "ask":
            r = client.post("/v1/requests", json={"text": args.text,
                            "request_id": str(uuid.uuid4()), "session": args.session})
            r.raise_for_status()
            if args.wait:
                job = r.json()
                deadline = time.monotonic() + cfg.engine_timeout + 75
                while job["status"] in {"queued", "running"} and time.monotonic() < deadline:
                    time.sleep(0.5)
                    r = client.get("/v1/jobs/" + job["id"])
                    r.raise_for_status()
                    job = r.json()
        elif args.command == "cancel":
            r = client.post("/v1/jobs/" + args.id + "/cancel")
        else:
            r = client.get("/v1/jobs/" + args.id)
        r.raise_for_status()
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
        if args.command == "ask" and args.wait and r.json().get("status") != "succeeded":
            raise SystemExit(1)


def main():
    try:
        _run()
    except httpx.ConnectError:
        print("MAX no está disponible. Comprueba: systemctl --user status max.service", file=sys.stderr)
        raise SystemExit(1) from None
    except httpx.HTTPError:
        print("No se pudo completar la solicitud a MAX. Comprueba la conexión y la configuración.",
              file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
