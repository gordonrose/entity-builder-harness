#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.compile-retrieval-policy.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-06-28"
#   updated_on: "2026-10-26"
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
assert len(compiled["dimensions"]) == 15
assert len(compiled["recognition_sources"]["sources"]) == 7
assert compiled["recognition_sources"]["counts"]["terms"] > 0
assert compiled["intent_resolution"]["default_intent_id"] == "intent.context.retrieve"
assert compiled["intent_resolution"]["precedence"][0] == "intent.no-action.explanation"
assert compiled["intent_resolution"]["labels"]["intent.deploy.execution"] == "Deploy execution"
assert [intent["intent_id"] for intent in compiled["user_intents"]] == [
    "user-intent.explain",
    "user-intent.troubleshoot",
    "user-intent.validate",
    "user-intent.find-source",
]
assert compiled["evidence_bundles"][0]["question_category_id"] == "question.architecture-boundary.capability-placement"
assert compiled["evidence_bundles"][0]["family_source_paths"]["evidence.layer.apps"].endswith("apps.yml")
assert compiled["retrieval_strategy"]["strategy_id"] == "retrieval-selector.v1.hybrid-deterministic-first"
assert compiled["chunk_selection"]["purpose_priority_by_intent"]["intent.explanation.tutor"][0] == "source-explanation"
assert compiled["chunk_selection"]["side_effect_restrictions"]["authorization_authorities"] == ["execution-authority"]
assert [stage["stage_id"] for stage in compiled["retrieval_strategy"]["stages"]][:3] == [
    "exact-identifiers",
    "generated-concepts",
    "curated-concepts",
]
assert compiled["feature_flags"]["semantic_recall_enabled"] is False
assert len(compiled["content_hash"]) == 64
assert compiled["input_fingerprints"]["policy_pack"]["sha256"]
assert compiled["input_fingerprints"]["compiler"]["sha256"]
assert compiled["rule_graph"]["edge_count"] > 0
PY

python3 - "$INDEX_FILE" "$TMP_DIR" <<'ARCHIVE_TEST'
import json, os, shutil, subprocess, sys
from pathlib import Path
root=Path.cwd(); fixture=Path(sys.argv[2])/'source-archive';fixture.mkdir()
for directory in ['.agentic','.github','scripts','infra','docs']:
    shutil.copytree(root/directory,fixture/directory,ignore=shutil.ignore_patterns('__pycache__','node_modules','.cache'))
for name in ['package.json','AGENTS.md','packages/core/README.md','packages/core/src/index.ts','packages/core/src/audit/index.ts','packages/core/src/queues/index.ts','platform/contracts/README.md','platform/adapters/README.md']:
    path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,path)
source_commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
env={**os.environ,'RAG_REPO_ROOT':str(fixture),'RAG_SOURCE_COMMIT_SHA':source_commit}
# Match the real packaged-source runtime: derive recognition from the files
# actually exported into the archive, rather than retaining checkout-only
# artifact references for application/test files the archive does not carry.
regenerated=subprocess.run(['bash',str(root/'scripts/02.rag-rulebook/generate-recognition-sources/script.sh'),'--write-all'],env=env,text=True,capture_output=True)
assert regenerated.returncode==0,regenerated.stderr
command=['bash',str(root/'scripts/02.rag-rulebook/compile-retrieval-policy/script.sh'),'--current','--index',sys.argv[1]]
result=subprocess.run(command,env=env,text=True,capture_output=True)
assert result.returncode!=0 and 'source path does not exist: .codex/rules/governed-scripts.rules' in result.stderr,(result.returncode,result.stderr)
result=subprocess.run(command+['--source-layout','packaged-source-archive'],env=env,text=True,capture_output=True)
assert result.returncode==0,result.stderr
compiled=json.loads(result.stdout)
assert compiled['source_layout']=='packaged-source-archive'
bundle=next(item for item in compiled['evidence_bundles'] if item['question_category_id']=='question.harness.governed-script-permissions')
expected={'.codex/rules/governed-scripts.rules','.claude/settings.json','.vibe/config.toml'}
assert set(bundle['unavailable_sources'])==expected
assert expected.issubset(bundle['always_source_paths']) and all(bundle['unavailable_sources'].values())
(fixture/'AGENTS.md').unlink()
result=subprocess.run(command+['--source-layout','packaged-source-archive'],env=env,text=True,capture_output=True)
assert result.returncode!=0 and 'source path does not exist: AGENTS.md' in result.stderr,(result.returncode,result.stderr)
print('Archive evidence availability CLI checks passed (3).')
ARCHIVE_TEST

echo "Compiled retrieval policy smoke test passed."
