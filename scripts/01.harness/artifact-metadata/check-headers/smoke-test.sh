#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.check-headers-smoke-test
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Smoke test v1 and v2 artifact metadata header validation.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: harness.script.artifact-metadata.check-headers
#       path: scripts/01.harness/artifact-metadata/check-headers/script.sh

repo_root="$(git rev-parse --show-toplevel)"
checker="$repo_root/scripts/01.harness/artifact-metadata/check-headers/script.sh"

bash "$checker" --paths \
  .agentic/00.chat/workflows/chat-start.md \
  .agentic/shared/standards/upstream-repo-bootstrap.md \
  docs/00.chat/README.md \
  scripts/00.chat/startup/start-chat-session/script.sh \
  scripts/01.harness/artifact-metadata/check-headers/script.sh \
  scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh

tmp_dir="$repo_root/scripts/01.harness/artifact-metadata/check-headers/.tmp-check-headers-smoke-$$"
trap 'rm -rf "$tmp_dir"' EXIT
mkdir -p "$tmp_dir"
printf '#!/usr/bin/env bash\n' > "$tmp_dir/missing.sh"

if bash "$checker" --paths "$tmp_dir/missing.sh" >/dev/null 2>&1; then
  echo "ERROR: missing-header fixture unexpectedly passed." >&2
  exit 1
fi

echo "Artifact metadata header checker smoke test passed."
