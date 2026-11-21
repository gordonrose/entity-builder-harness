#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.core-server-dependency-boundary
#   version: 2
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-11-15"
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
import subprocess
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

BUILD_INPUT_READER = Path(__file__).resolve().parent.parent / "runnable-program-contract/build-inputs.mjs"

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


@dataclass(frozen=True)
class DeclarationBindings:
    package_roots: dict[str, tuple[Path, str]]
    compiler_paths: dict[str, Path]
    external_owners: dict[str, str]
    node_builtins: frozenset[str]


def declaration_bindings() -> DeclarationBindings:
    """Read approved names/exports; never substitute them for observed imports."""
    try:
        result = subprocess.run(
            ["node", str(BUILD_INPUT_READER), "--program", PROGRAM_ID,
             "--contract", CONTRACT_PATH.relative_to(ROOT).as_posix()],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
    except subprocess.TimeoutExpired:
        raise BoundaryFailure("program-build-inputs-timeout") from None
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        raise BoundaryFailure("program-build-inputs-unavailable") from None
    if result.returncode != 0:
        raise BoundaryFailure("program-build-inputs-rejected")
    try:
        value = json.loads(result.stdout)
        if not isinstance(value, dict) or value.get("programId") != PROGRAM_ID:
            raise ValueError()
        inputs, owners = value["inputs"], value["workspaceOwners"]
        if not isinstance(inputs, dict) or not isinstance(owners, dict):
            raise ValueError()
        roots: dict[str, tuple[Path, str]] = {}
        for directory, owner in owners.items():
            if not isinstance(directory, str) or not directory.endswith("/") or not isinstance(owner, str):
                raise ValueError()
            relative = Path(directory)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError()
            manifest = json.loads((ROOT / relative / "package.json").read_text(encoding="utf-8"))
            name = manifest["name"]
            if not isinstance(name, str) or name in roots:
                raise ValueError()
            roots[name] = (relative, owner)
        if not roots or set(inputs["packageNames"]) != set(roots) or not isinstance(inputs["compilerPaths"], dict):
            raise ValueError()
        paths: dict[str, Path] = {}
        for specifier, targets in inputs["compilerPaths"].items():
            if not isinstance(specifier, str) or not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], str):
                raise ValueError()
            target = Path(targets[0])
            if target.is_absolute() or ".." in target.parts:
                raise ValueError()
            paths[specifier] = target
        external, builtins = value["externalOwners"], value["nodeBuiltins"]
        if not isinstance(external, dict) or not all(isinstance(name, str) and isinstance(owner, str) for name, owner in external.items()):
            raise ValueError()
        if not isinstance(builtins, list) or not all(isinstance(name, str) for name in builtins):
            raise ValueError()
        return DeclarationBindings(roots, paths, external, frozenset(builtins))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        raise BoundaryFailure("program-build-inputs-invalid") from None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: parser.exit(2, "DIAGNOSTIC_CODE=DEPENDENCY_BOUNDARY_ARGUMENTS_INVALID\n")
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


def package_for_specifier(specifier: str, bindings: DeclarationBindings) -> tuple[str, Path, str] | None:
    for package_name, (package_path, package_id) in bindings.package_roots.items():
        if specifier == package_name or specifier.startswith(f"{package_name}/"):
            return package_name, package_path, package_id
    return None


def source_file_for_specifier(source: Path, specifier: str, bindings: DeclarationBindings) -> Path | None:
    if specifier.startswith("."):
        base = (source.parent / specifier).resolve()
        options = (base, base.with_suffix(".ts"), base / "index.ts")
        return next((candidate for candidate in options if candidate.is_file()), None)

    target = bindings.compiler_paths.get(specifier)
    return ROOT / target if target is not None else None


def import_specifiers(source: Path) -> tuple[str, ...]:
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise BoundaryFailure("typescript-source-unreadable") from None
    return tuple(match.group(1) for match in IMPORT_RE.finditer(text))


def discover_typescript_graph(bindings: DeclarationBindings) -> BoundaryFacts:
    entrypoint = ROOT / SOURCE_ENTRYPOINT
    if not entrypoint.is_file():
        raise BoundaryFailure("source-entrypoint-missing")

    pending = [entrypoint]
    visited: set[Path] = set()
    package_names: set[str] = set()
    external_ids: set[str] = set()
    forbidden = False
    while pending:
        source = pending.pop()
        if source in visited:
            continue
        visited.add(source)
        try:
            relative_source = source.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            raise BoundaryFailure("typescript-source-outside-repository") from None
        for name, (directory, _) in bindings.package_roots.items():
            if relative_source.startswith(directory.as_posix() + "/"):
                package_names.add(name)
        if any(segment in relative_source for segment in FORBIDDEN_SOURCE_SEGMENTS):
            forbidden = True

        for specifier in import_specifiers(source):
            if specifier.startswith(FORBIDDEN_PACKAGE_PREFIXES):
                forbidden = True
            package = package_for_specifier(specifier, bindings)
            if package is not None:
                package_names.add(package[0])
            resolved = source_file_for_specifier(source, specifier, bindings)
            if resolved is None:
                if package is not None or specifier.startswith("."):
                    raise BoundaryFailure("typescript-import-unresolved")
                builtin = specifier.removeprefix("node:")
                if specifier in bindings.node_builtins or (specifier.startswith("node:") and builtin in bindings.node_builtins):
                    continue
                parts = specifier.split("/")
                name = "/".join(parts[:2]) if specifier.startswith("@") else parts[0]
                if name not in bindings.external_owners:
                    raise BoundaryFailure("dependency-unapproved")
                external_ids.add(bindings.external_owners[name])
            if resolved is not None:
                pending.append(resolved)

    if forbidden:
        raise BoundaryFailure("forbidden-dependency-observed")

    manifest_names = discover_manifest_dependencies(package_names, bindings)
    all_package_names = package_names | manifest_names
    package_ids = {bindings.package_roots[name][1] for name in all_package_names} | external_ids
    ensure_lockfile_records(all_package_names, bindings)
    return BoundaryFacts(
        package_ids=tuple(sorted(package_ids)),
        package_names=tuple(sorted(all_package_names)),
    )


def discover_manifest_dependencies(initial_package_names: set[str], bindings: DeclarationBindings) -> set[str]:
    discovered: set[str] = set()
    pending = list(initial_package_names)
    while pending:
        package_name = pending.pop()
        if package_name in discovered:
            continue
        discovered.add(package_name)
        package_path = ROOT / bindings.package_roots[package_name][0] / "package.json"
        try:
            document = json.loads(package_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise BoundaryFailure("package-manifest-unreadable") from None
        if not isinstance(document, dict):
            raise BoundaryFailure("package-manifest-invalid")
        dependencies = document.get("dependencies", {})
        if not isinstance(dependencies, dict):
            raise BoundaryFailure("package-manifest-invalid")
        for dependency in dependencies:
            if dependency.startswith(FORBIDDEN_PACKAGE_PREFIXES):
                raise BoundaryFailure("forbidden-dependency-observed")
            if dependency in bindings.package_roots and dependency not in discovered:
                pending.append(dependency)
    return discovered


def ensure_lockfile_records(package_names: set[str], bindings: DeclarationBindings) -> None:
    try:
        lockfile = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
        if not isinstance(lockfile, dict):
            raise BoundaryFailure("lockfile-invalid")
        records = lockfile["packages"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError):
        raise BoundaryFailure("lockfile-unreadable") from None
    if not isinstance(records, dict):
        raise BoundaryFailure("lockfile-invalid")
    for package_name in package_names:
        package_path = bindings.package_roots[package_name][0].as_posix()
        record = records.get(package_path)
        if not isinstance(record, dict) or record.get("name") != package_name:
            raise BoundaryFailure("lockfile-workspace-missing")


def ensure_build_output(build_output: Path) -> None:
    entrypoint = build_output / COMPILED_ENTRYPOINT
    if not entrypoint.is_file():
        raise BoundaryFailure("build-output-entrypoint-missing")
    try:
        compiled_sources = "\n".join(path.read_text(encoding="utf-8") for path in sorted(build_output.rglob("*.js")))
    except (OSError, UnicodeError):
        raise BoundaryFailure("build-output-unreadable") from None
    imported = set(REQUIRE_RE.findall(compiled_sources))
    if any(specifier.startswith(FORBIDDEN_PACKAGE_PREFIXES) for specifier in imported):
        raise BoundaryFailure("build-output-forbidden-dependency")


def contract_dependencies() -> tuple[set[str], set[str]]:
    try:
        document = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
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
    facts = discover_typescript_graph(declaration_bindings())
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
