#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.binding.persistence-ordinary-update
#   version: 2
#   status: draft
#   created_on: "2026-11-19"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind the shared update sequence to existing persistence command and proof contracts.
#   portability: {class: internal, targets: []}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.core-server-persistence.acceptance-route
#     path: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/acceptance-route-contract.yml
import importlib.util
from pathlib import Path
import re


def collector():
    path = Path(__file__).with_name("collect-acceptance-evidence") / "script.py"
    spec = importlib.util.spec_from_file_location("delivery_persistence_collector", path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


class Consumer:
    def __init__(self, context, halt, require):
        self.context, self.halt, self.require = context, halt, require
        self.C = collector()
        values = context.values
        require(set(values) == {"candidate_receipt", "expected_predecessor", "delivery_label", "operation_predecessors", "rollback_receipt", "rollback_compatibility_id"}, "delivery-values-invalid")
        require(isinstance(values["delivery_label"], str) and re.fullmatch(r"[a-z][a-z0-9-]{0,23}", values["delivery_label"]), "delivery-label-invalid")
        context.package = context.owned(lambda: self.C.receipt(context.package_path()), (self.C.EvidenceFailure,))
        context.accepted_package = self.accepted_package
        self.rollback = context.retain_input(context.path(values["rollback_receipt"]))
        self.rollback_package = context.owned(lambda: self.C.receipt(self.rollback), (self.C.EvidenceFailure,))
        self.prepare = self.load(context.root / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py")
        self.verifier = self.load(Path(__file__).with_name("verify-candidate") / "script.py")
        self.policy = self.C.updates().policy(self.C.owner())
        self.proofs = self.policy["fresh_tasks"]
        commands = [context.route["proofs"][name]["command"] for name in self.proofs] + ["current-health"]
        needed = {item[1:-1] for name in commands for item in context.route["commands"][name]["argv"] if item.endswith("_predecessor}")}
        supplied = values["operation_predecessors"]
        require(isinstance(supplied, dict) and set(supplied) == needed
                and all(isinstance(v, str) and (v == "none" or re.fullmatch(r"kp-[a-f0-9]{32}", v)) for v in supplied.values()), "delivery-operation-predecessors-invalid")
        self.arguments = {**supplied, "candidate_receipt": str(context.package_path())}
        self.receipts, self.health, self.inputs, self.candidate = {}, None, None, None

    @staticmethod
    def load(path):
        spec = importlib.util.spec_from_file_location("delivery_" + path.parent.name, path)
        value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
        return value

    def release_effects(self):
        ctx = self.context
        prior, _ = ctx.succession.history_record_for_id(ctx.evidence_root, ctx.expected)
        self.require(all(self.rollback_package[k] == prior["release"][k] for k in ("source_revision", "image_digest")), "delivery-rollback-package-mismatch")
        return {"account": self.C.ACCOUNT, "region": self.C.REGION, "rollback_package": self.rollback_package,
            "operations": ["update", *self.proofs, "readiness", "rollback", "rollback-b-health", "rollback-b-read"],
            "protected_resources": "database-schema-data-permissions-and-other-scopes", "recovery": "exact-accepted-predecessor-only"}

    def failure_code(self, error):
        if isinstance(error, (self.C.EvidenceFailure, self.verifier.OperationError, self.context.succession.SuccessionFailure)):
            return str(error)
        if isinstance(error, (self.prepare.update_operations().OperationFailure, self.prepare.update_operations().RESERVATIONS.ReservationFailure)):
            return error.code
        return "delivery-boundary-not-confirmed"

    def admit(self):
        C, ctx = self.C, self.context
        self.require(self.prepare.rollback_compatibility(self.rollback_package, ctx.values["rollback_compatibility_id"]), "delivery-rollback-compatibility-required")
        _, compatibility = ctx.owned(lambda: ctx.succession.compatibility_record(ctx.evidence_root, ctx.values["rollback_compatibility_id"]), (ctx.succession.SuccessionFailure,))
        self.require(compatibility["identity"].get("historical_release_id") == ctx.expected, "delivery-rollback-predecessor-mismatch")
        previous, _ = ctx.owned(lambda: C.updates().accepted(C.owner(), ctx.expected), (C.EvidenceFailure,))
        qualification = previous["qualification"]
        S = ctx.succession
        current = {**qualification["binding"], "source_revision": ctx.package["source_revision"],
            "configuration_contract_sha256": S.sha256_bytes(C.scope_contract().read_bytes()),
            "permission_contract_sha256": S.sha256_bytes((C.ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml").read_bytes())}
        self.require(qualification["input_paths"] == self.policy["recovery_input_paths"], "delivery-requalification-required")
        policy = ctx.compiler.proof_policy()
        ctx.owned(lambda: policy.recovery_applicability(qualification["binding"], current,
            self.policy["recovery_input_paths"], root=ctx.root), (policy.PolicyFailure,))

    def accepted_package(self, state):
        record, _ = self.context.owned(lambda: self.C.updates().accepted(self.C.owner(), state["release_id"]), (self.C.EvidenceFailure,))
        self.require(record["schema"] == self.C.updates().SCHEMA, "delivery-successor-record-required")
        return record["release"]

    def deploy(self, *, rollback=False):
        ctx = self.context
        script = "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.sh"
        argv = ["bash", script, "--receipt", str(self.rollback if rollback else ctx.package_path()), "--operation", "rollback" if rollback else "update",
            "--operation-label", ctx.values["delivery_label"], "--json"]
        if rollback: argv += ["--support-receipt", str(ctx.package_path()), "--rollback-compatibility-id", ctx.values["rollback_compatibility_id"]]
        ctx.runner(argv, {"transitioned"}, root=ctx.root)

    def transition(self, rollback=False):
        ctx, P = self.context, self.prepare
        package = self.rollback_package if rollback else ctx.package
        phase = "rollback" if rollback else "update"
        name = P.labelled_update_name("kanbien-core-platform-persistence-" + phase + "-" + package["image_digest"][7:19], ctx.values["delivery_label"])
        request = P.update_request(name=name, receipt=package,
            controller=ctx.root / "scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/transition-qualified-release/script.py",
            template=ctx.root / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml",
            settings={"operation": phase, "support": ctx.package if rollback else None, "compatibility": ctx.values["rollback_compatibility_id"] if rollback else None})
        store = P.update_operations().store(ctx.root)
        return name, request, store

    def candidate_operation(self, mode):
        """Find the direct successor of the originally approved journal head."""
        ctx, V = self.context, self.verifier
        command = "current-health" if mode == "health-ready" else ctx.route["proofs"]["rollback-final-read"]["command"]
        keys = [a[1:-1] for a in ctx.route["commands"][command]["argv"] if a.endswith("_predecessor}")]
        expected = ctx.values["operation_predecessors"][keys[0]]
        path, _ = V.operation_paths(mode)
        matches = []
        for candidate in [path, *sorted((path.parent / "history").glob("kp-*.json"))]:
            if not candidate.exists(): continue
            raw = V.task_journal().read(candidate)
            if raw.get("mode") != mode: continue
            value = V.load_operation(candidate, mode)
            if value["predecessor"] == (None if expected == "none" else expected):
                digest = V.image_digest(value["request"]["task_definition"])
                self.require(digest in {ctx.package["image_digest"], self.rollback_package["image_digest"]}, "delivery-verification-image-mismatch")
                if digest == ctx.package["image_digest"]: matches.append(value)
        self.require(len(matches) <= 1, "delivery-verification-operation-ambiguous")
        return matches[0] if matches else None, expected

    def completed_transition(self, *, rollback=False):
        """Use the original execution token, including after AWS removes its change set."""
        _, request, store = self.transition(rollback=rollback)
        execution, preparation = store.read("update-execute", request), store.read("update-create", request)
        self.require(execution is not None and preparation is not None, "delivery-deployment-completion-required")
        ok, stacks, _ = self.prepare.aws("cloudformation", "describe-stacks", "--stack-name", self.prepare.STACK)
        rows = stacks.get("Stacks") if ok and isinstance(stacks, dict) else None
        self.require(isinstance(rows, list) and len(rows) == 1 and rows[0].get("StackName") == self.prepare.STACK, "delivery-deployment-completion-required")
        ok, events, _ = self.prepare.aws("cloudformation", "describe-stack-events", "--stack-name", self.prepare.STACK)
        self.require(ok, "delivery-deployment-completion-required")
        owned = self.prepare.update_operations().CHANGE_SETS.execution_events(events, execution["operation_id"], rows[0].get("StackId"))
        completed = [event for event in owned if event.get("ResourceStatus") == "UPDATE_COMPLETE"]
        self.require(len(completed) == 1, "delivery-deployment-completion-required")
        return self.C.parsed_time(completed[0].get("Timestamp"))

    def terminal_failure(self, stage):
        if stage not in {*self.proofs, "readiness"}: return None
        V, ctx = self.verifier, self.context
        if stage in {"rollback-final-read", "readiness"}:
            value, _ = self.candidate_operation("health-ready" if stage == "readiness" else "read")
            proof = V.retained_completion(value) if value is not None else None
            successes = {V.SUCCESS[value["mode"]]} if value else set()
        else:
            admin = self.load(Path(__file__).with_name("run-administration") / "script.py")
            operations = admin.MIGRATION.task_operations()
            operation = operations.BoundOperation(root=ctx.root, proof_type="administration",
                family="kanbien-core-platform-persistence-administration", container="persistence-administration",
                selector="PERSISTENCE_ADMINISTRATION_OPERATION", results=admin.SUCCESS,
                aws=admin.MIGRATION.aws, report=admin.report, accept=admin.accept, receipts=admin.RECEIPTS)
            argv = ctx.route["commands"][ctx.route["proofs"][stage]["command"]]["argv"]
            mode = argv[argv.index("--operation") + 1]
            key = next(a[1:-1] for a in argv if a.endswith("_predecessor}"))
            expected = ctx.values["operation_predecessors"][key]
            path, _ = operation.paths(mode)
            value = ctx.owned(lambda: operation.load(path, mode), (operations.OperationFailure,)) if path.exists() else None
            if value is not None:
                self.require(value["predecessor"] == (None if expected == "none" else expected), "delivery-verification-operation-mismatch")
            proof = ctx.owned(lambda: operation.completion(value), (operations.OperationFailure,)) if value is not None else None
            success = admin.SUCCESS[mode]
            successes = {success} if isinstance(success, str) else set(success)
        if value is None: return None
        if proof is None: return None
        task = proof["task"]
        if task["exit_code"] == 0 and task["result_code"] in successes: return None
        self.require(task["image_digest"] == ctx.package["image_digest"]
            and proof["provenance"].get("evidence_class", "live") == "live"
            and self.C.parsed_time(task["started_at"]) >= self.completed_transition(), "delivery-terminal-evidence-mismatch")
        return {"operation_id": value["operation_id"], "proof_receipt": value["proof_receipt"], "proof_sha256": value["proof_sha256"],
                "mode" if stage in {"rollback-final-read", "readiness"} else "operation": value["mode"]}

    def confirm_failure(self, stage, error):
        report = error.evidence
        schema = "deploy/private-persistence-verification-report/v1" if stage in {"rollback-final-read", "readiness"} else "deploy/persistence-administration-report/v1"
        if not isinstance(report, dict) or report.get("schema") != schema: return False
        facts = report.get("facts")
        if not isinstance(facts, dict) or any(k not in facts for k in ("operation_id", "proof_receipt", "proof_sha256")): return False
        selected = self.terminal_failure(stage)
        return selected is not None and all(facts[k] == v for k, v in selected.items())

    def pending_recovery(self):
        _, request, store = self.transition(rollback=True)
        if store.read("update-create", request) is None: return None
        for stage in (*self.proofs, "readiness"):
            if self.terminal_failure(stage) is not None:
                return self.halt("delivery-candidate-verification-failed", verdict="failed")
        raise self.halt("delivery-recovery-evidence-required")

    def recovery_proof(self, name):
        ctx, C, V = self.context, self.C, self.verifier
        mode = "health-ready" if name == "rollback-b-health" else "read"
        candidate, expected = self.candidate_operation(mode)
        predecessor = candidate["operation_id"] if candidate is not None else expected
        key = "rollback_b_health_predecessor" if mode == "health-ready" else "rollback_b_read_predecessor"
        outputs = C.stack_outputs()
        # Both runtime and private verifier use the exact compatible predecessor;
        # administration/restoration support stays on the qualified candidate.
        C.current_service(outputs["CoreServerPersistenceTaskDefinitionArn"], self.rollback_package, C.qualified_runnable_digest(self.rollback_package))
        result = ctx.command(name, {"accepted"}, **{key: predecessor})
        facts = result.get("facts", {})
        value = V.load_operation(V.operation_paths(mode)[0], mode)
        proof = V.retained_completion(value)
        self.require(proof is not None and facts.get("proof_receipt") == value["proof_receipt"] and value["predecessor"] == (None if predecessor == "none" else predecessor)
            and proof["task"]["image_digest"] == self.rollback_package["image_digest"] and proof["task"]["definition"] == outputs["CoreServerPersistenceVerifierTaskDefinitionArn"]
            and proof["task"]["exit_code"] == 0 and proof["task"]["result_code"] == V.SUCCESS[mode], "delivery-restored-proof-mismatch")
        self.require(C.parsed_time(proof["task"]["started_at"]) >= self.completed_transition(rollback=True), "delivery-restored-proof-stale")

    def recovery_steps(self):
        yield "rollback", lambda: self.deploy(rollback=True)
        for name in ("rollback-b-health", "rollback-b-read"):
            yield name, lambda name=name: self.recovery_proof(name)

    def proof(self, name):
        command = self.context.route["proofs"][name]["command"]
        result = self.context.command(command, {"accepted"}, **self.arguments)
        path = result.get("facts", {}).get("proof_receipt")
        self.require(isinstance(path, str), "delivery-proof-reference-missing")
        self.receipts[name] = str(self.context.path(path))

    def readiness(self):
        result = self.context.command("current-health", {"accepted"}, **self.arguments)
        self.health = result.get("facts", {}).get("verifier_task")
        self.require(isinstance(self.health, str), "delivery-health-reference-missing")

    def collect(self, directory):
        ctx = self.context
        self.inputs = ctx.manifest({"candidate_receipt": str(ctx.package_path()), "expected_predecessor": ctx.expected,
            "proof_receipts": self.receipts, "current_health_task": self.health}, directory)
        result = ctx.command("collect", {"recorded"}, acceptance_inputs=self.inputs)
        self.candidate = result.get("facts", {}).get("candidate_record")
        self.require(isinstance(self.candidate, str), "delivery-candidate-reference-missing")
        return self.candidate, self.inputs

    def steps(self):
        yield "deploy", self.deploy
        for name in self.proofs:
            yield name, lambda name=name: self.proof(name)
        yield "readiness", self.readiness
