#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.generate-index-smoke-test
#   version: 2
#   status: active
#   created_on: "2026-06-24"
#   updated_on: "2026-10-20"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Smoke test artifact metadata index generation for compatible legacy and lifecycle headers.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: harness.script.artifact-metadata.generate-index
#       path: scripts/01.harness/artifact-metadata/generate-index/script.sh

repo_root="$(git rev-parse --show-toplevel)"
generator="$repo_root/scripts/01.harness/artifact-metadata/generate-index/script.sh"

json_output="$(bash "$generator" --paths \
  .agentic/01.harness/artifact-metadata/examples/markdown.v2.md \
  .agentic/01.harness/artifact-metadata/examples/yaml.v2.yml \
  scripts/01.harness/artifact-metadata/check-headers/script.sh \
  scripts/01.harness/check-artifact-metadata-headers.sh \
  docs/02.rag-rulebook/rules/README.md \
  docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml \
  docs/03.product/rules/core/layers/packages-core.yml)"

python3 -c '
import json, sys
data = json.load(sys.stdin)
paths = {artifact["path"]: artifact for artifact in data["artifacts"]}
assert data["schema"] == "agentic-artifact-index/v1"
assert data["summary"]["v2_artifacts"] + data["summary"]["v3_artifacts"] >= 7
assert data["summary"]["legacy_artifacts"] == 0
assert paths[".agentic/01.harness/artifact-metadata/examples/markdown.v2.md"]["id"] == "harness.example.artifact-metadata.markdown-v2"
assert paths["scripts/01.harness/artifact-metadata/check-headers/script.sh"]["kind"] == "script"
assert paths["scripts/01.harness/check-artifact-metadata-headers.sh"]["metadata_schema"] == "agentic-artifact/v3"
assert paths["scripts/01.harness/check-artifact-metadata-headers.sh"]["id"] == "harness.script.artifact-metadata.check-headers-compatibility-wrapper"
assert paths["docs/02.rag-rulebook/rules/README.md"]["layer"] == "02.rag-rulebook"
assert paths["docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml"]["kind"] == "rule"
' <<< "$json_output"

python3 - "$generator" <<'PY'
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import yaml

# Compile only the legacy selector functions; never execute its mutation/commit path.
legacy_script = Path(sys.argv[1]).parent.parent / "backfill-v2-headers/script.sh"
legacy_source = legacy_script.read_text().split("python3 - \"$batch\" > \"$paths_file\" <<'PY'\n", 1)[1].split("\nPY", 1)[0]
function_names = {"strip_comment", "parse_header", "existing_metadata", "has_versioned_header", "selected_for_batch"}
functions = [node for node in ast.parse(legacy_source).body if isinstance(node, ast.FunctionDef) and node.name in function_names]
legacy = {"Path": Path, "Any": Any, "yaml": yaml, "batch": 1}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(legacy_script), "exec"), legacy)

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    docs = root / "docs/01.harness"
    docs.mkdir(parents=True)
    replacement = "docs/01.harness/current.md"
    for name, fields in {
        "old.md": 'schema: agentic-artifact/v3\nid: test.old\nstatus: superseded\ncreated_on: "2020-02-29"\nupdated_on: "2024-03-01"\ndeprecated_on: "2023-01-01"\nsuperseded_on: "2024-03-01"\nsuperseded_by:\n- id: test.current\n  path: ' + replacement,
        "current.md": "schema: agentic-artifact/v2\nid: test.current\nstatus: active",
        "legacy.md": "kind: guide\npurpose: Legacy metadata without a declared schema.",
    }.items():
        (docs / name).write_text("<!-- agentic-artifact:\n" + fields + "\n-->\n")
    environment = {**os.environ, "RAG_REPO_ROOT": str(root), "RAG_SOURCE_COMMIT_SHA": "a" * 40}
    command = ["bash", sys.argv[1], "--paths", "docs/01.harness", "--strict"]
    result = subprocess.run(command, env=environment, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    assert data["summary"]["v3_artifacts"] == 1
    assert data["summary"]["v2_artifacts"] == 1
    assert data["summary"]["legacy_artifacts"] == 1
    artifact = next(item for item in data["artifacts"] if item.get("id") == "test.old")
    assert artifact["metadata_schema"] == "agentic-artifact/v3" and not artifact["legacy"]
    assert artifact["status"] == "superseded"
    assert artifact["created_on"] == "2020-02-29"
    assert artifact["updated_on"] == artifact["superseded_on"] == "2024-03-01"
    assert artifact["deprecated_on"] == "2023-01-01"
    assert artifact["superseded_by"] == [{"id": "test.current", "path": replacement}]
    (docs / "unknown.md").write_text("<!-- agentic-artifact:\nschema: agentic-artifact/v99\n-->\n")
    failure = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert failure.returncode != 0 and "unsupported metadata schema" in failure.stderr
    skipped = json.loads(subprocess.run(command[:-1], env=environment, check=True, capture_output=True, text=True).stdout)
    assert skipped["summary"]["skipped"] == 1 and skipped["summary"]["legacy_artifacts"] == 1
    for invalid_header, error in [
        ('schema: null', 'unsupported metadata schema'),
        ('schema: agentic-artifact/v3\ncreated_on: 2024-01-01\nupdated_on: "2024-01-01"', 'created_on must be a quoted'),
        ('schema: agentic-artifact/v3\ncreated_on: "2024-02-30"\nupdated_on: "2024-03-01"', 'created_on must be a valid calendar'),
        ('schema: agentic-artifact/v3\ncreated_on: "2024-01-01"', 'updated_on must be a quoted'),
    ]:
        (docs / "unknown.md").write_text("<!-- agentic-artifact:\n" + invalid_header + "\n-->\n")
        failure = subprocess.run(command, env=environment, capture_output=True, text=True)
        assert failure.returncode != 0 and error in failure.stderr and "Traceback" not in failure.stderr
        skipped = json.loads(subprocess.run(command[:-1], env=environment, check=True, capture_output=True, text=True).stdout)
        assert skipped["summary"]["skipped"] == 1

    status_root = root / "status-fixture"
    (status_root / "docs").mkdir(parents=True)
    (status_root / "docs/v2.md").write_text("<!-- agentic-artifact:\nschema: agentic-artifact/v2\n-->\nExample: schema: agentic-artifact/v3\n")
    (status_root / "docs/v3.md").write_text("<!-- agentic-artifact:\nschema: agentic-artifact/v3\n-->\n")
    (status_root / "docs/legacy.md").write_text("<!-- agentic-artifact:\nkind: guide\n-->\n")
    status = subprocess.run(["bash", str(legacy_script), "--status"], cwd=status_root, check=True, capture_output=True, text=True)
    assert status.stdout.strip() == "v2=1 v3=1 legacy=1 missing=0"

    previous_cwd = Path.cwd()
    try:
        os.chdir(root)
        fixture = Path(".agentic/01.harness/README.md")
        fixture.parent.mkdir(parents=True)
        for schema, selected in [("agentic-artifact/v1", True), ("agentic-artifact/v2", False), ("agentic-artifact/v3", False)]:
            fixture.write_text("<!-- agentic-artifact:\nschema: " + schema + "\n-->\n")
            assert legacy["selected_for_batch"](fixture) == selected
        fixture.write_text("<!-- agentic-artifact:\nschema: agentic-artifact/v99\n-->\n")
        try:
            legacy["selected_for_batch"](fixture)
        except ValueError as exc:
            assert "Unsupported metadata schema" in str(exc)
        else:
            raise AssertionError("Legacy backfill must reject unknown versions instead of downgrading them")
    finally:
        os.chdir(previous_cwd)
PY

echo "Artifact metadata index generator smoke test passed."
