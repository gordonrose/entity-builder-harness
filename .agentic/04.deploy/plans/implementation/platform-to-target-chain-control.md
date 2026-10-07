<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.implementation.platform-to-target-chain-control
version: 13
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

## Repo-Wide Agentic Change-Governance Outcome

This is a platform-to-target plan, not a deployment-only plan. Its outcome is
that an agent can safely add, refactor, or retire product functionality by
following one connected, layer-owned set of instructions rather than collecting
mandatory rules from code comments, READMEs, and documentation.

`.agentic` is the authoritative source for *how an agent changes the
repository*: required assessment, ownership, stop conditions, records, checks,
and evidence. It does not replace the authoritative implementation facts in
source, package configuration, infrastructure declarations, or executable
scripts. READMEs and documentation remain essential human explanation and
reference material, but a mandatory instruction in either must link to its
owning `.agentic` artifact.

<!-- deterministic-check: allow reason="This table is an architectural ownership map; future workflows and gates own executable procedures." -->
The intended connected ownership is:

| Change concern | Governing layer | Required outcome |
| --- | --- | --- |
| How an agent finds applicable rules, records evidence, and handles cross-layer work | `.agentic/01.harness/` and `.agentic/06.shared/` | A change route and shared rules that do not depend on an agent remembering scattered instructions. |
| How a platform module, adapter, configuration contract, or runnable program is added or changed | `.agentic/03.product/` | The product change is structurally complete, testable, documented, and mapped to downstream impact. |
| How a runnable program is packaged, bound to a target, and proved safe to deploy and run | `.agentic/04.deploy/` | The deployment decision, target prerequisites, and proof chain are explicit and checked. |
| What the software and target actually do | Source, package configuration, `infra/`, and executable scripts | One implementation authority for each factual setting or behaviour. |
| How a person understands the system | READMEs and `docs/` | Clear explanation that links to, but does not compete with, the governing instruction. |

A product change therefore follows this governed path:

```text
change request
  -> shared change routing
  -> product-module or runnable-program assessment
  -> local construction and proof
  -> affected deployment-scope assessment, where applicable
  -> package, target, and deployment proof
```

Not every platform-module change reaches a provider or target check. The
product workflow must record when there is no runnable-program or deployment
impact. When there is impact, it must identify the affected scope; it may not
leave that decision implicit.

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

## Foundation Resource, Provider Selection, and Access Model

The plan distinguishes four facts which must never be collapsed into one vague
"service" or "persistence" field:

| Fact | Question answered | Example |
| --- | --- | --- |
| Logical capability | What behaviour is needed? | Shared request rate limiting. |
| Provider realisation | Which technology fulfils it? | AWS DynamoDB. |
| Exact target resource | Which concrete provider resource is used? | The staging `RateLimitTable`. |
| Workload runtime | How does the consuming scope run? | An ECS service, Lambda function, or one-pass task. |

A target may have several resources in the same capability family, several
providers for different purposes, and several workload runtime types. A
foundation resource is not inferred from its filename or provider type.

A resource is **foundation-owned** when it is shared, long-lived, required
before workloads can run, or has an independently managed security, recovery,
or operational lifecycle. A resource is **scope-owned** when it exists only
for one scope and should be created, changed, and retired with that scope.
This is a reviewed ownership decision. A foundation control domain is not
automatically a deployment scope; it becomes a scope only when it has its own
distinct runnable process, requirements, proof, recovery behaviour, or
lifecycle.

Each active foundation resource will receive one target-local index record with
these facts: stable repository ID; logical capability; provider; resource kind;
exact provider identity or safe lookup path; ownership and lifecycle rationale;
authoritative declaration path; consumers; exported configuration references;
security/recovery requirements; status; and proof path. Provider identity uses
safe identifiers such as account, region, stack, logical ID, output, name, or
ARN reference as appropriate; it never stores a secret value.

A scope declares its dependency by stable resource ID. A workload binding then
records the selected provider realisation, workload runtime, configuration
binding, and runtime role. An access requirement records the workload, exact
provider action, exact resource, reason, attached role, policy declaration,
safe proof, and prohibited/bounded access. This is the required chain:

```text
capability need
  -> selected adapter and provider
  -> foundation or scope-owned resource
  -> configuration binding
  -> workload role and narrow provider policy
  -> safe behavioural and policy proof
```

Selecting a provider is a compatibility decision, not merely an environment
variable. The selection review must prove that the selected adapter implements
the required provider-neutral capability, the runnable program supports the
selection, target configuration and secret references are valid, the resource
and network path exist, the role has only the required access, and migration,
rollback, and proof are appropriate for the dependency.

## Scope Records and Change Maintenance

The plan separates the authoritative facts needed to keep scopes current:

| Information | Canonical location | Update rule |
| --- | --- | --- |
| Scope names, state, owner, required dependencies, and declaration-contract path | Future target-local scope index under `infra/04.deploy/03.product/targets/<client>/<environment>/` | Add, retire, or change a scope in the same change set as its runnable program, workload, or requirement change. |
| Expected settings, secret names, permissions, dependencies, health, rollback, and proof paths | One bounded declaration contract per active scope in that target directory | Update whenever functionality adds, changes, or removes a runtime setting, dependency, image input, identity requirement, network path, persistence need, queue, rollback condition, or operational signal. |
| Foundation resource identity, ownership, lifecycle, consumers, exported configuration references, and proof | Future target-local `foundation/foundation-index.yml` | Add, reclassify, or retire a resource in the same reviewed change as its authoritative declaration, consumer binding, security/recovery rule, or provider migration. |
| Provider selection and workload access requirements | Scope declaration contract and workload binding, pointing to the authoritative adapter and provider-policy sources | Update whenever a scope adds, changes, or removes an adapter, provider, resource binding, role, action, resource permission, secret reference, or dependency proof. |
| Generic field shapes and validation rules | `.agentic/04.deploy/schemas/` | Change through the provider-neutral deployment governance workflow, with a field guide and compatibility review. |
| When scope review is required | `.agentic/04.deploy/standards/` and workflows | A changed platform module, adapter, entrypoint, image, target definition, or deploy script must be mapped to affected scope records before completion. |
| Deterministic proof of current repository consistency | `scripts/04.deploy/` | The future chain checker fails for a missing, orphaned, stale, or contradictory scope link. |

The current `declaration-contract.yml` remains the first server-baseline
contract. The initial slice does not move it. When a second active scope is
introduced, the design review will introduce the target-local scope index and
per-scope contract directory through a compatible migration, rather than
silently relocating the current contract.

Adding functionality therefore requires its owning change to identify affected
scopes, foundation resources, provider selections, access requirements, and
proofs. Removing functionality requires the reverse: remove its
workload/program references, consumer bindings, roles, configuration,
pipelines, and proofs; update or retire its scope/resource record; and prove
that no target binding or requirement still refers to it. The checker reports
an unreviewed affected scope, an orphaned declaration, a permission without a
declared dependency, a resource without an owner or consumer, or a target
reference to a retired program as a failure.

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

Before the first foundation resource record is created, the harness must also
provide a Foundation Resource Governance Artifact Set:

```text
.agentic/04.deploy/
  standards/target-foundation-resource.md
  workflows/change-target-foundation-resource.md
  schemas/target-foundation-resource.v1.schema.yml
  schemas/target-foundation-resource.v1.guide.md
  templates/target-foundation-resource/
  gates/check-target-foundation-resource.md

scripts/04.deploy/
  check-target-foundation-resource/
```

It teaches and checks the ownership classification, capability/provider/kind
distinction, provider identity, consumers, exported configuration references,
access requirements, lifecycle, security/recovery facts, and retirement path.
It must reject a broad provider policy unless a reviewed exception records why
the exact action or resource cannot be narrowed. It validates links and safe
identifiers; it does not read secret values or replace provider declarations.

The first target-local layout will be:

```text
infra/04.deploy/03.product/targets/kanbien/staging/
  foundation/
    README.md
    foundation-index.yml
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

The foundation README explains target-level facilities, ownership boundaries,
and how to follow an index record to its provider declaration and consuming
scopes. `foundation-index.yml` is a map of authoritative declarations, not a
second CloudFormation, IAM, or secret definition. This is a logical layout
only; existing files remain in place until the later reviewed information
architecture migration.

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

- Keep harness governance generic and portable. An `.agentic` standard,
  workflow, schema, template, or gate may define how any scope, dependency,
  provider selection, workload, or target resource is assessed; it must not
  prescribe the current product, environment, provider, account, region,
  service, database, queue, or other target decision.
- Model generic governance fields in terms such as capability, provider,
  resource kind, availability classification, configuration binding, access
  requirement, and proof. A target-specific record supplies their concrete
  values in `infra/04.deploy/.../targets/<client>/<environment>/`.
- Mark examples in governance artifacts as non-normative. Examples may explain
  a rule, but cannot turn a current provider or target choice into a universal
  requirement. Provider-specific implementation belongs in the appropriate
  adapter or target declaration, not in provider-neutral harness governance.
- Review proposed harness artifacts for accidental embedded target decisions.
  Reject or relocate a product-, environment-, or provider-specific decision
  unless it is genuinely required by the owning governance boundary.
- Derive facts from existing source and configuration where possible; do not
  create a second hand-maintained copy merely to satisfy the harness.
- Add a declaration only where a relationship cannot be reliably derived, such
  as the intended workload role or its required proof.
- Keep one authoritative declaration for each fact.
- Start report-only. A check becomes blocking only after existing gaps are
  understood and corrected.
- Assign each control to one lifecycle stage under
  `.agentic/04.deploy/lifecycle/`; do not duplicate checks across stages.
- Treat a self-explanatory deployment tree as an architectural outcome, not a
  cosmetic refactor. A person must be able to navigate from a scope, shared
  foundation, pipeline, or check to its purpose, owner, lifecycle role,
  dependencies, evidence, and governing instructions without relying on
  filename archaeology.
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
- every discovered target resource, provider adapter, permission-bearing role,
  workload, and pipeline with status `covered`, `deferred`, `unclassified`,
  or `retired`;
- each foundation-resource candidate's logical capability, provider, kind,
  source declaration, consumers, lifecycle/ownership rationale, and unknowns;
- missing, duplicated, contradictory, and currently unproved links.

**Deliverable:** a current-state report with source paths and no new runtime or
target declarations.

**Exit criterion:** every statement in the report points to existing
repository evidence; unknowns are labelled as unknown rather than inferred.
The report also proposes the initial scope catalogue and foundation-resource
catalogue, clearly separating active server coverage, foundation control
domains, excluded capabilities, and not-yet-modelled capabilities. No active
item may disappear into an unlabelled remainder.

### Phase 1 — Establish scope and foundation governance

**Question answered:** How does an agent create, change, or retire a scope or
target resource consistently rather than relying on memory?

Create the Scope Governance Artifact Set above, with fixtures proving both a
valid public-server scope and common invalid cases: absent index record,
missing owner, missing exclusion list, unresolved declaration path, and a
retired scope still selected by a target binding.

All Phase 1 harness artifacts must obey the governance portability boundary:
their rules, schemas, and templates describe generic classes of scope,
dependency, provider, resource, access, and proof. Fixtures may use concrete
example values to test a shape, but must be marked non-normative and must not
make a current product, environment, AWS service, or provider choice a
requirement. Concrete decisions remain in the target-local records.

Create the Foundation Resource Governance Artifact Set with fixtures proving
valid shared and scope-owned records, multiple resources in one capability
family, multiple provider types in one target, an unclassified active resource,
a missing consumer, a stale exported configuration reference, a permission not
connected to a declared dependency, and an impermissibly broad policy.

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
must introduce the target-local scope index, foundation index,
`scopes/README.md`, foundation README, and public-server scope README. The
foundation index must record every public-server dependency that Phase 0 has
classified as foundation-owned, or record its status as deferred/unclassified
with an owner and follow-up path. After Phase 0 has inventoried every reference to
the current root-level `declaration-contract.yml`, migrate that contract into
the scope folder in one compatible, reviewed change. Update every repository
reference; do not leave two authoritative copies. A compatibility pointer is
permitted only when a verified consumer requires it.

The initial scope record must name its active state, owner, covered concerns,
explicit exclusions, dependencies, provider-selection status, contract path,
and known proof paths. Its workload binding and access requirements are added
in the later target-binding phase; the scope record must say that this proof is
pending rather than pretending it exists.

**Deliverable:** report-only scope, foundation-resource, and pipeline checks;
the governed first `platform-server` scope; its classified foundation
dependencies; and its declared package-publication pipeline.

**Exit criterion:** a reviewer can follow the scope workflow, find the first
scope from the index, understand it from its README, validate its structure,
identify its approved package route and foundation dependencies, and distinguish
its current coverage from pending target-binding and access work.

### Phase 2 — Establish documentation and governance linkage

**Question answered:** Which artifact is allowed to instruct an agent, and
which artifact merely explains the system?

Extend the harness placement/authoring rules with a small, enforceable
documentation-linkage standard. It will define:

- a repository-wide instruction inventory that classifies existing material in
  platform modules, adapters, `infra`, scripts, READMEs, docs, and comments as
  implementation fact, human explanation, executable check, or mandatory
  agent instruction;
- a migration rule: each mandatory agent instruction receives one owned
  `.agentic` home in the appropriate harness, product, deploy, or shared
  layer; its former README or documentation location becomes explanation with
  a link to that governing artifact;
- required links from module and deploy READMEs to their governing workflow or
  standard;
- required links from agentic workflows to the human explanation necessary to
  apply them safely;
- a conflict rule: agentic governance, executable contract, and documentation
  must be reconciled before a change is considered complete;
- a deliberately limited checker that detects missing links, not the truth of
  prose.

The inventory is a migration ledger, not a reason to copy all existing prose
into `.agentic`. It must preserve one authoritative implementation fact and
one authoritative agent instruction for each governed concern.

**Deliverable:** one cross-layer standard, a repository-wide instruction
inventory and migration ledger, and an initially report-only linkage check.

**Exit criterion:** the public-server chain and its selected product modules
have a clear map from each mandatory instruction to its governance owner; each
README or document either links to that owner or has a recorded migration gap.

### Phase 3 — Define the platform-module contract

**Question answered:** What evidence makes a platform module safe to change?

Build on the existing platform-runtime workflow. Establish the corresponding
generic product-governance artifact set under `.agentic/03.product/`: a
platform-module standard, change workflow, field guide or schema where a
machine-readable record is needed, template where it improves consistency, and
report-only gate backed by a deterministic check. These artifacts govern a
class of module change; they must not prescribe a current module, product,
provider, or target.

The module contract must require evidence for:

- a supported public boundary such as `index.ts`;
- ownership, non-ownership, and dependency-direction rules;
- an explicit configuration surface when the module consumes or defines
  runtime configuration;
- type check, build, runtime test, and boundary test when applicable;
- a module README and source map that explain the module to a human;
- a recorded reason when a normal proof is not applicable.

The change workflow must first identify whether the module is used by a
runnable program. If it is, it must pass that impact to the relevant
deployment-scope workflow. If it is not, it must record that no deployment
scope is affected rather than forcing an irrelevant target check.

The configuration surface must be visible from the module tree rather than
hidden among unrelated implementation. A configured module uses this shape:

```text
platform/<module>/
  src/
    configuration/
      README.md
      <configuration-concern>.ts
      index.ts
```

Each concern file owns one coherent configuration concern and its typed shape,
validation, defaults, sensitivity classification, and documented relationship
to any dependency. `configuration/index.ts` is the deliberate shared doorway
for those individual concerns, following the same public-surface pattern used
for module responsibilities. The module's `src/index.ts` re-exports only the
configuration contracts that other modules or a runnable-program composition
are allowed to use.

`configuration/README.md` is the human configuration source map. It explains
each concern in plain language, names its owning TypeScript file, states
whether it is required or optional, identifies its runtime consumer and
dependency relationship, and links to its validation and proof. It records
secret *classification* and approved source only; it never contains a secret
value. The README orients a reader and links to the authoritative contracts; it
must not duplicate configuration values or override the TypeScript definition.

A module with no configuration does not need an empty directory; its README
and source map must state that it consumes and defines no runtime
configuration. A module may retain a small private constant beside one function
only when it is not a runtime configuration choice. Existing direct
environment reads are an inventory-and-migration concern: later work must move
their parsing and validation to the runnable-program composition boundary and
pass typed configuration into modules. It must not claim that this structure
already exists until each selected module has been reviewed and migrated.

The checker must derive the build and test facts from `package.json`,
`tsconfig*`, and test locations. It must not introduce a duplicate module
manifest for information already held there.

**Deliverable:** generic product-governance artifacts and a report-only
product-layer module-contract check, first applied to the modules used by the
public-server chain.

**Exit criterion:** the checker identifies whether each selected module has a
public boundary, declared ownership, expected proofs, and an explanation.

### Phase 4 — Declare runnable programs

**Question answered:** Which files can a package or target start as processes?

Add one small registry beside `infra/04.deploy/03.product/entrypoints/`. It
lists runnable programs only, not shared helpers. Each record must identify:

- stable program identifier;
- source file;
- role: HTTP server, long-running worker, or one-pass task;
- selected product composition, provider-neutral capability contracts, and
  supported provider-adapter selections;
- the boundary at which raw target configuration is validated and translated
  into typed module configuration;
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
- workload runtime type, such as ECS service, Lambda function, or one-pass
  task;
- selected image contract;
- configuration/declaration-contract scope;
- selected provider adapters and the foundation or scope-owned resource IDs
  that fulfil their dependencies;
- attached execution and runtime roles, plus each access requirement's policy
  declaration and bounded action/resource reference;
- health and rollback proofs; and
- target owner.

AWS-specific command details remain in the existing CloudFormation source. The
binding is provider-neutral and the checker compares it to the provider
definition; it does not replace that definition. A provider selection is valid
only when its adapter, typed configuration, target resource, network/secret
reference where applicable, role policy, migration/rollback treatment, and
proof are all linked.

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
-> foundation/scope-owned resource classification
-> target workload binding
-> configuration and access requirement bindings
-> declaration-contract requirements and proofs
```

Possible results are `complete`, `missing-declaration`,
`declared-but-not-implemented`, `implemented-but-unproved`, and
`explicitly-out-of-scope`. It additionally reports `unclassified-active-item`,
`permission-without-dependency`, `dependency-without-permission`, and
`provider-selection-incompatible`.

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
- selected provider, foundation-resource identity, workload role, and narrow
  access-policy facts;
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
4. require every new or changed platform module, configuration concern,
   adapter, runnable program, resource, role, workload, or pipeline to satisfy
   its product-layer contract and identify its affected scope and foundation
   records before completion; where no deployment scope is affected, require a
   recorded reason instead of an irrelevant provider check;
5. extend coverage one reviewed area at a time: foundation control domains,
   worker/queue execution, relay, PostgreSQL, identity/access, public ingress,
   observability/alerting, and any other active capability revealed by Phase 0;
6. make an aggregate target result possible only after the scope and foundation
   indexes contain no unowned, unknown, or deliberately deferred active item.

**Deliverable:** lifecycle-stage gate references and change-scope routing.

**Exit criterion:** a relevant change cannot be treated as deploy-ready with a
missing source-to-target link, unreviewed affected scope/foundation record, or
unbounded provider selection or access requirement, while unrelated platform
changes do not trigger provider checks. A relevant product change cannot be
treated as complete without its product-layer contract and recorded deployment
impact decision. A claim of full target coverage names every active scope,
foundation resource, and remaining exclusion. New harness artifacts are also
rejected when they embed a target-specific decision that belongs in a target
record or provider-specific implementation.

### Phase 11 — Reorganise the verified deployment information architecture

**Question answered:** Once ownership and proof are known, how should `infra`
and `scripts` be arranged so their purpose and relationships are apparent from
their structure?

This phase follows the evidence mapping and scope adoption work; it does not
guess ownership from a filename or move files merely to make the tree look
tidier. Design a reviewed target information architecture that makes these
boundaries visible:

- deployable scopes and their human-readable maps;
- foundation-owned target facilities, including resources that are shared,
  long-lived, target-wide, or independently managed;
- provider-specific adapters and target bindings;
- package-publication, deployment, verification, and drift-detection
  pipelines;
- reusable lifecycle-stage checks and scope-specific checks; and
- the governing workflow, standard, and deterministic validation for each
  meaningful directory.

<!-- deterministic-check: allow reason="Each reviewed migration has different consumers and requires a specifically designed reference check; the plan cannot safely invent that check before the migration design exists." -->
For every proposed move or split, the migration design must name the current
authoritative file, its consumers, its scope or foundation owner, the logical
capability/provider/resource-kind classification where applicable, the new
authoritative location, compatibility requirements, and the check that proves
every reference was updated. A scope or foundation map may link to shared or
reusable implementation, but it must never become a duplicate authority for
the same configuration, permission, or provider-resource fact.

Migrate one bounded, reviewed area at a time. Directory READMEs explain how a
human should navigate and link to governing `.agentic` artifacts; they do not
invent independent instructions. Retire an old path only after its consumers,
indexes, documentation, and deterministic checks all point to the approved
replacement. This phase does not authorize AWS mutation, target mutation, or
unreviewed PostgreSQL changes.

**Deliverable:** a reviewed deployment-tree information-architecture design,
a migration ledger, and one or more independently verified, bounded
migrations.

**Exit criterion:** a reviewer can navigate from any active scope,
foundation-owned facility, pipeline, or check to its purpose, owner,
dependencies, proof, and governance without reverse-engineering unrelated
files; every retained path is intentional and every migrated path has no stale
consumer.

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
8. Confirm the foundation-resource classification criteria, index shape, and
   provider-identity fields before creating target foundation records.
9. Confirm the provider-selection compatibility and access-requirement fields
   before binding a workload to a new provider or resource.

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
find, by command and source path, its platform inputs, adapter choice,
capability/provider/resource classification, compiled image command, staging
workload/runtime, required non-secret configuration, attached roles and narrow
access requirements, dependency declarations, local/package proofs,
target-alignment result, and target/run proofs. Any missing or contradictory
link is reported before a deployment is treated as ready.
