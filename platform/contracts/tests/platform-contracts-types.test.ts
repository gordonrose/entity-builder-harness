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
import {
  definePlatformApp,
  featureFlagName,
  fixedFeatureFlagReader,
  platformAppId,
  platformApiVersion,
  platformHealthName,
  platformJobName,
  platformRouteName,
  type FeatureFlagReader,
  type PlatformApp,
  type PlatformJobContext,
  type PlatformJobRegistration,
  type PlatformMountDeps,
  type PlatformPermissionDeclaration,
  type PlatformRequest,
  type PlatformRequestContext,
  type PlatformResponse,
  type PlatformRouteRegistration,
} from "../src/index";

const appId = platformAppId("crm");
const routeName = platformRouteName("crm.deals.show");
const jobName = platformJobName("crm.deals.recalculate-score");
const healthName = platformHealthName("crm.readiness");
const apiVersion = platformApiVersion("v1");
const flagName = featureFlagName("crm.deals.bulk-import");

if (!appId.ok || !routeName.ok || !jobName.ok || !healthName.ok || !apiVersion.ok || !flagName.ok) {
  throw new Error("Expected valid platform contract primitives.");
}

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
const dealReadPermission = "deal:read";
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
  validator: routeValidator,
  handler: {
    handle: () => response,
  },
};
void route.handler.handle(request, requestContext);

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
