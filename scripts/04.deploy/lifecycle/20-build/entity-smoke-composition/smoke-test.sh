#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.composition.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-11-07"
#   updated_on: "2026-11-11"
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
entity_smoke_build="$(mktemp -d /tmp/kanbien-entity-smoke-build.XXXXXXXX)"
[[ "$entity_smoke_build" == /tmp/kanbien-entity-smoke-build.* && -d "$entity_smoke_build" && ! -L "$entity_smoke_build" ]]
trap 'rm -rf -- "$entity_smoke_build"' EXIT
node_modules/.bin/tsc --project infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke.tsconfig.json --outDir "$entity_smoke_build" --incremental false
node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/dependency-boundary.mjs "$entity_smoke_build"
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --compiled-root "$entity_smoke_build" --dry-run
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs --compiled-root "$entity_smoke_build"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/runtime-test.mjs "$entity_smoke_build"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/access-control-test.mjs "$entity_smoke_build"
node scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-observation-test.mjs
node scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-recovery-test.mjs
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/preflight-test.mjs "$entity_smoke_build"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/database-proof-test.mjs "$entity_smoke_build"
node scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/dependency-test.mjs
python3 -B scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/template-test.py
python3 -B scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/alignment-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-evidence-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-runner-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/preflight-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-binding-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route-test.py &
entity_smoke_task_fixture_pid=$!
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/failure-route-test.py &
entity_smoke_failure_fixture_pid=$!
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restart-route-test.py &
entity_smoke_restart_fixture_pid=$!
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/credential-route-test.py &
entity_smoke_credential_fixture_pid=$!
entity_smoke_fixture_status=0
wait "$entity_smoke_task_fixture_pid" || entity_smoke_fixture_status=$?
wait "$entity_smoke_failure_fixture_pid" || entity_smoke_fixture_status=$?
wait "$entity_smoke_restart_fixture_pid" || entity_smoke_fixture_status=$?
wait "$entity_smoke_credential_fixture_pid" || entity_smoke_fixture_status=$?
[[ "$entity_smoke_fixture_status" -eq 0 ]]
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/resource-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/deployment-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/infrastructure-route-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/restore-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route-test.py
node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/qualification-control-test.mjs
