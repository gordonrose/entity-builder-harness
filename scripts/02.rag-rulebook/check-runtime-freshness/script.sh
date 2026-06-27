#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.check-runtime-freshness
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Verify that a local RAG/rulebook runtime cache matches current governed inputs.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.check-runtime-freshness.readme
#       path: scripts/02.rag-rulebook/check-runtime-freshness/README.md
#     - id: rag-rulebook.script.check-runtime-freshness.smoke-test
#       path: scripts/02.rag-rulebook/check-runtime-freshness/smoke-test.sh
#     - id: rag-rulebook.script.query-local-context
#       path: scripts/02.rag-rulebook/query-local-context/script.sh
#     - id: rag-rulebook.script.commit-gates
#       path: scripts/02.rag-rulebook/commit-gates/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RUNTIME_DIR=".cache/02.rag-rulebook"
JSON=false

usage() {
  cat <<'EOF'
Usage:
  check-runtime-freshness/script.sh [--runtime-dir <path>] [--json]

Checks whether a built local RAG/rulebook runtime cache still matches current
governed inputs and runtime output fingerprints. This command is read-only and
does not rebuild stale runtimes.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --runtime-dir)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --runtime-dir requires a path." >&2
        exit 2
      fi
      RUNTIME_DIR="$2"
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

RUNTIME_DIR="${RUNTIME_DIR%/}"
MANIFEST_FILE="$RUNTIME_DIR/manifest.json"

python3 - "$ROOT" "$RUNTIME_DIR" "$MANIFEST_FILE" "$JSON" <<'PY'
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
runtime_dir = Path(sys.argv[2])
manifest_path = Path(sys.argv[3])
emit_json = sys.argv[4] == "true"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def runtime_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(runtime_dir.resolve()))
    except ValueError:
        return rel(path)


def resolve_path(raw_path: Any) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else root / path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_fingerprint_files(raw_roots: list[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    missing_roots: list[str] = []
    for raw_root in raw_roots:
        root_path = Path(raw_root)
        absolute = root_path if root_path.is_absolute() else root / root_path
        if absolute.is_file():
            files.append(absolute)
        elif absolute.is_dir():
            files.extend(path for path in absolute.rglob("*") if path.is_file())
        else:
            missing_roots.append(raw_root)
    return sorted(set(files), key=lambda path: rel(path)), sorted(missing_roots)


def fingerprint_roots(raw_roots: list[str]) -> dict[str, Any]:
    files, missing_roots = iter_fingerprint_files(raw_roots)
    digest = hashlib.sha256()
    digest.update(b"rag-rulebook-fingerprint-v1\n")
    for raw_root in sorted(raw_roots):
        digest.update(f"root:{raw_root}\n".encode("utf-8"))
    for missing_root in missing_roots:
        digest.update(f"missing:{missing_root}\n".encode("utf-8"))
    for path in files:
        relative = rel(path)
        digest.update(f"file:{relative}\n".encode("utf-8"))
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return {
        "algorithm": "sha256-relpath-content-v1",
        "roots": raw_roots,
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "missing_roots": missing_roots,
        "paths": [rel(path) for path in files],
    }


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def base_report() -> dict[str, Any]:
    return {
        "schema": "rag-rulebook/runtime-freshness-report/v1",
        "policy_version": "strict-v1",
        "ok": False,
        "status": "blocked",
        "severity": "blocked",
        "runtime_dir": rel(runtime_dir),
        "manifest_path": rel(manifest_path),
        "checks": {
            "inputs": [],
            "runtime_outputs": [],
            "manifest": [],
        },
        "differences": {
            "inputs": [],
            "runtime_outputs": [],
            "manifest": [],
        },
        "build_command": f'bash scripts/02.rag-rulebook/build-local-runtime/script.sh --output-dir "{runtime_dir}" --pretty',
    }


def finish(report: dict[str, Any], exit_code: int) -> None:
    if emit_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = report.get("status", "blocked")
        stream = sys.stdout if exit_code == 0 else sys.stderr
        print(f"RAG/rulebook runtime freshness: {status}", file=stream)
        if exit_code != 0:
            for category in ("manifest", "inputs", "runtime_outputs"):
                for item in report.get("differences", {}).get(category, []):
                    name = item.get("name") or item.get("path") or category
                    message = item.get("message", "runtime freshness check failed")
                    print(f"- {category}: {name}: {message}", file=stream)
            print(f"Run: {report['build_command']}", file=stream)
    raise SystemExit(exit_code)


report = base_report()

if not manifest_path.is_file():
    report["status"] = "missing"
    report["differences"]["manifest"].append(
        {
            "path": rel(manifest_path),
            "message": "local runtime manifest is missing",
        }
    )
    finish(report, 1)

try:
    manifest = load_json_file(manifest_path)
except Exception as exc:
    report["status"] = "corrupt"
    report["differences"]["manifest"].append(
        {
            "path": rel(manifest_path),
            "message": f"manifest could not be parsed: {exc}",
        }
    )
    finish(report, 1)

if manifest.get("schema") != "rag-rulebook/local-runtime-manifest/v1":
    report["status"] = "corrupt"
    report["differences"]["manifest"].append(
        {
            "path": rel(manifest_path),
            "message": "manifest schema is missing or unsupported",
        }
    )

constraints = manifest.get("constraints") if isinstance(manifest.get("constraints"), dict) else {}
if constraints.get("network_calls") is not False or constraints.get("embeddings") is not False:
    report["status"] = "corrupt"
    report["differences"]["manifest"].append(
        {
            "path": "constraints",
            "message": "manifest does not declare deterministic offline constraints",
        }
    )

files = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
expected_runtime_files = {
    "rulebook_index": ("rulebook-index.json", "rag-rulebook/rulebook-index/v1"),
    "rulebook_chunks": ("rulebook-chunks.json", "rag-rulebook/chunk-set/v1"),
}
for name, (expected_relative_path, expected_schema) in expected_runtime_files.items():
    raw_path = files.get(name)
    path = resolve_path(raw_path)
    item = {
        "name": name,
        "expected_path": expected_relative_path,
        "manifest_path": raw_path,
    }
    if path is None:
        item.update({"status": "corrupt", "message": "manifest file path is missing"})
        report["checks"]["runtime_outputs"].append(item)
        report["differences"]["runtime_outputs"].append(item)
        continue
    item["path"] = rel(path)
    if runtime_rel(path) != expected_relative_path:
        item.update({"status": "corrupt", "message": "manifest file path does not match runtime directory"})
        report["checks"]["runtime_outputs"].append(item)
        report["differences"]["runtime_outputs"].append(item)
        continue
    if not path.is_file():
        item.update({"status": "corrupt", "message": "runtime output file is missing"})
        report["checks"]["runtime_outputs"].append(item)
        report["differences"]["runtime_outputs"].append(item)
        continue
    try:
        output = load_json_file(path)
    except Exception as exc:
        item.update({"status": "corrupt", "message": f"runtime output could not be parsed: {exc}"})
        report["checks"]["runtime_outputs"].append(item)
        report["differences"]["runtime_outputs"].append(item)
        continue
    if output.get("schema") != expected_schema:
        item.update({"status": "corrupt", "message": "runtime output schema is missing or unsupported"})
        report["checks"]["runtime_outputs"].append(item)
        report["differences"]["runtime_outputs"].append(item)
        continue
    item.update({"status": "present", "schema": expected_schema})
    report["checks"]["runtime_outputs"].append(item)

fingerprints = manifest.get("fingerprints")
if not isinstance(fingerprints, dict):
    report["status"] = "corrupt"
    report["differences"]["manifest"].append(
        {
            "path": "fingerprints",
            "message": "manifest has no fingerprints",
        }
    )
    finish(report, 1)

inputs = fingerprints.get("inputs")
if not isinstance(inputs, dict) or not inputs:
    report["status"] = "corrupt"
    report["differences"]["manifest"].append(
        {
            "path": "fingerprints.inputs",
            "message": "manifest has no input fingerprints",
        }
    )
else:
    for name, expected_fingerprint in sorted(inputs.items()):
        item = {"name": str(name)}
        if not isinstance(expected_fingerprint, dict):
            item.update({"status": "corrupt", "message": "input fingerprint is not an object"})
            report["checks"]["inputs"].append(item)
            report["differences"]["inputs"].append(item)
            continue
        roots = expected_fingerprint.get("roots")
        if not isinstance(roots, list) or not all(isinstance(entry, str) for entry in roots):
            item.update({"status": "corrupt", "message": "input fingerprint roots are invalid"})
            report["checks"]["inputs"].append(item)
            report["differences"]["inputs"].append(item)
            continue
        current = fingerprint_roots(roots)
        item.update(
            {
                "roots": roots,
                "expected_sha256": expected_fingerprint.get("sha256"),
                "current_sha256": current.get("sha256"),
                "expected_file_count": expected_fingerprint.get("file_count"),
                "current_file_count": current.get("file_count"),
                "expected_missing_roots": expected_fingerprint.get("missing_roots"),
                "current_missing_roots": current.get("missing_roots"),
            }
        )
        if (
            current.get("sha256") != expected_fingerprint.get("sha256")
            or current.get("file_count") != expected_fingerprint.get("file_count")
            or current.get("missing_roots") != expected_fingerprint.get("missing_roots")
        ):
            item.update({"status": "stale", "message": "current input fingerprint does not match manifest"})
            report["checks"]["inputs"].append(item)
            report["differences"]["inputs"].append(item)
        else:
            item.update({"status": "fresh"})
            report["checks"]["inputs"].append(item)

runtime_outputs = fingerprints.get("runtime_outputs")
if not isinstance(runtime_outputs, dict):
    report["status"] = "corrupt"
    report["differences"]["manifest"].append(
        {
            "path": "fingerprints.runtime_outputs",
            "message": "manifest has no runtime output fingerprints",
        }
    )
else:
    for name, expected_output in sorted(runtime_outputs.items()):
        item = {"name": str(name)}
        if not isinstance(expected_output, dict):
            item.update({"status": "corrupt", "message": "runtime output fingerprint is not an object"})
            report["checks"]["runtime_outputs"].append(item)
            report["differences"]["runtime_outputs"].append(item)
            continue
        path = resolve_path(expected_output.get("path"))
        item["path"] = expected_output.get("path")
        item["expected_sha256"] = expected_output.get("sha256")
        if path is None or not path.is_file():
            item.update({"status": "corrupt", "message": "runtime output path is missing"})
            report["checks"]["runtime_outputs"].append(item)
            report["differences"]["runtime_outputs"].append(item)
            continue
        current_sha256 = file_sha256(path)
        item["current_sha256"] = current_sha256
        if current_sha256 != expected_output.get("sha256"):
            item.update({"status": "stale", "message": "runtime output content does not match manifest"})
            report["checks"]["runtime_outputs"].append(item)
            report["differences"]["runtime_outputs"].append(item)
        else:
            item.update({"status": "fresh"})
            report["checks"]["runtime_outputs"].append(item)

has_corrupt_input = any(
    item.get("status") == "corrupt"
    for item in report["differences"]["inputs"]
)
has_corrupt_runtime_output = any(
    item.get("status") == "corrupt"
    for item in report["differences"]["runtime_outputs"]
)

if report["differences"]["manifest"] or has_corrupt_input or has_corrupt_runtime_output:
    report["status"] = "corrupt"
elif report["differences"]["inputs"] or report["differences"]["runtime_outputs"]:
    report["status"] = "stale"
else:
    report["ok"] = True
    report["status"] = "fresh"
    report["severity"] = "fresh"

finish(report, 0 if report["ok"] else 1)
PY
