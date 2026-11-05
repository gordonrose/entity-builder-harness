<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.plan.telemetry-implementation-follow-on
version: 1
status: draft
created_on: "2026-10-29"
updated_on: "2026-11-05"
layer: 03.product
domain: observability
disciplines: [architecture, security, sre]
kind: implementation-plan
purpose: Preserve deferred telemetry implementation and assurance review beyond the diagnostics project.
portability: {class: source-only, targets: []}
used_by:
- id: product.readme
  path: .agentic/03.product/README.md
- id: shared.plan.governed-diagnostic-coverage
  path: .agentic/shared/plans/implementation/governed-diagnostic-coverage.md
-->
# Deferred telemetry implementation and assurance

## Status and boundary

Deferred until the diagnostics project is finished and the user selects a
bounded follow-on slice. Recording this plan authorizes no runtime changes,
new metrics, package builds, cloud access, deployment or notification tests.
The current work remains governed by the
[diagnostic coverage plan](../../../shared/plans/implementation/governed-diagnostic-coverage.md).

Metrics already exist. The walkthrough exposed implementation questions and
assurance gaps as well as missing diagnostics; it did not demonstrate that the
whole telemetry stack is broken. The observations below are from source review
on 2026-10-29, not a fresh live deployment test. Design limits are not defects
unless they conflict with an approved requirement. Historical qualification
receipts remain historical evidence, not proof of the current source or stage.

Changing delivery, validation, cancellation, buffering, metric coverage or alarm
policy belongs here. Safely explaining what the existing path actually observed
belongs in the diagnostic project. If a diagnostic slice cannot safely proceed
without a behavior change, surface that prerequisite for explicit approval;
neither silently defer required safety nor expand the slice without agreement.

## Ownership and resumption

Core owns provider-neutral contracts. Platform owns reusable recording and
readiness behavior. Adapters own SDK integration and provider evidence. Product
and target owners choose adopted signals and policies. Deployment configuration,
package qualification and live assurance remain governed by `04.deploy` and
applicable AWS workflows. Harness rules govern proof, not runtime vocabulary.

At resumption, recheck each observation against current source, identify the
approved requirement, decide whether a change is needed, and inventory affected
consumers. Record exact focused tests and selector-selected broader checks
before implementation. Complete consumer changes and focused proof before
expensive checks; freeze their inputs. Separate local, package and explicitly
authorized live evidence. Do not use this backlog to add a parallel framework.

## Deferred workstreams

### Required DIAG-013 input to the logging/telemetry maturity review

[DIAG-013](../../../shared/plans/implementation/diagnostics-backlog.md#diag-013--expose-diagnostic-reporting-outcomes-without-changing-workload-results)
remains open and implementation-deferred. Resumption of this plan must decide
receiving responsibilities, optional versus required reporting, observable
handoff/rejection/unavailability and asynchronous completion, and independent
failure visibility through real callers before choosing an implementation.
Preserve workload results, disabled/omitted reporters, privacy, no replay and
no recursive reporting through a failed sink. A local handoff or completed
logger call is not evidence of collector/backend receipt. Current production
qualification must state its actual remote evidence and any gap; it must not
mark this requirement complete or start the logging redesign incidentally.

### 1. Synchronous and asynchronous recording contract

- **Observed:** `packages/core/src/monitoring/metrics.ts` permits `record` to
  return `void` or `Promise<void>`. `platform/observability/src/metrics.ts` uses
  synchronous try/catch and does not observe a returned promise. The current
  CloudWatch adapter records synchronously; no current live async failure was
  demonstrated.
- **Decision/work:** decide supported async behavior and best-effort isolation;
  reconcile the Core contract, helper and implementations without letting a
  rejected telemetry promise change business outcomes or become unhandled.
  This decision may be a prerequisite for accurate local-recording diagnostics.
- **Proof:** synchronous success/throw, async resolve/reject, disabled provider
  and callers that do not await recording. Establish actual guarantees rather
  than treating a normal return as backend delivery.

### 2. Validation, label privacy and measurement timestamps

- **Observed:** the helper validates parts of a point but does not use Core's
  `metricPoint` constructor. The CloudWatch adapter independently checks its
  catalogue, kind, unit, value and label names. Current label syntax/blocklists
  are not a general secret detector. Adapter instrument calls pass value and
  attributes, not the point's `recordedAt` timestamp.
- **Owners:** `packages/core/src/monitoring/{metrics,validation}.ts`,
  `platform/observability/src/{metrics,normalization}.ts`, and
  `platform/adapters/aws/observability/cloudwatch/src/{index,configuration}.ts`.
- **Decision/work:** agree validation ownership, permitted label-value sources,
  supported untyped inputs and timestamp meaning. Do not silently tighten
  accepted inputs or claim a leak from a policy question alone.
- **Proof:** constructor/helper/adapter acceptance parity, hostile untyped
  inputs and canaries, approved label cardinality/privacy rules, controlled
  clocks and actual SDK timestamp behavior. Include accepted alternatives.

### 3. Aggregation, overflow, durability and flush guarantees

- **Observed:** the inspected local OpenTelemetry metrics SDK version 2.11.0
  groups excess attribute combinations under `otel.metric.overflow`; this is
  not necessarily rejected data, though the original grouping is lost. The
  examined path aggregates in memory. Its periodic reader handles some export
  errors/timeouts internally, so a fulfilled flush is not delivery proof.
- **Owners:** the CloudWatch adapter, its pinned package dependencies and
  runtime tests; shared contracts only where an approved guarantee requires it.
- **Decision/work:** decide whether existing best-effort retention, cardinality
  and shutdown guarantees meet requirements. Any queue, retry, cap or lifecycle
  policy change needs its own compatibility decision. Exposing safe evidence
  of existing export/flush behavior remains diagnostic work.
- **Proof:** actual pinned SDK behavior for overflow counts and dimensions,
  empty collection, failed/timed-out export, partial collection, force-flush,
  shutdown and process termination. Do not substitute a fake throwing SDK for
  proof of errors the real SDK absorbs.

### 4. Readiness deadlines, cancellation and staleness

- **Observed:** `platform/observability/src/readiness-observation.ts` bounds the
  wait for a probe but that race does not itself cancel the probe. Other
  database deadlines need review before declaring a query unbounded.
  `staleAfterMs` is read/validated in `configuration.ts`, but no runtime consumer
  beyond configuration was found. The target's missing-data alarm is a separate
  policy, not proof that this setting expires an observation.
- **Owners:** those Platform files, the PostgreSQL probe/adapter, target
  entrypoints and `core-server-persistence.yml` under the target's AWS
  CloudFormation directory.
- **Decision/work:** choose cancellation/overlap guarantees and the source of
  truth for staleness. Reconcile configuration and alarm policy deliberately;
  do not change health responses, cadence or recovery behavior for diagnostics.
- **Proof:** fake-clock and never-settling/late probe tests, actual database
  deadline behavior, configuration-to-target parity and separately approved
  live alarm timing. Do not promise an exact three-minute alarm transition.

### 5. Collector declaration and package qualification alignment

- **Observed static differences:** the current target uses a dedicated private
  collector with inline `AOT_CONFIG_CONTENT`; the foundation observability
  declaration still describes `task-local-sidecar` and parameter delivery.
  The qualification fixture includes a `readiness` dimension absent from the
  target's EMF dimension set. The package behavior test reads an
  `ObservabilityCollectorConfiguration` resource not found in the current
  template. That test was not executed in this review.
- **Owners:** `infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/observability.yml`,
  the same target's `30-provider-realization/aws/cloudformation/core-server-persistence.yml`,
  `infra/04.deploy/03.product/image/core-server-persistence-observability-collector/`
  and `scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/behavior-test.py`.
- **Decision/work:** reconcile intended topology, canonical configuration
  extraction and dimension parity. Assess this compatibility gap before any
  slice relying on that package test. Do not relabel old receipts or reconfigure
  deployed IAM/network resources merely to make fixtures pass.
- **Proof:** source/fixture parity and an intentional mismatch counterexample,
  then real image qualification. Local stdout EMF proof is not CloudWatch
  extraction proof; cloud verification needs separate stage authority.

### 6. Target metric coverage

- **Observed:** the persistence target approves only
  `platform.dependency.readiness` mapped to
  `kanbien.core_server.postgresql_readiness`. Generic HTTP/job helpers elsewhere
  do not establish exported coverage on this target. Readiness-only may be the
  intended approved scope, not a missing implementation.
- **Owners:** target `PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON` configuration,
  `platform/observability/src/metric-series-configuration.ts`, capability callers
  and the adapter catalogue binding.
- **Decision/work:** compare adopted signals with approved workload needs and
  decide any additional metric separately. Do not widen selectors or implement
  the illustrative HTTP timer from the walkthrough without approval.
- **Proof:** approved/undeclared series selection, caller-to-export mapping,
  dimension/cardinality budgets and stage-specific extraction. A diagnostic
  for an undeclared name cannot infer that the caller made a typo.

### 7. Alarm and notification assurance

- **Observed:** the current alarm can represent not-ready data or missing data;
  it does not establish root cause. The readiness rehearsal accepts a confirmed
  email subscription and operator-supplied delivery time. Its delivery evidence
  is human attestation, not independent inbox/message observation. Subscription
  confirmation alone is not message delivery proof.
- **Owners:** target alarm/SNS resources,
  `scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.py`
  and adjacent `observability-receipts.py` and their tests.
- **Decision/work:** decide whether that assurance level meets requirements or
  needs privacy-preserving recipient/message correlation. Review intended
  subscription matching; retain the distinction between provider evidence and
  operator claims. No recipient, token, message body or credential in records.
- **Proof:** missing/unconfirmed/wrong subscription cases, invalid or unrelated
  delivery attestation, ALARM/OK behavior and an explicitly authorized fresh
  delivery-chain rehearsal. Receipt hashes protect recorded content, not the
  independent truth of an attestation. Never rewrite historical receipts.

## Completion criteria

This is an unimplemented follow-on backlog, not a claim that these changes are
all necessary. Close each workstream with an approved decision, evidence for
its promised guarantees, explicit remaining limitations and unchanged behavior
outside that decision. Keep diagnostics completeness separate from telemetry
feature completeness and from live delivery assurance.
