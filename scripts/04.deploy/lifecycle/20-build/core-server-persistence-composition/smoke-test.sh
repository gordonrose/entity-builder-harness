#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-persistence-composition
#   version: 2
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-28"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Compile and prove the provider-neutral persistence-capable core-server composition using an injected local fake only.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.plan.implementation.platform-to-target-chain-control
#     path: .agentic/04.deploy/plans/implementation/platform-to-target-chain-control.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TEMPORARY_DIRECTORY="$(mktemp -d)"
trap 'rm -rf "$TEMPORARY_DIRECTORY"' EXIT
COMPILED_DIRECTORY="$TEMPORARY_DIRECTORY/compiled"

bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/build.sh --out-dir "$COMPILED_DIRECTORY"
node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs --compiled-root "$COMPILED_DIRECTORY"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/verify-runtime.mjs --compiled-root "$COMPILED_DIRECTORY"
BASELINE_FINGERPRINT="$(node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs --fingerprint "$COMPILED_DIRECTORY")"
# The composed entrypoint imports its optional target metrics adapter at module
# load time.  Resolve its real external packages here just as the image payload
# does, while the individual runtime fixtures still select provider `none`.
# Each child copies the immutable compiled payload before injecting any module.
# Fast mutation fixtures prove order/repetition without repeating TLS proofs.
node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-isolation-test.mjs
for fixture in runtime-test restore-diagnostic-test configuration-test observability-runtime-test; do
  NODE_PATH="$ROOT/node_modules" node "scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/$fixture.mjs" "$COMPILED_DIRECTORY"
done
test "$BASELINE_FINGERPRINT" = "$(node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/fixture-runtime.mjs --fingerprint "$COMPILED_DIRECTORY")"

python3 -B "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime-configuration-test.py"
