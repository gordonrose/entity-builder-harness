#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-yaml-syntax.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the RAG/rulebook YAML syntax validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.validate-yaml-syntax
#       path: scripts/02.rag-rulebook/validate-yaml-syntax/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$TMP_DIR/valid" "$TMP_DIR/invalid"

cat > "$TMP_DIR/valid/example.yml" <<'YAML'
schema: example/v1
rules:
  - "`source_material` proves human-readable source exists."
YAML

cat > "$TMP_DIR/invalid/example.yml" <<'YAML'
schema: example/v1
rules:
  - `source_material` proves human-readable source exists.
YAML

bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh \
  --paths "$TMP_DIR/valid" >/dev/null

if bash scripts/02.rag-rulebook/validate-yaml-syntax/script.sh \
  --paths "$TMP_DIR/invalid" >/dev/null 2>&1; then
  echo "ERROR: invalid YAML unexpectedly passed." >&2
  exit 1
fi

python3 - "$TMP_DIR/valid" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys

result = subprocess.run(
    [
        "bash",
        "scripts/02.rag-rulebook/validate-yaml-syntax/script.sh",
        "--paths",
        sys.argv[1],
        "--json",
    ],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
)
report = json.loads(result.stdout)
assert report["schema"] == "rag-rulebook/yaml-syntax-validation-report/v1"
assert report["ok"] is True
assert report["files_checked"] == 1
PY

echo "YAML syntax validator smoke test passed."
