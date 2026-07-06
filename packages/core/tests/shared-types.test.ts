import {
  correlationId,
  entityId,
  err,
  isErr,
  isOk,
  messageDescriptor,
  messageKey,
  ok,
  requestContext,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type MessageDescriptor,
  type MessageKey,
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
const acceptedMessageKey: MessageKey = messageKey("validation.required");
const acceptedMessageDescriptor: MessageDescriptor = messageDescriptor({
  code: "VALIDATION_REQUIRED",
  defaultMessage: "Field is required.",
  messageKey: acceptedMessageKey,
  params: { field: "email", minimum: 1, required: true, optional: null },
});

void acceptedTenantId;
void acceptedPrincipalId;
void acceptedCorrelationId;
void acceptedMessageKey;
void acceptedMessageDescriptor;

// @ts-expect-error message descriptors must keep params JSON-primitive and localization-friendly.
messageDescriptor({ code: "BAD_PARAM", defaultMessage: "Bad param.", params: { nested: { value: "nope" } } });

// @ts-expect-error message descriptors require fallback/debug text for untranslated contexts.
messageDescriptor({ code: "MISSING_DEFAULT_MESSAGE" });

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
const failure: Result<string> = err({ code: "TEST_FAILURE", defaultMessage: "Expected failure." });

if (isOk(success)) {
  const value: string = success.value;
  void value;
}

if (isErr(failure)) {
  const code: string = failure.error.code;
  void code;
}

void context;
