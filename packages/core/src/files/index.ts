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

export function fileName(value: string): Result<FileName, FileError> {
  if (value.length === 0 || value.length > 255 || value.trim() !== value || /[\\/]/.test(value) || hasControlCharacter(value)) {
    return err(
      fileError({
        code: "FILE_INVALID_NAME",
        defaultMessage: "File name must be non-empty, bounded, and must not contain path separators or control characters.",
        messageKey: "files.name.invalid",
      }),
    );
  }

  return ok(brand<string, "FileName">(value));
}

export function fileContentType(value: string): Result<FileContentType, FileError> {
  const normalized = value.toLowerCase();

  if (normalized.length > 255 || !contentTypePattern.test(normalized)) {
    return err(
      fileError({
        code: "FILE_INVALID_CONTENT_TYPE",
        defaultMessage: "File content type must use a valid type/subtype value.",
        messageKey: "files.content_type.invalid",
        params: { contentType: value },
      }),
    );
  }

  return ok(brand<string, "FileContentType">(normalized));
}

export function fileSizeBytes(value: number): Result<FileSizeBytes, FileError> {
  if (!Number.isSafeInteger(value) || value < 0) {
    return err(
      fileError({
        code: "FILE_INVALID_SIZE",
        defaultMessage: "File size must be a non-negative safe integer number of bytes.",
        messageKey: "files.size.invalid",
        params: { sizeBytes: String(value) },
      }),
    );
  }

  return ok(brand<number, "FileSizeBytes">(value));
}

export function fileChecksumAlgorithm(value: string): Result<FileChecksumAlgorithm, FileError> {
  if (!tokenPattern.test(value)) {
    return err(
      fileError({
        code: "FILE_INVALID_CHECKSUM",
        defaultMessage: "File checksum algorithm must be a non-empty token.",
        messageKey: "files.checksum.algorithm.invalid",
        params: { algorithm: value },
      }),
    );
  }

  return ok(brand<string, "FileChecksumAlgorithm">(value.toLowerCase()));
}

export function fileChecksumValue(value: string): Result<FileChecksumValue, FileError> {
  if (value.length === 0 || value.trim() !== value || /\s/.test(value) || hasControlCharacter(value)) {
    return err(
      fileError({
        code: "FILE_INVALID_CHECKSUM",
        defaultMessage: "File checksum value must be non-empty and must not contain whitespace or control characters.",
        messageKey: "files.checksum.value.invalid",
      }),
    );
  }

  return ok(brand<string, "FileChecksumValue">(value));
}

export function fileChecksum(input: {
  readonly algorithm: string | FileChecksumAlgorithm;
  readonly value: string | FileChecksumValue;
}): Result<FileChecksum, FileError> {
  const algorithm =
    typeof input.algorithm === "string" ? fileChecksumAlgorithm(input.algorithm) : ok(input.algorithm);
  if (!algorithm.ok) {
    return err(algorithm.error);
  }

  const value = typeof input.value === "string" ? fileChecksumValue(input.value) : ok(input.value);
  if (!value.ok) {
    return err(value.error);
  }

  return ok({
    algorithm: algorithm.value,
    value: value.value,
  });
}

export function fileStorageKey(value: string): Result<FileStorageKey, FileError> {
  if (
    value.length === 0 ||
    value.length > 1024 ||
    value.startsWith("/") ||
    hasControlCharacter(value) ||
    value.split("/").some((segment) => segment === "" || segment === "." || segment === "..")
  ) {
    return err(
      fileError({
        code: "FILE_INVALID_STORAGE_KEY",
        defaultMessage: "File storage key must be non-empty, bounded, relative, and path-traversal safe.",
        messageKey: "files.storage_key.invalid",
      }),
    );
  }

  return ok(brand<string, "FileStorageKey">(value));
}

export function fileMetadata<TValue extends FileMetadata>(value: TValue): Result<TValue, FileError> {
  return copyFileMetadataResult(value);
}

export function fileScanResult(input: {
  readonly status: FileScanStatus;
  readonly scannedAt?: ISODateTime;
  readonly scanner?: string;
  readonly details?: FileMetadata;
}): Result<FileScanResult, FileError> {
  if (!fileScanStatuses.includes(input.status)) {
    return err(
      fileError({
        code: "FILE_INVALID_SCAN_STATUS",
        defaultMessage: "File scan status must use the approved scan status vocabulary.",
        messageKey: "files.scan_status.invalid",
        params: { status: input.status },
      }),
    );
  }

  if (input.scanner !== undefined && input.scanner.trim().length === 0) {
    return err(
      fileError({
        code: "FILE_SCAN_FAILED",
        defaultMessage: "File scan result scanner must not be empty when supplied.",
        messageKey: "files.scan.scanner.invalid",
      }),
    );
  }

  const details = input.details === undefined ? undefined : copyFileMetadataResult(input.details);
  if (details !== undefined && !details.ok) {
    return err(details.error);
  }

  return ok({
    status: input.status,
    ...(input.scannedAt === undefined ? {} : { scannedAt: input.scannedAt }),
    ...(input.scanner === undefined ? {} : { scanner: input.scanner }),
    ...(details === undefined ? {} : { details: details.value }),
  });
}

export function fileStorageRef(input: { readonly key: FileStorageKey }): FileStorageRef {
  return { key: input.key };
}

export function fileRetentionPolicy(input: {
  readonly retainUntil?: ISODateTime;
  readonly legalHold?: boolean;
} = {}): FileRetentionPolicy {
  return {
    ...(input.retainUntil === undefined ? {} : { retainUntil: input.retainUntil }),
    ...(input.legalHold === undefined ? {} : { legalHold: input.legalHold }),
  };
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
}): StoredFile {
  return {
    id: input.id,
    fileName: input.fileName,
    contentType: input.contentType,
    sizeBytes: input.sizeBytes,
    storage: { ...input.storage },
    createdAt: input.createdAt,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.checksum === undefined ? {} : { checksum: { ...input.checksum } }),
    ...(input.metadata === undefined ? {} : { metadata: copyFileMetadata(input.metadata) }),
    ...(input.scan === undefined ? {} : { scan: copyFileScanResult(input.scan) }),
    ...(input.retention === undefined ? {} : { retention: copyFileRetentionPolicy(input.retention) }),
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
}): PutFileInput<TBody> {
  return {
    id: input.id,
    fileName: input.fileName,
    contentType: input.contentType,
    sizeBytes: input.sizeBytes,
    body: input.body,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.checksum === undefined ? {} : { checksum: { ...input.checksum } }),
    ...(input.metadata === undefined ? {} : { metadata: copyFileMetadata(input.metadata) }),
    ...(input.scan === undefined ? {} : { scan: copyFileScanResult(input.scan) }),
    ...(input.retention === undefined ? {} : { retention: copyFileRetentionPolicy(input.retention) }),
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
}): Result<FileAccessIntent, FileError> {
  if (!fileAccessOperations.includes(input.operation)) {
    return err(
      fileError({
        code: "FILE_INVALID_ACCESS_OPERATION",
        defaultMessage: "File access operation must use the approved operation vocabulary.",
        messageKey: "files.access.operation.invalid",
        params: { operation: input.operation },
      }),
    );
  }

  const metadata = input.metadata === undefined ? undefined : copyFileMetadataResult(input.metadata);
  if (metadata !== undefined && !metadata.ok) {
    return err(metadata.error);
  }

  return ok({
    fileId: input.fileId,
    operation: input.operation,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.expiresAt === undefined ? {} : { expiresAt: input.expiresAt }),
    ...(input.reason === undefined ? {} : { reason: input.reason }),
    ...(metadata === undefined ? {} : { metadata: metadata.value }),
  });
}

export function fileError(input: {
  readonly code: FileErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly details?: Readonly<Record<string, unknown>>;
}): FileError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}

export function inMemoryFileStorage<TBody = unknown>(storageOptions: {
  readonly now: ISODateTime;
  readonly storageKeyFor?: (input: PutFileInput<TBody>) => FileStorageKey;
}): InMemoryFileStorage<TBody> {
  const files = new Map<string, StoredFile>();
  const puts: FilePut<TBody>[] = [];

  return {
    async put(input, putOptions = {}) {
      const existing = files.get(input.id);
      if (existing !== undefined) {
        if ((putOptions.duplicateStrategy ?? "conflict") === "idempotent" && matchesIdempotentPut(existing, input)) {
          return ok(fileObject(existing));
        }

        return err(
          fileError({
            code: "FILE_ALREADY_EXISTS",
            defaultMessage: "File already exists.",
            messageKey: "files.already_exists",
            details: { fileId: input.id },
          }),
        );
      }

      const storageKey = storageOptions.storageKeyFor?.(input) ?? defaultStorageKeyFor(input.id);
      const storedFile = fileObject({
        id: input.id,
        fileName: input.fileName,
        contentType: input.contentType,
        sizeBytes: input.sizeBytes,
        storage: fileStorageRef({ key: storageKey }),
        createdAt: storageOptions.now,
        ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
        ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
        ...(input.checksum === undefined ? {} : { checksum: input.checksum }),
        ...(input.metadata === undefined ? {} : { metadata: input.metadata }),
        ...(input.scan === undefined ? {} : { scan: input.scan }),
        ...(input.retention === undefined ? {} : { retention: input.retention }),
      });
      files.set(input.id, storedFile);
      puts.push({
        input: copyPutFileInput(input),
        ...(Object.keys(putOptions).length === 0 ? {} : { options: copyFilePutOptions(putOptions) }),
        storedFile,
      });

      return ok(fileObject(storedFile));
    },

    async get(intent) {
      if (intent.operation !== "read") {
        return err(accessOperationDeniedError(intent, "read"));
      }

      const storedFile = files.get(intent.fileId);
      if (storedFile === undefined) {
        return err(
          fileError({
            code: "FILE_NOT_FOUND",
            defaultMessage: "File was not found.",
            messageKey: "files.not_found",
            details: { fileId: intent.fileId },
          }),
        );
      }

      const access = validateStoredFileAccess(storedFile, intent);
      if (!access.ok) {
        return err(access.error);
      }

      return ok(fileObject(storedFile));
    },

    async delete(intent) {
      if (intent.operation !== "delete") {
        return err(accessOperationDeniedError(intent, "delete"));
      }

      const storedFile = files.get(intent.fileId);
      if (storedFile === undefined) {
        return err(
          fileError({
            code: "FILE_NOT_FOUND",
            defaultMessage: "File was not found.",
            messageKey: "files.not_found",
            details: { fileId: intent.fileId },
          }),
        );
      }

      const access = validateStoredFileAccess(storedFile, intent);
      if (!access.ok) {
        return err(access.error);
      }

      files.delete(intent.fileId);
      return ok(undefined);
    },

    acceptedPuts() {
      return puts.map((put) => ({
        input: copyPutFileInput(put.input),
        ...(put.options === undefined ? {} : { options: copyFilePutOptions(put.options) }),
        storedFile: fileObject(put.storedFile),
      }));
    },

    storedFiles() {
      return [...files.values()].map(fileObject);
    },
  };
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

function copyPutFileInput<TBody>(input: PutFileInput<TBody>): PutFileInput<TBody> {
  return putFileInput(input);
}

function copyFilePutOptions(options: FilePutOptions): FilePutOptions {
  return {
    ...(options.duplicateStrategy === undefined ? {} : { duplicateStrategy: options.duplicateStrategy }),
  };
}

function copyFileScanResult(scan: FileScanResult): FileScanResult {
  return {
    status: scan.status,
    ...(scan.scannedAt === undefined ? {} : { scannedAt: scan.scannedAt }),
    ...(scan.scanner === undefined ? {} : { scanner: scan.scanner }),
    ...(scan.details === undefined ? {} : { details: copyFileMetadata(scan.details) }),
  };
}

function copyFileRetentionPolicy(retention: FileRetentionPolicy): FileRetentionPolicy {
  return fileRetentionPolicy(retention);
}

function copyFileMetadataResult<TValue extends FileMetadata>(value: TValue): Result<TValue, FileError> {
  try {
    return ok(copyFileMetadata(value));
  } catch (cause) {
    return err(
      fileError({
        code: "FILE_INVALID_METADATA",
        defaultMessage: "File metadata must be plain JSON-safe values.",
        messageKey: "files.metadata.invalid",
        cause,
      }),
    );
  }
}

function copyFileMetadata<TValue extends FileMetadata>(value: TValue): TValue {
  return Object.fromEntries(
    Object.entries(value).map(([key, nestedValue]) => [key, copyJsonValue(nestedValue, "file metadata")]),
  ) as TValue;
}

function accessOperationDeniedError(intent: FileAccessIntent, expectedOperation: FileAccessOperation): FileError {
  return fileError({
    code: "FILE_ACCESS_DENIED",
    defaultMessage: "File access intent does not allow this operation.",
    messageKey: "files.access.operation.denied",
    details: {
      fileId: intent.fileId,
      operation: intent.operation,
      expectedOperation,
    },
  });
}

function validateStoredFileAccess(storedFile: StoredFile, intent: FileAccessIntent): Result<void, FileError> {
  if (storedFile.tenantId !== undefined && intent.tenantId !== storedFile.tenantId) {
    return err(
      fileError({
        code: "FILE_ACCESS_DENIED",
        defaultMessage: "File access tenant does not match stored file tenant.",
        messageKey: "files.access.tenant.denied",
        details: {
          fileId: storedFile.id,
          tenantScoped: true,
        },
      }),
    );
  }

  return ok(undefined);
}

function matchesIdempotentPut<TBody>(storedFile: StoredFile, input: PutFileInput<TBody>): boolean {
  return (
    storedFile.id === input.id &&
    storedFile.fileName === input.fileName &&
    storedFile.contentType === input.contentType &&
    storedFile.sizeBytes === input.sizeBytes &&
    storedFile.tenantId === input.tenantId &&
    storedFile.correlationId === input.correlationId &&
    jsonEqual(storedFile.checksum, input.checksum) &&
    jsonEqual(storedFile.metadata, input.metadata) &&
    jsonEqual(storedFile.scan, input.scan) &&
    jsonEqual(storedFile.retention, input.retention)
  );
}

function jsonEqual(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function hasControlCharacter(value: string): boolean {
  return /[\u0000-\u001f\u007f]/.test(value);
}
