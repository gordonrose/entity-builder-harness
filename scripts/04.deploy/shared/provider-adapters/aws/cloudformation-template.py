#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.cloudformation-template
#   version: 4
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [security, sre]
#   kind: script
#   purpose: Normalize CloudFormation source and project explicitly selected non-secret String or integer Number parameters and literal equality guards without provider resolution.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.execute-runtime-change-set
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py
#   - id: deploy.adapter.platform-shell-release-control
#     path: scripts/04.deploy/legacy/kanbien-staging/reconcile-platform-shell-staging/release_control.py
"""AWS source normalization only; deployment qualification remains target-owned."""
import copy
import json
import re
import yaml


class Loader(getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
    pass


def mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError("cloudformation-template-mapping-invalid")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


def intrinsic(loader, tag, node):
    value = loader.construct_scalar(node) if isinstance(node, yaml.ScalarNode) else loader.construct_sequence(node) if isinstance(node, yaml.SequenceNode) else mapping(loader, node)
    if tag == "GetAtt" and isinstance(value, str):
        value = value.split(".", 1)
    return {tag if tag == "Ref" else "Fn::" + tag: value}


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
Loader.add_multi_constructor("!", intrinsic)


def template(raw):
    try:
        value = yaml.load(raw, Loader=Loader) if isinstance(raw, str) else raw
        if not isinstance(value, dict) or not value:
            raise ValueError("cloudformation-template-body-invalid")
        # Reject recursive aliases, non-JSON values and non-finite numbers.
        json.dumps(value, sort_keys=True, allow_nan=False)
        return value
    except (yaml.YAMLError, TypeError, ValueError, RecursionError) as error:
        raise ValueError("cloudformation-template-body-invalid") from error


def templates_equal(left, right):
    # JSON canonicalization preserves scalar types (Python considers True == 1).
    return json.dumps(template(left), sort_keys=True, allow_nan=False) == json.dumps(template(right), sort_keys=True, allow_nan=False)


def project_string_parameters(raw, names, overrides=None):
    """Copy source, projecting selected non-secret Strings, never live resources.

    Names are a nonempty list/tuple; overrides select only those declarations.
    Unselected expressions stay symbolic. Consumers requiring a literal must
    still reject unresolved expressions; this is not a template interpreter.
    """
    return _project_parameters(raw, names, overrides, False, ())


def project_parameters(raw, names, overrides=None, *, condition_names=()):
    """Project selected Strings/integer Numbers and named literal equality guards.

    Conditions only gate complete resources/outputs. Fn::If, condition graphs,
    unresolved selected conditions and references to removed resources reject;
    unselected conditions and provider expressions remain symbolic.
    """
    return _project_parameters(raw, names, overrides, True, condition_names)


def _project_parameters(raw, names, overrides, allow_number, condition_names):
    try:
        document = copy.deepcopy(template(raw))
    except (ValueError, TypeError, RecursionError):
        raise ValueError("cloudformation-template-body-invalid") from None
    declarations = document.get("Parameters")
    overrides = {} if overrides is None else overrides
    if (not isinstance(declarations, dict) or not isinstance(names, (list, tuple)) or not names
            or not all(isinstance(name, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) for name in names)
            or len(set(names)) != len(names) or not set(names) <= set(declarations)
            or not isinstance(overrides, dict) or not set(overrides) <= set(names)):
        raise ValueError("cloudformation-parameter-selection-invalid")

    def require(valid, code="cloudformation-string-parameter-invalid"):
        if not valid:
            raise ValueError(code)

    values = {}
    attributes = {"Type", "Default", "Description", "ConstraintDescription", "AllowedPattern",
                  "AllowedValues", "MinLength", "MaxLength", "NoEcho"}
    for name in names:
        declaration = declarations[name]
        if allow_number and isinstance(declaration, dict) and declaration.get("Type") == "Number":
            code = "cloudformation-number-parameter-invalid"
            require(not set(declaration) - {"Type", "Default", "Description", "ConstraintDescription", "AllowedValues", "MinValue", "MaxValue", "NoEcho"}
                    and declaration.get("NoEcho", False) is False, code)
            require(all(key not in declaration or isinstance(declaration[key], str) for key in ("Description", "ConstraintDescription")), code)
            require(all(key not in declaration or type(declaration[key]) is int for key in ("MinValue", "MaxValue")), code)
            minimum, maximum = declaration.get("MinValue"), declaration.get("MaxValue")
            require(minimum is None or maximum is None or minimum <= maximum, code)
            allowed = declaration.get("AllowedValues")
            require("AllowedValues" not in declaration or isinstance(allowed, list) and bool(allowed)
                    and all(type(item) is int for item in allowed), code)
            require(name in overrides or "Default" in declaration, code)
            selected = overrides[name] if name in overrides else declaration["Default"]
            for value in ([declaration["Default"]] if "Default" in declaration else []) + [selected]:
                require(type(value) is int and (minimum is None or value >= minimum)
                        and (maximum is None or value <= maximum) and (allowed is None or value in allowed), code)
            values[name] = selected
            continue
        require(isinstance(declaration, dict) and not set(declaration) - attributes
                and declaration.get("Type") == "String" and declaration.get("NoEcho", False) is False)
        for key in ("Description", "ConstraintDescription", "AllowedPattern"):
            require(key not in declaration or isinstance(declaration[key], str))
        for key in ("MinLength", "MaxLength"):
            require(key not in declaration or type(declaration[key]) is int and declaration[key] >= 0)
        minimum, maximum = declaration.get("MinLength", 0), declaration.get("MaxLength")
        require(maximum is None or minimum <= maximum)
        allowed = declaration.get("AllowedValues")
        require("AllowedValues" not in declaration or isinstance(allowed, list) and bool(allowed)
                and all(isinstance(item, str) for item in allowed))
        try:
            pattern = re.compile(declaration["AllowedPattern"]) if "AllowedPattern" in declaration else None
        except (re.error, OverflowError, RecursionError):
            raise ValueError("cloudformation-string-parameter-invalid") from None
        require(name in overrides or "Default" in declaration)
        selected = overrides[name] if name in overrides else declaration["Default"]
        for value in ([declaration["Default"]] if "Default" in declaration else []) + [selected]:
            require(isinstance(value, str) and "${" not in value and "{{resolve:" not in value)
            require(len(value) >= minimum and (maximum is None or len(value) <= maximum)
                    and (allowed is None or value in allowed)
                    and (pattern is None or pattern.fullmatch(value) is not None))
        values[name] = selected

    tokens = re.compile(r"\$\{([^}]+)\}")

    def selected_use(value):
        if isinstance(value, str):
            return any(match in values for match in tokens.findall(value))
        if isinstance(value, list):
            return any(selected_use(item) for item in value)
        if isinstance(value, dict):
            return (isinstance(value.get("Ref"), str) and value["Ref"] in values
                    or any(selected_use(item) for item in value.values()))
        return False

    def project(value):
        if isinstance(value, list):
            return [project(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "Ref" in value and isinstance(value["Ref"], str) and value["Ref"] in values:
            if set(value) != {"Ref"}:
                raise ValueError("cloudformation-parameter-substitution-unsupported")
            return values[value["Ref"]]
        if "Fn::Sub" in value:
            substitution = value["Fn::Sub"]
            if not selected_use(substitution):
                return value
            if set(value) != {"Fn::Sub"} or not isinstance(substitution, str) or "{{resolve:" in substitution:
                raise ValueError("cloudformation-parameter-substitution-unsupported")
            replaced = sum(match in values for match in tokens.findall(substitution))
            result = tokens.sub(lambda match: str(values[match[1]]) if match[1] in values else match[0], substitution)
            # Also reject new openers assembled across replacement boundaries.
            if result.count("${") != substitution.count("${") - replaced or "{{resolve:" in result:
                raise ValueError("cloudformation-parameter-substitution-unsupported")
            return {"Fn::Sub": result} if "${" in result else result
        return {key: project(item) for key, item in value.items()}

    try:
        projected = project(document)
        return _project_conditions(projected, condition_names)
    except RecursionError:
        raise ValueError("cloudformation-parameter-substitution-unsupported") from None


def _project_conditions(document, names):
    """Resolve only caller-selected equality guards; never evaluate a CF program."""
    def require(value, code="cloudformation-condition-unsupported"):
        if not value: raise ValueError(code)
    require(isinstance(names, (list, tuple)) and all(isinstance(name, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) for name in names)
            and len(set(names)) == len(names), "cloudformation-condition-selection-invalid")
    if not names: return document
    conditions = document.get("Conditions")
    require(isinstance(conditions, dict) and set(names) <= set(conditions), "cloudformation-condition-selection-invalid")
    decisions = {}
    for name in names:
        expression = conditions[name]
        require(isinstance(expression, dict) and set(expression) == {"Fn::Equals"})
        values = expression["Fn::Equals"]
        require(isinstance(values, list) and len(values) == 2 and all(type(value) in (str, int) for value in values)
                and type(values[0]) is type(values[1])
                and all(not isinstance(value, str) or "${" not in value and "{{resolve:" not in value for value in values))
        decisions[name] = values[0] == values[1]
        del conditions[name]
    removed = set()
    for section in ("Resources", "Outputs"):
        rows = document.get(section, {})
        require(isinstance(rows, dict))
        for name, row in list(rows.items()):
            require(isinstance(row, dict))
            condition = row.get("Condition")
            require("Condition" not in row or isinstance(condition, str))
            if condition not in decisions: continue
            if not decisions[condition]:
                del rows[name]
                if section == "Resources": removed.add(name)
            else: del row["Condition"]

    def selected_condition(value):
        if isinstance(value, str): return value in decisions
        if isinstance(value, list): return any(selected_condition(item) for item in value)
        if isinstance(value, dict): return any(selected_condition(item) for item in value.values())
        return False

    def inspect(value):
        if isinstance(value, list):
            for item in value: inspect(item)
        elif isinstance(value, dict):
            condition = value.get("Condition")
            require(not selected_condition(condition))
            branch = value.get("Fn::If")
            require(not selected_condition(branch))
            reference = value.get("Ref")
            require(not isinstance(reference, str) or reference not in removed, "cloudformation-removed-resource-reference")
            attribute = value.get("Fn::GetAtt")
            resource = attribute[0] if isinstance(attribute, list) and attribute else attribute.split(".", 1)[0] if isinstance(attribute, str) else None
            require(not isinstance(resource, str) or resource not in removed, "cloudformation-removed-resource-reference")
            dependencies = value.get("DependsOn", [])
            if isinstance(dependencies, str): dependencies = [dependencies]
            require(not isinstance(dependencies, list) or not any(isinstance(item, str) and item in removed for item in dependencies), "cloudformation-removed-resource-reference")
            for item in value.values(): inspect(item)
        elif isinstance(value, str):
            require(not any(token.split(".", 1)[0] in removed for token in re.findall(r"\$\{([^}]+)\}", value)), "cloudformation-removed-resource-reference")
    inspect(document)
    return document
