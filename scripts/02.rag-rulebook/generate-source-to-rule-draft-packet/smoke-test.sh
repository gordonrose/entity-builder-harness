#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-source-to-rule-draft-packet.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the source-to-rule draft packet generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-source-to-rule-draft-packet
#       path: scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REPORT="$TMP_DIR/draft-packet.json"

bash scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/script.sh \
  --current \
  --projection-id projection.04.deploy.02-rag-rulebook.mcp-server-deployment \
  --max-file-chars 20000 \
  --json > "$REPORT"

python3 - "$REPORT" <<'PY'
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert report["schema"] == "rag-rulebook/source-to-rule-draft-packet/v1"
assert report["ok"] is True
assert report["counts"]["draft_packets"] == 1

packet = report["draft_packets"][0]
assert packet["projection_id"] == "projection.04.deploy.02-rag-rulebook.mcp-server-deployment"
assert packet["target"]["corpus_id"] == "corpus.04.deploy"
assert packet["draft_objectives"]
assert packet["banned_actions"]
assert packet["work_actions"]
assert packet["required_checks"]
assert packet["source_material"][0]["content"]
assert "MCP Server Deployment Source Material" in packet["source_material"][0]["content"]
assert packet["current_rule_files"]
assert packet["derivation_reports"]
assert packet["corpus_gaps"]
assert packet["selector_evaluations"]

for group in ["source_material", "current_rule_files", "derivation_reports", "corpus_gaps", "selector_evaluations"]:
    for item in packet[group]:
        assert item["path"]
        assert item["exists"] is True
        assert item["sha256"]
        assert isinstance(item["content"], str)
        assert isinstance(item["truncated"], bool)

print("Source-to-rule draft packet smoke assertions passed.")
PY

echo "Source-to-rule draft packet smoke test passed."
