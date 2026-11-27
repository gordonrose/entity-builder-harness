import {
  captureDiagnosticRecord, requireDiagnosticRecord, createDiagnosticRecord, defineDiagnostic,
  deliverDiagnosticRecords, selectDiagnosticEvidenceWithReport, diagnosticProcessingRecord, coreDiagnosticCatalog,
  numberConfigValue, stringConfigValue, type ConfigSource, type CoreQueueDiagnosticOptions,
  type DiagnosticRecord, type DiagnosticDefinition, type QueueMessage,
} from "@kanbien/core";
import { decodePlatformQueueMessage } from "./messages";
import type { PlatformSqsWorkerQueue } from "./worker";
import { sqsVisibilityTimeoutConstraint } from "./configuration/index";

export const sqsLambdaBatchDiagnostic = defineDiagnostic({ code: "aws-sqs.batch-boundary-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["maximum-batch-size", "expected-source", "processor", "event", "records", "record", "message-id", "source", "body", "receipt-handle", "continuation", "processor-result", "retry-delay", "visibility"] },
    reason: { type: "enum", values: ["missing", "wrong-type", "empty", "not-finite", "not-integer", "out-of-range", "duplicate", "mismatch", "rejected", "threw"] },
    effect: { type: "enum", values: ["not-started", "record-not-acknowledged", "remaining-not-started"] },
  } },
} as const);
export const sqsLambdaBatchDiagnosticCatalog = { owner: "aws-sqs", definitions: [sqsLambdaBatchDiagnostic] } as const;
type Detail = NonNullable<typeof sqsLambdaBatchDiagnostic.__detail>;

export type PlatformSqsLambdaRecordDisposition =
  | { readonly disposition: "acknowledge" }
  | { readonly disposition: "retry"; readonly delayMs?: number };
export interface PlatformSqsLambdaBatchOptions extends CoreQueueDiagnosticOptions {
  readonly expectedSourceArn: string;
  readonly maximumBatchSize: number;
  readonly processMessage: (message: QueueMessage) => Promise<PlatformSqsLambdaRecordDisposition>;
  /** Only visibility changes: managed delivery owns receive and acknowledgement. */
  readonly visibility?: Pick<PlatformSqsWorkerQueue, "release">;
}
export interface PlatformSqsLambdaBatchResponse { readonly batchItemFailures: readonly { readonly itemIdentifier: string }[]; }
export interface PlatformSqsLambdaBatchHandler {
  run(event: unknown, invocation?: { readonly shouldContinue?: () => boolean }): Promise<PlatformSqsLambdaBatchResponse>;
}

/** One bounded sequential batch. Native IDs identify acknowledgements, never durable work. */
export function createPlatformSqsLambdaBatchHandler(options: PlatformSqsLambdaBatchOptions): PlatformSqsLambdaBatchHandler {
  function observe(detail: Detail, cause?: unknown): DiagnosticRecord {
    const definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...sqsLambdaBatchDiagnosticCatalog.definitions];
    const own = requireDiagnosticRecord(definitions, captureDiagnosticRecord(() => {
      const checked = createDiagnosticRecord(sqsLambdaBatchDiagnostic, detail);
      return checked.ok ? checked.value : undefined;
    }));
    const notices: DiagnosticRecord[] = [];
    let selected = definitions;
    try { selected = [...definitions, ...(options.diagnosticDefinitions ?? [])]; }
    catch { notices.push(diagnosticProcessingRecord("definition-selection-failed")); }
    const evidence = selectDiagnosticEvidenceWithReport(selected, cause, record => notices.push(record));
    deliverDiagnosticRecords([own, ...(evidence.diagnosticRecord === undefined ? [] : [evidence.diagnosticRecord]),
      ...(evidence.relatedDiagnosticRecords ?? []), ...notices], record => options.onDiagnostic?.(record, { operation: "receive", boundary: "response" }));
    return own;
  }
  function reject(field: Detail["field"], reason: Detail["reason"]): never {
    throw Object.assign(new TypeError("Managed queue batch was rejected before execution."), {
      diagnosticRecord: observe({ field, reason, effect: "not-started" }),
    });
  }
  function read<T>(field: Detail["field"], action: () => T): T {
    try { return action(); } catch (cause) { observe({ field, reason: "threw", effect: "not-started" }, cause); throw cause; }
  }
  const suppliedMaximum = read("maximum-batch-size", () => options.maximumBatchSize);
  const maximum = numberConfigValue({ get: () => suppliedMaximum } as ConfigSource, "maximum-batch-size");
  if (!maximum.ok) reject("maximum-batch-size", suppliedMaximum === undefined ? "missing" : typeof suppliedMaximum !== "number" ? "wrong-type" : "not-finite");
  if (!Number.isInteger(maximum.value)) reject("maximum-batch-size", "not-integer");
  if (maximum.value < 1 || maximum.value > 10) reject("maximum-batch-size", "out-of-range");
  const suppliedSource = read("expected-source", () => options.expectedSourceArn);
  const source = stringConfigValue({ get: () => suppliedSource } as ConfigSource, "expected-source");
  if (!source.ok) reject("expected-source", suppliedSource === undefined ? "missing" : "wrong-type");
  if (source.value.trim().length === 0) reject("expected-source", "empty");
  const processMessage = read("processor", () => options.processMessage);
  if (typeof processMessage !== "function") reject("processor", processMessage === undefined ? "missing" : "wrong-type");
  const visibility = read("visibility", () => options.visibility);

  return { async run(event, invocation = {}) {
    // Validate all response identities before effects; duplicates are ambiguous
    // in a partial-failure response and therefore reject the entire invocation.
    if (!record(event)) reject("event", "wrong-type");
    const raw = read("records", () => event.Records);
    if (!Array.isArray(raw)) reject("records", raw === undefined ? "missing" : "wrong-type");
    if (raw.length > maximum.value) reject("records", "out-of-range");
    const seen = new Set<string>();
    const entries = Array.from(raw, value => {
      if (!record(value)) reject("record", "wrong-type");
      const id = read("message-id", () => value.messageId);
      if (typeof id !== "string") reject("message-id", id === undefined ? "missing" : "wrong-type");
      if (id.length === 0) reject("message-id", "empty");
      if (seen.has(id)) reject("message-id", "duplicate");
      seen.add(id);
      const nativeSource = read("source", () => value.eventSourceARN);
      if (nativeSource !== source.value) reject("source", nativeSource === undefined ? "missing" : typeof nativeSource !== "string" ? "wrong-type" : "mismatch");
      return { id, value };
    });
    const failed: { itemIdentifier: string }[] = [];
    for (let index = 0; index < entries.length; index++) {
      const entry = entries[index]!;
      let shouldContinue: boolean;
      try { const continuation = invocation.shouldContinue; shouldContinue = continuation === undefined || continuation() === true; }
      catch (cause) {
        observe({ field: "continuation", reason: "threw", effect: "remaining-not-started" }, cause);
        failed.push(...entries.slice(index).map(item => ({ itemIdentifier: item.id })));
        break;
      }
      if (!shouldContinue) {
        failed.push(...entries.slice(index).map(item => ({ itemIdentifier: item.id })));
        break;
      }
      let field: Detail["field"] = "body";
      try {
        const body = entry.value.body;
        if (typeof body !== "string") {
          observe({ field, reason: body === undefined ? "missing" : "wrong-type", effect: "record-not-acknowledged" });
          failed.push({ itemIdentifier: entry.id }); continue;
        }
        const decoded = decodePlatformQueueMessage(body, options);
        if (!decoded.ok) { observe({ field, reason: "rejected", effect: "record-not-acknowledged" }, decoded.error); failed.push({ itemIdentifier: entry.id }); continue; }
        field = "processor";
        const result = await processMessage(decoded.value);
        field = "processor-result";
        if (result?.disposition === "acknowledge") continue;
        if (result?.disposition !== "retry") {
          observe({ field, reason: "rejected", effect: "record-not-acknowledged" }); failed.push({ itemIdentifier: entry.id }); continue;
        }
        failed.push({ itemIdentifier: entry.id });
        field = "retry-delay";
        const supplied = result.delayMs;
        if (supplied !== undefined) {
          const checked = numberConfigValue({ get: () => supplied } as ConfigSource, "retry-delay");
          if (!checked.ok || checked.value < sqsVisibilityTimeoutConstraint.minimum * 1000 || checked.value > sqsVisibilityTimeoutConstraint.maximum * 1000) {
            observe({ field, reason: !checked.ok ? typeof supplied === "number" ? "not-finite" : "wrong-type" : "out-of-range", effect: "record-not-acknowledged" }); continue;
          }
          field = "receipt-handle";
          const receipt = entry.value.receiptHandle;
          if (typeof receipt !== "string" || !receipt.length) {
            observe({ field, reason: receipt === undefined ? "missing" : typeof receipt !== "string" ? "wrong-type" : "empty", effect: "record-not-acknowledged" }); continue;
          }
          field = "visibility";
          if (visibility === undefined) { observe({ field, reason: "missing", effect: "record-not-acknowledged" }); continue; }
          await visibility.release(receipt, Math.ceil(checked.value / 1000));
        }
      } catch (cause) {
        observe({ field, reason: "threw", effect: "record-not-acknowledged" }, cause);
        if (!failed.some(item => item.itemIdentifier === entry.id)) failed.push({ itemIdentifier: entry.id });
      }
    }
    return { batchItemFailures: failed };
  } };
}

function record(value: unknown): value is Record<string, unknown> { return typeof value === "object" && value !== null && !Array.isArray(value); }
