#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.task-binding
#   version: 2
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-27"
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
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_TASK_BINDING_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).resolve().parents[2]
M = module("entity_smoke_task_binding_fixture", DIRECTORY / "task-execution/implementation/task-binding.py")
F = module("entity_smoke_task_binding_source_fixture", DIRECTORY / "controls-and-readiness/tests/deployment-control-test.py")
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
    def __init__(self, workload, *, parameters=None, resources=None, snapshot=None):
        parameters = PARAMETERS if parameters is None else parameters
        resources = RESOURCES if resources is None else resources
        snapshot = M.DEPLOY.source()[1] if snapshot is None else snapshot
        self.calls, self.workload = [], workload
        self.task = M.expected_task(workload, parameters, resources, snapshot)
        self.task.update(taskDefinitionArn=resources[M.WORKLOADS[workload] + "TaskDefinition"]["physical_id"], revision=1, status="ACTIVE", compatibilities=["EC2", "FARGATE"], registeredBy="arn:aws:iam::337159794548:role/fixture")
        self.task["volumes"] = []; self.task["placementConstraints"] = []; self.task["enableFaultInjection"] = False
        self.task["containerDefinitions"][0].update(cpu=0, mountPoints=[], volumesFrom=[])
        self.task["containerDefinitions"][0].update(copy.deepcopy(EMPTY_CONTAINER_DEFAULTS))
        self.task["containerDefinitions"][0]["linuxParameters"].update(devices=[], tmpfs=[])
        self.roles, self.policies, self.groups = {}, {}, {}
        self.attached, self.paginated, self.encoded = False, False, False
        for logical, resource in snapshot["Resources"].items():
            if resource["Type"] == "AWS::IAM::Role":
                properties = M.resolve(resource["Properties"], parameters, resources, workload)
                name = resources[logical]["physical_id"]
                self.roles[name] = {"RoleName": name, "Arn": "arn:aws:iam::337159794548:role/" + name, "Path": "/", "AssumeRolePolicyDocument": properties["AssumeRolePolicyDocument"]}
                self.policies[name] = {entry["PolicyName"]: entry["PolicyDocument"] for entry in properties["Policies"]}
            if resource["Type"] == "AWS::EC2::SecurityGroup":
                group = resources[logical]["physical_id"]
                properties = M.resolve(resource["Properties"], parameters, resources, workload)
                self.groups[group] = {"GroupId": group, "VpcId": parameters["VpcId"], "OwnerId": M.ACCOUNT, "IpPermissions": [], "IpPermissionsEgress": [permission(row) for row in properties["SecurityGroupEgress"]]}
        for group in (parameters["EndpointSecurityGroupId"], parameters["DatabaseSecurityGroupId"]):
            self.groups[group] = {"GroupId": group, "VpcId": parameters["VpcId"], "OwnerId": M.ACCOUNT, "IpPermissions": [], "IpPermissionsEgress": []}
        for logical, resource in snapshot["Resources"].items():
            if resource["Type"] == "AWS::EC2::SecurityGroupIngress":
                row = M.resolve(resource["Properties"], parameters, resources, workload)
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


def runtime_fixture(workload="verifier", *, package=None):
    """Controlled source/observation handoff shared by the actual consumer fixtures."""
    snapshot, parameters, resources = copy.deepcopy(M.DEPLOY.source()[1]), copy.deepcopy(PARAMETERS), copy.deepcopy(RESOURCES)
    parameters.update(ResourceNamePrefix="session-check", ClusterArn="arn:aws:ecs:eu-west-1:337159794548:cluster/session-check",
                      LogGroupName="/aws/ecs/session-check")
    if package is not None: parameters.update(ImageDigest=package["image_digest"], SourceRevision=package["source_revision"])
    # Extra captured declarations demonstrate exact source closure, not persistent constants.
    snapshot["Parameters"]["CapturedFixture"] = {"Type": "String"}
    parameters["CapturedFixture"] = "checked"
    snapshot["Resources"]["CapturedLog"] = {"Type": "AWS::Logs::LogGroup", "Properties": {"LogGroupName": "/fixture/captured"}}
    resources["CapturedLog"] = {"type": "AWS::Logs::LogGroup", "physical_id": "/fixture/captured"}
    for name, prefix in M.WORKLOADS.items():
        definition = snapshot["Resources"][prefix + "TaskDefinition"]["Properties"]
        definition["Family"] = "session-checked-" + name
        container = definition["ContainerDefinitions"][0]
        container["Name"] = "renamed-" + name
        container["LogConfiguration"]["Options"]["awslogs-stream-prefix"] = "checked-" + name
        resources[prefix + "TaskDefinition"]["physical_id"] = "arn:aws:ecs:eu-west-1:337159794548:task-definition/session-checked-" + name + ":1"
    view = {"schema": "deploy/aws-session-runtime-view/v1", "binding": {"target": "kanbien-core-platform", "scope": "entity-smoke",
                "session_id": "1" * 32, "source_inputs_sha256": "2" * 64, "starts_at": 1, "expires_at": 3601},
            "source_plan_sha256": "3" * 64, "account": M.ACCOUNT, "region": M.REGION, "component": "entity-smoke",
            "stack": "session-checked-entity", "stack_id": "arn:aws:cloudformation:eu-west-1:337159794548:stack/session-checked-entity/11111111-1111-1111-1111-111111111111",
            "phase": "activation", "template_reference": "30-provider-realization/aws/cloudformation/entity-smoke.yml",
            "template": snapshot, "parameters": parameters, "resources": resources, "outputs": {}, "observed_at": 100,
            "custody": {name: "4" * 64 for name in ("creation_request_sha256", "change_set_id_sha256", "template_sha256", "parameters_sha256", "resources_sha256")}}
    provider = Provider(workload, parameters=parameters, resources=resources, snapshot=snapshot)
    return view, provider


def bound_request(request):
    view, provider = runtime_fixture(request["workload"], package=request)
    checked = M.inspect(provider, request["workload"], view["parameters"], view["resources"], view["template"], runtime_view=view)
    return {**copy.deepcopy(request), **{key: copy.deepcopy(checked[key]) for key in ("definition", "security_group", "subnets", "runtime")}}


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
    assert M.SHARED.resolve({"Fn::If": ["selected", {"Ref": "kept"}, {"Ref": "AWS::NoValue"}]}, {"selected": True}) == {"Ref": "kept"}
    provider = Provider("migration")
    with patch.object(M.SHARED, "runtime_task_definition", wraps=M.SHARED.runtime_task_definition) as shared_task, \
            patch.object(M.SHARED, "runtime_role", wraps=M.SHARED.runtime_role) as shared_role, \
            patch.object(M.SHARED, "runtime_network", wraps=M.SHARED.runtime_network) as shared_network:
        M.inspect(provider, "migration", PARAMETERS, RESOURCES)
        assert shared_task.call_count == 1 and shared_role.call_count == 2 and shared_network.call_count == 1
    observed = []
    value = {"revision": 1, "nested": {"value": 1}}
    def raw(service, operation, **parameters):
        observed.append((service, operation, parameters))
        return value
    scope = M.observation_scope(raw)
    first = scope("iam", "get-role", RoleName="owned")
    first["nested"]["value"] = 99
    value["revision"] = 2
    assert scope("iam", "get-role", RoleName="owned") == {"revision": 1, "nested": {"value": 1}}
    assert len(observed) == 1
    assert M.observation_scope(raw)("iam", "get-role", RoleName="owned")["revision"] == 2
    assert len(observed) == 2, "a subsequent guard must not reuse a preparation observation"
    scope("iam", "get-role", RoleName="other")
    assert len(observed) == 3
    for service, operation in (("ecs", "describe-tasks"), ("ecs", "describe-services"), ("logs", "get-log-events"),
                               ("iam", "simulate-principal-policy"), ("ecs", "run-task")):
        before = len(observed)
        scope(service, operation); scope(service, operation)
        assert len(observed) == before + 2, "runtime observations and mutations are never cached"
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
    for workload in M.WORKLOADS:
        view, provider = runtime_fixture(workload)
        result = M.inspect(provider, workload, view["parameters"], view["resources"], view["template"], runtime_view=view)
        assert result["runtime"]["family"] == "session-checked-" + workload
        assert result["runtime"]["container_name"] == "renamed-" + workload
        assert result["runtime"]["log_group"] == "/aws/ecs/session-check"
        assert result["runtime"]["log_stream_prefix"] == "checked-" + workload
        assert result["runtime"]["binding_sha256"] == M.DEPLOY.fingerprint({key: view[key] for key in ("binding", "custody", "stack_id")})
        view["observed_at"] += 1
        repeated = M.inspect(provider, workload, view["parameters"], view["resources"], view["template"], runtime_view=view)
        assert result == repeated, "observation time is not immutable task identity"
        result["runtime"]["session_id"] = "0" * 32
        assert view["binding"]["session_id"] == "1" * 32
    for field, value in (("account", "000000000000"), ("region", "us-east-1"), ("component", "foundation"),
                         ("observed_at", True), ("observed_at", -1), ("observed_at", "100"), ("custody", {"raw": CANARY}),
                         ("stack_id", CANARY), ("outputs", {"Uncaptured": CANARY}), ("phase", "unknown"), ("unknown", CANARY)):
        view, provider = runtime_fixture()
        view[field] = value
        fails(lambda: M.inspect(provider, "verifier", view["parameters"], view["resources"], view["template"], runtime_view=view), "runtime-binding-invalid", "verifier")
        assert provider.calls == [], "malformed source handoff cannot trigger provider reads"
    for field in ("parameters", "resources", "template"):
        view, provider = runtime_fixture()
        supplied = {name: copy.deepcopy(view[name]) for name in ("parameters", "resources", "template")}
        supplied[field]["uncaptured"] = CANARY
        fails(lambda: M.inspect(provider, "verifier", supplied["parameters"], supplied["resources"], supplied["template"], runtime_view=view), "runtime-binding-invalid", "verifier")
        assert provider.calls == []
    for field, key, reason in (("parameters", "CapturedFixture", "task-binding-parameters-not-confirmed"),
                              ("resources", "CapturedLog", "task-binding-resources-not-confirmed")):
        view, provider = runtime_fixture()
        del view[field][key]
        fails(lambda: M.inspect(provider, "verifier", view["parameters"], view["resources"], view["template"], runtime_view=view), reason, "verifier")
        assert provider.calls == [], "equal but incomplete maps cannot hide missing captured declarations"
    print(json.dumps({"schema": "deploy/entity-smoke-task-binding-fixture/v1", "verdict": "passed", "provider_observation": False, "workloads": 5,
                      "checks": ["actual-source-template", "immutable-task-revision", "no-extra-command-or-credentials", "exact-role-trust-and-policies", "url-encoded-policy", "private-network-and-destination-ingress", "finite-context", "no-native-values"]}))


if __name__ == "__main__": main()
