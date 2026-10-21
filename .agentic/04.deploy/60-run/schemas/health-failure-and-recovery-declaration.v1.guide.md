<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.health-failure-and-recovery-declaration.v1.guide
version: 1
status: active
created_on: "2026-10-21"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [agentic, security, sre]
kind: guide
purpose: Explain how to author the embedded health, safe-failure, recovery, and proof declaration for a scope.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.schema.health-failure-and-recovery-declaration.v1
  path: .agentic/04.deploy/60-run/schemas/health-failure-and-recovery-declaration.v1.schema.yml
-->
# Health, Failure, and Recovery Declaration v1 Guide

Place the `health_recovery` block in the scope's canonical declaration contract.
The target declaration states the facts; this guide and the standard state how
to express them.

Liveness asks only whether the process is alive enough to answer. Readiness
asks whether it is safe to serve the scope's declared operation. They should
normally be different operations. `depends_on` lists only dependencies that
readiness actually considers. It is `[]` for a genuinely dependency-free
scope.

`startup_failure` describes invalid required startup configuration. Each entry
in `dependency_failures` describes an unavailable selected dependency. Use a
short safe diagnostic category, not a password, hostname, provider response,
or exception message.

An orchestrator may replace an unhealthy task, but must not replay an uncertain
request or transaction. Release recovery is a separate operation: restore the
retained immutable accepted release and then repeat the declared health and
meaningful-operation verification.

Local and package proof name the commands that have run or will run. Live
recovery proof records either a safe evidence reference after it has passed, or
an accountable deferment. A deferment must not be used to accept a new
dependency-bearing scope without an explicit reviewed exception.
