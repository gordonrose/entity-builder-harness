#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.platform-shell-publication-image
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Qualify the exact selected platform-shell image and retain its input identity before publication.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml
set -euo pipefail
if [ "${EXISTING_IMAGE:-}" = true ]; then
  docker pull "$ECR_URI@${EXISTING_DIGEST:-}" >/dev/null
  candidate="$ECR_URI@${EXISTING_DIGEST:-}"
else
  candidate="$CANDIDATE_IMAGE"
fi
qualified_image="$(docker image inspect "$candidate" --format '{{.Id}}')"
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --image "$qualified_image"
python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py record --image "$qualified_image" --receipt "$RUNNER_TEMP/qualified-image.json" --input infra/04.deploy/03.product/image/Dockerfile --input scripts/04.deploy/smoke-test-platform-shell-image/script.sh --input scripts/04.deploy/smoke-test-platform-shell-image/relational-package-test.py --configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml '*'
echo "image_id=$qualified_image" >> "$GITHUB_OUTPUT"
