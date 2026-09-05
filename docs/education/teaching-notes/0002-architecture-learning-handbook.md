<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.teaching-notes.0002-architecture-learning-handbook
  version: 1
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

Every return path reaches the server's finishing step. It measures latency,
records a request metric with the route and status, and writes a structured log
using the request's correlation id. This means an allowed 200 response, a 400
validation failure, a 403 authorization failure, and a 500 handler failure
all leave an operational trail without asking every app handler to remember
how to log them.

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
response policy for exact allowed origins; it does not yet implement explicit
`OPTIONS` preflight handling. A browser-facing target that needs non-simple
cross-origin requests needs that further work, tests, and a deliberate
credential policy. In particular, a real credentialed browser policy should
use named allowed origins, never a casual wide-open origin.

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
3. Otherwise, use the first `x-forwarded-for` address, then `x-real-ip`.
4. If none is available, share the `anonymous` bucket.

There is a subtle implementation detail worth noticing. The current server
performs rate limiting *before* authentication, so its present request path
passes headers only to the key selector. That means the raw-token hash, IP, or
anonymous paths are used today; the authenticated `rateLimitKey` branch is a
capability for a later arrangement that has already established identity.

This baseline is valuable but has limits:

- It is per process. Two server instances each have their own counters, and a
  restart forgets the old counters. A shared/distributed limiter is needed when
  limits must apply across instances.
- A fixed window permits a boundary burst: a caller can use their quota at the
  end of one minute and again immediately at the start of the next.
- Forwarded-IP headers are trustworthy only when the service is behind a
  trusted proxy that overwrites or normalizes them. A directly reachable
  service must not treat arbitrary client-supplied forwarding headers as fact.
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

This is a **proposal**, not an enforced repository rule yet. Before locking it,
we should reconcile it with the existing semantic identifier policy, make it a
versioned Core/product taxonomy, define extension ownership, and add validators
and fixtures. The feature harness can then require capabilities to select from
it rather than inventing names freely.

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

## 44. Next Lesson Queue

1. Map future queue-adapter requirements from the worker's provider-neutral
   queue boundary and its safe shutdown policy.
2. Continue through platform runtime, server, adapters, apps, product, and
   infrastructure at the learner's pace.

## Repository Evidence

- [Current session log](../../../commitLogs/2026/aug/31/2026-08-31-01-11-product-harness-foundation-plan/README.md)
- [Core package overview](../../../packages/core/README.md)
- [Core security public entry point](../../../packages/core/src/security/index.ts)
- [Platform contracts README](../../../platform/contracts/README.md)
- [Platform contracts source](../../../platform/contracts/src/index.ts)
- [Platform runtime source](../../../platform/runtime/src/index.ts)
- [Platform server source](../../../platform/server/src/index.ts)
- [Platform worker source](../../../platform/workers/src/index.ts)
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

- 2026-09-01: Created from the architecture tutoring session. Covers the
  completed core/security and platform/contracts lessons; future lessons will
  be appended rather than rewritten.
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
