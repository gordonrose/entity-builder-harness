#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Compare actual own immutable task revisions, IAM policies and private security-group rules with the reviewed source before task capability is supplied.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Read-only own-template adapter, not a general CloudFormation interpreter.

The caller must first prove exact own-stack source/parameters/resource lineage.
No secret is fetched; provider dictionaries are ephemeral and never reports.
Successful comparison is not effective SQL access or execution approval.
"""
import copy
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote

SPEC = importlib.util.spec_from_file_location("entity_smoke_binding_deployment", Path(__file__).with_name("deployment-control.py"))
DEPLOY = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(DEPLOY)
ACCOUNT, REGION = DEPLOY.RESOURCE.ACCOUNT, DEPLOY.RESOURCE.REGION
WORKLOADS = {"server": "Server", "migration": "Migration", "administration": "Administration", "verifier": "Verifier", "database-proof": "DatabaseProof"}


class BindingFailure(Exception):
    def __init__(self, code, workload, field, item=None):
        super().__init__(code)
        self.code, self.workload, self.field = code, workload, field
        self.item = item or field


def require(value, code, workload, field, item=None):
    if not value: raise BindingFailure(code, workload, field, item)


def same(left, right):
    try: return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError): return False


def resolve(value, parameters, resources, workload):
    if isinstance(value, list): return [resolve(item, parameters, resources, workload) for item in value]
    if not isinstance(value, dict): return value
    if set(value) == {"Ref"}:
        name = value["Ref"]
        known = {**{key: row["physical_id"] for key, row in resources.items() if row["type"] == "AWS::EC2::SecurityGroup"}, **parameters, "AWS::AccountId": ACCOUNT, "AWS::Region": REGION}
        require(isinstance(name, str) and name in known, "task-binding-source-not-supported", workload, "source")
        return known[name]
    if set(value) == {"Fn::GetAtt"}:
        parts = value["Fn::GetAtt"]
        require(isinstance(parts, list) and len(parts) == 2 and isinstance(parts[0], str) and parts[0] in resources and parts[1] == "Arn"
                and resources[parts[0]]["type"] == "AWS::IAM::Role", "task-binding-source-not-supported", workload, "source")
        return "arn:aws:iam::" + ACCOUNT + ":role/" + resources[parts[0]]["physical_id"]
    if set(value) == {"Fn::Sub"}:
        text = value["Fn::Sub"]
        require(isinstance(text, str), "task-binding-source-not-supported", workload, "source")
        return re.sub(r"\$\{([^}]+)\}", lambda match: resolve({"Ref": match[1]}, parameters, resources, workload), text)
    require(not any(key == "Ref" or key.startswith("Fn::") for key in value), "task-binding-source-not-supported", workload, "source")
    return {key: resolve(item, parameters, resources, workload) for key, item in value.items()}


def lower_keys(value):
    if isinstance(value, list): return [lower_keys(item) for item in value]
    if isinstance(value, dict): return {key[:1].lower() + key[1:]: lower_keys(item) for key, item in value.items()}
    return value


def selected_prefix(workload, prefix):
    if prefix is None:
        require(isinstance(workload, str) and workload in WORKLOADS, "task-binding-selection-invalid", "unselected", "selection")
        return WORKLOADS[workload]
    require(workload == "restore-reader" and prefix == "RestoreReader", "task-binding-selection-invalid", "unselected", "selection")
    return prefix


def expected_task(workload, parameters, resources, snapshot=None, *, prefix=None):
    prefix = selected_prefix(workload, prefix)
    snapshot = DEPLOY.source()[1] if snapshot is None else snapshot
    source = snapshot["Resources"][prefix + "TaskDefinition"]["Properties"]
    allowed = {"Family", "Cpu", "Memory", "NetworkMode", "RequiresCompatibilities", "RuntimePlatform", "ExecutionRoleArn", "TaskRoleArn", "ContainerDefinitions"}
    container_allowed = {"Name", "Image", "Essential", "ReadonlyRootFilesystem", "LinuxParameters", "Command", "LogConfiguration", "Environment", "Secrets", "PortMappings", "HealthCheck"}
    require(not set(source) - allowed and len(source["ContainerDefinitions"]) == 1 and not set(source["ContainerDefinitions"][0]) - container_allowed,
            "task-binding-source-not-supported", workload, "source")
    return lower_keys(resolve(source, parameters, resources, workload))


def sorted_entries(value, key, workload):
    require(isinstance(value, list) and all(isinstance(item, dict) and isinstance(item.get(key), str) for item in value)
            and len({item[key] for item in value}) == len(value), "task-binding-container-not-confirmed", workload, "container")
    return sorted(value, key=lambda item: item[key])


def task_definition(provider, workload, parameters, resources, snapshot=None, *, prefix=None):
    selected = selected_prefix(workload, prefix)
    expected = expected_task(workload, parameters, resources, snapshot, prefix=prefix)
    arn = resources[selected + "TaskDefinition"]["physical_id"]
    require(isinstance(arn, str) and re.fullmatch(r"arn:aws:ecs:" + REGION + ":" + ACCOUNT + ":task-definition/" + expected["family"] + r":[1-9][0-9]*", arn) is not None,
            "task-binding-definition-not-confirmed", workload, "identity")
    response = provider("ecs", "describe-task-definition", taskDefinition=arn)
    actual = response.get("taskDefinition") if isinstance(response, dict) else None
    require(isinstance(actual, dict) and actual.get("taskDefinitionArn") == arn and actual.get("status") == "ACTIVE"
            and type(actual.get("revision")) is int and actual["revision"] == int(arn.rsplit(":", 1)[1])
            and isinstance(actual.get("compatibilities"), list) and "FARGATE" in actual["compatibilities"], "task-binding-definition-not-confirmed", workload, "identity")
    metadata = {"taskDefinitionArn", "revision", "status", "compatibilities", "requiresAttributes", "registeredAt", "registeredBy"}
    actual = {key: copy.deepcopy(value) for key, value in actual.items() if key not in metadata}
    defaults = {"volumes": [], "placementConstraints": [], "inferenceAccelerators": [], "enableFaultInjection": False, "ephemeralStorage": {"sizeInGiB": 20}, "taskRoleArn": ""}
    for key, default in defaults.items():
        if key not in expected and key in actual:
            require(same(actual[key], default), "task-binding-definition-not-confirmed", workload, "identity")
            del actual[key]
    require(set(actual) == set(expected), "task-binding-definition-not-confirmed", workload, "identity")
    containers = actual.get("containerDefinitions")
    require(isinstance(containers, list) and len(containers) == 1 and isinstance(containers[0], dict), "task-binding-container-not-confirmed", workload, "container")
    observed, intended = containers[0], expected["containerDefinitions"][0]
    container_defaults = {"cpu": 0, "mountPoints": [], "volumesFrom": [], "portMappings": [], "secrets": [], "environmentFiles": [], "ulimits": [], "systemControls": [], "dependsOn": [], "privileged": False, "interactive": False, "pseudoTerminal": False, "disableNetworking": False,
                          "credentialSpecs": [], "dnsSearchDomains": [], "dnsServers": [], "dockerLabels": {}, "dockerSecurityOptions": [], "entryPoint": [], "extraHosts": [], "links": []}
    for key, default in container_defaults.items():
        if key not in intended and key in observed:
            require(same(observed[key], default), "task-binding-container-not-confirmed", workload, "container")
            del observed[key]
    for container in (observed, intended):
        for key in ("environment", "secrets"):
            if key in container: container[key] = sorted_entries(container[key], "name", workload)
        linux = container.get("linuxParameters")
        require(isinstance(linux, dict) and isinstance(linux.get("capabilities"), dict), "task-binding-container-not-confirmed", workload, "container")
        for key in ("devices", "tmpfs"):
            if key not in intended["linuxParameters"] and key in linux:
                require(same(linux[key], []), "task-binding-container-not-confirmed", workload, "container")
                del linux[key]
        capabilities = linux["capabilities"]
        if capabilities.get("add") == []: del capabilities["add"]
        logging = container.get("logConfiguration", {})
        require(isinstance(logging, dict), "task-binding-container-not-confirmed", workload, "container")
        if logging.get("secretOptions") == []: del logging["secretOptions"]
        ports = container.get("portMappings", [])
        require(isinstance(ports, list) and all(isinstance(port, dict) for port in ports), "task-binding-container-not-confirmed", workload, "container")
        for port in ports:
            if isinstance(port, dict) and "containerPort" in port: port.setdefault("hostPort", port["containerPort"])
    require(same(actual, expected), "task-binding-container-not-confirmed", workload, "container")
    return arn, expected


def policy(value, workload):
    if isinstance(value, str):
        require(len(value) <= 393216, "task-binding-policy-not-confirmed", workload, "roles")
        def pairs(items):
            result = {}
            for key, item in items:
                if key in result: raise ValueError()
                result[key] = item
            return result
        try: value = json.loads(value if value.lstrip().startswith("{") else unquote(value), object_pairs_hook=pairs)
        except (TypeError, ValueError, UnicodeError, RecursionError): raise BindingFailure("task-binding-policy-not-confirmed", workload, "roles") from None
    require(isinstance(value, dict) and set(value) == {"Version", "Statement"} and value["Version"] == "2012-10-17" and isinstance(value["Statement"], list), "task-binding-policy-not-confirmed", workload, "roles")
    statements = copy.deepcopy(value["Statement"])
    for statement in statements:
        require(isinstance(statement, dict), "task-binding-policy-not-confirmed", workload, "roles")
        statement.pop("Sid", None)  # A statement label confers no authority.
        for key in ("Action", "Resource"):
            if isinstance(statement.get(key), str): statement[key] = [statement[key]]
            if key in statement:
                require(isinstance(statement[key], list) and all(isinstance(item, str) for item in statement[key]), "task-binding-policy-not-confirmed", workload, "roles")
                statement[key] = sorted(statement[key])
    try: return {"Version": "2012-10-17", "Statement": sorted(statements, key=lambda item: json.dumps(item, sort_keys=True, allow_nan=False))}
    except (TypeError, ValueError, RecursionError): raise BindingFailure("task-binding-policy-not-confirmed", workload, "roles") from None


def _role(provider, logical, parameters, resources, workload, snapshot=None):
    name = resources[logical]["physical_id"]
    require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_+=,.@-]{1,64}", name) is not None, "task-binding-role-not-confirmed", workload, "roles")
    snapshot = DEPLOY.source()[1] if snapshot is None else snapshot
    expected = resolve(snapshot["Resources"][logical]["Properties"], parameters, resources, workload)
    response = provider("iam", "get-role", RoleName=name)
    value = response.get("Role") if isinstance(response, dict) else None
    require(isinstance(value, dict) and value.get("RoleName") == name and value.get("Arn") == "arn:aws:iam::" + ACCOUNT + ":role/" + name and value.get("Path") == "/" and "PermissionsBoundary" not in value
            and same(policy(value.get("AssumeRolePolicyDocument"), workload), policy(expected["AssumeRolePolicyDocument"], workload)), "task-binding-role-not-confirmed", workload, "roles")
    attached = provider("iam", "list-attached-role-policies", RoleName=name)
    require(isinstance(attached, dict) and attached.get("AttachedPolicies") == [] and attached.get("IsTruncated") is False and not attached.get("Marker"), "task-binding-attached-policy-prohibited", workload, "roles")
    inline = provider("iam", "list-role-policies", RoleName=name)
    policies = {item["PolicyName"]: item["PolicyDocument"] for item in expected.get("Policies", [])}
    require(isinstance(inline, dict) and isinstance(inline.get("PolicyNames"), list) and len(inline["PolicyNames"]) == len(policies) and all(isinstance(item, str) for item in inline["PolicyNames"])
            and set(inline["PolicyNames"]) == set(policies) and inline.get("IsTruncated") is False and not inline.get("Marker"), "task-binding-policy-inventory-not-confirmed", workload, "roles")
    for selected, document in policies.items():
        observed = provider("iam", "get-role-policy", RoleName=name, PolicyName=selected)
        require(isinstance(observed, dict) and observed.get("RoleName") == name and observed.get("PolicyName") == selected and same(policy(observed.get("PolicyDocument"), workload), policy(document, workload)), "task-binding-policy-not-confirmed", workload, "roles")
    return DEPLOY.fingerprint(expected)


def role(provider, logical, parameters, resources, workload, snapshot=None):
    try: return _role(provider, logical, parameters, resources, workload, snapshot)
    except BindingFailure as failure:
        failure.item = "execution-role" if logical.endswith("ExecutionRole") else "task-role"
        raise


def permissions(rows, workload):
    require(isinstance(rows, list) and len(rows) <= 20, "task-binding-network-not-confirmed", workload, "network")
    result = []
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("IpProtocol"), str) and type(row.get("FromPort")) is int and type(row.get("ToPort")) is int and not row.get("Ipv6Ranges"), "task-binding-network-not-confirmed", workload, "network")
        destinations = []
        for key, field in (("UserIdGroupPairs", "GroupId"), ("IpRanges", "CidrIp"), ("PrefixListIds", "PrefixListId")):
            values = row.get(key, [])
            require(isinstance(values, list) and all(isinstance(item, dict) and isinstance(item.get(field), str) for item in values), "task-binding-network-not-confirmed", workload, "network")
            if key == "UserIdGroupPairs": require(all(item.get("UserId", ACCOUNT) == ACCOUNT and not item.get("VpcPeeringConnectionId") for item in values), "task-binding-network-not-confirmed", workload, "network")
            destinations.extend((field, item[field]) for item in values)
        require(bool(destinations), "task-binding-network-not-confirmed", workload, "network")
        result.extend((row["IpProtocol"], row["FromPort"], row["ToPort"], *destination) for destination in destinations)
    require(len(set(result)) == len(result), "task-binding-network-not-confirmed", workload, "network")
    return sorted(result)


def network(provider, workload, parameters, resources, snapshot=None, *, prefix=None):
    logical = selected_prefix(workload, prefix) + "SecurityGroup"
    group_id = resources[logical]["physical_id"]
    require(isinstance(group_id, str) and re.fullmatch(r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", group_id) is not None, "task-binding-network-not-confirmed", workload, "network")
    response = provider("ec2", "describe-security-groups", GroupIds=[group_id])
    groups = response.get("SecurityGroups") if isinstance(response, dict) else None
    require(isinstance(groups, list) and len(groups) == 1 and isinstance(groups[0], dict), "task-binding-network-not-confirmed", workload, "network")
    group = groups[0]
    require(group.get("GroupId") == group_id and group.get("VpcId") == parameters["VpcId"] and group.get("OwnerId") == ACCOUNT, "task-binding-network-not-confirmed", workload, "network")
    snapshot = DEPLOY.source()[1] if snapshot is None else snapshot
    source = snapshot["Resources"]
    expected_egress = []
    for row in resolve(source[logical]["Properties"]["SecurityGroupEgress"], parameters, resources, workload):
        key, field = next((key, field) for key, field in (("DestinationSecurityGroupId", "GroupId"), ("CidrIp", "CidrIp"), ("DestinationPrefixListId", "PrefixListId")) if key in row)
        expected_egress.append((str(row["IpProtocol"]), row["FromPort"], row["ToPort"], field, row[key]))
    expected_ingress = []
    if workload == "server": expected_ingress = [("tcp", 3000, 3000, "GroupId", resources["VerifierSecurityGroup"]["physical_id"])]
    actual = {"ingress": permissions(group.get("IpPermissions"), workload), "egress": permissions(group.get("IpPermissionsEgress"), workload)}
    require(actual["ingress"] == sorted(expected_ingress) and actual["egress"] == sorted(expected_egress), "task-binding-network-not-confirmed", workload, "network")
    destinations = [(parameters["EndpointSecurityGroupId"], 443)]
    destinations.append((resources["ServerSecurityGroup"]["physical_id"], 3000) if workload == "verifier" else (parameters["DatabaseSecurityGroupId"], 5432))
    for destination, port in destinations:
        item = "delivery-ingress" if port == 443 else "private-server-ingress" if workload == "verifier" else "database-ingress"
        response = provider("ec2", "describe-security-groups", GroupIds=[destination])
        values = response.get("SecurityGroups") if isinstance(response, dict) else None
        require(isinstance(values, list) and len(values) == 1 and isinstance(values[0], dict) and values[0].get("GroupId") == destination
                and values[0].get("VpcId") == parameters["VpcId"] and values[0].get("OwnerId") == ACCOUNT, "task-binding-destination-not-confirmed", workload, "network", item)
        ingress = values[0].get("IpPermissions")
        require(isinstance(ingress, list) and any(isinstance(row, dict) and row.get("IpProtocol") == "tcp" and type(row.get("FromPort")) is int and row["FromPort"] == port
                and type(row.get("ToPort")) is int and row["ToPort"] == port and isinstance(row.get("UserIdGroupPairs"), list)
                and any(isinstance(pair, dict) and pair.get("GroupId") == group_id and pair.get("UserId", ACCOUNT) == ACCOUNT and not pair.get("VpcPeeringConnectionId") for pair in row["UserIdGroupPairs"]) for row in ingress),
                "task-binding-destination-not-confirmed", workload, "network", item)
    return group_id, DEPLOY.fingerprint(actual)


def inspect(provider, workload, parameters, resources, snapshot=None):
    require(isinstance(workload, str) and workload in WORKLOADS, "task-binding-selection-invalid", "unselected", "selection")
    require(isinstance(parameters, dict) and set(parameters) == DEPLOY.PARAMETERS and all(isinstance(value, str) and value and not any(character in value for character in "\n\r\0") for value in parameters.values()), "task-binding-parameters-not-confirmed", workload, "source")
    require(isinstance(resources, dict) and set(resources) == set(DEPLOY.RESOURCE_TYPES) and all(isinstance(row, dict) and set(row) == {"type", "physical_id"} and row["type"] == DEPLOY.RESOURCE_TYPES[name] and isinstance(row["physical_id"], str) for name, row in resources.items()), "task-binding-resources-not-confirmed", workload, "source")
    # A prepared operation may share its checked source view across its own
    # inspections. The public caller reads afresh at later preparation/guards;
    # provider observations and final source fingerprints are never cached.
    snapshot = DEPLOY.source()[1] if snapshot is None else snapshot
    definition, configuration = task_definition(provider, workload, parameters, resources, snapshot)
    prefix = WORKLOADS[workload]
    names = [prefix + "ExecutionRole"] + ([prefix + "TaskRole"] if workload in {"server", "migration", "database-proof"} else [])
    identities = {name: role(provider, name, parameters, resources, workload, snapshot) for name in names}
    group, network_digest = network(provider, workload, parameters, resources, snapshot)
    return {"definition": definition, "security_group": group, "subnets": parameters["PrivateSubnetIds"].split(","),
            "configuration_sha256": DEPLOY.fingerprint(configuration), "roles_sha256": DEPLOY.fingerprint(identities), "network_sha256": network_digest}
