#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-rulebook-index.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: indexing
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only prototype rulebook index generator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.generate-rulebook-index
#       path: scripts/02.rag-rulebook/generate-rulebook-index/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INDEX_FILE="$TMP_DIR/rulebook-index.json"

bash scripts/02.rag-rulebook/generate-rulebook-index/script.sh --pretty > "$INDEX_FILE"

python3 - "$INDEX_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

index_path = Path(sys.argv[1])
data = json.loads(index_path.read_text(encoding="utf-8"))

assert data["schema"] == "rag-rulebook/rulebook-index/v1"
assert data["diagnostics"]["ok"], data["diagnostics"]
assert data["diagnostics"]["counts"]["corpus_packages"] >= 10
assert data["diagnostics"]["counts"]["artifacts"] >= 27
assert data["diagnostics"]["counts"]["rule_packs"] == 4
assert data["diagnostics"]["counts"]["rules"] > 0
assert data["diagnostics"]["counts"]["graph_edges"] > 0
assert data["diagnostics"]["counts"]["chunk_candidates"] > data["diagnostics"]["counts"]["rules"]

source_roots = {root["root_id"]: root for root in data["source_roots"]}
assert source_roots["root.rulebook-rules"]["path"] == "docs/02.rag-rulebook/rules"
assert source_roots["root.rulebook-rules"]["role"] == "corpus-package"
assert source_roots["root.corpus.04.deploy.rules"]["path"] == "docs/04.deploy/rules"
assert source_roots["root.corpus.04.deploy.rules"]["role"] == "corpus-package"
assert source_roots["root.corpus.04.deploy.rules"]["corpus_id"] == "corpus.04.deploy"

corpus_packages = {package["corpus_id"]: package for package in data["corpus_packages"]}
assert corpus_packages["corpus.04.deploy"]["status"] == "current"
assert corpus_packages["corpus.04.deploy"]["proposed_root"] == "docs/04.deploy/rules"

artifacts_by_path = {artifact["current_path"]: artifact for artifact in data["artifacts"]}
mcp_artifact = artifacts_by_path["docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml"]
assert mcp_artifact["corpus_id"] == "corpus.02.rag-rulebook"
assert mcp_artifact["migration_status"] == "current"
deploy_artifact = artifacts_by_path["docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml"]
assert deploy_artifact["corpus_id"] == "corpus.04.deploy"
assert deploy_artifact["migration_status"] == "current"

rule_ids = {rule["rule_id"] for rule in data["rules"]}
assert "mcp-server-deployment-architecture.uses-validated-context-packets" in rule_ids
assert "mcp-server-deployment.blocks-on-readiness-gaps" in rule_ids

deploy_rules = [rule for rule in data["rules"] if rule["corpus_id"] == "corpus.04.deploy"]
assert any(rule["rule_id"] == "mcp-server-deployment.exposes-read-only-mcp-first" for rule in deploy_rules)

print("Rulebook index smoke test passed.")
print(json.dumps(data["diagnostics"]["counts"], sort_keys=True))
PY
