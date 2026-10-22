<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.secret-dependency-contract.v1.guide
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.secret-management
disciplines: [agentic, security, sre]
kind: schema-guide
purpose: Explain how to declare a dependency's secret requirement without storing secret material.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.schema.secret-dependency-contract.v1
  path: .agentic/04.deploy/00-target-alignment/schemas/secret-dependency-contract.v1.schema.yml
-->
# Secret Dependency Contract v1

A secret dependency is an explicit, non-secret statement that a workload needs
credential material to use a dependency. It belongs inside the scope's
`configuration.secret_dependencies` list. An empty list is required when the
scope intentionally has no injected secrets.

Each entry names a stable `target_reference_id`, never a value, ARN, password,
token, or connection string. `expected_fields` describes only field names.
An ARN is a reference rather than a secret value, but provider-specific
references belong in the provider binding—not this portable declaration. The
provider realization later maps the identifier to its provider secret store.

`access_class` describes credential privilege, not workload lifecycle. A
`runtime` entry may be used by a server, worker, or limited one-shot verifier.
A `migration` or `administrative` entry may be used only by a separately
approved run-to-completion task, never by an ordinary server or worker.

Rotation and retirement name separate owners, policies, and conditions. The
supported task-start injection route requires `replacement-required`; a future
task start receives the rotated credential. Rotation never authorises replaying
a completed task. Live refresh is rejected until a real refresh mechanism and
its mechanically checked proof exist. Server/worker failure behaviour names
startup and readiness effects; a completion task names unsuccessful completion
outcomes. Diagnostic codes identify the condition, never the secret or contents.

The validator rejects explicit value-bearing fields and common credential
formats, but it is shape validation—not a general secret scanner. Repository
artifacts, reports, logs, and diagnostics must never contain secret values.
