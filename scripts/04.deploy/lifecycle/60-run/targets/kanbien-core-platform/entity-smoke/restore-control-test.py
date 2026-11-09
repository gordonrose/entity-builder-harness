#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.restore-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise isolated restore review, lost-response reconciliation and owned cleanup with simulated provider responses, never live restore evidence.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

if not __debug__: raise SystemExit("ENTITY_SMOKE_RESTORE_CONTROL_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_restore_control_test", Path(__file__).with_name("restore-control.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
R = M.RESOURCE
CANARY = "credential-row-provider-canary"
BINDING = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64, "configuration_contract_sha256": "sha256:" + "c" * 64,
           "permission_contract_sha256": "sha256:" + "d" * 64, "dependency_incarnation_sha256": "sha256:" + "e" * 64,
           "proof_label": "entity-smoke-" + "f" * 24, "record_digest": "1" * 64}
STACK, CHANGE, DATABASE = M.names(BINDING)
STACK_ARN = "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + STACK + "/11111111-2222-3333-4444-555555555555"
CHANGE_ARN = "arn:aws:cloudformation:eu-west-1:337159794548:changeSet/" + CHANGE + "/11111111-2222-3333-4444-555555555555"
PARAMETERS = {"VpcId": "vpc-" + "1" * 17, "VpcCidr": "10.71.0.0/16", "EndpointSecurityGroupId": "sg-" + "2" * 17, "S3ArtifactPrefixListId": "pl-abc123", "LogGroupName": "/aws/ecs/kanbien-core-platform", "DatabaseSubnetGroupName": "private-database-group", "RestoredDatabaseName": "kanbienpersistence", "RestoredDatabaseIdentifier": DATABASE,
              "SourceSnapshotArn": "arn:aws:rds:eu-west-1:337159794548:snapshot:kanbien-core-platform-" + BINDING["proof_label"], "ProofLabel": BINDING["proof_label"],
              "ImageRepositoryUri": "337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/entity-smoke", "ImageRepositoryArn": "arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/entity-smoke", "ImageDigest": BINDING["image_digest"], "SourceRevision": BINDING["source_revision"]}
DEFINITION = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-restore-reader:1"
PHYSICAL = {"RestoreDatabaseSecurityGroup": "sg-" + "3" * 17, "RestoredDatabase": DATABASE, "RestoreReaderSecurityGroup": "sg-" + "4" * 17, "EndpointIngressFromRestoreReader": "sgr-" + "5" * 17, "RestoreReaderExecutionRole": "OwnedRestoreExecutionRole", "RestoreReaderTaskRole": "OwnedRestoreReaderRole", "RestoreReaderTaskDefinition": DEFINITION, "RestoreDatabaseIngressFromReader": "sgr-" + "6" * 17}


def reader_fixture():
    incarnation = M.digest({"resource_id": "db-RESTOREDABCDEFGHIJKLMNOP", "database": PARAMETERS["RestoredDatabaseName"], "schema": "entity_smoke"})
    request = {"workload": "restore-reader", "definition": DEFINITION, "image_digest": BINDING["image_digest"], "source_revision": BINDING["source_revision"],
               "configuration_contract_sha256": BINDING["configuration_contract_sha256"], "permission_contract_sha256": BINDING["permission_contract_sha256"], "dependency_incarnation_sha256": incarnation,
               "security_group": PHYSICAL["RestoreReaderSecurityGroup"], "subnets": ["subnet-" + "7" * 17], "environment": {"ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "restore-read", "ENTITY_SMOKE_PROOF_LABEL": BINDING["proof_label"], "ENTITY_SMOKE_EXPECTED_DIGEST": BINDING["record_digest"]}, "deadline_seconds": 180, "proof_label": BINDING["proof_label"]}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + "8" * 32, "request": request, "request_sha256": hashlib.sha256(R.CONTROL.canonical(request)).hexdigest(), "reserved_at": "2026-11-08T13:00:00Z"}
    task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "9" * 32, "taskDefinitionArn": DEFINITION, "startedBy": reservation["operation_id"], "overrides": R.CONTROL.overrides(request), "lastStatus": "STOPPED", "launchType": "FARGATE", "createdAt": "2026-11-08T13:00:01Z", "startedAt": "2026-11-08T13:00:02Z", "stoppedAt": "2026-11-08T13:00:05Z", "containers": [{"name": "entity-smoke-restore-reader", "imageDigest": BINDING["image_digest"], "exitCode": 0}]}
    result = {"schema": "deploy/entity-smoke-database-proof/v1", "verdict": "passed", "operation": "restore-read", "code": "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED", "record_digest": BINDING["record_digest"], "proof_label_sha256": hashlib.sha256(BINDING["proof_label"].encode()).hexdigest(), "steps": ["identity", "read"], "checked_at": "2026-11-08T13:00:04Z"}
    receipt = R.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(result)}]}, "2026-11-08T13:00:06Z")
    return task, reservation, receipt


class Provider:
    def __init__(self, lost=None, pending=False):
        self.calls, self.lost, self.pending = [], lost, pending
        self.state, self.change, self.execution_token, self.deleted = None, None, None, False
        self.task, self.reader_reservation, self.reader_receipt = reader_fixture()
        self.orphan_role, self.unknown_absence, self.wrong_reader_host, self.foreign_lineage = False, False, False, False
    def __call__(self, service_name, operation, **parameters):
        self.calls.append((service_name, operation, copy.deepcopy(parameters)))
        if operation == "describe-stacks":
            assert parameters["StackName"] in {STACK, STACK_ARN}
            if self.state is None: raise R.ResourceMissing()
            value = {"StackName": STACK, "StackId": STACK_ARN, "StackStatus": self.state}
            if self.state != "REVIEW_IN_PROGRESS": value.update(Tags=[{"Key": key, "Value": value} for key, value in M.tags(BINDING).items()], Parameters=[{"ParameterKey": key, "ParameterValue": value} for key, value in PARAMETERS.items()])
            return {"Stacks": [value]}
        if operation == "create-change-set":
            assert self.change is None and parameters["StackName"] == STACK and parameters["ChangeSetType"] == "CREATE" and parameters["OnStackFailure"] == "DO_NOTHING"
            assert parameters["Capabilities"] == ["CAPABILITY_IAM"] and M.CF.templates_equal(parameters["TemplateBody"], M.source()[0])
            self.state = "REVIEW_IN_PROGRESS"
            self.change = {"StackName": STACK, "StackId": STACK_ARN, "ChangeSetName": CHANGE, "ChangeSetId": CHANGE_ARN, "Description": parameters["Description"], "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "OnStackFailure": "DO_NOTHING", "Capabilities": ["CAPABILITY_IAM"], "Parameters": parameters["Parameters"], "Tags": parameters["Tags"], "Changes": [{"ResourceChange": {"Action": "Add", "LogicalResourceId": name, "ResourceType": kind}} for name, kind in M.RESOURCE_TYPES.items()]}
            if self.lost == operation: raise OSError(CANARY)
            return {}
        if operation == "describe-change-set":
            if self.change is None: raise R.ResourceMissing()
            return copy.deepcopy(self.change)
        if operation == "get-template":
            if "ChangeSetName" not in parameters: assert self.state != "REVIEW_IN_PROGRESS", "a CREATE review stack has no deployed body yet"
            return {"TemplateBody": M.source()[0]}
        if operation == "execute-change-set":
            assert self.state == "REVIEW_IN_PROGRESS" and parameters["StackName"] == STACK_ARN and parameters["ChangeSetName"] == CHANGE_ARN and set(parameters) == {"StackName", "ChangeSetName", "ClientRequestToken"}
            self.execution_token = parameters["ClientRequestToken"]
            self.state = "CREATE_IN_PROGRESS" if self.pending else "CREATE_COMPLETE"
            self.change["ExecutionStatus"] = "EXECUTE_COMPLETE"
            if self.lost == operation: raise OSError(CANARY)
            return {}
        if operation == "describe-stack-events":
            return {"StackEvents": [{"PhysicalResourceId": STACK_ARN, "ClientRequestToken": "wrong-actor" if self.foreign_lineage else self.execution_token}]}
        if operation == "list-stack-resources":
            return {"StackResourceSummaries": [{"LogicalResourceId": name, "ResourceType": kind, "PhysicalResourceId": PHYSICAL[name], "ResourceStatus": "CREATE_COMPLETE"} for name, kind in M.RESOURCE_TYPES.items()]}
        if operation == "describe-db-instances":
            assert parameters == {"DBInstanceIdentifier": DATABASE}, "the source database cannot be a restore/cleanup target"
            if self.state in {None, "REVIEW_IN_PROGRESS"}: raise R.ResourceMissing()
            if self.deleted:
                if self.unknown_absence: raise OSError(CANARY)
                raise R.ResourceMissing()
            return {"DBInstances": [{"DBInstanceIdentifier": DATABASE, "DbiResourceId": "db-RESTOREDABCDEFGHIJKLMNOP", "DBInstanceArn": "arn:aws:rds:eu-west-1:337159794548:db:" + DATABASE, "DBInstanceStatus": "available", "StorageEncrypted": True, "PubliclyAccessible": False, "IAMDatabaseAuthenticationEnabled": True, "DeletionProtection": False, "Engine": "postgres", "EngineVersion": "18.3", "DBName": PARAMETERS["RestoredDatabaseName"], "Endpoint": {"Address": "restored-provider-canary.internal"}}]}
        if operation == "list-tags-for-resource": return {"TagList": [{"Key": key, "Value": value} for key, value in M.tags(BINDING).items()]}
        if operation == "describe-tasks":
            assert parameters["tasks"] == [self.task["taskArn"]]
            return {"tasks": [copy.deepcopy(self.task)]}
        if operation == "list-tasks":
            return {"taskArns": [self.task["taskArn"]] if parameters["family"].endswith("-restore-reader") and parameters["desiredStatus"] == "STOPPED" else []}
        if operation == "describe-task-definition":
            assert parameters["taskDefinition"] == DEFINITION
            if self.deleted: return {"taskDefinition": {"taskDefinitionArn": DEFINITION, "status": "INACTIVE"}}
            env = {"NODE_ENV": "production", "PLATFORM_SOURCE_COMMIT_SHA": BINDING["source_revision"], "ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "restore-read", "PERSISTENCE_POSTGRES_HOST": "source-provider-canary.internal" if self.wrong_reader_host else "restored-provider-canary.internal", "PERSISTENCE_POSTGRES_PORT": "5432", "PERSISTENCE_POSTGRES_DATABASE": PARAMETERS["RestoredDatabaseName"], "PERSISTENCE_POSTGRES_SCHEMA": "entity_smoke", "PERSISTENCE_POSTGRES_CA_PATH": "/app/assets/rds-eu-west-1-bundle.crt", "PERSISTENCE_POSTGRES_IAM_REGION": "eu-west-1", "PERSISTENCE_RUNTIME_DATABASE_USERNAME": "entity_smoke_runtime", "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE": "arn:aws:rds-db:eu-west-1:337159794548:dbuser:db-RESTOREDABCDEFGHIJKLMNOP/entity_smoke_runtime", "PLATFORM_DEPLOYMENT_EXPOSURE": "private"}
            return {"taskDefinition": {"taskDefinitionArn": DEFINITION, "taskRoleArn": "arn:aws:iam::337159794548:role/" + PHYSICAL["RestoreReaderTaskRole"], "executionRoleArn": "arn:aws:iam::337159794548:role/" + PHYSICAL["RestoreReaderExecutionRole"], "containerDefinitions": [{"name": "entity-smoke-restore-reader", "image": PARAMETERS["ImageRepositoryUri"] + "@" + BINDING["image_digest"], "command": ["artifacts/kanbien-entity-smoke-database-proof.main.js"], "readonlyRootFilesystem": True, "linuxParameters": {"capabilities": {"drop": ["ALL"]}}, "environment": [{"name": key, "value": value} for key, value in env.items()]}]}}
        if operation == "delete-stack":
            assert parameters["StackName"] == STACK_ARN and set(parameters) == {"StackName", "ClientRequestToken"}
            self.state, self.deleted = "DELETE_COMPLETE", True
            if self.lost == operation: raise OSError(CANARY)
            return {}
        if operation == "describe-security-groups":
            assert set(parameters["GroupIds"]) <= {PHYSICAL["RestoreDatabaseSecurityGroup"], PHYSICAL["RestoreReaderSecurityGroup"]}
            assert self.deleted
            raise R.ResourceMissing()
        if operation == "get-role":
            assert parameters["RoleName"] in {PHYSICAL["RestoreReaderExecutionRole"], PHYSICAL["RestoreReaderTaskRole"]} and self.deleted
            if self.orphan_role: return {"Role": {"RoleName": parameters["RoleName"]}}
            raise R.ResourceMissing()
        raise AssertionError("unexpected simulated provider operation")


def fails(call, code):
    try: call()
    except R.ResourceFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected restore-control rejection")


def run():
    with tempfile.TemporaryDirectory(prefix="entity-smoke-restore-controls-") as temporary:
        root = Path(temporary)
        def store(name): return R.ResourceStore(root / name)
        def prepare(provider, owner): return M.prepare_restore(provider, owner, BINDING, PARAMETERS)
        def execute(provider, owner): return M.execute_restore(provider, owner, BINDING, PARAMETERS, CHANGE_ARN, STACK_ARN)
        def cleanup(provider, owner, deployment): return M.cleanup_restore(provider, owner, BINDING, PARAMETERS, deployment, provider.reader_reservation, provider.reader_receipt)
        provider, owner = Provider(), store("normal")
        reviewed = prepare(provider, owner)
        assert reviewed["status"] == "reviewed" and reviewed["facts"]["resource_count"] == 8
        assert prepare(provider, owner)["facts"] == reviewed["facts"]
        assert sum(op == "create-change-set" for _, op, _ in provider.calls) == 1
        deployment = execute(provider, owner)
        assert deployment["status"] == "completed" and deployment["facts"]["database_identifier"] != R.SOURCE_DATABASE
        assert execute(provider, owner)["facts"] == deployment["facts"]
        assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 1
        assert cleanup(provider, owner, deployment["facts"])["status"] == "completed"
        assert cleanup(provider, owner, deployment["facts"])["status"] == "completed"
        assert sum(op == "delete-stack" for _, op, _ in provider.calls) == 1
        # Acceptance receives only a read facade, with no reservation method,
        # and a provider that rejects every non-observation operation.
        class ReadStore:
            def read(self, phase, request): return owner.read(phase, request)
        allowed_reads = {("cloudformation", "describe-stacks"), ("rds", "describe-db-instances"),
                         ("ec2", "describe-security-groups"), ("iam", "get-role"), ("ecs", "describe-task-definition")}
        def read_only(service, operation, **parameters):
            assert (service, operation) in allowed_reads, "acceptance cannot submit any provider mutation"
            return provider(service, operation, **parameters)
        before_bytes = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.json")}
        observed = M.observe_cleanup(read_only, ReadStore(), BINDING, PARAMETERS, deployment["facts"], provider.reader_reservation, provider.reader_receipt)
        assert observed["status"] == "completed" and observed["facts"]["absence_observed"] is True
        assert observed["facts"]["source_mutation"] is False
        assert {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.json")} == before_bytes
        assert sum(op == "delete-stack" for _, op, _ in provider.calls) == 1
        unreserved = store("unreserved-read-only-observer")
        calls_before = len(provider.calls)
        fails(lambda: M.observe_cleanup(read_only, unreserved, BINDING, PARAMETERS, deployment["facts"], provider.reader_reservation, provider.reader_receipt), "restore-cleanup-journal-required")
        assert len(provider.calls) == calls_before and not unreserved.root.exists(), "absence cannot manufacture a cleanup reservation"
        provider.orphan_role = True
        assert M.observe_cleanup(read_only, ReadStore(), BINDING, PARAMETERS, deployment["facts"], provider.reader_reservation, provider.reader_receipt)["status"] == "pending"
        provider.orphan_role = False
        provider.unknown_absence = True
        fails(lambda: M.observe_cleanup(read_only, ReadStore(), BINDING, PARAMETERS, deployment["facts"], provider.reader_reservation, provider.reader_receipt), "restore-cleanup-observation-unavailable")
        provider.unknown_absence = False
        provider.state = "DELETE_IN_PROGRESS"
        assert M.observe_cleanup(read_only, ReadStore(), BINDING, PARAMETERS, deployment["facts"], provider.reader_reservation, provider.reader_receipt)["status"] == "pending"
        provider.state = "DELETE_COMPLETE"
        for operation in ("create-change-set", "execute-change-set", "delete-stack"):
            provider, owner = Provider(lost=operation), store("lost-" + operation)
            if operation == "create-change-set":
                fails(lambda: prepare(provider, owner), "restore-change-submission-uncertain-reconcile-only")
                assert prepare(provider, owner)["status"] == "reviewed"
            else:
                prepare(provider, owner)
                if operation == "execute-change-set":
                    fails(lambda: execute(provider, owner), "restore-execution-uncertain-reconcile-only")
                    assert execute(provider, owner)["status"] == "completed"
                else:
                    deployment = execute(provider, owner)
                    fails(lambda: cleanup(provider, owner, deployment["facts"]), "restore-cleanup-submission-uncertain-reconcile-only")
                    assert cleanup(provider, owner, deployment["facts"])["status"] == "completed"
            assert sum(op == operation for _, op, _ in provider.calls) == 1
        provider, owner = Provider(pending=True), store("pending")
        prepare(provider, owner)
        assert execute(provider, owner)["status"] == "pending"
        provider.state = "CREATE_COMPLETE"
        assert execute(provider, owner)["status"] == "completed"
        assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 1
        for index, (mutation, code) in enumerate([
            (lambda p: p.change.update(OnStackFailure="ROLLBACK"), "restore-change-not-ready"),
            (lambda p: p.change["Changes"][0]["ResourceChange"].update(Action="Modify"), "restore-change-shape-invalid"),
            (lambda p: p.change["Changes"].append({"ResourceChange": {"Action": "Add", "LogicalResourceId": "Unowned", "ResourceType": "AWS::RDS::DBInstance"}}), "restore-change-resource-set-invalid"),
            (lambda p: p.change.update(Description="unreserved-operation"), "restore-change-identity-not-confirmed"),
        ]):
            provider, owner = Provider(), store("bad-review-" + str(index)); prepare(provider, owner); mutation(provider)
            fails(lambda: execute(provider, owner), code)
            assert not any(op == "execute-change-set" for _, op, _ in provider.calls)
        provider, owner = Provider(), store("wrong-lineage"); prepare(provider, owner); provider.foreign_lineage = True
        fails(lambda: execute(provider, owner), "restore-execution-lineage-not-confirmed")
        provider, owner = Provider(), store("wrong-reader"); prepare(provider, owner); deployment = execute(provider, owner); provider.wrong_reader_host = True
        fails(lambda: cleanup(provider, owner, deployment["facts"]), "restore-reader-task-definition-not-confirmed")
        assert not any(op == "delete-stack" for _, op, _ in provider.calls)
        provider, owner = Provider(), store("nonterminal-reader"); prepare(provider, owner); deployment = execute(provider, owner); provider.task["lastStatus"] = "STOPPING"
        fails(lambda: cleanup(provider, owner, deployment["facts"]), "restore-reader-terminal-state-not-confirmed")
        assert not any(op == "delete-stack" for _, op, _ in provider.calls)
        provider, owner = Provider(), store("orphan"); prepare(provider, owner); deployment = execute(provider, owner); provider.orphan_role = True
        assert cleanup(provider, owner, deployment["facts"])["status"] == "pending"
        provider.orphan_role = False
        assert cleanup(provider, owner, deployment["facts"])["status"] == "completed"
        assert sum(op == "delete-stack" for _, op, _ in provider.calls) == 1
        provider, owner = Provider(), store("unknown-absence"); prepare(provider, owner); deployment = execute(provider, owner); provider.unknown_absence = True
        fails(lambda: cleanup(provider, owner, deployment["facts"]), "restore-cleanup-observation-unavailable")
        assert sum(op == "delete-stack" for _, op, _ in provider.calls) == 1
        provider.unknown_absence = False
        assert cleanup(provider, owner, deployment["facts"])["status"] == "completed"
        assert sum(op == "delete-stack" for _, op, _ in provider.calls) == 1
        provider, owner = Provider(), store("before-review")
        fails(lambda: execute(provider, owner), "restore-review-reservation-missing")
        assert provider.calls == [] and not owner.root.exists()
        provider, owner = Provider(), store("foreign-snapshot")
        wrong = {**PARAMETERS, "SourceSnapshotArn": "arn:aws:rds:eu-west-1:337159794548:snapshot:unowned"}
        fails(lambda: M.prepare_restore(provider, owner, BINDING, wrong), "restore-parameters-invalid")
        assert provider.calls == []
        assert all(CANARY not in path.read_text() for path in root.rglob("*.json"))
    print(json.dumps({"schema": "deploy/entity-smoke-restore-control-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "cases": ["exact-create-review", "review-stack-without-deployed-body", "single-execution", "retained-reader-before-cleanup", "observed-owned-absence", "read-only-observer-no-reserve-or-mutation", "read-only-observer-no-journal-no-io", "read-only-orphan-pending", "read-only-unknown-not-absence", "read-only-deletion-still-pending", "lost-review-no-replay", "lost-execution-no-replay", "lost-cleanup-no-replay", "pending-execution-resume", "unsafe-change-shape-rejected", "execution-lineage", "source-reader-route-rejected", "stopping-reader-blocks-delete", "orphan-remains-pending", "unknown-not-absence", "no-unreviewed-execution", "no-foreign-snapshot"]}))


if __name__ == "__main__": run()
