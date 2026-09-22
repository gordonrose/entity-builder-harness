# Chat Session: 2026-09-19-01-27 apply-worker-observability-profiles

<!-- agentic-session
id: 2026-09-19-01-27-it-s-been-a-while-since-i-worked-on-this-can-you-catch-me-up
task: it's been a while since i worked on this - can you catch me up on this thread- what have we been working on?
branch: chat/2026-09-19-01-27-it-s-been-a-while-since-i-worked-on-this-can-you-catch-me-up
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-09-19-01-27-it-s-been-a-while-since-i-worked-on-this-can-you-catch-me-up-3744436689
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-09-19T00:27:23Z
transcript_provider: codex
transcript_path: /home/owner/.codex/sessions/2026/08/31/rollout-2026-08-31T01-09-34-01a05526-6410-73f3-a691-39a27d433af7.jsonl
transcript_bytes: 97691410
transcript_source: codex path: /home/owner/.codex/sessions/2026/08/31/rollout-2026-08-31T01-09-34-01a05526-6410-73f3-a691-39a27d433af7.jsonl
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc: 2026-09-21T23:48:49Z
latest_commit_sha: 3182c74
chat_duration: 256886s (02:23:21:26)
estimated_chat_tokens: 24422853 estimated from chat transcript bytes (97691410 bytes; source: codex path: /home/owner/.codex/sessions/2026/08/31/rollout-2026-08-31T01-09-34-01a05526-6410-73f3-a691-39a27d433af7.jsonl)
estimated_chat_cost: unavailable; no pricing profile selected
estimated_chat_cost_basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE
-->

## Initial Intent

it's been a while since i worked on this - can you catch me up on this thread- what have we been working on?

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- What does an observability profile mean in the worker path, and can the
  platform finish the local profile-consumption proof before provider queue
  work begins?

## Issues Raised

- The worker previously emitted generic job telemetry even when a job declared
  an explicit observability profile or opt-out. The declaration therefore did
  not yet control runtime signal emission.

## Decisions Made

- The profile declaration and its pure field-projection helpers remain in
  `platform/contracts`; `platform/workers` resolves the profile and emits
  provider-neutral signals through `platform/observability` and Core ports.
- A worker emits capability telemetry only when a registered job profile
  permits that signal and its relevant canonical fields. Explicit job opt-outs
  emit no capability telemetry; unregistered queue messages have no app-owned
  profile and are dead-lettered without invented capability evidence.
- Logger, metrics, and tracer failure are best effort for this operational
  path. They must not change the job result. Durable audit and security-record
  guarantees remain separately designed work.
- The same rule now applies to HTTP routes: a matched route resolves its
  profile before policy gates, uses only that profile's safe canonical facts,
  and emits no capability telemetry when it has an explicit opt-out.
- Existing HTTP transport timeouts are capacity guardrails, not NFR promises.
  A target-owned timeout-budget catalogue remains a later policy and
  adapter/infra validation slice; provider-backed worker timeout and lease
  policy remains separately deferred.
- Each target SLO objective has a separate error budget. Future alarms must
  use sustained, minimum-sample-aware burn rather than paging on one slow
  request; low-volume periods must state insufficient confidence and use a
  named synthetic check.
- Alert definitions must declare one primary family: capability SLO,
  platform/infrastructure health, or security detection. They may link safe
  evidence across families but cannot substitute one family for another.
- A future target `observability.slos` catalogue will own one record per
  independently evaluated objective. Provider alarms remain in
  `observability.alarms` and reference that record rather than duplicate its
  thresholds or burn calculation.
- A future histogram exporter will implement the injected Core `Metrics` port
  at target composition. It must use an approved target metric-series catalogue
  with threshold-aligned buckets and bounded labels, preserve evidence coverage,
  and remain outside request/job success semantics.
- A future target dashboard catalogue must distinguish platform health,
  capability SLO, and restricted security views; no data is not a healthy SLO
  result. Low-volume targets require declared synthetic checks that exercise
  real boundaries with a least-privilege, safe fixture.
- Observability data has a target-owned lifecycle: ordinary logs, metrics,
  traces, security signals, and audit evidence need different retention and
  access rules. SLO metrics are complete by default; sampling is explicit and
  exporter loss is recorded as coverage failure.
- Ordinary capability observability has a staged completion gate: target policy,
  histogram adapter, target composition/IaC, public synthetic proof, SLO
  calculation, and exporter-failure/alert-delivery proof. Local in-memory
  emission alone is not a production-operational claim.


- Decision: Record RAG knowledge disposition: covered
  Rationale: The provider-neutral observability-profile implementation activates existing platform runtime guidance: platform owns safe telemetry mechanisms, app routes/jobs use runtime seams, and provider translation remains in a later adapter.

## Context Hygiene



- Summary: Runtime source, tests, package maps, implementation plan, handbook, and session evidence are the durable record for the completed profile-consumption slice; temporary test symlinks were removed.
  Durable evidence: Verification passed: platform contracts, observability, workers, server, and platform-smoke checks. Deferred target adapter/SLO/dashboard/security/audit decisions are recorded in the platform plan and handbook.

## Activity Log

### 2026-09-19T00:27:23Z - Session started

Initial intent: it's been a while since i worked on this - can you catch me up on this thread- what have we been working on?

### 2026-09-21T00:00:00Z - Worker observability-profile consumption implemented

- Updated `platform/contracts` with pure, tested profile signal, field, and
  latency-projection helpers.
- Updated `platform/workers` to resolve job profiles, suppress opt-out signals,
  project only approved fields, and emit only declared latency intervals.
- Updated `platform/observability` so logger and metric failures are best
  effort, matching the existing tracer fallback rule.
- Updated the platform implementation plan, package/source maps, and learning
  handbook. The handbook records the completed worker slice and leaves server
  profile consumption as the next observability implementation slice.
- Verification passed: `npm run platform:contracts:check`,
  `npm run platform:observability:check`, and
  `npm run platform:workers:check`.

### 2026-09-21T00:00:00Z - HTTP observability-profile consumption implemented

- Updated `platform/server` to resolve a matched route's registered profile
  before route policy runs. Its profile controls ordinary operational logs,
  metrics, traces, and the request/response timer; emitted fields are projected
  from the canonical capability vocabulary only.
- A malformed body, admission refusal, authentication denial, validation
  failure, or handler failure for a known route uses that route's profile. An
  explicit route opt-out emits no capability telemetry. Failures before a route
  can be identified retain separate generic platform-server evidence rather
  than being labelled as a business capability.
- Extended server runtime proof for projected log/metric/trace fields, declared
  request/response latency, and opt-out suppression. Extended the real
  platform-smoke app proof to verify its registered route profile on an
  unauthenticated and successful request. Updated the platform plan, server
  responsibility maps, and the learning handbook.
- Kept the profile-governed completion counter distinct as
  `platform.server.request.outcome`; the older generic request timer retains
  `platform.server.request`, so a future metrics backend never sees a counter
  and timer under the same metric identity.
- Verification passed: `npm run platform:server:check` (outside the sandbox
  because its runtime suite starts a loopback HTTP listener) and
  `npm run app:platform-smoke:check`.

### 2026-09-21T00:00:00Z - Timeout-budget policy gap recorded

- Recorded the current server transport safeguards and their boundary: they
  cap damage but do not define interactive-performance expectations.
- Added deferred target timeout-budget catalogue requirements, including
  ingress/server/downstream deadline ordering, cleanup reserve, retries, safe
  timeout outcomes, and provider-worker execution/lease/DLQ concerns.
- No runtime timeout value, adapter, infrastructure resource, or AWS state
  changed. The observability lesson continues with histogram-derived SLO
  evaluation and alert behaviour before this later timeout-policy
  implementation slice.

### 2026-09-21T00:00:00Z - Error-budget alerting rule recorded

- Recorded the distinction between separate availability and latency budgets,
  the burn-rate calculation, deliberate short/long alert windows, and the
  low-volume synthetic-check fallback.
- No numerical target, provider exporter, dashboard, alarm resource, or AWS
  state was selected or changed. Those remain target-policy and adapter work
  after the observability teaching sequence.

### 2026-09-21T00:00:00Z - Alert-family boundary recorded

- Recorded the separate question, owner, policy home, and evidence boundary for
  capability SLO, platform/infrastructure health, and security alerts.
- Confirmed the current staging alarm catalogue covers infrastructure health;
  capability SLO delivery needs an application metrics adapter, while security
  detection needs its own future signal/delivery policy.
- No alarm threshold, notification recipient, target profile, IaC resource, or
  AWS state changed.

### 2026-09-21T00:00:00Z - Target SLO catalogue shape recorded

- Recorded the planned separation of target SLO meaning/calculation from
  provider alarm delivery, with one objective per record and explicit
  population, evidence, budget, response, and lifecycle fields.
- No `observability.slos` target configuration exists yet; no SLO value,
  exporter, dashboard, IaC resource, or AWS state was selected or changed.

### 2026-09-21T00:00:00Z - Histogram-exporter boundary recorded

- Recorded the provider-neutral Core metrics seam, target metric-series
  catalogue, threshold-aligned histogram requirements, bounded exporter
  behaviour, and incomplete-evidence rule.
- No metrics provider, adapter package, metric backend, dashboard, alarm, or
  AWS state was selected or changed.

### 2026-09-21T00:00:00Z - Dashboard and synthetic-check boundary recorded

- Recorded target-owned dashboard evidence requirements, explicit
  healthy/partial/no-data states, separate audience/access boundaries, and the
  minimum policy facts for synthetic checks.
- No dashboard, synthetic monitor, identity, fixture, target configuration,
  IaC resource, or AWS state was selected or changed.

### 2026-09-21T00:00:00Z - Observability data-lifecycle boundary recorded

- Recorded separate purpose/retention/access requirements for operational
  logs, aggregate metrics, traces, security signals, and audit events; the
  current 14-day staging log retention applies only to the existing log group.
- Recorded least-privilege evidence audiences, auditable break-glass access,
  complete initial SLO measurement, and the distinction between sampling and
  exporter coverage loss.
- No retention value, telemetry store, access identity, provider resource, or
  AWS state was selected or changed.

### 2026-09-21T00:00:00Z - Observability delivery readiness roadmap recorded

- Recorded the completed local provider-neutral instrumentation slice and the
  dependency-ordered future implementation/proof gates required before calling
  target capability observability operational.
- No provider, adapter implementation, target policy value, dashboard, alarm,
  IaC resource, or AWS state was selected or changed.


### 2026-09-21T22:34:41Z - Context hygiene

Summary: Runtime source, tests, package maps, implementation plan, handbook, and session evidence are the durable record for the completed profile-consumption slice; temporary test symlinks were removed.

Durable evidence: Verification passed: platform contracts, observability, workers, server, and platform-smoke checks. Deferred target adapter/SLO/dashboard/security/audit decisions are recorded in the platform plan and handbook.


### 2026-09-21T22:34:41Z - ADR disposition

ADR needed: no

Reason: This commit implements and documents an already planned provider-neutral observability vertical slice. Target provider, retention values, SLO values, and infrastructure decisions remain deliberately deferred; create an ADR when one of those durable target choices is selected.


### 2026-09-21T22:36:08Z - Decision

Decision: Record RAG knowledge disposition: covered

Rationale: The provider-neutral observability-profile implementation activates existing platform runtime guidance: platform owns safe telemetry mechanisms, app routes/jobs use runtime seams, and provider translation remains in a later adapter.


### 2026-09-21T22:37:23Z - Commit recorded

Commit: `11283f6`

Message: feat(observability): govern capability telemetry profiles

Summary: Implemented provider-neutral observability-profile consumption for server and worker paths, profile-safe telemetry projection, sink-failure isolation, smoke proof, and the target observability readiness roadmap.

ADR impact: No ADR: this activates existing provider-neutral platform guidance; target provider and infrastructure choices remain deferred.

### 2026-09-22 - Staging metric-delivery selection and local adapter implementation

- Corrected the runtime-implementation workflow's ADR references so it points
  to the four real ADR files rather than ambiguous numbers.
- Selected the staging capability-metrics route as a target-composed AWS
  CloudWatch OpenTelemetry adapter sending only to a task-local collector.
  ADR 0029 records that boundary; no generic platform runtime or application
  module imports an AWS package.
- Added the adapter package with strict target-series validation, bounded
  labels/cardinality, explicit histogram buckets, a private local endpoint,
  and controlled flush/shutdown. Its local type, runtime, build, and boundary
  checks pass.
- Added staging target policy entries for the smoke-read outcome counter and
  request/response histogram, along with provisional 28-day availability,
  p95, and p99 objectives. All records are explicitly selected but not
  deployed/evaluable.
- Extended the existing staging infrastructure check to validate the catalogue
  structure and the SLO-to-histogram relationship without duplicating target
  thresholds in the check.
- No AWS resource, IAM permission, task definition, collector, metric backend,
  dashboard, alarm, or live target configuration changed. AWS SSO was used
  only for prior read-only target inspection.

### 2026-09-22 - Prepared staging collector composition and IaC

- Added the target-only observability composition module. It constructs the
  reviewed CloudWatch OTel adapter from non-secret target configuration and
  injects only its provider-neutral Core `Metrics` port into the generic server.
- The target entrypoint owns startup failure handling and ordered shutdown:
  close the server first, then make the adapter's bounded final flush/shutdown
  attempt. The generic server still has no AWS import.
- Prepared focused CloudFormation source for a pinned ADOT task sidecar, a
  distinct collector log group, a named non-secret SSM collector configuration
  record, narrow execution-role `ssm:GetParameters`, and task-role
  `cloudwatch:PutMetricData`. The sidecar has no published task port; the
  adapter can send only to task-loopback `127.0.0.1:4318`.
- Recorded the ECS limitation explicitly: task-role credentials are shared by
  containers in a task, so reviewed task composition and the fixed loopback
  endpoint complement IAM; this is not per-container credential isolation.
- Increased the planned task definition from 256 CPU / 512 MiB to 512 CPU /
  1024 MiB and reserved 128 CPU / 256 MiB for the collector. This is source
  preparation only, not a live capacity change.
- Local checks passed: CloudWatch adapter, generic server (including injected
  metrics-port proof), sealed image/runtime payload, static infrastructure
  policy, deployment workflow, smoke app, and whitespace validation.
- AWS CloudFormation's read-only `validate-template` operation accepted both
  the freshly rendered foundation template and the service template. This
  checks template syntax and IAM capability declarations; it did not create a
  change set, deploy a container, or inspect/live-test metric delivery.
- The target deploy-readiness manifest now names capability metric delivery as
  a blocking evidence gap. Its governed planning check remains intentionally
  `blocked` with seven blockers; this is honest status, not a failed build.
- Read-only AWS preflight confirms the foundation stack is `UPDATE_COMPLETE`,
  the service stack is `CREATE_COMPLETE`, and the live ECS service is active
  with one desired/running task on task-definition revision `1`. No drift or
  target mutation was attempted in this inspection.
- Deployment sequencing check: do not create an apply-ready service change set
  from this local working tree. The prepared service template requires an image
  containing the new target composition; the live revision-1 ECR image predates
  it. First commit and merge reviewed source, obtain the GitHub-built,
  scan-accepted immutable image digest from `origin/main`, then create and
  review the foundation/service change sets against that exact artifact.
- No AWS CLI mutation, CloudFormation change set, IAM policy application, ECS
  task-definition update, collector deployment, or telemetry delivery occurred.


### 2026-09-21T23:48:49Z - Commit recorded

Commit: `3182c74`

Message: feat(observability): prepare CloudWatch metric delivery

Summary: Added a target-only CloudWatch OpenTelemetry metrics adapter, target composition, prepared ECS collector/IAM/SSM IaC, local and template validation, and durable plan/handbook/readiness evidence; AWS remains unchanged.

ADR impact: ADR 0029 records the task-local collector boundary and ECS task-role limitation.

### 2026-09-22 - Image-publication and service-deployment authority separated

- Found that the protected GitHub workflow combined image publication with a
  CloudFormation service-stack deployment. That would have allowed a
  scan-accepted image run to change the running service without a separately
  reviewed change set.
- Changed the workflow and its verifier so it may only build, scan, attest,
  and publish an immutable ECR image. It is mechanically rejected if it
  contains a CloudFormation or ECS service-mutation command.
- Narrowed the source GitHub OIDC policy to the two ECR-only statements and
  updated the target profile/readiness manifest to distinguish GitHub image
  publication from the governed manual service-stack change-set procedure.
  The source change does not alter the live AWS role; that IAM update remains
  an explicitly reviewed AWS operation.
- Updated the deployment plan, runtime plan, and learning handbook with the
  rationale and next sequencing: publish the image first, then create, review,
  and explicitly approve the CloudFormation change set against its immutable
  digest.
- Verification passed: workflow static check, infrastructure static-policy
  check, readiness planning check (intentionally blocked with seven evidence
  gaps), and whitespace validation. No AWS resource or identity changed.

### 2026-09-22 - ADR disposition

ADR needed: no

Reason: This is a least-privilege enforcement refinement of the existing
target delivery decision in ADR 0029. It does not select a new provider,
runtime boundary, or persistence model; it constrains the automation authority
that publishes the already selected image.

## Sub-Agent Activity

- None recorded yet.

## Commits



- Commit: `11283f6`
  Time UTC: 2026-09-21T22:37:23Z
  Message: feat(observability): govern capability telemetry profiles
  Summary: Implemented provider-neutral observability-profile consumption for server and worker paths, profile-safe telemetry projection, sink-failure isolation, smoke proof, and the target observability readiness roadmap.
  ADR impact: No ADR: this activates existing provider-neutral platform guidance; target provider and infrastructure choices remain deferred.


- Commit: `3182c74`
  Time UTC: 2026-09-21T23:48:49Z
  Message: feat(observability): prepare CloudWatch metric delivery
  Summary: Added a target-only CloudWatch OpenTelemetry metrics adapter, target composition, prepared ECS collector/IAM/SSM IaC, local and template validation, and durable plan/handbook/readiness evidence; AWS remains unchanged.
  ADR impact: ADR 0029 records the task-local collector boundary and ECS task-role limitation.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/04.deploy/adrs/0029-use-task-local-otel-collector-for-cloudwatch-metrics.md
Reason: The target now selects a durable provider-specific capability-metrics delivery boundary. The ADR preserves the distinction between local adapter selection and the still-unapproved AWS collector, IAM, task-definition, dashboard, and alarm implementation.

## Session Metrics

Raised at UTC: 2026-09-19T00:27:23Z
Latest commit at UTC: 2026-09-21T23:48:49Z
Latest commit SHA: 3182c74
Chat duration: 256886s (02:23:21:26)
Estimated chat tokens: 24422853 estimated from chat transcript bytes (97691410 bytes; source: codex path: /home/owner/.codex/sessions/2026/08/31/rollout-2026-08-31T01-09-34-01a05526-6410-73f3-a691-39a27d433af7.jsonl)
Estimated chat cost: unavailable; no pricing profile selected
Estimated chat cost basis: unavailable; set CHAT_COST_PROFILE or CHAT_COST_PRICING_FILE

## Notes

- The provider-neutral server and worker slice was followed by a local AWS
  metrics-adapter and target-policy selection slice. No AWS resources, IAM
  permissions, task definitions, collector, dashboards, alarms, or deployment
  configuration changed. The selected target delivery remains not deployed.

## RAG Knowledge Disposition

Status: covered
Reason: The provider-neutral observability-profile implementation activates existing platform runtime guidance: platform owns safe telemetry mechanisms, app routes/jobs use runtime seams, and provider translation remains in a later adapter.
Evidence:
- docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md
- docs/03.product/rules/platform/layers/platform.yml
- .agentic/03.product/plans/implementation/platform-runtime-implementation.md
Corpus gaps:
- None.
