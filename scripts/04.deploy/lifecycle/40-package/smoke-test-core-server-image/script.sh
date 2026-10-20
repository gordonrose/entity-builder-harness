#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.smoke-test-core-server-image
#   version: 2
#   status: draft
#   created_on: "2026-10-19"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Locally smoke test the dedicated core-server image and its safe health and release-verification operations.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: deploy.command.smoke-test-core-server-image.readme
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/README.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
source "$ROOT/scripts/04.deploy/shared/safe-command-diagnostics.sh"
TAG="entity-builder-harness/04.deploy/kanbien-core-server:smoke"
PORT="${CORE_SERVER_IMAGE_SMOKE_PORT:-39454}"
ALLOW_SKIP=false
CONTAINER_NAME="kanbien-core-server-image-smoke-$$"

usage() {
  cat <<'EOF'
Usage: smoke-test-core-server-image/script.sh [--tag <tag>] [--port <port>] [--allow-skip-without-engine]

Builds and starts a local-only core-server image, then checks liveness,
readiness, safe release identity, and the payload rejection fixture.
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
    --port)
      require_value "$1" "${2:-}"
      PORT="$2"
      shift 2
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
      printf 'ERROR: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [[ "$PORT" -lt 1 || "$PORT" -gt 65535 ]]; then
  printf '%s\n' 'ERROR: --port must be an integer between 1 and 65535.' >&2
  exit 2
fi

bash scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/payload-fixture-test.sh

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  if [[ "$ALLOW_SKIP" == true ]]; then
    printf '%s\n' 'SKIP: core-server payload fixture passed; container engine is unavailable.'
    exit 0
  fi
  printf '%s\n' 'ERROR: core-server payload fixture passed, but Docker is required to run the image smoke test.' >&2
  exit 1
fi

cleanup() {
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

safe_command_diagnostic IMAGE_SMOKE_BUILD_FAILED 40-package \
  'core-server image build did not complete' \
  'inspect the bounded build diagnostic and image contract' -- \
  bash scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh --tag "$TAG"
safe_command_diagnostic IMAGE_SMOKE_CONTAINER_START_FAILED 40-package \
  'core-server container did not start' \
  'inspect the bounded container-start diagnostic and runtime command' -- \
  docker run --detach --rm --name "$CONTAINER_NAME" \
  --publish "127.0.0.1:${PORT}:3000" \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
  --cap-drop ALL --security-opt no-new-privileges \
  "$TAG"

EXPECTED_REVISION="$(git rev-parse HEAD)"
node - "$PORT" "$EXPECTED_REVISION" <<'NODE'
const [port, expectedRevision] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;

async function waitFor(path, expected) {
  const deadline = Date.now() + 20000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${base}${path}`);
      const body = await response.json();
      if (response.status === expected.status && expected.test(body)) return;
      lastError = new Error(`${path} returned an unexpected safe response`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw lastError || new Error(`${path} did not respond`);
}

await waitFor("/livez", { status: 200, test: (body) => body.status === "live" });
await waitFor("/readyz", { status: 200, test: (body) => body.status === "ready" });
await waitFor("/internal/release-verification", {
  status: 200,
  test: (body) => body && body.release && body.release.sourceCommitSha === expectedRevision,
});
NODE

printf '%s\n' 'Core-server image smoke test passed.'
