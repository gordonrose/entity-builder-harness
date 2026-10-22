#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-provider-condition-evidence
#   version: 3
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   kind: script
#   purpose: Prove the generic provider-condition validator accepts safe waiting evidence and rejects incomplete, stale, temporally inconsistent, or expired evidence.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.validate-provider-condition-evidence.wrapper
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh

ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh"
FIXTURE="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/fixtures/valid-waiting.yml"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

bash "$SCRIPT" --evidence "$FIXTURE" --json >/dev/null
python3 - "$FIXTURE" "$TEMPORARY_DIRECTORY/verified.yml" <<'PY'
from pathlib import Path
import sys
import yaml

value = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
value["status"] = "verified"
value["checked_at"] = "2026-10-20T12:00:00Z"
value["next_check_after"] = "2026-10-20T13:00:00Z"
Path(sys.argv[2]).write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
if output="$(bash "$SCRIPT" --evidence "$TEMPORARY_DIRECTORY/verified.yml" --at 2026-10-20T13:00:00Z --json 2>&1)"; then
  echo 'ERROR: validator accepted stale verified evidence.' >&2
  exit 1
fi
[[ "$output" == *'provider-condition-evidence-stale'* ]]
python3 - "$FIXTURE" "$TEMPORARY_DIRECTORY/future-observation.yml" "$TEMPORARY_DIRECTORY/inconsistent-window.yml" <<'PY'
from pathlib import Path
import sys
import yaml

value = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
future = dict(value)
future["checked_at"] = "2026-10-21T12:00:01Z"
future["next_check_after"] = "2026-10-21T13:00:00Z"
Path(sys.argv[2]).write_text(yaml.safe_dump(future, sort_keys=False), encoding="utf-8")
inconsistent = dict(value)
inconsistent["checked_at"] = "2026-10-20T13:00:00Z"
inconsistent["next_check_after"] = "2026-10-20T12:00:00Z"
Path(sys.argv[3]).write_text(yaml.safe_dump(inconsistent, sort_keys=False), encoding="utf-8")
PY
if output="$(bash "$SCRIPT" --evidence "$TEMPORARY_DIRECTORY/future-observation.yml" --at 2026-10-21T12:00:00Z --json 2>&1)"; then
  echo 'ERROR: validator accepted a future provider observation.' >&2
  exit 1
fi
[[ "$output" == *'provider-condition-observation-in-future'* ]]
if output="$(bash "$SCRIPT" --evidence "$TEMPORARY_DIRECTORY/inconsistent-window.yml" --at 2026-10-20T14:00:00Z --json 2>&1)"; then
  echo 'ERROR: validator accepted an inconsistent validity window.' >&2
  exit 1
fi
[[ "$output" == *'provider-condition-validity-window-invalid'* ]]
python3 - "$FIXTURE" "$TEMPORARY_DIRECTORY/invalid-waiver.yml" <<'PY'
from pathlib import Path
import sys
import yaml

value = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
value["status"] = "waived-by-approved-exception"
value["waiver"] = {"authority_reference": "approved-change-001"}
Path(sys.argv[2]).write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
if output="$(bash "$SCRIPT" --evidence "$TEMPORARY_DIRECTORY/invalid-waiver.yml" --json 2>&1)"; then
  echo 'ERROR: validator accepted an incomplete waiver.' >&2
  exit 1
fi
[[ "$output" == *'provider-condition-waiver-invalid'* ]]
python3 - "$FIXTURE" "$TEMPORARY_DIRECTORY/valid-waiver.yml" <<'PY'
from pathlib import Path
import sys
import yaml

value = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
value["status"] = "waived-by-approved-exception"
value["waiver"] = {
    "authority_reference": "approved-change-001",
    "reason_code": "provider-delay",
    "expires_at": "2026-10-22T12:00:00Z",
    "compensating_controls": ["one-task-only"],
    "follow_up_owner": "cost-owner",
}
Path(sys.argv[2]).write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
PY
bash "$SCRIPT" --evidence "$TEMPORARY_DIRECTORY/valid-waiver.yml" --required-status waived-by-approved-exception --at 2026-10-21T12:00:00Z --json >/dev/null
if output="$(bash "$SCRIPT" --evidence "$TEMPORARY_DIRECTORY/valid-waiver.yml" --required-status waived-by-approved-exception --at 2026-10-22T12:00:00Z --json 2>&1)"; then
  echo 'ERROR: validator accepted an expired waiver.' >&2
  exit 1
fi
[[ "$output" == *'provider-condition-waiver-expired'* ]]
echo 'Provider-condition evidence smoke test passed.'
