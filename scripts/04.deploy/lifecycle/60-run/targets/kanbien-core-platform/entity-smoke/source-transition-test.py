#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.source-transition
#   version: 1
#   status: draft
#   created_on: "2026-11-11"
#   updated_on: "2026-11-12"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject unreviewed image transitions, changed historical evidence and mutation replay using controlled provider fixtures, not live proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
from contextlib import ExitStack
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
plan = {"binding": after, "previous_binding": before, "resources": resources, "desired_count": 0, "automatic_retry": False, "controller_sha256": "sha256:" + "f" * 64,
        "stack_arn": "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-entity-smoke/11111111-1111-1111-1111-111111111111", "parameters": {"ServerDesiredCount": "0"}}
digest = C.DEPLOY.fingerprint(plan)
receipt = {"schema": "deploy/entity-smoke-source-transition/v1", "plan": plan, "plan_sha256": digest, "resources": successors,
           "terminal_token": "es-source-execute-" + digest[7:39], "completed_at": "2026-11-11T10:00:00Z"}
with tempfile.TemporaryDirectory(prefix="entity-smoke-transition-gate-") as gate_root:
    gate_path = M.gates(C, Path(gate_root), plan, "controlled-execution")
    receipt.update(graph=M.graph(C), gate=C.read_json(gate_path))


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

class Provider:
    def __init__(self):
        self.value = {"StackId": plan["stack_arn"], "ChangeSetId": "owned-change", "ChangeSetName": "entity-smoke-source-" + digest[7:31],
                      "Description": "es-source-review-" + digest[7:39], "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "Capabilities": ["CAPABILITY_IAM"],
                      "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in plan["parameters"].items()], "Changes": []}
        for name in sorted(M.TASK_DEFINITIONS | {"FeatureService"}):
            self.value["Changes"].append({"ResourceChange": {"LogicalResourceId": name, "PhysicalResourceId": resources[name]["physical_id"], "ResourceType": resources[name]["type"],
                "Action": "Modify", "Replacement": "True" if name in M.TASK_DEFINITIONS else "False", "Scope": ["Properties"],
                "Details": [{"Target": {"Attribute": "Properties", "Name": "ContainerDefinitions" if name in M.TASK_DEFINITIONS else "TaskDefinition"}}]}})
        self.calls = []
    def __call__(self, service, operation, **parameters):
        self.calls.append((service, operation, parameters))
        if operation == "describe-change-set": return copy.deepcopy(self.value)
        assert operation == "get-template"
        return {"TemplateBody": C.DEPLOY.source()[0]}

provider = Provider()
assert M.change(C, provider, plan) == "owned-change"
assert all(operation in {"describe-change-set", "get-template"} for _, operation, _ in provider.calls)
for field, value in (("Action", "Remove"), ("LogicalResourceId", "MigrationTaskRole"), ("PhysicalResourceId", "not-owned"), ("Replacement", "Conditional")):
    altered = Provider(); altered.value["Changes"][0]["ResourceChange"][field] = value
    fails(lambda: M.change(C, altered, plan), "source-transition-change-shape-invalid")
altered = Provider(); altered.value["Changes"][0]["ResourceChange"]["Details"][0]["Target"]["Name"] = "TaskRoleArn"
fails(lambda: M.change(C, altered, plan), "source-transition-change-property-invalid")
altered = Provider(); altered.value["Parameters"][0]["ParameterValue"] = "1"
fails(lambda: M.change(C, altered, plan), "deployment-provider-parameters-mismatch")
altered = Provider(); altered.value["Status"] = "CREATE_IN_PROGRESS"
assert M.change(C, altered, plan) is None

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

# Both completed replacement stages renew only their unused ready probe.
for stage, tag, condition, prefix in (
    ("server-replacement", "REPLACEMENT", "resource-observation-not-confirmed", "task-replacement-read-recovery"),
    ("credential-recovery", "CREDENTIAL", "aws-command-failed", "task-credential-read-recovery"),
):
    with tempfile.TemporaryDirectory(prefix="entity-smoke-replacement-renewal-") as temporary, ExitStack() as patches:
        root = Path(temporary); cache = root / "proof"
        patches.enter_context(patch.object(C, "ROOT", root))
        task, reservation, result = EF.fixture("verifier", "ready")
        request = reservation["request"]
        request["deadline_seconds"] = 90
        request["environment"]["ENTITY_SMOKE_EXPECTED_SOURCE"] = request["source_revision"]
        reservation["request_sha256"] = M.hashlib.sha256(EF.EVIDENCE.CONTROL.canonical(request)).hexdigest()
        task["overrides"] = EF.EVIDENCE.CONTROL.overrides(request)
        binding = {key: request[key] for key in ("source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")}
        binding["proof_label"] = M.LABEL
        packet = {"schema": "deploy/entity-smoke-task-step/v1", "binding": binding, "plan_sha256": "sha256:" + "8" * 64,
                  "reservation": reservation, "receipt": EF.collect(task, reservation, result)}
        target = cache / f"task-steps/verifier-read-{stage}-preflight.json"
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
        context = {"cache": cache, "binding": binding}; original_label = request["proof_label"]
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
        key = "task-" + M.hashlib.sha256((M.LABEL + ":verifier:read:operation:" + stage).encode()).hexdigest()[:48]
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

# Run the complete public coordinator with retained single-submission intent.
# Source/identity/alignment are controlled prerequisites; real file retention,
# change review and generic gate validation remain exercised.
class ExecutionProvider(Provider):
    def __init__(self):
        super().__init__()
        self.effect = "not-started"
        self.stack_status, self.updated, self.token = "CREATE_COMPLETE", False, None
        self.submissions = []
        self.lose_review, self.lose_execution = True, True
    def _invoke(self, service, operation, parameters):
        self.submissions.append(operation)
        if operation == "create-change-set":
            self.value.update(ChangeSetName=parameters["ChangeSetName"], Description=parameters["Description"], Parameters=parameters["Parameters"])
            if self.lose_review: raise OSError("sensitive-response-canary")
        elif operation == "execute-change-set":
            self.updated = True; self.stack_status = "UPDATE_COMPLETE"; self.token = parameters["ClientRequestToken"]
            if self.lose_execution: raise OSError("sensitive-response-canary")
        else: raise AssertionError(operation)
        return {}
    def __call__(self, service, operation, **parameters):
        if operation == "validate-template": return {"Parameters": [{"ParameterKey": name} for name in C.DEPLOY.PARAMETERS], "Capabilities": ["CAPABILITY_IAM"]}
        if operation == "describe-stacks": return {"Stacks": [{"StackId": plan["stack_arn"], "StackStatus": self.stack_status}]}
        if operation == "describe-stack-events": return {"StackEvents": [{"PhysicalResourceId": plan["stack_arn"], "ClientRequestToken": self.token, "ResourceStatus": self.stack_status}]}
        return super().__call__(service, operation, **parameters)

with tempfile.TemporaryDirectory(prefix="entity-smoke-source-transition-") as temporary, ExitStack() as patches:
    root = Path(temporary)
    cache = root / ".cache/entity-smoke-live" / M.LABEL
    created = {"binding": before, "result": {"facts": {"resources": resources, "stack_arn": plan["stack_arn"]}}}
    C.RESOURCE.write_exclusive(cache / "receipts/create.json", created)
    custody = {"source_revision": after["source_revision"], "image_digest": after["image_digest"], "receipt_reference": "fixture:qualified-image"}
    source_files = {name: (C.ROOT / "infra/04.deploy/03.product/entrypoints/entity-smoke" / name).read_text() for name in ("administration.ts", "preflight.ts")}
    actual_digest = C.digest_file
    actual_module, readbacks = C.module, []
    def selected_module(name, path):
        if path.name == "task-binding.py":
            return SimpleNamespace(inspect=lambda provider, workload, parameters, selected, source: readbacks.append((workload, copy.deepcopy(selected))))
        return actual_module(name, path)
    def digest_file(path):
        relative = str(path.relative_to(cache)) if path.is_relative_to(cache) else None
        program = str(path.relative_to(root)) if path.is_relative_to(root) else None
        if program in M.RECOVERY_PROGRAMS: return "sha256:" + M.RECOVERY_PROGRAMS[program]
        return "sha256:" + M.RECOVERY[relative] if relative in M.RECOVERY else actual_digest(path)
    def command(arguments):
        if arguments[:2] == ["git", "diff"]: return "\n".join("infra/04.deploy/03.product/entrypoints/entity-smoke/" + name for name in source_files)
        assert arguments[:2] == ["git", "show"]
        return source_files[arguments[2].rsplit("/", 1)[1]]
    def inventory(common, provider, binding, parameters):
        assert binding == (after if provider.updated else before)
        return {"StackId": plan["stack_arn"], "StackStatus": provider.stack_status}, copy.deepcopy(successors if provider.updated else resources)
    for owner, name, value in ((C, "ROOT", root), (C, "local_checks", lambda: None), (C, "source_digest", lambda: "sha256:" + "f" * 64),
            (C, "operator_preflight", lambda provider: "sha256:" + "1" * 64), (C, "binding_for", lambda receipt, alignment: {key: value for key, value in after.items() if key != "proof_label"}),
            (C, "digest_file", digest_file), (C, "module", selected_module), (C.ALIGN, "read_receipt", lambda path: custody), (C.ALIGN, "source_preflight", lambda receipt: None),
            (C.ALIGN, "inspect", lambda *args: ({}, {"ServerDesiredCount": "0"}, None)), (C.ALIGN, "command", command), (M, "inventory", inventory)):
        patches.enter_context(patch.object(owner, name, value))
    provider = ExecutionProvider()
    args = SimpleNamespace(receipt=root / "custody.json", mode="plan", approved_plan=None)
    planned = M.run(C, args, provider)
    assert not provider.submissions and planned["verdict"] == "planned"
    args.mode = "review"; args.approved_plan = "sha256:" + "0" * 64
    fails(lambda: M.run(C, args, provider), "source-transition-approved-plan-mismatch")
    args.approved_plan = planned["plan_sha256"]
    try: M.run(C, args, provider)
    except OSError: pass
    else: raise AssertionError("expected lost review response")
    assert M.run(C, args, provider)["verdict"] == "reviewed" and provider.submissions == ["create-change-set"]
    args.mode = "execute"
    try: M.run(C, args, provider)
    except OSError: pass
    else: raise AssertionError("expected lost execution response")
    args.mode = "reconcile"
    assert M.run(C, args, provider)["verdict"] == "completed"
    assert M.run(C, args, provider)["verdict"] == "completed"
    assert provider.submissions == ["create-change-set", "execute-change-set"]
    assert len(readbacks) == 10 and {workload for workload, _ in readbacks} == {"server", "migration", "administration", "verifier", "database-proof"}
    assert all(selected == successors for _, selected in readbacks)
    assert M.read(C, cache, after)["resources"] == successors
print("ENTITY_SMOKE_SOURCE_TRANSITION_CONTROLS_PASSED")
