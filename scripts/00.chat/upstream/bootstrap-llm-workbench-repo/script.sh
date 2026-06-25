#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.upstream.bootstrap-llm-workbench-repo
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: upstream
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Plan or apply the file and package merge for bootstrapping llm-workbench.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.upstream.bootstrap-llm-workbench-repo.readme
#     path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/README.md
#   - id: chat.workflows.bootstrap-chat-workbench-repo
#     path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   effects:
#   - read-only
#   - writes-files

usage() {
  cat <<'EOF'
Usage:
  bootstrap-llm-workbench-repo.sh --target <git-repo> --dry-run
  bootstrap-llm-workbench-repo.sh --target <git-repo> --apply

Plans or applies how the portable chat workbench is materialized into a target
Git repo. Apply mode refuses to write when the plan contains conflicts.
EOF
}

TARGET_REPO=""
MODE=""

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
      if [ -n "$MODE" ]; then
        echo "ERROR: choose exactly one mode: --dry-run or --apply." >&2
        exit 2
      fi
      MODE="dry-run"
      shift
      ;;
    --apply)
      if [ -n "$MODE" ]; then
        echo "ERROR: choose exactly one mode: --dry-run or --apply." >&2
        exit 2
      fi
      MODE="apply"
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

if [ -z "$TARGET_REPO" ] || [ -z "$MODE" ]; then
  usage >&2
  exit 2
fi

if [ ! -d "$TARGET_REPO/.git" ]; then
  echo "ERROR: target is not a Git repo: $TARGET_REPO" >&2
  exit 1
fi

SOURCE_REPO="$(git rev-parse --show-toplevel)"
TEMPLATE_ROOT="$SOURCE_REPO/docs/00.chat/bootstrap/llm-workbench-template/root"
PUBLIC_ADR_MANIFEST="$SOURCE_REPO/docs/00.chat/public-chat-workbench-adrs.md"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/llm-workbench-bootstrap-plan.XXXXXX")"
PLAN_PATHS="$TMP_DIR/planned-paths.txt"
PACKAGE_OUTPUT="$TMP_DIR/package-output.txt"
FILE_ACTIONS="$TMP_DIR/file-actions.tsv"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

: > "$PLAN_PATHS"
: > "$FILE_ACTIONS"

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

  echo "llm-workbench bootstrap ${MODE}"
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
      printf 'SAME\t%s\t%s\n' "$source" "$relative_path" >> "$FILE_ACTIONS"
      SAME_COUNT=$((SAME_COUNT + 1))
    else
      echo "CONFLICT $relative_path"
      printf 'CONFLICT\t%s\t%s\n' "$source" "$relative_path" >> "$FILE_ACTIONS"
      CONFLICT_COUNT=$((CONFLICT_COUNT + 1))
    fi
  else
    echo "CREATE $relative_path"
    printf 'CREATE\t%s\t%s\n' "$source" "$relative_path" >> "$FILE_ACTIONS"
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

plan_public_adrs() {
  local path

  if [ ! -f "$PUBLIC_ADR_MANIFEST" ]; then
    echo "ERROR: public ADR manifest missing: ${PUBLIC_ADR_MANIFEST#$SOURCE_REPO/}" >&2
    exit 1
  fi

  while IFS= read -r path; do
    case "$path" in
      docs/harness/architecture/adrs/*.md)
        plan_selected_file "$path"
        ;;
    esac
  done < "$PUBLIC_ADR_MANIFEST"
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
    printf 'CREATE_PACKAGE\t%s\tpackage.json\n' "$template_package" >> "$FILE_ACTIONS"
    CREATE_COUNT=$((CREATE_COUNT + 1))
    return 0
  fi

  printf 'MERGE_PACKAGE\t%s\tpackage.json\n' "$template_package" >> "$FILE_ACTIONS"

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
        printf 'PRESERVE\t%s\t%s\n' "$file" "$relative_path" >> "$FILE_ACTIONS"
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
plan_tree ".agentic/shared/standards"
plan_tree ".agentic/shared/workflows"
plan_tree ".agentic/01.harness"
plan_tree "scripts/00.chat"
plan_tree "scripts/01.harness"
plan_tree "docs/00.chat"
plan_selected_file "docs/harness/architecture/adrs/README.md"
plan_public_adrs
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
echo "mode: $MODE"

if [ "$CONFLICT_COUNT" -gt 0 ]; then
  exit 1
fi

merge_package_json() {
  local target_package="$TARGET_REPO/package.json"
  local template_package="$TEMPLATE_ROOT/package.json.template"

  node - "$target_package" "$template_package" <<'NODE'
const fs = require('fs');
const targetPath = process.argv[2];
const templatePath = process.argv[3];

const target = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
const template = JSON.parse(fs.readFileSync(templatePath, 'utf8'));

target.scripts = target.scripts || {};
for (const [name, expected] of Object.entries(template.scripts || {})) {
  if (target.scripts[name] === undefined || target.scripts[name] === expected) {
    target.scripts[name] = expected;
  } else {
    throw new Error(`conflicting script during apply: ${name}`);
  }
}

fs.writeFileSync(targetPath, `${JSON.stringify(target, null, 2)}\n`);
NODE
}

copy_file() {
  local source="$1"
  local relative_path="$2"
  local target="$TARGET_REPO/$relative_path"

  mkdir -p "$(dirname "$target")"
  cp "$source" "$target"
}

apply_plan() {
  local action
  local source
  local relative_path

  echo
  echo "Applying clean plan..."

  while IFS=$'\t' read -r action source relative_path; do
    case "$action" in
      CREATE)
        copy_file "$source" "$relative_path"
        echo "APPLIED_CREATE $relative_path"
        ;;
      CREATE_PACKAGE)
        copy_file "$source" "$relative_path"
        echo "APPLIED_CREATE package.json"
        ;;
      MERGE_PACKAGE)
        merge_package_json
        echo "APPLIED_MERGE package.json"
        ;;
      SAME|PRESERVE)
        :
        ;;
      *)
        echo "ERROR: unexpected action in clean plan: $action" >&2
        exit 1
        ;;
    esac
  done < "$FILE_ACTIONS"

  echo "Apply completed."
}

if [ "$MODE" = "apply" ]; then
  apply_plan
fi
