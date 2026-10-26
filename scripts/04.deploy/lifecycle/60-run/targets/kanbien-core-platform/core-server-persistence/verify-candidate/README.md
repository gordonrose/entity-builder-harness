<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: deploy.reference.kanbien-core-platform.private-verifier-continuation
  version: 1
  status: active
  created_on: "2026-10-26"
  updated_on: "2026-10-26"
  layer: 04.deploy
  domain: deployment.core-server-persistence
  disciplines: [security, sre]
  kind: reference
  purpose: Define bounded private verifier operation continuation and explicit fresh-proof succession.
  portability: {class: internal, targets: []}
  used_by:
  - id: deploy.command.kanbien-core-platform.verify-core-server-persistence-candidate
    path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh
-->
# Private verifier continuation

The first ordinary `--mode <mode> --json` invocation reserves a logical operation before calling ECS. The reservation binds the mode, exact task definition, network, overrides and completion deadline. It is private worktree metadata under the Git directory, following the existing candidate controller reservation pattern. Completed task evidence still belongs to `../proof-receipts.py`; this command does not introduce an execution journal.

Repeating the same ordinary invocation observes the reserved operation. It never repeats `run-task`, including after a timeout, lost response, interruption, pending task or missing provider metadata. The first execution polls up to its declared deadline; later invocations perform one observation. Concurrent invocations use an exclusive mode lock. Both the reservation and initialization marker are durably written before submission.

A successful result includes the full `facts.verifier_task` ARN, `facts.operation_id` and `facts.proof_receipt`. Fresh terminal observation is marked `facts.evidence_reuse: fresh-terminal-observation`. A retained completion is marked `historical-completion` and retains the original completion time; it does not prove current health. Terminal unsuccessful or deadline-exceeded task outcomes are also retained and remain failures.

For a deliberately new verification after a proven terminal operation, invoke the same mode with:

```text
--new-operation --expected-operation <previous facts.operation_id>
```

The expected predecessor is checked under the lock. Repeating this exact successor request resumes its already reserved successor. It cannot create successive tasks. Use the prior operation from the same mode, including a prior failed terminal operation. A mismatched predecessor, pending predecessor, absent terminal receipt or changed request while pending blocks submission.

A caller that knows this mode has never run may explicitly assert `--new-operation --expected-operation none`. This creates the initial reservation or reconciles that identical initial request. It never replaces an existing reservation, including a pending, uncertain or terminal reservation; it rejects an initial assertion after a successor exists. Missing metadata is not interpreted as `none` when the retained initialization marker or reservation demonstrates prior use.

When the selected definition or configuration changed before an older task was captured, use `--reconcile-operation <operation-id>` (or its exact `--reconcile-task <task-arn>`). A matching reservation is observed against its original request and deadline, without submitting anything. Once the old terminal proof is retained, an explicit successor must pass today's configuration prerequisites. Unmatched legacy reconciliation retains the existing current-definition constraints.

Missing or malformed reservation metadata, unavailable safe logs, expired task metadata and uncertain provider outcomes never authorize replay. A reservation interrupted before the provider call can remain unobservable; it intentionally cannot be retried by submission. A definite provider rejection without a terminal task also leaves a spent reservation. These cases require separately governed recovery; deleting metadata to retry is not a supported recovery path.

The guarantee covers retained metadata in this chat's worktree. Complete erasure of all worktree metadata or execution from a different worktree cannot be distinguished from first use by this local owner; it is not a global provider lock. Preserve the worktree and its Git metadata when resuming.

The existing smoke entrypoint runs `operation-test.py`, which exercises the actual shell/Python interfaces in disposable Git roots with synthetic provider processes. It covers initial and successor operations, identical retry, missing metadata, changed requests, concurrent invocation, interruption before and after possible submission, terminal failures, durable evidence reuse, and the runtime credential caller's explicit fresh health checks. These fixtures provide no live AWS proof.
