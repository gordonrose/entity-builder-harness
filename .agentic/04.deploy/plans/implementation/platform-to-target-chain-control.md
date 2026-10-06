<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.implementation.platform-to-target-chain-control
version: 3
status: draft
layer: 04.deploy
domain: deployment.governance
disciplines:
- agentic
- architecture
- security
- sre
kind: implementation-plan
purpose: Plan a governed, checkable chain from platform modules through runnable programs, packages, and deployment targets.
portability:
  class: source-only
  targets: []
used_by:
- id: product.workflow.platform-runtime-implementation
  path: .agentic/03.product/workflows/platform-runtime-implementation.md
- id: deploy.standards.declaration-coverage
  path: .agentic/04.deploy/standards/declaration-coverage.md
- id: deploy.standards.target-alignment-preflight
  path: .agentic/04.deploy/standards/target-alignment-preflight.md
-->
# Platform-to-Target Chain Control Plan

## Status and Intent

This is a review plan, not permission to implement, move, deploy, or inspect a
cloud target. Each phase requires separate approval after its detailed design
has been reviewed.

The goal is to make the following relationship explicit and mechanically
checkable:

```text
platform capability
  -> provider adapter, if one is selected
  -> runnable program
  -> container image command
  -> target workload
  -> expected configuration, permissions, dependencies, and proof
  -> Target Alignment comparison
  -> current target configuration and facts
  -> aligned / mismatch / insufficient evidence
```

The chain through the expected configuration establishes what the repository
requires. Target Alignment is a separate comparison step: it safely compares
those declared expectations with the actual target. It runs early enough to
identify an unsuitable target before implementation work, and again immediately
before deployment because the target may have changed since the earlier check.

The initial vertical slice is the existing Kanbien Platform public server only.
Workers, relay, PostgreSQL Stage 6, identity provisioning, ingress, and
observability delivery remain out of scope until this slice is proven. This
preserves the existing PostgreSQL controls and avoids a broad reorganisation.

## Starting Evidence

The plan extends rather than replaces these existing controls:

- `.agentic/03.product/workflows/platform-runtime-implementation.md` governs
  platform runtime changes and their local checks.
- `.agentic/04.deploy/standards/declaration-coverage.md` defines the required
  declaration and proof chain for bounded deploy requirements.
- `infra/04.deploy/03.product/targets/kanbien/staging/declaration-contract.yml`
  is the initial, deliberately limited server-baseline contract.
- `scripts/04.deploy/inventory-deploy-control/` provides a read-only census of
  the current deploy surface.
- Existing TypeScript configurations, Dockerfile, image-payload checks,
  CloudFormation, and target profiles remain the current factual evidence.

## Source-of-Truth Model

The repository must distinguish an instruction from an explanation and from
the thing being controlled. No layer may become a competing silent authority.

| Need | Canonical home | Role of the other artifacts |
| --- | --- | --- |
| What a source file, image, or target definition actually does | TypeScript, package configuration, Dockerfile, CloudFormation, target declarations, and executable scripts | Governance and docs describe and validate these facts; they do not duplicate them as independent facts. |
| What an agent must do, when it must stop, and what evidence is required | `.agentic/<owner-layer>/` workflow, standard, schema, checklist, or gate | READMEs and docs link to the governing artifact; they cannot introduce an unreferenced mandatory agent rule. |
| Why a design exists and how a human understands it | `docs/<owner-layer>/` and local README files | Agentic workflows may cite these as required reading or source material. They explain, justify, and orient; they do not override governance. |
| What can be checked deterministically | `scripts/<owner-layer>/` | The owning agentic workflow or gate states when the script is required and how a failure is handled. |

This means documentation and READMEs are inputs to, and human-readable
projections of, agentic governance—not competitors to it. When a README says a
process is required, it must link to the owning `.agentic` artifact. When an
agentic workflow relies on architectural explanation, it must link to the
owned README or documentation source. Contradictions are a governance defect:
the agent must stop and resolve the conflict rather than choose silently.

## Principles

- Derive facts from existing source and configuration where possible; do not
  create a second hand-maintained copy merely to satisfy the harness.
- Add a declaration only where a relationship cannot be reliably derived, such
  as the intended workload role or its required proof.
- Keep one authoritative declaration for each fact.
- Start report-only. A check becomes blocking only after existing gaps are
  understood and corrected.
- Assign each control to one lifecycle stage under
  `.agentic/04.deploy/lifecycle/`; do not duplicate checks across stages.
- Do not move existing AWS or PostgreSQL artifacts as part of this plan.
- Keep provider-neutral governance in `.agentic/04.deploy/`; retain AWS
  execution authority in `.agentic/aws/` until the existing migration plan
  explicitly changes that boundary.

## Delivery Phases

### Phase 0 — Baseline the current chain

**Question answered:** What does the repository currently claim and execute?

Create a read-only evidence map for the public server that identifies:

- the platform modules and product composition it uses;
- provider adapters selected by its target-specific composition;
- which `entrypoints/` files are runnable programs and which are helpers;
- image build inputs, compiled output, default command, payload verifier, and
  local image smoke proof;
- staging workload command, configuration names, health policy, permissions,
  dependencies, immutable-image rule, and rollback declaration;
- missing, duplicated, contradictory, and currently unproved links.

**Deliverable:** a current-state report with source paths and no new runtime or
target declarations.

**Exit criterion:** every statement in the report points to existing
repository evidence; unknowns are labelled as unknown rather than inferred.

### Phase 1 — Establish documentation and governance linkage

**Question answered:** Which artifact is allowed to instruct an agent, and
which artifact merely explains the system?

Extend the harness placement/authoring rules with a small, enforceable
documentation-linkage standard. It will define:

- required links from module and deploy READMEs to their governing workflow or
  standard;
- required links from agentic workflows to the human explanation necessary to
  apply them safely;
- a conflict rule: agentic governance, executable contract, and documentation
  must be reconciled before a change is considered complete;
- a deliberately limited checker that detects missing links, not the truth of
  prose.

**Deliverable:** one cross-layer standard and an initially report-only check.

**Exit criterion:** the public-server chain has a clear map from each README
and document to its governance owner or has a recorded gap.

### Phase 2 — Define the platform-module contract

**Question answered:** What evidence makes a platform module safe to change?

Build on the existing platform-runtime workflow. The module contract must
require evidence for:

- a supported public boundary such as `index.ts`;
- ownership, non-ownership, and dependency-direction rules;
- type check, build, runtime test, and boundary test when applicable;
- a module README and source map that explain the module to a human;
- a recorded reason when a normal proof is not applicable.

The checker must derive the build and test facts from `package.json`,
`tsconfig*`, and test locations. It must not introduce a duplicate module
manifest for information already held there.

**Deliverable:** a report-only product-layer module-contract check, first
applied to the modules used by the public-server chain.

**Exit criterion:** the checker identifies whether each selected module has a
public boundary, declared ownership, expected proofs, and an explanation.

### Phase 3 — Declare runnable programs

**Question answered:** Which files can a package or target start as processes?

Add one small registry beside `infra/04.deploy/03.product/entrypoints/`. It
lists runnable programs only, not shared helpers. Each record must identify:

- stable program identifier;
- source file;
- role: HTTP server, long-running worker, or one-pass task;
- selected product composition and provider adapters;
- expected compiled command;
- required local proof; and
- owner.

The registry is necessary because role, intended command, and proof cannot be
reliably inferred from a TypeScript filename alone.

**Deliverable:** an entrypoint schema, field guide, registry, and static
reporter for the existing public server only.

**Exit criterion:** the reporter proves that the registered server source file
exists, is included in the image compilation input, has an expected compiled
command, and has a named local proof.

### Phase 4 — Declare the image contract

**Question answered:** What must the package contain and how may it start?

Add an image contract beside the Dockerfile. It declares only facts that cannot
be safely inferred from the Dockerfile and TypeScript image configuration:

- supported runnable-program records;
- default program;
- runtime assumptions such as user, port, health boundary, and immutable
  image identity requirement;
- package-level verification command.

The checker compares the contract with the Dockerfile,
`platform/server/tsconfig.image.json`, runtime-payload verifier, and image
smoke test.

**Deliverable:** a report that identifies programs declared but absent from the
payload, payload programs lacking proof, and an invalid default command.

**Exit criterion:** the public server’s source, compiled output, Docker
default command, and package smoke proof agree.

### Phase 5 — Bind programs to target workloads

**Question answered:** Which target workload runs which approved program?

Add a target-local workload binding beside the staging target profile. A
binding refers to a runnable-program identifier and names:

- the target workload/service or one-pass task;
- selected image contract;
- configuration/declaration-contract scope;
- health and rollback proofs; and
- target owner.

AWS-specific command details remain in the existing CloudFormation source. The
binding is provider-neutral and the checker compares it to the provider
definition; it does not replace that definition.

**Deliverable:** a public-server workload binding and static comparison with
the existing task/service definition.

**Exit criterion:** no workload selects an unknown command; no declared
runnable program is presented as deployed without an explicit binding.

### Phase 6 — Assemble a repository-only chain checker

**Question answered:** Is the declared source-to-target chain internally
complete before cloud inspection?

Create one read-only `scripts/04.deploy/` capability. For a selected program
and target, it traces:

```text
platform/module evidence
-> adapter selection
-> runnable-program record
-> image contract and compiled command
-> target workload binding
-> declaration-contract requirements and proofs
```

Possible results are `complete`, `missing-declaration`,
`declared-but-not-implemented`, `implemented-but-unproved`, and
`explicitly-out-of-scope`.

**Deliverable:** human-readable and machine-readable report modes, fixtures,
and a smoke test. It remains repository-only and makes no AWS call.

**Exit criterion:** the public-server chain is reported consistently from the
same authoritative declarations and existing factual evidence.

### Phase 7 — Connect to target alignment preflight

**Question answered:** Does the current target meet the already-complete
repository declaration?

Extend the existing Target Alignment Preflight only after Phase 6 is stable.
The preflight consumes the chain-check result and safely confirms live facts:

- destination identity and selected workload;
- image identity and approved deployment route;
- non-secret configuration and secret-name presence;
- permissions, dependencies, health, and rollback configuration;
- freshness and drift.

It has two required use points with the same comparison contract:

1. **Early alignment:** compare a fresh target snapshot with the selected
   repository declaration before implementation is considered target-ready.
   A still-valid cached result may be used only within its declared expiry.
2. **Pre-deploy refresh:** re-run the comparison immediately before target
   mutation so a changed account, workload, permission, setting, dependency,
   health policy, or rollback route cannot be hidden by an old result.

No secret values may be read or reported. The future AWS read adapter remains
subject to the existing AWS workflow and approval boundary.

**Deliverable:** a provider-neutral input/output contract and an AWS read-only
adapter design; no target mutation.

**Exit criterion:** the preflight can distinguish a repository coverage gap
from a live-target mismatch.

### Phase 8 — Stage enforcement and broaden scope

<!-- deterministic-check: allow reason="The enforcement threshold is a phased human risk decision until the reviewed report-only controls exist and can become gates." -->
**Question answered:** When should a missing link block work?

Adopt controls in order:

1. report-only for the public server;
2. required on changes to its entrypoint, image, target, or deployment
   declaration;
3. required before packaging, with a fresh target-alignment refresh required
   before deployment;
4. repeated for worker, relay, and then PostgreSQL only under separately
   approved scopes.

**Deliverable:** lifecycle-stage gate references and change-scope routing.

**Exit criterion:** a relevant change cannot be treated as deploy-ready with a
missing source-to-target link, while unrelated platform changes do not trigger
provider checks.

## Decisions Required Before Implementation

1. Confirm the public server is the correct first vertical slice.
<!-- deterministic-check: allow reason="Whether a registry is warranted depends on human assessment of which deployment facts cannot safely be derived from source code." -->
2. Confirm that a machine-readable runnable-program registry is acceptable
   when role and proof cannot be derived from code.
3. Choose whether the Phase 1 documentation-linkage rule belongs in the
   existing harness placement standard or in a new cross-layer standard.
4. Agree the threshold at which report-only checks become blocking gates.
5. Review the Phase 0 evidence map before creating any new declarations.

## Safety Boundaries

- Do not move or delete files in the initial slice.
- Do not change AWS resources, CloudFormation, GitHub deployment settings, or
  secrets while establishing repository-only controls.
- Do not modify PostgreSQL Stage 6 implementation, target state, or existing
  controllers without a separately approved scope.
- Do not treat a green static checker as proof of a live deployment; package,
  target-alignment, and run-stage proofs remain distinct.
- Record unresolved contradictions as gaps rather than resolving them through
  undocumented assumptions.

## Definition of Success

For the public server, a reviewer can start with one program identifier and
find, by command and source path, its platform inputs, adapter choice, compiled
image command, staging workload, required non-secret configuration, permission
and dependency declarations, local/package proofs, target-alignment result,
and target/run proofs. Any missing or contradictory link is reported before a
deployment is treated as ready.
