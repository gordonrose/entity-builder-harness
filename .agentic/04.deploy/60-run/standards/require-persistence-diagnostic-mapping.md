<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.persistence-diagnostic-mapping
version: 3
status: active
created_on: "2026-10-23"
updated_on: "2026-10-25"
layer: 04.deploy
domain: deployment.persistence-diagnostics
disciplines: [security, sre, agentic]
kind: standard
purpose: Require scope-specific, workload-aware mappings from persistence diagnostic classes to safe consequences.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.declare-persistence-diagnostic-mapping
  path: .agentic/04.deploy/60-run/workflows/declare-persistence-diagnostic-mapping.md
- id: shared.standards.safe-diagnostic-record
  path: .agentic/shared/standards/require-safe-diagnostic-record.md
-->
# Require Persistence Diagnostic Mapping

A new-framework scope must explicitly classify `dependencies.persistence` and
declare whether persistence diagnostics are inapplicable or map the controlled
persistence taxonomy to every workload that can use a classified persistence
dependency. Absence is not an inapplicability claim. A persistence dependency
cannot be hidden behind a logical identifier: migration, server-mediated, and
declared write usage must agree with the classification.

Mappings are provider-neutral. `platform/persistence` owns neutral meanings;
provider adapters translate selected provider facts; scope contracts own
workload consequence and proof. A long-running server keeps process liveness
separate from dependency readiness. A completion task fails completion or
blocks acceptance as appropriate; it never gains HTTP readiness or an
unbounded reconnect loop. An uncertain migration outcome blocks release and
requires a declared, read-only fresh-state observation with a durable receipt
before replay. Its replay-permitted result must be explicit; arbitrary task
completion or a parsed provider log is not permission to submit again.

Every mapped workload handles `persistence.unclassified-failure` by stopping
and escalating. Diagnostic records use a closed field set, controlled summary
value, and controlled next-check route; provider detail has no place in the
record. Local declaration validation does not prove actual adapter mapping
prevents raw errors, provider permission, target routing, or live failure
behaviour; each is required separately before scope acceptance.
