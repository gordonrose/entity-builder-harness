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

`npm run platform:shell:persistence-delivery-proof -- --execute
--approve-outbox-delivery-proof` has no selectable target, credentials, task,
network, queue, message, work-item, or timeout. It is allowed once only when
the target profile records the exact post-acceptance aggregate state: three
table records, one due outbox obligation, empty queues, no relay task, dormant
worker, healthy server, and five healthy alarms.

The command verifies account and stack state, starts exactly one existing
relay Fargate task, waits for that task to stop successfully, confirms its one
delivery reached the existing source queue, scales the existing worker to one,
waits for the processing record and queue settlement, leaves it alive through
the existing 75-second exporter interval, and always returns the worker to
zero. It emits only a safe status, rounded duration, relay exit code, and the
aggregate terminal table count. It never prints or records secrets, headers,
request bodies, DynamoDB items, queue URLs/messages, task IDs, or raw AWS
responses.

This is a bounded first delivery proof, not a scheduler, a continuous relay,
an arbitrary worker queue test, or permission to replay the existing outbox
entry.
