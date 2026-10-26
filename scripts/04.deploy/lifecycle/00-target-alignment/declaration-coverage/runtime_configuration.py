#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.validation.runtime-configuration
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Compare workload requirements with normalized package and provider configuration facts.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.compiler.declaration-coverage
#     path: scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py
"""Compare workload requirements with normalized package/provider delivery facts."""
from __future__ import annotations
import importlib.util
import hashlib
import json
import re
from pathlib import Path
import yaml


def inspect(contract, binding, image, template_path, root):
    findings = []
    def gap(code, reference):
        item = {"code": code, "reference": reference}
        if item not in findings: findings.append(item)
    requirements = binding.get("runtime_requirements")
    if not isinstance(requirements, list) or not requirements:
        return [{"code": "runtime-requirements-missing"}]
    adapter_name = binding.get("proposed_provider_binding", {}).get("configuration_adapter")
    adapter = (root / adapter_name).resolve() if isinstance(adapter_name, str) else root
    adapter_root = (root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters").resolve()
    if not adapter.is_relative_to(adapter_root) or adapter.suffix != ".py" or not adapter.is_file():
        return [{"code": "runtime-configuration-adapter-unsupported"}]
    try:
        spec = importlib.util.spec_from_file_location("ecs_runtime_configuration", adapter)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        facts = module.normalize(template_path, binding)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, ImportError, yaml.YAMLError):
        return [{"code": "runtime-provider-configuration-invalid"}]
    workloads = {item.get("id"): item for item in binding.get("workloads", []) if isinstance(item, dict)}
    declared = set()
    defaults = image.get("runtime", {}).get("non_secret_defaults", {})
    accounted = set()
    try:
        catalog = yaml.safe_load((root / 'scripts/repo/check-selection/checks.yml').read_text())
    except (OSError, yaml.YAMLError): catalog = {}
    checks = catalog.get('checks', {}) if isinstance(catalog, dict) else {}
    scope_requirements = contract.get('change_impact', {}).get('requirements', [])
    selected_local = {proof for item in scope_requirements if isinstance(item, dict) for proof in (item.get('local_proofs') if isinstance(item.get('local_proofs'), list) else []) if isinstance(proof, str)}
    consumers = {consumer for item in scope_requirements if isinstance(item, dict) for consumer in (item.get('required_by') if isinstance(item.get('required_by'), list) else []) if isinstance(consumer, str)}
    route_path = contract.get('acceptance', {}).get('route')
    try: route = yaml.safe_load((root / route_path).read_text()) if isinstance(route_path, str) else {}
    except (OSError, yaml.YAMLError): route = {}
    route_commands = route.get('commands', {}) if isinstance(route, dict) else {}
    def supplied_by_command(producer, workload, name):
        if not isinstance(producer, dict) or set(producer) != {'source', 'command', 'proof'}: return False
        source, command_id, proof = producer.get('source'), producer.get('command'), producer.get('proof')
        if not isinstance(source, str) or not isinstance(command_id, str): return False
        selected = route_commands.get(command_id, {})
        if not isinstance(selected, dict): return False
        command = selected.get('argv')
        delivery = selected.get('runtime_input_contract')
        if not isinstance(delivery, dict) or delivery.get('workload') != workload or name not in delivery.get('names', []) or delivery.get('observation_required') is not True: return False
        if not isinstance(command, list) or len(command) < 2 or command[0] != 'bash' or not all(isinstance(arg, str) and arg for arg in command): return False
        source_path, command_path = root / source, root / command[1]
        if not source_path.resolve().is_relative_to(root.resolve()) or not command_path.resolve().is_relative_to(root.resolve()) or not source_path.is_file() or not command_path.is_file() or source_path.parent != command_path.parent: return False
        if command[1] not in consumers or not isinstance(proof, str) or proof not in selected_local: return False
        check = checks.get(proof, {})
        if not isinstance(check, dict) or check.get('stage') != 'local' or check.get('evidence_class') != 'local-runtime': return False
        argv = check.get('argv', [])
        if not isinstance(argv, list) or len(argv) < 2 or not (root / argv[1]).is_file(): return False
        return any(source == value or source.startswith(value.rstrip('/') + '/') for value in check.get('inputs', []) if isinstance(value, str))
    for requirement in requirements:
        if not isinstance(requirement, dict): gap("runtime-requirement-invalid", "shape"); continue
        identity = requirement.get("workload")
        if identity not in workloads or identity in declared:
            gap("runtime-workload-requirement-invalid", str(identity)); continue
        declared.add(identity)
        def names(value, empty=True):
            return isinstance(value, list) and (empty or bool(value)) and all(isinstance(item, str) and item.strip() and '\0' not in item for item in value) and len(value) == len(set(value))
        command = requirement.get('command')
        digest = requirement.get('command_sha256')
        inline = workloads[identity].get('execution', {}).get('kind') == 'inline-command'
        valid_command = isinstance(command, list) and bool(command) and all(isinstance(arg, str) and arg.strip() and '\0' not in arg for arg in command) and digest is None
        valid_digest = command is None and inline and isinstance(digest, str) and bool(re.fullmatch(r'[0-9a-f]{64}', digest))
        if not valid_command and not valid_digest:
            gap('runtime-workload-command-required', identity)
        if not names(requirement.get('secret_names')) or type(requirement.get('identity_required')) is not bool:
            gap('runtime-requirement-invalid', identity + ':secret-or-identity-shape'); continue
        capabilities = requirement.get('optional_capabilities', [])
        if not isinstance(capabilities, list) or any(not isinstance(item, dict) or set(item) != {'selector', 'required_names'} or not isinstance(item.get('selector'), dict) or set(item['selector']) != {'name', 'equals'} or not all(isinstance(value, str) and value.strip() for value in item['selector'].values()) or not names(item.get('required_names'), empty=False) for item in capabilities):
            gap('runtime-requirement-invalid', identity + ':optional-capability-shape'); continue
        runtime_inputs = requirement.get('runtime_inputs', {})
        if not isinstance(runtime_inputs, dict):
            gap('runtime-requirement-invalid', identity + ':runtime-input-shape'); continue
        for name, producer in runtime_inputs.items():
            if not isinstance(name, str) or not supplied_by_command(producer, identity, name):
                gap('runtime-input-producer-unbound', identity + ':' + str(name))
        declaration_id = requirement.get("declaration_workload")
        semantic_workloads = {item.get("id") for item in contract.get("health_recovery", {}).get("workloads", []) if isinstance(item, dict)}
        if declaration_id not in semantic_workloads:
            gap("runtime-workload-declaration-unmapped", identity)
        config = contract.get("configuration", {})
        identity_needed = any(declaration_id in item.get("authorised_workloads", []) for item in config.get("workload_identity_dependencies", []) if isinstance(item, dict))
        declared_secrets = {item.get("injection_name") for item in config.get("secret_dependencies", []) if isinstance(item, dict) and declaration_id in item.get("authorised_workloads", [])}
        required = requirement.get("required_names")
        if not isinstance(required, list) or not all(isinstance(name, str) and name for name in required):
            gap("runtime-required-names-invalid", identity); continue
        accounted.update(required)
        variants = facts.get(identity)
        if not variants: gap("runtime-workload-provider-missing", identity); continue
        for variant in variants:
            values = {**defaults, **variant["environment"], **variant["secrets"]}
            needed = set(required)
            for capability in requirement.get("optional_capabilities", []):
                selector = capability.get("selector", {})
                if values.get(selector.get("name")) == selector.get("equals"):
                    needed.update(capability.get("required_names", []))
            for name in needed:
                if name not in values or values[name] is None or values[name] == "":
                    # Task-input producers remain a separate command-boundary proof.
                    producer = requirement.get("runtime_inputs", {}).get(name)
                    if not supplied_by_command(producer, identity, name):
                        gap("runtime-required-configuration-missing", identity + ":" + name)
            secrets = set(requirement.get("secret_names", [])) | declared_secrets
            if not secrets.issubset(variant["secrets"]): gap("runtime-secret-injection-missing", identity)
            if secrets & set(variant["environment"]): gap("runtime-secret-delivered-as-environment", identity)
            if (identity_needed or requirement.get("identity_required") is True) and not variant["identity"]:
                gap("runtime-workload-identity-missing", identity)
            expected = requirement.get("command")
            command = variant["command"] if variant["command"] is not None else image.get("command")
            if expected is not None and command != expected: gap("runtime-workload-command-mismatch", identity)
            if valid_digest and hashlib.sha256(json.dumps(command, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest() != digest:
                gap('runtime-workload-command-mismatch', identity)
            if not variant["permissions_valid"]: gap("runtime-workload-permission-missing", identity)
    if declared != set(workloads): gap("runtime-workload-requirement-missing", ",".join(sorted(set(workloads) - declared)))
    configured = contract.get("configuration", {}).get("required_names", [])
    for name in set(configured) - accounted:
        gap("runtime-required-name-unmapped", name)
    return findings
