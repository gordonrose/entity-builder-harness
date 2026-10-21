<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.accepted-release-and-recovery
version: 3
status: active
created_on: "2026-10-20"
updated_on: "2026-10-21"
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
The candidate does not replace it until candidate deployment and verification
both pass. Restoration selects only the retained immutable digest; it must not
rebuild an old source revision or select a mutable tag.

Every update and restoration requires fresh target alignment, a reviewed
provider change set, a bounded deployment command, and private verification.
Neither failed verification nor provider uncertainty authorizes automatic retry
or automatic restoration. A workflow may prepare the restoration, but explicit
provider-mutation authority remains required to execute it.

Safe evidence contains identifiers, digests, revisions, verdicts, timestamps,
and opaque evidence references only. It never contains secrets, raw provider
responses, endpoints, or credentials.
