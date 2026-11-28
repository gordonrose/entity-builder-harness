#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.build-environment-session-controller-image
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Build and qualify the committed controller image without publication or deployment.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-environment-session-controller
#     path: .github/workflows/publish-kanbien-core-platform-environment-session-controller.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source scripts/04.deploy/shared/safe-command-diagnostics.sh
source scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh
if [[ $# != 4 || "$1" != --tag || "$3" != --receipt ]]; then
  printf '%s\n' 'SESSION_IMAGE_ARGUMENTS_INVALID' >&2; exit 2
fi
session_image_tag="$2"
session_image_receipt="$4"
[[ "$session_image_tag" =~ ^kanbien-environment-session-controller:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || {
  printf '%s\n' 'SESSION_IMAGE_ARGUMENTS_INVALID' >&2; exit 2;
}
if [[ -n "$(git status --porcelain --untracked-files=all -- . ':!commitLogs')" ]]; then
  printf '%s\n' 'SESSION_IMAGE_COMMITTED_SOURCE_REQUIRED' >&2; exit 1
fi
session_image_source="$(git rev-parse HEAD)"
session_image_paths="$(python3 -c 'import yaml; d=yaml.safe_load(open("infra/04.deploy/03.product/image/environment-session-controller/image-contract.yml")); assert d["schema"]=="deploy/controller-image-contract/v1" and isinstance(d["source_paths"],list) and d["source_paths"]; print("\n".join(d["source_paths"]))')" || {
  printf '%s\n' 'SESSION_IMAGE_CONTRACT_INVALID' >&2; exit 1;
}
mapfile -t session_image_selection <<< "$session_image_paths"
if ! timeout 30 docker info >/dev/null 2>&1; then
  printf '%s\n' 'SESSION_IMAGE_LOCAL_ENGINE_UNAVAILABLE' >&2; exit 1
fi
git archive "$session_image_source" -- "${session_image_selection[@]}" |
  candidate_image_build SESSION_IMAGE_BUILD_FAILED 'Controller image build failed.' 'Inspect this build; publication was not invoked.' infra/04.deploy/03.product/image/environment-session-controller/Dockerfile "$session_image_tag" "$session_image_source" "$session_image_source" - --load --platform linux/amd64 --provenance=false
session_image_cli="$(timeout 30 docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=256m --entrypoint /usr/local/bin/aws "$session_image_tag" --version)"
[[ "$session_image_cli" == aws-cli/2.36.50* ]] || {
  printf '%s\n' 'SESSION_IMAGE_TOOLCHAIN_MISMATCH' >&2; exit 1;
}
timeout 180 docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=256m --entrypoint /usr/local/bin/python3 "$session_image_tag" -I -B /opt/controller/scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/integration-test.py CommandTests ControllerTests StartupTests NativeControlTests NativeRoleBoundaryTests CleanupObservationTests ConnectedRecordsTests.test_network_role_binding_uses_original_output_and_never_replays_retained_intent
session_image_inputs=()
while IFS= read -r -d '' session_image_path; do
  session_image_inputs+=(--input "$session_image_path")
done < <(git ls-files -z -- "${session_image_selection[@]}")
[[ "${#session_image_inputs[@]}" -gt 0 ]]
python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py record --image "$session_image_tag" --receipt "$session_image_receipt" "${session_image_inputs[@]}"
printf '%s\n' 'SESSION_IMAGE_QUALIFIED_NOT_PUBLISHED'
