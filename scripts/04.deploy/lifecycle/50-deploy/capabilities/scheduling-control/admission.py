# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.helper.scheduling-admission
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.scheduling
#   disciplines: [security, sre]
#   kind: script
#   purpose: Derive scoped scheduling safety facts from current provider observations without authorizing or performing mutations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, network]
#   used_by:
#   - id: deploy.capability.scheduling-control
#     path: scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/script.py
"""Read-only fact composition. No receipt JSON, executable root, or provider CLI."""
from datetime import datetime, timezone
import base64
import binascii
import fnmatch
import hashlib
import ipaddress
import json
import re
import uuid


class AdmissionFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise AdmissionFailure(code)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def collection(provider, service, operation, field, **arguments):
    """Bound each collection; service pagination is not interchangeable."""
    request_key, response_key = {
        "ecs": ("nextToken", "nextToken"), "lambda": ("Marker", "NextMarker"),
        "iam": ("Marker", "Marker"), "logs": ("nextToken", "nextToken"),
    }.get(service, ("NextToken", "NextToken"))
    result, token, seen = [], None, set()
    for _ in range(20):
        value = provider(service, operation, **arguments, **({request_key: token} if token else {}))
        rows = value.get(field)
        require(isinstance(rows, list), "admission-collection-invalid")
        result.extend(rows)
        require(len(result) <= 2000, "admission-collection-limit")
        token = value.get(response_key)
        if service == "iam" and not value.get("IsTruncated", False):
            token = None
        if token is None:
            require(not value.get("IsTruncated", False), "admission-collection-incomplete")
            return result
        require(isinstance(token, str) and token and token not in seen, "admission-pagination-invalid")
        seen.add(token)
    raise AdmissionFailure("admission-collection-limit")


def strings(value):
    values = [value] if isinstance(value, str) else value
    require(isinstance(values, list) and values and all(isinstance(item, str) and item for item in values), "admission-policy-invalid")
    return values


def reject_network_conditions(document, code):
    """Private DNS changes request context, including explicit-deny policies."""
    require(isinstance(document, dict), "admission-policy-invalid")
    statements = document.get("Statement", [])
    statements = [statements] if isinstance(statements, dict) else statements
    require(isinstance(statements, list), "admission-policy-invalid")
    sensitive = {"aws:sourceip", "aws:sourcevpc", "aws:sourcevpce", "aws:vpcsourceip",
        "aws:vpceaccount", "aws:vpceorgid", "aws:vpceorgpaths"}
    for statement in statements:
        require(isinstance(statement, dict), "admission-policy-invalid")
        conditions = statement.get("Condition", {})
        require(isinstance(conditions, dict), "admission-policy-invalid")
        for values in conditions.values():
            require(isinstance(values, dict), "admission-policy-invalid")
            require(not any(isinstance(key, str) and key.lower() in sensitive for key in values), code)


def role(provider, arn, account):
    require(isinstance(arn, str) and re.fullmatch(r"arn:aws:iam::" + account + r":role/[A-Za-z0-9+=,.@_/-]+", arn), "admission-role-invalid")
    name = arn.rsplit("/", 1)[1]
    actual = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(actual, dict) and actual.get("Arn") == arn and actual.get("RoleName") == name
            and isinstance(actual.get("RoleId"), str), "admission-role-identity-mismatch")
    documents = {}
    names = collection(provider, "iam", "list-role-policies", "PolicyNames", RoleName=name)
    require(len(names) == len(set(names)) and all(isinstance(item, str) for item in names), "admission-role-policies-invalid")
    for policy_name in sorted(names):
        value = provider("iam", "get-role-policy", RoleName=name, PolicyName=policy_name)
        require(value.get("RoleName") == name and value.get("PolicyName") == policy_name, "admission-role-policy-mismatch")
        documents["inline:" + policy_name] = value.get("PolicyDocument")
    attached = collection(provider, "iam", "list-attached-role-policies", "AttachedPolicies", RoleName=name)
    for item in attached:
        policy_arn = item.get("PolicyArn") if isinstance(item, dict) else None
        require(isinstance(policy_arn, str) and policy_arn not in documents, "admission-attached-policy-invalid")
        policy = provider("iam", "get-policy", PolicyArn=policy_arn).get("Policy", {})
        require(policy.get("Arn") == policy_arn and isinstance(policy.get("DefaultVersionId"), str), "admission-policy-version-invalid")
        version = provider("iam", "get-policy-version", PolicyArn=policy_arn, VersionId=policy["DefaultVersionId"]).get("PolicyVersion", {})
        require(version.get("VersionId") == policy["DefaultVersionId"] and version.get("IsDefaultVersion") is True, "admission-policy-version-mismatch")
        documents[policy_arn] = version.get("Document")
    boundary_documents = {}
    boundary = actual.get("PermissionsBoundary")
    if boundary is not None:
        require(isinstance(boundary, dict) and boundary.get("PermissionsBoundaryType") == "Policy"
            and isinstance(boundary.get("PermissionsBoundaryArn"), str), "admission-boundary-invalid")
        boundary_arn = boundary["PermissionsBoundaryArn"]
        policy = provider("iam", "get-policy", PolicyArn=boundary_arn).get("Policy", {})
        require(policy.get("Arn") == boundary_arn and isinstance(policy.get("DefaultVersionId"), str), "admission-policy-version-invalid")
        version = provider("iam", "get-policy-version", PolicyArn=boundary_arn, VersionId=policy["DefaultVersionId"]).get("PolicyVersion", {})
        require(version.get("VersionId") == policy["DefaultVersionId"] and version.get("IsDefaultVersion") is True, "admission-policy-version-mismatch")
        boundary_documents[boundary_arn] = version.get("Document")
    for document in [*documents.values(), *boundary_documents.values(), actual.get("AssumeRolePolicyDocument", {"Statement": []})]:
        reject_network_conditions(document, "admission-role-network-condition")
    grants = set()
    for document in documents.values():
        require(isinstance(document, dict), "admission-policy-invalid")
        statements = document.get("Statement")
        statements = [statements] if isinstance(statements, dict) else statements
        require(isinstance(statements, list), "admission-policy-invalid")
        for statement in statements:
            require(isinstance(statement, dict) and statement.get("Effect") in {"Allow", "Deny"}, "admission-policy-invalid")
            if statement["Effect"] != "Allow":
                continue
            require("NotAction" not in statement and "NotResource" not in statement, "admission-indeterminate-permission")
            actions = strings(statement.get("Action"))
            # Another assumable identity defeats a proof based on this role alone.
            require(not any(fnmatch.fnmatchcase("sts:assumerole", action.lower()) for action in actions), "admission-indirect-identity")
            for action in actions:
                if action.lower().startswith("sqs:") or fnmatch.fnmatchcase("sqs:sendmessage", action.lower()):
                    require(not any(char in action for char in "*?"), "admission-unbounded-queue-permission")
                    for resource in strings(statement.get("Resource")):
                        require(not any(char in resource for char in "*?"), "admission-unbounded-queue-permission")
                        grants.add((action.lower(), resource))
    identity = {key: actual[key] for key in ("Arn", "RoleId", "RoleName", "Path", "AssumeRolePolicyDocument", "PermissionsBoundary", "MaxSessionDuration") if key in actual}
    return {"identity": identity, "documents": documents, "boundaries": boundary_documents}, grants


def queue(provider, arn, account, region):
    prefix = f"arn:aws:sqs:{region}:{account}:"
    require(isinstance(arn, str) and arn.startswith(prefix) and re.fullmatch(r"[A-Za-z0-9_-]+(?:\.fifo)?", arn[len(prefix):]), "admission-queue-identity-invalid")
    url = provider("sqs", "get-queue-url", QueueName=arn[len(prefix):], QueueOwnerAWSAccountId=account).get("QueueUrl")
    require(url == f"https://sqs.{region}.amazonaws.com/{account}/{arn[len(prefix):]}", "admission-queue-url-mismatch")
    attributes = provider("sqs", "get-queue-attributes", QueueUrl=url, AttributeNames=["All"]).get("Attributes")
    require(isinstance(attributes, dict) and attributes.get("QueueArn") == arn, "admission-queue-identity-mismatch")
    stable = {key: value for key, value in attributes.items() if key not in {
        "ApproximateNumberOfMessages", "ApproximateNumberOfMessagesDelayed", "ApproximateNumberOfMessagesNotVisible", "LastModifiedTimestamp"}}
    for key in ("Policy", "RedrivePolicy", "RedriveAllowPolicy"):
        if key in stable:
            try:
                stable[key] = json.loads(stable[key])
            except (TypeError, ValueError, RecursionError):
                raise AdmissionFailure("admission-queue-policy-invalid") from None
    # Network-context policies require a separate preservation argument: the
    # endpoint changes source IP/VPC context even when identities stay unchanged.
    reject_network_conditions(stable.get("Policy", {}), "admission-queue-network-condition")
    return stable


def regional_queue_policies(provider, account, region, queues, roles, known_grants, *, created=None):
    """An absent identity Allow does not exclude a queue resource-policy grant.

    Inspect every same-account regional queue, including queues not named by
    this deployment. Conditions are not interpreted as proof that a possible
    grant is harmless. This deliberately rejects unreviewed access rather than
    extending the new endpoint's permissions to accommodate it.
    """
    urls = collection(provider, "sqs", "list-queues", "QueueUrls", MaxResults=1000)
    require(len(urls) == len(set(urls)), "admission-queue-inventory-invalid")
    prefix = f"https://sqs.{region}.amazonaws.com/{account}/"
    policies = {}
    for url in sorted(urls):
        require(isinstance(url, str) and url.startswith(prefix)
            and re.fullmatch(r"[A-Za-z0-9_-]+(?:\.fifo)?", url[len(prefix):]), "admission-queue-url-mismatch")
        arn = f"arn:aws:sqs:{region}:{account}:" + url[len(prefix):]
        attributes = queues.get(arn)
        if attributes is None:
            attributes = queue(provider, arn, account, region)
        document = attributes.get("Policy", {"Statement": []})
        statements = document.get("Statement", [])
        statements = [statements] if isinstance(statements, dict) else statements
        require(isinstance(statements, list), "admission-queue-policy-invalid")
        for statement in statements:
            require(isinstance(statement, dict) and statement.get("Effect") in {"Allow", "Deny"}, "admission-queue-policy-invalid")
            if statement["Effect"] != "Allow":
                continue
            require(not {"NotAction", "NotResource", "NotPrincipal"} & set(statement), "admission-indeterminate-queue-policy")
            actions, resources = strings(statement.get("Action")), strings(statement.get("Resource"))
            actions = [action.lower() for action in actions if action.lower().startswith("sqs:")
                or any(char in action.split(":", 1)[0] for char in "*?")]
            if not actions or not any(fnmatch.fnmatchcase(arn, resource) for resource in resources):
                continue
            principal = statement.get("Principal")
            require(isinstance(principal, (str, dict)), "admission-queue-policy-invalid")
            if isinstance(principal, dict):
                require(bool(principal) and set(principal) <= {"AWS", "Service"}, "admission-indeterminate-queue-principal")
                principals = strings(principal["AWS"]) if "AWS" in principal else []
            else:
                principals = strings(principal)
            require(all(item == "*" or not any(char in item for char in "*?") for item in principals), "admission-indeterminate-queue-principal")
            for role_arn, (state, _identity_grants) in roles.items():
                identity = state["identity"]
                session_prefix = f"arn:aws:sts::{account}:assumed-role/{identity['RoleName']}/"
                possible = any(item in {"*", account, f"arn:aws:iam::{account}:root", role_arn, identity["RoleId"]}
                    or item.startswith(session_prefix) or item.startswith(identity["RoleId"] + ":")
                    for item in principals)
                if possible:
                    require(role_arn in known_grants and all((action, arn) in known_grants[role_arn]
                        for action in actions), "admission-resource-only-queue-consumer")
        policies[arn] = document
    require(set(queues) <= set(policies), "admission-queue-inventory-incomplete")
    owned = set() if created is None else set(created["queues"])
    require(owned <= set(policies), "admission-created-queue-inventory-incomplete")
    return {arn: document for arn, document in policies.items() if arn not in owned}


def private_subnet_paths(provider, vpc, parameters, interfaces, routes):
    """Admit only directly local IPv4 routes and the bounded allow-all ACL shape.

    This is a compatibility check, not a general firewall evaluator. Any custom
    IPv4 ACL or overlapping nonlocal route needs a separately reviewed argument.
    """
    subnet_ids = set(parameters["PrivateSubnetIds"].split(",")) | {row.get("SubnetId") for row in interfaces}
    require(all(isinstance(item, str) and item.startswith("subnet-") for item in subnet_ids), "admission-subnet-inventory-invalid")
    subnets = provider("ec2", "describe-subnets", SubnetIds=sorted(subnet_ids)).get("Subnets")
    require(isinstance(subnets, list) and len(subnets) == len(subnet_ids)
        and {row.get("SubnetId") for row in subnets} == subnet_ids
        and all(row.get("VpcId") == vpc for row in subnets), "admission-subnet-inventory-incomplete")
    try:
        networks = {row["SubnetId"]: ipaddress.IPv4Network(row["CidrBlock"]) for row in subnets}
    except (KeyError, TypeError, ValueError):
        raise AdmissionFailure("admission-subnet-cidr-invalid") from None
    acls = collection(provider, "ec2", "describe-network-acls", "NetworkAcls", Filters=[{"Name": "vpc-id", "Values": [vpc]}])
    selected, prefix_lists = {}, {}
    for subnet in sorted(subnet_ids):
        matches = [acl for acl in acls if any(item.get("SubnetId") == subnet for item in acl.get("Associations", []))]
        require(len(matches) == 1 and matches[0].get("VpcId") == vpc, "admission-subnet-acl-incomplete")
        acl = matches[0]
        require(isinstance(acl.get("NetworkAclId"), str) and isinstance(acl.get("Entries"), list), "admission-subnet-acl-invalid")
        for egress in (False, True):
            ipv4 = [entry for entry in acl["Entries"] if "CidrBlock" in entry and entry.get("Egress") is egress]
            require(len(ipv4) == 2 and all(set(entry) == {"RuleNumber", "Protocol", "RuleAction", "Egress", "CidrBlock"} for entry in ipv4)
                and {fingerprint(entry) for entry in ipv4} == {fingerprint({"RuleNumber": number, "Protocol": "-1", "RuleAction": action,
                    "Egress": egress, "CidrBlock": "0.0.0.0/0"}) for number, action in ((100, "allow"), (32767, "deny"))}, "admission-subnet-acl-unreviewed")
        selected[acl["NetworkAclId"]] = acl
        explicit = [table for table in routes if any(item.get("SubnetId") == subnet for item in table.get("Associations", []))]
        candidates = explicit or [table for table in routes if any(item.get("Main") is True for item in table.get("Associations", []))]
        require(len(candidates) == 1 and candidates[0].get("VpcId") == vpc, "admission-subnet-route-incomplete")
        local = []
        for route in candidates[0].get("Routes", []):
            if "DestinationPrefixListId" in route:
                identifier = route["DestinationPrefixListId"]
                require(isinstance(identifier, str) and re.fullmatch(r"pl-[a-f0-9]+", identifier)
                    and route.get("State") == "active" and isinstance(route.get("GatewayId"), str)
                    and route["GatewayId"].startswith("vpce-"), "admission-private-route-unreviewed")
                if identifier not in prefix_lists:
                    descriptions = provider("ec2", "describe-managed-prefix-lists", PrefixListIds=[identifier]).get("PrefixLists")
                    require(isinstance(descriptions, list) and len(descriptions) == 1
                        and descriptions[0].get("PrefixListId") == identifier and descriptions[0].get("OwnerId") == "AWS"
                        and descriptions[0].get("AddressFamily") == "IPv4" and descriptions[0].get("State") in {"create-complete", "modify-complete"},
                        "admission-private-prefix-unreviewed")
                    entries = collection(provider, "ec2", "get-managed-prefix-list-entries", "Entries", PrefixListId=identifier, MaxResults=100)
                    require(entries and len({entry.get("Cidr") for entry in entries}) == len(entries), "admission-private-prefix-incomplete")
                    try:
                        destinations = [ipaddress.IPv4Network(entry["Cidr"]) for entry in entries]
                    except (KeyError, TypeError, ValueError):
                        raise AdmissionFailure("admission-private-prefix-unreviewed") from None
                    require(not any(destination.overlaps(network) for destination in destinations for network in networks.values()),
                        "admission-private-route-unreviewed")
                    prefix_lists[identifier] = {"description": descriptions[0], "entries": sorted(entries, key=lambda entry: entry["Cidr"])}
                continue
            if "DestinationCidrBlock" not in route:
                continue
            try:
                destination = ipaddress.IPv4Network(route["DestinationCidrBlock"])
            except (TypeError, ValueError):
                raise AdmissionFailure("admission-private-route-unreviewed") from None
            if route.get("GatewayId") == "local" and route.get("State") == "active":
                local.append(destination)
            elif destination.prefixlen:
                require(not any(destination.overlaps(network) for network in networks.values()), "admission-private-route-unreviewed")
        require(all(any(network.subnet_of(destination) for destination in local) for network in networks.values()), "admission-private-local-route-missing")
    # Endpoint/Lambda interfaces consume addresses without changing routing.
    stable_subnets = [{key: value for key, value in row.items() if key != "AvailableIpAddressCount"} for row in subnets]
    return {"subnets": sorted(stable_subnets, key=lambda row: row["SubnetId"]),
        "network_acls": [selected[key] for key in sorted(selected)],
        "route_prefix_lists": [prefix_lists[key] for key in sorted(prefix_lists)]}


def credential_overrides(definition):
    forbidden = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE",
                 "AWS_CONTAINER_CREDENTIALS_FULL_URI", "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "AWS_WEB_IDENTITY_TOKEN_FILE", "AWS_ROLE_ARN", "AWS_ENDPOINT_URL", "AWS_ENDPOINT_URL_SQS"}
    for container in definition.get("containerDefinitions", []):
        names = {row.get("name") for key in ("environment", "secrets") for row in container.get(key, [])}
        require(not names & forbidden and not container.get("environmentFiles"), "admission-unresolved-credentials")


def compute_consumers(provider, binding, vpc, interfaces, known_grants, known_groups, roles, *, created=None):
    account = binding["provider"]["account_id"]
    ecs_interfaces = {row["NetworkInterfaceId"]: row for row in interfaces if isinstance(row.get("Description"), str) and row["Description"].startswith(f"arn:aws:ecs:{binding['provider']['region']}:{account}:attachment/")}
    mapped, consumers = set(), []
    for cluster in collection(provider, "ecs", "list-clusters", "clusterArns"):
        tasks = collection(provider, "ecs", "list-tasks", "taskArns", cluster=cluster)
        require(len(tasks) == len(set(tasks)), "admission-task-inventory-invalid")
        for offset in range(0, len(tasks), 100):
            value = provider("ecs", "describe-tasks", cluster=cluster, tasks=tasks[offset:offset + 100])
            actual = value.get("tasks")
            require(not value.get("failures") and isinstance(actual, list) and {row.get("taskArn") for row in actual} == set(tasks[offset:offset + 100]), "admission-task-observation-incomplete")
            for task in actual:
                ids = {item.get("value") for attachment in task.get("attachments", []) for item in attachment.get("details", []) if item.get("name") == "networkInterfaceId"}
                selected = ids & set(ecs_interfaces)
                if not selected:
                    continue
                require(len(selected) == 1 and not selected & mapped, "admission-task-network-ambiguous")
                definition = provider("ecs", "describe-task-definition", taskDefinition=task["taskDefinitionArn"]).get("taskDefinition")
                require(isinstance(definition, dict) and definition.get("taskDefinitionArn") == task["taskDefinitionArn"]
                        and definition.get("networkMode") == "awsvpc", "admission-task-definition-mismatch")
                credential_overrides(definition)
                # Overrides can change identity or introduce alternate credentials.
                overrides = task.get("overrides", {})
                require(not overrides.get("taskRoleArn") or overrides["taskRoleArn"] == definition.get("taskRoleArn"), "admission-task-role-override")
                credential_overrides({"containerDefinitions": overrides.get("containerOverrides", [])})
                arn = definition.get("taskRoleArn")
                grants = set()
                if arn:
                    if arn not in roles:
                        roles[arn] = role(provider, arn, account)
                    grants = roles[arn][1]
                if grants:
                    require(arn in known_grants and grants == known_grants[arn], "admission-unknown-queue-consumer")
                    groups = {row.get("GroupId") for row in ecs_interfaces[next(iter(selected))].get("Groups", [])}
                    require(bool(groups & known_groups[arn]), "admission-consumer-network-uncovered")
                mapped |= selected
                consumers.append({"kind": "container", "identity_sha256": fingerprint({"task": task["taskArn"], "definition": definition, "overrides": overrides}),
                    "role": arn, "queue_capable": bool(grants), "interface": next(iter(selected))})
    require(mapped == set(ecs_interfaces), "admission-unmapped-compute-interface")
    # Only functions resolved from this controller's original completed stack
    # operations may be excluded from the pre-existing consumer comparison.
    functions = collection(provider, "lambda", "list-functions", "Functions")
    selected = [row for row in functions if row.get("VpcConfig", {}).get("VpcId") == vpc]
    owned = {} if created is None else created["functions"]
    require(len(selected) == len(owned) and {row.get("FunctionArn") for row in selected} == set(owned), "admission-function-consumer-unreviewed")
    for function in selected:
        expected = owned[function["FunctionArn"]]
        require(function.get("Role") == expected["role"]
            and set(function["VpcConfig"].get("SecurityGroupIds", [])) == {expected["group"]}
            and set(function["VpcConfig"].get("SubnetIds", [])) == set(expected["subnets"]), "admission-created-function-mismatch")
    return mapped, sorted(consumers, key=lambda row: row["interface"])


def network_facts(provider, binding, parameters, *, created=None):
    """Inspect the whole VPC before initial private-DNS endpoint creation.

    Returned fingerprints are observations, not an approval. Their retained
    original intent must later be compared with fresh observations.
    """
    account, region, vpc = binding["provider"]["account_id"], binding["provider"]["region"], parameters["VpcId"]
    endpoints = collection(provider, "ec2", "describe-vpc-endpoints", "VpcEndpoints", Filters=[{"Name": "vpc-id", "Values": [vpc]}])
    queue_endpoints = [row for row in endpoints if row.get("ServiceName") == f"com.amazonaws.{region}.sqs"]
    if created is None:
        require(not queue_endpoints, "admission-existing-queue-endpoint")
    else:
        require(len(queue_endpoints) == 1 and queue_endpoints[0] == created["endpoint"], "admission-created-endpoint-mismatch")
    interfaces = collection(provider, "ec2", "describe-network-interfaces", "NetworkInterfaces", Filters=[{"Name": "vpc-id", "Values": [vpc]}])
    require(all(isinstance(row, dict) and row.get("VpcId") == vpc and isinstance(row.get("NetworkInterfaceId"), str) for row in interfaces)
            and len({row["NetworkInterfaceId"] for row in interfaces}) == len(interfaces), "admission-interface-inventory-invalid")
    # A shared resolver/peering/VPN route extends the blast radius beyond this
    # inventory; do not silently claim these external consumers are covered.
    routes = collection(provider, "ec2", "describe-route-tables", "RouteTables", Filters=[{"Name": "vpc-id", "Values": [vpc]}])
    require(not any(any(key in route for key in ("VpcPeeringConnectionId", "TransitGatewayId", "NetworkInterfaceId"))
        or str(route.get("GatewayId", "")).startswith("vgw-") for table in routes for route in table.get("Routes", [])), "admission-external-network-consumer")
    consume = {"sqs:receivemessage", "sqs:deletemessage", "sqs:getqueueattributes", "sqs:changemessagevisibility"}
    known_grants, known_groups, roles, queues = {}, {}, {}, {}
    for queue_key, worker_key, relay_key in (
        ("LegacyWorkerQueueArn", "LegacyWorkerRoleArn", "LegacyRelayRoleArn"),
        ("LegacyRelationalQueueArn", "LegacyRelationalWorkerRoleArn", "LegacyRelationalRelayRoleArn"),
    ):
        queue_arn = parameters[queue_key]
        queues[queue_arn] = queue(provider, queue_arn, account, region)
        for role_key, actions in ((worker_key, consume), (relay_key, {"sqs:sendmessage"})):
            arn = parameters[role_key]
            known_grants[arn] = {(action, queue_arn) for action in actions}
            # Relational relay and worker both use the existing worker network.
            group_key = "LegacyRelaySecurityGroupId" if role_key == "LegacyRelayRoleArn" else "LegacyWorkerSecurityGroupId"
            known_groups[arn] = {parameters[group_key]}
            roles[arn] = role(provider, arn, account)
            require(roles[arn][1] == known_grants[arn], "admission-legacy-queue-permission-mismatch")
    mapped, consumers = compute_consumers(provider, binding, vpc, interfaces, known_grants, known_groups, roles, created=created)
    endpoint_interfaces = {item for endpoint in endpoints for item in endpoint.get("NetworkInterfaceIds", [])}
    for row in interfaces:
        if row["NetworkInterfaceId"] in mapped:
            continue
        if created is not None and row.get("InterfaceType") == "lambda" and row.get("RequesterManaged") is True:
            groups = {item.get("GroupId") for item in row.get("Groups", [])}
            require(any(groups == {item["group"]} and row.get("SubnetId") in item["subnets"] for item in created["functions"].values()), "admission-created-function-interface-uncovered")
            continue
        service_owned = row.get("RequesterManaged") is True and (
            row.get("InterfaceType") == "vpc_endpoint" and row["NetworkInterfaceId"] in endpoint_interfaces
            or row.get("RequesterId") == "amazon-rds" and row.get("Description") == "RDSNetworkInterface"
            or row.get("RequesterId") == "amazon-elasticache" and str(row.get("Description", "")).startswith("ElastiCache ")
            or row.get("RequesterId") == "amazon-elb" and str(row.get("Description", "")).startswith("ELB "))
        require(service_owned, "admission-unmapped-compute-interface")
    policies = regional_queue_policies(provider, account, region, queues, roles, known_grants, created=created)
    subnet_paths = private_subnet_paths(provider, vpc, parameters, interfaces, routes)
    group_ids = ({parameters["LegacyWorkerSecurityGroupId"], parameters["LegacyRelaySecurityGroupId"]}
        | {item["GroupId"] for row in interfaces for item in row.get("Groups", [])})
    if created is not None:
        group_ids -= {created["endpoint_group"], *[row["group"] for row in created["functions"].values()]}
    group_ids = sorted(group_ids)
    groups = provider("ec2", "describe-security-groups", GroupIds=group_ids).get("SecurityGroups")
    require(isinstance(groups, list) and {row.get("GroupId") for row in groups} == set(group_ids)
            and all(row.get("VpcId") == vpc for row in groups), "admission-security-groups-incomplete")
    if created is not None:
        # Strip only the exact source-owned new DB ingress, then compare every
        # remaining legacy field. Never ignore the whole shared security group.
        groups = json.loads(json.dumps(groups))
        for ingress in created["database_ingress"]:
            matches = [row for row in groups if row["GroupId"] == ingress["target"]]
            require(len(matches) == 1, "admission-created-database-group-uncovered")
            removed = 0
            for rule in matches[0].get("IpPermissions", []):
                if rule.get("IpProtocol") == "tcp" and rule.get("FromPort") == rule.get("ToPort") == 5432:
                    pairs = rule.get("UserIdGroupPairs", [])
                    owned = [pair for pair in pairs if pair.get("GroupId") == ingress["source"]]
                    require(all(set(pair) <= {"GroupId", "UserId"} and pair.get("UserId") == account for pair in owned), "admission-created-database-rule-mismatch")
                    removed += len(owned)
                    rule["UserIdGroupPairs"] = [pair for pair in pairs if pair not in owned]
            require(removed == 1, "admission-created-database-rule-mismatch")
            matches[0]["IpPermissions"] = [rule for rule in matches[0].get("IpPermissions", []) if any(rule.get(key) for key in ("UserIdGroupPairs", "IpRanges", "Ipv6Ranges", "PrefixListIds"))]
    snapshot = {"parameters": parameters, "security_groups": sorted(groups, key=lambda row: row["GroupId"]),
        "roles": {arn: state for arn, (state, _grants) in sorted(roles.items())}, "queues": queues,
        "consumers": consumers, "routes": sorted(routes, key=lambda row: row["RouteTableId"]),
        "regional_queue_policies": policies, **subnet_paths}
    return {"schema": "deploy/scheduling-network-observation/v1", "verdict": "observed", "account": account, "region": region, "vpc": vpc,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "consumer_count": len(consumers), "legacy_role_count": 4, "legacy_queue_count": 2,
        "preservation_sha256": fingerprint(snapshot), "snapshot": snapshot}


def update_overrides(actual, desired, *, controls_only, fault_only=False):
    """Select only owned changes; shared change_sets renders UsePreviousValue."""
    require(isinstance(actual, dict) and isinstance(desired, dict) and set(actual) == set(desired), "admission-parameter-set-changed")
    require(not (controls_only and fault_only), "admission-mixed-control-change")
    owned = {"DenyDispatcherSend"} if fault_only else {"TickEnabled", "WorkerEnabled"} if controls_only else set()
    require(all(actual[key] == desired[key] for key in actual if key not in owned), "admission-nonowned-parameter-change")
    if controls_only:
        require(owned.issubset(actual) and all(desired[key] in {"true", "false"} for key in owned), "admission-control-value-invalid")
        require(desired["TickEnabled"] != "true" or desired["WorkerEnabled"] == "true", "admission-worker-required-before-tick")
        require(desired.get("DenyDispatcherSend", "false") == "false", "admission-delivery-fault-not-restored")
    if fault_only:
        require(owned.issubset(actual) and desired["DenyDispatcherSend"] in {"true", "false"}, "admission-control-value-invalid")
        require(all(actual.get(key) == desired.get(key) == "false" for key in ("TickEnabled", "WorkerEnabled")), "admission-fault-requires-disabled-controls")
    return {key: desired[key] for key in owned if desired[key] != actual[key]}


def disabled_facts(provider, binding, parameters, template, *, normalize, parameter_values):
    """Verify immutable disabled resource state; not runtime or release acceptance."""
    value = provider("cloudformation", "describe-stacks", StackName=binding["stack"]).get("Stacks")
    require(isinstance(value, list) and len(value) == 1, "admission-stack-observation-invalid")
    stack = value[0]
    require(stack.get("StackName") == binding["stack"] and stack.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}, "admission-stack-not-stable")
    actual = parameter_values(stack.get("Parameters"))
    require(actual == parameters and parameters.get("TickEnabled") == parameters.get("WorkerEnabled") == "false"
            and parameters.get("DenyDispatcherSend", "false") == "false", "admission-disabled-parameters-mismatch")
    deployed = provider("cloudformation", "get-template", StackName=stack["StackId"], TemplateStage="Original").get("TemplateBody")
    require(normalize(deployed) == template, "admission-deployed-template-mismatch")
    resources = collection(provider, "cloudformation", "list-stack-resources", "StackResourceSummaries", StackName=stack["StackId"])
    require(len(resources) == len(template["Resources"]) and {row.get("LogicalResourceId") for row in resources} == set(template["Resources"]), "admission-resource-inventory-mismatch")
    require(all(row.get("ResourceType") == template["Resources"][row["LogicalResourceId"]]["Type"]
                and row.get("ResourceStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"} and isinstance(row.get("PhysicalResourceId"), str) for row in resources), "admission-resource-state-mismatch")
    return {"schema": "deploy/scheduling-disabled-observation/v1", "verdict": "observed", "stack_id": stack["StackId"],
        "parameters_sha256": fingerprint(parameters), "template_sha256": fingerprint(template),
        "resources_sha256": fingerprint(sorted(resources, key=lambda row: row["LogicalResourceId"])),
        "qualification": "disabled-provider-state-only"}


def utc(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value), "admission-timestamp-invalid")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AdmissionFailure("admission-timestamp-invalid") from None


def function_log_stream(stream, version_arn):
    """Bind the documented custom-group stream to one qualified function.

    The environment identifier is opaque: only its bracket/path delimiters
    and control characters are constrained, not an invented UUID alphabet.
    """
    require(isinstance(version_arn, str) and re.fullmatch(r"arn:aws:lambda:[a-z0-9-]+:[0-9]{12}:function:[A-Za-z0-9_-]+:[1-9][0-9]*", version_arn), "admission-function-version-invalid")
    function, version = version_arn.rsplit(":", 2)[1:]
    require(isinstance(stream, str) and len(stream) <= 512 and re.fullmatch(r"\d{4}/\d{2}/\d{2}/" + re.escape(function)
        + r"\[" + re.escape(version) + r"\]\[[^\[\]/\x00-\x1f\x7f]+\]", stream), "admission-function-log-stream-mismatch")
    try:
        datetime.strptime(stream[:10], "%Y/%m/%d")
    except ValueError:
        raise AdmissionFailure("admission-function-log-stream-mismatch") from None
    return stream


def preflight_body(body, expected, reservation, *, now=None, fresh=True):
    """Validate only a response obtained by the owned Invoke/log reader."""
    require(isinstance(body, dict) and set(body) == {"schema", "purpose", "source_revision", "request_id", "function_arn", "operation_id", "checked_at", "database", "queue"}, "admission-preflight-shape-invalid")
    operation_id = str(uuid.UUID(reservation["operation_id"].removeprefix("scheduling-preflight-")))
    require(body["schema"] == "kanbien/scheduling-runtime-preflight/v1" and body["operation_id"] == operation_id
        and all(body[key] == expected[key] for key in ("purpose", "source_revision", "function_arn", "database")), "admission-preflight-identity-mismatch")
    require(isinstance(body["request_id"], str) and re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[1-5][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}", body["request_id"]), "admission-preflight-request-invalid")
    checked, reserved = utc(body["checked_at"]), utc(reservation["reserved_at"].replace("+00:00", "Z"))
    current = now or datetime.now(timezone.utc)
    # Original-result reconciliation remains valid after the admission window.
    # A later action separately requires a recent observation; age never permits
    # replaying an uncertain original Invoke.
    require(0 <= (checked - reserved).total_seconds() <= 120, "admission-preflight-interval-invalid")
    require(not fresh or -30 <= (current - checked).total_seconds() <= 900, "admission-preflight-stale")
    if expected["purpose"] == "dispatch":
        require(body["queue"] is None, "admission-preflight-dispatch-queue-invalid")
    else:
        require(body["queue"] == expected["queue"], "admission-preflight-endpoint-mismatch")
    return body


def preflight_logs(logs, expected, reservation, *, body=None, now=None, fresh=True):
    """Use the owned success log plus AWS's actual request/billing report.

    Supports only direct SafeLogger records and the documented Lambda JSON
    envelope. No arbitrary nested object traversal or caller success flags.
    """
    require(isinstance(logs, list) and len(logs) <= 1000, "admission-preflight-logs-invalid")
    results, reports = [], []
    for record in logs:
        require(isinstance(record, dict), "admission-preflight-logs-invalid")
        if record.get("type") == "platform.report":
            reports.append(record.get("record"))
            continue
        selected = record
        if set(record) & {"timestamp", "requestId"} and "message" in record:
            selected = record["message"]
            if isinstance(selected, str):
                try:
                    selected = json.loads(selected)
                except (ValueError, RecursionError):
                    continue
        if isinstance(selected, dict) and selected.get("level") == "info" and selected.get("message") == "Scheduling read-only preflight completed.":
            fields = selected.get("fields")
            if isinstance(fields, dict) and set(fields) == {"scheduling_preflight"}:
                candidate = fields["scheduling_preflight"]
                if isinstance(candidate, dict) and candidate.get("operation_id") == str(uuid.UUID(reservation["operation_id"].removeprefix("scheduling-preflight-"))):
                    results.append(candidate)
    require(len(results) == 1, "admission-preflight-result-not-unique")
    observed = preflight_body(results[0], expected, reservation, now=now, fresh=fresh)
    require(body is None or body == observed, "admission-preflight-response-log-mismatch")
    selected = [row for row in reports if isinstance(row, dict) and row.get("requestId") == observed["request_id"]]
    require(len(selected) == 1, "admission-preflight-report-not-unique")
    report = selected[0]
    require(report.get("status", "success") == "success", "admission-preflight-runtime-failed")
    metrics = report.get("metrics", {})
    require(type(metrics.get("billedDurationMs")) in {int, float} and 0 < metrics["billedDurationMs"] <= 120000
        and metrics.get("memorySizeMB") == 512, "admission-preflight-billing-invalid")
    return {"response": observed, "billed_duration_ms": metrics["billedDurationMs"], "memory_mb": 512,
        "request_id": observed["request_id"], "logs_sha256": fingerprint(logs),
        "report": {"type": "platform.report", "record": {"requestId": report["requestId"], "status": report.get("status", "success"),
            "metrics": {"billedDurationMs": metrics["billedDurationMs"], "memorySizeMB": metrics["memorySizeMB"]}}}}


def invocation_evidence(metadata, body, expected, reservation, *, now=None):
    require(isinstance(metadata, dict) and metadata.get("StatusCode") == 200 and "FunctionError" not in metadata
        and metadata.get("ExecutedVersion") == expected["function_arn"].rsplit(":", 1)[1], "admission-preflight-invocation-failed")
    preflight_body(body, expected, reservation, now=now)
    try:
        encoded = metadata.get("LogResult")
        require(isinstance(encoded, str) and len(encoded) <= 16384, "admission-preflight-logs-invalid")
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        logs = [json.loads(line) for line in decoded.splitlines() if line.strip()]
    except (ValueError, UnicodeError, binascii.Error, RecursionError):
        raise AdmissionFailure("admission-preflight-logs-invalid") from None
    return preflight_logs(logs, expected, reservation, body=body, now=now)
