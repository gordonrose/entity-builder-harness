#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.release-contract
#   version: 4
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-22"
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
sed -i 's/- CMD$/- CMD-SHELL/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml"
expect workload-health-command-invalid sed -i 's/- CMD-SHELL$/- CMD/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml"
sed -i 's/            - -e/            - node/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml"
expect verifier-entrypoint-contract-invalid sed -i 's/            - node/            - -e/' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml"
sed -i 's|path: /readyz|path: /declared-but-not-workload-readyz|' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"
expect workload-health-command-invalid sed -i 's|path: /declared-but-not-workload-readyz|path: /readyz|' "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"
python3 - "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["health_recovery"]["workloads"][1]["completion"]["success"]["result_code"] = "NEVER_EMITTED"
value["health_recovery"]["workloads"][1]["proof"]["completion"]["result_code"] = "NEVER_EMITTED"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect target-declaration-invalid python3 - "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["health_recovery"]["workloads"][1]["completion"]["success"]["result_code"] = "KANBIEN_CORE_RELEASE_VERIFIED"
value["health_recovery"]["workloads"][1]["proof"]["completion"]["result_code"] = "KANBIEN_CORE_RELEASE_VERIFIED"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
python3 - "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace("  ReleaseVerifierTaskDefinition:\n    Type: AWS::ECS::TaskDefinition", "  ReleaseVerifierTaskDefinition:\n    Type: AWS::ECS::Service", 1)
path.write_text(text, encoding="utf-8")
PY
expect target-declaration-invalid python3 - "$fixture/infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace("  ReleaseVerifierTaskDefinition:\n    Type: AWS::ECS::Service", "  ReleaseVerifierTaskDefinition:\n    Type: AWS::ECS::TaskDefinition", 1)
path.write_text(text, encoding="utf-8")
PY
echo 'Core-platform release-contract tests passed.'
