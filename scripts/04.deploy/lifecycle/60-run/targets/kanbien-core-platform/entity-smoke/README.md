<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.readme.entity-smoke.execution
version: 2
status: draft
created_on: "2026-11-08"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.entity-smoke
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain the actual infrastructure and initial task commands, safe evidence and unfinished proof/acceptance connections without claiming live qualification.
portability: {class: internal, targets: [kanbien-core-platform]}
used_by:
- id: deploy.plan.entity-smoke-core-platform
  path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
-->
# Entity-smoke infrastructure and proof controls

The feature needs its own private AWS resources before it can run. Creating
those resources must not also start an application whose database permissions
and tables have not been prepared. The infrastructure commands therefore first
create an isolated service with **zero** running application tasks. A separate
activation changes its desired count to one only after required task receipts
have been checked.

This folder also contains public preparation/feature tasks, bounded server
replacement, initial failure stopping, restart/preservation and credential-recovery observations, plus internal snapshot/restore
controls. The acceptance template and guarded local promotion are connected,
but the complete live recovery/acceptance proof has **not yet run**;
the [implementation plan](../../../../../../../.agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md)
tracks that work. None of the local fixtures is live AWS proof.

## What each file does

| Files | Responsibility |
| --- | --- |
| [plan.sh](plan.sh) | Runs only planning; rejects an attempt to override it into another mode. AWS reads, local checks/cache writes and credential-cache refresh are possible; AWS writes are not admitted. |
| [script.sh](script.sh), [script.py](script.py) | Public command wrapper and actual argument checking, source/custody checks, provider boundary, gate evidence, plan matching and execution orchestration. |
| [task-plan.sh](task-plan.sh), [task-execute.sh](task-execute.sh), [task-route.py](task-route.py) | Separate read-only planning and explicit single-task execution commands; check actual bindings, exact approval and original admission/attempt. Initial preparation, baseline, initial-recovery and credential-recovery observations are connected; restored-reader orchestration remains unfinished. |
| [task-binding.py](task-binding.py), [task-graph.py](task-graph.py) | Compare deployed task/role/private-network settings with the own source template, then derive the selected workload's complete reachable realization graph for the existing compiler. These checks are not actual database access. |
| [task-steps.py](task-steps.py) | Build closed task requests, reobserve immutable preparation receipts in order and assemble the existing four-pair activation manifest. |
| [task-completion.py](task-completion.py) | Link each collected step to its actual final gate through an immutable completion sidecar. An interrupted result without that gate cannot admit the next step. |
| [feature-steps.py](feature-steps.py) | Require actual activation and original-record proof before lifecycle, collision and baseline read; admit a read-only observer only after the original reserved create task is terminal with its qualified image. |
| [replacement.sh](replacement.sh), [replacement-route.py](replacement-route.py) | Plan or explicitly execute one original-record-bound server replacement. The original task is selected by the controller and retained across interruption; the successor cannot become a second stop target. A separate staged verifier read must establish data survival. |
| [deployment-control.py](deployment-control.py) | Exact main-template creation and count-only activation, with durable reservations and observation after uncertain responses. |
| [resource-control.py](resource-control.py) | Shared resource reservations; original-record-bound replacement, controlled healthy stop/start and snapshot creation. Healthy stop/start is not emergency failure recovery. |
| [failure-plan.sh](failure-plan.sh), [failure-stop.sh](failure-stop.sh), [failure-route.py](failure-route.py) | Plan and explicitly execute the initial-release stop control. Hold the real release-succession lock, reselect its policy and guard each exact reserved effect. No healthy application or SQL connection is required to stop a failed workload. |
| [failure-binding.py](failure-binding.py), [failure-control.py](failure-control.py) | Observe own failed/partial stack lineage, exact task revisions and other service configurations; reserve each count-zero or exact task-stop request once, reconcile uncertainty and retain actual stopped-state facts. |
| [restart.sh](restart.sh), [restart-route.py](restart-route.py) | Plan or explicitly execute one own count-one restart after initial-stop custody and a real earlier original-record read. Require a newly created qualified healthy task; do not claim data/history readback. |
| [recovery-state.py](recovery-state.py), [recovery-steps.py](recovery-steps.py) | Check retained stop/restart journals and gate bytes against current ownership and actual task evidence. Admit a new original read, then require applied migration history through the existing task route. |
| [credential-steps.py](credential-steps.py) | Require preserved read/history, permission observation, revocation, expected denial, restoration and a distinct replacement before fresh recovered read/permission proof. It supplies prerequisites, not launch or permission-repair authority. |
| [recovery-history.py](recovery-history.py) | Retain the completed credential step and exact bounded evidence-file closure before long restore work. Historical task validation never means current readiness. |
| [snapshot.sh](snapshot.sh), [snapshot-route.py](snapshot-route.py) | Plan or explicitly execute one original-record-bound source snapshot after completed credential proof and fresh target checks. No task replay, deletion or restored-database proof. |
| [task-control.py](task-control.py) | One reserved task submission, exact request identity and reconciliation without replay. |
| [task-evidence.py](task-evidence.py) | Closed, source-catalogue-checked task results, terminal-state/deadline checks and safe receipt validation. |
| [task-runner.py](task-runner.py) | Bounded observation and retention of one reserved task. Historical receipt reuse does not establish current state. |
| [preflight-control.py](preflight-control.py) | Closed observation-only launch selection and fresh, immutable prerequisite-receipt matching. It does not produce generic gate passes or grant provider authority. |
| [unready-control.py](unready-control.py) | Separate negative-recovery admission bound to a successful permission-revocation task. The public credential stage consumes it; expected-unready evidence cannot substitute for ordinary readiness. |
| [restore-control.py](restore-control.py) | Exact isolated restore creation/execution and owned cleanup after original-record reader completion. No source-database deletion. |
| [acceptance-evidence.py](acceptance-evidence.py) | Draft historical task-archive validation and immutable evidence retention, reusing the actual task/admission/completion owners. Historical proof is not current readiness. |
| [acceptance-controls.py](acceptance-controls.py) | Draft archive of the original safe control plan, selected graph, seven-gate report and original submission identity/time/hash. It cannot call AWS or execute a plan. |
| [collect-acceptance.sh](collect-acceptance.sh), [acceptance-route.py](acceptance-route.py) | Read the bounded acceptance input manifest, recheck actual proof and retain immutable candidate evidence. The provider allows reads only; collection does not accept a release. |
| [acceptance-state.sh](acceptance-state.sh), [acceptance-state.py](acceptance-state.py) | Validate a candidate or the existing succession current reference and its full archived feature proof. Historical validation is not current health. |
| [promote-acceptance.sh](promote-acceptance.sh), [acceptance-promote.py](acceptance-promote.py) | Recheck fresh same-candidate proof before ordinary release and local scope promotion. Reconcile exact retained custody after interruption without claiming new health or repeating AWS work. |

The task/resource/deployment/restore controls have corresponding `*-test.py`
fixtures here; binding has its own fixture, while graph/step/feature wiring is
exercised through `task-route-test.py`.
[infrastructure-route-test.py](infrastructure-route-test.py) exercises the public
route and actual generic gate with controlled source/custody/provider responses,
plus real CLI rejection cases. [deployment-control-test.py](deployment-control-test.py)
also supplies reusable simulated provider fixtures without running its cases
when imported. These Python functions are internal implementation seams, not a
general-purpose public deployment SDK.

## Check the command without accessing AWS

From the repository root, this example checks arguments only. The deliberately
nonexistent receipt is not opened:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/plan.sh \
  --phase create \
  --receipt /tmp/not-a-real-receipt.json \
  --proof-label entity-smoke-eeeeeeeeeeeeeeeeeeeeeeee \
  --validate-arguments
```

The actual output is:

```json
{"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []}
```

That establishes argument validity only—not package qualification, deployment
readiness, permission or approval. Missing approval on a review/execute command
returns `infrastructure-approved-plan-required`; it never silently becomes a
planning or deployment operation.

## Plan, review, execute

For actual planning, remove `--validate-arguments` and supply a real qualified
custody receipt. Use the frozen committed source checkpoint recorded by that
receipt. The selected account/profile/region are fixed by the target owner;
there is no caller-supplied endpoint or alternative target flag.

`script.py` first runs the existing declaration/delivery checks and registered
local checks. The selector may reuse matching local evidence. It then observes
the actual private target/dependency/image through the read-only alignment
consumer and performs the operator's identity/policy preflight. A policy
simulation is a preflight result, not proof that a change has executed;
[AWS documents that simulation can differ from live behaviour](https://docs.aws.amazon.com/IAM/latest/APIReference/API_SimulatePrincipalPolicy.html).

The safe plan includes source/image identity, contract/template/parameter
hashes, operator fingerprint, label and resource counts. Initial creation admits
exactly thirty own resources, including four added ingress rules on the existing
database security group and five on the existing delivery-endpoint group. It
does not replace the source database or modify its data/schema. Activation
modifies only the feature service's desired count, without replacement.
Endpoint and administrator-secret references stay in memory, not plan output.

After the user approves the concrete AWS plan, `script.sh --mode review` takes
the same phase/receipt/label plus `--approved-plan sha256:<the-plan-digest>`.
Review **creates a provider change set**, so it is itself a separately approved
AWS effect. `--mode execute` checks that reviewed change, exercises the execution
preflight and submits only its exact identity. The supplied digest prevents a
different plan from being executed; possessing a digest does not grant approval.
Follow the existing [AWS execution workflow](../../../../../../../.agentic/aws/workflows/execute-approved-aws-change.md).
These live examples have not been executed for entity-smoke.

The operation-specific [infrastructure graph](../../../../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/infrastructure-realization-contract.v2.yml)
describes this controller, its operator, control-plane connection and durable
intent store. It is deliberately separate from the application's runtime graph:
infrastructure validation cannot claim that not-yet-created application roles or
tasks have proved database access. Normalized observations pass through the
existing generic compiler; its [standard](../../../../../../../.agentic/04.deploy/standards/operational-realization-gate.md)
still owns the gate sequence and freshness requirements.

## Activation and interruptions

Activation additionally requires `--prerequisites <manifest.json>`. The manifest
contains exactly four reservation/receipt pairs: `bootstrap`, `migration`,
`grant-runtime` and `permissions`. The command validates the real receipt
protocol, current task/log observations, source/image/dependency/definition
bindings, declared completion codes/deadlines and order. The final permission
proof must be fresh. A migration's already-applied result cannot substitute for
the declared applied-completion result here. The initial task route below
assembles this manifest from actual collector receipts; do not hand-author
invented receipts.

Before submission, a private, synchronously flushed reservation records the
exact immutable attempt. A lost response permits observation of that attempt,
not another submission. Executing an existing reservation takes the observation
path even when the change is already executing or complete. Activation
reconciliation does not incorrectly demand that its predecessor still has a
zero desired count, but does compare retained resource identity with the actual
stack. Missing or mismatched observations block success.

`--wait-seconds` is bounded from zero to sixty, default thirty. A `pending`
verdict exits 2: the original remote operation has not been proved complete.
It is not a failed-task retry instruction. Finite failures keep supplied values,
native provider errors and parser text out of output. A before-submission
rejection remains distinct from an uncertain remote submission.
When a local check fails and its retained selector report is available, the
failure includes a checked `evidence_reference` for that report instead of
forwarding the child's native output.

## Initial task preparation

After infrastructure creation, the connected sequence is:

```text
administrator probe -> bootstrap
  -> migration probe -> apply
  -> administrator probe -> grant-runtime
  -> runtime-only probe -> permissions -> activation manifest
```

Each arrow requires the preceding operation's actual terminal task/log receipt,
not just a local file claiming success. The permission task uses the runtime-only
identity; the administrator still does not acquire runtime-login access.

`task-plan.sh` accepts `--receipt`, `--proof-label`, `--workload`, `--operation`
and `--phase preflight|operation`. Database-preparation workload/operation pairs
are `administration/bootstrap`, `migration/apply`,
`administration/grant-runtime` and `database-proof/permissions`. For example,
this is an offline argument check, not an executed AWS example:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-plan.sh \
  --receipt /tmp/not-a-real-receipt.json \
  --proof-label entity-smoke-eeeeeeeeeeeeeeeeeeeeeeee \
  --workload administration --operation bootstrap --phase preflight \
  --validate-arguments
```

It returns the same `deploy/command-arguments-report/v1` valid report shown
above. Without that offline flag, `prepare` checks qualified custody/source,
registered local proof, own infrastructure lineage, exact immutable ECS revision,
IAM trust/inline-policy inventory and private security groups. It derives the
selected operation graph and retains first-five evidence through the existing
generic compiler. The plan binds intended database effect, prepared versus
actual operation, deterministic probe label, request/prerequisite hashes and
source/rule/graph/template/role/network/operator identities. Missing prior work
sets `execution_route_available` false and names `pending_prerequisite`; it is
not treated as success. An implemented route awaiting activation, for example,
returns `task-prerequisite-required` with item `activation` on execution. An
unsupported operation instead returns `task-execution-prerequisites-not-connected`.

After concrete AWS approval, `task-execute.sh` takes those same arguments plus
`--approved-plan sha256:<the-exact-plan-digest>`. First execute the `preflight`
phase, then separately plan/approve/execute the `operation` phase. The command
never launches the second task automatically. It rechecks source/rule/target
bindings immediately before the sole RunTask, using a flushed reservation,
fixed private network and closed proof-selector overrides. A digest prevents
plan substitution; it is not human approval. `task-plan.sh` rejects execution
flags entirely.

`execute` calls the existing runner/collector. Only an actual successful probe
can supply gate six. Business admission requires that matching fresh probe,
created after the relevant preceding operation, and durably retains its original
admission before submission. Completed step packets are written under
`task-steps/`; original task receipts and admissions use `task-receipts/`.
Each step also needs its adjacent `.completion.json` sidecar, bound to the
unchanged collected packet, original plan and exact retained seven-gate report.
The route reobserves its own result before producing that final gate, then
writes the sidecar. If interrupted between those writes, later steps remain
blocked by `task-step-completion-required`. Resuming the original task can finish
its completion record without another launch. Historical completion bytes and
timestamps are not rewritten or treated as fresh current readiness.
Interrupted attempts reconcile their original reservation, not a new launch.
Historical completion is reobserved against the task/log consumer before it
advances this route; its original collection time is not rewritten.

Successful `permissions` completion returns an `activation_prerequisites` path.
`task-steps.py` assembles its exact four pairs and runs the existing activation
consumer against them. This establishes that the manifest is usable; it does
not activate the service or accept the release. Known pre-submission rejection
returns its finite condition with `effect: not-started`; a lost submission
returns `task-submission-uncertain-reconcile-required` with
`effect: unknown-reconcile-only`. Neither is automatic retry authority.

[task-route-test.py](task-route-test.py) exercises the actual provider guard,
runner, collector, generic compiler and activation consumer with controlled
transport and source/custody/alignment prerequisites. Its four probes/four
operations include a lost-response reconciliation with no second launch. These
are local protocol tests, not actual qualified image or AWS results.

## Evidence and remaining proof

### First-release failure stop

An image that cannot start or connect to its database still needs a safe stop
path. `failure-plan.sh` therefore uses a separate control-plane graph, not the
application's health graph. It checks qualified source/custody, the original
creation reservation and actual stack event lineage, exact own definitions and
operator permissions. A terminal failed or partial creation is allowed; an
in-progress stack writer or incomplete ownership observation is not.

This offline example checks arguments only and returns the same `valid` envelope
shown above. It neither opens the deliberately missing receipt nor calls AWS:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/failure-plan.sh \
  --receipt /tmp/not-a-real-receipt.json \
  --proof-label entity-smoke-eeeeeeeeeeeeeeeeeeeeeeee \
  --validate-arguments
```

For a real plan, supply the qualified receipt and omit the offline flag. The
plan permits at most one update of the own service's desired count to zero,
plus stopping at most 32 individually identified own standalone tasks. An
owned isolated restore reader is included only with its original creation
reservation and actual matching stack/template/definition lineage. No task
launch, SQL, permission change, database/stack deletion or baseline change is
available through this command.

After concrete approval, `failure-stop.sh --mode execute` takes the same receipt
and label plus `--approved-plan sha256:<the-exact-plan-digest>`. That digest is
not approval by itself. The command holds the canonical
[custody lock](../../../../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/30-release-evidence/README.md)
and rechecks policy/source/ownership immediately before each effect. Once an
accepted release exists, this initial stop policy is unavailable. Normal
compatible-image restoration remains required for subsequent releases.

`failure-attempts/` retains the original plan and each single submission under
the existing private label cache. Lost responses reconcile those reservations;
neither a smaller remaining task set nor an expired wait authorizes a new
submission. Completion requires zero service counts and actual `STOPPED` facts
for the original tasks. A retained historical receipt is identified as such,
with a separate current-stopped flag; reusing it does not stop a restarted
service again. Wait bounds and `pending` exit status match the commands above.

The receipt deliberately says `independent_data_readback: false` and
`migration_history_readback: false`. Non-SQL database metadata and no database
mutation are not proof that original records/history survived. Independent
read/state proof is still required before first acceptance. The
[failure fixture](failure-route-test.py) covers unhealthy/unpulled/queued jobs,
partial creation, an owned restore reader, uncertain responses without replay,
changed custody/baselines, altered payloads and retained-evidence rejection.
Those controlled responses are not live AWS or data-preservation proof.

### Restart and independent preservation observations

Stopping a service without deleting its database is not proof that its original
record and migration history survived. The first-release recovery sequence is
therefore deliberately separate:

```text
earlier original-record read -> owned stop -> separately approved restart
  -> new ready probe -> original-record read
  -> administrator preflight -> applied migration-history observation
```

`restart-route.prepare` requires the original stop journal, receipt and unchanged
gate bytes, the actual earlier read, the initial-release custody policy and exact
source/image/runtime role/network bindings. It checks the other services have
not changed. The stopped application does not have to be ready to admit its own
start. `run` holds the real succession lock and supplies only the exact own
UpdateService desired-count-one capability after concrete approval and the normal
control-plane gates. It cannot RunTask, execute SQL, repair permissions or delete
resources. A pending or lost-response attempt reconciles its original reservation;
it cannot submit another start. Completion requires the qualified healthy server
created after that reservation. Its receipt still explicitly says both independent
data and migration-history readback are false.

For an offline argument check only, this invented receipt is not opened:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restart.sh \
  --mode plan --receipt /tmp/not-a-real-receipt.json \
  --proof-label entity-smoke-eeeeeeeeeeeeeeeeeeeeeeee \
  --expected-digest 1111111111111111111111111111111111111111111111111111111111111111 \
  --validate-arguments
```

It returns `deploy/command-arguments-report/v1` with `verdict: valid`, not an
execution plan, deployment approval or AWS proof. Actual execution additionally
requires `--mode execute --approved-plan sha256:<the-reviewed-plan-digest>` and
concrete authority; the digest itself is not permission.

For the following observations, the existing task plan/execute commands use
`--proof-stage initial-recovery` with the same original label/digest. Only
`verifier/read` and `administration/observe-migration-state` are admitted in this
stage. Each has its own separately selected preflight and attempt keys. The
original read must follow the actual restarted server. The administrator's later
observation must follow that read and report
`PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED`; a result saying a migration may
run is rejected as preservation proof. The digest stays in administrator plan
metadata, not an undeclared environment override. Existing fresh-ready admission
and no-replay rules still apply.

`recovery-state` reuses the stop owner's static scope-binding checks without
removing its original unplanned-task guard. A running recovery observation may
be reconciled only through its own exact reservation; unrelated active jobs
block it. Copied old read journals cannot satisfy the new creation-time floor.
The stop journal/observation keeps fractional UTC time, so an immediately prior
read cannot be falsely reordered by rounding the stop down to a whole second.
Retained timestamps are read as recorded, never rewritten.

[restart-route-test.py](restart-route-test.py) drives the actual restart and task
route/runner/collector/gate consumers with shared controlled source, custody,
alignment, task and transport producers. It exercises preservation ordering,
lost/pending starts, exact payloads, changed prerequisites/evidence and unsuitable
history results without another launch. These are local protocol tests, not
database or AWS survival proof. The later connected restore fixture covers
isolated restore/cleanup and the distinct final read; actual live acceptance
collection remains required.

### Baseline feature operations and uncertain create

After activation, the same task commands support `verifier/create`,
`verifier/lifecycle`, `database-proof/collision` and `verifier/read` in that
order, each with its own separately planned/approved probe and operation.
Collision and read require `--expected-digest` equal to the original create
receipt's `record_digest`. Lifecycle creates and exercises the separate
`<label>-lifecycle` entity; its digest cannot substitute for the original.
These are baseline checks, not post-replacement or restore proof.

`feature-steps.py` requires the real activation reservation/receipt and current
exact running service/image, plus reobserved preparation packets. Verifier
plans also bind the server's actual role/configuration/network checks and
recheck that callee before launch. Later operations require preceding feature
receipts, exact original digest and creation-after-predecessor ordering.
Each prepared operation shares one validated template snapshot across its task,
server-callee and prerequisite binding checks. A later preparation or provider
guard reads afresh; all provider comparisons still run. Completion deadlines
come from the prepared checked declaration rather than reparsing it for every
prerequisite request. There is no process-wide source cache; source/rule and
configuration fingerprints are rechecked after provider reads before submission.

If original create has an uncertain result, do not submit it again. The
`verifier/observe-create` route requires that original reservation and matching
actual terminal task/qualified image before its own probe and read. It retrieves
the one indexed original and retains its ID-bound digest without recreating it.
Missing reservation, a still-running original task, wrong image, absent record
or failed read blocks advancement. Later steps may consume this observer's
receipt instead of a missing create success. Read-only reconciliation is an
explicit task-control function; it has no RunTask branch.

The controlled route fixture simulates a completed create with missing success
output. Repeating observation of that attempt still cannot collect success or
launch another create; the separate observer then establishes its original
digest. Lifecycle, collision and read consume it while the original create
submission count stays one. The HTTP/feature fixtures cover their own behavior;
these task-protocol doubles do not establish actual PostgreSQL or AWS effects.

Both public task and infrastructure failure reports preserve the selected
primary `diagnostic`, `related_diagnostics` and observed bundles through the
existing catalogue validator. If diagnostic projection itself fails, they keep
the operation's condition/effect and report the finite
`diagnostic_processing_condition: task-diagnostic-not-confirmed`; they neither
expose native values nor replay an operation. This does not make unsupported
recovery or cleanup operations executable.

### Runtime replacement and a fresh original-record read

First complete the baseline original-record read above. Then `replacement.sh`
takes `--mode plan`, the same qualified `--receipt` and `--proof-label`, and
`--expected-digest` from that original record. It reobserves the actual baseline
task/log receipt and its preparation/activation/feature prefix. It chooses the
one own running server task; the caller cannot supply an alternative task ARN.
The plan binds that exact task, original digest, source/image, network/roles,
dependency and operator. These provider reads and policy simulation are not
evidence of a completed replacement.

After concrete approval, `--mode execute --approved-plan sha256:<the-plan-digest>`
admits one exact reserved StopTask with its original operation reason. The
provider has no task-launch, count-change, SQL or stack-write capability.
Actual stopping must match that reason and be followed by a distinct healthy
same-definition/image server. A known guard rejection remains `not-started`;
a lost response is uncertain and only reconciles the original reservation.
`replacement-plan.json`, `replacement-plans/` and `replacement-receipt.json`
live in the existing private label cache. They are not accepted release custody.
Default wait and pending-exit behavior match the other bounded controllers.

Replacement completion says `post_replacement_record_readback: false`. To prove
survival, use the normal task commands with `--workload verifier --operation read`,
the original label/digest and `--proof-stage server-replacement`. Plan, approve
and execute its `--phase preflight`, then separately its `--phase operation`.
The default stage is `baseline`; initial and credential recovery have the
separate closed selections described here. No non-baseline stage permits create,
lifecycle or an arbitrary operation.

The staged route checks the actual retained approved replacement plan, original
resource journal, generic gate bytes and current stopped predecessor/healthy
successor. Its new ready probe and read must be created after replacement, with
distinct stage keys and a separately selected probe label. A baseline probe or
copied baseline read cannot substitute, and the original record is never created
again. [task-route-test.py](task-route-test.py) exercises this connected sequence
with controlled source/custody/alignment/transport; the
[resource fixture](resource-control-test.py) separately rejects impossible timing
and distinguishes known non-submission from a lost response. These are local
protocol tests, not proof of real AWS replacement or PostgreSQL survival.

### Read-only preflight before database work

Before a migration can change a table, its own restricted identity must prove
that it can reach the selected database. This is not done by letting the
administrator impersonate that identity. The existing administration, migration
and database-proof programs now each support an explicit `preflight` operation.
The private HTTP verifier uses its existing `ready` operation.

The [preflight implementation](../../../../../../../infra/04.deploy/03.product/entrypoints/entity-smoke/preflight.ts)
opens one connection through the same checked pool as the later operation,
begins a read-only transaction, and observes the current user/database and
selected authority/schema facts. It rolls back and releases the connection
before returning `ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED`. It does not create
the schema, apply a migration, change grants or attempt denied writes. These
checks establish connection and selected prerequisites, not every future SQL
permission. The separate effective-access proof remains required.

For example, the migration program's successful stdout is exactly:

```json
{"verdict":"passed","code":"ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED"}
```

The administration program additionally includes `"operation":"preflight"`.
If the observed database identity differs from its configured one, the actual
reporter preserves the following diagnostic (excerpt of its failure envelope):

```json
{"schema":"core/diagnostic-record/v1","code":"entity-smoke-target.preflight-rejected","definitionVersion":1,"detail":{"identity":"migration","field":"identity","condition":"mismatch","effect":"not-started"}}
```

Supplied usernames, credentials and provider messages are not part of the
record. Native SQL denials use the existing PostgreSQL translator instead of
being replaced by that semantic mismatch. A rollback/release failure prevents
success; cleanup failure after a body error is retained separately without
replacing the original error.

All three SQL programs now delay their success line until the pool also closes.
The proof reader follows forward log tokens through at most three pages and
rejects incomplete pagination rather than accepting a prefix. That establishes
the observed stream end, not a guarantee about future log ingestion.

`validate_launch` in [preflight-control.py](preflight-control.py) admits only
the declared observation mode and closed proof selectors, with a deadline of
at most ninety seconds. `require_receipt` checks the real evidence collector's
result, matching task/image/source/configuration/permission/dependency/network
bindings, the explicitly selected probe label, freshness and prerequisite
ordering. The probe label can be separate from the business-record label;
it must be selected by the owning operation plan, not invented to replay an
uncertain launch. No receipt timestamp is advanced to make it current.

Before a new business launch, its original preflight admission packet is also
flushed under the selected receipt root's `admissions/<operation-id>.json` and bound to the exact
task reservation. On interruption, reconciliation checks that original packet
at its original admission time. Missing or changed admission blocks proof; an
expired historical probe is never restamped or automatically launched again.

`run_owned_task` now requires a matching `preflight` packet and `required_after`
before reserving a **new** business task. Missing evidence returns
`task-preflight-receipt-required` before provider calls. An existing reservation
can only reconcile; an unchanged retained success can be returned historically
without launching again. Preflight reservations also prevent alternate keys
from repeating their one launch. A deadline does not itself stop the remote
task or authorize another submission.

The [AWS applicability rule](../../../../../../../.agentic/aws/standards/operational-realization-applicability.md#entity-smoke-read-only-execution-preflight)
allows a concretely approved observation task after the first five normal
gates so that real connection proof can supply the sixth. It does not mark that
gate passed in advance. The initial task preparation route above consumes these
controls; the infrastructure command itself still cannot launch a task.
[preflight-control-test.py](preflight-control-test.py), the task/evidence/runner
fixtures and the [actual-entrypoint fixture](../../../../20-build/entity-smoke-composition/preflight-test.mjs)
exercise controlled responses only. Finished-image qualification now includes
these modes, but it has not been executed against Docker/PostgreSQL yet.

### Expected-unready recovery observation

The declared recovery test deliberately removes runtime database access, then
checks that the server is still live but correctly reports not ready. Requiring
the usual successful `ready` probe at that point would contradict the test.
The approved [bounded exception](../../../../../../../.agentic/aws/standards/operational-realization-applicability.md#expected-unready-recovery-observation)
therefore permits the existing read-only `unready` mode for this proof only.
It does not permit business work against an unready application.

Inside the runner, `unready-control.validate_launch` checks the actual collector's
retained administration `revoke-runtime` packet, the selected label and matching
source/image/configuration/permission/dependency. It rejects arbitrary overrides
or a deadline above ninety seconds. Before submission, `retain_admission` flushes
that exact packet bound to the new reservation under
`unready/admissions/<operation-id>.json`. `read_admission` checks the same packet
on interruption; it cannot be silently replaced. The observation task must have
been created after revocation and return `ENTITY_SMOKE_LIVE_NOT_READY` through
the actual task/log collector. Ordinary `preflight-control.require_receipt`
still rejects that result as readiness admission for feature work.

For example, `run_owned_task` given `unready` with no matching revocation packet
returns `unready-revocation-required` before reserving or launching anything.
With valid evidence it can collect that one negative observation; another caller
key cannot relaunch a lost attempt. Historical reuse does not reobserve current
health or restamp the original admission. A separately reserved successful
`ready` probe after restoring access is still required by the recovery rule.

The public task commands now connect this observation through the closed
`--proof-stage credential-recovery` sequence:

```text
initial recovered original read + applied history
  -> administrator probe + observe-permissions
  -> administrator probe + revoke-runtime
  -> one unready observation (no separate preflight phase)
  -> administrator probe + restore-runtime
  -> separately approved credential replacement
  -> new ready probe + original-record read
  -> runtime-only probe + permissions
```

Each operation uses the same original label/digest and qualified receipt. The
administrator receives no extra digest override. Except for the one negative
observation, each task still requires its own separately planned and approved
preflight. The commands never automatically run this entire sequence.

For an offline argument check only, this invented receipt is not opened:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-plan.sh \
  --receipt /tmp/not-a-real-receipt.json \
  --proof-label entity-smoke-eeeeeeeeeeeeeeeeeeeeeeee \
  --proof-stage credential-recovery --workload verifier --operation unready \
  --expected-digest 1111111111111111111111111111111111111111111111111111111111111111 \
  --validate-arguments
```

It returns the `deploy/command-arguments-report/v1` valid envelope, not a live
plan or execution permission. Selecting `--phase preflight` instead is rejected
with `task-unready-preflight-phase-prohibited` before provider access.

`credential-steps.prefix` reads the actual predecessor packets, admissions and
task/log results in order. Its negative graph retains every reachable component
but explicitly declares revoked access and observation-only semantics. Its
sixth gate means only this completed expected-denial observation, never ordinary
healthy database access. Missing or copied revocation cannot admit it, and an
ordinary healthy response cannot satisfy its collector.

After restoration, `replacement.sh` uses the same receipt/label/digest with
`--proof-stage credential-recovery`. Its plan and single StopTask target the
original restarted server, not a caller-supplied ARN or its successor. Separate
`credential-replacement-*` plan/receipt/gate paths and the existing resource
journal retain that original operation across interruption. Subsequent read
must match its actual qualified successor and a new successful ready probe.
Neither baseline replacement evidence nor pre-restoration readiness substitutes.
The final permission proof does not rewrite the original activation manifest.

[task-runner-test.py](task-runner-test.py) covers the internal bounded admission.
[credential-route-test.py](credential-route-test.py) exercises the real public
task/replacement/collector/compiler/store consumers, the interruption between a
collected result and final gate, missing/changed prerequisites, wrong negative
result at the real reporter, and lost launch/stop responses without replay.
Their source/custody/alignment/task/transport responses are controlled local
protocols, not an executed AWS recovery or PostgreSQL proof. Neither helper
availability nor a local pass grants AWS execution authority.

### Retained evidence

The completed credential permission task also returns `credential_history`.
That private `credential-history.json` packet binds its final plan, prerequisite
packets, original digest and at most 256 retained file references. Each reference
is limited to the owned cache layout and one MiB; journals, receipts, admissions,
step sidecars and their referenced final gates keep exact byte hashes. Required
dependencies cannot be omitted. Its `current_readiness` and `scope_acceptance`
fields are explicitly false.

This matters because old stopped-task observations may expire while a database
restores. `recovery-history.read` validates the retained source/protocol/custody
instead of requesting those old tasks again. The explicit historical task-step
mode still requires the original reservation, receipt, admission and completion;
it is never selected automatically after a failed provider observation. The
ordinary task route still reobserves current task/log completion. Missing or
changed retained files block history; neither missing AWS data nor a local
packet authorizes replay, fresh readiness or acceptance.

### Snapshot before isolated restoration

A completed feature recovery and a new RDS snapshot are different proofs:

```text
completed credential history -> fresh target/current-runtime checks
  -> separately approved original-record-bound snapshot
  -> isolated restore/read/owned cleanup -> distinct final probe/read
```

`snapshot-route.context` revalidates committed qualified custody, registered local
proof, live alignment and own infrastructure lineage. It checks current server
image/definition, identity, private networking and absence of active proof jobs,
independently of historical task retention. The source snapshot helper separately
requires the same available, encrypted, private database incarnation. A historical
success cannot make a rebooting or changed database an eligible snapshot source.

This offline argument example does not open the invented receipt or call AWS:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/snapshot.sh \
  --mode plan --receipt /tmp/not-a-real-receipt.json \
  --proof-label entity-smoke-eeeeeeeeeeeeeeeeeeeeeeee \
  --expected-digest 1111111111111111111111111111111111111111111111111111111111111111 \
  --validate-arguments
```

It returns the same `deploy/command-arguments-report/v1` valid envelope shown
earlier. Actual planning omits that flag and needs the frozen qualified receipt
and original digest. It binds the history hash, source/image/contracts,
configuration, exact operator and one owned snapshot name. Operator policy
simulation is not proof of successful snapshot creation. First-five evidence
uses a distinct control-plane snapshot graph, not healthy SQL-access claims.

After concrete AWS approval, `--mode execute --approved-plan sha256:<plan-digest>`
admits only one exact CreateDBSnapshot request, including the source and owned
label tags. The original reservation is flushed before I/O, and the actual
source/target/history/operator bindings are rechecked at that boundary. The
guard reuses the prepared local source proof only while its source digest remains
unchanged; it does not skip fresh target observations. A known pre-I/O rejection
remains `not-started`, distinct from an uncertain remote response. Both consumed
attempts reconcile rather than submitting another create.

Completion requires actual snapshot identity, source incarnation, ownership,
availability and creation at or after the retained original-record observation
and reservation. `snapshot-plan.json`, `snapshot-plans/`, `snapshot-realization/`
and `snapshot-receipt.json` use the same private label cache. A pending snapshot
exits 2 under the existing zero-to-sixty-second observation bound. Its receipt
always says `isolated_restore_proven: false`: it does not create a clone, read
restored data, delete resources or accept the feature. Those later public
connections remain required by the implementation plan.

The connected credential fixture exercises the actual snapshot route/provider/
resource helper and compiler, including expired controlled old tasks/logs,
tampered/omitted history, denied operator, unavailable source and lost-response
reconciliation with one create and no task replay. Its observations remain
controlled local protocols, not AWS snapshot or restoration evidence.

### Working and accepted evidence

Working reservations, normalized observations and safe infrastructure receipts
live under ignored `.cache/entity-smoke-live/<proof-label>/`, not the chat log.
Observations retain their original component times; serialization does not make
them fresh again. Their outer record also binds the selected plan hash, without
putting provider values into generic compiler facts. Local test-run reports use
`.cache/test-runs/` as usual.
These working receipts are not an accepted release or a parallel release ledger.
The final collector must validate and retain actual live proof under the scope's
existing release-evidence ownership before normal succession/promotion.

The draft acceptance archive keeps the checked plan and gate report, not merely
a hash claiming they existed. `acceptance-controls.capture` reads the original
gate only under the selected control's private cache directory and compares its
original byte hash. `validate` checks the plan's closed fields and limits, exact
source/contracts/original-record binding, graph, original submission identity
and all seven gates through the existing completion/generic gate owners. Stop
and restart keep their existing custody-composed controller hash; they are not
silently relabelled as ordinary task-controller proof.

For example, passing only a snapshot fact projection to the collector's full
`validate_control` returns `acceptance-control-custody-required`: knowing a
snapshot name is not proof of the approved operation. Historical validation
does not call AWS, query today's source or advance timestamps. The
[acceptance-control fixture](acceptance-control-test.py) exercises all seven
control graphs with real local gate production and controlled plans, including
the explicitly approved disposable-restore cleanup declaration. Ordinary deletion
still fails without that declaration. These tests are not live control receipts;
no candidate or accepted release has been produced for this feature.

For cleanup, [restore-route.py](restore-route.py) first validates the original
successful reader and retained plan/gate custody, observes exact clone ownership
and requires the approved concrete plan digest. The bounded
[provider rule](../../../../../../../.agentic/aws/standards/operational-realization-applicability.md#entity-smoke-disposable-restore-cleanup)
protects source database/snapshot, accepted baselines and staging. Rule approval
alone does not authorize AWS execution. The controller reserves one DeleteStack;
an uncertain response reconciles that reservation without another submission.
`completed_cleanup` is the read-only consumer: it requires original gated cleanup
and actual owned absence, not just missing resources.

The [connected restore fixture](restore-route-test.py) now reaches that cleanup
and the distinct final probe/read through the actual controllers, runner,
collector and compiler, using controlled source/custody/provider protocols.
Missing original reader/cleanup, foreign ownership, changed resources and wrong
approval are rejected. Lost cleanup/final-read responses do not replay effects.
This establishes local protocol behavior, not real PostgreSQL/RDS restoration,
image qualification or completed live collection/promotion.

### Acceptance commands and their boundary

The [scope route](../../../../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/acceptance-route-contract.yml)
lists the actual commands. Its composite proof requires nineteen named task
selections and seven control selections, not only a healthy process. The
registered `entity-smoke-acceptance` check runs at the acceptance stage, not as
ordinary local development feedback. Its input manifest has exactly
`candidate_receipt`, `proof_label` and `expected_digest`, under the existing
`deploy/acceptance-inputs/v1` target/scope envelope. The collector reads actual
owned receipts; the manifest is not a place to supply invented passing results.

This offline example checks only arguments; it does not open the missing input
file, contact AWS or write a candidate:

```bash
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/collect-acceptance.sh \
  --inputs /tmp/not-a-real-acceptance-manifest.yml --write-candidate --validate-arguments
```

It returns `deploy/command-arguments-report/v1` with `verdict: valid` and the
composite `proof_contract`. An unknown argument returns the finite
`acceptance-arguments-invalid` condition, not parser text or submitted values.
Without the offline flag, successful collection returns `candidate_record` and
explicitly reports `scope_acceptance: false` and `current_readiness: false`.

`acceptance-state.sh --operation validate-candidate --candidate-record <path>`
checks that candidate and its exact content-addressed proof. `--operation
current-release` returns the existing accepted release ID, or `none` only when
the governed first-release policy really permits missing custody. It does not
create an accepted record. `--operation validate-current` follows the existing
current reference through immutable history to the feature candidate/proof;
it does not require historical contracts to equal today's files.

The route's `promote-acceptance.sh` command additionally requires the manifest,
candidate path, exact scope contract, `--expected-predecessor` and explicit
`--write`. Before new acceptance it reobserves full current proof, requires the
same candidate and fresh original-record read, and checks current contracts.
Under the existing succession lock it then uses normal immutable release
promotion and the shared scope promoter. It does not mutate AWS. The generic
succession aliases in the route are compatibility interfaces, not a substitute
for this feature's fresh-proof guard or a feature legacy-import proof.

An exact already-current release or its original interrupted archive can
reconcile without new provider work; that outcome is `retained`, with
`current_readiness: false`. If release custody advances but the later local
scope transition fails, the report preserves that known effect. Do not discard
the current reference or replay deployment to repair a local index transition.
The [route fixture](acceptance-route-test.py) distinguishes real offline-parser
checks from controlled candidate/validator/promotion protocols. Neither those
protocols nor a covered route template is live acceptance evidence.

The public infrastructure route does not launch tasks, perform SQL, delete
resources, purge feature records or grant application acceptance. Isolated restore/
cleanup, final collection/validation and actual package/publication/AWS
execution remain required. Existing accepted scopes and staging are preserved.
