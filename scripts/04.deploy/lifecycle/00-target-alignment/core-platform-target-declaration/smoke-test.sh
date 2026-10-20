#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-platform-target-declaration
#   version: 2
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the core-platform target declaration checker accepts its planned declaration and rejects unsafe claims.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.core-platform-target-declaration
#     path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.sh"
SOURCE="$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

expect_pass() {
  local output
  output="$(bash "$SCRIPT" --target-root "$1" --json)"
  [[ "$output" == *'"verdict": "repository-declaration-complete"'* ]]
}

expect_failure() {
  local code="$1"
  local root="$2"
  local output
  if output="$(bash "$SCRIPT" --target-root "$root" --json 2>&1)"; then
    echo "ERROR: expected $code failure" >&2
    exit 1
  fi
  [[ "$output" == *"\"code\": \"$code\""* ]] || { echo "ERROR: expected $code" >&2; exit 1; }
}

copy_fixture() {
  local name="$1"
  local fixture="$TEMPORARY_DIRECTORY/$name"
  cp -R "$SOURCE" "$fixture"
  printf '%s' "$fixture"
}

expect_pass "$SOURCE"

missing="$(copy_fixture missing)"
python3 - "$missing/target-profile.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["e0_required_facts"] = [fact for fact in value["e0_required_facts"] if fact["id"] != "cost-guard"]
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "e0-fact-missing" "$missing"

replaced="$(copy_fixture replaced)"
python3 - "$replaced/target-profile.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8") )
value["target_mutation"]["allowed_operation"] = "replace"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "target-mutation-not-create-only" "$replaced"

unowned="$(copy_fixture unowned)"
python3 - "$unowned/target-profile.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["e0_required_facts"][0].pop("owner")
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "e0-fact-unowned" "$unowned"

ready="$(copy_fixture falsely-ready)"
python3 - "$ready/target-profile.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["live_alignment"] = "aligned"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "live-alignment-state-invalid" "$ready"

cost="$(copy_fixture invalid-cost-control)"
python3 - "$cost/foundation/cost-control.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["waiver"]["compensating_controls"] = []
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "cost-control-invalid" "$cost"

echo "Core-platform target declaration tests passed."
