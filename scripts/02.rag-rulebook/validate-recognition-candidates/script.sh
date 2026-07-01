#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-recognition-candidates
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Validate governed RAG/rulebook recognition-candidate YAML files without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.schema.recognition-candidate
#       path: .agentic/02.rag-rulebook/schemas/recognition-candidate.schema.yml
#     - id: rag-rulebook.standard.recognition-candidate-review
#       path: .agentic/02.rag-rulebook/standards/recognition-candidate-review.md
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.validate-recognition-candidates.readme
#       path: scripts/02.rag-rulebook/validate-recognition-candidates/README.md
#     - id: rag-rulebook.script.validate-recognition-candidates.smoke-test
#       path: scripts/02.rag-rulebook/validate-recognition-candidates/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for recognition-candidate validation.", file=sys.stderr)
    sys.exit(2)


CANDIDATE_SCHEMA = "rag-rulebook/recognition-candidate/v1"
DEFAULT_ROOT = ".agentic/02.rag-rulebook/recognition-candidates"
LOWER_DOT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
OWNER_LAYER = re.compile(r"^[0-9]{2}\.[a-z0-9-]+$")
CORPUS_ID = re.compile(r"^corpus\.[0-9]{2}\.[a-z0-9-]+(?:\.[a-z0-9-]+)*$")
ALLOWED_STATUS = {"needs-review", "accepted", "rejected", "merged", "deferred"}
ALLOWED_OBSERVED_SOURCES = {
    "chat-prompt",
    "chat-response",
    "evaluation-fixture",
    "commit-log",
    "human-note",
    "generated-report",
}
ALLOWED_CATEGORIES = {
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
ALLOWED_REVIEW_DECISIONS = {"pending", "accept", "reject", "merge", "defer"}
ALLOWED_COVERAGE_STATUS = {"missing", "partial", "covered", "not-required"}
ALLOWED_COVERAGE_STAGE_STATUS = {"missing", "present", "not-required"}
ALLOWED_EXECUTION_READINESS_STATUS = {"not-required", "ready", "blocked"}
REQUIRED_COVERAGE_STAGES = [
    "source_material",
    "structured_rulebook",
    "indexed_chunks",
    "selector_evaluation",
]
STATUS_TO_DECISION = {
    "needs-review": "pending",
    "accepted": "accept",
    "rejected": "reject",
    "merged": "merge",
    "deferred": "defer",
}
STATUS_TO_DIRECTORY = {
    "needs-review": "inbox",
    "accepted": "accepted",
    "rejected": "rejected",
    "merged": "merged",
    "deferred": "deferred",
}
DIRECTORY_TO_STATUS = {directory: status for status, directory in STATUS_TO_DIRECTORY.items()}
TERMINAL_STATUSES = {"accepted", "rejected", "merged", "deferred"}
REQUIRED_TOP_LEVEL = [
    "schema",
    "candidate_id",
    "status",
    "observed",
    "suggested",
    "reason",
    "review",
]


def repo_root() -> Path:
    override = os.environ.get("RAG_REPO_ROOT")
    if override:
        root = Path(override).resolve()
        assert_repo_root(root)
        return root
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    root = Path(result.stdout.strip())
    assert_repo_root(root)
    return root


def assert_repo_root(root: Path) -> None:
    markers = [
        "package.json",
        ".agentic/02.rag-rulebook/service",
        "scripts/02.rag-rulebook",
    ]
    for marker in markers:
        if not (root / marker).exists():
            raise SystemExit(f"ERROR: RAG repo root is missing required marker: {marker}")


ROOT = repo_root()


def usage() -> str:
    return """Usage:
  validate-recognition-candidates/script.sh --current [--json]
  validate-recognition-candidates/script.sh --candidate <path> [--candidate <path> ...] [--json]

Validates rag-rulebook/recognition-candidate/v1 YAML files. The command is
read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--candidate", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.candidate):
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


def lifecycle_directory(path: Path) -> str | None:
    try:
        relative_parts = path.resolve().relative_to(repo_path(DEFAULT_ROOT).resolve()).parts
    except ValueError:
        relative_parts = ()
    if relative_parts and relative_parts[0] in DIRECTORY_TO_STATUS:
        return relative_parts[0]

    parent = path.parent.name
    return parent if parent in DIRECTORY_TO_STATUS else None


def list_files(args: argparse.Namespace, errors: list[str], warnings: list[str]) -> list[Path]:
    roots = [repo_path(DEFAULT_ROOT)] if args.current else [repo_path(path) for path in args.candidate]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix in {".yml", ".yaml"}:
                files.append(root)
            else:
                errors.append(f"candidate path is not a YAML file: {rel(root)}")
            continue
        if root.is_dir():
            files.extend(sorted(root.rglob("*.yml")))
            files.extend(sorted(root.rglob("*.yaml")))
            continue
        if args.current and root == repo_path(DEFAULT_ROOT):
            warnings.append(f"recognition candidate directory is absent: {DEFAULT_ROOT}")
        else:
            errors.append(f"candidate path does not exist: {rel(root)}")

    if args.current and repo_path(DEFAULT_ROOT).is_dir() and not files:
        warnings.append(f"recognition candidate directory contains no YAML files: {DEFAULT_ROOT}")
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


def lower_contains(haystack: str, needle: str) -> bool:
    return needle.casefold() in haystack.casefold()


def validate_coverage_stages(
    owner: str,
    coverage: dict[str, Any],
    coverage_status: str | None,
    coverage_required: bool,
    errors: list[str],
) -> dict[str, int]:
    stages = coverage.get("stages")
    if stages is None:
        if coverage_required:
            errors.append(f"{owner}.coverage.stages must be present when coverage.required is true")
        return {"present": 0, "missing": 0, "not-required": 0}
    if not isinstance(stages, dict):
        errors.append(f"{owner}.coverage.stages must be an object when present")
        return {"present": 0, "missing": 0, "not-required": 0}

    if coverage_required:
        for stage_name in REQUIRED_COVERAGE_STAGES:
            if stage_name not in stages:
                errors.append(f"{owner}.coverage.stages missing required stage: {stage_name}")

    unsupported_stages = sorted(set(stages) - set(REQUIRED_COVERAGE_STAGES))
    for stage_name in unsupported_stages:
        errors.append(f"{owner}.coverage.stages has unsupported stage: {stage_name}")

    counts = {"present": 0, "missing": 0, "not-required": 0}
    for stage_name in REQUIRED_COVERAGE_STAGES:
        stage = stages.get(stage_name)
        if stage is None:
            continue
        stage_owner = f"{owner}.coverage.stages.{stage_name}"
        if not isinstance(stage, dict):
            errors.append(f"{stage_owner} must be an object")
            continue
        stage_status = stage.get("status")
        if stage_status not in ALLOWED_COVERAGE_STAGE_STATUS:
            errors.append(
                f"{stage_owner}.status must be one of: {', '.join(sorted(ALLOWED_COVERAGE_STAGE_STATUS))}"
            )
            continue
        counts[stage_status] += 1
        evidence_paths = validate_string_array(
            f"{stage_owner}.evidence_paths",
            stage.get("evidence_paths"),
            errors,
            required=stage_status == "present",
        )
        for evidence_path in evidence_paths:
            if not path_exists(evidence_path):
                errors.append(f"{stage_owner}.evidence_paths path does not exist: {evidence_path}")

    required_stage_count = counts["present"] + counts["missing"]
    if coverage_status == "missing" and counts["present"] > 0:
        errors.append(f"{owner}.coverage.status missing requires no required stages to be present")
    if coverage_status == "partial":
        if counts["present"] == 0:
            errors.append(f"{owner}.coverage.status partial requires at least one present stage")
        if counts["missing"] == 0:
            errors.append(f"{owner}.coverage.status partial requires at least one missing required stage")
    if coverage_status == "covered":
        if required_stage_count == 0:
            errors.append(f"{owner}.coverage.status covered requires at least one required stage")
        if counts["missing"] > 0:
            errors.append(f"{owner}.coverage.status covered requires every required stage to be present")
    if coverage_status == "not-required" and coverage_required:
        errors.append(f"{owner}.coverage.status not-required cannot be used when coverage.required is true")

    return counts


def validate_candidate(path: Path, data: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    owner = rel(path)
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"{owner} missing required field: {field}")

    if data.get("schema") != CANDIDATE_SCHEMA:
        errors.append(f"{owner}.schema must be {CANDIDATE_SCHEMA}")

    candidate_id = require_string(owner, data, "candidate_id", errors)
    if candidate_id and not LOWER_DOT_ID.match(candidate_id):
        errors.append(f"{owner}.candidate_id must be a lower dot/dash/underscore id: {candidate_id}")

    status = data.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"{owner}.status must be one of: {', '.join(sorted(ALLOWED_STATUS))}")
    lifecycle_dir = lifecycle_directory(path)
    if lifecycle_dir and status in ALLOWED_STATUS:
        expected_status = DIRECTORY_TO_STATUS[lifecycle_dir]
        if status != expected_status:
            errors.append(
                f"{owner}.status {status} does not match lifecycle directory {lifecycle_dir}; "
                f"expected {expected_status}"
            )

    observed = data.get("observed")
    if not isinstance(observed, dict):
        errors.append(f"{owner}.observed must be an object")
        observed = {}
    term = require_string(f"{owner}.observed", observed, "term", errors)
    sentence = require_string(f"{owner}.observed", observed, "sentence", errors)
    observed_source = observed.get("source")
    if observed_source not in ALLOWED_OBSERVED_SOURCES:
        errors.append(f"{owner}.observed.source must be one of: {', '.join(sorted(ALLOWED_OBSERVED_SOURCES))}")
    if term and sentence and not lower_contains(sentence, term):
        errors.append(f"{owner}.observed.sentence must include observed.term: {term}")
    prompt_excerpt = observed.get("prompt_excerpt")
    if prompt_excerpt is not None and (not isinstance(prompt_excerpt, str) or not prompt_excerpt.strip()):
        errors.append(f"{owner}.observed.prompt_excerpt must be a non-empty string when present")
    layer = observed.get("layer")
    if layer is not None and (not isinstance(layer, str) or not OWNER_LAYER.match(layer)):
        errors.append(f"{owner}.observed.layer must look like 02.rag-rulebook when present")
    mode = observed.get("mode")
    if mode is not None and (not isinstance(mode, str) or not mode.strip()):
        errors.append(f"{owner}.observed.mode must be a non-empty string when present")
    workflow = observed.get("workflow")
    if workflow is not None:
        if not isinstance(workflow, str) or not workflow.strip():
            errors.append(f"{owner}.observed.workflow must be a non-empty string when present")
        elif workflow.startswith(".agentic/") and not path_exists(workflow):
            errors.append(f"{owner}.observed.workflow path does not exist: {workflow}")
    observed_at = observed.get("observed_at_utc")
    if observed_at is not None and (not isinstance(observed_at, str) or not observed_at.endswith("Z")):
        errors.append(f"{owner}.observed.observed_at_utc must be an ISO-8601 UTC string ending in Z when present")

    suggested = data.get("suggested")
    if not isinstance(suggested, dict):
        errors.append(f"{owner}.suggested must be an object")
        suggested = {}
    source_id = require_string(f"{owner}.suggested", suggested, "source_id", errors)
    if source_id and not source_id.startswith("recognition.curated."):
        errors.append(f"{owner}.suggested.source_id must target a curated recognition source")
    category = require_string(f"{owner}.suggested", suggested, "category", errors)
    if category and category not in ALLOWED_CATEGORIES:
        errors.append(f"{owner}.suggested.category must be one of: {', '.join(sorted(ALLOWED_CATEGORIES))}")
    canonical_id = require_string(f"{owner}.suggested", suggested, "canonical_id", errors)
    if canonical_id and not LOWER_DOT_ID.match(canonical_id):
        errors.append(f"{owner}.suggested.canonical_id must be a lower dot/dash/underscore id: {canonical_id}")
    confidence_weight = suggested.get("confidence_weight")
    if not isinstance(confidence_weight, (int, float)) or not 0 <= float(confidence_weight) <= 1:
        errors.append(f"{owner}.suggested.confidence_weight must be between 0 and 1")
    target_source_path = suggested.get("target_source_path")
    if target_source_path is not None and (not isinstance(target_source_path, str) or not target_source_path.strip()):
        errors.append(f"{owner}.suggested.target_source_path must be a non-empty string when present")
    fixture_path = suggested.get("fixture_path")
    if fixture_path is not None:
        if not isinstance(fixture_path, str) or not fixture_path.strip():
            errors.append(f"{owner}.suggested.fixture_path must be a non-empty string when present")
        elif not path_exists(fixture_path):
            errors.append(f"{owner}.suggested.fixture_path path does not exist: {fixture_path}")

    coverage = data.get("coverage")
    coverage_status = None
    coverage_required = False
    if coverage is not None:
        if not isinstance(coverage, dict):
            errors.append(f"{owner}.coverage must be an object when present")
            coverage = {}
        coverage_required = coverage.get("required") is True
        if "required" in coverage and not isinstance(coverage.get("required"), bool):
            errors.append(f"{owner}.coverage.required must be a boolean when present")
        coverage_status = coverage.get("status")
        if coverage_status not in ALLOWED_COVERAGE_STATUS:
            errors.append(f"{owner}.coverage.status must be one of: {', '.join(sorted(ALLOWED_COVERAGE_STATUS))}")
        needed_corpus_ids = validate_string_array(
            f"{owner}.coverage.needed_corpus_ids",
            coverage.get("needed_corpus_ids"),
            errors,
            required=coverage_status in {"missing", "partial"},
        )
        for corpus_id in needed_corpus_ids:
            if not CORPUS_ID.match(corpus_id):
                errors.append(f"{owner}.coverage.needed_corpus_ids contains invalid corpus ID: {corpus_id}")
        evidence_paths = validate_string_array(
            f"{owner}.coverage.evidence_paths",
            coverage.get("evidence_paths"),
            errors,
        )
        for evidence_path in evidence_paths:
            if not path_exists(evidence_path):
                errors.append(f"{owner}.coverage.evidence_paths path does not exist: {evidence_path}")
        gap_id = coverage.get("gap_id")
        if coverage_status in {"missing", "partial"}:
            if not isinstance(gap_id, str) or not gap_id.startswith("gap."):
                errors.append(f"{owner}.coverage.gap_id must be a stable gap.* ID when coverage is missing or partial")
            require_string(f"{owner}.coverage", coverage, "needed_topic", errors)
            require_string(f"{owner}.coverage", coverage, "suggested_resolution", errors)
        elif gap_id is not None and (not isinstance(gap_id, str) or not gap_id.startswith("gap.")):
            errors.append(f"{owner}.coverage.gap_id must be a stable gap.* ID when present")
        validate_coverage_stages(owner, coverage, coverage_status, coverage_required, errors)

    execution_readiness = data.get("execution_readiness")
    if execution_readiness is not None:
        if not isinstance(execution_readiness, dict):
            errors.append(f"{owner}.execution_readiness must be an object when present")
            execution_readiness = {}
        readiness_status = execution_readiness.get("status")
        if readiness_status not in ALLOWED_EXECUTION_READINESS_STATUS:
            errors.append(
                f"{owner}.execution_readiness.status must be one of: "
                f"{', '.join(sorted(ALLOWED_EXECUTION_READINESS_STATUS))}"
            )
        readiness_gap_id = execution_readiness.get("gap_id")
        if readiness_status == "blocked":
            if not isinstance(readiness_gap_id, str) or not readiness_gap_id.startswith("gap."):
                errors.append(f"{owner}.execution_readiness.gap_id must be a stable gap.* ID when execution is blocked")
            require_string(f"{owner}.execution_readiness", execution_readiness, "reason", errors)
        elif readiness_gap_id is not None and (not isinstance(readiness_gap_id, str) or not readiness_gap_id.startswith("gap.")):
            errors.append(f"{owner}.execution_readiness.gap_id must be a stable gap.* ID when present")

    reason = data.get("reason")
    reason_items = as_string_list(reason)
    if not isinstance(reason, list) or not reason_items or len(reason_items) != len(reason):
        errors.append(f"{owner}.reason must be a non-empty string array")

    review = data.get("review")
    if not isinstance(review, dict):
        errors.append(f"{owner}.review must be an object")
        review = {}
    required = review.get("required")
    if not isinstance(required, bool):
        errors.append(f"{owner}.review.required must be a boolean")
    decision = review.get("decision")
    if decision not in ALLOWED_REVIEW_DECISIONS:
        errors.append(f"{owner}.review.decision must be one of: {', '.join(sorted(ALLOWED_REVIEW_DECISIONS))}")
    if status in STATUS_TO_DECISION and decision in ALLOWED_REVIEW_DECISIONS and STATUS_TO_DECISION[status] != decision:
        errors.append(f"{owner}.status {status} requires review.decision {STATUS_TO_DECISION[status]}")

    reviewer_notes = review.get("reviewer_notes", "")
    if reviewer_notes is not None and not isinstance(reviewer_notes, str):
        errors.append(f"{owner}.review.reviewer_notes must be a string when present")
    reviewer = review.get("reviewer")
    if reviewer is not None and (not isinstance(reviewer, str) or not reviewer.strip()):
        errors.append(f"{owner}.review.reviewer must be a non-empty string when present")
    reviewed_at = review.get("reviewed_at_utc")
    if reviewed_at is not None and (not isinstance(reviewed_at, str) or not reviewed_at.endswith("Z")):
        errors.append(f"{owner}.review.reviewed_at_utc must be an ISO-8601 UTC string ending in Z when present")
    if status in TERMINAL_STATUSES:
        require_string(f"{owner}.review", review, "reviewer", errors)
        require_string(f"{owner}.review", review, "reviewed_at_utc", errors)
        if not str(reviewer_notes or "").strip():
            errors.append(f"{owner}.review.reviewer_notes must explain terminal review decisions")
    if status == "accepted":
        accepted_source_path = require_string(f"{owner}.review", review, "accepted_source_path", errors)
        accepted_fixture_path = require_string(f"{owner}.review", review, "accepted_fixture_path", errors)
        if accepted_source_path and not path_exists(accepted_source_path):
            errors.append(f"{owner}.review.accepted_source_path path does not exist: {accepted_source_path}")
        if accepted_fixture_path and not path_exists(accepted_fixture_path):
            errors.append(f"{owner}.review.accepted_fixture_path path does not exist: {accepted_fixture_path}")
        if coverage_required and coverage_status != "covered":
            errors.append(f"{owner}.coverage.status must be covered before accepting a coverage-required candidate")
    if status == "merged":
        require_string(f"{owner}.review", review, "merged_into_candidate_id", errors)

    return {
        "path": rel(path),
        "candidate_id": candidate_id,
        "status": status,
        "lifecycle_directory": lifecycle_dir,
        "term": term,
        "suggested_source_id": source_id,
        "category": category,
        "coverage_status": coverage_status,
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    files = list_files(args, errors, warnings)
    summaries: list[dict[str, Any]] = []
    seen_candidate_ids: dict[str, str] = {}

    for path in files:
        data = load_yaml(path, errors)
        if data is None:
            continue
        summary = validate_candidate(path, data, errors, warnings)
        candidate_id = summary.get("candidate_id")
        if candidate_id:
            if candidate_id in seen_candidate_ids:
                errors.append(
                    f"duplicate candidate_id {candidate_id}: {seen_candidate_ids[candidate_id]} and {summary['path']}"
                )
            seen_candidate_ids[candidate_id] = summary["path"]
        summaries.append(summary)

    status_counts: dict[str, int] = {}
    for summary in summaries:
        status = str(summary.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    report = {
        "ok": not errors,
        "schema": CANDIDATE_SCHEMA,
        "root": str(ROOT),
        "counts": {
            "files": len(files),
            "candidates": len(summaries),
            "statuses": dict(sorted(status_counts.items())),
        },
        "candidates": summaries,
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
        print(f"Recognition candidates valid: {len(summaries)} candidate(s).")
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
