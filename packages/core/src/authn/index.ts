import { entityId, type EntityId } from "../shared/index";
import type { TenantId } from "../tenancy/index";

export type PrincipalId = EntityId<"PrincipalId">;
export type PrincipalType = "user" | "service";
export type PrincipalClaimValue =
  | string
  | number
  | boolean
  | null
  | readonly PrincipalClaimValue[]
  | { readonly [key: string]: PrincipalClaimValue };
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
}): Principal {
  return {
    id: input.id,
    type: input.type,
    subject: input.subject,
    ...(input.currentTenantId === undefined ? {} : { currentTenantId: input.currentTenantId }),
    claims: copyPrincipalClaims(input.claims ?? {}),
    ...(input.scopes === undefined ? {} : { scopes: [...input.scopes] }),
  };
}

export function fixedAuthenticator<TCredential>(result: AuthenticationResult): Authenticator<TCredential> {
  return {
    authenticate: async () => result,
  };
}

function copyPrincipalClaims(claims: PrincipalClaims): PrincipalClaims {
  return Object.fromEntries(
    Object.entries(claims).map(([key, value]) => [key, copyPrincipalClaimValue(value)]),
  );
}

function copyPrincipalClaimValue(value: PrincipalClaimValue): PrincipalClaimValue {
  if (Array.isArray(value)) {
    return value.map(copyPrincipalClaimValue);
  }

  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, nestedValue]) => [key, copyPrincipalClaimValue(nestedValue)]),
    );
  }

  return value;
}
