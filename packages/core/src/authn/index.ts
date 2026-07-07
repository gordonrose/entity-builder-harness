import { entityId, type EntityId } from "../shared/index";
import type { TenantId } from "../tenancy/index";

export type PrincipalId = EntityId<"PrincipalId">;
export type PrincipalType = "user" | "service";
export type PrincipalClaims = Readonly<Record<string, unknown>>;
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
}): Principal {
  return {
    id: input.id,
    type: input.type,
    subject: input.subject,
    ...(input.currentTenantId === undefined ? {} : { currentTenantId: input.currentTenantId }),
    claims: { ...(input.claims ?? {}) },
    ...(input.scopes === undefined ? {} : { scopes: [...input.scopes] }),
  };
}

export function fixedAuthenticator<TCredential>(result: AuthenticationResult): Authenticator<TCredential> {
  return {
    authenticate: async () => result,
  };
}
