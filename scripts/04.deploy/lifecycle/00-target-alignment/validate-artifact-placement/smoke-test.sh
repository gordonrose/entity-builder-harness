#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-artifact-placement
#   version: 4
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [agentic, architecture]
#   kind: script
#   purpose: Regression-test canonical deployment artifact path and naming validation.
#   portability: { class: reusable, targets: [entity-builder] }
#   used_by:
#   - id: deploy.script.validate-artifact-placement
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py
#   effects: [read-only]

ROOT="$(git rev-parse --show-toplevel)"
CHECK="python3 $ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-artifact-placement/script.py"

expect_pass() { $CHECK --kind "$1" --path "$2" --json >/dev/null; }
expect_fail() { if $CHECK --kind "$1" --path "$2" --json >/dev/null 2>&1; then echo "expected failure: $1 $2" >&2; exit 1; fi; }

expect_pass program-entrypoint infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts
expect_pass program-entrypoint infra/04.deploy/03.product/entrypoints/example-worker.handler.ts
expect_pass program-entrypoint infra/04.deploy/03.product/entrypoints/shared/scheduling/dispatch.ts
expect_pass program-build-contract infra/04.deploy/03.product/entrypoints/example-worker.tsconfig.json
expect_pass image-declaration infra/04.deploy/03.product/image/example-worker/Dockerfile
expect_pass image-declaration infra/04.deploy/03.product/image/example-worker/Dockerfile.dockerignore
expect_pass image-declaration infra/04.deploy/03.product/image/example-worker/image-contract.yml
expect_fail program-entrypoint infra/04.deploy/03.product/entrypoints/../outside.ts
expect_fail program-entrypoint infra/04.deploy/03.product/entrypoints/example.sh
expect_fail program-entrypoint infra/04.deploy/03.product/targets/example/worker.ts
expect_fail program-build-contract infra/04.deploy/03.product/entrypoints/example.json
expect_fail image-declaration infra/04.deploy/03.product/image/example-worker/implementation.py
expect_fail image-declaration infra/04.deploy/03.product/image/example-worker/nested/Dockerfile

expect_pass foundation-declaration infra/04.deploy/03.product/targets/example/10-foundation/network.yml
expect_pass scope-declaration infra/04.deploy/03.product/targets/example/20-scopes/server/00-declaration/declaration-contract.yml
expect_pass provider-template infra/04.deploy/03.product/targets/example/30-provider-realization/aws/cloudformation/server.yml
expect_pass release-evidence infra/04.deploy/03.product/targets/example/20-scopes/server/30-release-evidence/rehearsals/release-b-to-a-2026-10-21.yml
expect_pass generic-workflow .agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md
expect_pass aws-target-workflow .agentic/aws/60-run/workflows/targets/example/20-scopes/server/privately-verify-release.md
expect_pass lifecycle-script scripts/04.deploy/lifecycle/50-deploy/targets/example/server/review-and-execute-target-update/script.sh
expect_pass public-deploy-command scripts/04.deploy/commands/review-target-update/command.sh
expect_pass lifecycle-capability scripts/04.deploy/lifecycle/20-build/capabilities/source-qualification/receipt-validation/implementation.py
expect_pass target-capability-binding scripts/04.deploy/lifecycle/60-run/targets/example/server/bindings/source-qualification/receipt-validation/binding.py
expect_pass provider-adapter scripts/04.deploy/shared/provider-adapters/aws/change-set-submission/request/implementation.py
expect_fail generic-workflow .agentic/04.deploy/workflows/release-flow.md
expect_fail scope-declaration infra/04.deploy/03.product/targets/example/scopes/server/declaration-contract.yml
expect_fail provider-template infra/04.deploy/03.product/targets/example/30-provider-realization/aws/server.yml
expect_fail lifecycle-script scripts/04.deploy/lifecycle/50-deploy/targets/example/review/script.sh
expect_fail lifecycle-capability scripts/04.deploy/lifecycle/20-build/capabilities/source-qualification/implementation.py

expect_pass target-operation-script scripts/04.deploy/lifecycle/60-run/targets/example/server/task-execution/implementation/task-runner.py
expect_pass target-operation-script scripts/04.deploy/lifecycle/60-run/targets/example/server/task-execution/tests/task-runner-test.py
expect_pass target-operation-script scripts/04.deploy/lifecycle/60-run/targets/example/server/recovery-and-replacement/restore/restore-route.py
expect_pass retained-deploy-script scripts/04.deploy/legacy/kanbien-staging/assess-platform-shell-service-drift/drift_test.py
expect_pass retained-deploy-script scripts/04.deploy/legacy/rag-rulebook/verify-rag-rulebook-deploy-readiness/script.sh
expect_pass retained-deploy-script scripts/04.deploy/legacy/kanbien-staging/shared/provider-adapters/aws/cognito-provisioning.py
expect_fail target-operation-script scripts/04.deploy/lifecycle/60-run/targets/example/server/task-runner.py
expect_fail target-operation-script scripts/04.deploy/lifecycle/60-run/targets/example/server/task-execution/implementation/utils/task-runner.py
expect_fail retained-deploy-script scripts/04.deploy/legacy/verify/script.sh
expect_fail retained-deploy-script scripts/04.deploy/legacy/example/../current/script.sh
expect_fail retained-deploy-script scripts/04.deploy/lifecycle/60-run/targets/example/server/task-execution/commands/script.sh
expect_fail lifecycle-capability scripts/04.deploy/legacy/example/build/source-qualification/implementation.py

expect_pass cross-phase-standard .agentic/04.deploy/standards/operational-realization-gate.md
expect_pass cross-phase-workflow .agentic/04.deploy/workflows/operational-realization-gate.md
expect_pass aws-standard .agentic/aws/standards/operational-realization-applicability.md
expect_fail cross-phase-standard .agentic/01.harness/standards/operational-realization-gate.md
expect_fail cross-phase-workflow .agentic/04.deploy/50-deploy/workflows/review-and-execute-target-update.md
expect_fail aws-standard .agentic/04.deploy/standards/operational-realization-applicability.md
set +e
rejected="$($CHECK --kind 'https://private.invalid/argument-canary' --path ignored 2>&1)"
status=$?
set -e
[[ "$status" -eq 2 && "$rejected" == 'DIAGNOSTIC_CODE=ARTIFACT_PLACEMENT_ARGUMENTS_INVALID' ]]
