<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.standard.operational-realization-applicability
version: 1
status: active
created_on: "2026-10-24"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.realization
disciplines: [agentic, architecture, sre]
kind: standard
purpose: Own the bounded provider-specific applicability exception without changing its approval requirements.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: aws.readme
  path: .agentic/aws/README.md
-->
# Provider Operational Realization Applicability

The generic [deployment proof standard](../../04.deploy/standards/operational-realization-gate.md) owns contract and proof semantics. This provider surface owns the following operation-specific applicability and approval conditions.

## Bounded PostgreSQL Stage 6 Applicability

The [Kanbien/staging PostgreSQL restart plan](../plans/implementation/postgresql-stage6-restart-2026-10-03.md)
provides an operation-scoped alternative only after the user explicitly adopts
this applicability change and approves its concrete execution plan. Saving a
draft or applying this instruction change alone grants no execution authority.
Until both approvals exist, the normal requirements below remain effective.

For that approved slice only, its reviewed operation/evidence matrix replaces
whole-route generic contract/compiler migration and full-estate programme
completion as prerequisites. It must cover every actual dependency of the
selected PostgreSQL operation: reviewed source, immutable image and entrypoint,
adapter/target compatibility, identity, safe configuration shapes, TLS/network,
database semantics, queue completion, observability, cost and bounded recovery.
Evidence from a healthy HTTP process does not qualify a relational task.

Existing executable gates remain binding, including applicable realization,
reconciliation, change-shape and candidate/task preflights. A required failure
pauses the affected operation and its dependants while its outcome is reconciled
and relevant code/configuration is repaired within the approved allowance.
Rerun affected checks, prove proportionate prevention, qualify a changed image
and resume from the first incomplete checkpoint. Do not close out merely to
report an ordinary failure that can be safely repaired within that authority.
No failed check is bypassed or manufactured into a pass.

The concrete approval must include the plan's source/configuration repair,
image-publication, reattempt, time, cost and owned-recovery allowances. Passing
source review and renewed operation bindings within them do not require a new
human execution approval per repair. Existing controllers must enforce the
supported identities, checkpoint semantics and cumulative limits before this
route is executable; instruction prose alone is insufficient. Scheduler,
storage, tenant authority and the replacement programme remain deferred.

Preserve consumed labels, terminal outcomes, uncertain-outcome reconciliation,
rollback/restore and verified cleanup. Reuse unchanged artifact evidence only
with unchanged relevant bindings and valid freshness; a failed attempt remains
terminal. A new attempt need not imply a new image, but must use an explicitly
reviewed, supported identity and recovery route within approved limits. Count
all failed or possibly accepted submissions across new labels/images/chats.
Escalate exhausted limits, new effects, broader permissions, persistent-data
repair outside the approved manifest, or inability to reconcile and recover
safely. Expressly approved cleanup of positively owned disposable restores and
reviewed rollback use their recovery allowance without redundant reapproval;
other destructive actions need separate authority.

For every material failure record evidence, cause and earlier-check gap,
correction/verification, proportionate prevention with proof, and resumed
outcome or precise blocker in existing Stage 6/session records. At closeout
provide both PostgreSQL acceptance evidence and those completed records.
Keep evidence safe and append-only. Other capabilities use the normal
contract/compiler route; generic schemas and compiler guarantees are unchanged.
