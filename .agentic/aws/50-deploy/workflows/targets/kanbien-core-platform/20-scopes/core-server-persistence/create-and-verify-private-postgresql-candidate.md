<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
version: 1
status: active
created_on: "2026-10-23"
updated_on: "2026-10-24"
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

Run exactly one migration task. It has the only structural credential. A task
timeout, non-zero completion or lost controller observation blocks acceptance
and needs a fresh database-state observation; it must not be replayed
automatically.

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
snapshot=kanbien-core-platform-persistence-recovery-YYYYMMDD
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

The migration credential remains the recovery identity.  The server receives
only the runtime secret and never refreshes it in place: a successful runtime
credential rotation writes a new secret version, uses the migration task to
apply the matching database role password, replaces the server task, then
requires both ready health and a meaningful retained-record read.  If the
migration outcome is uncertain after the secret advances, this route blocks;
it never blindly restores a secret version or replays a completed migration.

Urgent revocation is a separate, bounded exercise.  The migration task first
sets the runtime role to `NOLOGIN` and terminates sessions for that role.  ECS
then starts a replacement carrying the now-denied version; it must remain live
but not ready.  Recovery writes a new runtime secret version, applies the
matching role password through the migration identity, replaces the server,
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
`prepared` verdict requires the next action to be the matching `rotate`
migration reconciliation; never invoke it again as a retry.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-runtime-credential-lifecycle/script.sh --receipt "$receipt" --operation recover-secret --json
```

This command creates no new persistent AWS resource.  It never prints or
records a credential value: only secret-version identifiers, task identities,
and the bounded verifier/migration verdicts may become evidence.

## Qualified Persistence Image Transition

The only governed route for a persistence-capable image update or rollback is
receipt-bound and permits CloudFormation to alter only ECS task definitions and
the candidate service. It rejects database, secret, role, network, or target
changes. `rollback` requires an earlier qualified persistence receipt; the
dependency-free bootstrap image is never an eligible persistence rollback.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh --receipt "$release_b_receipt" --operation update --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh --receipt "$release_a_receipt" --operation rollback --json
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
