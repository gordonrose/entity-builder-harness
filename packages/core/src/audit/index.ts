import type { PrincipalId } from "../authn/index";
import type { CorrelationId, ISODateTime } from "../shared/index";
import type { TenantId } from "../tenancy/index";

export interface AuditEvent {
  readonly type: string;
  readonly actorId?: PrincipalId;
  readonly tenantId?: TenantId;
  readonly occurredAt: ISODateTime;
  readonly correlationId?: CorrelationId;
  readonly target?: string;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface AuditRecorder {
  record(event: AuditEvent): Promise<void>;
}
