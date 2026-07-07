import { deepEqual, equal } from "node:assert/strict";
import {
  fixedAuthenticator,
  principal,
  principalId,
} from "../src/authn/index";
import { tenantId } from "../src/tenancy/index";

async function main(): Promise<void> {
  const actorId = principalId("principal-123");
  const currentTenantId = tenantId("tenant-123");
  const claims: Record<string, unknown> = {
    email: "person@example.test",
    provider: "test-idp",
  };
  const scopes = ["profile:read", "session:refresh"];

  const actor = principal({
    id: actorId,
    type: "user",
    subject: "oidc:test-idp:subject-123",
    currentTenantId,
    claims,
    scopes,
  });

  deepEqual(actor, {
    id: "principal-123",
    type: "user",
    subject: "oidc:test-idp:subject-123",
    currentTenantId: "tenant-123",
    claims: {
      email: "person@example.test",
      provider: "test-idp",
    },
    scopes: ["profile:read", "session:refresh"],
  });

  claims.email = "changed@example.test";
  scopes.push("changed:scope");
  equal(actor.claims.email, "person@example.test");
  deepEqual(actor.scopes, ["profile:read", "session:refresh"]);

  const service = principal({
    id: principalId("service-rag-builder"),
    type: "service",
    subject: "service:rag-builder",
  });
  deepEqual(service, {
    id: "service-rag-builder",
    type: "service",
    subject: "service:rag-builder",
    claims: {},
  });

  const authenticator = fixedAuthenticator<{ readonly token: string }>(actor);
  const authenticated = await authenticator.authenticate({ token: "opaque-token" });
  deepEqual(authenticated, actor);

  const unauthenticated = await fixedAuthenticator<{ readonly token: string }>(null).authenticate({
    token: "invalid-token",
  });
  equal(unauthenticated, null);
}

main()
  .then(() => {
    console.log("packages/core authn runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
