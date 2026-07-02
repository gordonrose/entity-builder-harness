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
REQUEST_TEXT=""
SESSION_ID=""
SESSION_BRANCH=""
SESSION_WORKTREE=""
SESSION_LAYER="unknown"
SESSION_MODE="unknown"
SESSION_WORKFLOW="unknown"
PREVIOUS_PACKET_ID=""
PREVIOUS_ROUTING_SUMMARY=""
TRUST_SESSION_ROUTING=false
MAX_CHUNKS=""
PRETTY=false
FORMAT="full"
NO_FOCUSED_PATHS=false
FOCUSED_PATHS=()

usage() {
  cat <<'EOF'
Usage:
  query-local-context/script.sh --request-text <text> [options]

Options:
  --runtime-dir <path>       Local runtime cache. Default: .cache/02.rag-rulebook
  --session-id <id>          Chat/session ID for provenance
  --session-branch <branch>  Chat/session branch for provenance
  --session-worktree <path>  Chat/session worktree for provenance
  --session-layer <layer>    Legacy session routing hint. Default: unknown
  --session-mode <mode>      Legacy session routing hint. Default: unknown
  --session-workflow <path>  Legacy session routing hint. Default: unknown
  --previous-packet-id <id>  Previous context packet for continuity
  --previous-routing-summary <text>
                              Previous packet routing summary
  --trust-session-routing     Trust supplied session layer/mode/workflow after
                              governed session ownership verification
  --focused-path <path>      Focused path signal. Repeatable
  --no-focused-paths         Use no focused path signals
  --max-chunks <n>           Maximum selected chunks. Range: 3-12
  --format <full|compact>    Output format. Default: full
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
    --session-id)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-id requires a value." >&2
        exit 2
      fi
      SESSION_ID="$2"
      shift 2
      ;;
    --session-branch)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-branch requires a value." >&2
        exit 2
      fi
      SESSION_BRANCH="$2"
      shift 2
      ;;
    --session-worktree)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --session-worktree requires a value." >&2
        exit 2
      fi
      SESSION_WORKTREE="$2"
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
    --previous-packet-id)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --previous-packet-id requires a value." >&2
        exit 2
      fi
      PREVIOUS_PACKET_ID="$2"
      shift 2
      ;;
    --previous-routing-summary)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --previous-routing-summary requires text." >&2
        exit 2
      fi
      PREVIOUS_ROUTING_SUMMARY="$2"
      shift 2
      ;;
    --trust-session-routing)
      TRUST_SESSION_ROUTING=true
      shift
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
    --format)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --format requires full or compact." >&2
        exit 2
      fi
      FORMAT="$2"
      case "$FORMAT" in
        full|compact)
          ;;
        *)
          echo "ERROR: --format must be full or compact." >&2
          exit 2
          ;;
      esac
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
COMPILED_POLICY_FILE="$RUNTIME_DIR/compiled-retrieval-policy.json"

if [ ! -f "$MANIFEST_FILE" ] || [ ! -f "$CHUNKS_FILE" ] || [ ! -f "$COMPILED_POLICY_FILE" ]; then
  echo "ERROR: local RAG/rulebook runtime is missing: $RUNTIME_DIR" >&2
  echo "Run: bash scripts/02.rag-rulebook/build-local-runtime/script.sh --output-dir \"$RUNTIME_DIR\" --pretty" >&2
  exit 1
fi

bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir "$RUNTIME_DIR" >/dev/null

COMMAND=(
  bash
  scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh
  --chunks "$CHUNKS_FILE"
  --compiled-policy "$COMPILED_POLICY_FILE"
  --request-text "$REQUEST_TEXT"
  --session-id "$SESSION_ID"
  --session-branch "$SESSION_BRANCH"
  --session-worktree "$SESSION_WORKTREE"
  --session-layer "$SESSION_LAYER"
  --session-mode "$SESSION_MODE"
  --session-workflow "$SESSION_WORKFLOW"
  --previous-packet-id "$PREVIOUS_PACKET_ID"
  --previous-routing-summary "$PREVIOUS_ROUTING_SUMMARY"
)

if [ "$TRUST_SESSION_ROUTING" = true ]; then
  COMMAND+=(--trust-session-routing)
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

if [ "$FORMAT" = "full" ]; then
  "${COMMAND[@]}"
  exit 0
fi

TMP_PACKET="$(mktemp)"
trap 'rm -f "$TMP_PACKET"' EXIT

"${COMMAND[@]}" > "$TMP_PACKET"

python3 - "$TMP_PACKET" "$PRETTY" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet_path = Path(sys.argv[1])
pretty = sys.argv[2] == "true"
packet = json.loads(packet_path.read_text(encoding="utf-8"))

selected_chunks = packet.get("selected_chunks", [])
citation_ids = set()
for chunk in selected_chunks:
    citation_ids.update(chunk.get("citation_ids", []))
for gap in packet.get("gaps", []):
    citation_ids.update(gap.get("citation_ids", []))

citations = [
    citation
    for citation in packet.get("citations", [])
    if citation.get("id") in citation_ids
]

selector_trace = packet.get("selector_trace") or {}
stage_statuses = [
    {
        "rank": stage.get("rank"),
        "stage_id": stage.get("stage_id"),
        "status": stage.get("status"),
    }
    for stage in selector_trace.get("stages", [])
]
request = packet.get("request") or {}
compact_request = {
    "raw_text": request.get("raw_text"),
    "normalized_summary": request.get("normalized_summary"),
    "focused_paths": request.get("focused_paths", []),
    "open_artifact_ids": request.get("open_artifact_ids", []),
    "previous_packet_id": request.get("previous_packet_id"),
}

compact = {
    "schema": "rag-rulebook/context-packet-compact/v1",
    "source_schema": packet.get("schema"),
    "packet_id": packet.get("packet_id"),
    "generated_at": packet.get("generated_at"),
    "request": compact_request,
    "intent": packet.get("intent"),
    "routing": packet.get("routing"),
    "confidence": packet.get("confidence"),
    "selected_chunks": [
        {
            "rank": chunk.get("rank"),
            "chunk_id": chunk.get("chunk_id"),
            "corpus_id": chunk.get("corpus_id"),
            "artifact_id": chunk.get("artifact_id"),
            "source_path": chunk.get("source_path"),
            "section_path": chunk.get("section_path"),
            "retrieval_score": chunk.get("retrieval_score"),
            "token_estimate": chunk.get("token_estimate"),
            "selection_reason": chunk.get("selection_reason"),
            "citation_ids": chunk.get("citation_ids", []),
            "rule_ids": chunk.get("rule_ids", []),
            "content": chunk.get("content"),
        }
        for chunk in selected_chunks
    ],
    "citations": citations,
    "gaps": packet.get("gaps", []),
    "required_checks": packet.get("required_checks", []),
    "forbidden_actions": packet.get("forbidden_actions", []),
    "stop_conditions": packet.get("stop_conditions", []),
    "budgets": packet.get("budgets"),
    "debug": {
        "full_packet_available_with": "--format full",
        "selector_trace_available_in_full_packet": bool(selector_trace),
        "selector_strategy_id": selector_trace.get("strategy_id"),
        "selector_stage_statuses": stage_statuses,
    },
    "packet_summary": {
        "selected_chunk_count": len(selected_chunks),
        "citation_count": len(citations),
        "gap_count": len(packet.get("gaps", [])),
        "required_check_count": len(packet.get("required_checks", [])),
        "stop_condition_count": len(packet.get("stop_conditions", [])),
    },
}

indent = 2 if pretty else None
print(json.dumps(compact, indent=indent, sort_keys=pretty))
PY
