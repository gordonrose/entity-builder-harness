import { deepEqual, equal, throws } from "node:assert/strict";
import { isoDateTimeFromDate, messageDescriptor } from "../src/shared/index";
import {
  defaultMetricLabelStringLengthLimit,
  defaultUnsafeMetricLabelNames,
  createInMemoryTracer,
  fixedHealthCheck,
  healthCheckName,
  healthCheckResult,
  metricLabels,
  metricName,
  metricPoint,
  metricUnit,
  monitoringComponent,
  monitoringComponentName,
  monitoringMetadata,
  monitoringSignalDefinition,
  monitoringSignalName,
  noopMetrics,
  noopTracer,
  spanId,
  traceContext,
  traceId,
  traceSpanName,
  type HealthCheckResult,
  type MetricPoint,
  type Metrics,
  coreMonitoringValidationDiagnosticRecord,
  coreMonitoringValidationDiagnostic,
  coreMonitoringBoundaryDiagnosticRecord,
  observeCoreMonitoringDiagnostic,
  type CoreMonitoringDiagnosticOptions,
} from "../src/monitoring/index";
import type { DiagnosticRecord } from "../src/diagnostics/index";

async function main(): Promise<void> {
  const checkedAt = isoDateTimeFromDate(new Date("2026-07-07T10:00:00Z"));
  const apiComponent = monitoringComponent({ type: "api", name: "public-api" });
  deepEqual(apiComponent, { type: "api", name: "public-api" });
  throws(
    () => monitoringComponent({ type: "database" as "api", name: "Primary Database" }),
    /monitoring component name must use lowercase dot-separated segments/,
  );

  const metadata = {
    dependency: "postgres",
    attempts: 1,
    nested: { reachable: true },
  };
  const result = healthCheckResult({
    name: healthCheckName("api.readiness"),
    type: "readiness",
    component: apiComponent,
    status: "degraded",
    checkedAt,
    durationMs: 42,
    message: messageDescriptor({
      code: "DEPENDENCY_DEGRADED",
      defaultMessage: "A dependency is reachable but degraded.",
      messageKey: "monitoring.health.degraded",
    }),
    metadata,
  });
  metadata.nested.reachable = false;
  deepEqual(result.metadata, {
    dependency: "postgres",
    attempts: 1,
    nested: { reachable: true },
  });
  throws(
    () =>
      healthCheckResult({
        name: healthCheckName("api.readiness"),
        type: "readiness",
        component: apiComponent,
        status: "healthy",
        checkedAt,
        durationMs: -1,
      }),
    /health check durationMs must be non-negative/,
  );
  throws(
    () =>
      healthCheckResult({
        name: healthCheckName("api.readiness"),
        type: "dependency",
        component: apiComponent,
        status: "healthy",
        checkedAt,
        metadata: {
          checkedAt: new Date() as never,
        },
      }),
    /monitoring metadata must contain only plain objects/,
  );

  const check = fixedHealthCheck(result);
  const checked = await check.check();
  deepEqual(checked, result);

  const safeLabels = metricLabels({
    service: "api",
    route: "deals.list",
    status_code: 200,
    cached: false,
  });
  deepEqual(safeLabels, {
    service: "api",
    route: "deals.list",
    status_code: 200,
    cached: false,
  });
  throws(() => metricLabels({ user_id: "user-123" }), /unsafe or too high-cardinality/);
  throws(() => metricLabels({ tenant_id: "tenant-123" }), /unsafe or too high-cardinality/);
  throws(() => metricLabels({ tenant: "enterprise" }), /unsafe or too high-cardinality/);
  throws(() => metricLabels({ http_path: "/deals/123" }), /unsafe or too high-cardinality/);
  throws(() => metricLabels({ "http-method": "GET" }), /must use lowercase snake_case/);
  throws(() => metricLabels({ status_code: Number.NaN }), /metric label "status_code" must be a finite number/);
  throws(
    () =>
      metricLabels({
        route: "a".repeat(defaultMetricLabelStringLengthLimit + 1),
      }),
    /must not exceed/,
  );
  equal(defaultUnsafeMetricLabelNames.includes("token"), true);

  const point: MetricPoint = metricPoint({
    name: metricName("api.requests.total"),
    kind: "counter",
    value: 1,
    unit: metricUnit("count"),
    recordedAt: checkedAt,
    labels: safeLabels,
  });
  deepEqual(point, {
    name: "api.requests.total",
    kind: "counter",
    value: 1,
    unit: "count",
    recordedAt: checkedAt,
    labels: safeLabels,
  });
  throws(
    () =>
      metricPoint({
        name: metricName("api.requests.total"),
        kind: "counter",
        value: Number.POSITIVE_INFINITY,
        unit: metricUnit("count"),
        recordedAt: checkedAt,
      }),
    /metric value must be a finite number/,
  );
  throws(() => metricName("Api Requests"), /metric name must use lowercase dot-separated segments/);
  throws(() => metricUnit("milliseconds per request"), /metric unit must use lowercase token characters/);

  const signal = monitoringSignalDefinition({
    name: monitoringSignalName("api.request.latency"),
    category: "latency",
    owner: "platform-runtime",
    intents: ["alerting", "service-level-indicator"],
    component: apiComponent,
    metric: {
      name: metricName("api.request.duration_ms"),
      kind: "timer",
      unit: metricUnit("milliseconds"),
    },
  });
  deepEqual(signal, {
    name: "api.request.latency",
    category: "latency",
    owner: "platform-runtime",
    intents: ["alerting", "service-level-indicator"],
    component: apiComponent,
    metric: {
      name: "api.request.duration_ms",
      kind: "timer",
      unit: "milliseconds",
    },
  });
  throws(
    () =>
      monitoringSignalDefinition({
        name: monitoringSignalName("api.request.latency"),
        category: "latency",
        owner: "",
        intents: ["alerting"],
      }),
    /monitoring signal owner must be non-empty and trimmed/,
  );
  throws(
    () =>
      monitoringSignalDefinition({
        name: monitoringSignalName("api.request.latency"),
        category: "latency",
        owner: "platform-runtime",
        intents: [],
      }),
    /monitoring signal intents must include at least one intent/,
  );

  deepEqual(monitoringMetadata({ safe: true, nested: { value: 1 } }), {
    safe: true,
    nested: { value: 1 },
  });

  const written: MetricPoint[] = [];
  const metrics: Metrics = {
    record: (entry) => {
      written.push(entry);
    },
  };
  await metrics.record(point);
  deepEqual(written, [point]);
  await noopMetrics.record(point);

  const tracer = createInMemoryTracer();
  const requestSpan = tracer.startSpan({
    name: traceSpanName("platform.server.request"),
    attributes: { method: "GET" },
  });
  const handlerSpan = tracer.startSpan({
    name: traceSpanName("platform.server.handler"),
    parent: requestSpan.context,
    attributes: { route: "smoke.echo" },
  });
  handlerSpan.end({ outcome: "succeeded", attributes: { status: 200 } });
  requestSpan.end({ outcome: "succeeded", attributes: { status: 200 } });
  requestSpan.end({ outcome: "failed" });
  deepEqual(tracer.spans(), [
    {
      name: "platform.server.request",
      context: { traceId: "trace-1", spanId: "span-1" },
      attributes: { method: "GET" },
      end: { outcome: "succeeded", attributes: { status: 200 } },
    },
    {
      name: "platform.server.handler",
      context: { traceId: "trace-1", spanId: "span-2", parentSpanId: "span-1" },
      attributes: { route: "smoke.echo" },
      end: { outcome: "succeeded", attributes: { status: 200 } },
    },
  ]);
  const providerContext = traceContext({ traceId: traceId("provider.trace-1"), spanId: spanId("provider-span-1") });
  deepEqual(providerContext, { traceId: "provider.trace-1", spanId: "provider-span-1" });
  throws(() => traceId("trace value"), /trace ID must use 1 to 128 safe identifier characters/);
  const noOpSpan = noopTracer.startSpan({ name: traceSpanName("platform.server.request") });
  noOpSpan.end({ outcome: "succeeded" });

  const healthResult: HealthCheckResult = checked;
  void healthResult;
  await monitoringDiagnostics();
}

async function monitoringDiagnostics(): Promise<void> {
  const events: DiagnosticRecord[] = [];
  const contexts: unknown[] = [];
  const diagnostics: CoreMonitoringDiagnosticOptions = { onDiagnostic(record, context) { equal(this, diagnostics); events[events.length] = record; contexts[contexts.length] = context; } };
  const checkedAt = isoDateTimeFromDate(new Date("2026-10-30T00:00:00Z"));
  const health = { name: healthCheckName("api.readiness"), type: "readiness" as const, status: "healthy" as const, component: monitoringComponent({ type: "api", name: "api" }), checkedAt };
  const point = { name: metricName("api.count"), kind: "counter" as const, value: 1, unit: metricUnit("count"), recordedAt: checkedAt };
  const signal = { name: monitoringSignalName("api.latency"), category: "latency" as const, owner: "api", intents: ["alerting" as const] };
  const guards: readonly [() => unknown, string, string, string, number?][] = [
    [() => monitoringComponentName("", diagnostics), "identifier", "component-name", "empty"],
    [() => monitoringComponentName(" api", diagnostics), "identifier", "component-name", "untrimmed"],
    [() => monitoringComponentName("API", diagnostics), "identifier", "component-name", "invalid-format"],
    [() => healthCheckName("api", diagnostics), "identifier", "health-name", "invalid-format"],
    [() => monitoringSignalName("api", diagnostics), "identifier", "signal-name", "invalid-format"],
    [() => traceSpanName("api", diagnostics), "identifier", "span-name", "invalid-format"],
    [() => traceId("", diagnostics), "identifier", "trace-id", "empty"],
    [() => spanId(" value", diagnostics), "identifier", "span-id", "untrimmed"],
    [() => traceId("x".repeat(129), diagnostics), "identifier", "trace-id", "invalid-format"],
    [() => monitoringComponent({ type: "secret" as never, name: "api" }, diagnostics), "component", "component-type", "closed-value-rejected"],
    [() => monitoringComponent({ type: "api", name: "" }, diagnostics), "component", "component-name", "empty"],
    [() => healthCheckResult({ ...health, type: "secret" as never }, diagnostics), "health-result", "health-type", "closed-value-rejected"],
    [() => healthCheckResult({ ...health, status: "secret" as never }, diagnostics), "health-result", "health-status", "closed-value-rejected"],
    [() => healthCheckResult({ ...health, durationMs: Infinity }, diagnostics), "health-result", "duration", "not-finite"],
    [() => healthCheckResult({ ...health, durationMs: -1 }, diagnostics), "health-result", "duration", "negative"],
    [() => monitoringSignalDefinition({ ...signal, category: "secret" as never }, diagnostics), "signal-definition", "signal-category", "closed-value-rejected"],
    [() => monitoringSignalDefinition({ ...signal, owner: "" }, diagnostics), "signal-definition", "signal-owner", "empty"],
    [() => monitoringSignalDefinition({ ...signal, owner: " api" }, diagnostics), "signal-definition", "signal-owner", "untrimmed"],
    [() => monitoringSignalDefinition({ ...signal, intents: [] }, diagnostics), "signal-definition", "signal-intents", "empty"],
    [() => monitoringSignalDefinition({ ...signal, intents: ["alerting", "secret" as never] }, diagnostics), "signal-definition", "signal-intent", "closed-value-rejected", 1],
    [() => monitoringSignalDefinition({ ...signal, metric: { ...point, kind: "secret" as never } }, diagnostics), "signal-definition", "metric-kind", "closed-value-rejected"],
    [() => metricPoint({ ...point, kind: "secret" as never }, diagnostics), "metric-point", "metric-kind", "closed-value-rejected"],
    [() => metricPoint({ ...point, value: NaN }, diagnostics), "metric-point", "metric-value", "not-finite"],
    [() => metricLabels({}, { maxStringLength: Infinity }, undefined, diagnostics), "metric-labels", "max-string-length", "not-finite"],
    [() => metricLabels({}, { maxStringLength: -1 }, undefined, diagnostics), "metric-labels", "max-string-length", "negative"],
  ];
  for (const [invoke, operation, field, reason, ordinal] of guards) {
    events.length = 0;
    let thrown: unknown;
    try { invoke(); } catch (error) { thrown = error; }
    equal(thrown instanceof TypeError, true);
    equal(events.length, 1);
    equal(events[0]?.code, "core.monitoring.validation-rejected");
    equal(events[0]?.definitionVersion, 1);
    deepEqual(coreMonitoringValidationDiagnostic.classification, { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
    deepEqual(events[0]?.detail, { operation, field, reason, effect: "rejected", ...(ordinal === undefined ? {} : { ordinal }) });
    deepEqual((thrown as { diagnosticRecord: unknown }).diagnosticRecord, events[0]);
  }
  events.length = 0;
  equal(metricPoint({ ...point, value: -1 }, diagnostics).value, -1);
  deepEqual(metricLabels({}, { maxStringLength: 0.5 }, undefined, diagnostics), {});
  equal(traceId("x", diagnostics), "x");
  equal(events.length, 0);
  const facts: unknown[] = [];
  throws(() => metricLabels({ password: "canary" }, {}, (fact) => facts.push(fact), diagnostics), /unsafe/);
  equal(events.length, 0);
  deepEqual(facts, [{ field: "label", reason: "unsafe-name", index: 0 }]);

  const raw = Object.freeze(new Error("PRIVATE_CANARY"));
  const boundaryCases: readonly [() => unknown, string, string, string?][] = [
    [() => monitoringComponent({ get type(): "api" { throw raw; }, name: "api" }, diagnostics), "component", "predicate-invocation", "component-type"],
    [() => healthCheckResult({ ...health, get type(): "readiness" { throw raw; } }, diagnostics), "health-result", "input-projection", "health-type"],
    [() => healthCheckResult({ ...health, get metadata(): never { throw raw; } }, diagnostics), "health-result", "input-projection", "metadata"],
    [() => monitoringMetadata(Object.defineProperty({}, "secret", { enumerable: true, get() { throw raw; } }), diagnostics), "metadata", "metadata-enumeration", "metadata"],
    [() => monitoringMetadata({ nested: new Date() as never }, diagnostics), "metadata", "metadata-copy", "metadata"],
    [() => metricPoint({ ...point, get value(): number { throw raw; } }, diagnostics), "metric-point", "input-projection", "metric-value"],
    [() => metricLabels({}, { get maxStringLength(): number { throw raw; } }, undefined, diagnostics), "metric-labels", "label-options", "max-string-length"],
    [() => metricLabels(Object.defineProperty({}, "secret", { enumerable: true, get() { throw raw; } }), {}, undefined, diagnostics), "metric-labels", "label-enumeration", "labels"],
    [() => monitoringSignalDefinition({ ...signal, get metric(): never { throw raw; } }, diagnostics), "signal-definition", "input-projection", "metric"],
    [() => traceContext({ get traceId(): never { throw raw; }, spanId: spanId("s") }, diagnostics), "trace-context", "input-projection", "trace-id"],
  ];
  for (const [invoke, operation, phase, field] of boundaryCases) {
    events.length = 0;
    throws(invoke);
    equal(events[0]?.code, "core.monitoring.boundary-failed");
    deepEqual(events[0]?.detail, { operation, phase, field, reason: "threw", effect: "result-not-returned" });
  }
  let typeReads = 0, durationReads = 0;
  healthCheckResult({ ...health, get type() { typeReads++; return "readiness" as const; }, get durationMs() { return ++durationReads; } }, diagnostics);
  equal(typeReads, 2); equal(durationReads, 4);
  let diagnosticInputReads = 0;
  metricLabels({}, { get diagnosticDefinitions() { diagnosticInputReads++; throw raw; }, get onDiagnostic() { diagnosticInputReads++; throw raw; } } as never);
  equal(diagnosticInputReads, 0);
  const metadata = { first: 1, second: 2 };
  const entries = [["first", 1], ["second", 2]];
  let entryReads = 0;
  Object.defineProperty(entries, "1", { get() { entryReads++; throw raw; } });
  const nativeEntries = Object.entries;
  events.length = 0;
  try {
    Object.entries = ((value: object) => value === metadata ? entries : nativeEntries(value)) as typeof Object.entries;
    throws(() => monitoringMetadata(metadata, diagnostics), (error) => error === raw);
  } finally { Object.entries = nativeEntries; }
  equal(entryReads, 1);
  deepEqual(events[0]?.detail, { operation: "metadata", phase: "metadata-enumeration", field: "metadata", reason: "threw", effect: "result-not-returned" });
  const snapshotTracer = createInMemoryTracer(diagnostics);
  snapshotTracer.startSpan({ name: traceSpanName("api.snapshot") });
  const nativeMap = Array.prototype.map;
  events.length = 0;
  try {
    Array.prototype.map = function <T, U>(this: T[], callback: (value: T, index: number, array: T[]) => U, thisArg?: unknown): U[] {
      const result = Reflect.apply(nativeMap, this, [callback, thisArg]) as U[];
      if ((this[0] as { name?: unknown } | undefined)?.name === "api.snapshot") throw raw;
      return result;
    };
    throws(() => snapshotTracer.spans(), (error) => error === raw);
  } finally { Array.prototype.map = nativeMap; }
  deepEqual(events[0]?.detail, { operation: "trace-snapshot", phase: "snapshot-copy", reason: "threw", effect: "snapshot-not-returned" });

  const sources = Array.from({ length: 9 }, (_, ordinal) => coreMonitoringValidationDiagnosticRecord({ operation: "signal-definition", field: "signal-intent", reason: "closed-value-rejected", ordinal, effect: "rejected" }));
  const cause = Object.freeze({ diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1), secret: "PRIVATE_CANARY" });
  const own = coreMonitoringBoundaryDiagnosticRecord({ operation: "trace-context", phase: "input-projection", field: "trace-id", reason: "threw", effect: "result-not-returned" });
  events.length = 0; contexts.length = 0;
  const selected = observeCoreMonitoringDiagnostic(diagnostics, own, cause);
  equal(events.length, 10); deepEqual(events.slice(1), sources);
  equal(selected.relatedDiagnosticRecords?.length, 8);
  deepEqual(contexts, Array.from({ length: 10 }, () => ({ operation: "trace-context", phase: "input-projection", field: "trace-id" })));
  equal(JSON.stringify(events).includes("PRIVATE_CANARY"), false);
  events.length = 0;
  throws(() => traceContext({ get traceId(): never { throw cause; }, spanId: spanId("s") }, diagnostics), (error) => error === cause);
  equal(events.length, 10); deepEqual(events.slice(1), sources);
  let old: unknown;
  try { healthCheckName("bad", diagnostics); } catch (error) { old = error; }
  events.length = 0;
  throws(() => healthCheckResult({ ...health, get status(): never { throw old; } }, diagnostics), (error) => error === old);
  deepEqual(events.map(({ code }) => code), ["core.monitoring.boundary-failed", "core.monitoring.validation-rejected"]);
  events.length = 0;
  throws(() => traceContext({ get traceId(): never { throw undefined; }, spanId: spanId("s") }, diagnostics));
  equal(events.length, 1);
  const tracer = createInMemoryTracer(diagnostics);
  events.length = 0;
  throws(() => tracer.startSpan({ name: traceSpanName("api.work"), get parent(): never { throw raw; } }), (error) => error === raw);
  deepEqual(events[0]?.detail, { operation: "trace-start", phase: "parent-projection", field: "parent", reason: "threw", effect: "sequence-advanced-record-not-added" });
  const span = tracer.startSpan({ name: traceSpanName("api.work") });
  equal(span.context.spanId, "span-2");
  events.length = 0;
  throws(() => span.end({ get outcome(): never { throw raw; } }), (error) => error === raw);
  deepEqual(events[0]?.detail, { operation: "trace-end", phase: "end-projection", field: "outcome", reason: "threw", effect: "end-marked-record-not-replaced" });
  span.end({ get outcome(): never { throw new Error("must not read"); } });
  equal(events.length, 1); equal(tracer.spans()[0]?.end, undefined);

  const nativePush = Array.prototype.push;
  events.length = 0;
  try {
    Array.prototype.push = function (...items: unknown[]) {
      const size = Reflect.apply(nativePush, this, items) as number;
      if ((items[0] as { name?: unknown } | undefined)?.name === "api.append") throw raw;
      return size;
    };
    throws(() => tracer.startSpan({ name: traceSpanName("api.append") }), (error) => error === raw);
  } finally { Array.prototype.push = nativePush; }
  deepEqual(events[0]?.detail, { operation: "trace-start", phase: "append", reason: "threw", effect: "sequence-advanced-append-unknown" });
  equal(tracer.spans().length, 2);
  events.length = 0;
  throws(() => tracer.startSpan({ name: traceSpanName("api.parent"), parent: { get traceId(): never { throw raw; }, spanId: spanId("parent") } }), (error) => error === raw);
  equal((events[0]?.detail as { field?: unknown }).field, "parent-trace-id");
  const attributeGetter = Object.defineProperty({}, "secret", { enumerable: true, get() { throw raw; } });
  events.length = 0;
  throws(() => tracer.startSpan({ name: traceSpanName("api.attributes"), attributes: attributeGetter }), (error) => error === raw);
  deepEqual(events[0]?.detail, { operation: "trace-start", phase: "attribute-copy", field: "attributes", reason: "threw", effect: "sequence-advanced-record-not-added" });
  const frozenTracer = createInMemoryTracer(diagnostics);
  let capturedRecord: object | undefined;
  try {
    Array.prototype.push = function (...items: unknown[]) {
      const size = Reflect.apply(nativePush, this, items) as number;
      if ((items[0] as { name?: unknown } | undefined)?.name === "api.frozen") { capturedRecord = items[0] as object; Object.freeze(this); }
      return size;
    };
    const frozenSpan = frozenTracer.startSpan({ name: traceSpanName("api.frozen") });
    events.length = 0;
    throws(() => frozenSpan.end({ outcome: "failed" }), TypeError);
    deepEqual(events[0]?.detail, { operation: "trace-end", phase: "record-replacement", reason: "threw", effect: "end-marked-replacement-unknown" });
    frozenSpan.end({ get outcome(): never { throw raw; } });
    equal(events.length, 1);
  } finally { Array.prototype.push = nativePush; }
  Object.defineProperty(capturedRecord!, "name", { get() { throw raw; } });
  events.length = 0;
  throws(() => frozenTracer.spans(), (error) => error === raw);
  deepEqual(events[0]?.detail, { operation: "trace-snapshot", phase: "snapshot-copy", field: "name", reason: "threw", effect: "snapshot-not-returned" });
  const iterator = { length: 1, [Symbol.iterator]() { throw raw; } };
  events.length = 0;
  throws(() => monitoringSignalDefinition({ ...signal, intents: iterator as never }, diagnostics), (error) => error === raw);
  deepEqual(events[0]?.detail, { operation: "signal-definition", phase: "intent-iteration", field: "signal-intents", reason: "threw", effect: "result-not-returned" });
  const sinkOptions: CoreMonitoringDiagnosticOptions[] = [
    { get onDiagnostic(): never { throw raw; } },
    { onDiagnostic() { throw raw; } },
    { onDiagnostic() { return Promise.reject(raw); } },
    { onDiagnostic() { return { then(_resolve: unknown, reject: (error: unknown) => void) { reject(raw); } }; } },
    { onDiagnostic() { const value = Promise.reject(raw); Object.defineProperty(value, "then", { get() { throw raw; } }); return value; } },
    { get diagnosticDefinitions(): never { throw raw; } },
  ];
  for (const options of sinkOptions) throws(() => healthCheckName("bad", options), /lowercase dot-separated/);
  await new Promise((resolve) => setTimeout(resolve, 0));
}

main()
  .then(() => {
    console.log("packages/core monitoring runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
