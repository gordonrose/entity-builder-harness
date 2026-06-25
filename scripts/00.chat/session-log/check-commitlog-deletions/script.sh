#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.check-commitlog-deletions
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Block staged deletion of commit logs that record committed work.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.check-commitlog-deletions.readme
#     path: scripts/00.chat/session-log/check-commitlog-deletions/README.md
#   - id: chat.script.session-log.check-commitlog-deletions.smoke-test
#     path: scripts/00.chat/session-log/check-commitlog-deletions/smoke-test.sh
#   - id: harness.architecture.adr.0010-protect-commit-logs-with-recorded-work
#     path: docs/harness/architecture/adrs/0010-protect-commit-logs-with-recorded-work.md
#   effects:
#   - read-only
usage() {
  cat <<'EOF'
Usage:
  check-commitlog-deletions.sh

Blocks staged deletion of commit logs that record committed work or are
explicitly marked for retention. Empty, unsaved session logs may be deleted by
an intentional cleanup commit.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ $# -ne 0 ]; then
  usage >&2
  exit 2
fi

FAILURES=0

fail() {
  echo "ERROR: $*" >&2
  FAILURES=$((FAILURES + 1))
}

staged_deleted_commit_logs() {
  git diff --cached --name-only --diff-filter=D -- 'commitLogs/**/README.md'
}

head_content() {
  local path="$1"
  git show "HEAD:${path}" 2>/dev/null || true
}

has_recorded_commit() {
  local content="$1"

  if printf '%s\n' "$content" | grep -Eq '^latest_commit_sha: +[^[:space:]]+'; then
    return 0
  fi

  if printf '%s\n' "$content" | awk '
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
  '; then
    return 0
  fi

  return 1
}

has_retention_marker() {
  local content="$1"

  printf '%s\n' "$content" | grep -Eiq \
    '^(saved|retain|retained|preserve|preserved|keep|kept): +(yes|true)$|agentic-(save|saved|retain|retained|preserve|preserved|keep|kept)-log'
}

while IFS= read -r path; do
  if [ -z "${path// }" ]; then
    continue
  fi

  content="$(head_content "$path")"

  if [ -z "${content// }" ]; then
    fail "cannot inspect deleted commit log from HEAD: $path"
    continue
  fi

  if has_recorded_commit "$content"; then
    fail "cannot delete commit log with recorded commits: $path"
    continue
  fi

  if has_retention_marker "$content"; then
    fail "cannot delete commit log marked for retention: $path"
    continue
  fi
done < <(staged_deleted_commit_logs)

if [ "$FAILURES" -gt 0 ]; then
  echo "Commit log deletion gate failed." >&2
  echo "Restore protected logs or remove them from the staged deletion set." >&2
  exit 1
fi

echo "Commit log deletion gate passed."
