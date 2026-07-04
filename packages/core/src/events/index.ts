import type { CorrelationId, EntityId, ISODateTime } from "../shared/index";
import type { TenantId } from "../tenancy/index";

export type EventId = EntityId<"EventId">;

export interface EventEnvelope<TPayload = unknown> {
  readonly id: EventId;
  readonly type: string;
  readonly version: number;
  readonly occurredAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly payload: TPayload;
}

export interface EventBus {
  publish(events: readonly EventEnvelope[]): Promise<void>;
}
