#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.collector-image-startup
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Qualify assembled collector startup and enabled OTLP-to-EMF behavior with isolated disposable resources.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-observability-collector
#     path: .github/workflows/publish-kanbien-core-platform-observability-collector.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
source "$ROOT/scripts/04.deploy/shared/safe-command-diagnostics.sh"
image="kanbien-observability-collector:qualification"
if [[ "$#" -gt 0 ]]; then
  if [[ "$#" -ne 2 || "$1" != --image || -z "$2" ]]; then echo "Usage: qualify-image.sh [--image <reference>]" >&2; exit 2; fi
  image="$2"
fi
name="kanbien-observability-collector-qualification-${GITHUB_RUN_ID:-$$}"
cleanup() { python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py" --container "$name"; }
finish() {
  local original=$? cleanup_status=0
  trap - EXIT
  cleanup || cleanup_status=$?
  if [[ "$original" -ne 0 ]]; then exit "$original"; fi
  exit "$cleanup_status"
}
trap finish EXIT
safe_command_diagnostic COLLECTOR_CONTAINER_START_FAILED package 'Disposable collector start failed.' 'Inspect the collector startup fixture.' -- docker run --detach --rm --name "$name" --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL \
  --security-opt no-new-privileges \
  -e AWS_EC2_METADATA_DISABLED=true \
  -e "AOT_CONFIG_CONTENT=$(cat infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml)" \
  "$image"
sleep 5
collector_running() { test "$(docker inspect --format '{{.State.Running}}' "$name")" = true; }
safe_command_diagnostic COLLECTOR_RUNNING_OBSERVATION_FAILED package 'Collector running observation did not qualify.' 'Inspect the collector running observation fixture.' -- collector_running
collector_logs() { logs="$(docker logs "$name" 2>&1)"; }
safe_command_diagnostic COLLECTOR_LOG_OBSERVATION_FAILED package 'Collector log observation failed.' 'Inspect the collector log observation fixture.' -- collector_logs
collector_logs_qualify() { ! grep -Ei 'error.*(config|awsemf)|failed.*(config|awsemf)' <<<"$logs"; }
safe_command_diagnostic COLLECTOR_LOG_QUALIFICATION_FAILED package 'Observed collector logs did not qualify.' 'Inspect the collector log qualification fixture.' -- collector_logs_qualify
cleanup
trap - EXIT

exec python3 -B "$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/behavior-test.py" --image "$image"
