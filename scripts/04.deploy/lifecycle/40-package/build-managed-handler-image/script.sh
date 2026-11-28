#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.build-managed-handler-image
#   version: 2
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Build one declared managed Node handler through the existing candidate image operation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-scheduling
#     path: .github/workflows/publish-kanbien-core-platform-scheduling.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [[ $# != 4 || "$1" != --program || "$3" != --tag || ! "$2" =~ ^[a-z][a-z0-9-]+$ || ! "$4" =~ ^[a-z0-9][a-z0-9._/-]*:[A-Za-z0-9_.-]+$ ]]; then
  printf '%s\n' '{"verdict":"failed","code":"managed-image-arguments-invalid"}' >&2
  exit 2
fi
PROGRAM_ID="$2"
TAG="$4"
node --input-type=module - "$PROGRAM_ID" <<'NODE'
import { readProgramBuildInputs } from "./scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs";
try {
  const input = readProgramBuildInputs(process.cwd(), { programId: process.argv[2] });
  if (input.runtimeEntry.executionKind !== "managed-handler" || input.runtimeEntry.output !== "handler.js" || input.runtimeEntry.handlerExport !== "handler") throw Error();
} catch {
  console.error('{"verdict":"failed","code":"managed-image-program-invalid"}');
  process.exitCode = 1;
}
NODE
source scripts/04.deploy/shared/safe-command-diagnostics.sh
source scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh
SOURCE_REVISION="$(git rev-parse HEAD)"
candidate_image_build MANAGED_IMAGE_BUILD_FAILED 'Managed image build failed.' 'Inspect the retained package failure before retrying.' \
  infra/04.deploy/03.product/image/scheduling-lambda/Dockerfile "$TAG" "$SOURCE_REVISION" "$SOURCE_REVISION" "$ROOT" \
  --platform linux/amd64 --provenance=false --build-arg "PROGRAM_ID=$PROGRAM_ID"
