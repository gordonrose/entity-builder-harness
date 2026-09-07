import type { SpanId, TraceId, TraceSpanName } from "./identifiers";
import { spanId, traceId } from "./identifiers";

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
}): TraceContext {
  return {
    traceId: input.traceId,
    spanId: input.spanId,
    ...(input.parentSpanId === undefined ? {} : { parentSpanId: input.parentSpanId }),
  };
}

export function createInMemoryTracer(): InMemoryTracer {
  const records: InMemoryTraceSpanRecord[] = [];
  let sequence = 0;

  return {
    startSpan: (input) => {
      sequence += 1;
      const context = traceContext({
        traceId: input.parent?.traceId ?? traceId(`trace-${sequence}`),
        spanId: spanId(`span-${sequence}`),
        ...(input.parent === undefined ? {} : { parentSpanId: input.parent.spanId }),
      });
      const record: InMemoryTraceSpanRecord = {
        name: input.name,
        context: copyTraceContext(context),
        ...(input.attributes === undefined ? {} : { attributes: copyTraceAttributes(input.attributes) }),
      };
      records.push(record);
      let ended = false;

      return {
        context: copyTraceContext(context),
        end: (input) => {
          if (ended) {
            return;
          }
          ended = true;
          const index = records.indexOf(record);
          records[index] = {
            ...record,
            end: {
              outcome: input.outcome,
              ...(input.attributes === undefined ? {} : { attributes: copyTraceAttributes(input.attributes) }),
            },
          };
        },
      };
    },
    spans: () => records.map(copyTraceSpanRecord),
  };
}

function copyTraceSpanRecord(record: InMemoryTraceSpanRecord): InMemoryTraceSpanRecord {
  return {
    name: record.name,
    context: copyTraceContext(record.context),
    ...(record.attributes === undefined ? {} : { attributes: copyTraceAttributes(record.attributes) }),
    ...(record.end === undefined
      ? {}
      : {
          end: {
            outcome: record.end.outcome,
            ...(record.end.attributes === undefined ? {} : { attributes: copyTraceAttributes(record.end.attributes) }),
          },
        }),
  };
}

function copyTraceContext(context: TraceContext): TraceContext {
  return {
    traceId: context.traceId,
    spanId: context.spanId,
    ...(context.parentSpanId === undefined ? {} : { parentSpanId: context.parentSpanId }),
  };
}

function copyTraceAttributes(attributes: TraceAttributes): TraceAttributes {
  return { ...attributes };
}
