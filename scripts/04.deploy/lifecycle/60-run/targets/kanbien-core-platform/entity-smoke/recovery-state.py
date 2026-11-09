#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.recovery-state
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate actual initial-stop custody and the preceding original-record read without requiring a stopped application to be ready.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import importlib.util
from pathlib import Path
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location("entity_smoke_recovery_stop", Path(__file__).with_name("failure-route.py"))
STOP = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(STOP)


class RecoveryStateFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise RecoveryStateFailure(code)


def stopped(route, args, provider, custody):
    C = route.C
    cache = C.ROOT / ".cache/entity-smoke-live" / args.proof_label
    store = STOP.F.StopStore(C, cache / "failure-attempts")
    root = store.read("root")
    require(root is not None and set(root["request"]) == {"packet"}, "recovery-original-stop-required")
    packet = STOP.validate_packet(root["request"]["packet"])
    STOP.F.validate_intent(C, packet["intent"], STOP.B.MAX_TASKS)
    policy = STOP.policy(C)
    require(packet["plan"].get("policy_sha256") == C.DEPLOY.fingerprint(policy)
            and packet["plan"].get("controller_sha256") == STOP.artifact(C), "recovery-stop-source-or-custody-changed")
    target = cache / "failure-receipts/stopped.json"
    C.RESOURCE.CONTROL.no_symlinks(target)
    require(target.is_file(), "recovery-stop-receipt-required")
    receipt = STOP.F.validate_receipt(C, C.read_json(target), root, cache)
    current = STOP.B.inspect(C, STOP.RESTORE, provider, custody, args.proof_label, cache)
    STOP.F.verify_scope_bindings(C, packet["intent"], current)
    require(STOP.F.terminal_tasks(C, provider, packet["intent"]) == receipt["facts"]["terminal_tasks"], "recovery-original-stop-not-terminal")
    require(current["service"] is not None, "recovery-feature-service-required")
    require(current["database"].get("state") == "same-incarnation", "recovery-source-database-incarnation-not-confirmed")
    return {"cache": cache, "root": root, "stop": receipt, "scope": current, "policy": policy}


def context(route, args, provider, custody, *, snapshot=None):
    C = route.C
    state = stopped(route, args, provider, custody)
    scope = state["scope"]
    # Require complete, stable own infrastructure and exact runtime/task bindings,
    # not successful application health or unnecessary operator RunTask authority.
    parameters, resources = route.owned_stack(provider, scope["binding"], scope["parameters"], state["cache"])
    snapshot = route.BINDING.DEPLOY.source()[1] if snapshot is None else snapshot
    server = route.BINDING.inspect(provider, "server", parameters, resources, snapshot)
    service = C.RESOURCE.service(provider, server["definition"], scope["service"]["desired_count"])
    network = service.get("networkConfiguration")
    awsvpc = network.get("awsvpcConfiguration") if isinstance(network, dict) else None
    require(service.get("launchType") == "FARGATE" and isinstance(network, dict) and set(network) == {"awsvpcConfiguration"}
            and isinstance(awsvpc, dict) and set(awsvpc) == {"assignPublicIp", "subnets", "securityGroups"} and awsvpc["assignPublicIp"] == "DISABLED"
            and isinstance(awsvpc["subnets"], list) and all(isinstance(item, str) for item in awsvpc["subnets"])
            and len(awsvpc["subnets"]) == len(server["subnets"]) and set(awsvpc["subnets"]) == set(server["subnets"])
            and awsvpc["securityGroups"] == [server["security_group"]], "recovery-runtime-network-not-confirmed")
    verifier = route.BINDING.inspect(provider, "verifier", parameters, resources, snapshot)
    declaration = C.yaml.safe_load((C.CONTRACT.parent / "declaration-contract.yml").read_text())
    deadlines = {row["id"].removeprefix("entity-smoke-"): row["completion"]["deadline_seconds"] for row in declaration["health_recovery"]["workloads"] if "completion" in row}
    base = {"binding": scope["binding"], "cache": state["cache"], "parameters": parameters, "resources": resources, "checked": verifier,
            "callees": {"server": server}, "binding_snapshot": snapshot, "completion_deadlines": deadlines,
            "report": {"plan": {"preflight_label": "entity-smoke-" + "0" * 24}}}
    selected = SimpleNamespace(**{**vars(args), "workload": "verifier", "operation": "read", "phase": "operation", "proof_stage": "server-replacement"})
    read = route.STEPS.observe_packet(route.dependencies(), base, selected, provider)
    require(read is not None, "recovery-pre-stop-original-read-required")
    require(read["receipt"]["result"].get("record_digest") == args.expected_digest, "recovery-original-digest-mismatch")
    timestamp = route.RUNNER.EVIDENCE.timestamp
    require(timestamp(read["receipt"]["task"]["stopped_at"]) <= timestamp(state["root"]["reserved_at"])
            and timestamp(read["reservation"]["reserved_at"]) <= timestamp(state["root"]["reserved_at"]), "recovery-original-read-not-before-stop")
    return {**state, "task_context": base, "read": read, "server": server}


def validate_restart(C, value, packet, reservation, cache):
    require(isinstance(value, dict) and set(value) == {"schema", "packet", "result", "server", "realization_evidence", "realization_evidence_sha256", "independent_data_readback", "migration_history_readback"}
            and value["schema"] == "deploy/entity-smoke-initial-restart-receipt/v1" and value["packet"] == packet
            and value["independent_data_readback"] is False and value["migration_history_readback"] is False, "recovery-restart-receipt-invalid")
    result, server = value["result"], value["server"]
    require(isinstance(result, dict) and result.get("status") == "completed" and result.get("reservation") == reservation
            and isinstance(result.get("facts"), dict) and set(result["facts"]) == {"desired_count", "running_count", "tasks"}
            and all(type(result["facts"].get(key)) is int and result["facts"][key] == 1 for key in ("desired_count", "running_count"))
            and isinstance(server, dict) and set(server) == {"task", "created_at", "started_at"} and result["facts"].get("tasks") == [server["task"]], "recovery-restart-facts-invalid")
    require(isinstance(server["task"], str) and C.re.fullmatch(r"arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":task/" + C.RESOURCE.CLUSTER + r"/[a-f0-9]{32}", server["task"]), "recovery-restart-facts-invalid")
    require(C.RESOURCE.timestamp(server["started_at"]) >= C.RESOURCE.timestamp(server["created_at"]) >= C.RESOURCE.timestamp(reservation["reserved_at"]), "recovery-restart-time-invalid")
    reference = value["realization_evidence"]
    prefix = str((cache / "initial-restart-realization").relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and C.re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):])
            and C.digest_file(C.ROOT / reference) == value["realization_evidence_sha256"], "recovery-restart-gate-changed")
    evidence = C.read_json(C.ROOT / reference)
    require(isinstance(evidence, dict) and evidence.get("plan_sha256") == packet["plan_sha256"]
            and isinstance(evidence.get("facts"), dict) and [row.get("gate") for row in evidence["facts"].get("gate_evidence", [])] == list(C.GATE.GATE_ORDER[:7]), "recovery-restart-gate-invalid")
    return value
