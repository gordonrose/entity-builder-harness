<!-- agentic-artifact:
schema: agentic-artifact/v3
id: aws.runbooks.platform-shell-staging-rollback
version: 1
status: active
created_on: "2026-07-13"
updated_on: "2026-10-26"
layer: 04.deploy
domain: infra.operations
disciplines:
- sre
kind: runbook
purpose: Define the Kanbien staging platform shell rollback procedure before first AWS deploy.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Platform Shell Staging Rollback

The supported service-change boundary is
`scripts/04.deploy/reconcile-platform-shell-staging/script.sh`. The guarded
`service-update` and `service-rollback` modes replace the former raw ECS
`update-service` instructions. The GitHub publication workflow remains an image
publisher; it does not deploy the service. Mutation still requires the current
explicit approval governed by `.agentic/aws/workflows/execute-approved-aws-change.md`.

Before a rollback, retain the current and selected historical manifests, the
published `platform-shell-package-custody-<run-id>` artifact, and the generic
accepted-release evidence root. Each manifest names repository-relative
`acceptance.evidence_root`, `acceptance.package_custody_receipt` and
`acceptance.current_observation` paths. The source commit, publication workflow,
run and image digest must agree with the captured custody receipt.

1. Inspect the accepted current reference and the selected retained release.
   Refresh the current service observation through the existing owner:

   ```bash
   bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh \
     --mode runtime-alignment --deployment-manifest <current-manifest> --json
   ```

   This proves current provider configuration, permissions, runtime health and
   image identity, captures immutable receipts and emits a verified candidate.
   It does not promote a release. An unchanged current accepted release can
   consume the fresh observation without rewriting its historical proof.

2. Produce an additive rollback compatibility decision for the retained image:

   ```bash
   bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
     --manifest <retained-manifest> \
     --record-rollback-compatibility <retained-release-id> --json
   ```

   Reuse succeeds only when the retained runtime/package receipts match the
   current configuration and permission source inputs exactly. A changed
   boundary requires separate governed qualification; it cannot be approved by
   editing an old receipt. The compatibility command does not advance current
   acceptance. First creation has no retained rollback target and cannot use
   this rollback path.

3. Review an image-only Service-stack change set with the compatible retained
   immutable image, preserving every other parameter and resource boundary.
   After explicit approval, execute through the guarded owner:

   ```bash
   bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh \
     --mode service-rollback \
     --deployment-manifest <retained-manifest> \
     --current-deployment-manifest <current-manifest> \
     --service-change-set <reviewed-change-set-id> \
     --expected-predecessor <current-release-id> \
     --rollback-compatibility-id <compatibility-id> \
     --realization-facts <fresh-normalized-facts> \
     --realization-change-summary <reviewed-change-summary> --json
   ```

   The command enforces package custody, accepted current state, fresh provider
   alignment, exact reviewed change-set scope and rollback compatibility before
   execution. Unsupported configuration, security or routing changes block.
   For an approved fresh candidate, use `--mode service-update` with its
   manifest and current predecessor; first creation uses predecessor `none`.

4. If the submission response is interrupted or uncertain, inspect the same
   change set before any retry:

   ```bash
   bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh \
     --mode service-operation-status --deployment-manifest <retained-manifest> \
     --service-change-set <reviewed-change-set-id> --json
   ```

   This mode only reads provider status. Pending, failed, absent and uncertain
   results are not successful deployment proof and do not authorize replay.

5. After provider completion, collect the selected release's actual current
   runtime observation, then promote the emitted candidate using the generic
   compare-and-swap boundary:

   ```bash
   bash scripts/04.deploy/reconcile-platform-shell-staging/script.sh \
     --mode runtime-alignment --deployment-manifest <retained-manifest> --json
   bash scripts/04.deploy/lifecycle/60-run/release-succession/script.sh \
     --operation promote --evidence-root <evidence-root> \
     --candidate-record <emitted-candidate-path> \
     --expected-predecessor <current-release-id> --json
   bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
     --manifest <retained-manifest> --json
   ```

   Promotion retains every predecessor and receipt. If interrupted after the
   archive write, retry the same candidate and expected predecessor; the
   generic owner resumes without overwriting history. Scope activation does
   not replace this release transition.

If rollback fails, retain the safe command result and the original failure.
Use read-only operation status and the existing diagnostic owner to establish
what occurred. A different image, changed security boundary or public-exposure
change requires its own reviewed change plan; do not bypass this route with a
raw service update or amend accepted evidence to describe an unproved outcome.
