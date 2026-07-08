import { messageDescriptor } from "../src/shared/index";
import {
  dataClassification,
  fixedSecurityPolicyEvaluator,
  hash,
  secretString,
  securityPolicyAllowed,
  securityPolicyDenied,
  securityPolicyId,
  securityPolicyViolation,
  type DataClassification,
  type DataSensitivity,
  type Hash,
  type HashAlgorithm,
  type HashValue,
  type Hasher,
  type SecretString,
  type SecurityPolicyDecision,
  type SecurityPolicyEvaluator,
  type SecurityPolicyEvidence,
  type SecurityPolicyEvidenceValue,
  type SecurityPolicyId,
  type SecurityPolicyViolation,
  type SecurityPolicyViolationCode,
  type SensitiveValueKind,
} from "../src/security/index";

const secret: SecretString = secretString("s3cr3t");
const storedHash: Hash = hash({ algorithm: "argon2id", value: "$argon2id$hash" });
const algorithm: HashAlgorithm = storedHash.algorithm;
const hashValue: HashValue = storedHash.value;
const policyId: SecurityPolicyId = securityPolicyId("platform.security.redaction");
const violationCode: SecurityPolicyViolationCode = "SECURITY_POLICY_DENIED";
const evidenceValue: SecurityPolicyEvidenceValue = { nested: ["safe", true] };
const evidence: SecurityPolicyEvidence = { matchedPolicy: "platform.security.redaction", value: evidenceValue };
const kind: SensitiveValueKind = "credential";
const sensitivity: DataSensitivity = "secret";
const classification: DataClassification = dataClassification({
  kind,
  sensitivity,
  reason: messageDescriptor({
    code: "SECURITY_CLASSIFICATION",
    defaultMessage: "Value is security-sensitive.",
  }),
});
const violation: SecurityPolicyViolation = securityPolicyViolation({
  code: violationCode,
  defaultMessage: "Security policy denied the operation.",
  details: evidence,
});
const allowed: SecurityPolicyDecision = securityPolicyAllowed({ policyId, evidence });
const denied: SecurityPolicyDecision = securityPolicyDenied({ policyId, violation, evidence });
const evaluator: SecurityPolicyEvaluator<{ readonly value: SecretString }> = fixedSecurityPolicyEvaluator(allowed);
const hasher: Hasher = {
  hash: async () => storedHash,
  verify: async (value, expected) => value === secret && expected.value === storedHash.value,
};

void algorithm;
void hashValue;
void classification;
void denied;
void evaluator;
void hasher;

// @ts-expect-error secret strings must be explicitly branded.
const invalidSecret: SecretString = "s3cr3t";
void invalidSecret;

// @ts-expect-error hash algorithms must be explicitly branded.
const invalidAlgorithm: HashAlgorithm = "argon2id";
void invalidAlgorithm;

// @ts-expect-error hash values must be explicitly branded.
const invalidHashValue: HashValue = "$argon2id$hash";
void invalidHashValue;

// @ts-expect-error security policy ids must be explicitly branded.
const invalidPolicyId: SecurityPolicyId = "platform.security.redaction";
void invalidPolicyId;

// @ts-expect-error security policy violation codes are constrained.
securityPolicyViolation({ code: "PASSWORD_TOO_SHORT", defaultMessage: "Password too short." });

// @ts-expect-error sensitive value kinds are constrained.
const invalidKind: SensitiveValueKind = "session";
void invalidKind;

// @ts-expect-error sensitivity labels are constrained.
const invalidSensitivity: DataSensitivity = "top-secret";
void invalidSensitivity;

// @ts-expect-error security policy evidence must stay plain and serializable.
const invalidEvidenceValue: SecurityPolicyEvidenceValue = new Date();
void invalidEvidenceValue;

// @ts-expect-error denied security policy decisions must include a violation.
const invalidDeniedDecision: SecurityPolicyDecision = { allowed: false };
void invalidDeniedDecision;

// @ts-expect-error hashers must receive branded secrets.
hasher.hash("s3cr3t");

// @ts-expect-error policy evaluators preserve input type.
evaluator.evaluate({ value: "s3cr3t" });
