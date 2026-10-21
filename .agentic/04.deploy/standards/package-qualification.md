<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.package-qualification
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
- agentic
- security
- sre
kind: standard
purpose: Require a candidate image, its selected runtime base, and its publication evidence to pass distinct qualification gates before target use.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.standards.package-custody-and-promotion
  path: .agentic/04.deploy/40-package/standards/require-immutable-package-custody.md
-->
# Package Qualification

Package qualification is earlier and narrower than target deployment. It
proves that a selected runtime base and assembled candidate meet the declared
policy before a workload may select the resulting digest.

## Required order

1. Select an immutable runtime base and record its source and digest in the
   image contract.
2. Build the candidate and run its local package checks, including a real
   container smoke where an engine is available.
3. Publish only to the declared immutable package destination.
4. Independently scan the published digest, generate required SBOM/provenance
   evidence, and reject blocked severities.
5. Write a safe package-custody receipt only when every required check passed.

A target foundation may be prepared only to the minimum extent needed to host
the approved package destination. A workload foundation or workload deployment
must not proceed until package qualification has an accepted receipt.

## Failure rule

A rejected image is evidence, not an invitation to lower the policy. The
workflow retains the immutable rejected digest for investigation where the
package destination allows it, writes no qualified receipt, and never deploys,
deletes, or replaces a workload automatically.
