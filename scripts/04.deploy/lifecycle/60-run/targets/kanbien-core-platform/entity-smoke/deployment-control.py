#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.deployment-control
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-11"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reserve, review and reconcile isolated feature creation with no running server, then a desired-count-only activation without mutation replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Internal control; the owning public route supplies the gated capability.

No AWS CLI, authority grant or fabricated pre-record digest. Before supplying
live capability the route must establish source/custody/normal realization
gates, fresh alignment and concrete approval. Activation additionally needs
the retained successful bootstrap, migration, grant and runtime-access proofs.
"""
import hashlib
import importlib.util
from pathlib import Path
import re


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


RESOURCE = module("entity_smoke_deployment_resource", Path(__file__).with_name("resource-control.py"))
ROOT = Path(__file__).resolve().parents[7]
CF = module("entity_smoke_deployment_cf", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
SOURCE = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/entity-smoke.yml"
STACK = "kanbien-core-platform-entity-smoke"
PARAMETERS = {"VpcId", "VpcCidr", "PrivateSubnetIds", "ClusterArn", "NamespaceId", "EndpointSecurityGroupId", "S3ArtifactPrefixListId", "LogGroupName", "DatabaseEndpoint", "DatabaseName", "DatabaseResourceId", "DatabaseSecurityGroupId", "AdministratorSecretArn", "ImageRepositoryUri", "ImageRepositoryArn", "ImageDigest", "SourceRevision", "ServerDesiredCount"}
RESOURCE_TYPES = {name + "SecurityGroup": "AWS::EC2::SecurityGroup" for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof")}
RESOURCE_TYPES.update({"EndpointIngressFrom" + name: "AWS::EC2::SecurityGroupIngress" for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof")})
RESOURCE_TYPES.update({"DatabaseIngressFrom" + name: "AWS::EC2::SecurityGroupIngress" for name in ("Server", "Migration", "Administration", "DatabaseProof")})
RESOURCE_TYPES.update({name: "AWS::IAM::Role" for name in ("ServerExecutionRole", "ServerTaskRole", "MigrationExecutionRole", "MigrationTaskRole", "AdministrationExecutionRole", "VerifierExecutionRole", "DatabaseProofExecutionRole", "DatabaseProofTaskRole")})
RESOURCE_TYPES.update({name + "TaskDefinition": "AWS::ECS::TaskDefinition" for name in ("Server", "Migration", "Administration", "Verifier", "DatabaseProof")})
RESOURCE_TYPES.update(ServerIngressFromVerifier="AWS::EC2::SecurityGroupIngress", FeatureServiceDiscovery="AWS::ServiceDiscovery::Service", FeatureService="AWS::ECS::Service")
require, only = RESOURCE.require, RESOURCE.only


def fingerprint(value):
    return "sha256:" + hashlib.sha256(RESOURCE.CONTROL.canonical(value)).hexdigest()


def source():
    RESOURCE.CONTROL.no_symlinks(SOURCE)
    try:
        body = SOURCE.read_text()
        require(0 < len(body.encode("utf-8")) <= 51200, "deployment-source-size-invalid")
        template = CF.template(body)
        resources = template.get("Resources")
        require(isinstance(resources, dict) and all(isinstance(value, dict) for value in resources.values()) and {key: value.get("Type") for key, value in resources.items()} == RESOURCE_TYPES and set(template.get("Parameters", {})) == PARAMETERS, "deployment-source-shape-invalid")
        return body, template
    except (OSError, ValueError, TypeError):
        raise RESOURCE.ResourceFailure("deployment-source-unavailable") from None


def change_name(binding, activate):
    return "entity-smoke-" + ("activate" if activate else "create") + "-" + binding["proof_label"].removeprefix("entity-smoke-")


def parameters_for(binding, parameters, activate):
    RESOURCE.validate_binding(binding, record_required=False)
    require(type(activate) is bool and isinstance(parameters, dict) and set(parameters) == PARAMETERS and all(isinstance(value, str) and value and not any(char in value for char in "\n\r\0") for value in parameters.values()), "deployment-parameters-invalid")
    _, template = source()
    fixed = {"ImageDigest": binding["image_digest"], "SourceRevision": binding["source_revision"], "ServerDesiredCount": "1" if activate else "0",
             "ClusterArn": "arn:aws:ecs:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":cluster/" + RESOURCE.CLUSTER,
             "ImageRepositoryUri": RESOURCE.ACCOUNT + ".dkr.ecr." + RESOURCE.REGION + ".amazonaws.com/kanbien-core-platform/entity-smoke",
             "ImageRepositoryArn": "arn:aws:ecr:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":repository/kanbien-core-platform/entity-smoke",
             "LogGroupName": "/aws/ecs/kanbien-core-platform"}
    require(all(parameters[key] == value for key, value in fixed.items()), "deployment-parameters-invalid")
    for key, value in parameters.items():
        declaration = template["Parameters"][key]
        if "AllowedPattern" in declaration: require(re.fullmatch(declaration["AllowedPattern"], value) is not None, "deployment-parameters-invalid")
        if "AllowedValues" in declaration: require(value in [str(item) for item in declaration["AllowedValues"]], "deployment-parameters-invalid")
    for key, prefix in (("VpcId", "vpc"), ("EndpointSecurityGroupId", "sg"), ("DatabaseSecurityGroupId", "sg")):
        require(re.fullmatch(prefix + r"-(?:[a-f0-9]{8}|[a-f0-9]{17})", parameters[key]) is not None, "deployment-parameters-invalid")
    subnets = parameters["PrivateSubnetIds"].split(",")
    require(1 <= len(subnets) <= 3 and len(set(subnets)) == len(subnets) and all(re.fullmatch(r"subnet-(?:[a-f0-9]{8}|[a-f0-9]{17})", value) is not None for value in subnets), "deployment-parameters-invalid")
    require(parameters["AdministratorSecretArn"].startswith("arn:aws:secretsmanager:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":secret:kanbien-core-platform-persistence-migration-"), "deployment-parameters-invalid")
    require(fingerprint({"resource_id": parameters["DatabaseResourceId"], "database": parameters["DatabaseName"], "schema": "entity_smoke"}) == binding["dependency_incarnation_sha256"], "deployment-dependency-incarnation-mismatch")
    return parameters


def request(binding, parameters, activate):
    parameters_for(binding, parameters, activate)
    return {"binding": binding, "parameters_sha256": fingerprint(parameters), "template_sha256": "sha256:" + hashlib.sha256(source()[0].encode()).hexdigest()}


def exact_tags(value, binding):
    require(isinstance(value, list) and all(isinstance(item, dict) and isinstance(item.get("Key"), str) and isinstance(item.get("Value"), str) for item in value), "deployment-ownership-not-confirmed")
    tags = {item["Key"]: item["Value"] for item in value}
    require(len(tags) == len(value) and all(tags.get(key) == content for key, content in {"Target": RESOURCE.CLUSTER, "Scope": "entity-smoke", "ProofLabel": binding["proof_label"]}.items()), "deployment-ownership-not-confirmed")


def exact_parameters(value, expected):
    require(isinstance(value, list) and len(value) == len(expected) and all(isinstance(item, dict) and isinstance(item.get("ParameterKey"), str) and isinstance(item.get("ParameterValue"), str) for item in value) and {item["ParameterKey"]: item["ParameterValue"] for item in value} == expected, "deployment-provider-parameters-mismatch")


def exact_stack(value, binding):
    require(value.get("StackName") == STACK and isinstance(value.get("StackId"), str) and re.fullmatch(r"arn:aws:cloudformation:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":stack/" + STACK + r"/[A-Za-z0-9-]+", value["StackId"]) is not None, "deployment-stack-identity-not-confirmed")
    exact_tags(value.get("Tags"), binding)


def deployed_stack(provider, binding, parameters):
    value = only(provider("cloudformation", "describe-stacks", StackName=STACK), "Stacks")
    exact_stack(value, binding)
    exact_parameters(value.get("Parameters"), parameters)
    actual = provider("cloudformation", "get-template", StackName=value["StackId"], TemplateStage="Original")
    require(isinstance(actual, dict) and CF.templates_equal(actual.get("TemplateBody"), source()[0]), "deployment-provider-template-mismatch")
    return value


def reviewed_change(provider, binding, parameters, reservation, activate, *, executed=False):
    name = change_name(binding, activate)
    value = provider("cloudformation", "describe-change-set", StackName=STACK, ChangeSetName=name)
    require(isinstance(value, dict) and value.get("StackName") == STACK and value.get("ChangeSetName") == name and value.get("Description") == reservation["operation_id"] and not value.get("NextToken"), "deployment-change-identity-not-confirmed")
    if value.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}: return None
    require(value.get("Status") == "CREATE_COMPLETE" and value.get("ExecutionStatus") in ({"EXECUTE_IN_PROGRESS", "EXECUTE_COMPLETE"} if executed else {"AVAILABLE"}) and value.get("Capabilities") == ["CAPABILITY_IAM"] and value.get("IncludeNestedStacks", False) is False and value.get("ImportExistingResources", False) is False and not value.get("RoleARN") and not value.get("NotificationARNs"), "deployment-change-not-ready")
    require(value.get("OnStackFailure") == (None if activate else "DO_NOTHING"), "deployment-change-failure-policy-invalid")
    exact_tags(value.get("Tags"), binding)
    exact_parameters(value.get("Parameters"), parameters)
    changes = value.get("Changes")
    expected = {"FeatureService": RESOURCE_TYPES["FeatureService"]} if activate else RESOURCE_TYPES
    require(isinstance(changes, list) and len(changes) == len(expected), "deployment-change-resource-set-invalid")
    actual = {}
    for item in changes:
        resource = item.get("ResourceChange") if isinstance(item, dict) else None
        require(isinstance(resource, dict) and isinstance(resource.get("LogicalResourceId"), str) and resource["LogicalResourceId"] not in actual and resource.get("Action") == ("Modify" if activate else "Add") and resource.get("Replacement", "False") == "False", "deployment-change-shape-invalid")
        actual[resource["LogicalResourceId"]] = resource.get("ResourceType")
        if activate:
            details = resource.get("Details")
            require(resource.get("Scope") == ["Properties"] and isinstance(details, list) and len(details) == 1 and isinstance(details[0], dict) and details[0].get("Target") == {"Attribute": "Properties", "Name": "DesiredCount", "RequiresRecreation": "Never"} and details[0].get("ChangeSource") == "ParameterReference" and details[0].get("CausingEntity") == "ServerDesiredCount", "deployment-activation-not-count-only")
    require(actual == expected, "deployment-change-resource-set-invalid")
    change_arn, stack_arn = value.get("ChangeSetId"), value.get("StackId")
    require(isinstance(change_arn, str) and re.fullmatch(r"arn:aws:cloudformation:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":changeSet/" + name + r"/[A-Za-z0-9-]+", change_arn) is not None and isinstance(stack_arn, str) and re.fullmatch(r"arn:aws:cloudformation:" + RESOURCE.REGION + ":" + RESOURCE.ACCOUNT + ":stack/" + STACK + r"/[A-Za-z0-9-]+", stack_arn) is not None, "deployment-change-identity-not-confirmed")
    prospective = provider("cloudformation", "get-template", StackName=STACK, ChangeSetName=change_arn, TemplateStage="Original")
    require(isinstance(prospective, dict) and CF.templates_equal(prospective.get("TemplateBody"), source()[0]), "deployment-change-template-mismatch")
    return {"change_set_arn": change_arn, "stack_arn": stack_arn, "resource_count": len(actual)}


def initial_stack(provider, value, binding, parameters, reservation, *, executed=False):
    """Bind an unexecuted CREATE placeholder through its original change set.

    CloudFormation does not apply the proposed tags to the provisional stack.
    Never infer its ownership from an empty tag list or its name alone.
    """
    if value.get("StackStatus") != "REVIEW_IN_PROGRESS":
        exact_stack(value, binding)
        return
    if value.get("Tags") != []:
        exact_tags(value.get("Tags"), binding)
    facts = reviewed_change(provider, binding, parameters, reservation, False, executed=executed)
    require(facts is not None, "deployment-change-not-ready")
    require(value.get("StackName") == STACK and value.get("StackId") == facts["stack_arn"], "deployment-stack-identity-not-confirmed")


def prepare(provider, store, binding, parameters, *, activate=False):
    intent = request(binding, parameters, activate)
    reservation, fresh = store.reserve("deploy-activate-change-set" if activate else "deploy-create-change-set", intent)
    if fresh:
        if activate:
            before = deployed_stack(provider, binding, {**parameters, "ServerDesiredCount": "0"})
            require(before.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}, "deployment-activation-precondition-not-confirmed")
        else:
            try: provider("cloudformation", "describe-stacks", StackName=STACK)
            except RESOURCE.ResourceMissing: pass
            except Exception: raise RESOURCE.ResourceFailure("deployment-initial-absence-unavailable") from None
            else: raise RESOURCE.ResourceFailure("deployment-stack-already-exists")
        try:
            provider("cloudformation", "create-change-set", StackName=STACK, ChangeSetName=change_name(binding, activate), ChangeSetType="UPDATE" if activate else "CREATE", TemplateBody=source()[0],
                     Parameters=[{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())], Capabilities=["CAPABILITY_IAM"],
                     Description=reservation["operation_id"], ClientToken=reservation["operation_id"],
                     Tags=[{"Key": key, "Value": value} for key, value in {"Target": RESOURCE.CLUSTER, "Scope": "entity-smoke", "ProofLabel": binding["proof_label"]}.items()],
                     **({} if activate else {"OnStackFailure": "DO_NOTHING"}))
        except RESOURCE.SubmissionNotStarted: raise
        except Exception: raise RESOURCE.ResourceFailure("deployment-change-submission-uncertain-reconcile-only") from None
    try: facts = reviewed_change(provider, binding, parameters, reservation, activate)
    except RESOURCE.ResourceMissing: return {"status": "pending", "reservation": reservation}
    return {"status": "reviewed" if facts is not None else "pending", "reservation": reservation, "facts": facts}


def observe(provider, store, binding, parameters, change_arn, stack_arn, *, activate=False):
    intent = {**request(binding, parameters, activate), "change_set_arn": change_arn, "stack_arn": stack_arn}
    reservation = store.read("deploy-execute-activate" if activate else "deploy-execute-create", intent)
    require(reservation is not None, "deployment-execution-reservation-missing")
    value = only(provider("cloudformation", "describe-stacks", StackName=stack_arn), "Stacks")
    if not activate and value.get("StackStatus") == "REVIEW_IN_PROGRESS":
        review = store.read("deploy-create-change-set", request(binding, parameters, False))
        require(review is not None, "deployment-review-reservation-missing")
        initial_stack(provider, value, binding, parameters, review, executed=True)
    else:
        exact_stack(value, binding)
    require(value["StackId"] == stack_arn, "deployment-stack-identity-not-confirmed")
    pending = {"UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"} if activate else {"REVIEW_IN_PROGRESS", "CREATE_IN_PROGRESS"}
    if value.get("StackStatus") in pending: return {"status": "pending", "reservation": reservation}
    value = deployed_stack(provider, binding, parameters)
    require(value["StackId"] == stack_arn and value.get("StackStatus") == ("UPDATE_COMPLETE" if activate else "CREATE_COMPLETE"), "deployment-execution-not-successful")
    events = provider("cloudformation", "describe-stack-events", StackName=stack_arn)
    require(isinstance(events, dict) and isinstance(events.get("StackEvents"), list) and not events.get("NextToken") and any(isinstance(event, dict) and event.get("PhysicalResourceId") == stack_arn and event.get("ClientRequestToken") == reservation["operation_id"] for event in events["StackEvents"]), "deployment-execution-lineage-not-confirmed")
    response = provider("cloudformation", "list-stack-resources", StackName=stack_arn)
    rows = response.get("StackResourceSummaries") if isinstance(response, dict) else None
    require(isinstance(rows, list) and len(rows) == len(RESOURCE_TYPES) and not response.get("NextToken") and all(isinstance(row, dict) and all(isinstance(row.get(key), str) for key in ("LogicalResourceId", "ResourceType", "PhysicalResourceId", "ResourceStatus")) and row["PhysicalResourceId"] and row["ResourceStatus"] in {"CREATE_COMPLETE", "UPDATE_COMPLETE"} for row in rows) and {row["LogicalResourceId"]: row["ResourceType"] for row in rows} == RESOURCE_TYPES, "deployment-resources-not-confirmed")
    resources = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows}
    current = RESOURCE.service(provider, resources["ServerTaskDefinition"]["physical_id"], 1 if activate else 0)
    require(current.get("runningCount") == (1 if activate else 0) and current.get("pendingCount") == 0, "deployment-service-not-steady")
    tasks = RESOURCE.running_service_tasks(provider)
    require(len(tasks) == (1 if activate else 0), "deployment-service-not-steady")
    if activate:
        running = RESOURCE.task(provider, tasks[0], resources["ServerTaskDefinition"]["physical_id"], binding["image_digest"])
        require(running.get("lastStatus") == "RUNNING" and running.get("healthStatus") == "HEALTHY", "deployment-service-not-steady")
    return {"status": "completed", "reservation": reservation, "facts": {"stack_arn": stack_arn, "desired_count": 1 if activate else 0, "resources": resources, "resources_sha256": fingerprint(resources)}}


def execute(provider, store, binding, parameters, change_arn, stack_arn, *, activate=False):
    intent = request(binding, parameters, activate)
    review = store.read("deploy-activate-change-set" if activate else "deploy-create-change-set", intent)
    require(review is not None, "deployment-review-reservation-missing")
    execution, fresh = store.reserve("deploy-execute-activate" if activate else "deploy-execute-create", {**intent, "change_set_arn": change_arn, "stack_arn": stack_arn})
    if fresh:
        facts = reviewed_change(provider, binding, parameters, review, activate)
        require(isinstance(facts, dict) and facts["change_set_arn"] == change_arn and facts["stack_arn"] == stack_arn, "deployment-change-not-ready")
        before = deployed_stack(provider, binding, {**parameters, "ServerDesiredCount": "0"}) if activate else only(provider("cloudformation", "describe-stacks", StackName=stack_arn), "Stacks")
        if activate: exact_stack(before, binding)
        else: initial_stack(provider, before, binding, parameters, review)
        require(before["StackId"] == stack_arn and before.get("StackStatus") in ({"CREATE_COMPLETE", "UPDATE_COMPLETE"} if activate else {"REVIEW_IN_PROGRESS"}), "deployment-execution-precondition-not-confirmed")
        try:
            provider("cloudformation", "execute-change-set", StackName=stack_arn, ChangeSetName=change_arn, ClientRequestToken=execution["operation_id"], **({"DisableRollback": True} if activate else {}))
        except RESOURCE.SubmissionNotStarted: raise
        except Exception: raise RESOURCE.ResourceFailure("deployment-execution-uncertain-reconcile-only") from None
    return observe(provider, store, binding, parameters, change_arn, stack_arn, activate=activate)
