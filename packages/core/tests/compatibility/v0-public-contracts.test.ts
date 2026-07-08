import {
  allow,
  auditActor,
  auditEvent,
  auditEventId,
  auditEventType,
  auditTarget,
  booleanConfigValue,
  concurrencyToken,
  correlationId,
  createLogRedactor,
  dataClassification,
  diagnosticDescriptor,
  eventEnvelope,
  eventId,
  eventType,
  eventVersion,
  fixedAuthenticator,
  fixedAuthorizer,
  fixedHealthCheck,
  fixedSecurityPolicyEvaluator,
  fixedTenantResolver,
  hash,
  healthCheckName,
  healthCheckResult,
  inMemoryAuditRecorder,
  inMemoryEventBus,
  inMemoryQueue,
  inMemoryRepository,
  inMemoryUnitOfWork,
  invalidResult,
  isOk,
  isoDateTime,
  logRecord,
  messageDescriptor,
  metricLabels,
  metricName,
  metricPoint,
  metricUnit,
  monitoringComponent,
  monitoringSignalDefinition,
  monitoringSignalName,
  noopLogger,
  page,
  pageRequest,
  pageTotals,
  permission,
  principal,
  principalId,
  queueAttempt,
  queueDelaySeconds,
  queueDelivery,
  queueIdempotencyKey,
  queueMessage,
  queueMessageId,
  queueMessageType,
  queueSendOptions,
  recordConfigSource,
  redactingLogger,
  requestContext,
  resourceRef,
  secretString,
  securityPolicyAllowed,
  securityPolicyId,
  stringConfigValue,
  tenantContext,
  tenantId,
  validResult,
  validationIssue,
  type AuditRecorder,
  type Authenticator,
  type Authorizer,
  type ConfigSource,
  type DiagnosticDescriptor,
  type EventBus,
  type EventEnvelope,
  type HealthCheck,
  type Logger,
  type Metrics,
  type Queue,
  type QueueMessage,
  type Repository,
  type RequestContext,
  type Result,
  type SecurityPolicyEvaluator,
  type TenantResolver,
  type UnitOfWork,
  type Validator,
} from "../../src/index";

interface DealRecord {
  readonly id: string;
  readonly title: string;
  readonly version: ReturnType<typeof concurrencyToken>;
}

const tenant = tenantId("tenant-123");
const tenantScope = tenantContext({ tenantId: tenant, isolationKey: "tenant-123" });
const currentCorrelationId = correlationId("request-123");
const timestampResult = isoDateTime("2026-07-08T00:00:00.000Z");

if (!isOk(timestampResult)) {
  throw new Error("Expected compatibility fixture timestamp to be valid.");
}

const now = timestampResult.value;
const request: RequestContext = requestContext({
  correlationId: currentCorrelationId,
  now,
});
void request;

const displayReason = messageDescriptor({
  code: "DEAL_VIEW_ALLOWED",
  defaultMessage: "Deal view allowed.",
  messageKey: "deals.view.allowed",
  params: { resource: "deal" },
});

const configSource: ConfigSource = recordConfigSource({
  API_URL: "https://api.example.test",
  FEATURE_ENABLED: true,
});
const apiUrl = stringConfigValue(configSource, "API_URL");
const featureEnabled = booleanConfigValue(configSource, "FEATURE_ENABLED");
void apiUrl;
void featureEnabled;

const logger: Logger = redactingLogger(noopLogger, createLogRedactor({ additionalKeys: ["tenantSecret"] }));
logger.write(
  logRecord({
    level: "info",
    message: "Compatibility fixture log record.",
    correlationId: currentCorrelationId,
    fields: { tenantId: tenant, tenantSecret: "hidden" },
  }),
);

const validationFieldIssue = validationIssue({
  path: ["deal", "title"],
  code: "VALIDATION_REQUIRED",
  defaultMessage: "Deal title is required.",
  messageKey: "validation.required",
  params: { field: "title" },
});
const validationFailure = invalidResult(validationFieldIssue);
const dealTitleValidator: Validator<string> = {
  validate: (value): value is string => typeof value === "string" && value.length > 0,
  explain: (value) => (typeof value === "string" && value.length > 0 ? validResult : validationFailure),
};
void dealTitleValidator;

const actor = principal({
  id: principalId("principal-123"),
  type: "user",
  subject: "user@example.test",
  currentTenantId: tenant,
  claims: { emailVerified: true },
  scopes: ["deals:read"],
});
const authenticator: Authenticator<unknown> = fixedAuthenticator(actor);
void authenticator;

const dealResource = resourceRef({ type: "deal", id: "deal-123" });
const dealViewPermission = permission("deal", "view");
const authorizer: Authorizer = fixedAuthorizer(allow({ reason: displayReason, evidence: { source: "fixture" } }));
void authorizer.decide({
  principal: actor,
  permission: dealViewPermission,
  tenantId: tenant,
  resource: dealResource,
  attributes: {
    principal: { team: "sales" },
    resource: { stage: "qualified" },
    environment: { channel: "api" },
  },
});

const tenantResolver: TenantResolver<unknown> = fixedTenantResolver(tenantScope);
void tenantResolver;

const initialDeal: DealRecord = {
  id: "deal-123",
  title: "Example deal",
  version: concurrencyToken("v1"),
};
const repository: Repository<DealRecord, string> = inMemoryRepository({
  getId: (deal) => deal.id,
  getConcurrencyToken: (deal) => deal.version,
  initialEntities: [initialDeal],
});
void repository.save(initialDeal, { expectedConcurrencyToken: initialDeal.version });

const pageRequestResult = pageRequest({ limit: 25, cursor: "next" });
const totalsResult = pageTotals({ totalItems: 100, totalMatchingItems: 1 });
if (!isOk(pageRequestResult) || !isOk(totalsResult)) {
  throw new Error("Expected compatibility fixture page values to be valid.");
}
const dealPage = page({
  items: [initialDeal],
  nextCursor: "next-page",
  totals: totalsResult.value,
});
void dealPage;

const unitOfWork: UnitOfWork = inMemoryUnitOfWork();
void unitOfWork.run((transaction) => {
  transaction.afterCommit(() => undefined);
  return "committed";
});

const eventTypeResult = eventType("deal.viewed");
const eventVersionResult = eventVersion(1);
if (!isOk(eventTypeResult) || !isOk(eventVersionResult)) {
  throw new Error("Expected compatibility fixture event values to be valid.");
}
const dealViewedEvent: EventEnvelope = eventEnvelope({
  id: eventId("event-123"),
  type: eventTypeResult.value,
  version: eventVersionResult.value,
  occurredAt: now,
  tenantId: tenant,
  correlationId: currentCorrelationId,
  payload: { dealId: "deal-123" },
});
const eventBus: EventBus = inMemoryEventBus();
void eventBus.publish([dealViewedEvent]);

const queueTypeResult = queueMessageType("deal.recalculate-score");
const queueDelayResult = queueDelaySeconds(30);
const queueAttemptResult = queueAttempt(1);
if (!isOk(queueTypeResult) || !isOk(queueDelayResult) || !isOk(queueAttemptResult)) {
  throw new Error("Expected compatibility fixture queue values to be valid.");
}
const queueWork: QueueMessage = queueMessage({
  id: queueMessageId("queue-message-123"),
  type: queueTypeResult.value,
  enqueuedAt: now,
  tenantId: tenant,
  correlationId: currentCorrelationId,
  idempotencyKey: queueIdempotencyKey("deal-123:score"),
  payload: { dealId: "deal-123" },
});
const queue: Queue = inMemoryQueue();
void queue.send(queueWork, queueSendOptions({ delaySeconds: queueDelayResult.value }));
void queueDelivery({
  message: queueWork,
  receivedAt: now,
  attempt: queueAttemptResult.value,
});

const auditTypeResult = auditEventType("deal.viewed");
const auditTargetResult = auditTarget({ type: "deal", id: "deal-123" });
if (!isOk(auditTypeResult) || !isOk(auditTargetResult)) {
  throw new Error("Expected compatibility fixture audit values to be valid.");
}
const audit = auditEvent({
  id: auditEventId("audit-123"),
  type: auditTypeResult.value,
  outcome: "succeeded",
  actor: auditActor({ type: "user", id: actor.id, subject: actor.subject }),
  tenantId: tenant,
  occurredAt: now,
  correlationId: currentCorrelationId,
  target: auditTargetResult.value,
  reason: displayReason,
  metadata: { source: "compatibility-fixture" },
});
const auditRecorder: AuditRecorder = inMemoryAuditRecorder();
void auditRecorder.record(audit);

const classification = dataClassification({
  kind: "tenant-data",
  sensitivity: "confidential",
  reason: displayReason,
});
const secret = secretString("example-secret");
const storedHash = hash({ algorithm: "fixture-hash-v1", value: "hash-value" });
const securityEvaluator: SecurityPolicyEvaluator<unknown> = fixedSecurityPolicyEvaluator(
  securityPolicyAllowed({
    policyId: securityPolicyId("fixture.policy"),
    evidence: { classification: classification.sensitivity },
  }),
);
void secret;
void storedHash;
void securityEvaluator;

const diagnostic: DiagnosticDescriptor = diagnosticDescriptor({
  failureKind: "user_input",
  failureSource: "user",
  severity: "warning",
  recovery: "user_correctable",
  action: "ask_user",
  messageKey: "diagnostics.csv.invalid_row",
  facts: { importId: "csv-import-123", rowNumber: 42 },
});
void diagnostic;

const component = monitoringComponent({ type: "api", name: "deals.api" });
const health = healthCheckResult({
  name: healthCheckName("deals.api.readiness"),
  type: "readiness",
  component,
  status: "healthy",
  checkedAt: now,
  durationMs: 12,
  message: displayReason,
  metadata: { dependency: "database" },
});
const healthCheck: HealthCheck = fixedHealthCheck(health);
void healthCheck;

const labels = metricLabels({ route: "deals.show", statusClass: "2xx" });
const metrics: Metrics = {
  record: () => undefined,
};
void metrics.record(
  metricPoint({
    name: metricName("deals.requests.total"),
    kind: "counter",
    value: 1,
    unit: metricUnit("count"),
    recordedAt: now,
    labels,
  }),
);
void monitoringSignalDefinition({
  name: monitoringSignalName("deals.api.readiness"),
  category: "traffic",
  owner: "platform",
  intents: ["health-detection", "alerting"],
  component,
  metric: {
    name: metricName("deals.requests.total"),
    kind: "counter",
    unit: metricUnit("count"),
  },
  description: displayReason,
});

const compatibilityResult: Result<string> = { ok: true, value: "compatible" };
void compatibilityResult;
