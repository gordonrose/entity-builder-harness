#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-gate
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove the generic Operational Realization Gate accepts complete graphs and rejects unsafe or provider-coupled contracts.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.deployment-realization-test
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
SCRIPT="scripts/04.deploy/operational-realization-gate/script.sh"
FIXTURES="scripts/04.deploy/operational-realization-gate/fixtures"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

expect_failure() {
  local expected_code="$1"
  shift
  local output
  if output="$("$@" 2>&1)"; then
    echo "ERROR: expected realization gate failure $expected_code" >&2
    exit 1
  fi
  if [[ "$output" != *"\"code\": \"$expected_code\""* ]]; then
    echo "ERROR: realization gate emitted an unexpected unsafe failure" >&2
    exit 1
  fi
}

python3 - <<'PY'
from pathlib import Path
import yaml

source = Path("scripts/04.deploy/operational-realization-gate/script.py").read_text(encoding="utf-8")
compile(source, "operational-realization-gate.py", "exec")
for path in (
    ".agentic/01.harness/templates/operational-realization-contract.v1.template.yml",
    ".agentic/01.harness/templates/operational-realization-contract.v1.schema.yml",
):
    if not isinstance(yaml.safe_load(Path(path).read_text(encoding="utf-8")), dict):
        raise SystemExit("ERROR: realization template/schema must be valid YAML mappings")
PY
valid_output="$(bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$FIXTURES/valid-normalized-facts.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through recovery --json)"
if [[ "$valid_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: valid realization contract did not pass" >&2
  exit 1
fi

preflight_output="$(bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$FIXTURES/preflight-normalized-facts.yml" --change-summary "$FIXTURES/valid-normalized-change-summary.yml" --through execution-preflight --json)"
if [[ "$preflight_output" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: complete preflight evidence did not pass before controlled execution" >&2
  exit 1
fi

expect_failure "assumption-proof-unknown" bash "$SCRIPT" --contract "$FIXTURES/unknown-assumption.yml" --json

sed '/to: delivery-store, purpose: persists/d' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/undeclared-edge.yml"
expect_failure "undeclared-dependency-edge" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/undeclared-edge.yml" --json

sed 's/mode: reviewed-recovery-only/mode: automatic/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/unsafe-retry.yml"
expect_failure "unsafe-retry-policy" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/unsafe-retry.yml" --json

sed '0,/id: delivery-store/s//id: aws-store/' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/provider-leakage.yml"
expect_failure "provider-specific-leakage" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/provider-leakage.yml" --json

sed '/sensitivity: secret-reference-only/a\    endpoint: unsafe-value' "$FIXTURES/valid-contract.yml" > "$TEMPORARY_DIRECTORY/unsafe-value.yml"
expect_failure "unsafe-value-field-declared" bash "$SCRIPT" --contract "$TEMPORARY_DIRECTORY/unsafe-value.yml" --json

expect_failure "normalized-change-summary-required-for-gate" bash "$SCRIPT" --contract "$FIXTURES/valid-contract.yml" --facts "$FIXTURES/valid-normalized-facts.yml" --through change-set --json

if rg -n '(^|[[:space:]])(import|from)[[:space:]]+(platform\.adapters|boto|azure|oci|oracle)' scripts/04.deploy/operational-realization-gate/script.py; then
  echo "ERROR: provider adapter import leaked into generic realization core" >&2
  exit 1
fi
if rg -n 'subprocess|socket|urllib|requests' scripts/04.deploy/operational-realization-gate/script.py; then
  echo "ERROR: generic realization core must not invoke network or provider tooling" >&2
  exit 1
fi
echo "Operational Realization Gate local tests passed."
