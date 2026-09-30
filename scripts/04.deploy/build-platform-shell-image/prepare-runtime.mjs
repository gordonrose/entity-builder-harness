#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.build-platform-shell-image.prepare-runtime
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - agentic
//   - sre
//   kind: script
//   purpose: Prepare CommonJS package shims for the platform shell image runtime payload.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.script.build-platform-shell-image
//     path: scripts/04.deploy/build-platform-shell-image/script.sh

import { prepareWorkspaceRuntime } from './workspace-runtime.mjs';

const runtimeRoot = '.cache/platform-shell-image-build';
prepareWorkspaceRuntime('platform/server/tsconfig.image.json', runtimeRoot);
console.log('Prepared compiler-bound platform shell runtime');
