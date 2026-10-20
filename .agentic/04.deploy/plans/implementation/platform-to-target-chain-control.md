<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.implementation.platform-to-target-chain-control
version: 32
status: draft
created_on: "2026-10-06"
updated_on: "2026-10-20"
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

The first controlled vertical slice is the planned `kanbien-core-platform`
target, beginning with a bootstrap runtime scope. No target directory, AWS
resource, identity, or deployment route is created by this planning phase. The
existing `kanbien/staging` public server remains unchanged as a read-only
reference and possible later migration candidate. Its workers, relay,
PostgreSQL Stage 6, Cognito, DynamoDB, ingress, and observability work are not
silently inherited by the new target. This preserves existing PostgreSQL
controls and avoids retrofitting a new model around a live composition.

## Staged Foundation Model

The initial `kanbien-core-platform` slice is the **bootstrap runtime slice**, not a claim
that the full platform foundation already exists. Its purpose is to prove that
one exact server package can be configured, deployed, observed safely enough
to make a release decision, and restored to a prior immutable package. It
includes the runnable server, configuration and secret-reference boundary,
health/readiness, package and delivery route, rollback route, and safe release
receipts. It deliberately does not claim durable application data, end-user
security, external integration, queue processing, or a complete production
observability service.

Its first implementation goal is a complete but deliberately narrow lifecycle
proof: establish the target from a declared absent baseline as immutable
release A, then make one separately declared update to immutable release B.
The target can be treated as updated only after B completes the same health and
meaningful-operation verification and has an accepted receipt. A failed B must
not advance the baseline or trigger an automatic replacement deployment; the
recorded prior baseline A remains the recovery target. This tests target
creation, planned change, package custody, fresh alignment, verification,
receipt, and recovery before deferred foundations are introduced.

The intended foundation grows in ordered slices:

```text
bootstrap runtime and minimum release evidence
  -> persistence foundation
  -> application security boundary
  -> fuller observability foundation
  -> product capabilities that use those foundations
```

This order avoids circular proof: for example, initial delivery receipts live
in the delivery system rather than relying on an application persistence
capability whose own safe deployment is still being proved. A later foundation
slice must declare its configuration, provider selection, network, workload
access, failure behaviour, observation, recovery, and proof before product
capabilities may rely on it.

Existing `packages/core/` and `platform/` work remains the factual product
source. The plan does not duplicate or relocate that work into `infra`. It
first maps only the core/package and platform modules actually composed by the
bootstrap runnable program; later foundation slices bring their relevant
modules, adapters, configuration surfaces, and tests into the same controlled
chain. A module is not assumed deployable solely because it exists, and a
module not selected by a scope is not prematurely treated as a gap.

## Target Separation Decision

The target identifier for the first controlled foundation build is
`kanbien-core-platform`. Its planned repository location is
`infra/04.deploy/03.product/targets/kanbien/core-platform/`, but that path is
not created until the target-design package is separately approved. The target
will have distinct declared workload names, infrastructure-stack names,
identity/permission bindings, configuration and secret-reference namespace,
network boundary, evidence route, package/delivery route, and rollback record.

It may later share an AWS account or region with `kanbien/staging` only through
an explicit target declaration and isolation review; same-account placement is
not assumed. Reuse of an existing ECR repository, role, secret, VPC, security
group, log store, service, or pipeline requires the same explicit decision.
Until then, the correct status is `planned`, not deployed or aligned.

`kanbien/staging` is retained as a **reference target**. A read-only inventory
may learn from its existing public-server composition, but no foundation
requirement is inferred from that composition and no migration, deletion,
rename, or target mutation is authorised. A later, separately approved
comparison will decide whether any workload moves, remains, or is retired.

## Bootstrap Lifecycle and Boundary Design

The planned bootstrap target is private. It has no public ingress, end-user
authentication route, persistence provider, queue, or inherited staging
dependency. Its one meaningful operation is a controlled internal verification
request: the server accepts the request, validates its required safe startup
configuration, and returns a safe identity for the selected immutable release.
That operation proves more than process liveness or generic readiness without
claiming a product capability that the slice does not yet provide.

The bootstrap runnable program is a planned new
`infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts`. The
`kanbien-core-<role>.main.ts` prefix identifies runnable programs for the new
controlled core family; helper files do not use `.main.ts`. The existing
`kanbien-platform-server.main.ts` remains reference evidence and must not be
reused unchanged: it composes the product-smoke application and optional
staging-era adapter paths that this slice deliberately excludes.

`kanbien-core-server.main.ts` reuses the existing generic
`platform/server/src/main.ts` process lifecycle and
`platform/server/src/transport.ts` HTTP transport. It must not fork either.
The planned configuration surface under `platform/server/src/configuration/`
makes generic server requirements, including safe release identity, visible
and typed; it is a future migration from the selected direct environment reads
in the existing startup code, not a claim that the folder already exists.

The selected bootstrap module graph is `platform/server` and its existing
generic contracts, runtime, configuration, health, security, and observability
dependencies. It selects no product application, provider adapter, persistence
service, identity provider, queue, or public-ingress capability. A code-package
dependency is not by itself a selected runtime dependency or live target
service, but it must be inventoried before the image is accepted.

Generic release verification belongs in `platform/server`, not in an AWS target
or one product app. It provides a controlled route that returns only approved
release metadata. It does not itself prove the running image digest: the
candidate verifier must combine the server response with independent workload
image-digest evidence and package-custody evidence before accepting a release.

Before the bootstrap image is selected, move the existing
persistence-observability bridge from generic `platform/observability` into
`platform/persistence/src/observability/`. Generic logs, metrics, traces,
correlation, and health signals remain in `platform/observability` without a
`platform/persistence` dependency. The persistence-owned integration depends
on generic observability and is selected only by a later persistence scope.
This is a required dependency-boundary refactor, not a provider adapter or an
AWS target decision.

Technical infrastructure permissions are grouped under `technical-access/`,
not `identity/` or bare `access/`, to keep them distinct from application
authentication and authorisation. Target-wide records may declare
`delivery-permissions.yml` and `workload-startup-permissions.yml`; a scope
declares its own `runtime-permissions.yml`. The first bootstrap runtime grants
no application-service runtime permission. The actual provider roles and
policies remain their authoritative provider declarations; these records state
the bounded purpose, actor, action/resource requirement, and proof link.

A shared internal-verifier *facility*, if one is later selected, is
foundation-owned. The verifier-to-bootstrap-server route is scope-owned and
must be declared with the bootstrap runtime rather than incorrectly presented
as a target-wide route for every future workload.

The bootstrap program has a dedicated `core-server` container image boundary,
not the existing broad platform-shell image. Its planned location is
`infra/04.deploy/03.product/image/core-server/`. The image contract compiles
and starts only `kanbien-core-server.main.ts` and includes only its reviewed
runtime dependency graph, safe defaults, health command, and local payload
proof. It must not package staging-server, worker, relay, PostgreSQL-specific,
or provider-adapter programs merely because they exist elsewhere in the
repository. The image repository decision remains unresolved and requires the
same target-isolation review as every other shared AWS resource.

The separately reviewed target-design package must declare, before any target
path or AWS resource is created:

- the absent-baseline, first-release, accepted-baseline, update-candidate, and
  failed-candidate lifecycle states;
- the selected runnable program and immutable package identity;
- every required, optional, and not-applicable configuration setting, including
  value shape, supply route, and safe missing/invalid-setting diagnostic;
- the delivery, workload-startup, and running-workload access requirements as
  separate technical access concerns, without conflating them with application
  identity or authentication;
- the private network boundary and the deliberately narrow internal verifier
  route, while leaving the AWS mechanism unresolved until reviewed;
- distinct liveness, readiness, and meaningful-operation checks; candidate
  acceptance/rejection rules; GitHub Actions receipt route; and prior accepted
  immutable rollback target; and
- safe structured verifier result codes and evidence fields that reveal no
  secrets, tokens, connection strings, personal data, or unapproved private
  target details.

The repository will eventually separate these factual target declarations from
the verifier implementation and pipeline orchestration: server code implements
the verification operation; the scope declaration states what must be proved;
the deploy script performs the controlled request; the pipeline runs it; and
the receipt records the result. No existing staging smoke test is assumed to
fill any of these roles without review.

## First Bootstrap Implementation Map

This is the intended *future* layout for the first bounded implementation
packages. It is not authorisation to create the target, AWS resources, or
runtime code in one change. Each package remains separately reviewable, and
the existing `kanbien/staging` tree and its scripts are not moved as part of
this work.

```text
.agentic/
  03.product/
    standards/runnable-program-contract.md
    workflows/runnable-program-change.md
  04.deploy/
    standards/image-contract.md
    workflows/package-candidate.md
    workflows/verify-candidate-release.md

platform/
  server/src/
    configuration/                 ← typed generic server configuration
    verification/                  ← safe generic release-verification route
  persistence/src/
    observability/                 ← persistence-owned integration only

infra/04.deploy/03.product/
  entrypoints/
    runnable-program-index.yml     ← factual program records
    kanbien-core-server.main.ts    ← first runnable program
  image/core-server/
    Dockerfile
    image-contract.yml             ← factual image boundary and start facts

infra/04.deploy/03.product/targets/kanbien-core-platform/
  target-profile.yml               ← created only after target design approval
  foundation/                      ← shared target requirements
  scopes/bootstrap-runtime/
    declaration-contract.yml       ← required settings and proof promises
    workload-binding.yml           ← program-to-workload selection
    technical-access/              ← delivery, startup, runtime access facts
    network/                       ← verifier route and network proof

scripts/04.deploy/lifecycle/
  20-build/core-server-dependency-boundary/
  40-package/build-core-server-image/
  40-package/smoke-test-core-server-image/
  50-deploy/prepare-core-server-candidate/
  50-deploy/deploy-core-server-candidate/
  60-run/verify-core-server-candidate/
```

The `.agentic` artifacts govern how agents assess and change a class of
program, image, or candidate verification. The `platform`, `infra`, and
`scripts` artifacts state and perform the factual implementation. README files
explain the local tree and link back to the governing artifact; they do not add
independent mandatory rules.

The four checks have deliberately separate jobs:

| Check | Inputs | Required result | Safe result location |
| --- | --- | --- | --- |
| `20-build/core-server-dependency-boundary` | declared program root, TypeScript imports, package manifests, lockfile, and forbidden roots | the allowed compile/runtime graph is reported; a product app, provider adapter, persistence package, worker, relay, or old staging program cannot enter unnoticed | ephemeral local output and CI artifact; never a committed generated list |
| `40-package/build-core-server-image` | program record, image contract, Docker build output, payload verifier | the compiled selected command and only its reviewed runtime payload are present | CI build artifact and package custody record |
| `40-package/smoke-test-core-server-image` | locally built image | one declared start command, liveness, readiness, safe release identity, and no sensitive output | CI/local test output; only safe receipt fields are retained |
| `60-run/verify-core-server-candidate` | tested digest, target declaration, fresh read-only target evidence, controlled verifier response | the deployed workload digest, safe server identity, and package custody evidence agree | GitHub Actions candidate receipt and job summary |

The dependency-boundary reporter derives its result rather than accepting a
hand-written exhaustive file list. The program record names the root and its
deliberate exclusions; TypeScript imports, package manifests, the lockfile,
and built payload establish the actual graph. A mismatch is a safe failure,
not an invitation for the check to widen the image automatically.

Implementation order is intentionally narrow:

1. create generic runnable-program and image-contract governance plus
   report-only fixtures;
2. extract the persistence-owned observability integration and verify the
   generic observability graph no longer selects persistence;
3. add the core program record, entrypoint, dependency-boundary reporter, and
   local proof without AWS state;
4. add the dedicated image contract, build, payload check, and local smoke
   proof;
5. only after an approved target design, create target declarations and add
   the read-only alignment, deployment, and candidate-verification path.

Each package stops on a failed gate, unclear declaration, or target-mutation
boundary. No report, check, or pipeline may create AWS resources merely to
make its own evidence pass.

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
| How failures are classified, redacted, tested, and made actionable without exposing sensitive information | `.agentic/06.shared/`, referenced by product and deploy controls | Safe diagnostic records distinguish observed failures from guessed causes and give an agent a bounded next check. |
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

## Safe Diagnostic and Error-Evidence Model

Safe, granular diagnostics are a required part of any product-to-target
implementation. They must let an agent distinguish a missing setting from a
name-resolution failure, a connection timeout, a TLS failure, authentication
failure, permission denial, absent resource, invalid response, or
schema/version mismatch without disclosing secret values, connection strings,
tokens, headers, or unapproved private target details.

A diagnostic records the observed fact rather than guessing its cause. It has a
stable code; logical scope and dependency identifiers; lifecycle stage such as
startup, readiness, request, background work, preflight, or deployment
verification; safe context; retryability; and a bounded next check. A timeout,
for example, may direct an agent to the network-path proof; it must not assert
that one particular firewall rule is wrong without evidence.

The future shared standard under `.agentic/06.shared/` defines this safe
diagnostic contract, redaction rules, code taxonomy, test expectations, and
remediation-routing rules. Product controls require modules, adapters, and
runnable programs to map their meaningful failures into the contract. Deploy
controls require scope declarations, preflight, and target evidence to state
the expected failure behaviour and safe proof without duplicating raw provider
errors. Runtime events remain in the approved operational logging system, not
in Git; repository records retain only contracts, mappings, tests, and safe
evidence references.

Every declared dependency-availability behaviour must also declare its required
observation: safe failure diagnostic, safe recovery diagnostic, health-state
effect, metric or status signal, alert policy, and proof path. An alert policy
is explicitly `required`, `deferred`, or `not-required`; `deferred` records an
owner and follow-up path and prevents a claim of complete observability. This
is a declaration of required evidence, not a second definition of the log,
metric, dashboard, or alert implementation.

## Concern Control Matrix

Before implementation, the plan maintains one concern-control matrix for the
selected vertical slice. It prevents a concern from being treated as covered
merely because it is mentioned in prose. Each row names the intended record or
implementation home, the quality/proof obligation, the agentic instruction
owner, and whether the design is ready or still needs detailed design.

| Concern | Structure: record or implementation home | Quality: required proof | Instructions: owning agentic layer | Design state |
| --- | --- | --- | --- | --- |
| Repository change routing and source-of-truth linkage | Layer-owned `.agentic` workflow plus migration ledger; implementation facts remain in source and `infra` | Every mandatory instruction has one owner; explanations link to it; conflicts stop work | `01.harness` and `06.shared` | Planned in Phase 2 |
| Platform modules and provider adapters | Module source, public boundary, visible configuration surface when applicable, tests, source map | Type, build, boundary, runtime, and configuration proof as applicable | `03.product` | Planned in Phase 3 |
| Runnable program and image | Runnable-program registry, entrypoint, image contract, compiled command | Validated configuration boundary, payload check, local image smoke proof | `03.product` and `04.deploy` | Planned in Phases 4–5 |
| Configuration and secret references | Typed module configuration plus target scope declaration and authoritative target binding | Required/optional status, validation, safe secret-reference handling, local and target proof | `03.product` and `04.deploy` | Planned; field-level scope design remains to be reviewed |
| Dependency and availability behaviour | Scope declaration and workload binding, linked to foundation or scope-owned resource | Required/optional/degraded classification; startup, readiness, request, recovery behaviour; safe failure/recovery diagnostics; health effect; metric/status signal; alert policy; and proof | `04.deploy`, with product contracts where the failure originates | Needs dedicated contract, schema, field guide, fixtures, and checker design |
| Foundation resource and provider selection | Target-local foundation index, scope declaration, workload binding, authoritative provider declaration | Ownership/lifecycle rationale, adapter compatibility, resource identity, consumer, migration and rollback proof | `04.deploy` | Planned in Phase 1 and later binding phases |
| Network relationship | Scope/workload network requirement linked to authoritative provider network declaration | Safe proof of name resolution, transport/application protocol and port, route, narrow source/destination rule, TLS/server-identity policy, local equivalent, and target/runtime evidence | `04.deploy`, with product diagnostics at the connection boundary | Needs dedicated contract, schema, field guide, fixtures, and alignment-check design |
| Workload identity, access, and application authentication | Workload identity/access record, workload binding, and authoritative provider/IAM or application-auth declaration | Authz versus workload-identity separation; narrow action/resource access; safe credential supply, rotation/revocation, and authentication-failure proof; execution/runtime/dependency identity separation | `03.product` and `04.deploy` | Needs dedicated contract, schema, field guide, fixtures, and checker design |
| Health, release verification, and recovery | Runnable-program behaviour, image contract, scope declaration, workload binding, target health/deployment declaration, and pipeline receipt | Process, liveness, readiness, candidate-specific meaningful verification, declared rollout/deadline, rollback to prior immutable digest, restoration proof, and safe receipt | `03.product` and `04.deploy` | Needs dedicated contract, schema, field guide, fixtures, and checker design |
| Safe diagnostics and operational evidence | Shared diagnostic contract, product/adaptor mapping, scope proof references, approved runtime logging | Stable observed-fact code, secret and PII minimisation/redaction, stage, retryability, bounded next check, test fixtures, and safe evidence reference | `06.shared`, referenced by `03.product` and `04.deploy` | Needs dedicated standard, taxonomy, schema, fixtures, and gate design |
| Observability and alerting implementation | Scope observation contract, workload binding, shared safe-evidence contract, and authoritative provider log/metric/trace/alert declarations | Operation-linked signal, safe correlation identifiers, access/retention, alert condition/duration/owner/deduplication/recovery proof, and explicit covered/deferred/excluded state | `04.deploy`, `06.shared`, and provider-specific operations governance | Needs dedicated contract, schema, field guide, fixtures, and checker design; deferred from first-slice runtime coverage |
| Package publication and delivery pipeline | Target-local pipeline catalogue, package-custody record, and existing workflow/provider declarations | Source-to-digest provenance, test/scan/attestation evidence, approved repository and separated identities, target promotion/approval, exception expiry, custody handoff, and rollback route | `04.deploy` | Needs dedicated contract, schema, field guide, fixtures, and checker design |
| Target alignment, drift, and live verification | Alignment contract, safe evidence record, target read adapter, and run proof | Fresh expected-versus-actual comparison, expiry, drift state, live health and meaningful behaviour | `04.deploy`, with AWS execution remaining under `.agentic/aws/` | Planned in Phases 8–9 |

The matrix is a governance index, not a second configuration system. It points
to the authoritative source or target record for each fact. A row marked
“needs dedicated design” is an explicit gap: no agent may claim that concern is
fully governed, or silently invent its missing structure, quality rule, or
instruction.

## Scope Model

A **scope** is a bounded deployable capability, not a repository layer and not
simply a platform module. It is the unit for which the repository can state
expected target requirements and later report an alignment result.

| Term | Meaning | Example |
| --- | --- | --- |
| Platform module | Reusable runtime building block. A module can be used by several deployable capabilities. | `platform/security` or `platform/observability` |
| Runnable program | A process that composes product, platform, and selected adapters. | `kanbien-platform-server.main.ts` |
| Deployment scope | The bounded capability and target workload whose requirements are declared and proved together. | `kanbien-core-platform-bootstrap-runtime` |
| Scope operation | A named job the scope promises to perform, with its required outcome. | `bootstrap-verification`: safely report that the selected release accepts a controlled internal request. |
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
| Scope operations, their promised outcomes, implementation/test evidence, and explicit exclusions | The active scope's bounded declaration contract | Add, change, or retire an operation in the same reviewed change as the product behaviour, route, job, command, or test that implements it. A dependency must reference the operation it supports; no operation means no inferred business criticality. |
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
shape and fields, including an operation-and-promise catalogue. Each operation
has a stable ID, plain-language promised outcome, implementation and test
evidence links, and explicit exclusions. The script and gate validate the
facts that can be checked deterministically. They do not infer business
criticality from source code: a missing promised outcome is a design gap that
requires a reviewed human decision.

The workflow must build a responsibility inventory before it creates or changes
a scope. For every concern in the current concern-control matrix—runnable
program, configuration, dependencies, foundation/provider selection, network,
workload identity/access, health/recovery, observation, delivery route, and
target alignment—the inventory records `covered`, `deferred`, `excluded`, or
`unresolved`, with a reason, owner/follow-up where applicable, and source,
target, and proof links. `excluded` requires evidence that the scope does not
use the concern; `deferred` requires an owner and follow-up; `unresolved`
blocks any claim of complete scope coverage. No concern may be silently absent.

The agent derives candidates for the inventory from the approved product
change, runnable-program and image boundaries, configuration declarations,
adapter/dependency use, existing target declarations, and the Phase 0 evidence
map. It must trace and record those links, not infer product criticality,
acceptable degradation, provider choice, security policy, or alert policy. A
missing human decision stays `unresolved` and stops the workflow for review.

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

Before a scope can claim a dependency's availability behaviour is governed, the
harness must also provide a Dependency Availability and Observation Artifact
Set:

```text
.agentic/04.deploy/
  standards/dependency-availability-and-observation.md
  workflows/change-scope-dependency.md
  schemas/dependency-availability-and-observation.v1.schema.yml
  schemas/dependency-availability-and-observation.v1.guide.md
  templates/dependency-availability-and-observation/
  gates/check-dependency-availability-and-observation.md

scripts/04.deploy/
  check-dependency-availability-and-observation/
```

It defines the provider-neutral shape for a dependency classification; startup,
readiness, request, and recovery behaviour; safe failure and recovery
diagnostics; health effect; metric or status signal; alert policy; and local,
target, and runtime proof. It must distinguish an explicitly deferred alert
implementation from an intentional no-alert decision, and require an owner and
follow-up for the former. It validates declarations and safe links only; it
does not read secret values, capture production error dumps, or duplicate a
provider's logging, metric, dashboard, or alert definition. Each dependency
record must reference one declared scope operation; it must not classify a
provider or resource as universally required, optional, or degraded.

At minimum, the record must carry a stable logical identity and stated
capability; its operation and promise; its classification and rationale; all
four lifecycle behaviours; observation and proof references; and safe links to
the configuration, network, access, and provider/foundation records that make
the dependency usable. Those linked records retain their own facts. The
dependency record must not become a copy of a connection string, credential,
private network address, IAM policy, or provider resource definition.

The request and recovery fields must also distinguish a dependency unavailable
before work starts, a confirmed failure, and an unknown outcome after work may
have been sent. An unknown outcome requires an explicit idempotent-retry or
reconciliation path; no declaration may silently convert it into confirmed
success, confirmed failure, or unrestricted blind retry. Recovery must
separately prove availability for new work and state how uncertain in-progress
work is reconciled.

Before a scope can claim a network relationship is governed, the harness must
also provide a Network Relationship Governance Artifact Set:

```text
.agentic/04.deploy/
  standards/network-relationship.md
  workflows/change-scope-network-relationship.md
  schemas/network-relationship.v1.schema.yml
  schemas/network-relationship.v1.guide.md
  templates/network-relationship/
  gates/check-network-relationship.md

scripts/04.deploy/
  check-network-relationship/
```

It defines the provider-neutral relationship between a named workload and a
named dependency/resource: approved destination-name and resolution policy;
transport and application protocol; port; private/public boundary; route;
narrow source/destination network rule; TLS encryption and server-identity
verification policy; any reference to client authentication; local equivalent;
safe diagnostic categories; and local, target, and runtime proof. The
authoritative provider declaration owns the real DNS, addresses, subnets,
routes, firewalls, security groups, certificates, certificate rotation, and
mutual-TLS configuration. The network record links to those facts; it does not
duplicate them or store a private address, certificate, or secret value.

Before a scope can claim workload identity, access, or dependency
authentication is governed, the harness must provide a Workload Identity and
Access Artifact Set:

```text
.agentic/04.deploy/
  standards/workload-identity-and-access.md
  workflows/change-scope-workload-identity-and-access.md
  schemas/workload-identity-and-access.v1.schema.yml
  schemas/workload-identity-and-access.v1.guide.md
  templates/workload-identity-and-access/
  gates/check-workload-identity-and-access.md

scripts/04.deploy/
  check-workload-identity-and-access/
```

It distinguishes user-facing application authorisation from the identity used
by a workload to reach a dependency. It records the workload and operation,
authentication method, safe identity or credential reference, supply method,
refresh method, rotation and revocation owner, narrow required actions, and
startup/readiness/request/recovery behaviour. It separately identifies the
pipeline identity, execution role, runtime role, and any dependency identity;
one must not be silently reused as another. It links to the authoritative IAM,
secret-management, provider, and application-auth declarations rather than
copying role policy, token, password, certificate body, or secret value.

Before a scope can claim its health, release verification, or rollback behaviour
is governed, the harness must provide a Health and Release Verification
Artifact Set:

```text
.agentic/04.deploy/
  standards/health-and-release-verification.md
  workflows/change-scope-health-and-release-verification.md
  schemas/health-and-release-verification.v1.schema.yml
  schemas/health-and-release-verification.v1.guide.md
  templates/health-and-release-verification/
  gates/check-health-and-release-verification.md

scripts/04.deploy/
  check-health-and-release-verification/
```

It distinguishes process/liveness, readiness, and meaningful operation proof;
declares the candidate identity, rollout strategy, required healthy capacity,
startup grace period, decision deadline, acceptance/rejection conditions,
rollback target, and restoration proof. Meaningful verification must prove the
candidate's immutable identity rather than merely obtain a successful response
from an older task behind a shared route. The artifact set defines a safe
verification-receipt shape and reference path; it does not store request
payloads, credentials, or raw provider error dumps.

Initially, the delivery pipeline stores each per-run receipt as a
machine-readable GitHub Actions artifact with a human-readable job summary.
The repository records the required receipt and its safe reference, not the
receipt itself. A later durable operational-evidence store may replace or
supplement that route only after its retention, access, independence, and
bootstrap behaviour are reviewed; an application persistence capability is not
automatically suitable because it can create circular deployment dependency.

Before a scope can claim runtime observability or alerting is governed, the
harness must provide an Observability and Alerting Artifact Set. It references
the shared safe-diagnostic contract; it does not replace it:

```text
.agentic/04.deploy/
  standards/observability-and-alerting.md
  workflows/change-scope-observability-and-alerting.md
  schemas/observability-and-alerting.v1.schema.yml
  schemas/observability-and-alerting.v1.guide.md
  templates/observability-and-alerting/
  gates/check-observability-and-alerting.md

scripts/04.deploy/
  check-observability-and-alerting/
```

It records which scope operation or dependency behaviour needs a log, metric,
trace, health-state transition, receipt, or combination; safe correlation
identifiers; approved evidence location; access and retention policy; and the
state `covered`, `deferred`, or `excluded`. Alert records name the signal,
condition, persistence duration, severity, owner, safe next check,
deduplication behaviour, and verified recovery condition. A deferred record
requires an owner and follow-up; excluded means the scope does not use the
concern and cannot conceal a relevant gap.

<!-- deterministic-check: allow reason="This is a human-governed security design constraint; the future observability gate will enforce its concrete schema fields." -->
Operational evidence must contain no secret or PII by default. Any approved
exception requires a documented necessity, data minimisation, restricted
access, retention/deletion behaviour, auditability, and an explicit rule that
the data must not flow into broad logs, alerts, or high-cardinality metric
labels. Metrics use stable, low-cardinality safe labels; individual requests
belong in appropriately controlled logs or traces, not metrics.

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

Before a scope can claim package publication or target promotion is governed,
the harness must provide a Package Custody and Promotion Artifact Set:

```text
.agentic/04.deploy/
  standards/package-custody-and-promotion.md
  workflows/change-package-custody-and-promotion.md
  schemas/package-custody-and-promotion.v1.schema.yml
  schemas/package-custody-and-promotion.v1.guide.md
  templates/package-custody-and-promotion/
  gates/check-package-custody-and-promotion.md

scripts/04.deploy/
  check-package-custody-and-promotion/
```

It defines a provider-neutral chain from allowed source revision through build,
test, scan, attestation, approved package repository, immutable digest, and
publication receipt. It separates package approval from target approval: a
digest may be safely stored without being authorised for any target. A target
promotion records the same digest, source and destination targets, package
evidence, source-target verification where required, destination alignment,
approval route, and result. The standard prohibits a target from selecting a
mutable tag as package identity or rebuilding a promoted package.

The artifact set also separates build/publication, deployment, and verification
identities. Package policy records required checks, blocking outcomes,
target-specific stricter rules, and any exception's owner, expiry, evidence,
and follow-up. An agent may prepare an exception record but may not approve its
own exception or convert unavailable scan evidence into a pass.

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

Create a read-only evidence map for the existing `kanbien/staging` public
server as a reference and possible migration candidate. It identifies:

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
valid bootstrap-runtime scope and common invalid cases: absent index record,
missing owner, missing exclusion list, unresolved declaration path, and a
retired scope still selected by a target binding. Include an operation with no
promised outcome, an operation lacking implementation or test evidence, a
changed operation absent from the scope declaration, and a dependency pointing
to an unknown operation. Include an unclassified responsibility concern, an
unjustified exclusion, a deferred concern with no owner/follow-up, and a scope
that claims complete coverage despite an unresolved decision.

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

Create the Dependency Availability and Observation Artifact Set with fixtures
proving required, optional, and degraded behaviour; a missing lifecycle action;
a missing failure or recovery diagnostic; an absent health effect; a missing
metric/status signal; an intentional no-alert decision; a deferred alert with
owner/follow-up; an unowned deferred alert; and a proof reference that exposes
a prohibited sensitive value. Include an unknown request outcome without an
idempotent-retry or reconciliation path, a blind retry of uncertain work, and
<!-- deterministic-check: allow reason="This is a non-executable fixture requirement for a future checker; the future gate will own the deterministic assertion." -->
a recovery check that restores readiness without addressing uncertain work.
The first scope may record a concern as pending while its detailed declaration
is reviewed, but may not report it as governed or fully observed without a
valid record.

Create the Network Relationship Governance Artifact Set with fixtures proving
a valid private connection; a missing name-resolution policy; a missing
transport, application protocol, or port; an absent route or narrow
source/destination rule; a TLS-required relationship without server-identity
verification; a local equivalent that weakens the target requirement; a
diagnostic that reveals a prohibited sensitive network detail; and a target
proof reference that does not establish the declared relationship.

Create the Workload Identity and Access Artifact Set with fixtures proving an
approved workload identity and narrow action/resource access; a user-facing
authorisation rule incorrectly treated as an infrastructure permission; a
missing or exposed credential reference; a missing supply or refresh method;
an unowned rotation or revocation path; an execution, runtime, pipeline, or
dependency identity reused for the wrong job; authentication rejection without
safe failure behaviour; and a permission denial without an operation-specific
access requirement or proof.

Create the Health and Release Verification Artifact Set with fixtures proving
distinct liveness, readiness, and meaningful-operation checks; a candidate
response whose identity does not match the selected immutable digest; a rollout
without a declared healthy-capacity rule, startup grace period, or decision
deadline; a failure treated as acceptance; a rollback using a mutable tag
rather than a recorded prior digest; a restoration reported without health and
meaningful verification; and a receipt that exposes a prohibited sensitive
value or is stored in Git.

Create the Observability and Alerting Artifact Set with fixtures proving an
operation-linked safe log/metric/health/receipt record; a missing owner or
recovery condition for an alert; an alert without a persistence duration or
deduplication rule; a symptom incorrectly treated as a cause, or vice versa;
a deferred concern without owner/follow-up; an excluded concern that still has
an active dependency; a secret or PII field in operational evidence; a
high-cardinality or personal metric label; and a runtime-observability claim
without approved evidence location, access, retention, and deletion policy.

Create the Package Custody and Promotion Artifact Set with fixtures proving an
allowed source revision through build, test, scan, attestation, approved
repository, immutable digest, and publication receipt. Reject a mutable tag
presented as the selected package; a source or digest mismatch; missing test,
scan, or attestation evidence; unavailable scan evidence treated as a pass;
package approval mistaken for target approval; a package rebuilt during
promotion; a promotion without destination alignment or approval evidence; an
unseparated identity performing incompatible custody and deployment actions;
and an exception without an owner, expiry, evidence, or follow-up.

Add the target-local pipeline catalogue and its first package-publication
record for `.github/workflows/deploy-platform-shell-staging.yml`. The record
must state that it publishes a tested, scanned, immutable image digest to the
approved ECR repository and does not deploy that digest. It must link the
source-to-digest receipt, required test/scan/attestation evidence, approved
repository, and publication identity without granting target-deployment
authority. The bootstrap-runtime scope must reference this record as its
package-publication route.

Record the scheduled reconciliation workflow as a `drift-detection` pipeline
with state `blocked`, and record its planned separate artifact-stack
drift-evidence producer as the missing dependency. The catalogue must make
clear that the existing reconciler authenticates and reads safely but cannot
create the required fresh evidence itself.

Use that workflow and template to establish the first bootstrap-runtime scope.
It
must introduce the target-local scope index, foundation index,
`scopes/README.md`, foundation README, and bootstrap-runtime scope README. The
foundation index must record every bootstrap-runtime dependency that Phase 0 has
classified as foundation-owned, or record its status as deferred/unclassified
with an owner and follow-up path. After Phase 0 has inventoried every reference to
the current root-level `declaration-contract.yml`, migrate that contract into
the scope folder in one compatible, reviewed change. Update every repository
reference; do not leave two authoritative copies. A compatibility pointer is
permitted only when a verified consumer requires it.

The initial scope record must name its active state, owner, covered concerns,
explicit exclusions, operations and their promised outcomes, dependencies,
provider-selection status, contract path, and known proof paths. Its workload
binding and access requirements are added in the later target-binding phase;
the scope record must say that this proof is pending rather than pretending it
exists.

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
- the shared safe-diagnostic standard and its links to product and deployment
  controls, so error guidance is a governed cross-cutting requirement rather
  than prose scattered through integration code or operational notes;
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

Create and maintain the concern-control matrix above for the selected
`kanbien-core-platform` bootstrap scope. It must identify every relevant concern as planned,
explicitly out of scope, or needing detailed design before a later phase claims
full chain coverage.

**Deliverable:** cross-layer documentation-linkage and safe-diagnostic
standards, a repository-wide instruction inventory and migration ledger, and
an initially report-only linkage check.

**Exit criterion:** the first controlled bootstrap chain and its selected product modules
have a clear map from each mandatory instruction to its governance owner; each
README or document either links to that owner or has a recorded migration gap.
The concern-control matrix contains no silently unowned active concern.

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
- a safe diagnostic mapping and redaction test when it communicates with an
  external dependency or translates lower-level failures;
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
product-layer module-contract check, first applied to the modules selected by
the `kanbien-core-platform` bootstrap design. The existing public-server
composition is reference evidence only, not an implied selection.

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
- the boundary at which dependency failures are translated into the shared
  safe diagnostic contract and startup/readiness/request behaviour;
- expected compiled command;
- required local proof; and
- owner.

The first core-family record uses the `kanbien-core-server.main.ts` source
name. Future core-family runnable programs follow
`kanbien-core-<role>.main.ts`; non-runnable composition helpers omit the
`.main.ts` suffix.

The registry is necessary because role, intended command, and proof cannot be
reliably inferred from a TypeScript filename alone.

**Deliverable:** an entrypoint schema, field guide, registry, and static
reporter for the runnable-program candidates. The first target binding is
created only after the `kanbien-core-platform` target design is approved.

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

**Exit criterion:** the selected bootstrap program’s source, compiled output, Docker
default command, and package smoke proof agree.

### Phase 6 — Bind programs to target workloads

**Question answered:** Which target workload runs which approved program?

Add a target-local workload binding beside the approved `kanbien-core-platform`
target profile. A
binding refers to a runnable-program identifier and names:

- the target workload/service or one-pass task;
- workload runtime type, such as ECS service, Lambda function, or one-pass
  task;
- selected image contract;
- configuration/declaration-contract scope;
- selected provider adapters and the foundation or scope-owned resource IDs
  that fulfil their dependencies;
- selected network-relationship records and their authoritative provider
  declaration references;
- attached execution and runtime roles, plus each access requirement's policy
  declaration and bounded action/resource reference;
- each dependency authentication method, safe credential or identity reference,
  supply/refresh method, rotation/revocation owner, and safe authentication
  failure proof;
- expected dependency-availability behaviour and safe failure/recovery
  diagnostic, health-effect, metric/status, alert-policy, and proof references
  for startup, readiness, real requests, and recovery;
- liveness, readiness, and candidate-specific meaningful-verification
  operations; rollout/healthy-capacity and timing policy; candidate acceptance
  and rejection conditions; receipt route; prior immutable rollback target; and
  restoration proof; and
- applicable observation-contract records, or explicit deferred/excluded
  status with owner and follow-up; and
- target owner.

AWS-specific command details remain in the existing CloudFormation source. The
binding is provider-neutral and the checker compares it to the provider
definition; it does not replace that definition. A provider selection is valid
only when its adapter, typed configuration, target resource, network/secret
reference where applicable, role policy, migration/rollback treatment, and
proof are all linked.

**Deliverable:** a bootstrap-runtime workload binding and static comparison
with its approved provider definition. The existing task/service definition is
reference evidence only; it is not an implied binding for the new target.

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
`provider-selection-incompatible`. It also reports a missing diagnostic
contract, recovery observation, health effect, metric/status signal, alert
decision, or proof where a declared dependency has no safe, actionable failure
path; an unknown request outcome without reconciliation treatment; and a
network relationship missing a declared or proved name-resolution, protocol,
port, route, narrow rule, TLS policy, local equivalent, or target/runtime path;
or a workload identity/access record missing a supply, rotation, least-
privilege, operation, or safe authentication-failure link.
It also reports a health/release declaration without distinct liveness,
readiness, and meaningful-operation proof; candidate-identity comparison;
rollout deadline; safe receipt route; immutable rollback target; or restoration
verification.
It reports an active scope behaviour without the required observation record,
or a record with unsafe evidence data, missing location/access/retention,
missing alert owner/recovery treatment, invalid correlation identifier, or an
unjustified deferred/excluded state.
It also reports a package route without source-to-digest provenance, required
test/scan/attestation evidence, an approved repository, immutable selected
digest, or safe publication receipt; a target binding that selects a mutable
tag; a promotion that rebuilds rather than transfers the approved digest; a
package approval substituted for destination alignment or target approval; an
unavailable required scan treated as successful; or an exception lacking its
owner, expiry, evidence, or follow-up.

**Deliverable:** human-readable and machine-readable report modes, fixtures,
and a smoke test. It remains repository-only and makes no AWS call.

**Exit criterion:** the first controlled target chain is reported consistently from the
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
The preflight consumes the chain-check result and safely confirms live facts.
It is strictly read-only: detection never implies remediation, remediation
never implies deployment, and only an approved delivery route may mutate a
target.

The comparison keeps three distinct records:

```text
declared desired state
→ reviewed repository intention for the selected scope and candidate

known live baseline
→ last verified safe release and target state, referenced by operational proof

fresh actual observation
→ time-limited safe facts read from the provider now
```

An approved transition from a healthy baseline digest to a selected candidate
is not drift merely because the target has not yet run the candidate. Drift is
an unexplained difference between declared expectation, the approved transition
state, and actual observation. The preflight must distinguish `match`,
`mismatch`, `insufficient-evidence`, and explicit `not-applicable`; only all
required `match` results allow the delivery pipeline to proceed.

An approved pending transition is comparison context, not a fifth assertion
verdict: before candidate deployment, the previous accepted digest may still be
the expected actual state. After deployment, only an accepted candidate-specific
live-verification receipt may advance the known healthy baseline. A rejected or
unproved candidate never becomes baseline merely because it was selected,
started, or briefly answered a health request.

The preflight safely confirms assertions including:

- destination identity and selected workload;
- image identity and approved deployment route;
- selected provider, foundation-resource identity, workload role, and narrow
  access-policy facts;
- network-relationship facts: approved workload and destination, safe
  resolution, protocol/port, private/public boundary, narrow rule, and TLS
  policy where applicable;
- non-secret configuration and secret-name presence, workload identity/role
  references, and safe credential supply/rotation facts;
- permissions, dependencies, health, and rollback configuration;
- candidate-specific verification, receipt-route, and immutable rollback facts;
- safe diagnostic categories, health effects, metric/status and alert-policy
  references, and safe evidence for target mismatches or unavailable declared
  dependencies;
- freshness and drift; and
- assertion verdict, safe observed fact, expiry, evidence reference, and
  bounded next check for every non-match.

It has two required use points with the same comparison contract:

1. **Early alignment:** compare a fresh target snapshot with the selected
   repository declaration before implementation is considered target-ready.
   A still-valid cached result may be used only within its declared expiry.
2. **Pre-deploy refresh:** re-run the comparison immediately before target
   mutation so a changed account, workload, permission, setting, dependency,
   health policy, or rollback route cannot be hidden by an old result.

The resulting evidence sequence is: approved candidate and declaration,
fresh pre-deployment observation, approved delivery action, candidate-specific
live verification, then acceptance or rejection receipt. Only acceptance links
the selected immutable digest and its proved target facts to the next baseline;
the detector itself never repairs a mismatch or initiates another deployment.

No secret values may be read or reported. The future AWS read adapter remains
subject to the existing AWS workflow and approval boundary. It uses a dedicated
least-privilege read identity which may inspect only the safe facts needed by
the declared assertions and write safe evidence; it cannot deploy, alter
resources, read secret values, or widen its own access. If an assertion cannot
be established within that boundary, its verdict is `insufficient-evidence`.

The initial core-server scope applies only its relevant assertions: target and
workload identity, approved delivery route, declared configuration/role names,
health/release-verification/rollback prerequisites, and evidence freshness.
Dependency-specific assertions remain explicitly excluded until their scope
selects a dependency; runtime observability assertions remain deferred until
their approved evidence route exists.

**Deliverable:** a provider-neutral input/output contract and an AWS read-only
adapter design; no target mutation.

**Exit criterion:** the preflight can distinguish a repository coverage gap
from a live-target mismatch.

### Phase 10 — Stage enforcement and broaden scope

<!-- deterministic-check: allow reason="The enforcement threshold is a phased human risk decision until the reviewed report-only controls exist and can become gates." -->
**Question answered:** When should a missing link block work?

Adopt controls in order:

1. report-only for the `kanbien-core-platform` bootstrap scope;
2. required on changes to its entrypoint, image, target, or deployment
   declaration;
3. required before packaging, with a fresh target-alignment refresh required
   before deployment;
4. require every new or changed platform module, configuration concern,
   adapter, runnable program, resource, role, workload, or pipeline to satisfy
   its product-layer contract and identify its affected scope and foundation
   records before completion; where no deployment scope is affected, require a
   recorded reason instead of an irrelevant provider check;
5. require each changed or newly introduced scope operation to have a declared
   promised outcome and implementation/test evidence; require each dependency
   to reference the operation whose behaviour it affects;
6. require each affected concern to have a matrix row with an approved
    structure, quality obligation, and instruction owner, or to remain an
    explicitly recorded design gap that blocks any claim of full coverage;
7. extend coverage one reviewed area at a time: foundation control domains,
   worker/queue execution, relay, PostgreSQL, identity/access, public ingress,
   observability/alerting, and any other active capability revealed by Phase 0;
8. make an aggregate target result possible only after the scope and foundation
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

<!-- deterministic-check: allow reason="These are human design approvals that establish scope, lifecycle intent, and acceptable architecture before later scripts can validate the resulting declarations." -->
1. Confirm the `kanbien-core-platform` bootstrap scope is the first controlled
   vertical slice; retain `kanbien/staging` as reference only.
2. Confirm that the first slice must prove both clean creation from an absent
   baseline and one controlled update from accepted release A to candidate B.
   Confirm the private internal-verifier boundary before any target-design
   package selects an AWS implementation mechanism.
3. Confirm the scope criteria and the target-local scope-folder shape before
   building the Scope Governance Artifact Set.
<!-- deterministic-check: allow reason="Registry adoption depends on human assessment of which deployment facts cannot safely be derived from source code; a later validator enforces the approved registry." -->
4. Decide whether a machine-readable runnable-program registry is acceptable
   when role and proof cannot be derived from code.
5. Choose whether the Phase 2 documentation-linkage rule belongs in the
   existing harness placement standard or in a new cross-layer standard.
6. Agree the threshold at which report-only checks become blocking gates.
7. Review the Phase 0 reference evidence map and the separately proposed
   `kanbien-core-platform` target design before creating any new declarations.
8. Review the proposed scope catalogue and the compatibility path for adding
   the target-local scope index before adding a second active scope.
9. Confirm the foundation-resource classification criteria, index shape, and
   provider-identity fields before creating target foundation records.
10. Confirm the provider-selection compatibility and access-requirement fields
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

For the `kanbien-core-platform` bootstrap scope, a reviewer can start with one program identifier and
find, by command and source path, its platform inputs, adapter choice,
capability/provider/resource classification, compiled image command, target
workload/runtime, required non-secret configuration, attached roles and narrow
access requirements, scope operations and their promised outcomes, dependency
declarations linked to those operations, local/package proofs,
target-alignment result, target/run proofs, and safe diagnostics for failures
at each boundary. Any missing or contradictory link is reported before a
deployment is treated as ready.

The reviewer can also prove the full narrow lifecycle without relying on an
existing staging resource: the declared target begins absent and conflict-free;
release A establishes the first accepted baseline; a separately declared
immutable release B is compared against that real baseline and verified; and a
rejected B preserves the prior baseline rather than creating an automatic
redeployment loop.
