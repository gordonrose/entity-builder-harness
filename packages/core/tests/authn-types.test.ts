import {
  fixedAuthenticator,
  principal,
  principalId,
  type AuthenticationResult,
  type Authenticator,
  type Principal,
  type PrincipalClaims,
  type PrincipalClaimValue,
  type PrincipalId,
  type PrincipalType,
} from "../src/authn/index";
import { tenantId } from "../src/tenancy/index";

const actorId: PrincipalId = principalId("principal-123");
const actorType: PrincipalType = "user";
const claims: PrincipalClaims = {
  email: "person@example.test",
  provider: "test-idp",
  profile: { locale: "en-GB" },
  roles: ["viewer"],
};
const nestedClaimValue: PrincipalClaimValue = {
  profile: {
    locale: "en-GB",
    flags: [true, false],
  },
};

const actor: Principal = principal({
  id: actorId,
  type: actorType,
  subject: "oidc:test-idp:subject-123",
  currentTenantId: tenantId("tenant-123"),
  claims,
  scopes: ["profile:read"],
});

const service: Principal = principal({
  id: principalId("service-rag-builder"),
  type: "service",
  subject: "service:rag-builder",
});

const result: AuthenticationResult = actor;
const missing: AuthenticationResult = null;
const authenticator: Authenticator<{ readonly token: string }> = fixedAuthenticator(actor);

void actor;
void service;
void result;
void missing;
void authenticator;
void nestedClaimValue;

// @ts-expect-error principal IDs must be explicitly branded.
principal({ id: "principal-123", type: "user", subject: "subject-123" });

// @ts-expect-error principal type is intentionally constrained.
principal({ id: actorId, type: "robot", subject: "subject-123" });

// @ts-expect-error current tenant context must receive a TenantId, not a PrincipalId.
principal({ id: actorId, type: "user", subject: "subject-123", currentTenantId: actorId });

// @ts-expect-error tenantId is ambiguous; use currentTenantId for the active tenant context.
principal({ id: actorId, type: "user", subject: "subject-123", tenantId: tenantId("tenant-123") });

// @ts-expect-error authentication result is either a principal or null.
const invalidResult: AuthenticationResult = undefined;
void invalidResult;

// @ts-expect-error principal claims must stay provider-neutral and serializable.
const invalidClaimValue: PrincipalClaimValue = new Date();
void invalidClaimValue;
