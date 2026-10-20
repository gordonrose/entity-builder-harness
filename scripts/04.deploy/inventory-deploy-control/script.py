#!/usr/bin/env python3
"""Report the current deploy-control surface without changing it."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path("scripts/04.deploy")
INFRA_ROOT = Path("infra/04.deploy")
ROOT_INDEX = SCRIPT_ROOT / "README.md"
ENTRYPOINT_NAMES = {"script.sh", "script.py", "script.mjs"}
SKIPPED_PATH_PARTS = {".git", "node_modules", ".cache", "commitLogs"}
MUTATION_MARKERS = (
    "--execute",
    "cloudformation deploy",
    "create-",
    "update-",
    "delete-",
    "put-",
    "register-task-definition",
)


class InventoryError(Exception):
    """Represent an actionable inability to build the local control inventory."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory deploy scripts and infrastructure without writing files or calling a provider."
    )
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate that the inventory can be built; gaps are reported, not treated as success claims.",
    )
    return parser.parse_args()


def repository_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise InventoryError("run this command inside a Git working tree")
    return Path(result.stdout.strip())


def tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise InventoryError("could not list repository files")
    # `git ls-files` intentionally reports a tracked file that has been
    # removed in the working tree.  A read-only inventory must instead report
    # the actual tree it is asked to inspect; otherwise a safe replacement of
    # an obsolete control makes the inventory itself unusable before commit.
    return [Path(line) for line in result.stdout.splitlines() if line and (root / line).is_file()]


def is_text_candidate(path: Path) -> bool:
    return not any(part in SKIPPED_PATH_PARTS for part in path.parts) and path.suffix.lower() in {
        ".json",
        ".md",
        ".mjs",
        ".py",
        ".sh",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }


def text(root: Path, path: Path) -> str:
    try:
        return (root / path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    except OSError as exc:
        raise InventoryError(f"could not read {path}: {exc}") from exc


def script_effects(content: str) -> list[str]:
    match = re.search(r"^#\s+effects:\s*\n((?:#\s+-\s+[^\n]+\n?)*)", content, re.MULTILINE)
    if match is None:
        return ["not-declared"]
    effects = re.findall(r"^#\s+-\s+([^\n]+)", match.group(1), re.MULTILINE)
    return effects or ["not-declared"]


def potential_mutation(content: str) -> str:
    lower = content.lower()
    return "review-required" if any(marker in lower for marker in MUTATION_MARKERS) else "not-detected"


def package_commands(root: Path) -> dict[str, str]:
    try:
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"could not read package.json scripts: {exc}") from exc
    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        raise InventoryError("package.json scripts must be an object")
    return {name: value for name, value in scripts.items() if isinstance(name, str) and isinstance(value, str)}


def capability_dirs(root: Path) -> list[Path]:
    directory = root / SCRIPT_ROOT
    if not directory.is_dir():
        raise InventoryError(f"missing script root: {SCRIPT_ROOT}")
    return sorted(
        [path for path in directory.iterdir() if path.is_dir() and not path.name.startswith(".") and path.name != "lifecycle"],
        key=lambda path: path.name,
    )


def text_contents(root: Path, all_paths: list[Path]) -> dict[Path, str]:
    """Load eligible repository text once so the census stays fast as it grows."""

    return {path: text(root, path) for path in all_paths if is_text_candidate(path)}


def external_references(contents: dict[Path, str], needle: str, excluded_prefix: Path) -> list[str]:
    references: list[str] = []
    for candidate, body in contents.items():
        if candidate.is_relative_to(excluded_prefix):
            continue
        if needle in body:
            references.append(candidate.as_posix())
    return references


def script_inventory(root: Path, contents: dict[Path, str]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    root_index = text(root, ROOT_INDEX) if (root / ROOT_INDEX).is_file() else ""
    commands = package_commands(root)
    capabilities: list[dict[str, Any]] = []
    gaps: list[dict[str, str]] = []

    for directory in capability_dirs(root):
        name = directory.name
        relative_dir = directory.relative_to(root)
        entrypoints = sorted(
            path.relative_to(root).as_posix()
            for path in directory.iterdir()
            if path.is_file() and path.name in ENTRYPOINT_NAMES
        )
        primary_path = next((Path(path) for path in entrypoints if path.endswith("script.sh")), None)
        if primary_path is None and entrypoints:
            primary_path = Path(entrypoints[0])
        primary_content = text(root, primary_path) if primary_path is not None else ""
        capability_content = "\n".join(text(root, Path(path)) for path in entrypoints)
        directory_prefix = f"{relative_dir.as_posix()}/"
        package_refs = sorted(name for name, command in commands.items() if directory_prefix in command)
        callers = external_references(contents, directory_prefix, relative_dir)
        indexed = f"`{name}/`" in root_index
        has_readme = (directory / "README.md").is_file()
        effects = script_effects(primary_content) if primary_path is not None else ["not-declared"]
        item = {
            "capability": name,
            "path": relative_dir.as_posix(),
            "entrypoints": entrypoints,
            "root_indexed": indexed,
            "has_readme": has_readme,
            "declared_effects": effects,
            "potential_cloud_mutation": potential_mutation(capability_content) if "network" in effects else "not-detected",
            "package_commands": package_refs,
            "external_callers": callers,
        }
        capabilities.append(item)
        if not indexed:
            gaps.append({"kind": "missing-root-index-entry", "path": relative_dir.as_posix()})
        if not has_readme:
            gaps.append({"kind": "missing-capability-readme", "path": relative_dir.as_posix()})
        if not entrypoints:
            gaps.append({"kind": "missing-primary-entrypoint", "path": relative_dir.as_posix()})

    return capabilities, gaps


def infra_role(path: Path) -> str:
    parts = path.parts
    name = path.name
    if name == "target-profile.yml":
        return "target decisions and retained non-secret evidence"
    if name == "deploy-readiness.yml":
        return "readiness status and proof gaps"
    if "cloudformation" in parts:
        return "desired AWS resource configuration"
    if "iam" in parts:
        return "deployment or operational identity policy"
    if "operational-realization" in parts:
        return "candidate execution preflight declaration"
    if "entrypoints" in parts:
        return "target runtime composition"
    if "image" in parts:
        return "package image definition"
    if "drift-detection" in parts:
        return "live-state inspection boundary"
    return "unclassified deploy artifact"


def infra_inventory(root: Path, all_paths: list[Path], contents: dict[Path, str]) -> list[dict[str, Any]]:
    files = sorted(path for path in all_paths if path.is_relative_to(INFRA_ROOT) and (root / path).is_file())
    inventory: list[dict[str, Any]] = []
    for path in files:
        body = contents.get(path, "")
        references = external_references(contents, path.as_posix(), path)
        inventory.append(
            {
                "path": path.as_posix(),
                "role": infra_role(path),
                "lines": len(body.splitlines()),
                "external_references": references,
            }
        )
    return inventory


def report(root: Path) -> dict[str, Any]:
    all_paths = tracked_paths(root)
    contents = text_contents(root, all_paths)
    scripts, gaps = script_inventory(root, contents)
    infra = infra_inventory(root, all_paths, contents)
    profile = next((item for item in infra if item["path"].endswith("target-profile.yml")), None)
    profile_reference_count = len(profile["external_references"]) if profile is not None else 0
    effects = Counter(effect for item in scripts for effect in item["declared_effects"])
    mutation_review = [item["path"] for item in scripts if item["potential_cloud_mutation"] == "review-required"]
    return {
        "schema": "deploy/control-inventory/v1",
        "scope": "repository source only; no provider reads, writes, or execution",
        "summary": {
            "script_capabilities": len(scripts),
            "primary_entrypoints": sum(len(item["entrypoints"]) for item in scripts),
            "infra_files": len(infra),
            "declared_effects": dict(sorted(effects.items())),
            "capabilities_requiring_mutation_review": len(mutation_review),
            "target_profile_external_references": profile_reference_count,
            "gaps": len(gaps),
        },
        "gaps": gaps,
        "scripts": scripts,
        "infra": infra,
    }


def markdown(value: dict[str, Any]) -> str:
    summary = value["summary"]
    lines = [
        "# Deploy Control Inventory",
        "",
        "This is a repository-source census. It makes no provider call, performs no deployment, and does not claim a target is healthy.",
        "",
        "## Summary",
        "",
        f"- Script capabilities: {summary['script_capabilities']}",
        f"- Script entrypoints: {summary['primary_entrypoints']}",
        f"- Infrastructure files: {summary['infra_files']}",
        f"- Capabilities requiring mutation review: {summary['capabilities_requiring_mutation_review']}",
        f"- External references to the target profile: {summary['target_profile_external_references']}",
        f"- Control gaps found: {summary['gaps']}",
        "",
        "## Attention Needed",
        "",
    ]
    if value["gaps"]:
        lines.extend(f"- `{item['kind']}`: `{item['path']}`" for item in value["gaps"])
    else:
        lines.append("- No catalogue gaps detected by this source-only check.")

    lines.extend(["", "## Script Capabilities", "", "| Capability | README | Effects | Mutation review | Package commands |", "| --- | --- | --- | --- | --- |"])
    for item in value["scripts"]:
        commands = ", ".join(f"`{command}`" for command in item["package_commands"]) or "—"
        lines.append(
            "| `{capability}` | {readme} | {effects} | {mutation} | {commands} |".format(
                capability=item["capability"],
                readme="yes" if item["has_readme"] else "**no**",
                effects=", ".join(item["declared_effects"]),
                mutation=item["potential_cloud_mutation"],
                commands=commands,
            )
        )

    lines.extend(["", "## Infrastructure Files", "", "| Path | Current role | Lines | External references |", "| --- | --- | ---: | ---: |"])
    for item in value["infra"]:
        lines.append(
            f"| `{item['path']}` | {item['role']} | {item['lines']} | {len(item['external_references'])} |"
        )
    lines.extend(["", "## Interpretation", "", "`review-required` is deliberately conservative. It means the source contains a possible execution marker and a human must read the command and its README before treating it as safe. It does not mean the command will mutate AWS."])
    return "\n".join(lines) + "\n"


def main() -> int:
    arguments = parse_arguments()
    try:
        root = repository_root()
        value = report(root)
    except InventoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if arguments.json:
        print(json.dumps(value, indent=2, sort_keys=True))
    elif not arguments.check:
        print(markdown(value), end="")
    else:
        print(
            "Deploy control inventory is readable: "
            f"{value['summary']['script_capabilities']} script capabilities, "
            f"{value['summary']['infra_files']} infra files, "
            f"{value['summary']['gaps']} reported control gaps."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
