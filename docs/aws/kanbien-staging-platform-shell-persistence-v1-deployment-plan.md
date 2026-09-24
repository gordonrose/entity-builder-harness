<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-persistence-v1-deployment
version: 7
status: draft
layer: 04.deploy
domain: runtime.operations
disciplines:
- architecture
- security
- sre
kind: change-plan
purpose: Define the staged Kanbien staging deployment and bounded live proof for the DynamoDB transactional-outbox persistence reference slice.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
- id: product.plan.persistence-foundation-v1
  path: .agentic/03.product/plans/implementation/persistence-foundation-v1.md
-->
# Kanbien Staging Platform Shell: Persistence v1 Deployment Plan

## Status and authority

This is a **change plan**, not permission to mutate AWS. Every action that
creates, updates, starts, scales, or configures an AWS resource must use
`.agentic/aws/workflows/execute-approved-aws-change.md`, follow an inspected
CloudFormation change set where applicable, and receive explicit current-chat
approval.

The target is `kanbien/staging`, account `337159794548`, region `eu-west-1`,
using the `kanbien-dev` profile. The plan is limited to the bounded
platform-smoke transactional-outbox reference path. It must not alter the
legacy brochure site, DNS, shared ALB default action, listener default
certificate, stored secret values, existing alert destination, or any
non-staging target.

## Read-only baseline — 2026-09-24

The following was inspected read-only before this plan was written:

| Surface | Observed state | Meaning for this plan |
| --- | --- | --- |
| Foundation stack | `UPDATE_COMPLETE` | Existing shared target can receive an additive Foundation change set. |
| Service stack | `UPDATE_COMPLETE` | Existing public service is healthy enough to plan a rolling task-definition update. |
| Public ECS service | desired/running `1/1`, task revision `6` | Preserve its service name, ALB attachment, desired count, and normal health behaviour. |
| Worker ECS service | desired/running `0/0`, task revision `1` | Preserve dormant steady state; it scales to one only during an approved proof. |
| SQS source/DLQ | Both existing | Reuse them; do not replace, purge, or delete them. |
| Persistence table | Absent | Expected: it is source-defined but has not been deployed. |
| Existing Cognito resource server | Only `platform-shell/smoke.read` | It cannot yet issue the write scope needed by the harmless acceptance route. |
| Existing controlled-smoke client | Only `platform-shell/smoke.read` | Keep it read-only; do not give routine synthetic-read automation write capability. |

This baseline contains only resource state, names, counts, and revisions. It
does not retain credentials, secret values, tokens, request bodies, table
items, queue messages, or provider payloads.

## Foundation execution evidence — 2026-09-24

The immutable persistence-capable image was published through the existing
GitHub workflow before any Foundation change was executed. Its safe workflow
result was successful and its immutable digest was
`sha256:a112641f69f60984bfa2e1660b756c36449c0bf66c4dc8af3e2c544c21ecf27e`.

The reviewed additive Foundation change set was then executed. It added the
persistence table, relay task role and network group, relay log groups, and
only the narrow server/worker/deployment-role policy changes defined above.
It did not delete or replace a shared routing, DNS, certificate, ALB, queue,
rate-limit, or public-service resource.

Post-deployment inspection established these safe facts:

| Surface | Verified state |
| --- | --- |
| Foundation stack | `UPDATE_COMPLETE` |
| Persistence table | `ACTIVE`, on-demand billing, encryption, point-in-time recovery, deletion protection, and retain-on-delete policies |
| Required indexes | `OutboxDueIndex` and `LineageCauseIndex` |
| Relay network boundary | No ingress; only reviewed TLS and DNS egress paths |
| Workload roles | Server atomic transaction only; worker queue settlement/processing state only; relay due-query, lease, source-queue send, and safe metrics only |
| Preserved runtime | Public server desired/running `1/1`; worker desired/running `0/0`; source and dead-letter queues empty; worker visibility timeout `120` seconds |

No service task definition has been registered from this persistence image,
no relay task has run, no worker has been scaled, no Cognito scope or client
has changed, and no persistence write has been made. Those remain later,
separately approved stages.

## Service change-set inspection — 2026-09-24

The service change set for the immutable image was created and inspected before
execution. It contained exactly five changes:

- add `RelayTaskDefinition` only—a dormant task definition, not an ECS service
  or scheduler;
- update the existing public server service to reference a new task revision,
  without replacing that service;
- replace the public server task definition, as normal for an ECS container
  definition revision;
- update the existing worker service to reference a new task revision, without
  replacing it and with desired count remaining `0`; and
- replace the worker task definition, again only as an ECS container definition
  revision.

The review found no shared-boundary, routing, load-balancer, DNS, certificate,
queue, alert-destination, Cognito, or permission-scope change. The Foundation
and service stacks remain `UPDATE_COMPLETE`; the public server remains
desired/running `1/1`, and the worker remains `0/0`. Execution requires a new,
explicit approval because it will cause the public service to roll to its new
task definition.

## Service execution evidence — 2026-09-24

After explicit approval, the reviewed service change set was executed. The
service stack reached `UPDATE_COMPLETE`; its public server completed the
rolling revision update with desired/running `1/1`, the expected immutable
persistence-capable image active, one healthy target, and public `/livez`
returning `200`.

The existing fixed protected-read smoke also returned `200` with a redacted,
safe result. This confirms that the deployment did not break the established
read-only authentication path. It did not request a new scope or send a write
request.

The worker completed its task-definition update while remaining desired/running
`0/0`; no relay task is running and the source and dead-letter queues remain
empty. No Cognito resource, secret, scope, client, persistence item, relay
pass, or worker delivery was changed or exercised.

This is therefore a successful **service-deployment proof**, not yet an
outbox-delivery proof. The next bounded stage is separately approving the
write-only identity/client setup and exactly one harmless acceptance request;
only after that may a relay pass and temporary worker scale-up be considered.

## Write identity provisioning evidence — 2026-09-24

The one reviewed `platform-shell/smoke.write` scope, separate confidential
client-credentials client, and target-owned persistence-smoke secret were
found provisioned by a narrow staging preflight. The source record had not
yet been reconciled, so this stage records only the safe client identifier and
secret reference in the target profile; the secret value was neither read nor
recorded.

The server has not yet been configured to trust this client: its explicit
additional-client allowlist still contains only the existing negative-test
client. Consequently, no write token has been used, no work-item request has
been sent, and no table, queue, relay, or worker action has occurred in this
stage. The next step is a reviewed server configuration deployment that adds
only this already-provisioned client identifier to that allowlist.

## Write-client allowlist deployment evidence — 2026-09-24

The reviewed staging service change set contained exactly two expected
changes: a normal replacement of the public server task-definition revision
for its container environment, and an in-place update of the existing server
service to reference that revision. It did not include a worker, relay, queue,
Cognito, DNS, routing, alert, or secret-value change.

After execution, the service stack reached `UPDATE_COMPLETE`; the server was
desired/running `1/1` with a completed rollout, its target was healthy, and
public liveness returned `200`. The worker remained `0/0` and both queues
remained empty. The deployed server now trusts exactly the pre-existing
negative-test client and the isolated persistence-write client. No token was
requested and no work-item write was sent in this deployment stage.

## Atomic-acceptance diagnostic evidence — 2026-09-24

The one approved no-body work-item acceptance request returned safe status
`503` in `229` milliseconds. An aggregate-only table check proved that the
atomic transaction committed no records, so no outbox obligation exists. The
relay was not run and the worker was not scaled.

Read-only diagnosis established that the active server task has the required
persistence configuration, the table is active with both required indexes,
and its task role is allowed to perform the atomic DynamoDB transaction. The
account audit trail does not retain DynamoDB data-plane events, so it cannot
recover the provider error class for this earlier request.

This uncovered an application-observability gap, not deployment drift: a
route could return a safe failure response while dropping its stable internal
failure class before profile-governed logs, metrics, and traces. The source
remediation adds a response-only `observability.errorClass` fact. The server
projects that value only through the route's approved profile; it is never
serialized into the HTTP response and may not carry provider messages,
payloads, identifiers, or credentials. Its local contract and server-runtime
proofs pass.

No second acceptance request is permitted by this proof stage. The next live
action requires a separately reviewed image deployment of that remediation,
healthy server verification, and fresh explicit approval for exactly one
replacement harmless acceptance request before any relay or worker action.

## Desired source-defined change

### Foundation stack: additive resources and narrow policy changes

The reviewed Foundation template is expected to:

- create `PlatformPersistenceTable` with on-demand billing, server-side
  encryption, point-in-time recovery, deletion protection, retain-on-delete,
  and only `OutboxDueIndex` plus `LineageCauseIndex`;
- create the non-public relay security group, relay task role, and separate
  relay application/collector log groups;
- modify the server role only to permit the atomic write for the selected
  persistence table;
- modify the worker role only to read/create/update durable processing state;
- preserve the worker’s lack of due-query and queue-send permission;
- permit the relay only to query `OutboxDueIndex`, get/update outbox rows, and
  send to the existing source queue; and
- extend stack outputs and the deployment role’s pass-role list only for the
  reviewed relay task role.

It must not replace the shared ALB, host rule, DNS record, certificate, SQS
queues, existing rate-limit table, or the existing public server service.

### Service stack: revised task definitions, no new continuous process

The reviewed service template is expected to:

- register a new public-server task revision with selected persistence
  configuration and the existing rolling-health/circuit-breaker policy;
- register a revised worker task definition with table/index configuration and
  a 90-second durable lease inside the declared 120-second SQS visibility
  window, while retaining worker desired count `0`;
- register `RelayTaskDefinition` with no port, load balancer, health endpoint,
  ECS service, or scheduler; and
- pass only the exact Foundation exports required by those definitions.

Creating a task definition does not run a task. The relay remains dormant until
one separately approved `ecs run-task` invocation.

## Required identity decision before execution

The source task configuration names `platform-shell/smoke.write` for the new
`platform-smoke.persistence.work-item:create` permission, but the target
profile's auth declaration and the deployed resource server/read-smoke client
currently expose only `smoke.read`. The source prerequisite must make that
scope declaration explicit before any live identity change is proposed.

**Recommended decision: create a separate confidential machine client that
may request only `platform-shell/smoke.write`.** Store its generated secret in
a new target-owned Secrets Manager secret; do not print it or add it to the
repository. Add its generated client ID only to the server’s approved client
allowlist through reviewed target configuration. Keep the existing controlled
read client, its secret, and the GitHub synthetic workflow read-only.

This is safer than adding the write scope to the existing read client because
the read client’s secret is deliberately available to bounded synthetic-read
automation. A separate write client limits the blast radius of that automation
and makes the controlled persistence proof independently revocable.

The source prerequisite is now complete and locally validated. The two focused
commands are:

- `npm run platform:shell:persistence-write-client:provision -- --validate`,
  which fails closed unless the profile names the one reviewed scope, client,
  secret, starting resource-server state, and lifecycle; and
- `npm run platform:shell:persistence-smoke -- --validate`, which validates the
  one fixed no-body `POST /smoke/work-items` proof. Its live mode refuses any
  status other than `deployed-pending-write-proof`.

The provisioner accepts no arbitrary scope, client name, secret name, or
target. It creates the single client and secret, rolls back only changes it
made if a later step fails, and emits only a client ID and secret ARN. The
smoke command accepts no caller-supplied route, request body, client ID,
scope, or request ID; it emits only a verdict, HTTP status, and rounded
duration. The source commands remain the execution controls. The identity
provisioning stage is now recorded above; no write request has been made yet.

## Ordered execution plan

1. **Complete in source:** validate the controlled write-client provisioner
   and one-shot smoke command locally, then merge the persistence source to
   `main`. This does not provision an identity or send a request.
2. Publish a new immutable platform-shell image from `main` through the
   existing narrow GitHub ECR workflow. Record only the image digest and safe
   workflow result.
3. Re-run the read-only preflight: account/region, both stack states, public
   service health, worker desired/running zero, empty source/DLQ, listener
   rule/default action, existing alert topic, and absence of the persistence
   table. Stop for drift.
4. Render and validate the Foundation template. Create and inspect its change
   set. Stop for any replacement, unexpected deletion, shared-boundary change,
   public relay/worker ingress, broader IAM, altered alert destination, or
   cost-sensitive unplanned resource.
5. After explicit current approval, execute the reviewed Foundation change
   set. Inspect the deployed table protection/indexes, task roles, no-ingress
   groups, outputs, logs, and preserved queue configuration.
6. Create and inspect the service change set with the published immutable image
   digest and `WorkerDesiredCount=0`. Confirm that it registers definitions
   without starting relay/worker work and preserves the public service’s
   desired count and ALB attachment.
7. After explicit current approval, execute the reviewed service change set.
   Wait for public-service stability, verify target health, and run only the
   existing bounded read/health proof before granting the new write client.
8. After explicit current approval, create the reviewed write-only Cognito
   resource-server scope, separate client, and target-owned secret. Read back
   only safe identifiers and scope lists. Never rotate, print, or reuse the
   read-smoke secret.
9. Record the returned client ID and secret ARN in the target profile with the
   lifecycle status `provisioned-pending-service-deployment`. Deploy the small
   target configuration revision that adds only that client ID to the explicit
   client allowlist; record `deployed-pending-write-proof` only after public
   service health is verified. The secret remains out of ECS task environment.
10. Run exactly one controlled no-body work-item acceptance request. On a
    successful safe result, record `deployed-and-write-proven`, which prevents
    a second invocation using the same deterministic request identity. If it
    fails, record only safe aggregate diagnostics, do not relay or scale a
    worker, and require fresh approval before any replacement request.
11. Run one relay `RunTask` and a bounded worker scale-up to one. Observe only safe
    status/count/metric/log facts. Return the worker to zero in a `finally`
    path, including a failed proof.

## Bounded live proof and pass conditions

| Stage | Fixed action | Pass condition | Retained evidence |
| --- | --- | --- | --- |
| Atomic acceptance | One fixed `POST /smoke/work-items` with a write-only token. | Success response and one safe acceptance outcome; no request body. | Status, duration, source commit/image revision, safe verdict. |
| Relay | One `ecs run-task` from `RelayTaskDefinition`; it handles at most one due outbox fact and exits. | Task stops successfully, with one published transition and no raw envelope/log payload retained. | Task result, exit status, safe transition metric/log verdict. |
| Worker | Scale the existing worker service from zero to one only long enough to receive the source message, then return it to zero. | One durable completion; duplicate delivery is later tested only in a separately approved rehearsal. | Desired/running post-state, safe completion/metric verdict, no message or receipt data. |
| Recovery | Inspect queue/DLQ, task state, table-safe status, and public-server health. | Worker is zero, queues are empty, public service remains healthy. | Aggregate counts/statuses and rollback state only. |

The first proof does **not** prove continuous relay scheduling, business
workload safety, product retention/lifecycle policy, a worker SLO, or all
retry/DLQ failure modes. Those require separately bounded rehearsals.

## Rollback and stop conditions

- If the public task revision fails health checks, use the existing
  [staging rollback runbook](runbooks/platform-shell-staging-rollback.md) to
  restore the prior known-good server task definition.
- If a worker proof is unhealthy or inconclusive, return desired count to zero
  first; preserve source/DLQ messages and investigate rather than purging or
  replaying them.
- Do not delete the persistence table. Its CloudFormation retain policy and
  deletion protection are intentional. An unneeded table is a cost-review
  issue, not an automatic cleanup target.
- If a relay task fails, do not start another automatically. Inspect its safe
  exit/metric facts, wait for lease expiry where applicable, and seek separate
  approval for any retry.
- Stop for unexpected resource replacement/deletion, wider IAM, public
  ingress, identity-scope drift, non-empty queues before the proof, sensitive
  output, unexpected cost, failed public health, or a result outside this
  plan’s fixed boundaries.

## Completion boundary

The persistence smoke reference reaches its first live-proof milestone only
after the target profile/readiness record contains safe evidence for the
reviewed change sets, table/role/task deployment, separate write-client scope,
one controlled acceptance, one relay pass, one durable worker completion, safe
telemetry delivery, and worker return to zero.

It is not a declaration that every future Entity Builder feature uses DynamoDB
or SQS, nor that this staging target has a continuously operating outbox
service.
