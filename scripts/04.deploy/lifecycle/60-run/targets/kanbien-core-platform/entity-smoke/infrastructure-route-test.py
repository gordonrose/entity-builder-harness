#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.infrastructure-route
#   version: 8
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise the public infrastructure route, real generic gate and actual CLI rejection with controlled source/custody/provider prerequisites, never live qualification.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import copy
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_INFRASTRUCTURE_ROUTE_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
M = module("entity_smoke_infrastructure_route_test", DIRECTORY / "script.py")
F = module("entity_smoke_deployment_fixture", DIRECTORY / "deployment-control-test.py")
REAL_ROOT = M.ROOT
CANARY = F.CANARY


class Provider(F.Provider):
    def __init__(self, **arguments):
        super().__init__(**arguments)
        self.write_operation, self.prewrite, self.effect = None, None, "not-started"
        self.deny_policy, self.tamper = False, False
        self.proof_tasks, self.proof_logs = {}, {}
        families = {"Server": "server", "Migration": "migration", "Administration": "administration", "Verifier": "verifier", "DatabaseProof": "database-proof"}
        for index, row in enumerate(self.resources, 1):
            if row["ResourceType"] == "AWS::ECS::TaskDefinition":
                row["PhysicalResourceId"] = "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-" + families[row["LogicalResourceId"].removesuffix("TaskDefinition")] + ":1"
            if row["ResourceType"] == "AWS::EC2::SecurityGroup": row["PhysicalResourceId"] = "sg-" + format(index, "017x")
    def enable(self, operation, prewrite):
        assert operation in M.WRITES
        self.write_operation, self.prewrite = operation, prewrite
    def __call__(self, service, operation, **parameters):
        selected = service, operation
        assert selected in M.READS or selected == self.write_operation
        if selected in M.WRITES:
            if self.tamper: parameters["RoleARN"] = "unreviewed-role-canary"
            try: self.prewrite(operation, parameters)
            except M.InfrastructureFailure as failure: raise M.RESOURCE.SubmissionNotStarted(failure.code) from None
            self.write_operation, self.prewrite, self.effect = None, None, "unknown-reconcile-only"
        if operation == "get-caller-identity":
            return {"Account": M.ALIGN.ACCOUNT, "Arn": "arn:aws:sts::337159794548:assumed-role/ApprovedOperator/fixture"}
        if operation == "get-role":
            return {"Role": {"RoleName": "ApprovedOperator", "Arn": "arn:aws:iam::337159794548:role/ApprovedOperator"}}
        if operation == "simulate-principal-policy":
            return {"EvaluationResults": [{"EvalActionName": action, "EvalDecision": "implicitDeny" if self.deny_policy else "allowed"} for action in parameters["ActionNames"]]}
        if operation == "validate-template": return {"Parameters": [{"ParameterKey": name} for name in M.DEPLOY.PARAMETERS], "Capabilities": ["CAPABILITY_IAM"]}
        if operation == "describe-tasks" and parameters["tasks"][0] in self.proof_tasks:
            return {"tasks": [copy.deepcopy(self.proof_tasks[parameters["tasks"][0]])]}
        if operation == "get-log-events":
            return {"events": [] if "nextToken" in parameters else [{"message": json.dumps(self.proof_logs[parameters["logStreamName"].rsplit("/", 1)[1]])}], "nextForwardToken": "terminal-page"}
        try: return super().__call__(service, operation, **parameters)
        except F.R.ResourceMissing: raise M.RESOURCE.ResourceMissing() from None


def failed(call, code):
    try: call()
    except (M.InfrastructureFailure, M.RESOURCE.ResourceFailure, M.GATE.ContractFailure, M.RESOURCE.EVIDENCE.EvidenceFailure) as failure:
        assert failure.code == code, (failure.code, code)
        assert CANARY not in str(failure)
    else: raise AssertionError("expected public infrastructure rejection")


# Controlled prerequisites exercise the public orchestration and real generic
# compiler, not source/custody qualification or provider observations. Actual
# CLI failures below run without these substitutions and cannot contact AWS.
original = {name: getattr(M, name) for name in ("ROOT", "source_digest", "digest_file", "local_qualification")}
old_receipt, old_preflight, old_inspect = M.ALIGN.read_receipt, M.ALIGN.source_preflight, M.ALIGN.inspect
with tempfile.TemporaryDirectory(prefix="entity-smoke-infrastructure-route-") as temporary:
    root = Path(temporary)
    M.ROOT = root
    artifact = "sha256:" + "f" * 64
    M.source_digest = lambda: artifact
    actual_digest = original["digest_file"]
    M.digest_file = lambda path: actual_digest(path) if path.is_file() else "sha256:" + "c" * 64
    source_calls = []
    M.local_qualification = lambda *_: source_calls.append("package-local-qualification-double")
    M.ALIGN.read_receipt = lambda path: {"source_revision": F.BINDING["source_revision"], "image_digest": F.BINDING["image_digest"], "receipt_reference": "github-actions-run:123"}
    M.ALIGN.source_preflight = lambda receipt: source_calls.append("committed-source-double")
    M.ALIGN.inspect = lambda provider, receipt, checked_at: ({"dependency_incarnation_sha256": F.BINDING["dependency_incarnation_sha256"]}, copy.deepcopy(F.PARAMETERS), "private-group")
    def arguments(mode="plan", label=None, approved=None, phase="create", prerequisites=None):
        return SimpleNamespace(mode=mode, phase=phase, receipt=root / "controlled-receipt.json", proof_label=label or F.BINDING["proof_label"], approved_plan=approved, wait_seconds=0, prerequisites=prerequisites, validate_arguments=False)
    def expiry_at_main(args, expected_effect):
        response = SimpleNamespace(returncode=254, stdout="", stderr="An error occurred (ExpiredToken) when calling the GetCallerIdentity operation: " + CANARY)
        output = io.StringIO()
        with patch.object(M.CLI.subprocess, "run", return_value=response) as call, \
             patch.object(M, "parse", lambda: args), redirect_stdout(output):
            status = M.main()
        report = json.loads(output.getvalue())
        assert status == 1 and report["condition"] == "aws-credentials-expired"
        assert report["effect"] == expected_effect and CANARY not in output.getvalue()
        assert report["context"]["provider_operation"] == "sts/get-caller-identity"
        assert call.call_count == 1 and call.call_args.args[0][1:3] == ["sts", "get-caller-identity"]
    expiry_at_main(arguments(), "not-started")
    provider = Provider()
    plan = M.run(arguments(), provider)
    assert plan["verdict"] == "planned" and not any(operation in {"create-change-set", "execute-change-set"} for _, operation, _ in provider.calls)
    assert plan["plan"]["baseline_database_ingress_additions"] == 4 and plan["plan"]["baseline_endpoint_ingress_additions"] == 5
    assert CANARY not in json.dumps(plan) and F.PARAMETERS["AdministratorSecretArn"] not in json.dumps(plan)
    failed(lambda: M.run(arguments("review", approved="sha256:" + "0" * 64), provider), "infrastructure-approved-plan-mismatch")
    assert not any(operation == "create-change-set" for _, operation, _ in provider.calls)
    reviewed = M.run(arguments("review", approved=plan["plan_sha256"]), provider)
    assert reviewed["verdict"] == "reviewed"
    assert sum(operation == "create-change-set" for _, operation, _ in provider.calls) == 1
    # AWS leaves the provisional stack untagged until execution. Ownership on
    # resume must come from the exact original reservation and reviewed change.
    assert provider.stack["StackStatus"] == "REVIEW_IN_PROGRESS" and provider.stack["Tags"] == []
    assert M.run(arguments("review", approved=plan["plan_sha256"]), provider)["verdict"] == "reviewed"
    assert sum(operation == "create-change-set" for _, operation, _ in provider.calls) == 1
    failed(lambda: M.run(arguments(label="entity-smoke-" + "9" * 24), provider), "infrastructure-existing-stack-not-owned-by-attempt")
    original_stack_id = provider.stack["StackId"]
    provider.stack["StackId"] = original_stack_id.replace("11111111-1111", "99999999-9999")
    failed(lambda: M.run(arguments("review", approved=plan["plan_sha256"]), provider), "deployment-stack-identity-not-confirmed")
    provider.stack["StackId"] = original_stack_id
    for field, value, code in (
        ("Tags", [], "deployment-ownership-not-confirmed"),
        ("Description", "es-" + "0" * 32, "deployment-change-identity-not-confirmed"),
        ("Status", "CREATE_IN_PROGRESS", "deployment-change-not-ready"),
    ):
        provider.mutate_change = lambda change, field=field, value=value: change.update({field: value})
        failed(lambda: M.run(arguments("review", approved=plan["plan_sha256"]), provider), code)
    provider.mutate_change = lambda change: None
    provider.wrong_template = True
    failed(lambda: M.run(arguments("review", approved=plan["plan_sha256"]), provider), "deployment-change-template-mismatch")
    provider.wrong_template = False
    assert sum(operation == "create-change-set" for _, operation, _ in provider.calls) == 1
    assert not any(operation == "execute-change-set" for _, operation, _ in provider.calls)
    # Submitted and completed are different states. A lost response may only
    # observe the reserved operation, never submit a second execute request.
    provider.lost_execute = True
    failed(lambda: M.run(arguments("execute", approved=plan["plan_sha256"]), provider), "deployment-execution-uncertain-reconcile-only")
    # Once admitted, unavailable NEW-admission checks and lost write permission
    # must not obstruct observation. Completion still proves real owned state.
    def admission_unavailable(*args, **kwargs):
        raise M.InfrastructureFailure("infrastructure-local-proof-unavailable")
    resume_args = arguments("execute", approved=plan["plan_sha256"])
    gate_root = root / ".cache/entity-smoke-live" / F.BINDING["proof_label"] / "realization"
    admission_bytes = {path: path.read_bytes() for path in gate_root.glob("execution-preflight-*.json")}
    reserved_bytes = {path: path.read_bytes() for path in (gate_root.parent / "attempts").glob("*.json")}
    preparation_path = gate_root.parent / "attempts" / (F.BINDING["proof_label"] + "-deploy-create-change-set.json")
    preparation_bytes = preparation_path.read_bytes()
    # A real execution alone is not enough. Reject missing/malformed preparation
    # without another mutation and never replace either reservation.
    calls_before = len(provider.calls)
    preparation_path.unlink()
    failed(lambda: M.run(resume_args, provider), "infrastructure-reviewed-attempt-required")
    preparation_path.write_text("{malformed-private-canary")
    failed(lambda: M.run(resume_args, provider), "resource-reservation-unavailable")
    preparation_path.write_bytes(preparation_bytes)
    assert all(operation.startswith(("describe-", "get-", "list-", "simulate-")) for _, operation, _ in provider.calls[calls_before:])
    assert all(path.read_bytes() == raw for path, raw in reserved_bytes.items())
    expiry_at_main(resume_args, "original-operation-reconcile-only")
    assert all(path.read_bytes() == raw for path, raw in {**admission_bytes, **reserved_bytes}.items())
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    provider.deny_policy = True
    with patch.object(M, "local_qualification", admission_unavailable), patch.object(M.ALIGN, "source_preflight", admission_unavailable), \
         patch.object(M.ALIGN, "inspect", admission_unavailable), patch.object(M, "now", lambda: "2099-01-01T00:00:00Z"):
        provider.stack["StackStatus"] = "CREATE_IN_PROGRESS"
        with patch.object(M.DEPLOY.CHANGE_SETS, "retained_execution", wraps=M.DEPLOY.CHANGE_SETS.retained_execution) as selection:
            pending = M.run(resume_args, provider)
            assert selection.call_count == 1  # Validated reconstructed intent.
        assert pending["verdict"] == "pending" and pending["effect"] == "original-operation-not-terminal"
        provider.stack["StackStatus"] = "CREATE_FAILED"
        failed(lambda: M.run(resume_args, provider), "deployment-execution-not-successful")
        provider.stack["StackStatus"] = "CREATE_COMPLETE"
        completed = M.run(resume_args, provider)
        assert completed["verdict"] == "completed"
        assert M.run(resume_args, provider) == completed
        assert provider.write_operation is None
        failed(lambda: M.run(arguments("execute", approved="sha256:" + "0" * 64), provider), "infrastructure-approved-plan-mismatch")
        admission_path = next(iter(admission_bytes))
        changed = json.loads(admission_bytes[admission_path])
        changed["facts"]["gate_evidence"][0]["input_sha256"] = "sha256:" + "0" * 64
        admission_path.write_text(json.dumps(changed))
        failed(lambda: M.run(resume_args, provider), "task-step-completion-facts-mismatch")
        admission_path.unlink()
        failed(lambda: M.run(resume_args, provider), "infrastructure-original-admission-required")
        admission_path.write_bytes(admission_bytes[admission_path])
        changed = json.loads(admission_bytes[admission_path])
        changed["change_summary"]["operation_counts"]["delete"] = 1
        admission_path.write_text(json.dumps(changed))
        failed(lambda: M.run(resume_args, provider), "infrastructure-original-admission-required")
        admission_path.write_bytes(admission_bytes[admission_path])
        def wrong_account(service, operation, **parameters):
            if operation == "get-caller-identity": return {"Account": "000000000000", "Arn": CANARY}
            return provider(service, operation, **parameters)
        failed(lambda: M.run(resume_args, wrong_account), "infrastructure-operator-identity-not-confirmed")
        assert all(path.read_bytes() == raw for path, raw in admission_bytes.items())
        admission_facts = json.loads(next(iter(admission_bytes.values())))["facts"]
        resumed_gates = [M.read_json(path) for path in gate_root.glob("controlled-execution-*.json")]
        assert any(item["facts"]["gate_evidence"][:6] == admission_facts["gate_evidence"]
                   and item["facts"]["component_evidence"] == admission_facts["component_evidence"] for item in resumed_gates)
        # Unknown reads stay unknown at the real reporting boundary; never retry
        # the mutation or turn a failed observation into missing intent.
        def unavailable_read(service, operation, **parameters):
            if operation == "describe-stacks":
                raise M.InfrastructureFailure("infrastructure-provider-observation-unavailable", provider_operation=(service, operation))
            return provider(service, operation, **parameters)
        unavailable_read.effect = "not-started"
        output = io.StringIO()
        with patch.object(M, "Provider", lambda: unavailable_read), patch.object(M, "parse", lambda: resume_args), redirect_stdout(output):
            status = M.main()
        report = json.loads(output.getvalue())
        assert status == 1 and report["condition"] == "infrastructure-provider-observation-unavailable"
        assert report["effect"] == "original-operation-reconcile-only" and CANARY not in output.getvalue()
        # An absent attempt does not gain this continuation privilege.
        failed(lambda: M.run(arguments("execute", label="entity-smoke-" + "7" * 24, approved=plan["plan_sha256"]), Provider()),
               "infrastructure-local-proof-unavailable")
    provider.deny_policy = False
    assert completed["verdict"] == "completed"
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    assert M.run(arguments("execute", approved=plan["plan_sha256"]), provider)["receipt"] == completed["receipt"]
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    assert provider.changes == {}  # Executed change-set disappearance is normal.
    original_tokens = provider.tokens[:]
    provider.tokens = []
    failed(lambda: M.run(arguments("execute", approved=plan["plan_sha256"]), provider), "deployment-execution-lineage-not-confirmed")
    provider.tokens = original_tokens
    provider.wrong_template = True
    failed(lambda: M.run(arguments("execute", approved=plan["plan_sha256"]), provider), "deployment-provider-template-mismatch")
    provider.wrong_template = False
    journal = root / ".cache/entity-smoke-live" / F.BINDING["proof_label"] / "attempts" / (F.BINDING["proof_label"] + "-deploy-execute-create.json")
    original_journal = journal.read_bytes()
    changed_journal = json.loads(original_journal)
    changed_journal["request"]["parameters_sha256"] = "sha256:" + "0" * 64
    changed_journal["request_sha256"] = hashlib.sha256(M.RESOURCE.CONTROL.canonical(changed_journal["request"])).hexdigest()
    journal.write_text(json.dumps(changed_journal))
    failed(lambda: M.run(arguments("execute", approved=plan["plan_sha256"]), provider), "infrastructure-execution-reservation-mismatch")
    journal.write_bytes(original_journal)
    journal.unlink()
    assert M.run(arguments("execute", approved=plan["plan_sha256"]), provider)["verdict"] == "pending"
    journal.write_bytes(original_journal)
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    deployed_tags = provider.stack["Tags"]
    provider.stack["Tags"] = []
    failed(lambda: M.run(arguments("execute", approved=plan["plan_sha256"]), provider), "deployment-ownership-not-confirmed")
    provider.stack["Tags"] = deployed_tags
    evidence = sorted(root.rglob("realization/*.json"))
    assert evidence
    for path in evidence:
        value = json.loads(path.read_text())
        assert value["plan_sha256"] == plan["plan_sha256"]
        M.GATE.validate_facts(value["facts"], M.GateBook(artifact, root / "unused").contract, "entity-smoke-infrastructure-control", M.GateBook(artifact, root / "unused").known, value["facts"]["gate_evidence"][-1]["gate"])
        assert CANARY not in path.read_text() and "arn:" not in path.read_text()
    assert not any("runtime" in entry["component_id"] for entry in value["facts"]["component_evidence"])
    # First-release absence must cross the real CLI classifier/provider into
    # the actual plan caller, including the observed zero-retry CLI decoration.
    old_cli = M.subprocess.run
    class CliAbsenceProvider(Provider):
        def __call__(self, service, operation, **parameters):
            if (service, operation) == ("cloudformation", "describe-stacks"):
                return M.Provider()(service, operation, **parameters)
            return super().__call__(service, operation, **parameters)
    try:
        for decoration in ("", " (reached max retries: 0)"):
            attempts = []
            def absent_cli(arguments, **options):
                attempts.append(arguments)
                assert arguments[1:3] == ["cloudformation", "describe-stacks"]
                assert json.loads(arguments[arguments.index("--cli-input-json") + 1]) == {"StackName": M.DEPLOY.STACK}
                assert options["env"]["AWS_MAX_ATTEMPTS"] == "1"
                return SimpleNamespace(returncode=254, stdout="", stderr="An error occurred (ValidationError) when calling the DescribeStacks operation" + decoration + ": Stack with id " + M.DEPLOY.STACK + " does not exist\n")
            M.subprocess.run = absent_cli
            selected = CliAbsenceProvider()
            actual = M.run(arguments(label="entity-smoke-" + "c" * 24), selected)
            assert actual["verdict"] == "planned" and actual["plan"]["resource_additions"] == 30 and actual["effect"] == "not-started"
            assert len(attempts) == 1 and not any(operation in {"create-change-set", "execute-change-set"} for _, operation, _ in selected.calls)
    finally:
        M.subprocess.run = old_cli
    # A new proof label does not authorize adopting an existing feature stack.
    failed(lambda: M.run(arguments(label="entity-smoke-" + "1" * 24), provider), "infrastructure-existing-stack-not-owned-by-attempt")
    denied = Provider(); denied.deny_policy = True
    failed(lambda: M.run(arguments(label="entity-smoke-" + "2" * 24), denied), "infrastructure-operator-policy-preflight-not-confirmed")
    assert denied.calls == []
    # Missing prerequisite proofs cannot activate the feature even when the
    # current image/template are otherwise selected correctly.
    failed(lambda: M.run(arguments(phase="activate"), provider), "infrastructure-activation-proof-required")
    # Build genuine local-fixture receipts through the real evidence collector.
    # These controlled tasks are never written to the production evidence root.
    base_time = datetime.now(timezone.utc)
    manifest = {}
    resource_ids = {row["LogicalResourceId"]: row["PhysicalResourceId"] for row in provider.resources}
    for index, (name, workload, operation, logical) in enumerate((
        ("bootstrap", "administration", "bootstrap", "Administration"),
        ("migration", "migration", "apply", "Migration"),
        ("grant-runtime", "administration", "grant-runtime", "Administration"),
        ("permissions", "database-proof", "permissions", "DatabaseProof"),
    ), 1):
        instant = lambda seconds: (base_time + timedelta(seconds=seconds)).isoformat()
        request = {**plan["plan"]["binding"], "workload": workload, "definition": resource_ids[logical + "TaskDefinition"], "security_group": resource_ids[logical + "SecurityGroup"],
                   "subnets": F.PARAMETERS["PrivateSubnetIds"].split(","), "deadline_seconds": 180,
                   "environment": {M.RESOURCE.CONTROL.OPERATIONS[workload][0]: operation}}
        if workload == "database-proof": request["environment"]["ENTITY_SMOKE_PROOF_LABEL"] = F.BINDING["proof_label"]
        reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "operation_id": "es-" + format(index, "032x"), "request": request,
                       "request_sha256": hashlib.sha256(M.RESOURCE.CONTROL.canonical(request)).hexdigest(), "reserved_at": instant(index * 4)}
        task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + format(index, "032x"), "taskDefinitionArn": request["definition"], "startedBy": reservation["operation_id"],
                "overrides": M.RESOURCE.CONTROL.overrides(request), "lastStatus": "STOPPED", "launchType": "FARGATE", "createdAt": instant(index * 4), "startedAt": instant(index * 4 + 1), "stoppedAt": instant(index * 4 + 2),
                "containers": [{"name": "entity-smoke-" + workload, "imageDigest": request["image_digest"], "exitCode": 0}]}
        if workload == "administration": result = {"verdict": "passed", "code": "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED", "operation": operation}
        elif workload == "migration": result = {"verdict": "passed", "code": "ENTITY_SMOKE_MIGRATION_APPLIED"}
        else:
            result = {"schema": "deploy/entity-smoke-database-proof/v1", "verdict": "passed", "operation": "permissions", "code": "ENTITY_SMOKE_EFFECTIVE_PRIVILEGES_PROVEN",
                      "proof_label_sha256": hashlib.sha256(F.BINDING["proof_label"].encode()).hexdigest(), "steps": ["identity", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write"], "checked_at": instant(index * 4 + 1)}
        receipt = M.RESOURCE.EVIDENCE.collect(task, reservation, {"events": [{"message": json.dumps(result)}]}, instant(index * 4 + 3))
        manifest[name] = {"reservation": reservation, "receipt": receipt}
        provider.proof_tasks[task["taskArn"]] = task
        provider.proof_logs[task["taskArn"].rsplit("/", 1)[1]] = result
    prerequisites = root / "prerequisites.json"
    prerequisites.write_text(json.dumps(manifest))
    substituted = copy.deepcopy(manifest)
    probe = substituted["bootstrap"]["reservation"]
    probe["request"]["environment"]["ENTITY_SMOKE_ADMINISTRATION_OPERATION"] = "preflight"
    probe["request"]["deadline_seconds"] = 90
    probe["request_sha256"] = hashlib.sha256(M.RESOURCE.CONTROL.canonical(probe["request"])).hexdigest()
    probe_task = copy.deepcopy(provider.proof_tasks[substituted["bootstrap"]["receipt"]["task"]["arn"]])
    probe_task["overrides"] = M.RESOURCE.CONTROL.overrides(probe["request"])
    probe_result = {"verdict": "passed", "code": "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED", "operation": "preflight"}
    substituted["bootstrap"]["receipt"] = M.RESOURCE.EVIDENCE.collect(probe_task, probe, {"events": [{"message": json.dumps(probe_result)}]}, substituted["bootstrap"]["receipt"]["collected_at"])
    preflight_only = root / "preflight-not-bootstrap.json"
    preflight_only.write_text(json.dumps(substituted))
    failed(lambda: M.run(arguments(phase="activate", prerequisites=preflight_only), provider), "infrastructure-activation-proof-binding-mismatch")
    already_applied = copy.deepcopy(manifest)
    already_applied["migration"]["receipt"]["result"]["code"] = "ENTITY_SMOKE_MIGRATION_ALREADY_APPLIED"
    bad_proof = root / "invalid-prerequisites.json"
    bad_proof.write_text(json.dumps(already_applied))
    failed(lambda: M.run(arguments(phase="activate", prerequisites=bad_proof), provider), "infrastructure-activation-completion-contract-mismatch")
    extended_deadline = copy.deepcopy(manifest)
    extended_deadline["bootstrap"]["reservation"]["request"]["deadline_seconds"] = 900
    changed_hash = hashlib.sha256(M.RESOURCE.CONTROL.canonical(extended_deadline["bootstrap"]["reservation"]["request"])).hexdigest()
    extended_deadline["bootstrap"]["reservation"]["request_sha256"] = changed_hash
    extended_deadline["bootstrap"]["receipt"]["request_sha256"] = changed_hash
    bad_proof.write_text(json.dumps(extended_deadline))
    failed(lambda: M.run(arguments(phase="activate", prerequisites=bad_proof), provider), "infrastructure-activation-completion-contract-mismatch")
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    activation = arguments(phase="activate", prerequisites=prerequisites)
    cache = root / ".cache/entity-smoke-live" / F.BINDING["proof_label"]
    store = M.RESOURCE.ResourceStore(cache / "attempts")
    active_parameters = {**F.PARAMETERS, "ServerDesiredCount": "1"}
    real_datetime = M.datetime
    class Later(datetime):
        @classmethod
        def now(cls, tz=None): return datetime.now(tz) + timedelta(hours=2)
    M.datetime = Later
    failed(lambda: M.activation_prerequisites(provider, prerequisites, plan["plan"]["binding"], active_parameters, cache, store), "infrastructure-activation-proof-not-fresh")
    M.datetime = real_datetime
    activation_plan = M.run(activation, provider)
    activation.mode, activation.approved_plan = "review", activation_plan["plan_sha256"]
    assert M.run(activation, provider)["verdict"] == "reviewed"
    activation.mode = "execute"; provider.lost_execute = False
    assert M.run(activation, provider)["verdict"] == "completed"
    assert M.run(activation, provider)["verdict"] == "completed"
    # An older valid CREATE approval cannot be attached to ACTIVATE intent.
    activation.approved_plan = plan["plan_sha256"]
    with patch.object(M, "local_qualification", admission_unavailable), patch.object(M.ALIGN, "inspect", admission_unavailable):
        failed(lambda: M.run(activation, provider), "infrastructure-approved-plan-mismatch")
    activation.approved_plan = activation_plan["plan_sha256"]
    original_execution = M.read_execution_reservation(store, plan["plan"]["binding"], active_parameters, True)
    M.datetime = Later
    M.activation_prerequisites(provider, prerequisites, plan["plan"]["binding"], active_parameters, cache, store, resuming=True, admitted_at=original_execution["reserved_at"])
    failed(lambda: M.activation_prerequisites(provider, prerequisites, plan["plan"]["binding"], active_parameters, cache, store, resuming=True, admitted_at=Later.now(timezone.utc).isoformat()), "infrastructure-activation-proof-not-fresh")
    M.datetime = real_datetime
    provider.paginated_events = True
    artifact = "sha256:" + "e" * 64
    activation.mode = "plan"
    repaired_plan = M.run(activation, provider)
    assert repaired_plan["plan_sha256"] != activation_plan["plan_sha256"]
    activation.mode, activation.approved_plan = "execute", repaired_plan["plan_sha256"]
    assert M.run(activation, provider)["verdict"] == "completed"
    assert M.read_execution_reservation(store, plan["plan"]["binding"], active_parameters, True) == original_execution
    provider.paginated_events = False
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 2
    tampered = Provider(); tampered.tamper = True
    args = arguments(label="entity-smoke-" + "3" * 24)
    tampered_plan = M.run(args, tampered)
    args.mode, args.approved_plan = "review", tampered_plan["plan_sha256"]
    failed(lambda: M.run(args, tampered), "infrastructure-submission-does-not-match-plan")
    assert not any(operation == "create-change-set" for _, operation, _ in tampered.calls)
    main_provider = Provider(); main_provider.tamper = True
    main_args = arguments(label="entity-smoke-" + "4" * 24)
    main_plan = M.run(main_args, main_provider)
    main_args.mode, main_args.approved_plan = "review", main_plan["plan_sha256"]
    original_factory, original_parse = M.Provider, M.parse
    M.Provider, M.parse = lambda: main_provider, lambda: main_args
    output = io.StringIO()
    with redirect_stdout(output): status = M.main()
    M.Provider, M.parse = original_factory, original_parse
    failure = json.loads(output.getvalue())
    assert status == 1 and failure["condition"] == "infrastructure-submission-does-not-match-plan" and failure["effect"] == "not-started", failure
    assert failure["context"]["mode"] == "review" and failure["context"]["phase"] == "create" and CANARY not in output.getvalue()
    lost_provider = Provider(lost_execute=True)
    lost_args = arguments(label="entity-smoke-" + "5" * 24)
    lost_plan = M.run(lost_args, lost_provider)
    lost_args.mode, lost_args.approved_plan = "review", lost_plan["plan_sha256"]
    M.run(lost_args, lost_provider)
    lost_args.mode = "execute"
    M.Provider, M.parse = lambda: lost_provider, lambda: lost_args
    output = io.StringIO()
    with redirect_stdout(output): status = M.main()
    M.Provider, M.parse = original_factory, original_parse
    failure = json.loads(output.getvalue())
    assert status == 1 and failure["condition"] == "deployment-execution-uncertain-reconcile-only" and failure["effect"] == "unknown-reconcile-only"
    assert sum(operation == "execute-change-set" for _, operation, _ in lost_provider.calls) == 1 and CANARY not in output.getvalue()
    # Missing component observations and reordered gates are rejected by the
    # same compiler path used by actual execution, not an alternate fake gate.
    incomplete = M.GateBook(artifact, root / "incomplete")
    incomplete.gate("source")
    failed(lambda: incomplete.validate("source"), "infrastructure-component-proof-incomplete")
    failed(lambda: incomplete.gate("live-read"), "infrastructure-gate-order-invalid")
    timestamps = M.GateBook(artifact, root / "timestamps")
    for name in timestamps.known: timestamps.component(name)
    timestamps.bind_plan(plan["plan_sha256"])
    failed(lambda: timestamps.bind_plan("sha256:" + "0" * 64), "infrastructure-evidence-plan-mismatch")
    timestamps.gate("source"); timestamps.validate("source")
    observed_times = copy.deepcopy(timestamps.facts["component_evidence"])
    old_clock = M.now
    M.now = lambda: (datetime.now(timezone.utc) + timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamps.validate("source")
    assert timestamps.facts["component_evidence"] == observed_times
    M.now = old_clock
    for path in root.rglob("*.json"):
        assert CANARY not in path.read_text() and F.PARAMETERS["AdministratorSecretArn"] not in path.read_text()
    assert source_calls.count("committed-source-double") == source_calls.count("package-local-qualification-double")
    original_source = M.DEPLOY.SOURCE
    oversized = root / "oversized-template.yml"
    oversized.write_text(original_source.read_text() + "\n# bounded payload fixture\n" * 3000)
    M.DEPLOY.SOURCE = oversized
    failed(M.DEPLOY.source, "deployment-source-size-invalid")
    M.DEPLOY.SOURCE = original_source

for name, value in original.items(): setattr(M, name, value)
M.ALIGN.read_receipt, M.ALIGN.source_preflight, M.ALIGN.inspect = old_receipt, old_preflight, old_inspect

# Exercise the actual process boundary: fake AWS is a sentinel that must never
# run for offline parsing, missing approval or invalid/unavailable custody.
with tempfile.TemporaryDirectory(prefix="entity-smoke-infrastructure-cli-") as temporary:
    root = Path(temporary); marker = root / "provider-called"
    fake_aws = root / "aws"
    fake_aws.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\nraise SystemExit(99)\n")
    fake_aws.chmod(0o700)
    environment = {**os.environ, "PATH": str(root) + os.pathsep + os.environ["PATH"]}
    common = ["--phase", "create", "--receipt", str(root / "missing.json"), "--proof-label", F.BINDING["proof_label"]]
    public = REAL_ROOT / DIRECTORY.relative_to(REAL_ROOT) / "script.sh"
    for suffix, expected in ((["--validate-arguments"], "valid"), ([], "blocked"), (["--unrecognised", CANARY], "blocked")):
        result = subprocess.run(["bash", str(public), "--mode", "plan", *common, *suffix], cwd=REAL_ROOT, env=environment, capture_output=True, text=True, check=False)
        value = json.loads(result.stdout)
        assert value["verdict"] == expected and CANARY not in result.stdout + result.stderr and "Traceback" not in result.stderr
    result = subprocess.run(["bash", str(public), "--mode", "review", *common], cwd=REAL_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and json.loads(result.stdout)["condition"] == "infrastructure-approved-plan-required"
    result = subprocess.run(["bash", str(public.with_name("plan.sh")), "--mode=execute", *common], cwd=REAL_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and json.loads(result.stdout)["condition"] == "infrastructure-arguments-invalid"
    result = subprocess.run(["bash", str(public.with_name("plan.sh")), "--mo", "execute", *common, "--approved-plan", "sha256:" + "0" * 64, "--validate-arguments"], cwd=REAL_ROOT, env=environment, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and json.loads(result.stdout)["condition"] == "infrastructure-arguments-invalid"
    assert not marker.exists()

# Live admission validates the package receipt only; executing local tests is
# owned by package qualification. The binding rejects any missing or altered
# local proof before the main route can reach a provider observer.
with tempfile.TemporaryDirectory(prefix="entity-smoke-local-qualification-") as temporary:
    root = Path(temporary)
    checks = {identity: {"input_digest": f"{index:064x}", "evidence_key": f"{index + 3:064x}"}
              for index, identity in enumerate(sorted(M.LOCAL_QUALIFICATION.REQUIRED_CHECKS), 1)}
    receipt = {"schema": "deploy/package-custody-receipt/v2", "target": "kanbien-core-platform", "source_revision": "a" * 40,
               "local_qualification": {"schema": "deploy/local-qualification/v1", "target": "kanbien-core-platform", "scope": "entity-smoke", "source_revision": "a" * 40, "checks": checks}}
    M.local_qualification(receipt)
    failed(lambda: M.local_qualification({}), "infrastructure-local-qualification-not-confirmed")
    old_parse, old_read, old_source = M.parse, M.ALIGN.read_receipt, M.ALIGN.source_preflight
    M.parse = lambda: SimpleNamespace(receipt=root / "controlled.json", mode="plan", phase="create", proof_label=F.BINDING["proof_label"], validate_arguments=False)
    M.ALIGN.read_receipt, M.ALIGN.source_preflight = lambda path: {}, lambda value: None
    output = io.StringIO()
    with redirect_stdout(output): status = M.main()
    failure = json.loads(output.getvalue())
    assert status == 1 and failure["condition"] == "infrastructure-local-qualification-not-confirmed" and failure["effect"] == "not-started"
    assert CANARY not in output.getvalue()
    M.parse, M.ALIGN.read_receipt, M.ALIGN.source_preflight = old_parse, old_read, old_source

# Preserve actual evidence-owner meaning at the real infrastructure reporter.
primary = {"schema": "core/diagnostic-record/v1", "code": "entity-smoke-target.preflight-rejected", "definitionVersion": 1,
           "detail": {"identity": "runtime", "field": "identity", "condition": "mismatch", "effect": "not-started"}}
bundle = {"diagnostic": primary, "related_diagnostics": []}
old_parse, old_run = M.parse, M.run
M.parse = lambda: SimpleNamespace(mode="execute", phase="activate", proof_label=F.BINDING["proof_label"], validate_arguments=False)
observed_failure = M.RESOURCE.EVIDENCE.EvidenceFailure("task-unsuccessful-completion", primary, [], [bundle])
M.run = lambda *arguments: (_ for _ in ()).throw(observed_failure)
output = io.StringIO()
with redirect_stdout(output): status = M.main()
failure = json.loads(output.getvalue())
assert status == 1 and failure["condition"] == "task-unsuccessful-completion" and failure["diagnostic"] == primary
assert failure["observations"] == [bundle] and failure["related_diagnostics"] == [] and CANARY not in output.getvalue()
M.parse, M.run = old_parse, old_run

# Actual controller source identity includes the extracted execution dependency.
original_digest = M.digest_file
identity_paths = []
dependency_paths = [REAL_ROOT / "scripts/04.deploy/shared/provider-adapters/aws" / name for name in ("cli.py", "tasks.py", "resource_reservation.py", "snapshots.py", "change_sets.py", "ecr-scan.py", "foundation-checks.py")]
dependency_paths.append(REAL_ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
dependency_paths.append(REAL_ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py")
dependency_paths.append(Path(M.LOCAL_QUALIFICATION.__file__))
dependency_paths.extend([Path(M.ALIGN.INPUT_OWNER.__file__), Path(M.ALIGN.INPUT_OWNER.PATHS.__file__),
                         *(REAL_ROOT / reference for reference in M.ALIGN.INPUTS["references"])])
try:
    def fixed_digest(path):
        identity_paths.append(path)
        return "sha256:" + "1" * 64
    M.digest_file = fixed_digest
    original_identity = M.source_digest()
    assert not any(path.name.endswith(("-test.py", "-test.sh")) for path in identity_paths)
    for source in (DIRECTORY / "script.py", DIRECTORY / "script.sh", DIRECTORY / "task-control.py"):
        assert source in identity_paths
    for fixture in DIRECTORY.glob("*-test.*"):
        M.digest_file = lambda path: "sha256:" + ("2" if path == fixture else "1") * 64
        assert M.source_digest() == original_identity
    for dependency in dependency_paths:
        assert dependency in identity_paths
        M.digest_file = lambda path: "sha256:" + ("2" if path == dependency else "1") * 64
        assert M.source_digest() != original_identity
finally:
    M.digest_file = original_digest

# Test-file addition/removal also leaves controller identity stable, while the
# unchanged registered input directory continues to fingerprint test contents.
with tempfile.TemporaryDirectory(prefix="entity-smoke-controller-inputs-") as temporary:
    directory = Path(temporary)
    production = directory / "controller.py"; production.write_text("first")
    virtual = REAL_ROOT / ".cache/controller-input-fixture"
    listing = SimpleNamespace(iterdir=lambda: (virtual / path.name for path in directory.iterdir()))
    with patch.object(M, "DIRECTORY", listing), patch.object(M, "digest_file",
            lambda path: original_digest(directory / path.name if path.parent == virtual else path)):
        initial = M.source_digest()
        fixture = directory / "future-test.py"; fixture.write_text("first")
        assert M.source_digest() == initial
        fixture.write_text("second")
        assert M.source_digest() == initial
        shell_fixture = directory / "future-test.sh"; shell_fixture.write_text("exit 0")
        assert M.source_digest() == initial
        fixture.unlink(); shell_fixture.unlink()
        assert M.source_digest() == initial
        production.write_text("second")
        assert M.source_digest() != initial

# Exercise the real provider adapter with a controlled subprocess response,
# checking that the caller cannot choose another endpoint or enable retries.
old_subprocess = M.subprocess.run
observed = []
def response(arguments, **options):
    observed.append((arguments, options))
    return SimpleNamespace(returncode=0, stdout='{"Account":"337159794548"}', stderr="")
M.subprocess.run = response
provider = M.Provider()
assert provider("sts", "get-caller-identity")["Account"] == M.ALIGN.ACCOUNT
argv, options = observed[-1]
assert argv[argv.index("--endpoint-url") + 1] == "https://sts.eu-west-1.amazonaws.com" and "--no-verify-ssl" not in argv
assert options["env"]["AWS_MAX_ATTEMPTS"] == "1" and options["timeout"] == 40
assert argv[argv.index("--region") + 1] == "eu-west-1"
for service, operation, endpoint, region in [
    ("iam", "get-role", "iam.amazonaws.com", "us-east-1"),
    ("route53", "get-hosted-zone", "route53.amazonaws.com", "us-east-1"),
    ("budgets", "describe-budget", "budgets.amazonaws.com", "us-east-1"),
    ("ecr", "describe-repositories", "api.ecr.eu-west-1.amazonaws.com", "eu-west-1"),
    ("cloudformation", "describe-stacks", "cloudformation.eu-west-1.amazonaws.com", "eu-west-1"),
]:
    provider(service, operation)
    argv, options = observed[-1]
    assert argv[argv.index("--region") + 1] == region, (service, "incorrect-signing-region")
    assert argv[argv.index("--endpoint-url") + 1] == "https://" + endpoint
    assert argv[argv.index("--profile") + 1] == M.ALIGN.PROFILE and "--no-verify-ssl" not in argv
    assert options["env"]["AWS_MAX_ATTEMPTS"] == "1" and options["timeout"] == 40
successful_calls = len(observed)
failed(lambda: provider("ecs", "run-task", cluster=CANARY), "infrastructure-provider-operation-prohibited")
provider.enable(("cloudformation", "create-change-set"), lambda operation, parameters: None)
failed(lambda: provider("cloudformation", "create-change-set", StackName="kanbien-staging"), "infrastructure-write-target-invalid")
assert len(observed) == successful_calls
M.subprocess.run = old_subprocess

# Actual provider failures retain the finite attempted operation at the final
# reporter, never provider parameters or native messages. Only a known read
# transport timeout gets bounded retries; semantic failures remain single-call.
old_parse, old_run, old_subprocess = M.parse, M.run, M.subprocess.run
M.parse = lambda: SimpleNamespace(mode="plan", phase="create", proof_label=F.BINDING["proof_label"], validate_arguments=False)
M.run = lambda args, selected: selected("route53", "get-hosted-zone", Id=CANARY)
for scenario, condition in [
    ("signature", "aws-command-failed"),
    ("denied", "aws-access-denied"),
    ("malformed", "infrastructure-provider-response-invalid"),
    ("wrong-type", "infrastructure-provider-response-invalid"),
    ("timeout", "infrastructure-provider-observation-unavailable"),
]:
    attempts = []
    def rejected(arguments, **options):
        attempts.append(arguments)
        if scenario == "timeout": raise subprocess.TimeoutExpired(arguments, 40, stderr=CANARY)
        if scenario == "malformed": return SimpleNamespace(returncode=0, stdout=CANARY, stderr=CANARY)
        if scenario == "wrong-type": return SimpleNamespace(returncode=0, stdout='[]', stderr=CANARY)
        code = "SignatureDoesNotMatch" if scenario == "signature" else "AccessDenied"
        return SimpleNamespace(returncode=254, stdout="", stderr="An error occurred (" + code + ") when calling the GetHostedZone operation: " + CANARY)
    M.subprocess.run = rejected
    output = io.StringIO()
    with redirect_stdout(output): status = M.main()
    failure = json.loads(output.getvalue())
    assert status == 1 and failure["condition"] == condition and failure["effect"] == "not-started"
    assert failure["context"]["provider_operation"] == "route53/get-hosted-zone"
    assert len(attempts) == (3 if scenario == "timeout" else 1) and CANARY not in output.getvalue() and "SignatureDoesNotMatch" not in output.getvalue()
assert M.InfrastructureFailure("controlled", provider_operation=(CANARY, "get-hosted-zone")).provider_operation is None
M.parse, M.run, M.subprocess.run = old_parse, old_run, old_subprocess

# Exact fixed-endpoint timeout text permits up to three read calls only.
# Success after a timeout is consumed normally, while unknown/foreign messages
# and every mutation timeout remain one call and never authorize replay.
old_subprocess = M.subprocess.run
try:
    for scenario, expected_calls in (("recover", 2), ("exhaust", 3), ("foreign", 1), ("unknown", 1)):
        attempts = []
        def transport(arguments, **options):
            attempts.append(arguments)
            assert options["env"]["AWS_MAX_ATTEMPTS"] == "1"
            assert arguments[arguments.index("--cli-connect-timeout") + 1] == "10"
            assert arguments[arguments.index("--cli-read-timeout") + 1] == "20" and options["timeout"] == 40
            if scenario == "recover" and len(attempts) == 2: return SimpleNamespace(returncode=0, stdout='{"observed":true}', stderr="")
            endpoint = "https://foreign.invalid" if scenario == "foreign" else "https://rds.eu-west-1.amazonaws.com/"
            error = CANARY if scenario == "unknown" else 'aws: [ERROR]: Connect timeout on endpoint URL: "' + endpoint + '"'
            return SimpleNamespace(returncode=255, stdout="", stderr=error)
        M.subprocess.run = transport
        current = M.Provider()
        if scenario == "recover": assert current("rds", "describe-db-instances")["observed"] is True
        else: failed(lambda: current("rds", "describe-db-instances"), "aws-command-failed")
        assert len(attempts) == expected_calls and current.effect == "not-started"
    for process_timeout in (False, True):
        attempts = []
        def mutation_timeout(arguments, **options):
            attempts.append(arguments)
            assert arguments[arguments.index("--cli-connect-timeout") + 1] == "10" and options["timeout"] == 40
            if process_timeout: raise subprocess.TimeoutExpired(arguments, 40)
            return SimpleNamespace(returncode=255, stdout="", stderr='aws: [ERROR]: Connect timeout on endpoint URL: "https://cloudformation.eu-west-1.amazonaws.com/"')
        M.subprocess.run = mutation_timeout
        current = M.Provider()
        current.enable(("cloudformation", "create-change-set"), lambda *args: None)
        failed(lambda: current("cloudformation", "create-change-set", StackName=M.DEPLOY.STACK), "infrastructure-provider-observation-unavailable" if process_timeout else "aws-command-failed")
        assert len(attempts) == 1 and current.effect == "unknown-reconcile-only"
finally:
    M.subprocess.run = old_subprocess
def successor_protocols():
    with tempfile.TemporaryDirectory(prefix="entity-smoke-successor-route-") as temporary:
        root = Path(temporary)
        receipt = {**F.delivery_fixture()["candidate"]}
        predecessor = F.delivery_fixture()["predecessor"]
        history = {"release": {"id": predecessor["release_id"], **{key: predecessor[key] for key in ("source_revision", "image_digest", "proof_set_sha256")}}}
        current = {"target": M.RESOURCE.CLUSTER, "scope": "entity-smoke", "release_id": predecessor["release_id"]}
        actual_digest = M.digest_file
        real_selection = M.rollback_selection
        compatibility_metadata = {"compatibility_id": "rollback-compatibility-" + "8" * 24, "compatibility_sha256": "sha256:" + "8" * 64, "receipt_reference": "github-actions-run:99"}
        admission = []
        with patch.object(M, "ROOT", root), patch.object(M, "source_digest", lambda: "sha256:" + "f" * 64), \
             patch.object(M, "digest_file", lambda path: actual_digest(path) if path.is_file() else "sha256:" + "c" * 64), \
             patch.object(M, "local_qualification", lambda *_: None), patch.object(M.ALIGN, "source_preflight", lambda value: None), \
             patch.object(M.ALIGN, "read_receipt", lambda path: receipt), \
             patch.object(M.ALIGN, "inspect", lambda *arguments: ({"dependency_incarnation_sha256": F.BINDING["dependency_incarnation_sha256"]}, copy.deepcopy(F.PARAMETERS), "fixture")), \
             patch.object(M.SUCCESSION, "current", lambda path: current), patch.object(M.SUCCESSION, "history_record_for_id", lambda *arguments: (history, b"controlled")), \
             patch.object(M, "successor_admission", lambda delivery, binding: admission.append(delivery["delivery_id"])), \
             patch.object(M, "rollback_selection", lambda args, delivery, binding: ({**binding, **{key: predecessor[key] for key in ("source_revision", "image_digest")}}, compatibility_metadata)):
            args = SimpleNamespace(mode="plan", phase="update", receipt=root / "candidate.json", proof_label=F.BINDING["proof_label"],
                                   expected_predecessor=predecessor["release_id"], approved_plan=None, wait_seconds=0, prerequisites=None)
            provider = Provider(lost_execute=True)
            F.accepted_provider(provider, F.delivery_fixture())
            provider.stack["StackStatus"] = "UPDATE_ROLLBACK_COMPLETE"
            # The real public updater must reject unavailable recovery custody
            # before creating a change set, not only when rollback is requested.
            with patch.object(M, "rollback_selection", real_selection):
                failed(lambda: M.run(args, provider), "infrastructure-rollback-compatibility-required")
                args.rollback_receipt = root / "rollback.json"
                args.rollback_compatibility_id = compatibility_metadata["compatibility_id"]
                def unavailable(*arguments): raise M.SUCCESSION.SuccessionFailure("release-succession-compatibility-not-found")
                with patch.object(M.SUCCESSION, "compatibility_record", unavailable):
                    failed(lambda: M.run(args, provider), "release-succession-compatibility-not-found")
            assert not any(op in {"create-change-set", "execute-change-set"} for _, op, _ in provider.calls)
            planned = M.run(args, provider)
            assert planned["plan"]["schema"] == "deploy/entity-smoke-infrastructure-plan/v3" and planned["plan"]["automatic_rollback"] is True
            assert planned["plan"]["resource_modifications"] == 1 and planned["plan"]["resource_replacements"] == 5 and planned["plan"]["resource_additions"] == 0
            delivery, binding = planned["plan"]["delivery"], planned["plan"]["binding"]
            cache = M.delivery_cache(args.proof_label, delivery)
            assert str(cache).endswith("/releases/" + delivery["delivery_id"])
            assert not any(op in {"create-change-set", "execute-change-set"} for _, op, _ in provider.calls)
            args.mode, args.approved_plan = "apply", "sha256:" + "0" * 64
            failed(lambda: M.run(args, provider), "infrastructure-approved-plan-mismatch")
            assert not any(op in {"create-change-set", "execute-change-set"} for _, op, _ in provider.calls)
            args.approved_plan = planned["plan_sha256"]
            # A pending review must not reach execution. Correct observation
            # of the same reserved review may continue without creating again.
            provider.mutate_change = lambda change: change.update(Status="CREATE_IN_PROGRESS")
            assert M.run(args, provider)["verdict"] == "pending"
            assert not any(op == "execute-change-set" for _, op, _ in provider.calls)
            provider.mutate_change = lambda change: None
            failed(lambda: M.run(args, provider), "deployment-execution-uncertain-reconcile-only")
            assert [op for _, op, _ in provider.calls if op in {"create-change-set", "execute-change-set"}] == ["create-change-set", "execute-change-set"]
            with patch.object(M, "local_qualification", admission_unavailable), patch.object(M.ALIGN, "source_preflight", admission_unavailable), \
                 patch.object(M.ALIGN, "inspect", admission_unavailable), patch.object(M, "successor_admission", admission_unavailable), \
                 patch.object(M, "rollback_selection", admission_unavailable):
                provider.stack["StackStatus"] = "UPDATE_IN_PROGRESS"
                assert M.run(args, provider)["verdict"] == "pending"
                provider.stack["StackStatus"] = "UPDATE_COMPLETE"
                assert M.run(args, provider)["verdict"] == "completed"
            assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 1
            packet = M.read_json(cache / "receipts/update.json")
            assert packet["plan"]["rollback_compatibility"] == compatibility_metadata
            for gate in (cache / "realization").glob("controlled-execution-*.json"):
                assert M.read_json(gate)["change_summary"]["operation_counts"] == {"create": 0, "update": 1, "delete": 0, "replace": 5, "broaden-permission": 0}
            assert M.validate_deployment_receipt(packet, binding, delivery) is packet
            legacy = copy.deepcopy(packet)
            legacy["plan"].update(schema="deploy/entity-smoke-infrastructure-plan/v2", automatic_rollback=False)
            legacy["plan_sha256"] = M.DEPLOY.fingerprint(legacy["plan"])
            assert M.validate_deployment_receipt(legacy, binding, delivery) is legacy
            for invalid in (copy.deepcopy(packet), legacy):
                invalid["plan"]["automatic_rollback"] = not invalid["plan"]["automatic_rollback"]
                invalid["plan_sha256"] = M.DEPLOY.fingerprint(invalid["plan"])
                failed(lambda: M.validate_deployment_receipt(invalid, binding, delivery), "infrastructure-delivery-plan-mismatch")
            reused = copy.deepcopy(packet)
            reused["plan"]["rollback_compatibility"]["compatibility_id"] = "accepted-proof-" + predecessor["release_id"].removeprefix("release-")
            reused["plan_sha256"] = M.DEPLOY.fingerprint(reused["plan"])
            assert M.validate_deployment_receipt(reused, binding, delivery) is reused
            reused["plan"]["rollback_compatibility"]["compatibility_id"] = "accepted-proof-" + "9" * 24
            reused["plan_sha256"] = M.DEPLOY.fingerprint(reused["plan"])
            failed(lambda: M.validate_deployment_receipt(reused, binding, delivery), "infrastructure-delivery-compatibility-invalid")
            checked = M.completed_deployment(provider, binding, {**F.PARAMETERS, "ServerDesiredCount": "1"}, delivery)
            assert checked["receipt"] == packet and checked["required_after"] == packet["result"]["facts"]["completed_at"]
            for mutate, code in (
                (lambda item: item["plan"].update(phase="rollback"), "infrastructure-delivery-plan-mismatch"),
                (lambda item: item["plan"].update(previous_parameters_sha256="sha256:" + "0" * 64), "infrastructure-delivery-plan-mismatch"),
                (lambda item: item["result"]["facts"].update(resources_sha256="sha256:" + "0" * 64), "infrastructure-delivery-facts-invalid"),
                (lambda item: item["result"]["reservation"].update(request_sha256="0" * 64), "resource-reservation-mismatch"),
            ):
                changed = copy.deepcopy(packet); mutate(changed); changed["plan_sha256"] = M.DEPLOY.fingerprint(changed["plan"])
                failed(lambda: M.validate_deployment_receipt(changed, binding, delivery), code)
            changed = copy.deepcopy(delivery); changed["candidate"]["image_digest"] = "sha256:" + "0" * 64
            failed(lambda: M.validate_deployment_receipt(packet, binding, changed), "resource-delivery-identity-mismatch")
            args.expected_predecessor = "release-" + "9" * 24
            failed(lambda: M.run(args, provider), "infrastructure-predecessor-mismatch")
            args.expected_predecessor = predecessor["release_id"]
            rollback_receipt = {"source_revision": predecessor["source_revision"], "image_digest": predecessor["image_digest"], "receipt_reference": "github-actions-run:99"}
            compatibility_id = "rollback-compatibility-" + "8" * 24
            compatibility = {"target": M.RESOURCE.CLUSTER, "scope": "entity-smoke", "sha256": "sha256:" + "8" * 64,
                "identity": {"historical_release_id": predecessor["release_id"], "source_revision": predecessor["source_revision"], "image_digest": predecessor["image_digest"],
                    "workloads": ["server", "migration", "administration", "verifier", "database-proof"],
                    "configuration_contract": {"path": str(M.ALIGN.SCOPE), "sha256": binding["configuration_contract_sha256"]},
                    "permission_contract": {"path": str(M.DEPLOY.SOURCE.relative_to(REAL_ROOT)), "sha256": binding["permission_contract_sha256"]}}}
            # Production contract paths remain repository-relative even while
            # this fixture's output store lives under a disposable root.
            with patch.object(M.ALIGN, "read_receipt", lambda path: rollback_receipt if path.name == "rollback.json" else receipt), \
                 patch.object(M.SUCCESSION, "compatibility_record", lambda *arguments: ({}, compatibility)):
                args.phase, args.mode, args.rollback_receipt, args.rollback_compatibility_id = "rollback", "plan", root / "rollback.json", compatibility_id
                # Use the same current-contract path ownership as production.
                with patch.object(M, "ROOT", REAL_ROOT):
                    selected, metadata = real_selection(args, delivery, binding)
                    assert selected["image_digest"] == predecessor["image_digest"] and metadata["compatibility_id"] == compatibility_id
                    compatibility["identity"]["workloads"].pop()
                    failed(lambda: real_selection(args, delivery, binding), "infrastructure-rollback-workloads-incomplete")
                    compatibility["identity"]["workloads"].append("database-proof")
                with patch.object(M, "rollback_selection", lambda *arguments: (selected, metadata)):
                    rollback_plan = M.run(args, provider)
                    assert rollback_plan["plan"]["binding"] == selected and rollback_plan["plan"]["delivery"] == delivery
                    args.approved_plan, args.mode = rollback_plan["plan_sha256"], "apply"
                    provider.lost_execute = False
                    assert M.run(args, provider)["verdict"] == "completed"
                    with patch.object(M, "local_qualification", admission_unavailable), patch.object(M.ALIGN, "inspect", admission_unavailable):
                        assert M.run(args, provider)["verdict"] == "completed"
                    assert sum(op == "execute-change-set" for _, op, _ in provider.calls) == 2
            assert admission and current["release_id"] == predecessor["release_id"]
            for path in cache.rglob("*.json"):
                assert CANARY not in path.read_text() and F.PARAMETERS["AdministratorSecretArn"] not in path.read_text()


# A returned non-success review is also terminal for the connected invocation;
# no execute call follows, even if a future review owner returns rather than raises.
actual_run = M.run
failed(lambda: M.parse(["--mode", "apply", "--phase", "create", "--receipt", "fixture.json",
    "--proof-label", F.BINDING["proof_label"], "--approved-plan", "sha256:" + "1" * 64]), "infrastructure-arguments-invalid")
for verdict in ("pending", "blocked", "failed", "uncertain"):
    args = SimpleNamespace(mode="apply", receipt=Path("fixture.json"))
    report = {"verdict": verdict, "effect": "not-started"}
    with patch.object(M.ALIGN, "read_receipt", return_value={}), \
         patch.object(M, "resume_execution", return_value=None), \
         patch.object(M, "run", return_value=report) as child:
        assert actual_run(args, Provider()) is report
        assert child.call_count == 1 and child.call_args.args[0].mode == "review"

successor_protocols()
print(json.dumps({"schema": "deploy/entity-smoke-infrastructure-route-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "prerequisites": "controlled-source-custody-alignment-and-policy-responses-not-qualification",
                  "checks": ["actual-generic-gates", "plan-is-not-approval", "changed-plan-rejected", "review-before-execute", "lost-execution-observe-only", "resume-before-new-admission", "original-admission-not-restamped", "resume-pending-failed-and-unknown", "successor-and-rollback-resume", "completed-receipt-reconciliation", "no-fictional-runtime-facts", "same-label-ownership", "activation-proof-required", "activation-binds-four-real-collector-receipts", "activation-resume-no-old-zero-count-requirement", "submission-must-match-plan", "missing-gate-observation-rejected", "actual-cli-safe-rejection", "no-provider-on-offline-failure", "fixed-provider-endpoint", "no-automatic-mutation-retry"]}))
