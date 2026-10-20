#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.check-headers
#   version: 3
#   status: active
#   created_on: "2026-06-24"
#   updated_on: "2026-10-20"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Validate artifact metadata, lifecycle dates, and staged changes across supported header versions.
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
#     - id: harness.checklist.before-commit
#       path: .agentic/00.chat/checklists/before-commit.md

python3 - "${BASH_SOURCE[0]}" "$@" 3<&0 <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[1]))


try:
    import yaml
except ImportError:  # pragma: no cover - environment gate
    print("ERROR: python3 yaml module is required for artifact metadata checks.", file=sys.stderr)
    sys.exit(2)

try:
    from header_discovery import (
        HeaderError, has_declared_header, header_span, is_excluded,
        is_legacy_script_path, is_legacy_markdown_path, is_legacy_yaml_path,
        parse_header_text as shared_parse_header_text, requires_header,
        strip_comment, repository_paths, recover_legacy_baseline,
    )
except ImportError:
    print("ERROR: installed header_discovery.py is required beside metadata capabilities.", file=sys.stderr)
    sys.exit(2)


V1_OWNERS = {"00.chat", "shared", "harness", "aws", "product", "education"}
V1_PORTABILITY = {
    "llm-workbench-required",
    "llm-workbench-validation",
    "llm-workbench-compatibility",
    "source-only",
    "internal",
}
PATH_PREFIXES = (
    "AGENTS.md",
    ".github/workflows/",
    ".agentic/",
    "docs/00.chat/",
    "docs/01.harness/",
    "docs/02.rag-rulebook/",
    "docs/03.product/",
    "docs/harness/",
    "docs/04.deploy/",
    "docs/06.shared/",
    "infra/",
    "scripts/",
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$")
DOMAIN_RE = ID_RE
V2_STATUSES = {"draft", "active", "deprecated", "retired"}
V3_STATUSES = V2_STATUSES | {"superseded"}
DATE_FIELDS = ("created_on", "updated_on", "deprecated_on", "superseded_on")
TODAY = dt.datetime.now(dt.timezone.utc).date()
STAGED = False
INDEX_ENTRIES: dict[str, tuple[str, str]] = {}
CONTENT_CACHE: dict[str, str] = {}
PROPOSED: dict[str, str] = {}


class CheckError(Exception):
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


def load_taxonomy() -> dict[str, Any]:
    path = PurePosixPath(".agentic", "01.harness", "artifact-metadata", "taxonomy.yml").as_posix()
    if not path_exists(path):
        return {
            "layers": [
                {"id": "00.chat"},
                {"id": "01.harness"},
                {"id": "02.rag-rulebook"},
                {"id": "03.product"},
                {"id": "04.deploy"},
                {"id": "05.education"},
                {"id": "06.shared"},
            ],
            "disciplines": [
                "agentic",
                "architecture",
                "backend",
                "frontend",
                "requirements",
                "security",
                "sre",
            ],
            "statuses": ["draft", "active", "deprecated", "retired"],
            "portability_classes": [
                "required",
                "reusable",
                "compatible",
                "source-only",
                "internal",
            ],
            "script_effects": [
                "read-only",
                "writes-files",
                "stages-files",
                "commits",
                "branches",
                "worktrees",
                "network",
                "destructive",
            ],
        }
    return yaml.safe_load(read_text(path)) or {}


LAYERS: set[str] = set()
DISCIPLINES: set[str] = set()
PORTABILITY_CLASSES: set[str] = set()
SCRIPT_EFFECTS: set[str] = set()


def usage() -> str:
    return """Usage:
  check-artifact-metadata-headers.sh --proposed < proposed-files.json
  check-artifact-metadata-headers.sh --staged
  check-artifact-metadata-headers.sh --staged-added
  check-artifact-metadata-headers.sh --paths <path> [path...]
  check-artifact-metadata-headers.sh --all

Checks declared file-level metadata across tracked files of every extension,
plus existing paths that require headers, for v1, v2, and v3 compatibility.
Embedded examples are not declarations; public bootstrap scaffolds are excluded. --staged reads added,
copied, renamed, and modified files from the Git index and checks v3 lifecycle
maintenance against HEAD. It also validates supersession links from unchanged
v3 sources against the full Git index, so target moves, removals, or identity
changes cannot leave dangling references. Existing headerless files remain
allowed on ordinary modifications during migration. --staged-added retains the legacy A/C/R scope.
--proposed reads a JSON object mapping repository-relative paths to full proposed
file text from stdin. It validates that overlay, including replacement links,
without writing files or applying staged-maintenance rules.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--proposed", action="store_true")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--staged-added", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)

    if args.help:
        print(usage(), end="")
        sys.exit(0)

    modes = [args.proposed, args.staged, args.staged_added, args.all, args.paths is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.paths == []:
        print("ERROR: --paths requires at least one path.", file=sys.stderr)
        sys.exit(2)
    return args


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout


def normalize_path(path: Path | str) -> str:
    path_obj = Path(path)
    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return path_obj.as_posix()
    return path_obj.as_posix()


def collect_staged_changes(include_modified: bool) -> dict[str, tuple[str, str]]:
    output = run_git([
        "diff", "--cached", "--name-status", "-z", "--find-renames", "--find-copies",
        "--diff-filter=ACRMT" if include_modified else "--diff-filter=ACR",
    ])
    fields = iter(output.rstrip("\0").split("\0") if output else [])
    changes: dict[str, tuple[str, str]] = {}
    for status in fields:
        source = next(fields)
        path = next(fields) if status.startswith(("R", "C")) else source
        changes[path] = (status[0], source)
    return changes


def load_index_entries() -> None:
    for record in run_git(["ls-files", "--stage", "-z"]).split("\0"):
        if not record:
            continue
        attributes, path = record.split("\t", 1)
        mode, object_id, stage = attributes.split()
        if stage != "0":
            raise CheckError(f"unmerged index entry: {path}")
        INDEX_ENTRIES[path] = (mode, object_id)


def path_exists(path: str) -> bool:
    if path in PROPOSED or any(p.startswith(path.rstrip("/") + "/") for p in PROPOSED):
        return True
    if STAGED:
        return path in INDEX_ENTRIES or any(p.startswith(path.rstrip("/") + "/") for p in INDEX_ENTRIES)
    return (ROOT / path).exists()


def is_regular_file(path: str) -> bool:
    if path in PROPOSED:
        return True
    if STAGED:
        return INDEX_ENTRIES.get(path, ("", ""))[0] in {"100644", "100755"}
    candidate = ROOT / path
    return (candidate.is_file() and candidate.resolve().is_relative_to(ROOT.resolve())
            and not any(item.is_symlink() for item in (candidate, *candidate.parents)))


def read_text(path: str) -> str:
    if path in PROPOSED:
        return PROPOSED[path]
    if path not in CONTENT_CACHE:
        try:
            if STAGED:
                mode, object_id = INDEX_ENTRIES[path]
                if mode not in {"100644", "100755"}:
                    raise CheckError(f"metadata requires a regular file: {path}")
                CONTENT_CACHE[path] = run_git(["cat-file", "blob", object_id])
            else:
                if not is_regular_file(path):
                    raise CheckError(f"metadata requires a regular repository file: {path}")
                CONTENT_CACHE[path] = (ROOT / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError, KeyError, subprocess.CalledProcessError) as exc:
            raise CheckError(f"cannot read metadata file: {path}: {exc}") from exc
    return CONTENT_CACHE[path]


def head_text(path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("utf-8")
    except UnicodeError:
        return None


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
    return repository_paths(ROOT)


is_script_artifact = is_legacy_script_path
is_markdown_artifact = is_legacy_markdown_path
is_yaml_artifact = is_legacy_yaml_path


def parse_header_text(path: str, text: str) -> tuple[dict[str, Any], tuple[int, int] | None]:
    try:
        parsed = shared_parse_header_text(text)
        span = header_span(text)
    except HeaderError as exc:
        raise CheckError(f"{exc}: {path}") from exc
    return parsed, (span.start, span.end) if span else None


def discovery_text(path: str) -> str | None:
    """Skip unrelated binary files, but fail on corrupt declared metadata."""
    if not is_regular_file(path):
        return None
    try:
        if path in PROPOSED:
            raw = PROPOSED[path].encode("utf-8")
        elif STAGED:
            raw = subprocess.run(["git", "cat-file", "blob", INDEX_ENTRIES[path][1]],
                                 check=True, stdout=subprocess.PIPE).stdout
        else:
            raw = (ROOT / path).read_bytes()
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise CheckError(f"cannot read artifact candidate: {path}: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        if requires_header(path) or has_declared_header(raw.decode("utf-8", errors="replace")):
            raise CheckError(f"declared metadata must be UTF-8 text: {path}") from exc
        return None
    if "\0" in text:
        if requires_header(path) or has_declared_header(text):
            raise CheckError(f"declared metadata must not contain NUL bytes: {path}")
        return None
    CONTENT_CACHE[path] = text
    return text


def parse_header(path: str, text: str | None = None) -> dict[str, Any]:
    return parse_header_text(path, read_text(path) if text is None else text)[0]


def without_lifecycle_dates(path: str, text: str) -> str:
    _, span = parse_header_text(path, text)
    if span is None:
        return text
    lines = text.splitlines(keepends=True)
    start, end = span
    kept = []
    for index, line in enumerate(lines):
        key = strip_comment(line).strip().split(":", 1)[0]
        if start < index < end and key in DATE_FIELDS:
            continue
        kept.append(line)
    return "".join(kept)


def require_fields(path: str, metadata: dict[str, Any], fields: list[str], label: str) -> None:
    for field in fields:
        if field not in metadata or metadata[field] in (None, ""):
            raise CheckError(f"missing {field} in {label} metadata header: {path}")


def validate_used_by_path(path: str, ref: str) -> None:
    if not ref or not ref.startswith(PATH_PREFIXES):
        return
    if not path_exists(ref):
        raise CheckError(f"{path} references missing used_by path: {ref}")


def validate_v1_used_by_paths(path: str, used_by: Any) -> None:
    if not isinstance(used_by, list):
        raise CheckError(f"used_by must be a list in metadata header: {path}")
    for entry in used_by:
        if isinstance(entry, str):
            validate_used_by_path(path, entry)
        elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
            validate_used_by_path(path, entry["path"])


def validate_v1_script(path: str, metadata: dict[str, Any]) -> None:
    require_fields(path, metadata, ["owner", "purpose", "domain", "portability", "used_by", "effects"], "script")
    if metadata["owner"] not in V1_OWNERS:
        raise CheckError(f"invalid owner value in script metadata header: {path}")
    if metadata["portability"] not in V1_PORTABILITY:
        raise CheckError(f"invalid portability value in script metadata header: {path}")
    validate_v1_used_by_paths(path, metadata["used_by"])


def validate_v1_artifact(path: str, metadata: dict[str, Any], yaml_artifact: bool) -> None:
    label = "YAML artifact" if yaml_artifact else "artifact"
    require_fields(path, metadata, ["owner", "kind", "purpose", "domain", "portability", "used_by"], label)
    if metadata["owner"] not in V1_OWNERS:
        raise CheckError(f"invalid owner value in {label} metadata header: {path}")
    if metadata["portability"] not in V1_PORTABILITY:
        raise CheckError(f"invalid portability value in {label} metadata header: {path}")
    validate_v1_used_by_paths(path, metadata["used_by"])


def require_type(path: str, field: str, value: Any, expected_type: type, description: str) -> None:
    if not isinstance(value, expected_type):
        raise CheckError(f"{field} must be {description} in versioned metadata header: {path}")


def validate_id(path: str, field: str, value: str) -> None:
    if not ID_RE.match(value):
        raise CheckError(f"invalid {field} value in versioned metadata header: {path}")


def validate_versioned(path: str, metadata: dict[str, Any]) -> None:
    required = [
        "schema",
        "id",
        "version",
        "status",
        "layer",
        "domain",
        "disciplines",
        "kind",
        "purpose",
        "portability",
        "used_by",
    ]
    require_fields(path, metadata, required, "versioned artifact")


    require_type(path, "id", metadata["id"], str, "a string")
    validate_id(path, "id", metadata["id"])

    if type(metadata["version"]) is not int or metadata["version"] < 1:
        raise CheckError(f"version must be an integer greater than zero in versioned metadata header: {path}")

    statuses = V3_STATUSES if metadata["schema"] == "agentic-artifact/v3" else V2_STATUSES
    if not isinstance(metadata["status"], str) or metadata["status"] not in statuses:
        raise CheckError(f"invalid status value in versioned metadata header: {path}")
    if not isinstance(metadata["layer"], str) or metadata["layer"] not in LAYERS:
        raise CheckError(f"invalid layer value in versioned metadata header: {path}")

    require_type(path, "domain", metadata["domain"], str, "a string")
    if not DOMAIN_RE.match(metadata["domain"]):
        raise CheckError(f"invalid domain value in versioned metadata header: {path}")

    disciplines = metadata["disciplines"]
    if not isinstance(disciplines, list) or not disciplines:
        raise CheckError(f"disciplines must be a non-empty list in versioned metadata header: {path}")
    for discipline in disciplines:
        if not isinstance(discipline, str) or discipline not in DISCIPLINES:
            raise CheckError(f"invalid discipline value in versioned metadata header: {path}: {discipline}")

    require_type(path, "kind", metadata["kind"], str, "a string")
    require_type(path, "purpose", metadata["purpose"], str, "a string")
    if not metadata["kind"].strip() or not metadata["purpose"].strip():
        raise CheckError(f"kind and purpose must be non-empty in versioned metadata header: {path}")

    portability = metadata["portability"]
    if not isinstance(portability, dict):
        raise CheckError(f"portability must be an object in versioned metadata header: {path}")
    if not isinstance(portability.get("class"), str) or portability["class"] not in PORTABILITY_CLASSES:
        raise CheckError(f"invalid portability.class value in versioned metadata header: {path}")
    targets = portability.get("targets")
    if not isinstance(targets, list):
        raise CheckError(f"portability.targets must be a list in versioned metadata header: {path}")
    for target in targets:
        if not isinstance(target, str) or not target:
            raise CheckError(f"portability.targets entries must be strings in versioned metadata header: {path}")

    used_by = metadata["used_by"]
    if not isinstance(used_by, list) or not used_by:
        raise CheckError(f"used_by must be a non-empty list in versioned metadata header: {path}")
    for entry in used_by:
        if not isinstance(entry, dict):
            raise CheckError(f"used_by entries must be objects in versioned metadata header: {path}")
        ref_id = entry.get("id")
        if not isinstance(ref_id, str) or not ref_id:
            raise CheckError(f"used_by.id is required in versioned metadata header: {path}")
        validate_id(path, "used_by.id", ref_id)
        ref_path = entry.get("path")
        if ref_path is not None:
            if not isinstance(ref_path, str):
                raise CheckError(f"used_by.path must be a string in versioned metadata header: {path}")
            validate_used_by_path(path, ref_path)

    effects = metadata.get("effects")
    if metadata["kind"] == "script" or is_script_artifact(path):
        if metadata["kind"] != "script":
            raise CheckError(f"script file must use kind: script in versioned metadata header: {path}")
        if not isinstance(effects, list) or not effects:
            raise CheckError(f"effects must be a non-empty list for versioned script metadata header: {path}")
    if effects is not None:
        if not isinstance(effects, list):
            raise CheckError(f"effects must be a list in versioned metadata header: {path}")
        for effect in effects:
            if not isinstance(effect, str) or effect not in SCRIPT_EFFECTS:
                raise CheckError(f"invalid effects value in versioned metadata header: {path}: {effect}")


def validate_lifecycle(path: str, metadata: dict[str, Any]) -> None:
    require_fields(path, metadata, ["created_on", "updated_on"], "v3 artifact")
    dates: dict[str, dt.date] = {}
    for field in DATE_FIELDS:
        if field not in metadata:
            continue
        value = metadata[field]
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise CheckError(f"{field} must be a quoted YYYY-MM-DD string: {path}")
        try:
            dates[field] = dt.date.fromisoformat(value)
        except ValueError as exc:
            raise CheckError(f"{field} must be a real calendar date: {path}") from exc
        if dates[field] > TODAY:
            raise CheckError(f"{field} cannot be in the future (UTC): {path}")
    if dates["created_on"] > dates["updated_on"]:
        raise CheckError(f"created_on must not follow updated_on: {path}")
    for field in ("deprecated_on", "superseded_on"):
        if field in dates and not dates["created_on"] <= dates[field] <= dates["updated_on"]:
            raise CheckError(f"{field} must be between created_on and updated_on: {path}")
    status = metadata["status"]
    if status == "deprecated" and "deprecated_on" not in dates:
        raise CheckError(f"deprecated status requires deprecated_on: {path}")
    if "deprecated_on" in dates and status not in {"deprecated", "superseded", "retired"}:
        raise CheckError(f"deprecated_on is only allowed for deprecated, superseded, or retired artifacts: {path}")
    has_date, has_refs = "superseded_on" in metadata, "superseded_by" in metadata
    if has_date != has_refs:
        raise CheckError(f"superseded_on and superseded_by must be provided together: {path}")
    if status == "superseded" and not has_date:
        raise CheckError(f"superseded status requires superseded_on and superseded_by: {path}")
    if has_date and status not in {"superseded", "retired"}:
        raise CheckError(f"supersession metadata is only allowed for superseded or retired artifacts: {path}")
    if "deprecated_on" in dates and "superseded_on" in dates and dates["deprecated_on"] > dates["superseded_on"]:
        raise CheckError(f"deprecated_on must not follow superseded_on: {path}")
    if has_refs:
        validate_replacement_graph(path, metadata, [])


def validate_replacement_graph(path: str, metadata: dict[str, Any], ancestors: list[str]) -> None:
    if path in ancestors:
        raise CheckError("supersession cycle: " + " -> ".join([*ancestors, path]))
    if "superseded_by" not in metadata:
        return
    refs = metadata["superseded_by"]
    if not isinstance(refs, list) or not refs:
        raise CheckError(f"superseded_by must be a non-empty list: {path}")
    seen: set[str] = set()
    for entry in refs:
        if not isinstance(entry, dict):
            raise CheckError(f"superseded_by entries must be objects with id and path: {path}")
        ref_id, ref_path = entry.get("id"), entry.get("path")
        if not isinstance(ref_id, str) or not ref_id:
            raise CheckError(f"superseded_by.id must be a non-empty string: {path}")
        validate_id(path, "superseded_by.id", ref_id)
        if not isinstance(ref_path, str) or not ref_path:
            raise CheckError(f"superseded_by.path must be a non-empty repository-relative path: {path}")
        parts = PurePosixPath(ref_path)
        if parts.is_absolute() or ".." in parts.parts or "\\" in ref_path or parts.as_posix() != ref_path:
            raise CheckError(f"superseded_by.path must stay inside the repository: {path}: {ref_path}")
        if not STAGED and not (ROOT / ref_path).resolve().is_relative_to(ROOT.resolve()):
            raise CheckError(f"superseded_by.path must stay inside the repository: {path}: {ref_path}")
        if ref_path == path or ref_id == metadata.get("id"):
            raise CheckError(f"superseded_by must not reference itself: {path}")
        if ref_path in seen:
            raise CheckError(f"duplicate superseded_by path: {path}: {ref_path}")
        seen.add(ref_path)
        if not is_regular_file(ref_path):
            raise CheckError(f"superseded_by references missing or non-regular file: {path}: {ref_path}")
        target = parse_header(ref_path).get("agentic-artifact")
        if not isinstance(target, dict) or target.get("schema") not in ("agentic-artifact/v2", "agentic-artifact/v3"):
            raise CheckError(f"superseded_by target needs a supported stable artifact ID: {path}: {ref_path}")
        if target.get("id") != ref_id:
            raise CheckError(f"superseded_by id/path mismatch: {path}: {ref_path}")
        validate_replacement_graph(ref_path, target, [*ancestors, path])


def validate_path(path: str, parsed: dict[str, Any]) -> None:
    artifact = parsed.get("agentic-artifact")
    script = parsed.get("agentic-script")
    if isinstance(artifact, dict) and "schema" in artifact:
        if artifact["schema"] not in ("agentic-artifact/v1", "agentic-artifact/v2", "agentic-artifact/v3"):
            raise CheckError(f"unsupported artifact metadata schema: {path}: {artifact['schema']}")
        if artifact["schema"] in ("agentic-artifact/v2", "agentic-artifact/v3"):
            validate_versioned(path, artifact)
            if artifact["schema"] == "agentic-artifact/v3":
                validate_lifecycle(path, artifact)
            return
    if isinstance(script, dict) and "schema" in script and script["schema"] != "agentic-script/v1":
        raise CheckError(f"unsupported script metadata schema: {path}: {script['schema']}")
    if is_script_artifact(path) or isinstance(script, dict):
        if isinstance(script, dict):
            validate_v1_script(path, script)
            return
        raise CheckError(f"missing agentic-script or versioned agentic-artifact metadata header: {path}")
    if isinstance(artifact, dict):
        validate_v1_artifact(path, artifact, is_yaml_artifact(path))
        return
    raise CheckError(f"missing agentic-artifact metadata header: {path}")


def validate_staged_maintenance(path: str, change: tuple[str, str], parsed: dict[str, Any]) -> bool:
    status, source = change
    previous_text = head_text(source if status == "R" else path)
    repairing_legacy = False
    try:
        previous = parse_header(path, previous_text) if previous_text is not None else {}
    except CheckError:
        previous = recover_legacy_baseline(previous_text or "")
        if not previous:
            raise
        repairing_legacy = True
    old = previous.get("agentic-artifact") or {}
    if not isinstance(old, dict):
        old = {}
    current = parsed.get("agentic-artifact") or {}
    old_v3 = isinstance(old, dict) and old.get("schema") == "agentic-artifact/v3"
    new_v3 = isinstance(current, dict) and current.get("schema") == "agentic-artifact/v3"
    if old_v3 and not new_v3:
        raise CheckError(f"v3 metadata must not be downgraded or removed: {path}")
    if not parsed and status == "M" and not previous and previous_text is not None:
        return False  # Grandfather only files which already had no header in HEAD.
    if new_v3:
        if old_v3 and current.get("created_on") != old.get("created_on"):
            raise CheckError(f"created_on is immutable after v3 adoption: {path}")
        if status == "R" and old.get("id") and current.get("id") != old["id"]:
            raise CheckError(f"artifact id must be preserved across a rename: {path}")
        if old_v3:
            for field in ("deprecated_on", "superseded_on"):
                if field in old and field not in current and current.get("status") not in ("active", "draft"):
                    raise CheckError(f"{field} must be retained unless the artifact is reactivated: {path}")
                if field in old and field in current and old[field] != current[field]:
                    raise CheckError(f"{field} is immutable while retained: {path}")
        text = read_text(path)
        if repairing_legacy or previous_text is None or without_lifecycle_dates(path, text) != without_lifecycle_dates(path, previous_text):
            if current.get("updated_on") != TODAY.isoformat():
                raise CheckError(f"updated_on must be today's UTC date for changed content: {path}")
        for field, event_status in (("deprecated_on", "deprecated"), ("superseded_on", "superseded")):
            new_transition = current.get("status") == event_status and old.get("status") != event_status
            new_retained_event = current.get("status") == "retired" and field in current and field not in old and old_v3
            if (new_transition or new_retained_event) and current.get(field) != TODAY.isoformat():
                raise CheckError(f"{field} must be today's UTC date for a new lifecycle transition: {path}")
    return True


def load_proposed() -> None:
    try:
        with os.fdopen(3, "r", encoding="utf-8") as handle:
            proposed = json.load(handle)
    except (OSError, UnicodeError, ValueError) as exc:
        raise CheckError(f"--proposed requires a JSON path-to-text object on stdin: {exc}") from exc
    if not isinstance(proposed, dict) or not proposed:
        raise CheckError("--proposed requires a non-empty JSON path-to-text object")
    for path, text in proposed.items():
        parts = PurePosixPath(path)
        if not path or parts.is_absolute() or ".." in parts.parts or "\\" in path or parts.as_posix() != path:
            raise CheckError(f"unsafe proposed repository path: {path}")
        if not (ROOT / path).resolve().is_relative_to(ROOT.resolve()):
            raise CheckError(f"proposed path resolves outside the repository: {path}")
        if not isinstance(text, str):
            raise CheckError(f"proposed file text must be a string: {path}")
        if is_excluded(path):
            raise CheckError(f"proposed path is an excluded bootstrap scaffold: {path}")
        if not requires_header(path) and not has_declared_header(text):
            raise CheckError(f"proposed path is outside metadata coverage: {path}")
        PROPOSED[path] = text


def main(argv: list[str]) -> int:
    global STAGED, LAYERS, DISCIPLINES, PORTABILITY_CLASSES, SCRIPT_EFFECTS
    args = parse_args(argv)
    STAGED = args.staged or args.staged_added
    try:
        changes = collect_staged_changes(args.staged) if STAGED else {}
        if STAGED:
            load_index_entries()
        if args.proposed:
            load_proposed()
        taxonomy = load_taxonomy()
        LAYERS = {entry["id"] for entry in taxonomy.get("layers", [])}
        DISCIPLINES = set(taxonomy.get("disciplines", []))
        PORTABILITY_CLASSES = set(taxonomy.get("portability_classes", []))
        SCRIPT_EFFECTS = set(taxonomy.get("script_effects", []))
    except CheckError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.proposed:
        paths = sorted(PROPOSED)
    elif STAGED:
        paths = sorted(changes)
    elif args.all:
        paths = collect_all_paths()
    else:
        paths = collect_paths_from_args(args.paths or [])
    failures = checked = grandfathered = 0
    for path in paths:
        if not path or not path_exists(path):
            continue
        try:
            previous = None
            previous_path = path
            if args.staged:
                change, source = changes[path]
                previous_path = source if change == "R" else path
                previous = head_text(previous_path)
            previously_declared = not is_excluded(previous_path) and has_declared_header(previous or "")
            if is_excluded(path) and not previously_declared:
                continue
            text = discovery_text(path)
            if text is None:
                if requires_header(path) or previously_declared:
                    raise CheckError(f"metadata requires a regular text repository file: {path}")
                continue
            if not (requires_header(path) or has_declared_header(text) or previously_declared):
                continue
            parsed = parse_header(path, text)
            if args.staged and not validate_staged_maintenance(path, changes[path], parsed):
                grandfathered += 1
                continue
            checked += 1
            validate_path(path, parsed)
        except CheckError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failures += 1
    if args.staged:
        # A target can change without its inbound sources appearing in the diff.
        # Validate those sources against the same staged snapshot, without
        # requiring unchanged files to refresh their lifecycle dates.
        for path in sorted(INDEX_ENTRIES):
            if path in changes or is_excluded(path) or not is_regular_file(path):
                continue
            try:
                text = discovery_text(path)
                if text is None or not has_declared_header(text):
                    continue
                metadata = parse_header(path, text).get("agentic-artifact")
                if isinstance(metadata, dict) and metadata.get("schema") == "agentic-artifact/v3" and "superseded_by" in metadata:
                    validate_replacement_graph(path, metadata, [])
            except CheckError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                failures += 1
    if failures:
        print(f"Artifact metadata header check failed: {failures} file(s).", file=sys.stderr)
        return 1
    print(f"Artifact metadata headers passed for {checked} file(s); {grandfathered} existing headerless modification(s) grandfathered.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[2:]))
PY
