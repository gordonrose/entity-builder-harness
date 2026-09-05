export interface PlatformCorsPolicy {
  readonly allowedOrigin?: string;
  readonly allowedMethods?: readonly string[];
  readonly allowedHeaders?: readonly string[];
  readonly allowCredentials?: boolean;
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
    ...(options.cors?.allowedOrigin === undefined ? {} : { "access-control-allow-origin": options.cors.allowedOrigin }),
    ...(options.cors?.allowedMethods === undefined ? {} : { "access-control-allow-methods": options.cors.allowedMethods.join(", ") }),
    ...(options.cors?.allowedHeaders === undefined ? {} : { "access-control-allow-headers": options.cors.allowedHeaders.join(", ") }),
    ...(options.cors?.allowCredentials === undefined ? {} : { "access-control-allow-credentials": String(options.cors.allowCredentials) }),
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
  };
}

export function corsPolicyForRequestOrigin(input: {
  readonly requestOrigin?: string;
  readonly allowedOrigins?: readonly string[];
  readonly allowCredentials?: boolean;
}): PlatformCorsPolicy {
  const requestOrigin = input.requestOrigin;
  if (requestOrigin === undefined || requestOrigin.length === 0) {
    return {};
  }

  const allowedOrigins = input.allowedOrigins ?? [];
  if (!allowedOrigins.includes(requestOrigin)) {
    return {};
  }

  return {
    ...corsPolicyForOrigin(requestOrigin),
    ...(input.allowCredentials === undefined ? {} : { allowCredentials: input.allowCredentials }),
  };
}
