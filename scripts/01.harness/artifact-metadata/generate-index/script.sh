#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.generate-index
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Generate a machine-readable artifact metadata index from v1 and v2 headers.
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

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment gate
    print("ERROR: python3 yaml module is required for artifact metadata indexing.", file=sys.stderr)
    sys.exit(2)


class IndexErrorInfo(Exception):
    pass


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


ROOT = repo_root()


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout.strip()


def usage() -> str:
    return """Usage:
  generate-index.sh --paths <path> [path...] [--pretty] [--strict]
  generate-index.sh --all [--pretty] [--strict]

Emits an agentic artifact metadata index as JSON to stdout. By default, files
without parseable metadata are skipped and counted in the summary. Use --strict
to fail when a relevant file cannot be indexed.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--strict", action="store_true")
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
    return args


def normalize_path(path: Path | str) -> str:
    path_obj = Path(path)
    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return path_obj.as_posix()
    return path_obj.as_posix()


def collect_paths_from_args(paths: list[str]) -> list[str]:
    collected: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        absolute = path if path.is_absolute() else ROOT / path
        if absolute.is_dir():
            collected.extend(normalize_path(child) for child in absolute.rglob("*") if child.is_file())
        elif absolute.is_file():
            collected.append(normalize_path(absolute))
        else:
            print(f"WARN: path does not exist, skipping: {raw_path}", file=sys.stderr)
    return sorted(set(collected))


def collect_all_paths() -> list[str]:
    roots = [
        ROOT / "scripts",
        ROOT / ".agentic",
        ROOT / "docs/00.chat",
        ROOT / "docs/02.rag-rulebook",
        ROOT / "docs/harness",
    ]
    collected: list[str] = []
    for root in roots:
        if root.is_dir():
            collected.extend(normalize_path(path) for path in root.rglob("*") if path.is_file())
    return sorted(set(collected))


def is_script_artifact(path: str) -> bool:
    return path.startswith("scripts/") and path.endswith((".sh", ".js"))


def is_markdown_artifact(path: str) -> bool:
    return path.endswith(".md") and (
        path.startswith(".agentic/")
        or path.startswith("docs/00.chat/")
        or path.startswith("docs/02.rag-rulebook/")
        or path.startswith("docs/aws/")
        or path.startswith("docs/education/")
        or path.startswith("docs/harness/")
        or path.startswith("scripts/")
    )


def is_yaml_artifact(path: str) -> bool:
    return path.endswith((".yml", ".yaml")) and (
        path.startswith(".agentic/")
        or path.startswith("docs/02.rag-rulebook/")
        or path.startswith("docs/harness/")
    )


def is_relevant_path(path: str) -> bool:
    return is_script_artifact(path) or is_markdown_artifact(path) or is_yaml_artifact(path)


def strip_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("# "):
        return stripped[2:]
    if stripped.startswith("#"):
        return stripped[1:]
    if stripped.startswith("// "):
        return stripped[3:]
    if stripped.startswith("//"):
        return stripped[2:]
    return line


def parse_header(path: str) -> dict[str, Any]:
    full_path = ROOT / path
    lines = full_path.read_text(encoding="utf-8").splitlines()[:120]

    for index, line in enumerate(lines):
        if "agentic-artifact:" not in line and "agentic-script:" not in line:
            continue
        if line.lstrip().startswith("<!--"):
            marker = line.replace("<!--", "", 1).strip()
            body_lines = []
            for following in lines[index + 1 :]:
                if "-->" in following:
                    before_end = following.split("-->", 1)[0]
                    if before_end.strip():
                        body_lines.append(before_end)
                    break
                body_lines.append(following)
            header_lines = [marker]
            header_lines.extend(f"  {body_line}" if body_line.strip() else body_line for body_line in body_lines)
        else:
            header_lines = [strip_comment(line)]
            for following in lines[index + 1 :]:
                stripped = following.lstrip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    header_lines.append(strip_comment(following))
                    continue
                if not following.strip():
                    break
                break
        try:
            parsed = yaml.safe_load("\n".join(header_lines)) or {}
        except yaml.YAMLError as exc:
            raise IndexErrorInfo(f"invalid metadata YAML: {exc}") from exc
        if not isinstance(parsed, dict):
            raise IndexErrorInfo("invalid metadata header shape")
        return parsed
    raise IndexErrorInfo("missing metadata header")


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


def normalize_v2(path: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
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
        if artifact.get("schema") == "agentic-artifact/v2":
            return normalize_v2(path, artifact)
        return normalize_v1_artifact(path, artifact)
    if isinstance(script, dict):
        return normalize_v1_script(path, script)
    raise IndexErrorInfo("missing recognized metadata payload")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    paths = collect_all_paths() if args.all else collect_paths_from_args(args.paths or [])

    artifacts: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    ids: dict[str, str] = {}
    duplicate_ids: list[dict[str, str]] = []

    for path in paths:
        if not is_relevant_path(path) or not (ROOT / path).is_file():
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

    if args.strict and (skipped or duplicate_ids):
        for entry in skipped:
            print(f"ERROR: skipped {entry['path']}: {entry['reason']}", file=sys.stderr)
        for entry in duplicate_ids:
            print(
                f"ERROR: duplicate id {entry['id']}: {entry['first_path']} and {entry['path']}",
                file=sys.stderr,
            )
        return 1

    output = {
        "schema": "agentic-artifact-index/v1",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "git_commit": run_git(["rev-parse", "HEAD"]),
        "summary": {
            "artifacts": len(artifacts),
            "legacy_artifacts": sum(1 for artifact in artifacts if artifact.get("legacy")),
            "v2_artifacts": sum(1 for artifact in artifacts if artifact.get("metadata_schema") == "agentic-artifact/v2"),
            "skipped": len(skipped),
            "duplicate_ids": len(duplicate_ids),
        },
        "artifacts": artifacts,
        "skipped": skipped,
        "duplicate_ids": duplicate_ids,
    }
    indent = 2 if args.pretty else None
    print(json.dumps(output, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY
