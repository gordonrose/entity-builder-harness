import { principal, principalId } from "../src/authn/index";
import {
  allow,
  authorizationRequest,
  deny,
  fixedAuthorizer,
  permission,
  resourceRef,
  type AuthorizationAttributes,
  type AuthorizationDecision,
  type AuthorizationRequest,
  type AuthorizationValue,
  type Authorizer,
  type Permission,
  type ResourceRef,
} from "../src/authz/index";
import { messageDescriptor } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

const actor = principal({
  id: principalId("principal-123"),
  type: "user",
  subject: "oidc:test-idp:subject-123",
});
const currentTenantId = tenantId("tenant-123");
const readDeal: Permission = permission("deal", "read");
const resource: ResourceRef = resourceRef({ type: "deal", id: "deal-123" });
const attributes: AuthorizationAttributes = {
  principal: { region: "EU" },
  resource: { archived: false, score: 12 },
  environment: { channel: "web", tags: ["trusted", "interactive"] },
};

const request: AuthorizationRequest = authorizationRequest({
  principal: actor,
  tenantId: currentTenantId,
  permission: readDeal,
  resource,
  attributes,
});

const allowed: AuthorizationDecision = allow();
const denied: AuthorizationDecision = deny({
  reason: messageDescriptor({
    code: "AUTHZ_DENIED",
    defaultMessage: "You do not have access to this resource.",
  }),
});
const authorizer: Authorizer = fixedAuthorizer(allowed);
const nestedValue: AuthorizationValue = {
  region: "EU",
  tags: ["trusted"],
  flags: { archived: false },
};

void request;
void denied;
void authorizer;
void nestedValue;

// @ts-expect-error permissions should be created as resource:action strings.
const invalidPermission: Permission = "deal";
void invalidPermission;

// @ts-expect-error authorization requires a Principal from authn.
authorizationRequest({ principal: "principal-123", permission: readDeal });

// @ts-expect-error authorization tenant context must receive a TenantId.
authorizationRequest({ principal: actor, tenantId: "tenant-123", permission: readDeal });

// @ts-expect-error resource references need a type and id.
resourceRef({ type: "deal" });

// @ts-expect-error ABAC values must stay plain and serializable.
const invalidAttributeValue: AuthorizationValue = new Date();
void invalidAttributeValue;

// @ts-expect-error deny decisions need a translation-ready reason.
deny({});

// @ts-expect-error denied authorization decisions must include a reason even without using the helper.
const invalidDeniedDecision: AuthorizationDecision = { allowed: false };
void invalidDeniedDecision;
