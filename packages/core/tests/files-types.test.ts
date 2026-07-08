import {
  fileAccessIntent,
  fileChecksum,
  fileContentType,
  fileId,
  fileMetadata,
  fileName,
  fileObject,
  fileScanResult,
  fileSizeBytes,
  fileStorageKey,
  fileStorageRef,
  putFileInput,
  type FileAccessIntent,
  type FileMetadata,
  type FileObject,
  type FileScanStatus,
  type FileStorage,
  type PutFileInput,
} from "../src/files/index";
import { isOk, type ISODateTime } from "../src/shared/index";

const nameResult = fileName("contacts.csv");
const typeResult = fileContentType("text/csv");
const sizeResult = fileSizeBytes(1024);
const keyResult = fileStorageKey("tenant-123/imports/contacts.csv");
const checksumResult = fileChecksum({ algorithm: "sha256", value: "abc123" });
const scanResult = fileScanResult({ status: "passed", scanner: "fixture-scanner" });
const metadataResult = fileMetadata({
  source: "csv-import",
  rowCount: 42,
  reviewed: false,
  optional: null,
});

if (
  !isOk(nameResult) ||
  !isOk(typeResult) ||
  !isOk(sizeResult) ||
  !isOk(keyResult) ||
  !isOk(checksumResult) ||
  !isOk(scanResult) ||
  !isOk(metadataResult)
) {
  throw new Error("Expected file type fixture values to be valid.");
}

const metadata: FileMetadata = metadataResult.value;
const createdAt = "2026-07-08T12:00:00.000Z" as ISODateTime;
const storedFile: FileObject = fileObject({
  id: fileId("file-123"),
  fileName: nameResult.value,
  contentType: typeResult.value,
  sizeBytes: sizeResult.value,
  storage: fileStorageRef({ key: keyResult.value }),
  createdAt,
  checksum: checksumResult.value,
  metadata,
  scan: scanResult.value,
});
const input: PutFileInput<string> = putFileInput({
  id: storedFile.id,
  fileName: storedFile.fileName,
  contentType: storedFile.contentType,
  sizeBytes: storedFile.sizeBytes,
  checksum: checksumResult.value,
  metadata,
  scan: scanResult.value,
  body: "email,name\nuser@example.test,Test User\n",
});
const storage: FileStorage<string> = {
  put: async (_input, _options) => ({ ok: true, value: storedFile }),
  get: async (_intent) => ({ ok: true, value: storedFile }),
  delete: async (_intent) => ({ ok: true, value: undefined }),
};
const accessIntentResult = fileAccessIntent({
  fileId: storedFile.id,
  operation: "read",
  expiresAt: createdAt,
  metadata: { reason: "preview" },
});
if (!isOk(accessIntentResult)) {
  throw new Error("Expected file access intent fixture to be valid.");
}
const accessIntent: FileAccessIntent = accessIntentResult.value;
const deleteIntentResult = fileAccessIntent({
  fileId: storedFile.id,
  operation: "delete",
});
if (!isOk(deleteIntentResult)) {
  throw new Error("Expected file delete intent fixture to be valid.");
}
const scanStatus: FileScanStatus = "quarantined";

void input;
void storage;
void accessIntent;
void storage.get(accessIntent);
void storage.delete(deleteIntentResult.value);
void scanStatus;

// @ts-expect-error file storage reads must use an access intent, not a raw id.
void storage.get(storedFile.id);

// @ts-expect-error scan statuses must use the approved vocabulary.
const rejectedScanStatus: FileScanStatus = "clean";
void rejectedScanStatus;

// @ts-expect-error file metadata must stay JSON-safe and serializable.
const rejectedMetadata: FileMetadata = { uploadedAt: new Date() };
void rejectedMetadata;

fileObject({
  id: fileId("file-456"),
  // @ts-expect-error raw strings are not accepted where branded file names are required.
  fileName: "contacts.csv",
  contentType: typeResult.value,
  sizeBytes: sizeResult.value,
  storage: fileStorageRef({ key: keyResult.value }),
  createdAt,
});
