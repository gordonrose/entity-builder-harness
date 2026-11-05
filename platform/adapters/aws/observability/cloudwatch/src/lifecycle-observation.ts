import { PeriodicExportingMetricReader, TimeoutError, type CollectionResult, type PeriodicExportingMetricReaderOptions,
  type PushMetricExporter } from "@opentelemetry/sdk-metrics";
import { capturePlatformMetricDiagnostic, metricCollectionIssuesRecord, metricCollectionFailureRecord, metricExportFailureRecord, metricLifecycleFailureRecord,
  reportPlatformObservationBoundary, reportPlatformObservationSources,
  type PlatformMetricLifecycleDiagnosticBinding, type PlatformObservationDiagnostics, type PlatformObservationBoundaryDetail } from "@kanbien/platform-observability";

const intrinsicPromiseThen = Promise.prototype.then;

/** Public collection override only: SDK scheduling, producer selection and data remain owned by the SDK. */
export class ObservedPeriodicMetricReader extends PeriodicExportingMetricReader {
  private readonly diagnostics: PlatformMetricLifecycleDiagnosticBinding | undefined;
  private readonly observations: PlatformObservationDiagnostics | undefined;
  constructor(options: PeriodicExportingMetricReaderOptions, diagnostics?: PlatformMetricLifecycleDiagnosticBinding, observations?: PlatformObservationDiagnostics) {
    super(options);
    this.diagnostics = diagnostics; this.observations = metricObservationContext(observations, "runtime");
  }
  override async collect(options?: Parameters<PeriodicExportingMetricReader["collect"]>[0]): Promise<CollectionResult> {
    let result: CollectionResult;
    try { result = await super.collect(options); }
    catch (error) {
      reportPlatformObservationBoundary(this.observations, { operation: "metric-collection", phase: "collection", reason: "rejected", effect: "unknown" }, error);
      safely(() => this.diagnostics?.report(capturePlatformMetricDiagnostic(() => metricCollectionFailureRecord(failureReason(error))), "collection"));
      throw error;
    }
    // Reporting/inspection failures must not become SDK collection failures.
    try {
      const errors = result.errors, count = errors.length;
      if (count > 0) {
        safely(() => this.diagnostics?.report(capturePlatformMetricDiagnostic(() => metricCollectionIssuesRecord(count)), "collection"));
        // Public returned errors only; bounded own data, never accessors/iterators/private causes.
        if (this.observations?.reporter !== undefined && Number.isSafeInteger(count) && Array.isArray(errors)) {
          for (let index = 0; index < Math.min(count, 8); index++) {
            const item = Object.getOwnPropertyDescriptor(errors, String(index));
            if (item !== undefined && "value" in item) reportPlatformObservationSources(this.observations, item.value);
          }
        }
      }
    } catch (error) {
      reportPlatformObservationBoundary(this.observations, { operation: "metric-collection", phase: "result-projection", field: "result", reason: "threw", effect: "observation-incomplete" }, error);
    }
    return result;
  }
}

/** Decorate only declared public operations, preserving exporter and callback receivers. */
export function observeMetricExporter(exporter: PushMetricExporter, diagnostics?: PlatformMetricLifecycleDiagnosticBinding, observations?: PlatformObservationDiagnostics,
  construction?: CloudWatchConstructionObservation): PushMetricExporter {
  const runtimeObservations = metricObservationContext(observations, "runtime");
  const observed: PushMetricExporter = {
    export(data, callback) {
      let callbackThrew = false;
      let phase: "sink-selection" | "export" = "sink-selection";
      try {
        return exporter.export(data, (phase = "export", function(this: unknown, result) {
          // SDK ExportResultCode.SUCCESS is 0; no transitive @opentelemetry/core import.
          try {
            if (result.code !== 0) {
              safely(() => diagnostics?.report(capturePlatformMetricDiagnostic(() => metricExportFailureRecord("callback-failed")), "export"));
              if (observations?.reporter !== undefined) {
                const error = Object.getOwnPropertyDescriptor(result, "error");
                if (error !== undefined && "value" in error) reportPlatformObservationSources(runtimeObservations, error.value);
              }
            }
          } catch (error) {
            reportPlatformObservationBoundary(runtimeObservations, { operation: "metric-export", phase: "result-projection", field: "result", reason: "threw", effect: "observation-incomplete" }, error);
          }
          try { return Reflect.apply(callback, this, [result]); }
          catch (error) {
            callbackThrew = true;
            reportPlatformObservationBoundary(runtimeObservations, { operation: "metric-export", phase: "sink-invocation", field: "result", reason: "threw", effect: "unknown" }, error);
            throw error;
          }
        }));
      } catch (error) {
        if (!callbackThrew) {
          reportPlatformObservationBoundary(runtimeObservations, { operation: "metric-export", phase, reason: "threw", effect: "unknown" }, error);
          safely(() => diagnostics?.report(capturePlatformMetricDiagnostic(() => metricExportFailureRecord("invocation-threw")), "export"));
        }
        throw error;
      }
    },
    forceFlush: () => observeMetricLifecycle(() => exporter.forceFlush(), "flush", "exporter", diagnostics, observations),
    shutdown: () => observeMetricLifecycle(() => exporter.shutdown(), "shutdown", "exporter", diagnostics, observations),
  };
  // Absence is significant: the SDK supplies defaults when a selector is absent.
  const current = construction ?? new CloudWatchConstructionObservation(observations);
  const selectors = (): void => {
    const aggregation = current.at("sink-selection", "aggregation-selector", () => exporter.selectAggregation),
      temporality = current.at("sink-selection", "temporality-selector", () => exporter.selectAggregationTemporality);
    if (aggregation !== undefined) observed.selectAggregation = current.at("sink-selection", "aggregation-selector", () => aggregation.bind((current.location("sink-invocation", "aggregation-selector"), exporter)));
    if (temporality !== undefined) observed.selectAggregationTemporality = current.at("sink-selection", "temporality-selector", () => temporality.bind((current.location("sink-invocation", "temporality-selector"), exporter)));
  };
  if (construction === undefined) current.run(selectors); else selectors();
  return observed;
}

/** Observe the existing promise once; failure is rethrown unchanged, never retried or cancelled. */
export function observeMetricLifecycle(operation: () => Promise<void>, phase: "flush" | "shutdown", boundary: "exporter" | "runtime",
  diagnostics?: PlatformMetricLifecycleDiagnosticBinding, observations?: PlatformObservationDiagnostics,
  invocationLocation?: () => Pick<PlatformObservationBoundaryDetail, "phase" | "field"> | undefined): Promise<void> {
  const scopedObservations = metricObservationContext(observations, phase === "shutdown" ? "shutdown" : "runtime");
  let pending: Promise<void>;
  try { pending = operation(); }
  catch (error) { reportFailure(error, "invocation-threw"); throw error; }
  const rejected = (error: unknown): never => { reportFailure(error); throw error; };
  try { return Reflect.apply(intrinsicPromiseThen, pending, [undefined, rejected]) as Promise<void>; }
  catch {
    // Standard thenables use assimilation. Malicious native constructor/species
    // hooks remain outside portable isolation guarantees, as in local recording.
    try { return Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [undefined, rejected]) as Promise<void>; }
    catch (error) {
      reportPlatformObservationBoundary(scopedObservations, { operation: phase === "flush" ? "metric-flush" : "metric-shutdown", phase: "sink-completion", reason: "threw", effect: "unknown" }, error);
      throw error;
    }
  }
  function reportFailure(error: unknown, reason?: "invocation-threw"): void {
    let location: Pick<PlatformObservationBoundaryDetail, "phase" | "field"> | undefined;
    try { if (reason !== undefined) location = invocationLocation?.(); } catch { /* Optional location cannot replace original failure. */ }
    reportPlatformObservationBoundary(scopedObservations, { operation: phase === "flush" ? "metric-flush" : "metric-shutdown", phase: location?.phase ?? phase, ...(location?.field === undefined ? {} : { field: location.field }), reason: reason === undefined ? "rejected" : "threw", effect: location === undefined ? "unknown" : "not-attempted" }, error);
    safely(() => diagnostics?.report(capturePlatformMetricDiagnostic(() => metricLifecycleFailureRecord(phase, boundary, reason ?? failureReason(error))), phase));
  }
}

function failureReason(error: unknown): "sdk-timeout" | "rejected" {
  try { return error instanceof TimeoutError ? "sdk-timeout" : "rejected"; }
  catch { return "rejected"; }
}
function safely(operation: () => unknown): void {
  try {
    const returned = operation();
    if (returned === undefined) return;
    try { Reflect.apply(intrinsicPromiseThen, returned, [undefined, () => undefined]); }
    catch { Reflect.apply(intrinsicPromiseThen, Promise.resolve(returned), [undefined, () => undefined]); }
  } catch { /* No report can change the delegated outcome. */ }
}

/** Process phases are local to this returned binding, never mutable global request state. */
export function metricObservationContext(observations: PlatformObservationDiagnostics | undefined, stage: "runtime" | "shutdown"): PlatformObservationDiagnostics | undefined {
  try {
    if (observations === undefined) return undefined;
    const context = observations.context;
    // Preserve accessor/nonplain provenance for the shared validator, never invoke context getters.
    const fields = Object.getOwnPropertyDescriptors(context);
    return Object.create(Object.getPrototypeOf(observations), { ...Object.getOwnPropertyDescriptors(observations),
      context: { value: Object.create(Object.getPrototypeOf(context), { ...fields, stage: { value: stage, enumerable: true } }), enumerable: true } });
  }
  catch { return undefined; }
}

/** One current construction call, with nested read locations restored only on success. */
export class CloudWatchConstructionObservation {
  private phase: PlatformObservationBoundaryDetail["phase"] = "runtime-construction";
  private field: PlatformObservationBoundaryDetail["field"];
  private effect: PlatformObservationBoundaryDetail["effect"] = "unknown";
  constructor(private readonly observations: PlatformObservationDiagnostics | undefined) {}
  location(phase: PlatformObservationBoundaryDetail["phase"], field: PlatformObservationBoundaryDetail["field"]): void { this.phase = phase; this.field = field; }
  at<T>(phase: PlatformObservationBoundaryDetail["phase"], field: PlatformObservationBoundaryDetail["field"], action: () => T,
    effect: PlatformObservationBoundaryDetail["effect"] = this.effect): T {
    const previous = { phase: this.phase, field: this.field, effect: this.effect };
    this.location(phase, field); this.effect = effect;
    const result = action();
    this.phase = previous.phase; this.field = previous.field; this.effect = previous.effect;
    return result;
  }
  run<T>(action: () => T): T {
    try { return action(); }
    catch (error) {
      reportPlatformObservationBoundary(this.observations, { operation: "metric-runtime-construction", phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason: "threw", effect: this.effect }, error);
      throw error;
    }
  }
}
