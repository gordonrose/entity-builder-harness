#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.query-local-context
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Query the local RAG/rulebook runtime cache for a validated context packet.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.plan.repo
#       path: .agentic/02.rag-rulebook/plans/repo-plan.md
#     - id: rag-rulebook.scripts.readme
#       path: scripts/02.rag-rulebook/README.md
#     - id: rag-rulebook.script.query-local-context.readme
#       path: scripts/02.rag-rulebook/query-local-context/README.md
#     - id: rag-rulebook.script.query-local-context.smoke-test
#       path: scripts/02.rag-rulebook/query-local-context/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RUNTIME_DIR=".cache/02.rag-rulebook"
REQUEST_TEXT=""
SESSION_LAYER="02.rag-rulebook"
SESSION_MODE="implementation"
SESSION_WORKFLOW=""
MAX_CHUNKS=""
PRETTY=false
NO_FOCUSED_PATHS=false
FOCUSED_PATHS=()

usage() {
  cat <<'EOF'
Usage:
  query-local-context/script.sh --request-text <text> [options]

Options:
  --runtime-dir <path>       Local runtime cache. Default: .cache/02.rag-rulebook
  --session-layer <layer>    Session layer. Default: 02.rag-rulebook
  --session-mode <mode>      Session mode. Default: implementation
  --session-workflow <path>  Session workflow path
  --focused-path <path>      Focused path signal. Repeatable
  --no-focused-paths         Use no focused path signals
  --max-chunks <n>           Maximum selected chunks. Range: 3-12
  --pretty                   Pretty-print JSON

Reads a built local runtime cache and emits a validated
rag-rulebook/context-packet/v1 packet. Build the runtime first with:
  bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
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
    --request-text)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --request-text requires text." >&2
        exit 2
      fi
      REQUEST_TEXT="$2"
      shift 2
      ;;
    --session-layer)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-layer requires a layer." >&2
        exit 2
      fi
      SESSION_LAYER="$2"
      shift 2
      ;;
    --session-mode)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-mode requires a mode." >&2
        exit 2
      fi
      SESSION_MODE="$2"
      shift 2
      ;;
    --session-workflow)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-workflow requires a path." >&2
        exit 2
      fi
      SESSION_WORKFLOW="$2"
      shift 2
      ;;
    --focused-path)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --focused-path requires a path." >&2
        exit 2
      fi
      FOCUSED_PATHS+=("$2")
      shift 2
      ;;
    --no-focused-paths)
      NO_FOCUSED_PATHS=true
      shift
      ;;
    --max-chunks)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --max-chunks requires a number." >&2
        exit 2
      fi
      MAX_CHUNKS="$2"
      shift 2
      ;;
    --pretty)
      PRETTY=true
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

if [ -z "$REQUEST_TEXT" ]; then
  echo "ERROR: --request-text is required." >&2
  usage >&2
  exit 2
fi

RUNTIME_DIR="${RUNTIME_DIR%/}"
MANIFEST_FILE="$RUNTIME_DIR/manifest.json"
CHUNKS_FILE="$RUNTIME_DIR/rulebook-chunks.json"

if [ ! -f "$MANIFEST_FILE" ] || [ ! -f "$CHUNKS_FILE" ]; then
  echo "ERROR: local RAG/rulebook runtime is missing: $RUNTIME_DIR" >&2
  echo "Run: bash scripts/02.rag-rulebook/build-local-runtime/script.sh --output-dir \"$RUNTIME_DIR\" --pretty" >&2
  exit 1
fi

python3 - "$ROOT" "$MANIFEST_FILE" "$CHUNKS_FILE" <<'PY'
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
chunks_path = Path(sys.argv[3])

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
chunks = json.loads(chunks_path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


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


def fingerprint_roots(raw_roots: list[str]) -> dict:
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


def resolve_manifest_path(raw_path: str | None) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else root / path

if manifest.get("schema") != "rag-rulebook/local-runtime-manifest/v1":
    raise SystemExit(f"ERROR: invalid local runtime manifest schema: {manifest_path}")
if chunks.get("schema") != "rag-rulebook/chunk-set/v1":
    raise SystemExit(f"ERROR: invalid local runtime chunk schema: {chunks_path}")
constraints = manifest.get("constraints") if isinstance(manifest.get("constraints"), dict) else {}
if constraints.get("network_calls") is not False or constraints.get("embeddings") is not False:
    raise SystemExit("ERROR: local runtime manifest does not declare deterministic offline constraints")

manifest_chunks = manifest.get("files", {}).get("rulebook_chunks")
if manifest_chunks:
    expected = (root / manifest_chunks).resolve() if not Path(manifest_chunks).is_absolute() else Path(manifest_chunks)
    if expected != chunks_path.resolve():
        raise SystemExit("ERROR: --runtime-dir chunks do not match manifest rulebook_chunks path")

fingerprints = manifest.get("fingerprints")
if not isinstance(fingerprints, dict):
    raise SystemExit(
        "ERROR: local RAG/rulebook runtime manifest has no fingerprints; rebuild with build-local-runtime."
    )

stale_inputs: list[str] = []
inputs = fingerprints.get("inputs")
if not isinstance(inputs, dict) or not inputs:
    raise SystemExit(
        "ERROR: local RAG/rulebook runtime manifest has no input fingerprints; rebuild with build-local-runtime."
    )
for name, expected_fingerprint in sorted(inputs.items()):
    if not isinstance(expected_fingerprint, dict):
        stale_inputs.append(str(name))
        continue
    roots = expected_fingerprint.get("roots")
    if not isinstance(roots, list) or not all(isinstance(item, str) for item in roots):
        stale_inputs.append(str(name))
        continue
    current = fingerprint_roots(roots)
    if (
        current.get("sha256") != expected_fingerprint.get("sha256")
        or current.get("file_count") != expected_fingerprint.get("file_count")
        or current.get("missing_roots") != expected_fingerprint.get("missing_roots")
    ):
        stale_inputs.append(str(name))

runtime_output_errors: list[str] = []
runtime_outputs = fingerprints.get("runtime_outputs")
if not isinstance(runtime_outputs, dict):
    runtime_output_errors.append("runtime_outputs")
else:
    for name, expected_output in sorted(runtime_outputs.items()):
        if not isinstance(expected_output, dict):
            runtime_output_errors.append(str(name))
            continue
        path = resolve_manifest_path(expected_output.get("path"))
        if path is None or not path.is_file():
            runtime_output_errors.append(str(name))
            continue
        if file_sha256(path) != expected_output.get("sha256"):
            runtime_output_errors.append(str(name))

if stale_inputs or runtime_output_errors:
    details = []
    if stale_inputs:
        details.append(f"changed inputs: {', '.join(stale_inputs)}")
    if runtime_output_errors:
        details.append(f"changed runtime outputs: {', '.join(runtime_output_errors)}")
    print("ERROR: local RAG/rulebook runtime is stale.", file=sys.stderr)
    for detail in details:
        print(f"- {detail}", file=sys.stderr)
    print(
        f"Run: bash scripts/02.rag-rulebook/build-local-runtime/script.sh --output-dir \"{manifest_path.parent}\" --pretty",
        file=sys.stderr,
    )
    raise SystemExit(1)
PY

COMMAND=(
  bash
  scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh
  --chunks "$CHUNKS_FILE"
  --request-text "$REQUEST_TEXT"
  --session-layer "$SESSION_LAYER"
  --session-mode "$SESSION_MODE"
)

if [ -n "$SESSION_WORKFLOW" ]; then
  COMMAND+=(--session-workflow "$SESSION_WORKFLOW")
fi

if [ "$NO_FOCUSED_PATHS" = true ]; then
  COMMAND+=(--no-focused-paths)
else
  for focused_path in "${FOCUSED_PATHS[@]}"; do
    COMMAND+=(--focused-path "$focused_path")
  done
fi

if [ -n "$MAX_CHUNKS" ]; then
  COMMAND+=(--max-chunks "$MAX_CHUNKS")
fi

if [ "$PRETTY" = true ]; then
  COMMAND+=(--pretty)
fi

"${COMMAND[@]}"
