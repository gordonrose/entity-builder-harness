import { brand, type Brand } from "../shared/index";
import type { SecretString } from "./secrets";
import { attachCoreDiagnosticRecord } from "../shared/index";
import { coreSecurityPrimitiveRecord } from "./diagnostics";

export type HashAlgorithm = Brand<string, "HashAlgorithm">;
export type HashValue = Brand<string, "HashValue">;

export interface Hash {
  readonly algorithm: HashAlgorithm;
  readonly value: HashValue;
}

export interface Hasher {
  hash(value: SecretString): Promise<Hash>;
  verify(value: SecretString, expected: Hash): Promise<boolean>;
}

export function hashAlgorithm(value: string): HashAlgorithm {
  assertToken("hash algorithm", value);
  return brand<string, "HashAlgorithm">(value);
}

export function hashValue(value: string): HashValue {
  assertToken("hash value", value);
  return brand<string, "HashValue">(value);
}

export function hash(input: { readonly algorithm: string | HashAlgorithm; readonly value: string | HashValue }): Hash {
  return {
    algorithm: hashAlgorithm(input.algorithm),
    value: hashValue(input.value),
  };
}

function assertNonEmpty(label: "hash algorithm" | "hash value", value: string): void {
  if (value.length === 0) {
    throw attachCoreDiagnosticRecord(new TypeError(`${label} must be non-empty.`), coreSecurityPrimitiveRecord(label === "hash algorithm" ? "hash-algorithm" : "hash-value", "empty"));
  }
}

function assertToken(label: "hash algorithm" | "hash value", value: string): void {
  assertNonEmpty(label, value);

  const field = label === "hash algorithm" ? "hash-algorithm" : "hash-value";
  if (value.trim() !== value) throw attachCoreDiagnosticRecord(new TypeError(`${label} must not contain whitespace.`), coreSecurityPrimitiveRecord(field, "surrounding-whitespace"));
  if (/\s/.test(value)) throw attachCoreDiagnosticRecord(new TypeError(`${label} must not contain whitespace.`), coreSecurityPrimitiveRecord(field, "whitespace"));
}
