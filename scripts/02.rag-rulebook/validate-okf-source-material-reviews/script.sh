#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-okf-source-material-reviews
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#     - sre
#   kind: script
#   purpose: Validate governed OKF source-material review records without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.okf-source-material-review
#       path: .agentic/02.rag-rulebook/schemas/okf-source-material-review.schema.yml
#     - id: rag-rulebook.workflow.review-okf-source-material
#       path: .agentic/02.rag-rulebook/workflows/review-okf-source-material.md
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.validate-okf-source-material-reviews.readme
#       path: scripts/02.rag-rulebook/validate-okf-source-material-reviews/README.md
#     - id: rag-rulebook.script.validate-okf-source-material-reviews.smoke-test
#       path: scripts/02.rag-rulebook/validate-okf-source-material-reviews/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for OKF source-material review validation.", file=sys.stderr)
    sys.exit(2)


RECORD_SCHEMA = "rag-rulebook/okf-source-material-review/v1"
REPORT_SCHEMA = "rag-rulebook/okf-source-material-review-validation-report/v1"
DEFAULT_ROOT = ".agentic/02.rag-rulebook/source-material-reviews"
ALLOWED_STATUS = {"needs-review", "needs-revision", "accepted", "blocked", "superseded"}
ALLOWED_SOURCE_STATES = {"draft", "revised", "accepted", "blocked", "retired"}
ALLOWED_DECISIONS = {"pass", "revise", "block"}
CANONICAL_PASSING_SCORE = 9.5
CANONICAL_PASS_RULE = "every required reviewer score must be greater than 9.5 and no blocking gaps may remain"
CANONICAL_REQUIRED_ROLES = (
    "architect",
    "agentic-engineer",
    "secops-engineer",
    "senior-sre",
)
CANONICAL_REQUIRED_ROLE_SET = set(CANONICAL_REQUIRED_ROLES)
REQUIRED_DIMENSIONS = {
    "coverage",
    "necessity",
    "production_grade_gaps",
    "execution_variables",
    "human_readability",
    "machine_readability",
    "cost_optimization",
    "security",
    "performance",
    "token_optimization",
}


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
  validate-okf-source-material-reviews/script.sh --current [--json]
  validate-okf-source-material-reviews/script.sh --record <path> [--record <path> ...] [--json]

Validates rag-rulebook/okf-source-material-review/v1 YAML records. The command
is read-only.
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
                errors.append(f"review record path is not a YAML file: {rel(root)}")
            continue
        if root.is_dir():
            files.extend(sorted(root.rglob("*.yml")))
            files.extend(sorted(root.rglob("*.yaml")))
            continue
        if args.current and root == repo_path(DEFAULT_ROOT):
            warnings.append(f"review record directory is absent: {DEFAULT_ROOT}")
        else:
            errors.append(f"review record path does not exist: {rel(root)}")
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


def string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def validate_score(owner: str, value: Any, errors: list[str]) -> float | None:
    score = number(value)
    if score is None or score < 0 or score > 10:
        errors.append(f"{owner} must be a number between 0 and 10")
        return None
    return score


def validate_iteration(record_path: str, item: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(item, dict):
        errors.append(f"{record_path}.iterations[] must be an object")
        return {}
    owner = f"{record_path}.iterations[{item.get('iteration', '?')}]"
    assessments = item.get("reviewer_assessments")
    if not isinstance(assessments, list) or not assessments:
        errors.append(f"{owner}.reviewer_assessments must be a non-empty array")
        return {}
    by_role: dict[str, dict[str, Any]] = {}
    for index, assessment in enumerate(assessments, start=1):
        assessment_owner = f"{owner}.reviewer_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{assessment_owner} must be an object")
            continue
        role = assessment.get("role")
        if not isinstance(role, str) or not role.strip():
            errors.append(f"{assessment_owner}.role must be a non-empty string")
            continue
        if role not in CANONICAL_REQUIRED_ROLE_SET:
            errors.append(
                f"{assessment_owner}.role must be one of {sorted(CANONICAL_REQUIRED_ROLE_SET)}"
            )
        if role in by_role:
            errors.append(f"{owner} has duplicate reviewer role: {role}")
        by_role[role] = assessment
        validate_score(f"{assessment_owner}.overall_score", assessment.get("overall_score"), errors)
        if assessment.get("decision") not in ALLOWED_DECISIONS:
            errors.append(f"{assessment_owner}.decision must be one of {sorted(ALLOWED_DECISIONS)}")
        if not isinstance(assessment.get("blocking_gaps"), list):
            errors.append(f"{assessment_owner}.blocking_gaps must be an array")
        dimensions = assessment.get("dimension_scores")
        if not isinstance(dimensions, dict):
            errors.append(f"{assessment_owner}.dimension_scores must be an object")
        else:
            missing = sorted(REQUIRED_DIMENSIONS - set(dimensions))
            if missing:
                errors.append(f"{assessment_owner}.dimension_scores missing: {', '.join(missing)}")
            for key, value in dimensions.items():
                validate_score(f"{assessment_owner}.dimension_scores.{key}", value, errors)
        if not isinstance(assessment.get("recommendations"), list):
            errors.append(f"{assessment_owner}.recommendations must be an array")
    summary = item.get("cross_review_summary")
    if not isinstance(summary, dict):
        errors.append(f"{owner}.cross_review_summary must be an object")
    elif not isinstance(summary.get("unresolved_blockers"), list):
        errors.append(f"{owner}.cross_review_summary.unresolved_blockers must be an array")
    handling = item.get("recommendation_handling")
    if not isinstance(handling, dict):
        errors.append(f"{owner}.recommendation_handling must be an object")
    else:
        if not isinstance(handling.get("applied"), list):
            errors.append(f"{owner}.recommendation_handling.applied must be an array")
        if not isinstance(handling.get("rejected"), list):
            errors.append(f"{owner}.recommendation_handling.rejected must be an array")
    if not isinstance(item.get("rerun_required"), bool):
        errors.append(f"{owner}.rerun_required must be boolean")
    return by_role


def validate_record(path: Path, data: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    record_path = rel(path)
    if data.get("schema") != RECORD_SCHEMA:
        errors.append(f"{record_path}.schema must be {RECORD_SCHEMA}")
    if data.get("status") not in ALLOWED_STATUS:
        errors.append(f"{record_path}.status must be one of {sorted(ALLOWED_STATUS)}")

    source = data.get("source_material")
    source_hash = None
    if not isinstance(source, dict):
        errors.append(f"{record_path}.source_material must be an object")
    else:
        if source.get("source_state") not in ALLOWED_SOURCE_STATES:
            errors.append(f"{record_path}.source_material.source_state must be one of {sorted(ALLOWED_SOURCE_STATES)}")
        source_path = source.get("path")
        if not isinstance(source_path, str) or not source_path.strip():
            errors.append(f"{record_path}.source_material.path must be a non-empty string")
        else:
            source_file = repo_path(source_path)
            if not source_file.is_file():
                errors.append(f"{record_path}.source_material.path does not exist: {source_path}")
            else:
                source_hash = file_sha256(source_file)
                declared_hash = source.get("sha256")
                if isinstance(declared_hash, str) and declared_hash != source_hash:
                    errors.append(
                        f"{record_path}.source_material.sha256 is stale for {source_path}: "
                        f"expected {declared_hash}, current {source_hash}"
                    )

    threshold = data.get("threshold")
    passing_score = None
    required_roles: list[str] = []
    if not isinstance(threshold, dict):
        errors.append(f"{record_path}.threshold must be an object")
    else:
        passing_score = validate_score(f"{record_path}.threshold.passing_score", threshold.get("passing_score"), errors)
        if passing_score != CANONICAL_PASSING_SCORE:
            errors.append(
                f"{record_path}.threshold.passing_score must be {CANONICAL_PASSING_SCORE}"
            )
        required_roles = string_list(threshold.get("required_roles"))
        if not required_roles:
            errors.append(f"{record_path}.threshold.required_roles must be a non-empty string array")
        if len(set(required_roles)) != len(required_roles):
            errors.append(f"{record_path}.threshold.required_roles contains duplicates")
        if tuple(required_roles) != CANONICAL_REQUIRED_ROLES:
            errors.append(
                f"{record_path}.threshold.required_roles must be exactly: "
                f"{', '.join(CANONICAL_REQUIRED_ROLES)}"
            )
        if threshold.get("pass_rule") != CANONICAL_PASS_RULE:
            errors.append(f"{record_path}.threshold.pass_rule must be: {CANONICAL_PASS_RULE}")

    iterations = data.get("iterations")
    final_roles: dict[str, dict[str, Any]] = {}
    final_iteration = None
    if not isinstance(iterations, list) or not iterations:
        errors.append(f"{record_path}.iterations must be a non-empty array")
    else:
        for item in iterations:
            roles = validate_iteration(record_path, item, errors)
            if isinstance(item, dict) and (
                final_iteration is None
                or int(item.get("iteration") or 0) >= int(final_iteration.get("iteration") or 0)
            ):
                final_iteration = item
                final_roles = roles

    final_decision = data.get("final_decision")
    if not isinstance(final_decision, dict):
        errors.append(f"{record_path}.final_decision must be an object")
    elif data.get("status") == "accepted":
        if final_decision.get("status") != "accepted":
            errors.append(f"{record_path}.final_decision.status must be accepted")
        if source and source.get("source_state") != "accepted":
            errors.append(f"{record_path}.source_material.source_state must be accepted when review status is accepted")
        accepted_hash = final_decision.get("accepted_source_sha256")
        if source_hash and accepted_hash != source_hash:
            errors.append(
                f"{record_path}.final_decision.accepted_source_sha256 is stale: "
                f"expected {accepted_hash}, current {source_hash}"
            )
        if not isinstance(final_decision.get("accepted_at_utc"), str) or not final_decision["accepted_at_utc"].strip():
            errors.append(f"{record_path}.final_decision.accepted_at_utc must be a non-empty string")
        if not isinstance(final_decision.get("required_before_derivation"), list):
            errors.append(f"{record_path}.final_decision.required_before_derivation must be an array")
        if final_iteration and final_iteration.get("rerun_required") is not False:
            errors.append(f"{record_path}.final iteration must have rerun_required: false")
        summary = final_iteration.get("cross_review_summary") if isinstance(final_iteration, dict) else {}
        unresolved = summary.get("unresolved_blockers") if isinstance(summary, dict) else []
        if unresolved:
            errors.append(f"{record_path}.final iteration has unresolved blockers")
        if passing_score is not None:
            for role in required_roles:
                assessment = final_roles.get(role)
                if not assessment:
                    errors.append(f"{record_path}.final iteration missing required reviewer role: {role}")
                    continue
                score = number(assessment.get("overall_score"))
                if score is None or score <= passing_score:
                    errors.append(
                        f"{record_path}.final reviewer score for {role} must be greater than {passing_score}"
                    )
                if assessment.get("decision") != "pass":
                    errors.append(f"{record_path}.final reviewer decision for {role} must be pass")
                if assessment.get("blocking_gaps"):
                    errors.append(f"{record_path}.final reviewer {role} has blocking gaps")

    return {
        "path": record_path,
        "status": data.get("status"),
        "source_path": (source or {}).get("path") if isinstance(source, dict) else None,
        "required_roles": required_roles,
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    files = list_files(args, errors, warnings)
    records = []
    ids: dict[str, str] = {}
    for path in files:
        data = load_yaml(path, errors)
        if data is None:
            continue
        review_id = data.get("review_id")
        if isinstance(review_id, str):
            if review_id in ids:
                errors.append(f"duplicate review_id {review_id}: {ids[review_id]} and {rel(path)}")
            ids[review_id] = rel(path)
        else:
            errors.append(f"{rel(path)}.review_id must be a string")
        records.append(validate_record(path, data, errors))

    report = {
        "schema": REPORT_SCHEMA,
        "ok": not errors,
        "counts": {
            "records": len(files),
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
        print(f"OKF source-material review records valid: {len(files)} record(s).")
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
