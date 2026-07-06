import {
  correlationId,
  entityId,
  err,
  isErr,
  isOk,
  ok,
  requestContext,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type Result,
} from "../src/shared/index";

type TenantId = EntityId<"TenantId">;
type PrincipalId = EntityId<"PrincipalId">;

const tenantId = entityId<"TenantId">("tenant-123");
const principalId = entityId<"PrincipalId">("principal-456");
const requestId = correlationId("request-789");

const acceptedTenantId: TenantId = tenantId;
const acceptedPrincipalId: PrincipalId = principalId;
const acceptedCorrelationId: CorrelationId = requestId;

void acceptedTenantId;
void acceptedPrincipalId;
void acceptedCorrelationId;

// @ts-expect-error branded IDs with different names must not be interchangeable.
const rejectedTenantId: TenantId = principalId;
void rejectedTenantId;

// @ts-expect-error correlation IDs must not be accepted as entity IDs.
const rejectedEntityId: EntityId<"TenantId"> = requestId;
void rejectedEntityId;

const timestamp = "2026-07-06T12:00:00.000Z" as ISODateTime;
const context = requestContext({ correlationId: requestId, now: timestamp });

// @ts-expect-error request context must receive a CorrelationId, not an arbitrary entity ID.
requestContext({ correlationId: tenantId, now: timestamp });

const success: Result<string> = ok("ready");
const failure: Result<string> = err({ code: "TEST_FAILURE", message: "Expected failure." });

if (isOk(success)) {
  const value: string = success.value;
  void value;
}

if (isErr(failure)) {
  const code: string = failure.error.code;
  void code;
}

void context;
