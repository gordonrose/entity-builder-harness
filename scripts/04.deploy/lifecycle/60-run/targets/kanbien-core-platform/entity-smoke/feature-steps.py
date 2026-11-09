#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.feature-steps
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind initial feature operations and read-only uncertain-create observation to activation, original reservations and immutable proof receipts.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from types import SimpleNamespace

SUPPORTED = {("verifier", operation) for operation in ("create", "observe-create", "lifecycle", "read")} | {("database-proof", "collision")}


class FeatureStepFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(value, code):
    if not value: raise FeatureStepFailure(code)


def supported(args):
    return (args.workload, args.operation) in SUPPORTED


def arguments(args, workload, operation):
    return SimpleNamespace(**{**vars(args), "workload": workload, "operation": operation, "phase": "operation", "proof_stage": "baseline", "expected_digest": None})


def checked_context(route, context, workload):
    return {**context, "checked": route.BINDING.inspect(context["provider"], workload, context["parameters"], context["resources"], context.get("binding_snapshot"))}


def original_terminal(route, context, args):
    runner, steps, provider = route.RUNNER, route.STEPS, context["provider"]
    selected = arguments(args, "verifier", "create")
    request = steps.request(route, checked_context(route, context, "verifier"), selected)
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    reservation = store.read(steps.key(selected), request)
    require(reservation is not None, "feature-original-create-reservation-required")
    _, task = runner.CONTROL.reconcile_reserved(provider, reservation)
    containers = task.get("containers")
    require(task.get("lastStatus") == "STOPPED", "feature-original-create-not-terminal")
    require(task.get("launchType") == "FARGATE", "feature-original-create-launch-type-not-confirmed")
    require(isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict)
            and containers[0].get("name") == "entity-smoke-verifier", "feature-original-create-container-not-confirmed")
    require(containers[0].get("imageDigest") == context["binding"]["image_digest"], "feature-original-create-image-not-confirmed")
    stopped = task.get("stoppedAt")
    created, started, stop = (runner.EVIDENCE.timestamp(task.get(field)) for field in ("createdAt", "startedAt", "stoppedAt"))
    require(created <= started <= stop and runner.EVIDENCE.timestamp(reservation["reserved_at"]).timestamp() <= created.timestamp() + 60, "feature-original-create-order-invalid")
    return {"reservation": reservation, "task_arn": task["taskArn"], "stopped_at": stopped}


def observe(route, context, args, workload, operation, digest=None):
    selected = arguments(args, workload, operation)
    selected.expected_digest = digest
    return route.STEPS.observe_packet(route, checked_context(route, context, workload), selected, context["provider"])


def activation(route, context, args):
    C, steps, provider = route.C, route.STEPS, context["provider"]
    path = context["cache"] / "receipts/activate.json"
    route.RUNNER.CONTROL.no_symlinks(path)
    if not path.exists(): raise steps.PrerequisiteMissing("activation")
    value = C.read_json(path)
    require(isinstance(value, dict) and set(value) == {"schema", "binding", "result"} and value["schema"] == "deploy/entity-smoke-infrastructure-receipt/v1"
            and value["binding"] == context["binding"] and isinstance(value["result"], dict) and value["result"].get("status") == "completed"
            and isinstance(value["result"].get("reservation"), dict) and isinstance(value["result"]["reservation"].get("request"), dict), "feature-activation-receipt-invalid")
    reservation = value["result"]["reservation"]
    expected = C.DEPLOY.request(context["binding"], context["parameters"], True)
    require(all(reservation["request"].get(key) == content for key, content in expected.items()), "feature-activation-binding-mismatch")
    request = reservation["request"]
    store = C.RESOURCE.ResourceStore(context["cache"] / "attempts")
    current = C.DEPLOY.observe(provider, store, context["binding"], context["parameters"], request["change_set_arn"], request["stack_arn"], activate=True)
    require(current == value["result"] and current["facts"]["resources"] == context["resources"], "feature-activation-not-confirmed")
    prep_args = arguments(args, "database-proof", "permissions")
    prefix = steps.prerequisites(route, context, prep_args, provider)
    permissions = observe(route, context, args, "database-proof", "permissions")
    if permissions is None: raise steps.PrerequisiteMissing("permissions")
    require(route.RUNNER.EVIDENCE.timestamp(permissions["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(prefix["required_after"])
            and route.RUNNER.EVIDENCE.timestamp(reservation["reserved_at"]) >= route.RUNNER.EVIDENCE.timestamp(permissions["receipt"]["task"]["stopped_at"]), "feature-activation-order-invalid")
    return {"required_after": reservation["reserved_at"], "packets": {**prefix["packets"], "permissions": {"reservation": permissions["reservation"], "receipt": permissions["receipt"]}, "activation": value}}


def replacement(route, context, args, base, digest):
    C, provider = route.C, context["provider"]
    path = context["cache"] / "replacement-receipt.json"
    route.RUNNER.CONTROL.no_symlinks(path)
    if not path.exists(): raise route.STEPS.PrerequisiteMissing("server-replacement")
    receipt = C.read_json(path)
    require(isinstance(receipt, dict) and set(receipt) == {"schema", "packet", "result", "realization_evidence", "realization_evidence_sha256"}
            and receipt["schema"] == "deploy/entity-smoke-replacement-receipt/v1", "feature-replacement-receipt-invalid")
    packet = receipt["packet"]
    require(isinstance(packet, dict) and set(packet) == {"schema", "plan", "request", "plan_sha256"}
            and packet["schema"] == "deploy/entity-smoke-replacement-plan-packet/v1" and isinstance(packet["plan"], dict)
            and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "feature-replacement-plan-invalid")
    request, plan = packet["request"], packet["plan"]
    C.RESOURCE.validate_request("server-replacement", request)
    require(request["binding"] == {**context["binding"], "record_digest": digest} and request["definition"] == context["resources"]["ServerTaskDefinition"]["physical_id"]
            and plan.get("target") == C.RESOURCE.CLUSTER and plan.get("scope") == "entity-smoke" and type(plan.get("maximum_task_stops")) is int and plan["maximum_task_stops"] == 1
            and all(plan.get(key) is False for key in ("database_mutation", "task_launch", "automatic_retry", "post_replacement_record_readback"))
            and plan.get("binding") == request["binding"] and plan.get("request_sha256") == C.DEPLOY.fingerprint(request)
            and plan.get("controller_sha256") == context["artifact"]
            and plan.get("configuration_sha256") == C.DEPLOY.fingerprint({"parameters": context["parameters"], "resources": context["resources"], "server": context["callees"]["server"]}), "feature-replacement-binding-mismatch")
    active = context["cache"] / "replacement-plan.json"
    approved = context["cache"] / "replacement-plans" / (packet["plan_sha256"].removeprefix("sha256:") + ".json")
    require(C.read_json(active) == packet and C.read_json(approved) == packet, "feature-replacement-plan-not-retained")
    store = C.RESOURCE.ResourceStore(context["cache"] / "attempts")
    reservation = store.read("server-replacement", request)
    require(reservation is not None and isinstance(receipt["result"], dict) and receipt["result"].get("reservation") == reservation,
            "feature-replacement-reservation-required")
    baseline_read = observe(route, context, args, "verifier", "read", digest)
    require(baseline_read is not None, "feature-replacement-baseline-read-required")
    require(plan.get("baseline_read_sha256") == C.DEPLOY.fingerprint(baseline_read) and plan.get("prerequisites_sha256") == C.DEPLOY.fingerprint(base)
            and route.RUNNER.EVIDENCE.timestamp(baseline_read["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(base["required_after"])
            and route.RUNNER.EVIDENCE.timestamp(reservation["reserved_at"]) >= route.RUNNER.EVIDENCE.timestamp(baseline_read["receipt"]["task"]["stopped_at"]), "feature-replacement-order-invalid")
    # The checked existing journal makes this observation-only: the helper must
    # not be allowed to reserve a fresh stop from a supplied receipt alone.
    current = C.RESOURCE.replace_runtime(provider, store, request["binding"], request["definition"], request["original_task"])
    require(current.get("status") == "completed" and current == receipt["result"], "feature-replacement-not-confirmed")
    reference = receipt["realization_evidence"]
    prefix = str((context["cache"] / "replacement-realization").relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(prefix) and route.re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(prefix):])
            and C.digest_file(C.ROOT / reference) == receipt["realization_evidence_sha256"], "feature-replacement-gate-evidence-changed")
    gate = C.read_json(C.ROOT / reference)
    require(isinstance(gate, dict) and gate.get("plan_sha256") == packet["plan_sha256"] and isinstance(gate.get("facts"), dict)
            and [row.get("gate") for row in gate["facts"].get("gate_evidence", [])] == list(C.GATE.GATE_ORDER[:7]), "feature-replacement-gate-evidence-invalid")
    required_after = max(baseline_read["receipt"]["task"]["stopped_at"], reservation["reserved_at"], current["facts"]["successor_started_at"], key=route.RUNNER.EVIDENCE.timestamp)
    return {"required_after": required_after, "packets": {**base["packets"], "baseline-read": baseline_read, "server-replacement": receipt}}


def prerequisites(route, context, args, provider):
    if not supported(args): return None
    context = {**context, "provider": provider}
    base = activation(route, context, args)
    if args.operation == "create": return base
    if args.operation == "observe-create":
        terminal = original_terminal(route, context, args)
        base["packets"]["original-create-terminal"] = terminal
        base["required_after"] = max(base["required_after"], terminal["stopped_at"], key=route.RUNNER.EVIDENCE.timestamp)
        return base
    primary = observe(route, context, args, "verifier", "create")
    if primary is None:
        primary = observe(route, context, args, "verifier", "observe-create")
        if primary is None: raise route.STEPS.PrerequisiteMissing("original-record")
        terminal = original_terminal(route, context, args)
        require(route.RUNNER.EVIDENCE.timestamp(primary["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(terminal["stopped_at"]), "feature-create-observer-order-invalid")
        base["packets"]["original-create-terminal"] = terminal
    base["packets"]["original-record"] = {"reservation": primary["reservation"], "receipt": primary["receipt"]}
    require(route.RUNNER.EVIDENCE.timestamp(primary["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(base["required_after"]), "feature-original-record-order-invalid")
    base["required_after"] = primary["receipt"]["task"]["stopped_at"]
    if args.operation == "lifecycle": return base
    digest = primary["receipt"]["result"]["record_digest"]
    require(args.expected_digest == digest, "feature-original-record-digest-mismatch")
    lifecycle = observe(route, context, args, "verifier", "lifecycle")
    if lifecycle is None: raise route.STEPS.PrerequisiteMissing("lifecycle")
    require(route.RUNNER.EVIDENCE.timestamp(lifecycle["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(base["required_after"]), "feature-lifecycle-order-invalid")
    base["packets"]["lifecycle"] = {"reservation": lifecycle["reservation"], "receipt": lifecycle["receipt"]}
    base["required_after"] = lifecycle["receipt"]["task"]["stopped_at"]
    if args.operation == "collision": return base
    collision = observe(route, context, args, "database-proof", "collision", digest)
    if collision is None: raise route.STEPS.PrerequisiteMissing("collision")
    require(route.RUNNER.EVIDENCE.timestamp(collision["receipt"]["task"]["created_at"]) >= route.RUNNER.EVIDENCE.timestamp(base["required_after"]), "feature-collision-order-invalid")
    base["packets"]["collision"] = {"reservation": collision["reservation"], "receipt": collision["receipt"]}
    base["required_after"] = collision["receipt"]["task"]["stopped_at"]
    if route.STEPS.stage(args) == "server-replacement": return replacement(route, context, args, base, digest)
    return base
