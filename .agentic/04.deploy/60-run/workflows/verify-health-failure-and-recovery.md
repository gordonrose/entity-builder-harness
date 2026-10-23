<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.verify-health-failure-and-recovery
version: 8
status: active
created_on: "2026-10-21"
updated_on: "2026-10-23"
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
2. Validate every workload's type-aware `health_recovery` entry, binding,
   health-signal mapping, and source/command trace. A shared image is not proof
   that two workloads execute the same code. For a dependency-bearing server,
   stop if the provider replacement signal is dependency readiness rather than
   process liveness. Stop on an absent, malformed, or mismatched declaration.
   When a scope declares a required persistence dependency, validate its
   persistence diagnostic mapping: controlled provider-neutral codes only,
   workload-appropriate consequence, and an unclassified stop-and-escalate
   fallback. This declaration check does not replace adapter or live proof.
   Validate the target scope lifecycle inventory so no new-framework scope is
   omitted and no two active scopes claim the same workload identity.
3. Run the declared local and package proof commands when their status is
   `planned` or when their relevant behavior changed. A passed record does not
   excuse a stale proof after that behavior changes.
4. Before accepting a dependency-bearing scope, require applicable live failure
   proof or a separately reviewed exception. Do not treat a generic endpoint
   response as that proof.
   If migration execution is declared, require all three persistence recovery
   proof requirements: retained data after replacement, compatible image
   restoration, and isolated database restoration. Do not let evidence for one
   operation substitute for either of the others. Before accepting verifier or
   migration evidence, confirm the declared repeat, concurrent, conflicting,
   lost-response, and cleanup/replay behaviours were covered by the applicable
   local and package proof; do not infer them from one successful execution.
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
Also stop when migration execution lacks one of its separate persistence
recovery requirements, when an image rollback claims database reversal, or
when a restore would alter its source database. Also stop when a verifier could
silently recreate or overwrite its acceptance record, clean up before the
declared retention boundary, or when a migration could replay a checksum
mismatch or race another executor.
