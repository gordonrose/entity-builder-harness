#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.ecs-runtime-configuration
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Normalize source ECS configuration and compare checked task revisions, IAM policies and private network rules with actual observations.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, network]
#   used_by:
#   - id: deploy.validation.runtime-configuration
#     path: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py
#   - id: deploy.library.entity-smoke.task-binding
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/implementation/task-binding.py
#   - id: deploy.library.core-persistence.task-operations
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/task-operations.py
"""Static ECS normalization and explicit read-only runtime comparison; never read secrets."""
from itertools import product
from pathlib import Path
import re
import yaml

class Loader(yaml.SafeLoader): pass
def intrinsic(loader, tag, node):
    key = {"Ref": "Ref"}.get(tag, "Fn::" + tag)
    value = loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else loader.construct_sequence(node) if isinstance(node, yaml.SequenceNode) else loader.construct_mapping(node)
    return {key: value}
Loader.add_multi_constructor("!", intrinsic)

def resolve(value, conditions):
    if isinstance(value, dict):
        if set(value) == {"Fn::If"}:
            name, yes, no = value["Fn::If"]
            return resolve(yes if conditions[name] else no, conditions)
        if value == {"Ref": "AWS::NoValue"}: return None
        return {key: resolve(item, conditions) for key, item in value.items()}
    if isinstance(value, list):
        return [item for entry in value if (item := resolve(entry, conditions)) is not None]
    return value

def normalize(path, binding):
    """Normalize declared workloads, including explicitly selected sibling templates."""
    path = Path(path).absolute()
    workloads = binding["workloads"]
    if not isinstance(workloads, list) or not workloads:
        raise ValueError("workload-binding-invalid")
    groups, identities = {}, set()
    for workload in workloads:
        identity = workload.get("id") if isinstance(workload, dict) else None
        if not isinstance(identity, str) or not identity or identity in identities:
            raise ValueError("workload-binding-invalid")
        identities.add(identity)
        source = path
        if "provider_template" in workload:
            name = workload["provider_template"]
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
                raise ValueError("workload-template-invalid")
            source = path.with_name(name)
        if not source.is_file() or source.is_symlink() or any(parent.is_symlink() for parent in source.parents):
            raise ValueError("workload-template-invalid")
        groups.setdefault(source, []).append(workload)
    result = {}
    for source, selected in groups.items():
        try:
            result.update(_normalize_template(source, {**binding, "workloads": selected}))
        except (OSError, KeyError, TypeError, AttributeError, yaml.YAMLError):
            raise ValueError("runtime-provider-configuration-invalid") from None
    return result


def _normalize_template(path, binding):
    doc = yaml.load(path.read_text(), Loader=Loader)
    names = set()
    def visit(value):
        if isinstance(value, dict):
            if "Fn::If" in value: names.add(value["Fn::If"][0])
            for item in value.values(): visit(item)
        elif isinstance(value, list):
            for item in value: visit(item)
    visit(doc)
    if len(names) > 8: raise ValueError("conditional-state-space-unbounded")
    result = {item["id"]: [] for item in binding["workloads"]}
    for bits in product((False, True), repeat=len(names)):
        resources = resolve(doc, dict(zip(sorted(names), bits)))["Resources"]
        for workload in binding["workloads"]:
            resource = resources[workload["provider_reference"]]
            if resource["Type"] == "AWS::ECS::Service":
                resource = resources[resource["Properties"]["TaskDefinition"]["Ref"]]
            if resource["Type"] != "AWS::ECS::TaskDefinition": raise ValueError("workload-kind-unsupported")
            properties = resource["Properties"]
            containers = properties["ContainerDefinitions"]
            container_name = workload.get("configuration_container")
            selected = [entry for entry in containers if entry.get("Name") == container_name] if container_name else containers[:1]
            if len(selected) != 1: raise ValueError("container-binding-invalid")
            container = selected[0]
            environment = {entry["Name"]: entry.get("Value") for entry in container.get("Environment", [])}
            secrets = {entry["Name"]: entry.get("ValueFrom") for entry in container.get("Secrets", [])}
            if len(environment) != len(container.get("Environment", [])): raise ValueError("duplicate-environment")
            if any(value is None or value == "" for value in secrets.values()): raise ValueError("empty-secret-reference")
            identity = properties.get("TaskRoleArn")
            permission_ok = True
            for role_key, required_actions in workload.get("required_role_actions", {}).items():
                role = properties.get(role_key)
                if isinstance(role, dict) and "Fn::GetAtt" in role:
                    name = role["Fn::GetAtt"]
                    role_name = name.split(".")[0] if isinstance(name, str) else name[0]
                    policies = resources[role_name]["Properties"].get("Policies", [])
                    actions = set()
                    for policy in policies:
                        for statement in policy["PolicyDocument"].get("Statement", []):
                            if statement.get("Effect") == "Allow":
                                action = statement.get("Action", [])
                                actions.update([action] if isinstance(action, str) else action)
                    permission_ok = permission_ok and set(required_actions).issubset(actions)
                else: permission_ok = False
            result[workload["id"]].append({"environment": environment, "secrets": secrets, "identity": identity, "command": container.get("Command"), "permissions_valid": permission_ok})
    return result


def package_projection(path, selector):
    """Package behavior inputs, independent of current IAM/deployment authority.

    Select declared container names (or every container with '*'), retaining
    commands, environment, secret references, resource limits and capability
    conditions. Resolve references to template parameter defaults and SSM
    configuration values without fetching secrets or provider state.
    """
    import re
    doc=yaml.load(path.read_text(),Loader=Loader)
    if not isinstance(doc,dict) or not isinstance(doc.get('Resources'),dict):raise ValueError('package-template-invalid')
    wanted=None if selector=='*' else set(selector.split(','))
    if wanted is not None and (not wanted or any(not re.fullmatch(r'[A-Za-z0-9_.-]+',name) for name in wanted)):raise ValueError('package-container-selector-invalid')
    found=set()
    def selected(value):
        if isinstance(value,list):return [item for candidate in value if (item:=selected(candidate)) is not None]
        if not isinstance(value,dict):return None
        if set(value)=={'Fn::If'}:
            condition,yes,no=value['Fn::If'];yes,no=selected(yes),selected(no)
            return {'Fn::If':[condition,yes,no]} if yes or no else None
        name=value.get('Name')
        if isinstance(name,str) and (wanted is None or name in wanted):found.add(name);return value
        return None
    tasks={}
    for name,resource in doc['Resources'].items():
        if not isinstance(resource,dict) or resource.get('Type')!='AWS::ECS::TaskDefinition':continue
        properties=resource.get('Properties',{});containers=selected(properties.get('ContainerDefinitions',[]))
        if containers:
            tasks[name]={key:properties[key] for key in ['Cpu','Memory','RuntimePlatform','NetworkMode','RequiresCompatibilities','EphemeralStorage','Volumes'] if key in properties}
            tasks[name]['ContainerDefinitions']=containers
    if not tasks or wanted is not None and wanted-found:raise ValueError('package-container-selection-missing')
    references=set();conditions=set();mappings=set()
    def discover(value):
        if isinstance(value,dict):
            supported={'Fn::GetAtt','Fn::Sub','Fn::If','Fn::FindInMap','Fn::Join','Fn::Split','Fn::Select','Fn::Equals','Fn::And','Fn::Or','Fn::Not','Fn::Base64','Fn::GetAZs','Fn::ImportValue'}
            if any(key.startswith('Fn::') and key not in supported for key in value):raise ValueError('package-intrinsic-unsupported')
            if 'Fn::FindInMap' in value:
                lookup=value['Fn::FindInMap']
                if not isinstance(lookup,list) or len(lookup)!=3 or not isinstance(lookup[0],str):raise ValueError('package-mapping-reference-unsupported')
                mappings.add(lookup[0])
            if set(value)=={'Condition'} and isinstance(value.get('Condition'),str):conditions.add(value['Condition'])
            if isinstance(value.get('Ref'),str):references.add(value['Ref'])
            if 'Fn::GetAtt' in value:
                name=value['Fn::GetAtt'];references.add(name.split('.')[0] if isinstance(name,str) else name[0])
            if 'Fn::Sub' in value:
                substitution=value['Fn::Sub'];text=substitution if isinstance(substitution,str) else substitution[0]
                references.update(match.split('.')[0] for match in re.findall(r'\$\{([A-Za-z0-9_:.-]+)\}',text))
            if 'Fn::If' in value:conditions.add(value['Fn::If'][0])
            for item in value.values():discover(item)
        elif isinstance(value,list):
            for item in value:discover(item)
    discover(tasks);parameters={};configuration={};condition_values={};mapping_values={}
    for _ in range(len(doc['Resources'])+len(doc.get('Conditions',{}))+len(doc.get('Mappings',{}))+2):
        previous=(len(references),len(conditions),len(mappings))
        for name in sorted(conditions):
            if name not in doc.get('Conditions',{}):raise ValueError('package-condition-missing')
            condition_values[name]=doc['Conditions'][name];discover(condition_values[name])
        for name in sorted(mappings):
            if name not in doc.get('Mappings',{}):raise ValueError('package-mapping-missing')
            mapping_values[name]=doc['Mappings'][name];discover(mapping_values[name])
        for name in sorted(references):
            if name in doc.get('Parameters',{}):parameters[name]=doc['Parameters'][name]
            resource=doc['Resources'].get(name,{})
            if resource.get('Type')=='AWS::SSM::Parameter':
                values=resource.get('Properties',{});configuration[name]={key:values[key] for key in ['Name','Type','Value'] if key in values};discover(configuration[name])
        if previous==(len(references),len(conditions),len(mappings)):break
    return {'containers':tasks,'parameters':parameters,'conditions':condition_values,'configuration':configuration,'mappings':mapping_values}


# Runtime comparison consumes already checked source lineage; it grants no task capability.
import copy
import hashlib
import importlib.util
import json
from urllib.parse import unquote

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



def runtime_fingerprint(value):
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def observation_scope(provider):
    """Reuse identical configuration reads only within one caller-owned phase.

    A pre-submission guard creates a new scope. Runtime state, task results,
    logs, policy simulation and every mutation always reach the real provider.
    """
    selected = {("ecs", "describe-task-definition"), ("ec2", "describe-security-groups"),
                *(('iam', name) for name in ('get-role', 'list-role-policies', 'list-attached-role-policies', 'get-role-policy'))}
    observations = {}
    def observe(service, operation, **parameters):
        if (service, operation) not in selected: return provider(service, operation, **parameters)
        key = service, operation, json.dumps(parameters, sort_keys=True, allow_nan=False)
        if key not in observations: observations[key] = copy.deepcopy(provider(service, operation, **parameters))
        return copy.deepcopy(observations[key])
    return observe

def runtime_resolve(value, parameters, resources, workload, *, account, region, _attributes=None):
    if isinstance(value, list): return [runtime_resolve(item, parameters, resources, workload, account=account, region=region, _attributes=_attributes) for item in value]
    if not isinstance(value, dict): return value
    if set(value) == {"Ref"}:
        name = value["Ref"]
        known = {**{key: row["physical_id"] for key, row in resources.items() if row["type"] in {"AWS::EC2::SecurityGroup", "AWS::SecretsManager::Secret"}}, **parameters, "AWS::AccountId": account, "AWS::Region": region, "AWS::Partition": "aws"}
        require(isinstance(name, str) and name in known, "task-binding-source-not-supported", workload, "source")
        return known[name]
    if set(value) == {"Fn::GetAtt"}:
        parts = value["Fn::GetAtt"]
        if isinstance(parts, str): parts = parts.split(".", 1)
        if isinstance(parts, list) and len(parts) == 2 and _attributes is not None and tuple(parts) in _attributes:
            return _attributes[tuple(parts)]
        require(isinstance(parts, list) and len(parts) == 2 and isinstance(parts[0], str) and parts[0] in resources and parts[1] == "Arn"
                and resources[parts[0]]["type"] == "AWS::IAM::Role", "task-binding-source-not-supported", workload, "source")
        return "arn:aws:iam::" + account + ":role/" + resources[parts[0]]["physical_id"]
    if set(value) == {"Fn::Sub"}:
        text = value["Fn::Sub"]
        require(isinstance(text, str), "task-binding-source-not-supported", workload, "source")
        return re.sub(r"\$\{([^}]+)\}", lambda match: "${" + match[1][1:] + "}" if match[1].startswith("!") else runtime_resolve({"Fn::GetAtt": match[1].split(".", 1)} if "." in match[1] else {"Ref": match[1]}, parameters, resources, workload, account=account, region=region, _attributes=_attributes), text)
    require(not any(key == "Ref" or key.startswith("Fn::") for key in value), "task-binding-source-not-supported", workload, "source")
    return {key: runtime_resolve(item, parameters, resources, workload, account=account, region=region, _attributes=_attributes) for key, item in value.items()}

def lower_keys(value):
    if isinstance(value, list): return [lower_keys(item) for item in value]
    if isinstance(value, dict): return {key[:1].lower() + key[1:]: lower_keys(item) for key, item in value.items()}
    return value

def runtime_expected_task(logical, workload, parameters, resources, snapshot, *, account, region, _attributes=None):
    source = snapshot["Resources"][logical]["Properties"]
    allowed = {"Family", "Cpu", "Memory", "NetworkMode", "RequiresCompatibilities", "RuntimePlatform", "ExecutionRoleArn", "TaskRoleArn", "ContainerDefinitions", "Tags"}
    container_allowed = {"Name", "Image", "Essential", "ReadonlyRootFilesystem", "LinuxParameters", "Command", "LogConfiguration", "Environment", "Secrets", "PortMappings", "HealthCheck"}
    require(not set(source) - allowed and len(source["ContainerDefinitions"]) == 1 and not set(source["ContainerDefinitions"][0]) - container_allowed,
            "task-binding-source-not-supported", workload, "source")
    return lower_keys(runtime_resolve(source, parameters, resources, workload, account=account, region=region, _attributes=_attributes))

def sorted_entries(value, key, workload, *, code="task-binding-container-not-confirmed", field="container"):
    require(isinstance(value, list) and all(isinstance(item, dict) and isinstance(item.get(key), str) for item in value)
            and len({item[key] for item in value}) == len(value), code, workload, field)
    return sorted(value, key=lambda item: item[key])

def runtime_task_definition(provider, logical, workload, parameters, resources, snapshot, *, account, region, _attributes=None):
    expected = runtime_expected_task(logical, workload, parameters, resources, snapshot, account=account, region=region, _attributes=_attributes)
    tags = expected.pop("tags", None)
    arn = resources[logical]["physical_id"]
    require(isinstance(arn, str) and re.fullmatch(r"arn:aws:ecs:" + region + ":" + account + ":task-definition/" + expected["family"] + r":[1-9][0-9]*", arn) is not None,
            "task-binding-definition-not-confirmed", workload, "identity")
    response = provider("ecs", "describe-task-definition", taskDefinition=arn, **({"include": ["TAGS"]} if tags is not None else {}))
    if tags is not None:
        tag_contract = {"code": "task-binding-definition-not-confirmed", "field": "identity"}
        require(isinstance(response, dict) and same(sorted_entries(response.get("tags"), "key", workload, **tag_contract),
                sorted_entries(tags, "key", workload, **tag_contract)), "task-binding-definition-not-confirmed", workload, "identity")
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
    return arn, {**expected, **({"tags": tags} if tags is not None else {})}

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

def runtime_managed_policy(provider, arn, expected, workload):
    """Check the native default version; an ARN alone cannot qualify its grant."""
    response = provider("iam", "get-policy", PolicyArn=arn)
    metadata = response.get("Policy") if isinstance(response, dict) else None
    require(isinstance(metadata, dict) and metadata.get("Arn") == arn
            and metadata.get("IsAttachable") is True and isinstance(metadata.get("DefaultVersionId"), str)
            and re.fullmatch(r"v[1-9][0-9]*", metadata["DefaultVersionId"]),
            "task-binding-policy-not-confirmed", workload, "roles")
    version = metadata["DefaultVersionId"]
    response = provider("iam", "get-policy-version", PolicyArn=arn, VersionId=version)
    current = response.get("PolicyVersion") if isinstance(response, dict) else None
    require(isinstance(current, dict) and current.get("VersionId") == version
            and current.get("IsDefaultVersion") is True
            and same(policy(current.get("Document"), workload), policy(expected, workload)),
            "task-binding-policy-not-confirmed", workload, "roles")
    return runtime_fingerprint({"arn": arn, "version": version, "policy": policy(expected, workload)})


def runtime_role(provider, logical, parameters, resources, workload, snapshot, *, account, region, _attributes=None, _managed_policies=None):
    name = resources[logical]["physical_id"]
    require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_+=,.@-]{1,64}", name) is not None, "task-binding-role-not-confirmed", workload, "roles")
    expected = runtime_resolve(snapshot["Resources"][logical]["Properties"], parameters, resources, workload, account=account, region=region, _attributes=_attributes)
    require(_managed_policies is not None or "ManagedPolicyArns" not in expected, "task-binding-source-not-supported", workload, "roles")
    managed = expected.get("ManagedPolicyArns", [])
    require(isinstance(managed, list) and all(isinstance(arn, str) for arn in managed)
            and len(set(managed)) == len(managed) and (_managed_policies is None or isinstance(_managed_policies, dict)
                and all(arn in _managed_policies for arn in managed)), "task-binding-source-not-supported", workload, "roles")
    boundary = expected.get("PermissionsBoundary")
    require("PermissionsBoundary" not in expected or isinstance(boundary, str) and re.fullmatch(r"arn:aws:iam::" + account + r":policy/[A-Za-z0-9_+=,.@/-]+", boundary) is not None,
            "task-binding-source-not-supported", workload, "roles")
    require("RoleName" not in expected or expected["RoleName"] == name, "task-binding-role-not-confirmed", workload, "roles")
    response = provider("iam", "get-role", RoleName=name)
    value = response.get("Role") if isinstance(response, dict) else None
    expected_boundary = {"PermissionsBoundaryType": "Policy", "PermissionsBoundaryArn": boundary} if boundary is not None else None
    require(isinstance(value, dict) and value.get("RoleName") == name and value.get("Arn") == "arn:aws:iam::" + account + ":role/" + name and value.get("Path") == "/"
            and (value.get("PermissionsBoundary") == expected_boundary if boundary is not None else "PermissionsBoundary" not in value)
            and same(policy(value.get("AssumeRolePolicyDocument"), workload), policy(expected["AssumeRolePolicyDocument"], workload)), "task-binding-role-not-confirmed", workload, "roles")
    attached = provider("iam", "list-attached-role-policies", RoleName=name)
    rows = attached.get("AttachedPolicies") if isinstance(attached, dict) else None
    require(isinstance(rows, list) and len(rows) == len(managed)
            and all(isinstance(row, dict) and set(row) == {"PolicyName", "PolicyArn"}
                    and isinstance(row["PolicyArn"], str) and row["PolicyName"] == row["PolicyArn"].rsplit("/", 1)[-1] for row in rows)
            and {row["PolicyArn"] for row in rows} == set(managed)
            and attached.get("IsTruncated") is False and not attached.get("Marker"), "task-binding-attached-policy-prohibited", workload, "roles")
    for arn in managed:
        runtime_managed_policy(provider, arn, _managed_policies[arn], workload)
    inline = provider("iam", "list-role-policies", RoleName=name)
    policies = {item["PolicyName"]: item["PolicyDocument"] for item in expected.get("Policies", [])}
    require(isinstance(inline, dict) and isinstance(inline.get("PolicyNames"), list) and len(inline["PolicyNames"]) == len(policies) and all(isinstance(item, str) for item in inline["PolicyNames"])
            and set(inline["PolicyNames"]) == set(policies) and inline.get("IsTruncated") is False and not inline.get("Marker"), "task-binding-policy-inventory-not-confirmed", workload, "roles")
    for selected, document in policies.items():
        observed = provider("iam", "get-role-policy", RoleName=name, PolicyName=selected)
        require(isinstance(observed, dict) and observed.get("RoleName") == name and observed.get("PolicyName") == selected and same(policy(observed.get("PolicyDocument"), workload), policy(document, workload)), "task-binding-policy-not-confirmed", workload, "roles")
    return runtime_fingerprint(expected)

def permissions(rows, workload, *, account):
    require(isinstance(rows, list) and len(rows) <= 20, "task-binding-network-not-confirmed", workload, "network")
    result = []
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("IpProtocol"), str) and type(row.get("FromPort")) is int and type(row.get("ToPort")) is int and not row.get("Ipv6Ranges"), "task-binding-network-not-confirmed", workload, "network")
        destinations = []
        for key, field in (("UserIdGroupPairs", "GroupId"), ("IpRanges", "CidrIp"), ("PrefixListIds", "PrefixListId")):
            values = row.get(key, [])
            require(isinstance(values, list) and all(isinstance(item, dict) and isinstance(item.get(field), str) for item in values), "task-binding-network-not-confirmed", workload, "network")
            if key == "UserIdGroupPairs": require(all(item.get("UserId", account) == account and not item.get("VpcPeeringConnectionId") for item in values), "task-binding-network-not-confirmed", workload, "network")
            destinations.extend((field, item[field]) for item in values)
        require(bool(destinations), "task-binding-network-not-confirmed", workload, "network")
        result.extend((row["IpProtocol"], row["FromPort"], row["ToPort"], *destination) for destination in destinations)
    require(len(set(result)) == len(result), "task-binding-network-not-confirmed", workload, "network")
    return sorted(result)

def runtime_network(provider, logical, workload, context, *, account, region, related=(), destination_items=None):
    """Compare the selected owned group; only required ingress of its peers."""
    parameters, resources, snapshot = context["parameters"], context["resources"], context["template"]
    group_id = resources[logical]["physical_id"]
    require(resources[logical]["type"] == "AWS::EC2::SecurityGroup" and isinstance(group_id, str)
            and re.fullmatch(r"sg-(?:[a-f0-9]{8}|[a-f0-9]{17})", group_id), "task-binding-network-not-confirmed", workload, "network")
    expected = {"ingress": [], "egress": []}
    def append_rule(direction, row):
        require(isinstance(row, dict) and type(row.get("FromPort")) is int and type(row.get("ToPort")) is int,
                "task-binding-source-not-supported", workload, "network")
        names = (("SourceSecurityGroupId" if direction == "ingress" else "DestinationSecurityGroupId", "GroupId"),
                 ("CidrIp", "CidrIp"), ("SourcePrefixListId" if direction == "ingress" else "DestinationPrefixListId", "PrefixListId"))
        destinations = [(field, row[key]) for key, field in names if key in row]
        require(len(destinations) == 1 and not set(row) - {"GroupId", "IpProtocol", "FromPort", "ToPort", "Description", *(key for key, _ in names)},
                "task-binding-source-not-supported", workload, "network")
        expected[direction].append((str(row["IpProtocol"]), row["FromPort"], row["ToPort"], *destinations[0]))
    for selected in (context, *related):
        for name, resource in selected["template"]["Resources"].items():
            kind = resource["Type"]
            if kind == "AWS::EC2::SecurityGroup":
                if selected["resources"][name]["physical_id"] != group_id: continue
                properties = runtime_resolve(resource["Properties"], selected["parameters"], selected["resources"], workload, account=account, region=region)
                for direction, field in (("ingress", "SecurityGroupIngress"), ("egress", "SecurityGroupEgress")):
                    for row in properties.get(field, []): append_rule(direction, row)
            elif kind in {"AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress"}:
                row = runtime_resolve(resource["Properties"], selected["parameters"], selected["resources"], workload, account=account, region=region)
                if row["GroupId"] == group_id: append_rule("ingress" if kind.endswith("Ingress") else "egress", row)
    def observe(identity, reason, item):
        response = provider("ec2", "describe-security-groups", GroupIds=[identity])
        groups = response.get("SecurityGroups") if isinstance(response, dict) else None
        require(isinstance(groups, list) and len(groups) == 1 and isinstance(groups[0], dict)
                and groups[0].get("GroupId") == identity and groups[0].get("VpcId") == parameters["VpcId"]
                and groups[0].get("OwnerId") == account, reason, workload, "network", item)
        return groups[0]
    group = observe(group_id, "task-binding-network-not-confirmed", "network")
    actual = {"ingress": permissions(group.get("IpPermissions"), workload, account=account),
              "egress": permissions(group.get("IpPermissionsEgress"), workload, account=account)}
    require(all(actual[key] == sorted(set(expected[key])) for key in expected), "task-binding-network-not-confirmed", workload, "network")
    for protocol, start, end, field, destination in sorted(set(expected["egress"])):
        if field != "GroupId": continue
        item = (destination_items or {}).get((destination, start), "network")
        peer = observe(destination, "task-binding-destination-not-confirmed", item)
        rows = peer.get("IpPermissions")
        require(isinstance(rows, list) and any(isinstance(row, dict) and row.get("IpProtocol") == protocol
                and type(row.get("FromPort")) is int and row["FromPort"] == start
                and type(row.get("ToPort")) is int and row["ToPort"] == end
                and isinstance(row.get("UserIdGroupPairs"), list)
                and any(isinstance(pair, dict) and pair.get("GroupId") == group_id and pair.get("UserId", account) == account
                        and not pair.get("VpcPeeringConnectionId") for pair in row["UserIdGroupPairs"]) for row in rows),
                "task-binding-destination-not-confirmed", workload, "network", item)
    return group_id, runtime_fingerprint(actual)


def check_runtime_view(view, workload, *, account, region):
    fields = {"schema", "binding", "source_plan_sha256", "account", "region", "component", "stack", "stack_id",
              "phase", "template_reference", "template", "parameters", "resources", "outputs", "custody", "observed_at"}
    require(isinstance(view, dict) and set(view) == fields and view["schema"] == "deploy/aws-session-runtime-view/v1"
            and view["account"] == account and view["region"] == region and isinstance(view["component"], str)
            and view["phase"] in {"creation", "activation", "prepare-discard"}
            and type(view["observed_at"]) is int and view["observed_at"] >= 0
            and isinstance(view["source_plan_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", view["source_plan_sha256"])
            and isinstance(view["binding"], dict)
            and set(view["binding"]) == {"target", "scope", "session_id", "source_inputs_sha256", "starts_at", "expires_at"}
            and all(isinstance(view["binding"][key], str) and view["binding"][key] for key in ("target", "scope"))
            and isinstance(view["binding"]["session_id"], str) and re.fullmatch(r"[a-f0-9]{32}", view["binding"]["session_id"])
            and isinstance(view["binding"]["source_inputs_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", view["binding"]["source_inputs_sha256"])
            and all(type(view["binding"][key]) is int for key in ("starts_at", "expires_at"))
            and 0 <= view["binding"]["starts_at"] < view["binding"]["expires_at"]
            and isinstance(view["stack"], str) and isinstance(view["stack_id"], str)
            and re.fullmatch(r"arn:aws:cloudformation:" + re.escape(region) + ":" + re.escape(account)
                             + ":stack/" + re.escape(view["stack"]) + r"/[a-f0-9-]{36}", view["stack_id"])
            and isinstance(view["template_reference"], str) and bool(view["template_reference"])
            and isinstance(view["custody"], dict)
            and set(view["custody"]) == {"creation_request_sha256", "change_set_id_sha256", "template_sha256", "parameters_sha256", "resources_sha256"}
            and all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in view["custody"].values())
            and isinstance(view["template"], dict) and isinstance(view["template"].get("Parameters"), dict)
            and isinstance(view["template"].get("Resources"), dict)
            and isinstance(view["outputs"], dict) and not set(view["outputs"]) - set(view["template"].get("Outputs", {}))
            and all(isinstance(value, str) and value for value in view["outputs"].values()),
            "runtime-binding-invalid", workload, "source")
    names, source = set(view["template"]["Parameters"]), view["template"]["Resources"]
    require(isinstance(view["parameters"], dict) and set(view["parameters"]) == names
            and all(isinstance(value, str) and not any(c in value for c in "\n\r\0") for value in view["parameters"].values()),
            "task-binding-parameters-not-confirmed", workload, "source")
    require(isinstance(view["resources"], dict) and set(view["resources"]) == set(source)
            and all(isinstance(row, dict) and set(row) == {"type", "physical_id"} and row["type"] == source[name]["Type"]
                    and isinstance(row["physical_id"], str) and row["physical_id"] for name, row in view["resources"].items()),
            "task-binding-resources-not-confirmed", workload, "source")
    return copy.deepcopy(view)


def task_runtime(view, configuration, workload, *, account, region):
    container = configuration["containerDefinitions"][0]
    logging = container["logConfiguration"]
    require(logging["logDriver"] == "awslogs" and logging["options"]["awslogs-region"] == region, "runtime-binding-invalid", workload, "source")
    value = {"schema": "deploy/aws-task-runtime/v1", "session_id": view["binding"]["session_id"],
             "source_plan_sha256": view["source_plan_sha256"],
             "binding_sha256": runtime_fingerprint({key: view[key] for key in ("binding", "custody", "stack_id")}),
             "stack_id": view["stack_id"], "cluster_arn": view["parameters"]["ClusterArn"], "family": configuration["family"],
             "container_name": container["name"], "log_group": logging["options"]["awslogs-group"],
             "log_stream_prefix": logging["options"]["awslogs-stream-prefix"]}
    path = Path(__file__).resolve().parents[4] / "shared/provider-adapters/aws/tasks.py"
    spec = importlib.util.spec_from_file_location("checked_runtime_tasks", path)
    tasks = importlib.util.module_from_spec(spec); spec.loader.exec_module(tasks)
    try: return tasks.runtime_binding(value, account=account, region=region)
    except tasks.TaskFailure: raise BindingFailure("runtime-binding-invalid", workload, "source") from None


def _runtime_attributes(provider, view, logical, workload, *, account, region):
    """Read only attributes reached by the selected task and its own role policies."""
    source, resources, parameters = view["template"]["Resources"], view["resources"], view["parameters"]
    wanted = set()
    def discover(value):
        if isinstance(value, list):
            for item in value: discover(item)
        elif isinstance(value, dict):
            if set(value) == {"Fn::GetAtt"}:
                parts = value["Fn::GetAtt"]; parts = parts.split(".", 1) if isinstance(parts, str) else parts
                if isinstance(parts, list) and len(parts) == 2: wanted.add(tuple(parts))
            if set(value) == {"Fn::Sub"} and isinstance(value["Fn::Sub"], str):
                wanted.update(tuple(item.split(".", 1)) for item in re.findall(r"\$\{([^}]+)\}", value["Fn::Sub"]) if "." in item)
            for item in value.values(): discover(item)
    properties = source[logical]["Properties"]
    discover(properties)
    for field in ("ExecutionRoleArn", "TaskRoleArn"):
        if field not in properties: continue
        ref = properties[field].get("Fn::GetAtt") if isinstance(properties[field], dict) else None
        parts = ref.split(".", 1) if isinstance(ref, str) else ref
        require(isinstance(parts, list) and len(parts) == 2 and parts[1] == "Arn"
                and resources.get(parts[0], {}).get("type") == "AWS::IAM::Role", "task-binding-source-not-supported", workload, "roles")
        discover(source[parts[0]]["Properties"])
    result = {}
    for name in sorted({name for name, attribute in wanted if resources.get(name, {}).get("type") == "AWS::RDS::DBInstance"}):
        attrs = {attribute for selected, attribute in wanted if selected == name}
        require(attrs <= {"Endpoint.Address", "Endpoint.Port", "DbiResourceId"}, "task-binding-source-not-supported", workload, "source")
        identifier = resources[name]["physical_id"]
        response = provider("rds", "describe-db-instances", DBInstanceIdentifier=identifier)
        databases = response.get("DBInstances") if isinstance(response, dict) else None
        require(isinstance(databases, list) and len(databases) == 1 and isinstance(databases[0], dict)
                and not response.get("Marker") and not response.get("NextToken"), "task-binding-resources-not-confirmed", workload, "source")
        database = databases[0]; endpoint = database.get("Endpoint")
        require(database.get("DBInstanceIdentifier") == identifier
                and database.get("DBInstanceArn") == "arn:aws:rds:" + region + ":" + account + ":db:" + identifier
                and database.get("DBInstanceStatus") == "available" and isinstance(endpoint, dict)
                and isinstance(endpoint.get("Address"), str) and re.fullmatch(r"[A-Za-z0-9.-]{1,253}", endpoint["Address"])
                and type(endpoint.get("Port")) is int and 1 <= endpoint["Port"] <= 65535
                and isinstance(database.get("DbiResourceId"), str) and re.fullmatch(r"db-[A-Z0-9]{1,64}", database["DbiResourceId"]),
                "task-binding-resources-not-confirmed", workload, "source")
        values = {"Endpoint.Address": endpoint["Address"], "Endpoint.Port": str(endpoint["Port"]), "DbiResourceId": database["DbiResourceId"]}
        for attribute in ("Endpoint.Address", "DbiResourceId"):
            outputs = [key for key, row in view["template"].get("Outputs", {}).items()
                       if row.get("Value") in ({"Fn::GetAtt": [name, attribute]}, {"Fn::GetAtt": name + "." + attribute})]
            require(bool(outputs) and all(view["outputs"].get(key) == values[attribute] for key in outputs),
                    "task-binding-resources-not-confirmed", workload, "source")
        result.update({(name, attribute): value for attribute, value in values.items()})
    return result


def inspect_runtime(provider, *, view, selection, related_views=(), account, region):
    """Source-selected checked configuration, not freshness or execution authority."""
    workload = selection.get("workload") if isinstance(selection, dict) else None
    require(isinstance(workload, str) and workload, "task-binding-selection-invalid", "unselected", "selection")
    try:
        require(callable(provider) and isinstance(selection, dict) and set(selection) == {"workload", "definition", "security_group"},
                "task-binding-selection-invalid", workload, "selection")
        view = check_runtime_view(view, workload, account=account, region=region)
        require(isinstance(related_views, (list, tuple)), "runtime-binding-invalid", workload, "source")
        views = [view] + [check_runtime_view(item, workload, account=account, region=region) for item in related_views]
        require(len({item["component"] for item in views}) == len(views)
                and len({item["stack_id"] for item in views}) == len(views)
                and all(same(item["binding"], view["binding"]) and item["source_plan_sha256"] == view["source_plan_sha256"] for item in views),
                "runtime-binding-invalid", workload, "source")
        logical, group = selection["definition"], selection["security_group"]
        require(isinstance(logical, str) and view["resources"].get(logical, {}).get("type") == "AWS::ECS::TaskDefinition"
                and isinstance(group, dict) and set(group) in ({"component", "resource"}, {"component", "resource", "parameter", "output"})
                and isinstance(group["component"], str) and isinstance(group["resource"], str), "task-binding-selection-invalid", workload, "selection")
        selected = [item for item in views if item["component"] == group["component"]]
        require(len(selected) == 1 and selected[0]["resources"].get(group["resource"], {}).get("type") == "AWS::EC2::SecurityGroup",
                "task-binding-selection-invalid", workload, "selection")
        group_view = selected[0]
        if group_view is not view:
            identity = group_view["resources"][group["resource"]]["physical_id"]
            require(set(group) == {"component", "resource", "parameter", "output"}
                    and isinstance(group["parameter"], str) and isinstance(group["output"], str)
                    and group_view["template"].get("Outputs", {}).get(group["output"], {}).get("Value") == {"Ref": group["resource"]}
                    and group_view["outputs"].get(group["output"]) == identity
                    and view["template"]["Parameters"].get(group["parameter"], {}).get("Type") == "AWS::EC2::SecurityGroup::Id"
                    and view["parameters"].get(group["parameter"]) == identity
                    and group_view["parameters"]["VpcId"] == view["parameters"]["VpcId"],
                    "task-binding-resources-not-confirmed", workload, "source")
        else:
            require(set(group) == {"component", "resource"}, "task-binding-selection-invalid", workload, "selection")
        attributes = _runtime_attributes(provider, view, logical, workload, account=account, region=region)
        # Secret reference identity is observed without retrieving a value.
        references = set()
        def secrets(value):
            if isinstance(value, dict):
                if set(value) == {"Ref"} and view["resources"].get(value["Ref"], {}).get("type") == "AWS::SecretsManager::Secret": references.add(value["Ref"])
                for item in value.values(): secrets(item)
            elif isinstance(value, list):
                for item in value: secrets(item)
        properties = view["template"]["Resources"][logical]["Properties"]; secrets(properties)
        for name in references:
            identity = view["resources"][name]["physical_id"]
            response = provider("secretsmanager", "describe-secret", SecretId=identity)
            expected_name = runtime_resolve(view["template"]["Resources"][name]["Properties"]["Name"], view["parameters"], view["resources"], workload, account=account, region=region)
            require(isinstance(response, dict) and response.get("ARN") == identity and response.get("Name") == expected_name
                    and re.fullmatch("arn:aws:secretsmanager:" + re.escape(region) + ":" + account + ":secret:" + re.escape(expected_name) + "-[A-Za-z0-9]{6}", identity)
                    and "DeletedDate" not in response, "task-binding-resources-not-confirmed", workload, "source")
        definition, configuration = runtime_task_definition(provider, logical, workload, view["parameters"], view["resources"], view["template"], account=account, region=region, _attributes=attributes)
        identities = {}
        for field in ("ExecutionRoleArn", "TaskRoleArn"):
            if field not in properties: continue
            parts = properties[field]["Fn::GetAtt"]; parts = parts.split(".", 1) if isinstance(parts, str) else parts
            try: identities[parts[0]] = runtime_role(provider, parts[0], view["parameters"], view["resources"], workload, view["template"], account=account, region=region, _attributes=attributes)
            except BindingFailure as failure:
                failure.item = "execution-role" if field == "ExecutionRoleArn" else "task-role"
                raise
        group_id, network_digest = runtime_network(provider, group["resource"], workload, group_view, account=account, region=region,
                                                   related=tuple(item for item in views if item is not group_view))
        return {"runtime": task_runtime(view, configuration, workload, account=account, region=region),
                "definition": definition, "security_group": group_id, "subnets": view["parameters"]["PrivateSubnetIds"].split(","),
                "configuration_sha256": runtime_fingerprint(configuration), "roles_sha256": runtime_fingerprint(identities), "network_sha256": network_digest}
    except BindingFailure: raise
    except Exception: raise BindingFailure("runtime-binding-invalid", workload, "source") from None
