import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as core from "@kanbien/core";
import { ChangeMessageVisibilityCommand } from "@aws-sdk/client-sqs";
import { type DiagnosticRecord, type QueueMessage } from "@kanbien/core";
import { createPlatformSqsLambdaBatchHandler, createPlatformSqsWorkerQueue, sqsDiagnosticCatalog,
  sqsConfigurationDiagnosticCatalog, sqsLambdaBatchDiagnosticCatalog, type PlatformSqsLambdaBatchOptions } from "../../src/index";

const source = "arn:aws:sqs:eu-west-1:123456789012:fixture";
const canary = "PRIVATE-BATCH-CANARY";
const envelope = { id: "durable-identity", idempotencyKey: "durable-identity", type: "fixture.cleanup", version: 1,
  enqueuedAt: "2026-11-26T12:00:00.000Z", payload: { outboxEntryId: "durable-identity" } };
const native = (messageId: string, body: unknown = JSON.stringify(envelope)) => ({ messageId, eventSourceARN: source, receiptHandle: "private-receipt", body });
const acknowledged = { disposition: "acknowledge" } as const;

async function main(): Promise<void> {
  deepEqual(sqsDiagnosticCatalog.definitions, [...sqsConfigurationDiagnosticCatalog.definitions, ...sqsLambdaBatchDiagnosticCatalog.definitions]);
  equal(sqsDiagnosticCatalog.definitions.at(-1), sqsLambdaBatchDiagnosticCatalog.definitions[0], "aggregate keeps the same versioned definition object");
  const calls: QueueMessage[] = [], commands: unknown[] = [], records: DiagnosticRecord[] = [];
  const visibility = createPlatformSqsWorkerQueue({ queueUrl: "https://fixture.invalid/queue", waitTimeSeconds: 0, visibilityTimeoutSeconds: 60,
    client: { async send(command) { commands.push(command); return {}; } } });
  let outcome = 0;
  const handler = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 10, visibility,
    onDiagnostic(record) { records.push(record); },
    async processMessage(message) { calls.push(message); outcome++; if (outcome === 2) return { disposition: "retry", delayMs: 1001 }; if (outcome === 3) throw Error(canary); return acknowledged; } });
  deepEqual(await handler.run({ Records: [native("native-a"), native("native-b"), native("native-c"), native("native-invalid", "not-json"), native("native-d")] }),
    { batchItemFailures: [{ itemIdentifier: "native-b" }, { itemIdentifier: "native-c" }, { itemIdentifier: "native-invalid" }] });
  equal(calls.length, 4);
  equal(calls.every(message => message.id === envelope.id && message.idempotencyKey === envelope.id), true);
  equal(commands.length, 1); equal(commands[0] instanceof ChangeMessageVisibilityCommand, true);
  deepEqual((commands[0] as ChangeMessageVisibilityCommand).input, { QueueUrl: "https://fixture.invalid/queue", ReceiptHandle: "private-receipt", VisibilityTimeout: 2 });
  equal(JSON.stringify(records).includes(canary), false); equal(JSON.stringify(records).includes("private-receipt"), false);
  equal(JSON.stringify(records).includes(source), false);
  deepEqual(await handler.run({ Records: [] }), { batchItemFailures: [] });
  deepEqual(await handler.run({ Records: [native("redelivered-native")] }), { batchItemFailures: [] });
  equal(calls.at(-1)!.id, envelope.id);

  for (const event of [null, {}, { Records: null }, { Records: [null] }, { Records: [native("same"), native("same")] },
    { Records: [native("")] }, { Records: [{ body: "private" }] },
    { Records: [{ ...native("foreign"), eventSourceARN: "PRIVATE-OTHER-SCOPE" }] },
    { Records: new Array(1) }, { Records: Array.from({ length: 11 }, (_, index) => native(String(index))) }]) {
    let processed = 0;
    const rejected = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 10,
      async processMessage() { processed++; return acknowledged; } });
    await rejects(rejected.run(event), cause => cause instanceof TypeError && (cause as TypeError & { diagnosticRecord: DiagnosticRecord }).diagnosticRecord.code === "aws-sqs.batch-boundary-observed");
    equal(processed, 0, "an ambiguous batch is rejected before any record effect");
  }
  const seen: string[] = [];
  const stopped = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 3,
    async processMessage(message) { seen.push(String(message.id)); return acknowledged; } });
  let checks = 0;
  const batch = { Records: [native("one"), native("two"), native("three")] };
  deepEqual(await stopped.run(batch, { shouldContinue: () => ++checks < 2 }), { batchItemFailures: [{ itemIdentifier: "two" }, { itemIdentifier: "three" }] });
  equal(seen.length, 1);
  deepEqual(await stopped.run(batch, { shouldContinue: () => { throw Error(canary); } }), { batchItemFailures: [{ itemIdentifier: "one" }, { itemIdentifier: "two" }, { itemIdentifier: "three" }] });
  equal(seen.length, 1);

  for (const value of [undefined, null, "wrong", NaN, Infinity, 0, 11, 1.5]) {
    let processorReads = 0;
    throws(() => createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: value,
      get processMessage() { processorReads++; throw Error("must remain unread"); } } as unknown as PlatformSqsLambdaBatchOptions), TypeError);
    equal(processorReads, 0);
  }
  for (const value of [undefined, null, "", "  ", false]) throws(() => createPlatformSqsLambdaBatchHandler({ expectedSourceArn: value, maximumBatchSize: 1, processMessage: async () => acknowledged } as unknown as PlatformSqsLambdaBatchOptions), TypeError);
  const raw = Object.freeze(new Error(canary));
  throws(() => createPlatformSqsLambdaBatchHandler({ get maximumBatchSize(): never { throw raw; } } as unknown as PlatformSqsLambdaBatchOptions), cause => cause === raw);

  for (const result of [undefined, null, false, {}, { disposition: "unknown" }, { disposition: "retry" },
    { disposition: "retry", delayMs: -1 }, { disposition: "retry", delayMs: Infinity }, { disposition: "retry", delayMs: 43_200_001 }]) {
    let deliveries = 0;
    const unknown = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 1,
      onDiagnostic() { throw raw; }, async processMessage() { deliveries++; return result as never; } });
    deepEqual(await unknown.run({ Records: [native("retained")] }), { batchItemFailures: [{ itemIdentifier: "retained" }] });
    equal(deliveries, 1);
  }
  let visibilityCalls = 0;
  const failedVisibility = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 1,
    visibility: { async release() { visibilityCalls++; throw raw; } },
    onDiagnostic: (() => Promise.reject(raw)) as NonNullable<PlatformSqsLambdaBatchOptions["onDiagnostic"]>,
    async processMessage() { return { disposition: "retry", delayMs: 1000 }; } });
  deepEqual(await failedVisibility.run({ Records: [native("retained")] }), { batchItemFailures: [{ itemIdentifier: "retained" }] });
  equal(visibilityCalls, 1);
  await new Promise<void>(resolve => setImmediate(resolve));

  // The shared decoder is the actual path, not a second envelope representation.
  const codec = require("../../src/messages") as typeof import("../../src/messages");
  const original = codec.decodePlatformQueueMessage;
  try {
    let decoded = 0, processed = 0;
    codec.decodePlatformQueueMessage = () => { decoded++; return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID", defaultMessage: "fixture" } }; };
    const useCodec = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 1, async processMessage() { processed++; return acknowledged; } });
    deepEqual(await useCodec.run({ Records: [native("codec-rejected")] }), { batchItemFailures: [{ itemIdentifier: "codec-rejected" }] });
    equal(decoded, 1); equal(processed, 0);
  } finally { codec.decodePlatformQueueMessage = original; }

  const loaded = (replacements: Partial<typeof core>) => {
    const filename = require.resolve("../../src/lambda-batch"), localRequire = createRequire(filename);
    const fixture = { exports: {} as typeof import("../../src/lambda-batch") };
    new Function("require", "module", "exports", readFileSync(filename, "utf8"))(
      (name: string) => name === "@kanbien/core" ? { ...core, ...replacements } : localRequire(name), fixture, fixture.exports);
    return fixture.exports.createPlatformSqsLambdaBatchHandler;
  };
  for (const create of [() => { throw raw; }, () => undefined, () => ({ ok: true, value: { malformed: canary } })]) {
    const observed: DiagnosticRecord[] = []; let effects = 0;
    const make = loaded({ createDiagnosticRecord: create as never });
    const tested = make({ expectedSourceArn: source, maximumBatchSize: 1, onDiagnostic(record) { observed.push(record); },
      async processMessage() { effects++; throw raw; } });
    deepEqual(await tested.run({ Records: [native("failed-builder")] }), { batchItemFailures: [{ itemIdentifier: "failed-builder" }] });
    equal(effects, 1); equal(observed.some(record => record.code === "core.diagnostics.processing-failed"), true);
    equal(JSON.stringify(observed).includes(canary), false);
  }
  const definitionReports: DiagnosticRecord[] = [];
  const unavailableDefinitions = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: source, maximumBatchSize: 1,
    get diagnosticDefinitions(): never { throw raw; }, onDiagnostic(record) { definitionReports.push(record); }, async processMessage() { throw raw; } });
  deepEqual(await unavailableDefinitions.run({ Records: [native("definition-failed")] }), { batchItemFailures: [{ itemIdentifier: "definition-failed" }] });
  equal(definitionReports.some(record => record.code === "core.diagnostics.processing-failed"), true);
  let checkedReads = 0;
  const changedMaximum = loaded({ numberConfigValue: ((config: core.ConfigSource, key: string) => {
    checkedReads++; return key === "maximum-batch-size" ? { ok: true, value: 1 } : core.numberConfigValue(config, key);
  }) as typeof core.numberConfigValue });
  const limited = changedMaximum({ expectedSourceArn: source, maximumBatchSize: 10, async processMessage() { throw Error("must not run"); } });
  await rejects(limited.run(batch), TypeError); equal(checkedReads, 1, "batch limit uses the checked Core value, not the submitted setting");
  console.log("Managed batch validation, partial settlement, identity, visibility and diagnostic safety tests passed.");
}
void main().catch(error => { console.error(error); process.exitCode = 1; });
