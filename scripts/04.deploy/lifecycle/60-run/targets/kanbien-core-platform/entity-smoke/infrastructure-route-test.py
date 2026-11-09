#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.infrastructure-route
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
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
original = {name: getattr(M, name) for name in ("ROOT", "source_digest", "digest_file", "local_checks")}
old_receipt, old_preflight, old_inspect = M.ALIGN.read_receipt, M.ALIGN.source_preflight, M.ALIGN.inspect
with tempfile.TemporaryDirectory(prefix="entity-smoke-infrastructure-route-") as temporary:
    root = Path(temporary)
    M.ROOT = root
    artifact = "sha256:" + "f" * 64
    M.source_digest = lambda: artifact
    actual_digest = original["digest_file"]
    M.digest_file = lambda path: actual_digest(path) if path.is_file() else "sha256:" + "c" * 64
    source_calls = []
    M.local_checks = lambda: source_calls.append("registered-local-proof-double")
    M.ALIGN.read_receipt = lambda path: {"source_revision": F.BINDING["source_revision"], "image_digest": F.BINDING["image_digest"], "receipt_reference": "github-actions-run:123"}
    M.ALIGN.source_preflight = lambda receipt: source_calls.append("committed-source-double")
    M.ALIGN.inspect = lambda provider, receipt, checked_at: ({"dependency_incarnation_sha256": F.BINDING["dependency_incarnation_sha256"]}, copy.deepcopy(F.PARAMETERS), "private-group")
    def arguments(mode="plan", label=None, approved=None, phase="create", prerequisites=None):
        return SimpleNamespace(mode=mode, phase=phase, receipt=root / "controlled-receipt.json", proof_label=label or F.BINDING["proof_label"], approved_plan=approved, wait_seconds=0, prerequisites=prerequisites, validate_arguments=False)
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
    # Submitted and completed are different states. A lost response may only
    # observe the reserved operation, never submit a second execute request.
    provider.lost_execute = True
    failed(lambda: M.run(arguments("execute", approved=plan["plan_sha256"]), provider), "deployment-execution-uncertain-reconcile-only")
    completed = M.run(arguments("execute", approved=plan["plan_sha256"]), provider)
    assert completed["verdict"] == "completed"
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    assert M.run(arguments("execute", approved=plan["plan_sha256"]), provider)["receipt"] == completed["receipt"]
    assert sum(operation == "execute-change-set" for _, operation, _ in provider.calls) == 1
    evidence = sorted(root.rglob("realization/*.json"))
    assert evidence
    for path in evidence:
        value = json.loads(path.read_text())
        assert value["plan_sha256"] == plan["plan_sha256"]
        M.GATE.validate_facts(value["facts"], M.GateBook(artifact, root / "unused").contract, "entity-smoke-infrastructure-control", M.GateBook(artifact, root / "unused").known, value["facts"]["gate_evidence"][-1]["gate"])
        assert CANARY not in path.read_text() and "arn:" not in path.read_text()
    assert not any("runtime" in entry["component_id"] for entry in value["facts"]["component_evidence"])
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
    activation_plan = M.run(activation, provider)
    activation.mode, activation.approved_plan = "review", activation_plan["plan_sha256"]
    assert M.run(activation, provider)["verdict"] == "reviewed"
    activation.mode = "execute"; provider.lost_execute = False
    assert M.run(activation, provider)["verdict"] == "completed"
    assert M.run(activation, provider)["verdict"] == "completed"
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
    assert source_calls.count("committed-source-double") == source_calls.count("registered-local-proof-double")
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

# A failed real local-check consumer retains its safe report reference at the
# actual main reporter, without forwarding the child's native stderr.
with tempfile.TemporaryDirectory(prefix="entity-smoke-local-proof-reference-") as temporary:
    root = Path(temporary)
    reference = ".cache/test-runs/20261108T000000Z-" + "1" * 32 + "/report.json"
    report = root / reference; report.parent.mkdir(parents=True); report.write_text('{"fixture":true}')
    old_root, old_run, old_parse = M.ROOT, M.subprocess.run, M.parse
    old_read, old_source = M.ALIGN.read_receipt, M.ALIGN.source_preflight
    M.ROOT = root
    M.subprocess.run = lambda *arguments, **options: SimpleNamespace(returncode=1, stdout=json.dumps({"run_report_path": reference, "checks": [], "findings": []}), stderr=CANARY)
    M.parse = lambda: SimpleNamespace(receipt=root / "controlled.json", mode="plan", phase="create", proof_label=F.BINDING["proof_label"], validate_arguments=False)
    M.ALIGN.read_receipt, M.ALIGN.source_preflight = lambda path: {}, lambda receipt: None
    output = io.StringIO()
    with redirect_stdout(output): status = M.main()
    failure = json.loads(output.getvalue())
    assert status == 1 and failure["condition"] == "infrastructure-local-proof-not-passed" and failure["evidence_reference"] == reference
    assert CANARY not in output.getvalue() and failure["effect"] == "not-started"
    M.ROOT, M.subprocess.run, M.parse = old_root, old_run, old_parse
    M.ALIGN.read_receipt, M.ALIGN.source_preflight = old_read, old_source

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
assert options["env"]["AWS_MAX_ATTEMPTS"] == "1" and options["timeout"] == 30
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
    assert options["env"]["AWS_MAX_ATTEMPTS"] == "1" and options["timeout"] == 30
successful_calls = len(observed)
failed(lambda: provider("ecs", "run-task", cluster=CANARY), "infrastructure-provider-operation-prohibited")
provider.enable(("cloudformation", "create-change-set"), lambda operation, parameters: None)
failed(lambda: provider("cloudformation", "create-change-set", StackName="kanbien-staging"), "infrastructure-write-target-invalid")
assert len(observed) == successful_calls
M.subprocess.run = old_subprocess

# Actual provider failures retain the finite attempted operation at the final
# reporter, never provider parameters, native messages or automatic retries.
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
        if scenario == "timeout": raise subprocess.TimeoutExpired(arguments, 30, stderr=CANARY)
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
    assert len(attempts) == 1 and CANARY not in output.getvalue() and "SignatureDoesNotMatch" not in output.getvalue()
assert M.InfrastructureFailure("controlled", provider_operation=(CANARY, "get-hosted-zone")).provider_operation is None
M.parse, M.run, M.subprocess.run = old_parse, old_run, old_subprocess
print(json.dumps({"schema": "deploy/entity-smoke-infrastructure-route-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "prerequisites": "controlled-source-custody-alignment-and-policy-responses-not-qualification",
                  "checks": ["actual-generic-gates", "plan-is-not-approval", "changed-plan-rejected", "review-before-execute", "lost-execution-observe-only", "completed-receipt-reconciliation", "no-fictional-runtime-facts", "same-label-ownership", "activation-proof-required", "activation-binds-four-real-collector-receipts", "activation-resume-no-old-zero-count-requirement", "submission-must-match-plan", "missing-gate-observation-rejected", "actual-cli-safe-rejection", "no-provider-on-offline-failure", "fixed-provider-endpoint", "no-automatic-mutation-retry"]}))
