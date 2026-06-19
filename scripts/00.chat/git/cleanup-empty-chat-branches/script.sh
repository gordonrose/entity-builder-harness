#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Delete empty chat branches and matching empty session logs after dry-run inspection.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-cleanup.md
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/chat/cleanup-empty-chat-branches.sh
#     - scripts/shared/chat/request-initialization/start-chat-session.sh
#   effects: branches, writes-files, destructive

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

MODE="dry-run"
BASE_BRANCH=""

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

  metadata="$(sed -n '/<!-- agentic-session/,/-->/p' "$log_file")"

  if [ -n "$metadata" ]; then
    printf '%s\n' "$metadata" | grep -Fxq "branch: ${branch}"
    return
  fi

  grep -Fxq "\`${branch}\`" "$log_file"
}

log_has_recorded_commit() {
  local log_file="$1"

  if sed -n '/<!-- agentic-session/,/-->/s/^latest_commit_sha: //p' "$log_file" \
    | grep -Eq '[^[:space:]]'; then
    return 0
  fi

  awk '
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

  grep -Eiq \
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
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

current_branch="$(git branch --show-current)"

if [ -z "$current_branch" ]; then
  echo "ERROR: current HEAD is detached; refusing cleanup." >&2
  exit 1
fi

if [ -z "$BASE_BRANCH" ]; then
  if git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    BASE_BRANCH="master"
  else
    echo "ERROR: could not infer base branch. Pass --base <branch>." >&2
    exit 1
  fi
fi

if ! git rev-parse --verify --quiet "$BASE_BRANCH" >/dev/null; then
  echo "ERROR: base branch does not exist: $BASE_BRANCH" >&2
  exit 1
fi

deleted_count=0
skipped_count=0

echo "Mode: $MODE"
echo "Base branch: $BASE_BRANCH"
echo "Current branch: $current_branch"

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

  if git worktree list --porcelain \
    | awk -v branch="refs/heads/${branch}" '/^branch / && substr($0, 8) == branch { found = 1 } END { exit found ? 0 : 1 }'; then
    echo "SKIP checked-out worktree branch: $branch"
    skipped_count=$((skipped_count + 1))
    continue
  fi

  ahead_count="$(git rev-list --count "${BASE_BRANCH}..${branch}")"
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
      elif log_has_retention_marker "$log_file"; then
        keep_log_reason="retention marker"
      else
        delete_log="yes"
      fi
    else
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
    git branch -D "$branch"
    if [ "$delete_log" = "yes" ]; then
      git rm -r --ignore-unmatch "$log_dir" >/dev/null
      rm -rf "$log_dir"
    fi
    echo "Deleted empty branch: $branch"
    if [ "$delete_log" = "yes" ]; then
      echo "Deleted matching log: $log_dir"
    elif [ -n "$keep_log_reason" ]; then
      echo "Kept matching log (${keep_log_reason}): $log_dir"
    fi
  fi

  deleted_count=$((deleted_count + 1))
done < <(git branch --format='%(refname:short)')

echo "Empty chat branches found: $deleted_count"
echo "Branches skipped: $skipped_count"
