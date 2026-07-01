#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.generate-derived-rules
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Generate a source-to-rule projection plan and optionally refresh YAML provenance blocks.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.source-projections.v1
#       path: .agentic/02.rag-rulebook/source-projections/v1.yml
#     - id: rag-rulebook.script.generate-derived-rules.readme
#       path: scripts/02.rag-rulebook/generate-derived-rules/README.md

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
except ImportError:
    print("ERROR: python3 yaml module is required for derived rule projection planning.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/derived-rule-projection-plan/v1"
MANIFEST_SCHEMA = "rag-rulebook/source-projection-manifest/v1"
DEFAULT_MANIFEST = ".agentic/02.rag-rulebook/source-projections/v1.yml"
DERIVATION_WORKFLOW = ".agentic/02.rag-rulebook/workflows/derive-rules-from-source.md"
GENERATOR = "agent-assisted-source-to-rule"
GENERATOR_VERSION = "v1"
PROVENANCE_VERSION = "rag-rulebook/source-derivation-provenance/v1"
SOURCE_PROJECTION_CHECK = "scripts/02.rag-rulebook/check-source-projections/script.sh"


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
  generate-derived-rules/script.sh --current [--json] [--check]
  generate-derived-rules/script.sh --current --apply-provenance [--json]
  generate-derived-rules/script.sh --current --manifest <path> [--json] [--check]

Generates a read-only source-to-rule projection plan. The command does not
rewrite YAML rule content. In --check mode it fails when declared source
projections are mechanically stale or incomplete. In --apply-provenance mode it
rewrites only existing top-level source_derivation blocks for declared rule
paths, then reruns source projection checks.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply-provenance", action="store_true")
    parser.add_argument("--generated-at-utc")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if not args.current:
        print("ERROR: --current is required.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.check and args.apply_provenance:
        print("ERROR: --check and --apply-provenance cannot be combined.", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def load_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(repo_path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def list_strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def list_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def file_sha256(path: str) -> str | None:
    path_obj = repo_path(path)
    if not path_obj.is_file():
        return None
    digest = hashlib.sha256()
    with path_obj.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_source_projection_check(manifest_path: str) -> dict[str, Any]:
    result = subprocess.run(
        [
            "bash",
            SOURCE_PROJECTION_CHECK,
            "--current",
            "--manifest",
            manifest_path,
            "--json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        report = {
            "schema": "rag-rulebook/source-projection-check-report/v1",
            "ok": False,
            "errors": [result.stderr.strip() or result.stdout.strip() or "source projection check did not emit JSON"],
        }
    if result.returncode != 0:
        report["ok"] = False
    return report


def source_material_entries(raw_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in raw_entries:
        path = item.get("path")
        role = item.get("role")
        if not isinstance(path, str):
            continue
        entries.append(
            {
                "path": path,
                "role": role if isinstance(role, str) else "unknown",
                "exists": repo_path(path).is_file(),
                "sha256": file_sha256(path),
            }
        )
    return entries


def provenance_template(source_entries: list[dict[str, Any]], report_paths: list[str]) -> dict[str, Any]:
    return {
        "provenance_version": PROVENANCE_VERSION,
        "mode": "generated-projection",
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "generated_at_utc": "<set-on-apply>",
        "derivation_workflow": DERIVATION_WORKFLOW,
        "derivation_report": report_paths[0] if report_paths else "<required-derivation-report>",
        "source_material": [
            {
                "path": item["path"],
                "sha256": item["sha256"] or "<missing-source>",
            }
            for item in source_entries
        ],
    }


def applied_generated_at(args: argparse.Namespace) -> str:
    if isinstance(args.generated_at_utc, str) and args.generated_at_utc.strip():
        return args.generated_at_utc.strip()
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def applied_provenance(
    source_entries: list[dict[str, Any]],
    report_paths: list[str],
    generated_at_utc: str,
) -> dict[str, Any]:
    data = provenance_template(source_entries, report_paths)
    data["generated_at_utc"] = generated_at_utc
    return data


def report_status(path: str) -> dict[str, Any]:
    if not repo_path(path).is_file():
        return {"path": path, "exists": False, "status": "missing", "review_decision": "missing"}
    data = load_yaml(path)
    review = data.get("review") if isinstance(data.get("review"), dict) else {}
    return {
        "path": path,
        "exists": True,
        "status": data.get("status") if isinstance(data.get("status"), str) else "unknown",
        "review_decision": review.get("decision") if isinstance(review.get("decision"), str) else "unknown",
    }


def rule_projection_status(
    rule_path: str,
    source_entries: list[dict[str, Any]],
    report_paths: list[str],
) -> dict[str, Any]:
    path_obj = repo_path(rule_path)
    if not path_obj.is_file():
        return {
            "path": rule_path,
            "exists": False,
            "action": "create-derived-rule",
            "source_derivation_current": False,
            "errors": ["derived rule file is missing"],
        }

    data = load_yaml(rule_path)
    derivation = data.get("source_derivation")
    if not isinstance(derivation, dict):
        return {
            "path": rule_path,
            "exists": True,
            "action": "add-source-derivation",
            "source_derivation_current": False,
            "errors": ["source_derivation is missing"],
        }

    errors: list[str] = []
    expected_sources = {item["path"]: item["sha256"] for item in source_entries}
    actual_sources: dict[str, str] = {}
    material = derivation.get("source_material")
    if not isinstance(material, list) or not material:
        errors.append("source_derivation.source_material is missing")
    else:
        for material_item in material:
            if not isinstance(material_item, dict):
                errors.append("source_derivation.source_material contains a non-object item")
                continue
            path = material_item.get("path")
            sha256 = material_item.get("sha256")
            if isinstance(path, str) and isinstance(sha256, str):
                actual_sources[path] = sha256

    for path, expected_sha in expected_sources.items():
        actual_sha = actual_sources.get(path)
        if actual_sha is None:
            errors.append(f"source_derivation is missing source material: {path}")
        elif expected_sha is None:
            errors.append(f"source material is missing on disk: {path}")
        elif actual_sha != expected_sha:
            errors.append(f"source_derivation hash is stale for {path}")

    for path in sorted(set(actual_sources) - set(expected_sources)):
        errors.append(f"source_derivation includes undeclared source material: {path}")

    derivation_report = derivation.get("derivation_report")
    if report_paths and derivation_report not in report_paths:
        errors.append("source_derivation.derivation_report is not declared in projection manifest")

    for field, expected in [
        ("provenance_version", PROVENANCE_VERSION),
        ("generator", GENERATOR),
        ("generator_version", GENERATOR_VERSION),
        ("derivation_workflow", DERIVATION_WORKFLOW),
    ]:
        if derivation.get(field) != expected:
            errors.append(f"source_derivation.{field} differs from generator expectation")

    action = "current" if not errors else "refresh-source-derivation"
    return {
        "path": rule_path,
        "exists": True,
        "action": action,
        "source_derivation_current": not errors,
        "errors": errors,
        "current_source_derivation": derivation,
        "provenance_template": provenance_template(source_entries, report_paths),
    }


def render_source_derivation_block(provenance: dict[str, Any]) -> list[str]:
    rendered = yaml.safe_dump(
        {"source_derivation": provenance},
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )
    return rendered.splitlines()


def replace_existing_source_derivation(rule_path: str, provenance: dict[str, Any]) -> bool:
    path_obj = repo_path(rule_path)
    lines = path_obj.read_text(encoding="utf-8").splitlines()
    start = None
    for index, line in enumerate(lines):
        if line == "source_derivation:":
            start = index
            break
    if start is None:
        raise ValueError(f"{rule_path} has no existing top-level source_derivation block")

    end = start + 1
    top_level_pattern = re.compile(r"^[A-Za-z0-9_-]+:")
    while end < len(lines):
        line = lines[end]
        if line.strip() and top_level_pattern.match(line):
            break
        end += 1

    new_block = render_source_derivation_block(provenance)
    if end < len(lines) and (not new_block or new_block[-1] != ""):
        new_block.append("")
    next_lines = lines[:start] + new_block + lines[end:]
    next_text = "\n".join(next_lines) + "\n"
    current_text = path_obj.read_text(encoding="utf-8")
    if next_text == current_text:
        return False
    path_obj.write_text(next_text, encoding="utf-8")
    return True


def projection_plan(item: dict[str, Any], generated_at_utc: str | None = None) -> dict[str, Any]:
    projection_id = item.get("id") if isinstance(item.get("id"), str) else "unknown"
    report_paths = list_strings(item.get("derivation_reports"))
    source_entries = source_material_entries(list_dicts(item.get("source_material")))
    rule_paths = list_strings(item.get("expected_rule_paths"))
    rule_statuses = []
    for rule_path in rule_paths:
        status = rule_projection_status(rule_path, source_entries, report_paths)
        if generated_at_utc is not None:
            status["apply_provenance"] = applied_provenance(source_entries, report_paths, generated_at_utc)
        rule_statuses.append(status)
    derivation_reports = [report_status(path) for path in report_paths]
    actions = sorted({status["action"] for status in rule_statuses if status["action"] != "current"})
    if not actions:
        actions = ["none"]
    mechanically_current = actions == ["none"] and all(report["exists"] for report in derivation_reports)
    semantic_review = "needs-review" if any(report["status"] == "needs-review" for report in derivation_reports) else "current"
    return {
        "id": projection_id,
        "status": item.get("status"),
        "projection_mode": item.get("projection_mode"),
        "target": item.get("target") if isinstance(item.get("target"), dict) else {},
        "source_material": source_entries,
        "derivation_reports": derivation_reports,
        "expected_rule_paths": rule_statuses,
        "corpus_gap_paths": list_strings(item.get("corpus_gap_paths")),
        "expected_selector_evaluations": list_strings(item.get("expected_selector_evaluations")),
        "required_checks": list_strings(item.get("required_checks")),
        "provenance_template": (
            applied_provenance(source_entries, report_paths, generated_at_utc)
            if generated_at_utc is not None
            else provenance_template(source_entries, report_paths)
        ),
        "mechanically_current": mechanically_current,
        "semantic_review": semantic_review,
        "actions": actions,
    }


def apply_provenance_updates(projection_sets: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    writes: list[dict[str, Any]] = []
    errors: list[str] = []
    for projection in projection_sets:
        for rule in projection["expected_rule_paths"]:
            action = rule.get("action")
            rule_path = rule.get("path")
            if action == "current":
                continue
            if action != "refresh-source-derivation":
                errors.append(
                    f"{rule_path} requires {action}; apply-provenance can only refresh existing source_derivation blocks"
                )
                continue
            provenance = rule.get("apply_provenance")
            if not isinstance(rule_path, str) or not isinstance(provenance, dict):
                errors.append(f"{projection['id']} has invalid apply data for {rule_path}")
                continue
            try:
                changed = replace_existing_source_derivation(rule_path, provenance)
            except Exception as exc:
                errors.append(str(exc))
                continue
            writes.append(
                {
                    "path": rule_path,
                    "changed": changed,
                    "projection_id": projection["id"],
                    "action": "refreshed-source-derivation" if changed else "already-current",
                }
            )
    return writes, errors


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    manifest_path = args.manifest
    generated_at_utc = applied_generated_at(args) if args.apply_provenance else None

    try:
        manifest = load_yaml(manifest_path)
    except Exception as exc:
        print(f"ERROR: failed to load projection manifest: {exc}", file=sys.stderr)
        return 2

    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append(f"{manifest_path}.schema must be {MANIFEST_SCHEMA}")

    projection_check = run_source_projection_check(manifest_path)
    if not args.apply_provenance and not projection_check.get("ok"):
        errors.extend(str(error) for error in projection_check.get("errors") or [])

    projection_sets = [
        projection_plan(item, generated_at_utc)
        for item in list_dicts(manifest.get("projection_sets"))
        if item.get("status") == "active"
    ]

    writes: list[dict[str, Any]] = []
    post_apply_projection_check: dict[str, Any] | None = None
    if args.apply_provenance:
        writes, apply_errors = apply_provenance_updates(projection_sets)
        errors.extend(apply_errors)
        post_apply_projection_check = run_source_projection_check(manifest_path)
        if not post_apply_projection_check.get("ok"):
            errors.extend(str(error) for error in post_apply_projection_check.get("errors") or [])
        projection_sets = [
            projection_plan(item)
            for item in list_dicts(manifest.get("projection_sets"))
            if item.get("status") == "active"
        ]

    stale_sets = [
        item["id"]
        for item in projection_sets
        if not item["mechanically_current"]
    ]
    ok = not errors and not stale_sets

    report = {
        "schema": REPORT_SCHEMA,
        "ok": ok,
        "mode": "apply-provenance" if args.apply_provenance else ("check" if args.check else "plan"),
        "manifest_path": manifest_path,
        "manifest_id": manifest.get("manifest_id"),
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "source_projection_check": {
            "ok": bool(projection_check.get("ok")),
            "error_count": len(projection_check.get("errors") or []),
        },
        "post_apply_source_projection_check": (
            {
                "ok": bool(post_apply_projection_check.get("ok")),
                "error_count": len(post_apply_projection_check.get("errors") or []),
            }
            if post_apply_projection_check is not None
            else None
        ),
        "counts": {
            "projection_sets": len(projection_sets),
            "mechanically_current": sum(1 for item in projection_sets if item["mechanically_current"]),
            "stale_or_incomplete": len(stale_sets),
            "writes": len(writes),
            "errors": len(errors),
        },
        "projection_sets": projection_sets,
        "writes": writes,
        "stale_or_incomplete_projection_sets": stale_sets,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not ok:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for projection_id in stale_sets:
            print(f"ERROR: projection set is stale or incomplete: {projection_id}", file=sys.stderr)
    else:
        if args.apply_provenance:
            changed_count = sum(1 for item in writes if item["changed"])
            print(
                "Derived rule provenance applied: "
                f"{changed_count} file(s) changed, {len(writes) - changed_count} already current."
            )
        else:
            print(
                "Derived rule projection plan current: "
                f"{len(projection_sets)} projection set(s), "
                f"{sum(len(item['expected_rule_paths']) for item in projection_sets)} rule output(s)."
            )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
