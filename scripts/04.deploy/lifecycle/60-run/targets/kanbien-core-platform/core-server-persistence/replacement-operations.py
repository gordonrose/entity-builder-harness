#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.core-persistence.replacement-operations
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.core-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind one baseline replacement original to existing immutable reservation mechanics without changing historical proof readers.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.rehearse-core-server-persistence-replacement.impl
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-server-replacement/script.py
"""A closed baseline binding, not a new journal, proof store or retry policy."""
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


SHARED = Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws"
RESERVATIONS = module("persistence_replacement_reservations", SHARED / "resource_reservation.py")
TASKS = module("persistence_replacement_tasks", SHARED / "tasks.py")
PHASE = "server-replacement"


class OperationFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class Store(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/persistence-replacement-reservation/v1"
    operation_prefix = "kp-"
    failure = staticmethod(lambda code: OperationFailure("persistence-replacement-" + code))

    def selection_path(self, receipt, admission=None):
        if not isinstance(receipt, dict) or any(not isinstance(receipt.get(key), str) or re.fullmatch(pattern, receipt[key]) is None for key, pattern in {"source_revision": r"[a-f0-9]{40}", "image_digest": r"sha256:[a-f0-9]{64}"}.items()):
            raise self.failure("request-invalid")
        if admission is not None and (not isinstance(admission, str) or re.fullmatch(r"[a-f0-9]{64}", admission) is None):
            raise self.failure("admission-invalid")
        path = self.root / (receipt["source_revision"] + "-" + receipt["image_digest"][7:] + ("-" + admission if admission else "") + ".json")
        RESERVATIONS.no_symlinks(path)
        return path

    def path_for(self, phase, request):
        if phase != PHASE or not isinstance(request, dict) or set(request) != {"source_revision", "image_digest", "definition", "original_task", "administration_receipt_sha256"}:
            raise self.failure("request-invalid")
        patterns = {"definition": r"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-core-server-persistence:[1-9][0-9]*",
                    "original_task": r"arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/[a-f0-9]{32}"}
        if any(not isinstance(request[key], str) or re.fullmatch(pattern, request[key]) is None for key, pattern in patterns.items()):
            raise self.failure("request-invalid")
        return self.selection_path(request, request["administration_receipt_sha256"])

    def validate_time(self, value):
        try:
            if not isinstance(value, str) or datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None: raise ValueError()
        except (ValueError, TypeError): raise self.failure("time-invalid") from None

    def selected(self, receipt, admission=None):
        """Read the original from the closed release slot, then verify its envelope."""
        path = self.selection_path(receipt, admission)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, "rb") as stream: raw = stream.read(65537)
            if len(raw) > 65536: raise self.failure("reservation-unavailable")
            value = json.loads(raw)
            request = value.get("request") if isinstance(value, dict) else None
        except FileNotFoundError: return None
        except (OSError, ValueError, TypeError, UnicodeError): raise self.failure("reservation-unavailable") from None
        if not isinstance(request, dict) or any(request.get(key) != receipt[key] for key in ("image_digest", "source_revision")) or self.path_for(PHASE, request) != path:
            raise self.failure("reservation-mismatch")
        selected = self.read(PHASE, request)
        if selected is None: raise self.failure("reservation-unavailable")
        return selected


def administration_admission(root, reference, receipts, aws):
    """Validate a real revoke/restore completion, never a reset label or authority."""
    if reference is None: return None, None
    try:
        relative = Path(reference)
        if relative.is_absolute() or ".." in relative.parts: raise ValueError()
        path = root / relative
        RESERVATIONS.no_symlinks(path)
        if path.parent != receipts.RECEIPTS: raise ValueError()
        with path.open("rb") as stream: raw = stream.read(1048577)
        if len(raw) > 1048576: raise ValueError()
        value = receipts.validate(json.loads(raw))
        expected = {"revoke-runtime": "PERSISTENCE_RUNTIME_IAM_ACCESS_REVOKED", "restore-runtime": "PERSISTENCE_RUNTIME_IAM_ACCESS_RESTORED"}
        task, context, provenance = value["task"], value["context"], value["provenance"]
        if value["proof_type"] != "administration" or value["operation"] not in expected or task["exit_code"] != 0 or task["result_code"] != expected[value["operation"]]: raise ValueError()
        if provenance["controller"] != "run-administration" or provenance.get("evidence_class", "live") != receipts.EVIDENCE_CLASS or context["completion_duration_seconds"] > context["completion_deadline_seconds"]: raise ValueError()
        start, stop = (datetime.fromisoformat(task[key].replace("Z", "+00:00")) for key in ("started_at", "stopped_at"))
        if start.tzinfo is None or stop.tzinfo is None or stop < start or (stop-start).total_seconds() > context["completion_deadline_seconds"]: raise ValueError()
        ok, result, code = aws("cloudformation", "describe-stacks", "--stack-name", "kanbien-core-platform-core-server-persistence")
        if not ok: raise TASKS.ProviderFailure(code)
        stacks = result.get("Stacks") if isinstance(result, dict) else None
        outputs = stacks[0].get("Outputs") if isinstance(stacks, list) and len(stacks)==1 and isinstance(stacks[0],dict) else None
        definitions = [row.get("OutputValue") for row in outputs if isinstance(row,dict) and row.get("OutputKey")=="CoreServerPersistenceAdministrationTaskDefinitionArn"] if isinstance(outputs,list) else []
        if definitions != [task["definition"]] or re.fullmatch(r"arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:[1-9][0-9]*", task["definition"]) is None: raise ValueError()
        ok, result, code = aws("ecs", "describe-task-definition", "--task-definition", task["definition"])
        if not ok: raise TASKS.ProviderFailure(code)
        definition = result.get("taskDefinition") if isinstance(result,dict) else None
        containers = definition.get("containerDefinitions") if isinstance(definition,dict) and definition.get("taskDefinitionArn")==task["definition"] else None
        if not isinstance(containers,list) or len(containers)!=1 or not isinstance(containers[0],dict) or containers[0].get("name")!="persistence-administration" or containers[0].get("image")!="337159794548.dkr.ecr.eu-west-1.amazonaws.com/kanbien-core-platform/core-server@"+task["image_digest"]: raise ValueError()
        return hashlib.sha256(raw).hexdigest(), stop
    except TASKS.ProviderFailure: raise
    except (OSError, ValueError, TypeError, KeyError, RESERVATIONS.ReservationFailure):
        raise OperationFailure("persistence-replacement-administration-admission-invalid") from None


def store(root):
    try:
        git = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
        return Store(Path(git) / "persistence-replacements")
    except (OSError, subprocess.SubprocessError, RESERVATIONS.ReservationFailure):
        raise OperationFailure("persistence-replacement-store-unavailable") from None


def provider(aws):
    def invoke(service, operation, **parameters):
        if service != "ecs" or operation != "stop-task" or set(parameters) != {"cluster", "task", "reason"}:
            raise TASKS.ProviderFailure("persistence-replacement-provider-arguments-invalid")
        ok, value, code = aws("ecs", "stop-task", "--cluster", parameters["cluster"], "--task", parameters["task"], "--reason", parameters["reason"])
        if not ok: raise TASKS.ProviderFailure(code)
        return value
    return invoke
