<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.implementation.platform-to-target-chain-control
version: 7
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

## Scope Model

A **scope** is a bounded deployable capability, not a repository layer and not
simply a platform module. It is the unit for which the repository can state
expected target requirements and later report an alignment result.

| Term | Meaning | Example |
| --- | --- | --- |
| Platform module | Reusable runtime building block. A module can be used by several deployable capabilities. | `platform/security` or `platform/observability` |
| Runnable program | A process that composes product, platform, and selected adapters. | `kanbien-platform-server.main.ts` |
| Deployment scope | The bounded capability and target workload whose requirements are declared and proved together. | `kanbien-staging-platform-server-baseline` |
| Target | The real destination in which one or more scopes run. | Kanbien staging in its selected AWS account and region |

For example, a change to `platform/security` may affect the public-server,
worker, and identity scopes. The change-impact process must identify all
affected scopes; it must not assume that a module name is itself the scope.

An alignment verdict is always scope-qualified. `aligned` means only
`aligned within the named declared scope`; it must list its covered concerns
and exclusions. A target is fully covered only when every active required scope
in its scope index has current, successful alignment evidence and no unresolved
common-foundation gap.

## Scope Records and Change Maintenance

The plan separates the authoritative facts needed to keep scopes current:

| Information | Canonical location | Update rule |
| --- | --- | --- |
| Scope names, state, owner, required dependencies, and declaration-contract path | Future target-local scope index under `infra/04.deploy/03.product/targets/<client>/<environment>/` | Add, retire, or change a scope in the same change set as its runnable program, workload, or requirement change. |
| Expected settings, secret names, permissions, dependencies, health, rollback, and proof paths | One bounded declaration contract per active scope in that target directory | Update whenever functionality adds, changes, or removes a runtime setting, dependency, image input, identity requirement, network path, persistence need, queue, rollback condition, or operational signal. |
| Generic field shapes and validation rules | `.agentic/04.deploy/schemas/` | Change through the provider-neutral deployment governance workflow, with a field guide and compatibility review. |
| When scope review is required | `.agentic/04.deploy/standards/` and workflows | A changed platform module, adapter, entrypoint, image, target definition, or deploy script must be mapped to affected scope records before completion. |
| Deterministic proof of current repository consistency | `scripts/04.deploy/` | The future chain checker fails for a missing, orphaned, stale, or contradictory scope link. |

The current `declaration-contract.yml` remains the first server-baseline
contract. The initial slice does not move it. When a second active scope is
introduced, the design review will introduce the target-local scope index and
per-scope contract directory through a compatible migration, rather than
silently relocating the current contract.

Adding functionality therefore requires its owning change to identify affected
scopes and update their contracts and proofs. Removing functionality requires
the reverse: remove its workload/program references, update or retire the
scope record, and prove that no target binding or requirement still refers to
it. The checker reports an unreviewed affected scope, an orphaned declaration,
or a target reference to a retired program as a failure.

## Scope Governance Artifact Set

Before the first scope is created, the harness must provide the following
owned artifacts. They teach an agent how to make the human scope decision and
then enforce the resulting structure; a README alone is not sufficient.

```text
.agentic/04.deploy/
  standards/deployment-scope.md
  workflows/change-deployment-scope.md
  schemas/deployment-scope.v1.schema.yml
  schemas/deployment-scope.v1.guide.md
  templates/deployment-scope/
  gates/check-deployment-scope.md

scripts/04.deploy/
  check-deployment-scope/
```

The standard defines when a new scope is required: a separate scope is needed
when a capability has a distinct runnable process, target prerequisites,
required proof, recovery behaviour, or lifecycle. Capabilities remain in one
scope only when those properties change together. The workflow requires an
agent to assess those criteria and name all affected existing scopes before
changing code or target definitions. The schema and template define the folder
shape and fields. The script and gate validate the facts that can be checked
deterministically.

The first target-local layout will be:

```text
infra/04.deploy/03.product/targets/kanbien/staging/
  scope-index.yml
  pipelines/
    github-actions/
      README.md
      pipeline-index.yml
  scopes/
    README.md
    platform-server/
      README.md
      declaration-contract.yml
      workload-binding.yml       # added when target binding is introduced
```

The scope README explains the capability, covered concerns, exclusions, and
evidence path for a human. It links to the owning `.agentic` workflow and
standard; it does not create independent agent instructions.

## Pipeline Catalogue

GitHub executes workflow files only from `.github/workflows/`; those files
remain the authoritative executable definition. The target-local
`pipelines/github-actions/` directory does not copy workflow steps. It records
how each executable pipeline fits the target's controlled delivery model.

Its `pipeline-index.yml` contains one record per pipeline with its stable ID,
type, executable workflow path, trigger, permitted source ref, approval,
AWS identity, effects, inputs, outputs, used-by scopes, and proof path. Types
initially include `package-publication`, `deployment`, `live-verification`, and
`drift-detection`.

For example, the existing platform-shell GitHub workflow is recorded as a
`package-publication` pipeline: it builds, tests, scans, attests, and publishes
an immutable image digest to ECR, but does not deploy it to ECS. The public
server scope references that pipeline as its approved package-publication
route.

The future pipeline checker verifies that a catalogue record points to an
existing workflow, its declared repository/role/source-ref facts agree with
the executable workflow and target declarations where those comparisons are
deterministic, and every scope requiring a package or live proof names an
approved pipeline. It must not duplicate GitHub workflow semantics or grant
execution authority.

The catalogue must also report operational state. The current scheduled
reconciliation pipeline is known to fail closed when fresh artifact-stack drift
evidence is absent. Its target profile deliberately prevents its GitHub role
from starting drift detection, while the required separate detector is marked
source-planned-not-deployed. This is a known shared verification gap, not proof
that the reconciliation workflow or artifact stack is broken.

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
- The scheduled staging reconciliation workflow provides current operational
  evidence: authentication, account identity, and artifact-stack status pass,
  while artifact-stack drift evidence is blocked because its separate evidence
  producer is not deployed.
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
- the package-publication pipeline, its approval/identity/repository route,
  immutable digest handoff, and custody/scan proof;
- the scheduled reconciliation pipeline, its stale-evidence failure mode, and
  the absent drift-evidence producer on which it depends;
- staging workload command, configuration names, health policy, permissions,
  dependencies, immutable-image rule, and rollback declaration;
- missing, duplicated, contradictory, and currently unproved links.

**Deliverable:** a current-state report with source paths and no new runtime or
target declarations.

**Exit criterion:** every statement in the report points to existing
repository evidence; unknowns are labelled as unknown rather than inferred.
The report also proposes the initial scope catalogue, clearly separating active
server coverage from excluded or not-yet-modelled capabilities.

### Phase 1 — Establish scope governance and the first scope

**Question answered:** How does an agent create, change, or retire a scope
consistently rather than relying on memory?

Create the Scope Governance Artifact Set above, with fixtures proving both a
valid public-server scope and common invalid cases: absent index record,
missing owner, missing exclusion list, unresolved declaration path, and a
retired scope still selected by a target binding.

Add the target-local pipeline catalogue and its first package-publication
record for `.github/workflows/deploy-platform-shell-staging.yml`. The record
must state that it publishes a tested, scanned, immutable image digest to the
approved ECR repository and does not deploy that digest. The public-server
scope must reference this record as its package-publication route.

Record the scheduled reconciliation workflow as a `drift-detection` pipeline
with state `blocked`, and record its planned separate artifact-stack
drift-evidence producer as the missing dependency. The catalogue must make
clear that the existing reconciler authenticates and reads safely but cannot
create the required fresh evidence itself.

Use that workflow and template to establish the first public-server scope. It
must introduce the target-local scope index, `scopes/README.md`, and the
public-server scope README. After Phase 0 has inventoried every reference to
the current root-level `declaration-contract.yml`, migrate that contract into
the scope folder in one compatible, reviewed change. Update every repository
reference; do not leave two authoritative copies. A compatibility pointer is
permitted only when a verified consumer requires it.

The initial scope record must name its active state, owner, covered concerns,
explicit exclusions, dependencies, contract path, and known proof paths. Its
workload binding is added in the later target-binding phase; the scope record
must say that this proof is pending rather than pretending it exists.

**Deliverable:** a report-only scope-and-pipeline checker, the governed first
`platform-server` scope, and its declared package-publication pipeline.

**Exit criterion:** a reviewer can follow the scope workflow, find the first
scope from the index, understand it from its README, validate its structure,
identify its approved package route, and distinguish its current coverage from
its pending target-binding work.

### Phase 2 — Establish documentation and governance linkage

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

### Phase 3 — Define the platform-module contract

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

### Phase 4 — Declare runnable programs

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

### Phase 5 — Declare the image contract

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

### Phase 6 — Bind programs to target workloads

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

### Phase 7 — Assemble a repository-only chain checker

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

### Phase 8 — Design and establish the drift-evidence producer

**Question answered:** How is fresh, safe drift evidence produced so that
scheduled reconciliation and future target alignment can distinguish a healthy
target from missing evidence?

Create a separate AWS-governed remediation design for the artifact-stack
drift-evidence producer. It must define its owner, trigger cadence, isolated
least-privilege identity, permitted drift-detection operations, safe evidence
record shape, expiry, retry behaviour, failure status, and how the existing
reconciliation pipeline consumes the result. It must start no application
workload, read no secret value, and mutate no application resource; starting
the AWS drift-detection assessment is the only target-facing operation under
its approved authority.

The design and any AWS execution remain governed by `.agentic/aws/`. This
provider-neutral plan records the dependency and its required evidence; it
does not authorize the role, detector, scheduler, or target change.

**Deliverable:** a reviewed AWS implementation plan, local validation for the
safe evidence shape, and a target-pipeline catalogue record linking producer
and consumer.

**Exit criterion:** after separate AWS approval and implementation, fresh
evidence lets reconciliation report an evidence-based pass or real drift
mismatch; it no longer sends repeated failure notifications solely because no
evidence producer exists.

### Phase 9 — Connect to target alignment preflight

**Question answered:** Does the current target meet the already-complete
repository declaration?

Extend the existing Target Alignment Preflight only after Phase 7 is stable.
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

### Phase 10 — Stage enforcement and broaden scope

<!-- deterministic-check: allow reason="The enforcement threshold is a phased human risk decision until the reviewed report-only controls exist and can become gates." -->
**Question answered:** When should a missing link block work?

Adopt controls in order:

1. report-only for the public server;
2. required on changes to its entrypoint, image, target, or deployment
   declaration;
3. required before packaging, with a fresh target-alignment refresh required
   before deployment;
4. add the scope index and extend coverage one reviewed scope at a time:
   shared target foundation, worker/queue execution, relay, PostgreSQL,
   identity/access, public ingress, observability/alerting, and any other
   active deployable capability revealed by Phase 0;
5. make an aggregate target result possible only after the scope index has no
   unowned, unknown, or deliberately deferred active capability.

**Deliverable:** lifecycle-stage gate references and change-scope routing.

**Exit criterion:** a relevant change cannot be treated as deploy-ready with a
missing source-to-target link or unreviewed affected scope, while unrelated
platform changes do not trigger provider checks. A claim of full target
coverage names every active scope and any remaining exclusions.

## Decisions Required Before Implementation

1. Confirm the public server is the correct first vertical slice.
2. Confirm the scope criteria and the target-local scope-folder shape before
   building the Scope Governance Artifact Set.
<!-- deterministic-check: allow reason="Registry adoption depends on human assessment of which deployment facts cannot safely be derived from source code; a later validator enforces the approved registry." -->
3. Confirm that a machine-readable runnable-program registry is acceptable
   when role and proof cannot be derived from code.
4. Choose whether the Phase 2 documentation-linkage rule belongs in the
   existing harness placement standard or in a new cross-layer standard.
5. Agree the threshold at which report-only checks become blocking gates.
6. Review the Phase 0 evidence map before creating any new declarations.
7. Review the proposed scope catalogue and the compatibility path for adding
   the target-local scope index before adding a second active scope.

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
