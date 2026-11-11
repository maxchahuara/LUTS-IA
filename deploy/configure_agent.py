#!/usr/bin/env python3
"""Configura exclusivamente el agente MAX; conserva el resto de OpenClaw."""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", default="max")
    parser.add_argument("--model", default="openai/gpt-6.1-sol")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_-]+", args.agent):
        parser.error("ID de agente inválido")
    home = pathlib.Path.home()
    config = pathlib.Path(os.environ.get("OPENCLAW_CONFIG_PATH", home / ".openclaw/openclaw.json"))
    command = shutil.which("openclaw") or str(home / ".npm-global/bin/openclaw")
    original = config.read_bytes()
    data = json.loads(original)
    workspace = home / ".local/share/max/agent-workspace"
    existing = data.get("agents", {}).get("entries", {}).get(args.agent)
    if existing and pathlib.Path(existing.get("workspace", "")).expanduser().resolve() != workspace:
        parser.error("Ese agente ya usa otro workspace; elige otro ID para conservarlo")
    state = home / ".local/share/max"
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    state.chmod(0o700)
    backups = state / "backups"
    backups.mkdir(exist_ok=True, mode=0o700)
    stamp = str(time.time_ns())
    backup = backups / ("openclaw-before-max-" + stamp + ".json")
    backup.write_bytes(original)
    backup.chmod(0o600)
    if not existing:
        subprocess.run([command, "agents", "add", args.agent, "--workspace", str(workspace),
                        "--model", args.model, "--non-interactive", "--json"],
                       check=True, capture_output=True)
        data = json.loads(config.read_text())
    entry = data["agents"]["entries"][args.agent]
    entry.update({"model": args.model, "thinkingDefault": "low", "skills": [],
                  "tools": {"allow": ["session_status"]}})
    config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    config.chmod(0o600)
    result = subprocess.run([command, "config", "validate"], capture_output=True, text=True)
    if result.returncode:
        config.write_bytes(original)
        raise SystemExit("OpenClaw rechazó el cambio; se restauró la configuración anterior")
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    instructions = workspace / "AGENTS.md"
    if instructions.exists():
        target = backups / ("max-instructions-" + stamp + ".md")
        shutil.copy2(instructions, target)
        target.chmod(0o600)
    shutil.copy2(pathlib.Path(__file__).with_name("max-agent.md"), instructions)
    if not existing:
        (workspace / "BOOTSTRAP.md").write_text("MAX ya está configurado. Atiende la solicitud de la pasarela.\n")
    print(json.dumps({"agent": args.agent, "model": args.model,
                      "tools_allow": ["session_status"], "personal_agents_preserved": True}))


if __name__ == "__main__":
    main()
