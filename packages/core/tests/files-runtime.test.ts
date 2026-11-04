import { deepEqual, equal, notEqual, throws, rejects } from "node:assert/strict";
import {
  fileAccessIntent,
  fileChecksum,
  fileChecksumAlgorithm,
  fileChecksumValue,
  coreFileDiagnosticDefinitions,
  coreFileBoundaryDiagnosticRecord,
  observeCoreFileDiagnostic,
  type CoreFileDiagnosticOptions,
  type CoreFileDiagnosticContext,
  type PutFileInput,
  fileContentType,
  fileError,
  fileId,
  fileMetadata,
  fileName,
  fileObject,
  fileRetentionPolicy,
  fileScanResult,
  fileSizeBytes,
  fileStorageKey,
  fileStorageRef,
  inMemoryFileStorage,
  putFileInput,
} from "../src/files/index";
import { createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticRecord, diagnosticDescriptor } from "../src/diagnostics/index";
import { correlationId, isErr, isOk, type ISODateTime } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

const name = fileName("contacts.csv");
equal(isOk(name), true);
if (!isOk(name)) {
  throw new Error("Expected file name to be valid.");
}
equal(name.value, "contacts.csv");

const badName = fileName("../contacts.csv");
equal(isErr(badName), true);
if (!isErr(badName)) {
  throw new Error("Expected path-like file name to be rejected.");
}
equal(badName.error.code, "FILE_INVALID_NAME");

const contentType = fileContentType("TEXT/CSV");
equal(isOk(contentType), true);
if (!isOk(contentType)) {
  throw new Error("Expected content type to be valid.");
}
equal(contentType.value, "text/csv");
equal(isErr(fileContentType("text csv")), true);

const size = fileSizeBytes(128);
equal(isOk(size), true);
if (!isOk(size)) {
  throw new Error("Expected file size to be valid.");
}
equal(size.value, 128);
equal(isErr(fileSizeBytes(-1)), true);
equal(isErr(fileSizeBytes(Number.POSITIVE_INFINITY)), true);

const checksum = fileChecksum({ algorithm: "SHA256", value: "abc123" });
equal(isOk(checksum), true);
if (!isOk(checksum)) {
  throw new Error("Expected file checksum to be valid.");
}
equal(checksum.value.algorithm, "sha256");
equal(checksum.value.value, "abc123");
equal(isErr(fileChecksum({ algorithm: "sha 256", value: "abc123" })), true);
const checksumValue = checksum.value;

const storageKey = fileStorageKey("tenant-123/imports/contacts.csv");
equal(isOk(storageKey), true);
if (!isOk(storageKey)) {
  throw new Error("Expected file storage key to be valid.");
}
equal(storageKey.value, "tenant-123/imports/contacts.csv");
equal(isErr(fileStorageKey("/tenant-123/imports/contacts.csv")), true);
equal(isErr(fileStorageKey("tenant-123/../contacts.csv")), true);

const metadata = fileMetadata({
  source: "csv-import",
  rowCount: 42,
  reviewed: false,
  nested: { optional: null },
});
equal(isOk(metadata), true);
if (!isOk(metadata)) {
  throw new Error("Expected file metadata to be valid.");
}
const metadataValue = metadata.value;
deepEqual(metadataValue, {
  source: "csv-import",
  rowCount: 42,
  reviewed: false,
  nested: { optional: null },
});
const copiedMetadata = fileMetadata(metadataValue);
equal(isOk(copiedMetadata), true);
if (!isOk(copiedMetadata)) {
  throw new Error("Expected copied file metadata to be valid.");
}
notEqual(metadataValue, copiedMetadata.value);
const invalidMetadata = fileMetadata({ uploadedAt: new Date() as never });
equal(isErr(invalidMetadata), true);
if (!isErr(invalidMetadata)) {
  throw new Error("Expected non-plain metadata to be invalid.");
}
equal(invalidMetadata.error.code, "FILE_INVALID_METADATA");

const scan = fileScanResult({
  status: "passed",
  scanner: "fixture-scanner",
  details: { signatureVersion: "v1" },
});
equal(isOk(scan), true);
if (!isOk(scan)) {
  throw new Error("Expected file scan result to be valid.");
}
equal(scan.value.status, "passed");
equal(isErr(fileScanResult({ status: "not-real" as never })), true);
equal(isErr(fileScanResult({ status: "passed", scanner: " " })), true);
const scanValue = scan.value;

const createdAt = "2026-07-08T12:00:00.000Z" as ISODateTime;
const tenant = tenantId("tenant-123");
const requestCorrelationId = correlationId("request-123");
const retention = fileRetentionPolicy({
  retainUntil: createdAt,
  legalHold: false,
});
const storedFile = fileObject({
  id: fileId("file-123"),
  fileName: name.value,
  contentType: contentType.value,
  sizeBytes: size.value,
  storage: fileStorageRef({ key: storageKey.value }),
  createdAt,
  tenantId: tenant,
  correlationId: requestCorrelationId,
  checksum: checksum.value,
  metadata: metadataValue,
  scan: scan.value,
  retention,
});
equal(storedFile.id, "file-123");
equal(storedFile.storage.key, "tenant-123/imports/contacts.csv");
equal(storedFile.tenantId, tenant);
equal(storedFile.correlationId, requestCorrelationId);

const accessIntent = fileAccessIntent({
  fileId: storedFile.id,
  operation: "read",
  tenantId: tenant,
  correlationId: requestCorrelationId,
  expiresAt: createdAt,
  metadata: { reason: "preview" },
});
equal(isOk(accessIntent), true);
if (!isOk(accessIntent)) {
  throw new Error("Expected file access intent to be valid.");
}
const accessIntentValue = accessIntent.value;
equal(accessIntentValue.operation, "read");
const invalidAccessIntent = fileAccessIntent({ fileId: storedFile.id, operation: "share" as never });
equal(isErr(invalidAccessIntent), true);
if (!isErr(invalidAccessIntent)) {
  throw new Error("Expected invalid file access operation to be rejected.");
}
equal(invalidAccessIntent.error.code, "FILE_INVALID_ACCESS_OPERATION");

const storageUnavailable = fileError({
  code: "FILE_STORAGE_UNAVAILABLE",
  defaultMessage: "File storage is unavailable.",
  messageKey: "files.storage.unavailable",
  diagnostic: diagnosticDescriptor({
    failureKind: "dependency_unavailable",
    failureSource: "provider",
    severity: "error",
    recovery: "automation_retryable",
    action: "retry",
  }),
});
equal(storageUnavailable.diagnostic?.retryable, true);

const deleteIntent = fileAccessIntent({
  fileId: storedFile.id,
  operation: "delete",
  tenantId: tenant,
  correlationId: requestCorrelationId,
});
equal(isOk(deleteIntent), true);
if (!isOk(deleteIntent)) {
  throw new Error("Expected delete access intent to be valid.");
}
const deleteIntentValue = deleteIntent.value;

async function main(): Promise<void> {
  const storage = inMemoryFileStorage<string>({ now: createdAt });
  const input = putFileInput({
    id: storedFile.id,
    fileName: storedFile.fileName,
    contentType: storedFile.contentType,
    sizeBytes: storedFile.sizeBytes,
    tenantId: tenant,
    correlationId: requestCorrelationId,
    checksum: checksumValue,
    metadata: metadataValue,
    scan: scanValue,
    retention,
    body: "email,name\nuser@example.test,Test User\n",
  });
  const put = await storage.put(
    input,
  );
  equal(isOk(put), true);
  if (!isOk(put)) {
    throw new Error("Expected in-memory file put to succeed.");
  }
  equal(put.value.storage.key, "memory/file-123");

  const duplicate = await storage.put(input);
  equal(isErr(duplicate), true);
  if (!isErr(duplicate)) {
    throw new Error("Expected duplicate file put to fail by default.");
  }
  equal(duplicate.error.code, "FILE_ALREADY_EXISTS");

  const idempotentDuplicate = await storage.put(input, { duplicateStrategy: "idempotent" });
  equal(isOk(idempotentDuplicate), true);

  const fetched = await storage.get(accessIntentValue);
  equal(isOk(fetched), true);
  if (!isOk(fetched)) {
    throw new Error("Expected stored file to be fetched.");
  }
  equal(fetched.value.fileName, "contacts.csv");
  equal(fetched.value.tenantId, tenant);
  equal(storage.acceptedPuts().length, 1);
  equal(storage.storedFiles().length, 1);

  const tenantlessIntent = fileAccessIntent({
    fileId: storedFile.id,
    operation: "read",
  });
  equal(isOk(tenantlessIntent), true);
  if (!isOk(tenantlessIntent)) {
    throw new Error("Expected tenantless access intent to be structurally valid.");
  }
  const tenantlessIntentValue = tenantlessIntent.value;
  const tenantlessRead = await storage.get(tenantlessIntentValue);
  equal(isErr(tenantlessRead), true);
  if (!isErr(tenantlessRead)) {
    throw new Error("Expected tenantless read of tenant-scoped file to be denied.");
  }
  equal(tenantlessRead.error.code, "FILE_ACCESS_DENIED");

  const deleted = await storage.delete(deleteIntentValue);
  equal(isOk(deleted), true);
  const missing = await storage.get(accessIntentValue);
  equal(isErr(missing), true);
  if (!isErr(missing)) {
    throw new Error("Expected deleted file to be missing.");
  }
  equal(missing.error.code, "FILE_NOT_FOUND");

  await fileDiagnosticsProof();
  console.log("packages/core files runtime test passed.");
}

const literalFileRecord = (code: string, detail: unknown) => ({
  schema: "core/diagnostic-record/v1", code: "core.files." + code, definitionVersion: 1, detail,
});
async function fileDiagnosticsProof(): Promise<void> {
  const seen: DiagnosticRecord[] = [];
  const contexts: CoreFileDiagnosticContext[] = [];
  const options: CoreFileDiagnosticOptions = {
    onDiagnostic(this: unknown, record, context) {
      equal(this, options);
      seen.push(record);
      contexts.push(context);
    },
  };
  const own = () => seen.filter((record) => record.code.startsWith("core.files."));
  const reset = () => { seen.length = 0; contexts.length = 0; };
  const invalid = (run: () => unknown, operation: string, field: string, reason: string, ordinal?: number) => {
    reset(); run();
    deepEqual(seen, [literalFileRecord("validation-rejected", { operation, field, reason, effect: "rejected", ...(ordinal === undefined ? {} : { ordinal }) })]);
  };
  for (const [value, reason] of [["", "empty"], ["a".repeat(256), "too-long"], [" a", "untrimmed"], ["a/b", "path-separator"], ["a\\b", "path-separator"], ["a\u0000b", "control-character"]] as const) {
    invalid(() => fileName(value, options), "name", "name", reason);
  }
  invalid(() => fileContentType("a".repeat(256), options), "content-type", "content-type", "too-long");
  invalid(() => fileContentType("bad", options), "content-type", "content-type", "invalid-format");
  invalid(() => fileSizeBytes(NaN, options), "size", "size", "not-safe-integer");
  invalid(() => fileSizeBytes(1.5, options), "size", "size", "not-safe-integer");
  invalid(() => fileSizeBytes(-1, options), "size", "size", "negative");
  invalid(() => fileChecksumAlgorithm("bad value", options), "checksum-algorithm", "checksum-algorithm", "invalid-format");
  for (const [value, reason] of [["", "empty"], [" a", "untrimmed"], ["a b", "whitespace"], ["a\u0000b", "control-character"]] as const) {
    invalid(() => fileChecksumValue(value, options), "checksum-value", "checksum-value", reason);
  }
  for (const [value, reason] of [["", "empty"], ["a".repeat(1025), "too-long"], ["/a", "absolute-path"], ["a\u0000b", "control-character"], ["a//b", "empty-segment"], ["a/./b", "dot-segment"], ["a/../b", "parent-segment"]] as const) {
    invalid(() => fileStorageKey(value, options), "storage-key", "storage-key", reason, reason.endsWith("-segment") ? 1 : undefined);
  }
  invalid(() => fileScanResult({ status: "unselected" as never }, options), "scan-result", "scan-status", "closed-value-rejected");
  invalid(() => fileScanResult({ status: "passed", scanner: " \t" }, options), "scan-result", "scanner", "blank");
  invalid(() => fileAccessIntent({ fileId: storedFile.id, operation: "unknown" as never }, options), "access-intent", "access-operation", "closed-value-rejected");
  const classification = coreFileDiagnosticDefinitions.find((definition) => definition.code === "core.files.operation-rejected")!.classification;
  deepEqual(classification, { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", retryable: false, userCorrectable: false, action: "none" });
  for (const definition of coreFileDiagnosticDefinitions) {
    equal(parseDiagnosticRecord<unknown>(definition, { schema: "core/diagnostic-record/v1", code: definition.code, definitionVersion: 1, detail: { private: "FILES-PRIVATE-CANARY" } }).ok, false);
  }

  // Preserve short-circuit getter counts and current aggregate return truthiness.
  let lengthReads = 0, trimReads = 0;
  invalid(() => fileName({
    get length() { lengthReads++; return 0; },
    get trim(): never { trimReads++; throw new Error("not reached"); },
  } as never, options), "name", "name", "empty");
  equal(lengthReads, 1); equal(trimReads, 0);
  let splitReads = 0, someCalls = 0, segmentCalls = 0;
  const aggregateValue = (callbackResult: boolean | undefined, aggregate: unknown) => ({
    length: 4,
    startsWith() { return false; },
    toString() { return "safe"; },
    split() {
      splitReads++;
      return { some(callback: (segment: string, index?: number) => boolean) {
        someCalls++;
        if (callbackResult !== undefined) { segmentCalls++; equal(callback(callbackResult ? ".." : "safe", 999), callbackResult); }
        return aggregate;
      } };
    },
  });
  invalid(() => fileStorageKey(aggregateValue(undefined, "truthy") as never, options), "storage-key", "storage-key", "predicate-rejected");
  invalid(() => fileStorageKey(aggregateValue(false, {}) as never, options), "storage-key", "storage-key", "predicate-rejected");
  invalid(() => fileStorageKey(aggregateValue(true, "truthy") as never, options), "storage-key", "storage-key", "parent-segment", 0);
  reset();
  const aggregateAccepted = aggregateValue(true, false);
  const accepted = fileStorageKey(aggregateAccepted as never, options);
  equal(accepted.ok, true);
  if (accepted.ok) equal(accepted.value, aggregateAccepted);
  equal(seen.length, 0);
  equal(splitReads, 4); equal(someCalls, 4); equal(segmentCalls, 3);
  let checksumValueReads = 0;
  invalid(() => fileChecksum({ algorithm: "bad value", get value() { checksumValueReads++; return "safe"; } }, options), "checksum-algorithm", "checksum-algorithm", "invalid-format");
  equal(checksumValueReads, 0);
  // Legacy runtime forwarding of nonstrings is not a newly invented guard.
  deepEqual(fileChecksum({ algorithm: 23, value: null } as never), { ok: true, value: { algorithm: 23, value: null } });

  const sourceDefinition = defineDiagnostic({
    code: "fixture.files.source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const sources = Array.from({ length: 9 }, (_, ordinal) => {
    const result = createDiagnosticRecord(sourceDefinition, { ordinal });
    if (!result.ok) throw new Error("source fixture failed");
    return result.value;
  });
  const sourceFailure = Object.freeze({ diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1), private: "FILES-PRIVATE-CANARY" });
  const selectedOptions = { ...options, diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record: DiagnosticRecord, context: CoreFileDiagnosticContext) => { seen.push(record); contexts.push(context); } };
  reset();
  throws(() => fileStorageRef({ get key(): never { throw sourceFailure; } }, selectedOptions), (cause) => cause === sourceFailure);
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "storage-ref", phase: "input-projection", field: "storage-key", reason: "threw", effect: "value-not-produced" }), ...sources]);
  equal(contexts.every((context) => context.operation === "storage-ref" && context.field === "storage-key"), true);
  equal(JSON.stringify(seen).includes("FILES-PRIVATE-CANARY"), false);
  reset();
  throws(() => fileStorageRef({ get key(): never { throw sourceFailure; } }, options), (cause) => cause === sourceFailure);
  equal(seen.length, 1); // unselected external source
  let evidenceReads = 0;
  const accessorSource = Object.defineProperty({}, "diagnosticRecord", { get() { evidenceReads++; return sources[0]; } });
  reset();
  throws(() => fileStorageRef({ get key(): never { throw accessorSource; } }, selectedOptions), (cause) => cause === accessorSource);
  equal(seen.length, 1); equal(evidenceReads, 0);
  for (const raw of [undefined, null, 17, "FILES-PRIVATE-CANARY", Object.freeze(new TypeError("FILES-PRIVATE-CANARY"))]) {
    reset();
    throws(() => putFileInput({ get id(): never { throw raw; } } as never, options), (cause) => cause === raw);
    deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put-input", phase: "input-projection", field: "id", reason: "threw", effect: "value-not-produced" })]);
  }
  // A previously generated guard error is not a current predicate observation.
  const old = fileName("");
  if (old.ok) throw new Error("Expected rejection");
  reset();
  throws(() => fileRetentionPolicy({ get legalHold(): never { throw old.error; } }, options), (cause) => cause === old.error);
  equal(own()[0]?.code, "core.files.boundary-failed");
  equal(seen[1]?.code, "core.files.validation-rejected");

  // Metadata's catch-all reduction stays unknown; entries getters precede nested copy.
  reset();
  const reduced = fileMetadata({ get secret(): never { throw sourceFailure; } }, selectedOptions);
  equal(reduced.ok, false);
  if (reduced.ok) throw new Error("Expected metadata error");
  equal(reduced.error.code, "FILE_INVALID_METADATA"); equal(reduced.error.cause, sourceFailure);
  deepEqual(reduced.error.diagnosticRecord, sources[0]); deepEqual(reduced.error.relatedDiagnosticRecords, sources.slice(1));
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "metadata", phase: "metadata-enumeration", field: "metadata", reason: "threw", effect: "value-not-produced" }), ...sources]);
  const metadataOrder: string[] = [];
  reset();
  const badMetadata = fileMetadata({
    get first() { metadataOrder.push("first"); return new Date() as never; },
    get second(): never { metadataOrder.push("second"); throw sourceFailure; },
  }, selectedOptions);
  equal(badMetadata.ok, false); deepEqual(metadataOrder, ["first", "second"]);
  equal((seen[0]?.detail as { phase: string }).phase, "metadata-enumeration");
  reset();
  const badNested = fileMetadata({ secret: new Date() as never }, options);
  equal(badNested.ok, false);
  equal((seen[0]?.detail as { phase: string }).phase, "metadata-copy");
  equal(seen[0]?.code, "core.files.boundary-failed");
  equal(seen.some((record) => record.code === "core.shared.json-invalid"), true);

  const input = (id: string): PutFileInput<unknown> => ({
    id: fileId(id), fileName: storedFile.fileName, contentType: storedFile.contentType,
    sizeBytes: storedFile.sizeBytes, body: "FILES-PRIVATE-CANARY",
  });
  const decision = (operation: string, field: string, reason: string) => literalFileRecord("operation-rejected", { operation, field, reason, effect: "rejected-before-write" });
  const storage = inMemoryFileStorage<unknown>({ now: createdAt }, selectedOptions);
  const first = input("FILES-PRIVATE-CANARY");
  reset(); equal((await storage.put(first)).ok, true); equal(seen.length, 0);
  equal((await storage.put(first)).ok, false);
  deepEqual(seen, [decision("put", "id", "existing-file")]);
  reset();
  // Body is not read or compared during idempotent duplicate handling.
  let bodyReads = 0;
  equal((await storage.put({ ...first, get body(): never { bodyReads++; throw sourceFailure; } }, { duplicateStrategy: "idempotent" })).ok, true);
  equal(bodyReads, 0); equal(seen.length, 0);
  const mismatches = [
    ["fileName", "different", "file-name"], ["contentType", "different", "content-type"], ["sizeBytes", 42, "size"],
    ["tenantId", "different", "tenant-id"], ["correlationId", "different", "correlation-id"],
    ["checksum", { algorithm: "sha256", value: "different" }, "checksum"], ["metadata", { different: true }, "metadata"],
    ["scan", { status: "failed" }, "scan"], ["retention", { legalHold: true }, "retention"],
  ] as const;
  for (const [property, value, field] of mismatches) {
    reset();
    equal((await storage.put({ ...first, [property]: value } as never, { duplicateStrategy: "idempotent" })).ok, false);
    deepEqual(seen, [decision("put", field, "idempotent-mismatch")]);
  }
  reset();
  let laterReads = 0;
  equal((await storage.put({ ...first, fileName: "different" as never, get contentType(): never { laterReads++; throw sourceFailure; } }, { duplicateStrategy: "idempotent" })).ok, false);
  equal(laterReads, 0);
  deepEqual(seen, [decision("put", "file-name", "idempotent-mismatch")]);
  reset();
  let idReads = 0, strategyReads = 0;
  equal((await storage.put({ ...first, get id() { return ++idReads === 1 ? first.id : fileId("different"); } }, {
    get duplicateStrategy() { strategyReads++; return "idempotent" as const; },
  })).ok, false);
  equal(idReads, 3); equal(strategyReads, 1);
  deepEqual(seen, [decision("put", "id", "idempotent-mismatch")]);

  const stringifyOrder: string[] = [];
  const jsonStorage = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  const leftChecksum = { algorithm: checksumValue.algorithm, value: checksumValue.value, toJSON() { stringifyOrder.push("left"); return { value: "left" }; } };
  equal((await jsonStorage.put({ ...input("json"), checksum: leftChecksum })).ok, true);
  reset();
  let metadataReads = 0;
  const rightChecksum = { ...leftChecksum, toJSON() { stringifyOrder.push("right"); return { value: "right" }; } };
  equal((await jsonStorage.put({
    ...input("json"),
    checksum: rightChecksum,
    get metadata(): never { metadataReads++; throw sourceFailure; },
  }, { duplicateStrategy: "idempotent" })).ok, false);
  deepEqual(stringifyOrder, ["left", "right"]); equal(metadataReads, 0);
  deepEqual(seen, [decision("put", "checksum", "idempotent-mismatch")]);
  stringifyOrder.length = 0; reset();
  const throwingChecksum = { ...leftChecksum, toJSON(): never { stringifyOrder.push("right"); throw sourceFailure; } };
  await rejects(jsonStorage.put({
    ...input("json"), checksum: throwingChecksum,
  }, { duplicateStrategy: "idempotent" }), (cause) => cause === sourceFailure);
  deepEqual(stringifyOrder, ["left", "right"]);
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "json-comparison", field: "checksum", reason: "threw", effect: "put-write-not-reached" }), ...sources]);
  reset();
  equal((await storage.put(first, { duplicateStrategy: "unselected" as never })).ok, false);
  deepEqual(seen, [decision("put", "id", "existing-file")]);
  reset();
  equal((await storage.get({ fileId: first.id, operation: "write" })).ok, false);
  deepEqual(seen, [decision("get", "access-operation", "operation-mismatch")]);
  reset();
  equal((await storage.delete({ fileId: first.id, operation: "read" })).ok, false);
  deepEqual(seen, [decision("delete", "access-operation", "operation-mismatch")]);
  reset();
  let operationReads = 0, intentIdReads = 0;
  equal((await storage.get({
    get operation() { operationReads++; return "write" as const; },
    get fileId() { intentIdReads++; return first.id; },
  })).ok, false);
  equal(operationReads, 2); equal(intentIdReads, 1);
  deepEqual(seen, [decision("get", "access-operation", "operation-mismatch")]);
  for (const operation of ["get", "delete"] as const) {
    reset();
    equal((await storage[operation]({ fileId: fileId("missing"), operation: operation === "get" ? "read" : "delete" })).ok, false);
    deepEqual(seen, [decision(operation, "id", "file-absent")]);
  }
  const scoped = { ...input("scoped"), tenantId: tenant };
  equal((await storage.put(scoped)).ok, true);
  for (const operation of ["get", "delete"] as const) {
    reset();
    equal((await storage[operation]({ fileId: scoped.id, operation: operation === "get" ? "read" : "delete" })).ok, false);
    deepEqual(seen, [decision(operation, "tenant-id", "tenant-mismatch")]);
  }
  // Scan/retention/expired access remain facts, not new enforcement.
  const policyInput = { ...input("policy"), scan: { status: "quarantined" as const }, retention: { legalHold: true, retainUntil: createdAt } };
  equal((await storage.put(policyInput)).ok, true);
  reset();
  equal((await storage.get({ fileId: policyInput.id, operation: "read", expiresAt: "1900-01-01T00:00:00Z" as ISODateTime })).ok, true);
  equal((await storage.delete({ fileId: policyInput.id, operation: "delete", expiresAt: "1900-01-01T00:00:00Z" as ISODateTime })).ok, true);
  equal(seen.length, 0);

  // Selector first, receiver preserved, nullish fallback unchanged.
  const selectorOrder: string[] = [];
  let selectorCalls = 0;
  const config = {
    get storageKeyFor() { selectorOrder.push("select"); return function(this: unknown, received: unknown) {
      equal(this, config); equal(received, selectorInput); selectorCalls++; selectorOrder.push("invoke"); return null as never;
    }; },
    get now() { selectorOrder.push("now"); return createdAt; },
  };
  const selectorInput = { ...input("selector"), get id() { selectorOrder.push("id"); return fileId("selector"); } };
  reset(); equal((await inMemoryFileStorage(config, selectedOptions).put(selectorInput)).ok, true);
  deepEqual(selectorOrder, ["id", "select", "invoke", "id", "id", "now", "id", "id"]);
  equal(selectorCalls, 1); equal(seen.length, 0);
  const oldOptionalCall = (storageOptions: { readonly storageKeyFor?: (input: PutFileInput<unknown>) => unknown }, input: PutFileInput<unknown>) =>
    storageOptions.storageKeyFor?.(input);
  const nativeMessage = (action: () => unknown): string => {
    try { action(); } catch (cause) {
      equal(cause instanceof TypeError, true);
      return (cause as TypeError).message;
    }
    throw new Error("Expected native non-callable TypeError");
  };
  for (const noncallable of [false, 17, "", {}, Symbol("private")]) {
    let selections = 0, argumentReads = 0;
    const storageOptions = {
      now: createdAt,
      get storageKeyFor() { selections++; return noncallable as never; },
    };
    const noncallableInput = { ...input("noncallable"), get body(): never { argumentReads++; throw sourceFailure; } };
    const expectedMessage = nativeMessage(() => oldOptionalCall(storageOptions, noncallableInput));
    equal(selections, 1);
    reset();
    await rejects(inMemoryFileStorage(storageOptions, selectedOptions).put(noncallableInput), (cause) => cause instanceof TypeError && cause.message === expectedMessage);
    equal(selections, 2); equal(argumentReads, 0);
    deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "storage-key-invocation", field: "storage-key-for", reason: "threw", effect: "put-write-not-reached" })]);
  }
  // Actual private map/history receivers are retained, including native error text.
  let capturedMap: Map<string, unknown> | undefined;
  let capturedPuts: unknown[] | undefined;
  const captureSet = Map.prototype.set, capturePush = Array.prototype.push;
  const nativeStore = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  Map.prototype.set = function (key: unknown, value: unknown) {
    if (key === "native-seed") capturedMap = this;
    return Reflect.apply(captureSet, this, [key, value]);
  };
  Array.prototype.push = function (...items: unknown[]) {
    if (items.length === 1 && typeof items[0] === "object" && items[0] !== null && "storedFile" in items[0]) capturedPuts = this;
    return Reflect.apply(capturePush, this, items);
  };
  try { equal((await nativeStore.put(input("native-seed"))).ok, true); }
  finally { Map.prototype.set = captureSet; Array.prototype.push = capturePush; }
  if (capturedMap === undefined || capturedPuts === undefined) throw new Error("Expected actual store receiver capture");
  for (const method of ["get", "set", "delete"] as const) {
    const order: string[] = [];
    const files = capturedMap;
    const marker = { get id() { order.push("argument"); return fileId("native-seed"); } };
    Object.defineProperty(files, method, { configurable: true, get() { equal(this, files); order.push("selection"); return 17; } });
    const expectedMessage = nativeMessage(() => {
      if (method === "get") return files.get(marker.id);
      if (method === "set") return files.set(marker.id, storedFile);
      return files.delete(marker.id);
    });
    deepEqual(order, ["selection", "argument"]); order.length = 0;
    let selected = false;
    // Selection-before-argument is measured only at the targeted native member.
    Object.defineProperty(files, method, { configurable: true, get() { equal(this, files); order.push("selection"); selected = true; return 17; } });
    const actualInput = { ...input(method === "set" ? "native-new" : "native-seed"), get id() { if (selected) order.push("argument"); return fileId(method === "set" ? "native-new" : "native-seed"); } };
    const actualIntent = { get fileId() { if (selected) order.push("argument"); return fileId("native-seed"); }, operation: method === "delete" ? "delete" as const : "read" as const };
    try {
      await rejects(method === "delete" ? nativeStore.delete(actualIntent) : method === "get" ? nativeStore.get(actualIntent) : nativeStore.put(actualInput),
        (cause) => cause instanceof TypeError && cause.message === expectedMessage);
      deepEqual(order, ["selection", "argument"]);
    } finally { delete (files as unknown as Record<string, unknown>)[method]; }
  }
  {
    const puts = capturedPuts;
    let selections = 0;
    Object.defineProperty(puts, "push", { configurable: true, get() { equal(this, puts); selections++; return 17; } });
    const expectedMessage = nativeMessage(() => puts.push({ input: input("history-native"), storedFile }));
    try {
      await rejects(nativeStore.put(input("history-native")), (cause) => cause instanceof TypeError && cause.message === expectedMessage);
      equal(selections, 2);
    } finally { delete (puts as unknown as Record<string, unknown>)["push"]; }
  }
  for (const [field, configValue] of [
    ["storage-key-selection", { now: createdAt, get storageKeyFor(): never { throw sourceFailure; } }],
    ["storage-key-invocation", { now: createdAt, storageKeyFor(): never { throw sourceFailure; } }],
  ] as const) {
    reset();
    await rejects(inMemoryFileStorage(configValue, selectedOptions).put(input("key-failure")), (cause) => cause === sourceFailure);
    deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: field, field: "storage-key-for", reason: "threw", effect: "put-write-not-reached" }), ...sources]);
  }

  // Actual map-write/history boundaries. No rollback is implied.
  const postWrite = inMemoryFileStorage<unknown>({ now: createdAt }, selectedOptions);
  const postWriteInput = { ...input("post-write"), get body(): never { throw sourceFailure; } };
  reset();
  await rejects(postWrite.put(postWriteInput), (cause) => cause === sourceFailure);
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "history-copy", field: "body", reason: "threw", effect: "map-written-history-not-appended" }), ...sources]);
  equal(postWrite.storedFiles().length, 1); equal(postWrite.acceptedPuts().length, 0);
  const optionsFailure = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  reset();
  await rejects(optionsFailure.put(input("options"), new Proxy({}, { ownKeys(): never { throw sourceFailure; } })), (cause) => cause === sourceFailure);
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "options-enumeration", field: "options", reason: "threw", effect: "map-written-history-not-appended" }), ...sources]);
  equal(optionsFailure.storedFiles().length, 1); equal(optionsFailure.acceptedPuts().length, 0);
  const originalPush = Array.prototype.push;
  const appendFailure = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  Array.prototype.push = function (...items: unknown[]) {
    if (items.length === 1 && typeof items[0] === "object" && items[0] !== null && "storedFile" in items[0]) {
      Reflect.apply(originalPush, this, items);
      throw sourceFailure;
    }
    return Reflect.apply(originalPush, this, items);
  };
  reset();
  try { await rejects(appendFailure.put(input("append")), (cause) => cause === sourceFailure); }
  finally { Array.prototype.push = originalPush; }
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "history-append", reason: "threw", effect: "map-written-history-append-unknown" }), ...sources]);
  equal(appendFailure.storedFiles().length, 1); equal(appendFailure.acceptedPuts().length, 1);

  const originalSet = Map.prototype.set;
  const writeFailure = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  Map.prototype.set = function (key: unknown, value: unknown) {
    const result = Reflect.apply(originalSet, this, [key, value]);
    if (key === "write-uncertain") throw sourceFailure;
    return result;
  };
  reset();
  try { await rejects(writeFailure.put(input("write-uncertain")), (cause) => cause === sourceFailure); }
  finally { Map.prototype.set = originalSet; }
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "map-write", reason: "threw", effect: "map-write-unknown" }), ...sources]);
  equal(writeFailure.storedFiles().length, 1); equal(writeFailure.acceptedPuts().length, 0);

  // A return-copy failure occurs after both state and history succeeded.
  const returnFailure = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  Map.prototype.set = function (key: unknown, value: unknown) {
    if (key === "return-failure") {
      let nameReads = 0;
      const file = value as { fileName: unknown };
      const name = file.fileName;
      Object.defineProperty(file, "fileName", { configurable: true, get() { if (++nameReads === 1) throw sourceFailure; return name; } });
    }
    return Reflect.apply(originalSet, this, [key, value]);
  };
  reset();
  try { await rejects(returnFailure.put(input("return-failure")), (cause) => cause === sourceFailure); }
  finally { Map.prototype.set = originalSet; }
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "put", phase: "result-projection", field: "file-name", reason: "threw", effect: "map-written-history-appended" }), ...sources]);
  equal(returnFailure.storedFiles().length, 1); equal(returnFailure.acceptedPuts().length, 1);

  // Custom map failures after a successful callback use the enclosing traversal.
  const originalMap = Array.prototype.map;
  const snapshotStore = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  await snapshotStore.put(input("snapshot"));
  for (const snapshot of ["acceptedPuts", "storedFiles"] as const) {
    let copies = 0;
    Array.prototype.map = function (callback, receiver) {
      const result = Reflect.apply(originalMap, this, [callback, receiver]);
      if (this.length === 1 && typeof this[0] === "object" && this[0] !== null && ("storedFile" in this[0] || "fileName" in this[0])) {
        copies++; throw sourceFailure;
      }
      return result;
    };
    reset();
    try { throws(() => snapshotStore[snapshot](), (cause) => cause === sourceFailure); }
    finally { Array.prototype.map = originalMap; }
    equal(copies, 1);
    deepEqual(seen, [literalFileRecord("boundary-failed", { operation: snapshot === "acceptedPuts" ? "accepted-puts" : "stored-files", phase: "snapshot-iteration", reason: "threw", effect: "read-only" }), ...sources]);
  }

  reset();
  const deleteFailure = inMemoryFileStorage({ now: createdAt }, selectedOptions);
  await deleteFailure.put(input("delete-uncertain"));
  const originalDelete = Map.prototype.delete;
  Map.prototype.delete = function (key: unknown) {
    Reflect.apply(originalDelete, this, [key]);
    if (key === "delete-uncertain") throw sourceFailure;
    return false; // The original boolean is deliberately ignored by Files.
  };
  reset();
  try { await rejects(deleteFailure.delete({ fileId: fileId("delete-uncertain"), operation: "delete" }), (cause) => cause === sourceFailure); }
  finally { Map.prototype.delete = originalDelete; }
  deepEqual(seen, [literalFileRecord("boundary-failed", { operation: "delete", phase: "map-delete", reason: "threw", effect: "delete-unknown" }), ...sources]);
  equal(deleteFailure.storedFiles().length, 0);

  // Error companions are explicit, bounded, own-data and independent of old primary.
  const oldPrimary = sources[0]!;
  const errorInput = { code: "FILE_STORAGE_UNAVAILABLE" as const, defaultMessage: "Legacy", diagnosticRecord: oldPrimary };
  const suppliedRelated = sources.slice(1);
  const wrapper = fileError(errorInput, { relatedDiagnosticDefinitions: [sourceDefinition], relatedDiagnosticRecords: suppliedRelated });
  equal(wrapper.diagnosticRecord, oldPrimary); deepEqual(wrapper.relatedDiagnosticRecords, sources.slice(1));
  notEqual(wrapper.relatedDiagnosticRecords, suppliedRelated);
  equal(Object.isFrozen(wrapper.relatedDiagnosticRecords), true);
  for (const evidence of [
    { relatedDiagnosticDefinitions: [sourceDefinition], relatedDiagnosticRecords: sources },
    { relatedDiagnosticDefinitions: [], relatedDiagnosticRecords: sources.slice(1) },
    { relatedDiagnosticDefinitions: [sourceDefinition], relatedDiagnosticRecords: [{ ...sources[1], detail: { private: "FILES-PRIVATE-CANARY" } }] },
  ]) {
    const rejected = fileError(errorInput, evidence as never);
    equal(rejected.diagnosticRecord, oldPrimary); equal(rejected.relatedDiagnosticRecords, undefined);
  }
  let newEvidenceReads = 0;
  for (const key of ["relatedDiagnosticDefinitions", "relatedDiagnosticRecords"]) {
    const evidence = Object.defineProperty({ relatedDiagnosticDefinitions: [sourceDefinition], relatedDiagnosticRecords: sources.slice(1) }, key, { get(): never { newEvidenceReads++; throw sourceFailure; } });
    equal(fileError(errorInput, evidence).diagnosticRecord, oldPrimary);
  }
  equal(newEvidenceReads, 0);

  // Observer outcomes do not await or change results, including native-shadowed promises.
  let observerThenReads = 0, thenableCalls = 0;
  const rejectedPromise = Promise.reject(sourceFailure);
  Object.defineProperty(rejectedPromise, "then", { get(): never { observerThenReads++; throw sourceFailure; } });
  const badSinks: CoreFileDiagnosticOptions[] = [
    { onDiagnostic() { throw sourceFailure; } },
    { onDiagnostic() { return rejectedPromise; } },
    { onDiagnostic() { return { then(_resolve: unknown, reject: (cause: unknown) => void) { thenableCalls++; reject(sourceFailure); } }; } },
    Object.defineProperty({}, "onDiagnostic", { get(): never { throw sourceFailure; } }),
  ];
  for (const sink of badSinks) equal(fileName("", sink).ok, false);
  await new Promise((resolve) => setTimeout(resolve, 0));
  equal(observerThenReads, 0); equal(thenableCalls, 1);
  // Direct helper checks own records; malformed own data cannot reach observer.
  reset();
  observeCoreFileDiagnostic(options, { ...coreFileBoundaryDiagnosticRecord({ operation: "get", phase: "map-lookup", reason: "threw", effect: "read-only" }), detail: { private: "FILES-PRIVATE-CANARY" } });
  equal(seen.length, 0);
  reset();
  throws(() => fileStorageRef({ get key(): never { throw sourceFailure; } }, Object.defineProperty({ onDiagnostic: selectedOptions.onDiagnostic }, "diagnosticDefinitions", { get(): never { throw sourceFailure; } })), (cause) => cause === sourceFailure);
  equal(seen.length, 1);
  equal(JSON.stringify(seen).includes("FILES-PRIVATE-CANARY"), false);
}

void main();
