"""Inventario de solo lectura por SSDP y mDNS. No inscribe ni controla dispositivos."""
from __future__ import annotations

import ipaddress
import socket
import threading
import time
from urllib.parse import urlsplit
from xml.etree import ElementTree

import httpx
from zeroconf import IPVersion, ServiceBrowser, ServiceListener, Zeroconf

SERVICES = ["_spotify-connect._tcp.local.", "_amzn-wplay._tcp.local.",
            "_amazon-alexa._tcp.local.", "_googlecast._tcp.local.",
            "_airplay._tcp.local.", "_adb._tcp.local."]


def discover(seconds=4):
    records, lock = [], threading.Lock()

    class Listener(ServiceListener):
        def add_service(self, zc, kind, name):
            info = zc.get_service_info(kind, name, timeout=1200)
            if not info:
                return
            props = {k.decode(errors="replace"): v.decode(errors="replace")
                     for k, v in info.properties.items() if isinstance(v, bytes)
                     and k.decode(errors="replace").lower() in {
                         "model", "md", "fn", "brand", "manufacturer", "name", "modelname"}}
            with lock:
                records.append({"source": "mdns", "service": kind, "name": name,
                                "host": info.server, "addresses": info.parsed_addresses(),
                                "port": info.port, "metadata": props})

        def update_service(self, zc, kind, name):
            self.add_service(zc, kind, name)

        def remove_service(self, zc, kind, name):
            pass

    zc = Zeroconf(ip_version=IPVersion.V4Only)
    browser = ServiceBrowser(zc, SERVICES, listener=Listener())
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.3)
    message = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
               "MAN: \"ssdp:discover\"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n").encode()
    deadline, locations = time.monotonic() + seconds, set()
    try:
        sock.sendto(message, ("239.255.255.250", 1900))
        while time.monotonic() < deadline:
            try:
                packet, sender = sock.recvfrom(8192)
            except socket.timeout:
                continue
            for line in packet.decode(errors="replace").splitlines():
                if line.lower().startswith("location:"):
                    url = line.split(":", 1)[1].strip()
                    parsed = urlsplit(url)
                    if (parsed.hostname == sender[0] and ipaddress.ip_address(sender[0]).is_private
                            and parsed.scheme in {"http", "https"}
                            and not parsed.username and not parsed.password):
                        locations.add((sender[0], url))
    finally:
        sock.close()
        browser.cancel()
        zc.close()
    with httpx.Client(timeout=1, trust_env=False, follow_redirects=False) as client:
        for address, url in sorted(locations)[:12]:
            try:
                with client.stream("GET", url) as r:
                    r.raise_for_status()
                    data = bytearray()
                    for chunk in r.iter_bytes(chunk_size=8192):
                        data.extend(chunk)
                        if len(data) > 65536:
                            raise ValueError("Descripción demasiado grande")
                root = ElementTree.fromstring(data)
                record = {"source": "ssdp", "addresses": [address]}
                for key in ["friendlyName", "manufacturer", "modelName"]:
                    element = root.find(".//{*}" + key)
                    if element is not None and element.text:
                        record[key] = element.text[:200]
                records.append(record)
            except (httpx.HTTPError, ValueError, ElementTree.ParseError):
                continue
    return records
