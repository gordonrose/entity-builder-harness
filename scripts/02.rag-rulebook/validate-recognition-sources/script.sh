#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-recognition-sources
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate governed RAG/rulebook recognition-source YAML files without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.recognition-source
#       path: .agentic/02.rag-rulebook/schemas/recognition-source.schema.yml
#     - id: rag-rulebook.standard.recognition-source-system
#       path: .agentic/02.rag-rulebook/standards/recognition-source-system.md
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.validate-recognition-sources.readme
#       path: scripts/02.rag-rulebook/validate-recognition-sources/README.md
#     - id: rag-rulebook.script.validate-recognition-sources.smoke-test
#       path: scripts/02.rag-rulebook/validate-recognition-sources/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for recognition-source validation.", file=sys.stderr)
    sys.exit(2)


SOURCE_SCHEMA = "rag-rulebook/recognition-source/v1"
DEFAULT_ROOT = ".agentic/02.rag-rulebook/recognition-sources"
LOWER_DOT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
OWNER_LAYER = re.compile(r"^[0-9]{2}\.[a-z0-9-]+$")
ALLOWED_STATUS = {"draft", "active", "superseded", "retired"}
ALLOWED_SOURCE_KINDS = {
    "artifact-id",
    "file-path",
    "schema-name",
    "corpus-id",
    "layer-name",
    "mode-name",
    "workflow-name",
    "rule-id",
    "rule-pack-id",
    "action-verb",
    "risk-word",
    "domain-noun",
    "alias",
    "intent-form",
    "stop-condition",
    "check-name",
}
ALLOWED_GENERATION_MODES = {"generated", "curated"}
ALLOWED_MATCH_TYPES = {"exact", "normalized", "alias", "phrase"}
REQUIRED_TOP_LEVEL = [
    "schema",
    "source_id",
    "version",
    "status",
    "source_kinds",
    "generation_mode",
    "owner_layer",
    "purpose",
    "match_priority",
    "used_by_dimensions",
    "terms",
    "validation_rules",
    "refresh_policy",
]
REQUIRED_TERM_FIELDS = ["term", "category", "match_type"]


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
  validate-recognition-sources/script.sh --current [--json]
  validate-recognition-sources/script.sh --source <path> [--source <path> ...] [--json]

Validates rag-rulebook/recognition-source/v1 YAML files. The command is
read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.source):
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def path_exists(path: str) -> bool:
    return repo_path(path).exists()


def list_files(args: argparse.Namespace, errors: list[str], warnings: list[str]) -> list[Path]:
    roots = [repo_path(DEFAULT_ROOT)] if args.current else [repo_path(path) for path in args.source]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix in {".yml", ".yaml"}:
                files.append(root)
            else:
                errors.append(f"source path is not a YAML file: {rel(root)}")
            continue
        if root.is_dir():
            files.extend(sorted(root.rglob("*.yml")))
            files.extend(sorted(root.rglob("*.yaml")))
            continue
        if args.current and root == repo_path(DEFAULT_ROOT):
            warnings.append(f"recognition source directory is absent: {DEFAULT_ROOT}")
        else:
            errors.append(f"source path does not exist: {rel(root)}")

    if args.current and repo_path(DEFAULT_ROOT).is_dir() and not files:
        errors.append(f"recognition source directory contains no YAML files: {DEFAULT_ROOT}")
    return sorted(set(files))


def load_yaml(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{rel(path)} failed to parse as YAML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{rel(path)} must contain a YAML object")
        return None
    return data


def as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def require_string(owner: str, data: dict[str, Any], field: str, errors: list[str]) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{owner}.{field} must be a non-empty string")
        return ""
    return value.strip()


def validate_source(path: Path, data: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    owner = rel(path)
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"{owner} missing required field: {field}")

    source_id = require_string(owner, data, "source_id", errors)
    if source_id and not LOWER_DOT_ID.match(source_id):
        errors.append(f"{owner}.source_id must be a lower dot/dash/underscore id: {source_id}")

    if data.get("schema") != SOURCE_SCHEMA:
        errors.append(f"{owner}.schema must be {SOURCE_SCHEMA}")

    version = data.get("version")
    if not isinstance(version, int) or version < 1:
        errors.append(f"{owner}.version must be an integer >= 1")

    status = data.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"{owner}.status must be one of: {', '.join(sorted(ALLOWED_STATUS))}")

    generation_mode = data.get("generation_mode")
    if generation_mode not in ALLOWED_GENERATION_MODES:
        errors.append(f"{owner}.generation_mode must be generated or curated")

    owner_layer = require_string(owner, data, "owner_layer", errors)
    if owner_layer and not OWNER_LAYER.match(owner_layer):
        errors.append(f"{owner}.owner_layer must look like 02.rag-rulebook")

    require_string(owner, data, "purpose", errors)

    match_priority = data.get("match_priority")
    if not isinstance(match_priority, int) or match_priority < 1:
        errors.append(f"{owner}.match_priority must be an integer >= 1")

    raw_source_kinds = data.get("source_kinds")
    source_kinds = as_string_list(raw_source_kinds)
    if not isinstance(raw_source_kinds, list) or not source_kinds or len(source_kinds) != len(raw_source_kinds):
        errors.append(f"{owner}.source_kinds must be a non-empty string array")
    for source_kind in source_kinds:
        if source_kind not in ALLOWED_SOURCE_KINDS:
            errors.append(f"{owner}.source_kinds contains invalid source kind: {source_kind}")
    if len(source_kinds) != len(set(source_kinds)):
        errors.append(f"{owner}.source_kinds must not contain duplicates")

    raw_used_by = data.get("used_by_dimensions")
    used_by_dimensions = as_string_list(raw_used_by)
    if not isinstance(raw_used_by, list) or not used_by_dimensions or len(used_by_dimensions) != len(raw_used_by):
        errors.append(f"{owner}.used_by_dimensions must be a non-empty string array")

    raw_rules = data.get("validation_rules")
    validation_rules = as_string_list(raw_rules)
    if not isinstance(raw_rules, list) or not validation_rules or len(validation_rules) != len(raw_rules):
        errors.append(f"{owner}.validation_rules must be a non-empty string array")

    refresh_policy = data.get("refresh_policy")
    if not isinstance(refresh_policy, dict):
        errors.append(f"{owner}.refresh_policy must be an object")
        refresh_policy = {}
    else:
        require_string(f"{owner}.refresh_policy", refresh_policy, "trigger", errors)
        require_string(f"{owner}.refresh_policy", refresh_policy, "owner", errors)

    if generation_mode == "generated":
        raw_source_artifacts = data.get("source_artifacts")
        source_artifacts = as_string_list(raw_source_artifacts)
        if not isinstance(raw_source_artifacts, list) or not source_artifacts or len(source_artifacts) != len(raw_source_artifacts):
            errors.append(f"{owner}.source_artifacts must be a non-empty string array for generated sources")
        for artifact in source_artifacts:
            if not path_exists(artifact):
                errors.append(f"{owner}.source_artifacts path does not exist: {artifact}")
        generation_command = require_string(owner, data, "generation_command", errors)
        command_path = generation_command.split()[0] if generation_command else ""
        if command_path.startswith("scripts/") and not path_exists(command_path):
            errors.append(f"{owner}.generation_command script does not exist: {command_path}")

    if generation_mode == "curated":
        review_required_when = as_string_list(refresh_policy.get("review_required_when"))
        if not review_required_when:
            errors.append(f"{owner}.refresh_policy.review_required_when must list review triggers for curated sources")

    terms = data.get("terms")
    if not isinstance(terms, list) or not terms:
        errors.append(f"{owner}.terms must be a non-empty array")
        terms = []

    term_keys: set[str] = set()
    alias_keys: set[str] = set()
    categories: set[str] = set()
    for index, term_obj in enumerate(terms, start=1):
        term_owner = f"{owner}.terms[{index}]"
        if not isinstance(term_obj, dict):
            errors.append(f"{term_owner} must be an object")
            continue
        for field in REQUIRED_TERM_FIELDS:
            if field not in term_obj:
                errors.append(f"{term_owner} missing required field: {field}")

        term = require_string(term_owner, term_obj, "term", errors)
        category = require_string(term_owner, term_obj, "category", errors)
        match_type = term_obj.get("match_type")
        if match_type not in ALLOWED_MATCH_TYPES:
            errors.append(f"{term_owner}.match_type must be one of: {', '.join(sorted(ALLOWED_MATCH_TYPES))}")

        if category:
            categories.add(category)
        if term:
            term_key = term.lower()
            if term_key in term_keys:
                errors.append(f"{owner} duplicate term: {term}")
            term_keys.add(term_key)

        aliases = term_obj.get("aliases", [])
        if aliases is None:
            aliases = []
        if not isinstance(aliases, list) or any(not isinstance(alias, str) or not alias.strip() for alias in aliases):
            errors.append(f"{term_owner}.aliases must be a string array when present")
            aliases = []
        for alias in aliases:
            alias_key = alias.strip().lower()
            if term and alias_key == term.lower():
                errors.append(f"{term_owner}.aliases must not repeat the canonical term: {alias}")
            if alias_key in alias_keys:
                errors.append(f"{owner} duplicate alias: {alias}")
            if alias_key in term_keys:
                errors.append(f"{owner} alias also appears as a term: {alias}")
            alias_keys.add(alias_key)

        confidence_weight = term_obj.get("confidence_weight")
        if confidence_weight is not None:
            if not isinstance(confidence_weight, (int, float)) or not 0 <= float(confidence_weight) <= 1:
                errors.append(f"{term_owner}.confidence_weight must be between 0 and 1")

        if generation_mode == "generated":
            evidence_path = require_string(term_owner, term_obj, "evidence_path", errors)
            if evidence_path and not path_exists(evidence_path):
                errors.append(f"{term_owner}.evidence_path does not exist: {evidence_path}")

    if generation_mode == "generated" and not categories:
        warnings.append(f"{owner} has no term categories to report")

    return {
        "path": rel(path),
        "source_id": source_id,
        "generation_mode": generation_mode,
        "source_kinds": source_kinds,
        "terms": len(terms),
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    files = list_files(args, errors, warnings)
    summaries: list[dict[str, Any]] = []
    seen_source_ids: dict[str, str] = {}

    for path in files:
        data = load_yaml(path, errors)
        if data is None:
            continue
        summary = validate_source(path, data, errors, warnings)
        source_id = summary.get("source_id")
        if source_id:
            if source_id in seen_source_ids:
                errors.append(
                    f"duplicate source_id {source_id}: {seen_source_ids[source_id]} and {summary['path']}"
                )
            seen_source_ids[source_id] = summary["path"]
        summaries.append(summary)

    report = {
        "ok": not errors,
        "schema": SOURCE_SCHEMA,
        "root": str(ROOT),
        "counts": {
            "files": len(files),
            "sources": len(summaries),
            "terms": sum(int(summary.get("terms", 0)) for summary in summaries),
            "generated_sources": sum(1 for summary in summaries if summary.get("generation_mode") == "generated"),
            "curated_sources": sum(1 for summary in summaries if summary.get("generation_mode") == "curated"),
        },
        "sources": summaries,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    else:
        print(
            "Recognition sources valid: "
            f"{len(summaries)} source(s), "
            f"{report['counts']['terms']} term(s)."
        )
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
