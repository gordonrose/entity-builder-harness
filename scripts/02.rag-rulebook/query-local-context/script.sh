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
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
chunks_path = Path(sys.argv[3])

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

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
