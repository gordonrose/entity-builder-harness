import { deepEqual, equal, throws } from "node:assert/strict";
import { messageDescriptor } from "../src/shared/index";
import {
  dataClassification,
  fixedSecurityPolicyEvaluator,
  hash,
  hashAlgorithm,
  hashValue,
  secretString,
  securityPolicyAllowed,
  securityPolicyDenied,
  securityPolicyId,
  securityPolicyViolation,
  type Hasher,
} from "../src/security/index";

async function main(): Promise<void> {
  const secret = secretString("correct horse battery staple");
  equal(secret, "correct horse battery staple");
  throws(() => secretString(""), /secret string must be non-empty/);

  const storedHash = hash({
    algorithm: "argon2id",
    value: "$argon2id$v=19$m=65536,t=3,p=4$hash",
  });
  equal(storedHash.algorithm, "argon2id");
  equal(storedHash.value, "$argon2id$v=19$m=65536,t=3,p=4$hash");
  throws(() => hashAlgorithm("argon 2"), /hash algorithm must not contain whitespace/);
  throws(() => hashValue(""), /hash value must be non-empty/);

  const hasher: Hasher = {
    hash: async () => storedHash,
    verify: async (value, expected) => value === secret && expected.value === storedHash.value,
  };
  deepEqual(await hasher.hash(secret), storedHash);
  equal(await hasher.verify(secret, storedHash), true);

  const reason = messageDescriptor({
    code: "SECURITY_REQUIRES_REDACTION",
    defaultMessage: "This value must not cross the boundary in raw form.",
    messageKey: "security.redaction.required",
  });
  const classification = dataClassification({
    kind: "token",
    sensitivity: "secret",
    reason,
  });
  deepEqual(classification, {
    kind: "token",
    sensitivity: "secret",
    reason,
  });
  throws(
    () =>
      dataClassification({
        kind: "session" as "token",
        sensitivity: "secret",
      }),
    /sensitive value kind must be one of/,
  );

  const details = {
    field: "authorization",
    nested: {
      redacted: true,
    },
    tags: ["token", "header"],
  };
  const violation = securityPolicyViolation({
    code: "SECURITY_SENSITIVE_VALUE_REJECTED",
    defaultMessage: "Sensitive value cannot be exported in raw form.",
    messageKey: "security.sensitive_value.rejected",
    details,
  });
  details.nested.redacted = false;
  details.tags.push("mutated");
  deepEqual(violation.details, {
    field: "authorization",
    nested: {
      redacted: true,
    },
    tags: ["token", "header"],
  });
  throws(
    () =>
      securityPolicyViolation({
        code: "SECURITY_POLICY_DENIED",
        defaultMessage: "Policy denied the operation.",
        details: {
          score: Number.NaN,
        },
      }),
    /security policy evidence must contain only finite numbers/,
  );

  const policyId = securityPolicyId("platform.logging.redaction");
  const allowedEvidence = { matchedPolicy: "safe-summary" };
  const allowed = securityPolicyAllowed({ policyId, evidence: allowedEvidence });
  allowedEvidence.matchedPolicy = "changed";
  deepEqual(allowed, {
    allowed: true,
    policyId: "platform.logging.redaction",
    evidence: {
      matchedPolicy: "safe-summary",
    },
  });

  const denied = securityPolicyDenied({
    policyId,
    violation,
    evidence: {
      field: "authorization",
    },
  });
  equal(denied.allowed, false);
  if (denied.allowed) {
    throw new Error("Expected security policy to be denied.");
  }
  equal(denied.violation.code, "SECURITY_SENSITIVE_VALUE_REJECTED");

  const evaluator = fixedSecurityPolicyEvaluator<{ readonly field: string }>(denied);
  const decision = await evaluator.evaluate({ field: "authorization" });
  deepEqual(decision, denied);

  throws(() => securityPolicyId("platform logging"), /security policy id must not contain whitespace/);
}

main()
  .then(() => {
    console.log("packages/core security runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
