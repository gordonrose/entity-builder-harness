#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.build-local-runtime.smoke-test
#   version: 2
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the local deterministic RAG/rulebook runtime build command.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.build-local-runtime
#       path: scripts/02.rag-rulebook/build-local-runtime/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

OUTPUT_DIR="$TMP_DIR/runtime"

bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir "$OUTPUT_DIR" \
  --pretty >/dev/null

python3 - "$OUTPUT_DIR" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

runtime = Path(sys.argv[1])
index_path = runtime / "rulebook-index.json"
chunks_path = runtime / "rulebook-chunks.json"
compiled_policy_path = runtime / "compiled-retrieval-policy.json"
manifest_path = runtime / "manifest.json"
validation_path = runtime / "validation-report.json"

for path in [index_path, chunks_path, compiled_policy_path, manifest_path, validation_path]:
    assert path.is_file(), path

index = json.loads(index_path.read_text(encoding="utf-8"))
chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
compiled_policy = json.loads(compiled_policy_path.read_text(encoding="utf-8"))
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
validation = json.loads(validation_path.read_text(encoding="utf-8"))

assert index["schema"] == "rag-rulebook/rulebook-index/v1"
assert chunks["schema"] == "rag-rulebook/chunk-set/v1"
assert compiled_policy["schema"] == "rag-rulebook/compiled-retrieval-policy/v1"
assert manifest["schema"] == "rag-rulebook/local-runtime-manifest/v1"
assert validation["schema"] == "rag-rulebook/local-runtime-validation-report/v1"
assert validation["ok"] is True
assert manifest["constraints"]["local_only"] is True
assert manifest["constraints"]["network_calls"] is False
assert manifest["constraints"]["embeddings"] is False
assert set(manifest["fingerprints"]["inputs"]) == {
    "chunk_generation",
    "corpus_gaps",
    "index_inputs",
    "retirements",
    "retrieval_policy",
    "recognition_candidates",
    "recognition_sources",
    "source_derivations",
    "source_material",
    "source_projections",
    "structured_rules",
    "validation_machinery",
}
for fingerprint in manifest["fingerprints"]["inputs"].values():
    assert fingerprint["algorithm"] == "sha256-relpath-content-v1"
    assert len(fingerprint["sha256"]) == 64
    assert isinstance(fingerprint["file_count"], int)
assert ".agentic/02.rag-rulebook/guides" in manifest["fingerprints"]["inputs"]["source_material"]["roots"]
assert manifest["fingerprints"]["runtime_outputs"]["rulebook_index"]["sha256"]
assert manifest["fingerprints"]["runtime_outputs"]["rulebook_chunks"]["sha256"]
assert manifest["fingerprints"]["runtime_outputs"]["compiled_retrieval_policy"]["sha256"]
assert manifest["counts"]["chunk_candidates"] == manifest["counts"]["chunks"]
assert manifest["counts"]["chunks"] > 0
assert manifest["counts"]["compiled_policy_dimensions"] == 15
assert manifest["counts"]["compiled_policy_recognition_sources"] == 7
assert manifest["files"]["rulebook_index"].endswith("rulebook-index.json")
assert manifest["files"]["rulebook_chunks"].endswith("rulebook-chunks.json")
assert manifest["files"]["compiled_retrieval_policy"].endswith("compiled-retrieval-policy.json")
assert validation["reports"]["compiled_retrieval_policy"]["schema"] == "rag-rulebook/compiled-retrieval-policy/v1"
assert compiled_policy["intent_resolution"]["precedence"][0] == "intent.no-action.explanation"
assert compiled_policy["user_intents"][0]["intent_id"] == "user-intent.explain"
assert compiled_policy["evidence_bundles"]
assert compiled_policy["retrieval_strategy"]["strategy_id"] == "retrieval-selector.v1.hybrid-deterministic-first"
PY

echo "Local RAG/rulebook runtime smoke test passed."
