#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-persistence-observability-collector-package-custody
#   version: 1
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
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$GUARD" --workflow "$WORKFLOW" --contract "$CONTRACT" --config "$CONFIG" --json >/dev/null
cp "$WORKFLOW" "$TMP/workflow.yml"
printf '\n      - run: aws ecs update-service --cluster forbidden\n' >> "$TMP/workflow.yml"
if python3 "$GUARD" --workflow "$TMP/workflow.yml" --contract "$CONTRACT" --config "$CONFIG" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted a workload mutation' >&2
  exit 1
fi
cp "$CONTRACT" "$TMP/contract.yml"
sed -i 's#sha256:7968fb60db6a2390a47ba6a2df029745638486e285c9b2487da1b722d0855a3e#sha256:0000000000000000000000000000000000000000000000000000000000000000#' "$TMP/contract.yml"
if python3 "$GUARD" --workflow "$WORKFLOW" --contract "$TMP/contract.yml" --config "$CONFIG" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted a mutable or wrong source identity' >&2
  exit 1
fi
cp "$CONFIG" "$TMP/config.yml"
printf '\npassword: synthetic-only\n' >> "$TMP/config.yml"
if python3 "$GUARD" --workflow "$WORKFLOW" --contract "$CONTRACT" --config "$TMP/config.yml" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted secret-bearing configuration' >&2
  exit 1
fi
echo 'Collector package-custody workflow tests passed.'
