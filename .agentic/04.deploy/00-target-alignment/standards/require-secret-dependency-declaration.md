<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standard.require-secret-dependency-declaration
version: 1
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.secret-management
disciplines: [agentic, security, sre]
kind: standard
purpose: Require safe, explicit secret dependency declarations before a workload may rely on injected secret material.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.declare-secret-dependency
  path: .agentic/04.deploy/00-target-alignment/workflows/declare-secret-dependency.md
- id: deploy.command.validate-secret-dependency-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh
-->
# Require a Secret Dependency Declaration

Use this standard whenever a scope introduces, changes, rotates, or retires a
secret that a workload receives to reach a dependency. It applies before target
alignment and before a provider secret, role, or workload binding is changed.

The scope contract must explicitly declare `configuration.secret_dependencies`.
Use an empty list only when no workload in the scope receives a secret. A secret
dependency declaration names purpose, owner, authorised workload, access class,
safe reference identifier, expected field names, delivery, rotation, retirement, failure
behaviour, and safe diagnostics. It never contains a secret value or a
provider-specific secret address.

<!-- deterministic-check: allow reason="The secret-dependency validator enforces declaration shape and workload-type boundaries; this standard explains the portable security policy." -->
Runtime, migration, and administrative access classes are separate from
workload lifecycle. A runtime credential can serve a server, worker, or a
limited one-shot verifier. A migration or administrative secret is available
only to its declared run-to-completion task; it cannot be assigned to an
ordinary server or worker. Reusing a credential across privilege classes
requires a new design decision; it must not be hidden by changing a workload
type.

The secret store holds secret values. Repository artifacts hold references,
resource configuration, policies, and non-secret evidence only. The provider
binding owns concrete provider references and role policies; the portable scope
declaration links through `target_reference_id`. Target alignment may verify a
reference exists and is usable without reading or reporting its contents.

Rotation and retirement are part of the contract. The supported task-start
injection route requires a replacement/new start to receive a new value.
Live-refresh claims are rejected until a supported mechanism and deterministic
proof exist. Rotation does not authorise replay of a completed task. Safe errors
distinguish unavailable secret material, invalid shape, rejected credential,
and denied dependency permission without exposing values. The validator blocks
explicit value-bearing fields and common credential formats, but it does not
replace repository secret scanning.
