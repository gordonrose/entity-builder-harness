#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.credential-steps
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind deliberate credential revocation and expected denial to actual preserved-record, restoration, replacement and fresh positive proof without replay or privilege repair.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
from types import SimpleNamespace

STEPS = (("permission-state", "administration", "observe-permissions"), ("revoke", "administration", "revoke-runtime"),
         ("unready", "verifier", "unready"), ("restore", "administration", "restore-runtime"),
         ("read", "verifier", "read"), ("permissions", "database-proof", "permissions"))


class CredentialFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(allowed, code):
    if not allowed: raise CredentialFailure(code)


def selected(args):
    if getattr(args, "proof_stage", "baseline") != "credential-recovery": return None
    return next((i for i, (_, workload, operation) in enumerate(STEPS) if (args.workload, args.operation) == (workload, operation)), None)


def supported(args): return selected(args) is not None


def negative(args): return supported(args) and (args.workload, args.operation) == ("verifier", "unready")


def arguments(args, workload, operation, stage="credential-recovery"):
    return SimpleNamespace(**{**vars(args), "workload": workload, "operation": operation, "phase": "operation", "proof_stage": stage})


def observe(route, context, args, provider, workload, operation, stage="credential-recovery"):
    selected_args = arguments(args, workload, operation, stage)
    checked = route.BINDING.inspect(provider, workload, context["parameters"], context["resources"], context.get("binding_snapshot"))
    value = route.STEPS.observe_packet(route, {**context, "checked": checked}, selected_args, provider)
    if value is None: raise route.STEPS.PrerequisiteMissing(stage + "-" + operation)
    return value


def ordered(route, packet, after):
    timestamp = route.RUNNER.EVIDENCE.timestamp
    require(timestamp(packet["receipt"]["task"]["created_at"]) >= timestamp(after), "credential-step-order-invalid")
    return packet["receipt"]["task"]["stopped_at"]


def initial(route, context, args, provider):
    initial = route.RECOVERY.restart(route, context, args, provider, require_current=False)
    after, packets = initial["required_after"], initial["packets"]
    read = observe(route, context, args, provider, "verifier", "read", "initial-recovery")
    after = ordered(route, read, after)
    require(read["receipt"]["result"].get("record_digest") == args.expected_digest, "credential-original-digest-mismatch")
    history = observe(route, context, args, provider, "administration", "observe-migration-state", "initial-recovery")
    after = ordered(route, history, after)
    require(history["receipt"]["result"].get("code") == "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED", "credential-applied-history-required")
    packets.update({"initial-recovery-original-read": read, "initial-recovery-applied-history": history})
    return {**initial, "required_after": after, "packets": packets}


def prefix(route, context, args, provider, limit):
    base = initial(route, context, args, provider)
    after, packets, revocation = base["required_after"], base["packets"], None
    for name, workload, operation in STEPS[:limit]:
        packet = observe(route, context, args, provider, workload, operation)
        after = ordered(route, packet, after)
        packets["credential-" + name] = packet
        if name == "revoke": revocation = {"reservation": packet["reservation"], "receipt": packet["receipt"], "label": args.proof_label}
        if name == "unready":
            try: route.RUNNER.UNREADY.read_admission(context["cache"] / "task-receipts", packet["reservation"], revocation)
            except route.RUNNER.UNREADY.UnreadyFailure as failure: raise CredentialFailure(failure.code) from None
    return {"base": base, "required_after": after, "packets": packets, "revocation": revocation}


def original_server(route, context, base, provider):
    C = route.C
    original = base["restart"]["server"]["task"]
    definition = base["restart"]["packet"]["request"]["definition"]
    server = C.RESOURCE.task(provider, original, definition, context["binding"]["image_digest"])
    service = C.RESOURCE.service(provider, definition, 1)
    require(server.get("lastStatus") == "RUNNING" and server.get("healthStatus") == "HEALTHY" and service.get("runningCount") == 1 and service.get("pendingCount") == 0
            and C.RESOURCE.running_service_tasks(provider) == [original], "credential-original-runtime-not-confirmed")
    return original


def public_prefix(value):
    return {key: value[key] for key in ("required_after", "packets", "revocation")}


def replacement(route, context, args, provider, prior):
    C = route.C
    path = context["cache"] / "credential-replacement-receipt.json"
    route.RUNNER.CONTROL.no_symlinks(path)
    if not path.is_file(): raise route.STEPS.PrerequisiteMissing("credential-replacement")
    value = C.read_json(path)
    require(isinstance(value, dict) and set(value) == {"schema", "packet", "result", "realization_evidence", "realization_evidence_sha256"}
            and value["schema"] == "deploy/entity-smoke-replacement-receipt/v1", "credential-replacement-receipt-invalid")
    packet = value["packet"]
    require(isinstance(packet, dict) and set(packet) == {"schema", "plan", "request", "plan_sha256"} and packet["schema"] == "deploy/entity-smoke-replacement-plan-packet/v1"
            and isinstance(packet["plan"], dict) and packet["plan_sha256"] == C.DEPLOY.fingerprint(packet["plan"]), "credential-replacement-plan-invalid")
    request, plan = packet["request"], packet["plan"]
    C.RESOURCE.validate_request("credential-replacement", request)
    server = route.BINDING.inspect(provider, "server", context["parameters"], context["resources"], context.get("binding_snapshot"))
    require(request["binding"] == {**context["binding"], "record_digest": args.expected_digest} and request["definition"] == server["definition"]
            and request["original_task"] == prior["base"]["restart"]["server"]["task"] and plan.get("proof_stage") == "credential-recovery"
            and plan.get("binding") == request["binding"] and plan.get("request_sha256") == C.DEPLOY.fingerprint(request)
            and plan.get("controller_sha256") == context["artifact"] and plan.get("graph_sha256") == C.DEPLOY.fingerprint(route.GRAPH.replacement(C.GATE, C.CONTRACT, "credential-recovery"))
            and plan.get("baseline_read_sha256") == C.DEPLOY.fingerprint(prior["packets"]["initial-recovery-original-read"])
            and plan.get("prerequisites_sha256") == C.DEPLOY.fingerprint(public_prefix(prior))
            and plan.get("configuration_sha256") == C.DEPLOY.fingerprint({"parameters": context["parameters"], "resources": context["resources"], "server": server}), "credential-replacement-binding-mismatch")
    for name in ("credential-replacement-plan.json", "credential-replacement-plans/" + packet["plan_sha256"].removeprefix("sha256:") + ".json"):
        require(C.read_json(context["cache"] / name) == packet, "credential-replacement-plan-not-retained")
    store = C.RESOURCE.ResourceStore(context["cache"] / "attempts")
    reservation = store.read("credential-replacement", request)
    require(reservation is not None, "credential-replacement-journal-required")
    require(C.RESOURCE.timestamp(reservation["reserved_at"]) >= C.RESOURCE.timestamp(prior["required_after"]), "credential-replacement-predates-restore")
    actual = C.RESOURCE.replace_runtime(provider, store, request["binding"], request["definition"], request["original_task"], credential_recovery=True)
    require(actual.get("status") == "completed" and actual == value["result"], "credential-replacement-not-confirmed")
    reference = value["realization_evidence"]
    root = str((context["cache"] / "credential-replacement-realization").relative_to(C.ROOT)) + "/controlled-execution-"
    require(isinstance(reference, str) and reference.startswith(root) and route.re.fullmatch(r"[a-f0-9]{32}\.json", reference[len(root):])
            and C.digest_file(C.ROOT / reference) == value["realization_evidence_sha256"], "credential-replacement-gate-changed")
    evidence = C.read_json(C.ROOT / reference)
    require(isinstance(evidence, dict) and evidence.get("plan_sha256") == packet["plan_sha256"] and isinstance(evidence.get("facts"), dict)
            and [row.get("gate") for row in evidence["facts"].get("gate_evidence", [])] == list(C.GATE.GATE_ORDER[:7]), "credential-replacement-gate-invalid")
    return value


def prerequisites(route, context, args, provider):
    index = selected(args)
    require(index is not None, "credential-operation-not-supported")
    value = prefix(route, context, args, provider, min(index, 4))
    route.RECOVERY.require_active(route, context, args, provider, value["base"]["state"])
    if index < 4: original_server(route, context, value["base"], provider)
    else:
        replaced = replacement(route, context, args, provider, value)
        value["packets"]["credential-replacement"] = replaced
        value["required_after"] = replaced["result"]["facts"]["successor_started_at"]
        if index == 5:
            read = observe(route, context, args, provider, "verifier", "read")
            value["required_after"] = ordered(route, read, value["required_after"])
            require(read["receipt"]["result"].get("record_digest") == args.expected_digest, "credential-original-digest-mismatch")
            value["packets"]["credential-read"] = read
    return public_prefix(value)


def replacement_context(route, args, provider):
    C = route.C
    custody = C.ALIGN.read_receipt(args.receipt.absolute())
    C.ALIGN.source_preflight(custody); C.local_checks()
    state = route.RECOVERY.STATE.context(route, args, provider, custody)
    context = {**state["task_context"], "custody": custody, "artifact": C.source_digest(), "provider": provider,
               "callees": {"server": state["server"]}}
    value = prefix(route, context, args, provider, 4)
    require(not any(row["workload"] != "server" for row in state["scope"]["active_tasks"].values()), "credential-replacement-active-job-not-permitted")
    context["prerequisites"] = public_prefix(value)
    context["credential_original_task"] = value["base"]["restart"]["server"]["task"]
    return context, value["packets"]["initial-recovery-original-read"]
