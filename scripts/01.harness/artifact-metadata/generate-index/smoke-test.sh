#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.generate-index-smoke-test
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Smoke test artifact metadata index generation for v1 and v2 headers.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: harness.script.artifact-metadata.generate-index
#       path: scripts/01.harness/artifact-metadata/generate-index/script.sh

repo_root="$(git rev-parse --show-toplevel)"
generator="$repo_root/scripts/01.harness/artifact-metadata/generate-index/script.sh"

json_output="$(bash "$generator" --paths \
  .agentic/01.harness/artifact-metadata/examples/markdown.v2.md \
  .agentic/01.harness/artifact-metadata/examples/yaml.v2.yml \
  scripts/01.harness/artifact-metadata/check-headers/script.sh \
  scripts/01.harness/check-artifact-metadata-headers.sh \
  docs/02.rag-rulebook/rules/README.md \
  docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml \
  docs/harness/architecture/rules/layers/packages-core.yml)"

python3 -c '
import json, sys
data = json.load(sys.stdin)
paths = {artifact["path"]: artifact for artifact in data["artifacts"]}
assert data["schema"] == "agentic-artifact-index/v1"
assert data["summary"]["v2_artifacts"] >= 7
assert data["summary"]["legacy_artifacts"] == 0
assert paths[".agentic/01.harness/artifact-metadata/examples/markdown.v2.md"]["id"] == "harness.example.artifact-metadata.markdown-v2"
assert paths["scripts/01.harness/artifact-metadata/check-headers/script.sh"]["kind"] == "script"
assert paths["scripts/01.harness/check-artifact-metadata-headers.sh"]["metadata_schema"] == "agentic-artifact/v2"
assert paths["scripts/01.harness/check-artifact-metadata-headers.sh"]["id"] == "harness.script.artifact-metadata.check-headers-compatibility-wrapper"
assert paths["docs/02.rag-rulebook/rules/README.md"]["layer"] == "02.rag-rulebook"
assert paths["docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml"]["kind"] == "rule"
' <<< "$json_output"

echo "Artifact metadata index generator smoke test passed."
