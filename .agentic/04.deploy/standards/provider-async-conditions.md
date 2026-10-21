<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.provider-async-conditions
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.target-alignment
disciplines:
- agentic
- security
- sre
kind: standard
purpose: Model provider-controlled propagation and asynchronous conditions without treating a request as proof of readiness.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: infra.04-deploy.03-product.targets.kanbien-core-platform.foundation.cost-control
  path: infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/cost-control.yml
-->
# Provider Asynchronous Conditions

Provider-controlled states such as tag discovery, cost-allocation activation,
image scanning, DNS propagation, and stack completion are not complete when a
request has been accepted. They require separately fresh evidence.

Each condition must declare its owner, required evidence, status, next safe
recheck, expiry, and whether an explicitly approved temporary waiver exists.
Allowed statuses are `not-requested`, `requested`, `waiting-on-provider`,
`verified`, `expired`, and `waived-by-approved-exception`.

Condition evidence is validated by the provider-neutral
`validate-provider-condition-evidence` command before any workflow treats a
condition as verified or waived. A provider adapter may collect the fact, but
the validator receives only the safe evidence record.

A waiver is narrow: it names the waived condition, authority, reason, expiry,
compensating controls, and required follow-up. It does not waive unrelated
security, access, cost, or target-alignment conditions.
