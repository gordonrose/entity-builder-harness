#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.check-headers-compatibility-wrapper
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Preserve the legacy artifact metadata checker entrypoint while delegating to the capability-scoped checker.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: harness.standard.artifact-metadata-headers-v1
#       path: .agentic/01.harness/standards/artifact-metadata-headers.md
#     - id: harness.standard.artifact-metadata
#       path: .agentic/01.harness/artifact-metadata/standard.md
#     - id: harness.checklist.before-commit
#       path: .agentic/00.chat/checklists/before-commit.md

repo_root="$(git rev-parse --show-toplevel)"

exec bash "$repo_root/scripts/01.harness/artifact-metadata/check-headers/script.sh" "$@"
