<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.deployment-operation-diagnostic.v1.guide
version: 1
status: draft
created_on: "2026-10-25"
updated_on: "2026-10-26"
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
available. `pending` means the source's declared delivery window has not
elapsed; `partial` means some required bounded sources were observed but at
least one was unavailable. They are not clean observations and require the
declared follow-up decision. A failure or delay collecting diagnostics never
changes the original failure or exit status.

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
