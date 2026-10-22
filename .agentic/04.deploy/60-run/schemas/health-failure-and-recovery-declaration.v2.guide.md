<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.health-failure-and-recovery-declaration.v2.guide
version: 2
status: active
created_on: "2026-10-22"
updated_on: "2026-10-22"
layer: 04.deploy
domain: deployment.runtime-safety
disciplines: [agentic, security, sre]
kind: guide
purpose: Explain how to author workload-type-aware health, failure, recovery, completion, and proof declarations.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.schema.health-failure-and-recovery-declaration.v2
  path: .agentic/04.deploy/60-run/schemas/health-failure-and-recovery-declaration.v2.schema.yml
-->
# Health, Failure, and Recovery Declaration v2 Guide

Put one `workloads[]` entry in a scope's canonical declaration contract for
every runtime workload that the scope creates or relies on. The entry is about
the workload, not merely its image: one image may legitimately supply a
server, a worker, and a one-shot verifier with different safety requirements.

Use `long-running-server` when the workload remains available to serve
requests. It declares distinct liveness and readiness operations, safe startup
and dependency failure behaviour, orchestrator replacement, release
restoration, and proof of recovery.

Use `continuous-worker` when work is continuously consumed rather than served
over HTTP. It declares progress health, dependency availability, safe shutdown,
and how interrupted work is handled. HTTP endpoints are optional and must not
be invented simply to satisfy a server-shaped contract.

Use `run-to-completion-task` when the workload has a bounded job. It declares
its deadline, exact safe success result, interruption policy, and retry policy.
Completion proof must identify an evidence reference, a successful exit, a
safe result code, and timestamps showing it was observed no earlier than the
release or recovery boundary it is intended to prove. The target-specific
provider mapping must compare those declared facts with the referenced evidence
and its real start/stop duration; two self-declared timestamps are not enough.
Task submission alone is not completion evidence.

`not_applicable` is optional but, when used, must state the concern, why the
declared workload type makes it inapplicable, and why that is appropriate for
the declared scope. It cannot hide a requirement that belongs to the selected
type. For example, a completion task can justify no HTTP readiness; a server
cannot use this to omit readiness.

Legacy infrastructure is not silently grandfathered. A target scope index may
list only retiring reference workloads and must state the owner, reason,
replacement path, review condition, and retirement condition. New framework
scopes cannot take that route. Every active index entry points only to that
scope's canonical declaration and binding files, and those files must identify
the same target and scope.

The corresponding workload binding must trace each workload to the code it
actually runs. Use `compiled-entrypoint` for a packaged program and
`inline-command` for code defined in a provider task definition. Record a safe
source reference and command description. Do not assume that workloads share a
program just because they share a container image.

Keep declarations and evidence safe: use identifiers, paths, timestamps,
verdicts, and opaque references only. Never record secrets, credentials,
connection strings, raw provider responses, personal data, or internal
addresses.
