import { deepEqual, equal, throws } from "node:assert/strict";
import { principal, principalId } from "../src/authn/index";
import {
  allow,
  authorizationRelation,
  authorizationRequest,
  deny,
  fixedAuthorizer,
  permission,
  resourceRef,
} from "../src/authz/index";
import { messageDescriptor } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

async function main(): Promise<void> {
  const currentTenantId = tenantId("tenant-123");
  const actor = principal({
    id: principalId("principal-123"),
    type: "user",
    subject: "oidc:test-idp:subject-123",
    currentTenantId,
    claims: { email: "person@example.test" },
  });

  const deal = resourceRef({ type: "deal", id: "deal-123" });
  const conversation = resourceRef({
    type: "conversation",
    id: "conversation-456",
    parent: deal,
  });
  const team = resourceRef({ type: "team", id: "team-x" });
  const principalNode = resourceRef({ type: "principal", id: actor.id });

  const request = authorizationRequest({
    principal: actor,
    tenantId: currentTenantId,
    permission: permission("conversation", "read"),
    resource: conversation,
    relations: [
      authorizationRelation({ subject: principalNode, relation: "member", object: team }),
      authorizationRelation({ subject: team, relation: "assigned", object: deal }),
    ],
    attributes: {
      principal: { region: "EU", clearance: "confidential" },
      tenant: { plan: "team", region: "EU" },
      resource: { archived: false, sensitivity: "confidential" },
      environment: { channel: "web", businessHours: true },
    },
    facts: {
      policyFamily: "deal-access",
    },
  });

  deepEqual(request.resource, {
    type: "conversation",
    id: "conversation-456",
    parent: {
      type: "deal",
      id: "deal-123",
    },
  });
  equal(request.permission, "conversation:read");
  equal(request.tenantId, "tenant-123");
  equal(request.attributes?.resource?.archived, false);
  equal(request.relations?.[0]?.relation, "member");

  const allowed = allow({
    evidence: {
      policyId: "deal-team-access",
      matchedRelation: "team.assigned",
    },
  });
  deepEqual(allowed, {
    allowed: true,
    evidence: {
      policyId: "deal-team-access",
      matchedRelation: "team.assigned",
    },
  });

  throws(() => permission("", "read"), /Permission resource/);
  throws(() => permission("conversation", ""), /Permission action/);
  throws(() => permission("deal:conversation", "read"), /Permission resource/);
  throws(() => permission("conversation", "read all"), /Permission action/);

  const mutableEvidence = {
    matched: { relation: "team.assigned" },
    tags: ["rebac"],
  };
  const copiedEvidence = allow({ evidence: mutableEvidence });
  mutableEvidence.matched.relation = "changed";
  mutableEvidence.tags.push("changed");
  deepEqual(copiedEvidence.evidence, {
    matched: { relation: "team.assigned" },
    tags: ["rebac"],
  });

  const denied = deny({
    reason: messageDescriptor({
      code: "AUTHZ_DENIED",
      defaultMessage: "You do not have access to this resource.",
      messageKey: "authz.denied",
    }),
    evidence: {
      policyId: "deal-team-access",
      requiredRelation: "team.assigned",
    },
  });
  equal(denied.allowed, false);
  if (denied.reason === undefined) {
    throw new Error("Expected denied decision to include a reason.");
  }
  equal(denied.reason.code, "AUTHZ_DENIED");
  equal(denied.evidence?.requiredRelation, "team.assigned");

  const authorizer = fixedAuthorizer(allowed);
  const decision = await authorizer.decide(request);
  deepEqual(decision, allowed);
}

main()
  .then(() => {
    console.log("packages/core authz runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
