#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.preparation-inputs
#   version: 9
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Resolve AWS preparation inputs from existing declarations without provider calls or a parallel configuration registry.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.plan.consolidate-core-platform-deployment-routes
#     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
import importlib.util
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
import re


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


ROOT = Path(__file__).resolve().parents[6]
PATHS = module("preparation_declaration_paths", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py")
CF_REFERENCE = "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py"
CF = module("preparation_cloudformation", ROOT / CF_REFERENCE)
CHECKS = module("preparation_foundation_checks", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py")
PUBLICATION_REFERENCE = "scripts/04.deploy/shared/provider-adapters/aws/ecr_publication.py"
PUBLICATION = None
try:
    PUBLICATION = module("preparation_publication_sources", ROOT / PUBLICATION_REFERENCE)
except Exception:
    # Existing read callers own finite reporting of unavailable source helpers.
    pass

PG = module("preparation_postgresql_version", ROOT / "scripts/04.deploy/shared/postgresql-version.py")
LIFECYCLE_REFERENCE = "scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/policy/implementation.py"
SESSION_REFERENCE = "scripts/04.deploy/lifecycle/00-target-alignment/capabilities/environment-lifecycle/session-binding/implementation.py"
LIFECYCLE = None
try:
    LIFECYCLE = module("preparation_environment_lifecycle", ROOT / LIFECYCLE_REFERENCE)
except Exception:
    # Existing load callers own reporting; retain no imported exception details.
    pass


class InputFailure(ValueError):
    """Finite condition only; source text and native errors stay private."""
    def __init__(self, condition):
        self.code = "preparation-inputs-" + condition
        super().__init__(self.code)


def require(condition, reason):
    if not condition:
        raise InputFailure(reason)


def text(value, pattern, reason):
    require(isinstance(value, str) and re.fullmatch(pattern, value) is not None, reason)
    return value


def one(rows, key, value, reason):
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), reason + "-invalid")
    selected = [row for row in rows if row.get(key) == value]
    require(bool(selected), reason + "-missing")
    require(len(selected) == 1, reason + "-ambiguous")
    return selected[0]


def load(root, target, scope):
    try:
        require(LIFECYCLE is not None, "source-unavailable")
        return _load(root, target, scope)
    except InputFailure:
        raise
    except (AttributeError, KeyError, TypeError, RecursionError):
        raise InputFailure("document-invalid") from None


def endpoint_policies(template, account, region):
    """Project only supported endpoint policy literals and explicit references."""
    def literal(value):
        if isinstance(value, dict) and set(value) == {"Fn::Sub"}:
            value = value["Fn::Sub"]
            require(isinstance(value, str), "endpoint-policy-source-unsupported")
            values = {"AWS::AccountId": account, "AWS::Region": region}
            require(all(name in values for name in re.findall(r"\$\{([^}]+)\}", value)), "endpoint-policy-source-unsupported")
            value = re.sub(r"\$\{([^}]+)\}", lambda match: values[match[1]], value)
        require(isinstance(value, str) and bool(value) and "${" not in value, "endpoint-policy-source-unsupported")
        return value

    def resource(value):
        if not isinstance(value, dict) or set(value) != {"Ref"}: return literal(value)
        name = value["Ref"]
        require(isinstance(name, str), "endpoint-policy-reference-unsupported")
        parameter = template.get("Parameters", {}).get(name)
        if parameter is not None:
            require(isinstance(parameter, dict) and parameter.get("Type") == "String", "endpoint-policy-reference-unsupported")
            pattern = parameter.get("AllowedPattern")
            require(pattern is None or isinstance(pattern, str), "endpoint-policy-reference-unsupported")
            return {"parameter": name, "pattern": pattern}
        selected = template.get("Resources", {}).get(name, {})
        require(selected.get("Type") == "AWS::SecretsManager::Secret", "endpoint-policy-reference-unsupported")
        outputs = [key for key, row in template.get("Outputs", {}).items() if isinstance(row, dict) and row.get("Value") == value]
        require(bool(outputs), "endpoint-policy-output-missing")
        return {"outputs": sorted(outputs)}

    policies = {}
    for entry in template.get("Resources", {}).values():
        if entry.get("Type") != "AWS::EC2::VPCEndpoint": continue
        properties = entry.get("Properties", {})
        service = literal(properties.get("ServiceName"))
        if service not in {"com.amazonaws." + region + "." + suffix for suffix in ("ecr.api", "ecr.dkr", "secretsmanager")}: continue
        require(service not in policies, "endpoint-policy-selection-ambiguous")
        policy = properties.get("PolicyDocument")
        require(isinstance(policy, dict) and set(policy) == {"Version", "Statement"} and policy["Version"] == "2012-10-17"
                and isinstance(policy["Statement"], list) and bool(policy["Statement"]), "endpoint-policy-source-unsupported")
        statements = []
        for row in policy["Statement"]:
            require(isinstance(row, dict) and set(row) == {"Effect", "Principal", "Action", "Resource"}, "endpoint-policy-source-unsupported")
            values = row["Resource"] if isinstance(row["Resource"], list) else [row["Resource"]]
            statements.append({**row, "Resource": [resource(value) for value in values]})
        policies[service] = {**policy, "Statement": statements}
    return policies


def policy_values(policy, parameters, outputs):
    """Bind projected references to already checked stack facts; never guess values."""
    def bind(value):
        if isinstance(value, str): return value
        values = [parameters.get(value["parameter"])] if "parameter" in value else [outputs.get(key) for key in value["outputs"]]
        require(all(isinstance(item, str) and bool(item) for item in values), "endpoint-policy-reference-missing")
        require(len(set(values)) == 1, "endpoint-policy-output-mismatch")
        selected = values[0]
        pattern = value.get("pattern")
        if pattern is not None:
            try: matched = re.fullmatch(pattern, selected)
            except re.error: raise InputFailure("endpoint-policy-pattern-unsupported") from None
            require(matched is not None, "endpoint-policy-parameter-mismatch")
        return selected
    return {**policy, "Statement": [{**row, "Resource": [bind(value) for value in row["Resource"]]} for row in policy["Statement"]]}


def source_bytes(root, reference, capture=None):
    path = PATHS.within(root, reference)
    require(path is not None, "path-invalid")
    try:
        raw = capture[reference] if capture is not None and reference in capture else path.read_bytes()
    except OSError: raise InputFailure("source-unavailable") from None
    if capture is not None: capture[reference] = raw
    return raw


def read_document(root, reference, references=None, capture=None):
    try: source = source_bytes(root, reference, capture).decode("utf-8")
    except UnicodeError: raise InputFailure("source-unavailable") from None
    try: result = CF.template(source)
    except ValueError: raise InputFailure("document-invalid") from None
    if references is not None: references.add(reference)
    return result


def instance_controls(document, temporary=False):
    """Check template-owned creation/activation controls and production defaults.

    These are source-plan selections, not authorization to change a live stack.
    Optional role/secret groups and bounded ECS counts are explicit controls;
    named default-false guards may additionally be resolved for temporary plans.
    """
    parameters, resources = document.get("Parameters", {}), document.get("Resources", {})
    conditions, outputs = document.get("Conditions", {}), document.get("Outputs", {})
    metadata = document.get("Metadata")
    require(isinstance(metadata, dict) and "CreationControls" in metadata, "instance-controls-invalid")
    controls = metadata["CreationControls"]
    require(all(isinstance(value, dict) for value in (parameters, resources, conditions, outputs, controls)), "instance-controls-invalid")
    values, guards = {}, []
    def names(value, allow_empty=False):
        require(isinstance(value, list) and (allow_empty or bool(value))
                and all(isinstance(item, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", item) for item in value)
                and len(set(value)) == len(value), "instance-controls-invalid")
        return value
    claimed = set()
    for parameter, row in controls.items():
        require(isinstance(parameter, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", parameter) and isinstance(row, dict), "instance-controls-invalid")
        kind = row.get("kind")
        require(kind in ("optional-resources", "desired-count"), "instance-controls-invalid")
        fields = {"kind", "temporary", "resources"} | ({"condition", "outputs"} if kind == "optional-resources" else {"active"})
        require(set(row) == fields, "instance-controls-invalid")
        selected = names(row["resources"])
        require(not claimed.intersection(selected), "instance-controls-invalid")
        claimed.update(selected)
        require(all(isinstance(resources.get(name), dict) for name in selected), "instance-controls-invalid")
        if kind == "desired-count":
            expected = parameters.get(parameter)
            require(isinstance(expected, dict) and set(expected) == {"Type", "Default", "AllowedValues"}
                    and expected["Type"] == "Number" and type(expected["Default"]) is int and expected["Default"] >= 0, "instance-controls-invalid")
            domain = expected["AllowedValues"]
            require(isinstance(domain, list) and bool(domain) and all(type(value) is int and value >= 0 for value in domain)
                    and len(set(domain)) == len(domain) and 0 in domain and expected["Default"] in domain, "instance-controls-invalid")
            require(type(row["temporary"]) is int and row["temporary"] == 0, "instance-controls-invalid")
            require(type(row["active"]) is int and row["active"] > 0 and row["active"] in domain, "instance-controls-invalid")
            require(all(resources[name].get("Type") == "AWS::ECS::Service" and resources[name].get("Properties", {}).get("DesiredCount") == {"Ref": parameter}
                        for name in selected), "instance-controls-invalid")
            require({name for name, value in resources.items() if isinstance(value, dict) and value.get("Type") == "AWS::ECS::Service"
                     and value.get("Properties", {}).get("DesiredCount") == {"Ref": parameter}} == set(selected), "instance-controls-invalid")
        else:
            expected = {"Type": "String", "Default": "true", "AllowedValues": ["true", "false"]}
            require(row["temporary"] == "false" and all(resources[name].get("Type") in ("AWS::IAM::Role", "AWS::SecretsManager::Secret") for name in selected), "instance-controls-invalid")
            guard = row["condition"]
            require(isinstance(guard, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", guard) and guard not in guards, "instance-controls-invalid")
            require(conditions.get(guard) == {"Fn::Equals": [{"Ref": parameter}, "true"]}, "instance-controls-invalid")
            for section, bound in ((resources, selected), (outputs, names(row["outputs"], allow_empty=True))):
                require(all(isinstance(section.get(key), dict) and section[key].get("Condition") == guard for key in bound), "instance-controls-invalid")
                require({key for key, value in section.items() if isinstance(value, dict) and value.get("Condition") == guard} == set(bound), "instance-controls-invalid")
            guards.append(guard)
        require(CF.templates_equal({"value": parameters.get(parameter)}, {"value": expected}), "instance-controls-invalid")
        values[parameter] = row["temporary"] if temporary else expected["Default"]
    # Closure detects omitted declarations; it never invents temporary choices.
    # Unsupported default-true optional resource groups fail closed.
    for resource in resources.values():
        require(isinstance(resource, dict), "instance-controls-invalid")
        count = resource.get("Properties", {}).get("DesiredCount")
        if resource.get("Type") == "AWS::ECS::Service":
            require(isinstance(count, dict) and set(count) == {"Ref"} and isinstance(count["Ref"], str), "instance-controls-invalid")
            parameter = count["Ref"]
            require(parameter in controls and controls[parameter]["kind"] == "desired-count", "instance-controls-invalid")
        guard = resource.get("Condition")
        expression = conditions.get(guard) if isinstance(guard, str) else None
        operands = expression.get("Fn::Equals") if isinstance(expression, dict) and set(expression) == {"Fn::Equals"} else None
        if isinstance(operands, list) and len(operands) == 2 and isinstance(operands[0], dict) and set(operands[0]) == {"Ref"} and isinstance(operands[0]["Ref"], str) and operands[1] == "true":
            parameter = operands[0]["Ref"]
            declaration = parameters.get(parameter, {})
            if isinstance(declaration, dict) and declaration.get("Type") == "String" and declaration.get("Default") == "true":
                require(resource.get("Type") in ("AWS::IAM::Role", "AWS::SecretsManager::Secret") and parameter in controls
                        and controls[parameter]["kind"] == "optional-resources", "instance-controls-invalid")
    default_guards = names(metadata.get("TemporaryDefaultConditions", []), allow_empty=True)
    default_parameters = set()
    for guard in default_guards:
        require(guard not in guards, "instance-controls-invalid")
        expression = conditions.get(guard)
        operands = expression.get("Fn::Equals") if isinstance(expression, dict) and set(expression) == {"Fn::Equals"} else None
        require(isinstance(operands, list) and len(operands) == 2 and operands[1] == "true"
                and isinstance(operands[0], dict) and set(operands[0]) == {"Ref"}, "instance-controls-invalid")
        parameter = operands[0]["Ref"]
        require(isinstance(parameter, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", parameter)
                and parameter not in values and parameter not in default_parameters, "instance-controls-invalid")
        declaration = parameters.get(parameter)
        require(isinstance(declaration, dict) and set(declaration) == {"Type", "Default", "AllowedValues"}
                and declaration["Type"] == "String" and declaration["Default"] == "false"
                and isinstance(declaration["AllowedValues"], list) and len(declaration["AllowedValues"]) == 2
                and all(isinstance(value, str) for value in declaration["AllowedValues"])
                and set(declaration["AllowedValues"]) == {"true", "false"}, "instance-controls-invalid")
        default_parameters.add(parameter)
        if temporary:
            values[parameter] = declaration["Default"]
            guards.append(guard)
    return values, tuple(guards)


def target_template(document, target, references=None):
    """Project checked production defaults; public callers pin their target."""
    controls, guards = instance_controls(document)
    try: selected = CF.project_parameters(document, ["ResourceNamePrefix", *controls], condition_names=guards)
    except ValueError: raise InputFailure("document-invalid") from None
    require(selected["Parameters"]["ResourceNamePrefix"]["Default"] == target, "target-mismatch")
    if references is not None: references.add(CF_REFERENCE)
    return selected


def discard_projection(original, projected):
    """Copy an original phase projection with declared disposable retention.

    This closed source inventory is not physical-resource cleanup support. New
    resource types or retention paths require their owning reviewed capability.
    """
    supported = {
        "AWS::Budgets::Budget", "AWS::CloudWatch::Alarm", "AWS::EC2::RouteTable",
        "AWS::EC2::SecurityGroup", "AWS::EC2::SecurityGroupEgress", "AWS::EC2::SecurityGroupIngress",
        "AWS::EC2::Subnet", "AWS::EC2::SubnetRouteTableAssociation", "AWS::EC2::VPC",
        "AWS::EC2::VPCEndpoint", "AWS::ECS::Cluster", "AWS::ECS::Service", "AWS::ECS::TaskDefinition",
        "AWS::IAM::Role", "AWS::Logs::LogGroup", "AWS::RDS::DBInstance", "AWS::RDS::DBSubnetGroup",
        "AWS::SNS::Subscription", "AWS::SNS::Topic", "AWS::SecretsManager::Secret",
        "AWS::ServiceDiscovery::PrivateDnsNamespace", "AWS::ServiceDiscovery::Service",
    }
    result = deepcopy(projected)
    resources = result.get("Resources")
    source_resources = original.get("Resources")
    metadata = original.get("Metadata")
    require(all(isinstance(value, dict) for value in (resources, source_resources, metadata)), "discard-controls-invalid")
    controls = metadata.get("DiscardControls", {})
    require(isinstance(controls, dict), "discard-controls-invalid")
    permitted = {
        "AWS::RDS::DBInstance": {"attributes": {"DeletionPolicy": "Delete", "UpdateReplacePolicy": "Delete"},
                                "properties": {"DeletionProtection": False, "DeleteAutomatedBackups": True, "BackupRetentionPeriod": 0}},
        "AWS::Logs::LogGroup": {"attributes": {"DeletionPolicy": "Delete", "UpdateReplacePolicy": "Delete"}, "properties": {}},
    }
    for logical, row in controls.items():
        require(isinstance(logical, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", logical)
                and isinstance(row, dict) and set(row) == {"type", "attributes", "properties"}, "discard-controls-invalid")
        source, selected = source_resources.get(logical), resources.get(logical)
        require(isinstance(source, dict) and isinstance(selected, dict)
                and isinstance(row["type"], str) and row["type"] in permitted
                and row["type"] == source.get("Type") == selected.get("Type"), "discard-controls-invalid")
        for section, paths in permitted[row["type"]].items():
            changes = row[section]
            require(isinstance(changes, dict) and set(changes) == set(paths), "discard-controls-invalid")
            before = source if section == "attributes" else source.get("Properties")
            after = selected if section == "attributes" else selected.get("Properties")
            require(isinstance(before, dict) and isinstance(after, dict), "discard-controls-invalid")
            for key, value in paths.items():
                transition = changes[key]
                require(isinstance(transition, dict) and set(transition) in ({"expected", "discard"}, {"expected_absent", "discard"}), "discard-controls-invalid")
                if key == "BackupRetentionPeriod":
                    require(set(transition) == {"expected", "discard"}, "discard-controls-invalid")
                if row["type"] == "AWS::Logs::LogGroup":
                    require(set(transition) == {"expected", "discard"} and transition["expected"] == "Retain", "discard-controls-invalid")
                require(type(transition["discard"]) is type(value) and transition["discard"] == value, "discard-controls-invalid")
                if "expected_absent" in transition:
                    require(transition["expected_absent"] is True and key not in before and key not in after, "discard-controls-invalid")
                else:
                    expected = transition["expected"]
                    require(type(expected) is type(value) and (section != "attributes" or expected in {"Delete", "Retain", "RetainExceptOnCreate", "Snapshot"})
                            and key in before and key in after
                            and CF.templates_equal({"value": before[key]}, {"value": expected})
                            and CF.templates_equal({"value": after[key]}, {"value": expected}), "discard-controls-invalid")
                after[key] = value
    for resource in resources.values():
        require(isinstance(resource, dict) and isinstance(resource.get("Type"), str)
                and resource["Type"] in supported, "discard-resource-type-unsupported")
        properties = resource.get("Properties", {})
        require(isinstance(properties, dict), "discard-retention-unresolved")
        database = resource["Type"] == "AWS::RDS::DBInstance"
        require(resource.get("DeletionPolicy", "Snapshot" if database else "Delete") == "Delete"
                and resource.get("UpdateReplacePolicy", "Delete") == "Delete", "discard-retention-unresolved")
        if database:
            require(properties.get("DeletionProtection") is False and properties.get("DeleteAutomatedBackups") is True
                    and type(properties.get("BackupRetentionPeriod")) is int and properties["BackupRetentionPeriod"] == 0,
                    "discard-retention-unresolved")
        else:
            require("DeletionProtection" not in properties and "DeleteAutomatedBackups" not in properties,
                    "discard-retention-unresolved")
        if resource["Type"] == "AWS::Logs::LogGroup":
            require(properties.get("DeletionProtectionEnabled", False) is False, "discard-retention-unresolved")
    return result


def budget_settings(root, target, foundation, references=None, capture=None):
    """Read only budget declarations; provisioning has no image/package prerequisite."""
    text(target, r"[a-zA-Z0-9][a-zA-Z0-9_-]*", "target-invalid")
    foundation = target_template(foundation, target, references)
    declaration = read_document(root, "infra/04.deploy/03.product/targets/" + target + "/10-foundation/budget-control.yml", references, capture)
    require(declaration.get("target") == target, "budget-target-mismatch")
    values = declaration.get("expected_provider_configuration")
    require(isinstance(values, dict) and set(values) == {"budget_name", "budget_type", "time_unit", "amount", "unit", "target_filter"}, "budget-declaration-invalid")
    expected = {"BudgetName": values["budget_name"], "BudgetType": values["budget_type"], "TimeUnit": values["time_unit"],
                "BudgetLimit": {"Amount": values["amount"], "Unit": values["unit"]}, "CostFilters": {"TagKeyValue": [values["target_filter"]]}}
    try: CHECKS.budget_configuration(expected)
    except CHECKS.FoundationFailure: raise InputFailure("budget-declaration-invalid") from None
    resources = foundation.get("Resources") if isinstance(foundation, dict) else None
    require(isinstance(resources, dict) and all(isinstance(row, dict) for row in resources.values()), "budget-template-invalid")
    budgets = [row.get("Properties", {}).get("Budget") for row in resources.values() if row.get("Type") == "AWS::Budgets::Budget" and isinstance(row.get("Properties"), dict)]
    selected = [row for row in budgets if isinstance(row, dict) and row.get("BudgetName") == expected["BudgetName"]]
    require(len(selected) == 1, "budget-selection-not-confirmed")
    try: CHECKS.budget(selected[0], expected)
    except CHECKS.FoundationFailure: raise InputFailure("budget-template-mismatch") from None
    return expected


def publication_repository(pipelines, pipeline_id, scope, region):
    """Use the same checked publication selection for ordinary and session reads."""
    text(pipeline_id, r"[a-zA-Z0-9][a-zA-Z0-9_-]*", "pipeline-selection-invalid")
    pipeline = one(pipelines.get("pipelines"), "id", pipeline_id, "pipeline")
    scopes = pipeline.get("used_by_scopes")
    require(isinstance(scopes, list) and scope in scopes, "pipeline-scope-mismatch")
    require(pipeline.get("provider_region_alias") == "aws-" + region, "pipeline-region-mismatch")
    return text(pipeline.get("package_destination"), r"[a-z0-9]+(?:[._/-][a-z0-9]+)*", "repository-invalid")


def _load(root, target, scope, capture=None):
    """Resolve one selected AWS scope. Returned references also feed impact analysis."""
    references = set()
    read = lambda reference: read_document(root, reference, references, capture)

    name = r"[a-zA-Z0-9][a-zA-Z0-9_-]*"
    text(target, name, "target-invalid")
    text(scope, name, "scope-invalid")
    base = "infra/04.deploy/03.product/targets/" + target
    profile = read(base + "/00-target/target-profile.yml")
    require(profile.get("schema") == "deploy/target-profile/v1" and profile.get("id") == target, "target-mismatch")
    try:
        lifecycle = LIFECYCLE.require_persistent(LIFECYCLE.read(profile))
    except LIFECYCLE.PolicyFailure as failure:
        raise InputFailure(failure.code) from None
    references.add(LIFECYCLE_REFERENCE)
    provider = profile.get("provider")
    require(isinstance(provider, dict) and provider.get("family") == "aws", "provider-unsupported")
    account = text(provider.get("account_id"), r"[0-9]{12}", "account-invalid")
    region = text(provider.get("region"), r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", "region-invalid")
    cli_profile = provider.get("profile")
    if "profile" in provider:
        text(cli_profile, r"[A-Za-z0-9][A-Za-z0-9_.-]*", "profile-invalid")
    foundation = provider.get("foundation")
    require(isinstance(foundation, dict), "foundation-invalid")
    foundation_stack = text(foundation.get("stack"), r"[A-Za-z][A-Za-z0-9-]*", "foundation-stack-invalid")
    foundation_template = foundation.get("template")
    require(PATHS.safe_path(foundation_template), "path-invalid")
    foundation_source = read(base + "/" + foundation_template)
    foundation_document = target_template(foundation_source, target, references)
    # Follow selected outputs, not fixed logical resource names or copied values.
    def resource_for(output, intrinsic, resource_type):
        value = foundation_document.get("Outputs", {}).get(output, {}).get("Value")
        require(isinstance(value, dict) and set(value) == {intrinsic}, "foundation-output-unsupported")
        reference = value[intrinsic]
        if intrinsic == "Fn::GetAtt":
            require(isinstance(reference, list) and len(reference) == 2 and reference[1] == "Arn", "foundation-output-unsupported")
            reference = reference[0]
        require(isinstance(reference, str), "foundation-output-unsupported")
        resource = foundation_document.get("Resources", {}).get(reference, {})
        require(resource.get("Type") == resource_type and isinstance(resource.get("Properties"), dict), "foundation-resource-unsupported")
        return resource["Properties"]
    cluster = resource_for("ClusterArn", "Fn::GetAtt", "AWS::ECS::Cluster")
    logs = resource_for("LogGroupName", "Ref", "AWS::Logs::LogGroup")
    service = resource_for("ServiceDiscoveryArn", "Fn::GetAtt", "AWS::ServiceDiscovery::Service")
    namespace_ref = service.get("DnsConfig", {}).get("NamespaceId")
    require(isinstance(namespace_ref, dict) and set(namespace_ref) == {"Ref"} and isinstance(namespace_ref["Ref"], str), "foundation-namespace-unsupported")
    namespace = foundation_document.get("Resources", {}).get(namespace_ref["Ref"], {})
    require(namespace.get("Type") == "AWS::ServiceDiscovery::PrivateDnsNamespace", "foundation-namespace-unsupported")
    foundation_expected = {
        "cluster_arn": "arn:aws:ecs:" + region + ":" + account + ":cluster/" + text(cluster.get("ClusterName"), r"[A-Za-z0-9_-]+", "foundation-cluster-unsupported"),
        "log_group": text(logs.get("LogGroupName"), r"[A-Za-z0-9_./#-]+", "foundation-log-group-unsupported"),
        "namespace": text(namespace.get("Properties", {}).get("Name"), r"[a-zA-Z0-9.-]+", "foundation-namespace-unsupported"),
    }

    def binding_for(selected):
        text(selected, name, "scope-invalid")
        binding = read(base + "/20-scopes/" + selected + "/10-workload-binding/workload-binding.yml")
        require(binding.get("target") == target and binding.get("scope") == selected, "binding-mismatch")
        selected_provider = binding.get("proposed_provider_binding")
        require(isinstance(selected_provider, dict), "binding-invalid")
        text(selected_provider.get("stack"), r"[A-Za-z][A-Za-z0-9-]*", "stack-invalid")
        require(PATHS.safe_path(selected_provider.get("template")), "path-invalid")
        source = read(base + "/" + selected_provider["template"])
        controls, _ = instance_controls(source)
        template = target_template(source, target, references)
        return binding, selected_provider, template, controls

    binding, selected, own_template, creation_parameters = binding_for(scope)
    image = read(binding.get("image_contract"))
    try: postgresql = PG.configuration(image) if "postgresql" in image or "postgresql" in image.get("payload", {}).get("required_dependency_ids", []) else None
    except PG.VersionFailure as failure: raise InputFailure(failure.code) from None
    program = binding.get("program_id")
    require(isinstance(program, str) and image.get("program_id") == program, "program-mismatch")
    require(image.get("runnable_program_contract") == binding.get("program_contract"), "program-contract-mismatch")
    programs = read(binding.get("program_contract"))
    one(programs.get("runnable_programs"), "id", program, "program")
    image_selection = one(programs.get("image_contracts"), "id", image.get("id"), "image")
    require(image_selection.get("program") == program, "image-program-mismatch")
    candidate = one(programs.get("package_candidates"), "image_contract", image.get("id"), "candidate")
    text(candidate.get("id"), name, "candidate-invalid")
    pipelines = read(base + "/40-package-custody/github-actions/pipeline-index.yml")
    repository = publication_repository(pipelines, selected.get("publication_pipeline"), scope, region)
    dependencies = selected.get("dependencies")
    require(isinstance(dependencies, dict), "dependencies-invalid")
    resolved = {}
    for key, dependency in dependencies.items():
        text(key, name, "dependency-invalid")
        require(isinstance(dependency, dict) and set(dependency) == {"scope", "output"}, "dependency-invalid")
        _, supplier, template, _ = binding_for(dependency["scope"])
        output = text(dependency["output"], name, "dependency-output-invalid")
        # Only supported RDS properties/output references, never arbitrary CF expressions.
        value = template.get("Outputs", {}).get(output, {}).get("Value")
        require(isinstance(value, dict) and set(value) == {"Ref"} and isinstance(value["Ref"], str), "dependency-output-unsupported")
        resource = template.get("Resources", {}).get(value["Ref"], {})
        require(resource.get("Type") == "AWS::RDS::DBInstance", "dependency-output-unsupported")
        properties = resource.get("Properties", {})
        identifier = text(properties.get("DBInstanceIdentifier"), r"[A-Za-z][A-Za-z0-9-]*", "dependency-identifier-unsupported")
        database_name = text(properties.get("DBName"), r"[a-z][a-z0-9_]{0,62}", "dependency-name-unsupported")
        engine = text(properties.get("Engine"), r"postgres", "dependency-engine-unsupported")
        selected_major = text(properties.get("EngineVersion"), r"[1-9][0-9]", "dependency-engine-version-unsupported")
        require(postgresql is not None and int(selected_major) == postgresql["compatible_major"], "dependency-engine-major-incompatible")
        administrator = template.get("Outputs", {}).get("AdministratorCredentialsSecretArn", {}).get("Value")
        require(isinstance(administrator, dict) and set(administrator) == {"Ref"} and isinstance(administrator["Ref"], str), "dependency-administrator-output-unsupported")
        secret = template.get("Resources", {}).get(administrator["Ref"], {})
        require(secret.get("Type") == "AWS::SecretsManager::Secret", "dependency-administrator-secret-unsupported")
        administrator_name = text(secret.get("Properties", {}).get("Name"), r"[A-Za-z0-9/_+=.@-]{1,512}", "dependency-administrator-name-unsupported")
        resolved[key] = {"stack": supplier["stack"], "output": output, "identifier": identifier,
                         "database_name": database_name, "engine": engine, "engine_major": int(selected_major), "administrator_secret_name": administrator_name,
                         "endpoint_policies": endpoint_policies(template, account, region)}
    if postgresql is not None:
        references.add("scripts/04.deploy/shared/postgresql-version.py")
        for resource in own_template.get("Resources", {}).values():
            if resource.get("Type") == "AWS::RDS::DBInstance" and "DBSnapshotIdentifier" not in resource.get("Properties", {}):
                props = resource.get("Properties", {})
                require(props.get("Engine") == "postgres" and props.get("EngineVersion") == str(postgresql["compatible_major"]), "engine-major-incompatible")
    budget = budget_settings(root, target, foundation_source, references, capture)
    return {"target": target, "scope": scope, "account": account, "region": region, "profile": cli_profile, "budget": budget,
            "environment_lifecycle": asdict(lifecycle),
            "creation_parameters": {key: str(value) for key, value in creation_parameters.items()},
            "foundation_stack": foundation_stack, "foundation_template": base + "/" + foundation_template,
            "foundation_expected": foundation_expected,
            "foundation_endpoint_policies": endpoint_policies(foundation_document, account, region),
            "stack": selected["stack"], "template": base + "/" + selected["template"],
            "program": program, "package": image["id"], "candidate": candidate["id"],
            "repository": repository, "repository_uri": account + ".dkr.ecr." + region + ".amazonaws.com/" + repository,
            "dependencies": resolved, "postgresql": postgresql, "references": sorted(references)}


def instance_prerequisites(root, base, source, scopes, capture, references):
    """Capture direct foundation suppliers without resolving provider outputs."""
    profile = read_document(root, base + "/00-target/target-profile.yml", capture=capture)
    rows = profile["provider"]["foundation"].get("instance_prerequisites", {})
    require(isinstance(rows, dict), "session-prerequisite-invalid")
    foundation = read_document(root, source["foundation_template"], capture=capture)
    controls, _ = instance_controls(foundation, temporary=True)
    parameters = foundation.get("Parameters", {})
    components, destinations = [], set()
    for name, row in rows.items():
        text(name, r"[A-Za-z0-9][A-Za-z0-9_-]*", "session-prerequisite-invalid")
        require(name not in {"foundation", *scopes}, "session-prerequisite-identity-ambiguous")
        require(isinstance(row, dict) and {"stack", "template", "foundation_parameters"} <= set(row)
                and not set(row) - {"stack", "template", "foundation_parameters", "execution_parameters"}, "session-prerequisite-invalid")
        stack = text(row["stack"], r"[A-Za-z][A-Za-z0-9-]{0,127}", "session-prerequisite-invalid")
        template = row["template"]
        require(PATHS.safe_path(template) and all(part not in {"", ".", ".."} for part in template.split("/")), "path-invalid")
        reference = base + "/" + template
        producer = read_document(root, reference, references, capture)
        outputs = producer.get("Outputs", {})
        bindings = row["foundation_parameters"]
        require(isinstance(bindings, dict) and bool(bindings), "session-prerequisite-binding-invalid")
        require(isinstance(outputs, dict), "session-prerequisite-binding-invalid")
        for parameter, output in bindings.items():
            text(parameter, r"[A-Za-z][A-Za-z0-9]*", "session-prerequisite-binding-invalid")
            text(output, r"[A-Za-z][A-Za-z0-9]*", "session-prerequisite-binding-invalid")
            require(parameter not in {"ResourceNamePrefix", *controls} and isinstance(parameters.get(parameter), dict), "session-prerequisite-binding-invalid")
            require(parameter not in destinations, "session-prerequisite-destination-ambiguous")
            require(isinstance(outputs.get(output), dict) and outputs[output].get("Value") is not None, "session-prerequisite-binding-invalid")
            destinations.add(parameter)
        components.append((name, stack, reference, tuple(sorted(bindings.items()))))
    return tuple(sorted(components))


def session_control(root, base, profile, prefix, references=None, capture=None):
    selected = profile["provider"].get("session_control")
    require(isinstance(selected, dict) and set(selected) == {"schema", "stack_suffix", "template", "records_stack", "records_template", "record_key"}
            and selected["schema"] == "deploy/aws-session-control/v1", "session-control-invalid")
    text(prefix, r"s-[a-f0-9]{19}", "session-control-invalid")
    text(selected["stack_suffix"], r"[A-Za-z][A-Za-z0-9-]{0,63}", "session-control-invalid")
    text(selected["records_stack"], r"[A-Za-z][A-Za-z0-9-]{0,127}", "session-control-invalid")
    text(selected["record_key"], r"sessions/[a-z][a-z0-9-]*/current\.json", "session-control-invalid")
    result = {key: selected[key] for key in ("schema", "records_stack", "record_key")}
    result["stack"] = prefix + "-" + selected["stack_suffix"]
    require(not result["records_stack"].startswith(prefix + "-"), "session-control-invalid")
    for field in ("template", "records_template"):
        text(selected[field], r"30-provider-realization/aws/cloudformation/[A-Za-z0-9-]+\.yml", "session-control-invalid")
        result[field] = base + "/" + selected[field]
        read_document(root, result[field], references=references, capture=capture)
    return result


def execution_provenance(root, base, selections, prerequisites, stacks, stack_templates, stack_dependencies,
                         stack_order, stack_parameter_sources, capture):
    """Close source-owned producers without accepting live values or qualification."""
    require(PUBLICATION is not None, "session-publication-source-unavailable")
    source_bytes(root, PUBLICATION_REFERENCE, capture)
    profile = read_document(root, base + "/00-target/target-profile.yml", capture=capture)
    foundation = profile["provider"]["foundation"]
    bindings = {"foundation": foundation}
    bindings.update({name: foundation["instance_prerequisites"][name] for name, _, _, _ in prerequisites})
    for name in selections:
        document = read_document(root, base + "/20-scopes/" + name + "/10-workload-binding/workload-binding.yml", capture=capture)
        bindings[name] = document["proposed_provider_binding"]
    stack_by_component, template_by_stack = dict(stacks), dict(stack_templates)
    documents = {stack: CF.template(capture[reference].decode("utf-8")) for stack, reference in stack_templates}
    publications = {}
    pipelines = read_document(root, base + "/40-package-custody/github-actions/pipeline-index.yml", capture=capture)
    for name, source in selections.items():
        publications[name] = {key: source[key] for key in ("target", "account", "region", "candidate", "package", "program", "repository", "repository_uri")}
        publications[name].update(pipeline=bindings[name]["publication_pipeline"],
                                  repository_arn="arn:aws:ecr:" + source["region"] + ":" + source["account"] + ":repository/" + source["repository"])
        pipeline = one(pipelines.get("pipelines"), "id", bindings[name]["publication_pipeline"], "pipeline")
        acquisition = pipeline.get("custody_acquisition")
        require(isinstance(acquisition, dict) and {"source_repository", "artifact_prefix", "receipt_member"} <= set(acquisition)
                and set(acquisition) <= {"source_repository", "artifact_prefix", "receipt_member", "source_ref"},
                "session-publication-acquisition-invalid")
        repository = text(acquisition["source_repository"], r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}",
                          "session-publication-acquisition-invalid")
        prefix = text(acquisition["artifact_prefix"], r"[A-Za-z0-9][A-Za-z0-9_.-]{0,170}-", "session-publication-acquisition-invalid")
        member = text(acquisition["receipt_member"], r"[A-Za-z0-9][A-Za-z0-9_.-]{0,120}\.json", "session-publication-acquisition-invalid")
        workflow = text(pipeline.get("executable_workflow"), r"\.github/workflows/[A-Za-z0-9][A-Za-z0-9_.-]*\.ya?ml",
                        "session-publication-workflow-invalid")
        require(pipeline.get("trigger") == "workflow_dispatch", "session-publication-source-route-invalid")
        try:
            selected_policy = PUBLICATION.source_policy(pipeline)
        except PUBLICATION.PublicationFailure:
            raise InputFailure("session-publication-source-route-invalid") from None
        require(selected_policy["default"] == "refs/heads/main", "session-publication-source-route-invalid")
        raw = source_bytes(root, workflow, capture)
        require(0 < len(raw) <= 1048576, "session-publication-workflow-invalid")
        publications[name].update(source_repository=repository, workflow=workflow, source_ref=selected_policy["acquisition"],
                                  artifact_prefix=prefix, receipt_member=member, workflow_sha256=hashlib.sha256(raw).hexdigest())
    if "publication_pipeline" in foundation:
        pipeline = text(foundation["publication_pipeline"], r"[A-Za-z0-9][A-Za-z0-9_-]*", "pipeline-selection-invalid")
        candidates = [facts for facts in publications.values() if facts["pipeline"] == pipeline]
        require(bool(candidates) and all(facts == candidates[0] for facts in candidates), "session-publication-selection-invalid")
        publications["foundation"] = dict(candidates[0])
    dependencies = dict(stack_dependencies)

    def ancestors(stack):
        return {producer for direct in dependencies[stack] for producer in (direct, *ancestors(direct))}

    recipes, outputs, values, omissions = [], [], [], {}
    choices = {"vpc_cidr", "subnet_one_cidr", "subnet_two_cidr", "availability_zone_one", "availability_zone_two"}
    for component, binding in bindings.items():
        stack = stack_by_component[component]
        document = documents[stack]
        declarations = document.get("Parameters", {})
        controls, _ = instance_controls(document, temporary=True)
        controlled = {"ResourceNamePrefix", *controls}
        rows = binding.get("execution_parameters", {})
        require(isinstance(rows, dict), "session-execution-recipes-invalid")
        selected_omissions = {name for name, row in rows.items() if isinstance(row, dict) and row.get("kind") == "omit-if-unused"}
        defaults = {name for name, row in declarations.items() if isinstance(row, dict) and "Default" in row} - controlled - selected_omissions
        supplied = {parameter for consumer, parameter, _, _ in stack_parameter_sources if consumer == stack}
        require(not supplied.intersection(controlled | defaults) and not set(rows).intersection(controlled | defaults | supplied)
                and set(declarations) == controlled | defaults | supplied | set(rows), "session-execution-coverage-invalid")
        omitted = []
        for parameter, row in rows.items():
            text(parameter, r"[A-Za-z][A-Za-z0-9]{0,127}", "session-execution-recipe-invalid")
            require(isinstance(declarations[parameter], dict) and (parameter in selected_omissions or declarations[parameter].get("NoEcho", False) is False),
                    "session-execution-recipe-invalid")
            require(isinstance(row, dict) and all(isinstance(value, str) for value in row.values()), "session-execution-recipe-invalid")
            kind = row.get("kind")
            if kind == "choice":
                require(set(row) == {"kind", "contract", "field"} and row["contract"] == "private-network/v1"
                        and row["field"] in choices, "session-execution-recipe-invalid")
            elif kind == "package":
                require(set(row) == {"kind", "field"} and row["field"] in {"image_digest", "source_revision"}
                        and component in publications, "session-execution-recipe-invalid")
            elif kind == "source":
                if set(row) == {"kind", "field"}:
                    require(row["field"] in {"repository_arn", "repository_uri"} and component in publications,
                            "session-execution-recipe-invalid")
                    value = publications[component][row["field"]]
                else:
                    require(set(row) == {"kind", "field", "dependency"} and row["field"] == "database_name"
                            and component in selections, "session-execution-recipe-invalid")
                    text(row["dependency"], r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", "session-execution-recipe-invalid")
                    require(row["dependency"] in selections[component]["dependencies"], "session-execution-dependency-invalid")
                    value = selections[component]["dependencies"][row["dependency"]]["database_name"]
                values.append((stack, parameter, value))
            elif kind == "output":
                require(set(row) in ({"kind", "output", "component"}, {"kind", "output", "dependency"}), "session-execution-recipe-invalid")
                text(row["output"], r"[A-Za-z][A-Za-z0-9]{0,127}", "session-execution-recipe-invalid")
                if "component" in row:
                    producer_component = text(row["component"], r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", "session-execution-recipe-invalid")
                    require(producer_component in {"foundation", *(name for name, _, _, _ in prerequisites)}, "session-execution-dependency-invalid")
                else:
                    alias = text(row["dependency"], r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", "session-execution-recipe-invalid")
                    require(alias in binding.get("dependencies", {}), "session-execution-dependency-invalid")
                    producer_component = binding["dependencies"][alias]["scope"]
                producer = stack_by_component.get(producer_component)
                require(producer in ancestors(stack) and stack_order.index(producer) < stack_order.index(stack), "session-execution-dependency-invalid")
                output = documents[producer].get("Outputs", {}).get(row["output"])
                require(isinstance(output, dict) and output.get("Value") is not None, "session-execution-output-invalid")
                outputs.append((stack, parameter, producer, row["output"]))
            elif kind == "provider":
                require(set(row) == {"kind", "contract"} and row["contract"] == "aws-regional-s3-prefix-list/v1", "session-execution-recipe-invalid")
            elif kind == "omit-if-unused":
                require(set(row) == {"kind"}, "session-execution-recipe-invalid")
                omitted.append(parameter)
            else:
                raise InputFailure("session-execution-recipe-invalid")
            recipes.append((stack, parameter, tuple(sorted(row.items()))))
        omissions[template_by_stack[stack]] = tuple(sorted(omitted))
    return {"execution_parameters": tuple(sorted(recipes)), "execution_output_sources": tuple(sorted(outputs)),
            "execution_source_values": tuple(sorted(values)),
            "publication_selections": tuple(sorted((stack_by_component[name], tuple(sorted(facts.items()))) for name, facts in publications.items()))}, omissions


def _session_reader():
    try:
        return module("preparation_environment_session", ROOT / SESSION_REFERENCE)
    except Exception:
        raise InputFailure("session-source-unavailable") from None


def initial_task_selections(root, base, selections, order, capture, session_id):
    """Capture native finite workflows, without runtime ownership or admission."""
    compiler_reference = "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py"
    source_bytes(root, compiler_reference, capture)
    try:
        compiler = module("preparation_initial_task_selection", PATHS.within(root, compiler_reference))
    except Exception:
        raise InputFailure("session-task-source-unavailable") from None
    result = []
    for component in order:
        declaration = base + "/20-scopes/" + component + "/00-declaration/"
        contract = read_document(root, declaration + "declaration-contract.yml", capture=capture)
        route_reference = contract.get("acceptance", {}).get("route")
        require(isinstance(route_reference, str) and route_reference.startswith(declaration)
                and PATHS.safe_path(route_reference), "session-task-selection-invalid")
        route = read_document(root, route_reference, capture=capture)
        require(route.get("target") == contract.get("target") and route.get("scope") == component,
                "session-task-selection-invalid")
        binding = read_document(root, base + "/20-scopes/" + component + "/10-workload-binding/workload-binding.yml", capture=capture)
        try: sources = compiler.initial_task_sources(route)
        except ValueError: raise InputFailure("session-task-selection-invalid") from None
        for reference in sources: source_bytes(root, reference, capture)
        proof_label = "entity-smoke-" + session_id[:24] if route["initial_selection"]["kind"] == "entity-smoke-baseline/v1" else None
        try: steps = compiler.initial_tasks(route, binding, root=Path(root), proof_label=proof_label)
        except ValueError: raise InputFailure("session-task-selection-invalid") from None
        template = read_document(root, selections[component]["template"], capture=capture)
        field = "task_definition" if route["initial_selection"]["kind"] == "ordered-commands/v1" else "task_definition_ref"
        require(all(template.get("Resources", {}).get(row[field], {}).get("Type") == "AWS::ECS::TaskDefinition" for row in steps),
                "session-task-definition-invalid")
        result.append((component, {"kind": route["initial_selection"]["kind"], "route": route_reference,
                                  "proof_label": proof_label, "steps": steps, "sources": sources}))
    return tuple(deepcopy(result))


SESSION_TAG = "kanbien:session-id"
SESSION_TAGGED_TYPES = frozenset({
    "AWS::EC2::VPC", "AWS::EC2::Subnet", "AWS::EC2::RouteTable", "AWS::EC2::VPCEndpoint", "AWS::EC2::SecurityGroup",
    "AWS::ECS::Cluster", "AWS::ECS::Service", "AWS::ECS::TaskDefinition", "AWS::IAM::Role", "AWS::Logs::LogGroup",
    "AWS::RDS::DBInstance", "AWS::RDS::DBSubnetGroup", "AWS::SecretsManager::Secret",
    "AWS::ServiceDiscovery::PrivateDnsNamespace", "AWS::ServiceDiscovery::Service",
})


def session_fences(document, session_id):
    """Fence temporary resources and role permissions, never prove ownership."""
    text(session_id, r"[a-f0-9]{32}", "session-id-invalid")
    result = deepcopy(document)
    for resource in result["Resources"].values():
        if resource["Type"] not in SESSION_TAGGED_TYPES:
            continue
        properties = resource.setdefault("Properties", {})
        tags = properties.setdefault("Tags", [])
        require(isinstance(tags, list) and all(isinstance(row, dict) and set(row) == {"Key", "Value"}
                and isinstance(row["Key"], str) for row in tags)
                and len({row["Key"] for row in tags}) == len(tags), "session-tags-invalid")
        reserved = [row for row in tags if row["Key"] == SESSION_TAG]
        require(not reserved or reserved == [{"Key": SESSION_TAG, "Value": session_id}], "session-tag-conflict")
        if not reserved:
            tags.append({"Key": SESSION_TAG, "Value": session_id})
        if resource["Type"] == "AWS::IAM::Role":
            boundary = {"Fn::Sub": "arn:${AWS::Partition}:iam::${AWS::AccountId}:policy/s-"
                        + session_id[:19] + "-workloads"}
            require("PermissionsBoundary" not in properties or properties["PermissionsBoundary"] == boundary,
                    "session-boundary-conflict")
            properties["PermissionsBoundary"] = boundary
    return result


def load_session_plan(root, target, scope, document, now, approved_max_duration_seconds):
    """Capture a new unexpired session plan; never admit execution."""
    session = _session_reader()
    try:
        require(LIFECYCLE is not None, "source-unavailable")
        intent = session.read(document, target=target, scope=scope, now=now,
                              approved_max_duration_seconds=approved_max_duration_seconds)
    except session.SessionFailure as failure:
        raise InputFailure(failure.code) from None
    except (AttributeError, KeyError, TypeError, RecursionError):
        raise InputFailure("document-invalid") from None
    return _capture_session_plan(root, session, intent)


def revalidate_session_plan(root, retained_plan, now, approved_max_duration_seconds):
    """Recapture the complete existing plan without extending or admitting it."""
    session = _session_reader()
    try:
        require(LIFECYCLE is not None, "source-unavailable")
        require(isinstance(retained_plan, dict), "session-plan-invalid")
        expected = deepcopy(retained_plan)
        binding = expected["binding"]
        expected["binding"] = asdict(binding) if is_dataclass(binding) else binding
        original = expected["binding"]["intent"]
        document = {"schema": "deploy/environment-session-intent/v1",
                    **{key: original[key] for key in ("target", "scope", "session_id", "starts_at", "expires_at")},
                    "environment_lifecycle": {key: value for key, value in original["lifecycle"].items() if key != "explicit"}}
        intent = session.read_existing(document, target=original["target"], scope=original["scope"], now=now,
                                       approved_max_duration_seconds=approved_max_duration_seconds)
        fresh = _capture_session_plan(root, session, intent)
        observed = {**fresh, "binding": asdict(fresh["binding"])}

        def same_shape(left, right):
            if isinstance(left, dict):
                return isinstance(right, dict) and left.keys() == right.keys() and all(same_shape(value, right[key]) for key, value in left.items())
            if isinstance(left, (tuple, list)):
                return type(left) is type(right) and len(left) == len(right) and all(same_shape(a, b) for a, b in zip(left, right))
            return True

        require(same_shape(observed, expected) and CF.templates_equal(observed, expected), "session-plan-mismatch")
        return fresh
    except session.SessionFailure as failure:
        raise InputFailure(failure.code) from None
    except InputFailure:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError):
        raise InputFailure("session-plan-invalid") from None


def recover_session_plan(root, record_document, now, approved_max_duration_seconds):
    """Rebuild source from a positively checked record, without reopening it.

    The concrete caller supplies document and observed_at from one
    SessionRecords.observe_existing() result. Record ownership, schema, version
    and provider context stay with that owner; hashes alone cannot prove them.
    """
    session = _session_reader()
    try:
        require(LIFECYCLE is not None, "source-unavailable")
        require(isinstance(record_document, dict), "session-record-invalid")
        binding, base = deepcopy(record_document["binding"]), deepcopy(record_document["base"])
        fields = ("target", "scope", "session_id", "starts_at", "expires_at")
        require(isinstance(binding, dict) and set(binding) == {*fields, "source_inputs_sha256"}
                and isinstance(base, dict), "session-record-invalid")
        maximum = base["lifecycle_max_duration_seconds"]
        require(type(maximum) is int and maximum > 0
                and all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value)
                        for value in (binding["source_inputs_sha256"], base["source_plan_sha256"])), "session-record-invalid")
        document = {"schema": "deploy/environment-session-intent/v1", **{key: binding[key] for key in fields},
                    "environment_lifecycle": {"mode": "temporary", "data_retention": "discard", "max_duration_seconds": maximum}}
        intent = session.read_existing(document, target=binding["target"], scope=binding["scope"], now=now,
                                       approved_max_duration_seconds=approved_max_duration_seconds)
        fresh = _capture_session_plan(root, session, intent)
        # Match the immutable record's complete-plan canonical JSON, not only
        # source bytes: lifecycle policy and all projected maps are included.
        observed = {**fresh, "binding": asdict(fresh["binding"])}
        digest = hashlib.sha256(json.dumps(observed, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        require(fresh["binding"].source_inputs_sha256 == binding["source_inputs_sha256"]
                and digest == base["source_plan_sha256"], "session-plan-mismatch")
        require(base.get("execution_roles") == fresh["execution_roles"], "session-plan-mismatch")
        return fresh
    except session.SessionFailure as failure:
        raise InputFailure(failure.code) from None
    except InputFailure:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, RecursionError):
        raise InputFailure("session-record-invalid") from None


def _capture_session_plan(root, session, intent):
    """Render one captured graph for all readers, not an atomic source snapshot.

    Ordinary load() remains persistent-only. Source identities cannot establish
    package qualification, provider ownership or freshness after this returns.
    """
    try:
        target, scope = intent.target, intent.scope
        capture, selections, dependencies, order = {}, {}, {}, []
        references = {SESSION_REFERENCE, "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py"}
        base = "infra/04.deploy/03.product/targets/" + target

        def selected(name, ancestors=()):
            require(name not in ancestors, "session-dependency-cycle")
            if name in selections: return
            resolved = _load(root, target, name, capture)
            selections[name] = resolved
            references.update(resolved["references"])
            binding = read_document(root, base + "/20-scopes/" + name + "/10-workload-binding/workload-binding.yml", capture=capture)
            dependencies[name] = tuple(sorted({dependency["scope"] for dependency in binding["proposed_provider_binding"]["dependencies"].values()}))
            for dependency in dependencies[name]:
                selected(dependency, (*ancestors, name))
            order.append(name)

        selected(scope)
        source = selections[scope]
        prerequisites = instance_prerequisites(root, base, source, selections, capture, references)
        prefix = "s-" + intent.session_id[:19]
        require(prefix != target, "session-production-identity-conflict")
        profile = read_document(root, base + "/00-target/target-profile.yml", capture=capture)
        control = session_control(root, base, profile, prefix, references, capture)
        require(control["stack"] not in (source["stack"], source["foundation_stack"]), "session-control-invalid")
        role_source = profile["provider"].get("session_execution_roles")
        require(isinstance(role_source, dict) and set(role_source) == {"schema", "role_name_suffixes"}
                and role_source["schema"] == "deploy/aws-session-execution-roles/v1", "session-execution-roles-invalid")
        suffixes = role_source["role_name_suffixes"]
        require(isinstance(suffixes, dict) and set(suffixes) == {"creation", "cleanup"}
                and all(isinstance(value, str) for value in suffixes.values()), "session-execution-roles-invalid")
        role_names = {}
        for phase, suffix in suffixes.items():
            text(suffix, r"[A-Za-z0-9][A-Za-z0-9-]*", "session-execution-role-name-invalid")
            role_names[phase] = prefix + "-" + suffix
            require(len(role_names[phase]) <= 64, "session-execution-role-name-invalid")
        require(len({value.lower() for value in role_names.values()}) == 2, "session-execution-roles-ambiguous")
        execution_roles = {phase: "arn:aws:iam::" + source["account"] + ":role/" + name for phase, name in role_names.items()}

        def stack_name(value):
            require(value.startswith(target + "-"), "session-stack-source-unsupported")
            name = prefix + value[len(target):]
            text(name, r"[A-Za-z][A-Za-z0-9-]{0,127}", "session-stack-identity-invalid")
            return name

        stacks = [("foundation", stack_name(source["foundation_stack"]))]
        stack_templates = [(stacks[0][1], source["foundation_template"])]
        template_paths = {source["foundation_template"]}
        for name, stack, reference, _ in prerequisites:
            stacks.append((name, stack_name(stack)))
            stack_templates.append((stacks[-1][1], reference))
            template_paths.add(reference)
        for name, value in sorted(selections.items()):
            require(name != "foundation", "session-scope-unsupported")
            stacks.append((name, stack_name(value["stack"])))
            stack_templates.append((stacks[-1][1], value["template"]))
            template_paths.add(value["template"])
        require(len({value for _, value in stacks}) == len(stacks), "session-stack-identity-ambiguous")
        require(len({Path(reference).as_posix() for _, reference in stack_templates}) == len(stack_templates), "session-template-identity-ambiguous")
        stack_by_scope = dict(stacks)
        prerequisite_components = tuple(name for name, _, _, _ in prerequisites)
        prerequisite_stacks = tuple(stack_by_scope[name] for name in prerequisite_components)
        stack_parameter_sources = tuple(sorted((stacks[0][1], parameter, stack_by_scope[name], output)
                                              for name, _, _, bindings in prerequisites for parameter, output in bindings))
        stack_dependencies = ((stacks[0][1], prerequisite_stacks), *((stack, ()) for stack in prerequisite_stacks),
                              *((stack_by_scope[name], (stacks[0][1], *(stack_by_scope[dependency] for dependency in dependencies[name])))
                                for name in sorted(selections)))
        stack_order = (*prerequisite_stacks, stacks[0][1], *(stack_by_scope[name] for name in order))
        provenance, omissions = execution_provenance(root, base, selections, prerequisites, stacks, stack_templates,
                                                     stack_dependencies, stack_order, stack_parameter_sources, capture)
        task_selections = initial_task_selections(root, base, selections, order, capture, intent.session_id)
        references.update(capture)
        projected, creation_parameters, activation_templates, activation_parameters = [], [], [], []
        discard_templates, discard_parameters = [], []
        for reference in sorted(template_paths):
            try:
                original = CF.template(capture[reference].decode("utf-8"))
                controls, guards = instance_controls(original, temporary=True)
                parameters = {"ResourceNamePrefix": prefix, **controls}
                template = CF.project_parameters(original, list(parameters), parameters, condition_names=guards, omit_if_unused=omissions[reference])
                for rows, reason in ((stack_parameter_sources, "session-prerequisite-binding-invalid"),
                                     (provenance["execution_output_sources"], "session-execution-output-invalid")):
                    for _, _, producer, output in rows:
                        if dict(stack_templates)[producer] == reference:
                            require(output in template.get("Outputs", {}), reason)
                template = session_fences(discard_projection(original, template), intent.session_id)
                projected.append((reference, json.dumps(template, sort_keys=True, separators=(",", ":"), allow_nan=False)))
                creation_parameters.append((reference, tuple((key, str(value)) for key, value in sorted(parameters.items()))))
                discard_templates.append(projected[-1])
                discard_parameters.append(creation_parameters[-1])
                active = {name: row["active"] for name, row in original["Metadata"]["CreationControls"].items() if row["kind"] == "desired-count"}
                if active:
                    parameters = {**parameters, **active}
                    template = CF.project_parameters(original, list(parameters), parameters, condition_names=guards, omit_if_unused=omissions[reference])
                    template = session_fences(discard_projection(original, template), intent.session_id)
                    activation_templates.append((reference, json.dumps(template, sort_keys=True, separators=(",", ":"), allow_nan=False)))
                    activation_parameters.append((reference, tuple((key, str(value)) for key, value in sorted(parameters.items()))))
            except InputFailure:
                raise
            except ValueError:
                raise InputFailure("session-template-projection-invalid") from None
        inputs = tuple((reference, hashlib.sha256(raw).hexdigest()) for reference, raw in sorted(capture.items()))
        binding = session.bind_sources(intent, inputs, tuple(sorted(selections)))
        # Detect edits observed during planning. This is not a filesystem lock,
        # and cannot establish freshness after this read-only function returns.
        for reference, raw in capture.items():
            path = PATHS.within(root, reference)
            require(path is not None, "path-invalid")
            try: current = path.read_bytes()
            except OSError: raise InputFailure("source-unavailable") from None
            require(current == raw, "session-source-changed")
        return {"schema": "deploy/aws-session-source-plan/v1", "execution_status": "not-admitted",
                "binding": binding, "source_configuration": source, "resource_name_prefix": prefix, **provenance,
                "task_selections": task_selections, "execution_roles": execution_roles, "control": control,
                "stack_names": tuple(stacks), "projected_templates": tuple(projected),
                "stack_templates": tuple(stack_templates),
                "stack_dependencies": stack_dependencies, "stack_order": stack_order,
                "prerequisite_components": prerequisite_components, "stack_parameter_sources": stack_parameter_sources,
                "creation_parameters": tuple(creation_parameters),
                "activation_templates": tuple(activation_templates), "activation_parameters": tuple(activation_parameters),
                "discard_templates": tuple(discard_templates), "discard_parameters": tuple(discard_parameters),
                "references": sorted(references)}
    except session.SessionFailure as failure:
        raise InputFailure(failure.code) from None
    except InputFailure:
        raise
    except (AttributeError, KeyError, TypeError, RecursionError):
        raise InputFailure("document-invalid") from None
