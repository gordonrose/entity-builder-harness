import { copyJsonValue, entityId, type EntityId, type JsonValue } from "../shared/index";
import type { TenantId } from "../tenancy/index";
import { PrincipalObservation } from "./observations";
import type { CoreAuthnDiagnosticOptions } from "./diagnostics";
export { coreAuthnBoundaryDiagnostic, coreAuthnBoundaryDiagnosticRecord, coreAuthnDiagnosticDefinitions } from "./diagnostics";
export type { CoreAuthnBoundaryDetail, CoreAuthnDiagnosticContext, CoreAuthnDiagnosticOptions } from "./diagnostics";
export { observeCoreAuthnDiagnostic } from "./observations";

export type PrincipalId = EntityId<"PrincipalId">;
export type PrincipalType = "user" | "service";
export type PrincipalClaimValue = JsonValue;
export type PrincipalClaims = Readonly<Record<string, PrincipalClaimValue>>;
export type AuthenticationResult = Principal | null;

export interface Principal {
  readonly id: PrincipalId;
  readonly type: PrincipalType;
  readonly subject: string;
  readonly currentTenantId?: TenantId;
  readonly claims: PrincipalClaims;
  readonly scopes?: readonly string[];
}

export interface Authenticator<TCredential> {
  authenticate(credential: TCredential): Promise<AuthenticationResult>;
}

export function principalId(value: string): PrincipalId {
  return entityId<"PrincipalId">(value);
}

export function principal(input: {
  readonly id: PrincipalId;
  readonly type: PrincipalType;
  readonly subject: string;
  readonly currentTenantId?: TenantId;
  readonly claims?: PrincipalClaims;
  readonly scopes?: readonly string[];
}, diagnostics?: CoreAuthnDiagnosticOptions): Principal {
  const observation = new PrincipalObservation(diagnostics);
  return observation.run(() => ({
    id: observation.at("input-projection", "id", () => input.id),
    type: observation.at("input-projection", "type", () => input.type),
    subject: observation.at("input-projection", "subject", () => input.subject),
    ...(observation.at("input-projection", "current-tenant-id", () => input.currentTenantId) === undefined ? {} : { currentTenantId: observation.at("input-projection", "current-tenant-id", () => input.currentTenantId)! }),
    claims: copyPrincipalClaims(observation.at("input-projection", "claims", () => input.claims) ?? {}, observation),
    ...(observation.at("input-projection", "scopes", () => input.scopes) === undefined ? {} : { scopes: observation.at("scopes-copy", "scopes", () => [...input.scopes!]) }),
  }));
}

export function fixedAuthenticator<TCredential>(result: AuthenticationResult): Authenticator<TCredential> {
  return {
    authenticate: async () => result,
  };
}

function copyPrincipalClaims(claims: PrincipalClaims, observation: PrincipalObservation): PrincipalClaims {
  return observation.at("result-projection", "claims", () => Object.fromEntries(
    observation.at("claims-copy", "claims", () => observation.at("claims-enumeration", "claims", () => Object.entries(claims))
      .map(([key, value]) => [key, copyPrincipalClaimValue(value)])),
  ));
}

function copyPrincipalClaimValue(value: PrincipalClaimValue): PrincipalClaimValue {
  return copyJsonValue(value, "principal claims");
}
