<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.kanbien-staging-image-execution-preflight-v1
version: 2
status: deprecated
layer: 04.deploy
domain: runtime.operations
disciplines:
- architecture
- security
- sre
kind: implementation-plan
purpose: Prevent public-service rollout from being the first proof that a candidate platform image can execute in its real target boundary.
portability:
  class: source-only
  targets: []
used_by:
- id: deploy.plan.operational-realization-v2-programme
  path: docs/04.deploy/plans/operational-realization-v2-programme.md
-->
# Kanbien staging image execution preflight v1

> **Superseded as an independent programme.** This document captured one
> symptom (candidate image execution) after a failed rollout. Its bounded
> candidate-task approach is now implemented only as a controlled sub-slice of
> the governing
> [`operational-realization-v2-programme.md`](operational-realization-v2-programme.md).
> That active programme is the source of truth for current implementation and
> live-proof status; this document remains a historical design trace.

## Decision

An immutable image is not eligible for a public ECS service rollout merely
because it built, scanned, and exists in ECR. Before the active service image
changes, the same candidate digest must complete one bounded, non-public
execution preflight in the target's real Fargate boundary.

The provider-neutral policy belongs in the Operational Realization Gate. This
plan owns the AWS/Fargate adapter and the Kanbien staging implementation. It
does not alter the public default route, DNS, Cognito, alert destination,
database data, queue messages, or secrets.

## Failure that prompted the plan

On 2026-09-27 a reviewed PostgreSQL recovery image passed source, image,
scan, and change-set gates but a public-service rollout could not retrieve its
image. CloudFormation automatically rolled the service stack back. The old
server remained available; the worker stayed at zero; the relational bootstrap
never ran; and the isolated relational queues remained empty.

That was a safe failure, but it exposed a missing proof edge: published image
to real Fargate execution. The category is not a root-cause conclusion. No
image, IAM, networking, or runtime correction may be assumed until the new
preflight isolates and proves the relevant edge.

## First-principles execution graph

```text
source + immutable digest + provenance
        │
        ▼
candidate task definition ── same execution role, task role, configuration,
        │                    network policy, CPU/OS, sidecar and health check
        ▼
one private Fargate preflight task ── healthy ── controlled stop and cleanup
        │
        ▼
normal service-only change set ── public service rollout
```

The candidate task is not registered with an ALB target group. Its security
group permits no new public ingress. It does not call a business route, create
a record, send a message, start a worker, run a migration, or contact a
database beyond dependencies already required by normal server startup.

## Required source changes

### 1. Provider-neutral realization contract correction

The generic Operational Realization contract must support a bounded execution
unit with no state store and no asynchronous channel. It must not require a
fake persistence or queue declaration simply to describe an image-start
preflight. The compiler, schema, template, guide, fixtures, and boundary tests
will accept empty state/async collections only when no execution unit refers to
them; all actual references remain strict.

### 2. Candidate and active artifact separation

The staging service template will retain `ImageUri` as the active service
image and add a distinct required `CandidateImageUri` used only by a new,
dormant preflight task definition.

The initial onboarding change set supplies the currently active immutable
digest for both parameters. It may add the dormant task definition but must
not modify an ECS service, IAM policy, network rule, queue, database, ALB,
WAF, DNS, alert destination, or secret value.

For each later image:

1. update only `CandidateImageUri` and the preflight task definition;
2. run the bounded Fargate preflight; and
3. only after a passing result, update `ImageUri` to that exact digest through
   the normal reviewed service-only change set.

This prevents a candidate failure from replacing the live public task
definition.

### 3. Exact Fargate execution preflight

Add a target-owned controller under `scripts/04.deploy/` that accepts no
caller-selected target, digest, task, role, subnet, security group, payload,
credential, endpoint, or timeout. It will derive all values from the committed
target profile and the deployed candidate task definition.

Before starting a task, it verifies:

- the reviewed account, region, Foundation stack, and service stack;
- an immutable digest-shaped candidate image is bound to the candidate task;
- the active service has not already changed to that candidate digest;
- the candidate task uses the reviewed server execution/task roles, CPU/OS,
  environment and secret-reference shape, read-only filesystem, sidecar, log
  policy, and health check; and
- the preflight network configuration is derived from the existing server
  service, with no target group attachment.

It creates at most one labelled task per candidate digest. It waits only for
the bounded healthy state, stops that private task deliberately, verifies
cleanup, and emits only stable check identifiers and one allowlisted outcome:
`passed`, `image-distribution-failure`, `execution-authority-failure`,
`network-path-failure`, `runtime-startup-failure`, `health-failure`, or
`unclassified-failure`. It never prints or commits task identifiers, raw stop
reasons, logs, headers, records, messages, endpoints, credentials, or provider
responses.

### 4. Artifact publication proof

The image build will declare the reviewed target platform explicitly. The
publication workflow will pull and inspect the exact ECR digest for that
platform before scan/attestation completion. This is an artifact proof, not a
substitute for the Fargate execution preflight.

The target profile, static workflow verifier, image-builder tests, and the
realization adapter will all enforce the same declared platform fact.

### 5. Normalized evidence and gates

The AWS adapter converts source, artifact, semantic-integration, live-read,
change-set, and execution-preflight results into safe normalized facts for the
generic compiler. The PostgreSQL relational Stage 6 controller may not run
bootstrap until that contract passes through `execution-preflight` for the
exact active candidate image.

The adapter will bind each proof to a candidate digest internally, while the
provider-neutral facts expose only component IDs and passing check IDs. Target
evidence may name the reviewed source commit and digest but never provider
payloads or secret-bearing values.

## Delivery stages and gates

| Stage | Work | Mutation scope | Pass condition |
| --- | --- | --- | --- |
| A | Correct generic contract support for non-persistent execution units. | Source only. | Compiler and fixtures reject fake/undeclared edges and accept a genuine no-state preflight unit. |
| B | Define the staging realization contract, adapter, controller, template, static checks, and runbook. | Source only. | Full deterministic suite passes. |
| C | Add the dormant candidate task definition using the existing known-good active digest. | One reviewed task-definition addition only. | Change set has no public-service, IAM, network, data, or routing change. |
| D | Publish a candidate image, update only `CandidateImageUri`, and run one preflight. | One candidate task-definition replacement and one private task lifecycle. | Candidate becomes healthy, is cleaned up, and normalized execution-preflight evidence passes. |
| E | Promote the same candidate digest through the existing service-only change-set guard. | Existing reviewed task-definition/service-reference shape only. | Public service is healthy and post-rollout read checks pass. |
| F | Resume PostgreSQL Stage 6 from the realization-gate-controlled bootstrap route. | Existing bounded proof scope. | Bootstrap precedes any migration, relay, worker, or restore stage. |

Any non-passing stage is terminal for its immutable candidate/label. The next
attempt requires a new candidate digest or label and a reviewed correction;
there is no direct replay.

## Cost, permissions, and rollback

The dormant task definition has no recurring cost. A preflight creates one
short-lived Fargate task using existing capacity/networking and returns to zero
tasks. It adds no database, storage, queue, NAT, load-balancer, DNS, or alert
resource. The target execution role receives no broader permission: the probe
uses the same already-reviewed roles as the server.

The candidate task never changes the public service. If it fails, it is stopped
and the existing active image remains in service. If an active-service rollout
later fails, CloudFormation's normal rollback retains the last healthy service
revision; it does not authorize a database or queue recovery action.

## Completion evidence

This plan is complete when the generic realization compiler accepts the
PostgreSQL route contract through `execution-preflight`, the candidate task has
proved an exact image in the real Fargate boundary without public traffic, the
same digest has been promoted through a constrained change set, and the
evidence records show safe source/artifact/live-read/change-set/preflight
facts. Only then can the PostgreSQL Stage 6 bootstrap be attempted again.
