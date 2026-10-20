#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-provider-condition-evidence
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   kind: script
#   purpose: Prove the generic provider-condition validator accepts safe waiting evidence and rejects an incomplete waiver.
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
echo 'Provider-condition evidence smoke test passed.'
