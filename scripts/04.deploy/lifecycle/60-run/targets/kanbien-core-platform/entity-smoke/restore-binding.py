#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.restore-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Compare the isolated clone and reader with their own checked source and incarnation without admitting source database access or caller overrides.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md


def expanded(template, database):
    def expand(value):
        if isinstance(value, list): return [expand(item) for item in value]
        if not isinstance(value, dict): return value
        if set(value) == {"Fn::GetAtt"}:
            if value["Fn::GetAtt"] == ["RestoredDatabase", "Endpoint.Address"]: return database["Endpoint"]["Address"]
            if value["Fn::GetAtt"] == ["RestoredDatabase", "DbiResourceId"]: return database["DbiResourceId"]
        if set(value) == {"Fn::Sub"} and isinstance(value["Fn::Sub"], str):
            return {"Fn::Sub": value["Fn::Sub"].replace("${RestoredDatabase.DbiResourceId}", database["DbiResourceId"])}
        return {key: expand(item) for key, item in value.items()}
    return expand(template)


def inspect(C, comparator, restore, provider, binding, parameters, deployment, subnets):
    restore.parameters_for(binding, parameters)
    resources = deployment["resources"]
    workload = "restore-reader"
    require = lambda value, code, field, item=None: comparator.require(value, code, workload, field, item)
    database = C.RESOURCE.only(provider("rds", "describe-db-instances", DBInstanceIdentifier=deployment["database_identifier"]), "DBInstances")
    require(database.get("DBInstanceIdentifier") == deployment["database_identifier"] == restore.names(binding)[2]
            and database.get("DbiResourceId") == deployment["restored_resource_id"] and database.get("DBName") == parameters["RestoredDatabaseName"]
            and database.get("DBInstanceStatus") == "available" and database.get("StorageEncrypted") is True and database.get("PubliclyAccessible") is False
            and database.get("IAMDatabaseAuthenticationEnabled") is True and database.get("DeletionProtection") is False, "task-binding-definition-not-confirmed", "identity")
    endpoint, subnet = database.get("Endpoint"), database.get("DBSubnetGroup")
    require(isinstance(endpoint, dict) and isinstance(endpoint.get("Address"), str) and endpoint["Address"] and not any(ch in endpoint["Address"] for ch in "\r\n\0")
            and type(endpoint.get("Port")) is int and endpoint["Port"] == 5432, "task-binding-container-not-confirmed", "container")
    require(isinstance(subnet, dict) and subnet.get("DBSubnetGroupName") == parameters["DatabaseSubnetGroupName"] and subnet.get("VpcId") == parameters["VpcId"]
            and subnet.get("SubnetGroupStatus") == "Complete", "task-binding-network-not-confirmed", "network", "database-ingress")
    groups = database.get("VpcSecurityGroups")
    own_group = resources["RestoreDatabaseSecurityGroup"]["physical_id"]
    require(isinstance(groups, list) and len(groups) == 1 and isinstance(groups[0], dict) and groups[0].get("Status") == "active"
            and groups[0].get("VpcSecurityGroupId") == own_group, "task-binding-network-not-confirmed", "network", "database-ingress")
    incarnation = C.DEPLOY.fingerprint({"resource_id": database["DbiResourceId"], "database": parameters["RestoredDatabaseName"], "schema": "entity_smoke"})
    require(incarnation != binding["dependency_incarnation_sha256"], "task-binding-definition-not-confirmed", "identity")
    view = expanded(restore.source()[1], database)
    inputs = {**parameters, "PrivateSubnetIds": ",".join(subnets), "DatabaseSecurityGroupId": own_group}
    definition, configuration = comparator.task_definition(provider, workload, inputs, resources, view, prefix="RestoreReader")
    roles = {name: comparator.role(provider, name, inputs, resources, workload, view) for name in ("RestoreReaderExecutionRole", "RestoreReaderTaskRole")}
    group, network_hash = comparator.network(provider, workload, inputs, resources, view, prefix="RestoreReader")
    actual = C.RESOURCE.only(provider("ec2", "describe-security-groups", GroupIds=[own_group]), "SecurityGroups")
    require(actual.get("GroupId") == own_group and actual.get("VpcId") == parameters["VpcId"] and actual.get("OwnerId") == C.ALIGN.ACCOUNT, "task-binding-network-not-confirmed", "network", "database-ingress")
    ingress = comparator.permissions(actual.get("IpPermissions"), workload)
    egress = comparator.permissions(actual.get("IpPermissionsEgress"), workload)
    expected = comparator.resolve(view["Resources"]["RestoreDatabaseSecurityGroup"]["Properties"], inputs, resources, workload)["SecurityGroupEgress"]
    require(ingress == [("tcp", 5432, 5432, "GroupId", group)] and egress == sorted((str(row["IpProtocol"]), row["FromPort"], row["ToPort"], "CidrIp", row["CidrIp"]) for row in expected), "task-binding-network-not-confirmed", "network", "database-ingress")
    return {"checked": {"definition": definition, "security_group": group, "subnets": list(subnets), "configuration_sha256": C.DEPLOY.fingerprint(configuration),
                        "roles_sha256": C.DEPLOY.fingerprint(roles), "network_sha256": C.DEPLOY.fingerprint({"reader": network_hash, "database": {"ingress": ingress, "egress": egress}})},
            "binding": {**{key: value for key, value in binding.items() if key != "record_digest"}, "dependency_incarnation_sha256": incarnation, "permission_contract_sha256": C.digest_file(restore.SOURCE)},
            "database": database, "view": view, "inputs": inputs}
