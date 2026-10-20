#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.release-contract
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove representative image-to-runtime incompatibilities fail before any provider mutation.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.release-contract
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/script.py
#   effects: [read-only, writes-files]
ROOT="$(git rev-parse --show-toplevel)"
CHECK="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/script.sh"
fixture="$(mktemp -d)"; trap 'rm -rf "$fixture"' EXIT
mkdir -p "$fixture/infra/04.deploy/03.product"
cp -R "$ROOT/infra/04.deploy/03.product/image" "$fixture/infra/04.deploy/03.product/"
cp -R "$ROOT/infra/04.deploy/03.product/entrypoints" "$fixture/infra/04.deploy/03.product/"
cp -R "$ROOT/infra/04.deploy/03.product/targets" "$fixture/infra/04.deploy/03.product/"
expect() {
  local code="$1"; shift
  local result
  if result="$("$CHECK" --root "$fixture" --json 2>&1)"; then
    echo "ERROR: expected release-contract failure" >&2; exit 1
  fi
  [[ "$result" == *"$code"* ]] || { echo "ERROR: expected $code, got $result" >&2; exit 1; }
  "$@"
}
"$CHECK" --root "$fixture" --json | grep -q '"verdict": "passed"'
sed -i 's/USER nonroot/USER root/' "$fixture/infra/04.deploy/03.product/image/core-server/Dockerfile"
expect image-command-contract-invalid sed -i 's/USER root/USER nonroot/' "$fixture/infra/04.deploy/03.product/image/core-server/Dockerfile"
sed -i 's/- CMD$/- CMD-SHELL/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml"
expect workload-health-command-invalid sed -i 's/- CMD-SHELL$/- CMD/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml"
sed -i 's/            - -e/            - node/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml"
expect verifier-entrypoint-contract-invalid sed -i 's/            - node/            - -e/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/bootstrap-runtime.yml"
echo 'Core-platform release-contract tests passed.'
