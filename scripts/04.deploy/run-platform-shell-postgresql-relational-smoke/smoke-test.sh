#!/usr/bin/env bash
#
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-postgresql-relational-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the PostgreSQL relational proof command without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: deploy.script.run-platform-shell-postgresql-relational-smoke.readme
#     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/README.md
#   effects:
#   - read-only
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
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --execute-recovery-continuation >/dev/null 2>&1; then
  echo "ERROR: recovery continuation execution must require its explicit fixed approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --diagnose-bootstrap-recovery >/dev/null 2>&1; then
  echo "ERROR: bootstrap failure diagnosis must require its explicit fixed approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --reconcile-current-state --approve-relational-stage6 >/dev/null 2>&1; then
  echo "ERROR: aggregate-state reconciliation must not accept an execution approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --execute --execute-bootstrap-recovery --approve-relational-stage6 --approve-relational-bootstrap-recovery >/dev/null 2>&1; then
  echo "ERROR: bootstrap recovery must be mutually exclusive with the full proof" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --execute-bootstrap-recovery --execute-recovery-continuation --approve-relational-bootstrap-recovery --approve-relational-recovery-continuation >/dev/null 2>&1; then
  echo "ERROR: recovery continuation must be mutually exclusive with bootstrap recovery" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --validate --approve-relational-stage6 >/dev/null 2>&1; then
  echo "ERROR: relational smoke approval must be unavailable in validation mode" >&2
  exit 1
fi
if grep -Eq -- 'parser\.add_argument\("--(target|database|task-definition|queue-url|secret|restore-database|timeout)' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: relational smoke must not accept caller-selected live target inputs" >&2
  exit 1
fi
if ! grep -q 'created = True' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: relational smoke must own cleanup immediately after an accepted recovery restore" >&2
  exit 1
fi
if ! grep -Eq -- 'def execute_bootstrap_recovery' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap recovery must retain a dedicated one-stage execution path" >&2
  exit 1
fi
if ! grep -Eq -- 'def execute_recovery_continuation' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! grep -Eq -- 'prior_label_succeeded\("bootstrap", policy\)' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: recovery continuation must require one successful consumed bootstrap and never replay it" >&2
  exit 1
fi
if ! grep -Eq -- 'def diagnose_bootstrap_recovery' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! grep -Eq -- 'logs", "get-log-events"' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap diagnostic must retain only its fixed safe log classification path" >&2
  exit 1
fi
if ! grep -Eq -- 'bootstrap-runtime-module-unavailable' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! grep -Eq -- 'bootstrap-database-connectivity-failure' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap diagnostic must retain the reviewed allowlisted failure categories" >&2
  exit 1
fi
if ! grep -Eq -- 'def bootstrap_metadata_category' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! grep -Eq -- 'bootstrap-secret-injection-failure' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap diagnostic must safely classify no-log-stream terminal metadata" >&2
  exit 1
fi
if ! grep -Eq -- 'failure_category' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-task.ts || ! grep -Eq -- 'bootstrapFailureCategory' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts; then
  echo "ERROR: bootstrap must emit only an allowlisted failure category after a workload failure" >&2
  exit 1
fi
if ! grep -Eq -- 'code === "42501"' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts || ! grep -Eq -- 'phase === "bootstrap-input-validation-failure"' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts; then
  echo "ERROR: bootstrap authorization failures must retain their reviewed operation phase." >&2
  exit 1
fi
if ! grep -Eq -- 'GRANT psmokemigrate TO CURRENT_USER' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts || ! grep -Eq -- 'CREATE SCHEMA IF NOT EXISTS platform_smoke AUTHORIZATION psmokemigrate' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts; then
  echo "ERROR: bootstrap must establish the reviewed SET ROLE membership before assigning schema ownership." >&2
  exit 1
fi
if ! grep -Eq -- 'credentialsFromEnvironment\("RELATIONAL_MASTER_SECRET_JSON"\)' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts || ! grep -Eq -- 'host: migration\.host, port: migration\.port' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts; then
  echo "ERROR: bootstrap must support a credentials-only RDS-managed master secret through the target-owned migration connection endpoint" >&2
  exit 1
fi
python3 - <<'PY'
import runpy
from pathlib import Path
import tempfile

module = runpy.run_path(Path("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py"))
assert "/tmp/" not in str(module["DEFAULT_LEDGER_PATH"])
assert module["DEFAULT_LEDGER_PATH"].parent.name == "postgresql-stage6-receipts"
temporary = Path(tempfile.mkdtemp())
ledger_policy = {
    "ledger_path": temporary / "receipts.json",
    "labels": {stage: f"reviewed-{stage}" for stage in ("bootstrap", "migration", "relay", "worker", "restore_verification")},
    "attempt_limit_per_stage": 4,
    "attempt_limit_total": 20,
    "maximum_elapsed_seconds": 60,
    "maximum_cost_usd": 100,
    "cleanup_reserve_usd": 25,
    "estimated_stage_cost_usd": {stage: 1 for stage in ("bootstrap", "migration", "relay", "worker", "restore_verification")},
}
_, attempt, label = module["reserve_stage"]("bootstrap", ledger_policy)
assert attempt == 1 and label == "reviewed-bootstrap-a1"
module["record_stage_state"]("bootstrap", "succeeded", ledger_policy)
assert module["stage_succeeded"]("bootstrap", ledger_policy)

observed = []

def empty_task_list(arguments, _policy, allow_not_found=False):
    observed.append(arguments)
    return {"taskArns": []}

module["no_prior_label"].__globals__["aws"] = empty_task_list
module["no_prior_label"]("reviewed-fixed-label-a1", {"cluster": "reviewed-cluster"})
assert [arguments[-1] for arguments in observed] == ["RUNNING", "STOPPED"]

# The relational controller must consume the exact successful candidate receipt,
# including a successful later same-image reattempt, rather than re-deriving a
# divergent label shape.
candidate_image = "registry.example/platform-shell@sha256:" + "a" * 64
candidate_hash = module["hashlib"].sha256(("a" * 64).encode("ascii")).hexdigest()[:16]
candidate_receipts = temporary / "candidate-receipts.json"
candidate_receipts.write_text(module["json"].dumps({
    "schema": "postgresql-candidate-attempt-ledger/v1",
    "attempts": [
        {"image_hash": candidate_hash, "label": f"kb-candidate-{candidate_hash}-a1", "state": "failed"},
        {"image_hash": candidate_hash, "label": f"kb-candidate-{candidate_hash}-a2", "state": "succeeded"},
    ],
}), encoding="utf-8")
assert module["candidate_preflight_label"](candidate_image, candidate_receipts) == f"kb-candidate-{candidate_hash}-a2"

# Diagnosis must use the durable failed attempt label, not the unqualified
# base label that cannot identify a finite Recovery-5 task.
diagnostic_policy = {
    **ledger_policy,
    "ledger_path": temporary / "diagnostic-receipts.json",
    "labels": {stage: f"kb-pg6-{stage.replace('_verification', '')}-r5" for stage in ("bootstrap", "migration", "relay", "worker", "restore_verification")},
}
module["reserve_stage"]("bootstrap", diagnostic_policy)
module["record_stage_state"]("bootstrap", "failed", diagnostic_policy)
assert module["failed_bootstrap_receipt_label"](diagnostic_policy) == "kb-pg6-bootstrap-r5-a1"

observed = []
def successful_predecessor(arguments, _policy, allow_not_found=False):
    observed.append(arguments)
    if arguments[0:2] == ["ecs", "list-tasks"]:
        return {"taskArns": ["reviewed-task"]}
    return {"tasks": [{"containers": [{"name": "reviewed-container", "exitCode": 0}]}]}

module["prior_label_succeeded"].__globals__["aws"] = successful_predecessor
predecessor_policy = {
    **ledger_policy,
    "cluster": "reviewed-cluster",
    "containers": {"bootstrap": "reviewed-container"},
}
module["prior_label_succeeded"]("bootstrap", predecessor_policy)
assert observed[0][-1] == "STOPPED"

# A later-stage failure resumes only the first incomplete checkpoint after a restart.
for stage in ("migration",):
    module["reserve_stage"](stage, ledger_policy)
    module["record_stage_state"](stage, "succeeded", ledger_policy)
module["reserve_stage"]("relay", ledger_policy)
module["record_stage_state"]("relay", "failed", ledger_policy)
assert module["stage_succeeded"]("migration", ledger_policy)
assert not module["stage_succeeded"]("relay", ledger_policy)

# A timeout retains cleanup ownership in the durable receipt, even after process loss.
module["reserve_stage"]("worker", ledger_policy)
timeout_policy = {**ledger_policy, "cluster": "reviewed-cluster", "task_stop_seconds": 0}
module["stop_and_verify"].__globals__["aws"] = lambda *_args, **_kwargs: {"tasks": [{"lastStatus": "RUNNING"}]}
try:
    module["stop_and_verify"]("worker", "reviewed-task", timeout_policy)
except module["RelationalSmokeError"] as error:
    assert str(error) == "a timed-out relational stage has an unresolved cleanup obligation"
else:
    raise AssertionError("timeout cleanup was accepted without terminal proof")
assert module["load_ledger"](ledger_policy)["stages"]["worker"]["state"] == "timeout-cleanup-pending"

# A lost submission response is recorded as unknown and blocks another attempt.
module["reserve_stage"]("restore_verification", ledger_policy)
module["reconcile_unacknowledged_submission"].__globals__["aws"] = lambda *_args, **_kwargs: (_ for _ in ()).throw(module["RelationalSmokeError"]("provider-unavailable"))
try:
    module["reconcile_unacknowledged_submission"]("restore_verification", "reviewed-restore-verification-a1", {**ledger_policy, "cluster": "reviewed-cluster"})
except module["RelationalSmokeError"] as error:
    assert str(error) == "a relational stage submission outcome is uncertain and blocks retry"
else:
    raise AssertionError("uncertain acceptance was not blocked")
assert module["load_ledger"](ledger_policy)["stages"]["restore_verification"]["state"] == "unknown"

# Reloading the ledger preserves consumed limits; restart cannot reset the allowance.
reloaded = module["load_ledger"](ledger_policy)
assert len(reloaded["attempts"]) == 5

diagnostic_policy = {"bootstrap_diagnostic_categories": {
    "bootstrap-image-retrieval-failure",
    "bootstrap-secret-injection-failure",
    "bootstrap-essential-container-exited-without-log-stream",
}}
assert module["bootstrap_metadata_category"](
    {"stopCode": "TaskFailedToStart"},
    {"reason": "CannotPullContainerError"},
    diagnostic_policy,
) == "bootstrap-image-retrieval-failure"
assert module["bootstrap_metadata_category"](
    {"stopCode": "TaskFailedToStart"},
    {"reason": "ResourceInitializationError: secret retrieval"},
    diagnostic_policy,
) == "bootstrap-secret-injection-failure"
assert module["bootstrap_metadata_category"](
    {"stopCode": "EssentialContainerExited"},
    {},
    diagnostic_policy,
) == "bootstrap-essential-container-exited-without-log-stream"
assert module["derived_bootstrap_log_stream"](
    {"taskArn": "arn:aws:ecs:eu-west-1:123456789012:task/reviewed-cluster/0123456789abcdef0123456789abcdef"},
    {"bootstrap_diagnostic_log_stream_prefix": "relational-bootstrap/relational-bootstrap/"},
) == "relational-bootstrap/relational-bootstrap/0123456789abcdef0123456789abcdef"
assert module["derived_bootstrap_log_stream"](
    {"taskArn": "not-a-reviewed-task-arn"},
    {"bootstrap_diagnostic_log_stream_prefix": "relational-bootstrap/relational-bootstrap/"},
) is None

# Aggregate reconciliation exposes only fixed counts and posture verdicts.
reconciliation_globals = module["reconcile_current_state"].__globals__
reconciliation_globals["verify_account"] = lambda _policy: None
reconciliation_globals["update_complete"] = lambda _stack, _policy: None
reconciliation_globals["stack_outputs"] = lambda _policy: {"RelationalSmokeQueueUrl": "source", "RelationalSmokeDeadLetterQueueUrl": "dlq"}
reconciliation_globals["service_counts"] = lambda name, _policy: (1, 1) if name == module["SERVER_SERVICE"] else (0, 0)
reconciliation_globals["queue_total"] = lambda _url, _policy: 0
reconciliation_globals["source_database"] = lambda _policy: {"subnet_group": "reviewed"}
reconciliation_globals["restore_absent"] = lambda _policy: True
state = module["reconcile_current_state"]({"foundation_stack": "foundation", "service_stack": "service"})
assert state == {"source_database": "available-reviewed-posture", "restore_target": "absent", "server": {"desired": 1, "running": 1}, "worker": {"desired": 0, "running": 0}, "source_queue_total": 0, "dead_letter_queue_total": 0}
PY
if ! grep -q 'ALTER DEFAULT PRIVILEGES IN SCHEMA platform_smoke GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-migration.main.ts || grep -q 'ALTER DEFAULT PRIVILEGES FOR ROLE' infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-bootstrap.main.ts; then
  echo "ERROR: migration must own default privileges for its own future tables" >&2
  exit 1
fi
echo "PostgreSQL relational smoke local validation passed."
