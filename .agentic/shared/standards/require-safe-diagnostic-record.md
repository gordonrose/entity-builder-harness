<!-- agentic-artifact:
schema: agentic-artifact/v3
id: shared.standards.safe-diagnostic-record
version: 7
status: active
created_on: "2026-10-23"
updated_on: "2026-11-04"
layer: 06.shared
domain: diagnostics
disciplines: [security, sre, agentic]
kind: standard
purpose: Require safe, bounded, actionable diagnostic records across product and deployment layers.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.standard.persistence-diagnostic-mapping
  path: .agentic/04.deploy/60-run/standards/require-persistence-diagnostic-mapping.md
-->
# Require Safe Diagnostic Records

A diagnostic records an observed failure class and the next governed check. It
does not expose raw implementation detail, infer an unproved cause, or grant
permission for an unsafe repair.

Every diagnostic record has a stable code, logical dependency and scope where
applicable, lifecycle stage, workload identity where applicable, safe summary,
retryability, and bounded next check. Stable codes are controlled vocabulary,
not ad-hoc message text. An unknown observation uses a named unclassified code
with stop-and-escalate behaviour; it never becomes permission to guess, expose
raw output, replay uncertain work, or mutate a target.

A deployment-operation diagnostic additionally records the named operation,
whether its effect is known, unknown, pending, rejected, or failed, and a
reference to retained evidence. It names the next permitted observation or
retry decision. A timeout, interrupted response, or failed diagnosis remains
an *unknown operation outcome* until the governed reconciliation route proves
otherwise; it is never authority to resubmit a mutation.

Repository artifacts, reports, logs, and diagnostics must not contain secret
or credential values, tokens, connection strings, hostnames or internal
addresses, certificate bodies, SQL values, raw provider responses, or personal
data. A provider reference is not a secret value, but it belongs in the
provider binding rather than a portable diagnostic record. Pattern redaction
is a useful boundary check; it is not a general secret or PII detector. Do not
retain or print arbitrary provider response bodies merely because a pattern
redactor removed one apparent credential. Useful provider facts are copied
only into a field explicitly allowed by the owning report schema, such as a
resource logical identifier, resource type, provider status, or safe property
path. If no safe fact is available, report that fact as unavailable rather than
guessing from raw output.

Credential-bearing commands require an end-to-end logging review, not only a
check of the program's own output. Before a command can create, alter, rotate,
or revoke a database credential, its owner must identify downstream logs and
error surfaces (for example, database-server logs, provider logs, shell
tracing, task logs, and retained CI artifacts). Plaintext passwords, derived
password verifiers, authentication tokens, and connection strings are all
sensitive credential material. A hash or redaction pattern does not make one
safe to put in a command or diagnostic. Qualification must exercise a rejected
path where practical and inspect the applicable downstream logs using only
synthetic canaries; it must not suppress error logging merely to pass.

The product/core layer owns bounded provider-neutral diagnostic primitives.
Platform capabilities own provider-neutral meaning and safe workload effects.
Provider adapters translate provider facts privately into those meanings.
Deploy declarations state the lifecycle consequence and proof requirement.
Deployment scripts preserve child exit status and emit only safe bounded
diagnostics. No one layer substitutes for another's provider observation or
live proof.

## Executable definitions and adoption

`packages/core/src/diagnostics/` owns the closed schema subset, definition and
record constructors and parser. A definition is a reviewed, versioned list of
allowed fields and values; arbitrary strings and raw exception objects are not
allowed in its detail. Existing primitive descriptor facts remain compatible
and do not become permission for structured unchecked detail. Error helpers
preserve the separate `diagnosticRecord` when supplied.

Each capability or app owns its definitions in runtime source. Platform owns
catalog registration, namespace enforcement and internal delivery. Adapters
classify only evidence from the failed invocation. Target composition binds
logical settings to environment keys and selects catalogs and sinks. Python
and other consumers read generated runtime exports; harness schemas must not
become a second vocabulary registry.

## Module-local catalogue exports

When adopting or refactoring a substantial module's diagnostic catalogue, keep
its executable definitions and explicit selected catalogue with that module's
reporting contract. Generate local JSON from those objects with the existing
exporter; never author a second list of fields, reasons or definitions in JSON.
Config is the reference: `packages/core/src/config/contract/reporting/diagnostics.ts`
owns its definitions/catalogue and the adjacent `diagnostics.v1.json` is derived.
Use the module's public TypeScript export and a declared package JSON subpath,
not an external import of private contract files. Public indexes only re-export.

Retain supported aggregate catalogues and historical code/version contracts.
Local and aggregate outputs must derive from the same definition objects, with
conflicting identities rejected. An export-format version is separate from the
versions of individual definitions. A local selection must not silently widen
an operation-specific reader or make unrelated records acceptable. Migration
does not mean removing other modules from the retained aggregate.

Prove exact module membership, public access and asset inclusion in the affected
package/compiled fixture, deterministic generation, stale-output rejection and
historical reader acceptance/rejection. TypeScript compilation alone does not
prove an unimported JSON asset was copied. Update export-enumerating tooling
without weakening module boundaries or forcing unused assets into every runtime.
Account for actual consumers in the existing task/review inventory. Future
adoption is scoped work, not a requirement to retrofit every module immediately.

## Shared names and versioned selections

A shared collection of reason names supplies reusable wording; it is not the
allowed-reason selection for every diagnostic. Each owning code/version chooses
its applicable names explicitly. Do not derive a published definition's choices
from all entries of a growing shared collection, including via Object.values or
a compatibility list. Capability-specific reasons remain with their capability;
Core is not a registry for every provider or workload condition.

Adding a shared name alone must leave every existing definition unchanged. To
accept another reason under an existing code, introduce a new definition version
and retain supported historical definitions and readers under the existing
compatibility rules. Fixed legacy exports/default selections stay fixed for
compatibility; new definitions select names rather than introducing progressively
larger global lists. Runtime source owns both names and selections, not harness
schemas or separately edited generated catalogs.

Review direct and indirect users, including type-only users, wrappers, catalog
assembly and non-TypeScript readers. Record explicit no-change decisions. Prove
that fixture-only growth of shared names cannot widen retained definitions, that
same-version widening fails compatibility, and that supported new-version and
historical records reach their actual readers. Do not refresh snapshots to hide
an unapproved change. Reuse existing compatibility and caller fixtures instead
of adding another registry or check framework.

## Context and consumer obligations

At the final internal reporting boundary, an investigating agent must be able
to identify the attempted operation, logical item or source, failure step,
observed condition, established effect/outcome, remaining uncertainty and next
permitted investigation where applicable. Account for each fact in the owning
task's existing inventory: its supplier, runtime contract, report/context or
code-owned lookup, and proving consumer test. Explicitly explain non-applicable
facts; do not fabricate a value to fill a required field. Known outcome of a
source read is not automatically known outcome of the enclosing operation.

This is a requirement on the assembled explanation, not permission to add all
fields to every Core record. Shared Core diagnostics owns record mechanisms;
each capability owns its reusable meanings and observations; Platform owns
reusable workload context and approved delivery; adapters translate positively
observed provider facts; entrypoints supply concrete bindings and execution
context. An operation's code/version may identify fixed meaning without copying
that meaning into every payload. An investigation instruction must be governed,
bounded and safe; it never grants mutation or replay authority.

The consuming responsibility must require its needed context through an owning
interface and validated construction path. Use typed required fields and runtime
checks for unchecked/declaration boundaries. Prefer code-owned permitted choices
and legitimate combinations over arbitrary strings or a universal all-optional
context object. Bind fixed context once during assembly when useful; introduce
no mandatory service wrapper, parallel manifest or context registry. Do not
require a Core import in a caller that correctly uses an existing checked wrapper.

Core need not know a caller's startup/request/job context, and callers must not
guess Core observations. For multiple inputs, distinguish problems established
from checks prevented by a read failure. Source-access failure does not mean
missing/invalid contents; an unexplained exception does not mean access denied.
Preserve existing continuation/throwing behavior unless a change is explicitly
approved. Checked values, failure handling and report preservation must reach
the actual consumer before dependent work where the contract requires rejection.

Validate operation bindings before dependent work where practical. A failure
while delivering diagnostics must not replace the original workload outcome,
expose rejected context or replay the operation. Preserve existing opt-outs and
internal/public disclosure boundaries. Closed fields and valid records establish
representation, not diagnostic truth or correct attribution to a setting/stage.
Actual caller/delivery tests and source review must establish those claims.

### Reuse optional delivery mechanics

For new or refactored optional diagnostic delivery, use Core diagnostics'
`deliverDiagnosticRecord` or `deliverDiagnosticRecords`, implemented in
`packages/core/src/diagnostics/reporting/delivery.ts` and exposed through
the public module. Owners still validate/select records with the existing Core
record functions and supply their approved context through a receiver closure.
Delivery does not validate contents, establish diagnostic truth, await completion,
retry, confirm a log write or authorise replay. Keep source selection, diagnostic
meanings, opt-outs and context with their existing owners.

Do not independently copy exception/rejected-result handling into each adapter
or capability. In the existing consumer inventory, record any required different
semantics, including status-bearing sink completion and pinned legacy indexes;
do not weaken those contracts or silently expand the task to migrate them.
Prove actual helper use and original result/error, call order, receiver/context,
return identity and reporting-failure isolation through existing caller fixtures.
Architectural review and bounded substitution tests establish reuse here; source
hashes and schema checks alone do not prove the absence of copied mechanics.

Evolve context requirements with their consumers. Use existing compatibility
rules for versioned records; adding a required field or widening allowed choices
is not a structural file move. Upgrade readers before emission and retain supported
historical definitions. Runtime source owns schemas/choices; READMEs explain and
link to the harness, and generated JSON stays derived rather than separately edited.

## Supported reason preservation

For new or changed diagnostic paths and scoped adoption/refactoring, every
supported failure established by the operation must retain its safe meaning
and applicable item/operation context through to the actual error-handling
consumer. Trace actual checks and returned failures, not only names already
listed in a catalogue. A shared reason name is not automatically applicable to
every operation. Missing mappings, wrong attribution, unselected owned
definitions and precise-to-generic reductions are not fixed by merely emitting
some valid record or replacing them with diagnostic-unavailable.

Apply the existing [ownership and module structure rules](../../03.product/standards/public-module-structure.md#dependency-direction-and-diagnostic-ownership).
Correct the responsible producer, mapping, definition selection, registration
or caller. Reuse genuinely shared mechanisms; keep capability/provider meaning
with its owner and concrete bindings in composition. Do not move dependency
rules into entrypoints, accumulate service-specific meanings in Core, or create
another mapping registry. Reuse correct definitions; changes to allowed detail
follow the existing versioning rules. Generated JSON remains derived.

Normal-failure proof uses inputs or controlled dependency responses that trigger
the real operation's supported check, with its real diagnostic builder and
wrappers. Assert the exact code/version, reason and applicable context at the
actual consumer. Include successes, supported failure alternatives/combinations,
and sensitive-value exclusion. Preserve first-error/collection policy, explicit
truncation, original workload results and effects; do not invent checks or
causes. Demonstrate that material dropped/mislabelled/genericized-reason or
missing-registration counterexamples fail the owning assertions, using bounded
existing fixtures rather than a blanket mutation campaign.

Separately test unexpected diagnostic-processing failure. That safeguard cannot
substitute for normal reason-preservation proof. Strict rejection of untrusted
evidence remains required; report only safely established processing outcomes,
not raw rejected content. A compatibility helper returning undefined is not
itself proof of production loss: inspect the real caller and prove its use of
the supported structured-result path where required. Record deliberate opt-outs
and evidence limits. Packet preservation does not establish logger acceptance
or remote delivery; those require their own consumer proof.

These are source-review and behaviour-test obligations, not claims that the
structural adoption scanner proves all reason paths. Unproved in-scope paths
remain open; a sample does not certify repository-wide completeness.

## Adoption proof and limits

For every new or changed configuration, attribute validation, call, connection,
endpoint, job or lifecycle boundary, identify the exact observed predicate,
safe detail, effect that is actually known, and next permitted observation.
Record unproved causes and effects as unknown. Test every declared alternative,
multiple independent issues, wrapper preservation, malformed/unrecognized
evidence, sensitive canaries, sink failure and public-response exclusion where
applicable. A combined guard returning `undefined` is not an adequate diagnostic
when the code can safely identify the failed setting or check.

The [diagnostic coverage workflow](../workflows/verify-diagnostic-coverage.md)
owns adoption and review. Its structural gate discovers ordinary code without
requiring a deployment. An unchanged legacy baseline is debt, not compliance;
a source-matched partial review names remaining debt. Passing structural checks
does not establish semantic completeness, actual image qualification or live
failure behavior. Do not claim those proof levels interchangeably.
