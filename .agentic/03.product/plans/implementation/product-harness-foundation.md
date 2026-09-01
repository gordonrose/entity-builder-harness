<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.product-harness-foundation
version: 1
status: active
layer: 03.product
domain: governance
disciplines:
- agentic
- architecture
- security
kind: plan
purpose: Define the staged plan for a product harness that enables apps and products to adopt the platform runtime safely and consistently.
portability:
  class: source-only
  targets: []
used_by:
- id: product.readme
  path: .agentic/03.product/README.md
-->
# Product Harness Foundation Plan

## Goal

Create the governed foundation for future product apps to consume the platform
through a repeatable, validated path. The harness must make platform adoption,
product composition, secure defaults, and capability-specific decisions
explicit without making app internals, cloud providers, or tenant data part of
the platform contract.

This is a planning and governance artifact. It does not authorize implementation
of a real product app, cloud resource, tenant policy store, provider adapter, or
production deployment.

## Why This Plan Exists

The platform runtime plan proves the platform shell with `apps/platform-smoke`.
It deliberately does not define how a real app should choose features,
persistence, integrations, tenant-aware policy, schemas, or product composition.

The next architectural concern is a product harness: the agent-facing
governance, defaults, templates, and checks that let an app consume the proven
platform contract correctly. It must be built incrementally from actual app
consumer needs, rather than by guessing a final application architecture.

## Locked Boundaries

- `packages/core` defines provider-neutral nouns and ports; it does not own
  product roles, tenant memberships, security policy engines, provider clients,
  or cloud resources.
- `platform/contracts` is the app-facing runtime contract. Platform composition
  roots may consume public app mounts; ordinary platform modules must not import
  app feature, repository, route-handler, job-handler, or domain internals.
- `apps/**` owns product behavior, feature organization, routes, jobs,
  permissions, app config meaning, migrations, resource authorization, and
  tenant-specific product behavior.
- `products/**` composes public app modules into named products. It does not
  contain cloud account, region, DNS, secret value, provider-resource, or image
  selection data.
- `.agentic/03.product/**` governs how agents create, change, validate, and
  compose product apps. It is not a runtime policy engine and must not hold live
  tenant memberships, raw credentials, or cloud configuration.
- `infra/04.deploy/**` and `.agentic/aws/**` own provider selection, resource
  provisioning, IAM, KMS, TLS, deployment target profiles, and cloud mutation.

## Consumer Promise

When the foundation is implemented, an agent receiving a request such as
"create an app", "add a feature", or "add persistence" should be able to:

1. identify the appropriate product-harness workflow;
2. determine which platform capabilities are available, experimental, or
   unavailable;
3. apply an approved baseline rather than rediscovering routine decisions;
4. collect the product-specific and tenant-specific decisions that cannot be
   safely defaulted;
5. create only the public app surfaces and internal structures the selected
   capability requires;
6. run executable checks that prove platform adoption and app-owned behavior;
7. stop with an explicit gap when requested behavior requires an unavailable
   platform capability, provider choice, deployment mutation, or ungoverned
   product decision.

## Initial Capability Maturity Model

The harness must publish an explicit capability inventory before it produces
templates or defaults. Each capability is classified as `available`,
`planning-only`, `experimental`, or `unavailable` with evidence and a required
workflow.

Initial planning assumptions are:

| Capability | Current adoption position | Harness consequence |
| --- | --- | --- |
| Public app mount, manifest, routes, permissions, jobs, config, health, lifecycle, and local mount tests | Available through the platform shell proof | May be covered by the first app-adoption workflow and template. |
| Product composition through public app surfaces | Available for the platform-shell proof | May be validated without importing app internals. |
| JWT-backed route authentication and mapped route permissions | Available for local shell proof | May be used only within the documented provider/config and test boundary. |
| Verified principal and tenant context in real app handlers | Not yet a general live app-consumption guarantee | Do not make a tenant-aware handler template claim this is available. Record a platform gap first. |
| Resource, relationship, and attribute-based authorization | Core vocabulary exists; a general runtime path and product policy engine are not yet proven | Do not scaffold regional/team membership policy as a working default. Require a bounded product/platform implementation plan. |
| Persistence, files, events, queues, and external integrations | Core contracts exist, but provider/runtime availability varies | Each requires its own capability playbook and an explicit availability check. |
| Tenant policy storage and membership administration | Product behavior, not a core or harness data store | Govern the design and validation path; do not put live tenant values in `.agentic`. |

The inventory is a required first implementation slice because it keeps later
workflows honest about what an app can actually consume.

## Defaults And Decisions Model

Every product-harness rule must be classified before it is offered to app
builders.

| Class | Meaning | Example |
| --- | --- | --- |
| Invariant | Cannot be bypassed without a governed exception | An app exposes only an approved public mount; app code does not import cloud SDK clients directly. |
| Versioned baseline | A product explicitly adopts a reusable default profile | Security baseline v1 requires safe logging, classification of sensitive data, and a declared auth posture. |
| Product decision | Selected once for a named product | Which apps form the product; product-level role groupings; export/audit policy. |
| App decision | Chosen by the owning app or feature | Permission vocabulary, data classification, route/job behavior, app-owned migration intent. |
| Tenant restriction | Runtime policy that may tighten a product policy | EU residency, regional access scope, or dedicated encryption-key reference. |
| Deployment decision | Chosen in a client/environment target profile | Cloud provider, account, region, concrete KMS key, TLS certificate, network, and provider adapter. |

Tenant restrictions must not silently weaken a product's adopted baseline.
Any permitted relaxation requires an explicit exception, owner, reason, expiry,
and evidence path. Tenant policy documents or runtime records may contain
references, classifications, and policy facts, but never raw secrets or keys.

## Planned Harness Surfaces

The foundation should grow into focused, small artifacts rather than one
catch-all default workflow.

```text
.agentic/03.product/
  plans/implementation/              durable coordination plans
  standards/                          app/platform adoption and policy rules
  workflows/                          task-specific agent paths
  templates/                          minimal validated starter artifacts
  checklists/                         human-readable review evidence
```

The exact folder set and file names are deferred until the capability inventory
is approved. Likely initial artifacts are:

- an app/platform adoption standard;
- a security-baseline adoption standard;
- a workflow for creating a platform-consumable app;
- a workflow for composing a product from public app surfaces;
- a capability inventory or registry with maturity and evidence;
- a minimal app template; and
- validators for app manifests, mount declarations, policy adoption, and
  product composition.

The existing placeholder default workflow must not become the implementation
path for these concerns. Replace or retire it only after focused workflows are
implemented and linked from the product workflow index.

## Capability Playbooks

The harness will add a playbook only when a real app consumer needs that
capability. A feature does not automatically require every playbook.

| Playbook | App/product ownership | Required harness coverage |
| --- | --- | --- |
| Create app | Public mount, manifest, initial app identity | Platform contract selection, baseline adoption, app mount/manifest checks, local proof. |
| Add feature or use case | Product behavior and internal organization | Feature boundary, dependencies, tests, capability selection, and app-owned error behavior. |
| Add schema and validation | Product request, domain, and persistence shapes | Boundary validation, compatibility/versioning decision, generated-code policy where applicable, and rejected-input tests. |
| Add route | Route semantics and handler | Auth posture, declared permissions, validator, safe response/error behavior, observability, and mounted-route proof. |
| Add job or event | Work meaning, payload, and app handler | Payload validation, idempotency, retry/dead-letter decision, correlation/tenant facts, and worker proof. |
| Add persistence | App schema, repositories, queries, and ordered migrations | Tenant scoping, transaction/concurrency decision, migration review, failure behavior, and integration proof. |
| Add integration | Product use of a provider-neutral port | Adapter boundary, config/secret references, timeout/retry/error mapping, health/observability, and provider-availability check. |
| Add tenant-scoped authorization | Product membership, role, group, scope, and resource policy | Separation of principal, tenant, permissions, relations, attributes, policy decision, deny proof, and audit evidence. |
| Compose product | Product app list and product-level policy choices | Public-surface-only composition, permission/reference validation, profile adoption, and no target-specific deploy values. |

Each playbook must state when to use it, ownership boundaries, defaults,
mandatory decisions, required checks, output, and stop conditions.

## Security Baseline Direction

The first baseline should be declarative and versioned. It should state
requirements, not hardcode an encryption provider or cloud resource.

Initial policy topics to evaluate include:

- authenticated/public route classification and permission declarations;
- safe structured logging and redaction;
- classification of financial, tenant, personal, credential, and other
  sensitive data;
- encryption-in-transit and encryption-at-rest requirements expressed as
  product needs, with provider proof delegated to deployment targets;
- tenant isolation and resource-scope authorization expectations;
- audit expectations for high-risk actions such as exports or permission
  changes; and
- exception and policy-version migration rules.

An app or product adopts a named baseline version. A tenant may tighten it;
provider details such as AWS KMS keys, certificates, and IAM policies remain
deployment concerns.

## Implementation Sequence

### 0. Record This Foundation Plan

Status: complete when this artifact is present, reviewed, and linked from the
product layer index or an approved successor.

Acceptance:

- The plan is a standalone `03.product` implementation artifact.
- It separates governance, runtime code, tenant policy, and deployment
  ownership.
- It names the deferred work rather than presenting the product harness as
  already implemented.

### 1. Build The Capability Inventory

Create a machine-readable or otherwise validated inventory of app-consumable
platform capabilities, maturity, evidence, owner, and required workflow.

Acceptance:

- Every initial app template default references an inventory entry.
- An unavailable capability produces an explicit gap, not a fabricated
  template or fallback.
- The inventory distinguishes core contract availability from live platform
  runtime availability.

### 2. Define The App/Platform Adoption Standard

Specify the stable public app boundary and the minimum proof for a new app.

Acceptance:

- The standard requires an approved public mount and declarative manifest.
- It preserves app-owned internal organization and forbids platform imports of
  app internals.
- It defines required app identity, config, permissions, health, lifecycle,
  route/job, and test declarations only when the selected capability needs
  them.
- It names the product-composition and deployment handoff boundaries.

### 3. Define Security-Baseline Adoption

Define how a product adopts a versioned security baseline and how apps declare
their additional data, access, audit, and tenant-scoped requirements.

Acceptance:

- The baseline is one canonical source of reusable policy requirements.
- Product adoption pins a version rather than inheriting unreviewed changes.
- Tenant restrictions can tighten but not silently weaken baseline rules.
- No policy artifact contains raw credentials, keys, or provider resource
  configuration.

### 4. Add Focused Workflows And Checklists

Start with `create platform app` and `compose product`; add other playbooks only
when a pilot requires them.

Acceptance:

- Each workflow has explicit inputs, steps, output, required evidence, and
  stop conditions.
- Workflows direct agent changes to the right owner layer.
- The former placeholder workflow is no longer offered for real work.

### 5. Add Executable Validators Before Generators

Implement the smallest validators that prove public app mounts, manifests,
permission declarations, baseline adoption, and product composition.

Acceptance:

- A template cannot be accepted merely because it resembles an example.
- Validators reject platform imports of app internals and target-specific deploy
  data in product manifests.
- Validators expose gaps where platform support is unavailable.

### 6. Add Minimal Templates

Create a minimal new-app template only after validators establish the contract.

Acceptance:

- The template contains no fake persistence, tenant, provider, or security
  implementation that platform does not actually support.
- It is deliberately smaller than a real product app and remains internally
  flexible.
- It passes the app-adoption and composition validators unchanged.

### 7. Prove The Harness With One Pilot App

Use one bounded real app as a consumer of the harness while keeping
`apps/platform-smoke` as the platform canary.

Acceptance:

- The pilot proves the new workflows, defaults, templates, and checks through
  an actual consumer journey.
- Gaps found by the pilot update the capability inventory and focused playbooks
  rather than being hidden in app-specific exceptions.
- Any new platform contract need is evaluated separately from app feature work.

## Non-Goals

- Do not decide a final universal app folder structure.
- Do not embed provider SDKs, AWS resources, IAM, DNS, secrets, KMS keys, or
  environment values in app or product harness artifacts.
- Do not make `.agentic/03.product` a tenant-data or runtime-policy store.
- Do not replace platform contract tests with templates or agent instructions.
- Do not represent a product deployment target such as `kanbien/staging` as a
  product.
- Do not start a real product feature solely to prove a harness document.

## Stop Conditions

Stop and record an explicit gap when:

- a requested playbook depends on a platform capability whose maturity is not
  `available`;
- work requires a provider, account, region, deployment target, secret,
  network, or cloud mutation;
- a policy would require live tenant memberships, product roles, or resource
  inheritance rules that have no approved product policy model;
- implementation would alter `packages/core` or the public platform contract
  without a bounded owning change plan and checks; or
- a proposed default would silently weaken a baseline or hide a required
  product/tenant decision.

## Validation Plan

For this planning artifact:

- validate the artifact metadata header;
- verify Markdown and repository whitespace with `git diff --check`; and
- review the plan against the product layer boundary, app layer rules, core
  contract rules, and the platform runtime implementation plan.

For later implementation slices:

- run the narrow validators introduced by the slice;
- update the capability inventory evidence;
- run contract, boundary, mount, integration, and product-composition tests
  required by selected playbooks; and
- regenerate recognition sources if a new governed artifact requires it.

## Deferred Decisions

- The canonical format and runtime location for product policy profiles.
- The tenant-policy administration model and persistence store.
- The policy-engine or authorizer implementation for relationship-,
  attribute-, and tenant-scoped authorization.
- The first approved persistence, event, file-storage, and integration adapter
  set for real apps.
- The first pilot app and its feature scope.
- Exact template, workflow, validator, and script path names after capability
  inventory review.

## Current Status

Planning baseline recorded. Product-harness implementation is intentionally
deferred until the platform capability inventory and an approved first consumer
slice are selected.
