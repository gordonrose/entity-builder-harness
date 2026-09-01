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
11. [Next lesson queue](#11-next-lesson-queue)

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
`docs/harness/architecture/rules/layers/platform.yml`. That rule already says
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
`docs/harness/architecture/rules/layers/platform.yml`. Its source material,
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
| `platform/security` | 661-line source file | authentication/JWT, authorization mapping, CORS, headers, rate limiting, errors | High value, but security behaviour must not change during a structural refactor |
| `platform/runtime` | 509-line source file | registry, app mounting, contexts, lifecycle | Good second platform candidate after contracts |
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

## 11. Next Lesson Queue

1. Follow one registered route through the server request pipeline.
2. Contrast tenant and authorization facts in a route with those in a queued
   job.
3. Confirm the proposed `platform/contracts` topic names and ownership before
   changing files.
4. If approved, make the file split while preserving the public package import
   and its existing proof.
5. Plan registry-level namespace validation and contract tests in a separate,
   compatibility-preserving implementation slice.
6. Map `platform/security` responsibilities and its security-preserving
   refactor constraints.
7. Continue through platform runtime, server, adapters, apps, product, and
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
- [Core-module authoring rule pack](../../../docs/harness/architecture/rule-packs/add-core-module.yml)

## Continuation Protocol

After each completed learning chunk:

1. Add a numbered subsection under the relevant lesson or create the next
   numbered lesson.
2. Record the concept, current repository evidence, intended architecture,
   misconception check, and one study question.
3. If code changes, record the public-contract impact, verification run, and
   whether the change is committed or only present in the chat worktree.
4. Update the next-lesson queue so the reader can resume without rereading the
   full conversation.
5. Update the linked session log with a short activity entry.

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
