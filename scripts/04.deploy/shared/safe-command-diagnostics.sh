#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.shared.safe-command-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
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
    printf 'SAFE_CHILD_OUTPUT_BEGIN\n'
    tail -n 80 "$output" | sed -E \
      -e 's/([Pp]assword|[Tt]oken|[Ss]ecret|[Aa]uthorization|[Aa][Pp][Ii][_-]?[Kk]ey)[[:space:]]*=[[:space:]]*[^[:space:]]+/\1=[REDACTED]/g' \
      -e 's/(Bearer[[:space:]]+)[^[:space:]]+/\1[REDACTED]/g' \
      -e 's#(https?://)[^/@[:space:]]+@#\1[REDACTED]@#g'
    printf 'SAFE_CHILD_OUTPUT_END\n'
  } >&2
  rm -f "$output"
  return "$status"
}
