#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Verify architecture rulebook layer test taxonomy structure and vocabulary references.
#   domain: architecture-rulebook
#   portability: llm-workbench-required
#   used_by:
#     - docs/harness/architecture/rules/concerns/ci-quality.yml
#     - .agentic/01.harness/README.md
#   effects: read-only

python3 - "$@" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml


CI_QUALITY_PATH = Path("docs/harness/architecture/rules/concerns/ci-quality.yml")
VALID_ROLES = {"primary", "secondary", "conditional"}
GENERIC_EVIDENCE = {
    "test important behavior",
    "test important cases",
    "cover the main path",
    "cover edge cases",
    "validate behavior",
    "ensure it works",
}


def load_yaml(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def as_non_empty_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def list_text(value: object) -> str:
    if not isinstance(value, list):
        return ""
    return " ".join(item for item in value if isinstance(item, str)).lower()


def has_any(text: str, needles: object) -> bool:
    return isinstance(needles, list) and any(
        isinstance(needle, str) and needle.lower() in text for needle in needles
    )


def validate(ci_quality: dict, layer_paths: list[Path]) -> list[str]:
    failures: list[str] = []

    test_types = {
        item.get("id")
        for item in ci_quality.get("test_types", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    test_categories = {
        item.get("id")
        for item in ci_quality.get("test_categories", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    if not test_types:
        failures.append(f"{CI_QUALITY_PATH}: missing test_types vocabulary")
    if not test_categories:
        failures.append(f"{CI_QUALITY_PATH}: missing test_categories vocabulary")

    role_semantics = {
        item.get("id")
        for item in ci_quality.get("test_role_semantics", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if VALID_ROLES - role_semantics:
        failures.append(f"{CI_QUALITY_PATH}: test_role_semantics must define {sorted(VALID_ROLES)}")

    category_requirements = {
        item.get("id"): item.get("must_name_negative_evidence")
        for item in ci_quality.get("category_evidence_requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for category_id in category_requirements:
        if category_id not in test_categories:
            failures.append(f"{CI_QUALITY_PATH}: category_evidence_requirements references unknown category {category_id!r}")

    substitute_limits = {
        item.get("type"): item
        for item in ci_quality.get("substitute_limits", [])
        if isinstance(item, dict) and isinstance(item.get("type"), str)
    }
    for substitute_type, rule in substitute_limits.items():
        if substitute_type not in test_types:
            failures.append(f"{CI_QUALITY_PATH}: substitute_limits references unknown type {substitute_type!r}")
        for category_id in rule.get("forbidden_as_sole_proof_for_categories", []):
            if category_id not in test_categories:
                failures.append(f"{CI_QUALITY_PATH}: substitute_limits for {substitute_type!r} references unknown category {category_id!r}")

    seen_layer_paths: set[Path] = set()
    for path in layer_paths:
        if path in seen_layer_paths:
            failures.append(f"{CI_QUALITY_PATH}: duplicate layer taxonomy scope path {path}")
            continue
        seen_layer_paths.add(path)
        if not path.exists():
            failures.append(f"{CI_QUALITY_PATH}: scoped layer file does not exist: {path}")
            continue

        layer = load_yaml(path)
        if not isinstance(layer, dict):
            failures.append(f"{path}: expected YAML mapping")
            continue

        taxonomy = layer.get("test_taxonomy")
        if not isinstance(taxonomy, list) or not taxonomy:
            failures.append(f"{path}: missing non-empty test_taxonomy")
            continue

        for index, row in enumerate(taxonomy, start=1):
            prefix = f"{path}: test_taxonomy[{index}]"
            if not isinstance(row, dict):
                failures.append(f"{prefix}: expected mapping")
                continue

            row_type = row.get("type")
            if row_type not in test_types:
                failures.append(f"{prefix}: unknown type {row_type!r}")

            role = row.get("role")
            if role not in VALID_ROLES:
                failures.append(f"{prefix}: invalid role {role!r}")

            if not as_non_empty_list(row.get("minimum_evidence")):
                failures.append(f"{prefix}: missing non-empty minimum_evidence list")

            if not as_non_empty_list(row.get("must_not")):
                failures.append(f"{prefix}: missing non-empty must_not list")

            row_evidence_text = list_text(row.get("minimum_evidence"))
            row_must_not_text = list_text(row.get("must_not"))
            row_text = f"{row_evidence_text} {row_must_not_text}"
            if any(generic in row_text for generic in GENERIC_EVIDENCE):
                failures.append(f"{prefix}: evidence is too generic to guide deterministic QA enforcement")

            categories = row.get("categories")
            if not isinstance(categories, list) or not categories:
                failures.append(f"{prefix}: missing non-empty categories list")
                continue

            row_category_ids: set[str] = set()
            for category_index, category in enumerate(categories, start=1):
                category_prefix = f"{prefix}.categories[{category_index}]"
                if not isinstance(category, dict):
                    failures.append(f"{category_prefix}: expected mapping")
                    continue

                category_id = category.get("id")
                if category_id not in test_categories:
                    failures.append(f"{category_prefix}: unknown id {category_id!r}")
                elif category_id in row_category_ids:
                    failures.append(f"{category_prefix}: duplicate category id {category_id!r}")
                elif isinstance(category_id, str):
                    row_category_ids.add(category_id)

                if not as_non_empty_list(category.get("should_prove")):
                    failures.append(f"{category_prefix}: missing non-empty should_prove list")
                    continue

                category_text = f"{list_text(category.get('should_prove'))} {row_text}"
                required_terms = category_requirements.get(category_id)
                if required_terms and not has_any(category_text, required_terms):
                    failures.append(
                        f"{category_prefix}: {category_id!r} evidence must name at least one required negative case: {required_terms}"
                    )

            substitute_rule = substitute_limits.get(row_type)
            if substitute_rule:
                forbidden_categories = set(substitute_rule.get("forbidden_as_sole_proof_for_categories", []))
                covered_forbidden = sorted(row_category_ids & forbidden_categories)
                if covered_forbidden and not has_any(row_must_not_text, substitute_rule.get("cannot_replace")):
                    failures.append(
                        f"{prefix}: {row_type!r} covers closer-proof categories {covered_forbidden} but must_not does not name closer test types it cannot replace"
                    )

    return failures


def configured_layer_paths(ci_quality: dict) -> list[Path]:
    scope = ci_quality.get("layer_test_taxonomy_scope")
    if not isinstance(scope, dict):
        return []
    paths = scope.get("layer_files")
    if not isinstance(paths, list):
        return []
    return [Path(path) for path in paths if isinstance(path, str)]


def main() -> int:
    ci_quality = load_yaml(CI_QUALITY_PATH)
    if not isinstance(ci_quality, dict):
        print(f"ERROR: {CI_QUALITY_PATH}: expected YAML mapping", file=sys.stderr)
        return 1

    layer_paths = configured_layer_paths(ci_quality)
    if not layer_paths:
        print(f"ERROR: {CI_QUALITY_PATH}: missing layer_test_taxonomy_scope.layer_files", file=sys.stderr)
        return 1

    failures = validate(ci_quality, layer_paths)

    if "--self-test" in sys.argv:
        weak_ci_quality = dict(ci_quality)
        weak_path = layer_paths[0]
        weak_layer = load_yaml(weak_path)
        if isinstance(weak_layer, dict) and isinstance(weak_layer.get("test_taxonomy"), list):
            weak_layer = dict(weak_layer)
            weak_layer["test_taxonomy"] = [
                {
                    "type": "unit",
                    "role": "primary",
                    "minimum_evidence": ["Test important behavior."],
                    "must_not": ["Do not write weak tests."],
                    "categories": [
                        {
                            "id": "validation",
                            "should_prove": ["Ensure it works."],
                        }
                    ],
                }
            ]
            original_load_yaml = globals()["load_yaml"]

            def load_yaml_override(path: Path) -> object:
                if path == weak_path:
                    return weak_layer
                return original_load_yaml(path)

            globals()["load_yaml"] = load_yaml_override
            weak_failures = validate(weak_ci_quality, [weak_path])
            globals()["load_yaml"] = original_load_yaml
            if not weak_failures:
                failures.append("self-test: weak generic taxonomy row was not rejected")
        else:
            failures.append("self-test: could not build weak taxonomy fixture")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        print(f"Rule test taxonomy check failed: {len(failures)} issue(s).", file=sys.stderr)
        return 1

    print(f"Rule test taxonomy check passed for {len(layer_paths)} layer file(s).")
    return 0


raise SystemExit(main())
PY
