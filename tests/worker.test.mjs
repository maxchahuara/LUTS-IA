import assert from "node:assert/strict";
import { test } from "node:test";
import worker from "../deploy/cloudflare/worker.mjs";

const base = "https://max.example.workers.dev";
const origin = "https://max-test.trycloudflare.com";
const token = "max-test-register-token-".repeat(3);
async function hash(text) {
  return Buffer.from(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text))).toString("hex");
}
async function environment(initial) {
  let value = initial;
  let writes = 0;
  return { REGISTER_TOKEN_SHA256: await hash(token), MAX_RELAY: {
    async get() { return value; },
    async put(key, text) { assert.equal(key, "origin"); value = JSON.parse(text); writes++; },
  }, state() { return { value, writes }; } };
}
function request(path, options) { return new Request(base + path, options); }
function registration(value = origin, auth = token) {
  return request("/internal/relay", { method: "PUT", headers: { authorization: "Bearer " + auth },
    body: JSON.stringify({ origin: value }) });
}

test("administration stays inaccessible and anonymous registration cannot write", async t => {
  const env = await environment({ origin });
  t.mock.method(globalThis, "fetch", () => { throw new Error("must not fetch"); });
  for (const path of ["/v1/status", "/v1/devices", "/setup/ha/callback", "/internal/relay"]) {
    assert.equal((await worker.fetch(request(path), env)).status, 404);
  }
  assert.equal((await worker.fetch(registration(origin, "x".repeat(64)), env)).status, 404);
  assert.equal(env.state().writes, 0);
});

test("registration verifies the runtime and stores only the origin; retries are idempotent", async t => {
  const env = await environment();
  const calls = [];
  t.mock.method(globalThis, "fetch", async (url, options) => {
    calls.push(url); assert.equal(url, origin + "/health");
    assert.equal(options.redirect, "manual");
    return Response.json({ service: "MAX", status: "ok", version: "0.1.2" });
  });
  for (let i = 0; i < 2; i++) {
    const response = await worker.fetch(registration(), env);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { status: "registered", origin_hash: await hash(origin) });
  }
  assert.equal(calls.length, 2); assert.equal(env.state().writes, 1);
  assert.equal(env.state().value.origin, origin);
  assert.ok(!JSON.stringify(env.state().value).includes(token));
});

for (const value of ["http://127.0.0.1:8787", "https://example.org", "https://a.trycloudflare.com.evil.test",
  "https://a.trycloudflare.com/path", "https://user@a.trycloudflare.com", "https://a.trycloudflare.com?x=1"]) {
  test("registration rejects unrelated or unsafe origin: " + value, async t => {
    const env = await environment();
    t.mock.method(globalThis, "fetch", () => { throw new Error("must not fetch"); });
    assert.equal((await worker.fetch(registration(value), env)).status, 400);
    assert.equal(env.state().writes, 0);
  });
}

test("an unavailable runtime cannot replace the last working origin", async t => {
  const env = await environment({ origin });
  t.mock.method(globalThis, "fetch", async () => new Response("private failure", { status: 503 }));
  const response = await worker.fetch(registration("https://other.trycloudflare.com"), env);
  assert.equal(response.status, 503); assert.equal(env.state().writes, 0);
  assert.ok(!(await response.text()).includes("private failure"));
});

test("health exposes only readiness fields and follows no upstream redirects", async t => {
  const env = await environment({ origin });
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(options.redirect, "manual");
    return Response.json({ service: "MAX", status: "ok", version: "0.1.2", api_token: "private" });
  });
  const response = await worker.fetch(request("/health"), env);
  assert.deepEqual(await response.json(), { service: "MAX", status: "ok", version: "0.1.2" });
  assert.equal(response.headers.get("cache-control"), "no-store");
});

test("unsigned Alexa requests are rejected before contacting Linux", async t => {
  const env = await environment({ origin });
  t.mock.method(globalThis, "fetch", () => { throw new Error("must not fetch"); });
  assert.equal((await worker.fetch(request("/alexa", { method: "POST", body: "{}" }), env)).status, 400);
});

test("voice preserves exact signed bytes and only permitted headers", async t => {
  const env = await environment({ origin });
  const raw = '{ "request": {"text":"hola Máx"} }\n';
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(url, origin + "/alexa"); assert.equal(options.method, "POST");
    assert.equal(new TextDecoder().decode(options.body), raw);
    assert.equal(options.headers.get("signature-256"), "signed-by-amazon");
    assert.equal(options.headers.get("signaturecertchainurl"), "https://s3.amazonaws.com/cert.pem");
    assert.equal(options.headers.get("cookie"), null);
    assert.equal(options.redirect, "manual");
    return Response.json({ response: { outputSpeech: { text: "MAX listo" } } });
  });
  const response = await worker.fetch(request("/alexa", { method: "POST", body: raw, headers: {
    "signature-256": "signed-by-amazon", signaturecertchainurl: "https://s3.amazonaws.com/cert.pem",
    "content-type": "application/json", cookie: "private-browser-cookie",
  } }), env);
  assert.equal(response.status, 200);
  assert.equal((await response.json()).response.outputSpeech.text, "MAX listo");
});

test("oversized voice bodies are rejected without forwarding", async t => {
  const env = await environment({ origin });
  t.mock.method(globalThis, "fetch", () => { throw new Error("must not fetch"); });
  assert.equal((await worker.fetch(request("/v1/voice", { method: "POST", body: "x".repeat(65537) }), env)).status, 413);
});

test("missing registry or untrusted registry data fails closed", async t => {
  t.mock.method(globalThis, "fetch", () => { throw new Error("must not fetch"); });
  for (const env of [{}, await environment(), await environment({ origin: "http://127.0.0.1:8787" })]) {
    const response = await worker.fetch(request("/health"), env);
    assert.equal(response.status, 503); assert.deepEqual(await response.json(), { service: "MAX", status: "starting" });
  }
});

test("an upstream redirect is not followed and is never returned to Alexa", async t => {
  const env = await environment({ origin });
  t.mock.method(globalThis, "fetch", async () => new Response(null, { status: 302, headers: { location: "https://example.org" } }));
  assert.equal((await worker.fetch(request("/v1/voice", { method: "POST", body: "{}" }), env)).status, 503);
});
