#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: shared-harness
#   purpose: Verify metadata headers on newly added or selected harness artifacts.
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/harness/standards/artifact-metadata-headers.md
#     - .agentic/00.chat/checklists/before-commit.md
#   effects: read-only

MODE=""
PATH_ARGS=()

usage() {
  cat <<'EOF'
Usage:
  check-artifact-metadata-headers.sh --staged-added
  check-artifact-metadata-headers.sh --paths <path> [path...]
  check-artifact-metadata-headers.sh --all

Checks scripts and harness Markdown documents for required agentic metadata
headers. --staged-added enforces only newly added files so existing files can be
backfilled in batches.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --staged-added|--all)
      if [ -n "$MODE" ]; then
        echo "ERROR: choose exactly one mode." >&2
        exit 2
      fi
      MODE="${1#--}"
      shift
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

if [ -z "$MODE" ]; then
  usage >&2
  exit 2
fi

is_script_artifact() {
  case "$1" in
    scripts/*.sh|scripts/**/*.sh|scripts/*.js|scripts/**/*.js)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_markdown_artifact() {
  case "$1" in
    .agentic/*.md|.agentic/**/*.md|docs/harness/*.md|docs/harness/**/*.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_relevant_path() {
  is_script_artifact "$1" || is_markdown_artifact "$1"
}

collect_staged_added_paths() {
  git diff --cached --name-status --diff-filter=ACR \
    | awk '
      $1 == "R" || $1 ~ /^R[0-9]+$/ { print $3; next }
      { print $2 }
    ' \
    | sort -u
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

collect_all_paths() {
  {
    [ -d scripts ] && find scripts -type f
    [ -d .agentic ] && find .agentic -type f -name '*.md'
    [ -d docs/harness ] && find docs/harness -type f -name '*.md'
  } | sort -u
}

header_block() {
  local path="$1"
  sed -n '1,40p' "$path"
}

validate_used_by_paths() {
  local path="$1"
  local line
  local ref
  local failures=0

  while IFS= read -r line; do
    ref="$line"
    ref="${ref#\#}"
    ref="${ref#//}"
    ref="${ref#  }"
    ref="${ref#  - }"
    ref="${ref#- }"
    ref="${ref%% *}"
    ref="${ref%%	*}"

    [ -n "$ref" ] || continue
    case "$ref" in
      AGENTS.md|.agentic/*|docs/harness/*|scripts/*)
        if [ ! -e "$ref" ]; then
          echo "ERROR: $path references missing used_by path: $ref" >&2
          failures=$((failures + 1))
        fi
        ;;
    esac
  done < <(header_block "$path" | grep -E '^[#/]?[[:space:]]*- (AGENTS.md|\.agentic/|docs/harness/|scripts/)' || true)

  return "$failures"
}

check_script_header() {
  local path="$1"
  local header

  header="$(header_block "$path")"

  if ! printf '%s\n' "$header" | grep -q 'agentic-script:'; then
    echo "ERROR: missing agentic-script metadata header: $path" >&2
    return 1
  fi

  for field in owner purpose portability used_by effects; do
    if ! printf '%s\n' "$header" | grep -Eq "^(#|//)[[:space:]]+${field}:"; then
      echo "ERROR: missing ${field} in script metadata header: $path" >&2
      return 1
    fi
  done

  if ! printf '%s\n' "$header" | grep -Eq 'portability: (llm-workbench-required|llm-workbench-validation|llm-workbench-compatibility|source-only|internal)$'; then
    echo "ERROR: invalid portability value in script metadata header: $path" >&2
    return 1
  fi

  validate_used_by_paths "$path"
}

check_markdown_header() {
  local path="$1"
  local header

  header="$(header_block "$path")"

  if ! printf '%s\n' "$header" | grep -q 'agentic-artifact:'; then
    echo "ERROR: missing agentic-artifact metadata header: $path" >&2
    return 1
  fi

  for field in owner kind purpose portability used_by; do
    if ! printf '%s\n' "$header" | grep -Eq "^${field}:"; then
      echo "ERROR: missing ${field} in artifact metadata header: $path" >&2
      return 1
    fi
  done

  if ! printf '%s\n' "$header" | grep -Eq '^portability: (llm-workbench-required|llm-workbench-validation|llm-workbench-compatibility|source-only|internal)$'; then
    echo "ERROR: invalid portability value in artifact metadata header: $path" >&2
    return 1
  fi

  validate_used_by_paths "$path"
}

case "$MODE" in
  staged-added)
    PATHS="$(collect_staged_added_paths)"
    ;;
  paths)
    PATHS="$(collect_paths_from_args)"
    ;;
  all)
    PATHS="$(collect_all_paths)"
    ;;
esac

FAILURES=0
CHECKED=0

while IFS= read -r path; do
  [ -n "$path" ] || continue
  is_relevant_path "$path" || continue
  [ -f "$path" ] || continue

  CHECKED=$((CHECKED + 1))
  if is_script_artifact "$path"; then
    check_script_header "$path" || FAILURES=$((FAILURES + 1))
  elif is_markdown_artifact "$path"; then
    check_markdown_header "$path" || FAILURES=$((FAILURES + 1))
  fi
done <<< "$PATHS"

if [ "$FAILURES" -gt 0 ]; then
  echo "Artifact metadata header check failed: $FAILURES file(s)." >&2
  exit 1
fi

echo "Artifact metadata headers passed for $CHECKED file(s)."
