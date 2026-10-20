#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.generate-recognition-sources.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-06-25"
#   updated_on: "2026-10-20"
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test deterministic recognition-source generation.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-recognition-sources
#       path: scripts/02.rag-rulebook/generate-recognition-sources/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

GENERATED_ARTIFACTS="$TMP_DIR/artifacts.yml"
GENERATED_ROUTING="$TMP_DIR/routing.yml"
PRINTED_ARTIFACTS="$TMP_DIR/printed-artifacts.yml"
PRINTED_ROUTING="$TMP_DIR/printed-routing.yml"

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source artifacts \
  --output "$GENERATED_ARTIFACTS" >/dev/null

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --source "$GENERATED_ARTIFACTS" >/dev/null

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source routing \
  --output "$GENERATED_ROUTING" >/dev/null

bash scripts/02.rag-rulebook/validate-recognition-sources/script.sh \
  --source "$GENERATED_ROUTING" >/dev/null

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source artifacts \
  --print > "$PRINTED_ARTIFACTS"

bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh \
  --source routing \
  --print > "$PRINTED_ROUTING"

python3 - "$GENERATED_ARTIFACTS" "$GENERATED_ROUTING" "$PRINTED_ARTIFACTS" "$PRINTED_ROUTING" <<'PY'
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

import yaml

artifacts = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
routing = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert artifacts == yaml.safe_load(Path(sys.argv[3]).read_text(encoding="utf-8"))
assert routing == yaml.safe_load(Path(sys.argv[4]).read_text(encoding="utf-8"))

# New output paths use v3; a no-op preserves old dates and exact bytes.
path = Path(sys.argv[2])
def header(text):
    lines = []
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        lines.append(line[2:])
    return yaml.safe_load("\n".join(lines))["agentic-artifact"]

metadata = header(path.read_text())
assert metadata["schema"] == "agentic-artifact/v3"
today = dt.datetime.now(dt.UTC).date().isoformat()
assert metadata["created_on"] == metadata["updated_on"] == today
text = path.read_text().replace(today, "2000-01-01")
path.write_text(text)
command = ["bash", "scripts/02.rag-rulebook/generate-recognition-sources/script.sh", "--source", "routing", "--output", str(path)]
subprocess.run(command + ["--check"], check=True, capture_output=True, text=True)
subprocess.run(command, check=True, capture_output=True, text=True)
assert path.read_text() == text
path.write_text(text + "obsolete_body_field: remove-me\n")
subprocess.run(command, check=True, capture_output=True, text=True)
updated = header(path.read_text())
assert updated["created_on"] == "2000-01-01"
assert updated["updated_on"] == today
subprocess.run(command + ["--check"], check=True, capture_output=True, text=True)
path.write_text(path.read_text().replace("agentic-artifact/v3", "agentic-artifact/v99", 1))
failure = subprocess.run(command, capture_output=True, text=True)
assert failure.returncode != 0 and "Unsupported generated metadata schema" in failure.stderr

assert artifacts["schema"] == "rag-rulebook/recognition-source/v1"
assert artifacts["source_id"] == "recognition.generated.artifacts"
assert artifacts["generation_mode"] == "generated"
artifact_terms = {term["term"]: term for term in artifacts["terms"]}
assert "rag-rulebook.schema.recognition-source" in artifact_terms
assert ".agentic/02.rag-rulebook/schemas/recognition-source.schema.yml" in artifact_terms
assert "recognition-source.schema.yml" in artifact_terms
assert artifacts["generation_summary"]["term_count"] == len(artifacts["terms"])
assert len(artifacts["terms"]) > 100

assert routing["schema"] == "rag-rulebook/recognition-source/v1"
assert routing["source_id"] == "recognition.generated.routing"
assert routing["generation_mode"] == "generated"
routing_terms = {term["term"]: term for term in routing["terms"]}
assert "02.rag-rulebook" in routing_terms
assert "corpus.02.rag-rulebook" in routing_terms
assert "implementation" in routing_terms
assert ".agentic/02.rag-rulebook/workflows/default.md" in routing_terms
assert routing["generation_summary"]["term_count"] == len(routing["terms"])
assert len(routing["terms"]) > 20
PY

if [ -f ".agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml" ]; then
  bash scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check >/dev/null
fi

echo "Recognition-source generator smoke test passed."
