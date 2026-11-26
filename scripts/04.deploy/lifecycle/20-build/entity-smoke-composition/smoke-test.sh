#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.composition.wrapper
#   version: 3
#   status: draft
#   created_on: "2026-11-07"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compile fresh isolated feature output and exercise its public app and controlled target boundaries.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: infra.04-deploy.03-product.entrypoints.runnable-program-index
#     path: infra/04.deploy/03.product/entrypoints/runnable-program-index.yml
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [ "$#" -eq 0 ]; then
  exec bash scripts/repo/check-selection/script.sh --aggregate-members entity-smoke-composition --execute-local --json
fi
if [ "$#" -ne 2 ] || [ "$1" != "--unit" ]; then
  echo "Usage: smoke-test.sh [--unit infrastructure|base|suite|task-route|failure-route|restart-route|credential-route]" >&2
  exit 2
fi
case "$2" in
  infrastructure) exec python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/infrastructure-route-test.py ;;
  task-route) exec python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-route-test.py ;;
  failure-route) exec python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/failure-handling/tests/failure-route-test.py ;;
  restart-route) exec python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/recovery-and-replacement/restart/restart-route-test.py ;;
  credential-route) exec python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/credential-route-test.py ;;
  base|suite) ;;
  *) echo "Usage: smoke-test.sh [--unit infrastructure|base|suite|task-route|failure-route|restart-route|credential-route]" >&2; exit 2 ;;
esac
entity_smoke_scratch="${TMPDIR:-/tmp}"
entity_smoke_build="$(mktemp -d "$entity_smoke_scratch/kanbien-entity-smoke-build.XXXXXXXX")"
[[ "$entity_smoke_build" == "$entity_smoke_scratch"/kanbien-entity-smoke-build.* && -d "$entity_smoke_build" && ! -L "$entity_smoke_build" ]]
trap 'rm -rf -- "$entity_smoke_build"' EXIT
node scripts/04.deploy/lifecycle/20-build/runnable-program-contract/compile.mjs --program kanbien-entity-smoke --outDir "$entity_smoke_build" --incremental false
node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/dependency-boundary.mjs "$entity_smoke_build"
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --compiled-root "$entity_smoke_build" --dry-run
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --compiled-root "$entity_smoke_build"
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-dependencies.mjs "$ROOT" "$entity_smoke_build/.dependencies/node_modules"
NODE_PATH="$entity_smoke_build/.dependencies/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/runtime-test.mjs "$entity_smoke_build"
NODE_PATH="$entity_smoke_build/.dependencies/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/access-control-test.mjs "$entity_smoke_build"
node scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-recovery/tests/administrator-observation-test.mjs
node scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-recovery/tests/administrator-recovery-test.mjs
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/recovery-and-replacement/source-transition/source-transition-test.py
NODE_PATH="$entity_smoke_build/.dependencies/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/preflight-test.mjs "$entity_smoke_build"
NODE_PATH="$entity_smoke_build/.dependencies/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/database-proof-test.mjs "$entity_smoke_build"
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/dependency-test.mjs
python3 -B scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/template-test.py
python3 -B scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/alignment-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-evidence-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-runner-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/preflight-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-binding-test.py
run_post_route_controls() {
  python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/resource-control-test.py
  python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/deployment-control-test.py
  node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/qualification-control-test.mjs
}
if [ "$2" = "base" ]; then
  run_post_route_controls
  exit 0
fi
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/tests/task-route-test.py &
entity_smoke_task_fixture_pid=$!
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/failure-handling/tests/failure-route-test.py &
entity_smoke_failure_fixture_pid=$!
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/recovery-and-replacement/restart/restart-route-test.py &
entity_smoke_restart_fixture_pid=$!
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/tests/credential-route-test.py &
entity_smoke_credential_fixture_pid=$!
entity_smoke_fixture_status=0
wait "$entity_smoke_task_fixture_pid" || entity_smoke_fixture_status=$?
wait "$entity_smoke_failure_fixture_pid" || entity_smoke_fixture_status=$?
wait "$entity_smoke_restart_fixture_pid" || entity_smoke_fixture_status=$?
wait "$entity_smoke_credential_fixture_pid" || entity_smoke_fixture_status=$?
[[ "$entity_smoke_fixture_status" -eq 0 ]]
run_post_route_controls
bash scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/commands/acceptance-control-test.sh
