import type { SecurityTrustMaterialFailureDetail, SecurityPeerIdentityFailureDetail, SecurityPeerTrustFailureDetail } from "../../../src/security/index";
import type { SecurityOperationReason } from "../../../src/security/index";
const tokenReason: SecurityOperationReason<"token"> = "expired";
// @ts-expect-error token reasons do not include CORS observations
const wrongOperation: SecurityOperationReason<"token"> = "origin-missing";
void [tokenReason, wrongOperation];

const content: SecurityTrustMaterialFailureDetail = { phase: "certificate-content-parsing", reason: "no-certificate-blocks", effect: "not-assessed" };
const identity: SecurityPeerIdentityFailureDetail = { phase: "peer-identity-verification", reason: "hostname-mismatch", effect: "not-assessed" };
const trust: SecurityPeerTrustFailureDetail = { phase: "peer-trust-verification", reason: "expired", effect: "not-assessed" };
void [content, identity, trust];
// @ts-expect-error parsing does not establish certificate expiry
const invalidContent: SecurityTrustMaterialFailureDetail = { ...content, reason: "expired" };
// @ts-expect-error peer identity is not trust-chain verification
const invalidIdentity: SecurityPeerIdentityFailureDetail = { ...identity, phase: "peer-trust-verification" };
// @ts-expect-error security observations do not establish application-operation effects
const invalidEffect: SecurityPeerTrustFailureDetail = { ...trust, effect: "not-started" };
void [invalidContent, invalidIdentity, invalidEffect];
