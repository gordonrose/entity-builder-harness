#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.safe-command-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Prove the shared diagnostic wrapper preserves a safe failure signal without leaking a controlled secret fixture.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.shared.safe-command-diagnostics
#     path: scripts/04.deploy/shared/safe-command-diagnostics.sh

ROOT="$(git rev-parse --show-toplevel)"
source "$ROOT/scripts/04.deploy/shared/safe-command-diagnostics.sh"
if output="$(safe_command_diagnostic TEST_CHILD_FAILURE 40-package 'controlled child failed' 'inspect fixture' -- bash -c 'printf "token=controlled-secret\\n"; printf "token=controlled-secret-stderr\\n" >&2; exit 17' 2>&1)"; then
  echo 'ERROR: safe diagnostic wrapper accepted a failed child command.' >&2
  exit 1
else
  status=$?
fi
[[ "$status" -eq 17 ]]
[[ "$output" == *'DIAGNOSTIC_CODE=TEST_CHILD_FAILURE'* ]]
[[ "$output" == *'CHILD_OUTPUT=not-retained-unstructured-output'* ]]
[[ "$output" != *'controlled-secret'* ]]
report="$(mktemp)"
fixture="$(mktemp -d)"
trap 'rm -f "$report"; rm -rf "$fixture"' EXIT
if output="$(safe_command_deployment_diagnostic TEST_CHILD_FAILURE package 'controlled child failed' 'inspect fixture' test-target test-scope test-operation github-actions-artifact:diagnostics-test "$report" -- bash -c 'printf "token=controlled-secret\\n"; printf "token=controlled-secret-stderr\\n" >&2; exit 17' 2>&1)"; then
  echo 'ERROR: safe deployment diagnostic accepted a failed child command.' >&2
  exit 1
else
  status=$?
fi
[[ "$status" -eq 17 ]]
[[ "$output" == *'DIAGNOSTIC_COLLECTION_STATUS=collected'* ]]
[[ "$output" != *'controlled-secret'* ]]
python3 "$ROOT/scripts/04.deploy/shared/deployment-operation-diagnostics.py" validate --report "$report" >/dev/null
[[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["original_failure"]["exit_status"])' "$report")" == 17 ]]
# A failed diagnostic writer must retain the child's status and original code.
if output="$(safe_command_deployment_diagnostic TEST_CHILD_FAILURE deploy 'controlled child failed' 'inspect fixture' test-target test-scope test-operation github-actions-artifact:diagnostics-test "$report/cannot-create.json" -- bash -c 'exit 23' 2>&1)"; then
  exit 1
else
  status=$?
fi
[[ "$status" -eq 23 && "$output" == *'DIAGNOSTIC_CODE=TEST_CHILD_FAILURE'* && "$output" == *'DIAGNOSTIC_COLLECTION_STATUS=failed'* ]]
[[ "$output" == *'DIAGNOSTIC_COLLECTION_CODE=deployment-operation-diagnostic-collection-failed'* ]]
# A noisy nested writer cannot leak either stream or replace the child status.
mkdir "$fixture/bin"
printf '%s\n' '#!/usr/bin/env bash' 'printf "controlled-writer-secret-stdout\\n"' 'printf "controlled-writer-secret-stderr\\n" >&2' 'printf "called\\n" >>"$B10_WRITER_LOG"' 'exit "$B10_WRITER_STATUS"' >"$fixture/bin/python3"
chmod +x "$fixture/bin/python3"
for writer_status in 0 91; do
  for child_status in 17 23; do
    if PATH="$fixture/bin:$PATH" B10_WRITER_STATUS="$writer_status" B10_WRITER_LOG="$fixture/writer-calls" safe_command_deployment_diagnostic TEST_CHILD_FAILURE deploy 'controlled child failed' 'inspect fixture' test-target test-scope test-operation github-actions-artifact:diagnostics-test "$report" -- bash -c 'printf "controlled-child-secret-stdout\\n"; printf "controlled-child-secret-stderr\\n" >&2; exit "$1"' _ "$child_status" >"$fixture/stdout" 2>"$fixture/stderr"; then
      exit 1
    else
      status=$?
    fi
    [[ "$status" -eq "$child_status" && ! -s "$fixture/stdout" ]]
    output="$(<"$fixture/stderr")"
    [[ "$output" != *'secret'* && "$output" == *'DIAGNOSTIC_CODE=TEST_CHILD_FAILURE'* ]]
    if [[ "$writer_status" -eq 0 ]]; then
      [[ "$output" == *'DIAGNOSTIC_COLLECTION_STATUS=collected'* && "$output" != *'DIAGNOSTIC_COLLECTION_CODE='* ]]
    else
      [[ "$output" == *'DIAGNOSTIC_COLLECTION_STATUS=failed'* && "$output" == *'DIAGNOSTIC_COLLECTION_CODE=deployment-operation-diagnostic-collection-failed'* ]]
    fi
  done
done
[[ "$(wc -l <"$fixture/writer-calls")" -eq 4 ]]
# Successful children remain silent and never invoke diagnostic collection.
for wrapper in safe_command_diagnostic safe_command_deployment_diagnostic; do
  arguments=(TEST_CHILD_SUCCESS package 'unused summary' 'unused next check')
  if [[ "$wrapper" == safe_command_deployment_diagnostic ]]; then
    arguments+=(test-target test-scope test-operation github-actions-artifact:diagnostics-test "$report")
  fi
  PATH="$fixture/bin:$PATH" B10_WRITER_STATUS=91 B10_WRITER_LOG="$fixture/writer-calls" "$wrapper" "${arguments[@]}" -- bash -c 'printf "controlled-success-secret\\n"; printf "controlled-success-secret-stderr\\n" >&2' >"$fixture/stdout" 2>"$fixture/stderr"
  [[ ! -s "$fixture/stdout" && ! -s "$fixture/stderr" ]]
done
[[ "$(wc -l <"$fixture/writer-calls")" -eq 4 ]]
echo 'Safe command diagnostics smoke test passed.'
