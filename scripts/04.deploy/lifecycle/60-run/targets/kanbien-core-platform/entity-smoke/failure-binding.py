#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.entity-smoke.failure-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Observe exact own failed or partial scope ownership and other-service configurations without requiring application or database health.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Read-only failure alignment; no permission to launch, repair or delete.

The owning route supplies source/custody checks and release-policy selection.
Observed absence is distinct from incomplete or failed provider observation.
"""
import re

TERMINAL_STACKS = {"CREATE_COMPLETE", "CREATE_FAILED", "ROLLBACK_COMPLETE", "ROLLBACK_FAILED", "UPDATE_COMPLETE", "UPDATE_FAILED", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_FAILED", "DELETE_COMPLETE", "DELETE_FAILED"}
TERMINAL_RESOURCES = {"CREATE_COMPLETE", "CREATE_FAILED", "DELETE_COMPLETE", "DELETE_FAILED", "DELETE_SKIPPED", "UPDATE_COMPLETE", "UPDATE_FAILED", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_FAILED", "ROLLBACK_COMPLETE", "ROLLBACK_FAILED"}
WORKLOADS = {"server": "Server", "administration": "Administration", "migration": "Migration", "verifier": "Verifier", "database-proof": "DatabaseProof"}
MAX_TASKS = 32


class FailureBindingError(Exception):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


def require(value, code, item=None):
    if not value: raise FailureBindingError(code, item)


def task_arn(C, value):
    return isinstance(value, str) and re.fullmatch(r"arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":task/" + C.RESOURCE.CLUSTER + r"/[a-f0-9]{32}", value) is not None


def original_reservation(C, cache, phase):
    value = C.read_json(cache / "attempts" / (cache.name + "-" + phase + ".json"))
    require(isinstance(value, dict) and isinstance(value.get("request"), dict), "failure-creation-reservation-invalid", phase)
    store = C.RESOURCE.ResourceStore(cache / "attempts")
    require(store.read(phase, value["request"]) == value, "failure-creation-reservation-not-confirmed", phase)
    return value


def lineage(C, provider, stack_arn, reservation):
    token = None
    seen = set()
    for _ in range(3):
        response = provider("cloudformation", "describe-stack-events", StackName=stack_arn, **({"NextToken": token} if token is not None else {}))
        rows = response.get("StackEvents") if isinstance(response, dict) else None
        require(isinstance(rows, list) and len(rows) <= 100 and all(isinstance(row, dict) for row in rows), "failure-creation-lineage-incomplete")
        if any(row.get("PhysicalResourceId") == stack_arn and row.get("ClientRequestToken") == reservation["operation_id"] for row in rows): return
        token = response.get("NextToken")
        if not token: break
        require(isinstance(token, str) and len(token) <= 4096 and token not in seen, "failure-creation-lineage-incomplete")
        seen.add(token)
    raise FailureBindingError("failure-creation-lineage-not-confirmed")


def stack_resources(C, provider, stack, expected):
    response = provider("cloudformation", "list-stack-resources", StackName=stack["StackId"])
    rows = response.get("StackResourceSummaries") if isinstance(response, dict) else None
    require(isinstance(rows, list) and len(rows) <= len(expected) and not response.get("NextToken"), "failure-resource-observation-incomplete")
    result = {}
    for row in rows:
        require(isinstance(row, dict), "failure-resource-observation-invalid")
        name = row.get("LogicalResourceId")
        require(isinstance(name, str) and name in expected and name not in result and row.get("ResourceType") == expected[name], "failure-resource-ownership-not-confirmed")
        require(row.get("ResourceStatus") in TERMINAL_RESOURCES, "failure-resource-writer-not-terminal", name)
        physical = row.get("PhysicalResourceId")
        require(physical is None or isinstance(physical, str) and bool(physical), "failure-resource-observation-invalid", name)
        result[name] = {"type": row["ResourceType"], "physical_id": physical}
    return result


def main_scope(C, provider, receipt, label, cache):
    creation = original_reservation(C, cache, "deploy-execute-create")
    request = creation["request"]
    binding = request["binding"]
    expected = {"source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"], "proof_label": label,
                "configuration_contract_sha256": C.digest_file(C.ROOT / C.ALIGN.SCOPE), "permission_contract_sha256": C.digest_file(C.DEPLOY.SOURCE)}
    require(all(binding.get(key) == value for key, value in expected.items()), "failure-qualified-binding-mismatch")
    stack = C.RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=request["stack_arn"]), "Stacks")
    C.DEPLOY.exact_stack(stack, binding)
    require(stack.get("StackId") == request["stack_arn"] and stack.get("StackStatus") in TERMINAL_STACKS, "failure-stack-writer-not-terminal")
    rows = stack.get("Parameters")
    require(isinstance(rows, list) and len(rows) == len(C.DEPLOY.PARAMETERS) and all(isinstance(row, dict) and set(row) >= {"ParameterKey", "ParameterValue"}
            and isinstance(row["ParameterKey"], str) and isinstance(row["ParameterValue"], str) for row in rows), "failure-parameters-not-confirmed")
    parameters = {row["ParameterKey"]: row["ParameterValue"] for row in rows}
    require(len(parameters) == len(rows) and parameters.get("ServerDesiredCount") in {"0", "1"}, "failure-parameters-not-confirmed")
    C.DEPLOY.parameters_for(binding, parameters, parameters["ServerDesiredCount"] == "1")
    initial = C.DEPLOY.request(binding, {**parameters, "ServerDesiredCount": "0"}, False)
    require(all(request.get(key) == value for key, value in initial.items()), "failure-creation-input-mismatch")
    template = provider("cloudformation", "get-template", StackName=stack["StackId"], TemplateStage="Original")
    require(isinstance(template, dict) and C.DEPLOY.CF.templates_equal(template.get("TemplateBody"), C.DEPLOY.source()[0]), "failure-template-not-confirmed")
    lineage(C, provider, stack["StackId"], creation)
    resources = stack_resources(C, provider, stack, C.DEPLOY.RESOURCE_TYPES)
    physical_service = resources.get("FeatureService", {}).get("physical_id")
    service_arn = "arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":service/" + C.RESOURCE.CLUSTER + "/" + C.RESOURCE.SERVICE
    require(physical_service is None or physical_service in {C.RESOURCE.SERVICE, service_arn}, "failure-service-resource-not-confirmed")
    return {"binding": binding, "parameters": parameters, "resources": resources, "stack_arn": stack["StackId"], "creation_sha256": C.DEPLOY.fingerprint(creation)}


def restore_scope(C, restore, provider, context, cache):
    binding = context["binding"]
    name = "kanbien-core-platform-entity-smoke-restore-" + binding["proof_label"].removeprefix("entity-smoke-")
    path = cache / "attempts" / (cache.name + "-execute-restore.json")
    C.RESOURCE.CONTROL.no_symlinks(path)
    if not path.exists():
        try: provider("cloudformation", "describe-stacks", StackName=name)
        except C.RESOURCE.ResourceMissing: return None
        raise FailureBindingError("failure-restore-creation-reservation-required")
    creation = original_reservation(C, cache, "execute-restore")
    request = creation["request"]
    require(all(request["binding"].get(key) == value for key, value in binding.items()), "failure-restore-binding-mismatch")
    stack = C.RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=request["stack_arn"]), "Stacks")
    require(stack.get("StackName") == name and stack.get("StackId") == request["stack_arn"] and stack.get("StackStatus") in TERMINAL_STACKS, "failure-restore-writer-not-terminal")
    C.DEPLOY.exact_tags(stack.get("Tags"), binding)
    rows = stack.get("Parameters")
    require(isinstance(rows, list) and len(rows) == len(restore.PARAMETERS) and all(isinstance(row, dict) and isinstance(row.get("ParameterKey"), str) and isinstance(row.get("ParameterValue"), str) for row in rows), "failure-restore-parameters-not-confirmed")
    parameters = {row["ParameterKey"]: row["ParameterValue"] for row in rows}
    require(len(parameters) == len(rows), "failure-restore-parameters-not-confirmed")
    expected = restore.request(request["binding"], parameters)
    require(all(request.get(key) == value for key, value in expected.items()), "failure-restore-input-mismatch")
    template = provider("cloudformation", "get-template", StackName=stack["StackId"], TemplateStage="Original")
    require(isinstance(template, dict) and C.DEPLOY.CF.templates_equal(template.get("TemplateBody"), restore.source()[0]), "failure-restore-template-not-confirmed")
    lineage(C, provider, stack["StackId"], creation)
    resources = stack_resources(C, provider, stack, restore.RESOURCE_TYPES)
    return {"parameters": parameters, "resources": resources, "stack_arn": stack["StackId"], "creation_sha256": C.DEPLOY.fingerprint(creation)}


def definitions(C, provider, context, restored):
    refs = {workload: context["resources"].get(prefix + "TaskDefinition", {}).get("physical_id") for workload, prefix in WORKLOADS.items()}
    refs["restore-reader"] = None if restored is None else restored["resources"].get("RestoreReaderTaskDefinition", {}).get("physical_id")
    for workload, arn in refs.items():
        if arn is None: continue
        family = "kanbien-core-platform-entity-smoke-" + workload
        require(isinstance(arn, str) and re.fullmatch(r"arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":task-definition/" + family + r":[1-9][0-9]*", arn) is not None, "failure-definition-ownership-not-confirmed", workload)
        response = provider("ecs", "describe-task-definition", taskDefinition=arn)
        value = response.get("taskDefinition") if isinstance(response, dict) else None
        require(isinstance(value, dict) and value.get("taskDefinitionArn") == arn and value.get("family") == family and value.get("status") in {"ACTIVE", "INACTIVE"}, "failure-definition-ownership-not-confirmed", workload)
        containers = value.get("containerDefinitions")
        require(isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict) and containers[0].get("name") == "entity-smoke-" + workload,
                "failure-definition-container-not-confirmed", workload)
        require(containers[0].get("image") == context["parameters"]["ImageRepositoryUri"] + "@" + context["binding"]["image_digest"], "failure-definition-image-not-confirmed", workload)
        command = "artifacts/kanbien-entity-smoke" + ("" if workload == "server" else "-database-proof" if workload == "restore-reader" else "-" + workload) + ".main.js"
        require(containers[0].get("command") == [command], "failure-definition-command-not-confirmed", workload)
    return refs


def service_projection(C, value):
    require(isinstance(value, dict) and isinstance(value.get("serviceName"), str) and isinstance(value.get("serviceArn"), str)
            and value.get("clusterArn") == "arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":cluster/" + C.RESOURCE.CLUSTER
            and isinstance(value.get("taskDefinition"), str) and type(value.get("desiredCount")) is int and value["desiredCount"] >= 0,
            "failure-service-observation-invalid")
    fields = ("serviceArn", "serviceName", "clusterArn", "taskDefinition", "desiredCount", "status", "deploymentController", "deploymentConfiguration", "networkConfiguration", "serviceRegistries", "capacityProviderStrategy", "launchType", "platformVersion", "enableExecuteCommand", "enableECSManagedTags", "propagateTags", "placementConstraints", "placementStrategy", "loadBalancers", "schedulingStrategy")
    return {"arn": value["serviceArn"], "name": value["serviceName"], "definition": value["taskDefinition"], "desired_count": value["desiredCount"],
            "configuration_sha256": C.DEPLOY.fingerprint({key: value[key] for key in fields if key in value}),
            "stable_configuration_sha256": C.DEPLOY.fingerprint({key: value[key] for key in fields if key in value and key not in {"desiredCount", "status"}})}


def own_service(C, row, physical, definition):
    projected = service_projection(C, row)
    expected_arn = "arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":service/" + C.RESOURCE.CLUSTER + "/" + C.RESOURCE.SERVICE
    require(row.get("serviceName") == C.RESOURCE.SERVICE and physical in {row["serviceArn"], row["serviceName"]} and definition is not None
            and row["serviceArn"] == expected_arn and row.get("taskDefinition") == definition and row.get("status") in {"ACTIVE", "DRAINING", "INACTIVE"}
            and row.get("desiredCount") in {0, 1}, "failure-own-service-not-confirmed")
    require(all(type(row.get(key)) is int and row[key] >= 0 for key in ("runningCount", "pendingCount")), "failure-own-service-count-not-confirmed")
    require(row["status"] != "INACTIVE" or all(row[key] == 0 for key in ("desiredCount", "runningCount", "pendingCount")), "failure-inactive-service-count-not-confirmed")
    return {**projected, "running_count": row["runningCount"], "pending_count": row["pendingCount"]}


def services(C, provider, context, refs):
    response = provider("ecs", "list-services", cluster=C.RESOURCE.CLUSTER)
    arns = response.get("serviceArns") if isinstance(response, dict) else None
    require(isinstance(arns, list) and len(arns) <= 100 and not response.get("nextToken") and all(isinstance(arn, str) for arn in arns) and len(set(arns)) == len(arns), "failure-service-observation-incomplete")
    expected_prefix = "arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":service/"
    require(all(arn.startswith(expected_prefix) for arn in arns), "failure-service-target-not-confirmed")
    own, other = None, {}
    physical = context["resources"].get("FeatureService", {}).get("physical_id")
    for offset in range(0, len(arns), 10):
        batch = arns[offset:offset + 10]
        response = provider("ecs", "describe-services", cluster=C.RESOURCE.CLUSTER, services=batch)
        rows = response.get("services") if isinstance(response, dict) else None
        require(isinstance(rows, list) and len(rows) == len(batch) and not response.get("failures") and all(isinstance(row, dict) for row in rows)
                and {row.get("serviceArn") for row in rows} == set(batch), "failure-service-observation-incomplete")
        for row in rows:
            projected = service_projection(C, row)
            if row["serviceName"] != C.RESOURCE.SERVICE:
                other[row["serviceArn"]] = projected
                continue
            require(own is None, "failure-own-service-not-confirmed")
            own = own_service(C, row, physical, refs["server"])
    if physical is not None and own is None:
        response = provider("ecs", "describe-services", cluster=C.RESOURCE.CLUSTER, services=[physical])
        require(isinstance(response, dict), "failure-own-service-absence-not-confirmed")
        rows, failures = response.get("services"), response.get("failures")
        if isinstance(rows, list) and len(rows) == 1 and not failures:
            own = own_service(C, rows[0], physical, refs["server"])
        else:
            require(rows == [] and isinstance(failures, list) and len(failures) == 1 and isinstance(failures[0], dict)
                    and failures[0].get("reason") == "MISSING" and failures[0].get("arn") == physical, "failure-own-service-absence-not-confirmed")
    return own, other


def tasks(C, provider, refs):
    result = {}
    for workload, definition in refs.items():
        family = "kanbien-core-platform-entity-smoke-" + workload
        arns = set()
        for status in ("RUNNING", "STOPPED"):
            response = provider("ecs", "list-tasks", cluster=C.RESOURCE.CLUSTER, family=family, desiredStatus=status)
            rows = response.get("taskArns") if isinstance(response, dict) else None
            require(isinstance(rows, list) and len(rows) <= 100 and all(task_arn(C, arn) for arn in rows) and len(set(rows)) == len(rows)
                    and not response.get("nextToken"), "failure-task-observation-incomplete", workload)
            arns.update(rows)
        require(len(arns) <= 100, "failure-task-observation-incomplete", workload)
        if not arns: continue
        response = provider("ecs", "describe-tasks", cluster=C.RESOURCE.CLUSTER, tasks=sorted(arns))
        rows = response.get("tasks") if isinstance(response, dict) else None
        require(isinstance(rows, list) and len(rows) == len(arns) and not response.get("failures") and all(isinstance(row, dict) for row in rows)
                and {row.get("taskArn") for row in rows} == arns, "failure-task-observation-incomplete", workload)
        for row in rows:
            if row.get("lastStatus") == "STOPPED": continue
            require(definition is not None and row.get("taskDefinitionArn") == definition and row.get("launchType") == "FARGATE"
                    and row.get("group") == ("service:" + C.RESOURCE.SERVICE if workload == "server" else "family:" + family), "failure-task-ownership-not-confirmed", workload)
            require(isinstance(row.get("lastStatus"), str) and row["lastStatus"] in {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}, "failure-task-state-not-confirmed", workload)
            require(row["taskArn"] not in result, "failure-task-observation-invalid", workload)
            result[row["taskArn"]] = {"definition": definition, "workload": workload, "state": row["lastStatus"]}
    require(len(result) <= MAX_TASKS, "failure-task-bound-exceeded")
    return result


def database(C, provider, context):
    try: response = provider("rds", "describe-db-instances", DBInstanceIdentifier=C.ALIGN.DATABASE)
    except C.RESOURCE.ResourceMissing: return {"state": "missing"}
    except C.InfrastructureFailure as failure: return {"state": "not-observed", "condition": failure.code}
    row = C.RESOURCE.only(response, "DBInstances")
    require(row.get("DBInstanceIdentifier") == C.ALIGN.DATABASE and isinstance(row.get("DbiResourceId"), str), "failure-database-observation-invalid")
    if not isinstance(row.get("DBName"), str) or not row["DBName"]:
        return {"state": "not-observed", "condition": "database-name-not-confirmed", "data_readback": "not-performed"}
    identity = C.DEPLOY.fingerprint({"resource_id": row["DbiResourceId"], "database": row.get("DBName"), "schema": "entity_smoke"})
    fields = ("DBInstanceIdentifier", "DbiResourceId", "DBName", "Engine", "EngineVersion", "StorageEncrypted", "PubliclyAccessible", "IAMDatabaseAuthenticationEnabled", "DBInstanceClass", "DBParameterGroups", "VpcSecurityGroups", "DBSubnetGroup")
    return {"state": "same-incarnation" if identity == context["binding"]["dependency_incarnation_sha256"] else "different-incarnation", "identity_sha256": identity,
            "configuration_sha256": C.DEPLOY.fingerprint({key: row[key] for key in fields if key in row}), "data_readback": "not-performed"}


def inspect(C, restore, provider, receipt, label, cache):
    context = main_scope(C, provider, receipt, label, cache)
    restored = restore_scope(C, restore, provider, context, cache)
    refs = definitions(C, provider, context, restored)
    own, other = services(C, provider, context, refs)
    active = tasks(C, provider, refs)
    require(own is not None or context["resources"].get("FeatureService", {}).get("physical_id") is not None
            or not any(row["workload"] == "server" for row in active.values()), "failure-orphan-service-task-not-confirmed")
    return {**context, "definitions": refs, "restored": restored, "service": own, "other_services": other, "active_tasks": active,
            "database": database(C, provider, context)}
