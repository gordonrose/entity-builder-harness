#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.restore-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Review, execute and observe only the isolated restore stack and positively owned cleanup after retained original-record proof.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Internal execution helpers; no AWS CLI or authorization bypass.

The owning route must establish its normal realization gates, immutable image,
fresh alignment and explicit concrete creation/deletion authority before it
supplies a provider. All resource mutation calls below are single-submission.
"""
import hashlib
import json
from pathlib import Path
import re
import importlib.util


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


RESOURCE = module("entity_smoke_restore_resource_control", Path(__file__).with_name("resource-control.py"))
ROOT = Path(__file__).resolve().parents[7]
CF = module("entity_smoke_restore_cf", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
SOURCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke-isolated-restore.yml"
RESOURCE_TYPES = {"RestoreDatabaseSecurityGroup": "AWS::EC2::SecurityGroup", "RestoredDatabase": "AWS::RDS::DBInstance", "RestoreReaderSecurityGroup": "AWS::EC2::SecurityGroup", "EndpointIngressFromRestoreReader": "AWS::EC2::SecurityGroupIngress", "RestoreReaderExecutionRole": "AWS::IAM::Role", "RestoreReaderTaskRole": "AWS::IAM::Role", "RestoreReaderTaskDefinition": "AWS::ECS::TaskDefinition", "RestoreDatabaseIngressFromReader": "AWS::EC2::SecurityGroupIngress"}
PARAMETERS = {"VpcId", "VpcCidr", "EndpointSecurityGroupId", "S3ArtifactPrefixListId", "LogGroupName", "DatabaseSubnetGroupName", "RestoredDatabaseName", "RestoredDatabaseIdentifier", "SourceSnapshotArn", "ProofLabel", "ImageRepositoryUri", "ImageRepositoryArn", "ImageDigest", "SourceRevision"}
require, only, timestamp = RESOURCE.require, RESOURCE.only, RESOURCE.timestamp


def digest(value):
    return "sha256:" + hashlib.sha256(RESOURCE.CONTROL.canonical(value)).hexdigest()


def names(binding):
    RESOURCE.validate_binding(binding)
    label = binding["proof_label"].removeprefix("entity-smoke-")
    return "kanbien-core-platform-entity-smoke-restore-" + label, "entity-smoke-restore-" + label, "kanbien-core-platform-entity-smoke-restore-" + label[:16]


def source():
    RESOURCE.CONTROL.no_symlinks(SOURCE)
    try:
        text = SOURCE.read_text()
        value = CF.template(text)
    except (OSError, ValueError, TypeError): raise RESOURCE.ResourceFailure("restore-source-unavailable") from None
    require({key: item.get("Type") for key, item in value.get("Resources", {}).items()} == RESOURCE_TYPES and set(value.get("Parameters", {})) == PARAMETERS, "restore-source-resource-set-invalid")
    return text, value


def parameters_for(binding, parameters):
    stack, change, database = names(binding)
    _, template = source()
    require(isinstance(parameters, dict) and set(parameters) == PARAMETERS and all(isinstance(value, str) and value and "\n" not in value and "\0" not in value for value in parameters.values()), "restore-parameters-invalid")
    fixed = {"ProofLabel": binding["proof_label"], "ImageDigest": binding["image_digest"], "SourceRevision": binding["source_revision"], "RestoredDatabaseIdentifier": database,
             "SourceSnapshotArn": "arn:aws:rds:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":snapshot:kanbien-core-platform-" + binding["proof_label"],
             "ImageRepositoryUri": RESOURCE.ACCOUNT + ".dkr.ecr." + RESOURCE.REGION + ".amazonaws.com/kanbien-core-platform/entity-smoke",
             "ImageRepositoryArn": "arn:aws:ecr:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":repository/kanbien-core-platform/entity-smoke", "LogGroupName": "/aws/ecs/kanbien-core-platform"}
    require(all(parameters[key] == value for key, value in fixed.items()), "restore-parameters-invalid")
    for key, value in parameters.items():
        declaration = template["Parameters"][key]
        pattern = declaration.get("AllowedPattern")
        allowed = declaration.get("AllowedValues")
        if pattern is not None: require(re.fullmatch(pattern, value) is not None, "restore-parameters-invalid")
        if allowed is not None: require(value in allowed, "restore-parameters-invalid")
    require(re.fullmatch(r"vpc-(?:[a-f0-9]{8}|[a-f0-9]{17})", parameters["VpcId"]) is not None and re.fullmatch(r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", parameters["EndpointSecurityGroupId"]) is not None, "restore-parameters-invalid")
    return stack, change, database


def request(binding, parameters):
    parameters_for(binding, parameters)
    text, _ = source()
    return {"binding": binding, "parameters_sha256": digest(parameters), "template_sha256": "sha256:" + hashlib.sha256(text.encode()).hexdigest()}


def tags(binding):
    return {"Target": RESOURCE.CLUSTER, "Scope": "entity-smoke", "ProofLabel": binding["proof_label"]}


def exact_tags(value, binding):
    require(isinstance(value, list) and len(value) <= 50 and all(isinstance(item, dict) and isinstance(item.get("Key"), str) and isinstance(item.get("Value"), str) for item in value), "restore-ownership-not-confirmed")
    mapped = {item["Key"]: item["Value"] for item in value}
    require(len(mapped) == len(value) and all(mapped.get(key) == content for key, content in tags(binding).items()), "restore-ownership-not-confirmed")


def reviewed_change(provider, binding, parameters, reservation):
    stack, change, _ = parameters_for(binding, parameters)
    value = provider("cloudformation", "describe-change-set", StackName=stack, ChangeSetName=change)
    require(isinstance(value, dict) and value.get("StackName") == stack and value.get("ChangeSetName") == change and value.get("Description") == reservation["operation_id"] and not value.get("NextToken"), "restore-change-identity-not-confirmed")
    if value.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}: return None
    require(value.get("Status") == "CREATE_COMPLETE" and value.get("ExecutionStatus") == "AVAILABLE" and value.get("OnStackFailure") == "DO_NOTHING" and value.get("Capabilities") in (["CAPABILITY_IAM"], ["CAPABILITY_NAMED_IAM"]) and value.get("IncludeNestedStacks", False) is False and value.get("ImportExistingResources", False) is False and not value.get("RoleARN") and not value.get("NotificationARNs"), "restore-change-not-ready")
    exact_tags(value.get("Tags"), binding)
    observed_parameters = value.get("Parameters")
    require(isinstance(observed_parameters, list) and len(observed_parameters) == len(parameters) and all(isinstance(item, dict) and isinstance(item.get("ParameterKey"), str) and isinstance(item.get("ParameterValue"), str) for item in observed_parameters) and {item["ParameterKey"]: item["ParameterValue"] for item in observed_parameters} == parameters, "restore-change-parameters-mismatch")
    changes = value.get("Changes")
    require(isinstance(changes, list) and len(changes) == len(RESOURCE_TYPES), "restore-change-resource-set-invalid")
    actual = {}
    for item in changes:
        change_resource = item.get("ResourceChange") if isinstance(item, dict) else None
        require(isinstance(change_resource, dict) and change_resource.get("Action") == "Add" and change_resource.get("Replacement", "False") == "False" and change_resource.get("LogicalResourceId") not in actual, "restore-change-shape-invalid")
        actual[change_resource.get("LogicalResourceId")] = change_resource.get("ResourceType")
    require(actual == RESOURCE_TYPES, "restore-change-resource-set-invalid")
    change_id = value.get("ChangeSetId")
    require(isinstance(change_id, str) and re.fullmatch(r"arn:aws:cloudformation:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":changeSet/" + change + r"/[A-Za-z0-9-]+", change_id) is not None, "restore-change-identity-not-confirmed")
    actual_template = provider("cloudformation", "get-template", StackName=stack, ChangeSetName=change_id, TemplateStage="Original")
    require(isinstance(actual_template, dict) and CF.templates_equal(actual_template.get("TemplateBody"), source()[0]), "restore-change-template-mismatch")
    stack_arn = value.get("StackId")
    require(isinstance(stack_arn, str) and re.fullmatch(r"arn:aws:cloudformation:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":stack/" + stack + r"/[A-Za-z0-9-]+", stack_arn) is not None, "restore-change-identity-not-confirmed")
    return {"change_set_arn": change_id, "stack_arn": stack_arn, "resource_count": len(actual), "template_sha256": request(binding, parameters)["template_sha256"]}


def prepare_restore(provider, store, binding, parameters):
    stack, change, identifier = parameters_for(binding, parameters)
    intent = request(binding, parameters)
    reservation, fresh = store.reserve("restore-change-set", intent)
    if fresh:
        try: provider("cloudformation", "describe-stacks", StackName=stack)
        except RESOURCE.ResourceMissing: pass
        except Exception: raise RESOURCE.ResourceFailure("restore-stack-precondition-unavailable") from None
        else: raise RESOURCE.ResourceFailure("restore-stack-already-exists")
        try: provider("rds", "describe-db-instances", DBInstanceIdentifier=identifier)
        except RESOURCE.ResourceMissing: pass
        except Exception: raise RESOURCE.ResourceFailure("restore-database-precondition-unavailable") from None
        else: raise RESOURCE.ResourceFailure("restore-database-already-exists")
        try:
            provider("cloudformation", "create-change-set", StackName=stack, ChangeSetName=change, ChangeSetType="CREATE", TemplateBody=source()[0],
                     Parameters=[{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())],
                     Capabilities=["CAPABILITY_IAM"], OnStackFailure="DO_NOTHING", Description=reservation["operation_id"], ClientToken=reservation["operation_id"],
                     Tags=[{"Key": key, "Value": value} for key, value in tags(binding).items()])
        except RESOURCE.SubmissionNotStarted: raise
        except Exception: raise RESOURCE.ResourceFailure("restore-change-submission-uncertain-reconcile-only") from None
    try: reviewed = reviewed_change(provider, binding, parameters, reservation)
    except RESOURCE.ResourceMissing: return {"status": "pending", "reservation": reservation}
    return {"status": "reviewed" if reviewed is not None else "pending", "reservation": reservation, "facts": reviewed}


def restore_stack(provider, binding, parameters, observed=None):
    stack, _, database = parameters_for(binding, parameters)
    value = observed if observed is not None else only(provider("cloudformation", "describe-stacks", StackName=stack), "Stacks")
    require(value.get("StackName") == stack and isinstance(value.get("StackId"), str) and re.fullmatch(r"arn:aws:cloudformation:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":stack/" + stack + r"/[A-Za-z0-9-]+", value["StackId"]) is not None, "restore-stack-identity-not-confirmed")
    exact_tags(value.get("Tags"), binding)
    require({item.get("ParameterKey"): item.get("ParameterValue") for item in value.get("Parameters", [])} == parameters, "restore-stack-parameters-mismatch")
    template = provider("cloudformation", "get-template", StackName=value["StackId"], TemplateStage="Original")
    require(isinstance(template, dict) and CF.templates_equal(template.get("TemplateBody"), source()[0]), "restore-stack-template-mismatch")
    return value


def resource_map(provider, stack):
    response = provider("cloudformation", "list-stack-resources", StackName=stack["StackId"])
    summaries = response.get("StackResourceSummaries") if isinstance(response, dict) else None
    require(isinstance(summaries, list) and len(summaries) == len(RESOURCE_TYPES) and not response.get("NextToken"), "restore-resources-not-confirmed")
    require({item.get("LogicalResourceId"): item.get("ResourceType") for item in summaries} == RESOURCE_TYPES and all(isinstance(item.get("PhysicalResourceId"), str) and item["PhysicalResourceId"] and item.get("ResourceStatus") == "CREATE_COMPLETE" for item in summaries), "restore-resources-not-confirmed")
    return {item["LogicalResourceId"]: {"type": item["ResourceType"], "physical_id": item["PhysicalResourceId"]} for item in summaries}


def observe_restore(provider, store, binding, parameters, change_set_arn, stack_arn):
    intent = {**request(binding, parameters), "change_set_arn": change_set_arn, "stack_arn": stack_arn}
    execution = store.read("execute-restore", intent)
    require(execution is not None, "restore-execution-reservation-missing")
    observed = only(provider("cloudformation", "describe-stacks", StackName=stack_arn), "Stacks")
    require(observed.get("StackId") == stack_arn and observed.get("StackName") == names(binding)[0], "restore-stack-identity-not-confirmed")
    if observed.get("StackStatus") == "REVIEW_IN_PROGRESS": return {"status": "pending", "reservation": execution}
    value = restore_stack(provider, binding, parameters, observed)
    events = provider("cloudformation", "describe-stack-events", StackName=value["StackId"])
    records = events.get("StackEvents") if isinstance(events, dict) else None
    require(isinstance(records, list) and not events.get("NextToken") and any(item.get("PhysicalResourceId") == value["StackId"] and item.get("ClientRequestToken") == execution["operation_id"] for item in records), "restore-execution-lineage-not-confirmed")
    if value.get("StackStatus") == "CREATE_IN_PROGRESS": return {"status": "pending", "reservation": execution}
    require(value.get("StackStatus") == "CREATE_COMPLETE", "restore-execution-not-successful")
    resources = resource_map(provider, value)
    identifier = names(binding)[2]
    require(resources["RestoredDatabase"]["physical_id"] == identifier and identifier != RESOURCE.SOURCE_DATABASE, "restore-database-identity-not-confirmed")
    database = only(provider("rds", "describe-db-instances", DBInstanceIdentifier=identifier), "DBInstances")
    require(database.get("DBInstanceIdentifier") == identifier and database.get("DBInstanceStatus") == "available" and database.get("StorageEncrypted") is True and database.get("PubliclyAccessible") is False and database.get("IAMDatabaseAuthenticationEnabled") is True and database.get("DeletionProtection") is False and database.get("Engine") == "postgres" and database.get("EngineVersion") == "18.3" and database.get("DBName") == parameters["RestoredDatabaseName"], "restore-database-posture-not-confirmed")
    require(isinstance(database.get("DbiResourceId"), str) and re.fullmatch(r"db-[A-Za-z0-9]+", database["DbiResourceId"]) is not None, "restore-database-identity-not-confirmed")
    require(digest({"resource_id": database["DbiResourceId"], "database": database["DBName"], "schema": "entity_smoke"}) != binding["dependency_incarnation_sha256"], "restore-database-not-isolated")
    own_tags = provider("rds", "list-tags-for-resource", ResourceName=database.get("DBInstanceArn"))
    exact_tags(own_tags.get("TagList") if isinstance(own_tags, dict) else None, binding)
    return {"status": "completed", "reservation": execution, "facts": {"stack_arn": value["StackId"], "database_identifier": identifier, "restored_resource_id": database["DbiResourceId"], "resources": resources, "resources_sha256": digest(resources)}}


def execute_restore(provider, store, binding, parameters, change_set_arn, stack_arn):
    review_intent = request(binding, parameters)
    review_reservation = store.read("restore-change-set", review_intent)
    require(review_reservation is not None, "restore-review-reservation-missing")
    intent = {**review_intent, "change_set_arn": change_set_arn, "stack_arn": stack_arn}
    execution, fresh = store.reserve("execute-restore", intent)
    if fresh:
        review = reviewed_change(provider, binding, parameters, review_reservation)
        require(isinstance(review, dict) and review["change_set_arn"] == change_set_arn and review["stack_arn"] == stack_arn, "restore-change-not-ready")
        stack = only(provider("cloudformation", "describe-stacks", StackName=stack_arn), "Stacks")
        # A CREATE review stack need not have deployed parameters/template yet;
        # the exact prospective body was checked on the change set above.
        require(stack.get("StackStatus") == "REVIEW_IN_PROGRESS" and stack.get("StackId") == stack_arn and stack.get("StackName") == names(binding)[0], "restore-stack-precondition-not-confirmed")
        try: provider("cloudformation", "execute-change-set", StackName=stack["StackId"], ChangeSetName=change_set_arn, ClientRequestToken=execution["operation_id"])
        except RESOURCE.SubmissionNotStarted: raise
        except Exception: raise RESOURCE.ResourceFailure("restore-execution-uncertain-reconcile-only") from None
    return observe_restore(provider, store, binding, parameters, change_set_arn, stack_arn)


def validate_reader(provider, binding, parameters, resources, database, reservation, receipt, *, historical=False):
    require(type(historical) is bool, "restore-reader-observation-mode-invalid")
    try: retained = RESOURCE.EVIDENCE.validate_retained(receipt, reservation)
    except RESOURCE.EVIDENCE.EvidenceFailure: raise RESOURCE.ResourceFailure("restore-reader-receipt-not-confirmed") from None
    require(retained["workload"] == "restore-reader" and retained["operation"] == "restore-read" and retained["source_revision"] == binding["source_revision"] and retained["image_digest"] == binding["image_digest"] and retained["result"].get("record_digest") == binding["record_digest"] and retained["result"].get("proof_label_sha256") == hashlib.sha256(binding["proof_label"].encode()).hexdigest() and retained["task"]["definition"] == resources["RestoreReaderTaskDefinition"]["physical_id"], "restore-reader-identity-not-confirmed")
    incarnation = digest({"resource_id": database["DbiResourceId"], "database": parameters["RestoredDatabaseName"], "schema": "entity_smoke"})
    require(retained["dependency_incarnation_sha256"] == incarnation and incarnation != binding["dependency_incarnation_sha256"], "restore-reader-dependency-not-confirmed")
    if not historical:
        task = only(provider("ecs", "describe-tasks", cluster=RESOURCE.CLUSTER, tasks=[retained["task"]["arn"]]), "tasks")
        try:
            current = RESOURCE.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(retained["result"])}]}, retained["collected_at"])
        except RESOURCE.EVIDENCE.EvidenceFailure: raise RESOURCE.ResourceFailure("restore-reader-terminal-state-not-confirmed") from None
        require(current == retained, "restore-reader-terminal-state-not-confirmed")
    definition = provider("ecs", "describe-task-definition", taskDefinition=retained["task"]["definition"]).get("taskDefinition")
    require(isinstance(definition, dict) and definition.get("taskDefinitionArn") == retained["task"]["definition"], "restore-reader-task-definition-not-confirmed")
    for field, logical in (("taskRoleArn", "RestoreReaderTaskRole"), ("executionRoleArn", "RestoreReaderExecutionRole")):
        require(definition.get(field) == "arn:aws:iam::" + RESOURCE.ACCOUNT + ":role/" + resources[logical]["physical_id"], "restore-reader-task-definition-not-confirmed")
    containers = definition.get("containerDefinitions")
    require(isinstance(containers, list) and len(containers) == 1, "restore-reader-task-definition-not-confirmed")
    container = containers[0]
    environment = container.get("environment")
    require(isinstance(environment, list) and all(isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("value"), str) for item in environment), "restore-reader-task-definition-not-confirmed")
    env = {item["name"]: item["value"] for item in environment}
    expected = {"NODE_ENV": "production", "PLATFORM_SOURCE_COMMIT_SHA": binding["source_revision"], "ENTITY_SMOKE_DATABASE_PROOF_OPERATION": "restore-read", "PERSISTENCE_POSTGRES_HOST": database.get("Endpoint", {}).get("Address"), "PERSISTENCE_POSTGRES_PORT": "5432", "PERSISTENCE_POSTGRES_DATABASE": parameters["RestoredDatabaseName"], "PERSISTENCE_POSTGRES_SCHEMA": "entity_smoke", "PERSISTENCE_POSTGRES_CA_PATH": "/app/assets/rds-eu-west-1-bundle.crt", "PERSISTENCE_POSTGRES_IAM_REGION": RESOURCE.REGION, "PERSISTENCE_RUNTIME_DATABASE_USERNAME": "entity_smoke_runtime", "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE": "arn:aws:rds-db:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":dbuser:" + database["DbiResourceId"] + "/entity_smoke_runtime", "PLATFORM_DEPLOYMENT_EXPOSURE": "private"}
    require(len(env) == len(environment) and env == expected and container.get("name") == "entity-smoke-restore-reader" and container.get("command") == ["artifacts/kanbien-entity-smoke-database-proof.main.js"] and container.get("image") == parameters["ImageRepositoryUri"] + "@" + binding["image_digest"] and not container.get("secrets") and container.get("readonlyRootFilesystem") is True and container.get("privileged", False) is False and not container.get("entryPoint") and container.get("linuxParameters", {}).get("capabilities") == {"drop": ["ALL"]}, "restore-reader-task-definition-not-confirmed")
    return retained


def absent(provider, service_name, operation, **parameters):
    try: provider(service_name, operation, **parameters)
    except RESOURCE.ResourceMissing: return True
    except Exception: raise RESOURCE.ResourceFailure("restore-cleanup-observation-unavailable") from None
    return False


def cleanup_identity(binding, parameters, deployment, reader_reservation, reader_receipt):
    """Validate retained ownership/readback without provider calls or writes."""
    stack_name, _, identifier = parameters_for(binding, parameters)
    require(isinstance(deployment, dict) and set(deployment) == {"stack_arn", "database_identifier", "restored_resource_id", "resources", "resources_sha256"} and deployment["database_identifier"] == identifier and deployment["resources_sha256"] == digest(deployment["resources"]), "restore-cleanup-deployment-not-confirmed")
    resources = deployment["resources"]
    require(isinstance(resources, dict) and set(resources) == set(RESOURCE_TYPES) and all(isinstance(value, dict) and set(value) == {"type", "physical_id"} and value["type"] == RESOURCE_TYPES[key] and isinstance(value["physical_id"], str) and value["physical_id"] for key, value in resources.items()) and resources["RestoredDatabase"]["physical_id"] == identifier and identifier != RESOURCE.SOURCE_DATABASE, "restore-cleanup-ownership-not-confirmed")
    for logical in ("RestoreDatabaseSecurityGroup", "RestoreReaderSecurityGroup"):
        require(re.fullmatch(r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", resources[logical]["physical_id"]) is not None, "restore-cleanup-physical-identity-invalid")
    for logical in ("RestoreReaderExecutionRole", "RestoreReaderTaskRole"):
        require(re.fullmatch(r"[A-Za-z0-9+=,.@_-]{1,64}", resources[logical]["physical_id"]) is not None, "restore-cleanup-physical-identity-invalid")
    require(re.fullmatch(r"arn:aws:ecs:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + r":task-definition/kanbien-core-platform-entity-smoke-restore-reader:[1-9][0-9]*", resources["RestoreReaderTaskDefinition"]["physical_id"]) is not None, "restore-cleanup-physical-identity-invalid")
    # The complete retained reader remains a prerequisite on every invocation,
    # including after deletion. Do not replace it with exit code/health alone.
    try: retained = RESOURCE.EVIDENCE.validate_retained(reader_receipt, reader_reservation)
    except RESOURCE.EVIDENCE.EvidenceFailure: raise RESOURCE.ResourceFailure("restore-reader-receipt-not-confirmed") from None
    require(retained["workload"] == "restore-reader" and retained["operation"] == "restore-read" and retained["source_revision"] == binding["source_revision"] and retained["image_digest"] == binding["image_digest"] and retained["result"].get("record_digest") == binding["record_digest"] and retained["task"]["definition"] == resources["RestoreReaderTaskDefinition"]["physical_id"], "restore-reader-identity-not-confirmed")
    intent = {"binding": binding, "stack_arn": deployment["stack_arn"], "restored_resource_id": deployment["restored_resource_id"], "resources_sha256": deployment["resources_sha256"], "reader_task_arn": retained["task"]["arn"], "reader_receipt_sha256": digest(retained)}
    return stack_name, identifier, resources, intent, retained


def observe_cleanup(provider, store, binding, parameters, deployment, reader_reservation, reader_receipt):
    """Observe only an existing cleanup journal; never reserve or delete.

    This is the acceptance boundary. Absence without a positively bound original
    journal and retained reader is not cleanup proof. The provider is used only
    for the closed describe/get operations below.
    """
    stack_name, identifier, resources, intent, _ = cleanup_identity(binding, parameters, deployment, reader_reservation, reader_receipt)
    reservation = store.read("delete-restore", intent)
    require(reservation is not None, "restore-cleanup-journal-required")
    try: stack = only(provider("cloudformation", "describe-stacks", StackName=deployment["stack_arn"]), "Stacks")
    except RESOURCE.ResourceMissing: stack = None
    if stack is not None:
        require(stack.get("StackId") == deployment["stack_arn"] and stack.get("StackName") == stack_name, "restore-cleanup-stack-identity-not-confirmed")
        if stack.get("StackStatus") == "DELETE_IN_PROGRESS": return {"status": "pending", "reservation": reservation}
        require(stack.get("StackStatus") == "DELETE_COMPLETE", "restore-cleanup-not-confirmed")
    checks = [("rds", "describe-db-instances", {"DBInstanceIdentifier": identifier})]
    for logical in ("RestoreDatabaseSecurityGroup", "RestoreReaderSecurityGroup"):
        physical = resources[logical]["physical_id"]
        require(re.fullmatch(r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", physical) is not None, "restore-cleanup-physical-identity-invalid")
        checks.append(("ec2", "describe-security-groups", {"GroupIds": [physical]}))
    for logical in ("RestoreReaderExecutionRole", "RestoreReaderTaskRole"):
        physical = resources[logical]["physical_id"]
        require(re.fullmatch(r"[A-Za-z0-9+=,.@_-]{1,64}", physical) is not None, "restore-cleanup-physical-identity-invalid")
        checks.append(("iam", "get-role", {"RoleName": physical}))
    for family, operation, arguments in checks:
        if not absent(provider, family, operation, **arguments): return {"status": "pending", "reservation": reservation}
    try:
        definition = provider("ecs", "describe-task-definition", taskDefinition=resources["RestoreReaderTaskDefinition"]["physical_id"]).get("taskDefinition")
        require(isinstance(definition, dict) and definition.get("taskDefinitionArn") == resources["RestoreReaderTaskDefinition"]["physical_id"], "restore-cleanup-task-definition-not-confirmed")
        if definition.get("status") != "INACTIVE": return {"status": "pending", "reservation": reservation}
    except RESOURCE.ResourceMissing: pass
    return {"status": "completed", "reservation": reservation, "facts": {"stack_arn": deployment["stack_arn"], "database_identifier": identifier, "resources_sha256": deployment["resources_sha256"], "absence_observed": True, "source_mutation": False}}


def cleanup_restore(provider, store, binding, parameters, deployment, reader_reservation, reader_receipt, *, historical_reader=False):
    """Existing approved execution/reconciliation path; not an acceptance reader."""
    require(type(historical_reader) is bool, "restore-reader-observation-mode-invalid")
    stack_name, identifier, resources, intent, retained = cleanup_identity(binding, parameters, deployment, reader_reservation, reader_receipt)
    previous = store.read("delete-restore", intent)
    if previous is None:
        stack = restore_stack(provider, binding, parameters)
        require(stack.get("StackId") == deployment["stack_arn"] and stack.get("StackStatus") == "CREATE_COMPLETE" and resource_map(provider, stack) == resources, "restore-cleanup-ownership-not-confirmed")
        database = only(provider("rds", "describe-db-instances", DBInstanceIdentifier=identifier), "DBInstances")
        require(database.get("DBInstanceIdentifier") == identifier and database.get("DbiResourceId") == deployment["restored_resource_id"] and database.get("DeletionProtection") is False, "restore-cleanup-database-identity-not-confirmed")
        exact_tags(provider("rds", "list-tags-for-resource", ResourceName=database.get("DBInstanceArn")).get("TagList"), binding)
        validate_reader(provider, binding, parameters, resources, database, reader_reservation, retained, historical=historical_reader)
        RESOURCE.require_other_tasks_terminal(provider)
    reservation, fresh = store.reserve("delete-restore", intent)
    if fresh:
        try: provider("cloudformation", "delete-stack", StackName=deployment["stack_arn"], ClientRequestToken=reservation["operation_id"])
        except RESOURCE.SubmissionNotStarted: raise
        except Exception: raise RESOURCE.ResourceFailure("restore-cleanup-submission-uncertain-reconcile-only") from None
    return observe_cleanup(provider, store, binding, parameters, deployment, reader_reservation, reader_receipt)
