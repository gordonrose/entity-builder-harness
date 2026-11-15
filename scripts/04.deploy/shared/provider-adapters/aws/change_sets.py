#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.change-set-execution
#   version: 3
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Share reserved CloudFormation submissions and explicit-reconciliation UPDATE sequencing without owning workload approval or rollback policy.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.entity-smoke.deployment-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/deployment-control.py
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


def reviewed_update(*, inspect, create, review, admit, execute, observe, failure,
                    reconcile_existing=lambda _change: False):
    """Share the legacy explicit-reconciliation UPDATE sequence.

    The caller has already checked authority, custody and workload alignment.
    Callbacks retain exact resource/parameter guards and bounded review timing.
    This method performs each effect at most once per invocation, not once per
    release: interrupted callers MUST use their existing read-only reconcile
    mode. Unlike prepare/execute above, it does not claim durable replay safety
    or infer a new approved operation from an existing one.
    """
    ok, existing, code = inspect()
    if ok and reconcile_existing(existing):
        return observe()
    created = not ok
    if created:
        if code != "aws-resource-missing":
            return failure("blocked", code)
        ok, _response, code = create()
        if not ok:
            return failure("uncertain", code)
    change, _code = review(existing, created)
    if change is None or change.get("ExecutionStatus") != "AVAILABLE":
        return observe()
    rejection = admit(change)
    if rejection is not None:
        return failure("blocked", rejection)
    ok, _response, code = execute()
    if not ok:
        return failure("uncertain", code)
    return observe()
