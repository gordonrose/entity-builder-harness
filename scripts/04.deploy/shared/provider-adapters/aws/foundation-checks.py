#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.foundation-checks
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate shared AWS foundation observations and proposed or existing private networks through caller-owned read access.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network]
#   used_by:
#   - id: deploy.library.aws.environment-sessions
#     path: scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py
#   - id: deploy.plan.consolidate-core-platform-deployment-routes
#     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
from ipaddress import IPv4Network
from decimal import Decimal, InvalidOperation
import json
import re

STABLE_STACK_STATUSES = frozenset({"CREATE_COMPLETE", "UPDATE_COMPLETE"})
NETWORK_OUTPUTS = frozenset({"VpcId", "PrivateSubnetIds", "ClusterArn", "LogGroupName", "ServiceDiscoveryArn"})


class FoundationFailure(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(self.code)


def require(condition, reason):
    if not condition:
        raise FoundationFailure("foundation-" + reason)


def only(document, key, reason):
    rows = document.get(key) if isinstance(document, dict) else None
    require(isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict), reason)
    return rows[0]


def stack_outputs(document, required):
    """Validate one completed stack; do not silently discard malformed rows."""
    stack = only(document, "Stacks", "stack-observation-invalid")
    status = stack.get("StackStatus")
    require(isinstance(status, str), "stack-observation-invalid")
    require(status in STABLE_STACK_STATUSES, "stack-not-ready")
    rows = stack.get("Outputs")
    require(isinstance(rows, list), "outputs-invalid")
    outputs = {}
    for row in rows:
        require(isinstance(row, dict), "outputs-invalid")
        key, value = row.get("OutputKey"), row.get("OutputValue")
        require(isinstance(key, str) and bool(key) and isinstance(value, str) and bool(value), "outputs-invalid")
        require(key not in outputs, "outputs-ambiguous")
        outputs[key] = value
    require(set(required) <= outputs.keys(), "outputs-missing")
    return outputs


def foundation(document, required, expected):
    outputs = stack_outputs(document, required)
    require(outputs.get("ClusterArn") == expected["cluster_arn"], "cluster-mismatch")
    require(outputs.get("LogGroupName") == expected["log_group"], "log-group-mismatch")
    return outputs


def budget_configuration(value):
    """Normalize the supported target-filtered monthly cost budget, not its evidence."""
    require(isinstance(value, dict), "budget-observation-invalid")
    name, limit, filters = value.get("BudgetName"), value.get("BudgetLimit"), value.get("CostFilters")
    require(isinstance(name, str) and 0 < len(name) <= 100 and not any(ord(c) < 32 for c in name)
            and value.get("BudgetType") == "COST" and value.get("TimeUnit") == "MONTHLY"
            and isinstance(limit, dict) and isinstance(filters, dict), "budget-configuration-invalid")
    raw = limit.get("Amount")
    require(type(raw) in (str, int, float) and len(str(raw)) <= 128, "budget-amount-invalid")
    try: amount = Decimal(str(raw))
    except InvalidOperation: raise FoundationFailure("foundation-budget-amount-invalid") from None
    require(amount.is_finite() and amount > 0, "budget-amount-invalid")
    unit, tags = limit.get("Unit"), filters.get("TagKeyValue")
    require(isinstance(unit, str) and re.fullmatch(r"[A-Z]{3}", unit) is not None
            and set(filters) == {"TagKeyValue"} and isinstance(tags, list) and len(tags) == 1
            and isinstance(tags[0], str) and re.fullmatch(r"user:[^$\s]+\$[^$\s]+", tags[0]) is not None,
            "budget-configuration-invalid")
    return name, value["BudgetType"], value["TimeUnit"], amount, unit, tags[0]


def budget(observed, expected):
    require(budget_configuration(observed) == budget_configuration(expected), "budget-configuration-mismatch")


def endpoint_policy(observed, expected, service, account, region, required_resource):
    """Exact declared access plus independent service restrictions, not IAM evaluation."""
    reads = frozenset({"ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"})
    token = frozenset({"ecr:GetAuthorizationToken"})
    secret = frozenset({"secretsmanager:GetSecretValue"})
    require(service in {"ecr.api", "ecr.dkr", "secretsmanager"}, "endpoint-policy-service-unsupported")

    def normalized(value):
        def pairs(items):
            result = {}
            for key, item in items:
                if key in result: raise ValueError()
                result[key] = item
            return result
        try:
            require(len(value if isinstance(value, str) else json.dumps(value)) <= 65536, "endpoint-policy-invalid")
            if isinstance(value, str): value = json.loads(value, object_pairs_hook=pairs)
        except (ValueError, TypeError, RecursionError): raise FoundationFailure("foundation-endpoint-policy-invalid") from None
        require(isinstance(value, dict) and set(value) == {"Version", "Statement"} and value["Version"] == "2012-10-17"
                and isinstance(value["Statement"], list) and len(value["Statement"]) == (2 if service == "ecr.api" else 1), "endpoint-policy-invalid")
        statements = {}
        for row in value["Statement"]:
            require(isinstance(row, dict) and set(row) == {"Effect", "Principal", "Action", "Resource"}
                    and row["Effect"] == "Allow" and row["Principal"] == "*", "endpoint-policy-invalid")
            selected = []
            for field in ("Action", "Resource"):
                entries = [row[field]] if isinstance(row[field], str) else row[field]
                require(isinstance(entries, list) and bool(entries) and all(isinstance(item, str) and 0 < len(item) <= 2048 for item in entries)
                        and len(set(entries)) == len(entries), "endpoint-policy-invalid")
                selected.append(frozenset(entries))
            actions, resources = selected
            require(actions not in statements, "endpoint-policy-invalid")
            if actions == token and service == "ecr.api":
                require(resources == {"*"}, "endpoint-policy-unsafe")
            else:
                require(actions == (secret if service == "secretsmanager" else reads), "endpoint-policy-unsafe")
                prefix = "arn:aws:" + ("secretsmanager" if service == "secretsmanager" else "ecr") + ":" + region + ":" + account + ":"
                suffix = r"secret:[A-Za-z0-9/_+=.@-]+" if service == "secretsmanager" else r"repository/[a-z0-9]+(?:[._/-][a-z0-9]+)*"
                require(all(re.fullmatch(re.escape(prefix) + suffix, resource) for resource in resources), "endpoint-policy-unsafe")
                require(required_resource in resources and (service != "secretsmanager" or resources == {required_resource}), "endpoint-policy-required-resource-missing")
            statements[actions] = resources
        require(set(statements) == ({reads, token} if service == "ecr.api" else {secret if service == "secretsmanager" else reads}), "endpoint-policy-unsafe")
        return statements
    require(normalized(expected) == normalized(observed), "endpoint-policy-mismatch")


def private_endpoints(provider, vpc_id, services):
    """Check caller-selected prerequisites; leave permission policies to callers."""
    require(isinstance(services, (set, frozenset, list, tuple)) and bool(services)
            and all(isinstance(name, str) and bool(name) for name in services)
            and len(set(services)) == len(services), "endpoint-selection-invalid")
    document = provider("ec2", "describe-vpc-endpoints", Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
    rows = document.get("VpcEndpoints") if isinstance(document, dict) else None
    require(isinstance(rows, list) and all(isinstance(row, dict) and isinstance(row.get("ServiceName"), str)
                                         and bool(row["ServiceName"]) for row in rows), "endpoint-observation-invalid")
    selected, groups = [], set()
    for name in sorted(services):
        matches = [row for row in rows if row["ServiceName"] == name]
        require(bool(matches), "endpoint-missing")
        require(len(matches) == 1, "endpoint-ambiguous")
        endpoint = matches[0]
        require(all(isinstance(endpoint.get(key), str) and bool(endpoint[key]) for key in ("VpcId", "State", "VpcEndpointType")), "endpoint-observation-invalid")
        require(endpoint["VpcId"] == vpc_id, "endpoint-vpc-mismatch")
        require(endpoint["State"] == "available", "endpoint-not-available")
        require(endpoint["VpcEndpointType"] == "Interface", "endpoint-not-interface")
        require(type(endpoint.get("PrivateDnsEnabled")) is bool, "endpoint-observation-invalid")
        require(endpoint["PrivateDnsEnabled"], "endpoint-dns-not-private")
        attached = endpoint.get("Groups")
        require(isinstance(attached, list) and len(attached) == 1 and isinstance(attached[0], dict)
                and isinstance(attached[0].get("GroupId"), str) and bool(attached[0]["GroupId"]), "endpoint-group-invalid")
        groups.add(attached[0]["GroupId"])
        selected.append(endpoint)
    require(len(groups) == 1, "endpoint-group-mismatch")
    return selected, next(iter(groups))


def s3_prefix_list(provider, region):
    """Resolve one prefix-list ID, not proof of an effective route or permission."""
    document = provider("ec2", "describe-managed-prefix-lists", Filters=[{"Name": "prefix-list-name", "Values": ["com.amazonaws." + region + ".s3"]}])
    rows = document.get("PrefixLists") if isinstance(document, dict) else None
    require(isinstance(rows, list) and all(isinstance(row, dict) and isinstance(row.get("PrefixListId"), str)
                                         and bool(row["PrefixListId"]) for row in rows), "s3-prefix-observation-invalid")
    require(bool(rows), "s3-prefix-missing")
    require(len(rows) == 1, "s3-prefix-ambiguous")
    return rows[0]["PrefixListId"]


def private_network_choice_syntax(choices, region):
    """Validate non-sensitive private ranges and zone names before retaining input."""
    fields = {"vpc_cidr", "subnet_one_cidr", "subnet_two_cidr", "availability_zone_one", "availability_zone_two"}
    require(isinstance(region, str)
            and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region) is not None,
            "network-choice-context-invalid")
    require(isinstance(choices, dict) and set(choices) == fields
            and all(isinstance(value, str) for value in choices.values()), "network-choices-invalid")
    private = tuple(IPv4Network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
    ranges = []
    for field in ("vpc_cidr", "subnet_one_cidr", "subnet_two_cidr"):
        try:
            value = IPv4Network(choices[field], strict=True)
        except ValueError:
            raise FoundationFailure("foundation-network-cidr-invalid") from None
        require(str(value) == choices[field], "network-cidr-invalid")
        require(any(value.subnet_of(parent) for parent in private), "network-cidr-not-private")
        require(16 <= value.prefixlen <= 28, "network-cidr-size-invalid")
        ranges.append(value)
    vpc, first, second = ranges
    require(all(value.subnet_of(vpc) and value != vpc for value in (first, second)), "network-subnet-containment-invalid")
    require(not first.overlaps(second), "network-subnet-overlap")
    zones = [choices["availability_zone_one"], choices["availability_zone_two"]]
    require(len(set(zones)) == 2 and all(re.fullmatch(re.escape(region) + r"[a-z]", name) for name in zones),
            "network-zone-selection-invalid")
    return dict(choices)


def private_network_choices(provider, choices, region):
    """Check syntax through its shared owner, then prove the actual native zones."""
    require(callable(provider), "network-choice-context-invalid")
    choices = private_network_choice_syntax(choices, region)
    zones = [choices["availability_zone_one"], choices["availability_zone_two"]]
    response = provider("ec2", "describe-availability-zones", ZoneNames=zones)
    rows = response.get("AvailabilityZones") if isinstance(response, dict) else None
    require(isinstance(rows, list) and all(isinstance(row, dict)
            and all(isinstance(row.get(key), str) for key in ("ZoneName", "ZoneId", "RegionName", "State", "ZoneType"))
            for row in rows), "network-zone-observation-invalid")
    require(len(rows) == 2 and {row["ZoneName"] for row in rows} == set(zones), "network-zone-selection-mismatch")
    require(all(row["RegionName"] == region for row in rows), "network-zone-region-mismatch")
    require(all(row["State"] == "available" for row in rows), "network-zone-not-available")
    require(all(row["ZoneType"] == "availability-zone" for row in rows), "network-zone-type-unsupported")
    require(all(re.fullmatch(r"[a-z0-9]+-az[0-9]+", row["ZoneId"]) for row in rows)
            and len({row["ZoneId"] for row in rows}) == 2, "network-zone-ambiguous")
    return dict(choices)


def private_network(provider, outputs, namespace_name, region):
    """Check declared private placement, not actual application connectivity."""
    require(isinstance(outputs, dict) and all(isinstance(outputs.get(key), str) and outputs[key] for key in NETWORK_OUTPUTS), "outputs-invalid")
    vpc_id = outputs["VpcId"]
    vpc = only(provider("ec2", "describe-vpcs", VpcIds=[vpc_id]), "Vpcs", "vpc-observation-invalid")
    require(isinstance(vpc.get("VpcId"), str) and isinstance(vpc.get("State"), str), "vpc-observation-invalid")
    require(vpc.get("VpcId") == vpc_id, "vpc-mismatch")
    require(vpc.get("State") == "available", "vpc-not-available")
    cidr = vpc.get("CidrBlock")
    require(isinstance(cidr, str), "vpc-cidr-invalid")
    try:
        IPv4Network(cidr)
    except ValueError:
        raise FoundationFailure("foundation-vpc-cidr-invalid") from None
    subnet_ids = outputs["PrivateSubnetIds"].split(",")
    require(all(subnet_ids) and len(set(subnet_ids)) == len(subnet_ids), "subnet-selection-invalid")
    response = provider("ec2", "describe-subnets", SubnetIds=subnet_ids)
    subnets = response.get("Subnets") if isinstance(response, dict) else None
    require(isinstance(subnets, list) and all(isinstance(row, dict) and isinstance(row.get("SubnetId"), str) for row in subnets), "subnet-observation-invalid")
    require(len(subnets) == len(subnet_ids) and {row["SubnetId"] for row in subnets} == set(subnet_ids), "subnet-selection-mismatch")
    require(all(row.get("VpcId") == vpc_id for row in subnets), "subnet-vpc-mismatch")
    require(all(row.get("State") == "available" for row in subnets), "subnet-not-available")
    require(all(type(row.get("MapPublicIpOnLaunch")) is bool for row in subnets), "subnet-observation-invalid")
    require(all(row.get("MapPublicIpOnLaunch") is False for row in subnets), "subnet-not-private")
    response = provider("servicediscovery", "get-service", Id=outputs["ServiceDiscoveryArn"].rsplit("/", 1)[-1])
    service = response.get("Service") if isinstance(response, dict) else None
    dns = service.get("DnsConfig") if isinstance(service, dict) else None
    namespace_id = dns.get("NamespaceId") if isinstance(dns, dict) else None
    require(isinstance(namespace_id, str) and re.fullmatch(r"ns-[a-z0-9]+", namespace_id) is not None, "namespace-reference-invalid")
    response = provider("servicediscovery", "get-namespace", Id=namespace_id)
    namespace = response.get("Namespace") if isinstance(response, dict) else None
    require(isinstance(namespace, dict) and all(isinstance(namespace.get(key), str) for key in ("Id", "Name", "Type")), "namespace-observation-invalid")
    require(namespace.get("Id") == namespace_id and namespace.get("Name") == namespace_name, "namespace-mismatch")
    require(namespace.get("Type") == "DNS_PRIVATE", "namespace-not-private")
    properties = namespace.get("Properties")
    dns = properties.get("DnsProperties") if isinstance(properties, dict) else None
    zone_id = dns.get("HostedZoneId") if isinstance(dns, dict) else None
    require(isinstance(zone_id, str) and bool(zone_id) and zone_id.isascii() and zone_id.isalnum() and zone_id == zone_id.upper(), "zone-reference-invalid")
    response = provider("route53", "get-hosted-zone", Id=zone_id)
    zone = response.get("HostedZone") if isinstance(response, dict) else None
    config = zone.get("Config") if isinstance(zone, dict) else None
    require(isinstance(config, dict) and type(config.get("PrivateZone")) is bool, "zone-observation-invalid")
    require(config["PrivateZone"], "zone-not-private")
    vpcs = response.get("VPCs")
    require(isinstance(vpcs, list) and all(isinstance(row, dict) and isinstance(row.get("VPCRegion"), str) and isinstance(row.get("VPCId"), str) for row in vpcs), "zone-vpcs-invalid")
    require(len(vpcs) == 1 and vpcs[0]["VPCRegion"] == region and vpcs[0]["VPCId"] == vpc_id, "zone-vpc-mismatch")
    return {"VpcId": vpc_id, "VpcCidr": cidr, "PrivateSubnetIds": outputs["PrivateSubnetIds"],
            "ClusterArn": outputs["ClusterArn"], "NamespaceId": namespace_id, "LogGroupName": outputs["LogGroupName"]}
