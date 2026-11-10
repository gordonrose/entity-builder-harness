#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject changed immutable task, IAM and network bindings using actual-template controlled provider responses without AWS observations.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
import importlib.util
import json
from pathlib import Path
from urllib.parse import quote

if not __debug__: raise SystemExit("ENTITY_SMOKE_TASK_BINDING_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
M = module("entity_smoke_task_binding_fixture", DIRECTORY / "task-binding.py")
F = module("entity_smoke_task_binding_source_fixture", DIRECTORY / "deployment-control-test.py")
CANARY = "private-task-secret-reference-and-provider-canary"
EMPTY_CONTAINER_DEFAULTS = {"credentialSpecs": [], "dnsSearchDomains": [], "dnsServers": [], "dockerLabels": {}, "dockerSecurityOptions": [], "entryPoint": [], "extraHosts": [], "links": []}
PARAMETERS = copy.deepcopy(F.PARAMETERS)
RESOURCES = {}
for index, (logical, kind) in enumerate(M.DEPLOY.RESOURCE_TYPES.items(), 1):
    physical = "owned-role-" + str(index)
    if kind == "AWS::EC2::SecurityGroup": physical = "sg-" + format(index, "017x")
    if kind == "AWS::ECS::TaskDefinition":
        workload = next(name for name, prefix in M.WORKLOADS.items() if logical == prefix + "TaskDefinition")
        physical = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-" + workload + ":1"
    RESOURCES[logical] = {"type": kind, "physical_id": physical}


def permission(row):
    value = {"IpProtocol": str(row["IpProtocol"]), "FromPort": row["FromPort"], "ToPort": row["ToPort"], "IpRanges": [], "Ipv6Ranges": [], "UserIdGroupPairs": [], "PrefixListIds": []}
    for key, collection, field in (("DestinationSecurityGroupId", "UserIdGroupPairs", "GroupId"), ("CidrIp", "IpRanges", "CidrIp"), ("DestinationPrefixListId", "PrefixListIds", "PrefixListId")):
        if key in row:
            value[collection].append({field: row[key], **({"UserId": M.ACCOUNT} if collection == "UserIdGroupPairs" else {})})
    return value


class Provider:
    def __init__(self, workload):
        self.calls, self.workload = [], workload
        self.task = M.expected_task(workload, PARAMETERS, RESOURCES)
        self.task.update(taskDefinitionArn=RESOURCES[M.WORKLOADS[workload] + "TaskDefinition"]["physical_id"], revision=1, status="ACTIVE", compatibilities=["EC2", "FARGATE"], registeredBy="arn:aws:iam::337159794548:role/fixture")
        self.task["volumes"] = []; self.task["placementConstraints"] = []; self.task["enableFaultInjection"] = False
        self.task["containerDefinitions"][0].update(cpu=0, mountPoints=[], volumesFrom=[])
        self.task["containerDefinitions"][0].update(copy.deepcopy(EMPTY_CONTAINER_DEFAULTS))
        self.task["containerDefinitions"][0]["linuxParameters"].update(devices=[], tmpfs=[])
        self.roles, self.policies, self.groups = {}, {}, {}
        self.attached, self.paginated, self.encoded = False, False, False
        for logical, resource in M.DEPLOY.source()[1]["Resources"].items():
            if resource["Type"] == "AWS::IAM::Role":
                properties = M.resolve(resource["Properties"], PARAMETERS, RESOURCES, workload)
                name = RESOURCES[logical]["physical_id"]
                self.roles[name] = {"RoleName": name, "Arn": "arn:aws:iam::337159794548:role/" + name, "Path": "/", "AssumeRolePolicyDocument": properties["AssumeRolePolicyDocument"]}
                self.policies[name] = {entry["PolicyName"]: entry["PolicyDocument"] for entry in properties["Policies"]}
            if resource["Type"] == "AWS::EC2::SecurityGroup":
                group = RESOURCES[logical]["physical_id"]
                properties = M.resolve(resource["Properties"], PARAMETERS, RESOURCES, workload)
                self.groups[group] = {"GroupId": group, "VpcId": PARAMETERS["VpcId"], "OwnerId": M.ACCOUNT, "IpPermissions": [], "IpPermissionsEgress": [permission(row) for row in properties["SecurityGroupEgress"]]}
        for group in (PARAMETERS["EndpointSecurityGroupId"], PARAMETERS["DatabaseSecurityGroupId"]):
            self.groups[group] = {"GroupId": group, "VpcId": PARAMETERS["VpcId"], "OwnerId": M.ACCOUNT, "IpPermissions": [], "IpPermissionsEgress": []}
        for logical, resource in M.DEPLOY.source()[1]["Resources"].items():
            if resource["Type"] == "AWS::EC2::SecurityGroupIngress":
                row = M.resolve(resource["Properties"], PARAMETERS, RESOURCES, workload)
                self.groups[row["GroupId"]]["IpPermissions"].append(permission({"IpProtocol": row["IpProtocol"], "FromPort": row["FromPort"], "ToPort": row["ToPort"], "DestinationSecurityGroupId": row["SourceSecurityGroupId"]}))

    def __call__(self, service, operation, **parameters):
        self.calls.append((service, operation, parameters))
        if operation == "describe-task-definition":
            assert parameters == {"taskDefinition": self.task["taskDefinitionArn"]}
            return {"taskDefinition": copy.deepcopy(self.task)}
        if operation == "describe-security-groups": return {"SecurityGroups": [copy.deepcopy(self.groups[name]) for name in parameters["GroupIds"]]}
        name = parameters["RoleName"]
        if operation == "get-role": return {"Role": copy.deepcopy(self.roles[name])}
        if operation == "list-attached-role-policies": return {"AttachedPolicies": [{"PolicyArn": CANARY}] if self.attached else [], "IsTruncated": False}
        if operation == "list-role-policies": return {"PolicyNames": list(self.policies[name]), "IsTruncated": self.paginated}
        assert operation == "get-role-policy"
        selected = parameters["PolicyName"]
        document = self.policies[name][selected]
        return {"RoleName": name, "PolicyName": selected, "PolicyDocument": quote(json.dumps(document), safe="") if self.encoded else copy.deepcopy(document)}


def fails(call, code, workload):
    try: call()
    except M.BindingFailure as failure:
        assert failure.code == code, (failure.code, code)
        assert failure.workload == workload and failure.field in {"selection", "source", "identity", "container", "roles", "network"}
        assert failure.item in {"selection", "source", "identity", "container", "roles", "network", "execution-role", "task-role", "delivery-ingress", "private-server-ingress", "database-ingress"}
        assert CANARY not in json.dumps(vars(failure)) and CANARY not in str(failure)
        return failure
    else: raise AssertionError("expected exact binding rejection")


def main():
    for workload in M.WORKLOADS:
        provider = Provider(workload)
        original_source, reads = M.DEPLOY.source, []
        def source_once():
            reads.append(True)
            return original_source()
        M.DEPLOY.source = source_once
        result = M.inspect(provider, workload, PARAMETERS, RESOURCES)
        assert len(reads) == 1, "task, roles and network must consume one checked source snapshot per inspection"
        M.inspect(provider, workload, PARAMETERS, RESOURCES)
        assert len(reads) == 2, "a later inspection must revalidate source, not reuse a global cache"
        M.DEPLOY.source = original_source
        assert result["definition"].endswith("entity-smoke-" + workload + ":1") and len(result["roles_sha256"]) == 71
        assert CANARY not in json.dumps(result) and PARAMETERS["AdministratorSecretArn"] not in json.dumps(result) and PARAMETERS["DatabaseEndpoint"] not in json.dumps(result)
        container = provider.task["containerDefinitions"][0]
        assert container["readonlyRootFilesystem"] is True and container["linuxParameters"]["capabilities"]["drop"] == ["ALL"]
        assert container["image"].endswith("@" + PARAMETERS["ImageDigest"])
        assert {entry["name"]: entry["value"] for entry in container["environment"]}["PLATFORM_SOURCE_COMMIT_SHA"] == PARAMETERS["SourceRevision"]
        if workload in {"administration", "verifier"}: assert "taskRoleArn" not in provider.task
        if workload == "administration":
            assert container["command"] == ["artifacts/kanbien-entity-smoke-administration.main.js"]
            assert container["secrets"] == [{"name": "PERSISTENCE_ADMINISTRATOR_CREDENTIALS", "valueFrom": PARAMETERS["AdministratorSecretArn"]}]
            assert not any(entry["name"] == "PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE" for entry in container["environment"])
        else: assert "secrets" not in container
        if workload == "verifier": assert not any(entry["name"].startswith("PERSISTENCE_") for entry in container["environment"])
        if workload in {"server", "migration", "database-proof"}:
            name = RESOURCES[M.WORKLOADS[workload] + "TaskRole"]["physical_id"]
            document = next(iter(provider.policies[name].values()))
            assert document["Statement"] == [{"Effect": "Allow", "Action": "rds-db:connect", "Resource": "arn:aws:rds-db:eu-west-1:337159794548:dbuser:" + PARAMETERS["DatabaseResourceId"] + "/entity_smoke_" + ("migration" if workload == "migration" else "runtime")}]
        provider.encoded = True
        assert M.inspect(provider, workload, PARAMETERS, RESOURCES) == result, "documented URL-encoded and SDK-decoded policies must agree"

    for key, default in {**EMPTY_CONTAINER_DEFAULTS, "devices": [], "tmpfs": []}.items():
        for value in ([CANARY] if isinstance(default, list) else {"fixture": CANARY}, None, False, 0, ""):
            provider = Provider("administration")
            container = provider.task["containerDefinitions"][0]
            selected = container["linuxParameters"] if key in {"devices", "tmpfs"} else container
            selected[key] = value
            fails(lambda: M.inspect(provider, "administration", PARAMETERS, RESOURCES), "task-binding-container-not-confirmed", "administration")
    provider = Provider("administration")
    provider.task["containerDefinitions"][0]["unsupportedFixtureField"] = []
    fails(lambda: M.inspect(provider, "administration", PARAMETERS, RESOURCES), "task-binding-container-not-confirmed", "administration")
    
    for key, value, code in [("status", "INACTIVE", "task-binding-definition-not-confirmed"), ("revision", True, "task-binding-definition-not-confirmed"),
                             ("cpu", "1024", "task-binding-container-not-confirmed"), ("taskRoleArn", CANARY, "task-binding-definition-not-confirmed"),
                             ("enableFaultInjection", True, "task-binding-definition-not-confirmed")]:
        provider = Provider("administration"); provider.task[key] = value
        fails(lambda: M.inspect(provider, "administration", PARAMETERS, RESOURCES), code, "administration")
    for key, value in [("image", CANARY), ("command", [CANARY]), ("entryPoint", [CANARY]), ("privileged", True), ("cpu", False), ("environmentFiles", [{"value": CANARY}]), ("linuxParameters", CANARY), ("logConfiguration", None), ("portMappings", [CANARY])]:
        provider = Provider("migration"); provider.task["containerDefinitions"][0][key] = value
        fails(lambda: M.inspect(provider, "migration", PARAMETERS, RESOURCES), "task-binding-container-not-confirmed", "migration")
    provider = Provider("migration")
    environment = provider.task["containerDefinitions"][0]["environment"]
    environment.append(copy.deepcopy(environment[0]))
    fails(lambda: M.inspect(provider, "migration", PARAMETERS, RESOURCES), "task-binding-container-not-confirmed", "migration")
    for mutation, code in [("attached", "task-binding-attached-policy-prohibited"), ("paginated", "task-binding-policy-inventory-not-confirmed"),
                           ("trust", "task-binding-role-not-confirmed"), ("boundary", "task-binding-role-not-confirmed"), ("empty-boundary", "task-binding-role-not-confirmed"), ("policy", "task-binding-policy-not-confirmed")]:
        provider = Provider("database-proof")
        name = RESOURCES["DatabaseProofExecutionRole"]["physical_id"]
        if mutation in {"attached", "paginated"}: setattr(provider, mutation, True)
        if mutation == "trust": provider.roles[name]["AssumeRolePolicyDocument"]["Statement"][0]["Principal"] = {"AWS": "*"}
        if mutation == "boundary": provider.roles[name]["PermissionsBoundary"] = {"PermissionsBoundaryArn": CANARY}
        if mutation == "empty-boundary": provider.roles[name]["PermissionsBoundary"] = {}
        if mutation == "policy": next(iter(provider.policies[name].values()))["Statement"][0]["Action"] = "*"
        observed = fails(lambda: M.inspect(provider, "database-proof", PARAMETERS, RESOURCES), code, "database-proof")
        assert observed.item == "execution-role", "a generic roles location would lose which checked identity failed"
    for mutation in ("owner", "vpc", "egress", "ingress", "destination"):
        provider = Provider("migration"); group = provider.groups[RESOURCES["MigrationSecurityGroup"]["physical_id"]]
        if mutation == "owner": group["OwnerId"] = "000000000000"
        if mutation == "vpc": group["VpcId"] = CANARY
        if mutation == "egress": group["IpPermissionsEgress"].append({"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]})
        if mutation == "ingress": group["IpPermissions"] = [permission({"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0"})]
        if mutation == "destination": provider.groups[PARAMETERS["DatabaseSecurityGroupId"]]["IpPermissions"] = []
        observed = fails(lambda: M.inspect(provider, "migration", PARAMETERS, RESOURCES), "task-binding-destination-not-confirmed" if mutation == "destination" else "task-binding-network-not-confirmed", "migration")
        if mutation == "destination": assert observed.item == "database-ingress"
    provider = Provider("administration")
    fails(lambda: M.inspect(provider, [], PARAMETERS, RESOURCES), "task-binding-selection-invalid", "unselected")
    assert provider.calls == []
    fails(lambda: M.inspect(provider, "migration", {**PARAMETERS, "DatabaseEndpoint": []}, RESOURCES), "task-binding-parameters-not-confirmed", "migration")
    assert provider.calls == []
    fails(lambda: M.resolve({"Fn::Join": [",", []]}, PARAMETERS, RESOURCES, "migration"), "task-binding-source-not-supported", "migration")
    fails(lambda: M.policy('{"Version":"2012-10-17","Statement":[],"Statement":[]}', "migration"), "task-binding-policy-not-confirmed", "migration")
    print(json.dumps({"schema": "deploy/entity-smoke-task-binding-fixture/v1", "verdict": "passed", "provider_observation": False, "workloads": 5,
                      "checks": ["actual-source-template", "immutable-task-revision", "no-extra-command-or-credentials", "exact-role-trust-and-policies", "url-encoded-policy", "private-network-and-destination-ingress", "finite-context", "no-native-values"]}))


if __name__ == "__main__": main()
