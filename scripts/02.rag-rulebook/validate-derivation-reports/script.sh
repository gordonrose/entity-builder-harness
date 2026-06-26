#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-derivation-reports
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate governed source-to-rule derivation report YAML files without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.source-to-rule-derivation-report
#       path: .agentic/02.rag-rulebook/schemas/source-to-rule-derivation-report.schema.yml
#     - id: rag-rulebook.standard.source-to-rule-derivation
#       path: .agentic/02.rag-rulebook/standards/source-to-rule-derivation.md
#     - id: rag-rulebook.workflow.derive-rules-from-source
#       path: .agentic/02.rag-rulebook/workflows/derive-rules-from-source.md
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.validate-derivation-reports.readme
#       path: scripts/02.rag-rulebook/validate-derivation-reports/README.md
#     - id: rag-rulebook.script.validate-derivation-reports.smoke-test
#       path: scripts/02.rag-rulebook/validate-derivation-reports/smoke-test.sh

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
    print("ERROR: python3 yaml module is required for derivation-report validation.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/source-to-rule-derivation-report/v1"
DEFAULT_ROOT = ".agentic/02.rag-rulebook/derivation-reports"
LOWER_DOT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
OWNER_LAYER = re.compile(r"^[0-9]{2}\.[a-z0-9-]+$")
CORPUS_ID = re.compile(r"^corpus\.[0-9]{2}\.[a-z0-9-]+(?:\.[a-z0-9-]+)*$")
ALLOWED_STATUS = {"needs-review", "accepted", "blocked", "superseded"}
ALLOWED_CHANGE_TYPES = {"created", "updated", "removed", "split", "merged", "reorganized"}
ALLOWED_SOURCE_STATES = {"approved", "pending-review", "removed"}
ALLOWED_CONFLICT_STATUS = {"none-found", "suspected", "confirmed"}
ALLOWED_DRIFT_STATUS = {"none-found", "expected", "suspected", "confirmed"}
ALLOWED_OWNERSHIP_STATUS = {"ok", "needs-review", "conflict"}
ALLOWED_CHECK_RESULTS = {"passed", "failed", "skipped"}
ALLOWED_REVIEW_DECISIONS = {"pending", "approved", "blocked", "superseded"}
REQUIRED_TOP_LEVEL = [
    "schema",
    "report_id",
    "status",
    "source_change",
    "target",
    "semantic_review",
    "proposed_updates",
    "downstream_effects",
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
  validate-derivation-reports/script.sh --current [--json]
  validate-derivation-reports/script.sh --report <path> [--report <path> ...] [--json]

Validates rag-rulebook/source-to-rule-derivation-report/v1 YAML files. The
command is read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--report", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.report):
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


def path_exists(path: str) -> bool:
    return repo_path(path).exists()


def list_files(args: argparse.Namespace, errors: list[str], warnings: list[str]) -> list[Path]:
    roots = [repo_path(DEFAULT_ROOT)] if args.current else [repo_path(path) for path in args.report]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix in {".yml", ".yaml"}:
                files.append(root)
            else:
                errors.append(f"report path is not a YAML file: {rel(root)}")
            continue
        if root.is_dir():
            files.extend(sorted(root.rglob("*.yml")))
            files.extend(sorted(root.rglob("*.yaml")))
            continue
        if args.current and root == repo_path(DEFAULT_ROOT):
            warnings.append(f"derivation report directory is absent: {DEFAULT_ROOT}")
        else:
            errors.append(f"report path does not exist: {rel(root)}")
    if args.current and repo_path(DEFAULT_ROOT).is_dir() and not files:
        warnings.append(f"derivation report directory contains no YAML files: {DEFAULT_ROOT}")
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


def require_object(owner: str, data: dict[str, Any], field: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        errors.append(f"{owner}.{field} must be an object")
        return {}
    return value


def require_string(owner: str, data: dict[str, Any], field: str, errors: list[str]) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{owner}.{field} must be a non-empty string")
        return ""
    return value.strip()


def require_bool(owner: str, data: dict[str, Any], field: str, errors: list[str]) -> bool | None:
    value = data.get(field)
    if not isinstance(value, bool):
        errors.append(f"{owner}.{field} must be a boolean")
        return None
    return value


def validate_path_list(
    owner: str,
    value: Any,
    errors: list[str],
    *,
    required: bool = False,
    must_exist: bool = False,
) -> list[str]:
    paths = validate_string_array(owner, value, errors, required=required)
    if must_exist:
        for path in paths:
            if not path_exists(path):
                errors.append(f"{owner} references missing path: {path}")
    return paths


def validate_source_change(owner: str, data: dict[str, Any], errors: list[str]) -> None:
    source = require_object(owner, data, "source_change", errors)
    if not source:
        return
    change_type = require_string(f"{owner}.source_change", source, "change_type", errors)
    if change_type and change_type not in ALLOWED_CHANGE_TYPES:
        errors.append(f"{owner}.source_change.change_type is not allowed: {change_type}")
    source_state = require_string(f"{owner}.source_change", source, "approved_source_state", errors)
    if source_state and source_state not in ALLOWED_SOURCE_STATES:
        errors.append(f"{owner}.source_change.approved_source_state is not allowed: {source_state}")
    changed_paths = validate_path_list(
        f"{owner}.source_change.changed_paths",
        source.get("changed_paths"),
        errors,
        required=True,
        must_exist=source_state != "removed",
    )
    if source_state == "removed" and change_type != "removed":
        errors.append(f"{owner}.source_change removed source state requires change_type: removed")
    if source_state != "removed" and not changed_paths:
        errors.append(f"{owner}.source_change.changed_paths must name source paths")
    require_string(f"{owner}.source_change", source, "summary", errors)


def validate_target(owner: str, data: dict[str, Any], errors: list[str]) -> None:
    target = require_object(owner, data, "target", errors)
    if not target:
        return
    corpus_id = require_string(f"{owner}.target", target, "corpus_id", errors)
    if corpus_id and not CORPUS_ID.fullmatch(corpus_id):
        errors.append(f"{owner}.target.corpus_id must be a numbered corpus id: {corpus_id}")
    owner_layer = require_string(f"{owner}.target", target, "owner_layer", errors)
    if owner_layer and not OWNER_LAYER.fullmatch(owner_layer):
        errors.append(f"{owner}.target.owner_layer must be a numbered layer id: {owner_layer}")
    if isinstance(target.get("deploy_track"), str) and not OWNER_LAYER.fullmatch(target["deploy_track"]):
        errors.append(f"{owner}.target.deploy_track must be a numbered layer id when present")
    for field in [
        "expected_rule_paths",
        "affected_rule_paths",
        "affected_evaluations",
        "affected_corpus_gaps",
    ]:
        validate_path_list(
            f"{owner}.target.{field}",
            target.get(field),
            errors,
            must_exist=field != "expected_rule_paths",
        )
    validate_string_array(f"{owner}.target.affected_rulesets", target.get("affected_rulesets"), errors)


def validate_source_claims(owner: str, semantic: dict[str, Any], errors: list[str]) -> None:
    claims = semantic.get("source_claims")
    if not isinstance(claims, list) or not claims:
        errors.append(f"{owner}.semantic_review.source_claims must be a non-empty array")
        return
    for index, claim in enumerate(claims, start=1):
        claim_owner = f"{owner}.semantic_review.source_claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{claim_owner} must be an object")
            continue
        claim_id = require_string(claim_owner, claim, "claim_id", errors)
        if claim_id and not LOWER_DOT_ID.fullmatch(claim_id):
            errors.append(f"{claim_owner}.claim_id must be a stable lower id: {claim_id}")
        require_string(claim_owner, claim, "summary", errors)
        evidence_path = require_string(claim_owner, claim, "evidence_path", errors)
        if evidence_path and not path_exists(evidence_path):
            errors.append(f"{claim_owner}.evidence_path does not exist: {evidence_path}")


def validate_status_items(
    owner: str,
    data: dict[str, Any],
    field: str,
    allowed: set[str],
    errors: list[str],
) -> None:
    section = data.get(field)
    section_owner = f"{owner}.semantic_review.{field}"
    if not isinstance(section, dict):
        errors.append(f"{section_owner} must be an object")
        return
    status = require_string(section_owner, section, "status", errors)
    if status and status not in allowed:
        errors.append(f"{section_owner}.status is not allowed: {status}")
    items = section.get("items")
    if not isinstance(items, list):
        errors.append(f"{section_owner}.items must be an array")
        items = []
    if status == "none-found" and items:
        errors.append(f"{section_owner}.items must be empty when status is none-found")
    if status in {"suspected", "confirmed", "expected"} and not items:
        errors.append(f"{section_owner}.items must be non-empty when status is {status}")
    if field == "conflicts":
        validate_string_array(f"{section_owner}.search_scope", section.get("search_scope"), errors)


def validate_semantic_review(owner: str, data: dict[str, Any], errors: list[str]) -> None:
    semantic = require_object(owner, data, "semantic_review", errors)
    if not semantic:
        return
    validate_source_claims(owner, semantic, errors)
    validate_status_items(owner, semantic, "conflicts", ALLOWED_CONFLICT_STATUS, errors)
    validate_status_items(owner, semantic, "drift", ALLOWED_DRIFT_STATUS, errors)
    ownership = semantic.get("ownership")
    ownership_owner = f"{owner}.semantic_review.ownership"
    if not isinstance(ownership, dict):
        errors.append(f"{ownership_owner} must be an object")
        return
    ownership_status = require_string(ownership_owner, ownership, "status", errors)
    if ownership_status and ownership_status not in ALLOWED_OWNERSHIP_STATUS:
        errors.append(f"{ownership_owner}.status is not allowed: {ownership_status}")
    validate_string_array(f"{ownership_owner}.notes", ownership.get("notes"), errors, required=True)


def validate_proposed_updates(owner: str, data: dict[str, Any], errors: list[str]) -> None:
    updates = require_object(owner, data, "proposed_updates", errors)
    if not updates:
        return
    for field in [
        "rules",
        "rule_packs",
        "recognition_sources",
        "recognition_candidates",
        "corpus_gaps",
        "evaluations",
        "notes",
    ]:
        items = validate_string_array(f"{owner}.proposed_updates.{field}", updates.get(field), errors)
        if field in {"rules", "recognition_candidates", "corpus_gaps"}:
            for item in items:
                if item.startswith((".agentic/", "docs/", "scripts/")) and not path_exists(item):
                    errors.append(f"{owner}.proposed_updates.{field} references missing path: {item}")


def validate_downstream_effects(owner: str, data: dict[str, Any], errors: list[str]) -> None:
    effects = require_object(owner, data, "downstream_effects", errors)
    if not effects:
        return
    requires_follow_up = False
    for field in ["index_required", "chunks_required", "selector_evaluation_required", "publish_required"]:
        value = require_bool(f"{owner}.downstream_effects", effects, field, errors)
        requires_follow_up = requires_follow_up or bool(value)
    stale = validate_string_array(f"{owner}.downstream_effects.stale_artifacts", effects.get("stale_artifacts"), errors)
    if requires_follow_up and not stale:
        errors.append(f"{owner}.downstream_effects.stale_artifacts must name stale outputs when follow-up is required")


def validate_validation(owner: str, data: dict[str, Any], errors: list[str]) -> None:
    validation = require_object(owner, data, "validation", errors)
    if not validation:
        return
    validate_string_array(f"{owner}.validation.required_checks", validation.get("required_checks"), errors, required=True)
    checks_run = validation.get("checks_run")
    if not isinstance(checks_run, list):
        errors.append(f"{owner}.validation.checks_run must be an array")
        checks_run = []
    for index, check in enumerate(checks_run, start=1):
        check_owner = f"{owner}.validation.checks_run[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{check_owner} must be an object")
            continue
        require_string(check_owner, check, "command", errors)
        result = require_string(check_owner, check, "result", errors)
        if result and result not in ALLOWED_CHECK_RESULTS:
            errors.append(f"{check_owner}.result is not allowed: {result}")
    validate_string_array(f"{owner}.validation.checks_pending", validation.get("checks_pending"), errors)


def validate_review(owner: str, data: dict[str, Any], status: str, errors: list[str]) -> None:
    review = require_object(owner, data, "review", errors)
    if not review:
        return
    required = require_bool(f"{owner}.review", review, "required", errors)
    decision = require_string(f"{owner}.review", review, "decision", errors)
    if decision and decision not in ALLOWED_REVIEW_DECISIONS:
        errors.append(f"{owner}.review.decision is not allowed: {decision}")
    expected_decision = {
        "needs-review": "pending",
        "accepted": "approved",
        "blocked": "blocked",
        "superseded": "superseded",
    }.get(status)
    if expected_decision and decision != expected_decision:
        errors.append(f"{owner}.status {status} requires review.decision: {expected_decision}")
    if status == "accepted":
        for field in ["reviewer", "reviewed_at_utc"]:
            require_string(f"{owner}.review", review, field, errors)
        validate_string_array(f"{owner}.review.notes", review.get("notes"), errors, required=True)
    if status == "blocked":
        validate_string_array(f"{owner}.review.notes", review.get("notes"), errors, required=True)
    if status == "superseded":
        require_string(f"{owner}.review", review, "superseded_by", errors)
    if required is False and decision == "pending":
        errors.append(f"{owner}.review cannot be pending when review.required is false")


def validate_report(path: Path, data: dict[str, Any], errors: list[str]) -> str:
    owner = rel(path)
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"{owner}.{field} is required")

    schema = data.get("schema")
    if schema != REPORT_SCHEMA:
        errors.append(f"{owner}.schema must be {REPORT_SCHEMA}")

    report_id = require_string(owner, data, "report_id", errors)
    if report_id and not LOWER_DOT_ID.fullmatch(report_id):
        errors.append(f"{owner}.report_id must be a stable lower id: {report_id}")

    status = require_string(owner, data, "status", errors)
    if status and status not in ALLOWED_STATUS:
        errors.append(f"{owner}.status is not allowed: {status}")

    validate_source_change(owner, data, errors)
    validate_target(owner, data, errors)
    validate_semantic_review(owner, data, errors)
    validate_proposed_updates(owner, data, errors)
    validate_downstream_effects(owner, data, errors)
    validate_validation(owner, data, errors)
    validate_review(owner, data, status, errors)
    return report_id


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    files = list_files(args, errors, warnings)
    report_ids: dict[str, str] = {}

    for path in files:
        data = load_yaml(path, errors)
        if data is None:
            continue
        report_id = validate_report(path, data, errors)
        if report_id:
            previous = report_ids.get(report_id)
            if previous:
                errors.append(f"duplicate report_id {report_id}: {previous} and {rel(path)}")
            report_ids[report_id] = rel(path)

    report = {
        "ok": not errors,
        "schema": REPORT_SCHEMA,
        "counts": {
            "reports": len(files),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "reports": sorted(report_ids),
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
        print(f"Derivation reports valid: {len(files)} report(s).")
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
