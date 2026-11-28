#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.environment-sessions
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Coordinate captured temporary deployment, native tests and reverse cleanup through existing operation owners.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.disposable-test-environments
#     path: docs/04.deploy/plans/disposable-test-environments.md
"""One resumable pass; durable intent and single submission stay with senders.

The concrete assembly supplies qualified operations and native task consumers.
A pending pass leaves admission open; terminal functionality closes it and starts
cleanup. An independent worker invokes this same cleanup path after expiry.
"""
from copy import deepcopy
import argparse
import importlib.util
import json
import os
from pathlib import Path
import time


class ControllerFailure(Exception):
    def __init__(self, condition):
        self.code = "environment-session-controller-" + condition
        super().__init__(self.code)


def require(condition, reason):
    if not condition:
        raise ControllerFailure(reason)


class Controller:
    def __init__(self, assembly):
        self.assembly = assembly
        self.operations = assembly.operations
        self.plan = deepcopy(assembly.plan)
        self.order = tuple(self.plan["stack_order"])
        self.templates = dict(self.plan["stack_templates"])
        self.components = dict(self.plan["stack_names"])
        require(bool(self.order) and len(set(self.order)) == len(self.order)
                and set(self.order) == set(self.templates) == set(self.components.values()),
                "stack-order-invalid")
        self.tasks = tuple(self.plan["task_selections"])
        require(len(dict(self.tasks)) == len(self.tasks)
                and set(dict(self.tasks)) <= set(self.components), "task-selection-invalid")

    def _phase(self, kind, stack):
        observation = self.operations.reconcile_operation(kind=kind, stack=stack, phase="execute")
        if observation["status"] != "unreserved":
            return observation
        if kind == "creation":
            setup = self.assembly.prepare_stack(stack)
            if setup["status"] != "ready":
                return setup
        prepared = self.operations.reconcile_operation(kind=kind, stack=stack, phase="prepare")
        if prepared["status"] == "unreserved":
            self.operations.prepare(kind, stack=stack, template_reference=self.templates[stack])
            prepared = self.operations.reconcile_operation(kind=kind, stack=stack, phase="prepare")
        if prepared["status"] != "ready":
            return prepared
        self.operations.execute(kind, stack=stack, template_reference=self.templates[stack])
        return self.operations.reconcile_operation(kind=kind, stack=stack, phase="execute")

    def _failure_code(self, failure):
        return failure.code if isinstance(failure, ControllerFailure) else self.assembly.failure_code(failure)

    def _task_phase(self, component, phase):
        selected = dict(self.tasks).get(component)
        if selected is None:
            return {"status": "succeeded"}
        for row in selected["steps"]:
            placement = row["phase"] if selected["kind"] == "ordered-commands/v1" else row["activation"]
            if placement != phase:
                continue
            result = self.assembly.run_task(component, deepcopy(row))
            require(isinstance(result, dict) and result.get("status") in
                    {"succeeded", "failed", "pending", "unknown", "blocked", "skipped"}, "task-result-invalid")
            if result["status"] == "skipped":
                require(selected["kind"] == "entity-smoke-baseline/v1"
                        and row["condition"] != "always", "required-task-skipped")
            elif result["status"] != "succeeded":
                return result
        return {"status": "succeeded"}

    def _run(self):
        for stack in self.order:
            result = self._phase("creation", stack)
            if result["status"] != "succeeded":
                return result
        by_stack = {stack: component for component, stack in self.components.items()}
        for stack in self.order:
            component = by_stack[stack]
            result = self._task_phase(component, "before-activation")
            if result["status"] != "succeeded":
                return result
            if self.templates[stack] in dict(self.plan["activation_templates"]):
                result = self._phase("activation", stack)
                if result["status"] != "succeeded":
                    return result
            result = self._task_phase(component, "after-activation")
            if result["status"] != "succeeded":
                return result
        return {"status": "succeeded", "reason": "functionality-passed"}

    def _cleanup(self):
        self.operations.seal()
        delegated = self.assembly.handoff_cleanup()
        if delegated is not None:
            require(isinstance(delegated, dict) and delegated.get("status") in
                    {"completed", "pending", "unknown", "blocked"}, "cleanup-result-invalid")
            return delegated
        tasks = self.assembly.reconcile_tasks()
        require(isinstance(tasks, dict) and tasks.get("status") in
                {"ready", "pending", "unknown", "blocked"}, "task-reconciliation-invalid")
        if tasks["status"] != "ready":
            return tasks
        stops = self.operations.reconcile_stops()
        require(isinstance(stops, list) and len(stops) == len(self.order)
                and {row["stack"] for row in stops} == set(self.order), "stop-observation-invalid")
        blockers = []
        for row in stops:
            status = row["status"]
            if status == "stop-required":
                result = self._phase("prepare-discard", row["stack"])
                if result["status"] != "succeeded":
                    blockers.append(result)
            elif status not in {"stopped", "never-allocated", "not-started", "delete-observation-only"}:
                blockers.append(row)
        if blockers:
            return {"status": "pending" if all(row["status"] == "pending" for row in blockers) else "blocked",
                    "reason": "stops-unresolved", "operations": blockers}
        document = self.assembly.records.observe_existing()["document"]
        for stack in reversed(self.order):
            preparation = "creation:" + stack + ":prepare"
            if preparation not in document["operations"]:
                continue
            if (document["operation_outcomes"].get(preparation, {}).get("status") == "not-submitted"
                    and "creation:" + stack + ":execute" not in document["operations"]):
                continue
            stack_id = document["incarnations"].get(stack)
            require(stack_id is not None, "owned-stack-unconfirmed")
            self.operations.retain_physical_observation(stack=stack, stack_id=stack_id)
            result = self.operations.reconcile_operation(kind="delete", stack=stack, phase="delete")
            if result["status"] == "unreserved":
                self.operations.delete(stack=stack, stack_id=stack_id)
                result = self.operations.reconcile_operation(kind="delete", stack=stack, phase="delete")
            if result["status"] != "succeeded":
                return result
        result = self.assembly.complete_cleanup()
        require(isinstance(result, dict) and result.get("status") in
                {"completed", "pending", "unknown", "blocked"}, "cleanup-result-invalid")
        return result

    def advance(self, operation="run"):
        require(operation in {"run", "cleanup"}, "operation-unsupported")
        functional = None
        try:
            document = self.assembly.initialize() if operation == "run" else self.assembly.records.observe_existing()["document"]
            functional = self.assembly.functional_result()
            if operation == "run" and document["state"] == "open" and functional is None:
                outcome = self._run()
                if outcome["status"] in {"pending", "unknown"}:
                    return {"functional": outcome, "cleanup": {"status": "not-started"}}
                functional = {"status": "succeeded" if outcome["status"] == "succeeded" else "failed"}
                if functional["status"] == "failed":
                    functional["reason"] = outcome.get("reason") or next(iter(outcome.get("reasons", ())), "functionality-failed")
                self.assembly.retain_functional(functional)
            elif functional is None:
                functional = {"status": "interrupted"}
                self.assembly.retain_functional(functional)
        except Exception as failure:
            reason = self._failure_code(failure)
            functional = functional or {"status": "failed"}
            functional = {**functional, "reason": reason}
            try:
                self.assembly.retain_functional(functional)
            except Exception:
                pass
        # Adopt a report whose status write was interrupted before cleanup.
        try:
            self.assembly.retain_functional(functional)
        except Exception:
            pass
        try:
            cleanup = self._cleanup()
        except Exception as failure:
            cleanup = {"status": "blocked", "reason": self._failure_code(failure)}
        try:
            self.assembly.retain_cleanup(cleanup)
        except Exception as failure:
            cleanup = {**cleanup, "report_reason": self._failure_code(failure)}
        return {"functional": functional, "cleanup": cleanup}


def command_assembly(document, operation):
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("environment_session_live_assembly", here / "aws.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    factory = helper.new_assembly if operation == "run" else helper.existing_assembly
    return factory(root=here.parents[5], document=document, environment=dict(os.environ))


def start_setup(document):
    here = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("environment_session_startup", here / "setup.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper.Startup(root=here.parents[5], document=document, environment=dict(os.environ))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a qualified temporary session or request/resume its fixed cleanup worker.")
    parser.add_argument("operation", choices=("start", "run", "cleanup"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--max-seconds", type=int)
    args = parser.parse_args(argv)
    # SSO role chaining gives the foreground one hour; leave five minutes for
    # retaining its result and requesting cleanup. Independent expiry is two hours.
    maximum = 540 if args.operation == "cleanup" else 3300
    if args.max_seconds is None:
        args.max_seconds = maximum
    if not 1 <= args.max_seconds <= maximum:
        parser.error("--max-seconds must be between 1 and " + str(maximum))
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError()
            value[key] = item
        return value
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(131073)
        if len(raw) > 131072:
            raise ValueError()
        document = json.loads(raw, object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        print(json.dumps({"schema": "deploy/environment-session-command-result/v1", "status": "blocked", "reason": "environment-session-command-input-invalid"}))
        return 1
    deadline = time.monotonic() + args.max_seconds
    try:
        operation = "run" if args.operation == "start" else args.operation
        if args.operation == "start":
            setup = start_setup(document)
            while True:
                assembly = setup.advance()
                if assembly is not None:
                    break
                if time.monotonic() >= deadline:
                    print(json.dumps({"schema": "deploy/environment-session-command-result/v1",
                        "status": "pending", "stage": "setup", "reason": "environment-session-setup-pending"}))
                    return 2
                time.sleep(min(5, max(0, deadline - time.monotonic())))
        else:
            assembly = command_assembly(document, operation)
        controller = Controller(assembly)
        while True:
            result = controller.advance(operation)
            pending = result["cleanup"]["status"] in ("pending", "unknown", "not-started")
            if not pending or time.monotonic() >= deadline:
                if operation == "run" and result["cleanup"]["status"] == "not-started":
                    result = controller.advance("cleanup")
                break
            time.sleep(min(5, max(0, deadline - time.monotonic())))
        if args.operation == "start" and result["cleanup"]["status"] == "completed":
            result["controller_cleanup"] = {"status": "pending"}
            while True:
                try:
                    retired = setup.finish()
                except Exception:
                    result["controller_cleanup"] = {"status": "blocked",
                        "reason": "environment-session-controller-retirement-unconfirmed"}
                    break
                if retired:
                    result["controller_cleanup"] = {"status": "completed"}
                    break
                if time.monotonic() >= deadline:
                    break
                time.sleep(min(5, max(0, deadline - time.monotonic())))
    except Exception:
        # Construction may reject unknown native state before any record exists.
        # Never print provider stderr, input content or arbitrary exception text.
        print(json.dumps({"schema": "deploy/environment-session-command-result/v1", "status": "blocked", "reason": "environment-session-construction-unconfirmed"}))
        return 1
    print(json.dumps({"schema": "deploy/environment-session-command-result/v1", **result}, sort_keys=True))
    if result.get("controller_cleanup", {}).get("status") == "pending":
        return 2
    if result.get("controller_cleanup", {}).get("status") == "blocked":
        return 1
    if result["cleanup"]["status"] != "completed":
        return 2 if result["cleanup"]["status"] in ("pending", "unknown", "not-started") else 1
    return 0 if args.operation == "cleanup" or result["functional"]["status"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
