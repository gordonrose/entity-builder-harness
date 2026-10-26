#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.ecs-runtime-configuration
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Normalize ECS template configuration alternatives for provider-neutral workload requirement validation.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.validation.runtime-configuration
#     path: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/runtime_configuration.py
"""Normalize ECS CloudFormation alternatives without contacting AWS or resolving secrets."""
from itertools import product
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
