#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-persistence-observability-collector-package-custody
#   version: 2
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
SOURCE_GUARD="$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/verify-source-manifest.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$GUARD" --workflow "$WORKFLOW" --contract "$CONTRACT" --config "$CONFIG" --json >/dev/null
printf '%s' '{"schemaVersion":2,"mediaType":"application/vnd.oci.image.index.v1+json","manifests":[{"digest":"sha256:1111111111111111111111111111111111111111111111111111111111111111","platform":{"os":"linux","architecture":"amd64"}}]}' >"$TMP/source-index.json"
source_index_digest="sha256:$(sha256sum "$TMP/source-index.json" | awk '{print $1}')"
python3 "$SOURCE_GUARD" --index "$TMP/source-index.json" --expected-index-digest "$source_index_digest" --json >/dev/null
if python3 "$SOURCE_GUARD" --index "$TMP/source-index.json" --expected-index-digest sha256:0000000000000000000000000000000000000000000000000000000000000000 --json >/dev/null 2>&1; then
  echo 'collector source guard accepted a mismatched OCI index identity' >&2
  exit 1
fi
printf '%s' '{"schemaVersion":2,"mediaType":"application/vnd.oci.image.index.v1+json","manifests":[{"digest":"sha256:1111111111111111111111111111111111111111111111111111111111111111","platform":{"os":"linux","architecture":"amd64"}},{"digest":"sha256:2222222222222222222222222222222222222222222222222222222222222222","platform":{"os":"linux","architecture":"amd64"}}]}' >"$TMP/ambiguous-source-index.json"
ambiguous_index_digest="sha256:$(sha256sum "$TMP/ambiguous-source-index.json" | awk '{print $1}')"
if python3 "$SOURCE_GUARD" --index "$TMP/ambiguous-source-index.json" --expected-index-digest "$ambiguous_index_digest" --json >/dev/null 2>&1; then
  echo 'collector source guard accepted ambiguous platform manifests' >&2
  exit 1
fi
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
cp "$WORKFLOW" "$TMP/unprivileged-scan-boundary.yml"
sed -i '/scan-mirrored-payload:/a\    permissions: { contents: read, id-token: write }' "$TMP/unprivileged-scan-boundary.yml"
if python3 "$GUARD" --workflow "$TMP/unprivileged-scan-boundary.yml" --contract "$CONTRACT" --config "$CONFIG" --json >/dev/null 2>&1; then
  echo 'collector custody guard accepted privileged third-party scan execution' >&2
  exit 1
fi
echo 'Collector package-custody workflow tests passed.'
