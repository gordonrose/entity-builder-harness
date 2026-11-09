import type { Brand } from "../contract/branding";

export type EntityId<Name extends string = "EntityId"> = Brand<string, Name>;
export type CorrelationId = Brand<string, "CorrelationId">;
export type CausationId = Brand<string, "CausationId">;
