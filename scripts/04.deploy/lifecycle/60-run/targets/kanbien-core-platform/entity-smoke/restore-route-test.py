#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.connected-restore-route
#   version: 3
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-12"
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
from datetime import datetime, timedelta, timezone
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
    task_definition["containerDefinitions"][0]["linuxParameters"]["capabilities"]["add"] = []
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
        fail_reader = False
        fail_absence = False

        def missing(self, service, operation, code):
            condition = "aws-command-failed" if self.fail_absence else C.RESPONSE.classify_error(service, operation,
                "An error occurred (" + code + ") when calling the Fixture operation: " + canary)
            if condition == "aws-resource-missing": raise C.RESOURCE.ResourceMissing()
            raise C.InfrastructureFailure(condition)

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
                    if clone.deleted: self.missing(service, operation, "InvalidGroup.NotFound")
                    return {"SecurityGroups": [copy.deepcopy(groups[name]) for name in parameters["GroupIds"]]}
                name = parameters.get("RoleName")
                if name in roles:
                    if clone.deleted: self.missing(service, operation, "NoSuchEntity")
                    assert clone.state == "CREATE_COMPLETE"
                    if operation == "get-role": return {"Role": copy.deepcopy(roles[name])}
                    if operation == "list-attached-role-policies": return {"AttachedPolicies": [], "IsTruncated": False}
                    if operation == "list-role-policies": return {"PolicyNames": list(policies[name]), "IsTruncated": False}
                    if operation == "get-role-policy": return {"RoleName": name, "PolicyName": parameters["PolicyName"], "PolicyDocument": copy.deepcopy(policies[name][parameters["PolicyName"]])}
                result = original_call(service, operation, **parameters)
                if operation == "run-task" and self.fail_reader and parameters["taskDefinition"] == F.DEFINITION:
                    for task in result["tasks"]:
                        arn = task["taskArn"]
                        for row in (task, original_transport.jobs.remote[arn], original_transport.task_rows[arn]): row["containers"][0]["exitCode"] = 1
                        original_transport.jobs.results[arn.rsplit("/", 1)[1]] = {"verdict": "failed", "code": "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED",
                            "diagnostic": {"schema": "core/diagnostic-record/v1", "code": "persistence.unclassified-failure", "definitionVersion": 2,
                                "detail": {"phase": "pool_connect", "classification": "unknown", "codeStatus": "absent", "operation": "readiness", "effect": "not-assessed"}}, "related_diagnostics": []}
                return result
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
    # A checked controller successor consumes the unchanged snapshot/clone
    # custody only through exact pins; it cannot create either resource again.
    changed_context = {**value, "artifact": "sha256:" + "e" * 64}
    snapshot_path = value["cache"] / "snapshot-receipt.json"
    deployment_path = value["cache"] / "restore-deploy-receipt.json"
    original_controls = {path: path.read_bytes() for path in (snapshot_path, deployment_path)}
    fails(lambda: S.completed(changed_context, root_args, original_transport), "snapshot-completed-binding-mismatch")
    fails(lambda: D.deployment(changed_context, root_args, provider(D)), "restore-deployment-binding-mismatch")
    pins = {(name, C.digest_file(path)): C.read_json(path)["packet"]["plan"]["controller_sha256"]
            for name, path in (("snapshot", snapshot_path), ("restore-deployment", deployment_path))}
    C.CONTROL_COMPLETION.REPAIRS.update(pins)
    try:
        assert S.completed(changed_context, root_args, original_transport) == C.read_json(snapshot_path)
        assert D.deployment(changed_context, root_args, provider(D)) == C.read_json(deployment_path)
        assert all(path.read_bytes() == content for path, content in original_controls.items())
    finally:
        for pin in pins: C.CONTROL_COMPLETION.REPAIRS.pop(pin)
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
    # A terminal failed clone probe remains negative evidence. Its one explicitly
    # selected successor uses the real route/runner, not a successful stub.
    failed_args = reader_args("preflight")
    failed_context, _ = Y.prepare(failed_args, provider(Y))
    planned(Y, failed_args); failed_args.mode = "execute"; transport.fail_reader = True
    observed_failure = fails(lambda: Y.run(failed_args, provider(Y)), "task-unsuccessful-completion")
    transport.fail_reader = False
    original_request = T.STEPS.request(T.dependencies(), failed_context, failed_args)
    original_reservation = T.RUNNER.CONTROL.AttemptStore(value["cache"] / "task-attempts").read(T.STEPS.key(failed_args), original_request)
    original_task = next(task for task in original_transport.task_rows.values() if task.get("startedBy") == original_reservation["operation_id"])
    failed_path = value["cache"] / "task-attempts" / (original_request["proof_label"] + "-restore-reader-preflight.json")
    failed_bytes = failed_path.read_bytes()
    failure_report = {"condition": observed_failure.code, "effect": "unknown-reconcile-only", "context": {"mode": "execute", "phase": "preflight", "workload": "restore-reader"}, **T.RUNNER.EVIDENCE.failure_report(observed_failure)}
    failure_report_path = value["cache"] / "diagnostics/fixture-restore-failure-report.json"
    C.RESOURCE.write_exclusive(failure_report_path, failure_report)
    failure_path = value["cache"] / "diagnostics/fixture-restore-failure.json"
    negative = {"schema": "deploy/entity-smoke-restore-reader-failure/v1", "scope_acceptance": False, "current_readiness": False,
        "condition": observed_failure.code, "observed_at": max(C.RESOURCE.timestamp(C.now()), C.RESOURCE.timestamp(original_task["stoppedAt"])).isoformat(), "reservation_path": str(failed_path.relative_to(C.ROOT)), "reservation_sha256": C.digest_file(failed_path),
        "failure_path": str(failure_report_path.relative_to(C.ROOT)), "failure_sha256": C.digest_file(failure_report_path),
        "deployment_sha256": C.digest_file(value["cache"] / "restore-deploy-receipt.json"),
        "task": {"arn": original_task["taskArn"], "operation_id": original_reservation["operation_id"], "created_at": original_task["createdAt"],
            "started_at": original_task["startedAt"], "stopped_at": original_task["stoppedAt"], "exit_code": 1, "image_digest": original_request["image_digest"]},
        **T.RUNNER.EVIDENCE.failure_report(observed_failure)}
    C.RESOURCE.write_exclusive(failure_path, negative)
    negative_bytes = failure_path.read_bytes()
    overrides = []
    for owner in (C.TRANSITION, T.STEPS.TRANSITION):
        for key, item in {"RESTORE_LABEL": root_args.proof_label, "RESTORE_PROBE": original_reservation["operation_id"], "RESTORE_FAILURE": str(failure_path.relative_to(value["cache"])), "RESTORE_FAILURE_HASH": C.digest_file(failure_path)}.items():
            overrides.append((owner, key, getattr(owner, key))); setattr(owner, key, item)
    new_context, _ = Y.prepare(reader_args("preflight"), provider(Y))
    assert new_context["report"]["plan"]["preflight_label"] != original_request["proof_label"]
    assert "connection-recovery-1" in str(T.STEPS.path(new_context, reader_args("preflight")))
    failure_path.write_bytes(negative_bytes + b"\n")
    try: fails(lambda: Y.prepare(reader_args("preflight"), provider(Y)), "restore-reader-recovery-evidence-changed")
    finally: failure_path.write_bytes(negative_bytes)
    failed_path.write_bytes(failed_bytes + b"\n")
    try: fails(lambda: Y.prepare(reader_args("preflight"), provider(Y)), "restore-reader-recovery-reservation-changed")
    finally: failed_path.write_bytes(failed_bytes)
    operation_path = value["cache"] / "task-attempts" / (T.STEPS.key(reader_args("operation")) + ".json")
    operation_path.write_text("{}")
    try: fails(lambda: Y.prepare(reader_args("preflight"), provider(Y)), "restore-reader-recovery-operation-already-reserved")
    finally: operation_path.unlink()
    for mutate, code in (
        (lambda v: v.update(deployment_sha256="sha256:" + "0" * 64), "restore-reader-recovery-evidence-invalid"),
        (lambda v: v["task"].update(exit_code=0), "restore-reader-recovery-terminal-required"),
        (lambda v: v["diagnostic"]["detail"].update(phase="query"), "restore-reader-recovery-diagnostic-invalid")):
        changed = copy.deepcopy(negative); mutate(changed)
        failure_path.write_bytes(C.RESOURCE.CONTROL.canonical(changed) + b"\n")
        old_hash = C.TRANSITION.RESTORE_FAILURE_HASH
        C.TRANSITION.RESTORE_FAILURE_HASH = C.digest_file(failure_path)
        try: fails(lambda: C.TRANSITION.restore_reader_preflight(C, new_context, new_context["deployed"], original_request["proof_label"]), code)
        finally:
            failure_path.write_bytes(negative_bytes); C.TRANSITION.RESTORE_FAILURE_HASH = old_hash
    wrong_clone = {**new_context, "binding": {**new_context["binding"], "dependency_incarnation_sha256": "sha256:" + "0" * 64}}
    fails(lambda: C.TRANSITION.restore_reader_preflight(C, wrong_clone, new_context["deployed"], original_request["proof_label"]), "restore-reader-recovery-original-request-mismatch")
    assert len(original_transport.jobs.remote) == before_jobs + 1
    probe_args = reader_args("preflight")
    planned(Y, probe_args); probe_args.mode = "execute"; original_transport.jobs.lost_next = True
    fails(lambda: Y.run(probe_args, provider(Y)), "task-submission-uncertain-reconcile-required")
    recovered_context, _ = Y.prepare(probe_args, provider(Y))
    recovered_request = T.STEPS.request(T.dependencies(), recovered_context, probe_args)
    recovered_reservation = recovered_context["store"].read(T.STEPS.key(probe_args), recovered_request)
    recovered_task = next(task for task in original_transport.task_rows.values() if task.get("startedBy") == recovered_reservation["operation_id"])
    recovered_id = recovered_task["taskArn"].rsplit("/", 1)[1]
    # Controlled negative observation branch: repeated failure admits no third
    # launch. Restore the fixture's original success for downstream tests only.
    saved_result = original_transport.jobs.results[recovered_id]
    recovered_task["containers"][0]["exitCode"] = 1
    original_transport.jobs.results[recovered_id] = original_transport.jobs.results[original_task["taskArn"].rsplit("/", 1)[1]]
    try:
        for _ in range(2): fails(lambda: Y.run(probe_args, provider(Y)), "task-unsuccessful-completion")
        assert len(original_transport.jobs.remote) == before_jobs + 2
    finally:
        recovered_task["containers"][0]["exitCode"] = 0; original_transport.jobs.results[recovered_id] = saved_result
    assert Y.run(probe_args, provider(Y))["verdict"] == "completed"
    planned_read = reader_args("operation"); planned(Y, planned_read); planned_read.mode = "execute"; original_transport.jobs.lost_next = True
    fails(lambda: Y.run(planned_read, provider(Y)), "task-submission-uncertain-reconcile-required")
    read_result = Y.run(planned_read, provider(Y))
    assert read_result["verdict"] == "completed"
    assert len(original_transport.jobs.remote) == before_jobs + 3
    assert failed_path.read_bytes() == failed_bytes and failure_path.read_bytes() == negative_bytes
    assert Y.run(planned_read, provider(Y))["historical"] is True
    read_packet = C.read_json(case.root / read_result["receipt"])
    assert read_packet["receipt"]["result"]["record_digest"] == snapshot_args.expected_digest
    assert read_packet["reservation"]["request"]["dependency_incarnation_sha256"] != case.binding["dependency_incarnation_sha256"]
    assert read_packet["reservation"]["request"]["permission_contract_sha256"] == C.digest_file(D.RESTORE.SOURCE)
    # Completed clone-reader proof belongs to the original controller, including
    # its separately retained plan. A successor cannot restamp it or rerun jobs.
    task_pins = {}
    for selected_phase in ("preflight", "operation"):
        selected_args = reader_args(selected_phase)
        step_path = T.STEPS.path(value, selected_args)
        step = C.read_json(step_path); completion = C.read_json(T.COMPLETION.path(step_path))
        task_pins[C.TRANSITION.document(step)] = (C.TRANSITION.document(completion), value["artifact"][7:])
    C.CONTROL_COMPLETION.REPAIRS.update(pins)
    C.TRANSITION.CONTROLLER_REPAIR_PINS.update(task_pins)
    try:
        assert D.reader(changed_context, root_args, provider(D))["step"] == read_packet
    finally:
        for pin in pins: C.CONTROL_COMPLETION.REPAIRS.pop(pin)
        for pin in task_pins: C.TRANSITION.CONTROLLER_REPAIR_PINS.pop(pin)
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
    # Retain an actual public not-started response from the old comparison,
    # then derive the corrected plan without overwriting the original or
    # granting any submission/replay capability to this selector.
    original_validation = D.RESTORE.validate_reader
    old_parse, old_provider = D.parse, D.Provider
    D.RESTORE.validate_reader = lambda *a, **kw: D.RESTORE.require(False, "restore-reader-task-definition-not-confirmed")
    provider_for_cleanup = provider(D); output = io.StringIO()
    D.parse, D.Provider = lambda: cleanup_args, lambda: provider_for_cleanup
    try:
        with redirect_stdout(output): failed_status = D.main()
    finally:
        D.RESTORE.validate_reader = original_validation
        D.parse, D.Provider = old_parse, old_provider
    failure_report = json.loads(output.getvalue())
    assert failed_status == 1 and failure_report["condition"] == "restore-reader-task-definition-not-confirmed" and failure_report["effect"] == "not-started"
    failed_plan_path = value["cache"] / "restore-cleanup-plan.json"
    failed_plan_bytes = failed_plan_path.read_bytes(); failed_plan = C.read_json(failed_plan_path)
    repaired_plan = copy.deepcopy(failed_plan)
    repaired_plan["plan"]["controller_sha256"] = changed_context["artifact"]
    repaired_plan["plan_sha256"] = C.DEPLOY.fingerprint(repaired_plan["plan"])
    failure_report_path = value["cache"] / "cleanup-failure-fixture.json"
    C.RESOURCE.write_exclusive(failure_report_path, failure_report)
    repair_values = {"CLEANUP_LABEL": root_args.proof_label, "CLEANUP_PLAN_HASH": C.digest_file(failed_plan_path),
                     "CLEANUP_FAILURE": str(failure_report_path.relative_to(C.ROOT)), "CLEANUP_FAILURE_HASH": C.digest_file(failure_report_path)}
    saved_repair_values = {key: getattr(C.TRANSITION, key) for key in repair_values}
    for key, item in repair_values.items(): setattr(C.TRANSITION, key, item)
    store = D.R.ResourceStore(value["cache"] / "attempts")
    try:
        selected_path = C.TRANSITION.cleanup_plan_path(C, value["cache"], repaired_plan, store)
        assert selected_path != failed_plan_path and not selected_path.exists() and failed_plan_path.read_bytes() == failed_plan_bytes
        original_source = D.source
        C.CONTROL_COMPLETION.REPAIRS.update(pins); C.TRANSITION.CONTROLLER_REPAIR_PINS.update(task_pins)
        D.source = lambda *a, **kw: changed_context
        try:
            replanned = D.prepare(SimpleNamespace(**{**vars(cleanup_args), "mode": "plan", "approved_plan": None}), provider(D))
            assert replanned["packet"] == repaired_plan and replanned["active"] == selected_path
            assert C.read_json(selected_path) == repaired_plan and failed_plan_path.read_bytes() == failed_plan_bytes
        finally:
            D.source = original_source
            for pin in pins: C.CONTROL_COMPLETION.REPAIRS.pop(pin)
            for pin in task_pins: C.TRANSITION.CONTROLLER_REPAIR_PINS.pop(pin)
        selected_path.unlink()
        changed_intent = copy.deepcopy(repaired_plan); changed_intent["plan"]["resource_count"] += 1
        fails(lambda: C.TRANSITION.cleanup_plan_path(C, value["cache"], changed_intent, store), "restore-cleanup-repair-intent-changed")
        reserved = SimpleNamespace(read=lambda *a: {"operation_id": "existing-operation"})
        fails(lambda: C.TRANSITION.cleanup_plan_path(C, value["cache"], repaired_plan, reserved), "restore-cleanup-repair-already-reserved")
        C.RESOURCE.write_exclusive(selected_path, repaired_plan)
        assert C.TRANSITION.cleanup_plan_path(C, value["cache"], repaired_plan, reserved) == selected_path
        selected_path.unlink()
        original_failure_bytes = failure_report_path.read_bytes(); failure_report_path.write_text("{}")
        try: fails(lambda: C.TRANSITION.cleanup_plan_path(C, value["cache"], repaired_plan, store), "restore-cleanup-repair-failure-changed")
        finally: failure_report_path.write_bytes(original_failure_bytes)
        failed_plan_path.write_text("{}")
        try: fails(lambda: C.TRANSITION.cleanup_plan_path(C, value["cache"], repaired_plan, store), "restore-cleanup-repair-original-plan-changed")
        finally: failed_plan_path.write_bytes(failed_plan_bytes)
    finally:
        for key, item in saved_repair_values.items(): setattr(C.TRANSITION, key, item)
    assert not any(operation == "delete-stack" for _, operation, _ in clone.calls)
    approved = cleanup_args.approved_plan
    cleanup_args.approved_plan = "sha256:" + "0" * 64
    fails(lambda: D.run(cleanup_args, provider(D)), "restore-approved-plan-mismatch")
    assert not any(operation == "delete-stack" for _, operation, _ in clone.calls)
    cleanup_args.approved_plan = approved; clone.lost = "delete-stack"
    fails(lambda: D.run(cleanup_args, provider(D)), "restore-cleanup-submission-uncertain-reconcile-only")
    transport.fail_absence = True
    old_parse, old_provider = D.parse, D.Provider
    observer = provider(D); D.parse, D.Provider = lambda: cleanup_args, lambda: observer
    output = io.StringIO()
    try:
        with redirect_stdout(output): failed_status = D.main()
    finally: D.parse, D.Provider = old_parse, old_provider
    failed_observation = json.loads(output.getvalue())
    assert failed_status == 1 and failed_observation["condition"] == "restore-cleanup-observation-unavailable"
    assert failed_observation["effect"] == "original-restore-operation-reconcile-only" and clone.deleted
    observation_path = value["cache"] / "cleanup-absence-failure.json"
    C.RESOURCE.write_exclusive(observation_path, failed_observation)
    original_packet = C.read_json(failed_plan_path)
    journal_path = store.path_for("delete-restore", original_packet["request"])
    journal = C.read_json(journal_path)
    admissions = [path for path in (value["cache"] / "restore-cleanup-realization").glob("execution-preflight-*.json")
                  if C.read_json(path)["plan_sha256"] == approved and C.RESOURCE.timestamp(C.read_json(path)["facts"]["gate_evidence"][-1]["timestamp"]) <= C.RESOURCE.timestamp(journal["reserved_at"])]
    assert admissions
    admission_path = sorted(admissions)[0]
    source_paths = {"plan": value["cache"] / "restore-cleanup-plans" / (approved[7:] + ".json"), "reservation": journal_path, "gate": admission_path}
    reconcile_values = {**repair_values, "CLEANUP_RECONCILE_PLAN": approved,
        "CLEANUP_RECONCILE": {name: (str(path.relative_to(value["cache"])), C.digest_file(path)) for name, path in source_paths.items()},
        "CLEANUP_RECONCILE_FAILURE": str(observation_path.relative_to(C.ROOT)), "CLEANUP_RECONCILE_FAILURE_HASH": C.digest_file(observation_path)}
    for key, item in reconcile_values.items():
        overrides.append((C.TRANSITION, key, getattr(C.TRANSITION, key))); setattr(C.TRANSITION, key, item)
    original_bytes = {path: path.read_bytes() for path in (*source_paths.values(), observation_path, failed_plan_path)}
    missing_store = SimpleNamespace(read=lambda *a: None)
    fails(lambda: C.TRANSITION.cleanup_reconciliation(C, value["cache"], original_packet["plan"]["binding"], original_packet["request"], missing_store, D.graph("cleanup")), "restore-cleanup-reconciliation-original-mismatch")
    for name, path in source_paths.items():
        path.write_bytes(original_bytes[path] + b"\n")
        try: fails(lambda: C.TRANSITION.cleanup_reconciliation(C, value["cache"], original_packet["plan"]["binding"], original_packet["request"], store, D.graph("cleanup")), "restore-cleanup-reconciliation-custody-changed")
        finally: path.write_bytes(original_bytes[path])
    # The normal seventh-gate reader must still reject a six-gate admission.
    fails(lambda: T.COMPLETION.validate_gate(SimpleNamespace(C=C, STEPS=SimpleNamespace(require=C.require)), D.graph("cleanup"), C.read_json(admission_path), approved,
          {"restore-cleanup-controller-source": value["artifact"]}), "task-step-completion-gates-incomplete")
    transport.fail_absence = False; cleanup_args.mode = "plan"
    reconciled = planned(D, cleanup_args)
    assert reconciled["plan"]["reconciles_plan_sha256"] == approved and reconciled["plan_sha256"] != approved
    cleanup_args.mode = "execute"
    old_cleanup, old_reserve, old_enable = D.RESTORE.cleanup_restore, D.R.ResourceStore.reserve, D.Provider.enable_restore
    def prohibited(*a, **kw): raise AssertionError("observation-only reconciliation attempted a mutation capability")
    D.RESTORE.cleanup_restore = D.R.ResourceStore.reserve = D.Provider.enable_restore = prohibited
    try:
        assert D.run(cleanup_args, provider(D))["verdict"] == "completed"
        assert D.run(cleanup_args, provider(D))["verdict"] == "completed"
    finally: D.RESTORE.cleanup_restore, D.R.ResourceStore.reserve, D.Provider.enable_restore = old_cleanup, old_reserve, old_enable
    assert all(path.read_bytes() == content for path, content in original_bytes.items())
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
                if name == "restore-read":
                    pin = C.TRANSITION.document(archived["packet"])
                    previous_pin = C.TRANSITION.CONTROLLER_REPAIR_PINS.get(pin)
                    C.TRANSITION.CONTROLLER_REPAIR_PINS[pin] = (C.TRANSITION.document(archived["completion"]), archived["controller_sha256"][7:])
                    try:
                        assert K.A.validate_task(archived, collection_binding, expected_binding=context["binding"]) is archived
                        try: K.A.validate_task(archived, collection_binding, expected_binding=value["binding"])
                        except K.A.EvidenceFailure as failure: assert failure.code == "acceptance-task-binding-mismatch"
                        else: raise AssertionError("a controller pin cannot waive the clone binding")
                    finally:
                        if previous_pin is None: C.TRANSITION.CONTROLLER_REPAIR_PINS.pop(pin)
                        else: C.TRANSITION.CONTROLLER_REPAIR_PINS[pin] = previous_pin
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
            if name in {"snapshot", "restore-deployment", "restore-cleanup"}:
                pin = (name, K.A.document_digest(receipt))
                C.CONTROL_COMPLETION.REPAIRS[pin] = receipt["packet"]["plan"]["controller_sha256"]
                try:
                    historical = K.control_proof(name, receipt, collection_binding, value["cache"], "sha256:" + "e" * 64)
                    assert historical["custody"]["plan"] == receipt["packet"]["plan"]
                finally: C.CONTROL_COMPLETION.REPAIRS.pop(pin)
            if name == "restore-cleanup":
                assert archived["custody"]["plan"]["reconciles_plan_sha256"] == approved
                assert archived["custody"]["gate"]["change_summary"]["operation_counts"] == {"create": 0, "update": 0, "delete": 8, "replace": 0, "broaden-permission": 0}
                assert archived["facts"]["absence_observed"] is True and archived["facts"]["source_mutation"] is False
        def archive_failure(call, kind, condition):
            try: call()
            except kind as failure:
                assert failure.code == condition and canary not in str(failure)
            else: raise AssertionError("original archive custody must reject corruption")
        cleanup_plan = captured_cleanup["receipt"]["packet"]["plan"]
        for changed in ({"reconciles_plan_sha256": "sha256:" + "0" * 64}, {"binding": None},
                        {"binding": {**cleanup_plan["binding"], "proof_label": "foreign-proof"}}):
            archive_failure(lambda: K.CONTROL.validate_plan(K.A, "restore-cleanup", {**cleanup_plan, **changed}, collection_binding),
                            K.CONTROL.ControlFailure, "acceptance-control-reconciliation-reference-invalid")
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
        # The actual failed-collection recovery consumes original immutable
        # packets, journals, admissions and seven-gate companions. Only the
        # expiry clock is controlled; all new task gates use the normal clock.
        transition = C.TRANSITION
        original_paths, refresh_inputs = {}, {}
        for phase in ("preflight", "operation"):
            selected = SimpleNamespace(**{**vars(final), "phase": phase})
            path = T.STEPS.path(final_context, selected)
            companion = T.COMPLETION.path(path)
            original_paths[path], original_paths[companion] = path.read_bytes(), companion.read_bytes()
            refresh_inputs[phase] = (str(path.relative_to(value["cache"])), C.digest_file(path), C.digest_file(companion))
        failure_path = value["cache"] / "controlled-collector-failure.json"
        failure_path.write_text(json.dumps({"schema": "deploy/entity-smoke-acceptance-report/v1", "verdict": "blocked",
            "condition": "source-transition-binding-incompatible", "effect": "no-provider-mutation-no-scope-promotion",
            "context": {"proof_label_sha256": hashlib.sha256(final.proof_label.encode()).hexdigest(), "stage": "acceptance-collection"}}))
        changes = {"ACCEPTANCE_REFRESH_LABEL": final.proof_label, "ACCEPTANCE_REFRESH_CONTROLLER": value["artifact"],
            "ACCEPTANCE_REFRESH_FAILURE": str(failure_path.relative_to(C.ROOT)), "ACCEPTANCE_REFRESH_FAILURE_HASH": C.digest_file(failure_path),
            "ACCEPTANCE_REFRESH_INPUTS": refresh_inputs}
        original_key = T.STEPS.key(final)
        for key, replacement in changes.items():
            overrides.append((transition, key, getattr(transition, key))); setattr(transition, key, replacement)
        overrides.append((T.STEPS.TRANSITION, "ACCEPTANCE_REFRESH_LABEL", T.STEPS.TRANSITION.ACCEPTANCE_REFRESH_LABEL))
        T.STEPS.TRANSITION.ACCEPTANCE_REFRESH_LABEL = final.proof_label
        before = archives["final-read"]["preflight"]["packet"]["reservation"]["request"]["proof_label"]
        future = (C.RESOURCE.timestamp(final_packet["receipt"]["collected_at"]) + timedelta(seconds=901)).isoformat()
        expiry_check = transition.acceptance_refresh_preflight
        check = lambda: expiry_check(C, final_context, final, before, current_time=future)
        assert check() == transition.replacement_label(final_context, final, before)
        fails(lambda: expiry_check(C, final_context, final, before, current_time=C.now()), "acceptance-refresh-original-read-not-expired")
        for path, content in original_paths.items():
            path.write_bytes(content + b"\n")
            try: fails(check, "acceptance-refresh-original-custody-changed")
            finally: path.write_bytes(content)
        failed_bytes = failure_path.read_bytes(); failure_path.write_bytes(failed_bytes + b"\n")
        try: fails(check, "acceptance-refresh-failure-changed")
        finally: failure_path.write_bytes(failed_bytes)
        gate_path = case.root / completion["realization_evidence"]
        gate_bytes = gate_path.read_bytes(); gate_path.write_bytes(gate_bytes + b"\n")
        try: fails(check, "acceptance-refresh-original-gate-changed")
        finally: gate_path.write_bytes(gate_bytes)
        assert T.STEPS.key(final) != original_key and T.STEPS.path(final_context, final) not in original_paths
        transition.acceptance_refresh_preflight = lambda C, context, args, original, **kw: expiry_check(C, context, args, original, current_time=future)
        try:
            for phase in ("preflight", "operation"):
                final.phase = phase
                refreshed_plan = T.plan(final, provider(T))
                final.approved_plan = refreshed_plan["plan_sha256"]
                if phase == "operation":
                    original_transport.jobs.lost_next = True
                    fails(lambda: T.execute(final, provider(T)), "task-submission-uncertain-reconcile-required")
                assert T.execute(final, provider(T))["verdict"] == "completed"
                refreshed_context = T.prepare(final, provider(T))
                refreshed = K.A.capture_task(T, refreshed_context, final, provider(T), "final-read", collection_binding, historical=False)
                assert refreshed["packet"]["binding"] == final_context["binding"]
            assert T.execute(final, provider(T))["verdict"] == "completed"
            assert len(original_transport.jobs.remote) == 4, "one fresh pair, no third pair or lost-response replay"
            K.A.fresh_final(refreshed, captured_cleanup["required_after"], C.now())
            assert all(path.read_bytes() == content for path, content in original_paths.items())
            assert cleanup_path.read_bytes() == cleanup_bytes and sum(operation == "delete-stack" for _, operation, _ in clone.calls) == 1
        finally: transition.acceptance_refresh_preflight = expiry_check
    finally: T.ACCEPTANCE.restore_owner = previous_restore_owner
    for path in case.cache.rglob("*.json"): assert canary not in path.read_text()
    for owner, key, old in reversed(overrides): setattr(owner, key, old)
    print(json.dumps({"schema": "deploy/entity-smoke-connected-restore-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "cases": ["actual-owned-clone-review-execute", "lost-review-and-execute-no-replay", "reader-required-before-cleanup", "separate-real-protocol-preflight", "source-host-role-network-denial", "actual-reader-main-reason", "clone-incarnation-and-permission-binding", "original-digest-read", "lost-preflight-and-read-no-replay", "historical-read-not-current-readiness", "expired-reader-cleanup-custody", "missing-original-reader-and-foreign-ownership-denied", "changed-resource-and-wrong-approval-denied", "lost-cleanup-one-delete", "owned-absence-and-baselines", "read-only-completed-cleanup", "missing-cleanup-blocks-final-task", "distinct-final-probe-and-original-record-read", "lost-final-read-no-replay", "original-reader-and-final-four-phase-archives", "original-snapshot-restore-cleanup-control-archives", "missing-or-altered-original-completion-denied", "original-task-and-cleanup-gate-bytes-required", "archive-handoff-has-no-new-effect"]}))


if __name__ == "__main__": runpy.run_path(str(Path(__file__).with_name("credential-route-test.py")), run_name="__main__")
