#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.infrastructure.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-10"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Enforce source, custody, actual target alignment, normal realization gates and exact approved-plan binding before isolated infrastructure effects.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [aws-mutation, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.infrastructure
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/script.sh
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import yaml


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


ROOT = Path(__file__).resolve().parents[7]
DIRECTORY = Path(__file__).parent
DEPLOY = module("entity_smoke_public_deployment", DIRECTORY / "deployment-control.py")
RESOURCE = DEPLOY.RESOURCE
ALIGN = module("entity_smoke_public_alignment", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py")
RESPONSE = module("entity_smoke_public_response", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/response.py")
GATE = module("entity_smoke_public_gate", ROOT / "scripts/04.deploy/operational-realization-gate/script.py")
CONTRACT = ROOT / ALIGN.TARGET / "20-scopes/entity-smoke/00-declaration/infrastructure-realization-contract.v2.yml"
READS = ALIGN.READS | {("cloudformation", operation) for operation in ("describe-change-set", "get-template", "list-stack-resources", "describe-stack-events", "validate-template")} | {
    ("iam", "get-role"), ("iam", "simulate-principal-policy"), ("ecs", "describe-services"), ("ecs", "describe-tasks"),
    ("ecs", "list-tasks"), ("logs", "get-log-events"),
}
WRITES = {("cloudformation", "create-change-set"), ("cloudformation", "execute-change-set")}


class InfrastructureFailure(Exception):
    def __init__(self, code, evidence_reference=None, *, provider_operation=None):
        super().__init__(code)
        self.code = code
        self.evidence_reference = evidence_reference
        self.provider_operation = provider_operation if isinstance(provider_operation, tuple) and all(isinstance(item, str) for item in provider_operation) and provider_operation in READS | WRITES else None


def require(value, code):
    if not value: raise InfrastructureFailure(code)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def digest_file(path):
    RESOURCE.CONTROL.no_symlinks(path)
    try: return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError): raise InfrastructureFailure("infrastructure-source-unavailable") from None


def read_json(path):
    RESOURCE.CONTROL.no_symlinks(path)
    try:
        with path.open("rb") as stream: raw = stream.read(1048577)
        require(len(raw) <= 1048576, "infrastructure-input-too-large")
        return json.loads(raw)
    except (OSError, ValueError, TypeError, UnicodeError): raise InfrastructureFailure("infrastructure-input-unavailable") from None


class Provider:
    """A single-call, no-retry CLI boundary; read capability is the default.

    A plan hash is not proof of human approval. The invoking agent/operator
    must hold the concrete AWS approval required by the execution workflow.
    """
    def __init__(self):
        self.write_operation = None
        self.prewrite = None
        self.effect = "not-started"

    def enable(self, operation, prewrite):
        require(operation in WRITES, "infrastructure-write-capability-invalid")
        self.write_operation = operation
        self.prewrite = prewrite

    def __call__(self, service, operation, **parameters):
        selected = service, operation
        require(selected in READS or selected == self.write_operation, "infrastructure-provider-operation-prohibited")
        if selected in WRITES:
            try:
                require(parameters.get("StackName") == DEPLOY.STACK or isinstance(parameters.get("StackName"), str) and parameters["StackName"].startswith("arn:aws:cloudformation:" + ALIGN.REGION + ":" + ALIGN.ACCOUNT + ":stack/" + DEPLOY.STACK + "/"), "infrastructure-write-target-invalid")
                require(callable(self.prewrite), "infrastructure-write-preflight-missing")
                self.prewrite(operation, parameters)
            except (InfrastructureFailure, RESOURCE.ResourceFailure) as failure:
                raise RESOURCE.SubmissionNotStarted(failure.code) from None
            except Exception:
                raise RESOURCE.SubmissionNotStarted("infrastructure-submission-preflight-not-confirmed") from None
            self.write_operation, self.prewrite = None, None
            self.effect = "unknown-reconcile-only"
        return self._invoke(service, operation, parameters)

    def _invoke(self, service, operation, parameters):
        global_services = {"iam": "iam.amazonaws.com", "route53": "route53.amazonaws.com", "budgets": "budgets.amazonaws.com"}
        hostname = global_services.get(service, ("api.ecr" if service == "ecr" else service) + "." + ALIGN.REGION + ".amazonaws.com")
        signing_region = "us-east-1" if service in global_services else ALIGN.REGION
        def failure(code):
            return InfrastructureFailure(code, provider_operation=(service, operation))
        arguments = ["aws", service, operation, "--profile", ALIGN.PROFILE, "--region", signing_region,
                     "--endpoint-url", "https://" + hostname, "--output", "json", "--no-paginate", "--no-cli-pager",
                     "--cli-connect-timeout", "5", "--cli-read-timeout", "20", "--cli-input-json", json.dumps(parameters)]
        try:
            result = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=30,
                                    env={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1", "AWS_EC2_METADATA_DISABLED": "true"})
        except (OSError, UnicodeError, subprocess.SubprocessError): raise failure("infrastructure-provider-observation-unavailable") from None
        if result.returncode:
            code = RESPONSE.classify_error(service, operation, result.stderr)
            if code == "aws-resource-missing": raise RESOURCE.ResourceMissing()
            raise failure(code)
        try: value = json.loads(result.stdout) if result.stdout.strip() else {}
        except (ValueError, TypeError): raise failure("infrastructure-provider-response-invalid") from None
        if not isinstance(value, dict): raise failure("infrastructure-provider-response-invalid")
        return value


def local_checks():
    arguments = ["python3", "-B", "scripts/repo/check-selection/script.py", "--checks", "entity-smoke-composition", "secret-dependency-declaration-regression", "--execute-local", "--json"]
    try:
        result = subprocess.run(arguments, cwd=ROOT, capture_output=True, text=True, timeout=180)
        value = json.loads(result.stdout)
    except (OSError, ValueError, TypeError, UnicodeError, subprocess.SubprocessError): raise InfrastructureFailure("infrastructure-local-proof-unavailable") from None
    checks = value.get("checks") if isinstance(value, dict) else None
    reference = value.get("run_report_path") if isinstance(value, dict) else None
    retained = isinstance(reference, str) and re.fullmatch(r"\.cache/test-runs/[0-9]{8}T[0-9]{6}Z-[a-f0-9]{32}/report\.json", reference) is not None
    if retained:
        RESOURCE.CONTROL.no_symlinks(ROOT / reference)
        retained = (ROOT / reference).is_file()
    if result.returncode != 0:
        raise InfrastructureFailure("infrastructure-local-proof-not-passed", reference if retained else None)
    require(result.returncode == 0 and isinstance(value, dict) and value.get("findings") == [] and isinstance(checks, list)
            and {item.get("check_id") for item in checks if isinstance(item, dict)} == {"entity-smoke-composition", "secret-dependency-declaration-regression"}
            and all(isinstance(item, dict) and item.get("status") == "passed" for item in checks), "infrastructure-local-proof-not-passed")


def source_digest():
    paths = sorted([*DIRECTORY.glob("*.py"), *DIRECTORY.glob("*.sh"), CONTRACT, DEPLOY.SOURCE,
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/response.py",
                    ROOT / "scripts/04.deploy/operational-realization-gate/script.py",
                    Path(ALIGN.__file__)])
    return DEPLOY.fingerprint({str(path.relative_to(ROOT)): digest_file(path) for path in paths})


def filesystem_preflight(cache):
    RESOURCE.CONTROL.no_symlinks(cache)
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    probe = cache / ("preflight-" + uuid.uuid4().hex + ".json")
    value = {"schema": "deploy/entity-smoke-local-intent-preflight/v1", "nonsecret": True}
    require(RESOURCE.write_exclusive(probe, value) and read_json(probe) == value and probe.stat().st_mode & 0o777 == 0o600, "infrastructure-intent-store-not-confirmed")
    probe.unlink()
    descriptor = os.open(cache, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def operator_preflight(provider):
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == ALIGN.ACCOUNT and isinstance(arn, str) and re.fullmatch(r"arn:aws:sts::" + ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn) is not None, "infrastructure-operator-identity-not-confirmed")
    name = arn.split("/")[1]
    role = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(role, dict) and role.get("RoleName") == name and isinstance(role.get("Arn"), str) and role["Arn"].startswith("arn:aws:iam::" + ALIGN.ACCOUNT + ":role/") and role["Arn"].endswith("/" + name), "infrastructure-operator-role-not-confirmed")
    actions = {"cloudformation:CreateChangeSet", "cloudformation:ExecuteChangeSet"}
    result = provider("iam", "simulate-principal-policy", PolicySourceArn=role["Arn"], ActionNames=sorted(actions), ResourceArns=["arn:aws:cloudformation:" + ALIGN.REGION + ":" + ALIGN.ACCOUNT + ":stack/" + DEPLOY.STACK + "/*"])
    evaluations = result.get("EvaluationResults") if isinstance(result, dict) else None
    require(isinstance(evaluations, list) and len(evaluations) == len(actions) and result.get("IsTruncated", False) is False and {item.get("EvalActionName") for item in evaluations if isinstance(item, dict)} == actions and all(isinstance(item, dict) and item.get("EvalDecision") == "allowed" and not item.get("MissingContextValues") for item in evaluations), "infrastructure-operator-policy-preflight-not-confirmed")
    # Policy simulation is a preflight, never a claim that execution succeeded.
    return DEPLOY.fingerprint({"account": caller["Account"], "role": role["Arn"]})


class GateBook:
    def __init__(self, artifact, cache, *, contract=None, artifact_bindings=None):
        self.contract = yaml.safe_load(CONTRACT.read_text()) if contract is None else contract
        self.identity = GATE.validate_contract(self.contract)
        self.component_check_id = "feature-infrastructure-components" if contract is None else self.identity + "-components"
        self.known = GATE.ids(self.contract)[1]
        self.cache, self.components, self.gates = cache, {}, []
        self.plan_digest = None
        bindings = {"infrastructure-controller-source": artifact} if artifact_bindings is None else artifact_bindings
        require(set(bindings) == {item["id"] for item in self.contract["artifacts"]}, "infrastructure-artifact-binding-incomplete")
        self.facts = {"schema": GATE.FACTS_SCHEMA, "contract_id": self.identity, "gate_evidence": [], "component_evidence": [],
                      "artifact_bindings": [{"component_id": name, "immutable_reference": selected,
                                             "check_id": self.contract["gates"][1]["evidence"][0], "timestamp": now(), "verdict": "passed"} for name, selected in sorted(bindings.items())]}

    def component(self, identifier):
        require(identifier in self.known and identifier not in self.components, "infrastructure-component-observation-invalid")
        self.components[identifier] = now()

    def gate(self, identifier):
        require(identifier == GATE.GATE_ORDER[len(self.gates)], "infrastructure-gate-order-invalid")
        self.gates.append(identifier)
        self.facts["gate_evidence"].append({"gate": identifier, "check_id": self.contract["gates"][len(self.gates) - 1]["evidence"][0], "timestamp": now(), "verdict": "passed", "input_sha256": GATE.evidence_bindings(self.contract, self.facts)["gates"][identifier]})

    def bind_plan(self, selected):
        require(isinstance(selected, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", selected) is not None and self.plan_digest in (None, selected), "infrastructure-evidence-plan-mismatch")
        self.plan_digest = selected

    def validate(self, through, change_count=None, activate=False, *, operation_class=None):
        require(set(self.components) == set(self.known), "infrastructure-component-proof-incomplete")
        require(self.plan_digest is not None, "infrastructure-evidence-plan-missing")
        bindings = GATE.evidence_bindings(self.contract, self.facts)
        self.facts["component_evidence"] = [{"component_id": name, "component_kind": self.known[name], "check_id": self.component_check_id, "timestamp": self.components[name], "verdict": "passed", "input_sha256": bindings["components"][name]} for name in sorted(self.components)]
        GATE.validate_facts(self.facts, self.contract, self.identity, self.known, through)
        summary = None
        if change_count is not None:
            selected_operation = ("update" if activate else "create") if operation_class is None else operation_class
            require(selected_operation in {"create", "update", "delete"}, "infrastructure-change-operation-invalid")
            summary = {"schema": GATE.CHANGE_SCHEMA, "contract_id": self.identity, "check_id": self.contract["gates"][4]["evidence"][0], "timestamp": now(),
                       "input_sha256": bindings["gates"]["change-set"], "operation_counts": {name: change_count if name == selected_operation else 0 for name in ("create", "update", "delete", "replace", "broaden-permission")}}
            GATE.validate_change_summary(summary, self.contract, self.identity, self.facts)
        path = self.cache / (through + "-" + uuid.uuid4().hex + ".json")
        require(RESOURCE.write_exclusive(path, {"plan_sha256": self.plan_digest, "facts": self.facts, "change_summary": summary}), "infrastructure-gate-evidence-retention-failed")
        return path


def binding_for(receipt, alignment):
    return {"source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"],
            "configuration_contract_sha256": digest_file(ROOT / ALIGN.SCOPE), "permission_contract_sha256": digest_file(DEPLOY.SOURCE),
            "dependency_incarnation_sha256": alignment["dependency_incarnation_sha256"]}


def activation_prerequisites(provider, path, binding, parameters, cache, store, *, resuming=False):
    require(path is not None, "infrastructure-activation-proof-required")
    previous = read_json(cache / "receipts/create.json")
    require(isinstance(previous, dict) and set(previous) == {"schema", "binding", "result"} and previous["schema"] == "deploy/entity-smoke-infrastructure-receipt/v1" and previous["binding"] == binding
            and isinstance(previous["result"], dict) and previous["result"].get("status") == "completed" and isinstance(previous["result"].get("reservation"), dict)
            and isinstance(previous["result"]["reservation"].get("request"), dict) and isinstance(previous["result"].get("facts"), dict)
            and isinstance(previous["result"]["facts"].get("resources"), dict), "infrastructure-create-receipt-invalid")
    execution = previous["result"]["reservation"]["request"]
    require(all(execution.get(key) == value for key, value in DEPLOY.request(binding, {**parameters, "ServerDesiredCount": "0"}, False).items()), "infrastructure-create-receipt-binding-mismatch")
    if resuming:
        require(store.read("deploy-execute-create", execution) == previous["result"]["reservation"], "infrastructure-create-reservation-not-confirmed")
        created = previous["result"]
        response = provider("cloudformation", "list-stack-resources", StackName=created["facts"]["stack_arn"])
        rows = response.get("StackResourceSummaries") if isinstance(response, dict) else None
        require(isinstance(rows, list) and len(rows) == len(DEPLOY.RESOURCE_TYPES) and not response.get("NextToken")
                and all(isinstance(row, dict) and all(isinstance(row.get(field), str) for field in ("LogicalResourceId", "ResourceType", "PhysicalResourceId")) for row in rows)
                and {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows} == created["facts"]["resources"], "infrastructure-activation-resource-lineage-mismatch")
    else:
        created = DEPLOY.observe(provider, store, binding, {**parameters, "ServerDesiredCount": "0"}, execution["change_set_arn"], execution["stack_arn"])
        require(created["status"] == "completed" and created == previous["result"], "infrastructure-create-state-not-confirmed")
    manifest = read_json(path)
    declaration = yaml.safe_load((CONTRACT.parent / "declaration-contract.yml").read_text())
    workloads = {item["id"]: item for item in declaration["health_recovery"]["workloads"]}
    expected = {"bootstrap": ("administration", "bootstrap", "AdministrationTaskDefinition"), "migration": ("migration", "apply", "MigrationTaskDefinition"),
                "grant-runtime": ("administration", "grant-runtime", "AdministrationTaskDefinition"), "permissions": ("database-proof", "permissions", "DatabaseProofTaskDefinition")}
    require(isinstance(manifest, dict) and set(manifest) == set(expected), "infrastructure-activation-proof-set-invalid")
    previous_stop = RESOURCE.timestamp(created["reservation"]["reserved_at"])
    for name, (workload, operation, logical) in expected.items():
        entry = manifest[name]
        require(isinstance(entry, dict) and set(entry) == {"reservation", "receipt"}, "infrastructure-activation-proof-invalid")
        reservation, receipt = entry["reservation"], entry["receipt"]
        retained = RESOURCE.EVIDENCE.validate_retained(receipt, reservation)
        require(retained["workload"] == workload and retained["operation"] == operation and all(reservation["request"].get(key) == value for key, value in binding.items())
                and retained["task"]["definition"] == created["facts"]["resources"][logical]["physical_id"], "infrastructure-activation-proof-binding-mismatch")
        completion = workloads["entity-smoke-" + workload]["completion"]
        require(retained["task"]["completion_duration_seconds"] <= completion["deadline_seconds"] and reservation["request"]["deadline_seconds"] <= completion["deadline_seconds"]
                and retained["result"]["code"] == completion["success"]["result_code"], "infrastructure-activation-completion-contract-mismatch")
        require(previous_stop is None or RESOURCE.timestamp(retained["task"]["created_at"]) >= previous_stop, "infrastructure-activation-proof-order-invalid")
        task = RESOURCE.only(provider("ecs", "describe-tasks", cluster=RESOURCE.CLUSTER, tasks=[retained["task"]["arn"]]), "tasks")
        logs = RESOURCE.EVIDENCE.read_logs(provider, reservation["request"], retained["task"]["arn"])
        current = RESOURCE.EVIDENCE.collect(task, reservation, logs, retained["collected_at"])
        require(current == retained, "infrastructure-activation-proof-not-confirmed")
        previous_stop = RESOURCE.timestamp(retained["task"]["stopped_at"])
    require(-60 <= (datetime.now(timezone.utc) - previous_stop).total_seconds() <= GATE.CURRENT_EVIDENCE_MAX_AGE_SECONDS, "infrastructure-activation-proof-not-fresh")


def run(args, provider):
    receipt = ALIGN.read_receipt(args.receipt.absolute())
    ALIGN.source_preflight(receipt)
    local_checks()
    artifact = source_digest()
    cache = ROOT / ".cache/entity-smoke-live" / args.proof_label
    filesystem_preflight(cache)
    store = RESOURCE.ResourceStore(cache / "attempts")
    book = GateBook(artifact, cache / "realization")
    for name in ("infrastructure-controller-source", "attempt-store", "infrastructure-safe-reports", "infrastructure-reconciliation", "infrastructure-controller"):
        book.component(name)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration")
    alignment, parameters, _ = ALIGN.inspect(provider, receipt, now())
    activate = args.phase == "activate"
    parameters["ServerDesiredCount"] = "1" if activate else "0"
    binding = {**binding_for(receipt, alignment), "proof_label": args.proof_label}
    DEPLOY.parameters_for(binding, parameters, activate)
    operator = operator_preflight(provider)
    existing_execution = None
    if args.mode == "execute":
        change = provider("cloudformation", "describe-change-set", StackName=DEPLOY.STACK, ChangeSetName=DEPLOY.change_name(binding, activate))
        existing_execution = store.read("deploy-execute-activate" if activate else "deploy-execute-create", {**DEPLOY.request(binding, parameters, activate), "change_set_arn": change.get("ChangeSetId"), "stack_arn": change.get("StackId")})
        if existing_execution is not None: provider.effect = "original-operation-reconcile-only"
    book.component("infrastructure-operator"); book.component("control-state-connection"); book.component("intent-connection")
    if activate:
        activation_prerequisites(provider, args.prerequisites.absolute() if args.prerequisites else None, binding, parameters, cache, store, resuming=existing_execution is not None)
    else:
        try:
            state = RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=DEPLOY.STACK), "Stacks")
        except RESOURCE.ResourceMissing: state = None
        intent = DEPLOY.request(binding, parameters, False)
        if state is not None:
            original_review = store.read("deploy-create-change-set", intent)
            require(original_review is not None, "infrastructure-existing-stack-not-owned-by-attempt")
            DEPLOY.initial_stack(provider, state, binding, parameters, original_review, executed=existing_execution is not None)
    book.component("resource-control-state")
    plan = {"schema": "deploy/entity-smoke-infrastructure-plan/v1", "target": RESOURCE.CLUSTER, "scope": "entity-smoke", "account": ALIGN.ACCOUNT, "region": ALIGN.REGION,
            "phase": args.phase, "binding": binding, "operator_sha256": operator, "controller_sha256": artifact, "graph_sha256": digest_file(CONTRACT),
            "parameters_sha256": DEPLOY.fingerprint(parameters), "template_sha256": digest_file(DEPLOY.SOURCE),
            "package_custody_reference": receipt["receipt_reference"], "resource_additions": 0 if activate else 30, "resource_modifications": 1 if activate else 0,
            "server_desired_count": 1 if activate else 0, "database_data_or_schema_changes": False, "source_database_replacement": False,
            "baseline_database_ingress_additions": 0 if activate else 4, "baseline_endpoint_ingress_additions": 0 if activate else 5, "automatic_rollback": False}
    plan_digest = DEPLOY.fingerprint(plan)
    book.bind_plan(plan_digest); book.component("infrastructure-inputs")
    book.gate("live-read"); book.validate("live-read")
    if args.mode == "plan": return {"verdict": "planned", "plan": plan, "plan_sha256": plan_digest, "effect": "not-started"}
    require(args.approved_plan == plan_digest, "infrastructure-approved-plan-mismatch")
    intent = DEPLOY.request(binding, parameters, activate)
    phase = "deploy-activate-change-set" if activate else "deploy-create-change-set"
    if args.mode == "execute": require(store.read(phase, intent) is not None, "infrastructure-reviewed-attempt-required")
    def prewrite(operation, supplied):
        require(source_digest() == artifact and digest_file(ROOT / ALIGN.SCOPE) == binding["configuration_contract_sha256"], "infrastructure-source-changed-before-submission")
        if operation == "create-change-set":
            expected = {"StackName", "ChangeSetName", "ChangeSetType", "TemplateBody", "Parameters", "Capabilities", "Description", "ClientToken", "Tags"} | (set() if activate else {"OnStackFailure"})
            require(set(supplied) == expected and supplied["ChangeSetName"] == DEPLOY.change_name(binding, activate) and supplied["ChangeSetType"] == ("UPDATE" if activate else "CREATE")
                    and supplied["Capabilities"] == ["CAPABILITY_IAM"] and "sha256:" + hashlib.sha256(supplied["TemplateBody"].encode()).hexdigest() == plan["template_sha256"]
                    and re.fullmatch(r"es-[a-f0-9]{32}", supplied["ClientToken"]) is not None and supplied["ClientToken"] == supplied["Description"], "infrastructure-submission-does-not-match-plan")
            reserved = store.read(phase, intent)
            require(reserved is not None and supplied["ClientToken"] == reserved["operation_id"] and isinstance(supplied["Tags"], list) and len(supplied["Tags"]) == 3
                    and isinstance(supplied["Parameters"], list) and all(isinstance(item, dict) and set(item) == {"ParameterKey", "ParameterValue"} for item in supplied["Parameters"]), "infrastructure-submission-does-not-match-plan")
            DEPLOY.exact_parameters(supplied["Parameters"], parameters)
            DEPLOY.exact_tags(supplied["Tags"], binding)
            require(activate or supplied.get("OnStackFailure") == "DO_NOTHING", "infrastructure-submission-does-not-match-plan")
        else:
            require(set(supplied) == {"StackName", "ChangeSetName", "ClientRequestToken"} | ({"DisableRollback"} if activate else set())
                    and supplied["StackName"] == reviewed["facts"]["stack_arn"] and supplied["ChangeSetName"] == reviewed["facts"]["change_set_arn"]
                    and re.fullmatch(r"es-[a-f0-9]{32}", supplied["ClientRequestToken"]) is not None and (not activate or supplied["DisableRollback"] is True), "infrastructure-submission-does-not-match-plan")
            reserved = store.read("deploy-execute-activate" if activate else "deploy-execute-create", {**intent, "change_set_arn": supplied["ChangeSetName"], "stack_arn": supplied["StackName"]})
            require(reserved is not None and supplied["ClientRequestToken"] == reserved["operation_id"], "infrastructure-submission-does-not-match-plan")
    if args.mode == "review": provider.enable(("cloudformation", "create-change-set"), prewrite)
    if existing_execution is not None:
        review_reservation = store.read(phase, intent)
        require(review_reservation is not None, "infrastructure-reviewed-attempt-required")
        reviewed = {"status": "reviewed", "facts": DEPLOY.reviewed_change(provider, binding, parameters, review_reservation, activate, executed=True)}
        require(reviewed["facts"] is not None, "infrastructure-executed-change-unavailable")
    else:
        reviewed = DEPLOY.prepare(provider, store, binding, parameters, activate=activate)
    if reviewed["status"] == "pending": return {"verdict": "pending", "phase": args.phase, "plan_sha256": plan_digest, "effect": provider.effect}
    book.gate("change-set"); book.validate("change-set", reviewed["facts"]["resource_count"], activate)
    if args.mode == "review": return {"verdict": "reviewed", "phase": args.phase, "plan_sha256": plan_digest, "effect": "change-set-reviewed-not-executed"}
    validation = provider("cloudformation", "validate-template", TemplateBody=DEPLOY.source()[0])
    require(isinstance(validation.get("Parameters"), list) and len(validation["Parameters"]) == len(DEPLOY.PARAMETERS)
            and all(isinstance(item, dict) and isinstance(item.get("ParameterKey"), str) for item in validation["Parameters"])
            and {item["ParameterKey"] for item in validation["Parameters"]} == DEPLOY.PARAMETERS
            and validation.get("Capabilities") == ["CAPABILITY_IAM"] and not validation.get("DeclaredTransforms"), "infrastructure-execution-boundary-preflight-not-confirmed")
    require(operator_preflight(provider) == operator, "infrastructure-operator-changed")
    book.gate("execution-preflight"); book.validate("execution-preflight", reviewed["facts"]["resource_count"], activate)
    if existing_execution is None: provider.enable(("cloudformation", "execute-change-set"), prewrite)
    facts = reviewed["facts"]
    result = DEPLOY.execute(provider, store, binding, parameters, facts["change_set_arn"], facts["stack_arn"], activate=activate)
    deadline = time.monotonic() + args.wait_seconds
    while result["status"] == "pending" and time.monotonic() < deadline:
        print(json.dumps({"schema": "deploy/entity-smoke-infrastructure-progress/v1", "phase": args.phase, "state": "waiting-for-original-operation"}), flush=True, file=os.sys.stderr)
        time.sleep(2)
        result = DEPLOY.observe(provider, store, binding, parameters, facts["change_set_arn"], facts["stack_arn"], activate=activate)
    if result["status"] != "completed": return {"verdict": "pending", "phase": args.phase, "plan_sha256": plan_digest, "effect": "original-operation-not-terminal"}
    book.gate("controlled-execution"); book.validate("controlled-execution", facts["resource_count"], activate)
    path = cache / "receipts" / (args.phase + ".json")
    retained = {"schema": "deploy/entity-smoke-infrastructure-receipt/v1", "binding": binding, "result": result}
    if not RESOURCE.write_exclusive(path, retained): require(read_json(path) == retained, "infrastructure-receipt-conflict")
    return {"verdict": "completed", "phase": args.phase, "plan_sha256": plan_digest, "receipt": str(path.relative_to(ROOT)), "effect": "owned-infrastructure-observed"}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(InfrastructureFailure("infrastructure-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "review", "execute"), required=True)
    parser.add_argument("--phase", choices=("create", "activate"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--prerequisites", type=Path)
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) is not None and 0 <= args.wait_seconds <= 60, "infrastructure-arguments-invalid")
    require(args.mode == "plan" or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan) is not None, "infrastructure-approved-plan-required")
    require(args.phase != "activate" or args.prerequisites is not None, "infrastructure-activation-proof-required")
    return args


def main():
    provider = Provider()
    context = {}
    try:
        args = parse()
        context = {"mode": args.mode, "phase": args.phase, "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = run(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-infrastructure-report/v1", "target": RESOURCE.CLUSTER, "scope": "entity-smoke", **result}, sort_keys=True))
        return 0 if result["verdict"] in {"planned", "reviewed", "completed"} else 2
    except Exception as failure:
        # The real CLI boundary never emits a native provider/parser exception.
        # Owned codes are finite; uncontrolled exception text cannot become one.
        if isinstance(failure, (InfrastructureFailure, RESOURCE.ResourceFailure, RESOURCE.CONTROL.TaskFailure, RESOURCE.EVIDENCE.EvidenceFailure, ALIGN.AlignmentFailure, GATE.ContractFailure)):
            condition = failure.code
        else: condition = "infrastructure-boundary-not-confirmed"
        evidence = failure.evidence_reference if isinstance(failure, InfrastructureFailure) else None
        if isinstance(failure, InfrastructureFailure) and failure.provider_operation is not None:
            context = {**context, "provider_operation": "/".join(failure.provider_operation)}
        diagnostics = RESOURCE.EVIDENCE.failure_report(failure) if isinstance(failure, RESOURCE.EVIDENCE.EvidenceFailure) else {}
        print(json.dumps({"schema": "deploy/entity-smoke-infrastructure-report/v1", "target": RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "blocked", "condition": condition, "effect": provider.effect, "context": context,
                          **diagnostics, **({"evidence_reference": evidence} if evidence is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
