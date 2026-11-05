import {
  brand,
  copyJsonValue,
  entityId,
  err,
  messageKey,
  ok,
  type Brand,
  type CoreError,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type JsonValue,
  type MessageDescriptor,
  type MessageKey,
  type MessageParams,
  type Result,
} from "../shared/index";
import type { DiagnosticDescriptor } from "../diagnostics/index";
import type { TenantId } from "../tenancy/index";
import { FileObservation, selectedFileCompanions } from "./observations";
import type { CoreFileDiagnosticOptions, CoreFileDiagnosticEvidence } from "./diagnostics";
export * from "./diagnostics";
export { observeCoreFileDiagnostic, selectCoreFileDiagnosticEvidence } from "./observations";

export type FileId = EntityId<"FileId">;
export type FileName = Brand<string, "FileName">;
export type FileContentType = Brand<string, "FileContentType">;
export type FileSizeBytes = Brand<number, "FileSizeBytes">;
export type FileChecksumAlgorithm = Brand<string, "FileChecksumAlgorithm">;
export type FileChecksumValue = Brand<string, "FileChecksumValue">;
export type FileStorageKey = Brand<string, "FileStorageKey">;
export type FileMetadataValue = JsonValue;
export type FileMetadata = Readonly<Record<string, FileMetadataValue>>;

export const fileScanStatuses = ["not_required", "pending", "passed", "failed", "quarantined", "unknown"] as const;
export type FileScanStatus = (typeof fileScanStatuses)[number];

export const fileAccessOperations = ["read", "write", "delete"] as const;
export type FileAccessOperation = (typeof fileAccessOperations)[number];

export const fileDuplicateStrategies = ["conflict", "idempotent"] as const;
export type FileDuplicateStrategy = (typeof fileDuplicateStrategies)[number];

export type FileErrorCode =
  | "FILE_ACCESS_DENIED"
  | "FILE_ALREADY_EXISTS"
  | "FILE_INVALID_CHECKSUM"
  | "FILE_INVALID_ACCESS_OPERATION"
  | "FILE_INVALID_CONTENT_TYPE"
  | "FILE_INVALID_METADATA"
  | "FILE_INVALID_NAME"
  | "FILE_INVALID_SCAN_STATUS"
  | "FILE_INVALID_SIZE"
  | "FILE_INVALID_STORAGE_KEY"
  | "FILE_NOT_FOUND"
  | "FILE_POLICY_DENIED"
  | "FILE_SCAN_FAILED"
  | "FILE_STORAGE_UNAVAILABLE";

export interface FileError extends CoreError {
  readonly code: FileErrorCode;
}

export interface FileChecksum {
  readonly algorithm: FileChecksumAlgorithm;
  readonly value: FileChecksumValue;
}

export interface FileStorageRef {
  readonly key: FileStorageKey;
}

export interface FileRetentionPolicy {
  readonly retainUntil?: ISODateTime;
  readonly legalHold?: boolean;
}

export interface FileScanResult {
  readonly status: FileScanStatus;
  readonly scannedAt?: ISODateTime;
  readonly scanner?: string;
  readonly details?: FileMetadata;
}

export interface FileObject {
  readonly id: FileId;
  readonly fileName: FileName;
  readonly contentType: FileContentType;
  readonly sizeBytes: FileSizeBytes;
  readonly storage: FileStorageRef;
  readonly createdAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly checksum?: FileChecksum;
  readonly metadata?: FileMetadata;
  readonly scan?: FileScanResult;
  readonly retention?: FileRetentionPolicy;
}

export type StoredFile = FileObject;

export interface PutFileInput<TBody = unknown> {
  readonly id: FileId;
  readonly fileName: FileName;
  readonly contentType: FileContentType;
  readonly sizeBytes: FileSizeBytes;
  readonly body: TBody;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly checksum?: FileChecksum;
  readonly metadata?: FileMetadata;
  readonly scan?: FileScanResult;
  readonly retention?: FileRetentionPolicy;
}

export interface FilePutOptions {
  readonly duplicateStrategy?: FileDuplicateStrategy;
}

export interface FileAccessIntent {
  readonly fileId: FileId;
  readonly operation: FileAccessOperation;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly expiresAt?: ISODateTime;
  readonly reason?: MessageDescriptor;
  readonly metadata?: FileMetadata;
}

export interface FileStorage<TBody = unknown> {
  put(input: PutFileInput<TBody>, options?: FilePutOptions): Promise<Result<StoredFile, FileError>>;
  get(intent: FileAccessIntent): Promise<Result<StoredFile, FileError>>;
  delete(intent: FileAccessIntent): Promise<Result<void, FileError>>;
}

export interface FilePut<TBody = unknown> {
  readonly input: PutFileInput<TBody>;
  readonly options?: FilePutOptions;
  readonly storedFile: StoredFile;
}

export interface InMemoryFileStorage<TBody = unknown> extends FileStorage<TBody> {
  acceptedPuts(): readonly FilePut<TBody>[];
  storedFiles(): readonly StoredFile[];
}

export function fileId(value: string): FileId {
  return entityId<"FileId">(value);
}

export function fileName(value: string, diagnostics?: CoreFileDiagnosticOptions): Result<FileName, FileError> {
  const o = new FileObservation("name", diagnostics);
  return o.run(() => {
  if (o.check("name", "empty", () => value.length === 0) || o.check("name", "too-long", () => value.length > 255) || o.check("name", "untrimmed", () => value.trim() !== value) || o.check("name", "path-separator", () => /[\\/]/.test(value)) || o.check("name", "control-character", () => hasControlCharacter(value))) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_NAME",
        defaultMessage: "File name must be non-empty, bounded, and must not contain path separators or control characters.",
        messageKey: "files.name.invalid",
      }), "name"),
    );
  }

  return ok(brand<string, "FileName">(value));
  });
}

export function fileContentType(value: string, diagnostics?: CoreFileDiagnosticOptions): Result<FileContentType, FileError> {
  const o = new FileObservation("content-type", diagnostics);
  return o.run(() => {
  const normalized = o.at("normalization", "content-type", () => value.toLowerCase());

  if (o.check("content-type", "too-long", () => normalized.length > 255) || o.check("content-type", "invalid-format", () => !contentTypePattern.test(normalized))) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_CONTENT_TYPE",
        defaultMessage: "File content type must use a valid type/subtype value.",
        messageKey: "files.content_type.invalid",
        params: { contentType: value },
      }), "content-type"),
    );
  }

  return ok(brand<string, "FileContentType">(normalized));
  });
}

export function fileSizeBytes(value: number, diagnostics?: CoreFileDiagnosticOptions): Result<FileSizeBytes, FileError> {
  const o = new FileObservation("size", diagnostics);
  return o.run(() => {
  if (o.check("size", "not-safe-integer", () => !Number.isSafeInteger(value)) || o.check("size", "negative", () => value < 0)) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_SIZE",
        defaultMessage: "File size must be a non-negative safe integer number of bytes.",
        messageKey: "files.size.invalid",
        params: { sizeBytes: o.at("result-projection", "size", () => String(value)) },
      }), "size"),
    );
  }

  return ok(brand<number, "FileSizeBytes">(value));
  });
}

export function fileChecksumAlgorithm(value: string, diagnostics?: CoreFileDiagnosticOptions): Result<FileChecksumAlgorithm, FileError> {
  const o = new FileObservation("checksum-algorithm", diagnostics);
  return o.run(() => {
  if (o.check("checksum-algorithm", "invalid-format", () => !tokenPattern.test(value))) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_CHECKSUM",
        defaultMessage: "File checksum algorithm must be a non-empty token.",
        messageKey: "files.checksum.algorithm.invalid",
        params: { algorithm: value },
      }), "checksum-algorithm"),
    );
  }

  return ok(brand<string, "FileChecksumAlgorithm">(o.at("normalization", "checksum-algorithm", () => value.toLowerCase())));
  });
}

export function fileChecksumValue(value: string, diagnostics?: CoreFileDiagnosticOptions): Result<FileChecksumValue, FileError> {
  const o = new FileObservation("checksum-value", diagnostics);
  return o.run(() => {
  if (o.check("checksum-value", "empty", () => value.length === 0) || o.check("checksum-value", "untrimmed", () => value.trim() !== value) || o.check("checksum-value", "whitespace", () => /\s/.test(value)) || o.check("checksum-value", "control-character", () => hasControlCharacter(value))) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_CHECKSUM",
        defaultMessage: "File checksum value must be non-empty and must not contain whitespace or control characters.",
        messageKey: "files.checksum.value.invalid",
      }), "checksum-value"),
    );
  }

  return ok(brand<string, "FileChecksumValue">(value));
  });
}

export function fileChecksum(input: {
  readonly algorithm: string | FileChecksumAlgorithm;
  readonly value: string | FileChecksumValue;
}, diagnostics?: CoreFileDiagnosticOptions): Result<FileChecksum, FileError> {
  const o = new FileObservation("checksum", diagnostics);
  return o.run(() => {
  const algorithm =
    typeof o.read("checksum-algorithm", () => input.algorithm)! === "string" ? fileChecksumAlgorithm(o.read("checksum-algorithm", () => input.algorithm)!, diagnostics) : ok(o.read("checksum-algorithm", () => input.algorithm) as FileChecksumAlgorithm);
  if (!algorithm.ok) {
    return err(algorithm.error);
  }

  const value = typeof o.read("checksum-value", () => input.value)! === "string" ? fileChecksumValue(o.read("checksum-value", () => input.value)!, diagnostics) : ok(o.read("checksum-value", () => input.value) as FileChecksumValue);
  if (!value.ok) {
    return err(value.error);
  }

  return ok({
    algorithm: algorithm.value,
    value: value.value,
  });
  });
}

export function fileStorageKey(value: string, diagnostics?: CoreFileDiagnosticOptions): Result<FileStorageKey, FileError> {
  const o = new FileObservation("storage-key", diagnostics);
  return o.run(() => {
  let segmentOrdinal = 0;
  if (
    o.check("storage-key", "empty", () => value.length === 0) ||
    o.check("storage-key", "too-long", () => value.length > 1024) ||
    o.check("storage-key", "absolute-path", () => value.startsWith("/")) ||
    o.check("storage-key", "control-character", () => hasControlCharacter(value)) ||
    o.at("predicate-invocation", "storage-key", () => value.split("/").some((segment) => {
      const ordinal = segmentOrdinal++;
      return o.test("empty-segment", () => segment === "", ordinal) || o.test("dot-segment", () => segment === ".", ordinal) || o.test("parent-segment", () => segment === "..", ordinal);
    }))
  ) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_STORAGE_KEY",
        defaultMessage: "File storage key must be non-empty, bounded, relative, and path-traversal safe.",
        messageKey: "files.storage_key.invalid",
      }), "storage-key"),
    );
  }

  return ok(brand<string, "FileStorageKey">(value));
  });
}

export function fileMetadata<TValue extends FileMetadata>(value: TValue, diagnostics?: CoreFileDiagnosticOptions): Result<TValue, FileError> {
  const o = new FileObservation("metadata", diagnostics);
  return o.run(() => {
  return copyFileMetadataResult(value, o);
  });
}

export function fileScanResult(input: {
  readonly status: FileScanStatus;
  readonly scannedAt?: ISODateTime;
  readonly scanner?: string;
  readonly details?: FileMetadata;
}, diagnostics?: CoreFileDiagnosticOptions): Result<FileScanResult, FileError> {
  const o = new FileObservation("scan-result", diagnostics);
  return o.run(() => {
  if (o.check("scan-status", "closed-value-rejected", () => !fileScanStatuses.includes(o.read("scan-status", () => input.status)!))) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_SCAN_STATUS",
        defaultMessage: "File scan status must use the approved scan status vocabulary.",
        messageKey: "files.scan_status.invalid",
        params: { status: o.read("scan-status", () => input.status)! },
      }), "scan-status"),
    );
  }

  if (o.read("scanner", () => input.scanner)! !== undefined && o.check("scanner", "blank", () => o.read("scanner", () => input.scanner)!.trim().length === 0)) {
    return err(
      o.validation(fileError({
        code: "FILE_SCAN_FAILED",
        defaultMessage: "File scan result scanner must not be empty when supplied.",
        messageKey: "files.scan.scanner.invalid",
      }), "scanner"),
    );
  }

  const details = o.read("details", () => input.details)! === undefined ? undefined : copyFileMetadataResult(o.read("details", () => input.details)!, o);
  if (details !== undefined && !details.ok) {
    return err(details.error);
  }

  return ok({
    status: o.read("scan-status", () => input.status)!,
    ...(o.read("scanned-at", () => input.scannedAt)! === undefined ? {} : { scannedAt: o.read("scanned-at", () => input.scannedAt)! }),
    ...(o.read("scanner", () => input.scanner)! === undefined ? {} : { scanner: o.read("scanner", () => input.scanner)! }),
    ...(details === undefined ? {} : { details: details.value }),
  });
  });
}

export function fileStorageRef(input: { readonly key: FileStorageKey }, diagnostics?: CoreFileDiagnosticOptions): FileStorageRef {
  const o = new FileObservation("storage-ref", diagnostics);
  return o.run(() => {
  return { key: o.read("storage-key", () => input.key)! };
  });
}

export function fileRetentionPolicy(input: {
  readonly retainUntil?: ISODateTime;
  readonly legalHold?: boolean;
} = {}, diagnostics?: CoreFileDiagnosticOptions): FileRetentionPolicy {
  const o = new FileObservation("retention-policy", diagnostics);
  return o.run(() => {
  return {
    ...(o.read("retain-until", () => input.retainUntil)! === undefined ? {} : { retainUntil: o.read("retain-until", () => input.retainUntil)! }),
    ...(o.read("legal-hold", () => input.legalHold)! === undefined ? {} : { legalHold: o.read("legal-hold", () => input.legalHold)! }),
  };
  });
}

export function fileObject(input: {
  readonly id: FileId;
  readonly fileName: FileName;
  readonly contentType: FileContentType;
  readonly sizeBytes: FileSizeBytes;
  readonly storage: FileStorageRef;
  readonly createdAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly checksum?: FileChecksum;
  readonly metadata?: FileMetadata;
  readonly scan?: FileScanResult;
  readonly retention?: FileRetentionPolicy;
}, diagnostics?: CoreFileDiagnosticOptions): StoredFile {
  const o = new FileObservation("file-object", diagnostics);
  return o.run(() => copyStoredFile(input, o));
}

function copyStoredFile(input: FileObject, o: FileObservation): StoredFile {
  return {
    id: o.read("id", () => input.id)!,
    fileName: o.read("file-name", () => input.fileName)!,
    contentType: o.read("content-type", () => input.contentType)!,
    sizeBytes: o.read("size", () => input.sizeBytes)!,
    storage: o.at("storage-copy", "storage", () => ({ ...o.read("storage", () => input.storage)! })),
    createdAt: o.read("created-at", () => input.createdAt)!,
    ...(o.read("tenant-id", () => input.tenantId)! === undefined ? {} : { tenantId: o.read("tenant-id", () => input.tenantId)! }),
    ...(o.read("correlation-id", () => input.correlationId)! === undefined ? {} : { correlationId: o.read("correlation-id", () => input.correlationId)! }),
    ...(o.read("checksum", () => input.checksum)! === undefined ? {} : { checksum: o.at("checksum-copy", "checksum", () => ({ ...o.read("checksum", () => input.checksum)! })) }),
    ...(o.read("metadata", () => input.metadata)! === undefined ? {} : { metadata: copyFileMetadata(o.read("metadata", () => input.metadata)!, o) }),
    ...(o.read("scan", () => input.scan)! === undefined ? {} : { scan: copyFileScanResult(o.read("scan", () => input.scan)!, o) }),
    ...(o.read("retention", () => input.retention)! === undefined ? {} : { retention: copyFileRetentionPolicy(o.read("retention", () => input.retention)!, o) }),
  };
}

export function putFileInput<TBody>(input: {
  readonly id: FileId;
  readonly fileName: FileName;
  readonly contentType: FileContentType;
  readonly sizeBytes: FileSizeBytes;
  readonly body: TBody;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly checksum?: FileChecksum;
  readonly metadata?: FileMetadata;
  readonly scan?: FileScanResult;
  readonly retention?: FileRetentionPolicy;
}, diagnostics?: CoreFileDiagnosticOptions): PutFileInput<TBody> {
  const o = new FileObservation("put-input", diagnostics);
  return o.run(() => copyPutFileInput(input, o));
}

function projectPutFileInput<TBody>(input: PutFileInput<TBody>, o: FileObservation): PutFileInput<TBody> {
  return {
    id: o.read("id", () => input.id)!,
    fileName: o.read("file-name", () => input.fileName)!,
    contentType: o.read("content-type", () => input.contentType)!,
    sizeBytes: o.read("size", () => input.sizeBytes)!,
    body: o.read("body", () => input.body)!,
    ...(o.read("tenant-id", () => input.tenantId)! === undefined ? {} : { tenantId: o.read("tenant-id", () => input.tenantId)! }),
    ...(o.read("correlation-id", () => input.correlationId)! === undefined ? {} : { correlationId: o.read("correlation-id", () => input.correlationId)! }),
    ...(o.read("checksum", () => input.checksum)! === undefined ? {} : { checksum: o.at("checksum-copy", "checksum", () => ({ ...o.read("checksum", () => input.checksum)! })) }),
    ...(o.read("metadata", () => input.metadata)! === undefined ? {} : { metadata: copyFileMetadata(o.read("metadata", () => input.metadata)!, o) }),
    ...(o.read("scan", () => input.scan)! === undefined ? {} : { scan: copyFileScanResult(o.read("scan", () => input.scan)!, o) }),
    ...(o.read("retention", () => input.retention)! === undefined ? {} : { retention: copyFileRetentionPolicy(o.read("retention", () => input.retention)!, o) }),
  };
}

export function fileAccessIntent(input: {
  readonly fileId: FileId;
  readonly operation: FileAccessOperation;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly expiresAt?: ISODateTime;
  readonly reason?: MessageDescriptor;
  readonly metadata?: FileMetadata;
}, diagnostics?: CoreFileDiagnosticOptions): Result<FileAccessIntent, FileError> {
  const o = new FileObservation("access-intent", diagnostics);
  return o.run(() => {
  if (o.check("access-operation", "closed-value-rejected", () => !fileAccessOperations.includes(o.read("access-operation", () => input.operation)!))) {
    return err(
      o.validation(fileError({
        code: "FILE_INVALID_ACCESS_OPERATION",
        defaultMessage: "File access operation must use the approved operation vocabulary.",
        messageKey: "files.access.operation.invalid",
        params: { operation: o.read("access-operation", () => input.operation)! },
      }), "access-operation"),
    );
  }

  const metadata = o.read("metadata", () => input.metadata)! === undefined ? undefined : copyFileMetadataResult(o.read("metadata", () => input.metadata)!, o);
  if (metadata !== undefined && !metadata.ok) {
    return err(metadata.error);
  }

  return ok({
    fileId: o.read("id", () => input.fileId)!,
    operation: o.read("access-operation", () => input.operation)!,
    ...(o.read("tenant-id", () => input.tenantId)! === undefined ? {} : { tenantId: o.read("tenant-id", () => input.tenantId)! }),
    ...(o.read("correlation-id", () => input.correlationId)! === undefined ? {} : { correlationId: o.read("correlation-id", () => input.correlationId)! }),
    ...(o.read("expires-at", () => input.expiresAt)! === undefined ? {} : { expiresAt: o.read("expires-at", () => input.expiresAt)! }),
    ...(o.read("reason", () => input.reason)! === undefined ? {} : { reason: o.read("reason", () => input.reason)! }),
    ...(metadata === undefined ? {} : { metadata: metadata.value }),
  });
  });
}

export function fileError(input: {
  readonly code: FileErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly details?: Readonly<Record<string, unknown>>;
}, evidence?: CoreFileDiagnosticEvidence, diagnostics?: CoreFileDiagnosticOptions): FileError {
  const o = new FileObservation("error", diagnostics);
  return o.run(() => {
  const error: FileError = {
    code: o.read("error-code", () => input.code)!,
    defaultMessage: o.read("default-message", () => input.defaultMessage)!,
    ...(o.read("message-key", () => input.messageKey)! === undefined ? {} : { messageKey: messageKey(o.read("message-key", () => input.messageKey)!) }),
    ...(o.read("params", () => input.params)! === undefined ? {} : { params: o.read("params", () => input.params)! }),
    ...(o.read("cause", () => input.cause)! === undefined ? {} : { cause: o.read("cause", () => input.cause)! }),
    ...(o.read("diagnostic", () => input.diagnostic)! === undefined ? {} : { diagnostic: o.read("diagnostic", () => input.diagnostic)! }),
    ...(o.read("diagnostic-record", () => input.diagnosticRecord)! === undefined ? {} : { diagnosticRecord: o.read("diagnostic-record", () => input.diagnosticRecord)! }),
    ...(o.read("details", () => input.details)! === undefined ? {} : { details: o.read("details", () => input.details)! }),
  };
  const related = selectedFileCompanions(evidence);
  return related === undefined ? error : { ...error, relatedDiagnosticRecords: related };
  });
}

export function inMemoryFileStorage<TBody = unknown>(storageOptions: {
  readonly now: ISODateTime;
  readonly storageKeyFor?: (input: PutFileInput<TBody>) => FileStorageKey;
}, diagnostics?: CoreFileDiagnosticOptions): InMemoryFileStorage<TBody> {
  const initialization = new FileObservation("initialize", diagnostics);
  return initialization.run(() => {
  const files = initialization.at("state-creation", undefined, () => new Map<string, StoredFile>());
  const puts: FilePut<TBody>[] = [];

  return {
    async put(input: PutFileInput<TBody>, putOptions: FilePutOptions = {}) {
      const o = new FileObservation("put", diagnostics);
      o.effectIs("put-write-not-reached");
      return o.run(() => {
      const existing = o.at("map-selection", undefined, () => files.get(
        (o.location("map-lookup", "id"), o.read("id", () => input.id)!),
      ));
      if (existing !== undefined) {
        let idempotent = false;
        if ((idempotent = (o.read("duplicate-strategy", () => putOptions.duplicateStrategy)! ?? "conflict") === "idempotent") && matchesIdempotentPut(existing, input, o)) {
          return ok(o.at("result-projection", undefined, () => copyStoredFile(existing, o)));
        }

        return err(o.decision(
          fileError({
            code: "FILE_ALREADY_EXISTS",
            defaultMessage: "File already exists.",
            messageKey: "files.already_exists",
            details: { fileId: o.read("id", () => input.id)! },
          }), idempotent ? "idempotent-mismatch" : "existing-file", idempotent ? o.mismatch : "id",
        ));
      }

      const storageKey = o.at("storage-key-selection", "storage-key-for", () =>
        storageOptions.storageKeyFor?.((o.location("storage-key-invocation", "storage-key-for"), input))) ??
        o.at("default-storage-key", "storage-key", () => defaultStorageKeyFor(o.read("id", () => input.id)!));
      const storedFile = o.at("input-projection", undefined, () => copyStoredFile({
        id: o.read("id", () => input.id)!,
        fileName: o.read("file-name", () => input.fileName)!,
        contentType: o.read("content-type", () => input.contentType)!,
        sizeBytes: o.read("size", () => input.sizeBytes)!,
        storage: o.at("storage-copy", "storage", () => fileStorageRef({ key: storageKey })),
        createdAt: o.read("now", () => storageOptions.now)!,
        ...(o.read("tenant-id", () => input.tenantId)! === undefined ? {} : { tenantId: o.read("tenant-id", () => input.tenantId)! }),
        ...(o.read("correlation-id", () => input.correlationId)! === undefined ? {} : { correlationId: o.read("correlation-id", () => input.correlationId)! }),
        ...(o.read("checksum", () => input.checksum)! === undefined ? {} : { checksum: o.read("checksum", () => input.checksum)! }),
        ...(o.read("metadata", () => input.metadata)! === undefined ? {} : { metadata: o.read("metadata", () => input.metadata)! }),
        ...(o.read("scan", () => input.scan)! === undefined ? {} : { scan: o.read("scan", () => input.scan)! }),
        ...(o.read("retention", () => input.retention)! === undefined ? {} : { retention: o.read("retention", () => input.retention)! }),
      }, o));
      o.at("map-selection", undefined, () => files.set(
        (o.location("map-write", "id"), o.read("id", () => input.id)!),
        o.argument("map-write", "map-write-unknown", storedFile),
      ));
      o.effectIs("map-written-history-not-appended");
      o.at("history-selection", undefined, () => puts.push(o.argument("history-append", "map-written-history-append-unknown", o.at("history-copy", undefined, () => ({
        input: copyPutFileInput(input, o),
        ...(o.at("options-enumeration", "options", () => Object.keys(putOptions).length) === 0 ? {} : { options: o.at("options-copy", "options", () => copyFilePutOptions(putOptions, o)) }),
        storedFile,
      })))));
      o.effectIs("map-written-history-appended");
      return ok(o.at("result-projection", undefined, () => copyStoredFile(storedFile, o)));
      });
    },

    async get(intent: FileAccessIntent) {
      const o = new FileObservation("get", diagnostics);
      o.effectIs("read-only");
      return o.run(() => {
      if (o.read("access-operation", () => intent.operation) !== "read") {
        return err(o.decision(accessOperationDeniedError(intent, "read", o), "operation-mismatch", "access-operation"));
      }
      const storedFile = o.at("map-selection", undefined, () => files.get(
        (o.location("map-lookup", "id"), o.read("id", () => intent.fileId)),
      ));
      if (storedFile === undefined) {
        return err(o.decision(
          fileError({
            code: "FILE_NOT_FOUND",
            defaultMessage: "File was not found.",
            messageKey: "files.not_found",
            details: { fileId: o.read("id", () => intent.fileId) },
          }), "file-absent", "id",
        ));
      }
      const access = validateStoredFileAccess(storedFile, intent, o);
      if (!access.ok) return err(access.error);
      return ok(o.at("result-projection", undefined, () => copyStoredFile(storedFile, o)));
      });
    },

    async delete(intent: FileAccessIntent) {
      const o = new FileObservation("delete", diagnostics);
      o.effectIs("delete-not-reached");
      return o.run(() => {
      if (o.read("access-operation", () => intent.operation) !== "delete") {
        return err(o.decision(accessOperationDeniedError(intent, "delete", o), "operation-mismatch", "access-operation"));
      }
      const storedFile = o.at("map-selection", undefined, () => files.get(
        (o.location("map-lookup", "id"), o.read("id", () => intent.fileId)),
      ));
      if (storedFile === undefined) {
        return err(o.decision(
          fileError({
            code: "FILE_NOT_FOUND",
            defaultMessage: "File was not found.",
            messageKey: "files.not_found",
            details: { fileId: o.read("id", () => intent.fileId) },
          }), "file-absent", "id",
        ));
      }
      const access = validateStoredFileAccess(storedFile, intent, o);
      if (!access.ok) return err(access.error);
      o.at("map-selection", undefined, () => files.delete(
        o.argument("map-delete", "delete-unknown", o.at("map-delete", "id", () => intent.fileId)),
      ));
      o.effectIs("delete-returned");
      return ok(undefined);
      });
    },

    acceptedPuts() {
      const o = new FileObservation("accepted-puts", diagnostics);
      o.effectIs("read-only");
      return o.run(() => o.at("snapshot-iteration", undefined, () => puts.map((put) => o.at("snapshot-copy", undefined, () => ({
        input: copyPutFileInput(o.read("body", () => put.input), o),
        ...(o.read("options", () => put.options) === undefined ? {} : { options: copyFilePutOptions(o.read("options", () => put.options)!, o) }),
        storedFile: copyStoredFile(o.read("storage", () => put.storedFile), o),
      })))));
    },

    storedFiles() {
      const o = new FileObservation("stored-files", diagnostics);
      o.effectIs("read-only");
      return o.run(() => {
        const snapshot = o.at("snapshot-iteration", undefined, () => [...files.values()]);
        return o.at("snapshot-iteration", undefined, () => snapshot.map((file) => o.at("snapshot-copy", undefined, () => copyStoredFile(file, o))));
      });
    },
  };
  });
}

const contentTypePattern = /^[a-z0-9][a-z0-9!#$&^_.+-]*\/[a-z0-9][a-z0-9!#$&^_.+-]*$/;
const tokenPattern = /^[a-zA-Z0-9][a-zA-Z0-9._-]*$/;

function defaultStorageKeyFor(id: FileId): FileStorageKey {
  const key = fileStorageKey(`memory/${encodeURIComponent(id)}`);
  if (!key.ok) {
    throw key.error;
  }

  return key.value;
}

function copyPutFileInput<TBody>(input: PutFileInput<TBody>, o: FileObservation): PutFileInput<TBody> {
  return projectPutFileInput(input, o);
}

function copyFilePutOptions(options: FilePutOptions, o: FileObservation): FilePutOptions {
  return {
    ...(o.read("duplicate-strategy", () => options.duplicateStrategy)! === undefined ? {} : { duplicateStrategy: o.read("duplicate-strategy", () => options.duplicateStrategy)! }),
  };
}

function copyFileScanResult(scan: FileScanResult, o: FileObservation): FileScanResult {
  return o.at("scan-copy", "scan", () => ({
    status: o.read("scan-status", () => scan.status)!,
    ...(o.read("scanned-at", () => scan.scannedAt)! === undefined ? {} : { scannedAt: o.read("scanned-at", () => scan.scannedAt)! }),
    ...(o.read("scanner", () => scan.scanner)! === undefined ? {} : { scanner: o.read("scanner", () => scan.scanner)! }),
    ...(o.read("scan-details", () => scan.details)! === undefined ? {} : { details: copyFileMetadata(o.read("scan-details", () => scan.details)!, o) }),
  }));
}

function copyFileRetentionPolicy(retention: FileRetentionPolicy, o: FileObservation): FileRetentionPolicy {
  return o.at("retention-copy", "retention", () => ({
    ...(o.read("retain-until", () => retention.retainUntil)! === undefined ? {} : { retainUntil: o.read("retain-until", () => retention.retainUntil)! }),
    ...(o.read("legal-hold", () => retention.legalHold)! === undefined ? {} : { legalHold: o.read("legal-hold", () => retention.legalHold)! }),
  }));
}

function copyFileMetadataResult<TValue extends FileMetadata>(value: TValue, o: FileObservation): Result<TValue, FileError> {
  try {
    return ok(copyFileMetadata(value, o));
  } catch (cause) {
    const selected = o.boundary(cause);
    return err(Object.assign(
      fileError({
        code: "FILE_INVALID_METADATA",
        defaultMessage: "File metadata must be plain JSON-safe values.",
        messageKey: "files.metadata.invalid",
        cause,
      }), selected,
    ));
  }
}

function copyFileMetadata<TValue extends FileMetadata>(value: TValue, o: FileObservation): TValue {
  return o.at("metadata-copy", "metadata", () => Object.fromEntries(
    o.at("metadata-enumeration", "metadata", () => Object.entries(value)).map(([key, nestedValue]) =>
      o.at("metadata-copy", "metadata", () => [key, copyJsonValue(nestedValue, "file metadata")])),
  )) as TValue;
}

function accessOperationDeniedError(intent: FileAccessIntent, expectedOperation: FileAccessOperation, o: FileObservation): FileError {
  return fileError({
    code: "FILE_ACCESS_DENIED",
    defaultMessage: "File access intent does not allow this operation.",
    messageKey: "files.access.operation.denied",
    details: {
      fileId: o.read("id", () => intent.fileId),
      operation: o.read("access-operation", () => intent.operation),
      expectedOperation,
    },
  });
}

function validateStoredFileAccess(storedFile: StoredFile, intent: FileAccessIntent, o: FileObservation): Result<void, FileError> {
  if (o.read("tenant-id", () => storedFile.tenantId) !== undefined && o.read("tenant-id", () => intent.tenantId) !== o.read("tenant-id", () => storedFile.tenantId)) {
    return err(o.decision(
      fileError({
        code: "FILE_ACCESS_DENIED",
        defaultMessage: "File access tenant does not match stored file tenant.",
        messageKey: "files.access.tenant.denied",
        details: {
          fileId: o.read("id", () => storedFile.id),
          tenantScoped: true,
        },
      }), "tenant-mismatch", "tenant-id",
    ));
  }

  return ok(undefined);
}

function matchesIdempotentPut<TBody>(storedFile: StoredFile, input: PutFileInput<TBody>, o: FileObservation): boolean {
  return (
    o.equal("id", () => storedFile.id === input.id) &&
    o.equal("file-name", () => storedFile.fileName === input.fileName) &&
    o.equal("content-type", () => storedFile.contentType === input.contentType) &&
    o.equal("size", () => storedFile.sizeBytes === input.sizeBytes) &&
    o.equal("tenant-id", () => storedFile.tenantId === input.tenantId) &&
    o.equal("correlation-id", () => storedFile.correlationId === input.correlationId) &&
    o.equal("checksum", () => o.at("json-comparison", "checksum", () => jsonEqual(storedFile.checksum, input.checksum))) &&
    o.equal("metadata", () => o.at("json-comparison", "metadata", () => jsonEqual(storedFile.metadata, input.metadata))) &&
    o.equal("scan", () => o.at("json-comparison", "scan", () => jsonEqual(storedFile.scan, input.scan))) &&
    o.equal("retention", () => o.at("json-comparison", "retention", () => jsonEqual(storedFile.retention, input.retention)))
  );
}

function jsonEqual(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function hasControlCharacter(value: string): boolean {
  return /[\u0000-\u001f\u007f]/.test(value);
}
