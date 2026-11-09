#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.failure-route
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual gated stop/reservation/custody behavior with failed or queued workloads and controlled provider responses, not AWS proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timezone
import copy
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

if not __debug__: raise SystemExit("ENTITY_SMOKE_FAILURE_ROUTE_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
M = module("entity_smoke_failure_route_fixture", DIRECTORY / "failure-route.py")
BF = module("entity_smoke_failure_task_responses", DIRECTORY / "task-binding-test.py")
F = BF.F
REAL_ROOT, CANARY = M.C.ROOT, "failure-provider-endpoint-credential-row-canary"
PREFIX = "arn:aws:ecs:eu-west-1:337159794548:"
SERVICE_ARN = PREFIX + "service/kanbien-core-platform/kanbien-core-platform-entity-smoke"
SERVER, MIGRATION = PREFIX + "task/kanbien-core-platform/" + "1" * 32, PREFIX + "task/kanbien-core-platform/" + "2" * 32
READER = PREFIX + "task/kanbien-core-platform/" + "3" * 32

catalog = M.C.yaml.safe_load((REAL_ROOT / "scripts/repo/check-selection/checks.yml").read_text())
required_inputs = {"scripts/04.deploy/lifecycle/60-run/release-succession/script.py",
                   "scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py",
                   "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/scope-index.yml"}


def assert_custody_input_binding(inputs):
    assert required_inputs <= set(inputs), "real policy/lifecycle dependencies must invalidate composition reuse"


declared_inputs = catalog["checks"]["entity-smoke-composition"]["inputs"]
assert_custody_input_binding(declared_inputs)
for dependency in required_inputs:
    try: assert_custody_input_binding([value for value in declared_inputs if value != dependency])
    except AssertionError: pass
    else: raise AssertionError("missing custody dependency must reject the actual catalog binding")


class Transport(F.Provider):
    def __init__(self):
        super().__init__()
        self.observed, self.desired, self.server_running = [], 0, False
        self.bindings = {name: BF.Provider(name) for name in M.B.WORKLOADS}
        self.resources = [{"LogicalResourceId": name, "ResourceType": row["type"], "PhysicalResourceId": SERVICE_ARN if name == "FeatureService" else row["physical_id"], "ResourceStatus": "CREATE_COMPLETE"} for name, row in BF.RESOURCES.items()]
        self.task_rows = {}
        self.lost_service, self.lost_task, self.delayed = False, False, False
        self.pagination, self.denied_write = False, False
        self.before_write = lambda operation, parameters: None
        self.during_simulation = lambda: None
        self.partial, self.service_present, self.clone = False, True, None
        self.other = []
        for name in ("kanbien-core-platform-bootstrap-runtime", "kanbien-core-platform-core-server-persistence", "kanbien-core-platform-observability-collector"):
            self.other.append({"serviceName": name, "serviceArn": PREFIX + "service/kanbien-core-platform/" + name,
                               "clusterArn": F.PARAMETERS["ClusterArn"], "taskDefinition": PREFIX + "task-definition/" + name + ":17",
                               "status": "ACTIVE", "desiredCount": 1, "runningCount": 1, "pendingCount": 0,
                               "networkConfiguration": {"awsvpcConfiguration": {"subnets": ["subnet-" + "2" * 17], "securityGroups": ["sg-" + "3" * 17], "assignPublicIp": "DISABLED"}},
                               "events": [{"message": CANARY}]})

    def service(self):
        return {"serviceName": M.C.RESOURCE.SERVICE, "serviceArn": SERVICE_ARN, "clusterArn": F.PARAMETERS["ClusterArn"],
                "taskDefinition": BF.RESOURCES["ServerTaskDefinition"]["physical_id"], "status": "ACTIVE", "desiredCount": self.desired,
                "runningCount": int(self.server_running), "pendingCount": 0, "events": [{"message": CANARY}]}

    def failed_runtime(self):
        self.stack["StackStatus"] = "UPDATE_FAILED"
        for row in self.stack["Parameters"]:
            if row["ParameterKey"] == "ServerDesiredCount": row["ParameterValue"] = "1"
        self.desired, self.server_running = 1, True
        for arn, workload, group, state in ((SERVER, "server", "service:" + M.C.RESOURCE.SERVICE, "RUNNING"),
                (MIGRATION, "migration", "family:kanbien-core-platform-entity-smoke-migration", "PENDING")):
            self.task_rows[arn] = {"taskArn": arn, "taskDefinitionArn": BF.RESOURCES[M.B.WORKLOADS[workload] + "TaskDefinition"]["physical_id"], "group": group,
                                   "lastStatus": state, "launchType": "FARGATE", "healthStatus": "UNHEALTHY", "containers": [{"name": "entity-smoke-" + workload, "reason": CANARY}],
                                   "createdAt": datetime.now(timezone.utc).isoformat()}

    def stopped(self, arn):
        self.task_rows[arn].update(lastStatus="STOPPED", stoppedAt=datetime.now(timezone.utc).isoformat())
        if arn == SERVER: self.server_running = False

    def __call__(self, service_name, operation, **parameters):
        self.observed.append((service_name, operation, copy.deepcopy(parameters)))
        if operation == "get-caller-identity": return {"Account": M.C.ALIGN.ACCOUNT, "Arn": "arn:aws:sts::337159794548:assumed-role/ApprovedOperator/fixture"}
        if operation == "get-role": return {"Role": {"RoleName": "ApprovedOperator", "Arn": "arn:aws:iam::337159794548:role/ApprovedOperator"}}
        if operation == "simulate-principal-policy":
            self.during_simulation()
            return {"IsTruncated": False, "EvaluationResults": [{"EvalActionName": parameters["ActionNames"][0], "EvalResourceName": arn, "EvalDecision": "allowed"} for arn in parameters["ResourceArns"]]}
        if operation == "describe-stacks" and "entity-smoke-restore-" in parameters["StackName"]:
            if self.clone is None: raise M.C.RESOURCE.ResourceMissing()
            return {"Stacks": [copy.deepcopy(self.clone["stack"])]}
        if self.clone is not None and parameters.get("StackName") == self.clone["stack"]["StackId"]:
            if operation == "get-template": return {"TemplateBody": M.RESTORE.source()[0]}
            if operation == "describe-stack-events": return {"StackEvents": [{"PhysicalResourceId": self.clone["stack"]["StackId"], "ClientRequestToken": self.clone["operation_id"]}]}
            if operation == "list-stack-resources": return {"StackResourceSummaries": copy.deepcopy(self.clone["resources"])}
        if operation == "describe-task-definition":
            if self.clone is not None and parameters["taskDefinition"] == self.clone["definition"]["taskDefinitionArn"]: return {"taskDefinition": copy.deepcopy(self.clone["definition"])}
            name = next(name for name in self.bindings if self.bindings[name].task["taskDefinitionArn"] == parameters["taskDefinition"])
            return {"taskDefinition": copy.deepcopy(self.bindings[name].task)}
        if operation == "list-services": return {"serviceArns": [*([SERVICE_ARN] if self.service_present else []), *[row["serviceArn"] for row in self.other]]}
        if operation == "describe-services":
            rows = [*([self.service()] if self.service_present else []), *self.other]
            return {"services": [copy.deepcopy(row) for row in rows if row["serviceArn"] in parameters["services"] or row["serviceName"] in parameters["services"]], "failures": []}
        if operation == "list-tasks":
            rows = []
            for arn, row in self.task_rows.items():
                if "serviceName" in parameters and row["group"] != "service:" + parameters["serviceName"]: continue
                if "family" in parameters and row["taskDefinitionArn"].split("/")[1].split(":")[0] != parameters["family"]: continue
                desired = "STOPPED" if row["lastStatus"] in {"STOPPED", "STOPPING", "DEPROVISIONING"} else "RUNNING"
                if desired == parameters["desiredStatus"]: rows.append(arn)
            return {"taskArns": rows, **({"nextToken": CANARY} if self.pagination else {})}
        if operation == "describe-tasks": return {"tasks": [copy.deepcopy(self.task_rows[arn]) for arn in parameters["tasks"]], "failures": []}
        if operation in {"update-service", "stop-task"}:
            self.before_write(operation, parameters)
            if self.denied_write: raise M.C.InfrastructureFailure("aws-access-denied")
            if operation == "update-service":
                assert parameters == {"cluster": M.C.RESOURCE.CLUSTER, "service": SERVICE_ARN, "desiredCount": 0}
                self.desired = 0
                if self.delayed: self.task_rows[SERVER]["lastStatus"] = "STOPPING"
                else: self.stopped(SERVER)
                if self.lost_service: raise OSError(CANARY)
            else:
                assert parameters["cluster"] == M.C.RESOURCE.CLUSTER and parameters["task"] in {MIGRATION, READER} and parameters["reason"].startswith("es-")
                if self.delayed: self.task_rows[parameters["task"]]["lastStatus"] = "STOPPING"
                else: self.stopped(parameters["task"])
                if self.lost_task: raise OSError(CANARY)
            return {}
        if operation == "describe-db-instances":
            return {"DBInstances": [{"DBInstanceIdentifier": M.C.ALIGN.DATABASE, "DbiResourceId": F.PARAMETERS["DatabaseResourceId"], "DBName": F.PARAMETERS["DatabaseName"],
                                     "DBInstanceStatus": "rebooting", "StorageEncrypted": True, "PubliclyAccessible": False, "Endpoint": {"Address": CANARY}, "MasterUsername": CANARY}]}
        try:
            value = super().__call__(service_name, operation, **parameters)
            if operation == "execute-change-set" and self.partial:
                self.stack["StackStatus"] = "CREATE_FAILED"
                self.resources = [row for row in self.resources if row["LogicalResourceId"] in {"ServerExecutionRole", "AdministrationExecutionRole"}]
            return value
        except F.R.ResourceMissing: raise M.C.RESOURCE.ResourceMissing() from None


def fails(call, code):
    try: call()
    except (M.RecoveryFailure, M.B.FailureBindingError, M.F.StopFailure, M.C.InfrastructureFailure, M.C.RESOURCE.ResourceFailure, M.C.GATE.ContractFailure) as failure:
        assert failure.code == code, (failure.code, code)
        return failure
    else: raise AssertionError("expected governed stop rejection")


@contextmanager
def scenario(*, partial=False, transport_factory=Transport):
    originals = {name: getattr(M.C, name) for name in ("ROOT", "source_digest", "local_checks")}
    old_read, old_source, old_artifact, old_repo = M.C.ALIGN.read_receipt, M.C.ALIGN.source_preflight, M.artifact, M.SUCCESSION.REPOSITORY_ROOT
    with tempfile.TemporaryDirectory(prefix="entity-smoke-failure-") as temporary:
        root = Path(temporary)
        scope = root / M.C.ALIGN.SCOPE
        scope.parent.mkdir(parents=True)
        scope.write_bytes((REAL_ROOT / M.C.ALIGN.SCOPE).read_bytes())
        inventory = scope.parent.parent.parent / "scope-index.yml"
        inventory.write_bytes((REAL_ROOT / M.C.ALIGN.SCOPE).parent.parent.parent.joinpath("scope-index.yml").read_bytes())
        evidence = scope.parent.parent / "30-release-evidence"; evidence.mkdir()
        M.C.ROOT, M.SUCCESSION.REPOSITORY_ROOT = root, root
        M.C.local_checks, M.C.source_digest = lambda: None, lambda: "sha256:" + "f" * 64
        M.artifact = lambda common=None: "sha256:" + "f" * 64
        receipt = {"source_revision": F.BINDING["source_revision"], "image_digest": F.BINDING["image_digest"], "receipt_reference": "controlled-not-qualification"}
        M.C.ALIGN.read_receipt, M.C.ALIGN.source_preflight = lambda path: receipt, lambda receipt: None
        binding = {**F.BINDING, "configuration_contract_sha256": M.C.digest_file(scope), "permission_contract_sha256": M.C.digest_file(M.C.DEPLOY.SOURCE)}
        transport = transport_factory()
        transport.partial, transport.service_present = partial, not partial
        cache = root / ".cache/entity-smoke-live" / binding["proof_label"]
        store = M.C.RESOURCE.ResourceStore(cache / "attempts")
        review = M.C.DEPLOY.prepare(transport, store, binding, F.PARAMETERS)
        try: created = M.C.DEPLOY.execute(transport, store, binding, F.PARAMETERS, review["facts"]["change_set_arn"], review["facts"]["stack_arn"])
        except M.C.RESOURCE.ResourceFailure as failure:
            assert partial and failure.code == "deployment-execution-not-successful"
        else: assert not partial and created["status"] == "completed"
        if not partial: transport.failed_runtime()
        def capability():
            result = provider_class()
            result._invoke = lambda service, operation, parameters: transport(service, operation, **parameters)
            return result
        provider_class = M.Provider
        args = SimpleNamespace(mode="plan", receipt=root / "controlled.json", proof_label=binding["proof_label"], approved_plan=None, wait_seconds=0, validate_arguments=False)
        yield SimpleNamespace(root=root, evidence=evidence, cache=cache, transport=transport, capability=capability, args=args,
                              binding=binding, custody=receipt, creation=None if partial else created)
    for name, value in originals.items(): setattr(M.C, name, value)
    M.C.ALIGN.read_receipt, M.C.ALIGN.source_preflight, M.artifact, M.SUCCESSION.REPOSITORY_ROOT = old_read, old_source, old_artifact, old_repo


def planned(case):
    result = M.run(case.args, case.capability())
    assert result["verdict"] == "planned" and result["plan"]["maximum_service_updates"] == 1 and result["plan"]["maximum_task_stops"] == 1
    assert result["plan"]["application_health_prerequisite"] is False and result["plan"]["database_mutation"] is False
    assert CANARY not in json.dumps(result) and "arn:" not in json.dumps(result)
    case.args.mode, case.args.approved_plan = "execute", result["plan_sha256"]
    return result


def run():
    with scenario() as case:
        result = planned(case)
        before = copy.deepcopy(case.transport.other)
        def reserved_before_call(operation, parameters):
            key = "service" if operation == "update-service" else M.F.task_key(parameters["task"])
            child = case.cache / "failure-attempts" / (key + ".json")
            assert child.is_file() and child.stat().st_mode & 0o777 == 0o600
            descriptor = os.open(case.evidence / ".release-succession.lock", os.O_RDWR)
            try:
                try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: pass
                else: raise AssertionError("stop must hold the actual succession lock at provider I/O")
            finally: os.close(descriptor)
        case.transport.before_write = reserved_before_call
        completed = M.run(case.args, case.capability())
        assert completed["verdict"] == "completed" and completed["independent_data_readback"] is False
        assert case.transport.other == before
        receipt = json.loads((case.root / completed["receipt"]).read_text())
        assert receipt["facts"]["terminal_tasks"][MIGRATION]["state"] == "STOPPED" and receipt["facts"]["migration_history_readback"] is False
        assert receipt["facts"]["source_database_after"]["state"] == "same-incarnation", "rebooting DB is not a stop prerequisite failure"
        repeated = M.run(case.args, case.capability())
        assert repeated["historical"] is True and repeated["current_scope_stopped"] is True
        assert sum(op == "update-service" for _, op, _ in case.transport.observed) == 1
        assert sum(op == "stop-task" for _, op, _ in case.transport.observed) == 1
        retained_path = case.root / completed["receipt"]
        original = retained_path.read_bytes(); changed = json.loads(original)
        changed["facts"]["independent_data_readback"] = True
        retained_path.write_text(json.dumps(changed))
        fails(lambda: M.run(case.args, case.capability()), "failure-retained-stopped-facts-invalid")
        retained_path.write_bytes(original)
        gate = case.root / receipt["realization_evidence"]
        original_gate = gate.read_bytes(); gate.write_text('{"native":"' + CANARY + '"}')
        fails(lambda: M.run(case.args, case.capability()), "failure-retained-gate-evidence-changed")
        gate.write_bytes(original_gate)
        assert sum(op in {"update-service", "stop-task"} for _, op, _ in case.transport.observed) == 2
        for path in case.cache.rglob("*.json"): assert CANARY not in path.read_text()

    for effect in ("service", "task"):
        with scenario() as case:
            planned(case)
            setattr(case.transport, "lost_" + effect, True)
            fails(lambda: M.run(case.args, case.capability()), "failure-submission-uncertain-reconcile-only")
            result = M.run(case.args, case.capability())
            assert result["verdict"] == "completed"
            assert sum(op == "update-service" for _, op, _ in case.transport.observed) == 1
            assert sum(op == "stop-task" for _, op, _ in case.transport.observed) == 1

    with scenario() as case:
        planned(case); case.transport.delayed = True
        assert M.run(case.args, case.capability())["verdict"] == "pending"
        assert M.run(case.args, case.capability())["verdict"] == "pending", "desired STOPPED and STOPPING is not terminal"
        assert sum(op == "stop-task" for _, op, _ in case.transport.observed) == 1
        case.transport.stopped(SERVER); case.transport.stopped(MIGRATION)
        assert M.run(case.args, case.capability())["verdict"] == "completed"
        assert sum(op == "stop-task" for _, op, _ in case.transport.observed) == 1

    with scenario() as case:
        planned(case); case.transport.other[0]["desiredCount"] = 2
        fails(lambda: M.run(case.args, case.capability()), "failure-other-service-configuration-changed")
        assert not any(op in {"stop-task", "update-service"} for _, op, _ in case.transport.observed)

    with scenario(partial=True) as case:
        result = M.run(case.args, case.capability())
        assert result["plan"]["maximum_service_updates"] == 0 and result["plan"]["maximum_task_stops"] == 0
        case.args.mode, case.args.approved_plan = "execute", result["plan_sha256"]
        assert M.run(case.args, case.capability())["verdict"] == "completed"
        assert not any(op in {"stop-task", "update-service"} for _, op, _ in case.transport.observed)

    with scenario() as case:
        data_binding = {**F.BINDING, "configuration_contract_sha256": M.C.digest_file(case.root / M.C.ALIGN.SCOPE), "permission_contract_sha256": M.C.digest_file(M.C.DEPLOY.SOURCE), "record_digest": "f" * 64}
        stack_name, change_name, database_name = M.RESTORE.names(data_binding)
        parameters = {key: F.PARAMETERS[key] for key in ("VpcId", "VpcCidr", "EndpointSecurityGroupId", "S3ArtifactPrefixListId", "LogGroupName", "ImageRepositoryUri", "ImageRepositoryArn", "ImageDigest", "SourceRevision")}
        parameters.update(DatabaseSubnetGroupName="kanbien-core-platform-persistence", RestoredDatabaseName="kanbienpersistence", RestoredDatabaseIdentifier=database_name,
                          SourceSnapshotArn="arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + case.args.proof_label, ProofLabel=case.args.proof_label)
        stack_arn = "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + stack_name + "/11111111-1111-1111-1111-111111111111"
        request = {**M.RESTORE.request(data_binding, parameters), "stack_arn": stack_arn,
                   "change_set_arn": "arn:aws:cloudformation:eu-west-1:337159794548:changeSet/" + change_name + "/22222222-2222-2222-2222-222222222222"}
        reservation, _ = M.C.RESOURCE.ResourceStore(case.cache / "attempts").reserve("execute-restore", request)
        definition_arn = PREFIX + "task-definition/kanbien-core-platform-entity-smoke-restore-reader:1"
        case.transport.clone = {"stack": {"StackName": stack_name, "StackId": stack_arn, "StackStatus": "CREATE_FAILED", "Tags": [{"Key": key, "Value": value} for key, value in M.RESTORE.tags(data_binding).items()],
                                          "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in parameters.items()]},
                                "operation_id": reservation["operation_id"], "resources": [{"LogicalResourceId": logical, "ResourceType": kind, "ResourceStatus": "CREATE_COMPLETE",
                                    "PhysicalResourceId": definition_arn if logical == "RestoreReaderTaskDefinition" else "own-" + logical} for logical, kind in M.RESTORE.RESOURCE_TYPES.items()],
                                "definition": {"family": "kanbien-core-platform-entity-smoke-restore-reader", "taskDefinitionArn": definition_arn, "status": "ACTIVE",
                                    "containerDefinitions": [{"name": "entity-smoke-restore-reader", "image": F.PARAMETERS["ImageRepositoryUri"] + "@" + F.PARAMETERS["ImageDigest"], "command": ["artifacts/kanbien-entity-smoke-database-proof.main.js"]}]}}
        case.transport.task_rows[READER] = {"taskArn": READER, "taskDefinitionArn": definition_arn, "lastStatus": "PENDING", "launchType": "FARGATE", "group": "family:kanbien-core-platform-entity-smoke-restore-reader"}
        result = M.run(case.args, case.capability())
        assert result["plan"]["maximum_task_stops"] == 2
        case.args.mode, case.args.approved_plan = "execute", result["plan_sha256"]
        assert M.run(case.args, case.capability())["verdict"] == "completed"
        assert len([row for _, operation, row in case.transport.observed if operation == "stop-task" and row["task"] == READER]) == 1

    with scenario() as case:
        case.transport.pagination = True
        fails(lambda: M.run(case.args, case.capability()), "failure-task-observation-incomplete")
        assert not any(op in {"stop-task", "update-service"} for _, op, _ in case.transport.observed)

    with scenario() as case:
        result = planned(case)
        case.transport.stack["StackStatus"] = "UPDATE_IN_PROGRESS"
        fails(lambda: M.run(case.args, case.capability()), "failure-stack-writer-not-terminal")
        case.transport.stack["StackStatus"] = "UPDATE_FAILED"
        case.transport.task_rows[MIGRATION]["taskDefinitionArn"] = case.transport.task_rows[MIGRATION]["taskDefinitionArn"].rsplit(":", 1)[0] + ":999"
        fails(lambda: M.run(case.args, case.capability()), "failure-task-ownership-not-confirmed")
        case.transport.task_rows[MIGRATION]["taskDefinitionArn"] = BF.RESOURCES["MigrationTaskDefinition"]["physical_id"]
        unexpected = PREFIX + "task/kanbien-core-platform/" + "9" * 32
        case.transport.task_rows[unexpected] = {**case.transport.task_rows[MIGRATION], "taskArn": unexpected}
        fails(lambda: M.run(case.args, case.capability()), "failure-unplanned-owned-task")
        del case.transport.task_rows[unexpected]
        assert not any(op in {"stop-task", "update-service"} for _, op, _ in case.transport.observed)
        original_current = M.SUCCESSION.current
        def acceptance_during_guard():
            target = case.evidence / ".release-succession.lock"
            if not target.exists(): return
            descriptor = os.open(target, os.O_RDWR)
            try:
                try: fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    M.SUCCESSION.current = lambda root: {"target": M.C.RESOURCE.CLUSTER, "scope": "entity-smoke", "release_id": "a" * 64}
                else: fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally: os.close(descriptor)
        case.transport.during_simulation = acceptance_during_guard
        fails(lambda: M.run(case.args, case.capability()), "failure-initial-policy-not-applicable")
        M.SUCCESSION.current = original_current
        assert not any(op in {"stop-task", "update-service"} for _, op, _ in case.transport.observed), "fresh custody is rechecked at the actual boundary"

    with scenario() as case:
        planned(case)
        case.transport.denied_write = True
        original_parse, original_factory = M.parse, M.Provider
        M.parse, M.Provider = lambda: case.args, case.capability
        output = io.StringIO()
        with redirect_stdout(output): status = M.main()
        rejected = json.loads(output.getvalue())
        assert status == 1 and rejected["condition"] == "failure-submission-uncertain-reconcile-only"
        assert rejected["context"]["provider_condition"] == "aws-access-denied" and rejected["effect"] == "unknown-reconcile-only"
        assert CANARY not in output.getvalue() and not (case.cache / "failure-receipts/stopped.json").exists()
        M.parse, M.Provider = original_parse, original_factory

    with scenario() as case:
        prepared = M.prepare(case.args, case.capability())
        store, packet = prepared["store"], prepared["packet"]
        root, _ = store.reserve("root", {"packet": packet})
        provider = case.capability()
        provider.enable_stop(root, store, lambda: (_ for _ in ()).throw(AssertionError("invalid payload reached the final guard")))
        payload = {"cluster": M.C.RESOURCE.CLUSTER, "service": SERVICE_ARN, "desiredCount": 0}
        store.reserve("service", {"root_sha256": M.C.DEPLOY.fingerprint(root), "operation": "update-service", "payload": payload})
        for change in ({"desiredCount": 1}, {"desiredCount": False}, {"cluster": "another-cluster"},
                       {"service": case.transport.other[0]["serviceArn"]}, {"forceNewDeployment": True}):
            fails(lambda: provider("ecs", "update-service", **{**payload, **change}), "failure-submission-does-not-match-plan")
        task_payload = {"cluster": M.C.RESOURCE.CLUSTER, "task": MIGRATION}
        child, _ = store.reserve(M.F.task_key(MIGRATION), {"root_sha256": M.C.DEPLOY.fingerprint(root), "operation": "stop-task", "payload": task_payload})
        for change in ({"reason": CANARY}, {"cluster": "another-cluster"}, {"extra": True}):
            fails(lambda: provider("ecs", "stop-task", **{**task_payload, "reason": child["operation_id"], **change}), "failure-submission-does-not-match-plan")
        fails(lambda: provider("ecs", "stop-task", cluster=M.C.RESOURCE.CLUSTER, task=SERVER, reason=child["operation_id"]), "failure-task-not-planned")
        assert not any(op in {"stop-task", "update-service"} for _, op, _ in case.transport.observed)

    with tempfile.TemporaryDirectory(prefix="entity-smoke-failure-cli-") as temporary:
        root = Path(temporary); marker = root / "aws-called"
        fake = root / "aws"; fake.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\nraise SystemExit(99)\n"); fake.chmod(0o700)
        environment = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
        common = ["--receipt", str(root / "missing.json"), "--proof-label", F.BINDING["proof_label"]]
        for wrapper, suffix, verdict in (("failure-plan.sh", ["--validate-arguments"], "valid"), ("failure-plan.sh", [], "blocked"),
                ("failure-plan.sh", ["--mode=execute", "--approved-plan", "sha256:" + "0" * 64], "blocked"),
                ("failure-stop.sh", ["--mode", "execute"], "blocked"), ("failure-plan.sh", ["--unknown", CANARY], "blocked")):
            result = subprocess.run(["bash", str(DIRECTORY / wrapper), *common, *suffix], cwd=REAL_ROOT, env=environment, capture_output=True, text=True)
            assert json.loads(result.stdout)["verdict"] == verdict and CANARY not in result.stdout + result.stderr and "Traceback" not in result.stderr
        assert not marker.exists()

    denied = M.Provider()
    denied._invoke = lambda *arguments: (_ for _ in ()).throw(AssertionError("unapproved mutation reached transport"))
    fails(lambda: denied("ecs", "update-service", cluster=M.C.RESOURCE.CLUSTER, service=SERVICE_ARN, desiredCount=0), "failure-provider-operation-prohibited")
    denied.enable(("cloudformation", "execute-change-set"), lambda *arguments: None)
    fails(lambda: denied("cloudformation", "execute-change-set", StackName=M.C.DEPLOY.STACK), "failure-provider-operation-prohibited")
    fails(lambda: denied("ecs", "run-task", cluster=M.C.RESOURCE.CLUSTER), "failure-provider-operation-prohibited")

    print(json.dumps({"schema": "deploy/entity-smoke-failure-route-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "prerequisites": "controlled-source-custody-local-proof-and-provider-transport-not-qualification", "checks": ["actual-control-plane-gates", "actual-custody-lock", "failed-unhealthy-and-unpulled-image", "rebooting-db-no-health-precondition", "queued-and-stopping-tasks", "original-plan-resume", "no-second-service-or-task-submission", "baseline-configurations-preserved", "no-data-readback-claim", "safe-private-receipts", "pagination-not-absence", "partial-creation", "owned-restore-reader", "terminal-writer-required", "exact-task-revision", "unplanned-task-rejected", "fresh-custody-at-io", "actual-main-preserves-provider-condition", "closed-effect-payloads", "tampered-retained-evidence-rejected", "offline-public-cli", "no-inherited-mutation-capability"]}))


if __name__ == "__main__": run()
