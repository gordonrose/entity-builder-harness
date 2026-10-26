#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.prepare-chat-session-before-commit
#   version: 3
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-10-26"
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Run commit-boundary gates and session-log readiness checks before task commits.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.prepare-chat-session-before-commit.readme
#     path: scripts/00.chat/session-log/prepare-chat-session-before-commit/README.md
#   effects:
#   - read-only
#   - writes-files

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  prepare-chat-session-before-commit/script.sh
  prepare-chat-session-before-commit/script.sh --before-verification --paths <task-path> [<task-path>...]

The default command validates a staged commit boundary. The before-verification
mode completes lifecycle metadata for the named task paths, validates their
artifact structure and emits the focused selector plan whose input identities
must remain unchanged for commit-time evidence reuse.
EOF
}

prepare_before_verification() {
  shift
  if [ "${1:-}" != "--paths" ]; then
    echo "ERROR: --before-verification requires --paths <task-path> [...]" >&2
    usage >&2
    exit 2
  fi
  shift
  if [ "$#" -eq 0 ]; then
    echo "ERROR: --paths requires at least one task path" >&2
    exit 2
  fi

  local lifecycle_report
  local -a lifecycle_artifacts
  lifecycle_report="$(mktemp "${TMPDIR:-/tmp}/verification-preparation-lifecycle.XXXXXX")"

  bash scripts/00.chat/worktree/check-write-location/script.sh
  bash scripts/00.chat/session-log/check-commit-prerequisites/script.sh
  if ! bash scripts/01.harness/artifact-metadata/update-lifecycle/script.sh \
    --paths "$@" --skip-non-artifacts --apply > "$lifecycle_report"; then
    cat "$lifecycle_report"
    rm -f "$lifecycle_report"
    return 1
  fi
  cat "$lifecycle_report"
  mapfile -t lifecycle_artifacts < <(python3 - "$lifecycle_report" <<'PY'
import json
import sys
report = json.load(open(sys.argv[1], encoding='utf-8'))
for plan in report.get('plans', []):
    if isinstance(plan, dict) and isinstance(plan.get('path'), str):
        print(plan['path'])
PY
)
  if [ "${#lifecycle_artifacts[@]}" -gt 0 ]; then
    bash scripts/01.harness/artifact-metadata/generate-index/script.sh --paths "${lifecycle_artifacts[@]}" --strict > /dev/null
  fi
  rm -f "$lifecycle_report"
  bash scripts/01.harness/artifact-metadata/check-headers/script.sh --paths "$@"
  if [ -f scripts/repo/check-selection/script.sh ]; then
    bash scripts/repo/check-selection/script.sh --paths "$@" --stage local --record-preparation --json
  else
    echo "Repository selector is absent; portable lifecycle preparation completed without repository verification planning."
  fi
  echo "Verification preparation passed. Run the selected final verification next; commit preparation will reuse only unchanged input identities."
}

case "${1:-}" in
  --before-verification)
    prepare_before_verification "$@"
    exit 0
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    echo "ERROR: unknown argument: $1" >&2
    usage >&2
    exit 2
    ;;
esac

bash scripts/00.chat/worktree/check-write-location/script.sh
bash scripts/00.chat/session-log/check-commit-prerequisites/script.sh
bash scripts/00.chat/session-log/check-commitlog-deletions/script.sh
bash scripts/01.harness/check-deterministic-process-drift.sh --staged
bash scripts/01.harness/artifact-metadata/check-headers/script.sh --staged
bash scripts/01.harness/check-governed-script-command-drift.sh

REPO_COMMIT_GATES_SCRIPT="${CHAT_REPO_COMMIT_GATES_SCRIPT:-${LLM_WORKBENCH_OPTIONAL_COMMIT_GATE:-scripts/repo/commit-gates/script.sh}}"

if [ -n "${REPO_COMMIT_GATES_SCRIPT//[[:space:]]/}" ] && [ -e "$REPO_COMMIT_GATES_SCRIPT" ]; then
  case "$REPO_COMMIT_GATES_SCRIPT" in
    /*|../*|*/../*|*/..|..|-*|*$'\n'*|*$'\r'*)
      echo "ERROR: refused non-repository commit extension hook: $REPO_COMMIT_GATES_SCRIPT" >&2
      exit 1
      ;;
  esac

  if [ ! -x "$REPO_COMMIT_GATES_SCRIPT" ]; then
    echo "ERROR: repository commit extension hook is not executable: $REPO_COMMIT_GATES_SCRIPT" >&2
    exit 1
  fi

  bash "$REPO_COMMIT_GATES_SCRIPT"
fi

BRANCH="$(git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

FAILURES=0

fail() {
  echo "ERROR: $*" >&2
  FAILURES=$((FAILURES + 1))
}

section_has_recorded_entry() {
  local section="$1"

  awk -v section="$section" '
    $0 == section {
      in_section = 1
      next
    }
    in_section && /^## / {
      exit
    }
    in_section && $0 != "" && $0 != "- None recorded yet." {
      found = 1
    }
    END {
      exit found ? 0 : 1
    }
  ' "$LOG_FILE"
}

field_value() {
  local label="$1"
  sed -n "s/^${label}: //p" "$LOG_FILE" | tail -n 1
}

adr_paths() {
  awk '
    $0 == "## ADR Disposition" {
      in_section = 1
      next
    }
    in_section && /^## / {
      exit
    }
    in_section && /^ADR path: / {
      path = substr($0, 11)
      if (path != "") {
        print path
      }
      next
    }
    in_section && /^ADR paths:$/ {
      in_paths = 1
      next
    }
    in_section && in_paths && /^- / {
      print substr($0, 3)
      next
    }
    in_section && in_paths && /^[^[:space:]-]/ {
      in_paths = 0
    }
  ' "$LOG_FILE"
}

is_governed_adr_path() {
  local path="$1"

  case "$path" in
    docs/[0-9][0-9].*/adrs/*.md|docs/*/architecture/adrs/*.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

require_section_entry() {
  local section="$1"
  local description="$2"

  if ! section_has_recorded_entry "$section"; then
    fail "$description is still missing in $LOG_FILE"
  fi
}

require_section_entry "## Initial Intent" "Initial intent"
require_section_entry "## Decisions Made" "Decisions made summary"
require_section_entry "## Context Hygiene" "Context hygiene summary"
require_section_entry "## ADR Disposition" "ADR disposition"

ADR_NEEDED="$(field_value "ADR needed")"
ADR_REASON="$(field_value "Reason")"
ADR_PATHS=()

while IFS= read -r adr_path; do
  ADR_PATHS+=("$adr_path")
done < <(adr_paths)

case "$ADR_NEEDED" in
  yes)
    if [ "${#ADR_PATHS[@]}" -eq 0 ]; then
      fail "ADR needed is yes, but ADR path is empty"
    else
      for ADR_PATH in "${ADR_PATHS[@]}"; do
        if ! is_governed_adr_path "$ADR_PATH"; then
          fail "ADR path must be under docs/<numbered-layer>/adrs/ or docs/<track>/architecture/adrs/: $ADR_PATH"
        elif [ ! -f "$ADR_PATH" ]; then
          fail "ADR path does not exist: $ADR_PATH"
        fi
      done
    fi

    if [ -z "${ADR_REASON// }" ]; then
      fail "ADR needed is yes, but reason is empty"
    fi
    ;;
  no)
    if [ -z "${ADR_REASON// }" ]; then
      fail "ADR needed is no, but reason is empty"
    fi
    ;;
  *)
    fail "ADR needed must be yes or no, got: ${ADR_NEEDED:-missing}"
    ;;
esac

if [ "$FAILURES" -gt 0 ]; then
  echo "Chat session is not ready for commit." >&2
  exit 1
fi

echo "Chat session is ready for commit: $LOG_FILE"
