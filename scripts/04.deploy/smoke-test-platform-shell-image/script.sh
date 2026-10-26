#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.smoke-test-platform-shell-image
#   version: 1
#   status: active
#   created_on: "2026-07-10"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - agentic
#   - sre
#   kind: script
#   purpose: Smoke test the platform shell container image with liveness and readiness checks.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   - writes-files
#   used_by:
#   - id: deploy.script.smoke-test-platform-shell-image.readme
#     path: scripts/04.deploy/smoke-test-platform-shell-image/README.md
#   - id: deploy.script.build-platform-shell-image
#     path: scripts/04.deploy/build-platform-shell-image/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -z "${DOCKER_CONFIG:-}" ]; then
  export DOCKER_CONFIG="$ROOT/.cache/04.deploy/docker-config"
fi
mkdir -p "$DOCKER_CONFIG"

PORT="${PLATFORM_SHELL_IMAGE_SMOKE_PORT:-39453}"
ALLOW_SKIP=false
TAG="entity-builder-harness/03.product/platform-shell:smoke"
IMAGE_REFERENCE=""
CONTAINER_NAME="platform-shell-smoke-$$"

usage() {
  cat <<'EOF'
Usage:
  smoke-test-platform-shell-image/script.sh [--port <port>] [--image <immutable-image>] [--allow-skip-without-engine]

Builds and runs a local image, or qualifies a supplied immutable image, then verifies:
  GET /livez
  GET /readyz
EOF
}

require_value() {
  local flag="$1"
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ] || [[ "${2:-}" == --* ]]; then
    echo "ERROR: $flag requires a value." >&2
    exit 2
  fi
}

validate_port() {
  if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "ERROR: --port must be an integer between 1 and 65535." >&2
    exit 2
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --port)
      require_value "$1" "${2:-}"
      PORT="$2"
      shift 2
      ;;
    --allow-skip-without-engine)
      ALLOW_SKIP=true
      shift
      ;;
    --image)
      require_value "$1" "${2:-}"
      IMAGE_REFERENCE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

validate_port
if [[ -n "$IMAGE_REFERENCE" ]] && [[ ! "$IMAGE_REFERENCE" =~ ^(.+@)?sha256:[a-f0-9]{64}$ ]]; then
  echo "ERROR: --image must be an immutable sha256 image reference." >&2
  exit 2
fi

find_engine() {
  if command -v docker >/dev/null 2>&1; then
    printf '%s\n' docker
    return
  fi
  return 1
}

if ! ENGINE="$(find_engine)"; then
  if [ "$ALLOW_SKIP" = true ]; then
    echo "SKIP: no container engine found."
    exit 77
  fi
  echo "ERROR: docker is required for this image smoke test." >&2
  exit 1
fi

if ! "$ENGINE" info >/dev/null 2>&1; then
  if [ "$ALLOW_SKIP" = true ]; then
    echo "SKIP: container engine is not running or not reachable: $ENGINE"
    exit 77
  fi
  echo "ERROR: container engine is not running or not reachable: $ENGINE" >&2
  exit 1
fi

cleanup() { python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py" --container "$CONTAINER_NAME" --container "$CONTAINER_NAME-task"; }
finish() {
  local original=$? cleanup_status=0
  trap - EXIT
  cleanup || cleanup_status=$?
  if [[ "$original" -ne 0 ]]; then exit "$original"; fi
  exit "$cleanup_status"
}
trap finish EXIT

if [[ -n "$IMAGE_REFERENCE" ]]; then
  TAG="$IMAGE_REFERENCE"
else
  bash scripts/04.deploy/build-platform-shell-image/script.sh \
    --tag "$TAG" >/dev/null
fi

qualify_relational_entrypoint() {
  local entrypoint="$1"
  local output
  set +e
  output="$("$ENGINE" run --rm --name "$CONTAINER_NAME-task" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "$TAG" ".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/$entrypoint" 2>&1)"
  local status=$?
  set -e
  if [[ "$status" -ne 1 ]] || [[ "$output" != *'"outcome":"failed"'* ]]; then
    echo "ERROR: immutable image did not safely load relational entrypoint $entrypoint." >&2
    exit 1
  fi
}

for relational_entrypoint in \
  kanbien-platform-postgresql-bootstrap.main.js \
  kanbien-platform-postgresql-migration.main.js \
  kanbien-platform-postgresql-relay.main.js \
  kanbien-platform-postgresql-worker.main.js \
  kanbien-platform-postgresql-restore-verify.main.js; do
  qualify_relational_entrypoint "$relational_entrypoint"
done

"$ENGINE" run \
  --detach \
  --rm \
  --name "$CONTAINER_NAME" \
  --publish "127.0.0.1:${PORT}:3000" \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --env HOST=0.0.0.0 \
  --env PORT=3000 \
  --env PLATFORM_SMOKE_APP_NAME="Platform Shell Image Smoke" \
  "$TAG" >/dev/null

node - "$PORT" <<'NODE'
const [port] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;

async function waitFor(path, expectedStatus, expectedBodyStatus) {
  const deadline = Date.now() + 20000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${base}${path}`);
      if (response.status === expectedStatus) {
        const body = await response.json();
        if (body.status === expectedBodyStatus) return;
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw lastError || new Error(`${path} did not return ${expectedStatus} ${expectedBodyStatus}`);
}

async function main() {
  await waitFor("/livez", 200, "live");
  await waitFor("/readyz", 200, "ready");
}

main().catch((error) => {
  console.error(error.stack || error);
  process.exit(1);
});
NODE

# Qualify enabled composition through a real exported health measurement.
python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py" --container "$CONTAINER_NAME"
metrics_series='[{"sourceName":"platform.health.state","sourceKind":"counter","sourceUnit":"count","instrumentName":"package.shell.health","description":"Package health","allowedLabelNames":["health_state"],"cardinalityLimit":4}]'
"$ENGINE" run --detach --rm --name "$CONTAINER_NAME" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges --env HOST=0.0.0.0 --env PORT=3000 --env PLATFORM_SMOKE_APP_NAME=Package --env PLATFORM_SOURCE_COMMIT_SHA=package-qualification --env PLATFORM_OBSERVABILITY_METRICS_PROVIDER=cloudwatch-otel --env PLATFORM_OBSERVABILITY_METRICS_ENDPOINT=http://127.0.0.1:4318/v1/metrics --env PLATFORM_OBSERVABILITY_METRICS_REGION=eu-west-1 --env PLATFORM_OBSERVABILITY_SERVICE_NAME=platform-shell --env PLATFORM_OBSERVABILITY_DEPLOYMENT_ENVIRONMENT=package-qualification --env PLATFORM_OBSERVABILITY_EXPORT_INTERVAL_MS=1000 --env PLATFORM_OBSERVABILITY_EXPORT_TIMEOUT_MS=500 --env "PLATFORM_OBSERVABILITY_METRIC_SERIES_JSON=$metrics_series" "$TAG" >/dev/null
"$ENGINE" exec --detach "$CONTAINER_NAME" /nodejs/bin/node -e 'const fs=require("fs");require("http").createServer((req,res)=>{const chunks=[];req.on("data",b=>chunks.push(b));req.on("end",()=>{const b=Buffer.concat(chunks);if(req.url==="/v1/metrics"&&b.includes(Buffer.from("package.shell.health"))&&b.includes(Buffer.from("health_state"))&&b.includes(Buffer.from("ready")))fs.writeFileSync("/tmp/package-health-exported","observed");res.end();});}).listen(4318,"127.0.0.1");'
node - "$PORT" <<'NODE'
const base=`http://127.0.0.1:${process.argv[2]}`;
(async()=>{for(let attempt=0;attempt<40;attempt++){try{if((await fetch(base+"/readyz")).status===200)return;}catch{}await new Promise(r=>setTimeout(r,250));}throw Error("enabled-shell-not-ready");})().catch(e=>{console.error(e.message);process.exit(1)});
NODE
metric_observed=false
for attempt in $(seq 1 30); do
  if "$ENGINE" exec "$CONTAINER_NAME" /nodejs/bin/node -e 'process.exit(require("fs").existsSync("/tmp/package-health-exported")?0:1)'; then metric_observed=true; break; fi
  sleep 1
done
if [[ "$metric_observed" != true ]]; then echo 'ERROR: enabled shell metric was not exported.' >&2; exit 1; fi

python3 -B scripts/04.deploy/smoke-test-platform-shell-image/relational-package-test.py --image "$("$ENGINE" image inspect "$TAG" --format '{{.Id}}')"

cleanup
trap - EXIT
echo "Platform shell image smoke test passed."
