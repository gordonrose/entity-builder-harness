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

export interface Clock {
  now(): Date;
}

export const systemClock: Clock = {
  now: () => new Date(),
};

export interface RequestContext {
  readonly correlationId: CorrelationId;
  readonly now: ISODateTime;
}
