<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.teaching-notes.0003-packaging-and-deployment-learning-handbook
  version: 4
  status: active
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
12. [Next lesson queue](#12-next-lesson-queue)

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

## 12. Next Lesson Queue

Continue this handbook incrementally with:

1. required configuration versus secret references, including safe proof;
2. target alignment: comparing expected declarations with real AWS state;
3. package publication and custody: GitHub Actions, OIDC, ECR, approvals, and
   immutable-digest handoff;
4. deployment and rollback: changing the workload to run a tested candidate;
5. live verification and drift evidence;
6. the public-server scope's complete evidence map;
7. additional scopes: shared foundation, worker/queue, relay, PostgreSQL,
   identity/access, public ingress, and observability/alerting.
