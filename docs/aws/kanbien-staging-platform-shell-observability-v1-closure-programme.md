<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-observability-v1-closure
version: 8
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- sre
- security
- architecture
kind: change-plan
purpose: Close the bounded Kanbien staging platform-shell observability-v1 implementation and proof gaps without treating temporary synthetic evidence as a customer SLO.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Kanbien Staging Platform Shell: Observability v1 Closure Programme

## Mission and boundary

This programme turns the deployed platform-smoke telemetry path into a
bounded, evidence-backed observability-v1 reference target. It closes the
implementation and rehearsal gaps for one staging HTTP capability; it does
not declare a customer-facing product SLO, a production multi-region service,
or a completed reusable platform scheduler.

The target is account `337159794548`, region `eu-west-1`, environment
`kanbien/staging`, service `kanbien-staging-platform-shell`, and hostname
`staging.platform.kanbien.com`. The baseline at programme start is ECS task
definition revision `2`, desired/running count `1`, foundation stack
`UPDATE_COMPLETE`, and five `OK` infrastructure alarms. The public legacy
brochure, `service-platform`, DNS, shared ALB default routing, stored secret
values, and non-staging targets are explicitly out of scope.

## Definition of complete

Observability-v1 is complete only when the readiness record has safe evidence
for all of the following:

1. A reviewed capability profile governs logs, metric labels, traces, and NFR
   measurements for the smoke capability.
2. The application emits the reviewed outcome counter and duration histogram;
   the task-local collector exports them to CloudWatch; a signed PromQL query
   returns both series.
3. An independent, least-privilege coverage verifier detects the absence of an
   expected metric after a controlled synthetic request and reports
   `insufficient-confidence`, never a healthy SLO result.
4. The coverage concern reaches the existing operator alert destination and
   normal metric delivery is proven after rollback.
5. The staging target has redacted evidence for protected success, valid
   wrong-scope denial, shared rate limiting, WAF/host routing, log delivery,
   alarm receipt, and task-definition rollback.
6. Availability, p95, and p99 queries are executable from their declared
   target-profile policy and return an explicit confidence state. The first
   28-day window remains an evidence clock, not a shortcut claim.
7. Runbooks, dashboard definitions, retention requirements, ownership, and
   cost-budget follow-up are recorded with their proof status.

## Operating invariants

- The generic platform server, worker, contracts, and observability package
  remain provider-neutral. AWS-specific query, IAM, collector, and alerting
  behaviour belongs only in the target and deployment layer.
- Logs, metrics, and traces remain distinct from durable audit and security
  records. No source in this programme turns an operational signal into an
  audit store.
- Coverage queries use only the approved low-cardinality capability facts.
  They never add a tenant, principal, request ID, trace ID, raw path, IP,
  email, token, body, prompt, transcript, or object identifier.
- The synthetic request is technical boundary evidence. It is not represented
  as customer traffic or as proof that a customer SLO has been met.
- Every AWS mutation is preceded by a read-only preflight, reviewed exact
  source, named rollback, and post-change inspection. A successful command
  alone never closes a readiness item.
- Any unplanned permission broadening, sensitive output, unexpected cost,
  service-health regression, or target drift stops the programme.

## Work packages

### A. Source and policy closure

Create a target-owned metric-coverage command and static policy check. The
command reads the target profile, verifies the selected AWS account, signs a
native CloudWatch PromQL request, and emits only a safe coverage verdict. Its
only permitted verdicts are `observed`, `missing`, `query-failed`, and
`notification-failed`. Every non-observed result maps to
`insufficient-confidence`.

Add a separate main-only GitHub OIDC role, workflow, policy source, and trust
source for the coverage checker. It has only `cloudwatch:GetMetricData`,
`cloudwatch:ListMetrics`, and `sns:Publish` for the exact existing alarm topic.
It cannot read Cognito secrets, call arbitrary routes, publish an image, or
deploy CloudFormation/ECS resources. Its nominal four-hour schedule occurs
after the existing synthetic schedule, with a bounded query window that covers
the expected request and delivery grace period.

Add an SLO evaluation mode to the same command. It derives its PromQL from the
target profile's fixed availability, p95, and p99 definitions, returning only
safe aggregate values and `healthy`, `breached`, or
`insufficient-confidence` states. It does not write results back into metrics
or manufacture observations.

CloudWatch documents a maximum seven-day request range. However, the selected
staging OTLP series returned a safe `400` response for `increase()` lookbacks
above one day during a read-only live query on 2026-09-22; one-day current and
historical evaluations succeeded. Until AWS changes that observed behaviour,
the target calculates its 28-day objectives from 28 adjacent one-day
counter-increase windows. Histograms are merged as cumulative buckets across
the same 28 windows before p95/p99 calculation; averaging daily percentiles
would be mathematically wrong.

### B. Static and local verification

Run the coverage command's offline validation and smoke test, the coverage
policy check, the existing controlled-smoke/synthetic/infrastructure gates,
CloudFormation rendering and validation, adapter checks, and diff/metadata
checks. The policy checker must reject a changed schedule, role, account,
region, topic, action set, metric name, label set, timeout, or workflow step.

Record source decisions in the target profile, readiness manifest, deployment
plan, platform implementation plan, handbook, and session log. The source
state remains `implemented-pending-live-proof` until AWS inspection and the
rehearsals below succeed.

### C. Coverage activation and normal-path proof

After source is merged to `main`, inspect the existing service, task revision,
SNS topic, and metric labels again. Create only the reviewed coverage IAM role
and its inline policy. Read both back and compare them with repository source.
Dispatch the existing protected synthetic, wait for the declared arrival grace,
then dispatch the coverage workflow. Expect `observed`; retain only the run
identifiers, safe verdict, status, and duration. Record the first
clock-triggered coverage result separately when it arrives.

### D. Exporter-loss and rollback rehearsal

Capture baseline revision and service health. Keep the application's fixed
`127.0.0.1:4318` exporter endpoint unchanged: it is an enforced egress-safety
boundary, so changing it to an alternative port is a configuration failure, not
an exporter-loss test. Register one disposable task-definition revision whose
collector, and only its non-secret receiver configuration, listens on closed
port `4319`; retain its health check, processors, AWS exporter, image, task
role, and every other setting. No application image, stored secret value, DNS,
WAF, rate-limit, or authorization setting may change. Update only the staging
platform-shell service and wait for a healthy steady state.

Run the controlled protected smoke. It must still return `200`. After that
request, wait the full declared 1,200-second coverage lookback—not merely the
five-minute arrival grace—before running the independent verifier. The wait
must exclude all earlier healthy observations from the query window. The
verifier must then report `missing`, mark the affected SLO result
`insufficient-confidence`, and notify the existing alert destination. Restore
the exact captured task definition and wait for steady state. A fresh
cumulative counter needs one fixed recovery smoke to establish its exported
baseline and a second fixed recovery smoke at least 75 seconds later to
advance it; only then can PromQL `increase()` prove an `observed` verdict.
Any health or smoke failure triggers immediate baseline restoration.

The 2026-09-22 rehearsal completed the collector-receiver fault, isolated
`missing`/`insufficient-confidence` verdict, and restored `observed` coverage.
It also established that a fresh cumulative counter needs a baseline request and
a later advancing request before `increase()` can prove recovery. Main-only
workflow run `35764615475` subsequently proved the governed two-point synthetic
implementation: it made the fixed pair 75 seconds apart and the read-only
coverage verdict after its five-minute arrival grace was `observed`. This is
manual-dispatch implementation evidence only: the first clock-trigger proof
remains outstanding. The operator has confirmed receipt of the existing fixed
alert; the source record deliberately retains no email content, email address,
subscription identifier, or link.

### E. Remaining bounded readiness proof

Create one separately scoped valid Cognito machine client with no
`platform-smoke.smoke:read` permission and prove `403` using only a safe HTTP
status result. Retain the existing correctly-scoped `200` proof separately.

The existing staging adapter binds the JWT `client_id` claim to exactly one
machine client. Therefore a second client cannot be used for this proof until
the target is deliberately configured to accept its exact identifier: otherwise
the correct result is `401` at authentication, not `403` at authorization.
The correction is a finite client-ID allowlist, not a wildcard. The generic JWT
verifier supports an exact `oneOf` claim requirement; the Cognito adapter keeps
the primary client required and accepts optional additional IDs only from a
validated target environment list. The list rejects empty values, duplicates,
and repetition of the primary client.

Before the live proof, deploy the reviewed immutable image and target
configuration containing exactly the primary client ID and the separately
created negative-test client ID. Create a dedicated Cognito resource-server
scope for that negative client which is intentionally absent from the
platform permission mapping. It must not receive the smoke-read scope, user
authentication flows, a wildcard scope, or a role in the running task. Keep
its secret outside source control and use it only in a bounded local
status-only command. If provisioning, deployment, or cleanup cannot preserve
these constraints, stop rather than falling back to the primary client or an
invalid token.

Run no more than the target's declared rate-limit window plus one sequential
request, stopping at the first `429`. Inspect the host rule and WAF association
read-only and make a bounded public host check. Confirm one redacted structured
log event, explicitly marked alert receipt without an email body, and the
rollback evidence from work package D.

### F. SLO operation and evidence clock

Provision the reviewed PromQL dashboard and capability alarms only after their
queries have been locally and live validated against the selected metric model.
Link their runbooks and the target policy. Start the 28-day evidence clock;
the target remains `insufficient-confidence` until it has at least 100 eligible
observations in that actual rolling window. A dashboard or healthy-looking
single query never replaces this condition.

Activate the existing `service=platform-shell` cost-allocation tag in Billing,
allow data to appear, configure the existing $25 monthly target budget and
forecast thresholds, and prove the alert path without committing billing data.

## Evidence and closure record

Each work package records only: source commit, reviewed resource name or ARN,
safe workflow/run/change-set identifiers, UTC timestamps, status/verdict,
bounded duration/count, task revision, alarm state, rollback state, and a
human alert-receipt confirmation where required. It records no secrets,
headers, tokens, messages, email bodies, customer data, raw log bodies, raw
PromQL responses, or provider error payloads.

The readiness manifest remains blocked until each named proof has evidence.
Claims such as "deployed", "query-proven", and "operator receipt proven" are
kept separate so later reviewers can see exactly what was established.

## Deferred after v1

The following are deliberately not closure conditions for this smoke target:

- a reusable platform scheduler contract and target adapter;
- a deployed queue/worker service and its live telemetry proof;
- a selected trace exporter, sampling policy, trace retention, and trace-store
  access model;
- multi-tenant product analytics or tenant-specific metric dimensions;
- SIEM/security-event integration; and
- multi-region or high-scale telemetry topology.

## References

- [Exporter-loss rehearsal plan](kanbien-staging-platform-shell-exporter-loss-rehearsal-plan.md)
- [Initial deployment plan](kanbien-staging-platform-shell-initial-deployment-plan.md)
- [Staging target profile](../../infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml)
- [Staging readiness manifest](../../infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml)
- [Task-local collector decision](../04.deploy/adrs/0029-use-task-local-otel-collector-for-cloudwatch-metrics.md)
- [AWS PromQL query permissions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-PromQL.html)
- [AWS PromQL alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-PromQL-Alarms.html)
