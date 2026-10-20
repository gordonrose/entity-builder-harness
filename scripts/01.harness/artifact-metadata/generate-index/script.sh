#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.generate-index
#   version: 3
#   status: active
#   created_on: "2026-06-24"
#   updated_on: "2026-10-20"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Generate a machine-readable artifact metadata index from v1, v2, and v3 headers.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: harness.standard.artifact-metadata
#       path: .agentic/01.harness/artifact-metadata/standard.md

python3 - "${BASH_SOURCE[0]}" "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Resolve support code from this capability, never an overridden source root.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[1]))
try:
    from header_discovery import (
        HeaderError, has_declared_header, is_excluded, parse_header_text,
        requires_header, repository_paths,
    )
except ImportError as exc:  # pragma: no cover - environment gate
    print(f"ERROR: artifact metadata discovery support is required: {exc}", file=sys.stderr)
    sys.exit(2)


class IndexErrorInfo(Exception):
    pass


def repo_root() -> Path:
    override = os.environ.get("RAG_REPO_ROOT")
    if override:
        return Path(override).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


ROOT = repo_root()


def is_git_root() -> bool:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == ROOT


GIT_ROOT = is_git_root()


def source_commit() -> str:
    override = os.environ.get("RAG_SOURCE_COMMIT_SHA", "").strip()
    if override:
        return override
    if not GIT_ROOT:
        raise IndexErrorInfo("RAG_SOURCE_COMMIT_SHA is required for a source archive without Git metadata")
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise IndexErrorInfo("source repository has no HEAD; provide RAG_SOURCE_COMMIT_SHA")
    return result.stdout.strip()


def usage() -> str:
    return """Usage:
  generate-index.sh --paths <path> [path...] [--pretty] [--strict]
  generate-index.sh --all [--pretty] [--strict] [--check-coverage]

Emits an agentic artifact metadata index as JSON to stdout. By default, files
without parseable metadata are skipped and counted in the summary. Use --strict
to fail when a required or declared file cannot be indexed. --all scans tracked
and untracked files outside Git ignore rules for file-level declarations; existing
required-header scopes remain unchanged. --check-coverage requires --all and fails
if any declared artifact is malformed or absent from the emitted index.

RAG_REPO_ROOT can select a source archive without Git metadata. Archives are walked
without following symlinks, excluding repository internals and conventional build/
dependency directories, and require RAG_SOURCE_COMMIT_SHA for provenance.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--check-coverage", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)

    if args.help:
        print(usage(), end="")
        sys.exit(0)
    modes = [args.all, args.paths is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one collection mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.paths == []:
        print("ERROR: --paths requires at least one path.", file=sys.stderr)
        sys.exit(2)
    if args.check_coverage and not args.all:
        print("ERROR: --check-coverage requires --all.", file=sys.stderr)
        sys.exit(2)
    return args


def normalize_path(path: Path | str) -> str:
    path_obj = Path(path)
    absolute = path_obj if path_obj.is_absolute() else ROOT / path_obj
    if any(item.is_symlink() for item in (absolute, *absolute.parents)):
        raise IndexErrorInfo(f"symlink paths are not supported: {path}")
    try:
        relative = absolute.resolve().relative_to(ROOT)
    except ValueError as exc:
        raise IndexErrorInfo(f"path must stay inside source root: {path}") from exc
    if ".git" in relative.parts:
        raise IndexErrorInfo(f"Git metadata is not an artifact path: {path}")
    return relative.as_posix()


ARCHIVE_EXCLUDED_DIRS = frozenset({
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
})


def walk_files(root: Path, *, archive: bool = False) -> list[str]:
    paths = []
    excluded = ARCHIVE_EXCLUDED_DIRS if archive else {".git"}
    for directory, children, filenames in os.walk(root, followlinks=False):
        children[:] = [name for name in children
                       if name not in excluded and not (Path(directory) / name).is_symlink()]
        for name in filenames:
            path = Path(directory) / name
            if name != ".git" and not path.is_symlink() and path.is_file():
                paths.append(normalize_path(path))
    return paths


def collect_paths_from_args(paths: list[str]) -> list[str]:
    collected: list[str] = []
    for raw_path in paths:
        relative = normalize_path(raw_path)
        absolute = ROOT / relative
        if absolute.is_dir():
            collected.extend(walk_files(absolute))
        elif absolute.is_file():
            collected.append(relative)
        else:
            print(f"WARN: path does not exist, skipping: {raw_path}", file=sys.stderr)
    return sorted(set(collected))


def collect_all_paths() -> list[str]:
    if not GIT_ROOT:
        return sorted(set(walk_files(ROOT, archive=True)))
    return repository_paths(ROOT)


def readable_path(path: str) -> bool:
    absolute = ROOT / path
    return (not is_excluded(path) and absolute.is_file()
            and not any(item.is_symlink() for item in (absolute, *absolute.parents)))


def declares_header(path: str) -> bool:
    # Invalid UTF-8 after a declaration must be reported, not hide the header.
    return has_declared_header((ROOT / path).read_bytes().decode("utf-8", "replace"))


def parse_header(path: str) -> dict[str, Any]:
    try:
        parsed = parse_header_text((ROOT / path).read_text(encoding="utf-8"))
    except (HeaderError, UnicodeError) as exc:
        raise IndexErrorInfo(str(exc)) from exc
    if not parsed:
        raise IndexErrorInfo("missing metadata header")
    return parsed


def content_hash(path: str) -> str:
    data = (ROOT / path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def provisional_id(path: str) -> str:
    stem = path.rsplit(".", 1)[0]
    cleaned = re.sub(r"[^a-z0-9]+", ".", stem.lower()).strip(".")
    return f"legacy.{cleaned}"


def used_by_paths(entries: Any) -> list[str]:
    if not isinstance(entries, list):
        return []
    paths: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            paths.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
            paths.append(entry["path"])
    return paths


def normalize_versioned(path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    date_fields = ("created_on", "updated_on", "deprecated_on", "superseded_on")
    for field in date_fields:
        required = metadata.get("schema") == "agentic-artifact/v3" and field in {"created_on", "updated_on"}
        if field not in metadata and not required:
            continue
        value = metadata.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise IndexErrorInfo(f"{field} must be a quoted YYYY-MM-DD date")
        try:
            dt.date.fromisoformat(value)
        except ValueError as exc:
            raise IndexErrorInfo(f"{field} must be a valid calendar date") from exc
    artifact = {
        "path": path,
        "metadata_schema": metadata.get("schema"),
        "id": metadata.get("id"),
        "version": metadata.get("version"),
        "status": metadata.get("status"),
        "layer": metadata.get("layer"),
        "domain": metadata.get("domain"),
        "disciplines": metadata.get("disciplines") or [],
        "kind": metadata.get("kind"),
        "purpose": metadata.get("purpose"),
        "portability": metadata.get("portability"),
        "effects": metadata.get("effects"),
        "used_by": metadata.get("used_by") or [],
        "legacy": False,
        "content_hash": content_hash(path),
    }
    for field in ("created_on", "updated_on", "deprecated_on", "superseded_on", "superseded_by"):
        if field in metadata:
            artifact[field] = metadata[field]
    return artifact


def normalize_v1_artifact(path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path,
        "metadata_schema": "agentic-artifact/v1",
        "id": None,
        "provisional_id": provisional_id(path),
        "version": None,
        "status": None,
        "layer": None,
        "owner": metadata.get("owner"),
        "domain": metadata.get("domain"),
        "disciplines": [],
        "kind": metadata.get("kind"),
        "purpose": metadata.get("purpose"),
        "portability": metadata.get("portability"),
        "effects": None,
        "used_by": metadata.get("used_by") or [],
        "used_by_paths": used_by_paths(metadata.get("used_by")),
        "legacy": True,
        "content_hash": content_hash(path),
    }


def normalize_v1_script(path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    effects = metadata.get("effects")
    if isinstance(effects, str):
        effects = [part.strip() for part in effects.split(",") if part.strip()]
    return {
        "path": path,
        "metadata_schema": "agentic-script/v1",
        "id": None,
        "provisional_id": provisional_id(path),
        "version": None,
        "status": None,
        "layer": None,
        "owner": metadata.get("owner"),
        "domain": metadata.get("domain"),
        "disciplines": [],
        "kind": "script",
        "purpose": metadata.get("purpose"),
        "portability": metadata.get("portability"),
        "effects": effects or [],
        "used_by": metadata.get("used_by") or [],
        "used_by_paths": used_by_paths(metadata.get("used_by")),
        "legacy": True,
        "content_hash": content_hash(path),
    }


def normalize_artifact(path: str) -> dict[str, Any]:
    parsed = parse_header(path)
    artifact = parsed.get("agentic-artifact")
    script = parsed.get("agentic-script")
    if isinstance(artifact, dict):
        schema = artifact.get("schema")
        if schema in {"agentic-artifact/v2", "agentic-artifact/v3"}:
            return normalize_versioned(path, artifact)
        if "schema" in artifact and schema != "agentic-artifact/v1":
            raise IndexErrorInfo(f"unsupported metadata schema: {schema}")
        return normalize_v1_artifact(path, artifact)
    if isinstance(script, dict):
        schema = script.get("schema")
        if "schema" in script and schema != "agentic-script/v1":
            raise IndexErrorInfo(f"unsupported metadata schema: {schema}")
        return normalize_v1_script(path, script)
    raise IndexErrorInfo("missing recognized metadata payload")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    paths = collect_all_paths() if args.all else collect_paths_from_args(args.paths or [])
    commit = source_commit()

    artifacts: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    ids: dict[str, str] = {}
    duplicate_ids: list[dict[str, str]] = []

    for path in paths:
        if not readable_path(path):
            continue
        if not requires_header(path) and not declares_header(path):
            continue
        try:
            artifact = normalize_artifact(path)
        except IndexErrorInfo as exc:
            skipped.append({"path": path, "reason": str(exc)})
            continue
        artifact_id = artifact.get("id")
        if isinstance(artifact_id, str) and artifact_id:
            if artifact_id in ids:
                duplicate_ids.append({"id": artifact_id, "first_path": ids[artifact_id], "path": path})
            else:
                ids[artifact_id] = path
        artifacts.append(artifact)

    coverage = None
    missing = []
    if args.check_coverage:
        # Independently rescan the complete declaration scope, so a future
        # collector/filter regression cannot silently shrink index coverage.
        if GIT_ROOT:
            reference_paths = repository_paths(ROOT)
        else:
            reference_paths = []
            for directory, children, filenames in os.walk(ROOT, followlinks=False):
                children[:] = [name for name in children if name not in ARCHIVE_EXCLUDED_DIRS
                               and not (Path(directory) / name).is_symlink()]
                reference_paths.extend((Path(directory) / name).relative_to(ROOT).as_posix()
                                       for name in filenames if name != ".git")
        declared = {path for path in reference_paths
                    if readable_path(path) and declares_header(path)}
        indexed = {artifact["path"] for artifact in artifacts}
        missing = sorted(declared - indexed)
        coverage = {
            "scope": "tracked-and-untracked" if GIT_ROOT else "source-archive",
            "declared_artifacts": len(declared),
            "indexed_declared_artifacts": len(declared & indexed),
            "missing_paths": missing,
        }

    if (args.strict and (skipped or duplicate_ids)) or missing:
        for entry in skipped:
            print(f"ERROR: skipped {entry['path']}: {entry['reason']}", file=sys.stderr)
        for entry in duplicate_ids:
            print(
                f"ERROR: duplicate id {entry['id']}: {entry['first_path']} and {entry['path']}",
                file=sys.stderr,
            )
        for path in missing:
            print(f"ERROR: declared artifact missing from index: {path}", file=sys.stderr)
        return 1

    output = {
        "schema": "agentic-artifact-index/v1",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git_commit": commit,
        "summary": {
            "artifacts": len(artifacts),
            "legacy_artifacts": sum(1 for artifact in artifacts if artifact.get("legacy")),
            "v2_artifacts": sum(1 for artifact in artifacts if artifact.get("metadata_schema") == "agentic-artifact/v2"),
            "v3_artifacts": sum(1 for artifact in artifacts if artifact.get("metadata_schema") == "agentic-artifact/v3"),
            "skipped": len(skipped),
            "duplicate_ids": len(duplicate_ids),
        },
        "artifacts": artifacts,
        "skipped": skipped,
        "duplicate_ids": duplicate_ids,
    }
    if coverage is not None:
        output["coverage"] = coverage
    indent = 2 if args.pretty else None
    print(json.dumps(output, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[2:]))
    except (IndexErrorInfo, HeaderError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
PY
