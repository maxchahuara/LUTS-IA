#!/usr/bin/env python3
"""Instalación de usuario en Linux; no modifica servicios ajenos ni requiere sudo."""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

home = pathlib.Path.home()
repo = pathlib.Path(__file__).resolve().parents[1]
venv = home / ".local/share/max/venv"
if sys.version_info < (3, 12):
    raise SystemExit("Se requiere Python 3.12 o posterior")
if repo != home / "projects/LUTS-IA":
    raise SystemExit("Clona el repositorio original en ~/projects/LUTS-IA para usar esta unidad")
subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
subprocess.run([str(venv / "bin/pip"), "install", "pip==26.3"], check=True)
lock = repo / "requirements.lock"
if lock.exists():
    subprocess.run([str(venv / "bin/pip"), "install", "-r", str(lock)], check=True)
subprocess.run([str(venv / "bin/pip"), "install", "--no-deps", "-e", str(repo)], check=True)
subprocess.run([str(venv / "bin/max-cli"), "init"], check=True)
unit_dir = home / ".config/systemd/user"
unit_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(repo / "deploy/max.service", unit_dir / "max.service")
subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
subprocess.run(["systemctl", "--user", "enable", "--now", "max.service"], check=True)
for attempt in range(30):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=1) as response:
            if response.status == 200:
                break
    except urllib.error.URLError:
        time.sleep(0.2)
else:
    raise SystemExit("El servicio no respondió. Comprueba journalctl --user -u max.service")
print("MAX instalado. Comprueba: ~/.local/share/max/venv/bin/max-cli status")
