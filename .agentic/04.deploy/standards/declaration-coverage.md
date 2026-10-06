<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.standards.declaration-coverage
version: 1
status: draft
layer: 04.deploy
domain: deployment.declaration-coverage
disciplines:
- agentic
- architecture
- security
- sre
kind: standard
purpose: Define how deployable requirements are declared, traced, and proved before target alignment.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.workflow.declaration-coverage
  path: .agentic/04.deploy/workflows/declaration-coverage.md
- id: deploy.workflow.target-alignment-preflight
  path: .agentic/04.deploy/workflows/target-alignment-preflight.md
- id: deploy.schema.declaration-contract.v1
  path: .agentic/04.deploy/schemas/declaration-contract.v1.schema.yml
-->
# Declaration Coverage Standard

## Purpose

Declaration Coverage answers whether every requirement in a selected,
explicitly bounded deployment scope has a declared local representation and a
complete proof path. It runs before Target Alignment Preflight. It does not
inspect a provider or authorize a target mutation.

## Requirement Chain

Each requirement in scope must name all of the following:

1. what is required and why;
2. the code, package, runtime, or operational capability that requires it;
3. the local source declaration that provides it;
4. the expected non-secret value or allowed shape;
5. a local proof that the declaration is internally consistent;
6. a target proof that can confirm the declared requirement safely;
7. a package or live proof when the requirement needs one; and
8. an accountable owner.

Missing, ambiguous, unowned, or unproved requirements are coverage gaps. A
scope is complete only when every in-scope requirement has this chain and every
out-of-scope dependency is named explicitly. A declaration contract must not
claim coverage for PostgreSQL, queues, workers, identity, ingress, or another
dependency merely because it names a general platform service.

## Boundaries

The declaration contract records requirement identities, source paths,
non-secret expected values or shapes, and proof references. It must not record
secret values, tokens, raw provider responses, customer data, or a copy of an
entire provider target profile.

Declaration Coverage proves that the repository has accounted for a
requirement. Target Alignment Preflight separately proves that the selected
target currently satisfies it. Package and Run phases separately prove that the
assembled artifact and deployed application behave correctly.

## Change Rule

When a change introduces or alters a runtime setting, dependency, image input,
identity, network path, persistence need, queue, rollback requirement, or
operational signal, update the affected declaration contract before treating
the work as covered. Existing contracts may be extended only within their
declared scope; a new capability or dependency requires a new bounded scope.
