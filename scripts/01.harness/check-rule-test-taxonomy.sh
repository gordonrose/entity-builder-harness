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

python3 - <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

import yaml


CI_QUALITY_PATH = Path("docs/harness/architecture/rules/concerns/ci-quality.yml")
LAYER_PATHS = [
    Path("docs/harness/architecture/rules/layers/apps.yml"),
    Path("docs/harness/architecture/rules/layers/packages-core.yml"),
    Path("docs/harness/architecture/rules/layers/platform.yml"),
    Path("docs/harness/architecture/rules/layers/tools.yml"),
    Path("docs/harness/architecture/rules/layers/infra.yml"),
    Path("docs/harness/architecture/rules/layers/design-system.yml"),
    Path("docs/harness/architecture/rules/layers/frontend-kit.yml"),
]
VALID_ROLES = {"primary", "secondary", "conditional"}


def load_yaml(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def as_non_empty_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def main() -> int:
    failures: list[str] = []

    ci_quality = load_yaml(CI_QUALITY_PATH)
    if not isinstance(ci_quality, dict):
        failures.append(f"{CI_QUALITY_PATH}: expected YAML mapping")
        ci_quality = {}

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

    for path in LAYER_PATHS:
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

            categories = row.get("categories")
            if not isinstance(categories, list) or not categories:
                failures.append(f"{prefix}: missing non-empty categories list")
                continue

            for category_index, category in enumerate(categories, start=1):
                category_prefix = f"{prefix}.categories[{category_index}]"
                if not isinstance(category, dict):
                    failures.append(f"{category_prefix}: expected mapping")
                    continue

                category_id = category.get("id")
                if category_id not in test_categories:
                    failures.append(f"{category_prefix}: unknown id {category_id!r}")

                if not as_non_empty_list(category.get("should_prove")):
                    failures.append(f"{category_prefix}: missing non-empty should_prove list")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        print(f"Rule test taxonomy check failed: {len(failures)} issue(s).", file=sys.stderr)
        return 1

    print(f"Rule test taxonomy check passed for {len(LAYER_PATHS)} layer file(s).")
    return 0


raise SystemExit(main())
PY
