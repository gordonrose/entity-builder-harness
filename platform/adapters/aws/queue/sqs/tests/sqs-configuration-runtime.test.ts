import { deepEqual, equal, throws } from "node:assert/strict";
import { withDiagnosticDeliverySuppressed } from "../../../../../../packages/core/tests/diagnostic-delivery-fixture";
import * as sdk from "@aws-sdk/client-sqs";
import { ReceiveMessageCommand, SendMessageCommand } from "@aws-sdk/client-sqs";
import { recordConfigSource, validateConfigRequirements, defineDiagnostic, createDiagnosticRecord, type DiagnosticRecord,
  type ConfigSource, queueMessage, queueMessageId, queueMessageType, isoDateTime } from "@kanbien/core";
import { loadPlatformConfiguration } from "../../../../../config/src/index";
import { sqsSenderRequirements, sqsWorkerRequirements, sqsReceiveWaitConstraint, sqsVisibilityTimeoutConstraint,
  validateSqsSenderConfiguration, validateSqsWorkerConfiguration, assembleSqsWorkerConfiguration,
  createAwsSdkPlatformSqsQueueFromConfiguration, createAwsSdkPlatformSqsWorkerQueueFromConfiguration,
  createAwsSdkPlatformSqsWorkerQueueFromEnv, createPlatformSqsWorkerQueue,
  sqsConfigurationDiagnosticCatalog, type SqsConfigurationCheck } from "../src/index";

const valid = { "queue.address": "https://sqs.example.invalid/fixture", "queue.region": "fixture-region",
  "queue.receive-wait": "20", "queue.visibility-timeout": "120" };
const canary = "PRIVATE_CONFIGURATION_CANARY";
const packet = (role: "sender" | "worker", issues: readonly { setting: string; reason: string }[]) => ({
  schema: "core/diagnostic-record/v1", code: `aws-sqs.${role}-configuration-invalid`, definitionVersion: 1, detail: { issues },
});
const fake = sdk as unknown as { SQSClient: typeof sdk.SQSClient };
const originalClient = sdk.SQSClient;
const constructions: unknown[] = [], commands: unknown[] = [];
class FakeClient {
  constructor(options: unknown) { constructions.push(options); }
  async send(command: unknown) { commands.push(command); return { Messages: [] }; }
}
async function main() {
  fake.SQSClient = FakeClient as unknown as typeof sdk.SQSClient;
  try {
    withDiagnosticDeliverySuppressed(attempted => {
      let delivered = 0;
      equal(validateSqsWorkerConfiguration(recordConfigSource({}), undefined, { onDiagnostic() { delivered++; } }).ok, false);
      equal(delivered, 0, "actual SQS configuration reporting delegates to Core delivery");
      deepEqual(attempted, [packet("worker", sqsWorkerRequirements.map(item => ({ setting: item.setting, reason: "missing" })))]);
    });
    equal(sqsConfigurationDiagnosticCatalog.definitions.length, 4);
    equal(Object.isFrozen(sqsReceiveWaitConstraint), true); equal(Object.isFrozen(sqsWorkerRequirements), true);
    equal(sqsWorkerRequirements[2].rule, sqsReceiveWaitConstraint);
    equal(sqsWorkerRequirements[3].rule, sqsVisibilityTimeoutConstraint);
    for (const role of ["sender", "worker"] as const) {
      const factory = role === "sender" ? createAwsSdkPlatformSqsQueueFromConfiguration : createAwsSdkPlatformSqsWorkerQueueFromConfiguration;
      const requirements = role === "sender" ? sqsSenderRequirements : sqsWorkerRequirements;
      for (const requirement of requirements) {
        const cases: readonly (readonly [unknown, string])[] = [[undefined, "missing"], [false, "wrong-type"], [" \t", "blank"], [" value ", "surrounding-whitespace"],
          ...(requirement.rule.kind === "integer" ? [[canary, "invalid-integer"], [String(requirement.rule.maximum + 1), "out-of-range"], ["-1", "out-of-range"]] as const : [])];
        for (const [value, reason] of cases) {
          constructions.length = 0;
          const observed: DiagnosticRecord[] = [];
          const result = factory(recordConfigSource({ ...valid, [requirement.setting]: value as never }), { onDiagnostic(record, context) {
            observed.push(record); deepEqual(context, { operation: "client-initialization", boundary: "selection" });
          } });
          equal(result.ok, false); equal(constructions.length, 0, "every content rejection precedes SDK construction");
          if (!result.ok) { deepEqual(result.error, { code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID", defaultMessage: "AWS SQS configuration is invalid.", diagnosticRecord: packet(role, [{ setting: requirement.setting, reason }]) });
            deepEqual(observed, [result.error.diagnosticRecord]); equal(JSON.stringify(result).includes(canary), false); }
        }
      }
      const all = factory(recordConfigSource({})); equal(all.ok, false);
      if (!all.ok) deepEqual(all.error.diagnosticRecord, packet(role, requirements.map(item => ({ setting: item.setting, reason: "missing" }))));
    }
    for (const [wait, visibility, accepted] of [["0", "0", true], ["20", "43200", true], ["21", "120", false], ["20", "43201", false], ["0x10", "120", false], ["1e1", "120", false], ["1.0", "120", false]] as const)
      equal(validateSqsWorkerConfiguration(recordConfigSource({ ...valid, "queue.receive-wait": wait, "queue.visibility-timeout": visibility })).ok, accepted);
    let ignored = 0;
    const senderSource = { get(name: string) { if (name === "queue.receive-wait" || name === "queue.visibility-timeout") { ignored++; throw Error(canary); } return valid[name as keyof typeof valid]; } };
    equal(validateSqsSenderConfiguration(senderSource).ok, true); equal(ignored, 0);
    const checked: SqsConfigurationCheck = (source, requirements) => {
      const result = validateConfigRequirements(source, requirements);
      return result.ok ? { ok: true, value: { ...result.value, "queue.address": "checked-address", "queue.region": "checked-region",
        "queue.receive-wait": 7, "queue.visibility-timeout": 29 } } : result;
    };
    constructions.length = commands.length = 0;
    const worker = createAwsSdkPlatformSqsWorkerQueueFromConfiguration(recordConfigSource(valid), undefined, checked);
    equal(worker.ok, true); deepEqual(constructions, [{ region: "checked-region" }]);
    if (worker.ok) await worker.value.receive();
    equal(commands.length, 1); equal(commands[0] instanceof ReceiveMessageCommand, true);
    deepEqual((commands[0] as ReceiveMessageCommand).input, { QueueUrl: "checked-address", MaxNumberOfMessages: 1,
      WaitTimeSeconds: 7, VisibilityTimeout: 29, MessageSystemAttributeNames: ["ApproximateReceiveCount"] });
    constructions.length = commands.length = 0;
    const sender = createAwsSdkPlatformSqsQueueFromConfiguration(recordConfigSource(valid), undefined, checked);
    const messageType = queueMessageType("fixture.work"); const enqueuedAt = isoDateTime("2026-11-04T12:00:00.000Z");
    if (!messageType.ok || !enqueuedAt.ok || !sender.ok) throw Error("fixture-invalid");
    equal((await sender.value.send(queueMessage({ id: queueMessageId("fixture-1"), type: messageType.value,
      enqueuedAt: enqueuedAt.value, payload: {} }))).ok, true);
    deepEqual(constructions, [{ region: "checked-region" }]); equal(commands.length, 1);
    equal(commands[0] instanceof SendMessageCommand, true); equal((commands[0] as SendMessageCommand).input.QueueUrl, "checked-address");
    const refused: SqsConfigurationCheck = () => ({ ok: false, error: { code: "CONFIGURATION_INVALID", issues: [{ setting: "queue.region", reason: "missing" }] } });
    constructions.length = 0;
    equal(createAwsSdkPlatformSqsWorkerQueueFromConfiguration(recordConfigSource(valid), undefined, refused).ok, false); equal(constructions.length, 0);

    // Actual Platform loader composition: binding names change, adapter rules do not.
    for (const prefix of ["FIRST_", "SECOND_"]) {
      const bindings = Object.fromEntries(sqsWorkerRequirements.map((item, index) => [item.setting, prefix + index]));
      const env = Object.fromEntries(sqsWorkerRequirements.map(item => [bindings[item.setting]!, valid[item.setting]]));
      const loaded = loadPlatformConfiguration({ source: recordConfigSource(env), bindings, requirements: sqsWorkerRequirements,
        assemble: assembleSqsWorkerConfiguration });
      deepEqual(loaded, { ok: true, value: { queueUrl: valid["queue.address"], region: valid["queue.region"], waitTimeSeconds: 20, visibilityTimeoutSeconds: 120 } });
      const mapped: ConfigSource = { get(name) { return env[bindings[name]!]; } };
      const platformCheck: SqsConfigurationCheck = (source, requirements) => loadPlatformConfiguration({ source,
        requirements, bindings: Object.fromEntries(requirements.map(item => [item.setting, item.setting])), assemble: value => ({ ok: true, value }) });
      equal(createAwsSdkPlatformSqsWorkerQueueFromConfiguration(mapped, undefined, platformCheck).ok, true);
    }

    const sourceDefinition = defineDiagnostic({ code: "fixture.sqs.source", version: 1,
      classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
      detail: { type: "integer", minimum: 0, maximum: 8 } } as const);
    const bundle = Array.from({ length: 9 }, (_, index) => { const result = createDiagnosticRecord(sourceDefinition, index); if (!result.ok) throw Error("fixture"); return result.value; });
    for (const role of ["sender", "worker"] as const) {
      const requirements = role === "sender" ? sqsSenderRequirements : sqsWorkerRequirements;
      const factory = role === "sender" ? createAwsSdkPlatformSqsQueueFromConfiguration : createAwsSdkPlatformSqsWorkerQueueFromConfiguration;
      for (const [position, requirement] of requirements.entries()) {
        const cause = Object.freeze(Object.assign(Error(canary), { diagnosticRecord: bundle[0], relatedDiagnosticRecords: bundle.slice(1) }));
        const reads: string[] = [], observed: DiagnosticRecord[] = [];
        const source: ConfigSource = { get(name) { equal(this, source); reads.push(name); if (name === requirement.setting) throw cause; return valid[name as keyof typeof valid]; } };
        constructions.length = 0;
        throws(() => factory(source, { diagnosticDefinitions: [sourceDefinition], onDiagnostic(record, context) {
          observed.push(record); deepEqual(context, { operation: "client-initialization", boundary: "selection" });
        } }), error => error === cause);
        deepEqual(reads, requirements.slice(0, position + 1).map(item => item.setting)); equal(constructions.length, 0);
        deepEqual(observed, [{ schema: "core/diagnostic-record/v1", code: `aws-sqs.${role}-configuration-source-failed`, definitionVersion: 1,
          detail: { phase: "configuration-source-read", source: requirement.setting, reason: "unclassified-read-failure", effect: "not-assessed" } }, ...bundle]);
        equal(JSON.stringify(observed).includes(canary), false);
      }
    }
    for (const onDiagnostic of [() => { throw Error(canary); }, async () => { throw Error(canary); },
      () => Object.defineProperty(Promise.reject(Error(canary)), "then", { value() { throw Error(canary); } })]) {
      equal(createAwsSdkPlatformSqsWorkerQueueFromConfiguration(recordConfigSource({}), { onDiagnostic }).ok, false);
      const cause = Object.freeze(Error(canary)); throws(() => createAwsSdkPlatformSqsWorkerQueueFromConfiguration({ get() { throw cause; } }, { onDiagnostic }), error => error === cause);
    }
    await new Promise(resolve => setImmediate(resolve));
    const ownOnly: DiagnosticRecord[] = [];
    equal(createAwsSdkPlatformSqsWorkerQueueFromConfiguration(recordConfigSource({}), {
      get diagnosticDefinitions(): never { throw Error(canary); }, onDiagnostic(record) { ownOnly.push(record); },
    }).ok, false);
    deepEqual(ownOnly, [packet("worker", sqsWorkerRequirements.map(item => ({ setting: item.setting, reason: "missing" })))]);
    const sourceCause = Object.freeze(Object.assign(Error(canary), { diagnosticRecord: bundle[0], relatedDiagnosticRecords: bundle.slice(1) }));
    let deliveries = 0; const surviving: DiagnosticRecord[] = [];
    throws(() => createAwsSdkPlatformSqsWorkerQueueFromConfiguration({ get() { throw sourceCause; } }, {
      diagnosticDefinitions: [sourceDefinition], onDiagnostic(record) { deliveries++; if (deliveries === 1) throw Error(canary); surviving.push(record); },
    }), error => error === sourceCause);
    equal(deliveries, 10); deepEqual(surviving, bundle, "failed own delivery cannot discard independently selected source evidence");

    // Retained environment APIs deliberately have different historical text/number policies.
    const legacy = { PLATFORM_WORKER_SQS_QUEUE_URL: valid["queue.address"], PLATFORM_WORKER_SQS_REGION: valid["queue.region"],
      PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "20", PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS: "120" };
    for (const wait of ["", " ", "0x10", "1e1", "1.0"]) equal(createAwsSdkPlatformSqsWorkerQueueFromEnv({ ...legacy, PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: wait }).ok, true);
    equal(createAwsSdkPlatformSqsWorkerQueueFromEnv({ ...legacy, PLATFORM_WORKER_SQS_REGION: " region " }).ok, true);
    const reads: string[] = [];
    const failed = createAwsSdkPlatformSqsWorkerQueueFromEnv(new Proxy({}, { get(_target, key: string) { reads.push(key); return undefined; } }));
    deepEqual(reads, Object.keys(legacy)); equal(failed.ok, false);
    if (!failed.ok) deepEqual(failed.error, { code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID", defaultMessage: "AWS SQS worker queue configuration is invalid.",
      details: { path: "PLATFORM_WORKER_SQS_QUEUE_URL", reason: "A non-empty value is required." }, configurationIssue: { setting: "queue-address", reason: "missing" } });
    for (const factory of [createAwsSdkPlatformSqsWorkerQueueFromEnv]) {
      const cause = Object.freeze(Error(canary)); throws(() => factory(Object.defineProperty({}, "PLATFORM_WORKER_SQS_REGION", { get() { throw cause; } })), error => error === cause);
    }
    // Counterexample: constructor validation must read the same declared bounds, not copies.
    const requireFromHere = require;
    const module = requireFromHere("../src/configuration/contract/requirements.js") as { sqsReceiveWaitConstraint: typeof sqsReceiveWaitConstraint };
    const original = module.sqsReceiveWaitConstraint;
    try {
      module.sqsReceiveWaitConstraint = { ...original, maximum: 3 } as unknown as typeof original;
      throws(() => createPlatformSqsWorkerQueue({ queueUrl: "fixture", waitTimeSeconds: 4, visibilityTimeoutSeconds: 0, client: new FakeClient({}) }), RangeError);
      equal(createAwsSdkPlatformSqsWorkerQueueFromEnv({ ...legacy, PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS: "4" }).ok, false);
    } finally { module.sqsReceiveWaitConstraint = original; }
    console.log("SQS strict configuration, legacy compatibility, actual client guards and Platform composition passed.");
  } finally { fake.SQSClient = originalClient; }
}
void main();
