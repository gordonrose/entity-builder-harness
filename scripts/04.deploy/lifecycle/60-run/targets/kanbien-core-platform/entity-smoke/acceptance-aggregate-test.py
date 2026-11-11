#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.acceptance-aggregate
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual collector aggregate connections using explicitly prevalidated task/control protocols, never fake complete gate or AWS proof.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.acceptance-route
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-route-test.py
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


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("entity_smoke_aggregate_fixture_collector", Path(__file__).with_name("acceptance-route.py"))
    K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
    run(K)
