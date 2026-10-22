<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.implementation.health-failure-and-recovery-declaration
version: 3
status: active
created_on: "2026-10-21"
updated_on: "2026-10-22"
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

1. Add a provider-neutral Run standard, workload-type-aware embedded declaration
   schema, template, authoring guide, and verification workflow.
2. Add one deterministic validator with positive and negative fixtures for
   servers, workers, tasks, freshness, bindings, and legacy exceptions.
3. Route the validator through the target scope-health inventory, generic product-runtime workflow, the Run
   workflow, the lifecycle map, the core target-declaration check, and the
   core release-contract check.
4. Add the factual bootstrap-runtime declaration: the core server's
   liveness/readiness endpoints, startup-failure behaviour, no selected
   dependencies, ECS replacement policy, immutable-release restoration policy,
   and recovery proof; and the private verifier's deadline, exit/result,
   interruption and no-retry completion policy with fresh completion evidence.

## Non-goals

- No AWS mutation, fault injection, live task termination, or release update.
- No new persistence provider, secret, database, queue, identity, ingress, or
  observability foundation.
- No claim that deliberate readiness-failure injection or ECS deployment
  circuit-breaker rollback has been exercised.

## Completion criteria

- A workload without a known type, applicable health/completion requirements,
  matching binding, bounded recovery, fresh meaningful task evidence, or
  accountable proof fails deterministically.
- Every active new-framework target scope is indexed and validated; a legacy
  exception is only valid for a retiring named reference workload.
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

## Proposed bounded live rehearsal — review and execution authority required

This is a proposed review packet, not standing permission to mutate AWS. It preserves
the accepted candidate: source revision
`1b56931d914d8f91162b30398967c150b1032e9b`, immutable image digest
`sha256:0992b48fdd66bb53c08d621e871b2e8975f40b8e6bbaa62816803f755d55d5d5`,
and the current private `kanbien-core-platform/bootstrap-runtime` target. It
does not publish an image, alter configuration, or introduce a deliberately
bad application release.

### Preconditions

1. Run the inventory, target-declaration, release-contract, current cost
   condition, and runtime-alignment controls. The historical Target-cost waiver
   has an expiry and is not evidence that a new rehearsal is currently allowed.
2. Confirm the accepted service has desired/running count one, the accepted
   task definition and digest, retained restoration identity, private endpoint
   access, and no unresolved deployment.
3. Obtain one bounded AWS execution approval covering the exact cases below,
   including one controlled task stop and, separately, the timeout-fixture
   cleanup stop. Stop on an access denial, cost-condition failure, unhealthy
   baseline, or an outcome outside the stated cases.

### Cases and commands

| Case | Exact candidate/configuration | Command and expected result |
| --- | --- | --- |
| Successful replacement and completion | The accepted image and task definition; no image/configuration change. | First run `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-accepted-workload-replacement/script.sh --json`; after approval run the same command with `--execute --json`. ECS must replace exactly one stopped accepted server task; the verifier must exit 0 with `KANBIEN_CORE_RELEASE_VERIFIED` within its declared 120 seconds. |
| Controlled verifier failure | The same accepted image and private verifier task definition, with a fixed target-bound expected-source-revision mismatch override only. | Run `rehearse-private-verifier-fault/script.sh --case expected-source-mismatch --json`, then with `--execute` under the bounded authority. It must run one verifier task, expect non-zero exit and `KANBIEN_CORE_RELEASE_VERIFICATION_FAILED`, and must not change the server service, image, task definition, or accepted release. |
<!-- deterministic-check: allow reason="The target-specific rehearse-private-verifier-fault script enforces the controller-deadline case and containment; this plan preserves the reviewed live-rehearsal record." -->
| Controlled controller timeout | The same accepted image and verifier task definition, with a fixed target-bound sleep-only command override of 121 seconds. | Run the same command with `--case controller-deadline`. At 120 seconds it must return `private-verifier-controller-deadline-remote-task-still-running`, must not launch another task or restore automatically, then stop only the returned fixture task and confirm it is stopped. |

### Evidence, cleanup, and final checks

For each case, record only safe evidence: source revision, immutable digest,
task-definition identities, declared deadline, actual provider start/stop times,
duration, exit/result verdict, case identifier, and final server health. A
successful case is accepted only when its completion evidence matches the
declared result and boundary. Failure and timeout cases are successful only
when they produce the declared blocker without changing the accepted server.

After each case, inspect the service desired/running count, primary task
definition, digest, deployment state, fresh private verification where
applicable, and target cost/alignment verdict. The timeout fixture's cleanup
must be a separately logged, target-bound stop of the identified fixture task;
then repeat the same final-state checks. Restore the retained accepted release
only if those checks show it changed, using the existing reviewed restoration
route. Do not use an ad-hoc bad release or arbitrary command override.
