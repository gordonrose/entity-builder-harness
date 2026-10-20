<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.delivery-access-coverage
version: 1
status: draft
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 04.deploy
domain: deployment.delivery-access
disciplines:
- agentic
- security
- sre
kind: standard
purpose: Require an executable, least-privilege link between a delivery pipeline's declared provider operations and its actual provider policy.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.schema.delivery-access-contract.v1
  path: .agentic/04.deploy/schemas/delivery-access-contract.v1.schema.yml
-->
# Delivery Access Coverage

A delivery pipeline must declare every provider operation it needs before it is
trusted to publish a package or mutate a target. Its declaration is not an IAM
policy: the provider template remains the authority for actual permissions.

## Required chain

For every delivery operation, the contract names the pipeline, workflow step,
provider action, bounded resource class, purpose, and proof. A deterministic
repository check proves that every declared action is granted by the named
provider policy and that every policy action is justified by the contract or an
explicitly documented provider bootstrap requirement.

Before a publication or deployment workflow performs a consequential action,
it must run its named safe live access probes. A probe is read-only or uses an
intentionally nonexistent identifier. `AccessDenied` is failure; an expected
not-found response may prove authorisation, but never resource readiness.

The reusable validator accepts only a delivery contract, workflow, and
normalized provider-policy coverage. Provider-specific policy parsing and live
probes live in an adapter. A target wrapper supplies the fixed contract,
provider policy source, and package destination; it must reject arbitrary
target or destination substitution.

## Boundaries

- Do not copy an AWS policy into a generic contract.
- Do not infer permission from a successful earlier workflow run.
- Do not use broad wildcards to make a coverage check pass.
- A missing, denied, ambiguous, or stale access proof blocks the affected
  operation with a safe diagnostic.
- The contract must not contain credentials, account identifiers, endpoints,
  secret values, or raw provider responses.
