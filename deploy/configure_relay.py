#!/usr/bin/env python3
"""Prepara la identidad privada del conector; nunca muestra su token."""
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
import subprocess
from pathlib import Path

from max_runtime.relay import RelaySettings, load_settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_url", help="https://NOMBRE.CUENTA.workers.dev")
    args = parser.parse_args()
    home = Path.home()
    repo = Path(__file__).resolve().parents[1]
    if repo != home / "projects/LUTS-IA":
        parser.exit(1, "Utiliza el clon original en ~/projects/LUTS-IA\n")
    directory = home / ".config/max"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    bootstrap = directory / "cloudflared-bootstrap.yml"
    if not bootstrap.exists():
        bootstrap.touch(mode=0o600)
        bootstrap.write_text("{}\n")
    if bootstrap.read_text().strip() != "{}":
        parser.exit(1, "El bootstrap existente no está vacío; no se modificó\n")
    target = directory / "relay.json"
    if target.exists():
        settings = load_settings(target)
        if settings.public_url != args.public_url.rstrip("/"):
            parser.exit(1, "Ya existe una identidad para otro hostname; no se reemplazó\n")
    else:
        settings = RelaySettings(public_url=args.public_url, register_token=secrets.token_urlsafe(48))
        target.touch(mode=0o600)
        target.write_text(json.dumps(settings.model_dump(mode="json"), indent=2) + "\n")
    unit_dir = home / ".config/systemd/user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    for name in ["max-edge.service", "max-relay.service"]:
        shutil.copy2(repo / "deploy" / name, unit_dir / name)
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    print("Configura este verificador como REGISTER_TOKEN_SHA256 en el Worker:")
    print(hashlib.sha256(settings.register_token.encode()).hexdigest())
    print("Después de vincular MAX_RELAY, habilita max-relay.service según la guía.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError):
        raise SystemExit("No se pudo preparar el conector; revisa URL, archivos y permisos privados") from None
