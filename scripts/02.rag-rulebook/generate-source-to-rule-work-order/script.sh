#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-source-to-rule-work-order
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate a read-only source-to-rule work order for governed corpus-to-YAML derivation.
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
#     - id: rag-rulebook.script.generate-source-to-rule-work-order.readme
#       path: scripts/02.rag-rulebook/generate-source-to-rule-work-order/README.md

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
    print("ERROR: python3 yaml module is required for source-to-rule work orders.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/source-to-rule-work-order/v1"
DEFAULT_MANIFEST = ".agentic/02.rag-rulebook/source-projections/v1.yml"
DERIVATION_WORKFLOW = ".agentic/02.rag-rulebook/workflows/derive-rules-from-source.md"
DERIVATION_STANDARD = ".agentic/02.rag-rulebook/standards/source-to-rule-derivation.md"
PROJECTION_PLANNER = "scripts/02.rag-rulebook/generate-derived-rules/script.sh"
GENERATOR = "source-to-rule-work-order"
GENERATOR_VERSION = "v1"


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
  generate-source-to-rule-work-order/script.sh --current [--json]
  generate-source-to-rule-work-order/script.sh --current --projection-id <id> [--json]
  generate-source-to-rule-work-order/script.sh --current --manifest <path> [--json]

Generates a read-only work order for semantic source-to-rule derivation. The
command does not write YAML rule content, derivation reports, chunks, or
evaluations.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--projection-id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if not args.current:
        print("ERROR: --current is required.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def load_yaml(path: str | Path) -> Any:
    return yaml.safe_load(repo_path(path).read_text(encoding="utf-8"))


def list_strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def file_sha256(path: str) -> str | None:
    path_obj = repo_path(path)
    if not path_obj.is_file():
        return None
    digest = hashlib.sha256()
    with path_obj.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def markdown_outline(path: str, max_headings: int = 24) -> list[dict[str, Any]]:
    path_obj = repo_path(path)
    if not path_obj.is_file():
        return []
    outline: list[dict[str, Any]] = []
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    for line_number, line in enumerate(path_obj.read_text(encoding="utf-8").splitlines(), start=1):
        match = heading_pattern.match(line)
        if not match:
            continue
        outline.append(
            {
                "line": line_number,
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
            }
        )
        if len(outline) >= max_headings:
            break
    return outline


def run_projection_planner(manifest: str) -> tuple[dict[str, Any], list[str]]:
    result = subprocess.run(
        [
            "bash",
            PROJECTION_PLANNER,
            "--current",
            "--manifest",
            manifest,
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    errors: list[str] = []
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return (
            {
                "schema": "rag-rulebook/derived-rule-projection-plan/v1",
                "ok": False,
                "projection_sets": [],
                "errors": [result.stderr.strip() or result.stdout.strip() or "projection planner did not emit JSON"],
            },
            ["projection planner did not emit JSON"],
        )
    if result.returncode != 0:
        errors.extend(str(error) for error in report.get("errors") or [])
        for projection_id in report.get("stale_or_incomplete_projection_sets") or []:
            errors.append(f"projection set is stale or incomplete: {projection_id}")
    return report, errors


def report_review_state(path: str) -> dict[str, Any]:
    path_obj = repo_path(path)
    if not path_obj.is_file():
        return {"path": path, "exists": False, "status": "missing", "review_decision": "missing"}
    data = load_yaml(path)
    if not isinstance(data, dict):
        return {"path": path, "exists": True, "status": "invalid", "review_decision": "invalid"}
    review = data.get("review") if isinstance(data.get("review"), dict) else {}
    return {
        "path": path,
        "exists": True,
        "status": data.get("status") if isinstance(data.get("status"), str) else "unknown",
        "review_decision": review.get("decision") if isinstance(review.get("decision"), str) else "unknown",
    }


def path_status(path: str) -> dict[str, Any]:
    return {
        "path": path,
        "exists": repo_path(path).exists(),
        "kind": "file" if repo_path(path).is_file() else ("directory" if repo_path(path).is_dir() else "missing"),
    }


def work_actions(projection: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    rule_items = projection.get("expected_rule_paths") if isinstance(projection.get("expected_rule_paths"), list) else []
    reports = projection.get("derivation_reports") if isinstance(projection.get("derivation_reports"), list) else []

    if any(isinstance(item, dict) and item.get("action") == "create-derived-rule" for item in rule_items):
        actions.append(
            {
                "id": "draft-derived-rule-yaml",
                "reason": "One or more expected structured rule files are missing.",
            }
        )
    if any(isinstance(item, dict) and item.get("action") == "add-source-derivation" for item in rule_items):
        actions.append(
            {
                "id": "add-source-derivation",
                "reason": "One or more projected YAML files lack source_derivation provenance.",
            }
        )
    if any(isinstance(item, dict) and item.get("action") == "refresh-source-derivation" for item in rule_items):
        actions.append(
            {
                "id": "refresh-source-derivation",
                "reason": "One or more projected YAML files have stale or incomplete provenance.",
            }
        )
    if any(isinstance(item, dict) and not item.get("exists") for item in reports):
        actions.append(
            {
                "id": "create-derivation-report",
                "reason": "The projection requires a derivation report that is missing.",
            }
        )
    if any(isinstance(item, dict) and item.get("status") == "needs-review" for item in reports):
        actions.append(
            {
                "id": "review-derivation-report",
                "reason": "A derivation report exists but still needs review.",
            }
        )
    if projection.get("semantic_review") == "needs-review":
        actions.append(
            {
                "id": "semantic-review",
                "reason": "Semantic derivation is not accepted yet.",
            }
        )
    if projection.get("corpus_gap_paths"):
        actions.append(
            {
                "id": "review-corpus-gaps",
                "reason": "The projection names corpus gaps that may block retrieval or deployment readiness.",
            }
        )
    if projection.get("expected_selector_evaluations"):
        actions.append(
            {
                "id": "verify-selector-evaluations",
                "reason": "Selector behavior must prove that derived knowledge is retrievable in the expected contexts.",
            }
        )
    if projection.get("required_checks"):
        actions.append(
            {
                "id": "run-required-checks",
                "reason": "The projection manifest names checks that must pass after semantic updates.",
            }
        )

    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for action in actions:
        if action["id"] in seen:
            continue
        seen.add(action["id"])
        deduped.append(action)
    return deduped or [{"id": "none", "reason": "Projection is mechanically current and has no immediate work-order actions."}]


def derivation_instructions() -> list[str]:
    return [
        f"Read {DERIVATION_WORKFLOW} and {DERIVATION_STANDARD}.",
        "Compare source material claims with existing structured rules before writing YAML.",
        "Record conflicts, drift, ownership issues, and unresolved decisions in the derivation report.",
        "Prefer narrow YAML rule updates over broad rewrites.",
        "Do not mark chunks, selector evaluations, packages, or runtime outputs current until generators and checks prove them.",
        "Use provenance-only apply mode only after semantic rule content and derivation report state are correct.",
    ]


def build_projection_work_order(projection: dict[str, Any]) -> dict[str, Any]:
    source_entries = []
    for item in projection.get("source_material") or []:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        path = item["path"]
        source_entries.append(
            {
                "path": path,
                "role": item.get("role") if isinstance(item.get("role"), str) else "unknown",
                "exists": repo_path(path).is_file(),
                "sha256": file_sha256(path),
                "outline": markdown_outline(path),
            }
        )

    return {
        "id": projection.get("id"),
        "status": projection.get("status"),
        "projection_mode": projection.get("projection_mode"),
        "target": projection.get("target") if isinstance(projection.get("target"), dict) else {},
        "source_material": source_entries,
        "expected_rule_paths": projection.get("expected_rule_paths") or [],
        "derivation_reports": [
            report_review_state(item.get("path"))
            if isinstance(item, dict) and isinstance(item.get("path"), str)
            else item
            for item in (projection.get("derivation_reports") or [])
        ],
        "corpus_gap_paths": [path_status(path) for path in projection.get("corpus_gap_paths") or []],
        "expected_selector_evaluations": [path_status(path) for path in projection.get("expected_selector_evaluations") or []],
        "required_checks": projection.get("required_checks") or [],
        "mechanically_current": bool(projection.get("mechanically_current")),
        "semantic_review": projection.get("semantic_review"),
        "work_actions": work_actions(projection),
        "derivation_instructions": derivation_instructions(),
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    projection_report, projection_errors = run_projection_planner(args.manifest)
    projection_sets = [
        item
        for item in projection_report.get("projection_sets") or []
        if isinstance(item, dict)
    ]

    if args.projection_id:
        projection_sets = [
            item for item in projection_sets if item.get("id") == args.projection_id
        ]
        if not projection_sets:
            print(f"ERROR: projection not found: {args.projection_id}", file=sys.stderr)
            return 1

    work_orders = [build_projection_work_order(item) for item in projection_sets]
    ok = bool(projection_report.get("ok")) and not projection_errors
    report = {
        "schema": REPORT_SCHEMA,
        "ok": ok,
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "manifest_path": args.manifest,
        "projection_planner": {
            "schema": projection_report.get("schema"),
            "ok": bool(projection_report.get("ok")),
            "error_count": len(projection_errors),
        },
        "counts": {
            "projection_sets": len(work_orders),
            "work_actions": sum(len(item["work_actions"]) for item in work_orders),
            "mechanically_current": sum(1 for item in work_orders if item["mechanically_current"]),
        },
        "work_orders": work_orders,
        "errors": projection_errors,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif ok:
        print(f"Source-to-rule work order ready: {len(work_orders)} projection set(s).")
    else:
        for error in projection_errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
