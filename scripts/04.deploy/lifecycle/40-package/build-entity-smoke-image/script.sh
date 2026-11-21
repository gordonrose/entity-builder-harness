#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.build-entity-smoke-image
#   version: 2
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-20"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Build only the isolated feature image from a committed source checkpoint after declaration and local wiring checks.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: infra.04-deploy.entity-smoke.image.contract
#     path: infra/04.deploy/03.product/image/entity-smoke/image-contract.yml
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/04.deploy/shared/safe-command-diagnostics.sh
source scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh
entity_smoke_tag="kanbien-entity-smoke:qualification"
if [[ $# == 2 && "$1" == --tag ]]; then entity_smoke_tag="$2"; elif [[ $# != 0 ]]; then
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_ARGUMENTS_INVALID' >&2; exit 2
fi
[[ "$entity_smoke_tag" =~ ^kanbien-entity-smoke:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || {
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_ARGUMENTS_INVALID' >&2; exit 2;
}
# Session notes do not enter the image or executable governance. Every other
# tracked/untracked task input must belong to the immutable checkpoint.
if [[ -n "$(git status --porcelain --untracked-files=all -- . ':!commitLogs')" ]]; then
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_COMMITTED_SOURCE_REQUIRED' >&2; exit 1
fi
entity_smoke_source="$(git rev-parse HEAD)"
[[ "$entity_smoke_source" =~ ^[a-f0-9]{40}$ ]] || { printf '%s\n' 'ENTITY_SMOKE_IMAGE_SOURCE_INVALID' >&2; exit 1; }
candidate_image_prechecks infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes ENTITY_SMOKE_IMAGE_PROGRAM_INVALID 'The isolated program contract was not confirmed.' 'Inspect the program declaration without changing accepted programs.' python3 -B
safe_command_diagnostic ENTITY_SMOKE_IMAGE_DIAGNOSTICS_NOT_CONFIRMED package 'The source diagnostic contract check failed.' 'Regenerate code-owned catalog exports or correct their source before packaging.' -- \
  bash scripts/repo/diagnostic-coverage/verify.sh --unit catalog
safe_command_diagnostic ENTITY_SMOKE_IMAGE_FEATURE_NOT_CONFIRMED package 'The feature contract and use-case checks failed.' 'Correct the feature before image qualification.' -- \
  npm --ignore-scripts run app:entity-smoke:check
bash scripts/repo/check-selection/script.sh --checks entity-smoke-composition --task-paths infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml --record-preparation --json
safe_command_diagnostic ENTITY_SMOKE_IMAGE_COMPOSITION_FAILED package 'The isolated feature composition failed.' 'Correct the local wiring before image qualification.' -- \
  bash scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
if ! command -v docker >/dev/null 2>&1 || ! timeout 30 docker info >/dev/null 2>&1; then
  printf '%s\n' 'ENTITY_SMOKE_IMAGE_LOCAL_ENGINE_UNAVAILABLE' >&2; exit 1
fi
candidate_image_build ENTITY_SMOKE_IMAGE_BUILD_FAILED 'The isolated image build failed.' 'Inspect this build attempt; publication and deployment were not invoked.' infra/04.deploy/03.product/image/entity-smoke/Dockerfile "$entity_smoke_tag" "$entity_smoke_source" "$entity_smoke_source" "$ROOT" --load --platform linux/amd64 --provenance=false
printf '%s\n' 'ENTITY_SMOKE_LOCAL_IMAGE_BUILT_NOT_QUALIFIED'
