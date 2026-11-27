<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform.disabled-scheduling
version: 3
status: active
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.scheduling
disciplines: [security, sre]
kind: workflow
purpose: Sequence initial disabled scheduling resources, reserved read-only connection proof and bounded synthetic execution without weakening final acceptance.
portability: {class: internal, targets: []}
used_by:
- id: deploy.capability.scheduling-control
  path: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
-->
# Deploy disabled scheduling and prove its runtime

Use this workflow only under the [approved provider rule](../../../../../standards/operational-realization-applicability.md#disabled-scheduling-resources-and-bounded-runtime-proof).
The shared [controller](../../../../../../../scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py)
owns AWS effects. Its immutable records preserve the original operation after
timeouts; a command, plan hash or local JSON verdict cannot grant authority.

## Prepare source and current safety facts

Require the declared source, package and semantic checks at their exact input
identities. Authenticate both managed images through the protected publication
owner and retain their current source/configuration binding. Bind the existing
scope's additive migration, effective dispatch/worker permissions and empty
unrelated work inventory through the actual task receipt readers before creating
that scope's disabled functions. Shared network creation uses network
compatibility; it does not depend on application database
readiness. Each scope retains its own database readiness gate.

Pass the selected scope's `--dispatch-receipt` and `--worker-receipt` to
initial prepare/execute commands. For scope creation, the existing
`--database-selections` input also supplies its maintenance package selection.
That selection is retained in the existing immutable phase intent and inherited
by its control changes. Qualified package/source/database identity is required;
another scope's deployment or a cost record is not.

Inventory the whole current VPC, not only the selected subnets. Map compute
interfaces to actual workloads and current identities, including attached policy
versions. Preserve the existing worker/relay groups, four legacy roles and two
queues. Unknown consumers, indirect credentials, incompatible queue policies,
external network dependencies or an unowned existing endpoint block creation.
Do not send, receive or delete existing queue messages to test compatibility.

After proof work changes the pending-work inventory, refresh only the existing
read-only `observe-scheduling-state` task. Its continuation identity must select
a finite, source-owned disabled control phase whose original operation has
completed. Before reserving the task, authenticate that original phase, the
current disabled controls, qualified maintenance source/image and unchanged
database identity. Retain the phase evidence with the task's existing plan and
prerequisites. An unknown original task must reconcile under its original
identity; another phase or label cannot bypass it. This continuation does not
rerun grants, permission probes or migrations, and does not substitute for
application acceptance. Reuse a still-fresh observation while its database
identity and relevant work inventory remain unchanged; a control-only toggle
does not itself require another database task.

Retain the initial observation fingerprints and a finite execution window.
The user explicitly moved detailed cost checks after the first bounded live
proof. Do not require `prepare-cost` before that proof or describe the US$10
target as an enforced pre-run cap. Keep invocation, concurrency, retry and
duration limits. After proof, use the existing cost collector and actual original
operation records; include all work and report any target miss. The measured
US$25 monthly gate still applies before leaving either scheduler enabled.

## Create disabled resources

1. Resolve any retained execution before refreshing mutable live inputs. An
   unresolved reservation cannot be bypassed by a new label, revision or token.
2. Retain the exact source, parameters, templates and resource prerequisites in
   the private intent. Review the shared endpoint addition and each independent
   scope change set. Reject replacement, deletion and unrelated resources.
3. Execute each original reviewed operation once. Require its original-token
   terminal event, exact deployed template/parameters and actual resource
   readback. Scope creation requires `TickEnabled=false`, `WorkerEnabled=false`
   and `DenyDispatcherSend=false`.
4. Compare current legacy access with the retained original observations. A
   resource creation success is not proof that legacy applications executed.

## Prove the unchanged runtime connections

Reserve the closed `{kind:'scheduling-preflight/v1'}` synchronous request to each
numeric function version. Put only the reserved UUID in ClientContext; never
allow caller-selected code, queue destinations or business arguments. The
dispatcher performs read-only database checks. The worker additionally resolves
regional queue DNS and calls GetQueueAttributes on its own queue without new
permissions.

Match the actual version, image, source, configuration, database identity,
endpoint-address digest, operation ID and request ID. Retain the selected success
log and AWS request/billing report. A lost response permits only bounded reads
of the original logs. Missing or ambiguous evidence leaves the attempt unknown;
do not invoke again or use a different label.

## Execute bounded synthetic cases

Admit only declared new synthetic rows/reminders and the finite proof envelope.
Keep each scope independent. Enable its worker and minute trigger in one reviewed
control-only change. Require actual worker-enabled and trigger-enabled readback
before accepting automatic delivery proof; this does not promise which provider
resource became enabled first. Retain the update and terminal readback. Disable both when
the bounded run ends or cannot progress safely. Source permission to perform the
proof is not evidence that it ran.

For the controlled delivery failure, first disable both controls. Review the
QueuePolicy-only `DenyDispatcherSend=true` change and reserve one dispatch of the
identified synthetic outbox entry. Observe durable waiting/retry state. Restore
the exact false state through the retained recovery operation before ordinary
delivery resumes. Never replace a queue, edit shared database rules or deny a
legacy principal to obtain the failure.

## Accept or stop

Use the existing observability receipt owner for the scheduler's own dispatch
error alarm. Its scheduler selection reads the genuine failed dispatch, the
matching alarm episode, confirmed subscription and later recovery; it must not
run the PostgreSQL-readiness failure/revoke route. The existing
`record-notification` operation may retain delivery confirmation only when the
human recipient confirms receiving that exact scheduler alarm. A successful
SNS publish or subscription confirmation is not an observed email delivery.
Retain this source-bound proof with the existing scheduler acceptance material,
not in a new alert journal. Missing human confirmation remains incomplete proof.

Leaving the scheduler enabled requires the existing canonical acceptance owner
to validate all actual runtime cases, independent baseline/Entity scope identity,
failure recovery, alarms and a measured combined monthly projection within
US$25 at 100,000 jobs. Include 31 days, both endpoint zones, all eight alarms and
measured initialization/retries plus priced database/network/storage extras.
Timeout and concurrency settings alone are not a cost forecast.

Keep unknown original operations, partial resources and evidence intact. Any
repair outside the declared control/fault restoration paths needs its owning
governed decision; never rewrite history, invent success or silently broaden
this workflow. The current controller's blocked result must be respected until
its source-bound gates are connected and verified.
