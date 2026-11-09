#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.connected-restore-route
#   version: 2
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Extend the shared completed-credential/snapshot fixture through actual owned clone, restricted reader and cleanup consumers with controlled provider protocols, not AWS proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.credential-route
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/credential-route-test.py
import copy
import hashlib
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_RESTORE_ROUTE_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def run(case, snapshot_args, S, T, canary):
    directory = Path(__file__).parent
    D = module("entity_smoke_connected_restore", directory / "restore-route.py")
    Y = module("entity_smoke_connected_restore_reader", directory / "restore-reader-route.py")
    F = module("entity_smoke_connected_clone_protocol", directory / "restore-control-test.py")
    BF = module("entity_smoke_connected_clone_binding_protocol", directory / "task-binding-test.py")
    D.S, D.TASK, D.C = S, T, T.C
    Y.D, Y.TASK, Y.C = D, T, T.C
    C = T.C
    original_transport = case.transport
    original_call = original_transport.__call__
    root_args = SimpleNamespace(**{**vars(snapshot_args), "mode": "plan", "phase": "deploy", "approved_plan": None})
    value = D.source(root_args, original_transport)
    F.BINDING = value["restore_binding"]
    F.STACK, F.CHANGE, F.DATABASE = D.RESTORE.names(F.BINDING)
    F.PARAMETERS = copy.deepcopy(value["restore_parameters"])
    F.STACK_ARN = "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + F.STACK + "/11111111-2222-3333-4444-555555555555"
    F.CHANGE_ARN = "arn:aws:cloudformation:eu-west-1:337159794548:changeSet/" + F.CHANGE + "/11111111-2222-3333-4444-555555555555"
    F.PHYSICAL["RestoredDatabase"] = F.DATABASE
    F.PHYSICAL["RestoreDatabaseSecurityGroup"] = "sg-" + "a" * 17
    F.PHYSICAL["RestoreReaderSecurityGroup"] = "sg-" + "b" * 17
    assert not {F.PHYSICAL["RestoreDatabaseSecurityGroup"], F.PHYSICAL["RestoreReaderSecurityGroup"]} & {value["parameters"]["EndpointSecurityGroupId"], value["parameters"]["DatabaseSecurityGroupId"]}
    clone = F.Provider()
    resources = {name: {"type": kind, "physical_id": F.PHYSICAL[name]} for name, kind in D.RESTORE.RESOURCE_TYPES.items()}
    db = {"DbiResourceId": "db-RESTOREDABCDEFGHIJKLMNOP", "Endpoint": {"Address": "restored-provider-canary.internal"}}
    view = D.BINDING.expanded(D.RESTORE.source()[1], db)
    inputs = {**F.PARAMETERS, "PrivateSubnetIds": value["parameters"]["PrivateSubnetIds"], "DatabaseSecurityGroupId": F.PHYSICAL["RestoreDatabaseSecurityGroup"]}
    task_definition = T.BINDING.expected_task("restore-reader", inputs, resources, view, prefix="RestoreReader")
    task_definition.update(taskDefinitionArn=F.DEFINITION, revision=1, status="ACTIVE", compatibilities=["FARGATE"])
    roles, policies, groups = {}, {}, {}
    for name, resource in view["Resources"].items():
        if resource["Type"] == "AWS::IAM::Role":
            props = T.BINDING.resolve(resource["Properties"], inputs, resources, "restore-reader")
            role = F.PHYSICAL[name]
            roles[role] = {"RoleName": role, "Arn": "arn:aws:iam::337159794548:role/" + role, "Path": "/", "AssumeRolePolicyDocument": props["AssumeRolePolicyDocument"]}
            policies[role] = {row["PolicyName"]: row["PolicyDocument"] for row in props["Policies"]}
        if resource["Type"] == "AWS::EC2::SecurityGroup":
            props = T.BINDING.resolve(resource["Properties"], inputs, resources, "restore-reader")
            group = F.PHYSICAL[name]
            groups[group] = {"GroupId": group, "VpcId": inputs["VpcId"], "OwnerId": C.ALIGN.ACCOUNT, "IpPermissions": [], "IpPermissionsEgress": [BF.permission(row) for row in props["SecurityGroupEgress"]]}
    endpoint = original_transport.bindings["administration"].groups[inputs["EndpointSecurityGroupId"]]
    endpoint_before = copy.deepcopy(endpoint["IpPermissions"])
    reader_group = F.PHYSICAL["RestoreReaderSecurityGroup"]
    endpoint_rule = BF.permission({"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "DestinationSecurityGroupId": reader_group})
    groups[F.PHYSICAL["RestoreDatabaseSecurityGroup"]]["IpPermissions"] = [BF.permission({"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "DestinationSecurityGroupId": reader_group})]

    class Transport:
        def __call__(self, service, operation, **parameters):
            clone_stack = parameters.get("StackName") in {F.STACK, F.STACK_ARN}
            try:
                if clone_stack and operation in {"describe-stacks", "create-change-set", "describe-change-set", "get-template", "execute-change-set", "describe-stack-events", "list-stack-resources", "delete-stack"}:
                    try: return clone(service, operation, **parameters)
                    finally:
                        # Lost transport responses do not undo remote effects.
                        if operation == "execute-change-set" and clone.state == "CREATE_COMPLETE": endpoint["IpPermissions"] = endpoint_before + [copy.deepcopy(endpoint_rule)]
                        if operation == "delete-stack" and clone.deleted: endpoint["IpPermissions"] = copy.deepcopy(endpoint_before)
                if operation == "describe-db-instances" and parameters.get("DBInstanceIdentifier") == F.DATABASE:
                    result = clone(service, operation, **parameters)
                    result["DBInstances"][0].update(Endpoint={"Address": db["Endpoint"]["Address"], "Port": 5432},
                        DBSubnetGroup={"DBSubnetGroupName": inputs["DatabaseSubnetGroupName"], "VpcId": inputs["VpcId"], "SubnetGroupStatus": "Complete"},
                        VpcSecurityGroups=[{"VpcSecurityGroupId": F.PHYSICAL["RestoreDatabaseSecurityGroup"], "Status": "active"}])
                    return result
                if operation == "list-tags-for-resource" and parameters.get("ResourceName") == "arn:aws:rds:eu-west-1:337159794548:db:" + F.DATABASE: return clone(service, operation, **parameters)
                if operation == "describe-task-definition" and parameters.get("taskDefinition") == F.DEFINITION:
                    if clone.deleted: return clone(service, operation, **parameters)
                    assert clone.state == "CREATE_COMPLETE"
                    return {"taskDefinition": copy.deepcopy(task_definition)}
                if operation == "describe-security-groups" and set(parameters["GroupIds"]) <= set(groups):
                    if clone.deleted: raise C.RESOURCE.ResourceMissing()
                    return {"SecurityGroups": [copy.deepcopy(groups[name]) for name in parameters["GroupIds"]]}
                name = parameters.get("RoleName")
                if name in roles:
                    if clone.deleted: raise C.RESOURCE.ResourceMissing()
                    assert clone.state == "CREATE_COMPLETE"
                    if operation == "get-role": return {"Role": copy.deepcopy(roles[name])}
                    if operation == "list-attached-role-policies": return {"AttachedPolicies": [], "IsTruncated": False}
                    if operation == "list-role-policies": return {"PolicyNames": list(policies[name]), "IsTruncated": False}
                    if operation == "get-role-policy": return {"RoleName": name, "PolicyName": parameters["PolicyName"], "PolicyDocument": copy.deepcopy(policies[name][parameters["PolicyName"]])}
                return original_call(service, operation, **parameters)
            except F.R.ResourceMissing: raise C.RESOURCE.ResourceMissing() from None

    transport = Transport()
    def provider(owner):
        selected = owner.Provider(); selected._invoke = lambda service, operation, parameters: transport(service, operation, **parameters)
        return selected
    def fails(call, code):
        try: call()
        except D.known() + Y.known() as failure:
            assert failure.code == code, (failure.code, code)
            assert canary not in str(failure)
            return failure
        else: raise AssertionError("expected isolated restore rejection")
    def planned(owner, args):
        result = owner.run(args, provider(owner))
        assert result["verdict"] == "planned"
        args.approved_plan = result["plan_sha256"]
        return result
    def reader_args(phase):
        return SimpleNamespace(**{**vars(root_args), "mode": "plan", "phase": phase, "workload": "restore-reader", "operation": "restore-read", "proof_stage": "isolated-restore", "approved_plan": None})

    original_others = copy.deepcopy(original_transport.other)
    planned(D, root_args)
    root_args.mode = "review"; clone.lost = "create-change-set"
    fails(lambda: D.run(root_args, provider(D)), "restore-change-submission-uncertain-reconcile-only")
    assert D.run(root_args, provider(D))["verdict"] == "completed"
    assert sum(operation == "create-change-set" for _, operation, _ in clone.calls) == 1
    root_args.mode = "execute"; clone.lost = "execute-change-set"
    fails(lambda: D.run(root_args, provider(D)), "restore-execution-uncertain-reconcile-only")
    assert D.run(root_args, provider(D))["verdict"] == "completed"
    assert sum(operation == "execute-change-set" for _, operation, _ in clone.calls) == 1
    clone.lost = None
    cleanup_args = SimpleNamespace(**{**vars(root_args), "mode": "plan", "phase": "cleanup", "approved_plan": None})
    fails(lambda: D.run(cleanup_args, provider(D)), "restore-reader-completion-required")
    read_args = reader_args("operation")
    planned(Y, read_args); read_args.mode = "execute"
    before_jobs = len(original_transport.jobs.remote)
    fails(lambda: Y.run(read_args, provider(Y)), "restore-reader-preflight-required")
    assert len(original_transport.jobs.remote) == before_jobs
    host = next(row for row in task_definition["containerDefinitions"][0]["environment"] if row["name"] == "PERSISTENCE_POSTGRES_HOST")
    saved_host = host["value"]; host["value"] = value["parameters"]["DatabaseEndpoint"]
    failure = fails(lambda: Y.run(reader_args("preflight"), provider(Y)), "task-binding-container-not-confirmed")
    assert failure.workload == "restore-reader" and failure.field == "container"
    old_parse, old_provider = Y.parse, Y.Provider
    parsed = reader_args("preflight"); main_provider = provider(Y)
    Y.parse, Y.Provider = lambda: parsed, lambda: main_provider
    output = io.StringIO()
    try:
        with redirect_stdout(output): status = Y.main()
    finally: Y.parse, Y.Provider = old_parse, old_provider
    report = json.loads(output.getvalue())
    assert status == 1 and report["condition"] == "task-binding-container-not-confirmed" and report["context"]["affected_workload"] == "restore-reader" and report["effect"] == "not-started"
    assert canary not in output.getvalue()
    host["value"] = saved_host
    role_policy = policies[F.PHYSICAL["RestoreReaderTaskRole"]]["entity-smoke-restore-reader-database"]["Statement"][0]
    saved_resource = role_policy["Resource"]
    assert "db-RESTOREDABCDEFGHIJKLMNOP/entity_smoke_runtime" in saved_resource and value["parameters"]["DatabaseResourceId"] not in saved_resource
    role_policy["Resource"] = "arn:aws:rds-db:eu-west-1:337159794548:dbuser:" + value["parameters"]["DatabaseResourceId"] + "/entity_smoke_runtime"
    failure = fails(lambda: Y.run(reader_args("preflight"), provider(Y)), "task-binding-policy-not-confirmed")
    assert failure.item == "task-role" and failure.workload == "restore-reader"
    role_policy["Resource"] = saved_resource
    db_group = groups[F.PHYSICAL["RestoreDatabaseSecurityGroup"]]
    db_group["IpPermissions"].append(BF.permission({"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "CidrIp": "0.0.0.0/0"}))
    failure = fails(lambda: Y.run(reader_args("preflight"), provider(Y)), "task-binding-network-not-confirmed")
    assert failure.item == "database-ingress"
    db_group["IpPermissions"].pop()
    probe_args = reader_args("preflight")
    planned(Y, probe_args); probe_args.mode = "execute"; original_transport.jobs.lost_next = True
    fails(lambda: Y.run(probe_args, provider(Y)), "task-submission-uncertain-reconcile-required")
    assert Y.run(probe_args, provider(Y))["verdict"] == "completed"
    planned_read = reader_args("operation"); planned(Y, planned_read); planned_read.mode = "execute"; original_transport.jobs.lost_next = True
    fails(lambda: Y.run(planned_read, provider(Y)), "task-submission-uncertain-reconcile-required")
    read_result = Y.run(planned_read, provider(Y))
    assert read_result["verdict"] == "completed"
    assert len(original_transport.jobs.remote) == before_jobs + 2
    assert Y.run(planned_read, provider(Y))["historical"] is True
    read_packet = C.read_json(case.root / read_result["receipt"])
    assert read_packet["receipt"]["result"]["record_digest"] == snapshot_args.expected_digest
    assert read_packet["reservation"]["request"]["dependency_incarnation_sha256"] != case.binding["dependency_incarnation_sha256"]
    assert read_packet["reservation"]["request"]["permission_contract_sha256"] == C.digest_file(D.RESTORE.SOURCE)
    # A declaration never substitutes for original reader custody or ownership.
    read_path = case.root / read_result["receipt"]
    read_bytes = read_path.read_bytes()
    read_path.unlink()
    try: fails(lambda: D.run(cleanup_args, provider(D)), "restore-reader-completion-required")
    finally: read_path.write_bytes(read_bytes)
    old_tags = D.RESTORE.tags
    D.RESTORE.tags = lambda binding: {**old_tags(binding), "Scope": "foreign-scope"}
    try: fails(lambda: D.run(cleanup_args, provider(D)), "restore-ownership-not-confirmed")
    finally: D.RESTORE.tags = old_tags
    old_group = F.PHYSICAL["RestoreReaderSecurityGroup"]
    F.PHYSICAL["RestoreReaderSecurityGroup"] = "sg-" + "c" * 17
    try: fails(lambda: D.run(cleanup_args, provider(D)), "restore-deployment-observation-changed")
    finally: F.PHYSICAL["RestoreReaderSecurityGroup"] = old_group
    assert not any(operation == "delete-stack" for _, operation, _ in clone.calls)
    # Captured successful read, not expired remote observations, admits cleanup.
    for arn in list(original_transport.jobs.remote):
        original_transport.task_rows.pop(arn)
    original_transport.jobs.remote.clear(); original_transport.jobs.results.clear()
    planned(D, cleanup_args); cleanup_args.mode = "execute"
    approved = cleanup_args.approved_plan
    cleanup_args.approved_plan = "sha256:" + "0" * 64
    fails(lambda: D.run(cleanup_args, provider(D)), "restore-approved-plan-mismatch")
    assert not any(operation == "delete-stack" for _, operation, _ in clone.calls)
    cleanup_args.approved_plan = approved; clone.lost = "delete-stack"
    fails(lambda: D.run(cleanup_args, provider(D)), "restore-cleanup-submission-uncertain-reconcile-only")
    assert D.run(cleanup_args, provider(D))["verdict"] == "completed"
    assert D.run(cleanup_args, provider(D))["verdict"] == "completed"
    assert sum(operation == "delete-stack" for _, operation, _ in clone.calls) == 1
    assert original_transport.other == original_others and endpoint["IpPermissions"] == endpoint_before and original_transport.snapshot is not None
    assert clone.deleted is True
    # Acceptance observes the original gated cleanup with no deletion capability.
    before_delete = len(clone.calls)
    captured_cleanup = D.completed_cleanup(D.source(cleanup_args, provider(D)), cleanup_args, provider(D))
    assert captured_cleanup["receipt"]["result"]["facts"]["absence_observed"] is True
    assert not any(operation == "delete-stack" for _, operation, _ in clone.calls[before_delete:])
    # Use the real acceptance prerequisite and task caller, with the same actual
    # restore owner in this controlled source/custody/transport fixture. Never
    # replace cleanup validation with a successful stub.
    previous_restore_owner = T.ACCEPTANCE.restore_owner
    T.ACCEPTANCE.restore_owner = lambda: D
    try:
        final = SimpleNamespace(**{**vars(root_args), "workload": "verifier", "operation": "read", "phase": "preflight", "proof_stage": "acceptance", "execute": False})
        cleanup_path = value["cache"] / "restore-cleanup-receipt.json"
        cleanup_bytes = cleanup_path.read_bytes()
        cleanup_path.unlink()
        try:
            try: T.plan(final, provider(T))
            except T.ACCEPTANCE.AcceptanceFailure as failure: assert failure.code == "restore-cleanup-completion-required"
            else: raise AssertionError("final admission cannot omit original cleanup")
        finally: cleanup_path.write_bytes(cleanup_bytes)
        for phase in ("preflight", "operation"):
            final.phase = phase
            selected_plan = T.plan(final, provider(T))
            assert selected_plan["plan"]["execution_route_available"] is True
            final.approved_plan = selected_plan["plan_sha256"]
            if phase == "operation":
                original_transport.jobs.lost_next = True
                fails(lambda: T.execute(final, provider(T)), "task-submission-uncertain-reconcile-required")
            completed_final = T.execute(final, provider(T))
            assert completed_final["verdict"] == "completed"
        assert len(original_transport.jobs.remote) == 2, "one new final probe and one read, no replay after response loss"
        final_packet = C.read_json(case.root / completed_final["receipt"])
        assert final_packet["receipt"]["result"]["record_digest"] == snapshot_args.expected_digest
        assert T.RUNNER.EVIDENCE.timestamp(final_packet["receipt"]["task"]["created_at"]) >= T.RUNNER.EVIDENCE.timestamp(captured_cleanup["required_after"])
        assert final_packet["receipt"]["task"]["arn"] != read_packet["receipt"]["task"]["arn"]
        assert T.execute(final, provider(T))["verdict"] == "completed"
        assert len(original_transport.jobs.remote) == 2
        # Feed exact original route-produced receipts into the real acceptance
        # archivers, not hand-built passing plan/gate or primitive-validator stubs.
        K = module("entity_smoke_connected_original_archives", directory / "acceptance-route.py")
        K.D, K.T, K.C, K.A.T, K.A.C = D, T, C, T, C
        collection_binding = {**value["binding"], "record_digest": snapshot_args.expected_digest}
        final_context = T.prepare(final, provider(T))
        archives = {}
        for name, context, selection, historical in (
            ("restore-read", captured_cleanup["reader"]["context"], planned_read, True),
            ("final-read", final_context, final, False)):
            archives[name] = {}
            for phase in ("preflight", "operation"):
                selected = SimpleNamespace(**{**vars(selection), "phase": phase})
                archived = K.A.capture_task(T, context, selected, provider(T), name, collection_binding, historical=historical)
                original_path = T.STEPS.path(context, selected)
                assert archived["packet"] == C.read_json(original_path)
                assert archived["completion"]["step_sha256"] == "sha256:" + hashlib.sha256(original_path.read_bytes()).hexdigest()
                assert [row["gate"] for row in archived["gate"]["facts"]["gate_evidence"]] == list(C.GATE.GATE_ORDER[:7])
                assert archived["collection_binding"] == collection_binding
                archives[name][phase] = archived
        assert archives["restore-read"]["operation"]["packet"]["binding"]["dependency_incarnation_sha256"] != collection_binding["dependency_incarnation_sha256"]
        assert archives["final-read"]["operation"]["packet"]["binding"]["dependency_incarnation_sha256"] == collection_binding["dependency_incarnation_sha256"]
        assert archives["restore-read"]["operation"]["packet"]["receipt"]["task"]["arn"] != archives["final-read"]["operation"]["packet"]["receipt"]["task"]["arn"]
        K.A.fresh_final(archives["final-read"]["operation"], captured_cleanup["required_after"], C.now())
        for name, receipt in (("snapshot", value["snapshot"]), ("restore-deployment", captured_cleanup["reader"]["deployed"]), ("restore-cleanup", captured_cleanup["receipt"])):
            archived = K.control_proof(name, receipt, collection_binding, value["cache"], value["artifact"])
            assert K.validate_control(name, archived, collection_binding) is archived
            assert archived["custody"]["plan"] == receipt["packet"]["plan"]
            assert archived["operation_id"] == receipt["result"]["reservation"]["operation_id"]
            assert [row["gate"] for row in archived["custody"]["gate"]["facts"]["gate_evidence"]] == list(C.GATE.GATE_ORDER[:7])
            if name == "restore-cleanup":
                assert archived["custody"]["gate"]["change_summary"]["operation_counts"] == {"create": 0, "update": 0, "delete": 8, "replace": 0, "broaden-permission": 0}
                assert archived["facts"]["absence_observed"] is True and archived["facts"]["source_mutation"] is False
        def archive_failure(call, kind, condition):
            try: call()
            except kind as failure:
                assert failure.code == condition and canary not in str(failure)
            else: raise AssertionError("original archive custody must reject corruption")
        completion_path = T.COMPLETION.path(T.STEPS.path(final_context, final))
        completion_bytes = completion_path.read_bytes()
        capture_final = lambda: K.A.capture_task(T, final_context, final, provider(T), "final-read", collection_binding, historical=False)
        completion_path.unlink()
        try: archive_failure(capture_final, T.STEPS.StepFailure, "task-step-completion-required")
        finally: completion_path.write_bytes(completion_bytes)
        completion = C.read_json(completion_path)
        completion_path.write_text(json.dumps({**completion, "step_sha256": "sha256:" + "0" * 64}))
        try: archive_failure(capture_final, T.STEPS.StepFailure, "task-step-completion-binding-mismatch")
        finally: completion_path.write_bytes(completion_bytes)
        for gate_path, capture, kind, condition in (
            (case.root / completion["realization_evidence"], capture_final, T.STEPS.StepFailure, "task-step-completion-gate-changed"),
            (case.root / captured_cleanup["receipt"]["realization_evidence"],
             lambda: K.control_proof("restore-cleanup", captured_cleanup["receipt"], collection_binding, value["cache"], value["artifact"]),
             K.CONTROL.ControlFailure, "acceptance-control-original-gate-changed")):
            gate_bytes = gate_path.read_bytes()
            gate_path.write_bytes(gate_bytes + b"\n")
            try: archive_failure(capture, kind, condition)
            finally: gate_path.write_bytes(gate_bytes)
        assert completion_path.read_bytes() == completion_bytes
        assert capture_final()["packet"] == final_packet
        assert len(original_transport.jobs.remote) == 2 and sum(operation == "delete-stack" for _, operation, _ in clone.calls) == 1
    finally: T.ACCEPTANCE.restore_owner = previous_restore_owner
    for path in case.cache.rglob("*.json"): assert canary not in path.read_text()
    print(json.dumps({"schema": "deploy/entity-smoke-connected-restore-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "cases": ["actual-owned-clone-review-execute", "lost-review-and-execute-no-replay", "reader-required-before-cleanup", "separate-real-protocol-preflight", "source-host-role-network-denial", "actual-reader-main-reason", "clone-incarnation-and-permission-binding", "original-digest-read", "lost-preflight-and-read-no-replay", "historical-read-not-current-readiness", "expired-reader-cleanup-custody", "missing-original-reader-and-foreign-ownership-denied", "changed-resource-and-wrong-approval-denied", "lost-cleanup-one-delete", "owned-absence-and-baselines", "read-only-completed-cleanup", "missing-cleanup-blocks-final-task", "distinct-final-probe-and-original-record-read", "lost-final-read-no-replay", "original-reader-and-final-four-phase-archives", "original-snapshot-restore-cleanup-control-archives", "missing-or-altered-original-completion-denied", "original-task-and-cleanup-gate-bytes-required", "archive-handoff-has-no-new-effect"]}))


if __name__ == "__main__": runpy.run_path(str(Path(__file__).with_name("credential-route-test.py")), run_name="__main__")
