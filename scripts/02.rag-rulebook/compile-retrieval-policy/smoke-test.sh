#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.compile-retrieval-policy.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the compiled retrieval policy generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.compile-retrieval-policy
#       path: scripts/02.rag-rulebook/compile-retrieval-policy/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INDEX_FILE="$TMP_DIR/rulebook-index.json"
COMPILED_FILE="$TMP_DIR/compiled-retrieval-policy.json"

bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh \
  --pretty > "$INDEX_FILE"

bash scripts/02.rag-rulebook/compile-retrieval-policy/script.sh \
  --current \
  --index "$INDEX_FILE" \
  --output "$COMPILED_FILE" \
  --pretty

python3 - "$COMPILED_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

compiled = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert compiled["schema"] == "rag-rulebook/compiled-retrieval-policy/v1"
assert compiled["compiled_policy_id"].startswith("compiled.retrieval-policy.retrieval-selector.v1.")
assert compiled["policy_pack"]["policy_pack_id"] == "retrieval-selector.v1"
assert len(compiled["dimensions"]) == 14
assert len(compiled["recognition_sources"]["sources"]) == 7
assert compiled["recognition_sources"]["counts"]["terms"] > 0
assert compiled["intent_resolution"]["default_intent_id"] == "intent.context.retrieve"
assert compiled["intent_resolution"]["precedence"][0] == "intent.no-action.explanation"
assert compiled["intent_resolution"]["labels"]["intent.deploy.execution"] == "Deploy execution"
assert compiled["evidence_bundles"][0]["question_category_id"] == "question.architecture-boundary.capability-placement"
assert compiled["evidence_bundles"][0]["family_source_paths"]["evidence.layer.apps"].endswith("apps.yml")
assert compiled["feature_flags"]["semantic_recall_enabled"] is False
assert len(compiled["content_hash"]) == 64
assert compiled["input_fingerprints"]["policy_pack"]["sha256"]
assert compiled["input_fingerprints"]["compiler"]["sha256"]
assert compiled["rule_graph"]["edge_count"] > 0
PY

echo "Compiled retrieval policy smoke test passed."
