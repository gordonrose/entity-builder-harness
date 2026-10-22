<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-bootstrap-runtime-release
version: 5
status: active
created_on: "2026-10-20"
updated_on: "2026-10-21"
layer: 04.deploy
domain: deployment.bootstrap-runtime
disciplines: [security, sre]
kind: workflow
purpose: Govern the fixed AWS update, verification, and restoration lifecycle for the kanbien-core-platform bootstrap runtime.
portability: { class: internal, targets: [] }
used_by:
- id: deploy.workflow.release-update-and-recovery
  path: .agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md
- id: deploy.workflow.verify-accept-or-restore-release
  path: .agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md
-->
# Review and Execute ECS Runtime Update

Use this workflow only for the fixed `kanbien-core-platform/bootstrap-runtime`
scope with its foundation and accepted runtime already established. Follow
`.agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md`,
then `.agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md`.
An absent stack or a new persistence/security scope needs its own governed
creation or expansion route; historical rehearsal plans are not that route.

## Readiness Before Starting a Release

Resolve the recorded worktree, installed dependencies, exact committed source
revision and usable credentials before publication. The fixed operator context
is profile `kanbien-dev`, account `337159794548`, region `eu-west-1`. Package
publication uses its separately declared GitHub OIDC role.

Distinguish repository writes, commit/push, protected publication approval,
change-set creation, execution and restoration authority. Reuse explicit
approval already granted for the same scope; ask only for missing authority.
Check available account capability before claiming that only the user can
approve a protected workflow. Do not bypass its gate. For unattended work,
resolve approval availability and provider-condition expiry before starting;
retain safe receipt, run, change-set and task references in existing evidence.

## Build and Package Prerequisites

Follow the lifecycle map's Build and Package workflows. Use public script
entrypoints, with their declared arguments, rather than internal helpers:

```bash
bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json
bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/script.sh --json
bash scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access/script.sh --json
bash scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh --json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/script.sh --json
```

The protected, main-only
`.github/workflows/publish-kanbien-core-platform-core-server.yml` owns actual
image qualification, publication, scan, SBOM, provenance and custody receipt.
It cannot deploy. Its image smoke command is
`scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh`.
Use the exact published source revision and immutable digest from its qualified
receipt; a later evidence commit does not change the image's source identity.

When image or target contracts change, the connected release-contract gate and
`scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh`
must continue to prove the learned runtime constraints: private image pulls
need S3 layer access as well as ECR, ECS preserves the image's non-root user,
distroless health checks use the absolute Node executable without a shell, and
the verifier command does not duplicate the inherited Node entrypoint.

## Before Any Provider Mutation

Complete the checks above, then run:

```bash
bash scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/validate-cost-condition/script.sh --json
```

This local validator accepts retained evidence of live cost verification or an
explicit, unexpired target-local waiver with the declared compensating controls.
It does not perform a live AWS check or establish verified-evidence freshness.
Confirm the applicable condition and recheck immediately before each mutation,
including a verifier task launch. An existing waiver does not authorize a new
service or cost category outside its boundary.

## 50 Deploy: Prepare and Execute the Bounded Update

Set `receipt` to the retained qualified receipt file. Preparation performs fresh
read-only alignment, including the retained accepted baseline:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate/script.sh --receipt "$receipt" --operation update --json
```

Under change-set creation authority, create the bounded UPDATE proposal:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.sh --receipt "$receipt" --operation update --json
```

Inspect its completed contents through `.agentic/aws/workflows/inspect-aws-state.md`.
Review the exact image/source identity and task-definition/service-only resource
boundary. Set `change_set` to that reviewed name. Under execution authority:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh --receipt "$receipt" --operation update --approved-change-set "$change_set" --json
```

The control rechecks the proposal and waits for completion. A failed wait is an
uncertain result requiring inspection, not permission to resubmit. AWS may omit
`ChangeSetType`; the control accepts that only with an independently proved
complete existing stack, and still rejects CREATE and in-progress stacks.

## 60 Run: Verify and Accept the Candidate

Under private-verifier task authority, use the same candidate receipt and retain
the JSON report in `verification_report`:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh --receipt "$receipt" --json > "$verification_report"
```

Require `runtime-digest-and-private-verifier-accepted`. For a normal accepted
update, check acceptance readiness, then repeat with `--write` under repository
write authority:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/accept-release/script.sh --receipt "$receipt" --verification-report "$verification_report" --json
```

The record must retain the full qualified custody reference, source, digest,
runtime/verifier identities, proof and valid artifact metadata. Record candidate
proof separately during an approved A-to-B-to-A rehearsal; keep A as the retained
baseline until restoration is proved.

## 60 Run: Restore a Rejected Candidate

Under restoration change-set creation authority, invoke:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/restore-accepted-release/script.sh --json
```

This creates a change set: it is not a dry run. It derives A's receipt from the
retained accepted record, so do not supply B's receipt or rebuild A.

After inspecting and approving that exact change set, invoke the same wrapper
with `--approved-change-set "$change_set" --json`. This executes the restoration
and runs private verification itself. Its output contains two JSON documents:
the deployment report followed by the private-verification report. Retain both,
and retain the single private-verification document separately for acceptance;
the acceptance command cannot read the combined wrapper output. Use A's retained
original qualified receipt and that verification report to reconcile the accepted
record with the final restored task identities, under repository write authority.
Do not launch another verifier merely to obtain a separate report file.

## Interrupted Operations

Use `.agentic/aws/workflows/inspect-aws-state.md` to inspect the existing change
set, stack, service rollout or verifier task before repeating a mutation. The
verifier reuses completed accepted proof for the same runtime update; it does
not automatically reconcile pending, running or concurrent verifier invocations.
A deterministic change-set name is not a general retry guarantee either.

If a tool response is interrupted, observe the original provider operation. Do
not launch a second verifier merely because the restoration wrapper's response
was lost. If the existing state cannot be reconciled through the governed read
route, stop that effect and report the precise uncertainty. Use existing logs
and receipts for these references; no application database is required.

The `Target` cost-allocation condition must be verified or covered by a fresh,
explicit, unexpired waiver before any AWS mutation. The protected GitHub
environment controls package publication approval separately.

Evidence output is the qualified receipt, reviewed change-set report, deployment
report, private-verification report, accepted-release record, and any
restoration report. No command may select another account, region, target,
stack, or image tag.
