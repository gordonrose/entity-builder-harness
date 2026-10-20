#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.generate-index-smoke-test
#   version: 3
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
#     - writes-files
#     - stages-files
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
import shutil
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

# Exercise the shipped capability and library together, without importing from
# an overridden source archive or accidentally traversing the calling checkout.
with tempfile.TemporaryDirectory(prefix="artifact-discovery-index-") as temporary:
    temporary = Path(temporary)
    root = temporary / "repository"
    root.mkdir()
    capability = temporary / "capability/artifact-metadata/generate-index/script.sh"
    capability.parent.mkdir(parents=True)
    shutil.copyfile(sys.argv[1], capability)
    library = Path(sys.argv[1]).resolve().parents[1] / "header_discovery.py"
    shutil.copyfile(library, capability.parents[1] / "header_discovery.py")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    environment = {**os.environ, "RAG_REPO_ROOT": str(root), "RAG_SOURCE_COMMIT_SHA": "b" * 40}

    def write(path, content):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return target

    def header(identity, prefix="#"):
        fields = "schema: agentic-artifact/v2\nid: test.discovery." + identity + "\nstatus: active\n"
        if prefix == "<!--":
            return "<!-- agentic-artifact:\n" + fields + "-->\n"
        return prefix + " agentic-artifact:\n" + "".join(prefix + "   " + line + "\n" for line in fields.splitlines())

    def generate(*args, succeeds=True, env=None):
        result = subprocess.run(["bash", str(capability), *args], cwd=temporary,
                                env=environment if env is None else env, capture_output=True, text=True)
        assert (result.returncode == 0) == succeeds, result.stderr + result.stdout
        assert "Traceback" not in result.stderr
        return json.loads(result.stdout) if succeeds else result

    declared = {
        "application/component.ts": header("typescript", "//") + "export const x = 1;\n",
        "tools/inspect.py": '#!/usr/bin/env python3\n"""Python module description."""\n\n' + header("python") + "print('body')\n",
        "containers/Dockerfile": "# syntax=docker/dockerfile:1.7\n\n" + header("docker") + "FROM scratch\n",
        "custom/metadata.anything": header("arbitrary", "<!--") + "# Body\n",
        "infra/provider/foundation.yml": header("infra") + "Resources: {}\n",
        ".agentic/01.harness/artifact-metadata/examples/markdown.v2.md": header("example", "<!--") + "# Example\n",
    }
    for path, content in declared.items():
        write(path, content)
    write("application/headerless.ts", "export const x = 2;\n")
    write("examples/fenced.md", "# Example\n\n```md\n" + header("fenced", "<!--") + "```\n")
    write("examples/heredoc.sh", "cat <<'EOF'\n" + header("heredoc") + "EOF\n")
    write("examples/docstring.py", '#!/usr/bin/env python3\n"""\n' + header("docstring") + '"""\nprint(1)\n')
    write("examples/patch.diff", "diff --git a/a b/a\n+" + header("patch").replace("\n", "\n+"))
    excluded = ["docs/00.chat/bootstrap/llm-workbench-template/root/" + suffix for suffix in (
        "scripts/install.sh.template", "scripts/uninstall.sh.template",
        ".github/workflows/portability.yml.template",
    )]
    for path in excluded:
        write(path, "# agentic-artifact:\n#   schema: [unexpanded ${PLACEHOLDER}\n")
    write(".gitignore", "ignored/\n")
    write("ignored/declared.custom", header("ignored"))
    (root / "binary.asset").write_bytes(b"\0\xff\x80")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    declared["new/untracked.py"] = header("untracked") + "print(3)\n"
    write("new/untracked.py", declared["new/untracked.py"])
    outside = temporary / "outside.txt"
    outside.write_text(header("outside"))
    (root / "linked.custom").symlink_to(outside)

    snapshot = {path: ((root / path).read_bytes(), (root / path).stat().st_mtime_ns) for path in declared}
    index_tree = subprocess.check_output(["git", "-C", str(root), "write-tree"])
    data = generate("--all", "--strict", "--check-coverage")
    assert {item["path"] for item in data["artifacts"]} == set(declared)
    assert data["git_commit"] == "b" * 40
    assert data["coverage"] == {"scope": "tracked-and-untracked", "declared_artifacts": len(declared),
                                "indexed_declared_artifacts": len(declared), "missing_paths": []}
    assert data["summary"]["v2_artifacts"] == len(declared)
    # Fault injection reproduces the original class of omission: a candidate
    # collector drops a valid declaration. The independent coverage scan must
    # still see it and fail, even though ordinary indexing returns valid JSON.
    capability_source = capability.read_text()
    narrowed = capability_source.replace(
        "    return repository_paths(ROOT)",
        "    return [path for path in repository_paths(ROOT) if path != 'application/component.ts']", 1
    )
    assert narrowed != capability_source
    capability.write_text(narrowed)
    try:
        assert "application/component.ts" not in {item["path"] for item in generate("--all")["artifacts"]}
        failure = generate("--all", "--check-coverage", succeeds=False)
        assert "declared artifact missing from index: application/component.ts" in failure.stderr
    finally:
        capability.write_text(capability_source)
    assert all(((root / path).read_bytes(), (root / path).stat().st_mtime_ns) == value for path, value in snapshot.items())
    assert subprocess.check_output(["git", "-C", str(root), "write-tree"]) == index_tree
    assert not list(temporary.rglob("__pycache__")), "read-only imports must not create bytecode files"
    assert generate("--paths", *excluded, "--strict")["summary"]["artifacts"] == 0
    assert "requires --all" in generate("--paths", "application", "--check-coverage", succeeds=False).stderr
    assert "symlink" in generate("--paths", "linked.custom", succeeds=False).stderr
    assert "inside source root" in generate("--paths", str(outside), succeeds=False).stderr

    # A declared malformed header outside every mandatory scope cannot be hidden
    # by non-strict indexing when the explicit coverage check is requested.
    broken = write("outside/broken.custom", "# agentic-artifact:\n#   schema: [unterminated\n")
    skipped = generate("--all")
    assert skipped["summary"]["skipped"] == 1
    failure = generate("--all", "--check-coverage", succeeds=False)
    assert "outside/broken.custom" in failure.stderr and "invalid metadata YAML" in failure.stderr
    broken.write_text("# agentic-artifact:\n#   schema: agentic-artifact/v99\n")
    assert "unsupported metadata schema" in generate("--all", "--check-coverage", succeeds=False).stderr
    for invalid in (header("invalid-utf8").encode() + b"\xff", header("nul-body").encode() + b"\0"):
        broken.write_bytes(invalid)
        failure = generate("--all", "--check-coverage", succeeds=False)
        assert "outside/broken.custom" in failure.stderr
    broken.unlink()
    # Discovery does not broaden which headerless files require metadata.
    missing = write("scripts/missing.sh", "#!/usr/bin/env bash\nprintf 'hello'\n")
    assert generate("--all", "--check-coverage")["summary"]["skipped"] == 1
    assert "missing metadata header" in generate("--all", "--strict", succeeds=False).stderr
    missing.unlink()

    # An exported root nested inside another checkout is still an archive, not
    # the parent Git repository. Embedded examples and symlinks remain excluded.
    archive = root / "exported-snapshot"
    archive.mkdir()
    (archive / "component.ts").write_text(declared["application/component.ts"])
    (archive / "example.md").write_text("```md\n" + header("archive-example", "<!--") + "```\n")
    (archive / "link.custom").symlink_to(outside)
    for name in (".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"):
        ignored = archive / name
        ignored.mkdir()
        (ignored / "ignored.custom").write_text(header("archive-ignored-" + name.replace(".", "")))
    archive_env = {**environment, "RAG_REPO_ROOT": str(archive), "RAG_SOURCE_COMMIT_SHA": "c" * 40}
    data = generate("--all", "--strict", "--check-coverage", env=archive_env)
    assert [item["path"] for item in data["artifacts"]] == ["component.ts"]
    assert data["coverage"]["scope"] == "source-archive" and data["git_commit"] == "c" * 40
    archive_env.pop("RAG_SOURCE_COMMIT_SHA")
    assert "RAG_SOURCE_COMMIT_SHA is required" in generate("--all", env=archive_env, succeeds=False).stderr

PY

echo "Artifact metadata index generator smoke test passed."
