import type { DiagnosticDescriptor, DiagnosticRecord } from "../diagnostics/index";
import { attachCoreDiagnosticRecord, coreDateRecord, coreDateNormalizationRecord, coreJsonRecord } from "./diagnostics";
export * from "./diagnostics";

export type Brand<Value, Name extends string> = Value & { readonly __brand: Name };

export type EntityId<Name extends string = "EntityId"> = Brand<string, Name>;
export type CorrelationId = Brand<string, "CorrelationId">;
export type CausationId = Brand<string, "CausationId">;
export type ISODateTime = Brand<string, "ISODateTime">;
export type MessageKey = Brand<string, "MessageKey">;
export type MessageParamValue = string | number | boolean | null;
export type MessageParams = Readonly<Record<string, MessageParamValue>>;
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | readonly JsonValue[]
  | { readonly [key: string]: JsonValue };

export interface MessageDescriptor {
  readonly code: string;
  readonly defaultMessage: string;
  readonly messageKey?: MessageKey;
  readonly params?: MessageParams;
}

export type Result<Value, Failure = CoreError> =
  | { readonly ok: true; readonly value: Value }
  | { readonly ok: false; readonly error: Failure };

export interface CoreError extends MessageDescriptor {
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  /** Validated detail is separate from legacy primitive diagnostic facts. */
  readonly diagnosticRecord?: DiagnosticRecord;
  /** Bounded, independently schema-validated observations; never raw causes. */
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly details?: Readonly<Record<string, unknown>>;
}

export function brand<Value, Name extends string>(value: Value): Brand<Value, Name> {
  return value as Brand<Value, Name>;
}

export function entityId<Name extends string>(value: string): EntityId<Name> {
  return brand<string, Name>(value);
}

export function correlationId(value: string): CorrelationId {
  return brand<string, "CorrelationId">(value);
}

export function causationId(value: string): CausationId {
  return brand<string, "CausationId">(value);
}

export function messageKey(value: string): MessageKey {
  return brand<string, "MessageKey">(value);
}

export function messageDescriptor(input: {
  readonly code: string;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
}): MessageDescriptor {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
  };
}

export function copyJsonValue<TValue extends JsonValue>(value: TValue, label = "JSON value"): TValue {
  return copyJsonValueInternal(value, label, 0, []) as TValue;
}

const isoDateTimePattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

export function isoDateTime(value: string): Result<ISODateTime> {
  if (!isoDateTimePattern.test(value)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      defaultMessage: "Expected a valid ISO date-time string.",
      details: { value },
      diagnosticRecord: coreDateRecord("invalid-format"),
    });
  }

  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      defaultMessage: "Expected a valid ISO date-time string.",
      details: { value },
      diagnosticRecord: coreDateRecord("parse-rejected"),
    });
  }

  try { return ok(brand<string, "ISODateTime">(new Date(timestamp).toISOString())); }
  catch (error) { throw attachCoreDiagnosticRecord(error, coreDateNormalizationRecord("string-normalization")); }
}

export function isoDateTimeFromDate(value: Date): ISODateTime {
  try { return brand<string, "ISODateTime">(value.toISOString()); }
  catch (error) { throw attachCoreDiagnosticRecord(error, coreDateNormalizationRecord("date-normalization")); }
}

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

export interface Clock {
  now(): Date;
}

export const systemClock: Clock = {
  now: () => new Date(),
};

export function fixedClock(now: Date): Clock {
  return {
    now: () => new Date(now.getTime()),
  };
}

export interface RequestContext {
  readonly correlationId: CorrelationId;
  readonly now: ISODateTime;
}

export function requestContext(input: { readonly correlationId: CorrelationId; readonly now: Date | ISODateTime }): RequestContext {
  return {
    correlationId: input.correlationId,
    now: input.now instanceof Date ? isoDateTimeFromDate(input.now) : input.now,
  };
}

const nativeJsonArrayMap = Array.prototype.map;
const applyJsonArrayMap = Reflect.apply;

/** Retain one method read, the original receiver and the existing custom-map policy. */
function mapWithJsonPosition<TValue, TResult>(value: readonly TValue[], visit: (item: TValue, position: number | undefined) => TResult): TResult[] {
  const map: unknown = value.map;
  const callback = (item: TValue, claimedPosition: unknown = undefined): TResult => visit(item,
    map === nativeJsonArrayMap && typeof claimedPosition === "number" && Number.isSafeInteger(claimedPosition) && claimedPosition >= 0 ? claimedPosition : undefined);
  if (typeof map !== "function") {
    // Use the same native call expression for a noncallable cached method, without
    // another read of the supplied array's getter.
    const value = { map: map as (visitItem: typeof callback) => TResult[] };
    return value.map(callback);
  }
  return applyJsonArrayMap(map, value, [callback]) as TResult[];
}

function jsonCopyFailure(message: string, reason: "non-finite-number" | "non-plain-object", depth: number, path: readonly number[], locationUnavailable: boolean): TypeError {
  const error = new TypeError(message);
  try { return attachCoreDiagnosticRecord(error, coreJsonRecord(reason, depth, path, locationUnavailable)); }
  catch { return error; }
}

function copyJsonValueInternal(value: JsonValue, label: string, depth: number, path: readonly number[], locationUnavailable = false): JsonValue {
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw jsonCopyFailure(`${label} must contain only finite numbers.`, "non-finite-number", depth, path, locationUnavailable);
  }

  if (Array.isArray(value)) {
    return mapWithJsonPosition(value, (item, index) => copyJsonValueInternal(item, label, depth + 1,
      !locationUnavailable && index !== undefined && path.length < 16 ? [...path, index] : path,
      locationUnavailable || index === undefined));
  }

  if (value !== null && typeof value === "object") {
    if (Object.getPrototypeOf(value) !== Object.prototype) {
      throw jsonCopyFailure(`${label} must contain only plain objects.`, "non-plain-object", depth, path, locationUnavailable);
    }

    return Object.fromEntries(
      mapWithJsonPosition(Object.entries(value), ([key, nestedValue], index) => [key, copyJsonValueInternal(nestedValue, label, depth + 1,
        !locationUnavailable && index !== undefined && path.length < 16 ? [...path, index] : path,
        locationUnavailable || index === undefined)]),
    );
  }

  return value;
}
