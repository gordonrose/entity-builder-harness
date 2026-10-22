<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.workflow.target-alignment-preflight
version: 3
status: active
created_on: "2026-10-06"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.target-alignment
disciplines:
- agentic
- security
- sre
kind: workflow
purpose: Govern safe target discovery and alignment before deployable implementation and before target mutation.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.standards.target-alignment-preflight
  path: .agentic/04.deploy/00-target-alignment/standards/require-fresh-safe-target-evidence.md
- id: deploy.plan.migration.aws-provider-neutral-transition
  path: .agentic/04.deploy/plans/migration/aws-provider-neutral-transition.md
-->
# Compare Declared Requirements With Live Target

## Use When

Use this workflow after task framing and before implementation when the work
could produce a deployable artifact, change deployable runtime behavior, or
alter target configuration, dependencies, or release safety.

Run it again immediately before a target mutation. Do not use it for a task
explicitly classified as non-deployable; record that classification instead.

## Required Inputs

- the proposed work and source revision;
- selected target profile or a documented reason that no target applies;
- a `covered` Declaration Coverage result and its bounded declaration contract;
- declared local runtime, package, configuration-reference, and release-route
  requirements;
- an explicit secret-dependency declaration, including only safe reference and
  expected-field facts when a workload receives secret material;
- allowed evidence age and drift policy; and
- a provider adapter with a named read-only inspection authority.

## Procedure

1. Require a `covered` Declaration Coverage result. If it reports a gap, stop
   before target inspection or implementation.
2. Select the first intended target. If the work is deployable and no target is
   selected, stop before implementation.
3. Derive assertions only from the covered declaration contract and the
   dependencies affected by the proposed work.
4. Validate the local declarations, including any secret-dependency contract,
   and record the source revision they describe.
5. Invoke the provider adapter's bounded read-only inspection. The generic
   workflow does not itself call a provider or grant provider authority.
6. Compare every required assertion. Treat a mismatch, missing fact, unknown
   fact, stale evidence, or output-policy breach as a failed preflight.
7. Record the safe result and evidence reference. A pass permits implementation
   to begin; it does not authorize publication, deployment, or another target
   mutation.
8. Before a target mutation, repeat the affected local and target assertions.
   Follow the provider-specific execution workflow for any mutation.

## Stop Conditions

<!-- deterministic-check: allow reason="Whether a missing or unsafe target fact stops the work depends on the selected scope, provider authority, and safe normalization judgment until a provider adapter exists." -->
Stop when the target is missing for deployable work, an adapter is unavailable,
an assertion is unknown or stale, a required comparison fails, a dependency is
undeclared, a provider response cannot be normalized safely, or a proposed
operation would mutate the target.

## AWS Route

AWS inspection remains governed by the existing inspection workflow when its
required account/profile, region, and target inputs are known:

```text
.agentic/aws/workflows/inspect-aws-state.md
```

That workflow remains the authority for read-only AWS inspection. The first
AWS adapter may normalize the bounded first-release runtime facts only; it
accepts no arbitrary provider query and has no mutation authority. This
provider-neutral workflow adds no permission and does not authorize a live AWS
call by itself.

## Output

Produce one safe verdict: `aligned`, `not-aligned`, `not-applicable`, or
`blocked`. Include the selected target, assertion IDs and outcomes, source
revision, evidence freshness, and the next permitted action. Do not include
secrets, raw provider data, customer data, endpoints, or credential material.
