"""Espera el arranque del gateway antes de aceptar trabajos de MAX."""
from __future__ import annotations

import argparse
import time

import httpx


def wait_for_gateway(client: httpx.Client, *, timeout=180, interval=1):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            response = client.get("/startupz", timeout=2)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("ok") is True and data.get("status") == "started":
                return
        except (httpx.HTTPError, ValueError):
            pass
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(interval, remaining))
    raise TimeoutError("El gateway de OpenClaw todavía no completó su arranque")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway-url", default="http://127.0.0.1:18789")
    args = parser.parse_args()
    print("MAX espera a que OpenClaw complete su arranque", flush=True)
    with httpx.Client(base_url=args.gateway_url, trust_env=False, follow_redirects=False) as client:
        try:
            wait_for_gateway(client)
        except TimeoutError as error:
            parser.exit(1, str(error) + "\n")
    print("Gateway iniciado; MAX puede arrancar", flush=True)


if __name__ == "__main__":
    main()
