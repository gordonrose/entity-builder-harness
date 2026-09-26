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
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --execute-bootstrap-recovery >/dev/null 2>&1; then
  echo "ERROR: bootstrap recovery execution must require its explicit fixed approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --diagnose-bootstrap-recovery >/dev/null 2>&1; then
  echo "ERROR: bootstrap failure diagnosis must require its explicit fixed approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --execute --execute-bootstrap-recovery --approve-relational-stage6 --approve-relational-bootstrap-recovery >/dev/null 2>&1; then
  echo "ERROR: bootstrap recovery must be mutually exclusive with the full proof" >&2
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
if ! grep -q 'created = True' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: relational smoke must own cleanup immediately after an accepted recovery restore" >&2
  exit 1
fi
if ! rg -q 'def execute_bootstrap_recovery' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap recovery must retain a dedicated one-stage execution path" >&2
  exit 1
fi
if ! rg -q 'def diagnose_bootstrap_recovery' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! rg -q 'logs", "get-log-events"' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap diagnostic must retain only its fixed safe log classification path" >&2
  exit 1
fi
python3 - <<'PY'
import runpy
from pathlib import Path

module = runpy.run_path(Path("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py"))
observed = []

def empty_task_list(arguments, _policy, allow_not_found=False):
    observed.append(arguments)
    return {"taskArns": []}

module["no_prior_label"].__globals__["aws"] = empty_task_list
module["no_prior_label"]("bootstrap", {"cluster": "reviewed-cluster", "labels": {"bootstrap": "reviewed-fixed-label"}})
assert [arguments[-1] for arguments in observed] == ["RUNNING", "STOPPED"]
PY
if ! grep -q 'ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts || grep -q 'ALTER DEFAULT PRIVILEGES FOR ROLE' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts; then
  echo "ERROR: migration must own default privileges for its own future tables" >&2
  exit 1
fi
echo "PostgreSQL relational smoke local validation passed."
