#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.ecr-read-access
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Safely prove AWS ECR authorization with a declared repository and intentionally nonexistent image digest.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - network
#   used_by:
#   - id: deploy.command.kanbien-core-platform.verify-delivery-role-access
#     path: scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access/script.sh

readonly PROBE_DIGEST="sha256:0000000000000000000000000000000000000000000000000000000000000000"
REPOSITORY=""

fail() { printf 'DIAGNOSTIC_CODE=%s\n' "$1" >&2; exit 1; }
require_value() { [ -n "$2" ] || fail DELIVERY_ACCESS_ARGUMENTS_INVALID; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repository)
      shift
      require_value --repository "${1:-}"
      REPOSITORY="$1"
      ;;
    *) fail DELIVERY_ACCESS_ARGUMENTS_INVALID ;;
  esac
  shift
done

[ -n "$REPOSITORY" ] || fail DELIVERY_ACCESS_ARGUMENTS_INVALID
command -v aws >/dev/null 2>&1 || fail DELIVERY_ACCESS_AWS_CLI_UNAVAILABLE

probe_not_denied() {
  local operation="$1"; shift
  local output status
  output="$(mktemp)"
  if "$@" >"$output" 2>&1; then
    rm -f "$output"
    return 0
  else
    status=$?
  fi
  if grep -Eq 'AccessDenied|Unauthorized|not authorized' "$output"; then
    rm -f "$output"
    fail "DELIVERY_ACCESS_${operation}_DENIED"
  fi
  if grep -Eq 'ImageNotFound|ScanNotFound' "$output"; then
    rm -f "$output"
    return 0
  fi
  rm -f "$output"
  [ "$status" -eq 0 ] || fail "DELIVERY_ACCESS_${operation}_PROBE_INCONCLUSIVE"
}

probe_not_denied GET_AUTHORIZATION_TOKEN aws ecr get-authorization-token --output text
probe_not_denied DESCRIBE_IMAGES aws ecr describe-images --repository-name "$REPOSITORY" --image-ids imageDigest="$PROBE_DIGEST" --output json
probe_not_denied DESCRIBE_SCAN_FINDINGS aws ecr describe-image-scan-findings --repository-name "$REPOSITORY" --image-id imageDigest="$PROBE_DIGEST" --max-results 1 --output json
printf '%s\n' '{"schema":"deploy/provider-live-access/v1","provider":"aws","resource_class":"container-registry-repository","verdict":"passed"}'
