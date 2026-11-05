import type { SpanId, TraceId, TraceSpanName } from "./identifiers";
import { spanId, traceId } from "./identifiers";
import type { CoreMonitoringBoundaryDetail, CoreMonitoringDiagnosticOptions } from "./boundary-diagnostics";
import { MonitoringObservation } from "./observations";

export const traceSpanOutcomes = ["succeeded", "rejected", "failed", "cancelled"] as const;
export type TraceSpanOutcome = (typeof traceSpanOutcomes)[number];

export type TraceAttributeValue = string | number | boolean;
export type TraceAttributes = Readonly<Record<string, TraceAttributeValue>>;

export interface TraceContext {
  readonly traceId: TraceId;
  readonly spanId: SpanId;
  readonly parentSpanId?: SpanId;
}

export interface TraceSpanStartInput {
  readonly name: TraceSpanName;
  readonly parent?: TraceContext;
  readonly attributes?: TraceAttributes;
}

export interface TraceSpanEndInput {
  readonly outcome: TraceSpanOutcome;
  readonly attributes?: TraceAttributes;
}

export interface TraceSpan {
  readonly context: TraceContext;
  end(input: TraceSpanEndInput): void;
}

export interface Tracer {
  startSpan(input: TraceSpanStartInput): TraceSpan;
}

export interface InMemoryTraceSpanRecord {
  readonly name: TraceSpanName;
  readonly context: TraceContext;
  readonly attributes?: TraceAttributes;
  readonly end?: TraceSpanEndInput;
}

export interface InMemoryTracer extends Tracer {
  spans(): readonly InMemoryTraceSpanRecord[];
}

export const noopTracer: Tracer = {
  startSpan: (input) => ({
    context: traceContext({
      traceId: input.parent?.traceId ?? traceId("noop-trace"),
      spanId: spanId("noop-span"),
      ...(input.parent === undefined ? {} : { parentSpanId: input.parent.spanId }),
    }),
    end: () => undefined,
  }),
};

export function traceContext(input: {
  readonly traceId: TraceId;
  readonly spanId: SpanId;
  readonly parentSpanId?: SpanId;
}, diagnostics?: CoreMonitoringDiagnosticOptions): TraceContext {
  const observation = new MonitoringObservation("trace-context", diagnostics);
  return observation.run(() => copyTraceContext(input, observation, "input-projection"));
}

export function createInMemoryTracer(diagnostics?: CoreMonitoringDiagnosticOptions): InMemoryTracer {
  const records: InMemoryTraceSpanRecord[] = [];
  let sequence = 0;

  return {
    startSpan: (input) => {
      sequence += 1;
      const observation = new MonitoringObservation("trace-start", diagnostics);
      observation.effectIs("sequence-advanced-record-not-added");
      return observation.run(() => {
      const context = copyTraceContext({
        traceId: (() => {
          const parent = observation.at("parent-projection", "parent", () => input.parent);
          return observation.at("parent-projection", "parent-trace-id", () => parent?.traceId) ?? traceId(`trace-${sequence}`);
        })(),
        spanId: spanId(`span-${sequence}`),
        ...(observation.at("parent-projection", "parent", () => input.parent) === undefined ? {} : { parentSpanId: (() => {
          const parent = observation.at("parent-projection", "parent", () => input.parent);
          return observation.at("parent-projection", "parent-span-id", () => parent!.spanId);
        })() }),
      }, observation);
      const record: InMemoryTraceSpanRecord = {
        name: observation.at("input-projection", "name", () => input.name),
        context: copyTraceContext(context, observation),
        ...(observation.at("input-projection", "attributes", () => input.attributes) === undefined ? {} : { attributes: copyTraceAttributes(observation.at("input-projection", "attributes", () => input.attributes)!, observation) }),
      };
      observation.effectIs("sequence-advanced-append-unknown");
      observation.at("append", undefined, () => records.push(record));
      observation.effectIs("record-added-span-not-returned");
      let ended = false;

      return {
        context: copyTraceContext(context, observation, "return-context"),
        end: (input) => {
          if (ended) {
            return;
          }
          ended = true;
          const ending = new MonitoringObservation("trace-end", diagnostics);
          ending.effectIs("end-marked-record-not-replaced");
          ending.run(() => {
          const index = ending.at("record-lookup", undefined, () => records.indexOf(record));
          const replacement = {
            ...record,
            end: {
              outcome: ending.at("end-projection", "outcome", () => input.outcome),
              ...(ending.at("end-projection", "attributes", () => input.attributes) === undefined ? {} : { attributes: copyTraceAttributes(ending.at("end-projection", "attributes", () => input.attributes)!, ending) }),
            },
          };
          ending.effectIs("end-marked-replacement-unknown");
          ending.at("record-replacement", undefined, () => { records[index] = replacement; });
          });
        },
      };
      });
    },
    spans: () => {
      const observation = new MonitoringObservation("trace-snapshot", diagnostics);
      observation.effectIs("snapshot-not-returned");
      return observation.run(() => observation.at("snapshot-copy", undefined, () => records.map((record) => {
        const copied = copyTraceSpanRecord(record, observation);
        return observation.at("snapshot-copy", undefined, () => copied);
      })));
    },
  };
}

function copyTraceSpanRecord(record: InMemoryTraceSpanRecord, observation: MonitoringObservation): InMemoryTraceSpanRecord {
  return {
    name: observation.at("snapshot-copy", "name", () => record.name),
    context: copyTraceContext(observation.at("snapshot-copy", "context", () => record.context), observation),
    ...(observation.at("snapshot-copy", "attributes", () => record.attributes) === undefined ? {} : { attributes: copyTraceAttributes(observation.at("snapshot-copy", "attributes", () => record.attributes)!, observation) }),
    ...(observation.at("snapshot-copy", "end", () => record.end) === undefined
      ? {}
      : {
          end: {
            outcome: observation.at("snapshot-copy", "outcome", () => record.end!.outcome),
            ...(observation.at("snapshot-copy", "attributes", () => record.end!.attributes) === undefined ? {} : { attributes: copyTraceAttributes(observation.at("snapshot-copy", "attributes", () => record.end!.attributes)!, observation) }),
          },
        }),
  };
}

function copyTraceContext(context: TraceContext, observation: MonitoringObservation, phase: CoreMonitoringBoundaryDetail["phase"] = "context-copy"): TraceContext {
  return {
    traceId: observation.at(phase, "trace-id", () => context.traceId),
    spanId: observation.at(phase, "span-id", () => context.spanId),
    ...(observation.at(phase, "parent-span-id", () => context.parentSpanId) === undefined ? {} : { parentSpanId: observation.at(phase, "parent-span-id", () => context.parentSpanId) }),
  };
}

function copyTraceAttributes(attributes: TraceAttributes, observation: MonitoringObservation): TraceAttributes {
  return observation.at("attribute-copy", "attributes", () => ({ ...attributes }));
}
