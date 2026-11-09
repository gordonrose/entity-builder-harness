import { correlationId, causationId, entityId, type CorrelationId, type CausationId, type EntityId } from "../../../../src/shared/index";


type TenantId = EntityId<"TenantId">;
type PrincipalId = EntityId<"PrincipalId">;

const tenantId = entityId<"TenantId">("tenant-123");
const principalId = entityId<"PrincipalId">("principal-456");
const requestId = correlationId("request-789");
const triggerId = causationId("event-456");

const acceptedTenantId: TenantId = tenantId;
const acceptedPrincipalId: PrincipalId = principalId;
const acceptedCorrelationId: CorrelationId = requestId;
const acceptedCausationId: CausationId = triggerId;

void acceptedTenantId;
void acceptedPrincipalId;
void acceptedCorrelationId;
void acceptedCausationId;

// @ts-expect-error branded IDs with different names must not be interchangeable.
const rejectedTenantId: TenantId = principalId;
void rejectedTenantId;

// @ts-expect-error correlation IDs must not be accepted as entity IDs.
const rejectedEntityId: EntityId<"TenantId"> = requestId;
void rejectedEntityId;
