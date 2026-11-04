<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.standard.public-module-structure
version: 9
status: active
created_on: "2026-11-01"
updated_on: "2026-11-03"
layer: 03.product
domain: architecture
disciplines: [architecture, agentic]
kind: standard
purpose: Govern public exports, Core module responsibility separation and incremental legacy cleanup.
portability: {class: source-only, targets: []}
used_by:
- id: product.workflow.platform-runtime-implementation
  path: .agentic/03.product/workflows/platform-runtime-implementation.md
- id: shared.standard.require-change-completion
  path: .agentic/shared/standards/require-change-completion.md
-->
# Public module structure

## Rule and scope

A module's public `index.ts` exposes its public functions and types. Their
implementations and definitions belong in appropriately named files within the
module. Apply this to new modules and relevant refactoring in Core, Platform,
adapters, apps and products; it is not a diagnostic-only convention.

Use export declarations to expose those files. Do not put imports, functions,
constants, classes, enums, type/interface definitions or executable statements
in the index. Comments, empty statements and the empty `export {}` module marker
are harmless. Re-exporting dependencies can cause their initialization to run;
this rule prohibits initialization written in the index, not all effects of
loading the dependency graph.

Group implementation by cohesive responsibility. Do not replace a mixed index
with a file per function or another unstructured catch-all merely to pass a check.
Internal files should depend on the actual owning files rather than importing
back through their public index, especially where that would introduce cycles.
Preserve supported public import paths, exported names, types, behaviour, errors
and diagnostic contracts during a structural cleanup.

A temporary compatibility file must name the supported consumers or import-path
promise it preserves and its retirement condition in the existing task plan.
Do not retain a sibling forwarding file merely because a module moved into a
folder. Before retiring one, redirect callers to the owning module's supported interface
(or owning files within that same module), preserve
public exports/types and prove imports against fresh output without stale
compiled files. Existing boundary fixtures should prevent a retired bridge from
returning; a directory index is not itself an obsolete file.

## Apply during implementation and refactoring

Use the existing task inventory/session record, not a new review form:

- For a new module, start with an export-only index and named implementation.
- For a module-structure or public-surface refactor, include the index cleanup,
  affected internal imports and compatibility proof in the bounded plan.
- When adding functionality to an older module, place new implementation in
  named files and expose it through the index; do not add to its legacy logic.
- For an unrelated behaviour fix, assess the structure but do not silently grow
  the task into a module rewrite. If the fix must touch pinned legacy code,
  record why and obtain explicit approval for that exact exception or expand
  the planned refactor with the user's agreement before changing the allowance.
- Before claiming completion, review whether destination files represent useful
  responsibilities and whether all supported consumers still work. A structural
  pass alone cannot establish those judgements or runtime compatibility.

Earlier capability plans describing deliberate public export lists follow this
standard; they are not separate exceptions. Follow the owning workflows for
other architecture decisions and the shared change-completion standard for
connected review, focused proof and verification ordering.

## Core module responsibilities

For new Core modules and structural refactoring, account for the following in
the existing task inventory or plan. Name the owning files and proof, or give
a concrete not-applicable reason. Accounting for a responsibility does not
require another folder, manifest, service wrapper or checklist document.

| Responsibility | What must be accounted for |
| --- | --- |
| Public interface | Deliberately exposed names, supported import paths and private implementation. |
| Contracts | Accepted inputs, outputs, interfaces, schemas, error/report shapes and reusable constraints. |
| Capabilities | The actual reading, checking, transformations and other operations the module performs. |
| Diagnostics and privacy | Report definitions, the conditions establishing each diagnosis, preservation and permitted delivery; supplied sensitive information stays outside reports. |
| Dependencies and effects | What other Core modules or supplied functions may be called, what effects are possible and what is unknown after failure. |
| Assembly and registration | Any necessary construction, injected dependencies and catalog registration; otherwise state why no assembly factory is needed. |
| Reference implementations | Supported in-memory/no-op helpers and their limitations, distinguished from private test fixtures. |
| Compatibility and generated outputs | Supported public versions, affected consumers, canonical definitions and derived exports. |
| Proof and explanation | Type/runtime/boundary tests, material counterexamples and a source-backed README. |

`contract/` and `domain/` are the recommended role names for a Core module whose
size warrants directories. Here, domain means the module's own capabilities,
not permission to add application-specific business workflows to Core. Small
modules can keep clearly named files without empty directories; justify the
layout by responsibilities, not by identical folder counts. Do not create a
file per function or a large generic helpers/service file to hide mixed jobs.

For substantial modules, group cohesive work within those roles rather than
leaving unrelated files together merely because they are all contracts or all
operations. Config's reference groups report definitions under
`contract/reporting/` and operations under `domain/reading/`, `domain/validation/`
and `domain/reporting/`. Reading helpers may read and check one value together;
report construction is distinct from log delivery. These names are examples,
not a required taxonomy for every module. Choose groups that explain that
module's actual work, with a short placement rationale and consumer map in the
existing task inventory. Do not create empty folders or a public index per group.

Start new substantial modules this way. During a structural refactor, reconcile
the affected grouping, imports, public exports, tests and explanations together.
For ordinary fixes, assess the affected responsibility without silently starting
a whole-module retrofit. Small modules may retain cohesive named files.

Contracts may execute code: a checked constructor or schema validator can
enforce the representation it defines. Distinguish that from a capability that
reads a source, applies caller-selected requirements or coordinates an operation.
Classify by the promise enforced, not by whether a function's name says validate.
Use one authoritative representation; do not create matching independent schema,
type, reason or constraint lists simply to populate different folders.

Use names that explain the responsibility, not a generic types/helpers bucket.
Place error-specific types with error definitions and issue-specific types with
issue definitions. In config, setting issues describe information obtained;
sourcing issues describe failure to obtain it. Either can prevent an operation
from completing, but a failed read does not establish invalid contents. These
are responsibility distinctions, not mandatory filenames for every module.

Core remains provider- and product-neutral. Describe failures without HTTP
status selection; actual HTTP/queue transports, provider clients, database
implementations, environment loading and deployment assembly remain with their
existing Platform/app/target owners. Invoking an injected source can still have
effects or throw: dependency injection is not proof of purity or successful work.

## Reusable configuration constraint ownership

For new constraints and relevant refactoring, distinguish the representation of
a checking instruction, a named reusable requirement, and the operation applying
it. In Core config, `contract/types.ts` describes supported instructions;
`contract/constraints.ts` owns named, immutable requirements for acceptable
configuration values. Checking implementations remain with their capabilities.
This is not a mandatory filename or empty folder for every other module.

Admit a rule to Core config's `contract/constraints.ts` only when it expresses a
reusable configuration requirement with a stable meaning independent of a
particular product, provider, deployment or concrete source. Two consumers using
the same number or pattern is not sufficient: establish that they share the same
requirement and acceptance meaning. Do not promote coincidentally equal local
choices or create speculative rules merely to populate the file.

| Responsibility | Owner |
| --- | --- |
| Provider- and product-neutral configuration requirement with shared meaning | Core config's `contract/constraints.ts`, exposed through its public index. |
| Rule specific to a provider or capability, such as PostgreSQL login syntax | That provider/capability's owning contract, not automatically Core config. |
| Application-selected policy, such as a retry limit or timeout | The application/capability choosing that policy; sharing a number does not make it universal. |
| Required logical settings and service-specific constraints | The capability or adapter implementation that needs them. |
| Concrete source names, environment bindings, implementation selection and target policy | Target configuration and composition; no copied dependency requirements. |
| Reading, parsing, checking or coordinating supplied values | The capability performing that work, not the shared constraint declaration. |
| Failure shapes and diagnostic meanings | Their existing issue, error and diagnostic contract owners. |

Keep shared rule values code-owned and immutable through both the public type
and the runtime object. Reuse the supported instruction representation rather
than introducing a parallel schema or independently maintained bounds. Consumers
select the rule through the supported public interface and retain their own
source bindings and compatible reading/checking behaviour. A destination-port
range does not establish a listener/default policy; text and numeric input
checks need not become interchangeable to share the same range.

Record the placement decision, actual affected consumers and material
non-applicability cases in the existing task inventory. For changes to a shared
rule, account for every supported consumer and prove the affected acceptance
behaviour and actual reuse through the existing diagnostic review workflow.
These ownership decisions require source review: structural checks and matching
hashes do not establish shared meaning or semantic completeness. Do not add a
filename/import-regex gate that claims otherwise.

For service selection and relevant structural refactoring, apply the
[configuration ownership standard](config-runtime-settings.md#dependency-requirements-implementation-selection-and-composition).
Keep operation meaning, service translation, target wiring and generated build
output distinct; a matching folder shape is not evidence of compatible behaviour.

## Dependency direction and diagnostic ownership

- The public index re-exports selected contracts/capabilities, but no internal
  file imports back through its own index. Capability files can depend on their
  contracts and on cohesive sibling capabilities without creating cycles.
- Contracts do not import the module's capability implementation. They may
  depend on upstream Core contracts and small shared constructors where needed.
  Keep publicly exchanged descriptions owned once; do not duplicate a public
  model into both contract and domain folders without an actual representation
  difference and explicit conversion responsibility.
- Cross-module consumers use the target's supported public interface. Explicit
  package assembly may import an owning contract directly when the plan records
  why, which files may do so and why the exception creates no reverse dependency.
  No exception grants access to arbitrary private capability files.
- A module owns its diagnostic meanings; the shared diagnostics module owns
  construction/parsing mechanisms. Capability predicates establish what happened.
  Contract-valid report construction alone does not establish diagnostic truth.
  Observation helpers are permitted when they remove real repeated work, but a
  mandatory diagnostics service or folder is not required for every module.
- Apply the [safe diagnostic context requirements](../../shared/standards/require-safe-diagnostic-record.md#context-and-consumer-obligations).
  Shared Core mechanisms construct/parse records; each capability establishes
  its own facts. Platform adds reusable workload context and approved delivery,
  adapters interpret provider evidence, and entrypoints bind actual sources,
  implementations and execution context. Do not move reusable checking or
  reporting machinery into an entrypoint to supply its concrete binding.
- Account for required consumer context in the same module/task inventory:
  which interface requires each fact, its supplying owner and real caller proof.
  Use a validated construction path for the responsibility; bind fixed context
  once when useful rather than require every caller to rebuild it. A wrapper or
  assembly factory needs actual connecting work, not a mandatory architectural
  slot. Contracts must not acquire capability dependencies to perform assembly.
- Keep package catalog assembly outside the reusable capability dependency path.
  Generated JSON remains derived from executable definitions, not a second
  editable schema. Follow existing diagnostic evolution/privacy and completion
  requirements rather than introducing a new reporting vocabulary or registry.
  For local generated assets and public package access, apply the
  [module-local catalogue standard](../../shared/standards/require-safe-diagnostic-record.md#module-local-catalogue-exports).
  Exported JSON assets are not TypeScript module indexes; classify and package
  them explicitly without weakening existing module/dependency restrictions.

Before moving a module, map every public export and private helper to its owner,
identify genuine splits, state dependency directions and preservation tests,
and obtain the layout agreement required by the task. For the first config proof,
the user must approve the proposed layout before any source move. Record later
scope changes before acting rather than silently expanding to other modules.

For source layout decisions and not-applicable cases, source review remains
necessary. The existing checker now also enforces dependency edges for modules
adopting actual contract/domain folders and a public index: no contract-to-domain
reachability, internal own-index imports, internal cycles (including type-only)
or external private imports. Its exact Core catalog exception is bounded to
config's diagnostic contract. Future modules using these roles are discovered
without another manifest. Supported literal import forms, aliases, discovery
roots and unresolved/dynamic-import treatment are documented in the command guide.
Per-operation context enforcement and end-to-end report completeness likewise
need runtime/type/consumer proof; export-only indexes and review hashes do not
establish them. Apply this guidance to new work and relevant refactors without
silently claiming or starting repository-wide adoption.

## Executable coverage and legacy debt

The same existing command also applies the configuration standard's
[narrow source-access boundary](config-runtime-settings.md#narrow-automatic-access-boundary-and-limitations).
Its scope and limits are separate from index/dependency proof; it does not
establish checked-result use or universal diagnostic completeness.

[The shared checker](../../../scripts/repo/module-structure/check.mjs) parses
TypeScript rather than matching source with regular expressions. It discovers
`index.ts` and `index.tsx` under `src/` within `packages/`, `platform/`, `apps/`
and `products/`, including new untracked modules. Test/fixture, build, dependency
and Git directories are excluded. JavaScript indexes, other source layouts and
other repository roots are not mechanically covered; review must identify such
a new public boundary and extend the owning check when applicable, rather than
claim automatic coverage. Symbolic-link source traversal fails closed.

The [legacy manifest](../../../scripts/repo/module-structure/legacy.v1.json)
pins the exact non-export statements of the 23 existing mixed indexes retained
when this rule was introduced. It is debt, not a compliant-module list. New
re-exports may be added without changing a pin; new or changed implementation
fails. Core config has no allowance and cannot be added to this manifest.
Cleaning up or removing a legacy module requires removing its stale allowance.

There is no automatic baseline-refresh command. Changes to allowances require
explicit approval and source review of the exact implementation, justification
and fixture consequences recorded in the current task/session. Do not refresh
hashes just to make a failed check green. The checker validates the current
pins, not whether a human approved editing them; that approval remains governed
by the harness and review. This task does not authorize migrating all legacy
modules or modifying upstream-owned tooling.

The registered `module-index-structure` check runs at the commit boundary and
normal integration selection. `module-index-structure-regression` proves the
checker and its legacy/counterexample handling at integration. Both use existing
local verification; no container, provider operation or dependency installation
is needed. Refer to the [command guide](../../../scripts/repo/module-structure/README.md)
for inputs, outputs, tests and limitations.
