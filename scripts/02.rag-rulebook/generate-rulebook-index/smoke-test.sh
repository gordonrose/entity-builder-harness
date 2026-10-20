#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.generate-rulebook-index.smoke-test
#   version: 4
#   status: active
#   created_on: "2026-06-25"
#   updated_on: "2026-10-20"
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
assert data["diagnostics"]["counts"]["artifacts"] >= 28
assert data["diagnostics"]["counts"]["rule_packs"] == 4
assert data["diagnostics"]["counts"]["rules"] > 0
assert data["diagnostics"]["counts"]["graph_edges"] > 0
assert data["diagnostics"]["counts"]["chunk_candidates"] > data["diagnostics"]["counts"]["rules"]

for candidate in data["chunk_candidates"]:
    assert candidate["chunk_purpose"], candidate["chunk_id"]
    assert candidate["authority"], candidate["chunk_id"]
assert all(
    candidate["authority"] == "execution-authority"
    for candidate in data["chunk_candidates"]
    if candidate["content_kind"] in {"rule", "rule-pack-step", "required-check"}
)
assert all(
    candidate["authority"] == "orientation"
    for candidate in data["chunk_candidates"]
    if candidate["content_kind"] == "artifact-summary"
)
source_explanation_candidates = [
    candidate
    for candidate in data["chunk_candidates"]
    if candidate["content_kind"] == "source-explanation"
]
assert source_explanation_candidates
assert all(candidate["chunk_purpose"] == "source-explanation" for candidate in source_explanation_candidates)
assert all(candidate["authority"] == "explanation-support" for candidate in source_explanation_candidates)
assert any(
    candidate["source_path"] == "docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md"
    and candidate["heading_path"].endswith("Platform Runtime Shell Surfaces")
    and candidate["line_start"] >= 1
    and candidate["line_end"] >= candidate["line_start"]
    for candidate in source_explanation_candidates
)

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
github_deploy_artifact = artifacts_by_path["docs/04.deploy/rules/02.rag-rulebook/github-to-aws-deployment.yml"]
assert github_deploy_artifact["corpus_id"] == "corpus.04.deploy"
assert github_deploy_artifact["migration_status"] == "current"
aws_runtime_artifact = artifacts_by_path["docs/04.deploy/rules/02.rag-rulebook/aws-runtime-boundaries.yml"]
assert aws_runtime_artifact["corpus_id"] == "corpus.04.deploy"
assert aws_runtime_artifact["migration_status"] == "current"
readiness_artifact = artifacts_by_path["docs/04.deploy/rules/02.rag-rulebook/deployment-readiness-checks.yml"]
assert readiness_artifact["corpus_id"] == "corpus.04.deploy"
assert readiness_artifact["migration_status"] == "current"
platform_runtime_source = artifacts_by_path["docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md"]
assert platform_runtime_source["artifact_type"] == "source-material"
assert platform_runtime_source["corpus_id"] == "corpus.03.product.platform"
assert platform_runtime_source["migration_status"] == "current"
path_mappings = {mapping["proposed_path"]: mapping for mapping in data["path_mappings"]}
assert path_mappings["docs/03.product/source-material/platform/platform-runtime-enterprise-obligations-v1.md"]["migration_status"] == "current"

rule_ids = {rule["rule_id"] for rule in data["rules"]}
assert "mcp-server-deployment-architecture.uses-validated-context-packets" in rule_ids
assert "mcp-server-deployment-architecture.transport-auth-model-is-explicit" in rule_ids
assert "mcp-server-deployment.blocks-on-readiness-gaps" in rule_ids
assert "github-to-aws-deployment.prefers-oidc-over-long-lived-secrets" in rule_ids
assert "aws-runtime-boundaries.defines-rollback-and-failure-detection" in rule_ids
assert "deployment-readiness-checks.protects-remote-main-before-deploy" in rule_ids
assert "deployment-readiness-checks.controls-cost-capacity-and-quotas" in rule_ids

deploy_rules = [rule for rule in data["rules"] if rule["corpus_id"] == "corpus.04.deploy"]
assert any(rule["rule_id"] == "mcp-server-deployment.exposes-read-only-mcp-first" for rule in deploy_rules)
assert any(rule["rule_id"] == "github-to-aws-deployment.uses-github-as-release-control-plane" for rule in deploy_rules)
assert any(rule["rule_id"] == "aws-runtime-boundaries.names-target-before-mutation" for rule in deploy_rules)
assert any(rule["rule_id"] == "deployment-readiness-checks.requires-mcp-threat-model-and-access-control" for rule in deploy_rules)
assert any(rule["rule_id"] == "deployment-readiness-checks.controls-cost-capacity-and-quotas" for rule in deploy_rules)

print("Rulebook index smoke test passed.")
print(json.dumps(data["diagnostics"]["counts"], sort_keys=True))
PY

python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import tempfile

import yaml

generator = Path("scripts/02.rag-rulebook/generate-rulebook-index/script.sh").resolve()
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    def write(path, content):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def metadata(name, status, kind, layer):
        result = {"schema": "agentic-artifact/v3", "id": "test." + name, "version": 1,
                  "status": status, "kind": kind, "layer": layer,
                  "created_on": "2020-01-01", "updated_on": "2024-01-01"}
        if status == "superseded":
            result.update(superseded_on="2024-01-01", superseded_by=[{"id": "test.current", "path": "docs/01.harness/source-material/current.md"}])
        return result

    write(".agentic/02.rag-rulebook/plans/prototype-corpus-migration-map.yml", yaml.safe_dump({
        "target_corpora": [{"corpus_id": "corpus.01.harness"}, {"corpus_id": "corpus.02.rag-rulebook"}]
    }))
    fixture_paths = {}
    for family, folder, kind in [
        ("source", "docs/01.harness/source-material", "source-material"),
        ("process", ".agentic/01.harness/standards", "standard"),
    ]:
        for status in ("active", "deprecated", "superseded", "retired"):
            path = f"{folder}/{status}.md"
            fixture_paths[path] = status
            header = metadata(f"{family}.{status}", status, kind, "01.harness")
            write(path, "<!-- agentic-artifact:\n" + yaml.safe_dump(header, sort_keys=False) + "-->\n\n# Fixture\n\nThis document has enough words to produce an explanation chunk when it is current guidance.\n")
    for status in ("active", "superseded"):
        path = f"docs/02.rag-rulebook/rules/concerns/{status}.yml"
        fixture_paths[path] = status
        header = yaml.safe_dump({"agentic-artifact": metadata(f"rules.{status}", status, "rule", "02.rag-rulebook")}, sort_keys=False)
        body = yaml.safe_dump({"id": f"test.rules.{status}", "status": "active", "rules": [{"id": f"test.rule.{status}", "summary": "Fixture rule."}]})
        write(path, "".join("# " + line + "\n" for line in header.splitlines()) + "\n" + body)
    environment = {**os.environ, "RAG_REPO_ROOT": str(root), "RAG_SOURCE_COMMIT_SHA": "a" * 40}
    command = ["bash", str(generator)]
    result = subprocess.run(command, env=environment, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    by_path = {artifact["current_path"]: artifact for artifact in data["artifacts"]}
    for path, status in fixture_paths.items():
        artifact = by_path[path]
        assert artifact["status"] == status, path
        assert artifact["metadata_schema"] == "agentic-artifact/v3", path
        assert artifact["created_on"] == "2020-01-01", path
        if status == "superseded":
            assert artifact["superseded_on"] == "2024-01-01", path
            assert artifact["superseded_by"][0]["id"] == "test.current", path
        candidates = [candidate for candidate in data["chunk_candidates"] if candidate["source_path"] == path]
        assert bool(candidates) == (status == "active"), path
    assert "test.rule.active" in {rule["rule_id"] for rule in data["rules"]}
    assert "test.rule.superseded" not in {rule["rule_id"] for rule in data["rules"]}
    path = root / "docs/01.harness/source-material/active.md"
    path.write_text(path.read_text().replace("agentic-artifact/v3", "agentic-artifact/v99", 1))
    failure = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert failure.returncode != 0 and "Unsupported metadata schema" in failure.stderr
print("Rulebook lifecycle compatibility fixtures passed.")
PY
