#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Dry-run the file and package merge plan for bootstrapping llm-workbench.
#   domain: upstream
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/upstream/bootstrap-llm-workbench-repo/README.md
#     - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   effects: read-only

usage() {
  cat <<'EOF'
Usage:
  bootstrap-llm-workbench-repo.sh --target <git-repo> --dry-run

Plans how the portable chat workbench would be materialized into a target Git
repo. This implementation is dry-run only and writes nothing to the target.
EOF
}

TARGET_REPO=""
DRY_RUN="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      TARGET_REPO="${2:-}"
      if [ -z "$TARGET_REPO" ]; then
        echo "ERROR: --target requires a value." >&2
        exit 2
      fi
      shift 2
      ;;
    --dry-run)
      DRY_RUN="yes"
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

if [ -z "$TARGET_REPO" ] || [ "$DRY_RUN" != "yes" ]; then
  usage >&2
  exit 2
fi

if [ ! -d "$TARGET_REPO/.git" ]; then
  echo "ERROR: target is not a Git repo: $TARGET_REPO" >&2
  exit 1
fi

SOURCE_REPO="$(git rev-parse --show-toplevel)"
TEMPLATE_ROOT="$SOURCE_REPO/docs/harness/bootstrap/llm-workbench-template/root"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/llm-workbench-bootstrap-plan.XXXXXX")"
PLAN_PATHS="$TMP_DIR/planned-paths.txt"
PACKAGE_OUTPUT="$TMP_DIR/package-output.txt"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

: > "$PLAN_PATHS"

CREATE_COUNT=0
SAME_COUNT=0
CONFLICT_COUNT=0
PRESERVE_COUNT=0
PACKAGE_CONFLICTS="no"

print_header() {
  local head
  local branch

  head="$(git -C "$TARGET_REPO" rev-parse --verify HEAD 2>/dev/null || true)"
  branch="$(git -C "$TARGET_REPO" branch --show-current 2>/dev/null || true)"

  echo "llm-workbench bootstrap dry-run"
  echo
  echo "Source repo: $SOURCE_REPO"
  echo "Target repo: $TARGET_REPO"
  echo "Target branch: ${branch:-<none>}"
  echo "Target HEAD: ${head:-<unborn>}"
  echo
}

plan_file() {
  local source="$1"
  local relative_path="$2"
  local target="$TARGET_REPO/$relative_path"

  printf '%s\n' "$relative_path" >> "$PLAN_PATHS"

  if [ -e "$target" ]; then
    if cmp -s "$source" "$target"; then
      echo "SAME $relative_path"
      SAME_COUNT=$((SAME_COUNT + 1))
    else
      echo "CONFLICT $relative_path"
      CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
    fi
  else
    echo "CREATE $relative_path"
    CREATE_COUNT=$((CREATE_COUNT + 1))
  fi
}

plan_tree() {
  local tree="$1"
  local file
  local relative_path

  [ -d "$SOURCE_REPO/$tree" ] || return 0

  while IFS= read -r file; do
    relative_path="${file#$SOURCE_REPO/}"
    plan_file "$file" "$relative_path"
  done < <(find "$SOURCE_REPO/$tree" -type f | sort)
}

plan_selected_file() {
  local path="$1"

  [ -f "$SOURCE_REPO/$path" ] || return 0
  plan_file "$SOURCE_REPO/$path" "$path"
}

plan_templates() {
  local file
  local relative_template
  local relative_path

  while IFS= read -r file; do
    relative_template="${file#$TEMPLATE_ROOT/}"
    relative_path="${relative_template%.template}"

    if [ "$relative_path" = "package.json" ]; then
      continue
    fi

    plan_file "$file" "$relative_path"
  done < <(find "$TEMPLATE_ROOT" -type f -name '*.template' | sort)
}

plan_package_json() {
  local target_package="$TARGET_REPO/package.json"
  local template_package="$TEMPLATE_ROOT/package.json.template"

  printf '%s\n' "package.json" >> "$PLAN_PATHS"

  if [ ! -f "$target_package" ]; then
    echo "CREATE package.json"
    CREATE_COUNT=$((CREATE_COUNT + 1))
    return 0
  fi

  if ! node - "$target_package" "$template_package" > "$PACKAGE_OUTPUT" <<'NODE'
const fs = require('fs');
const targetPath = process.argv[2];
const templatePath = process.argv[3];

let target;
let template;

try {
  target = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
} catch (error) {
  console.log(`CONFLICT package.json invalid-json ${error.message}`);
  process.exit(1);
}

try {
  template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));
} catch (error) {
  console.log(`CONFLICT package.json template-invalid-json ${error.message}`);
  process.exit(1);
}

const actualScripts = target.scripts || {};
const expectedScripts = template.scripts || {};
let conflicts = 0;

for (const [name, expected] of Object.entries(expectedScripts)) {
  const actual = actualScripts[name];
  if (actual === undefined) {
    console.log(`PACKAGE_ADD_SCRIPT ${name} ${expected}`);
  } else if (actual === expected) {
    console.log(`PACKAGE_SAME_SCRIPT ${name}`);
  } else {
    console.log(`PACKAGE_CONFLICT_SCRIPT ${name} actual=${actual} expected=${expected}`);
    conflicts += 1;
  }
}

for (const name of Object.keys(actualScripts).sort()) {
  if (expectedScripts[name] === undefined) {
    console.log(`PACKAGE_PRESERVE_SCRIPT ${name} ${actualScripts[name]}`);
  }
}

process.exit(conflicts > 0 ? 1 : 0);
NODE
  then
    PACKAGE_CONFLICTS="yes"
    CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
  fi

  cat "$PACKAGE_OUTPUT"
}

plan_preserved_target_owned_files() {
  local target_subtree
  local file
  local relative_path

  for target_subtree in ".agentic/shared" "scripts/shared"; do
    [ -d "$TARGET_REPO/$target_subtree" ] || continue

    while IFS= read -r file; do
      relative_path="${file#$TARGET_REPO/}"
      if ! grep -Fxq "$relative_path" "$PLAN_PATHS"; then
        echo "PRESERVE $relative_path"
        PRESERVE_COUNT=$((PRESERVE_COUNT + 1))
      fi
    done < <(find "$TARGET_REPO/$target_subtree" -type f | sort)
  done
}

print_header

echo "Package plan:"
plan_package_json
echo

echo "File plan:"
plan_templates
plan_tree ".agentic/00.chat"
plan_tree ".agentic/shared/checklists"
plan_tree ".agentic/shared/gates"
plan_tree ".agentic/shared/standards"
plan_tree ".agentic/shared/workflows"
plan_tree ".agentic/harness"
plan_tree "scripts/00.chat"
plan_tree "scripts/shared/harness"
plan_selected_file "docs/harness/architecture/script-layout.md"
plan_selected_file "docs/harness/architecture/chat-workbench-public-repo-readiness.md"
plan_selected_file "docs/harness/architecture/adrs/README.md"
plan_selected_file "docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md"
plan_selected_file "docs/harness/architecture/adrs/0002-clean-up-duplicate-chat-branches.md"
plan_selected_file "docs/harness/architecture/adrs/0003-review-process-prose-for-deterministic-gates.md"
plan_selected_file "docs/harness/architecture/adrs/0004-group-chat-logs-and-summarize-session-metrics.md"
plan_selected_file "docs/harness/architecture/adrs/0005-preserve-bootstrap-dirty-worktree-before-workflow-loading.md"
plan_selected_file "docs/harness/architecture/adrs/0006-use-session-metadata-for-routing-after-chat-start.md"
plan_selected_file "docs/harness/architecture/adrs/0007-require-explicit-write-permission-with-bookkeeping-exception.md"
plan_selected_file "docs/harness/architecture/adrs/0009-allow-automatic-session-branch-commit-context.md"
plan_selected_file "docs/harness/architecture/adrs/0010-protect-commit-logs-with-recorded-work.md"
plan_selected_file "docs/harness/architecture/adrs/0011-use-chat-owned-worktrees-for-local-convergence.md"
plan_selected_file "docs/harness/architecture/adrs/0012-treat-missing-governance-as-stop-condition.md"
plan_selected_file "docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md"
plan_selected_file "docs/harness/architecture/adrs/0014-promote-reusable-lessons-upstream.md"
plan_selected_file "docs/harness/architecture/adrs/0015-use-shared-upstream-repo-bootstrap-standard.md"
plan_selected_file "docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md"
plan_preserved_target_owned_files
echo

echo "Excluded source paths:"
echo "EXCLUDE commitLogs/"
echo "EXCLUDE .agentic/product/"
echo "EXCLUDE .agentic/education/"
echo "EXCLUDE .agentic/aws/"
echo "EXCLUDE product src/, app tests, deployment docs, local transcripts, and local worktree paths"
echo

echo "Summary:"
echo "create: $CREATE_COUNT"
echo "same: $SAME_COUNT"
echo "preserve: $PRESERVE_COUNT"
echo "conflicts: $CONFLICT_COUNT"
echo "package_conflicts: $PACKAGE_CONFLICTS"
echo "mode: dry-run"

if [ "$CONFLICT_COUNT" -gt 0 ]; then
  exit 1
fi
