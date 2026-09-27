#!/usr/bin/env bash
#
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-postgresql-live-boundary.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the PostgreSQL live-boundary verifier without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: aws.runbook.kanbien-staging-postgresql-relational-reference-v1-stage6
#     path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-stage6-runbook.md
#   effects:
#   - read-only
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/script.py").read_text(encoding="utf-8"), "postgresql-live-boundary.py", "exec")'
result="$(bash scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/script.sh --validate --json)"
if [[ "$result" != *'"id": "source-policy"'* || "$result" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: PostgreSQL live-boundary source validation did not emit the expected safe result" >&2
  exit 1
fi
if grep -Eq -- 'get-secret-value|execute-change-set|create-db-instance|delete-db-instance|restore-db-instance' scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/script.py; then
  echo "ERROR: PostgreSQL live-boundary verifier must not retrieve secrets or mutate RDS" >&2
  exit 1
fi
echo "PostgreSQL relational live-boundary local check passed."
