#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-persistence-observability-collector-package-custody
#   version: 3
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the collector custody guard accepts only the fixed, non-mutating package route.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/script.sh

ROOT="$(git rev-parse --show-toplevel)"
GUARD="$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/verify-workflow.py"
WORKFLOW="$ROOT/.github/workflows/publish-kanbien-core-platform-observability-collector.yml"
CONTRACT="$ROOT/infra/04.deploy/03.product/image/core-server-persistence-observability-collector/image-contract.yml"
CONFIG="$ROOT/infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml"
DOCKERFILE="$ROOT/infra/04.deploy/03.product/image/core-server-persistence-observability-collector/Dockerfile"
COMPONENT_MANIFEST="$ROOT/infra/04.deploy/03.product/image/core-server-persistence-observability-collector/builder-config.yaml"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$GUARD" --workflow "$WORKFLOW" --contract "$CONTRACT" --config "$CONFIG" --json >/dev/null
cp "$WORKFLOW" "$TMP/wrong-archive-boundary.yml"
sed -i 's#scan-qualified-payload#scan-untrusted-payload#g' "$TMP/wrong-archive-boundary.yml"
if python3 "$GUARD" --workflow "$TMP/wrong-archive-boundary.yml" --contract "$CONTRACT" --config "$CONFIG" --dockerfile "$DOCKERFILE" --component-manifest "$COMPONENT_MANIFEST" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted a missing qualified-archive boundary' >&2
  exit 1
fi
cp "$WORKFLOW" "$TMP/workflow.yml"
printf '\n      - run: aws ecs update-service --cluster forbidden\n' >> "$TMP/workflow.yml"
if python3 "$GUARD" --workflow "$TMP/workflow.yml" --contract "$CONTRACT" --config "$CONFIG" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted a workload mutation' >&2
  exit 1
fi
cp "$CONTRACT" "$TMP/contract.yml"
sed -i 's#0bd72a020e0b8414c85df56fd5dcc1ebd05f160a8bbe03f8fb2c53a1248218e8#0000000000000000000000000000000000000000000000000000000000000000#' "$TMP/contract.yml"
if python3 "$GUARD" --workflow "$WORKFLOW" --contract "$TMP/contract.yml" --config "$CONFIG" --dockerfile "$DOCKERFILE" --component-manifest "$COMPONENT_MANIFEST" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted a wrong upstream manifest identity' >&2
  exit 1
fi
cp "$CONFIG" "$TMP/config.yml"
printf '\npassword: synthetic-only\n' >> "$TMP/config.yml"
if python3 "$GUARD" --workflow "$WORKFLOW" --contract "$CONTRACT" --config "$TMP/config.yml" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted secret-bearing configuration' >&2
  exit 1
fi
cp "$WORKFLOW" "$TMP/unprivileged-scan-boundary.yml"
sed -i '/scan-qualified-payload:/a\    permissions: { contents: read, id-token: write }' "$TMP/unprivileged-scan-boundary.yml"
if python3 "$GUARD" --workflow "$TMP/unprivileged-scan-boundary.yml" --contract "$CONTRACT" --config "$CONFIG" --dockerfile "$DOCKERFILE" --component-manifest "$COMPONENT_MANIFEST" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted privileged third-party scan execution' >&2
  exit 1
fi
cp "$DOCKERFILE" "$TMP/Dockerfile"
sed -i 's#--config=env:AOT_CONFIG_CONTENT#--config=/untrusted/config.yml#' "$TMP/Dockerfile"
if python3 "$GUARD" --workflow "$WORKFLOW" --contract "$CONTRACT" --config "$CONFIG" --dockerfile "$TMP/Dockerfile" --component-manifest "$COMPONENT_MANIFEST" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted an undeclared configuration startup route' >&2
  exit 1
fi
echo 'Collector package-custody workflow tests passed.'
