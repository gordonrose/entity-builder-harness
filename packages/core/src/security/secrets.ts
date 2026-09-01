import { brand, type Brand } from "../shared/index";

export type SecretString = Brand<string, "SecretString">;

export function secretString(value: string): SecretString {
  assertNonEmpty("secret string", value);
  return brand<string, "SecretString">(value);
}

function assertNonEmpty(label: string, value: string): void {
  if (value.length === 0) {
    throw new TypeError(`${label} must be non-empty.`);
  }
}
