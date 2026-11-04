#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.build-core-server-image
#   version: 1
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Qualify the core-server compiled payload, then build its local-only candidate image without publishing or selecting a target.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: deploy.command.smoke-test-core-server-image
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source "$ROOT/scripts/04.deploy/shared/safe-command-diagnostics.sh"
python3 scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
TAG="entity-builder-harness/04.deploy/kanbien-core-server:local"
ALLOW_SKIP=false
NO_CACHE=false

usage() {
  cat <<'EOF'
Usage: build-core-server-image/script.sh [--tag <tag>] [--no-cache] [--allow-skip-without-engine]

Qualifies the declared core-server program and builds a local image only. It
does not publish an image, use cloud credentials, select a target, or deploy.
EOF
}

require_value() {
  if [[ "$#" -lt 2 || -z "${2:-}" || "${2:-}" == --* ]]; then
    printf 'ERROR: %s requires a value.\n' "$1" >&2
    exit 2
  fi
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --tag)
      require_value "$1" "${2:-}"
      TAG="$2"
      shift 2
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    --allow-skip-without-engine)
      ALLOW_SKIP=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '%s\n' 'DIAGNOSTIC_CODE=CORE_IMAGE_ARGUMENTS_INVALID' >&2
      usage >&2
      exit 2
      ;;
  esac
done

safe_command_diagnostic CORE_IMAGE_CONTAINER_BOUNDARY_FAILED package 'Container boundary validation failed.' 'Inspect the container boundary fixture.' -- bash scripts/04.deploy/validate-container-boundaries/script.sh --build-context repository-root

TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT

safe_command_diagnostic CORE_IMAGE_PROGRAM_CONTRACT_FAILED package 'Runnable program validation failed.' 'Inspect the runnable program contract fixture.' -- bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh \
  --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json
safe_command_diagnostic CORE_IMAGE_DEPENDENCY_BOUNDARY_FAILED package 'Dependency boundary validation failed.' 'Inspect the dependency boundary fixture.' -- bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh --json
safe_command_diagnostic CORE_IMAGE_COMPILATION_FAILED package 'Candidate compilation failed.' 'Inspect the local compiler fixture.' -- bash scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/build.sh --out-dir "$TEMPORARY_DIRECTORY/artifacts"
safe_command_diagnostic CORE_IMAGE_RUNTIME_PREPARATION_FAILED package 'Runtime preparation failed.' 'Inspect the runtime preparation fixture.' -- node scripts/04.deploy/lifecycle/40-package/build-core-server-image/prepare-runtime.mjs \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts"
python3 scripts/04.deploy/lifecycle/40-package/build-core-server-image/verify-payload.py \
  --compiled-root "$TEMPORARY_DIRECTORY/artifacts" --json

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  if [[ "$ALLOW_SKIP" == true ]]; then
    printf '%s\n' 'SKIP: core-server payload qualification passed; container engine is unavailable.'
    exit 77
  fi
  printf '%s\n' 'ERROR: core-server payload qualification passed, but Docker is required to build the image.' >&2
  exit 1
fi

BUILD_ARGS=(
  build
  --file infra/04.deploy/03.product/image/core-server/Dockerfile
  --tag "$TAG"
  --label "org.opencontainers.image.revision=$(git rev-parse HEAD)"
  --label 'org.opencontainers.image.source=entity-builder-harness'
  --build-arg 'BUILD_NODE_IMAGE=node:22-bookworm-slim'
  --build-arg 'RUNTIME_NODE_IMAGE=gcr.io/distroless/nodejs22-debian12@sha256:afa48e2ae1100924bfb069244f4ef70c0f9c061654c669da6b7faa7881c1ec7f'
  --build-arg "SOURCE_COMMIT_SHA=$(git rev-parse HEAD)"
)
if [[ "$NO_CACHE" == true ]]; then
  BUILD_ARGS+=(--no-cache)
fi
BUILD_ARGS+=("$ROOT")
safe_command_diagnostic CORE_IMAGE_BUILD_FAILED package 'Local image build failed.' 'Inspect the retained build operation without replaying publication.' -- docker "${BUILD_ARGS[@]}"
printf 'Built local core-server image: %s\n' "$TAG"
