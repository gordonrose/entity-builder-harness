<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standard.require-secret-dependency-declaration
version: 5
status: active
created_on: "2026-10-22"
updated_on: "2026-10-25"
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
safe reference identifier, expected field names, delivery, access-grant,
rotation, revocation, retirement, failure behaviour, and safe diagnostics. It
never contains a secret value or a provider-specific secret address.

<!-- deterministic-check: allow reason="The secret-dependency validator enforces declaration shape and workload-type boundaries; this standard explains the portable security policy." -->
Runtime, migration, and administrative access classes are separate from
workload lifecycle. A runtime credential can serve a server, worker, or a
limited one-shot verifier. A migration or administrative secret is available
only to its declared run-to-completion task; it cannot be assigned to an
ordinary server or worker. Reusing a credential across privilege classes
requires a new design decision; it must not be hidden by changing a workload
type.

Every entry also identifies the declared dependency it serves. A verifier that
declares `server_mediated_dependency_proof` cannot receive a secret for that
dependency: its purpose is to prove the server path, not bypass it. This rule
does not forbid an unrelated, separately justified dependency credential; its
scope is the dependency named by the proof.

A task that declares `migration_execution` for a dependency must receive a
matching `migration` access-class secret for that dependency. This is the
currently governed structural-change delivery method; missing access is a
declaration failure, not a reason to reuse the runtime credential.

The secret store holds secret values. Repository artifacts hold references,
resource configuration, policies, and non-secret evidence only. The provider
binding owns concrete provider references and role policies; the portable scope
declaration links through `target_reference_id`. Target alignment may verify a
reference exists and is usable without reading or reporting its contents.

Some providers support short-lived workload-identity tokens instead of an
injected database password. Those are declared separately in
`configuration.workload_identity_dependencies`, with the same owner,
authorised-workload, access-class, delivery, authentication lifecycle, revocation, retirement,
failure, and diagnostic boundaries. The declaration contains only an opaque
authentication reference ID, never a token. Provider binding and live proof
must still establish the matching task identity and effective access. A
migration executor may use a matching `migration` workload identity instead
of a migration secret, but it may not silently omit authentication.

Access grants, rotation, revocation, and retirement are separate parts of the
contract. `access_grant` names accountable ownership and a declared
access-class boundary; its policy text and fixed boundary value are not proof
of an executable provider policy or effective least privilege. The provider
binding and live verification later supply the actual role/grant mapping and
prove both permitted and prohibited operations. The supported task-start
injection route requires a replacement/new start to receive a new value.
Live-refresh claims are rejected until a supported mechanism and deterministic
proof exist. Rotation does not authorise replay of a completed task. The future
PostgreSQL route must govern credential/secret/task coordination, permitted
interruption, partial-failure recovery, and fresh-connection meaningful
operation from the replacement task.

Workload identity has a different lifecycle from a startup-injected password.
Its declaration must state provider-managed task-role renewal, per-new-
connection token generation, existing-session behaviour, and the fact that
ordinary token expiry does not itself require workload replacement. Urgent
revocation is separate: it changes permission, handles established sessions,
and needs fresh provider and effective-access evidence. A successful IAM login
does not, by itself, prove renewal, revocation, replacement, or remediation.

`revocation` must block new starts, stop any active authorised workload, and
require later observation that both new access and established sessions are
denied. Blocking secret retrieval or changing a password alone does not prove
that existing sessions ended. A stopped migration follows its existing
interruption and unknown-outcome controls: block release acceptance, require
fresh state observation, and never blindly replay. Planned retirement follows
its declared retirement condition; urgent revocation uses immediate containment.
Safe errors distinguish unavailable secret material, invalid shape, rejected
credential, and denied dependency permission without exposing values. The
validator blocks explicit value-bearing fields and common credential formats,
but it does not replace repository secret scanning.
