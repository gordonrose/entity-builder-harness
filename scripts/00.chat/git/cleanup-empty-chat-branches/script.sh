#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.git.cleanup-empty-chat-branches
#   version: 2
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: git
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Delete empty chat branches and matching empty session logs after dry-run
#     inspection.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-cleanup
#     path: .agentic/00.chat/workflows/chat-cleanup.md
#   - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
#   - id: chat.script.startup.start-chat-session
#     path: scripts/00.chat/startup/start-chat-session/script.sh
#   effects:
#   - branches
#   - destructive
#   - writes-files

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

MODE="dry-run"
BASE_BRANCH=""

read_failed() { echo "ERROR: cleanup-$1-read-failed" >&2; return 2; }
observe() {
  local stage="$1"
  shift
  "$@" 2>/dev/null || read_failed "$stage"
}
matches() {
  local stage="$1" status
  shift
  if "$@" 2>/dev/null; then return 0; else status=$?; fi
  [ "$status" -ne 1 ] || return 1
  read_failed "$stage"
}
perform_cleanup() {
  local stage="$1" output status
  shift
  if output="$("$@" 2>/dev/null)"; then
    [ -z "$output" ] || printf '%s\n' "$output"
  else
    status=$?
    echo "ERROR: cleanup-$stage-failed; effect=unknown; inspect branches and logs before retrying" >&2
    exit "$status"
  fi
}

usage() {
  cat <<'EOF'
Usage: cleanup-empty-chat-branches.sh [--dry-run|--apply] [--base <branch>]

Deletes empty chat branches and their matching empty commitLogs directories.

Safety:
- Dry-run is the default.
- --apply is required to delete branches or commitLogs.
- The current branch is never deleted.
- Branches checked out in any worktree are never deleted by this script.
- Only chat/* branches are considered.
- A branch is empty when it has no commits beyond the base branch.
- commitLogs/<yyyy>/<mmm>/<dd>/<session> or legacy commitLogs/<session> is
  deleted only when it names the same branch and has no recorded commits or
  retention marker.
EOF
}

log_names_branch() {
  local log_file="$1"
  local branch="$2"
  local metadata

  metadata="$(observe log-metadata sed -n '/<!-- agentic-session/,/-->/p' "$log_file")" || return 2

  if [ -n "$metadata" ]; then
    matches log-branch grep -Fxq -- "branch: ${branch}" <<< "$metadata"
    return
  fi

  matches log-branch grep -Fxq -- "\`${branch}\`" "$log_file"
}

log_has_recorded_commit() {
  local log_file="$1" recorded status

  recorded="$(observe log-commit sed -n '/<!-- agentic-session/,/-->/s/^latest_commit_sha: //p' "$log_file")" || return 2
  if matches log-commit grep -Eq '[^[:space:]]' <<< "$recorded"; then
    return 0
  else
    status=$?
    [ "$status" -eq 1 ] || return "$status"
  fi

  matches log-commit awk '
    $0 == "## Commits" {
      in_section = 1
      next
    }
    in_section && /^## / {
      exit
    }
    in_section && /^- Commit: `[^`]+`/ {
      found = 1
    }
    in_section && /^Commit: `[^`]+`/ {
      found = 1
    }
    END {
      exit found ? 0 : 1
    }
  ' "$log_file"
}

log_has_retention_marker() {
  local log_file="$1"

  matches log-retention grep -Eiq \
    '^(saved|retain|retained|preserve|preserved|keep|kept): +(yes|true)$|agentic-(save|saved|retain|retained|preserve|preserved|keep|kept)-log' \
    "$log_file"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --apply)
      MODE="apply"
      shift
      ;;
    --base)
      if [ $# -lt 2 ] || [ -z "${2:-}" ]; then
        echo "ERROR: --base requires a branch name." >&2
        exit 2
      fi
      BASE_BRANCH="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument" >&2
      usage >&2
      exit 2
      ;;
  esac
done

current_branch="$(observe branch git branch --show-current)"

if [ -z "$current_branch" ]; then
  echo "ERROR: current HEAD is detached; refusing cleanup." >&2
  exit 1
fi

if [ -z "$BASE_BRANCH" ]; then
  if matches base-reference git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
  else
    reference_status=$?
    [ "$reference_status" -eq 1 ] || exit "$reference_status"
    if matches base-reference git show-ref --verify --quiet refs/heads/master; then
      BASE_BRANCH="master"
    else
      reference_status=$?
      [ "$reference_status" -eq 1 ] || exit "$reference_status"
      echo "ERROR: could not infer base branch. Pass --base <branch>." >&2
      exit 1
    fi
  fi
fi

if ! git rev-parse --verify --quiet "$BASE_BRANCH" >/dev/null 2>&1; then
  echo "ERROR: base branch could not be resolved" >&2
  exit 1
fi

deleted_count=0
skipped_count=0

echo "Mode: $MODE"
echo "Base branch: $BASE_BRANCH"
echo "Current branch: $current_branch"

branches="$(observe branch-list git branch --format='%(refname:short)')"
while IFS= read -r branch; do
  case "$branch" in
    chat/*)
      ;;
    *)
      continue
      ;;
  esac

  if [ "$branch" = "$current_branch" ]; then
    echo "SKIP current branch: $branch"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  worktrees="$(observe worktree-list git worktree list --porcelain)"
  if matches worktree-match awk -v branch="refs/heads/${branch}" '/^branch / && substr($0, 8) == branch { found = 1 } END { exit found ? 0 : 1 }' <<< "$worktrees"; then
    echo "SKIP checked-out worktree branch: $branch"
    skipped_count=$((skipped_count + 1))
    continue
  else
    worktree_status=$?
    [ "$worktree_status" -eq 1 ] || exit "$worktree_status"
  fi

  ahead_count="$(observe comparison git rev-list --count "${BASE_BRANCH}..${branch}")"
  if [ "$ahead_count" != "0" ]; then
    echo "SKIP non-empty branch: $branch ($ahead_count commits ahead of $BASE_BRANCH)"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  session="${branch#chat/}"
  log_dir="$(chat_log_dir_for_session "$session")"
  log_file="${log_dir}/README.md"
  delete_log="no"
  keep_log_reason=""

  if [ -f "$log_file" ]; then
    if log_names_branch "$log_file" "$branch"; then
      if log_has_recorded_commit "$log_file"; then
        keep_log_reason="recorded commits"
      else
        log_status=$?
        [ "$log_status" -eq 1 ] || exit "$log_status"
        if log_has_retention_marker "$log_file"; then
          keep_log_reason="retention marker"
        else
          log_status=$?
          [ "$log_status" -eq 1 ] || exit "$log_status"
          delete_log="yes"
        fi
      fi
    else
      log_status=$?
      [ "$log_status" -eq 1 ] || exit "$log_status"
      echo "WARN log branch mismatch, leaving log in place: $log_dir"
    fi
  elif [ -e "$log_dir" ]; then
    echo "WARN commit log path exists without README, leaving in place: $log_dir"
  fi

  if [ "$MODE" = "dry-run" ]; then
    echo "DRY-RUN delete branch: $branch"
    if [ "$delete_log" = "yes" ]; then
      echo "DRY-RUN delete log: $log_dir"
    elif [ -n "$keep_log_reason" ]; then
      echo "DRY-RUN keep log (${keep_log_reason}): $log_dir"
    fi
  else
    perform_cleanup delete-branch git branch -D "$branch"
    if [ "$delete_log" = "yes" ]; then
      perform_cleanup unstage-log git rm -r --ignore-unmatch "$log_dir" >/dev/null
      perform_cleanup delete-log rm -rf "$log_dir"
    fi
    echo "Deleted empty branch: $branch"
    if [ "$delete_log" = "yes" ]; then
      echo "Deleted matching log: $log_dir"
    elif [ -n "$keep_log_reason" ]; then
      echo "Kept matching log (${keep_log_reason}): $log_dir"
    fi
  fi

  deleted_count=$((deleted_count + 1))
done <<< "$branches"

echo "Empty chat branches found: $deleted_count"
echo "Branches skipped: $skipped_count"
