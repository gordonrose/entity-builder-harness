#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-retirement-records
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate governed RAG/rulebook retirement records without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.retirement-record
#       path: .agentic/02.rag-rulebook/schemas/retirement-record.schema.yml
#     - id: rag-rulebook.retirements.readme
#       path: .agentic/02.rag-rulebook/retirements/README.md
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.validate-retirement-records.readme
#       path: scripts/02.rag-rulebook/validate-retirement-records/README.md
#     - id: rag-rulebook.script.validate-retirement-records.smoke-test
#       path: scripts/02.rag-rulebook/validate-retirement-records/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for retirement-record validation.", file=sys.stderr)
    sys.exit(2)


RECORD_SCHEMA = "rag-rulebook/retirement-record/v1"
REPORT_SCHEMA = "rag-rulebook/retirement-record-validation-report/v1"
DEFAULT_ROOT = ".agentic/02.rag-rulebook/retirements"
LOWER_DOT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
OWNER_LAYER = re.compile(r"^[0-9]{2}\.[a-z0-9-]+$")
CORPUS_ID = re.compile(r"^corpus\.[0-9]{2}\.[a-z0-9-]+(?:\.[a-z0-9-]+)*$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
ALLOWED_STATUS = {"proposed", "accepted", "superseded"}
ALLOWED_REVIEW_DECISIONS = {"pending", "accept", "reject", "supersede"}
STATUS_TO_DECISION = {
    "proposed": "pending",
    "accepted": "accept",
    "superseded": "supersede",
}
ALLOWED_ARTIFACT_KINDS = {
    "source-material",
    "rule",
    "rule-pack",
    "derivation-report",
    "corpus-gap",
    "recognition-source",
    "recognition-candidate",
    "evaluation",
    "index",
    "chunk",
    "runtime-cache",
    "workflow",
    "script",
    "other",
}
ALLOWED_PATH_STATES = {"removed", "renamed", "superseded", "retained-retired"}
ACTIVE_REFERENCE_ROOTS = [
    ".agentic/02.rag-rulebook",
    ".agentic/aws",
    "docs/02.rag-rulebook",
    "docs/04.deploy",
    "scripts/02.rag-rulebook",
]
EXCLUDED_REFERENCE_ROOTS = [
    ".agentic/02.rag-rulebook/retirements",
]
REQUIRED_TOP_LEVEL = [
    "schema",
    "retirement_id",
    "status",
    "owner_layer",
    "corpus_id",
    "retired_artifacts",
    "reason",
    "reference_checks",
    "validation",
    "review",
]


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
  validate-retirement-records/script.sh --current [--json]
  validate-retirement-records/script.sh --record <path> [--record <path> ...] [--json]

Validates rag-rulebook/retirement-record/v1 YAML files. The command is
read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--record", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.record):
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


def path_is_under(path: Path, root: str) -> bool:
    try:
        path.resolve().relative_to(repo_path(root).resolve())
        return True
    except ValueError:
        return False


def is_excluded_reference_path(path: Path) -> bool:
    return any(path_is_under(path, root) for root in EXCLUDED_REFERENCE_ROOTS)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_files(args: argparse.Namespace, errors: list[str], warnings: list[str]) -> list[Path]:
    roots = [repo_path(DEFAULT_ROOT)] if args.current else [repo_path(path) for path in args.record]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix.lower() in {".yml", ".yaml"}:
                files.append(root)
            else:
                errors.append(f"retirement record path is not a YAML file: {rel(root)}")
            continue
        if root.is_dir():
            files.extend(sorted(root.rglob("*.yml")))
            files.extend(sorted(root.rglob("*.yaml")))
            continue
        if args.current and root == repo_path(DEFAULT_ROOT):
            warnings.append(f"retirement record directory is absent: {DEFAULT_ROOT}")
        else:
            errors.append(f"retirement record path does not exist: {rel(root)}")

    if args.current and repo_path(DEFAULT_ROOT).is_dir() and not files:
        warnings.append(f"retirement record directory contains no YAML files: {DEFAULT_ROOT}")
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


def validate_string_array(owner: str, value: Any, errors: list[str], *, required: bool = False) -> list[str]:
    items = as_string_list(value)
    if required and not items:
        errors.append(f"{owner} must be a non-empty string array")
    elif value is not None and (not isinstance(value, list) or len(items) != len(value)):
        errors.append(f"{owner} must be a string array when present")
    return items


def require_string(owner: str, data: dict[str, Any], field: str, errors: list[str]) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{owner}.{field} must be a non-empty string")
        return ""
    return value.strip()


def active_reference_paths() -> list[Path]:
    paths: list[Path] = []
    for root in ACTIVE_REFERENCE_ROOTS:
        root_path = repo_path(root)
        if not root_path.exists():
            continue
        candidates = [root_path] if root_path.is_file() else sorted(root_path.rglob("*"))
        for path in candidates:
            if not path.is_file() or is_excluded_reference_path(path):
                continue
            if path.suffix.lower() not in {".md", ".yml", ".yaml", ".sh", ".json"}:
                continue
            paths.append(path)
    return sorted(set(paths), key=rel)


def find_active_references(retired_paths: list[str]) -> dict[str, list[str]]:
    references: dict[str, list[str]] = {path: [] for path in retired_paths}
    if not retired_paths:
        return references
    for candidate in active_reference_paths():
        try:
            text = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for retired_path in retired_paths:
            if retired_path in text:
                references[retired_path].append(rel(candidate))
    return {key: sorted(set(values)) for key, values in references.items()}


def validate_artifact(owner: str, item: Any, status: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        errors.append(f"{owner} must be an object")
        return None

    path = require_string(owner, item, "path", errors)
    kind = require_string(owner, item, "kind", errors)
    path_state = require_string(owner, item, "path_state", errors)
    previous_sha256 = require_string(owner, item, "previous_sha256", errors)
    replacement_paths = validate_string_array(
        f"{owner}.replacement_paths",
        item.get("replacement_paths"),
        errors,
        required=path_state in {"renamed", "superseded"} and status == "accepted",
    )

    if kind and kind not in ALLOWED_ARTIFACT_KINDS:
        errors.append(f"{owner}.kind must be one of {sorted(ALLOWED_ARTIFACT_KINDS)}")
    if path_state and path_state not in ALLOWED_PATH_STATES:
        errors.append(f"{owner}.path_state must be one of {sorted(ALLOWED_PATH_STATES)}")
    if previous_sha256 and not SHA256.match(previous_sha256):
        errors.append(f"{owner}.previous_sha256 must be a lowercase 64-character SHA-256 hex string")

    path_obj = repo_path(path) if path else None
    path_exists = bool(path_obj and path_obj.exists())
    if status == "accepted" and path:
        if path_state == "retained-retired":
            if not path_exists:
                errors.append(f"{owner}.path_state retained-retired requires path to exist: {path}")
            elif previous_sha256 and SHA256.match(previous_sha256):
                current_sha256 = file_sha256(path_obj)
                if current_sha256 != previous_sha256:
                    errors.append(
                        f"{owner}.previous_sha256 is stale for retained-retired path {path}: "
                        f"expected {previous_sha256}, current {current_sha256}"
                    )
        elif path_exists:
            errors.append(f"{owner}.path must not exist after accepted {path_state} retirement: {path}")

    for replacement in replacement_paths:
        if not repo_path(replacement).exists():
            errors.append(f"{owner}.replacement_paths entry does not exist: {replacement}")

    return {
        "path": path,
        "kind": kind,
        "path_state": path_state,
        "previous_sha256": previous_sha256,
        "replacement_paths": replacement_paths,
        "path_exists": path_exists,
    }


def validate_validation(owner: str, value: Any, status: str, errors: list[str]) -> dict[str, int]:
    if not isinstance(value, dict):
        errors.append(f"{owner}.validation must be an object")
        return {"required_checks": 0, "checks_run": 0, "checks_pending": 0}

    required_checks = validate_string_array(f"{owner}.validation.required_checks", value.get("required_checks"), errors)
    checks_pending = validate_string_array(f"{owner}.validation.checks_pending", value.get("checks_pending"), errors)
    checks_run_raw = value.get("checks_run")
    checks_run = [item for item in checks_run_raw if isinstance(item, dict)] if isinstance(checks_run_raw, list) else []
    if checks_run_raw is not None and (not isinstance(checks_run_raw, list) or len(checks_run) != len(checks_run_raw)):
        errors.append(f"{owner}.validation.checks_run must be an object array")

    for index, check in enumerate(checks_run, start=1):
        check_owner = f"{owner}.validation.checks_run[{index}]"
        command = check.get("command")
        result = check.get("result")
        if not isinstance(command, str) or not command.strip():
            errors.append(f"{check_owner}.command must be a non-empty string")
        if result not in {"passed", "failed", "skipped"}:
            errors.append(f"{check_owner}.result must be passed, failed, or skipped")

    if status == "accepted":
        if not required_checks:
            errors.append(f"{owner}.validation.required_checks must be non-empty for accepted records")
        if not checks_run:
            errors.append(f"{owner}.validation.checks_run must be non-empty for accepted records")
        if checks_pending:
            errors.append(f"{owner}.validation.checks_pending must be empty for accepted records")

    return {
        "required_checks": len(required_checks),
        "checks_run": len(checks_run),
        "checks_pending": len(checks_pending),
    }


def validate_review(owner: str, value: Any, status: str, errors: list[str]) -> str:
    if not isinstance(value, dict):
        errors.append(f"{owner}.review must be an object")
        return ""
    required = value.get("required")
    decision = value.get("decision")
    if not isinstance(required, bool):
        errors.append(f"{owner}.review.required must be a boolean")
    if decision not in ALLOWED_REVIEW_DECISIONS:
        errors.append(f"{owner}.review.decision must be one of {sorted(ALLOWED_REVIEW_DECISIONS)}")
        return ""
    expected_decision = STATUS_TO_DECISION.get(status)
    if expected_decision and decision != expected_decision:
        errors.append(f"{owner}.review.decision must be {expected_decision} when status is {status}")
    if status == "accepted":
        reviewer = value.get("reviewer")
        if not isinstance(reviewer, str) or not reviewer.strip():
            errors.append(f"{owner}.review.reviewer must be present for accepted records")
    return decision


def validate_record(path: Path, data: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    owner = rel(path)
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"{owner} missing required field: {field}")

    schema = data.get("schema")
    if schema != RECORD_SCHEMA:
        errors.append(f"{owner}.schema must be {RECORD_SCHEMA}")

    retirement_id = require_string(owner, data, "retirement_id", errors)
    if retirement_id and not LOWER_DOT_ID.match(retirement_id):
        errors.append(f"{owner}.retirement_id must be a lower-dot identifier")

    status = require_string(owner, data, "status", errors)
    if status and status not in ALLOWED_STATUS:
        errors.append(f"{owner}.status must be one of {sorted(ALLOWED_STATUS)}")

    owner_layer = require_string(owner, data, "owner_layer", errors)
    if owner_layer and not OWNER_LAYER.match(owner_layer):
        errors.append(f"{owner}.owner_layer must use numbered layer form, such as 02.rag-rulebook")

    corpus_id = require_string(owner, data, "corpus_id", errors)
    if corpus_id and not CORPUS_ID.match(corpus_id):
        errors.append(f"{owner}.corpus_id must use corpus.<numbered-layer> form")

    if status == "superseded":
        superseded_by = data.get("superseded_by")
        if not isinstance(superseded_by, str) or not superseded_by.strip():
            errors.append(f"{owner}.superseded_by must be present when status is superseded")
    if status == "accepted":
        retired_at = data.get("retired_at_utc")
        if not isinstance(retired_at, str) or not retired_at.strip():
            errors.append(f"{owner}.retired_at_utc must be present when status is accepted")

    artifacts_raw = data.get("retired_artifacts")
    artifacts = [item for item in artifacts_raw if isinstance(item, dict)] if isinstance(artifacts_raw, list) else []
    if not artifacts:
        errors.append(f"{owner}.retired_artifacts must be a non-empty object array")
    elif len(artifacts) != len(artifacts_raw):
        errors.append(f"{owner}.retired_artifacts must contain only objects")

    normalized_artifacts = []
    for index, item in enumerate(artifacts_raw if isinstance(artifacts_raw, list) else [], start=1):
        artifact = validate_artifact(f"{owner}.retired_artifacts[{index}]", item, status, errors)
        if artifact:
            normalized_artifacts.append(artifact)

    artifact_paths = [item["path"] for item in normalized_artifacts if item.get("path")]
    duplicate_paths = sorted({item for item in artifact_paths if artifact_paths.count(item) > 1})
    for retired_path in duplicate_paths:
        errors.append(f"{owner}.retired_artifacts contains duplicate path: {retired_path}")

    reasons = validate_string_array(f"{owner}.reason", data.get("reason"), errors, required=True)

    reference_checks = data.get("reference_checks")
    checked_roots: list[str] = []
    declared_remaining: list[str] = []
    discovered_remaining: dict[str, list[str]] = {}
    if not isinstance(reference_checks, dict):
        errors.append(f"{owner}.reference_checks must be an object")
    else:
        checked_roots = validate_string_array(
            f"{owner}.reference_checks.checked_roots",
            reference_checks.get("checked_roots"),
            errors,
            required=status == "accepted",
        )
        declared_remaining = validate_string_array(
            f"{owner}.reference_checks.remaining_references",
            reference_checks.get("remaining_references"),
            errors,
        )
        for checked_root in checked_roots:
            if not repo_path(checked_root).exists():
                warnings.append(f"{owner}.reference_checks.checked_roots entry does not exist: {checked_root}")
        if status == "accepted" and declared_remaining:
            errors.append(f"{owner}.reference_checks.remaining_references must be empty for accepted records")
        if status == "accepted":
            discovered_remaining = find_active_references(artifact_paths)
            for retired_path, reference_paths in discovered_remaining.items():
                if reference_paths:
                    errors.append(
                        f"{owner} accepted retirement still has active references to {retired_path}: "
                        + ", ".join(reference_paths)
                    )

    validation_counts = validate_validation(owner, data.get("validation"), status, errors)
    review_decision = validate_review(owner, data.get("review"), status, errors)

    return {
        "path": owner,
        "retirement_id": retirement_id,
        "status": status,
        "owner_layer": owner_layer,
        "corpus_id": corpus_id,
        "retired_artifacts": normalized_artifacts,
        "reason_count": len(reasons),
        "checked_roots": checked_roots,
        "declared_remaining_references": declared_remaining,
        "discovered_remaining_references": discovered_remaining,
        "validation_counts": validation_counts,
        "review_decision": review_decision,
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    files = list_files(args, errors, warnings)

    records: list[dict[str, Any]] = []
    ids: list[str] = []
    for path in files:
        data = load_yaml(path, errors)
        if data is None:
            continue
        record = validate_record(path, data, errors, warnings)
        records.append(record)
        if record.get("retirement_id"):
            ids.append(record["retirement_id"])

    for retirement_id in sorted({item for item in ids if ids.count(item) > 1}):
        errors.append(f"duplicate retirement_id: {retirement_id}")

    report = {
        "schema": REPORT_SCHEMA,
        "ok": not errors,
        "records_root": DEFAULT_ROOT,
        "counts": {
            "records": len(records),
            "accepted": sum(1 for item in records if item.get("status") == "accepted"),
            "proposed": sum(1 for item in records if item.get("status") == "proposed"),
            "superseded": sum(1 for item in records if item.get("status") == "superseded"),
            "retired_artifacts": sum(len(item.get("retired_artifacts") or []) for item in records),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "records": records,
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
        print(f"Retirement records valid: {len(records)} record(s).")
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
