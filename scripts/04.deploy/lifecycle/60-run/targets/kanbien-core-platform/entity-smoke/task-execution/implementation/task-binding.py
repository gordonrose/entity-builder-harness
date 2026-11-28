#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.task-binding
#   version: 2
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Compare actual own immutable task revisions, IAM policies and private security-group rules with the reviewed source before task capability is supplied.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
"""Read-only own-template adapter, not a general CloudFormation interpreter.

The caller must first prove exact own-stack source/parameters/resource lineage.
No secret is fetched; provider dictionaries are ephemeral and never reports.
Successful comparison is not effective SQL access or execution approval.
"""
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("entity_smoke_binding_deployment", (Path(__file__).resolve().parents[2] / "controls-and-readiness/implementation/deployment-control.py"))
DEPLOY = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(DEPLOY)
ACCOUNT, REGION = DEPLOY.RESOURCE.ACCOUNT, DEPLOY.RESOURCE.REGION
WORKLOADS = {"server": "Server", "migration": "Migration", "administration": "Administration", "verifier": "Verifier", "database-proof": "DatabaseProof"}


_SHARED_SPEC = importlib.util.spec_from_file_location("checked_ecs_configuration", Path(__file__).resolve().parents[6] / "00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
SHARED = importlib.util.module_from_spec(_SHARED_SPEC); _SHARED_SPEC.loader.exec_module(SHARED)
BindingFailure, require, same = SHARED.BindingFailure, SHARED.require, SHARED.same
observation_scope, lower_keys, sorted_entries, policy = SHARED.observation_scope, SHARED.lower_keys, SHARED.sorted_entries, SHARED.policy


def resolve(value, parameters, resources, workload):
    return SHARED.runtime_resolve(value, parameters, resources, workload, account=ACCOUNT, region=REGION)


def selected_prefix(workload, prefix):
    if prefix is None:
        require(isinstance(workload, str) and workload in WORKLOADS, "task-binding-selection-invalid", "unselected", "selection")
        return WORKLOADS[workload]
    require(workload == "restore-reader" and prefix == "RestoreReader", "task-binding-selection-invalid", "unselected", "selection")
    return prefix


def expected_task(workload, parameters, resources, snapshot=None, *, prefix=None):
    logical = selected_prefix(workload, prefix) + "TaskDefinition"
    return SHARED.runtime_expected_task(logical, workload, parameters, resources, DEPLOY.source()[1] if snapshot is None else snapshot, account=ACCOUNT, region=REGION)


def task_definition(provider, workload, parameters, resources, snapshot=None, *, prefix=None):
    logical = selected_prefix(workload, prefix) + "TaskDefinition"
    return SHARED.runtime_task_definition(provider, logical, workload, parameters, resources, DEPLOY.source()[1] if snapshot is None else snapshot, account=ACCOUNT, region=REGION)


def role(provider, logical, parameters, resources, workload, snapshot=None):
    try:
        return SHARED.runtime_role(provider, logical, parameters, resources, workload, DEPLOY.source()[1] if snapshot is None else snapshot, account=ACCOUNT, region=REGION)
    except BindingFailure as failure:
        failure.item = "execution-role" if logical.endswith("ExecutionRole") else "task-role"
        raise


def permissions(rows, workload):
    return SHARED.permissions(rows, workload, account=ACCOUNT)


def network(provider, workload, parameters, resources, snapshot=None, *, prefix=None):
    logical = selected_prefix(workload, prefix) + "SecurityGroup"
    context = {"parameters": parameters, "resources": resources, "template": DEPLOY.source()[1] if snapshot is None else snapshot}
    destinations = {(parameters["EndpointSecurityGroupId"], 443): "delivery-ingress"}
    destinations[(resources["ServerSecurityGroup"]["physical_id"], 3000) if workload == "verifier" else (parameters["DatabaseSecurityGroupId"], 5432)] = "private-server-ingress" if workload == "verifier" else "database-ingress"
    return SHARED.runtime_network(provider, logical, workload, context, account=ACCOUNT, region=REGION, destination_items=destinations)


def runtime_source(view, workload, parameters, resources, snapshot):
    try:
        checked = SHARED.check_runtime_view(view, workload, account=ACCOUNT, region=REGION)
        require(checked["component"] == "entity-smoke" and checked["binding"]["target"] == "kanbien-core-platform"
                and checked["binding"]["scope"] == "entity-smoke" and same(snapshot, checked["template"])
                and same(parameters, checked["parameters"]) and same(resources, checked["resources"]),
                "runtime-binding-invalid", workload, "source")
        configuration = expected_task(workload, parameters, resources, snapshot)
        runtime = SHARED.task_runtime(checked, configuration, workload, account=ACCOUNT, region=REGION)
        return set(snapshot["Parameters"]), {name: row["Type"] for name, row in snapshot["Resources"].items()}, runtime
    except BindingFailure: raise
    except Exception: raise BindingFailure("runtime-binding-invalid", workload, "source") from None


def inspect(provider, workload, parameters, resources, snapshot=None, *, runtime_view=None):
    require(isinstance(workload, str) and workload in WORKLOADS, "task-binding-selection-invalid", "unselected", "selection")
    names, kinds, runtime = DEPLOY.PARAMETERS, DEPLOY.RESOURCE_TYPES, None
    if runtime_view is not None:
        names, kinds, runtime = runtime_source(runtime_view, workload, parameters, resources, snapshot)
    require(isinstance(parameters, dict) and set(parameters) == names and all(isinstance(value, str) and value and not any(character in value for character in "\n\r\0") for value in parameters.values()), "task-binding-parameters-not-confirmed", workload, "source")
    require(isinstance(resources, dict) and set(resources) == set(kinds) and all(isinstance(row, dict) and set(row) == {"type", "physical_id"} and row["type"] == kinds[name] and isinstance(row["physical_id"], str) and (runtime is None or bool(row["physical_id"])) for name, row in resources.items()), "task-binding-resources-not-confirmed", workload, "source")
    # A prepared operation may share its checked source view across its own
    # inspections. The public caller reads afresh at later preparation/guards;
    # provider observations and final source fingerprints are never cached.
    snapshot = DEPLOY.source()[1] if snapshot is None else snapshot
    definition, configuration = task_definition(provider, workload, parameters, resources, snapshot)
    prefix = WORKLOADS[workload]
    names = [prefix + "ExecutionRole"] + ([prefix + "TaskRole"] if workload in {"server", "migration", "database-proof"} else [])
    identities = {name: role(provider, name, parameters, resources, workload, snapshot) for name in names}
    group, network_digest = network(provider, workload, parameters, resources, snapshot)
    return {**({"runtime": runtime} if runtime is not None else {}), "definition": definition, "security_group": group, "subnets": parameters["PrivateSubnetIds"].split(","),
            "configuration_sha256": DEPLOY.fingerprint(configuration), "roles_sha256": DEPLOY.fingerprint(identities), "network_sha256": network_digest}
