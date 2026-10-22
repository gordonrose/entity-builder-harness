<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.verify-health-failure-and-recovery
version: 3
status: active
created_on: "2026-10-21"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [security, sre]
kind: workflow
purpose: Route scope health, safe-failure, and recovery declaration validation before live release verification or acceptance.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.verify-accept-or-restore-release
  path: .agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md
-->
# Verify Health, Failure, and Recovery

## Use When

Use when a scope becomes runnable, changes its liveness/readiness/dependency
behaviour, or is about to accept or restore a release. Follow
`require-health-failure-and-recovery-declaration.md` and validate the scope
contract with `validate-health-failure-and-recovery-declaration` before calling
provider or target commands.

## Required sequence

1. Locate the canonical scope declaration; do not construct a parallel health
   record in a plan, README, or provider template.
2. Validate every workload's type-aware `health_recovery` entry, binding, and
   source/command trace. A shared image is not proof that two workloads execute
   the same code.
   Stop on an absent, malformed, or mismatched declaration. Validate the target
   scope-health inventory so a new active workload cannot be omitted.
3. Run the declared local and package proof commands when their status is
   `planned` or when their relevant behavior changed. A passed record does not
   excuse a stale proof after that behavior changes.
4. Before accepting a dependency-bearing scope, require applicable live failure
   proof or a separately reviewed exception. Do not treat a generic endpoint
   response as that proof.
<!-- deterministic-check: allow reason="the target-specific release and verification controls perform the provider reads; this workflow routes the required human decision" -->
5. Before live verification or restoration, confirm that the deployed operation
   and recovery path match the declaration. Record only safe verdicts and
   evidence references.

For a passed one-shot completion proof, validate through the selected provider
mapping that the recorded exit/result matches the declared success criteria,
the actual evidence boundary matches `fresh_after`, and the recorded duration
is within the declared deadline. A task that was merely submitted, an older
accepted result, or two self-declared timestamps do not prove the current
operation.

## Stop conditions

Stop rather than guess when liveness and readiness are indistinguishable,
selected dependencies are absent from readiness/failure behaviour, a diagnostic
would disclose sensitive data, uncertain work could be replayed automatically,
or a deferred live proof lacks an owner, follow-up, and review boundary.
