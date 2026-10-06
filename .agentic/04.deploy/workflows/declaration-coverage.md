<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.workflow.declaration-coverage
version: 2
status: draft
layer: 04.deploy
domain: deployment.declaration-coverage
disciplines:
- agentic
- architecture
- security
- sre
kind: workflow
purpose: Govern declaration coverage for a bounded deployable scope before target alignment or implementation.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.standards.declaration-coverage
  path: .agentic/04.deploy/standards/declaration-coverage.md
- id: deploy.script.declaration-coverage.readme
  path: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/README.md
-->
# Declaration Coverage

## Use When

Use this workflow after task framing and before implementation when work could
change a deployable artifact, runtime behavior, target configuration,
dependency, or release safety property.

## Required Inputs

- proposed work and selected bounded capability scope;
- selected target profile or an explicit non-deployable classification;
- declaration contract for that scope; and
- source paths and proof commands named by the contract.

## Procedure

1. Select the smallest capability scope affected by the work. Name every known
   excluded dependency rather than implying that it is covered.
2. Identify requirements from the changed code, package/runtime definition,
   configuration shape, infrastructure definitions, and release controls.
3. For each requirement, create or update a declaration-contract entry with
   the complete chain required by the Declaration Coverage Standard.
<!-- deterministic-check: allow reason="A future declaration-contract checker can verify referenced paths and commands; until it exists, a reviewer must assess the selected scope and expectation meaning." -->
4. Confirm that all referenced local declarations and proof commands exist and
   that the expected value or shape is non-secret and unambiguous.
5. Report `covered` only when every in-scope requirement has a complete chain.
   Otherwise report `gap` with the missing chain element and stop before Target
   Alignment or implementation.
6. Pass the covered declaration contract to Target Alignment Preflight. It is
   the sole source of assertions for the selected scope.

## Stop Conditions

Stop when the scope is unclear, a requirement has no owner, a required source
declaration or proof is missing, a target proof would require an unsafe query,
or the contract attempts to cover an undeclared dependency.

## Output

Produce a safe `covered`, `gap`, or `not-applicable` result with the contract
reference, source revision, requirement IDs, excluded dependencies, and any
missing chain elements. This workflow performs no provider read or mutation.
