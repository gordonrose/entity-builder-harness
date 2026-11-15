#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.core-persistence.change-set-operations
#   version: 2
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.core-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind baseline CREATE reservations and explicit-reconciliation UPDATE parameter transport to shared change-set mechanics without changing historical receipt readers.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.plan.consolidate-core-platform-deployment-routes
#     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


SHARED = Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws"
RESERVATIONS = module("persistence_resource_reservations", SHARED / "resource_reservation.py")
CHANGE_SETS = module("persistence_change_sets", SHARED / "change_sets.py")


class OperationFailure(Exception):
    def __init__(self, verdict, code):
        super().__init__(code)
        self.verdict, self.code = verdict, code


class Reported(Exception):
    """The caller already retained and printed its original finite diagnostic."""
    def __init__(self, status):
        self.status = status


class Store(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/persistence-change-set-reservation/v1"
    operation_prefix = "kp-"
    failure = staticmethod(lambda code: OperationFailure("blocked", "persistence-change-set-" + code))

    def path_for(self, phase, request):
        fields = {"change_set", "image_digest", "source_revision", "parameters_sha256", "template_sha256"}
        if phase not in {"create", "execute"} or not isinstance(request, dict) or set(request) != fields:
            raise self.failure("request-invalid")
        patterns = {"image_digest": r"sha256:[a-f0-9]{64}", "source_revision": r"[a-f0-9]{40}",
                    "parameters_sha256": r"[a-f0-9]{64}", "template_sha256": r"[a-f0-9]{64}"}
        if any(not isinstance(request[key], str) or re.fullmatch(pattern, request[key]) is None for key, pattern in patterns.items()):
            raise self.failure("request-invalid")
        if request["change_set"] != "kanbien-core-platform-persistence-create-" + request["image_digest"][7:19]:
            raise self.failure("request-invalid")
        path = self.root / (request["change_set"] + "-" + phase + ".json")
        RESERVATIONS.no_symlinks(path)
        return path

    def validate_time(self, value):
        try:
            if not isinstance(value, str) or datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None: raise ValueError()
        except (TypeError, ValueError): raise self.failure("time-invalid") from None


def store(root):
    try:
        git = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True).stdout.strip()
        return Store(Path(git) / "persistence-change-sets")
    except (OSError, subprocess.SubprocessError, RESERVATIONS.ReservationFailure):
        raise OperationFailure("blocked", "persistence-change-set-store-unavailable") from None


def intent(name, receipt, parameters, template):
    try:
        return {"change_set": name, "image_digest": receipt["image_digest"], "source_revision": receipt["source_revision"],
                "parameters_sha256": hashlib.sha256(RESERVATIONS.canonical(parameters)).hexdigest(),
                "template_sha256": hashlib.sha256(template.read_bytes()).hexdigest()}
    except (OSError, TypeError, ValueError, KeyError):
        raise OperationFailure("blocked", "persistence-change-set-inputs-unavailable") from None


def apply_update(aws, *, stack, name, parameters, template_arguments, review,
                 admit, observe, failure, reconcile_existing=lambda _change: False):
    """Baseline CLI binding for the common explicit-reconciliation protocol.

    Only parameter transport is owned here; the caller supplies its reviewed
    template choice, allowed resources, full parameter guard and final reader.
    Private parameter values are never copied into a failure report.
    """
    def create():
        submitted = False
        result = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as stream:
                json.dump(parameters, stream)
                stream.flush()
                submitted = True
                result = aws("cloudformation", "create-change-set", "--stack-name", stack,
                             "--change-set-name", name, "--change-set-type", "UPDATE",
                             *template_arguments, "--parameters", f"file://{stream.name}",
                             "--capabilities", "CAPABILITY_NAMED_IAM")
            return result
        except (OSError, ValueError, TypeError, UnicodeError):
            if result is not None and result[0] is False:
                return result  # Preserve the provider reason if cleanup also failed.
            raise OperationFailure("uncertain" if submitted else "blocked",
                                   "persistence-update-parameter-file-outcome-uncertain" if submitted
                                   else "persistence-update-parameter-file-unavailable") from None
    try:
        return CHANGE_SETS.reviewed_update(
            inspect=lambda: aws("cloudformation", "describe-change-set", "--stack-name", stack, "--change-set-name", name),
            create=create, review=review, admit=admit, observe=observe, failure=failure,
            reconcile_existing=reconcile_existing,
            execute=lambda: aws("cloudformation", "execute-change-set", "--stack-name", stack, "--change-set-name", name),
        )
    except OperationFailure as problem:
        return failure(problem.verdict, problem.code)
