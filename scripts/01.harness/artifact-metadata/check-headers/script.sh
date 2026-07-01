#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.check-headers
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Validate v1 and v2 artifact metadata headers for harness artifacts.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: harness.standard.artifact-metadata
#       path: .agentic/01.harness/artifact-metadata/standard.md
#     - id: harness.checklist.before-commit
#       path: .agentic/00.chat/checklists/before-commit.md

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment gate
    print("ERROR: python3 yaml module is required for artifact metadata checks.", file=sys.stderr)
    sys.exit(2)


V1_OWNERS = {"00.chat", "shared", "harness", "aws", "product", "education"}
V1_PORTABILITY = {
    "llm-workbench-required",
    "llm-workbench-validation",
    "llm-workbench-compatibility",
    "source-only",
    "internal",
}
PATH_PREFIXES = (
    "AGENTS.md",
    ".github/workflows/",
    ".agentic/",
    "docs/00.chat/",
    "docs/02.rag-rulebook/",
    "docs/harness/",
    "infra/",
    "scripts/",
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$")
DOMAIN_RE = ID_RE


class CheckError(Exception):
    pass


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


ROOT = repo_root()


def load_taxonomy() -> dict[str, Any]:
    path = ROOT / ".agentic/01.harness/artifact-metadata/taxonomy.yml"
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


TAXONOMY = load_taxonomy()
LAYERS = {entry["id"] for entry in TAXONOMY.get("layers", [])}
DISCIPLINES = set(TAXONOMY.get("disciplines", []))
STATUSES = set(TAXONOMY.get("statuses", []))
PORTABILITY_CLASSES = set(TAXONOMY.get("portability_classes", []))
SCRIPT_EFFECTS = set(TAXONOMY.get("script_effects", []))


def usage() -> str:
    return """Usage:
  check-artifact-metadata-headers.sh --staged-added
  check-artifact-metadata-headers.sh --paths <path> [path...]
  check-artifact-metadata-headers.sh --all

Checks scripts, chat Markdown documents, harness Markdown documents, and harness
YAML artifacts for required agentic metadata headers. --staged-added enforces
only newly added files so existing files can be backfilled in batches.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--staged-added", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)

    if args.help:
        print(usage(), end="")
        sys.exit(0)

    modes = [args.staged_added, args.all, args.paths is not None]
    if sum(1 for mode in modes if mode) != 1:
        print("ERROR: choose exactly one mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    if args.paths == []:
        print("ERROR: --paths requires at least one path.", file=sys.stderr)
        sys.exit(2)
    return args


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE)
    return result.stdout


def normalize_path(path: Path | str) -> str:
    path_obj = Path(path)
    if path_obj.is_absolute():
        try:
            return path_obj.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return path_obj.as_posix()
    return path_obj.as_posix()


def collect_staged_added_paths() -> list[str]:
    output = run_git(["diff", "--cached", "--name-status", "--diff-filter=ACR"])
    paths = []
    for line in output.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            paths.append(parts[2])
        elif len(parts) >= 2:
            paths.append(parts[1])
    return sorted(set(paths))


def collect_paths_from_args(paths: list[str]) -> list[str]:
    collected: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        absolute = path if path.is_absolute() else ROOT / path
        if absolute.is_dir():
            collected.extend(normalize_path(child) for child in absolute.rglob("*") if child.is_file())
        elif absolute.is_file():
            collected.append(normalize_path(absolute))
        else:
            print(f"WARN: path does not exist, skipping: {raw_path}", file=sys.stderr)
    return sorted(set(collected))


def collect_all_paths() -> list[str]:
    roots = [
        ROOT / "scripts",
        ROOT / ".github/workflows",
        ROOT / ".agentic",
        ROOT / "docs/00.chat",
        ROOT / "docs/02.rag-rulebook",
        ROOT / "docs/harness",
        ROOT / "infra",
    ]
    collected: list[str] = []
    for root in roots:
        if root.is_dir():
            collected.extend(normalize_path(path) for path in root.rglob("*") if path.is_file())
    return sorted(set(collected))


def is_script_artifact(path: str) -> bool:
    return (
        path.startswith("scripts/")
        and path.endswith((".sh", ".js", ".mjs"))
    ) or (
        path.startswith(".agentic/")
        and path.endswith((".js", ".mjs"))
    )


def is_markdown_artifact(path: str) -> bool:
    return path.endswith(".md") and (
        path.startswith(".agentic/")
        or path.startswith("docs/00.chat/")
        or path.startswith("docs/02.rag-rulebook/")
        or path.startswith("docs/aws/")
        or path.startswith("docs/education/")
        or path.startswith("docs/harness/")
        or path.startswith("infra/")
        or path.startswith("scripts/")
    )


def is_yaml_artifact(path: str) -> bool:
    return path.endswith((".yml", ".yaml")) and (
        path.startswith(".agentic/")
        or path.startswith(".github/workflows/")
        or path.startswith("docs/02.rag-rulebook/")
        or path.startswith("docs/harness/")
    )


def is_relevant_path(path: str) -> bool:
    return is_script_artifact(path) or is_markdown_artifact(path) or is_yaml_artifact(path)


def strip_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("# "):
        return stripped[2:]
    if stripped.startswith("#"):
        return stripped[1:]
    if stripped.startswith("// "):
        return stripped[3:]
    if stripped.startswith("//"):
        return stripped[2:]
    return line


def parse_header(path: str) -> dict[str, Any]:
    full_path = ROOT / path
    lines = full_path.read_text(encoding="utf-8").splitlines()[:120]

    for index, line in enumerate(lines):
        if "agentic-artifact:" not in line and "agentic-script:" not in line:
            continue

        if line.lstrip().startswith("<!--"):
            marker = line.replace("<!--", "", 1).strip()
            body_lines = []
            for following in lines[index + 1 :]:
                if "-->" in following:
                    before_end = following.split("-->", 1)[0]
                    if before_end.strip():
                        body_lines.append(before_end)
                    break
                body_lines.append(following)
            header_lines = [marker]
            header_lines.extend(f"  {body_line}" if body_line.strip() else body_line for body_line in body_lines)
        else:
            header_lines = [strip_comment(line)]
            for following in lines[index + 1 :]:
                stripped = following.lstrip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    header_lines.append(strip_comment(following))
                    continue
                if not following.strip():
                    break
                break

        try:
            parsed = yaml.safe_load("\n".join(header_lines)) or {}
        except yaml.YAMLError as exc:
            raise CheckError(f"invalid metadata YAML: {path}: {exc}") from exc
        if not isinstance(parsed, dict):
            raise CheckError(f"invalid metadata header shape: {path}")
        return parsed

    return {}


def require_fields(path: str, metadata: dict[str, Any], fields: list[str], label: str) -> None:
    for field in fields:
        if field not in metadata or metadata[field] in (None, ""):
            raise CheckError(f"missing {field} in {label} metadata header: {path}")


def validate_used_by_path(path: str, ref: str) -> None:
    if not ref or not ref.startswith(PATH_PREFIXES):
        return
    if not (ROOT / ref).exists():
        raise CheckError(f"{path} references missing used_by path: {ref}")


def validate_v1_used_by_paths(path: str, used_by: Any) -> None:
    if not isinstance(used_by, list):
        raise CheckError(f"used_by must be a list in metadata header: {path}")
    for entry in used_by:
        if isinstance(entry, str):
            validate_used_by_path(path, entry)
        elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
            validate_used_by_path(path, entry["path"])


def validate_v1_script(path: str, metadata: dict[str, Any]) -> None:
    require_fields(path, metadata, ["owner", "purpose", "domain", "portability", "used_by", "effects"], "script")
    if metadata["owner"] not in V1_OWNERS:
        raise CheckError(f"invalid owner value in script metadata header: {path}")
    if metadata["portability"] not in V1_PORTABILITY:
        raise CheckError(f"invalid portability value in script metadata header: {path}")
    validate_v1_used_by_paths(path, metadata["used_by"])


def validate_v1_artifact(path: str, metadata: dict[str, Any], yaml_artifact: bool) -> None:
    label = "YAML artifact" if yaml_artifact else "artifact"
    require_fields(path, metadata, ["owner", "kind", "purpose", "domain", "portability", "used_by"], label)
    if metadata["owner"] not in V1_OWNERS:
        raise CheckError(f"invalid owner value in {label} metadata header: {path}")
    if metadata["portability"] not in V1_PORTABILITY:
        raise CheckError(f"invalid portability value in {label} metadata header: {path}")
    validate_v1_used_by_paths(path, metadata["used_by"])


def require_type(path: str, field: str, value: Any, expected_type: type, description: str) -> None:
    if not isinstance(value, expected_type):
        raise CheckError(f"{field} must be {description} in v2 metadata header: {path}")


def validate_id(path: str, field: str, value: str) -> None:
    if not ID_RE.match(value):
        raise CheckError(f"invalid {field} value in v2 metadata header: {path}")


def validate_v2(path: str, metadata: dict[str, Any]) -> None:
    required = [
        "schema",
        "id",
        "version",
        "status",
        "layer",
        "domain",
        "disciplines",
        "kind",
        "purpose",
        "portability",
        "used_by",
    ]
    require_fields(path, metadata, required, "v2 artifact")

    if metadata["schema"] != "agentic-artifact/v2":
        raise CheckError(f"invalid schema value in v2 metadata header: {path}")

    require_type(path, "id", metadata["id"], str, "a string")
    validate_id(path, "id", metadata["id"])

    if not isinstance(metadata["version"], int) or metadata["version"] < 1:
        raise CheckError(f"version must be an integer greater than zero in v2 metadata header: {path}")

    if metadata["status"] not in STATUSES:
        raise CheckError(f"invalid status value in v2 metadata header: {path}")
    if metadata["layer"] not in LAYERS:
        raise CheckError(f"invalid layer value in v2 metadata header: {path}")

    require_type(path, "domain", metadata["domain"], str, "a string")
    if not DOMAIN_RE.match(metadata["domain"]):
        raise CheckError(f"invalid domain value in v2 metadata header: {path}")

    disciplines = metadata["disciplines"]
    if not isinstance(disciplines, list) or not disciplines:
        raise CheckError(f"disciplines must be a non-empty list in v2 metadata header: {path}")
    for discipline in disciplines:
        if discipline not in DISCIPLINES:
            raise CheckError(f"invalid discipline value in v2 metadata header: {path}: {discipline}")

    require_type(path, "kind", metadata["kind"], str, "a string")
    require_type(path, "purpose", metadata["purpose"], str, "a string")
    if not metadata["kind"].strip() or not metadata["purpose"].strip():
        raise CheckError(f"kind and purpose must be non-empty in v2 metadata header: {path}")

    portability = metadata["portability"]
    if not isinstance(portability, dict):
        raise CheckError(f"portability must be an object in v2 metadata header: {path}")
    if portability.get("class") not in PORTABILITY_CLASSES:
        raise CheckError(f"invalid portability.class value in v2 metadata header: {path}")
    targets = portability.get("targets")
    if not isinstance(targets, list):
        raise CheckError(f"portability.targets must be a list in v2 metadata header: {path}")
    for target in targets:
        if not isinstance(target, str) or not target:
            raise CheckError(f"portability.targets entries must be strings in v2 metadata header: {path}")

    used_by = metadata["used_by"]
    if not isinstance(used_by, list) or not used_by:
        raise CheckError(f"used_by must be a non-empty list in v2 metadata header: {path}")
    for entry in used_by:
        if not isinstance(entry, dict):
            raise CheckError(f"used_by entries must be objects in v2 metadata header: {path}")
        ref_id = entry.get("id")
        if not isinstance(ref_id, str) or not ref_id:
            raise CheckError(f"used_by.id is required in v2 metadata header: {path}")
        validate_id(path, "used_by.id", ref_id)
        ref_path = entry.get("path")
        if ref_path is not None:
            if not isinstance(ref_path, str):
                raise CheckError(f"used_by.path must be a string in v2 metadata header: {path}")
            validate_used_by_path(path, ref_path)

    effects = metadata.get("effects")
    if metadata["kind"] == "script" or is_script_artifact(path):
        if metadata["kind"] != "script":
            raise CheckError(f"script file must use kind: script in v2 metadata header: {path}")
        if not isinstance(effects, list) or not effects:
            raise CheckError(f"effects must be a non-empty list for v2 script metadata header: {path}")
    if effects is not None:
        if not isinstance(effects, list):
            raise CheckError(f"effects must be a list in v2 metadata header: {path}")
        for effect in effects:
            if effect not in SCRIPT_EFFECTS:
                raise CheckError(f"invalid effects value in v2 metadata header: {path}: {effect}")


def validate_path(path: str) -> None:
    parsed = parse_header(path)
    artifact = parsed.get("agentic-artifact")
    script = parsed.get("agentic-script")

    if is_script_artifact(path):
        if isinstance(artifact, dict) and artifact.get("schema") == "agentic-artifact/v2":
            validate_v2(path, artifact)
            return
        if isinstance(script, dict):
            validate_v1_script(path, script)
            return
        raise CheckError(f"missing agentic-script or agentic-artifact/v2 metadata header: {path}")

    if isinstance(artifact, dict):
        if artifact.get("schema") == "agentic-artifact/v2":
            validate_v2(path, artifact)
        else:
            validate_v1_artifact(path, artifact, is_yaml_artifact(path))
        return

    raise CheckError(f"missing agentic-artifact metadata header: {path}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.staged_added:
        paths = collect_staged_added_paths()
    elif args.all:
        paths = collect_all_paths()
    else:
        paths = collect_paths_from_args(args.paths or [])

    failures = 0
    checked = 0
    for path in paths:
        if not path or not is_relevant_path(path):
            continue
        if not (ROOT / path).is_file():
            continue
        checked += 1
        try:
            validate_path(path)
        except CheckError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failures += 1

    if failures:
        print(f"Artifact metadata header check failed: {failures} file(s).", file=sys.stderr)
        return 1

    print(f"Artifact metadata headers passed for {checked} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY
