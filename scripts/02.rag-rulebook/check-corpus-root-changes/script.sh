#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-corpus-root-changes
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Detect changed governed RAG/rulebook corpus-root files and require coverage, indexing, chunking, or retirement proof.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.check-corpus-root-changes.readme
#       path: scripts/02.rag-rulebook/check-corpus-root-changes/README.md
#     - id: rag-rulebook.script.check-corpus-root-changes.smoke-test
#       path: scripts/02.rag-rulebook/check-corpus-root-changes/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for corpus-root change checks.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/corpus-root-change-check-report/v1"
SOURCE_ROOTS = [
    "docs/02.rag-rulebook/source-material",
    "docs/04.deploy/source-material",
]
RULE_ROOTS = [
    "docs/02.rag-rulebook/rules",
    "docs/04.deploy/rules",
]
GOVERNED_ROOTS = [
    *SOURCE_ROOTS,
    *RULE_ROOTS,
    ".agentic/02.rag-rulebook/source-projections",
    ".agentic/02.rag-rulebook/derivation-reports",
    ".agentic/02.rag-rulebook/corpus-gaps",
    ".agentic/02.rag-rulebook/evaluations",
    ".agentic/02.rag-rulebook/recognition-sources",
    ".agentic/02.rag-rulebook/recognition-candidates",
]
RETIREMENT_RECORD_ROOT = ".agentic/02.rag-rulebook/retirements"
INDEX_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-index/script.sh"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"
SOURCE_COVERAGE_SCRIPT = "scripts/02.rag-rulebook/check-source-material-coverage/script.sh"


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


ROOT = repo_root()


def usage() -> str:
    return """Usage:
  check-corpus-root-changes/script.sh --current [--json]
  check-corpus-root-changes/script.sh --changes-file <path> [--json]

Detects changes under governed RAG/rulebook corpus roots. Deleted or renamed
old paths require accepted retirement records. Existing changed rule files must
reach the generated index and chunk set. Existing changed source-material files
require source-material coverage to remain valid.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--changes-file")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.changes_file):
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_under(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def is_source_path(path: str) -> bool:
    return is_under(path, SOURCE_ROOTS) and path.endswith(".md") and Path(path).name != "README.md"


def is_rule_path(path: str) -> bool:
    return is_under(path, RULE_ROOTS) and path.endswith((".yml", ".yaml"))


def is_governed_path(path: str) -> bool:
    return is_under(path, GOVERNED_ROOTS)


def load_yaml(path: str | Path, errors: list[str]) -> dict[str, Any] | None:
    path_obj = repo_path(path)
    try:
        data = yaml.safe_load(path_obj.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"{rel(path_obj)} failed to parse as YAML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{rel(path_obj)} must contain a YAML object")
        return None
    return data


def list_files(roots: list[str], suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        root_path = repo_path(root)
        if not root_path.exists():
            continue
        candidates = [root_path] if root_path.is_file() else sorted(root_path.rglob("*"))
        for path in candidates:
            if path.is_file() and path.suffix.lower() in suffixes:
                files.append(path)
    return sorted(set(files))


def load_accepted_retirements(errors: list[str]) -> dict[str, list[str]]:
    retired_by_path: dict[str, list[str]] = {}
    for path in list_files([RETIREMENT_RECORD_ROOT], {".yml", ".yaml"}):
        record_path = rel(path)
        data = load_yaml(record_path, errors)
        if data is None:
            continue
        if data.get("schema") != "rag-rulebook/retirement-record/v1":
            errors.append(f"{record_path}.schema must be rag-rulebook/retirement-record/v1")
            continue
        if data.get("status") != "accepted":
            continue
        retirement_id = data.get("retirement_id")
        if not isinstance(retirement_id, str) or not retirement_id.strip():
            errors.append(f"{record_path}.retirement_id must be a non-empty string")
            retirement_id = record_path
        artifacts = data.get("retired_artifacts")
        if not isinstance(artifacts, list):
            errors.append(f"{record_path}.retired_artifacts must be an array")
            continue
        for index, artifact in enumerate(artifacts, start=1):
            owner = f"{record_path}.retired_artifacts[{index}]"
            if not isinstance(artifact, dict):
                errors.append(f"{owner} must be an object")
                continue
            path_value = artifact.get("path")
            if not isinstance(path_value, str) or not path_value.strip():
                errors.append(f"{owner}.path must be a non-empty string")
                continue
            retired_by_path.setdefault(path_value, []).append(retirement_id)
    return {path: sorted(set(ids)) for path, ids in retired_by_path.items()}


def parse_status_line(line: str) -> list[dict[str, str]]:
    parts = line.rstrip("\n").split("\t")
    if not parts or not parts[0]:
        return []
    status = parts[0]
    code = status[0]
    if code == "R":
        if len(parts) < 3:
            return []
        return [
            {"status": "R-old", "path": parts[1], "counterpart": parts[2]},
            {"status": "R-new", "path": parts[2], "counterpart": parts[1]},
        ]
    if len(parts) < 2:
        return []
    return [{"status": code, "path": parts[1], "counterpart": ""}]


def current_changes() -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "diff", "--name-status", "--find-renames", "HEAD", "--", *GOVERNED_ROOTS],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    changes: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        changes.extend(parse_status_line(line))

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *GOVERNED_ROOTS],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    tracked_paths = {change["path"] for change in changes}
    for path in sorted(value for value in untracked.stdout.splitlines() if value):
        if path not in tracked_paths:
            changes.append({"status": "?", "path": path, "counterpart": ""})
    return sorted(changes, key=lambda item: (item["path"], item["status"]))


def fixture_changes(path: str) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for line in repo_path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        changes.extend(parse_status_line(line))
    return sorted(changes, key=lambda item: (item["path"], item["status"]))


def generate_index_and_chunks() -> tuple[dict[str, Any], dict[str, Any]]:
    index_result = subprocess.run(
        ["bash", INDEX_GENERATOR_SCRIPT],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    chunks_result = subprocess.run(
        ["bash", CHUNK_GENERATOR_SCRIPT, "--generate-current"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return json.loads(index_result.stdout), json.loads(chunks_result.stdout)


def indexed_rule_paths(index: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for artifact in index.get("artifacts") or []:
        if isinstance(artifact, dict):
            path = artifact.get("current_path")
            if isinstance(path, str) and is_rule_path(path):
                paths.add(path)
    for candidate in index.get("chunk_candidates") or []:
        if isinstance(candidate, dict):
            path = candidate.get("source_path")
            if isinstance(path, str) and is_rule_path(path):
                paths.add(path)
    return paths


def chunked_rule_paths(chunks: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for chunk in chunks.get("chunks") or []:
        if isinstance(chunk, dict):
            path = chunk.get("source_path")
            if isinstance(path, str) and is_rule_path(path):
                paths.add(path)
    return paths


def source_coverage_report() -> dict[str, Any]:
    result = subprocess.run(
        ["bash", SOURCE_COVERAGE_SCRIPT, "--current", "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        report = {
            "schema": "rag-rulebook/source-material-coverage-report/v1",
            "ok": False,
            "errors": [result.stdout.strip() or "source-material coverage produced invalid JSON"],
        }
    if result.returncode != 0:
        report["ok"] = False
    return report


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    changes = current_changes() if args.current else fixture_changes(args.changes_file)
    governed_changes = [item for item in changes if is_governed_path(item["path"])]
    accepted_retirements = load_accepted_retirements(errors)

    deleted_or_old = [
        item for item in governed_changes if item["status"] in {"D", "R-old"}
    ]
    for item in deleted_or_old:
        path = item["path"]
        if path not in accepted_retirements:
            errors.append(f"{item['status']} governed path lacks accepted retirement record: {path}")

    existing_source_changes = [
        item
        for item in governed_changes
        if item["status"] not in {"D", "R-old"} and is_source_path(item["path"]) and repo_path(item["path"]).is_file()
    ]
    source_coverage = None
    if existing_source_changes:
        source_coverage = source_coverage_report()
        if not source_coverage.get("ok"):
            errors.append("changed source-material files require valid source-material coverage")

    existing_rule_changes = [
        item
        for item in governed_changes
        if item["status"] not in {"D", "R-old"} and is_rule_path(item["path"]) and repo_path(item["path"]).is_file()
    ]
    indexed_rules: set[str] = set()
    chunked_rules: set[str] = set()
    if existing_rule_changes:
        index, chunks = generate_index_and_chunks()
        indexed_rules = indexed_rule_paths(index)
        chunked_rules = chunked_rule_paths(chunks)
        for item in existing_rule_changes:
            path = item["path"]
            if path not in indexed_rules:
                errors.append(f"changed rule path is not present in generated index: {path}")
            if path not in chunked_rules:
                errors.append(f"changed rule path is not present in generated chunks: {path}")

    report = {
        "schema": REPORT_SCHEMA,
        "ok": not errors,
        "mode": "current" if args.current else "changes-file",
        "governed_roots": GOVERNED_ROOTS,
        "counts": {
            "changes": len(changes),
            "governed_changes": len(governed_changes),
            "deleted_or_renamed_old_paths": len(deleted_or_old),
            "existing_source_changes": len(existing_source_changes),
            "existing_rule_changes": len(existing_rule_changes),
            "accepted_retirement_paths": len(accepted_retirements),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "changes": governed_changes,
        "accepted_retirements": accepted_retirements,
        "source_coverage": source_coverage,
        "changed_rule_indexed_paths": sorted(path for path in {item["path"] for item in existing_rule_changes} if path in indexed_rules),
        "changed_rule_chunked_paths": sorted(path for path in {item["path"] for item in existing_rule_changes} if path in chunked_rules),
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    else:
        print(f"Corpus root changes valid: {len(governed_changes)} governed change(s).")
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
