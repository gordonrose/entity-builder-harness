<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.accepted-release-and-recovery
version: 4
status: active
created_on: "2026-10-20"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.release-lifecycle
disciplines: [security, sre]
kind: standard
purpose: Define immutable accepted-release custody and bounded restoration requirements for an existing healthy deployment scope.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.release-update-and-recovery
  path: .agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md
- id: deploy.workflow.verify-accept-or-restore-release
  path: .agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md
- id: deploy.command.release-succession
  path: scripts/04.deploy/lifecycle/60-run/release-succession/script.sh
-->
# Retain Accepted Release for Restoration

An accepted release is not merely a qualified package. It is the exact qualified
immutable package that has been verified running in one declared target.

<!-- deterministic-check: allow reason="the target-specific accepted-release validator and acceptance command enforce fields; this standard assigns the durable cross-provider expectation" -->
An accepted-release record must contain the source revision, complete immutable
digest, target workload identity, private verification result, evidence
reference, acceptance time, and enough retained identity to restore the same
package. The image source revision and the commit that records acceptance are
separate facts.

Before an existing runtime is changed, retain its accepted record unchanged.
Use the governed release-succession control to archive every accepted record
immutably and atomically advance only a `current-accepted-release` reference.
The candidate does not replace that reference until candidate deployment and
verification both pass, its target/scope and source/digest agree, its complete
proof set is retained, and its configuration and permission contracts are
hashed. A caller supplies the expected predecessor; a stale or concurrent
promotion is rejected rather than overwriting history.

An interrupted promotion can be resumed only through that control: it validates
the existing archive and either completes its reference replacement or rejects a
conflict. A prior accepted record is never edited, deleted, or recreated.
Legacy records may be imported as historical evidence, but must be labelled
`legacy-not-recorded` for any facts they did not contain. They are not evidence
that an older release is compatible with a newer permission model.

Where a retained legacy image is needed after a permission-model change, record
a fresh immutable **rollback-compatibility** proof through the same
release-succession control. It binds the exact retained source/digest, current
configuration and permission-contract hashes, the rollback workload set, and
allowlisted terminal proof receipts. It is additive evidence: it neither edits
the original acceptance record nor recasts it as permission-compliant. A
selected rollback must keep administration and ordinary-migration support on a
qualified support image when the retained image lacks those bounded programs.

Restoration selects only a retained immutable digest whose application schema,
configuration and permission contract are explicitly compatible with the
current target. It must not rebuild an old source revision, select a mutable
tag, re-broaden database grants, reinstate administration credentials in an
ordinary migration task, restore migration-history write access, or undo a
revocation merely because the image is old.

Every update and restoration requires fresh target alignment, a reviewed
provider change set, a bounded deployment command, and private verification.
Neither failed verification nor provider uncertainty authorizes automatic retry
or automatic restoration. A workflow may prepare the restoration, but explicit
provider-mutation authority remains required to execute it.

Safe evidence contains identifiers, digests, revisions, verdicts, timestamps,
and opaque evidence references only. It never contains secrets, raw provider
responses, endpoints, or credentials.
