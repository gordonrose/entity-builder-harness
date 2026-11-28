#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.task-execution
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Submit one reserved ECS task or observe its original operation without replaying uncertain mutations.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network]
#   used_by:
#   - id: deploy.library.entity-smoke.task-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-execution/implementation/task-control.py
#   - id: deploy.library.core-persistence.task-operations
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/task-operations.py
"""Private task mechanics. Callers own durable reservations, gates and proof.

No function grants provider authority, retries a mutation or decides whether a
subsequent operation is authorised. Replacement uses the supplied existing
reservation owner; RunTask requires a caller-reserved identity. Historical receipt
schemas and workload-specific identity/admission checks remain with callers.
"""
import json
import re
import time


class TaskFailure(Exception):
    def __init__(self, code, *, provider_code=None, rejected=False):
        super().__init__(code)
        self.code, self.provider_code, self.rejected = code, provider_code, rejected


class ProviderFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def runtime_binding(value, *, account, region):
    """Check copied runtime identity syntax, not provider ownership or admission.

    Workload bindings supply their checked account/region and source-derived
    identity. Keeping this context in their immutable request prevents recovery
    from silently selecting a different environment. Persistent defaults stay
    with those bindings; omission here is not a production fallback.
    """
    if not (isinstance(account, str) and re.fullmatch(r"[0-9]{12}", account)
            and isinstance(region, str) and len(region) <= 32
            and re.fullmatch(r"[a-z]{2}(?:-[a-z]+)+-[0-9]+", region)):
        raise TaskFailure("runtime-binding-invalid")
    patterns = {"session_id": r"[a-f0-9]{32}", "source_plan_sha256": r"[a-f0-9]{64}",
                "binding_sha256": r"sha256:[a-f0-9]{64}",
                "stack_id": rf"arn:aws:cloudformation:{re.escape(region)}:{account}:stack/[A-Za-z][A-Za-z0-9-]{{0,127}}/[A-Za-z0-9][A-Za-z0-9-]*",
                "cluster_arn": rf"arn:aws:ecs:{re.escape(region)}:{account}:cluster/[A-Za-z0-9_-]{{1,255}}",
                "family": r"[A-Za-z0-9_-]{1,255}", "container_name": r"[A-Za-z0-9_-]{1,255}",
                "log_group": r"[.\-_/#A-Za-z0-9]{1,512}", "log_stream_prefix": r"[.\-_/#A-Za-z0-9]{1,512}"}
    if not (isinstance(value, dict) and set(value) == {"schema", *patterns}
            and value.get("schema") == "deploy/aws-task-runtime/v1"
            and all(isinstance(value[key], str) and len(value[key]) <= 2048
                    and re.fullmatch(pattern, value[key]) for key, pattern in patterns.items())
            and len(value["log_stream_prefix"] + "/" + value["container_name"] + "/" + "0" * 32) <= 512
            and all("//" not in value[key] and not {".", ".."}.intersection(value[key].split("/"))
                    for key in ("log_group", "log_stream_prefix"))):
        raise TaskFailure("runtime-binding-invalid")
    return dict(value)


def cli_provider(aws):
    """Adapt the existing tuple-returning CLI boundary, not an AWS client."""
    def invoke(service, operation, **parameters):
        allowed = {
            "run-task": ("cluster", "taskDefinition", "launchType", "count", "startedBy", "clientToken", "networkConfiguration", "overrides"),
            "list-tasks": ("cluster", "family", "desiredStatus"),
            "describe-tasks": ("cluster", "tasks"),
            "stop-task": ("cluster", "task", "reason"),
        }
        if service != "ecs" or operation not in allowed or set(parameters) != set(allowed[operation]):
            raise ProviderFailure("ecs-task-provider-arguments-invalid")
        names = {"taskDefinition": "task-definition", "launchType": "launch-type", "startedBy": "started-by", "clientToken": "client-token", "networkConfiguration": "network-configuration", "desiredStatus": "desired-status"}
        arguments = [service, operation]
        for name in allowed[operation]:
            value = parameters[name]
            arguments.append("--" + names.get(name, name))
            if name == "tasks": arguments.extend(value)
            else: arguments.append(json.dumps(value) if isinstance(value, dict) else str(value))
        ok, value, code = aws(*arguments)
        if not ok: raise ProviderFailure(code)
        return value
    return invoke


def submit_task(provider, *, cluster, definition, operation_id, network, overrides,
                validate_task, before_submit=None, passthrough=()):
    """Exactly one submission after the caller has durably reserved this ID."""
    if before_submit is not None: before_submit()
    try:
        result = provider("ecs", "run-task", cluster=cluster, taskDefinition=definition,
                          launchType="FARGATE", count=1, startedBy=operation_id,
                          clientToken=operation_id, networkConfiguration=network, overrides=overrides)
    except passthrough: raise
    except Exception as failure:
        raise TaskFailure("submission-uncertain", provider_code=failure.code if isinstance(failure, ProviderFailure) else None) from None
    tasks = result.get("tasks") if isinstance(result, dict) else None
    if not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict) or result.get("failures"):
        rejected = isinstance(result, dict) and isinstance(result.get("failures"), list) and bool(result["failures"])
        raise TaskFailure("submission-uncertain", rejected=rejected)
    return validate_task(tasks[0])


def observed_tasks(provider, *, cluster, definition, operation_id=None,
                   sort_arns=False, maximum_list_size=None):
    """Observe a complete bounded family set; callers decide cardinality policy.

    An absent operation filter serves owned cleanup readers only. This function
    grants no task submission authority, including for an empty observation.
    """
    family = definition.rsplit("/", 1)[-1].split(":", 1)[0]
    arns = []
    for status in ("RUNNING", "STOPPED"):
        # ECS forbids combining startedBy with another ListTasks filter.
        try: result = provider("ecs", "list-tasks", cluster=cluster, family=family, desiredStatus=status)
        except Exception: raise TaskFailure("reconciliation-unavailable") from None
        batch = result.get("taskArns") if isinstance(result, dict) else None
        if not isinstance(batch, list) or result.get("nextToken") or any(not isinstance(arn, str) for arn in batch) or maximum_list_size is not None and len(batch) > maximum_list_size:
            raise TaskFailure("reconciliation-unavailable")
        arns.extend(batch)
    arns = list(dict.fromkeys(arns))
    if sort_arns: arns.sort()
    matching = []
    for offset in range(0, len(arns), 100):
        batch = arns[offset:offset + 100]
        try: result = provider("ecs", "describe-tasks", cluster=cluster, tasks=batch)
        except Exception: raise TaskFailure("reconciliation-unavailable") from None
        tasks = result.get("tasks") if isinstance(result, dict) else None
        if not isinstance(tasks, list) or len(tasks) != len(batch) or result.get("failures") or any(not isinstance(task, dict) or not isinstance(task.get("taskArn"), str) for task in tasks) or {task["taskArn"] for task in tasks} != set(batch):
            raise TaskFailure("reconciliation-unavailable")
        matching.extend(task for task in tasks if operation_id is None or task.get("startedBy") == operation_id)
    return matching


def reconcile_task(provider, *, cluster, definition, operation_id, validate_task, sort_arns=False):
    """Read-only lookup; unknown absence or duplicates never authorise RunTask."""
    matching = observed_tasks(provider, cluster=cluster, definition=definition,
        operation_id=operation_id, sort_arns=sort_arns)
    # Preserve exact filtering even for a malformed/None caller input; only the
    # discovery API treats an omitted filter as an all-operation observation.
    matching = [task for task in matching if task.get("startedBy") == operation_id]
    if len(matching) != 1: raise TaskFailure("reconciliation-unresolved")
    return validate_task(matching[0])


def describe_task(provider, *, cluster, arn, validate_task):
    try: result = provider("ecs", "describe-tasks", cluster=cluster, tasks=[arn])
    except Exception as failure:
        raise TaskFailure("observation-unavailable", provider_code=failure.code if isinstance(failure, ProviderFailure) else None) from None
    tasks = result.get("tasks") if isinstance(result, dict) else None
    if not isinstance(tasks, list) or len(tasks) != 1 or not isinstance(tasks[0], dict) or result.get("failures"):
        raise TaskFailure("observation-unavailable")
    task = validate_task(tasks[0])
    if task.get("taskArn") != arn: raise TaskFailure("observation-identity-mismatch")
    return task


def replace_task(provider, store, *, phase, request, cluster, original,
                 reason, precondition, observe, passthrough=()):
    """Stop the durably selected original once, then only observe successors.

    The binding validates/selects the original before entry. Completion, health,
    image and historical receipt policy stay in observe; a retained intent is
    never permission to stop the current service task instead.
    """
    reservation, fresh = store.reserve(phase, request)
    if fresh:
        precondition(reservation)
        try:
            provider("ecs", "stop-task", cluster=cluster, task=original,
                     reason=reason(reservation))
        except passthrough: raise
        except Exception as failure:
            raise TaskFailure("submission-uncertain", provider_code=failure.code if isinstance(failure, ProviderFailure) else None) from None
    return observe(reservation)


def observe_until_terminal(read_task, *, seconds, interval, initial=None, wait=True,
                           pending_states=None, monotonic=time.monotonic,
                           sleep=time.sleep, on_pending=None):
    """Bound observation only; terminal proof and remote duration stay caller-owned.

An initial RunTask observation may already be terminal. With no initial value,
one DescribeTasks observation is made even for a read-only, non-waiting resume.
Returning nonterminal never permits another submission.
"""
    deadline, current, observed = monotonic() + seconds, initial, False
    while True:
        if current is not None:
            if current.get("lastStatus") == "STOPPED": return current, True
            if not wait or pending_states is not None and current.get("lastStatus") not in pending_states:
                return current, False
            remaining = deadline - monotonic()
            if remaining <= 0: return current, False
            if observed:
                sleep(min(interval, remaining))
                if monotonic() >= deadline: return current, False
            if on_pending is not None: on_pending(current)
        current = read_task(current)
        observed = True
