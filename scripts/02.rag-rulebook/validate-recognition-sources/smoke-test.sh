#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-recognition-sources.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the recognition-source validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-recognition-sources
#       path: scripts/02.rag-rulebook/validate-recognition-sources/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT_FILE="$TMP_DIR/current.json"
VALID_SOURCE="$TMP_DIR/valid-generated.yml"
BROKEN_NO_EVIDENCE="$TMP_DIR/broken-no-evidence.yml"
BROKEN_DUPLICATE_TERM="$TMP_DIR/broken-duplicate-term.yml"
BROKEN_CURATED_REVIEW="$TMP_DIR/broken-curated-review.yml"
BROKEN_MISSING_ARTIFACT="$TMP_DIR/broken-missing-artifact.yml"

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --current \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["schema"] == "rag-rulebook/recognition-source/v1"
assert "counts" in report
PY

cat > "$VALID_SOURCE" <<'EOF'
schema: rag-rulebook/recognition-source/v1
source_id: recognition.test.generated
version: 1
status: active
source_kinds:
  - artifact-id
  - file-path
generation_mode: generated
owner_layer: 02.rag-rulebook
purpose: Smoke-test generated recognition source.
match_priority: 10
used_by_dimensions:
  - prompt
source_artifacts:
  - .agentic/02.rag-rulebook/schemas/recognition-source.schema.yml
generation_command: scripts/02.rag-rulebook/validate-recognition-sources/script.sh --help
terms:
  - term: rag-rulebook.schema.recognition-source
    category: artifact-id
    match_type: exact
    canonical_id: rag-rulebook.schema.recognition-source
    evidence_path: .agentic/02.rag-rulebook/schemas/recognition-source.schema.yml
    confidence_weight: 1
  - term: .agentic/02.rag-rulebook/schemas/recognition-source.schema.yml
    category: file-path
    match_type: exact
    canonical_id: rag-rulebook.schema.recognition-source
    evidence_path: .agentic/02.rag-rulebook/schemas/recognition-source.schema.yml
    confidence_weight: 1
validation_rules:
  - Generated terms must retain evidence paths.
refresh_policy:
  trigger: Regenerate when source artifacts change.
  owner: 02.rag-rulebook
EOF

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --source "$VALID_SOURCE" >/dev/null

python3 - "$VALID_SOURCE" "$BROKEN_NO_EVIDENCE" "$BROKEN_DUPLICATE_TERM" "$BROKEN_MISSING_ARTIFACT" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml

valid_path = Path(sys.argv[1])

no_evidence = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
no_evidence["terms"][0].pop("evidence_path", None)
Path(sys.argv[2]).write_text(yaml.safe_dump(no_evidence, sort_keys=False), encoding="utf-8")

duplicate = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
duplicate["terms"][1]["term"] = duplicate["terms"][0]["term"]
Path(sys.argv[3]).write_text(yaml.safe_dump(duplicate, sort_keys=False), encoding="utf-8")

missing_artifact = yaml.safe_load(valid_path.read_text(encoding="utf-8"))
missing_artifact["source_artifacts"] = ["does/not/exist.yml"]
Path(sys.argv[4]).write_text(yaml.safe_dump(missing_artifact, sort_keys=False), encoding="utf-8")
PY

cat > "$BROKEN_CURATED_REVIEW" <<'EOF'
schema: rag-rulebook/recognition-source/v1
source_id: recognition.test.curated
version: 1
status: active
source_kinds:
  - action-verb
generation_mode: curated
owner_layer: 02.rag-rulebook
purpose: Smoke-test curated recognition source.
match_priority: 50
used_by_dimensions:
  - prompt
terms:
  - term: validate
    category: action-verb
    match_type: exact
validation_rules:
  - Curated terms require review.
refresh_policy:
  trigger: Review when prompt vocabulary changes.
  owner: 02.rag-rulebook
EOF

for broken in \
  "$BROKEN_NO_EVIDENCE" \
  "$BROKEN_DUPLICATE_TERM" \
  "$BROKEN_CURATED_REVIEW" \
  "$BROKEN_MISSING_ARTIFACT"; do
  if bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
    --source "$broken" >/dev/null 2>&1; then
    echo "ERROR: recognition-source validator accepted broken source: $broken" >&2
    exit 1
  fi
done

echo "Recognition-source validator smoke test passed."
