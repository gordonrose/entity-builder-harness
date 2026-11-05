export {
  authzMappingPermissions,
  authorizePlatformPermissions,
  permissionsFromClaims,
  observePermissionsFromClaims,
  validateAuthzMappingPermissions,
} from "./authorization";
export type {
  PlatformAuthzPermissionMapping,
  PlatformClaimPermissionMapping,
  PlatformClaimValuePermissionMapping,
} from "./authorization";
export {
  createJwtBearerAuthenticationHook,
  observeBearerTokenFromHeaders,
  denyByDefaultAuthenticationResult,
  principalFromPlatformAuthenticationResult,
} from "./authentication";
export type {
  JwtBearerAuthenticationHookOptions,
  PlatformAuthenticationHook,
  PlatformAuthenticationRequest,
  PlatformAuthenticationResult,
  PlatformPrincipalMissingAttribute,
  PlatformPrincipalDiagnosticContext,
  PlatformPrincipalDiagnosticOptions,
} from "./authentication";
export type { PlatformSecurityError, PlatformSecurityErrorCode } from "./errors";
export {
  corsPolicyForOrigin,
  corsPolicyForRequestOrigin,
  observeCorsPolicyForRequestOrigin,
  createPlatformSecurityHeaders,
} from "./headers";
export type { PlatformCorsPolicy, PlatformSecurityHeadersOptions } from "./headers";
export { createJwksJwtVerifier } from "./jwt";
export { validateJwtVerifierConfiguration, jwtDefaultClockSkewSeconds, jwtConfigurationDiagnostic, jwtConfigurationDiagnosticCatalog, jwtConfigurationError, isJwtConfigurationError } from "./jwt-configuration/index";
export type { CheckedJwtVerifierConfiguration, JwtConfigurationFailure } from "./jwt-configuration/index";
export type {
  PlatformJsonWebKey,
  PlatformJwks,
  PlatformJwksFetcher,
  PlatformJwtClaimRequirement,
  PlatformJwtClaimScalar,
  PlatformJwtExactClaimRequirement,
  PlatformJwtOneOfClaimRequirement,
  PlatformJwtVerificationOptions,
  PlatformJwtVerifier,
  PlatformVerifiedJwt,
} from "./jwt";
export {
  createInMemoryPlatformRateLimiter,
  platformRateLimitError,
  platformRateLimitKey,
  observePlatformRateLimitCheck,
} from "./rate-limiting";
export type {
  InMemoryPlatformRateLimiterOptions,
  InMemoryPlatformRateLimiter,
  PlatformRateLimitDecision,
  PlatformRateLimitKeyInput,
  PlatformRateLimiter,
} from "./rate-limiting";
export { validateCertificateAuthorityContent } from "./certificates";
export type { CertificateAuthorityContentObservation, CertificateAuthorityContentError } from "./certificates";
export {
  platformSecurityDiagnosticCatalog,
  securityTrustMaterialDiagnostic, securityPeerIdentityDiagnostic, securityPeerTrustDiagnostic,
  securityTrustMaterialDiagnosticRecord, securityPeerIdentityDiagnosticRecord, securityPeerTrustDiagnosticRecord,
} from "./diagnostics";
export { securityCertificateBlockDiagnostic, securityCertificateBlockDiagnosticRecord } from "./diagnostics";
export { securityOperationDiagnosticRecord, observeSecurityFailure, observedSecurityPeerFailures, securityFailureDiagnosticRecord, securityDiagnosticRecordsFrom, securityOwnedHeaderReferences, securityConfigurationPredicateRecord, securityRateLimitClockFailureRecord } from "./diagnostics";
export type { SecurityObservationOptions } from "./diagnostics";
export { securityPrincipalBoundaryDiagnostic, securityPrincipalBoundaryDiagnosticRecord } from "./diagnostics";
export type { SecurityPrincipalBoundaryDetail } from "./diagnostics";

export { assertPlatformRateLimitPositiveInteger, securityRateLimitPositiveIntegerFailureRecord } from "./rate-limit-configuration";
