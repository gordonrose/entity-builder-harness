#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.recovery-steps
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Require actual initial restart before separately admitted original-record and applied-migration-history observations without replay or fabricated preservation claims.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import importlib.util
from pathlib import Path
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location("entity_smoke_recovery_steps_state", Path(__file__).with_name("recovery-state.py"))
STATE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(STATE)


class RecoveryStepFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise RecoveryStepFailure(code)


def supported(args):
    return getattr(args, "proof_stage", "baseline") == "initial-recovery" and (args.workload, args.operation) in {("verifier", "read"), ("administration", "observe-migration-state")}


def failures():
    return (RecoveryStepFailure, STATE.RecoveryStateFailure, STATE.STOP.RecoveryFailure, STATE.STOP.F.StopFailure,
            STATE.STOP.B.FailureBindingError, STATE.STOP.SUCCESSION.SuccessionFailure, STATE.STOP.RESTORE.RESOURCE.ResourceFailure)


def failure_item(failure):
    if isinstance(failure, (STATE.STOP.RecoveryFailure, STATE.STOP.F.StopFailure, STATE.STOP.B.FailureBindingError)):
        return failure.item
    return None


def restart(route, context, args, provider, *, require_current=True):
    C, runner, steps = route.C, route.RUNNER, route.STEPS
    state = STATE.context(route, args, provider, context["custody"], snapshot=context.get("binding_snapshot"))
    target = context["cache"] / "initial-restart-receipt.json"
    runner.CONTROL.no_symlinks(target)
    if not target.is_file(): raise steps.PrerequisiteMissing("initial-restart")
    value = C.read_json(target)
    require(isinstance(value, dict) and isinstance(value.get("packet"), dict), "recovery-step-restart-invalid")
    packet = value["packet"]
    require(set(packet) == {"schema", "plan", "request", "plan_sha256"} and packet["schema"] == "deploy/entity-smoke-initial-restart-plan-packet/v1"
            and isinstance(packet["plan"], dict) and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "recovery-step-restart-plan-invalid")
    request, plan = packet["request"], packet["plan"]
    C.RESOURCE.validate_request("start-runtime", request)
    require(request["binding"] == {**context["binding"], "record_digest": args.expected_digest} and request["definition"] == state["server"]["definition"]
            and plan.get("binding") == request["binding"] and plan.get("request_sha256") == C.DEPLOY.fingerprint(request)
            and plan.get("controller_sha256") == STATE.STOP.artifact(C) and plan.get("policy_sha256") == C.DEPLOY.fingerprint(state["policy"])
            and plan.get("stop_sha256") == C.DEPLOY.fingerprint(state["stop"]) and plan.get("original_read_sha256") == C.DEPLOY.fingerprint(state["read"])
            and plan.get("configuration_sha256") == C.DEPLOY.fingerprint({"parameters": state["scope"]["parameters"], "resources": state["scope"]["resources"], "server": state["server"]}), "recovery-step-restart-binding-mismatch")
    for path in (context["cache"] / "initial-restart-plan.json", context["cache"] / "initial-restart-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json")):
        require(C.read_json(path) == packet, "recovery-step-restart-plan-not-retained")
    reservation = C.RESOURCE.ResourceStore(context["cache"] / "attempts").read("start-runtime", request)
    require(reservation is not None, "recovery-step-restart-journal-required")
    STATE.validate_restart(C, value, packet, reservation, context["cache"])
    timestamp = runner.EVIDENCE.timestamp
    require(timestamp(reservation["reserved_at"]) >= timestamp(state["stop"]["facts"]["observed_at"]), "recovery-step-start-predates-stop")
    server = C.RESOURCE.task(provider, value["server"]["task"], request["definition"], request["binding"]["image_digest"])
    if require_current:
        service = C.RESOURCE.service(provider, request["definition"], 1)
        require(server.get("lastStatus") == "RUNNING" and server.get("healthStatus") == "HEALTHY" and service.get("runningCount") == 1 and service.get("pendingCount") == 0
                and C.RESOURCE.running_service_tasks(provider) == [server["taskArn"]], "recovery-step-runtime-not-confirmed")
    require(timestamp(server.get("createdAt")) == timestamp(value["server"]["created_at"])
            and timestamp(server.get("startedAt")) == timestamp(value["server"]["started_at"]), "recovery-step-runtime-time-changed")
    after = max(reservation["reserved_at"], value["server"]["started_at"], key=timestamp)
    return {"state": state, "restart": value, "reservation": reservation, "required_after": after,
            "packets": {"initial-stop": state["stop"], "initial-restart": value}}


def require_active(route, context, args, provider, state):
    C, runner, steps = route.C, route.RUNNER, route.STEPS
    current_request = steps.request(route, context, args)
    current_reservation = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts").read(steps.key(args), current_request)
    require(sum(row["workload"] != "server" for row in state["scope"]["active_tasks"].values()) <= 1, "recovery-step-active-job-set-not-confirmed")
    for arn, row in state["scope"]["active_tasks"].items():
        if row["workload"] == "server": continue
        require(current_reservation is not None, "recovery-step-active-job-not-reserved")
        task = C.RESOURCE.only(provider("ecs", "describe-tasks", cluster=C.RESOURCE.CLUSTER, tasks=[arn]), "tasks")
        runner.CONTROL.exact_task(task, current_reservation)


def prerequisites(route, context, args, provider):
    value = restart(route, context, args, provider)
    require_active(route, context, args, provider, value["state"])
    C, runner, steps = route.C, route.RUNNER, route.STEPS
    timestamp = runner.EVIDENCE.timestamp
    after, packets = value["required_after"], value["packets"]
    if args.workload == "administration":
        selected = SimpleNamespace(**{**vars(args), "workload": "verifier", "operation": "read", "phase": "operation"})
        checked = route.BINDING.inspect(provider, "verifier", context["parameters"], context["resources"], context.get("binding_snapshot"))
        read = steps.observe_packet(route, {**context, "checked": checked}, selected, provider)
        if read is None: raise steps.PrerequisiteMissing("initial-recovery-original-read")
        require(timestamp(read["receipt"]["task"]["created_at"]) >= timestamp(after)
                and read["receipt"]["result"].get("record_digest") == args.expected_digest, "recovery-step-original-read-invalid")
        after, packets["initial-recovery-original-read"] = read["receipt"]["task"]["stopped_at"], read
    return {"required_after": after, "packets": packets}


def validate_result(args, receipt):
    if supported(args) and args.phase == "operation" and args.workload == "administration":
        require(receipt["result"].get("code") == "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED", "recovery-migration-history-not-applied")
