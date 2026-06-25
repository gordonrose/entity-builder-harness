#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-retrieval-policy-pack.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only retrieval policy-pack validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-retrieval-policy-pack
#       path: scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/policy-pack-report.json"
BROKEN_MISSING_DIMENSION="$TMP_DIR/broken-missing-dimension.yml"
BROKEN_MISSING_DIMENSION_FILE="$TMP_DIR/broken-missing-dimension-file.yml"
BROKEN_WEAK_DIMENSION="$TMP_DIR/broken-weak-dimension.yml"
BROKEN_WEAK_DIMENSION_FILE="$TMP_DIR/prompt-weak.yml"
BROKEN_SEMANTIC_RECALL="$TMP_DIR/broken-semantic-recall.yml"

bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["counts"]["dimensions"] == 12
assert report["counts"]["dimension_files"] == 12
assert report["counts"]["precedence"] >= 9
assert report["counts"]["smoke_fixtures"] >= 1
assert report["counts"]["validator_scripts"] >= 1
PY

python3 - "$BROKEN_MISSING_DIMENSION" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

policy_path = Path(".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml")
policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
policy["dimensions"] = [
    dimension
    for dimension in policy["dimensions"]
    if dimension.get("id") != "prompt"
]
Path(sys.argv[1]).write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --policy "$BROKEN_MISSING_DIMENSION" >/dev/null 2>&1; then
  echo "ERROR: retrieval policy-pack validator accepted a missing dimension" >&2
  exit 1
fi

python3 - "$BROKEN_MISSING_DIMENSION_FILE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

policy_path = Path(".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml")
policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
policy["dimensions"][0]["path"] = "does/not/exist.yml"
Path(sys.argv[1]).write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --policy "$BROKEN_MISSING_DIMENSION_FILE" >/dev/null 2>&1; then
  echo "ERROR: retrieval policy-pack validator accepted a missing dimension file" >&2
  exit 1
fi

python3 - "$BROKEN_WEAK_DIMENSION" "$BROKEN_WEAK_DIMENSION_FILE" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

policy_out = Path(sys.argv[1])
dimension_out = Path(sys.argv[2])
policy_path = Path(".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml")
dimension_path = Path(".agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/prompt.yml")
policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
dimension = yaml.safe_load(dimension_path.read_text(encoding="utf-8"))
dimension.pop("banned_actions", None)
policy["dimensions"][0]["path"] = str(dimension_out)
policy_out.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
dimension_out.write_text(yaml.safe_dump(dimension, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --policy "$BROKEN_WEAK_DIMENSION" >/dev/null 2>&1; then
  echo "ERROR: retrieval policy-pack validator accepted a dimension without banned actions" >&2
  exit 1
fi

python3 - "$BROKEN_SEMANTIC_RECALL" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

policy_path = Path(".agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml")
policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
policy["thresholds"]["semantic_recall_enabled"] = True
Path(sys.argv[1]).write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh \
  --policy "$BROKEN_SEMANTIC_RECALL" >/dev/null 2>&1; then
  echo "ERROR: retrieval policy-pack validator accepted enabled semantic recall in v1" >&2
  exit 1
fi

echo "Retrieval policy-pack validator smoke test passed."
