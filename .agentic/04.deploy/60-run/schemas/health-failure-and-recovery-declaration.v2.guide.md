<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.schema.health-failure-and-recovery-declaration.v2.guide
version: 8
status: active
created_on: "2026-10-22"
updated_on: "2026-10-25"
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

Every long-running server also declares `health_signal_mapping`. This is the
explicit bridge between the provider's replacement decision and the server's
operations: `provider_replacement_signal` is `liveness` or `readiness`,
`dependency_readiness_effect` is always `block-candidate-acceptance`, and
`candidate_acceptance_signals` is exactly `[liveness, readiness]`.

A server with required dependencies must use `liveness` for provider
replacement. A temporary dependency outage then prevents readiness and
candidate acceptance without repeatedly replacing an otherwise healthy process.
`readiness` is allowed as a provider replacement signal only for a
dependency-free transitional scope, and only with a concrete
`dependency_free_replacement_basis`. The corresponding workload binding must
repeat the same mapping so a provider-specific control can compare the chosen
runtime configuration with the portable declaration. This records the current
bootstrap mapping accurately; it does not make that mapping reusable for a
persistence-bearing successor.

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

A completion task that proves a dependency through a long-running server uses
`server_mediated_dependency_proof`. It names the dependency and target server,
allows only a private application route, prohibits direct dependency
credentials and network access, and sets its direct dependency connection limit
to zero. Its proof sequence is fixed: create and commit a synthetic record
through the server, replace that server, then read the original record through
the replacement. Its `acceptance_record` contract makes repetition safe: an
equivalent repeat returns the original record without a duplicate, concurrent
creation preserves exactly one original fact set, conflicting identifier reuse
is rejected without overwrite, and a lost response after commit is reconciled
by reading that original record before any retry. Its cleanup record names the
owner, retention through the replacement and restore proofs, the
server-mediated cleanup route, safe deletion outcome, and abandoned-verifier
handling. This is not an administrative dependency test: the verifier must
exercise the same server-mediated path that the application uses.

A one-shot task that changes dependency structure uses `migration_execution`.
It identifies the required dependency and `migration` credential class, uses a
strictly ordered immutable/checksummed manifest, permits exactly one executor,
and bounds both lock acquisition and execution. It states the transaction
boundary, never retries an uncertain outcome automatically, blocks release
until `fresh_state_observation` resolves that outcome, and uses
`expand-deploy-verify-contract-later` compatibility. Its `replay_handling`
requires a checksum-matching rerun to become a no-op with recorded accepted
state, a checksum mismatch to block the release pending fresh observation, and
a concurrent executor to be rejected before applying changes. A checksum
detects a changed manifest; it never proves whether an interrupted migration
committed. The fresh observer is a distinct run-to-completion administrative
workload for the same dependency. It is read-only, emits a durable task receipt,
and permits a new migration submission only for its declared
`PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED` result. A complete,
checksum-matching history instead produces
`PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED`: it is durable evidence that
the earlier migration took effect, but is not permission to replay it. A
partial, inconsistent, or unavailable history is a release block—not evidence
that an agent may replay the migration.

Any scope with `migration_execution` also declares `persistence_recovery`.
It contains three separate required-before-acceptance proofs: a named
server-mediated verifier proves the original record survives server
replacement; an image rollback is only to a prior persistence-capable accepted
release and never reverses database structure; and a recovery point is restored
to a new isolated database, read through an isolated application, without
mutating the source. One proof cannot stand in for the other two.

`not_applicable` is optional but, when used, must state the concern, why the
declared workload type makes it inapplicable, and why that is appropriate for
the declared scope. It cannot hide a requirement that belongs to the selected
type. For example, a completion task can justify no HTTP readiness; a server
cannot use this to omit readiness.

Legacy infrastructure is not silently grandfathered. A target scope lifecycle
index may list only retiring reference workloads and must state the owner,
reason, replacement path, review condition, and retirement condition. New
framework scopes cannot take that route. Every lifecycle entry points only to
that scope's canonical declaration and binding files, those files must identify
the same target and scope, and exactly one active scope owns each bound
workload identity.

The corresponding workload binding must trace each workload to the code it
actually runs. Use `compiled-entrypoint` for a packaged program and
`inline-command` for code defined in a provider task definition. Record a safe
source reference and command description. Do not assume that workloads share a
program just because they share a container image.

Keep declarations and evidence safe: use identifiers, paths, timestamps,
verdicts, and opaque references only. Never record secrets, credentials,
connection strings, raw provider responses, personal data, or internal
addresses.
