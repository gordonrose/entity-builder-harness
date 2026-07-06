export type Brand<Value, Name extends string> = Value & { readonly __brand: Name };

export type EntityId<Name extends string = "EntityId"> = Brand<string, Name>;
export type CorrelationId = Brand<string, "CorrelationId">;
export type ISODateTime = Brand<string, "ISODateTime">;

export type Result<Value, Failure = CoreError> =
  | { readonly ok: true; readonly value: Value }
  | { readonly ok: false; readonly error: Failure };

export interface CoreError {
  readonly code: string;
  readonly message: string;
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

export function isoDateTime(value: string): Result<ISODateTime> {
  const timestamp = Date.parse(value);

  if (Number.isNaN(timestamp)) {
    return err({
      code: "INVALID_ISO_DATE_TIME",
      message: "Expected a valid ISO date-time string.",
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
