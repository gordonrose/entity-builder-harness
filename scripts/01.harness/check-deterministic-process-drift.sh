#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Flag process prose that should likely be represented as deterministic scripts or gates.
#   domain: governance
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - .agentic/shared/workflows/change-shared-process.md
#   effects: read-only

MODE=""
COMMIT_SHA=""
PATH_ARGS=()

usage() {
  cat <<'EOF'
Usage:
  check-deterministic-process-drift.sh --staged
  check-deterministic-process-drift.sh --commit <sha>
  check-deterministic-process-drift.sh --paths <path> [path...]
  check-deterministic-process-drift.sh --all

Flags harness process prose that looks like it could be represented by a
deterministic script or gate. The check suggests changes only; it never rewrites
files.

Allow intentional governance prose with:
  <!-- deterministic-check: allow reason="requires human approval judgment" -->
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --staged|--all)
      if [ -n "$MODE" ]; then
        echo "ERROR: choose exactly one mode." >&2
        exit 2
      fi
      MODE="${1#--}"
      shift
      ;;
    --commit)
      if [ -n "$MODE" ]; then
        echo "ERROR: choose exactly one mode." >&2
        exit 2
      fi
      if [ $# -lt 2 ] || [ -z "${2:-}" ]; then
        echo "ERROR: --commit requires a commit sha." >&2
        exit 2
      fi
      MODE="commit"
      COMMIT_SHA="$2"
      shift 2
      ;;
    --paths)
      if [ -n "$MODE" ]; then
        echo "ERROR: choose exactly one mode." >&2
        exit 2
      fi
      MODE="paths"
      shift
      if [ $# -eq 0 ]; then
        echo "ERROR: --paths requires at least one path." >&2
        exit 2
      fi
      while [ $# -gt 0 ]; do
        PATH_ARGS+=("$1")
        shift
      done
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

if [ -z "$MODE" ]; then
  usage >&2
  exit 2
fi

is_scannable_path() {
  local path="$1"

  case "$path" in
    docs/harness/architecture/adrs/*.md)
      return 1
      ;;
    AGENTS.md|.agentic/*.md|.agentic/**/*.md|docs/harness/*.md|docs/harness/**/*.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

collect_all_paths() {
  {
    [ -f AGENTS.md ] && printf '%s\n' AGENTS.md
    [ -d .agentic ] && find .agentic -type f
    [ -d docs/harness ] && find docs/harness -type f
  } | sort -u
}

collect_paths_from_args() {
  local path

  for path in "${PATH_ARGS[@]}"; do
    if [ -d "$path" ]; then
      find "$path" -type f
    elif [ -f "$path" ]; then
      printf '%s\n' "$path"
    else
      echo "WARN: path does not exist, skipping: $path" >&2
    fi
  done | sort -u
}

scan_file_content() {
  local source_path="$1"
  local content_file="$2"

  awk -v source="$source_path" '
    function finding(type, text) {
      printf "%s:%d\n", source, NR
      printf "  Type: %s\n", type
      printf "  Text: %s\n", text
      printf "  Suggestion: Move deterministic checks into a script or gate, or add an allow marker with a reason when the prose is intentionally human-governed.\n\n"
      findings++
    }

    /```/ {
      in_code = !in_code
      next
    }

    /deterministic-check: allow/ {
      if ($0 !~ /reason="[^"]+"/) {
        finding("allow-marker-missing-reason", $0)
      }
      allow_until = NR + 8
      next
    }

    in_code {
      next
    }

    NR <= allow_until {
      next
    }

    {
      line = $0
      lower = tolower(line)
    }

    lower ~ /(check|verify|ensure|confirm) that / {
      finding("scriptable-check", line)
      next
    }

    lower ~ /(current branch contains|file exists|files exist|path exists|if .*missing|if .*dirty|if .*exists|when .*missing|must contain)/ {
      finding("scriptable-condition", line)
      next
    }

    lower ~ /(run .*(and|then).*(inspect|check|verify|confirm)|rerun .*(checklist|gate|script))/ {
      finding("scriptable-sequence", line)
      next
    }

    lower ~ /^[-0-9. ]+(check|verify|ensure|confirm|inspect) / {
      procedural_bullets++
      if (procedural_bullets == 3) {
        finding("scriptable-enumeration", "Three or more nearby checklist items begin with deterministic process verbs.")
      }
      next
    }

    line !~ /^[-0-9. ]/ {
      procedural_bullets = 0
    }

    END {
      exit findings > 0 ? 1 : 0
    }
  ' "$content_file"
}

scan_worktree_file() {
  local path="$1"
  local result

  if ! is_scannable_path "$path"; then
    return 0
  fi

  set +e
  scan_file_content "$path" "$path"
  result=$?
  set -e
  return "$result"
}

scan_git_blob() {
  local ref="$1"
  local path="$2"
  local tmp

  if ! is_scannable_path "$path"; then
    return 0
  fi

  tmp="$(mktemp)"
  if ! git show "${ref}:${path}" > "$tmp" 2>/dev/null; then
    rm -f "$tmp"
    return 0
  fi

  set +e
  scan_file_content "$path" "$tmp"
  local result=$?
  set -e
  rm -f "$tmp"
  return "$result"
}

scan_diff_added_lines() {
  local source_path="$1"
  local diff_file="$2"

  if ! is_scannable_path "$source_path"; then
    return 0
  fi

  awk -v source="$source_path" '
    function finding(type, text) {
      printf "%s:%d\n", source, line_no
      printf "  Type: %s\n", type
      printf "  Text: %s\n", text
      printf "  Suggestion: Move deterministic checks into a script or gate, or add an allow marker with a reason when the prose is intentionally human-governed.\n\n"
      findings++
    }

    function scan_added_line(text, lower) {
      if (text ~ /```/) {
        in_code = !in_code
        return
      }

      if (text ~ /deterministic-check: allow/) {
        if (text !~ /reason="[^"]+"/) {
          finding("allow-marker-missing-reason", text)
        }
        allow_until = line_no + 8
        return
      }

      if (in_code || line_no <= allow_until) {
        return
      }

      lower = tolower(text)

      if (lower ~ /(check|verify|ensure|confirm) that /) {
        finding("scriptable-check", text)
        return
      }

      if (lower ~ /(current branch contains|file exists|files exist|path exists|if .*missing|if .*dirty|if .*exists|when .*missing|must contain)/) {
        finding("scriptable-condition", text)
        return
      }

      if (lower ~ /(run .*(and|then).*(inspect|check|verify|confirm)|rerun .*(checklist|gate|script))/) {
        finding("scriptable-sequence", text)
        return
      }

      if (lower ~ /^[-0-9. ]+(check|verify|ensure|confirm|inspect) /) {
        procedural_bullets++
        if (procedural_bullets == 3) {
          finding("scriptable-enumeration", "Three or more nearby added checklist items begin with deterministic process verbs.")
        }
        return
      }

      if (text !~ /^[-0-9. ]/) {
        procedural_bullets = 0
      }
    }

    /^@@ / {
      hunk = $0
      sub(/^.* \+/, "", hunk)
      sub(/ .*/, "", hunk)
      split(hunk, parts, ",")
      line_no = parts[1] - 1
      next
    }

    /^\+\+\+ / {
      next
    }

    /^\+/ {
      line_no++
      scan_added_line(substr($0, 2))
      next
    }

    /^ / {
      line_no++
      next
    }

    END {
      exit findings > 0 ? 1 : 0
    }
  ' "$diff_file"
}

TOTAL_FINDINGS=0

scan_path_list() {
  local path

  while IFS= read -r path; do
    if [ -z "${path// }" ]; then
      continue
    fi

    if ! scan_worktree_file "$path"; then
      TOTAL_FINDINGS=$((TOTAL_FINDINGS + 1))
    fi
  done
}

case "$MODE" in
  staged)
    while IFS= read -r path; do
      if [ -z "${path// }" ]; then
        continue
      fi

      tmp="$(mktemp)"
      git diff --cached -U0 --no-ext-diff -- "$path" > "$tmp"
      if ! scan_diff_added_lines "$path" "$tmp"; then
        TOTAL_FINDINGS=$((TOTAL_FINDINGS + 1))
      fi
      rm -f "$tmp"
    done < <(git diff --cached --name-only --diff-filter=ACMR)
    ;;
  commit)
    if ! git rev-parse --verify --quiet "$COMMIT_SHA" >/dev/null; then
      echo "ERROR: commit does not exist: $COMMIT_SHA" >&2
      exit 2
    fi

    while IFS= read -r path; do
      if [ -z "${path// }" ]; then
        continue
      fi

      tmp="$(mktemp)"
      git show --format= --unified=0 --no-ext-diff "$COMMIT_SHA" -- "$path" > "$tmp"
      if ! scan_diff_added_lines "$path" "$tmp"; then
        TOTAL_FINDINGS=$((TOTAL_FINDINGS + 1))
      fi
      rm -f "$tmp"
    done < <(git diff-tree --no-commit-id --name-only -r "$COMMIT_SHA")
    ;;
  paths)
    scan_path_list < <(collect_paths_from_args)
    ;;
  all)
    scan_path_list < <(collect_all_paths)
    ;;
  *)
    echo "ERROR: unsupported mode: $MODE" >&2
    exit 2
    ;;
esac

if [ "$TOTAL_FINDINGS" -gt 0 ]; then
  echo "ERROR: deterministic process drift found." >&2
  echo "Review the suggestions, then either move deterministic procedure into a script/gate or add an allow marker with a reason." >&2
  exit 1
fi

echo "No deterministic process drift found."
