<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.deployment-operation-diagnostic.v1.guide
version: 1
status: draft
created_on: "2026-10-25"
updated_on: "2026-10-25"
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
available. A failure collecting diagnostics never changes the original failure
or exit status.

`facts` is optional and intentionally small. Only the exact fields listed in
the schema may be supplied. Resource logical identifiers, resource types,
provider lifecycle status, and a property *path* can be useful. Property
values, raw error text, hostnames, request IDs, credentials, and arbitrary
extra fields are not safe facts.

For CloudFormation, the AWS helper reads the named change set and bounded stack
events after the operation. It classifies only known patterns and otherwise
records `provider-details-unavailable`. It does not infer a root cause from a
missing event, and it does not repeat a create or execute operation.
