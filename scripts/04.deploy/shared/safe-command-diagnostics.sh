#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.shared.safe-command-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Preserve bounded redacted child-command diagnostics for lifecycle scripts.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.command.smoke-test-core-server-image
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh
#   - id: deploy.test.safe-command-diagnostics
#     path: scripts/04.deploy/shared/safe-command-diagnostics-smoke-test.sh

safe_command_diagnostic() {
  local code="$1"
  local stage="$2"
  local summary="$3"
  local next_check="$4"
  shift 4
  if [[ "${1:-}" != "--" ]]; then
    printf 'ERROR: safe command diagnostic requires -- before its command.\n' >&2
    return 2
  fi
  shift
  local output status
  output="$(mktemp)"
  if "$@" >"$output" 2>&1; then
    rm -f "$output"
    return 0
  else
    status=$?
  fi
  {
    printf 'DIAGNOSTIC_CODE=%s\n' "$code"
    printf 'LIFECYCLE_STAGE=%s\n' "$stage"
    printf 'SUMMARY=%s\n' "$summary"
    printf 'NEXT_CHECK=%s\n' "$next_check"
    printf 'CHILD_OUTPUT=not-retained-unstructured-output\n'
  } >&2
  rm -f "$output"
  return "$status"
}

# Run a consequential child command and retain only an allowlisted operation
# report. The report path is selected by the caller's governed evidence route;
# this helper never copies the child output into it. Collection failure is
# reported separately while the child status remains the returned status.
safe_command_deployment_diagnostic() {
  local code="$1" stage="$2" summary="$3" next_check="$4"
  local target="$5" scope="$6" operation_id="$7" evidence_reference="$8" report_path="$9"
  shift 9
  if [[ "${1:-}" != "--" ]]; then
    printf 'ERROR: safe deployment diagnostic requires -- before its command.\n' >&2
    return 2
  fi
  shift
  local output status root
  root="$(git rev-parse --show-toplevel)"
  output="$(mktemp)"
  if "$@" >"$output" 2>&1; then
    rm -f "$output"
    return 0
  else
    status=$?
  fi
  {
    printf 'DIAGNOSTIC_CODE=%s\n' "$code"
    printf 'LIFECYCLE_STAGE=%s\n' "$stage"
    printf 'SUMMARY=%s\n' "$summary"
    printf 'NEXT_CHECK=%s\n' "$next_check"
    printf 'CHILD_OUTPUT=not-retained-unstructured-output\n'
  } >&2
  if ! python3 "$root/scripts/04.deploy/shared/deployment-operation-diagnostics.py" record \
      --target "$target" --scope "$scope" --operation-id "$operation_id" --stage "$stage" \
      --original-code "$code" --exit-status "$status" --outcome unknown --classification child-command-failed \
      --evidence-reference "$evidence_reference" --next-decision inspect-retained-evidence \
      --report "$report_path" >/dev/null; then
    printf 'DIAGNOSTIC_COLLECTION_STATUS=failed\n' >&2
    printf 'DIAGNOSTIC_COLLECTION_CODE=deployment-operation-diagnostic-collection-failed\n' >&2
  else
    printf 'DIAGNOSTIC_COLLECTION_STATUS=collected\n' >&2
  fi
  rm -f "$output"
  return "$status"
}
