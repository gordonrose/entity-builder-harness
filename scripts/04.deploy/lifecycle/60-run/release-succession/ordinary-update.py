#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.ordinary-update
#   version: 2
#   status: draft
#   created_on: "2026-11-19"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Connect existing ordinary-update controllers without owning operation retries or release evidence.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.command.ordinary-update
#     path: scripts/04.deploy/lifecycle/60-run/release-succession/ordinary-update.sh
"""Sequencing only. Child controllers own admission, reservations and custody."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
from itertools import chain

ROOT = Path(__file__).resolve().parents[5]


def module(path):
    spec = importlib.util.spec_from_file_location("delivery_" + hashlib.sha256(str(path).encode()).hexdigest()[:12], path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class Halt(Exception):
    def __init__(self, condition, *, verdict="blocked", reasons=(), evidence=None):
        self.condition, self.verdict, self.reasons = condition, verdict, list(reasons)
        # Private child evidence is checked by its owner, never projected raw.
        self.evidence = evidence


def require(condition, code):
    if not condition:
        raise Halt(code)


def owned_call(operation, failures):
    """Only explicitly supplied owning exception types carry their reason."""
    try:
        return operation()
    except failures as error:
        condition = getattr(error, "code", None) or str(error)
        if not isinstance(condition, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,159}", condition):
            raise Halt("delivery-owner-failure-unclassified") from None
        raise Halt(condition) from None


def read(path):
    try:
        require(not any(p.is_symlink() for p in (path, *path.parents)), "delivery-input-symlink")
        with path.open("rb") as stream:
            raw = stream.read(65537)
        require(len(raw) <= 65536, "delivery-input-too-large")
        require(bool(raw), "delivery-input-empty")
        try:
            value = json.loads(raw)
        except (UnicodeError, ValueError):
            raise Halt("delivery-input-json-invalid") from None
        require(isinstance(value, dict), "delivery-input-shape-invalid")
        return value
    except FileNotFoundError:
        raise Halt("delivery-input-missing") from None
    except PermissionError:
        raise Halt("delivery-input-inaccessible") from None
    except OSError:
        raise Halt("delivery-input-unreadable") from None


def invoke(argv, success, *, root=ROOT):
    """Never retry a child or expose native output on a boundary failure."""
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True)
        report = json.loads(result.stdout)
    except (OSError, ValueError, UnicodeError):
        raise Halt("delivery-child-outcome-unavailable", verdict="uncertain") from None
    if not isinstance(report, dict) or not isinstance(report.get("schema"), str) or not report["schema"].startswith("deploy/"):
        raise Halt("delivery-child-report-invalid", verdict="uncertain")
    verdict = report.get("verdict")
    if result.returncode or verdict not in success:
        codes = [report.get("condition")]
        findings = report.get("findings", [])
        if isinstance(findings, list):
            codes += [f.get("code") for f in findings if isinstance(f, dict)]
        safe = [code for code in codes if isinstance(code, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,159}", code)]
        raise Halt("delivery-child-not-successful", verdict=verdict if verdict in {"pending", "failed", "uncertain", "blocked"} else "uncertain", reasons=safe[:16], evidence=report)
    return report


class Context:
    owned = staticmethod(owned_call)
    def __init__(self, scope, inputs, *, root=ROOT, runner=invoke):
        self.root, self.scope, self.input_path, self.runner = root, scope, inputs, runner
        self.compiler = module(root / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
        self.succession = module(root / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
        self.route, _ = self.compiler.load_route(scope, root)
        self.data = read(inputs)
        require(set(self.data) == {"schema", "target", "scope", "values"}
                and self.data.get("schema") == "deploy/ordinary-update-inputs/v1"
                and all(self.data.get(k) == self.route.get(k) for k in ("target", "scope")), "delivery-subject-invalid")
        self.values = self.data.get("values")
        require(isinstance(self.values, dict), "delivery-values-invalid")
        self.expected = self.values.get("expected_predecessor")
        require(isinstance(self.expected, str) and re.fullmatch(r"release-[a-f0-9]{24}", self.expected), "delivery-predecessor-invalid")
        self.evidence_root = scope.parent.parent / "30-release-evidence"
        self.bindings = {"scope_contract": str(scope), "evidence_root": str(self.evidence_root),
            "target_root": str(scope.parents[2]), "target_directory": str(scope.parents[3]),
            "current_release_id": self.expected}
        self.package = None
        self.snapshots = {inputs: inputs.read_bytes(), scope: scope.read_bytes()}
        route_path = self.compiler.load_route(scope, root)[1]
        self.snapshots[route_path] = route_path.read_bytes()

    def path(self, value):
        require(isinstance(value, str) and value and not any(c in value for c in "\n\r\0"), "delivery-path-invalid")
        path = Path(value)
        return path if path.is_absolute() else self.root / path

    def package_path(self):
        path = self.path(self.values.get("candidate_receipt"))
        read(path)
        raw = path.read_bytes()
        require(path not in self.snapshots or self.snapshots[path] == raw, "delivery-input-changed")
        self.snapshots[path] = raw
        return path

    def retain_input(self, path):
        read(path)
        self.snapshots[path] = path.read_bytes()
        return path

    def release_boundary(self, consumer):
        """Reviewable immutable intent, not a new approval or operation ledger."""
        state = self.current()
        require(state["release_id"] == self.expected or self.already_accepted(state), "delivery-predecessor-changed")
        prior, _ = self.succession.history_record_for_id(self.evidence_root, self.expected)
        sources = {}
        for directory in ("scripts/04.deploy", "infra/04.deploy", ".agentic/04.deploy", ".agentic/aws"):
            for path in sorted((self.root / directory).rglob("*")):
                if "30-release-evidence" in path.parts or "__pycache__" in path.parts:
                    continue
                require(not path.is_symlink(), "delivery-source-symlink")
                if path.is_file():
                    sources[path.relative_to(self.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        value = {"schema": "deploy/ordinary-release-approval/v1", "target": self.route["target"], "scope": self.route["scope"],
            "inputs_sha256": hashlib.sha256(self.input_path.read_bytes()).hexdigest(), "candidate": self.package,
            "predecessor": prior["release"], "expected_predecessor": self.expected,
            "source_sha256": fingerprint(sources), "input_sha256": fingerprint({str(p): hashlib.sha256(raw).hexdigest() for p, raw in self.snapshots.items()}),
            **consumer.release_effects()}
        return value

    def authorize(self, consumer, approved):
        boundary = self.release_boundary(consumer)
        require(isinstance(approved, str) and approved == fingerprint(boundary), "delivery-release-approval-mismatch")
        self.approved_release = approved
        self.approval_consumer = consumer

    def check_authority(self):
        self.unchanged()
        require(fingerprint(self.release_boundary(self.approval_consumer)) == self.approved_release, "delivery-release-approval-changed")

    def unchanged(self):
        require(all(path.read_bytes() == raw for path, raw in self.snapshots.items()), "delivery-input-changed")

    def command(self, name, success, **values):
        argv = self.compiler.resolve(self.route["commands"][name]["argv"], {**self.values, **self.bindings, **values})
        require(argv is not None, "delivery-command-input-missing")
        return self.runner(argv, success, root=self.root)

    def current(self):
        state = self.owned(lambda: self.succession.current(self.evidence_root), (self.succession.SuccessionFailure,))
        require(state is not None and all(state[k] == self.route[k] for k in ("target", "scope")), "delivery-current-release-invalid")
        return state

    def already_accepted(self, state):
        if state["release_id"] == self.expected:
            return False
        history, _ = self.succession.history_record_for_id(self.evidence_root, state["release_id"])
        release = history["release"]
        require(state.get("predecessor") == self.expected
                and all(release.get(k) == self.package[k] for k in ("source_revision", "image_digest"))
                and self.accepted_package(state)["receipt_reference"] == self.package["receipt_reference"], "delivery-predecessor-changed")
        return True

    def manifest(self, values, directory, *, ordinary=True):
        # Ephemeral collector input, not another operation/evidence journal.
        path = Path(directory) / "acceptance-inputs.json"
        path.write_text(json.dumps({"schema": "deploy/acceptance-inputs/v1", "target": self.route["target"],
            "scope": self.route["scope"], **({"release_mode": "ordinary-update"} if ordinary else {}), "values": values}))
        return str(path)


def fingerprint(value):
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def boundary_condition(consumer, error):
    try: code = consumer.failure_code(error)
    except Exception: return "delivery-boundary-not-confirmed"
    return code if isinstance(code, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,159}", code) else "delivery-boundary-not-confirmed"


def restore(consumer, failure, completed):
    """Only called with owner-validated terminal evidence; no recursive recovery."""
    ctx, stage = consumer.context, "rollback-admission"
    try:
        for stage, operation in consumer.recovery_steps():
            ctx.check_authority()
            require(ctx.current()["release_id"] == ctx.expected, "delivery-predecessor-changed")
            operation()
            completed.append(stage)
        require(ctx.current()["release_id"] == ctx.expected, "delivery-predecessor-changed")
        return {"verdict": "failed", "candidate_verdict": "failed", "recovery": "restored",
            "condition": failure.condition, "reasons": failure.reasons, "completed": completed,
            "release_id": ctx.expected, "current_readiness": True, "delivery_budget": "not-established",
            "next_action": "inspect-rejected-candidate"}
    except Halt as error:
        return {"verdict": error.verdict, "candidate_verdict": "failed", "recovery": "incomplete", "stage": stage,
            "condition": error.condition, "reasons": error.reasons, "candidate_reasons": failure.reasons,
            "completed": completed, "current_readiness": False, "delivery_budget": "not-established",
            "next_action": "reconcile-owned-recovery"}
    except Exception as error:
        return {"verdict": "uncertain", "candidate_verdict": "failed", "recovery": "incomplete", "stage": stage,
            "condition": boundary_condition(consumer, error), "completed": completed, "current_readiness": False,
            "delivery_budget": "not-established", "next_action": "reconcile-owned-recovery"}


def continue_update(consumer):
    """Repeat only owner-defined reconciliation, never infer a retry from failure."""
    context, completed, stage = consumer.context, [], "admission"
    started = time.monotonic()
    try:
        context.unchanged()
        if context.already_accepted(context.current()):
            return {"verdict": "retained", "completed": [], "current_readiness": False,
                    "release_id": context.current()["release_id"], "delivery_budget": "not-established"}
        context.check_authority()
        consumer.admit()
        recovery = consumer.pending_recovery()
        if recovery is not None:
            return restore(consumer, recovery, completed)
        # One temporary input directory lasts through collection and promotion.
        # All durable state remains in each controller's existing receipt store.
        with tempfile.TemporaryDirectory(prefix="ordinary-update-") as directory:
            def collect():
                candidate, inputs = consumer.collect(directory)
                require(isinstance(candidate, str) and candidate, "delivery-candidate-reference-missing")
                context.bindings.update(candidate_record=candidate, acceptance_inputs=inputs)
            acceptance = [("collect", collect),
                ("validate-candidate", lambda: context.command("validate-candidate", {"valid"})),
                ("promote", lambda: context.command("promote", {"promoted", "accepted", "retained", "already-current"}))]
            for stage, operation in chain(consumer.steps(), acceptance):
                context.check_authority()
                require(context.current()["release_id"] == context.expected, "delivery-predecessor-changed")
                try:
                    operation()
                except Halt as error:
                    if "deploy" in completed and error.verdict == "failed" and consumer.confirm_failure(stage, error):
                        return restore(consumer, error, completed)
                    raise
                completed.append(stage)
            stage = "acceptance-observation"
            state = context.current()
            require(context.already_accepted(state), "delivery-acceptance-not-confirmed")
        return {"verdict": "accepted", "completed": completed, "release_id": state["release_id"],
                "current_readiness": True, "delivery_budget": "not-established", "invocation_seconds": time.monotonic() - started}
    except Halt as error:
        return {"verdict": error.verdict, "stage": stage, "condition": error.condition, "reasons": error.reasons,
                "completed": completed, "current_readiness": False, "delivery_budget": "not-established",
                "next_action": "reconcile-owned-operation" if error.verdict in {"pending", "uncertain"} else
                    "inspect-failure-and-select-authorised-recovery" if error.verdict == "failed" else "resolve-admission-without-replay"}
    except Exception as error:
        # Unknown errors cannot establish whether a child effect happened.
        return {"verdict": "uncertain", "stage": stage, "condition": boundary_condition(consumer, error),
                "completed": completed, "current_readiness": False, "delivery_budget": "not-established",
                "next_action": "reconcile-owned-operation"}


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--scope-contract", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--plan-release", action="store_true")
    parser.add_argument("--approved-release")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    parser.error = lambda _message: (_ for _ in ()).throw(Halt("delivery-arguments-invalid"))
    try:
        args = parser.parse_args()
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        require(args.execute != args.plan_release, "delivery-execution-not-selected")
        scope = args.scope_contract.absolute()
        require(scope.is_relative_to(ROOT) and scope == scope.resolve()
                and not any(path.is_symlink() for path in (scope, *scope.parents)), "delivery-scope-invalid")
        context = Context(scope, args.inputs.absolute())
        report = context.compiler.inspect(scope, ROOT, probe_commands=False)
        require(not report["findings"], "delivery-route-invalid")
        selected = context.route.get("ordinary_delivery", {})
        implementation = context.compiler.reference(ROOT, selected.get("implementation"))
        require(implementation is not None and implementation.is_file()
                and context.compiler.command_metadata(implementation).get("id") == selected.get("owner"), "delivery-owner-invalid")
        consumer = module(implementation).Consumer(context, Halt, require)
        if args.plan_release:
            boundary = context.release_boundary(consumer)
            report = {"verdict": "planned", "release": boundary, "approval_sha256": fingerprint(boundary)}
        else:
            context.authorize(consumer, args.approved_release)
            report = continue_update(consumer)
        report.update(target=context.route["target"], scope=context.route["scope"])
    except Halt as error:
        report = {"verdict": error.verdict, "condition": error.condition, "reasons": error.reasons}
    except Exception:
        report = {"verdict": "uncertain", "condition": "delivery-boundary-not-confirmed"}
    print(json.dumps({"schema": "deploy/ordinary-update-report/v1", **report}, sort_keys=True))
    return 0 if report["verdict"] in {"accepted", "retained", "planned"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
