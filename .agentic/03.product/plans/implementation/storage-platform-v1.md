<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.plan.storage-platform-v1
version: 1
status: draft
layer: 03.product
domain: storage
disciplines:
- architecture
- security
- sre
- requirements
kind: implementation-plan
purpose: Deliver a provider-neutral, policy-governed object-storage platform and prove a bounded AWS S3 reference only after the operational-realization gate is available.
portability:
  class: source-only
  targets: []
used_by:
- id: product.plan.persistence-foundation-v1
  path: .agentic/03.product/plans/implementation/persistence-foundation-v1.md
- id: product.plan.production-reference-target-baseline
  path: .agentic/03.product/plans/implementation/production-reference-target-baseline.md
- id: harness.architecture.plan.platform-runtime-implementation
  path: .agentic/03.product/plans/implementation/platform-runtime-implementation.md
-->
# Storage Platform v1

## Purpose

Create a reusable platform boundary for profile images, documents, exports,
and later media without making each feature invent its own upload security,
retention, access, processing, or provider integration.

The platform must eventually make this path safe and explainable:

```text
feature declares purpose and approved profiles
        │
        ▼
platform authorises and records an object transfer
        │
        ▼
private provider storage receives untrusted bytes
        │
        ▼
validation / scanning / approved processing
        │
        ▼
authorised, time-bounded delivery or governed lifecycle action
```

This plan is not permission to create an S3 bucket or accept customer files.
It defines the source, policy, infrastructure, and operational evidence needed
before either happens.

## Relationship To Existing Work

`packages/core/src/files/index.ts` already provides a small provider-neutral
vocabulary: file identity, display name, declared content type and size,
checksum, opaque storage reference, scan result, retention fact, access intent,
and a minimal `FileStorage` port. It deliberately does **not** create upload
URLs, buckets, lifecycle resources, scanners, image tooling, or business
document workflows.

That is the correct starting boundary. This plan adds the missing platform
coordination around it; it does not make Core an object-storage SDK or turn the
existing `FileStorage` helper into an unsafe generic file manager.

[Data Governance Foundation v1](data-governance-foundation-v1.md) owns the
shared policy vocabulary and resolver boundary for classification, residency,
lifecycle, permitted processing, transfer, recovery, and evidence. Its Core
vocabulary and provider-neutral resolver stages are prerequisites for this
plan's storage-profile coordination stage. Storage applies the resolved policy;
it does not create a competing residency, retention, or telemetry policy.

The completed DynamoDB/SQS smoke proof remains a proof of one harmless
transactional-delivery path. The PostgreSQL relational reference is an
additive, unfinished persistence option. Neither selects the object-metadata
store for future product files. A storage implementation may begin only after
the provider-neutral operational-realization gate is integrated and the
selected metadata persistence boundary has a compatible, operationally proven
path.

## Outcomes And Non-Outcomes

### This plan delivers

1. A scanable, provider-neutral storage platform with explicit policy,
   transfer, processing, access, lifecycle, reconciliation, and observability
   seams.
2. A clear ownership split between stable Core nouns, feature meaning,
   platform coordination, provider adapters, and target infrastructure.
3. A bounded AWS S3 reference design with a harmless staging smoke proof,
   completed only through reviewed change sets and the realization gate.
4. A route to feature-ready document and image handling that accounts for
   quarantine, malware/DLP selection, tenant isolation, retention, legal hold,
   residency, recovery, and safe access delivery.

### This plan does not deliver

- a product document schema, attachment model, user interface, or business
  document workflow;
- a blanket choice of S3, PostgreSQL, or any scanner for every future feature;
- public buckets, permanent download URLs, arbitrary proxy downloads, or a
  generic file browser;
- a claim that browser multipart uploads, archive restore, OCR, AI, video
  streaming, or bulk transfer are ready before their relevant stages pass;
- a way to place file bytes, object keys, signed URLs, filenames containing
  personal data, scanner output, or extracted text in Git, ordinary logs,
  audit events, metrics, traces, alarms, or evidence records.

## Architecture And Ownership

| Layer | Planned location | Owns | Must not own |
| --- | --- | --- | --- |
| Data governance | `packages/core/src/data-governance/` and `platform/data-governance/` | Shared handling-policy vocabulary and resolved policy. | Storage implementation, provider selection, tenant-policy store, or product document meaning. |
| Core | `packages/core/src/files/` | Durable provider-neutral names, validated metadata, access intent, checksum, retention facts, and minimal storage port. | Provider client, bucket/key layout, URL signing, scanner implementation, product attachment schema. |
| Platform | `platform/storage/` | Storage-specific validation of a resolved policy, transfer/lifecycle state coordination, secure delivery/processing ports, safe errors and telemetry facts. | Product document purpose, shared policy resolution, provider SDK, bucket policy, cloud region, or an arbitrary scanner choice. |
| Provider adapter | `platform/adapters/<provider>/storage/<service>/` | Translation from approved platform operations to one object-storage service and bounded provider-error mapping. | Business authorisation, feature attachment meaning, tenant policy source, infrastructure provisioning. |
| Feature/product | `apps/**` or product package | Object purpose, attachment relationship, permitted user actions, policy-profile selection, business retention rule, and human-review requirement. | Provider key construction, raw object credentials, bucket calls, scanner implementation, or global quota logic. |
| Target/infra | `infra/04.deploy/03.product/targets/<client>/<environment>/` | Buckets, encryption, IAM, networking, lifecycle resources, provider placement, alarm routing, cost limits, and change-set evidence. | TypeScript business workflow or a generic feature API. |

The intended scanable platform layout is:

```text
packages/core/src/files/
  identity.ts          stable object, checksum, name, type, size and opaque-reference nouns
  metadata.ts          bounded safe metadata validation
  access.ts            provider-neutral read/write/delete access intent
  retention.ts         retention and legal-hold facts
  storage.ts           small storage port and put options
  errors.ts            stable error vocabulary
  in-memory.ts         deterministic test helper
  index.ts             deliberate public exports

platform/storage/
  policy.ts            resolved storage-profile constraints and validation
  transfer.ts          upload/download intent and resumable-transfer state
  access.ts            time-bounded delivery-grant coordination
  processing.ts        quarantine, validation, scanner and derivative ports
  lifecycle.ts         delete, restore, archive, purge and legal-hold coordination
  reconciliation.ts    safe orphan and drift detection facts
  observability.ts     profile-governed, allowlisted storage telemetry
  errors.ts            platform storage error translation
  index.ts             deliberate public exports

platform/adapters/aws/storage/s3/
  configuration.ts     injected, validated target configuration
  client.ts            narrow S3 client seam
  transfers.ts         approved upload/delivery translation
  objects.ts           object metadata/head/copy/delete translation
  lifecycle.ts         supported provider lifecycle operations
  errors.ts            finite provider-error mapping
  index.ts             deliberate public exports
```

Every new package receives a local README with a file-by-file source map before
it becomes public.

## Non-Negotiable Rules

1. **An object key is neither an identity nor permission.** The platform owns
   opaque, non-PII provider-key construction. A feature may never construct a
   provider path from a user name, filename, or request value.
2. **A file and its attachment are different.** One immutable object/version
   may be attached to one or more product records. Product attachments carry
   business meaning; generic storage must not learn it.
3. **Untrusted upload is not approved content.** A successful byte transfer
   ends in a non-deliverable quarantine/verification state until the selected
   controls have passed.
4. **Authorisation precedes every capability.** Upload, resume, download,
   preview, export, restore, share, delete, and purge each require a current
   approved policy decision. A past upload grant cannot become a permanent
   download right.
5. **Policy may narrow but not weaken a floor.** A feature selects a named
   approved profile; tenant configuration may narrow quotas, retention, access
   grant lifetime, or permitted types within platform/product floors.
6. **Derived data inherits protection.** Preview, thumbnail, extracted text,
   OCR, transcript, and AI output inherit at least the source object's
   classification, residency, retention, legal-hold, and access constraints.
7. **Logical deletion is a repair state, not erasure.** Restore, legal hold,
   retention expiry, physical purge, provider version cleanup, backup expiry,
   and attachment removal are separate governed decisions.
8. **Safe telemetry describes a fact, not the file.** It may use an approved
   object purpose, finite state/outcome, size band, profile ID, and bounded
   provider category. It must never contain content, filename, object key,
   URL, checksum, raw scanner result, or extracted text.
9. **No live object-storage mutation on an unknown prerequisite.** The
   realization gate must prove source, artifact, identity, dependent resource,
   change-set, recovery, and safe evidence conditions before each target step.

## Storage Profile Model

A feature does not assemble ad-hoc upload rules. It selects an approved,
versioned storage profile which references the resolved data-handling policy.
The storage-specific profile must cover at least:

| Concern | Example platform-owned profile decision |
| --- | --- |
| Object purpose | `profile-image`, `exam-evidence`, `generated-export`; a feature declares an approved name. |
| Type and size | Allowed detected media families, maximum object size, maximum object count, and safe size band. |
| Transfer | Server-mediated versus direct transfer, resumability, expiry, retry, cancel and incomplete-part cleanup. |
| Processing | Required validation, malware/DLP scan, preview/derivative rule, OCR/AI prohibition or reviewed allowance. |
| Access | Delivery mode, grant lifetime, cache disposition, watermark/viewer requirement, sharing rule. |
| Lifecycle | Retention policy reference, restore window, archive eligibility, legal hold, purge rule. |
| Residency | Allowed storage and processing location, replication and support-access restrictions. |
| Operations | Quota, cost attribution, telemetry profile, reconciliation cadence, owner and runbook. |

The storage profile narrows and applies a shared policy; it is not a second
residency/retention/telemetry policy or a provider configuration file. The S3
adapter and target profile translate the resolved requirements into selected
provider controls only at the approved composition boundary.

## Platform State Boundaries

The platform must make transfer, content approval, and lifecycle state
separate so that a file cannot be accidentally delivered because it was merely
uploaded:

```text
requested → authorised → transferring → uploaded → verifying
                                              │
                         ┌────────────────────┴───────────────────┐
                         ▼                                        ▼
                    quarantined                              rejected
                         │
                         ▼
                      approved ──→ archived ──→ restore-requested ──→ approved
                         │
                         ▼
             delete-pending-restore ──→ purge-eligible ──→ purged
```

The exact permitted transitions are profile-governed. A scanner failure,
expired upload, legal hold, missing byte object, or failed archive restore has
a stable error/outcome, not an implicit fallback to approval.

## Staged Delivery Programme

### Cross-cutting prerequisite — data governance foundation

Complete Stages 1 and 2 of
[Data Governance Foundation v1](data-governance-foundation-v1.md) before
creating `platform/storage` policy resolution. The storage platform may own
object-purpose and transfer-specific rules, but it must receive classification,
residency, lifecycle, permitted-processing, recovery, and evidence constraints
from the shared resolved-policy boundary.

**Exit:** one validated provider-neutral handling requirement can be passed to
a deterministic storage fixture without duplicating the policy or relying on a
provider value.

### Stage 0 — admission and dependency map

Before implementation, record the proposed dependency graph in the
operational-realization contract. It must name metadata persistence,
asynchronous processing, scanner/DLP provider, delivery path, object storage,
key/encryption choice, lifecycle policy, alert path, cost ceiling, recovery
path, and all operator identities.

**Exit:** the provider-neutral realization gate is integrated on `main` and
the graph has no unproven or ambiguous mutating edge. No AWS resource changes.

### Stage 1 — organise and preserve Core file contracts

Split the existing `packages/core/src/files/index.ts` by its existing natural
topics, preserving its public barrel and compatibility tests. Add only stable,
provider-neutral identifiers/facts which more than one platform or feature
surface needs. Do not prematurely add S3 concepts, URLs, multipart parts,
scanner vendors, or feature attachment fields.

**Proof:** Core type, runtime, compatibility, and provider-leak boundary tests
pass; the local README maps every source file; existing consumers retain their
public imports.

### Stage 2 — provider-neutral platform storage coordination

Create `platform/storage` with small named files rather than one large index.
Implement storage-profile validation against the resolved handling policy,
transfer intent, approval-state transitions,
time-bounded access-grant port, processing/derivative port, lifecycle intent,
reconciliation fact, finite errors, and profile-governed observability. Supply
only deterministic in-memory implementations for local proof.

**Proof:** unit and contract tests prove denial-by-default, tenant/profile
matching, expiry, stale/resumed transfer rejection, upload-versus-approved
separation, legal-hold-aware lifecycle rejection, orphan reporting without
deletion, and no forbidden telemetry fact. Boundary tests prove no provider
vocabulary enters generic platform code.

### Stage 3 — persistence and asynchronous seams

Define the narrow approved seams to persist authoritative object metadata and
transfer state, relate it to a feature-owned attachment, and schedule safe
processing/lifecycle work through the existing outbox/queue/worker rules.
No platform table becomes a product attachment database; the selected
persistence implementation must provide atomic transitions where a state change
also requires later processing.

**Proof:** local integration tests show that an object cannot become approved
without a completed policy transition, retries remain idempotent, a stale worker
cannot overwrite a newer outcome, and a failed publication leaves recoverable
state rather than silently losing work.

### Stage 4 — AWS S3 adapter source and local contract proof

Create `platform/adapters/aws/storage/s3/` only after Stage 2 ports are stable.
Use injected configuration and a narrow client seam. The adapter may translate
approved object creation, metadata check, transfer/delivery issue, copy/promote,
delete-marker, and error categories that the selected profile needs. It may not
invent a public URL, bypass platform approval, build provider keys from input,
or return raw provider errors.

**Proof:** recording-client tests prove the exact requested operations,
private-only assumptions, encryption and checksum requirements, finite error
mapping, and that signed URL values never enter observability/evidence paths.
No bucket is created in this stage.

### Stage 5 — target design and reviewed change set

Produce a separate `04.deploy` storage target plan and threat model before any
AWS mutation. Select and price the minimum viable target design: bucket
topology (at least quarantined versus approved storage where direct untrusted
upload is enabled), public-access blocks, owner controls, TLS-only policy,
encryption/key choice, region/residency, versioning, lifecycle/archival policy,
service identities, scanner path, delivery boundary, logging/alarms, recovery,
and monthly ceiling.

The design must explicitly decide whether the first reference supports only a
harmless service-controlled transfer or browser direct/resumable upload. It
must not describe a scanner, archive, Object Lock/legal hold, OCR, or AI path
as operational merely because S3 can store bytes.

**Exit:** an inspected change set, least-privilege operation contract,
rollback/recovery plan, target evidence schema, and cost estimate pass the
realization gate. Still no execution without a separately approved AWS change.

### Stage 6 — bounded Kanbien/staging S3 reference proof

After a specific AWS approval, create only the reviewed target resources and
execute one fixed harmless synthetic object flow. The proof is bounded to one
opaque object identifier and safe aggregate facts:

```text
authorised storage intent
  → private quarantine write
  → selected validation/scan proof
  → approved transition/promotion
  → authorised short-lived delivery check
  → logical delete and restoration check where selected
  → final no-unexpected-object / healthy-alarm / cost-state evidence
```

It must separately prove denied unauthorised/expired delivery, no public
access, tenant/purpose isolation, safe telemetry, queue/worker drain where
processing is asynchronous, and clean rollback/recovery. It records only
aggregate outcomes and stable evidence identifiers.

**Exit:** the first S3 reference is operationally proven for its exact selected
profile, not for arbitrary file types or future business documents.

### Stage 7 — feature-ready document and image baseline

Before accepting real profile images or documents, finish the selected
untrusted-content control path: content sniffing versus declared type, size and
quota enforcement, malware/DLP scanning, quarantine response, safe preview
handling, processor timeout/retry/DLQ policy, access/audit profile, tenant
isolation negative tests, retention/restore/purge evidence, and support
runbook. This stage also adds the feature-consumption decision record and its
validation to each new file-using capability.

**Exit:** an approved feature can reuse a named profile without calling a
provider SDK or reimplementing its own security workflow.

### Stage 8 — advanced delivery and processing, each separately proven

These are independent promotions, not hidden assumptions in Stage 7:

- multipart/resumable transfers, cancellation, retry and stale-part cleanup;
- concurrent transfer admission/progress facts and client-owned UI queue;
- archive/cold-tier transitions, restore request/status, cost guard and
  restoration test;
- streaming/range delivery and cache controls;
- preview, thumbnail, OCR, transcription, or file extraction;
- AI-assisted processing with explicit purpose, residency, prompt isolation,
  output classification, provenance and human review;
- bulk upload/download manifests, per-item outcome, partial-failure policy,
  rate limits and controlled operator recovery.

Each promotion needs a profile extension, threat model, adapter/infra impact,
negative tests, operator runbook, cost assessment, and evidence rehearsal.

## Evidence And Observability Requirements

Storage telemetry uses the existing profile-governed observability model. It
may report finite facts such as object purpose, transfer state, outcome,
bounded error category, approved storage profile, size band, processing class,
and target/environment. It must not create per-object, per-tenant, filename,
checksum, request, correlation, or URL metric labels.

The target plan must declare separate operational, security, and audit records:

| Record class | Question answered | Example permitted fact |
| --- | --- | --- |
| Operational telemetry | Is the transfer/processor/lifecycle path healthy? | `processing=scan`, `outcome=retryable-failure`, `size_band=1mb-10mb` |
| Security record | Was a protective control denied or changed? | `operation=deliver`, `decision=denied`, `reason=expired-grant` |
| Audit event | Who performed an accountable object lifecycle action? | `action=restore-requested`, `object_purpose=exam-evidence`, `outcome=accepted` |

No class is a substitute for another, and none contains file contents or a
credential-bearing delivery location.

## Completion Criteria

The storage platform is not described as *feature-ready* until all of the
following are true for the selected profile:

- source contracts, boundaries, deterministic tests, and package source maps
  pass;
- an authoritative metadata/attachment path has a selected, proven persistence
  boundary and consumes the same resolved handling policy;
- untrusted bytes cannot be delivered as approved content before the required
  controls pass;
- target infrastructure has private access, encryption, residency, scoped
  identities, lifecycle, cost, and recovery evidence;
- a harmless live proof shows allow and deny behaviour, processing recovery,
  access expiry, safe telemetry, and no residual synthetic work; and
- the feature consumption record captures purpose, classification, profile,
  retention, sharing, processing, and human-review decisions.

## Deferred Decisions

The following stay deliberately open until a real approved feature creates a
requirement: exact scanner/DLP provider, customer-managed versus provider
managed key, browser direct-upload topology, Object Lock/legal-hold mechanism,
archive class and restore objective, cross-region recovery, deduplication,
watermarking, OCR/AI processor, media streaming, and bulk transfer experience.
Each has material security, cost, or product consequences; none should be
guessed through a generic default.

## Related Artifacts

- `packages/core/src/files/index.ts` — current minimal Core file contract.
- `docs/03.product/rules/platform/concerns/persistence-files-storage.yml` —
  cross-cutting ownership and safety rule.
- `.agentic/03.product/plans/implementation/persistence-foundation-v1.md` —
  current transaction/outbox/lifecycle foundation.
- `.agentic/03.product/plans/implementation/data-governance-foundation-v1.md`
  — shared handling-policy and resolution foundation.
- `.agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md`
  — additive relational-reference path; it is not a storage selection.
- `docs/04.deploy/plans/kanbien-staging-aws-change-reliability-programme.md`
  — target-specific deployment reliability direction.
- `docs/04.deploy/plans/kanbien-staging-platform-foundation-convergence-v1.md`
  — integrated source-to-target programme and ordered S3-reference train.
