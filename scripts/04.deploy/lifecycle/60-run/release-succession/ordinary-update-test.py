#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.ordinary-update
#   version: 4
#   status: draft
#   created_on: "2026-11-19"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise connected consumer commands, interruption and failure without provider access.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
"""Connected bindings with controlled child outcomes; never provider proof."""
import json
import copy
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import importlib.util
import contextlib
import io
import sys
import hashlib

spec = importlib.util.spec_from_file_location("ordinary_delivery_test_owner", Path(__file__).with_name("ordinary-update.py"))
D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
ROOT = D.ROOT
TARGET = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform"
OLD, NEW = "release-" + "a" * 24, "release-" + "b" * 24
PACKAGE = {"source_revision": "c" * 40, "image_digest": "sha256:" + "d" * 64, "receipt_reference": "fixture-qualified-package"}


class Harness:
    def __init__(self, scope, directory, *, parse=False):
        self.scope, self.parse = scope, parse
        self.calls, self.effects, self.retained = [], [], {}
        self.fail_at, self.interrupt_at, self.change_at = None, None, None
        self.failure_verdict, self.failure_evidence = "failed", None
        self.state = {"target": "kanbien-core-platform", "scope": scope, "release_id": OLD, "predecessor": None}
        self.receipt = Path(directory) / (scope + "-package.json")
        self.receipt.write_text(json.dumps(PACKAGE))
        self.scope_path = TARGET / "20-scopes" / scope / "00-declaration/declaration-contract.yml"
        compiler = D.module(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
        route, _ = compiler.load_route(self.scope_path)
        self.adapter = D.module(ROOT / route["ordinary_delivery"]["implementation"])
        self.collector = self.adapter.collector()
        values = {"candidate_receipt": str(self.receipt), "expected_predecessor": OLD,
                  "rollback_receipt": str(self.receipt), "rollback_compatibility_id": "rollback-compatibility-" + "a" * 24}
        if scope == "core-server-persistence":
            self.collector.receipt = lambda _path: dict(PACKAGE)
            policy = self.collector.updates().policy(self.collector.owner())
            commands = [route["proofs"][name]["command"] for name in policy["fresh_tasks"]] + ["current-health"]
            names = {v[1:-1] for name in commands for v in route["commands"][name]["argv"] if v.endswith("_predecessor}")}
            values.update(delivery_label="local-connection", operation_predecessors={name: "none" for name in names})
        else:
            self.collector.C.ALIGN.read_receipt = lambda _path: dict(PACKAGE)
            values.update(proof_label="entity-smoke-" + "e" * 24, expected_digest="f" * 64)
        self.input_path = Path(directory) / (scope + "-inputs.json")
        self.input_path.write_text(json.dumps({"schema": "deploy/ordinary-update-inputs/v1", "target": "kanbien-core-platform", "scope": scope, "values": values}))
        self.adapter.collector = lambda: self.collector

    def consumer(self):
        context = D.Context(self.scope_path, self.input_path, runner=self.runner)
        consumer = self.adapter.Consumer(context, D.Halt, D.require)
        context.current = lambda: dict(self.state)
        context.succession.history_record_for_id = lambda *_: ({"release": dict(PACKAGE)}, b"fixture")
        context.accepted_package = lambda _state: dict(PACKAGE)
        # Admission and custody readers have their own real collector regressions.
        # Here their observations are controlled; actual command wiring/parsers
        # and the shared progression are exercised, without claiming live proof.
        consumer.admit = lambda: self.calls.append("admission")
        context.check_authority = context.unchanged
        consumer.pending_recovery = lambda: None
        if self.scope == "entity-smoke":
            consumer.release_context = lambda: ({}, {}, self.receipt.parent)
            consumer.qualification = lambda: {"mode": "reuse"}
            consumer.approved_plan = lambda *_args, **_kwargs: "sha256:" + "1" * 64
        return consumer

    def runner(self, argv, success, *, root):
        def arg(flag): return argv[argv.index(flag) + 1]
        script = argv[1]
        if "transition-qualified-release" in script or (script.endswith("entity-smoke/script.sh")):
            if self.scope == "entity-smoke":
                assert arg("--mode") in {"plan", "apply"}, "ordinary update must review before execution"
            name = "rollback" if arg("--phase" if self.scope == "entity-smoke" else "--operation") == "rollback" else "deploy"
            verdict, facts = "transitioned" if self.scope == "core-server-persistence" else "completed", {}
        elif script.endswith(("task-execute.sh", "task-plan.sh")):
            name = "/".join(arg(f) for f in ("--proof-stage", "--workload", "--operation", "--phase"))
            verdict, facts = "completed", {}
        elif "run-administration/" in script or "verify-candidate/" in script:
            name = arg("--operation") if "--operation" in argv else arg("--mode")
            proof = self.receipt.parent / (name + ".json")
            proof.write_text("{}")
            verdict, facts = "accepted", {"proof_receipt": str(proof), "verifier_task": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32}
        elif "collect-acceptance" in script:
            name, verdict, facts = "collect", "recorded" if self.scope == "core-server-persistence" else "collected", {"candidate_record": "fixture-candidate.yml"}
            manifest = json.loads(Path(arg("--inputs")).read_text())
            self.last_manifest = manifest
            D.module(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py").input_values(Path(arg("--inputs")), self.consumer_route(), root=ROOT)
        elif "promote-acceptance" in script or "--operation" in argv and arg("--operation") == "promote":
            name, verdict, facts = "promote", "accepted" if self.scope == "entity-smoke" else "promoted", {}
            assert arg("--expected-predecessor") == OLD
        else:
            name, verdict, facts = "validate-candidate", "valid", {}
        if self.parse:
            result = subprocess.run([*argv, "--validate-arguments"], cwd=root, capture_output=True, text=True)
            assert result.returncode == 0, (name, result.stdout, result.stderr)
            assert json.loads(result.stdout)["verdict"] == "valid"
        if script.endswith("task-plan.sh") or "--mode" in argv and arg("--mode") == "plan":
            return {"schema": "deploy/fixture-report/v1", "verdict": "planned", "plan": {}, "plan_sha256": "sha256:" + "1" * 64}
        self.calls.append(name)
        if name == self.fail_at:
            raise D.Halt("delivery-child-not-successful", verdict=self.failure_verdict, reasons=["fixture-task-failed"], evidence=self.failure_evidence)
        response = {"schema": "deploy/fixture-report/v1", "verdict": verdict, "facts": facts, **facts}
        key = tuple(argv)
        # Controllers retain effects, not the coordinator. Collection is an
        # observation, and its generated manifest location is intentionally ephemeral.
        if name not in {"collect", "validate-candidate"} and key not in self.retained:
            self.effects.append(name)
            self.retained[key] = response
        if name == "promote":
            self.state.update(release_id=NEW, predecessor=OLD)
        if name == self.change_at:
            self.state.update(release_id="release-" + "9" * 24, predecessor="release-" + "8" * 24)
        if name == self.interrupt_at:
            self.interrupt_at = None
            raise D.Halt("delivery-child-outcome-unavailable", verdict="uncertain")
        assert verdict in success, (name, verdict, success)
        return response

    def consumer_route(self):
        compiler = D.module(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
        return compiler.load_route(self.scope_path)[0]


class DeliveryTests(unittest.TestCase):
    def test_requalification_sequence_and_bounded_access_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("entity-smoke", directory); c = h.consumer()
            c.qualification = lambda: {"mode": "requalify"}
            calls = []
            c.deploy = lambda phase="update": calls.append(("deploy", phase))
            c.task = lambda name, phase: calls.append((name, phase))
            c.control = lambda name, phase=None: calls.append((name, phase))
            steps = list(c.steps())
            names = [name for name, _ in steps]
            self.assertEqual(len(names), 30)
            self.assertLess(names.index("credential-restore.operation"), names.index("credential-replacement"))
            self.assertLess(names.index("credential-replacement"), names.index("credential-read.preflight"))
            self.assertLess(names.index("credential-permissions.operation"), names.index("snapshot"))
            self.assertLess(names.index("snapshot"), names.index("restore-deployment"))
            self.assertLess(names.index("restore-read.operation"), names.index("restore-cleanup"))
            self.assertLess(names.index("restore-cleanup"), names.index("final-read.preflight"))
            self.assertNotIn("credential-unready.preflight", names)
            self.assertFalse(any("bootstrap" in name or "migrate" in name or "initial-stop" in name for name in names))
            for _, execute in steps: execute()
            self.assertEqual(len(calls), len(names))
            self.assertEqual(calls[-1], ("final-read", "operation"))
            aggregate = D.module(ROOT / c.directory / "acceptance-aggregate-test.py")
            fixture = aggregate.successor_fixture(c.K)
            delivery, binding = fixture["delivery"], fixture["binding"]
            c.context.values["proof_label"] = binding["proof_label"]
            c.release_context = lambda: (binding, delivery, Path(directory))
            self.assertEqual([n for n, _ in c.recovery_steps()], ["rollback", "rollback-read.preflight", "rollback-read.operation"])
            args = SimpleNamespace(proof_stage="credential-recovery", workload="administration",
                operation="revoke-runtime", phase="operation", proof_label=binding["proof_label"])
            key = c.K.T.STEPS.key(args, delivery)
            journal = Path(directory) / "task-attempts" / (key + ".json")
            journal.parent.mkdir(); journal.write_text("{}")
            # Existence schedules the original restore owner; it does not
            # validate a reservation or authorize replay/new role permissions.
            recovery = list(c.recovery_steps())
            self.assertEqual([n for n, _ in recovery], ["recovery-credential-restore.preflight",
                "recovery-credential-restore.operation", "rollback", "rollback-read.preflight", "rollback-read.operation"])
            calls.clear()
            for _, execute in recovery: execute()
            self.assertEqual(calls[:3], [("credential-restore", "preflight"), ("credential-restore", "operation"), ("deploy", "rollback")])

    def test_persistence_failure_uses_original_journal_receipt_and_deployment_time(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("core-server-persistence", directory); c = h.consumer(); V = c.verifier
            root = Path(directory); subprocess.run(["git", "init", "--quiet", str(root)], check=True)
            receipts = V.proof_receipts(); receipts.RECEIPTS = root / "proofs"
            V.ROOT = root
            V.proof_receipts = lambda: receipts
            definition = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-verifier:17"
            V.image_digest = lambda selected: PACKAGE["image_digest"] if selected == definition else "sha256:" + "e" * 64
            c.rollback_package = {**PACKAGE, "image_digest": "sha256:" + "e" * 64}
            task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "a" * 32,
                "taskDefinitionArn": definition, "startedBy": "kp-" + "a" * 32, "lastStatus": "STOPPED", "containers": [{"exitCode": 1}],
                "startedAt": "2026-11-19T10:00:00Z", "stoppedAt": "2026-11-19T10:00:02Z"}
            proof = receipts.make(proof_type="verifier", operation="read", task=task, image_digest=PACKAGE["image_digest"],
                result_code="private-persistence-verifier-unsuccessful-completion", controller="verify-candidate", collected_at="2026-11-19T10:00:03Z",
                context={"record_id": V.RECORD_ID, "completion_deadline_seconds": 120, "completion_duration_seconds": 2})
            path = receipts.persist(proof)
            value = {"schema": "deploy/private-persistence-verifier-operation/v1", "operation_id": task["startedBy"], "mode": "read", "predecessor": None,
                "task_arn": task["taskArn"], "proof_receipt": path.relative_to(root).as_posix(), "proof_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "request": {"task_definition": definition, "network": "fixture-private-network", "deadline_seconds": 120,
                    "overrides": {"containerOverrides": [{"name": "private-persistence-verifier", "environment": [
                        {"name": "PERSISTENCE_VERIFIER_MODE", "value": "read"}, {"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": V.RECORD_ID},
                        {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": V.FACT}]}]}}}
            journal, _ = V.operation_paths("read"); V.save_operation(journal, value)
            c.completed_transition = lambda **_: c.C.parsed_time("2026-11-19T09:59:00Z")
            selected = c.terminal_failure("rollback-final-read")
            error = D.Halt("delivery-child-not-successful", verdict="failed", evidence={"schema": "deploy/private-persistence-verification-report/v1", "facts": selected})
            self.assertTrue(c.confirm_failure("rollback-final-read", error))
            self.assertFalse(c.confirm_failure("collect", error))
            c.completed_transition = lambda **_: c.C.parsed_time("2026-11-19T10:01:00Z")
            with self.assertRaises(D.Halt) as failure: c.terminal_failure("rollback-final-read")
            self.assertEqual(failure.exception.condition, "delivery-terminal-evidence-mismatch")
            c.completed_transition = lambda **_: c.C.parsed_time("2026-11-19T09:59:00Z")
            # Recovery advances this same mode; original failure stays reachable.
            history = V.task_journal().directory(journal.parent, "history")
            V.save_operation(history / (value["operation_id"] + ".json"), value)
            replacement = {**value, "operation_id": "kp-" + "b" * 32, "predecessor": value["operation_id"],
                "request": {**value["request"], "task_definition": definition[:-2] + "18"}, "task_arn": None, "proof_receipt": None, "proof_sha256": None}
            V.save_operation(journal, replacement)
            self.assertEqual(c.terminal_failure("rollback-final-read"), selected)
            path.write_text("private-canary")
            with self.assertRaises(V.OperationError): c.terminal_failure("rollback-final-read")

    def test_persistence_completion_requires_exact_original_execution_event(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("core-server-persistence", directory); c = h.consumer()
            operation = "kp-" + "a" * 32
            c.transition = lambda **_: ("fixture", {}, SimpleNamespace(read=lambda *_: {"operation_id": operation}))
            event = {"PhysicalResourceId": "owned-stack", "ClientRequestToken": operation, "ResourceStatus": "UPDATE_COMPLETE", "Timestamp": "2026-11-19T10:00:00Z"}
            for defect in (None, "foreign", "pending", "missing"):
                selected = {**event}
                if defect == "foreign": selected["ClientRequestToken"] = "kp-" + "b" * 32
                if defect == "pending": selected["ResourceStatus"] = "UPDATE_IN_PROGRESS"
                def aws(*args):
                    if args[1] == "describe-stacks": return True, {"Stacks": [{"StackName": c.prepare.STACK, "StackId": "owned-stack"}]}, "ok"
                    self.assertEqual(args[1], "describe-stack-events")
                    return True, {"StackEvents": [] if defect == "missing" else [selected]}, "ok"
                c.prepare.aws = aws
                if defect:
                    with self.assertRaises(D.Halt) as failure: c.completed_transition()
                    self.assertEqual(failure.exception.condition, "delivery-deployment-completion-required")
                else: self.assertEqual(c.completed_transition(), c.C.parsed_time(event["Timestamp"]))

    def test_release_approval_binds_inputs_sources_packages_and_predecessor(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("entity-smoke", directory)
            c = h.consumer(); ctx = c.context
            ctx.root = Path(directory)
            source = ctx.root / "scripts/04.deploy/controller.py"
            source.parent.mkdir(parents=True); source.write_text("original")
            approved = D.fingerprint(ctx.release_boundary(c))
            ctx.authorize(c, approved)
            D.Context.check_authority(ctx)
            with self.assertRaises(D.Halt) as failure: ctx.authorize(c, "sha256:" + "0" * 64)
            self.assertEqual(failure.exception.condition, "delivery-release-approval-mismatch")
            source.write_text("changed")
            with self.assertRaises(D.Halt) as failure: D.Context.check_authority(ctx)
            self.assertEqual(failure.exception.condition, "delivery-release-approval-changed")
            source.write_text("original")
            h.state["release_id"] = "release-" + "9" * 24
            with self.assertRaises(D.Halt): D.Context.check_authority(ctx)
            self.assertEqual(h.effects, [])

    def recovery_harness(self, scope, directory):
        h = Harness(scope, directory)
        c = h.consumer()
        if scope == "entity-smoke":
            h.fail_at = "baseline/verifier/lifecycle/operation"
            marker = {"operation_id": "es-" + "a" * 32}
            h.failure_evidence = {"schema": "deploy/entity-smoke-task-report/v1", "terminal_failure": marker}
            c.terminal_failure = lambda stage: marker if stage == "lifecycle.operation" else None
        else:
            h.fail_at = "read"
            marker = {"operation_id": "kp-" + "a" * 32, "proof_receipt": "fixture", "proof_sha256": "a" * 64, "mode": "read"}
            h.failure_evidence = {"schema": "deploy/private-persistence-verification-report/v1", "facts": marker}
            c.terminal_failure = lambda stage: marker if stage == "rollback-final-read" else None
            def recovery_proof(name):
                # Actual declared commands, with controlled original head lookup.
                key = "rollback_b_health_predecessor" if name.endswith("health") else "rollback_b_read_predecessor"
                old = h.fail_at; h.fail_at = None
                try: c.context.command(name, {"accepted"}, **{key: "kp-" + "a" * 32})
                finally: h.fail_at = old
            c.recovery_proof = recovery_proof
        c.pending_recovery = lambda: D.Halt("delivery-candidate-verification-failed", verdict="failed") if "rollback" in h.effects else None
        return h, c

    def test_exact_failed_verification_restores_without_accepting_candidate(self):
        for scope in ("entity-smoke", "core-server-persistence"):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as directory:
                h, c = self.recovery_harness(scope, directory)
                result = D.continue_update(c)
                self.assertEqual(result.get("recovery"), "restored", result)
                self.assertEqual(result["verdict"], "failed")
                self.assertEqual(result["release_id"], OLD)
                self.assertTrue(result["current_readiness"])
                self.assertNotIn("promote", h.calls)
                before = list(h.effects)
                result = D.continue_update(c)
                self.assertEqual(result.get("recovery"), "restored", result)
                self.assertEqual(before, h.effects)
                self.assertEqual(h.calls.count("deploy"), 1)

    def test_uncertain_blocked_generic_or_wrong_evidence_cannot_restore(self):
        for scope in ("entity-smoke", "core-server-persistence"):
            for defect in ("pending", "uncertain", "blocked", "missing", "wrong-identity", "collection"):
                with self.subTest(scope=scope, defect=defect), tempfile.TemporaryDirectory() as directory:
                    h, c = self.recovery_harness(scope, directory)
                    if defect in {"pending", "uncertain", "blocked"}: h.failure_verdict = defect
                    elif defect == "missing": h.failure_evidence = None
                    elif defect == "wrong-identity": c.terminal_failure = lambda _: {"operation_id": "wrong"}
                    else: h.fail_at = "collect"
                    result = D.continue_update(c)
                    self.assertNotIn("recovery", result, result)
                    self.assertNotIn("rollback", h.effects)
                    self.assertEqual(h.state["release_id"], OLD)

    def test_interrupted_recovery_reconciles_without_redeploying_candidate(self):
        for scope in ("entity-smoke", "core-server-persistence"):
            names = ["rollback", "rollback/verifier/read/preflight", "rollback/verifier/read/operation"] if scope == "entity-smoke" else ["rollback", "health-ready", "read"]
            for name in names:
                with self.subTest(scope=scope, name=name), tempfile.TemporaryDirectory() as directory:
                    h, c = self.recovery_harness(scope, directory)
                    h.interrupt_at = name
                    result = D.continue_update(c)
                    self.assertEqual(result.get("recovery"), "incomplete", result)
                    self.assertEqual(result["candidate_verdict"], "failed")
                    result = D.continue_update(c)
                    self.assertEqual(result.get("recovery"), "restored", result)
                    self.assertEqual(h.calls.count("deploy"), 1)
                    self.assertEqual(h.effects.count("rollback"), 1)
                    self.assertNotIn("promote", h.effects)

    def test_both_actual_bindings_and_real_command_parsers(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as directory:
                h = Harness(scope, directory, parse=True)
                result = D.continue_update(h.consumer())
                self.assertEqual(result["verdict"], "accepted", result)
                self.assertEqual(result["completed"][-3:], ["collect", "validate-candidate", "promote"])
                self.assertEqual(result["delivery_budget"], "not-established")
                before = list(h.effects)
                result = D.continue_update(h.consumer())
                self.assertEqual(result["verdict"], "retained", result)
                self.assertFalse(result["current_readiness"])
                self.assertEqual(h.effects, before)
                if scope == "core-server-persistence":
                    self.assertEqual(set(h.last_manifest["values"]["proof_receipts"]), set(h.collector.updates().policy(h.collector.owner())["fresh_tasks"]))
                else:
                    self.assertEqual(len([name for name in h.calls if name.endswith(("/operation", "/preflight"))]), 10)

    def test_interruption_at_each_child_boundary_resumes_original_operations(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            with tempfile.TemporaryDirectory() as directory:
                baseline = Harness(scope, directory)
                self.assertEqual(D.continue_update(baseline.consumer())["verdict"], "accepted")
                names = [name for name in baseline.calls if name != "admission"]
            for name in names:
                with self.subTest(scope=scope, stage=name), tempfile.TemporaryDirectory() as directory:
                    h = Harness(scope, directory); h.interrupt_at = name
                    result = D.continue_update(h.consumer())
                    self.assertEqual(result["verdict"], "uncertain", result)
                    result = D.continue_update(h.consumer())
                    self.assertIn(result["verdict"], {"accepted", "retained"}, result)
                    self.assertEqual(len(h.effects), len(set(h.effects)))

    def test_failed_and_changed_predecessor_never_promote(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            for mode in ("fail_at", "change_at"):
                with self.subTest(scope=scope, mode=mode), tempfile.TemporaryDirectory() as directory:
                    h = Harness(scope, directory); setattr(h, mode, "deploy")
                    result = D.continue_update(h.consumer())
                    self.assertNotIn(result["verdict"], {"accepted", "retained"})
                    self.assertNotIn("promote", h.calls)
                    if mode == "fail_at":
                        self.assertEqual(result["reasons"], ["fixture-task-failed"])
                        self.assertEqual(h.state["release_id"], OLD)

    def test_failed_final_checks_never_accept(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            for stage in ("collect", "validate-candidate", "promote"):
                with self.subTest(scope=scope, stage=stage), tempfile.TemporaryDirectory() as directory:
                    h = Harness(scope, directory); h.fail_at = stage
                    result = D.continue_update(h.consumer())
                    self.assertEqual(result["verdict"], "failed", result)
                    self.assertEqual(h.state["release_id"], OLD)
                    self.assertEqual(result["stage"], stage)
                    self.assertEqual(result["next_action"], "inspect-failure-and-select-authorised-recovery")

    def test_input_classification_and_route_owner_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for contents, expected in ((None, "delivery-input-missing"), ("", "delivery-input-empty"),
                                       ("{", "delivery-input-json-invalid"), ("[]", "delivery-input-shape-invalid"),
                                       ("x" * 65537, "delivery-input-too-large")):
                if contents is not None: path.write_text(contents)
                with self.assertRaises(D.Halt) as raised: D.read(path)
                self.assertEqual(raised.exception.condition, expected)
        compiler = D.module(ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
        for scope in ("core-server-persistence", "entity-smoke"):
            selected = TARGET / "20-scopes" / scope / "00-declaration/declaration-contract.yml"
            original = compiler.load_route
            route, path = original(selected)
            checked = compiler.inspect(selected)
            self.assertEqual(checked["verdict"], "covered", checked["findings"])
            self.assertIn("scripts/04.deploy/lifecycle/60-run/release-succession/ordinary-update.sh", checked["references"])
            compiler.load_route = lambda *_: ({**route, "ordinary_delivery": {**route["ordinary_delivery"], "owner": "wrong-owner"}}, path)
            self.assertIn("acceptance-route-delivery-owner-invalid", [f["code"] for f in compiler.inspect(selected, probe_commands=False)["findings"]])
            compiler.load_route = original
            for link in (None, "undeclared-command", 42, []):
                changed = copy.deepcopy(route)
                if link is None: changed["ordinary_delivery"].pop("command")
                else: changed["ordinary_delivery"]["command"] = link
                with patch.object(compiler, "load_route", return_value=(changed, path)):
                    self.assertIn("acceptance-route-delivery-owner-invalid",
                                  [f["code"] for f in compiler.inspect(selected, probe_commands=False)["findings"]])
            for field, value in (("owner", "wrong-owner"), ("effects", ["read-only"])):
                changed = copy.deepcopy(route)
                changed["commands"][route["ordinary_delivery"]["command"]][field] = value
                with patch.object(compiler, "load_route", return_value=(changed, path)):
                    self.assertIn("acceptance-route-command-owner-or-effects-mismatch",
                                  [f["code"] for f in compiler.inspect(selected, probe_commands=False)["findings"]])

    def test_noncanonical_scope_rejected_before_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for scope in (root / "nested/../scope.yml", root / "../outside.yml"):
                output = io.StringIO()
                with patch.object(D, "ROOT", root), patch.object(sys, "argv", ["ordinary-update", "--scope-contract", str(scope),
                        "--inputs", str(root / "unused.json"), "--execute"]), contextlib.redirect_stdout(output):
                    self.assertEqual(D.main(), 1)
                self.assertEqual(json.loads(output.getvalue())["condition"], "delivery-scope-invalid")

    def test_custody_and_input_changes_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("core-server-persistence", directory)
            c = h.consumer()
            h.state.update(release_id=NEW, predecessor=OLD)
            c.context.accepted_package = lambda _: {**PACKAGE, "receipt_reference": "different-custody"}
            self.assertEqual(D.continue_update(c)["condition"], "delivery-predecessor-changed")
            self.assertEqual(h.calls, [])
            c = h.consumer(); h.receipt.write_text("{}")
            self.assertEqual(D.continue_update(c)["condition"], "delivery-input-changed")
            self.assertEqual(h.calls, [])

    def test_child_reports_and_sensitive_output(self):
        canary = "private-secret-canary"
        for code, output in ((0, canary), (1, json.dumps({"schema": "deploy/test/v1", "verdict": "accepted"})),
                             (0, json.dumps({"schema": "deploy/test/v1", "verdict": "pending"}))):
            with patch.object(D.subprocess, "run", return_value=SimpleNamespace(returncode=code, stdout=output, stderr=canary)):
                with self.assertRaises(D.Halt) as raised:
                    D.invoke(["fixture"], {"accepted"})
                self.assertNotIn(canary, str(vars(raised.exception)))
        class OwnedFailure(Exception): pass
        with self.assertRaises(D.Halt) as raised:
            D.owned_call(lambda: (_ for _ in ()).throw(OwnedFailure("acceptance-recovery-requalification-required")), (OwnedFailure,))
        self.assertEqual(raised.exception.condition, "acceptance-recovery-requalification-required")
        with self.assertRaises(RuntimeError):
            D.owned_call(lambda: (_ for _ in ()).throw(RuntimeError(canary)), (OwnedFailure,))

    def test_changed_release_authority_does_not_submit_task(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("entity-smoke", directory)
            c = h.consumer()
            calls = []
            def authority():
                calls.append(True)
                if len(calls) == 3: raise D.Halt("delivery-release-approval-changed")
            c.context.check_authority = authority
            result = D.continue_update(c)
            self.assertEqual(result["condition"], "delivery-release-approval-changed")
            self.assertEqual(h.effects, ["deploy"])
            self.assertNotIn("promote", h.calls)

    def test_owner_failure_meaning_survives_without_native_details(self):
        with tempfile.TemporaryDirectory() as directory:
            h = Harness("core-server-persistence", directory); c = h.consumer()
            for error, expected in ((c.verifier.OperationError("private-persistence-verifier-terminal-proof-unavailable"), "private-persistence-verifier-terminal-proof-unavailable"),
                                    (RuntimeError("private-secret-canary"), "delivery-boundary-not-confirmed")):
                c.admit = lambda: (_ for _ in ()).throw(error)
                result = D.continue_update(c)
                self.assertEqual(result["condition"], expected)
                self.assertEqual(result["verdict"], "uncertain")
                self.assertNotIn("private-secret-canary", json.dumps(result))
                self.assertEqual(h.effects, [])


if __name__ == "__main__":
    unittest.main()
