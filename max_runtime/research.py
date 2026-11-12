from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx
import trafilatura


async def public_address(host):
    records = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
    addresses = list(dict.fromkeys(r[4][0] for r in records))
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise ValueError("Solo se pueden leer sitios públicos de Internet")
    return addresses[0]


async def read_page(client: httpx.AsyncClient, url: str):
    """Fija DNS por petición y revalida cada redirección; no acepta redes locales."""
    for _ in range(4):
        parsed = urlsplit(url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.port not in {None, 80, 443}):
            raise ValueError("URL pública inválida")
        address = await public_address(parsed.hostname)
        target = httpx.URL(url).copy_with(host=address)
        headers = {"Host": parsed.netloc, "User-Agent": "MAX/0.1 (public research)"}
        # httpcore conserva SNI/certificado del sitio original al fijar la IP.
        async with client.stream("GET", target, headers=headers, timeout=8,
                                 extensions={"sni_hostname": parsed.hostname},
                                 follow_redirects=False) as r:
            if r.is_redirect:
                url = urljoin(url, r.headers.get("location", ""))
                continue
            r.raise_for_status()
            content_type = r.headers.get("content-type", "").lower()
            if not any(t in content_type for t in ["text/html", "text/plain", "application/xhtml"]):
                raise ValueError("Solo se admiten páginas de texto")
            raw = bytearray()
            async for chunk in r.aiter_bytes():
                raw.extend(chunk)
                if len(raw) > 1_000_000:
                    raise ValueError("Página demasiado grande")
        text = await asyncio.to_thread(trafilatura.extract, bytes(raw), include_tables=False)
        return {"url": url, "text": (text or "")[:12000]}
    raise ValueError("Demasiadas redirecciones")


class Research:
    def __init__(self, base_url, client):
        self.base_url, self.client = base_url, client

    async def search(self, query):
        r = await self.client.get(self.base_url.rstrip("/") + "/search", params={
            "q": query[:500], "format": "json", "language": "es", "safesearch": 1,
        }, timeout=20)
        r.raise_for_status()
        candidates = r.json().get("results", [])[:5]
        sources = []
        for entry in candidates:
            url = entry.get("url", "")
            parsed = urlsplit(url)
            if parsed.scheme not in {"https", "http"} or not parsed.hostname:
                continue
            source = {"url": url, "title": entry.get("title", "")[:300],
                      "snippet": entry.get("content", "")[:2500], "page_read": False}
            if len(sources) < 2:
                try:
                    page = await read_page(self.client, url)
                    source.update(page)
                    source["page_read"] = bool(page["text"])
                except (httpx.HTTPError, ValueError, OSError):
                    pass
            sources.append(source)
        if not sources:
            raise RuntimeError("La búsqueda no devolvió fuentes; no inventaré una respuesta actual")
        return sources
