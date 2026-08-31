import type { Clock, Permission, PrincipalType, Result } from "@kanbien/core";
import {
  createJwksJwtVerifier,
  createJwtBearerAuthenticationHook,
  type PlatformAuthenticationHook,
  type PlatformAuthzPermissionMapping,
  type PlatformClaimPermissionMapping,
  type PlatformClaimValuePermissionMapping,
  type PlatformJwksFetcher,
  type PlatformJwtVerifier,
} from "@kanbien/platform-security";

export interface CognitoAccessTokenVerifierOptions {
  readonly region: string;
  readonly userPoolId: string;
  readonly appClientId: string;
  readonly clock?: Clock;
  readonly clockSkewSeconds?: number;
  readonly fetchJwks?: PlatformJwksFetcher;
}

export interface CognitoAuthzPermissionMapping {
  readonly groups?: Readonly<Record<string, readonly Permission[]>>;
  readonly scopes?: Readonly<Record<string, readonly Permission[]>>;
  readonly claims?: readonly PlatformClaimPermissionMapping[];
}

export interface CognitoJwtBearerAuthenticationHookOptions extends CognitoAccessTokenVerifierOptions {
  readonly authz: CognitoAuthzPermissionMapping;
  readonly principalType?: PrincipalType;
}

export interface CognitoEnvironmentAuthenticationHookOptions {
  readonly clock?: Clock;
  readonly clockSkewSeconds?: number;
  readonly fetchJwks?: PlatformJwksFetcher;
  readonly principalType?: PrincipalType;
}

export interface CognitoAdapterConfigurationError {
  readonly code: "PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{
    readonly path: string;
    readonly reason: string;
  }>;
}

export const adapterMetadata = {
  provider: "aws",
  capability: "authentication",
  implementation: "cognito",
  packageName: "@kanbien/platform-adapter-aws-auth-cognito",
} as const;

export function createCognitoAccessTokenVerifier(
  options: CognitoAccessTokenVerifierOptions,
): PlatformJwtVerifier {
  return createJwksJwtVerifier({
    issuer: cognitoIssuer(options.region, options.userPoolId),
    jwksUri: cognitoJwksUri(options.region, options.userPoolId),
    requiredClaims: [
      { claim: "token_use", equals: "access" },
      { claim: "client_id", equals: options.appClientId },
    ],
    ...(options.clock === undefined ? {} : { clock: options.clock }),
    ...(options.clockSkewSeconds === undefined ? {} : { clockSkewSeconds: options.clockSkewSeconds }),
    ...(options.fetchJwks === undefined ? {} : { fetchJwks: options.fetchJwks }),
  });
}

export function createCognitoAuthzPermissionMapping(
  mapping: CognitoAuthzPermissionMapping,
): PlatformAuthzPermissionMapping {
  const valueClaims: PlatformClaimValuePermissionMapping[] = [];

  if (mapping.groups !== undefined) {
    valueClaims.push({
      claim: "cognito:groups",
      format: "string-array",
      values: mapping.groups,
    });
  }

  if (mapping.scopes !== undefined) {
    valueClaims.push({
      claim: "scope",
      format: "space-delimited",
      values: mapping.scopes,
    });
  }

  return {
    ...(valueClaims.length === 0 ? {} : { valueClaims }),
    ...(mapping.claims === undefined ? {} : { claims: mapping.claims }),
  };
}

export function createCognitoJwtBearerAuthenticationHook(
  options: CognitoJwtBearerAuthenticationHookOptions,
): PlatformAuthenticationHook {
  return createJwtBearerAuthenticationHook({
    verifier: createCognitoAccessTokenVerifier(options),
    authz: createCognitoAuthzPermissionMapping(options.authz),
    ...(options.principalType === undefined ? {} : { principalType: options.principalType }),
  });
}

export function createCognitoJwtBearerAuthenticationHookFromEnv(
  env: Readonly<Record<string, string | undefined>>,
  options: CognitoEnvironmentAuthenticationHookOptions = {},
): Result<PlatformAuthenticationHook, CognitoAdapterConfigurationError> {
  const region = requiredEnv(env, "PLATFORM_AUTH_COGNITO_REGION");
  const userPoolId = requiredEnv(env, "PLATFORM_AUTH_COGNITO_USER_POOL_ID");
  const appClientId = requiredEnv(env, "PLATFORM_AUTH_COGNITO_APP_CLIENT_ID");
  const groups = permissionMapFromJsonEnv(env, "PLATFORM_AUTHZ_GROUP_PERMISSIONS");
  const scopes = permissionMapFromJsonEnv(env, "PLATFORM_AUTHZ_SCOPE_PERMISSIONS");
  const claims = claimPermissionMappingsFromJsonEnv(env, "PLATFORM_AUTHZ_CLAIM_PERMISSIONS");

  if (!region.ok) {
    return region;
  }
  if (!userPoolId.ok) {
    return userPoolId;
  }
  if (!appClientId.ok) {
    return appClientId;
  }
  if (!groups.ok) {
    return groups;
  }
  if (!scopes.ok) {
    return scopes;
  }
  if (!claims.ok) {
    return claims;
  }

  return {
    ok: true,
    value: createCognitoJwtBearerAuthenticationHook({
      region: region.value,
      userPoolId: userPoolId.value,
      appClientId: appClientId.value,
      authz: {
        groups: groups.value,
        scopes: scopes.value,
        claims: claims.value,
      },
      ...(options.clock === undefined ? {} : { clock: options.clock }),
      ...(options.clockSkewSeconds === undefined ? {} : { clockSkewSeconds: options.clockSkewSeconds }),
      ...(options.fetchJwks === undefined ? {} : { fetchJwks: options.fetchJwks }),
      ...(options.principalType === undefined ? {} : { principalType: options.principalType }),
    }),
  };
}

export function cognitoIssuer(region: string, userPoolId: string): string {
  return `https://cognito-idp.${region}.amazonaws.com/${userPoolId}`;
}

export function cognitoJwksUri(region: string, userPoolId: string): string {
  return `${cognitoIssuer(region, userPoolId)}/.well-known/jwks.json`;
}

function requiredEnv(
  env: Readonly<Record<string, string | undefined>>,
  key: string,
): Result<string, CognitoAdapterConfigurationError> {
  const value = env[key];
  if (value !== undefined && value.length > 0) {
    return { ok: true, value };
  }

  return configurationError(key, "Required environment value is missing.");
}

function permissionMapFromJsonEnv(
  env: Readonly<Record<string, string | undefined>>,
  key: string,
): Result<Readonly<Record<string, readonly Permission[]>>, CognitoAdapterConfigurationError> {
  const raw = env[key];
  if (raw === undefined || raw.length === 0) {
    return { ok: true, value: {} };
  }

  const parsed = parseJsonEnv(raw, key);
  if (!parsed.ok) {
    return parsed;
  }

  if (!isRecord(parsed.value)) {
    return configurationError(key, "Expected a JSON object mapping strings to permission arrays.");
  }

  const values: Record<string, readonly Permission[]> = {};
  for (const [mappingKey, permissions] of Object.entries(parsed.value)) {
    if (!Array.isArray(permissions) || !permissions.every(isPermissionString)) {
      return configurationError(key, "Expected every mapped value to be an array of permission strings.");
    }
    values[mappingKey] = permissions;
  }

  return { ok: true, value: values };
}

function claimPermissionMappingsFromJsonEnv(
  env: Readonly<Record<string, string | undefined>>,
  key: string,
): Result<readonly PlatformClaimPermissionMapping[], CognitoAdapterConfigurationError> {
  const raw = env[key];
  if (raw === undefined || raw.length === 0) {
    return { ok: true, value: [] };
  }

  const parsed = parseJsonEnv(raw, key);
  if (!parsed.ok) {
    return parsed;
  }
  if (!Array.isArray(parsed.value)) {
    return configurationError(key, "Expected a JSON array of claim permission mappings.");
  }

  const claims: PlatformClaimPermissionMapping[] = [];
  for (const value of parsed.value) {
    if (
      !isRecord(value)
      || typeof value["claim"] !== "string"
      || !isClaimEqualsValue(value["equals"])
      || !Array.isArray(value["permissions"])
      || !value["permissions"].every(isPermissionString)
    ) {
      return configurationError(key, "Expected claim, equals, and permissions fields for every claim mapping.");
    }
    claims.push({
      claim: value["claim"],
      equals: value["equals"],
      permissions: value["permissions"],
    });
  }

  return { ok: true, value: claims };
}

function parseJsonEnv(raw: string, key: string): Result<unknown, CognitoAdapterConfigurationError> {
  try {
    return { ok: true, value: JSON.parse(raw) as unknown };
  } catch {
    return configurationError(key, "Expected valid JSON.");
  }
}

function configurationError(path: string, reason: string): Result<never, CognitoAdapterConfigurationError> {
  return {
    ok: false,
    error: {
      code: "PLATFORM_ADAPTER_AWS_COGNITO_CONFIG_INVALID",
      defaultMessage: "Cognito authentication adapter configuration is invalid.",
      details: { path, reason },
    },
  };
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPermissionString(value: unknown): value is Permission {
  return typeof value === "string" && /^[^:\s]+:[^:\s]+$/.test(value);
}

function isClaimEqualsValue(value: unknown): value is string | number | boolean {
  return typeof value === "string" || typeof value === "number" || typeof value === "boolean";
}
