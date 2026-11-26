#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.deployment-control
#   version: 3
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual-template isolated creation and activation controls with lost responses, unsafe changes and immutable ownership counterexamples, not live AWS proof.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_DEPLOYMENT_CONTROL_ASSERTIONS_DISABLED")
SPEC = importlib.util.spec_from_file_location("entity_smoke_deployment_control_test", (Path(__file__).resolve().parents[2] / "controls-and-readiness/implementation/deployment-control.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
R = M.RESOURCE
CANARY = "private-provider-endpoint-canary.internal"
BINDING = {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64,
           "configuration_contract_sha256": "sha256:" + "c" * 64, "permission_contract_sha256": "sha256:" + "d" * 64,
           "dependency_incarnation_sha256": M.fingerprint({"resource_id": "db-ABCDEFGHIJKLMNOP", "database": "kanbienpersistence", "schema": "entity_smoke"}),
           "proof_label": "entity-smoke-" + "e" * 24}
PARAMETERS = {"VpcId": "vpc-" + "1" * 17, "VpcCidr": "10.71.0.0/16", "PrivateSubnetIds": "subnet-" + "2" * 17,
              "ClusterArn": "arn:aws:ecs:eu-west-1:337159794548:cluster/kanbien-core-platform", "NamespaceId": "ns-abc123",
              "EndpointSecurityGroupId": "sg-" + "3" * 17, "S3ArtifactPrefixListId": "pl-abc123", "LogGroupName": "/aws/ecs/kanbien-core-platform",
              "DatabaseEndpoint": CANARY, "DatabaseName": "kanbienpersistence", "DatabaseResourceId": "db-ABCDEFGHIJKLMNOP",
              "DatabaseSecurityGroupId": "sg-" + "4" * 17, "AdministratorSecretArn": "arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien-core-platform-persistence-migration-aBc123",
              "ImageRepositoryUri": "337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/entity-smoke",
              "ImageRepositoryArn": "arn:aws:ecr:eu-west-1:337159794548:repository/kanbien-core-platform/entity-smoke",
              "ImageDigest": BINDING["image_digest"], "SourceRevision": BINDING["source_revision"], "ServerDesiredCount": "0"}
STACK_ARN = "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + M.STACK + "/11111111-1111-1111-1111-111111111111"
SERVER_DEFINITION = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-server:1"
TASK = "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "1" * 32


class Provider:
    def __init__(self, *, lost_prepare=False, lost_execute=False, delayed=False):
        self.calls, self.changes, self.stack, self.tokens = [], {}, None, []
        self.lost_prepare, self.lost_execute, self.delayed = lost_prepare, lost_execute, delayed
        self.mutate_change = lambda value: None
        self.wrong_template, self.wrong_image, self.paginated_resources, self.paginated_events = False, False, False, False
        self.resources = [{"LogicalResourceId": name, "ResourceType": kind, "PhysicalResourceId": SERVER_DEFINITION if name == "ServerTaskDefinition" else "own-" + name, "ResourceStatus": "CREATE_COMPLETE"} for name, kind in M.RESOURCE_TYPES.items()]
    def __call__(self, service_name, operation, **parameters):
        self.calls.append((service_name, operation, copy.deepcopy(parameters)))
        if operation == "describe-stacks":
            assert parameters["StackName"] in {M.STACK, STACK_ARN}
            if self.stack is None: raise R.ResourceMissing()
            return {"Stacks": [copy.deepcopy(self.stack)]}
        if operation == "create-change-set":
            assert parameters["StackName"] == M.STACK
            activate = parameters["ChangeSetType"] == "UPDATE"
            assert activate or parameters["ChangeSetType"] == "CREATE" and parameters["OnStackFailure"] == "DO_NOTHING"
            assert not activate or "OnStackFailure" not in parameters
            value = {"StackName": M.STACK, "StackId": STACK_ARN, "ChangeSetName": parameters["ChangeSetName"],
                     "ChangeSetId": "arn:aws:cloudformation:eu-west-1:337159794548:changeSet/" + parameters["ChangeSetName"] + "/22222222-2222-2222-2222-222222222222",
                     "Description": parameters["Description"], "Status": "CREATE_COMPLETE", "ExecutionStatus": "AVAILABLE", "Capabilities": parameters["Capabilities"],
                     "Tags": parameters["Tags"], "Parameters": parameters["Parameters"], "Changes": [{"ResourceChange": {"LogicalResourceId": name, "ResourceType": kind, "Action": "Add"}} for name, kind in M.RESOURCE_TYPES.items()]}
            if activate:
                value["Changes"] = [{"ResourceChange": {"LogicalResourceId": "FeatureService", "ResourceType": "AWS::ECS::Service", "Action": "Modify", "Replacement": "False", "Scope": ["Properties"], "Details": [{"Target": {"Attribute": "Properties", "Name": "DesiredCount", "RequiresRecreation": "Never"}, "ChangeSource": "ParameterReference", "CausingEntity": "ServerDesiredCount"}]}}]
                details = value["Changes"][0]["ResourceChange"]["Details"]
                details[0]["Evaluation"] = "Static"
                details.append({"Target": copy.deepcopy(details[0]["Target"]), "Evaluation": "Dynamic", "ChangeSource": "DirectModification"})
                if parameters.get("UsePreviousTemplate"):
                    assert "TemplateBody" not in parameters
                    old = {row["ParameterKey"]: row["ParameterValue"] for row in self.stack["Parameters"]}
                    value["Parameters"] = [{"ParameterKey": row["ParameterKey"], "ParameterValue": old[row["ParameterKey"]] if row.get("UsePreviousValue") is True else row["ParameterValue"]} for row in parameters["Parameters"]]
                    value["Changes"] = []
                    for name, kind in M.RESOURCE_TYPES.items():
                        if not (name.endswith("TaskDefinition") or name == "FeatureService"): continue
                        task = name.endswith("TaskDefinition")
                        value["Changes"].append({"ResourceChange": {"LogicalResourceId": name, "ResourceType": kind, "Action": "Modify", "Replacement": "True" if task else "False", "Scope": ["Properties"],
                            "Details": [{"Target": {"Attribute": "Properties", "Name": "ContainerDefinitions" if task else "TaskDefinition", "RequiresRecreation": "Always" if task else "Never"},
                                         "ChangeSource": "ParameterReference" if task else "ResourceReference", "CausingEntity": "ImageDigest" if task else "ServerTaskDefinition", "Evaluation": "Static"}]}})
            else:
                value["OnStackFailure"] = "DO_NOTHING"
                assert self.stack is None
                # A real CREATE review stack has no deployed template yet.
                self.stack = {"StackName": M.STACK, "StackId": STACK_ARN, "StackStatus": "REVIEW_IN_PROGRESS", "Tags": []}
            self.changes[parameters["ChangeSetName"]] = value
            if self.lost_prepare: raise OSError(CANARY)
            return {}
        if operation == "describe-change-set":
            if parameters["ChangeSetName"] not in self.changes: raise R.ResourceMissing()
            value = copy.deepcopy(self.changes[parameters["ChangeSetName"]]); self.mutate_change(value)
            return value
        if operation == "get-template":
            assert "ChangeSetName" in parameters or self.stack["StackStatus"] != "REVIEW_IN_PROGRESS"
            return {"TemplateBody": "Resources: {}" if self.wrong_template else M.source()[0]}
        if operation == "execute-change-set":
            assert parameters["StackName"] == STACK_ARN
            matches = [change for change in self.changes.values() if change["ChangeSetId"] == parameters["ChangeSetName"]]
            assert len(matches) == 1
            change = matches[0]; activate = not change["ChangeSetName"].startswith("entity-smoke-create-")
            successor = any(row["ResourceChange"].get("Replacement") == "True" for row in change["Changes"])
            assert (parameters.get("DisableRollback") is (not successor)) if activate else "DisableRollback" not in parameters
            self.tokens.append(parameters["ClientRequestToken"])
            self.completed_at = datetime.now(timezone.utc).isoformat()
            self.stack.update(Tags=copy.deepcopy(change["Tags"]), Parameters=copy.deepcopy(change["Parameters"]), StackStatus=("UPDATE_IN_PROGRESS" if activate else "CREATE_IN_PROGRESS") if self.delayed else ("UPDATE_COMPLETE" if activate else "CREATE_COMPLETE"))
            change["ExecutionStatus"] = "EXECUTE_COMPLETE"
            # The executed change-set API object is not durable completion
            # evidence. Model its observed disappearance after execution.
            self.changes.clear()
            if self.lost_execute: raise OSError(CANARY)
            return {}
        if operation == "describe-stack-events":
            return {"StackEvents": [{"PhysicalResourceId": STACK_ARN, "ClientRequestToken": token, "ResourceStatus": "UPDATE_COMPLETE", "Timestamp": self.completed_at} for token in self.tokens], **({"NextToken": CANARY} if self.paginated_events else {})}
        if operation == "list-stack-resources":
            return {"StackResourceSummaries": copy.deepcopy(self.resources), **({"NextToken": CANARY} if self.paginated_resources else {})}
        desired = int(next(item["ParameterValue"] for item in self.stack["Parameters"] if item["ParameterKey"] == "ServerDesiredCount"))
        if operation == "describe-services":
            return {"services": [{"serviceName": R.SERVICE, "clusterArn": PARAMETERS["ClusterArn"], "taskDefinition": SERVER_DEFINITION, "status": "ACTIVE", "desiredCount": desired, "runningCount": desired, "pendingCount": 0}]}
        if operation == "list-tasks": return {"taskArns": [TASK] if desired else []}
        assert operation == "describe-tasks"
        digest = next(row["ParameterValue"] for row in self.stack["Parameters"] if row["ParameterKey"] == "ImageDigest")
        return {"tasks": [{"taskArn": TASK, "taskDefinitionArn": SERVER_DEFINITION, "group": "service:" + R.SERVICE, "launchType": "FARGATE", "lastStatus": "RUNNING", "healthStatus": "HEALTHY", "containers": [{"name": "entity-smoke-server", "imageDigest": "sha256:" + "0" * 64 if self.wrong_image else digest}]}]}


def fails(call, code):
    try: call()
    except R.ResourceFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected deployment-control rejection")


def delivery_fixture():
    identity = {"expected_predecessor": "release-" + "1" * 24,
                "predecessor": {"release_id": "release-" + "1" * 24, "source_revision": "1" * 40, "image_digest": "sha256:" + "2" * 64, "proof_set_sha256": "sha256:" + "3" * 64},
                "candidate": {"source_revision": BINDING["source_revision"], "image_digest": BINDING["image_digest"], "receipt_reference": "github-actions-run:123"},
                "contracts": {key: BINDING[key] for key in ("configuration_contract_sha256", "permission_contract_sha256")},
                "dependency_incarnation_sha256": BINDING["dependency_incarnation_sha256"], "proof_label": BINDING["proof_label"]}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"schema": "deploy/entity-smoke-delivery-context/v1", **identity, "delivery_id": digest, "smoke_label": "entity-smoke-" + digest[:24]}


def accepted_provider(provider, delivery):
    old = {**PARAMETERS, "ServerDesiredCount": "1", "ImageDigest": delivery["predecessor"]["image_digest"], "SourceRevision": delivery["predecessor"]["source_revision"]}
    provider.stack = {"StackName": M.STACK, "StackId": STACK_ARN, "StackStatus": "UPDATE_COMPLETE",
                      "Tags": [{"Key": key, "Value": value} for key, value in {"Target": R.CLUSTER, "Scope": "entity-smoke", "ProofLabel": BINDING["proof_label"]}.items()],
                      "Parameters": [{"ParameterKey": key, "ParameterValue": value} for key, value in old.items()]}
    return old


def successor_cases(root):
    delivery, active = delivery_fixture(), {**PARAMETERS, "ServerDesiredCount": "1"}
    provider = Provider(lost_prepare=True, lost_execute=True)
    old = accepted_provider(provider, delivery)
    provider.stack["StackStatus"] = "UPDATE_ROLLBACK_COMPLETE"
    store = R.ResourceStore(root / "successor")
    options = {"activate": True, "delivery": delivery, "previous_parameters": old}
    fails(lambda: M.prepare(provider, store, BINDING, active, **options), "deployment-change-submission-uncertain-reconcile-only")
    reviewed = M.prepare(provider, store, BINDING, active, **options)
    assert reviewed["status"] == "reviewed" and reviewed["facts"]["resource_count"] == 6
    submitted = next(arguments for _, operation, arguments in provider.calls if operation == "create-change-set")
    assert submitted["UsePreviousTemplate"] is True and "TemplateBody" not in submitted
    assert {row["ParameterKey"] for row in submitted["Parameters"] if row.get("UsePreviousValue") is True} == set(PARAMETERS) - {"ImageDigest", "SourceRevision"}
    assert [row for row in submitted["Parameters"] if "ParameterValue" in row] == [{"ParameterKey": "ImageDigest", "ParameterValue": active["ImageDigest"]}, {"ParameterKey": "SourceRevision", "ParameterValue": active["SourceRevision"]}]
    facts = reviewed["facts"]
    fails(lambda: M.execute(provider, store, BINDING, active, facts["change_set_arn"], facts["stack_arn"], **options), "deployment-execution-uncertain-reconcile-only")
    result = M.execute(provider, store, BINDING, active, facts["change_set_arn"], facts["stack_arn"], **options)
    assert result["status"] == "completed" and result["reservation"]["request"]["delivery"] == delivery
    assert sum(op == "create-change-set" for _, op, _ in provider.calls) == sum(op == "execute-change-set" for _, op, _ in provider.calls) == 1
    for status in ("UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS"):
        provider.stack["StackStatus"] = status
        assert M.execute(provider, store, BINDING, active, facts["change_set_arn"], facts["stack_arn"], **options)["status"] == "pending"
    for status in ("UPDATE_FAILED", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_FAILED"):
        provider.stack["StackStatus"] = status
        fails(lambda: M.execute(provider, store, BINDING, active, facts["change_set_arn"], facts["stack_arn"], **options), "deployment-execution-not-successful")
    provider.stack["StackStatus"] = "UPDATE_COMPLETE"
    assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 1
    provider.lost_prepare = provider.lost_execute = False
    rollback_binding = {**BINDING, "source_revision": old["SourceRevision"], "image_digest": old["ImageDigest"]}
    rollback = {"activate": True, "delivery": delivery, "previous_parameters": active, "rollback": True}
    restored_review = M.prepare(provider, store, rollback_binding, old, **rollback)
    restored = M.execute(provider, store, rollback_binding, old, restored_review["facts"]["change_set_arn"], STACK_ARN, **rollback)
    assert restored["status"] == "completed" and restored["reservation"]["operation_id"] != result["reservation"]["operation_id"]
    assert restored["reservation"]["phase"] == "deploy-execute-rollback"
    assert {row["ParameterKey"]: row["ParameterValue"] for row in provider.stack["Parameters"]} == old
    assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 2
    assert all(arguments["DisableRollback"] is False for _, op, arguments in provider.calls if op == "execute-change-set")
    for status in ("UPDATE_FAILED", "UPDATE_ROLLBACK_IN_PROGRESS", "UPDATE_ROLLBACK_FAILED"):
        unsafe = Provider(); accepted_provider(unsafe, delivery)
        unsafe.stack["StackStatus"] = status
        fails(lambda: M.prepare(unsafe, R.ResourceStore(root / status), BINDING, active, **options), "deployment-successor-precondition-not-confirmed")
        assert not any(op in {"create-change-set", "execute-change-set"} for _, op, _ in unsafe.calls)
    changed = Provider(); accepted_provider(changed, delivery)
    changed.stack["StackStatus"] = "UPDATE_ROLLBACK_COMPLETE"
    changed.stack["Parameters"][0]["ParameterValue"] = "wrong-restored-value"
    fails(lambda: M.prepare(changed, R.ResourceStore(root / "wrong-restored-parameters"), BINDING, active, **options), "deployment-provider-parameters-mismatch")
    assert not any(op in {"create-change-set", "execute-change-set"} for _, op, _ in changed.calls)
    untouched = Provider(); accepted_provider(untouched, delivery)
    fails(lambda: M.prepare(untouched, R.ResourceStore(root / "changed-network"), BINDING, {**active, "VpcCidr": "10.72.0.0/16"}, **options), "deployment-non-image-parameter-change-prohibited")
    assert untouched.calls == []
    for index, mutate in enumerate((lambda value: value.update(delivery_id="0" * 64), lambda value: value["predecessor"].update(image_digest="sha256:" + "0" * 64), lambda value: value.update(smoke_label=BINDING["proof_label"]))):
        invalid = copy.deepcopy(delivery); mutate(invalid)
        fails(lambda: M.prepare(untouched, R.ResourceStore(root / ("invalid-delivery-" + str(index))), BINDING, active, activate=True, delivery=invalid, previous_parameters=old), "resource-delivery-identity-mismatch")
    for index, mutate in enumerate((lambda row: row.update(Action="Remove"), lambda row: row.update(Replacement="False"),
                                   lambda row: row["Details"][0]["Target"].update(Name="TaskRoleArn"), lambda row: row["Details"][0].update(CausingEntity="DatabaseEndpoint"))):
        bad = Provider(); accepted_provider(bad, delivery)
        bad.mutate_change = lambda value, mutate=mutate: mutate(value["Changes"][0]["ResourceChange"])
        fails(lambda: M.prepare(bad, R.ResourceStore(root / ("unsafe-successor-" + str(index))), BINDING, active, **options), "deployment-change-shape-invalid" if index < 2 else "deployment-update-not-image-only")
        assert not any(op == "execute-change-set" for _, op, _ in bad.calls)
    for path in root.rglob("*.json"):
        assert CANARY not in path.read_text() and PARAMETERS["AdministratorSecretArn"] not in path.read_text()


if __name__ == "__main__":
    rows = [{"ParameterKey": key, "ParameterValue": value} for key, value in PARAMETERS.items()]
    M.exact_parameters(rows, PARAMETERS)
    for invalid in (None, {}, rows + [rows[0]], rows + [{"ParameterKey": "ImageDigest", "ParameterValue": CANARY}],
                    rows + [None], rows[:-1], [{"ParameterKey": key, "ParameterValue": None} for key in PARAMETERS]):
        fails(lambda: M.exact_parameters(invalid, PARAMETERS), "deployment-provider-parameters-mismatch")
    # The real feature binding must consume the shared reader, not a local copy.
    with patch.object(M.CHANGE_SETS, "parameter_values", return_value=None) as guard:
        fails(lambda: M.exact_parameters(rows, PARAMETERS), "deployment-provider-parameters-mismatch")
        guard.assert_called_once_with(rows)
    with tempfile.TemporaryDirectory(prefix="entity-smoke-deployment-controls-") as temporary:
        root = Path(temporary)
        def store(name): return R.ResourceStore(root / name)
        def create(provider, owner):
            review = M.prepare(provider, owner, BINDING, PARAMETERS)
            facts = review["facts"]
            return M.execute(provider, owner, BINDING, PARAMETERS, facts["change_set_arn"], facts["stack_arn"])
        provider, owner = Provider(lost_prepare=True), store("lost-prepare")
        fails(lambda: M.prepare(provider, owner, BINDING, PARAMETERS), "deployment-change-submission-uncertain-reconcile-only")
        review = M.prepare(provider, owner, BINDING, PARAMETERS)
        assert review["status"] == "reviewed" and review["facts"]["resource_count"] == 30
        assert sum(op == "create-change-set" for _, op, _ in provider.calls) == 1
        fails(lambda: M.prepare(provider, owner, {**BINDING, "configuration_contract_sha256": "sha256:" + "0" * 64}, PARAMETERS), "resource-reservation-mismatch")
        assert sum(op == "create-change-set" for _, op, _ in provider.calls) == 1
        provider.lost_execute = True
        facts = review["facts"]
        invoke = lambda: M.execute(provider, owner, BINDING, PARAMETERS, facts["change_set_arn"], facts["stack_arn"])
        fails(invoke, "deployment-execution-uncertain-reconcile-only")
        assert invoke()["status"] == "completed"
        assert invoke()["facts"]["desired_count"] == 0
        assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 1
        active = {**PARAMETERS, "ServerDesiredCount": "1"}
        provider.lost_prepare, provider.lost_execute = False, False
        activation = M.prepare(provider, owner, BINDING, active, activate=True)
        activated = M.execute(provider, owner, BINDING, active, activation["facts"]["change_set_arn"], activation["facts"]["stack_arn"], activate=True)
        assert activated["status"] == "completed" and activated["facts"]["desired_count"] == 1
        assert all(op not in {"run-task", "delete-stack", "delete-db-instance", "modify-db-instance"} for _, op, _ in provider.calls)
        provider.wrong_image = True
        fails(lambda: M.observe(provider, owner, BINDING, active, activation["facts"]["change_set_arn"], activation["facts"]["stack_arn"], activate=True), "resource-server-task-identity-not-confirmed")
        provider.paginated_resources = True
        fails(lambda: M.observe(provider, owner, BINDING, active, activation["facts"]["change_set_arn"], activation["facts"]["stack_arn"], activate=True), "deployment-resources-not-confirmed")
        invalid = {**PARAMETERS, "ImageDigest": "sha256:" + "0" * 64}
        fresh = Provider()
        fails(lambda: M.prepare(fresh, store("wrong-image"), BINDING, invalid), "deployment-parameters-invalid")
        assert fresh.calls == []
        invalid = {**PARAMETERS, "DatabaseResourceId": "db-OTHERINCARNATION"}
        fails(lambda: M.prepare(fresh, store("wrong-dependency"), BINDING, invalid), "deployment-dependency-incarnation-mismatch")
        assert fresh.calls == []
        fails(lambda: M.prepare(fresh, store("invented-record"), {**BINDING, "record_digest": "0" * 64}, PARAMETERS), "resource-binding-invalid")
        fails(lambda: R.validate_binding(BINDING), "resource-binding-invalid")
        assert fresh.calls == []
        existing = Provider(); existing.stack = {"StackName": M.STACK}
        fails(lambda: M.prepare(existing, store("existing"), BINDING, PARAMETERS), "deployment-stack-already-exists")
        assert not any(op == "create-change-set" for _, op, _ in existing.calls)
        unsafe = Provider()
        unsafe.mutate_change = lambda change: change["Parameters"].insert(0, {"ParameterKey": "ImageDigest", "ParameterValue": CANARY})
        fails(lambda: M.prepare(unsafe, store("ambiguous-parameters"), BINDING, PARAMETERS), "deployment-provider-parameters-mismatch")
        assert not any(op == "execute-change-set" for _, op, _ in unsafe.calls)
        unsafe = Provider()
        unsafe.mutate_change = lambda change: change["Changes"][0]["ResourceChange"].update(Action="Remove")
        fails(lambda: M.prepare(unsafe, store("delete"), BINDING, PARAMETERS), "deployment-change-shape-invalid")
        assert not any(op == "execute-change-set" for _, op, _ in unsafe.calls)
        unsafe = Provider()
        unsafe.mutate_change = lambda change: change["Changes"][0]["ResourceChange"].update(Replacement="True")
        fails(lambda: M.prepare(unsafe, store("replacement"), BINDING, PARAMETERS), "deployment-change-shape-invalid")
        template = Provider(); template.wrong_template = True
        fails(lambda: M.prepare(template, store("wrong-template"), BINDING, PARAMETERS), "deployment-change-template-mismatch")
        pending, owner = Provider(delayed=True), store("pending")
        result = create(pending, owner)
        assert result["status"] == "pending"
        pending.stack["StackStatus"] = "CREATE_COMPLETE"
        original_change = result["reservation"]["request"]["change_set_arn"]
        assert M.observe(pending, owner, BINDING, PARAMETERS, original_change, STACK_ARN)["status"] == "completed"
        assert sum(op == "execute-change-set" for _, op, _ in pending.calls) == 1
        pending.paginated_events = True
        assert M.observe(pending, owner, BINDING, PARAMETERS, original_change, STACK_ARN)["status"] == "completed"
        assert sum(op == "execute-change-set" for _, op, _ in pending.calls) == 1
        pending.tokens.clear()
        fails(lambda: M.observe(pending, owner, BINDING, PARAMETERS, original_change, STACK_ARN), "deployment-execution-lineage-not-confirmed")
        no_review = Provider()
        fails(lambda: M.execute(no_review, store("no-review"), BINDING, PARAMETERS, original_change, STACK_ARN), "deployment-review-reservation-missing")
        assert no_review.calls == []
        count_only, owner = Provider(), store("activation-shape")
        create(count_only, owner)
        count_only.mutate_change = lambda change: change["Changes"][0]["ResourceChange"]["Details"][0]["Target"].update(Name="TaskDefinition")
        fails(lambda: M.prepare(count_only, owner, BINDING, active, activate=True), "deployment-activation-not-count-only")
        assert sum(op == "execute-change-set" for _, op, _ in count_only.calls) == 1
        # Real AWS emits two evaluations of the same count property, not two
        # independent resource changes. Keep the legacy single-entry shape too.
        count_only.mutate_change = lambda change: None
        assert M.prepare(count_only, owner, BINDING, active, activate=True)["status"] == "reviewed"
        def details_of(change): return change["Changes"][0]["ResourceChange"]["Details"]
        for mutation in (
            lambda rows: rows[1]["Target"].update(Name="TaskDefinition"),
            lambda rows: rows[1].update(Evaluation="Static"),
            lambda rows: rows[1].update(CausingEntity="ServerDesiredCount"),
            lambda rows: rows[0].update(CausingEntity="OtherParameter"),
            lambda rows: rows[0].update(Evaluation=[CANARY]),
            lambda rows: rows.append(copy.deepcopy(rows[0])),
            lambda rows: rows.pop(0),
        ):
            count_only.mutate_change = lambda change, mutation=mutation: mutation(details_of(change))
            fails(lambda: M.prepare(count_only, owner, BINDING, active, activate=True), "deployment-activation-not-count-only")
        count_only.mutate_change = lambda change: details_of(change).pop()
        assert M.prepare(count_only, owner, BINDING, active, activate=True)["status"] == "reviewed"
        assert sum(op == "create-change-set" for _, op, _ in count_only.calls) == 2
        assert sum(op == "execute-change-set" for _, op, _ in count_only.calls) == 1
        missing, owner = Provider(lost_prepare=True), store("missing-after-loss")
        fails(lambda: M.prepare(missing, owner, BINDING, PARAMETERS), "deployment-change-submission-uncertain-reconcile-only")
        missing.changes.clear(); missing.stack = None
        assert M.prepare(missing, owner, BINDING, PARAMETERS)["status"] == "pending"
        assert sum(op == "create-change-set" for _, op, _ in missing.calls) == 1
        successor_cases(root)
        for path in root.rglob("*.json"):
            assert CANARY not in path.read_text() and PARAMETERS["AdministratorSecretArn"] not in path.read_text()
    print(json.dumps({"schema": "deploy/entity-smoke-deployment-control-fixture/v1", "verdict": "passed", "provider_observation": False,
                      "cases": ["exact-thirty-resource-create", "no-server-before-activation", "lost-create-no-replay", "changed-input-no-replay", "lost-execute-no-replay", "count-only-activation", "actual-service-image", "no-source-database-mutation", "incomplete-resources-rejected", "wrong-image-before-provider", "wrong-dependency-before-provider", "no-invented-record-digest", "existing-stack-not-adopted", "delete-rejected", "replacement-rejected", "prospective-template-mismatch", "pending-execution-observe-only", "missing-after-loss-not-resubmitted", "root-event-lineage", "review-required", "safe-private-retention"]}))
