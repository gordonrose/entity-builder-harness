import type { CoreError } from "./errors";

export type Result<Value, Failure = CoreError> =
  | { readonly ok: true; readonly value: Value }
  | { readonly ok: false; readonly error: Failure };

export function ok<Value>(value: Value): Result<Value, never> {
  return { ok: true, value };
}

export function err<Failure = CoreError>(error: Failure): Result<never, Failure> {
  return { ok: false, error };
}

export function isOk<Value, Failure>(result: Result<Value, Failure>): result is { readonly ok: true; readonly value: Value } {
  return result.ok;
}

export function isErr<Value, Failure>(result: Result<Value, Failure>): result is { readonly ok: false; readonly error: Failure } {
  return !result.ok;
}
