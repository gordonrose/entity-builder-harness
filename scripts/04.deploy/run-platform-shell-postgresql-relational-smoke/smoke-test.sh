#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py").read_text(encoding="utf-8"), "postgresql-relational-smoke.py", "exec")'
if [[ "$(bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --validate)" != '{"postgresql_relational_smoke":"validated"}' ]]; then
  echo "ERROR: relational smoke validation must emit only the reviewed safe verdict" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --execute >/dev/null 2>&1; then
  echo "ERROR: relational smoke execution must require its explicit fixed approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --validate --approve-relational-stage6 >/dev/null 2>&1; then
  echo "ERROR: relational smoke approval must be unavailable in validation mode" >&2
  exit 1
fi
if rg -q 'parser\.add_argument\("--(target|database|task-definition|queue-url|secret|restore-database|timeout)' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: relational smoke must not accept caller-selected live target inputs" >&2
  exit 1
fi
echo "PostgreSQL relational smoke local validation passed."
