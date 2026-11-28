#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.core-persistence.task-operations
#   version: 3
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind administration and migration to the existing durable task reservation protocol and original proof receipt readers.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.plan.consolidate-core-platform-deployment-routes
#     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
"""Baseline workload binding, not another task engine or proof receipt format."""
import hashlib
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


SHARED = Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws"
JOURNAL = module("persistence_task_journal", SHARED / "task_journal.py")
TASKS = module("persistence_task_execution", SHARED / "tasks.py")
RESPONSE = module("persistence_task_response", SHARED / "response.py")
ACCOUNT, REGION, CLUSTER = "337159794548", "eu-west-1", "kanbien-core-platform"
PENDING = {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}


class OperationFailure(Exception):
    pass


def checked_runtime(provider, *, view, workload_binding, workload, related_views=()):
    """Select only captured workload declarations; no ambient provider or launch."""
    shared = module("persistence_checked_runtime", Path(__file__).resolve().parents[4] / "00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
    try:
        shared.require(isinstance(workload_binding, dict) and isinstance(view, dict)
                       and workload_binding.get("target") == view.get("binding", {}).get("target")
                       and workload_binding.get("scope") == view.get("component")
                       and isinstance(workload, str) and isinstance(workload_binding.get("workloads"), list),
                       "task-binding-selection-invalid", "unselected", "selection")
        rows = [row for row in workload_binding["workloads"] if isinstance(row, dict) and row.get("id") == workload]
        shared.require(len(rows) == 1 and rows[0].get("runtime_class") == "task"
                       and rows[0].get("workload_type") == "run-to-completion-task",
                       "task-binding-selection-invalid", workload, "selection")
        group = copy.deepcopy(rows[0].get("security_group"))
        if isinstance(group, dict) and group.get("component") != view["component"]:
            recipe = workload_binding.get("proposed_provider_binding", {}).get("execution_parameters", {}).get(group.get("parameter"))
            shared.require(recipe == {"kind": "output", "component": group.get("component"), "output": group.get("output")},
                           "task-binding-selection-invalid", workload, "selection")
        return shared.inspect_runtime(provider, view=view, selection={"workload": workload, "definition": rows[0].get("provider_reference"), "security_group": group},
                                      related_views=related_views, account=ACCOUNT, region=REGION)
    except shared.BindingFailure:
        raise
    except Exception:
        raise shared.BindingFailure("runtime-binding-invalid", "unselected", "source") from None


class BoundOperation:
    """Closed baseline binding; only existing controllers supply live capability."""
    def __init__(self, *, root, proof_type, family, container, selector, results, aws, report, accept, receipts,
                 runtime=None, storage=None, step_id=None):
        self.root, self.proof_type = Path(root), proof_type
        self.family, self.container, self.selector, self.results = family, container, selector, results
        self.aws, self.report, self.accept, self.receipts = aws, report, accept, receipts
        self.prefix = "persistence-" + proof_type
        self.schema = "deploy/" + self.prefix + "-operation/v1"
        self.marker = (self.prefix + "-operation/v1\n").encode()
        try: self.runtime = TASKS.runtime_binding(runtime, account=ACCOUNT, region=REGION) if runtime is not None else None
        except TASKS.TaskFailure: raise OperationFailure("operation-runtime-invalid") from None
        self.storage, self.step_id = storage, step_id

    def context(self, request):
        runtime = request.get("runtime")
        if runtime is None:
            return {"family": self.family, "container_name": self.container, "cluster_arn": CLUSTER}
        return TASKS.runtime_binding(runtime, account=ACCOUNT, region=REGION)

    def task_prefix(self, request):
        cluster = self.context(request)["cluster_arn"].rsplit("/", 1)[-1]
        return f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{cluster}/"

    def paths(self, mode):
        if mode not in self.results: raise OperationFailure("operation-mode-invalid")
        git = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
        directory = JOURNAL.directory(git, self.prefix)
        return directory / (mode + ".json"), directory / (mode + ".lock")

    def validate_request(self, request, mode):
        fields = {"task_definition", "network", "overrides", "deadline_seconds", "admission"}
        if mode not in self.results or not isinstance(request, dict) or set(request) not in (fields, fields | {"runtime"}): raise ValueError()
        if "runtime" in request and request["runtime"] is None: raise ValueError()
        try: context = self.context(request)
        except TASKS.TaskFailure: raise ValueError() from None
        admission = request["admission"]
        if admission is not None and (not isinstance(admission, dict) or set(admission) != {"path", "sha256"} or not isinstance(admission["path"], str) or Path(admission["path"]).is_absolute() or ".." in Path(admission["path"]).parts or not isinstance(admission["sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", admission["sha256"]) is None): raise ValueError()
        definition = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{context['family']}:"
        expected = {"containerOverrides": [{"name": context["container_name"], "environment": [{"name": self.selector, "value": mode}]}]}
        if not isinstance(request["task_definition"], str) or re.fullmatch(re.escape(definition) + r"[1-9][0-9]*", request["task_definition"]) is None or not isinstance(request["network"], str) or not request["network"] or request["overrides"] != expected or type(request["deadline_seconds"]) is not int or request["deadline_seconds"] <= 0: raise ValueError()

    def load(self, path, mode):
        try:
            return self.validate_record(JOURNAL.read(path), mode)
        except (OSError, ValueError, TypeError, KeyError): raise OperationFailure("operation-metadata-invalid") from None

    def validate_record(self, value, mode):
        try:
            fields = {"schema", "mode", "operation_id", "predecessor", "request", "task_arn", "proof_receipt", "proof_sha256", "integrity"}
            if not isinstance(value, dict) or set(value) != fields or value["schema"] != self.schema or value["mode"] != mode: raise ValueError()
            if not isinstance(value["operation_id"], str) or re.fullmatch(r"kp-[a-f0-9]{32}", value["operation_id"]) is None: raise ValueError()
            if value["predecessor"] is not None and (not isinstance(value["predecessor"], str) or re.fullmatch(r"kp-[a-f0-9]{32}", value["predecessor"]) is None): raise ValueError()
            request = value["request"]
            self.validate_request(request, mode)
            arn = value["task_arn"]
            if arn is not None and (not isinstance(arn, str) or re.fullmatch(re.escape(self.task_prefix(request)) + r"[a-f0-9]{32}", arn) is None): raise ValueError()
            if (value["proof_receipt"] is None) != (value["proof_sha256"] is None): raise ValueError()
            if value["proof_receipt"] is not None and (not isinstance(value["proof_receipt"], str) or not isinstance(value["proof_sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", value["proof_sha256"]) is None): raise ValueError()
            body = {key: item for key, item in value.items() if key != "integrity"}
            if value["integrity"] != hashlib.sha256(JOURNAL.canonical(body)).hexdigest(): raise ValueError()
            return value
        except (OSError, ValueError, TypeError, KeyError):
            raise OperationFailure("operation-metadata-invalid") from None

    def completion(self, value):
        if value["proof_receipt"] is None: return None
        try:
            proof = self.receipts.read({"path": value["proof_receipt"], "sha256": value["proof_sha256"]},
                root=self.root, storage=self.storage, task_arn_prefix=self.task_prefix(value["request"]))
            task = proof["task"]
            result = self.results[value["mode"]]
            allowed = {result} if isinstance(result, str) else set(result)
            allowed |= {self.prefix + "-unsuccessful-completion", self.prefix + "-completion-deadline-exceeded"}
            if proof["proof_type"] != self.proof_type or proof["operation"] != value["mode"] or task["arn"] != value["task_arn"] or task["definition"] != value["request"]["task_definition"] or task["result_code"] not in allowed or proof["context"]["completion_deadline_seconds"] != value["request"]["deadline_seconds"]: raise ValueError()
            return proof
        except Exception:
            raise OperationFailure("terminal-proof-unavailable") from None

    def remember(self, value, path, receipt):
        if self.storage is not None:
            return self.attach(value, "retain_proof", receipt)
        value["proof_receipt"] = receipt.relative_to(self.root).as_posix()
        value["proof_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
        JOURNAL.save(path, value)

    def attach(self, value, method, argument):
        try:
            JOURNAL.attach_retained(self.storage, self.step_id, value, method=method, argument=argument,
                validate_record=lambda item: self.validate_record(item, value["mode"]))
        except JOURNAL.JournalFailure as failure: raise OperationFailure(str(failure)) from None

    def remember_task(self, value, path, arn):
        if self.storage is not None: return self.attach(value, "retain_task", arn)
        value["task_arn"] = arn; JOURNAL.save(path, value)

    def exact(self, task, value):
        arn = task.get("taskArn")
        if not isinstance(arn, str) or re.fullmatch(re.escape(self.task_prefix(value["request"])) + r"[a-f0-9]{32}", arn) is None or task.get("taskDefinitionArn") != value["request"]["task_definition"] or task.get("startedBy") != value["operation_id"] or not RESPONSE.task_overrides_match(task, self.context(value["request"])["container_name"], {self.selector: value["mode"]}):
            raise TASKS.TaskFailure("observation-identity-mismatch")
        return task

    def observe(self, value, path, *, wait):
        proof = self.completion(value)
        if proof is not None:
            task = proof["task"]
            failed = task["exit_code"] != 0 or task["result_code"] in {self.prefix + "-unsuccessful-completion", self.prefix + "-completion-deadline-exceeded"}
            return self.report("failed" if failed else "accepted", task["result_code"] if failed else self.prefix + "-reconciled-retained-receipt",
                facts={"operation_id": value["operation_id"], "operation": value["mode"], "proof_receipt": value["proof_receipt"], "proof_sha256": value["proof_sha256"],
                       "evidence_reuse": "historical-completion", "completed_at": task["stopped_at"], self.proof_type + "_task": task["arn"], "safe_result_code": task["result_code"]})
        provider = TASKS.cli_provider(self.aws)
        cluster = self.context(value["request"])["cluster_arn"]
        if value["task_arn"] is None:
            task = TASKS.reconcile_task(provider, cluster=cluster, definition=value["request"]["task_definition"], operation_id=value["operation_id"], validate_task=lambda task: self.exact(task, value))
            self.remember_task(value, path, task["taskArn"])
        def read(_previous):
            task = TASKS.describe_task(provider, cluster=cluster, arn=value["task_arn"], validate_task=lambda task: self.exact(task, value))
            if self.storage is None: JOURNAL.save(path, value)
            return task
        task, terminal = TASKS.observe_until_terminal(read, seconds=value["request"]["deadline_seconds"], interval=5,
            wait=wait, pending_states=PENDING, monotonic=time.monotonic, sleep=time.sleep)
        if not terminal:
            return self.report("pending" if task.get("lastStatus") in PENDING else "uncertain", self.prefix + "-reconciliation-task-not-terminal",
                facts={"operation_id": value["operation_id"], self.proof_type + "_task": value["task_arn"]})
        context = {"runtime": value["request"]["runtime"], "provider": self.aws, "receipt_storage": self.storage} if self.storage is not None else {}
        return self.accept(task, value["request"]["deadline_seconds"], value["mode"], on_receipt=lambda receipt: self.remember(value, path, receipt), **context)

    def run(self, *, mode, definition, network, overrides, seconds, new_operation=False, expected_operation=None, historical=None, admission=None, authorize_successor=None):
        value, remote_possible = None, False
        try:
            request = {"task_definition": definition, "network": network, "overrides": json.loads(overrides), "deadline_seconds": seconds, "admission": admission}
            if self.runtime is not None: request["runtime"] = copy.deepcopy(self.runtime)
            try: self.validate_request(request, mode)
            except (ValueError, TypeError): raise OperationFailure("operation-request-invalid") from None
            def completed(previous):
                proof = self.completion(previous)
                if proof is not None and authorize_successor is not None: authorize_successor(previous, proof)
                return proof
            if self.runtime is not None or self.storage is not None or self.step_id is not None:
                if self.runtime is None or not isinstance(self.step_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", self.step_id) is None or not all(callable(getattr(self.storage, name, None)) for name in ("read", "compare_and_reserve", "retain_task", "retain_proof", "before_submit", "read_receipt", "retain_receipt")):
                    raise OperationFailure("operation-storage-invalid")
                value, fresh = JOURNAL.reserve_retained(self.storage, self.step_id, schema=self.schema, mode=mode,
                    request=request, new_operation=new_operation, expected=None if expected_operation == "none" else expected_operation,
                    completed=completed, validate_record=lambda item: self.validate_record(item, mode))
                if not fresh:
                    remote_possible = True
                    return self.observe(value, None, wait=False)
                try: admitted = self.storage.before_submit(self.step_id, copy.deepcopy(value))
                except Exception: raise OperationFailure("operation-admission-not-confirmed") from None
                if admitted is not True: raise OperationFailure("operation-admission-not-confirmed")
                remote_possible = True
                task = TASKS.submit_task(TASKS.cli_provider(self.aws), cluster=self.context(request)["cluster_arn"], definition=definition,
                    operation_id=value["operation_id"], network=network, overrides=request["overrides"], validate_task=lambda task: self.exact(task, value))
                self.remember_task(value, None, task["taskArn"])
                return self.observe(value, None, wait=True)
            path, lock_path = self.paths(mode)
            with JOURNAL.locked(path, lock_path, self.marker, lambda item: self.load(item, mode)) as (path, descriptor, value):
                remote_possible = value is not None
                if value is None and not new_operation and historical is not None:
                    reused = historical()
                    if reused is not None: return reused
                value, fresh = JOURNAL.reserve(path, descriptor, value, schema=self.schema, marker=self.marker, mode=mode,
                    request=request, new_operation=new_operation, expected=None if expected_operation == "none" else expected_operation, completed=completed)
                if not fresh: return self.observe(value, path, wait=False)
                self.report("pending", self.prefix + "-submission-prepared", facts={"operation_id": value["operation_id"]}, stream=sys.stderr)
                sys.stderr.flush()
                remote_possible = True
                task = TASKS.submit_task(TASKS.cli_provider(self.aws), cluster=CLUSTER, definition=definition, operation_id=value["operation_id"],
                    network=network, overrides=request["overrides"], validate_task=lambda task: self.exact(task, value))
                value["task_arn"] = task["taskArn"]; JOURNAL.save(path, value)
                return self.observe(value, path, wait=True)
        except (JOURNAL.JournalFailure, OperationFailure) as error:
            uncertain = remote_possible and self.storage is not None
            return self.report("uncertain" if uncertain else "pending" if str(error) == "operation-busy" else "blocked", self.prefix + "-" + str(error), facts={"operation_id": value["operation_id"]} if value else None)
        except TASKS.TaskFailure as error:
            names = {"submission-uncertain": "submission-uncertain-reconcile-required", "reconciliation-unavailable": "observation-uncertain", "reconciliation-unresolved": "task-identity-unresolved", "observation-unavailable": "controller-observation-uncertain", "observation-identity-mismatch": "controller-task-identity-mismatch"}
            return self.report("failed" if error.rejected else "uncertain", error.provider_code or self.prefix + "-" + names[error.code], facts={"operation_id": value["operation_id"]} if value else None)
        except (OSError, subprocess.SubprocessError):
            return self.report("uncertain" if remote_possible else "blocked", self.prefix + "-operation-store-unavailable",
                facts={"operation_id": value["operation_id"]} if value else None)
