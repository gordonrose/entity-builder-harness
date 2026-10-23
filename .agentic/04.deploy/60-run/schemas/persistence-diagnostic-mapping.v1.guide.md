<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.persistence-diagnostic-mapping.v1.guide
version: 3
status: active
created_on: "2026-10-23"
updated_on: "2026-10-23"
layer: 04.deploy
domain: deployment.persistence-diagnostics
disciplines: [security, sre, agentic]
kind: guide
purpose: Explain safe provider-neutral persistence diagnostic mappings for scope declarations.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.schema.persistence-diagnostic-mapping.v1
  path: .agentic/04.deploy/60-run/schemas/persistence-diagnostic-mapping.v1.schema.yml
-->
# Persistence Diagnostic Mapping v1 Guide

Every new-framework scope declares `persistence_diagnostics` and classifies
its persistence dependencies in `dependencies.persistence`. A scope without
persistence uses `status: not-applicable`, explicitly excludes `persistence`,
declares `dependencies.persistence: []`, has no migration or server-mediated
dependency use, and has no workload declaring `persistence_writes: true`. It
does not omit the field. A scope with a
required persistence dependency uses `status: declared`, repeats that
dependency ID from the nonempty `dependencies.persistence` list, and maps the
controlled taxonomy for every workload that can encounter it. The validator
does not infer a dependency’s kind from its identifier.

The mapping is an operation policy, not a raw-error catalogue. Provider
adapters translate PostgreSQL/RDS/driver details privately. Generic platform
code and scope declarations use only the neutral `persistence.*` code. A
record has exactly the schema fields: its summary is the controlled value
`PERSISTENCE_DIAGNOSTIC_OBSERVED:<code>` and its next check is one controlled
route. This prevents scope declarations from embedding an address, connection
string, credential, SQL value, raw provider response, personal data, or a
guessed infrastructure cause. This structural check is not a replacement for
adapter tests proving that raw runtime errors cannot reach emitted diagnostics.

Long-running servers distinguish process liveness from dependency readiness.
A transport outage may make readiness false and trigger bounded reconnect; a
trust-validation failure also makes readiness false but requires target
correction rather than retry. A server that declares `persistence_writes: true`
must map an uncertain write as `request-uncertain-reconcile-before-retry` with
no automatic retry. Completion tasks must not declare HTTP readiness or
reconnect loops. A migration timeout or interruption that leaves its outcome
uncertain blocks release and requires fresh state observation before any
replay. Every workload declares
`persistence.unclassified-failure` with `stop-and-escalate`; novel provider
output is never an implicit retry or repair authority.

The mapping validates declaration intent. It does not prove a driver actually
emits each code, provider access is effective, target routing exists, or a
live failure was rehearsed. Those remain adapter, target-alignment, and live
proof obligations.
