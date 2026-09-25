<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.teaching-notes.0002-architecture-learning-handbook
  version: 40
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - architecture
  - agentic
  kind: guide
  purpose: Record a printable, incremental architecture study handbook derived from the current learning session.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Architecture Learning Handbook

> A living, printable study guide from the architecture learning session.
> It records the decisions, examples, and questions that matter more than a
> verbatim transcript. Append one lesson chunk at a time as the session
> continues.

## How to Use This Handbook

Read one numbered lesson at a time. Each lesson distinguishes:

- **Current state** — what the repository does today.
- **Architecture intent** — the direction we have chosen, which may not yet be
  fully implemented.
- **Misconception check** — a tempting but inaccurate simplification.
- **Study question** — a quick way to test whether the idea has landed.

Do not treat an intended structure as proof that all code has already moved to
that structure. Repository links are the current evidence.

## Learning Map

1. [Layers and ownership](#1-layers-and-ownership)
2. [Authentication and authorization](#2-authentication-and-authorization)
3. [Tenancy and scoped access](#3-tenancy-and-scoped-access)
4. [Security, encryption, and residency](#4-security-encryption-and-residency)
5. [Packages, public APIs, and file structure](#5-packages-public-apis-and-file-structure)
6. [The product harness](#6-the-product-harness)
7. [Platform contracts](#7-platform-contracts)
8. [Applying semantic scanability](#8-applying-semantic-scanability)
9. [App mount and registry](#9-app-mount-and-registry)
10. [Registered jobs and workers](#10-registered-jobs-and-workers)
11. [Policy-controlled dead-letter remediation](#11-policy-controlled-dead-letter-remediation)
12. [The server receives and matches a request](#12-the-server-receives-and-matches-a-request)
13. [Authentication: 401 versus 403](#13-authentication-401-versus-403)
14. [Tenant and resource-level authorization](#14-tenant-and-resource-level-authorization)
15. [Validation, handler, error, and response](#15-validation-handler-error-and-response)
16. [Server lifecycle: startup, readiness, and shutdown](#16-server-lifecycle-startup-readiness-and-shutdown)
17. [Worker lifecycle: receiving, draining, and retrying](#17-worker-lifecycle-receiving-draining-and-retrying)
18. [Tenant and authority: request versus queued job](#18-tenant-and-authority-request-versus-queued-job)
19. [Platform adapters: translating providers without spreading them everywhere](#19-platform-adapters-translating-providers-without-spreading-them-everywhere)
20. [Next lesson queue](#20-next-lesson-queue)
116. [Logical deletion is a repair state, not a retention policy](#116-logical-deletion-is-a-repair-state-not-a-retention-policy)

## 1. Layers and Ownership

### The main mental model

```text
core → platform → app → product → infrastructure
```

Each layer answers a different ownership question:

| Layer | Owns | Does not own |
|---|---|---|
| `packages/core` | Stable nouns, contracts, ports, small pure helpers | Provider SDKs, HTTP servers, product workflows |
| `platform` | Reusable runtime mechanics that implement or compose core contracts | Customer-specific product rules |
| `apps` | Product-facing application behaviour and feature composition | Generic cloud plumbing |
| `products` | A named product's composition, policy, and release intent | The reusable mechanics themselves |
| `infra/04.deploy` | Cloud resources, deployment topology, and operational provisioning | Application business rules |

An easy way to remember this is: **core names, platform enables, apps use,
products decide, infrastructure provisions.**

### Current state

`packages/core` is provider-neutral and has capability modules such as authn,
authz, tenancy, security, persistence, queues, and audit. `platform` is split
into package-level responsibilities including contracts, runtime, server,
security, config, health, observability, workers, and testing.

### Misconception check

“Anything shared belongs in core.”

No. A thing can be shared and still be the wrong kind of shared. A concrete AWS
client may be used in many places but belongs in a platform adapter, not core.
Core is for a stable meaning or port that remains useful without knowing which
provider supplies it.

### Study question

Where should a provider-neutral `Hasher` interface live? Where should a
concrete Argon2 or cloud-KMS implementation live?

Answer: the port belongs in core security; its implementation belongs in a
platform adapter or runtime implementation.

## 2. Authentication and Authorization

Authentication and authorization are connected but different decisions.

| Question | Name | Example answer |
|---|---|---|
| Who is making this request? | Authentication, or authn | “This is Bill, a verified user.” |
| May this authenticated actor do this here? | Authorization, or authz | “Bill may read this Benelux invoice.” |

### A request in small trust decisions

1. A request arrives with credentials, such as a bearer token.
2. The authentication mechanism verifies the credential: signature, issuer,
   intended audience/client, expiry, and other required claims.
3. It translates the verified result into a provider-neutral `Principal`.
4. The route declares whether authentication is required and which permission
   it needs.
5. The authorization mechanism checks the relevant permission and policy facts.
6. A deeper resource decision can also check tenant, group, role, relationship,
   classification, region, and ownership facts.
7. The handler receives the request only after those checks pass.

### Current state versus intended architecture

The current platform server performs generic bearer-token authentication and
route-permission checks, returning `401` for no valid identity and `403` for a
valid identity lacking the route permission. The core authz contracts can model
resources, relationships, attributes, and evidence. Broader resource-level
policy enforcement remains a follow-on integration concern rather than a claim
that every data access path already has it.

### Misconception check

“A valid login means the user can access the resource.”

No. A valid login only establishes who is asking. Authorization still needs to
decide whether that actor may perform this action against this resource in this
context.

## 3. Tenancy and Scoped Access

Tenancy answers: **which customer's boundary are we operating within?**

Authorization inside that boundary often needs more detail than a simple role.
For example:

```text
Bill
  is an accountant
  belongs to the Benelux region group
  may read invoices for Benelux clients
  may not read customer-service queries
```

This is a combination of several policy facts:

| Fact | What it controls |
|---|---|
| Tenant | Which customer boundary applies |
| Group or region | Which portion of that tenant's data is in scope |
| Role or permission | Which action is allowed |
| Resource type | Whether the request concerns an invoice or customer query |
| Relationship/attributes | Whether Bill and the specific resource match the allowed scope |

The policy should be enforced at the point where data is selected or changed,
not merely hidden in a user interface. A hidden button is not an authorization
decision.

### Misconception check

“Tenant membership is the same as permission.”

No. Membership gets an actor into the tenant boundary. Group, role, resource,
and relationship rules decide the access that actor has within that boundary.

## 4. Security, Encryption, and Residency

Security is broader than login and permissions. It includes the rules that
protect data and operations across the system.

### Encryption

Security policy normally covers both:

- **In transit** — data is protected while moving between browser, service,
  queue, database connection, or provider.
- **At rest** — data is protected while stored in a database, object store,
  backup, log sink, or secret store.

The useful separation is:

```text
mechanism → policy → target configuration
```

| Part | Example |
|---|---|
| Mechanism | “This storage adapter can encrypt data using an approved key.” |
| Policy | “This product, tenant, or data classification requires customer-managed encryption.” |
| Target configuration | “In this environment, use this provider, region, key reference, and rotation setting.” |

This avoids one vague “security configuration” bucket. Core can name the
provider-neutral requirement; platform chooses and enforces an implementation;
the app or product provides policy; infrastructure provisions the provider
resources and permissions.

### Default security policy

Reusable defaults are valuable. A new app, product, or tenant should begin with
safe default policy rather than require every team to rediscover baseline
choices. Defaults should be explicit, versioned, and overrideable by an
authorized product or tenant policy. They are not a substitute for the
mechanism that actually enforces them.

### Data residency

Data residency is related to security but is not merely an encryption setting.
It answers where data is allowed to be stored or processed. For now, it is a
provider-neutral security requirement. If it grows to include retention, legal
holds, consent, provenance, and cross-border transfer, it may deserve a wider
data-governance capability.

The planned home for the first real core security residency contract is
`packages/core/src/security/residency.ts`. It is intentionally not an empty
placeholder today.

## 5. Packages, Public APIs, and File Structure

There are two independent organization questions:

| Question | Example |
|---|---|
| Which layer or package owns this? | Provider-neutral hash contracts belong in `packages/core/security`. |
| How should that owner organize its contents? | Hash contracts belong in `hashing.ts`. |

This means named topic files are **not another architecture layer**. They are a
way to make a capability module readable once it contains several independently
meaningful concerns.

### The role of `index.ts`

`index.ts` is the deliberate public doorway. It re-exports the contracts that
other modules are allowed to consume. It should not automatically make every
internal file a supported package import path.

### When to split a module

Split when a reader can reasonably ask a separate question, such as:

- “Where are data classifications defined?”
- “Where is `SecretString` constructed?”
- “What is the hashing port?”
- “How are policy denials represented?”

Do not split one trivial helper into a new file just to achieve visual symmetry.
A small cohesive module can remain in one file.

### `types.ts` is not compulsory

TypeScript does not require a `types.ts` file. Place a contract beside the
capability it describes when that capability has a clear owner. Use `types.ts`
only when several files share a coherent type model that has no more specific
home. Otherwise it becomes a vague drawer for “all the nouns.”

### Worked example: core security

The current chat worktree applies the convention to core security:

| File | Owns |
|---|---|
| `classification.ts` | data sensitivities, sensitive-value kinds, classifications |
| `secrets.ts` | `SecretString` |
| `hashing.ts` | hash shapes, constructors, and the `Hasher` port |
| `policy.ts` | policy IDs, decisions, violations, and evaluators |
| `index.ts` | approved public exports |

Consumers continue to use `@kanbien/core/security`; they do not gain automatic
permission to import internal file paths. The module's README records this
layout.

### Current state

Most core and platform packages still have one source `index.ts` per package.
Core security is the first current example of the finer-grained layout in this
session. This is an incremental migration, not a demand to refactor every
package immediately.

## 6. The Product Harness

The platform is being built before most applications exist. That means the
future product harness needs to teach applications how to consume the platform
correctly and begin with safe defaults.

An application will need guidance for at least:

- features and their ownership
- schemas and validation
- source code and public entry points
- routes and capabilities
- persistence and migrations
- external integrations
- policy defaults for tenancy, authorization, security, encryption, and
  residency
- verification and release evidence

The harness should not impose one giant product folder that owns all of these.
Instead, it should give a product or app a clear structure, default policy
profiles, decision records, and verification paths. The durable starting plan
is recorded in the product layer.

## 7. Platform Contracts

### Lesson 7.1: the boundary

`platform/contracts` is the agreement between an app and the runtime platform.
It lets an app register routes, jobs, health checks, configuration schemas, and
lifecycle hooks without receiving a raw HTTP server, worker loop, provider SDK,
or platform internals.

```text
app declares what it needs
        ↓
platform/contracts defines the allowed contribution
        ↓
platform/runtime collects and validates contributions
        ↓
platform/server or platform/workers runs them in a real process
```

Core contracts answer “what does this stable concept mean everywhere?” Platform
contracts answer “how may an app plug into this runtime?”

### Lesson 7.2: a real route journey

The smoke app registers an authenticated `GET /smoke/:id` route. It declares a
permission, a route, a handler, a job, a health check, and a configuration
schema. It does not start an HTTP server.

At startup, `platform/runtime` creates a registry, calls each app's `mount`,
and validates duplicate registrations and route/permission consistency. It
returns the validated route list.

`platform/server` then validates configuration, compiles route patterns, and
prepares lifecycle and rate-limit mechanisms. At request time, it finds the
route and runs the shared pipeline before the app handler:

```text
request id → logging → CORS → security headers → rate limit → parse
→ authentication → context → authorization → validation → handler
→ response logging
```

The app handler receives a prepared request and context. This is why an app can
declare its business intent once rather than reimplement HTTP and security
mechanics for every route.

### Current state

`platform/contracts`, `platform/runtime`, `platform/server`, and the other
platform packages are currently package-level boundaries with most of their
source in one `index.ts`. The next architectural discussion is to identify
their genuine internal capability seams before we create files.

### Lesson 7.3: grouping the contract surface

The current `index.ts` contains several coherent topics. They should be grouped
by the question an app author asks, not merely by whether a declaration is a
type, function, or error.

| Proposed topic | Main responsibility | Current examples |
|---|---|---|
| `errors.ts` | The common language for invalid platform contributions | `PlatformContractError`, error codes, duplicate and malformed registration helpers |
| `names.ts` | Valid branded names used across the platform grammar | app, route, job, health, API-version, and feature-flag names with their constructors |
| `feature-flags.ts` | The platform's small feature-flag read contract | `FeatureFlagContext`, `FeatureFlagReader`, fixed reader helper |
| `context.ts` | The prepared facts a running handler receives | runtime, request, and job contexts; HTTP method vocabulary |
| `permissions.ts` | Declaring and validating an app permission | `PlatformPermissionDeclaration` and its validator |
| `routes.ts` | The grammar of an HTTP route | request/response, auth requirement, handler, registration, reserved paths, route validation |
| `jobs.ts` | The grammar of a background job | job handler, registration, and validation |
| `registry.ts` | What an app may register with the platform | registry interface plus health-check and config-schema registrations |
| `app.ts` | What a mountable platform app is | app definition, lifecycle hooks, mount dependencies, `definePlatformApp` |
| `index.ts` | The deliberate public contract surface | re-exports from the approved topic files |

This proposal leaves `types.ts` out on purpose. `PlatformRouteRegistration`
belongs with routes, `PlatformJobRegistration` with jobs, and
`PlatformRequestContext` with contexts. A separate `types.ts` would hide those
connections rather than clarify them.

`registry.ts` is still cohesive even though it refers to routes, jobs,
permissions, health checks, and configuration schemas: it owns the single
question “what may an app register?” It is not a miscellaneous utility file.

No files have moved yet. Before an implementation, we must confirm the file
names, preserve `@kanbien/platform-contracts` as the public import, retain the
current type/runtime/boundary tests, and add any useful compatibility proof.

### Misconception check

“The natural split is `types.ts`, `functions.ts`, and `errors.ts`.”

That groups code by TypeScript syntax. It makes a reader jump between files to
understand one capability. The proposed structure groups the contract and its
validation by the capability it serves.

### Lesson 7.4: each grouping in plain English

Imagine the platform as a building that lets independent apps offer services.
The files below describe the building's common rules. They do not contain an
app's invoice, customer, or booking business rules.

#### `app.ts`: what an app is

This is the app's identity card and welcome agreement. It says: “I am this app,
I have this name and optional lifecycle work, and here is how I describe what I
need from the platform.” Its central action is `mount(...)`.

`mount(...)` happens when the platform is starting up, not every time a user
makes a request. It is the app filling in its registration form.

**Misconception:** `app.ts` is the HTTP server for an app. It is not. The
server lives in `platform/server`; this contract lets an app join that server
without controlling it.

#### `registry.ts`: the reception desk

The registry receives each app's registration form. An app can declare a
permission, route, job, health check, or configuration schema through this
single interface. The runtime later checks that all submitted registrations
make sense together.

This file is intentionally cross-cutting because it owns one clear question:
**what may an app register?** It should not contain the detailed grammar of
each individual route or job; those remain in their own topics.

#### `names.ts`: the consistent labels

Apps, routes, jobs, health checks, API versions, and feature flags need stable
names. A name is more than a convenient string: it is used for lookup,
configuration, diagnostics, validation, and avoiding collisions.

This topic creates branded names such as a platform route name or job name and
checks their shared naming format. Putting them together is useful because they
all follow the same “dot-separated, lowercase label” rule.

**Misconception:** a branded name proves that the thing is unique. It does not.
It proves that the value was created as the right *kind* of name and met the
format rule. The registry detects duplicate registrations later.

#### `errors.ts`: the standard rejection slips

When an app tries to register something malformed, the platform needs to say
what is wrong in a predictable form. This topic defines those contract errors:
invalid name, duplicate registration, reserved path, unknown permission, and
malformed route, job, or permission.

These are not unexpected crashes. They are useful, structured feedback about
an invalid platform contribution, suitable for a test, log, or setup report.

#### `context.ts`: the work folder handed to a handler

A route or job handler needs facts about the work it is about to perform:
correlation id, current time, tenant, principal, logger, metrics,
configuration, feature flags, and cancellation signal. That prepared bundle is
a context.

There are three related forms:

- runtime context: facts shared by a running operation
- request context: runtime facts plus request id, HTTP method, and path
- job context: runtime facts plus job name, queue message, and delivery facts

Context is deliberately created by the runtime. It is not a global bag that
handlers freely mutate or invent.

#### `feature-flags.ts`: the switchboard

A feature flag asks whether a capability is enabled in a particular context.
For example, a bulk-import feature might be enabled for one tenant and not
another. This topic defines the small read contract for asking that question.

**Misconception:** a feature flag is authorization. It is not. A flag decides
whether a capability is enabled; authorization decides whether this principal
may perform an action. A disabled feature blocks everyone; an authorization
rule can permit one person and deny another.

#### `permissions.ts`: the labels on access cards

An app declares the permissions it uses, such as `invoice:read`. This gives a
route a known vocabulary to request and lets the runtime detect a route asking
for an undeclared permission.

It does not decide whether Bill actually receives `invoice:read`. That is the
job of authorization policy, using tenant, group, role, relationship, and
resource facts.

#### `routes.ts`: the public service counters

A route describes one HTTP service an app offers: method, path, authentication
requirement, optional validation, and handler. The route contract also names
the request and response shapes that the handler works with.

Route validation happens at registration time so bad declarations fail before
the server begins accepting requests. The actual HTTP server still lives in
`platform/server`.

#### `jobs.ts`: the back-office work queue

A job is work that happens away from the immediate HTTP request: process a
queue message, recalculate a score, send a notification, or generate a report.
Its contract names the job, the message type it accepts, optional payload
validation, and its handler.

Routes and jobs look similar because both give the platform a handler to run.
They remain separate because an HTTP request and a queue delivery have very
different lifecycles, failure handling, and input facts.

#### `index.ts`: the public directory

`index.ts` is the list of approved things an app may import from
`@kanbien/platform-contracts`. It should re-export the public contract topics,
not contain all their implementation itself and not accidentally publish every
internal helper as a supported import path.

### Whole flow recap

```text
app identifies itself in app.ts
  → uses the registry to declare routes, jobs, permissions, health, and config
  → the runtime validates the shared names and errors
  → the server runs HTTP routes with a prepared context
  → workers run jobs with a prepared context
```

### Study question

If an app has a `GET /invoices/:id` route requiring `invoice:read`, which topic
describes the route, which topic declares the permission, and which part of the
system ultimately decides whether Bill may read that particular invoice?

Answer: `routes.ts` describes the route; `permissions.ts` declares the
permission; the authorization policy and its resource/tenant facts make the
final access decision.

### Lesson 7.5: why the topic dependencies are one-way

Splitting a file is useful only if the resulting files have a healthy direction
of dependency. An arrow below means “the file on the left needs vocabulary from
the file on the right.” It does **not** mean that code on the right runs first.

```text
app.ts → registry.ts
registry.ts → routes.ts, jobs.ts, permissions.ts, errors.ts
routes.ts → context.ts, names.ts, errors.ts
jobs.ts → context.ts, names.ts, errors.ts
context.ts → feature-flags.ts, names.ts
feature-flags.ts → names.ts
permissions.ts → errors.ts
names.ts → errors.ts
errors.ts → packages/core
index.ts → all approved public topic files
```

This is the proposed internal direction for a future split. The current source
is still one `index.ts`, so this diagram is a design test before refactoring.

#### What “lower level” means

Lower level does not mean less important. It means more general and less aware
of the surrounding situation.

- `errors.ts` only needs core value types. It must not know what a route or job
  is; it can describe an invalid contribution with a code and plain details.
- `names.ts` can use those errors to reject invalid labels, but it should not
  know why a route is being registered.
- `context.ts` can carry a job name or feature-flag reader, but it should not
  need to know a route's path or validation rules.
- `routes.ts` and `jobs.ts` are more specific. They can use lower-level names,
  errors, and contexts to describe their own kind of work.
- `registry.ts` is a higher-level coordinator. It knows about routes, jobs,
  permissions, health checks, and configuration registrations because its job
  is to collect them.
- `app.ts` is higher again: it uses the registry to declare what one app needs.

#### A worked route example

Suppose an app wants `GET /invoices/:id`.

1. `names.ts` validates the route name, such as `billing.invoices.show`.
2. `permissions.ts` lets the app declare `invoice:read`.
3. `routes.ts` describes the HTTP method, path, permission requirement,
   validation, and handler. It uses the request context type without creating
   the context itself.
4. `registry.ts` accepts that route alongside the declared permission and can
   report a duplicate or inconsistent registration.
5. `app.ts` is where the billing app makes the registrations during startup.

The route may *run* later in the server, but the contract's source dependencies
flow toward the more general building blocks shown above.

#### Why this protects the design

- **No circular trap.** If `errors.ts` imported routes so it could understand
  every route shape, while routes imported errors to report mistakes, the two
  files would depend on each other. Keeping errors general avoids that loop.
- **Easier testing.** Name and error validation can be tested without creating
  a route, server, app, or queue message.
- **Smaller change impact.** A new job feature should not force changes to the
  HTTP route contract.
- **Clearer responsibility.** A job context does not have to know HTTP paths;
  a route contract does not need to know queue-delivery details.

#### The barrel is different

`index.ts` imports or re-exports the approved topic files so outside consumers
have one stable package entry point. Internal topic files should not import the
barrel. If they did, every small file would indirectly depend on every other
public topic and the one-way map would collapse.

### Misconception check

“If TypeScript permits a circular import, the architecture is fine.”

Not necessarily. TypeScript can sometimes compile type-only circles, but a
cycle often tells us two files are trying to know too much about each other.
First look for a lower-level vocabulary or contract that lets each topic stay
independent.

### Lesson 7.6: semantic names and permissions

The repository already validates the *syntax* of these identifiers:

- platform names use lowercase, dot-separated segments
- permissions use `resource:action`

That catches malformed values such as spaces or missing separators. It does not
yet make ownership obvious. Both `foo.bar` and `thing:do` are syntactically
valid but tell a future reader very little.

The recommended next standard is a semantic naming profile for app-owned
platform contributions:

| Contribution | Proposed pattern | Example | What it tells us |
|---|---|---|---|
| App id | `<app>` | `billing` | Which app owns the contribution |
| Route name | `<app>.<resource-or-capability>.<operation>` | `billing.invoice.show` | Billing owns an operation that shows an invoice |
| Job name | `<app>.<resource-or-capability>.<operation>` | `billing.invoice.generate-statement` | Billing owns a background invoice operation |
| Feature flag | `<app>.<resource-or-capability>.<capability>` | `billing.invoice.bulk-import` | Billing owns that optional capability |
| Permission | `<app>.<resource>:<action>` | `billing.invoice:read` | Billing protects invoice reading |
| Health name | `<app>.<probe-purpose>` | `billing.readiness` | Billing supplies this health signal |

The initial action vocabulary should be deliberately small and documented:
`create`, `read`, `list`, `update`, `delete`, `export`, plus explicit business
actions such as `approve` or `submit` when CRUD words are not truthful. Avoid
vague actions such as `do`, `access`, or `manage` unless their exact meaning is
defined.

### What must not go in a permission name

The permission names a protected capability. It does not encode who receives
that capability in a particular situation. Therefore do not put tenant,
region, group, role, provider, or API version into the permission identifier.

```text
Good:    billing.invoice:read
Not good: benelux-accountant.invoice:read
Not good: cognito-group-invoice:read
Not good: billing.invoice:v1:read
```

Bill's Benelux accountant membership is a policy fact used when evaluating
`billing.invoice:read` against a particular invoice. It is not part of the
permission's stable name. API version is already an explicit route field, so it
does not need to be repeated in the route or permission identifier.

### Where enforcement belongs

The name constructor can enforce syntax because it only sees one name. It
cannot verify the owning app prefix because it does not know which app is
mounting the contribution.

The registry or runtime mount process sees both the app id and its declarations.
That is the right place to enforce the semantic rule that app-owned route, job,
flag, health, and permission names begin with that app's namespace. The policy
mechanism then evaluates who may use a permission; it does not rename it.

This is a proposal, not yet a codified rule or source change. It should be
agreed before the `platform/contracts` split so names, validation, tests, and
the public handbook all tell the same story.

### Lesson 7.7: category prefixes—put kind in the context, capability in the name

It is useful to distinguish a name's **functional category** from the
**owner and capability** it identifies. A category says what sort of thing it
is: app, job, feature flag, configuration value, or error. An owner and
capability say whose behaviour it represents and what that behaviour is.

The guiding rule is:

> Put the functional category in the file, TypeScript type, or explicit field;
> put the stable owner and capability in the identifier value.

| Location | Good use of category | Why |
|---|---|---|
| File | `jobs.ts`, `flags.ts`, `errors.ts` | A reader can find the family of contracts quickly. |
| Type | `PlatformJobName`, `FeatureFlagName`, `PlatformErrorCode` | The type prevents a job name from being confused with another kind of name. |
| Field | `job.name`, `flag.name`, `error.code` | The object tells the reader what the value represents. |
| Identifier value | `billing.invoice.generate-statement` | The value says which app/capability it refers to, without repeating `job`. |

Therefore these are normally the clearer values:

| Category | Prefer | Usually avoid | Why |
|---|---|---|---|
| App | `billing` | `app.billing` | It is already stored as an app id. |
| Route | `billing.invoice.show` | `route.billing.invoice.show` | The route declaration already supplies the category. |
| Job | `billing.invoice.generate-statement` | `job.billing.invoice.generate-statement` | The `PlatformJobName` type and job registry supply the category. |
| Feature flag | `billing.invoice.bulk-import` | `flag.billing.invoice.bulk-import` | The flag registry supplies the category. |
| Permission | `billing.invoice:read` | `permission.billing.invoice:read` | The permission field and evaluator supply the category. |
| Health probe | `billing.readiness` | `health.billing.readiness` | The health registry supplies the category. |

This is not an argument for short, contextless values such as `show` or
`generate`. The `billing` prefix is valuable because it identifies ownership;
the extra `job.` prefix would merely repeat information that is already present.

### Configuration and errors

Configuration keys and error codes often appear in flatter, less typed places:
an environment-variable list, a dashboard, a log line, or a support ticket.
They need an intelligible owner and subject, but still do not usually need the
literal category word.

```text
Prefer: PLATFORM_AUTH_PROVIDER
Avoid:  CONFIG_PLATFORM_AUTH_PROVIDER

Prefer: PLATFORM_CONTRACT_INVALID_NAME
Avoid:  ERROR_PLATFORM_CONTRACT_INVALID_NAME
```

The environment-variable mechanism already says “configuration”; an `error`
object's `code` field already says “error.” `PLATFORM` and `AUTH` or
`CONTRACT` carry the useful information: which subsystem owns the value and
what has gone wrong. If different kinds of identifiers must share one generic,
untyped registry, give the record an explicit `kind` such as `job` or `flag`
instead of encoding that kind redundantly into every name.

### Decision test

Before adding a category prefix, ask:

1. Does the surrounding file, type, field, or registry already say that this is
   a job, flag, app, configuration value, or error?
2. Does the proposed prefix add new information, rather than repeat that
   category?
3. Would an owner/capability prefix make the value more traceable without
   revealing tenant, group, role, customer, or provider detail?

If the first answer is yes and the second is no, leave the category out of the
value. Prefer `billing.invoice:read`, not
`permission.billing.invoice:read`; Bill's accountant role and Benelux scope
remain policy facts, not identifier text.

### Misconception check

“More words always make a name more self-documenting.”

No. Repetition makes names longer, harder to rename, and noisier in logs and
policy screens. A good identifier supplies the information its context does
not already provide.

### Study question

Should a feature flag stored in a `FeatureFlagName` field be called
`flag.billing.invoice.bulk-import`?

No. The type and field already identify it as a feature flag. The identifier
should be `billing.invoice.bulk-import`, which tells us the owning app and
capability.

### Lesson 7.8: should this become a policy?

Yes. This is a small **platform-contract naming standard**, not a new security
policy and not a product-harness convention. Its proposed home is the existing
`platform.contracts-are-the-app-boundary` rule in
`docs/03.product/rules/platform/layers/platform.yml`. That rule already says
that apps declare routes, permissions, jobs, health checks, and config schemas
through `platform/contracts`, and that platform validates app identity and
route namespacing before traffic is served.

The standard should extend that existing boundary with these rules:

1. A file, TypeScript type, registry, or explicit field declares the functional
   category: app, route, job, flag, health check, configuration, or error.
2. An app-owned identifier value begins with the stable app id and identifies
   the capability; it does not repeat the category.
3. Permissions use `<app>.<resource>:<action>` and never encode tenant, group,
   role, provider, API version, or customer facts.
4. Flat operational names, such as environment keys and error codes, identify
   a stable subsystem and subject without redundant `CONFIG_` or `ERROR_`
   prefixes.
5. The platform registry validates app ownership and namespacing while mounting
   an app; simple constructors keep validating syntax locally.

### Why this is the right home

| Candidate home | Decision | Reason |
|---|---|---|
| `packages/core` | No | These are names for platform contributions, not provider-neutral concepts needed by every consumer. |
| `.agentic/03.product` | No | The product harness will teach apps to follow the rule, but it should not own the runtime contract that enforces it. |
| Security or tenancy rules | No | Permissions are one affected identifier kind, but the rule also governs routes, jobs, flags, health, errors, and config. |
| Platform layer rule | Yes | It owns the app-facing contract, registry validation, and public names that apps supply. |

### Safe adoption sequence

First document the profile and representative accepted/rejected examples in the
existing platform rule. Then, in a separate implementation slice, split the
contract topics if approved, keep the public package import stable, and add
registry-level tests for app ownership and namespacing. Existing names must be
migrated deliberately with compatibility evidence rather than silently
rewritten.

### Codification result

The profile is now codified as the warning-level
`platform.contract-identifiers-are-semantic` rule in
`docs/03.product/rules/platform/layers/platform.yml`. Its source material,
two-iteration source review record, derivation report, refreshed provenance,
and focused retrieval-selector fixture provide the evidence chain.

The rule governs the vocabulary expected of new or deliberately migrated
app-mount contributions. It does **not** yet add a validator or alter runtime
behaviour. A later implementation slice must add registry-level app-prefix
checks and accepted/rejected contract tests while preserving existing public
identifiers through an explicit migration.

## 8. Applying Semantic Scanability

Semantic scanability means a reader can infer a file's responsibility and an
identifier's owner or intent without opening a giant registry or one giant
source file. It should be applied selectively: where responsibilities are
independently understandable, changed, tested, or security-sensitive.

### Strong current candidates

| Area | Current signal | Likely natural topics | Priority and caution |
|---|---:|---|---|
| `platform/contracts` | 483-line source file; topics already mapped | names, errors, flags, contexts, permissions, routes, jobs, registry, app | First candidate because it is app-facing and already studied |
| `platform/security` | Responsibility files and deliberate barrel | errors, authentication, JWT, authorization mapping, headers/CORS, rate limiting | Completed with preserved public imports and security tests |
| `platform/runtime` | Responsibility files and deliberate barrel | errors, registry/mounting, contexts, lifecycle | Completed with preserved public imports and runtime-consumer tests |
| `platform/server` | 632-line source file | server shell, route matching, request pipeline, Node transport, errors | Valuable but later: this is process-critical code |
| Core capability modules | Some are large mixed capability files, such as files, monitoring, queues, and persistence | Split only after a concrete responsibility map | Apply incrementally, as with core security |

Small cohesive modules should remain small. A short `index.ts` is not a defect.
Line count only suggests where to look; it does not prove that a split is wise.

### Security and operational downsides

Semantic names must improve orientation without becoming a source of sensitive
information or brittle policy behaviour.

| Risk | Why it matters | Guardrail |
|---|---|---|
| Sensitive identifier leakage | Names appear in logs, metrics, traces, audit records, and sometimes error responses | Never include tenant ids, user ids, email addresses, regions tied to customers, secrets, provider claim names, or raw business data in names |
| Capability discovery | A detailed route or permission name can reveal that a sensitive capability exists | Keep authorization real, do not expose registry listings unnecessarily, and return safe client errors; names are not a security boundary |
| Breaking rename | Permissions, route names, job names, flags, and event-like names may appear in policy, config, dashboards, audit, and deployed clients | Treat public identifiers as compatibility-sensitive; migrate or alias deliberately rather than casually renaming |
| Accidental wildcard privilege | Prefixes can tempt a later system to interpret `billing.*` as broad permission | Use exact permission matching by default; define wildcard semantics explicitly before allowing them |
| False implication | A name like `read` can be mistaken for permission to list, export, or view sensitive fields | Define action meanings and make exceptional actions explicit |
| File-structure ceremony | Excessive tiny files make navigation slower rather than faster | Split only at stable responsibility seams; keep private helpers local to their topic |
| Naming freeze | A namespace tied to a temporary folder or provider becomes misleading after reorganisation | Use stable logical app/capability names, not file paths, vendor names, or deployment targets |

### A safe adoption sequence

1. Describe the responsibility map and naming profile before changing code.
2. Keep the package-root public import stable through a thin `index.ts` barrel.
3. Move code mechanically first; do not combine a structural move with changed
   authorization, cryptography, routing, or rate-limit behaviour.
4. Run the existing type, runtime, boundary, and compatibility proof.
5. Add semantic validation only where the validator has the facts it needs:
   syntax at construction; app-ownership prefixes during registry/runtime mount.
6. Make identifier renames deliberate migrations with compatibility evidence.

The principle therefore applies beyond folder structure: public contract names,
permission vocabulary, route/job/flag names, logs, metrics, audit types, and
documentation should all be understandable without being overly revealing.

### Runtime source-organisation result

The runtime split is now complete. It uses four responsibility files behind
the existing `@kanbien/platform-runtime` public doorway:

| File | The question it answers |
|---|---|
| `errors.ts` | “How does the runtime describe a safe, stable failure?” |
| `registry.ts` | “Which declarations belong to this process, and do they fit together?” |
| `contexts.ts` | “Which shared runtime facts should this request or job receive?” |
| `lifecycle.ts` | “In which order may this process start, become ready, drain, and stop?” |
| `index.ts` | “Which runtime names are a supported promise to callers?” |

This is a useful example of a good split because the responsibilities have
different reasons to change. A registration rule changes for a different
reason than shutdown order; a context gets a different fact for a different
reason than an error gains a safe code. Keeping them separate makes each
change easier to find and test.

### Misconception to avoid

> “Because runtime now has several files, apps should import whichever file
> contains the function they need.”

No. Apps, server targets, and worker targets still import the supported public
package. The barrel is the stable doorway; the files behind it are maintained
as an internal map. That is why we could make the split without asking every
consumer to change its imports.

## 9. App Mount and Registry

### One idea first: a registry is an arrivals desk

An app has useful things to contribute: an HTTP route, a permission, a
background job, a health check, and perhaps a configuration schema. The app
should declare those things, but it should not need to know how the platform
opens a network port, polls a queue, or coordinates process shutdown.

The **registry** is the startup-time catalogue where an app hands those
declarations to the platform. The platform can then validate the whole
catalogue before accepting traffic or polling work.

```text
app declaration
      |
      v
app.mount(registry, dependencies)
      |
      v
checked registry catalogue
      |
      +-- server uses routes, permissions, health checks, and config schemas
      |
      +-- worker uses jobs and config schemas
```

The registry is in memory and is freshly built while a server or worker shell
starts. It is not a database, an API endpoint, or a global bag of mutable
application state.

### The current repository path

`PlatformApp` gives every app a `mount` function. The runtime's
`mountPlatformRuntimeApps` function creates one registry, validates each app
id, rejects duplicate app ids, and calls each app's mount function. The smoke
app is the concrete example: during mount it registers a configuration schema,
one permission, one route, one job, and one health check.

Each registration has two checks to understand:

1. **Local checks while registering.** The registry validates a route or job's
   own shape and rejects duplicates, reserved route paths, or invalid names.
   Registration errors are remembered by the registry.
2. **Relationship checks after all apps have mounted.** The registry verifies
   that every permission named by an authenticated route or resource
   authorizer was actually declared. This can only be checked after it has
   seen the whole catalogue.

If either kind of error exists, the runtime returns a mount failure. The server
then refuses to start listening; the worker refuses to start polling. An app
cannot quietly publish a route whose required permission was forgotten.

### Why the platform owns the boundary

The app owns the declaration and its handler. The platform owns the mechanism
that turns declarations into live behaviour:

| Concern | Owner | Why |
|---|---|---|
| “There is an invoice route.” | App | This is product-facing behaviour. |
| “This route needs `billing.invoice:read`.” | App | The app states the capability it protects. |
| Check that the permission was declared | Runtime registry | It sees the full set of declarations. |
| Authenticate, authorize, match the HTTP route, and call its handler | Server shell | These are reusable HTTP mechanics. |
| Match a queued message to a job and invoke its handler | Worker shell | These are reusable background-work mechanics. |

This division lets one app declaration be consumed in more than one runtime
context without the app importing the HTTP server or a queue-polling loop.
Both the server and worker build the same kind of registry independently at
startup; each then consumes the parts it needs.

### A useful failure example

Imagine an app declares an authenticated invoice route requiring
`billing.invoice:read`, but forgets to declare that permission. The route may
look complete when viewed alone. Once all contributions are together, the
registry detects the missing relationship and prevents startup.

This is a valuable architecture habit: validate **relationships** where all
participants are visible, not inside a smaller object that can see only one
side of the relationship.

### Naming-policy connection

The runtime currently validates identifier syntax, duplicate registrations,
and route-to-permission relationships. It does not yet verify that a route,
job, or permission belongs to the app that mounted it. That deferred check
needs the mount context: the individual name constructor sees a name, but the
mount process sees both the app id and its contributions.

That is exactly why the semantic naming policy assigns future ownership-prefix
validation to the registry/runtime mount boundary. Existing smoke-app names
remain existing public identifiers; this lesson does not claim that runtime
enforcement has already been added.

### Misconception check

“The registry is just another `index.ts` that re-exports things.”

No. A barrel file groups imports for source-code consumers. A runtime registry
collects declarations as a process starts, rejects invalid combinations, and
hands a checked snapshot to the server or worker. They are both organising
tools, but they solve different problems.

### Study question

Why is a final registry validation necessary if `registerRoute` has already
validated the route?

Because a route can name a permission that is declared by a different call—or
not declared at all. The relationship can only be checked once the registry has
seen every app contribution.

## 10. Registered Jobs and Workers

### The job's purpose

A route usually responds while a person waits. A job represents work that can
happen later: generate a statement, resize an upload, send a notification, or
rebuild a search index. The app supplies the job's business handler; the
worker shell supplies the reliable delivery mechanics around it.

The current smoke app registers a job named `platform-smoke.rebuild`. Its
queue message type is also `platform-smoke.rebuild`, and its payload must
contain a boolean `rebuild` value. A job name is the useful human-facing
identity for logs and metrics; the message type is the dispatch key the worker
uses to find the handler. They happen to be the same in this small example,
but they are separate contract fields.

### The journey of one message

```text
App registers a job
       |
       v
Worker mounts apps and builds a message-type -> job lookup
       |
       v
Queue supplies one message
       |
       +-- no matching job? -----> dead letter
       |
       +-- invalid payload? -----> dead letter
       |
       +-- already processed? ---> skip safely
       |
       v
Build job context and run the handler
       |
       +-- success -------------> record success
       |
       +-- temporary failure ---> retry, until the attempt limit
       |
       +-- final failure -------> dead letter
```

Before this journey begins, the worker mounts every app through the same
runtime registry used by the server, validates configuration, and creates a
lookup from every registered message type to its job. It also must be started
before it will take work from the queue.

### Why each protection exists

| Step | What the worker does | Why it is this way |
|---|---|---|
| Match | Looks up the job by the message type | A queue message must not run an arbitrary handler. An unknown type is quarantined. |
| Validate | Runs the job's payload validator before its handler | Bad input should not reach business logic. Retrying malformed data will not repair it. |
| Deduplicate | If an optional idempotency key was already processed, skips the handler | Queues can deliver a message more than once; this avoids doing the same work twice where an idempotency store is provided. |
| Context | Builds a job context with correlation id, logger, metrics, config, flags, clock, and tenant when the message includes one | A background handler needs operational context without reaching into global process state. |
| Handle | Invokes the app-owned handler | This is the only step that performs the app's business action. |
| Observe | Logs and records metrics for success, retry, and dead-letter outcomes | Operators need to see what happened without inspecting application memory. |

### Retry and dead letter are different decisions

Not every failure deserves a retry. The current worker immediately dead-letters
an unknown message type and an invalid payload because another identical
attempt is very unlikely to succeed. A handler failure is treated as
potentially temporary: by default the worker allows three total attempts,
using a one-second delay after the first failure and a two-second delay after
the second. A third handler failure is dead-lettered.

A **dead letter** is a preserved record of a message that was not processed,
along with its failure reason and attempt count. It is safer than silently
discarding it and more controlled than retrying forever. A human or a repair
process can later inspect, correct, or replay it according to an explicit
operational policy.

The current in-memory queue records the requested retry delay as metadata; it
does not sleep or schedule the message for later. That is suitable for the
local shell and tests. A production queue adapter must honour delayed delivery
for the retry policy to be real in deployment.

### Tenancy and authorization in background work

An asynchronous message does not arrive with a browser session. When a queue
message includes a tenant id, the worker places that id in the job context so
the handler can stay within the correct tenant boundary.

The worker does not invent an end-user principal or automatically grant a job
permission. Normally the user-facing route authorizes the request to start the
work before it enqueues the job. If the background action needs a further
authorization decision, that policy must be explicit in the job's design.

### Misconception check

“A retry means the work happened exactly once, eventually.”

No. Retries are an **at-least-once delivery** mechanism: a handler may have
completed its external side effect just before a failure is observed. An
idempotency key and an idempotency store are the extra tools that make repeating
the work safe where that matters.

### Study question

With the default maximum of three attempts, what happens after a handler fails
on attempts one, two, and three?

Attempts one and two are re-queued with increasing delay. After the third
failure, the message is dead-lettered with its error and attempt count.

## 11. Policy-Controlled Dead-Letter Remediation

### One idea first: a DLQ is a quarantine desk, not a bin

When a message cannot be processed safely after its allowed attempts, the
worker puts it in a **dead-letter queue** (DLQ). The point is to preserve the
message and its failure evidence for investigation. It should not disappear,
and it should not retry forever.

A future **DLQ remediation capability** can help an operator with that desk.
It may classify the failure, gather safe evidence, identify a likely cause,
and recommend the next action. It may eventually perform a few pre-approved,
low-risk actions. We have recorded this as a deliberately deferred platform
plan item; it is not implemented in the current worker shell.

### Why call it policy-controlled?

An “agent” sounds capable, but capability without boundaries is dangerous. A
language model can form a useful hypothesis, such as “this message looks like
it failed because an older payload version is no longer accepted.” It cannot be
the authority that decides to replay, delete, repair, or broadly purge data.

That authority comes from an explicit remediation policy. The policy says what
the capability may inspect, which job types are eligible, what evidence it
needs, whether a human must approve the action, and when it must stop.

| Outcome | Can it eventually be automatic? | Why or why not? |
|---|---|---|
| Redact and classify failure evidence | Usually yes | It is read-only and helps an operator understand the problem. |
| Alert a human with a recommended runbook step | Usually yes | The capability informs; a human remains accountable for the consequence. |
| Replay one message | Sometimes | Only if the job type is explicitly allowlisted, idempotent, version-compatible, tenant-safe, rate-limited, and audited. |
| Repair a payload or change permissions | Normally no | It changes business or security meaning and needs a deliberate approval path. |
| “Clear this event type” | Not by default | Queue purges can affect unrelated tenants or messages; exact selection and approval are required. |

### Who owns each part?

| Layer | Responsibility |
|---|---|
| `platform/workers` | The neutral mechanics for inspecting DLQ items, applying a policy decision, and recording audits. |
| Queue adapter | Provider-specific actions, such as retrieving or re-driving a message. |
| App | What the job means, whether replay is idempotent, and what a safe repair would mean. |
| Product and deployment target | Which job types are allowlisted, who approves higher-risk actions, alert destinations, retention/residency rules, and environment-specific limits. |

This preserves the same idea used elsewhere in the platform: **mechanism →
policy → target configuration**. Platform supplies a safe mechanism; a product
sets the business policy; a particular deployed target supplies the real
operational configuration.

### A safe future sequence

1. Start with a read-only reporter that produces a redacted summary and a
   recommended human action.
2. Add immutable audit records, a dry-run mode, rate limits, and a kill switch.
3. Allow an automated replay only for one specifically approved, proven
   idempotent job class.
4. Expand only when tests prove tenant isolation, least-privilege tool access,
   safe failure behavior, and an operator can see and stop what is happening.

### Misconception check

“A self-healing layer should automatically fix every DLQ item.”

No. The safest self-healing system knows when to **stop and escalate**. An
unknown or sensitive failure should stay quarantined with good evidence for a
human, rather than receive an inventive automated repair.

### Study question

Why is a replay of one invoice-generation message potentially safe, while a
request to purge all `invoice.generated` messages is much riskier?

The first can be limited to a known message, tenant, idempotency key, and
audited retry policy. The second may remove unrelated work across tenants or
hide a systemic fault, so it needs exact selection, policy, and human approval.

## 12. The Server Receives and Matches a Request

### One idea first: the handler is not the front door

An app route handler contains the business response: for example, "show this
invoice." It should not be the first code that receives an internet request.
The platform server is the front door. It creates a controlled request envelope
before deciding whether any app handler should run.

Imagine Bill sends a `GET` request to `/invoices/benelux-104`.

The app previously registered this route:

| Route field | Value |
|---|---|
| Name | `billing.invoice.show` |
| Method | `GET` |
| Path | `/invoices/:id` |

At this early point, the server knows only that the method and path match. It
does **not** yet trust Bill, assume that he may read the invoice, or call the
invoice handler. A route match finds the correct doorway; it does not grant
access through it.

### What happens before the match?

When the server shell starts, it mounts the apps and builds one complete
catalogue of routes. It checks mount and config validity before listening for
traffic. When a request arrives, the current server records a request id,
starts safe request logging, derives CORS and security headers, applies a rate
limit, and parses the request. It handles platform health paths separately;
then it looks for a route with both the requested method and a matching path.

For Bill's example, matching `/invoices/:id` creates a neutral request shape
whose path parameters include `id: benelux-104`. The later authentication,
authorization, tenant, validation, and handler stages use that shape. The
server does not make the app parse raw Node HTTP objects or reimplement route
matching.

### Why not let each app do this itself?

If every app handler owned its own request ids, headers, CORS, rate limits,
parsing, and error responses, one forgotten step could create a different
security or operational hole on one route. Centralising those cross-cutting
concerns gives every app the same guarded entrance. The app still owns its
business meaning: what an invoice is, how it is loaded, and which result it
returns after platform has made the request safe to handle.

The current server test records the successful middleware order. It confirms
that the handler comes after request preparation rather than being the raw
entrypoint.

### Misconception check

"Finding `GET /invoices/benelux-104` means Bill is allowed to see it."

No. Matching only answers, "which declared route would handle this request?"
The next chunks answer, "who is Bill?" and "may Bill read this particular
invoice in this tenant?"

### Study question

Why does the server need the complete route catalogue before it starts
listening, rather than allowing each route to check only itself when a request
arrives?

Because duplicate methods and paths, reserved platform paths, undeclared
permissions, and missing required dependencies are relationships between
declarations. The server can reject an invalid app setup before it accepts
real traffic.

## 13. Authentication: 401 versus 403

### The smallest useful distinction

Suppose the route `billing.invoice.show` requires the permission
`billing.invoice:read`.

There are three different outcomes before the invoice handler can run:

| What the server learns | Result | Meaning |
|---|---:|---|
| No valid identity can be established | 401 | “Authenticate first.” |
| A valid identity is established, but it lacks `billing.invoice:read` | 403 | “You are known, but not allowed to do this.” |
| A valid identity has the declared permission | Continue | The request can move to tenant, resource, validation, and handler checks. |

The current server first asks its authentication hook to inspect the request.
For an authenticated route, it converts a successful result into a
provider-neutral `Principal`: the platform's standard representation of the
caller. If authentication did not produce that principal, the server returns
401. It does not ask the handler to decide whether the caller is real.

Only after the principal exists does the server compare the route's declared
permissions with the permissions granted to that authenticated caller. A
missing required permission produces 403. In both failure cases, the app's
protected handler is not called.

### A concrete test case

The current server test sends the protected echo route three kinds of request:

| Request condition | Server result | Did the protected handler run? |
|---|---:|---|
| No bearer credential | 401 | No |
| A recognized bearer credential with no required permission | 403 | No |
| A recognized credential with the required permission | 200, if later checks pass | Yes |

This ordering is useful to clients as well. A 401 tells an application that it
may need to sign in, refresh its credentials, or present a valid token. A 403
tells it that signing in again will not by itself grant the missing capability.

### Public routes are a deliberate exception

A route declared public can run without an authenticated principal. In the
current contract, even presenting a credential to a public route does not make
the principal available to that route's handler. This prevents app behaviour
from changing accidentally because a caller happened to include a credential.
If an app needs optional identity, that must be designed as an explicit future
contract rather than inferred from raw request headers.

### Misconception check

“403 means authentication failed.”

No. Authentication succeeded enough to identify the caller. Authorization then
denied the requested capability. The two statuses help both users and client
software choose the right next action.

### Study question

Why does the server check the route's broad permission before asking an app to
resolve the particular invoice or its tenant facts?

Because a caller who lacks even the general capability should not make the
system spend work or reveal resource-specific information while resolving
objects they cannot access. The next lesson will add those tenant and resource
checks for callers who pass this first permission gate.

## 14. Tenant and Resource-Level Authorization

### A broad permission is not a blank cheque

Suppose Bill has passed authentication and has the broad permission
`billing.invoice:read`. That answers one question: Bill may perform the kind of
action called “read an invoice.” It does not yet answer whether he may read
this invoice for this tenant.

For the example we discussed, Bill is an accountant assigned to the Benelux
group. A complete decision can therefore include:

| Decision fact | Example |
|---|---|
| Principal | Bill |
| Broad permission | `billing.invoice:read` |
| Tenant scope | Benelux |
| Resource | Invoice `benelux-104` |
| Policy facts | Bill's group assignment and the invoice's client/region facts |

The group assignment and region membership are policy facts. They do not
belong in a permission string such as
`billing.invoice.benelux-accountant:read`; that would make a stable capability
name carry changing organisational policy.

### The two later gates

After the route's broad permission check, a route that requires a tenant asks a
tenant resolver to establish the caller's tenant context. If the resolver
cannot produce a valid tenant for a route that requires one, the current server
fails closed with 403 and does not call the handler.

The server then creates request context containing the verified principal and,
when available, the tenant. A route that needs a particular resource can ask an
app-provided resolver for a safe description of that resource: its stable
reference and the narrowly relevant relationships, attributes, or facts. The
platform `Authorizer` evaluates all of those together.

In plain language, the later question is: “May this authenticated Bill, using
this permission, access invoice `benelux-104` inside the Benelux tenant, given
the policy facts we know?”

### Why check the broad permission first?

It is an economical and protective early gate. Someone without even
`billing.invoice:read` should not trigger invoice lookup, tenant resolution, or
resource-policy work. The current test confirms that a caller denied at this
coarse permission step does not call either the tenant resolver or the resource
resolver.

That does not weaken tenant isolation. Once the server begins resolving a
resource, the tenant context and resource facts are part of the authorization
request. The app's data-access design must also stay tenant-scoped; the
platform context is a guardrail and a shared decision input, not permission to
query across tenants.

### Resource existence is also a policy decision

Sometimes it is safe to say “that invoice does not exist” (404). Sometimes
even confirming that an invoice exists reveals sensitive information. The
resource resolver can therefore mark a missing-looking resource as forbidden,
which the server returns as 403 instead. This is an explicit disclosure choice,
not an accident of route matching.

### Misconception check

“Bill's accountant group should be embedded in the permission name.”

No. The permission names the capability. Group, role, tenant, region, and
customer facts tell the authorizer whether Bill receives that capability for
this resource at this time.

### Study question

Why is it useful that the resource resolver supplies only a resource reference
and relevant facts to the authorizer, rather than handing the authorizer the
entire invoice record?

It reduces unnecessary data exposure, makes the policy decision easier to
audit, and keeps the authorizer focused on access facts rather than business
processing. The invoice handler can load or use fuller business data only after
the access decision allows it.

## 15. Validation, Handler, Error, and Response

### The handler receives a prepared request, not the internet

By this point, the server has matched the route and passed the relevant
identity, permission, tenant, and resource checks. The handler should now
receive a prepared platform request and context, rather than raw Node HTTP
objects or a credential it must interpret for itself.

Before calling the handler, the server runs the route's input validator. This
checks the request body's expected shape. For example, an echo route might
require a `message` value that is text. If the body has the wrong shape, the
server returns a controlled 400 response and never calls the handler.

That is different from business validation. Route validation asks, “is this a
safe, well-formed request shape?” The handler may still ask business questions
such as, “is the invoice still editable?” or “does this amount fit the account
rules?”

### Three outcome paths

| What happens | HTTP result | What the platform does |
|---|---:|---|
| Input shape is invalid | 400 | Returns a stable invalid-request error before the handler runs. |
| Handler returns normally | The handler's chosen success result | Adds platform headers, logs the outcome, and records metrics. |
| Handler throws unexpectedly | 500 | Maps the failure to a safe platform error, logs the internal error, and records a failure metric. |

The key word is **safe**. A client needs a stable message and error code; it
does not need an exception stack, secret-bearing provider detail, database
query, or private policy evidence. Operators do need enough protected log and
metric evidence to investigate the failure. The platform keeps those two
audiences separate.

### The response trail

Every return path reaches the server's finishing step. For a route with a
declared observability profile, it records only the profile-approved canonical
facts and only the signal families the profile permits. A 200 response, 400
validation failure, 403 authorization failure, and 500 handler failure can
therefore leave an operational trail without every app handler remembering how
to log—but they cannot turn a raw request, a principal, a tenant, or a body into
an accidental telemetry field. A route that explicitly opts out produces no
capability telemetry. Server failures that occur before any route is known are
recorded separately as platform operations, not mislabelled as business work.

### Misconception check

“If the server catches errors, app handlers do not need to care about errors.”

No. The platform catches unexpected failures at the boundary so one failure
does not leak internal detail or crash the request path. Apps still need to
express expected business outcomes deliberately: for example, a known
conflicting update or a rule that prevents an invoice from being edited.

### Study question

Why is a malformed body a 400 instead of a 500?

The client supplied a request that does not satisfy the route's published
shape. That is an expected client-correctable condition. A 500 means the
server failed while trying to fulfil a valid request, which needs operator
investigation rather than a client retry with the same data.

## 16. Server Lifecycle: Startup, Readiness, and Shutdown

### Start with the shop analogy

Imagine a shop in the morning. There is a difference between a person being
inside the building and the shop being ready for customers.

- **Alive** means the building and its basic process exist. Someone can answer
  the door.
- **Ready** means the tills work, the stock system is available, the staff have
  completed their opening tasks, and the shop can actually serve a customer.

The same distinction matters to a platform server. A process may have started
but still be mounting apps, checking configuration, connecting resources, or
waiting for a dependency. Sending real traffic too early creates intermittent,
hard-to-diagnose failures.

### What the current server checks before it listens

The current server does not open its network port first and hope to discover
problems later. It first builds the server shell. That preparation mounts the
registered apps, validates their registrations, checks that authz mappings only
refer to declared permissions, confirms that required tenant/resource
authorization dependencies exist, validates app configuration, and compiles the
route catalogue.

Only after that preparation succeeds does the process start the runtime
lifecycle and ask Node to listen on a port. This is a useful architecture rule:
**reject an invalid configuration at startup, before it can serve real
traffic.**

| Startup stage | Plain-English purpose | Example failure it prevents |
|---|---|---|
| Mount apps | Build the shared catalogue of app contributions | Two apps attempt to register the same route. |
| Validate policy wiring | Check that declared routes have the dependencies they require | A tenant-required route has no tenant resolver. |
| Validate configuration | Check required configuration before opening the port | A required app setting is missing or malformed. |
| Start lifecycle | Run app and resource startup work in a known order | A needed shared resource cannot start. |
| Listen | Accept network traffic only after the earlier stages pass | A load balancer reaches a half-initialised server. |

### `/livez` and `/readyz` answer different questions

The server exposes two health questions, not one.

| Endpoint | Question | Current behaviour |
|---|---|---|
| `/livez` | “Is this server process able to respond at all?” | Returns `live` with 200 when the process can answer. |
| `/readyz` | “Should this instance receive normal application traffic?” | Requires the runtime lifecycle to be ready and every registered readiness check to be healthy. It returns 503 when not ready. |

In the current test, `/livez` returns 200 before the lifecycle starts, while
`/readyz` returns 503. After lifecycle startup succeeds, `/readyz` returns 200
with `ready`. That is intentional: a process can be alive while it is still
unsafe to route normal work to it.

Health exposure is itself policy. The current process defaults liveness to
public, while readiness defaults to authenticated when an auth hook is present.
A deployment target can choose the appropriate exposure policy; the app route
handlers do not make that global decision for themselves.

### What happens when the shop closes?

Shutdown is a sequence, not one abrupt stop. When the current server process
receives `SIGTERM` or `SIGINT`, it records that shutdown began, stops the HTTP
listener, and then asks the runtime lifecycle to close in a controlled order.

The runtime's intended order is:

1. Apps run `beforeStop` hooks, so they can stop beginning new app work.
2. Resources drain, so in-flight work can finish where their adapter supports
   it.
3. Resources close in reverse startup order, which is useful when one resource
   depends on another.
4. Telemetry flushes, so the final logs and metrics are not lost.
5. Apps run `afterStop` hooks, and the lifecycle becomes stopped.

The lifecycle becomes not-ready while it is stopping. That gives an orchestrator
or load balancer a signal to stop sending it new work before the process exits.

### Why not make `/livez` check every dependency too?

It is tempting to make one health endpoint check everything: database, queue,
identity provider, cache, and every app dependency. That usually creates the
wrong recovery action. A temporary dependency failure may mean “do not send new
traffic here” rather than “kill and restart this server immediately.”

Keeping liveness small and readiness richer lets deployment tooling make a more
appropriate distinction: restart a genuinely dead process, but remove an
unready instance from traffic while it recovers or drains.

### Misconception check

“A 503 from `/readyz` means the server has crashed.”

No. In the current design it can mean the server is still starting, is draining
for shutdown, or has a readiness dependency that is not healthy. The process
may be alive and able to explain that state.

### Study question

Why does the server validate app registration and configuration before opening
its port, rather than accepting traffic and returning an error only when the
first affected route is called?

Because startup is the moment when the platform has the complete catalogue of
apps, routes, permissions, and configuration. Failing there is deterministic,
visible to deployment tooling, and prevents customers from discovering a
partially broken release one route at a time.

## 17. Worker Lifecycle: Receiving, Draining, and Retrying

### Start with the familiar picture

The HTTP server and the worker are both **process shells**. Each mounts the
same app declarations, validates configuration, starts the shared runtime
lifecycle, reports readiness, and shuts down in an ordered way. That is why
they can both use the same PlatformApp and runtime lifecycle controller.

They differ in one central question:

| Shell | Where work arrives | When its caller learns the outcome |
|---|---|---|
| HTTP server | A caller sends a request to a route. | Immediately, in an HTTP response. |
| Worker | A queue holds a message until a worker takes it. | Usually not immediately; the producer may only know that the message was accepted. |

Imagine a Benelux accountant requests an invoice PDF. The server might respond
quickly with “your document is being prepared,” then place a
billing.statement:generate message on a queue. A worker later receives that
message, generates the file, and records success or failure. The accountant's
browser is not waiting for the worker to finish in the same connection.

That difference is why a worker needs retries, idempotency, and dead letters;
an HTTP route normally has only one chance to produce a response before its
client connection ends.

### What the current worker actually is

The current platform/workers package is a provider-neutral **worker shell**
with an in-memory queue. It is intentionally deterministic: tests or a future
provider adapter call runNext() to ask it to process one available message. It
is not yet a deployed, continuously polling queue process with signal handlers
like the server process.

Its startup path is deliberately similar to the server's:

    mount app declarations
            |
            v
    validate all declared configuration
            |
            v
    create job-message lookup and lifecycle
            |
            v
    start lifecycle
            |
            v
    worker is ready to run a message

The shell refuses to run a message before its lifecycle is ready. In the
runtime test, runNext() before start() returns PLATFORM_WORKER_NOT_READY; after
startup, its health result becomes ready. This is the worker equivalent of
refusing ordinary HTTP traffic before server startup is complete.

### One message's lifecycle

Once ready, the worker takes one queue entry and follows this decision path:

    queue entry
        |
        +-- no job for its message type? --> dead letter
        |
        +-- payload does not match job contract? --> dead letter
        |
        +-- idempotency key already processed? --> safely skip handler
        |
        v
    build job context (correlation id, optional tenant, shared dependencies)
        |
        v
    run the app's job handler
        |
        +-- succeeds --> record success; record idempotency key when present
        |
        +-- fails before attempt limit --> enqueue retry with next attempt number
        |
        +-- fails at attempt limit --> dead letter

The same queue message can carry a tenant id, and the worker turns it into
tenant context for the job. It does **not** invent a browser user or silently
reuse a person's HTTP permission. A job normally acts under a separately
designed service/workflow authority, while tenant scope keeps its data work in
the correct customer boundary. If the message has no tenant id, the handler's
tenant context is absent; the current test proves both cases.

### Why idempotency matters more for workers

Here is a common misconception: “If a job succeeds once, the queue will never
deliver it again.”

That is not a safe assumption. A worker can finish an external action, then
crash or lose a network acknowledgement before the queue records completion.
The queue may deliver the message again. At-least-once delivery is often the
reliable choice, but it shifts a responsibility to the job design: repeating
the same message must not charge the customer twice or create two invoice
files.

An idempotency key is the worker's answer. When the key was already recorded,
the current worker marks the result successful but skips the handler. In the
test, the same message is enqueued twice, yet the handler's counter remains at
one. This is not merely an optimisation: it is a protection against duplicate
side effects.

### Retry is an outcome, not a hidden loop

When a handler fails, the worker records a structured failure and makes an
explicit decision:

- Before maxAttempts, it asks the queue to retry the entry, records the next
  attempt number and backoff, and emits a retry log and metric.
- At the limit, it moves the entry to the dead-letter collection and records
  the failure as dead-lettered.
- A bad message type or invalid payload goes straight to dead letter. Retrying
  a message that can never match a job or pass validation would only create
  noise and cost.

The current in-memory queue stores a delayMs value on a retry, but it does not
wait for wall-clock time before returning that entry. That is a useful honesty
boundary: the worker owns retry **policy and outcome reporting**; the future
provider queue adapter must supply real delayed delivery, message leases or
acknowledgements, and polling behaviour.

### Shutdown: same shared lifecycle, different front door

For the server, shutdown closes the network listener first. It stops accepting
new requests, then lets the runtime lifecycle run app hooks, resource draining,
resource closure, telemetry flush, and final app hooks.

For the current worker shell, shutdown() closes its queue first, then runs that
same shared runtime lifecycle. The test confirms that health becomes not-ready
and a later enqueue is rejected. In other words, it stops accepting new local
work before declaring the worker stopped.

But do not over-read that small implementation. The current shell has no
continuous poll loop and no explicit tracking of a handler already running
while shutdown begins. Therefore it does not yet prove real production
“drain-in-flight-messages” behaviour.

A future queue-provider process needs to make that policy explicit:

1. Stop polling or receiving new messages.
2. Mark itself unready so orchestration can replace it without adding work.
3. Decide what to do with in-flight messages: wait up to a bounded grace
   period, stop them cooperatively, or let their lease expire for safe retry.
4. Close the queue connection only after that decision, then run the shared
   runtime shutdown and flush telemetry.

That is the worker version of gracefully closing a server listener. The shared
runtime gives both shells the same orderly shutdown vocabulary; the queue
provider supplies the worker-specific mechanics.

### Current state versus future work

| Concern | Current repository evidence | Later provider/process responsibility |
|---|---|---|
| Startup and readiness | Worker mounts apps, validates config, and must start before runNext(). | A long-running host starts polling only after that succeeds. |
| One-message handling | Dispatch, validation, tenant context, idempotency, metrics, logs, retry decision, and dead letter are present. | Translate provider messages, acknowledgements, and failures into this boundary. |
| Retry delay | A retry delay is calculated and recorded. | Deliver it after real delay, with visibility/lease rules. |
| Shutdown | Queue is closed and the common runtime lifecycle shuts down. | Stop receive, coordinate in-flight work, and handle lease expiry/requeue safely. |
| Process signals | No worker main/signal host exists in this package today. | Install SIGTERM/SIGINT handling analogous to the server, with worker-specific drain policy. |

### Misconception check

“A worker is just an HTTP server without routes.”

No. Both are reusable platform shells, but their delivery contracts are
different. A server protects a short request-response interaction; a worker
protects a durable, possibly repeated message and its side effects. That is
why the worker's most important concepts are acknowledgement, idempotency,
retry, dead letter, and draining—not HTTP status codes.

### Study question

Why should a future worker stop receiving new messages before it waits for
in-flight jobs to finish during shutdown?

Because otherwise the worker can keep increasing the amount of work it must
drain. Stopping delivery first makes the in-flight set finite, gives the
orchestrator a clear not-ready signal, and makes every remaining job subject to
the chosen timeout, completion, or safe-retry policy.

## 18. Tenant and Authority: Request versus Queued Job

### First, correct a tempting idea

It is tempting to think: “A queued job is just Bill's HTTP request, paused until
later. We should put his bearer token in the message and repeat the same
authorization check when the worker runs.”

That is usually the wrong model.

A queue can retain a message, retry it, and place it in a dead-letter queue.
Putting a person's credential into that durable delivery path risks secret
exposure and mixes a short-lived login session with a longer-running workflow.
It also leaves an unanswered policy question: if Bill's group membership
changes between request time and execution time, should the job continue,
cancel, or require new approval?

Instead, distinguish the **human request** that started work from the
**workflow authority** that is allowed to carry it out later.

### The same business action, two contexts

Suppose Bill, a Benelux accountant, asks the web app to generate a statement for
customer ACME Belgium.

| Fact | HTTP request from Bill | Queued statement-generation job |
|---|---|---|
| Immediate actor | A verified principal representing Bill. | No browser principal is supplied by the current worker. |
| Permission decision | The server checks the route's declared permission, then may make a resource-level decision. | The current worker dispatches a registered job; it does not call the Authorizer. |
| Tenant source | The server asks a tenant resolver using the authenticated principal and route/request facts. | The message may carry a tenant id, which the worker turns directly into tenant context. |
| Resource facts | A route's resource resolver can provide a resource reference, relations, attributes, and policy facts. | The job handler must retrieve only the tenant-scoped business data it needs; no generic job resource-authorizer stage exists today. |
| Result visible to caller | An HTTP status and response, such as 200, 401, or 403. | A success, retry, or dead-letter outcome for operational systems. |
| Continuity evidence | Request id and authenticated principal. | Message id, correlation id, causation id, tenant id, and idempotency key when supplied. |

The tenant boundary matters in both columns. The source and meaning of authority
do not.

### What the server does for Bill

For an authenticated route, the server turns a successful authentication result
into a principal. It checks the route's broad permissions before resolving
tenant or resource facts. For a tenant-required route, it asks the tenant
resolver for a tenant context using the principal and request. For a
resource-authorized route, it asks the Authorizer to decide using the
principal, permission, tenant id, and safe resource facts.

In ordinary language, the server answers this question:

“Is this verified Bill allowed, right now, to ask for this statement for this
Benelux customer?”

The answer can be no because Bill is not logged in, lacks the broad capability,
is not assigned to Benelux, or lacks access to this particular customer. Those
are request-time authorization decisions about a human caller.

### What the worker does for the message

A queue message has an id, type, version, time, payload, and optional tenant,
correlation, causation, idempotency, and grouping metadata. It has no principal,
permission, group, role, or raw credential field.

When the worker processes it, it validates the payload and creates job context.
If the message has a tenant id, it adds tenant context. The runtime's job-context
input accepts a tenant but no principal, and the current worker supplies no
principal. The job handler therefore knows which tenant it is working for, but
does not receive an assertion that “Bill currently has permission X.”

This is a useful safety boundary. A queue message says, “perform this recognised
workflow for tenant Benelux,” not “trust this unverified claim that a particular
person may do anything.”

### How a safe handoff should work

The following is the intended decision sequence; the repository has the
individual server and worker building blocks, but does not yet enforce this as
one end-to-end workflow contract.

1. Bill makes an authenticated request to create the statement.
2. The server verifies Bill, checks the required permission, resolves Benelux,
   and applies any resource-level policy.
3. The app decides that this allowed request may create a background workflow.
   It records the initiating action for audit according to product policy.
4. The app enqueues a narrow message: stable job type and version, tenant id,
   safe business references such as the statement request id, correlation and
   causation ids, and an idempotency key where duplicate effects matter.
5. Later, the worker accepts the message only through its trusted delivery
   boundary, validates its shape, rebuilds tenant context, and runs the
   registered workflow.
6. The handler performs tenant-scoped work under the workflow/service authority
   chosen by the product and deployment target. It does not reuse Bill's bearer
   token.
7. It records success, retry, or dead-letter evidence.

An audit record may need to preserve who initiated the work, but that is
different from storing a reusable credential or treating the initiator as the
worker's active principal. The exact audit fields, retention, and access rules
are product and security policy choices.

### Why time changes the answer

Consider two policies for the same queued statement:

| Policy question | Possible product decision |
|---|---|
| Bill loses the accountant role after starting the job. Should generation finish? | It may finish because it was validly approved at enqueue time. |
| Bill is disabled because of a suspected compromise. Should a delayed export finish? | It may be cancelled or require a fresh approval. |
| A nightly billing run has no human initiator. Can it generate statements? | Yes, if a specifically configured workflow/service authority is allowed to do so. |

There is no universal answer. The important architectural rule is: make it an
explicit product policy. Do not accidentally decide it by forwarding an old
browser token, or by assuming that a queued message carries the same authority
as an interactive request.

### Current repository boundary

The current source proves several things and deliberately does not prove
others:

- The server has principal, permission, tenant-resolver, and optional
  resource-authorizer stages before the route handler.
- Queue messages can preserve tenant and correlation continuity, but tenant id
  is optional at the core message level.
- The worker converts a present tenant id into job context, validates a message,
  and invokes a registered handler.
- The worker does not currently declare that a job requires a tenant, identify
  a producing service, or evaluate group, role, permission, or
  resource-level authorization at execution time.

So it would be inaccurate to say “the current worker already authorizes
accountants to run Benelux jobs.” It currently supplies the building blocks for
a tenant-aware workflow; the app, product policy, and future provider adapter
must define and enforce the real producer and workflow-authority boundary.

### Who owns the later policy?

| Owner | Question it owns |
|---|---|
| Platform server | How an interactive caller is authenticated and authorized before app code runs. |
| Platform worker | How a registered message is validated, contextualised, run, retried, and recorded. |
| App | What the job means, which data it may change, and how it maintains tenant-scoped invariants. |
| Product | Whether a valid human request creates durable work, whether execution can outlive a role change, and what approval/audit rule applies. |
| Queue and identity adapters plus deployment target | Which producers and worker service identities may use the real queue, and how their credentials, encryption, network access, and audit are configured. |

This is the same mechanism → policy → target configuration pattern we saw
earlier. It prevents a generic queue worker from guessing a customer's business
authorization rules.

### Misconception check

“Adding a tenant id to the message fully authorizes the worker.”

No. Tenant id answers “which customer boundary applies?” It does not answer
“who produced this message?”, “is this workflow allowed?”, “may this job access
this resource?”, or “should work initiated yesterday still run today?” Tenant
scope is necessary, but it is only one fact in a complete security decision.

### Study question

Bill is authorised to request a Benelux statement at 09:00. The job is delayed
until 11:00, when his role is revoked. Which decision should be repeated at
11:00: the old human request, the workflow authority, both, or neither?

The correct answer is not built into the queue. It depends on the product's
risk and business policy—but whichever answer is chosen must be explicit,
auditable, and enforced at the appropriate boundary.

## 19. Platform Adapters: Translating Providers without Spreading Them Everywhere

### Start with a travel-plug analogy

A laptop needs electricity, not knowledge of every country's wall socket. A travel
adapter translates the local socket into the shape the laptop expects. The
laptop does not become “a UK device” or “an Irish device” because an adapter is
connected.

Platform adapters play the same role:

    platform needs a capability
            |
            v
    provider-neutral platform contract or port
            |
            v
    adapter translates one provider's details
            |
            v
    deployment target selects and configures that adapter
            |
            v
    provider service performs the real work

The adapter is a **translator**, not the owner of the app's business behaviour,
product policy, or cloud provisioning.

### The current concrete example: Cognito authentication

The repository currently has one implemented provider adapter:

    platform/adapters/aws/auth/cognito/

Its path is deliberately descriptive:

| Path part | Meaning |
|---|---|
| aws | The provider family. |
| auth | The capability being adapted. |
| cognito | The concrete AWS service. |

The adapters guide also shows possible paths for SQS, S3, Secrets Manager,
CloudWatch, ECS/Fargate, and Lambda. They are examples of the intended layout,
not claims that those adapter packages already exist.

### What each layer knows

Imagine the app declares a protected invoice route requiring
billing.invoice:read.

| Layer | What it is allowed to know |
|---|---|
| Core | Stable ideas such as Principal and Permission. It does not know Cognito. |
| Platform security | Generic JWT verification, bearer-token extraction, claim-to-permission mechanics, and the PlatformAuthenticationHook shape. It does not choose an identity provider. |
| Cognito adapter | Cognito issuer and JWKS URL formats, Cognito access-token requirements, and the Cognito group-claim name. |
| App | Which route exists and which stable permission protects it. It does not import Cognito. |
| Product and target entrypoint | Whether this deployed product uses Cognito and which allowed provider claims map to the app's declared permissions. |
| Infrastructure | The real user pool, network and IAM access, configuration delivery, encryption, and deployment environment. |

A useful boundary test is: if you changed Cognito to another identity provider,
which layers should need changes? The adapter and target composition should
change. Core, app route declarations, platform server, and generic security
mechanics should not need provider-specific edits.

### Trace one sign-in request

Suppose Cognito issues a signed access token for a user in the
kanbien-admins group.

1. The deployment target entrypoint reads PLATFORM_AUTH_PROVIDER.
2. When it is cognito, the entrypoint asks the Cognito adapter to create a
   PlatformAuthenticationHook from target configuration.
3. The adapter builds Cognito's issuer and JWKS address from the configured
   region and user-pool id.
4. It requires Cognito-specific token facts: token_use must be access, and
   client_id must match the configured app client.
5. It translates Cognito's group claim, scope claim, and optional configured
   claims into the generic permission-mapping shape.
6. Generic platform security verifies the JWT and produces a provider-neutral
   authentication result containing a principal and permissions.
7. The provider-neutral server uses that hook for its ordinary 401/403 route
   pipeline. The protected app route sees the standard context, not a Cognito
   object.

The adapter test proves this composition: no credential receives 401; a signed
Cognito-shaped token whose configured group, scope, and claim produce the
declared smoke:read permission receives 200.

### The key split: claim vocabulary versus permission policy

The phrase cognito:groups belongs to the adapter because it is a Cognito claim
name. The fact that a particular group grants billing.invoice:read does **not**
belong in core or the generic server.

The current adapter reads group, scope, and claim mappings from target
environment configuration. That keeps the provider claim vocabulary and the
mapping mechanism inside the adapter, while the actual mapping values remain
configuration rather than hard-coded Cognito behaviour.

This is security-sensitive configuration. Changing a mapping can grant access,
so only approved product/target configuration should control it, changes should
be reviewed and auditable, and every mapped permission should correspond to a
permission an app actually declares. A later product-policy surface may make
that ownership more explicit; the current code uses target environment values.

### Why generic security still has JWT code

At first glance it may seem strange that generic platform security contains JWT
and JWKS verification while Cognito is an adapter.

The distinction is not “uses the internet” versus “does not use the internet.”
JWT signature verification, expiry checks, issuer comparison, and fetching a
JWKS document are standard identity-provider mechanics. They can work for many
providers.

Cognito-specific knowledge is different:

| Generic security can say | Cognito adapter must say |
|---|---|
| Verify a token against a configured issuer and JWKS endpoint. | This is the exact Cognito issuer and JWKS URL for this region and user pool. |
| Require named claims to have configured values. | A Cognito access token has token_use = access and uses client_id in this way. |
| Map a string-array claim into permissions. | The Cognito group claim is named cognito:groups. |

The adapter does not use a raw AWS SDK client today because JWT verification only
needs Cognito's public JWKS document over HTTPS. It is still provider-specific:
the issuer construction, required claims, and claim names are Cognito rules.

### Why the target entrypoint is allowed to import the adapter

Ordinary app code must not import provider adapters. If it did, app behaviour
would become tied to one cloud provider and every app author would need to learn
provider setup details.

The target composition entrypoint is different. It is the one deliberate place
where this deployment says, “run these product apps using this provider
adapter.” It imports the Cognito adapter, selects it only when the target's
provider configuration says cognito, and hands the resulting generic hook to
the provider-neutral server.

This keeps dependency direction honest:

    app -> platform contracts
    server -> generic platform security
    Cognito adapter -> core plus generic platform security
    target entrypoint -> product, server, and selected adapter
    infrastructure -> provisions the chosen provider

The adapter's boundary test enforces part of this: its source may import only
core and generic platform security, not apps, infrastructure, or arbitrary
provider SDK code.

### Current state versus intended adapter family

| Concern | Current repository state | Later work, if needed |
|---|---|---|
| Identity provider | Cognito authentication adapter is implemented and composed by the Kanbien target entrypoint. | Another identity provider would receive a separate adapter, not a Cognito switch inside generic server code. |
| Queue provider | No SQS adapter is implemented. | Define the provider-neutral queue port and delivery semantics first, then build a narrow SQS adapter. |
| Storage, secrets, observability, compute | Directory examples document the intended naming convention only. | Add an adapter only when a real platform capability needs a provider implementation. |
| App dependency | Apps declare permissions, routes, jobs, and config through platform contracts. | Preserve that rule; do not give ordinary apps provider imports for convenience. |

### Misconception check

“An adapter is a miscellaneous folder where all AWS code can live.”

No. Each adapter should be narrow and named by provider, capability, and
service. It translates a defined platform need. Cloud provisioning remains in
infrastructure; product policy remains in product configuration; provider-free
mechanics remain in platform packages.

### Study question

Where should each fact live?

- The literal claim name cognito:groups.
- The permission billing.invoice:read.
- The decision that the deployed Kanbien target uses Cognito.
- The actual Cognito user pool and its access permissions.

Answer: adapter; app/platform contract; target composition; and infrastructure,
respectively. That four-way split prevents a provider detail from quietly
becoming a business rule or a cloud resource definition.

## 20. Platform Security, Part 1: The Boundary

We have already followed one complete request through the server. The next
question is: which parts of keeping that request safe should belong to the
platform, and which parts must remain the product's business decision?

That question matters because “security” is a broad word. Without a boundary,
it becomes a tempting home for every rule that happens to deny access.

### The short answer

`platform/security` owns reusable *mechanisms*: the technical machinery that
helps the platform establish identity and apply consistent protection.

The product and its apps own *policy*: the business meaning of an allowed
action, including tenant, group, role, region, and particular-resource rules.

Here is the division using Bill, the Benelux accountant:

| Question | Owner | Why |
|---|---|---|
| Is the bearer token correctly formed, signed, unexpired, and from a trusted issuer? | Platform security | Every protected app needs the same reliable identity check. |
| Which generic permissions are associated with a verified caller’s claims? | Platform security, using target-supplied mapping | This is the reusable translation from identity facts to platform permissions. |
| Is Bill an accountant in this tenant? | Product/app authorization policy | It is a business role assignment, not a universal platform fact. |
| Is Bill assigned to the Benelux region group? | Product/app authorization policy | The group and its meaning vary by product. |
| Does this invoice belong to a Benelux client? | Product/app resource policy and data access | It depends on the actual invoice and business data. |
| May a browser at this origin call the API? | Platform security, with target configuration | It is a transport boundary shared across routes. |

The platform can answer “who presented this token?” and “does this caller have
the route's declared permission?” It must not quietly decide that accountants
can read invoices. That last rule belongs to the product because another
product could use the same platform while having completely different roles.

### An illustration: building security versus company policy

Imagine a secure office building.

    Platform security: checks the badge is genuine and opens a turnstile for an authorised badge type.
    Product policy: decides that Benelux finance staff may enter the invoice archive, but not the customer-support room.
    Resource policy: checks that the particular archive drawer concerns a Benelux client.

The building should not contain a hard-coded rule about the company's
accountants. Equally, the company's finance team should not need to implement
cryptographic badge validation for every room. The boundary lets each concern
change without silently breaking the other.

### What exists in the repository today

The current `platform/security/src/` module is organised into responsibility
files while retaining the same public package import. The following table is
both a map of the current files and a reminder of why they are separate:

| Current capability | What it does | Boundary it protects |
|---|---|---|
| Authentication hook | Gives the server one provider-neutral way to ask whether a request is authenticated. | Identity provider differences stay outside normal app code. |
| JWT and JWKS verifier | Verifies a signed token against the trusted issuer and its published public keys. | An invented or altered token must not become an identity. |
| Claims-to-permissions mapping | Converts configured token claims into declared platform permissions. | A route uses permissions without knowing a provider's claim vocabulary. |
| CORS and security headers | Creates consistent browser-facing defensive headers. | A browser cannot bypass the target's permitted cross-origin boundary. |
| Rate limiter | Limits repeated requests using a stable caller, token hash, IP address, or anonymous key. | One caller cannot consume unlimited request capacity. |
| Standard security errors | Gives server code stable 401, 403, and rate-limit failure shapes. | Callers get predictable responses without receiving sensitive diagnostic detail. |

The current files are `errors.ts`, `authentication.ts`, `jwt.ts`,
`authorization.ts`, `headers.ts`, and `rate-limiting.ts`; `index.ts` is the
deliberate public barrel. The split moved no provider choice, product policy,
or security control. The existing public type, runtime, and boundary checks
passed before and after the move.

### The current split-status distinction

There are two layers with “security” in their name, and they are at different
stages. `packages/core/src/security/` **has** been split into
`classification.ts`, `secrets.ts`, `hashing.ts`, and `policy.ts`, with its
small `index.ts` acting as the public barrel. Those are provider-neutral nouns
and ports.

`platform/security/src/` **is now** split into errors,
authentication/principal bridging, JWT/JWKS verification, authorization
mapping, browser protection, and rate limiting. It was reorganised only after
the test baseline and actual dependency directions were inspected. Its public
package import remains unchanged, and its internal helper exports are not made
public merely because the source has several files.

### What platform security deliberately does not own

It does not declare an app's permissions: the app declares those through
platform contracts. It does not provision a Cognito user pool: infrastructure
does that. It does not hard-code a Cognito claim name: the Cognito adapter does
that. And it does not apply the Benelux invoice rule: the product/app and its
data-aware resource policy do that.

This is the same mechanism → policy → target-configuration idea we used for
encryption:

    mechanism: verify an identity token and produce consistent defences
    policy: decide what a verified identity may do to a business resource
    target configuration: select Cognito, permitted browser origins, and limits for this deployment

### Misconception check

“If authorization uses security code, all authorization rules belong in
`platform/security`.”

Not quite. Platform security owns the *generic permission check*: “this route
requires `billing.invoice:read`; does the caller have it?” The app or product
owns the meaning behind that permission and any richer question such as “is
this invoice in Bill's permitted region?” Generic checks are reusable
mechanisms; business decisions are policy.

### Study question

Suppose a second product uses the platform for clinical records instead of
invoices. Should it have to edit platform security to replace “accountant” with
“clinician”?

No. It can reuse the same token verification, headers, rate limiting, and
permission-check mechanism while supplying its own roles, groups, permissions,
tenant rules, and patient-record policy. That is the practical value of this
boundary.

### Repository evidence

- [Platform security source](../../../platform/security/src/index.ts) defines
  the provider-neutral authentication hook, JWT/JWKS verification, permission
  mapping, security headers, CORS helpers, and rate limiter.
- [Platform server source](../../../platform/server/src/index.ts) consumes the
  header, rate-limit, and permission mechanisms during a request.
- [Cognito authentication adapter](../../../platform/adapters/aws/auth/cognito/src/index.ts)
  supplies Cognito-specific issuer, claim, and token requirements.

## 21. Package READMEs: Documentation as a Navigational Boundary

When we split a large `index.ts` into clearly named responsibility files, the
file tree becomes more useful. A nearby README completes that benefit: it tells
the reader why those files are separate, which imports are public, and where to
look for proof that the boundary works.

The rule is deliberately layered:

    parent catalogue: a short map of all capabilities
    package README: purpose, public boundary, file map, dependencies, proof
    multi-file module README: why this local set of files exists
    index.ts: the deliberate supported exports
    tests: evidence that the stated contract works

For example, `packages/core/README.md` should remain an abridged catalogue of
core capabilities. Once the `security` module has several files,
`packages/core/src/security/README.md` should describe `classification.ts`,
`secrets.ts`, `hashing.ts`, `policy.ts`, and its `index.ts` barrel. Readers no
longer need to search a large root document to understand one small module.

### Why not add a README to every directory?

That would create boilerplate and documentation drift. The useful threshold is
a package boundary or a genuinely multi-file capability whose file roles are
not self-evident. One obvious private helper next to one `index.ts` does not
need another document.

### The maintenance rule

When a substantive responsibility file is created, split, moved, removed, or
given a new owner, update its nearest README in the same change. This makes the
file map a small navigation contract instead of an aspirational diagram.

### Study question

Why can `index.ts` not replace the README?

Because `index.ts` answers “what may another module import?” A README answers
“why are these files here, what must not live here, and where is their proof?”
Both are useful, but they protect different forms of understanding.

## 22. Platform Security, Part 2: From Bearer Token to Principal

We now know the boundary: platform security establishes a trusted caller, while
the product decides what that caller may do to particular business data.

This lesson follows the first part in slow motion. It stops just before
permission mapping, tenant policy, and resource authorization; those are the
next decisions in the request path.

### Start with the question the server is answering

For a protected route, the server is not asking “does this string look like a
token?” It is asking:

> Can I safely treat this request as coming from this particular identity?

That is a chain of trust decisions. Every answer must be yes before the server
creates a `Principal` for the app to use.

    HTTP request
        -> find a bearer token
        -> parse its JWT shape
        -> find the matching public signing key
        -> verify the signature
        -> verify issuer, purpose, time, and subject claims
        -> create a provider-neutral authentication result
        -> create a core Principal
        -> let the server continue to permission checks

If a protected route cannot reach a trusted principal, its handler does not
run.

### First, what is a bearer token?

The client sends an HTTP header in this form:

    Authorization: Bearer <token>

“Bearer” means whoever possesses the token may present it. That is why it must
travel only over encrypted HTTPS connections, be short-lived, and never appear
in logs, browser URLs, README examples, error responses, or chat transcripts.

Platform security reads this header case-insensitively and accepts the value
only when it has the `Bearer` form. No header, malformed header, or empty token
does not create a partial identity; it produces the shared unauthenticated
result.

### A JWT is three readable-looking pieces, not three proof steps

A JSON Web Token (JWT) usually looks like this:

    encoded-header.encoded-payload.encoded-signature

The first two pieces are Base64URL-encoded JSON. They are *encoded*, not
encrypted. A person who obtains the token can normally decode the header and
payload. Do not put a password, secret, customer data, or other sensitive
information in JWT claims simply because the token looks opaque.

The third piece is the cryptographic signature. That is the part that lets the
server detect whether someone invented or modified the first two pieces.

### A closer illustration: how the signature is verified

Think of the identity provider as a notary with a unique private seal. The
notary creates the header and claims, joins their encoded forms, and uses its
private signing key to create a signature for that *exact* text.

    identity provider's private key
        + exact encoded header and claims
        -> signature

The token contains the header, claims, and signature. It does not contain the
private key.

When Bill presents the token, the server reads the `kid` from its header. The
`kid` is only a **key ID**: a label such as “key-2026-09,” not Bill's id and not
a secret. The server finds the matching public key in the trusted issuer's
JWKS list and asks whether that public key validates the signature for this
exact header-and-claims text.

    token header says kid = key-2026-09
        -> server finds public key key-2026-09 in the trusted JWKS list
        -> server verifies the signature against the exact token contents
        -> valid or invalid

If somebody changes one claim—Bill's group, expiry time, or subject—the exact
text changes, but the old signature does not. Verification fails.

The server holds only a public verification key. It can recognise a signature
made by the provider, but cannot make one itself. Giving every app server the
private signing key would be dangerous: a compromised server could mint
convincing tokens. The `kid` also lets the provider rotate keys: old and new
public keys can coexist during a transition while tokens identify the key that
signed them.

### The trust decisions, one at a time

| Step | Current platform behaviour | Why it is necessary |
|---|---|---|
| 1. Extract | Finds a `Bearer` token in the request headers. | The server needs an explicit credential rather than guessing from an arbitrary value. |
| 2. Parse | Requires exactly three non-empty JWT segments and JSON-object header and claims. | A malformed value cannot reach cryptographic or application logic as though it were a token. |
| 3. Select algorithm and key | Requires `alg` to be `RS256` and a `kid` key identifier. | The platform refuses an unexpected signing method and knows which signing key to use. |
| 4. Obtain public key | Looks up `kid` in the issuer's JWKS public-key document and keeps a per-process cache. | The server verifies a signature with a public key; it never needs the identity provider's private signing key. |
| 5. Verify signature | Checks the token signature using RSA-SHA256. | Changing Bill's name, group, expiry, or scope invalidates the token. |
| 6. Verify issuer and purpose | Checks `iss`, plus adapter-supplied required claims. | A correctly signed token from the wrong identity system or for the wrong client is still not acceptable. |
| 7. Verify time | Requires `exp`; checks optional `nbf` and `iat`, allowing the configured clock skew. | A captured old token and a token that is not yet valid must not become an identity. |
| 8. Verify subject | Requires a non-empty `sub` claim. | A valid token needs a stable identity to represent. |
| 9. Create principal | Requires authenticated state plus an id, type, and subject before making a core `Principal`. | App code should never receive a half-formed authenticated caller. |

### The unfamiliar words

| Word | Plain-English meaning | Why we need it |
|---|---|---|
| `iss` (issuer) | The identity system that says it issued this token. | Stops one identity system’s token being accepted as another’s. |
| `kid` (key id) | The label of the public key used to verify the signature. | Lets an identity provider rotate signing keys without taking every server offline. |
| JWKS | A published set of public verification keys. | Lets the platform check signatures without possessing secrets. |
| `exp` | Expiry time. | Limits how long a stolen token remains useful. |
| `nbf` | “Not before” time. | Stops a future-dated token being accepted early. |
| `iat` | Issued-at time. | Detects a token that claims to have been issued implausibly in the future. |
| `sub` (subject) | The stable identity inside the token. | Becomes the basis of the provider-neutral principal identity. |
| clock skew | A small tolerance for two machines whose clocks differ slightly. | Prevents harmless timing differences causing needless login failures without granting unlimited extra life to a token. |

The current generic verifier allows 60 seconds of clock skew by default. That
is a small operational tolerance, not a reason to make token expiry vague.

### Bill's request, as an illustration

Imagine Bill’s browser sends a request to a protected invoice route.

1. The server finds Bill’s bearer token.
2. It sees a JWT header naming `RS256` and a particular `kid`.
3. It obtains the matching public key from the trusted issuer's JWKS set.
4. It proves the signature matches. If someone changed a claim from “Bill” to
   “administrator”, this step fails.
5. It checks that the token's issuer is the configured issuer, that the token
   has not expired, and that `sub` identifies Bill.
6. The adapter's provider-specific requirements must also hold. For Cognito,
   the configured checks require an access token and the intended app client.
7. The generic authentication hook returns a provider-neutral result. Only
   then can the platform create Bill's core `Principal`.

At this point, the system knows whom the request represents. It has *not yet*
decided whether Bill may read any invoice. The group-to-permission mapping,
tenant scope, and particular-invoice decision happen later.

### Why Cognito details are not in generic platform security

Generic platform security knows how to verify a JWT given an issuer, JWKS URL,
and required claims. It should work for more than one identity provider.

The Cognito adapter supplies Cognito facts:

| Cognito adapter supplies | Generic platform security supplies |
|---|---|
| The Cognito issuer and JWKS URL from region and user-pool id. | The JWT parsing, public-key lookup, signature check, and generic claim validation process. |
| The `token_use = access` requirement. | The ability to require any named claim to equal an expected value. |
| The matching `client_id` requirement. | The provider-neutral authentication result and core-principal bridge. |
| Later, the special `cognito:groups` claim name. | The generic mechanism for mapping a configured string-array claim. |

The deployment target selects this adapter. Ordinary apps do not need to know
the issuer URL, JWKS endpoint, Cognito token vocabulary, or key-rotation
details.

### The safe principal boundary

After verification, the authentication hook can carry several facts: the
subject, claims, scopes, generic permissions, and a stable rate-limit key.
But `platform/security` creates a core `Principal` only when all of these are
present:

    authenticated state
    principal id
    principal type
    subject

This is defensive design. It prevents a future authentication adapter from
returning `authenticated: true` but forgetting to state whom it authenticated.
For an authenticated route, the server treats either an unauthenticated result
or a missing principal as a `401 Unauthorized` response and never calls the
handler.

### Safe failure has two meanings

For a malformed, altered, expired, wrong-issuer, wrong-purpose, or
subject-less token, the verifier returns an invalid-token result. The generic
authentication hook deliberately turns that into the same unauthenticated
result as a missing token. The client receives the generic `401` response,
not a cryptographic troubleshooting guide that would help an attacker.

There is one useful current-implementation nuance: the default JWKS fetcher
throws when it cannot reach the key endpoint or receives an invalid JWKS
document. That is an identity-provider dependency failure, not proof that the
caller's token is fake. In the current server shell, an unhandled failure moves
to the outer safe-error path and becomes a generic `500` response. A future
hardening slice may classify that operational failure more precisely, but it
must still avoid exposing key-fetch details to the client.

### Misconception check

“The token has Bill's group in it, so token validation has already authorised
Bill to read the invoice.”

No. Token validation establishes that the trusted issuer made particular claims
about Bill. Authorization still has to interpret those claims through
configured group-to-permission mapping, the route's declared permission,
tenant resolution, and perhaps a resource-level policy. A genuine identity is
not automatically an allowed action.

### Study question

Why does the server use a *public* JWKS key instead of storing the identity
provider’s private signing key?

Because the server only needs to verify signatures. Giving every application
server the private signing key would let a compromised server mint convincing
tokens. Public keys can verify a signature but cannot create one.

### Repository evidence

- [JWT authentication hook and principal bridge](../../../platform/security/src/index.ts)
  extract bearer tokens, verify tokens, produce generic authentication facts,
  and refuse to create an incomplete principal.
- [JWT claim validation and JWKS fetcher](../../../platform/security/src/index.ts)
  validate issuer, time, required claims, and token shape.
- [Cognito adapter](../../../platform/adapters/aws/auth/cognito/src/index.ts)
  supplies Cognito issuer, key endpoint, access-token, and app-client facts.
- [Server request path](../../../platform/server/src/index.ts) maps a missing
  or untrusted authenticated-route identity to `401` before authorization or
  handler execution.

## 23. Platform Security, Part 3: Claims Become Permissions

JWT verification establishes that a trusted identity provider made claims about
Bill. A claim is a fact in the token, such as Bill's subject, group list, or
scopes. It is not automatically an application permission.

This next layer translates trusted identity facts into a small, stable
permission vocabulary that routes can check consistently.

### Four things that are easy to blur together

| Concept | Example | What it means |
|---|---|---|
| Claim | `cognito:groups` contains `accountant` | A trusted provider says this fact about Bill. |
| Group | `accountant` | A collection used by the identity/product administration model. |
| Permission | `billing.invoice:read` | A stable product action that a route may require. |
| Resource policy | “Bill may read only invoices for Benelux clients.” | A decision about a particular business object and its facts. |

The translation is deliberately narrow:

    trusted claim value
        -> configured mapping
        -> generic permission
        -> route's declared permission check

It does not decide tenant scope or a particular invoice's region.

### Bill's example

Imagine a verified token carries these facts:

    subject: bill-123
    cognito:groups: [accountant, benelux]

The target configuration might say:

    accountant -> billing.invoice:read
    customer-service -> customer.query:read

When Bill's `accountant` group appears, the generic mapping produces
`billing.invoice:read`. A route that declares that permission can pass its
coarse permission gate.

Bill's `benelux` group should not be copied into the permission name. A
permission such as `billing.invoice:read` answers “what kind of action?” The
Benelux restriction answers “which records?” That later question belongs to
tenant and resource authorization, where the system can inspect the specific
invoice and the caller's policy facts.

    Bill has billing.invoice:read
        -> route permission gate passes
        -> tenant resolver establishes the organisation boundary
        -> resource policy checks the invoice's client region against Bill's allowed scope
        -> allow or deny this particular invoice

For a customer-query route, Bill does not receive `customer.query:read` from
the shown mapping. He is authenticated, but the route permission check returns
`403 Forbidden`. That is different from the `401` outcome for an invalid or
missing identity.

### Where the translation happens

Generic `platform/security` can map a string-array claim, a space-delimited
scope claim, or a claim with a particular value. For every matching value, it
collects configured permissions into a set. A set prevents two matching groups
from accidentally producing duplicate permission entries.

The Cognito adapter supplies the provider vocabulary, while generic platform
security supplies the mechanism:

| Cognito adapter says | Generic platform security does |
|---|---|
| Group values are in `cognito:groups`. | Reads a configured string-array claim. |
| Scope values are in `scope`, separated by spaces. | Reads a configured space-delimited claim. |
| Target environment configuration contains the mappings. | Collects the resulting generic permissions. |

The current adapter reads group, scope, and claim mappings from target
environment configuration, including `PLATFORM_AUTHZ_GROUP_PERMISSIONS`,
`PLATFORM_AUTHZ_SCOPE_PERMISSIONS`, and
`PLATFORM_AUTHZ_CLAIM_PERMISSIONS`. This configuration is powerful policy and
should be controlled like other deployment configuration, even though it is
not a secret value.

### A useful startup-time safety check

There are two separate moments to check this mapping.

**At startup**, the server mounts every app and gathers the permissions apps
declared. The authentication hook can also list every permission its mapping
could grant. The server rejects the configuration if the mapping could grant a
permission that no mounted app declared.

That prevents a configuration typo such as:

    accountant -> billing.invoice:reed

from silently creating an orphan permission that looks almost right but
protects no declared route.

**For each request**, the platform compares the route's required permissions
with Bill's mapped permissions. Every required permission must be present. If
one is missing, the identity remains valid but the route returns `403`.

This is why the whole mounted registry matters. A route cannot prove by itself
that a permission was declared elsewhere; only startup validation can see both
the app declaration catalogue and the configured universe of granted
permissions.

### What this mapping does not do

The mapping does not authenticate Bill, determine Bill's tenant, look up which
client or region an invoice belongs to, or replace a resource-level authorizer.

It also does not instantly change the claims inside a token that was already
issued. If the identity provider embeds group facts in a short-lived token, an
administrator changing Bill's membership normally takes effect when Bill
receives a new token or the old one expires. Token lifetime, refresh, and
urgent revocation are separate product and identity-provider policy decisions.

### Misconception check

“Why not make the group itself the permission and skip the mapping?”

Because groups are administration vocabulary and permissions are application
vocabulary. One product might call its people `accountant`; another might call
them `finance-analyst`; both can need the same invoice-read action. Conversely,
one group can legitimately grant several permissions. Mapping keeps identity
administration separate from stable route contracts.

### Study question

Why is `billing.invoice:read` a better route requirement than
`benelux-accountant`?

Because the route needs to describe the action it protects, not one current
way of assigning people. The system can later grant invoice-read permission to
an auditor, automated process, or differently named regional group without
rewriting the route. Tenant and resource policy still decide which invoices the
caller may read.

### Repository evidence

- [Generic claim-to-permission mapping](../../../platform/security/src/index.ts)
  maps configured claim values to de-duplicated permissions and validates the
  configured permission universe.
- [Cognito mapping adapter](../../../platform/adapters/aws/auth/cognito/src/index.ts)
  identifies Cognito group and scope claim formats, then converts them to the
  generic mapping shape.
- [Platform server startup validation](../../../platform/server/src/index.ts)
  checks that potentially granted permissions were declared by mounted apps
  before the server serves traffic.
- [Platform server request authorization](../../../platform/server/src/index.ts)
  returns `403` when a valid identity lacks a route's declared permission.

## 24. Platform Security, Part 4: Browser Boundaries and Request Pressure

Authentication and authorization answer two important questions:

> Who is making this request, and may they perform this action?

They do not answer every security question. A browser can make cross-site
requests in surprising ways, a response can be placed inside another page, and
one caller can send work faster than the service can safely handle it.

The platform therefore has three small, separate defences:

| Defence | The risk it addresses | What it does **not** decide |
|---|---|---|
| CORS | Which browser origins may read an API response | Who the caller is, or whether they have a permission |
| Security headers | How a browser may interpret or embed a response | Whether the network connection is encrypted |
| Rate limiting | How quickly one request source may consume service capacity | Whether a request is legitimate or authorized |

Keeping them separate avoids a common mistake: calling all three “security”
and then assuming that one has done the work of another.

### Where they sit in the request path

The current server records its middleware sequence like this:

    request id and request logging
        -> CORS decision and security headers
        -> rate-limit check
        -> route parsing
        -> authentication
        -> authorization
        -> tenant and resource decisions
        -> handler

The rate limit is intentionally early. Rejecting an obvious flood before JWT
verification, database work, or a business handler conserves the capacity that
real callers need. Authentication and authorization still happen later for a
request that is allowed through.

### CORS: a browser-origin rule, not a caller identity rule

An *origin* is the scheme, host, and port of the page that JavaScript runs in.
For example, `https://app.example.com` and `https://reports.example.com` are
different origins even if the same company owns both.

Imagine these two pages ask the API for Bill's invoices:

    Benelux accounting app                 Unrelated malicious page
    https://app.example.com                https://not-our-company.example
              |                                        |
              | browser request                         | browser request
              v                                        v
    API sees an allowed Origin                 API sees an unlisted Origin
              |                                        |
              v                                        v
    sends matching CORS response headers       sends no CORS permission headers
              |                                        |
              v                                        v
    browser lets the app's JavaScript read     browser does not give that page's
    the response, subject to authentication    JavaScript permission to read it

The platform's CORS helper uses an **exact allowlist**. It reads the request's
`Origin` header and only emits the CORS response policy when that exact string
appears in the configured `corsAllowlist` (or the older single `corsOrigin`
setting). Its current policy names the HTTP methods `GET`, `POST`, `PUT`,
`PATCH`, and `DELETE`, and allows `authorization`, `content-type`, and
`x-request-id` request headers.

The important misconception is:

> “An unlisted origin cannot call the API.”

Not reliably. CORS is primarily a rule that browsers enforce around
cross-origin JavaScript and whether that JavaScript may read a response. A
script using `curl`, a mobile client, another server, or a deliberately
malicious client is not protected by CORS. The API must still authenticate the
bearer token and authorize Bill's requested action. Some browser requests also
require a preflight check before they are sent, but that does not turn CORS
into identity verification.

There is a useful present-state boundary here: the server now emits CORS
response policy for exact allowed origins and explicitly handles `OPTIONS`
preflight. For an approved origin it emits `Vary: Origin`, so a shared cache
does not reuse one origin's CORS response for another. A browser-facing target
still needs a deliberate credential policy: a real credentialed browser policy
should use named allowed origins, never a casual wide-open origin.

### Security headers: instructions for browsers receiving a response

The server applies these headers to its JSON responses:

| Header | Plain-language purpose |
|---|---|
| `content-type: application/json; charset=utf-8` | States that this response is JSON rather than leaving the browser to guess. |
| `x-content-type-options: nosniff` | Tells a browser not to reinterpret a response as another kind of content. |
| `x-frame-options: DENY` | Prevents another page from embedding the response in a frame, a clickjacking defence. |
| `referrer-policy: no-referrer` | Prevents the browser from sending referrer information with a follow-on request. |
| `content-security-policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'` | Sets a very restrictive browser policy: load no default resources, permit no framing ancestors, and do not accept a page base URL. |

These are a strong fit for a JSON API: an API response normally should not load
scripts, images, fonts, or be rendered inside a page. If the same server later
serves an HTML user interface, its content-security policy needs a separate,
deliberate review; simply copying the JSON API policy could break the UI or
encourage someone to weaken it broadly.

Another misconception:

> “Security headers encrypt the response.”

No. Encryption in transit is TLS/HTTPS, negotiated before HTTP headers are
available. These headers instruct a browser how to handle an already-delivered
HTTP response. Encryption at rest is another, storage-layer concern again.

### Rate limiting: protecting capacity without retaining secrets

The default limiter is an in-memory, fixed-window counter: by default, up to
1,000 requests per key in 60 seconds. It stores a small bucket for each key:
when that key's window begins and how many requests it has made. Once the
limit is reached, the platform returns `429` and includes the remaining wait in
safe error details.

Its current key selection is intentionally privacy-aware:

1. If a caller's authentication result has a safe `rateLimitKey`, use it.
2. Otherwise, if there is a bearer token, use a SHA-256 hash of it—never the
   raw token—as `token:<hash>`.
3. Otherwise, use only a client address supplied by a trusted host boundary.
   The generic Node listener supplies its socket peer address and never reads a
   caller-controlled forwarding header.
4. If none is available, share the `anonymous` bucket.

There is a subtle implementation detail worth noticing. The current server
performs a transport admission limit *before* authentication, so malformed or
oversized input cannot force identity work. The generic Node listener uses its
socket peer address at that first gate. After a protected route has established
identity, it also applies a principal-specific limit when the authentication
result provides a safe `rateLimitKey`.

This baseline is valuable but has limits:

- It is per process. Two server instances each have their own counters, and a
  restart forgets the old counters. A shared/distributed limiter is needed when
  limits must apply across instances.
- A fixed window permits a boundary burst: a caller can use their quota at the
  end of one minute and again immediately at the start of the next.
- Forwarded-IP headers are trustworthy only when a target-owned ingress policy
  proves that a proxy removes caller values and writes a trusted replacement.
  The generic server refuses to interpret them; a directly reachable service
  must never treat arbitrary client-supplied forwarding headers as fact.
- It limits request pressure; it does not make a denial-of-service attack
  impossible and it does not grant permissions.

### Put the three defences back in Bill's story

Bill's accounting browser at an allowed company origin asks to read a Benelux
invoice. CORS lets that company's browser JavaScript read the response; the
security headers make the JSON response harder to misuse in a browser; the
rate limiter stops a faulty loop from consuming unlimited capacity. Then the
JWT verifies Bill, the group mapping grants the invoice-read permission, and
tenant/resource policy decides whether *this* invoice is within Benelux.

If any one layer is missing, the other layers do not silently fill the gap.

### Study questions

1. Why is CORS insufficient if an attacker can use a command-line HTTP client?
2. Why is a per-process in-memory rate limit not a complete limit for a service
   deployed on several instances?
3. Why should a JSON API's strict content-security policy be reviewed instead
   of copied blindly when the server begins to serve HTML?

### Repository evidence

- [Security headers, exact-origin CORS policy, and in-memory rate limiter](../../../platform/security/src/index.ts)
  define the current generic platform mechanisms.
- [Server middleware order and `429` path](../../../platform/server/src/index.ts)
  show that headers and rate limiting happen before parsing and authentication.
- [Environment-backed CORS configuration](../../../platform/server/src/main.ts)
  supplies the current origin or allowlist configuration to the server target.

## 25. Security Policy Applied: Untrusted Input and Bounded Agents

The earlier security lessons explained the request path. We have now recorded
the policy that applies when a future capability introduces untrusted content,
LLM/RAG behaviour, or a model-facing tool.

The key rule is deliberately simple:

    untrusted content -> model proposal -> typed, independently authorized tool -> bounded result

The content may help the model reason; it cannot change the authenticated
principal, tenant, permission, resource policy, tool list, approval requirement,
or higher-priority governing policy. This protects against prompt injection.

The same policy also covers code injection. A request value or model output is
not allowed to flow into a general SQL, shell, template, file, network, or code
execution interface. It must pass a typed schema and a narrow, purpose-built
operation such as “replay this declared job message,” whose authorization and
tenant scope are checked again at the tool boundary.

### What is now governed

- One canonical [untrusted-input and bounded-agent safety rule](../../03.product/rules/concerns/untrusted-input-and-bounded-agent-safety.yml)
  applies to product harness, core, platform, apps, and products.
- A focused [implementation workflow](../../../.agentic/03.product/workflows/untrusted-input-and-bounded-agent-safety.md)
  requires a trust-boundary map, least-privilege tools, independent authorization,
  retrieval filtering, approval decisions, and adversarial proof before such a
  change proceeds.
- The rule is linked from the core, platform, and app layer rules, so it is not
  discoverable only by knowing the new filename.
- A retrieval fixture proves that a request for a tenant-aware remediation
  agent retrieves this policy rather than silently treating prompt injection as
  a deployment or generic automation problem.

### What is deliberately *not* claimed

Policy and workflow are not a general agent runtime, approval service,
distributed policy engine, or universal static injection scanner. When a
future agent needs one of those platform seams, the workflow requires a bounded
gap or implementation slice rather than an app-local or prompt-only bypass.

### Study question

Why must authorization happen inside the tool that replays a message, even if
the agent was already given a carefully written system prompt that says “only
replay safe messages”?

Because the tool is the point that causes the side effect. The tool can verify
current principal, tenant, target, approval, idempotency, and allowlist facts;
the prompt cannot reliably prove or enforce them.

## 26. Security Assessment Depth: What Needs Review?

The answer is not “every changed line needs a full security audit.” That would
turn security into paperwork and eventually cause people to stop taking the
reviews seriously.

Instead, every meaningful change follows the security baseline, while the
*depth* of assessment depends on the new trust boundary and blast radius.

### Three review depths

| Depth | Use it when | Example |
|---|---|---|
| Baseline check | A change uses existing approved patterns without adding a new sensitive boundary. | Rename an invoice-label helper while leaving its data, route, authorization, and output unchanged. |
| Focused assessment | A change adds or changes an input, route, job, persistence path, integration, permission, data classification, or tenant boundary. | Add an endpoint that reads invoices. |
| Deep assessment | A change is high impact, novel, or can act beyond one ordinary user request. | Bulk invoice export, tenant administration, payment action, identity policy, or an agent that may replay messages. |

The baseline is always present; a deep assessment adds more questions and more
proof. It does not replace the ordinary tests.

### A simple way to decide

Ask these questions in order:

1. **Did the change cross a trust boundary?** For example, did it accept a
   request, queue message, file, integration response, browser value, or
   retrieved document?
2. **Did it introduce or change authority?** For example, a permission, role,
   group mapping, tenant resolver, service identity, tool capability, or
   approval rule?
3. **Did it handle sensitive or tenant-scoped data?** A new query, export,
   file, audit record, search/retrieval path, or data-store change matters even
   if the user interface is small.
4. **Can it cause a consequential action?** Deleting, exporting, sending,
   paying, replaying, changing security policy, or changing infrastructure has
   a larger blast radius than showing a page.
5. **Is the capability new or merely reused?** Reusing a well-tested JWT
   verifier does not repeat its cryptographic review; adding a new claim
   mapping or a new permission still needs review of that adoption.

If the answer is yes to the first three, use a focused assessment. If the
answer is yes to the fourth, or the design includes an agent or automation,
use a deep assessment.

### Bill's invoice examples

| Change | Review depth | Why |
|---|---|---|
| Correct a spelling error in an invoice-page heading | Baseline check | It changes no trust or data boundary. |
| Add `GET /invoices/:id` | Focused assessment | It needs authentication, `billing.invoice:read`, tenant/resource policy, and denial tests. |
| Add “export all Benelux invoices” | Deep assessment | It can disclose a large amount of sensitive data and needs export scope, audit, retention, download security, and possibly approval decisions. |
| Add an agent that recommends or replays a failed invoice job | Deep assessment | Untrusted failure evidence, model reasoning, tool authority, tenant context, idempotency, audit, and approval all meet. |

### What is *not* a security review trigger by itself

A refactor that preserves behaviour, a copy change, or moving a private helper
does not automatically need a separate assessment. It still needs the normal
checks for the changed package. If the refactor accidentally alters a query,
permission check, error output, serialization path, or dependency boundary,
then it has become a security-relevant change and should be reassessed.

### The current harness rule

The new bounded-agent workflow uses this same idea. It triggers for untrusted
input at an interpreter boundary; LLM, retrieval, automation, or model-facing
tools; automated sensitive reads or changes; and changes to authority,
approval, audit, rate-limit, retry, or kill-switch behaviour. It stops rather
than improvising when the required platform security seam does not exist.

### Study question

Why is “reuse the existing JWT authentication capability” not enough evidence
to skip review when a new invoice-export route is added?

Because JWT verification only establishes identity. The export route still
introduces its own permission, tenant/resource scope, data-disclosure, audit,
and download/retention decisions.

## 27. A Focused Security Assessment: The Small Reusable Checklist

A focused assessment is not a 40-page compliance report. For an ordinary new
route, job, integration, or persistence boundary, it is a short record that
makes the reviewer and implementer ask the right questions before the change
becomes hard to undo.

It has five parts:

| Part | The question it answers |
|---|---|
| Change | What capability is being added or changed? |
| Risk | What could go wrong at the new boundary? |
| Controls | What specific mechanism prevents or limits that failure? |
| Proof | Which test or check demonstrates the control works? |
| Outcome | Did it pass, or is there a named gap that blocks completion? |

That is the whole starting shape. “Security audit” sounds large; in its first
useful form it is simply a disciplined explanation of these five things.

### Worked example: read one invoice

Imagine the billing app adds an endpoint to read one invoice by its identifier.
The focused assessment could read like this:

| Part | Invoice-route assessment |
|---|---|
| Change | Add a route that returns one requested invoice. |
| Risk | An unauthenticated caller, a customer-service representative, or an accountant outside Benelux could obtain it. A guessed invoice identifier might cross a tenant or regional boundary. |
| Controls | Require a verified principal; require `billing.invoice:read`; resolve trusted tenant context; evaluate the invoice's tenant/region policy; return a safe denial; avoid logging the invoice body. |
| Proof | Test no identity, missing permission, invoice from another tenant, invoice outside Benelux scope, and the permitted Bill case. |
| Outcome | Pass only if each denial causes no invoice data to be returned; otherwise name the missing control as a blocking gap. |

Notice that each risk has a matching control and a matching proof. If we say
“tenant isolation matters” but have no denial test, that is not yet evidence.

### What a focused assessment does *not* do

It does not re-review every shared component beneath the route. We do not
re-prove JWT public-key cryptography just because this route uses the existing
authentication hook. We ask whether this *new route* uses that hook correctly,
declares the right permission, applies the right scope, and handles its
particular data safely.

It also does not decide unrelated topics. Adding the route does not
automatically require choosing a new encryption provider, writing an incident
runbook, or building an agent approval service. Those become relevant only if
the route actually introduces that kind of risk.

### A useful self-check

Read the completed five parts from bottom to top:

    proof -> control -> risk -> change

If the proof does not actually demonstrate the stated control, or the control
does not really limit the stated risk, the assessment needs work.

### Study question

Why is “Bill can successfully read a Benelux invoice” not enough proof for the
new route?

Because a successful allowed case proves only that the route works. Security
proof needs the rejected cases too: wrong tenant, wrong region, missing
permission, and no identity must not disclose the invoice.

## 28. Security Assessment Lifecycle: Ask, Prove, Record

The five questions should not be asked only after code is complete. At that
point, the design may already be expensive to change. They appear at three
different moments for different reasons:

    change proposed -> questions selected -> implementation produces proof -> review decides -> evidence is recorded

### 1. Ask: before implementation

When the task introduces a route, job, integration, persistence boundary,
tenant/data boundary, permission, agent, or consequential action, the change
is classified as baseline, focused, or deep *before* implementation begins.

The assessment starts as a short prediction:

- this is the capability we are adding;
- these are the likely risks;
- these are the controls we expect to use; and
- these are the proofs we will need.

It is not a test that someone can “pass” by writing reassuring prose. It is a
design aid that makes the implementation plan visible before the code chooses
an unsafe path.

If the scope changes materially—perhaps a read-only invoice route becomes an
export route—the assessment is revisited. The old answers were for a smaller
blast radius.

### 2. Prove: during implementation and review

Reliability comes from making an answer point to concrete evidence rather than
asking a reviewer to trust the wording.

| Assessment answer | Reliable evidence |
|---|---|
| “This route requires invoice-read permission.” | A declared route permission plus a denied-permission test. |
| “This data is tenant-scoped.” | A tenant-aware repository/query path plus a cross-tenant denial test. |
| “The tool cannot replay a message without approval.” | A tool-side approval check plus a test showing the side effect does not happen when approval is absent. |
| “Secrets are protected.” | A redaction/secret-handling check and a test or scanner result; not a promise in a pull-request description. |

Consistency comes from three things:

1. **One controlled template** — every focused assessment has the same
   change/risk/control/proof/outcome fields.
2. **A control catalogue** — stable IDs such as `SEC-TENANT-001` let two
   reviews refer to the same requirement rather than inventing different names.
3. **Independent checks** — tests, validators, and scanners decide the parts
   machines can decide; a security reviewer handles the high-risk judgment that
   code cannot infer.

A deep assessment adds a human security review because, for example, a test
can prove that a proposed approval check exists but cannot independently decide
whether an invoice export should require a human at all.

### 3. Record: keep three kinds of record separate

This is where “audit” can become confusing. We need three different records:

| Record | What it says | Proposed home |
|---|---|---|
| Policy and control catalogue | What the rules are for every change. | Version-controlled shared documentation, proposed under `docs/06.shared/security-assurance/`. |
| Change assessment and evidence | What this feature on this commit was assessed against, its checks, findings, and outcome. | CI evidence attached to the pull request and later a durable, access-controlled evidence store. |
| Posture overview | The safe repository-wide summary: control coverage, open gaps, expiring exceptions, and links/digests to evidence. | A generated sanitized index in the proposed shared documentation area, backed by the durable evidence store. |

Runtime audit events are a fourth, separate kind of record: “Bill exported this
invoice at this time.” They belong in an append-oriented audit store, not in
Git or a pull-request report.

The first two proposed paths do **not** exist yet. The repository now has the
untrusted-input rule and workflow that tell us *when* to ask and what to prove;
it does not yet have the approved assessment schema, evidence store, or
repository-wide posture index. Naming that boundary prevents us from pretending
that a handbook entry is already compliance evidence.

### Bill's invoice route in the lifecycle

Before code, the change is classified as focused and names its likely risks:
unauthenticated access, missing permission, another tenant, and outside-Benelux
scope. During implementation, the route, tenant/resource policy, and denial
tests provide proof. In pull-request review, the reviewer checks that each
risk has a real control and a matching test. The assessment then records the
commit, result, and evidence links; it does not record the invoices themselves.

### Study question

Why should a report say “test X passed for commit Y” rather than merely
“tenant isolation is compliant”?

Because a control can be changed or regressed later. Binding the claim to a
specific test, commit, and baseline version makes it auditable and lets a later
review see exactly what was proven.

## 29. One Focused Assessment Record: Bill's Invoice Export

An assessment record is not a certificate that says “this change is secure.”
It is a compact, reviewable account of what the team considered, what the
system does to reduce the risks, and the proof available for *this exact
change*.

Imagine that the existing invoice dashboard gains an **Export invoices**
button. That is more consequential than simply viewing one invoice: it may
assemble a large amount of customer financial data into a downloadable file.
The change therefore needs a focused assessment.

### What the record would say

| Part of the record | Example for the export feature | Why it matters |
|---|---|---|
| Identity | An assessment ID, the change/commit reference, author, and date. | A reviewer can find the exact decision later instead of guessing which version it describes. |
| Scope | “Allow authorised users to export invoices visible in the dashboard.” | Stops the review silently expanding into an assessment of every invoice feature. |
| Assessment depth | Focused. | Makes it clear that this crossed a meaningful trust or data boundary, but did not automatically require the more extensive deep-review process. |
| Risks considered | Unauthenticated use; wrong permission; cross-tenant export; outside-Benelux invoices; excessive download size; sensitive data in generated files. | A successful export is not enough. These are the ways the feature could cause harm. |
| Controls selected | Require identity; require the export permission; apply tenant and Benelux resource scope in the data query; limit and log the export; use the approved storage/download path. | Connects each risk to a deliberate protective behaviour. |
| Evidence | Tests showing an accountant from Benelux can export only permitted invoices; denial tests for a customer-service representative, a different tenant, and an accountant outside Benelux; the relevant CI run links. | Lets another person verify the claim rather than trusting the author’s summary. |
| Findings and exceptions | For example, “Export files expire after the approved period; no exception requested.” | Makes unresolved risk visible. An exception is a decision with an owner and expiry, not a quiet omission. |
| Outcome | Approved, approved with time-limited exception, changes required, or rejected; plus reviewer and date. | Records who made the judgment and what must happen next. |

The record would refer to **facts about the export**, not copy invoices, tokens,
customer details, or raw vulnerability scans into Git. It should point to
sanitised evidence or controlled CI evidence instead.

### Walk it through as a reviewer

1. The reviewer reads the scope and asks, “Is this only a download of results
   the user may already see, or can it reveal more data?”
2. They compare the risks with the controls. “You listed cross-tenant export;
   where is tenant scope enforced—in the route, in a query, or both?”
3. They open the evidence. “Does the denied test actually use another tenant
   and another region, or only an unauthenticated request?”
4. They make the outcome match the evidence. A missing denial test means
   “changes required,” not “approved because the happy path works.”

This is why a template helps. It makes the same important questions hard to
forget, while still allowing the reviewer to identify a risk that the template
did not predict.

### Common misconception

**“If the assessment has all the fields filled in, the change is safe.”**

No. A completed record is evidence that the change was assessed. Its quality
depends on whether its risks are realistic, controls are genuinely enforced,
and proof actually tests the dangerous cases. The record makes those judgments
inspectable; it cannot guarantee that no future defect exists.

### Study question

Why does the export assessment need a test for an accountant outside Benelux,
even if that accountant has the same `invoice.export` permission?

Because permission answers *what kind of action* they may attempt. Tenant and
regional resource scope answer *which invoices* they may act on. Both decisions
must be true before an export is allowed.

## 30. Choosing Review Depth: Three People, Three Jobs

The person changing a feature should not be the only person deciding how much
security attention it receives. But a rigid automatic rule is not enough
either: a tool can see that a route was added, but may not understand that the
route quietly turns a single-invoice view into a bulk financial-data export.

The useful model is **proposal, signals, challenge**:

    author proposes a depth -> defined signals flag obvious risk -> reviewer confirms or raises it

### 1. The author proposes the starting depth

Before implementation, the author chooses baseline, focused, or deep and
writes a one-sentence reason.

For Bill's invoice export, the author might say: “Focused: this creates a
downloadable collection of financial data and must preserve permission, tenant,
and regional scope.”

This is not self-approval. It makes the author's understanding of the change
visible early, when it is still inexpensive for someone to say, “You have
missed an important boundary.”

### 2. Defined signals catch predictable cases

Later, the feature-builder harness can recognise a small set of clear signals:

| Change signal | Minimum expected response |
|---|---|
| A new public route or integration | At least a baseline review. |
| Authentication, permissions, tenant scope, sensitive data, export, or a consequential action changes | At least a focused assessment. |
| A privileged cross-tenant operation, a new trust boundary, high-impact automation, or a security exception is introduced | Escalate for deep review. |

These signals are a **floor**, not a complete risk detector. They prevent an
author accidentally treating an obvious permission change as ordinary
formatting work. They do not replace judgement.

### 3. A reviewer confirms or challenges the decision

The reviewer looks at the actual design and can raise the depth. For example:

- The author proposes focused review for invoice export.
- The reviewer discovers exports will be placed in a shared third-party file
  service with a long-lived link.
- That creates an additional trust and data-retention boundary, so the review
  becomes deep.

Raising the depth should be easy and recorded with a reason. Lowering it should
also be explicit: perhaps a proposed “export” is actually a browser print view
of one already-authorised invoice and creates no stored file. The point is not
to make everything deep; it is to make the reasoning visible and proportionate.

### Why three jobs are better than one

| Role | What it contributes | What it cannot safely do alone |
|---|---|---|
| Author | Knows the intended behaviour and starts the conversation early. | Independently certify their own blind spots. |
| Defined signals | Apply predictable minimums consistently. | Understand every product implication or novel attack path. |
| Reviewer/security owner for deep changes | Supplies independent judgement and context. | Reliably notice every routine trigger without the author and signals surfacing it. |

### What exists today, and what is deferred

The repository already has an untrusted-input and bounded-agent-safety workflow
that identifies focused-security triggers for that kind of work. It does **not**
yet have the general feature-builder classifier, assessment template, merge
gate, or reporting system described above. Those mechanics remain deliberately
deferred to the product-harness work.

### Study question

An author calls a change “baseline” because it adds only one export button.
What fact should cause the reviewer to raise it to focused review?

The button is not the risk measure. If it creates a downloadable collection of
customer financial data or changes permission, tenant, regional, or data-flow
boundaries, it requires at least focused review.

## 31. Three Different Records: Security Log, Audit Event, Observability

The word “log” is often used for every record a system writes. That is a
dangerous shortcut. Different records exist to answer different questions, and
trying to use one record for all three jobs usually produces poor security,
poor diagnosis, or both.

Imagine Bill exports the invoices he is permitted to see in the Benelux region.
One action may create three very different records.

| Record | The question it answers | Example from Bill's export | Main audience |
|---|---|---|---|
| Security log | “Did something suspicious, unsafe, or protective happen?” | A request was blocked because the caller had no valid identity, was rate-limited, or attempted an outside-Benelux export. | Security and incident responders. |
| Audit event | “Who performed this accountable action, on what, and what was the result?” | Bill, acting in tenant A, requested `invoice.export` for the Benelux scope at this time; the operation succeeded or was denied. | Compliance, business accountability, and authorised investigators. |
| Operational observability | “Is the system healthy and where is it slow or failing?” | The export endpoint took 1.8 seconds, generated a timeout error, or caused the queue depth to rise. | Engineers and operators. |

### 1. Security logs: protecting the boundary

A security log records an event worth defending against or investigating. It
might capture repeated failed authentication, a rate-limit decision, a blocked
permission attempt, an invalid token, or an unexpected request shape.

Its purpose is detection and response. It should contain enough context to
investigate—such as time, safe actor/request identifiers, decision, and
correlation ID—but never the token, password, invoice contents, or a copied
secret.

Bill's successful ordinary export may produce no special security log at all.
If a customer-service representative tries the same action without the export
permission, the denial can produce a security signal because it may reveal a
misconfiguration or suspicious pattern.

### 2. Audit events: proving accountable actions

An audit event is a more deliberate business and security record. It answers a
later question such as: “Who exported customer financial information on Tuesday
afternoon, under which tenant and authority?”

For the export, an audit event needs the verified actor, tenant, action,
resource or safe scope, outcome, time, and correlation identifier. It must be
append-oriented and protected against inappropriate alteration, because its
value is accountability. It records that an export happened; it does **not**
need to embed every invoice line in the audit system.

A useful misconception to avoid is: **“An application console log is an audit
trail.”** Console logs are often rotated, changed freely, incomplete, and
visible to people who should not see business accountability data. They can
help investigate; they are not automatically formal audit evidence.

### 3. Operational observability: keeping the service working

Operational records help engineers answer questions such as:

- Are invoice exports becoming slow?
- Did a queue back up after a deployment?
- Which service produced this error?
- Did one release increase the export failure rate?

Metrics, traces, and structured application logs may carry an operation name,
status category, duration, deployment version, and correlation ID. Their volume
can be very high, so they should avoid personal or financial data by default.
They are designed for diagnosis and trend analysis, not for a compliance
investigator to reconstruct every accountable business action.

### The same action, viewed three ways

    Bill requests invoice export
        -> audit event: accountable request and outcome
        -> observability: latency, status, trace and service health
        -> security log: only when a security-relevant signal occurs

The records may share a correlation ID so an authorised investigation can join
them. They should not become copies of one another. Sharing a stable reference
is safer than scattering the same sensitive facts through three systems.

### Current architecture boundary

The repository's shared audit rule already describes audit as formal
accountability evidence with actor, tenant, resource, action, time, and
correlation context, distinct from ordinary logs and analytics. Core already
has an audit-event schema and recorder *contract*. What remains future work is
the durable recorder, retention policy, provider adapters, and deployment
resources. Likewise, `platform/observability` has safe helper functions, but
not a concrete provider adapter in this worktree.

### Where these responsibilities belong

They should not become one broad `audit-logging-security-diagnostics` module.
That would make it tempting to treat all recorded facts as interchangeable. The
repository already has a useful split, with a few future implementation pieces:

| Layer and module | Responsibility | Status |
|---|---|---|
| `packages/core/logging` | Provider-neutral operational `LogRecord`, `Logger`, and redaction contracts. | Exists. |
| `packages/core/monitoring` | Provider-neutral metric and health-signal contracts. | Exists. |
| `packages/core/diagnostics` | Small, safe vocabulary for describing failure kind and possible recovery; it does not write logs. | Exists as a Core contract only. |
| `packages/core/audit` | Provider-neutral `AuditEvent` and `AuditRecorder` contracts for accountability records. | Exists. |
| `platform/observability` | Provides safe structured-log, metric, and trace-field helpers. | Exists as helpers; no concrete sink/adapter is wired here. |
| `platform/security` | Makes authentication, permission, CORS, and rate-limit decisions. | The decisions exist; a named security-log event model and emission path do not yet exist. |
| `platform/audit` | A future home for the durable implementation of the core `AuditRecorder` port. It should not be hidden inside ordinary logging. | Planned; not yet created. |
| `platform/adapters/<provider>/observability/<service>` | Translates the logging/metrics/tracing contracts to a concrete provider, such as the documented CloudWatch adapter path. | Adapter convention exists; provider work is future. |
| `platform/adapters/<provider>/audit/<service>` | Translates the audit recorder contract to the chosen durable audit store. | Future. |
| `infra/04.deploy` | Provisions log groups, monitoring resources, audit storage, encryption, access controls, retention, and alerts. | Infrastructure concern, not a core contract. |

Here is the crucial distinction between the three output types:

| Output type | What exists now | Where its future runtime writing belongs |
|---|---|---|
| Security log | Security controls can deny a request, but they do not yet create a named, structured security record such as `security.permission.denied`. | `platform/security` decides *which* security outcomes are worth recording; `platform/observability` safely writes the redacted operational record through a provider adapter. |
| Audit event | `packages/core/audit` already defines the typed event and recorder port, including actor, target, tenant, outcome, and correlation information. No durable platform recorder exists yet. | A future `platform/audit` implements the recorder; an audit adapter writes it to the durable provider store. Apps decide which product action, such as `invoice.export`, requires an audit event. |
| Operational record | `platform/observability` can normalise fields and record logs and metrics through supplied logger/metrics ports. No concrete external sink is implemented here. | `platform/observability` remains the owner; its provider adapter exports records to the chosen log, metric, and tracing services. |

The direction of travel is:

    app chooses “invoice.export must be auditable”
        -> core supplies the audit/logging/metric contracts
        -> platform supplies safe runtime behaviour
        -> adapter selects the provider implementation
        -> infrastructure provisions and protects the provider resources

`diagnostics` is deliberately different. It supplies safe labels such as “a
provider timeout occurred” so logging, monitoring, audit, and future recovery
workflows can describe a failure consistently. It does not become a fourth log
store. It currently exists only as `packages/core/diagnostics`; there is no
`platform/diagnostics` runtime module, and we should not create one unless a
distinct runtime responsibility emerges.

Also keep audit/logging separate from business events. “Invoice export was
requested” might be a product event that starts a worker job; an audit record
explains who requested it and with what result; an operational log explains how
the job ran. One action can legitimately create all three, but none replaces
the others.

### Study question

Why is a correlation ID useful on all three record types, even though the
records serve different purposes?

It lets authorised people connect the same request during diagnosis or an
investigation without copying its sensitive details into every record.

## 32. Audit Integrity: Append-Oriented and Tamper-Evident

An audit record is meant to answer a difficult later question: “What actually
happened?” That answer is not useful if the person whose action is being
investigated can quietly rewrite or remove the record.

### Append-oriented: add the next fact; do not rewrite the old one

“Append-oriented” means the normal audit operation is to **add** a new record.
It is not to edit yesterday's record in place.

Suppose Bill requests an invoice export:

1. The system records that Bill requested the export, under his tenant and
   Benelux scope.
2. The export later succeeds, fails, or is denied.
3. The system records that outcome as another accountable fact, or records one
   completed event if the design makes the request synchronous.

If an administrator later discovers that the requested export had the wrong
scope, they add a correction, revocation, or remediation event. They do not
change the original event so it now appears that the wrong request never
happened.

This does **not** mean data can never expire. Retention, legal hold, privacy,
and deletion requirements still exist. It means those changes are governed,
authorised operations with their own evidence—not an ordinary “update audit
row” button.

### Tamper-resistant versus tamper-evident

These related terms mean different things:

| Property | Meaning | Example |
|---|---|---|
| Tamper-resistant | Makes unauthorised alteration difficult or impossible for ordinary actors. | Strict writer permissions, separate reader access, protected backups, and a storage service that does not offer ordinary updates. |
| Tamper-evident | Makes a later alteration detectable. | A protected sequence, signed records, or a cryptographic chain that no longer verifies after one record changes. |

Tamper-evident does **not** mean “nobody can ever tamper with it.” It means an
investigator has evidence that a record was altered, omitted, or reordered—if
the integrity mechanism, its keys, and the verification process are themselves
protected.

In a high-risk design, the two properties work together: access controls make
tampering hard; integrity checks make successful tampering easier to detect;
separate operational oversight makes abuse of privileged access harder to hide.

### Why ordinary logs and Git are not enough

| Store | Helpful for | Why it is not the runtime audit store |
|---|---|---|
| Application log | Diagnosing an export failure. | May be rotated, sampled, mutable, incomplete, broadly accessible, or missing the accountable action fields. |
| Git and `commitLogs` | Recording code, plan, and change-assessment history. | Cannot safely receive live customer actions; it has the wrong availability, access model, retention model, and operational write path for runtime audit evidence. |
| Durable audit store | Investigating a specific accountable runtime action. | Must be deliberately designed with writer/reader access, retention, integrity, and export controls. |

Git is still useful for a different audit question: “Who changed the audit
implementation or policy?” The durable audit store answers: “Who exported
these invoices in production?” Keep those questions separate.

### Durable does not mean permanent

Audit records are often retained much longer than high-volume troubleshooting
logs, but “keep them forever” is rarely the right default. A record may contain
personal, customer, financial, or security information, so its retention must
be justified by the accountable purpose, contract, policy, and applicable legal
or regulatory obligations.

| Record class | Typical retention reasoning |
|---|---|
| Operational troubleshooting logs | Kept only long enough to diagnose outages, trends, and recent incidents; high volume often makes shorter periods sensible. |
| Security logs | Kept long enough to detect and investigate suspicious patterns, subject to risk and privacy controls. |
| Audit events | Kept for the defined accountability, dispute, compliance, customer-review, and legal purpose; this is often longer, but must still be explicit and justified. |

The policy must define more than a number of days. It needs the event class,
purpose, start point, normal retention period, authorised readers, regional
placement, and what happens at expiry: deletion, anonymisation, or a governed
archive. A legal hold or live investigation may pause normal deletion for a
defined relevant set; it should be visible as another accountable decision.

So a future product might choose short operational-log retention, longer audit
retention for invoice exports and authority changes, and a documented review
process. It must not assume “audit = permanent” or “two weeks is enough”
without a policy decision. Append-oriented integrity applies while the record
is retained; approved expiry is a separate lifecycle operation.

### What a future audit slice must decide

Before selecting a store, the future vertical slice must decide the threat
model: who might try to alter records, what access they hold, how long evidence
must remain, whether a tenant can access its own records, where records may
reside, and how an authorised investigation verifies integrity. A storage
product alone cannot answer those questions.

The current platform plan records this as deferred work. Core already supplies
the portable audit-event and recorder contracts; the durable recorder, adapter,
storage, access controls, retention, and integrity proof have not been built.

### How a real system checks for tampering

A strong audit path uses several independent controls. Each closes a different
hole:

| Control | What it protects against | Important limitation |
|---|---|---|
| Separate writer and reader permissions | A normal user, application developer, or investigator editing records freely. | A highly privileged storage administrator may still be a risk. |
| Append-only or immutable retention storage | Ordinary updates and deletes after a record is accepted. | It does not prove the record was complete or correct when written. |
| Per-record or per-batch hashes | A stored record changing after its hash was calculated. | A hash stored beside the record can be recomputed by the same attacker. |
| Digital signatures | An attacker forging the signed digest without the signing key. | The signing key and key-management access must be independently protected. |
| Chained or anchored digests | A record or batch being removed, reordered, or replaced within a verified sequence. | A chain alone cannot prove the newest unanchored end was not removed. |
| Scheduled verification and alerts | A discovered integrity failure being ignored. | Verification must be performed, monitored, and retained as evidence. |

Here is the conceptual flow for Bill's export. The audit writer records the
plain, versioned event. A trusted process creates a hash for that record or a
batch of records. It puts those hashes and the previous digest reference into a
digest, then signs the digest with a key that the ordinary application writer
cannot use. The raw events and signed digest are retained with separate access
controls. Later, a verifier recomputes the hashes, verifies the signature with
the public key, and checks the digest sequence.

If someone changes Bill's event, its recomputed hash no longer matches the
signed digest. If they delete a record or digest from the middle of a verified
sequence, the chain breaks. If they try to create a convincing replacement,
they need the separately protected signing key. A periodic verifier should
raise an alert and retain its own result when any check fails.

The most important misconception is that a hash by itself solves the problem.
It does not. An attacker who can change both a record and its nearby hash can
calculate a new hash. The integrity evidence must be signed or anchored outside
the attacker's ordinary write authority, and the verification process must not
depend on that same authority.

Large systems often do this in batches rather than signing every individual
event. One signed digest can list many event hashes, or commit to them through a
tree structure. The verification result is the same question: do the stored
events still match the independently protected digest?

### Is that a blockchain?

It is **blockchain-like in one narrow sense**: both can link records with
hashes so changing history becomes detectable. But a normal enterprise audit
trail does not need to be a blockchain.

| Audit integrity chain | Blockchain |
|---|---|
| One organisation operates the audit writer and store, with deliberately separated access roles. | Multiple parties use a shared ledger and need a way to agree on ordering without trusting one operator. |
| Uses append-oriented storage, hashes, signatures, and independent verification. | Also uses linked hashes, but adds distributed replication and a consensus protocol. |
| Does not need cryptocurrency, proof-of-work, or a public network. | May use public or permissioned consensus, and can have substantially different cost, privacy, and operational trade-offs. |

For our future platform, a signed, append-oriented audit store with protected
keys, provider controls, and scheduled verification is the simpler default.
We would consider a permissioned ledger only if several independent
organisations had to share the same evidence while none could be trusted to
operate the record system alone. No current requirement calls for that.

### Common misconception

**“Append-only means we may never correct an audit record.”**

No. It means corrections must be new, accountable facts. The history should
show both the original event and the later correction, rather than silently
substituting one story for another.

### Study question

Why is a protected audit store still not necessarily tamper-evident?

Access controls can prevent ordinary edits, but without an integrity mechanism
and a verification process, a highly privileged actor or compromised system may
alter a record without leaving reliable evidence of the change.

## 33. Audit Policy: What Is Important Enough to Record?

An audit trail is not a video camera pointed at every line of code. Recording
every request, page view, retry, and internal detail would be expensive, noisy,
and may create a new privacy problem. Audit policy selects actions for which a
later accountable answer matters.

The useful question is not “Did the system do something?” It is:

> “Would a customer, investigator, regulator, or authorised operator later need
> to know who caused this meaningful outcome, under what authority, and with
> what result?”

### A practical decision test

An action is a strong audit candidate when it does one or more of these things:

| Signal | Example |
|---|---|
| Changes authority | An administrator assigns the accountant role or adds Bill to the Benelux group. |
| Reveals, exports, or shares sensitive data | Bill exports invoices or creates a long-lived download link. |
| Changes material business data | A payment status, invoice, contract, or legal hold is created, changed, or deleted. |
| Causes an external or irreversible effect | The system sends a customer notification, submits a payment instruction, or deletes a record. |
| Acts across many records or a special scope | A bulk export, mass update, cross-tenant support operation, or break-glass action occurs. |
| Approves, rejects, overrides, or grants an exception | A human approves a high-impact request or temporarily bypasses a normal control. |
| Changes security or policy configuration | A permission mapping, retention rule, authentication setting, or product policy changes. |

This is a risk-based guide, not a magic checklist. Reading one ordinary public
page is usually operational telemetry, not audit. Viewing one highly restricted
customer record may be auditable because the data and accountability context
are different.

### Bill's invoice examples

| Action | Likely record choice | Why |
|---|---|---|
| Bill loads his normal invoice list | Usually operational telemetry only. | Useful for performance diagnosis, but not automatically an accountable event. |
| Bill views a restricted invoice | Product policy decides; often audit if the record is sensitive or regulated. | The data access itself may need an accountable explanation. |
| Bill exports Benelux invoices | Audit event, plus operational telemetry. | It creates a downloadable collection of financial data. |
| A customer-service representative attempts the export | Security log; audit too if policy treats sensitive denied attempts as accountable. | The denial can indicate misuse, a training issue, or an attack pattern. |
| An administrator adds Bill to the accountant group | Audit event, plus operational telemetry. | It changes Bill's future authority. |

### Who decides?

No one layer should invent all audit policy:

| Owner | Decision it owns |
|---|---|
| App or feature owner | Names the action and proposes why it is accountable: for example, `invoice.export`. |
| Product owner and security/privacy policy | Set the reusable baseline: exports, role changes, sensitive-data access, exceptions, and high-impact actions require audit. |
| Tenant policy | May tighten the product baseline—for example, require audit for every restricted-record view—but must not silently weaken it. |
| Platform | Provides the safe recorder path and enforces the record contract. It does not decide whether “invoice export” matters to a particular product. |
| Infrastructure and deployment owner | Protect the store, retention, access, residency, and integrity controls selected for the environment. |

This prevents two opposite mistakes. Platform does not become a catalogue of
every product action, and each app does not make up security expectations from
scratch.

### A small policy example, in words

A product baseline could say: “Audit all exports, permission or membership
changes, policy changes, approval/exception decisions, and high-risk data
access. Audit denied attempts for those actions when the policy identifies a
security or accountability need.” Each feature then names its relevant action
types and supplies the target/context, while the shared recorder preserves the
common record shape.

The current repository has the Core audit contract and this policy direction,
but not yet the feature-harness policy registry or the durable runtime recorder.
Those remain planned work; this lesson defines how the later decision should be
made.

### Common misconception

**“If an action is denied, there is nothing to audit because nothing happened.”**

A denied attempt can be meaningful: someone requested a sensitive export,
attempted a privilege change, or exercised break-glass access. It did not cause
the business effect, but it may still require accountable evidence. The policy,
not an automatic rule, decides which denials are important enough to retain.

### Study question

Why should “all exports are audited” be a product baseline rather than a hidden
rule inside the invoice-export screen?

Because another feature may later export contracts, users, or reports. A named
product policy creates a consistent rule across features; each feature still
declares its own action and target context.

## 34. Denied and Failed Actions: Audit, Security Log, Both, or Neither?

An HTTP status such as `401`, `403`, or `500` does not decide the record type
by itself. The policy needs to understand the attempted action, its sensitivity,
the actor/context, and whether there is a security signal or an accountable
business outcome.

### Start with the questions each record answers

| Record | Question | It is selected because... |
|---|---|---|
| Audit event | “Who attempted this significant action, under which authority, and what was the outcome?” | The product policy says the action is accountable, whether it succeeds, is denied, or fails. |
| Security log | “Did a protective control fire or did this look suspicious?” | The denial, authentication failure, unusual volume, cross-tenant attempt, or other pattern needs security investigation. |
| Operational record | “Why did the system behave this way?” | Engineers need diagnostic details such as error class, latency, dependency timeout, or retry count. |

### Four invoice-export cases

| Situation | Likely records | Why |
|---|---|---|
| An anonymous browser visits the export URL once and receives `401`. | Operational telemetry; perhaps a low-level security signal according to policy. Usually no audit event. | A routine unauthenticated request has not yet attempted an accountable action under a verified actor. |
| A customer-service representative requests `invoice.export` and receives `403`. | Security log; audit event too if the product baseline says denied sensitive exports are accountable; operational telemetry. | The action is sensitive and the denial may indicate misuse or a training/configuration issue. |
| Bill is allowed to export Benelux invoices, but the file service times out. | Audit event with failed outcome; operational logs/metrics/traces. Usually no security log. | Bill made an accountable request, but the failure is technical rather than suspicious. |
| One identity repeatedly attempts exports across tenants or regions. | Security log and incident signal; audit events for sensitive attempted actions if policy requires; operational telemetry. | The pattern, not merely one `403`, may indicate active abuse or a broken client. |

Notice that a denied action can be both a security and an audit matter. The two
records have different meanings:

- The **security log** says the protective control was triggered and may join a
  pattern of abuse.
- The **audit event** says a particular accountable action was attempted by a
  particular actor, with a denied outcome.

### When neither gets a durable individual record

Not every rejected input needs a durable event. A malformed optional filter,
an expired page-navigation link, or a routine validation error may be counted as
an operational metric or handled in a bounded troubleshooting log, without
creating an individual audit or security record. The policy should avoid keeping
identifiable data merely because a user made an ordinary mistake.

### A compact decision order

1. **Is the action accountable by product/tenant policy?** If yes, create an
   audit event and record its actual outcome: succeeded, denied, or failed.
2. **Did a security-relevant control or suspicious pattern occur?** If yes,
   create a safe security signal.
3. **Does an engineer need to diagnose the system's behaviour?** If yes,
   produce bounded operational telemetry.

These questions can all be true. They should be answered independently rather
than forcing one record to do every job.

### Current implementation boundary

This is policy guidance for the future record pipelines. The current platform
does not yet emit structured security logs or persist durable audit events, so
it cannot claim to make these distinctions at runtime yet. The lesson tells the
future feature, platform, and policy work what it must decide.

### Study question

Why does Bill's failed export normally need an audit event but not a security
log?

The export is an accountable action under the audit policy, so its failed
outcome matters. A file-service timeout is an operational failure, not by itself
evidence of suspicious or malicious behaviour.

## 35. Data Minimisation: Enough Audit Evidence, Not a Second Data Store

An audit event should explain an action without copying the sensitive data that
the action touched. This matters because audit records are often durable,
searchable, exportable, and accessible to a different set of people than the
original business data.

### The useful facts for Bill's export

For a Benelux invoice export, the audit event normally needs facts such as:

| Useful fact | Why it is needed |
|---|---|
| Verified actor reference and actor type | Identifies who or what caused the request without copying credentials. |
| Tenant reference | Establishes whose data and policy context applied. |
| Stable action name and event version | Makes `invoice.export` interpretable after the feature changes. |
| Target or safe scope reference | Identifies the export job or resource scope, such as Benelux, without embedding every invoice. |
| Outcome, timestamp, and correlation ID | Explains what happened and joins authorised investigation records. |
| Safe reason or policy reference | Explains a denial or approval without copying raw request content. |
| Bounded summary, when justified | For example, an invoice count or output-file identifier—not invoice rows or a download URL. |

The event answers “Bill exported 217 permitted invoices for this tenant and
region at this time.” It does **not** need to contain the invoices, customer
names, balances, file contents, or the signed download link.

### Facts that should normally stay out

| Do not put this in audit metadata by default | Why |
|---|---|
| Passwords, tokens, cookies, API keys, credentials, or raw authorisation headers | They grant access or materially increase the impact of a breach. |
| Raw request or response bodies | They often contain unnecessary personal, financial, or confidential data. |
| Invoice lines, customer details, document contents, and uploaded files | The audit system would become a duplicate sensitive-data store. |
| Raw stack traces or provider error payloads | They are diagnostic data, can be noisy, and may expose implementation or secret details. |
| Chat prompts, retrieved content, voice transcripts, or audio | They need a separate, explicit product privacy and retention decision. |
| Signed URLs, file-system paths, or rich provider objects | They can create unintended access, leak topology, or resist safe serialization. |

### Why each of these is dangerous in an audit event

| Value | What it is | Why it must stay out by default | Safer audit fact |
|---|---|---|---|
| Token, credential, cookie, or raw `Authorization` header | Proof that a caller may be authenticated; many tokens are bearer credentials, meaning possession can be enough to use them. | Anyone who later reads, exports, backs up, or searches the audit event may gain the ability to impersonate the caller. An expiry time reduces risk but does not make disclosure acceptable. | A verified actor ID, actor type, authentication method label, or token/key identifier that cannot be replayed. |
| Invoice rows, balances, customer names, or file contents | The actual business and personal data Bill accessed or exported. | The audit store becomes a second financial/customer-data store with different readers, retention, exports, and breach surface. Its access policy may be broader than the original invoice system. | Resource/export ID, tenant, safe scope, count, classification, and outcome. |
| Raw request or response body | A complete unfiltered copy of what a caller sent or received. | It is a grab bag: it can contain credentials, personal data, free text, files, payment details, and untrusted content. Its shape changes per feature, so it cannot be safely governed as stable evidence. | Named, allowlisted fields that explain the action, such as action type, safe target reference, and validation outcome. |
| Stack trace or provider error payload | Developer diagnostics from code, databases, cloud SDKs, or third-party services. | It may reveal internal paths, query fragments, host names, implementation details, provider response bodies, or even secrets accidentally included by a dependency. It is also noisy and unstable as audit evidence. | A stable error class/code and a correlation ID pointing authorised engineers to redacted operational diagnostics. |
| Chat prompt, retrieved content, voice transcript, or audio | Conversational input/output and, for voice, potentially a recording of a person. | It can contain confidential instructions, personal or financial data, pasted credentials, third-party content, or sensitive spoken details. Audio and transcripts require their own consent, purpose, access, residency, and retention decision; they are not made safe merely by calling them audit data. | Conversation/session reference, channel type, approved action type, confirmation reference, and outcome—only if the relevant policy justifies them. |
| Signed download URL | A time-limited link that commonly grants direct access to a file. | It is a capability: somebody who obtains the URL may be able to download the export while it remains valid. Storing it durably defeats the purpose of keeping that access link short-lived and controlled. | A controlled file/export identifier; an authorised investigator can resolve it through the file service under current access checks. |

The rule is not “never retain sensitive data anywhere.” A product may have a
specific legal, security, or operational reason to retain some of it, but that
requires an explicit data model, lawful purpose, restricted access, retention
schedule, and suitable storage. It should not arrive accidentally through a
generic audit-metadata field.

An opaque internal identifier is often safer than a human-readable name, but it
is not automatically harmless. It may still be personal data or sensitive in a
given product. Classification and purpose decide whether the reference belongs
in the event.

### Why “redact it later” is too late

Once a raw token or invoice body has been written, it may already have reached
replicas, indexes, backups, exports, alert notifications, or an investigation
tool. Removing one visible copy does not prove the sensitive value has gone
everywhere.

The safer design is to minimise and validate **before** the event crosses the
audit-recorder boundary:

1. Construct events from a small allowlist of named facts.
2. Classify each optional field and reject or redact disallowed values before
   serialization.
3. Keep rich technical diagnostics in the bounded operational path, not in the
   durable audit event.
4. Test that dangerous fields cannot enter the recorder, including through
   error objects or future channel inputs.

### The reusable standard: envelope plus action profile

The best general pattern is not one huge universal audit schema, and not a
free-form `metadata` bag. It is two layers:

| Layer | Purpose | Examples |
|---|---|---|
| Fixed audit envelope | The minimum facts every accountable event needs, in the same shape across the platform. | Event ID and version, occurred-at time, actor reference/type, tenant/context, action, target, outcome, correlation ID, and safe reason/policy reference. |
| Versioned action profile | A small allowlist of extra facts justified by one stable action type. | `invoice.export` may allow region, export ID, record count, and approved output classification. A permission-change action may allow old/new permission identifiers, but not the user's raw profile. |

The profile acts like a narrow form. If `invoice.export` v1 permits only
`region`, `exportId`, and `recordCount`, an attempted field such as
`invoiceRows`, `downloadUrl`, `authorizationHeader`, or `customerName` is
rejected before persistence. Adding a new field is a small reviewed change to
that profile, with its data classification and retention purpose—not a casual
new property in a feature handler.

For every candidate field, the standard asks:

1. Which accountable question does this field answer?
2. Can a stable identifier, category, count, or classification answer it
   instead of the original sensitive value?
3. Is the field always allowed, conditionally allowed with an explicit policy,
   or forbidden?
4. What are its maximum length, cardinality, and permitted value type?
5. Is it safe for the audit store's readers, retention period, region, and
   export path?

Enforcement should happen in several places: typed/profile-aware event builders
make the safe path easy; a recorder validator rejects unknown keys and unsafe
shapes; bounded sizes prevent accidental payload dumps; and tests deliberately
try to pass a token, invoice body, raw error, transcript, and signed URL. A
reviewer then examines changes to profiles as security/privacy changes, not as
routine logging text.

The current Core audit contract supplies a portable event envelope and JSON-safe
metadata values, but it does not yet implement this repository-wide profile
registry or unknown-field rejection. The future security-record vertical slice
must add that stricter boundary rather than relying on every caller to remember
the rules.

### One capability, separate record profiles

Every capability should decide whether it needs audit evidence, security
signals, and operational observability. It should **not** send the same full
audit profile to every system.

| Concern | What the capability declares | What it needs to know |
|---|---|---|
| Audit | Whether the action is accountable and its action-specific audit profile. | Who acted, tenant/context, safe target/scope, outcome, and the few justified durable facts. |
| Observability | Its operational instrumentation profile. | Operation/capability name, status, latency, error class, retry count, deployment/version, and safe correlation reference. |
| Security logging | Which control outcomes or patterns are security-significant. | Control/decision type, safe actor or source reference, capability/route, outcome, and correlation reference. |

These profiles can share a few stable references—capability/action name,
correlation ID, safe tenant/actor reference, and outcome—so an authorised
investigation can connect them. They should not share their entire metadata.

For `invoice.export`, the audit profile might retain a safe export ID, Benelux
scope, and record count. The operational profile might retain duration, status,
error class, and job retry count. The security profile might retain a
permission-denied control name and correlation ID. Copying the audit record's
data into metrics or logs would be unnecessary and can be dangerous; for
example, actor, tenant, or export IDs may create privacy or high-cardinality
problems in a metrics system.

The future feature harness should therefore ask each capability three small
questions: “Is this action auditable?”, “What operational proof or diagnosis is
needed?”, and “Which security outcomes are significant?” It should link the
three profiles by stable identifiers, not merge them into one giant event.

### Ownership

The feature owner knows which target and scope explain the action. Product
security/privacy policy decides the baseline of permitted audit facts and the
retention purpose. Core provides a portable, JSON-safe audit contract.
Platform and its future recorder enforce the boundary before persistence.
Infrastructure protects the resulting store. No individual layer can safely
make all these decisions alone.

The current Core audit contract already excludes many unsafe runtime shapes, but
the field taxonomy, redaction policy, and durable recorder remain planned work.
Until they exist, we must not claim automatic audit-data minimisation at runtime.

### Study question

Why is an output-file identifier potentially acceptable in Bill's audit event,
but a signed download URL is not?

The identifier can help an authorised investigation find the controlled file
record. A signed URL may itself grant access and can become a security secret in
the durable audit store.

## 36. Audit Anchors: Actor, Target, Tenant, and Scope

An audit event without an actor and target is like a sentence that says “an
important thing happened.” It cannot reliably answer who was accountable or
what was affected.

The current Core audit contract already names these anchors: `actor`, `target`,
optional `tenantId`, outcome, timestamp, correlation ID, and a possible parent
target. The later recorder must preserve those facts; it must not reduce them
to a vague message string.

### Actor: who or what caused the action?

An actor is the accountable origin of an action. It is not simply whatever
network connection happened to reach the server.

| Actor kind | Example | Useful audit meaning |
|---|---|---|
| User | Bill clicks Export invoices. | A verified principal reference identifies Bill as the person requesting the action. |
| Service | A payroll integration calls a permitted API. | The service principal identifies the authorised machine identity. |
| Anonymous | An unauthenticated visitor requests a public form or protected URL. | The event deliberately says no identity was verified; a safe source/session reference may be useful under policy. |
| System | A scheduler or platform maintenance process runs a governed task. | The system component or job identity explains that no human directly performed this occurrence. |

An agent, chat interface, voice interface, or worker is **not** a magical new
authority. If an agent executes an action for Bill, the audit design must make
clear whether Bill is the accountable requester, a service is the technical
executor, and which approved policy allowed the delegation. Natural-language
text, a voice recording, or a model output is never the actor identity.

The current Core contract supports user, service, anonymous, and system actor
types. It has one actor field. If a future capability genuinely needs both “Bill
requested this” and “service X executed it,” that delegation model needs an
explicit governed contract change or action-profile design. It should not be
smuggled into an unstructured metadata note.

### Target: what did the action affect?

A target is the resource, operation, or bounded collection that the action was
about. It needs a stable type and identifier, not only a display name.

| Action | Suitable target | Why |
|---|---|---|
| Bill views one invoice | Invoice ID, with an optional parent customer/account reference. | Identifies the particular protected resource. |
| Bill exports 217 invoices | Export-job or export-file ID, with tenant as context and Benelux plus count in the action profile. | Avoids writing 217 invoice rows into audit while retaining a controlled way to investigate. |
| Administrator adds Bill to a group | Membership or assignment ID, with a parent group or principal target where relevant. | Identifies the authority change, not only the screen used to make it. |
| Scheduler runs nightly cleanup | Scheduled-run or job-execution ID, with the job definition as parent. | Distinguishes one occurrence from the schedule definition. |

The Core target shape already permits a parent target. That is useful for a
resource hierarchy, such as an invoice under a customer account, without
duplicating all business data in every event.

### Tenant and scope: which boundary applied?

Tenant is neither the actor nor the target. It answers: “Under whose data and
policy boundary did this action take place?” For Bill's export, the tenant and
Benelux scope explain why an allowed invoice action in one context may be
denied in another.

Where a tenant fact exists, the event should carry it explicitly. Some platform
or global policy actions may be deliberately tenantless, but that absence should
mean “global/system context,” not “we forgot to include tenant.” Region, group,
relationship, and attribute constraints belong in the action's safe profile as
scope facts; they are not substitutes for the tenant boundary.

### Read the event as a complete sentence

A useful event can be read like this:

> Bill, a verified user, requested `invoice.export` against export job E-42 in
> tenant A for the Benelux scope. The outcome was denied, correlated with this
> request, because the required permission was absent.

That sentence has enough accountability context without listing invoices,
customer names, the original request body, or the access token.

### Proposed v1 audit taxonomy: keep the dimensions separate

Yes, a stable shared vocabulary makes audit records easier to scan, validate,
search, report on, and compare across capabilities. The important design rule
is that these are **separate fields**, not interchangeable words in one long
event name.

| Dimension | Proposed v1 shape | Why it is separate |
|---|---|---|
| Event type | `<app>.<resource>.<verb>`, such as `billing.invoice.export`. | Names the durable meaning of the accountable action. The current Core contract already accepts lowercase dot-separated event types. |
| Event version | Positive integer, starting at `1`. | Lets the record remain interpretable when its permitted profile changes. |
| Actor type | `user`, `service`, `anonymous`, or `system`. | Says who or what held the accountable authority; these types already exist in the Core contract. |
| Interaction channel | `web`, `mobile`, `chat`, `voice`, `cli`, or `api` when known and policy justifies recording it. | Says how the request was initiated, not who had authority. |
| Execution context | `server`, `worker`, or `scheduler` when useful. | Says where the action was performed; a web request may later be executed by a worker. |
| Outcome | `succeeded`, `denied`, or `failed`. | Says what happened to the action; these outcomes already exist in the Core contract. |
| Target | Stable type, ID, and optional parent. | Says what was affected without relying on a display name. |

The vocabulary for source is often accidentally mixed together. `web`, `mobile`,
`chat`, and `voice` are interaction channels. `user`, `service`, and `system`
are actor types. An `integration` is usually an external client or a service
actor using the `api` channel, while a worker or scheduler is an execution
context. Separating them lets us ask precise questions later: “Show all invoice
exports,” “show all voice-initiated actions,” or “show denied service actions.”

For verbs, start with a small controlled vocabulary and prefer one word for one
meaning. For example:

| Verb family | Proposed verbs |
|---|---|
| Data lifecycle | `create`, `read`, `update`, `delete`, `archive`, `restore` |
| Access and sharing | `export`, `download`, `share`, `assign`, `grant`, `revoke` |
| Decisions | `approve`, `reject`, `override` |
| Operations | `execute`, `cancel`, `retry` |
| Configuration | `configure`, `enable`, `disable` |

Choose `update` rather than sometimes using `edit`, for example. The list is a
shared baseline, not a prison: a genuinely distinct product verb may be added
through a reviewed taxonomy change rather than invented ad hoc in one feature.

Do not put outcome into the event type. Prefer `billing.invoice.export` with
outcome `denied`, rather than a distinct type such as
`billing.invoice.export.denied`. That keeps all exports groupable while still
making the outcome queryable. An asynchronous lifecycle—where a request is
accepted now and a worker completes later—needs a future explicit lifecycle
design; it should not overload the current three outcome values with vague
states such as `pending`.

This was initially a **proposal**. Lesson 75 later locked the main
provider-neutral operational vocabulary in
`platform/contracts/src/observability.ts`, including controlled actions,
interaction sources, execution contexts, operational outcomes, job-delivery
dispositions, capability names, and canonical emitted field names. The existing
Core audit event and outcome contracts remain deliberately unchanged: adopting
this vocabulary as a versioned Core audit taxonomy, and requiring every future
capability profile to use it, is still later governed work.

### Study question

Why should a bulk export target the export job or file rather than every invoice
inside it?

It identifies one controlled, reviewable operation and lets authorised systems
resolve its contents under current access checks. Listing every invoice would
turn audit into a duplicate sensitive-data store.

## 37. Following One Piece of Work: Correlation and Causation

When a request stays inside one server function, it is easy to see what
happened. Real systems are harder: one request may create an event, enqueue a
job, run later in a worker, write an audit record, and emit several operational
records. We need two small labels to make that chain understandable without
copying all of the request data everywhere.

### The two questions are different

| Identifier | Answers | Mental picture |
|---|---|---|
| Correlation ID | “Which larger piece of work does this record belong to?” | A case-folder number written on every relevant document. |
| Causation ID | “Which immediately earlier fact or message directly caused this record?” | A “replying to document X” note. |

Correlation groups siblings as well as descendants. Causation draws a direct
parent-to-child line. They are useful together because a single case can branch
into several direct causes.

### Bill's export, step by step

Imagine Bill asks the web application to export invoices for the Benelux scope.
The system gives the whole logical operation correlation ID `C-901`.

```text
Bill's web request                         correlation: C-901
        |
        +-- export-requested event E-10    correlation: C-901
        |                                  causation: request / accepted action
        |
        +-- queue message M-41             correlation: C-901
        |                                  causation: E-10
        |
        +-- worker creates export file F-7 correlation: C-901
        |                                  causation: M-41
        |
        +-- export-completed event E-11    correlation: C-901
                                           causation: M-41
```

The precise identifiers above are illustrations, not current record values.
The important pattern is this:

- Searching for `C-901` finds the whole export story: request, event, message,
  worker activity, security signal, audit event, log, metric, and result.
- Looking at the causation of the completion event tells us the immediate reason
  it exists: the worker handled message `M-41`, not simply that Bill once made
  a request.

This answers two different investigations. “Why did this worker event happen?”
uses causation. “Show me everything that happened during Bill's one export”
uses correlation.

### A misconception to avoid

> “The invoice ID is enough to connect the records.”

No. Bill can request two exports of the same invoice at different times. They
share a target, but they are two separate pieces of work and need different
correlation IDs. Conversely, one export can affect many invoices but still have
one correlation ID. Resource identity, tenant identity, and correlation are
three different facts.

### What happens on retry?

Suppose the worker's first attempt to create `F-7` times out and the queue
re-delivers `M-41`.

The logical export is still `C-901`; retrying must not make it disappear into a
new unrelated story. The message remains the work item's stable identity, while
the delivery attempt and its error are their own bounded operational facts.

Yes: when the retry is scheduled **because attempt A-1 failed**, the retry
record should causally link to that failure. If the system creates a
`retry-scheduled` fact R-2, its causation is A-1; the later attempt A-2 is then
caused by R-2. That makes the explanation inspectable: “A-2 happened because
the system scheduled a retry after A-1 timed out.”

```text
queue message M-41     correlation: C-901
        |
attempt A-1 fails      correlation: C-901    caused by: M-41
        |
retry R-2 scheduled    correlation: C-901    caused by: A-1
        |
attempt A-2 runs       correlation: C-901    caused by: R-2
```

One causation field normally names one immediate parent. Do not make it carry
both “M-41 and A-1” as an improvised string. The message identifier explains
which work item is being delivered; the causal chain explains why this
particular retry occurred. Idempotency then answers a third question: “Have we
already safely applied this effect?” It is related to tracing, but it is not an
identifier replacement.

### What the repository has today

Core deliberately gives `CorrelationId` and `CausationId` different types.
Core event envelopes and queue messages can carry both. Audit events currently
carry a correlation ID, while the runtime context declares an optional
causation ID. The current worker passes a queue message's correlation ID to its
job context, but does not yet pass its causation ID through.

So do not read the presence of these names as proof that every current path is
fully traceable. The planned record-pipeline slice now makes propagation and
tests an explicit future obligation. It will need a governed design for the
cross-record reference used as a causation ID, especially if audit events also
need direct-parent links.

### Safety boundary

These IDs are tracing facts, not authority. A client-provided request ID must
be bounded and treated as untrusted at the system boundary; it cannot grant
Bill access to Benelux invoices, select his tenant, or prove who he is. The
system must also avoid putting customer names, tokens, prompts, invoice rows,
or file contents into an identifier merely to make it “more useful.”

### Study question

If one scheduled run creates reports for 300 tenants, should all 300 reports
share one correlation ID?

Usually the scheduled-run trigger is one parent fact, but each tenant report
is its own tenant-bounded unit of work. A later design might correlate all of
them to a safe parent run while giving each tenant report its own correlation
for access, troubleshooting, and retention boundaries. The answer depends on
the use case; it should never accidentally join tenant data just because it was
scheduled at the same time.

## 38. One Job, Three Reliability Ideas: Retry, Attempt, and Idempotency

These three ideas work together, but they solve different problems. Mixing them
up creates either lost work or duplicate work.

| Idea | The question it answers | Bill's export example |
|---|---|---|
| Delivery attempt | “Which physical try at handling this message is this?” | The worker is handling message M-41 for the first time, then perhaps a second time. |
| Retry | “Should the system try this failed work again?” | The file provider timed out, so a bounded policy schedules another attempt after a delay. |
| Idempotency | “If this logical effect has already happened, can a repeat safely do nothing?” | If export job E-42 already created its one authorised file, another delivery must not create a second file. |

### The normal, awkward situation

Message delivery is usually **at least once**, rather than exactly once. A
worker or network can fail at an unfortunate moment: the provider may have
created the export file, but the worker loses the response before it can record
success. From the worker's view, the first attempt looks like a failure, so a
retry is sensible. From the provider's view, the effect may already exist.

```text
message M-41, correlation C-901, idempotency key K-export-E-42
        |
attempt 1: create file F-7 at provider
        |
provider succeeds, but the response is lost
        |
worker schedules retry; attempt 2 receives M-41 again
        |
idempotency decision: create another file, or recognise the prior effect?
```

Retry protects against lost work. Idempotency protects against duplicate
effects. Neither replaces the other.

### What each record keeps stable

| Fact | Changes on retry? | Why |
|---|---|---|
| Message ID | No | It identifies the same queued work item. |
| Correlation ID | No | It keeps every attempt in Bill's one export story. |
| Delivery attempt | Yes: 1, then 2, then 3 | It shows how many times the worker was asked to handle the message. |
| Retry decision | One per failed attempt that policy permits retrying | It records the choice to try again and its backoff delay. |
| Idempotency key | No | It identifies the one intended business effect, such as this tenant's export job E-42. |

The idempotency key is normally a stable, scoped business reference—not a raw
request body, token, customer name, or a random delivery-attempt number. It
must include tenant or product scope when that scope matters. Using only a
message ID can deduplicate re-delivery of that exact message, but may fail to
recognise that two independently created messages request the same logical
export.

### What the current worker shell does

The current in-memory worker starts with attempt 1. On handler failure, it
requeues the same message as the next attempt and calculates a backoff value.
It can ask an idempotency store whether a key was already processed. If the key
is present, it skips the handler; if the handler succeeds, it records the key.

That is a valuable local test baseline, but it does **not** prove exactly-once
processing. The handler can make an external change and then the process can
fail before the worker records the key. A durable production design must choose
how to reconcile that gap—for example, by making the downstream create
operation itself idempotent for the same key, or by using a deliberate durable
claim/transaction design. The right answer depends on the provider and product
effect; the generic worker must not pretend it has solved it automatically.

The in-memory queue also records a retry delay for test inspection; it is not a
real delayed-delivery service or a production queue provider.

### A misconception to avoid

> “If we have idempotency, we never need retries.”

Idempotency only makes repeating an effect safe. It does not make a temporary
provider outage succeed. Retry supplies another opportunity; idempotency makes
that opportunity non-destructive.

### Planning result

The platform-runtime plan now requires each repeatable external job to define
its key and scope, durable record/claim, concurrent-worker behaviour,
expiry/reconciliation policy, and atomic boundary with the external effect.
This was a plan change, not merely a teaching observation.

### Study question

Why might an export-job ID be a stronger idempotency key than the queue-message
ID?

The export-job ID represents the intended business effect. If a caller or
provider accidentally creates a second queue message for the same export job,
both messages can still resolve to one safe result. A message ID only recognises
duplicates of the exact delivery item.

## 39. Platform Contracts Refresher: The App-to-Platform Socket

`platform/contracts` is the stable agreement between an application and the
generic runtime platform. Think of it as the shape of an electrical socket:
the app says which approved things it is contributing, and the platform knows
how to connect and run them. Neither side needs to know the other's internal
wiring.

| Layer | Main responsibility | Example |
|---|---|---|
| Core | Portable business and technical nouns. | `TenantId`, `Principal`, `CorrelationId`, `QueueMessage`, `Result`. |
| Platform contracts | The app-facing shape for participating in this particular runtime. | Route registration, job registration, mounted app, request/job context, health registration. |
| Platform runtime, server, and worker | The mechanics that use those registrations. | Match a route, create its context, invoke a handler, poll or deliver a job. |
| App | Product meaning and implementation. | “Export Benelux invoices,” its validation, and its business rules. |

The distinction matters. Core should not know that this particular platform has
HTTP routes or worker mounts; that would make portable Core vocabulary depend on
one runtime design. Conversely, an app should not receive a raw Node server,
queue loop, or AWS client merely to register a route or job. It contributes a
small declaration through `platform/contracts`; the platform owns the machinery
around it.

For example, an app can declare, “I provide this route; it requires this stable
permission and tenant context; this handler will process an approved request
context.” The server then performs the generic work—matching, authentication,
authorisation, context creation, validation, error mapping, and logging—before
the app handler runs. The same idea applies to jobs: the app declares the job;
the worker owns delivery, retries, shutdown, and observability mechanics.

### Why we are looking at it now

The public contracts are currently collected in a large source entry point. We
want to split that source into understandable topic files while keeping the
single public package import stable. Before moving anything, we need to know
which contracts naturally belong together and which must not depend on each
other.

Otherwise, it is easy to organise by visual convenience—putting everything
used by a server together, for example—and accidentally make app-facing
contracts depend on server implementation details. That would defeat the
boundary we are trying to preserve.

So our next step is not implementation yet. It is a map-reading exercise: name
the natural contract topics, their responsibilities, and their allowed
dependencies. Once that map is clear, the file split becomes mechanical rather
than risky.

### Planning triage

No plan change is needed for this refresher. It confirms the already-recorded
platform-runtime direction: apps integrate through public mount and contract
surfaces while generic runtime modules do not import app internals. The next
topic-grouping decision may change the existing restructure plan, so it will be
triaged when we reach it.

### Study question

Why should an app register a route through a platform contract rather than
being handed the raw web-server object?

The contract limits the app to an approved, portable contribution. The platform
can then apply consistent security, lifecycle, health, logging, and testing
behaviour around every app route without exposing server-specific internals.

## 40. Capability Declarations: The Information Beyond Runtime Registration

Yes. An app needs more than its route, job, health, configuration, and
lifecycle registrations when it describes a real product capability. Those
runtime registrations explain **how** the platform can run something. A future
capability declaration explains **what it means**, which rules apply, and which
safe supporting information is available to people, harnesses, and bounded LLM
experiences.

| Capability concern | A future declaration should provide | It should not provide |
|---|---|---|
| Purpose | Stable ID, owner, version, and a concise description of the intended outcome. | An unrestricted product specification or a prompt that grants authority. |
| Interfaces | References to input/output schemas, errors, routes, jobs, events, and approved web/chat/voice adapters. | A second copy of handlers or business logic. |
| Policies | References to permission, tenant/resource scope, approval, confirmation, and delegation requirements. | Live group membership, raw tenant policy data, or a policy engine. |
| Information handling | Data classification plus approved persistence, integration, retention, and residency requirements. | Credentials, provider configuration, or cloud resources. |
| Records | Separate allowlisted audit, security-signal, and operational-observability profiles. | One large free-form log/audit payload containing sensitive data. |
| LLM/agent discovery | A bounded user-facing purpose, supported input/output form, and approved invocation path. | Tool authority, direct database/provider access, hidden instructions, or trust in model output. |

The important placement decision is that this does **not** make
`platform/contracts` a giant catalogue of every product idea. Platform
contracts stay narrow: “this route exists and has these runtime requirements.”
The capability declaration belongs to the future app/product-harness boundary:
“this invoice export capability exists, uses those route/job registrations, has
these safe record profiles, and must follow these policies.” A validator can
later check that the references line up.

### LLM descriptions need a particularly careful boundary

A description can help an LLM present a capability to a user: “Export a
permitted invoice set to an authorised file.” It is **discovery metadata**, not
permission. The real execution path still verifies identity, tenant, group and
scope rules, validates the request, requires confirmation where needed, and
authorises every side effect. A model must never infer that a description means
“you may now read every invoice” or “you may call this provider directly.”

### Planning result

This identified a real missing planning item. The product-harness plan now has
a deferred, versioned capability-declaration profile: it will use references
and allowlists, keep LLM fields non-authoritative, and wait for a real first
consumer before choosing its exact file format or repository location.

### Study question

Why should the invoice-export capability reference its approved audit profile
rather than embed a free-form `metadata` section?

The reference lets one profile allowlist and validate only the safe facts needed
for export accountability. A free-form field invites each capability to leak
different sensitive details into a durable store.

## 41. Record Profiles: What Each Capability May Send Where

We had already separated three record destinations, but the capability
declaration needs to point to a more precise rule: not just “this capability
has audit logging,” but “these exact safe facts may go to this kind of record.”

| Record profile | Its purpose | Typical safe facts for invoice export | Facts that do not belong there by default |
|---|---|---|---|
| Audit profile | Durable accountability: who did what, to which bounded target, under which tenant/context, and with what outcome. | Capability/action ID, actor type and stable reference, tenant ID, export-job ID, outcome, time, correlation ID, approved reason code. | Invoice rows, balances, customer names, request body, download URL, access token. |
| Security-signal profile | Detect or investigate a security-relevant control outcome. | Authentication/permission/rate-limit result, route/capability ID, safe source classification, outcome, correlation ID. | Raw authorisation header, session cookie, JWT, password, or broad request payload. |
| Operational-observability profile | Diagnose availability, performance, and reliability. | Capability ID, status class, latency bucket, retry attempt, error class, queue/job name, deployment version, correlation ID when useful. | Full audit event, per-customer metric labels, raw provider response, stack trace containing customer data. |

The word **profile** is doing important work. It is a small allowlist with a
purpose—not an instruction to send every available value to every destination.
For each permitted field, the future profile must say:

- why the field is needed for this record type;
- its data classification and whether it is an ID, a bounded category, a count,
  or another safe form;
- permitted values and maximum length/cardinality;
- who may read it and how long/where it may be retained; and
- whether it is required, optional, aggregated, redacted, or excluded.

This gives us a reliable decision process. “Could this be useful later?” is not
enough reason to store it. A fact has to earn its place in one named profile.

### A small but important difference

The **capability declaration** does not repeat every field rule. It references
the selected audit, security-signal, and operational profiles. The platform
record pipeline later validates and writes them; the product harness later
checks that a feature has made a deliberate selection. This keeps policy
consistent without turning every feature into a miniature logging framework.

### Planning result

The platform plan already required field-level allowlists for the future record
pipeline. We added the corresponding product-harness requirement: each
capability profile must reference record profiles that include field purpose,
classification, permitted values, bounds, audience, and retention/residency
justification.

### Study question

Why is `customerId` usually safer as a bounded audit target reference than as a
metric label?

An audit investigation may need a controlled resource reference. A metric label
creates a separate high-cardinality time series for every customer, which is
expensive, hard to query, and risks spreading customer-linked data through an
operational store.

## 42. Platform Contract Topic Map: Preparing a Safe File Split

We inspected the actual `platform/contracts` entry point. It is about 565 lines
because it currently holds several different responsibilities in one file. The
goal is not to make more folders for their own sake. The goal is to make each
responsibility visible while preserving the one public package import that apps
already use.

| Proposed topic file | Plain-English role |
|---|---|
| `errors.ts` | The standard ways a contract declaration can be invalid. |
| `identifiers.ts` | The checked names for apps, routes, jobs, health checks, and API versions. |
| `flags.ts` | Feature-flag names, context, readers, and a fixed test reader. |
| `contexts.ts` | The safe bundle of request/job facts passed to an app handler. |
| `routes.ts` | What an HTTP route is allowed to declare: request, response, handler, auth, tenant, and resource checks. |
| `jobs.ts` | What a background job is allowed to declare: message type, payload validator, and handler. |
| `app.ts` | How an app mounts its registrations: permissions, health, config, lifecycle, and dependencies. |
| `validation.ts` | The cross-field checks that decide whether a declaration is valid. |
| `index.ts` | A deliberate public front door that re-exports the approved contracts. |

The dependency direction matters more than the filenames:

```text
errors and identifiers
        ↓
flags and contexts
        ↓
route, job, and app declarations
        ↓
cross-declaration validation
        ↓
one public index barrel
```

For example, a route declaration can depend on a request context and a route
name. It should not import a validator that examines every other route in the
registry. Validation is the later “inspector” layer; it reads the declarations
rather than becoming part of each declaration.

### Misconception to avoid

> “After the split, consumers should import from the topic file that sounds
> most convenient.”

Not in this first refactor. Apps and other packages keep importing from the
single public package entry point. Topic files make internal maintenance easier;
the barrel protects callers from the internal file layout changing again.

### Implementation result

The split is now implemented. `platform/contracts/src/index.ts` is a small,
deliberate public barrel, while the listed topic files hold their individual
responsibilities. The public import is still exactly
`@kanbien/platform-contracts`; no consumer needs to know or use a topic-file
path.

The package README now provides the file map at the point of use. The owning
platform-runtime plan records the completed source-organisation slice. Type
checking, declaration build, runtime tests, and the import-boundary test all
passed after the move.

### Misconception to avoid

> “A small barrel means the package has fewer capabilities.”

No. It means the public doorway is intentionally small. The same route, job,
app-mount, validation, error, context, and flag contracts are still available
to callers; their implementation is simply easier for maintainers to find.

### Study question

Why do we keep `validation.ts` behind the barrel rather than make apps import
it from a file path?

Because the validator is still a supported package capability, but its file
location is an internal organisation choice. The barrel lets us reorganise the
inside again without making every app change an import.

### What this map deliberately does not contain

The file map covers the contracts that exist **today**. It is not a claim that
all of our future architecture has been squeezed into `platform/contracts`.
That would make the package confusing and give the generic runtime ownership of
product and deployment decisions it should never make.

| Discussion topic | Where it belongs instead |
|---|---|
| Audit events, authorization vocabulary, queues/events, correlation, causation | Core contracts. |
| Security decisions, redaction helpers, future security/audit/operational writers | Platform security, observability, and the deferred record-pipeline slice. |
| Capability purpose, policy references, LLM discovery text, data and record-profile choices | Future app/product-harness capability declaration. |
| Tenant groups, roles, memberships, and resource policies | App/product policy and authorization boundary. |
| Encryption provider/keys, actual residence, retention stores, and SIEM/log vendor | Deployment target, adapters, and infrastructure. |

Some current platform contracts do expose **hooks into** those worlds. For
example, a route can say it needs authenticated access, a tenant, or resource
authorization, and mount dependencies may receive an audit recorder. That is a
socket for an approved mechanism—not the full policy, durable store, or
provider implementation itself.

### Study question

Why should `validation.ts` consume route/job/app declarations instead of route
declarations importing registry validation?

A route can validate its own shape, but only the later validation layer can see
the complete registry and detect relationships such as duplicate names or a
route permission that was never declared.

## 43. Startup Registries and Zero-Downtime Changes

The future runtime registry is created during the startup of **each** server or
worker process. It mounts the apps for that one process, validates their
declarations, and allows the process to become ready only when the complete
registry is valid. It is not a central object that is edited while a live
service handles requests.

That means an invalid new registration normally has this shape:

```text
old service instances: healthy and serving traffic
new service instance: starts, builds registry, finds an invalid declaration
new service instance: fails readiness and receives no traffic
deployment: retains or rolls back to healthy old capacity
```

The registry protects process integrity. It does **not** itself provide zero
downtime. The deploy target's rolling, blue/green, or equivalent strategy owns
traffic cutover, capacity, health checks, and rollback.

### Why a migration still matters

Old and new process versions can coexist during a normal deployment. A route
name, permission, job message type, or target authorization mapping may cross
that version boundary. The safe general sequence is:

1. Add acceptance for both old and new forms where they must coexist.
2. Deploy consumers that understand both forms.
3. Start producing or granting the new form.
4. Migrate callers, queue producers, and deployment target mappings.
5. Use evidence to confirm the old form is no longer used.
6. Remove old-form acceptance in a later, deliberate release.

For example, a worker must understand both an old and new queue message before
any producer sends only the new message. Likewise, a permission rename may need
temporary target authorization mapping for both the legacy and replacement
permission while old and new application instances overlap.

### Misconception to avoid

> “If the registry validates at startup, changing the rule has no live-service
> impact.”

It has no in-place mutation of an already running process. But it can still
block **new** instances, and it can still break cross-version callers if the
new version stops recognising a value that old instances, tokens, or messages
are still using. Compatibility planning is what protects that overlap.

### Planning result

The platform-runtime plan now requires per-process startup validation, makes a
failed registry block readiness rather than mutate a live service, places
traffic retention and rollback in deployment/infra, and records the explicit
add–consume-both–produce-new–retire-old migration sequence.

### Current repository implementation

The repository now scopes every real runtime mount and every reusable test
mount to the already-validated app ID. The runtime creates
`registry.forApp(appId)` and passes that narrowed registry to the app's
`mount` function. The app therefore cannot nominate a different owner while it
registers a permission, route, job, or health check.

The rule is deliberately simple: the name must start with `<app-id>.`.
For example, the app `smoke` can register `smoke.echo`,
`smoke.rebuild`, `smoke.readiness`, and `smoke.smoke:read`; an attempt to
register `billing.invoice.list` or `billing.invoice:read` fails with the stable
`PLATFORM_CONTRACT_NAMESPACE_MISMATCH` error. The complete shared registry
still prevents cross-app collisions, so two correctly named routes may not
silently claim the same HTTP method and path.

The production runtime tests prove accepted own-namespace declarations,
rejected foreign permission/route/job/health declarations, and preserved
cross-app duplicate detection. The test-helper tests use the same scoped-mount
path, so an app's fast contract test is not looser than production startup.
Feature flags are still readers rather than app registrations, and are not part
of this particular namespace rule.

### Study question

Why should a queue consumer be deployed before producers start sending a new
message type?

Because a producer can send work to any healthy worker version. If an old
worker does not recognise the new message, it may reject, retry, or dead-letter
perfectly valid work.

### Worked permission migration: `smoke:read`

The smoke app has app ID `platform-smoke`. It previously declared
`smoke:read`; this implementation migrated it directly to the app-owned form
`platform-smoke.smoke:read`. This is not a change to Core's portable
`resource:action` permission type: the resource part can contain a dot. It is
an app-aware registry rule applied while the `platform-smoke` app is mounting.

What must change is every place that uses the exact permission value:

| Concern | Former example | Implemented result |
| --- | --- | --- |
| App declaration | `platformSmokeReadPermission = "smoke:read"` | `platformSmokeReadPermission = "platform-smoke.smoke:read"`. |
| Route requirement and manifest | The route and manifest used the old constant. | They use the replacement constant, so their values cannot drift apart. |
| Test authentication hooks and fixtures | Tests granted the old value. | The smoke, runtime, testing, server, and Cognito-adapter fixtures use the app-owned form appropriate to each fixture app ID. |
| Provider claim/group mapping | No deployed platform-smoke mapping exists in this repository. | A future live mapping must grant the replacement through the governed compatibility sequence. |
| Future policy, role, UI, audit, or client configuration | No durable product instance exists in this repository yet. | Inventory and migrate each real-world grant, policy reference, cache, token, and documentation reference before retiring a legacy value. |

There is a subtle current behavior: a route's `permissions` array is an
**all-required** list, not an either/or list. Giving a route both `smoke:read`
and `platform-smoke.smoke:read` would require the caller to have both. It does
not create a compatibility alias.

For this repository there is no deployed authorization mapping, persisted
grant data, or coexistence of old and new platform-smoke processes. A direct
replacement is therefore the honest compatibility decision: there is no legacy
alias. In a real live service, one possible overlap strategy is to grant both
old and new permission values to the same eligible identities while old and new
versions coexist; old routes require the old value, new routes require the new
one. Once old instances, token/session lifetimes, and external references are
gone, a later release deliberately removes the legacy grant. A first-class
permission alias mechanism is another possible design, but it does not exist
today and must not be assumed accidentally.

### Planning disposition

The platform-runtime plan now records this implemented scope and direct local
migration decision, while retaining the explicit cross-version sequence for a
future live migration. That distinction matters: a clean repository literal
replacement is not evidence that a customer-facing permission rename can skip
compatibility analysis.

## 44. Public Navigation: A Product Address, Not a Source Folder

Public URLs are part of the product's information architecture. A customer may
bookmark, share, dictate, support, or automate against an address long after
the implementation behind it has changed. That makes a public browser address
a durable product interface.

The same business capability has three related but different forms:

| Form | Question it answers | Invoice export example |
|---|---|---|
| Public navigation address | “Where is the user in the product?” | `/finance/invoices/INV-123/export` |
| Backend API route | “Which HTTP request asks the system to do or return something?” | `POST /api/v1/invoices/INV-123/export` |
| Shared capability | “What product meaning, validation, authority, and consequence controls apply?” | `invoice.export` |

The first may display an export-review page. The second asks for the export.
The third is the shared product boundary that web, chat, voice, workers, and
CLI consumers should reach through their own approved adapters.

### Product classification is valid public language

Names such as `finance`, `support`, `invoices`, and
`customer-queries` may be useful path segments when they are stable,
outward-facing product classifications. They are not implementation leaks
merely because an app or module happens to implement them.

The question is whether the name survives an implementation rewrite:

```text
stable public product language
  finance → invoices → INV-123

replaceable implementation
  one app today → several apps later → another UI technology later
```

Avoid a path label only when it reports a transient technical choice, such as
a source folder, component, provider, internal service, or temporary project
name. A product area is appropriate when users, support staff, and product
owners would still use the term after those technical details change.

### The recommended baseline

- The host/origin carries deployment addressing. Production, staging, preview,
  DNS, TLS, and custom-domain resources remain deployment decisions.
- The path carries stable product navigation: product area, resource, resource
  identity, view, or a user-visible workflow step.
- Query fields are limited to safe, bounded view state such as page, sort, or
  selected tab; they are not a place for credentials, personal data, authority,
  or destructive commands.
- A URL is not authorization evidence. The server still verifies identity,
  resolves trusted tenant context, and enforces permission and resource policy.
- A safe browser read must not produce a consequential side effect. An
  action-looking browser address can present a confirmation view, while the
  protected API/capability path performs the action only after confirmation.

Tenant custom domains, subdomains, and path prefixes are all possible later
models. None of them proves access to a tenant; each requires trusted
resolution and the ordinary authorization path.

### Planning result

The product-harness foundation plan now records a deferred public-navigation
and addressing direction. When the first real web consumer is chosen, it must
define a versioned navigation declaration, product-level namespace ownership
and collision checks, safe addressing rules, bookmarked-address compatibility
or redirects, tenant-addressing policy, and proof that navigation cannot bypass
the shared capability controls. No frontend router, public URL package, or
specific hostname grammar has been implemented.

### Misconception to avoid

> “If the URL names the product area, it must be coupled to one app module.”

No. The product owns the durable public namespace. An app contributes an
approved view/capability mapping inside it. The implementation may move behind
that address while the public product language remains stable.

### Study question

Why may `/finance/invoices/INV-123/export` be a suitable browser address
without allowing a `GET` request to export the invoice?

Because the address can identify an export-review view. The separate protected
action request, after the required confirmation and authorization checks,
creates the export.

## 45. Server Pipeline, Part 1: Establishing a Safe Request Envelope

The platform server has two timescales. At startup it mounts apps, validates
configuration, prepares routes, and creates lifecycle control. For every
individual request, it creates a small safe envelope before considering the
caller’s identity or an app handler.

Incoming HTTP requests first gain a request identity and outcome trail, then
pass browser-origin and response-safety rules, rate-limit capacity protection,
and health or route selection. Only after those steps does the server consider
authentication and authorization.

The current server records these early pipeline stages as request ID, request
logging, CORS, security headers, rate limiting, and parsing. Its in-memory
handle entry receives an already normalised platform request for tests; the
real Node listener first adapts raw HTTP into that request shape.

### One request ID, one outcome trail

At the beginning, the server accepts or creates a request ID and uses it as
the correlation ID for its final request record. Its finish step records only
safe operational facts: route, method, status, latency, and a bounded error
class when there was an error. It does not make a raw request body, bearer
token, cookie, or customer data part of the ordinary request record.

This lets an operator answer “what happened to this request?” without turning
operational logs into a second database of sensitive inputs.

### CORS and security headers come before identity

CORS answers a browser-specific question: “may a page from this origin read
this response?” The current server allows an origin only when it is in the
configured allowlist. It is not authentication—an allowed browser origin does
not make the human using that browser trusted.

Security headers are added to the response envelope before later success or
error outcomes. This makes a denied or failed response receive the same
browser-safety baseline as a successful response.

### Rate limiting comes before authentication

The current rate limit is checked before body parsing, health handling, route
matching, and authentication. This is deliberate: a flood of anonymous or
malformed requests should consume as little downstream work as possible. The
generic listener derives its early key from the actual socket peer address, not
from caller-supplied forwarded-address headers; after authentication it can
also apply a verified principal-specific key.

If the limit is exceeded, the server returns a safe 429 response, records the
bounded rate-limit outcome, and does not run an app handler.

### Health endpoints are a small early branch

After the rate-limit check, /livez and /readyz are handled before ordinary
route matching. They can be public or require authentication according to
their exposure policy. Liveness answers whether the process is alive;
readiness also considers lifecycle state and registered health checks.

### Misconception to avoid

> “The request logger must log the whole request so we can debug it later.”

No. A useful operational record explains the outcome with correlation ID,
route, method, status, latency, and bounded failure class. Raw request content
belongs only in a deliberately authorised diagnostic path, if one is needed at
all.

### Study question

Why does the server rate-limit before authentication, even though an
authenticated principal could provide a more precise key?

Because authentication itself costs work and may depend on remote identity
infrastructure. An early anonymous request limit protects capacity before an
attacker can force the later pipeline to run.

## 46. Server Pipeline, Part 2: Route, Identity, Permission, and Tenant

After the early request envelope, the server finds a route by HTTP method and
path. A match means only “this declaration describes the request.” It does not
mean the caller may use the route.

A matched protected route follows this sequence: authenticate the caller, check
the route's declared broad permission, resolve trusted tenant context when
required, construct the app request context, and only then continue to
validation, resource authorization, and handler invocation.

### Route matching is not access

The server compiles the mounted route patterns and extracts path parameters.
An unknown route returns a safe not-found response without invoking an app
handler. A public route also does not authenticate an optional credential just
because the caller sent one; its handler receives no principal. This prevents
an accidental optional-identity behaviour from becoming part of the public
route contract.

### Authentication answers “who is this caller?”

For an authenticated route, the server calls the configured authentication
hook. That hook belongs at the platform security/provider boundary: it may
verify a bearer token and translate verified claims into a provider-neutral
principal and granted permissions.

If there is no authentication hook, the server denies by default. If the hook
reports an unauthenticated caller, the server returns 401 and the route handler
does not run. A missing/invalid identity is different from an identity that is
known but not permitted.

### Permission authorization answers “may this identity attempt this kind of action?”

The route declares its required permission. The server compares that
declaration with the authenticated result before tenant or resource work. A
missing permission produces 403, and the current tests prove that neither the
tenant resolver, the resource resolver, nor the handler run afterward.

This is the broad capability gate. It answers, for example, whether Bill may
attempt to read invoices at all. It does not yet decide whether this particular
invoice is in Bill's authorised regional scope.

### Tenant resolution supplies a trusted scope

If a route requires a tenant, the server asks the configured tenant resolver
to derive tenant context from the matched route, prepared request, and verified
principal. It accepts only a complete tenant context with a tenant ID and
isolation key. A missing or malformed result is denied with 403 before the
handler runs.

The server checks configuration earlier too: if any mounted route requires a
tenant but no resolver was supplied, the server shell fails during startup
rather than listening with an accidental tenant bypass.

For Bill, the sequence is: his verified identity has the broad invoice-read
permission; the resolver establishes trusted Benelux tenant context; the
handler receives both principal and tenant facts; then later resource policy
decides access to the particular invoice.

Group, role, and regional membership policy are not hardcoded into the server.
They may help the provider map claims to permissions or help the app/product
authorizer decide a later resource request. The server enforces their results
at the correct point in the request pipeline.

### Planning disposition

No plan change is required. This lesson explains the already implemented
provider-neutral server sequence and its startup guard; it does not introduce a
new tenancy model, role/group policy engine, or route contract.

### Study question

Why does the server check broad permission before asking the tenant or resource
resolver for facts about a particular invoice?

Because a caller who cannot attempt invoice access should not cause policy work
or receive information that a tenant/resource resolver might reveal. The early
permission gate is both cheaper and a smaller information-disclosure surface.

## 47. Server Pipeline, Part 3: Validation, Resource Policy, Handler, and Response

The later request stages answer different questions in a deliberate order:

| Stage | Question | Failed outcome |
| --- | --- | --- |
| Request validation | “Is the supplied request shaped correctly?” | Safe 400 |
| Resource resolution | “Can we identify the target and its policy facts?” | Safe 403 or 404, by disclosure policy |
| Resource authorization | “May this verified principal perform this permission on this resource in this tenant?” | Safe 403 |
| Handler | “Perform the permitted product behaviour.” | Its declared response or safe 500 |

### Validation comes before resource work

Once the server has constructed the request context, it calls the route's
declared validator. The validator checks the request body shape, not whether a
caller deserves access. A malformed export request is a client-input problem,
so it receives 400 and never reaches resource resolution or the app handler.

This is different from business validation inside a handler. Route validation
asks whether the input can safely cross the boundary; the handler may still
reject a well-shaped request because the requested export options conflict with
product rules.

### Resource resolution identifies facts; it does not grant access

For a route that declares resource authorization, its resolver receives the
prepared request and trusted request context. It may return a resource
reference plus relationship, attribute, or other bounded policy facts.

The platform then asks the configured authorizer to decide using the verified
principal, declared permission, tenant ID where present, resource reference,
and those facts. The resolver finds and classifies the target; the authorizer
decides whether the action is allowed. Neither responsibility should silently
replace the other.

For Bill's invoice export, the resolver might identify invoice INV-123 and its
customer/region facts. The authorizer then decides whether Bill's verified
principal, Benelux tenant scope, and accountant policy permit export of that
invoice.

### Not found and hidden are deliberately different

A resolver can say that a target is genuinely absent and permit a 404 response.
It can instead say that existence must not be disclosed; the server then
returns 403. A malformed resolver result also fails closed with 403.

This makes resource disclosure an explicit product policy. It is not an
accidental side effect of a database lookup.

### The handler is now allowed to run

Only after all prior checks pass does the server invoke the app-owned handler.
The handler receives the prepared request and its runtime context, including
the verified principal and tenant context when applicable. It returns an HTTP
status, body, and optional response headers; the server preserves its safety
headers and adds only the handler's permitted response headers.

If the handler throws unexpectedly, the server returns a generic 500 response.
The detailed thrown error is classified for the bounded operational record,
not returned to the caller as an implementation leak.

Every ending—400, 403, 404, 500, or success—passes through the same finish
step. It records route, method, status, latency, correlation ID, and bounded
error class, then emits the response.

### Misconception to avoid

> “Resource authorization is just another permission check.”

No. Broad permission answers whether Bill may attempt invoice export at all.
Resource authorization answers whether Bill may export this invoice, for this
tenant, with these policy facts. It is the difference between a building pass
and permission to enter one particular locked room.

### Planning disposition

No plan change is required. The lesson explains the existing route declaration,
resource-resolution, authorizer, and error-response seams. A general live
product policy engine and durable audit/record pipeline remain explicitly
future work.

### Study question

Why is the resource resolver allowed to choose between 404 and 403 for a
missing-looking target?

Because resource existence can itself be sensitive. The product decides
whether telling a caller that a target exists would reveal information beyond
their authority.

## 48. Server Pipeline, Part 4: The HTTP Transport Gate

The earlier lessons began with a prepared platform request. A real server has
an earlier, more defensive stage: **the transport gate**. It handles bytes and
connections from the network before the request is safe enough for the normal
route, identity, and authorization pipeline.

Think of the system as two entrances:

```text
network bytes and sockets
        ↓
transport gate: bounded, recognised, cancellable HTTP request
        ↓
platform request pipeline: route, identity, permission, tenant, policy, handler
```

The distinction matters because a malicious or simply broken request may never
be suitable for the usual request pipeline. For example, the server should not
read a 10 GB body, parse invalid JSON, or invoke a remote identity provider
before it can say that the request is too large or under rate limit pressure.

### The transport gate, one small decision at a time

| Transport decision | What it prevents | Why it happens here |
| --- | --- | --- |
| Create or validate a request ID | An app can neither invent nor replace the common correlation identity. | This is the first shared fact about a request. |
| Recognise the HTTP method | `TRACE`, a typo, or an unexpected method cannot become `GET` by accident. | The route matcher must receive an intentional method. |
| Rate-limit admission | A denied caller cannot spend body-parser, authentication, or handler capacity. | This is the cheapest useful capacity decision. |
| Enforce header/body limits | A single client cannot make the process retain unbounded bytes. | The data is still raw network input. |
| Require JSON before parsing a non-empty mutation body | An XML, form, or ambiguous payload does not quietly reach a JSON route. | The transport owns media-type interpretation. |
| Map malformed input safely | Invalid JSON becomes a bounded 400 rather than a framework stack trace. | The app has not run and cannot safely explain it. |
| Apply time and concurrency limits | Slow connections and stuck handlers cannot consume all process capacity forever. | Socket/request lifetime is a host concern. |
| Create cancellation and drain gracefully | A handler can stop work when the caller disappears or the process is stopping. | The transport sees connection closure and listener shutdown. |

The current `platform/server` listener proves these cases through a real local
TCP listener, not only by passing convenient objects directly to a function.
That is important: an in-process test is excellent for route policy, but it
cannot prove how Node handles headers, connections, bodies, or a listening
socket.

### Request IDs and header ownership

If a trusted upstream already sends a syntactically valid request ID, the
server keeps it so logs across services can be connected. Otherwise it makes a
fresh one. The app handler may add an ordinary response header, but it may not
replace `x-request-id`, CORS decisions, or security headers such as the
content-security policy.

That is a useful general rule: **the layer that owns a cross-cutting security
decision owns the resulting header**. Allowing every handler to overwrite the
final header would let one feature silently weaken a protection shared by the
whole product.

### CORS preflight is a real request, not an app route

A browser often sends `OPTIONS` before a cross-origin write. The server checks
whether the path exists, determines the methods actually registered there, and
returns a short preflight response. For an approved browser origin it also
sends `Vary: Origin`, which tells shared caches that the response can differ by
origin.

The preflight does not prove the person may perform the later write. It only
answers the browser question: “may code from this origin attempt to make this
kind of request?” The later `POST` still needs authentication, permission,
tenant, validation, and resource authorization.

### Why the server does not trust `X-Forwarded-For`

A newcomer often hears “use the forwarded IP for rate limiting” and assumes it
is automatically safe. It is not. Any ordinary caller can send a fabricated
forwarded-address header unless the specific ingress removes it and writes a
trusted replacement.

The generic server therefore uses its actual socket peer address only. That is
safe from a caller spoofing a header, but it may be too coarse behind a load
balancer because many users appear to come from the same ingress. A public
target must make a separate, documented decision about trusted ingress address
resolution. That decision belongs to the target/adaptor boundary because it
depends on the chosen proxy, network, and deployment topology.

### A safe local limiter is not yet a scalable public limiter

The current in-memory limiter has two worthwhile properties: its bucket map is
bounded, and it never uses the raw bearer token as a key. Those prevent an
unbounded-memory attack and avoid making a credential appear in a likely log or
debugging surface.

However, each server replica has its own memory. If two replicas each allow
100 requests, a caller may obtain roughly 200 requests by being sent to both.
That is not a bug in JavaScript; it is the meaning of process-local state. A
public multi-replica deployment therefore needs a selected shared limiter and
an approved target-specific client-address rule. The plan and readiness record
now treat those as public-exposure gates rather than quietly claiming that the
local fallback is production scaling.

### Draining is more careful than “close the server”

When a process receives a shutdown signal, it first marks itself not ready.
The load balancer can then stop sending new requests. The listener also stops
accepting new work, while already-running requests get a bounded period to
finish. If that deadline expires, their cancellation signals are aborted and
the remaining connections are closed.

This is kinder to legitimate in-flight work than immediately killing the
process, but it still has a limit. A handler must honour its cancellation
signal; the server cannot safely undo an external side effect that the handler
already began.

If a handler ignores that signal and outlives its request deadline, the client
still receives a safe timeout response. But the server keeps that handler in
the concurrency count until it settles. Otherwise an attacker could repeatedly
cause timeouts and turn a maximum of 100 concurrent requests into unlimited
background work merely by making handlers ignore cancellation.

### Misconception to avoid

> “Once route authentication is robust, raw HTTP handling is just plumbing.”

No. Authentication protects *who may act*. Transport hardening protects the
finite CPU, memory, sockets, and time that are needed even to decide whether a
request may act. Both are security boundaries.

### Study question

Why must a public target use a target-owned trusted-ingress address policy
instead of letting every app read `X-Forwarded-For` directly?

Because whether that header is trustworthy depends on the actual proxy and
network path. If every app interprets it independently, a caller may spoof it
or different features may disagree about identity and rate-limit scope. One
target-owned resolver makes the trust boundary explicit and testable.

## 49. Composition Is More Than Authentication

We have used Cognito as a concrete example, so it would be easy to form this
mistaken picture:

```text
target composition entrypoint = the file that connects Cognito
```

That is too narrow. A target composition entrypoint is the place where a
particular running target answers a larger question:

> “Which real implementations, host facilities, and operating rules make this
> product run safely in *this* environment?”

Authentication is one answer to that question. It is not the whole question.

### A small analogy

Think of `platform/server` as a standardised empty control room. It has labelled
connections for the things a service needs, and it knows the order in which to
operate safely. It does **not** decide which company supplies electricity,
which alarm service is used, or which building it is installed in.

The target composition entrypoint is the installation plan for one building.
It says which approved services are connected there and makes the choices
auditable. The infrastructure then provisions the actual building facilities.

```text
platform contracts and shell       target composition              infrastructure
----------------------------       ------------------              --------------
“a logger can be used”        ->   “this target emits JSON”   ->   container collector,
“a rate limiter can be used”  ->   “this target uses X”        ->   network/service rules
“an identity can be verified” ->   “this target uses Cognito”  ->   Cognito configuration
```

### The three pieces that must not be confused

| Piece | It answers | Example |
| --- | --- | --- |
| **Port or platform seam** | “What capability does the application need?” | `Logger`, `PlatformRateLimiter`, authentication facts, an audit-record contract |
| **Adapter or host delivery** | “How is that capability supplied here?” | a Cognito adapter; a Redis-backed limiter; stdout collected by the container host |
| **Target/infrastructure choice** | “Where, under what operating rules, and with what evidence?” | allowed log destination, retention, access controls, WAF, secret injection, a queue resource |

An adapter is often TypeScript code, but it does not have to be. Writing safe
structured JSON to stdout is a platform behaviour; a container log driver
collecting it can be an infrastructure delivery mechanism. Both sides must be
specified before we can honestly say “observability is present.”

### What the current Kanbien shell has — and does not yet have

| Capability | Current position | Important limitation |
| --- | --- | --- |
| Authentication | The target composition selects the approved Cognito adapter. | It proves one identity choice, not logging, quotas, queues, or storage. |
| Observability | The platform can create safe structured records and has metric/trace seams. | No external exporter or durable observability sink has been selected. ECS collection alone is not a complete observability design. |
| Rate limiting | The generic shell has a bounded local in-memory limiter. | It cannot enforce one quota across multiple service replicas; public readiness remains blocked until a shared adapter and ingress trust policy are selected. |
| Client address | The listener can use the direct socket peer address. | A public proxy path requires a target-owned trusted-ingress resolver; individual apps must not read forwarded headers themselves. |
| Queues and workers | The platform has provider-neutral job/worker mechanics. | No queue provider has been selected or provisioned. |
| Secrets and configuration | Process configuration can be consumed by the runtime. | Target-level secret injection is not the same as a completed secrets-management strategy. |
| Audit/security records | The platform has record shapes and safe normalisation. | No durable, queryable record sink has been selected. |

### The useful inventory

For each target-relevant capability, we will record six facts:

1. The **port/contract**: what the product or platform asks for.
2. The **selected implementation or host delivery**: what actually provides it.
3. The **composition owner**: who is accountable for making that choice.
4. The **infrastructure resource**: what must exist outside the process.
5. The **failure behaviour**: what happens if it is unavailable, slow, or unsafe.
6. The **readiness proof**: what test, configuration check, or operational evidence proves the target is safe to expose.

This is deliberately stronger than a list of installed packages. A package can
exist while nothing has selected or configured it. Conversely, a container host
may deliver a capability without a new TypeScript package. The inventory makes
either situation visible.

### Misconceptions to avoid

> “The service runs in ECS and sends logs to CloudWatch, so observability is
> complete.”

Not yet. We still need an agreed safe record shape, redaction, delivery path,
access and retention rules, metrics/traces where needed, alert ownership, and
evidence that those controls are active.

> “We should immediately add one adapter folder for every possible capability.”

Also no. An empty adapter is only architecture-shaped clutter. We create a
bounded adapter slice when there is a chosen provider, an owner, a failure
model, acceptance tests, and target readiness evidence.

### Study question

Why is a target entrypoint still accountable for log delivery when a container
platform performs the collection rather than a TypeScript logging adapter?

Because the target must explicitly choose and prove the destination, access,
retention, and failure behaviour. Moving the delivery mechanism outside the
process does not remove the operating decision.

### Plan record

The target capability inventory and the explicit current gaps have been added
to the [Platform Runtime Implementation Plan](../../../.agentic/03.product/plans/implementation/platform-runtime-implementation.md).
This is a clarification of ownership and future readiness work; it does not
pretend that unselected observability, shared-rate-limit, queue, secret, or
audit providers now exist.

## 50. Cognito Is An Adapter, Not The Whole Identity Operation

Yes: Cognito needs the same operational layer as rate limiting. We already
have more of it recorded than for a shared rate limiter, but it is not yet
complete or proven for a public deployment.

The Cognito adapter answers a deliberately narrow technical question:

```text
Given a bearer token, can this process verify that Cognito issued an acceptable
access token and translate its approved claims into platform identity facts?
```

It constructs the Cognito issuer and JWKS address, requires an access token for
the expected client, extracts Cognito groups/scopes when configured, and
returns the provider-neutral authentication result that the server understands.
That is important—but it is only the in-process verification step.

### Compare the two layers

| Layer | Cognito adapter owns it | Target operational model owns it |
| --- | --- | --- |
| Token verification | issuer, JWKS lookup, access-token and client requirements | key-rotation and cache-failure operating policy |
| Permission facts | extracting configured groups/scopes and mapping them | who may change mappings, least privilege, review and rollback |
| Client credentials | reading the selected configuration names | secret injection, rotation, revocation, emergency recovery |
| Exposure | returning authenticated facts to the generic server | public/private access, CORS, TLS, ingress, rate limits and WAF |
| Evidence | safe local contract and adapter tests | deployed protected-route smoke, monitoring, audit access and alert ownership |

### What is already recorded

The Kanbien staging target profile has an initial Cognito provider choice, user
pool, confidential machine-to-machine client, resource-server scope, scope to
permission map, client-secret storage location, and CORS intent. This is why
Cognito is further along than the shared-rate-limiter adapter.

But the target and its readiness manifest are still draft/blocked. Recording a
user-pool identifier is not proof that its operation is ready for public use.

### The important limitation of the present example

The selected Cognito path is **machine-to-machine**. It is suitable for a
service presenting a client-credentials access token. It is not yet Bill the
accountant in a Benelux group.

That later human-user scenario needs additional, explicit decisions:

```text
identity provider verifies Bill
        ↓
product/identity boundary establishes Bill's tenant and group membership
        ↓
app/resource authorisation decides whether Bill may read this Benelux invoice
```

Parsing a Cognito group claim alone cannot safely provide that complete model.
The platform must still determine the membership source, change/revocation
flow, tenant binding, and resource-level decision.

### Operational questions we must answer before public exposure

1. Who owns the user pool, client, permissions, and emergency access?
2. How are client credentials injected, rotated, revoked, and recovered?
3. What happens when keys rotate, a JWKS lookup fails, or a token is suspected
   compromised?
4. How long may an issued token remain valid, and what is the response when it
   must stop being trusted sooner?
5. Who reviews group/scope-to-permission changes, and how are they rolled back?
6. What authentication events are safely recorded, monitored, retained, and
   alerted on without storing bearer tokens?
7. What deployed test proves a real protected route rejects invalid,
   unauthorised, and allowed requests?

### Misconception to avoid

> “JWT verification passed locally, so authentication is production-ready.”

Local verification proves only that the process can validate a correctly
configured token. Production readiness additionally depends on credential and
key lifecycle, abuse controls, target configuration, operational ownership,
and deployed evidence.

### Study question

Why does a machine-to-machine scope mapping not automatically solve the
earlier example of Bill accessing only invoices for Benelux clients?

Because it says what a calling client may generally do. It does not, by itself,
prove Bill's current group membership, tenant assignment, geographic scope, or
the relationship between an individual invoice and the Benelux region.

### Plan record

The [Platform Runtime Implementation Plan](../../../.agentic/03.product/plans/implementation/platform-runtime-implementation.md)
now explicitly separates the Cognito adapter from target operational readiness.
It assigns the latter to target profile, deployment readiness, infrastructure,
and runbook work rather than expanding the adapter into an identity-management
system.

## 51. Resetting The Learning Map: Define The Target Before Declaring Layers Complete

The concern that prompted this reset is important: following the folder tree
can teach us how a module works, but it cannot prove that a real deployed
system has every dependency it needs.

We are therefore changing the question from:

```text
“Have we finished platform/security?”
```

to:

```text
“For the intended production target, is every required capability complete
from contract through operating proof?”
```

### The first target we are designing

The initial reference target is a real public-internet production target for
the future Entity Builder on AWS ECS Fargate in `eu-west-1`. Its first release
starts with API capability, profile image/document handling, safe bulk
upload/download, and later agent workflow. Its long-term design keeps web,
desktop, mobile, tablet, chat, and voice as different clients of the same
governed capability path.

It must anticipate personal and medical/sensitive data, tenant/group/resource
authorisation, EU/UK data-residency requirements, hundreds of concurrent users,
and a cost-aware single-operator beginning. Those facts make a local
server-and-JWT demo plainly insufficient as the definition of ready.

### The new reading rule

Every platform capability now has a maturity state:

| State | Plain meaning |
| --- | --- |
| Requirements captured | We know it is needed, but have not built its boundary. |
| Contract/local proof | We can prove the provider-neutral behaviour locally. |
| Adapter selected | A real provider/host mechanism has been chosen. |
| Infrastructure planned | We know the target resources and controls needed, without creating them. |
| Target configured | The target explicitly selects the capability. |
| Operationally proven | It works, fails safely, is observable, recoverable, and has target-level evidence. |

For example, the current rate limiter is at **contract/local proof**. That is
good progress—not an AWS multi-replica production quota. Cognito has a real
adapter, but the current example is machine-to-machine and does not yet solve
human membership, tenant, or resource authorisation. This wording lets us be
honest without discarding useful earlier work.

### A crucial distinction

We are not trying to build every possible cloud service before making a
product. We will build every capability required by the first release to its
complete vertical slice, then build future capabilities before the feature that
needs them ships.

```text
first real file upload
  requires storage + access control + retention + safe upload path
  + observability/audit + recovery proof

first agent workflow
  additionally requires durable work + prompt/tool safety
  + provider data-boundary decision + evaluation/incident controls
```

### The remaining decisions are visible, not forgotten

The baseline intentionally marks several decisions as open: human onboarding
and MFA/recovery model, first-tenancy model, precise EU-versus-UK residency,
sensitive-data onboarding approval, document threat model, AI/voice data
boundary, recovery objectives, and initial cost ceiling. We will decide these
in small batches before selecting providers or provisioning infrastructure.

### Plan record

The complete matrix is now the
[Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md).
The platform-runtime and product-harness plans now point to it, so a package
cannot be called a production default merely because it has local tests.

## 52. Multi-Tenancy, Root Approval, And Residency Homes

Three decisions now make the first reference target much more concrete:

1. The first `PlatformRoot` is securely bootstrapped and root identities are
   invite-only. A self-service admin/app-user signup is only a request; it has
   no active tenant access or privileged grant until a verified root approves
   it.
2. The product must support multiple independent tenants from the first real
   release.
3. Each tenant has an EU or UK residency home. Cross-boundary processing is
   denied by default.

### Why signup is not access

It is tempting to picture a signup as this:

```text
person signs up -> person can use the application
```

For a multi-tenant sensitive-data system, the safer model is:

```text
person signs up -> pending identity/application
                    -> root approval
                    -> tenant membership and granted role
                    -> resource-level authorisation on each action
```

The first arrow proves only that an identity wants an account. It does not
prove that the person belongs to a tenant, should receive a role, or may read
any tenant data.

`PlatformRoot` is deliberately unusual. It is an operator/product authority
for bootstrap and approval, not a shorthand for unrestricted everyday access to
every tenant's business or medical data. Any exceptional access must be narrow,
audited, and separately designed.

### Why `eu-west-1` is not enough for a UK-residency tenant

The initial EU target is intended for `eu-west-1`. If a tenant is UK-resident
and the policy says no cross-boundary processing by default, that tenant's
sensitive data cannot simply be put in the EU target to save money.

This is not only the primary database. The residency home follows the data:

```text
tenant data -> database, file store, backups, logs, audit records,
               queues, caches, search, support access, and AI/voice processing
```

Therefore, support for UK-residency tenants requires a separately planned and
proved UK-residency production target. If that is not affordable for the first
launch, the honest low-cost choice is an explicitly EU-only launch that refuses
UK-residency onboarding until the UK target is complete.

### Misconception to avoid

> “Tenant isolation means putting a `tenantId` column on every table.”

That column can be part of the design, but it is not the proof. Isolation must
hold at identity/membership resolution, every query and object key, queue/job
payload, signed download, log/audit record, operator tool, backup, and AI/tool
call. A tenant-looking value sent by the browser, chat, or URL is untrusted
input—not authority.

### Study question

Why must a self-service signup remain unable to access a tenant even after it
has passed email verification?

Email verification proves control of an email address. It does not prove a
tenant membership, approved role, regional residency home, or access to a
specific resource.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now records root approval, first-release multi-tenancy, and EU/UK residency
homes as target requirements. It also makes the cost-safe constraint explicit:
an EU-only launch is permissible if UK-residency onboarding is refused until a
separate UK target is proven; silently placing UK data in the EU target is not.

## 53. Administrative Roles Have Scopes, Not Just Names

The initial EU-only launch and the three administrative role concepts are now
defined:

| Role | Scope | Primary responsibility | Cannot do by implication |
| --- | --- | --- | --- |
| `PlatformRoot` | Platform | Manage tenants, tenant roots, and platform-level tenant administration. | Read every tenant's business/medical data merely because it is powerful. |
| `TenantRoot` | One verified tenant | Manage that tenant's app users and tenant administration. | Administer another tenant, create tenants, or manage platform roots. |
| `TenantAppUser` | One verified tenant and assigned resources | Use authorised front-office and back-office business capabilities. | Administer the tenant or platform merely by consuming the app. |

### The central rule: scope is part of the authority

The word `root` alone does not decide what an action may touch. A request must
still carry a verified principal, a verified tenant where applicable, a
declared permission, and any required resource facts.

```text
PlatformRoot + platform tenant-management permission
  -> may create or administer a tenant record

TenantRoot + tenant-user-management permission + tenant A membership
  -> may administer users in tenant A
  -> may not administer users in tenant B

TenantAppUser + business permission + tenant A membership + resource approval
  -> may use the permitted business capability in tenant A
```

This is why roles should be permission bundles at an explicit scope, rather
than magic labels scattered through route handlers. It also lets one human have
more than one deliberate assignment if needed without silently widening a
lower-scope grant into a higher-scope one.

### Signup and tenant administration

The earlier rule remains: a self-service signup is a pending request, not
access. `PlatformRoot` approval is the initial gate. The remaining policy
question is whether a `TenantRoot` may later approve app-user requests *after*
that initial gate. We will decide it explicitly, with an audit trail, rather
than assuming that “manage app users” automatically means “approve all
signups.”

### EU-only initial launch

The first launch accepts EU-residency tenants only. This is a cost-conscious
scope reduction, not a relaxation of the no-cross-boundary rule. UK support is
a later capability that needs its own target and evidence before any UK tenant
is onboarded.

### Study question

Why is `TenantRoot` not simply a less powerful `PlatformRoot`?

Because they are authorities over different scopes. A tenant root's
administrative power is bounded by verified membership of one tenant; it must
not be able to traverse or enumerate other tenants at all.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now records the three scope-bound role concepts and makes the first production
launch explicitly EU-only.

## 54. Creation By The Parent Is Approval

The approval hierarchy is now explicit:

```text
PlatformRoot creates/approves tenant + appoints TenantRoot
  -> TenantRoot creates/approves TenantAppUser for that tenant
    -> TenantAppUser uses explicitly granted business capabilities
```

There is no separate approval click after an authorised parent directly creates
the lower-scope record. The creation itself is the approval and must produce an
audit record such as `created-and-approved`.

Self-service requests work differently:

| Request | Starts as | Required parent action |
| --- | --- | --- |
| Prospective tenant / tenant-root request | Pending | `PlatformRoot` approves and activates the tenant/root relationship. |
| Prospective tenant app-user request | Pending in one verified tenant | That tenant's `TenantRoot` approves and activates membership. |
| Direct authorised creation | Active only after validation | The parent actor's creation is the approval. |

### The safety catch

“A user created another user” is not sufficient on its own. We must always ask:

> Did the actor have the explicit user-management permission at the parent
> scope?

An ordinary `TenantAppUser` does not gain the ability to approve another user
just because a browser, API client, or chat request says “create user.” A
`TenantRoot` may do so only for the tenant resolved from verified membership;
it can never use a supplied tenant ID to create someone in another tenant.

### Study question

Why should direct creation be recorded as `created-and-approved` rather than
only `user-created`?

Because the record needs to explain why the new identity became active without
a separate approval event. It captures the approving actor, their scope, the
tenant, the resulting role, and the decision in one accountable action.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now owns this parent-scope approval rule. It replaces the previous open question
about whether a tenant root may approve app users.

## 55. Deferred MFA And Controlled Root Recovery

The initial decision is not to require MFA for `PlatformRoot` or `TenantRoot`.
This is allowed as a consciously recorded early-stage risk decision, but it
does **not** make single-factor privileged access a secure default or a future
compliance claim.

The practical consequence is that the later human-identity design must make
the compensating controls visible: chosen primary credential, reset policy,
session duration, privileged-login rate limits, safe authentication alerts,
and recovery evidence. MFA remains a deliberate future upgrade rather than an
unfulfilled promise hidden in a plan.

### Replacement root through a controlled migration

If the only `PlatformRoot` becomes unavailable, the recovery policy is to
create a replacement root through a governed one-shot migration.

That word needs care. This must **not** mean:

```text
ordinary deployment automatically creates a root
application API can create a root
chat or voice command can recover root access
operator edits the database without evidence
```

Instead, the recovery operation must be deliberately invoked through a
protected recovery/deployment path and answer these questions:

```text
Who authorised recovery?
Which new identity becomes the replacement root?
What happened to the prior root?
Which preconditions were checked?
What immutable audit evidence proves the action?
```

The migration should be idempotent: retrying it must not accidentally create
several platform roots. It must also avoid becoming a routine schema migration
that runs whenever the application deploys.

### Misconception to avoid

> “A database migration is automatically safer than an admin screen.”

Not necessarily. A migration may be more tightly governed than an app route,
but if every routine deploy can invoke it without special control, it becomes a
very powerful hidden route. Safety comes from its protected invocation,
preconditions, audit evidence, and recovery governance.

### Study question

Why must a root-recovery migration consider the previous root's state?

Because creating a replacement without disabling or accounting for a
compromised prior root can leave two uncontrolled high-privilege identities
active at once.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now records MFA as deferred for the initial release and root recovery as a
governed one-shot migration, with its required controls still visible.

## 56. Email And Password Is The Sign-In Method, Not The Full Policy

The initial human sign-in method is email and password. This answers the
experience question—what a person enters to sign in—but it does not yet answer
all the security questions around that credential.

```text
email + password
  -> email verification rule
  -> password strength/reuse/breach rule
  -> reset and recovery rule
  -> session lifetime rule
  -> login rate-limit and alert rule
  -> approval and tenant-assignment rule
```

The existing Cognito example validates machine-to-machine access tokens. It is
not yet evidence that the human email/password flow, reset flow, or approval
state machine is implemented. A later selected human Cognito configuration and
adapter behaviour must translate that human identity safely into the same
provider-neutral principal and scoped-authorisation path.

### Misconception to avoid

> “Email/password means the identity problem is solved.”

No. It chooses the first door into the system. Verification, credential reset,
sessions, abuse resistance, privilege approval, tenant membership, and
revocation decide whether that door is safe to use.

### Study question

Why must password-reset policy be considered alongside the no-MFA decision?

Because reset is another way to obtain the credential. If its proof and
rate-limit rules are weaker than normal sign-in, it becomes the easiest path to
take over a privileged account.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now records email/password as the selected initial human sign-in method while
keeping the remaining credential-policy controls visible.

## 57. Verification Links And Password-Reset Links Prove Different Things

Email verification is mandatory before a self-service signup may enter the
pending approval workflow. Password reset also uses an email link.

The links use the same delivery channel, but they must not be interchangeable:

| Link purpose | What it may do | What it must not do |
| --- | --- | --- |
| `verify-email` | Mark that an identity controls the stated email address. | Reset a password or approve membership. |
| `reset-password` | Allow one password-reset flow for the requested identity. | Verify an unrelated address, approve membership, or act as a normal session. |

Each link must be purpose-bound, one-time, and short-lived. The token inside a
link is credential-like: it must never appear in normal logs, audit records,
analytics, error reports, or referrer-bearing outbound requests. The system
must never email a password.

### Why this matters more while MFA is deferred

For an email/password account, a reset link is another way to become that
account. If it can be replayed, lasts too long, or leaks through logs, it can
be used to take over a privileged identity. The reset policy therefore needs
its own rate limits, session-invalidation decision, and safe notification path.

### Study question

Why does verified email still not make a new tenant app user active?

It proves control of an email address. It does not prove that the person belongs
to the tenant or should receive the requested role; `TenantRoot` approval or
direct authorised creation still establishes that membership.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now makes email verification mandatory and defines verification/reset links as
separate, purpose-bound credential flows.

## 58. Password Reset Ends Old Sessions

When password reset succeeds, every existing session for that identity is
revoked. The reset browser does **not** receive an authenticated session; the
identity signs in normally with the new password, and receives a safe post-reset
notification.

```text
password reset succeeds
  -> previous browser, mobile, API, and remembered sessions become invalid
  -> reset browser must perform normal sign-in with the new password
  -> safe notification helps the identity notice unexpected recovery
```

This is especially valuable while MFA is deferred. If someone else had already
obtained a session using the old credential, the legitimate person can remove
that access by resetting their password.

The notification says that a reset happened. It never contains the password,
reset link/token, or other credential material.

### Study question

Why is it unsafe to revoke only the session that requested the reset?

Because a compromise may be occurring in a different browser, device, or API
client. Revoking only one session leaves that unknown session active.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now makes full existing-session revocation, normal post-reset sign-in, and safe
post-reset notification the initial reset policy.

## 59. Tenant Configuration Uses A Security Floor, Not A Security Escape Hatch

The identity-policy settings will be tenant-configurable, with defaults
implemented as a versioned baseline. That is the right direction—but “tenant
configurable” must not mean “a tenant may turn off platform safety.”

```text
platform invariants
        + product baseline version
        + tenant restriction
        = effective identity policy
```

Every applicable requirement must pass. A tenant can make its own policy
stricter, but cannot lower the shared floor merely by choosing a value in a
configuration screen.

| Policy control | Tenant may do | Tenant may not do |
| --- | --- | --- |
| MFA | Require it sooner for that tenant. | Disable it if a later platform/product baseline makes it mandatory. |
| Password strength | Require a stronger rule. | Set a weaker rule than the platform floor. |
| Session lifetime | Shorten it. | Extend it beyond the platform maximum. |
| Login/reset limits | Choose stricter limits. | Remove the anti-abuse floor. |
| Notifications | Add tenant notifications. | Remove required security/recovery evidence. |
| Email verification and reset safety | Use the standard flow. | Disable verification, reuse a link, or retain old sessions after reset. |

`PlatformRoot` owns the floor, baseline versions, and any formal exception
path. `TenantRoot` can choose an approved baseline and tighten settings for its
tenant. Any requested relaxation needs an explicit exception with an owner,
reason, expiry, and evidence—it cannot be a hidden checkbox.

### Why policy changes are security events

Changing a password/session policy may affect active sessions, pending users,
and recovery behaviour. Therefore every policy change needs an authorised
actor, scope, before/after version, validation result, effective time, and
audit record. The policy record contains settings and version references, never
passwords, reset links, or provider secrets.

### Study question

Why is “set tenant policy to a weaker password rule” not just another tenant
configuration choice?

Because it weakens a shared security boundary and can expose the whole product
to account takeover or compliance risk. That is an exception to a platform
baseline, not ordinary tenant preference.

### Plan record

The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now applies the existing versioned-baseline and tenant-tightening model to
identity policy.

## 60. Identity Security Baseline v1

We have now turned the earlier identity decisions into one named, versioned
policy: `identity-security-baseline.v1`. Naming the policy matters. It lets a
product say exactly which security promise it adopted, lets a tenant make that
promise stricter without inventing its own model, and gives future changes a
clear migration point.

The policy is intentionally not “a Cognito configuration file.” It describes
the result the implementation must produce, regardless of whether the eventual
human identity adapter is Cognito or another approved provider.

| Area | Baseline default | Why it exists |
| --- | --- | --- |
| Password | Minimum 15 characters, accepts at least 64, allows spaces/Unicode/paste/password managers, and screens breached/common/contextual passwords. | Longer unique passwords are useful; awkward character rules and password-manager bans usually make passwords worse rather than safer. |
| Password lifetime | No routine expiry; force a change for compromise, recovery, or authorised revocation. | Arbitrary expiry teaches predictable minor changes, while compromise signals point to a real reason to act. |
| Verification and reset | Separate one-time `verify-email` and `reset-password` tokens, each limited to 15 minutes. | Possession of a reset link must not accidentally become email approval, a normal session, or a reusable credential. |
| Reset result | Revoke all sessions, then require normal sign-in with the new password. | Someone holding an old cookie or token loses access; a stolen reset link does not itself leave an authenticated session behind. |
| Sessions | 15-minute idle limit, 8-hour absolute limit, server-side enforcement, identifier rotation after authentication and privilege change. | A browser timer alone cannot revoke a copied token; the server must decide whether the session still exists. |
| High-risk actions | Reauthenticate with the current password for credential changes, role changes, tenant-policy changes, and ordinary privileged recovery actions. | A temporarily unattended but authenticated browser should not be enough to alter the account's security boundary. |
| Abuse resistance | Generic responses plus progressive server-side delay after repeated sign-in failures; no permanent automatic lockout. Reset requests are rate-limited without revealing whether an account exists. | It raises the cost of guessing and reset-email abuse without turning an attacker into the person who can permanently lock out a legitimate user. |
| Audit and alerts | Audit lifecycle/grant/policy/reset completion facts; create separate security signals for escalating abuse; send safe success notices, not one email per failed attempt. | We need a reliable compliance trail and meaningful operator signal without filling logs and inboxes with sensitive or noisy data. |

### The important correction to our earlier reset explanation

Earlier we said that the reset browser could continue as the only new session.
The approved baseline is stricter: reset invalidates every session and then
requires a normal sign-in. A reset token proves recovery permission for one
short-lived action; it is not a durable login credential.

### What a tenant can and cannot change

```text
platform floor
  + adopted baseline v1
  + stricter tenant setting
  = effective identity policy
```

A tenant can shorten a session lifetime, require an available extra factor,
or reduce permitted reset attempts. It cannot lower the password minimum,
disable email verification, extend reset-token lifetime, retain sessions after
reset, or remove required evidence. A formal exception has an owner, reason,
scope, expiry, approval, and audit trail; it does not silently change the
platform floor.

### A crucial implementation boundary

The policy is active, but the human identity capability is still only
`requirements captured`. We have not built a human Cognito adapter, a tenant
policy resolver, verification/reset delivery, session revocation, or MFA.
The policy tells the next implementation slice how to prove itself; it does
not make the system protected merely by existing in a Markdown file.

Medical or other special-category data remains behind an additional gate: an
MFA-capable identity baseline and target must be available and applied to the
relevant privileged roles, alongside the separate privacy, residency, and
operating evidence.

### Study questions

Why is a reset token not used as a normal login session after the password was
changed?

Because recovery permission is narrower and more short-lived than an ordinary
session. Requiring the new password at normal sign-in limits what a stolen or
misdirected recovery link can achieve.

Why do we distinguish an audit event from a security signal after failed
sign-ins?

An audit event explains a completed accountable action, such as a password
reset. A security signal highlights a concerning pattern, such as repeated
failures. Combining them blindly creates a large, sensitive, and noisy record
that is useful for neither purpose.

### Plan record

The approved policy is now recorded in the
[Identity Security Baseline v1](../../../.agentic/03.product/standards/identity-security-baseline.v1.md).
The [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
keeps the honest implementation state and completion gate.

## 61. Scope Correction: Platform Proof Before Application Work

We were beginning to design a future identity-and-access application too soon.
That architecture is worth recording, but it is **not** the next implementation
task.

The immediate goal is smaller and more disciplined: prove a production-shaped
platform layer with the deliberately boring `platform-smoke` app.

```text
now
  platform shell + smoke app + target/deployment proof

later
  identity-and-access app + tenant membership + business features
```

The smoke app is not a business application. It is a controlled probe that
lets us test whether the platform can mount an app, start a server/worker,
validate configuration, apply the selected machine authentication boundary,
produce health and safe records, package itself, and eventually run in an
approved target.

This distinction resolves the apparent conflict in the earlier discussion:
the future identity-and-access app will reuse platform mechanisms, but it must
not be built merely to prove those mechanisms. Building user profiles, tenant
membership, groups, approvals, or entity data now would blur the platform
proof and make failures much harder to diagnose.

### What a successful smoke deployment does—and does not—prove

| A smoke deployment can prove | It does not prove |
| --- | --- |
| The image starts in the selected target. | Human registration, sign-in, verification, reset, or MFA. |
| The public edge, health endpoints, configuration, and selected machine-token boundary work together. | Tenant approval, group membership, or invoice/resource authorisation. |
| A mounted app can receive a safe authenticated request and return a response. | That the Entity Builder is ready for real users or personal/medical data. |
| Logs, metrics, alerts, rollback, and operational evidence can be exercised for that narrow slice. | That every future product capability has a provider, persistence model, or compliance evidence. |

### Study question

Why not build the identity-and-access app first if every later product will need
it?

Because it would test too many unknowns at once: the platform, the target,
human credentials, mail delivery, session revocation, persistence, tenant
policy, approval logic, and product authorisation. A smoke proof keeps the
first question answerable: “Can our platform foundation deploy and run safely?”

### Plan record

The [Platform Runtime Implementation Plan](../../../.agentic/03.product/plans/implementation/platform-runtime-implementation.md)
and [Production Reference Target Baseline](../../../.agentic/03.product/plans/implementation/production-reference-target-baseline.md)
now explicitly hold this boundary.

## 62. A Read-Only Inspection Separates Planned From Real

We inspected the existing Kanbien staging AWS boundary without changing any
resource. This is the first operational lesson in practice: a target profile
is a promise about what should exist, while a cloud inspection tells us what
does exist.

The inspection found a mixed result:

| Exists now | Does not exist yet |
| --- | --- |
| Shared ECS cluster and ALB boundary | Platform-shell ECS task definition and service |
| Immutable, scan-on-push `platform-shell` ECR repository | Any platform-shell image in that repository |
| Machine Cognito client and `smoke.read` scope | Platform-shell target group, host rule, and DNS record |
| Existing HTTPS listener for other services | Platform-shell log group and alarms |
| Rollback procedure written down | A deployed workload, smoke result, or rollback exercise |

This is why operational work cannot be inferred from TypeScript or even from a
target profile. The source code can be correct, the desired AWS design can be
written down, and the service can still be absent.

The next change is not “add more logging code.” It is a bounded AWS runtime
target plan that makes the smoke app a real, observable ECS service by
immutable image digest. Only after that target exists can we prove delivery of
logs, alarms, health behaviour, protected-route responses, and rollback.

### Study question

Why is the empty ECR repository useful evidence but not a deployable platform?

It proves a controlled place for immutable images exists. It does not prove an
image was built from approved source, that ECS can run it, that traffic reaches
it, or that an operator can detect and recover from failure.

### Evidence record

The fresh [AWS target inspection](../../../docs/aws/inventory/kanbien-staging-platform-shell-target-inspection.md)
and the [staging readiness manifest](../../../infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml)
now reflect these verified facts.

## 63. A Hostname Can Point to an Application, Not Just a Static File Store

The word “website” describes what a person experiences. It does not tell us
how that experience is delivered.

In this case, the public route worked like this:

```text
kanbien.com / www.kanbien.com
        ↓ DNS alias
shared public load balancer
        ↓ default HTTPS route
old service-platform container
        ↓ startup migration
PostgreSQL database
```

The first two steps were healthy. The last two were not: the container tried
to migrate its database on startup, the database could not be reached, the
container exited, and the load balancer had no target to forward to. A `503`
here means “the gateway exists, but it currently has no healthy application
behind it.” It does **not** mean “the domain name has disappeared.”

This also explains why “keep the DNS records” does not automatically mean
“keep every old resource forever.” DNS is the stable public address. Behind it
we may eventually repair the old application or deliberately switch the
address to a replacement. We must first know which resources form the running
site and what recovery evidence exists; deletion before that is not cleanup,
it is an uncontrolled outage.

For now, the record is deliberately conservative: preserve the hosted zone and
public records, make no deletion, and keep public-site recovery separate from
the platform-shell smoke proof.

### Study question

Why does an empty load-balancer target group create a `503` even though DNS and
TLS are working?

DNS only tells the browser where to connect, and TLS establishes a protected
connection to the load balancer. The load balancer still needs a healthy target
that can answer the request. With no target, it has nowhere safe to send it.

## 64. A Deployment Profile Is Executable Security Policy

A target profile can look like “just configuration,” but it is part of the
security boundary. It tells a deployed process which identity provider to
trust, which permissions a token scope grants, which browser origins may call
it, and which health endpoints are public.

The smoke target revealed two useful mistakes before anything reached AWS:

- the app declared `platform-smoke.smoke:read`, while the target had tried to
  grant a different permission called `smoke:read`;
- the target selected Cognito but omitted the non-secret identifiers the
  Cognito adapter needs to verify tokens.

Neither error is dramatic in a text file. In a live process, the first would
turn a valid smoke token into an unexpected `403`; the second would prevent
the process from starting. This is why a deploy profile needs the same review
and validation discipline as source code.

The broader lesson is that a secure public deployment is a chain, not a single
container: an immutable image, dedicated IAM and network rules, exact runtime
configuration, shared rate limiting, a trusted ingress policy, edge defence,
observability, and rollback must all agree. A healthy `/livez` endpoint proves
only one link in that chain.

## 65. A Compiled Program Is Not Yet a Deployable Program

We found a useful deployment failure before AWS: the TypeScript compiler had
successfully produced the target entrypoint, but when Node tried to start it,
one imported AWS adapter resolved back to its workspace TypeScript file. Node
cannot execute TypeScript source directly, so the process failed before it
could listen for health checks.

The important distinction is:

```text
source code compiles
        is not the same as
the packaged runtime can resolve every dependency and start
```

In a development workspace, a package name such as
`@kanbien/platform-adapter-aws-auth-cognito` is often a helpful symbolic link
to a nearby source directory. That is convenient for editing, but it is not a
safe assumption for a production container. A container should have a sealed
runtime payload: compiled JavaScript for every internal package it uses,
deliberate package shims that resolve those compiled files, and only the
external production dependencies it needs.

The image build now follows that shape:

```text
TypeScript sources
        ↓ compile
compiled platform, app, product, and AWS-adapter JavaScript
        ↓ prepare
generated internal package shims + production external dependencies
        ↓ copy into final image stage
small runtime image with no source-tree fallback
```

The new runtime-payload check temporarily hides the normal workspace package
links before starting the compiled entrypoint with the public target's
non-secret configuration. If a shim were missing, Node could not quietly fall
back to source code; the check would fail. This is a stronger proof than
compilation alone.

On 2026-09-06 we completed the next proof as well: Docker built the actual
image, ran it with a read-only root filesystem, temporary `/tmp`, dropped Linux
capabilities, and no-new-privileges, then successfully checked `/livez` and
`/readyz`. That proves the sealed local container can start under its intended
runtime restrictions. It still does **not** prove AWS networking, the ALB/WAF
path, an ECS deployment, real Cognito tokens, or rollback; those require a
separately reviewed cloud change and deployed smoke tests.

### Misconception check

“`tsc` passed, so the Docker image must work.”

Not necessarily. The compiler proves that TypeScript can be transformed and
type-checked. It does not prove the final filesystem layout, package exports,
production-only dependency set, image user, network behaviour, or health check
can work together. Those are deployment concerns, so they need deployment
proofs as well.

### Study question

Why did hiding the workspace links make this test more valuable?

Because a missing production shim would otherwise be hidden by the development
workspace. The test deliberately removes that accidental safety net and asks
the same question the final sealed runtime needs to answer: “Can every import
be resolved from the artifact I am actually shipping?”

Planning triage: this changed the platform-runtime implementation plan and the
staging deployment readiness record. It did not change a public app contract.

## 66. Observability: Safe Records, Metrics, and Traces

Observability begins with questions, not a dashboard or cloud service. For
every capability, the platform should be able to answer whether the system is
healthy, why a particular request failed, which policy decision applied, and
which meaningful action occurred—without creating a second, less-protected copy
of customer or credential data.

### Five related, but separate, forms of evidence

| Form | Primary question | Example | It must not become |
|---|---|---|---|
| Operational log | “What did the software or dependency do?” | A request timed out while creating an export file. | A raw request/response archive. |
| Metric | “Is there a pattern?” | Export failures increased this hour. | A per-customer record store. |
| Trace | “Where did one execution spend time or fail?” | Database lookup took 310 ms of an 842 ms request. | A copy of SQL, prompts, tokens, or provider payloads. |
| Security signal | “What control decision or unusual access pattern occurred?” | A verified principal lacked the required export permission. | A raw JWT, cookie, password, or full claim set. |
| Audit event | “Who attempted a meaningful action, on what, with what result?” | A tenant user requested an invoice export; it was accepted. | A duplicate of invoice rows, balances, or file contents. |

One request may produce several of these records. They can share an opaque
correlation ID, but no record family copies another family’s full payload. The
correlation ID describes the larger story; it is not a tenant ID, user ID,
invoice ID, credential, or authority claim.

### Allowlisted facts, not "log everything except secrets"

A denylist fails when a new sensitive field appears. An allowlist starts from
the safer position: a record may contain only named facts that its approved
profile permits. Unknown facts are omitted or rejected before they reach a
recording provider.

For an invoice export, an audit record may need an opaque export-job target,
verified actor type/reference, tenant reference, action, outcome, time, and
correlation ID. It does not need invoice rows, customer names, export contents,
signed download URLs, request bodies, tokens, cookies, raw authorisation
headers, stack traces, provider payloads, chat prompts, voice transcripts, or
audio.

Encryption and access control remain necessary later, but they do not make
unnecessary collection safe. First minimise the record; then protect the
bounded record that remains.

### A stable event vocabulary

HTTP methods are transport facts, not business actions. A `POST` can create a
user, request an export, approve a tenant, or start an agent workflow. The
event vocabulary therefore keeps these dimensions separate:

| Dimension | Examples | Purpose |
|---|---|---|
| Record family | `audit`, `security`, `operational` | Says which evidence contract and destination rules apply. |
| Event type | `billing.invoice.export` | Stable category for grouping and validation inside its record family. |
| Action | `export` | Meaningful canonical verb. |
| Outcome | `succeeded`, `denied`, `failed`; later operational lifecycle values may include `accepted`, `rejected`, `cancelled`, `timed_out`, or `retried`. | What happened to the action. |
| Actor type | `user`, `service`, `system`, `anonymous` | Who held accountable authority. |
| Interaction source | `web`, `mobile`, `desktop`, `tablet`, `chat`, `voice`, `cli`, `api`, `integration`, `scheduled_job`, `system` | How the work began. |
| Execution context | `server`, `worker`, `scheduler` | Where the work ran. |

The controlled action baseline is:

| Family | Actions |
|---|---|
| Resource lifecycle | `create`, `read`, `list`, `search`, `update`, `delete`, `archive`, `restore` |
| Relationships/access | `assign`, `unassign`, `grant`, `revoke` |
| Decisions/state | `approve`, `reject`, `enable`, `disable`, `publish`, `unpublish` |
| Data movement | `upload`, `download`, `import`, `export` |
| Workflow | `submit`, `cancel`, `execute`, `schedule`, `retry` |
| Identity/security | `authenticate`, `verify`, `reset`, `recover`, `rotate` |
| Generation | `generate` |

The controlled operational vocabulary is now implemented in
`platform/contracts/src/observability.ts`; it is not a licence for arbitrary
new strings. A genuinely new action requires a reviewed contract change,
corresponding validators, fixtures, and documentation. A feature must not use
transport words such as `POST` or put outcome into its event type. The existing
Core audit taxonomy is separate and remains unchanged until its own governed,
versioned migration.

### Metric cardinality and tenant visibility

Metrics are aggregates. Their labels must come from small, known sets such as
route/capability ID, bounded outcome, bounded source, dependency name,
deployment version, or tenant tier. A tenant, user, principal, resource,
request, correlation, trace, session, token, raw path, URL, IP address, and
free-text error can produce an unbounded number of metric series or disclose
sensitive context. They are not shared metric labels.

This does **not** mean that the platform ignores tenants. Tenant-scoped
investigation belongs in authorised audit/security/log search, and tenant usage
belongs in a deliberately designed usage-reporting record. A `TenantRoot` must
be limited to its verified tenant; a `PlatformRoot` starts from aggregate health
and needs explicit authority for a tenant-specific investigation. Tenant tier
or residency class may be a metric label only when its permitted values are
small, stable, and non-sensitive.

### Trace and span boundaries

Metrics reveal a pattern; a trace shows the timed path of one execution.

```text
request trace
  -> authentication span
  -> authorisation span
  -> database lookup span
  -> file-storage span
  -> queue-submission span
```

A correlation ID links the overall logical workflow. A trace ID links the
timing path of one execution, and each span has a parent/child relationship
within that trace. A worker handling a queued export later keeps the original
correlation ID but begins a separate execution trace linked through the job or
message causation chain.

Trace attributes have the same minimisation rules as logs. Trace sampling may
retain failures, unusually slow work, and a bounded successful sample, but
audit evidence and required security evidence are never sampled away.

### Capability observability profiles

A future capability declaration will reference separate audit,
security-signal, and operational-observability profiles. Each profile states
which events are meaningful, which allowlisted facts may be emitted, who may
read them, and why their retention/residency is justified. The platform owns
correlation/trace propagation, redaction, providers, and delivery behaviour;
the capability supplies only its approved business meaning.

For example, `billing.invoice.export` may audit an accepted export request and
its later completion or failure, emit a security signal for a relevant denial,
and record bounded request duration and export-outcome metrics. It must not
select a cloud vendor, log raw invoices, or turn a trace into a durable audit
record.

### What is implemented and what is not

Core already has correlation/causation concepts, versioned audit-event shapes,
and a metric-label guard that rejects many unsafe labels. Platform runtime
already carries correlation context and the deployed shell writes redacted
stdout JSON through its ECS host facility. These are useful seams, not a
complete record pipeline.

There is not yet a selected provider-neutral log/metric/trace exporter, durable
audit/security sink, tenant-scoped record-retrieval model, trace-propagation
implementation, canonical-action validator, or full metric guard against every
tenant-ID spelling. Those remain planned work and must be proved before the
platform is described as operationally complete for audit or observability.

### Current repository implementation

The existing observability helper has now been split into responsibility-named
files: `normalization.ts`, `logging.ts`, `metrics.ts`, and `tracing.ts`.
`index.ts` remains the one deliberate public barrel, so consumers continue to
import `@kanbien/platform-observability` without depending on internal paths.

This is a navigation and maintainability change, not a claim that a provider
or record pipeline now exists. The split makes the current seams easier to
inspect: normalisation is the safety gateway; logging and trace fields consume
it; metrics remain an independent aggregate-measurement concern.

### First tracing implementation slice

The repository now has the smallest useful tracing path without choosing a
tracing product:

```text
server request
  -> starts one provider-neutral span
  -> applies route/security/handler policy
  -> records the response outcome on that span
  -> ends the span
```

`packages/core/monitoring` defines the portable nouns: a trace context has a
trace ID and span ID; a child span also records its immediate parent span ID.
It defines the `Tracer` and `TraceSpan` ports, a no-op implementation for
normal operation with tracing disabled, and an in-memory implementation for
tests. Neither implementation selects a backend.

`platform/observability` is the safety bridge. It converts only an allowlisted
operational summary—HTTP method, stable route identifier, status, latency,
outcome, and bounded error class—into scalar trace attributes. It deliberately
does not put a request body, headers, cookies, token, raw URL, raw path,
tenant/user identifier, correlation ID, or trace ID into this general trace
attribute set. If a supplied tracer fails, the bridge replaces it with a no-op
span so observing a request cannot change the request's response.

This is not distributed tracing yet. The server does not accept a remote parent
context, an app handler cannot create a child span through its request context,
and there is no sampler, exporter, trace store, retention policy, or provider
adapter. A local queue message may retain an internal trace parent so its
worker span can become a child span, but the platform still has no general
application producer/outbox path that attaches a server span to a newly
created message. Those are later decisions because they change the operational
and data-governance boundary.

### Study question

Why should a request that creates an export job record `accepted` separately
from the worker later recording `succeeded` or `failed`?

The request accepted responsibility for future work; it did not prove that the
file exists. The later worker record supplies the actual completion outcome,
linked through correlation and causation without copying the export content.

## 67. Queued Work: Direct Cause, Trace Continuity, and Record History

### Start with three labels that do different jobs

Suppose a request begins an invoice export. The request creates event `e-17`,
which creates queue message `m-42`, which the worker delivers on its first
attempt. All of those facts may belong to one workflow, but they must not be
made to look identical.

```text
correlation: c-9    tells us “these facts belong to one story”

e-17 ──causes──> m-42 ──causes──> worker job
                         └── has internal trace parent ──> job span
```

| Fact | Its question | Worker-job value in this example |
|---|---|---|
| Correlation ID | “Which broader workflow is this part of?” | `c-9` |
| Causation ID | “What directly caused this work?” | `m-42`, not `e-17` |
| Trace parent | “Which timed span should this execution follow?” | The message’s internal trace-parent context, when present |
| Delivery attempt | “How many times has this message been delivered?” | `1`; a retry changes this, not the business cause |

The direct cause is deliberately the message the worker actually received. It
is tempting to copy `e-17` because it feels like the original reason for the
work. But `m-42` is the immediate parent and therefore the most useful link for
finding one exact delivery, retry sequence, or dead-letter outcome. The message
itself still preserves its earlier cause (`e-17`), so the complete chain is not
lost.

### What this implementation now does

Core queue messages can safely carry an optional internal trace parent. The
worker creates one job span for every non-idle delivery. If that queue trace
parent exists, the job span becomes its child; otherwise the worker begins a
new trace. The app handler never receives the trace context. It receives the
ordinary job context, whose direct cause is the input message ID and whose
correlation ID remains the workflow-wide value.

This difference matters because trace context is diagnostic machinery, while
causation is a durable business-lineage fact. A trace can be sampled, disabled,
or exported to a different operational system. The job’s direct cause must
continue to mean the same thing even when tracing is off.

The worker source is also now split by responsibility:

| File | Question it answers |
|---|---|
| `errors.ts` | What predictable worker failures look like internally |
| `types.ts` | What a queue, delivery, shell, and result mean |
| `queue.ts` | How the deterministic in-memory queue and idempotency fake behave |
| `worker.ts` | How one delivery is validated, observed, retried, or dead-lettered |
| `index.ts` | Which worker contracts and factories are supported for consumers |

The split does not add a cloud queue, a continuously polling worker, a database,
or a trace provider. It makes the current provider-neutral behaviour easier to
inspect and test.

### The deferred persistence rule

When a future capability changes a business record, the eventual persistence
transaction must be able to record a protected, append-oriented history entry
for the changed record version. That entry needs a bounded record reference,
version, action, tenant when applicable, actor or system when known,
correlation ID, and direct event/message cause. It must use an allowlisted diff
or revision policy—not a default copy of every row, request, token, prompt, or
medical/personal value.

Deletion should first create a controlled recovery state rather than instantly
destroy a record. A later scheduled purge or anonymisation must obey retention,
privacy-erasure, residency, and legal-hold policy. In other words, a soft
delete creates a repair window; it is not permission to retain sensitive data
forever. This is deferred until a real product schema and persistence adapter
exist, and is recorded in the platform-runtime implementation plan.

### Misconception check

“The trace ID is enough to explain why the worker changed a record.”

No. A trace ID is an operational timing link and may not exist or be retained.
The stable direct cause is the event or message ID. Record-change history then
uses that cause to answer which record version changed because of a particular
piece of work.

### Study question

If `m-42` is retried after an initial handler failure, should the second
delivery be caused by the first failed attempt?

No. It is still caused by `m-42`; only the delivery attempt changes. That is
why message identity, business causation, and delivery-attempt count are
separate facts.

Planning triage: the persistence lifecycle and record-lineage requirements are
now recorded in `platform-runtime-implementation.md`. The queue trace-parent,
worker job-span, and direct-cause contract work is implemented and tested in
this chat worktree, but has not yet been committed.

## 68. Observability Delivery: What the Target Already Does

### Emitting a fact is not delivering it

The platform server and worker can create safe operational facts: a structured
log record, a bounded metric observation, or a span. That is only the first
half of observability. A deployed target still needs to collect, retain,
protect, search, aggregate, alert on, and eventually expire those facts.

For the current Kanbien staging target, the log route is deliberately modest:

```text
platform process writes safe JSON to stdout
        ↓
ECS awslogs log driver
        ↓
CloudWatch log group: /ecs/kanbien-staging-platform-shell
        ↓
operator searches a 14-day operational-log window
```

This does not require generic platform code to import an AWS CloudWatch SDK.
The application process uses the provider-neutral logger; the ECS task
definition is the AWS-specific delivery mechanism. Platform emits a safe
record; the target adapter and infrastructure deliver it.

### Four sources of operational evidence

| Source | What it tells us | Current delivery | What it does not prove |
|---|---|---|---|
| Application stdout logs | A particular server or worker decision/outcome | ECS `awslogs` to a retained CloudWatch log group | A durable audit trail or security-record store |
| ALB metrics | Whether traffic reaches healthy targets and whether targets return 5xx responses | Native CloudWatch metrics and alarms | Why an individual application decision failed |
| ECS metrics | Whether the service has the desired number of tasks and is approaching CPU/memory pressure | Native CloudWatch metrics and alarms | Business capability success or failure |
| WAF metrics | Whether web-request rules are matching | Native CloudWatch WAF metrics | Full request logging; that is deliberately deferred pending a redaction/retention profile |

The foundation target also sends availability alarms through an SNS topic to an
operator-controlled email subscription. An alarm says, “this service may need
attention.” It is not a diagnostic log, security signal, or accountable audit
event.

### What is still missing

The current target has a **log destination and infrastructure health alarms**.
It does not yet have all forms of observability delivery:

- Platform metric observations do not yet have a selected CloudWatch metric or
  log-derived-metric delivery path.
- Provider-neutral traces are tested in memory but have no exporter, trace
  store, sampler, or access/retention policy.
- Security decisions do not yet emit a named security-record stream.
- Audit events have no durable, protected recorder or store.
- WAF request logging remains intentionally deferred because raw web-request
  evidence needs its own redaction, access, and retention policy.

This is why “CloudWatch exists” is not the same as “observability is complete.”
The target can show that a container was unhealthy or returned 5xx responses.
It cannot yet answer every product-level question, such as which approved
export job failed at which stage with what safe error classification.

### Misconception check

“If we add a CloudWatch SDK to `platform/observability`, every problem is
solved.”

No. That would couple generic platform code to one provider and still leave
record profiles, metric-cardinality rules, trace sampling, retention, access,
audit integrity, and security-record policy unresolved. The target already
shows a better first pattern for plain logs: keep the process provider-neutral
and let the runtime environment collect stdout.

### Study question

Why is an ALB `5xx` alarm useful but insufficient for an invoice-export
investigation?

It can show a damaging pattern—targets are returning server errors—but it has
no knowledge of the business capability, its safe target reference, the queue
message, or the bounded failure classification. The relevant application log,
trace, audit event, or security signal must answer those separate questions.

### Live target check

After renewing the `kanbien-dev` SSO session, a read-only inspection confirmed
that the target log group has 14-day retention and a recent ECS log-stream
event, the platform-shell service has one desired and one running task, and
the SNS email subscription is confirmed. The two currently implemented ALB
alarms are both `OK`.

The same inspection revealed a useful readiness discrepancy: the target
profile requires five alarms, but both the CloudFormation source and live AWS
currently contain only the two ALB alarms. The missing three cover ECS
running-count mismatch, high CPU, and high memory. They remain required rather
than being silently removed from the profile. The staging deploy-readiness
manifest now records that blocking gap and the reduced operational-proof gap.

Planning triage: the platform implementation plan does not change because
this is target-specific evidence. The staging deploy-readiness manifest owns
the evidence and missing-infrastructure alarm work. No AWS state was changed.

## 69. Provider-Neutral Ports: One Word, Three Different Jobs

### A port is a socket, not a cloud service

In this architecture, a **port** is a small interface owned by Core or the
platform that describes an effect the platform needs. It deliberately says
nothing about AWS, CloudWatch, a vendor SDK, credentials, network addresses,
or billing.

Think of a wall socket. The building defines the socket; a lamp, charger, or
appliance supplies a compatible plug. Likewise, the platform defines the
observability port; a no-op implementation, test fake, ECS stdout collector,
or future AWS adapter can supply the implementation.

```text
server or worker
    │
    ├─ Logger.write(safe record) ──> stdout implementation ──> ECS awslogs
    │
    ├─ Metrics.record(bounded point) ──> no-op or future metrics adapter
    │
    └─ Tracer.startSpan/end(span) ──> no-op/test fake or future trace adapter
```

The vertical arrows are intentionally different. “Observability” is an
umbrella term, but a log line, a metric point, and a trace span have different
data shapes, retention needs, costs, query patterns, and failure modes.

### The three current ports

| Port | What platform code asks for | Why it has its own shape |
|---|---|---|
| `Logger` | Write one safe record with level, stable message, optional correlation, and fields. | Logs are discrete explanations for an operator or investigator. ECS can collect stdout records directly. |
| `Metrics` | Record one numeric point with a fixed name, kind, unit, time, and bounded labels. | Metrics are aggregated patterns. A label such as tenant, user, request, or trace would create unsafe/high-cardinality series, so Core rejects those labels. |
| `Tracer` | Start a named span, optionally beneath an internal parent, then end it with a bounded outcome. | Traces are timed execution trees. They need parent/child handling and later sampling/export policy, neither of which belongs in ordinary logging. |

`platform/observability` sits immediately before these ports. It normalises
and bounds fields, redacts unsafe values, turns request/job facts into safe
metric labels, and limits trace attributes. It is a safety bridge, not a cloud
client.

### Why one CloudWatch SDK would be the wrong first answer

It is tempting to give every platform concern a CloudWatch client. That makes
the generic platform know provider credentials and turns a later provider
change into a widespread code change. It also hides the real design questions:

- Which application metrics are worth paying to retain and alarm on?
- Which labels are small, stable, and non-sensitive?
- Which traces are sampled, who may search them, and how long may they live?
- What must never be sent to a normal operational system because it belongs in
  a protected audit or security-record path instead?

For ordinary logs, the ECS host already supplies a clean solution: the process
writes safe stdout and the target collects it. A future provider adapter would
be appropriate only when a port needs a delivery mechanism the host cannot
provide—for example, a deliberate metrics exporter or trace exporter. Its
provider-specific home would be under
`platform/adapters/aws/observability/cloudwatch/`, while the generic platform
continues to depend only on the port.

### Misconception check

“A no-op implementation means the platform has no observability.”

No. It means a target can deliberately run without one optional delivery path
while the server and worker behaviour stays correct. The target can still use
stdout logging and native AWS health signals. A no-op is safer than making a
request fail because an optional telemetry service is unavailable. Required
audit or security evidence needs a different, durable design; it must not
silently become no-op telemetry.

### Study question

Why may `tenant_id` be suitable for an authorised audit search but unsafe as a
shared metric label?

An audit search is an authorised lookup over discrete evidence for a particular
tenant. A metric system creates a separate time series for each label
combination; tenant IDs create an unbounded number of globally visible series
and can leak or destabilise the monitoring system. The information need is
real, but the record type and access boundary must match it.

Planning triage: no generic platform plan change is needed. These ports and
their safety boundaries already exist in Core, platform observability, and the
target-direction plan. The target-specific missing ECS alarms are recorded in
the staging deploy-readiness manifest. A future metrics or trace adapter still
requires a bounded use case, provider/retention/access decisions, and its own
implementation slice.

## 70. Alarm Definitions: Turning a Concern into an Operable Rule

### An alarm is a small decision system

It is tempting to define an alarm as a name plus a number:

> “Tell me when CPU is above 80%.”

That sentence leaves out most of the decisions that determine whether the
alarm is useful or noisy. A complete alarm definition answers eight questions:

| Question | Example in the platform-shell target | Why it matters |
| --- | --- | --- |
| What signal? | `AWS/ECS` `CPUUtilization` | The alarm must name a real provider metric. |
| Which exact resource? | `ClusterName` plus `ServiceName` dimensions | Without dimensions, a shared cluster's unrelated workload could trigger it. |
| What is bad? | Average CPU is at least 80% | This turns a number into an explicit failure condition. |
| For how long? | Three of five one-minute periods | A short spike should not normally wake an operator. |
| What if there is no data? | `notBreaching` for CPU/memory; `breaching` for running count | Missing data has a meaning that must be chosen per signal. |
| Who is notified? | The foundation-owned SNS alarm topic | A CloudWatch state change is not helpful unless it reaches an owned notification route. |
| Who owns the resource? | Foundation owns shared ALB alarms; service owns service-specific ECS alarms | The resource must live with the thing that supplies its dimensions and lifecycle. |
| How is it handled? | A named runbook | The operator needs a safe first action, not only a red dashboard. |

### Why the running-count alarm has a prerequisite

The desired rule is:

```text
if the service is meant to run 1 task
and RunningTaskCount is below 1 for two minutes
then raise a critical alarm
```

The `RunningTaskCount` metric comes from `ECS/ContainerInsights`, not the
ordinary free Fargate CPU/memory metrics. The existing shared ECS cluster must
therefore use enhanced Container Insights, and CloudWatch must already have
seen a metric for this particular cluster and service. Otherwise the alarm can
be perfectly written yet have nothing reliable to evaluate.

The repository now makes this explicit in two layers:

```text
target profile
  └─ says enhanced telemetry and the metric are prerequisites
       ↓
read-only deployment preflight
  └─ checks cluster setting and metric presence
       ↓
CloudFormation service stack
  └─ creates the running-count, CPU, and memory alarms
```

That is a useful general pattern: a declaration says what must be true; a
preflight proves the external prerequisite; infrastructure applies the rule.

### Why two stacks own different alarms

The shared foundation stack already owns the ALB target group and the SNS
topic, so it owns the “no healthy target” and “target 5xx” alarms. The service
stack owns the ECS service and its `ClusterName`/`ServiceName` dimensions, so
it owns the running-task, CPU, and memory alarms.

This does **not** mean there are two separate alarm policies. The structured
five-alarm policy lives in the staging target profile. The static infrastructure
check compares each profile definition with its CloudFormation resource,
including metric, dimensions, threshold, evaluation window, missing-data rule,
notification path, tags, and runbook. That prevents the profile saying one
thing while the deployed template quietly says another.

The repository now also has a reusable **Platform Target Alerting Policy**
standard. It says that every future product target puts its complete alarm
catalogue in its own `target-profile.yml`; the target index only links to that
catalogue, its infrastructure implementation, and its runbook. This is a
useful anti-drift pattern: one authoritative policy, with a quick human map to
find it. The static target check verifies both the detailed policy-to-template
match and the link back to the governing standard.

### Misconception check

“If CloudFormation accepts an alarm resource, the alarm is production-ready.”

No. CloudFormation validates the resource shape, not whether a source metric
exists, the execution role may create it, notification reaches an operator, or
the threshold is operationally useful. Those are separate properties. This
slice adds the preflight and narrowly scoped IAM source declarations, but AWS
has not yet been changed; live verification and delivery proof remain blocking
readiness work.

### Study question

Why should the CPU alarm treat missing data as `notBreaching`, while the
running-task alarm treats it as `breaching`?

CPU has no meaningful high-use datapoint when the task is not running, so
treating absence as high CPU creates misleading noise. A missing running-task
signal, after enhanced telemetry has been confirmed as a prerequisite, can mean
the service or telemetry is unhealthy; it should draw attention rather than
silently count as healthy.

Planning triage: this is target-specific observability work. The structured
target profile, CloudFormation sources, deployment preflight, runbook, staging
readiness manifest, AWS deployment plan, alert-policy standard, and target
catalogue index are updated together. The generic platform-observability plan
does not change: no provider SDK or application metric/trace exporter was
added to platform code.

## 71. Capability Observability Profiles: One Capability, Four Different Needs

### The missing declaration layer

The platform already has safe helpers for operational logs, request/job
metrics, and trace spans. What it does **not** yet have is a declarative
`CapabilityObservabilityProfile` that tells the platform which of those helpers
a particular route or job should use, and why.

That distinction matters. A helper answers, “how do I safely write a metric?”
A profile answers, “does this capability need that metric at all, and which
safe facts are allowed?” The profile is a design-time declaration; it is not a
new record emitted for every request.

```text
capability declaration
  └─ observability profile says what may be measured or traced
       ↓
platform observability helpers normalise and emit safe operational facts
       ↓
target composition selects collection, retention, access, dashboards, and alarms
       ↓
provider receives only the selected, bounded telemetry
```

### One action can create several kinds of evidence

Imagine a future `invoice.download` capability. It is only an illustration;
this repository does not yet contain that business capability.

| Need | Example fact | Why it exists | What it must not contain |
| --- | --- | --- | --- |
| Operational log | `capability=invoice.download`, `outcome=ok`, `latency_ms=180` | Diagnose one request's technical behaviour. | Invoice contents, customer name, download URL, access token. |
| Metric | request duration with route/method/outcome labels | See aggregate rate, latency, and failure trends. | Tenant, user, invoice ID, request ID, raw URL. |
| Trace span | a bounded timing segment for the route and downstream storage call | See where time was spent along one execution path. | Request body, headers, token, customer data, raw provider response. |
| Audit event | authorised actor performed an invoice download on a bounded invoice reference | Accountability and later authorised investigation. | The document itself or broad diagnostic payload. |

The first three are operational observability. The fourth is durable business
and security evidence, with different retention and access rules. A single
free-form “log everything” call is not a substitute for this separation.

### What a future capability profile should decide

A profile should name only what the platform needs to handle telemetry safely:

1. **Capability identity** — a stable name such as `invoice.download`, not a
   URL or user-provided label.
2. **Operational log facts** — a small allowlist such as outcome, bounded error
   class, latency, retry count, and deployment version.
3. **Metrics** — aggregate measurements and low-cardinality labels. For a
   request, method, stable route name, outcome, and status are reasonable;
   tenant and user are not.
4. **Tracing** — whether a span is useful, its stable span name, and the small
   attribute allowlist. A trace explains timing and causal flow; it is not the
   durable audit trail.
5. **Audit/security handoff** — whether successful action, denial, or another
   security decision needs separately governed durable evidence.
6. **Failure behaviour** — observability failure normally must not fail a user
   request, while required audit/security evidence may need a stricter,
   separately designed path.

### Why cardinality is the trap

Metric systems make a separate time series for every unique combination of
labels. A few good labels stay small:

```text
method: GET | POST
outcome: ok | rejected | error
route: invoice.download | invoice.list
```

One bad label grows with your customers:

```text
tenant_id: tenant-a | tenant-b | tenant-c | ...
invoice_id: invoice-1 | invoice-2 | invoice-3 | ...
```

The second form increases cost and query difficulty, can exhaust metric
limits, and exposes identifiers to a broadly accessible operational system.
That is why the current `recordPlatformRequestMetric` helper records a stable
route and bounded result fields, while logging and audit paths handle different
facts under different controls.

### What already exists, and what remains future work

| Existing now | Still to design and implement |
| --- | --- |
| `normalization.ts` bounds unknown log/trace values and redacts known sensitive fields. | Direct server and worker consumption of resolved capability profiles. |
| `platform/contracts/src/observability-profiles.ts` declares provider-neutral profiles, safe field allowlists, NFR classes, and latency intervals. | Target-selected metric and trace export adapters, retention, access controls, and dashboards. |
| Runtime and test registries require every route/job to adopt a registered profile or use a bounded, justified opt-out. | Capability-specific sampling and trace propagation policy. |
| `metrics.ts` records provider-neutral request, job, and health metric points. | Per-capability profile-consumption tests and an explicit opt-out review workflow for real apps. |
| `tracing.ts` creates bounded provider-neutral spans and falls back safely when tracing is unavailable. | A selected histogram implementation and target-governed percentile, SLO, error-budget, and alert policy. |

### Misconception check

“If I add an audit event, I do not need a metric.”

No. An audit event may tell an authorised investigator that one specific
download happened. It does not efficiently answer, “are downloads failing more
often today than yesterday?” A metric can answer that aggregate health question
without carrying a person, tenant, or document identifier.

### Study question

Why is a correlation ID acceptable in a safe operational log but normally a
poor metric label?

It lets an operator find the few records for one execution. As a metric label,
it creates a new time series for nearly every request, which is expensive,
unsearchable at aggregate level, and needlessly exposes a request identifier.

Planning triage: the capability profile is a platform-contract design slice,
not an AWS adapter decision. It should be designed and tested before a product
app adopts it; selecting a metrics/tracing exporter comes later through target
configuration and provider adapters.

## 72. Where a Capability Observability Profile Belongs

### Start with the question the profile answers

A route or job needs to declare, “these are my approved operational
measurements.” That makes it an **app-facing declaration**, just like its
route name, authentication requirement, tenant requirement, or input
validator. It is not generic metric vocabulary and it is not a cloud-delivery
implementation.

The future ownership shape is:

```text
packages/core/monitoring
  └─ universal vocabulary: metric kinds, units, safe label rules, tracer port
       ↓
platform/contracts/observability
  └─ app-facing profile declaration and explicit opt-out vocabulary
       ↓
platform/runtime/registry
  └─ complete mounted view: profiles, routes, jobs, and cross-reference checks
       ↓
platform/server and platform/workers
  └─ use the resolved profile with safe platform-observability helpers
       ↓
target configuration and adapters
  └─ choose exporter, retention, access, dashboards, and alarms
```

### Why it does not belong in Core

Core should be able to say what a metric is and which labels are unsafe. It
cannot know whether a future `billing.invoice.download` route exists or whether
that route is important enough to measure. That is product/app meaning, so an
app-facing contract is the right boundary.

### Why it does not belong in `platform/observability`

`platform/observability` owns the safe machinery: normalise a field, write a
safe log, record a metric, start/end a span. If it also decided which app
capabilities need telemetry, it would need advance knowledge of every product
app and become a hidden policy owner.

Think of it as the difference between a camera and a filming plan. The camera
knows how to capture an image; the plan decides what is worth filming.

### The declaration and reference pattern

The recommended shape is a **named registered profile** plus a reference from
each route or job. An app can reuse one profile where several capabilities
genuinely have the same safe operational needs, but the reference remains
visible beside each capability.

```text
Billing app mount
  ├─ registers profile: billing.read-operation
  ├─ registers route: billing.invoice.list → billing.read-operation
  └─ registers job: billing.invoice.export → explicit different profile
```

This is preferable to silently giving every route the same telemetry, because
read operations, exports, writes, and long-running jobs have different risks
and useful measurements. It is also preferable to copying a full profile into
every route, which would make later safe changes repetitive and inconsistent.

An explicit opt-out remains possible, but it needs a short reason. For example,
a platform-internal route with no product behaviour might have no meaningful
application metric. “We forgot” is not an opt-out; a registry should reject a
route or job that has neither a valid profile reference nor a reasoned opt-out.

### Why the complete registry must decide

This is the same principle as permission validation.

```text
Route: billing.invoice.list → profile billing.read-operation
Profile: billing.read-operation → registered elsewhere during app mount
```

The route can check that its reference looks like a valid name. It cannot know
on its own whether that profile was registered, whether another profile reused
the same name, or whether every other route/job made a deliberate choice. Only
the runtime registry sees the complete mounted application.

The existing `platform/runtime` registry already uses this pattern for route
permissions: it gathers declarations during app mount, then validates their
relationships before returning a mounted runtime. Observability-profile
validation should happen at the same startup boundary, before the server or
worker accepts work.

### The checks a future registry needs

| Check | Failure it prevents |
| --- | --- |
| Profile ID is unique and belongs to its mounting app namespace. | Two apps accidentally redefine the same operational policy. |
| Every route/job has a profile reference or reasoned opt-out. | New capabilities quietly become invisible. |
| Every reference resolves to a registered profile. | A typo leaves a route with undocumented telemetry. |
| Profile labels and allowed facts satisfy Core safety limits. | Tenant/user/request data leaks into shared metrics or traces. |
| Server/worker consume only the resolved profile. | A handler bypasses the capability policy with an ad hoc telemetry call. |
| No contracts import a provider SDK. | A CloudWatch or tracing vendor becomes a hidden app dependency. |

### Misconception check

“If the route contains its telemetry code, we do not need a registry check.”

No. The route can prove only what it wrote nearby. It cannot prove that the
profile it references exists elsewhere, has not been duplicated, follows the
same safety rules as a job profile, or that all other capabilities made a
deliberate choice. The registry turns separate local declarations into one
system-wide guarantee.

### Study question

Why is a named profile plus a visible route/job reference better than placing a
large inline metric-and-tracing object directly in every route declaration?

It provides reuse and one place to improve a common safe policy, while the
visible reference keeps each capability's observability choice reviewable.
The full registry can then validate that every reference resolves and every
capability is covered or deliberately opted out.

Planning triage: this is now recorded as a planned platform-contract and
runtime-registry slice in the platform-runtime implementation plan. No
TypeScript contract, telemetry behaviour, provider adapter, or AWS resource is
changed by the lesson.

## 73. Selecting the First Bounded Telemetry Proof

### Choose a narrow real path, not a generic promise

The first useful telemetry proof is the existing protected smoke route:

```text
route name: platform-smoke.echo
app-relative path: /smoke/:id
```

It is a good teaching and test target because it crosses authentication,
authorisation, routing, request timing, logging, metrics, and tracing without
containing business records. Its `:id` parameter is especially useful: it
looks tempting to record, but is exactly the kind of resource/request value
that must not become a shared metric label or general trace attribute.

### What we want to learn from it

The existing platform server already creates a provider-neutral request timer
called `platform.server.request` and a span called `platform.server.request`.
For this route, the useful safe operational facts are:

| Safe fact | Why it is useful |
| --- | --- |
| HTTP method | Separates different operation kinds without identifying a person. |
| Stable route name: `platform-smoke.echo` | Identifies the declared capability, not a user-provided URL. |
| HTTP status and outcome | Shows whether requests succeed, are rejected, or fail. |
| Latency | Shows how long the platform took to return a response. |
| Bounded error class | Helps group technical failures without exporting an error payload. |

The following must stay out of ordinary metrics and general trace attributes:

| Unsafe fact | Why it stays out |
| --- | --- |
| `:id` value | It is a resource identifier and can grow without limit. |
| Tenant, principal, or email | Identifies a customer or person and creates high-cardinality series. |
| Request/correlation/trace ID | Useful for finding individual logs, but nearly unique per request. |
| Headers, body, response body | May contain credentials, tokens, personal data, or business content. |

### The complete local proof

Before selecting an exporter, a local test should prove four things:

```text
request arrives at /smoke/:id
  → server records one safe request metric for platform-smoke.echo
  → server starts and ends one safe request span
  → no metric or trace attribute contains the actual :id or identity facts
  → tracer/metric failure does not change the HTTP response
```

This proof demonstrates correct platform behaviour. It does **not** prove that
CloudWatch, OpenTelemetry, or another provider received the data. The current
Core metrics and tracer ports can use deterministic in-memory test doubles;
the ECS target currently has safe stdout collection and infrastructure alarms,
but no chosen application-metrics or trace exporter.

### Why exporter selection is a later decision

An exporter is an operational and cost decision, not a TypeScript convenience.
Before a target sends these metrics or traces to a real provider, it must decide:

- who may search them;
- how long they are retained;
- whether traces are sampled and at what rate;
- what happens during provider failure or backpressure;
- what data-residency and encryption boundary applies;
- what dashboards or alerts use the resulting data; and
- the cost limit and owner.

Choosing an SDK first would reverse the design: it would make the available
vendor fields decide what the product records. The safe profile and local proof
must come first.

### Misconception check

“Because `platform.server.request` is already emitted for every request, the
smoke route has finished observability.”

Not yet. It has local provider-neutral instrumentation. It still needs the
future capability-profile declaration/registry coverage, local assertions that
the selected facts are safe, and—only when a real operational need is approved—a
target-selected delivery adapter and operating model.

### Study question

Why is `platform-smoke.echo` a better first proof than a future invoice export?

It exercises the same platform boundary while avoiding business data, product
meaning, persistence, and retention decisions that do not yet exist. It gives
us a small test of the telemetry rules before they are trusted with sensitive
capabilities.

Planning triage: the selected smoke-route proof and its forbidden facts are
recorded in the platform-runtime implementation plan. No exporter, provider
SDK, target configuration, dashboard, alarm, or AWS resource is selected by
this lesson.

## 74. Testing Telemetry with In-Memory Recorders

### A recorder is a notebook, not a cloud simulation

The first local proof does not need CloudWatch, OpenTelemetry, a network, or
AWS credentials. It replaces the *port* that would send telemetry with a small
in-memory recorder that keeps entries in an array for the test to inspect.

```text
production-shaped path                  local proof path

server → Metrics port → provider        server → Metrics port → array of points
server → Tracer port  → provider        server → Tracer port  → array of spans
```

The question is deliberately narrow: *did the platform try to emit exactly the
safe operational facts we approved?* It is not: *did a cloud provider store
them?* The latter belongs to a later adapter and deployment proof.

Two repository helpers make the local question deterministic:

| Helper | What it records | Why it is useful in a test |
| --- | --- | --- |
| `createPlatformTestMetrics()` | Every `MetricPoint` passed to its `record` method. | The test can inspect name, kind, unit, value, timestamp, and labels without a provider. |
| `createInMemoryTracer()` | Every span's stable test context, start attributes, and first end outcome/attributes. | The test can prove a span starts and completes with only approved attributes. |

The tracer assigns predictable test-only contexts such as `trace-1` and
`span-1`. That makes assertions repeatable. A real tracing adapter would use
its own trace context; the fake is not pretending to be a tracing backend.

### Walk through one smoke request

Imagine a successfully authorised request for `/smoke/record-479`. The server
matches the route declaration and deliberately changes the unbounded concrete
path into the stable route name `platform-smoke.echo`.

```text
incoming path: /smoke/record-479
                    ↓ route matching
declared route: platform-smoke.echo
                    ↓ safe request instrumentation
metric and span use platform-smoke.echo — never record-479
```

With the fixed test clock, the expected local metric record is conceptually:

| Part | Expected value | Reason |
| --- | --- | --- |
| Name | `platform.server.request` | A stable platform-owned measurement. |
| Kind and unit | timer / milliseconds | This measures duration rather than a business count. |
| Value | `0` in a fixed-clock test | The test proves shape, not wall-clock performance. |
| `method` label | `GET` | A small known set. |
| `route` label | `platform-smoke.echo` | Stable capability identity, not the raw path. |
| `status` and `outcome` labels | `200` and `ok` | Small result vocabulary for aggregate health. |
| Absent labels | `record-479`, tenant, principal, request ID, correlation ID | They are identifiers or high-cardinality/sensitive context. |

The corresponding request span begins with `method=GET`. When the server has
the response, it ends the span as `succeeded` with the method, stable route,
status, and latency. The **span context** itself necessarily has a trace ID
and span ID so tracing can connect work; the policy is that those IDs are not
copied into arbitrary attributes or metric labels.

### What the test should assert

Think of this as a small MOT-style inspection for telemetry. It should look at
both the things that must exist and the things that must not exist.

1. Send a real in-memory request through the mounted smoke server, with the
   authentication required to reach the route.
2. Assert the HTTP response is still the expected successful result. This
   proves the test exercised the real route rather than manually calling a
   metrics helper.
3. Find exactly the request metric for `platform-smoke.echo`; assert its timer
   shape and each approved low-cardinality label.
4. Find exactly the corresponding `platform.server.request` span; assert its
   start attributes, end outcome, and end attributes.
5. Assert the actual path parameter and identity/request facts occur in
   neither metric labels nor span attributes. Checking only the expected values
   is insufficient: a later accidental extra field could otherwise slip in.
6. Exercise a rejection or failure separately, then assert its distinct bounded
   outcome/error class rather than leaking the error message or payload.

The current server-runtime test already provides the beginnings of this proof:
it captures metrics with `createPlatformTestMetrics()`, captures spans with
`createInMemoryTracer()`, checks a completed request span, and checks that
request/correlation IDs are absent from end attributes. The future smoke-route
proof should make the route-specific metric and the forbidden `:id` assertion
equally explicit.

### An important finding: safe data is not the same as safe failure behaviour

It would be easy to read “safe observability helpers” as meaning every possible
failure is already harmless. It does not mean that yet.

| Path today | What happens if its injected provider port throws | Status |
| --- | --- | --- |
| Tracing | `startPlatformTraceSpan` uses a no-op span and `endPlatformTraceSpan` catches an end failure. | Already failure-isolated. |
| Metrics | `recordPlatformMetric` directly calls `metrics.record`. | Hardening still required. |
| Ordinary operational logs | `writePlatformLog` directly calls `logger.write`. | Hardening still required. |

This is why a negative test is valuable. A test metric sink that throws should
not make an already-completed `200` route become a `500`; a failing ordinary
log sink should not do so either. At present, those tests would expose a real
gap rather than pass. We have recorded the requirement in the platform plan
instead of quietly claiming that a test recorder proves resilience.

This does **not** mean “swallow every security problem.” Ordinary diagnostics,
metrics, and traces are optional operational signals. Required audit or
security-record delivery has its own explicitly designed durability and failure
policy, and must not be hidden behind the optional-observability fallback.

### Misconception check

“If an in-memory test sees a metric, observability is production-ready.”

No. It proves the application-side emission shape, redaction boundary, and
local behaviour. A production-ready target still needs an approved exporter,
access control, retention, residency, sampling, backpressure/failure policy,
dashboards, alarms, and delivery evidence.

### Study question

Why does the test need to assert that `record-479` is *absent*, rather than
only asserting that the route label equals `platform-smoke.echo`?

Because both facts could exist at once. An accidental extra label or trace
attribute can create a high-cardinality data leak even when the correct stable
route name is also present.

Planning triage: this lesson identifies a platform hardening requirement. It
does not change telemetry code, select a provider, deploy an adapter, or alter
AWS resources.

## 75. Locking the Main Observability Names

### The names we have now fixed

We have now made the main provider-neutral observability vocabulary a public
`platform/contracts` type surface. This is deliberately a small dictionary,
not a command to emit every field for every capability.

| Semantic fact | Canonical emitted field | Examples | What it must not be confused with |
| --- | --- | --- | --- |
| Capability | `capability` | `billing.invoice.export` | A raw URL, route parameter, provider operation, or metric name. |
| Business action | `action` | `create`, `read`, `export`, `approve` | An HTTP method such as `POST`. |
| Actor category | `actor_type` | `user`, `service`, `system`, `anonymous` | An actor ID, email, or identity claim. |
| Interaction source | `interaction_source` | `web`, `chat`, `voice`, `api` | The process that later performed the work. |
| Execution context | `execution_context` | `server`, `worker`, `scheduler`, `cli` | The interaction channel. |
| HTTP result | `http_method`, `http_status_code` | `GET`, `200` | A business action or job delivery state. |
| Worker delivery | `job_delivery_disposition` | `succeeded`, `retry_scheduled`, `dead_lettered` | The business operation's logical outcome. |
| Logical result | `outcome` | `accepted`, `succeeded`, `denied`, `rejected`, `failed`, `cancelled`, `timed_out` | A raw error message or HTTP status. |
| Failure classification | `error_class` | A bounded stable platform/application code | Stack trace, provider payload, or free-text error. |

The external field names use lower snake case consistently. TypeScript uses
readable camel-case property names internally and exposes one mapping to those
emitted names. That gives us a stable schema without tying it to CloudWatch,
OpenTelemetry, or any other provider's naming system.

### Three distinctions worth remembering

```text
voice request → worker execution → invoice export
     source          context          capability/action
```

`voice` says how the request started. `worker` says where the later work ran.
`export` says what the business capability means. All three can be true at once
and none can safely substitute for another.

Likewise, a worker can have `outcome=failed` and
`job_delivery_disposition=retry_scheduled`. The first describes the attempted
work; the second describes what the delivery mechanism will do next. Combining
them into a vague `status=retry` loses that distinction.

### What this does not yet do

The vocabulary does not retrospectively rename the existing generic request
metric fields, automatically create a profile for a registration, select a
provider, alter audit storage, or make server and worker delivery consume a
resolved profile. Route/job coverage is now mandatory through either a
registered profile or a bounded, justified opt-out. The next runtime and
adapter slices must turn that protected declaration into safe emitted evidence.

### Study question

Why can a voice-initiated invoice export truthfully have
`interaction_source=voice`, `execution_context=worker`, and `action=export`?

Because each field answers a different question: how the work began, where it
ran, and what meaningful business operation was attempted.

Planning triage: the provider-neutral type vocabulary is now implemented in
`platform/contracts`. That vocabulary slice itself did not select a telemetry
exporter, provider, or AWS resource; the later profile slice added route/job
coverage enforcement.

## 76. Capability Profiles Measure Intervals; NFR Policies Set Targets

### What we have now implemented

`platform/contracts/src/observability-profiles.ts` is now the declaration card
for each capability's ordinary operational evidence. An app registers one or
more named profiles while it mounts. Every route and job must either reference
one of those profiles or provide a controlled opt-out reason and a short
justification. The complete runtime registry sees all three lists—profiles,
routes, and jobs—so it can reject an unknown profile or a duplicate before the
process is ready.

The smoke app proves both shapes:

| Registration | Profile class | Measured interval | Why it is truthful |
| --- | --- | --- | --- |
| `platform-smoke.echo` route | `interactive_read` | `request_response_latency` | The route does its meaningful work before it sends its response. |
| `platform-smoke.rebuild` job | `async_completion` | `job_execution_latency` | The worker's handler performs the meaningful background work. |

### A profile does not contain a promise

This distinction is the important one:

```text
Profile: “measure request/response latency for this interactive read.”
NFR policy: “95% must complete within X, and 99% within Y, over window Z.”
Alert policy: “page or notify when the error budget burns at this rate.”
```

Putting `X`, `Y`, and `Z` in every route would create contradictory targets and
make a policy change require many feature edits. The profile therefore names a
controlled NFR class and a specific start-to-finish interval. A central,
target-governed NFR/SLO policy will later own the numerical thresholds,
eligible requests, time window, error budget, owner, review date, and response
when the target is missed.

### Why intervals matter

“Export took five minutes” is not enough information to improve it. It could
mean that the API was slow, the export waited in a queue, or the worker spent
time generating the file. The contract makes those separate measurements
available:

| Interval | Starts | Ends | Diagnoses |
| --- | --- | --- | --- |
| Request/response | Server receives request | Response completes | Slow interactive API handling. |
| Queue wait | Job is enqueued | Worker starts it | Insufficient worker capacity or queue contention. |
| Job execution | Worker starts handler | Handler completes | Slow application or dependency work. |
| End-to-end completion | Work is accepted | Declared final outcome | The whole customer-visible asynchronous journey. |
| Health check | Probe starts | Probe completes | A dependency or readiness check becoming slow. |

An asynchronous export may need all three middle intervals. That is not
over-measuring: each one answers a different operational question.

### What p95 and p99 still need

The Core monitoring contract can describe a histogram, but the current generic
platform timer point does not by itself prove that a selected metrics backend
retains a latency distribution, uses suitable buckets, or calculates reliable
percentiles. We must not claim a p95/p99 SLO until a provider adapter does
that work and its target policy identifies the aggregation and retained data.

The profile slice is still valuable now. It prevents an app from silently
inventing an action, metric dimension, measurement interval, or unregistered
profile while the later adapter and target-policy work is deliberately staged.

### Misconception check

“A route can check that its profile exists when it is declared.”

No. A profile may be registered later in the same mount, and a duplicate may
appear in a different app. Only the complete process registry can check the
relationship correctly. This is the same whole-catalogue reasoning we used for
permission declarations.

### Study question

Why should an export's API acceptance and its worker completion not share one
`request_response_latency` target?

Because the API can correctly acknowledge queued work quickly while the worker
has not yet begun or completed the export. One metric would hide either queue
delay or worker execution time.

Planning triage: the profile contract, registry enforcement, smoke proof, and
NFR-class/interval vocabulary are implemented. Percentile aggregation,
numerical SLOs, error budgets, dashboarding, alerting, retention, and provider
selection remain intentionally deferred to the target-policy and adapter slices.

## 77. Data Classification Chooses Requirements, Not Telemetry Payloads

### The four things we must not merge together

An attribute classification, a business capability, an operational profile,
and an evidence record each answer a different question:

| Thing | Question it answers | Example |
| --- | --- | --- |
| Attribute classification | How carefully must this data be handled? | A client email is `personal-data`; an amount is `financial-data`. |
| Capability | What meaningful operation is being attempted? | `invoice.export` |
| Operational profile | Which safe diagnostic facts may the runtime emit? | Capability, action, outcome, latency, bounded error class. |
| Audit/security record | What durable or security-relevant evidence must be preserved? | An authorised accountant exported invoices. |

The fact that an attribute is classified does **not** make it suitable for a
log, metric, or trace. Usually the opposite is true: a stricter classification
means fewer operational facts may be emitted, while accountability controls
become stronger.

### The policy-evaluation picture

```text
future entity/attribute classification
  + capability action and declared data access
  + adopted product baseline
  + tenant restriction
                ↓
     resolved data-handling requirements
                ↓
authorisation / approval / audit / security signal /
operational profile / retention / residency
```

`packages/core/security/classification.ts` already owns the reusable nouns:
data sensitivity and sensitive-value kind. It is not an entity model; it must
not learn about an `Invoice`, `clientEmail`, or product-specific export rule.
Those belong in a future app/entity schema and capability declaration. Core's
generic policy-decision contract provides a future seam for evaluating the
combined facts without choosing an identity provider, database, telemetry
service, or tenant-policy store.

### Worked example

Imagine a future invoice entity:

```text
invoice reference  → internal business data
amount             → financial data, confidential handling
client email       → personal data, confidential handling
attachment         → inherited or explicitly declared classification
```

An accountant invokes `invoice.export`. The capability declares that it can
process the relevant financial and personal classifications. The policy result
might require a durable audit event, an export-specific authorisation check,
an approved retention/residency path, and perhaps a security signal. Its
ordinary operational profile may still emit only this:

```text
capability=invoice.export
action=export
outcome=succeeded
execution_context=worker
```

It must not add the invoice number, amount, client email, file contents, or a
signed download URL merely because the export was important enough to audit.

### The strictest applicable rule wins

An entity can have a default classification and an attribute can declare a
stricter override. A capability can touch several attributes. The policy must
apply the strictest relevant treatment rather than averaging them into a weaker
one. A tenant may tighten the adopted product baseline—for example by requiring
longer audit retention or stricter residency—but must not silently weaken it.

### Misconception check

“We need a `financial` telemetry profile for financial fields.”

No. The operational profile is an allowlist of safe facts about program
behaviour. Classification determines whether audit, security, retention,
approval, residency, and access controls apply. It rarely permits the original
financial or personal value to enter telemetry.

### Study question

Why might a display-name update and an invoice export both use the action
`update` or `export`, yet require very different evidence and handling?

Because the action tells us what happened, while the affected data
classifications, actor scope, product baseline, and tenant restrictions tell us
the risk and therefore the required controls.

Planning triage: Core already has the classification and generic policy
vocabulary. The future app/entity schema, capability data-access declaration,
resolved-policy evaluator, persistence representation, and generated harness
validators remain intentionally deferred until the first real entity consumer.

## 78. A Bounded DynamoDB Reference Is Not a Permanent Database Decision

### Why this matters now

The platform-smoke app should prove more than a server can start. It should
eventually prove that a harmless state change, its required bounded evidence,
and an outgoing outbox message cannot become separated when a later delivery
step fails. That needs a real transaction-capable store, even though we are
not ready to choose the Entity Builder's general persistence approach.

The chosen first reference is DynamoDB on-demand in the EU target. The choice
fits a low-volume, cost-aware operational proof. It is deliberately narrow:
it applies only to a non-business smoke work item and its outbox/evidence
records. It does not decide where future entities, customer data, medical
data, documents, or reporting models live.

### What the future proof will contain

```text
one DynamoDB transaction
    |
    +-- harmless smoke work-item state
    +-- bounded audit-evidence record
    +-- pending outbox record
```

All three writes either succeed together or fail together. A later platform
relay will take the pending outbox record to a queue or event destination. We
have *not* selected that destination yet; choosing DynamoDB does not silently
mean SQS, EventBridge, or another service is already approved.

### What exists today

Core currently supplies portable persistence and audit vocabulary, including a
transaction seam and an `AuditRecorder` port. The repository does not yet have
a DynamoDB persistence/outbox adapter, an outbox table, a relay, a queue/event
provider, or a deployed durability proof. The only existing DynamoDB adapter
is for shared rate limiting, which is a different responsibility.

### Misconception check

“We chose DynamoDB, so the future Entity Builder must use DynamoDB.”

No. We chose a low-cost provider for one operational proof. Future real entity
requirements—relationships, flexible reporting/search, constraints,
migrations, transaction shape, measured cost, and operating evidence—will
trigger a separate persistence decision. A later relational adapter is an
additive migration path, not a reason to rewrite history or claim the smoke
proof was a product data model.

### Study question

Why is it useful to prove a state/outbox transaction with a harmless smoke
work item before designing an invoice, customer, or entity feature?

Because it proves the platform's failure and delivery mechanics without
accidentally making a temporary demo schema the permanent business model.

Planning triage: the bounded selection is recorded in the production-reference
baseline and platform-runtime plan. It introduces no AWS mutation, no empty
adapter package, and no change to the deferred entity-persistence boundary.

## 79. The Outbox Is Several Records, Not One Queue Write

### The five logical records

A durable smoke operation requires five logical records, although they do not
necessarily require five DynamoDB tables:

| Record | Purpose |
|---|---|
| Idempotency claim | Stops one client retry becoming two work items. |
| Smoke work item | Holds the harmless state being changed. |
| Audit evidence | Records the bounded accountable milestones. |
| Outbox record | Preserves the obligation to deliver a later message. |
| Worker processing record | Stops a duplicate delivery applying work twice. |

The first transaction atomically claims idempotency, creates the accepted work
item, writes acceptance evidence, and creates a pending outbox record. A relay
then leases the outbox record, sends a message to the selected transport, and
marks delivery only after confirmation. The worker separately leases and
processes the message. Its terminal work-item change, processing marker, and
terminal evidence must also share an atomic boundary.

### Idempotency protects a request, not every concurrency problem

An idempotency key is scoped to the verified caller, capability, and tenant
when applicable. A protected fingerprint distinguishes a genuine retry from
key reuse for different input. The raw key never enters ordinary telemetry.
Idempotency does not replace version checks for normal updates, state
transitions, authorisation, or business constraints.

### State and race protection

The harmless work-item lifecycle begins as:

```text
accepted → processing → completed
                     ↘ failed
```

Every transition has an allowed predecessor, expected version, owner, and
failure outcome. A relay or worker claim uses an expiring lease and an
increasing attempt/lease version. That fencing value stops a stale worker from
writing after another worker has taken over. We prefer a possible duplicate
delivery to lost work, then make the consumer duplicate-safe with its stable
outbox/message identity.

### Misconception check

“One transaction gives us exactly-once processing everywhere.”

No. The transaction protects one database decision. The external queue,
worker, and later integrations can fail independently. Effective one-time
business outcomes come from atomic state changes, conditional transitions,
idempotency, leases/fencing, bounded retries, and repair evidence together.

### Study question

Why must a worker's completion marker and its harmless state transition share
one transaction?

Otherwise a crash after changing state but before recording completion permits
a later duplicate delivery to apply the effect again.

## 80. Queue Delivery Policy Is Generic; SQS Is One Target Mapping

### The selected first transport

The first smoke outbox relay will use SQS Standard with a DLQ. It fits one
accepted work item becoming one worker job. It deliberately does not make
EventBridge, FIFO ordering, or product-event fan-out part of the initial
platform proof.

### The named short-work policy

`platform-short-idempotent-work.v1` requires at-least-once delivery,
idempotent consumers, no ordering assumption, a 30-second expected execution
budget, two-minute visibility, five total delivery attempts, bounded
exponential backoff with jitter, seven-day main retention, fourteen-day DLQ
retention, and manual review before any DLQ redrive.

These are target defaults for short safe-to-retry work, not universal settings
for long-running imports, integrations, payments, or future agent workflows.
Those need their own named policies.

### One configuration source, several consumers

```text
Generic delivery policy
    → target-owned SQS configuration
        → infrastructure resources and IAM
        → target composition references
        → validated AWS adapter
```

The generic policy owns the meaning: retry, execution budget, dead-letter
recovery, idempotency, ordering, retention, observability, and security.
Target configuration owns the SQS mapping: queue/DLQ resource references,
visibility, redrive count, retention, encryption, IAM, and provider alarms.
Platform invariants—such as bounded retries and duplicate-safe consumers—are
not optional configuration switches. No application should hardcode a queue
URL, SQS receipt handle, or independently adjustable delivery value.

### Study question

Why should a target profile, rather than an adapter source file, own a
two-minute visibility timeout?

Because it is an environment-specific operational decision that must stay
reviewable alongside queue resources, IAM, alarms, and rollback—not an
unreviewed provider constant hidden in code.

## 81. Worker Completion Is Not Queue Acknowledgement

### The worker's safe order

A queue message is a request to attempt work, not proof that work happened.
For the selected SQS proof, a worker must follow this order:

```text
receive message
    → conditionally claim durable processing
    → perform bounded work
    → atomically record terminal outcome and safe evidence
    → acknowledge/delete the queue message
```

SQS temporarily hides a received message from other workers for its visibility
period. That is a lease, not permanent ownership. If the worker crashes or the
lease expires, SQS can deliver the message again. The durable processing claim,
stable outbox/message identity, and fencing value decide whether a worker may
still cause an outcome.

### Why durable completion comes before acknowledgement

| Order | Crash consequence |
|---|---|
| Delete the queue message, then record completion | Work can be lost permanently. |
| Record completion, then delete the queue message | The message may return, but the duplicate is recognised and becomes harmless. |

The worker's harmless smoke state, completion marker, and bounded terminal
evidence need one atomic boundary. A stale worker must not write after its
processing lease expired and another worker claimed the work; a monotonically
increasing fencing or attempt value protects that condition.

### Failure is classified before it is retried

| Result | Correct action |
|---|---|
| Already completed | Acknowledge the duplicate without repeating work. |
| Transient failure | Record safe diagnostics and retry only within the named policy. |
| Permanent invalid message or policy failure | Record terminal failure and allow the DLQ path. |
| Unexpected failure | Record safe diagnostics and consume only the remaining bounded attempts. |

### Misconception check

“Deleting a message means the worker completed its job.”

No. Deletion only ends normal queue delivery. The job is complete when durable
state proves its intended outcome and duplicate processing can no longer alter
that outcome.

### Study question

Why is a duplicate after durable completion preferable to a crash after early
queue deletion?

Because durable idempotency can make the duplicate harmless, whereas early
deletion can remove the only instruction to finish work that was never
recorded as complete.

## 82. A Dead-Letter Queue Is Quarantine, Not a Retry Button

### What entering the DLQ means

After a message exhausts the policy's delivery budget, the SQS redrive rule
moves it from the main queue to the DLQ. That means the platform could not
safely prove its intended outcome through normal automation. It does not prove
that the intended work never happened, and it does not make a replay safe.

### The recovery sequence

```text
correlate → inspect durable outcome → classify cause → repair cause
          → record a bounded recovery decision → close, escalate, or retry
```

The DLQ item must be correlated with its stable message/outbox/work identity,
attempt history, and safe failure facts. An operator then checks durable state
before choosing an action. A controlled retry creates an evidence link to the
original failure; it is not an untracked redrive of every message in the queue.

### What is safe to record

Safe evidence includes identifiers, policy version, attempt count, timestamps,
failure category, safe error code, and recovery decision. The raw queue payload
remains restricted operational data. It must not be copied into general logs,
audit events, alerts, LLM prompts, or dashboards simply to make investigation
easier.

### Future automation has a narrow role

A future resolver agent may classify a known duplicate, group repeated
transient failures, recommend a runbook action, or perform a separately
allowlisted idempotent recovery. It must not have a blanket permission to
empty the DLQ, replay every message, change production configuration, or read
unrestricted tenant data. The existing deferred remediation plan remains the
owner of that later design.

### Misconception check

“When the dependency recovers, replay the whole DLQ.”

No. Some prior attempts may have partly succeeded, some messages may be
permanently invalid, and a bulk redrive can overload a recovering dependency.
Repair first, then use a small controlled batch with evidence and idempotency
checks.

### Study question

Why must a DLQ recovery decision link back to the original failed delivery?

So an operator or later audit can explain why work was retried, determine
whether it already partly succeeded, and distinguish recovery from a new
business request.

## 83. A Capability Declares Need; The Platform Supplies Coordination

### Do not make fencing an app toggle

A job should declare a named delivery policy such as
`platform-short-idempotent-work.v1`. It should not contain an ad hoc
`useFencing` flag, SQS visibility value, DynamoDB condition expression, or
provider-specific retry callback. Those are platform coordination details.

The policy tells the platform which safety envelope the job requires. The
worker then establishes the required claim, lease, fence, retry, terminal
recording, and acknowledgement order. This makes the safe path ordinary rather
than asking every future capability author to reproduce distributed-systems
logic.

### Business logic still declares business meaning

| Question | Owner |
|---|---|
| How does a worker safely claim and finish queued work? | Platform worker. |
| Which delivery policy does this job require? | App capability contract. |
| What does `completed` mean for this workflow? | Business capability. |
| Can an external provider call be repeated safely? | Business capability and its integration adapter. |
| Did two users submit competing normal record edits? | Entity revision and business-concurrency rules. |

An app capability must still provide the stable idempotency identity and
define valid business state transitions. The platform cannot infer whether an
email, payment, document upload, or external provisioning action is safe to
repeat. It can only provide the generic coordination envelope around the job.

### When an entity needs no fence

A normal entity is not a leased work item. Two users editing the same customer
record usually need revision-based optimistic concurrency: the second update
is rejected or reconciled if it was based on an older revision. A fence is only
appropriate when a restartable processor temporarily owns exclusive work—for
example, a reconciliation job, import partition, or document conversion.
That fence normally belongs on a dedicated work/processing record, not on the
customer row itself.

### Misconception check

“If the platform handles leases, business code no longer needs concurrency
rules.”

No. The platform prevents stale workers from defeating the processing protocol.
Business code still protects its own state transitions, authorisation, data
constraints, and external effects.

### Study question

Why is a named delivery-policy reference safer than a `useFencing` flag on
each job?

Because a policy describes a reviewed, complete safety envelope. A lone flag
would invite incompatible combinations of retries, ordering, timeouts, and
acknowledgement behaviour.

## 84. A Profile Must Change What the Worker Emits

### From a declaration to a guardrail

Earlier, a job could *declare* a profile while the worker still emitted its
own generic facts such as a raw message type and retry count. That is like a
restaurant collecting an allergy card at the door, then letting every cook use
any ingredient anyway: the declaration exists, but it does not protect the
outcome.

The worker now resolves the job's declared profile from the complete mounted
registry before it emits telemetry. It gives the profile a small typed set of
facts it knows truthfully:

```text
capability=platform-smoke.smoke.rebuild
action=execute
execution_context=worker
job_delivery_disposition=retry_scheduled
outcome=failed
error_class=PLATFORM_WORKER_HANDLER_FAILED
```

The profile may select some of those facts for an operational log, a stricter
subset for metric dimensions, and another subset for trace attributes. It
cannot select the queue payload, tenant, message ID, raw exception, retry
delay, or a free-form new field, because those are not in the typed canonical
vocabulary. The worker does not add them after the projection either.

### What the runtime now does

| Profile says | Worker behaviour |
|---|---|
| `operational_log` | Write one bounded `platform.worker.job.delivery` record with only its approved log fields. |
| `metric` | Record one bounded delivery counter using only approved metric dimensions. |
| `trace` | Create and complete one `platform.worker.job` span with only approved trace fields. |
| `job_execution_latency` | Record that interval only after the handler was invoked, because otherwise no job execution occurred to measure. |
| `queue_wait_latency` | Record that interval only when the profile declares it, because the worker knows when this delivery entered its queue. |
| explicit opt-out | Emit no *capability* telemetry through this path. |

An unregistered message has no app-owned capability profile. The worker still
dead-letters it safely, but it must not pretend that the message belongs to a
known business capability or invent an app-level telemetry record for it.

### A crucial reliability rule

Observability answers “what happened?” It must not decide whether the work
happens. Therefore logging, metric recording, and tracing are all best effort:
if a telemetry port throws, the worker continues and returns the real job
result. The test deliberately supplies a broken logger, metrics sink, and
tracer, and the job still succeeds.

This does **not** mean evidence is unimportant. It means a future durable audit
or security requirement needs its own explicitly designed delivery guarantee;
we must not quietly treat a short-lived diagnostic signal as the proof that an
important action happened.

### Misconception check

“The normalisation helper redacts secrets, so a profile allowlist is optional.”

No. Normalisation protects against obviously dangerous values that reach a
helper. A profile decides which *kind* of fact should reach a helper in the
first place. Both are needed: profile first, normalisation second.

### Study question

Why does the worker record queue-wait latency only when a profile declares that
measurement rather than whenever it happens to have an enqueue timestamp?

Because collecting a number is not automatically meaningful. The profile says
the capability and its operators have agreed that this interval is worth
measuring; otherwise the platform avoids creating unreviewed cost, dashboards,
and alert pressure from every available timestamp.

## 85. A Profile Must Change What the Server Emits

### The same rule applies to HTTP

An HTTP route can be reached through more than its happy path. A caller may be
denied authentication, fail validation, exceed a rate limit, send malformed
JSON, or receive a timeout. Those are still attempts to use a known
capability—provided the server could match the method and path to that route.

The server therefore resolves the route's profile as soon as it can identify
the route. Its completion step then gives the profile a small truthful set of
facts:

```text
capability=platform-smoke.echo
action=read
execution_context=server
http_method=GET
http_status_code=403
outcome=denied
error_class=PLATFORM_SERVER_FORBIDDEN
```

The profile can approve a structured operational log, bounded metric labels,
a trace span, and a `request_response_latency` timer independently. It cannot
approve a path such as `/invoices/benelux-104`, the caller's token, a request
ID, a tenant, an account number, a request body, a response body, or an error
object. Those facts either identify a person/resource, contain business data,
or create unsafe cardinality in a metric.

### Why route matching happens before the decision, not before security

Finding a route means only: “this request is aimed at a known capability.” It
does **not** authorize the caller or invoke the handler. The normal security
order remains intact:

```text
match route → resolve its profile → rate limit/authenticate/authorize/validate → handler when allowed → emit approved evidence
```

This early route match lets the platform correctly describe a rejected attempt
as an attempt at `invoice.read`, while keeping the real authorization decision
where it belongs. It is like recognising the department a visitor is trying to
enter before deciding whether their badge opens the door.

### The two cases that must stay different

| Situation | What the server emits | Why |
| --- | --- | --- |
| `POST /invoices/123` matches `invoice.update`, but JSON is malformed | That route's approved capability telemetry, normally with `outcome=rejected`. | The request attempted a known business capability even though the handler never ran. |
| `TRACE /anything` is not a supported platform method, or the URL is malformed | Generic platform-server evidence only. | There is no trustworthy app capability to name. |
| A known route has an explicit profile opt-out | No capability telemetry. | An exception must genuinely suppress this optional evidence, not merely hide the declaration. |

Health checks are also platform operations. They retain their separate health
metric rather than being mistaken for a product capability.

### What “full” means at this point

Workers and HTTP routes now have the same **local, provider-neutral profile
behaviour**: profile selection, safe field projection, signal gating, declared
latency intervals, opt-out suppression, and failure isolation. That does not
yet mean a production observability system exists. We still need a selected
exporter/sink, real latency distributions for p95/p99, retention and access
policy, dashboards, SLO rules, and alarms.

### Timeouts are safety ceilings, not performance promises

The server already has mechanical time limits: 10 seconds for headers, 30
seconds for a request and handler, 5 seconds for an idle keep-alive connection,
and 30 seconds for shutdown draining. When a handler crosses its deadline, the
server aborts its signal and returns a safe timeout response, but still holds
its concurrency slot until the handler really stops. That prevents a slow
handler from becoming invisible background work.

Those settings protect capacity; they do **not** mean an interactive read is
allowed to take 30 seconds. Its ordinary performance target can still be p95
at 300 ms and p99 at 750 ms. A later target policy must divide a user-visible
deadline between ingress, server handling, downstream calls, cleanup, and the
safe error response. A provider-backed worker will need a separate execution,
queue-visibility or lease, retry, and shutdown budget.

### Timeout check

Why must a database or provider call have a smaller timeout than the server
handler that called it?

Because the handler needs remaining time to cancel work, release local
resources, record safe operational evidence, and return a controlled response.
If the downstream call consumes the whole budget, the caller cannot fail
safely.

### Misconception check

“A 403 should not create capability telemetry because the user never got to
use the capability.”

No. A 403 is often operationally important: it tells us a caller attempted a
known protected action and was denied. The record says `outcome=denied`; it
does not claim that the business action completed. The profile still prevents
the event from revealing who the caller was or which customer record they
tried to access.

### Study question

Why does an unsupported HTTP method use generic platform evidence instead of
borrowing the profile of a route with the same path?

Because the method is part of the route's contract. Borrowing a profile would
assert a business action we cannot truthfully identify and could make unrelated
traffic distort that capability's metrics.

## 86. Error Budgets Turn Targets into Sensible Alerts

### An objective includes an allowance

An SLO is not a claim that nothing may ever go wrong. It says how much imperfect
behaviour is acceptable over a stated window. That allowance is the **error
budget**.

For a 99.9% availability objective, 0.1% of eligible requests may fail. In a
window with 100,000 eligible requests, the allowance is 100 failures. The 101st
failure means that objective has been missed. A latency objective has an
independent allowance: “95% within 300 ms” permits up to 5% of its eligible
successful requests to take longer than 300 ms.

Do not add those allowances together. A request that takes 900 ms may spend the
300-ms latency budget and the 750-ms slow-tail budget; a request that returns a
safe `500` may spend the availability budget but is not treated as a successful
latency sample. Each objective needs its own honest denominator and budget.

### Burn rate asks how quickly the allowance is disappearing

The burn rate is the observed bad-event fraction divided by the fraction the
objective allows. If a 99.9% availability target allows 0.1% failures but a
service is currently failing 1% of eligible requests, it is burning its budget
at ten times the sustainable rate. If that continued, a 28-day allowance would
be exhausted in about 2.8 days.

One slow request is evidence, not an emergency. A useful alert policy combines
a short window that detects an active problem with a longer window that proves
it is sustained, and it requires enough eligible requests for the percentage to
mean something. At very low traffic, the honest result is “insufficient
confidence”; a named synthetic check provides the stronger early-stage signal.

### Misconception check

“A p99 objective gives us one global error budget.”

No. Availability, typical latency, and slow-tail latency answer different
questions and have separate allowances. Combining them hides whether users are
being rejected, most users are being slowed, or only a small but important tail
is suffering.

### Study question

Why should an alert use both a short and a long observation window?

The short window finds an active deterioration quickly. The long window filters
out an isolated spike. Requiring both avoids paging for a single unusual request
while still escalating a real, fast-moving outage.

## 87. Three Alert Families Answer Different Questions

### Do not make “alert” mean one thing

An alert is a request for attention. The signal that creates it determines who
should respond, what evidence they need, and where its policy belongs. The
platform needs three separate families.

| Family | Question it answers | Example | Policy home |
|---|---|---|---|
| Capability SLO | Is a named workload delivering its promised experience? | Interactive reads are persistently missing their 300-ms target. | Target NFR/SLO catalogue, after a metrics adapter can retain real distributions. |
| Platform/infrastructure health | Is a shared operating component unhealthy? | The ALB has no healthy targets, an ECS service lacks desired tasks, or a queue is building up. | Target `observability.alarms` catalogue, IaC, and its runbook. |
| Security | Does a control outcome or pattern require investigation? | Repeated denied export attempts across tenants or an unusual sign-in pattern. | Security-signal/detection policy, protected evidence store, and security incident runbook. |

An ALB target-health alarm cannot say whether `invoice.export` is slow. A
capability latency SLO cannot say whether somebody is probing permissions across
tenants. A security detection cannot be replaced by a high CPU alarm. They may
be correlated during an investigation, but they must not be substituted for one
another.

### One alert, one primary question

An alert definition may link a trace, a log query, a dashboard, or a related
security case. Its **trigger**, owner, severity, notification destination, and
runbook must nevertheless name one primary family. That keeps operations from
asking an infrastructure responder to interpret possible abuse, or a security
responder to diagnose ordinary latency regressions.

The staging target already has an infrastructure-health alarm catalogue. It
does not yet have a selected application metrics exporter for capability SLO
alarms, nor a general security-signal delivery and detection pipeline. Those
are explicit gaps, not evidence that the existing alarms cover every concern.

### Misconception check

“A `403` response should create an availability page because the user did not
get what they wanted.”

No. A valid permission denial is normally an expected policy outcome. It can be
important security evidence when it forms a suspicious pattern, but it is not
proof that the platform became unavailable. A server `500` or target timeout is
different: it can affect the availability objective.

### Study question

Why is a growing queue depth usually an infrastructure/worker-health alarm,
rather than an immediate failure of every asynchronous business capability?

Queue depth says the delivery system may be losing capacity or keeping work
waiting too long. A separate capability completion or queue-wait SLO determines
which business outcomes are actually being affected and how severely.

## 88. A Complete Target SLO Record

### One objective per record

A target should not put “the service must be fast and available” in one large,
ambiguous setting. It needs one policy record per independently evaluated
objective. Availability, typical latency, and slow-tail latency have different
denominators, error budgets, and escalation choices.

For example, an interactive read might eventually have three records:

| Semantic record | Question it answers |
|---|---|
| `interactive-read.availability` | Did eligible requests complete successfully? |
| `interactive-read.request-response.typical-latency` | Did most eligible successful requests complete within the typical threshold? |
| `interactive-read.request-response.slow-tail-latency` | Did almost all eligible successful requests avoid a seriously slow experience? |

These are examples of names, not live target settings. The target path already
supplies the environment; the name supplies the workload, interval, and
objective without hiding the meaning in a provider alarm name.

### Fields the policy must answer

The future target-owned `observability.slos` catalogue must make each record
answer the following questions.

| Field group | Question | Why it matters |
|---|---|---|
| Identity and purpose | What stable SLO is this and why does it exist? | Operators can find one unambiguous policy without reverse-engineering a dashboard. |
| NFR class and measurement | Which profile class and timed interval does it govern? | A queue-wait target cannot accidentally be applied to HTTP handler time. |
| Population | Which completed requests/jobs count, and which carefully justified cases do not? | The percentage is meaningless without a denominator. |
| Objective | What is a good event, success condition, or latency threshold? | “Fast” and “available” become testable. |
| Window and confidence | Over what rolling period, with what minimum sample, and what happens at low volume? | Prevents both noisy claims and hidden blind spots. |
| Budget and burn | What bad-event allowance exists, and what short/long sustained burn requires action? | Separates a routine outlier from an emerging incident. |
| Telemetry prerequisite | Which bounded metric, histogram, exporter, and synthetic check prove it? | A policy cannot claim p99 before a real distribution exists. |
| Response and lifecycle | Who owns it, where is the dashboard/runbook, and when is it reviewed? | An unowned objective cannot improve reliability. |

### Two catalogues, two jobs

The future `observability.slos` catalogue owns the **meaning and calculation**
of an SLO. The existing `observability.alarms` catalogue owns provider alarm
delivery and IaC mapping. An SLO alarm should reference the SLO record by its
stable id instead of copying the threshold and burn calculation into both
catalogues.

```text
observability profile → names workload class and interval
target SLO record     → defines the objective and evidence required
target alarm record   → defines notification and provider implementation
```

This avoids an easy drift problem: changing a 300-ms target in one file while a
provider alarm still evaluates the old value elsewhere.

### Misconception check

“If an SLO is target-owned, every capability automatically has one.”

No. A profile may declare useful telemetry without a user-facing promise. A
capability receives an SLO only when its target policy intentionally adopts its
NFR class and measurement, with enough evidence and an owner to stand behind
the objective.

### Study question

Why should a provider alarm reference an SLO record rather than duplicate the
SLO threshold in its own definition?

Because the SLO policy is the authority for what “good” means. The alarm is one
delivery mechanism for acting on that policy. One authoritative calculation
prevents their values and intent drifting apart.

## 89. A Histogram Exporter Turns Timer Points into SLO Evidence

### What exists today

The server and worker already emit provider-neutral Core metric points. A timer
point says, in effect, “this approved interval took 284 milliseconds, at this
safe recorded time, with these bounded labels.” It is one observation, not a
percentile calculation and not a histogram by itself.

The `Metrics` port is the seam between that application-side fact and a future
provider. Target composition will inject an exporter behind the port. Routes,
jobs, profiles, and generic platform modules must not import a cloud metrics
SDK or learn a provider's histogram syntax.

### What the exporter must add

| Exporter responsibility | Why the timer point alone is insufficient |
|---|---|
| Accept only target-approved metric definitions | A generic metric name must not become a way to create unreviewed paid series or unsafe labels. |
| Turn each approved timer into a histogram observation | Percentiles need a distribution of many values, not one duration. |
| Preserve count, sum, and bucket counts | Compliance queries need to know how many events fell at or below each threshold. |
| Use fixed bucket boundaries that include adopted SLO thresholds | A 300-ms objective needs a 300-ms boundary; otherwise its result is only an approximation. |
| Keep the profile's bounded label set | A histogram per tenant, user, request, or raw path would create unsafe cardinality and cost. |
| Batch and flush outside request/job work | Exporting must not make the user wait on a remote metrics service. |
| Expose exporter coverage/health | A missing or dropping exporter means the SLO evidence may be incomplete. |

For the provisional interactive-read target, the histogram would eventually
include boundaries at 300 ms and 750 ms, alongside useful neighbouring values.
The resulting counts can answer both “how many completed within 300 ms?” and
“how many completed within 750 ms?” without storing individual customer
requests as metric labels.

### The evidence path

1. A route or job measures only an interval its profile declared.
2. It emits one bounded Core timer point through the `Metrics` port.
3. The target-composed exporter validates the metric identity, unit, and label
   set against its catalogue.
4. The exporter adds the value to the approved histogram and delivers/batches
   it using its provider-specific mechanism.
5. The SLO query uses histogram bucket counts and the declared population to
   calculate compliance and burn.
6. An alarm, if justified, references that SLO result and routes the response.

### Reliability does not mean blocking the user

The exporter needs a bounded in-memory buffer, bounded retries, and an orderly
flush during shutdown. It must never turn an otherwise successful route or job
into a failure because a metrics provider is unavailable. That is the same
best-effort boundary as the existing local observability helpers.

But “best effort” does not permit silent false confidence. If delivery is lost
or cannot be verified for a required period, the target should report that SLO
evidence is incomplete and raise an operational coverage/health concern. It
must not claim that the objective passed simply because no measurements arrived.

### Misconception check

“We can calculate p99 later from ordinary request logs.”

Not reliably. Logs may be sampled, retained briefly, redacted differently,
inaccessible to the metrics query engine, or absent during an exporter failure.
A designed histogram preserves the aggregate distribution needed for the SLO
without making per-request logs into a fragile metric store.

### Study question

Why must a histogram bucket boundary include the actual 300-ms SLO threshold?

Without that boundary, the metrics system can only say that a value fell in a
wide range, such as between 200 and 500 ms. It cannot truthfully count exactly
how many requests met the 300-ms promise.

## 90. Dashboards Show Evidence; Synthetic Checks Cover Quiet Periods

### A dashboard is not an alarm

An alarm asks somebody to act. A dashboard helps that person understand what is
happening before, during, and after an incident. It must answer a small set of
operational questions without becoming a wall of unrelated graphs.

| View | Primary questions | Intended audience |
|---|---|---|
| Platform health | Are public targets healthy? Are tasks, capacity, queue delivery, and telemetry coverage operating? | Platform operator |
| Capability SLO | Is this workload receiving traffic? Are latency, success, budget, and burn meeting its named objective? | Capability/service owner |
| Security view | Are approved security signals forming a concerning pattern? | Authorised security operator |

The target policy should record each dashboard's stable id, owner, audience and
access boundary, safe panels, SLO/alarm references, runbook links, review date,
and retention assumptions. A security dashboard is not a convenient place for
ordinary broad operational access; raw customer or credential data belongs in
none of these views.

### “No data” is not green

Each SLO panel needs three visibly different states:

| State | Meaning |
|---|---|
| Measured and healthy | Required telemetry arrived and the calculation currently meets its objective. |
| Partial or insufficient confidence | Some evidence arrived, but volume or delivery coverage cannot support the claimed percentile/SLO result. |
| No data or telemetry failure | The required measurement is absent, delayed, or unverifiable. This is an observability-coverage concern, not a passing result. |

This matters especially in the early smoke target: its current short-retention
operational log destination and infrastructure alarms do not automatically
create capability dashboards or trustworthy application SLO evidence.

### Synthetic checks ask a controlled question

Live traffic explains what real users experienced. But early traffic is sparse.
A synthetic check is a scheduled, controlled request that asks, “can this
important path work right now?”

A good target-owned synthetic check declares its stable id, purpose, owner,
frequency, boundary/identity scope, expected status and latency, safe fixture,
notification/runbook, and result retention. A protected-path check uses a
least-privilege synthetic identity and a non-mutating or idempotent fixture. It
must not quietly bypass the ingress, authentication, authorisation, or
rate-control boundary it claims to prove.

For example, a liveness synthetic check proves that the public health endpoint
can be reached. A protected smoke-route check proves more: DNS/TLS/ingress,
token validation, routing, permission handling, application execution, and the
safe response. Neither one manufactures a p99; it supplements the honest
low-volume status with a repeatable availability signal.

### Misconception check

“A green synthetic check proves the platform is meeting its user SLO.”

No. It proves one controlled path worked at one point in time. Real traffic
distributions still determine whether ordinary users experience acceptable
latency and success rates. The two forms of evidence complement each other.

### Study question

Why should a protected synthetic check use an ordinary least-privilege identity
instead of a special bypass credential?

Because a bypass can remain green while ordinary authentication, permission, or
routing policy is broken. The check must exercise the boundary it is supposed to
prove, while using a safe fixture that cannot damage business data.

## 91. Observability Data Has a Lifecycle Too

### Retention follows purpose, not one universal number

“Logs are kept for two weeks” is not a complete data policy. The current
staging operational log destination has 14-day retention, but that applies only
to those ordinary operational logs. It does not decide the retention of metric
aggregates, traces, security signals, or durable audit evidence.

| Evidence class | Typical purpose | Retention rule it needs |
|---|---|---|
| Operational logs | Diagnose recent technical behaviour. | Short, cost-conscious operational retention. |
| Aggregate metrics/histograms | Calculate SLOs and see trends. | At least the complete SLO window plus a review margin. |
| Diagnostic traces | Follow a bounded technical path in detail. | Separately selected, usually short and access-restricted. |
| Security signals | Detect and investigate suspicious control outcomes. | Security-policy retention, access, integrity, and incident requirements. |
| Audit events | Prove accountable actions. | Product/compliance/legal retention and integrity requirements. |

The last two are deliberately not “just observability data.” Their durability
and lifecycle must be designed separately from optional metrics or logs.

### Access follows the audience

| Audience | Evidence normally needed | Boundary |
|---|---|---|
| Platform operator | Bounded health dashboards and ordinary operational logs. | No automatic customer-data or unrestricted tenant access. |
| Authorised engineer | Scoped diagnostic traces/log queries during investigation. | Time-bound, justified access; no credentials or raw payloads. |
| Security operator | Approved security signals and detection evidence. | Separately protected security workflow. |
| Compliance/audit reader | Durable accountable-event evidence. | Separate audit access model and retention rules. |

Administrative or break-glass access is not a reason to remove these
boundaries. It should be time-bound, justified, and auditable itself.

### Sampling is a deliberate choice

Sampling means intentionally recording a known subset of events under a named
rule. It is different from losing events because an exporter failed.

The first SLO metrics adapter should preserve every eligible measurement. If a
future high-volume target adopts a statistically valid sampling strategy, it
must make the rate and coverage visible so calculations remain honest. Traces
and ordinary successful logs may be sampled separately for cost, while errors,
timeouts, and other high-value diagnostic cases receive explicit priority.

Required audit and security evidence must never silently inherit optional
operational sampling. A dropped exporter batch is a coverage failure, not a
sampling strategy.

### Misconception check

“Metrics are aggregate, so access control and residency do not matter.”

No. Even aggregate series can reveal product behaviour, tenant activity when
labelled badly, or operational topology. The platform's bounded label policy
reduces that risk, but target access, EU residency, and retention still need to
be selected and enforced.

### Study question

Why must a 28-day SLO retain aggregate evidence for at least 28 days?

Because the calculation needs the whole rolling window. Deleting week-one
histogram data on day 14 would make a claimed 28-day compliance result
incomplete, even if the dashboard still displayed a percentage.

## 92. From Local Instrumentation to Operational Evidence

### What is complete now

The repository has completed the **local, provider-neutral instrumentation
slice**:

- Core owns bounded metric, logging, and tracing ports plus unsafe-label
  guardrails.
- Capability profiles declare approved signal families, facts, and truthful
  timing intervals.
- The registry validates profile adoption before a mounted app begins work.
- The server and worker emit only resolved-profile evidence; an explicit opt-out
  emits no capability telemetry.
- Local tests and the smoke app prove safe emission, opt-out suppression, and
  telemetry-failure isolation.
- The staging target has an ordinary log destination and infrastructure-health
  alarms.

That is valuable, but it is not the same as proving a provider received a
histogram, calculated an SLO, displayed a dashboard, or delivered an alert.

### The first target metric catalogue and adapter

The staging target now records its first deliberately small catalogue:

| Item | What it answers | Why it is deliberately narrow |
|---|---|---|
| `platform-smoke-read-outcome` | How many eligible smoke-read requests succeeded or failed? | It supports availability without treating authentication denials or invalid client input as a platform outage. |
| `platform-smoke-read-request-response-latency` | How long did an eligible successful smoke-read request take from server receipt to response completion? | It measures one truthful interval, rather than a vague end-to-end duration. |
| p95 ≤ 300 ms / p99 ≤ 750 ms | Is the typical and slow-tail experience within the provisional interactive-read thresholds? | The histogram has exact 300 ms and 750 ms bucket boundaries, so either claim can later be calculated honestly. |

The new AWS adapter translates only a metric in that catalogue from the generic
Core `Metrics` port into an OpenTelemetry instrument. It refuses an undeclared
metric, incompatible unit, or unapproved label. It also permits only a
task-local collector address—not an arbitrary internet destination.

This is an important distinction:

```text
Profile:     “These safe facts may be measured for this capability.”
Catalogue:  “This target retains exactly these aggregate metric series.”
Adapter:    “Translate only those approved points to the selected provider.”
IaC:        “Run a local collector, give its task narrow AWS access, and prove it works.”
```

All four source lines are represented and checked locally. On 2026-09-22 the
first live-delivery proof was completed as well: a protected smoke read reached
the deployed ECS task, and CloudWatch returned both approved metric series.
The SLO entries still say `selected-not-evaluable`: one observation is not the
28-day evidence population, and exporter-loss coverage is still unproven.

### A subtle CloudWatch lesson: two metric query models

The first inspection used CloudWatch's familiar `ListMetrics` API and found no
capability series. That looked like a delivery failure, but it was the wrong
query model.

```text
classic CloudWatch metrics  → ListMetrics / GetMetricData
native OpenTelemetry metrics → PromQL query endpoint
```

The collector sends native OpenTelemetry Protocol (OTLP) metrics to CloudWatch.
CloudWatch keeps their OpenTelemetry resource attributes and point labels, so
they are queried with PromQL. The successful staging proof found both the
outcome counter and the latency histogram through that interface. A missing
result from a classic API therefore does not prove that an OTLP delivery path is
broken; first confirm which metric model the target selected.

### What the live proof establishes — and what it does not

The controlled client-credentials smoke request received `200`. Its safe,
allowlisted labels identify only the capability, action, server context, HTTP
method, response status, and outcome. CloudWatch then returned one successful
outcome counter and one histogram observation. A prior unauthenticated request
also produced its separate denied `401` series.

That proves the whole bounded path:

```text
protected request → profile → Core Metrics port → AWS adapter
→ task-local collector → CloudWatch OTLP endpoint → PromQL result
```

It does **not** yet make the SLO healthy. The availability objective requires
at least 100 eligible observations over its 28-day window; a controlled request
is a delivery proof, not a representative customer population. Nor has the
target deliberately stopped the exporter to prove the coverage alarm and
incomplete-confidence behaviour.

### What the prepared target composition actually does

The generic server still knows only about the portable `Metrics` port. The
Kanbien target entrypoint is the seam that chooses the AWS adapter, passes that
port into the server, and calls the adapter's bounded shutdown method when the
process stops. This prevents a route, worker, or generic server module from
learning the words “CloudWatch,” “OTLP,” or “AWS region.”

The ECS task definition adds a small ADOT sidecar. The application sends OTLP
HTTP only to `127.0.0.1:4318`, meaning another process inside the same task—not
an arbitrary host on the internet. The sidecar batches the points and uses
SigV4 to send them to CloudWatch. Its pipeline definition sits in an SSM
Parameter Store **String** because it is configuration, not a secret. The ECS
execution role reads that String at task startup; the ECS task role has
`cloudwatch:PutMetricData` for the collector's later request.

One subtle but important limitation: ECS task-role credentials are shared by
all containers in that task. The collector is therefore isolated by reviewed
task composition and the adapter's fixed loopback endpoint, not by a magical
per-container IAM wall. If a later risk model requires that stronger wall, the
collector must become a separate gateway/task.

The foundation and service templates first passed CloudFormation's read-only
validator, then their reviewed change sets were applied on 2026-09-22. ECS now
runs task revision 2 with the collector sidecar; both stacks are
`UPDATE_COMPLETE`, enhanced Container Insights is enabled, and all five
platform infrastructure alarms are `OK`. This is stronger than template
validation, but it still leaves the capability SLO, exporter-loss coverage,
and alert-destination proof to do.

### Why publishing an image is not deployment

An image is a sealed application artefact. Publishing it means placing one
immutable digest in ECR after the scan, SBOM, and provenance checks succeed.
Deployment is a separate action: it tells CloudFormation and ECS to make a
running service use that digest. That can change live traffic, task capacity,
IAM use, and service health.

The staging policy keeps those authorities separate. The protected GitHub
workflow may publish only the checked image and its evidence. A governed AWS
change-set procedure then shows the exact infrastructure delta, requires
review, and is the only route that may alter the service. The GitHub role's
source policy is correspondingly reduced to ECR actions; its live IAM update
remains a separately reviewed operation.

### Misconception check

“If a GitHub environment requires approval, it is safe for the workflow to do
everything after that approval.”

Not necessarily. An approval says a named action may proceed; it does not make
an unnecessarily broad action easier to review or reverse. Separating image
publication from service deployment makes the actual change set visible before
traffic is affected and limits the standing power of the automated identity.

### What remains before capability observability is operational

| Stage | Deliverable | Evidence of completion |
|---|---|---|
| Target policy | Initial metric-series and SLO catalogue selected; dashboard, synthetic-check, detailed delivery/access catalogues remain. | The target profile is the authority for the selected series, labels, buckets, populations, and provisional thresholds. |
| Metrics adapter | AWS CloudWatch OTel adapter is deployed and queried. | The approved outcome counter and latency histogram were returned through CloudWatch PromQL; unknown series/labels remain locally rejected. |
| Target composition | Target entrypoint, non-secret SSM collector configuration, ADOT sidecar, task capacity, collector log group, and narrow IAM are deployed. | ECS task revision 2 is healthy, and the source still keeps AWS outside generic platform modules. |
| Public synthetic proof | A controlled least-privilege client reaches the protected smoke capability through the real boundary. | A correct scope produced `200`; the unauthenticated boundary produced `401`. A valid wrong-scope `403` proof remains. |
| SLO proof | Histogram observations calculate the policy's good-event ratio/burn correctly. | Dashboard/runbook can find the evidence without sensitive fields. |
| Failure proof | Exporter failure causes coverage concern, not user/job failure or a false green SLO. | Controlled failure proves isolation, incomplete-confidence state, and alert/runbook path. |

Trace delivery and provider-backed worker queue/lease telemetry are later
extensions after their own adapters exist. Security-signal and durable audit
delivery are separate, stricter programmes; they are not additions to a metric
exporter.

### The correct completion claim

We may say today:

> Routes and jobs have local, provider-neutral, profile-governed observability
> instrumentation, and the staging HTTP smoke path has query-proven CloudWatch
> counter and latency-histogram delivery.

We must not yet say:

> The staging target has complete capability observability and trustworthy SLO
> alerting.

That stronger statement still needs a recurring public synthetic check,
enough eligible observations, exporter-loss coverage, access/dashboard,
SLO-calculation, and alert-delivery proofs above.

### Misconception check

“The smoke app's in-memory test saw a timer, so metrics delivery is complete.”

No. The test proves correct application-side emission. It does not prove a
histogram backend, retention, access control, SLO calculation, dashboard,
notification, or response path.

### Study question

Why must the exporter-failure proof show both that a request succeeds and that
SLO confidence becomes incomplete?

The first result protects product behaviour from an optional telemetry outage.
The second protects operators from mistaking missing evidence for healthy
performance. We need both to make the boundary trustworthy.

## 93. Next Lesson Queue

0. Persistence continuation: source-define the Kanbien staging table, indexes,
   encryption/recovery posture, and non-secret configuration are complete in
   source. Next, compose the acceptance, relay, and worker path, then grant
   each component only the access it uses.
1. Add focused physical failure tests, especially a conditional-write
   cancellation, before a real create-once result is treated as a precise
   duplicate result.
2. After separate AWS approval, prove the harmless state/lineage/outbox path,
   relay, queue delivery, durable worker completion, and recovery in staging.
3. Keep real product/entity persistence separate: its tenant rules, schema,
   classification, migration, retention, and restore policy remain future
   product work.

## 94. A Temporary Scheduler Is Not a Platform Scheduler

The staging smoke command now has an active temporary delivery mechanism: a
GitHub Actions workflow scheduled at `17 */4 * * *` UTC. Its isolated IAM role
is deployed and a manual run has proved the whole fixed request path. The first
clock-triggered run remains evidence to collect. It is a practical bridge for
a quiet, low-cost target—not the reusable scheduler capability the platform
will eventually expose.

```text
GitHub's best-effort clock
        ↓
separate main-only OIDC role
        ↓
read exactly one smoke-client secret
        ↓
fixed protected GET /smoke/synthetic-read
        ↓
safe status and latency result
```

## 95. What the Exporter-Loss Rehearsal Proves

The exporter-loss rehearsal is not a test to see whether an application can
survive a broken application feature. Telemetry is deliberately best effort, so
the application should survive. It is a test of whether operations notices
that the evidence path has become unreliable.

```text
one expected protected request
        │
        ├── application result: 200
        │
        └── expected metric: absent after grace period
                         │
                         ▼
       coverage verdict: missing → SLO confidence: insufficient-confidence
                         │
                         ▼
                    operator alert
```

The monitor is independent of the application exporter. It queries the
approved CloudWatch OpenTelemetry series through PromQL after the expected
request. It must use only the existing bounded labels—not a unique request ID
or customer identifier. A missing expected metric is not an error rate of zero;
it is missing evidence.

### Grace period versus query window

These two durations answer different questions. The five-minute **arrival
grace** gives a healthy exporter time to send a metric and for the provider to
ingest it. The twenty-minute **query window** is the history that the coverage
verifier searches.

For an ordinary scheduled check, the two work together: the synthetic request
arrives before the verifier and the twenty-minute query can find it. For an
exporter-loss rehearsal, they must not be confused. Waiting only five minutes
after breaking export could still let the verifier find an older healthy
observation from before the fault. The rehearsal therefore waits the whole
twenty-minute query window after its broken-export request. Only then can a
`missing` verdict be evidence of the intended fault rather than an ambiguous
mix of old and new telemetry.

The rehearsal keeps the application's fixed approved endpoint and moves only
the disposable collector receiver to a different loopback port. The request
must still return `200`; then the monitor must report `missing`, mark the
affected SLO window `insufficient-confidence`, notify the operator, and prove
recovery after the normal revision is restored. The detailed execution boundary
is in the exporter-loss rehearsal plan and needs separate AWS approval.

The role cannot deploy ECS, change CloudFormation, administer Cognito, or read
any other secret. It does not reuse the image-publishing role because “can push
an image” and “can read the synthetic client secret” are unrelated privileges.
If either purpose is compromised, keeping the roles separate limits the damage.

### A useful failed rehearsal

The first rehearsal intentionally changed the application's metrics endpoint
from port `4318` to `4319`. ECS rolled the task back because the target adapter
rejects that configuration before the server starts. This was not a failed
metric export: it was the security check doing its job. The endpoint rule stops
target configuration from redirecting operational telemetry to an arbitrary
destination.

The corrected fault leaves the application at its fixed approved endpoint and
moves only the disposable collector's receiver to `4319`. That creates a
connection failure at the intended boundary while the server remains able to
serve traffic. The broader lesson is that a good resilience rehearsal tests the
failure you mean to test; if a guard rejects the setup earlier, record that as
useful evidence and redesign the experiment rather than weakening the guard.

### A counter needs movement, not merely existence

The recovery check uncovered a subtle property of cumulative counters. A
freshly started task begins its request counter at zero. Its first successful
request creates an exported value such as `1`; later periodic exports can keep
reporting that same value. PromQL `increase()` asks whether the value changed
within its window, so a lone first request can correctly return zero even
though telemetry delivery is healthy.

```text
fresh task → request A → exported counter: 1 → request B → exported counter: 2
                                 baseline                 increase = 1
```

The controlled staging recovery proved this directly: after the normal task
revision returned, the first protected request was successful but the
freshness query remained `missing`. A second bounded request, made against the
same fixed route after the first export interval, advanced the counter and the
same read-only query returned `observed`.

This is not permission to weaken the coverage query to “does a metric exist?”
An old value could exist even when the expected new request never exported. The
correct rule is a two-point sequence: establish a baseline, then make a later
fixed request that advances it. The temporary scheduler now uses two bounded
requests 75 seconds apart, longer than the target's 60-second export interval.
Both requests remain protected, use the existing least-privilege identity, and
emit only their safe status and latency.

### The subtle limitation

“Every four hours” is only a nominal schedule when GitHub Actions supplies the
clock. GitHub can delay or miss a scheduled run. Therefore a completed run
means “the controlled path worked at that time”; an absent run means “we may
not have enough evidence.” Neither result proves a customer-facing SLO or that
the telemetry exporter delivered every measurement.

The later platform scheduler will have its own contract, target adapter,
durable schedule record, delivery/lease semantics, retry policy, and target
observability. At that point, this workflow can be retired rather than quietly
growing into a hidden platform subsystem.

## 96. A Documented Limit Is Not Always Your Effective Limit

Provider documentation is an important design input, but a production target
must still prove the exact query shape it relies on. CloudWatch documents a
seven-day maximum PromQL range. During the staging read-only check, however,
the selected OpenTelemetry counter accepted a one-day `increase()` lookback
and returned a safe HTTP `400` for two days and above. Historical one-day
evaluations—one, seven, and twenty-seven days earlier—did work.

So the target records both facts rather than pretending they are the same:

```text
documented provider maximum:      7 days
live-proven target query window:  1 day
28-day SLO calculation:           28 adjacent one-day windows
```

The evaluator reuses the same 28 time boundaries for every part of one
calculation. It sums counter increases for availability, then merges the
histogram's cumulative bucket counts before calculating p95 and p99. It does
not average daily percentiles: an average of p95 values is not the p95 of the
combined population.

The first live result had only about two eligible requests. That is a useful
proof of the query mechanism, but the policy needs 100 observations over the
real rolling 28-day period. The result is therefore
`insufficient-confidence`, which is the honest state—not healthy and not a
service failure.

### Misconception check

“The documentation says seven days, so a seven-day query must be safe in every
target.”

No. Documentation describes a supported outer boundary. Your exact metric
model, function, labels, endpoint behaviour, and currently deployed target
must still be verified. Record the observed effective limit, test it without
retaining raw provider errors, and keep the evaluator inside that limit.

### Study question

Why do we merge histogram buckets before calculating p95/p99 instead of
averaging a p95 from each day?

Because a percentile depends on the complete distribution of observations.
Bucket counts let us reconstruct that combined distribution; daily percentile
values have already thrown information away.

### Misconception check

“The scheduler is in GitHub Actions, so it is a CI test.”

Not quite. Normal CI checks source code and makes no live protected request.
This is a narrowly governed operational synthetic: it obtains a short-lived
token and crosses the real public boundary. That is why it receives its own
IAM role, no repository-secret fallback, a fixed route, and redacted output.

## 97. A Queue Consumer Is Not an Outbox

The smoke target now has a source-defined worker path: an SQS queue, a DLQ, a
separate no-ingress ECS worker, and a handler for the harmless
`platform-smoke.rebuild` job. The worker receives one message, runs the
registered job, and acknowledges the SQS message only if that job succeeds.

```text
one direct harmless message
        ↓
SQS source queue → worker receives it → job succeeds → SQS acknowledge
                                                        ↓
                                            worker returns to zero
```

That is a valuable proof, but it is deliberately small. A later business
capability must first make one durable transaction that changes business state
and writes its outbox obligation together. A relay then publishes that outbox
record. The worker must also claim durable processing state before any business
side effect. Those persistence records make retries and duplicate delivery
safe; an SQS message alone cannot do so.

### Why the worker starts at zero

The public server needs to stay available continuously. The worker is a
dormant operational component until we intentionally test it. Desired count
zero means the queue has no polling task and no idle Fargate cost. The future
proof starts exactly one worker only after confirming both source queue and DLQ
are empty, sends one safe message, waits for settlement, and returns it to
zero even when the proof fails.

### Misconception check

“If the source queue becomes empty, the worker definitely completed the work.”

Not by itself. Queue counts are approximate operational evidence. A reliable
business outcome also needs the worker's durable processing record and state
transition. For this harmless smoke handler, settlement plus worker health and
metric evidence is enough to demonstrate the consumer boundary, because the
handler has no external side effect.

### Study question

Why is a direct SQS smoke command not allowed to evolve quietly into the real
application's outbox producer?

Because it has no atomic relationship to an accepted business change. A crash
between changing a record and sending a direct queue message can leave one
without the other. The later outbox transaction exists precisely to preserve
that obligation.

## 98. Persistence Foundation: Facts, Coordination, and One Atomic Boundary

### The problem we are solving

Imagine a future capability accepts a request to create a harmless work item.
It changes the work-item state and needs background work to happen afterwards.
There are two dangerous half-successes:

```text
state saved              state not saved
outbox missing           outbox message exists
─────────────            ────────────────────
work is silently lost    background work refers to a thing that never existed
```

The durable-outbox pattern prevents both outcomes. One **atomic transaction**
makes the state change, its safe record-history fact, and an obligation for
later background delivery succeed together or fail together. A relay and a
worker then deal safely with the fact that queues can redeliver messages.

### First, separate three jobs that can look like “persistence”

| Layer | Question it answers | What we added locally | What it deliberately does not decide |
| --- | --- | --- | --- |
| Core persistence | “What stable facts must all providers understand?” | Versioned `OutboxEntry`, bounded `RecordChange`, transaction-aware repository option, errors, versions, pages, and repository vocabulary. | DynamoDB tables, SQS messages, product fields, or a cloud provider. |
| Platform persistence | “How does durable delivery stay safe across retries and restarts?” | Pending/leased/published outbox state; processing claims; attempts; leases; fences; safe lineage ports; atomic-write port. | A business entity's schema, a tenant's retention policy, or an AWS SDK call. |
| Future adapter and target | “How is that made real in this deployment?” | Nothing yet in this slice. | It must later choose and configure DynamoDB/SQS resources, IAM, encryption, alarms, and live proof. |

This is the same ownership pattern used elsewhere in the repository: Core
names stable nouns; Platform supplies reusable mechanics; an adapter translates
those mechanics to a provider; target infrastructure supplies real resources
and settings.

### What Core now means by an outbox entry

An `OutboxEntry` is deliberately a small, immutable promise:

```text
outbox ID
stable subject reference ──> which durable work record this concerns
versioned message type   ──> what a later consumer understands
delivery-policy name     ──> which retry/timeout/DLQ rules apply
created time and safe correlation/causation facts
```

It does **not** contain an arbitrary business payload, customer name,
document, token, raw request body, or free-form object. The queue can carry
the stable outbox identity; the worker retrieves the durable work record by
its safe subject reference. That is both easier to evolve and less likely to
turn the queue into an uncontrolled copy of business data.

The companion `RecordChange` is not an audit event and not a full history-row
copy. It records a stable record reference, revision, action (`created`,
`updated`, `deleted`, or `restored`), direct cause, optional safe actor, and
an allowlisted list of changed field names. It answers “which record revision
changed because of what?” without storing before/after values.

### The relay and worker have a small state machine

The new provider-neutral platform package models the following state changes:

```text
outbox:      pending ──claim──> leased ──publish──> published
                           │
                           └── lease expires ──> a later claimant may reclaim

processing:  unclaimed ──claim──> claimed ──complete──> completed
                           │
                           └── lease expires ──> a later worker may reclaim
```

Each claim gets two related numbers:

| Fact | Meaning | Example |
| --- | --- | --- |
| Attempt | How many delivery/processing tries have occurred. | `2` means this is the second claim. |
| Fence | Which claimant is currently allowed to complete the action. | Fence `2` supersedes fence `1`. |

A **lease** is a temporary permission to do work. A **fence** is the
monotonically increasing proof of which permission is current. If relay A has
fence 1, pauses, and relay B claims the expired item with fence 2, relay A's
later publish is rejected. We also enforce a subtler rule: a holder cannot
complete after *its own lease expires*, even before anyone else takes over.
Otherwise an abandoned process could still complete work outside the authority
window it was granted.

### The atomic-write seam: an honest promise, not a fake one

The latest slice adds `PlatformPersistenceAtomicWriter`. It is a contract that
a real provider adapter must implement. It gives the product code one scoped
transaction handle:

```text
transaction scope
    ├── transaction-aware product repository saves state
    └── scope stages one validated lineage + outbox mutation
                ↓
adapter commits all three writes together, or commits none
```

The staged pair is checked before the adapter accepts it:

- the outbox subject must be the same record as the lineage subject;
- both facts must share the same direct cause;
- declared tenant scopes and correlation IDs may not conflict.

There is intentionally **no in-memory implementation** that claims to provide
this atomicity. The Core in-memory repository now rejects a transaction handle
with `PERSISTENCE_TRANSACTION_UNSUPPORTED`. That may seem less convenient,
but it is a valuable safety rule: silently ignoring the transaction would let
a local test look successful while writing product state outside the durable
outbox boundary.

### A concrete story

Suppose a future import capability accepts `work-17` because request `r-4`
asked for it.

1. The product repository changes `work-17` to `accepted` using the scoped
   transaction.
2. It stages a record change saying revision 1 of `work-17` was created by
   `r-4`.
3. It stages an outbox entry for the same `work-17`, also caused by `r-4`.
4. The real adapter either commits all three records or rolls all three back.
5. Later, a relay leases the outbox item, sends a small identity/reference
   message, and marks publication only if it still holds an unexpired fence.
6. A worker claims that stable identity, records its terminal outcome before
   acknowledging the queue, and a duplicate delivery recognises the completed
   processing record.

The important distinction is this: the initial transaction makes the
**obligation** durable. It does not prove the queue received the message or
that the worker finished. Those are later, independently recorded stages.

### What is implemented, and what is not

| Implemented locally in this chat worktree | Still planned before a real smoke proof |
| --- | --- |
| Semantic Core persistence files and source guides. | DynamoDB persistence adapter and transactional write construction. |
| Immutable outbox and bounded record-lineage contracts. | DynamoDB table/index, encryption, TTL/backup, IAM, and alarms. |
| In-memory outbox/processing/lineage state-machine proof. | DynamoDB persistence adapter and concrete queue sender/receiver composition. |
| Provider-neutral relay composition with the existing Core queue-send port. | Durable processing-claim composition inside the worker lifecycle. |
| Lease expiry and stale-fence rejection tests. | A harmless smoke capability using the atomic writer. |
| Atomic-writer contract and transaction-aware repository seam. | Controlled staging proof, duplicate/recovery evidence, and cost review. |

The source is tested locally, but it has not yet been committed or deployed.
No AWS resource changed during this persistence work.

### Misconception checks

“We now have exactly-once processing.”

No. We have the local contracts and state rules needed for duplicate-safe
delivery. Queues may still deliver more than once. The real outcome becomes
effectively once only when the adapter atomically records processing and the
business state transition.

“The in-memory test can prove a database transaction.”

No. It can prove state-machine rules. It must not pretend to prove atomic
durability, so it rejects a transaction-aware save.

“The outbox is just another name for SQS.”

No. The outbox is a durable database obligation. SQS is one possible later
transport used by a relay after that obligation exists.

### Study questions

1. Why is rejecting an unsupported transaction safer than accepting it and
   performing an ordinary in-memory save?

   Because accepting it would make the caller believe state, lineage, and
   outbox writes share a rollback boundary when they do not.

2. Why does a fence not replace a lease-expiry check?

   A fence protects against a later claimant. The expiry check protects the
   interval before that later claimant exists, when the original process has
   already lost its authority.

3. Why is an outbox's stable record reference safer than a raw job payload for
   this first platform foundation?

   It lets the consumer retrieve current durable state and avoids creating a
   second uncontrolled copy of business or sensitive data in a queue message.

Planning triage: the implementation order, ownership boundaries, and future
DynamoDB/SQS smoke proof are recorded in
[`persistence-foundation-v1.md`](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
This teaching chunk adds no new policy beyond that plan; it records the local
implementation and its explicit limits.

## 99. The Outbox Relay: A Bridge, Not a Worker

The next local slice adds the missing bridge between the durable outbox and a
queue. It is deliberately small: the relay chooses one due outbox obligation,
temporarily claims it, asks the queue to accept a minimal message, and only
then records that publication succeeded.

```text
durable outbox entry
        │ claim (lease + fence)
        ▼
relay ──send only { outboxEntryId }──> queue
        │ queue accepts
        ▼
mark entry published using the same unexpired fence
```

The message does not carry a customer record, a document, a full job payload,
or a provider-specific receipt. It carries the stable outbox ID. That ID is
also the queue message ID and idempotency key, so a later worker has one
durable identity to use when it looks up and claims the work.

### Why the order matters

If the relay marked the outbox as published **before** the queue accepted the
message, a crash or send failure could lose work permanently. This implementation
does the safer order:

1. claim the pending entry;
2. send the minimal envelope;
3. only after acceptance, mark the entry published.

There is an unavoidable opposite edge case: the queue can accept the message,
then the relay can stop before it writes the published marker. On recovery the
entry may be sent again. That is not a bug; it is why the worker must later
claim and complete the same stable outbox identity before acknowledgement.

### What happens when the queue is unavailable

The relay does not invent its own retry loop, backoff, DLQ policy, telemetry,
or shutdown behaviour. A queue-send failure leaves the outbox entry in its
leased state. Once that lease expires, a later relay can reclaim it. The new
local test proves that this recovery gets a new, higher fence and a second
attempt number.

This is an important separation:

| Component | Responsibility | Does not do |
| --- | --- | --- |
| Outbox relay | Make the durable obligation visible to a queue. | Receive, retry, acknowledge, or dead-letter a job. |
| Existing worker | Receive delivery, run the handler, retry/DLQ, trace, log, and shut down safely. | Decide whether an outbox promise was published. |
| Future adapter | Preserve the stable outbox ID and causation across the concrete transport. | Replace the platform's portable contracts. |

### Misconception check

“A relay completing means the job completed.”

No. A relay completing means only that the queue accepted a request to perform
later work. The worker's durable processing claim and completion record are
the separate proof that the work was handled safely.

### Study question

Why is a provider message ID not a safe replacement for `outboxEntryId`?

Because the provider can redeliver the same logical work with a different
delivery ID. The outbox ID survives retries and lets durable worker processing
recognise that the work is the same obligation.

Planning triage: the relay's current local scope and the remaining worker and
transport composition are recorded in
[`persistence-foundation-v1.md`](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
This lesson adds no new plan; it records the completed provider-neutral relay
slice and its explicit non-goals.

## 100. A Durable Worker: Claim, Run, Settle, Then Acknowledge

The relay makes a durable obligation visible to a queue. The worker must now
make sure that the obligation is not performed twice when the queue delivers a
duplicate.

The worker is given an **optional durable-outbox mode**. It is deliberately
not enabled for every background job: a direct scheduled job may not have an
outbox record at all. When enabled, it accepts only a message that identifies
the same outbox obligation in all three places:

```text
queue message ID       = outbox-42
idempotency key        = outbox-42
payload.outboxEntryId  = outbox-42
```

If one differs, the worker rejects the delivery before the app handler runs.
This is important because a transport provider can assign a new delivery ID on
redelivery. That new provider ID must never quietly replace the stable
`outboxEntryId` used by the persistence record.

### The worker's safe paths

```text
arrival
  │
  ├── completed success ──> skip handler ──> succeed/ack
  │
  ├── completed terminal failure ──> skip handler ──> existing DLQ outcome
  │
  └── claim current fence
          │
          ├── handler succeeds ──> record completion ──> succeed/ack
          │
          ├── handler fails but may retry ──> release claim ──> existing retry path
          │
          └── final handler failure ──> record terminal failure ──> existing DLQ path
```

The word **release** matters. If a worker keeps its lease after a temporary
failure, its next legitimate retry would find its own still-active claim and
be blocked. Releasing preserves the previous attempt and fence as history,
but makes the record immediately eligible for a new claim with a higher fence.

There is a subtle but important distinction in the first two branches. A
terminal-completion record means **do not execute the business effect again**;
it does *not* mean **the message was successful**. Returning success there
would acknowledge a later redelivery and bypass the provider's DLQ policy. The
worker instead returns the same non-success, dead-letter outcome without
calling the handler a second time.

### What “acknowledge last” means

The generic worker reports success only after durable processing records
success. The target-specific queue loop already acknowledges only a successful
worker result. Therefore this order holds:

```text
durable completion first
queue acknowledgement second
```

If completion cannot be stored—for example, because the lease expired—the
worker does not report success. The target loop releases the delivery, letting
the queue redeliver it according to its own retry/DLQ policy.

### An honest remaining limit

This local worker composition proves the control-flow order. It does not yet
prove that a real business state change and the durable completion marker share
one physical database transaction. That stronger promise belongs to the later
DynamoDB adapter and harmless smoke capability. Until then, the code is clear
about the intended boundary rather than claiming exactly-once business effects.

### Study question

Why must a temporary handler failure release the current processing claim
before the worker’s normal retry mechanism runs?

## 101. Observing the Persistence Conveyor Belt Without Copying Its Cargo

The outbox flow now has several small but important transitions. “The worker
failed” is too vague to diagnose all of them. Did the relay fail to claim the
outbox item? Did the queue accept it but the publication marker fail? Did the
worker release a retry, or reach terminal failure?

We give each of those an approved **transition name**. The transition name is
like a label on the conveyor-belt station, not a photograph of the package:

```text
safe station label                         never copied into telemetry
────────────────────────────────────────   ───────────────────────────────
processing.retry_released                  outbox ID, invoice/customer data,
outbox.publish_marker_failed               payload, tenant, queue receipt,
processing.duplicate_terminal_failure      fence number, or raw error text
```

`platform/persistence` says only: “this named transition happened, with this
bounded outcome.” It sends that fact through an optional observer port. It
does not know whether the target uses CloudWatch, another provider, or no
telemetry at all.

`platform/observability` supplies the other half. It takes a registered
profile and can make the same safe fact into:

- a structured operational log, with an optional correlation reference;
- a metric counter, using only low-cardinality profile fields; and
- a small trace span, optionally linked to the enclosing worker trace.

The metric uses a separate fixed name per transition, such as
`platform.persistence.outbox.claimed.outcome`. We intentionally do **not** add
an arbitrary `transition` label. Fixed names are easy to review in the target
metric catalogue; arbitrary labels are a common route to costly,
high-cardinality metrics.

### Misconception check

“If the observer knows an outbox entry exists, it needs the outbox ID in every
metric to be useful.”

No. Aggregate metrics answer “how often is publication-marker failure
happening?” They should not become a database of individual work items. A safe
correlation reference can help follow one authorised incident through logs, and
existing trace context can connect spans, while durable persistence records
remain the place to inspect the particular obligation.

### Study question

Why is a fixed metric name such as
`platform.persistence.processing.retry_released.outcome` safer than one metric
with a free-form `transition` label?

Because otherwise the retry meets the first attempt's still-valid lease and
cannot become the authorised claimant, even though it is the legitimate next
attempt at the same work.

Planning triage: the worker composition, release-for-retry state, and remaining
adapter/operational-profile work are recorded in
[`persistence-foundation-v1.md`](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
This lesson records the completed local composition; it does not create a new
plan or claim an AWS deployment.

## 102. A Storage Adapter: Keeping DynamoDB Details Out of the Application

We now have a **DynamoDB persistence adapter**. An adapter is a translator at
the edge of the platform. The app asks for things using the stable vocabulary
it already understands—an outbox entry, a processing claim, a record change.
The adapter translates those requests into DynamoDB-specific keys, index
queries, condition expressions, and commands.

```text
app capability                 DynamoDB adapter                 DynamoDB table
───────────────                ────────────────                 ──────────────
"this work item changed"  ──>  encode safe lineage row      ──>  LINEAGE#...
"send later"               ──>  encode durable obligation   ──>  OUTBOX#...
"may I process this?"      ──>  condition + lease + fence    ──>  PROCESSING#...
```

The table contains several **logical record types**. That does not mean they
are muddled together. Each has a recognisable key:

- an outbox row has the stable outbox ID and a separate due-time index, so a
  relay asks “what is eligible now?” without searching every row;
- a processing row has that same stable ID, so an SQS redelivery finds the
  existing claim instead of starting anonymous work again; and
- a lineage row is ordered by a record's revision and can also be looked up by
  its direct cause.

The index query is a candidate list, not permission to act. DynamoDB secondary
indexes may be slightly behind the primary table. The adapter therefore still
uses the conditional claim as the final authority. If two relays see the same
candidate, only one conditional write wins; the other reads the honest
`lease-active` state.

### What the transaction does—and does not—prove today

The adapter can write the **platform-owned facts**—one lineage entry and one
initial outbox obligation—in a DynamoDB transaction. Both appear, or neither
does. That is useful, but it is not yet the full business promise:

```text
today:       lineage + outbox                         one transaction
next slice:  smoke work-item state + lineage + outbox one transaction
```

Why not have Platform invent the missing work-item write? Because Platform
does not know which fields the future entity has, what its valid states are,
or how its version/lifecycle should work. Making a generic fake write would
hide that responsibility and create a dangerous false sense of atomicity.

### Misconception check

“If we use DynamoDB, the app must know DynamoDB keys and condition syntax.”

No. The adapter owns those implementation details. The smoke app will declare
only its harmless work-item meaning and call the provider-neutral persistence
seam. A later relational adapter could provide the same seam with a different
physical design.

### Study question

Why is a due-index query not enough by itself to let a relay publish an outbox
entry?

Planning triage: this is Phase 3a of the existing
[Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
The plan records that the smoke item's own transaction participant remains a
Phase 4 requirement; no new plan is needed.

## 103. An App Asks for One Transaction Without Knowing the Database

The next persistence slice gives the smoke app one tiny piece of product
meaning: a harmless work item can be accepted once. Its state is deliberately
small:

```text
work item ID → accepted → revision 1
```

Accepting the item also requires two platform-owned facts:

```text
app meaning                 platform facts
───────────                 ──────────────
work item is accepted  +    record change: created
                         +  outbox obligation: work-item accepted
```

The app does not save those things one after another on its own. Instead, it
asks an injected `PlatformPersistenceAtomicWriter` for a transaction scope.
It gives the scope's transaction to its own repository and stages the safe
lineage/outbox facts through the same scope.

```text
accept capability
   │
   ├── repository.create(work item, transaction)
   └── scope.stage(lineage + outbox)
             │
             ▼
selected composition / adapter decides how one physical transaction works
```

This is an important separation. The app is allowed to know the business
rule—"a work item is accepted once"—but it is not allowed to know a table
name, DynamoDB key shape, conditional expression, SDK client, or IAM role.
Those are implementation details chosen later by target composition.

### What the local test proves

The test uses a recording atomic writer. It proves that the repository sees
the exact transaction scope supplied by the writer and that the staged facts
refer to the same work item and direct cause. A second attempt returns a
duplicate result before an outbox entry is staged.

That is a valuable **contract proof**, but it is not yet a database proof. The
recording writer does not store anything. The next slice must implement a
transaction-aware DynamoDB work-item repository and compose its write into the
same DynamoDB transaction as lineage and outbox.

### Misconception check

“The app uses a transaction port, so we have already proved three database
writes are atomic.”

No. We have proved the app asks for the right boundary and refuses to stage an
outbox fact after a duplicate. The selected adapter must still prove that it
can make all three writes succeed or fail together.

### Study question

Why is the work-item repository an app-owned port rather than a generic
platform repository?

Because only the app knows what a work item is, which states are valid, whether
creation is idempotent, and which fields or lifecycle rules apply. Platform can
provide the transaction coordination rule without inventing that product
meaning.

Planning triage: this completes the semantic request portion of Phase 4 in the
[Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
The physical three-record transaction is explicitly still pending; no AWS
resource or target configuration has changed.

## 104. One Physical Transaction Needs a Participant, Not Just Good Intentions

The previous lesson showed the application *asking* for a transaction. This
lesson covers the next layer down: how the selected DynamoDB adapter prevents
that request becoming three adjacent but independent writes.

The adapter now provides an atomic writer with a very narrow conversation:

```text
target-composed repository          DynamoDB atomic writer
──────────────────────────          ──────────────────────
stage product-state write      ──>  hold it in one short-lived scope
stage lineage + outbox facts   ──>  validate the shared platform mutation
                                    │
                                    ▼
                           send one TransactWriteItems request
```

The adapter itself does **not** know what the product row means. It only knows
that a target-composed repository has supplied exactly one valid DynamoDB
transaction operation while the writer's scope is open. It then combines that
operation with the two platform-owned writes:

```text
1. product-owned state row     (defined later by smoke composition)
2. bounded lineage fact        (defined by Core)
3. initial outbox obligation   (defined by Core)
```

All three are sent to DynamoDB as one transaction. If any conditional check or
write fails, DynamoDB makes none of them visible.

### Two useful safeguards

- The adapter refuses to send anything without both kinds of contribution: a
  product participant **and** a validated lineage/outbox mutation. This catches
  a repository that accidentally uses the scope but forgets to stage required
  durable delivery facts.
- The staging function works only while the supplied transaction is open. A
  repository cannot save the handle and use it later to smuggle an unrelated
  write into a future request.

The transaction does not allow an after-commit callback. A callback is local
process memory: if the process dies after DynamoDB commits, its promised later
work could disappear. The durable outbox is the reliable replacement—it stores
the obligation with the state and lets a relay deliver it safely later.

### Misconception check

“The adapter now has a product-row write, so it knows how to store every
future entity.”

No. The adapter only knows the *shape of a DynamoDB transaction operation*.
The still-pending smoke repository will define its one harmless work-item row.
A future invoice, document, or medical record must define its own schema,
lifecycle, classification, and repository rather than reuse a fake universal
row.

### Study question

Why does the atomic writer reject a transaction that contains lineage and an
outbox fact but no product participant?

Because that would make the platform appear to have protected a state change
when no state write participated at all. Refusing the incomplete transaction
makes the missing responsibility visible before it reaches the database.

Planning triage: this completes the reusable physical-coordination portion of
Phase 3. The target-composed smoke repository remains the next Phase 4 slice;
no AWS resource or deployment setting has changed.

## 105. Composition Is Where a Product Row Finally Becomes Real

The previous two lessons deliberately stopped short of defining a database row.
That was not hesitation—it protected the architecture. The generic DynamoDB
adapter can coordinate a transaction, but it cannot honestly decide what a
work item, invoice, or medical record means.

The new Kanbien staging composition root supplies that missing product-specific
piece. It chooses the adapter and defines one harmless smoke row:

```text
app acceptance capability
        │ asks for a transaction
        ▼
target-composed smoke repository
        │ supplies one SMOKE-WORK-ITEM write
        ▼
DynamoDB atomic writer
        │ adds lineage and outbox writes
        ▼
one intended three-write DynamoDB transaction
```

### What each layer knows

| Layer | It knows | It must not know |
| --- | --- | --- |
| Smoke app | A work item is accepted once. | DynamoDB table names, keys, SDK calls, or IAM. |
| Generic Platform adapter | How to combine valid writes into a DynamoDB transaction. | What a smoke work item means. |
| Kanbien target composition | The one harmless work-item row and the selected adapter. | Reusable application business rules for future entities. |

The row is intentionally boring: an opaque work-item ID, the fixed
`accepted` state, a first revision, and a timestamp. It contains no request
body, user data, tenant data, document, prompt, or message payload.

### What the new proof demonstrates

The compiled platform-shell verifier creates the target composition with a
recording DynamoDB client and invokes the app's acceptance capability. The
recording client sees exactly one command with three writes:

1. the product-owned smoke work-item row;
2. the bounded record-change lineage fact; and
3. the outbox obligation for later relay work.

This is stronger than a unit test that merely checks whether three functions
were called. It proves that the *compiled target wiring* can request the one
atomic DynamoDB operation without quietly importing TypeScript source files at
runtime.

### What it does not prove

It does not send anything to AWS. There is no staging table, selected target
configuration, relay, worker result, or deployed recovery evidence yet.

There is also an important distinction about duplicates. The target row has a
create-once condition. In a real DynamoDB transaction that condition rejects a
second physical write. The generic adapter safely returns a bounded store
failure for a cancelled transaction today; it does not pretend it can always
identify every cancellation as exactly “this work item already exists.” A
focused failure test must settle that product-facing result before real code
depends on it.

### Misconception check

“Because the target composition contains a DynamoDB row, all future apps can
reuse it.”

No. The point is the opposite: each future app supplies its own narrow row
meaning at its own composition boundary. The reusable part is the transaction
discipline, not a fake universal record shape.

### Study question

Why is the harmless row definition allowed in target composition rather than
the generic DynamoDB adapter?

Because it depends on both the selected provider and the smoke app's one
business meaning. Putting it in the adapter would make the adapter secretly
own product schemas; putting it in the app would make the app dependent on
DynamoDB.

Planning triage: this completes Phase 4b of the
[Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
The next governed slice is Phase 5 target resource/configuration planning;
no AWS resource changed.

## 106. A Table Is a Protected Cabinet, Not an Active Feature

We have now described the physical storage cabinet for the harmless smoke
workflow. That does **not** mean the application is using it yet.

The table has one primary lookup and two secondary lookup paths:

```text
primary key:          find one known record directly
outbox due index:     find delivery obligations that are ready to relay
lineage cause index:  find safe record changes caused by one direct event
```

The indexes exist because the relay and an investigation ask different
questions. Reading every row to find work that is due would become slower and
more expensive as the table grows. An index is like a separate card catalogue:
it lets DynamoDB find the relevant category without inspecting every cabinet
drawer.

### Why the protection settings matter

| Setting | What it protects against | What it does not promise |
| --- | --- | --- |
| On-demand billing | Paying for idle capacity on this tiny initial workload. | A fixed monthly cost. Requests and stored data still cost money. |
| Server-side encryption | Reading storage media or backups without DynamoDB decrypting it. | Permission to read the table; IAM still decides that. |
| Point-in-time recovery | Restoring a table to a recent moment after an operational mistake. | A tested application restore process or a product retention policy. |
| Deletion protection and CloudFormation retain | Accidentally deleting the whole table through a stack operation. | Keeping every individual record forever. |
| No DynamoDB TTL | Avoiding a false claim that background expiry is a governed deletion rule. | A future retention, legal-hold, restore, or privacy-erasure policy. |

### The deliberate Phase 5a non-step: no IAM permission yet

It might seem safer to grant the server and worker access now, while we know
they will need it later. It is not. A permission should name a real actor and
a real action. Today there is no mounted acceptance route, relay process, or
worker lookup that uses this table. Granting access before those components
exist would be unused authority.

At that point, the source said three honest things at once:

```text
table design:             ready for review
target configuration:     selected but not delivered to a task
workload IAM access:      intentionally absent
live AWS evidence:        absent
```

That was not a permanent prohibition. It was a rule about sequence. Phase 5b
now has a real server component to justify one permission, so the staging
source grants its task exactly `dynamodb:PutItem` against this one table for
the all-`Put` members of the `TransactWriteItems` request
table. It still cannot read arbitrary rows, query an index, delete data, or
administer DynamoDB. The relay and worker still receive no table access because
they still do not exist as target-composed components.

### Misconception check

“The CloudFormation file defines a table, so there is now a database in
staging.”

No. CloudFormation source is a blueprint. A reviewed change set must still be
created and explicitly approved before AWS is allowed to create or change
anything. Until then, this is a tested design in the repository.

### Study question

Why do we create an `OutboxDueIndex` instead of letting the relay scan the
whole table for pending entries?

Because a scan grows with every record, including unrelated work-item and
lineage records. The index makes “what is ready now?” a deliberate, bounded
query while the conditional lease remains the final authority against races.

Planning triage: this completes Phase 5a of the
[Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
The next slice is component composition and narrowly justified IAM; Phase 5b
now composes the server acceptance component, but no AWS resource changed.

## 107. A Safe Write Endpoint Is a Thin Vertical Slice

We now have a server-facing way to start the harmless workflow. It is not a
general “write anything to DynamoDB” endpoint. It is one very specific promise:

```text
authorised caller
      │ POST /smoke/work-items (no body)
      ▼
stable request ID ──> smoke work-item ID
      │
      ├── create work-item state
      ├── append safe lineage fact
      └── create outbox obligation
                │
                ▼
          one DynamoDB transaction
```

### Why accept no body?

For this proof we do not need a customer name, an invoice, a file, or even a
human-readable task description. Allowing a body would create unnecessary
input validation, classification, logging, and retention questions. The route
therefore rejects every body, including `{}`. It gets its identity from the
request ID generated by the server (or an accepted UUID-shaped request ID).

That identity has two jobs:

1. It is the new work-item ID.
2. It is the **idempotency identity**: retrying the same request uses the same
   create-once key instead of creating a second item.

This is useful when a server times out after DynamoDB completes the transaction
but before the client receives its response. The caller retries with the same
request ID; it must not silently create duplicate later work.

### Why a separate permission?

The old smoke permission means “read a harmless response.” It would be too
broad to let it create durable work as well. The new route requires:

```text
platform-smoke.persistence.work-item:create
```

The staging target maps that permission to a planned
`platform-shell/smoke.write` identity scope. This mapping is source code only:
the Cognito scope has deliberately not been created or issued yet. So the
route is locally proved, but no person or client can use it in staging today.

### Where each responsibility sits

| Layer | Responsibility |
| --- | --- |
| Smoke app | Route meaning, no-body validation, request-ID idempotency, and safe `202` response. |
| Product | Chooses whether the smoke app receives the optional persistence seam. |
| Staging entrypoint | Selects DynamoDB and validates the target table/index configuration. |
| CloudFormation IAM | Lets the server submit one atomic transaction to this table—nothing else. |
| Cognito configuration | Still pending: issue the separately scoped controlled-write token. |

### Misconception check

“The server has DynamoDB permission, so it can now inspect or repair any
persistence record.”

No. `TransactWriteItems` is a single write operation. The server has no
`GetItem`, `Query`, `Scan`, `UpdateItem`, or `DeleteItem` permission on the
table. It can perform only the one carefully composed acceptance transaction.

### Study question

Why is returning `202 Accepted` more honest than `200 Completed`?

Because the state and durable obligation were accepted, but the relay has not
yet placed the message on SQS and the worker has not yet performed or recorded
the later work.

Planning triage: this completes the source-composed server half of Phase 4/5
in the [Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md).
The target proof, Cognito write scope, relay, worker completion, and all AWS
changes remain pending.

## 108. A Named Delivery Policy Must Match Its Target Mapping

We found a useful kind of architecture error: the named delivery policy said
one thing, while the target configuration said another.

```text
Named policy: 30-second work + 120-second visibility + 5 deliveries
Target source: 30-second visibility + 3 deliveries
```

That is called **configuration drift**. It does not mean either number is
automatically unsafe. It means the system has two competing answers to the
same operational question, so people can no longer reliably reason about
retries and DLQ behaviour.

### Which layer decides?

The named policy owns the promise in plain language: this is short,
idempotent, at-least-once work with a 30-second expected execution budget.
The staging target translates that promise into SQS settings:

| Policy question | Target mapping |
| --- | --- |
| How long can one attempt run before another worker may see it? | `VisibilityTimeout: 120` seconds. |
| How many deliveries can SQS make before quarantine? | `maxReceiveCount: 5`. |
| How long does ordinary work remain available? | Seven days. |
| How long does a dead-letter record remain reviewable? | Fourteen days. |

The extra 90 seconds of visibility is deliberate headroom. A 30-second normal
execution budget is not a guarantee that cleanup, network delay, controlled
logging, or a brief platform pause take zero time. It is still a bounded
policy: a genuinely slow workload needs a different named delivery policy,
not an endless visibility timeout.

### What changed today?

The repository’s target profile, CloudFormation queue definition, ECS worker
environment, sealed-runtime fixture, and static infrastructure gate now agree
on 120 seconds and five deliveries. AWS was not changed. A reviewed
CloudFormation change set must compare those source values with the live queue
before the target may claim the corrected behaviour.

### Misconception check

“Changing a CloudFormation file immediately changes the queue.”

No. The file is a reviewed blueprint. AWS changes only when the approved
change-set workflow applies that blueprint. Keeping source and live evidence
separate prevents a local edit from being mistaken for operational proof.

### Study question

Why is a target-profile value not just a duplicate of a generic policy?

Because the generic policy explains the desired behaviour, while the target
profile proves how this one environment maps that behaviour to a specific
provider’s settings, IAM, alarms, and rollback process.

## 109. A Queue Delivery Is Not the Same Thing as the Work Item

We added the missing producer half of the AWS SQS adapter. The important
lesson is not the `SendMessage` API call. It is the identity boundary around
that call.

```text
durable outbox entry
    │ stable ID: outbox-1
    │ direct cause: request-1
    ▼
Core queue envelope ──> SQS message body ──> temporary SQS delivery
                                               │ MessageId: provider-delivery-1
                                               │ ReceiptHandle: receipt-1
                                               ▼
                                      worker reconstructs outbox-1
```

### Why are there three identifiers?

They answer different questions:

| Value | Who owns it? | What is it for? |
| --- | --- | --- |
| `outbox-1` | Our persistence layer | The durable obligation and idempotency identity. |
| `request-1` | The direct earlier action | Causation: what directly created the obligation. |
| SQS `MessageId` / receipt handle | AWS SQS | One provider delivery and the temporary right to settle it. |

SQS may deliver the same message more than once. Each delivery can have a new
provider ID and receipt handle. If the worker treated either as the durable
identity, the duplicate would look like brand-new work. Instead, the sender
puts the Core envelope in the message body and the receiver recovers its ID,
causation, correlation, trace context, and idempotency key from that body.

### What does the sender do?

The provider-neutral relay passes a Core `QueueMessage` to `Queue.send`.
The SQS adapter validates the one SQS Standard-specific setting it accepts here
(a delay from zero to 900 seconds), serialises the safe JSON envelope, and asks
SQS to accept it. A provider failure returns a bounded `QUEUE_SEND_FAILED`
result, not a raw AWS error. The relay can therefore leave the outbox item
recoverable and retry it later.

The adapter deliberately refuses a message group key: this target selected SQS
**Standard**, which makes no ordering promise. Quietly accepting a FIFO-only
feature would let configuration mistakes become data-flow surprises.

### Misconception check

“SQS assigns a message ID, so we do not need our own ID.”

No. The SQS ID identifies one transport delivery. The outbox ID identifies the
one durable piece of work across all transport deliveries, retries, worker
restarts, and later investigations.

### Study question

Why is the receipt handle never written into an outbox or processing record?

Because it is short-lived authority to acknowledge one current delivery. A
later retry has a different handle, while the durable record must still refer
to the same stable outbox item.

Planning triage: the SQS sender/receiver adapter is now a locally verified
source component. Target relay composition, least-privilege sender IAM,
continuous dispatch, a live DynamoDB/SQS proof, and live Cognito write scope
remain deliberately unclaimed.

## 110. A Vertical Proof Connects the Stations Before AWS Is Involved

We now have a local proof that joins the small persistence pieces together.
It begins with the smoke app accepting one harmless work item, then follows
the durable obligation through the relay and worker:

```text
app accepts one work item
        │
        ├── work-item state
        ├── record-change fact
        └── outbox fact: "platform-smoke.work-item.accepted"
                         │
                         ▼
                    relay publishes
                         │
                         ▼
                  Core queue envelope
                         │
                         ▼
                 worker claims processing
                         │
                         ▼
                 handler completes once
                         │
                         ▼
              later duplicate is skipped
```

### The first integration mistake we found

The outbox fact already said the future message type was
`platform-smoke.work-item.accepted`, but the app had only registered the older
`platform-smoke.rebuild` job. The individual pieces looked reasonable, yet a
real worker would have received the new message and replied, “I do not have a
job for that type.” Its normal safe response would be to dead-letter it.

We fixed this by adding a harmless job registration for the exact outbox
message type. This is a useful general rule:

> A message type is a contract between the producer and consumer, not merely a
> string in one file.

The registry sees the complete set of registered jobs at startup. That is why
it is the right place to reject a missing or mismatched handler before a live
queue has to discover the mistake.

### What the local proof proves

The test uses small in-memory stores and the provider-neutral queue port. It
proves that:

- the app’s staged outbox fact produces the same job type the app registered;
- the relay retains the stable outbox identity in the queue envelope;
- the worker creates a durable completion record before it reports success;
- an identical later delivery is `durable-skipped`, so the app handler is not
  run a second time.

This is more meaningful than four isolated unit tests. It proves the seams
agree with one another.

### What it does *not* prove

In-memory proof is not a staging proof. We still have to give AWS a reviewed
way to run the relay and worker:

| Still needed | Why it matters |
| --- | --- |
| Relay task or scheduler | The one-pass relay knows how to relay once; it does not decide how often it should be invoked. |
| Worker task configuration | The worker needs the selected table/index values and a lease shorter than the queue visibility timeout. |
| Least-privilege IAM | The relay and worker each need only their own DynamoDB/SQS actions; the public server must not acquire those powers. |
| Live controlled proof | Only a real table and queue can demonstrate physical conditional writes, delivery, redelivery, and recovery. |

### Misconception check

“The source contains a relay entrypoint, so the relay is running.”

No. An entrypoint is an instruction for how a process would start. It becomes a
running component only when target infrastructure gives it a task, selected
configuration, permissions, a schedule or service topology, and an approved
deployment.

### Study question

Why is the duplicate test more valuable than simply proving that one message
was handled successfully?

Because queues are normally at-least-once. A single successful delivery says
nothing about the ordinary failure case where a worker completes the business
effect but loses its acknowledgement. The duplicate test proves the stable
outbox identity reaches durable processing, which is what prevents that later
delivery from repeating the effect.

Planning triage: the Persistence Foundation v1 plan and platform-runtime plan
now record the completed local vertical proof and the remaining target task,
IAM, scheduling, metric-catalogue, identity-scope, and live-evidence work.
No AWS resource was changed.

## 111. A Task Definition Is a Recipe, Not a Running Relay

We have now written the source blueprint for the next staging proof. That is a
meaningful step, but it is easy to overstate what it means.

```text
source definition in the repository
              │
              │ reviewed CloudFormation change set
              ▼
task definition registered in AWS
              │
              │ explicit ECS RunTask request
              ▼
one relay process runs one pass
              │
              ▼
process exits
```

The first box is where we are. A task definition is a recipe: which compiled
command to run, which role it receives, how much CPU/memory it may use, which
non-secret configuration it receives, and where its safe operational logs go.
It does not itself start a container.

### Three deliberately different identities

The same persistence workflow needs three processes, but they should not share
one large set of permissions:

| Process | May do | Must not do |
| --- | --- | --- |
| Public server | Atomically accept the harmless work-item state, lineage fact, and outbox obligation. | Read due outbox work, send a queue message, or settle worker delivery. |
| Relay | Query the *due* outbox index, lease one outbox record, and send its safe envelope to the source queue. | Write product state, receive queue messages, or process a business effect. |
| Worker | Receive/settle queue delivery and claim/complete durable processing state. | Search due work or create a new queue message. |

This is called **least privilege**. If a future bug affects the worker, it
cannot silently become a producer. If a public-server bug appears, it cannot
scan outbox work or consume the queue.

### Why query an index instead of scanning a table?

The relay needs only outbox records that are due now. `OutboxDueIndex` is an
organised lookup path for that question. A table scan would inspect unrelated
work-item state, lineage, and processing records, cost more as the table
grows, and demand unnecessarily broad access.

### Safe transition telemetry

The relay and worker now have a small shared catalogue of persistence events,
such as `platform.persistence.outbox.published` or
`platform.persistence.processing.completed`. The accompanying metric adds only
the suffix `.outcome` and retains these labels:

```text
capability, action, execution_context, outcome, error_class
```

It must not place an outbox ID, queue URL, payload, tenant, lease owner,
fence, or attempt number in a metric label. Those facts either identify a
specific record or create unbounded metric-cardinality cost. A safe correlation
reference may exist in a bounded log envelope when its separate profile allows
it, but it does not belong in the metric series.

### Misconception check

“The repository now defines `RelayTaskDefinition`, so the relay is running in
staging.”

No. It only defines the recipe that a reviewed deployment *could* register.
Nothing runs until the target change set is applied and an operator makes a
separate one-shot `RunTask` request. There is intentionally no relay ECS
service and no scheduler yet.

### Study question

Why does the first proof use a one-shot relay task instead of immediately
running a relay forever?

Because the first question is whether one harmless state change can be
accepted, relayed, processed exactly once in effect, and observed safely. A
continuous process creates separate availability, scheduling, recovery, and
cost obligations. We should choose that operating model only after the narrow
path is proven.

Planning triage: the Persistence Foundation v1 plan, platform-runtime plan,
staging readiness record, target profile, infrastructure guide, and static
infrastructure gate now distinguish source-defined relay/worker deployment
from live AWS proof. No AWS resource was changed.

## 112. A Scope Is Also a Permission Boundary for Automation

Before deploying the harmless write route, we inspected Cognito. The existing
machine client can request only `platform-shell/smoke.read`. That is correct for
the scheduled read-health check, but it cannot safely exercise a write route.

It would be tempting to add `smoke.write` to the same client. We are not doing
that. The read client’s secret is deliberately accessible to narrow automated
read checks. Giving that client a write scope would mean that compromise or
mistake in a read-check boundary could request a token that creates a work
item.

```text
read scheduler ── read-only client ── platform-shell/smoke.read

controlled persistence proof ── separate client ── platform-shell/smoke.write
```

The separate write client is still deliberately small: it receives one scope,
its secret stays in its own target-owned secret, and the server accepts its
client ID only after reviewed target configuration. This is an example of
least privilege applying to automation identities, not only to AWS IAM roles.

### Misconception check

“Both clients call the same smoke application, so one client is simpler and
therefore safer.”

No. Simplicity has value, but combining read automation and write authority
increases blast radius. Separate identities make the write path easier to
disable, audit, and reason about without interrupting routine read evidence.

### Study question

Why is the client secret not enough by itself to control write authority?

Because a secret identifies a client; it does not limit what scopes that client
may request. Scope assignment is the separate authorization boundary. A
write-capable secret must therefore be available to fewer workflows and used
only by a fixed, reviewed command.

Planning triage: the new Persistence v1 deployment plan records the live
baseline, expected CloudFormation changes, separate write-client requirement,
rollback, and proof sequence. No AWS resource was changed.

## 113. A One-Shot Write Proof Needs Its Own Identity and Its Own Brake

We have now put two small safety controls into the repository. They do not
change AWS yet. They tell us exactly what a later approved AWS operation is
allowed to do.

```text
source validation
       │
       ▼
separate write-only client ── short-lived token ── POST /smoke/work-items
       │                                                    │
       │                                                    ▼
       └──── service allowlist after reviewed deployment ── 202 Accepted
                                                            │
                                                            ▼
                                                    mark proof complete
                                                    and reject a rerun
```

The first command is a narrow **provisioner**. It has a fixed shopping list:
one Cognito `smoke.write` scope, one confidential client, and one named secret.
It refuses an arbitrary scope such as `admin`, an arbitrary client name, or an
existing resource server that has drifted from the reviewed read-only starting
state. If creating the secret fails after it created the client, it removes
only what it created and restores the read-only scope.

The second command is a narrow **proof runner**. It can neither receive a URL
from a caller nor send a body. It obtains a short-lived write-only token and
makes one fixed request to `POST /smoke/work-items`. Its request ID is fixed,
so the application derives the same work-item identity every time. That gives
us an important safety brake: after a successful proof we record a completed
lifecycle state, and the command refuses to run again rather than treating a
duplicate response as a fresh success.

### Why is the secret recorded in the target profile but not passed to ECS?

The target profile records the **secret reference**—its name, ARN, and safe
delivery rule—so a reviewer can see which isolated proof identity is used. It
does not contain the secret value. The delivery rule says it is for the bounded
proof command only, not an environment variable in the public server, worker,
or relay. The server needs the non-secret client ID in its allowlist to trust a
token from that client; it never needs the client secret to verify a JWT.

### Misconception check

“A fixed request ID makes retries impossible.”

No. Networks can still fail after the server accepts a request. The fixed ID
makes the *application effect* create-once, so the same request can be
recognised rather than creating another work item. The command’s lifecycle
brake adds a separate operational rule: do not casually rerun the live proof.

### Study question

Why must the client be provisioned before the server allowlists its ID?

Because Cognito generates the client ID. The server should trust an explicit
real identifier, not a wildcard or guessed future value. Until the reviewed
server revision includes that exact ID, a valid write token remains
untrusted—and that is the intended fail-closed state.

Planning triage: Persistence Foundation v1 and the staging Persistence v1
deployment plan now own the client lifecycle and fixed proof command. The
target profile and static infrastructure gate enforce the source policy. The
new commands were locally tested only; no AWS resource or data changed.

## 114. A Safe Failure Needs a Private Category, Not a Public Explanation

The first controlled persistence acceptance reached the public server but
returned `503`. A safe aggregate check established that its atomic transaction
did **not** commit, so there was no outbox item to relay and no reason to start
the worker. That stop was successful safety behaviour: the later stages did
not guess that a write had happened.

The useful diagnosis then became limited. The route had reduced its internal
persistence error to a client-safe `503`, but it had not carried the stable
error category into the route's observability profile. The table, required
indexes, task configuration, and task-role permission were all healthy. The
AWS audit trail did not retain this DynamoDB data-plane event. We therefore
knew the write had not committed, but not whether DynamoDB rejected its shape
or the adapter met another provider-side error.

The repair is a deliberately tiny internal lane:

```text
route gets a stable application error code
             │
             ├── HTTP response: 503 + safe public status
             │
             └── observability.errorClass: stable internal category
                                      │
                                      ▼
                         approved log / metric / trace profile
```

`observability.errorClass` is never serialized into the response. It exists so
the server can place one reviewed, low-cardinality category in the signal
profiles already declared for that capability. It may be a code such as
`PLATFORM_PERSISTENCE_WRITE_ATOMIC_FAILED`; it must never be a stack trace,
provider message, request body, identifier, token, or customer value.

### Misconception check

“To diagnose a `503`, return the database exception to the client.”

No. That can expose infrastructure details and potentially sensitive data. The
client needs the outcome and a safe retry/next-step contract. Operators need a
bounded class in private telemetry. Those are different audiences, so they get
different facts.

### Study question

Why was the relay forbidden after the `503` even though the database itself
was healthy?

Because a relay acts on a committed outbox obligation, not on a request that
was merely attempted. The aggregate proof showed no committed transaction, so
there was nothing legitimate to publish. Starting a worker would test a
different system path and could falsely make the failed acceptance look like a
successful delivery.

Planning triage: the contracts/server remediation is locally proven and now
deployed to the reviewed staging server. Fresh approval for one replacement
acceptance request is still required. The previous request is permanently
recorded as failed and non-committing; it is not silently retried.

## 115. Deploying a Diagnosis Repair Is Not Retrying the Business Action

The error-class repair was deployed after the failed write. That deployment
gave the public server new code so a *future* safe failure can be classified in
private telemetry. It did not re-send the earlier request, create a database
record, add an outbox item, or start a worker.

```text
failed write ──> no committed state ──> deploy diagnostic repair
                                           │
                                           └── proves only that future failures
                                               can be classified safely
```

This distinction matters because a deployment proves the application is
running its new version. A persistence proof proves that one particular
transaction committed. They need different evidence. After the deployment we
verified a healthy server, a protected-read `200`, a zero-count worker, empty
queues, and healthy alarms—but none of those facts turns the old `503` into a
successful write.

### Study question

Why does the next write need fresh approval when the repair is now deployed?

Because it is a new state-changing request. The original one-shot allowance
was consumed and did not commit. Treating a replacement as automatic would
hide a new business action behind a diagnostic repair. The safe rule is: deploy
and verify the repair first; then authorize one exact replacement request.

## 116. Logical Deletion Is a Repair State, Not a Retention Policy

When someone presses “delete”, it is tempting to picture this:

```text
record exists  ──delete──>  record disappears forever
```

That is sometimes the right result, but it is not safe as a universal default.
An authorised user can make a mistake, a request can be applied to the wrong
record, and another process may still need to understand that the relationship
used to exist. The reusable Core contract therefore starts with a smaller,
reversible fact:

```text
active record  ──logical delete──>  deleted record
                                      │
                                      ├── within recovery window: may restore
                                      └── after recovery window: evaluate a
                                          separately governed purge decision
```

The `RecordLifecycle` stored beside a product row says either `active` or
`deleted`. A deleted state carries the deletion time, the exact restoration
deadline, and a reference to the retention policy that governed that deletion.
The reference is a reviewed name such as `customer.invoice-retention.v1`; it
is not a hard-coded number copied into every feature.

### What does “eligible for purge” mean?

It does **not** mean “delete now”. The Core helper can return a clear reason:

| Result | Meaning |
| --- | --- |
| `not-deleted` | This is an active record, so purge is not the question. |
| `within-recovery-window` | Keep it recoverable for now. |
| `retention-not-met` | The owning policy says it must be kept longer. |
| `legal-hold` | A legal or investigation hold forbids removal. |
| `eligible` | A separately authorised product purge/anonymisation process may now be considered. |

That final result deliberately does not issue a database delete. Choosing the
actual process requires product data classification, tenant authority,
jurisdiction, erasure requirements, legal holds, backup behaviour, and a
safe provider implementation. Those decisions differ too much to hide inside
a generic helper.

### How does history fit in?

Current lifecycle state answers “is this row active now?” History answers
“what change happened to which revision?” They are related but distinct.

```text
current row:       state = deleted
lineage entry:     action = deleted, revision = 7, cause = event-42
```

Restoring the row similarly creates a bounded `restored` lineage action. The
lineage record contains safe references and allowlisted field names, never a
full copy of the record before and after the change. This is why the existing
`RecordChange` vocabulary contains `created`, `updated`, `deleted`, and
`restored` rather than creating a separate, less protected deletion log.

### Misconception check

“Logical deletion lets us retain every record forever.”

No. It only provides a short repair phase. Retention expiry, privacy erasure,
and legal hold are still binding product policies. A provider TTL is not a
substitute: it can remove data on a provider schedule, but cannot decide
whether a recovery window, legal hold, or authorised erasure process permits
that removal.

### Current proof status

The reusable lifecycle contract and its tests are complete locally. The live
transaction-to-outbox proof is not complete: the one separately approved
replacement request returned a safe `503`, committed no record, left both
queues empty, and had no matching structured server-request observation. The
relay and worker were therefore correctly not started. The next step is a
single **non-mutating write-admission probe** after a reviewed deployment, not
another unreviewed write attempt.

### Study question

Why is `eligible` a decision rather than a command that physically removes a
record?

Because the generic lifecycle layer can know that its recovery and policy
conditions are satisfied, but it cannot know whether the product's legal,
tenant, classification, backup, and erasure obligations have been performed
by an authorised purge process.

## 117. A Diagnostic Probe Can Test the Door Without Entering the Building

We had two failed write attempts. Each was safely non-committing, but the
second did not leave a matching structured server observation. That leaves an
important question unanswered:

> Does an authenticated request reach the application server at all, or does
> it fail earlier at a network/edge boundary?

Sending a third state-changing request just to answer that question would be
poor engineering. Instead, the smoke app has a separate *admission probe*:

```text
write-only token
       │
       ▼
WAF / load balancer / server transport
       │
       ▼
authentication ──> authorisation ──> route validation
                                             │
                                             ▼
                               return 204 immediately
                               (do not call persistence)
```

The route is `POST /smoke/work-items/admission`. It deliberately uses the
same narrow write permission as the real acceptance route, but it accepts no
request body and its handler never calls a repository, transaction, DynamoDB,
outbox, SQS, relay, or worker. The local test checks three things:

1. no token receives `401` and a read-only token receives `403`;
2. the write token receives `204`;
3. the recording atomic writer has no mutation after the request.

The runner is also constrained: no caller can provide a URL, route, scope,
body, request identity, or timeout. Its only permitted live result is a safe
status and rounded latency. It can execute once only after a reviewed immutable
server deployment and health check.

### What a passing probe means

A `204` proves that this exact authenticated request reached the server route
and produced profile-governed telemetry. It does **not** prove a database
transaction, an outbox entry, queue publication, or worker delivery. It merely
makes the next decision rational: if a later, separately governed acceptance
fails, we can focus on the persistence path rather than guessing about ingress.

### Misconception check

“Because it uses the write token, the probe is a write.”

No. Authorisation determines what the caller *may ask to do*; the route’s
implemented effect determines what it *does*. This route needs the write
permission to test the real authorisation boundary, but its bounded handler
performs no state change.

### Study question

Why is a `204` admission result not enough to start the relay?

Because the relay needs a durable outbox obligation. The probe deliberately
creates none, so there is nothing legitimate to publish.

## 118. An API Name Is Not Always an IAM Permission Name

The next acceptance request did reach the application, but returned `503` and
committed nothing. The table count, queues, server, worker, and alarms were
all healthy, so we asked a narrower read-only question: *may the live server
role perform the operation that DynamoDB needs?*

The answer was no: `dynamodb:PutItem` was `implicitDeny`. This feels odd
because the code calls DynamoDB’s `TransactWriteItems` API. The useful rule is:

```text
API request:         TransactWriteItems
transaction members: Put, Put, Put
IAM permissions:     dynamodb:PutItem on the one table
```

IAM authorises the member operations within this transaction, rather than a
permission named after the API request. The correction remains least privilege:
the server receives `PutItem` on the one persistence table, but still cannot
read, query, scan, update, delete, administer the table, or access a queue.

The important safety lesson is sequence. We do not retry the failed identity.
We deploy the narrow policy correction, prove its live IAM decision without
writing data, and only then use a new fixed identity for one final acceptance.

### What the live proof showed

The Foundation update changed the server role in place. The change-set also
listed the deployment role, but only as a dynamic dependency: its existing
policy refers to the server role's ARN, so CloudFormation re-evaluated it even
though its policy text did not change. The direct change was only the
table-scoped `PutItem` permission.

After deployment, IAM answered `allowed` for the active server role and that
one table. The server remained healthy, the dormant worker remained at zero,
both queues were empty, and all five alarms were OK. That is a useful dividing
line: we have proved the *permission*, but not yet the transaction. The next
step is one new acceptance request; only a successful atomic commit can create
the outbox work that a relay may publish.

Planning triage: the [Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md)
owns the staged proof sequence; the staging target profile and infrastructure
gate own the exact runner policy. The probe was deployed through a reviewed
immutable-image service rollout and then returned `204` in 95 milliseconds.
One matching structured application observation arrived. Because the handler
does no persistence work, that result permits one *new fixed-identity*
acceptance request; it is not permission to retry the earlier failed writes or
to start relay/worker processing early.

## Repository Evidence

- [Current session log](../../../commitLogs/2026/sep/23/2026-09-23-14-51-let-s-expand-the-smoke-target-and-work-through-the-remainder/README.md)
- [Core package overview](../../../packages/core/README.md)
- [Core security public entry point](../../../packages/core/src/security/index.ts)
- [Platform contracts README](../../../platform/contracts/README.md)
- [Platform contracts source](../../../platform/contracts/src/index.ts)
- [Platform runtime source](../../../platform/runtime/src/index.ts)
- [Platform server source](../../../platform/server/src/index.ts)
- [Platform server package guide](../../../platform/server/README.md)
- [Platform server source guide](../../../platform/server/src/README.md)
- [Platform observability package guide](../../../platform/observability/README.md)
- [Platform observability source guide](../../../platform/observability/src/README.md)
- [Platform observability public barrel](../../../platform/observability/src/index.ts)
- [Core monitoring vocabulary](../../../packages/core/src/monitoring/index.ts)
- [Platform worker source](../../../platform/workers/src/index.ts)
- [Core persistence source guide](../../../packages/core/src/persistence/README.md)
- [Core persistence public barrel](../../../packages/core/src/persistence/index.ts)
- [Platform persistence source guide](../../../platform/persistence/README.md)
- [Platform persistence public barrel](../../../platform/persistence/src/index.ts)
- [AWS DynamoDB persistence adapter](../../../platform/adapters/aws/persistence/dynamodb/README.md)
- [Kanbien target persistence composition](../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-persistence.ts)
- [Kanbien one-pass relay entrypoint](../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-relay.main.ts)
- [Kanbien durable worker entrypoint](../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-worker.main.ts)
- [Staging persistence table source](../../../infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation/persistence.yml)
- [Persistence Foundation v1 plan](../../../.agentic/03.product/plans/implementation/persistence-foundation-v1.md)
- [Current persistence session log](../../../commitLogs/2026/sep/23/2026-09-23-18-13-record-worker-telemetry-evidence/README.md)
- [Smoke app mount](../../../apps/platform-smoke/src/app.mount.ts)
- [Product harness foundation plan](../../../.agentic/03.product/plans/implementation/product-harness-foundation.md)
- [Platform runtime implementation plan](../../../.agentic/03.product/plans/implementation/platform-runtime-implementation.md)
- [Core-module authoring rule pack](../../../docs/03.product/rule-packs/core/add-core-module.yml)

## Continuation Protocol

After each completed learning chunk:

1. Add a numbered subsection under the relevant lesson or create the next
   numbered lesson.
2. Record the concept, current repository evidence, intended architecture,
   misconception check, and one study question.
3. Triage every new architectural rule, clarification, boundary, ownership
   decision, or deferred obligation. Identify the existing implementation or
   architecture plan that owns it and update that plan in the same learning
   chunk. If it does not change a plan, record the reason explicitly in the
   handbook and session log; do not let the decision exist only in teaching
   notes.
4. If no suitable plan exists, stop before inventing one: identify the missing
   plan owner and obtain direction on whether to create a bounded plan or defer
   the decision.
5. If code changes, record the public-contract impact, verification run, and
   whether the change is committed or only present in the chat worktree.
6. Update the next-lesson queue so the reader can resume without rereading the
   full conversation.
7. Update the linked session log with a short activity entry, including the
   plan path changed or the explicit no-plan-change rationale.

## Revision History

- 2026-09-25: Added the IAM-vocabulary correction lesson after the first fresh
  acceptance safely returned `503` with no commit. It records why a DynamoDB
  `TransactWriteItems` request needs `dynamodb:PutItem` for its all-`Put`
  members and preserves the no-retry sequence.

- 2026-09-25: Recorded the successful no-side-effect admission probe: `204` in
  95 ms, exactly one matching structured application observation, and a
  post-probe healthy server/dormant worker/empty queues/five-healthy-alarms
  preflight. The next stage is one new fixed-identity acceptance, not a retry.

- 2026-09-25: Recorded the completed admission-diagnostic deployment: an
  immutable scan-clean and attested image, a five-change service-only change
  set, healthy `1/1` server, zero worker, empty queues, healthy alarms, and
  successful public health/protected-read checks. The live route is still not
  persistence evidence until its one bounded execution occurs.
- 2026-09-25: Added the write-admission diagnostic lesson. It distinguishes a
  no-side-effect route from a state-changing acceptance, explains why it tests
  the authenticated server boundary first, and records the next governed
  deployment/probe/acceptance sequence.
- 2026-09-24: Added the safe-failure observability lesson. The first bounded
  staging write returned 503 and was proved non-committing with aggregate-only
  evidence; relay and worker execution did not occur. The new route-response
  observability class preserves a bounded internal failure category without
  exposing it to clients. A reviewed remediation deployment and new approval
  remain required before another write attempt.
- 2026-09-24: Added the diagnostic-repair deployment lesson. The scan-clean
  image with the private failure-class seam was deployed and verified through
  a normal server rollout, but no replacement write, relay, or worker action
  occurred. A new explicit one-request approval remains the next boundary.
- 2026-09-24: Added the automation-identity scope lesson and a dedicated
  persistence deployment plan. Read-only inspection confirmed the current
  stacks are healthy, the persistence table is absent as expected, and the
  deployed machine client is read-only. The plan recommends a separate
  write-only client rather than widening synthetic-read authority; no AWS
  resource changed.
- 2026-09-24: Added the source-deployment-definition lesson. It explains why
  an ECS task definition is only a recipe, separates server/relay/worker least
  privilege, explains a due-record index, and records safe persistence metric
  labels. The deployment plans/readiness records now name the required
  reviewed change-set and one-shot live-proof sequence; no AWS resource
  changed.
- 2026-09-24: Added the local persistence vertical-proof lesson. It explains
  the repaired outbox-message/job contract, acceptance-to-relay-to-worker
  flow, durable duplicate skip, and the difference between a compiled
  entrypoint and a deployed target process. The Persistence Foundation and
  platform-runtime plans now record the remaining task/IAM/schedule/live-proof
  work; no AWS resource changed.
- 2026-09-23: Added the persistence-foundation chapter. It records the local
  Core split, immutable outbox/lineage facts, provider-neutral delivery state
  machines, lease/fence rules, and atomic-writer seam. It distinguishes this
  uncommitted local work from the future DynamoDB/SQS smoke proof; no AWS
  resource changed.
- 2026-09-23: Added the outbox-relay continuation. It records the minimal
  stable-ID queue envelope, safe claim/send/publish order, recovery after a
  queue-send failure, and the remaining worker/transport composition. No AWS
  resource changed.
- 2026-09-23: Added the durable-worker continuation. It records the stable
  three-part outbox identity, claim/release/complete ordering, duplicate skip,
  terminal-failure recording, and the remaining transaction/adapter limit. No
  AWS resource changed.
- 2026-09-23: Added the source-defined staging worker extension: a
  provider-neutral worker process, SQS consumer adapter, zero-desired-count
  worker service/queue/DLQ/IAM source, guarded consumer rehearsal, and the
  worker-and-operations closure plan. This remains local source until a
  reviewed change set and bounded live proof complete; it is explicitly not an
  outbox or business persistence implementation.
- 2026-09-22: Promoted the temporary scheduler source to `origin/main` and
  manually dispatched its first run. GitHub run `35711517748` completed from
  source `9ccad368a34684afaa9b7ed64d7dba85f4b3fae8` with the approved redacted
  result: protected request `200` in `266` ms. This proves the controlled path,
  not the first clock-triggered run, telemetry coverage, or a customer SLO.
- 2026-09-22: Created and read back the temporary scheduler's separate AWS IAM
  role. Its main-only GitHub OIDC trust, four ownership tags, and one
  `GetSecretValue` permission exactly match the reviewed source. The workflow
  is still absent from remote `main`, so no scheduled run, secret retrieval,
  or protected request occurred in this IAM step.
- 2026-09-22: Prepared a temporary, target-specific GitHub Actions synthetic
  scheduler source for the controlled protected-route smoke. Its workflow,
  separate main-only OIDC trust policy, one-secret-read IAM policy, and static
  policy gate are source-only and locally verified. Its nominal four-hour
  cadence is explicitly best effort and not SLO/telemetry-coverage proof; no
  IAM role, workflow run, or AWS resource was created in this step.
- 2026-09-22: Applied and query-proved the staging CloudWatch metrics delivery
  slice. The collector sidecar, narrow IAM, enhanced Container Insights, and
  five infrastructure alarms are live; a controlled `200` and denied `401`
  request produced the approved counter and histogram through PromQL. The
  handbook now records the four closure paths: recurring synthetic evidence,
  exporter-loss coverage, bounded public/operational proofs, and a safe
  reusable controlled-token command. SLO confidence and alerting are not yet
  claimed complete.
- 2026-09-22: Prepared the first staging capability-metrics target-composition
  slice. The sealed target runtime injects the AWS OpenTelemetry adapter only
  as Core `Metrics`; CloudFormation source adds non-secret SSM collector
  configuration, a task-local ADOT sidecar, distinct collector logs, task
  capacity, and narrow execution/task-role source policies. The adapter and
  source checks pass locally. No AWS resource, IAM policy, task definition,
  collector, metric, dashboard, SLO query, or alarm was deployed.
- 2026-09-22: Separated image publication from service deployment. The GitHub
  workflow can publish a scanned, attested immutable ECR digest but is checked
  to contain no CloudFormation or ECS mutation command. A reviewed,
  explicitly approved CloudFormation change set remains required for a running
  service change; the live GitHub IAM role still needs its separately governed
  narrowing update.
- 2026-09-21: Added the observability delivery-readiness roadmap. The local
  instrumentation slice is distinguished from the policy, adapter, target,
  public synthetic, coverage, and alert-delivery proofs required for an
  operational target claim. No provider or target state changed.
- 2026-09-21: Added the observability data-lifecycle lesson. Retention,
  access, residency, and sampling are now separated by evidence class; the
  current 14-day staging log retention is explicitly not a universal policy.
  No telemetry store or target retention value was selected.
- 2026-09-21: Added the dashboard and synthetic-check lesson. Future target
  policy must distinguish healthy, partial, and no-data evidence; it must keep
  platform, capability, and security views separate, and use safe
  least-privilege synthetic checks during low traffic. No provider resource was
  selected.
- 2026-09-21: Added the histogram-exporter lesson. A future target-composed
  Core metrics adapter must use an approved metric-series catalogue,
  threshold-aligned buckets, bounded delivery, and explicit evidence-coverage
  handling before it can support SLO claims. No provider was selected.
- 2026-09-21: Added the complete target SLO-record lesson. A later
  `observability.slos` catalogue will own each objective's meaning and
  calculation, while the existing alarm catalogue remains the provider-delivery
  and IaC source. No target SLO configuration or provider resource changed.
- 2026-09-21: Added the alert-family lesson. Capability SLO, platform or
  infrastructure health, and security alerts now have distinct policy homes,
  owners, and primary questions; existing staging alarms cover only the
  infrastructure family. No target alarm or provider state changed.
- 2026-09-21: Added the error-budget and burn-rate lesson. The target-policy
  plan now requires separate objective budgets, sustained short/long-window
  alerting, a minimum eligible sample, and a synthetic-check fallback for
  low-volume periods. No numeric target or provider implementation changed.
- 2026-09-21: Clarified that existing HTTP transport timeouts are safety and
  capacity guardrails, not interactive-performance promises. The platform plan
  now reserves a later target-owned timeout-budget catalogue, including nested
  deadline ordering and separate provider-worker execution/lease policy. No
  runtime timeout configuration or target infrastructure changed.
- 2026-09-21: Completed the matching provider-neutral HTTP profile-consumption
  slice. A matched route now emits only profile-approved logs, metric labels,
  traces, and declared request/response timing; known opt-outs emit no
  capability telemetry. The lesson distinguishes known capability attempts
  from generic server/transport operations, and the platform plan records the
  same boundary. No provider exporter, cloud resource, audit pipeline, or
  security-record pipeline was selected.
- 2026-09-21: Implemented the first profile-consumption vertical slice. The
  worker now resolves registered job profiles, emits only approved canonical
  facts and declared latency intervals, suppresses capability telemetry for an
  explicit opt-out, and keeps logger/metrics/tracer failure best effort. The
  contracts, observability, and worker checks passed locally. Server profile
  consumption, provider export, durable audit/security evidence, and target
  NFR/SLO policy remain deferred.
- 2026-09-09: Selected DynamoDB on-demand only for the future harmless
  platform-smoke transaction/outbox reference proof. The lesson separates that
  low-cost operational decision from the still-deferred Entity Builder
  persistence choice. At that point, relay transport, AWS resources, and
  product data remained unselected. No runtime source or AWS resource changed.
- 2026-09-09: Selected SQS Standard with a DLQ as the first relay transport for
  that smoke proof. Added the five-record/outbox, idempotency, state/fencing,
  and target-owned queue-policy lessons. EventBridge, FIFO ordering, adapters,
  target resources, and AWS mutation remain deferred.
- 2026-09-09: Added the worker-completion and DLQ-quarantine lessons. The
  platform plans now require durable completion before queue acknowledgement,
  duplicate/lease safety, bounded failure classification, and manual linked
  DLQ recovery for the smoke proof. No runtime source or AWS resource changed.
- 2026-09-09: Added the capability-versus-platform coordination lesson. Apps
  now declare a named delivery policy and business idempotency/transition
  meaning; platform workers own generic lease and fencing mechanics. Normal
  entity edits continue to use revision-based concurrency unless a separate
  restartable workflow needs exclusive processing.

- 2026-09-01: Created from the architecture tutoring session. Covers the
  completed core/security and platform/contracts lessons; future lessons will
  be appended rather than rewritten.
- 2026-09-06: Added the deployment-artifact lesson after a strict runtime probe
  caught an internal adapter resolving from workspace TypeScript rather than
  the compiled image payload. The platform plan and target readiness record
  now distinguish compiled-runtime proof from an unavailable Docker-engine
  smoke test; no AWS resource was changed.
- 2026-09-01: Added the proposed natural-topic grouping for
  `platform/contracts`. This is a design decision record, not a source-file
  refactor.
- 2026-09-01: Added a first-time-learner explanation of every proposed
  `platform/contracts` grouping, including misconceptions and an end-to-end
  recap. No source files moved.
- 2026-09-01: Added the proposed one-way dependency map for the platform
  contract topics, including a worked invoice-route example and why cycles are
  harmful. No source files moved.
- 2026-09-01: Added a proposed semantic naming profile for app-owned platform
  contributions and permissions. It separates stable capability names from
  tenant, role, group, provider, and version policy facts. No rule or source
  change has been made.
- 2026-09-01: Added a selective codebase scanability roadmap with priority
  candidates, security/operational risks, and a safe adoption sequence. No
  source files moved.
- 2026-09-01: Added the category-prefix lesson. It keeps functional category in
  file/type/field context and reserves identifier values for stable ownership
  and capability; no rule or source change has been made.
- 2026-09-01: Identified the existing platform-contract boundary rule as the
  future home for the semantic naming profile. The profile remains a proposal
  until it is deliberately codified and then implemented separately.
- 2026-09-01: Codified the platform-contract identifier naming profile through
  source material, an accepted two-iteration source review, derivation report,
  generated provenance, and a focused retrieval fixture. Runtime enforcement
  remains explicitly deferred to a later compatibility-preserving slice.
- 2026-09-01: Added the app-mount and registry lesson. It explains the
  startup-time declaration catalogue, local and cross-declaration validation,
  the server/worker handoff, and why future app-ownership naming validation
  belongs at this boundary. No runtime source files changed.
- 2026-09-01: Added the registered-job and worker lesson. It traces message
  dispatch, payload validation, idempotency, tenant context, handler execution,
  retries, dead letters, and the local queue's delayed-delivery limitation. No
  runtime source files changed.
- 2026-09-03: Added a field-by-field, focused security-assessment example for
  Bill's invoice export. It distinguishes an assessment record from a security
  guarantee, explains the evidence and outcome fields, and keeps sensitive
  runtime data and raw scanner output out of Git. No runtime source files
  changed.
- 2026-09-03: Added the review-depth triage lesson. It separates the author's
  proposal, predictable automated signals, and independent reviewer challenge;
  it also marks the general classifier and merge machinery as future
  feature-harness work. No runtime source files changed.
- 2026-09-04: Added the security-log, audit-event, and operational-observability
  lesson. It applies all three records to Bill's invoice export, distinguishes
  their audiences and data needs, and records the current audit-store and
  observability boundaries as future work. No runtime source files changed.
- 2026-09-04: Added the ownership map for those records: Core owns vocabulary
  and ports, platform owns runtime wiring and the future durable audit recorder,
  adapters own provider translation, infrastructure owns resources and
  lifecycle, and apps select product actions that require audit. No runtime
  source files changed.
- 2026-09-04: Corrected the ownership map to distinguish implemented contracts
  and helpers from absent runtime emitters, durable recorders, and provider
  sinks. It now shows the separate future writing paths for security logs,
  audit events, and operational records. No runtime source files changed.
- 2026-09-04: Added the audit-integrity lesson. It separates append-oriented
  history from retention/deletion decisions, distinguishes tamper-resistant
  from tamper-evident controls, and explains why runtime audit evidence cannot
  live in Git or ordinary logs. No runtime source files changed.
- 2026-09-04: Extended the audit-integrity lesson with the practical control
  stack: separated access, immutable retention, hashes, signatures, chained or
  anchored digests, and scheduled verification. It explains why a nearby hash
  alone is not trustworthy. No runtime source files changed.
- 2026-09-04: Added the blockchain comparison. A signed audit-integrity chain
  shares a hash-linking idea with a blockchain but does not require distributed
  consensus, cryptocurrency, proof-of-work, or a public network. No runtime
  source files changed.
- 2026-09-04: Added the audit-policy lesson. It uses a risk-based selection
  test, Bill's invoice examples, and explicit app/product/tenant/platform/infra
  ownership to distinguish meaningful accountability records from routine
  telemetry. No runtime source files changed.
- 2026-09-04: Extended the audit-integrity lesson with retention guidance:
  audit is usually longer-lived than troubleshooting logs but not automatically
  permanent; purpose, event class, jurisdiction, access, expiry, and legal hold
  require an explicit lifecycle policy. No runtime source files changed.
- 2026-09-04: Added the denied-and-failed-action lesson. It separates
  accountability, security signals, and technical diagnosis, and applies the
  distinction to anonymous, denied, failed, and repeated invoice-export cases.
  No runtime source files changed.
- 2026-09-04: Added the audit-data-minimisation lesson. It separates the safe
  facts needed to explain Bill's invoice export from credentials, raw payloads,
  business data, diagnostics, and channel content that must not enter durable
  audit metadata by default. No runtime source files changed.
- 2026-09-04: Expanded the audit-data-minimisation lesson with a value-by-value
  explanation of credentials, business data, raw payloads, diagnostics,
  conversational content, and signed URLs, plus the safer references to retain.
  No runtime source files changed.
- 2026-09-04: Added the reusable audit-event standard: a fixed accountability
  envelope plus a versioned, action-specific allowlist profile, enforced before
  persistence rather than through a free-form metadata field. No runtime source
  files changed.
- 2026-09-04: Clarified that a capability declares separate audit,
  observability, and security-log profiles. They share only safe stable
  references for correlation, rather than copying one profile's metadata into
  every record system. No runtime source files changed.
- 2026-09-04: Added the audit actor/target lesson. It distinguishes verified
  human, service, anonymous, and system actors; bounded resource and bulk
  targets; tenant/scope context; and the future need for an explicit delegation
  model when an agent or worker acts for a person. No runtime source files
  changed.
- 2026-09-04: Added a proposed v1 audit taxonomy. It separates event type,
  version, actor type, interaction channel, execution context, outcome, and
  target, with a small controlled verb vocabulary and an explicit future
  governance/validation step before enforcement. No runtime source files
  changed.
- 2026-09-04: Added the correlation-and-causation lesson. It separates one
  logical workflow from its direct parent-child relationships, traces Bill's
  queued invoice export, distinguishes retries and idempotency, and records the
  current propagation gap as future platform work. No runtime source files
  changed.
- 2026-09-04: Added the planning-triage rule for this learning session. Every
  architectural clarification now updates its owning plan in the same chunk or
  explicitly records why no plan change is needed; the retry causal-chain
  requirement is recorded in the platform-runtime plan. No runtime source files
  changed.
- 2026-09-04: Added the retry/delivery-attempt/idempotency lesson. It explains
  why at-least-once delivery needs both retry and duplicate-effect protection,
  distinguishes current test-shell behaviour from exactly-once processing, and
  records the required future idempotency-boundary design in the platform plan.
  No runtime source files changed.
- 2026-09-04: Added the platform-contracts refresher. It distinguishes Core
  vocabulary, app-facing platform integration contracts, runtime mechanics, and
  app-owned product meaning; it explains why topic grouping precedes the safe
  source-file split. Planning triage confirmed no plan change because the
  refresher restates the existing public-contract direction.
- 2026-09-04: Added the capability-declaration lesson. It separates runtime
  registrations from app/product capability meaning, policies, safe record
  profiles, and bounded LLM discovery metadata. Planning triage added the
  deferred capability-declaration profile to the product-harness plan; no
  runtime contract, provider, or product feature was implemented.
- 2026-09-04: Added the record-profile clarification. It separates the safe
  field allowlists for audit, security signals, and operational observability,
  and adds field purpose, classification, bounds, audience, and
  retention/residency requirements to the planned capability-declaration
  profile. No runtime record pipeline or feature was implemented.
- 2026-09-04: Confirmed the platform-contract source topic map against the
  current entry point. It separates errors, identifiers, flags, contexts,
  routes, jobs, app mounting/registration, and validation while preserving one
  public barrel. The exact map and compatibility requirements are now in the
  platform-runtime plan; no source file has moved.
- 2026-09-04: Clarified the boundary of the platform-contract topic map. It
  covers current app-to-runtime registrations only; Core, platform record
  pipelines, product capability declarations, tenant policy, and infrastructure
  continue to own the broader concerns discussed in the lessons. The
  platform-runtime plan now names those non-goals explicitly.
- 2026-09-01: Added the deferred DLQ remediation lesson and recorded a bounded
  platform-plan capability. It begins with read-only, redacted diagnosis and
  supervised recommendations; future automated replay is policy-controlled,
  tenant-safe, allowlisted, auditable, rate-limited, and stoppable. No runtime
  source files changed.
- 2026-09-01: Added the first platform-server lesson. It explains server
  startup validation, request preparation, route matching, and why a route
  match is not an authorization decision. No runtime source files changed.
- 2026-09-01: Added the authentication lesson. It distinguishes a missing or
  invalid identity (401) from a known caller lacking a route permission (403),
  explains provider-neutral principal creation, and records that protected
  handlers do not run in either case. No runtime source files changed.
- 2026-09-01: Added the tenant and resource-authorization lesson. It separates
  broad permissions from tenant scope, resource references, and policy facts;
  explains the fail-closed tenant gate and deliberate 403 versus 404 resource
  disclosure decision. No runtime source files changed.
- 2026-09-01: Added the request-completion lesson. It distinguishes route-shape
  validation from business validation, explains safe 400 and 500 error mapping,
  and records the shared logging and metrics trail around every response. No
  runtime source files changed.
- 2026-09-01: Added the server-lifecycle lesson at a slower, more detailed
  pace. It explains pre-listen validation, liveness versus readiness, health
  exposure policy, and ordered graceful shutdown. No runtime source files
  changed.
- 2026-09-01: Added the worker-lifecycle lesson at the same slower pace. It
  compares HTTP request delivery with queued-message delivery, traces startup,
  dispatch, idempotency, retry, dead letter, and shutdown, and explicitly
  separates the current deterministic in-memory worker shell from future
  provider polling and in-flight drain mechanics. No runtime source files
  changed.
- 2026-09-02: Added the request-versus-job authority lesson. It distinguishes
  an authenticated human principal from a tenant-scoped, durable workflow;
  records the current absence of worker-side group, role, permission, and
  resource authorization; and explains why execution-after-revocation must be
  an explicit product policy. No runtime source files changed.
- 2026-09-02: Added the platform-adapter lesson. It traces the implemented
  Cognito adapter from provider issuer, token, and claim details through the
  provider-neutral authentication hook to the target composition root; it also
  distinguishes current adapter evidence from future directory conventions.
  No runtime source files changed.
- 2026-09-02: Added the first platform-security boundary lesson and the package
  documentation lesson. The package documentation convention is now codified
  as a source-reviewed product-wide concern; it uses one canonical rule with
  layer references and stages README adoption as packages are changed.
- 2026-09-02: Added the JWT authentication-path lesson. It traces bearer
  extraction through token verification, provider-specific claim requirements,
  and principal creation; it also distinguishes invalid-token denial from an
  identity-provider key-fetch dependency failure. No runtime source files
  changed.
- 2026-09-02: Extended the JWT lesson with `kid` and signature-verification
  illustrations, then added the claims-to-permissions lesson. It separates
  trusted group/scope facts, configurable permission mapping, route permission
  checks, and later tenant/resource policy. No runtime source files changed.
- 2026-09-02: Added the browser-boundary and request-pressure lesson. It
  distinguishes exact-origin CORS, JSON API security headers, and the current
  in-memory rate-limit baseline from authentication, authorization, TLS, and
  distributed availability controls. No runtime source files changed.
- 2026-09-02: Codified the source-reviewed untrusted-input and bounded-agent
  safety policy, its focused product workflow, layer references, retrieval
  fixture, and generated recognition coverage. It governs future code-injection
  and prompt-injection boundaries without claiming a general agent runtime or
  approval service already exists.
- 2026-09-02: Added the security-assessment-depth lesson. It distinguishes the
  baseline check from focused and deep review, then uses trust boundaries and
  blast radius to decide the appropriate depth for a change. No runtime source
  files changed.
- 2026-09-02: Added the focused-security-assessment lesson. It defines the
  five-part change/risk/control/proof/outcome record and works through an
  invoice-read route without turning a normal feature review into a broad
  compliance exercise. No runtime source files changed.
- 2026-09-02: Added the security-assessment lifecycle lesson. It separates
  asking questions before code, proving controls during implementation/review,
  and recording policy, per-change evidence, and repository posture in distinct
  locations. It explicitly labels the central evidence schema/store/index as
  future work rather than current compliance evidence.
- 2026-09-07: Added the observability continuation: separate evidence records,
  allowlisted facts, canonical action/source/outcome terminology, safe metric
  cardinality, tenant-scoped investigation boundaries, and trace/sampling
  rules. The platform-runtime and product-harness plans now capture the
  implementation obligations; no record pipeline or provider adapter was
  claimed as implemented.
- 2026-09-07: Applied the observability source-organisation decision. The
  provider-neutral helper now has separate normalisation, logging, metrics,
  and tracing files, with package and source responsibility maps; its public
  barrel and its provider/pipeline status are unchanged.
- 2026-09-07: Added the first provider-neutral tracing slice. Core monitoring
  now has scanable health, metrics, signal, trace, identifier, and validation
  topics; the server starts and completes a safe request span through a
  no-op/in-memory-capable port. No trace provider, exporter, remote-context
  propagation, sampling policy, or durable record store was selected.
- 2026-09-25: Added the atomic-acceptance-to-delivery boundary. One successful
  write proves an atomic business-state, lineage, and outbox transaction; it
  does not prove that a background process has delivered the work. The next
  governed proof therefore starts one relay task for the one recorded outbox
  obligation, then temporarily wakes the existing worker. Its preconditions,
  action limits, terminal counts, and redaction rules are all target policy,
  so the command cannot be repurposed into a general queue tool or scheduler.
- 2026-09-07: Added the queued-work lineage continuation. Queue messages now
  preserve an optional internal trace parent; the worker creates a bounded job
  span and records its input message as the runtime job's direct cause. The
  plan now captures the deferred logical-deletion and protected
  record-change-history requirements. The worker source is organised by
  errors, contracts, queue mechanics, and delivery execution; provider,
  producer/outbox, persistence, and exporter decisions remain deferred.
- 2026-09-07: Added the observability-delivery lesson. It distinguishes the
  current target's ECS stdout-to-CloudWatch operational-log route and native
  infrastructure metrics/alarms from missing application metric/trace,
  security-record, audit, and WAF-request-log pipelines. No provider contract
  or AWS state changed; the existing target baseline already owns the gaps.
- 2026-09-07: Added live, read-only target evidence to the observability
  lesson. It confirms recent CloudWatch log delivery, healthy ECS desired versus
  running count, two ALB alarms in `OK`, and a confirmed SNS email subscription.
  It also records the target-profile mismatch: three required ECS alarms are
  not yet present in CloudFormation or AWS. The staging readiness manifest,
  rather than the generic platform plan, owns that deployment gap.
- 2026-09-07: Added the provider-neutral port lesson. It distinguishes the
  Logger, Metrics, and Tracer contracts, explains why stdout collection is a
  target facility rather than a generic CloudWatch dependency, and preserves
  the future AWS observability-adapter boundary for a deliberately selected
  metrics or trace delivery use case.
