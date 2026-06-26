#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-rulebook-chunks.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: chunking
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only rulebook chunk generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-rulebook-chunks
#       path: scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INDEX_FILE="$TMP_DIR/rulebook-index.json"
CHUNKS_FILE="$TMP_DIR/rulebook-chunks.json"
BROKEN_INDEX_FILE="$TMP_DIR/broken-rulebook-index.json"

bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh --pretty > "$INDEX_FILE"
bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --index "$INDEX_FILE" --pretty > "$CHUNKS_FILE"

python3 - "$INDEX_FILE" "$CHUNKS_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

index = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
chunk_set = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

assert chunk_set["schema"] == "rag-rulebook/chunk-set/v1"
assert chunk_set["diagnostics"]["ok"], chunk_set["diagnostics"]
assert chunk_set["source_index_id"] == index["index_id"]
assert len(chunk_set["chunks"]) == len(index["chunk_candidates"])
assert chunk_set["diagnostics"]["counts"]["chunks"] == len(index["chunk_candidates"])

citations = {citation["id"] for citation in chunk_set["citations"]}
content_kinds = {chunk["content_kind"] for chunk in chunk_set["chunks"]}
assert {"artifact-summary", "rule", "rule-pack-step", "required-check"} <= content_kinds

for chunk in chunk_set["chunks"]:
    assert chunk["content"].strip(), chunk["chunk_id"]
    assert chunk["token_estimate"] >= 1, chunk["chunk_id"]
    assert chunk["citation_ids"], chunk["chunk_id"]
    assert set(chunk["citation_ids"]) <= citations, chunk["chunk_id"]

rule_chunks = [chunk for chunk in chunk_set["chunks"] if chunk["content_kind"] == "rule"]
assert any("core.stable-cross-cutting-only" in chunk["content"] for chunk in rule_chunks)
assert any(
    chunk["source_path"] == "docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml"
    and "MCP servers expose governed capabilities" in chunk["content"]
    for chunk in rule_chunks
)
assert any(
    chunk["source_path"] == "docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml"
    and chunk["corpus_id"] == "corpus.02.rag-rulebook"
    for chunk in chunk_set["chunks"]
)
assert any(
    chunk["source_path"] == "docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml"
    and chunk["corpus_id"] == "corpus.04.deploy"
    and "Deployment readiness gaps block execution" in chunk["content"]
    for chunk in chunk_set["chunks"]
)
assert any(
    chunk["source_path"] == "docs/04.deploy/rules/02.rag-rulebook/github-to-aws-deployment.yml"
    and chunk["corpus_id"] == "corpus.04.deploy"
    and "GitHub controls release authorization" in chunk["content"]
    for chunk in chunk_set["chunks"]
)
assert any(
    chunk["source_path"] == "docs/04.deploy/rules/02.rag-rulebook/aws-runtime-boundaries.yml"
    and chunk["corpus_id"] == "corpus.04.deploy"
    and "AWS target identity is explicit before mutation" in chunk["content"]
    for chunk in chunk_set["chunks"]
)

print("Rulebook chunk generator smoke test passed.")
print(json.dumps(chunk_set["diagnostics"]["counts"], sort_keys=True))
PY

python3 - "$INDEX_FILE" "$BROKEN_INDEX_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
data["chunk_candidates"][0]["artifact_ref"] = "missing.artifact"
Path(sys.argv[2]).write_text(json.dumps(data), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --index "$BROKEN_INDEX_FILE" >/dev/null 2>&1; then
  echo "ERROR: chunk generator accepted an invalid index" >&2
  exit 1
fi
