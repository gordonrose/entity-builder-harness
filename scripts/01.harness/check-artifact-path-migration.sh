#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.check-artifact-path-migration
#   version: 4
#   status: active
#   created_on: "2026-06-20"
#   updated_on: "2026-11-26"
#   layer: 01.harness
#   domain: migration
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Validate that a path migration does not leave unapproved active old-path
#     references.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.workflows.migrate-artifact-paths
#     path: .agentic/01.harness/workflows/migrate-artifact-paths.md
#   - id: harness.standards.artifact-path-migrations
#     path: .agentic/01.harness/standards/artifact-path-migrations.md
#   effects:
#   - read-only

# Shared by the planner; sourcing this file must not run its command.
is_historical_path() {
  case "$1" in
    commitLogs/*|.agentic/02.rag-rulebook/retirements/*|.agentic/02.rag-rulebook/recognition-sources/generated/*|infra/04.deploy/03.product/targets/*/20-scopes/*/30-release-evidence/proof-receipts/*.json) return 0 ;;
    *) return 1 ;;
  esac
}

historical_reference_lines() {
  case "$1" in
    docs/education/*.md|.agentic/*/plans/implementation/*.md|.agentic/02.rag-rulebook/derivation-reports/*.yml|.agentic/02.rag-rulebook/source-material-reviews/*.yml|docs/04.deploy/plans/verification-diagnostics-timeout-inventory.tsv) ;;
    *) return 0 ;;
  esac
  python3 -B - "${BASH_SOURCE[0]}" "$1" "$2" <<'PY'
import datetime
import hashlib
import re
import sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parent / 'artifact-metadata'))
from header_discovery import HeaderError, _UniqueLoader, parse_header_text

path, needle = Path(sys.argv[2]), sys.argv[3]
data = path.read_bytes()
text = data.decode('utf-8')
lines, historical = text.splitlines(), set()
if path.as_posix() == 'docs/04.deploy/plans/verification-diagnostics-timeout-inventory.tsv':
    # Exact frozen evidence recorded in artifact-path-migrations.md, not a TSV exemption.
    if hashlib.sha256(data).hexdigest() == 'e765c0a2c2aa07874a15d25b19cdb041fd11995cd4ca2f79c556157cb1d5f7cf':
        print('\n'.join(str(index) for index, line in enumerate(lines, 1) if needle in line))
    sys.exit(0)
try:
    metadata = parse_header_text(text).get('agentic-artifact', {})
    created = datetime.date.fromisoformat(str(metadata.get('created_on', '')))
except (HeaderError, ValueError, yaml.YAMLError):
    sys.exit(0)  # Unrecognised provenance remains active, never an exemption.
if metadata.get('schema') != 'agentic-artifact/v3':
    sys.exit(0)
safe_path = r'(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+'
digest = r'(?:absent|[0-9a-f]{64})'
if path.suffix == '.md':
    fenced = None
    course = metadata.get('layer') == '05.education' and metadata.get('kind') == 'guide'
    for index, line in enumerate(lines):
        fence = re.fullmatch(r' {0,3}(`{3,}|~{3,})(.*)', line)
        if fence:
            if fenced is None:
                fenced = fence[1]
            elif fence[1][0] == fenced[0] and len(fence[1]) >= len(fenced) and not fence[2].strip():
                fenced = None
            continue
        if fenced:
            continue
        marker = re.fullmatch(r'<!-- course-file: (' + safe_path + r') -->', line)
        if course and 'frozen course inventory' in text and marker:
            end = next((n for n in range(index + 1, len(lines)) if lines[n].startswith('<!-- course-file:')), len(lines))
            if any(re.fullmatch(r'<!-- course-source-sha256: before=' + digest + r' after=[0-9a-f]{64} -->', value) for value in lines[index + 1:end]):
                historical.add(index + 1)
        label = re.fullmatch(r'- \[[ x]\] \[(' + safe_path + r')\]\(([^)]+)\) — (?:added|modified|deleted); before `(?:absent|[0-9a-f]{12})`, snapshot `[0-9a-f]{12}`\.', line)
        if course and 'The frozen inventory is' in text and label and needle not in label[2]:
            historical.add(index + 1)
        if metadata.get('kind') not in ('plan', 'implementation-plan') or line != 'Historical task paths (completed work; not current instructions):':
            continue
        start = index + 1
        while start < len(lines) and not lines[start].strip():
            start += 1
        if start < len(lines) and lines[start] == '```text':
            end = next((n for n in range(start + 1, len(lines)) if lines[n] == '```'), start)
            if end > start + 1 and all(re.fullmatch(safe_path, value) and '..' not in value.split('/') for value in lines[start + 1:end]):
                historical.update(range(start + 2, end + 1))
else:
    # Reuse strict metadata YAML loading, retaining positions for exact fields.
    try:
        if any(isinstance(token, yaml.AliasToken) for token in yaml.scan(text)):
            sys.exit(0)
        yaml.load(text, Loader=_UniqueLoader)
        document = yaml.compose(text, Loader=yaml.SafeLoader)
        def at(node, *keys):
            for key in keys:
                if not isinstance(node, yaml.MappingNode):
                    return None
                node = next((value for name, value in node.value if name.value == key), None)
            return node
        def value(node):
            return node.value if isinstance(node, yaml.ScalarNode) else None
        def items(node):
            return node.value if isinstance(node, yaml.SequenceNode) else []
        def record(node):
            if not isinstance(node, yaml.ScalarNode) or node.start_mark.line != node.end_mark.line:
                return
            line = lines[node.start_mark.line]
            outside = line[:node.start_mark.column] + line[node.end_mark.column:]
            if needle not in outside:
                historical.add(node.start_mark.line + 1)
        schema = value(at(document, 'schema'))
        if not path.name.startswith(created.isoformat() + '-'):
            sys.exit(0)
        if metadata.get('kind') == 'derivation-report' and schema == 'rag-rulebook/source-to-rule-derivation-report/v1':
            for claim in items(at(document, 'semantic_review', 'source_claims')):
                record(at(claim, 'evidence_path'))
            completed = set()
            for check in items(at(document, 'validation', 'checks_run')):
                result, command = value(at(check, 'result')), at(check, 'command')
                if result in ('passed', 'failed', 'blocked'):
                    record(command)
                if result == 'passed':
                    completed.add(value(command))
            pending = at(document, 'validation', 'checks_pending')
            if isinstance(pending, yaml.SequenceNode) and not pending.value:
                for command in items(at(document, 'validation', 'required_checks')):
                    if value(command) in completed:
                        record(command)
        elif metadata.get('kind') == 'review-record' and schema == 'rag-rulebook/okf-source-material-review/v1' and value(at(document, 'status')) == 'accepted' and re.fullmatch(r'[0-9a-f]{64}', value(at(document, 'source_material', 'sha256')) or ''):
            for iteration in items(at(document, 'iterations')):
                for assessment in items(at(iteration, 'reviewer_assessments')):
                    for evidence in items(at(assessment, 'evidence')):
                        record(evidence)
    except (HeaderError, ValueError, yaml.YAMLError, RecursionError):
        historical.clear()
print('\n'.join(str(number) for number in sorted(historical)))
PY
}

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return 0
fi

usage() {
  cat <<'EOF'
Usage:
  check-artifact-path-migration.sh [--plan <migration-plan-path>] [--allow-active-old-path] <old-path> <new-path>

Fails when active files still reference <old-path> unless compatibility for the
old path has been explicitly approved with --allow-active-old-path.
EOF
}

ALLOW_ACTIVE_OLD_PATH="no"
PLAN_PATH=""

normalize_input_path() {
  local path="$1"
  path="${path#./}"
  printf '%s\n' "$path"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --plan)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      PLAN_PATH="$(normalize_input_path "$2")"
      shift 2
      ;;
    --allow-active-old-path)
      ALLOW_ACTIVE_OLD_PATH="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [ $# -ne 2 ]; then
  usage >&2
  exit 2
fi

OLD_PATH="$1"
NEW_PATH="$2"

case "$OLD_PATH:$NEW_PATH" in
  *"
"*|*":")
    echo "ERROR: paths must be non-empty single-line values." >&2
    exit 2
    ;;
esac

if REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  status=$?
  echo "ERROR: artifact-path-migration-repository-observation-unavailable" >&2
  exit "$status"
fi
if cd "$REPO_ROOT" 2>/dev/null; then
  :
else
  status=$?
  echo "ERROR: artifact-path-migration-repository-access-unavailable" >&2
  exit "$status"
fi

if [ -n "$PLAN_PATH" ] && [ ! -f "$PLAN_PATH" ]; then
  echo "ERROR: artifact-path-migration-plan-not-file" >&2
  exit 2
fi

all_files() {
  {
    local failed=0
    git ls-files 2>/dev/null || failed=1
    git ls-files --others --exclude-standard 2>/dev/null || failed=1
    [ "$failed" -eq 0 ]
  } | sort -u 2>/dev/null
}

active_old_refs() {
  local file files matches found status offset historical
  local -a candidates=()

  if files="$(all_files)"; then
    :
  else
    echo "ERROR: artifact-path-migration-enumeration-unavailable" >&2
    return 1
  fi

  while IFS= read -r file; do
    [ -f "$file" ] || continue
    is_historical_path "$file" && continue
    if [ -n "$PLAN_PATH" ] && [ "$file" = "$PLAN_PATH" ]; then
      continue
    fi
    candidates+=("$file")
  done <<< "$files"

  for ((offset=0; offset<${#candidates[@]}; offset+=256)); do
    if found="$(grep -lF -- "$OLD_PATH" "${candidates[@]:offset:256}" 2>/dev/null)"; then
      :
    else
      status=$?
      [ "$status" -eq 1 ] && continue
      echo "ERROR: artifact-path-migration-reference-read-unavailable" >&2
      return 1
    fi
    while IFS= read -r file; do
      if matches="$(grep -nF -- "$OLD_PATH" "$file" 2>/dev/null | cut -d: -f1 2>/dev/null)"; then
        if historical="$(historical_reference_lines "$file" "$OLD_PATH" 2>/dev/null)"; then
          :
        else
          echo "ERROR: artifact-path-migration-history-observation-unavailable" >&2
          return 1
        fi
        while IFS= read -r line_no; do
          [[ $'\n'"$historical"$'\n' == *$'\n'"$line_no"$'\n'* ]] && continue
          printf '%s:%s\n' "$file" "$line_no"
        done <<< "$matches"
      else
        echo "ERROR: artifact-path-migration-reference-read-unavailable" >&2
        return 1
      fi
    done <<< "$found"
  done
}

if ACTIVE_REFS="$(active_old_refs)"; then
  :
else
  exit 1
fi

if [ -n "$ACTIVE_REFS" ] && [ "$ALLOW_ACTIVE_OLD_PATH" != "yes" ]; then
  echo "ERROR: active old-path references remain (artifact-path-migration-active-references)." >&2
  printf '%s\n' "$ACTIVE_REFS" >&2
  echo "Update active references or rerun with --allow-active-old-path after approving an alias, wrapper, or pointer." >&2
  exit 1
fi

if [ -e "$NEW_PATH" ]; then
  new_exists="yes"
else
  new_exists="no"
fi

if [ -n "$ACTIVE_REFS" ]; then
  active_old_refs="present"
else
  active_old_refs="none"
fi

printf 'artifact_path_migration_check=ok\n'
printf 'old_path=%s\n' "$OLD_PATH"
printf 'new_path=%s\n' "$NEW_PATH"
if [ -n "$PLAN_PATH" ]; then
  printf 'plan_path=%s\n' "$PLAN_PATH"
fi
printf 'new_exists=%s\n' "$new_exists"
printf 'active_old_refs=%s\n' "$active_old_refs"
