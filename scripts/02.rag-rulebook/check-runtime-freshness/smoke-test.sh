#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-runtime-freshness.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the local RAG/rulebook runtime freshness checker.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.check-runtime-freshness
#       path: scripts/02.rag-rulebook/check-runtime-freshness/script.sh

TMP_DIR="$(mktemp -d)"
SOURCE_PROJECTION_PROBE=".agentic/02.rag-rulebook/source-projections/.runtime-freshness-smoke-test.yml"
STRUCTURED_RULE_PROBE="docs/04.deploy/rules/02.rag-rulebook/.runtime-freshness-smoke-test.yml"
VALIDATION_SCRIPT_PROBE="scripts/02.rag-rulebook/check-source-material-coverage/script.sh"
VALIDATION_SCRIPT_BACKUP="$TMP_DIR/check-source-material-coverage-script.sh"

restore_smoke_files() {
  rm -f "$SOURCE_PROJECTION_PROBE" "$STRUCTURED_RULE_PROBE"
  if [ -f "$VALIDATION_SCRIPT_BACKUP" ]; then
    cp "$VALIDATION_SCRIPT_BACKUP" "$VALIDATION_SCRIPT_PROBE"
  fi
  rm -rf "$TMP_DIR"
}

cp "$VALIDATION_SCRIPT_PROBE" "$VALIDATION_SCRIPT_BACKUP"
trap restore_smoke_files EXIT

RUNTIME_DIR="$TMP_DIR/runtime"
FRESH_REPORT="$TMP_DIR/fresh.json"
STALE_REPORT="$TMP_DIR/stale.json"
MISSING_REPORT="$TMP_DIR/missing.json"
CORRUPT_REPORT="$TMP_DIR/corrupt.json"

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null

bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --json > "$FRESH_REPORT"

python3 - "$FRESH_REPORT" "$RUNTIME_DIR/manifest.json" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
manifest = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert report["schema"] == "rag-rulebook/runtime-freshness-report/v1"
assert report["policy_version"] == "strict-v1"
assert report["ok"] is True
assert report["status"] == "fresh"
assert report["severity"] == "fresh"
assert not report["differences"]["inputs"]
assert not report["differences"]["runtime_outputs"]
assert not report["differences"]["manifest"]
assert {item["name"] for item in report["checks"]["inputs"]} == set(manifest["fingerprints"]["inputs"])
assert "source_projections" in manifest["fingerprints"]["inputs"]
assert "validation_machinery" in manifest["fingerprints"]["inputs"]
assert {item["name"] for item in report["checks"]["runtime_outputs"]} >= {"rulebook_index", "rulebook_chunks"}
PY

python3 - "$RUNTIME_DIR/manifest.json" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["fingerprints"]["inputs"]["recognition_sources"]["sha256"] = "0" * 64
manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --json > "$STALE_REPORT"; then
  echo "ERROR: stale runtime unexpectedly passed freshness check." >&2
  exit 1
fi

python3 - "$STALE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["status"] == "stale"
assert report["severity"] == "blocked"
assert any(item["name"] == "recognition_sources" for item in report["differences"]["inputs"])
PY

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null

rm -f "$STRUCTURED_RULE_PROBE"
cat > "$STRUCTURED_RULE_PROBE" <<'YAML'
id: runtime-freshness-smoke-test
title: Runtime freshness smoke test
rules: []
YAML

if bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --json > "$STALE_REPORT"; then
  echo "ERROR: structured rule root change unexpectedly passed freshness check." >&2
  exit 1
fi

python3 - "$STALE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["status"] == "stale"
assert any(item["name"] == "structured_rules" for item in report["differences"]["inputs"])
PY

rm -f "$STRUCTURED_RULE_PROBE"

cat > "$SOURCE_PROJECTION_PROBE" <<'YAML'
schema: runtime-freshness-smoke-test/v1
purpose: Temporary source projection fingerprint probe.
YAML

if bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --json > "$STALE_REPORT"; then
  echo "ERROR: source projection change unexpectedly passed freshness check." >&2
  exit 1
fi

python3 - "$STALE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["status"] == "stale"
assert any(item["name"] == "source_projections" for item in report["differences"]["inputs"])
PY

rm -f "$SOURCE_PROJECTION_PROBE"

printf '\n# runtime-freshness-smoke-test\n' >> "$VALIDATION_SCRIPT_PROBE"

if bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --json > "$STALE_REPORT"; then
  echo "ERROR: validation machinery change unexpectedly passed freshness check." >&2
  exit 1
fi

python3 - "$STALE_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["status"] == "stale"
assert any(item["name"] == "source_projections" for item in report["differences"]["inputs"])
assert any(item["name"] == "validation_machinery" for item in report["differences"]["inputs"])
PY

cp "$VALIDATION_SCRIPT_BACKUP" "$VALIDATION_SCRIPT_PROBE"

if bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$TMP_DIR/missing-runtime" \
  --json > "$MISSING_REPORT"; then
  echo "ERROR: missing runtime unexpectedly passed freshness check." >&2
  exit 1
fi

python3 - "$MISSING_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["status"] == "missing"
assert report["differences"]["manifest"]
PY

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$RUNTIME_DIR" \
  --pretty >/dev/null
rm "$RUNTIME_DIR/rulebook-chunks.json"

if bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" \
  --json > "$CORRUPT_REPORT"; then
  echo "ERROR: corrupt runtime unexpectedly passed freshness check." >&2
  exit 1
fi

python3 - "$CORRUPT_REPORT" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"] is False
assert report["status"] == "corrupt"
assert any(item["name"] == "rulebook_chunks" for item in report["differences"]["runtime_outputs"])
PY

echo "RAG/rulebook runtime freshness smoke test passed."
