#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.core-server-dependency-boundary
#   version: 1
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Derive a safe dependency-boundary report for the fixed Kanbien core server runnable program.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.core-server-dependency-boundary
#     path: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPORT_SCHEMA = "deploy/core-server-dependency-report/v1"
PROGRAM_ID = "kanbien-core-server"
ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = ROOT / "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml"
SOURCE_ENTRYPOINT = Path("infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.ts")
COMPILED_ENTRYPOINT = Path("infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.js")

PACKAGE_ROOTS = {
    "@kanbien/core": (Path("packages/core"), "core"),
    "@kanbien/platform-config": (Path("platform/config"), "platform-config"),
    "@kanbien/platform-contracts": (Path("platform/contracts"), "platform-contracts"),
    "@kanbien/platform-health": (Path("platform/health"), "platform-health"),
    "@kanbien/platform-observability": (Path("platform/observability"), "platform-observability"),
    "@kanbien/platform-runtime": (Path("platform/runtime"), "platform-runtime"),
    "@kanbien/platform-security": (Path("platform/security"), "platform-security"),
    "@kanbien/platform-server": (Path("platform/server"), "platform-server"),
}

FORBIDDEN_PACKAGE_PREFIXES = (
    "@kanbien/app-platform-smoke",
    "@kanbien/product-kanbien-platform",
    "@kanbien/platform-persistence",
    "@kanbien/platform-workers",
    "@kanbien/platform-adapter-aws-",
)
FORBIDDEN_SOURCE_SEGMENTS = (
    "kanbien-platform-server.main.ts",
    "kanbien-platform-worker.main.ts",
    "kanbien-platform-relay.main.ts",
    "postgresql",
)
IMPORT_RE = re.compile(r"(?:from\s+|import\s+)[\"']([^\"']+)[\"']")
REQUIRE_RE = re.compile(r"require\([\"']([^\"']+)[\"']\)")


class BoundaryFailure(Exception):
    def __init__(self, *codes: str) -> None:
        self.codes = tuple(dict.fromkeys(codes))
        super().__init__(", ".join(self.codes))


@dataclass(frozen=True)
class BoundaryFacts:
    package_ids: tuple[str, ...]
    package_names: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--build-output", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args, unknown = parser.parse_known_args()
    if args.help:
        print("Usage: script.py --build-output <directory> [--json]")
        raise SystemExit(0)
    if unknown:
        raise BoundaryFailure("arguments-invalid")
    return args


def safe_report(verdict: str, codes: tuple[str, ...], facts: BoundaryFacts | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "program_id": PROGRAM_ID,
        "scope": "dependency-boundary",
        "verdict": verdict,
        "findings": [{"code": code} for code in codes],
    }
    if facts is not None:
        result["observed_dependencies"] = list(facts.package_ids)
        result["observed_dependency_packages"] = list(facts.package_names)
        result["inputs"] = ["typescript-imports", "package-manifests", "lockfile", "build-output"]
    return result


def package_for_specifier(specifier: str) -> tuple[str, Path, str] | None:
    for package_name, (package_path, package_id) in PACKAGE_ROOTS.items():
        if specifier == package_name or specifier.startswith(f"{package_name}/"):
            return package_name, package_path, package_id
    return None


def source_file_for_specifier(source: Path, specifier: str) -> Path | None:
    if specifier.startswith("."):
        base = (source.parent / specifier).resolve()
        options = (base, base.with_suffix(".ts"), base / "index.ts")
        return next((candidate for candidate in options if candidate.is_file()), None)

    package = package_for_specifier(specifier)
    if package is None:
        return None
    package_name, package_path, _ = package
    remainder = specifier.removeprefix(package_name).lstrip("/")
    base = ROOT / package_path / "src"
    if not remainder:
        return base / "index.ts"
    if package_name == "@kanbien/platform-server" and remainder == "main":
        return base / "main.ts"
    return base / remainder / "index.ts"


def import_specifiers(source: Path) -> tuple[str, ...]:
    try:
        text = source.read_text(encoding="utf-8")
    except OSError:
        raise BoundaryFailure("typescript-source-unreadable") from None
    return tuple(match.group(1) for match in IMPORT_RE.finditer(text))


def discover_typescript_graph() -> BoundaryFacts:
    entrypoint = ROOT / SOURCE_ENTRYPOINT
    if not entrypoint.is_file():
        raise BoundaryFailure("source-entrypoint-missing")

    pending = [entrypoint]
    visited: set[Path] = set()
    package_names: set[str] = set()
    forbidden = False
    while pending:
        source = pending.pop()
        if source in visited:
            continue
        visited.add(source)
        relative_source = source.relative_to(ROOT).as_posix()
        if any(segment in relative_source for segment in FORBIDDEN_SOURCE_SEGMENTS):
            forbidden = True

        for specifier in import_specifiers(source):
            if specifier.startswith(FORBIDDEN_PACKAGE_PREFIXES):
                forbidden = True
            package = package_for_specifier(specifier)
            if package is not None:
                package_names.add(package[0])
            resolved = source_file_for_specifier(source, specifier)
            if specifier.startswith((".", "@kanbien/")) and resolved is None:
                raise BoundaryFailure("typescript-import-unresolved")
            if resolved is not None:
                pending.append(resolved)

    if forbidden:
        raise BoundaryFailure("forbidden-dependency-observed")

    manifest_names = discover_manifest_dependencies(package_names)
    all_package_names = package_names | manifest_names
    package_ids = {PACKAGE_ROOTS[name][1] for name in all_package_names}
    ensure_lockfile_records(all_package_names)
    return BoundaryFacts(
        package_ids=tuple(sorted(package_ids)),
        package_names=tuple(sorted(all_package_names)),
    )


def discover_manifest_dependencies(initial_package_names: set[str]) -> set[str]:
    discovered: set[str] = set()
    pending = list(initial_package_names)
    while pending:
        package_name = pending.pop()
        if package_name in discovered:
            continue
        discovered.add(package_name)
        package_path = ROOT / PACKAGE_ROOTS[package_name][0] / "package.json"
        try:
            document = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise BoundaryFailure("package-manifest-unreadable") from None
        dependencies = document.get("dependencies", {})
        if not isinstance(dependencies, dict):
            raise BoundaryFailure("package-manifest-invalid")
        for dependency in dependencies:
            if dependency.startswith(FORBIDDEN_PACKAGE_PREFIXES):
                raise BoundaryFailure("forbidden-dependency-observed")
            if dependency in PACKAGE_ROOTS and dependency not in discovered:
                pending.append(dependency)
    return discovered


def ensure_lockfile_records(package_names: set[str]) -> None:
    try:
        lockfile = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
        records = lockfile["packages"]
    except (OSError, json.JSONDecodeError, KeyError):
        raise BoundaryFailure("lockfile-unreadable") from None
    if not isinstance(records, dict):
        raise BoundaryFailure("lockfile-invalid")
    for package_name in package_names:
        package_path = PACKAGE_ROOTS[package_name][0].as_posix()
        record = records.get(package_path)
        if not isinstance(record, dict) or record.get("name") != package_name:
            raise BoundaryFailure("lockfile-workspace-missing")


def ensure_build_output(build_output: Path) -> None:
    entrypoint = build_output / COMPILED_ENTRYPOINT
    if not entrypoint.is_file():
        raise BoundaryFailure("build-output-entrypoint-missing")
    try:
        compiled_sources = "\n".join(path.read_text(encoding="utf-8") for path in sorted(build_output.rglob("*.js")))
    except OSError:
        raise BoundaryFailure("build-output-unreadable") from None
    imported = set(REQUIRE_RE.findall(compiled_sources))
    if any(specifier.startswith(FORBIDDEN_PACKAGE_PREFIXES) for specifier in imported):
        raise BoundaryFailure("build-output-forbidden-dependency")


def contract_dependencies() -> tuple[set[str], set[str]]:
    try:
        document = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        raise BoundaryFailure("program-contract-unreadable") from None
    if not isinstance(document, dict):
        raise BoundaryFailure("program-contract-invalid")
    programs = document.get("runnable_programs")
    if not isinstance(programs, list):
        raise BoundaryFailure("program-contract-invalid")
    program = next((item for item in programs if isinstance(item, dict) and item.get("id") == PROGRAM_ID), None)
    if program is None:
        raise BoundaryFailure("program-record-missing")
    approved = program.get("approved_dependencies")
    observed = program.get("observed_dependencies")
    if not isinstance(approved, list) or not isinstance(observed, list) or not all(isinstance(item, str) for item in approved + observed):
        raise BoundaryFailure("program-contract-invalid")
    return set(approved), set(observed)


def validate(build_output: Path) -> BoundaryFacts:
    facts = discover_typescript_graph()
    approved, declared_observed = contract_dependencies()
    actual = set(facts.package_ids)
    if not actual.issubset(approved):
        raise BoundaryFailure("dependency-unapproved")
    if actual != declared_observed:
        raise BoundaryFailure("declared-observed-dependencies-mismatch")
    ensure_build_output(build_output)
    return facts


def main() -> int:
    try:
        args = parse_args()
        facts = validate(Path(args.build_output))
        print(json.dumps(safe_report("passed", (), facts), sort_keys=True))
        return 0
    except BoundaryFailure as failure:
        print(json.dumps(safe_report("failed", failure.codes), sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
