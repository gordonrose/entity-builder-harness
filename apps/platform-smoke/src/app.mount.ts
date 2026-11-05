import { stringConfigValue, type ConfigSchema } from "@kanbien/core/config";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformPersistenceDiagnosticCatalog, type PlatformPersistenceDiagnosticOptions } from "@kanbien/platform-persistence";
import { platformPersistenceErrorClasses } from "@kanbien/platform-persistence";
import { persistenceErrorCodes } from "@kanbien/core/persistence";
import { platformSmokeAcceptanceFailure, platformSmokeAttributeFailure, platformSmokeDiagnosticCatalog, platformSmokeConfigurationFailure, platformSmokeAcceptedPayloadFailure } from "./diagnostics";
import {
  healthCheckName,
  healthCheckResult,
  monitoringComponent,
  monitoringMetadata,
} from "@kanbien/core/monitoring";
import type { QueueMessage, QueueMessageType } from "@kanbien/core/queues";
import { causationId, isoDateTimeFromDate, ok, type JsonValue, type Result } from "@kanbien/core/shared";
import { invalidResult, validResult, validationIssue, type Validator } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformCapabilityName,
  platformHealthName,
  platformJobName,
  platformObservabilityProfileName,
  platformRouteName,
  type PlatformCapabilityObservabilityProfile,
  type PlatformContractError,
} from "@kanbien/platform-contracts";
import {
  platformSmokeAppManifest,
  platformSmokeReadPermission,
  platformSmokeWorkItemCreatePermission,
} from "./app.manifest";
import {
  acceptPlatformSmokeWorkItem,
  platformSmokeWorkItemId,
  type PlatformSmokeAcceptWorkItemDependencies,
} from "./persistence/index";

export interface PlatformSmokeConfig {
  readonly appName: string;
}

export interface PlatformSmokeRebuildPayload extends Readonly<Record<string, JsonValue>> {
  readonly rebuild: boolean;
}

/** The relay exposes no business data: only the durable outbox identity. */
export interface PlatformSmokeWorkItemAcceptedPayload extends Readonly<Record<string, JsonValue>> {
  readonly outboxEntryId: string;
}

/**
 * Target composition may opt into the bounded persistence proof by injecting
 * only the app-facing persistence seam. The app never receives provider
 * configuration, a table name, or an SDK client.
 */
export interface PlatformSmokeAppOptions {
  readonly workItemAcceptance?: PlatformSmokeAcceptWorkItemDependencies;
  /** Source definitions are selected here; the host still registers their reporter catalogs. */
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
}

export const platformSmokeAppId = unwrapPlatformName(platformAppId(platformSmokeAppManifest.appId));
export const platformSmokeRouteName = unwrapPlatformName(platformRouteName("platform-smoke.echo"));
export const platformSmokeWorkItemAcceptanceRouteName = unwrapPlatformName(platformRouteName("platform-smoke.persistence.work-item.accept"));
export const platformSmokeWorkItemAdmissionRouteName = unwrapPlatformName(platformRouteName("platform-smoke.persistence.work-item.admission"));
export const platformSmokeJobName = unwrapPlatformName(platformJobName("platform-smoke.rebuild"));
export const platformSmokeWorkItemAcceptedJobName = unwrapPlatformName(platformJobName("platform-smoke.work-item.accepted"));
export const platformSmokeHealthName = unwrapPlatformName(platformHealthName("platform-smoke.readiness"));
export const platformSmokeEchoObservabilityProfileName = unwrapPlatformName(platformObservabilityProfileName("platform-smoke.smoke.read"));
export const platformSmokeRebuildObservabilityProfileName = unwrapPlatformName(platformObservabilityProfileName("platform-smoke.smoke.rebuild"));
export const platformSmokeWorkItemDeliveryObservabilityProfileName = unwrapPlatformName(
  platformObservabilityProfileName("platform-smoke.persistence.work-item.delivery"),
);
export const platformSmokeWorkItemAcceptanceObservabilityProfileName = unwrapPlatformName(
  platformObservabilityProfileName("platform-smoke.persistence.work-item.accepted"),
);
export const platformSmokeWorkItemAdmissionObservabilityProfileName = unwrapPlatformName(
  platformObservabilityProfileName("platform-smoke.persistence.work-item.admission"),
);
export const platformSmokeJobMessageType = "platform-smoke.rebuild" as QueueMessageType;
export const platformSmokeWorkItemAcceptedJobMessageType = "platform-smoke.work-item.accepted" as QueueMessageType;

export const platformSmokeEchoObservabilityProfile: PlatformCapabilityObservabilityProfile = {
  name: platformSmokeEchoObservabilityProfileName,
  capability: unwrapPlatformName(platformCapabilityName("platform-smoke.smoke.read")),
  action: "read",
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "interactive_read", measurement: "request_response_latency" }],
};

export const platformSmokeRebuildObservabilityProfile: PlatformCapabilityObservabilityProfile = {
  name: platformSmokeRebuildObservabilityProfileName,
  capability: unwrapPlatformName(platformCapabilityName("platform-smoke.smoke.rebuild")),
  action: "execute",
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "async_completion", measurement: "job_execution_latency" }],
};

/** Governs both the harmless delivery handler and its persistence transitions. */
export const platformSmokeWorkItemDeliveryObservabilityProfile: PlatformCapabilityObservabilityProfile = {
  name: platformSmokeWorkItemDeliveryObservabilityProfileName,
  capability: unwrapPlatformName(platformCapabilityName("platform-smoke.persistence.work-item.delivery")),
  action: "execute",
  errorClasses: platformPersistenceErrorClasses,
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "async_completion", measurement: "job_execution_latency" }],
};

export const platformSmokeWorkItemAcceptanceObservabilityProfile: PlatformCapabilityObservabilityProfile = {
  name: platformSmokeWorkItemAcceptanceObservabilityProfileName,
  capability: unwrapPlatformName(platformCapabilityName("platform-smoke.persistence.work-item")),
  action: "create",
  errorClasses: [...platformPersistenceErrorClasses, ...persistenceErrorCodes],
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "async_acceptance", measurement: "request_response_latency" }],
};

/** Governs the non-mutating write-path diagnostic used before a fresh acceptance proof. */
export const platformSmokeWorkItemAdmissionObservabilityProfile: PlatformCapabilityObservabilityProfile = {
  name: platformSmokeWorkItemAdmissionObservabilityProfileName,
  capability: unwrapPlatformName(platformCapabilityName("platform-smoke.persistence.work-item.admission")),
  action: "verify",
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  metricDimensionFieldNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  traceAttributeNames: ["capability", "action", "execution_context", "http_method", "http_status_code", "outcome", "error_class"],
  nfrObjectives: [{ nfrClass: "async_acceptance", measurement: "request_response_latency" }],
};

export const platformSmokeConfigSchema: ConfigSchema<PlatformSmokeConfig> = {
  parse(source) {
    const appName = stringConfigValue(source, "PLATFORM_SMOKE_APP_NAME");
    if (!appName.ok) {
      return { ok: false, error: { ...appName.error, diagnosticRecord: platformSmokeConfigurationFailure(appName.error.code === "CONFIG_MISSING" ? "missing" : "wrong-type"),
        ...(appName.error.diagnosticRecord === undefined ? {} : { relatedDiagnosticRecords: [appName.error.diagnosticRecord] }) } };
    }

    return ok({ appName: appName.value });
  },
};

export const platformSmokeRebuildValidator: Validator<PlatformSmokeRebuildPayload> = {
  validate: isPlatformSmokeRebuildPayload,
  diagnose: (value) => {
    if (isPlatformSmokeRebuildPayload(value)) return undefined;
    const present = typeof value === "object" && value !== null && Object.hasOwn(value, "rebuild");
    return platformSmokeAttributeFailure("payload.rebuild", present ? "wrong-type" : "missing");
  },
  explain: (value) => isPlatformSmokeRebuildPayload(value)
    ? validResult
    : invalidResult(validationIssue({
      path: ["payload", "rebuild"],
      code: "PLATFORM_SMOKE_INVALID_REBUILD_PAYLOAD",
      defaultMessage: "Platform smoke rebuild payload must include a boolean rebuild flag.",
    })),
};

export const platformSmokeWorkItemAcceptedValidator: Validator<PlatformSmokeWorkItemAcceptedPayload> = {
  validate: isPlatformSmokeWorkItemAcceptedPayload,
  diagnose: platformSmokeAcceptedPayloadFailure,
  explain: (value) => isPlatformSmokeWorkItemAcceptedPayload(value)
    ? validResult
    : invalidResult(validationIssue({
      path: ["payload", "outboxEntryId"],
      code: "PLATFORM_SMOKE_INVALID_WORK_ITEM_ACCEPTED_PAYLOAD",
      defaultMessage: "Platform smoke work-item delivery must include its stable outbox entry ID.",
    })),
};

/** A persistence acceptance contains no caller-supplied business payload. */
export const platformSmokeWorkItemAcceptanceValidator: Validator<undefined> = {
  validate: (value): value is undefined => value === undefined,
  diagnose: (value) => value === undefined ? undefined : platformSmokeAttributeFailure("payload", "unexpected-body"),
  explain: (value) => value === undefined
    ? validResult
    : invalidResult(validationIssue({
      path: ["payload"],
      code: "PLATFORM_SMOKE_INVALID_WORK_ITEM_ACCEPTANCE_PAYLOAD",
      defaultMessage: "Platform smoke work-item acceptance does not accept a request body.",
    })),
};

export function createPlatformSmokeApp(options: PlatformSmokeAppOptions = {}) {
  return definePlatformApp({
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
      registry.registerDiagnosticCatalog(platformSmokeDiagnosticCatalog);
      registry.registerConfigSchema(platformSmokeConfigSchema);
      registry.registerObservabilityProfile(platformSmokeEchoObservabilityProfile);
      registry.registerObservabilityProfile(platformSmokeRebuildObservabilityProfile);
      registry.registerObservabilityProfile(platformSmokeWorkItemDeliveryObservabilityProfile);
      registry.registerPermission({
        permission: platformSmokeReadPermission,
        description: "Read the platform smoke route.",
      });
      registry.registerRoute({
        name: platformSmokeRouteName,
        method: "GET",
        path: "/smoke/:id",
        auth: { kind: "authenticated", permissions: [platformSmokeReadPermission] },
        observability: { kind: "profile", profile: platformSmokeEchoObservabilityProfileName },
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
      if (options.workItemAcceptance !== undefined) {
        registerPlatformSmokeWorkItemAcceptance(registry, options.workItemAcceptance, options);
      }
      registry.registerJob({
        name: platformSmokeJobName,
        messageType: platformSmokeJobMessageType,
        observability: { kind: "profile", profile: platformSmokeRebuildObservabilityProfileName },
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
      registry.registerJob({
        name: platformSmokeWorkItemAcceptedJobName,
        messageType: platformSmokeWorkItemAcceptedJobMessageType,
        observability: { kind: "profile", profile: platformSmokeWorkItemDeliveryObservabilityProfileName },
        validator: platformSmokeWorkItemAcceptedValidator,
        handler: {
          handle: (message, context) => {
            deps.logger.write({
              level: "info",
              message: "platform-smoke.persistence.work-item.completed",
              correlationId: context.correlationId,
              fields: { messageType: String(message.type) },
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
}

export const platformSmokeApp = createPlatformSmokeApp();

function registerPlatformSmokeWorkItemAcceptance(
  registry: Parameters<ReturnType<typeof definePlatformApp>["mount"]>[0],
  dependencies: PlatformSmokeAcceptWorkItemDependencies,
  options: Pick<PlatformSmokeAppOptions, "diagnosticDefinitions">,
): void {
  registry.registerObservabilityProfile(platformSmokeWorkItemAcceptanceObservabilityProfile);
  registry.registerObservabilityProfile(platformSmokeWorkItemAdmissionObservabilityProfile);
  registry.registerPermission({
    permission: platformSmokeWorkItemCreatePermission,
    description: "Accept the bounded platform smoke work item.",
  });
  registry.registerRoute({
    name: platformSmokeWorkItemAdmissionRouteName,
    method: "POST",
    path: "/smoke/work-items/admission",
    auth: { kind: "authenticated", permissions: [platformSmokeWorkItemCreatePermission] },
    observability: { kind: "profile", profile: platformSmokeWorkItemAdmissionObservabilityProfileName },
    validator: platformSmokeWorkItemAcceptanceValidator,
    handler: {
      handle: () => ({ status: 204, body: undefined }),
    },
  });
  registry.registerRoute({
    name: platformSmokeWorkItemAcceptanceRouteName,
    method: "POST",
    path: "/smoke/work-items",
    auth: { kind: "authenticated", permissions: [platformSmokeWorkItemCreatePermission] },
    observability: { kind: "profile", profile: platformSmokeWorkItemAcceptanceObservabilityProfileName },
    validator: platformSmokeWorkItemAcceptanceValidator,
    handler: {
      async handle(_request, context) {
        const diagnostics = workItemInvocationDiagnostics(context, options);
        const id = platformSmokeWorkItemId(String(context.requestId));
        if (!id.ok) {
          diagnostics.returned(id.error);
          return { status: 500, body: { status: "not-accepted" as const } };
        }
        const accepted = await acceptPlatformSmokeWorkItem({
          id: id.value,
          acceptedAt: context.now,
          causationId: causationId(String(context.requestId)),
          correlationId: context.correlationId,
        }, dependencies, diagnostics.invocation);
        if (!accepted.ok) {
          diagnostics.returned(accepted.error);
          return {
            status: accepted.error.code === "PERSISTENCE_DUPLICATE" ? 409 : 503,
            body: { status: "not-accepted" as const },
            observability: { errorClass: accepted.error.code, diagnosticRecord: platformSmokeAcceptanceFailure(accepted.error.code) },
          };
        }
        return {
          status: 202,
          body: {
            workItemId: String(accepted.value.workItem.id),
            status: accepted.value.workItem.state,
          },
        };
      },
    },
  });
}

const intrinsicPromiseThen = Promise.prototype.then;
/** Only validated copies are compared; finding a source record is not a delivery attempt. */
function workItemInvocationDiagnostics(context: { readonly onDiagnostic?: (record: DiagnosticRecord) => unknown },
  options: Pick<PlatformSmokeAppOptions, "diagnosticDefinitions">) {
  const builtinDefinitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions,
    ...platformPersistenceDiagnosticCatalog.definitions, ...platformSmokeDiagnosticCatalog.definitions];
  let definitions = builtinDefinitions;
  try { definitions = [...builtinDefinitions, ...(options.diagnosticDefinitions ?? [])]; } catch { /* Optional selection cannot replace application behavior. */ }
  let sink: ((record: DiagnosticRecord) => unknown) | undefined;
  try { const candidate = context.onDiagnostic; if (typeof candidate === "function") sink = candidate; } catch { /* An unavailable observer stays unavailable. */ }
  const attempted = new Map<string, number>();
  const selected = (record: DiagnosticRecord) => selectDiagnosticEvidence(definitions, { diagnosticRecord: record }).diagnosticRecord;
  const observe = (record: DiagnosticRecord): void => {
    const checked = selected(record);
    if (checked === undefined || sink === undefined) return;
    // selectDiagnosticEvidence produces owned, plain, frozen data without toJSON/accessors.
    const key = JSON.stringify(checked);
    attempted.set(key, (attempted.get(key) ?? 0) + 1);
    try {
      const pending = sink.call(context, checked);
      if (pending === undefined) return;
      const ignore = (): void => undefined;
      try { Reflect.apply(intrinsicPromiseThen, pending, [undefined, ignore]); }
      catch { Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [undefined, ignore]); }
    } catch { /* The attempted observation must not replace application results or throws. */ }
  };
  return {
    // Supplying {} deliberately overrides any writer-level diagnostic default on an opted-out route.
    invocation: sink === undefined ? {} : { diagnosticDefinitions: definitions, onDiagnostic: observe } satisfies PlatformPersistenceDiagnosticOptions,
    returned(error: unknown): void {
      const evidence = selectDiagnosticEvidence(definitions, error);
      const remaining = new Map(attempted);
      for (const record of [evidence.diagnosticRecord, ...(evidence.relatedDiagnosticRecords ?? [])]) {
        if (record === undefined) continue;
        const key = JSON.stringify(record);
        const previous = remaining.get(key) ?? 0;
        if (previous > 0) remaining.set(key, previous - 1);
        else observe(record);
      }
    },
  };
}

function isPlatformSmokeRebuildPayload(value: unknown): value is PlatformSmokeRebuildPayload {
  return typeof value === "object"
    && value !== null
    && "rebuild" in value
    && typeof (value as { readonly rebuild?: unknown }).rebuild === "boolean";
}

function isPlatformSmokeWorkItemAcceptedPayload(value: unknown): value is PlatformSmokeWorkItemAcceptedPayload {
  return typeof value === "object"
    && value !== null
    && "outboxEntryId" in value
    && typeof (value as { readonly outboxEntryId?: unknown }).outboxEntryId === "string"
    && (value as { readonly outboxEntryId: string }).outboxEntryId.length > 0;
}

function unwrapPlatformName<TName extends string>(
  result: Result<TName, PlatformContractError>,
): TName {
  if (!result.ok) {
    throw new Error(result.error.defaultMessage);
  }

  return result.value;
}

export type PlatformSmokeJobMessage = QueueMessage<JsonValue>;
