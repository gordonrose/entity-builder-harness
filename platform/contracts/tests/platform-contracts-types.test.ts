import type {
  Clock,
  ConfigSource,
  CorrelationId,
  HealthCheckName,
  ISODateTime,
  Logger,
  Metrics,
  MonitoringComponentName,
  Principal,
  QueueMessage,
  QueueMessageType,
  TenantContext,
  Validator,
} from "@kanbien/core";
import { tenantContext, tenantId } from "@kanbien/core/tenancy";
import {
  definePlatformApp,
  featureFlagName,
  fixedFeatureFlagReader,
  platformAppId,
  platformApiVersion,
  platformCapabilityName,
  platformHealthName,
  platformJobName,
  platformObservabilityProfileName,
  platformRouteName,
  type FeatureFlagReader,
  type PlatformApp,
  type PlatformOperationalNomenclature,
  type PlatformCapabilityObservabilityProfile,
  type PlatformJobContext,
  type PlatformJobRegistration,
  type PlatformMountDeps,
  type PlatformPermissionDeclaration,
  type PlatformRequest,
  type PlatformRequestContext,
  type PlatformResponse,
  type PlatformRouteRegistration,
  type PlatformTenantResolver,
} from "../src/index";

const appId = platformAppId("crm");
const routeName = platformRouteName("crm.deals.show");
const jobName = platformJobName("crm.deals.recalculate-score");
const healthName = platformHealthName("crm.readiness");
const apiVersion = platformApiVersion("v1");
const capabilityName = platformCapabilityName("crm.deal.export"); // Create one checked capability identity for the nomenclature type proof.
const observabilityProfileName = platformObservabilityProfileName("crm.deal.export"); // Create one checked profile identity for the capability observability proof.
const flagName = featureFlagName("crm.deals.bulk-import");

if (!appId.ok || !routeName.ok || !jobName.ok || !healthName.ok || !apiVersion.ok || !capabilityName.ok || !observabilityProfileName.ok || !flagName.ok) {
  throw new Error("Expected valid platform contract primitives.");
}

const nomenclature: PlatformOperationalNomenclature = { // Prove a complete provider-neutral operational vocabulary can be declared without a provider SDK.
  capability: capabilityName.value, // Use the separately branded stable capability identity.
  action: "export", // Use a controlled business action instead of an HTTP method.
  actorType: "user", // Use only a bounded actor category rather than an actor identifier.
  interactionSource: "voice", // Keep voice as an initiation channel, not an execution context.
  executionContext: "worker", // Record where the export actually executes.
  jobDeliveryDisposition: "retry_scheduled", // Record the worker delivery decision separately from the business result.
  outcome: "failed", // Record the logical operational result with the canonical outcome vocabulary.
  errorClass: "PLATFORM_WORKER_HANDLER_FAILED", // Use a bounded error code rather than an error message or provider payload.
}; // Finish the valid nomenclature example.
void nomenclature; // Mark the type-proof value as intentionally used.

// @ts-expect-error capability actions must use the reviewed controlled vocabulary.
const invalidNomenclatureAction: PlatformOperationalNomenclature = { ...nomenclature, action: "edit" };
void invalidNomenclatureAction;

// @ts-expect-error interaction sources and execution contexts are intentionally different dimensions.
const invalidNomenclatureExecutionContext: PlatformOperationalNomenclature = { ...nomenclature, executionContext: "voice" };
void invalidNomenclatureExecutionContext;

// @ts-expect-error operational field labels do not accept a raw identifier in place of a branded capability name.
const invalidNomenclatureCapability: PlatformOperationalNomenclature = { ...nomenclature, capability: "crm.deal.export" };
void invalidNomenclatureCapability;

const observabilityProfile: PlatformCapabilityObservabilityProfile = {
  name: observabilityProfileName.value,
  capability: capabilityName.value,
  action: "export",
  signals: ["operational_log", "metric", "trace"],
  logFieldNames: ["capability", "action", "outcome"],
  metricDimensionFieldNames: ["capability", "action", "outcome"],
  traceAttributeNames: ["capability", "action", "outcome"],
  nfrObjectives: [{ nfrClass: "async_completion", measurement: "job_execution_latency" }],
};
void observabilityProfile;

// @ts-expect-error NFR objective classes must use the controlled central-policy vocabulary.
const invalidObservabilityProfile: PlatformCapabilityObservabilityProfile = { ...observabilityProfile, nfrObjectives: [{ nfrClass: "fast", measurement: "job_execution_latency" }] };
void invalidObservabilityProfile;

const logger: Logger = { write: () => undefined };
const metrics: Metrics = { record: () => undefined };
const config: ConfigSource = { get: () => undefined };
const clock: Clock = { now: () => new Date("2026-07-08T00:00:00.000Z") };
const flags: FeatureFlagReader = fixedFeatureFlagReader({ [flagName.value]: true });
const tenant = { tenantId: "tenant-123", isolationKey: "tenant-123" } as TenantContext;
const principal = {
  id: "principal-123",
  type: "user",
  subject: "user@example.test",
  claims: {},
} as Principal;
const correlationId = "request-123" as CorrelationId;
const now = "2026-07-08T00:00:00.000Z" as ISODateTime;

const requestContext: PlatformRequestContext = {
  requestId: correlationId,
  correlationId,
  now,
  tenant,
  principal,
  logger,
  metrics,
  config,
  flags,
  clock,
  method: "GET",
  path: "/v1/crm/deals/:id",
};

const request: PlatformRequest = {
  params: { id: "deal-123" },
  query: {},
  headers: {},
};
void request;

const response: PlatformResponse = {
  status: 200,
  body: { ok: true },
};
void response;

const routeValidator: Validator<unknown> = {
  validate: (_value): _value is unknown => true,
  explain: () => ({ valid: true, issues: [] }),
};
const jobPayloadValidator: Validator<QueueMessage["payload"]> = {
  validate: (_value): _value is QueueMessage["payload"] => true,
  explain: () => ({ valid: true, issues: [] }),
};
const dealReadPermission = "crm.deal:read";
const permissionDeclaration: PlatformPermissionDeclaration = {
  permission: dealReadPermission,
  description: "Read deals.",
};

const route: PlatformRouteRegistration = {
  name: routeName.value,
  method: "GET",
  path: "/deals/:id",
  apiVersion: apiVersion.value,
  auth: { kind: "authenticated", permissions: [dealReadPermission] },
  observability: { kind: "profile", profile: observabilityProfileName.value },
  validator: routeValidator,
  handler: {
    handle: () => response,
  },
};
void route.handler.handle(request, requestContext);

const tenantResolver: PlatformTenantResolver = {
  resolve: async ({ request: tenantRequest, principal: tenantPrincipal }) => {
    void tenantRequest;
    void tenantPrincipal;
    return tenantContext({ tenantId: tenantId("tenant-123") });
  },
};
void tenantResolver;

const tenantAndResourceRoute: PlatformRouteRegistration = {
  ...route,
  tenant: "required",
  resourceAuthorization: {
    permission: dealReadPermission,
    resolve: ({ request: authorizationRequest, context }) => {
      void authorizationRequest;
      void context;
      return { kind: "authorize", facts: { source: "type-test" } };
    },
  },
};
void tenantAndResourceRoute;

const message = {
  id: "queue-message-123",
  type: "crm.deals.recalculate-score",
  version: 1,
  enqueuedAt: now,
  payload: { dealId: "deal-123" },
} as unknown as QueueMessage;

const jobContext: PlatformJobContext = {
  jobName: jobName.value,
  message,
  correlationId,
  now,
  logger,
  metrics,
  config,
  flags,
  clock,
};
const job: PlatformJobRegistration = {
  name: jobName.value,
  messageType: "crm.deals.recalculate-score" as QueueMessageType,
  observability: { kind: "profile", profile: observabilityProfileName.value },
  validator: jobPayloadValidator,
  handler: {
    handle: (_message, _context) => undefined,
  },
};
void job.handler.handle(message, jobContext);

const deps: PlatformMountDeps = { logger, metrics, config, flags, clock };
const app: PlatformApp = definePlatformApp({
  id: appId.value,
  name: "CRM",
  version: "0.0.0",
  mount(registry, mountDeps) {
    void mountDeps;
    registry.registerPermission(permissionDeclaration);
    registry.registerObservabilityProfile(observabilityProfile);
    registry.registerRoute(route);
    registry.registerJob(job);
    registry.registerHealthCheck({
      name: healthName.value,
      check: {
        check: () =>
          ({
            name: healthName.value as unknown as HealthCheckName,
            type: "readiness",
            component: { type: "api", name: "crm" as unknown as MonitoringComponentName },
            status: "healthy",
            checkedAt: now,
          }),
      },
    });
    registry.registerConfigSchema({
      parse: () => ({ ok: true, value: { crmEnabled: true } }),
    });
  },
});
void app.mount(
  {
    registerPermission: () => ({ ok: true, value: undefined }),
    registerRoute: () => ({ ok: true, value: undefined }),
    registerJob: () => ({ ok: true, value: undefined }),
    registerObservabilityProfile: () => ({ ok: true, value: undefined }),
    registerHealthCheck: () => ({ ok: true, value: undefined }),
    registerConfigSchema: () => ({ ok: true, value: undefined }),
  },
  deps,
);

// @ts-expect-error route methods are constrained to known HTTP methods.
const invalidMethod: PlatformRouteRegistration = { ...route, method: "TRACE" };
void invalidMethod;

// @ts-expect-error platform app ids must be explicitly created and branded.
definePlatformApp({ ...app, id: "crm" });
