<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.release-update-and-recovery
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.release-lifecycle
disciplines: [security, sre]
kind: workflow
purpose: Route a change to an existing accepted deployment scope through update, verification, acceptance, or bounded restoration.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.standards.accepted-release-and-recovery
  path: .agentic/04.deploy/standards/accepted-release-and-recovery.md
-->
# Release Update and Recovery

Use this workflow when a selected target already has an accepted healthy
release. It does not grant cloud authority; the provider-specific workflow
owns inspection and mutation permissions.

1. Confirm declaration coverage and build/package qualification.
2. Load the accepted-release record and run the scope's connected release-contract check.
3. Run fresh update alignment. It must prove the live workload matches the
   retained accepted baseline before a new candidate is proposed.
4. Create and review a bounded UPDATE change set. Do not execute it yet.
5. Under explicit provider authority, deploy the candidate and run private
   verification of its source revision and immutable digest.
6. Only after that proof, record the candidate as the new accepted release.
7. If candidate verification is rejected, retain the existing record. Prepare
   or, under explicit authority, execute restoration to its retained digest and
   privately verify restoration.

Stop when the accepted record, package receipt, alignment, release-contract
gate, reviewed change set, provider authority, or verification proof is absent
or mismatched. Do not discover a substitute procedure in a historical plan.
