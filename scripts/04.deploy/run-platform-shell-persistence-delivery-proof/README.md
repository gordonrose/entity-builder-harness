<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.run-platform-shell-persistence-delivery-proof.readme
  version: 1
  status: active
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
