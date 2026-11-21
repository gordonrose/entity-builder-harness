#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.preparation-inputs
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-16"
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
from pathlib import Path
import re


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


ROOT = Path(__file__).resolve().parents[6]
PATHS = module("preparation_declaration_paths", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py")
CF = module("preparation_cloudformation", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py")
CHECKS = module("preparation_foundation_checks", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py")

PG = module("preparation_postgresql_version", ROOT / "scripts/04.deploy/shared/postgresql-version.py")


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


def read_document(root, reference, references=None):
    path = PATHS.within(root, reference)
    require(path is not None, "path-invalid")
    try: raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError): raise InputFailure("source-unavailable") from None
    try: result = CF.template(raw)
    except ValueError: raise InputFailure("document-invalid") from None
    if references is not None: references.add(reference)
    return result


def budget_settings(root, target, foundation, references=None):
    """Read only budget declarations; provisioning has no image/package prerequisite."""
    text(target, r"[a-zA-Z0-9][a-zA-Z0-9_-]*", "target-invalid")
    declaration = read_document(root, "infra/04.deploy/03.product/targets/" + target + "/10-foundation/budget-control.yml", references)
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


def _load(root, target, scope):
    """Resolve one selected AWS scope. Returned references also feed impact analysis."""
    references = set()
    read = lambda reference: read_document(root, reference, references)

    name = r"[a-zA-Z0-9][a-zA-Z0-9_-]*"
    text(target, name, "target-invalid")
    text(scope, name, "scope-invalid")
    base = "infra/04.deploy/03.product/targets/" + target
    profile = read(base + "/00-target/target-profile.yml")
    require(profile.get("schema") == "deploy/target-profile/v1" and profile.get("id") == target, "target-mismatch")
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
    foundation_document = read(base + "/" + foundation_template)
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
        template = read(base + "/" + selected_provider["template"])
        return binding, selected_provider, template

    binding, selected, _ = binding_for(scope)
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
    pipeline_id = text(selected.get("publication_pipeline"), name, "pipeline-selection-invalid")
    pipeline = one(pipelines.get("pipelines"), "id", pipeline_id, "pipeline")
    scopes = pipeline.get("used_by_scopes")
    require(isinstance(scopes, list) and scope in scopes, "pipeline-scope-mismatch")
    require(pipeline.get("provider_region_alias") == "aws-" + region, "pipeline-region-mismatch")
    repository = text(pipeline.get("package_destination"), r"[a-z0-9]+(?:[._/-][a-z0-9]+)*", "repository-invalid")
    dependencies = selected.get("dependencies")
    require(isinstance(dependencies, dict), "dependencies-invalid")
    resolved = {}
    for key, dependency in dependencies.items():
        text(key, name, "dependency-invalid")
        require(isinstance(dependency, dict) and set(dependency) == {"scope", "output"}, "dependency-invalid")
        _, supplier, template = binding_for(dependency["scope"])
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
        own_template = read(base + "/" + selected["template"])
        for resource in own_template.get("Resources", {}).values():
            if resource.get("Type") == "AWS::RDS::DBInstance" and "DBSnapshotIdentifier" not in resource.get("Properties", {}):
                props = resource.get("Properties", {})
                require(props.get("Engine") == "postgres" and props.get("EngineVersion") == str(postgresql["compatible_major"]), "engine-major-incompatible")
    budget = budget_settings(root, target, foundation_document, references)
    return {"target": target, "scope": scope, "account": account, "region": region, "profile": cli_profile, "budget": budget,
            "foundation_stack": foundation_stack, "foundation_template": base + "/" + foundation_template,
            "foundation_expected": foundation_expected,
            "foundation_endpoint_policies": endpoint_policies(foundation_document, account, region),
            "stack": selected["stack"], "template": base + "/" + selected["template"],
            "program": program, "package": image["id"], "candidate": candidate["id"],
            "repository": repository, "repository_uri": account + ".dkr.ecr." + region + ".amazonaws.com/" + repository,
            "dependencies": resolved, "postgresql": postgresql, "references": sorted(references)}
