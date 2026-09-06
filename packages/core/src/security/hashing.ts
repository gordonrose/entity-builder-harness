import { brand, type Brand } from "../shared/index";
import type { SecretString } from "./secrets";

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

function assertNonEmpty(label: string, value: string): void {
  if (value.length === 0) {
    throw new TypeError(`${label} must be non-empty.`);
  }
}

function assertToken(label: string, value: string): void {
  assertNonEmpty(label, value);

  if (value.trim() !== value || /\s/.test(value)) {
    throw new TypeError(`${label} must not contain whitespace.`);
  }
}
