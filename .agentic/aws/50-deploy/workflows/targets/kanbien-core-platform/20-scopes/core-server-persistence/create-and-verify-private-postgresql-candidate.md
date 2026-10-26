<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
version: 6
status: active
created_on: "2026-10-23"
updated_on: "2026-10-26"
layer: 04.deploy
domain: deployment.core-server-persistence
disciplines: [security, sre]
kind: workflow
purpose: Govern the single target-bound creation, migration, verification, and later acceptance of the private PostgreSQL-backed core-server candidate.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.command.kanbien-core-platform.prepare-core-server-persistence-candidate
  path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh
-->
# Create and Verify Private PostgreSQL Candidate

Use this only for `kanbien-core-platform/core-server-persistence`. It creates
the separate candidate stack and never mutates `bootstrap-runtime` or staging.
Bootstrap remains the retained, accepted dependency-free baseline until the
candidate has completed its governed migration, verification and recovery work.

## Preconditions

Use the exact qualified persistence package-custody receipt. It must identify
the target, persistence candidate, image contract and runnable program. The
target’s live USD 100 budget, existing private foundation, immutable ECR image,
private ECR/Logs startup endpoints, and the region’s managed S3 artifact prefix
list must all be re-observed immediately before a stack mutation. The new
server and migration groups must allow that prefix list: ECR resolves image
layers to private S3 retrieval, so endpoint access alone is insufficient. A
failed or interrupted observation blocks creation; it does not permit a
substitute route.

## Creation

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.sh --receipt "$receipt" --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.sh --receipt "$receipt" --json
```

Change-set submission is asynchronous too. After an interrupted submission,
observe the fixed digest-derived name without submitting again:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/create-change-set/script.sh --receipt "$receipt" --reconcile --json
```

If CloudFormation rejects creation, the controller retains a
`deploy/deployment-operation-diagnostic/v1` report under the scope's governed
release evidence before any failed review artifact is removed. It contains only
the operation identity, safe classified provider finding, safe resource/property
facts when available, outcome, evidence reference, and next governed action.
It does not retain `StatusReason` or raw events. An unavailable diagnosis is
recorded as unavailable; it is not a reason to infer a cause or retry CREATE.

Review the fixed CREATE change set. It may create only the declared private
RDS, Secrets Manager, ECS, IAM, Cloud Map, security-group and Secrets Manager
endpoint resources. Verify its digest and source revision match the receipt,
the target tag is present, public access is absent, and the retention/deletion
controls match the template. Execute only the exact returned change-set name:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.sh --receipt "$receipt" --approved-change-set "$change_set" --json
```

Creation returns `pending` until that exact approved change set and its stack
are independently observed complete. Reconcile without executing again:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.sh --receipt "$receipt" --approved-change-set "$change_set" --reconcile --json
```

Follow `.agentic/04.deploy/standards/provider-async-conditions.md` and
`.agentic/04.deploy/standards/safe-command-diagnostics.md` for outcome
meaning. `failed` requires positively observed terminal failure; `uncertain`
retains the operation identity when observation cannot prove the result. Both
remain unaccepted. Do not delete, retry, or submit another change set merely
because a client response was lost. CREATE review requires the exact change-set
name, source revision, and both server and restore-verifier image digests.

## Run Proof

### Permission-separation update of an existing candidate

Privilege separation on an existing healthy candidate belongs to the bounded
permission-surface controller below. Its executable resource-change guard
requires the exact update scope and a newly qualified immutable image containing the
administration entrypoint, then permits the exact CloudFormation additions and
modifications required to separate administrator, ordinary-migration, and
runtime access.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-database-permission-surface/script.sh --receipt "$receipt" --rollback-receipt "$rollback_receipt" --rollback-compatibility-id "$rollback_compatibility_id" --json
```

Before it executes, the controller re-observes the current healthy stack,
service, budget, foundation alignment, and qualified image. It requires the
reviewed change set to add exactly the administration security group, private
network routes, ordinary migration secret, administrator role, and
administrator task definition; and to modify exactly the endpoint policy,
ordinary migration role and task definition, image-bound service task
definitions, and service rollout. It rejects any database, existing
administrator-secret, public-route, target, deletion, or unrelated resource
change. A lost controller response is reconciled through the named change set
and stack before another mutation; it is never treated as permission to
resubmit an update.

The update is not acceptance. It only makes the isolated administrative task
available. Continue with the administration, ordinary migration, effective
privilege, server/verifier, recovery, and retained-receipt proofs below.

#### Review packet and handoff boundary

The parent release coordinator supplies two immutable package-custody receipts:
`$candidate_receipt` for this new image and `$rollback_receipt` for the prior
accepted persistence-capable image. The latter is never the dependency-free
bootstrap image. The coordinator must retain the JSON reports produced below,
because each successful controller reports its durable proof-receipt path.
Before a fresh verifier phase, set its predecessor to the last completed report's
`facts.operation_id` for the **same mode**. Use `none` only when that mode has no
prior reservation. In the examples, `previous_read_operation` selects that read
predecessor. Preserve the exact arguments when continuing an interrupted phase;
those arguments reconcile the same reservation and cannot submit another task.
When the credential-lifecycle controller runs a verifier internally, consume its
`facts.verifier_operations.read.operation_id` or
`facts.verifier_operations["health-ready"].operation_id` as the next same-mode
predecessor. Its child handoff also retains the task ARN and proof-receipt path.

```bash
# 1. Provider surface: one reviewed UPDATE only.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-database-permission-surface/script.sh --receipt "$candidate_receipt" --rollback-receipt "$rollback_receipt" --rollback-compatibility-id "$rollback_compatibility_id" --json > permission_surface_report.json

# 2. Identities and structural schema, then the narrow runtime DML grant.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation bootstrap-identities --json > administration_bootstrap_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation confirm-runtime-iam-access --json > initial_identity_access_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh --json > migration_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation grant-runtime-application-access --json > administration_grant_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation prove-effective-privilege --json > effective_privilege_report.json

# 3. Meaningful server-mediated persistence and retained-data replacement.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode create --json > create_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh --receipt "$candidate_receipt" --json > replacement_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode read --new-operation --expected-operation "$previous_read_operation" --json > replacement_read_report.json

# 4. IAM identity revocation, replacement, and recovery.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$candidate_receipt" --operation revoke-and-recover --json > revocation_recovery_report.json

# 5. Isolated database restore proof. Image rollback is a separate compatibility
# decision: do not restore an image across a changed permission contract.
```

#### Migration interruption or unsuccessful completion

Do not rerun an unsuccessful, timed-out, or interrupted migration merely
because its task has stopped. First reconcile that task through the named
migration controller. If the outcome remains non-accepted, use the separate
read-only administrative observer. It compares the reviewed immutable manifest
with the migration-history table and writes a durable receipt. Only its
`PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED` result permits a later fresh
migration submission; an already-applied, partial, changed, or unavailable
history remains a release block and needs governed review.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation observe-migration-state --json > migration_state_observation_report.json
```

At the update boundary ECS replaces the image-bound service task. The service
is not acceptable merely because it is running: its private readiness and a
meaningful verifier operation must pass after the administration/migration/
grant sequence. The database remains private and retained; this route neither
replaces the RDS instance nor rotates the retained master secret. Its only new
database access path is the one-shot administration task.

Use the existing isolated-restore commands with one explicitly named recovery
snapshot after the retained synthetic record exists. The restore controller
writes the `isolated-restore` receipt and removes only the derived restored
database. Then give the acceptance collector the exact paths reported by the
controllers, all under
`infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/proof-receipts/`:

The derived restore must export its PostgreSQL and `iam-db-auth-error` logs.
If its verifier rejects, the controller makes one bounded, read-only
observation of both target-owned exports over the verifier's execution window.
It retains one closed classification with an honest `complete`, `empty`,
`unrecognized`, `malformed`, or `incomplete` observation, or an `unavailable`
or `failed` collection state, in the governed operation diagnostic; it never
prints, commits, or stores a raw server event, log stream, endpoint,
credential, or provider error. A missing or delayed export does not make the
verifier successful and does not authorize a new task: reconcile the same
operation first. This diagnosis supports correction; only an accepted verifier
receipt can prove recovery.

For a failed connection, the deployment chat may use the separate bounded mode
below after explicit task-launch and temporary-access authority. It targets the
positively tagged restored incarnation derived from this snapshot and retained
record proof. It launches at most one diagnostic task for that incarnation,
grants only its restored-instance runtime identity, runs separate TCP/TLS probes
and a driver connection plus `SELECT 1`, and removes temporary access after all
related tasks stop. A running diagnostic beyond 120 seconds can be stopped only
by this controller for its exact owned task. Existing `cleanup` observes both
recovery and diagnostic tasks before deleting the disposable database.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation diagnose-connection --snapshot-id "$snapshot" --record-proof-receipt "$record_proof_receipt" --json
```

The same command with `--observe-only` performs bounded reads without launching,
granting, stopping or revoking access. Each invocation reads at most three log
pages/observations per stream; each provider call retains its existing 30-second
process timeout. Delayed logs are reconciled against the same task, without
replaying it. A durable launch reservation survives interruptions and ECS task
retention expiry; absence of a discoverable task after reservation blocks
relaunch, IAM revocation and disposable-database deletion until the launch
outcome is resolved through governed observation or owner escalation. A local
exclusive controller lock serializes launch/access/cleanup decisions in this
checkout; it is not a distributed lock across operator checkouts. The deployment
chat remains the sole live execution owner. Policy removal requires the exact
restored-incarnation policy; a later foreign policy is left untouched. Collection/write failures preserve the
original safe verifier code and child status. Historical two-field results and
new typed v2 results remain readable. No diagnostic result is recovery evidence,
a release promotion, or proof that the underlying connection fault is repaired.
This chat implements/tests the route locally; live RDS execution stays with the
deployment chat using the merged revision and newly qualified verifier image.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.sh --inputs "$acceptance_inputs" --write-candidate --json
```

This command creates an immutable verified candidate record. It does not
overwrite the current accepted release. Validate the existing current reference,
then promote the candidate with its exact predecessor id:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/release-succession/script.sh --operation validate-candidate --evidence-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence --candidate-record "$candidate_record" --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/release-succession/script.sh --operation validate-current --evidence-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/release-succession/script.sh --operation promote --evidence-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence --candidate-record "$candidate_record" --expected-predecessor "$current_release_id" --json
```

The first command reports `$current_release_id`; the collector reports
`$candidate_record`. The promotion archives the candidate and atomically moves
only `current-accepted-release.yml`. Never edit legacy or archived records
manually.

The present persistence history records `legacy-not-recorded` permission facts.
It is therefore not a compatible rollback predecessor for the separated
administrator/migration design. Do not omit the four rollback receipts or use
`--permission-baseline`: that route deliberately fails until a separately
reviewed exception establishes a safe acceptance boundary. The live packet is
otherwise ready, but promotion is intentionally blocked at this decision rather
than restoring the old broad credential/privilege model.

Any controller interruption is a stop-and-reconcile boundary. Reconcile the
exact task/change-set identifier reported by that controller; the read-only
administration observations also reuse an exact retained receipt for the
current task definition and image. Do not submit a second update, rerun an
uncertain migration, rotate another secret version, or delete the candidate.
If the provider update itself fails or cannot be
observed as stable, preserve the database and stack for diagnosis. If a later
image rollback is needed, use the qualified-release rollback only after
checking schema and permission-contract compatibility; it restores an image,
not a database state. The historical persistence release predating separated
administrator/migration identities is not an automatic rollback candidate:
rolling it back could reintroduce broader credentials or grants.

### Durable completed-proof receipts

Each successful administration task, migration, private verifier, controlled
replacement, and isolated-restore verifier writes an allowlisted machine-readable receipt under
the scope's `30-release-evidence/proof-receipts/` directory before it reports
success.  A receipt contains only target/scope identity, proof operation,
terminal task/task-definition/image identity, timestamps, exit state, safe
result code, bounded non-secret context, controller provenance, and a
canonical payload digest.  It never contains a secret, connection string,
provider error text, or unbounded diagnostic payload.

Acceptance consumes those validated receipts for completed historical tasks,
so normal ECS stopped-task expiry does not erase already validated proof.  It
still independently observes current service/image/database/budget state and
restore cleanup.  Do not edit or recreate a receipt: a digest mismatch,
unknown field, conflicting task context, wrong target/image, missing terminal
fact, or invalid sequence blocks acceptance.  If a proof completed before
this control existed and no equally complete provider observation was retained,
repeat only that governed proof and let its controller capture the receipt.

An image change normally requires new receipts for every proof that executes
that image. The only narrow exception is a record created by
`qualify-proof-applicability`: it binds two qualified package receipts, retains
them under the target evidence root, recomputes the exact Git source delta, and
allows reuse only when that delta is confined to the isolated restore-verifier
entrypoint and its controller/tests/evidence. It never permits reuse of the
isolated-restore proof itself, current health, or a proof after a dependency,
template, permission, configuration, Dockerfile, or shared runtime change.
The acceptance input records the explicit path; a null value means ordinary
same-image receipt matching remains mandatory.

Run the bounded administrative bootstrap first. It is the only task permitted
to create or alter bounded login roles, transfer ownership, or grant/revoke
runtime application access. It never sets an application password or emits a
credential verifier. The existing CloudFormation logical
identifier `MigrationCredentialsSecret` is the retained RDS-master secret for
backward-compatible stack updates; from this transition onward it is injected
only into this administrator task, never into an ordinary migration or server.
The administrator creates the ordinary migration and runtime logins,
pre-provisions the schema under the migration owner, and removes broad runtime
grants. A timeout, non-zero completion, or lost controller observation blocks
the transition and requires fresh state observation; it must not be replayed.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation bootstrap-identities --json > "$administration_report"
```

Then run exactly one ordinary migration task. It has structural access only in
the already-administrated schema: it cannot administer login roles or create
schemas elsewhere in the database. A migration timeout, non-zero completion or
lost controller observation blocks acceptance and needs a fresh database-state
observation; it must not be replayed automatically.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh --json > "$migration_report"
```

The controller flushes a safe operation receipt to stderr before task submission
and emits one final JSON report on stdout. Retain both streams. If interrupted,
do **not** invoke the no-argument command again. Reconcile the already-submitted
task. If its ARN was lost, use the emitted operation ID with
`--reconcile-operation "$operation_id"` instead of `--reconcile-task`.
That route searches running and stopped tasks and never launches a replacement;
missing or ambiguous discovery remains `uncertain`. Discovery uses family and
status filters, then checks `startedBy` on described tasks; AWS requires
[`startedBy` to be the only ListTasks filter](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ListTasks.html),
so it is never combined with a desired-status filter.
The control accepts it only when its task ARN belongs to this target cluster,
its task definition matches the current candidate, it is terminal, it exited
successfully within the declared deadline, and its safe acceptance log is
present. Otherwise it blocks and release acceptance remains blocked.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh --reconcile-task "$migration_task_arn" --json > "$migration_report"
```

Then run the fixed private verifier through the service. It has no database
credential and no database network route. `create` proves a meaningful server
write/read path; `read` proves retained data after a controlled server
replacement; `cleanup` is only used after the retention/recovery proof permits
removal of the synthetic record.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode create --json > "$create_report"
```

If the verifier controller is interrupted after task submission, do **not** run
another verifier blindly. Reconcile the exact task only, or use its pre-submission
stderr receipt's `--reconcile-operation "$operation_id"` if the ARN was lost. The command requires
the current verifier task definition, terminal status, successful completion
within the declared deadline, no direct database credential, and the expected
mode-specific safe acceptance log.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode create --reconcile-task "$verifier_task_arn" --json > "$create_report"
```

Do not call this candidate accepted until the separate replacement, schema
compatible release rollback, and isolated database restore rehearsals are
implemented and their evidence is recorded. Initial creation, a successful
migration, and a private create/read proof establish a candidate only.

## Isolated Native Database Restore

Create one named encrypted recovery point after the retained synthetic record
and release/replacement evidence exist. Supply `--record-proof-receipt` with a
retained successful `verify-candidate` create/read receipt for the exact record.
The controller requires the record observation to finish no later than the
snapshot's original creation time (or creation time when no original time is
present). It also matches the source database resource ID and rejects a proof
from before the current source database incarnation. An earlier snapshot from
the same day therefore blocks before provisioning; the bounded suffix permits
a fresh follow-up snapshot after the record exists. The recovery point is native RDS
evidence, not a source-database mutation. The restoration route derives its
temporary database identifier from that snapshot; it restores it in the same
private subnets but with a distinct security group. Its one-shot verifier gets
the ordinary runtime credential and can reach only the restored copy, never
the source database. After initial submission, reconcile with the same operation
and snapshot identifier **plus `--observe-only`**. This mode performs no restore,
task launch or deletion, even when discovery has not caught up or retained task
evidence has expired. The command never chooses a new snapshot, target,
database, or task identity. Preserve accepted proof before temporary task
discovery expires; missing proof requires governed diagnosis, never replay.

```bash
snapshot=kanbien-core-platform-persistence-recovery-YYYYMMDD-<bounded-rehearsal-suffix>
record_proof=<retained-create-or-read-proof-receipt-path>
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/create-recovery-point/script.sh --snapshot-id "$snapshot" --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/create-recovery-point/script.sh --snapshot-id "$snapshot" --observe-only --json
# Continue only after that same snapshot is observed available:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation restore --snapshot-id "$snapshot" --record-proof-receipt "$record_proof" --json
# Re-observe the existing operation without submitting it again:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation restore --snapshot-id "$snapshot" --record-proof-receipt "$record_proof" --observe-only --json
# Once that database is ready, submit its one-shot verifier:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation verify --snapshot-id "$snapshot" --json
# Reconcile that existing verifier until its strict task-bound evidence is accepted:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation verify --snapshot-id "$snapshot" --observe-only --json
# Retire only that derived temporary database after the evidence is retained:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation cleanup --snapshot-id "$snapshot" --json
```

The first verifier launch waits for one bounded restoration-identity
stabilization interval after the exact temporary `rds-db:connect` policy is
observed. It then requires IAM's policy simulator to report `allowed` for that
exact task role, action, and restored-instance resource before submitting the
task. A missing simulator observation or any non-allowed result blocks before
task launch; the policy-write timestamp alone is insufficient. This covers the
controller's IAM authorization boundary without retrying a verifier that has
already run. An unsuccessful verifier remains a failed completion: collect its
closed safe result, clean up the derived database, diagnose through governed
controls, and start a fresh rehearsal only after the correction is reviewed.

New restores retain source, snapshot, record and proof-digest tags. Continue
with the same snapshot and record receipt; existing resources with absent or
mismatched tags cannot establish that rehearsal, and observation never submits
another restore. Snapshot time and immutable source identity follow the
[AWS DBSnapshot response contract](https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DBSnapshot.html).
Simulated receipts cannot authorize the ordinary restoration path. Previously
retained genuine restore receipts remain valid historical acceptance evidence.

Cleanup reports `pending` while the exact database is deleting and does not
submit deletion again; re-observe with `--operation cleanup --observe-only`.
The recovery-point control likewise re-observes its exact snapshot and separates
creating, failed, available and unknown outcomes. A restore-verifier task must
match the current database incarnation, task definition, started-by identity,
and expected record overrides; only a parsed accepted JSON record in that task's
log establishes proof. Missing logs remain pending evidence without rerunning a
completed task. Cleanup refuses a still-running verifier. The shared ECS task
evidence parser permits the captured empty `inferenceAcceleratorOverrides`
default, while command, role, resource and environment differences still fail.
The [ECS override contract](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_TaskOverride.html)
and the sanitized `fixtures/ecs-captured-responses.yml` fixture document that
provider boundary; derived restore fixtures are explicitly simulated.

The restore verifier requires a qualified image containing its reviewed
entrypoint and the corresponding provider control surface. Until both are
live, the operation blocks; it does not repurpose the normal server-mediated
verifier or direct the migration task at a restored database.

## Controlled Server Replacement

After `create` has retained the synthetic record, replace exactly the current
healthy candidate server task. This command cannot select another target,
service, or task. It requires a matching qualified receipt and live target
budget, binds the actual task-definition image and source revision plus the
running OCI digest to that receipt before any stop, records the original and
replacement task identities, and stops if ECS
does not restore one distinct healthy task using the unchanged candidate task
definition. It does not create or read a record itself: follow it with a fresh
private `read` verifier so the data-survival evidence is explicit. Set
`previous_read_operation` from the previous read report's `facts.operation_id`,
or `none` for the first read. A retained `historical-completion` result is retry
evidence, not a new observation after the replacement.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh --receipt "$receipt" --json > "$replacement_report"
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode read --new-operation --expected-operation "$previous_read_operation" --json > "$replacement_read_report"
```

## Runtime IAM Authentication and Urgent Revocation

The server receives no database password. Its ECS task role renews AWS
credentials through the provider; the adapter generates a fresh short-lived
RDS IAM token for each new database connection. Normal token expiry does not
require replacing a healthy server, and an existing database session remains
valid until it closes or an urgent revocation deliberately terminates it.

Urgent revocation is a separate, bounded exercise. The administrator task
first removes `rds_iam` membership, disables login, and confirms termination
of every active runtime session. ECS then starts a replacement with the denied
identity; it must remain live but not ready. Recovery verifies the role has
not acquired structural privilege, restores only login plus IAM membership,
replaces the server, and repeats ready/read proof. No verifier or migration is
replayed merely because access changed.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation revoke-and-recover --json
```

If the independently reconciled revocation task and its live-but-not-ready
proof have already completed but the controller was interrupted before recovery,
use the continuation below. It first re-proves denied readiness, then restores
only the governed IAM identity and a replacement task; it never replays the
revocation or a completed migration.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation recover-after-revocation --json
```

The outer identity-lifecycle report preserves the child controller's safe
checkpoint and `pending`, `failed` or `uncertain` outcome, including a timeout
while its response is captured. Reconcile that child's task before moving to
the next existing continuation; never restart the whole revocation merely
because a child observation was interrupted. This command creates no new
persistent AWS resource and never prints or records a password, token, or
verifier; only task identities and bounded safe result codes become evidence.

## Qualified Persistence Image Transition

The only governed route for a persistence-capable image update or compatible
rollback is receipt-bound and permits CloudFormation to alter only ECS task
definitions and the candidate service. It rejects database, secret, role,
network, or target changes. `rollback` requires an earlier qualified
persistence receipt and a predecessor whose permission contract is explicitly
compatible; the dependency-free bootstrap image and a predecessor with unknown
legacy permission facts are never eligible persistence rollbacks.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh --receipt "$release_b_receipt" --operation update --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh --receipt "$release_a_receipt" --operation rollback --rollback-compatibility-id "$rollback_compatibility_id" --support-receipt "$release_b_receipt" --json
```

After an interrupted update or rollback, repeat the same operation and receipt
with `--reconcile`. It observes only that named change set and its stack; it
never creates or executes a change set. Pending changes, terminal rollback
failure and missing observations are distinct. Completed updates require exact
current digest/source parameters before reporting `transitioned`.

## Failed Creation Cleanup

An initial candidate that never reaches acceptance may roll back until RDS
deletion protection stops CloudFormation. Do not manually remove resources or
reuse the failed stack. Once the named stack is `ROLLBACK_FAILED`, the database
is the exact target-tagged candidate instance, and the candidate service has
zero desired, running and pending tasks, the fixed cleanup command first
removes deletion protection from that failed candidate only and retains its
exact stack ARN in a safe receipt. Observe that identity, then use the explicit
continuation to advance to deletion after repeating database ownership and
service quiescence checks. It never repeats an unlock or a deletion already
observed in progress. CloudFormation's snapshot retention policy remains
required; the controller's deletion result is not proof that a final native
snapshot is available, so retain separate recovery-point evidence. Even an
observed `DELETE_COMPLETE` remains `pending` with `stack_deletion: confirmed`
and `final_snapshot_proof: separately-required`; this controller cannot report
full retirement or recovery completion without that separate required proof.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.sh --approved-failed-stack kanbien-core-platform-core-server-persistence --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.sh --approved-failed-stack kanbien-core-platform-core-server-persistence --reconcile-stack-id "$retirement_stack_id" --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.sh --approved-failed-stack kanbien-core-platform-core-server-persistence --continue-stack-id "$retirement_stack_id" --json
# Observe the same retained ARN until DELETE_COMPLETE; never resubmit deletion.
```

If the control cannot prove the failed state, exact target tag, quiesced
service, protected database, post-unlock observation, or stack deletion, it
blocks without substituting a manual cleanup procedure.

## Dedicated Observability MVP Activation

The first observability proof uses a separate private collector service, not a
sidecar sharing the server's RDS-capable task role. After both the server and
collector are qualified from the same source revision, the only activation
route is the controller below. It accepts a target-only notification address
at execution time; that address is never stored in the repository.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-observability-mvp-surface/script.sh --server-receipt "$server_receipt" --collector-receipt "$collector_receipt" --alert-email "$alert_email" --json
```

Before creating a named UPDATE change set, the controller requires the
declaration and package gates, healthy server, target budget, aligned
foundation, clean immutable server and collector images, and matching source
revisions. Its review permits only the enumerated collector identity, private
OTLP route, non-secret configuration, alarms, notification topic and
subscription, collector task/service, and server task/service update. Any
database, secret, broad permission, public route, or unrelated resource
change blocks the operation. A lost response is reconciled through the same
digest-derived change-set name:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-observability-mvp-surface/script.sh --server-receipt "$server_receipt" --collector-receipt "$collector_receipt" --alert-email "$alert_email" --reconcile --json
```

This update only composes the delivery path. It is not observability
acceptance: the retained readiness-failure, alarm-notification, and recovery
receipts plus fresh service/database/cleanup observations remain required.

### Readiness Failure, Notification and Recovery Rehearsal

Run the one bounded controlled-failure sequence only after the target-owned
email subscription is confirmed. The controller first retains the completed
private verifier proof and matching metric/alarm observation; an interruption
therefore resumes from that receipt instead of revoking access again. The
operator records confirmation timestamps but never email content, recipient,
or notification payload. A confirmed subscription alone is not proof that the
failure notification was received.

```bash
# 1. revoke only the runtime IAM identity; retain the unready verifier,
#    readiness metric 0, and ALARM observation before returning.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.sh --receipt "$receipt" --operation prepare-failure --json

# 2. after the same ALARM notification has actually arrived, record only the
#    two factual confirmation timestamps and the retained failure receipt.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.sh --receipt "$receipt" --operation record-notification --failure-receipt "$failure_receipt" --subscription-confirmed-at "$subscription_confirmed_at" --operator-delivery-confirmed-at "$delivery_confirmed_at" --json

# 3. restore the limited IAM identity, replace the server, prove ready/read,
#    then retain readiness metric 1 and the recovered OK alarm observation.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.sh --receipt "$receipt" --operation recover --failure-receipt "$failure_receipt" --notification-receipt "$notification_receipt" --json
```

The three receipts live under the target's `30-release-evidence/observability-receipts/` directory. The existing accepted record and historic proof receipts stay immutable. A future acceptance collection consumes the receipt map alongside its fresh current-state observations; elapsed ECS stopped-task retention never justifies another failure exercise.

### Readiness Metric Delivery Repair

If the collector is already live and a reviewed declaration correction changes
only its allowlisted non-secret metric-export configuration, use the same
controller with the explicit repair mode:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-observability-mvp-surface/script.sh --server-receipt "$server_receipt" --collector-receipt "$collector_receipt" --alert-email "$alert_email" --repair-readiness-metric-delivery --json
```

The repair route requires the already-enabled target to retain the exact
qualified server and collector identities, source revision, and all other
current activation parameters; it also requires both services to be healthy
before a change set is created. Review admits exactly two modifications:
`ObservabilityCollectorTaskDefinition` and `ObservabilityCollectorService`.
It cannot add resources or change the server, database, network, IAM,
notification, alarms, image, or secret bindings. A lost response is observed
through the same named change set with `--reconcile` and the same repair flag.

## Bounded Private Verifier Route Correction

When a completed migration and healthy server prove that only the private
verifier-to-server route is absent, this fixed update control may apply one
reviewed addition: `VerifierEgressToServer`. It requires the current healthy
candidate, receipt, budget, package gates, and an UPDATE change set containing
only that one rule; it cannot update the image, database, credentials, target,
or any other resource.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-private-verifier-route-update/script.sh --receipt "$receipt" --json
```

After an interrupted private-route correction, pass the same receipt with
`--reconcile`; it observes the reviewed correction without creating or executing
it again. Both qualified image digests and every foundation parameter must
match before initial execution.

## Bounded Restoration Verifier Surface Correction

For an existing candidate missing the isolated restoration surface, the fixed
`apply-restoration-verifier-surface` control may add only its enumerated restore
security groups, network rules, execution role and task definition. For an
already-created restoration surface, its explicit `--mode egress` correction
may add only `RestorationVerifierRestoredDatabaseEgress`; `--mode image` may
modify only `CoreServerPersistenceRestorationVerifierTaskDefinition` to use a
new qualified image. It rejects every other logical resource, action, type,
parameter, source-database or credential change. The image mode preserves the
current service image, source revision, support image, observability settings,
database, and all other stack parameters; it is a verifier-support correction,
not an application release transition. It deliberately uses the stack's
deployed provider template rather than the current repository template: later
scope work must not be smuggled into this repair. If a prior image review from
the current template was rejected by this guard while still unexecuted, the
same command's explicit `--discard-rejected-image-review` mode may remove only
that named, unexecuted review after re-observing its complete parameter identity
and rejecting its resource shape. All modes preserve every other current stack
parameter and require one qualified restore image digest. This is a separate
approved provider correction, not permission to change the source database or
credentials.
Use the same receipt plus `--reconcile` after interruption; observation contains
no mutation. The normal CREATE includes this surface already.

## RDS IAM-Authentication Log-Export Reconciliation

The persistence template requires both `postgresql` and
`iam-db-auth-error` exports. The latter is needed to diagnose a rejected
restoration-verifier IAM database connection without treating application output
as provider evidence. CloudFormation can report an otherwise healthy stack
while the live RDS export set has drifted, so do not use an empty stack update
or an ad-hoc `modify-db-instance` command to repair it.

Use the target-bound controller below. It first observes the exact private
PostgreSQL instance and template declaration. If and only if PostgreSQL logging
is present and the sole required export missing is `iam-db-auth-error`, it
enables that one export, preserves all existing exports, and returns `pending`.
It never changes credentials, IAM, engine settings, networking, database data,
or the ECS service. A transitional RDS status or lost response is a
stop-and-reconcile boundary; `--reconcile` makes no provider mutation.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface/script.sh --json

# Repeat only this read-only observation until it returns reconciled.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/reconcile-rds-log-export-surface/script.sh --reconcile --json
```

Only after `reconciled` may a new isolated restore operation rely on the two-log
collector. The controller's observation is configuration evidence, not a
successful restore or an acceptance record.

## Applicable Controller Continuation Audit

All commands below belong to this workflow's existing persistence scope. Their
safe continuation preserves the original operation identity and existing effect
permissions. A `pending`, `failed`, or `uncertain` result never means acceptance.

| Controller | Observation or continuation boundary |
| --- | --- |
| `prepare-candidate` | Read-only preflight; offline declaration coverage precedes provider observation. |
| `create-change-set` | Same receipt with `--reconcile`; never resubmits the fixed CREATE. |
| `deploy-candidate` | Same receipt/change-set with `--reconcile`; never executes again. |
| `run-migration` | Exact `--reconcile-task` or pre-submission `--reconcile-operation`; no new task. |
| `verify-candidate` | Repeat the exact original invocation to reconcile its durable reservation. A fresh phase requires `--new-operation --expected-operation <last-same-mode-operation-id>` (`none` only for initial creation); retrying the identical predecessor reconciles that same successor. Retained completion is explicitly historical. |
| `create-recovery-point` | Same snapshot with `--observe-only`; absence stays uncertain. |
| `rehearse-isolated-database-restore` | Same operation/snapshot with `--observe-only`; no restore, launch or deletion. |
| `rehearse-server-replacement` | `--reconcile-original-task`; no second stop, and no reuse across task definitions. |
| `rehearse-runtime-credential-lifecycle` | Preserve the child checkpoint; reconcile the exact administration/replacement/verifier task, then follow the existing continuation boundary. |
| `transition-qualified-release` | Same operation/receipt with `--reconcile`; no repeated UPDATE execution. |
| `apply-private-verifier-route-update` | Same receipt with `--reconcile`; no repeated route update. |
| `apply-restoration-verifier-surface` | Same receipt with `--reconcile`; no repeated surface update. |
| `apply-observability-mvp-surface` | Same server/collector receipts with `--reconcile`; no repeated observability update. |
| `reconcile-rds-log-export-surface` | `--reconcile` only observes the exact target's required export set; it never repeats an in-flight RDS mutation. |
| `retire-failed-candidate` | Retained exact stack ARN with `--reconcile-stack-id`; explicit `--continue-stack-id` advances only the incomplete deletion stage after safety checks. |

The regression suite at
`scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/controller-regression.py`
uses synthetic provider responses to exercise these boundaries. It is local
controller evidence; it establishes no container qualification, CI result,
provider state, native snapshot availability or live recovery success.


## Acceptance route and retained evidence

The authoritative route is the scope's
`00-declaration/acceptance-route-contract.yml`. It binds the actual controller
arguments, fifteen required retained proofs, qualified candidate/rollback
identities, collector, accepted-record schema, owning validator, lifecycle
promotion and downstream gates. The generic declaration preflight checks this
template before package construction or provider mutation through each command's
read-only `--validate-arguments` capability. A missing required mode, collector,
schema or proof route blocks there; future live receipts are required only at
the acceptance stage.

After every run proof completes, retain a `deploy/acceptance-inputs/v1` manifest
with `target: kanbien-core-platform`, `scope: core-server-persistence`, and
`values` matching the route's typed inputs: the qualified candidate and rollback
receipts, the fifteen-name `proof_receipts` mapping, the three-name
`observability_receipts` mapping (`readiness-failure-observed`,
`readiness-alarm-notified`, `readiness-recovery-observed`), original/successor task
identities, exact recovery snapshot, successful retained source-record proof,
and a fresh `current_health_task` from an explicit new `health-ready` operation.
The route also retains a predecessor identifier for each fresh read/health phase;
use the preceding report for the same mode, including across credential recovery,
rollback and final current-state observation. A health predecessor is never a
read predecessor. The initial value is `none` only if that mode has no operation.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode health-ready --new-operation --expected-operation "$previous_health_operation" --json > "$current_health_report"
```

Require `facts.evidence_reuse: fresh-terminal-observation` for a new phase and
retain its operation ID and proof-receipt path before the next phase. A retry may
return the same `historical-completion`; that preserves its original timestamp
and does not establish a fresh current-state check.
Use paths to existing controller receipts. Missing ECS history is not permission
to synthesize a receipt or replay a completed mutation. The normal value of
`proof_applicability` is `null`: every required proof must bind directly to the
candidate's immutable image. It may name a target-owned applicability record
only when the `qualify-proof-applicability` command has preserved both package
receipts and proven the exact source delta is restore-verifier-only. That record
can reuse only its closed allowlist of unaffected predecessor receipts; it
cannot carry an isolated restore proof or replace any fresh provider observation.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.sh --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml --inputs "$acceptance_inputs" --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.sh --inputs "$acceptance_inputs" --write --json
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/validate-accepted-release/script.sh --record infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/30-release-evidence/accepted-release.yml --json
```

The collector validates historical receipts offline and separately observes
fresh readiness, deployed immutable identity, database/snapshot binding, budget
and removal of the temporary restoration database. It refuses to overwrite an
existing accepted record. Retained receipt integrity is not an attestation of
trust: provenance must be genuine live controller observation. The existing
accepted record and its fifteen receipts remain usable unchanged after ECS
stopped-task expiry; new collection still requires the fresh observations.

For a newly accepted candidate, follow the provider-neutral
`govern-scope-lifecycle.md` promotion command and then the route's inventory and
target-declaration gates. The local regression wrapper
`scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/acceptance-route-rehearsal/smoke-test.sh`
exercises actual controller receipt capture, collection, record validation,
promotion and downstream validation with controlled observations. Its temporary
records are explicitly simulated and are rejected by production validation.

## Executable delivery boundaries

All supported candidate provider calls first require the generated local
`inventory-deploy-control --delivery --check` result. Missing registration or
runtime declarations block before provider observation. The actual Python
controllers enforce this as well as their shell wrappers.

Before a permission-surface change, the proposed current configuration and
permission contracts must already have an immutable rollback compatibility
record through the release-succession owner. Supply its identifier and the exact
retained rollback receipt; missing, stale, altered or differently bound evidence
blocks before change-set creation. A rollback also requires a qualified support
receipt matching the current support-image digest, so it cannot restore old
administration or migration programs. Selecting a retained image with the
`update` label cannot bypass compatibility checks.

Permission changes support `--reconcile` with the same candidate receipt. This
is observation-only, including failed or absent change sets. Failed reviews are
retained for diagnosis; the controller does not delete and recreate them.

Isolated restore cleanup requires independently observed database absence,
absent temporary IAM authority, and no active verifier tasks. If the database is
already absent, the bounded verifier family still must be observable. Pending,
denied, partial or unknown observations never become `cleaned-up`.
