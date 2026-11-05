<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.diagnostics.readme
version: 3
status: active
created_on: "2026-10-27"
updated_on: "2026-11-02"
layer: 06.shared
domain: diagnostics
disciplines: [architecture, security, sre, agentic]
kind: documentation
purpose: Explain diagnostic contract generation, independent adoption checks and their limits.
portability: {class: source-only, targets: []}
used_by:
- id: repo.diagnostics.coverage
  path: scripts/repo/diagnostic-coverage/script.sh
-->
# Diagnostic adoption checks

`script.sh` discovers executable source independently of deployments and compares
it with the immutable initial Git baseline and `reviews.v1.json`. Its JSON report
lists unchanged legacy debt explicitly. A new/changed file needs an owned review
whose SHA-256 matches its bytes, with exact tests and registered local check IDs.
The selector consumes these check references for ordinary, non-deployed code too.
This is a structural review/freshness check, not static proof that every possible
failure has a diagnostic. The linked behavior tests establish the reviewed claims.

The source census includes executable `bin/` commands even when they are not a
workspace or deployment. Discovery does not grant permission to modify imported
workbench files: those retain their upstream ownership and exception rules.

`verify.sh` compiles code-owned definitions, checks generated catalog snapshots,
compares TypeScript and Python readers against hostile input, exercises discovery
fixtures and runs affected package/app checks. PostgreSQL protocol, target payload
and controller checks remain with their existing registered owners.

To regenerate reviewed contract snapshots after a source/schema change:

```bash
node_modules/.bin/tsc -p scripts/repo/diagnostic-coverage/tsconfig.json
NODE_PATH="$PWD/node_modules" node scripts/repo/diagnostic-coverage/export-catalogs.mjs --compiled-root .cache/diagnostic-catalog-export
bash scripts/repo/diagnostic-coverage/verify.sh
```

`--check` on the exporter compares without rewriting snapshots. Do not edit
generated JSON to define new values. Runtime source remains authoritative.
Config is the first Core module with an adjacent generated catalogue:
`packages/core/src/config/contract/reporting/diagnostics.v1.json`. Its executable
owner exports `coreConfigDiagnosticCatalog` through `@kanbien/core/config`;
the public JSON address is `@kanbien/core/config/diagnostics.v1.json`.
The existing generator produces this four-definition view and the retained
whole-Core `packages/core/contracts/diagnostics.v1.json` from the same objects.
Its temporary compiled package copies the JSON asset explicitly; compiling
TypeScript alone would not include it. The reader tests prove selected-module
membership, public resolution, stale/conflicting-output rejection and aggregate
compatibility. This does not migrate every Core module or widen native readers.

For focused final catalogue/reader proof, use the existing registered unit
`diagnostic-catalog-readers`; the complete aggregate above remains an integration
boundary, not an instruction to run every runtime suite after each small edit.
Committed code/version identities are immutable: a changed schema needs a new
version while the old definition remains available to retained readers. The
exporter compares with HEAD and rejects changes/removals even when a snapshot is
regenerated. A future retirement needs an explicit governed compatibility path.
The generator resolves reviewed local compiled modules; it performs no provider
operation. The Python reader reconstructs the same closed subset without a second
capability vocabulary. Errors never return submitted values.

Core, Platform contract registration and platform-target configuration now have
explicit exports alongside existing capability catalogs. The platform-target
file is `entrypoints/contracts/kanbien-platform-diagnostics.v1.json`; the existing
`entrypoints/contracts/diagnostics.v1.json` remains core-server-persistence-owned.
The generic selected-record reader admits the exact current composition owners,
including worker/server/app configuration evidence. Operation-specific and
certificate/configuration readers remain narrower; selection does not make an
unrelated record valid in their envelopes. Add a real owner selection and
TypeScript/Python parity/rejection cases when an actual producer is introduced;
there is no unknown-code fallback or harness-owned duplicate vocabulary.

Core-server acceptance request predicates have their own app-owned export,
`entrypoints/contracts/kanbien-core-server-acceptance-diagnostics.v1.json`.
Its missing/type/format observations are registered through the app mount and
selected by the generic reader, not by configuration or database-operation
readers. They contain logical fields only, never submitted identifiers/digests.

The registered `dynamodb-persistence-runtime` leaf dispatches the existing complete
adapter check through `verify.sh --unit dynamodb-persistence`: typecheck, build,
runtime tests and dependency-boundary proof remain intact. It is a reusable
owned unit, not a replacement for app/target/payload or live-provider proof.

Queue delivery target predicates have a separate code-owned export,
`entrypoints/contracts/kanbien-platform-delivery-diagnostics.v1.json`. Core queue,
relay and Worker delivery observations are selected by generic composed readers,
not configuration or native database-operation readers. Literal cross-language
tests retain these boundaries and reject private or invented detail. The
`sqs-queue-runtime` leaf dispatches the existing complete adapter check through
`verify.sh --unit sqs-queue`; real target bindings remain with the compiled
payload owner. Local injected-port proof is not provider delivery qualification.

Persistence task envelopes retain validated Core/Persistence primary and bounded
source companions, including local rejection and boundary observations. Security
peer companions still require a positively classified TLS primary; certificate
content and unrelated configuration records do not become peer evidence. The
TypeScript projector and Python consumer share literal parity/rejection tests.
New CRUD v3 records do not alter the historical v1/v2 operation or execution
vocabulary; an uncertain client write is not labelled as unstarted or rejected.
An operation envelope explicitly opts into retaining a selected Core source primary: its operation
describes the source helper, not the enclosing task. Native Persistence primaries
still require the exact enclosing operation, and native restore execution facts
must agree. Independently validated Core source facts are not reinterpreted as
native execution facts. Existing successful/configuration envelope restrictions
and TLS pairing remain effective in the actual task readers.
The default operation reader remains Persistence-only; generic configuration
records cannot acquire operation meaning merely because they are Core records.

Adoption statuses are `adopted`, `partial` and `support`. Adopted reviews name
definitions and accuracy/disclosure/preservation/uncertainty proof. Partial
reviews identify concrete remaining debt. Supporting schema and verification
plumbing is not counted as adopted operational code. The gate has no blanket
update command; changing a source hash requires reviewing that source and proof.
The baseline commit must be available locally; CI already fetches full history.

Keep review records focused on the capability that owns the reviewed sources.
Each registered check binds the entire record, including its reasons, source
hashes and tests. Grouping independent capabilities therefore makes a change to
one invalidate the others' proof. Preserve genuine shared delivery, readiness
and companion-catalog checks; a shared definition can be referenced by downstream
records without merging source ownership. Name exact behavior tests and retain
partial debt when splitting records. The config, observability delivery,
persistence, server and worker reviews illustrate these separate owners; their
regression protects that separation without prohibiting integrated capabilities.

See [the workflow](../../../.agentic/shared/workflows/verify-diagnostic-coverage.md)
for ownership, stop conditions and deployment proof boundaries.
