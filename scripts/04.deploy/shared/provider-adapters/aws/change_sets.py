#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.change-set-execution
#   version: 4
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Share reserved CloudFormation submissions without owning workload approval or rollback policy.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.entity-smoke.deployment-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/implementation/deployment-control.py
#   - id: deploy.library.core-persistence.change-set-operations
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/change-set-operations.py
#   - id: deploy.command.kanbien-core-platform.transition-qualified-persistence-release.impl
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.py
"""Single-submission change-set protocol; callbacks retain workload proof rules.

The provider must already be gated by its owning command. A retained reservation
always selects observation, never another submission. No retries, wait loops,
resource inference, automatic approval or missing-object adoption live here.
"""


class ChangeSetFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def parameter_values(rows):
    """Read resolved provider parameters without silently losing invalid rows.

    Duplicate names are ambiguous even when their values match. Provider
    metadata such as ResolvedValue never replaces ParameterValue. The caller
    owns its safe rejection code; no raw value is included in a failure.
    """
    if not isinstance(rows, list):
        return None
    values = {}
    for row in rows:
        if not isinstance(row, dict):
            return None
        key, value = row.get("ParameterKey"), row.get("ParameterValue")
        if not isinstance(key, str) or not key or key in values or not isinstance(value, str):
            return None
        values[key] = value
    return values


def update_parameter_inputs(current, desired):
    """Preserve every unowned deployed value, including opaque NoEcho values.

    Omitting a parameter during UPDATE can select a template default rather
    than preserve the existing value. Only explicitly owned parameters may be
    replaced; new keys require a different, explicitly reviewed template change.
    """
    if not isinstance(current, dict) or not isinstance(desired, dict):
        return None
    if not all(isinstance(key, str) and key and isinstance(value, str)
               for mapping in (current, desired) for key, value in mapping.items()):
        return None
    if not set(desired) <= set(current):
        return None
    return ([{"ParameterKey": key, "UsePreviousValue": True} for key in sorted(set(current) - set(desired))] +
            [{"ParameterKey": key, "ParameterValue": desired[key]} for key in sorted(desired)])


def update_parameters_match(actual, desired, current):
    """Verify the complete resolved result, not merely the changed parameters."""
    if not all(isinstance(mapping, dict) for mapping in (actual, desired, current)):
        return False
    if not all(isinstance(key, str) and key and isinstance(value, str)
               for mapping in (actual, desired, current) for key, value in mapping.items()):
        return False
    return set(actual) == set(current) and set(desired) <= set(current) and actual == {**current, **desired}


def execution_events(response, operation_id, stack_id):
    """Select root-stack events belonging to the exact reserved submission."""
    if not isinstance(operation_id, str) or not operation_id or not isinstance(stack_id, str) or not stack_id or not isinstance(response, dict) or not isinstance(response.get("StackEvents"), list):
        return []
    return [event for event in response["StackEvents"] if isinstance(event, dict)
            and event.get("PhysicalResourceId") == stack_id and event.get("ClientRequestToken") == operation_id]


def retained_execution(store, *, preparation_phase, preparation_request,
                       execution_phase, execution_request, missing_preparation):
    """Select observation only from an intact, intent-matched reservation pair.

    Store readers own identity/integrity validation and propagate failures.
    A preparation alone does not establish submission. The caller supplies its
    existing orphan-record diagnostic; this read neither admits nor retries work.
    """
    prepared = store.read(preparation_phase, preparation_request)
    executed = store.read(execution_phase, execution_request)
    if executed is not None and prepared is None:
        raise missing_preparation()
    return executed


def _run(provider, store, *, phase, request, operation, token_field, arguments,
         precondition, observe, passthrough):
    # The durable operation owns the provider idempotency token. Workload policy
    # cannot silently replace it with a different or non-durable identity.
    if token_field in arguments or operation == "create-change-set" and "Description" in arguments:
        raise ChangeSetFailure("operation-token-conflict")
    reservation, fresh = store.reserve(phase, request)
    if fresh:
        precondition(reservation)
        try:
            identity = {token_field: reservation["operation_id"]}
            if operation == "create-change-set": identity["Description"] = reservation["operation_id"]
            provider("cloudformation", operation, **arguments, **identity)
        except passthrough: raise
        except Exception as failure:
            raise ChangeSetFailure(operation + "-submission-uncertain") from failure
    return observe(reservation)


def prepare(provider, store, *, phase, request, arguments, precondition, observe, passthrough=()):
    return _run(provider, store, phase=phase, request=request, operation="create-change-set",
                token_field="ClientToken", arguments=arguments, precondition=precondition,
                observe=observe, passthrough=passthrough)


def execute(provider, store, *, phase, request, arguments, precondition, observe, passthrough=()):
    return _run(provider, store, phase=phase, request=request, operation="execute-change-set",
                token_field="ClientRequestToken", arguments=arguments, precondition=precondition,
                observe=observe, passthrough=passthrough)
