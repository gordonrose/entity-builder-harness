#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.infrastructure.implementation
#   version: 8
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Enforce source, custody, actual target alignment, normal realization gates and exact approved-plan binding before isolated infrastructure effects.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [aws-mutation, writes-files]
#   used_by:
#   - id: deploy.command.entity-smoke.infrastructure
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/orchestration/commands/script.sh
import argparse
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
from types import SimpleNamespace
import uuid
import yaml
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


ROOT = Path(__file__).resolve().parents[9]
DIRECTORY = Path(__file__).resolve().parents[2]
DEPLOY = module("entity_smoke_public_deployment", DIRECTORY / "controls-and-readiness/implementation/deployment-control.py")
RESOURCE = DEPLOY.RESOURCE
ALIGN = module("entity_smoke_public_alignment", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/script.py")
CLI = module("entity_smoke_public_cli", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cli.py")
GATE = module("entity_smoke_public_gate", ROOT / "scripts/04.deploy/operational-realization-gate/script.py")
CONTRACT = ROOT / ALIGN.TARGET / "20-scopes/entity-smoke/00-declaration/infrastructure-realization-contract.v2.yml"
GRAPH = module("entity_smoke_public_graph", DIRECTORY / "task-execution/implementation/task-graph.py")
TRANSITION = module("entity_smoke_source_transition", DIRECTORY / "recovery-and-replacement/source-transition/source-transition.py")
CONTROL_COMPLETION = module("entity_smoke_control_completion", DIRECTORY / "controls-and-readiness/implementation/control-completion.py")
SUCCESSION = module("entity_smoke_infrastructure_succession", ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py")
LOCAL_QUALIFICATION = module("entity_smoke_local_qualification", DIRECTORY / "bindings/local-qualification/entity-smoke-proof/binding.py")
READS = ALIGN.READS | {("cloudformation", operation) for operation in ("describe-change-set", "get-template", "list-stack-resources", "describe-stack-events", "validate-template")} | {
    ("iam", "get-role"), ("iam", "simulate-principal-policy"), ("ecs", "describe-services"), ("ecs", "describe-tasks"),
    ("ecs", "list-tasks"), ("logs", "get-log-events"),
    ("ecs", "describe-task-definition"), ("ecs", "list-services"), ("ec2", "describe-security-groups"),
    ("iam", "list-role-policies"), ("iam", "list-attached-role-policies"), ("iam", "get-role-policy"),
    ("rds", "describe-db-snapshots"), ("rds", "list-tags-for-resource"),
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
    """Single-submission mutations; narrowly bounded transport retries on reads.

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
        ALIGN.preparation_ready()
        global_services = {"iam": "iam.amazonaws.com", "route53": "route53.amazonaws.com", "budgets": "budgets.amazonaws.com"}
        hostname = global_services.get(service, ("api.ecr" if service == "ecr" else service) + "." + ALIGN.REGION + ".amazonaws.com")
        signing_region = "us-east-1" if service in global_services else ALIGN.REGION
        def failure(code):
            return InfrastructureFailure(code, provider_operation=(service, operation))
        arguments = ["aws", service, operation, *(["--profile", ALIGN.PROFILE] if ALIGN.PROFILE else []), "--region", signing_region,
                     "--endpoint-url", "https://" + hostname, "--output", "json", "--no-paginate", "--no-cli-pager",
                     "--cli-connect-timeout", "10", "--cli-read-timeout", "20", "--cli-input-json", json.dumps(parameters)]
        attempts = 3 if (service, operation) in READS else 1
        for attempt in range(attempts):
            try:
                return CLI.invoke_json(
                    arguments, cwd=ROOT, timeout=40, empty_body="whitespace", object_only=True,
                    environment={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "1", "AWS_EC2_METADATA_DISABLED": "true"},
                    timeout_endpoint="https://" + hostname,
                )
            except CLI.CliFailure as error:
                if (error.code == "aws-command-timeout" or error.transport_timeout) and attempt + 1 < attempts:
                    time.sleep(0.1 * (attempt + 1)); continue
                if error.phase == "process": raise failure("infrastructure-provider-observation-unavailable") from None
                if error.phase == "response": raise failure("infrastructure-provider-response-invalid") from None
                if error.code == "aws-resource-missing": raise RESOURCE.ResourceMissing() from None
                raise failure(error.code) from None
            except (OSError, subprocess.SubprocessError): raise failure("infrastructure-provider-observation-unavailable") from None
            except (ValueError, TypeError): raise failure("infrastructure-provider-response-invalid") from None


def operator_resources_allowed(provider, role, action, resources, *, context=None):
    """Confirm each exact resource; IAM batches return aggregate action rows."""
    if not isinstance(resources, list) or not resources or not all(isinstance(item, str) for item in resources) or len(set(resources)) != len(resources): return False
    for resource in resources:
        parameters = {"PolicySourceArn": role, "ActionNames": [action], "ResourceArns": [resource]}
        if context is not None: parameters["ContextEntries"] = context
        value = provider("iam", "simulate-principal-policy", **parameters)
        rows = value.get("EvaluationResults") if isinstance(value, dict) else None
        if not (isinstance(rows, list) and len(rows) == 1 and value.get("IsTruncated") is False
                and isinstance(rows[0], dict) and rows[0].get("EvalActionName") == action
                and rows[0].get("EvalDecision") == "allowed" and not rows[0].get("MissingContextValues")
                and rows[0].get("EvalResourceName") == resource): return False
    return True


def local_qualification(receipt):
    """Live routes consume package-bound local proof; they never run local tests."""
    try: LOCAL_QUALIFICATION.require_current(receipt)
    except LOCAL_QUALIFICATION.BindingFailure: raise InfrastructureFailure("infrastructure-local-qualification-not-confirmed") from None


def source_paths(revision=None):
    scope = DIRECTORY.relative_to(ROOT)
    if revision is None:
        candidates, flat = DIRECTORY.rglob("*"), False
    else:
        names = ALIGN.command(["git", "ls-tree", "-r", "--name-only", revision,
            str(scope) + "/"]).splitlines()
        candidates = (ROOT / name for name in names)
        # Old receipts used the original flat controller inventory. Resolve its
        # layout from that revision, never from today's relocated controller.
        flat = str(scope / "script.py") in names
    controller_files = [path for path in candidates
                        if path.suffix in {".py", ".sh"} and not path.name.endswith(("-test.py", "-test.sh"))
                        and not {"tests", "fixtures", "bindings", "__pycache__"}.intersection(path.relative_to(ROOT / scope).parts[:-1])
                        and (not flat or path.parent == ROOT / scope)]
    paths = sorted([*controller_files, CONTRACT, DEPLOY.SOURCE, Path(LOCAL_QUALIFICATION.__file__),
                    CONTRACT.parent / "acceptance-record-schema.yml", CONTRACT.parent / "acceptance-route-contract.yml",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/response.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/foundation-checks.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/cli.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/tasks.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/resource_reservation.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/snapshots.py",
                    ROOT / "scripts/04.deploy/shared/provider-adapters/aws/change_sets.py",
                    ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/script.py",
                    ROOT / "scripts/04.deploy/lifecycle/60-run/release-succession/proof-policy.py",
                    ROOT / "scripts/04.deploy/operational-realization-gate/script.py",
                    Path(ALIGN.__file__)])
    paths.extend([Path(ALIGN.INPUT_OWNER.__file__), Path(ALIGN.INPUT_OWNER.PATHS.__file__),
                  *(ROOT / reference for reference in ALIGN.INPUTS["references"])])
    return paths


def source_digest():
    ALIGN.preparation_ready()
    return DEPLOY.fingerprint({str(path.relative_to(ROOT)): digest_file(path) for path in source_paths()})


@lru_cache(maxsize=32)
def historical_source_digest(revision):
    """Only immutable Git objects are cached; never current source or AWS state."""
    require(isinstance(revision, str) and re.fullmatch(r"[a-f0-9]{40}", revision), "infrastructure-source-unavailable")
    names = sorted({str(path.relative_to(ROOT)) for path in source_paths(revision)})
    entries = ALIGN.command(["git", "ls-tree", "-z", revision, "--", *names]).split("\0")[:-1]
    require(len(entries) == len(names) and all(row.startswith(("100644 blob ", "100755 blob ")) for row in entries), "infrastructure-source-unavailable")
    values = {}
    for name in names:
        try: result = subprocess.run(["git", "show", revision + ":" + name], cwd=ROOT, capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError): raise InfrastructureFailure("infrastructure-source-unavailable") from None
        require(result.returncode == 0 and len(result.stdout) <= 4 * 1024 * 1024, "infrastructure-source-unavailable")
        values[name] = "sha256:" + hashlib.sha256(result.stdout).hexdigest()
    return DEPLOY.fingerprint(values)


def retained_controller(packet, current):
    """Bind historical task gates to a checked controller-only Git checkpoint."""
    controller = packet["plan"]["controller_sha256"]
    if controller == current: return controller
    source = packet["binding"]["source_revision"]
    # The same existing guard proves that no image/runtime/configuration inputs
    # changed. An arbitrary hash in a retained packet cannot authorize its reuse.
    identity = ALIGN.source_checkpoint({"source_revision": source})
    revisions = [source, *ALIGN.command(["git", "rev-list", "--ancestry-path", "--max-count=32",
        source + ".." + identity["controller_revision"]]).splitlines()]
    for revision in revisions:
        if historical_source_digest(revision) == controller:
            ALIGN.source_checkpoint({"source_revision": source}, controller_revision=revision)
            return controller
    raise InfrastructureFailure("task-step-completion-artifacts-mismatch")


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


def operator_preflight(provider, *, mutation=True):
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == ALIGN.ACCOUNT and isinstance(arn, str) and re.fullmatch(r"arn:aws:sts::" + ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn) is not None, "infrastructure-operator-identity-not-confirmed")
    name = arn.split("/")[1]
    role = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(role, dict) and role.get("RoleName") == name and isinstance(role.get("Arn"), str) and role["Arn"].startswith("arn:aws:iam::" + ALIGN.ACCOUNT + ":role/") and role["Arn"].endswith("/" + name), "infrastructure-operator-role-not-confirmed")
    identity = DEPLOY.fingerprint({"account": caller["Account"], "role": role["Arn"]})
    if not mutation: return identity
    actions = {"cloudformation:CreateChangeSet", "cloudformation:ExecuteChangeSet"}
    result = provider("iam", "simulate-principal-policy", PolicySourceArn=role["Arn"], ActionNames=sorted(actions), ResourceArns=["arn:aws:cloudformation:" + ALIGN.REGION + ":" + ALIGN.ACCOUNT + ":stack/" + DEPLOY.STACK + "/*"])
    evaluations = result.get("EvaluationResults") if isinstance(result, dict) else None
    require(isinstance(evaluations, list) and len(evaluations) == len(actions) and result.get("IsTruncated", False) is False and {item.get("EvalActionName") for item in evaluations if isinstance(item, dict)} == actions and all(isinstance(item, dict) and item.get("EvalDecision") == "allowed" and not item.get("MissingContextValues") for item in evaluations), "infrastructure-operator-policy-preflight-not-confirmed")
    # Policy simulation is a preflight, never a claim that execution succeeded.
    return identity


class GateBook:
    def __init__(self, artifact, cache, *, contract=None, artifact_bindings=None, delivery=None):
        self.contract = yaml.safe_load(CONTRACT.read_text()) if contract is None else contract
        if delivery is not None:
            RESOURCE.validate_delivery(delivery)
            require(contract is None, "infrastructure-delivery-graph-selection-invalid")
            self.contract["change_shape"].update(
                allowed_operation_classes=["update", "replace"], forbidden_operation_classes=["create", "delete", "broaden-permission"],
                immutable_definition_refresh={name: True for name in ("owned_task_definitions_only", "unchanged_permissions_and_storage",
                    "qualified_image_required", "original_preparation_retained", "accepted_predecessor_required", "compatible_rollback_required")})
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

    def validate(self, through, change_count=None, activate=False, *, operation_class=None, operation_counts=None):
        require(set(self.components) == set(self.known), "infrastructure-component-proof-incomplete")
        require(self.plan_digest is not None, "infrastructure-evidence-plan-missing")
        bindings = GATE.evidence_bindings(self.contract, self.facts)
        self.facts["component_evidence"] = [{"component_id": name, "component_kind": self.known[name], "check_id": self.component_check_id, "timestamp": self.components[name], "verdict": "passed", "input_sha256": bindings["components"][name]} for name in sorted(self.components)]
        GATE.validate_facts(self.facts, self.contract, self.identity, self.known, through)
        summary = None
        if change_count is not None:
            selected_operation = ("update" if activate else "create") if operation_class is None else operation_class
            require(selected_operation in {"create", "update", "delete"}, "infrastructure-change-operation-invalid")
            counts = {name: change_count if name == selected_operation else 0 for name in ("create", "update", "delete", "replace", "broaden-permission")}
            if operation_counts is not None:
                require(isinstance(operation_counts, dict) and set(operation_counts) == set(counts)
                        and all(type(value) is int and value >= 0 for value in operation_counts.values())
                        and sum(operation_counts.values()) == change_count, "infrastructure-change-counts-invalid")
                counts = operation_counts
            summary = {"schema": GATE.CHANGE_SCHEMA, "contract_id": self.identity, "check_id": self.contract["gates"][4]["evidence"][0], "timestamp": now(),
                       "input_sha256": bindings["gates"]["change-set"], "operation_counts": counts}
            GATE.validate_change_summary(summary, self.contract, self.identity, self.facts)
        path = self.cache / (through + "-" + uuid.uuid4().hex + ".json")
        require(RESOURCE.write_exclusive(path, {"plan_sha256": self.plan_digest, "facts": self.facts, "change_summary": summary}), "infrastructure-gate-evidence-retention-failed")
        return path


def binding_for(receipt, alignment):
    return {"source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"],
            "configuration_contract_sha256": digest_file(ROOT / ALIGN.SCOPE), "permission_contract_sha256": digest_file(DEPLOY.SOURCE),
            "dependency_incarnation_sha256": alignment["dependency_incarnation_sha256"]}


def delivery_context(args, receipt, binding):
    expected = getattr(args, "expected_predecessor", None)
    if expected is None: return None
    require(isinstance(expected, str) and re.fullmatch(r"release-[a-f0-9]{24}", expected) is not None, "infrastructure-predecessor-invalid")
    root = CONTRACT.parent.parent / "30-release-evidence"
    try:
        current = SUCCESSION.current(root)
        require(current is not None and current["target"] == RESOURCE.CLUSTER and current["scope"] == "entity-smoke"
                and current["release_id"] == expected, "infrastructure-predecessor-mismatch")
        history, _ = SUCCESSION.history_record_for_id(root, expected)
    except SUCCESSION.SuccessionFailure as failure:
        code = str(failure)
        raise InfrastructureFailure(code if re.fullmatch(r"release-succession-[a-z0-9-]{1,100}", code) else "infrastructure-predecessor-unavailable") from None
    release = history["release"]
    identity = {"expected_predecessor": expected,
                "predecessor": {"release_id": expected, **{key: release[key] for key in ("source_revision", "image_digest", "proof_set_sha256")}},
                "candidate": {key: receipt[key] for key in ("source_revision", "image_digest", "receipt_reference")},
                "contracts": {key: binding[key] for key in ("configuration_contract_sha256", "permission_contract_sha256")},
                "dependency_incarnation_sha256": binding["dependency_incarnation_sha256"], "proof_label": binding["proof_label"]}
    digest = hashlib.sha256(RESOURCE.CONTROL.canonical(identity)).hexdigest()
    return RESOURCE.validate_delivery({"schema": "deploy/entity-smoke-delivery-context/v1", **identity,
                                      "delivery_id": digest, "smoke_label": "entity-smoke-" + digest[:24]})


def delivery_cache(proof_label, delivery=None):
    require(isinstance(proof_label, str) and re.fullmatch(RESOURCE.PATTERNS["proof_label"], proof_label) is not None, "infrastructure-proof-label-invalid")
    path = ROOT / ".cache/entity-smoke-live" / proof_label
    if delivery is not None:
        RESOURCE.validate_delivery(delivery)
        require(delivery["proof_label"] == proof_label, "infrastructure-delivery-label-mismatch")
        path = path / "releases" / delivery["delivery_id"]
    return path


def delivery_preflight_label(delivery, stage, workload, operation):
    RESOURCE.validate_delivery(delivery)
    require(all(isinstance(item, str) and re.fullmatch(r"[a-z][a-z-]*", item) is not None for item in (stage, workload, operation)), "infrastructure-delivery-task-selection-invalid")
    return "entity-smoke-" + hashlib.sha256(RESOURCE.CONTROL.canonical({"delivery_id": delivery["delivery_id"], "stage": stage,
                                                                   "workload": workload, "operation": operation})).hexdigest()[:24]


def delivery_operation_label(delivery, workload, operation):
    RESOURCE.validate_delivery(delivery)
    return delivery["smoke_label"] if (workload, operation) == ("verifier", "lifecycle") else delivery["proof_label"]


def previous_delivery_parameters(parameters, delivery, *, rollback=False):
    RESOURCE.validate_delivery(delivery)
    selected = delivery["candidate"] if rollback else delivery["predecessor"]
    return {**parameters, "ImageDigest": selected["image_digest"], "SourceRevision": selected["source_revision"], "ServerDesiredCount": "1"}


def validate_deployment_receipt(packet, binding, delivery, *, rollback=False):
    """Validate captured custody only; no current source, files or provider reads."""
    RESOURCE.validate_delivery(delivery)
    RESOURCE.validate_binding(binding, record_required=False)
    phase = "rollback" if rollback else "update"
    require(isinstance(packet, dict) and set(packet) == {"schema", "binding", "delivery", "plan_sha256", "plan", "result"}
            and packet["schema"] == "deploy/entity-smoke-infrastructure-receipt/v2" and packet["binding"] == binding and packet["delivery"] == delivery
            and isinstance(packet["plan_sha256"], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", packet["plan_sha256"]) is not None
            and isinstance(packet["result"], dict) and packet["result"].get("status") == "completed", "infrastructure-delivery-receipt-invalid")
    result = packet["result"]
    reservation = result.get("reservation")
    require(isinstance(reservation, dict) and isinstance(reservation.get("request"), dict), "infrastructure-delivery-reservation-invalid")
    request = reservation["request"]
    RESOURCE.validate_request("deploy-execute-" + phase, request)
    RESOURCE.ResourceStore.validate_record("deploy-execute-" + phase, request, reservation, validate_time=RESOURCE.timestamp)
    plan = packet["plan"]
    fields = {"schema", "target", "scope", "account", "region", "phase", "binding", "operator_sha256", "controller_sha256", "graph_sha256",
              "parameters_sha256", "template_sha256", "package_custody_reference", "resource_additions", "resource_modifications", "resource_replacements", "server_desired_count",
              "database_data_or_schema_changes", "source_database_replacement", "baseline_database_ingress_additions", "baseline_endpoint_ingress_additions",
              "automatic_rollback", "delivery", "previous_parameters_sha256", "rollback_compatibility"}
    require(isinstance(plan, dict) and set(plan) == fields and plan["schema"] in {"deploy/entity-smoke-infrastructure-plan/v2", "deploy/entity-smoke-infrastructure-plan/v3"}
            and DEPLOY.fingerprint(plan) == packet["plan_sha256"] and plan["delivery"] == request["delivery"] == delivery
            and plan["phase"] == phase and plan["binding"] == request["binding"] == binding
            and plan["target"] == RESOURCE.CLUSTER and plan["scope"] == "entity-smoke" and plan["account"] == ALIGN.ACCOUNT and plan["region"] == ALIGN.REGION
            and plan["package_custody_reference"] == delivery["candidate"]["receipt_reference"]
            and all(plan[key] == request[key] for key in ("parameters_sha256", "previous_parameters_sha256", "template_sha256")), "infrastructure-delivery-plan-mismatch")
    for key in ("operator_sha256", "controller_sha256", "graph_sha256"):
        require(isinstance(plan[key], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", plan[key]) is not None, "infrastructure-delivery-plan-mismatch")
    require(all(type(plan[key]) is int and plan[key] == expected for key, expected in {"resource_additions": 0, "resource_modifications": 1, "resource_replacements": 5, "server_desired_count": 1,
            "baseline_database_ingress_additions": 0, "baseline_endpoint_ingress_additions": 0}.items())
            and all(plan[key] is False for key in ("database_data_or_schema_changes", "source_database_replacement"))
            and plan["automatic_rollback"] is (plan["schema"] == "deploy/entity-smoke-infrastructure-plan/v3"), "infrastructure-delivery-plan-mismatch")
    compatibility = plan["rollback_compatibility"]
    require(isinstance(compatibility, dict) and set(compatibility) == {"compatibility_id", "compatibility_sha256", "receipt_reference"}
                and isinstance(compatibility["compatibility_id"], str) and re.fullmatch(r"(?:rollback-compatibility|accepted-proof)-[a-f0-9]{24}", compatibility["compatibility_id"]) is not None
                and isinstance(compatibility["compatibility_sha256"], str) and re.fullmatch(r"sha256:[a-f0-9]{64}", compatibility["compatibility_sha256"]) is not None
                and isinstance(compatibility["receipt_reference"], str) and re.fullmatch(r"github-actions-run:[0-9]+", compatibility["receipt_reference"]) is not None, "infrastructure-delivery-compatibility-invalid")
    require(not compatibility["compatibility_id"].startswith("accepted-proof-")
        or compatibility["compatibility_id"] == "accepted-proof-" + delivery["predecessor"]["release_id"].removeprefix("release-"),
        "infrastructure-delivery-compatibility-invalid")
    facts = result.get("facts")
    require(set(result) == {"status", "reservation", "facts"} and isinstance(facts, dict)
            and set(facts) == {"stack_arn", "desired_count", "resources", "resources_sha256", "completed_at"}
            and facts["stack_arn"] == request["stack_arn"] and type(facts["desired_count"]) is int and facts["desired_count"] == 1
            and isinstance(facts["resources"], dict) and set(facts["resources"]) == set(DEPLOY.RESOURCE_TYPES)
            and all(isinstance(row, dict) and set(row) == {"type", "physical_id"} and row["type"] == DEPLOY.RESOURCE_TYPES[key]
                    and isinstance(row["physical_id"], str) and row["physical_id"] for key, row in facts["resources"].items())
            and facts["resources_sha256"] == DEPLOY.fingerprint(facts["resources"]), "infrastructure-delivery-facts-invalid")
    require(RESOURCE.timestamp(facts["completed_at"]) >= RESOURCE.timestamp(reservation["reserved_at"]), "infrastructure-delivery-completion-invalid")
    return packet


def completed_deployment(provider, binding, parameters, delivery, *, rollback=False):
    """Reobserve an immutable delivery; never treat receipt presence as success."""
    cache = delivery_cache(binding["proof_label"], delivery)
    phase = "rollback" if rollback else "update"
    packet = validate_deployment_receipt(read_json(cache / "receipts" / (phase + ".json")), binding, delivery, rollback=rollback)
    result, plan = packet["result"], packet["plan"]
    reservation, request = result["reservation"], result["reservation"]["request"]
    previous = previous_delivery_parameters(parameters, delivery, rollback=rollback)
    require(read_json(cache / "plans" / (phase + ".json")) == plan
            and plan.get("parameters_sha256") == DEPLOY.fingerprint(parameters)
            and plan.get("previous_parameters_sha256") == DEPLOY.fingerprint(previous)
            and plan.get("template_sha256") == digest_file(DEPLOY.SOURCE), "infrastructure-delivery-plan-mismatch")
    store = RESOURCE.ResourceStore(cache / "attempts")
    require(store.read("deploy-execute-" + phase, request) == reservation
            and all(request.get(key) == value for key, value in DEPLOY.request(binding, parameters, True, delivery=delivery, previous_parameters=previous, rollback=rollback).items()), "infrastructure-delivery-reservation-mismatch")
    observed = DEPLOY.observe(provider, store, binding, parameters, request["change_set_arn"], request["stack_arn"], activate=True,
                              delivery=delivery, previous_parameters=previous, rollback=rollback)
    require(observed == result, "infrastructure-delivery-observation-mismatch")
    return {"receipt": packet, "required_after": result["facts"]["completed_at"], "resources": result["facts"]["resources"], "cache": cache}


def rollback_selection(args, delivery, binding):
    """Select exactly the accepted predecessor without replacing controller custody."""
    path, identifier = getattr(args, "rollback_receipt", None), getattr(args, "rollback_compatibility_id", None)
    require(delivery is not None and path is not None and isinstance(identifier, str), "infrastructure-rollback-compatibility-required")
    receipt = ALIGN.read_receipt(path.absolute())
    if identifier.startswith("accepted-proof-"):
        return accepted_rollback_selection(identifier, receipt, delivery, binding)
    root = CONTRACT.parent.parent / "30-release-evidence"
    try: record, checked = SUCCESSION.compatibility_record(root, identifier)
    except SUCCESSION.SuccessionFailure as failure:
        code = str(failure)
        raise InfrastructureFailure(code if re.fullmatch(r"release-succession-[a-z0-9-]{1,100}", code) else "infrastructure-rollback-compatibility-unavailable") from None
    identity, predecessor = checked["identity"], delivery["predecessor"]
    require(checked["target"] == RESOURCE.CLUSTER and checked["scope"] == "entity-smoke"
            and identity.get("historical_release_id") == predecessor["release_id"]
            and all(receipt[key] == predecessor[key] == identity[key] for key in ("source_revision", "image_digest")), "infrastructure-rollback-predecessor-mismatch")
    require(set(identity["workloads"]) == {"server", "migration", "administration", "verifier", "database-proof"}, "infrastructure-rollback-workloads-incomplete")
    for name, path, field in (("configuration_contract", ROOT / ALIGN.SCOPE, "configuration_contract_sha256"),
                              ("permission_contract", DEPLOY.SOURCE, "permission_contract_sha256")):
        require(identity[name] == {"path": str(path.relative_to(ROOT)), "sha256": binding[field]}, "infrastructure-rollback-contract-mismatch")
    return {**binding, **{key: predecessor[key] for key in ("source_revision", "image_digest")}}, {
        "compatibility_id": identifier, "compatibility_sha256": checked["sha256"], "receipt_reference": receipt["receipt_reference"]}


def accepted_rollback_selection(identifier, receipt, delivery, binding):
    """Reuse validated accepted proof, not a manufactured compatibility record."""
    owner = module("entity_smoke_rollback_state", DIRECTORY / "acceptance-evaluation/implementation/acceptance-state.py")
    try:
        accepted = owner.State().current()
        predecessor = delivery["predecessor"]
        require(accepted["reference"]["release_id"] == predecessor["release_id"]
            and identifier == "accepted-proof-" + predecessor["release_id"].removeprefix("release-")
            and all(accepted["identity"][key] == predecessor[key] for key in ("source_revision", "image_digest", "proof_set_sha256"))
            and all(receipt[key] == accepted["packet"]["package"][key]
                    for key in ("source_revision", "image_digest", "receipt_reference", "program_id", "package_contract_id")),
            "infrastructure-rollback-predecessor-mismatch")
        schema = yaml.safe_load((CONTRACT.parent / "acceptance-record-schema.yml").read_text())
        policy = schema.get("accepted_rollback_reuse")
        require(isinstance(policy, dict) and set(policy) == {"selection", "configuration_exclusion", "execution", "schema_input_paths"}
            and policy["selection"] == "exact-accepted-proof"
            and policy["configuration_exclusion"] == "top-level-change_impact-only"
            and policy["execution"] == "image-only-no-schema-or-permission-model-change", "infrastructure-rollback-reuse-policy-invalid")
        applicability = owner.A.POLICY.rollback_applicability(accepted["packet"]["binding"], binding,
            ALIGN.SCOPE, str(DEPLOY.SOURCE.relative_to(ROOT)), policy["schema_input_paths"], root=ROOT)
        evidence = {"accepted_candidate_sha256": accepted["sha256"],
            "accepted_proof_set_sha256": predecessor["proof_set_sha256"], "applicability": applicability}
    except Exception as failure:
        details = owner.K.failure_details(failure)
        if isinstance(failure, InfrastructureFailure): raise
        raise InfrastructureFailure(details["condition"]) from None
    return {**binding, **{key: predecessor[key] for key in ("source_revision", "image_digest")}}, {
        "compatibility_id": identifier, "compatibility_sha256": DEPLOY.fingerprint(evidence), "receipt_reference": receipt["receipt_reference"]}


def successor_admission(delivery, binding):
    owner = module("entity_smoke_update_applicability", DIRECTORY / "acceptance-evaluation/implementation/acceptance-route.py")
    try: return owner.successor_admission(delivery, binding)
    except Exception as failure:
        details = owner.failure_details(failure)
        raise InfrastructureFailure(details["condition"]) from None


def activation_prerequisites(provider, path, binding, parameters, cache, store, *, resuming=False, admitted_at=None):
    require(path is not None, "infrastructure-activation-proof-required")
    previous = read_json(cache / "receipts/create.json")
    transition = TRANSITION.read(SimpleNamespace(**globals()), cache, binding)
    creation_binding = transition["plan"]["previous_binding"] if transition else binding
    require(isinstance(previous, dict) and set(previous) == {"schema", "binding", "result"} and previous["schema"] == "deploy/entity-smoke-infrastructure-receipt/v1" and previous["binding"] == creation_binding
            and isinstance(previous["result"], dict) and previous["result"].get("status") == "completed" and isinstance(previous["result"].get("reservation"), dict)
            and isinstance(previous["result"]["reservation"].get("request"), dict) and isinstance(previous["result"].get("facts"), dict)
            and isinstance(previous["result"]["facts"].get("resources"), dict), "infrastructure-create-receipt-invalid")
    execution = previous["result"]["reservation"]["request"]
    require(all(execution.get(key) == value for key, value in DEPLOY.request(creation_binding, {**parameters, "ServerDesiredCount": "0", "SourceRevision": creation_binding["source_revision"], "ImageDigest": creation_binding["image_digest"]}, False).items()), "infrastructure-create-receipt-binding-mismatch")
    if transition:
        require(store.read("deploy-execute-create", execution) == previous["result"]["reservation"], "infrastructure-create-reservation-not-confirmed")
        created = previous["result"]
        current = DEPLOY.deployed_stack(provider, binding, {**parameters, "ServerDesiredCount": "1" if resuming else "0"})
        require(current["StackId"] == created["facts"]["stack_arn"] and current.get("StackStatus") in {"UPDATE_COMPLETE", "UPDATE_IN_PROGRESS"}, "infrastructure-transition-state-not-confirmed")
        response = provider("cloudformation", "list-stack-resources", StackName=current["StackId"])
        rows = response.get("StackResourceSummaries")
        require(isinstance(rows, list) and len(rows) == len(DEPLOY.RESOURCE_TYPES) and not response.get("NextToken")
                and {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows} == transition["resources"], "infrastructure-transition-resources-changed")
    elif resuming:
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
        original = False
        selected_binding = binding
        if name in {"bootstrap", "migration", "grant-runtime"}:
            step = cache / "task-steps" / (workload + "-" + operation + "-operation.json")
            completion_path = step.with_name(step.stem + ".completion.json")
            if step.is_file() and completion_path.is_file():
                packet, completion = read_json(step), read_json(completion_path)
                original = TRANSITION.historical(packet, completion)
                if original:
                    selected_binding = creation_binding if name in {"bootstrap", "migration"} else binding
                    require(packet["reservation"] == reservation and packet["receipt"] == receipt and packet["binding"] == selected_binding
                            and digest_file(ROOT / completion["realization_evidence"]) == completion["realization_evidence_sha256"], "infrastructure-original-preparation-changed")
        resources = transition["resources"] if transition and selected_binding == binding else created["facts"]["resources"]
        require(retained["workload"] == workload and retained["operation"] == operation and all(reservation["request"].get(key) == value for key, value in selected_binding.items())
                and retained["task"]["definition"] == resources[logical]["physical_id"], "infrastructure-activation-proof-binding-mismatch")
        completion = workloads["entity-smoke-" + workload]["completion"]
        require(retained["task"]["completion_duration_seconds"] <= completion["deadline_seconds"] and reservation["request"]["deadline_seconds"] <= completion["deadline_seconds"]
                and retained["result"]["code"] == completion["success"]["result_code"], "infrastructure-activation-completion-contract-mismatch")
        require(previous_stop is None or RESOURCE.timestamp(retained["task"]["created_at"]) >= previous_stop, "infrastructure-activation-proof-order-invalid")
        if not original:
            task = RESOURCE.only(provider("ecs", "describe-tasks", cluster=RESOURCE.CLUSTER, tasks=[retained["task"]["arn"]]), "tasks")
            logs = RESOURCE.EVIDENCE.read_logs(provider, reservation["request"], retained["task"]["arn"])
            current = RESOURCE.EVIDENCE.collect(task, reservation, logs, retained["collected_at"])
            require(current == retained, "infrastructure-activation-proof-not-confirmed")
        previous_stop = RESOURCE.timestamp(retained["task"]["stopped_at"])
    # Reconciliation observes an existing submission, not a new admission. Its
    # immutable reservation supplies the original freshness boundary; never
    # restamp a proof or require another activation merely because reads failed.
    reference = RESOURCE.timestamp(admitted_at) if resuming else datetime.now(timezone.utc)
    require(reference is not None and -60 <= (reference - previous_stop).total_seconds() <= GATE.CURRENT_EVIDENCE_MAX_AGE_SECONDS, "infrastructure-activation-proof-not-fresh")


def read_execution_reservation(store, binding, parameters, activate, *, delivery=None, previous_parameters=None, rollback=False):
    """Read the original durable identity without relying on an ephemeral API object."""
    phase = "deploy-execute-" + DEPLOY.selection(activate, delivery, rollback)
    path = store.root / (binding["proof_label"] + "-" + phase + ".json")
    RESOURCE.CONTROL.no_symlinks(path)
    if not path.exists(): return None
    value = read_json(path)
    require(isinstance(value, dict) and isinstance(value.get("request"), dict), "infrastructure-execution-reservation-invalid")
    intent = DEPLOY.request(binding, parameters, activate, delivery=delivery, previous_parameters=previous_parameters, rollback=rollback)
    original = DEPLOY.CHANGE_SETS.retained_execution(store,
        preparation_phase="deploy-" + DEPLOY.selection(activate, delivery, rollback) + "-change-set", preparation_request=intent,
        execution_phase=phase, execution_request=value["request"],
        missing_preparation=lambda: InfrastructureFailure("infrastructure-reviewed-attempt-required"))
    require(original is not None and all(original["request"].get(key) == item for key, item in intent.items()), "infrastructure-execution-reservation-mismatch")
    return original


def infrastructure_plan(args, receipt, binding, parameters, operator, artifact, book, *, delivery=None, previous_parameters=None, compatibility=None):
    activate = args.phase != "create"
    plan = {"schema": "deploy/entity-smoke-infrastructure-plan/v1", "target": RESOURCE.CLUSTER, "scope": "entity-smoke", "account": ALIGN.ACCOUNT, "region": ALIGN.REGION,
            "phase": args.phase, "binding": binding, "operator_sha256": operator, "controller_sha256": artifact, "graph_sha256": DEPLOY.fingerprint(book.contract) if delivery else digest_file(CONTRACT),
            "parameters_sha256": DEPLOY.fingerprint(parameters), "template_sha256": digest_file(DEPLOY.SOURCE),
            "package_custody_reference": receipt["receipt_reference"], "resource_additions": 0 if activate else 30, "resource_modifications": 1 if activate else 0,
            "server_desired_count": 1 if activate else 0, "database_data_or_schema_changes": False, "source_database_replacement": False,
            "baseline_database_ingress_additions": 0 if activate else 4, "baseline_endpoint_ingress_additions": 0 if activate else 5, "automatic_rollback": False}
    if delivery:
        plan.update(schema="deploy/entity-smoke-infrastructure-plan/v3", automatic_rollback=True, delivery=delivery, previous_parameters_sha256=DEPLOY.fingerprint(previous_parameters),
                    resource_modifications=1, resource_replacements=5, rollback_compatibility=compatibility)
    return plan


def retain_deployment(args, cache, binding, result, plan_digest, plan=None):
    path = cache / "receipts" / (args.phase + ".json")
    retained = {"schema": "deploy/entity-smoke-infrastructure-receipt/v1", "binding": binding, "result": result}
    if plan is not None:
        retained.update(schema="deploy/entity-smoke-infrastructure-receipt/v2", delivery=plan["delivery"], plan_sha256=plan_digest, plan=plan)
        validate_deployment_receipt(retained, binding, plan["delivery"], rollback=args.phase == "rollback")
    if not RESOURCE.write_exclusive(path, retained): require(read_json(path) == retained, "infrastructure-receipt-conflict")
    return {"verdict": "completed", "phase": args.phase, "plan_sha256": plan_digest, "receipt": str(path.relative_to(ROOT)), "effect": "owned-infrastructure-observed"}


def resume_execution(args, provider, receipt):
    """Observe admitted intent before new-submission checks; never enable writes."""
    if args.mode != "execute": return None
    base = delivery_cache(args.proof_label)
    phase = "deploy-execute-" + args.phase
    name = args.proof_label + "-" + phase + ".json"
    successor = args.phase in {"update", "rollback"}
    paths = sorted(base.glob("releases/*/attempts/" + name)) if successor else [base / "attempts" / name]
    matches = []
    for path in paths:
        RESOURCE.CONTROL.no_symlinks(path)
        if not path.exists(): continue
        value = read_json(path)
        require(isinstance(value, dict) and isinstance(value.get("request"), dict), "infrastructure-execution-reservation-invalid")
        store = RESOURCE.ResourceStore(path.parent)
        original = store.read(phase, value["request"])
        require(original is not None and store.path_for(phase, original["request"]) == path, "infrastructure-execution-reservation-mismatch")
        request = original["request"]
        delivery = request.get("delivery")
        if successor and (delivery["expected_predecessor"] != getattr(args, "expected_predecessor", None)
                          or delivery["candidate"] != {key: receipt[key] for key in ("source_revision", "image_digest", "receipt_reference")}):
            continue
        binding = request["binding"]
        expected = binding_for(receipt, binding)
        if args.phase == "rollback":
            expected.update({key: delivery["predecessor"][key] for key in ("source_revision", "image_digest")})
        require(binding == {**expected, "proof_label": args.proof_label}
                and path.parent.parent == delivery_cache(args.proof_label, delivery), "infrastructure-execution-reservation-mismatch")
        matches.append((store, original))
    require(len(matches) <= 1, "infrastructure-execution-reservation-mismatch")
    if not matches: return None
    store, original = matches[0]
    provider.effect = "original-operation-reconcile-only"
    request, cache = original["request"], store.root.parent
    binding, delivery = request["binding"], request.get("delivery")
    artifact = source_digest()
    book = GateBook(artifact, cache / "realization", delivery=delivery)
    # Reuse the original admission, not a new timestamp or a claim that current
    # source checks ran. A reviewed controller repair still takes the checked
    # admission path below when its source/approved plan differs.
    admissions, repair = [], False
    paths = sorted(book.cache.glob("execution-preflight-*.json"))
    require(paths, "infrastructure-original-admission-required")
    for path in paths:
        value = read_json(path)
        require(isinstance(value, dict) and isinstance(value.get("facts"), dict), "infrastructure-execution-reservation-invalid")
        artifacts = value["facts"].get("artifact_bindings")
        require(isinstance(artifacts, list) and len(artifacts) == 1 and isinstance(artifacts[0], dict), "infrastructure-execution-reservation-invalid")
        gates = value["facts"].get("gate_evidence")
        require(isinstance(gates, list) and len(gates) == 6 and isinstance(gates[-1], dict), "infrastructure-execution-reservation-invalid")
        admitted = RESOURCE.timestamp(gates[-1].get("timestamp"))
        if admitted > RESOURCE.timestamp(original["reserved_at"]): continue
        repair = repair or artifacts[0].get("immutable_reference") != artifact
        if value.get("plan_sha256") == args.approved_plan and artifacts[0].get("immutable_reference") == artifact:
            admissions.append(value)
    if not admissions:
        # Only a changed controller may seek fresh repair admission. Missing
        # original evidence or a wrong approved plan is not a new submission.
        require(repair, "infrastructure-approved-plan-mismatch")
        return None
    completion = module("entity_smoke_infrastructure_gate_custody", DIRECTORY / "task-execution/implementation/task-completion.py")
    reader = SimpleNamespace(C=SimpleNamespace(GATE=GATE), STEPS=SimpleNamespace(require=require))
    evidence = completion.validate_gate(reader, book.contract, admissions[-1], args.approved_plan,
                                        {"infrastructure-controller-source": artifact}, through="execution-preflight")
    require(RESOURCE.timestamp(evidence["facts"]["gate_evidence"][-1]["timestamp"]) <= RESOURCE.timestamp(original["reserved_at"]), "infrastructure-execution-reservation-mismatch")
    operator = operator_preflight(provider, mutation=False)
    state = RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=request["stack_arn"]), "Stacks")
    if state.get("StackStatus") == "REVIEW_IN_PROGRESS":
        state = provider("cloudformation", "describe-change-set", StackName=request["stack_arn"], ChangeSetName=request["change_set_arn"])
    parameters = DEPLOY.CHANGE_SETS.parameter_values(state.get("Parameters"))
    require(parameters is not None, "infrastructure-execution-reservation-mismatch")
    activate, rollback = args.phase != "create", args.phase == "rollback"
    parameters.update(ImageDigest=binding["image_digest"], SourceRevision=binding["source_revision"], ServerDesiredCount="1" if activate else "0")
    options = {"delivery": delivery, "previous_parameters": previous_delivery_parameters(parameters, delivery, rollback=rollback), "rollback": rollback} if delivery else {}
    require(read_execution_reservation(store, binding, parameters, activate, **options) == original, "infrastructure-execution-reservation-mismatch")
    plan = read_json(cache / "plans" / (args.phase + ".json")) if successor else None
    require(not successor or isinstance(plan, dict), "infrastructure-delivery-plan-mismatch")
    expected_plan = infrastructure_plan(args, receipt, binding, parameters, operator, artifact, book, delivery=delivery,
                                        previous_parameters=options.get("previous_parameters"), compatibility=plan.get("rollback_compatibility") if plan else None)
    require(DEPLOY.fingerprint(expected_plan) == args.approved_plan and (not successor or plan == expected_plan), "infrastructure-approved-plan-mismatch")
    summary = evidence["change_summary"]
    require(isinstance(summary, dict) and summary == {
        "schema": GATE.CHANGE_SCHEMA, "contract_id": book.identity, "check_id": book.contract["gates"][4]["evidence"][0],
        "timestamp": summary.get("timestamp"), "input_sha256": GATE.evidence_bindings(book.contract, evidence["facts"])["gates"]["change-set"],
        "operation_counts": {"create": expected_plan["resource_additions"], "update": expected_plan["resource_modifications"],
                             "replace": expected_plan.get("resource_replacements", 0), "delete": 0, "broaden-permission": 0}},
        "infrastructure-original-admission-required")
    require(RESOURCE.timestamp(summary["timestamp"]) <= RESOURCE.timestamp(original["reserved_at"]), "infrastructure-original-admission-required")
    deadline = time.monotonic() + args.wait_seconds
    while True:
        result = DEPLOY.observe(provider, store, binding, parameters, request["change_set_arn"], request["stack_arn"], activate=activate, **options)
        if result["status"] == "completed": break
        if time.monotonic() >= deadline:
            return {"verdict": "pending", "phase": args.phase, "plan_sha256": args.approved_plan, "effect": "original-operation-not-terminal"}
        time.sleep(2)
    book.facts, book.gates = evidence["facts"], list(GATE.GATE_ORDER[:6])
    book.gate("controlled-execution")
    completed = {**evidence, "facts": book.facts}
    completion.validate_gate(reader, book.contract, completed, args.approved_plan, {"infrastructure-controller-source": artifact})
    require(RESOURCE.write_exclusive(book.cache / ("controlled-execution-" + uuid.uuid4().hex + ".json"), completed), "infrastructure-gate-evidence-retention-failed")
    return retain_deployment(args, cache, binding, result, args.approved_plan, plan)


def run(args, provider):
    if args.mode == "apply":
        # Preserve the existing owner paths and original admission on resume.
        # A newly reviewed change is never inferred from execute-only failure.
        execution = argparse.Namespace(**{**vars(args), "mode": "execute"})
        resumed = resume_execution(execution, provider, ALIGN.read_receipt(args.receipt.absolute()))
        if resumed is not None: return resumed
        reviewed = run(argparse.Namespace(**{**vars(args), "mode": "review"}), provider)
        if reviewed["verdict"] != "reviewed": return reviewed
        return run(execution, provider)
    receipt = ALIGN.read_receipt(args.receipt.absolute())
    resumed = resume_execution(args, provider, receipt)
    if resumed is not None: return resumed
    ALIGN.source_preflight(receipt)
    local_qualification(receipt)
    artifact = source_digest()
    alignment, parameters, _ = ALIGN.inspect(provider, receipt, now())
    activate = args.phase != "create"
    parameters["ServerDesiredCount"] = "1" if activate else "0"
    binding = {**binding_for(receipt, alignment), "proof_label": args.proof_label}
    delivery = delivery_context(args, receipt, binding)
    successor = args.phase in {"update", "rollback"}
    require(successor == (delivery is not None), "infrastructure-delivery-selection-invalid")
    rollback = args.phase == "rollback"
    compatibility = None
    if rollback:
        binding, compatibility = rollback_selection(args, delivery, binding)
        parameters.update(ImageDigest=binding["image_digest"], SourceRevision=binding["source_revision"])
    elif successor:
        successor_admission(delivery, binding)
        _, compatibility = rollback_selection(args, delivery, binding)
    previous_parameters = previous_delivery_parameters(parameters, delivery, rollback=rollback) if delivery else None
    options = {"delivery": delivery, "previous_parameters": previous_parameters, "rollback": rollback} if delivery else {}
    cache = delivery_cache(args.proof_label, delivery)
    filesystem_preflight(cache)
    store = RESOURCE.ResourceStore(cache / "attempts")
    book = GateBook(artifact, cache / "realization", delivery=delivery)
    for name in ("infrastructure-controller-source", "attempt-store", "infrastructure-safe-reports", "infrastructure-reconciliation", "infrastructure-controller"):
        book.component(name)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration")
    DEPLOY.parameters_for(binding, parameters, activate)
    operator = operator_preflight(provider)
    existing_execution = None
    if args.mode == "execute" or activate:
        existing_execution = read_execution_reservation(store, binding, parameters, activate, **options)
        if existing_execution is not None: provider.effect = "original-operation-reconcile-only"
    book.component("infrastructure-operator"); book.component("control-state-connection"); book.component("intent-connection")
    if successor:
        # Admission proves the accepted image is still deployed. Reconciliation
        # instead observes the exact already-reserved candidate operation.
        if existing_execution is None:
            before_binding = {**binding, "source_revision": previous_parameters["SourceRevision"], "image_digest": previous_parameters["ImageDigest"]}
            state = DEPLOY.deployed_stack(provider, before_binding, previous_parameters)
            require(state.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"}, "infrastructure-successor-precondition-not-confirmed")
        DEPLOY.request(binding, parameters, activate, **options)
    elif activate:
        activation_prerequisites(provider, args.prerequisites.absolute() if args.prerequisites else None, binding, parameters, cache, store,
                                 resuming=existing_execution is not None, admitted_at=None if existing_execution is None else existing_execution["reserved_at"])
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
    plan = infrastructure_plan(args, receipt, binding, parameters, operator, artifact, book,
                               delivery=delivery, previous_parameters=previous_parameters, compatibility=compatibility)
    plan_digest = DEPLOY.fingerprint(plan)
    book.bind_plan(plan_digest); book.component("infrastructure-inputs")
    book.gate("live-read"); book.validate("live-read")
    if args.mode == "plan": return {"verdict": "planned", "plan": plan, "plan_sha256": plan_digest, "effect": "not-started"}
    require(args.approved_plan == plan_digest, "infrastructure-approved-plan-mismatch")
    if successor:
        plan_path = cache / "plans" / (args.phase + ".json")
        if not RESOURCE.write_exclusive(plan_path, plan): require(read_json(plan_path) == plan, "infrastructure-delivery-plan-conflict")
    intent = DEPLOY.request(binding, parameters, activate, **options)
    phase = "deploy-" + args.phase + "-change-set"
    if args.mode == "execute": require(store.read(phase, intent) is not None, "infrastructure-reviewed-attempt-required")
    def prewrite(operation, supplied):
        require(source_digest() == artifact and digest_file(ROOT / ALIGN.SCOPE) == binding["configuration_contract_sha256"], "infrastructure-source-changed-before-submission")
        if delivery is not None:
            require(delivery_context(args, receipt, {**binding, "source_revision": receipt["source_revision"], "image_digest": receipt["image_digest"]}) == delivery, "infrastructure-predecessor-changed-before-submission")
            require(rollback_selection(args, delivery, binding)[1] == compatibility, "infrastructure-rollback-compatibility-changed")
            if not rollback: successor_admission(delivery, binding)
        if operation == "create-change-set":
            reserved = store.read(phase, intent)
            require(reserved is not None and supplied == {**DEPLOY.change_arguments(binding, parameters, activate, **options),
                    "ClientToken": reserved["operation_id"], "Description": reserved["operation_id"]}, "infrastructure-submission-does-not-match-plan")
        else:
            require(set(supplied) == {"StackName", "ChangeSetName", "ClientRequestToken"} | ({"DisableRollback"} if activate else set())
                    and supplied["StackName"] == reviewed["facts"]["stack_arn"] and supplied["ChangeSetName"] == reviewed["facts"]["change_set_arn"]
                    and re.fullmatch(r"es-[a-f0-9]{32}", supplied["ClientRequestToken"]) is not None and (not activate or supplied["DisableRollback"] is (not plan["automatic_rollback"])), "infrastructure-submission-does-not-match-plan")
            reserved = store.read("deploy-execute-" + args.phase, {**intent, "change_set_arn": supplied["ChangeSetName"], "stack_arn": supplied["StackName"]})
            require(reserved is not None and supplied["ClientRequestToken"] == reserved["operation_id"], "infrastructure-submission-does-not-match-plan")
    if args.mode == "review": provider.enable(("cloudformation", "create-change-set"), prewrite)
    if existing_execution is not None:
        # Same-controller continuation returned above. This branch is retained
        # for the separately checked controller repair (or a concurrent original
        # reservation discovered after admission), never ordinary polling.
        review_reservation = store.read(phase, intent)
        require(review_reservation is not None, "infrastructure-reviewed-attempt-required")
        original = existing_execution["request"]
        observed_execution = DEPLOY.observe(provider, store, binding, parameters, original["change_set_arn"], original["stack_arn"], activate=activate, **options)
        if observed_execution["status"] != "completed":
            return {"verdict": "pending", "phase": args.phase, "plan_sha256": plan_digest, "effect": "original-operation-not-terminal"}
        # This is a current readback of the original admitted operation, not a
        # new preview or a restamped historical review. The existing observer
        # checks the original execution token plus exact deployed state. AWS
        # need not retain the executed change-set object for that proof.
        reviewed = {"status": "reviewed", "facts": {"change_set_arn": original["change_set_arn"], "stack_arn": original["stack_arn"], "resource_count": 6 if successor else 1 if activate else len(DEPLOY.RESOURCE_TYPES)}}
    else:
        reviewed = DEPLOY.prepare(provider, store, binding, parameters, activate=activate, **options)
    if reviewed["status"] == "pending": return {"verdict": "pending", "phase": args.phase, "plan_sha256": plan_digest, "effect": provider.effect}
    counts = {"operation_counts": {"create": 0, "update": 1, "delete": 0, "replace": 5, "broaden-permission": 0}} if successor else {}
    book.gate("change-set"); book.validate("change-set", reviewed["facts"]["resource_count"], activate, **counts)
    if args.mode == "review": return {"verdict": "reviewed", "phase": args.phase, "plan_sha256": plan_digest, "effect": "change-set-reviewed-not-executed"}
    validation = provider("cloudformation", "validate-template", TemplateBody=DEPLOY.source()[0])
    require(isinstance(validation.get("Parameters"), list) and len(validation["Parameters"]) == len(DEPLOY.PARAMETERS)
            and all(isinstance(item, dict) and isinstance(item.get("ParameterKey"), str) for item in validation["Parameters"])
            and {item["ParameterKey"] for item in validation["Parameters"]} == DEPLOY.PARAMETERS
            and validation.get("Capabilities") == ["CAPABILITY_IAM"] and not validation.get("DeclaredTransforms"), "infrastructure-execution-boundary-preflight-not-confirmed")
    require(operator_preflight(provider) == operator, "infrastructure-operator-changed")
    book.gate("execution-preflight"); book.validate("execution-preflight", reviewed["facts"]["resource_count"], activate, **counts)
    if existing_execution is None: provider.enable(("cloudformation", "execute-change-set"), prewrite)
    facts = reviewed["facts"]
    result = observed_execution if existing_execution is not None else DEPLOY.execute(provider, store, binding, parameters, facts["change_set_arn"], facts["stack_arn"], activate=activate, **options)
    deadline = time.monotonic() + args.wait_seconds
    while result["status"] == "pending" and time.monotonic() < deadline:
        print(json.dumps({"schema": "deploy/entity-smoke-infrastructure-progress/v1", "phase": args.phase, "state": "waiting-for-original-operation"}), flush=True, file=os.sys.stderr)
        time.sleep(2)
        result = DEPLOY.observe(provider, store, binding, parameters, facts["change_set_arn"], facts["stack_arn"], activate=activate, **options)
    if result["status"] != "completed": return {"verdict": "pending", "phase": args.phase, "plan_sha256": plan_digest, "effect": "original-operation-not-terminal"}
    book.gate("controlled-execution"); book.validate("controlled-execution", facts["resource_count"], activate, **counts)
    return retain_deployment(args, cache, binding, result, plan_digest, plan if successor else None)


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(InfrastructureFailure("infrastructure-arguments-invalid"))
    parser.add_argument("--mode", choices=("plan", "review", "execute", "apply"), required=True)
    parser.add_argument("--phase", choices=("create", "activate", "update", "rollback"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--approved-plan")
    parser.add_argument("--prerequisites", type=Path)
    parser.add_argument("--expected-predecessor")
    parser.add_argument("--rollback-receipt", type=Path)
    parser.add_argument("--rollback-compatibility-id")
    parser.add_argument("--wait-seconds", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    args = parser.parse_args(arguments)
    require(args.mode != "apply" or args.phase in {"update", "rollback"}, "infrastructure-arguments-invalid")
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) is not None and 0 <= args.wait_seconds <= 60, "infrastructure-arguments-invalid")
    require(args.mode == "plan" or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan) is not None, "infrastructure-approved-plan-required")
    require(args.phase != "activate" or args.prerequisites is not None, "infrastructure-activation-proof-required")
    require((args.phase in {"update", "rollback"}) == (args.expected_predecessor is not None), "infrastructure-predecessor-required")
    require(args.expected_predecessor is None or re.fullmatch(r"release-[a-f0-9]{24}", args.expected_predecessor) is not None, "infrastructure-predecessor-invalid")
    require((args.phase in {"update", "rollback"}) == (args.rollback_receipt is not None and args.rollback_compatibility_id is not None)
            and (args.phase in {"update", "rollback"} or args.rollback_receipt is None and args.rollback_compatibility_id is None), "infrastructure-rollback-arguments-invalid")
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
