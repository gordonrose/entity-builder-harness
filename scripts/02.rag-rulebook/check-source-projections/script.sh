#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-source-projections
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Verify source-material projection mappings to derived rules, reports, gaps, and selector proof.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.source-projections.v1
#       path: .agentic/02.rag-rulebook/source-projections/v1.yml
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh
#     - id: rag-rulebook.script.check-source-projections.readme
#       path: scripts/02.rag-rulebook/check-source-projections/README.md

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
    print("ERROR: python3 yaml module is required for source projection checks.", file=sys.stderr)
    sys.exit(2)


REPORT_SCHEMA = "rag-rulebook/source-projection-check-report/v1"
MANIFEST_SCHEMA = "rag-rulebook/source-projection-manifest/v1"
DEFAULT_MANIFEST = ".agentic/02.rag-rulebook/source-projections/v1.yml"
SOURCE_ROOTS = [
    "docs/02.rag-rulebook/source-material",
    "docs/04.deploy/source-material",
]
RULE_ROOTS = [
    "docs/02.rag-rulebook/rules",
    "docs/04.deploy/rules",
]
DERIVATION_REPORT_ROOT = ".agentic/02.rag-rulebook/derivation-reports"
RETIREMENT_RECORD_ROOT = ".agentic/02.rag-rulebook/retirements"
ALLOWED_SET_STATUSES = {"active", "planned", "retired"}
ALLOWED_PROJECTION_MODES = {"manual-reviewed", "generated", "planned"}


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
  check-source-projections/script.sh --current [--json]
  check-source-projections/script.sh --current --manifest <path> [--json]

Checks the source projection manifest against current governed source material,
derived rule YAML, derivation reports, corpus gaps, and selector evaluation
proof paths. The command is read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
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


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_under(path: str, roots: list[str]) -> bool:
    return any(path == root or path.startswith(f"{root}/") for root in roots)


def is_source_material_path(path: str) -> bool:
    return (
        is_under(path, SOURCE_ROOTS)
        and path.endswith(".md")
        and Path(path).name != "README.md"
    )


def is_rule_path(path: str) -> bool:
    return is_under(path, RULE_ROOTS) and path.endswith((".yml", ".yaml"))


def list_files(roots: list[str], suffixes: set[str]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        root_path = repo_path(root)
        if not root_path.exists():
            continue
        for path in root_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes:
                files.append(path)
    return sorted(set(files))


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with repo_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml(path: str | Path, errors: list[str]) -> dict[str, Any] | None:
    path_obj = repo_path(path)
    try:
        data = yaml.safe_load(path_obj.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        errors.append(f"{rel(path_obj)} failed to parse as YAML: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{rel(path_obj)} must contain a YAML object")
        return None
    return data


def list_strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def list_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def current_source_material_files() -> set[str]:
    return {
        rel(path)
        for path in list_files(SOURCE_ROOTS, {".md"})
        if path.name != "README.md"
    }


def current_derived_rule_files(errors: list[str]) -> dict[str, dict[str, Any]]:
    derived: dict[str, dict[str, Any]] = {}
    for path in list_files(RULE_ROOTS, {".yml", ".yaml"}):
        rule_path = rel(path)
        data = load_yaml(rule_path, errors)
        if data is None:
            continue
        if isinstance(data.get("source_derivation"), dict):
            derived[rule_path] = data
    return derived


def validate_manifest_shape(manifest: dict[str, Any], manifest_path: str, errors: list[str]) -> None:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append(f"{manifest_path}.schema must be {MANIFEST_SCHEMA}")
    for field in ["manifest_id", "status"]:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{manifest_path}.{field} must be a non-empty string")
    if manifest.get("status") not in {"active", "retired"}:
        errors.append(f"{manifest_path}.status must be active or retired")
    projection_sets = manifest.get("projection_sets")
    if not isinstance(projection_sets, list) or not projection_sets:
        errors.append(f"{manifest_path}.projection_sets must be a non-empty array")


def report_paths_for(report: dict[str, Any]) -> tuple[set[str], set[str]]:
    source_change = report.get("source_change") if isinstance(report.get("source_change"), dict) else {}
    semantic_review = report.get("semantic_review") if isinstance(report.get("semantic_review"), dict) else {}
    target = report.get("target") if isinstance(report.get("target"), dict) else {}
    proposed = report.get("proposed_updates") if isinstance(report.get("proposed_updates"), dict) else {}

    source_paths = {
        path
        for path in list_strings(source_change.get("changed_paths"))
        if is_source_material_path(path)
    }
    for claim in list_dicts(semantic_review.get("source_claims")):
        path = claim.get("evidence_path")
        if isinstance(path, str) and is_source_material_path(path):
            source_paths.add(path)

    rule_paths: set[str] = set()
    for field in ["expected_rule_paths", "affected_rule_paths"]:
        for path in list_strings(target.get(field)):
            if is_rule_path(path):
                rule_paths.add(path)
    for path in list_strings(proposed.get("rules")):
        if is_rule_path(path):
            rule_paths.add(path)
    return source_paths, rule_paths


def load_accepted_retirements(errors: list[str]) -> dict[str, list[str]]:
    retired_by_path: dict[str, list[str]] = {}
    for path in list_files([RETIREMENT_RECORD_ROOT], {".yml", ".yaml"}):
        record_path = rel(path)
        data = load_yaml(record_path, errors)
        if data is None:
            continue
        if data.get("schema") != "rag-rulebook/retirement-record/v1":
            errors.append(f"{record_path}.schema must be rag-rulebook/retirement-record/v1")
            continue
        if data.get("status") != "accepted":
            continue
        retirement_id = data.get("retirement_id")
        if not isinstance(retirement_id, str) or not retirement_id.strip():
            errors.append(f"{record_path}.retirement_id must be a non-empty string")
            retirement_id = record_path
        retired_artifacts = data.get("retired_artifacts")
        if not isinstance(retired_artifacts, list):
            errors.append(f"{record_path}.retired_artifacts must be an array")
            continue
        for index, artifact in enumerate(retired_artifacts, start=1):
            owner = f"{record_path}.retired_artifacts[{index}]"
            if not isinstance(artifact, dict):
                errors.append(f"{owner} must be an object")
                continue
            retired_path = artifact.get("path")
            if not isinstance(retired_path, str) or not retired_path.strip():
                errors.append(f"{owner}.path must be a non-empty string")
                continue
            retired_by_path.setdefault(retired_path, []).append(retirement_id)
    return {path: sorted(set(record_ids)) for path, record_ids in retired_by_path.items()}


def lifecycle_paths_for(item: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "source_material": item["source_paths"],
        "expected_rule_paths": item["rule_paths"],
        "derivation_reports": item["report_paths"],
        "corpus_gap_paths": item["corpus_gap_paths"],
        "expected_selector_evaluations": item["expected_selector_evaluations"],
    }


def validate_projection_set(
    item: dict[str, Any],
    index: int,
    errors: list[str],
) -> dict[str, Any]:
    owner = f"projection_sets[{index}]"
    set_id = item.get("id")
    status = item.get("status")
    mode = item.get("projection_mode")
    if not isinstance(set_id, str) or not set_id.strip():
        errors.append(f"{owner}.id must be a non-empty string")
        set_id = f"invalid.{index}"
    if status not in ALLOWED_SET_STATUSES:
        errors.append(f"{set_id}.status must be one of {sorted(ALLOWED_SET_STATUSES)}")
    if mode not in ALLOWED_PROJECTION_MODES:
        errors.append(f"{set_id}.projection_mode must be one of {sorted(ALLOWED_PROJECTION_MODES)}")

    target = item.get("target")
    if not isinstance(target, dict):
        errors.append(f"{set_id}.target must be an object")
        target = {}
    for field in ["corpus_id", "owner_layer"]:
        value = target.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{set_id}.target.{field} must be a non-empty string")

    source_material = list_dicts(item.get("source_material"))
    if not source_material:
        errors.append(f"{set_id}.source_material must be a non-empty array")
    source_paths: list[str] = []
    for source_index, source in enumerate(source_material, start=1):
        source_owner = f"{set_id}.source_material[{source_index}]"
        path = source.get("path")
        role = source.get("role")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{source_owner}.path must be a non-empty string")
            continue
        if not is_source_material_path(path):
            errors.append(f"{source_owner}.path is not under a governed source-material root: {path}")
        elif status == "active" and not repo_path(path).is_file():
            errors.append(f"{source_owner}.path does not exist: {path}")
        source_paths.append(path)
        if not isinstance(role, str) or not role.strip():
            errors.append(f"{source_owner}.role must be a non-empty string")

    rule_paths = list_strings(item.get("expected_rule_paths"))
    if status == "active" and not rule_paths:
        errors.append(f"{set_id}.expected_rule_paths must be non-empty for active projections")
    for path in rule_paths:
        if not is_rule_path(path):
            errors.append(f"{set_id}.expected_rule_paths contains non-rule path: {path}")
        elif status == "active" and not repo_path(path).is_file():
            errors.append(f"{set_id}.expected_rule_paths does not exist: {path}")

    report_paths = list_strings(item.get("derivation_reports"))
    if status == "active" and not report_paths:
        errors.append(f"{set_id}.derivation_reports must be non-empty for active projections")
    for path in report_paths:
        if not path.startswith(f"{DERIVATION_REPORT_ROOT}/") or not path.endswith((".yml", ".yaml")):
            errors.append(f"{set_id}.derivation_reports contains invalid report path: {path}")
        elif status == "active" and not repo_path(path).is_file():
            errors.append(f"{set_id}.derivation_reports does not exist: {path}")

    for field in ["corpus_gap_paths", "expected_selector_evaluations"]:
        for path in list_strings(item.get(field)):
            if status == "active" and not repo_path(path).is_file():
                errors.append(f"{set_id}.{field} does not exist: {path}")

    return {
        "id": set_id,
        "status": status,
        "projection_mode": mode,
        "source_paths": sorted(set(source_paths)),
        "rule_paths": sorted(set(rule_paths)),
        "report_paths": sorted(set(report_paths)),
        "corpus_gap_paths": sorted(set(list_strings(item.get("corpus_gap_paths")))),
        "expected_selector_evaluations": sorted(set(list_strings(item.get("expected_selector_evaluations")))),
    }


def validate_retirement_alignment(
    normalized_sets: list[dict[str, Any]],
    accepted_retirements: dict[str, list[str]],
    errors: list[str],
) -> None:
    for item in normalized_sets:
        set_id = item["id"]
        status = item["status"]
        for field, paths in lifecycle_paths_for(item).items():
            for path in paths:
                is_retired = path in accepted_retirements
                if status == "retired" and not is_retired:
                    errors.append(
                        f"{set_id} is retired but {field} lacks accepted retirement record: {path}"
                    )
                if status == "active" and is_retired:
                    records = ", ".join(accepted_retirements[path])
                    errors.append(
                        f"{set_id} is active but {field} references retired artifact "
                        f"{path} recorded by {records}"
                    )


def validate_rule_projection(
    set_id: str,
    rule_path: str,
    source_paths: set[str],
    report_paths: set[str],
    derived_rules: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    data = derived_rules.get(rule_path)
    if data is None:
        errors.append(f"{set_id} expected rule lacks source_derivation or does not exist: {rule_path}")
        return
    derivation = data.get("source_derivation")
    if not isinstance(derivation, dict):
        errors.append(f"{rule_path}.source_derivation must be an object")
        return

    report = derivation.get("derivation_report")
    if not isinstance(report, str) or not report.strip():
        errors.append(f"{rule_path}.source_derivation.derivation_report must be a non-empty string")
    elif report_paths and report not in report_paths:
        errors.append(f"{rule_path}.source_derivation.derivation_report is not declared in {set_id}: {report}")

    material = derivation.get("source_material")
    if not isinstance(material, list) or not material:
        errors.append(f"{rule_path}.source_derivation.source_material must be a non-empty array")
        return
    material_by_path: dict[str, dict[str, Any]] = {}
    for material_index, material_item in enumerate(material, start=1):
        owner = f"{rule_path}.source_derivation.source_material[{material_index}]"
        if not isinstance(material_item, dict):
            errors.append(f"{owner} must be an object")
            continue
        path = material_item.get("path")
        sha256 = material_item.get("sha256")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{owner}.path must be a non-empty string")
            continue
        if path not in source_paths:
            errors.append(f"{owner}.path is not declared by {set_id}: {path}")
            continue
        if not repo_path(path).is_file():
            errors.append(f"{owner}.path does not exist: {path}")
            continue
        if not isinstance(sha256, str) or len(sha256) != 64:
            errors.append(f"{owner}.sha256 must be a 64-character SHA-256 hex string")
            continue
        current_sha = file_sha256(path)
        if sha256 != current_sha:
            errors.append(
                f"{rule_path}.source_derivation.source_material hash is stale for {path}: "
                f"expected {sha256}, current {current_sha}"
            )
        material_by_path[path] = material_item

    for path in sorted(source_paths):
        if path not in material_by_path:
            errors.append(f"{rule_path}.source_derivation.source_material missing projection source: {path}")


def validate_report_projection(
    set_id: str,
    report_path: str,
    source_paths: set[str],
    rule_paths: set[str],
    errors: list[str],
) -> None:
    report = load_yaml(report_path, errors)
    if report is None:
        return
    if report.get("schema") != "rag-rulebook/source-to-rule-derivation-report/v1":
        errors.append(f"{report_path}.schema must be rag-rulebook/source-to-rule-derivation-report/v1")
    report_sources, report_rules = report_paths_for(report)
    for path in sorted(source_paths):
        if path not in report_sources:
            errors.append(f"{report_path} does not mention projection source from {set_id}: {path}")
    for path in sorted(rule_paths):
        if path not in report_rules:
            errors.append(f"{report_path} does not mention expected rule from {set_id}: {path}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = args.manifest
    manifest = load_yaml(manifest_path, errors)
    if manifest is None:
        report = {
            "schema": REPORT_SCHEMA,
            "ok": False,
            "manifest_path": manifest_path,
            "errors": errors,
            "warnings": warnings,
        }
        print(json.dumps(report, indent=2, sort_keys=True) if args.json else "\n".join(errors))
        return 1

    validate_manifest_shape(manifest, manifest_path, errors)
    projection_sets_raw = list_dicts(manifest.get("projection_sets"))
    normalized_sets = [
        validate_projection_set(item, index, errors)
        for index, item in enumerate(projection_sets_raw, start=1)
    ]
    accepted_retirements = load_accepted_retirements(errors)
    validate_retirement_alignment(normalized_sets, accepted_retirements, errors)

    ids = [item["id"] for item in normalized_sets]
    for set_id in sorted({item for item in ids if ids.count(item) > 1}):
        errors.append(f"duplicate projection set id: {set_id}")

    active_sets = [item for item in normalized_sets if item["status"] == "active"]
    declaration_sets = [
        item
        for item in normalized_sets
        if item["status"] in {"active", "planned"}
    ]
    declared_sources = {path for item in declaration_sets for path in item["source_paths"]}
    declared_rules = {path for item in active_sets for path in item["rule_paths"]}

    current_sources = current_source_material_files()
    undeclared_sources = sorted(current_sources - declared_sources)
    for path in undeclared_sources:
        errors.append(f"source material is not declared in active projection manifest: {path}")

    missing_sources = sorted(declared_sources - current_sources)
    for path in missing_sources:
        errors.append(f"projection manifest declares missing source material: {path}")

    derived_rules = current_derived_rule_files(errors)
    undeclared_derived_rules = sorted(set(derived_rules) - declared_rules)
    for path in undeclared_derived_rules:
        errors.append(f"derived rule with source_derivation is not declared in active projection manifest: {path}")

    for item in active_sets:
        source_paths = set(item["source_paths"])
        rule_paths = set(item["rule_paths"])
        report_paths = set(item["report_paths"])
        for rule_path in sorted(rule_paths):
            validate_rule_projection(item["id"], rule_path, source_paths, report_paths, derived_rules, errors)
        for report_path in sorted(report_paths):
            validate_report_projection(item["id"], report_path, source_paths, rule_paths, errors)

    report = {
        "schema": REPORT_SCHEMA,
        "ok": not errors,
        "manifest_path": manifest_path,
        "counts": {
            "projection_sets": len(normalized_sets),
            "active_projection_sets": len(active_sets),
            "accepted_retirement_paths": len(accepted_retirements),
            "current_source_material_files": len(current_sources),
            "declared_source_material_files": len(declared_sources),
            "derived_rules": len(derived_rules),
            "declared_rule_paths": len(declared_rules),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "projection_sets": normalized_sets,
        "accepted_retirements": accepted_retirements,
        "undeclared_source_material_files": undeclared_sources,
        "undeclared_derived_rules": undeclared_derived_rules,
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
        print(
            "Source projections valid: "
            f"{len(active_sets)} active projection set(s), "
            f"{len(declared_sources)} source file(s), "
            f"{len(declared_rules)} rule projection(s)."
        )
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
