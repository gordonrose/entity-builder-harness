<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.guide.aws-selected-readiness
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: guide
purpose: Define the fixed passive staging observation command and its explicit qualification limits.
portability: {class: internal, targets: [kanbien/staging]}
used_by:
- id: deploy.script.aws-selected-readiness
  path: scripts/04.deploy/release-control/adapters/aws/selected_readiness.py
-->

# Passive selected-target readiness

The existing operational-realization gate exposes a fixed read-only inspection of
`kanbien/staging`. It reuses the existing reconciliation, candidate and relational
inspectors, with bounded AWS CLI calls and closed, normalized output. It does not
execute tasks, start drift detection, fetch secret values or change resources.

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --selected-readiness --inspect-target \
  --blueprint infra/04.deploy/03.product/targets/kanbien/staging/operational-realization/target-release-blueprint.v1.yml \
  --source-root "$PWD" --source-revision <exact-source-revision> \
  --image-digest sha256:<exact-image-digest> --release-id <release-id> --json
```

Use the gate's existing Python wrapper entrypoint where that is the configured
caller. The fixed target profile supplies the AWS account, region and named
credential profile; the command accepts no alternate target, executable, raw
provider fixture or effect callback. Credentials must already be available.
Source revision and intended image are declared inputs, not independently verified
publication or Git HEAD evidence.

The inspector compiles the current selected blueprint before and after inspection.
It checks the existing passive account, stable stack, drift summary, artifact
bucket and budget policies. It resolves all nine exact ECS task revisions from the
named service stack and binds all thirteen container subjects to those revisions,
immutable image digests and hashed role/configuration observations. The current
server revision must match its stack output; candidate shape must mirror the
server under the existing comparison; returned service and cluster identities
must match the requested target, scalar counts must be integers, and the worker
stays dormant without pending tasks. Explicit command
drift and immutable image differences block the overall result. Inherited image
commands remain unknown. Full source-to-live equivalence remains blocked.

Receipts contain source, implementation and target fingerprints, observed time and
expiry. Raw account identifiers, ARNs, endpoints, role/configuration content and
provider error text are not serialized. Each provider response stays in memory and
is capped at 1 MiB; calls have at most 30 seconds, the whole inspection 180 seconds,
and AWS retries are fixed to one attempt. The existing 900-second evidence-age policy
bounds receipt life; successful passive drift evidence can shorten that expiry to
its existing six-hour policy deadline. Stale drift is reported as a distinct
blocked observation; this command cannot refresh it by starting drift detection.

Exit 0 means the specified passive facts were observed without the listed mismatch
conditions. It never means deployable, qualified or authorized. Both exit paths
retain blocked release eligibility, operation authorization, qualification and
source equivalence. A blocked inspection may retain safely observed earlier facts;
a blocked receipt's expiry dates that failed inspection, not stale underlying
proof. Schema, checksum, expiry, implementation, current blueprint and subject joins
are validated again before the CLI prints anything.

The public boundary has no uploaded-success mode. Provider fixtures exist only as
private injected unit-test transports. Local positive/negative tests cover the
source graph, safe output, identity/revision/image/command drift, expiry, schema and
checksum mutations, mixed modes, bounded subprocess output and timeout cleanup.
These tests do not constitute live target evidence.

Next work is explicitly unresolved: compare all source/live configurations, prove
task identity and network authority, run each task's fixed no-effect preflight
after its prerequisites exist, establish independent effects and cleanup, add
approved durable operation control, and satisfy the full seventeen release gates.
Per-task preflight cannot be aggregated before bootstrap creates its dependent
identities. Restore qualification needs an actual isolated restore target.

## Selected shared-store source conformance

The [conditional store adapter](selected-store.README.md) reuses the versioned
selected-operation and existing journal contracts. The normal gate source-check
command tests its fixed injected transport. It exposes no live AWS operation
and does not qualify shared durability or grant execution authority.
