<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.capability.foundation-access-update.readme
version: 1
status: draft
created_on: "2026-11-27"
updated_on: "2026-11-27"
layer: 04.deploy
domain: deployment.foundation-access
disciplines: [security, sre]
kind: readme
purpose: Explain the bounded repository observation permission update and its original-operation recovery boundary.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.capability.foundation-access-update
  path: scripts/04.deploy/lifecycle/50-deploy/capabilities/foundation-access-update/script.py
-->
# Foundation access update

Before publishing, the existing image publisher reads the repository's current
settings: tags must be immutable and new images must be scanned. The core delivery
role is missing the read permission needed for that check. This folder adds only
that permission to the existing role, through CloudFormation. It is not a general
IAM editor and cannot add another action, role, repository or resource.

[script.py](script.py) implements the operation; [smoke-test.py](smoke-test.py)
checks the same controller with a controlled provider and real disposable
reservation files. No test here contacts AWS. The
[workflow](../../../../../../.agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/10-foundation/update-delivery-observation-access.md)
owns approval and execution. The
[technical-access declaration](../../../../../../infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/technical-access.yml)
selects the one allowed change; existing target-profile data supplies the account,
region, foundation stack and template. No second target registry is introduced.

## How the pieces work

```text
committed source + declared permission
                ↓
plan: read current foundation and retain its fingerprints
                ↓
prepare: reserve once, create and review one change set
                ↓
execute: recheck, reserve once, submit that change set
                ↓
observe: original token + actual unchanged identities + exact new policy
```

A fingerprint is a hash of observed content. It lets later checks detect changes
without printing parameter values, role policies or provider errors. The retained
plan contains the exact source revisions and hashes; its own hash binds approval.
It is saved in the worktree's private Git directory, not as application evidence.

For example, `plan` returns a projected safe report shaped like:

```json
{"schema":"deploy/foundation-access-update-report/v1","verdict":"planned","code":"permission-update-plan-retained","plan_sha256":"<64 hexadecimal characters>"}
```

This example is illustrative, not a receipt from AWS. Under the owning workflow,
`prepare` and `execute` receive that exact hash through `--approved-plan-sha256`;
all operations use the same `--predecessor` full commit identity. Approval still
comes from the user/workflow, not from possessing the hash.

`source_delta` compares the entire old and new template, allowing only
`ecr:DescribeRepositories` in the selected repository statement. `make_intent`
captures actual foundation/role fingerprints. `control` reuses the existing
shared change-set and immutable-reservation owners; it does not implement a
second retry engine. `review` checks the actual change set and proposed template.
`observe_execution` checks the original execution token's terminal root event
and fresh role/resource/parameter readback. `main` exposes only plan, prepare,
review, execute and observe; no caller template, SQL, policy or provider endpoint
override is supported.

Every existing parameter is sent with `UsePreviousValue: true`. In particular,
the masked cost-alert address is never sent back as a replacement. A matching
masked readback cannot reveal the original secret; preservation is established
by the exact update request, not a claim to know the masked value.

## Failures and evidence limits

A lost create/execute response leaves its original reservation intact. The next
call observes that operation; it never submits again, even if the underlying
request might not have reached AWS. A failed guard after reservation is equally
observe-only. A missing event or failed read is uncertainty, not proof of absence.
Rollback is failure, and this command has no automatic inverse or repair mode.

Only one adoption intent exists for this declared permission. Different labels
or source revisions cannot silently evade an uncertain operation. New consumers
can reuse the shared reservation/change-set machinery; extending this controller
to another permission requires its own declaration and governed change, not an
arbitrary action parameter.

`failure_report` preserves the finite original condition through the existing
deployment diagnostic constructor. If constructing that explanation fails, the
original condition remains and diagnostic collection is marked unavailable.
Raw provider responses and failure text are not printed.

The local check covers exact changes, parameter preservation, approval mismatch,
response loss, duplicate submissions, malformed change sets, wrong lineage,
replacement readback and safe failures. It does not prove live ownership, actual
AWS permissions, package qualification or successful deployment. Those remain
separate workflow evidence, and a passing local fixture does not admit AWS access.
