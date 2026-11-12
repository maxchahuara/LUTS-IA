// MAX HTTPS relay. MIT; see max_runtime/LICENSE.
const VOICE_PATHS = new Set(["/alexa", "/v1/voice"]);
const MAX_BODY = 65536;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store",
      "x-content-type-options": "nosniff" },
  });
}

function unavailable() {
  return json({ service: "MAX", status: "starting" }, 503);
}

async function digest(text) {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(hash)].map(x => x.toString(16).padStart(2, "0")).join("");
}

async function authorized(request, env) {
  const expected = env.REGISTER_TOKEN_SHA256 || "";
  const header = request.headers.get("authorization") || "";
  if (!/^[a-f0-9]{64}$/.test(expected) || !/^Bearer [A-Za-z0-9_-]{32,128}$/.test(header)) return false;
  const actual = await digest(header.slice(7));
  let difference = 0;
  for (let i = 0; i < expected.length; i++) difference |= expected.charCodeAt(i) ^ actual.charCodeAt(i);
  return difference === 0;
}

function originUrl(value) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || !/^[a-z0-9-]+\.trycloudflare\.com$/.test(url.hostname)
        || url.username || url.password || url.port || url.pathname !== "/" || url.search || url.hash) return null;
    return url.origin;
  } catch { return null; }
}

async function limitedBody(request, limit) {
  const length = Number(request.headers.get("content-length"));
  if (length > limit) return null;
  if (!request.body) return new Uint8Array();
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > limit) { await reader.cancel(); return null; }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return bytes;
}

async function originHealth(origin) {
  const response = await fetch(origin + "/health", {
    redirect: "manual", signal: AbortSignal.timeout(4500),
  });
  if (response.status !== 200) return null;
  const data = await response.json();
  if (data?.service !== "MAX" || data?.status !== "ok") return null;
  return { service: "MAX", status: "ok", version: data.version };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === "/internal/relay" && request.method === "PUT") {
        if (!await authorized(request, env)) return json({ detail: "Not Found" }, 404);
        if (!env.MAX_RELAY) return unavailable();
        const body = await limitedBody(request, 2048);
        if (!body) return json({ detail: "Request too large" }, 413);
        let data;
        try { data = JSON.parse(new TextDecoder().decode(body)); }
        catch { return json({ detail: "Invalid JSON" }, 400); }
        const origin = originUrl(data?.origin);
        if (!origin) return json({ detail: "Invalid origin" }, 400);
        if (!await originHealth(origin)) return unavailable();
        const previous = await env.MAX_RELAY.get("origin", { type: "json", cacheTtl: 30 });
        if (previous?.origin !== origin) {
          await env.MAX_RELAY.put("origin", JSON.stringify({ origin, updated_at: new Date().toISOString() }));
        }
        return json({ status: "registered", origin_hash: await digest(origin) });
      }

      if (url.pathname === "/" && request.method === "GET") {
        return new Response(null, { status: 307, headers: { location: "/health", "cache-control": "no-store" } });
      }
      const health = url.pathname === "/health" && ["GET", "HEAD"].includes(request.method);
      const voice = VOICE_PATHS.has(url.pathname) && request.method === "POST";
      if (!health && !voice) return json({ detail: "Not Found" }, 404);
      if (url.pathname === "/alexa" && voice && !(
        (request.headers.get("signature-256") || request.headers.get("signature"))
        && request.headers.get("signaturecertchainurl"))) return json({ detail: "Falta firma Alexa" }, 400);
      if (!env.MAX_RELAY) return unavailable();
      const registered = await env.MAX_RELAY.get("origin", { type: "json", cacheTtl: 30 });
      const origin = originUrl(registered?.origin);
      if (!origin) return unavailable();
      if (health) {
        const data = await originHealth(origin);
        if (!data) return unavailable();
        const response = json(data);
        return request.method === "HEAD" ? new Response(null, response) : response;
      }
      const body = await limitedBody(request, MAX_BODY);
      if (!body) return json({ detail: "Request too large" }, 413);
      const headers = new Headers();
      for (const key of ["content-type", "signature", "signature-256", "signaturecertchainurl", "authorization"]) {
        if (request.headers.has(key)) headers.set(key, request.headers.get(key));
      }
      const response = await fetch(origin + url.pathname, { method: "POST", headers, body,
        redirect: "manual", signal: AbortSignal.timeout(4500) });
      if (response.status >= 300 && response.status < 400) return unavailable();
      return new Response(response.body, { status: response.status, headers: {
        "content-type": "application/json", "cache-control": "no-store", "x-content-type-options": "nosniff",
      } });
    } catch {
      return unavailable();
    }
  },
};
