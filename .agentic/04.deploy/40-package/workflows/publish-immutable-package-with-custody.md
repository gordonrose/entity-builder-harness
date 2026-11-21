<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.package-custody-and-promotion
version: 4
status: active
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
  - agentic
  - architecture
  - security
  - sre
kind: workflow
purpose: Govern a package-custody change without granting target-promotion authority.
portability:
  class: reusable
  targets:
    - entity-builder
used_by:
  - id: deploy.standards.package-custody-and-promotion
    path: .agentic/04.deploy/40-package/standards/require-immutable-package-custody.md
  - id: deploy.schema.package-custody-receipt.v1
    path: .agentic/04.deploy/40-package/schemas/package-custody-receipt.v1.schema.yml
created_on: "2026-10-20"
updated_on: "2026-11-19"
-->
# Publish Immutable Package With Custody

Follow the [shared change-completion principles](../../../shared/standards/require-change-completion.md) for consumer impact, selected verification, continuation and evidence reporting.
The [deployment proof standard](../../standards/operational-realization-gate.md) owns cross-phase proof requirements; this workflow applies its stage-specific controls.

## Use when

Use this workflow when a repository adds or changes the controlled route that
publishes an immutable package or records package evidence.

## Procedure

Use the recorded [end-to-end delivery authority](../../standards/operational-realization-gate.md#end-to-end-live-delivery-authority)
when publication is part of that request. Do not ask separately to publish its
qualified package; package-only approval still grants no workload mutation.

1. Name the package contract, candidate, destination, permitted source ref,
   publisher identity, and required qualification proofs.
2. Confirm the publisher can write only the declared destination and cannot
   mutate a workload through this route.
3. Build and qualify the package before it is published. Bind the publication
   result to an immutable digest.
   For workspace-backed runnable programs, consume the validated contract and
   observed dependency report from the existing
   [build workflow](../../20-build/workflows/prove-runnable-program-builds.md).
   Use the selected program's shared declaration-derived compiler and runtime
   preparer; package manifests own public exports and dependencies, while the
   program declaration owns its approved build boundary. Keep non-derivable
   assets explicit at their existing owner, not in a copied alias/shim map.
   <!-- deterministic-check: allow reason="the existing selector and package qualification owners execute these checks; this workflow states their evidence boundary rather than introducing another dispatcher" -->
   Run the affected existing payload and actual image qualification checks;
   declaration validation or local compilation alone is not package proof.
4. Require scan, SBOM, and provenance results before a qualified receipt is
   emitted.
5. Validate the receipt against the safe receipt contract and retain it as the
   delivery system's evidence artifact and summary.
6. Link a target's pipeline catalogue record to the executable workflow and
   receipt contract. Do not use that record as deployment authority.
7. When package qualification or publication fails, retain a separate safe
   deployment-operation diagnostic in the delivery system. It preserves the
   failed operation and bounded next action without becoming a qualified
   package receipt or exposing raw command/provider output.

## Stop conditions

Stop if the source ref, publisher identity, destination, digest, receipt, or a
required qualification proof is missing or mismatched. Stop if a publication
workflow can mutate a workload, use an unreviewed target selector, or emit
sensitive evidence.
