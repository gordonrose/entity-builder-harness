#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.core-persistence.change-set-operations
#   version: 4
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.core-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind CREATE and UPDATE reservations and CLI parameter transport to shared change-set mechanics without changing historical receipt readers.
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
        if phase in {"update-create", "update-execute"}:
            if (not isinstance(request, dict) or set(request) != {"stack", "change_set", "inputs_sha256"}
                    or any(not isinstance(request[key], str) or re.fullmatch(r"[a-zA-Z][a-zA-Z0-9-]{0,127}", request[key]) is None for key in ("stack", "change_set"))
                    or not isinstance(request["inputs_sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", request["inputs_sha256"]) is None):
                raise self.failure("request-invalid")
            path = self.root / (request["stack"] + "-" + request["change_set"] + "-" + phase + ".json")
            RESERVATIONS.no_symlinks(path)
            return path
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


def labelled_name(name, label):
    if label is None: return name
    if not isinstance(label, str) or re.fullmatch(r"[a-z][a-z0-9-]{0,23}", label) is None: return None
    return name + "-" + label


def update_request(*, stack, name, receipt, controller, template, settings):
    sources = (Path(controller), Path(template), Path(__file__), SHARED / "change_sets.py",
               SHARED / "resource_reservation.py", Path(__file__).parent / "prepare-candidate/script.py")
    inputs = {"receipt": receipt, "settings": settings,
              "sources": [hashlib.sha256(path.read_bytes()).hexdigest() for path in sources]}
    return {"stack": stack, "change_set": name,
            "inputs_sha256": hashlib.sha256(RESERVATIONS.canonical(inputs)).hexdigest()}


def begin_update(root, *, stack, name, receipt, controller, template, settings, observe, failure):
    """Recognise retained execution before gates which require a healthy predecessor.

    Bind immutable user intent, not observations that change during execution.
    An existing creation may advance through fresh gates; existing execution
    is observation-only. Historical operations without reservations are never
    adopted for execution. Their explicit read-only readers remain supported.
    """
    try:
        request = update_request(stack=stack, name=name, receipt=receipt, controller=controller, template=template, settings=settings)
        owner = store(root)
        executed = CHANGE_SETS.retained_execution(owner,
            preparation_phase="update-create", preparation_request=request,
            execution_phase="update-execute", execution_request=request,
            missing_preparation=lambda: OperationFailure("blocked", "persistence-change-set-reservation-mismatch"))
    except (OperationFailure, RESERVATIONS.ReservationFailure) as problem:
        return None, failure("blocked", problem.code)
    except (OSError, TypeError, ValueError):
        return None, failure("blocked", "persistence-change-set-inputs-unavailable")
    return request, observe(executed) if executed is not None else None


def apply_update(aws, *, root, stack, name, request, parameters, template_arguments, review,
                 admit, observe, failure):
    """CLI transport only; the existing shared primitives own single submission."""
    def provider(service, operation, **arguments):
        if operation == "execute-change-set":
            ok, _, code = aws(service, operation, "--stack-name", stack, "--change-set-name", name,
                              "--client-request-token", arguments["ClientRequestToken"])
            if not ok: raise Reported(failure("uncertain", code))
            return
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
                             "--capabilities", "CAPABILITY_NAMED_IAM", "--client-token", arguments["ClientToken"],
                             "--description", arguments["Description"])
            if not result[0]: raise Reported(failure("uncertain", result[2]))
        except (OSError, ValueError, TypeError, UnicodeError):
            if result is not None and result[0] is False:
                raise Reported(failure("uncertain", result[2])) from None
            raise OperationFailure("uncertain" if submitted else "blocked",
                                   "persistence-update-parameter-file-outcome-uncertain" if submitted
                                   else "persistence-update-parameter-file-unavailable") from None
    def absent(_reservation):
        ok, _, code = aws("cloudformation", "describe-change-set", "--stack-name", stack, "--change-set-name", name)
        if ok: raise OperationFailure("blocked", "persistence-update-unowned-change-set")
        if code != "aws-resource-missing": raise OperationFailure("blocked", code)

    def reviewed(reservation):
        ok, change, code = aws("cloudformation", "describe-change-set", "--stack-name", stack, "--change-set-name", name)
        if not ok: raise OperationFailure("uncertain", code)
        if not isinstance(change, dict) or change.get("Description") != reservation["operation_id"]:
            raise OperationFailure("blocked", "persistence-update-change-set-lineage-not-confirmed")
        change, _ = review(change, True)
        if change is None or change.get("ExecutionStatus") != "AVAILABLE": raise Reported(observe(reservation))
        if change.get("Description") != reservation["operation_id"]:
            raise OperationFailure("blocked", "persistence-update-change-set-lineage-not-confirmed")
        rejection = admit(change)
        if rejection is not None: raise OperationFailure("blocked", rejection)
        return change

    try:
        if not isinstance(request, dict) or request.get("stack") != stack or request.get("change_set") != name:
            raise OperationFailure("blocked", "persistence-change-set-request-invalid")
        owner = store(root)
        executed = CHANGE_SETS.retained_execution(owner,
            preparation_phase="update-create", preparation_request=request,
            execution_phase="update-execute", execution_request=request,
            missing_preparation=lambda: OperationFailure("blocked", "persistence-change-set-reservation-mismatch"))
        if executed is not None: return observe(executed)
        CHANGE_SETS.prepare(provider, owner, phase="update-create", request=request, arguments={},
                            precondition=absent, observe=reviewed, passthrough=(Reported, OperationFailure))
        return CHANGE_SETS.execute(provider, owner, phase="update-execute", request=request, arguments={},
                                   precondition=lambda _: reviewed(owner.read("update-create", request)),
                                   observe=observe, passthrough=(Reported, OperationFailure))
    except Reported as result:
        return result.status
    except (OperationFailure, RESERVATIONS.ReservationFailure) as problem:
        return failure(getattr(problem, "verdict", "blocked"), problem.code)
    except CHANGE_SETS.ChangeSetFailure:
        return failure("uncertain", "persistence-change-set-submission-uncertain")
    except (TypeError, KeyError, ValueError, AttributeError):
        return failure("uncertain", "persistence-update-review-unobservable")
