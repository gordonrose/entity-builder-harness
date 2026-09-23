<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-worker-and-operations-closure
version: 7
status: draft
layer: 04.deploy
domain: runtime.operations
disciplines:
- architecture
- security
- sre
kind: change-plan
purpose: Define the bounded staging deployment and live-proof sequence for the dormant platform-shell worker, public-boundary proofs, and cost controls.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Kanbien Staging Platform Shell: Worker and Operations Closure Plan

## Status and purpose

This is a **source and execution plan**, not permission to mutate AWS. It
closes the parts of the smoke target that can be implemented now while keeping
the 28-day HTTP SLO evidence clock honest. Each later AWS action must follow
`.agentic/aws/workflows/execute-approved-aws-change.md`, use a reviewed
change set or an explicitly bounded command, and receive current approval.

The target is `kanbien/staging` in `eu-west-1`, account `337159794548`, using
the `kanbien-dev` profile. It must not alter the legacy brochure site, DNS,
shared ALB default action, default certificate, Cognito configuration, stored
secrets, or any non-staging target.

## What source now defines

The repository defines these target-owned components:

- generic, provider-neutral worker lifecycle in `platform/workers/`;
- an AWS SQS adapter that can only receive, acknowledge, or release a source
  queue message;
- an encrypted SQS Standard queue and retained DLQ with `maxReceiveCount: 3`;
- a no-ingress worker task and least-privilege task role: source queue receive,
  acknowledge/release, and CloudWatch metric delivery only;
- a separate ECS Fargate worker service with desired count `0`, no ALB, no
  public port, and a task-local OpenTelemetry collector;
- source-defined worker delivery counter and execution-latency metric series,
  plus one fixed, query-only delivery-counter observation command;
- bounded rate-limit and WAF/routing proof commands that use only unauthenticated
  `GET /livez` and emit aggregate safe facts; and
- a tag-scoped $25 monthly budget definition that uses the existing alert SNS
  topic after the account activates the user-defined `service` cost tag.

The worker's direct smoke job is side-effect-free. It proves consumer
mechanics, not a producer transaction/outbox relay. No business workload may
use this path for side effects until persistence supplies the required durable
idempotency and processing state.

## Deployment sequence

1. Commit and merge the source only after local policy, package, rendered
   CloudFormation, and image-payload checks pass. Publish an immutable image
   from `main` through the existing narrow GitHub ECR workflow.
2. Read current staging state. Confirm account/region, baseline server health,
   five server alarms, shared ALB default route, listener rule priority, and
   the existing alert topic. Stop for drift.
3. Render and validate the foundation template. Create, inspect, then only
   after current approval execute a foundation change set. It may add the
   worker queue/DLQ, worker IAM/security/log groups, and tag-scoped budget. It
   must not replace or modify shared ALB default routing, DNS, certificates,
   Cognito, or secret values. Retained queues are never automatic rollback
   deletion targets.
4. Create and inspect a service change set using the published immutable image.
   It may add the worker task definition and service but must keep
   `WorkerDesiredCount=0`. Execute only after current approval and verify the
   public server remains healthy before continuing.
5. Record deployed facts separately from proof: task revision, service desired
   count `0`, source/DLQ resource existence, worker role scope, queue transport
   policy, and no worker inbound security-group rule. Do not call any worker
   metric or DLQ state healthy merely because resources exist.

## Bounded live proof sequence

Run these actions only after their source is on `main`, the reviewed resource
change set is deployed, and the current chat explicitly approves the named
operation.

| Proof | Fixed boundary | Pass condition | Evidence retained |
| --- | --- | --- | --- |
| Ingress and WAF | Read-only WAF association/listener/security-group checks plus one `GET /livez`. | Expected WAF, host rule, ALB-only server ingress, and `200`. | Status, duration, rule priority, and safe verdict only. |
| Shared rate limiting | Wait for the next fixed-window boundary, then make at most configured rate limit plus one sequential unauthenticated `GET /livez`; stop at first `429`. A window rollover is inconclusive, never a pass or a failed limiter claim. | At least one `200`, then one `429` inside the same declared window. | Aggregate counts, final status, total duration only. |
| Worker consumer | Verify source and DLQ are empty and worker desired/running count is zero; send the first fixed side-effect-free envelope; scale worker to one; observe settlement; wait 75 seconds; send the second fixed envelope; observe settlement and a final 75-second exporter-flush wait; then return worker to zero. After the declared metric-arrival grace, run the fixed `--coverage-target worker` query. | Source/DLQ are empty, worker returns to zero, and the declared delivery counter is observed with its fixed success labels and a real counter increase between the two deliveries. | Safe status/counts, task revision, metric verdict, and rollback state; never message body, receipt handle, queue URL, raw query, or AWS payload. |
| Cost controls | Activate only `user:service` cost-allocation tag, wait for billing data, then inspect tagged budget and alert configuration. | Tag active; tag-scoped budget exists with reviewed thresholds and existing topic. | Status, UTC time, safe resource name, and alert-topic ARN only. |

The rate and ingress probes are deliberately liveness-only, so they do not
contribute to protected capability SLO data. A `429` immediately on the first
request is inconclusive because an earlier caller may still occupy the shared
window; it must not be promoted into a pass by retrying or resetting state. The
proof begins at a fresh fixed-window boundary and reports a window rollover as
inconclusive, so sequential requests cannot be split across two otherwise
valid counter windows.

## Recorded public-boundary proofs

On 2026-09-23, the bounded rate-limit proof returned 120 allowed liveness
requests followed by the first `429` on request 121 within its reviewed fixed
window. The independent ingress proof also passed: the host-scoped WAF,
priority-20 host rule, ALB-only service ingress, and one public liveness
request all matched their declared policy.

These are public-boundary proofs, not protected-capability SLO observations.
Only aggregate count, status, duration, and listener-priority facts are
retained. The evidence contains no client address, HTTP body or header, WAF
payload, AWS response, credential, or token.

## Recorded worker proof

On 2026-09-23, the separately approved bounded worker command completed with
two fixed side-effect-free deliveries and returned `passed` in 278716 ms on
worker task definition revision `1`. The service was returned to desired and
running count zero, with the source and dead-letter queues empty. The separate,
fixed worker metric observation then returned `observed`.

This establishes the dormant worker consumer and delivery-metric boundary. It
does not establish a producer transaction, outbox relay, durable idempotency
store, business side-effect safety, or a worker customer SLO. The retained
evidence contains only the date, verdicts, bounded count and duration, task
revision, and dormant post-proof state; it contains no queue addresses,
message data, receipts, raw queries, or provider payloads.

## Recorded cost-control configuration

On 2026-09-23, the account's user-defined `service` cost-allocation tag was
confirmed active. The staging budget was confirmed as a 25 USD monthly budget
scoped to `user:service$platform-shell`. Its dedicated notification inventory
contained exactly the reviewed actual 50%, 80%, and 100% rules plus the
forecast 100% rule; each had an SNS subscriber. A Foundation change-set review
reported no changes, confirming the deployed stack already matched the
reviewed source.

The generic budget summary API did not embed the notification list, so the
dedicated notification inventory was used rather than treating that empty
summary field as a missing-alert drift. This evidence retains only configuration
facts. It does not retain billing amounts, subscriber addresses, email content,
or raw AWS responses.

Tagged billing data has not yet had time to appear. Until it does, the target
cannot claim charged-cost attribution or an exercised budget-alert path; that
is a time-based proof gap, not an infrastructure-deployment gap.

## Rollback and stop conditions

Rollback for the worker target means set worker desired count to `0` and return
the service task definition to the prior reviewed revision if needed. Preserve
the source queue and DLQ because both are retained resources; investigate
rather than delete messages. Restore the server only through its existing
task-definition rollback runbook.

Stop rather than improvise if a change set includes unexpected replacement,
shared-boundary changes, broader IAM, public worker ingress, any secret or raw
provider payload in output, non-empty source/DLQ before the controlled smoke,
unexpected billing cost, or a failed server health check. Record the safe
stop reason in readiness evidence and seek a new review.

## Still intentionally unresolved

- 28-day HTTP SLO evidence and its minimum eligible-observation count: time,
  not additional synthetic traffic, is the honest remaining requirement.
- a durable DynamoDB (or other selected persistence) transaction, outbox relay,
  idempotency claim, lease/fence, and worker processing record;
- reusable platform scheduler and worker-operation interfaces;
- worker SLOs, dashboard, capability alarms, and a long-term trace exporter.

These exclusions keep a controlled smoke consumer from accidentally becoming a
business persistence architecture.
