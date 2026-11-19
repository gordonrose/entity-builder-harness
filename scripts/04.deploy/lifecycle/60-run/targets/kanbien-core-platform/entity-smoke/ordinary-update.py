#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.binding.entity-smoke-ordinary-update
#   version: 3
#   status: draft
#   created_on: "2026-11-19"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind the shared update sequence to existing feature task identities and exact plan approvals.
#   portability: {class: internal, targets: []}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.entity-smoke.acceptance-route
#     path: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/acceptance-route-contract.yml
import importlib.util
from pathlib import Path
import re
from types import SimpleNamespace


def collector():
    path = Path(__file__).with_name("acceptance-route.py")
    spec = importlib.util.spec_from_file_location("delivery_feature_collector", path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


class Consumer:
    def __init__(self, context, halt, require):
        self.context, self.halt, self.require = context, halt, require
        self.K = collector()
        values = context.values
        require(set(values) == {"candidate_receipt", "expected_predecessor", "proof_label", "expected_digest",
            "rollback_receipt", "rollback_compatibility_id"}, "delivery-values-invalid")
        context.package = context.owned(lambda: self.K.C.ALIGN.read_receipt(context.package_path()), (self.K.C.ALIGN.AlignmentFailure,))
        context.accepted_package = self.accepted_package
        self.receipt = str(context.package_path())
        self.rollback = context.retain_input(context.path(values["rollback_receipt"]))
        self.rollback_package = context.owned(lambda: self.K.C.ALIGN.read_receipt(self.rollback), (self.K.C.ALIGN.AlignmentFailure,))
        require(all(isinstance(values[k], str) for k in ("proof_label", "expected_digest", "rollback_compatibility_id"))
            and re.fullmatch(r"entity-smoke-[a-f0-9]{24}", values["proof_label"]) is not None
            and re.fullmatch(r"[a-f0-9]{64}", values["expected_digest"]) is not None, "delivery-record-binding-invalid")
        self.common = ["--receipt", self.receipt, "--proof-label", values["proof_label"], "--expected-predecessor", context.expected]
        self.directory = Path(__file__).parent.relative_to(context.root).as_posix()
        self.inputs, self.candidate = None, None

    def release_effects(self):
        C, ctx = self.K.C, self.context
        previous, _ = ctx.succession.history_record_for_id(ctx.evidence_root, ctx.expected)
        self.require(all(self.rollback_package[k] == previous["release"][k] for k in ("source_revision", "image_digest")), "delivery-rollback-package-mismatch")
        result = {"account": C.ALIGN.ACCOUNT, "region": C.ALIGN.REGION, "rollback_package": self.rollback_package,
            "operations": ["update", *[n + "." + p for n in self.K.SUCCESSOR_TASKS for p in ("preflight", "operation")], "rollback", "rollback-read.preflight", "rollback-read.operation"],
            "protected_resources": "database-schema-data-permissions-and-other-scopes", "recovery": "exact-accepted-predecessor-only"}
        requirements = self.qualification()
        if requirements.get("mode") == "requalify":
            result.update(recovery_requirements=requirements,
                operations=[name for name, _ in self.steps()] + ["rollback", "rollback-read.preflight", "rollback-read.operation"],
                protected_resources="source-database-data-schema-original-record-source-snapshots-and-other-scopes",
                recovery_proof={"runtime_access": "revoke-and-restore-only-feature-role", "maximum_server_replacements": 1,
                    "maximum_source_snapshots": 1, "disposable_restore_resources": 8, "cleanup": "owned-clone-only-after-original-readback"})
        return result

    def qualification(self):
        binding, delivery, _ = self.release_context()
        return self.context.owned(lambda: self.K.successor_admission(delivery, binding),
            (self.K.CollectionFailure, self.K.A.POLICY.PolicyFailure,))["applicability"]

    def failure_code(self, error):
        return self.K.failure_details(error)["condition"]

    def release_context(self):
        if getattr(self, "_release_context", None) is not None: return self._release_context
        C, ctx = self.K.C, self.context
        provider = C.Provider()
        alignment, _, _ = C.ALIGN.inspect(provider, ctx.package, C.now())
        binding = {**C.binding_for(ctx.package, alignment), "proof_label": ctx.values["proof_label"]}
        args = SimpleNamespace(expected_predecessor=ctx.expected, rollback_receipt=self.rollback,
                               rollback_compatibility_id=ctx.values["rollback_compatibility_id"])
        delivery = C.delivery_context(args, ctx.package, binding)
        # Pin the invocation's release identity once. Every child still performs
        # its fresh source/dependency/provider gates; drift cannot change intent.
        self._release_context = binding, delivery, C.delivery_cache(ctx.values["proof_label"], delivery)
        return self._release_context

    def approved_plan(self, report, *, phase=None, selection=None):
        C, ctx = self.K.C, self.context
        ctx.check_authority()
        plan = report.get("plan")
        self.require(isinstance(plan, dict) and C.DEPLOY.fingerprint(plan) == report.get("plan_sha256"), "delivery-plan-invalid")
        binding, delivery, _ = self.release_context()
        self.require(all(plan.get(k) == v for k, v in {"target": ctx.route["target"], "scope": ctx.route["scope"],
            "account": C.ALIGN.ACCOUNT, "region": C.ALIGN.REGION, "delivery": delivery,
            "package_custody_reference": ctx.package["receipt_reference"], "controller_sha256": C.source_digest()}.items()), "delivery-plan-outside-approval")
        if phase == "rollback" or selection and selection[0] == "rollback":
            binding, _ = C.rollback_selection(SimpleNamespace(rollback_receipt=self.rollback,
                rollback_compatibility_id=ctx.values["rollback_compatibility_id"]), delivery, binding)
        self.require(plan.get("binding") == binding, "delivery-plan-outside-approval")
        if phase:
            self.require(plan.get("schema") == "deploy/entity-smoke-infrastructure-plan/v2" and plan.get("phase") == phase
                and all(type(plan.get(k)) is int and plan[k] == v for k, v in {"resource_additions": 0, "resource_modifications": 1,
                    "resource_replacements": 5, "server_desired_count": 1, "baseline_database_ingress_additions": 0, "baseline_endpoint_ingress_additions": 0}.items())
                and all(plan.get(k) is False for k in ("database_data_or_schema_changes", "source_database_replacement", "automatic_rollback"))
                and plan.get("rollback_compatibility", {}).get("compatibility_id") == ctx.values["rollback_compatibility_id"], "delivery-plan-outside-approval")
        else:
            stage, workload, operation, step = selection
            actual = ("ready" if workload == "verifier" else "preflight") if step == "preflight" else operation
            self.require(plan.get("schema") == "deploy/entity-smoke-task-plan/v2"
                and all(plan.get(k) == v for k, v in {"proof_stage": stage, "workload": workload, "prepared_operation": operation,
                    "operation": actual, "phase": step, "database_effect": self.K.T.EFFECTS[actual], "expected_record_digest": ctx.values["expected_digest"],
                    "task_count": 1, "automatic_retry": False, "execution_route_available": True, "pending_prerequisite": None}.items()), "delivery-plan-outside-approval")
        return report["plan_sha256"]

    def admit(self):
        # Full recovery applicability and compatibility remain checked by the
        # existing deployment controller before any provider submission.
        self.context.owned(lambda: self.K.C.parse(["--mode", "apply", "--phase", "update", *self.common,
            "--approved-plan", "sha256:" + "0" * 64, "--rollback-receipt", str(self.rollback),
            "--rollback-compatibility-id", self.context.values["rollback_compatibility_id"]]), (self.K.C.InfrastructureFailure,))

    def accepted_package(self, state):
        K, ctx = self.K, self.context
        owner = K.module("delivery_feature_state", Path(__file__).with_name("acceptance-state.py"))
        retained = ctx.owned(lambda: owner.State().current(), (owner.StateFailure, owner.K.CollectionFailure))
        self.require(retained["reference"] == state and retained["packet"]["binding"]["proof_label"] == ctx.values["proof_label"]
            and retained["packet"]["binding"]["record_digest"] == ctx.values["expected_digest"], "delivery-record-custody-mismatch")
        return retained["packet"]["package"]

    def deploy(self, phase="update"):
        ctx = self.context
        argv = ["bash", self.directory + "/script.sh", "--phase", phase, *self.common,
            "--rollback-receipt", str(self.rollback), "--rollback-compatibility-id", ctx.values["rollback_compatibility_id"], "--json"]
        _, _, cache = self.release_context()
        path = cache / "plans" / (phase + ".json")
        # Original admitted plan is the resume identity; current observations
        # may no longer describe the pre-update state. The owner revalidates it.
        plan = self.K.C.read_json(path) if path.exists() else None
        report = {"plan": plan, "plan_sha256": self.K.C.DEPLOY.fingerprint(plan)} if plan else ctx.runner([*argv, "--mode", "plan"], {"planned"}, root=ctx.root)
        approved = self.approved_plan(report, phase=phase)
        ctx.runner([*argv, "--mode", "apply", "--approved-plan", approved], {"completed"}, root=ctx.root)

    def task(self, name, phase):
        ctx = self.context
        stage, workload, operations = ("rollback", "verifier", ["read"]) if name == "rollback-read" else self.K.A.TASKS[name]
        self.require(len(operations) == 1, "delivery-task-selection-invalid")
        argv = [*self.common, "--proof-stage", stage,
            "--workload", workload, "--operation", operations[0], "--phase", phase,
            "--expected-digest", ctx.values["expected_digest"], "--json"]
        if stage == "rollback": argv += ["--rollback-receipt", str(self.rollback), "--rollback-compatibility-id", ctx.values["rollback_compatibility_id"]]
        report = ctx.runner(["bash", self.directory + "/task-plan.sh", *argv], {"planned"}, root=ctx.root)
        approved = self.approved_plan(report, selection=(stage, workload, operations[0], phase))
        ctx.runner(["bash", self.directory + "/task-execute.sh", *argv, "--approved-plan", approved], {"completed"}, root=ctx.root)

    def control(self, name, phase=None):
        """Use the original proof owners and their exact plans/reservations."""
        K, ctx = self.K, self.context
        binding, delivery, _ = self.release_context()
        original = {**binding, "record_digest": ctx.values["expected_digest"]}
        resource_binding = K.C.RESOURCE.recovery_binding(original, delivery)
        wrapper = {"credential-replacement": "replacement", "snapshot": "snapshot", "restore-deployment": "restore", "restore-cleanup": "restore", "restore-read": "restore-reader"}[name]
        argv = ["bash", self.directory + "/" + wrapper + ".sh", *self.common, "--expected-digest", ctx.values["expected_digest"], "--json"]
        if name == "credential-replacement": argv += ["--proof-stage", "credential-recovery"]
        if name.startswith("restore-"): argv += ["--phase", phase if name == "restore-read" else "deploy" if name == "restore-deployment" else "cleanup"]
        report = ctx.runner([*argv, "--mode", "plan"], {"planned"}, root=ctx.root)
        plan = report.get("plan")
        ctx.check_authority()
        self.require(isinstance(plan, dict) and K.C.DEPLOY.fingerprint(plan) == report.get("plan_sha256")
            and plan.get("controller_sha256") == K.C.source_digest()
            and plan.get("package_custody_reference") == ctx.package["receipt_reference"], "delivery-plan-outside-approval")
        if name == "restore-read":
            # Reader access is bound to the positively owned clone by its owner;
            # source incarnation/permissions must never pass as clone access.
            child = plan.get("binding", {})
            self.require(plan.get("schema") == "deploy/entity-smoke-restore-reader-plan/v1"
                and all(child.get(k) == original[k] for k in ("source_revision", "image_digest", "configuration_contract_sha256", "proof_label"))
                and child.get("dependency_incarnation_sha256") != binding["dependency_incarnation_sha256"]
                and child.get("permission_contract_sha256") == K.C.digest_file(K.D.RESTORE.SOURCE)
                and plan.get("expected_record_digest") == ctx.values["expected_digest"]
                and plan.get("phase") == phase and plan.get("task_count") == 1
                and all(plan.get(k) is False for k in ("source_mutation", "scope_acceptance", "automatic_retry")), "delivery-plan-outside-approval")
        else:
            ctx.owned(lambda: K.CONTROL.validate_plan(K.A, name, plan, original if name == "credential-replacement" else resource_binding), (K.CONTROL.ControlFailure, K.C.RESOURCE.ResourceFailure))
        approved = report["plan_sha256"]
        if name == "restore-deployment":
            ctx.runner([*argv, "--mode", "review", "--approved-plan", approved], {"completed"}, root=ctx.root)
        ctx.runner([*argv, "--mode", "execute", "--approved-plan", approved], {"completed"}, root=ctx.root)

    def terminal_failure(self, stage):
        """Reobserve the exact original reservation, without a launch capability."""
        name, phase = stage.rsplit(".", 1)
        tasks = getattr(self.K, "REQUALIFICATION_TASKS", self.K.SUCCESSOR_TASKS)
        if name not in tasks or name == "restore-read" or phase not in {"preflight", "operation"}: return None
        C, ctx = self.K.C, self.context
        T = self.K.T
        binding, delivery, cache = self.release_context()
        deployed = C.validate_deployment_receipt(C.read_json(cache / "receipts/update.json"), binding, delivery)
        proof_stage, workload, operations = self.K.A.TASKS[name]
        args = SimpleNamespace(proof_stage=proof_stage, workload=workload, operation=operations[0], phase=phase, proof_label=ctx.values["proof_label"])
        key = T.STEPS.key(args, delivery)
        label = C.delivery_preflight_label(delivery, proof_stage, workload, operations[0]) if phase == "preflight" else C.delivery_operation_label(delivery, workload, operations[0])
        filename = label + "-" + workload + "-preflight" if phase == "preflight" else label + "-lifecycle" if operations[0] == "lifecycle" else key
        path = cache / "task-attempts" / (filename + ".json")
        if not path.exists(): return None
        reservation = C.read_json(path)
        request = reservation["request"]
        store = T.RUNNER.CONTROL.AttemptStore(cache / "task-attempts")
        self.require(store.read(key, request) == reservation and store.path_for(key, request) == path
            and all(request.get(k) == v for k, v in binding.items() if k != "proof_label") and request["workload"] == workload and request["proof_label"] == label
            and request["environment"][T.RUNNER.CONTROL.OPERATIONS[workload][0]] == (("ready" if workload == "verifier" else "preflight") if phase == "preflight" else operations[0]), "delivery-terminal-evidence-mismatch")
        logical = {"verifier": "VerifierTaskDefinition", "database-proof": "DatabaseProofTaskDefinition", "administration": "AdministrationTaskDefinition"}[workload]
        self.require(request["definition"] == deployed["result"]["facts"]["resources"][logical]["physical_id"]
            and T.RUNNER.EVIDENCE.timestamp(reservation["reserved_at"]) >= T.RUNNER.EVIDENCE.timestamp(deployed["result"]["facts"]["completed_at"]), "delivery-terminal-evidence-mismatch")
        try:
            options = {}
            if operations[0] == "unready":
                options["revocation"] = C.read_json(T.RUNNER.UNREADY.path_for(cache / "task-receipts", reservation))["revocation"]
            T.RUNNER.run_owned_task(T.Provider(), store, key, request, cache / "task-receipts", required_after=deployed["result"]["facts"]["completed_at"], **options)
        except T.RUNNER.EVIDENCE.TerminalTaskFailure as failure:
            return failure.terminal
        return None

    def confirm_failure(self, stage, error):
        tasks = getattr(self.K, "REQUALIFICATION_TASKS", self.K.SUCCESSOR_TASKS)
        if stage not in {n + "." + p for n in tasks if n != "restore-read" for p in ("preflight", "operation")}: return False
        report = error.evidence
        if not isinstance(report, dict) or report.get("schema") != "deploy/entity-smoke-task-report/v1" or not isinstance(report.get("terminal_failure"), dict): return False
        return self.terminal_failure(stage) == report["terminal_failure"]

    def pending_recovery(self):
        _, _, cache = self.release_context()
        if not (cache / "plans/rollback.json").exists(): return None
        for name in getattr(self.K, "REQUALIFICATION_TASKS", self.K.SUCCESSOR_TASKS):
            if name == "restore-read": continue
            for phase in ("preflight", "operation"):
                if self.terminal_failure(name + "." + phase) is not None:
                    return self.halt("delivery-candidate-verification-failed", verdict="failed")
        raise self.halt("delivery-recovery-evidence-required")

    def recovery_steps(self):
        # An image rollback cannot repair deliberately revoked database access.
        # Restore only the original bounded role operation, before rolling back.
        if self.qualification().get("mode") == "requalify":
            _, delivery, cache = self.release_context()
            args = SimpleNamespace(proof_stage="credential-recovery", workload="administration", operation="revoke-runtime",
                phase="operation", proof_label=self.context.values["proof_label"])
            key = self.K.T.STEPS.key(args, delivery)
            if (cache / "task-attempts" / (key + ".json")).exists():
                for phase in ("preflight", "operation"):
                    yield "recovery-credential-restore." + phase, lambda phase=phase: self.task("credential-restore", phase)
        yield "rollback", lambda: self.deploy("rollback")
        for phase in ("preflight", "operation"):
            yield "rollback-read." + phase, lambda phase=phase: self.task("rollback-read", phase)

    def collect(self, directory):
        ctx = self.context
        self.inputs = ctx.manifest({key: str(ctx.package_path()) if key == "candidate_receipt" else ctx.values[key]
            for key in ("candidate_receipt", "expected_predecessor", "proof_label", "expected_digest")}, directory, ordinary=False)
        result = ctx.command("collect", {"collected", "retained"}, acceptance_inputs=self.inputs)
        self.candidate = result.get("candidate_record")
        self.require(isinstance(self.candidate, str), "delivery-candidate-reference-missing")
        return self.candidate, self.inputs

    def steps(self):
        yield "deploy", self.deploy
        requalify = self.qualification().get("mode") == "requalify"
        for name in (self.K.REQUALIFICATION_TASKS if requalify else self.K.SUCCESSOR_TASKS):
            if name == "credential-read":
                yield "credential-replacement", lambda: self.control("credential-replacement")
            if name == "restore-read":
                yield "snapshot", lambda: self.control("snapshot")
                yield "restore-deployment", lambda: self.control("restore-deployment")
            if requalify and name == "final-read":
                yield "restore-cleanup", lambda: self.control("restore-cleanup")
            for phase in (("operation",) if name == "credential-unready" else ("preflight", "operation")):
                operation = self.control if name == "restore-read" else self.task
                yield name + "." + phase, lambda name=name, phase=phase, operation=operation: operation(name, phase)
