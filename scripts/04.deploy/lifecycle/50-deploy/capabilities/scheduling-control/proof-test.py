#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.scheduling-runtime-proof
#   version: 2
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.scheduling
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove scheduler cost arithmetic rejects incomplete measurements and preserves explicit paid fixed costs and unknown extras.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.capability.scheduling-control
#     path: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
import copy
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile

spec = importlib.util.spec_from_file_location("scheduler_runtime_proof", Path(__file__).with_name("proof.py"))
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)


def inputs():
    samples = []
    for scope in ("one", "two"):
        for kind in ("idle-dispatch", "due-dispatch", "worker"):
            ordinal = len(samples)
            samples.append({"scope": scope, "kind": kind,
                "version_arn": "arn:aws:lambda:eu-west-1:123456789012:function:" + scope + ("-worker" if kind == "worker" else "-dispatch") + ":1",
                "request_id": "00000000-0000-4000-8000-" + str(ordinal).zfill(12),
                "billed_duration_ms": 1000, "memory_mb": 512, "evidence_sha256": "a" * 64})
    return {"region": "eu-west-1", "samples": samples, "image_bytes": 4 * 1024**3,
            "priced_extras": {name: {"usd": "0.10", "evidence_sha256": "b" * 64}
                             for name in ("database_cpu", "database_storage_and_backup", "recovery_snapshots", "notifications", "data_transfer")}}


def runtime_fixture(purpose="worker"):
    request = "ee860df1-9d61-45f3-b3ee-e64da98115da"
    expected = {"purpose": purpose, "source_revision": "a" * 40,
        "version_arn": "arn:aws:lambda:eu-west-1:123456789012:function:one-" + purpose + ":2",
        "image_uri": "123456789012.dkr.ecr.eu-west-1.amazonaws.com/one@sha256:" + "b" * 64,
        "log_group": "/aws/lambda/one/scheduling"}
    observed_at = "2026-11-26T12:00:01.000Z"
    body = {"schema": "kanbien/scheduling-runtime-observation/v1", "purpose": purpose,
        "source_revision": expected["source_revision"], "function_arn": expected["version_arn"],
        "request_id": request, "observed_at": observed_at,
        **({"kind": "delivery-completed", "outbox_sha256": "c" * 64, "attempt": 1, "idempotency": "durable-processed"}
           if purpose == "worker" else {"kind": "dispatch-completed", "trigger": None, "result": {
               "delivery": {"inspected": 1, "deliveryCreated": 1, "deliveryAlreadyCreated": 0, "notDue": 0},
               "relayAttempts": 2, "published": 1, "stopReason": "idle"}})}
    messages = [
        {"type": "platform.start", "record": {"requestId": request, "version": "2"}},
        {"level": "info", "message": "Scheduling runtime observation.", "fields": {"scheduling_runtime": body}},
        {"type": "platform.report", "record": {"requestId": request, "status": "success", "metrics": {
            "billedDurationMs": 1250, "memorySizeMB": 512}}},
    ]
    beginning = "2026-11-26T12:00:00.000Z"
    stamp = int(datetime.fromisoformat(beginning.replace("Z", "+00:00")).timestamp() * 1000)
    events = [{"eventId": "event-" + str(index), "logStreamName": "2026/11/26/one-" + purpose + "[2][controlled-environment]",
               "timestamp": stamp + index * 1000, "message": json.dumps(message)} for index, message in enumerate(messages)]
    return expected, events, {"started_at": beginning, "ended_at": "2026-11-26T12:01:00.000Z"}


def delivery_fixture(scope="core-server-persistence"):
    schedule_id = "10000000-0000-4000-8000-000000000001"
    subject_id = "10000000-0000-4000-8000-000000000002"
    outbox_id = "10000000-0000-4000-8000-000000000003"
    due = "2026-11-26T12:05:00.001Z" if scope == "entity-smoke" else "2026-11-26T12:05:00.000Z"
    job = owner.proof_semantics().PROOF_JOBS[scope]
    selection = {"kind": "schedule", "id": schedule_id} if scope == "core-server-persistence" else {"kind": "subject", "id": subject_id, "due_at": due}
    schedule = {"id": schedule_id, "state": "waiting", "job_name": job, "due_at": due}
    if scope == "entity-smoke": schedule["subject"] = {"kind": "entity-smoke.test-entity", "id": subject_id}
    before = {"schema": "kanbien/scheduling-proof-observation/v1", "selection": selection,
        "observed_at": "2026-11-26T12:00:01.000Z", "schedule": schedule, "outbox": None, "processing": None, "delivery_message": None,
        "application": {"kind": "acceptance", "present": False} if scope == "core-server-persistence" else {
            "kind": "entity", "present": True, "visibility": "archived", "lifecycle_state": "deleted",
            "deleted_at": "2026-11-26T12:00:00.000Z", "restore_eligible_until": "2026-11-26T12:01:00.000Z"}}
    after = copy.deepcopy(before)
    after.update(observed_at="2026-11-26T12:06:00.000Z", schedule={**schedule, "state": "delivery-created", "outbox_entry_id": outbox_id},
        outbox={"id": outbox_id, "state": "published", "attempt": 1, "created_at": "2026-11-26T12:05:01.000Z", "published_at": "2026-11-26T12:05:03.000Z"},
        processing={"outbox_entry_id": outbox_id, "state": "completed", "attempt": 1,
            "completion": {"outcome": "succeeded", "completed_at": "2026-11-26T12:05:02.000Z"}},
        application={"kind": "acceptance", "present": True, "fact_digest": "d" * 64} if scope == "core-server-persistence" else {"kind": "entity", "present": False})
    after["delivery_message"] = {"id": outbox_id, "idempotencyKey": outbox_id, "type": job, "version": 1,
        "enqueuedAt": after["observed_at"], "payload": {"outboxEntryId": outbox_id}}
    _, worker_events, window = runtime_fixture()
    worker = json.loads(worker_events[1]["message"])["fields"]["scheduling_runtime"]
    worker.update(observed_at="2026-11-26T12:05:02.000Z", outbox_sha256=owner.hashlib.sha256(outbox_id.encode()).hexdigest())
    _, dispatch_events, _ = runtime_fixture("dispatch")
    dispatch = json.loads(dispatch_events[1]["message"])["fields"]["scheduling_runtime"]
    dispatch.update(observed_at="2026-11-26T12:05:01.500Z", trigger={"schedule_arn": "arn:aws:scheduler:eu-west-1:123456789012:schedule/one/due-pass",
        "scheduled_at": due, "execution_sha256": "e" * 64, "attempt": 1})
    return {"scope": scope, "before": before, "after": after, "dispatches": [{"observation": dispatch}], "workers": [{"observation": worker}]}


def release_fixture(scope="core-server-persistence", maintenance_selection=None):
    control = owner.control_owner()
    binding = control.load_binding("kanbien-core-platform", scope)
    expected = {"target": binding["target"], "scope": scope, "source_revision": "a" * 40,
        "primary_image_digest": "sha256:" + "d" * 64, "components": {purpose: {"source_revision": "a" * 40,
            "program_id": binding["programs"][purpose], "image_digest": "sha256:" + character * 64}
            for purpose, character in (("dispatch", "b"), ("worker", "c"))}}
    raw = {name: control.CF.template((control.ROOT / binding[key]).read_text())
        for name, key in (("scope", "template"), ("network", "network_template"))}
    base = {name: {key: "controlled" for key in value["Parameters"]} for name, value in raw.items()}
    base["scope"].update(Scope=scope, SourceRevision=expected["source_revision"], DatabaseResourceId="db-CONTROLLED", DatabaseName="kanbienpersistence")
    prefix = f"{binding['provider']['account_id']}.dkr.ecr.eu-west-1.amazonaws.com/{binding['repository']}@"
    for purpose in ("dispatch", "worker"): base["scope"][purpose.title() + "ImageUri"] = prefix + expected["components"][purpose]["image_digest"]
    packets = {}
    def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with tempfile.TemporaryDirectory() as scratch:
        store = control.Store(Path(scratch))
        for phase, (predecessor, controls) in control.CONTROL_PHASES.items():
            if phase == "accepted-enable": continue
            component = "network" if phase == "network-create" else "scope"
            parameters = {**base[component]}
            if controls is not None: parameters.update(zip(("TickEnabled", "WorkerEnabled", "DenyDispatcherSend"), controls))
            template = control.rendered_template(binding, component, parameters)
            stack = binding["network_stack" if component == "network" else "stack"]
            resources = {key: {"ResourceType": resource["Type"], "PhysicalResourceId": "controlled-" + key} for key, resource in template["Resources"].items()}
            for logical, row in resources.items():
                if row["ResourceType"] == "AWS::Lambda::Version":
                    purpose = "dispatch" if logical.startswith("Dispatch") else "worker"
                    row["PhysicalResourceId"] = f"arn:aws:lambda:eu-west-1:{binding['provider']['account_id']}:function:kc-{scope}-schedule-{purpose}:1"
                if row["ResourceType"] == "AWS::SQS::Queue":
                    row["PhysicalResourceId"] = f"https://sqs.eu-west-1.amazonaws.com/{binding['provider']['account_id']}/{scope}-{logical}"
            state = {"stack_id": "controlled-stack-" + stack, "resources": resources}
            mode = "CREATE" if phase in {"network-create", "scope-create-disabled"} else "UPDATE"
            prior = packets.get(predecessor)
            before = None if mode == "CREATE" else {"parameters": prior["intent"]["parameters"], "state": prior["readback"]}
            inputs = [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())] if mode == "CREATE" else control.CHANGES.update_parameter_inputs(
                before["parameters"], control.ADMISSION.update_overrides(before["parameters"], parameters,
                    controls_only=phase not in {"fault-on", "fault-off"}, fault_only=phase in {"fault-on", "fault-off"}))
            intent = {"schema": "deploy/scheduling-phase-intent/v1", "target": binding["target"], "scope": "shared" if component == "network" else scope,
                "phase": phase, "stack": stack, "mode": mode, "created_at": now(), "template": template, "parameters": parameters,
                "parameter_inputs": inputs, "before": before, "predecessor_sha256": None if prior is None else control.digest(prior["intent"]),
                "source_revision": expected["source_revision"], "network_before": {} if component == "network" else None,
                "maintenance_selection": None if component == "network" else maintenance_selection or
                    ({"qualified_path": "/controlled/core-package.json"} if scope == "core-server-persistence" else
                    {"receipt_path": "/controlled/entity-package.json", "proof_label": "entity-smoke-" + "a" * 24, "expected_predecessor": None})}
            request = control.phase_request(intent)
            preparation, _ = store.reserve("prepare", request); execution, _ = store.reserve("execute", request)
            terminal = {"EventId": "controlled-event-" + phase, "StackId": state["stack_id"], "LogicalResourceId": stack,
                "PhysicalResourceId": state["stack_id"], "ResourceType": "AWS::CloudFormation::Stack", "ResourceStatus": mode + "_COMPLETE",
                "ClientRequestToken": execution["operation_id"], "Timestamp": now()}
            packets[phase] = {"schema": "deploy/scheduling-phase-evidence/v1", "intent": intent, "preparation": preparation,
                "execution": execution, "terminal": terminal, "readback": state, "captured_at": now()}
    return packets, expected


class ReleaseContextTests(unittest.TestCase):
    def test_original_control_chain_derives_immutable_runtime_and_scope(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            phases, expected = release_fixture(scope)
            result = owner.release_context(phases, expected=expected)
            self.assertEqual(result["runtime"]["dispatch"]["version_arn"].split(":")[-1], "1")
            self.assertEqual(result["native_binding"]["image_digest"], expected["primary_image_digest"])
            self.assertEqual(result["database"]["schema"], "platform" if scope == "core-server-persistence" else "entity_smoke")
            self.assertEqual(result, owner.release_context(json.loads(owner.canonical(phases)), expected=expected, historical=True))

    def test_missing_phase_changed_component_or_foreign_lineage_rejects(self):
        phases, expected = release_fixture()
        for change in (lambda p, e: p.pop("fault-off"), lambda p, e: e["components"]["worker"].update(image_digest="sha256:" + "f" * 64),
                       lambda p, e: p["proof-disable"]["intent"].update(predecessor_sha256="f" * 64),
                       lambda p, e: p["scope-create-disabled"]["terminal"].update(ClientRequestToken="foreign")):
            p, e = copy.deepcopy(phases), copy.deepcopy(expected); change(p, e)
            with self.subTest(change=change), self.assertRaises((ValueError, owner.control_owner().Failure)): owner.release_context(p, expected=e)


class ConnectionProofTests(unittest.TestCase):
    def fixture(self):
        context = {"phases": {phase: {"completed_at": stamp} for phase, stamp in (
            ("scope-create-disabled", "2026-11-26T12:00:00Z"), ("proof-enable", "2026-11-26T12:05:00Z"),
            ("proof-disable", "2026-11-26T13:00:00Z"))}}
        values, references = {}, {}
        for purpose in ("dispatch", "worker"):
            references[purpose] = []
            for slot, stamp in (("disabled", "2026-11-26T12:01:00Z"), ("acceptance", "2026-11-26T13:01:00Z")):
                key = purpose + ":" + slot
                references[purpose].append(key)
                values[key] = {"purpose": purpose, "slot": slot, "expected": {"purpose": purpose}, "response": {"checked_at": stamp}}
        def read(reference, kind):
            self.assertEqual(kind, "preflight")
            return values[reference]
        return context, values, references, read

    def test_reuses_initial_connection_without_redundant_middle_invocation(self):
        context, _, references, read = self.fixture()
        self.assertEqual(owner.connection_proof(references, context=context, read=read, observed_at="2026-11-26T13:02:00Z"), references)

    def test_stale_changed_or_misordered_connections_reject(self):
        for change in (
            lambda values, refs: values["worker:disabled"]["response"].update(checked_at="2026-11-26T11:59:00Z"),
            lambda values, refs: values["dispatch:acceptance"]["response"].update(checked_at="2026-11-26T12:59:00Z"),
            lambda values, refs: values["worker:acceptance"]["expected"].update(purpose="dispatch"),
            lambda values, refs: refs["dispatch"].reverse(),
            lambda values, refs: refs["worker"].pop(),
            lambda values, refs: refs["worker"].append(refs["worker"][1]),
        ):
            context, values, references, read = self.fixture(); change(values, references)
            with self.subTest(change=change), self.assertRaises(ValueError):
                owner.connection_proof(references, context=context, read=read, observed_at="2026-11-26T13:02:00Z")


class ScopeJoinTests(unittest.TestCase):
    def test_entity_control_selection_and_shared_manifest_are_required(self):
        context = {"binding": {"scope": "entity-smoke"}}
        state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
            "work_inventory": {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0}}
        values = {}
        references = {"preparation": None, "controls": {}}
        for name, case in (("untouched", "scope-isolation"), ("future", "cost-and-idle")):
            before = delivery_fixture("entity-smoke")["before"]
            if name == "untouched":
                before.update(selection={"kind": "subject", "id": "10000000-0000-4000-8000-000000000005"}, schedule=None,
                    application={"kind": "entity", "present": True, "visibility": "archived", "lifecycle_state": "active"})
            after = copy.deepcopy(before); after["observed_at"] = "2026-11-26T12:04:00.000Z"
            references["controls"][name] = {}
            for when, snapshot in (("before", before), ("after", after)):
                key = name + ":" + when
                references["controls"][name][when] = key
                values[key] = {"operation": "observe-scheduling-proof", "case": case,
                    "result": {"scheduling_observation": snapshot}, "archive": {"preparation": {
                        op: {"operation": {"packet": {"receipt": {"result": {"database_state": copy.deepcopy(state)}}}}}
                        for op in ("scheduling-state", "scheduling-grant", "scheduling-permissions")}}}
        def read(reference, kind):
            self.assertEqual(kind, "native")
            return values[reference]
        args = {"context": context, "read": read, "before_purge": "2026-11-26T12:02:00Z",
            "completed_at": "2026-11-26T12:03:00Z"}
        self.assertEqual(len(owner.scope_proof(references, **args)["controls"]), 2)
        values["untouched:before"]["result"]["scheduling_observation"]["observed_at"] = "2026-11-26T12:03:30.000Z"
        with self.assertRaisesRegex(ValueError, "entity-control-not-preserved"): owner.scope_proof(references, **args)
        values["untouched:before"]["result"]["scheduling_observation"]["observed_at"] = "2026-11-26T12:00:01.000Z"
        values["future:after"]["case"] = "minute-delivery"
        with self.assertRaisesRegex(ValueError, "selection-mismatch"): owner.scope_proof(references, **args)
        values["future:after"]["case"] = "cost-and-idle"
        values["future:after"]["archive"]["preparation"]["scheduling-state"]["operation"]["packet"]["receipt"]["result"]["database_state"]["manifest_sha256"] = "b" * 64
        with self.assertRaises(ValueError): owner.scope_proof(references, **args)

    def test_core_requires_native_initial_state_grant_and_permissions(self):
        context = {"binding": {"scope": "core-server-persistence"}, "phases": {
            "scope-create-disabled": {"completed_at": "2026-11-26T12:05:00Z"}}}
        operations = ("observe-scheduling-state", "grant-scheduling-access", "prove-scheduling-access")
        state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
            "work_inventory": {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0}}
        values = {operation: {"operation": operation, "result": {"database_state": copy.deepcopy(state)}, "task": {
            "started_at": "2026-11-26T12:0" + str(i) + ":00Z", "stopped_at": "2026-11-26T12:0" + str(i) + ":10Z"}}
            for i, operation in enumerate(operations)}
        references = {"preparation": {operation: operation for operation in operations}, "controls": None}
        def read(reference, kind):
            self.assertEqual(kind, "preparation")
            return values[reference]
        args = {"context": context, "read": read, "before_purge": "2026-11-26T12:10:00Z",
            "completed_at": "2026-11-26T12:15:00Z"}
        owner.scope_proof(references, **args)
        values[operations[1]]["result"]["database_state"]["work_inventory"]["pending_outbox"] = 1
        with self.assertRaisesRegex(ValueError, "unrelated-work"): owner.scope_proof(references, **args)


class OwnedSelectionTests(unittest.TestCase):
    def fixture(self, scope):
        before = delivery_fixture(scope)["before"]
        task = {"arn": "controlled", "definition": "controlled", "started_at": "2026-11-26T12:00:00.000Z",
            "stopped_at": "2026-11-26T12:00:02.000Z"}
        packet = {"operation": "observe-scheduling-proof", "result": {"scheduling_observation": before}, "task": task}
        materials = {}
        selected = {"snapshot": owner.proof_semantics().pack_archive(packet, materials, kind="native"), "seed": None}
        if scope == "core-server-persistence":
            seed = {"operation": "seed-scheduling-proof", "result": {"scheduling_seed": {
                "schedule_id": before["schedule"]["id"], "due_at": before["schedule"]["due_at"]}},
                "task": {**task, "stopped_at": "2026-11-26T12:00:00.000Z"}}
            selected["seed"] = owner.proof_semantics().pack_archive(seed, materials, kind="native")
        context = {"binding": {"target": "kanbien-core-platform", "scope": scope}, "native_binding": {"controlled": True},
            "required_after": "2026-11-26T11:59:00.000Z"}
        observation = {"schema": "kanbien/scheduling-database-observation/v1", **context["binding"],
            "binding": context["native_binding"], "task": {**task, "started_at": "2026-11-26T12:00:03.000Z", "stopped_at": "2026-11-26T12:00:04.000Z"},
            "required_after": context["required_after"], "checked_at": "2026-11-26T12:00:05.000Z",
            "database_state": {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
                "work_inventory": {"waiting_schedules": 1, "pending_outbox": 0, "active_processing": 0}}}
        return {"schema": "deploy/scheduling-owned-work-selection/v1", "materials": materials, "snapshots": [selected]}, context, observation

    def test_selected_archives_and_whole_counts_join_for_both_scopes(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            selection, context, observed = self.fixture(scope)
            # This unit controls only the already-tested native provenance
            # boundary; real codec, snapshot semantics and count joins run.
            with patch.object(owner, "native_packet", side_effect=lambda packet, **kwargs: packet) as native:
                result = owner.owned_work_selection(selection, context=context, qualified_path="controlled",
                    database_observation=observed, historical=True)
                self.assertEqual(result["work_inventory"]["waiting_schedules"], 1)
                self.assertEqual(native.call_args.kwargs["required_after"], context["required_after"])

    def test_empty_selection_requires_actual_empty_inventory_not_extra_row_reads(self):
        value, context, observed = self.fixture("core-server-persistence")
        value.update(materials={}, snapshots=[])
        with patch.object(owner, "native_packet", side_effect=AssertionError("unnecessary exact-row task")):
            with self.assertRaisesRegex(owner.ProofFailure, "unrelated-work"):
                owner.owned_work_selection(value, context=context, qualified_path="controlled", database_observation=observed, historical=True)
            observed["database_state"]["work_inventory"]["waiting_schedules"] = 0
            result = owner.owned_work_selection(value, context=context, qualified_path="controlled", database_observation=observed, historical=True)
            self.assertEqual(result["work_inventory"], observed["database_state"]["work_inventory"])

    def test_unrelated_counts_unused_material_stale_and_crossed_snapshot_reject(self):
        for change in (lambda v, c, o: o["database_state"]["work_inventory"].update(waiting_schedules=2),
                       lambda v, c, o: o.update(binding={"foreign": True}),
                       lambda v, c, o: o.update(checked_at="2026-11-26T12:30:00.000Z"),
                       lambda v, c, o: o["task"].update(started_at="2026-11-26T12:00:01.000Z"),
                       lambda v, c, o: owner.proof_semantics().pack_archive({"unrelated": True}, v["materials"], kind="native"),
                       lambda v, c, o: v["snapshots"].append(v["snapshots"][0])):
            selection, context, observed = self.fixture("core-server-persistence")
            change(selection, context, observed)
            with self.subTest(change=change), patch.object(owner, "native_packet", side_effect=lambda packet, **kwargs: packet), self.assertRaises(ValueError):
                owner.owned_work_selection(selection, context=context, qualified_path="controlled", database_observation=observed, historical=True)


class DurableCaseTests(unittest.TestCase):
    def test_entity_due_follows_both_retention_and_recovery_with_strict_boundary(self):
        def set_due(args, due):
            for when in ("before", "after"):
                args[when]["schedule"]["due_at"] = args[when]["selection"]["due_at"] = due
        args = delivery_fixture("entity-smoke")
        self.assertEqual(owner.completed_delivery(**args)["due_at"], "2026-11-26T12:05:00.001Z")
        args["before"]["application"]["restore_eligible_until"] = "2026-11-26T12:05:00.500Z"
        set_due(args, "2026-11-26T12:05:00.501Z")
        self.assertEqual(owner.completed_delivery(**args)["due_at"], "2026-11-26T12:05:00.501Z")
        for restore_until, due in (
            ("2026-11-26T12:01:00.000Z", "2026-11-26T12:05:00.000Z"),
            ("2026-11-26T12:01:00.000Z", "2026-11-26T12:05:00.002Z"),
            ("2026-11-26T12:05:00.500Z", "2026-11-26T12:05:00.001Z"),
            ("2026-11-26T12:05:00.500Z", "2026-11-26T12:05:00.500Z"),
        ):
            args = delivery_fixture("entity-smoke")
            args["before"]["application"]["restore_eligible_until"] = restore_until
            set_due(args, due)
            with self.subTest(restore_until=restore_until, due=due), self.assertRaisesRegex(ValueError, "entity-retention-effect-not-confirmed"):
                owner.completed_delivery(**args)

    def test_complete_native_chain_allows_worker_before_relay_publication_record(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            args = delivery_fixture(scope)
            result = owner.completed_delivery(**args)
            self.assertEqual(result["completed_at"], "2026-11-26T12:05:02.000Z")
            self.assertEqual(result["outbox_sha256"], args["workers"][0]["observation"]["outbox_sha256"])

    def test_incomplete_wrong_generation_early_or_late_delivery_rejected(self):
        changes = [
            lambda args: args["after"].update(processing=None),
            lambda args: args["after"]["processing"]["completion"].update(outcome="terminal-failure"),
            lambda args: args["after"]["schedule"].update(due_at="2026-11-26T12:04:00.000Z"),
            lambda args: args["after"]["outbox"].update(created_at="2026-11-26T12:04:59.000Z"),
            lambda args: args["workers"].clear(),
            lambda args: args["workers"].append(copy.deepcopy(args["workers"][0])),
            lambda args: args["workers"][0]["observation"].update(idempotency="durable-skipped"),
            lambda args: args["dispatches"][0]["observation"].update(trigger=None),
            lambda args: args["after"]["application"].update(present=True),
        ]
        for change in changes:
            args = delivery_fixture("entity-smoke"); change(args)
            with self.subTest(change=change), self.assertRaises(ValueError): owner.completed_delivery(**args)
        args = delivery_fixture(); args["after"]["processing"]["completion"]["completed_at"] = "2026-11-26T12:10:01.000Z"
        args["after"]["observed_at"] = args["after"]["delivery_message"]["enqueuedAt"] = "2026-11-26T12:11:00.000Z"
        with self.assertRaisesRegex(owner.ProofFailure, "time-budget"): owner.completed_delivery(**args)

    def test_restored_row_survives_and_duplicate_cannot_change_durable_fact(self):
        args = delivery_fixture("entity-smoke")
        args["before"]["application"] = args["after"]["application"] = {"kind": "entity", "present": True, "visibility": "archived", "lifecycle_state": "active"}
        owner.completed_delivery(**args, restored=True)
        args = delivery_fixture()
        original = args["after"]
        repeated = copy.deepcopy(original)
        repeated["observed_at"] = repeated["delivery_message"]["enqueuedAt"] = "2026-11-26T12:07:00.000Z"
        worker = args["workers"][0]["observation"]
        worker.update(observed_at="2026-11-26T12:06:30.000Z", idempotency="durable-skipped")
        owner.duplicate_delivery(scope=args["scope"], original=original, repeated=repeated, workers=args["workers"])
        repeated["application"]["fact_digest"] = "f" * 64
        with self.assertRaisesRegex(owner.ProofFailure, "durable-state-changed"):
            owner.duplicate_delivery(scope=args["scope"], original=original, repeated=repeated, workers=args["workers"])

    def test_whole_scope_inventory_cannot_hide_unselected_actionable_work(self):
        args = delivery_fixture()
        state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
            "work_inventory": {"waiting_schedules": 1, "pending_outbox": 0, "active_processing": 0}}
        owner.owned_work_inventory(scope=args["scope"], database_state=state, snapshots=[args["before"]])
        state["work_inventory"]["waiting_schedules"] = 2
        with self.assertRaisesRegex(owner.ProofFailure, "unrelated-work"):
            owner.owned_work_inventory(scope=args["scope"], database_state=state, snapshots=[args["before"]])
        with self.assertRaisesRegex(owner.ProofFailure, "selection-duplicated"):
            owner.owned_work_inventory(scope=args["scope"], database_state=state, snapshots=[args["before"], args["before"]])

    def test_failure_retains_exact_outbox_and_recovery_reuses_it(self):
        args = delivery_fixture("entity-smoke")
        interrupted = copy.deepcopy(args["after"])
        interrupted.update(observed_at="2026-11-26T12:05:01.500Z", processing=None, application=args["before"]["application"])
        interrupted["outbox"].update(state="pending")
        interrupted["outbox"].pop("published_at")
        interrupted["delivery_message"]["enqueuedAt"] = interrupted["observed_at"]
        args["after"]["outbox"]["attempt"] = 2
        args.update(interrupted=interrupted, disabled_at="2026-11-26T12:00:00.000Z",
            restored_at="2026-11-26T12:05:01.750Z", kind="send-failure")
        owner.interrupted_delivery(**args)
        for change in (lambda value: value["interrupted"]["outbox"].update(attempt=0),
                       lambda value: value["after"]["outbox"].update(attempt=1),
                       lambda value: value["interrupted"].update(application={"kind": "entity", "present": False}),
                       lambda value: value.update(restored_at="2026-11-26T12:04:00.000Z")):
            broken = copy.deepcopy(args); change(broken)
            with self.subTest(change=change), self.assertRaises(ValueError): owner.interrupted_delivery(**broken)

    def test_missed_tick_requires_a_due_reminder_still_waiting_for_a_full_minute(self):
        args = delivery_fixture()
        interrupted = copy.deepcopy(args["before"])
        interrupted["observed_at"] = "2026-11-26T12:06:00.000Z"
        args["after"]["observed_at"] = args["after"]["delivery_message"]["enqueuedAt"] = "2026-11-26T12:08:00.000Z"
        args["after"]["outbox"].update(created_at="2026-11-26T12:07:01.000Z", published_at="2026-11-26T12:07:03.000Z")
        args["after"]["processing"]["completion"]["completed_at"] = "2026-11-26T12:07:02.000Z"
        args["workers"][0]["observation"]["observed_at"] = "2026-11-26T12:07:02.000Z"
        args["dispatches"][0]["observation"]["observed_at"] = "2026-11-26T12:07:01.500Z"
        args.update(interrupted=interrupted, disabled_at="2026-11-26T12:00:00.000Z",
            restored_at="2026-11-26T12:07:00.000Z", kind="missed-tick")
        owner.interrupted_delivery(**args)
        args["interrupted"]["observed_at"] = "2026-11-26T12:05:59.000Z"
        with self.assertRaisesRegex(owner.ProofFailure, "missed-tick-not-observed"): owner.interrupted_delivery(**args)


class AutomaticTriggerTests(unittest.TestCase):
    def fixture(self):
        dispatches = delivery_fixture()["dispatches"]
        observation = dispatches[0]["observation"]
        expected = {"schedule_arn": observation["trigger"]["schedule_arn"], "function_arn": observation["function_arn"],
            "role_arn": "arn:aws:iam::123456789012:role/scheduling-tick", "dead_letter_queue_arn": "arn:aws:sqs:eu-west-1:123456789012:scope-dlq", "input": "controlled-source-owned-input"}
        group = expected["schedule_arn"].split("/")[1]
        schedule = {"Arn": expected["schedule_arn"], "GroupName": group, "Name": "due-pass", "State": "ENABLED", "ScheduleExpression": "rate(1 minute)",
            "ScheduleExpressionTimezone": "UTC", "FlexibleTimeWindow": {"Mode": "OFF"}, "Target": {"Arn": expected["function_arn"], "RoleArn": expected["role_arn"],
                "Input": expected["input"], "RetryPolicy": {"MaximumEventAgeInSeconds": 60, "MaximumRetryAttempts": 0}, "DeadLetterConfig": {"Arn": expected["dead_letter_queue_arn"]}}}
        metrics = {"Label": "InvocationAttemptCount", "Datapoints": [{"Timestamp": "2026-11-26T12:05:00+00:00", "Sum": 1.0, "Unit": "Count"}]}
        calls = []
        def provider(service, operation, **arguments):
            calls.append((service, operation, arguments))
            if operation == "get-schedule": return schedule
            if operation == "list-schedules": return {"Schedules": [{"Arn": expected["schedule_arn"]}]}
            self.assertEqual((service, operation), ("cloudwatch", "get-metric-statistics"))
            self.assertEqual(arguments["Namespace"], "AWS/Scheduler")
            self.assertEqual(arguments["Dimensions"], [{"Name": "ScheduleGroup", "Value": group}])
            self.assertEqual(arguments["Statistics"], ["Sum"])
            return metrics
        packet = owner.capture_automatic_trigger(provider, expected=expected, started_at="2026-11-26T12:05:00.000Z",
            ended_at="2026-11-26T12:06:00.000Z", dispatches=dispatches)
        self.assertEqual(len(calls), 3)
        return packet, expected, dispatches

    def test_actual_schedule_group_and_service_metric_join_native_runtime(self):
        packet, expected, dispatches = self.fixture()
        checked = owner.validate_automatic_trigger(json.loads(owner.canonical(packet)), expected=expected, dispatches=dispatches)
        self.assertEqual(checked["executions"], 1)
        self.assertEqual(checked["invocation_attempts"], 1)

    def test_event_marker_alone_does_not_prove_automatic_trigger(self):
        packet, expected, dispatches = self.fixture()
        mutations = [
            lambda value: value["schedule"].update(State="DISABLED"),
            lambda value: value["schedule"]["Target"].update(Arn="other-function"),
            lambda value: value["metric_response"].update(Datapoints=[]),
            lambda value: value["metric_response"]["Datapoints"][0].update(Sum=0),
            lambda value: value["metric_response"]["Datapoints"][0].update(Timestamp="2026-11-26T12:04:00Z"),
            lambda value: value["metric_query"]["Dimensions"][0].update(Value="other-group"),
            lambda value: value["group_schedule_arns"].append("other-schedule"),
        ]
        for mutate in mutations:
            value = copy.deepcopy(packet); mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(owner.ProofFailure):
                owner.validate_automatic_trigger(value, expected=expected, dispatches=dispatches)
        with self.assertRaisesRegex(owner.ProofFailure, "runtime-mismatch"):
            owner.validate_automatic_trigger(packet, expected=expected, dispatches=[*dispatches, *dispatches])


class RuntimeEvidenceTests(unittest.TestCase):
    def test_original_runtime_window_survives_archive_without_private_values(self):
        expected, events, window = runtime_fixture()
        def provider(service, operation, **arguments):
            if service == "lambda":
                return {"Code": {"ResolvedImageUri": expected["image_uri"]}, "Configuration": {
                    "FunctionArn": expected["version_arn"], "Version": "2", "State": "Active", "MemorySize": 512, "Timeout": 60,
                    "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": expected["source_revision"], "UNRELATED_SECRET": "PRIVATE-CANARY"}},
                    "LoggingConfig": {"LogGroup": expected["log_group"], "LogFormat": "JSON"}}}
            unrelated = {**events[0], "eventId": "unrelated", "message": json.dumps({"level": "error", "message": "PRIVATE-CANARY"})}
            return {"events": [*events, unrelated]}
        packet = owner.capture_runtime_window(provider, expected=expected, **window)
        self.assertNotIn("PRIVATE-CANARY", json.dumps(packet))
        self.assertEqual(packet["events"], events)
        # The exact accepted packet is sufficient after logs expire; this pure
        # route neither accepts a hand-written verdict nor needs live provider.
        retained = json.loads(owner.canonical(packet))
        self.assertEqual(owner.validate_runtime_window(retained, expected=expected), owner.runtime_records(events, expected=expected, **window))
        for variant in ("function", "expected", "event", "extra", "unrelated"):
            broken = copy.deepcopy(retained)
            if variant == "function": broken["function"]["Configuration"]["Version"] = "3"
            if variant == "expected": broken["expected"]["image_uri"] = "foreign"
            if variant == "event": broken["events"].pop()
            if variant == "extra": broken["passed"] = True
            if variant == "unrelated": broken["events"].append({**events[0], "eventId": "extra", "message": "unrelated"})
            with self.subTest(variant=variant), self.assertRaises(owner.ProofFailure):
                owner.validate_runtime_window(broken, expected=expected)

    def test_actual_function_reader_joins_original_paginated_reports(self):
        for purpose in ("worker", "dispatch"):
            expected, events, window = runtime_fixture(purpose)
            calls = []
            def provider(service, operation, **arguments):
                calls.append((service, operation, arguments))
                if (service, operation) == ("lambda", "get-function"):
                    self.assertEqual(arguments, {"FunctionName": expected["version_arn"]})
                    return {"Code": {"ResolvedImageUri": expected["image_uri"]}, "Configuration": {
                        "FunctionArn": expected["version_arn"], "Version": "2", "State": "Active", "MemorySize": 512, "Timeout": 60,
                        "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": expected["source_revision"]}},
                        "LoggingConfig": {"LogGroup": expected["log_group"], "LogFormat": "JSON"}}}
                self.assertEqual((service, operation), ("logs", "filter-log-events"))
                self.assertEqual(arguments["logGroupName"], expected["log_group"])
                return {"events": events[2:]} if arguments.get("nextToken") == "second" else {"events": events[:2], "nextToken": "second"}
            result = owner.runtime_window(provider, expected=expected, **window)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["billed_duration_ms"], 1250)
            self.assertEqual(result[0]["observation"]["purpose"], purpose)
            self.assertEqual(len(calls), 3)

    def test_known_lambda_wrapper_and_duplicate_delivery_outcome(self):
        expected, events, window = runtime_fixture()
        record = json.loads(events[1]["message"])
        record["fields"]["scheduling_runtime"]["idempotency"] = "durable-skipped"
        events[1]["message"] = json.dumps({"timestamp": "2026-11-26T12:00:01.000Z", "requestId": record["fields"]["scheduling_runtime"]["request_id"], "message": json.dumps(record)})
        result = owner.runtime_records(events, expected=expected, **window)
        self.assertEqual(result[0]["observation"]["idempotency"], "durable-skipped")

    def test_success_text_without_matching_system_custody_is_rejected(self):
        mutations = [
            (0, lambda row: row["record"].update(version="1")),
            (2, lambda row: row["record"].update(requestId="another")),
            (2, lambda row: row["record"].update(status="timeout")),
            (2, lambda row: row["record"]["metrics"].update(billedDurationMs=-1)),
            (2, lambda row: row["record"]["metrics"].update(memorySizeMB=1024)),
            (1, lambda row: row["fields"]["scheduling_runtime"].update(source_revision="d" * 40)),
            (1, lambda row: row["fields"]["scheduling_runtime"].update(payload="PRIVATE-CANARY")),
            (1, lambda row: row["fields"]["scheduling_runtime"].update(idempotency="processed")),
        ]
        for index, mutate in mutations:
            expected, events, window = runtime_fixture()
            row = json.loads(events[index]["message"]); mutate(row); events[index]["message"] = json.dumps(row)
            with self.subTest(index=index), self.assertRaises(owner.ProofFailure) as failure:
                owner.runtime_records(events, expected=expected, **window)
            self.assertNotIn("PRIVATE-CANARY", str(failure.exception))
        for variant in ("missing", "duplicate", "stream", "foreign-component", "chronology", "outside"):
            expected, events, window = runtime_fixture()
            if variant == "missing": events.pop()
            if variant == "duplicate": events.append(copy.deepcopy(events[1]))
            if variant == "stream": events[2]["logStreamName"] = "another"
            if variant == "foreign-component":
                for event in events: event["logStreamName"] = "2026/11/26/another-function[2][controlled-environment]"
            if variant == "chronology": events[0]["timestamp"] += 2000
            if variant == "outside": events[2]["timestamp"] += 61000
            with self.subTest(variant=variant), self.assertRaises((owner.ProofFailure, owner.ADMISSION.AdmissionFailure)):
                owner.runtime_records(events, expected=expected, **window)

    def test_foreign_actual_image_stops_before_log_read(self):
        expected, _, window = runtime_fixture()
        calls = []
        def provider(service, operation, **arguments):
            calls.append((service, operation))
            return {"Code": {"ResolvedImageUri": "foreign"}, "Configuration": {}}
        with self.assertRaises(owner.ProofFailure): owner.runtime_window(provider, expected=expected, **window)
        self.assertEqual(calls, [("lambda", "get-function")])


class AcceptanceCompositionTests(unittest.TestCase):
    """Real join/codec/runtime reducers; native/provider authenticity is controlled.

    These packets are local fixtures, not accepted AWS evidence. The separate
    native-owner tests establish original task and provider receipt provenance.
    """

    def fixture(self, scope):
        semantics, control = owner.proof_semantics(), owner.control_owner()
        beginning = datetime(2026, 11, 26, 12, tzinfo=timezone.utc)
        def stamp(seconds):
            return (beginning + timedelta(seconds=seconds)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        times = [beginning + timedelta(seconds=index * 600 + offset)
            for index in range(len(control.CONTROL_PHASES) - 1) for offset in (0, 10, 20)]
        with patch(__name__ + ".datetime") as clock:
            clock.now.side_effect = times
            phases, expected = release_fixture(scope)
        for index, packet in enumerate(phases.values()):
            packet["preparation"]["reserved_at"] = stamp(index * 600 + 2)
            packet["execution"]["reserved_at"] = stamp(index * 600 + 3)
        expected["evidence_class"] = "live"
        context = owner.release_context(phases, expected=expected, historical=True)
        materials, observations = {}, {}
        def add(kind, packet):
            if kind in semantics.ARCHIVE_KINDS:
                return semantics.pack_archive(packet, materials, kind=kind)
            entry = {"kind": kind, "packet": packet}
            reference = semantics.digest(entry); materials[reference] = entry
            return reference
        def native(checked, kind="native"):
            return add(kind, {"controlled_native": True, "binding": context["native_binding"], "checked": checked})
        state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
            "work_inventory": {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0}}
        preparation = {name: {"operation": {"packet": {"receipt": {"result": {"database_state": state}}}}}
            for name in ("scheduling-state", "scheduling-grant", "scheduling-permissions")}
        ordinal = 0
        def snapshot(case, value):
            return native({"operation": "observe-scheduling-proof", "case": case,
                "result": {"scheduling_observation": value}, "archive": {"preparation": preparation}})
        def runtime(purpose, body):
            selected = context["runtime"][purpose]
            body.update(purpose=purpose, source_revision=selected["source_revision"], function_arn=selected["version_arn"])
            at = owner.ADMISSION.utc(body["observed_at"])
            messages = [
                {"type": "platform.start", "record": {"requestId": body["request_id"], "version": "1"}},
                {"level": "info", "message": "Scheduling runtime observation.", "fields": {"scheduling_runtime": body}},
                {"type": "platform.report", "record": {"requestId": body["request_id"], "status": "success",
                    "metrics": {"billedDurationMs": 1250, "memorySizeMB": 512}}}]
            events = [{"eventId": body["request_id"] + str(i), "logStreamName": "2026/11/26/" + selected["version_arn"].split(":")[-2] + "[1][controlled]",
                "timestamp": int((at + timedelta(seconds=i - 1)).timestamp() * 1000), "message": json.dumps(message)}
                for i, message in enumerate(messages)]
            packet = {"schema": "deploy/scheduling-runtime-window/v1", "expected": selected,
                "started_at": (at - timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
                "ended_at": (at + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
                "function": {"Code": {"ResolvedImageUri": selected["image_uri"]}, "Configuration": {
                    "FunctionArn": selected["version_arn"], "Version": "1", "State": "Active", "MemorySize": 512, "Timeout": 60,
                    "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": selected["source_revision"]}},
                    "LoggingConfig": {"LogGroup": selected["log_group"], "LogFormat": "JSON"}}}, "events": events}
            owner.validate_runtime_window(packet, expected=selected)
            return add(purpose, packet)
        def delivery(case, due, delivered=None, restored=False):
            nonlocal ordinal
            ordinal += 1
            delivered = due if delivered is None else delivered
            data = delivery_fixture(scope)
            def translate(value):
                if isinstance(value, dict): return {key: translate(item) for key, item in value.items()}
                if isinstance(value, list): return [translate(item) for item in value]
                if isinstance(value, str) and value.startswith("2026-11-26T"):
                    return stamp((owner.ADMISSION.utc(value) - beginning).total_seconds() - 300 + due)
                if isinstance(value, str) and value.startswith("10000000-"):
                    return value[:-3] + str(ordinal * 10 + int(value[-3:])).zfill(3)
                return value
            before, after = translate(data["before"]), translate(data["after"])
            after["observed_at"] = stamp(delivered + 60)
            after["outbox"].update(created_at=stamp(delivered + 1), published_at=stamp(delivered + 3))
            after["processing"]["completion"]["completed_at"] = stamp(delivered + 2)
            after["delivery_message"]["enqueuedAt"] = after["observed_at"]
            if restored:
                before["application"] = {"kind": "entity", "present": True, "visibility": "archived", "lifecycle_state": "active"}
                after["application"] = copy.deepcopy(before["application"])
            dispatch = copy.deepcopy(data["dispatches"][0]["observation"])
            dispatch.update(observed_at=stamp(delivered + 1.5), request_id=f"00000000-0000-4000-8000-{ordinal:012d}")
            dispatch["trigger"].update(schedule_arn=context["trigger"]["schedule_arn"], scheduled_at=stamp(delivered))
            worker = copy.deepcopy(data["workers"][0]["observation"])
            worker.update(observed_at=stamp(delivered + 2), request_id=f"00000000-0000-4000-8001-{ordinal:012d}",
                outbox_sha256=owner.hashlib.sha256(after["outbox"]["id"].encode()).hexdigest())
            if case == "failure-recovery":
                after["outbox"].update(attempt=2, created_at=stamp(due + 1))
            result = {"seed": None, "before": snapshot(case, before), "after": snapshot(case, after),
                "dispatch": runtime("dispatch", dispatch), "worker": runtime("worker", worker)}
            if scope == "core-server-persistence":
                result["seed"] = native({"operation": "seed-scheduling-proof", "result": {"scheduling_seed": {
                    "schedule_id": before["schedule"]["id"], "due_at": before["schedule"]["due_at"]}},
                    "task": {"stopped_at": stamp(due - 300)}})
            automatic = AutomaticTriggerTests().fixture()[0]
            trigger = context["trigger"]
            automatic.update(expected=trigger, started_at=stamp(delivered), ended_at=stamp(delivered + 60),
                group_schedule_arns=[trigger["schedule_arn"]])
            automatic["schedule"].update(Arn=trigger["schedule_arn"], GroupName=trigger["schedule_arn"].split("/")[1])
            automatic["schedule"]["Target"].update(Arn=trigger["function_arn"], RoleArn=trigger["role_arn"], Input=trigger["input"],
                DeadLetterConfig={"Arn": trigger["dead_letter_queue_arn"]})
            automatic["metric_query"] = owner.trigger_query(trigger, automatic["started_at"], automatic["ended_at"])
            automatic["metric_response"]["Datapoints"][0]["Timestamp"] = stamp(delivered)
            result["automatic"] = add("automatic", automatic)
            if case in {"missed-tick-recovery", "failure-recovery"}:
                interrupted = copy.deepcopy(before); interrupted["observed_at"] = stamp(due + 61)
                if case == "failure-recovery":
                    interrupted.update(schedule=after["schedule"], outbox={**after["outbox"], "state": "pending", "attempt": 1},
                        delivery_message={**after["delivery_message"], "enqueuedAt": interrupted["observed_at"]})
                    interrupted["outbox"].pop("published_at")
                result["interrupted"] = snapshot(case, interrupted)
            return result, before, after, worker
        first, _, after, worker = delivery("minute-delivery", 1500)
        observations["minute-delivery"] = first
        repeated = copy.deepcopy(after); repeated["observed_at"] = stamp(1625)
        repeated["delivery_message"]["enqueuedAt"] = repeated["observed_at"]
        worker.update(observed_at=stamp(1623), idempotency="durable-skipped", request_id="00000000-0000-4000-8002-000000000001")
        observations["duplicate-delivery"] = {"delivery": first, "repeated": snapshot("minute-delivery", repeated),
            "worker": runtime("worker", worker), "effect": add("effect", {"queue_arn": context["queue_arn"], "acknowledgement": "retained", "reserved_at": stamp(1622)})}
        observations["missed-tick-recovery"] = delivery("missed-tick-recovery", 2100, 2460)[0]
        observations["failure-recovery"] = {"delivery": delivery("failure-recovery", 3900, 4860)[0], "effect": add("effect", {
            "queue_arn": context["queue_arn"], "operation_id": "controlled-failure", "request_id": "00000000-0000-4000-8003-000000000001",
            "invoked_at": stamp(3902), "request_sha256": "f" * 64})}
        if scope == "entity-smoke":
            observations["cancellation"] = delivery("cancellation", 1680, restored=True)[0]
            controls = {}
            for name, case in (("untouched", "scope-isolation"), ("future", "cost-and-idle")):
                value = copy.deepcopy(delivery_fixture(scope)["before"])
                value["selection"]["id"] = "20000000-0000-4000-8000-00000000000" + ("1" if name == "untouched" else "2")
                if name == "untouched":
                    value.update(selection={"kind": "subject", "id": value["selection"]["id"]}, schedule=None,
                        application={"kind": "entity", "present": True, "visibility": "active", "lifecycle_state": "active"})
                else:
                    value["schedule"]["subject"]["id"] = value["selection"]["id"]
                    value["selection"]["due_at"] = value["schedule"]["due_at"] = stamp(1700.001)
                    value["application"].update(deleted_at=stamp(1400), restore_eligible_until=stamp(1460))
                value["observed_at"] = stamp(1420)
                later = copy.deepcopy(value); later["observed_at"] = stamp(1560)
                controls[name] = {"before": snapshot(case, value), "after": snapshot(case, later)}
            observations["scope-isolation"] = {"preparation": None, "controls": controls}
        else:
            observations["cancellation"] = {"applicable": False, "reason": "baseline-job-has-no-entity-lifecycle"}
            observations["scope-isolation"] = {"controls": None, "preparation": {operation: native({"operation": operation,
                "result": {"database_state": state}, "task": {"started_at": stamp(60 + index * 60), "stopped_at": stamp(90 + index * 60)}}, "preparation")
                for index, operation in enumerate(("observe-scheduling-state", "grant-scheduling-access", "prove-scheduling-access"))}}
        connections = {}
        for purpose, runtime_identity in context["runtime"].items():
            selected = {"purpose": purpose, "function_arn": runtime_identity["version_arn"], "source_revision": expected["source_revision"],
                "image_uri": runtime_identity["image_uri"], "database": {**context["database"], "username": context["users"][purpose]},
                "endpoint_id": context["endpoint_id"], "queue": None if purpose == "dispatch" else {"arn": context["queue_arn"], "address_count": 2}}
            connections[purpose] = [add("preflight", {"reservation": {"request": {"expected": selected, "slot": slot}},
                "checked": {"purpose": purpose, "slot": slot, "expected": selected, "response": {"checked_at": stamp(at)}}})
                for slot, at in (("disabled", 660), ("acceptance", 5460))]
        cost = {"components": {scope: context["runtime"]}, "endpoint_id": context["endpoint_id"], "database": context["database"]["name"],
            "notification_topic_arn": phases["scope-create-disabled"]["intent"]["parameters"]["AlarmTopicArn"],
            "projection": {"expected": {"within_ceiling": True, "capacity_supported": True}}}
        recovery_ref = observations["failure-recovery"]["delivery"]["dispatch"]
        alert = {"recovery_window": materials[recovery_ref]["packet"], "notification_confirmed": True}
        observations["cost-and-idle"] = {"materials": materials,
            "phases": {phase: add("phase", packet) for phase, packet in phases.items()}, "qualified_path": "controlled/maintenance-receipt.json",
            "connections": connections, "cost": add("cost", cost), "alert": add("alert", alert)}
        evidence = {"schema": semantics.RUNTIME_SCHEMA, "evidence_class": "live", **{key: expected[key] for key in (
            "target", "scope", "source_revision", "primary_image_digest")}, "observed_at": stamp(5520),
            "components": {purpose: {"program_id": expected["components"][purpose]["program_id"],
                "image_digest": expected["components"][purpose]["image_digest"], "version_arn": item["version_arn"]}
                for purpose, item in context["runtime"].items()}, "observations": observations}
        return evidence, expected

    def validate(self, evidence, expected, *, reader=None):
        control = owner.control_owner()
        def native(packet, **args):
            self.assertTrue(packet["controlled_native"])
            self.assertEqual(packet["binding"], args["context"]["native_binding"])
            return packet["checked"]
        def effect(packet, **args):
            owner.require(packet["queue_arn"] == args["expected"]["queue_arn"], "controlled-effect-foreign")
            return packet
        def alert(packet, **args):
            owner.require(packet["notification_confirmed"] is True, "controlled-alert-human-confirmation-missing")
            return packet
        alert_owner = type("ControlledAlertOwner", (), {"validate_scheduling_alert": staticmethod(alert)})()
        real_module = control.module
        def selected_module(name, path):
            return alert_owner if name == "scheduling_final_alerts" else real_module(name, path)
        with patch.object(owner, "native_packet", side_effect=native), \
                patch.object(control, "validate_preflight_evidence", side_effect=lambda packet, **_: packet["checked"]), \
                patch.object(control, "validate_proof_effect", side_effect=effect), \
                patch.object(owner, "authenticate_cost_evidence", return_value=None), \
                patch.object(control, "module", side_effect=selected_module):
            return (reader or owner.validate_acceptance_evidence)(evidence, expected=expected, historical=True)

    def replace_material(self, evidence, container, key, mutate):
        materials = evidence["observations"]["cost-and-idle"]["materials"]
        previous = container[key]
        entry = materials[previous]
        if entry["kind"] in owner.proof_semantics().ARCHIVE_KINDS:
            packet, _ = owner.proof_semantics().unpack_archive(previous, materials, kind=entry["kind"])
            mutate(packet)
            container[key] = owner.proof_semantics().pack_archive(packet, materials, kind=entry["kind"])
        else:
            changed = copy.deepcopy(entry); mutate(changed["packet"])
            container[key] = owner.proof_semantics().digest(changed); materials[container[key]] = changed
        # An invalid branch must fail before old unused parts could hide it.

    def test_both_scopes_join_real_archives_phases_runtime_and_case_reducers(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            with self.subTest(scope=scope):
                evidence, expected = self.fixture(scope)
                self.assertIs(self.validate(evidence, expected), evidence)
                self.assertLess(len(owner.canonical(evidence)), owner.proof_semantics().LIMIT)
                self.assertEqual(evidence["observations"]["duplicate-delivery"]["delivery"],
                    evidence["observations"]["minute-delivery"])

    def test_duplicate_must_reuse_the_completed_minute_original(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            evidence, expected = self.fixture(scope)
            evidence["observations"]["duplicate-delivery"]["delivery"] = evidence["observations"]["missed-tick-recovery"]
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, "duplicate-original-not-minute"):
                self.validate(evidence, expected)

    def test_live_acceptance_rejects_actual_wiring_drift_before_other_evidence(self):
        evidence, expected = self.fixture("core-server-persistence")
        common = evidence["observations"]["cost-and-idle"]
        original, _ = owner.archive_materials(common["materials"])
        disabled = original(common["phases"]["proof-disable"], "phase")
        control = owner.control_owner()
        with patch.object(owner, "datetime") as clock, \
                patch.object(control, "Provider") as provider, \
                patch.object(control, "authenticate_phase_evidence") as authenticate, \
                patch.object(control, "disabled_phase", return_value=disabled), \
                patch.object(control, "observe_current", side_effect=control.Failure("function-budget-mismatch")) as observe, \
                patch.object(control, "cost_intent") as budget:
            clock.now.return_value = owner.ADMISSION.utc(evidence["observed_at"])
            with self.assertRaisesRegex(control.Failure, "function-budget-mismatch"):
                owner.validate_acceptance_evidence(evidence, expected=expected)
            observe.assert_called_once_with(provider.return_value, control.load_binding(expected["target"], expected["scope"]))
            self.assertEqual(authenticate.call_count, len(control.CONTROL_PHASES) - 1)
            budget.assert_not_called()

    def test_missing_connection_case_identity_and_unused_material_reject(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            for change, code in (
                (lambda e: e["observations"]["cost-and-idle"]["connections"].pop("worker"), "connections-incomplete"),
                (lambda e: e["observations"].pop("minute-delivery"), "cases-incomplete"),
                (lambda e: e["components"]["worker"].update(image_digest="sha256:" + "e" * 64), "components-mismatch"),
                (lambda e: self.replace_material(e, e["observations"]["duplicate-delivery"], "effect", lambda p: p.update(queue_arn="foreign")), "effect-foreign"),
                (lambda e: owner.proof_semantics().pack_archive({"unrelated": True}, e["observations"]["cost-and-idle"]["materials"], kind="native"), "material-unused"),
            ):
                evidence, expected = self.fixture(scope); change(evidence)
                with self.subTest(scope=scope, code=code), self.assertRaisesRegex(ValueError, code): self.validate(evidence, expected)

    def test_cost_alert_and_duplicate_chronology_remain_final_gates(self):
        for kind, code in (("cost", "monthly-cost-not-admitted"), ("alert", "human-confirmation-missing"), ("duplicate", "skip-predates-send")):
            evidence, expected = self.fixture("core-server-persistence")
            common = evidence["observations"]["cost-and-idle"]
            if kind == "cost":
                self.replace_material(evidence, common, "cost", lambda value: value["projection"]["expected"].update(within_ceiling=False))
            elif kind == "alert":
                self.replace_material(evidence, common, "alert", lambda value: value.update(notification_confirmed=False))
            else:
                self.replace_material(evidence, evidence["observations"]["duplicate-delivery"], "effect",
                    lambda p: p.update(reserved_at="2026-11-26T12:27:04.000Z"))
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, code): self.validate(evidence, expected)

    def test_controls_bracket_minute_purge_without_extending_real_retention(self):
        for name, when, stamp in (
            ("untouched", "before", "2026-11-26T12:25:30.000Z"),
            ("future", "before", "2026-11-26T12:25:30.000Z"),
            ("untouched", "after", "2026-11-26T12:25:01.000Z"),
            ("future", "after", "2026-11-26T12:25:01.000Z"),
        ):
            evidence, expected = self.fixture("entity-smoke")
            pair = evidence["observations"]["scope-isolation"]["controls"][name]
            self.replace_material(evidence, pair, when,
                lambda packet: packet["checked"]["result"]["scheduling_observation"].update(observed_at=stamp))
            with self.subTest(name=name, when=when), self.assertRaisesRegex(ValueError, "entity-control-not-preserved"):
                self.validate(evidence, expected)

    def test_native_case_and_original_runtime_rows_cannot_be_substituted(self):
        for kind, code in (("native", "native-case-mismatch"), ("worker", "runtime-")):
            evidence, expected = self.fixture("entity-smoke")
            delivery = evidence["observations"]["minute-delivery"]
            if kind == "native":
                self.replace_material(evidence, delivery, "before", lambda value: value["checked"].update(case="cancellation"))
            else:
                self.replace_material(evidence, delivery, "worker", lambda value: value["events"].pop())
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, code): self.validate(evidence, expected)

    def test_assembler_resolves_typed_originals_and_rejects_unused_selection(self):
        # Files/custody/current-provider authentication are controlled here;
        # the assembler, archive codec and complete historical join are real.
        evidence, expected = self.fixture("entity-smoke")
        common = evidence["observations"]["cost-and-idle"]
        semantics, control = owner.proof_semantics(), owner.control_owner()
        original, _ = owner.archive_materials(common["materials"])
        sources, packets, labels = {}, {}, {}
        def select(value):
            if isinstance(value, str) and value in common["materials"]:
                if value not in labels:
                    kind = common["materials"][value]["kind"]
                    label = "selected-" + str(len(labels)); path = "controlled/" + label + ".json"
                    labels[value] = label; sources[label] = {"kind": kind, "path": path}
                    packets[path] = original(value, kind)
                return {"schema": "deploy/scheduling-material-selection/v1", "name": labels[value]}
            if isinstance(value, dict): return {key: select(item) for key, item in value.items()}
            if isinstance(value, list): return [select(item) for item in value]
            return value
        selection = {"schema": "deploy/scheduling-runtime-selection/v1", "materials": sources,
            "observations": select({key: value for key, value in evidence["observations"].items() if key != "cost-and-idle"}),
            **{key: select(common[key]) for key in ("connections", "cost", "alert")}}
        phases = {phase: original(reference, "phase") for phase, reference in common["phases"].items()}
        budget = {"source_revision": expected["source_revision"], "scopes": {expected["scope"]: {
            "maintenance": {"image_digest": expected["primary_image_digest"]}}}}
        validate = owner.validate_acceptance_evidence
        def checked(value, *, expected):
            return self.validate(value, expected, reader=validate)
        with patch.object(semantics, "read", side_effect=lambda path: copy.deepcopy(packets[path])), \
                patch.object(control, "qualified_pair", return_value=expected["components"]), \
                patch.object(control, "cost_intent", return_value=budget), \
                patch.object(control, "capture_phase", side_effect=lambda provider, store, binding, phase: phases[phase]), \
                patch.object(owner, "validate_acceptance_evidence", side_effect=checked), \
                patch.object(owner, "datetime") as clock:
            clock.now.return_value = owner.ADMISSION.utc(evidence["observed_at"])
            arguments = {"package_paths": {"dispatch": "controlled/dispatch", "worker": "controlled/worker"},
                "qualified_path": common["qualified_path"], "selection": selection}
            result = owner.assemble_acceptance_evidence(None, None, control.load_binding(expected["target"], expected["scope"]), **arguments)
            self.assertEqual(result["observations"], evidence["observations"])
            selection["materials"]["unused"] = copy.deepcopy(next(iter(sources.values())))
            with self.assertRaisesRegex(ValueError, "assembly-material-unused"):
                owner.assemble_acceptance_evidence(None, None, control.load_binding(expected["target"], expected["scope"]), **arguments)


class ProjectionTests(unittest.TestCase):
    def test_initial_envelope_is_not_claimed_measured_or_automatically_enforced(self):
        value = owner.initial_cost_projection(**initial_inputs())
        self.assertLess(Decimal(value["projected_usd"]), 10)
        self.assertFalse(value["free_tier_assumed"])
        self.assertEqual(value["limits"]["endpoint_hours"], 24)
        self.assertEqual(value["qualification"], "operator-managed-lifetimes-and-complete-native-reservations-required")
        self.assertNotIn("maintenance_and_restore_reserve", value["costs_usd"])
        self.assertIn("maintenance:task-one", value["costs_usd"])

    def test_all_fixed_costs_and_worst_scope_are_counted(self):
        args = inputs(); value = owner.monthly_cost_projection(**args)
        self.assertEqual(value["days"], 31)
        self.assertEqual(value["billed_gb_seconds"], "180800.000000")
        self.assertEqual(value["costs_usd"]["endpoint"], "16.368000")
        self.assertEqual(value["costs_usd"]["alarms"], "0.800000")
        self.assertTrue(value["within_ceiling"])
        args["samples"][1]["billed_duration_ms"] = 10000
        expensive = owner.monthly_cost_projection(**args)
        self.assertFalse(expensive["within_ceiling"])
        self.assertNotEqual(expensive["inputs_sha256"], value["inputs_sha256"])

    def test_missing_foreign_duplicate_and_unpriced_facts_fail_closed(self):
        changes = [
            lambda args: args.update(region="us-east-1"),
            lambda args: args.update(image_bytes=0),
            lambda args: args["samples"].pop(),
            lambda args: args["samples"].append(copy.deepcopy(args["samples"][0])),
            lambda args: args["samples"][0].update(kind="preflight"),
            lambda args: args["samples"][0].update(memory_mb=256),
            lambda args: args["samples"][0].update(billed_duration_ms=float("nan")),
            lambda args: args["samples"][0].update(billed_duration_ms=-1),
            lambda args: args["samples"][0].update(evidence_sha256=""),
            lambda args: args["priced_extras"].pop("database_cpu"),
            lambda args: args["priced_extras"]["database_cpu"].update(usd=None),
            lambda args: args["priced_extras"]["database_cpu"].update(usd=True),
        ]
        for change in changes:
            args = inputs(); change(args)
            with self.subTest(change=change), self.assertRaises(owner.ProofFailure):
                owner.monthly_cost_projection(**args)


PRICE_NOW = datetime.fromisoformat("2026-11-27T12:00:00+00:00")
TASK_ARN = "arn:aws:ecs:eu-west-1:123456789012:task-definition/maintenance:7"
TOPIC = "arn:aws:sns:eu-west-1:123456789012:alerts"


def price_fixture(url):
    service = url.split("/")[-4]
    selected = {
        "AmazonECS": [("K4EXFQ5YFQCP98EN", "EU-Fargate-vCPU-Hours:perCPU", "hours", "0.04048"),
                      ("UP5ETC3QSW2QZGEY", "EU-Fargate-GB-Hours", "hours", "0.004445")],
        "AmazonRDS": [("S32D6FQC3879C222", "EU-RDS:GP3-Storage", "GB-Mo", "0.127"),
                      ("S4E2MMMTRUYQX32A", "EU-RDS:ChargedBackupUsage", "GB-Mo", "0.095"),
                      ("M4GMEFVGGWNKH9B6", "EU-InstanceUsage:db.t4g.micro", "Hrs", "0.017"),
                      ("YMX8EU2MHV3VCRA3", "EU-UnusedBox:db.t4g.micro", "Hrs", "0.001")],
    }[service]
    value = {"offerCode": service, "publicationDate": "2026-11-27T00:00:00Z", "products": {}, "terms": {"OnDemand": {}}}
    for sku, usage, unit, usd in selected:
        value["products"][sku] = {"attributes": {"usagetype": usage, "regionCode": "eu-west-1", "location": "EU (Ireland)",
            **({"databaseEngine": "PostgreSQL", "deploymentOption": "Single-AZ"} if service == "AmazonRDS" else {})}}
        if usage.endswith(":db.t4g.micro"):
            value["products"][sku]["productFamily"] = "Database Instance"
            value["products"][sku]["attributes"].update(instanceType="db.t4g.micro", operation="CreateDBInstance:0014",
                licenseModel="No license required", vcpu="2")
        value["terms"]["OnDemand"][sku] = {"offer": {"sku": sku, "effectiveDate": "2026-11-01T00:00:00Z",
            "priceDimensions": {"rate": {"unit": unit, "beginRange": "0", "endRange": "Inf", "appliesTo": [], "pricePerUnit": {"USD": usd}}}}}
    return json.dumps(value).encode()


def cost_provider(service, operation, **arguments):
    if (service, operation) == ("ecs", "describe-task-definition"):
        return {"taskDefinition": {"taskDefinitionArn": arguments["taskDefinition"], "cpu": "256", "memory": "512",
            "requiresCompatibilities": ["FARGATE"]}}
    if (service, operation) == ("rds", "describe-db-instances"):
        return {"DBInstances": [{"DBInstanceIdentifier": arguments["DBInstanceIdentifier"], "DBInstanceStatus": "available",
            "Engine": "postgres", "DBInstanceClass": "db.t4g.micro", "MultiAZ": False, "StorageType": "gp3",
            "AllocatedStorage": 20, "BackupRetentionPeriod": 7, "DbiResourceId": "db-CONTROLLED"}]}
    if (service, operation) == ("sns", "list-subscriptions-by-topic"):
        return {"Subscriptions": [{"TopicArn": TOPIC, "SubscriptionArn": TOPIC + ":00000000-0000-4000-8000-000000000001",
            "Protocol": "email", "Endpoint": "never-retained@example.invalid"}]}
    if (service, operation) == ("sns", "get-subscription-attributes"):
        return {"Attributes": {"TopicArn": TOPIC, "Protocol": "email", "PendingConfirmation": "false",
            "Endpoint": "never-retained@example.invalid"}}
    raise AssertionError((service, operation))


def initial_inputs():
    result = {"region": "eu-west-1", "image_bytes": 4 * 1024**3, "started_at": "2026-11-27T12:00:00Z",
        "maintenance": owner.maintenance_costs(cost_provider, reservations=[{
            "operation_id": "task-one", "task_definition_arn": TASK_ARN,
            "reserved_at": "2026-11-27T12:00:00Z", "request_sha256": "a" * 64}],
            started_at="2026-11-27T12:00:00Z", expires_at="2026-11-27T13:00:00Z"),
        "environment": owner.cost_environment(cost_provider, database="test-database", notification_topic_arn=TOPIC,
            price_fetch=price_fixture, now=PRICE_NOW)}
    result["resources"] = owner.resource_costs(reservations=[], environment=result["environment"],
        started_at=result["started_at"], expires_at=result["maintenance"]["expires_at"], now=PRICE_NOW)
    return result


class CostAdmissionTests(unittest.TestCase):
    def test_exact_regional_offers_retain_identity_and_do_not_leak_subscription(self):
        facts = owner.regional_price_facts(fetch=price_fixture, now=PRICE_NOW)
        self.assertEqual(facts["storage_gb_month"]["sku"], "S32D6FQC3879C222")
        self.assertEqual(facts["storage_gb_month"]["usd"], "0.127")
        self.assertEqual(facts["backup_gb_month"]["effective_at"], "2026-11-01T00:00:00Z")
        self.assertEqual(set(facts), {"fargate_vcpu_hour", "fargate_gb_hour", "storage_gb_month", "backup_gb_month", "rds_t4g_micro_instance_hour"})
        self.assertEqual(facts["rds_t4g_micro_instance_hour"]["sku"], "M4GMEFVGGWNKH9B6")
        self.assertEqual(facts["rds_t4g_micro_instance_hour"]["unit"], "Hrs")
        self.assertEqual(facts["rds_t4g_micro_instance_hour"]["usd"], "0.017", "unused reserved capacity is a different meter")
        environment = initial_inputs()["environment"]
        self.assertNotIn("never-retained", json.dumps(environment))
        self.assertEqual(environment["subscriptions"], {"email": 1, "https": 0})
        self.assertEqual(set(environment["prices"]), {"storage_gb_month", "backup_gb_month"}, "existing storage projection has no implicit restore charge")

    def test_restore_price_requires_exact_instance_product_and_hour_unit(self):
        changes = [
            ("usagetype", "EU-UnusedBox:db.t4g.micro"), ("instanceType", "db.t4g.small"),
            ("databaseEngine", "MySQL"), ("deploymentOption", "Multi-AZ"),
            ("regionCode", "us-east-1"), ("location", "US East (N. Virginia)"),
            ("operation", "CreateDBInstance:0002"), ("licenseModel", "Bring your own license"), ("vcpu", "4"),
        ]
        for field, replacement in changes:
            def fetch(url):
                value = json.loads(price_fixture(url))
                if value["offerCode"] == "AmazonRDS":
                    value["products"]["M4GMEFVGGWNKH9B6"]["attributes"][field] = replacement
                return json.dumps(value).encode()
            with self.subTest(field=field), self.assertRaisesRegex(owner.ProofFailure, "products-incomplete"):
                owner.regional_price_facts(fetch=fetch, now=PRICE_NOW)
        def wrong_unit(url):
            value = json.loads(price_fixture(url))
            if value["offerCode"] == "AmazonRDS":
                value["terms"]["OnDemand"]["M4GMEFVGGWNKH9B6"]["offer"]["priceDimensions"]["rate"]["unit"] = "GB-Mo"
            return json.dumps(value).encode()
        with self.assertRaisesRegex(owner.ProofFailure, "dimension-invalid"):
            owner.regional_price_facts(fetch=wrong_unit, now=PRICE_NOW)

    def test_unchanged_current_offer_does_not_need_a_recent_publication_date(self):
        def fetch(url):
            value = json.loads(price_fixture(url)); value["publicationDate"] = "2026-11-01T00:00:00Z"
            return json.dumps(value).encode()
        facts = owner.regional_price_facts(fetch=fetch, now=PRICE_NOW)
        self.assertEqual(facts["storage_gb_month"]["published_at"], "2026-11-01T00:00:00Z")
        self.assertEqual(facts["storage_gb_month"]["fetched_at"], PRICE_NOW.isoformat().replace("+00:00", "Z"))

    def test_changed_missing_future_or_wrong_region_prices_reject(self):
        changes = [
            lambda value: value.update(publicationDate="2026-12-01T00:00:00Z"),
            lambda value: value.update(products={}),
            lambda value: next(iter(value["products"].values()))["attributes"].update(location="US East (N. Virginia)"),
            lambda value: next(iter(next(iter(value["terms"]["OnDemand"].values())).values()))["priceDimensions"]["rate"].update(unit="GB"),
            lambda value: next(iter(next(iter(value["terms"]["OnDemand"].values())).values()))["priceDimensions"]["rate"]["pricePerUnit"].update(USD="0.8"),
        ]
        for change in changes:
            def fetch(url):
                value = json.loads(price_fixture(url)); change(value); return json.dumps(value).encode()
            with self.subTest(change=change), self.assertRaises(ValueError): owner.regional_price_facts(fetch=fetch, now=PRICE_NOW)
        with self.assertRaisesRegex(owner.ProofFailure, "source-unavailable"):
            owner.regional_price_facts(fetch=lambda url: b"not-json", now=PRICE_NOW)

    def test_tasks_reserve_real_sizes_full_window_and_reject_duplicates(self):
        value = initial_inputs()["maintenance"]["tasks"]["task-one"]
        self.assertEqual(value["reserved_seconds"], 3601)
        self.assertEqual(value["cpu_units"], 256)
        self.assertGreater(Decimal(value["reserved_usd"]), Decimal(".012"))
        row = {"operation_id": "task-one", "task_definition_arn": TASK_ARN,
            "reserved_at": "2026-11-27T12:00:00Z", "request_sha256": "a" * 64}
        arguments = {"reservations": [row], "started_at": row["reserved_at"], "expires_at": "2026-11-27T13:00:00Z"}
        def changed(service, operation, **kwargs):
            value = cost_provider(service, operation, **kwargs); value["taskDefinition"]["memory"] = "1024"; return value
        with self.assertRaisesRegex(owner.ProofFailure, "size-unpriced"): owner.maintenance_costs(changed, **arguments)
        arguments["reservations"].append(copy.deepcopy(row))
        with self.assertRaisesRegex(owner.ProofFailure, "reservation-invalid"): owner.maintenance_costs(cost_provider, **arguments)

    def test_native_missing_timestamp_is_explicit_full_window_not_fabricated_time(self):
        arguments = {"reservations": [{"operation_id": "unknown-native-task", "task_definition_arn": TASK_ARN,
            "reserved_at": None, "request_sha256": "a" * 64}], "started_at": "2026-11-27T12:00:00Z",
            "expires_at": "2026-11-27T13:00:00Z"}
        result = owner.maintenance_costs(cost_provider, **arguments)["tasks"]["unknown-native-task"]
        self.assertIsNone(result["reserved_at"])
        self.assertEqual(result["reservation_time_basis"], "budget-window-upper-bound")
        self.assertEqual(result["reserved_seconds"], 3601)
        self.assertEqual(result["reserved_usd"], initial_inputs()["maintenance"]["tasks"]["task-one"]["reserved_usd"])

    def test_native_utc_forms_price_equally_without_rewriting_original_custody(self):
        row = {"operation_id": "native-task", "task_definition_arn": TASK_ARN, "request_sha256": "a" * 64}
        compared = []
        for stamp in ("2026-11-27T12:00:00.123456Z", "2026-11-27T12:00:00.123456+00:00"):
            result = owner.maintenance_costs(cost_provider, reservations=[{**row, "reserved_at": stamp}],
                started_at="2026-11-27T12:00:00Z", expires_at="2026-11-27T13:00:00Z")["tasks"]["native-task"]
            self.assertEqual(result["reserved_at"], stamp)
            self.assertEqual(result["reservation_time_basis"], "original-reservation")
            compared.append((result["reserved_seconds"], result["reserved_usd"]))
        self.assertEqual(compared[0], compared[1])
        with self.assertRaises(owner.ADMISSION.AdmissionFailure):
            owner.ADMISSION.utc("2026-11-27T12:00:00+00:00")  # Global time rules are unchanged.
        for stamp in ("2026-11-27T12:00:00+01:00", "2026-11-27T12:00:00-01:00", "2026-11-27T12:00:00-00:00",
                "2026-11-27T12:00:00", "2026-11-27T12:00:00+0000", "2026-11-99T12:00:00+00:00", "private-canary", False):
            with self.subTest(stamp=stamp), self.assertRaisesRegex(owner.ProofFailure, "maintenance-reservation-time-invalid"):
                owner.maintenance_costs(cost_provider, reservations=[{**row, "reserved_at": stamp}],
                    started_at="2026-11-27T12:00:00Z", expires_at="2026-11-27T13:00:00Z")

    def test_maintenance_parsing_capacity_is_not_a_launch_or_spend_allowance(self):
        arguments = initial_inputs()
        rows = [{"operation_id": "task-" + str(index), "task_definition_arn": TASK_ARN,
            "reserved_at": "2026-11-27T12:00:00+00:00", "request_sha256": "a" * 64} for index in range(257)]
        for count in (132, 256):
            arguments["maintenance"] = owner.maintenance_costs(cost_provider, reservations=rows[:count],
                started_at=arguments["started_at"], expires_at="2026-11-27T13:00:00Z")
            projected = owner.initial_cost_projection(**arguments)
            self.assertEqual(len([key for key in projected["costs_usd"] if key.startswith("maintenance:")]), count)
            self.assertLessEqual(Decimal(projected["projected_usd"]), 10)
        with self.assertRaisesRegex(owner.ProofFailure, "maintenance-census-invalid"):
            owner.maintenance_costs(cost_provider, reservations=rows, started_at=arguments["started_at"], expires_at="2026-11-27T13:00:00Z")
        arguments["maintenance"]["tasks"]["task-256"] = copy.deepcopy(arguments["maintenance"]["tasks"]["task-0"])
        with self.assertRaisesRegex(owner.ProofFailure, "maintenance-census-invalid"):
            owner.initial_cost_projection(**arguments)

    def test_unpriced_environment_or_tampered_price_material_rejects(self):
        for key, value in (("MaxAllocatedStorage", 100), ("MultiAZ", True), ("DBInstanceClass", "db.t4g.small")):
            def changed(service, operation, **kwargs):
                result = cost_provider(service, operation, **kwargs)
                if service == "rds": result["DBInstances"][0][key] = value
                return result
            with self.subTest(key=key), self.assertRaisesRegex(owner.ProofFailure, "database-unpriced"):
                owner.cost_environment(changed, database="test-database", notification_topic_arn=TOPIC, price_fetch=price_fixture, now=PRICE_NOW)
        args = initial_inputs(); args["environment"]["prices"]["storage_gb_month"] = "0.001"
        with self.assertRaisesRegex(owner.ProofFailure, "environment-mismatch"): owner.initial_cost_projection(**args)

    def test_existing_reservations_cannot_be_refunded_or_extend_budget_clock(self):
        args = initial_inputs(); projection = owner.initial_cost_projection(**args)
        first = owner.admit_cost_effect(projection=projection, retained=[], operation_id="first",
            started_at="2026-11-27T12:00:00Z", now=PRICE_NOW)
        args["maintenance"]["tasks"] = {}
        second = owner.admit_cost_effect(projection=owner.initial_cost_projection(**args), retained=[first], operation_id="second",
            started_at="2026-11-27T12:00:00Z", now=PRICE_NOW)
        self.assertEqual(second["reserved_usd"], first["reserved_usd"])
        self.assertEqual(second["costs_usd"]["maintenance:task-one"], first["costs_usd"]["maintenance:task-one"])
        with self.assertRaisesRegex(owner.ProofFailure, "reservation-mismatch"):
            owner.admit_cost_effect(projection=projection, retained=[first, first], operation_id="third",
                started_at="2026-11-27T12:00:00Z", now=PRICE_NOW)
        with self.assertRaisesRegex(owner.ProofFailure, "budget-expired"):
            owner.admit_cost_effect(projection=projection, retained=[], operation_id="third",
                started_at="2026-11-27T12:00:00Z", now=datetime.fromisoformat("2026-11-27T13:00:00+00:00"))

    def test_prior_uncertain_tasks_still_consume_ceiling(self):
        args = initial_inputs(); projection = owner.initial_cost_projection(**args)
        first = owner.admit_cost_effect(projection=projection, retained=[], operation_id="first",
            started_at="2026-11-27T12:00:00Z", now=PRICE_NOW)
        first["costs_usd"]["maintenance:uncertain"] = "6.000000"
        first["reserved_usd"] = owner.dollars(sum(Decimal(value) for value in first["costs_usd"].values()))
        with self.assertRaisesRegex(owner.ProofFailure, "proof-budget-exceeded"):
            owner.admit_cost_effect(projection=projection, retained=[first], operation_id="second",
                started_at="2026-11-27T12:00:00Z", now=PRICE_NOW)


class ResourceCostTests(unittest.TestCase):
    def row(self, kind="clone", identity="kp-controlled"):
        return {"operation_id": identity, "request_sha256": "a" * 64, "reserved_at": "2026-11-27T12:00:00Z",
            "kind": kind, "source_resource_id": "db-CONTROLLED", "allocated_gib": 20,
            "instance_class": "db.t4g.micro" if kind == "clone" else None, "backup_days": 7 if kind == "clone" else 0,
            "log_exports": ["iam-db-auth-error", "postgresql"] if kind == "clone" else [], "absent_at": None}

    def projection(self, rows, *, now=PRICE_NOW, start="2026-11-27T12:00:00Z", expiry="2026-11-27T15:00:00Z"):
        return owner.resource_costs(reservations=rows, environment=initial_inputs()["environment"],
            started_at=start, expires_at=expiry, now=now)

    def test_exact_clone_and_snapshot_costs_keep_cpu_and_inherited_backups(self):
        result = self.projection([self.row(), self.row("snapshot", "es-snapshot")])
        clone, snapshot = result["resources"]["kp-controlled"], result["resources"]["es-snapshot"]
        self.assertEqual(clone["reserved_seconds"], 7200)
        self.assertEqual(clone["costs_usd"], {"instance": "0.034000", "cpu": "0.300000", "storage": "0.007560", "backup": "0.475000"})
        self.assertEqual(snapshot["reserved_seconds"], 10800)
        self.assertEqual(snapshot["costs_usd"], {"snapshot": "0.067858"})
        self.assertEqual(result["overdue_operation_ids"], [])
        changed = self.row(); changed["request_sha256"] = "b" * 64
        self.assertNotEqual(result["inputs_sha256"], self.projection([changed, self.row("snapshot", "es-snapshot")])["inputs_sha256"])

    def test_utc_dates_are_priced_conservatively_not_full_month_minimum(self):
        row = self.row("snapshot"); row["reserved_at"] = "2026-11-27T23:00:00Z"
        value = self.projection([row], now=owner.ADMISSION.utc(row["reserved_at"]), start=row["reserved_at"],
            expiry="2026-11-28T02:00:00Z")["resources"][row["operation_id"]]
        self.assertEqual(value["backup_billed_dates"], 2)
        self.assertEqual(value["costs_usd"]["snapshot"], "0.135715")
        self.assertLess(Decimal(value["reserved_usd"]), Decimal("1.9"))

    def test_unknown_clone_keeps_accruing_and_blocks_new_paid_work(self):
        args = initial_inputs()
        boundary = self.projection([self.row()], now=owner.ADMISSION.utc("2026-11-27T14:00:00Z"))
        self.assertEqual(boundary["overdue_operation_ids"], [])
        later = self.projection([self.row()], now=owner.ADMISSION.utc("2026-11-27T14:00:00.001Z"))
        self.assertEqual(later["overdue_operation_ids"], ["kp-controlled"])
        self.assertNotEqual(boundary["inputs_sha256"], later["inputs_sha256"])
        late = owner.ADMISSION.utc("2026-11-28T13:00:00Z")
        result = self.projection([self.row()], now=late)
        self.assertEqual(result["resources"]["kp-controlled"]["reserved_seconds"], 25 * 3600)
        self.assertEqual(result["overdue_operation_ids"], ["kp-controlled"])
        args["resources"] = owner.resource_costs(reservations=[self.row()], environment=args["environment"],
            started_at=args["started_at"], expires_at=args["maintenance"]["expires_at"], now=late)
        with self.assertRaisesRegex(owner.ProofFailure, "cleanup-overdue"):
            owner.initial_cost_projection(**args)

    def test_positive_absence_stops_growth_but_never_refunds_original_floor(self):
        for stamp, seconds in (("2026-11-27T12:30:00Z", 7200), ("2026-11-27T14:01:00Z", 7260)):
            row = self.row(); row["absent_at"] = stamp
            result = self.projection([row], now=owner.ADMISSION.utc("2026-11-28T13:00:00Z"))
            self.assertEqual(result["resources"][row["operation_id"]]["reserved_seconds"], seconds)
            self.assertEqual(result["overdue_operation_ids"], [])
        row = self.row("snapshot"); row["absent_at"] = "2026-11-27T12:30:00Z"
        result = self.projection([row], now=owner.ADMISSION.utc("2026-11-27T13:00:00Z"))
        self.assertEqual(result["resources"][row["operation_id"]]["reserved_seconds"], 10800)

    def test_invalid_native_projection_cannot_be_treated_as_free(self):
        for field, value in (("kind", {}), ("source_resource_id", "db-FOREIGN"), ("allocated_gib", True), ("allocated_gib", 21),
                ("backup_days", 1), ("instance_class", "db.t4g.small"), ("log_exports", ["unsupported"]),
                ("log_exports", ["postgresql", "postgresql"]), ("reserved_at", "2026-11-27T12:01:00Z"),
                ("absent_at", "2026-11-27T11:00:00Z"), ("request_sha256", "private-canary")):
            row = self.row(); row[field] = value
            with self.subTest(field=field), self.assertRaises(owner.ProofFailure) as failure:
                self.projection([row])
            self.assertNotIn("private-canary", str(failure.exception))
        with self.assertRaisesRegex(owner.ProofFailure, "reservation-invalid"):
            self.projection([self.row(), self.row()])
        with self.assertRaisesRegex(owner.ProofFailure, "census-invalid"):
            self.projection(None)

    def test_resource_price_and_replayed_arithmetic_must_match(self):
        args = initial_inputs()
        args["resources"]["resources"]["invented"] = {"reserved_usd": "0.00"}
        with self.assertRaisesRegex(owner.ProofFailure, "resource-cost-mismatch"):
            owner.initial_cost_projection(**args)
        for field, value in (("unit", "GB-Mo"), ("source", "https://untrusted.invalid"), ("fetched_at", "2026-11-28T12:00:00Z")):
            environment = initial_inputs()["environment"]
            environment["material"]["price_facts"]["rds_t4g_micro_instance_hour"][field] = value
            environment["evidence_sha256"] = owner.hashlib.sha256(owner.canonical(environment["material"])).hexdigest()
            with self.subTest(field=field), self.assertRaisesRegex(owner.ProofFailure, "price-invalid"):
                owner.resource_costs(reservations=[], environment=environment, started_at=args["started_at"],
                    expires_at=args["maintenance"]["expires_at"], now=PRICE_NOW)

    def test_source_cpu_uses_original_window_and_admission_rejects_clock_rebinding(self):
        args = initial_inputs(); result = owner.initial_cost_projection(**args)
        self.assertEqual(result["costs_usd"]["database_cpu"], "0.150000")
        with self.assertRaisesRegex(owner.ProofFailure, "cost-projection-invalid"):
            owner.admit_cost_effect(projection=result, retained=[], operation_id="later",
                started_at="2026-11-27T12:01:00Z", now=PRICE_NOW)

    def test_complete_original_census_not_entry_limit_decides_budget(self):
        args = initial_inputs(); start, expiry = "2026-11-27T23:00:00Z", "2026-11-28T02:00:00Z"
        args["started_at"] = start
        rows = [self.row(kind, kind + "-" + scope) for scope in ("core", "entity") for kind in ("clone", "snapshot")]
        for row in rows: row["reserved_at"] = start
        args["resources"] = owner.resource_costs(reservations=rows, environment=args["environment"], started_at=start,
            expires_at=expiry, now=owner.ADMISSION.utc(start))
        for count, permitted in ((20, True), (100, False), (132, False)):
            tasks = [{"operation_id": "task-" + str(index), "task_definition_arn": TASK_ARN,
                "reserved_at": start, "request_sha256": "a" * 64} for index in range(count)]
            args["maintenance"] = owner.maintenance_costs(cost_provider, reservations=tasks, started_at=start, expires_at=expiry)
            if permitted:
                projection = owner.initial_cost_projection(**args)
                self.assertLess(Decimal(projection["projected_usd"]), 10)
                self.assertEqual(projection["costs_usd"]["database_cpu"], "0.450000")
            else:
                with self.assertRaisesRegex(owner.ProofFailure, "proof-budget-exceeded"):
                    owner.initial_cost_projection(**args)

    def test_retained_resource_charge_cannot_be_refunded_by_later_empty_census(self):
        args = initial_inputs()
        args["resources"] = owner.resource_costs(reservations=[self.row()], environment=args["environment"],
            started_at=args["started_at"], expires_at=args["maintenance"]["expires_at"], now=PRICE_NOW)
        first = owner.admit_cost_effect(projection=owner.initial_cost_projection(**args), retained=[], operation_id="first",
            started_at=args["started_at"], now=PRICE_NOW)
        args = initial_inputs()
        second = owner.admit_cost_effect(projection=owner.initial_cost_projection(**args), retained=[first], operation_id="second",
            started_at=args["started_at"], now=PRICE_NOW)
        self.assertEqual(second["costs_usd"]["resource:kp-controlled"], first["costs_usd"]["resource:kp-controlled"])


def monthly_observation_fixture(*, billed_duration_ms=50):
    # Controlled affordable boundary, not a claim about actual AWS performance.
    # Separate 250ms/1250ms fixtures must reject under the unchanged $25 limit.
    components, functions, logs = {}, {}, {}
    for scope in ("core-server-persistence", "entity-smoke"):
        components[scope] = {}
        for purpose in ("dispatch", "worker"):
            expected, events, _ = runtime_fixture(purpose)
            expected = json.loads(json.dumps(expected).replace("one-", scope + "-").replace("/one/", "/" + scope + "/"))
            request = "00000000-0000-4000-8000-" + str(len(functions) + 1).zfill(12)
            events = json.loads(json.dumps(events).replace("one-", scope + "-").replace("ee860df1-9d61-45f3-b3ee-e64da98115da", request))
            for event in events:
                record = json.loads(event["message"])
                if record.get("type") == "platform.report":
                    record["record"]["metrics"]["billedDurationMs"] = billed_duration_ms
                    event["message"] = json.dumps(record)
            for event in events: event["eventId"] = scope + purpose + event["eventId"]
            if purpose == "dispatch":
                idle = json.loads(json.dumps(events).replace(request, "00000000-0000-4000-8000-" + str(len(functions) + 10).zfill(12)))
                for event in idle: event["eventId"] += "-idle"
                record = json.loads(idle[1]["message"])
                record["fields"]["scheduling_runtime"]["result"] = {"delivery": {"inspected": 0, "deliveryCreated": 0,
                    "deliveryAlreadyCreated": 0, "notDue": 0}, "relayAttempts": 0, "published": 0, "stopReason": "idle"}
                idle[1]["message"] = json.dumps(record)
                events += idle
            components[scope][purpose] = expected
            functions[expected["version_arn"]] = {"Code": {"ResolvedImageUri": expected["image_uri"]}, "Configuration": {
                "FunctionArn": expected["version_arn"], "Version": "2", "State": "Active", "MemorySize": 512, "Timeout": 60,
                "Environment": {"Variables": {"PLATFORM_SOURCE_COMMIT_SHA": expected["source_revision"]}},
                "LoggingConfig": {"LogGroup": expected["log_group"], "LogFormat": "JSON"}}}
            logs.setdefault(expected["log_group"], []).extend(events)
    def provider(service, operation, **arguments):
        if service == "lambda": return copy.deepcopy(functions[arguments["FunctionName"]])
        if service == "logs": return {"events": copy.deepcopy(logs[arguments["logGroupName"]])}
        if service == "ecr": return {"imageDetails": [{"registryId": arguments["registryId"], "repositoryName": arguments["repositoryName"],
            "imageDigest": arguments["imageIds"][0]["imageDigest"], "imageSizeInBytes": 100 * 1024**2}]}
        if service == "ec2": return {"VpcEndpoints": [{"VpcEndpointId": "vpce-12345678", "VpcId": "vpc-12345678",
            "State": "available", "VpcEndpointType": "Interface", "ServiceName": "com.amazonaws.eu-west-1.sqs"}]}
        if (service, operation) == ("cloudwatch", "describe-alarms"):
            periods = {"dispatch-silence": 3, "dispatch-errors": 1, "queue-age": 2, "dead-letter": 1}
            return {"MetricAlarms": [{"AlarmName": name, "Period": 60, "EvaluationPeriods": periods[name.split("-scheduling-")[1]],
                "AlarmActions": [TOPIC], "OKActions": [TOPIC]} for name in arguments["AlarmNames"]]}
        if service == "cloudwatch":
            beginning, ending = (datetime.fromisoformat(arguments[key].replace("Z", "+00:00")) for key in ("StartTime", "EndTime"))
            values = {"CPUCreditUsage": .01, "FreeStorageSpace": 10 * 1024**3, "CPUCreditBalance": 100, "CPUUtilization": 2}
            return {"Datapoints": [{"Timestamp": (beginning + timedelta(seconds=300 * index)).isoformat(),
                arguments["Statistics"][0]: values.get(arguments["MetricName"], 100)}
                for index in range(int((ending - beginning).total_seconds()) // 300)]}
        return cost_provider(service, operation, **arguments)
    def prices(url):
        value = json.loads(price_fixture(url)); value["publicationDate"] = "2026-11-26T00:00:00Z"; return json.dumps(value).encode()
    return provider, {"components": components, "database": "test-database", "notification_topic_arn": TOPIC,
        "endpoint_id": "vpce-12345678", "started_at": "2026-11-26T12:00:00Z", "ended_at": "2026-11-26T12:15:00Z",
        "price_fetch": prices, "now": datetime.fromisoformat("2026-11-26T12:16:00+00:00")}


class ObservedCostTests(unittest.TestCase):
    def validate(self, packet, arguments, **overrides):
        selected = {key: arguments[key] for key in ("components", "database", "notification_topic_arn", "endpoint_id")}
        return owner.validate_monthly_cost_observation(packet, **{**selected, **overrides})

    def test_actual_inputs_forecast_declared_workload_with_sensitivity_and_runway(self):
        provider, arguments = monthly_observation_fixture()
        with patch("subprocess.run", side_effect=AssertionError("cost observation launched a local command")):
            result = owner.observed_monthly_cost_projection(provider, **arguments)
        self.assertEqual(result["combined_jobs"], 100000)
        self.assertGreater(Decimal(result["projected_usd"]), 16)
        self.assertTrue(result["projection_complete"])
        self.assertTrue(result["within_ceiling"])
        self.assertTrue(result["capacity_supported"])
        self.assertEqual(len(result["observed_inputs"]["runtime_windows"]), 4)
        self.assertLess(Decimal(result["expected"]["costs_usd"]["database_storage_and_backup"]), 1)
        self.assertEqual(result["expected"]["costs_usd"]["recovery_snapshots"], "3.800000")
        self.assertEqual(result["assumptions"]["retained_recovery_snapshots"], 2)
        self.assertGreater(Decimal(result["sensitivity"]["projected_usd"]), Decimal(result["projected_usd"]))
        self.assertEqual(result["expected"]["notification_publications"], 16008)
        self.assertEqual(result["expected"]["costs_usd"]["database_cpu"], "0.000000")
        self.assertFalse(result["free_tier_assumed"])
        self.assertFalse(result["assumptions"]["retained_metadata_cleanup"])
        self.assertNotIn("never-retained", json.dumps(result))
        self.assertEqual(self.validate(result, arguments), result)

    def test_retained_projection_recomputes_amounts_and_checks_original_source(self):
        provider, arguments = monthly_observation_fixture()
        result = owner.observed_monthly_cost_projection(provider, **arguments)
        for key, value in (("projected_usd", "0.00"), ("within_ceiling", False)):
            altered = copy.deepcopy(result); altered[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(owner.ProofFailure, "projection-mismatch"):
                self.validate(altered, arguments)
        foreign = copy.deepcopy(arguments["components"]); foreign["entity-smoke"]["worker"]["source_revision"] = "f" * 40
        with self.assertRaisesRegex(owner.ProofFailure, "custody-mismatch"):
            self.validate(result, arguments, components=foreign)
        for key, value in (("database", "foreign-db"), ("notification_topic_arn", "foreign-topic"), ("endpoint_id", "foreign-endpoint")):
            with self.subTest(key=key), self.assertRaisesRegex(owner.ProofFailure, "environment-custody-mismatch"):
                self.validate(result, arguments, **{key: value})

    def test_retained_snapshots_can_make_slower_actual_samples_unaffordable(self):
        for duration in (250, 1250):
            provider, arguments = monthly_observation_fixture(billed_duration_ms=duration)
            result = owner.observed_monthly_cost_projection(provider, **arguments)
            self.assertEqual(result["expected"]["costs_usd"]["recovery_snapshots"], "3.800000")
            self.assertGreater(Decimal(result["expected"]["projected_usd"]), 25)
            self.assertFalse(result["within_ceiling"])
            with self.subTest(duration=duration), self.assertRaisesRegex(owner.ProofFailure, "cost-or-capacity-exceeded"):
                self.validate(result, arguments)

    def test_cpu_increment_is_not_baseline_and_insufficient_storage_blocks_acceptance(self):
        provider, arguments = monthly_observation_fixture()
        def loaded(service, operation, **kwargs):
            value = provider(service, operation, **kwargs)
            if service == "cloudwatch" and operation == "get-metric-statistics":
                if kwargs["MetricName"] == "CPUCreditUsage" and kwargs["StartTime"] == arguments["started_at"]:
                    for row in value["Datapoints"]: row["Sum"] = 1
                if kwargs["MetricName"] == "FreeStorageSpace":
                    for row in value["Datapoints"]: row["Minimum"] = 2 * 1024**3
            return value
        result = owner.observed_monthly_cost_projection(loaded, **arguments)
        self.assertGreater(Decimal(result["expected"]["costs_usd"]["database_cpu"]), 0)
        self.assertFalse(result["capacity_supported"])
        with self.assertRaisesRegex(owner.ProofFailure, "cost-or-capacity-exceeded"):
            self.validate(result, arguments)

    def test_actual_alarm_policy_and_subscription_policy_cannot_be_assumed(self):
        for mode in ("alarm", "subscription", "sparse-baseline"):
            provider, arguments = monthly_observation_fixture()
            def changed(service, operation, **kwargs):
                value = provider(service, operation, **kwargs)
                if mode == "alarm" and operation == "describe-alarms": value["MetricAlarms"][0]["AlarmActions"] = []
                if mode == "subscription" and operation == "get-subscription-attributes": value["Attributes"]["RedrivePolicy"] = "unpriced"
                if mode == "sparse-baseline" and operation == "get-metric-statistics" and len(value["Datapoints"]) == 288: value["Datapoints"].pop()
                return value
            with self.subTest(mode=mode), self.assertRaises(owner.ProofFailure): owner.observed_monthly_cost_projection(changed, **arguments)

    def test_missing_metrics_mismatched_image_or_foreign_endpoint_block(self):
        for selected in ("cloudwatch", "ecr", "ec2"):
            provider, arguments = monthly_observation_fixture()
            def broken(service, operation, **kwargs):
                value = provider(service, operation, **kwargs)
                if service == selected:
                    if selected == "cloudwatch": value["Datapoints"] = []
                    if selected == "ecr": value["imageDetails"][0]["imageDigest"] = "sha256:" + "f" * 64
                    if selected == "ec2": value["VpcEndpoints"][0]["ServiceName"] = "com.amazonaws.eu-west-1.s3"
                return value
            with self.subTest(selected=selected), self.assertRaises(ValueError): owner.observed_monthly_cost_projection(broken, **arguments)

    def test_actual_runtime_report_cannot_be_replaced_by_written_cost_sample(self):
        provider, arguments = monthly_observation_fixture()
        def broken(service, operation, **kwargs):
            value = provider(service, operation, **kwargs)
            if service == "logs": value["events"] = [row for row in value["events"] if "platform.report" not in row["message"]]
            return value
        with self.assertRaisesRegex(owner.ProofFailure, "system-report-missing"):
            owner.observed_monthly_cost_projection(broken, **arguments)


class CostEvidenceTests(unittest.TestCase):
    def setUp(self):
        from contextlib import ExitStack
        self.patches = ExitStack(); self.addCleanup(self.patches.close)
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.control = owner.control_owner()
        self.store = self.control.Store(Path(self.directory.name))
        self.binding = {"target": "kanbien-core-platform", "scope": "core-server-persistence"}
        provider, arguments = monthly_observation_fixture()
        original = owner.observed_monthly_cost_projection(provider, **arguments)
        material = copy.deepcopy(original["observed_inputs"])
        for scope in arguments["components"]:
            old, new = "/aws/lambda/" + scope + "/scheduling", "/aws/lambda/kanbien-core-platform/" + scope + "/scheduling"
            material = json.loads(json.dumps(material).replace(old, new))
            arguments["components"] = json.loads(json.dumps(arguments["components"]).replace(old, new))
        self.projection = owner.project_observed_monthly_cost(material)
        self.arguments = {key: arguments[key] for key in ("components", "database", "notification_topic_arn", "endpoint_id", "started_at", "ended_at")}
        self.selection = {key: value for key, value in self.arguments.items() if key not in {"started_at", "ended_at"}}
        def observed(service, operation, **kwargs):
            result = provider(service, operation, **kwargs)
            for scope in arguments["components"]:
                result = json.loads(json.dumps(result).replace("/aws/lambda/" + scope + "/scheduling", "/aws/lambda/kanbien-core-platform/" + scope + "/scheduling"))
            return result
        self.provider = observed
        self.phases = {}
        for ordinal, key in enumerate(("network-create", "core-server-persistence", "entity-smoke")):
            network = key == "network-create"
            stamp = "2026-11-26T11:" + str(50 + ordinal) + ":00Z"
            parameters = {"VpcId": "vpc-12345678", "PrivateSubnetIds": "subnet-one,subnet-two"}
            resources = {"SchedulingSqsEndpoint": {"ResourceType": "AWS::EC2::VPCEndpoint", "PhysicalResourceId": "vpce-12345678"},
                "SchedulingEndpointSecurityGroup": {"ResourceType": "AWS::EC2::SecurityGroup", "PhysicalResourceId": "sg-12345678"}}
            if not network:
                parameters.update(Scope=key, SourceRevision="a" * 40, AlarmTopicArn=TOPIC, EndpointSecurityGroupId="sg-12345678",
                    DatabaseResourceId="db-CONTROLLED", TickEnabled="false", WorkerEnabled="false", DenyDispatcherSend="false")
                resources = {}
                resources["RuntimeLogs"] = {"ResourceType": "AWS::Logs::LogGroup",
                    "PhysicalResourceId": self.arguments["components"][key]["dispatch"]["log_group"]}
                for purpose, expected in self.arguments["components"][key].items():
                    parameters[purpose.title() + "ImageUri"] = expected["image_uri"]
                    resources[purpose.title() + "Version"] = {"ResourceType": "AWS::Lambda::Version", "PhysicalResourceId": expected["version_arn"]}
            intent = {"schema": "deploy/scheduling-phase-intent/v1", "target": self.binding["target"], "scope": "shared" if network else key,
                "phase": "network-create" if network else "scope-create-disabled", "stack": "owned-" + key, "mode": "CREATE", "created_at": stamp,
                "template": {"Resources": {name: {"Type": value["ResourceType"]} for name, value in resources.items()}}, "parameters": parameters,
                "parameter_inputs": [{"ParameterKey": name, "ParameterValue": value} for name, value in sorted(parameters.items())], "before": None,
                "predecessor_sha256": None if network else self.control.digest(self.phases["network-create"]["intent"]), "source_revision": "a" * 40,
                "network_before": {} if network else None,
                "maintenance_selection": None if network else {"qualified_path": "/controlled/core-package.json"} if key == "core-server-persistence" else
                    {"receipt_path": "/controlled/entity-package.json", "proof_label": "entity-smoke-" + "a" * 24, "expected_predecessor": None}}
            request = self.control.phase_request(intent)
            reservations = {phase: {"schema": self.control.Store.schema, "phase": phase, "operation_id": "scheduling-" + str(ordinal * 2 + index + 1).zfill(32),
                "request": request, "request_sha256": self.control.digest(request), "reserved_at": stamp} for index, phase in enumerate(("prepare", "execute"))}
            state = {"stack_id": "owned-stack-" + key, "resources": resources}
            self.phases[key] = {"schema": "deploy/scheduling-phase-evidence/v1", "intent": intent, "preparation": reservations["prepare"], "execution": reservations["execute"],
                "terminal": {"EventId": key, "StackId": state["stack_id"], "LogicalResourceId": intent["stack"], "PhysicalResourceId": state["stack_id"],
                    "ResourceType": "AWS::CloudFormation::Stack", "ResourceStatus": "CREATE_COMPLETE", "ClientRequestToken": reservations["execute"]["operation_id"], "Timestamp": stamp},
                "readback": state, "captured_at": stamp}
        self.intent = {"schema": "deploy/scheduling-cost-intent/v1", "target": self.binding["target"], "source_revision": "a" * 40,
            "database": self.arguments["database"], "notification_topic_arn": TOPIC, "started_at": "2026-11-26T11:00:00Z", "expires_at": "2026-11-26T13:00:00Z",
            "scopes": {scope: {"receipt_files": {}, "packages": {purpose: {"source_revision": "a" * 40, "image_digest": expected["image_uri"].split("@")[-1]}
                for purpose, expected in pair.items()}} for scope, pair in self.arguments["components"].items()}}
        self.recovery = {"schema": "deploy/scheduling-retained-recovery-resources/v1", "intent_sha256": self.control.digest(self.intent),
            "snapshots": {scope: {"operation_id": prefix + "1" * 32, "request_sha256": str(index + 1) * 64,
                "snapshot": "owned-" + scope, "source_resource_id": "db-CONTROLLED", "allocated_gib": 20}
                for index, (scope, prefix) in enumerate((("core-server-persistence", "kp-"), ("entity-smoke", "es-")))},
            "clones": [{"operation_id": prefix + "2" * 32, "request_sha256": str(index + 3) * 64,
                "absent_at": "2026-11-26T12:10:00Z"} for index, prefix in enumerate(("es-", "kp-"))]}
        class Frozen(datetime):
            @classmethod
            def now(cls, tz=None): return datetime(2026, 11, 26, 12, 16, tzinfo=timezone.utc)
        self.patches.enter_context(patch.object(owner, "datetime", Frozen))
        self.patches.enter_context(patch.object(self.control, "cost_intent", side_effect=lambda *_: copy.deepcopy(self.intent)))
        self.patches.enter_context(patch.object(self.control, "load_binding", side_effect=lambda target, scope: {"target": target, "scope": scope}))
        self.patches.enter_context(patch.object(self.control, "capture_phase", side_effect=lambda _p, _s, binding, phase: copy.deepcopy(self.phases[phase if phase == "network-create" else binding["scope"]])))
        self.authenticate_phase = self.patches.enter_context(patch.object(self.control, "authenticate_phase_evidence", return_value={}))
        self.source = self.patches.enter_context(patch.object(owner, "cost_capture_current_source"))
        self.observe = self.patches.enter_context(patch.object(owner, "observed_monthly_cost_projection", return_value=copy.deepcopy(self.projection)))
        self.recovery_read = self.patches.enter_context(patch.object(self.control, "recovery_acceptance_resources", side_effect=lambda *_: copy.deepcopy(self.recovery)))

    def collect(self, **overrides):
        return owner.collect_cost_evidence(self.provider, self.store, self.binding, **{**self.arguments, **overrides})

    def test_capture_reuses_original_without_price_metric_recapture(self):
        first = self.collect()
        self.assertEqual(self.collect(), first)
        self.assertEqual(self.observe.call_count, 1)
        self.assertEqual(first["recovery_resources"], self.recovery)
        self.assertEqual(owner.authenticate_cost_evidence(self.provider, self.store, self.binding, first, **self.selection), first)
        with self.assertRaisesRegex(owner.ProofFailure, "window-changed"):
            self.collect(started_at="2026-11-26T12:05:00Z")
        self.assertEqual(owner.read_cost_evidence(owner.cost_evidence_path(self.store, self.binding)), first)

    def test_historical_replay_never_reads_current_source_store_or_provider(self):
        packet = self.collect()
        forbidden = AssertionError("historical replay performed a live read")
        with patch.object(owner, "read_cost_evidence", side_effect=forbidden), \
                patch.object(owner, "cost_capture_current_source", side_effect=forbidden), patch.object(self.control, "authenticate_phase_evidence", side_effect=forbidden), \
                patch.object(self.control, "recovery_acceptance_resources", side_effect=forbidden):
            self.assertEqual(owner.authenticate_cost_evidence(None, None, self.binding, packet, historical=True, **self.selection), packet)
        changed = copy.deepcopy(packet); changed["components"]["entity-smoke"]["worker"]["image_uri"] += "foreign"
        with self.assertRaises((ValueError, self.control.Failure)):
            owner.authenticate_cost_evidence(None, None, self.binding, changed, historical=True, **self.selection)

    def test_live_rejects_replaced_database_changed_source_and_expired_window(self):
        packet = self.collect()
        with patch.object(owner, "cost_capture_current_source", side_effect=owner.ProofFailure("cost-capture-source-changed")):
            with self.assertRaisesRegex(owner.ProofFailure, "source-changed"):
                owner.authenticate_cost_evidence(self.provider, self.store, self.binding, packet, **self.selection)
        def changed_database(service, operation, **kwargs):
            value = self.provider(service, operation, **kwargs)
            if service == "rds": value["DBInstances"][0]["DbiResourceId"] = "db-REPLACED"
            return value
        with self.assertRaisesRegex(owner.ProofFailure, "database-changed"):
            owner.authenticate_cost_evidence(changed_database, self.store, self.binding, packet, **self.selection)
        class Later(datetime):
            @classmethod
            def now(cls, tz=None): return datetime(2026, 11, 26, 13, 16, tzinfo=timezone.utc)
        with patch.object(owner, "datetime", Later), self.assertRaisesRegex(owner.ProofFailure, "stale"):
            owner.authenticate_cost_evidence(self.provider, self.store, self.binding, packet, **self.selection)
        self.assertEqual(self.observe.call_count, 1)

    def test_capture_mutex_is_distinct_and_does_not_remeasure_when_busy(self):
        path = owner.cost_evidence_path(self.store, self.binding)
        with self.control.JOURNAL.locked(path, path.with_suffix(".lock"), b"scheduling-monthly-cost-capture/v1\n", owner.read_cost_evidence):
            with self.assertRaisesRegex(owner.ProofFailure, "busy-or-metadata-invalid"): self.collect()
            budget = self.control.cost_path(self.store, self.binding["target"])
            with self.control.JOURNAL.locked(budget, budget.with_suffix(".lock"), b"scheduling-cost-intent/v1\n", owner.read_cost_evidence): pass
        self.observe.assert_not_called()

    def test_original_peer_phase_cannot_select_an_unbudgeted_image(self):
        packet = self.collect()
        changed = copy.deepcopy(packet)
        changed["intent"]["scopes"]["entity-smoke"]["packages"]["worker"]["image_digest"] = "sha256:" + "f" * 64
        changed["intent_sha256"] = self.control.digest(changed["intent"])
        with self.assertRaisesRegex(owner.ProofFailure, "package-mismatch"):
            owner.authenticate_cost_evidence(None, None, self.binding, changed, historical=True, **self.selection)

    def test_recovery_census_required_before_measurement_and_stable_before_retention(self):
        self.recovery_read.side_effect = self.control.Failure("recovery-clone-cleanup-required")
        with self.assertRaisesRegex(self.control.Failure, "clone-cleanup-required"): self.collect()
        self.observe.assert_not_called()
        changed = copy.deepcopy(self.recovery)
        changed["snapshots"]["entity-smoke"]["snapshot"] += "-changed"
        self.recovery_read.side_effect = [copy.deepcopy(self.recovery), changed]
        with self.assertRaisesRegex(owner.ProofFailure, "recovery-resources-changed"): self.collect()
        self.assertFalse(owner.cost_evidence_path(self.store, self.binding).exists())

    def test_live_recovery_census_cannot_change_or_remove_the_original_snapshots(self):
        packet = self.collect()
        self.recovery["snapshots"]["entity-smoke"]["snapshot"] += "-replacement"
        with self.assertRaisesRegex(owner.ProofFailure, "recovery-resources-changed"):
            owner.authenticate_cost_evidence(self.provider, self.store, self.binding, packet, **self.selection)
        self.assertEqual(owner.read_cost_evidence(owner.cost_evidence_path(self.store, self.binding)), packet)
        self.assertEqual(self.observe.call_count, 1)

    def test_historical_recovery_resources_reject_unpriced_foreign_or_incomplete_census(self):
        packet = self.collect()
        for change in (
            lambda r: r.update(intent_sha256="f" * 64),
            lambda r: r["snapshots"].pop("entity-smoke"),
            lambda r: r["snapshots"].update(extra=copy.deepcopy(r["snapshots"]["entity-smoke"])),
            lambda r: r["snapshots"]["entity-smoke"].update(source_resource_id="db-FOREIGN"),
            lambda r: r["snapshots"]["entity-smoke"].update(allocated_gib=40),
            lambda r: r["snapshots"]["entity-smoke"].update(snapshot=r["snapshots"]["core-server-persistence"]["snapshot"]),
            lambda r: r["clones"].pop(),
            lambda r: r["clones"][0].update(absent_at=None),
            lambda r: r["clones"][0].update(absent_at="2026-11-26T12:17:00Z"),
            lambda r: r["clones"][0].update(operation_id=r["snapshots"]["entity-smoke"]["operation_id"]),
        ):
            changed = copy.deepcopy(packet); change(changed["recovery_resources"])
            with self.subTest(resources=changed["recovery_resources"]), self.assertRaises(ValueError):
                owner.authenticate_cost_evidence(None, None, self.binding, changed, historical=True, **self.selection)

    def test_invalid_window_is_rejected_before_provider_capture(self):
        with self.assertRaisesRegex(owner.ProofFailure, "observation-window-invalid"):
            self.collect(started_at="2026-11-26T12:05:00Z")
        self.observe.assert_not_called()
        self.authenticate_phase.assert_not_called(); self.source.assert_not_called()

    def test_actual_log_group_must_match_selected_runtime(self):
        self.phases["entity-smoke"]["readback"]["resources"]["RuntimeLogs"]["PhysicalResourceId"] += "-different"
        with self.assertRaisesRegex(owner.ProofFailure, "runtime-mismatch"): self.collect()
        self.observe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
