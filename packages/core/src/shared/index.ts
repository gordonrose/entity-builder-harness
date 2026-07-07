export type Brand<Value, Name extends string> = Value & { readonly __brand: Name };

export type EntityId<Name extends string = "EntityId"> = Brand<string, Name>;
export type CorrelationId = Brand<string, "CorrelationId">;
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
  return copyJsonValueInternal(value, label) as TValue;
}

const isoDateTimePattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

export function isoDateTime(value: string): Result<ISODateTime> {
  if (!isoDateTimePattern.test(value)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      defaultMessage: "Expected a valid ISO date-time string.",
      details: { value },
    });
  }

  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      defaultMessage: "Expected a valid ISO date-time string.",
      details: { value },
    });
  }

  return ok(brand<string, "ISODateTime">(new Date(timestamp).toISOString()));
}

export function isoDateTimeFromDate(value: Date): ISODateTime {
  return brand<string, "ISODateTime">(value.toISOString());
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

function copyJsonValueInternal(value: JsonValue, label: string): JsonValue {
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw new TypeError(`${label} must contain only finite numbers.`);
  }

  if (Array.isArray(value)) {
    return value.map((item) => copyJsonValueInternal(item, label));
  }

  if (value !== null && typeof value === "object") {
    if (Object.getPrototypeOf(value) !== Object.prototype) {
      throw new TypeError(`${label} must contain only plain objects.`);
    }

    return Object.fromEntries(
      Object.entries(value).map(([key, nestedValue]) => [key, copyJsonValueInternal(nestedValue, label)]),
    );
  }

  return value;
}
