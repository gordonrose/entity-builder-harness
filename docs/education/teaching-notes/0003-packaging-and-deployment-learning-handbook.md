<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: education.teaching-notes.0003-packaging-and-deployment-learning-handbook
  version: 21
  status: active
  created_on: "2026-10-07"
  updated_on: "2026-10-20"
  layer: 05.education
  domain: education
  disciplines:
  - architecture
  - security
  - sre
  kind: guide
  purpose: Record a printable, incremental learning handbook for building a strong packaging and deployment pipeline from current repository evidence.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Packaging and Deployment Learning Handbook

> A living, printable study guide derived from the deployment learning session.
> It records decisions, real repository examples, and open questions rather
> than a verbatim chat transcript. Append one lesson chunk at a time as the
> work continues.

## How to Use This Handbook

Read one numbered lesson at a time. Each lesson separates:

- **Current state** — what the repository demonstrably contains today.
- **Architecture intent** — an agreed direction that may not be implemented
  yet.
- **Misconception check** — a tempting but inaccurate simplification.
- **Study question** — a quick way to check understanding.

This distinction matters. A planned scope record or check is not evidence that
the repository already has one. The current source files and their linked
checks remain the evidence.

## Learning Map

1. [The deployment journey](#1-the-deployment-journey)
2. [Target, scope, and workload](#2-target-scope-and-workload)
3. [The exact package: image tags and digests](#3-the-exact-package-image-tags-and-digests)
4. [What it means for a server to be healthy](#4-what-it-means-for-a-server-to-be-healthy)
5. [Configuration: instructions for a running program](#5-configuration-instructions-for-a-running-program)
6. [Permissions: the running program's keycard](#6-permissions-the-running-programs-keycard)
7. [How configuration completeness is established](#7-how-configuration-completeness-is-established)
8. [Why `workload-iam.yml` and `service.yml` are connected](#8-why-workload-iamyml-and-serviceyml-are-connected)
9. [From a scattered tree to a scannable deployment architecture](#9-from-a-scattered-tree-to-a-scannable-deployment-architecture)
10. [A visible module configuration surface](#10-a-visible-module-configuration-surface)
11. [Foundation resources, scopes, and provider selection](#11-foundation-resources-scopes-and-provider-selection)
12. [Where rules, decisions, and runtime evidence live](#12-where-rules-decisions-and-runtime-evidence-live)
13. [Dependencies and availability behaviour](#13-dependencies-and-availability-behaviour)
14. [Networking: reaching a dependency](#14-networking-reaching-a-dependency)
15. [Safe diagnostics: useful errors without leaks](#15-safe-diagnostics-useful-errors-without-leaks)
16. [Identity, authentication, authorisation, and workload access](#16-identity-authentication-authorisation-and-workload-access)
17. [Observability and alerts](#17-observability-and-alerts)
18. [Target alignment and drift](#18-target-alignment-and-drift)
19. [Defining a scope's responsibilities](#19-defining-a-scopes-responsibilities)
20. [Package publication and custody](#20-package-publication-and-custody)
21. [Foundation bootstrap and existing product work](#21-foundation-bootstrap-and-existing-product-work)
22. [Next lesson queue](#22-next-lesson-queue)

## 1. The Deployment Journey

### The main mental model

```text
platform capability
  → provider adapter, if one is selected
  → runnable program
  → container image command
  → published immutable image
  → target workload
  → required configuration, permissions, dependencies, and proof
  → target-alignment comparison
```

The chain answers one question at each step: does the next stage receive the
right thing, in the right form, with enough evidence to trust it?

### Current state

The repository has parts of this chain: platform code, entrypoints, image
builds, a GitHub image-publication workflow, AWS CloudFormation declarations,
and local and live smoke checks. They are useful but currently distributed
across several directories and are not yet collected into one scope-level
evidence record.

### Architecture intent

The deployment-control plan will make these links explicit and checkable one
bounded scope at a time. It will not claim full target coverage until every
active required scope has fresh evidence.

### Misconception check

“A successful image build means the application has been deployed.”

No. Building creates a candidate package. Publishing stores it. Deployment
selects it for a target workload. Live verification confirms what actually ran.

### Study question

Which step proves that the image currently running in AWS is the same exact
package that was tested locally?

Answer: the workload must be bound to the tested immutable image digest, and a
live check must compare the running workload's image reference with that
digest.

## 2. Target, Scope, and Workload

### The main mental model

```text
target = real destination
scope = bounded capability we can declare and prove
workload = a concrete running program in that target
```

For example, Kanbien staging is a target. The public platform server is an
initial deployment scope. The ECS public-server service and its running tasks
are workloads used to realise that scope.

### Current state

The staging target is described under
`infra/04.deploy/03.product/targets/kanbien/staging/`. The current declaration
contract covers a narrow public-server baseline and explicitly excludes several
concerns such as PostgreSQL, workers, identity provisioning, ingress, and
observability delivery.

### Architecture intent

A future target-local scope index will list active scopes, their owners,
dependencies, contracts, and proof paths. An alignment result will always be
scope-qualified: it will say what it covers and what it does not.

### Misconception check

“A platform module is automatically a deployment scope.”

No. A platform module can support several scopes. A scope is separated when
its runnable process, target prerequisites, evidence, recovery behaviour, or
lifecycle differs.

### Study question

Why might a public server and a background worker be separate scopes even when
they share platform code?

Answer: they can have different commands, permissions, dependencies, health
signals, failure modes, and deployment/recovery paths.

## 3. The Exact Package: Image Tags and Digests

### The main mental model

```text
tag    = a moveable label, such as "staging" or "latest"
digest = the permanent fingerprint of one exact image
```

Use the digest when deciding what to run. A tag may later point at a different
image; a digest cannot.

### Current state

The staging service template requires an image reference in
`repository@sha256:...` form. The existing GitHub publication workflow builds,
tests, scans, publishes, and resolves an immutable digest in ECR. It publishes
the package; it does not by itself deploy it to ECS.

### Misconception check

“The tag used during testing identifies the tested package forever.”

No. A tag is a signpost that can be moved. The digest is the sealed-package
identity needed for reliable deployment and rollback.

### Study question

What is the safe handoff between image testing and deployment?

Answer: record and pass the tested digest, not only a human-friendly tag.

## 4. What It Means for a Server to Be Healthy

### The main mental model

```text
process running
  → port listening
  → /livez responds
  → /readyz accepts normal traffic
  → safe meaningful request succeeds
```

Each step proves more than the one before it.

| Check | What it proves | What it does not prove |
| --- | --- | --- |
| Process is running | The program did not immediately stop. | It can accept useful work. |
| Port is listening | The server opened its expected door. | The application is ready. |
| `/livez` | The process is alive enough to respond. | Dependencies or normal traffic are ready. |
| `/readyz` | The server says it can serve ordinary traffic. | A meaningful protected action works. |
| Safe real request | Important user-facing behaviour works. | Every possible feature works. |

### Current state

The repository contains local image smoke checks for `/livez` and `/readyz`,
ECS and load-balancer health declarations, an ingress smoke check, and a
controlled protected-route smoke check. They are not yet assembled into a
single formal health-evidence record for the public-server scope.

### Different failures need different responders

| Observed problem | Safe immediate response | Primary responder |
| --- | --- | --- |
| Process crashes or freezes | Replace the task. | ECS or equivalent workload runtime. |
| Required dependency is temporarily unavailable | Stay alive if safe, become not-ready, and give a safe diagnostic. | Application. |
| One ordinary request fails | Reject that request honestly; do not automatically take down the server. | Application. |
| New release cannot become ready or verify | Reject the candidate and preserve the prior healthy release. | Deployment mechanism. |

This separates **recovery** from **rollback**. Recovery keeps the intended
release and restores it after a temporary problem. Rollback stops using a new
release because evidence indicates that the release itself is unsafe.

```text
temporary database outage while version A is running
→ A becomes not-ready
→ dependency returns
→ A proves readiness and resumes

new version B fails verification
→ reject B
→ restore prior tested version A
→ verify A again
```

### Accepting or rejecting a deployment candidate

A release needs a decision window: a declared startup grace period and
deadline. It is accepted only when the target proves the selected immutable
image digest is running at the required healthy capacity, passes liveness and
readiness, remains stable for that window, and passes a meaningful operation
check. It is rejected if it misses the deadline, repeatedly stops, fails a
required check, or reports a declared blocking diagnostic.

During a gradual rollout, old version A and new version B may run together.
Traffic must reach only ready tasks, and healthy A tasks stay available until
B has earned further rollout. A simple initial policy can keep the old healthy
task serving until its replacement has become ready and passed verification.

### Meaningful and candidate-specific verification

A meaningful verification proves a small, safe, deterministic operation tied
to a scope promise. It should not alter real user data or claim to test every
feature. Its response must also identify the candidate release, because a
shared load-balancer route can otherwise return a healthy response from old
version A while version B is broken.

```text
successful smoke response
+ observed release identity equals selected image digest B
= candidate B was verified
```

The scope may use a candidate-aware response, a candidate-specific route, or
provider deployment-controller evidence combined with an application check.
Any release identity returned by an endpoint must expose only approved safe
metadata.

### Receipts and rollback proof

Each deployment verification produces a safe receipt, for example:

```text
scope, target, candidate digest, workload revision, verification operation,
time, result, observed release identity, health state, diagnostic code when
needed, and an evidence reference
```

Initially, a GitHub Actions deployment run stores the receipt as a
machine-readable artifact and a human-readable job summary. Git stores the
requirement and the safe evidence reference, not the receipt. A later durable
operational evidence store can replace or supplement that route only after its
retention, access, independence, and bootstrap behaviour are reviewed.
Application persistence is not automatically suitable: deployment evidence may
be needed to prove that the persistence capability itself was safely deployed.

Rollback always selects the recorded prior **immutable digest**, never a
movable tag. It is complete only after the restored digest is running at the
required healthy capacity and passes readiness plus the meaningful verification
again. The rejected candidate's safe failure evidence is retained so the same
broken release is not blindly retried.

### Misconception check

“The container is running, so the service is healthy.”

No. A running container can still have the wrong command, port, configuration,
permissions, or application behaviour.

### Study question

Why should `/livez` and `/readyz` normally be different checks?

Answer: a process can be alive while it is not yet ready to serve normal
traffic, for example while starting required components or draining during
shutdown.

## 5. Configuration: Instructions for a Running Program

Configuration tells a program what to use and how to behave in a particular
target without changing its fundamental code.

### When configuration is appropriate

Use configuration when a fact varies by target, selects an external
dependency, controls approved operating behaviour, chooses an integration, or
is sensitive. Examples in the staging service declaration include the port,
the authentication provider, DynamoDB resource names, request timeouts, health
exposure, and the required `PLATFORM_SMOKE_APP_NAME` product setting.

Keep a fact in code when it is a universal correctness or security rule, an
internal implementation detail, or safely derived from another source. Do not
turn “reject malformed input” into a switch that could be accidentally disabled
in a target.

### Current state

`cloudformation/service.yml` supplies environment settings to the public
server task. The current declaration contract includes one small end-to-end
example: product code requires `PLATFORM_SMOKE_APP_NAME`, the task definition
supplies it, and the target profile records it.

### Misconception check

“Every value should be configurable.”

No. Excess configuration creates unowned, unsafe switches. Configuration is a
runtime contract, not a drawer for arbitrary values.

### Study question

Should a database password be stored as an ordinary value in the service
template?

Answer: no. The target may declare the secret's name and approved source, but
the value must remain in a suitable secret store and must not be printed by a
check.

## 6. Permissions: The Running Program's Keycard

Configuration tells the server *where* a dependency is. Permission decides
whether AWS lets the server use it.

### Two task identities

| Identity | Plain-language job |
| --- | --- |
| Execution role | Lets AWS prepare the task: fetch its image, write required logs, and inject approved startup configuration. |
| Task role | Lets the running application make narrowly approved AWS calls while doing its job. |

### Current state

`cloudformation/foundation/workload-iam.yml` defines the public-server task
identities and narrow allowed actions. `cloudformation/service.yml` imports
and attaches those identities to the ECS task definition. For example, the
task role allows specifically approved DynamoDB operations rather than blanket
access to AWS.

### Misconception check

“If the server knows a table name, it can use the table.”

No. The table name is configuration. The task role still needs the right,
narrow permission for that exact operation and resource.

### Study question

Why should the public server and a worker generally not share one all-powerful
task role?

Answer: each has a different job. Separate narrow roles limit accidental and
malicious access if one workload behaves incorrectly or is compromised.

## 7. How Configuration Completeness Is Established

There is no safe universal list of every setting every program needs. Instead,
use two complementary tools.

### A baseline concern checklist

Every server-like scope should be considered for runtime, environment,
network, health, authentication, authorization, dependencies, secrets,
resilience, observability, and deployment identity. A concern can be explicitly
not applicable; it should not be silently forgotten.

### A scope configuration inventory

For each actual setting, record its name, purpose, type, whether it is a
secret, owning capability, runtime consumer, local provider, target provider,
related permission, and proof path.

```text
code reads a setting
  ↔ scope declares it
  ↔ local configuration provides it
  ↔ image accepts it
  ↔ target task provides it
  ↔ task role permits its dependency use
  ↔ safe runtime behaviour proves it
```

### Current state

The repository has declarations and checks for parts of this chain, but not a
complete machine-checkable configuration inventory for the public-server scope.
It cannot yet prove that no setting is missing.

### Misconception check

“A large hand-written checklist proves completeness.”

No. A checklist prompts the right questions. Completeness comes from comparing
the checklist with what code reads, what the target supplies, and what the
running application safely proves.

## 8. Why `workload-iam.yml` and `service.yml` Are Connected

The target tree currently groups much of its AWS implementation by technical
mechanism. These two files are a concrete example:

```text
workload-iam.yml
  creates task keycards and their allowed actions
        ↓
foundation outputs
  makes the keycards available to other templates
        ↓
service.yml
  attaches the intended keycards, configuration, image, and health rules
  to the public-server task definition
        ↓
running ECS task
  receives the intended access
```

### Current state

`cloudformation/foundation.yml` is a composition manifest. It lists focused
foundation fragments such as logging, persistence, workload IAM, queues,
ingress, and alerting and renders them as one foundation stack. The service
template is the separate workload definition that consumes that foundation.

### Misconception check

“Files in different folders are unrelated.”

No. A scope can depend on files in several locations. The important question is
whether those links are explicit, searchable, and checked.

## 9. From a Scattered Tree to a Scannable Deployment Architecture

### The design problem

The current deployment files contain meaningful controls, but a reader cannot
yet reliably learn the delivery journey simply by following the directory tree.
That is a real architecture problem, not a cosmetic complaint.

### Architecture intent

The deployment-control plan adopts two outcomes:

1. **Control:** make the source-to-target chain verifiable and difficult to
   drift.
2. **Scanability:** make the tree show scope ownership, shared foundations,
   pipelines, checks, dependencies, and governing instructions clearly.

The safe order is:

```text
understand current responsibilities
  → make scope relationships explicit
  → distinguish shared from scope-owned material
  → review a target information architecture
  → migrate one bounded area at a time with reference checks
```

The scope folder is a map, not a duplicate implementation. It should point to
the authoritative shared configuration or IAM declaration until a reviewed
ownership decision says a move is safe.

### Misconception check

“Move all related YAML into a scope folder now, and the system will be clear.”

No. Moving before understanding can duplicate authority or break consumers.
Clarity comes from explicit ownership and checked relationships, then safe
migration.

## 10. A Visible Module Configuration Surface

### The design decision

When a platform module consumes or defines runtime configuration, a reader must
be able to find that fact from the module tree. The intended structure is:

```text
platform/<module>/
  src/
    configuration/
      README.md
      <configuration-concern>.ts
      index.ts
```

Each concern file defines one coherent configuration concern: its typed shape,
validation, defaults, sensitivity classification, and relationship to any
dependency. `configuration/index.ts` gathers the individual configuration
concerns in the same way a module's `index.ts` gathers its supported
responsibilities.

`configuration/README.md` is the human source map for this small area of the
tree. It explains each concern in plain language, its owning TypeScript file,
whether it is required or optional, who consumes it, which dependency it
relates to, and how it is proved. It may state that a concern is a secret and
name its approved source, but it never contains the secret value. It links to
the TypeScript contracts instead of becoming a competing source of truth.

### Current state

The repository is not consistent yet. Some modules define typed configuration
beside adapter logic, while the platform server reads several raw environment
variables directly in its startup source. Generic validation machinery exists
in `platform/config`, but there is no common visible configuration directory
in every configured module.

### Architecture intent

Raw environment variables and secret references belong at the runnable-program
composition boundary. That boundary validates them, then passes typed
configuration objects to modules. A module with no runtime configuration does
not need an empty directory, but its README and source map must say that it
consumes and defines none.

### Misconception check

“Every module needs an empty configuration folder for visual symmetry.”

No. The goal is meaningful visibility, not boilerplate. A directory means the
module has configuration. Its absence, plus an explicit README statement,
means it does not.

### Study question

Why is a typed configuration object safer than having every module read
`process.env` directly?

Answer: one composition boundary can validate names, types, defaults, and
secret handling before runtime starts. Modules receive only the values they
need, and the repository can inspect a clear configuration contract.

## 11. Foundation Resources, Scopes, and Provider Selection

### The distinction

Four questions must remain separate:

| Question | Example |
| --- | --- |
| What behaviour is needed? | Shared request rate limiting. |
| Which technology fulfils it? | DynamoDB. |
| Which exact target resource is used? | The Kanbien staging rate-limit table. |
| How does the consumer run? | An ECS public-server service. |

The same target can contain DynamoDB and PostgreSQL for different persistence
purposes, while running some workloads in ECS and others in Lambda. Neither
“persistence” nor “compute” is a single target setting.

### Ownership

```text
foundation owns the long-lived resource
scope owns the need for that resource
workload role owns the narrow right to use it
```

A resource is foundation-owned when it is shared, long-lived, needed before
workloads run, or independently managed for security, recovery, or operations.
It is scope-owned when it should be created, changed, and retired with one
scope. This is a reviewed lifecycle decision, not a guess based on whether a
file happens to be under CloudFormation.

### Provider selection

An app declares the provider-neutral capability it needs. A runnable program
can select from supported adapters. The target workload binding selects the
provider and the exact resource. The foundation provides that resource; IAM
gives the workload only the required action against it.

```text
app needs persistence
  → runnable program supports an adapter
  → target selects PostgreSQL or DynamoDB
  → foundation provides the selected resource
  → task role receives narrow access
```

### Current state

The repository contains these decisions across entrypoints, adapters,
CloudFormation, target configuration, and IAM policies. It does not yet have a
foundation index or enforced cross-layer record that proves all of them agree.

### Architecture intent

The plan now requires a target-local foundation index, scope access
requirements, provider-selection compatibility checks, and coverage statuses
for all active resources, workloads, roles, adapters, and pipelines.

### Misconception check

“If a PostgreSQL database exists in the foundation, the app automatically uses
PostgreSQL.”

No. A foundation resource existing only makes it available. A named workload
binding must select the compatible adapter, configuration, resource, role, and
proof for a particular scope.

## 12. Where Rules, Decisions, and Runtime Evidence Live

### The main mental model

```text
.agentic  → how an agent must change the repository
source and infra → what the software and target actually do
scripts → what can be checked deterministically
README and docs → human explanation and orientation
runtime logging → actual operational events
```

One concern can appear in several places, but each location has a different
job. The goal is not to put every fact in one file. The goal is to prevent two
places from silently claiming authority over the same fact.

### Architecture intent

The planned product-to-target controls divide responsibility as follows:

| Question | Intended authoritative home |
| --- | --- |
| How must an agent add or refactor a platform module? | `.agentic/03.product/` |
| How must an agent bind and prove a target workload? | `.agentic/04.deploy/` |
| Which shared rules apply across the repository? | `.agentic/01.harness/` and `.agentic/06.shared/` |
| Which provider, resource, configuration, and IAM policy are actually used? | Target declarations under `infra/` and provider implementation source |
| How does a human understand the design? | Local READMEs and `docs/`, linked to the governing instruction |

Mandatory instructions currently scattered through READMEs, docs, comments,
and operational notes will be inventoried and moved or linked to one owned
agentic artifact. The explanation stays where it is useful; the authority moves
to the governed location.

### Misconception check

“Making `.agentic` authoritative means it must copy all infrastructure and
application facts.”

No. `.agentic` governs how changes are assessed and verified. It must point to
the actual implementation rather than become a competing copy of it.

## 13. Dependencies and Availability Behaviour

A dependency is anything outside a deployment scope that it needs to do its
job: a data store, queue, identity service, rate-limit store, configuration
source, network path, or similar facility.

### The dependency chain

```text
scope needs a capability
  → target selects a provider
  → a concrete resource fulfils it
  → configuration binds the workload to it
  → access and network rules permit its use
  → proof verifies the declared behaviour
```

### Availability classification

Each dependency must be classified for the specific scope:

| Classification | Meaning |
| --- | --- |
| Required | The scope cannot safely perform its affected normal job without it. |
| Optional | The core job remains safe and honest without it; an extra capability is absent. |
| Degraded | The scope continues under deliberately restricted or safer rules. |

The classification is not enough by itself. The scope must declare what happens
at each point:

```text
startup → readiness → real request → recovery
```

A required dependency does not automatically mean “crash the process.” It may
mean that the process starts but reports not-ready, or that it rejects only the
operation that cannot safely proceed. The intended response must be explicit.

### Declare operations, not “core functionality”

The harness cannot safely infer business criticality from source code. It can
see that an operation calls a dependency, but cannot know whether a failed save
is acceptable, whether audit evidence is mandatory, or which reduced behaviour
is honest. A scope must therefore declare named operations and the promise each
one makes.

```text
operation: save-work
promise: report success only after durable storage confirms the save
```

Each dependency record points to the operation it supports. Its
required/optional/degraded classification is then a decision about that
operation and promise, not a permanent label on a database, queue, or provider.
Missing operation or promise information is a design gap that needs a reviewed
human decision; the harness must not guess.

### The lifecycle in detail

The four lifecycle stages answer different questions:

| Stage | Question | Example of a required storage dependency |
| --- | --- | --- |
| Startup | May the process begin? | Start but remain not-ready for a temporary storage outage; fail start for missing or invalid required configuration. |
| Readiness | May normal traffic be accepted? | Ready only after a safe storage check succeeds. |
| Real request | What honest outcome is given to the caller? | Do not report a save as successful unless durable storage confirms it. |
| Recovery | When may normal behaviour resume? | Verify the dependency for new work, then restore readiness. |

Process running is not the same as ready. A process may remain alive to provide
safe diagnostics and retry a temporary problem, while declaring itself not
ready so normal traffic is withheld.

### Request uncertainty and recovery

There are three different request outcomes:

```text
dependency unavailable before work begins
  → reject the operation; it was not attempted

confirmed failure
  → reject the operation; it did not complete

outcome unknown after work may have been sent
  → do not claim success or failure; use an approved idempotent retry
    or reconciliation path
```

For example, a connection might drop after a save request was sent. The server
cannot safely invent either answer. Blindly retrying can create duplicate work.

Recovery has two separate meanings:

```text
availability recovery
  → can safe new work resume?

outcome recovery
  → what happened to work already in progress when the failure occurred?
```

The first may restore readiness after a safe dependency check. The second may
require reconciliation before uncertain work is repeated or treated as complete.

### What a complete dependency declaration records

For each dependency used by an operation, the future record will make these
decisions visible:

```text
identity and capability
→ operation and promise it supports
→ required, optional, or degraded classification and reason
→ startup, readiness, request, and recovery behaviour
→ safe failure/recovery observations and health effect
→ metric/status signal and alert decision
→ implementation, local, target, and runtime proof
```

It deliberately does not become a place to copy a password, connection string,
private address, vendor-specific policy, or provider definition. Those facts
belong in their own controlled configuration, network, permission, or provider
records and are linked by safe references.

### Behaviour must be observable

Each declared failure and recovery behaviour also needs a safe observation
path:

```text
dependency failure
  → safe failure diagnostic
  → declared health effect
  → metric or status signal
  → alert policy: required, deferred, or not required
  → safe proof
  → safe recovery diagnostic when normal behaviour resumes
```

This does not mean every dependency failure immediately needs a dashboard or
human page. It means the scope must not become not-ready, reject work, or enter
degraded mode invisibly. A deferred alert requires an owner and follow-up; it
cannot be silently treated as complete observability.

### Current state

Dependency facts are still distributed among TypeScript, environment settings,
CloudFormation, IAM policies, and smoke checks. The planned scope declaration,
workload binding, and foundation index will make the relationship visible and
checkable without duplicating the provider declaration.

### Misconception check

“Optional means we can ignore errors.”

No. Optional means the approved reduced behaviour is known, observable, and
safe. Silent loss or invented success is not an optional-dependency policy.

## 14. Networking: Reaching a Dependency

Configuration identifies the dependency; networking determines whether the
workload can reach it.

```text
host → which network destination to contact
port → which network entrance to use
network path and rule → whether the workload may reach that entrance
TLS → whether the connection is securely established
```

For example, a host can be a private name such as `database.internal`. It is
the database server's network address, not the database name and not a
password.

### The separate gates

```text
correct configuration
  + usable network path
  + permitted network rule
  + valid TLS connection
  + valid application credentials
  + required provider/database permission
  = usable dependency
```

These gates are independent. Knowing a host name does not grant network access;
being able to reach a database door does not grant a valid database login; an
AWS IAM permission does not automatically create a network route.

### Architecture intent

The target scope will declare the network relationship it requires in generic
terms. Target infrastructure remains authoritative for real subnets, routes,
security groups, DNS, load balancers, and firewall rules. Target alignment
will compare the declared requirement with safe live facts. Local tests use a
safe equivalent rather than pretending a laptop network is AWS.

### Building a connection path

A connection is a chain, not one setting:

```text
destination name
→ name resolution
→ route
→ narrow network rule
→ transport and application protocol
→ TLS encryption and endpoint identity
→ application authentication and provider permission
```

Each point answers a different question. A name-resolution failure means the
workload could not turn the name into an address; it does not prove that a route
or firewall rule is wrong. A timeout can mean the name resolved but the
connection did not complete; it does not prove which rule caused it. A refusal
means a reachable endpoint was not accepting that entrance. A TLS failure is
about secure connection setup or endpoint identity, not evidence that the
password is wrong.

The transport is the basic connection method, commonly TCP. The application
protocol is the language spoken over it, such as PostgreSQL or HTTPS. The port
is the numbered entrance, such as PostgreSQL's usual `5432`. All three need to
be declared independently.

### TLS and certificates

TLS has two jobs: encrypt the connection and verify that the workload reached
the intended server. The server endpoint normally presents the certificate; a
database client verifies it and then authenticates separately with its own
credentials. A certificate therefore belongs to an endpoint, not automatically
to every dependency record or every client.

One certificate may cover multiple names, a provider may manage and rotate it,
or an internal certificate authority may issue it. Mutual TLS is different: it
also asks the client to present a certificate and is a deliberate client-
authentication design. The scope must not fall back to plaintext or skip server
identity verification merely because TLS is difficult to configure.

### What the future network record will declare

The future provider-neutral network record will name the workload and logical
destination, then declare the resolution policy, transport, application
protocol, port, private/public boundary, route expectation, narrow
source-to-destination rule, TLS and server-identity policy, any client-
authentication reference, local equivalent, safe diagnostic categories, and
local/target/runtime proof.

It will link to—rather than duplicate—the target provider's real DNS names,
addresses, subnets, routes, firewall or security-group rules, certificates,
certificate rotation, and mutual-TLS configuration. It must never store a
private address, certificate body, or secret value merely for convenience.

## 15. Safe Diagnostics: Useful Errors Without Leaks

An agent cannot safely remediate a vague message such as “database connection
failed.” It needs a safe diagnostic record: enough specific evidence to choose
the next check, without revealing secrets or claiming an unproved cause.

### The main mental model

```text
observed failure
  → stable diagnostic code
  → logical scope and dependency
  → lifecycle stage
  → safe context and retryability
  → bounded next check
```

For example, “network connection timed out during readiness” is an observed
fact. It can direct an agent to verify the network-path proof. It must not
claim that a particular firewall rule is wrong unless evidence proves that.

### Required distinction

Safe diagnostics should distinguish meaningful cases such as:

- missing or invalid configuration;
- unavailable secret reference, without revealing its value;
- name-resolution failure;
- connection refused or timed out;
- TLS failure;
- application authentication failure;
- provider permission denial;
- absent or wrong resource;
- invalid response; and
- schema, version, or migration mismatch.

They must also identify whether the failure occurred at startup, readiness,
a real request, background work, target preflight, or deployment verification.

### Where the pieces live

```text
shared diagnostic contract and redaction rules
  → future `.agentic/06.shared/` governance and shared product contracts

module and provider-adapter mappings
  → product implementation and tests

startup/readiness/request behaviour
  → runnable-program composition boundary

expected dependency behaviour and proof
  → target scope declarations and deployment checks

actual runtime events
  → approved operational logging, not Git
```

The dependency contract declares what observation is required. A later
observability scope supplies the actual log transport, metric storage,
dashboard, alert threshold, and notification route. This separation prevents
one dependency record from becoming a duplicate monitoring-system definition.

Never expose passwords, tokens, private keys, full connection strings, secret
values, sensitive headers, raw provider responses that could contain them, or
PII by default. PII includes names, email addresses, phone numbers, addresses,
profile content, uploaded files, and personal identifiers when a safer opaque
correlation ID will do. The repository stores diagnostic contracts, mappings,
tests, and safe evidence references—not production error dumps.

### Misconception check

“A detailed error must show every underlying value.”

No. A useful error identifies the safe logical dependency and observed failure,
then sends the agent to the next approved evidence check. Detail without
redaction is a security incident, not good observability.

## 16. Identity, Authentication, Authorisation, and Workload Access

Authentication asks “who are you?” Authorisation asks “what may you do?” They
are related but must not be confused.

```text
user request
  → application authentication identifies the user
  → platform authorisation decides whether that user may perform an operation

running workload
  → workload authentication identifies the server to a dependency
  → provider or dependency permission decides what that server may do there
```

For example, platform authorisation decides whether Alice may update a profile
in her tenant. Infrastructure cannot make that decision: AWS sees the platform
server, not Alice or the tenant rule. Infrastructure instead limits what the
server process can reach if it is misconfigured or compromised.

### The identities around one workload

Each identity has a separate job and should receive only the authority needed
for that job:

| Identity | Job |
| --- | --- |
| User identity | Identifies the person or client making an application request. |
| Pipeline identity | Lets the delivery pipeline publish and deploy an approved package. |
| ECS execution role | Lets AWS prepare a task: pull an image, write logs, and obtain approved startup inputs. |
| ECS task role | Lets the running application call narrowly approved AWS services. |
| Dependency identity | Lets the running application authenticate to PostgreSQL, an external API, or another non-AWS dependency. |

The pipeline identity must not silently become the server's runtime identity.
The execution role must not become a broad application role. A user-facing
authorisation rule must not be treated as an IAM policy. These separations
limit the consequences of a faulty component or leaked credential.

### Supplying a dependency identity

A workload can prove itself to a dependency in different ways:

```text
AWS task role
→ calling an AWS service directly

secret-backed service account
→ logging into PostgreSQL or another service protocol

API token or OAuth client credential
→ calling an external API

mutual-TLS client certificate
→ proving a client identity during the TLS connection
```

The repository declares a safe reference and the required capability, never a
credential value. For a database login, that might be a username configuration
reference plus a password secret reference. For an AWS service call, it might
be a task-role action and resource reference. The real password, token, private
key, and certificate body remain in approved identity or secret-management
systems.

### Lifecycle: create, supply, rotate, revoke

```text
create
→ provider or identity system establishes the identity

supply
→ approved workload mechanism receives a safe reference or value

use
→ application authenticates only for its declared dependency operation

rotate
→ provider and secret store are updated together; workload refresh behaviour is proved

revoke
→ access, references, and identity are removed when the dependency is retired
```

When ECS injects a secret at task start, a running task normally retains the
value it started with. Rotation may therefore require replacement tasks: the
replacement receives the new value, proves readiness, and then replaces the
old task. A design may support safe live refresh, but that must be explicit and
tested rather than assumed.

### Identity failures are distinct

```text
missing credential reference
→ workload was not given needed identity material

credential rejected
→ dependency was reached but did not accept the identity

permission denied
→ identity was accepted but lacks the needed action

secret retrieval denied
→ AWS could not supply the approved material to the relevant role
```

Each result has a different next check. Diagnostics record the observed
category, operation, logical dependency, lifecycle stage, and safe next check;
they never print a username, password, token, connection string, or secret
value. A required dependency normally keeps the workload not-ready until it is
safe, while an individual request must be rejected honestly if its required
identity or permission is unavailable.

### Architecture intent

The future workload identity and access record will link an operation and
dependency to its authentication method, safe identity/credential reference,
supply and refresh method, rotation/revocation owner, narrow permissions,
failure behaviour, diagnostics, and proof. It will link to authoritative IAM,
secret-management, provider, and application-auth definitions rather than
duplicating them.

## 17. Observability and Alerts

Observability is the ability to understand how a running system is behaving.
An alert is the smaller set of observations that requires a named person or
automation to act.

| Evidence | Main job | Example |
| --- | --- | --- |
| Log | Explain one observed event. | “Storage authentication rejected during readiness.” |
| Metric | Count or trend a condition. | “Ready task count is zero.” |
| Trace | Follow one operation through several components. | “Request reached the server then timed out at storage.” |
| Health state | Decide whether traffic is safe. | “This task is not-ready.” |
| Deployment receipt | Record a release decision. | “Candidate digest B was rejected and digest A restored.” |
| Alert | Tell an owner that action is needed. | “Zero ready tasks for five minutes.” |

### What must become observable

If a scope changes behaviour in a way that affects safety, availability,
correctness, or recovery, it needs a safe observation path. For a dependency
failure this commonly means:

```text
safe diagnostic event
→ structured log
→ metric or health-state transition where appropriate
→ alert only when the declared condition persists or creates serious risk
→ safe recovery event when normal behaviour is proved again
```

Not every failure should alert. A single invalid user request may need only a
safe log or counter. A required dependency making every server task not-ready
needs a health-state change, evidence for investigation, and usually an alert
if it persists.

### Evidence has different owners

```text
application
→ operation outcome, dependency behaviour, diagnostic code

workload runtime
→ task starts/stops, health, and replacement activity

provider resources
→ database, queue, network, IAM, and load-balancer facts

delivery pipeline
→ candidate digest, deployment decision, verification receipt, rollback result
```

Each producer records the facts it actually knows. The evidence is joined by
safe identifiers rather than copying private data between systems.

### Correlation identifiers

```text
scope and target
→ which bounded deployment concern and destination?

release digest and workload revision
→ which exact deployed software and runtime recipe?

operation and dependency
→ which promised job and logical facility were involved?

diagnostic code
→ which observed failure category occurred?

request ID and trace ID, when needed
→ which individual operation crossed components?
```

Request and trace IDs must be random opaque values, never a user ID, email,
session token, or encoded personal data. Metrics use only stable,
low-cardinality safe labels; individual requests belong in appropriately
controlled logs or traces, not metric labels.

### Alerts detect impact and guide action

A good alert names its signal, condition, persistence duration, scope,
severity, owner, safe next check, deduplication rule, and recovery condition.

```text
signal: ready task count
condition: zero
duration: five minutes
scope: platform-server / kanbien-staging
next check: inspect readiness diagnostic and active release receipt
recovery: required healthy capacity returns and meaningful verification passes
```

A **symptom** alert says users are affected, such as zero ready tasks. A
**cause** alert says something may lead to impact, such as rising database
connection failures. Symptom alerts are usually the urgent signal; cause
alerts help diagnose or warn earlier and can otherwise be noisy.

### Safe evidence, access, and retention

Operational evidence must contain no secret or PII by default. An approved
exception requires a specific purpose, minimised fields, restricted access,
defined retention/deletion, access auditability, and protection from broad logs
or alerts. The evidence design must state where it is stored, who can inspect
it, how long it is kept, and how it is removed.

The initial core-server slice has a deliberately small contract:

```text
required now
→ candidate digest, health result, safe server-level verification,
  GitHub Actions receipt, rollback receipt when needed

deferred
→ approved runtime log/metric/trace store, dashboards, notification routes,
  production alerts, SLOs, and error budgets

excluded until selected by a future scope
→ persistence, queue, identity, and external-dependency observation
```

`deferred` requires an owner and follow-up. `excluded` means the scope does not
use the concern. Neither may be described as complete coverage.

## 18. Target Alignment and Drift

Target alignment is a read-only comparison between what the repository says a
selected scope needs and safe facts from the real target. It answers:

```text
Are we looking at the right destination, and is it ready for this approved
candidate without relying on stale or guessed information?
```

It does not deploy, repair, reconcile, or read secret values.

### Planned change is not drift

The model keeps three separate records:

| Record | Meaning | Home |
| --- | --- | --- |
| Declared desired state | Reviewed intention for the selected scope and candidate. | Versioned repository declarations. |
| Known live baseline | The last release proved safely running. | Safe deployment verification evidence. |
| Fresh actual observation | What the provider safely reports now. | Time-limited alignment evidence. |

If digest A is the healthy baseline and digest B is the approved candidate,
the target still running A before deployment is expected. The alignment check
asks whether the target can safely receive B; it does not treat A as drift.
After B is verified, B becomes the new known live baseline.

Drift is an unexplained difference, for example when the repository and known
baseline require task role X but the fresh target observation reports role Y.
The check reports that mismatch; it never fixes the role or triggers another
deployment by itself.

An approved pending release is not a fifth assertion result. Before candidate
digest B is deployed, the target continuing to run accepted digest A is an
expected transition state. The assertion results remain `match`, `mismatch`,
`insufficient-evidence`, and `not-applicable`; the approved transition merely
explains why A is currently expected.

```text
detection never implies remediation
remediation never implies deployment
deployment uses only an approved delivery route
```

### Assertions and verdicts

An alignment result is a set of assertions, not one vague pass/fail:

```text
right target and workload
approved delivery route
required non-secret configuration and secret-reference names
roles and narrow access bindings
health, verification, and rollback prerequisites
selected dependency/network facts when the scope uses them
freshness and unexplained drift
```

Each assertion is `match`, `mismatch`, `insufficient-evidence`, or explicit
`not-applicable`. A required mismatch or insufficient-evidence result stops the
delivery pipeline. `not-applicable` is valid only when the scope declaration
explicitly says that concern is not used.

### Freshness and safe read access

An alignment snapshot records target, checked time, expiry, declared-state
reference, safe observed facts, verdict, and evidence reference. It may be
reused only until its declared expiry. A fresh read is required immediately
before a target mutation, because roles, configuration, services, and other
facts may have changed since earlier planning.

A dedicated read-only alignment identity may inspect only safe metadata needed
for declared assertions: target identity, workload/revision, image reference,
role names, configuration and secret-reference names, health configuration,
and safe drift-evidence status. It cannot deploy, alter resources, retrieve
secret values, or expand its own permission. If it cannot safely establish a
fact, the honest result is `insufficient-evidence`.

### How evidence moves forward

```text
approved candidate and declaration
→ fresh pre-deployment observation
→ approved delivery action
→ candidate-specific live verification
→ acceptance or rejection receipt
```

Only an **accepted** receipt advances the known healthy baseline. A candidate
that was selected, started, or briefly answered a generic health check has not
earned that status. A rejection preserves the prior accepted baseline and its
safe failure evidence. The alignment check only observes and records; it never
repairs AWS or launches another deployment itself.

### First core-server slice

The first slice aligns only its applicable facts: target/workload identity,
approved delivery route, declared configuration and role names,
health/release-verification/rollback prerequisites, and evidence freshness.
Persistence, queue, identity, and network assertions are excluded until a
scope actually selects those dependencies. Runtime-observability assertions are
deferred until their approved evidence route exists.

## 19. Defining a Scope's Responsibilities

An agent must not create a scope by guessing from directory names, or by
assuming that every platform module is separately deployable. Scope definition
starts from evidence: a runnable process, the operations it promises, the
target workload, and the concerns needed to make those promises true.

### The responsibility inventory

Before creating or changing a scope, the agent builds one inventory covering
every standard concern:

```text
runnable program and image
configuration
dependencies
foundation/provider selection
network
workload identity and access
health, recovery, and rollback
observability
delivery route
target alignment
```

Every concern must have one of four states:

| State | Meaning |
| --- | --- |
| Covered | The scope uses the concern and has the required declarations, implementation links, and proof. |
| Deferred | The concern is relevant, but later approved work owns the missing implementation or proof. It needs an owner and follow-up. |
| Excluded | The scope does not use the concern. The record explains why. |
| Unresolved | A product or architecture decision is missing. This blocks a claim that the scope is complete. |

There is no blank state. An agent may not silently omit a concern just because
it cannot find an obvious file for it.

### What the agent can and cannot determine

The workflow can trace candidates from the approved product change, entrypoint,
image boundary, configuration declarations, adapter/dependency use, existing
target declarations, and the repository evidence map. It records links between
source, target, and proof.

It cannot safely infer a business decision such as:

```text
is this operation allowed to lose data?
is a degraded response honest?
which provider should satisfy this capability?
is a permission or alert policy acceptable?
```

If one of those decisions is missing, the agent records `unresolved` and asks
for review. It must not invent a promise, mark a dependency optional, choose a
provider, or claim complete coverage.

### What makes the result checkable

The future scope workflow, schema, template, and checker will require stable
operations and promises, owners, covered/deferred/excluded/unresolved state,
reasons, follow-ups, and evidence links. They will reject, for example:

```text
a scope with an unnamed operation
a dependency linked to no operation
an excluded concern with no reason
a deferred concern with no owner
a scope claiming completeness while a decision is unresolved
```

This gives an agent a repeatable checklist while preserving the human decisions
that source code cannot reveal.

## 20. Package Publication and Custody

Publishing a package is not the same as deploying it. Publishing places one
verified container image into an approved warehouse, such as ECR. Deployment
later tells a selected target workload to use that exact package.

### An immutable package identity

The useful handoff is the image digest, not an image tag:

```text
approved source revision
  -> build
  -> tests and scans
  -> attestation
  -> immutable digest
  -> approved package repository
  -> publication receipt
```

A tag such as `staging` is a convenient label that can later be moved. A digest
identifies the exact image bytes that were tested. A target must select the
digest, and promotion must transfer that same digest rather than rebuild it.

### Custody is deliberately split

Different identities have different jobs:

| Job | It may do | It must not automatically do |
| --- | --- | --- |
| Build and publication | Build, test, scan, attest, and publish an approved digest. | Change a target workload. |
| Package approval | Decide whether the published digest meets package policy. | Decide that a specific target is ready. |
| Target promotion/deployment | Select the already approved digest for an approved target. | Rebuild or silently replace the package. |
| Live verification | Check what the target actually ran and whether it behaved correctly. | Approve its own deployment or alter the target. |

This separation limits the damage from a mistake or stolen credential. A
successful build cannot quietly become a production deployment just because it
uses the same automation account.

### Package approval is not target approval

Package approval asks: “Is digest D built from allowed source, tested, scanned,
attested, and stored in the approved repository?”

Target approval asks: “May this target receive digest D now?” It also needs
fresh target alignment, the approved delivery route, target-specific policy,
and the required human or governed approval. A database migration, unavailable
dependency, or failed alignment can block a target even when the package is
perfectly valid.

### Evidence and exceptions

A publication receipt links the source revision, digest, repository, required
checks, attestation, publishing identity, time, and safe evidence location. A
promotion receipt adds the source and destination targets, the same digest,
destination alignment, approval route, deployment result, and later live
verification result.

If a required scan is unavailable, the honest result is missing evidence, not
a pass. An exception may be prepared by an agent, but it needs an independent
approver, a narrow reason, compensating evidence, an expiry, and follow-up. An
agent must never approve its own exception.

### Architecture intent

The plan will add a provider-neutral package-custody standard, workflow,
schema, fixtures, and checker. Target-local pipeline records will link the
existing GitHub workflow to its source-to-digest evidence without copying its
steps or granting it deployment authority.

## 21. Foundation Bootstrap and Existing Product Work

A minimum usable platform foundation is larger than a server process, but it
does not have to arrive in one risky deployment. The server is the **bootstrap
runtime slice**: it proves we can start, configure, release, verify, and
restore one exact package. It is not yet a complete application foundation.

```text
bootstrap runtime and release evidence
→ persistence
→ application security boundary
→ fuller observability
→ product capabilities
```

The bootstrap slice includes a runnable server, configuration and
secret-reference validation, health/readiness, immutable package identity,
approved delivery/rollback route, and safe GitHub Actions receipts. It does
not claim durable user data, end-user login/authorisation, queues, external
integrations, or complete dashboards and alerts.

### The first lifecycle proof

The first controlled slice must prove both that the repository can establish a
clean target and that it can safely change one.

```text
declared absent baseline
→ create and verify immutable release A
→ accept A as the first known baseline
→ plan one controlled immutable update B
→ fresh comparison against A
→ verify B
→ accept B, or reject B and retain/recover A
```

This is intentionally more demanding than a one-off launch. It proves that
the repository can distinguish expected change from drift, keep an accepted
baseline, record receipts, and avoid an automatic failure/deploy loop. On the
very first failed release there is no prior baseline to restore, so the process
stops with safe evidence rather than inventing a replacement deployment.

### The planned bootstrap boundary

`kanbien-core-platform` is planned as a private target. Its first meaningful
operation is not a user feature: a controlled internal verifier asks the
server to perform one safe bootstrap operation. The server validates required
safe configuration and returns a non-secret identity for the exact immutable
release being tested. This proves a real request path without adding public
ingress, users, persistence, queues, or inherited staging dependencies.

The design separates five jobs:

```text
server code
→ implements the safe verification operation

scope declaration
→ says exactly what must be proved

verifier script
→ makes the controlled request and evaluates the result

delivery pipeline
→ runs the verifier at the candidate stage

receipt
→ records the digest, target, time, result, and safe diagnostic code
```

The current repository does not yet contain this verifier for the planned
target. Existing image smoke tests are useful evidence, but are not assumed to
be its controlled internal verifier without a later review.

### Selecting the bootstrap runnable program

An entrypoint is the source file that becomes the command the container runs
first. The existing `kanbien-platform-server.main.ts` can run privately without
activating its optional AWS adapters, but it still mounts the product-smoke app
and carries staging-oriented composition choices. It is reference evidence,
not the clean bootstrap program.

The planned program is:

```text
infra/04.deploy/03.product/entrypoints/
  kanbien-core-server.main.ts
```

The `kanbien-core-<role>.main.ts` naming family is reserved for runnable
programs intended for the controlled core foundation. For example, a later
worker uses `kanbien-core-worker.main.ts`. A helper such as a configuration or
persistence composer does not use `.main.ts`, because it cannot be started as
a process by itself.

The new entrypoint is deliberately small. It reuses, rather than copies:

```text
platform/server/src/main.ts
→ generic start, listen, and shutdown lifecycle

platform/server/src/transport.ts
→ HTTP port, request parsing, limits, timeouts, and response handling
```

It adds no product app, provider adapter, database, queue, identity provider,
or public-ingress composition.

### What the bootstrap server reuses and adds

The first program reuses the existing generic server stack:

```text
platform/server
platform/contracts
platform/runtime
platform/config
platform/health
platform/security
platform/observability
```

It selects none of the AWS adapters or product apps. The presence of a code
package in an image is not proof that the program uses a live dependency; the
scope must separately declare selected runtime dependencies, configuration,
network routes, and access.

`platform/server/src/configuration/` is planned new structure. Today
`main.ts` contains some direct environment handling. The future folder makes
each generic server configuration concern, including safe release identity,
visible, typed, testable, and exported through one shared index. It does not
replace `main.ts` or `transport.ts`.

The planned generic release-verification code belongs in `platform/server`.
It returns only approved build/release metadata to the internal verifier. It
does not itself prove the image digest: acceptance joins three independent
facts:

```text
AWS workload evidence
→ which immutable image digest the task actually runs

server verification response
→ which safe release/build metadata the reached process reports

package-custody evidence
→ how that digest relates to the reviewed source and build
```

### Split generic observability from persistence integration

The current generic `platform/observability` package declares a dependency on
`platform/persistence` for a persistence-observability bridge. That does not
make the bootstrap server a database user, but it does unnecessarily place
persistence code in its generic dependency graph.

The agreed architecture is:

```text
platform/observability
→ generic logs, metrics, traces, correlation, and health signals
→ no platform/persistence dependency

platform/persistence/src/observability/
→ persistence-owned integration code
→ depends on generic observability
→ selected only by a later persistence scope
```

This is a dependency-boundary refactor. It is not an AWS adapter and does not
create, configure, or contact a database.

### Technical access is not application identity

Infrastructure permissions are grouped under `technical-access/` so they are
not confused with user identity, authentication, or authorisation.

```text
foundation/technical-access/
  delivery-permissions.yml
  workload-startup-permissions.yml

scopes/bootstrap-runtime/technical-access/
  runtime-permissions.yml
```

Delivery permissions describe what the release process may change. Workload
startup permissions describe what the cloud runtime may do to start a
container, such as pull its image or later supply a specifically named secret.
Runtime permissions describe what the running application may access.

The bootstrap server initially has no application-service runtime permissions.
The actual AWS roles and policies remain in provider declarations; these
provider-neutral records explain the narrow purpose, actor, permitted action
and resource, and required proof.

A shared verifier network facility may be foundation-owned. The concrete route
from that verifier to the bootstrap server is scope-owned, because it exists
only for that workload's verification operation.

### Dedicated core-server image

The bootstrap target will use a dedicated image rather than the current broad
platform-shell image.

```text
kanbien-core-server.main.ts
→ dedicated core-server image
→ immutable image digest
→ kanbien-core-platform workload
```

The planned image boundary is:

```text
infra/04.deploy/03.product/image/core-server/
```

It will compile and start only the core server and include only its reviewed
runtime dependency graph, safe defaults, health command, and local payload
proof. It must not include the staging server, worker, relay, PostgreSQL, or
provider-adapter programs merely because they are present in the repository.

Whether the image uses a dedicated ECR repository or an explicitly reviewed
shared one remains a later target-isolation decision. A dedicated image does
not by itself authorise reuse of existing AWS package storage.

### Configuration, access, and network boundary

The server-side platform code defines the shape and validation behaviour of a
setting. The target scope decides whether that setting is required, optional,
or not applicable and how it is supplied. The target never stores secret
values in Git; it stores only approved references when secrets are introduced.

For the bootstrap target, likely required non-secret settings include listener
port, target identity, and immutable release identity. Persistence, login, and
queue settings are explicitly not applicable until a later scope selects those
dependencies.

Infrastructure access is named separately from application authentication:

```text
delivery access
→ may make approved target changes

workload-startup access
→ lets AWS pull the package, write startup evidence, and later supply named secrets

runtime access
→ lets the running server call only the services needed for its declared work
```

The initial runtime-access set should be empty of application-service access.
Its network boundary denies public and staging access, permits only the
controlled internal verifier route, and adds outbound routes only when a
declared startup, evidence, or later dependency need is reviewed. The exact
AWS network mechanism remains a target-design decision, not an assumption.

Verifier results use safe structured codes such as `WORKLOAD_NOT_READY`,
`CONFIG_REQUIRED_SETTING_MISSING`, or `VERIFIER_NETWORK_UNREACHABLE`. They
must never reveal secret values, tokens, connection strings, personal data, or
unapproved private target details.

The staged order prevents circular proof. For example, the first deployment
receipt is held by the delivery system, rather than by a new persistence
capability whose own deployment has not yet been proved.

### Existing platform and core code

Existing `packages/core/` and `platform/` work is retained as the factual
source for what the software does. The plan does not copy it into `infra` or
replace it with a second manifest. Instead, it progressively links selected
modules to their public boundary, configuration surface, adapters, tests,
runnable program, and deployment scope.

```text
platform capability
→ adapter when selected
→ runnable program
→ target resource and access
→ configuration, behaviour, and proof
```

The first inventory looks only at modules actually used by the bootstrap server.
A later persistence, security, or observability slice brings its own relevant
modules and adapters into the chain. A module does not become a deployment
scope merely because it exists, and an unselected module is not automatically a
gap.

### Keep the existing target safe while rebuilding the model

The existing `kanbien/staging` server already uses public ingress, Cognito,
DynamoDB, rate limiting, and CloudWatch-related composition. It is useful
evidence, but it is not the small dependency-free bootstrap target described
in this handbook.

The agreed approach is therefore:

```text
kanbien/staging
→ preserved reference target
→ no automatic migration, rename, deletion, or retrofit

kanbien-core-platform
→ planned new controlled foundation target
→ bootstrap runtime first
→ persistence, security, observability, then product capabilities
```

`kanbien-core-platform` is a target name, not evidence that AWS resources
already exist. Before any AWS work, it needs a separately reviewed target
design: workload and stack names, identities, configuration/secret-reference
namespace, network boundary, evidence route, delivery route, and rollback
record. It may share an account or region with the existing target only by an
explicit isolation decision. Nothing is inherited merely because both targets
belong to Kanbien.

## 22. From a Runnable Program to a Proven Package

The first core-server package will be built in small, separately checkable
pieces. This is the planned layout, not a description of files that already
exist:

```text
.agentic/
  03.product/  → generic rules for runnable-program changes
  04.deploy/   → generic rules for image and candidate-release checks

platform/server/src/
  configuration/  → typed generic server settings
  verification/   → safe generic release-verification response

platform/persistence/src/observability/
  → optional persistence-specific integration

infra/04.deploy/03.product/
  entrypoints/runnable-program-index.yml
  entrypoints/kanbien-core-server.main.ts
  image/core-server/image-contract.yml
  image/core-server/Dockerfile

scripts/04.deploy/lifecycle/
  20-build/core-server-dependency-boundary/
  40-package/build-core-server-image/
  40-package/smoke-test-core-server-image/
  50-deploy/prepare-core-server-candidate/
  50-deploy/deploy-core-server-candidate/
  60-run/verify-core-server-candidate/
```

The important separation is:

| Place | What it owns |
| --- | --- |
| `.agentic` | The rules an agent must follow when changing this kind of thing. |
| `platform` | Reusable program behaviour and typed generic contracts. |
| `infra` | The factual statement of which program, image, and later target are selected. |
| `scripts` | The repeatable checks that build, inspect, smoke-test, and verify those facts. |
| GitHub Actions receipt | Safe evidence from a particular candidate run; not a new source of truth. |

The first check does not maintain a fragile manual list of every source file.
It begins with the selected entrypoint and derives what it needs through the
TypeScript imports, package manifests, lockfile, and final image payload. The
program declaration also names what must stay out. If persistence, a product
app, old staging program, worker, relay, or provider adapter enters the graph,
the check reports the mismatch rather than silently widening the image.

The order is deliberately safe:

```text
generic rules and report-only fixtures
→ separate generic observability from persistence-owned integration
→ core entrypoint and local dependency proof
→ dedicated image and local smoke proof
→ approved target declaration, alignment, deployment, and live verification
```

The final arrow is not automatic. A failed check, unclear declaration, or AWS
mutation boundary stops the work for review. No diagnostic check creates AWS
resources just to make itself pass.

## 23. Next Lesson Queue

Continue this handbook incrementally with:

1. design the planned `kanbien-core-platform` bootstrap target: absent baseline,
   release A, controlled update B, private verifier route, safe receipt, and
   recovery path—without creating AWS resources;
2. complete the read-only reference inventory for the existing public staging
   server and identify only explicit migration candidates;
3. additional foundation and product scopes: persistence, security,
   observability, worker/queue, relay, PostgreSQL, identity/access, and public
   ingress.
