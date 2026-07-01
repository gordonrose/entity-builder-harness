#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.run-local-service
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Start the local RAG/rulebook HTTP service MSP skeleton.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#     - network
#   used_by:
#     - id: rag-rulebook.script.run-local-service.readme
#       path: scripts/02.rag-rulebook/run-local-service/README.md
#     - id: rag-rulebook.script.run-local-service.smoke-test
#       path: scripts/02.rag-rulebook/run-local-service/smoke-test.sh

if [ -n "${RAG_REPO_ROOT:-}" ]; then
  ROOT="$(cd "$RAG_REPO_ROOT" && pwd)"
else
  ROOT="$(git rev-parse --show-toplevel)"
fi
for marker in package.json .agentic/02.rag-rulebook/service scripts/02.rag-rulebook; do
  if [ ! -e "$ROOT/$marker" ]; then
    echo "ERROR: RAG repo root is missing required marker: $marker" >&2
    exit 2
  fi
done
cd "$ROOT"

RUNTIME_DIR=".cache/02.rag-rulebook"
HOST="127.0.0.1"
PORT="3000"
ALLOW_NON_LOOPBACK=false

usage() {
  cat <<'EOF'
Usage:
  run-local-service/script.sh [--runtime-dir <path>] [--host <host>] [--port <port>] [--allow-non-loopback]

Starts the thin local HTTP service for:
  GET  /health
  GET  /version
  POST /context/query

Build the runtime first:
  bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty

Security defaults:
  - binds to 127.0.0.1 by default
  - non-loopback binds require --allow-non-loopback and RAG_SERVICE_TOKEN
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --runtime-dir)
      RUNTIME_DIR="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --allow-non-loopback)
      ALLOW_NON_LOOPBACK=true
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

export RAG_REPO_ROOT="$ROOT"
export RAG_RUNTIME_DIR="$RUNTIME_DIR"
export HOST
export PORT
if [ "$ALLOW_NON_LOOPBACK" = true ]; then
  export RAG_ALLOW_NON_LOOPBACK=1
fi

exec node .agentic/02.rag-rulebook/service/server.mjs
