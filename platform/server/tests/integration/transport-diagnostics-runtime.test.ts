import { deepEqual, equal, rejects } from "node:assert/strict";
import { EventEmitter } from "node:events";
import { Server, type IncomingMessage, type ServerResponse } from "node:http";
import { parseDiagnosticRecord, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { correlationId } from "@kanbien/core/shared";
import type { PlatformServerRequest, PlatformServerResponse } from "../../src/index";
import { observeServerDiagnostic, platformServerDiagnosticCatalog, serverClientAddressFallbackRecord,
  serverClientAddressTrustConfigurationRecord } from "../../src/diagnostics";
import { listenNodePlatformServer, resolvePlatformServerTransportOptions, type PlatformServerTransportFailure } from "../../src/transport";

const canary = "synthetic-private-transport-canary";
const requestId = correlationId("transport-test-id");
const tick = (): Promise<void> => new Promise((resolve) => setImmediate(resolve));
const response: PlatformServerResponse = { status: 200, headers: {}, body: { ok: true }, middleware: [] };

class FakeResponse extends EventEmitter {
  writableEnded = false;
  destroyed = false;
  statusCode = 200;
  readonly headers: Record<string, string> = {};
  body: string | undefined;
  readonly done: Promise<void>;
  private finish!: () => void;
  constructor() { super(); this.done = new Promise((resolve) => { this.finish = resolve; }); }
  setHeader(key: string, value: string): this { this.headers[key] = value; return this; }
  end(body: string | undefined): this { this.body = body; this.writableEnded = true; this.finish(); return this; }
}

interface RequestOptions {
  readonly method?: string;
  readonly url?: string;
  readonly headers?: Record<string, string | readonly string[]>;
  readonly chunks?: readonly (Buffer | string)[];
  readonly streamError?: unknown;
}
function fakeRequest(options: RequestOptions = {}): IncomingMessage {
  return {
    method: options.method ?? "GET", url: options.url ?? "/test", headers: options.headers ?? {},
    socket: { remoteAddress: canary },
    async *[Symbol.asyncIterator]() {
      for (const chunk of options.chunks ?? []) yield chunk;
      if (options.streamError !== undefined) throw options.streamError;
    },
  } as unknown as IncomingMessage;
}

/** Real Node server listeners, controlled inputs; no production test seam or socket required. */
async function fixture(run: (input: {
  readonly server: Server;
  readonly handle: Awaited<ReturnType<typeof listenNodePlatformServer>>;
  readonly failures: PlatformServerTransportFailure[];
  readonly observations: DiagnosticRecord[];
  readonly receivedErrors: unknown[];
  readonly sent: (options?: RequestOptions) => FakeResponse;
  readonly handlerRequests: PlatformServerRequest[];
}) => Promise<void>, overrides: Partial<Parameters<typeof listenNodePlatformServer>[0]> = {},
  setup?: (server: Server) => void): Promise<void> {
  const originalListen = Server.prototype.listen;
  const originalAddress = Server.prototype.address;
  const originalClose = Server.prototype.close;
  const originalCloseAll = Server.prototype.closeAllConnections;
  let selectedServer: Server | undefined;
  Reflect.set(Server.prototype, "listen", function (this: Server) {
    selectedServer = this; setup?.(this); queueMicrotask(() => this.emit("listening")); return this;
  });
  Reflect.set(Server.prototype, "address", () => ({ port: 31000, address: canary, family: "IPv4" }));
  Reflect.set(Server.prototype, "close", function (this: Server, callback: (error?: Error) => void) {
    queueMicrotask(() => callback()); return this;
  });
  Reflect.set(Server.prototype, "closeAllConnections", () => {});
  const failures: PlatformServerTransportFailure[] = [];
  const observations: DiagnosticRecord[] = [];
  const receivedErrors: unknown[] = [];
  const handlerRequests: PlatformServerRequest[] = [];
  const transport = resolvePlatformServerTransportOptions({ maxRequestBodyBytes: 16, handlerTimeoutMs: 5, shutdownDrainTimeoutMs: 5, maxConcurrentRequests: 1 });
  if (!transport.ok) throw new Error("Invalid fixture options.");
  try {
    const handle = await listenNodePlatformServer({
      options: {}, transport: transport.value,
      handle: async (request) => { handlerRequests.push(request); return response; },
      admit: async () => ({ requestId }),
      failure: (failure) => { failures.push(failure); return { status: failure.status, headers: {}, middleware: [], body: { error: { code: failure.code, message: failure.message } } }; },
      onServerError: (error) => { receivedErrors.push(error); },
      onDiagnostic: (record) => { observations.push(record); },
      ...overrides,
    });
    const server = selectedServer!;
    const sent = (options?: RequestOptions): FakeResponse => {
      const res = new FakeResponse(); server.emit("request", fakeRequest(options), res as unknown as ServerResponse); return res;
    };
    await run({ server, handle, failures, observations, receivedErrors, sent, handlerRequests });
    for (const record of [...observations, ...failures.flatMap((failure) => failure.diagnosticRecord === undefined ? [] : [failure.diagnosticRecord])]) {
      const definition: DiagnosticDefinition | undefined = platformServerDiagnosticCatalog.definitions.find((candidate) => candidate.code === record.code && candidate.version === record.definitionVersion);
      equal(definition !== undefined && parseDiagnosticRecord(definition, record).ok, true);
      equal(JSON.stringify(record).includes(canary), false);
    }
  } finally {
    Reflect.set(Server.prototype, "listen", originalListen);
    Reflect.set(Server.prototype, "address", originalAddress);
    Reflect.set(Server.prototype, "close", originalClose);
    Reflect.set(Server.prototype, "closeAllConnections", originalCloseAll);
  }
}

async function rejectedRequests(): Promise<void> {
  const cases: readonly [RequestOptions, number, string][] = [
    [{ url: "http://[" + canary }, 400, "url-invalid"],
    [{ method: "TRACE" }, 405, "method-unsupported"],
    [{ headers: { "content-length": "1.5" } }, 400, "declared-length-not-integer"],
    [{ headers: { "content-length": "-1" } }, 400, "declared-length-negative"],
    [{ headers: { "content-length": "17" } }, 413, "declared-length-over-limit"],
    [{ method: "POST", chunks: ["12345678901234567"] }, 413, "streamed-body-over-limit"],
    [{ method: "POST", chunks: ["{}"] }, 415, "media-type-missing"],
    [{ method: "POST", chunks: ["{}"], headers: { "content-type": " ;" } }, 415, "media-type-empty"],
    [{ method: "POST", chunks: ["{}"], headers: { "content-type": canary } }, 415, "media-type-unsupported"],
    [{ method: "POST", chunks: ["{"], headers: { "content-type": "application/json" } }, 400, "body-decoding-threw"],
  ];
  await fixture(async ({ failures, sent, handlerRequests }) => {
    for (const [options, status, reason] of cases) {
      const res = sent(options); await res.done;
      equal(res.statusCode, status);
      equal((failures.at(-1)?.diagnosticRecord?.detail as { reason: string }).reason, reason);
      equal(res.body!.includes("diagnosticRecord"), false);
      equal(res.body!.includes(canary), false);
    }
    equal(handlerRequests.length, 0);
    for (const options of [
      { headers: { "content-length": "" } },
      { headers: { "content-length": "0x10" } },
      { method: "POST", chunks: [] },
      { method: "POST", chunks: ["{}"], headers: { "content-type": "Application/JSON ; charset=utf-8" } },
    ]) {
      const res = sent(options); await res.done; equal(res.statusCode, 200);
    }
    equal(failures.length, cases.length);
  });
}

async function callbackBoundaries(): Promise<void> {
  const streamError = Object.freeze(new Error(canary));
  await fixture(async ({ failures, sent }) => {
    const res = sent({ method: "POST", streamError }); await res.done;
    equal(failures[0]?.error, streamError);
    deepEqual(failures[0]?.diagnosticRecord?.detail, { phase: "body-stream", reason: "threw", effect: "request-not-returned" });
  });
  for (const phase of ["metadata", "admission", "handler"] as const) {
    const failure = Object.freeze(new Error(canary));
    const overrides = phase === "metadata" ? { clientAddressResolver: { resolve: () => { throw failure; } } }
      : phase === "admission" ? { admit: async () => { throw failure; } } : { handle: async () => { throw failure; } };
    await fixture(async ({ failures, sent }) => {
      const res = sent(); await res.done; equal(res.statusCode, 500);
      equal(failures[0]?.error, failure);
      deepEqual(failures[0]?.diagnosticRecord?.detail, { phase, reason: "threw", effect: "request-not-returned" });
    }, overrides);
  }
  const writerError = Object.freeze(new Error(canary));
  await fixture(async ({ failures, observations, sent }) => {
    const res = sent(); await res.done;
    equal(failures[0]?.error, writerError);
    deepEqual(observations[0]?.detail, { phase: "response-serialization", reason: "threw", effect: "unknown" });
    equal(failures[0]?.diagnosticRecord, undefined);
    equal(res.statusCode, 500);
  }, { handle: async () => ({ status: 200, headers: {}, body: { toJSON() { throw writerError; } } } as unknown as PlatformServerResponse) });
  for (const phase of ["response-headers", "response-status", "response-end"] as const) {
    await fixture(async ({ server, failures, observations }) => {
      const res = new FakeResponse();
      let calls = 0;
      if (phase === "response-headers") {
        res.setHeader = function (key, value) { if (calls++ === 0) throw writerError; return FakeResponse.prototype.setHeader.call(this, key, value); };
      } else if (phase === "response-status") {
        let status = 200;
        Object.defineProperty(res, "statusCode", { get: () => status, set: (value: number) => { if (calls++ === 0) throw writerError; status = value; } });
      } else {
        Object.defineProperty(res, "end", { get() { if (calls++ === 0) throw writerError; return FakeResponse.prototype.end; } });
      }
      server.emit("request", fakeRequest(), res as unknown as ServerResponse); await res.done;
      equal(failures[0]?.error, writerError);
      equal((observations[0]?.detail as { phase: string }).phase, phase);
      equal(res.statusCode, 500);
    }, { handle: async () => ({ ...response, headers: { "x-test": "value" } }) });
  }
  const evaluationOrder: string[] = [];
  await fixture(async ({ server }) => {
    const res = new FakeResponse();
    Object.defineProperty(res, "end", { get() { evaluationOrder.push("end"); return FakeResponse.prototype.end; } });
    server.emit("request", fakeRequest(), res as unknown as ServerResponse); await res.done;
    deepEqual(evaluationOrder.slice(0, 2), ["end", "json"]);
  }, { handle: async () => ({ ...response, body: { toJSON() { evaluationOrder.push("json"); throw writerError; } } } as unknown as PlatformServerResponse) });
  let failureCalls = 0;
  let finalFailure: PlatformServerTransportFailure | undefined;
  await fixture(async ({ sent }) => {
    const res = sent({ method: "TRACE" }); await res.done;
    equal(res.statusCode, 500); equal(finalFailure?.error, writerError);
    equal((finalFailure?.diagnosticRecord?.detail as { phase: string }).phase, "failure-projection");
  }, { failure: (failure) => {
    if (failureCalls++ === 0) throw writerError;
    finalFailure = failure; return { status: failure.status, headers: {}, middleware: [], body: null };
  } });
  let observedMethod: string | undefined;
  let observedPath: string | undefined;
  await fixture(async ({ server }) => {
    const res = new FakeResponse(); let calls = 0;
    Object.defineProperty(res, "end", { get() { if (calls++ === 0) throw writerError; return FakeResponse.prototype.end; } });
    server.emit("request", fakeRequest({ method: "TRACE", url: "/private" }), res as unknown as ServerResponse); await res.done;
    equal(observedMethod, "TRACE"); equal(observedPath, "/private");
  }, { onDiagnostic: (_record, request) => { observedMethod = request?.method; observedPath = request?.path; } });
}

async function listenerFailures(): Promise<void> {
  const error = Object.freeze(new Error(canary));
  for (const reason of ["threw", "error-event"] as const) {
    const observations: DiagnosticRecord[] = [];
    const legacy: unknown[] = [];
    await rejects(fixture(async () => { throw new Error("Unexpected listener success."); }, {
      onDiagnostic: (record) => { observations.push(record); }, onServerError: (value) => { legacy.push(value); },
    }, (server) => {
      if (reason === "threw") throw error;
      queueMicrotask(() => server.emit("error", error));
    }), (value) => value === error);
    deepEqual(observations.at(-1)?.detail, { phase: "listen", reason, effect: "listener-not-returned" });
    equal(observations.length, 1, "One native listen error is observed once, not repeated by both listeners.");
    equal(legacy.length, reason === "error-event" ? 1 : 0);
    if (reason === "error-event") equal(legacy[0], error);
  }
  let nativeValidation: unknown;
  try { new EventEmitter().on("error", undefined as unknown as () => void); }
  catch (value) { nativeValidation = value; }
  await rejects(fixture(async () => { throw new Error("Unexpected invalid-listener success."); }, {
    onServerError: undefined as unknown as (value: unknown) => void,
  }), (value) => value instanceof TypeError && nativeValidation instanceof TypeError && value.message === nativeValidation.message);
  const configured = resolvePlatformServerTransportOptions();
  if (!configured.ok) throw new Error("Invalid construction fixture.");
  const constructionRecords: DiagnosticRecord[] = [];
  await rejects(fixture(async () => { throw new Error("Unexpected invalid-server success."); }, {
    transport: { ...configured.value, maxHeaderBytes: -1 }, onDiagnostic: (record) => { constructionRecords.push(record); },
  }), RangeError);
  deepEqual(constructionRecords[0]?.detail, { phase: "server-construction", reason: "threw", effect: "listener-not-returned" });
}

async function deadlinesAndCapacity(): Promise<void> {
  let settle!: (value: PlatformServerResponse) => void;
  let calls = 0;
  await fixture(async ({ failures, sent }) => {
    const first = sent(); await first.done;
    deepEqual(failures[0]?.diagnosticRecord?.detail, { reason: "handler-deadline-observed", phase: "handler", effect: "handler-still-pending" });
    const second = sent(); await second.done;
    equal(second.statusCode, 503);
    equal((failures[1]?.diagnosticRecord?.detail as { reason: string }).reason, "concurrency-capacity-reached");
    equal(calls, 1);
    settle(response); await tick();
    const third = sent(); await third.done; equal(third.statusCode, 200); equal(calls, 2);
  }, { handle: async () => { calls++; return calls === 1 ? new Promise((resolve) => { settle = resolve; }) : response; } });
  await fixture(async ({ failures, sent }) => {
    const res = sent(); await res.done; equal(res.statusCode, 504);
    deepEqual(failures[0]?.diagnosticRecord?.detail, { reason: "handler-result-unavailable", phase: "handler", effect: "handler-result-not-returned" });
    await tick();
  }, { handle: async () => undefined as unknown as PlatformServerResponse });
  let rejectLate!: (error: unknown) => void;
  const lateError = Object.freeze(new Error(canary));
  await fixture(async ({ sent, observations, receivedErrors }) => {
    const res = sent(); await res.done;
    rejectLate(lateError); await tick();
    equal(receivedErrors[0], lateError);
    deepEqual(observations[0]?.detail, { phase: "late-handler", reason: "threw", effect: "handler-settled" });
  }, { handle: () => new Promise((_resolve, reject) => { rejectLate = reject; }) });
}

async function metadataSelection(): Promise<void> {
  const expected = serverClientAddressFallbackRecord("forwarded-header-missing", "socket-peer");
  const calls: string[] = [];
  const records: DiagnosticRecord[][] = [];
  await fixture(async ({ sent }) => {
    const res = sent(); await res.done;
    deepEqual(calls, ["resolve", "metadata", "admit"]);
    equal(records[0]?.length, 8);
    deepEqual(records[0]?.[0], expected);
  }, {
    clientAddressResolver: { resolve: (input) => {
      calls.push("resolve");
      input.onDiagnostic?.({ ...expected, detail: { ...expected.detail, raw: canary } });
      for (let index = 0; index < 10; index++) input.onDiagnostic?.(expected);
      return input.socketPeerAddress;
    } },
    onRequestMetadata: (_request, selected) => { calls.push("metadata"); records.push([...selected]); return Promise.reject(new Error(canary)); },
    admit: async () => { calls.push("admit"); return { requestId }; },
  });
  await tick();
}

async function processAndResponseObservations(): Promise<void> {
  const observedError = Object.freeze(new Error(canary));
  let originalReceiver: unknown;
  await fixture(async ({ server, observations }) => {
    let destroyed = 0;
    server.emit("clientError", observedError, { destroy() { destroyed++; } });
    equal(destroyed, 1);
    server.emit("error", observedError);
    deepEqual(observations.map((record) => (record.detail as { phase: string }).phase), ["client-error", "server-error"]);
    equal(originalReceiver, server);
  }, { onServerError: function (this: unknown, error) { originalReceiver = this; equal(error, observedError); } });
  let finishClose: ((error?: Error) => void) | undefined;
  let closeAllCalls = 0;
  await fixture(async ({ handle, failures, sent, observations }) => {
    const closing = handle.close();
    const res = sent(); await res.done; equal(res.statusCode, 503);
    equal((failures[0]?.diagnosticRecord?.detail as { reason: string }).reason, "server-closing");
    await new Promise((resolve) => setTimeout(resolve, 10));
    equal(closeAllCalls, 1);
    deepEqual(observations[0]?.detail, { reason: "drain-deadline-observed", phase: "shutdown", effect: "shutdown-still-pending" });
    finishClose!(); await closing;
  }, {}, (server) => {
    Reflect.set(server, "close", (callback: (error?: Error) => void) => { finishClose = callback; return server; });
    Reflect.set(server, "closeAllConnections", () => { closeAllCalls++; });
  });
  for (const phase of ["close-invocation", "close-callback"] as const) {
    await fixture(async ({ handle, observations }) => {
      await rejects(handle.close(), (error) => error === observedError);
      deepEqual(observations[0]?.detail, { phase, reason: phase === "close-callback" ? "callback-error" : "threw", effect: "close-not-confirmed" });
    }, {}, (server) => {
      Reflect.set(server, "close", (callback: (error?: Error) => void) => {
        if (phase === "close-invocation") throw observedError;
        callback(observedError); return server;
      });
    });
  }
  let complete!: (value: PlatformServerResponse) => void;
  let request: PlatformServerRequest | undefined;
  await fixture(async ({ server, observations }) => {
    const res = new FakeResponse();
    server.emit("request", fakeRequest(), res as unknown as ServerResponse);
    await tick(); res.destroyed = true; res.emit("close");
    equal(request?.abortSignal?.aborted, true);
    complete(response); await tick();
    deepEqual(observations.map((record) => (record.detail as { reason: string }).reason), ["response-closed-before-end", "response-destroyed"]);
  }, { handle: async (value) => { request = value; return new Promise((resolve) => { complete = resolve; }); } });
  await fixture(async ({ server, observations }) => {
    const res = new FakeResponse(); res.writableEnded = true;
    server.emit("request", fakeRequest(), res as unknown as ServerResponse); await tick();
    equal((observations[0]?.detail as { reason: string }).reason, "response-already-ended");
  });
}

async function observerIsolationAndDefinitions(): Promise<void> {
  const trust = serverClientAddressTrustConfigurationRecord();
  deepEqual(trust.detail, { phase: "configuration", setting: "http.client-address-trust", reason: "unsupported", effect: "rejected" });
  for (const observer of [
    () => { throw new Error(canary); },
    () => Promise.reject(new Error(canary)),
    () => ({ then(_resolve: unknown, reject: (error: unknown) => void) { reject(new Error(canary)); } }),
    () => Object.defineProperty({}, "then", { get() { throw new Error(canary); } }),
  ]) observeServerDiagnostic(observer, trust);
  for (const observer of [() => { throw new Error(canary); }, () => Promise.reject(new Error(canary))]) {
    await fixture(async ({ sent, server, receivedErrors }) => {
      const res = sent(); await res.done; equal(res.statusCode, 200);
      const failure = new Error(canary); server.emit("error", failure); equal(receivedErrors[0], failure);
    }, { onDiagnostic: observer });
  }
  await tick();
  const definition: DiagnosticDefinition = platformServerDiagnosticCatalog.definitions.find((candidate) => candidate.code === trust.code)!;
  equal(parseDiagnosticRecord(definition, { ...trust, detail: { ...trust.detail, raw: canary } }).ok, false);
  equal(parseDiagnosticRecord(definition, { ...trust, definitionVersion: 99 }).ok, false);
  equal(parseDiagnosticRecord(definition, { ...trust, detail: { ...trust.detail, reason: canary } }).ok, false);
}

async function main(): Promise<void> {
  await rejectedRequests(); await callbackBoundaries(); await deadlinesAndCapacity();
  await listenerFailures(); await metadataSelection(); await processAndResponseObservations(); await observerIsolationAndDefinitions();
  console.log("Platform transport diagnostic predicate, effect and isolation tests passed.");
}
void main().catch((error) => { console.error(error); process.exitCode = 1; });
