<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.package-custody-and-promotion
version: 1
status: draft
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
  - agentic
  - architecture
  - security
  - sre
kind: standard
purpose: Define the safe evidence and authority boundary between qualifying, publishing, and promoting an immutable package.
portability:
  class: reusable
  targets:
    - entity-builder
used_by:
  - id: deploy.workflow.package-custody-and-promotion
    path: .agentic/04.deploy/workflows/package-custody-and-promotion.md
  - id: deploy.schema.package-custody-receipt.v1
    path: .agentic/04.deploy/schemas/package-custody-receipt.v1.schema.yml
created_on: "2026-10-20"
updated_on: "2026-10-20"
-->
# Package Custody and Promotion

Package qualification, publication, and target promotion are separate
decisions. A qualified image may be stored by immutable digest without being
authorised for any workload. A later target-bound deployment control alone may
select that digest.

## Package custody requirements

A publication route must:

<!-- deterministic-check: allow reason="the target-bound workflow verifier enforces the executable publication sequence; this standard states the portable policy." -->
1. accept only an approved source revision and runnable-program/image contract;
2. run the named local qualification and package checks before publication;
3. publish an immutable digest to the declared package destination;
4. fail closed if a required scan, SBOM, provenance attestation, or digest
   binding is absent or rejected; and
5. write only a receipt conforming to the safe receipt schema.

The receipt may contain stable identifiers, source revision, digest, bounded
check verdicts, timestamp, and a non-secret run reference. It must not contain
credentials, secret values, headers, request bodies, personal data, full
provider locations, raw provider responses, or vulnerability details.

## Authority boundary

A package-publication workflow may build, scan, attest, publish, and retain
safe evidence. It must not create, update, select, restart, roll back, or
verify a workload. Those actions remain target-bound deploy or run controls.

If an image is published but a later qualification proof fails, the receipt is
rejected and the workflow stops. It must not delete the immutable image or
start a compensating deployment automatically.
