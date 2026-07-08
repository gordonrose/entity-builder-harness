import { deepEqual, equal, notEqual } from "node:assert/strict";
import {
  fileAccessIntent,
  fileChecksum,
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
import { diagnosticDescriptor } from "../src/diagnostics/index";
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

  console.log("packages/core files runtime test passed.");
}

void main();
