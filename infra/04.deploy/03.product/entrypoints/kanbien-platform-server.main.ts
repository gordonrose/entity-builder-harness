// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-server
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - architecture
//   - sre
//   kind: code
//   purpose: Start the platform server shell with the Kanbien Platform product app composition.
//   portability:
//     class: internal
//     targets: []
//   used_by:
//   - id: infra.04-deploy.03-product.image.dockerfile
//     path: infra/04.deploy/03.product/image/Dockerfile

import {
  kanbienPlatformApps,
  kanbienPlatformProductManifest,
} from "@kanbien/product-kanbien-platform";
import { createCognitoJwtBearerAuthenticationHookFromEnv } from "@kanbien/platform-adapter-aws-auth-cognito";
import { createDynamoDbFixedWindowPlatformRateLimiterFromEnv } from "@kanbien/platform-adapter-aws-security-dynamodb-rate-limiter";
import { createAlbTrustedClientAddressResolver } from "@kanbien/platform-adapter-aws-runtime-ecs-fargate";
import {
  resolvePlatformServerTransportOptions,
  type PlatformClientAddressResolver,
  type PlatformServerTransportOptions,
} from "@kanbien/platform-server";
import { startPlatformServerProcess } from "@kanbien/platform-server/main";
import type { PlatformRateLimiter } from "@kanbien/platform-security";

interface TargetRuntimeConfiguration {
  readonly rateLimiter?: PlatformRateLimiter;
  readonly clientAddressResolver?: PlatformClientAddressResolver;
  readonly transport?: PlatformServerTransportOptions;
}

interface TargetRuntimeConfigurationError {
  readonly code: "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{
    readonly path: string;
    readonly reason: string;
  }>;
}

export async function runKanbienPlatformServerMain(): Promise<void> {
  const authentication = authenticationFromTargetEnvironment(process.env);
  if (!authentication.ok) {
    console.error(JSON.stringify({ level: "error", message: "kanbien-platform.server.auth_configuration_invalid", error: authentication.error }));
    process.exitCode = 1;
    return;
  }

  const runtime = runtimeConfigurationFromTargetEnvironment(process.env);
  if (!runtime.ok) {
    console.error(JSON.stringify({ level: "error", message: "kanbien-platform.server.runtime_configuration_invalid", error: runtime.error }));
    process.exitCode = 1;
    return;
  }

  const started = await startPlatformServerProcess({
    apps: kanbienPlatformApps,
    configKeys: productConfigKeys(),
    ...(authentication.value === undefined ? {} : { auth: authentication.value }),
    ...(runtime.value.rateLimiter === undefined ? {} : { rateLimiter: runtime.value.rateLimiter }),
    ...(runtime.value.clientAddressResolver === undefined ? {} : { clientAddressResolver: runtime.value.clientAddressResolver }),
    ...(runtime.value.transport === undefined ? {} : { transport: runtime.value.transport }),
  });

  if (!started.ok) {
    console.error(JSON.stringify({
      level: "error",
      message: "kanbien-platform.server.start_failed",
      error: {
        code: started.error.code,
        message: started.error.defaultMessage,
      },
    }));
    process.exitCode = 1;
    return;
  }

  if (process.env["PLATFORM_SERVER_EXIT_AFTER_START"] === "1") {
    await started.value.close();
  }
}

function productConfigKeys(): readonly string[] {
  return [...new Set(kanbienPlatformProductManifest.apps.flatMap((app) => app.requiredConfig))];
}

function authenticationFromTargetEnvironment(env: NodeJS.ProcessEnv) {
  const provider = env["PLATFORM_AUTH_PROVIDER"];
  if (provider === undefined || provider.length === 0 || provider === "none") {
    return { ok: true as const, value: undefined };
  }
  if (provider === "cognito") {
    return createCognitoJwtBearerAuthenticationHookFromEnv(env);
  }

  return {
    ok: false as const,
    error: {
      code: "KANBIEN_PLATFORM_TARGET_AUTH_PROVIDER_INVALID",
      defaultMessage: "The Kanbien platform target selected an unsupported authentication provider.",
      details: { path: "PLATFORM_AUTH_PROVIDER", reason: "The target composition does not have an adapter for this provider." },
    },
  };
}

function runtimeConfigurationFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
): { readonly ok: true; readonly value: TargetRuntimeConfiguration } | { readonly ok: false; readonly error: TargetRuntimeConfigurationError } {
  const exposure = env["PLATFORM_DEPLOYMENT_EXPOSURE"];
  if (exposure !== undefined && exposure !== "private" && exposure !== "public") {
    return targetRuntimeConfigurationError("PLATFORM_DEPLOYMENT_EXPOSURE", "Expected private or public.");
  }

  const isPublic = exposure === "public";
  if (isPublic && env["PLATFORM_AUTH_PROVIDER"] !== "cognito") {
    return targetRuntimeConfigurationError("PLATFORM_AUTH_PROVIDER", "Public target requires the selected Cognito authentication provider.");
  }

  const rateLimiter = rateLimiterFromTargetEnvironment(env, isPublic);
  if (!rateLimiter.ok) {
    return rateLimiter;
  }

  const clientAddressResolver = clientAddressResolverFromTargetEnvironment(env, isPublic);
  if (!clientAddressResolver.ok) {
    return clientAddressResolver;
  }

  const transport = transportFromTargetEnvironment(env, isPublic);
  if (!transport.ok) {
    return transport;
  }

  return {
    ok: true,
    value: {
      ...(rateLimiter.value === undefined ? {} : { rateLimiter: rateLimiter.value }),
      ...(clientAddressResolver.value === undefined ? {} : { clientAddressResolver: clientAddressResolver.value }),
      ...(transport.value === undefined ? {} : { transport: transport.value }),
    },
  };
}

function rateLimiterFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
  isPublic: boolean,
): { readonly ok: true; readonly value: PlatformRateLimiter | undefined } | { readonly ok: false; readonly error: TargetRuntimeConfigurationError } {
  const provider = env["PLATFORM_RATE_LIMIT_PROVIDER"];
  if (provider === undefined || provider.length === 0) {
    return isPublic
      ? targetRuntimeConfigurationError("PLATFORM_RATE_LIMIT_PROVIDER", "Public target requires a shared rate-limit provider.")
      : { ok: true, value: undefined };
  }
  if (provider !== "dynamodb") {
    return targetRuntimeConfigurationError("PLATFORM_RATE_LIMIT_PROVIDER", "Unsupported rate-limit provider.");
  }

  const configured = createDynamoDbFixedWindowPlatformRateLimiterFromEnv(env);
  if (!configured.ok) {
    return targetRuntimeConfigurationError(configured.error.details.path, configured.error.details.reason);
  }
  return { ok: true, value: configured.value };
}

function clientAddressResolverFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
  isPublic: boolean,
): { readonly ok: true; readonly value: PlatformClientAddressResolver | undefined } | { readonly ok: false; readonly error: TargetRuntimeConfigurationError } {
  const ingressMode = env["PLATFORM_TRUSTED_INGRESS_MODE"];
  if (ingressMode === undefined || ingressMode.length === 0) {
    return isPublic
      ? targetRuntimeConfigurationError("PLATFORM_TRUSTED_INGRESS_MODE", "Public target requires a trusted ingress mode.")
      : { ok: true, value: undefined };
  }
  if (ingressMode !== "alb-security-group-only") {
    return targetRuntimeConfigurationError("PLATFORM_TRUSTED_INGRESS_MODE", "Unsupported trusted ingress mode.");
  }

  return {
    ok: true,
    value: createAlbTrustedClientAddressResolver({ ingressMode }),
  };
}

function transportFromTargetEnvironment(
  env: NodeJS.ProcessEnv,
  isPublic: boolean,
): { readonly ok: true; readonly value: PlatformServerTransportOptions | undefined } | { readonly ok: false; readonly error: TargetRuntimeConfigurationError } {
  const fields = [
    ["PLATFORM_SERVER_MAX_REQUEST_BODY_BYTES", "maxRequestBodyBytes"],
    ["PLATFORM_SERVER_MAX_HEADER_BYTES", "maxHeaderBytes"],
    ["PLATFORM_SERVER_MAX_HEADERS_COUNT", "maxHeadersCount"],
    ["PLATFORM_SERVER_HEADERS_TIMEOUT_MS", "headersTimeoutMs"],
    ["PLATFORM_SERVER_REQUEST_TIMEOUT_MS", "requestTimeoutMs"],
    ["PLATFORM_SERVER_KEEP_ALIVE_TIMEOUT_MS", "keepAliveTimeoutMs"],
    ["PLATFORM_SERVER_HANDLER_TIMEOUT_MS", "handlerTimeoutMs"],
    ["PLATFORM_SERVER_SHUTDOWN_DRAIN_TIMEOUT_MS", "shutdownDrainTimeoutMs"],
    ["PLATFORM_SERVER_MAX_CONCURRENT_REQUESTS", "maxConcurrentRequests"],
    ["PLATFORM_SERVER_MAX_REQUESTS_PER_SOCKET", "maxRequestsPerSocket"],
  ] as const;
  const values: Record<string, number> = {};

  for (const [environmentKey, optionKey] of fields) {
    const raw = env[environmentKey];
    if (raw === undefined || raw.length === 0) {
      if (isPublic) {
        return targetRuntimeConfigurationError(environmentKey, "Public target requires an explicit positive integer transport limit.");
      }
      continue;
    }
    const parsed = Number(raw);
    if (!Number.isInteger(parsed) || parsed <= 0) {
      return targetRuntimeConfigurationError(environmentKey, "Expected a positive integer transport limit.");
    }
    values[optionKey] = parsed;
  }

  if (Object.keys(values).length === 0) {
    return { ok: true, value: undefined };
  }

  const resolved = resolvePlatformServerTransportOptions(values);
  if (!resolved.ok) {
    return targetRuntimeConfigurationError("PLATFORM_SERVER_*", resolved.reason);
  }
  return { ok: true, value: values };
}

function targetRuntimeConfigurationError(
  path: string,
  reason: string,
): { readonly ok: false; readonly error: TargetRuntimeConfigurationError } {
  return {
    ok: false,
    error: {
      code: "KANBIEN_PLATFORM_TARGET_RUNTIME_CONFIG_INVALID",
      defaultMessage: "Kanbien platform target runtime configuration is invalid.",
      details: { path, reason },
    },
  };
}

if (typeof require !== "undefined" && require.main === module) {
  void runKanbienPlatformServerMain();
}
