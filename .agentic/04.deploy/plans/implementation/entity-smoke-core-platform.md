<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.entity-smoke-core-platform
version: 3
status: active
created_on: "2026-11-07"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.entity-smoke
disciplines: [architecture, backend, security, sre]
kind: implementation-plan
purpose: Govern the approved isolated entity-smoke scope and its feature persistence, packaging and target proof chain without changing accepted baselines.
portability: {class: internal, targets: []}
used_by:
- id: product.feature.plan.first-persistence-pilot
  path: .agentic/03.product/feature/plans/implementation/first-persistence-feature-pilot.md
-->
# Isolated entity-smoke scope on core-platform

## Authority and boundaries

The user approved repository implementation of an isolated `entity-smoke`
scope on `kanbien-core-platform`, its own feature image, PostgreSQL
migration/permissions and live proof chain. This is not AWS execution,
publication, resource creation, migration execution or staging-retirement
approval. Follow the existing declaration/build/package workflows, shared
diagnostic coverage and the AWS plan/execute workflows at their boundaries.

Preserve `bootstrap-runtime` and `core-server-persistence` accepted releases,
dependency approvals, workload identities, database roles and receipt history.
Do not mount the feature into either accepted image. Do not add staging
dependencies or treat the repaired staging-shell compiler as the feature image.

## Implementation and consumer inventory

| Owner | Change and consumer | Proof that rejects a broken implementation |
| --- | --- | --- |
| App feature | app-owned relational row mapping and repository using an injected SQL capability, public export only | fields/nulls/arrays/timestamps survive mapping; queries bind values; ordinary list excludes logical deletion; restore can read lifecycle state |
| Deployment composition | isolated entity-smoke program; inject existing PostgreSQL adapter, Core clock/UUID, lifecycle policy | real feature use cases operate through the repository; no app imports of provider/deployment code |
| Migration composition | checksum-bound feature migration through the existing transactional runner; separate migration identity | wrong checksum fails; second observation is already-applied; runtime cannot DDL or purge |
| Image | own image contract, exec entrypoint, payload and immutable custody | isolated public app imports; actual image start and disposable real PostgreSQL round trip; missing payload fails |
| Target scope | own declaration/binding, configuration, health/completion and permissions | declaration coverage and configuration delivery reject missing sources, commands, identities and proofs |
| Scope lifecycle harness | truthful initial isolated-scope state without inventing an accepted predecessor | unaccepted scope cannot claim active/accepted evidence; existing replacement and ownership rules remain enforced |
| Live route | bounded synthetic feature operations through deployed runtime, independent read after replacement | same original ID/facts retrieved without recreating them; safe failure and explicit terminal state; no replay on uncertainty |
| Selector/reviews/docs | registered phase-specific proof units, source-matched diagnostics, public guides and indexes | impact selects complete chain; exact safe diagnostic assertions; report distinguishes planned/local/container/live |

No platform package may import app internals. SQL values are bound parameters;
the reviewed schema identifier is validated and quoted by composition. Preserve
adapter diagnostics at repository failures. Optional diagnostic observation
cannot change outcomes or retry mutations. New local validation must carry safe
finite field/reason details, never SQL values, native errors or rows.

## Ordered delivery

1. Complete and retain the independent image-mapping/shim repair's focused
   registered proof before changing its verification inputs.
2. Establish the isolated scope's factual lifecycle and complete declaration
   chain. A planned command is not an implemented proof. Missing chain elements
   remain gaps; no package or target advancement until coverage passes.
3. Implement the repository/migration/runtime with separate themed modules,
   deliberate public indexes and focused tests. Keep existing accepted program
   dependencies unchanged. Use deterministic seams for local tests; label
   those as doubles, not real-engine proof.
4. Consolidate source/diagnostic review, freeze inputs, run focused registered
   checks, inspect the full impact plan, then complete affected integration.
   Do not repeat unrelated suites after every edit.
5. Qualify the actual isolated image against disposable PostgreSQL, including
   persisted read after replacement, index/nullable/type mapping, lifecycle and
   role-negative cases. Existing image proof cannot substitute. Retain immutable
   identity and safe results under the package owner.
6. Produce the concrete AWS change packet only after fresh target alignment.
   Bind the exact image/custody, foundation/network, isolated database/schema,
   roles/grants, migration task, runtime and private verifier. No public ingress,
   tenancy, application auth, queue or telemetry programme is added.
7. Ask for approval of the concrete plan before any provider mutation. Enforce
   realization gates and execute one labelled attempt per owned operation.
   Reconcile uncertain operations before any new attempt. Migration is never
   a startup side effect. Preserve existing core-platform workloads throughout.
8. Run the declared AWS proof only under that authority and retain safe,
   identity-bound receipts. Do not advance accepted state on health alone.

## Required feature proof

Create every selected attribute type including nullable values; view and edit;
list through the named status/createdAt index; archive and restore archive;
logical delete with default invisibility; restore inside the recovery window;
reject expired restore; assess purge eligibility without executing hard purge.
Read the original durable facts after runtime replacement. Prove validation and
database failure diagnostics are safe, runtime lacks structural/delete power,
and a failed/uncertain mutation is not automatically retried. An SQL index's
existence and query shape are separate from an optimizer's chosen plan on a
tiny fixture; do not falsely assert that PostgreSQL must choose an index scan.

Hard purge remains excluded until retention, legal-hold, target and execution
governance are selected separately. No cleanup may delete user or baseline data;
disposable fixtures require exact ownership and their own cleanup boundary.

### PostgreSQL role review

The isolated administrator reuses the existing bounded-login/IAM helpers and
selects only the new schema-owner role when applying object policy. PostgreSQL
16 does not automatically give a non-superuser role creator the ability to
`SET ROLE` to the created identity. The bootstrap therefore explicitly grants
that ability for `entity_smoke_migration`, without privilege inheritance; it
does not grant migration ownership to the runtime. Qualification must use a
restricted administrator, not a database superuser that would hide this gap.
Sources reviewed 2026-11-07: [role attributes](https://www.postgresql.org/docs/16/role-attributes.html)
and [GRANT](https://www.postgresql.org/docs/16/sql-grant.html). Real RDS
managed-role behaviour still requires target evidence, not inference from a
local PostgreSQL fixture.

## Current state

### Approved entity-smoke preflight applicability

The user approved the bounded preflight rule on 2026-11-08, closing the
task-launch governance question recorded below. Implementation belongs in the
existing AWS applicability standard, not a generic compiler bypass or the old
staging exception. Concrete AWS execution approval is still absent.

Consumer/predicate inventory for this slice: add an explicit read-only
`preflight` mode to the existing administration, migration and database-proof
programs; keep HTTP `ready` as its existing non-business-mutating probe. The
database mode uses the same immutable program, identity, TLS configuration and
network as the subsequent operation, but only read-only SQL. Check configured
database/current identity, single well-typed observation, administrative grant
authority or bounded migration/runtime role and schema privileges. Missing,
wrong-type, mismatched or rejected facts have separate finite safe conditions;
neither values nor native errors enter the new local diagnostic definition.
Always release the connection and confirm rollback before reporting success;
preserve a body failure if rollback also fails. Never bootstrap, migrate,
change grants or execute a DML/DDL denial probe in this mode.

The existing task request/evidence/runner owners must admit only these explicit
preflight selectors and their exact code, retain immutable source/image/config/
permission/dependency/network bindings, enforce a ninety-second task deadline,
and prevent alternate keys from resubmitting the same preflight. A provider
adapter may launch it after the first five normal gates pass under the bounded
AWS rule; it cannot mark execution-preflight passed until actual terminal task
evidence succeeds. Business operation admission requires a fresh matching
preflight receipt newer than any relevant state-changing prerequisite.

Prove through existing composition and task-control/evidence fixtures: no SQL
writes, identity/authority/count/type rejections before dependent work,
rollback/release failures, safe actual reporter preservation, exact success-code
selection, changed binding/stale receipt rejection and lost-launch no replay.
Extend actual finished-image qualification to run these packaged modes against
its real disposable engine before business operations. Regenerate the existing
code-owned target catalogue; do not hand-edit its diagnostic vocabulary. Public
provider wiring remains incomplete until it consumes these controls; no actual
task, engine/image or AWS proof follows from controlled local fixture passes.

Reviewing the new migration preflight caller found that its old catch reported
native pool errors only as a target-boundary fallback: unlike migration-runner
failures, a direct preflight query has not already been translated. Reuse the
existing PostgreSQL readiness failure translator and the explicit target
catalogue selection for this new read-only path. Apply the same accurate
readiness operation to the administration/database-proof preflight wrappers.
Keep existing business-operation mappings unchanged. Extend actual-entrypoint
fixtures with a recognized SQL denial, semantic rejection and rollback/release
failure; assert the exact source code/classification/operation/phase/effect,
no success, no replay and exclusion of native credential-message canaries.
The cleanup counterexample also covers a release throw after a body failure:
report the cleanup companion without replacing the original body error. A lone
rollback/release failure must still prevent a success result. This is the new
preflight owner's correction, not a refactor of unrelated database helpers.
Interrupted-launch review found a second boundary: keeping preflight only in
memory would let reconciliation lose the original admission ordering. Retain
an immutable admission packet, bound to the exact task reservation and original
admission time, before the sole provider call. Reconciliation validates that
original packet without demanding a fresh probe or rewriting its time. Missing,
changed or later-fabricated admission blocks evidence, never permits relaunch.
This is local attempt evidence, not a second accepted-release ledger. Cover
lost business launch, changed/missing admission and successful historical reuse.
The same review covers the read/reserve race: even if another process reserves
after the first lookup, the runner must validate the original retained admission
before collecting proof. A controlled race/missing-admission counterexample
rejects evidence and never launches another task.

Task-result consumer review found that the old single get-log-events response
could be a prefix, not a complete stream; the AWS
[GetLogEvents contract](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_GetLogEvents.html)
says partial or empty pages do not establish completion, and forward-token
equality marks its observed end. Reuse the existing baseline reader's bounded
pagination pattern within the own task-evidence owner, not a new telemetry
framework. The runner and actual activation caller must use that reader; direct
collector fixtures remain explicitly controlled data. Require a stable token
within three pages, retain at most the existing thousand events, and reject
missing/malformed/changing tokens or overflow. Do not retain provider tokens or
native logs. Exact fixtures cover empty intermediate pages and a later failure.
Also hold all three own SQL programs' success output until pool closure succeeds;
a close failure cannot leave an earlier apparent success in a log prefix.

Consolidated self-review for this bounded source batch is complete: read the
whole changed task control/evidence/runner/admission modules and selected SQL
programs, definitions/reporter and real adapter/role consumers. Corrections above
are connected at actual callers, including activation's log reader and its
counterexample rejecting a preflight substituted for bootstrap. Existing
compiler gates are unchanged; the provider rule is explicitly scoped and no
preflight pass is invented. The new reviews remain partial about unimplemented
public provider checks and unqualified actual engine/AWS semantics. README skill
updates explain the real modes/admission sequence, exact reports and remaining
route without broadening the documentation sweep. No agent is concurrently
editing these verification inputs. Focused verification may now run on this
stable batch; the full proof goal remains unfinished.
Final reading clarified the provider rule's introduction: it governs launch
and completion boundaries, not an impossible demand for terminal evidence before
the probe launches. Executable ordering is unchanged. This documentation input
change reopens the composition receipt's identity; revalidate that registered
unit without rerunning unrelated suites or the unchanged secret regression.

Final scoped verification for the approved preflight batch: composition
EXECUTED/PASSED in 74.081369 seconds at
`.cache/test-runs/20261108T183901Z-2459010aef0243e98e6d9a038874d084/report.json`
(SHA-256 `7725600b937ffa3f6e9041b503254daa9cc577e9969dd11e5903d2074859f2a1`).
Secret regression EXECUTED/PASSED in 11.143915 seconds in the preceding
`20261108T183648Z-500323e6d9034ab0b7f5b0b7028e8249` run; its declared inputs
are unchanged by the final wording correction. Exact input/runtime hashes and
that report hash are in the active session. Thirty-six metadata headers,
28 relative links and whitespace pass; actual feature secret/health declarations
pass. Adoption still reports 39 unfinished broader reviews and impact planning
still reports three acceptance-chain gaps. These results are scoped local proof
only. No AWS/Docker, publication, Git checkpoint or accepted-state transition.
The governance question is closed; the public gated task/provider controller is
next, not another permission decision for local repository implementation.

Public task-controller inventory: reuse source/custody/alignment and the exact
own-stack source/resource lineage before selecting any physical task/role/group.
Add an own read-only binding checker for the actual immutable ECS revision,
container image/command/environment/secret-reference/TLS settings, task and
execution roles (trust, exact inline policies, no attached policies/boundary),
and private group rules. Resolve only the actual own templates' Ref/GetAtt/Sub
forms; unsupported source structure is a finite rejection, not an interpreter
fallback. Policy URL decoding is allowed by the documented IAM API contract;
do not fetch secret values. Preserve physical identifiers only in the existing
bounded task intent, not normalized generic facts or safe public plans.

Use actual-template controlled responses for source/task/role/network mutation
counterexamples, duplicate/malformed/missing/paginated observations and finite
context/canary exclusion. This checker proves neither effective SQL access nor
generic gates: actual preflight and the public controller still own those. The
controller will provide a single-use RunTask capability only after first-five
normal gates and exact approved-plan binding. A known guard rejection before
submission must stay distinct from a lost remote response. Bind immutable
preflight admission through the existing runner, collect real operation receipts
and automatically assemble the four activation prerequisites. Keep restoration
readers on their own restored dependency rather than borrowing source authority.
Binding failures must also name the safe selected item (execution versus task
role, or delivery/database/server ingress) without exposing physical references;
otherwise a correct policy/network mismatch would lose its useful location.

Implemented the first-five public task-planning path, not task execution yet.
Its versioned operation graph derives the selected root's entire outgoing
dependency closure from the existing runtime graph, retaining the server/database
callee for an HTTP verifier, and combines it with the real source controller,
operator and durable local intents. It does not claim unrelated not-yet-running
workloads passed live checks. The existing generic compiler validates both source
graphs and the derived graph; no generic schema or gate is bypassed. The shared
infrastructure producer now accepts explicit trusted contract/artifact bindings
and uses that contract's change-summary check ID, retaining its original default
behavior. The AWS CLI I/O method is reused behind a planning-only read allowlist;
even an inherited CF write capability cannot admit a task-planner write.

The planner checks qualified receipt/clean source, registered local proof,
actual target/own creation/resource lineage, immutable task/role/network bindings
and operator RunTask/PassRole simulation. Its output binds actual versus prepared
operation, deterministic preflight label, template/parameter/configuration/
permission/network hashes and intended database effect. It emits only first-five
normalized evidence and explicitly reports execution unavailable. Controlled
positive prerequisites are not qualification/live evidence; actual CLI negative
cases must make no provider call. Task launch, admission consumption and automatic
activation-manifest assembly remain required source work.

Caller review found that the new planner would preserve a failed local check's
finite code but drop the already checked selector-report reference. Preserve
that trusted reference at its real main reporter, reusing the existing producer,
and assert it with an actual local-check consumer failure and no provider call.

Execution connection inventory: preserve the planning-only wrapper while adding
an explicit execute wrapper/mode with exact approved-plan binding. The task
provider admits only one RunTask with the reserved token, fixed cluster,
qualified immutable definition, closed environment and exact private network.
Known guards reject before provider I/O; remote/CLI uncertainty remains
reconcile-only. Source/rule/graph and first-five observations must still match
immediately before submission. The adopted allowance applies only to the
validated no-business-write preflight request; it never manufactures gate six.

Retain immutable step packets containing the actual reservation and collector
receipt. Reobserve prerequisite tasks/logs before advancing bootstrap -> migration
-> runtime grants -> effective permissions; bind source/image/configuration/
permission/dependency/definition and ordering. A successful actual probe supplies
the sixth gate before the business task goes through the existing admission
runner. Resume observes the original reservation rather than launching again.
Automatically assemble the existing four-pair activation manifest only from those
successful actual operation packets. Recovery and original-record observation
need their declared predecessor/record context; do not admit an unimplemented
recovery or substitute a probe for a business completion. Keep incomplete edges
explicitly blocked until connected, rather than exposing an unrestricted runner.

Initial preparation execution is now connected in `task-route.py`, with
planning-only and explicit execute wrappers. `task-steps.py` builds the exact
closed request, reobserves each original reservation/receipt and supplies the
existing activation consumer's four-pair manifest. Only bootstrap, migration,
runtime grants and effective permissions are executable so far; other plans
truthfully report the execution route unavailable. The public provider grants
one exact RunTask after approved-plan matching, source/rule/graph and fresh
target/operator/prerequisite checks. A known guard rejection preserves its safe
condition/role item as not-started; submission uncertainty remains reconcile-only.
An actual successful probe supplies gate six, never IAM simulation. Both lost
probe and business launches retain their original attempts/admissions. No new
task is launched by reconciliation or automatically by a preceding completion.

Consolidated source self-review covers the whole new binding/graph/route/step
modules, wrappers, shared provider/GateBook extraction and actual consumers.
Controlled initial-route exploration passed through the real runner/collector,
generic compiler and activation consumer. Added final counterexamples cover
lost business submission, original creation reservation, single-use capability,
exact payload and the actual main reporter; the registered frozen-batch run
below remains required to qualify those final inputs. Partial review entries
retain real provider/image and feature/recovery/acceptance debt. README skill
updates name the actual commands, files, sequence, report effects and remaining
unsupported operations without claiming any AWS execution. Source is frozen
for the focused composition run; unrelated secret proof may be reused only
under its unchanged registered identity. Broader integration remains required.

The first registered attempt ended in `selection-input-or-runtime-invalid`
(`OSError`) without a retained run report; it establishes no passing receipt.
Rerun needs the normal active-worktree cache write permission, not broader AWS
authority. A final receiving-caller review also found that the existing
activation consumer loads its own evidence exception class; treating only the
task runner's separately loaded class as supported would collapse its specific
failure and source diagnostic bundles into a generic boundary fallback. The
task main reporter now preserves both actual owners' class/code/observations.
Its focused counterexample supplies the activation owner's actual exception
class and asserts exact condition/bundle/canary exclusion at `main`. No runtime
definition or operation effect changed. This reopens the affected source review
and focused receipt; it is not an AWS or dependency failure claim.

Next feature-connection inventory: require the actual activation reservation,
receipt, current exact service/image and initial four preparation packets before
admitting feature probes. Connect original create, lifecycle on the existing
separate lifecycle label, original-identifier collision and baseline original
read, preserving the original digest rather than the lifecycle entity's digest.
Each operation uses the same exact-plan/preflight/admission/one-launch protocol.
Missing activation, prerequisite, digest or immutable binding blocks execution;
unsupported recovery/cleanup operations remain unavailable.

For an uncertain create, extract the existing read-only reconciliation branch
from task-control without changing its sole-submission behavior. The observer
requires the original create reservation and actual matching terminal task/image
before its own probe or read. It may retrieve the one indexed original and
retain its ID-bound digest; it cannot create or replay the original mutation.
Absence, nonterminal/mismatched original task or failed record observation is not
permission to relaunch. Later feature steps may consume a successful create or
this explicitly bound observer receipt; neither can substitute for lifecycle,
collision or post-replacement/restore obligations. Test actual connected route
with controlled terminal/result loss, wrong original digest, missing activation
and no second create, in addition to the existing real HTTP/feature fixtures.

Receiving-caller review in this feature slice also distinguishes an implemented
route awaiting a named prerequisite from an unsupported route: plans should name
the missing preparation/activation/record proof, and execution must report that
absence before any launch. Malformed existing proof remains a rejection, not
absence. The public task and infrastructure reporters must preserve the selected
primary and related source diagnostic bundles, not merely an unordered list or
generic condition. Reuse task-evidence's actual catalogue/bundle validator for
this projection; invalid diagnostic-processing input gets a finite safe companion
without replacing the operation's condition/effect or replaying it. Extend actual
main reporters and collector fixtures, including sensitive canary rejection.

The baseline feature connection is implemented and its first controlled end-to-end
route exploration passed: activation -> original create with missing result ->
separate terminal-bound observer -> lifecycle -> collision -> original read,
with exactly one original create submission. Final receiving-caller corrections
name pending prerequisites, preserve selected primary/related diagnostic bundles
and distinguish the selected caller from an affected server callee in safe
binding context. Actual main reporters and pure collector projection fixtures
cover the latter corrections; no new runtime vocabulary was needed. Whole-source
self-review reconciled the new feature adapter, read-only reconciliation extract,
server callee binding, shared projection and their real consumers. Source-matched
partial reviews retain actual-provider and later recovery/acceptance debt.
README skill source-reviewed the new file/commands, observer sequence and limits.
This source batch is now frozen for its registered focused run. The preceding
96-second preparation receipt is historical proof of that earlier input set,
not qualification of these later feature/projection inputs. No broader suite is
needed after each edit; full selected integration remains required before the
conditional local checkpoint and any actual package/live advancement.

The expanded frozen batch passed registered composition in 186.040531 seconds,
with unchanged secret regression reused; report
`.cache/test-runs/20261108T202634Z-93c53f7041b54ee39b7beb175ccb3aaa/report.json`.
This is genuine local proof, not integration or AWS. The measured duration also
exceeds the public controller's 180-second cold local-check boundary. Inspection
found repeated parsing/validation of the same source template for task, each
role and network inside one binding inspection. Correct this in the owning
binding adapter: read one validated source snapshot per inspection and pass it
through those existing checks, without global caching or skipped predicates.
Reinspect afresh on every later call and recheck the source/rule fingerprint
after the pre-submission provider reads. Existing mutation counterexamples must
continue to fail; assert one source read per inspection. Do not relax the timeout
or disguise the advisory feedback overrun. Requalify the affected registered
unit once this bounded correction is source-reviewed and frozen.
The same inspected hot path reparses the full checked health declaration for
every prerequisite request. Carry its completion deadlines in the prepared
operation context instead, still validating every closed request and rechecking
the configuration digest before submission. This is per-operation source reuse,
not a global cache or substituted declaration. Counterexamples retain exact
deadlines and demonstrate requests consume that prepared checked context.

Emergency first-release stop inventory: implement a separate control-plane-only
route, not the healthy stop/start helper. Reuse canonical release-succession
`recovery_policy` and its existing custody lock; select initial policy and
revalidate while holding that lock across the owned execution. Missing accepted
evidence directory is not an initial-state observation: establish the canonical
source-owned evidence folder first, without creating an accepted record.

Prove the own CF stack's tagged source/parameter identity and original flushed
creation-execution reservation/event lineage, including terminal failed/partial
creation. Admit only declared resource types and actual own task-definition
references. No application-health, SQL login, healthy runtime permission/network,
or available database prerequisite is appropriate for stopping a failed scope.
Inspect actual target/operator and source database incarnation/configuration
without SQL, and preserve all other cluster service configurations. Incomplete
pagination, foreign/unknown revisions/groups, in-progress CF writers, changed
custody/source/ownership or newly appearing unplanned standalone tasks block
effects or completion, not authorise broader stopping.

The concrete plan selects only own service desired-count zero and at most 32
exact own standalone tasks; no task launch, SQL, database/role/stack mutation,
replacement, baseline change or deletion is admitted. Desired RUNNING discovery
also covers provisioning tasks; inspect desired STOPPED tasks too because
STOPPING is not terminal. Current service tasks drain through the one count-zero
request rather than requiring health. Each effect has an exclusive flushed
reservation before its sole provider call; loss or uncertainty only reconciles.
Persist the original plan/baseline/task set so partial progress cannot recompute
a different approved plan or silently adopt new work. Actual STOPPED states and
zero service counts are required for completion. Source database may be
temporarily unavailable; this control reports only its non-SQL preservation
boundary, never invents original-data or migration-history readback. Later
independent read/state evidence remains necessary for first acceptance.

Extend existing controlled composition fixtures with failed/unhealthy/no-pulled-
image tasks, zero/partial scope, queued and stopping tasks, lost service/task
responses, no second submissions, changed baseline/custody/target/source, exact
payload, original-plan resume and real offline CLI/report preservation. Validate
normal generic gates against a separate own control-plane graph, not fictional
healthy application/database components. No concrete AWS authority is granted.

The failure fixture's actual-main reporting injection initially replaced its
own provider constructor recursively. Capture the real class before injecting
the factory; this is fixture wiring, not a provider-path fix. The corrected
fixture passes 22 named local cases in 46.93 seconds, including closed payload
rejection before the guard/transport and preservation of a known provider denial
inside submission uncertainty. Its controlled source/custody/transport remain
explicit doubles, not actual-provider qualification.

Adding those 47 seconds serially to the last 125-second composition plus selector
overhead would exceed the existing 180-second operational caller deadline.
Run only the independent task-route and failure-route fixtures concurrently in
separate processes: each owns its temporary directory and in-process module
doubles; neither uses the compiled payload or shared mutable service/cache.
Wait for both and fail if either fails. No assertion, timeout, input declaration
or source check is removed; measure the frozen registered batch afterwards.

Consumer review found three newly exercised verification inputs missing from
the composition declaration: the real succession selector, its declaration
validator and this target's scope index. Add those exact inputs so changed
policy/lifecycle code invalidates local reuse. A bounded real-catalog fixture
must reject removal of each input; existing selector mechanisms still own the
fingerprint/reuse semantics. This is a verification dependency correction,
not an exemption or scope-wide source narrowing. The first 129.756037-second
parallel registered pass predates this input correction; retain it historically
and rerun the affected unit against the final declared inputs.

Replacement continuation inventory: expose the existing original-record-bound
`replace_runtime` through a narrow public plan/execute controller. Its input is
the original proof label/digest, never a caller-supplied task ARN. Reobserve the
actual baseline read and its complete preparation/activation/feature prefix via
the current task-route consumers, then select exactly one own running immutable
server task. Persist that original task/approved plan before the single StopTask;
resumption must load it rather than select the successor as another predecessor.
The existing resource reservation and exact stop reason bind actual STOPPED old
task to a distinct healthy same-image/definition successor. Hold all other own
completion jobs terminal and give the provider no RunTask/UpdateService/SQL/CF
write capability. Use normal control-plane realization gates, without widening
the observation exception or pretending replacement itself reads original data.

Actual payload/target/reason changes, missing or changed baseline read, wrong
approval, source/role/network/dependency/operator change, ambiguous current task,
known before-I/O guard rejection and lost response need distinct finite outcomes
at the public caller with canary exclusion and no second submission. The private
resource helper currently collapses `SubmissionNotStarted` into uncertainty;
preserve that existing typed distinction before connecting it. A completed
replacement receipt is not the fresh original-record read after replacement;
that later task must have a separately selected stage/attempt, original label
and digest and creation after the replacement's actual successor start. Existing
baseline read/preflight keys cannot be replayed or relabelled as later proof.

Add only the closed `baseline` and `server-replacement` task-proof stages now;
non-baseline is legal only for verifier/read, including its separately labelled
ready probe. Preserve existing baseline keys/labels. Other contexts remain
unimplemented rather than accepting arbitrary caller stages. The later stage
must validate the public replacement packet, retained approval/active-plan bytes,
original resource reservation, full matching result and retained generic gate
hash, then reobserve the actual stopped predecessor and healthy distinct same-
image successor through the existing no-replay helper. Missing journal state
must reject before that helper can reserve. Require replacement reservation
after the baseline read and the new probe/read after actual successor start.
New stage keys permit explicitly planned read-only observations, never another
create, lifecycle mutation or inherited baseline preflight. Fixture assertions
must reject premature stage execution, unchanged original create count, stage
receipt substitution and changed gate/source/configuration bytes.

Consolidated source review caught a time-order gap in the existing replacement
helper: the predecessor's stop was parsed but not bounded against the reservation,
and successor start could precede its creation. The helper now rejects an old
stop beyond the existing sixty-second clock allowance and rejects start-before-
creation. Its receiving caller keeps the exact finite condition/known effect;
the nineteen-case resource fixture rejects both on repeated observation with
exactly one original stop. The expanded connected task fixture passes in
105.22 seconds, including actual public replacement lost-response reconciliation,
fresh separately staged probe/read, old-baseline substitution, changed retained
gate bytes and exact public guard context. These controlled observations remain
local only; the frozen registered batch is still required and being collected.

The frozen replacement batch passed: composition 160.411729 seconds and total
local selection 175.110117, close to the existing 180-second caller deadline.
Actual source inspection identifies repeated validated-template parsing in
`BINDING.inspect` for the selected task, server callee and every historical
preparation/feature prerequisite within one `TASK.prepare`. Extend its existing
internal snapshot seam to that one prepared operation, passing a single checked
snapshot through the actual prefix consumers. Each later preparation and each
provider guard must read its own fresh snapshot; keep every provider comparison,
source/rule/configuration fingerprint check and closed request. Guard role
selection should reuse its one resolved checked task, not parse it twice again.
Add a counterexample asserting exactly one binding-source read per preparation
across different workloads and subsequent unchanged preparations (not one global
read), while the existing role/network mutation guards still reject changes.

Initial-stop preservation continuation inventory: the stop receipt explicitly
does not read original data or migration history. Connect a separately planned,
approved, single own-service count-one start through the existing resource
`start-runtime` journal, then a distinct original-record read and administrative
`observe-migration-state` that requires APPLIED_CONFIRMED, not replay-permitted.
Do not reuse `restore-read` against the source and falsely call it restored data.
This proves preservation after recovery, not a fictional successful SQL read
while the service was stopped. No new schema, role grant, database reversal,
record create or runtime task command is needed.

Before start, revalidate the real initial policy under the actual succession
lock, the original stop root/receipt and unchanged gate bytes, original terminal
tasks/zero counts, current own source/definition/role/network/dependency bindings
and all other service configurations. Bind the historical actual server-
replacement read (original label/digest, own reservation/admission/task/log)
before the stop reservation. Read that completed task packet through the existing
collector consumer without requiring the stopped application to be healthy.
Do not call the ordinary activation consumer as a prerequisite to starting a
zero-count service. Source inspection/owned-stack/binding helpers can provide
that context without fabricating health or granting the operator RunTask merely
to change desired count.

The exact parent plan must allow only one own UpdateService count-one payload,
with its flushed existing start-runtime reservation, source/policy/operator/
ownership guards and normal control-plane gates. Missing/changed stop proof,
wrong label/digest, active unknown work, another service change, missing accepted
custody observation, inherited write capability, wrong approval/payload and lost
response must remain distinct finite safe outcomes. An existing reservation only
reconciles. Completion requires one actual healthy qualified server created after
the start reservation, with correctly ordered start time. Its receipt must still
say original-data and history readback have not yet occurred.

The later closed initial-recovery task stage may admit only verifier/read and
administration/observe-migration-state, with separately selected probe keys and
real fresh admissions. Keep the original record label/digest in plan metadata;
do not pass the digest as an undeclared administrator environment override.
Read must follow the actual recovered server; history observation must follow
that read and require the manifest-matching applied result. All selected jobs
finish before later cleanup/acceptance. A later intentional stop/replacement
does not mean an earlier completed proof's server must still be current: retain
historical identity/time evidence separately from a fresh-current-state claim.
Do not restamp historical task receipts or launch unknown operations again.

For independent fixture speed, reuse controlled prerequisite producers or a
guarded importable fixture rather than executing the entire public baseline
chain again inside another fixture. Use actual source-owned reservation,
admission and evidence validators at the new consumer; mark source/custody/
transport doubles explicitly and never write them into canonical acceptance.
Existing restore `validate_reader` already requires the clone's distinct actual
incarnation; the future public reader request, not that correct predicate,
needs the appropriate clone binding.

For this next test consumer, make `task-route-test.py` importable by wrapping its
existing executed cases in `run()` plus the ordinary main guard; keep its provider
fixture and module definitions importable. This is a mechanical test-only change
so the initial-recovery fixture can reuse its actual controlled task/log producer
without rerunning all baseline cases on import or copying their protocol. The
registered wrapper must still execute every existing case directly. No test,
assertion, provider boundary, source-read witness or selection input is removed.

Cold-start predicate found in the actual start/replacement helper: desired-RUNNING
discovery can return a provisioning/pending/activating successor whose pulled
image digest is not available yet. The existing strict runtime `task` check is
appropriate for the original running server but currently rejects that successor
before the caller can return pending. Add an internal, explicit starting-task
mode only for successor/start observation: keep exact ARN/definition/group/
container/Fargate checks; allow an absent digest only in those three startup
states; a present wrong digest still rejects. Completion still requires actual
RUNNING/HEALTHY with the correct digest and valid times. Preserve the existing
typed before-submit rejection for count control as well. Actual low-level
counterexamples must show repeated pending observations do not submit another
stop/update, followed by real matching running completion; default strict
inspection and wrong-image rejection stay enforced. No launch, health assertion
or automatic retry is added.

Implement this slice through `recovery-state.py` (shared historical stop/read
validation), `restart-route.py` plus `restart.sh` (public bounded count-one
control), and the existing task route's closed `initial-recovery` stage for
verifier/read and administration/observe-migration-state. Extract only static
scope binding checks from failure-control.verify_current; its original actor-set
guard remains intact. Reuse failure policy/lock/artifact with an optional common
owner argument rather than duplicating custody logic. Defaults remain unchanged.
New failures distinguish absent/changed stop custody, original read/time/digest,
wrong source/dependency/role/network, active unplanned work, nonzero precondition,
wrong approval/payload, missing journal, pending/uncertain effect and changed
retained gates. The public reporter preserves finite reasons and selected actual
task diagnostic bundles; native causes remain outside output. No restart receipt
alone claims data/history preservation. Prove the new real callers with shared
controlled source/task producers, historical evidence before stop, missing/altered
prerequisites, lost response, pending restart, unknown-job rejection, exact
before-I/O guard identity, original read followed by applied-history observation,
and unchanged baseline service configurations. Make the failure fixture importable
without executing its complete cases; the registered wrapper still executes them.

The restart's current service observation must also compare its actual Fargate
launch and private awsvpc settings with the checked server binding: exact selected
subnets, sole own server group and disabled public IP. A matching source template
and unchanged captured service configuration alone are not this comparison.
Missing/wrong service network emits the finite recovery-runtime-network condition
before any count-one effect; the controlled fixture supplies actual service shape
and exercises an already-drifted original network, not only drift after planning.

The connected pre-stop-read fixture exposed a real precision bug: failure
reservations and stopped observations use the common seconds-only clock, while
task receipts retain fractional time. A read completed before stop in the same
second can therefore appear later than its reservation. Use precise UTC time
for these new stop journal/observation writes, consistent with the resource/task
journals. Retained old timestamps remain readable. Do not backdate test receipts
or add clock-skew tolerance to permit a genuinely post-stop read. Prove actual
fractional producer ordering and the deliberately reversed counterexample.

Initial-recovery predicate/consumer review for the stable batch:

| Boundary | Observed alternatives and owner | Actual consumer/assertion |
| --- | --- | --- |
| Stop custody | absent root/receipt, malformed intent, changed policy/source/gate bytes or original terminal tasks; existing stop/state finite conditions | restart prepare and later stage use the actual stores and terminal task consumer; missing receipt and changed gate cases prevent count-one/RunTask |
| Original read | absent, wrong request/digest, genuinely after stop, or copied into the later stage | source-owned collector/admission/step read; precise-clock producer and late/copy counterexamples preserve strict ordering |
| Current runtime binding | missing service, changed source incarnation/role/network, including original public-IP drift versus source | checked server task/role/SG bindings plus actual service Fargate/subnet/group/public-IP observation before restart; bad original networking and changed baseline block |
| Count-one effect | wrong approval/payload/bool count/other service/inherited capability, typed pre-I/O denial, lost response or pending unpulled task | actual public provider, resource journal/helper and main reporter; sole reserved update under actual custody flock, no replay on resume |
| Recovery observation admission | missing restart journal/gate, unknown active job versus the exact reserved running task, stale preflight or old read | actual task route/runner/generic gates retain separately selected stage keys, fresh admission and creation floor; running task reconciles without a new launch |
| Migration-history completion | applied-confirmed versus replay-permitted or actual task failure | admin digest remains metadata; only applied-confirmed is retained as successful stage proof; real main condition/effect and no second launch are asserted |
| Evidence/reporting | unchanged historical receipt versus current task claim, malformed data/native failure and selected task diagnostics | no restamping; existing collector projection reused; safe finite conditions/canaries and fallback debt remain explicit in partial reviews |

All source/custody/alignment/task/transport doubles stay labelled local protocols.
The new fixture is registered in the existing composition unit, independent of
the other two controller processes. Every process must finish successfully;
no existing case or timeout is removed. Complete source/README reading review
precedes the final registered batch; earlier direct runs are editing feedback.

The first registered initial-recovery batch passed (composition 76.787955 seconds,
selection 92.283999). Subsequent caller review found supported item loss: reused
stop binding/terminal/operator failures retain a finite `item`, but the new
restart reporter and recovery task guard/main mapping handled only task-binding
and ordinary prerequisite items. Preserve those existing bounded items at both
actual callers, including through typed pre-I/O rejection; do not invent a new
definition. Extend the controlled old-server revision counterexample through
the real restart main and the task guard/main mapping, asserting code/item,
not-started effect, safe output and no provider replay. Reopen this batch's source
review and registered proof after that correction; the passing report remains
historical if its inputs change.

### Approved bounded expected-unready observation

#### Isolated clone, reader and cleanup connections

Connect the existing restore-control/template through restore-route.py/restore.sh
and a separate restore-reader-route.py/restore-reader.sh, consuming the actual
snapshot receipt and completed credential history. Retain the existing single
attempts directory and resource helper; do not build another scheduler or grant
execution authority. Clone parameters derive only from fresh target alignment,
the exact completed source snapshot and qualified source/image, not caller
endpoint/role/database overrides. Plan/review/execute are separate; review itself
creates a change set. Require its exact eight-resource CREATE-only source body,
parameters, named owned stack and retained execution/event lineage. Reconcile
original review/execution after interruption without another submission.

Use restore-binding.py to expand only the clone's positively observed endpoint/
resource-ID attributes in its checked template. Reuse the existing task/role/
network comparator with explicit internal prefix selection; do not widen the
main-workload inventory or pretend the clone uses the source identity. Check
clone subnet/VPC, sole own database security group, exact inbound reader rule,
private/encrypted/IAM posture and different incarnation. Verify actual reader
task/container, both roles/inline inventories and closed private egress against
source, including no source database IAM reference, credentials or extra command.
The child request uses the clone's incarnation and permission-template hash;
the parent plan continues to bind source scope/permission lineage separately.

The reader has only preflight then restore-read. Its exact bounded preflight is
already eligible under the approved observation rule; no new ordering exception
is needed. Actual SQL identity/TLS/read-only observation supplies gate six for
the separately approved read. Use the existing runner/admission/collector/step/
completion protocols and a selected graph retaining the actual restored-store
dependency. Require task creation after completed clone observation and original
ID/facts digest equality. Preserve uncertain/pending attempts and original
admission; a running original reader may reconcile, unrelated active jobs cannot.
Current snapshot callers retain their terminal-job default. Do not replay a
completed reader just because its terminal AWS observation expires.

Cleanup requires the actual captured read and its immutable final gate before
one separately approved DeleteStack. Verify positive original clone incarnation,
template/resources/tags and stopped jobs, never delete source database/snapshot,
and retain actual absence/inactive-definition evidence. After a cleanup
reservation exists, reconcile its original identities without demanding a deleted
database/role to exist again. A previously captured read may be used historically
only with its original protocol/gate custody, not a new readiness assertion.
Do not claim restoration or cleanup from helpers alone. Failed/partial clone
cleanup needs its own explicit positively owned failure branch, not successful
reader fabrication or unconstrained deletion; final acceptance remains blocked
until all required successful proofs and final current verification exist.

Bounded diagnostic/consumer inventory: missing/changed source snapshot/history,
review/execute plan/receipt/journal/gate; wrong clone template/physical database/
incarnation/network/role/task; missing/stale/mismatched preflight versus original
admission; bad digest/terminal reader code versus actual successful source result;
known pre-I/O rejection versus remote uncertainty; missing ownership/receipt or
incomplete absence versus confirmed cleanup. Reuse existing finite resource,
binding, task/evidence and compiler failures and preserve code/item/field/effect
at actual reporters with no raw provider/credential/endpoint output or replay.
Any required additive receipt field needs its reader before new emission; retain
existing helper defaults and historical bytes. Partial reviews must name genuine
unproved provider/concurrency/processing boundaries, not waive live acceptance.

Extend the existing connected fixture with controlled actual-template clone
responses and actual public routes, runner/collector/compiler/store consumers.
Reuse/import the restore helper fixture without executing its seventeen cases
on import; all direct cases still run. Keep task IDs monotonic after simulated
expiry rather than reusing an old ARN. Prove separate clone preflight/read,
source-host/IAM/network rejection, original digest, lost review/execute/read/
cleanup without repeat effects, owned cleanup/absence and unchanged baselines.
No controlled fixture is image, PostgreSQL or AWS qualification. Final local
checks remain the registered composition/related units; broad integration,
conditional source checkpoint and concrete AWS approval remain required.

Exploratory connected execution reached real controller/runner/collector local
protocol success for clone review/execution and restored original-record read,
including lost review, execution, preflight and reader responses without replay.
Source host/IAM/network counterexamples and actual reader reporter assertions
also passed before cleanup. Two fixture defects were corrected without weakening
runtime guards: cloned standalone security-group IDs originally collided with
the source fixture, and lost-response modelling updated a remote endpoint rule
only on a returned success instead of whenever the remote effect occurred.

Cleanup is currently blocked by a genuine generic harness conflict, not a
provider or database result. `operational-realization-gate/script.py`'s
`validate_change_shape` requires delete, replace and broaden-permission to all
remain forbidden. The own disposable-clone cleanup graph therefore rejects
`change-shape-invalid` before any deletion or AWS call. Do not relabel deletion
as create/update, bypass the compiler or fabricate cleanup proof. Asked the user
whether to add a narrowly explicit owned-isolated-cleanup rule, retaining default
deletion prohibition, mandatory captured original read/gate/ownership, source
database/snapshot protection and separate concrete AWS approval. The generic
compiler/rule has not been changed pending that decision. No new registered
pass is claimed for the incomplete source batch; previous reports are historical
for changed inputs. Source-matched reviews, README coverage and frozen final
checks remain open until the required cleanup connection can be completed.

#### Approved bounded disposable-restore cleanup — 2026-11-09

The user approved the rule change only: positively owned `entity-smoke` restore
resources may be deleted after their original successful readback and ownership
checks, with separate concrete execution approval. Source database, snapshot,
baselines and staging remain protected. No AWS execution authority follows.

Before editing, the consumer/predicate inventory is: generic compiler
`validate_change_shape`, v2 schema/guide and realization standard/workflow;
provider applicability; restore graph producer, prepare/guard, original reader,
resource cleanup and read-only acceptance consumer; actual compiler CLI fixture
and connected credential/restore fixture. Keep v1 admission and ordinary v2
delete prohibition unchanged. Introduce a v2-only exact opt-in declaration for
disposable-restore cleanup, permitting delete alone while forbidding create,
update, replace and broaden-permission. Missing, null, malformed, incomplete,
false or additional declaration fields must reject with existing safe
`change-shape-invalid`; normalized counts, evidence hashes and all gates remain
required. Declaration is not proof or provider authority.

Actual controller assertions must reject absent/altered original successful
reader custody, changed ownership/tags/resources/incarnation and wrong approved
plan before DeleteStack, retain source/other-service/snapshot protection and
reconcile one lost deletion response without resubmission. Existing finite
restore/binding/compiler reasons and safe reporter context remain the owners;
no provider payloads, endpoints or reader data enter diagnostics. The read-only
acceptance reader must validate original gated cleanup and absence without
enabling deletion. Extend existing fixtures, not a new permission registry.
Registered realization and entity-smoke composition checks are final local
proof; package/PostgreSQL/live proof remains distinct and pending.

Consolidated self-review closed the bounded rule/compiler/graph/caller/docs
changes and found two old acceptance fixture assertions still expecting the
unapproved cleanup rejection. Replaced them with positive seventh-control
archive coverage and retained default deletion rejection by removing the opt-in.
No production gate/approval was bypassed. The actual connected fixture now passes
clone/read/cleanup plus distinct final probe/read, rejecting missing cleanup
before a final launch, preserving the original digest and post-cleanup ordering,
and reconciling lost cleanup/final responses with one submission each. Compiler
CLI has93 cases, including all malformed opt-in fields and forbidden counts;
registered realization regression passed. Acceptance archive fixture passes all
seven selections and original tampering cases. Direct protocol fixtures remain
controlled source/custody/provider observations, not real engine or AWS proof.
README skill review corrected only the obsolete cleanup/status explanations,
checked both guides against actual callers and verified their relative links.
Source-matched reviews remain PARTIAL with actual processing/live/collector debt.
After metadata/whitespace and exact selector preparation, freeze affected inputs
for registered composition/acceptance-control/diagnostic verification. No
conditional checkpoint, image, AWS/publication or accepted-state write yet.

The frozen registered four-check batch PASSED: realization regression,
entity-smoke composition, acceptance controls and diagnostic adoption; retained
report `.cache/test-runs/20261109T081333Z-08dc4aca373a43a8bf8fdc464bcbbed2/report.json`.
Full754-path local integration planning separately found exactly one uncovered
input: the existing `.gitignore` addition for the entity-smoke succession lock.
Before its correction, inventory the actual Git consumer and release-succession
fixture/catalog binding: prove that only the exact own lock is ignored, while
candidate/current/history/proof evidence, other scope locks and lookalike names
are not hidden. Bind the consumed ignore file and Git runtime to the existing
release-succession regression; no runner/cache algorithm or production rule
change is needed. Use an isolated disposable Git repository with the actual
ignore file and a removed-entry counterexample. No operational diagnostic
contract changes: this is verification support and closes a selection gap, not
cleanup/provider authority. Then reopen affected preparation and reuse only
matching registered proof when completing integration.

Preparation follow-on: the complete754-path plan is now PLANNED/no findings
after adding the missing `.gitignore` repository_inputs mapping as well as the
fingerprint input. The actual Git fixture also asserts that mapping and binds
its consumed catalog. Owning registered regression PASSED7.9239s. Canonical
lifecycle preparation accepts existing file paths; the initial all-path request
included deleted tests and failed before applying. The supported existing-file
batch588 applied and structurally validated249 artifacts; all deleted paths
remain in the separate full impact selection. Its process-drift gate then
reported four pre-existing prose lines in the time/UUID migration plans, testing
README and diagnostic workflow. Before-commit rules require human disposition;
requested approval for bounded explanatory history/human-guidance annotations,
without changing requirements or execution permission. No broad verification or
checkpoint may bypass that gate.

Lifecycle stamping made57 review hashes stale. Independently reconstructed each
prior reviewed source by replacing only its single updated_on date and required
exact SHA-256 equality with the retained review. All57 matched; none needed a
body/contract/diagnostic change. Refresh only those date-only source hashes,
retaining all existing statuses, reason assertions and remaining debt. This is
mechanical reviewed-source equivalence, not expanded semantic/live adoption.
Earlier check receipts remain historical until matching-input revalidation.

#### Independent delivery census correction — 2026-11-09

The actual full inventory rejected nine implemented task/recovery wrappers as
delivery-consumer-unbound; its29 isolated CLI regressions passed. Directory
impact inputs do not register commands. Add the nine exact wrappers to this
scope's existing requirement.required_by list, retaining the same proof owners,
candidate state and execution permissions. Extend the existing composition
template fixture to assert each required operational wrapper is explicitly
bound, with a missing-wrapper counterexample for every selection. These are
declaration/test corrections, not runtime or diagnostic-vocabulary changes;
the existing inventory diagnostic remains accurate. Baselines remain untouched.
Prove the real full census covered after correction, then rerun affected
registered composition/inventory checks and complete full impact selection.
The prior original run was interrupted by environment turnover: its process
and temporary outputs are absent, but53 successful new Git-metadata receipts
remain. Do not fabricate a complete report or discard matching receipts.

Consolidated self-review: the nine new required_by entries match existing
wrappers and the fixture reads the actual owning scope. Each single omission
fails even with the directory impact declaration retained. Existing template,
role, environment, source and restore assertions remain unchanged. Exploratory
template proof passed; the real full census is now covered:499 entrypoints,
six routes, zero findings. No permissions, executable runtime behaviour,
diagnostic contracts or review hashes changed. Freeze these inputs for focused
registered proof and resumed full integration. Store safe command output below
the existing ignored test-run root, not only ephemeral /tmp; only the original
runner's matching private receipts can qualify reuse.

#### Resumed completion and documentation disposition — 2026-11-09

The user directed completion after reviewing why the four prose findings
blocked the goal. Resolve those exact findings with explanatory allow markers:
historical rename results, UUID review judgement, test-guidance ownership and
diagnostic evidence-reuse guidance. Preserve every existing requirement and
permission boundary. These comment-only edits introduce no runtime predicates,
diagnostic vocabulary, test waiver or AWS authority. The README skill review is
limited to its ownership explanation; no links or described behaviour change.
Canonical preparation passed all249 metadata headers and the process-prose
check, then exposed one documentation command missing the existing governed
runner prefix. Correct only that read-only select-recovery example to use its
required wrapper; arguments, selection, authority and runtime code are unchanged.
The wrapper already owns this enforcement, so no new rule or approval is needed.
Then complete canonical preparation and impact-selected local verification,
reuse only matching evidence, create the already-approved local checkpoint and
continue actual package qualification. Concrete publication/provider execution
approval remains separate. No general gate weakening or new framework is needed.

#### Connected original receipt-to-archive handoff — 2026-11-09

While the four process-prose dispositions await approval, independently verify
the required acceptance handoff using the actual receipts now produced by the
connected restore/final-task fixture. Existing control/archive fixtures use
constructed plans; the original connected fixture has not yet called
acceptance-evidence.capture_task and acceptance-route.control_proof on its exact
stored restore-reader/final-read and snapshot/restore/cleanup completions.
Extend that same fixture with the real capture and historical validators,
sharing only its explicitly controlled source/custody/provider dependencies.
No successful primitive validator, cleanup or archive may be stubbed.

Consumer/predicate inventory: original step/receipt/admission/completion/gate
paths and SHA-256; distinct parent versus restored incarnation/permission;
selected phase/stage/name and original digest; original control plan/reservation,
graph and seven-gate/change-count custody; missing/altered completion or gate
must reject before any task/deletion. Reuse existing task-completion, archive
and control finite conditions. Assert preserved original bytes, seven gates,
truthful delete8, separate reader/final identities, no additional effect and
safe canaries. Fixture-only changes do not add operational diagnostics or
permissions. Planned exploratory connected proof is not full19-task aggregation,
real qualification, provider proof, new accepted state or a preparation waiver.

Consolidated self-review: only the existing connected fixture changed, adding
actual archiver/custody calls with no successful-validator doubles. Production
sources, contracts, operations, runtime outcomes and diagnostic vocabulary remain
unchanged. The exploratory connected credential/restore fixture PASSED after
both positive handoffs and four original-custody corruption cases. Each mutated
temporary completion/gate byte is restored in finally; final good capture passes
again. Exact SHA-256 over stored original step bytes, four task phases, three
control archives, separate clone/source identity, truthful delete8 and unchanged
two final tasks/one cleanup submission are asserted. Existing restore negatives,
source canary checks and all credential cases still run. Headers, whitespace and
this plan's process-drift check pass. Added the actual fixture/driver to the
existing PARTIAL archive review's proving-test references; no source hashes or
remaining live/processing/full-collection requirements are waived. Prepare this
bounded slice and use registered composition for focused final proof while the
separate full-project four-prose-line disposition remains outstanding.

#### Historical custody before the long restore operation

The completed credential route still reobserves old stopped tasks at every
predecessor read. RDS snapshot/restore can outlast ECS retention, and the old
stop context also treats a newly owned clone as a change to its earlier scope.
Do not interpret expired tasks as successful observations, replay old work or
relax emergency-stop ownership. Instead, after the actual final credential
permission operation and its completion sidecar, retain one immutable bounded
`credential-history.json` packet in the existing private proof-label cache.
Bind its final safe plan, exact prerequisite packets, original record digest,
source/image/contracts/incarnation, and byte hashes of their existing journals,
receipts, admissions, plans and referenced final gates. No current readiness or
acceptance is granted by that packet. Missing, changed, omitted, unsafe-path or
incomplete retained dependencies block it. Existing source-owned receipt and
completion readers remain authoritative for historical protocol validation.

Add an explicit historical-only option to the existing task-step reader, with
its existing default still remotely reobserving the selected task/logs. The new
history reader alone selects retained evidence after validating the complete
closure; an observation failure must never trigger this mode automatically.
Current workload identity/role/network and the new snapshot's source database
incarnation remain independently reobserved through fresh ordinary alignment.
Keep incomplete/lost old attempts on their original reconciliation paths.

Consumers are the final credential task writer, history reader and the new
public snapshot/restore resource controller. Begin that controller with an exact
original-record-bound snapshot plan/execute phase using the existing resource
helper, one flushed reservation, exact operator/plan/source/dependency guards
and actual generic control-plane gates. It must positively observe absence,
reserve at/after original commit observation and retain actual terminal snapshot
facts. No task launch, SQL, source deletion, baseline mutation or acceptance is
admitted. Reconciliation observes only the original snapshot. Subsequent clone
review/execution/reader/cleanup remain required; this phase is not restore proof.

Own new files are recovery-history.py, snapshot-route.py and its public wrapper;
affected callers are task route/steps and the existing connected credential
fixture. Predicate inventory: absent/corrupt/changed history closure versus valid
historical bytes; missing/wrong final credential step/plan/sidecar; unchanged
source/image/contract/record versus mismatch; current operator policy denial,
dependency/source drift or active foreign job; preexisting/mismatched snapshot,
reserved-before-observation or lost/pending/terminal result. Reuse finite task,
resource, binding and gate conditions with bounded context; preserve native
canaries and known/uncertain effects at the real reporter. Tests must distinguish
retained history from current readiness, reject deletion/tampering before effects,
and assert one snapshot submission after loss, unchanged baseline services and
no replay of credential tasks. Register through the existing composition check.

Exploratory snapshot wiring correctly rejected the shared emergency-stop
fixture's intentionally rebooting source database before submission. Preserve
that source-helper predicate and its exact rejection assertion. The credential
fixture must explicitly model recovered `available` database state before its
successful snapshot branch; do not weaken the producer used by unhealthy-stop
tests or treat mocked alignment as actual database availability proof.

Consolidated parent self-review for the history/snapshot source batch is
complete. Reviewed both new full modules/wrapper, changed task-step/route
consumers, the resource snapshot helper and typed pre-I/O propagation, actual
compiler/receipt/admission/store readers, connected fixture and README against
this inventory. Historical mode defaults off and cannot omit completion; history
validates its candidate before writing, then revalidates retained immutable bytes.
Required per-step journals/receipts/admissions/final gates and restart/replacement
roots cannot be omitted. New clone/snapshot work does not rerun the old failure
scope observer or automatically relaunch expired tasks. Snapshot planning and
every actual guard still make fresh own target/runtime/role/network observations;
reusing its local source proof is limited to the same checked digest and actual
clean qualified source checkpoint. No generic gate, operation bound, source
availability predicate or existing case was removed.

The connected assertions reject unsafe/omitted/changed history, preserve failure
at the real snapshot main, reject a denied operator/rebooting source, preserve
typed guard rejection before I/O and reconcile its consumed attempt without
submission. The lost snapshot branch must create once, reconcile, retain actual
terminal facts/gate bytes and leave original credential tasks/baselines unchanged
even after controlled old tasks/logs disappear. These source-reviewed assertions
are not AWS evidence. Final current-source registered composition remains pending
until executed on frozen inputs; broader acceptance/integration gaps remain.
README skill scopes the walkthrough to real history/snapshot commands and marks
isolated clone/read/cleanup and acceptance as not yet connected.

#### Retained task completion boundary

Caller review found a narrow interruption gap in the existing task route: its
immutable collected step is written before the seventh gate, and later step
readers currently accept that packet without an exact retained completion-gate
reference. A crash or rejected gate in that interval must not advance recovery.
Keep the existing step/runner/admission protocols and add a completion sidecar
beside each step, written only after actual gate-seven validation. The ordinary
predecessor reader must require its exact step hash, plan hash, source/artifact
bindings and unchanged owned gate bytes. Only the currently completing step may
be reobserved before its sidecar exists. Reconciliation may finish that original
reserved task, never relaunch it. Existing completed sidecars are immutable;
historical gate facts retain their original timestamps and are not fresh current
readiness. Do not change the generic compiler or waive its current-state gates.

Own task-completion helper/step/route consumers and the shared fixture producer
are the bounded inventory. Missing completion, wrong step/plan/contract/graph,
changed gate bytes and wrong artifact bindings fail with finite task-owned
conditions, before dependent effects. Test the actual crash interval, blocked
next-step plan, original-task reconciliation and unchanged launch count. Seeded
historical fixture steps must use the real compiler, explicitly controlled
source/custody/transport protocols, not manually asserted AWS evidence. Final
acceptance still needs its separate collector and real live observations.

#### Connecting the credential-recovery sequence

Consolidated parent self-review for this local source batch is complete. Read
the full credential/completion/recovery helpers, task/graph/step consumers,
replacement route/provider/resource phase, actual runner/admission/collector,
shared fixture producers and execution README against this inventory. Closed
the collected-result/final-gate interruption gap through the existing step
reader and a sidecar, without changing the generic compiler or the v1 collected
receipt. The old receipt remains readable but cannot admit a dependent task
without its actual completion linkage. The currently completing caller alone
can reobserve its original result before that linkage is emitted. Partial source
reviews name retained remote-task/clock/concurrency and live qualification limits;
no changed source is promoted to universally adopted.

Reviewed counterexamples map to the actual fixture assertions: missing/copied
revocation and premature restore cannot expose an executable plan; a healthy
code fails the actual negative reporter; loss reconciles exactly one negative
launch and original stop; baseline replacement/old ready cannot admit recovered
read; missing replacement journal cannot invoke its helper; a final-gate
interruption blocks the next step and resumes the original task without launch;
changed gate bytes, graph identity or artifact binding fail its predecessor
reader. Existing runner cases retain closed request/deadline/alternate-key
assertions. The full registered batch remains pending until executed on these
frozen inputs; earlier direct passes are editing feedback only. README skill
review keeps command examples offline, identifies each added file/consumer and
does not describe local protocol success as package/PostgreSQL/AWS acceptance.

The first registered completion/credential batch failed in the existing restart
ordering fixture: it deliberately rewrites a controlled collected read to be
after the stop, but had not updated the new sidecar's step hash. The new custody
guard correctly rejected `task-step-completion-binding-mismatch` before reaching
the intended `recovery-original-read-not-before-stop` predicate. Keep that
original timing assertion intact; update only the synthetic fixture's linkage
hash so it still isolates the late-read rule. Separate connected tests already
reject changed gate bytes/contract/artifact and the missing completion interval.
No runtime predicate or retained real proof is relaxed or rewritten. Reopen
fixture review and registered verification for this correction.

Implement the approved negative observation through the existing task and
replacement routes, not a new scheduler or privilege-repair API. Add the closed
`credential-recovery` task stage for administration observe-permissions, revoke-
runtime and restore-runtime; verifier unready/read; and the post-recovery
database-proof permissions operation. Required order is initial preserved read/
applied-history -> bounded permission observation -> revoke -> one unready
observation -> restore -> one separately approved runtime replacement -> new
ready/read -> fresh effective-permission proof. Every ordinary operation retains
its own actual preflight and exact approval. Unready has no separate preflight
phase, uses the existing ninety-second negative admission and cannot admit
ordinary feature work. No AWS execution authority is added.

Extract historical initial-restart/read/history validation from its current-task
requirement so later owned replacement does not falsely invalidate completed
past evidence. Keep the existing initial-recovery caller's current-server and
active-job requirements intact. The new credential helper must validate real
stored requests, admissions, task/log results, source/image/contracts, exact
stage identities and predecessor times. Missing/changed evidence is never
absence permitting another launch. Before replacement require the same qualified
server that was deliberately revoked; afterwards require the original reserved
credential-replacement receipt and actual qualified successor.

Derive a distinct expected-denial graph retaining every reachable verifier/
server/database component, but declaring the expected revoked runtime access and
observation-only semantics. Its sixth-gate result means this specific negative
observation completed, not healthy database access. Launch only after first five;
record its source-owned terminal result before that negative gate/completion.
Keep normal graph/admission semantics unchanged and require a new successful
ready probe after restoration/replacement. Scope graph identity and receipt paths
so baseline proof cannot substitute. Credential permissions must not regenerate
the original activation manifest.

Reuse the resource helper's existing credential-replacement phase via the public
replacement route with closed baseline/credential selection, independently
retained plan/journal/receipt and original target across interruption. No extra
RunTask permission is needed merely to plan/perform the replacement. The helper
must never select its successor for another stop. Preserve supported conditions,
bounded item context and task diagnostic bundles at actual public reporters.

Extend the shared controlled fixture through real task/replacement/gate/runner/
collector consumers: exact sequence, premature or copied evidence, missing
revocation, wrong negative outcome, ninety-second/closed overrides, one launch
after loss, separate fresh ready/read, no second original stop, permission proof
without activation rewrite, and unchanged baseline configurations. Label source,
custody, alignment, task and transport doubles; local success is not AWS proof.
Own changes are credential-steps.py, task graph/route/steps, recovery-step
historical helpers, and the existing replacement route; use the existing
composition check/review ledger and execution README.

The user approved extending the existing observation allowance solely for the
declared credential-revocation recovery proof. This is governance/implementation
authority, not AWS execution permission. Retain the first five actual gates,
concrete approval, one flushed launch reservation, ninety-second bound, exact
source/image/task/network bindings and real terminal evidence. Expected-unready
is not healthy database access and cannot admit ordinary feature operations;
a separate successful ready observation after restoration remains mandatory.

Implement the negative admission in a separate `unready-control.py`, reusing
the existing task/evidence/storage owners. Its actual runner consumer must
validate a collector-backed administration/revoke-runtime reservation and
receipt with the selected proof label and matching source/image/configuration/
permission/dependency. Reject absent/malformed/wrong-operation/wrong-binding
evidence before reservation/provider effects. Retain the exact negative admission
before submission; a missing/changed admission blocks reconciliation. Its time
floor is the revocation task's actual terminal time; no constructed success,
boolean attestation or raw provider error is accepted. Preserve the ordinary
ready-only admission predicate unchanged. Fix the unready attempt key per mode/
label so another caller key cannot repeat an uncertain launch. The runner must
reject recovery context on any other operation and preserve finite validation
conditions, original evidence failures and no-replay behavior at its caller.

Extend the existing runner fixture with real collector-produced synthetic
revocation and unready results, bounded/closed-request failures, binding and
ordering counterexamples, missing/tampered admission, lost-response reconcile,
alternate-key no-replay, and attempted use of unready as business readiness.
Fixtures remain explicitly controlled protocols, not AWS or database proof.
The current public task route remains closed until real revoke/recovery
predecessors and truthful operation-specific gate semantics are connected; do
not stamp its ordinary healthy-database graph passed using expected denial.

### Profile-backed parser cost correction

The completed unchanged-runtime registered batch passed but took 242.233243
seconds for composition (273.423866 total). A disposable direct cProfile run of
the complete task fixture passed and recorded 1,626 YAML parses consuming
237.978 seconds of 247.656 measured seconds. This establishes parser cost,
not that the new unready helper caused the increase. Keep fresh source/provider
reads and every gate/assertion; do not introduce stale source snapshots, relax
predicates or raise the timeout.

The existing shared CloudFormation normalizer owns tag expansion, duplicate/
string-key checks, JSON-safe values, scalar-type distinction and finite invalid-
body failures. Prefer PyYAML's existing compiled safe loader when available,
with the same custom constructors and pure-Python safe fallback. There is no
new dependency or cache. Extend the existing bootstrap deployment CLI regression
to compare both actual loader paths against accepted/rejected examples and real
entity/bootstrap/restore templates. Include fallback loading, finite failures,
intrinsics, ambiguous/recursive/nonfinite input and unchanged typed comparison.
Actual consumers are bootstrap deployment, staging release reconciliation and
this scope's deployment/restore controls; their impact-selected registered local
proof remains required. No accepted baseline, infrastructure or package is
mutated. Record source-matched review and actual post-correction timing.

### Latest continuation: source chain and actual target inspection

The full-proof goal remains active and acceptance remains unfinished. This
snapshot supersedes earlier statements below about absent scope files, no AWS
reads, four task programs, PostgreSQL 16 qualification and the earlier fixture
counts. None of the following is release acceptance.

- Added candidate scope and binding for six distinct workloads, without changing
  either accepted baseline's state or ownership. Health/recovery and persistence
  diagnostic mapping validators pass. Complete acceptance/controller connections
  are still required; their absence correctly blocks package advancement.
- Added the own ECR/publication-role template, protected-main workflow, immutable
  pre-push reservation, single-push/reconcile control and pipeline/access sources.
  There has been no publication, Git checkpoint, push or provider mutation.
- Added durable task evidence/runner controls, source-exported cross-language
  diagnostic catalogues and generated exports. Historical task reuse does not
  claim fresh state; missing observations never authorize another mutation.
- Read-only `kanbien-dev`, account 337159794548, eu-west-1 inspection confirmed
  the existing foundation UPDATE_COMPLETE, private delivery endpoints including
  Secrets Manager, and PostgreSQL **18.3** with IAM authentication. Administrator
  delivery uses the existing target-owned secret, not RDS-managed MasterUserSecret.
  No secret value was read. Qualification now selects 18.3 with exact server
  version checking and the official image's versioned data-volume layout.
- The new read-only alignment command requires actual qualified custody and a
  matching clean checkpoint, then observes private namespace/VPC, delivery,
  dependency incarnation/TLS/IAM, immutable image/scan and target budget. Its
  twenty controlled negative cases pass; no qualified-image/live route result
  has been generated. Raw provider dictionaries and endpoints are not receipts.
- Removed database defaults from the common image so the HTTP-only verifier
  receives no inherited SQL setting. Added parsed delivery-pattern tests after
  finding over-escaped restore-template dots. Static proof now passes nine main
  and ten restore negatives, graph/configuration/environment counterexamples.
- Finished-image qualification source now also checks already-applied migration
  without changing history and checksum rejection on only the independently
  restored disposable fixture. It re-reads original source facts/history. Actual
  Docker/PostgreSQL/image qualification has **not** run.

The user approved the separate restricted proof-task arrangement on 2026-11-08.
The secret-dependency validator currently
requires the administrative executor itself to possess runtime-login probe
authority. This feature deliberately assigns real effective-access proof to a
separate runtime-only database task, with no administrator secret. Asked whether
to extend that rule for the separate task (recommended) or keep it and implement
an additional administrative runtime probe; the selected correction is now
authorised. Do not give administration a runtime task role or administrator
credentials to the separate proof task. This approval does not authorise AWS
changes, publication or acceptance without actual live evidence.

### Approved separate runtime proof: implementation and diagnostic inventory

- Owning standard/schema/guide/workflow: extend the secret-dependency contract's
  existing administrative `runtime_identity_probe` with a closed separate-task
  variant naming `workload` and `target_workload`. Preserve the existing exact
  three-field in-administrator variant and its runtime identity requirement.
- Validator: distinguish missing/malformed probe, absent/duplicate/non-completion
  proof workload, invalid application target, missing runtime identity, a
  different authentication reference, and administrative/migration credentials
  or privileged execution on the separate task. Keep finite findings only;
  never report supplied credentials, probe strings or native exceptions.
- Matching references prove only portable declaration wiring. Provider binding
  must still match the physical database/schema/user and deployed task policies;
  live evidence must prove permitted/denied SQL and real application requests.
  A declaration pass is never effective-access evidence or mutation authority.
- Consumers: existing bootstrap/core-server-persistence declarations unchanged;
  entity-smoke administrative declaration points at its database-proof task and
  server; existing completion and live acceptance controls remain mandatory.
- Planned proof: extend the existing actual-CLI secret-dependency smoke fixture
  with both supported arrangements, malformed/missing/wrong dependency/identity,
  privileged secret/identity, duplicate workload and server-mediated bypass
  counterexamples, including sensitive canaries. Register new runtime/input
  identity requirements in its existing check; review the whole changed
  validator before refreshing its existing diagnostic ledger entry.

Correction self-review: reviewed the whole validator and shell/CLI consumers,
preserved existing findings/three-field probes, and connected the actual feature
to its existing database-proof task/server authentication reference. The new
wrong-type target fixture caught a traceback before handoff; a string-type guard
now selects the finite workload finding. Added rejection of disabled fixture
assertions and fingerprinted PYTHONOPTIMIZE plus actual fixture declarations.
The existing secret-declaration review entry was updated only after this source
review. The scoped README addition follows the README skill and links to the
owning guide; it explains actual findings and explicitly excludes provider/live
proof. No permission change to accepted baselines or AWS is part of this slice.

Required remaining work is the actual gated mutation/reconciliation/recovery,
restore/cleanup and acceptance route; source-matched review and required impact
verification; conditional local checkpoint; separately approved main publication
and concrete AWS changes; actual image qualification and live proof/acceptance.

Independent control implementation inventory while the administrative rule is
pending: exact original/successor ownership and qualified image, stopped versus
STOPPING, confirmed user-requested stop reason, one flushed reservation per
phase/label, immutable input mismatch and lost-response reconciliation; snapshot
source incarnation, original-record observation time, exact missing-code
precondition and ownership; isolated restore CREATE-only exact template/parameters
and eight-resource change review, disabled automatic rollback, terminal execution
observation; cleanup only after retained original-record reader completion and
positive ownership of the new database, never the source. Existing task and
resource reservation helpers retain intent, not acceptance. The owning public
route must still supply genuinely gated provider capabilities. Planned fixtures
must reject changed image/incarnation, preexisting objects, incomplete observations,
unconfirmed terminal state and sensitive canaries without replay. No live claim
or source-review adoption follows merely from helper availability.

Resource-control review found a specific reconciliation gap: a preexisting
snapshot rejected by the fresh attempt could later be accepted by the reserved
attempt because its creation time was checked against the original record but
not the reservation. Require creation at or after both observations, retaining
the original reservation and never submitting again. The owner is
`resource-control.py`'s existing finite snapshot diagnostic boundary; no provider
response, record contents or credentials belong in its failure. Extend the
existing controlled-provider fixture with a full matching snapshot created
before the reservation, and reject it on both first attempt and resume with
zero creates. This is local control proof, not an actual RDS snapshot receipt.

Latest registered source verification (2026-11-08): composition EXECUTED and
PASSED in 25.150538 seconds, including sixteen resource-control cases and
seventeen isolated-restore control cases; publication-contract PASSED using
matching trusted-worktree-cache evidence from its preceding 1.116715-second
execution. Report:
`.cache/test-runs/20261108T145539Z-fc6630b9ec164f0699712df868f0be51/report.json`,
SHA-256 `1f875a1216d4483d3f5b25b50cc466623f71837c7676b7e994d62f6e9e1f1a48`.
Composition input/runtime:
`921db00e11824a0409ab8a0d612131764885fef8f1436733a46187554b3bf4af` /
`5f053c1d9a443bb46117a78268de25927766fa9ce0d23608918859d303bd98e4`.
Publication input/runtime:
`39dfbae9759ea5d515435225d94551be89d5a9bb83860952d609428b0f29f042` /
`64eb7c70b48fa435bf55de26a98449c6ab0c9e3934f510b27ce9e5b9605cbdd8`.
Whitespace passed. These are two scoped local checks only, not full integration,
source-review adoption, real PostgreSQL/image qualification or AWS acceptance.

Before the approval/correction above, rechecked actual blockers rather than
inferring readiness from local fixtures: secret declaration failed
`administrative-executor-declaration-invalid`; that finding is now resolved.
Declaration coverage still reports unsupported
`entity-smoke-acceptance` and the missing acceptance-route contract. Public
deployment/controller and acceptance wiring remain implementation work, not
merely unexecuted tests. The runtime count helper is a controlled healthy
stop/start rehearsal, not the emergency failure-stop controller. No new Git
checkpoint, Docker operation, publication, AWS call or accepted-history change
occurred during this verification continuation.

### Persistent full-proof goal and execution-control continuation

Implemented internal main deployment controls: reserve and reconcile the actual
main template's CREATE with desired count zero, then a source-identical UPDATE
that changes only the feature service's desired count to one. Use the existing
resource-intent store, admitting an explicit pre-record binding for deployment
phases rather than inventing a record digest before creation. Bind source,
qualified image, configuration/permission contracts, dependency incarnation,
proof label, exact template and parameter hashes. Require positive initial
absence, own immutable stack/change-set identities, exact source parameters and
all thirty own resource additions; activation may modify only FeatureService
without replacement. Preserve baseline stack/database resources. Lost create
or execute responses are observation-only; require root event/token lineage,
successful terminal resources and actual own service/task state. Finite owned
findings distinguish source/parameter/ownership/change-shape/lineage/pending or
failed observations; no endpoints, secret references or provider text enter
reservations or public failure details. Controlled tests must exercise each
mutation once and reject existing objects, wrong image/stack/dependency,
replacement/deletion, incomplete pages and activation drift. The owning public
route still must enforce normal realization gates, custody, concrete approval
and bootstrap/migration/grant prerequisites before supplying live capability;
these internal functions do not authorise or perform standalone AWS execution.
Twenty-one named controlled-provider cases now pass, along with existing
sixteen resource and seventeen restore control cases. Whole-source review is
explicitly partial at the still-absent public caller/provider boundary, not
adoption of unimplemented live authority, bootstrap ordering or acceptance.

Registered composition EXECUTED/PASSED in 35.243765 seconds after these changes:
`.cache/test-runs/20261108T165946Z-3e9acfd247284f52a3d3e0daf6d4b6aa/report.json`,
SHA-256 `2e771f4e631d9fa8fe2d9b9afb90ff3c48468f9ff55a836055f88ac69d8ea3ff`.
Input `83419242d33b872c5823cf95b9e6f33f0ee14385d5ff55fe28d854a7339e86b9`;
runtime `5f053c1d9a443bb46117a78268de25927766fa9ce0d23608918859d303bd98e4`.
Five affected metadata headers, 24 composition README links and whitespace pass.
This is scoped local proof only. No AWS/Docker operation, publication, commit,
push or accepted-history modification occurred.

Next required connection is the public gated deployment/task/acceptance route.
Its infrastructure controller must have a truthful operation graph and actual
normalized-fact producer under the existing realization standard: the runtime
graph cannot be labelled live-proven before its roles/tasks exist. First create
the reviewed own infrastructure with zero application tasks, then gate each
administrative/migration/runtime operation against its actual available
dependencies. Reuse existing compiler/custody/release-succession controls; do
not invent normalized passes, an accepted predecessor, or a pre-record digest.

Public infrastructure-route inventory: implement actual plan/review/execute
actions for creation and count-only activation, with offline argument parsing.
The plan binds exact source/custody, scope/permission/template/parameter hashes,
operator account/region, intended counts and label. Comparing an approved-plan
digest prevents executing a different plan; the digest itself is not approval,
which remains explicit user authority in the AWS workflow. Only reviewed own
change-set creation/execution capabilities are admitted, after normal gates.
No task launch, SQL, deletion or credential read is admitted by this route.
Use the operation-specific graph for the real source controller/operator,
checked inputs, verified control-plane connection and durable local intents,
not fictional live app-task facts. Normalize only after actual source checks,
custody/closure validation, controller/filesystem semantics, fresh alignment,
operator policy preflight and reviewed changes. Tests must reject changed plans,
incorrect provider destinations, missing gates and replay after lost responses.
The existing public reporting boundary must return finite safe findings, never
endpoints, credential references, parser text or raw provider error messages.
Full task and acceptance wiring remains required subsequent work.

The public payload-tampering counterexample found that the private CF wrapper
collapsed a known before-submission guard failure into submission uncertainty.
Preserve a narrowly typed not-submitted failure from the real provider guard;
continue treating CLI/remote/lost-response failures as uncertain and never
replay either. Assert the exact guard code and zero provider writes, separately
from the existing lost-response reconciliation assertion.

Infrastructure-route self-review is complete for this source batch, not for the
full proof goal. Reviewed the whole public route, both wrappers, private
deployment/resource controls, generic compiler consumer and actual CLI/test
callers. The planning wrapper cannot be changed into execution by an abbreviated
flag; the parser rejects abbreviations. Both creation and activation retain a
single original reservation after uncertain execution. Actual main-reporter
assertions preserve before-submission rejection versus remote uncertainty;
failed local proof carries only its checked retained report reference. The
actual generic gate rejects missing component observations and changed plan
bindings; component timestamps are not rewritten during serialization. All four
activation prerequisites are collector-validated and checked against current
task/log observations and declared completion contracts. AWS template payloads
are checked against the documented byte limit before submission. Scope and
selector inputs include the infrastructure graph/declaration consumed by these
fixtures. Source-matched diagnostic reviews remain explicitly partial about
unqualified actual provider behavior and the unfinished task/acceptance chain.

Task-route investigation found an applicability gap before implementing a
preflight launch capability: the normal standard requires real deployed
execution preflight before mutation, while a private ECS database-access probe
itself requires RunTask. The only provider-owned exception currently covers
the old staging Stage 6 route, not entity-smoke. Do not borrow that exception,
claim IAM simulation is real database access, or manufacture passed runtime
facts. Asked the user for a bounded entity-smoke preflight rule permitting
explicitly approved, single-submission no-business-write probe tasks before
bootstrap/migration/application effects. The affected task-launch design pauses
pending that harness decision; independent source review and scoped local
verification of the implemented infrastructure route can continue. This request
does not authorize any AWS call or widen either accepted baseline.

Focused registered verification for this infrastructure batch passed with both
checks executed: composition 49.014855 seconds, secret-declaration regression
11.383304 seconds. Report
`.cache/test-runs/20261108T180419Z-81745422e26141989723d8e2cd45b2b5/report.json`,
SHA-256 `2da5616d0f98cae9f8a71bfae20fc7efec3c2ac0752d70a2af934fe3a615adc1`.
The active session retains exact input/runtime identities. Seven affected
headers, fifteen relative guide links and whitespace pass. Read-only impact
planning still rejects the three missing acceptance-chain connections;
diagnostic adoption still reports 46 stale/missing reviews in the broader
unfinished source batch. No source checkpoint, actual package/engine or AWS
proof, publication or accepted-state transition follows from these local passes.

The user explicitly requested a persistent goal for completion of the entire
deployment/proof chain. That goal is active; local fixture passes are milestones,
not completion or acceptance. Existing AWS/publication approval boundaries remain.

Implemented explicit fixed-role revoke/restore operations with bounded-role
preflight, confirmed session termination/absence and observed LOGIN/IAM state.
Neither operation changes passwords, table grants, records or migration history.
Added a separate runtime-login database proof program: effective denied SQL
probes use rollback even after an unexpected success; restore reads use a
read-only repeatable snapshot and the same canonical original-ID/facts digest as
the HTTP verifier. The private HTTP verifier still receives no database access.
Its new observe-create phase reads a reserved label without recreation after a
lost response; the controller must enforce prior task terminal state and custody.

Added source-database proof task/identity/network and a separate owned-snapshot
restore template with its own private database, isolated reader and no source
database permission or administrative secret. The draft runtime graph now binds
six workload nodes to five actual executable programs and two distinct stores.
This is source representation, not proof that a snapshot or restoration occurred.

The new internal task-control primitive durably reserves exact inputs before
one launch and always reconciles an existing reservation. Alternate keys cannot
repeat a create for one proof label. Exact task definition/operation/overrides
are required; empty, paginated or unavailable observations cannot authorize a
replay. It accepts a capability from the future gated route and is not itself an
AWS command, authorization validator or alternative accepted-release ledger.

Direct fresh-build composition proof passed with controlled local dependencies:
public HTTP/lifecycle and observe-create, access controls, database denials and
restore reads, dependency preparation, nine runtime-template negatives, eight
restore-template negatives, two source-graph binding negatives and twelve named
task-control cases. These are exploratory wrapper results, not newly archived
registered evidence, actual PostgreSQL/image qualification or live AWS proof.
Required registration/reviews, complete declarations/controllers, qualification,
custody and approved live execution/acceptance are still in progress. No AWS call,
publication, commit, push or accepted-baseline modification has occurred.

Own build and finished-image qualification command sources now exist. They
require a committed source checkpoint (session notes excluded from image input),
own declaration coverage and delivery inventory before Docker effects. The image
qualifier uses actual packaged entrypoints against disposable TLS PostgreSQL 16,
restricted administrative/runtime identities, real lifecycle timing, effective
negative SQL probes, replacement and explicit access recovery. A second local
PostgreSQL instance receives fixture data by dump/restore; this is explicitly not
RDS snapshot or IAM-authentication proof. Normal PostgreSQL server logs and app
output are inspected for synthetic credential/verifier canaries. Its success
record is emitted only after the existing cleanup owner confirms absence. Syntax,
metadata and the actual CLI's canary-safe invalid-argument branch pass; Docker
execution remains pending the complete declaration/checkpoint chain.

The restricted fixture grants its administrator CREATE/CONNECT WITH GRANT OPTION
only on the disposable database, not CREATEDB or superuser authority. Bootstrap
now explicitly checks that database-local grant authority before changing roles
or schemas, because its temporary migration-owner CREATE grant cannot be made
from an ordinary CREATE-only grant. The controlled fixture rejects absence before
dependent writes. Actual target administrator authority remains a live alignment
precondition; this local fixture does not establish RDS managed-role behavior.

### Approved shared-model correction

The user approved correcting the shared deployment model and continuing proof
on 2026-11-08. Implement an opt-in `operational-realization-contract/v2`; keep
v1 connection/store admission and evidence identities unchanged. The v2 owner
belongs in `.agentic/04.deploy/schemas/`, not a new copy of the retained legacy
harness templates. Existing normalized-facts/change-summary/report formats and
all eight proof gates remain unchanged. No AWS exception is adopted.

Affected consumers are the generic compiler/CLI, its existing regression and
evidence-binding tests, new v2 schema/guide and private-call fixture, the owning
realization standard/workflow, selector inputs and the forthcoming isolated
feature declaration. Existing staging adapters keep their v1 contracts; no
provider code, permissions, TLS policy or historical receipts change.

Predicate inventory: exact v1/v2 selection and invalid schemas; explicitly empty
versus missing/wrong-type connection/store lists; declared execution-unit
destinations versus undeclared/wrong-kind targets; source ownership and both
directional edges; direct store declarations versus actual owned store
connections (not inherited permissions from a callee); unchanged security,
terminal/retry, gate order, evidence coverage, freshness and immutable bindings.
The compiler's finite `ContractFailure` codes must reach the actual JSON CLI
without a supplied canary, native exception or provider operation. Reuse the
existing diagnostics/reporting/evidence helper rather than a parallel registry.
Planned proof uses the real CLI for a verifier with `state_stores: []` calling
a server with a real store connection; missing edges/bindings, invented direct
storage, invalid targets and legacy-v1 widening must fail. Callee configuration,
permissions, graph and image changes must invalidate caller-dependent evidence,
while the caller identity gains no database permission. Independently qualified
unchanged artifact evidence must remain reusable where its stage inputs match.

Consolidated parent self-review for this bounded correction is complete. Reviewed
the whole compiler and its real report/evidence consumers, retained fixtures,
source boundaries and docs. Implemented v2 at the deployment owner; no v1
contract or normalized evidence format changed. Direct exploratory proof passed
the new 53 CLI cases and the complete legacy wrapper, including 19 existing
evidence-reuse cases. The counterexamples distinguish a real service graph from
a fabricated direct-store declaration and stale transitive proof. Only the
compiler's new exact source review is added; prior batch reviews remain pending.
Corrected this test unit's declared effect to `writes-files` because its actual
wrapper creates disposable fixtures. Connected schema/guide inputs and impact
selection to the existing unit. Focused registered proof passed on stable
inputs; these local fixtures do not qualify a package or target. The five current
passing identities are `operational-realization-regression`,
`entity-smoke-composition`, `entity-smoke-runtime` (matching trusted reuse),
`shell-candidate-preflight-regression` and
`shell-deployment-reconciliation-check`. The latter two prove the existing v1
callers locally, not staging provider state. Safe report references and exact
dirty-source/runtime bindings are retained in the active session's
`entity-smoke-realization-verification.json`. No integration claim is made.

Proof continuation now includes the actual own image's draft runtime graph at
`infra/04.deploy/03.product/image/entity-smoke/realization-contract.v2.yml`,
referenced by its image contract. It describes the four implemented runtime,
migration, administration and HTTP-only verifier programs, not a completed
acceptance/restore route. All image bindings are explicitly runtime-bound, with
no guessed digest or fabricated normalized facts. Assumptions remain declared;
real-engine/artifact/current-target evidence is still mandatory. Its private
HTTP connection declares transport security not applicable; this does not waive
private-network alignment or verified database TLS. The compiled composition
fixture validates this real source graph and matches every entrypoint against
the actual four task definitions and source files. Negative cases reject a
misbound verifier command and a structurally valid graph that incorrectly
attributes direct storage to the HTTP-only verifier. This closes the original
representability gap without claiming full declaration coverage. The isolated
restore reader and its execution/acceptance controls remain implementation work;
extend this graph when those units actually exist, before their live execution.

### Full-chain continuation, 2026-11-08

The focused registered batch passed all three selected checks: the actual
composition executed, matching feature-runtime proof was reused, and the whole
realization regression executed. During verification review, the new assertion
guard's `PYTHONOPTIMIZE` input was found absent from this unit's cache identity.
It was added to the existing unit, the disabled-assertion path was proven to
reject, and only the affected realization unit was rerun successfully. Its input
digest stayed unchanged while the declared runtime digest changed, so the old
receipt was not reused under the corrected runtime contract. Composition/runtime
observations were preserved; broad suites were not repeated. This is a
verification-contract correction, not a changed graph or relaxed test deadline.

The next review covers the actual package and provider boundary, not just the
compiled app. The package must copy the installed transitive closure rooted at
`pg` and `@aws-sdk/rds-signer`, retaining nested versions rather than copying
entire SDK namespaces. Its preparer owns missing/invalid manifest, unresolved
required dependency, unsafe source/destination and failed-copy observations;
the final report contains only finite phase/reason/effect, never exception text
or filesystem input. Missing optional dependencies may be absent, missing
required dependencies may not. Counterexamples are an unrelated SDK payload,
an omitted installed optional dependency, a nested version flattened into a
different package and a symlink escaping the installed package tree. These
require focused package-preparation fixtures before actual image qualification.

The provider template must disable automatic image rollback (the approved
recovery is explicitly controlled), drop Linux capabilities for every own
container, retain desired count zero initially, and keep the HTTP verifier
without SQL configuration, credentials, task role or database route. A local
template fixture must reject each unsafe counterexample, including a new
unreviewed resource; it is static proof only, not AWS schema/alignment proof.
Scope declaration and executable provider/acceptance controls remain required
before package/target advancement. Source checkpoint approval is being requested
separately; it grants neither publication nor AWS mutation.

The user has now approved a local Git checkpoint after the checks pass, without
a push. That condition is not met by the focused checks alone; the unfinished
scope/reviews and required integration proof still block that checkpoint.

Before the approved correction above, read-only investigation established a
shared-governance gap. The normal realization owner requires a complete
execution graph before a live operation, but the original v1 implementation
accepted connection destinations only of kind `state-store` or `async-channel`
and required a nonempty `state_stores` list for every unit. The HTTP-only
verifier must instead connect to the private server without direct database access.
Two bounded in-memory variations of the existing valid contract reproduce
`connection-destination-type-invalid` and `execution-unit-state_stores-missing`.
No provider call, receipt or shared gate change was made by that investigation.
Do not invent an asynchronous channel or database edge to pass the compiler.
The Stage 6 exception is explicitly scoped to the old staging plan and is not
adopted for this feature. Under AGENTS.md's missing-governance rule, the route
paused for approval of a shared model change. The user approved it, and the
opt-in v2 implementation/proof above closes that pause without altering v1
admission, omitting a gate or claiming live proof. Remaining chain work is
implementation/qualification, not an unresolved decision about service calls.

Target and isolated-scope direction are approved. The app now has a relational
executor port and mapping, and an additive public persistence app factory/private
command transport. New target configuration, PostgreSQL composition,
administration/migration and verifier entrypoints compile. Registered local
feature, compiled composition and generated-ID declaration fixtures passed on
2026-11-08; their safe observation is retained in the active session. The
administrative observer distinguishes replay-permitted absence from confirmed
applied state without applying migrations. Insert-only creation and update-only
saving reject ID collisions and missing-row recreation. The own Dockerfile,
default-deny context and provider template are drafts, not qualified artifacts.
The feature uses the existing core-platform database through its own fixed
schema and roles; it does not replace that database or modify baseline tables.

The complete declaration/binding/index/catalog/review chain, real PostgreSQL
qualification, image/custody, target alignment and live proof remain unfinished.
No AWS action has been performed. Do not describe these drafts as a deployed
scope or as acceptance evidence.

The user approved the initial-release rule on 2026-11-08: where this new scope
has no accepted release history, failure recovery stops only its own workloads
and preserves database records/migration history. Replacement and isolated
database-restore proof remain mandatory before first acceptance. Later releases
require a compatible accepted image for rollback; do not invent a predecessor.
Implementation inventory for this bounded governance slice: extend the existing
health standard/schema/guide and release workflows, validate a closed optional
initial policy, and add read-only recovery selection to release-succession.
Selection must use the scope's canonical evidence directory and lifecycle index,
reject missing/malformed/unsafe observations and orphaned/legacy accepted history,
and choose the normal restoration policy once a validated current release exists.
Its report is a local policy decision, not live proof, permission to mutate or a
rollback compatibility result. Keep the default recovery declarations intact.
Existing health and succession fixtures will exercise first/subsequent selection,
every unsafe policy field, immutable evidence and retained replacement/restore
requirements. Update only these scripts' source reviews after reviewing them;
the other unfinished batch's reviews remain pending.

Consolidated self-review for this rule is complete: the exact optional contract
is additive, old declarations/accepted records are unchanged, initial selection
is scope-local/read-only and refuses missing/broken/orphaned custody. Normal
selection explicitly leaves rollback compatibility unassessed. The promotion
guard rejects resetting archived history through a missing current reference,
while retaining exact interrupted-first-promotion recovery. Tests exercise the
real CLI, full file/directory snapshots, sensitive canaries and the transition
after simulated acceptance. Corrected registered check wiring to the catalogue's
required Bash wrapper and added the schema input used by the health fixture.
Only the two reviewed script hashes were updated, with partial adoption/debt
retained. All runtime/governance verification inputs for this bounded rule are
now stable for focused registered proof; no other agent is editing them.

Empty scope placeholders were removed after the inventory correctly
rejected an unindexed scope; no declaration, binding or active index entry exists
yet. This keeps the existing accepted inventory intact without claiming the
new scope is complete. Diagnostic adoption currently reports 28 stale/missing
source reviews for this unfinished batch; do not refresh hashes without the
remaining consolidated review or present focused passes as integration approval.

### Connected correctness work identified during implementation

- An exact supplied-envelope test found that write translation selected the
  PostgreSQL helper without its public security catalogue. Its default reader
  retained a persistence primary but filtered a security companion. The target
  now supplies the same explicit Core/persistence/security definition set used
  by its read boundary. A duplicate-ID translation test preserves both source
  records and invokes one query; do not change the shared adapter or infer a
  TLS failure from a duplicate-ID SQL state.
- The former repository conflated create/update through an upsert. Insert-only
  creation and update-only saving are now separate across the public port, both
  repositories, create service, target translation and doubles. Exact local
  collision/non-recreation cases passed; real PostgreSQL qualification remains
  required. This adds no idempotency or optimistic-concurrency framework;
  ordinary edits retain their explicitly bounded last-write-wins semantics.
- The generic server-mediated proof schema's default variant assumes a fixed,
  idempotent synthetic acceptance record and physical cleanup. A generated-ID
  feature needs a distinct declared variant: one reserved labelled create,
  retained original ID/facts digest, indexed lookup without recreation,
  no replay after unknown/completed work, and logical cleanup only. This
  variant is now implemented in the existing owner/checker/fixtures, with the
  fixed-ID requirements retained. Its declaration tests passed, but the live
  controller reservation/reconciliation/cleanup chain is not yet implemented.
- Keep the required server replacement, compatible image restoration and
  isolated database-restore proof obligations. The independent feature image
  must prove its own original data, not borrow the core acceptance table's
  receipt. Its private HTTP verifier has no database credentials; a separately
  bounded restoration reader may use only the isolated restored dependency.
- Migration uncertainty must be resolved by the declared administrative
  observer before replay decisions, preserving checksum/id/actor binding. An
  ordinary migration identity's observation is not substituted for that route.
- Initial candidate failure is not restoration of an imaginary accepted image.
  Declare a labelled stop/preserve-state path before an initial target change;
  normal release succession still requires its own accepted evidence.

Results belong in the active chat session, disposable local observations under
`.cache/test-runs/`, and genuine package/target receipts under their owning
scope. Never manufacture receipts to make declaration coverage appear green.

### Final acceptance connection inventory — 2026-11-09

Continue the existing verify/accept workflow and release-succession owners. The
cleanup deletion exception is still awaiting approval and must remain unchanged;
no collector may bypass its compiler or claim cleanup from missing resources
alone. A genuine retained successful reader, positively owned delete reservation,
terminal cleanup result and seventh-gate custody must precede final verification.

The existing credential history is explicitly historical/not-ready. Add a closed
`acceptance` task stage containing only verifier `read` (its separate existing
HTTP ready preflight supplies fresh liveness/readiness). Require original digest,
completed cleanup/history/snapshot and current source/image/role/network/operator
bindings before its preflight or read. Retain the same runner/admission/collector/
completion controls; do not introduce another task runner or accept the older
credential-read receipt as final proof. Completion must postdate cleanup and the
collector must reobserve the final task/logs and current running server, then
bound freshness. Historical receipt checks alone cannot establish current health.

Implement cleanup completion reading at the existing restore owner, rejecting
missing/changed plan/request/binding/journal/result/gate/readback/ownership and
ordering separately. Reconciliation is read-only only after the exact original
delete journal exists. The current generic delete prohibition still blocks this
stage until separately approved; tests must retain that honest limitation.

The collector will emit an immutable `deploy/release-candidate/v1`, not a new
accepted-release framework: archive checked proof bytes under the existing
scope evidence root, hash current configuration/permission contracts, preserve
source revision/digest/custody and the exact full required proof set. Promotion
remains the existing release-succession command with expected predecessor `none`
for an eligible first release; no accepted record, current reference or scope
lifecycle is advanced by collection. Later releases require the existing
compatible-accepted-image recovery obligations, not reuse of first-release proof.

The acceptance-route compiler's existing fixed accepted-record reader assumes
a legacy file with status accepted, whereas release succession owns an active
current-reference plus immutable accepted history. Inspect and connect that
existing current-reference contract rather than writing/overwriting a parallel
accepted-release.yml. Preserve all older route defaults and baseline/staging
records. Any necessary additive reader selection must be proved with old-route
and current-reference counterexamples before broader checks.

Required consumers: task-route/steps and completion, restore completion reader,
scope-local collector/record validator/public wrappers, acceptance route and
record/proof contract, existing selector run-check registration, release
succession and local scope promotion. Inventory source/custody/configuration/
permissions/digest/incarnation and every stage's exact producer, finite failure,
known effect and retained path. Tests must reject omission, copied/wrong-stage
or stale final reads, changed proof bytes/gates/parent digest, wrong-source clone,
unowned cleanup, replay, simulated-to-live evidence and missing acceptance
authority. Use controlled existing fixtures for local protocol proof, not fake
AWS acceptance. Source reviews and final registered proof remain required.

Safety review rejected the first proposed completion reader because it invoked
`cleanup_restore`, an execution-capable helper, even behind an existing-journal
guard. That patch was not applied. The safer implementation extracts the owning
helper's pure identity validation and read-only `observe_cleanup`; acceptance
never calls the execution helper or `.reserve`. The existing execution path
keeps its original checks, one reservation/submission and uncertainty behavior,
then delegates only observation. Controlled regression uses a store with no
reservation method and a provider permitting only describe/get calls, proves
unchanged journal bytes, rejects no-journal absence before all provider I/O and
retains pending/orphan/unknown outcomes. No new cleanup authority is granted.

The new `acceptance` stage is now connected to that strict cleanup reader through
the existing task route/steps; only verifier read and its distinct ready preflight
are selected. Snapshot inspection adds only two bounded read operations to the
task provider, not snapshot/deletion/secret-value capabilities. Module-boundary
translation preserves exact finite conditions, binding field/item and safe
evidence attachments at the actual task reporter; unexpected errors remain
unclassified without native text. Controlled stage tests distinguish its key
from every older stage and reject missing digest, other operations and absent
launch approval. They also prove the current real cleanup graph remains denied.
That last case represents the still-pending rule decision: if approved, replace
it with the appropriate default-denied versus explicitly eligible graph cases,
not a waiver of the generic deletion prohibition.

Register these fast local protocols as `entity-smoke-acceptance-controls`, with
conservative imported source/contract inputs, and include them in full composition
and the scope's local proof obligations. They are not the missing run-stage
`entity-smoke-acceptance` check and do not create acceptance evidence. The true
final collector, reference-based acceptance route/record validator and connected
post-cleanup task/collection tests still remain to be implemented. Positive
connected cleanup/final-stage proof remains blocked at the unapproved compiler
exception; successful controlled source/cleanup doubles cannot satisfy it.

Consolidated self-review for the fast control slice inspected complete restore
control extraction, new final-stage helper/fixture/wrapper, modified task route
and step selection, root completion-reader addition and catalog/scope/wrapper
consumers. The reader has no execution-helper/reservation call; missing journal
rejection precedes provider reads, and uncertain absence stays pending or failed.
Existing seventeen restore cases remain and five observer cases add explicit
no-write/no-mutation assertions. Final-stage keys cannot alias older tasks, and
the existing runner still requires concrete approval, distinct ready preflight,
admission, original reservation and completion gates. The actual wrapper's exact
two children and both failure exits are exercised through an owned command
double, not inferred from printed success. Provider read additions explicitly
reject deletion, snapshot creation and secret-value reads.

Two fresh PARTIAL reviews cover only restore-control and acceptance-steps;
unfinished restore/task-wrapper reviews are not refreshed to hide the blocked
connected positive path. Catalog registration uses conservative imported inputs
and retains the full composition obligation. Focused registered controls may
pass while connected cleanup, final launch, full collector/route, broader reviews
and live acceptance remain required and incomplete. All fast-unit inputs are now
closed for its registered verification; no AWS, package publication, acceptance
or source checkpoint is authorized by that local result.

Reopened only metadata preparation after the first registered batch: the control
wrapper executes Git to resolve its worktree, so its declared runtime now includes
Git; the final-stage prerequisite calls the existing context's local writeability
probe, so its library effects explicitly include local writes as well as network
observation. Neither correction grants an AWS mutation or changes task behavior.
Updated only that helper's reviewed hash after checking the existing context call.
The first fast control pass is historical for the older metadata; the selector
mechanics pass and repository-contract failure are retained, not relabelled fresh
proof after catalog input changes. Investigate the failing repository case with
supported fail-fast focused invocations; do not rerun or weaken the entire suite
merely to obtain a passing checkpoint. Final fast-unit inputs are closed again.

### Acceptance receipt retention and collector predicates — 2026-11-09

New collection and historical validation are different boundaries. Collection
uses qualified immutable custody, committed source/current contracts and fresh
target/role/network/image observations, the captured full credential history,
real completed snapshot/clone/read/cleanup and a distinct final preflight/read
after cleanup. The final task is remotely reobserved, must preserve the original
record digest and be no older than fifteen minutes (future skew at most sixty
seconds). Historical task receipts cannot satisfy that current observation.

Retain only validated, closed task packets/reservations/results, their completion
and gate facts, selected portable graph and explicit safe control facts. Do not
copy arbitrary cache trees, raw provider dictionaries, SQL values, credentials
or unvalidated extra JSON into the release evidence root. Task completion's
existing historical gate checks should be extracted within that owner for reuse
by the archive reader, with its current caller unchanged. Historical validation
binds retained artifacts to the captured controller/source/image/contracts and
selected graph, not to today's source digest or freshness clock. The current
collector still checks the present source and real final task separately.

The collector emits content-addressed immutable proof receipts and the existing
release-candidate format under this scope's existing evidence root. Candidate
identity covers the exact required proof set plus configuration/permission hashes.
Only collection writes those new files; no source record, accepted history,
current reference or scope lifecycle is changed. Repeated collection reconciles
the original immutable collection/candidate rather than restamping old proof as
fresh health or issuing another task. Incomplete/changed/conflicting retention
remains an explicit failure; partial files never imply successful collection.

Initial-release-only collection requires the existing recovery selector to
confirm no current or historical accepted custody. A later release must not reuse
first-release stop/preserve as its compatible-image restoration proof. Tests may
build explicitly simulated evidence only under owned temporary roots; production
has no caller override for evidence class, target or evidence root. Exact source
ownership, field/operation/phase/stage alternatives, prior-operation no-replay,
wrong record/source/incarnation, omission/changed bytes, retention conflicts and
native canaries remain required cases. New candidate collection never counts as
release promotion or AWS acceptance by itself.

Collector review found that closing only top-level control keys still allowed
unchecked nested terminal-task fields and untyped identifiers/timestamps into
retained evidence. Tighten those at the existing validator: exact owned ECS/RDS/
CloudFormation identities, bounded terminal sets, closed actor shapes, actual
booleans/integers, hashes and ordered times. Reject malformed selections before
dictionary lookup rather than lose the finite reason to a TypeError. At the real
collector reporter preserve existing binding context, source evidence references
and checked task diagnostic companions; native exception text stays excluded.
Extend the existing fast acceptance-control fixture with controlled positive and
negative shape/freshness/parser/reporter/immutable-retention cases. These are
local protocols only: complete control gate custody, full collector connection,
route integration, source reviews and live proof remain incomplete.

Consolidated self-review for this bounded draft slice inspected both complete
new modules, the completion extraction, actual source task/admission/gate readers,
existing collector failure reporters and the registered two-child fixture owner.
The new tests reject nested native fields, bool-as-count, wrong service identities,
non-distinct replacements, freshness one second outside both permitted bounds,
pre-cleanup final reads, absent write selection, mutation/secret-value calls,
changed immutable bytes and symlinks. Real main cases assert original source
condition/context, exact checked primary/related records and private unknown
fallback without another collection call. The archive case uses the actual local
task collector and GateBook, then rejects a missing gate even after its envelope
hash is recomputed; historical reading explicitly cannot call today's source
digest. No original tests were removed. Source-reviewed statuses remain PARTIAL:
projected control hashes alone do not retain original gate/plan custody, full
aggregate chronology and clone-permission bindings need completion, and no
candidate/current-reference integration or live acceptance is established.
Close this slice's fixture inputs for the focused registered local pass only;
do not describe it as full integration or broaden the pending cleanup authority.

### Complete retained control custody — 2026-11-09

The preceding focused turn was verified progress, not full acceptance. The next
connected gap is durable original control plans/gates. Extend the existing
acceptance evidence owner with a reusable historical gate check, and add its
control-custody sibling for the seven explicit operations. Capture the original
safe plan, selected graph, exact original gate bytes and bounded reservation
identity/time/request hash. Validate closed plan keys/scalars, operation-specific
limits, source/configuration/permission/incarnation/record binding, graph and
plan digests, all seven gate/component/artifact facts and exact operation counts.
Initial stop/restart use the existing custody-composed controller artifact,
not an invented equality to the plain task-controller hash. Historical readers
must not query AWS, inspect today's source or rerun an operation.

Production collection must read only the selected original gate under its own
fixed cache prefix and compare the original byte hash before copying. A projected
fact envelope alone must no longer pass full control validation. Keep projection
shape tests explicitly separate from full custody tests; use actual existing
GateBook producers for the six currently permitted graphs and reject the still-
prohibited cleanup graph without patching its compiler. Exercise missing plan/
gate, changed hashes and semantic counts, wrong operation/binding, uncontrolled
plan fields and native canaries with exact finite reasons. The existing fast
unit remains the local owner. The new helper and collector mapping must preserve
source exceptions/diagnostics at the real caller. This is receipt retention,
not a new gate engine, provider capability, cleanup approval or live proof.

Consolidated self-review inspected complete acceptance-controls, the shared
archive gate extraction and collector integration, actual six allowed graph/
plan/gate producers and the unchanged denied cleanup graph. Full validation now
requires custody; fact-only tests explicitly exercise only the projection reader.
The control plan key sets cover every retained scalar with type/limit/binding or
hash checks. The archive omits raw request/provider dictionaries, retaining only
original submission identity, time and request hash; that summary cannot prove a
complete payload or authorize replay. Capture compares actual original gate
bytes under a selected fixed prefix. The actual local GateBook cases reject
missing gates and recomputed-hash semantic/bool count tampering, wrong controller
path/source, reservation/time and binding changes, raw canaries and outside-cache
references. Both historical source-owner lookups are forbidden by the fixture.
Real collector main preserves the helper's original condition and selected item.
No old case, wrapper child or permission guard was removed.

README skill use is bounded to three draft-file inventory rows and the archive
explanation; preserve unrelated command guides. Source/reader review and all 58
relative links pass. The text explicitly separates local controlled plans/gates,
unfinished full collector/promotion wiring and actual live evidence. Current
source reviews remain PARTIAL with exact outstanding aggregate connections,
clone permission/role binding, partial collection and public-route integration
debt. No positive cleanup/archive chain, live candidate or accepted state is
claimed. Freeze these local unit inputs for the focused registered pass; broad
composition still has the same real cleanup-rule block pending separate approval.

### Connect the acceptance route and registered RUN obligation — 2026-11-09

The preceding control-custody turn was verified progress. Complete the missing
consumer connection rather than adding another acceptance ledger: the existing
collector produces the existing release-candidate format, and the current
accepted record is the existing release-succession current reference. Add a
target read-only candidate/current validator, a bounded manifest input and
public wrappers, a fresh-proof guard around normal release/scope promotion, the
scope acceptance route/schema and its missing registered acceptance-stage check.
The composite proof explicitly includes every selected task/control; its parser
must report that actual proof contract. No command may invent passed tasks,
promote a simulated production record, query historical expired ECS tasks as
current proof, or use a candidate as already accepted custody.

Generic route and scope-promotion consumers currently understand only embedded
legacy accepted records. Add only the explicit release-succession-current
selector, checking its current-reference schema/path and actual read-only owner
validator result/evidence class. Preserve the existing selector-absent legacy
branch and prove both paths through existing temporary rehearsal fixtures.
The current-reference reader must call the actual succession lineage/hash
validator and validate the archived entity-smoke candidate/proof, without
requiring historical contracts to equal today's files. New promotion still
requires current contracts and fresh same-candidate source/runtime/full proof.
Retained/idempotent reconciliation must not be reported as fresh health.

Implementation consumers are the scope declaration, route compiler, scope
promoter, check catalog/selector and existing fast/control plus route-regression
fixtures. Only offline real-parser/template validation is local route coverage;
actual acceptance remains blocked on genuine cleanup/final read/collection and
concrete package/AWS execution authority. Keep the pending cleanup rule unchanged.

Consolidated self-review inspected the complete collector manifest/report
extraction, state validator, promotion guard, three public wrappers, target
route/schema, generic selector/compiler/promoter changes and all direct catalog/
workflow/fixture consumers. The actual template parser reports covered; actual
impact discovery now reports planned with no missing route/check findings.
The feature's current-reference selector is explicit and rejects wrong source,
schema or path; the legacy absent-selector branch is unchanged. State readers
reject symlinks before resolution and preserve the original finite path condition
at the actual CLI. The shared failure projection preserves existing task/source
companions and native-error privacy instead of introducing a second reporter.

Seventeen named route groups distinguish real parser/wrapper and manifest/state
boundaries from explicit candidate/source/validator/inventory/promotion doubles.
They exercise full-same-candidate freshness, changed/missing proof or source before
any release effect, exact original archive/already-current reconciliation without
new health claims and preservation of a successful reference when a later index
step fails. The actual generic promoter uses real temporary index writes, but
its positive record validator/inventory are controlled protocols, not feature
acceptance. Existing control cases and first/second child failure exits remain;
a third route child and its failure exit were added to the same wrapper and
full composition. Its declared development estimate is now fifteen seconds.

An exploratory fixture exposed two test groups reusing the same disposable
evidence directory after the new symlink check. Isolated the state-reader
directory rather than weakening its rejection or changing production behavior.
No trusted proof was taken from that failed exploratory run. README skill use
updates only the relevant inventory/status and actual acceptance-command guide;
all sixty-five relative links pass, with controlled protocols versus actual AWS
proof explicitly distinguished. The work is still PARTIAL: aggregate chronology/
predecessor/custody/clone-permission links and original cleanup/final-read/full
candidate/current/promotion positive proof remain incomplete. Freeze these
reviewed inputs for registered focused controls plus existing connected legacy
route regression; do not run all repository checks repeatedly while the real
cleanup rule and broader source reviews remain unresolved.

The first registered frozen batch passed the feature controls but failed the
existing connected persistence route regression. One direct failing diagnostic
run located its real scope-promotion assertion: the fixture changes every scope
except persistence to active, so the new unrelated entity-smoke candidate is
incorrectly activated without accepted custody. It also assumes exactly two
scope rows and copies only the selected image contract into its otherwise full
target clone. Correct the owning fixture, not the production gate: select only
bootstrap as the active predecessor, copy each indexed scope's declared image
contract for complete template validation, and assert by identity that unrelated
scope entries remain exactly unchanged through successor and independent
activation. Preserve all prior failure/lineage/receipt tests and actual gate
calls; do not remove the new scope or weaken missing-acceptance rejection.

Reviewed that correction against the actual failed call and the inventory's
accepted-record validation. Both original selected-scope transitions still use
the same real route/record/inventory validators. The new identity-based
assertions preserve the original bootstrap/persistence lifecycle outcomes and
add exact preservation of every unrelated row; no scope is filtered out. All
declared image contracts are copied as fixture metadata only, not qualified
images or acceptance evidence. Freeze this corrected fixture and its metadata
with the already reviewed route implementation before the affected rerun.

### Aggregate proof connections — 2026-11-09

The preceding route/compatibility turn was verified progress. The remaining
aggregate gap is semantic connection between individually valid receipts. Keep
the agreed nineteen task/seven control set; do not replace actual owner checks
or add a parallel acceptance ledger. Extend the existing control archive owner
with pure aggregate checks: original prerequisite/preflight/operation order,
selected task-definition/private-network consistency and unique task/control
attempts, original stop/restart/replacement/read links, exact negative admission
revocation, recovered positive proof, snapshot/clone/read/cleanup/final order,
the same history/snapshot/reader/template hashes and clone permission/incarnation.
Retain both original control-value and canonical document hashes for links that
use different existing producer conventions.

Expose the existing stop owner's artifact basis without altering its hash
algorithm; retain that closed four-source basis once in the aggregate so the
historical reader can bind the actual custody-composed stop/restart artifact
to the root controller/configuration, without inspecting today's files. Source
capture still uses the real owner and actual file hashes. The collector and
historical candidate reader must call the same aggregate check before retaining
or accepting a candidate. Finite errors identify the affected task/control;
source diagnostic companions and native privacy remain with the existing shared
report projection. Wrong order, copied attempts, actor/network drift, swapped
negative admission or source/hash/template/predecessor must reject at the real
collector validator. Use explicit prevalidated-owner protocol fixtures for this
connection test, never label them full gate/AWS proof; cleanup's real compiler
prohibition remains in force until separately approved.

Consolidated self-review checked complete aggregate helper and collector call,
original task/preflight/credential/recovery/restore floors and hash conventions,
the stop artifact extraction and unchanged public failure boundary, plus schema
and direct fixture consumers. The helper uses captured source basis and semantic
timestamps, not today's files; it does not require impossible successor-start
versus predecessor-stop ordering or a healthy application to admit emergency
stopping. Workload consistency is definition/private-network evidence, not a
new claim of effective IAM/SQL authority. Runtime/network failures identify the
actual safe field and affected item through real collector main.

The aggregate fixture uses the real collector validator and connection helper
with explicitly prevalidated primitive-owner protocols; it asserts all thirty-
seven task phases and seven controls were visited and rejects twenty-three
independent misassemblies. Source/file lookup spies forbid historical reads;
no provider query, candidate retention or accepted-state write is part of this
fixture. Actual primitive collectors/gate producers retain their separate tests,
and the existing failure-route fixture passes its twenty-two controlled groups.
Source reviews remain PARTIAL for genuine original cleanup/final collection/
candidate/current/promotion and live/package proof, not silently adopted from
these doubles. Public CLI flags and the existing guide's unexecuted-live-proof
boundary are unchanged. Freeze this bounded source/review batch for the focused
registered control unit; full impact/integration remains pending.

### Package-boundary source review, 2026-11-09

Reviewed the complete feature runtime preparer, build/qualification wrappers,
image qualifier, dependency-boundary fixture, publication controller and workflow
validator/wrapper, alongside their existing dependency, runtime, qualification,
workflow, pipeline and publication fixtures. This review changes no runtime
predicate, public diagnostic, permission, cleanup policy or execution authority.
Reuse the existing runtime-preparation phase/location/effect report, fixed shell
codes, safe-command diagnostics and publication operation-diagnostic collector;
do not introduce another reporting registry. The dependency-boundary script is
verification plumbing, not a provider operation or evidence of image execution.

Review inventory: argument/source/clean-checkpoint rejection before build;
missing compiled entrypoint/export before shim writes versus partial preparation;
actual compiled package/asset resolution and forbidden dependency ownership;
qualified source/image/configuration before reserving publication; exact fixed
publisher/repository, reservation before the sole push, unknown push outcome
versus observed immutable digest/source; and positive disposable-resource absence
versus unavailable Docker observations. Existing qualification-control tests
exercise the actual qualifier CLI and exact reservation cleanup through a fake
Docker executable, with canary exclusion and no removal on failed observation.
Publication fixtures use controlled provider/command protocols and assert no
second push after loss. Workflow fixtures exercise the actual validator against
unsafe source, ordering, commands, retention, permissions and destination edits.
Those are local protocols, not actual image, ECR, RDS or AWS proof.

Record the operational sources as PARTIAL: shim failure/reporting and partial-write
permutations, downstream shell/source diagnostic failures, full qualifier error
paths and failed diagnostic collection still need their applicable proof. Actual
Docker/PostgreSQL qualification, vulnerability/SBOM/provenance custody, publication
and live approval remain outstanding. The bounded cleanup-rule decision remains
separate and cannot be inferred from this review or the user's unready approval.

### Runtime startup/close correction inventory, 2026-11-09

Source review found that a returned failed server start followed by a throwing
runtime.close enters the startup catch, reports the close error as startup and
calls runtime.close again. Correct only this target runtime boundary: preserve
the original startup diagnostic and companions, attempt pool close once, and
report a close failure through the existing close/not-assessed record. A thrown
startup and a returned rejection both require one close; successful startup must
not close its running app's pool. Invalid checked database configuration must
prevent pool construction and server startup entirely. No new diagnostic
definition, app/Platform contract, dependency or permission is necessary.

Consumers are entity-smoke/runtime.ts, its source entrypoint and generated package
wrapper, and the existing compiled runtime-test.mjs exercised by composition.
Extend that fixture with real target configuration, Core lifecycle policy, app
construction and PostgreSQL adapter setup, while explicitly controlling pg.Pool,
CA-file reading and the server's returned/thrown protocol. Assert exact reports,
original primary/related preservation, no native canary, one start/close at most
and success ownership; restore every test replacement in finally. The existing
real mounted HTTP fixture remains separate proof of server/app integration.
Demonstrate rejection of the old double-close behavior before the source fix.
Use freshly compiled exploratory runtime proof while full registered composition
remains blocked by the separately unapproved restore cleanup graph; do not claim
that this focused fixture satisfies composition or live/package verification.

The first new regression reproduced exactly two close attempts instead of one;
the corrected runtime passes the compiled runtime/preflight/database-proof slice.
Consolidated caller review also found that the target reporter's definition
selection omits Server's built-in diagnostic families, although startup can
return their records. Preserve those already-owned definitions only for startup
reporting, using their public catalog exports; do not widen the SQL operation
catalogs or inject duplicate server mount catalogs. Test a literal supported
server-start record and existing TLS companions through runEntitySmokeMain,
alongside unknown-thrown and close failures. Its exact record must survive,
not become the target's generic unknown startup record. The shared Python
selected-record reader already includes these built-in catalog families; no
cross-language vocabulary or generated definition changes are required.

Bounded self-review is complete for these two corrections: checked the complete
runtime/reporter, public catalog exports, source/generated entrypoints, actual
server return sites and shared Python generic reader against the inventory.
The old close behavior failed at exactly two attempts versus one; the old
selection failed by substituting target boundary/not-started for the literal
server listen/unknown record. Both corrections now pass the same freshly
compiled runtime fixture, including ten startup combinations and a separate
non-startup narrow-selection assertion. Existing real HTTP lifecycle, SQL
preflight callers, database-proof fixtures and source dependency closure pass
on those same compiled inputs. These are direct exploratory proofs; the owning
registered composition remains blocked by its real cleanup graph, not waived
or split to manufacture a pass. Current impact planning reports no findings
and retains its full local/package/deploy/acceptance obligations.

Reviewed the ten remaining target configuration/runtime/SQL/proof/entrypoint
sources in full and recorded PARTIAL reviews with concrete constructor, malformed
input, processing, per-family, transport and real-engine/live debt. Refreshed only
the changed reporter's reviewed source hash and reason. The canonical fact digest
is caller-validation-dependent; existing changed-fact counterexamples are not
an independent golden digest or every-field test. No definition export changed.
Structural adoption still has eighteen wider stale/unreviewed findings; none
belongs to this reviewed target-source batch. No checkpoint or integration
completion is claimed, and the pending cleanup decision still grants no AWS
execution authority.

### Alignment/restore/lifecycle review and fixture correction, 2026-11-09

Reviewed the remaining multi-template configuration adapter, alignment command
and wrapper, clone binding/restore/reader commands and wrappers, and whole scope
lifecycle validator. The review preserves existing finite owner failures and
private effects; no runtime policy or deletion exception is introduced. Alignment
fixtures pass twenty negative cases and actual-template configuration tests pass,
but these use controlled responses, not provider observations. Restore source
review explicitly retains the unapproved cleanup compiler rejection and the
unexecuted successful-cleanup/final-acceptance assertions as missing proof.

The registered active-workload-health-recovery-regression failed; one visible
diagnostic rerun identifies scope-lifecycle-inventory-incomplete at the old
successor fixture's first positive transition. That fixture replaces all scope
index entries with bootstrap, but retains the newly copied entity-smoke directory.
Correct only the fixture, not production discovery/ownership rules: preserve every
unrelated entry/directory and locate selected bootstrap/persistence entries by ID
rather than position. Assert unchanged unrelated entries through the positive
candidate and succession transitions. Retain all existing missing-predecessor,
duplicate-active, historical reciprocity, independent-candidate and secret tests.
This is test-maintenance for the approved isolated scope, not a new lifecycle
state, inventory exclusion, acceptance waiver or AWS execution authority. Review
the complete correction and then rerun its existing registered owner once.

The corrected lifecycle regression passes all retained transitions and unrelated-
scope assertions. Complete target-declaration source review and its existing
registered regression also pass, together with the publication-control fixture.
One new pipeline-state predicate introduced by the feature uses set membership
without a string guard: a list/dict state throws instead of preserving the owner's
pipeline-record-invalid rejection. Add explicit malformed-state counterexamples
to the existing pipeline fixture, reproduce the loss, and restore that owned
reason with a type guard before membership. No allowed lifecycle state, publisher,
destination, proof, authority or legacy pipeline selection changes. Re-review
the complete narrow correction and rerun the two affected registered owners;
the earlier passing report remains historical for changed source inputs.

Consolidated self-review of both corrections is complete: whole lifecycle
validator/fixture and target-declaration checker/fixture, changed pipeline
predicate, publication fixture and actual main reporter agree with that inventory.
The original lifecycle positive case failed for the precise incomplete-discovery
reason, not a provider result; no gate or discovered scope was removed. The
malformed-state case reproduced the old TypeError; four changed-state cases now
reach actual main with pipeline-record-invalid and no canary or later work.
The source guard does not widen any allowed state or identity.

On frozen inputs, registered lifecycle regression EXECUTED/PASSED29.785024s;
the corrected target-declaration and publication batch EXECUTED/PASSED31.618103s
and0.963682s (total41.353664s including selection). Exact reports and fingerprints
are retained in the session record. Nine new operational sources have complete
source reviews recorded as PARTIAL with exact remaining boundaries, and only the
reviewed target-declaration hash/reason was refreshed. Structural adoption still
fails at eight wider stale source reviews, with no unreviewed-source findings.
These results are not full impact/integration, successful connected cleanup,
qualified image/custody/publication, AWS execution or feature acceptance.

### Final source-review refresh and catalog invalidation, 2026-11-09

Read all eight remaining stale sources completely against their existing owner
reviews and connected callers: task graph/stages, exact task/role/network binding,
public task route, snapshot route, public infrastructure route, resource controls
and catalog exporter. Preserve their existing PARTIAL status and exact live,
cleanup, malformed-input, processing and concurrency debt. No source review can
turn the cleanup compiler failure or later unexecuted assertions into proof.

Exporter review found a real input-identity omission: the diagnostic compilation
already imports the feature app and exports its catalog, but catalog-readers and
the diagnostic aggregate omit apps/entity-smoke from their declared inputs.
Add that actual consumed source root to both existing owners and the feature
workspace package to their shared runtime identity. Keep every existing member,
prerequisite and stage/effect rule. Extend repository_contracts_test.py with a
temporary-file counterexample using the actual catalog inputs and actual
fingerprint function: changing feature diagnostic source or its exported JSON
must change identity, an unrelated file must not, and removing the feature root
must reproduce the omission. Assert the shared runtime package binding too.
Prove the old declaration fails, then correct it; no provider operation,
arbitrary evidence import or new test scheduler is introduced.

The new actual-fingerprint test reproduced the omission for both old declarations;
the corrected input/runtime bindings pass, with existing aggregate runtime and
package-membership tests unchanged. Complete bounded self-review checked the
actual compiler include/import closure, exporter selections, check declarations,
runtime inheritance, fingerprint implementation and discovered test collection.
No selection/cache algorithm or execution effect changes. All eight previously
stale operational/exporter sources and the changed verification-only fixture now
have source-matched reviews; existing PARTIAL debt is preserved, not relabelled
as adoption. Structural diagnostic review passes with no findings.

The actual task-binding, public task/activation/replacement route, infrastructure
route and resource-control fixtures pass on current sources with explicitly
controlled provider protocols. Complete original snapshot/clone/cleanup/acceptance
is still missing, and no command authorizes AWS. Freeze all affected executable,
catalog, review and fixture inputs for registered selector mechanics, repository
contracts and catalog/readers. The check plan is PLANNED without findings. This
batch does not waive the separate cleanup decision or full impact/integration;
retain those obligations and the known composition failure without replaying it.

Frozen registered batch EXECUTED/PASSED: selector mechanics219.455368s,
repository contracts371.819428s, catalog/readers43.788804s; total662.656387s
including selection/identity. A separate registered diagnostic-adoption pass
completes the structural review gate with no findings. Catalog compilation and
strict reader proof now match the corrected feature input/runtime identities.
This is local evidence, not full composition/integration or package/live proof.

The blocking audit re-read the actual compiler and cleanup graph: the compiler
still requires delete/replace/broaden-permission forbidden, while truthful clone
cleanup declares delete. The already-observed change-shape-invalid is therefore
still binding. The bounded cleanup governance decision has recurred across at
least three consecutive goal turns without an approval; safe independent source
review/cache/compatibility work is now verified. Do not invent an exception,
relabel cleanup, repeat the known composition failure or advance the conditional
checkpoint/package/live chain. The full goal must wait for that specific user
decision, then continue its original scope. Separate concrete AWS/publication
authority is still absent, even if the source-rule change is later approved.
