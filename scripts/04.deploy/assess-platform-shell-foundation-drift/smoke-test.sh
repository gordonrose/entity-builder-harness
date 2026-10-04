#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-foundation-drift.smoke-test
#   version: 2
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the bounded Foundation drift classifier without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: deploy.script.assess-platform-shell-foundation-drift.readme
#     path: scripts/04.deploy/assess-platform-shell-foundation-drift/README.md
#   effects:
#   - read-only

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/assess-platform-shell-foundation-drift/script.py").read_text(encoding="utf-8"), "foundation-active-drift-assessment.py", "exec")'
result="$(bash scripts/04.deploy/assess-platform-shell-foundation-drift/script.sh --validate --json)"
if [[ "$result" != *'"id": "source-policy"'* || "$result" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: Foundation drift-classifier source validation did not emit the expected safe result" >&2
  exit 1
fi
fake_aws="$(mktemp)"
trap 'rm -f "$fake_aws"' EXIT
cat >"$fake_aws" <<'EOF'
#!/usr/bin/env bash
exit 9
EOF
chmod 700 "$fake_aws"
if result="$(bash scripts/04.deploy/assess-platform-shell-foundation-drift/script.sh --execute-approved-active-foundation-drift-assessment --aws-cli "$fake_aws" --evidence-file /tmp/foundation-drift-smoke-evidence.json --json 2>&1)"; then
  echo "ERROR: Foundation drift classifier unexpectedly accepted a failing AWS subprocess" >&2
  exit 1
fi
if [[ "$result" != *'"id": "aws-account-verification-unavailable"'* || "$result" != *'"failure_class": "nonzero-exit"'* ]]; then
  echo "ERROR: Foundation drift classifier did not emit the safe AWS subprocess failure class" >&2
  exit 1
fi
if grep -Eq -- 'expectedvalue|actualvalue|create-change-set|execute-change-set|get-secret-value|put-role-policy' scripts/04.deploy/assess-platform-shell-foundation-drift/script.py; then
  echo "ERROR: Foundation drift classifier must not expose values, read secrets, or mutate configuration" >&2
  exit 1
fi
if ! grep -Eq -- 'describe-stack-resource-drifts' scripts/04.deploy/assess-platform-shell-foundation-drift/script.py; then
  echo "ERROR: Foundation drift classifier must retain its post-assessment structural classification read" >&2
  exit 1
fi
echo "Foundation drift-classifier local check passed."
