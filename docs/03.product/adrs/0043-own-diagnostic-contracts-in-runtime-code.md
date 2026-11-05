<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.adr.0043-own-diagnostic-contracts-in-runtime-code
version: 1
status: active
created_on: "2026-10-27"
updated_on: "2026-10-27"
layer: 03.product
domain: architecture.diagnostics
disciplines: [architecture, security, sre]
kind: adr
purpose: Keep diagnostic schemas and meanings in upstream runtime code with governed adoption and compatibility.
portability: {class: source-only, targets: []}
used_by:
- id: product.adrs.readme
  path: docs/03.product/adrs/README.md
- id: shared.workflow.verify-diagnostic-coverage
  path: .agentic/shared/workflows/verify-diagnostic-coverage.md
-->
# ADR 0043 Own diagnostic contracts in runtime code

## Status

Accepted for the user-authorized local diagnostic implementation project.

## Context

The repository already separates primitive recovery descriptors, validation
issues, operational profiles, public errors, readiness, audit and deployment
operation reports. These remain useful. A coarse missing/invalid result can,
however, discard a safely knowable setting or predicate. Harness-only rules do
not give implementations typed fields, validators or consistent permitted values.

## Decision

Core owns executable closed diagnostic schemas, versioned identities and record
constructors/parsers. The existing primitive descriptor and its recovery policy
remain intact. `CoreError.diagnosticRecord` carries independently validated detail
without changing descriptor facts or public error messages.

An error may retain a bounded list of related diagnostic records when one failed
operation has distinct capability and cross-cutting observations. The list bound
belongs to Core and is exported for other-language readers. Every record keeps
its own identity, version and closed schema; this is not recursive cause storage.
Internal reporters validate each selected record and isolate delivery failures.
Task consumers validate the list and bind its observations to the reported
operation before retaining them. Public errors and metric labels do not acquire
these related records.

Capabilities own operational meaning. Apps own business meaning and register
their catalogs through app mount. Platform validates ownership and conflicts,
selects catalogs and provides bounded internal reporting before startup and
during request/job execution. Operational log opt-outs remain effective; detail
does not become a metric label, HTTP body or audit record.

Cross-cutting security meaning belongs to security rather than the first
capability that uses it. Core security owns provider-neutral observation reasons;
platform security owns executable certificate-content and peer-verification
definitions and reusable runtime parsing. Provider adapters translate positive
evidence and targets bind sources. Configuration, source access, content syntax,
peer verification and transport outcomes remain distinct. Parsing does not prove
trust, and a failed verification alone does not establish an accountable source
or an application's operation outcome. Existing capability identities remain
compatible while their producers migrate separately.

Configuration-source access has its own Core configuration reasons and Platform
configuration definitions. Target path policy and filesystem evidence remain
separate from certificate-content syntax. Block-specific content failures may
identify a one-based block position without disclosing certificate contents.
Stricter certificate-marker acceptance is an explicit policy decision, not an
implicit consequence of adopting richer diagnostics.

Validated internal log envelopes have package-private provenance and their own
closed record budget. The safe logger preserves that approved detail instead of
truncating it as arbitrary data. Raw lookalike records do not acquire this path.
Default and target-added sensitive-key policies still apply: a conflicting sink
policy blocks delivery rather than silently changing a diagnostic's meaning.

Adapters translate only evidence observed during the actual invocation. Targets
bind logical settings to source keys and select providers. A separate successful
probe is not evidence of the failed connection's phase. A cancellation is not
proof of its cause, and a failed response does not establish a write's outcome.

<!-- deterministic-check: allow reason="compatibility.mjs and export-catalogs.mjs enforce immutable retained identities; this ADR records the decision, not a second procedure" -->
Cross-language consumers read deterministic exports from executable definitions.
Committed diagnostic identity/version pairs are immutable. New schemas add a new
version and retain the old definition until a governed retirement path exists.
Harness declarations retain workload effects, next checks, recovery authority and
proof obligations; they do not maintain duplicate diagnostic vocabularies.

The adoption gate independently discovers ordinary executable code and configured
workspace source roots. An immutable baseline exposes legacy debt. Changed/new
code needs a source-matched owned review and registered tests. Partial adoption
must name remaining debt; a structural pass is not full behavioral coverage.

## Consequences

Consumers are upgraded before new fields are emitted. Historical report readers,
public codes, healthy deployment behavior, deadlines and workload privileges
remain compatible. Generated exports and source review hashes must be refreshed
when their reviewed definitions or behavior change.

Closed enums deliberately exclude free text and arbitrary identifiers. Adding a
new safe fact requires a reviewed schema/version and consumer tests. Unknown
failures lose speculative detail but never expose raw errors or grant replay.
Legacy adoption remains incremental and visible rather than requiring an unsafe
repository-wide rewrite. Local source tests do not replace container or live
qualification and do not modify accepted release evidence.
