import { stringConfigValue, type ConfigSchema } from "@kanbien/core/config";
import {
  healthCheckName,
  healthCheckResult,
  monitoringComponent,
  monitoringMetadata,
} from "@kanbien/core/monitoring";
import type { QueueMessage, QueueMessageType } from "@kanbien/core/queues";
import { isoDateTimeFromDate, ok, type JsonValue, type Result } from "@kanbien/core/shared";
import { invalidResult, validResult, validationIssue, type Validator } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformHealthName,
  platformJobName,
  platformRouteName,
  type PlatformAppId,
  type PlatformContractError,
  type PlatformHealthName,
  type PlatformJobName,
  type PlatformRouteName,
} from "@kanbien/platform-contracts";
import {
  platformSmokeAppManifest,
  platformSmokeReadPermission,
} from "./app.manifest";

export interface PlatformSmokeConfig {
  readonly appName: string;
}

export interface PlatformSmokeRebuildPayload extends Readonly<Record<string, JsonValue>> {
  readonly rebuild: boolean;
}

export const platformSmokeAppId = unwrapPlatformName(platformAppId(platformSmokeAppManifest.appId));
export const platformSmokeRouteName = unwrapPlatformName(platformRouteName("platform-smoke.echo"));
export const platformSmokeJobName = unwrapPlatformName(platformJobName("platform-smoke.rebuild"));
export const platformSmokeHealthName = unwrapPlatformName(platformHealthName("platform-smoke.readiness"));
export const platformSmokeJobMessageType = "platform-smoke.rebuild" as QueueMessageType;

export const platformSmokeConfigSchema: ConfigSchema<PlatformSmokeConfig> = {
  parse(source) {
    const appName = stringConfigValue(source, "PLATFORM_SMOKE_APP_NAME");
    if (!appName.ok) {
      return { ok: false, error: appName.error };
    }

    return ok({ appName: appName.value });
  },
};

export const platformSmokeRebuildValidator: Validator<PlatformSmokeRebuildPayload> = {
  validate: isPlatformSmokeRebuildPayload,
  explain: (value) => isPlatformSmokeRebuildPayload(value)
    ? validResult
    : invalidResult(validationIssue({
      path: ["payload", "rebuild"],
      code: "PLATFORM_SMOKE_INVALID_REBUILD_PAYLOAD",
      defaultMessage: "Platform smoke rebuild payload must include a boolean rebuild flag.",
    })),
};

export const platformSmokeApp = definePlatformApp({
  id: platformSmokeAppId,
  name: platformSmokeAppManifest.displayName,
  version: "0.0.0",
  lifecycle: {
    beforeStart: () => undefined,
    afterStart: () => undefined,
    beforeStop: () => undefined,
    afterStop: () => undefined,
  },
  mount(registry, deps) {
    registry.registerConfigSchema(platformSmokeConfigSchema);
    registry.registerPermission({
      permission: platformSmokeReadPermission,
      description: "Read the platform smoke route.",
    });
    registry.registerRoute({
      name: platformSmokeRouteName,
      method: "GET",
      path: "/smoke/:id",
      auth: { kind: "authenticated", permissions: [platformSmokeReadPermission] },
      handler: {
        handle: (request, context) => ({
          status: 200,
          body: {
            app: platformSmokeAppManifest.appId,
            appName: context.config.get("PLATFORM_SMOKE_APP_NAME"),
            id: request.params["id"],
            ok: true,
          },
        }),
      },
    });
    registry.registerJob({
      name: platformSmokeJobName,
      messageType: platformSmokeJobMessageType,
      validator: platformSmokeRebuildValidator,
      handler: {
        handle: (message, context) => {
          deps.logger.write({
            level: "info",
            message: "platform-smoke.job.handled",
            correlationId: context.correlationId,
            fields: {
              messageType: String(message.type),
              rebuild: Boolean((message.payload as PlatformSmokeRebuildPayload).rebuild),
            },
          });
        },
      },
    });
    registry.registerHealthCheck({
      name: platformSmokeHealthName,
      check: {
        check: () =>
          healthCheckResult({
            name: healthCheckName("platform-smoke.readiness"),
            type: "readiness",
            component: monitoringComponent({ type: "runtime", name: "platform-smoke" }),
            status: "healthy",
            checkedAt: isoDateTimeFromDate(deps.clock.now()),
            metadata: monitoringMetadata({
              app: platformSmokeAppManifest.appId,
              config: deps.config.get("PLATFORM_SMOKE_APP_NAME") === undefined ? "missing" : "present",
            }),
          }),
      },
    });
  },
});

function isPlatformSmokeRebuildPayload(value: unknown): value is PlatformSmokeRebuildPayload {
  return typeof value === "object"
    && value !== null
    && "rebuild" in value
    && typeof (value as { readonly rebuild?: unknown }).rebuild === "boolean";
}

function unwrapPlatformName<TName extends PlatformAppId | PlatformRouteName | PlatformJobName | PlatformHealthName>(
  result: Result<TName, PlatformContractError>,
): TName {
  if (!result.ok) {
    throw new Error(result.error.defaultMessage);
  }

  return result.value;
}

export type PlatformSmokeJobMessage = QueueMessage<JsonValue>;
