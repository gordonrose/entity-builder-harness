<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.deployment-operation-diagnostic.v1.guide
version: 2
status: draft
created_on: "2026-10-25"
updated_on: "2026-10-31"
layer: 04.deploy
domain: deployment.diagnostics
disciplines: [security, sre, agentic]
kind: guide
purpose: Explain how to create and consume retained deployment-operation diagnostics.
portability: { class: reusable, targets: [entity-builder] }
used_by:
  - id: deploy.schema.deployment-operation-diagnostic.v1
    path: .agentic/04.deploy/schemas/deployment-operation-diagnostic.v1.schema.yml
-->
# Deployment Operation Diagnostic v1 Guide

This report records one failed or uncertain deployment operation. It is not an
application diagnostic record, a package qualification receipt, or a release
acceptance receipt.

`operation_id` is a deterministic, non-secret identity chosen before a
protected provider mutation. `operation_outcome` says what has actually been
observed: a rejected provider request is not the same as a failed asynchronous
operation, and neither is the same as an interrupted response with unknown
effect. `next_action.decision` must therefore be one of the small controlled
vocabulary in the schema. In particular, an `unknown` outcome normally permits
only `observe-current-operation` or `inspect-retained-evidence`.

`evidence.reference` points to the governed retained artifact or operation
receipt. It is opaque: it may identify a CI artifact, a receipt path, or a
provider operation identity, but must not be a URL, endpoint, account number,
or copied provider response. `collection` says whether bounded diagnosis was
available: its status is `collected`, `unavailable`, or `failed`. Optional
collection observations distinguish incomplete or malformed evidence without
introducing `pending` or `partial` collection statuses. `pending` remains an
operation outcome, not a collection status. A failure or delay collecting
diagnostics never changes the original failure or exit status. Historical v1
reports may omit the optional collection observation fields.

`facts` is optional and intentionally small. Only the exact fields listed in
the schema may be supplied. Resource logical identifiers, resource types,
provider lifecycle status, and a property *path* can be useful. Property
values, raw error text, hostnames, request IDs, credentials, and arbitrary
extra fields are not safe facts.

For CloudFormation, the AWS helper reads the named change set and bounded stack
events after the operation. It classifies only known patterns and otherwise
records `provider-details-unavailable`. It does not infer a root cause from a
missing event, and it does not repeat a create or execute operation.

Optional `execution` copies only the validated closed adapter observation:
classification, code-presence status, actual call phase and elapsed milliseconds
(or null). `pool_connect` does not identify an internal handshake stage;
`pool_query` includes acquisition. TCP and TLS probes have their own phases and
connections. `query_canceled` does not establish whether a deadline or explicit
cancellation caused it. No observation grants retry authority.

Optional `diagnostic` retains a validated core record from the explicitly
selected target, persistence or shared-security catalog. Source validation, file
access and certificate-content failures remain distinct configuration outcomes.
Runtime persistence records retain the actual operation and observed call
boundary. The shared reader reconstructs allowed fields from runtime exports;
it never retains source values, paths, certificate bodies or native errors.
Older reports without the field remain valid. Success results cannot carry
failure detail. Execution vocabularies likewise come from the persistence
catalog, not a second list maintained in this schema.

Optional `related_diagnostics` retains bounded peer-identity or peer-trust
observations beside a TLS-classified persistence primary. The list limit comes
from the generated delivery contract; every member is independently validated.
Task readers bind the primary to the reported operation and, for restore
results, require agreement with the execution observation. A content-parsing
record is not a runtime peer-verification companion. Historical definition
versions remain readable; revised attribution does not rewrite retained records.
Neither the primary nor its companions establish provider fault or authorize
replay of an uncertain operation.

Optional `task_failure` retains one explicitly validated private
`deploy/persistence-task-failure/v1` envelope. Its finite result codes, owning
observation definitions and both collection limits come from the generated
target contract, not this guide. It preserves the first selected source primary
and eight companions, bounded additional complete `source_bundles`, independent
task `observations`, and explicit nonzero `overflow` counters. Suppression counts
describe unretained occurrences, not proven unique causes. The historical
`diagnostic` reader is not broadened to accept these private task observations.
Unknown fields, unrelated task records and unselected source evidence are rejected.

For a failed verifier, one bounded read of its already identified log stream
may retain multiple validated rejection observations. Keep the first valid
code/source, merge only within the exported limits, and retain validated facts
through unrelated malformed lines or collection failure. Saturated windows or
unrepresentable aggregate counters remain incomplete, never proof of acceptance.
Successful verifier reads, acceptance and retry rules do not change. Historical
success/rejection and restore-v2 envelopes remain readable without rewriting.

Optional collection `observation` distinguishes complete, empty, unrecognized,
malformed, incomplete, unavailable and failed observations. `attempts` counts
at most three bounded reads in this invocation. Successful log reads can still
be incomplete because pagination or export delay prevents a complete window.
Historical v1 records lacking these optional fields remain valid. The shared
builder, validator and CLI own the reader; retained reports are never migrated
in place. Reconciliation writes a new diagnostic observation, preserving prior
records and the original safe verifier code/status.

`collection.task_observation` and `task_attempts` describe the verifier-log
stream independently from the server-log window. A unique validated rejection
survives malformed, unrecognized, missing later pages or failed collection;
acceptance still requires a complete, valid success observation. A saturated
page is incomplete. The evidence reference can include the safe ECS task id;
`facts.artifact_identity` retains the observed immutable image digest.

`authentication_material_invalid` is a closed adapter classification for the
exact installed pg SCRAM invariant. The message is inspected privately and never
retained. Its machine-code status remains `absent` or `unrecognized`; a known
library invariant does not invent a recognized provider code. Its observed phase
is the actual failed driver operation, usually `pool_connect`.
