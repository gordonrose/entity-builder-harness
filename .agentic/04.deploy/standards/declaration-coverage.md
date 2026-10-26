<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.declaration-coverage
version: 2
status: active
created_on: "2026-10-06"
updated_on: "2026-10-26"
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
  path: .agentic/04.deploy/00-target-alignment/workflows/compare-declared-requirements-with-live-target.md
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

## Executable scope coverage

For supported `deploy/target-scope-contract/v1` declarations, the additive
[change impact contract](../schemas/change-impact.v1.guide.md) connects each
requirement to affected inputs and catalogued proof checks. The existing
scope-health, secret and diagnostic validators retain ownership of their
constraints. The declaration-coverage command validates the chain, and the
repository selector discovers consumers without granting the selected checks'
effects. Unsupported requirements and uncovered impact are explicit gaps.
Valid non-applicability remains distinct from absent declarations or proof.

The [shared standard](../../shared/standards/require-change-completion.md)
owns completion principles; [deployment realization](operational-realization-gate.md)
owns proof semantics and stage order. Required later-stage evidence remains
blocking even when local coverage passes.

## Executable workload delivery

The existing workload binding owns `runtime_requirements`: one record per
workload, its required configuration names, exec command, secret injection
names, identity requirement and optional capability selectors. Each workload must bind
its exact nonempty command. An inline command may instead bind `command_sha256`
to the UTF-8 SHA-256 of its compact JSON argument array, preserving the provider
template as the only command source. Omitting both bindings is a gap. Required scope
names must map to at least one workload. Image defaults may satisfy ordinary
configuration; they never satisfy secret injection. Optional capability
requirements apply only to variants enabling their selector.

`proposed_provider_binding.configuration_adapter` references a repository
adapter under `scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/`.
It normalizes provider templates without target reads. The neutral checker
compares every normalized alternative with workload requirements; provider
permission names and conditional syntax remain in the adapter and binding.
Dynamic task inputs bind `source`, a `command` ID from the existing acceptance
route, and a
`proof` check ID. The producer command must be a declared consumer; its selected
local-runtime proof must fingerprint the producer source. The route binds the
selected workload/configuration names to the actual command parser
`runtime_input_contract`, including its requirement to observe delivered values.
The command arguments are validated by the existing acceptance-route checker. File existence alone
does not satisfy a required input. The controller still verifies delivered task
overrides before recording acceptance; a static presence result does not prove a live override or permission.

Declaration coverage invokes this comparison before image construction. The
repository delivery inventory independently discovers unregistered entrypoints,
and supported builders and publication workflows run that inventory before
expensive work. New scopes inherit the same checks through their declarations.


## Discovery and automatic enforcement

Declared consequential effects override filename-based fixture heuristics.
Public package wrappers and aliases inherit the delivery requirement of each
resolved implementation. Missing registration or an unsupported executable
relationship is a coverage gap; a registered neighboring command is not a
substitute. The inventory owns bounded supported syntax and emits explicit
unsupported relationships instead of evaluating arbitrary shell code.

Automatic delivery CI must cover the declared delivery inputs and normal pull
request updates. The current executable contract permits unrestricted pull
requests only; restrictive path, branch or event filters require an explicitly
governed coverage proof before the validator can accept them.
