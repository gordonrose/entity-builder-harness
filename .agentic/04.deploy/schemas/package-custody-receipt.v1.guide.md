<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.package-custody-receipt.v1.guide
version: 1
status: draft
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
  - agentic
  - architecture
  - security
  - sre
kind: guide
purpose: Explain the safe fields and use of a package-custody receipt.
portability:
  class: reusable
  targets:
    - entity-builder
used_by:
  - id: deploy.schema.package-custody-receipt.v1
    path: .agentic/04.deploy/schemas/package-custody-receipt.v1.schema.yml
created_on: "2026-10-20"
updated_on: "2026-10-20"
-->
# Package Custody Receipt v1 Guide

A package-custody receipt answers a narrow question: did one approved source
revision become one qualified immutable package digest? It is not a deployment
receipt and must not claim a workload is running.

`target` identifies the approved package destination. `provider_region_alias`
is a safe label such as `aws-eu-west-1`, not an account number or endpoint.
`receipt_reference` is an opaque delivery-run identifier, not a URL. `checks`
contains only named pass/fail verdicts; detailed scanner output stays in the
delivery system and is not copied into repository evidence.

Target-bound callers supply their expected target, candidate, package contract,
and program when validating the receipt. A receipt that has a valid general
shape but names a different target is rejected.
