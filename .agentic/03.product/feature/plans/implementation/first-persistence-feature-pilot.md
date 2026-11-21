<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.feature.plan.first-persistence-pilot
version: 3
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: feature-governance
disciplines: [architecture, backend, sre]
kind: implementation-plan
purpose: Bound the first real persistence-backed feature as a governed consumer of existing Core and Platform capabilities.
portability: {class: source-only, targets: []}
used_by:
- id: product.feature.workflow.create
  path: .agentic/03.product/feature/workflows/create-feature.md
-->
# First persistence-feature pilot

## Purpose

The first pilot is a deliberately small record feature. Its purpose is to qualify the feature-creation path, not to become a generic CRUD framework or a replacement for `apps/platform-smoke`.

## Intended capability

The first adopted owner is `apps/entity-smoke`; its feature is
`apps/entity-smoke/features/test-entity`. It is deliberately named as a test
entity, not as an assertion that future entities are generated. It owns:

- system identity (`EntityId<"TestEntity">`) generated from the injected UUID
  capability; a separate caller-supplied UUID attribute; integer, date-time,
  string, enum, boolean, categorical-array and free-text-array attributes;
- nullable `description`, `reviewedAt`, and `secondaryCategories` attributes;
- system timestamps from the injected Core clock; business visibility
  (`active` or `archived`), separately from Core lifecycle state; and
- one named index: ordinary active records by `status` then `createdAt`.

Its use cases are create, get, list through that index, edit, archive, restore
from archive, logical delete, restore during the recovery window, and assess
hard-purge eligibility. `null` is an intentional stored value for a nullable
attribute; it is not an omitted required create value.

Hard purge is not an ordinary feature operation. This pilot proves eligibility assessment only unless a later scope supplies retention, legal-hold, target, and execution governance.

## Excluded concerns

- public internet ingress;
- application authentication, authorization, and tenancy;
- logging, telemetry, alerts, and dashboards beyond existing required safe diagnostic propagation;
- a generic entity generator, generic CRUD framework, or universal app layout;
- autonomous purge, migration execution, AWS mutation, and production release.

## Consumer and proof inventory

| Consumer | Responsibility | Required proof |
| --- | --- | --- |
| `apps/entity-smoke/features/test-entity` | feature contract, services, repository mapping, migration reference | focused runtime/type tests |
| app public mount | exposes the feature without exposing internals | mount contract test |
| `products/kanbien-platform` | composes the app through its public surface | product-manifest test |
| Core/Platform persistence | lifecycle and provider-neutral repository contracts | existing contract tests plus feature integration test |
| selected deployment scope | package inclusion, migration execution, database dependency, release safety | 04.deploy declaration coverage and stage-specific proof |

## Advancement gates

1. Build the feature only after the selected persistence path is confirmed available for the pilot.
2. Treat local behaviour as local evidence only.
3. Before package or target work, add a complete declaration/proof chain for the feature’s workload, database dependency, migration, diagnostics, and recovery semantics.
4. Enter AWS only through separately authorised target alignment, deploy, and run workflows.

## Persistence and diagnostic decision inventory — 2026-11-06

The local feature currently has an in-memory implementation only as a behaviour
test double. The intended durable path is an app-specific PostgreSQL repository
bound only from the `04.deploy` composition layer, with a reviewed ordered
migration. That target repository binding and migration executor are not yet
implemented; the existing SQL migration declaration is not execution proof.
This is not a generic repository or ORM.

| Boundary | Conditions | Owner and safe diagnostic treatment | Proof |
| --- | --- | --- | --- |
| Core UUID parsing/generation | invalid input; system generation failure | Core shared UUID diagnostic; no submitted UUID or native error text in detail | Core UUID runtime/type tests |
| Feature input schemas | missing, wrong-type, invalid enum/UUID/date, invalid nullable/array element | feature validation issues plus `entity-smoke.test-entity.validation-failed` with field/reason only; root rejection identifies `input` | feature schema/service tests |
| Domain lifecycle transition | invalid visibility/lifecycle transition, restore-window expiry, ineligible purge | reuse Core persistence lifecycle errors/diagnostics; feature adds no duplicate lifecycle vocabulary | feature service tests |
| Repository call (planned target binding) | unavailable or returned failure | target PostgreSQL binding must preserve the existing adapter diagnostic envelope; local double has no provider claim | repository binding tests not yet implemented |

No mutation is retried by diagnostics. Ordinary reads exclude logically deleted
records. A target repository, migration executor and live proof chain still need
to be implemented before a separately authorised package, target-alignment,
deploy and live-run sequence can produce target evidence.

## Target decision — 2026-11-07

The user selected `kanbien-core-platform`, not `kanbien/staging`, because staging
is intended to retire only after feature parity. Do not add new feature
dependencies to staging or treat staging's platform-shell image as proof of the
core-platform feature workload. No staging retirement is authorised here.

The user approved an isolated `entity-smoke` scope with its own feature-capable
image, PostgreSQL migration/permissions and live-proof chain. Preserve the
bootstrap/persistence programs' narrower approved dependencies and accepted
release records. Their existing image or acceptance receipts cannot qualify
the new feature. Implementation is governed by the
[isolated-scope plan](../../../../04.deploy/plans/implementation/entity-smoke-core-platform.md).
Exact AWS changes still require target-specific approval under the owning
deployment workflow; the scope decision is not approval to execute them.

## Success criterion

The pilot succeeds when the same feature shape can be created and tested locally, selected into a product/package route, and taken through a declared AWS persistence proof without ad-hoc application code, console changes, or feature-specific provider imports. Each completed stage must have its own evidence; no earlier stage substitutes for a later one.

## Supported UUID explanation preservation — 2026-11-09

Independent of the pending disposable-restore cleanup governance decision, source
review found a concrete feature mapping loss: Core's real `systemUuidGenerator`
returns `core.shared.uuid-generation-failed/v1` with reason
`generated-value-invalid` and a `core.shared.uuid-invalid/v1` invalid-format
companion, but `createTestEntity` forwards only the primary record. The existing
`TestEntityError` interface and HTTP response consumer already support companions;
no new diagnostic definition, delivery framework or schema version is needed.

The bounded correction is an optional fourth companion argument on the existing
feature error constructor and forwarding that argument at the UUID and two Core
lifecycle wrappers in `domain/entity.ts`. Three-argument callers and existing
feature codes/messages, source record identity, control flow and disclosure
remain compatible. Native causes and unrelated diagnostic-processing adoption
are not changed. The constructor stays in `contract/errors.ts`; public indexes
remain export-only and no Core/Platform/provider ownership moves.

Planned proof in the existing app diagnostic integration fixture uses the actual
Core system generator with descriptor-restored controlled Crypto output. It
asserts the exact primary/companion code, version and reason at the public create
service, original primary and companion-array identity, one generator/native
invocation, no clock/read/create/save/list call, and synthetic canary exclusion.
Also retain successful creation, existing no-companion failure and validation
before side effects. Missing Crypto/thrown generation must not invent a format
companion. The existing registered `entity-smoke-runtime` owns local type/runtime
proof. HTTP delivery remains separately exercised by the existing composition
fixture, not claimed as new remote delivery or AWS proof here. Final review and
actual registered outcomes must be recorded before calling this slice verified.

Consolidated self-review: inspected all nineteen sources in the existing feature
review, their public service/type fixtures, the real Core generator and HTTP
companion consumer. No new schema/catalog/export or package-shim input is
introduced. The correction preserves the original primary and companion-array
identities; exact nonempty invalid-format companion assertions reject the former
loss, while exact absence for generation throws/unavailable Crypto rejects a
fabricated format diagnosis. Invocation and prevented-effect counters reject
replay or continuation; exact descriptor restoration runs in `finally`, including
on failed assertions. Existing primary-only callers remain covered. Updated only
this feature's source-matched partial review, retaining unrelated missing-error,
processing, lifecycle-alternative and delivery debt. Review inputs are closed for
this bounded slice; registered local proof and the wider integration/deployment
obligations remain distinct and pending until their actual outcomes are recorded.

## App persistence/transport review closure — 2026-11-09

Review the three relational source files, private HTTP adapter, durable public
app mount and export-only app index against their actual consumers and existing
local repository/composition fixtures. Source hashes must not claim whole-file
adoption: processing faults, arbitrary getters/dependency throws, actual database
execution, profile-governed logger delivery and AWS acceptance remain separate.

Observed correction: `assessTestEntityPurgeEligibilityService` returns either a
known eligibility string or `TestEntityError`; HTTP currently embeds either in a
200 response. A missing entity therefore looks like successful assessment. Map
only that established error through the existing response function (404 for
`TEST_ENTITY_NOT_FOUND`); retain the successful eligibility body and all codes,
messages and no-purge semantics. This corrects the uncommitted smoke route's
failure projection, not a new public ingress or purge-execution capability.

Planned local proof extends the existing source-discovered app suite with the
actual public durable app mount, captured registered route/health/profile/catalog
and typed request context. Use existing Core configuration, logger, metrics,
clock and identifier primitives; a narrow typed recording registry invokes
existing public catalog/profile/route validators rather than copying Platform
decisions. The more general Platform test registry was inspected; importing that
additional package solely for this bounded recording/rejection seam would expand
the app compiler, shim, package and registered-input closure. This fixture does
not claim full Platform registry/server or logger delivery proof; existing
composition tests retain that responsibility.

Assert rejected input before generator/repository calls, successful create/get,
known conflict/provider failure mapping, exact internal primary and companion
identity at the callback, callback absence/throw/rejection isolation without
replay, no diagnostic/provider canary in HTTP bodies, not-found eligibility 404,
unchanged successful eligibility, no hard-delete command, readiness-envelope
preservation, exact original registration rejection and delegated close hook.
Keep original relational parameter/mapping and error-identity assertions; extend
them with source companions, malformed-row list rejection and create/write
row-count alternatives where currently uncovered. `entity-smoke-runtime` is the
registered local proof; actual server/logging remains `entity-smoke-composition`
and its current full run is still blocked at the unrelated cleanup compiler.

Consolidated self-review inspected all six affected executable files, full new
mounted fixture, extended relational fixture, actual Core/Platform interfaces,
existing local-server composition cases and feature guide. The exact missing
assessment status/body assertion rejects the former 200-with-error outcome;
active assessment retains its exact successful body. Exact callback identities
and rejecting-sink invocation counts distinguish preservation from silent
omission, while effect counts distinguish isolation from replay. Full returned
row diagnostics reject wrong field classes; malformed-list tests reject partial
return/retry, and each write-count combination rejects unjustified one-row
success. Registration failures at all four stages retain the original envelope
and stop later registration. Core's base health interface remains unchanged;
runtime attachment identity is inspected explicitly, not claimed as a newly
typed Core field. The new registry is a recording dependency seam using public
validators, not a replacement Platform registry or server.

Exploratory app compiler/runtime proof passes after fixture-only corrections for
the health interface and two explicit TypeScript control-flow annotations. The
normal successful and rejected scenarios remain; no test is skipped or assertion
weakened to hide a production failure. Three new source-matched PARTIAL reviews
cover relational persistence, command transport and durable mount, while the
public-export support review now reflects the durable factory. Real remaining
processing/provider/server/deployment debt remains explicit. The README skill
was used to correct the stale in-memory-only description, trace actual ownership
and examples, and name local/database/image/AWS proof limits. Inputs for this
bounded slice are now closed before registered final proof; the pending cleanup
governance rule and unfinished restore batch are untouched.
