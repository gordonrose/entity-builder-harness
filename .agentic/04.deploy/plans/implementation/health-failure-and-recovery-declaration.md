<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.implementation.health-failure-and-recovery-declaration
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [agentic, architecture, security, sre]
kind: implementation-plan
purpose: Implement a reusable declaration and validation route for runtime health, safe failure behaviour, and bounded recovery.
portability: { class: source-only, targets: [] }
used_by:
- id: deploy.plan.implementation.platform-to-target-chain-control
  path: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md
-->
# Health, Failure, and Recovery Declaration Work Package

## Objective

Make a deployable scope state, and prove structurally, how it becomes live,
ready, safely unavailable, recovered, restored, and verified. The capability
must be reusable across targets and providers; `kanbien-core-platform` is the
first fixture, not a special case.

## Scope

1. Add a provider-neutral Run standard, embedded declaration schema, template,
   authoring guide, and verification workflow.
2. Add one deterministic validator with positive and negative fixtures.
3. Route the validator through the generic product-runtime workflow, the Run
   workflow, the lifecycle map, the core target-declaration check, and the
   core release-contract check.
4. Add the factual bootstrap-runtime declaration: its liveness/readiness
   endpoints, startup-failure behaviour, no selected dependencies, ECS task
   replacement policy, immutable-release restoration policy, passed
   local/package proof, and explicitly deferred live-fault rehearsal.

## Non-goals

- No AWS mutation, fault injection, live task termination, or release update.
- No new persistence provider, secret, database, queue, identity, ingress, or
  observability foundation.
- No claim that deferred live failure recovery has been exercised.

## Completion criteria

- A scope contract without distinct health operations, safe startup behaviour,
  bounded task/release recovery, or accountable proof fails deterministically.
- The current core scope validates and its existing target/release regression
  checks continue to pass.
- A later scope can use the same declaration and validator without copying
  core-server paths or AWS vocabulary.
- The active lifecycle route directs an agent to the contract before a release
  is accepted or restored.

## Follow-on authority

A deliberate AWS failure/replacement/circuit-breaker rehearsal is a separate
target-mutation packet. The contract makes that future proof visible; it does
not grant authority to perform it.
