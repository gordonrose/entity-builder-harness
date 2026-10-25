<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.health-failure-and-recovery-declaration
version: 9
status: active
created_on: "2026-10-21"
updated_on: "2026-10-25"
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

Every deployable scope must inventory each individual workload and declare type-aware health and recovery in its canonical scope
declaration before it can be described as release-ready. Use
`health-recovery` to mean the explicit relationship between process health,
dependency safety, task replacement, release restoration, and evidence—not a
single HTTP endpoint or a provider default.

<!-- deterministic-check: allow reason="the reusable validator enforces the declaration shape; this standard explains its safety purpose and scope" -->
Classify each workload as `long-running-server`, `continuous-worker`, or
`run-to-completion-task`. Servers declare distinct liveness and readiness.
Workers declare progress health, safe shutdown, and interrupted-work handling.
One-shot tasks declare a deadline, successful exit/result criteria,
interruption handling, and retry policy; they do not need HTTP endpoints.

Each workload binding must also state the safe source reference and command
description for the code it actually executes. Sharing an image does not mean
two workloads execute the same program: an ECS service may use a compiled
entrypoint while a one-shot verifier uses an inline task-definition command.

<!-- deterministic-check: allow reason="validate-health-failure-and-recovery-declaration enforces applicable operations and nested requirements; this standard explains the portable safety intent." -->
The declaration must contain the operations applicable to its workload type. It
must say which declared dependencies readiness considers, how invalid startup
configuration and unavailable dependencies behave, and which safe diagnostic
code category is emitted. A dependency-free scope explicitly declares an empty
dependency-failure list; it does not omit the concern.

Every new-framework scope also declares whether persistence diagnostics are
inapplicable or, for a required persistence dependency, supplies the complete
workload-aware mapping required by
`require-persistence-diagnostic-mapping.md`. That mapping controls safe
diagnostic code, consequence, retry boundary, and next check; it does not
replace health/recovery or provider-specific proof.

A long-running server must also declare its health-signal mapping: the signal
the provider uses for replacement, the readiness consequence for candidate
acceptance, and the two signals required to accept a candidate. A
dependency-bearing server may be replaced for process liveness, not merely
because a dependency is temporarily unavailable. The workload binding repeats
this mapping so the selected provider realization can be checked against it.
A dependency-free transitional workload using readiness for replacement must
say so explicitly and explain why; that exception never carries into a
dependency-bearing successor.

A run-to-completion verifier that proves a dependency through a server must
declare `server_mediated_dependency_proof`. It gets private application-route
access, not a dependency credential, database role, direct dependency network
path, or connection allocation. Its record creation, replacement read, and
governed cleanup are part of the declared completion proof—not an unbounded
test procedure hidden in a provider script. The declaration also fixes safe
repeat behaviour: equivalent and post-commit-lost-response attempts reconcile
the original record, concurrent creation preserves one fact set, conflicting
reuse is rejected without overwrite, and cleanup stays server-mediated until
the replacement and restore proof boundary is accepted.

A run-to-completion task that changes dependency structure must declare
`migration_execution`: one executor, bounded lock and execution waits, an
ordered immutable/checksummed manifest, transaction boundary, an interruption
policy that never retries an uncertain outcome automatically, and a release
block pending fresh state observation. That observation is a separately bound,
read-only administrative task for the same dependency. It must produce a
durable receipt before replay and permit replay only when the reviewed
migration-history state says it is safe. It must also state that a
checksum-matching rerun is a recorded no-op, a checksum mismatch blocks the
release, and a concurrent executor is rejected before apply. Its compatibility
strategy is expand → deploy → verify → contract later. The supported secret
contract also requires a matching `migration` credential for that task and
dependency.

Any scope that declares migration execution also declares three separate
`persistence_recovery` requirements before it can be accepted: server
replacement retaining the original record through a named server-mediated
verifier, restoration only to a prior persistence-capable accepted image that
is compatible with the resulting schema, and recovery-point restoration to a
new isolated database verified by an isolated application. Database reversal is
not an image rollback, and a restore rehearsal must not mutate its source.

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

Retiring legacy infrastructure may be recorded only in the target's scope
lifecycle inventory, with its workload identity, reason, accountable owner,
replacement path, review condition, and retirement condition. It is not an
exception route for an indexed new-framework scope or a newly created
workload. The lifecycle inventory also requires exactly one active scope to
own each workload identity and is validated before target alignment and
release controls can pass.

Declarations and evidence contain safe identifiers, paths, verdicts, and
opaque references only. They must not record secrets, credentials, connection
strings, raw provider responses, personal data, or internal addresses.
