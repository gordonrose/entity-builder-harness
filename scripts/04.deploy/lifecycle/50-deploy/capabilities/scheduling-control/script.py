#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.capability.scheduling-control
#   version: 3
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.scheduling
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind declared scheduling resources to reserved reviewed CloudFormation operations without replaying uncertain submissions.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: product.plan.reusable-aws-scheduling
#     path: .agentic/03.product/plans/implementation/reusable-aws-scheduling.md
"""Bounded provider control; no polling, publication, SQL, approval or replay."""
from datetime import datetime, timezone
import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[6]
sys.dont_write_bytecode = True


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


BASE = "scripts/04.deploy/shared/provider-adapters/aws/"
CF = module("scheduling_cf", BASE + "cloudformation-template.py")
CLI = module("scheduling_cli", BASE + "cli.py")
RESPONSE = module("scheduling_response", BASE + "response.py")
RESERVATIONS = module("scheduling_reservations", BASE + "resource_reservation.py")
JOURNAL = module("scheduling_cost_lock", BASE + "task_journal.py")
CHANGES = module("scheduling_changes", BASE + "change_sets.py")
FOUNDATION = module("scheduling_foundation", BASE + "foundation-checks.py")
CUSTODY = module("scheduling_custody", "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py")
ARTIFACT = module("scheduling_artifact", "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/github-artifact.py")
PUBLICATION = module("scheduling_publication", "scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/publication.py")
QUALIFICATION = module("scheduling_qualification", "scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py")
CONFIGURATION = module("scheduling_configuration", "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py")
ADMISSION = module("scheduling_admission", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/admission.py")
REALIZATION = module("scheduling_realization", "scripts/04.deploy/operational-realization-gate/script.py")


class Failure(Exception):
    def __init__(self, code, verdict="blocked"):
        self.code, self.verdict = code, verdict
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise Failure(code)


def read_json(path):
    try:
        raw = Path(path).read_bytes()
        require(len(raw) <= 262144, "input-too-large")
        return json.loads(raw)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise Failure("input-unavailable") from None


def digest(value):
    return hashlib.sha256(RESERVATIONS.canonical(value)).hexdigest()


def binding_path(target, scope):
    require(isinstance(target, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,63}", target), "target-invalid")
    require(isinstance(scope, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,63}", scope), "scope-invalid")
    return ROOT / "infra/04.deploy/03.product/targets" / target / "20-scopes" / scope / "10-workload-binding/scheduling-binding.yml"


def load_binding(target, scope):
    path = binding_path(target, scope)
    try:
        value = CF.template(path.read_text())
        require(value.get("schema") == "deploy/scheduling-control-binding/v1" and value.get("target") == target and value.get("scope") == scope, "binding-identity-invalid")
        profile = CF.template((path.parents[3] / "00-target/target-profile.yml").read_text())
        provider = profile["provider"]
        require(provider["family"] == "aws" and re.fullmatch(r"[0-9]{12}", provider["account_id"]) and re.fullmatch(r"[a-z]+-[a-z]+-[0-9]", provider["region"]), "provider-binding-invalid")
        value = {**value, "provider": provider}
        for key in ("stack", "network_stack", "database_stack", "legacy_foundation_stack"):
            require(isinstance(value.get(key), str) and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9-]{0,127}", value[key]), "stack-binding-invalid")
        for key in ("template", "network_template"):
            candidate = ROOT / value[key]
            require(candidate.is_file() and candidate.resolve().is_relative_to(path.parents[3].resolve()), "template-binding-invalid")
        require(set(value["programs"]) == {"dispatch", "worker"}, "program-binding-invalid")
        require(isinstance(value["repository"], str) and re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", value["repository"]), "repository-binding-invalid")
        contract = path.parents[1] / "00-declaration/scheduling-realization-contract.yml"
        require(value.get("realization_contract") == contract.relative_to(ROOT).as_posix()
            and contract.is_file() and contract.resolve().is_relative_to(path.parents[1].resolve()), "realization-contract-binding-invalid")
        require(REALIZATION.validate_contract(CF.template(contract.read_text())) == scope + "-scheduling-control", "realization-contract-identity-invalid")
        return value
    except Failure:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, REALIZATION.ContractFailure):
        raise Failure("binding-unavailable") from None


class Provider:
    def __init__(self, binding):
        self.binding = binding
        self.identity_checked = False
        self.coverage_checked = False

    def __call__(self, service, operation, **arguments):
        if not self.identity_checked and (service, operation) != ("sts", "get-caller-identity"):
            identity = self("sts", "get-caller-identity")
            require(identity.get("Account") == self.binding["provider"]["account_id"], "provider-identity-mismatch")
            self.identity_checked = True
        if not self.coverage_checked:
            require(RESPONSE.inventory_covered(ROOT), "delivery-inventory-not-covered")
            self.coverage_checked = True
        provider = self.binding["provider"]
        argv = ["aws", service, operation, "--region", provider["region"], "--output", "json", "--no-paginate", "--cli-connect-timeout", "5", "--cli-read-timeout", "20"]
        if provider.get("profile"):
            argv.extend(["--profile", provider["profile"]])
        if arguments:
            argv.extend(["--cli-input-json", json.dumps(arguments, separators=(",", ":"))])
        try:
            return CLI.invoke_json(argv, timeout=30, empty_body="whitespace", object_only=True, environment={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""})
        except CLI.CliFailure as failure:
            raise Failure(failure.code, "unknown") from None

    def invoke_preflight(self, function_arn, operation_id):
        return self._invoke_owned(function_arn, operation_id, "preflight")

    def invoke_failure_proof(self, function_arn, operation_id):
        return self._invoke_owned(function_arn, operation_id, "send-failure")

    def _invoke_owned(self, function_arn, operation_id, purpose):
        """One admitted synchronous invocation; private output is never printed."""
        require(purpose in {"preflight", "send-failure"}, "invocation-purpose-invalid")
        identity = self("sts", "get-caller-identity")
        require(identity.get("Account") == self.binding["provider"]["account_id"], "provider-identity-mismatch")
        prefix = f"arn:aws:lambda:{self.binding['provider']['region']}:{self.binding['provider']['account_id']}:function:kc-{self.binding['scope']}-schedule-"
        require(isinstance(function_arn, str) and re.fullmatch(re.escape(prefix) + r"(dispatch|worker):[1-9][0-9]*", function_arn), "preflight-function-invalid")
        require(purpose != "send-failure" or re.fullmatch(re.escape(prefix) + r"dispatch:[1-9][0-9]*", function_arn), "proof-invocation-function-invalid")
        require(str(uuid.UUID(operation_id)) == operation_id, "preflight-operation-invalid")
        provider = self.binding["provider"]
        with tempfile.TemporaryDirectory(prefix="scheduling-preflight-") as scratch:
            output = Path(scratch) / "response.json"
            argv = ["aws", "lambda", "invoke", "--region", provider["region"], "--output", "json",
                "--cli-connect-timeout", "5", "--cli-read-timeout", "70", "--cli-binary-format", "raw-in-base64-out",
                "--function-name", function_arn, "--invocation-type", "RequestResponse", "--log-type", "Tail",
                "--client-context", base64.b64encode(json.dumps({"custom": {"scheduling_preflight_operation_id" if purpose == "preflight" else "scheduling_proof_operation_id": operation_id}}, separators=(",", ":")).encode()).decode(),
                "--payload", '{"kind":"scheduling-preflight/v1"}' if purpose == "preflight" else '{}', str(output)]
            if provider.get("profile"):
                argv.extend(["--profile", provider["profile"]])
            try:
                metadata = CLI.invoke_json(argv, timeout=80, empty_body="reject", object_only=True,
                    environment={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""})
                require(output.is_file() and not output.is_symlink() and output.stat().st_size <= 16384, "preflight-response-invalid")
                body = json.loads(output.read_bytes())
                return metadata, body
            except CLI.CliFailure as failure:
                raise Failure(failure.code, "unknown") from None
            except (OSError, ValueError, UnicodeError, RecursionError):
                raise Failure("preflight-response-unavailable", "unknown") from None


def outputs(provider, stack, required):
    try:
        return FOUNDATION.stack_outputs(provider("cloudformation", "describe-stacks", StackName=stack), required)
    except FOUNDATION.FoundationFailure as failure:
        raise Failure(failure.code) from None


def resource(provider, stack, logical_id):
    value = provider("cloudformation", "describe-stack-resource", StackName=stack, LogicalResourceId=logical_id)
    row = value.get("StackResourceDetail")
    require(isinstance(row, dict) and row.get("LogicalResourceId") == logical_id and isinstance(row.get("PhysicalResourceId"), str), "resource-observation-invalid")
    return row["PhysicalResourceId"]


def network_parameters(provider, binding):
    foundation = outputs(provider, binding["provider"]["foundation"]["stack"], {"VpcId", "PrivateSubnetIds"})
    keys = {"WorkerSecurityGroupId", "RelaySecurityGroupId", "WorkerQueueArn", "RelationalSmokeQueueArn", "WorkerTaskRoleArn", "RelayTaskRoleArn", "RelationalWorkerTaskRoleArn", "RelationalRelayTaskRoleArn"}
    legacy = outputs(provider, binding["legacy_foundation_stack"], keys)
    subnets = foundation["PrivateSubnetIds"].split(",")
    require(len(subnets) == len(set(subnets)) == 2, "private-subnet-count-invalid")
    rows = provider("ec2", "describe-subnets", SubnetIds=subnets).get("Subnets")
    require(isinstance(rows, list) and len(rows) == 2 and {row.get("SubnetId") for row in rows} == set(subnets)
            and all(row.get("VpcId") == foundation["VpcId"] and row.get("MapPublicIpOnLaunch") is False and row.get("State") == "available" for row in rows)
            and len({row.get("AvailabilityZone") for row in rows}) == 2, "private-subnet-placement-invalid")
    groups = provider("ec2", "describe-security-groups", GroupIds=[legacy["WorkerSecurityGroupId"], legacy["RelaySecurityGroupId"]]).get("SecurityGroups")
    require(isinstance(groups, list) and len(groups) == 2 and all(row.get("VpcId") == foundation["VpcId"] for row in groups), "legacy-network-mismatch")
    require(all(any(rule.get("IpProtocol") == "tcp" and rule.get("FromPort") == rule.get("ToPort") == 443
                    and any(route.get("CidrIp") == "0.0.0.0/0" for route in rule.get("IpRanges", []))
                    for rule in group.get("IpPermissionsEgress", [])) for group in groups), "legacy-endpoint-egress-unproven")
    return {
        "VpcId": foundation["VpcId"], "PrivateSubnetIds": ",".join(subnets),
        "LegacyWorkerSecurityGroupId": legacy["WorkerSecurityGroupId"], "LegacyRelaySecurityGroupId": legacy["RelaySecurityGroupId"],
        "LegacyWorkerQueueArn": legacy["WorkerQueueArn"], "LegacyRelationalQueueArn": legacy["RelationalSmokeQueueArn"],
        "LegacyWorkerRoleArn": legacy["WorkerTaskRoleArn"], "LegacyRelayRoleArn": legacy["RelayTaskRoleArn"],
        "LegacyRelationalWorkerRoleArn": legacy["RelationalWorkerTaskRoleArn"], "LegacyRelationalRelayRoleArn": legacy["RelationalRelayTaskRoleArn"]}


def authenticated_package(binding, purpose, receipt):
    """Authenticate the producer before consuming its package-specific claims."""
    program = binding["programs"][purpose]
    selected = PUBLICATION.binding(program)
    require(selected.target == binding["target"] and selected.scope == binding["scope"]
        and selected.repository == binding["repository"] and selected.account == binding["provider"]["account_id"]
        and selected.region == binding["provider"]["region"], "publication-binding-mismatch")
    run_id = receipt["receipt_reference"].split(":", 1)[1]
    try:
        documents = ARTIFACT.documents(repository=selected.source_repository, workflow=selected.workflow,
            source_revision=receipt["source_revision"], run_id=run_id,
            artifact_name=program + "-package-custody-" + run_id,
            members=("package-custody-receipt.json", "qualified-image.json", "managed-runtime-qualification.json"))
    except ARTIFACT.ArtifactFailure as failure:
        raise Failure(failure.code) from None
    require(documents["package-custody-receipt.json"] == receipt, "publication-receipt-content-mismatch")
    qualified = documents["qualified-image.json"]
    runtime = documents["managed-runtime-qualification.json"]
    require(runtime.get("schema") == "deploy/managed-runtime-qualification/v1" and runtime.get("verdict") == "passed"
        and runtime.get("program_id") == program and runtime.get("source_revision") == receipt["source_revision"], "publication-runtime-proof-mismatch")
    require(runtime.get("cases") == {"invalid": QUALIFICATION.CASES["invalid"], "valid": QUALIFICATION.CASES[purpose]}
        and runtime.get("runtime_interface") == "official-aws-lambda-client" and runtime.get("network") == "none"
        and runtime.get("filesystem") == "read-only-with-tmpfs" and runtime.get("user") == "10001:10001", "publication-runtime-proof-incomplete")
    require(type(runtime.get("image_bytes")) is int and runtime["image_bytes"] > 0
        and isinstance(runtime.get("image_id"), str) and re.fullmatch(r"sha256:[a-f0-9]{64}", runtime["image_id"]), "publication-runtime-image-invalid")
    require(qualified.get("schema") == "deploy/local-image-qualification/v1" and qualified.get("image_id") == runtime["image_id"], "publication-qualified-image-mismatch")
    inputs = qualified.get("inputs")
    require(isinstance(inputs, dict) and inputs and all(isinstance(path, str) and isinstance(value, str)
        and re.fullmatch(r"[a-f0-9]{64}", value) and not Path(path).is_absolute() and ".." not in Path(path).parts
        and (ROOT / path).resolve().is_relative_to(ROOT) for path, value in inputs.items()), "publication-qualified-inputs-invalid")
    required = {binding["program_contract"], binding["image_contract"],
        "scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py"}
    require(required.issubset(inputs), "publication-qualified-inputs-missing")
    require(all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == value for path, value in inputs.items()), "publication-qualified-inputs-changed")
    configurations = []
    for adapter, source, selector in selected.configuration:
        require(adapter == "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py"
            and source == binding["template"], "publication-configuration-owner-mismatch")
        configurations.append({"adapter": adapter, "source": source, "selector": selector,
            "adapter_sha256": hashlib.sha256((ROOT / adapter).read_bytes()).hexdigest(),
            "projection_sha256": digest(CONFIGURATION.package_projection(ROOT / source, selector))})
    require(qualified.get("configuration_inputs") == configurations, "publication-configuration-mismatch")


def qualified_pair(binding, paths):
    receipts = {}
    for purpose in ("dispatch", "worker"):
        receipt = read_json(paths[purpose])
        program = binding["programs"][purpose]
        expected = SimpleNamespace(expected_target=binding["target"], expected_candidate=program + "-candidate", expected_package_contract=program + "-image", expected_program=program)
        try:
            CUSTODY.validate(receipt, expected)
        except CUSTODY.Failure:
            raise Failure("package-custody-rejected") from None
        require(len(receipt["source_revision"]) == 40, "source-revision-invalid")
        receipts[purpose] = receipt
    require(receipts["dispatch"]["source_revision"] == receipts["worker"]["source_revision"], "package-source-mismatch")
    revision = receipts["dispatch"]["source_revision"]
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    require(head == revision, "package-checkout-source-mismatch")
    changed = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=normal", "--",
        "apps", "packages", "platform", "infra", "scripts", ".github"], check=True, capture_output=True, text=True, timeout=10).stdout
    require(not changed.strip(), "package-checkout-uncommitted-inputs")
    # Plans/session notes may change, but executable/deployment input bytes must
    # be the published commit before downloading its source-owned proof.
    selected = [binding_path(binding["target"], binding["scope"]).relative_to(ROOT).as_posix(),
        binding["template"], binding["network_template"],
        "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py"]
    for relative in selected:
        committed = subprocess.run(["git", "-C", str(ROOT), "show", revision + ":" + relative], check=True, capture_output=True, timeout=10).stdout
        require(committed == (ROOT / relative).read_bytes(), "package-configuration-source-changed")
    for purpose, receipt in receipts.items():
        authenticated_package(binding, purpose, receipt)
    return receipts


def scope_parameters(provider, binding, receipts, tick_enabled, worker_enabled):
    network = outputs(provider, binding["network_stack"], {"EndpointSecurityGroupId", "SchedulingSqsEndpointId"})
    foundation = outputs(provider, binding["provider"]["foundation"]["stack"], {"VpcId", "PrivateSubnetIds"})
    database = outputs(provider, binding["database_stack"], {"PersistenceDatabaseIdentifier", "PersistenceDatabaseEndpoint"})
    rows = provider("rds", "describe-db-instances", DBInstanceIdentifier=database["PersistenceDatabaseIdentifier"]).get("DBInstances")
    require(isinstance(rows, list) and len(rows) == 1, "database-observation-invalid")
    db = rows[0]
    require(db.get("DBInstanceStatus") == "available" and db.get("PubliclyAccessible") is False and db.get("IAMDatabaseAuthenticationEnabled") is True
            and db.get("DBSubnetGroup", {}).get("VpcId") == foundation["VpcId"] and db.get("Endpoint", {}).get("Address") == database["PersistenceDatabaseEndpoint"], "database-alignment-invalid")
    vpcs = provider("ec2", "describe-vpcs", VpcIds=[foundation["VpcId"]]).get("Vpcs")
    require(isinstance(vpcs, list) and len(vpcs) == 1 and vpcs[0].get("State") == "available", "vpc-observation-invalid")
    database_group = resource(provider, binding["database_stack"], "DatabaseSecurityGroup")
    require(any(row.get("VpcSecurityGroupId") == database_group and row.get("Status") == "active" for row in db.get("VpcSecurityGroups", [])), "database-security-group-mismatch")
    topic = resource(provider, binding["database_stack"], "ObservabilityAlarmTopic")
    require(topic == f"arn:aws:sns:{binding['provider']['region']}:{binding['provider']['account_id']}:{binding['target']}-observability-alerts", "alarm-topic-mismatch")
    provider("sns", "get-topic-attributes", TopicArn=topic)
    prefix = binding["provider"]["account_id"] + ".dkr.ecr." + binding["provider"]["region"] + ".amazonaws.com/" + binding["repository"] + "@"
    return {"Scope": binding["scope"], "VpcId": foundation["VpcId"], "VpcCidr": vpcs[0]["CidrBlock"], "PrivateSubnetIds": foundation["PrivateSubnetIds"],
            "EndpointSecurityGroupId": network["EndpointSecurityGroupId"], "DatabaseEndpoint": database["PersistenceDatabaseEndpoint"],
            "DatabaseName": db["DBName"], "DatabaseResourceId": db["DbiResourceId"], "DatabaseSecurityGroupId": database_group,
            "DispatchImageUri": prefix + receipts["dispatch"]["image_digest"], "WorkerImageUri": prefix + receipts["worker"]["image_digest"],
            "SourceRevision": receipts["dispatch"]["source_revision"], "TickEnabled": str(tick_enabled).lower(), "WorkerEnabled": str(worker_enabled).lower(),
            "DenyDispatcherSend": "false", "AlarmTopicArn": topic}


def rendered_template(binding, component, parameters):
    path = ROOT / binding["network_template" if component == "network" else "template"]
    try:
        document = CF.template(path.read_text())
    except (OSError, ValueError):
        raise Failure("template-unavailable") from None
    require(isinstance(document, dict) and set(parameters) == set(document.get("Parameters", {})), "template-parameters-mismatch")
    if component == "scope":
        # Control toggles do not publish another version. Any runtime/environment
        # or image/source change does; the full template also binds code semantics.
        immutable = {key: value for key, value in parameters.items() if key in {
            "Scope", "PrivateSubnetIds", "DatabaseEndpoint", "DatabaseName", "DatabaseResourceId",
            "DispatchImageUri", "WorkerImageUri", "SourceRevision"}}
        fingerprint = digest({"parameters": immutable, "mappings": document["Mappings"],
            "functions": [document["Resources"][purpose + "Function"] for purpose in ("Dispatch", "Worker")]})[:20]
        replacements = {purpose + "Version": purpose + "Version" + fingerprint for purpose in ("Dispatch", "Worker")}
        def replace(value):
            if isinstance(value, dict):
                return {replacements.get(key, key): replace(item) for key, item in value.items()}
            if isinstance(value, list):
                return [replace(item) for item in value]
            if isinstance(value, str):
                if value in replacements:
                    return replacements[value]
                for old, new in replacements.items():
                    value = value.replace("${" + old + ".", "${" + new + ".")
                return value
            return value
        document = replace(document)
    return document


# This finite sequence is the controller's owned change policy, not a second
# deployment registry. Each transition has one durable identity per stack.
CONTROL_PHASES = {
    "network-create": (None, None),
    "scope-create-disabled": ("network-create", ("false", "false", "false")),
    "proof-enable": ("scope-create-disabled", ("true", "true", "false")),
    "missed-tick-disable": ("proof-enable", ("false", "false", "false")),
    "missed-tick-recovery-enable": ("missed-tick-disable", ("true", "true", "false")),
    "fault-disable": ("missed-tick-recovery-enable", ("false", "false", "false")),
    "fault-on": ("fault-disable", ("false", "false", "true")),
    "fault-off": ("fault-on", ("false", "false", "false")),
    "failure-recovery-enable": ("fault-off", ("true", "true", "false")),
    "proof-disable": ("failure-recovery-enable", ("false", "false", "false")),
    "accepted-enable": ("proof-disable", ("true", "true", "false")),
}


class Store(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/scheduling-change-reservation/v1"
    operation_prefix = "scheduling-"
    failure = staticmethod(lambda code: Failure("reservation-" + code))

    def path_for(self, phase, request):
        require(phase in {"prepare", "execute"} and isinstance(request, dict) and set(request) == {"stack", "change_set", "inputs_sha256", "control_phase"}
            and request["control_phase"] in CONTROL_PHASES, "reservation-request-invalid")
        require(all(isinstance(request[key], str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,127}", request[key]) for key in ("stack", "change_set")), "reservation-identity-invalid")
        require(request["change_set"] == "scheduling-" + request["control_phase"], "reservation-phase-name-mismatch")
        require(isinstance(request["inputs_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", request["inputs_sha256"]), "reservation-digest-invalid")
        return self.root / (request["stack"] + "-" + request["control_phase"] + "-" + phase + ".json")

    def validate_time(self, value):
        try:
            require(isinstance(value, str) and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None, "reservation-time-invalid")
        except ValueError:
            raise Failure("reservation-time-invalid") from None


class PreflightStore(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/scheduling-preflight-reservation/v1"
    operation_prefix = "scheduling-preflight-"
    failure = staticmethod(lambda code: Failure("preflight-reservation-" + code))
    slots = ("disabled", "bounded-proof", "acceptance")

    def path_for(self, phase, request):
        require(phase == "invoke" and isinstance(request, dict) and set(request) == {"scope", "slot", "expected"}
            and request["slot"] in self.slots, "preflight-request-invalid")
        expected = request["expected"]
        require(isinstance(request["scope"], str) and re.fullmatch(r"[a-z][a-z0-9-]{1,63}", request["scope"])
            and isinstance(expected, dict) and set(expected) == {"purpose", "function_arn", "source_revision", "database", "queue", "image_uri", "configuration_sha256", "endpoint_id"}
            and expected["purpose"] in {"dispatch", "worker"}, "preflight-request-invalid")
        # Fixed phase-owned slots, never a user label or an unbounded retry id.
        return self.root / (request["scope"] + "-" + request["slot"] + "-" + expected["purpose"] + "-invoke.json")

    def validate_time(self, value):
        ADMISSION.utc(value.replace("+00:00", "Z") if isinstance(value, str) else value)

    def result_path(self, request):
        return self.path_for("invoke", request).with_suffix(".result.json")


class ProofEffectStore(RESERVATIONS.ImmutableReservationStore):
    schema = "deploy/scheduling-proof-effect-reservation/v1"
    operation_prefix = "scheduling-proof-"
    failure = staticmethod(lambda code: Failure("proof-effect-reservation-" + code))

    def path_for(self, phase, request):
        require(phase == "submit" and isinstance(request, dict) and set(request) == {"scope", "case", "phase_sha256", "native_packet_sha256", "seed_packet_sha256", "expected", "message"}
            and request["case"] in {"duplicate", "send-failure"}
            and request["scope"] in {"core-server-persistence", "entity-smoke"}, "proof-effect-selection-invalid")
        require(all(isinstance(request[key], str) and re.fullmatch(r"[a-f0-9]{64}", request[key]) for key in ("phase_sha256", "native_packet_sha256"))
            and (request["seed_packet_sha256"] is None or isinstance(request["seed_packet_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", request["seed_packet_sha256"])), "proof-effect-reference-invalid")
        return self.root / (request["scope"] + "-" + request["case"] + "-proof.json")

    def validate_time(self, value):
        ADMISSION.utc(value.replace("+00:00", "Z"))

    def result_path(self, request):
        return self.path_for("submit", request).with_suffix(".result.json")


def proof_effect_request(*, binding, phase_packet, native_packet, expected, seed_packet=None):
    """Derive the only permitted message from the native production observer."""
    require(isinstance(expected, dict) and set(expected) == {"runtime", "queue_url", "queue_arn", "native_binding", "required_after"}, "proof-effect-expected-invalid")
    intent = phase_packet["intent"]
    checked = validate_phase_evidence(phase_packet, target=binding["target"], scope=binding["scope"],
        source_revision=expected["runtime"]["source_revision"], predecessor_sha256=intent["predecessor_sha256"])
    phase = checked["phase"]
    require(phase in {"proof-enable", "fault-on"}, "proof-effect-phase-invalid")
    case = "duplicate" if phase == "proof-enable" else "send-failure"
    purpose = "worker" if case == "duplicate" else "dispatch"
    runtime = expected["runtime"]
    require(isinstance(runtime, dict) and set(runtime) == {"purpose", "source_revision", "version_arn", "image_uri", "log_group"}
        and runtime["purpose"] == purpose and runtime["source_revision"] == intent["source_revision"]
        and runtime["image_uri"] == intent["parameters"][purpose.title() + "ImageUri"]
        and runtime["log_group"] == f"/aws/lambda/{binding['target']}/{binding['scope']}/scheduling", "proof-effect-runtime-mismatch")
    versions = [row["PhysicalResourceId"] for name, row in checked["state"]["resources"].items()
        if name.startswith(purpose.title() + "Version") and row["ResourceType"] == "AWS::Lambda::Version"]
    require(versions == [runtime["version_arn"]], "proof-effect-version-mismatch")
    queue = checked["state"]["resources"]["JobQueue"]["PhysicalResourceId"]
    queue_name = binding["target"] + "-" + binding["scope"] + "-scheduling"
    require(expected["queue_url"] == queue == f"https://sqs.{binding['provider']['region']}.amazonaws.com/{binding['provider']['account_id']}/{queue_name}"
        and expected["queue_arn"] == f"arn:aws:sqs:{binding['provider']['region']}:{binding['provider']['account_id']}:{queue_name}", "proof-effect-queue-mismatch")
    owner = cost_owner()
    schema = intent["template"]["Mappings"]["Scopes"][binding["scope"]]["Schema"]
    native_binding = expected["native_binding"]
    require(isinstance(native_binding, dict) and set(native_binding) == {"source_revision", "image_digest", "dependency_incarnation_sha256"}
        and native_binding["source_revision"] == runtime["source_revision"]
        and native_binding["dependency_incarnation_sha256"] == owner.proof_semantics().digest({"resource_id": intent["parameters"]["DatabaseResourceId"], "database": intent["parameters"]["DatabaseName"], "schema": schema}), "proof-effect-database-mismatch")
    context = {"binding": binding, "native_binding": native_binding}
    native = owner.native_packet(native_packet, context=context, qualified_path=None, required_after=expected["required_after"], historical=True)
    require(native["operation"] == "observe-scheduling-proof", "proof-effect-native-operation-invalid")
    snapshot = native["result"]["scheduling_observation"]
    owner.proof_semantics().proof_snapshot(snapshot, scope=binding["scope"])
    require(snapshot["schedule"] is not None, "proof-effect-schedule-required")
    if binding["scope"] == "core-server-persistence":
        require(seed_packet is not None, "proof-effect-seed-required")
        seed = owner.native_packet(seed_packet, context=context, qualified_path=None, required_after=expected["required_after"], historical=True)
        require(seed["operation"] == "seed-scheduling-proof"
            and seed["result"]["scheduling_seed"]["schedule_id"] == snapshot["schedule"]["id"]
            and seed["result"]["scheduling_seed"]["due_at"] == snapshot["schedule"]["due_at"]
            and ADMISSION.utc(seed["task"]["stopped_at"].replace("+00:00", "Z")) <= ADMISSION.utc(snapshot["observed_at"]), "proof-effect-seed-mismatch")
    else:
        require(seed_packet is None and native.get("case") == ("minute-delivery" if case == "duplicate" else "failure-recovery"), "proof-effect-native-case-mismatch")
    if case == "duplicate":
        require(snapshot["outbox"] is not None and snapshot["outbox"]["state"] == "published"
            and snapshot["processing"] is not None and snapshot["processing"].get("completion", {}).get("outcome") == "succeeded", "proof-effect-original-not-completed")
        message = json.dumps(snapshot["delivery_message"], separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    else:
        require(snapshot["schedule"]["state"] == "waiting" and snapshot["outbox"] is None and snapshot["processing"] is None,
            "proof-effect-waiting-reminder-required")
        message = "{}"
    return {"scope": binding["scope"], "case": case, "phase_sha256": digest(phase_packet), "native_packet_sha256": digest(native_packet),
        "seed_packet_sha256": None if seed_packet is None else digest(seed_packet), "expected": expected, "message": message}


def failed_invocation_evidence(logs, request, reservation, stream):
    """Select only the original marker and AWS start/error report, no raw errors."""
    runtime = request["expected"]["runtime"]
    ADMISSION.function_log_stream(stream, runtime["version_arn"])
    require(isinstance(logs, list) and len(logs) <= 1000, "proof-invocation-logs-invalid")
    operation_id = str(uuid.UUID(reservation["operation_id"].removeprefix(ProofEffectStore.operation_prefix)))
    markers, starts, reports = [], [], []
    for value in logs:
        require(isinstance(value, dict), "proof-invocation-logs-invalid")
        if value.get("type") in {"platform.start", "platform.report"}:
            (starts if value["type"] == "platform.start" else reports).append(value.get("record"))
            continue
        selected = value
        if set(value) & {"timestamp", "requestId"} and "message" in value:
            selected = value["message"]
            if isinstance(selected, str):
                try:
                    selected = json.loads(selected)
                except (ValueError, RecursionError):
                    continue
        if isinstance(selected, dict) and selected.get("level") == "info" and selected.get("message") == "Scheduling proof invocation.":
            fields = selected.get("fields")
            if isinstance(fields, dict) and set(fields) == {"scheduling_invocation"}:
                marker = fields["scheduling_invocation"]
                if isinstance(marker, dict) and marker.get("operation_id") == operation_id:
                    markers.append(marker)
    require(len(markers) == 1, "proof-invocation-marker-not-unique")
    marker = markers[0]
    require(set(marker) == {"schema", "operation_id", "source_revision", "request_id", "function_arn", "checked_at"}
        and marker["schema"] == "kanbien/scheduling-proof-invocation/v1" and marker["source_revision"] == runtime["source_revision"]
        and marker["function_arn"] == runtime["version_arn"] and isinstance(marker["request_id"], str)
        and re.fullmatch(r"[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}", marker["request_id"]), "proof-invocation-marker-invalid")
    began = ADMISSION.utc(reservation["reserved_at"].replace("+00:00", "Z"))
    require(0 <= (ADMISSION.utc(marker["checked_at"]) - began).total_seconds() <= 120, "proof-invocation-time-invalid")
    selected_starts = [row for row in starts if isinstance(row, dict) and row.get("requestId") == marker["request_id"]]
    selected_reports = [row for row in reports if isinstance(row, dict) and row.get("requestId") == marker["request_id"]]
    require(len(selected_starts) == len(selected_reports) == 1 and selected_starts[0].get("version") == runtime["version_arn"].rsplit(":", 1)[1], "proof-invocation-request-unconfirmed")
    report = selected_reports[0]
    metrics = report.get("metrics", {})
    require(report.get("status") == "error" and type(metrics.get("billedDurationMs")) in {int, float}
        and 0 < metrics["billedDurationMs"] <= 120000 and metrics.get("memorySizeMB") == 512, "proof-invocation-failure-unconfirmed")
    return {"log_stream": stream, "marker": marker, "start": {"requestId": marker["request_id"], "version": selected_starts[0]["version"]},
        "report": {"requestId": marker["request_id"], "status": "error", "metrics": {"billedDurationMs": metrics["billedDurationMs"], "memorySizeMB": 512}}}


def capture_failed_invocation(provider, request, reservation):
    expected = request["expected"]["runtime"]
    start = int(ADMISSION.utc(reservation["reserved_at"].replace("+00:00", "Z")).timestamp() * 1000)
    identity = str(uuid.UUID(reservation["operation_id"].removeprefix(ProofEffectStore.operation_prefix)))
    rows = ADMISSION.collection(provider, "logs", "filter-log-events", "events", logGroupName=expected["log_group"],
        startTime=start, endTime=start + 120000, filterPattern='"' + identity + '"')
    require(len(rows) == 1, "proof-invocation-original-unresolved")
    stream = rows[0].get("logStreamName")
    ADMISSION.function_log_stream(stream, expected["version_arn"])
    value = provider("logs", "get-log-events", logGroupName=expected["log_group"], logStreamName=stream,
        startTime=start, endTime=start + 120000, startFromHead=True, limit=1000)
    require(isinstance(value.get("events"), list) and len(value["events"]) < 1000, "proof-invocation-window-incomplete")
    return failed_invocation_evidence([json.loads(row["message"]) for row in value["events"]], request, reservation, stream)


def validate_proof_effect(packet, *, binding, phase_packet, native_packet, expected, seed_packet=None):
    request = proof_effect_request(binding=binding, phase_packet=phase_packet, native_packet=native_packet, expected=expected, seed_packet=seed_packet)
    require(isinstance(packet, dict) and set(packet) == {"schema", "reservation", "response", "invocation", "captured_at"}
        and packet["schema"] == "deploy/scheduling-proof-effect-evidence/v1", "proof-effect-packet-invalid")
    reserved = ProofEffectStore.validate_record("submit", request, packet["reservation"], validate_time=lambda value: ADMISSION.utc(value.replace("+00:00", "Z")))
    start, captured = ADMISSION.utc(reserved["reserved_at"].replace("+00:00", "Z")), ADMISSION.utc(packet["captured_at"])
    require(start <= captured and start >= ADMISSION.utc(phase_packet["terminal"]["Timestamp"].replace("+00:00", "Z")), "proof-effect-time-invalid")
    response = packet["response"]
    if request["case"] == "duplicate":
        require(packet["invocation"] is None, "proof-effect-invocation-unexpected")
        if response is not None:
            require(isinstance(response, dict) and set(response) == {"MessageId", "MD5OfMessageBody"}
                and isinstance(response["MessageId"], str) and re.fullmatch(r"[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}", response["MessageId"])
                and response["MD5OfMessageBody"] == hashlib.md5(request["message"].encode(), usedforsecurity=False).hexdigest(), "proof-effect-send-response-invalid")
    else:
        require(response is None or isinstance(response, dict) and set(response) == {"StatusCode", "ExecutedVersion", "FunctionError"}
            and response["StatusCode"] == 200 and response["ExecutedVersion"] == expected["runtime"]["version_arn"].rsplit(":", 1)[1]
            and response["FunctionError"] in {"Handled", "Unhandled"}, "proof-effect-invoke-response-invalid")
        observed = packet["invocation"]
        require(isinstance(observed, dict) and set(observed) == {"log_stream", "marker", "start", "report"}, "proof-effect-invocation-required")
        logs = [{"level": "info", "message": "Scheduling proof invocation.", "fields": {"scheduling_invocation": observed["marker"]}},
            {"type": "platform.start", "record": observed["start"]}, {"type": "platform.report", "record": observed["report"]}]
        require(failed_invocation_evidence(logs, request, reserved, observed["log_stream"]) == observed, "proof-effect-invocation-mismatch")
        require(ADMISSION.utc(observed["marker"]["checked_at"]) <= captured, "proof-effect-time-invalid")
    return {"case": request["case"], "operation_id": reserved["operation_id"], "reserved_at": reserved["reserved_at"],
        "request_sha256": reserved["request_sha256"],
        "request_id": None if packet["invocation"] is None else packet["invocation"]["marker"]["request_id"],
        "invoked_at": None if packet["invocation"] is None else packet["invocation"]["marker"]["checked_at"],
        "acknowledgement": "retained" if response is not None else "unknown", "message_sha256": hashlib.sha256(request["message"].encode()).hexdigest(),
        "invocation": packet["invocation"], "packet_sha256": digest(packet)}


def reobserve_proof_inputs(provider, store, binding, *, phase_packet, native_packet, expected, qualified_path, seed_packet=None):
    """Read original native/provider owners, never supplied success booleans."""
    phase = authenticate_phase_evidence(provider, store, binding, phase_packet)
    owner = cost_owner()
    context = {"binding": binding, "native_binding": expected["native_binding"]}
    native = owner.native_packet(native_packet, context=context, qualified_path=qualified_path,
        required_after=expected["required_after"], historical=False)
    if seed_packet is not None:
        owner.native_packet(seed_packet, context=context, qualified_path=qualified_path,
            required_after=expected["required_after"], historical=False)
    owner.runtime_function(provider("lambda", "get-function", FunctionName=expected["runtime"]["version_arn"]), expected["runtime"])
    return phase, native["result"]["scheduling_observation"]


def proof_effect_once(provider, store, binding, *, phase_packet, native_packet, expected, qualified_path,
        admit, seed_packet=None, reconcile=False):
    """One original controlled effect; unknown submission is never repeated.

    The owning phase gate supplies admission after authenticating all current
    work and budget facts. This function does not make a waiting reminder an
    authorization to execute unrelated queued work.
    """
    request = proof_effect_request(binding=binding, phase_packet=phase_packet, native_packet=native_packet,
        expected=expected, seed_packet=seed_packet)
    retained = store.read("submit", request)
    result_path = store.result_path(request)
    RESERVATIONS.no_symlinks(result_path)
    if result_path.exists():
        packet = read_json(result_path)
        require(retained is not None and packet.get("reservation") == retained, "proof-effect-result-orphaned")
        reobserve_proof_effect(provider, Store(store.root), binding, packet, phase_packet=phase_packet,
            native_packet=native_packet, expected=expected, qualified_path=qualified_path, seed_packet=seed_packet)
        return packet
    response, invocation = None, None
    if retained is None:
        require(not reconcile, "proof-effect-operation-not-reserved")
        phase, snapshot = reobserve_proof_inputs(provider, Store(store.root), binding, phase_packet=phase_packet,
            native_packet=native_packet, expected=expected, qualified_path=qualified_path, seed_packet=seed_packet)
        require(phase["current_phase"] == phase["phase"], "proof-effect-phase-no-longer-current")
        observed = ADMISSION.utc(snapshot["observed_at"])
        now = datetime.now(timezone.utc)
        require(0 <= (now - observed).total_seconds() <= 900, "proof-effect-native-observation-stale")
        if request["case"] == "send-failure":
            disabled_phase(provider, Store(store.root), binding, "fault-on")
            require(ADMISSION.utc(snapshot["schedule"]["due_at"]) <= now, "proof-effect-reminder-not-due")
        admit()
        retained, fresh = store.reserve("submit", request)
        require(fresh, "proof-effect-submission-uncertain-no-replay")
        if request["case"] == "duplicate":
            result = provider("sqs", "send-message", QueueUrl=expected["queue_url"], MessageBody=request["message"])
            response = {key: result.get(key) for key in ("MessageId", "MD5OfMessageBody")}
        else:
            operation_id = str(uuid.UUID(retained["operation_id"].removeprefix(ProofEffectStore.operation_prefix)))
            metadata, _private_body = provider.invoke_failure_proof(expected["runtime"]["version_arn"], operation_id)
            response = {key: metadata.get(key) for key in ("StatusCode", "ExecutedVersion", "FunctionError")}
    else:
        require(reconcile, "proof-effect-submission-uncertain-no-replay")
        reobserve_proof_inputs(provider, Store(store.root), binding, phase_packet=phase_packet,
            native_packet=native_packet, expected=expected, qualified_path=qualified_path, seed_packet=seed_packet)
    if request["case"] == "send-failure":
        invocation = capture_failed_invocation(provider, request, retained)
    packet = {"schema": "deploy/scheduling-proof-effect-evidence/v1", "reservation": retained,
        "response": response, "invocation": invocation, "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    validate_proof_effect(packet, binding=binding, phase_packet=phase_packet, native_packet=native_packet,
        expected=expected, seed_packet=seed_packet)
    require(RESERVATIONS.write_exclusive(result_path, packet), "proof-effect-result-retention-uncertain")
    # Unknown duplicate acknowledgement remains unknown: a later durable skip
    # cannot identify this physical send rather than a natural redelivery.
    return packet


def reobserve_proof_effect(provider, store, binding, packet, *, phase_packet, native_packet, expected, qualified_path, seed_packet=None):
    """Authenticate local original, remote history and fault logs without effects."""
    checked = validate_proof_effect(packet, binding=binding, phase_packet=phase_packet,
        native_packet=native_packet, expected=expected, seed_packet=seed_packet)
    effects = ProofEffectStore(store.root)
    request = packet["reservation"]["request"]
    require(effects.read("submit", request) == packet["reservation"]
        and read_json(effects.result_path(request)) == packet, "proof-effect-original-mismatch")
    reobserve_proof_inputs(provider, store, binding, phase_packet=phase_packet, native_packet=native_packet,
        expected=expected, qualified_path=qualified_path, seed_packet=seed_packet)
    if request["case"] == "send-failure":
        require(capture_failed_invocation(provider, request, packet["reservation"]) == packet["invocation"], "proof-effect-original-invocation-mismatch")
    return checked


def preflight_expected(provider, binding, parameters, purpose):
    require(purpose in {"dispatch", "worker"}, "preflight-purpose-invalid")
    values = outputs(provider, binding["stack"], {"DispatchVersionArn", "WorkerVersionArn", "JobQueueArn"})
    arn = values[purpose.title() + "VersionArn"]
    prefix = f"arn:aws:lambda:{binding['provider']['region']}:{binding['provider']['account_id']}:function:kc-{binding['scope']}-schedule-{purpose}:"
    require(isinstance(arn, str) and arn.startswith(prefix) and re.fullmatch(r"[1-9][0-9]*", arn[len(prefix):]), "immutable-function-version-required")
    value = provider("lambda", "get-function", FunctionName=arn)
    configuration = value.get("Configuration", {})
    require(configuration.get("FunctionArn") == arn and configuration.get("Version") == arn.rsplit(":", 1)[1]
        and configuration.get("State") == "Active" and configuration.get("LastUpdateStatus") == "Successful"
        and value.get("Code", {}).get("ResolvedImageUri") == parameters[purpose.title() + "ImageUri"], "preflight-function-mismatch")
    variables = configuration.get("Environment", {}).get("Variables", {})
    scopes = CF.template((ROOT / binding["template"]).read_text())["Mappings"]["Scopes"][binding["scope"]]
    username = scopes["Dispatcher" if purpose == "dispatch" else "Worker"]
    database = {"name": parameters["DatabaseName"], "schema": scopes["Schema"], "username": username}
    require(variables.get("PLATFORM_SOURCE_COMMIT_SHA") == parameters["SourceRevision"]
        and variables.get("PERSISTENCE_SCHEDULING_DATABASE_USERNAME") == username
        and variables.get("PERSISTENCE_POSTGRES_SCHEMA") == scopes["Schema"]
        and variables.get("PERSISTENCE_POSTGRES_DATABASE") == parameters["DatabaseName"]
        and variables.get("SCHEDULING_QUEUE_ARN") == values["JobQueueArn"], "preflight-configuration-mismatch")
    network = outputs(provider, binding["network_stack"], {"SchedulingSqsEndpointId", "EndpointSecurityGroupId"})
    endpoints = provider("ec2", "describe-vpc-endpoints", VpcEndpointIds=[network["SchedulingSqsEndpointId"]]).get("VpcEndpoints")
    require(isinstance(endpoints, list) and len(endpoints) == 1, "preflight-endpoint-unavailable")
    endpoint = endpoints[0]
    require(endpoint.get("VpcEndpointId") == network["SchedulingSqsEndpointId"] and endpoint.get("State") == "available"
        and endpoint.get("VpcId") == parameters["VpcId"] and endpoint.get("PrivateDnsEnabled") is True
        and endpoint.get("ServiceName") == f"com.amazonaws.{binding['provider']['region']}.sqs"
        and set(endpoint.get("SubnetIds", [])) == set(parameters["PrivateSubnetIds"].split(","))
        and [row.get("GroupId") for row in endpoint.get("Groups", [])] == [network["EndpointSecurityGroupId"]], "preflight-endpoint-mismatch")
    ids = endpoint.get("NetworkInterfaceIds")
    require(isinstance(ids, list) and len(ids) == len(set(ids)) == 2, "preflight-endpoint-interfaces-invalid")
    interfaces = provider("ec2", "describe-network-interfaces", NetworkInterfaceIds=ids).get("NetworkInterfaces")
    require(isinstance(interfaces, list) and {row.get("NetworkInterfaceId") for row in interfaces} == set(ids)
        and all(row.get("VpcId") == parameters["VpcId"] and isinstance(row.get("PrivateIpAddress"), str) for row in interfaces), "preflight-endpoint-addresses-invalid")
    addresses = sorted({row["PrivateIpAddress"] for row in interfaces})
    queue = None if purpose == "dispatch" else {"arn": values["JobQueueArn"], "address_count": len(addresses),
        "address_sha256": hashlib.sha256(json.dumps(addresses, separators=(",", ":")).encode()).hexdigest()}
    selected = {key: configuration.get(key) for key in ("FunctionArn", "Version", "Role", "Environment", "VpcConfig", "Timeout", "MemorySize", "Architectures", "LoggingConfig")}
    return {"purpose": purpose, "function_arn": arn, "source_revision": parameters["SourceRevision"], "database": database,
        "queue": queue, "image_uri": parameters[purpose.title() + "ImageUri"], "configuration_sha256": digest(selected), "endpoint_id": endpoint["VpcEndpointId"]}


def preflight_once(provider, store, request, *, admit, reconcile=False, fresh=True):
    """Retain first, submit once; missing acknowledgement is never a retry."""
    retained = store.read("invoke", request)
    result_path = store.result_path(request)
    RESERVATIONS.no_symlinks(result_path)
    previous = None
    if result_path.exists():
        require(retained is not None, "preflight-result-orphaned")
        result = read_json(result_path)
        require(result.get("schema") == "deploy/scheduling-preflight-evidence/v1" and result.get("reservation") == retained
            and result.get("request_sha256") == digest(request), "preflight-retained-result-mismatch")
        ADMISSION.preflight_body(result["evidence"]["response"], request["expected"], retained, fresh=False)
        previous = result
        reconcile = True
    if retained is not None:
        # Until original-log reconciliation establishes the same runtime result,
        # no fresh function invocation is permitted (even after a timeout).
        require(reconcile, "preflight-invocation-uncertain-no-replay")
        operation_id = str(uuid.UUID(retained["operation_id"].removeprefix(store.operation_prefix)))
        start = int(ADMISSION.utc(retained["reserved_at"].replace("+00:00", "Z")).timestamp() * 1000)
        group = f"/aws/lambda/{provider.binding['target']}/{request['scope']}/scheduling"
        rows = ADMISSION.collection(provider, "logs", "filter-log-events", "events", logGroupName=group,
            startTime=start, endTime=start + 120000, filterPattern='"' + operation_id + '"')
        require(len(rows) == 1 and isinstance(rows[0].get("message"), str), "preflight-original-result-unresolved")
        selected = json.loads(rows[0]["message"])
        # Fetch the actual bounded stream window, including the AWS report for
        # this request; never infer billing from our wall-clock time.
        stream = rows[0].get("logStreamName")
        # Lambda's documented custom-group stream includes name and version.
        # Both functions share this group; body text alone cannot select one.
        ADMISSION.function_log_stream(stream, request["expected"]["function_arn"])
        window = provider("logs", "get-log-events", logGroupName=group, logStreamName=stream, startTime=start, endTime=start + 120000, limit=1000, startFromHead=True)
        events = window.get("events")
        require(isinstance(events, list) and len(events) < 1000, "preflight-original-log-window-incomplete")
        logs = [json.loads(row["message"]) for row in events]
        require(selected in logs, "preflight-original-result-unresolved")
        evidence = ADMISSION.preflight_logs(logs, request["expected"], retained, fresh=False)
    else:
        require(not reconcile, "preflight-operation-not-reserved")
        index = store.slots.index(request["slot"])
        if index:
            for slot in store.slots[:index]:
                path = store.path_for("invoke", {**request, "slot": slot})
                if not path.exists():
                    require(slot != "disabled", "preflight-predecessor-required")
                    continue
                original = read_json(path)
                predecessor = original.get("request") if isinstance(original, dict) else None
                require(isinstance(predecessor, dict) and predecessor.get("scope") == request["scope"]
                    and predecessor.get("slot") == slot and predecessor.get("expected") == request["expected"], "preflight-predecessor-mismatch")
                # Optional freshness slots are not mandatory repeated tests.
                # Every actually reserved earlier invocation must nevertheless
                # resolve before a successor; uncertainty cannot be skipped.
                preflight_once(provider, store, predecessor, admit=trusted_admission_required, reconcile=True, fresh=False)
        admit()
        retained, new_reservation = store.reserve("invoke", request)
        require(new_reservation, "preflight-invocation-uncertain-no-replay")
        operation_id = str(uuid.UUID(retained["operation_id"].removeprefix(store.operation_prefix)))
        metadata, body = provider.invoke_preflight(request["expected"]["function_arn"], operation_id)
        evidence = ADMISSION.invocation_evidence(metadata, body, request["expected"], retained)
    result = {"schema": "deploy/scheduling-preflight-evidence/v1", "reservation": retained, "request_sha256": digest(request), "evidence": evidence}
    ADMISSION.preflight_body(evidence["response"], request["expected"], retained, fresh=fresh)
    if previous is not None:
        # Log windows may contain different unrelated records than Invoke Tail.
        # Compare every selected substantive fact against fresh provider logs.
        require({key: value for key, value in previous["evidence"].items() if key != "logs_sha256"}
                == {key: value for key, value in evidence.items() if key != "logs_sha256"}, "preflight-retained-provider-mismatch")
        return result
    require(RESERVATIONS.write_exclusive(result_path, result), "preflight-result-retention-uncertain")
    return result


def validate_preflight_evidence(packet, *, scope, slot, expected):
    """Pure original-result validation; freshness is a separate action gate."""
    require(isinstance(packet, dict) and set(packet) == {"schema", "reservation", "request_sha256", "evidence"}
        and packet["schema"] == "deploy/scheduling-preflight-evidence/v1" and slot in PreflightStore.slots, "preflight-evidence-invalid")
    request = {"scope": scope, "slot": slot, "expected": expected}
    retained = PreflightStore.validate_record("invoke", request, packet["reservation"],
        validate_time=lambda value: ADMISSION.utc(value.replace("+00:00", "Z")))
    evidence = packet["evidence"]
    require(packet["request_sha256"] == digest(request) and isinstance(evidence, dict)
        and set(evidence) == {"response", "billed_duration_ms", "memory_mb", "request_id", "logs_sha256", "report"}
        and isinstance(evidence["logs_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", evidence["logs_sha256"]), "preflight-evidence-invalid")
    logs = [{"level": "info", "message": "Scheduling read-only preflight completed.", "fields": {"scheduling_preflight": evidence["response"]}}, evidence["report"]]
    selected = ADMISSION.preflight_logs(logs, expected, retained, fresh=False)
    require({key: value for key, value in evidence.items() if key != "logs_sha256"}
        == {key: value for key, value in selected.items() if key != "logs_sha256"}, "preflight-evidence-report-mismatch")
    return {"scope": scope, "slot": slot, "purpose": expected["purpose"], "expected": expected,
        "response": evidence["response"], "billed_duration_ms": evidence["billed_duration_ms"], "memory_mb": evidence["memory_mb"], "packet_sha256": digest(packet)}


def capture_preflight(provider, store, binding, slot, purpose):
    """Re-read the reserved invocation's actual logs; never invoke a function."""
    require(slot in PreflightStore.slots and purpose in {"dispatch", "worker"}, "preflight-selection-invalid")
    path = store.root / (binding["scope"] + "-" + slot + "-" + purpose + "-invoke.json")
    RESERVATIONS.no_symlinks(path)
    original = read_json(path)
    request = original.get("request") if isinstance(original, dict) else None
    require(isinstance(request, dict) and request.get("scope") == binding["scope"] and request.get("slot") == slot
        and isinstance(request.get("expected"), dict) and request["expected"].get("purpose") == purpose, "preflight-selection-invalid")
    packet = preflight_once(provider, store, request, admit=trusted_admission_required, reconcile=True, fresh=False)
    validate_preflight_evidence(packet, scope=binding["scope"], slot=slot, expected=request["expected"])
    return packet


def version_configuration_replacement(provider, request, template, changes, entry, mode):
    """Allow only the retained async failure configuration's version transition."""
    if mode != "UPDATE" or entry.get("LogicalResourceId") != "DispatchAsyncFailure" or entry.get("ResourceType") != "AWS::Lambda::EventInvokeConfig" or entry.get("Action") != "Modify" or entry.get("Replacement") != "True":
        return False
    prior = provider("cloudformation", "get-template", StackName=request["stack"], TemplateStage="Original").get("TemplateBody")
    if isinstance(prior, str):
        prior = CF.template(prior)
    if not isinstance(prior, dict) or not isinstance(prior.get("Resources"), dict):
        return False
    current = prior["Resources"].get("DispatchAsyncFailure")
    desired = template["Resources"].get("DispatchAsyncFailure")
    if not isinstance(current, dict) or not isinstance(desired, dict) or desired.get("UpdateReplacePolicy") != "Retain" or current.get("Type") != desired.get("Type"):
        return False
    before, after = current.get("Properties"), desired.get("Properties")
    if not isinstance(before, dict) or not isinstance(after, dict) or {key: value for key, value in before.items() if key != "Qualifier"} != {key: value for key, value in after.items() if key != "Qualifier"}:
        return False
    if not isinstance(before.get("Qualifier"), dict) or not isinstance(after.get("Qualifier"), dict):
        return False
    old, new = before["Qualifier"].get("Fn::GetAtt"), after["Qualifier"].get("Fn::GetAtt")
    if not all(isinstance(value, list) and len(value) == 2 and value[1] == "Version" and isinstance(value[0], str) and re.fullmatch(r"DispatchVersion[a-f0-9]{20}", value[0]) for value in (old, new)) or old == new:
        return False
    if prior["Resources"].get(old[0], {}).get("Type") != "AWS::Lambda::Version" or template["Resources"].get(new[0], {}).get("Type") != "AWS::Lambda::Version":
        return False
    rows = [row.get("ResourceChange", {}) for row in changes if isinstance(row, dict)]
    return any(row.get("LogicalResourceId") == new[0] and row.get("Action") == "Add" for row in rows) and any(row.get("LogicalResourceId") == old[0] and row.get("Action") == "Remove" and row.get("PolicyAction") == "Retain" for row in rows)


def review(provider, request, reservation, template, parameters, mode):
    change = provider("cloudformation", "describe-change-set", StackName=request["stack"], ChangeSetName=request["change_set"])
    require(change.get("Description") == reservation["operation_id"] and change.get("ChangeSetType") == mode, "change-set-lineage-mismatch")
    if change.get("Status") in {"CREATE_PENDING", "CREATE_IN_PROGRESS"}:
        return {"verdict": "pending", "code": "change-set-pending"}
    require(change.get("Status") == "CREATE_COMPLETE", "change-set-not-reviewable")
    require(CHANGES.parameter_values(change.get("Parameters")) == parameters, "change-set-parameters-mismatch")
    observed = provider("cloudformation", "get-template", StackName=request["stack"], ChangeSetName=request["change_set"], TemplateStage="Original").get("TemplateBody")
    if isinstance(observed, str):
        observed = CF.template(observed)
    require(observed == template, "change-set-template-mismatch")
    changes = change.get("Changes")
    require(isinstance(changes, list) and bool(changes), "change-set-resources-invalid")
    for row in changes:
        entry = row.get("ResourceChange") if isinstance(row, dict) else None
        require(isinstance(entry, dict), "change-set-resources-invalid")
        logical = entry.get("LogicalResourceId")
        if mode == "UPDATE" and request.get("control_phase") in CONTROL_PHASES:
            allowed = {"QueueTransportPolicy"} if request["control_phase"] in {"fault-on", "fault-off"} else {"FixedTick", "WorkerMapping", "DispatchSilenceAlarm"}
            require(logical in allowed and entry.get("Action") == "Modify", "phase-change-set-resource-unowned")
            if logical == "DispatchSilenceAlarm":
                # A disabled tick intentionally silences only its missing-tick
                # alarm. No alarm threshold, destination or identity may move.
                details = entry.get("Details")
                prior = provider("cloudformation", "get-template", StackName=request["stack"], TemplateStage="Original").get("TemplateBody")
                if isinstance(prior, str):
                    prior = CF.template(prior)
                alarm = template["Resources"].get(logical)
                require(isinstance(prior, dict) and prior.get("Resources", {}).get(logical) == alarm
                    and isinstance(alarm, dict) and alarm.get("Type") == "AWS::CloudWatch::Alarm"
                    and alarm.get("Properties", {}).get("ActionsEnabled") == {"Fn::If": ["TickActivated", True, False]}
                    and prior.get("Conditions", {}).get("TickActivated") == template.get("Conditions", {}).get("TickActivated")
                    == {"Fn::Equals": [{"Ref": "TickEnabled"}, "true"]}
                    and isinstance(details, list) and bool(details)
                    and all(isinstance(item, dict) and item.get("Target") == {"Attribute": "Properties", "Name": "ActionsEnabled", "RequiresRecreation": "Never"} for item in details),
                    "phase-alarm-change-unowned")
        old_version = isinstance(logical, str) and re.fullmatch(r"(Dispatch|Worker)Version[a-f0-9]{20}", logical)
        require(logical in template["Resources"] or old_version and entry.get("Action") == "Remove" and entry.get("PolicyAction") == "Retain", "change-set-resource-unowned")
        if logical in template["Resources"]:
            require(entry.get("ResourceType") == template["Resources"][logical]["Type"], "change-set-resource-type-mismatch")
        require(entry.get("Action") in {"Add", "Modify", "Remove"} and (entry.get("Action") != "Remove" or old_version), "change-set-destructive-action")
        require(entry.get("Replacement", "False") == "False" or version_configuration_replacement(provider, request, template, changes, entry, mode), "change-set-replacement-rejected")
    require(change.get("ExecutionStatus") in {"AVAILABLE", "EXECUTE_IN_PROGRESS", "EXECUTE_COMPLETE"}, "change-set-execution-unavailable")
    return {"verdict": "reviewed", "code": "change-set-reviewed"}


def observe(provider, request, reservation):
    response = provider("cloudformation", "describe-stacks", StackName=request["stack"])
    stack = FOUNDATION.only(response, "Stacks", "stack-observation-invalid")
    events = provider("cloudformation", "describe-stack-events", StackName=request["stack"])
    selected = CHANGES.execution_events(events, reservation["operation_id"], stack.get("StackId"))
    require(bool(selected), "execution-lineage-not-observed")
    status = stack.get("StackStatus")
    if status in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}:
        require(any(row.get("ResourceStatus") == status for row in selected), "execution-completion-not-observed")
        return {"verdict": "completed", "code": "stack-operation-completed"}
    if status in {"CREATE_IN_PROGRESS", "UPDATE_IN_PROGRESS", "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS"}:
        return {"verdict": "pending", "code": "stack-operation-pending"}
    return {"verdict": "failed", "code": "stack-operation-not-completed"}


def control(provider, store, *, request, template, parameters, mode, action, target, admit, parameter_inputs=None):
    prepared = store.read("prepare", request)
    executed = CHANGES.retained_execution(store, preparation_phase="prepare", preparation_request=request,
        execution_phase="execute", execution_request=request, missing_preparation=lambda: Failure("execution-reservation-orphaned"))
    if executed is not None:
        return observe(provider, request, executed)
    if action == "observe" or prepared is not None and action == "prepare":
        require(prepared is not None, "operation-not-reserved")
        return review(provider, request, prepared, template, parameters, mode)
    def absent(_reservation):
        try:
            provider("cloudformation", "describe-change-set", StackName=request["stack"], ChangeSetName=request["change_set"])
        except Failure as failure:
            require(failure.code == "aws-resource-missing", "change-set-absence-unproven")
            return
        raise Failure("unowned-change-set")
    def check(reservation):
        result = review(provider, request, reservation, template, parameters, mode)
        if action != "execute" or result["verdict"] != "reviewed":
            return result
        change = provider("cloudformation", "describe-change-set", StackName=request["stack"], ChangeSetName=request["change_set"])
        require(change.get("ExecutionStatus") == "AVAILABLE", "change-set-not-available")
        admit()
        return CHANGES.execute(provider, store, phase="execute", request=request,
            arguments={"StackName": request["stack"], "ChangeSetName": request["change_set"]},
            precondition=lambda _reserved: None, observe=lambda reserved: observe(provider, request, reserved), passthrough=(Failure,))
    admit()
    require(parameter_inputs is not None or mode == "CREATE", "update-parameter-preservation-required")
    return CHANGES.prepare(provider, store, phase="prepare", request=request,
        arguments={"StackName": request["stack"], "ChangeSetName": request["change_set"], "ChangeSetType": mode,
                   "TemplateBody": json.dumps(template), "Parameters": parameter_inputs if parameter_inputs is not None else [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())],
                   "Capabilities": ["CAPABILITY_NAMED_IAM"], "Tags": [{"Key": "Target", "Value": target}]},
        precondition=absent, observe=check, passthrough=(Failure,))


def phase_path(store, binding, phase):
    require(phase in CONTROL_PHASES, "control-phase-invalid")
    stack = binding["network_stack"] if phase == "network-create" else binding["stack"]
    path = store.root / (stack + "-" + phase + "-intent.json")
    RESERVATIONS.no_symlinks(path)
    return path


def phase_request(intent):
    return {"stack": intent["stack"], "change_set": "scheduling-" + intent["phase"],
        "control_phase": intent["phase"], "inputs_sha256": digest(intent)}


def initial_database_readiness(store, binding, intent, selections):
    """Re-read the native task owners; supplied paths are data, never code.

    Each disabled scope creation uses its own zero-work gate. Shared network
    creation has no database dependency. Later phases require proof-owned exact
    synthetic inventory, not another empty-database assertion.
    """
    require(intent["phase"] == "scope-create-disabled"
        and phase_read(store, binding, intent["phase"]) == intent, "initial-database-phase-invalid")
    boundary = phase_read(store, binding, "network-create")
    require(boundary is not None and boundary["source_revision"] == intent["source_revision"], "initial-database-boundary-invalid")
    required_after = boundary["created_at"]
    scopes = {binding["scope"]}
    require(isinstance(selections, dict) and set(selections) == scopes, "initial-database-selection-invalid")
    result = {}
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    for scope in sorted(scopes):
        selected = selections[scope]
        require(isinstance(selected, dict) and isinstance(selected.get("image_digest"), str)
            and re.fullmatch(r"sha256:[a-f0-9]{64}", selected["image_digest"]), "initial-database-selection-invalid")
        try:
            if scope == "core-server-persistence":
                require(set(selected) == {"qualified_path", "receipt_paths", "image_digest"}
                    and isinstance(selected["receipt_paths"], dict) and set(selected["receipt_paths"]) == {"state", "grant", "prove"}, "initial-database-selection-invalid")
                owner = module("scheduling_core_readiness", base + "core-server-persistence/run-administration/script.py")
                observed = owner.scheduling_database_readiness(selected["qualified_path"], selected["receipt_paths"],
                    required_after=required_after, source_revision=intent["source_revision"], image_digest=selected["image_digest"])
            elif scope == "entity-smoke":
                require(set(selected) == {"receipt_path", "proof_label", "image_digest", "expected_predecessor"}, "initial-database-selection-invalid")
                owner = module("scheduling_entity_readiness", base + "entity-smoke/acceptance-evaluation/implementation/acceptance-evidence.py")
                observed = owner.scheduling_database_readiness(selected["receipt_path"], selected["proof_label"], owner.T.Provider(),
                    required_after=required_after, source_revision=intent["source_revision"], image_digest=selected["image_digest"],
                    expected_predecessor=selected["expected_predecessor"])
            else:
                raise Failure("initial-database-scope-unowned")
        except Failure:
            raise
        except Exception:
            raise Failure("initial-database-readiness-unconfirmed") from None
        require(isinstance(observed, dict) and observed.get("schema") == "kanbien/scheduling-database-readiness/v1"
            and observed.get("target") == binding["target"] and observed.get("scope") == scope
            and observed.get("source_revision") == intent["source_revision"] and observed.get("image_digest") == selected["image_digest"]
            and observed.get("required_after") == required_after, "initial-database-readiness-mismatch")
        result[scope] = observed
    return result


def disabled_phase(provider, store, binding, phase):
    """Observe one completed owned phase and its actual disabled controls."""
    require(phase in CONTROL_PHASES and CONTROL_PHASES[phase][1] is not None
        and CONTROL_PHASES[phase][1][:2] == ("false", "false"), "database-observation-controls-not-disabled")
    intent = phase_read(store, binding, phase)
    require(intent is not None, "phase-intent-required")
    completed = phase_completed(provider, store, intent)
    packet = capture_phase(provider, store, binding, phase, completed=completed)
    resources = completed["state"]["resources"]
    versions = {}
    for purpose in ("Dispatch", "Worker"):
        selected_versions = [row["PhysicalResourceId"] for logical, row in resources.items()
            if logical.startswith(purpose + "Version") and row["ResourceType"] == "AWS::Lambda::Version"]
        require(len(selected_versions) == 1, "database-observation-version-invalid")
        versions[purpose] = selected_versions[0]
    mapping_id = resources["WorkerMapping"]["PhysicalResourceId"]
    mapping = provider("lambda", "get-event-source-mapping", UUID=mapping_id)
    tick = provider("scheduler", "get-schedule", Name="due-pass", GroupName=binding["target"] + "-" + binding["scope"])
    require(mapping.get("UUID") == mapping_id and mapping.get("State") == "Disabled" and mapping.get("FunctionArn") == versions["Worker"]
        and tick.get("State") == "DISABLED" and tick.get("Target", {}).get("Arn") == versions["Dispatch"]
        and tick.get("Target", {}).get("Input") == intent["template"]["Resources"]["FixedTick"]["Properties"]["Target"]["Input"],
        "database-observation-controls-not-disabled")
    return packet


def read_disabled_phase(target, scope, phase):
    """Fixed executable/provider/store owner for native task prerequisites."""
    binding = load_binding(target, scope)
    git_dir = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, text=True, capture_output=True).stdout.strip()
    return disabled_phase(Provider(binding), Store(Path(git_dir) / "scheduling-control"), binding, phase)


def cost_owner():
    # Lazy loading avoids an executable-import cycle with the proof collector.
    return module("scheduling_cost_proof", "scripts/04.deploy/lifecycle/50-deploy/capabilities/scheduling-control/proof.py")


def validate_acceptance_evidence(evidence, *, expected, historical=False):
    """Fixed trusted reader used by both existing canonical scope collectors."""
    return cost_owner().validate_acceptance_evidence(evidence, expected=expected, historical=historical)


def read_proof_data(path):
    semantics = cost_owner().proof_semantics()
    try:
        return semantics.read(path)
    except semantics.ProofFailure as failure:
        raise Failure(failure.code) from None


def cost_admit(owner, **arguments):
    try:
        return owner.admit_cost_effect(**arguments)
    except owner.ProofFailure as failure:
        raise Failure(failure.code) from None


def cost_path(store, target):
    require(isinstance(target, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,63}", target), "cost-target-invalid")
    path = store.root / (target + "-cost-intent.json")
    RESERVATIONS.no_symlinks(path)
    return path


def cost_intent(store, binding):
    path = cost_path(store, binding["target"])
    if not path.exists():
        return None
    value = read_json(path)
    require(isinstance(value, dict) and set(value) == {"schema", "target", "source_revision", "started_at", "expires_at", "scopes", "database", "notification_topic_arn", "image_bytes", "initial_projection"}
        and value["schema"] == "deploy/scheduling-cost-intent/v1" and value["target"] == binding["target"]
        and isinstance(value["source_revision"], str) and re.fullmatch(r"[a-f0-9]{40}", value["source_revision"])
        and isinstance(value["scopes"], dict) and set(value["scopes"]) == {"core-server-persistence", "entity-smoke"}, "cost-intent-invalid")
    start, expiry = ADMISSION.utc(value["started_at"]), ADMISSION.utc(value["expires_at"])
    require(0 < (expiry - start).total_seconds() <= 86400, "cost-window-invalid")
    for scope, selected in value["scopes"].items():
        require(isinstance(selected, dict) and set(selected) == {"selection", "maintenance", "packages", "receipt_files", "receipt_paths"}
            and isinstance(selected["maintenance"], dict) and selected["maintenance"].get("source_revision") == value["source_revision"]
            and isinstance(selected["maintenance"].get("task_definition_arns"), list)
            and len(selected["maintenance"]["task_definition_arns"]) == len(set(selected["maintenance"]["task_definition_arns"]))
            and isinstance(selected["packages"], dict) and set(selected["packages"]) == {"dispatch", "worker"}
            and all(row.get("source_revision") == value["source_revision"] for row in selected["packages"].values())
            and isinstance(selected["receipt_files"], dict) and len(selected["receipt_files"]) == 3
            and isinstance(selected["receipt_paths"], dict) and set(selected["receipt_paths"]) == {"dispatch", "worker"}, "cost-intent-selection-invalid")
    return value


def maintenance_cost_binding(provider, binding, selection):
    """Use actual native package/source and deployed maintenance owners."""
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    scope = binding["scope"]
    require(isinstance(selection, dict), "cost-maintenance-selection-invalid")
    try:
        if scope == "core-server-persistence":
            require(set(selection) == {"qualified_path"}, "cost-maintenance-selection-invalid")
            owner = module("scheduling_cost_core", base + "core-server-persistence/run-administration/script.py")
            qualified = owner.RECEIPTS.qualified_maintenance(selection["qualified_path"])
            values, _ = owner.MIGRATION.outputs(owner.STACK)
            names = ("Administration", "Migration", "Verifier", "RestorationVerifier")
            definitions = [values["CoreServerPersistence" + name + "TaskDefinitionArn"] for name in names]
            checked = owner.MIGRATION.scheduling_database_binding(qualified, values,
                ((definitions[0], "core_runtime"), (definitions[1], "core_schema_migration")))
        elif scope == "entity-smoke":
            require(set(selection) == {"receipt_path", "proof_label", "expected_predecessor"}, "cost-maintenance-selection-invalid")
            owner = module("scheduling_cost_entity", base + "entity-smoke/task-execution/implementation/task-route.py")
            arguments = ["--receipt", str(selection["receipt_path"]), "--proof-label", selection["proof_label"],
                "--workload", "administration", "--operation", "observe-scheduling-prefix", "--proof-stage", "scheduling-preparation"]
            if selection["expected_predecessor"] is not None:
                arguments += ["--expected-predecessor", selection["expected_predecessor"]]
            native_provider = owner.Provider()
            context = owner.prepare(owner.parse(arguments), native_provider)
            qualified = context["custody"]
            checked = {key: context["binding"][key] for key in ("source_revision", "image_digest", "dependency_incarnation_sha256")}
            definitions = [owner.BINDING.inspect(native_provider, name, context["parameters"], context["resources"], context["binding_snapshot"])["definition"]
                for name in sorted(set(owner.BINDING.WORKLOADS) - {"server"})]
        else:
            raise Failure("cost-maintenance-scope-unowned")
        # All paid task revisions, including verifier/restore readers, must use
        # this qualified image. SQL role validation above remains purpose-aware.
        for definition in definitions:
            actual = provider("ecs", "describe-task-definition", taskDefinition=definition).get("taskDefinition", {})
            containers = actual.get("containerDefinitions", [])
            require(actual.get("taskDefinitionArn") == definition and len(containers) == 1
                and containers[0].get("image") == binding["provider"]["account_id"] + ".dkr.ecr." + binding["provider"]["region"] + ".amazonaws.com/" + binding["repository"] + "@" + qualified["image_digest"],
                "cost-maintenance-image-mismatch")
        return {**checked, "task_definition_arns": sorted(definitions)}
    except Failure:
        raise
    except Exception:
        raise Failure("cost-maintenance-binding-unconfirmed") from None


def cost_task_companions(store, intent):
    """Select native task originals already admitted by this exact budget.

    A companion is not execution authority. The fixed task callers own that
    validation; the native census below independently checks original custody.
    """
    selected = {}
    for path in sorted(store.root.glob("cost-*.admission.json")):
        RESERVATIONS.no_symlinks(path)
        value = read_json(path)
        require(isinstance(value, dict) and value.get("schema") == "deploy/scheduling-cost-admission/v1"
            and value.get("intent_sha256") == digest(intent)
            and path.name == "cost-" + str(value.get("operation_id")) + ".admission.json", "cost-original-companion-mismatch")
        if "task" not in value:
            continue
        task = value["task"]
        require(set(value) == {"schema", "intent_sha256", "operation_id", "request_sha256", "cost", "task"}
            and isinstance(task, dict) and set(task) == {"scope", "task_definition_arn"}
            and task["scope"] in intent["scopes"]
            and isinstance(task["task_definition_arn"], str)
            and re.fullmatch(r"arn:aws:ecs:eu-west-1:337159794548:task-definition/[A-Za-z0-9_-]+:[1-9][0-9]*", task["task_definition_arn"])
            and isinstance(value["request_sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", value["request_sha256"])
            and value["operation_id"] not in selected, "cost-task-companion-invalid")
        selected[value["operation_id"]] = value
    require(len(selected) <= 4096, "cost-task-census-bound-exceeded")
    return selected


def cost_native_census(intent, store):
    """Read fixed native owners, never a caller-provided file list or total."""
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    rows = []
    companions = cost_task_companions(store, intent)
    for scope, selected in intent["scopes"].items():
        initial = selected["maintenance"]["task_definition_arns"]
        admitted = {identity: value for identity, value in companions.items() if value["task"]["scope"] == scope}
        definitions = sorted(set(initial) | {value["task"]["task_definition_arn"] for value in admitted.values()})
        try:
            if scope == "core-server-persistence":
                owner = module("scheduling_cost_core_census", base + "core-server-persistence/run-administration/script.py")
                values = owner.scheduling_reservation_census(definitions)
            else:
                owner = module("scheduling_cost_entity_census", base + "entity-smoke/task-execution/implementation/task-route.py")
                values = owner.scheduling_reservation_census(selected["selection"]["proof_label"], definitions)
        except Exception:
            raise Failure("cost-native-census-unconfirmed") from None
        require(isinstance(values, list), "cost-native-census-invalid")
        for row in values:
            require(isinstance(row, dict) and set(row) == {"operation_id", "task_definition_arn", "reserved_at", "request_sha256", "task_arn"}
                and row["task_definition_arn"] in definitions, "cost-native-census-invalid")
            if row["operation_id"] in admitted:
                companion = admitted[row["operation_id"]]
                require(row["request_sha256"] == companion["request_sha256"]
                    and row["task_definition_arn"] == companion["task"]["task_definition_arn"], "cost-task-original-mismatch")
            # Querying a new immutable revision must not adopt unrelated old
            # operations from that revision. Only its admitted original joins.
            if row["task_definition_arn"] in initial or row["operation_id"] in admitted:
                rows.append(row)
        require(set(admitted) <= {row["operation_id"] for row in rows}, "cost-task-original-missing")
    require(len({row["operation_id"] for row in rows}) == len(rows), "cost-native-census-conflict")
    return rows


def recovery_native_census(intent):
    """Read complete original resource journals; never reinterpret old backups."""
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    owners = {"core-server-persistence": (
        "core-server-persistence/snapshot-operations.py", "core-server-persistence/rehearse-isolated-database-restore/script.py"),
        "entity-smoke": ("entity-smoke/controls-and-readiness/implementation/resource-control.py",)}
    rows = []
    try:
        for scope, paths in owners.items():
            for index, path in enumerate(paths):
                owner = module("scheduling_resource_census_" + scope.replace("-", "_") + str(index), base + path)
                arguments = [intent["scopes"][scope]["selection"]["proof_label"]] if scope == "entity-smoke" else []
                selected = owner.scheduling_resource_census(*arguments)
                require(isinstance(selected, list) and len(selected) <= 4096, "recovery-census-invalid")
                for original in selected:
                    require(isinstance(original, dict) and set(original) == {"schema", "phase", "operation_id", "request", "request_sha256", "reserved_at"}
                        and original["request_sha256"] == digest(original["request"]), "recovery-census-invalid")
                    rows.append({"scope": scope, "original": original})
    except Failure:
        raise
    except Exception:
        raise Failure("recovery-native-census-unconfirmed") from None
    require(len(rows) <= 8192 and len({row["original"]["operation_id"] for row in rows}) == len(rows), "recovery-census-conflict")
    return rows


def recovery_cleanup_admission(*, target, scope, original):
    """Only this budget's actual original can use its scoped cleanup authority.

    Cleanup does not reset or refund spend and remains available after expiry.
    The native owner still proves exact resource identity, safe dependents and
    any accepted-evidence retention rule before its own deletion operation.
    """
    binding = load_binding(target, scope)
    git_dir = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, text=True, capture_output=True).stdout.strip()
    store = Store(Path(git_dir) / "scheduling-control")
    intent = cost_intent(store, binding)
    require(intent is not None, "recovery-cleanup-budget-required")
    require(isinstance(original, dict) and isinstance(original.get("operation_id"), str), "recovery-cleanup-original-invalid")
    actual = [row["original"] for row in recovery_native_census(intent)
        if row["scope"] == scope and row["original"]["operation_id"] == original["operation_id"]]
    require(actual == [original], "recovery-cleanup-original-unconfirmed")
    require(original["phase"] in {"create-recovery-point", "restore-database", "execute-restore"}, "recovery-cleanup-phase-unowned")
    path = store.root / ("cost-" + original["operation_id"] + ".admission.json")
    RESERVATIONS.no_symlinks(path)
    companion = read_json(path)
    require(isinstance(companion, dict) and set(companion) in ({"schema", "intent_sha256", "operation_id", "request_sha256", "cost"},
        {"schema", "intent_sha256", "operation_id", "request_sha256", "cost", "resource"})
        and companion["schema"] == "deploy/scheduling-cost-admission/v1" and companion["intent_sha256"] == digest(intent)
        and companion["operation_id"] == original["operation_id"] and companion["request_sha256"] == original["request_sha256"]
        and companion["cost"].get("operation_id") == original["operation_id"], "recovery-cleanup-budget-mismatch")
    return original


def recovery_resource_owner(scope):
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    path = "core-server-persistence/rehearse-isolated-database-restore/script.py" if scope == "core-server-persistence" else "entity-smoke/recovery-and-replacement/restore/restore-control.py"
    require(scope in {"core-server-persistence", "entity-smoke"}, "recovery-scope-unowned")
    return module("scheduling_recovery_shape_" + scope.replace("-", "_"), base + path)


def recovery_identity(scope, original):
    request, phase = original["request"], original["phase"]
    require(phase in {"create-recovery-point", "restore-database" if scope == "core-server-persistence" else "execute-restore"}, "recovery-phase-unowned")
    if phase == "create-recovery-point":
        return "snapshot", request["snapshot"]
    owner = recovery_resource_owner(scope)
    if scope == "core-server-persistence":
        owner.restore_resource_store().path_for(phase, request)
        return "clone", request["database"]
    return "clone", owner.names(request["binding"])[2]


def recovery_lookup(provider, kind, identifier):
    operation, key, field = ("describe-db-snapshots", "DBSnapshotIdentifier", "DBSnapshots") if kind == "snapshot" else ("describe-db-instances", "DBInstanceIdentifier", "DBInstances")
    try:
        rows = provider("rds", operation, **{key: identifier}).get(field)
    except Failure as failure:
        if failure.code == "aws-resource-missing": return None
        raise
    require(isinstance(rows, list) and len(rows) == 1 and rows[0].get(key) == identifier, "recovery-resource-observation-invalid")
    return rows[0]


def recovery_descriptor(provider, intent, scope, original, environment):
    """Price only source-owned requests; physical resource facts are not inputs."""
    request, phase = original["request"], original["phase"]
    kind, identifier = recovery_identity(scope, original)
    db, maintenance = environment["database"], intent["scopes"][scope]["maintenance"]
    require(request.get("source_resource_id", db["resource_id"]) == db["resource_id"], "recovery-source-incarnation-mismatch")
    exports = []
    if scope == "entity-smoke":
        selected = request["binding"]
        require(all(selected.get(key) == maintenance[key] for key in ("source_revision", "image_digest", "dependency_incarnation_sha256"))
            and selected.get("proof_label") == intent["scopes"][scope]["selection"]["proof_label"], "recovery-native-binding-mismatch")
    if kind == "clone":
        owner = recovery_resource_owner(scope)
        if scope == "core-server-persistence":
            require(request["instance_class"] == db["class"], "recovery-class-unpriced")
            snapshot = request["snapshot"]
            # The existing native restore call explicitly enables these exports.
            exports = ["iam-db-auth-error", "postgresql"]
        else:
            text, template = owner.source()
            change = provider("cloudformation", "describe-change-set", StackName=request["stack_arn"], ChangeSetName=request["change_set_arn"])
            parameters = CHANGES.parameter_values(change.get("Parameters"))
            require(change.get("StackId") == request["stack_arn"] and change.get("ChangeSetId") == request["change_set_arn"]
                and not change.get("NextToken") and owner.request(request["binding"], parameters)
                    == {key: request[key] for key in ("binding", "parameters_sha256", "template_sha256")}, "recovery-change-binding-mismatch")
            actual = provider("cloudformation", "get-template", StackName=request["stack_arn"], ChangeSetName=request["change_set_arn"], TemplateStage="Original")
            require(CF.templates_equal(actual.get("TemplateBody"), text), "recovery-template-mismatch")
            properties = template["Resources"]["RestoredDatabase"]["Properties"]
            require(properties["DBInstanceClass"] == db["class"] and properties.get("MultiAZ") is False
                and properties.get("AllocatedStorage", db["allocated_gib"]) == db["allocated_gib"], "recovery-class-unpriced")
            exports = sorted(properties.get("EnableCloudwatchLogsExports", []))
            snapshot = parameters["SourceSnapshotArn"].rsplit(":snapshot:", 1)[-1]
        point = recovery_lookup(provider, "snapshot", snapshot)
        require(point is not None and point.get("Status") == "available" and point.get("DbiResourceId") == db["resource_id"]
            and point.get("AllocatedStorage") == db["allocated_gib"] and point.get("Engine") == "postgres", "recovery-snapshot-binding-mismatch")
    return {"operation_id": original["operation_id"], "request_sha256": original["request_sha256"],
        "reserved_at": original["reserved_at"].replace("+00:00", "Z"), "kind": kind, "source_resource_id": db["resource_id"],
        "allocated_gib": db["allocated_gib"], "instance_class": db["class"] if kind == "clone" else None,
        "backup_days": db["backup_days"] if kind == "clone" else 0, "log_exports": exports, "absent_at": None}


def recovery_cost_rows(provider, store, intent, originals):
    """Old protected snapshots are not adopted; unexplained new originals block."""
    result = []
    for selected in originals:
        scope, original = selected["scope"], selected["original"]
        kind, identifier = recovery_identity(scope, original)
        path = store.root / ("cost-" + original["operation_id"] + ".admission.json")
        RESERVATIONS.no_symlinks(path)
        if not path.exists():
            require(ADMISSION.utc(original["reserved_at"].replace("+00:00", "Z")) < ADMISSION.utc(intent["started_at"]), "recovery-current-original-unadmitted")
            observed = recovery_lookup(provider, kind, identifier)
            require(observed is None or (kind == "snapshot" and observed.get("Status") == "available"), "recovery-prior-operation-unresolved")
            continue
        companion = read_json(path)
        require(companion.get("schema") == "deploy/scheduling-cost-admission/v1" and companion.get("intent_sha256") == digest(intent)
            and companion.get("operation_id") == original["operation_id"] and companion.get("request_sha256") == original["request_sha256"]
            and isinstance(companion.get("resource"), dict), "recovery-original-cost-mismatch")
        descriptor = copy.deepcopy(companion["resource"])
        require(descriptor.get("operation_id") == original["operation_id"] and descriptor.get("request_sha256") == original["request_sha256"]
            and descriptor.get("reserved_at") == original["reserved_at"].replace("+00:00", "Z") and descriptor.get("kind") == kind
            and descriptor.get("absent_at") is None, "recovery-original-descriptor-mismatch")
        if kind == "clone":
            owner = recovery_resource_owner(scope)
            if scope == "core-server-persistence":
                cleanup = owner.scheduling_resource_cleanup(original)
            else:
                route = module("scheduling_entity_resource_cleanup", "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/recovery-and-replacement/restore/restore-route.py")
                selection = intent["scopes"][scope]["selection"]
                qualified = Path(selection["receipt_path"]).absolute()
                require(qualified.is_relative_to(ROOT), "recovery-package-path-invalid")
                cleanup = route.scheduling_resource_cleanup(original, receipt_path=qualified.relative_to(ROOT).as_posix(),
                    proof_label=selection["proof_label"], expected_predecessor=selection["expected_predecessor"], provider=provider)
            if cleanup is not None:
                require(recovery_lookup(provider, kind, identifier) is None, "recovery-cleanup-not-current")
                descriptor["absent_at"] = cleanup["observed_at"].replace("+00:00", "Z")
        result.append(descriptor)
    return result


def recovery_acceptance_resources(provider, store, binding):
    """Current original-owned recovery footprint for the monthly evidence.

    Both retained recovery points are priced; every newly created clone must
    have native positive cleanup evidence and still be absent. Old protected
    snapshots are not adopted into this proof or authorized for deletion.
    """
    intent = cost_intent(store, binding)
    require(intent is not None, "recovery-acceptance-budget-required")
    originals = recovery_native_census(intent)
    rows = recovery_cost_rows(provider, store, intent, originals)
    by_id = {row["original"]["operation_id"]: row for row in originals}
    snapshots, clones, clone_scopes = {}, [], set()
    for row in rows:
        selected = by_id[row["operation_id"]]
        scope, original = selected["scope"], selected["original"]
        kind, identifier = recovery_identity(scope, original)
        if kind == "snapshot":
            require(scope not in snapshots and row["allocated_gib"] == 20 and row["absent_at"] is None,
                "recovery-retained-snapshot-count-invalid")
            actual = recovery_lookup(provider, kind, identifier)
            require(actual is not None and actual.get("Status") == "available" and actual.get("Engine") == "postgres"
                and actual.get("AllocatedStorage") == row["allocated_gib"] and actual.get("DbiResourceId") == row["source_resource_id"],
                "recovery-retained-snapshot-mismatch")
            snapshots[scope] = {"operation_id": row["operation_id"], "request_sha256": row["request_sha256"],
                "snapshot": identifier, "source_resource_id": row["source_resource_id"], "allocated_gib": row["allocated_gib"]}
        else:
            require(row["absent_at"] is not None, "recovery-clone-cleanup-required")
            clone_scopes.add(scope)
            clones.append({"operation_id": row["operation_id"], "request_sha256": row["request_sha256"], "absent_at": row["absent_at"]})
    require(set(snapshots) == {"core-server-persistence", "entity-smoke"} and clone_scopes == set(snapshots),
        "recovery-accepted-resources-incomplete")
    require(recovery_native_census(intent) == originals and cost_intent(store, binding) == intent, "recovery-census-changed")
    return {"schema": "deploy/scheduling-retained-recovery-resources/v1", "intent_sha256": digest(intent),
        "snapshots": snapshots, "clones": sorted(clones, key=lambda row: row["operation_id"])}


def cost_resource_census(store, target):
    rows = []
    for scope in ("core-server-persistence", "entity-smoke"):
        binding = load_binding(target, scope)
        for phase in CONTROL_PHASES:
            if phase == "network-create" and scope != "core-server-persistence":
                continue
            intent = phase_read(store, binding, phase)
            if intent is not None:
                for kind in ("prepare", "execute"):
                    row = store.read(kind, phase_request(intent))
                    if row is not None:
                        rows.append(row)
        preflights = PreflightStore(store.root)
        for slot in preflights.slots:
            for purpose in ("dispatch", "worker"):
                path = store.root / (scope + "-" + slot + "-" + purpose + "-invoke.json")
                RESERVATIONS.no_symlinks(path)
                if path.exists():
                    value = read_json(path)
                    require(isinstance(value, dict) and isinstance(value.get("request"), dict)
                        and preflights.path_for("invoke", value["request"]) == path, "cost-original-selection-invalid")
                    rows.append(preflights.read("invoke", value["request"]))
        effects = ProofEffectStore(store.root)
        for case in ("duplicate", "send-failure"):
            path = store.root / (scope + "-" + case + "-proof.json")
            RESERVATIONS.no_symlinks(path)
            if path.exists():
                value = read_json(path)
                require(isinstance(value, dict) and isinstance(value.get("request"), dict)
                    and effects.path_for("submit", value["request"]) == path, "cost-original-selection-invalid")
                rows.append(effects.read("submit", value["request"]))
    return rows


def cost_companions(store, originals, intent):
    by_id = {row["operation_id"]: row for row in originals}
    require(len(by_id) == len(originals), "cost-original-identity-conflict")
    retained = []
    # These are companions to actual original records, never an independent
    # spend ledger. Orphaned/removed originals fail closed; no refund is inferred.
    for path in sorted(store.root.glob("cost-*.admission.json")):
        RESERVATIONS.no_symlinks(path)
        value = read_json(path)
        require(isinstance(value, dict) and set(value) in ({"schema", "intent_sha256", "operation_id", "request_sha256", "cost"},
            {"schema", "intent_sha256", "operation_id", "request_sha256", "cost", "resource"},
            {"schema", "intent_sha256", "operation_id", "request_sha256", "cost", "task"})
            and value["schema"] == "deploy/scheduling-cost-admission/v1" and value["intent_sha256"] == digest(intent)
            and value["operation_id"] in by_id and path.name == "cost-" + value["operation_id"] + ".admission.json"
            and value["request_sha256"] == by_id[value["operation_id"]]["request_sha256"]
            and value["cost"].get("operation_id") == value["operation_id"], "cost-original-companion-mismatch")
        retained.append(value["cost"])
    return retained


def cost_projection(provider, intent, native, *, recovery, environment=None):
    owner = cost_owner()
    definitions = {}
    def observed(service, operation, **arguments):
        key = (service, operation, digest(arguments))
        if key not in definitions:
            definitions[key] = provider(service, operation, **arguments)
        return copy.deepcopy(definitions[key])
    def cached(service, operation, **arguments):
        key = (service, operation, digest(arguments))
        require(key in definitions, "cost-task-size-observation-missing")
        return copy.deepcopy(definitions[key])
    if environment is None:
        environment = owner.cost_environment(provider, database=intent["database"], notification_topic_arn=intent["notification_topic_arn"])
    def calculate(rows, reader, resources):
        reservations = [{key: row[key] for key in ("operation_id", "task_definition_arn", "reserved_at", "request_sha256")} for row in rows]
        maintenance = owner.maintenance_costs(reader, reservations=reservations, started_at=intent["started_at"], expires_at=intent["expires_at"])
        priced = owner.resource_costs(reservations=resources, environment=environment, started_at=intent["started_at"], expires_at=intent["expires_at"])
        return owner.initial_cost_projection(region="eu-west-1", image_bytes=intent["image_bytes"], maintenance=maintenance,
            environment=environment, resources=priced, started_at=intent["started_at"])
    projection = calculate(native, observed, recovery)
    return projection, lambda rows, resources=recovery: calculate(rows, cached, resources)


def prepare_cost_intent(provider, store, binding, selections, *, expires_at):
    """Retain one fixed budget before paid tasks; this submits no cloud effect."""
    require(isinstance(selections, dict) and set(selections) == {"core-server-persistence", "entity-smoke"}, "cost-selection-invalid")
    selections = copy.deepcopy(selections)
    for scope, selected in selections.items():
        require(isinstance(selected, dict) and set(selected) == {"dispatch_receipt", "worker_receipt", "maintenance"}
            and isinstance(selected["maintenance"], dict), "cost-selection-invalid")
        for key in ("dispatch_receipt", "worker_receipt"):
            selected[key] = str(Path(selected[key]).absolute())
        key = "qualified_path" if scope == "core-server-persistence" else "receipt_path"
        selected["maintenance"][key] = str(Path(selected["maintenance"][key]).absolute())
    previous = cost_intent(store, binding)
    if previous is not None:
        expected = {scope: {"dispatch_receipt": selected["receipt_paths"]["dispatch"], "worker_receipt": selected["receipt_paths"]["worker"],
            "maintenance": selected["selection"]} for scope, selected in previous["scopes"].items()}
        # Existing intent is never replaced to restart its clock. Callers may
        # inspect it without re-evaluating mutable candidate selections.
        require(expires_at == previous["expires_at"] and expected == selections, "cost-intent-already-retained")
        return previous
    network = phase_read(store, binding, "network-create")
    require(network is not None, "phase-intent-required")
    authenticate_phase_evidence(provider, store, binding, capture_phase(provider, store, binding, "network-create"))
    started_at = network["created_at"]
    require(0 < (ADMISSION.utc(expires_at) - ADMISSION.utc(started_at)).total_seconds() <= 86400, "cost-window-invalid")
    selected_scopes, images, source_revision = {}, {}, None
    for scope in sorted(selections):
        selected = selections[scope]
        require(isinstance(selected, dict) and set(selected) == {"dispatch_receipt", "worker_receipt", "maintenance"}, "cost-selection-invalid")
        scoped = load_binding(binding["target"], scope)
        paths = {purpose: str(Path(selected[purpose + "_receipt"]).absolute()) for purpose in ("dispatch", "worker")}
        packages = qualified_pair(scoped, paths)
        maintenance_selection = dict(selected["maintenance"])
        path_key = "qualified_path" if scope == "core-server-persistence" else "receipt_path"
        maintenance_selection[path_key] = str(Path(maintenance_selection[path_key]).absolute())
        maintenance = maintenance_cost_binding(provider, scoped, maintenance_selection)
        revision = packages["dispatch"]["source_revision"]
        require(maintenance["source_revision"] == revision and source_revision in (None, revision), "cost-package-source-mismatch")
        source_revision = revision
        receipt_files = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in (*paths.values(), maintenance_selection[path_key])}
        selected_scopes[scope] = {"selection": maintenance_selection, "maintenance": maintenance, "packages": packages,
            "receipt_files": receipt_files, "receipt_paths": paths}
        for image_digest in {maintenance["image_digest"], *(row["image_digest"] for row in packages.values())}:
            identity = (scoped["repository"], image_digest)
            if identity not in images:
                values = provider("ecr", "describe-images", repositoryName=identity[0], imageIds=[{"imageDigest": image_digest}]).get("imageDetails", [])
                require(len(values) == 1 and values[0].get("imageDigest") == image_digest
                    and values[0].get("repositoryName") == identity[0] and type(values[0].get("imageSizeInBytes")) is int
                    and values[0]["imageSizeInBytes"] > 0, "cost-image-size-unconfirmed")
                images[identity] = values[0]["imageSizeInBytes"]
    values = outputs(provider, binding["database_stack"], {"PersistenceDatabaseIdentifier"})
    topic = resource(provider, binding["database_stack"], "ObservabilityAlarmTopic")
    require(topic == f"arn:aws:sns:{binding['provider']['region']}:{binding['provider']['account_id']}:{binding['target']}-observability-alerts", "cost-topic-mismatch")
    intent = {"schema": "deploy/scheduling-cost-intent/v1", "target": binding["target"], "source_revision": source_revision,
        "started_at": started_at, "expires_at": expires_at, "scopes": selected_scopes, "database": values["PersistenceDatabaseIdentifier"],
        "notification_topic_arn": topic, "image_bytes": sum(images.values()), "initial_projection": None}
    native = cost_native_census(intent, store)
    recovery_originals = recovery_native_census(intent)
    recovery = recovery_cost_rows(provider, store, intent, recovery_originals)
    intent["initial_projection"], _ = cost_projection(provider, intent, native, recovery=recovery)
    path = cost_path(store, binding["target"])
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    marker = b"scheduling-cost-intent/v1\n"
    try:
        with JOURNAL.locked(path, path.with_suffix(".lock"), marker, read_json) as (_path, descriptor, retained):
            require(retained is None and cost_native_census(intent, store) == native
                and recovery_native_census(intent) == recovery_originals, "cost-intent-or-census-changed")
            require(RESERVATIONS.write_exclusive(path, intent), "cost-intent-retention-uncertain")
            os.write(descriptor, marker)
            os.fsync(descriptor)
    except JOURNAL.JournalFailure:
        raise Failure("cost-reservation-lock-unavailable") from None
    return cost_intent(store, binding)


def reserve_cost_original(provider, store, binding, *, request, reserve, task_definition_arn=None, recovery_phase=None, required=True):
    """Short shared census/admission/native-reservation critical section.

    No cloud mutation or long provider wait is performed under this lock. The
    native owner still owns its original schema, uncertainty and submission.
    """
    intent = cost_intent(store, binding)
    if intent is None:
        # Cost observation follows bounded live proof. The native owner still
        # validates scope, source, request and original-operation identity.
        return reserve()
    if task_definition_arn is not None:
        key = "task_definition" if binding["scope"] == "core-server-persistence" else "definition"
        require(isinstance(request, dict) and request.get(key) == task_definition_arn
            and isinstance(task_definition_arn, str)
            and re.fullmatch(r"arn:aws:ecs:" + re.escape(binding["provider"]["region"]) + ":"
                + re.escape(binding["provider"]["account_id"]) + r":task-definition/[A-Za-z0-9_-]+:[1-9][0-9]*", task_definition_arn),
            "cost-task-request-mismatch")
        # The fixed native caller already owns current-stack/rollback/restore
        # execution authority. Cost admission never replaces that validation.
        # Every real revision is priced, even when it did not exist at intent
        # creation; required=False is NOT an active-budget escape hatch.
    # Package receipts are immutable data. Their reviewed source remains the
    # current checkout, not executable code selected by the receipt location.
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, text=True, capture_output=True, timeout=10).stdout.strip()
    require(head == intent["source_revision"], "cost-source-changed")
    changed = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=normal", "--",
        "apps", "packages", "platform", "infra", "scripts", ".github"], check=True, text=True, capture_output=True, timeout=10).stdout
    require(not changed.strip(), "cost-source-uncommitted")
    for selected in intent["scopes"].values():
        require(all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == checksum for path, checksum in selected["receipt_files"].items()), "cost-receipt-changed")
    native = cost_native_census(intent, store)
    recovery_originals = recovery_native_census(intent)
    recovery = recovery_cost_rows(provider, store, intent, recovery_originals)
    prospective = "prospective-" + uuid.uuid4().hex
    candidate = [] if task_definition_arn is None else [{"operation_id": prospective, "task_definition_arn": task_definition_arn,
        "reserved_at": None, "request_sha256": digest(request), "task_arn": None}]
    prospective_resource, environment = None, None
    if recovery_phase is not None:
        require(task_definition_arn is None, "cost-effect-kind-conflict")
        environment = cost_owner().cost_environment(provider, database=intent["database"], notification_topic_arn=intent["notification_topic_arn"])
        proposed = {"phase": recovery_phase, "request": request, "operation_id": prospective,
            "request_sha256": digest(request), "reserved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        prospective_resource = recovery_descriptor(provider, intent, binding["scope"], proposed, environment)
    resources = recovery + ([prospective_resource] if prospective_resource else [])
    projection, recalculate = cost_projection(provider, intent, native + candidate, recovery=resources, environment=environment)
    path = cost_path(store, binding["target"])
    marker = b"scheduling-cost-intent/v1\n"
    try:
        with JOURNAL.locked(path, path.with_suffix(".lock"), marker, read_json) as (_path, _descriptor, locked_intent):
            require(locked_intent == intent and cost_native_census(intent, store) == native
                and recovery_native_census(intent) == recovery_originals, "cost-census-changed")
            originals = native + cost_resource_census(store, binding["target"]) + [row["original"] for row in recovery_originals]
            retained = cost_companions(store, originals, intent)
            owner = cost_owner()
            initial_cost = cost_admit(owner, projection=intent["initial_projection"], retained=[], operation_id="initial-budget",
                started_at=intent["started_at"])
            retained = [initial_cost, *retained]
            # Reject ordinary budget failure before consuming a native identity.
            cost_admit(owner, projection=projection, retained=retained, operation_id=prospective, started_at=intent["started_at"])
            record, fresh = reserve()
            require(isinstance(record, dict) and record.get("request") == request and isinstance(record.get("operation_id"), str), "cost-original-reservation-mismatch")
            if not fresh:
                # Existing originals are observation-only at their native owner.
                return record, False
            actual = record["operation_id"]
            if candidate:
                actual_row = {**candidate[0], "operation_id": actual, "reserved_at": record.get("reserved_at")}
                projection = recalculate(native + [actual_row])
            if prospective_resource is not None:
                require(record.get("phase") == recovery_phase and record.get("request_sha256") == digest(request)
                    and isinstance(record.get("reserved_at"), str), "cost-original-reservation-mismatch")
                prospective_resource = {**prospective_resource, "operation_id": actual,
                    "reserved_at": record["reserved_at"].replace("+00:00", "Z")}
                projection = recalculate(native, recovery + [prospective_resource])
            admitted = cost_admit(owner, projection=projection, retained=retained, operation_id=actual, started_at=intent["started_at"])
            companion = {"schema": "deploy/scheduling-cost-admission/v1", "intent_sha256": digest(intent),
                "operation_id": actual, "request_sha256": digest(request), "cost": admitted}
            if task_definition_arn is not None:
                companion["task"] = {"scope": binding["scope"], "task_definition_arn": task_definition_arn}
            if prospective_resource is not None:
                companion["resource"] = prospective_resource
            require(RESERVATIONS.write_exclusive(store.root / ("cost-" + actual + ".admission.json"), companion), "cost-admission-retention-uncertain")
            return record, True
    except JOURNAL.JournalFailure:
        raise Failure("cost-reservation-lock-unavailable") from None


def reserve_cost_admission(*, target, scope, request, reserve, task_definition_arn, required=False):
    """Fixed native task-owner seam; callbacks are internal, not CLI inputs."""
    binding = load_binding(target, scope)
    git_dir = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, text=True, capture_output=True).stdout.strip()
    return reserve_cost_original(Provider(binding), Store(Path(git_dir) / "scheduling-control"), binding,
        request=request, reserve=reserve, task_definition_arn=task_definition_arn, required=required)


def reserve_recovery_cost_admission(*, target, scope, phase, request, reserve, required=False):
    """Native snapshot/clone reservation seam; no caller prices or authority."""
    binding = load_binding(target, scope)
    require(phase in {"create-recovery-point", "restore-database" if scope == "core-server-persistence" else "execute-restore"}, "recovery-phase-unowned")
    git_dir = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, text=True, capture_output=True).stdout.strip()
    return reserve_cost_original(Provider(binding), Store(Path(git_dir) / "scheduling-control"), binding,
        request=request, reserve=reserve, recovery_phase=phase, required=required)


def cost_intent_active(*, target):
    """An expired intent is still active for bypass prevention, never a refund."""
    binding = load_binding(target, "core-server-persistence")
    git_dir = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, text=True, capture_output=True).stdout.strip()
    return cost_intent(Store(Path(git_dir) / "scheduling-control"), binding) is not None


class CostAdmittedStore:
    """Compose cost admission at the original reserve call, not a new store."""
    def __init__(self, original, provider, binding):
        self.original, self.provider, self.binding = original, provider, binding

    def __getattr__(self, name):
        return getattr(self.original, name)

    def reserve(self, phase, request):
        if isinstance(self.original, Store) and request.get("control_phase") in {"missed-tick-disable", "fault-disable", "fault-off", "proof-disable"}:
            return reserve_cleanup_control(self.provider, self.original, self.binding, phase, request)
        return reserve_cost_original(self.provider, Store(self.original.root), self.binding, request=request,
            reserve=lambda: self.original.reserve(phase, request))


def reserve_cleanup_control(provider, store, binding, phase, request):
    """Exact no-capacity shutdown keeps its original lineage after budget expiry."""
    require(phase in {"prepare", "execute"} and request.get("control_phase") in {"missed-tick-disable", "fault-disable", "fault-off", "proof-disable"}, "cleanup-control-unowned")
    intent = phase_read(store, binding, request["control_phase"])
    budget = cleanup_control_shape(store, binding, intent)
    require(phase_request(intent) == request, "cleanup-control-intent-invalid")
    if budget is None:
        return store.reserve(phase, request)
    # Provider freshness, current incarnation and the source-owned change set
    # are checked by phase_control immediately before this short reservation.
    # No new instance/function/endpoint or proof task is admitted, and the fixed
    # budget is neither reset nor refunded by this operation.
    path = cost_path(store, binding["target"])
    marker = b"scheduling-cost-intent/v1\n"
    try:
        with JOURNAL.locked(path, path.with_suffix(".lock"), marker, read_json) as (_path, _descriptor, retained):
            require(retained == budget, "cost-intent-changed")
            return store.reserve(phase, request)
    except JOURNAL.JournalFailure:
        raise Failure("cost-reservation-lock-unavailable") from None


def cleanup_control_shape(store, binding, intent):
    budget = cost_intent(store, binding)
    require(intent is not None and intent["phase"] in {"missed-tick-disable", "fault-disable", "fault-off", "proof-disable"}
        and intent["mode"] == "UPDATE" and (budget is None or intent["source_revision"] == budget["source_revision"])
        and tuple(intent["parameters"].get(key) for key in ("TickEnabled", "WorkerEnabled", "DenyDispatcherSend")) == ("false", "false", "false"), "cleanup-control-intent-invalid")
    previous_phase = CONTROL_PHASES[intent["phase"]][0]
    previous = phase_read(store, binding, previous_phase)
    require(previous is not None and digest(previous) == intent["predecessor_sha256"]
        and intent["template"] == previous["template"] and intent["before"]["parameters"] == previous["parameters"], "cleanup-control-predecessor-invalid")
    overrides = ADMISSION.update_overrides(previous["parameters"], intent["parameters"],
        controls_only=intent["phase"] != "fault-off", fault_only=intent["phase"] == "fault-off")
    require(bool(overrides) and set(overrides) <= {"TickEnabled", "WorkerEnabled", "DenyDispatcherSend"}, "cleanup-control-parameters-invalid")
    return budget


def control_phase_inputs(store, binding, phase):
    require(phase in CONTROL_PHASES and CONTROL_PHASES[phase][0] is not None, "control-phase-invalid")
    previous = phase_read(store, binding, CONTROL_PHASES[phase][0])
    require(previous is not None, "phase-predecessor-required")
    parameters = {**previous["parameters"], **dict(zip(("TickEnabled", "WorkerEnabled", "DenyDispatcherSend"), CONTROL_PHASES[phase][1]))}
    return previous["template"], parameters, previous["source_revision"]


def initial_phase_inputs(provider, store, binding, phase, package_paths=None):
    require(phase in {"network-create", "scope-create-disabled"}, "trusted-admission-required")
    require(isinstance(package_paths, dict) and set(package_paths) == {"dispatch", "worker"}
        and all(isinstance(path, str) and path for path in package_paths.values()), "package-receipts-required")
    packages = qualified_pair(binding, package_paths)
    if phase == "network-create":
        parameters = network_parameters(provider, binding)
        template = rendered_template(binding, "network", parameters)
    else:
        parameters = scope_parameters(provider, binding, packages, False, False)
        template = rendered_template(binding, "scope", parameters)
    return template, parameters, packages["dispatch"]["source_revision"]


def admit_initial_phase(provider, store, binding, intent, selections, package_paths=None):
    """Only disabled resource creation; business-work activation stays closed."""
    require(intent["phase"] in {"network-create", "scope-create-disabled"}, "trusted-admission-required")
    template, parameters, revision = initial_phase_inputs(provider, store, binding, intent["phase"], package_paths)
    require(template == intent["template"] and parameters == intent["parameters"] and revision == intent["source_revision"], "initial-phase-inputs-changed")
    if intent["phase"] == "network-create":
        current = ADMISSION.network_facts(provider, binding, intent["parameters"])
        require(current["snapshot"] == intent["network_before"]["snapshot"], "network-before-create-changed")
    else:
        require(intent["maintenance_selection"] == scope_maintenance_selection(binding, selections[binding["scope"]]),
            "proof-work-package-selection-mismatch")
        initial_database_readiness(store, binding, intent, selections)
        network_preservation(provider, store, binding)


def admit_readonly_preflight(provider, store, binding, expected, slot):
    require(slot in PreflightStore.slots, "preflight-selection-not-admitted")
    phase = "proof-disable" if slot == "acceptance" else "scope-create-disabled"
    intent = phase_read(store, binding, phase)
    require(intent is not None, "phase-intent-required")
    disabled_phase(provider, store, binding, phase)
    ADMISSION.disabled_facts(provider, binding, intent["parameters"], intent["template"],
        normalize=CF.template, parameter_values=CHANGES.parameter_values)
    network_preservation(provider, store, binding)
    require(preflight_expected(provider, binding, intent["parameters"], expected["purpose"]) == expected, "preflight-target-changed")


def current_database_observation(provider, store, binding, intent, selection):
    """Read whole-scope counts; the proof owner must explain every pending row."""
    phase_packet = disabled_phase(provider, store, binding, intent["phase"])
    require(phase_packet["intent"] == intent, "database-observation-intent-mismatch")
    require(isinstance(selection, dict) and isinstance(selection.get("image_digest"), str)
        and re.fullmatch(r"sha256:[a-f0-9]{64}", selection["image_digest"]), "database-observation-selection-invalid")
    selected_phase = selection.get("scheduling_control_phase", intent["phase"])
    phases = list(CONTROL_PHASES)
    require(selected_phase in phases and phases.index(selected_phase) <= phases.index(intent["phase"]), "database-observation-phase-invalid")
    between = phases[phases.index(selected_phase):phases.index(intent["phase"]) + 1]
    require(all(CONTROL_PHASES[phase][1] is not None and CONTROL_PHASES[phase][1][:2] == ("false", "false") for phase in between), "database-observation-work-boundary-crossed")
    selected_packet = phase_packet
    if selected_phase != intent["phase"]:
        selected_packet = capture_phase(provider, store, binding, selected_phase)
        checked = authenticate_phase_evidence(provider, store, binding, selected_packet)
        require(checked["current_phase"] == intent["phase"], "database-observation-phase-changed")
    required_after = selected_packet["terminal"]["Timestamp"].replace("+00:00", "Z")
    if "fault-on" in between:
        effects = ProofEffectStore(store.root)
        effect_path = store.root / (binding["scope"] + "-send-failure-proof.json")
        RESERVATIONS.no_symlinks(effect_path)
        if effect_path.exists():
            original = read_json(effect_path)
            request = original.get("request")
            require(effects.read("submit", request) == original, "database-observation-effect-original-invalid")
            result = read_json(effects.result_path(request))
            require(result.get("schema") == "deploy/scheduling-proof-effect-evidence/v1" and result.get("reservation") == original
                and capture_failed_invocation(provider, request, original) == result.get("invocation"), "database-observation-effect-unresolved")
            required_after = max((required_after, result["captured_at"]), key=ADMISSION.utc)
    optional = {"scheduling_control_phase"} if "scheduling_control_phase" in selection else set()
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    try:
        if binding["scope"] == "core-server-persistence":
            require(set(selection) == {"qualified_path", "receipt_path", "image_digest"} | optional, "database-observation-selection-invalid")
            owner = module("scheduling_core_state", base + "core-server-persistence/run-administration/script.py")
            observed = owner.observe_scheduling_state_receipt(selection["receipt_path"], qualified_path=selection["qualified_path"],
                required_after=required_after, source_revision=intent["source_revision"], image_digest=selection["image_digest"])
        elif binding["scope"] == "entity-smoke":
            require(set(selection) == {"receipt_path", "proof_label", "image_digest", "expected_predecessor"} | optional, "database-observation-selection-invalid")
            owner = module("scheduling_entity_state", base + "entity-smoke/acceptance-evaluation/implementation/acceptance-evidence.py")
            observed = owner.observe_scheduling_state_receipt(selection["receipt_path"], selection["proof_label"], owner.T.Provider(),
                required_after=required_after, source_revision=intent["source_revision"], image_digest=selection["image_digest"], expected_predecessor=selection["expected_predecessor"],
                scheduling_control_phase=selected_phase)
        else:
            raise Failure("database-observation-scope-unowned")
    except Failure:
        raise
    except Exception:
        raise Failure("database-observation-unconfirmed") from None
    require(isinstance(observed, dict) and observed.get("schema") == "kanbien/scheduling-database-observation/v1"
        and observed.get("target") == binding["target"] and observed.get("scope") == binding["scope"]
        and isinstance(observed.get("binding"), dict) and observed["binding"].get("source_revision") == intent["source_revision"]
        and observed["binding"].get("image_digest") == selection["image_digest"] and observed.get("required_after") == required_after,
        "database-observation-identity-mismatch")
    require(disabled_phase(provider, store, binding, intent["phase"]) == phase_packet, "database-observation-phase-changed")
    return observed


def scope_maintenance_selection(binding, selection):
    """Keep native package selection in the existing immutable phase intent."""
    require(isinstance(selection, dict), "proof-work-package-selection-mismatch")
    key = "qualified_path" if binding["scope"] == "core-server-persistence" else "receipt_path"
    fields = {key} if binding["scope"] == "core-server-persistence" else {key, "proof_label", "expected_predecessor"}
    require(fields <= set(selection) and isinstance(selection[key], str) and bool(selection[key]),
        "proof-work-package-selection-mismatch")
    return {**{name: selection[name] for name in fields}, key: str(Path(selection[key]).absolute())}


def owned_scope_context(provider, store, binding, intent):
    """Derive native identity from original package/resource owners, not input."""
    selection = intent["maintenance_selection"]
    require(scope_maintenance_selection(binding, selection) == selection, "proof-work-package-selection-mismatch")
    maintenance = maintenance_cost_binding(provider, binding, selection)
    require(intent["source_revision"] == maintenance["source_revision"], "proof-work-source-mismatch")
    schema = intent["template"]["Mappings"]["Scopes"][binding["scope"]]["Schema"]
    native = {"source_revision": intent["source_revision"], "image_digest": maintenance["image_digest"],
        "dependency_incarnation_sha256": cost_owner().proof_semantics().digest({"resource_id": intent["parameters"]["DatabaseResourceId"],
            "database": intent["parameters"]["DatabaseName"], "schema": schema})}
    require(all(maintenance.get(key) == value for key, value in native.items()), "proof-work-database-mismatch")
    network = capture_phase(provider, store, binding, "network-create")
    authenticate_phase_evidence(provider, store, binding, network)
    require(network["intent"]["source_revision"] == intent["source_revision"], "proof-work-network-source-mismatch")
    key = "qualified_path" if binding["scope"] == "core-server-persistence" else "receipt_path"
    qualified = Path(selection[key]).absolute()
    require(qualified.is_relative_to(ROOT), "proof-work-package-path-invalid")
    return {"binding": binding, "native_binding": native,
        "required_after": network["terminal"]["Timestamp"].replace("+00:00", "Z")}, qualified.relative_to(ROOT).as_posix()


def current_owned_work(provider, store, binding, intent, database_selection, work_selection):
    context, qualified_path = owned_scope_context(provider, store, binding, intent)
    key = "qualified_path" if binding["scope"] == "core-server-persistence" else "receipt_path"
    require(isinstance(database_selection, dict) and database_selection.get("image_digest") == context["native_binding"]["image_digest"]
        and isinstance(database_selection.get(key), str)
        and Path(database_selection[key]).absolute() == (ROOT / qualified_path).absolute(), "proof-work-package-selection-mismatch")
    if binding["scope"] == "entity-smoke":
        selected = intent["maintenance_selection"]
        require(all(database_selection.get(name) == selected.get(name) for name in ("proof_label", "expected_predecessor")), "proof-work-task-selection-mismatch")
    observed = current_database_observation(provider, store, binding, intent, database_selection)
    owner = cost_owner()
    try:
        return owner.owned_work_selection(work_selection, context=context, qualified_path=qualified_path,
            database_observation=observed, historical=False)
    except owner.ProofFailure as failure:
        raise Failure(failure.code) from None


def proof_capture_context(provider, store, binding, phase):
    """Select immutable subjects from an actual retained phase, never a file ARN."""
    require(phase in CONTROL_PHASES and phase != "network-create", "proof-capture-phase-invalid")
    packet = capture_phase(provider, store, binding, phase)
    authenticate_phase_evidence(provider, store, binding, packet)
    context, qualified_path = owned_scope_context(provider, store, binding, packet["intent"])
    resources, parameters = packet["readback"]["resources"], packet["intent"]["parameters"]
    runtime = {}
    for purpose in ("dispatch", "worker"):
        observed = preflight_expected(provider, binding, parameters, purpose)
        runtime[purpose] = {"purpose": purpose, "source_revision": observed["source_revision"],
            "version_arn": observed["function_arn"], "image_uri": observed["image_uri"],
            "log_group": resources["RuntimeLogs"]["PhysicalResourceId"]}
    account, region = binding["provider"]["account_id"], binding["provider"]["region"]
    def queue_arn(name):
        url, prefix = resources[name]["PhysicalResourceId"], f"https://sqs.{region}.amazonaws.com/{account}/"
        require(isinstance(url, str) and url.startswith(prefix) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", url[len(prefix):]), "proof-capture-queue-invalid")
        return f"arn:aws:sqs:{region}:{account}:" + url[len(prefix):]
    role = resources["TickRole"]["PhysicalResourceId"]
    require(isinstance(role, str) and re.fullmatch(r"[A-Za-z0-9_+=,.@-]{1,64}", role), "proof-capture-tick-role-invalid")
    trigger = {"schedule_arn": f"arn:aws:scheduler:{region}:{account}:schedule/{binding['target']}-{binding['scope']}/due-pass",
        "function_arn": runtime["dispatch"]["version_arn"], "role_arn": f"arn:aws:iam::{account}:role/{role}",
        "dead_letter_queue_arn": queue_arn("DeadLetterQueue"),
        "input": packet["intent"]["template"]["Resources"]["FixedTick"]["Properties"]["Target"]["Input"]}
    return {**context, "qualified_path": qualified_path, "phase_packet": packet, "runtime": runtime, "trigger": trigger,
        "queue_url": resources["JobQueue"]["PhysicalResourceId"], "queue_arn": queue_arn("JobQueue")}


def capture_native_proof(provider, store, binding, phase, selection, *, preparation=False):
    """Read the existing native task owners; this route cannot submit a task."""
    require(phase in CONTROL_PHASES and phase != "network-create", "proof-capture-phase-invalid")
    packet = capture_phase(provider, store, binding, phase)
    authenticate_phase_evidence(provider, store, binding, packet)
    context, qualified_path = owned_scope_context(provider, store, binding, packet["intent"])
    boundary = context["required_after"]
    if preparation:
        require(binding["scope"] == "core-server-persistence", "proof-capture-preparation-unowned")
        boundary = capture_phase(provider, store, binding, "network-create")["intent"]["created_at"]
    owner = cost_owner().native_owner(binding["scope"])
    native = context["native_binding"]
    try:
        if binding["scope"] == "core-server-persistence":
            require(isinstance(selection, dict) and set(selection) == {"receipt_path"} and isinstance(selection["receipt_path"], str), "proof-capture-native-selection-invalid")
            reader = owner.observe_scheduling_preparation_receipt if preparation else owner.observe_scheduling_proof_receipt
            observed = reader(selection["receipt_path"], qualified_path=ROOT / qualified_path, required_after=boundary,
                source_revision=native["source_revision"], image_digest=native["image_digest"])
            return observed["packet"]
        require(isinstance(selection, dict) and set(selection) == {"operation", "case", "snapshot"}
            and selection["operation"] in owner.SYNTHETIC_TASKS, "proof-capture-native-selection-invalid")
        original = packet["intent"]["maintenance_selection"]
        arguments = ["--receipt", str(ROOT / qualified_path), "--proof-label", original["proof_label"],
            "--expected-predecessor", original["expected_predecessor"], "--proof-stage", "scheduling-proof",
            "--workload", owner.SYNTHETIC_TASKS[selection["operation"]][1], "--operation", selection["operation"], "--scheduling-case", selection["case"]]
        if selection["operation"] == "observe-scheduling-proof":
            require(isinstance(selection["snapshot"], str), "proof-capture-native-selection-invalid")
            arguments += ["--scheduling-snapshot", selection["snapshot"]]
        else:
            require(selection["snapshot"] is None, "proof-capture-native-selection-invalid")
        args, native_provider = owner.T.parse(arguments), owner.T.Provider()
        prepared = owner.T.prepare(args, native_provider)
        observed = owner.capture_scheduling_proof(owner.T, prepared, args, native_provider, required_after=boundary,
            source_revision=native["source_revision"], image_digest=native["image_digest"])
        return observed["archive"]
    except Failure:
        raise
    except Exception:
        raise Failure("proof-capture-native-unconfirmed") from None


def checked_connection_pair(provider, store, binding, parameters, *, fresh):
    """Reuse unchanged original results; never invoke while checking a gate."""
    initial = capture_phase(provider, store, binding, "scope-create-disabled")
    boundary = ADMISSION.utc(initial["terminal"]["Timestamp"].replace("+00:00", "Z"))
    preflights = PreflightStore(store.root)
    selected = {}
    for purpose in ("dispatch", "worker"):
        expected = preflight_expected(provider, binding, parameters, purpose)
        previous = None
        for slot in ("disabled", "bounded-proof"):
            path = preflights.path_for("invoke", {"scope": binding["scope"], "slot": slot, "expected": expected})
            RESERVATIONS.no_symlinks(path)
            if not path.exists():
                require(slot != "disabled", "proof-connection-required")
                continue
            packet = capture_preflight(provider, preflights, binding, slot, purpose)
            actual = packet["reservation"]["request"]["expected"]
            require(actual == expected, "proof-connection-identity-changed")
            checked = validate_preflight_evidence(packet, scope=binding["scope"], slot=slot, expected=expected)
            checked_at = ADMISSION.utc(checked["response"]["checked_at"])
            require(boundary <= checked_at and (previous is None or previous <= checked_at), "proof-connection-order-invalid")
            previous = checked_at
            selected[purpose] = packet
        ADMISSION.preflight_body(selected[purpose]["evidence"]["response"], expected, selected[purpose]["reservation"], fresh=fresh)
    return selected


def admit_bounded_phase(provider, store, binding, intent, database_selections, work_selection):
    """Only named proof transitions, after every actionable row is explained."""
    require(intent["phase"] in {"proof-enable", "missed-tick-recovery-enable", "fault-on", "failure-recovery-enable"}, "trusted-admission-required")
    require(isinstance(database_selections, dict) and set(database_selections) == {binding["scope"]}, "proof-database-selection-invalid")
    previous = phase_read(store, binding, CONTROL_PHASES[intent["phase"]][0])
    require(previous is not None and digest(previous) == intent["predecessor_sha256"], "phase-predecessor-changed")
    template, parameters, revision = control_phase_inputs(store, binding, intent["phase"])
    require(template == intent["template"] and parameters == intent["parameters"] and revision == intent["source_revision"], "proof-phase-inputs-changed")
    disabled_phase(provider, store, binding, previous["phase"])
    network_preservation(provider, store, binding)
    checked_connection_pair(provider, store, binding, previous["parameters"], fresh=intent["phase"] == "proof-enable")
    current_owned_work(provider, store, binding, previous, database_selections[binding["scope"]], work_selection)
    # Re-observe controls after native evidence collection, before submission.
    disabled_phase(provider, store, binding, previous["phase"])


def canonical_scheduling_acceptance(scope, *, reference_only=False):
    """Only the fixed live canonical owners can supply activation authority."""
    base = "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/"
    try:
        if scope == "core-server-persistence":
            owner = module("scheduling_accepted_core", base + "core-server-persistence/collect-acceptance-evidence/script.py")
            reference = owner.succession_module().current(owner.EVIDENCE_ROOT)
            require(reference is not None, "accepted-current-required")
            if reference_only:
                return reference
            record, _ = owner.updates().accepted(owner.owner(), reference["release_id"])
        elif scope == "entity-smoke":
            owner = module("scheduling_accepted_entity", base + "entity-smoke/acceptance-evaluation/implementation/acceptance-state.py")
            state = owner.State()
            if reference_only:
                reference = owner.S.current(state.root)
                require(reference is not None, "accepted-current-required")
                return reference
            selected = state.current(qualification_profile="scheduling-a2-v1")
            reference, record = selected["reference"], selected["packet"]
        else:
            raise Failure("accepted-scope-unowned")
        require(record.get("qualification_profile") == "scheduling-a2-v1"
            and record.get("evidence_class") == "live" and isinstance(record.get("scheduling_qualification"), dict), "accepted-scheduling-profile-required")
        if scope == "core-server-persistence":
            recovery = record.get("provider_observation", {}).get("database", {})
            snapshot = recovery.get("snapshot")
        else:
            # A successor that inherited older recovery proof is not evidence
            # of this budget's fresh snapshot. Do not invent a lineage fallback.
            recovery = record.get("controls", {}).get("snapshot", {}).get("facts", {})
            arn = recovery.get("snapshot_arn")
            require(isinstance(arn, str) and ":snapshot:" in arn, "accepted-recovery-evidence-required")
            snapshot = arn.rsplit(":snapshot:", 1)[1]
        require(isinstance(snapshot, str) and bool(snapshot)
            and isinstance(recovery.get("source_resource_id"), str) and bool(recovery["source_resource_id"]),
            "accepted-recovery-evidence-required")
        return {"reference": reference, "qualification": record["scheduling_qualification"],
            "recovery": {"snapshot": snapshot, "source_resource_id": recovery["source_resource_id"]}}
    except Failure:
        raise
    except Exception:
        raise Failure("accepted-canonical-record-unconfirmed") from None


def acceptance_companion(store, binding, intent, references, cost_packet, *, retain):
    """Bind the two current references to this one original control request."""
    require(intent.get("phase") == "accepted-enable", "accepted-phase-required")
    path = phase_path(store, binding, "accepted-enable").with_suffix(".acceptance.json")
    RESERVATIONS.no_symlinks(path)
    expected = {"schema": "deploy/scheduling-activation-acceptance/v1", "intent_sha256": digest(intent),
        "request_sha256": digest(phase_request(intent)), "references": references, "cost_sha256": digest(cost_packet)}
    if path.exists():
        require(read_json(path) == expected, "accepted-original-reference-changed")
    else:
        require(retain, "accepted-original-reference-required")
        require(RESERVATIONS.write_exclusive(path, expected), "accepted-reference-retention-uncertain")
    return expected


def admit_accepted_phase(provider, store, binding, intent, database_selections, work_selection):
    """Enable only this unchanged release after both canonical live acceptances."""
    require(intent.get("phase") == "accepted-enable", "accepted-phase-required")
    require(isinstance(database_selections, dict) and set(database_selections) == {binding["scope"]}, "proof-database-selection-invalid")
    previous = phase_read(store, binding, "proof-disable")
    require(previous is not None and digest(previous) == intent["predecessor_sha256"], "phase-predecessor-changed")
    template, parameters, revision = control_phase_inputs(store, binding, "accepted-enable")
    require((template, parameters, revision) == (intent["template"], intent["parameters"], intent["source_revision"]), "accepted-phase-inputs-changed")
    disabled_phase(provider, store, binding, "proof-disable")
    budget, owner = cost_intent(store, binding), cost_owner()
    require(budget is not None and budget["source_revision"] == intent["source_revision"], "accepted-budget-source-mismatch")
    accepted = {scope: canonical_scheduling_acceptance(scope) for scope in budget["scopes"]}
    references = {scope: value["reference"] for scope, value in accepted.items()}
    contexts, costs, peers = {}, {}, {}
    subscriptions = None
    alerts = module("scheduling_activation_alerts", "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/observability-receipts.py")
    for scope, selected in accepted.items():
        qualified, original = selected["qualification"], budget["scopes"][scope]
        require(qualified.get("profile") == "scheduling-a2-v1" and qualified.get("target") == binding["target"]
            and qualified.get("scope") == scope and qualified.get("source_revision") == budget["source_revision"]
            and qualified.get("primary_image_digest") == original["maintenance"]["image_digest"]
            and qualified.get("components") == original["packages"], "accepted-release-binding-mismatch")
        common = qualified["evidence"]["observations"]["cost-and-idle"]
        read, _ = owner.archive_materials(common["materials"])
        phases = {phase: read(reference, "phase") for phase, reference in common["phases"].items()}
        expected = {key: qualified[key] for key in ("target", "scope", "source_revision", "primary_image_digest", "components")}
        context = owner.release_context(phases, expected=expected, historical=True)
        scoped = context["binding"]
        actual = authenticate_phase_evidence(provider, store, scoped, phases["proof-disable"])
        require(actual["current_phase"] in ({"proof-disable"} if scope == binding["scope"] else {"proof-disable", "accepted-enable"}), "accepted-current-phase-invalid")
        if actual["current_phase"] == "proof-disable":
            require(disabled_phase(provider, store, scoped, "proof-disable") == phases["proof-disable"], "accepted-disabled-state-changed")
        else:
            peers[scope] = phase_read(store, scoped, "accepted-enable")
        observe_current(provider, scoped)
        packet = read(common["cost"], "cost")
        require(packet.get("intent") == budget and packet.get("notification_topic_arn") == parameters["AlarmTopicArn"], "accepted-original-cost-mismatch")
        alert = read(common["alert"], "alert")
        if subscriptions is None:
            subscriptions = alerts.scheduling_subscriptions(provider, budget["notification_topic_arn"])
        require(alert.get("subscriptions") == subscriptions, "accepted-notification-route-changed")
        contexts[scope], costs[scope] = context, packet
    packet = costs[binding["scope"]]
    require(all(value == packet for value in costs.values()), "accepted-shared-cost-mismatch")
    owner.authenticate_cost_evidence(provider, store, binding, packet,
        components={scope: context["runtime"] for scope, context in contexts.items()}, database=budget["database"],
        notification_topic_arn=budget["notification_topic_arn"], endpoint_id=contexts[binding["scope"]]["endpoint_id"], historical=False)
    for scope, selected in accepted.items():
        priced = packet["recovery_resources"]["snapshots"][scope]
        require(selected["recovery"] == {key: priced[key] for key in ("snapshot", "source_resource_id")},
            "accepted-recovery-cost-identity-mismatch")
    for scope, peer in peers.items():
        require(peer is not None, "accepted-peer-original-required")
        acceptance_companion(store, contexts[scope]["binding"], peer, references, packet, retain=False)
    network_preservation(provider, store, binding)
    current_owned_work(provider, store, binding, previous, database_selections[binding["scope"]], work_selection)
    disabled_phase(provider, store, binding, "proof-disable")
    require(all(canonical_scheduling_acceptance(scope, reference_only=True) == reference for scope, reference in references.items()), "accepted-current-reference-changed")
    acceptance_companion(store, binding, intent, references, packet, retain=True)


def run_proof_effect(provider, store, binding, *, case, native_packet, seed_packet=None,
        database_selections=None, work_selection=None, reconcile=False):
    """Only the two source-owned proof effects, derived from native custody."""
    require(case in {"duplicate", "send-failure"}, "proof-effect-case-invalid")
    phase = "proof-enable" if case == "duplicate" else "fault-on"
    context = proof_capture_context(provider, store, binding, phase)
    purpose = "worker" if case == "duplicate" else "dispatch"
    expected = {key: context[key] for key in ("queue_url", "queue_arn", "native_binding", "required_after")}
    expected["runtime"] = context["runtime"][purpose]
    def admit():
        network_preservation(provider, store, binding)
        checked_connection_pair(provider, store, binding, context["phase_packet"]["intent"]["parameters"], fresh=False)
        if case == "send-failure":
            require(isinstance(database_selections, dict) and set(database_selections) == {binding["scope"]}
                and work_selection is not None, "proof-effect-owned-work-required")
            current_owned_work(provider, store, binding, context["phase_packet"]["intent"],
                database_selections[binding["scope"]], work_selection)
        else:
            # The actual original completed synthetic message is checked by
            # proof_effect_request/reobserve_proof_inputs. No new job payload or
            # waiting reminder can be selected by this route.
            require(database_selections is None and work_selection is None, "proof-effect-unexpected-selection")
    effects = CostAdmittedStore(ProofEffectStore(store.root), provider, binding)
    return proof_effect_once(provider, effects, binding, phase_packet=context["phase_packet"], native_packet=native_packet,
        seed_packet=seed_packet, expected=expected, qualified_path=context["qualified_path"], admit=admit, reconcile=reconcile)


def phase_read(store, binding, phase):
    path = phase_path(store, binding, phase)
    if not path.exists():
        return None
    value = read_json(path)
    require(isinstance(value, dict) and set(value) == {"schema", "target", "scope", "phase", "stack", "mode", "created_at",
        "template", "parameters", "parameter_inputs", "before", "predecessor_sha256", "source_revision", "network_before", "maintenance_selection"}
        and value["schema"] == "deploy/scheduling-phase-intent/v1" and value["target"] == binding["target"]
        and value["scope"] == ("shared" if phase == "network-create" else binding["scope"])
        and value["phase"] == phase and value["stack"] == (binding["network_stack"] if phase == "network-create" else binding["stack"])
        and value["mode"] == ("CREATE" if phase in {"network-create", "scope-create-disabled"} else "UPDATE")
        and isinstance(value["source_revision"], str) and re.fullmatch(r"[a-f0-9]{40}", value["source_revision"]), "phase-intent-invalid")
    ADMISSION.utc(value["created_at"])
    require(isinstance(value["template"], dict) and isinstance(value["parameters"], dict)
        and isinstance(value["parameter_inputs"], list), "phase-intent-invalid")
    require(isinstance(value["network_before"], dict) if phase == "network-create" else value["network_before"] is None, "phase-network-observation-invalid")
    require(value["maintenance_selection"] is None if phase == "network-create" else
        isinstance(value["maintenance_selection"], dict) and scope_maintenance_selection(binding, value["maintenance_selection"]) == value["maintenance_selection"],
        "proof-work-package-selection-mismatch")
    store.path_for("prepare", phase_request(value))
    return value


def phase_state(provider, stack, template, parameters):
    """Read exact template/parameters and resource incarnations, not a status flag."""
    value = FOUNDATION.only(provider("cloudformation", "describe-stacks", StackName=stack), "Stacks", "phase-stack-invalid")
    require(value.get("StackName") == stack and value.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}
        and isinstance(value.get("StackId"), str), "phase-stack-not-stable")
    require(CHANGES.parameter_values(value.get("Parameters")) == parameters, "phase-parameters-mismatch")
    actual = provider("cloudformation", "get-template", StackName=value["StackId"], TemplateStage="Original").get("TemplateBody")
    require(CF.templates_equal(actual, template), "phase-template-mismatch")
    rows = ADMISSION.collection(provider, "cloudformation", "list-stack-resources", "StackResourceSummaries", StackName=value["StackId"])
    require(len(rows) == len(template["Resources"]) and {row.get("LogicalResourceId") for row in rows} == set(template["Resources"]), "phase-resources-mismatch")
    resources = {}
    for row in rows:
        require(row.get("ResourceType") == template["Resources"][row["LogicalResourceId"]]["Type"]
            and row.get("ResourceStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}
            and isinstance(row.get("PhysicalResourceId"), str) and row["PhysicalResourceId"], "phase-resource-state-invalid")
        resources[row["LogicalResourceId"]] = {key: row[key] for key in ("ResourceType", "PhysicalResourceId")}
    return {"stack_id": value["StackId"], "resources": resources}


def phase_completed(provider, store, intent, *, observed=None):
    request = phase_request(intent)
    executed = CHANGES.retained_execution(store, preparation_phase="prepare", preparation_request=request,
        execution_phase="execute", execution_request=request, missing_preparation=lambda: Failure("execution-reservation-orphaned"))
    require(executed is not None, "phase-predecessor-incomplete")
    result = observe(provider, request, executed) if observed is None else observed
    require(result["verdict"] == "completed", "phase-predecessor-incomplete")
    current = phase_state(provider, intent["stack"], intent["template"], intent["parameters"])
    if intent["before"] is not None:
        require(current == intent["before"]["state"], "phase-resource-incarnation-changed")
    return {**result, "state": current}


def validate_phase_evidence(packet, *, target, scope, source_revision, predecessor_sha256):
    """Pure historical lineage check, never fresh provider authorization.

    A canonical collector must obtain this packet through capture_phase and
    bind its digest. A caller-created packet is not an AWS observation.
    """
    require(isinstance(packet, dict) and set(packet) == {"schema", "intent", "preparation", "execution", "terminal", "readback", "captured_at"}
        and packet["schema"] == "deploy/scheduling-phase-evidence/v1", "phase-evidence-invalid")
    intent = packet["intent"]
    require(isinstance(intent, dict) and set(intent) == {"schema", "target", "scope", "phase", "stack", "mode", "created_at",
        "template", "parameters", "parameter_inputs", "before", "predecessor_sha256", "source_revision", "network_before", "maintenance_selection"}
        and intent["schema"] == "deploy/scheduling-phase-intent/v1" and intent["target"] == target and intent["scope"] == scope
        and intent["phase"] in CONTROL_PHASES and intent["source_revision"] == source_revision
        and isinstance(source_revision, str) and re.fullmatch(r"[a-f0-9]{40}", source_revision)
        and intent["predecessor_sha256"] == predecessor_sha256, "phase-evidence-intent-mismatch")
    phase = intent["phase"]
    require(intent["maintenance_selection"] is None if phase == "network-create" else
        isinstance(intent["maintenance_selection"], dict) and scope_maintenance_selection({"scope": scope}, intent["maintenance_selection"]) == intent["maintenance_selection"],
        "proof-work-package-selection-mismatch")
    require((scope == "shared") == (phase == "network-create") and intent["mode"] == ("CREATE" if phase in {"network-create", "scope-create-disabled"} else "UPDATE")
        and isinstance(intent["stack"], str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,127}", intent["stack"])
        and (predecessor_sha256 is None if phase == "network-create" else isinstance(predecessor_sha256, str) and re.fullmatch(r"[a-f0-9]{64}", predecessor_sha256)), "phase-evidence-intent-mismatch")
    request = phase_request(intent)
    preparation = Store.validate_record("prepare", request, packet["preparation"], validate_time=lambda value: ADMISSION.utc(value.replace("+00:00", "Z")))
    execution = Store.validate_record("execute", request, packet["execution"], validate_time=lambda value: ADMISSION.utc(value.replace("+00:00", "Z")))
    require(preparation["operation_id"] != execution["operation_id"], "phase-evidence-reservation-mismatch")
    terminal, state = packet["terminal"], packet["readback"]
    require(isinstance(terminal, dict) and set(terminal) == {"EventId", "StackId", "LogicalResourceId", "PhysicalResourceId", "ResourceType", "ResourceStatus", "ClientRequestToken", "Timestamp"}
        and isinstance(terminal["EventId"], str) and terminal["EventId"]
        and terminal["ResourceType"] == "AWS::CloudFormation::Stack" and terminal["LogicalResourceId"] == intent["stack"]
        and terminal["ResourceStatus"] == intent["mode"] + "_COMPLETE" and terminal["ClientRequestToken"] == execution["operation_id"], "phase-evidence-terminal-mismatch")
    require(isinstance(state, dict) and set(state) == {"stack_id", "resources"} and isinstance(state["stack_id"], str)
        and state["stack_id"] == terminal["StackId"] == terminal["PhysicalResourceId"]
        and isinstance(state["resources"], dict) and isinstance(intent["template"], dict)
        and isinstance(intent["template"].get("Resources"), dict)
        and set(state["resources"]) == set(intent["template"]["Resources"]), "phase-evidence-readback-mismatch")
    for logical, resource_state in state["resources"].items():
        require(isinstance(resource_state, dict) and set(resource_state) == {"ResourceType", "PhysicalResourceId"}
            and resource_state["ResourceType"] == intent["template"]["Resources"][logical]["Type"]
            and isinstance(resource_state["PhysicalResourceId"], str) and resource_state["PhysicalResourceId"], "phase-evidence-readback-mismatch")
    require(isinstance(intent["parameters"], dict) and isinstance(intent["parameter_inputs"], list), "phase-evidence-parameters-invalid")
    controls = CONTROL_PHASES[phase][1]
    if controls is not None:
        require(tuple(intent["parameters"].get(key) for key in ("TickEnabled", "WorkerEnabled", "DenyDispatcherSend")) == controls, "phase-evidence-controls-mismatch")
    if intent["mode"] == "UPDATE":
        require(isinstance(intent["before"], dict) and set(intent["before"]) == {"parameters", "state"}
            and intent["before"]["state"] == state, "phase-evidence-incarnation-mismatch")
        overrides = ADMISSION.update_overrides(intent["before"]["parameters"], intent["parameters"],
            controls_only=phase not in {"fault-on", "fault-off"}, fault_only=phase in {"fault-on", "fault-off"})
        require(bool(overrides) and intent["parameter_inputs"] == CHANGES.update_parameter_inputs(intent["before"]["parameters"], overrides), "phase-evidence-parameters-invalid")
    else:
        require(intent["before"] is None and intent["parameter_inputs"] == [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(intent["parameters"].items())], "phase-evidence-parameters-invalid")
    times = [ADMISSION.utc(value.replace("+00:00", "Z")) for value in (intent["created_at"], preparation["reserved_at"], execution["reserved_at"], terminal["Timestamp"], packet["captured_at"])]
    require(times == sorted(times), "phase-evidence-time-order-invalid")
    return {"phase": phase, "target": target, "scope": scope, "source_revision": source_revision, "stack": intent["stack"],
        "intent_sha256": digest(intent), "packet_sha256": digest(packet), "completed_at": terminal["Timestamp"], "state": state,
        "parameters": intent["parameters"]}


def capture_phase(provider, store, binding, phase, *, completed=None):
    """Capture once while that original completed phase is still current."""
    intent = phase_read(store, binding, phase)
    require(intent is not None, "phase-intent-required")
    path = phase_path(store, binding, phase).with_suffix(".evidence.json")
    RESERVATIONS.no_symlinks(path)
    if path.exists():
        packet = read_json(path)
        require(packet.get("intent") == intent, "phase-evidence-retained-intent-mismatch")
        validate_phase_evidence(packet, target=binding["target"], scope=intent["scope"], source_revision=intent["source_revision"], predecessor_sha256=intent["predecessor_sha256"])
        return packet
    current = phase_completed(provider, store, intent) if completed is None else completed
    request = phase_request(intent)
    preparation, execution = store.read("prepare", request), store.read("execute", request)
    rows = ADMISSION.collection(provider, "cloudformation", "describe-stack-events", "StackEvents", StackName=current["state"]["stack_id"])
    selected = CHANGES.execution_events({"StackEvents": rows}, execution["operation_id"], current["state"]["stack_id"])
    terminal = [row for row in selected if row.get("ResourceStatus") == intent["mode"] + "_COMPLETE"]
    require(len(terminal) == 1, "phase-terminal-not-unique")
    fields = ("EventId", "StackId", "LogicalResourceId", "PhysicalResourceId", "ResourceType", "ResourceStatus", "ClientRequestToken", "Timestamp")
    packet = {"schema": "deploy/scheduling-phase-evidence/v1", "intent": intent, "preparation": preparation, "execution": execution,
        "terminal": {key: terminal[0].get(key) for key in fields}, "readback": current["state"], "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
    validate_phase_evidence(packet, target=binding["target"], scope=intent["scope"], source_revision=intent["source_revision"], predecessor_sha256=intent["predecessor_sha256"])
    require(RESERVATIONS.write_exclusive(path, packet), "phase-evidence-retention-uncertain")
    return packet


def authenticate_phase_evidence(provider, store, binding, packet):
    """Reobserve original history and current incarnation, not old controls.

    The canonical live collector separately requires its selected final controls.
    A later owned toggle cannot erase the original operation's evidence, and an
    old captured success cannot authorize a replaced or currently failed stack.
    """
    require(isinstance(packet, dict) and isinstance(packet.get("intent"), dict), "phase-evidence-invalid")
    original = packet["intent"]
    phase = original.get("phase")
    require(phase in CONTROL_PHASES and phase_read(store, binding, phase) == original, "phase-evidence-retained-intent-mismatch")
    retained = capture_phase(provider, store, binding, phase)
    require(packet == retained, "phase-evidence-retained-packet-mismatch")
    checked = validate_phase_evidence(packet, target=binding["target"], scope=original["scope"], source_revision=original["source_revision"], predecessor_sha256=original["predecessor_sha256"])
    current = original
    if phase != "network-create":
        executed = []
        for candidate in list(CONTROL_PHASES)[1:]:
            intent = phase_read(store, binding, candidate)
            if intent is not None and store.read("execute", phase_request(intent)) is not None:
                executed.append(intent)
        require(bool(executed), "phase-evidence-current-operation-missing")
        current = executed[-1]
    require(current["source_revision"] == original["source_revision"], "phase-evidence-current-source-mismatch")
    current_state = phase_completed(provider, store, current)["state"]
    require(current_state == packet["readback"], "phase-evidence-incarnation-mismatch")
    rows = ADMISSION.collection(provider, "cloudformation", "describe-stack-events", "StackEvents", StackName=current_state["stack_id"])
    events = CHANGES.execution_events({"StackEvents": rows}, packet["execution"]["operation_id"], current_state["stack_id"])
    selected = [{key: event.get(key) for key in packet["terminal"]} for event in events
        if event.get("ResourceStatus") == original["mode"] + "_COMPLETE"]
    require(selected == [packet["terminal"]], "phase-evidence-original-terminal-unconfirmed")
    return {**checked, "current_phase": current["phase"], "current_intent_sha256": digest(current)}


def network_policy_value(value, parameters):
    """Resolve only the network template's existing Ref/string-Sub subset."""
    if isinstance(value, list):
        return [network_policy_value(item, parameters) for item in value]
    if isinstance(value, dict):
        if set(value) == {"Ref"}:
            require(value["Ref"] in parameters, "network-policy-reference-unowned")
            return parameters[value["Ref"]]
        if set(value) == {"Fn::Sub"}:
            text = value["Fn::Sub"]
            require(isinstance(text, str), "network-policy-substitution-unowned")
            def replace(match):
                require(match[1] in parameters, "network-policy-reference-unowned")
                return parameters[match[1]]
            return re.sub(r"\$\{([^}]+)\}", replace, text)
        require(not any(key.startswith("Fn::") for key in value), "network-policy-expression-unowned")
        return {key: network_policy_value(item, parameters) for key, item in value.items()}
    return value


def network_rules(group, key, account):
    """Compare actual owned group permissions, not just its identifier."""
    rows = group.get(key)
    require(isinstance(rows, list), "network-group-rules-invalid")
    result = []
    for row in rows:
        require(isinstance(row, dict) and not row.get("Ipv6Ranges") and not row.get("PrefixListIds")
            and row.get("IpProtocol") in {"tcp", "udp"} and type(row.get("FromPort")) is int and type(row.get("ToPort")) is int,
            "network-group-rule-unowned")
        for peer in row.get("UserIdGroupPairs", []):
            require(set(peer) <= {"GroupId", "UserId"} and peer.get("UserId") == account and isinstance(peer.get("GroupId"), str), "network-group-peer-unowned")
            result.append((row["IpProtocol"], row["FromPort"], row["ToPort"], "group", peer["GroupId"]))
        for peer in row.get("IpRanges", []):
            require(set(peer) == {"CidrIp"}, "network-group-peer-unowned")
            result.append((row["IpProtocol"], row["FromPort"], row["ToPort"], "cidr", peer["CidrIp"]))
    require(len(result) == len(set(result)), "network-group-rules-ambiguous")
    return set(result)


def created_network(provider, store, binding, original):
    """Derive new-resource exclusions from original completed owner operations.

    No caller-supplied ARN/group allowlist can exempt an unknown VPC consumer.
    The source template, actual endpoint policy, groups, functions and queue
    permissions must all agree before the legacy snapshot is compared.
    """
    require(original["phase"] == "network-create", "network-original-intent-required")
    parameters = original["parameters"]
    state = phase_completed(provider, store, original)["state"]
    ids = state["resources"]
    require(set(ids) == {"SchedulingSqsEndpoint", "SchedulingEndpointSecurityGroup"}, "network-resources-unowned")
    endpoint_id, group_id = ids["SchedulingSqsEndpoint"]["PhysicalResourceId"], ids["SchedulingEndpointSecurityGroup"]["PhysicalResourceId"]
    rows = provider("ec2", "describe-vpc-endpoints", VpcEndpointIds=[endpoint_id]).get("VpcEndpoints")
    require(isinstance(rows, list) and len(rows) == 1, "network-endpoint-unavailable")
    endpoint = rows[0]
    account, region = binding["provider"]["account_id"], binding["provider"]["region"]
    require(endpoint.get("VpcEndpointId") == endpoint_id and endpoint.get("VpcId") == parameters["VpcId"]
        and endpoint.get("ServiceName") == "com.amazonaws." + region + ".sqs" and endpoint.get("VpcEndpointType") == "Interface"
        and endpoint.get("State") == "available" and endpoint.get("PrivateDnsEnabled") is True
        and set(endpoint.get("SubnetIds", [])) == set(parameters["PrivateSubnetIds"].split(","))
        and [row.get("GroupId") for row in endpoint.get("Groups", [])] == [group_id], "network-endpoint-mismatch")
    expected_policy = network_policy_value(original["template"]["Resources"]["SchedulingSqsEndpoint"]["Properties"]["PolicyDocument"],
        {**parameters, "AWS::Region": region, "AWS::AccountId": account, "AWS::Partition": "aws"})
    require(CF.templates_equal(json.loads(endpoint["PolicyDocument"]), expected_policy), "network-endpoint-policy-mismatch")
    created = {"endpoint": endpoint, "endpoint_group": group_id, "functions": {}, "queues": {}, "database_ingress": []}
    endpoint_ingress = {("tcp", 443, 443, "group", parameters[key]) for key in ("LegacyWorkerSecurityGroupId", "LegacyRelaySecurityGroupId")}
    scopes = CF.template((ROOT / binding["template"]).read_text())["Mappings"]["Scopes"]
    for scope in scopes:
        selected = load_binding(binding["target"], scope)
        known = [phase_read(store, selected, phase) for phase in CONTROL_PHASES if phase != "network-create"]
        completed = [intent for intent in known if intent is not None and store.read("execute", phase_request(intent)) is not None]
        if not completed:
            continue
        current = completed[-1]
        resources = phase_completed(provider, store, current)["state"]["resources"]
        actual = current["parameters"]
        require(actual["VpcId"] == parameters["VpcId"] and actual["EndpointSecurityGroupId"] == group_id
            and set(actual["PrivateSubnetIds"].split(",")) == set(parameters["PrivateSubnetIds"].split(",")), "network-scope-placement-mismatch")
        scope_group = resources["SchedulingSecurityGroup"]["PhysicalResourceId"]
        groups = provider("ec2", "describe-security-groups", GroupIds=[scope_group]).get("SecurityGroups")
        require(isinstance(groups, list) and len(groups) == 1 and groups[0].get("GroupId") == scope_group and groups[0].get("VpcId") == parameters["VpcId"], "network-scope-group-mismatch")
        require(network_rules(groups[0], "IpPermissions", account) == set()
            and network_rules(groups[0], "IpPermissionsEgress", account) == {
                ("udp", 53, 53, "cidr", actual["VpcCidr"]), ("tcp", 53, 53, "cidr", actual["VpcCidr"]),
                ("tcp", 443, 443, "group", group_id), ("tcp", 5432, 5432, "group", actual["DatabaseSecurityGroupId"])}, "network-scope-group-rules-mismatch")
        endpoint_ingress.add(("tcp", 443, 443, "group", scope_group))
        created["database_ingress"].append({"target": actual["DatabaseSecurityGroupId"], "source": scope_group})
        observed = outputs(provider, selected["stack"], {"DispatchVersionArn", "WorkerVersionArn", "JobQueueArn", "DeadLetterQueueArn"})
        for queue_name in ("JobQueue", "DeadLetterQueue"):
            queue_arn = observed[queue_name + "Arn"]
            require(isinstance(queue_arn, str) and re.fullmatch(r"arn:aws:sqs:" + re.escape(region + ":" + account)
                + r":[A-Za-z0-9_-]+", queue_arn), "network-created-queue-mismatch")
            queue_url = f"https://sqs.{region}.amazonaws.com/{account}/" + queue_arn.rsplit(":", 1)[1]
            require(resources[queue_name]["PhysicalResourceId"] == queue_url, "network-created-queue-mismatch")
            created["queues"][queue_arn] = queue_url
        for purpose in ("dispatch", "worker"):
            arn = observed[purpose.title() + "VersionArn"]
            require(re.fullmatch(r"arn:aws:lambda:" + re.escape(region + ":" + account) + r":function:kc-" + re.escape(scope) + r"-schedule-" + purpose + r":[1-9][0-9]*", arn), "network-function-version-invalid")
            function = provider("lambda", "get-function", FunctionName=arn)
            configuration = function.get("Configuration", {})
            role_arn = f"arn:aws:iam::{account}:role/" + resources[purpose.title() + "Role"]["PhysicalResourceId"]
            require(configuration.get("FunctionArn") == arn and configuration.get("Role") == role_arn
                and configuration.get("State") == "Active" and configuration.get("LastUpdateStatus") == "Successful"
                and function.get("Code", {}).get("ResolvedImageUri") == actual[purpose.title() + "ImageUri"], "network-function-mismatch")
            _identity, grants = ADMISSION.role(provider, role_arn, account)
            expected_grants = {("sqs:sendmessage", observed[key]) for key in ("JobQueueArn", "DeadLetterQueueArn")} if purpose == "dispatch" else {
                (action, observed["JobQueueArn"]) for action in ("sqs:receivemessage", "sqs:deletemessage", "sqs:getqueueattributes", "sqs:changemessagevisibility")}
            require(grants == expected_grants, "network-function-queue-permissions-mismatch")
            created["functions"][arn.rsplit(":", 1)[0]] = {"role": role_arn, "group": scope_group, "subnets": actual["PrivateSubnetIds"].split(",")}
    groups = provider("ec2", "describe-security-groups", GroupIds=[group_id]).get("SecurityGroups")
    require(isinstance(groups, list) and len(groups) == 1 and groups[0].get("GroupId") == group_id and groups[0].get("VpcId") == parameters["VpcId"], "network-endpoint-group-mismatch")
    require(network_rules(groups[0], "IpPermissions", account) == endpoint_ingress
        and network_rules(groups[0], "IpPermissionsEgress", account) == {("tcp", 443, 443, "cidr", "127.0.0.1/32")}, "network-endpoint-group-rules-mismatch")
    return created


def network_preservation(provider, store, binding):
    original = phase_read(store, binding, "network-create")
    require(original is not None and isinstance(original["network_before"], dict), "network-original-observation-required")
    created = created_network(provider, store, binding, original)
    current = ADMISSION.network_facts(provider, binding, original["parameters"], created=created)
    before = original["network_before"]
    require(current["preservation_sha256"] == before["preservation_sha256"]
        and current["snapshot"] == before["snapshot"], "network-legacy-preservation-mismatch")
    return {key: value for key, value in current.items() if key != "snapshot"}


def phase_control(provider, store, binding, phase, *, action, build_inputs, admit, maintenance_selection=None):
    """Original intent is selected before reading any mutable candidate inputs.

    Public mutation admission remains closed until the fixed DB, network and
    cost owners are joined. Internal callbacks are policies of this owner, not
    caller supplied proof documents or an alternate provider interface.
    """
    require(action in {"prepare", "execute", "observe", "retain"} and (action != "retain" or phase == "network-create"), "phase-action-invalid")
    intent = phase_read(store, binding, phase)
    if intent is not None:
        request = phase_request(intent)
        executed = CHANGES.retained_execution(store, preparation_phase="prepare", preparation_request=request,
            execution_phase="execute", execution_request=request, missing_preparation=lambda: Failure("execution-reservation-orphaned"))
        if executed is not None:
            result = observe(provider, request, executed)
            if result["verdict"] == "completed":
                completed = phase_completed(provider, store, intent, observed=result)
                capture_phase(provider, store, binding, phase, completed=completed)
            return result
    else:
        require(action in {"prepare", "retain"}, "phase-intent-required")
        predecessor, controls = CONTROL_PHASES[phase]
        previous = None if predecessor is None else phase_read(store, binding, predecessor)
        require(predecessor is None or previous is not None, "phase-predecessor-required")
        if previous is not None:
            phase_completed(provider, store, previous)
        template, parameters, source_revision = build_inputs()
        require(isinstance(source_revision, str) and re.fullmatch(r"[a-f0-9]{40}", source_revision), "phase-source-invalid")
        if controls is not None:
            require(tuple(parameters.get(key) for key in ("TickEnabled", "WorkerEnabled", "DenyDispatcherSend")) == controls, "phase-controls-mismatch")
        mode = "CREATE" if phase in {"network-create", "scope-create-disabled"} else "UPDATE"
        before = None
        if mode == "UPDATE":
            require(previous["source_revision"] == source_revision and CF.templates_equal(previous["template"], template), "phase-source-transition-unowned")
            actual = previous["parameters"]
            overrides = ADMISSION.update_overrides(actual, parameters, controls_only=phase not in {"fault-on", "fault-off"}, fault_only=phase in {"fault-on", "fault-off"})
            parameter_inputs = CHANGES.update_parameter_inputs(actual, overrides)
            require(parameter_inputs is not None and bool(overrides), "phase-no-change")
            before = {"parameters": actual, "state": phase_state(provider, previous["stack"], template, actual)}
        else:
            parameter_inputs = [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())]
        intent = {"schema": "deploy/scheduling-phase-intent/v1", "target": binding["target"],
            "scope": "shared" if phase == "network-create" else binding["scope"], "phase": phase,
            "stack": binding["network_stack"] if phase == "network-create" else binding["stack"], "mode": mode,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "template": template,
            "parameters": parameters, "parameter_inputs": parameter_inputs, "before": before,
            "predecessor_sha256": None if previous is None else digest(previous), "source_revision": source_revision,
            "network_before": ADMISSION.network_facts(provider, binding, parameters) if phase == "network-create" else None,
            "maintenance_selection": None if phase == "network-create" else
                scope_maintenance_selection(binding, maintenance_selection) if phase == "scope-create-disabled" else previous["maintenance_selection"]}
        require(RESERVATIONS.write_exclusive(phase_path(store, binding, phase), intent), "phase-intent-retention-uncertain")
    if action == "retain":
        return {"verdict": "retained", "code": "initial-network-intent-retained", "intent_sha256": digest(intent), "created_at": intent["created_at"]}
    def fresh_admission():
        predecessor = CONTROL_PHASES[phase][0]
        if predecessor is not None:
            previous = phase_read(store, binding, predecessor)
            require(previous is not None and digest(previous) == intent["predecessor_sha256"], "phase-predecessor-changed")
            phase_completed(provider, store, previous)
        if intent["mode"] == "CREATE":
            prepared = store.read("prepare", phase_request(intent))
            try:
                observed = FOUNDATION.only(provider("cloudformation", "describe-stacks", StackName=intent["stack"]), "Stacks", "phase-stack-invalid")
            except Failure as failure:
                require(failure.code == "aws-resource-missing", "phase-stack-absence-unproven")
            else:
                # A CREATE change set creates its own REVIEW_IN_PROGRESS shell.
                # Only the exact retained preparation can own that shell.
                require(prepared is not None and observed.get("StackName") == intent["stack"]
                    and observed.get("StackStatus") == "REVIEW_IN_PROGRESS", "phase-stack-already-exists")
                change = provider("cloudformation", "describe-change-set", StackName=intent["stack"], ChangeSetName=phase_request(intent)["change_set"])
                require(change.get("Description") == prepared["operation_id"] and change.get("StackId") == observed.get("StackId"), "phase-stack-lineage-mismatch")
        else:
            require(phase_state(provider, intent["stack"], intent["template"], intent["before"]["parameters"]) == intent["before"]["state"], "phase-prior-state-changed")
        admit(intent)
    result = control(provider, store, request=phase_request(intent), template=intent["template"], parameters=intent["parameters"],
        parameter_inputs=intent["parameter_inputs"], mode=intent["mode"], action=action, target=binding["target"], admit=fresh_admission)
    if result["verdict"] == "completed":
        completed = phase_completed(provider, store, intent, observed=result)
        capture_phase(provider, store, binding, phase, completed=completed)
    return result


def observe_current(provider, binding):
    """Observe actual qualified wiring; never claim business execution or acceptance."""
    response = provider("cloudformation", "describe-stacks", StackName=binding["stack"])
    stack = FOUNDATION.only(response, "Stacks", "stack-observation-invalid")
    values = FOUNDATION.stack_outputs(response, {"DispatchVersionArn", "WorkerVersionArn", "JobQueueUrl", "JobQueueArn", "DeadLetterQueueArn", "WorkerMappingId"})
    parameters = CHANGES.parameter_values(stack.get("Parameters"))
    require(isinstance(parameters, dict) and parameters.get("Scope") == binding["scope"], "scope-parameters-invalid")
    source = CF.template((ROOT / binding["template"]).read_text())
    for purpose in ("Dispatch", "Worker"):
        arn = values[purpose + "VersionArn"]
        prefix = f"arn:aws:lambda:{binding['provider']['region']}:{binding['provider']['account_id']}:function:kc-{binding['scope']}-schedule-{purpose.lower()}:"
        require(arn.startswith(prefix) and re.fullmatch(r"[1-9][0-9]*", arn[len(prefix):]), "immutable-function-version-required")
        value = provider("lambda", "get-function", FunctionName=arn)
        configuration = value.get("Configuration", {})
        require(configuration.get("FunctionArn") == arn and configuration.get("Version") == arn.rsplit(":", 1)[1]
                and configuration.get("State") == "Active" and configuration.get("LastUpdateStatus") == "Successful", "function-not-ready")
        require(value.get("Code", {}).get("ResolvedImageUri") == parameters.get(purpose + "ImageUri"), "function-image-mismatch")
        environment = configuration.get("Environment", {}).get("Variables", {})
        require(environment.get("PLATFORM_SOURCE_COMMIT_SHA") == parameters.get("SourceRevision")
                and environment.get("SCHEDULING_QUEUE_ARN") == values["JobQueueArn"] and environment.get("SCHEDULING_QUEUE_URL") == values["JobQueueUrl"], "function-configuration-mismatch")
        require(configuration.get("Timeout") == 60 and configuration.get("MemorySize") == 512
                and configuration.get("Architectures") == ["x86_64"], "function-budget-mismatch")
        require(value.get("Concurrency", {}).get("ReservedConcurrentExecutions")
                == source["Resources"][purpose + "Function"]["Properties"]["ReservedConcurrentExecutions"], "function-concurrency-mismatch")
    mapping = provider("lambda", "get-event-source-mapping", UUID=values["WorkerMappingId"])
    require(mapping.get("FunctionArn") == values["WorkerVersionArn"] and mapping.get("EventSourceArn") == values["JobQueueArn"]
            and mapping.get("BatchSize") == 1 and mapping.get("FunctionResponseTypes") == ["ReportBatchItemFailures"]
            and mapping.get("State") == ("Enabled" if parameters.get("WorkerEnabled") == "true" else "Disabled"), "worker-mapping-mismatch")
    tick = provider("scheduler", "get-schedule", Name="due-pass", GroupName=binding["target"] + "-" + binding["scope"])
    tick_input = source["Resources"]["FixedTick"]["Properties"]["Target"]["Input"]
    require(tick.get("Target", {}).get("Arn") == values["DispatchVersionArn"]
            and tick.get("Target", {}).get("Input") == tick_input
            and tick.get("State") == ("ENABLED" if parameters.get("TickEnabled") == "true" else "DISABLED")
            and tick.get("ScheduleExpression") == "rate(1 minute)" and tick.get("ScheduleExpressionTimezone") == "UTC"
            and tick.get("FlexibleTimeWindow") == {"Mode": "OFF"}, "tick-mapping-mismatch")
    attributes = provider("sqs", "get-queue-attributes", QueueUrl=values["JobQueueUrl"], AttributeNames=["QueueArn", "VisibilityTimeout", "RedrivePolicy"]).get("Attributes", {})
    require(attributes.get("QueueArn") == values["JobQueueArn"] and attributes.get("VisibilityTimeout") == "360", "queue-configuration-mismatch")
    try:
        redrive = json.loads(attributes.get("RedrivePolicy", ""))
    except ValueError:
        raise Failure("queue-redrive-invalid") from None
    require(redrive.get("deadLetterTargetArn") == values["DeadLetterQueueArn"] and str(redrive.get("maxReceiveCount")) == "5", "queue-redrive-mismatch")
    asynchronous = provider("lambda", "get-function-event-invoke-config", FunctionName=values["DispatchVersionArn"])
    require(asynchronous.get("MaximumRetryAttempts") == 0 and asynchronous.get("MaximumEventAgeInSeconds") == 60
            and asynchronous.get("DestinationConfig", {}).get("OnFailure", {}).get("Destination") == values["DeadLetterQueueArn"], "dispatch-failure-route-mismatch")
    return {"verdict": "observed", "code": "provider-wiring-self-consistency-observed"}


def trusted_admission_required():
    raise Failure("trusted-admission-required")


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.error = lambda _message: (_ for _ in ()).throw(Failure("arguments-invalid"))
    parser.add_argument("--target", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--operation", choices=["prepare-cost", "capture-cost", "retain-network-intent", "prepare", "execute", "observe", "observe-current", "inspect-network", "inspect-preservation", "inspect-disabled", "run-preflight", "reconcile-preflight", "assemble-runtime-proof", "capture-runtime-window", "capture-automatic-trigger", "capture-native-proof", "capture-native-preparation", "run-proof-effect", "reconcile-proof-effect"], required=True)
    parser.add_argument("--phase", choices=list(CONTROL_PHASES))
    parser.add_argument("--preflight-slot", choices=list(PreflightStore.slots))
    parser.add_argument("--purpose", choices=["dispatch", "worker"])
    parser.add_argument("--dispatch-receipt")
    parser.add_argument("--worker-receipt")
    parser.add_argument("--cost-selections")
    parser.add_argument("--database-selections")
    parser.add_argument("--owned-work")
    parser.add_argument("--runtime-selection")
    parser.add_argument("--qualified-path")
    parser.add_argument("--native-selection")
    parser.add_argument("--started-at")
    parser.add_argument("--ended-at")
    parser.add_argument("--case", choices=("duplicate", "send-failure"))
    parser.add_argument("--native-packet")
    parser.add_argument("--seed-packet")
    parser.add_argument("--expires-at")
    parser.add_argument("--json", action="store_true")
    try:
        args = parser.parse_args(argv)
        binding = load_binding(args.target, args.scope)
        # Even disabled resources can change shared DNS, IAM, and paid capacity.
        # No prepare/execute path is admitted by an untrusted boolean or JSON.
        cleanup = args.phase in {"missed-tick-disable", "fault-disable", "fault-off", "proof-disable"}
        bounded = args.phase in {"proof-enable", "missed-tick-recovery-enable", "fault-on", "failure-recovery-enable"}
        accepted = args.phase == "accepted-enable"
        if args.operation in {"prepare", "execute"} and not cleanup:
            if (args.phase != "network-create" and args.database_selections is None) or ((bounded or accepted) and args.owned_work is None) or (not bounded and not accepted and args.phase not in {"network-create", "scope-create-disabled"}):
                trusted_admission_required()
        provider = Provider(binding)
        if args.operation == "inspect-network":
            parameters = network_parameters(provider, binding)
            observation = ADMISSION.network_facts(provider, binding, parameters)
            # Actual policies/task configuration remain in memory. The public
            # report contains only bounded identities/counts and a fingerprint.
            result = {"code": "network-compatibility-observed", **{key: value for key, value in observation.items() if key not in {"schema", "snapshot"}}}
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", **result}, sort_keys=True))
            return 0
        if args.operation == "inspect-disabled":
            require(args.dispatch_receipt and args.worker_receipt, "package-receipts-required")
            receipts = qualified_pair(binding, {"dispatch": args.dispatch_receipt, "worker": args.worker_receipt})
            parameters = scope_parameters(provider, binding, receipts, False, False)
            template = rendered_template(binding, "scope", parameters)
            observation = ADMISSION.disabled_facts(provider, binding, parameters, template,
                normalize=CF.template, parameter_values=CHANGES.parameter_values)
            observe_current(provider, binding)
            result = {"code": "disabled-provider-state-observed", **{key: value for key, value in observation.items() if key != "schema"}}
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", **result}, sort_keys=True))
            return 0
        if args.operation == "observe-current":
            result = observe_current(provider, binding)
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", **result}, sort_keys=True))
            return 0
        git_dir = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--absolute-git-dir"], check=True, text=True, capture_output=True).stdout.strip()
        store = Store(Path(git_dir) / "scheduling-control")
        if args.operation == "capture-cost":
            require(args.started_at is not None and args.ended_at is not None, "cost-capture-window-required")
            budget, owner = cost_intent(store, binding), cost_owner()
            require(budget is not None, "cost-intent-required")
            components = {scope: proof_capture_context(provider, store, load_binding(binding["target"], scope), "scope-create-disabled")["runtime"]
                for scope in budget["scopes"]}
            network = capture_phase(provider, store, binding, "network-create")
            authenticate_phase_evidence(provider, store, binding, network)
            endpoint = network["readback"]["resources"]["SchedulingSqsEndpoint"]["PhysicalResourceId"]
            try:
                packet = owner.collect_cost_evidence(provider, store, binding, components=components, database=budget["database"],
                    notification_topic_arn=budget["notification_topic_arn"], endpoint_id=endpoint, started_at=args.started_at, ended_at=args.ended_at)
            except owner.ProofFailure as failure:
                raise Failure(failure.code) from None
            print(json.dumps(packet, sort_keys=True, allow_nan=False))
            return 0
        if args.operation in {"run-proof-effect", "reconcile-proof-effect"}:
            require(args.case is not None and args.native_packet is not None, "proof-effect-selection-required")
            packet = run_proof_effect(provider, store, binding, case=args.case, native_packet=read_proof_data(args.native_packet),
                seed_packet=read_proof_data(args.seed_packet) if args.seed_packet else None,
                database_selections=read_json(args.database_selections) if args.database_selections else None,
                work_selection=read_proof_data(args.owned_work) if args.owned_work else None, reconcile=args.operation == "reconcile-proof-effect")
            print(json.dumps(packet, sort_keys=True, allow_nan=False))
            return 0
        if args.operation in {"capture-runtime-window", "capture-automatic-trigger", "capture-native-proof", "capture-native-preparation"}:
            require(args.phase is not None, "proof-capture-phase-required")
            owner = cost_owner()
            try:
                if args.operation.startswith("capture-native-"):
                    require(args.native_selection is not None, "proof-capture-native-selection-required")
                    packet = capture_native_proof(provider, store, binding, args.phase, read_json(args.native_selection),
                        preparation=args.operation == "capture-native-preparation")
                else:
                    require(args.started_at is not None and args.ended_at is not None, "proof-capture-window-required")
                    context = proof_capture_context(provider, store, binding, args.phase)
                    purpose = "dispatch" if args.operation == "capture-automatic-trigger" else args.purpose
                    require(purpose in context["runtime"], "proof-capture-purpose-required")
                    packet = owner.capture_runtime_window(provider, expected=context["runtime"][purpose], started_at=args.started_at, ended_at=args.ended_at)
                    if args.operation == "capture-automatic-trigger":
                        rows = owner.validate_runtime_window(packet, expected=context["runtime"]["dispatch"])
                        packet = owner.capture_automatic_trigger(provider, expected=context["trigger"], started_at=args.started_at, ended_at=args.ended_at, dispatches=rows)
            except owner.ProofFailure as failure:
                raise Failure(failure.code) from None
            print(json.dumps(packet, sort_keys=True, allow_nan=False))
            return 0
        if args.operation == "assemble-runtime-proof":
            require(args.dispatch_receipt and args.worker_receipt and args.qualified_path and args.runtime_selection, "runtime-proof-selection-required")
            owner = cost_owner()
            try:
                evidence = owner.assemble_acceptance_evidence(provider, store, binding,
                    package_paths={"dispatch": args.dispatch_receipt, "worker": args.worker_receipt},
                    qualified_path=args.qualified_path, selection=read_json(args.runtime_selection))
            except owner.ProofFailure as failure:
                raise Failure(failure.code) from None
            print(json.dumps(evidence, sort_keys=True, allow_nan=False))
            return 0
        if args.operation == "prepare-cost":
            require(args.cost_selections is not None and args.expires_at is not None, "cost-selection-required")
            value = prepare_cost_intent(provider, store, binding, read_json(args.cost_selections), expires_at=args.expires_at)
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", "verdict": "retained", "code": "cost-intent-retained",
                "intent_sha256": digest(value), "started_at": value["started_at"], "expires_at": value["expires_at"],
                "projected_usd": value["initial_projection"]["projected_usd"], "qualification": "original-budget-not-provider-authorization"}, sort_keys=True))
            return 0
        if args.operation == "retain-network-intent":
            result = phase_control(provider, store, binding, "network-create", action="retain",
                build_inputs=lambda: initial_phase_inputs(provider, store, binding, "network-create",
                    {"dispatch": args.dispatch_receipt, "worker": args.worker_receipt}), admit=lambda _intent: trusted_admission_required())
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", **result}, sort_keys=True))
            return 0
        if args.operation == "inspect-preservation":
            result = network_preservation(provider, store, binding)
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", "code": "network-preservation-observed",
                **{key: value for key, value in result.items() if key != "schema"}}, sort_keys=True))
            return 0
        if args.operation == "reconcile-preflight":
            require(args.preflight_slot is not None and args.purpose is not None, "preflight-selection-required")
            preflights = PreflightStore(store.root)
            # Resolve the fixed original record, not mutable current function or
            # package inputs. This path can only read the original AWS logs.
            path = store.root / (args.scope + "-" + args.preflight_slot + "-" + args.purpose + "-invoke.json")
            RESERVATIONS.no_symlinks(path)
            original = read_json(path)
            request = original["request"]
            require(request.get("scope") == args.scope and request.get("slot") == args.preflight_slot
                and request.get("expected", {}).get("purpose") == args.purpose, "preflight-selection-mismatch")
            result = preflight_once(provider, preflights, request, admit=trusted_admission_required, reconcile=True, fresh=False)
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", "verdict": "observed", "code": "original-preflight-reconciled",
                "operation_id": result["reservation"]["operation_id"], "request_sha256": result["request_sha256"],
                "evidence_sha256": digest(result), "qualification": "historical-runtime-connection-only"}, sort_keys=True))
            return 0
        if args.operation == "run-preflight":
            require(args.preflight_slot in PreflightStore.slots and args.purpose is not None, "preflight-selection-not-admitted")
            phase = "proof-disable" if args.preflight_slot == "acceptance" else "scope-create-disabled"
            intent = phase_read(store, binding, phase)
            require(intent is not None, "phase-intent-required")
            expected = preflight_expected(provider, binding, intent["parameters"], args.purpose)
            preflights = CostAdmittedStore(PreflightStore(store.root), provider, binding)
            packet = preflight_once(provider, preflights, {"scope": binding["scope"], "slot": args.preflight_slot, "expected": expected},
                admit=lambda: admit_readonly_preflight(provider, store, binding, expected, args.preflight_slot))
            print(json.dumps({"schema": "deploy/scheduling-control-report/v1", "verdict": "observed", "code": "read-only-preflight-observed",
                "operation_id": packet["reservation"]["operation_id"], "evidence_sha256": digest(packet),
                "qualification": "read-only-runtime-connection-not-business-acceptance"}, sort_keys=True))
            return 0
        require(args.phase is not None, "control-phase-required")
        # Observation resolves original intent before candidate/package/current
        # parameter reads. No alternate label can select a fresh submission.
        if args.operation in {"prepare", "execute"}:
            if cleanup:
                result = phase_control(provider, CostAdmittedStore(store, provider, binding), binding, args.phase,
                    action=args.operation, build_inputs=lambda: control_phase_inputs(store, binding, args.phase),
                    admit=lambda intent: cleanup_control_shape(store, binding, intent))
            elif bounded or accepted:
                selections, work = read_json(args.database_selections), read_proof_data(args.owned_work)
                result = phase_control(provider, CostAdmittedStore(store, provider, binding), binding, args.phase,
                    action=args.operation, build_inputs=lambda: control_phase_inputs(store, binding, args.phase),
                    admit=lambda intent: (admit_accepted_phase if accepted else admit_bounded_phase)(provider, store, binding, intent, selections, work))
            else:
                selections = None if args.phase == "network-create" else read_json(args.database_selections)
                require(selections is None or isinstance(selections, dict) and set(selections) == {binding["scope"]}, "initial-database-selection-invalid")
                package_paths = {"dispatch": args.dispatch_receipt, "worker": args.worker_receipt}
                require(all(isinstance(path, str) and path for path in package_paths.values()), "package-receipts-required")
                maintenance = None if selections is None else selections.get(binding["scope"])
                result = phase_control(provider, CostAdmittedStore(store, provider, binding), binding, args.phase,
                    action=args.operation, build_inputs=lambda: initial_phase_inputs(provider, store, binding, args.phase, package_paths),
                    admit=lambda intent: admit_initial_phase(provider, store, binding, intent, selections, package_paths),
                    maintenance_selection=maintenance)
        else:
            result = phase_control(provider, store, binding, args.phase,
                action=args.operation, build_inputs=trusted_admission_required, admit=lambda _intent: trusted_admission_required())
    except Failure as failure:
        result = {"verdict": failure.verdict, "code": failure.code}
    except ADMISSION.AdmissionFailure as failure:
        result = {"verdict": "blocked", "code": failure.code}
    except (CHANGES.ChangeSetFailure, RESERVATIONS.ReservationFailure) as failure:
        result = {"verdict": "unknown", "code": failure.code}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, subprocess.SubprocessError):
        result = {"verdict": "blocked", "code": "control-input-or-observation-invalid"}
    print(json.dumps({"schema": "deploy/scheduling-control-report/v1", **result}, sort_keys=True))
    return 0 if result["verdict"] in {"reviewed", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
