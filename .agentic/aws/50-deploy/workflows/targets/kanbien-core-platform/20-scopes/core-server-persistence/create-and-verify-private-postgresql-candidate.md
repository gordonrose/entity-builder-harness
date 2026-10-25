<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
version: 1
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

Review the fixed CREATE change set. It may create only the declared private
RDS, Secrets Manager, ECS, IAM, Cloud Map, security-group and Secrets Manager
endpoint resources. Verify its digest and source revision match the receipt,
the target tag is present, public access is absent, and the retention/deletion
controls match the template. Execute only the exact returned change-set name:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/deploy-candidate/script.sh --receipt "$receipt" --approved-change-set "$change_set" --json
```

The command may take time for RDS creation. A failed wait or interrupted
response is an uncertain provider operation: inspect that named stack through
the governed AWS state workflow before any further mutation. Do not delete,
retry, or submit another change set merely because a client response was lost.

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

If the controller is interrupted after submitting a task, do **not** invoke the
no-argument command again. Reconcile only the exact already-submitted task.
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
another verifier blindly. Reconcile the exact task only. The command requires
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
and release/replacement evidence exist. The recovery point is native RDS
evidence, not a source-database mutation. The restoration route derives its
temporary database identifier from that snapshot; it restores it in the same
private subnets but with a distinct security group. Its one-shot verifier gets
the ordinary runtime credential and can reach only the restored copy, never
the source database. A controller interruption is reconciled by repeating the
same operation and snapshot identifier; the command never chooses a new
snapshot, target, database, or task identity.

```bash
snapshot=kanbien-core-platform-persistence-recovery-YYYYMMDD-<bounded-rehearsal-suffix>
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation restore --snapshot-id "$snapshot" --json
# Re-observe until the same named temporary database is ready, then:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation verify --snapshot-id "$snapshot" --json
# Retire only that derived temporary database after the evidence is retained:
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-isolated-database-restore/script.sh --operation cleanup --snapshot-id "$snapshot" --json
```

The restore verifier requires a qualified image containing its reviewed
entrypoint and the corresponding provider control surface. Until both are
live, the operation blocks; it does not repurpose the normal server-mediated
verifier or direct the migration task at a restored database.

## Controlled Server Replacement

After `create` has retained the synthetic record, replace exactly the current
healthy candidate server task. This command cannot select another target,
service, or task. It requires a matching qualified receipt and live target
budget, records the original and replacement task identities, and stops if ECS
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

If the provider observer itself is interrupted after the denied-state proof,
the following explicit boundary may advance exactly one secret version. Its
`prepared` verdict requires the next action to be the matching administrator
rotation reconciliation; never invoke it again as a retry.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation recover-secret --json
```

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

## Failed Creation Cleanup

An initial candidate that never reaches acceptance may roll back until RDS
deletion protection stops CloudFormation. Do not manually remove resources or
reuse the failed stack. Once the named stack is `ROLLBACK_FAILED`, the database
is the exact target-tagged candidate instance, and the candidate service has
zero desired, running and pending tasks, the fixed cleanup command first
removes deletion protection from that failed candidate only, then deletes the
stack. CloudFormation retains its final native snapshot under the template's
snapshot policy; do not discard it as part of this control.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/retire-failed-candidate/script.sh --approved-failed-stack kanbien-core-platform-core-server-persistence --json
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
