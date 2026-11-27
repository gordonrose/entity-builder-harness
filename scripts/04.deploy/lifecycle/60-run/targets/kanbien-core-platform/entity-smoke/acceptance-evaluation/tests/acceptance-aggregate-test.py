#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.acceptance-aggregate
#   version: 4
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual collector aggregate connections using explicitly prevalidated task/control protocols, never fake complete gate or AWS proof.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/tests/acceptance-route-test.py
import copy
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_AGGREGATE_ASSERTIONS_DISABLED")


def fixture(K, source_revision=None):
    """Only connection-protocol inputs, not valid standalone gate archives."""
    A = K.A
    origin = datetime(2026, 11, 9, tzinfo=timezone.utc)
    stamp = lambda seconds: (origin + timedelta(seconds=seconds)).isoformat()
    basis = K.T.RECOVERY.STATE.STOP.artifact_basis(K.C)
    declaration = str((K.C.CONTRACT.parent / "declaration-contract.yml").relative_to(K.C.ROOT))
    binding = {"source_revision": source_revision or "a" * 40, "image_digest": "sha256:" + "c" * 64,
        "configuration_contract_sha256": basis["custody_sources"][declaration], "permission_contract_sha256": "sha256:" + "e" * 64,
        "dependency_incarnation_sha256": A.digest({"resource_id": "db-CONTROLLEDORIGINAL", "database": "controlled_database", "schema": "entity_smoke"}),
        "proof_label": "entity-smoke-" + "a" * 24, "record_digest": "b" * 64}
    child = {key: item for key, item in binding.items() if key != "record_digest"}
    child.update(permission_contract_sha256="sha256:" + "f" * 64,
        dependency_incarnation_sha256=A.digest({"resource_id": "db-CONTROLLEDRESTORED", "database": "controlled_database", "schema": "entity_smoke"}))
    arn = lambda number: "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + format(number, "032x")
    definition = lambda workload: "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-" + workload + ":1"
    start = dict(zip(A.TASKS, (0, 10, 20, 30, 40, 50, 60, 70, 80, 100, 110, 120, 130, 140, 150, 160, 170, 190, 200)))
    tasks, counter = {}, 0
    for name, (stage, workload, operations) in A.TASKS.items():
        pair = {}
        for phase in (("operation",) if name == "credential-unready" else ("preflight", "operation")):
            counter += 1
            at = start[name] + (2 if phase == "operation" else 0)
            request = {"definition": definition(workload), "security_group": "sg-" + ("b" if workload == "restore-reader" else "a") * 17,
                "subnets": ["subnet-" + "c" * 17]}
            reservation = {"operation_id": "es-" + format(counter, "032x"), "request": request}
            receipt = {"task": {"arn": arn(counter), "definition": definition(workload), "created_at": stamp(at),
                "started_at": stamp(at), "stopped_at": stamp(at + 1)}, "collected_at": stamp(at + 2), "result": {"record_digest": binding["record_digest"]}}
            pair[phase] = {"name": name, "stage": stage, "phase": phase, "requested_operation": operations[0],
                "controller_sha256": basis["controller"], "packet": {"binding": child if name == "restore-read" else {key: item for key, item in binding.items() if key != "record_digest"}, "reservation": reservation, "receipt": receipt}, "admission": None}
        if "preflight" in pair:
            before = pair["preflight"]["packet"]
            pair["operation"]["admission"] = {"preflight": {"reservation": before["reservation"], "receipt": before["receipt"]}, "required_after": stamp(start[name])}
        tasks[name] = pair
    tasks["migration-state"]["operation"]["packet"]["receipt"]["result"]["code"] = "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"
    revoke = tasks["credential-revoke"]["operation"]["packet"]
    tasks["credential-unready"]["operation"]["admission"] = {"revocation": {"reservation": revoke["reservation"], "receipt": revoke["receipt"], "label": binding["proof_label"]}}
    resources = A.digest({"controlled": "restore-resources"})
    stack = "arn:aws:cloudformation:eu-west-1:337159794548:stack/kanbien-core-platform-entity-smoke-restore-" + "a" * 24 + "/controlled-stack"
    facts = {
        "server-replacement": {"original_task": arn(10000), "successor_task": arn(10001), "predecessor_stopped_at": stamp(76), "successor_started_at": stamp(78)},
        "initial-stop": {"observed_at": stamp(88), "terminal_tasks": {arn(10001): {"workload": "server", "definition": definition("server")}}},
        "initial-restart": {"server": {"task": arn(10002), "created_at": stamp(91), "started_at": stamp(92)}},
        "credential-replacement": {"original_task": arn(10002), "successor_task": arn(10003), "predecessor_stopped_at": stamp(156), "successor_started_at": stamp(158)},
        "snapshot": {"snapshot_arn": "arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + binding["proof_label"],
            "source_resource_id": "db-CONTROLLEDORIGINAL", "snapshot_created_at": stamp(178)},
        "restore-deployment": {"stack_arn": stack, "database_identifier": "kanbien-core-platform-entity-smoke-restore-" + "a" * 16,
            "resources_sha256": resources, "restored_resource_id": "db-CONTROLLEDRESTORED", "reader_definition": definition("restore-reader"), "observed_at": stamp(188)},
        "restore-cleanup": {"stack_arn": stack, "database_identifier": "kanbien-core-platform-entity-smoke-restore-" + "a" * 16,
            "resources_sha256": resources, "observed_at": stamp(198)},
    }
    reserve_times = (75, 85, 90, 155, 175, 180, 195)
    reference = "controlled-aggregate-protocol-not-qualification"
    controls = {}
    for number, (name, detail) in enumerate(facts.items()):
        controls[name] = {"operation_id": "es-" + format(1000 + number, "032x"), "source_receipt_sha256": A.digest({"controlled-value": name}),
            "source_receipt_document_sha256": A.digest({"controlled-document": name}), "facts": detail, "custody": {
                "plan": {"controller_sha256": A.digest(basis) if name in {"initial-stop", "initial-restart"} else basis["controller"], "package_custody_reference": reference},
                "reservation": {"reserved_at": stamp(reserve_times[number])}}}
    packet = lambda name: tasks[name]["operation"]["packet"]
    plan = lambda name: controls[name]["custody"]["plan"]
    plan("server-replacement")["baseline_read_sha256"] = A.digest(packet("baseline-read"))
    plan("initial-restart").update(stop_sha256=controls["initial-stop"]["source_receipt_sha256"], original_read_sha256=A.digest(packet("replacement-read")))
    plan("credential-replacement")["baseline_read_sha256"] = A.digest(packet("initial-read"))
    plan("snapshot")["history_sha256"] = A.digest({"controlled": "original-history"})
    for name in ("restore-deployment", "restore-cleanup"):
        plan(name).update(history_sha256=plan("snapshot")["history_sha256"], snapshot_sha256=controls["snapshot"]["source_receipt_document_sha256"], template_sha256=child["permission_contract_sha256"])
    plan("restore-cleanup")["reader_sha256"] = A.digest(packet("restore-read"))
    return {"schema": K.SCHEMA, "target": K.TARGET, "scope": K.SCOPE, "evidence_class": "simulated", "binding": binding,
        "controller_sha256": basis["controller"], "controller_basis": basis, "package": {"source_revision": binding["source_revision"], "image_digest": binding["image_digest"],
            "receipt_reference": reference, "program_id": "kanbien-entity-smoke", "package_contract_id": "kanbien-entity-smoke-image"}, "tasks": tasks, "controls": controls, "restored_binding": child,
        "runtime": {"task": arn(10003), "definition": definition("server"), "created_at": stamp(157), "started_at": stamp(158),
            "source_resource_id": "db-CONTROLLEDORIGINAL", "database_name": "controlled_database", "observed_at": stamp(205)}}


def run(K):
    successor_protocols(K)
    requalification_protocols(K)
    value = fixture(K)
    A, M = K.A, K.CONTROL
    assert K.T.RECOVERY.STATE.STOP.artifact(K.C) == A.digest(value["controller_basis"])
    calls = []
    def task_owner(task, *args, **kw): calls.append((task["name"], task["phase"])); return task
    def control_owner(name, *args): calls.append((name, "control"))
    # The primitive task/control owners are explicit doubles. The real collector
    # and its aggregate validator run; no retained candidate is created.
    with patch.object(A, "validate_task", side_effect=task_owner), patch.object(K, "validate_control", side_effect=control_owner):
        with patch.object(K.C, "source_digest", side_effect=AssertionError("historical source lookup")), patch.object(A.C, "source_digest", side_effect=AssertionError("historical archive lookup")), patch.object(K.C, "digest_file", side_effect=AssertionError("historical file lookup")), patch.object(A.C, "digest_file", side_effect=AssertionError("historical archive file lookup")):
            assert K.validate_packet(value, evidence_class="simulated") is value
        assert len([item for item in calls if item[1] == "control"]) == 7 and len(calls) == 44
        # A prevalidated transition may change exact task-definition revisions,
        # never private networks or an unrecognised historical actor. Primitive
        # transition validation is explicit here; its own fixture proves custody.
        transitioned = copy.deepcopy(value)
        old_binding = {key: item for key, item in value["binding"].items() if key != "record_digest"}
        old_binding.update(source_revision="1" * 40, image_digest="sha256:" + "2" * 64)
        old_resources, new_resources = {}, {}
        for name, logical in (("bootstrap", "AdministrationTaskDefinition"), ("migration", "MigrationTaskDefinition")):
            for entry in transitioned["tasks"][name].values():
                request = entry["packet"]["reservation"]["request"]
                new_resources[logical] = {"physical_id": request["definition"]}
                request["definition"] = request["definition"].removesuffix(":1") + ":7"
                old_resources[logical] = {"physical_id": request["definition"]}
                entry["packet"]["binding"] = old_binding
                entry["completion"] = {"fixture": "pinned-original"}
        transition = {"plan": {"previous_binding": old_binding, "resources": old_resources}, "resources": new_resources}
        transitioned["source_transition"] = transition
        with patch.object(A.C.TRANSITION, "validate", return_value=transition), patch.object(A.C.TRANSITION, "historical", return_value=True):
            M.validate_connections(A, transitioned)
            for field, replacement, condition in (("definition", "foreign-definition", "acceptance-transition-actor-invalid"),
                    ("security_group", "sg-" + "d" * 17, "acceptance-workload-binding-drift"),
                    ("subnets", ["subnet-" + "d" * 17], "acceptance-workload-binding-drift")):
                invalid = copy.deepcopy(transitioned)
                invalid["tasks"]["bootstrap"]["operation"]["packet"]["reservation"]["request"][field] = replacement
                try: M.validate_connections(A, invalid)
                except M.ControlFailure as failure: assert failure.code == condition
                else: raise AssertionError("transition cannot waive " + field)
            with patch.object(A.C.TRANSITION, "historical", return_value=False):
                try: M.validate_connections(A, transitioned)
                except M.ControlFailure as failure: assert failure.code == "acceptance-transition-actor-invalid"
                else: raise AssertionError("unpinned historical actor accepted")
        previous = copy.deepcopy(value)
        pinned = {}
        for phase, entry in previous["tasks"]["bootstrap"].items():
            entry["controller_sha256"] = "sha256:" + "7" * 64
            entry["completion"] = {"fixture": "original-completion-" + phase}
            pinned[A.document_digest(entry["packet"])] = A.document_digest(entry["completion"])
        with patch.object(K.T.IMAGE_REPAIR, "BOOTSTRAP_COMPLETIONS", pinned), patch.object(K.T.IMAGE_REPAIR, "BOOTSTRAP_CONTROLLER", "sha256:" + "7" * 64):
            assert K.validate_packet(previous, evidence_class="simulated") is previous
            for selection, changed in (("bootstrap", "completion"), ("migration", "controller")):
                invalid = copy.deepcopy(previous)
                if changed == "completion": invalid["tasks"][selection]["operation"]["completion"]["fixture"] = "changed"
                else: invalid["tasks"][selection]["operation"]["controller_sha256"] = "sha256:" + "7" * 64
                try: K.validate_packet(invalid, evidence_class="simulated")
                except K.CollectionFailure as failure: assert (failure.code, failure.item) == ("acceptance-task-attribution-mismatch", selection)
                else: raise AssertionError("unrecognised historical controller attribution accepted")
        def task(v, name, phase="operation"): return v["tasks"][name][phase]
        def plan(v, name): return v["controls"][name]["custody"]["plan"]
        zero = "sha256:" + "0" * 64
        cases = [
            ("preflight-before-predecessor", lambda v: task(v,"migration","preflight")["packet"]["receipt"]["task"].update(created_at="2026-11-09T00:00:00Z"), "acceptance-proof-order-invalid", "migration"),
            ("operation-before-own-probe", lambda v: task(v,"grant-runtime")["packet"]["receipt"]["task"].update(created_at="2026-11-09T00:00:20Z"), "acceptance-proof-order-invalid", "grant-runtime"),
            ("old-admission-floor", lambda v: task(v,"initial-read")["admission"].update(required_after="2026-11-09T00:00:00Z"), "acceptance-proof-order-invalid", "initial-read"),
            ("copied-job", lambda v: task(v,"final-read")["packet"]["receipt"]["task"].update(arn=task(v,"credential-read")["packet"]["receipt"]["task"]["arn"]), "acceptance-proof-attempt-reused", "final-read"),
            ("copied-control-attempt", lambda v: v["controls"]["server-replacement"].update(operation_id=task(v,"bootstrap")["packet"]["reservation"]["operation_id"]), "acceptance-proof-attempt-reused", "server-replacement"),
            ("workload-network-drift", lambda v: task(v,"final-read")["packet"]["reservation"]["request"].update(security_group="sg-"+"d"*17), "acceptance-workload-binding-drift", "final-read"),
            ("wrong-replacement-read", lambda v: plan(v,"server-replacement").update(baseline_read_sha256=zero), "acceptance-control-predecessor-mismatch", "server-replacement"),
            ("document-hash-is-not-value-hash", lambda v: plan(v,"initial-restart").update(stop_sha256=v["controls"]["initial-stop"]["source_receipt_document_sha256"]), "acceptance-control-predecessor-mismatch", "initial-restart"),
            ("different-revocation", lambda v: task(v,"credential-unready")["admission"]["revocation"].update(reservation=task(v,"permission-state")["packet"]["reservation"]), "acceptance-original-revocation-mismatch", "credential-unready"),
            ("wrong-credential-predecessor", lambda v: v["controls"]["credential-replacement"]["facts"].update(original_task=v["controls"]["server-replacement"]["facts"]["successor_task"]), "acceptance-control-predecessor-mismatch", "credential-replacement"),
            ("value-hash-is-not-document-hash", lambda v: plan(v,"restore-deployment").update(snapshot_sha256=v["controls"]["snapshot"]["source_receipt_sha256"]), "acceptance-restore-custody-mismatch", "restore-deployment"),
            ("different-history", lambda v: plan(v,"restore-cleanup").update(history_sha256=zero), "acceptance-restore-custody-mismatch", "restore-cleanup"),
            ("different-template", lambda v: plan(v,"restore-deployment").update(template_sha256=zero), "acceptance-restore-custody-mismatch", "restore-deployment"),
            ("wrong-clone-permission", lambda v: v["restored_binding"].update(permission_contract_sha256=zero), "acceptance-restore-custody-mismatch", "restore-deployment"),
            ("wrong-reader", lambda v: plan(v,"restore-cleanup").update(reader_sha256=zero), "acceptance-restore-reader-predecessor-mismatch", "restore-cleanup"),
            ("cleanup-before-reader-collection", lambda v: v["controls"]["restore-cleanup"]["custody"]["reservation"].update(reserved_at="2026-11-09T00:03:13Z"), "acceptance-proof-order-invalid", "restore-cleanup"),
            ("final-probe-before-cleanup", lambda v: task(v,"final-read","preflight")["packet"]["receipt"]["task"].update(created_at="2026-11-09T00:03:17Z"), "acceptance-proof-order-invalid", "final-read"),
            ("wrong-basis-source", lambda v: v["controller_basis"]["custody_sources"].update({"scripts/04.deploy/lifecycle/60-run/release-succession/script.py":zero}), "acceptance-control-source-attribution-mismatch", "initial-stop"),
            ("native-extra-in-basis", lambda v: v["controller_basis"].update(native="private-aggregate-canary"), "acceptance-controller-basis-invalid", None),
            ("different-qualified-package", lambda v: plan(v,"server-replacement").update(package_custody_reference="different-qualified-package"), "acceptance-control-source-attribution-mismatch", "server-replacement"),
            ("different-successor-start", lambda v: v["runtime"].update(started_at="2026-11-09T00:02:39Z"), "acceptance-current-server-time-mismatch", "runtime"),
            ("different-stopped-server-definition", lambda v: next(iter(v["controls"]["initial-stop"]["facts"]["terminal_tasks"].values())).update(definition=v["runtime"]["definition"].replace(":1",":2")), "acceptance-stopped-server-definition-mismatch", "initial-stop"),
            ("unqualified-current-definition", lambda v: v["runtime"].update(definition="private-aggregate-canary"), "acceptance-current-server-binding-invalid", "runtime"),
        ]
        for name, mutate, code, item in cases:
            invalid = copy.deepcopy(value); mutate(invalid)
            try: K.validate_packet(invalid, evidence_class="simulated")
            except M.ControlFailure as failure:
                assert (failure.code, failure.item) == (code, item), (name, failure.code, failure.item)
                observed = K.failure_details(failure)
                assert observed["condition"] == code and (item is None or observed["context"]["item"] == item)
                field = {"workload-network-drift": "security_group", "different-successor-start": "started_at", "unqualified-current-definition": "definition"}.get(name)
                if field is not None:
                    assert observed["context"]["field"] == field
                    argv = ["acceptance-route.py", "--receipt", "/tmp/controlled-not-qualified.json", "--proof-label", value["binding"]["proof_label"], "--expected-digest", value["binding"]["record_digest"], "--write-candidate"]
                    output = io.StringIO()
                    with patch.object(sys, "argv", argv), patch.object(K, "collect", side_effect=failure), redirect_stdout(output): status = K.main()
                    delivered = json.loads(output.getvalue())
                    assert status == 1 and delivered["condition"] == code and delivered["context"]["item"] == item and delivered["context"]["field"] == field
                    assert "private-aggregate" not in output.getvalue()
                assert "private-aggregate" not in json.dumps(observed)
            else: raise AssertionError("Misassembled aggregate accepted: " + name)
    print(json.dumps({"schema": "deploy/entity-smoke-aggregate-fixture/v1", "verdict": "passed", "primitive_owners": "controlled-prevalidated-protocols-not-live-proof",
        "negative_connections": len(cases), "historical_file_or_provider_queries": False, "candidate_retention": False}))


def successor_fixture(K):
    value = fixture(K)
    A = K.A
    value["schema"] = K.SUCCESSOR_SCHEMA
    value.pop("controller_basis"); value.pop("controls"); value.pop("restored_binding")
    value["package"]["receipt_reference"] = "github-actions-run:12345"
    binding = value["binding"]
    identity = {"expected_predecessor": "release-" + "a" * 24,
        "predecessor": {"release_id": "release-" + "a" * 24, "source_revision": "b" * 40,
                        "image_digest": "sha256:" + "b" * 64, "proof_set_sha256": "sha256:" + "d" * 64},
        "candidate": {key: value["package"][key] for key in ("source_revision", "image_digest", "receipt_reference")},
        "contracts": {key: binding[key] for key in ("configuration_contract_sha256", "permission_contract_sha256")},
        "dependency_incarnation_sha256": binding["dependency_incarnation_sha256"], "proof_label": binding["proof_label"]}
    delivery_id = A.digest(identity)[7:]
    value["delivery"] = {"schema": "deploy/entity-smoke-delivery-context/v1", **identity,
                         "delivery_id": delivery_id, "smoke_label": "entity-smoke-" + delivery_id[:24]}
    value["predecessor"] = {"release_id": identity["expected_predecessor"],
        "candidate_record": "release-candidates/" + identity["expected_predecessor"] + ".yml",
        "candidate_sha256": "sha256:" + "9" * 64, "applicability": {
            "schema": "deploy/entity-smoke-recovery-applicability/v1", "predecessor_source": "b" * 40,
            "candidate_source": binding["source_revision"], "input_paths": ["platform"], "inputs_sha256": "sha256:" + "8" * 64}}
    plan = {"parameters_sha256": "sha256:" + "1" * 64, "template_sha256": "sha256:" + "2" * 64}
    value["deployment"] = {"fixture": "prevalidated-deployment-not-live-evidence", "plan": plan,
        "result": {"reservation": {"reserved_at": "2026-11-09T00:00:00Z"}, "facts": {
            "completed_at": "2026-11-09T00:00:01Z",
            "resources": {"ServerTaskDefinition": {"physical_id": value["runtime"]["definition"]}}}}}
    value["tasks"] = {name: value["tasks"][name] for name in K.SUCCESSOR_TASKS}
    after, earlier = value["deployment"]["result"]["facts"]["completed_at"], {}
    for name in K.SUCCESSOR_TASKS:
        for proof in value["tasks"][name].values():
            proof["packet"]["plan"] = {**plan, "controller_sha256": value["controller_sha256"],
                                      "package_custody_reference": value["package"]["receipt_reference"]}
            proof["packet"]["prerequisites"] = copy.deepcopy({"required_after": after,
                "packets": {"deployment": value["deployment"], "predecessor": value["predecessor"], **earlier}})
        stage, workload, operations = A.TASKS[name]
        operation = value["tasks"][name]["operation"]["packet"]
        earlier[workload + "-" + operations[0]] = copy.deepcopy(operation)
        after = operation["receipt"]["task"]["stopped_at"]
    return value


def successor_protocols(K):
    """Actual successor aggregate; primitive custody readers explicitly controlled."""
    value, A = successor_fixture(K), K.A
    def reject(mutator, expected):
        invalid = copy.deepcopy(value); mutator(invalid)
        try: K.validate_packet(invalid, evidence_class="simulated")
        except K.CollectionFailure as failure:
            assert failure.code == expected, (failure.code, expected)
            assert "private-successor-canary" not in json.dumps(K.failure_details(failure))
        else: raise AssertionError("invalid successor aggregate accepted: " + expected)
    with patch.object(A, "validate_task", side_effect=lambda task, *args, **kw: task) as tasks, \
            patch.object(K.C, "validate_deployment_receipt", return_value=value["deployment"]) as deployment:
        assert K.validate_packet(value, evidence_class="simulated") is value
        assert tasks.call_count == 10 and deployment.call_count == 1
        assert all(call.kwargs["delivery"] == value["delivery"] for call in tasks.call_args_list)
        reject(lambda v: v["tasks"].pop("lifecycle"), "acceptance-proof-set-incomplete")
        reject(lambda v: v["predecessor"].update(candidate_record="../private-successor-canary"), "acceptance-predecessor-reference-invalid")
        reject(lambda v: v["predecessor"]["applicability"].update(candidate_source="0" * 40), "acceptance-recovery-applicability-invalid")
        reject(lambda v: v["tasks"]["final-read"]["operation"]["packet"]["prerequisites"].update(required_after="2026-11-09T00:00:00Z"), "acceptance-task-prerequisite-mismatch")
        reject(lambda v: v["tasks"]["final-read"]["operation"]["packet"]["plan"].update(template_sha256="sha256:" + "0" * 64), "acceptance-task-delivery-plan-mismatch")
        reject(lambda v: v["tasks"]["final-read"]["operation"]["packet"]["receipt"]["task"].update(created_at="2026-11-09T00:00:00Z"), "acceptance-successor-task-order-invalid")
        reject(lambda v: v["tasks"]["final-read"]["operation"]["admission"]["preflight"].update(reservation={"other": True}), "acceptance-original-preflight-mismatch")
        reject(lambda v: v["runtime"].update(definition="private-successor-canary"), "acceptance-current-server-mismatch")
    print(json.dumps({"schema": "deploy/entity-smoke-successor-aggregate-fixture/v1", "verdict": "passed",
        "primitive_owners": "controlled-prevalidated-protocols-not-live-proof", "fresh_task_phases": 10,
        "candidate_retention": False, "provider_observation": False}))


def requalification_protocols(K):
    """Real connection validators; underlying archive/provider protocols are doubles."""
    A = K.A
    value, first = successor_fixture(K), fixture(K)
    value.update(schema=K.REQUALIFIED_SCHEMA, controller_basis=first["controller_basis"], restored_binding=first["restored_binding"],
        controls={k: v for k, v in first["controls"].items() if k in K.REQUALIFICATION_CONTROLS},
        tasks={k: v for k, v in first["tasks"].items() if k in K.REQUALIFICATION_TASKS})
    requirement = {"schema": "deploy/recovery-requirements/v1", "mode": "requalify", "predecessor_source": "b" * 40,
        "candidate_source": value["binding"]["source_revision"], "input_paths": ["platform"],
        "predecessor_inputs_sha256": "sha256:" + "8" * 64, "candidate_inputs_sha256": "sha256:" + "9" * 64,
        "changed_bindings": ["recovery_inputs"]}
    value["predecessor"]["applicability"] = requirement
    # Read follows the migration observation, before access-failure rehearsal.
    for proof in value["tasks"]["baseline-read"].values():
        receipt = proof["packet"]["receipt"]
        for key in ("created_at", "started_at", "stopped_at"):
            receipt["task"][key] = (datetime.fromisoformat(receipt["task"][key]) + timedelta(seconds=45)).isoformat()
        receipt["collected_at"] = (datetime.fromisoformat(receipt["collected_at"]) + timedelta(seconds=45)).isoformat()
    admission = value["tasks"]["baseline-read"]["operation"]["admission"]
    admission["required_after"] = (datetime.fromisoformat(admission["required_after"]) + timedelta(seconds=45)).isoformat()
    after, earlier = value["deployment"]["result"]["facts"]["completed_at"], {}
    packet = lambda name: value["tasks"][name]["operation"]["packet"]
    for name in K.REQUALIFICATION_TASKS:
        for proof in value["tasks"][name].values():
            proof["packet"]["plan"] = {**value["deployment"]["plan"], "controller_sha256": value["controller_sha256"],
                "package_custody_reference": value["package"]["receipt_reference"]}
            proof["packet"]["prerequisites"] = copy.deepcopy({"required_after": after, "packets": {
                "deployment": value["deployment"], "predecessor": value["predecessor"], **earlier}})
        if name in K.REQUALIFICATION_TASKS[:5]:
            _, workload, operations = A.TASKS[name]
            earlier[workload + "-" + operations[0]] = copy.deepcopy(packet(name))
        after = packet(name)["receipt"]["task"]["stopped_at"]
    start = {"deployment": value["deployment"], "predecessor": value["predecessor"],
        "recovery-baseline-read": packet("baseline-read"), "recovery-applied-history": packet("migration-state"),
        "recovery-runtime": {**first["controls"]["initial-restart"]["facts"]["server"],
            "definition": value["runtime"]["definition"], "other_services": "sha256:" + "a" * 64}}
    start["recovery-runtime"].pop("started_at")
    packet("permission-state")["prerequisites"]["packets"] = copy.deepcopy(start)
    controls = value["controls"]
    for name, control in controls.items():
        control["custody"]["plan"]["package_custody_reference"] = value["package"]["receipt_reference"]
    controls["credential-replacement"]["custody"]["plan"]["baseline_read_sha256"] = A.digest(packet("baseline-read"))
    resource = K.C.RESOURCE.recovery_binding(value["binding"], value["delivery"])
    stack, _, database = K.D.RESTORE.names(resource)
    controls["snapshot"]["facts"]["snapshot_arn"] = "arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + K.C.RESOURCE.resource_label(resource)
    for name in ("restore-deployment", "restore-cleanup"):
        controls[name]["facts"].update(stack_arn="arn:aws:cloudformation:eu-west-1:337159794548:stack/" + stack + "/fixture", database_identifier=database)
    controls["restore-cleanup"]["custody"]["plan"]["reader_sha256"] = A.digest(packet("restore-read"))
    for proof in value["tasks"]["final-read"].values():
        proof["packet"]["prerequisites"] = {"required_after": controls["restore-cleanup"]["facts"]["observed_at"], "packets": {
            "credential-history-sha256": controls["snapshot"]["custody"]["plan"]["history_sha256"],
            "source-snapshot-sha256": controls["snapshot"]["source_receipt_document_sha256"],
            "restore-cleanup-sha256": controls["restore-cleanup"]["source_receipt_document_sha256"],
            "restore-reader-sha256": A.digest(packet("restore-read"))}}
    # No real proof owner is bypassed by production. These explicit test doubles
    # isolate the aggregate connections; dedicated fixtures cover owner custody.
    with patch.object(A, "validate_task", side_effect=lambda task, *a, **kw: task) as task_owner, \
         patch.object(K, "validate_control", side_effect=lambda *a: None) as control_owner, \
         patch.object(K.C, "validate_deployment_receipt", return_value=value["deployment"]), \
         patch.object(A.C, "validate_deployment_receipt", return_value=value["deployment"]):
        assert K.validate_packet(value, evidence_class="simulated") is value
        assert task_owner.call_count == 25 and control_owner.call_count == 4
        # Check the code at its actual owner; the full packet also binds copies
        # of this result in later prerequisites and rejects altered copies first.
        for code in (None, "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED"):
            invalid = copy.deepcopy(value)
            result = invalid["tasks"]["migration-state"]["operation"]["packet"]["receipt"]["result"]
            if code is None: result.pop("code")
            else: result["code"] = code
            try: K.CONTROL.validate_connections(A, invalid)
            except A.EvidenceFailure as failure:
                assert (failure.code, failure.item) == ("acceptance-migration-state-not-applied", "migration-state")
            else: raise AssertionError("unconfirmed migration result accepted")
        cases = [
            (lambda v: v.pop("controller_basis"), "acceptance-collection-envelope-invalid"),
            (lambda v: v["controller_basis"].update(controller="sha256:" + "0" * 64), "acceptance-controller-basis-invalid"),
            (lambda v: v["tasks"].pop("credential-unready"), "acceptance-proof-set-incomplete"),
            (lambda v: v["controls"].pop("restore-cleanup"), "acceptance-proof-set-incomplete"),
            (lambda v: v["predecessor"]["applicability"].update(mode="reuse"), "acceptance-recovery-applicability-invalid"),
            (lambda v: v["controls"]["snapshot"]["facts"].update(snapshot_arn="arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + v["binding"]["proof_label"]), "acceptance-isolated-restore-mismatch"),
            (lambda v: v["tasks"]["final-read"]["operation"]["packet"]["prerequisites"]["packets"].update(**{"restore-reader-sha256": "sha256:" + "0" * 64}), "acceptance-task-prerequisite-mismatch"),
            (lambda v: v["controls"]["credential-replacement"]["custody"]["reservation"].update(reserved_at="2026-11-09T00:00:00Z"), "acceptance-proof-order-invalid"),
            (lambda v: v["tasks"]["permission-state"]["operation"]["packet"]["prerequisites"]["packets"].update(deployment={}), "acceptance-control-predecessor-mismatch"),
        ]
        for mutate, condition in cases:
            invalid = copy.deepcopy(value); mutate(invalid)
            try: K.validate_packet(invalid, evidence_class="simulated")
            except (K.CollectionFailure, K.CONTROL.ControlFailure, A.EvidenceFailure) as failure: assert failure.code == condition, (failure.code, condition)
            else: raise AssertionError("requalification connection accepted " + condition)
    print(json.dumps({"schema": "deploy/entity-smoke-requalification-aggregate-fixture/v1", "verdict": "passed",
        "primitive_owners": "controlled-not-live-proof", "negative_connections": len(cases) + 2, "provider_observation": False}))


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("entity_smoke_aggregate_fixture_collector", (Path(__file__).resolve().parents[2] / "acceptance-evaluation/implementation/acceptance-route.py"))
    K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
    run(K)
