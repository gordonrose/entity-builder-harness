import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { securityOperationDiagnosticRecord } from "./diagnostics";

export interface PlatformCorsPolicy {
  readonly allowedOrigin?: string;
  readonly allowedMethods?: readonly string[];
  readonly allowedHeaders?: readonly string[];
  readonly allowCredentials?: boolean;
  readonly maxAgeSeconds?: number;
}

export interface PlatformSecurityHeadersOptions {
  readonly cors?: PlatformCorsPolicy;
}

export function createPlatformSecurityHeaders(
  options: PlatformSecurityHeadersOptions = {},
): Readonly<Record<string, string>> {
  return {
    "content-type": "application/json; charset=utf-8",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "permissions-policy": "camera=(), geolocation=(), microphone=()",
    ...(options.cors?.allowedOrigin === undefined ? {} : { "access-control-allow-origin": options.cors.allowedOrigin }),
    ...(options.cors?.allowedMethods === undefined ? {} : { "access-control-allow-methods": options.cors.allowedMethods.join(", ") }),
    ...(options.cors?.allowedHeaders === undefined ? {} : { "access-control-allow-headers": options.cors.allowedHeaders.join(", ") }),
    ...(options.cors?.allowCredentials === undefined ? {} : { "access-control-allow-credentials": String(options.cors.allowCredentials) }),
    ...(options.cors?.maxAgeSeconds === undefined ? {} : { "access-control-max-age": String(options.cors.maxAgeSeconds) }),
    ...(options.cors?.allowedOrigin === undefined ? {} : { vary: "Origin" }),
  };
}

export function corsPolicyForOrigin(origin: string | undefined): PlatformCorsPolicy {
  if (origin === undefined || origin.length === 0) {
    return {};
  }

  return {
    allowedOrigin: origin,
    allowedMethods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
    allowedHeaders: ["authorization", "content-type", "x-request-id"],
    maxAgeSeconds: 600,
  };
}

export function corsPolicyForRequestOrigin(input: {
  readonly requestOrigin?: string;
  readonly allowedOrigins?: readonly string[];
  readonly allowCredentials?: boolean;
}): PlatformCorsPolicy {
  return observeCorsPolicyForRequestOrigin(input).policy;
}

/** Observation is available explicitly; normal missing/allowed origins are not logged by default.
 * Omitting a browser permission header does not reject server-side execution.
 */
export function observeCorsPolicyForRequestOrigin(input: { readonly requestOrigin?: string; readonly allowedOrigins?: readonly string[]; readonly allowCredentials?: boolean }): { readonly policy: PlatformCorsPolicy; readonly diagnosticRecord: DiagnosticRecord } {
  const requestOrigin = input.requestOrigin;
  if (requestOrigin === undefined || requestOrigin.length === 0) {
    return { policy: {}, diagnosticRecord: securityOperationDiagnosticRecord("cors", requestOrigin === undefined ? "origin-missing" : "origin-empty") };
  }

  const allowedOrigins = input.allowedOrigins ?? [];
  if (!allowedOrigins.includes(requestOrigin)) {
    return { policy: {}, diagnosticRecord: securityOperationDiagnosticRecord("cors", "origin-not-allowlisted") };
  }

  return { diagnosticRecord: securityOperationDiagnosticRecord("cors", "origin-allowed"), policy: {
    ...corsPolicyForOrigin(requestOrigin),
    ...(input.allowCredentials === undefined ? {} : { allowCredentials: input.allowCredentials }),
  } };
}
