<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.health-failure-and-recovery-declaration
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [security, sre]
kind: standard
purpose: Require every deployable scope to declare distinct health behaviour, safe failure behaviour, bounded recovery, and accountable proof.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.workflow.verify-health-failure-and-recovery
  path: .agentic/04.deploy/60-run/workflows/verify-health-failure-and-recovery.md
- id: deploy.workflow.verify-accept-or-restore-release
  path: .agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md
-->
# Require Health, Failure, and Recovery Declaration

Every deployable scope must declare health and recovery in its canonical scope
declaration before it can be described as release-ready. Use
`health-recovery` to mean the explicit relationship between process health,
dependency safety, task replacement, release restoration, and evidence—not a
single HTTP endpoint or a provider default.

<!-- deterministic-check: allow reason="the reusable validator enforces the declaration shape; this standard explains its safety purpose and scope" -->
The declaration must contain distinct liveness and readiness operations. It
must say which declared dependencies readiness considers, how invalid startup
configuration and unavailable dependencies behave, and which safe diagnostic
code category is emitted. A dependency-free scope explicitly declares an empty
dependency-failure list; it does not omit the concern.

It must also name the orchestrator decision for an unhealthy workload, prohibit
automatic replay of uncertain work, retain an immutable accepted release for
restoration, and require verification after restoration. Automatic task
replacement does not authorise automatic release rollback, data replay, or
repeating an uncertain external operation.

Proof is separately declared for local, package, and live operation. A live
proof may be `deferred` only with a safe reason, accountable owner, concrete
follow-up, and review boundary. A deferred declaration is not evidence that
the behaviour has occurred. A scope with a required dependency must not be
accepted as dependency-ready until its applicable live failure proof is
completed or separately approved as a documented exception.

Declarations and evidence contain safe identifiers, paths, verdicts, and
opaque references only. They must not record secrets, credentials, connection
strings, raw provider responses, personal data, or internal addresses.
