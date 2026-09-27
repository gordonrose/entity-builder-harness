<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.data-governance-foundation-v1
version: 1
status: draft
layer: 03.product
domain: data-governance
disciplines:
- architecture
- security
- sre
- requirements
kind: implementation-plan
purpose: Define the provider-neutral data-handling policy vocabulary and resolved-policy boundary that persistence, storage, observability, audit, AI, and integrations must consume without becoming a central data store or provider implementation.
portability:
  class: source-only
  targets: []
used_by:
- id: product.plan.persistence-foundation-v1
  path: .agentic/03.product/plans/implementation/persistence-foundation-v1.md
- id: product.plan.storage-platform-v1
  path: .agentic/03.product/plans/implementation/storage-platform-v1.md
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# Data Governance Foundation v1

## Purpose

Define one provider-neutral policy vocabulary for how classified data may be
stored, processed, moved, observed, retained, recovered, and removed. This
prevents persistence, object storage, observability, AI, integrations, and
future products from independently inventing conflicting residency, retention,
handling, and evidence rules.

It creates a **policy plane**, not a universal runtime data plane:

```text
platform floor + product baseline + tenant restriction + capability purpose
                                  │
                                  ▼
                        resolved handling policy
                                  │
             ┌────────────┬───────┼──────────────┬─────────────┐
             ▼            ▼       ▼              ▼             ▼
       persistence     storage  observability  audit/AI    integrations
       applies it      applies  applies it     apply it    apply it
```

Each consuming module retains its own mechanics. Data governance supplies the
question and the resolved constraints; it does not save a row, upload a file,
emit a log, encrypt a byte, or call a cloud provider.

## Current Starting Point

`packages/core/security/classification.ts` already owns the provider-neutral
`DataClassification` vocabulary: data sensitivity, sensitive-value kind, and
an optional reviewed reason. `packages/core/security/policy.ts` owns generic
policy-decision shapes. The platform-runtime plan already records that a
classification is not an observability profile and must never justify placing a
classified value in telemetry.

What is missing is the shared bridge from that classification to reusable
handling requirements. Today, residency, retention, permitted processing,
legal hold, access evidence, and telemetry constraints are described in several
plans but cannot yet be resolved once and consumed consistently.

## Scope And Non-Goals

### In scope

- stable, provider-neutral policy references and handling declarations;
- resolved requirements for classification, residency, lifecycle, permitted
  processing, transfer, evidence, and recovery;
- a fail-closed resolver seam with an explicit policy provenance/version;
- module-specific application boundaries for persistence, storage,
  observability, audit/security records, AI, and integrations;
- deterministic local validation and negative tests; and
- feature-consumption declaration requirements for future capabilities.

### Explicitly out of scope

- legal advice, a claim of GDPR/medical-data compliance, or a replacement for
  expert review;
- live tenant policy records, tenant membership, authorisation grants, or a
  central policy database;
- cloud-region, KMS-key, backup-store, log-sink, database, scanner, or AI
  provider selection;
- automatic inspection of arbitrary entity fields or raw request/file values;
- an exception path that silently weakens a platform/product safety floor.

## Architecture And Ownership

| Layer | Planned location | Owns | Must not own |
| --- | --- | --- | --- |
| Core security | `packages/core/src/security/` | Existing stable classification and generic decision vocabulary. | Provider location or tenant-policy values. |
| Core data governance | `packages/core/src/data-governance/` | Policy references, handling declarations, data-use vocabulary, resolved-policy shape, provenance, finite denial reason. | Cloud SDK, storage/database calls, app schema, real tenant settings. |
| Platform data governance | `platform/data-governance/` | Validates/combines an approved floor, product baseline, tenant restriction, and capability declaration into a resolved requirement. | A tenant-policy store, business authorisation, provider resources, raw data scanning. |
| Feature/product | `apps/**` or product package | Entity/attribute classification, business purpose, chosen approved profile, required human review, and narrower business rules. | Provider configuration or a weaker global policy. |
| Consuming platform module | `platform/persistence`, `platform/storage`, `platform/observability`, later audit/AI/integration packages | Applies its relevant part of the resolved requirement at its own boundary. | Re-resolving policy differently or inferring classification from untrusted content. |
| Target/infra | target profile, adapters, `infra/**` | Maps approved abstract requirements to provider region, encryption, retention resources, storage, backups, sinks, IAM, and evidence. | Changing a product's policy meaning. |

The intended source structure follows the repository scanability rule:

```text
packages/core/src/data-governance/
  references.ts       immutable named policy/profile references and versions
  handling.ts         data-use and handling declaration vocabulary
  residency.ts        provider-neutral placement/transfer requirement nouns
  lifecycle.ts        cross-cutting retention, legal-hold and recovery requirements
  evidence.ts         permitted operational, security and audit evidence classes
  decisions.ts        resolved-policy and finite deny/indeterminate outcomes
  index.ts            deliberate public exports

platform/data-governance/
  validation.ts       validates compatible declarations and narrowing rules
  resolution.ts        combines approved policy inputs into one result
  enforcement.ts       narrow adapters used by consuming platform modules
  errors.ts            stable policy-resolution failures
  observability.ts     safe resolution-decision facts only
  index.ts             deliberate public exports
```

`index.ts` files remain small public barrels. Every new package has a local
README that describes its files and explicitly documents what it does not own.

## The Resolved-Policy Rule

The resolver must apply requirements in a direction that cannot silently
weaken protections:

```text
platform safety floor
  ∩ product handling baseline
  ∩ tenant restriction
  ∩ capability/object/record purpose
  = effective handling requirement
```

The result is either a validated policy with provenance/version references or a
finite refusal/indeterminate outcome. It is never an implicit default that
allows cross-boundary processing, raw telemetry, unrestricted retention, or
unapproved AI use because a feature omitted a declaration.

The resolver is not a substitute for authorisation. A caller can pass a
residency policy and still lack permission to read a record or download a file.
Conversely, a caller with permission can still be denied if the policy prohibits
the requested processing or destination.

## Required Handling Dimensions

| Dimension | Shared question | Examples of consuming modules |
| --- | --- | --- |
| Classification | What sensitivity and value kind applies? | persistence schema, storage purpose, telemetry fact selection |
| Purpose | Why is this data being used now? | CRUD, download, export, support, OCR, AI, integration |
| Residency and transfer | Where may data and relevant copies/processors exist? | primary store, backup, preview, logs, analytics, support, model processor |
| Lifecycle | How long is it retained; can it be held, restored, purged, or anonymised? | record lifecycle, object lifecycle, backup, audit store |
| Access and disclosure | What approval, sharing, confirmation, or evidence is required? | file delivery, export, audit/security signal, support workflow |
| Processing | May it be scanned, indexed, OCR'd, transformed, or sent to AI? | storage workers, search, AI adapter, integrations |
| Observability | Which record classes and allowlisted facts may be emitted? | logs, metrics, traces, security records, audit events |
| Recovery | What recovery tier and restore evidence are required? | database backup, object version/archive, provider recovery plan |

## Required Consumer Changes

### Persistence

Persistence must not attempt field-by-field data discovery in generic
repositories. Product entity/schema declarations identify classifications and
handling-profile references; a persistence boundary consumes the resolved
requirements that apply to the operation.

The persistence plan must add:

- a provider-neutral seam carrying the relevant handling-policy provenance for
  a declared record operation, not raw field values;
- lifecycle checks that combine record retention/restore/purge intent with the
  effective legal-hold and residency requirements;
- migration, backup/restore, read-replica, export, and support-access design
  checks against the resolved handling policy; and
- safe lineage/telemetry facts that state a policy reference/outcome rather
  than a tenant, field, record body, or sensitive value.

### Storage

Storage profiles must reference a data-handling requirement rather than repeat
residency, retention, legal-hold, processing, and evidence rules in a separate
unrelated vocabulary. The effective policy governs original objects and every
relevant derivative, archive, preview, extraction result, backup, scanner
artefact, and processing destination.

### Observability

Observability retains its canonical allowlists and never receives arbitrary raw
values for classification. Before a log, metric, trace, security record, or
audit event is prepared, the consuming capability uses the resolved policy to
decide whether that record class is permitted and which already-approved facts
remain allowed.

The platform must not turn classification into a metric label, a trace
attribute, a filename substitute, or a bypass around existing operational
profile validation. Aggregate signals may state a finite policy posture or
outcome; metric labels must remain low-cardinality and never identify a tenant,
record, object, correlation, or policy instance.

### Future consumers

Audit/security-record delivery, exports/reporting, search/indexing,
integrations, support access, OCR, voice/transcript handling, and AI processing
must each name their data-use purpose and consume the same resolved policy
before they are exposed.

## Staged Programme

### Stage 0 — inventory and compatibility map

Inventory existing Core classification, lifecycle, observability profiles,
audit contracts, tenancy/residency direction, persistence, storage, queue, and
target-profile artefacts. Identify overlaps, ownership, and any policy terms
that cannot be reconciled without a deliberate migration.

**Exit:** a compatibility map identifies which existing values are reused,
which are references rather than duplicated values, and which consuming plans
must change. No source or provider mutation is authorised merely by this map.

### Stage 1 — Core data-governance vocabulary

Create the small Core module while preserving `core/security` as the home of
classification. Add only vocabulary proven reusable across two or more
consumers. Provide no tenant settings, raw data, provider SDK, region strings,
or runtime policy lookup.

**Proof:** type/runtime/compatibility tests validate references, finite data
uses, policy provenance, impossible combinations, narrowing direction, and
safe copying. Boundary tests reject provider and product vocabulary.

### Stage 2 — provider-neutral policy resolver

Create `platform/data-governance` with explicit input sources and a fail-closed
result. It validates that tenant restrictions only narrow the product/platform
baseline and reports finite resolution outcomes without emitting sensitive
policy settings.

**Proof:** deterministic tests cover missing declaration, missing resolver,
unknown reference, incompatible residency, expired exception, narrowing,
attempted weakening, and provenance preservation. No platform module silently
falls back to permissive handling.

### Stage 3 — consumer integration contracts

Update the persistence, storage, and observability plans and source contracts
to accept a resolved policy only at their natural boundaries. Preserve their
existing responsibilities: repositories persist, storage coordinates objects,
and observability normalises allowlisted facts. None becomes a policy engine.

**Proof:** focused integration tests prove the same declared requirement causes
consistent deny/allow/retain/evidence behaviour across in-memory consumer
fixtures. Tests prove that rejected handling prevents the consumer action and
that raw classified values never appear in safe facts.

### Stage 4 — feature-consumption declaration and validation

Extend the product feature-consumption decision record so each capability that
stores, reads, exports, observes, processes, or transfers data declares its
purpose, handling profile, relevant entity/attribute/object classification,
residency, lifecycle, observability, sharing, and human-review implications.

**Proof:** the feature harness rejects missing or incompatible declarations and
does not allow a feature to select provider implementation values.

### Stage 5 — target mapping and bounded operational proof

For each selected target capability, map abstract requirements to reviewed
provider/infrastructure controls: region, encryption, backup, object lifecycle,
log/audit sink, processor location, network boundary, identity, alerting,
retention, and recovery. The operational-realization gate must verify each
mutating edge before target execution.

**Proof:** one harmless synthetic capability proves the relevant resolved
policy is enforced through its selected persistence, storage, and observability
paths. It records only safe aggregate evidence. A separate approval is required
for every target mutation.

## Completion Criteria

Data governance is a usable foundation only when:

- existing classification vocabulary is reused rather than duplicated;
- policy resolution is provider-neutral, explicit, versioned, provenance-aware,
  and fail-closed;
- a tenant can narrow but cannot weaken the product/platform floor;
- persistence, storage, and observability consume the same resolved policy at
  their own boundaries;
- each consumer maintains its safe-value boundary and does not emit raw data;
- target mapping and recovery evidence are selected per provider rather than
  hidden inside a generic policy module; and
- feature declarations make required data-handling decisions reviewable before
  implementation.

## Related Artifacts

- `packages/core/src/security/classification.ts` — current classification
  vocabulary to be composed, not replaced.
- `.agentic/03.product/plans/implementation/persistence-foundation-v1.md` —
  persistence lifecycle/outbox foundation.
- `.agentic/03.product/plans/implementation/storage-platform-v1.md` — object
  storage policy and S3-reference route.
- `.agentic/03.product/plans/implementation/platform-runtime-implementation.md`
  — current observability data-classification/evidence-policy boundary.
- `.agentic/03.product/plans/implementation/production-reference-target-baseline.md`
  — EU-only target and cross-boundary-denial direction.
- `docs/04.deploy/plans/kanbien-staging-platform-foundation-convergence-v1.md`
  — staged source-to-target execution programme and live-proof gates.
