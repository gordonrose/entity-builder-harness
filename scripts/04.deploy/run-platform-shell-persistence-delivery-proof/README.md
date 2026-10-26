<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: deploy.script.run-platform-shell-persistence-delivery-proof.readme
  version: 1
  status: active
  created_on: "2026-09-25"
  updated_on: "2026-10-26"
  layer: 04.deploy
  domain: persistence
  disciplines:
  - security
  - sre
  kind: documentation
  purpose: Describe the bounded Kanbien staging transaction-to-outbox-to-worker delivery proof command.
  portability:
    class: internal
    targets:
    - kanbien/staging
  used_by:
  - id: deploy.script.run-platform-shell-persistence-delivery-proof
    path: scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.sh
-->
# Persistence delivery proof

`npm run platform:shell:persistence-delivery-proof -- --validate` validates
the committed `kanbien/staging` policy without contacting AWS.

The live proof is intentionally split into short, strictly ordered commands so
an interactive-client timeout cannot hide an in-progress cloud operation. It
has no selectable target, credentials, task, network, queue, message,
work-item, or timeout. Its only mutable commands require
`--approve-outbox-delivery-recovery`.

After the currently approved remediation image is deployed and health-checked, run these fixed
stages in order:

1. `--start-relay --approve-outbox-delivery-recovery` starts exactly one
   labelled Fargate relay and returns immediately.
2. `--assess-relay` requires that exact labelled relay to have exited `0` and
   produced exactly one source-queue delivery.
3. `--start-worker --approve-outbox-delivery-recovery` starts exactly one
   labelled worker task with its fixed self-termination-after-one-successful-
   delivery mode; it never changes the worker service desired count.
4. `--assess-worker` requires that task to have exited `0`, one durable
   completion record, and empty queues. It is run after the established
   75-second exporter settlement interval.
5. `--verify-terminal` requires the server to remain healthy, worker `0/0`,
   queues empty, no due outbox entry, and four aggregate persistence records.

Every stage revalidates the fixed account, stack, target profile, aggregate
preconditions, and safe output policy. It emits only a safe stage status,
relay exit code where applicable, and aggregate record count. It never prints
or records secrets, headers, request bodies, DynamoDB items, queue URLs or
messages, task IDs, or raw AWS responses.

This is a bounded recovery delivery proof, not a scheduler, a continuous
relay, an arbitrary worker queue test, or permission to replay the existing
outbox entry more than once. A failed label is permanently spent. A later
attempt requires a documented source change, an immutable-image rollout,
post-rollout health evidence, and a fresh fixed label in the target policy.

Before `run-task`, the command now writes one immutable submission artifact for
the fixed label beneath the repository common directory's
`platform-shell-delivery-proof/` directory. It binds the immutable task revision,
its full configuration, network and overrides through hashes, together with the
reviewed configuration/permission source inputs. The request uses the derived
idempotency token. A reservation is permanently spent even if the response is
lost; neither missing ECS history nor a restart authorizes another submission.
These are the two fixed stage outputs, not a general execution history.

`--assess-relay` and `--assess-worker` capture a safe immutable terminal receipt
while ECS still exposes the stopped task. Later stages may reuse that receipt
after ECS task history expires, while still checking fresh aggregate and cleanup
state. If a terminal result expired before capture, the result is unobservable
and replay remains blocked. The command cannot retrospectively manufacture
receipts for the already accepted historical proof.

Use `--reconcile` after an interruption. It makes provider reads only and may
retain an observed terminal receipt locally. It reports `pending` while normal
ECS provisioning/stopping states remain, `uncertain` when required outcomes are
unobservable, and `cleaned-up` only after retained terminal proof and fresh
aggregate checks agree. Worker and relay task families must have no active
tasks, the worker service must have no desired/running/pending tasks, and source
and dead-letter queues must have no visible or in-flight messages. Partial or
paginated observations never establish complete cleanup.
