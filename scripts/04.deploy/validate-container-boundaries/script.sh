#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.validate-container-boundaries
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - agentic
#   - sre
#   kind: script
#   purpose: Validate container image placement and ignore-file coverage without mutating the repo.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.validate-container-boundaries.readme
#     path: scripts/04.deploy/validate-container-boundaries/README.md
#   - id: deploy.script.validate-container-boundaries.smoke-test
#     path: scripts/04.deploy/validate-container-boundaries/smoke-test.sh

ROOT=""
JSON=false

usage() {
  cat <<'EOF'
Usage:
  validate-container-boundaries/script.sh [--root <path>] [--json]

Checks that Dockerfiles stay under:
  infra/<deploy-layer>/<deploy-track>/image/Dockerfile

The command is read-only.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --root requires a path." >&2
        exit 2
      fi
      ROOT="$2"
      shift 2
      ;;
    --json)
      JSON=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel)"
fi

python3 - "$ROOT" "$JSON" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
emit_json = sys.argv[2] == "true"

startup_errors: list[dict[str, str]] = []
if not root.exists():
    startup_errors.append(
        {
            "path": str(root),
            "message": "Validation root does not exist.",
            "resolution": "Pass an existing repository root or worktree path with --root.",
        }
    )
elif not root.is_dir():
    startup_errors.append(
        {
            "path": str(root),
            "message": "Validation root is not a directory.",
            "resolution": "Pass a repository directory or worktree path with --root.",
        }
    )

if startup_errors:
    report = {
        "schema": "deploy/container-boundary-report/v1",
        "ok": False,
        "root": str(root),
        "counts": {
            "dockerfiles": 0,
            "dockerignores": 0,
            "errors": len(startup_errors),
            "warnings": 0,
        },
        "allowed_dockerfile_pattern": "infra/<deploy-layer>/<deploy-track>/image/Dockerfile",
        "errors": startup_errors,
        "warnings": [],
    }
    if emit_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Container boundary validation failed:")
        for item in startup_errors:
            print(f"- {item['path']}: {item['message']} {item['resolution']}")
    sys.exit(1)

allowed_dockerfile = re.compile(r"^infra/[^/]+/[^/]+/image/Dockerfile$")
allowed_image_ignore = re.compile(r"^infra/[^/]+/[^/]+/image/(?:\.dockerignore|Dockerfile\.dockerignore)$")
ignored_dirs = {
    ".git",
    "node_modules",
    ".cache",
    "__pycache__",
}


def rel(path: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: Path) -> bool:
    parts = set(path.relative_to(root).parts)
    return bool(parts & ignored_dirs)


dockerfiles: list[Path] = []
dockerignores: list[Path] = []

for path in root.rglob("*"):
    if should_skip(path):
        continue
    if path.is_file() and path.name == "Dockerfile":
        dockerfiles.append(path)
    if path.is_file() and (path.name == ".dockerignore" or path.name.endswith(".dockerignore")):
        dockerignores.append(path)

errors: list[dict[str, str]] = []
warnings: list[dict[str, str]] = []


def error(path: str, message: str, resolution: str) -> None:
    errors.append({"path": path, "message": message, "resolution": resolution})


def warning(path: str, message: str) -> None:
    warnings.append({"path": path, "message": message})


MINIMUM_IGNORE_FAMILIES: list[tuple[str, tuple[str, ...]]] = [
    ("git internals", (".git",)),
    ("cache directories", (".cache",)),
    ("chat commit logs", ("commitLogs",)),
    ("environment files", (".env", "*.env")),
    ("credentials and secrets", ("secret", "secrets", "credential", "credentials", ".aws", "*.pem", "*.key", "id_rsa")),
    ("logs", ("*.log", "logs",)),
    ("temporary output", ("tmp", "temp", "*.tmp")),
    ("dependency folders", ("node_modules", ".venv", "vendor", "__pycache__")),
    ("generated runtime caches", (".cache/02.rag-rulebook", "runtime-cache", "local-runtime")),
    ("local agent and editor state", (".codex", ".agents", ".vscode", ".idea")),
    ("package manager and publishing credentials", (".npmrc", ".pypirc")),
]

ALLOWLIST_LATE_DENY_FAMILIES: list[tuple[str, tuple[str, ...]]] = [
    ("local agent state", (".codex", ".agents")),
    ("editor state", (".vscode", ".idea")),
    ("package manager and publishing credentials", (".npmrc", ".pypirc")),
    ("environment files", (".env", "*.env")),
    ("cloud credentials", (".aws",)),
    ("private keys", ("*.pem", "*.key", "id_rsa")),
    ("secrets and credentials", ("secret", "secrets", "credential", "credentials")),
]


def normalized_ignore_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            continue
        lines.append(line.rstrip("/"))
    return lines


def parsed_ignore_lines(path: Path) -> list[tuple[int, bool, str]]:
    lines: list[tuple[int, bool, str]] = []
    for index, raw in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:]
        lines.append((index, negated, line.rstrip("/")))
    return lines


def line_covers_token(line: str, token: str) -> bool:
    normalized_line = line.lower().replace("\\", "/")
    normalized_token = token.lower()
    return normalized_token in normalized_line


def validate_ignore_coverage(path: Path) -> None:
    path_text = rel(path)
    lines = normalized_ignore_lines(path)
    missing: list[str] = []
    for family, tokens in MINIMUM_IGNORE_FAMILIES:
        if not any(line_covers_token(line, token) for line in lines for token in tokens):
            missing.append(family)
    if missing:
        error(
            path_text,
            ".dockerignore coverage is too weak for a governed image boundary.",
            "Add ignore patterns for: " + ", ".join(missing) + ".",
        )

    parsed = parsed_ignore_lines(path)
    negated_indexes = [index for index, negated, _line in parsed if negated]
    if not negated_indexes:
        return
    last_allowlist_index = max(negated_indexes)
    missing_late_denies: list[str] = []
    late_deny_lines = [
        line
        for index, negated, line in parsed
        if not negated and index > last_allowlist_index
    ]
    for family, tokens in ALLOWLIST_LATE_DENY_FAMILIES:
        if not any(line_covers_token(line, token) for line in late_deny_lines for token in tokens):
            missing_late_denies.append(family)
    if missing_late_denies:
        error(
            path_text,
            ".dockerignore allowlist can re-include high-risk files without late deny rules.",
            "Add non-negated deny patterns after the final allowlist entry for: "
            + ", ".join(missing_late_denies)
            + ".",
        )


for dockerfile in sorted(dockerfiles):
    path = rel(dockerfile)
    if not allowed_dockerfile.fullmatch(path):
        error(
            path,
            "Dockerfile is outside the governed infra image boundary.",
            "Move it to infra/<deploy-layer>/<deploy-track>/image/Dockerfile or update the container-image-management rule through review.",
        )
        continue

    image_dir = dockerfile.parent
    readme = image_dir / "README.md"
    dockerignore = image_dir / ".dockerignore"
    dockerfile_specific_ignore = image_dir / "Dockerfile.dockerignore"
    if not readme.is_file():
        error(
            rel(readme),
            "Dockerfile is missing sibling README.md.",
            "Add a README.md that explains build context, runtime user, port, health, and provenance expectations.",
        )
    if not dockerignore.is_file() and not dockerfile_specific_ignore.is_file():
        error(
            rel(dockerignore),
            "Dockerfile is missing an effective ignore file.",
            "Add image/.dockerignore for image-directory contexts or image/Dockerfile.dockerignore for repo-root contexts.",
        )

for dockerignore in sorted(dockerignores):
    path = rel(dockerignore)
    if path == ".dockerignore":
        warning(path, "Repo-root .dockerignore is allowed only as a shared build-context safeguard.")
        validate_ignore_coverage(dockerignore)
        continue
    if not allowed_image_ignore.fullmatch(path):
        error(
            path,
            ".dockerignore is outside an approved image directory.",
            "Move it next to a governed Dockerfile as image/.dockerignore or image/Dockerfile.dockerignore, or use repo-root .dockerignore for shared context protection.",
        )
        continue
    validate_ignore_coverage(dockerignore)

report = {
    "schema": "deploy/container-boundary-report/v1",
    "ok": not errors,
    "root": str(root),
    "counts": {
        "dockerfiles": len(dockerfiles),
        "dockerignores": len(dockerignores),
        "errors": len(errors),
        "warnings": len(warnings),
    },
    "allowed_dockerfile_pattern": "infra/<deploy-layer>/<deploy-track>/image/Dockerfile",
    "errors": errors,
    "warnings": warnings,
}

if emit_json:
    print(json.dumps(report, indent=2, sort_keys=True))
else:
    if errors:
        print("Container boundary validation failed:")
        for item in errors:
            print(f"- {item['path']}: {item['message']} {item['resolution']}")
    else:
        print(f"Container boundaries valid: {len(dockerfiles)} Dockerfile(s).")
    for item in warnings:
        print(f"WARNING: {item['path']}: {item['message']}")

sys.exit(0 if report["ok"] else 1)
PY
