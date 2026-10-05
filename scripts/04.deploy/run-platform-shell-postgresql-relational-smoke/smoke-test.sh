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
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --reconcile-bootstrap-effects >/dev/null 2>&1; then
  echo "ERROR: bootstrap-effect reconciliation must require its explicit fixed approval guard" >&2
  exit 1
fi
if bash scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.sh --reconcile-bootstrap-effects --approve-relational-bootstrap-effects-reconciliation --approve-relational-bootstrap-recovery >/dev/null 2>&1; then
  echo "ERROR: bootstrap-effect reconciliation must reject every unrelated execution guard" >&2
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
if ! grep -Eq -- 'BOOTSTRAP_EFFECTS_RECONCILIATION_PROGRAM' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! grep -Eq -- "BEGIN TRANSACTION READ ONLY" scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py || ! grep -Eq -- 'bootstrap_effects_reconciled' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap-effect reconciliation must retain its fixed read-only program and safe result." >&2
  exit 1
fi
if grep -Eq -- 'BOOTSTRAP_EFFECTS_RECONCILIATION_PROGRAM.*(CREATE ROLE|CREATE SCHEMA|ALTER ROLE|GRANT |INSERT INTO|UPDATE [A-Za-z_]+ SET|DELETE FROM|DROP )' scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py; then
  echo "ERROR: bootstrap-effect reconciliation must not contain a database-writing SQL command." >&2
  exit 1
fi
python3 - <<'PY'
import runpy
from pathlib import Path
import subprocess
import tempfile

module = runpy.run_path(Path("scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py"))
assert "/tmp/" not in str(module["DEFAULT_LEDGER_PATH"])
assert module["DEFAULT_LEDGER_PATH"].parent.name == "postgresql-stage6-receipts"
program = module["BOOTSTRAP_EFFECTS_RECONCILIATION_PROGRAM"]
program_result = subprocess.run(["node", "-e", program], capture_output=True, check=False, text=True)
assert program_result.returncode == 1
assert not program_result.stdout.strip() or program_result.stdout.strip() == '{"level":"error","message":"kanbien-platform.relational-smoke.bootstrap_effects_reconciled","fields":{"outcome":"failed"}}'
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

# The requested restore point is durable and must include the completed proof
# before an RDS restore can be submitted; a lagging point blocks without an
# infrastructure effect.
restore_point_policy = {**ledger_policy, "ledger_path": temporary / "restore-point-receipts.json"}
restore_point_ledger = module["empty_ledger"]()
restore_point_ledger["stages"]["worker"] = {"state": "succeeded", "updated_at": 1_700_000_000.0}
module["save_ledger"](restore_point_policy, restore_point_ledger)
restore_source = {"latest_restorable_time": "2023-11-14T22:14:00+00:00"}
module["record_restore_point"](restore_point_policy, restore_source, "submission-in-progress")
restore_receipt = module["load_ledger"](restore_point_policy)["stages"]["restore_point_reconciliation"]
assert restore_receipt["proof_data_included"] is True and restore_receipt["restore_mode"] == "latest-restorable-time"
try:
    module["record_restore_point"](restore_point_policy, {"latest_restorable_time": "2023-11-14T22:12:00+00:00"}, "submission-in-progress")
except module["RelationalSmokeError"] as error:
    assert str(error) == "the requested restore point does not yet include the completed worker proof"
else:
    raise AssertionError("restore request accepted a point preceding the completed proof")

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

# A controller inspection failure remains failed.  A separate terminal
# assessment can authorize only its exact immutable image and first consumed
# label after independently proving the healthy controlled stop.
candidate_assessment = temporary / "candidate-assessment.json"
candidate_receipts.write_text(module["json"].dumps({
    "schema": "postgresql-candidate-attempt-ledger/v1",
    "attempts": [{"image_hash": candidate_hash, "label": f"kb-candidate-{candidate_hash}-a1", "state": "failed"}],
}), encoding="utf-8")
valid_candidate_assessment = {"stage": module["CANDIDATE_EXECUTION_ASSESSMENT_STAGE"], "state": "succeeded", "account": module["ACCOUNT"], "region": module["REGION"], "image": candidate_image, "label": f"kb-candidate-{candidate_hash}-a1", "original_receipt_state": "failed", "task_definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-staging-platform-shell-candidate-preflight:8", "task_definition_revision": 8, "last_status": "STOPPED", "health_status": "HEALTHY", "stop_code": "UserInitiated", "stopped_reason": "controlled-candidate-preflight-complete", "platform_shell_exit_code": 0, "platform_shell_health_status": "HEALTHY"}
candidate_assessment.write_text(module["json"].dumps({"stages": {module["CANDIDATE_EXECUTION_ASSESSMENT_STAGE"]: valid_candidate_assessment}}), encoding="utf-8")
assert module["candidate_preflight_label"](candidate_image, candidate_receipts, candidate_assessment) == f"kb-candidate-{candidate_hash}-a1"
for invalid in (
    {**valid_candidate_assessment, "label": f"kb-candidate-{candidate_hash}-a2"},
    {**valid_candidate_assessment, "original_receipt_state": "succeeded"},
    {**valid_candidate_assessment, "state": "failed"},
    {key: value for key, value in valid_candidate_assessment.items() if key != "platform_shell_exit_code"},
):
    candidate_assessment.write_text(module["json"].dumps({"stages": {module["CANDIDATE_EXECUTION_ASSESSMENT_STAGE"]: invalid}}), encoding="utf-8")
    try:
        module["candidate_preflight_label"](candidate_image, candidate_receipts, candidate_assessment)
    except module["RelationalSmokeError"]:
        pass
    else:
        raise AssertionError("missing, mismatched, or unexplained candidate evidence was accepted")

candidate_task = {
    "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/reviewed-candidate:8",
    "lastStatus": "STOPPED", "healthStatus": "HEALTHY", "stopCode": "UserInitiated", "stoppedReason": "controlled-candidate-preflight-complete",
    "containers": [{"name": "platform-shell", "image": candidate_image, "imageDigest": "sha256:" + "a" * 64, "lastStatus": "STOPPED", "healthStatus": "HEALTHY", "exitCode": 0}],
}
assert module["terminal_candidate_facts"](candidate_task, candidate_image, candidate_task["taskDefinitionArn"])["task_definition_revision"] == 8
candidate_task["containers"][0]["exitCode"] = 1
try:
    module["terminal_candidate_facts"](candidate_task, candidate_image, candidate_task["taskDefinitionArn"])
except module["RelationalSmokeError"]:
    pass
else:
    raise AssertionError("an unsuccessful candidate container exit was accepted")

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

# The fixed reconciliation consumes a single durable diagnostic receipt, uses
# the bootstrap task family, and returns only its allowlisted boolean facts.
effects_policy = {
    **ledger_policy,
    "ledger_path": temporary / "effects-receipts.json",
    "labels": {**ledger_policy["labels"], module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"]: "reviewed-effects"},
    "estimated_stage_cost_usd": {**ledger_policy["estimated_stage_cost_usd"], module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"]: 1},
}
_, attempt, label = module["reserve_stage"](module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"], effects_policy)
assert attempt == 1 and label == "reviewed-effects-a1"
module["record_stage_state"](module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"], "succeeded", effects_policy)
try:
    module["reserve_stage"](module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"], effects_policy)
except module["RelationalSmokeError"]:
    pass
else:
    raise AssertionError("a consumed bootstrap-effect reconciliation was reusable")

facts = {key: True for key in module["BOOTSTRAP_EFFECTS_RECONCILIATION_FACTS"]}
effect_globals = module["bootstrap_effects_facts"].__globals__
effect_globals["stack_outputs"] = lambda _policy: {"RelayLogGroupName": "reviewed-log-group"}
effect_globals["aws"] = lambda arguments, _policy, allowed_not_found_code=None: {"events": [{"message": module["json"].dumps({"level": "info", "message": "kanbien-platform.relational-smoke.bootstrap_effects_reconciled", "fields": {"outcome": "succeeded", **facts}})}]}
assert module["bootstrap_effects_facts"]({"containers": [{"name": "reviewed-bootstrap", "logStreamName": "reviewed-stream"}]}, {"containers": {"bootstrap": "reviewed-bootstrap"}}) == facts

gate_policy = {**effects_policy, "ledger_path": temporary / "gate-receipts.json", "source_database": "reviewed-source"}
try:
    module["require_bootstrap_effects_reconciliation"](gate_policy)
except module["RelationalSmokeError"] as error:
    assert str(error) == "bootstrap recovery requires a validated bootstrap-effect assessment"
else:
    raise AssertionError("bootstrap was not gated on an assessment")

fact_image = "registry.example/platform-shell@sha256:" + "c" * 64
fact_receipts = {
    stage: {"stage": stage, "label": label, "state": "succeeded", "submitted_at": index + 1,
            "task_definition_revision": 9, "image": fact_image,
            "diagnostic_code_sha256": module["hashlib"].sha256(stage.encode()).hexdigest()}
    for index, (stage, label) in enumerate(module["BOOTSTRAP_EFFECTS_FACT_LABELS"].items())
}
ledger = module["empty_ledger"]()
ledger["stages"] = {"bootstrap_effects_reconciliation": {"state": "failed", "label": "kb-pg6-bootstrap-effects-r5-a1"}, **fact_receipts}
module["save_ledger"](gate_policy, ledger)
(gate_policy["ledger_path"].parent / "bootstrap-effects-facts-fixture.stdout").write_text(module["json"].dumps({"postgresql_relational_bootstrap_effect_facts": module["RECOVERABLE_INTERRUPTED_SCHEMA_SETUP"]}), encoding="utf-8")
assessment_globals = module["assess_bootstrap_effects"].__globals__
assessment_globals["source_database"] = lambda _policy: None
assert module["assess_bootstrap_effects"](gate_policy) == "recoverable-interrupted-schema-setup"
module["require_bootstrap_effects_reconciliation"](gate_policy)

# Evidence without both exact completed receipts remains blocked.
bad_policy = {**gate_policy, "ledger_path": temporary / "bad-gate.json"}
module["save_ledger"](bad_policy, {"schema": "postgresql-stage6-attempt-ledger/v1", "started_at": 1, "stages": {"bootstrap_effects_facts_one": fact_receipts["bootstrap_effects_facts_one"]}, "attempts": [], "estimated_cost_usd": 0})
try:
    module["assess_bootstrap_effects"](bad_policy)
except module["RelationalSmokeError"]:
    pass
else:
    raise AssertionError("assessment accepted missing fact evidence")

# A valid-looking pair with an unexplained fact pattern remains blocked.
unexplained_policy = {**gate_policy, "ledger_path": temporary / "unexplained-gate.json"}
module["save_ledger"](unexplained_policy, {"schema": "postgresql-stage6-attempt-ledger/v1", "started_at": 1, "stages": fact_receipts, "attempts": [], "estimated_cost_usd": 0})
(unexplained_policy["ledger_path"].parent / "bootstrap-effects-facts-fixture.stdout").write_text(module["json"].dumps({"postgresql_relational_bootstrap_effect_facts": {**module["RECOVERABLE_INTERRUPTED_SCHEMA_SETUP"], "schema_exists": True}}), encoding="utf-8")
try:
    module["assess_bootstrap_effects"](unexplained_policy)
except module["RelationalSmokeError"]:
    pass
else:
    raise AssertionError("assessment accepted unexplained partial facts")

# The receipt is persisted before launch with the exact immutable task binding
# and fixed diagnostic code hash, never a task identifier or provider payload.
definition_image = "registry.example/platform-shell@sha256:" + "b" * 64
definition_globals = module["assert_task_definition"].__globals__
definition_globals["aws"] = lambda *_args, **_kwargs: {"taskDefinition": {"family": "reviewed-bootstrap-family", "revision": 9, "containerDefinitions": [{"name": "reviewed-bootstrap", "image": definition_image}]}}
binding = module["assert_task_definition"]("bootstrap", {"families": {"bootstrap": "reviewed-bootstrap-family"}, "containers": {"bootstrap": "reviewed-bootstrap"}})
assert binding == {"task_definition_revision": 9, "image": definition_image}
bound_policy = {**effects_policy, "ledger_path": temporary / "bound-effects-receipts.json"}
code_hash = module["hashlib"].sha256(module["BOOTSTRAP_EFFECTS_RECONCILIATION_PROGRAM"].encode("utf-8")).hexdigest()
module["reserve_stage"](module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"], bound_policy, {**binding, "diagnostic_code_sha256": code_hash})
bound_receipt = module["load_ledger"](bound_policy)["stages"][module["BOOTSTRAP_EFFECTS_RECONCILIATION_STAGE"]]
assert {key: bound_receipt[key] for key in ("task_definition_revision", "image", "diagnostic_code_sha256")} == {**binding, "diagnostic_code_sha256": code_hash}

observed = []
def successful_predecessor(arguments, _policy, allow_not_found=False):
    observed.append(arguments)
    if arguments[0:2] == ["ecs", "list-tasks"]:
        return {"taskArns": [] if arguments[-1] == "RUNNING" else ["reviewed-task"]}
    return {"tasks": [{"containers": [{"name": "reviewed-container", "exitCode": 0}]}]}

module["prior_label_succeeded"].__globals__["aws"] = successful_predecessor
predecessor_policy = {
    **ledger_policy,
    "cluster": "reviewed-cluster",
    "containers": {"bootstrap": "reviewed-container"},
}
module["prior_label_succeeded"]("bootstrap", predecessor_policy)
assert [arguments[-1] for arguments in observed[:2]] == ["RUNNING", "STOPPED"]

# ECS may expire stopped-task history after a successful durable receipt.  It
# remains a safe predecessor only when no matching task is still running.
module["prior_label_succeeded"].__globals__["aws"] = lambda arguments, *_args, **_kwargs: {"taskArns": []} if arguments[0:2] == ["ecs", "list-tasks"] else AssertionError("expired task metadata must not be described")
module["prior_label_succeeded"]("bootstrap", predecessor_policy)
module["prior_label_succeeded"].__globals__["aws"] = lambda arguments, *_args, **_kwargs: {"taskArns": ["still-running"]} if arguments[0:2] == ["ecs", "list-tasks"] else {}
try:
    module["prior_label_succeeded"]("bootstrap", predecessor_policy)
except module["RelationalSmokeError"]:
    pass
else:
    raise AssertionError("a live predecessor was accepted after receipt retention")

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
