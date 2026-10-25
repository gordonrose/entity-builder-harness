<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
version: 4
status: active
created_on: "2026-10-23"
updated_on: "2026-10-25"
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

Follow `.agentic/04.deploy/standards/provider-async-conditions.md` for outcome
meaning. `failed` requires positively observed terminal failure; `uncertain`
retains the operation identity when observation cannot prove the result. Both
remain unaccepted. Do not delete, retry, or submit another change set merely
because a client response was lost. CREATE review requires the exact change-set
name, source revision, and both server and restore-verifier image digests.

## Run Proof

### Permission-separation update of an existing candidate

If the persistence candidate already exists and is healthy, do not use the
CREATE-only candidate controller or the image-only transition controller for
the privilege-separation change. The bounded route below is the only governed
update: it uses a newly qualified immutable image because it contains the
administration entrypoint, then permits the exact CloudFormation additions and
modifications required to separate administrator, ordinary-migration, and
runtime access.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-database-permission-surface/script.sh --receipt "$receipt" --json
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

```bash
# 1. Provider surface: one reviewed UPDATE only.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-database-permission-surface/script.sh --receipt "$candidate_receipt" --json > permission_surface_report.json

# 2. Identities and structural schema, then the narrow runtime DML grant.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation bootstrap-identities --json > administration_bootstrap_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-migration/script.sh --json > migration_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation grant-runtime-application-access --json > administration_grant_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/run-administration/script.sh --operation prove-effective-privilege --json > effective_privilege_report.json

# 3. Meaningful server-mediated persistence and retained-data replacement.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode create --json > create_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh --receipt "$candidate_receipt" --json > replacement_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode read --json > replacement_read_report.json

# 4. Rotation, urgent revocation, replacement, and recovery.
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$candidate_receipt" --operation rotate --json > rotation_report.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$candidate_receipt" --operation revoke-and-recover --json > revocation_recovery_report.json

# 5. Isolated database restore proof. Image rollback is a separate compatibility
# decision: do not restore an image across a changed permission contract.
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

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.sh --receipt "$candidate_receipt" --rollback-receipt "$rollback_receipt" --server-replacement-original "$original_task_arn" --server-replacement-successor "$successor_task_arn" --recovery-snapshot "$snapshot" --proof-receipt migration-apply="$migration_receipt" --proof-receipt effective-privilege="$effective_privilege_receipt" --proof-receipt server-replacement="$replacement_receipt" --proof-receipt server-replacement-read="$replacement_read_receipt" --proof-receipt credential-rotation="$rotation_receipt" --proof-receipt credential-revocation="$revocation_receipt" --proof-receipt credential-revocation-unready="$revocation_unready_receipt" --proof-receipt credential-recovery="$recovery_receipt" --proof-receipt credential-recovery-health="$recovery_health_receipt" --proof-receipt credential-recovery-read="$recovery_read_receipt" --proof-receipt rollback-b-health="$rollback_health_receipt" --proof-receipt rollback-b-read="$rollback_read_receipt" --proof-receipt rollback-final-health="$return_health_receipt" --proof-receipt rollback-final-read="$return_read_receipt" --proof-receipt isolated-restore="$restore_receipt" --write-candidate --json
```

This command creates an immutable verified candidate record. It does not
overwrite the current accepted release. Validate the existing current reference,
then promote the candidate with its exact predecessor id:

```bash
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
exact task/change-set identifier reported by that controller; do not submit a
second update, rerun an uncertain migration, rotate another secret version, or
delete the candidate. If the provider update itself fails or cannot be
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

Run the bounded administrative bootstrap first. It is the only task permitted
to create or alter login roles, set a password, transfer ownership, or
grant/revoke runtime application access. The existing CloudFormation logical
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
private `read` verifier so the data-survival evidence is explicit.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.sh --receipt "$receipt" --json > "$replacement_report"
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode read --json > "$replacement_read_report"
```

## Runtime Credential Rotation and Urgent Revocation

The administrator credential remains the recovery identity. The server
receives only the runtime secret and never refreshes it in place: a successful
runtime credential rotation writes a new secret version, uses the separately
governed administrator task to apply the matching database role password,
replaces the server task, then requires both ready health and a meaningful
retained-record read. If the administrative outcome is uncertain after the
secret advances, this route blocks; it never blindly restores a secret version
or replays a completed task.

Urgent revocation is a separate, bounded exercise. The administrator task first
sets the runtime role to `NOLOGIN` and terminates sessions for that role. ECS
then starts a replacement carrying the now-denied version; it must remain live
but not ready.  Recovery writes a new runtime secret version, applies the
matching role password through the administrator identity, replaces the server,
and repeats ready/read proof.  No completed verifier or migration is replayed
merely because a credential changed.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation rotate --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation revoke-and-recover --json
```

If the independently reconciled revocation task and its live-but-not-ready
proof have already completed but the controller was interrupted before it could
perform recovery, use the continuation below. It first re-proves denied
readiness, then performs only fresh credential recovery; it never replays the
revocation migration.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation recover-after-revocation --json
```

A secret write uses a generated request token as its version identity and emits
that non-secret token before submission. If its response was interrupted, use
only metadata observation; this does not generate or write another secret and
does not launch a verifier or migration:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation reconcile-secret --secret-operation-id "$secret_operation_id" --json
```

`prepared` means that exact version is current and the matching migration is
still required. An absent or superseded version is `uncertain`; never rotate
again as a substitute for observing the first write.

If the provider observer itself is interrupted after the denied-state proof,
the following explicit boundary may advance exactly one secret version. Its
`prepared` verdict requires the next action to be the matching administrator
rotation reconciliation; never invoke it again as a retry.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation recover-secret --json
```

The outer credential-lifecycle report preserves the child controller's safe
checkpoint and `pending`, `failed` or `uncertain` outcome, including a timeout
while its response is captured. Reconcile that child's operation before moving
to the next existing continuation; never restart the whole rotation or
revocation merely because a child observation was interrupted.

This command creates no new persistent AWS resource.  It never prints or
records a credential value: only secret-version identifiers, task identities,
and the bounded verifier/administrator verdicts may become evidence.

## Qualified Persistence Image Transition

The only governed route for a persistence-capable image update or compatible
rollback is receipt-bound and permits CloudFormation to alter only ECS task
definitions and the candidate service. It rejects database, secret, role,
network, or target changes. `rollback` requires an earlier qualified
persistence receipt and a predecessor whose permission contract is explicitly
compatible; the dependency-free bootstrap image and a predecessor with unknown
legacy permission facts are never eligible persistence rollbacks.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh --receipt "$release_b_receipt" --operation update --expected-predecessor "$current_release_id" --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh --receipt "$release_a_receipt" --operation rollback --expected-predecessor "$current_release_id" --json
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
security groups, network rules, execution role and task definition. It preserves
all other current stack parameters and supplies one qualified restore image
digest. It must reject any additional change. This is a separate approved
provider correction, not permission to change the source database or credentials.
Use the same receipt plus `--reconcile` after interruption; observation contains
no mutation. The normal CREATE includes this surface already.

## Applicable Controller Continuation Audit

All commands below belong to this workflow's existing persistence scope. Their
safe continuation preserves the original operation identity and existing effect
permissions. A `pending`, `failed`, or `uncertain` result never means acceptance.

| Controller | Observation or continuation boundary |
| --- | --- |
| `prepare-candidate` | Read-only preflight; offline declaration coverage precedes provider observation. |
| `create-change-set` | Same receipt with `--reconcile`; never resubmits the fixed CREATE. |
| `deploy-candidate` | Same receipt/change-set with `--reconcile`; never executes again. |
| `run-migration`, `verify-candidate` | Exact `--reconcile-task` or pre-submission `--reconcile-operation`; no new task. |
| `create-recovery-point` | Same snapshot with `--observe-only`; absence stays uncertain. |
| `rehearse-isolated-database-restore` | Same operation/snapshot with `--observe-only`; no restore, launch or deletion. |
| `rehearse-server-replacement` | `--reconcile-original-task`; no second stop, and no reuse across task definitions. |
| `rehearse-runtime-credential-lifecycle` | Preserve child checkpoint; reconcile exact child task or secret version metadata, then follow the existing continuation boundary. |
| `transition-qualified-release` | Same operation/receipt with `--reconcile`; no repeated UPDATE execution. |
| `apply-private-verifier-route-update` | Same receipt with `--reconcile`; no repeated route update. |
| `apply-restoration-verifier-surface` | Same receipt with `--reconcile`; no repeated surface update. |
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
receipts, the fifteen-name `proof_receipts` mapping, original/successor task
identities, exact recovery snapshot, successful retained source-record proof,
and a fresh `current_health_task` from `verify-candidate --mode health-ready`.
Use paths to existing controller receipts. Missing ECS history is not permission
to synthesize a receipt or replay a completed mutation.

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
