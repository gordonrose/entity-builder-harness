import { deepEqual, equal, throws } from "node:assert/strict";
import { createRequire } from "node:module";
import { createAlbTrustedClientAddressResolver } from "../../src/index";

const resolver = createAlbTrustedClientAddressResolver({
  ingressMode: "alb-security-group-only",
});

equal(resolver.resolve({
  socketPeerAddress: "10.0.1.15",
  headers: { "x-forwarded-for": "198.51.100.20, 203.0.113.31" },
}), "203.0.113.31");

equal(resolver.resolve({
  socketPeerAddress: "10.0.1.15",
  headers: { "x-forwarded-for": "not-an-address" },
}), "10.0.1.15");

equal(resolver.resolve({
  socketPeerAddress: "10.0.1.15",
  headers: {},
}), "10.0.1.15");

deepEqual(
  resolver.resolve({
    socketPeerAddress: "10.0.1.15",
    headers: { "x-forwarded-for": ["198.51.100.20", "203.0.113.31"] },
  }),
  "198.51.100.20",
);

console.log("ECS Fargate trusted-ingress adapter runtime test passed.");

async function diagnosticsProof(): Promise<void> {
  const fallback = (reason: string, source: string) => ({ schema: "core/diagnostic-record/v1", code: "platform-server.client-address-fallback-selected", definitionVersion: 1,
    detail: { phase: "client-address-selection", reason, source, effect: "fallback-selected" } });
  let modeReads = 0;
  throws(() => createAlbTrustedClientAddressResolver(new Proxy({ ingressMode: "synthetic-private-trust-canary" }, { get(value, key) { modeReads++; return Reflect.get(value, key); } }) as never), (error: unknown) => {
    equal(error instanceof RangeError, true);
    equal((error as Error).message, "ECS Fargate client-address trust requires ALB-only task ingress.");
    deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, { schema: "core/diagnostic-record/v1", code: "platform-server.client-address-trust-invalid", definitionVersion: 1,
      detail: { phase: "configuration", setting: "http.client-address-trust", reason: "unsupported", effect: "rejected" } });
    equal(JSON.stringify(error).includes("synthetic-private-trust-canary"), false);
    return true;
  });
  equal(modeReads, 1);
  for (const [headers, expected, reason] of [
    [{}, "10.0.1.15", "forwarded-header-missing"],
    [{ "x-forwarded-for": [] }, "10.0.1.15", "forwarded-header-missing"],
    [{ "x-forwarded-for": "" }, "10.0.1.15", "forwarded-final-address-invalid"],
    [{ "x-forwarded-for": "198.51.100.20, synthetic-private-address-canary" }, "10.0.1.15", "forwarded-final-address-invalid"],
  ] as const) {
    const records: unknown[] = [];
    equal(resolver.resolve({ headers, socketPeerAddress: "10.0.1.15", onDiagnostic: (record) => { records.push(record); } }), expected);
    deepEqual(records, [fallback(reason, "socket-peer")]);
    equal(JSON.stringify(records).includes("synthetic-private-address-canary"), false);
    equal(JSON.stringify(records).includes("10.0.1.15"), false);
  }
  const unavailable: unknown[] = [];
  equal(resolver.resolve({ headers: {}, onDiagnostic: (record) => { unavailable.push(record); } }), undefined);
  deepEqual(unavailable, [fallback("forwarded-header-missing", "unavailable")]);
  const validObservations: unknown[] = [];
  equal(resolver.resolve({ headers: { "x-forwarded-for": "198.51.100.20, 2001:db8::1" }, onDiagnostic: (record) => { validObservations.push(record); } }), "2001:db8::1");
  deepEqual(validObservations, [], "ordinary valid selection is silent");
  let callbackGetterReads = 0;
  const accessor = Object.defineProperty({ headers: {}, socketPeerAddress: "10.0.1.15" }, "onDiagnostic", { get() { callbackGetterReads++; throw new Error("synthetic-private-observer-canary"); } });
  equal(resolver.resolve(accessor), "10.0.1.15"); equal(callbackGetterReads, 0);
  const unhandled: unknown[] = [];
  const onUnhandled = (error: unknown) => { unhandled.push(error); };
  process.on("unhandledRejection", onUnhandled);
  try {
    for (const observer of [() => { throw new Error("synthetic-private-observer-canary"); }, () => Promise.reject(new Error("synthetic-private-observer-canary")), () => ({ then(_resolve: unknown, reject: (error: unknown) => void) { reject(new Error("synthetic-private-observer-canary")); } })]) {
      equal(resolver.resolve({ headers: {}, socketPeerAddress: "10.0.1.15", onDiagnostic: observer }), "10.0.1.15");
    }
    await new Promise<void>((resolve) => setImmediate(resolve));
    deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", onUnhandled); }
  const net = createRequire(__filename)("node:net") as { isIP(value: string): number };
  const intrinsicIp = net.isIP, intrinsicTrim = String.prototype.trim, intrinsicSplit = String.prototype.split;
  const raw = " bad-first , not-an-address ";
  let ipCalls = 0, trims = 0, splits = 0;
  const reads: string[] = [];
  try {
    net.isIP = (value) => { ipCalls++; equal(value, "not-an-address"); return intrinsicIp(value); };
    String.prototype.trim = function () { if (String(this) === " bad-first " || String(this) === " not-an-address ") trims++; return Reflect.apply(intrinsicTrim, this, []); };
    String.prototype.split = function (this: string, separator: string | RegExp, limit?: number) { if (String(this) === raw) splits++; return Reflect.apply(intrinsicSplit, this, [separator, limit]); } as typeof intrinsicSplit;
    const input = new Proxy({ get headers() { reads.push("header-value"); return { "x-forwarded-for": raw }; }, get socketPeerAddress() { reads.push("peer-value"); return "10.0.1.15"; }, onDiagnostic: () => { reads.push("observe"); } }, { get(value, name) { reads.push(String(name)); return Reflect.get(value, name); } });
    equal(resolver.resolve(input), "10.0.1.15");
    deepEqual(reads, ["headers", "header-value", "socketPeerAddress", "peer-value", "observe"]);
    deepEqual([splits, trims, ipCalls], [1, 2, 1]);
  } finally { net.isIP = intrinsicIp; String.prototype.trim = intrinsicTrim; String.prototype.split = intrinsicSplit; }
}
void diagnosticsProof().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
