<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
version: 1
status: active
created_on: "2026-10-23"
updated_on: "2026-10-23"
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

Then run the fixed private verifier through the service. It has no database
credential and no database network route. `create` proves a meaningful server
write/read path; `read` proves retained data after a controlled server
replacement; `cleanup` is only used after the retention/recovery proof permits
removal of the synthetic record.

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/verify-candidate/script.sh --mode create --json > "$create_report"
```

Do not call this candidate accepted until the separate replacement, schema
compatible release rollback, and isolated database restore rehearsals are
implemented and their evidence is recorded. Initial creation, a successful
migration, and a private create/read proof establish a candidate only.

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
