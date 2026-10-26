#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.core-server-persistence-composition
#   version: 2
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-26"
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

bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/build.sh --out-dir "$TEMPORARY_DIRECTORY"
node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs --compiled-root "$TEMPORARY_DIRECTORY"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/verify-runtime.mjs --compiled-root "$TEMPORARY_DIRECTORY"
# The composed entrypoint imports its optional target metrics adapter at module
# load time.  Resolve its real external packages here just as the image payload
# does, while the individual runtime fixtures still select provider `none`.
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/runtime-test.mjs "$TEMPORARY_DIRECTORY"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/restore-diagnostic-test.mjs "$TEMPORARY_DIRECTORY"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/configuration-test.mjs "$TEMPORARY_DIRECTORY"
NODE_PATH="$ROOT/node_modules" node scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/observability-runtime-test.mjs "$TEMPORARY_DIRECTORY"
