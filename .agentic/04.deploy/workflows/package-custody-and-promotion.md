<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.package-custody-and-promotion
version: 1
status: draft
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
    path: .agentic/04.deploy/standards/package-custody-and-promotion.md
  - id: deploy.schema.package-custody-receipt.v1
    path: .agentic/04.deploy/schemas/package-custody-receipt.v1.schema.yml
created_on: "2026-10-20"
updated_on: "2026-10-20"
-->
# Package Custody and Promotion Workflow

## Use when

Use this workflow when a repository adds or changes the controlled route that
publishes an immutable package or records package evidence.

## Procedure

1. Name the package contract, candidate, destination, permitted source ref,
   publisher identity, and required qualification proofs.
2. Confirm the publisher can write only the declared destination and cannot
   mutate a workload through this route.
3. Build and qualify the package before it is published. Bind the publication
   result to an immutable digest.
4. Require scan, SBOM, and provenance results before a qualified receipt is
   emitted.
5. Validate the receipt against the safe receipt contract and retain it as the
   delivery system's evidence artifact and summary.
6. Link a target's pipeline catalogue record to the executable workflow and
   receipt contract. Do not use that record as deployment authority.

## Stop conditions

Stop if the source ref, publisher identity, destination, digest, receipt, or a
required qualification proof is missing or mismatched. Stop if a publication
workflow can mutate a workload, use an unreviewed target selector, or emit
sensitive evidence.
