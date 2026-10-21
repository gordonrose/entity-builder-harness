<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.workflow.kanbien-core-platform-bootstrap-runtime-release
version: 3
status: draft
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
  path: .agentic/04.deploy/workflows/release-update-and-recovery.md
-->
# Review and Execute ECS Runtime Update

Use this workflow only for the fixed `kanbien-core-platform` bootstrap-runtime
scope. Follow the provider-neutral release-update-and-recovery workflow first.

## Before Any Provider Mutation

Run the runnable-program, package-custody, image smoke, target declaration,
and release-contract checks. Then run:

```bash
bash scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/validate-cost-condition/script.sh --json
```

It accepts only live verified cost evidence or an explicit, unexpired
target-local waiver with the declared compensating controls.

## 50 Deploy: Prepare and Execute the Bounded Update

1. Run `prepare-candidate` with a qualified receipt and `--operation update`.
2. Create a fixed UPDATE change set and review its task-definition/service-only
   resource boundary.
3. Under explicit AWS authority, execute the exact approved change set.

## 60 Run: Verify and Accept the Candidate

1. Run private verification using the same qualified receipt. A repeated
   verification command reuses only completed, accepted verifier evidence from
   that runtime update; it must never create a duplicate verifier task.
2. Record acceptance only after the verification report agrees with the receipt.

## 60 Run: Restore a Rejected Candidate

On rejected candidate verification, use `restore-accepted-release` to
   prepare a reviewed restoration; execute only under explicit AWS authority,
   then privately verify the retained release.

The `Target` cost-allocation condition must be verified or covered by a fresh,
explicit, unexpired waiver before any AWS mutation. The protected GitHub
environment controls package publication approval separately.

Evidence output is the qualified receipt, reviewed change-set report, deployment
report, private-verification report, accepted-release record, and any
restoration report. No command may select another account, region, target,
stack, or image tag.
