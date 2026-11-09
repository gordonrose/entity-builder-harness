import { brand } from "../contract/branding";
import type { EntityId, CorrelationId, CausationId } from "./contracts";

export function entityId<Name extends string>(value: string): EntityId<Name> {
  return brand<string, Name>(value);
}

export function correlationId(value: string): CorrelationId {
  return brand<string, "CorrelationId">(value);
}

export function causationId(value: string): CausationId {
  return brand<string, "CausationId">(value);
}
