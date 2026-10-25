<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.declaration-coverage
version: 3
status: active
created_on: "2026-10-06"
updated_on: "2026-10-25"
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

Follow [shared change completion](../../shared/standards/require-change-completion.md)
and the [deployment proof authority](../standards/operational-realization-gate.md).
The [change impact guide](../schemas/change-impact.v1.guide.md) defines the
supported bridge from a scope declaration to consumers and check references.

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
   When a workload needs injected secret material, also follow
   `00-target-alignment/workflows/declare-secret-dependency.md`; record an
   explicit empty secret-dependency list when it does not.
4. Validate the supported scope contract and its additive `change_impact`
   requirements using `scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh --scope-contract <path> --json`.
   Use `scripts/repo/check-selection/script.sh --paths <changed-paths> --json`
   to discover affected consumers and required existing checks. The check
   catalog owns fixed commands, effects, stages and evidence classes. Coverage
   validates the requirement chain; it does not execute proof commands or grant
   provider operations. Select package, deploy and acceptance stages separately;
   their required proof cannot be replaced by local results.
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
