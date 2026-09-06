<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.product-harness-foundation
version: 7
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
- A product capability must remain independent of any one interaction channel.
  Traditional web UI, chat, and voice may each become consumers of the same
  governed capability, identity, authorization, validation, audit, and
  consequence-control path. A channel must not become a second backend with
  its own business or access-control rules.
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
workflow. Its production-capable availability claims must be reconciled with
the reference-target maturity states in
`production-reference-target-baseline.md`; a locally proven platform seam is
not automatically a production default for app builders.

Initial planning assumptions are:

| Capability | Current adoption position | Harness consequence |
| --- | --- | --- |
| Public app mount, manifest, routes, permissions, jobs, config, health, lifecycle, and local mount tests | Available through the platform shell proof | May be covered by the first app-adoption workflow and template. |
| Product composition through public app surfaces | Available for the platform-shell proof | May be validated without importing app internals. |
| JWT-backed route authentication and mapped route permissions | Available for local shell proof | May be used only within the documented provider/config and test boundary. |
| Verified principal and tenant context in real app handlers | Not yet a general live app-consumption guarantee | Do not make a tenant-aware handler template claim this is available. Record a platform gap first. |
| Resource, relationship, and attribute-based authorization | Core vocabulary exists; a general runtime path and product policy engine are not yet proven | Do not scaffold regional/team membership policy as a working default. Require a bounded product/platform implementation plan. |
| Persistence, files, events, queues, and external integrations | Core contracts exist, but provider/runtime availability varies | Each requires its own capability playbook and an explicit availability check. |
| Interaction channels: web UI, chat, and voice | The web/API-oriented platform shell is the current first consumer shape. Chat and voice have no approved general runtime, provider, conversation model, or repository convention. | Treat chat and voice as planning-only consumers of future capability contracts. Do not present a web-only feature template as a universal interaction architecture. |
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

The approved production-reference baseline has now introduced one focused
standard: `standards/identity-security-baseline.v1.md`. It records an initial
identity-security floor and adoption rules; it is not a generic feature
template and does not claim a human identity implementation exists.

The remaining folder set and file names are deferred until the capability
inventory is approved. Likely next artifacts are:

- an app/platform adoption standard;
- a broader security-baseline adoption standard, extending the identity
  baseline only when a real capability requires it;
- a workflow for creating a platform-consumable app;
- a workflow for composing a product from public app surfaces;
- a capability-first interaction-channel standard and, when a real consumer
  requires it, a focused web, chat, or voice adaptation playbook;
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
| Add interaction channel | A web UI, chat, or voice adaptation of an existing product capability | Channel declaration, verified identity/session context, same capability authorization path, untrusted-input handling, confirmation for consequential actions, privacy/retention decisions, accessibility or human handoff, and channel-specific proof. |
| Compose product | Product app list and product-level policy choices | Public-surface-only composition, permission/reference validation, profile adoption, and no target-specific deploy values. |

Each playbook must state when to use it, ownership boundaries, defaults,
mandatory decisions, required checks, output, and stop conditions.

## Future Capability Declaration Direction

An app's route, job, health, configuration, and lifecycle registrations state
how it participates in the platform runtime. They do not fully describe a
product capability. Before the harness generates real feature work, define a
small, versioned capability declaration/profile that brings together the
capability's stable meaning and references to the decisions it requires. Its
repository location and exact machine-readable shape remain deferred until a
bounded first consumer is selected.

The declaration must be a reference-and-allowlist surface, not a second copy of
business logic or an unbounded metadata document. A capability should be able
to declare only the facets it uses:

| Facet | What the declaration contributes | What it must not become |
| --- | --- | --- |
| Identity and purpose | Stable capability ID, owner, version, concise human/machine-readable description, and intended outcome. | A prompt that grants authority or an unbounded product specification. |
| Inputs and interfaces | References to approved schemas, errors, route/job/event registrations, and supported interaction-channel adapters. | A second route handler, queue worker, or channel-specific business path. |
| Authorization and consequences | Permission, tenant/resource-policy, confirmation, approval, and delegation requirements by reference. | Live role/group membership, a policy-engine implementation, or implied authority from a chat/voice prompt. |
| Data and lifecycle | Data classifications plus retention, residency, persistence, and integration requirements by reference. | Raw tenant data, credentials, provider settings, or deployment resources. |
| Accountability and observability | Separate audit, security-signal, and operational-observability profile references. Each profile classifies its allowlisted facts, permissible values, bounds/cardinality, audience, and retention/residency justification. | A free-form log/audit payload or a duplicate sensitive-data store. |
| LLM or agent discovery | A bounded description of the capability's user-facing intent, supported input/output form, and approved invocation path. | Tool permission, direct provider access, hidden instructions, retrieved-content trust, or a bypass of independent authorization and validation. |

The capability declaration belongs to the app/product-harness boundary, not to
the generic `platform/contracts` runtime registration surface. Platform
contracts remain narrow and reusable: a route needs its handler and runtime
requirements; a capability profile explains why the route, job, or channel
exists and which approved policies apply. A future registry may link the two
for validation, but one must not silently generate or override the other.

An LLM-facing description is discovery metadata only. It can help a governed
assistant explain or select a capability after permission-scoped retrieval, but
the capability boundary must still authenticate the caller, resolve tenant and
resource scope, validate input, enforce approval rules, and authorise every
tool or side effect. The description must not contain secrets, raw prompts,
tenant data, signed URLs, or instructions that let a model infer authority.

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

## Interaction Channel Direction

The original web/API-oriented implementation pipeline remains valuable, but it
is a **first consumer**, not the definition of a feature. The product harness
must treat a feature capability as the stable centre, then let approved
interaction-channel adapters invoke it.

For every supported channel, the path is the same in principle:

1. The channel adapter validates and normalises web, chat, or voice input.
2. The shared feature capability applies identity, tenant, authorization, and
   policy.
3. The channel adapter renders an appropriate response or a human handoff.

The exact repository folders and transport contracts are deliberately deferred.
When the first real consumer is chosen, the harness should make three scopes
visible rather than mixing them:

| Scope | Owns | Must not own |
| --- | --- | --- |
| Feature capability | Product command/query meaning, validation, authorization request, tenant/resource scope, outcome, and audit requirement. | Browser components, prompt wording, speech-provider clients, or channel session details. |
| Channel adapter | Web request/UI mapping, conversational turn handling, or voice input/output normalisation and rendering. | A bypass of feature authorization or a separate copy of business logic. |
| Channel/session policy | Verified identity association, consent, transcript/audio classification, retention, streaming/session limits, confirmation/handoff, and accessibility. | Authority inferred merely from natural-language text, model output, a transcript, or a caller-provided tenant value. |

Chat messages, voice transcripts, retrieved content, and model output are
untrusted input. A conversational or voice interface may help a user formulate
an intention, but it must never turn that text directly into a privileged tool
or database action. The verified principal, tenant context, permission and
resource checks, approval rules, and audit path remain independently enforced
at the shared capability boundary.

Before the harness offers a channel adaptation, it must ask:

1. Which existing capability is this channel consuming, and is it actually
   available in the capability inventory?
2. How is the human or machine identity verified and bound to the conversation
   or voice session?
3. Which data is retained—text transcript, audio, generated response, or none—
   and what classification, consent, residency, encryption, access, and
   retention rules apply?
4. Which actions need an explicit confirmation, a human handoff, or a
   non-conversational review screen before any side effect occurs?
5. How will the channel prove the same tenant/resource authorization and
   denied behaviour as its web/API counterpart?

Do not build generic voice, chat, agent, telephony, speech-to-text,
text-to-speech, transcript store, model, or prompt infrastructure merely to
reserve a future option. Start with one bounded consumer and add only the
channel contracts, adapters, and policies it demonstrably requires.

## Public Navigation And Addressing Direction

A public browser URL is a durable product interface, not a reflection of the
repository, frontend component tree, or deployment implementation. The harness
must distinguish three related but separate concepts:

| Concept | Meaning | Example |
| --- | --- | --- |
| Public navigation address | The stable browser location and user-facing information architecture. | `/finance/invoices/INV-123` |
| Backend API route | The HTTP interface through which a web adapter or another machine client obtains data or requests an action. | `POST /api/v1/invoices/INV-123/export` |
| Capability | The shared product meaning, validation, authorization, and consequence boundary that a web, chat, voice, worker, or CLI consumer may invoke. | `invoice.export` |

Public URL names may use deliberate, outward-facing product classifications
such as product area, product concept, resource, view, and user-visible
workflow step. Those names must be stable product language rather than
transient app, module, page, component, provider, or source-folder labels.
Changing the implementation behind a bookmarked address must not require
changing the address.

The initial policy direction is:

- the deployment target owns environment origins, DNS, TLS, and custom-domain
  resources; environment is not a default browser-path segment;
- product composition owns the top-level public navigation namespaces and
  detects collisions between app contributions;
- an app/feature may contribute a view or capability mapping within an approved
  product namespace, but must not claim another app's namespace;
- web adapters map a public address to an approved view and then invoke the
  shared capability path; they do not create a second business or
  authorization path;
- browser paths use stable, user-understandable product areas and resources;
  query fields are limited to safe, bounded view state;
- URLs must not contain credentials, tokens, raw personal or tenant data,
  permissions, roles, group assignments, or other authority claims;
- navigation never confers authority. Every request still resolves verified
  identity and tenant context, then enforces permission and resource policy;
  and
- a navigation address may display an action-review view, but an HTTP safe
  method must not itself perform a consequential action.

Tenant addressing—custom domain, tenant subdomain, or tenant path prefix—is a
deliberate future product and deployment decision. It affects identity,
cookies, TLS, support, branding, and trusted tenant resolution; a
tenant-looking host or path value is never authorization evidence.

Do not add a generic frontend router, universal URL package, or mandatory
folder grammar now. When the first real web consumer is selected, define a
versioned public-navigation declaration that references product namespace,
view, capability, access classification, and supported channel. Add
product-composition validation for duplicate or reserved public paths,
compatibility/redirect expectations for changed bookmarked addresses, and a
focused web-adaptation workflow. Codify the resulting enforceable policy as a
source-reviewed product concern rather than embedding it in the current
backend route contract.

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

### 3a. Define The Capability-First Interaction Boundary

Before a web template is described as the default feature shape, define how a
feature capability can be consumed by more than one interaction channel without
duplicating business logic or weakening controls.

Acceptance:

- The app/feature guidance distinguishes capability semantics from web, chat,
  and voice adaptation.
- The capability inventory represents chat and voice as unavailable or
  planning-only until an approved runtime and first consumer provide evidence.
- The future channel playbook requires verified identity, tenant/resource
  authorization, untrusted-input handling, confirmation/handoff decisions,
  audit expectations, and privacy/retention decisions appropriate to the
  channel.
- Repository conventions keep channel adapters discoverable without locking a
  universal feature folder structure before a consumer proves it.
- A web UI implementation pipeline remains supported as a first consumer, but
  does not define a second authorization or business-logic path.

### 3b. Define The Capability Declaration Profile

Before feature generators, LLM-facing discovery, or channel adapters create
capability artifacts, define the versioned declaration/profile that connects
app-owned capability meaning to its approved runtime registrations and policy
references.

Acceptance:

- The profile has an explicit version, stable capability identity, owner, and
  bounded purpose description.
- It references rather than duplicates schemas, routes, jobs, persistence,
  integrations, permissions, tenant/resource policy, and channel adapters.
- It declares separate audit, security-signal, and operational-observability
  profiles with allowlisted safe facts; an absent profile is deliberate. Each
  selected profile records field purpose, classification, permissible values,
  bounds/cardinality, audience, and retention/residency justification.
- Any LLM/agent discovery fields are explicitly non-authoritative and cannot
  confer access, tool permission, tenant scope, or side-effect authority.
- Validators reject secrets, raw tenant data, provider configuration, unbounded
  metadata, undeclared runtime registrations, and references to unavailable
  platform capabilities.
- The first real consumer determines the repository location and exact schema;
  do not create an empty universal capability package in advance.

### 3c. Define The Public Navigation Declaration And Web Addressing Policy

Before a web template, browser router, or product composition generator claims
to provide stable public pages, define the versioned declaration that maps
product namespaces and views to approved capabilities.

Acceptance:

- The declaration distinguishes public navigation addresses, backend API
  routes, and shared capabilities.
- Product composition owns top-level public namespaces and rejects duplicate
  or reserved paths across app contributions.
- Address names are stable product language and do not expose implementation
  topology, credentials, roles, permissions, group membership, or sensitive
  tenant data.
- It records which query values are safe view state, which identifiers are
  suitable for public addressing, and the required redirect or compatibility
  treatment for a changed bookmark.
- It requires a deliberate tenant-addressing model and rejects treating a
  supplied host/path value as authorization evidence.
- The first web-adaptation playbook proves that navigation does not bypass
  shared identity, tenant, authorization, validation, confirmation, audit, or
  consequence controls.

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
- The first approved chat or voice consumer, its provider/runtime, identity and
  session model, transcript/audio handling, retention/residency policy, and
  human-handoff model.
- Exact template, workflow, validator, and script path names after capability
  inventory review.

## Current Status

Planning baseline recorded. Product-harness implementation is intentionally
deferred until the platform capability inventory and an approved first consumer
slice are selected.
