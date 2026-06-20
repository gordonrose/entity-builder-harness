#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Classify one main-refresh conflict path using governed conflict types.
#   domain: main-refresh
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#     - .agentic/00.chat/standards/main-refresh-conflict-types.md
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  script.sh <conflicted-path>

Classifies one conflicted path from the Git index and prints:
  path=<path>
  type=<conflict-type>
  reason=<classification-reason>

The path must have unresolved Git conflict stages.
EOF
}

if [ $# -ne 1 ]; then
  usage >&2
  exit 2
fi

CONFLICT_PATH="$1"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not inside a Git worktree." >&2
  exit 1
fi

STAGES="$(git ls-files -u -- "$CONFLICT_PATH")"

if [ -z "$STAGES" ]; then
  echo "ERROR: path has no unresolved conflict stages: ${CONFLICT_PATH}" >&2
  exit 1
fi

has_stage() {
  local stage="$1"

  printf '%s\n' "$STAGES" | awk -v stage="$stage" '$3 == stage { found = 1 } END { exit found ? 0 : 1 }'
}

stage_content() {
  local stage="$1"

  if has_stage "$stage"; then
    git show ":${stage}:${CONFLICT_PATH}" 2>/dev/null || true
  fi
}

BASE_PRESENT=0
OURS_PRESENT=0
THEIRS_PRESENT=0

if has_stage 1; then BASE_PRESENT=1; fi
if has_stage 2; then OURS_PRESENT=1; fi
if has_stage 3; then THEIRS_PRESENT=1; fi

BASE_CONTENT="$(stage_content 1)"
OURS_CONTENT="$(stage_content 2)"
THEIRS_CONTENT="$(stage_content 3)"
ALL_CONTENT="$BASE_CONTENT
$OURS_CONTENT
$THEIRS_CONTENT"

contains_any() {
  local text="$1"
  shift
  local pattern

  for pattern in "$@"; do
    if printf '%s\n' "$text" | grep -Eq "$pattern"; then
      return 0
    fi
  done

  return 1
}

emit() {
  local type="$1"
  local reason="$2"

  printf 'path=%s\n' "$CONFLICT_PATH"
  printf 'type=%s\n' "$type"
  printf 'reason=%s\n' "$reason"
}

case "$CONFLICT_PATH" in
  commitLogs/README.md)
    if [ "$OURS_PRESENT" = "0" ] || [ "$THEIRS_PRESENT" = "0" ]; then
      emit "retired-artifact-delete-modify-conflict" "tracked aggregate commit log summary was deleted on one side and modified on the other"
      exit 0
    fi
    emit "generated-artifact-conflict" "tracked aggregate commit log summary is a retired generated artifact"
    exit 0
    ;;
  commitLogs/*/README.md)
    emit "session-bookkeeping-conflict" "path is a chat session log; preserve recorded session evidence"
    exit 0
    ;;
esac

LEGACY_SHARED_ROOT=".agentic/shared"
LEGACY_WORKFLOWS="${LEGACY_SHARED_ROOT}/workflows"
LEGACY_CHECKLISTS="${LEGACY_SHARED_ROOT}/checklists"

case "$CONFLICT_PATH" in
  "$LEGACY_WORKFLOWS/local-convergence.md"|"$LEGACY_WORKFLOWS/main-updated.md"|"$LEGACY_WORKFLOWS/chat-start-interview.md"|"$LEGACY_CHECKLISTS/before-commit.md")
    emit "ownership-migration-conflict" "path is a retired shared chat-lifecycle surface whose canonical owner is under .agentic/00.chat"
    exit 0
    ;;
esac

case "$CONFLICT_PATH" in
  *generate-commit-log-summary*|*commit-log-summary*)
    if contains_any "$ALL_CONTENT" 'commitLogs/README\.md|--write|--check|--print|--output'; then
      emit "retired-artifact-generator-conflict" "generator behavior touches retired tracked commitLogs/README.md summary policy"
      exit 0
    fi
    ;;
  *classify-main-refresh-dirty-state*|*classify-refresh-readiness*|*dirty-classifier*)
    if contains_any "$ALL_CONTENT" 'commitLogs/README\.md|generated-commitlog-summary|generated.*summary'; then
      emit "retired-artifact-policy-script-conflict" "classifier or test behavior treats retired commitLogs/README.md as active state"
      exit 0
    fi
    ;;
esac

if [ "$BASE_PRESENT" = "0" ] && [ "$OURS_PRESENT" = "1" ] && [ "$THEIRS_PRESENT" = "1" ]; then
  case "$CONFLICT_PATH" in
    scripts/*|*.sh|*.js|*.mjs)
      emit "script-add-add-conflict" "both sides added the same script-like path independently"
      exit 0
      ;;
  esac
fi

case "$CONFLICT_PATH" in
  .agentic/*|docs/*|scripts/*|src/*|tests/*|package.json)
    emit "normal-repo-conflict" "authored repository content has no more specific governed conflict type"
    ;;
  *)
    emit "unsupported-conflict" "path ownership or conflict shape is not covered by a deterministic classifier rule"
    ;;
esac
