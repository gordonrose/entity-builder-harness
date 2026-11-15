# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.shared.candidate-image-build
#   version: 1
#   status: draft
#   created_on: "2026-11-14"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Share ordered candidate prechecks and Docker argument assembly while caller bindings retain source policy, diagnostics and build options.
#   portability: {class: reusable, targets: []}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.build-core-server-persistence-image
#     path: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh
#   - id: deploy.command.build-entity-smoke-image
#     path: scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/script.sh

# Private sourced operations: callers provide reviewed literals and fail-stop
# shell policy, after their own CLI/source checks. No workload selection occurs.
candidate_image_prechecks() {
  local scope="$1" target="$2" code="$3" summary="$4" next_check="$5"
  shift 5
  bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh --scope-contract "$scope" --json
  "$@" scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
  bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh --target-root "$target" --json
  safe_command_diagnostic "$code" package "$summary" "$next_check" -- bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json
}

candidate_image_build() {
  local code="$1" summary="$2" next_check="$3" dockerfile="$4" tag="$5" revision="$6" source_commit="$7" root="$8"
  shift 8
  safe_command_diagnostic "$code" package "$summary" "$next_check" -- docker build "$@" --file "$dockerfile" --tag "$tag" --label "org.opencontainers.image.revision=$revision" --label org.opencontainers.image.source=entity-builder-harness --build-arg "SOURCE_COMMIT_SHA=$source_commit" "$root"
}
