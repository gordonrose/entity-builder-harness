#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.target-alignment-validation
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove target-alignment validation accepts full matching evidence and fails closed for any missing assertion.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.target-alignment-validation
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.sh
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.sh"
FIXTURES="$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/fixtures"
"$SCRIPT" --contract "$FIXTURES/contract.yml" --evidence "$FIXTURES/aligned.json" --json | grep -q '"verdict": "aligned"'
bad="$(mktemp)"; trap 'rm -f "$bad"' EXIT
python3 - "$FIXTURES/aligned.json" "$bad" <<'PY'
import json, sys
x=json.load(open(sys.argv[1])); x['assertions'][0]['outcome']='missing'; json.dump(x,open(sys.argv[2],'w'))
PY
if "$SCRIPT" --contract "$FIXTURES/contract.yml" --evidence "$bad" --json >/dev/null; then echo 'expected failure' >&2; exit 1; fi
echo 'Target alignment validation tests passed.'
