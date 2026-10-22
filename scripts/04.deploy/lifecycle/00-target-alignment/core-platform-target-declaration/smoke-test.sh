#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-platform-target-declaration
#   version: 6
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the core-platform target declaration checker accepts its accepted declaration and rejects unsafe claims, including mismatched waiver evidence.
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
python3 - "$missing/00-target/target-profile.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["e0_required_facts"] = [fact for fact in value["e0_required_facts"] if fact["id"] != "target-budget"]
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "e0-fact-missing" "$missing"

replaced="$(copy_fixture replaced)"
python3 - "$replaced/00-target/target-profile.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8") )
value["target_mutation"]["allowed_operation"] = "replace"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "target-mutation-not-controlled" "$replaced"

unowned="$(copy_fixture unowned)"
python3 - "$unowned/00-target/target-profile.yml" <<'PY'
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
python3 - "$ready/00-target/target-profile.yml" <<'PY'
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
python3 - "$cost/10-foundation/cost-control.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["evidence"] = ""
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "cost-control-invalid" "$cost"

mismatched_evidence="$(copy_fixture mismatched-cost-evidence)"
python3 - "$mismatched_evidence/10-foundation/evidence/target-cost-allocation-tag.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["status"] = "waiting-on-provider"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "cost-control-evidence-invalid" "$mismatched_evidence"

missing_rehearsal="$(copy_fixture missing-rehearsal)"
python3 - "$missing_rehearsal/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["acceptance"].pop("last_rehearsal")
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "accepted-release-rehearsal-missing" "$missing_rehearsal"

missing_restoration_rehearsal="$(copy_fixture missing-restoration-rehearsal)"
python3 - "$missing_restoration_rehearsal/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["acceptance"].pop("last_restoration_rehearsal")
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "accepted-release-restoration-rehearsal-missing" "$missing_restoration_rehearsal"

mismatched_verifier_evidence="$(copy_fixture mismatched-verifier-evidence)"
python3 - "$mismatched_verifier_evidence/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["health_recovery"]["workloads"][1]["proof"]["completion"]["observed_at"] = "2026-10-21T15:57:00Z"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "active-workload-health-recovery-inventory-invalid" "$mismatched_verifier_evidence"

contradictory_success="$(copy_fixture contradictory-success)"
python3 - "$contradictory_success/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["health_recovery"]["workloads"][1]["completion"]["success"]["result_code"] = "NEVER_EMITTED"
value["health_recovery"]["workloads"][1]["proof"]["completion"]["result_code"] = "NEVER_EMITTED"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "verifier-completion-evidence-invalid" "$contradictory_success"

missing_provider_resource="$(copy_fixture missing-provider-resource)"
python3 - "$missing_provider_resource/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["workloads"][1]["provider_reference"] = "MissingVerifierTaskDefinition"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "workload-provider-reference-invalid" "$missing_provider_resource"

wrong_provider_type="$(copy_fixture wrong-provider-type)"
python3 - "$wrong_provider_type/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace("  ReleaseVerifierTaskDefinition:\n    Type: AWS::ECS::TaskDefinition", "  ReleaseVerifierTaskDefinition:\n    Type: AWS::ECS::Service", 1)
path.write_text(text, encoding="utf-8")
PY
expect_failure "workload-provider-reference-invalid" "$wrong_provider_type"

missing_execution_trace="$(copy_fixture missing-execution-trace)"
python3 - "$missing_execution_trace/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["workloads"][1]["execution"]["command_description"] = "untraced"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "workload-execution-source-invalid" "$missing_execution_trace"

deadline_exceeded="$(copy_fixture deadline-exceeded)"
python3 - "$deadline_exceeded/20-scopes/bootstrap-runtime/30-release-evidence/rehearsals/accepted-workload-replacement-2026-10-22.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["fresh_private_verification"]["verifier_started_at"] = "2026-10-21T15:54:00Z"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "verifier-completion-evidence-invalid" "$deadline_exceeded"

stale_completion="$(copy_fixture stale-completion)"
python3 - "$stale_completion/20-scopes/bootstrap-runtime/30-release-evidence/rehearsals/accepted-workload-replacement-2026-10-22.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["rehearsal"]["original_task_stopped_at"] = "2026-10-21T15:57:00Z"
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "verifier-completion-evidence-invalid" "$stale_completion"

binding_without_declaration="$(copy_fixture binding-without-declaration)"
mkdir -p "$binding_without_declaration/20-scopes/binding-only/10-workload-binding"
cp "$binding_without_declaration/20-scopes/bootstrap-runtime/10-workload-binding/workload-binding.yml" "$binding_without_declaration/20-scopes/binding-only/10-workload-binding/workload-binding.yml"
python3 - "$binding_without_declaration/20-scopes/scope-index.yml" <<'PY'
from pathlib import Path
import sys
import yaml

path = Path(sys.argv[1])
value = yaml.safe_load(path.read_text(encoding="utf-8"))
value["active_scopes"].append({
    "id": "binding-only",
    "declaration": "binding-only/00-declaration/declaration-contract.yml",
    "workload_binding": "binding-only/10-workload-binding/workload-binding.yml",
})
path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
expect_failure "active-workload-health-recovery-inventory-invalid" "$binding_without_declaration"

echo "Core-platform target declaration tests passed."
