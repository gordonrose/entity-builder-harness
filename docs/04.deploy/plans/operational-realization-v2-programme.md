<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.operational-realization-v2-programme
version: 2
status: active
layer: 04.deploy
domain: deployment.realization
disciplines:
- architecture
- security
- sre
kind: implementation-plan
purpose: Replace symptom-driven target retries with a complete provider-neutral runtime-realization model and mechanically governed provider adapters.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.plans.readme
  path: docs/04.deploy/plans/README.md
-->
# Operational Realization v2 Programme

## Objective

Source, infrastructure, IAM, and tests can each be valid while their combined
runtime cannot execute. This programme makes the complete execution graph a
versioned source contract before a target changes:

```text
declared runtime graph
  -> source and artifact proof
  -> normalized target facts
  -> reviewed change shape
  -> bounded private execution proof
  -> one controlled capability operation
  -> explicit recovery after a terminal result
```

The core is provider-neutral. AWS, Azure, Oracle, or another provider is
implemented only through target-owned adapters that emit the same safe facts.

## Why v2 is required

`operational-realization-contract/v1` describes artifacts, identities,
configuration, state, asynchronous work, observability, and recovery. It does
not describe the whole runtime: artifact platform, execution environment,
artifact distribution, non-state dependencies, sidecars, health, or the
distinction between an ephemeral execution proof and a business-state mutation.
Those omissions make the contract unable to prevent the failure class we saw.

v2 is additive. It does not silently reinterpret or weaken v1 contracts.

## Required v2 graph

| Family | Required declaration |
| --- | --- |
| Artifact | Immutable payload, expected platform, provenance and payload assertions. |
| Execution environment | Operating system, architecture, isolation, resources, and bounded ephemeral-execution policy. |
| Execution units | Every primary process and sidecar, with identity, configuration, health, and dependencies. |
| Dependencies | Distribution, configuration, state, asynchronous work, telemetry, name-resolution, ingress, and egress relationships actually used. |
| Connections | Directional source/destination, transport expectation, runtime phase, and required proof. |
| Health | Liveness/readiness contract for each essential execution unit. |
| Identity and configuration | Narrow permission categories and safe input shapes only; never values. |
| Observability and recovery | Safe signals, failure categories, terminal conditions, cleanup, rollback, and new-label recovery. |

Empty collections are allowed only when the workload truly has no member of
that kind. A fake database, queue, or connection is a validation failure.

## Non-negotiable rules

1. A public rollout is never the first runtime test of a candidate.
2. Every actual dependency must have a declared node and directed edge.
3. Generic contracts/evidence contain no provider types, provider responses,
   endpoints, credentials, headers, bodies, records, task identifiers, logs,
   SQL, or queue messages.
4. Provider adapters accept no caller-selected target, role, network, digest,
   payload, or replay label; they derive scope from reviewed source.
5. A failing candidate is terminal. A new immutable candidate or label starts
   a fresh gate sequence.

## Fixed gate sequence

| Gate | Proof | Effect allowed |
| --- | --- | --- |
| G0 ownership | Target, owner, cost ceiling, steady state, and scope are complete. | Source only. |
| G1 source graph | v2 compiler and negative tests prove a complete truthful graph. | Source only. |
| G2 artifact | Digest, platform, provenance, scan, and payload assertions pass. | Publication only. |
| G3 live read | Target adapter proves all declared bindings with normalized facts. | Read-only inspection. |
| G4 change shape | Normalized plan matches the approved operation classes. | Change-set creation only. |
| G5 execution preflight | Exact candidate becomes healthy, stops, and cleans up without business-state mutation. | One declared ephemeral execution. |
| G6 controlled execution | One labelled harmless capability operation reaches terminal steady state. | One reviewed business operation. |
| G7 recovery | A separately labelled terminal recovery passes. | One reviewed recovery only. |

G5 may create one short-lived private execution instance. It must have no
public route, business write, migration, queue work, or persistent side effect,
and must prove cleanup. That is not authority to mutate application state.

## Adapter boundary

Each target implements four artifacts outside the generic core:

1. a realization mapping from generic component IDs to reviewed target
   resources, with no secret values or raw endpoint data;
2. a static verifier for source templates, workflows, policies, platform,
   composition, and mapping completeness;
3. a read-only collector that converts provider data into exact normalized
   facts while retaining raw responses only in process memory; and
4. a bounded controller which derives all inputs from the mapping, performs
   only the declared ephemeral operation, returns safe outcome categories, and
   proves cleanup.

The generic core never imports an adapter. An adapter does not grant provider
authority; a least-privilege target workflow remains separately required.

## Delivery phases

### A. Reusable foundation

Add the v2 schema, template, guide, compiler, fixtures, compatibility tests,
standard, and workflow. Tests must reject undeclared dependencies, incorrect
artifact platform, missing sidecars/health, unsafe evidence, provider leakage,
fake dependencies, and invalid ephemeral effects.

### B. Target adapter source

Create the Kanbien/staging realization mapping and AWS adapter for the server,
collector, artifact-distribution path, configuration resolution, identities,
network policy, health, telemetry, relational route, and steady state. Add
recording-client and static tests. No AWS changes occur in this phase.

### C. Candidate execution boundary

Add a dormant candidate-only task definition using the current active image.
It matches the declared server environment, roles, configuration references,
network, sidecar, and health, but attaches to no listener or public route. Its
change set may not change a service, IAM policy, database, queue, routing, DNS,
secret value, or legacy resource.

### D. Candidate proof, promotion, and persistence resumption

For a new digest, prove artifact platform/publication, update only the
candidate definition, run one private execution proof, stop it, and prove
cleanup. Only then may the normal service-only change set promote that same
digest. Only after post-rollout health and reconciliation pass may PostgreSQL
Stage 6 resume with new labels.

## Kanbien/staging implementation position

The first target slice is now implemented in source and deliberately remains
short of a claimed live proof.

- The generic realization gate supports a post-publication
  `runtime-bound-sha256` artifact binding. A target adapter must supply the
  exact digest as safe normalized evidence; mutable tags and missing bindings
  fail validation.
- The Kanbien target has a provider-neutral candidate-preflight contract and a
  CloudFormation-only dormant task definition. Its static verifier requires it
  to mirror the server task in every runtime-relevant field apart from task
  family, tags, and its distinct immutable candidate image parameter.
- The dormant definition has no ECS service, listener, load-balancer target,
  DNS change, new ingress rule, database work, queue work, or recurring cost.
  Its only live onboarding change is one task-definition addition. A later
  candidate revision may replace only that definition.
- The target-owned controller accepts no caller-selected image, task, target,
  role, network, label, or timeout. It derives one label from the candidate
  digest, rejects a consumed label, runs one task in the active server's exact
  `awsvpc` configuration, waits for `RUNNING` and `HEALTHY`, stops it, and
  verifies that no task remains running for that label. Raw provider data stays
  in process memory; output is an allowlisted safe result only.
- PostgreSQL Stage 6 now has a direct guard: before any bootstrap, migration,
  relay, worker, or restore work, the currently active immutable server image
  must have exactly one healthy, stopped candidate preflight using the reviewed
  dormant task family. This prevents a direct retry of the earlier failed
  recovery route.

The remaining target sequence is intentionally narrow: (1) deploy the
dormant definition with the known active digest, (2) publish a new immutable
candidate and replace only `CandidateImageUri`, (3) run and record the
candidate preflight, (4) promote that exact digest through the existing
service-only gate, and (5) resume the separately bounded Stage 6 proof. A
failure at any point leaves the public service untouched and requires a new
candidate digest rather than a replay.

## Completion

This programme completes when an exact candidate proves its full runtime graph
before public rollout, then the same digest is safely promoted, and PostgreSQL
continues from that proved foundation. Until then the honest state is
**operational-realization foundation in progress**, not production-proven
persistence.
