<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-exporter-loss-rehearsal
version: 1
status: draft
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

This is a **plan only**. It authorises no AWS, GitHub, ECS, IAM, SNS, or
CloudWatch mutation. A later execution turn must name the exact reviewed
source, AWS resources, reversible task revision, stop conditions, and rollback
command under `.agentic/aws/workflows/execute-approved-aws-change.md`.

The rehearsal applies only to the `kanbien/staging` platform-shell target in
account `337159794548`, region `eu-west-1`. It must not alter the legacy
brochure site, `service-platform`, DNS, ALB listeners, WAF rules, Cognito
clients, or stored secret values.

## Objective

Prove all six statements together:

1. A protected smoke request still returns the approved `200` while application
   metric export is unavailable.
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
| Arrival grace period | 5 minutes | Allows the 60-second exporter interval and normal ingestion delay without masking a sustained loss. This is a proposed policy value, not yet deployed. |
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
2. Create one disposable task-definition revision. Change only the
   application-side metrics exporter receiver to an intentionally closed
   loopback endpoint in the task network namespace. Do not change the
   collector, application image, secrets, DNS, ALB, WAF, rate limit, or
   authorization configuration.
3. Update only the staging platform-shell service to that revision and wait
   for the service to become steady. If it cannot become steady, stop and
   restore the recorded baseline before making a request.
4. Dispatch one controlled protected smoke request. Expect a redacted `200`.
   A request failure is not exporter-loss evidence; it is a separate service
   failure and triggers immediate rollback.
5. After the declared five-minute grace period, run the independent coverage
   verifier. Expect no increase for the approved outcome series, a `missing`
   coverage verdict, and `insufficient-confidence` for the affected SLO
   window.
6. Verify delivery of the explicitly marked coverage notification without
   storing the email body or any secret. A workflow success alone is not alert
   receipt proof.
7. Restore the exact baseline task definition through the governed rollback
   path. Wait until the service is steady, issue one more controlled smoke
   request, and verify metric arrival and an `observed` coverage verdict.
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
- the disposable exporter-loss revision and the one changed non-secret
  exporter receiver setting;
- a protected request `200` during the rehearsal;
- the redacted `missing` coverage verdict after grace;
- the operator's alert-receipt confirmation, without message content;
- restoration to the normal revision;
- a post-recovery protected `200` and `observed` coverage verdict; and
- the source commit, workflow/run identifiers, timestamps, and relevant
  CloudFormation or ECS revision identifiers.

This closes neither the 28-day SLO population requirement nor the remaining
wrong-scope `403`, rate-limit `429`, WAF/routing, rollback, dashboard/runbook,
and budget proof gaps.

## Sources

- [Initial deployment plan](kanbien-staging-platform-shell-initial-deployment-plan.md)
- [Target profile](../../infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml)
- [Metric-delivery ADR](../04.deploy/adrs/0029-use-task-local-otel-collector-for-cloudwatch-metrics.md)
- [AWS CloudWatch PromQL permissions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-PromQL.html)
- [AWS OpenTelemetry metric delivery guidance](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-otel-send.html)
