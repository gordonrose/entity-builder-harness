#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.source-transition
#   version: 2
#   status: draft
#   created_on: "2026-11-11"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the incident executor is retired and reject altered historical transition, gate and task-recovery evidence.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
from contextlib import ExitStack, redirect_stdout
import io
import json
import sys
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_SOURCE_TRANSITION_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
M = module("entity_smoke_source_transition_test", DIRECTORY / "source-transition.py")
C = module("entity_smoke_source_transition_common_test", DIRECTORY / "script.py")
before = {"source_revision": M.OLD_SOURCE, "image_digest": M.OLD_IMAGE, "proof_label": M.LABEL,
          "configuration_contract_sha256": "sha256:" + "c" * 64, "permission_contract_sha256": "sha256:" + "d" * 64,
          "dependency_incarnation_sha256": "sha256:" + "e" * 64}
after = {**before, "source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64}
resources = {name: {"type": kind, "physical_id": "owned-" + name + ":1"} for name, kind in C.DEPLOY.RESOURCE_TYPES.items()}
successors = {name: {**row, "physical_id": row["physical_id"][:-1] + "2"} if name in M.TASK_DEFINITIONS else copy.deepcopy(row) for name, row in resources.items()}
created = {"binding": before, "result": {"facts": {"resources": resources}}}
plan = {"binding": after, "previous_binding": before, "resources": resources, "desired_count": 0, "automatic_retry": False, "controller_sha256": "sha256:" + "f" * 64,
        "creation_sha256": "sha256:" + M.document(created),
        "stack_arn": "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-entity-smoke/11111111-1111-1111-1111-111111111111", "parameters": {"ServerDesiredCount": "0"}}
digest = C.DEPLOY.fingerprint(plan)
receipt = {"schema": "deploy/entity-smoke-source-transition/v1", "plan": plan, "plan_sha256": digest, "resources": successors,
           "terminal_token": "es-source-execute-" + digest[7:39], "completed_at": "2026-11-11T10:00:00Z"}
with tempfile.TemporaryDirectory(prefix="entity-smoke-transition-gate-") as gate_root:
    # Controlled historical input from the generic fixture machinery; the
    # removed incident executor must not manufacture this test's evidence.
    book = C.GateBook(plan["controller_sha256"], Path(gate_root), contract=M.graph(C))
    book.bind_plan(digest)
    for identifier in book.known: book.component(identifier)
    for identifier in C.GATE.GATE_ORDER:
        book.gate(identifier)
        if identifier == "controlled-execution": break
    gate = C.read_json(book.validate("controlled-execution"))
    gate["change_summary"] = {
        "schema": C.GATE.CHANGE_SCHEMA, "contract_id": book.identity,
        "check_id": book.contract["gates"][4]["evidence"][0], "timestamp": C.now(),
        "input_sha256": C.GATE.evidence_bindings(book.contract, book.facts)["gates"]["change-set"],
        "operation_counts": {"create": 0, "update": 1, "delete": 0, "replace": 5, "broaden-permission": 0}}
    receipt.update(graph=M.graph(C), gate=gate)


def fails(call, expected):
    try: call()
    except (C.InfrastructureFailure, C.RESOURCE.ResourceFailure) as failure:
        assert failure.code == expected, (failure.code, expected)
    else: raise AssertionError("expected source transition rejection")


assert M.validate(C, receipt, after) == receipt
for key in ("configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256", "proof_label"):
    changed = {**after, key: ("entity-smoke-" + "1" * 24) if key == "proof_label" else "sha256:" + "1" * 64}
    fails(lambda: M.compatible(C, before, changed), "source-transition-binding-incompatible")
fails(lambda: M.compatible(C, before, before), "source-transition-binding-incompatible")
for name in resources:
    broken = copy.deepcopy(receipt)
    broken["resources"][name]["physical_id"] = resources[name]["physical_id"] if name in M.TASK_DEFINITIONS else "different-resource"
    fails(lambda: M.validate(C, broken, after), "source-transition-resource-identity-invalid")
for field, value in (("terminal_token", "other-token"), ("plan_sha256", "sha256:" + "0" * 64)):
    fails(lambda: M.validate(C, {**receipt, field: value}, after), "source-transition-terminal-token-invalid" if field == "terminal_token" else "source-transition-plan-mismatch")

# The retained validator still rejects altered graphs and operation counts.
broken = copy.deepcopy(receipt); broken["graph"]["id"] += "-different"
fails(lambda: M.validate(C, broken, after), "source-transition-graph-mismatch")
broken = copy.deepcopy(receipt); broken["gate"]["change_summary"]["operation_counts"]["replace"] = 4
fails(lambda: M.validate(C, broken, after), "source-transition-change-counts-mismatch")

# Only exact pinned preparation bytes may be historical; no arbitrary receipt
# is trusted merely for carrying a former source or a valid-looking gate.
assert M.controller({}, {}, "current") == "current"
packet, completion = {"binding": before, "reservation": {"request": {"definition": "old-definition", "security_group": "old-group", "subnets": ["old-subnet"], "proof_label": "old-preflight"}}}, {"gate": "controlled-original"}
pin = M.document(packet); old_pins = M.PINS
M.PINS = {pin: (M.document(completion), "f" * 64)}
assert M.historical(packet, completion)
assert not M.historical({**packet, "unreviewed": True}, completion)
assert not M.historical(packet, {**completion, "gate": "restamped"})
route = SimpleNamespace(C=C)
context = {"binding": before, "checked": {}, "cache": Path("/not-used")}
legacy = M.legacy_context(route, context, None, packet, completion)
assert legacy["checked"]["definition"] == "old-definition" and legacy["binding"] == before
assert M.legacy_context(route, context, None, packet, {"gate": "wrong"}) is None
M.PINS = old_pins
# A controller-only correction retains the current image and exact original
# gate bytes; it must not depend on an image-transition observation.
with patch.object(M, "CONTROLLER_REPAIR_PINS", {pin: (M.document(completion), "f" * 64)}), \
     patch.object(M, "read", side_effect=AssertionError("same-image history must not read a transition")):
    assert M.controller(packet, completion, "current") == "sha256:" + "f" * 64
    assert M.legacy_context(route, context, None, packet, completion)["binding"] == before
    assert M.controller({**packet, "changed": True}, completion, "current") == "current"
    assert M.controller(packet, {**completion, "changed": True}, "current") == "current"
args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="grant-runtime", proof_stage="baseline")
label = M.replacement_label({}, args, "original")
assert label != "original" and M.replacement_label({}, args, "original") == label
assert M.replacement_label({}, SimpleNamespace(**{**vars(args), "operation": "bootstrap"}), "original") == "original"

# Controlled non-submission history: absence is never authority. Both exact
# original documents and the validated attempt-store identity are required.
probe_args = SimpleNamespace(proof_label=M.LABEL, workload="database-proof", operation="permissions", proof_stage="baseline")
probe_request = {**after, "proof_label": "original", "environment": {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "preflight", "ENTITY_SMOKE_PROOF_LABEL": "original"}}
probe_reservation = {"operation_id": M.UNSUBMITTED_PREFLIGHT, "request": probe_request}
probe_failure = {"effect": "not-started", "condition": "aws-command-failed"}
probe_context = {"cache": Path("/controlled/task-cache"), "binding": after}
probe_target = probe_context["cache"] / "task-attempts/original-database-proof-preflight.json"
probe_report = C.ROOT / M.UNSUBMITTED_REPORT
documents = {probe_target: probe_reservation, probe_report: probe_failure}
hashes = {probe_target: M.UNSUBMITTED_RESERVATION_HASH, probe_report: M.UNSUBMITTED_REPORT_HASH}
with patch.object(C, "read_json", side_effect=lambda path: documents[path]), \
     patch.object(C, "digest_file", side_effect=lambda path: hashes[path]), \
     patch.object(C.RESOURCE.CONTROL, "AttemptStore", return_value=SimpleNamespace(read=lambda key, request: probe_reservation)):
    selected = M.recovery_preflight(C, probe_context, probe_args, "original")
    assert selected != "original" and selected == M.replacement_label(None, probe_args, "original")
    for target in (probe_target, probe_report):
        original_hash = hashes[target]; hashes[target] = "sha256:" + "0" * 64
        fails(lambda: M.recovery_preflight(C, probe_context, probe_args, "original"), "task-unsubmitted-recovery-evidence-changed")
        hashes[target] = original_hash
    probe_failure["effect"] = "unknown-reconcile-only"
    fails(lambda: M.recovery_preflight(C, probe_context, probe_args, "original"), "task-unsubmitted-recovery-evidence-invalid")
    probe_failure["effect"] = "not-started"
    with patch.object(C.RESOURCE.CONTROL, "AttemptStore", return_value=SimpleNamespace(read=lambda key, request: None)):
        fails(lambda: M.recovery_preflight(C, probe_context, probe_args, "original"), "task-unsubmitted-recovery-evidence-invalid")
assert M.replacement_label(None, SimpleNamespace(**{**vars(probe_args), "proof_stage": "credential-recovery"}), "original") == "original"

# A successful but expired probe can be renewed only for the exact known
# non-submission. Exercise actual collected evidence, immutable files and store.
EF = module("entity_smoke_collision_recovery_evidence_fixture", DIRECTORY / "task-evidence-test.py")
with tempfile.TemporaryDirectory(prefix="entity-smoke-collision-renewal-") as temporary, ExitStack() as patches:
    root = Path(temporary); cache = root / "proof"
    patches.enter_context(patch.object(C, "ROOT", root))
    task, reservation, result = EF.fixture("database-proof", "preflight")
    original_label = reservation["request"]["proof_label"]
    binding = {key: reservation["request"][key] for key in ("source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")}
    binding["proof_label"] = M.LABEL
    retained = EF.collect(task, reservation, result)
    packet = {"schema": "deploy/entity-smoke-task-step/v1", "binding": binding, "plan_sha256": "sha256:" + "8" * 64, "reservation": reservation, "receipt": retained}
    target = cache / "task-steps/database-proof-collision-preflight.json"
    C.RESOURCE.write_exclusive(target, packet)
    gate = root / "controlled-gate.json"; C.RESOURCE.write_exclusive(gate, {"controlled_original_gate": True})
    completion = {"schema": "deploy/entity-smoke-task-completion/v1", "step_sha256": C.digest_file(target), "plan_sha256": packet["plan_sha256"],
                  "realization_evidence": "controlled-gate.json", "realization_evidence_sha256": C.digest_file(gate)}
    sidecar = target.with_name(target.stem + ".completion.json"); C.RESOURCE.write_exclusive(sidecar, completion)
    failure_path = root / "not-started.json"
    failure = {"effect": "not-started", "condition": "task-log-observation-incomplete", "context": {"workload": "database-proof", "operation": "collision", "phase": "operation", "proof_stage": "baseline"}}
    C.RESOURCE.write_exclusive(failure_path, failure)
    for name, value in {"COLLISION_PROBE": reservation["operation_id"], "COLLISION_PACKET": C.digest_file(target), "COLLISION_COMPLETION": C.digest_file(sidecar),
                        "COLLISION_FAILURE": "not-started.json", "COLLISION_FAILURE_HASH": C.digest_file(failure_path),
                        "CONTROLLER_REPAIR_PINS": {M.document(packet): (M.document(completion), "f" * 64)}}.items():
        patches.enter_context(patch.object(M, name, value))
    store = C.RESOURCE.CONTROL.AttemptStore(cache / "task-attempts")
    original_path = store.path_for("original", reservation["request"])
    C.RESOURCE.write_exclusive(original_path, reservation)
    selected_args = SimpleNamespace(proof_label=M.LABEL, workload="database-proof", operation="collision", proof_stage="baseline", phase="preflight")
    context = {"cache": cache, "binding": binding}
    original_bytes = {path: path.read_bytes() for path in (target, sidecar, gate, original_path, failure_path)}
    selected = M.recovery_preflight(C, context, selected_args, original_label)
    assert selected != original_label and selected == M.recovery_preflight(C, context, selected_args, original_label)
    assert M.preflight_step_suffix(selected_args) == "-readback-recovery-1"
    assert M.preflight_step_suffix(SimpleNamespace(**{**vars(selected_args), "phase": "operation"})) == ""
    assert M.preflight_step_suffix(SimpleNamespace(**{**vars(selected_args), "proof_stage": "credential-recovery"})) == ""
    for changed in (target, sidecar, failure_path):
        changed.write_bytes(b'{}\n')
        try: fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), "task-collision-recovery-evidence-changed")
        finally: changed.write_bytes(original_bytes[changed])
    gate.write_bytes(b'{}\n')
    try: fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), "task-collision-recovery-evidence-invalid")
    finally: gate.write_bytes(original_bytes[gate])
    failure_path.write_text(C.json.dumps({**failure, "effect": "unknown-reconcile-only"}))
    with patch.object(M, "COLLISION_FAILURE_HASH", C.digest_file(failure_path)):
        fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), "task-collision-recovery-evidence-invalid")
    failure_path.write_bytes(original_bytes[failure_path])
    with patch.object(C, "now", return_value=retained["task"]["stopped_at"]):
        fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), "task-collision-recovery-evidence-invalid")
    original_path.rename(original_path.with_suffix(".saved"))
    try: fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), "task-collision-recovery-reservation-required")
    finally: original_path.with_suffix(".saved").rename(original_path)
    key = "task-" + M.hashlib.sha256((M.LABEL + ":database-proof:collision:operation").encode()).hexdigest()[:48]
    operation_path = cache / "task-attempts" / (key + ".json")
    C.RESOURCE.write_exclusive(operation_path, {"existing_operation": True})
    fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), "task-collision-recovery-operation-already-reserved")
    operation_path.unlink()
    renewed_request = {**reservation["request"], "proof_label": selected, "environment": {**reservation["request"]["environment"], "ENTITY_SMOKE_PROOF_LABEL": selected}}
    renewed, fresh = store.reserve("renewed", renewed_request)
    assert fresh and M.recovery_preflight(C, context, selected_args, original_label) == selected
    assert store.read("renewed", renewed_request) == renewed
    assert all(path.read_bytes() == data for path, data in original_bytes.items())

# Completed replacement stages and final acceptance renew only unused probes.
for stage, tag, condition, prefix in (
    ("server-replacement", "REPLACEMENT", "resource-observation-not-confirmed", "task-replacement-read-recovery"),
    ("credential-recovery", "CREDENTIAL", "aws-command-failed", "task-credential-read-recovery"),
    ("acceptance", "ACCEPTANCE", "preflight-observation-not-fresh", "task-acceptance-read-recovery"),
):
    with tempfile.TemporaryDirectory(prefix="entity-smoke-replacement-renewal-") as temporary, ExitStack() as patches:
        root = Path(temporary); cache = root / "proof"
        patches.enter_context(patch.object(C, "ROOT", root))
        task, reservation, result = EF.fixture("verifier", "ready")
        request = reservation["request"]
        original_argument = request["proof_label"]
        if stage == "acceptance":
            request["proof_label"] = M.collector_label(original_argument)
            request["environment"]["ENTITY_SMOKE_PROOF_LABEL"] = request["proof_label"]
            result["proof_label_sha256"] = M.hashlib.sha256(request["proof_label"].encode()).hexdigest()
            # Prior collector-failure custody is an explicit primitive here;
            # connected restore tests and the actual archive audit own it.
            patches.enter_context(patch.object(M, "acceptance_refresh_preflight", return_value=request["proof_label"]))
        request["deadline_seconds"] = 90
        request["environment"]["ENTITY_SMOKE_EXPECTED_SOURCE"] = request["source_revision"]
        reservation["request_sha256"] = M.hashlib.sha256(EF.EVIDENCE.CONTROL.canonical(request)).hexdigest()
        task["overrides"] = EF.EVIDENCE.CONTROL.overrides(request)
        binding = {key: request[key] for key in ("source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")}
        binding["proof_label"] = M.LABEL
        packet = {"schema": "deploy/entity-smoke-task-step/v1", "binding": binding, "plan_sha256": "sha256:" + "8" * 64,
                  "reservation": reservation, "receipt": EF.collect(task, reservation, result)}
        target = cache / f"task-steps/verifier-read-{stage}{'-collector-recovery-1' if stage == 'acceptance' else ''}-preflight.json"
        C.RESOURCE.write_exclusive(target, packet)
        gate = root / "controlled-gate.json"; C.RESOURCE.write_exclusive(gate, {"controlled_original_gate": True})
        completion = {"step_sha256": C.digest_file(target), "plan_sha256": packet["plan_sha256"],
                      "realization_evidence": "controlled-gate.json", "realization_evidence_sha256": C.digest_file(gate)}
        sidecar = target.with_name(target.stem + ".completion.json"); C.RESOURCE.write_exclusive(sidecar, completion)
        failure_path = root / "not-started.json"
        failure = {"effect": "not-started", "condition": condition,
                   "context": {"workload": "verifier", "operation": "read", "phase": "operation", "proof_stage": stage}}
        C.RESOURCE.write_exclusive(failure_path, failure)
        for name, value in {tag + "_PROBE": reservation["operation_id"], tag + "_PACKET": C.digest_file(target),
                            tag + "_COMPLETION": C.digest_file(sidecar), tag + "_FAILURE": "not-started.json",
                            tag + "_FAILURE_HASH": C.digest_file(failure_path),
                            "CONTROLLER_REPAIR_PINS": {M.document(packet): (M.document(completion), "f" * 64)}}.items():
            patches.enter_context(patch.object(M, name, value))
        store = C.RESOURCE.CONTROL.AttemptStore(cache / "task-attempts")
        original_path = store.path_for("original", request); C.RESOURCE.write_exclusive(original_path, reservation)
        selected_args = SimpleNamespace(proof_label=M.LABEL, workload="verifier", operation="read", proof_stage=stage, phase="preflight")
        context = {"cache": cache, "binding": binding}; original_label = original_argument
        selected = M.recovery_preflight(C, context, selected_args, original_label)
        assert selected != original_label and selected == M.recovery_preflight(C, context, selected_args, original_label)
        assert M.readback_recovery(SimpleNamespace(**{**vars(selected_args), "proof_stage": "initial-recovery"})) is None
        for changed in (target, sidecar, failure_path, gate):
            saved = changed.read_bytes(); changed.write_bytes(b'{}\n')
            try: fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), prefix + ("-evidence-invalid" if changed == gate else "-evidence-changed"))
            finally: changed.write_bytes(saved)
        with patch.object(C, "now", return_value=packet["receipt"]["task"]["stopped_at"]):
            fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), prefix + "-evidence-invalid")
        failure_path.write_text(C.json.dumps({**failure, "effect": "unknown-reconcile-only"}))
        with patch.object(M, tag + "_FAILURE_HASH", C.digest_file(failure_path)):
            fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), prefix + "-evidence-invalid")
        failure_path.write_text(C.json.dumps(failure, sort_keys=True, separators=(",", ":")) + "\n")
        suffix = ":collector-recovery-1" if stage == "acceptance" else ""
        key = "task-" + M.hashlib.sha256((M.LABEL + ":verifier:read:operation:" + stage + suffix).encode()).hexdigest()[:48]
        if stage == "acceptance":
            steps = module("acceptance_renewal_steps", DIRECTORY / "task-steps.py")
            operation_args = SimpleNamespace(**{**vars(selected_args), "phase": "operation"})
            assert steps.key(operation_args) == key
            assert steps.path(context, selected_args).name == "verifier-read-acceptance-collector-recovery-1-readback-recovery-1-preflight.json"
            assert steps.path(context, operation_args).name == "verifier-read-acceptance-collector-recovery-1-operation.json"
        C.RESOURCE.write_exclusive(cache / "task-attempts" / (key + ".json"), {"existing_operation": True})
        fails(lambda: M.recovery_preflight(C, context, selected_args, original_label), prefix + "-operation-already-reserved")
        renewed_request = {**request, "proof_label": selected, "environment": {**request["environment"], "ENTITY_SMOKE_PROOF_LABEL": selected}}
        renewed, fresh = store.reserve("renewed", renewed_request)
        assert fresh and M.recovery_preflight(C, context, selected_args, original_label) == selected
        assert store.reserve("another-caller", renewed_request) == (renewed, False)
        assert C.read_json(target) == packet and C.read_json(sidecar) == completion

# The unused history probe renews with administration's closed environment.
with tempfile.TemporaryDirectory(prefix="entity-smoke-history-renewal-") as temporary, ExitStack() as patches:
    root = Path(temporary); cache = root / "proof"
    patches.enter_context(patch.object(C, "ROOT", root))
    task, reservation, result = EF.fixture("administration", "preflight")
    request = reservation["request"]; request["deadline_seconds"] = 90
    reservation["request_sha256"] = M.hashlib.sha256(EF.EVIDENCE.CONTROL.canonical(request)).hexdigest()
    task["overrides"] = EF.EVIDENCE.CONTROL.overrides(request)
    binding = {key: request[key] for key in ("source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")}
    binding["proof_label"] = M.LABEL
    packet = {"schema": "deploy/entity-smoke-task-step/v1", "binding": binding, "plan_sha256": "sha256:" + "8" * 64,
              "reservation": reservation, "receipt": EF.collect(task, reservation, result)}
    target = cache / "task-steps/administration-observe-migration-state-initial-recovery-preflight.json"
    C.RESOURCE.write_exclusive(target, packet)
    gate = root / "controlled-gate.json"; C.RESOURCE.write_exclusive(gate, {"controlled_original_gate": True})
    completion = {"step_sha256": C.digest_file(target), "plan_sha256": packet["plan_sha256"],
                  "realization_evidence": "controlled-gate.json", "realization_evidence_sha256": C.digest_file(gate)}
    sidecar = target.with_name(target.stem + ".completion.json"); C.RESOURCE.write_exclusive(sidecar, completion)
    failure_path = root / "not-started.json"
    failure = {"effect": "not-started", "condition": "preflight-observation-not-fresh",
               "context": {"workload": "administration", "operation": "observe-migration-state", "phase": "operation", "proof_stage": "initial-recovery"}}
    C.RESOURCE.write_exclusive(failure_path, failure)
    for name, value in {"HISTORY_PROBE": reservation["operation_id"], "HISTORY_PACKET": C.digest_file(target),
                        "HISTORY_COMPLETION": C.digest_file(sidecar), "HISTORY_FAILURE": "not-started.json",
                        "HISTORY_FAILURE_HASH": C.digest_file(failure_path),
                        "CONTROLLER_REPAIR_PINS": {M.document(packet): (M.document(completion), "f" * 64)}}.items():
        patches.enter_context(patch.object(M, name, value))
    store = C.RESOURCE.CONTROL.AttemptStore(cache / "task-attempts")
    C.RESOURCE.write_exclusive(store.path_for("original", request), reservation)
    args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="observe-migration-state", proof_stage="initial-recovery", phase="preflight")
    context = {"cache": cache, "binding": binding}; original_label = request["proof_label"]
    selected = M.recovery_preflight(C, context, args, original_label)
    assert selected != original_label and selected == M.recovery_preflight(C, context, args, original_label)
    assert M.preflight_step_suffix(args) == "-readback-recovery-1"
    assert M.readback_recovery(SimpleNamespace(**{**vars(args), "operation": "revoke-runtime"})) is None
    for changed in (target, sidecar, failure_path, gate):
        saved = changed.read_bytes(); changed.write_bytes(b'{}\n')
        try: fails(lambda: M.recovery_preflight(C, context, args, original_label), "task-history-read-recovery-evidence-invalid" if changed == gate else "task-history-read-recovery-evidence-changed")
        finally: changed.write_bytes(saved)
    with patch.object(C, "now", return_value=packet["receipt"]["task"]["stopped_at"]):
        fails(lambda: M.recovery_preflight(C, context, args, original_label), "task-history-read-recovery-evidence-invalid")
    for change in ({"effect": "unknown-reconcile-only"}, {"context": {**failure["context"], "operation": "revoke-runtime"}}):
        failure_path.write_text(C.json.dumps({**failure, **change}))
        with patch.object(M, "HISTORY_FAILURE_HASH", C.digest_file(failure_path)):
            fails(lambda: M.recovery_preflight(C, context, args, original_label), "task-history-read-recovery-evidence-invalid")
    failure_path.write_text(C.json.dumps(failure, sort_keys=True, separators=(",", ":")) + "\n")
    key = "task-" + M.hashlib.sha256((M.LABEL + ":administration:observe-migration-state:operation:initial-recovery").encode()).hexdigest()[:48]
    C.RESOURCE.write_exclusive(cache / "task-attempts" / (key + ".json"), {"existing_operation": True})
    fails(lambda: M.recovery_preflight(C, context, args, original_label), "task-history-read-recovery-operation-already-reserved")
    renewed_request = {**request, "proof_label": selected}
    renewed, fresh = store.reserve("renewed", renewed_request)
    assert fresh and renewed_request["environment"] == {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}
    assert M.recovery_preflight(C, context, args, original_label) == selected
    assert store.reserve("another-caller", renewed_request) == (renewed, False), "same renewed identity never launches again"
    assert C.read_json(target) == packet and C.read_json(sidecar) == completion


# Keep actual file-backed historical read coverage after removing its producer.
with tempfile.TemporaryDirectory(prefix="entity-smoke-transition-reader-") as temporary:
    cache = Path(temporary)
    C.RESOURCE.write_exclusive(cache / "receipts/create.json", created)
    retained = copy.deepcopy(receipt)
    assert retained["plan"]["creation_sha256"] == C.digest_file(cache / "receipts/create.json")
    C.RESOURCE.write_exclusive(cache / "source-transition/receipt.json", retained)
    expected = {}
    for name in M.RECOVERY:
        path = cache / name
        C.RESOURCE.write_exclusive(path, {"historical": name})
        expected[name] = C.digest_file(path).removeprefix("sha256:")
    with patch.object(M, "RECOVERY", expected):
        assert M.read(C, cache, after) == retained
        target = cache / next(iter(expected))
        saved = target.read_bytes(); target.write_text("{}")
        fails(lambda: M.read(C, cache, after), "source-transition-recovery-changed")
        target.write_bytes(saved)
        (cache / "receipts/create.json").write_text("{}")
        fails(lambda: M.read(C, cache, after), "source-transition-creation-changed")

# Actual former CLI refuses every mode without loading a provider or creating
# new proof. Hostile argument strings never appear in its finite report.
for argv in ([], ["--mode", "plan"], ["--mode", "review"], ["--mode", "execute"],
             ["--mode", "reconcile"], ["--receipt", "private-path-canary", "--unknown"]):
    output = io.StringIO()
    with patch.object(sys, "argv", [str(Path(M.__file__)), *argv]), \
         patch.object(importlib.util, "spec_from_file_location", side_effect=AssertionError("provider module loaded")) as loader, \
         patch.object(C.RESOURCE, "write_exclusive", side_effect=AssertionError("evidence write")) as write, \
         redirect_stdout(output):
        assert M.main() == 1
        loader.assert_not_called(); write.assert_not_called()
    assert json.loads(output.getvalue()) == {
        "verdict": "blocked", "condition": "source-transition-executor-retired", "effect": "not-started"}
    assert "private-path-canary" not in output.getvalue()
for removed in ("inventory", "retain", "gates", "change", "run", "RECOVERY_PROGRAMS"):
    assert not hasattr(M, removed), removed

print("ENTITY_SMOKE_SOURCE_TRANSITION_HISTORICAL_READERS_AND_RETIREMENT_PASSED")
