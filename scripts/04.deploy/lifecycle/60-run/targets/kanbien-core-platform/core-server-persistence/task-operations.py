#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.core-persistence.task-operations
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-19"
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
TASK_PREFIX = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task/{CLUSTER}/"
PENDING = {"PROVISIONING", "PENDING", "ACTIVATING", "RUNNING", "DEACTIVATING", "STOPPING", "DEPROVISIONING"}


class OperationFailure(Exception):
    pass


class BoundOperation:
    """Closed baseline binding; only existing controllers supply live capability."""
    def __init__(self, *, root, proof_type, family, container, selector, results, aws, report, accept, receipts):
        self.root, self.proof_type = Path(root), proof_type
        self.family, self.container, self.selector, self.results = family, container, selector, results
        self.aws, self.report, self.accept, self.receipts = aws, report, accept, receipts
        self.prefix = "persistence-" + proof_type
        self.schema = "deploy/" + self.prefix + "-operation/v1"
        self.marker = (self.prefix + "-operation/v1\n").encode()

    def paths(self, mode):
        if mode not in self.results: raise OperationFailure("operation-mode-invalid")
        git = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
        directory = JOURNAL.directory(git, self.prefix)
        return directory / (mode + ".json"), directory / (mode + ".lock")

    def validate_request(self, request, mode):
        if not isinstance(request, dict) or set(request) != {"task_definition", "network", "overrides", "deadline_seconds", "admission"}: raise ValueError()
        admission = request["admission"]
        if admission is not None and (not isinstance(admission, dict) or set(admission) != {"path", "sha256"} or not isinstance(admission["path"], str) or Path(admission["path"]).is_absolute() or ".." in Path(admission["path"]).parts or not isinstance(admission["sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", admission["sha256"]) is None): raise ValueError()
        definition = f"arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/{self.family}:"
        expected = {"containerOverrides": [{"name": self.container, "environment": [{"name": self.selector, "value": mode}]}]}
        if not isinstance(request["task_definition"], str) or re.fullmatch(re.escape(definition) + r"[1-9][0-9]*", request["task_definition"]) is None or not isinstance(request["network"], str) or not request["network"] or request["overrides"] != expected or type(request["deadline_seconds"]) is not int or request["deadline_seconds"] <= 0: raise ValueError()

    def load(self, path, mode):
        try:
            value = JOURNAL.read(path)
            fields = {"schema", "mode", "operation_id", "predecessor", "request", "task_arn", "proof_receipt", "proof_sha256", "integrity"}
            if not isinstance(value, dict) or set(value) != fields or value["schema"] != self.schema or value["mode"] != mode: raise ValueError()
            if not isinstance(value["operation_id"], str) or re.fullmatch(r"kp-[a-f0-9]{32}", value["operation_id"]) is None: raise ValueError()
            if value["predecessor"] is not None and (not isinstance(value["predecessor"], str) or re.fullmatch(r"kp-[a-f0-9]{32}", value["predecessor"]) is None): raise ValueError()
            request = value["request"]
            self.validate_request(request, mode)
            arn = value["task_arn"]
            if arn is not None and (not isinstance(arn, str) or re.fullmatch(re.escape(TASK_PREFIX) + r"[a-f0-9]{32}", arn) is None): raise ValueError()
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
            original = self.root / value["proof_receipt"]
            path = original.resolve()
            if not path.is_relative_to(self.root.resolve()) or original.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != value["proof_sha256"]: raise ValueError()
            proof = self.receipts.validate(json.loads(path.read_text()))
            task = proof["task"]
            result = self.results[value["mode"]]
            allowed = {result} if isinstance(result, str) else set(result)
            allowed |= {self.prefix + "-unsuccessful-completion", self.prefix + "-completion-deadline-exceeded"}
            if proof["proof_type"] != self.proof_type or proof["operation"] != value["mode"] or task["arn"] != value["task_arn"] or task["definition"] != value["request"]["task_definition"] or task["result_code"] not in allowed or proof["context"]["completion_deadline_seconds"] != value["request"]["deadline_seconds"]: raise ValueError()
            return proof
        except Exception:
            raise OperationFailure("terminal-proof-unavailable") from None

    def remember(self, value, path, receipt):
        value["proof_receipt"] = receipt.relative_to(self.root).as_posix()
        value["proof_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
        JOURNAL.save(path, value)

    def exact(self, task, value):
        arn = task.get("taskArn")
        if not isinstance(arn, str) or re.fullmatch(re.escape(TASK_PREFIX) + r"[a-f0-9]{32}", arn) is None or task.get("taskDefinitionArn") != value["request"]["task_definition"] or task.get("startedBy") != value["operation_id"] or not RESPONSE.task_overrides_match(task, self.container, {self.selector: value["mode"]}):
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
        if value["task_arn"] is None:
            task = TASKS.reconcile_task(provider, cluster=CLUSTER, definition=value["request"]["task_definition"], operation_id=value["operation_id"], validate_task=lambda task: self.exact(task, value))
            value["task_arn"] = task["taskArn"]; JOURNAL.save(path, value)
        def read(_previous):
            task = TASKS.describe_task(provider, cluster=CLUSTER, arn=value["task_arn"], validate_task=lambda task: self.exact(task, value))
            JOURNAL.save(path, value)
            return task
        task, terminal = TASKS.observe_until_terminal(read, seconds=value["request"]["deadline_seconds"], interval=5,
            wait=wait, pending_states=PENDING, monotonic=time.monotonic, sleep=time.sleep)
        if not terminal:
            return self.report("pending" if task.get("lastStatus") in PENDING else "uncertain", self.prefix + "-reconciliation-task-not-terminal",
                facts={"operation_id": value["operation_id"], self.proof_type + "_task": value["task_arn"]})
        return self.accept(task, value["request"]["deadline_seconds"], value["mode"], on_receipt=lambda receipt: self.remember(value, path, receipt))

    def run(self, *, mode, definition, network, overrides, seconds, new_operation=False, expected_operation=None, historical=None, admission=None, authorize_successor=None):
        value, remote_possible = None, False
        try:
            request = {"task_definition": definition, "network": network, "overrides": json.loads(overrides), "deadline_seconds": seconds, "admission": admission}
            try: self.validate_request(request, mode)
            except (ValueError, TypeError): raise OperationFailure("operation-request-invalid") from None
            path, lock_path = self.paths(mode)
            with JOURNAL.locked(path, lock_path, self.marker, lambda item: self.load(item, mode)) as (path, descriptor, value):
                remote_possible = value is not None
                if value is None and not new_operation and historical is not None:
                    reused = historical()
                    if reused is not None: return reused
                def completed(previous):
                    proof = self.completion(previous)
                    if proof is not None and authorize_successor is not None: authorize_successor(previous, proof)
                    return proof
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
            return self.report("pending" if str(error) == "operation-busy" else "blocked", self.prefix + "-" + str(error), facts={"operation_id": value["operation_id"]} if value else None)
        except TASKS.TaskFailure as error:
            names = {"submission-uncertain": "submission-uncertain-reconcile-required", "reconciliation-unavailable": "observation-uncertain", "reconciliation-unresolved": "task-identity-unresolved", "observation-unavailable": "controller-observation-uncertain", "observation-identity-mismatch": "controller-task-identity-mismatch"}
            return self.report("failed" if error.rejected else "uncertain", error.provider_code or self.prefix + "-" + names[error.code], facts={"operation_id": value["operation_id"]} if value else None)
        except (OSError, subprocess.SubprocessError):
            return self.report("uncertain" if remote_possible else "blocked", self.prefix + "-operation-store-unavailable",
                facts={"operation_id": value["operation_id"]} if value else None)
