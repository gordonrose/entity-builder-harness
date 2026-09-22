<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-exporter-loss-rehearsal
version: 5
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- sre
- security
- architecture
kind: change-plan
purpose: Define the separately approved, bounded staging rehearsal that proves loss of application metric export becomes incomplete SLO confidence and an operator signal.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
- id: aws.plan.kanbien-staging-platform-shell-initial-deployment
  path: docs/aws/kanbien-staging-platform-shell-initial-deployment-plan.md
-->
# Kanbien Staging Platform Shell: Exporter-Loss Rehearsal Plan

## Status and boundary

This plan is active only for the separately authorised, bounded
`kanbien/staging` rehearsal. Every AWS action must still name the exact
reviewed source, AWS resources, reversible task revision, stop conditions, and
rollback command under `.agentic/aws/workflows/execute-approved-aws-change.md`.

The rehearsal applies only to the `kanbien/staging` platform-shell target in
account `337159794548`, region `eu-west-1`. It must not alter the legacy
brochure site, `service-platform`, DNS, ALB listeners, WAF rules, Cognito
clients, or stored secret values.

## Objective

Prove all six statements together:

1. A protected smoke request still returns the approved `200` while its
   application metric export cannot reach the task-local collector.
2. A monitor outside that exporter path detects that the expected reviewed
   metric has not arrived after its grace period.
3. The affected SLO state is reported as `insufficient-confidence`, never as
   healthy or as a zero-error interval.
4. The coverage concern reaches the existing operator alert destination.
5. Restoring the normal task revision restores metric delivery.
6. The rehearsal leaves only redacted operational evidence: identifiers,
   timestamps, safe HTTP status, safe duration, coverage verdict, and recovery
   state. It never retains a secret, access token, authorization header,
   request/response body, customer data, or raw provider error payload.

## Why a separate coverage monitor is required

The application path is deliberately best effort:

```text
protected request → application metrics adapter → task-local collector → CloudWatch OTLP metrics
```

That path cannot reliably declare its own failure. If the application exporter
cannot reach its loopback receiver, it may be unable to send a warning by the
same route. A coverage monitor instead uses an independent CloudWatch query
path to ask whether the approved outcome counter advanced after a known
synthetic request.

```text
scheduled synthetic request ───────────────┐
                                           │ expected observation window
                                           ▼
coverage verifier → signed CloudWatch PromQL query → coverage verdict → operator alert
```

The verifier checks low-cardinality, already-approved capability labels. It
must not add a per-run identifier, trace ID, tenant, principal, raw path, or
synthetic token to a metric label just to correlate one request. This is a
freshness/coverage check, not per-request tracing.

## Correction from the first bounded attempt

The first disposable revision changed the application endpoint from the
reviewed `http://127.0.0.1:4318/v1/metrics` to port `4319`. ECS correctly
rolled it back before a smoke request: the CloudWatch adapter intentionally
rejects any endpoint other than the fixed task-local collector address during
startup. That was a configuration-boundary proof, not an exporter-loss proof.

Do **not** loosen that adapter rule or treat an arbitrary endpoint as a test
hook. The corrected rehearsal keeps the application endpoint at `4318` and
instead makes the disposable collector listen at `4319`. The application then
uses its normal reviewed address, but no process is listening there. This
induces a real local delivery failure without creating an arbitrary outbound
telemetry destination or changing the application image, authorization, or
request path.

## Proposed ownership and least-privilege boundary

| Concern | Proposed owner | Boundary |
| --- | --- | --- |
| Fixed protected request and token acquisition | Existing `github-platform-shell-staging-synthetic` role and job | Unchanged: one secret read, in-memory token, fixed HTTPS `GET`, safe status/latency output. |
| Metric-arrival verdict | New, separate `github-platform-shell-staging-metric-coverage` role and coverage job | It cannot read Cognito secrets or invoke arbitrary application routes. |
| Native OpenTelemetry query | CloudWatch PromQL HTTP endpoint, signed as service `monitoring` | Query only the approved outcome series and reviewed static labels. CloudWatch documents `cloudwatch:GetMetricData` and `cloudwatch:ListMetrics` for this API. |
| Operator signal | Existing target-owned alert destination | The coverage job may publish only a small allowlisted coverage result to the exact reviewed SNS topic; it must not publish user or request data. |
| SLO interpretation | Target coverage policy and verifier result | `missing`, query failure, or notification failure means `insufficient-confidence`; none can become a healthy SLO result. |

The proposed coverage role has a separate main-branch GitHub OIDC trust policy.
Its exact IAM source must be reviewed before creation. It must contain only the
two documented CloudWatch PromQL read actions and, if direct alert proof is
selected, `sns:Publish` to the one declared alert-topic ARN. It must not be
merged with the secret-reading synthetic role or the deployment role.

## Proposed coverage contract

The target profile remains the policy authority. Before source is implemented,
add one explicit coverage contract with these initial values and no defaults:

| Field | Proposed initial value | Reason |
| --- | --- | --- |
| Expected event | Successful `platform-smoke-protected-read` request | It is fixed, authorised, low-cost, and already uses the approved machine client. |
| Observed series | `kanbien.platform.server.request.outcome` | A counter can prove that an eligible completed request was exported. |
| Required static labels | `capability=platform-smoke.smoke.read`, `action=read`, `execution_context=server`, `http_method=GET`, `outcome=succeeded` | They are already in the reviewed label allowlist and avoid sensitive or unbounded fields. |
| Export interval | 60 seconds | Current target setting. |
| Recovery counter sequence | Two fixed protected requests, 75 seconds apart | After a fresh task starts, the first cumulative counter observation establishes a baseline; a later observation must advance it before `increase()` can demonstrate freshness. |
| Arrival grace period | 5 minutes | Allows the 60-second exporter interval and normal ingestion delay before ordinary coverage evaluation. It is not a rehearsal-isolation delay. |
| Coverage query window and rehearsal isolation wait | 20 minutes | The verifier examines the preceding 1,200 seconds. During exporter-loss rehearsal, wait the whole window after the broken-export smoke so an earlier healthy observation cannot satisfy the query. |
| Coverage verdicts | `observed`, `missing`, `query-failed`, `notification-failed` | Each non-observed verdict yields `insufficient-confidence`; only `observed` confirms this coverage check. |
| Persistent alerting | Existing operator alert destination | The rehearsal must prove an operator-facing signal without adding a new recipient or storing email content. |

The PromQL expression must calculate a counter increase over the defined
observation window. Its exact syntax, endpoint signing, response parsing, and
zero-result semantics must be locally tested with a read-only query before any
IAM or task-definition mutation is proposed. The verifier may emit only an
allowlisted verdict and timing fields; raw query responses remain ephemeral.

## Rehearsal sequence after separate approval

1. Capture the current healthy task-definition ARN and service desired/running
   counts as the rollback baseline. Confirm the current controlled smoke and
   metric-arrival query pass before changing anything.
2. Create one disposable task-definition revision. Leave the application
   container, including its fixed `4318` metrics endpoint, unchanged. Replace
   only the collector's non-secret `AOT_CONFIG_CONTENT` injection with an
   inline equivalent of the reviewed collector configuration whose OTLP HTTP
   receiver listens on `127.0.0.1:4319` instead of `4318`. Its health check,
   AWS exporter, processors, image, task role, and all other collector settings
   must remain identical. Do not change application image, stored secret
   values, DNS, ALB, WAF, rate limit, or authorization configuration.
3. Update only the staging platform-shell service to that revision and wait
   for the service to become steady. If it cannot become steady, stop and
   restore the recorded baseline before making a request.
4. Dispatch one controlled protected smoke request. Expect a redacted `200`.
   A request failure is not exporter-loss evidence; it is a separate service
   failure and triggers immediate rollback.
5. After the broken-export smoke, wait the full declared 1,200-second coverage
   query window—not only the five-minute arrival grace—then run the independent
   coverage verifier. Expect no increase for the approved outcome series, a
   `missing` coverage verdict, and `insufficient-confidence` for the affected
   SLO window. This full-window wait excludes an earlier healthy metric that
   would otherwise make the rehearsal falsely look `observed`.
6. Verify delivery of the explicitly marked coverage notification without
   storing the email body or any secret. A workflow success alone is not alert
   receipt proof.
7. Restore the exact baseline task definition through the governed rollback
   path. Wait until the service is steady. Issue one fixed controlled smoke to
   establish the fresh cumulative-counter baseline, wait at least the declared
   60-second export interval plus the reviewed 15-second margin, then issue a
   second fixed controlled smoke. Verify metric arrival and an `observed`
   coverage verdict. One post-restart request alone is not sufficient evidence
   for a PromQL `increase()` query.
8. Record only the evidence listed below. Remove no history, IAM identity,
   secret, alarm topic, or task-definition revision during the rehearsal.

## Stop conditions and recovery

Immediately restore the baseline task revision and stop the rehearsal if any
of these occurs:

- the service does not reach its recorded healthy count;
- `/livez`, `/readyz`, or the protected smoke request does not meet its
  approved expected result;
- the coverage query identity is in the wrong account or has broader
  permissions than the reviewed source;
- a command could expose a secret, token, authorization header, raw body, or
  provider error payload;
- the alert destination is not the declared target destination; or
- the recovery request does not restore a metric-arrival verdict.

Rollback is strictly the recorded normal task-definition ARN applied back to
the same service, followed by service-stability and recovered-metric checks.
Deleting the temporary task definition, IAM role, inline policy, or alert
resources is out of scope and needs a separate destructive-action approval.

## Evidence required for closure

The readiness record may move this gap only after it has safe evidence of:

- the normal baseline task revision and steady service state;
- the failed first revision `3` configuration-boundary result and automatic
  restoration to revision `2`, explicitly marked as non-evidence for exporter
  loss;
- the disposable collector-receiver-mismatch revision and the one changed
  non-secret receiver setting;
- a protected request `200` during the rehearsal;
- the redacted `missing` coverage verdict after the full coverage-window
  isolation wait;
- the operator's alert-receipt confirmation, without message content;
- restoration to the normal revision;
- a post-recovery protected `200` and `observed` coverage verdict; and
- the source commit, workflow/run identifiers, timestamps, and relevant
  CloudFormation or ECS revision identifiers.

This closes neither the 28-day SLO population requirement nor the remaining
wrong-scope `403`, rate-limit `429`, WAF/routing, rollback, dashboard/runbook,
and budget proof gaps.

## Live rehearsal outcome — 2026-09-22

The corrected bounded rehearsal completed against `kanbien/staging` in account
`337159794548`, region `eu-west-1`:

- Baseline revision `2` was captured; disposable revision `4` changed only the
  collector receiver from `4318` to `4319`, while the application retained its
  fixed `4318` endpoint.
- Controlled run `35745689762` returned `200` in 555 ms during the fault.
- After the 1,200-second isolation window, coverage run `35748133992` returned
  `missing` and `insufficient-confidence`. Its fixed SNS publish path completed,
  but operator receipt has not been claimed.
- Revision `2` was restored. Recovery runs `35748560439` (`200`, 512 ms) and
  `35761099278` (`200`, 445 ms) established then advanced the fresh cumulative
  counter. The subsequent governed read-only coverage query returned `observed`.

The initial recovery request alone returned `missing`, not because delivery was
broken, but because a fresh cumulative counter needs a baseline and a later
increment for PromQL `increase()` to show movement. The target now codifies the
two-point, 75-second sequence. The remaining closure item for this rehearsal is
operator confirmation that the existing alert destination received the concern;
email content must not be stored in this repository.

## Sources

- [Initial deployment plan](kanbien-staging-platform-shell-initial-deployment-plan.md)
- [Target profile](../../infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml)
- [Metric-delivery ADR](../04.deploy/adrs/0029-use-task-local-otel-collector-for-cloudwatch-metrics.md)
- [AWS CloudWatch PromQL permissions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-PromQL.html)
- [AWS OpenTelemetry metric delivery guidance](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-otel-send.html)
