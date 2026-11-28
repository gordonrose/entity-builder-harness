#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.environment-sessions.setup
#   version: 1
#   status: draft
#   created_on: "2026-11-28"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prepare exact session cleanup infrastructure and arm independent expiry before normal application deployment.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.environment-sessions
#     path: scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py
"""Trusted setup composition, not a general-purpose CloudFormation transport.

Only this source's records/control stacks can be created; no updates. Retirement
requires the original completed record, native control fingerprint and stack ARN.
Shared application transport still requires its exact delegated execution role.
Every mutation uses existing retained intent and single-submission mechanics.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import time
import zipfile


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


NATIVE = module("session_setup_native", Path(__file__).with_name("aws.py"))
ROOT = Path(__file__).resolve().parents[6]
OWNER = module("session_setup_owner", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py")


class SetupFailure(Exception):
    def __init__(self, reason):
        self.code = "environment-session-setup-" + reason
        super().__init__(self.code)


def require(condition, reason):
    if not condition:
        raise SetupFailure(reason)


class SetupStore(OWNER.RESERVATIONS.ImmutableReservationStore):
    schema, operation_prefix = "deploy/environment-session-setup-operation/v1", "session-setup-"

    def path_for(self, phase, request):
        require(phase in ("prepare", "execute", "upload", "arm", "stop", "delete")
            and isinstance(request, dict) and request.get("stage") in ("records", "control", "source", "expiry", "cleanup", "retire")
            and len(OWNER.RESERVATIONS.canonical(request)) <= OWNER.RECORDS.LIMIT, "reservation-invalid")
        return self.root / (request["stage"] + "-" + phase + ".json")

    def validate_time(self, value):
        OWNER.RECORDS.checked_time(value)


class Startup:
    def __init__(self, *, root, document, environment):
        require(isinstance(document, dict) and set(document) ==
            {"schema", "intent", "choices", "publications", "controller_publication"}
            and document["schema"] == "deploy/environment-session-start/v1"
            and isinstance(document["intent"], dict), "input-invalid")
        self.root, self.environment = Path(root), dict(environment)
        self.preparation = module("session_setup_preparation", self.root /
            "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        raw = document["intent"]
        require(raw.get("target") == "kanbien-core-platform"
            and raw.get("scope") in ("entity-smoke", "core-server-persistence")
            and not environment.get("CODEBUILD_BUILD_ARN"), "target-invalid")
        self.clock = lambda: int(datetime.now(timezone.utc).timestamp())
        self.plan = self.preparation.load_session_plan(self.root, raw["target"], raw["scope"], raw, self.clock(), 7200)
        binding = self.plan["binding"]
        self.binding = {name: getattr(binding, name) for name in
            ("target", "scope", "session_id", "starts_at", "expires_at", "source_inputs_sha256")}
        self.configuration = self.preparation.load(self.root, raw["target"], raw["scope"])
        choices, selections, _ = OWNER.checked_session_inputs(self.plan,
            choices=document["choices"], publications=document["publications"])
        choices["private-network/v1"] = OWNER.FOUNDATION.private_network_choice_syntax(
            choices["private-network/v1"], self.configuration["region"])
        self.control = dict(self.plan["control"])
        self.realization = module("session_setup_realization", self.root /
            "scripts/04.deploy/operational-realization-gate/evidence.py")
        self.realization_contract = self.preparation.read_document(self.root,
            "infra/04.deploy/03.product/image/environment-session-controller/setup-realization-contract.v2.yml")
        try:
            require(self.realization.GATE.validate_contract(self.realization_contract) ==
                "environment-session-setup-control", "realization-contract-unconfirmed")
        except self.realization.GATE.ContractFailure:
            raise SetupFailure("realization-contract-unconfirmed") from None
        self.provider = OWNER.SESSION_CLI.SessionProvider(profile=self.configuration["profile"],
            region=self.configuration["region"], environment=self.environment)
        self.operator = NATIVE.operator_arn(self.provider, self.configuration["account"])
        self.store = SetupStore(self.root / ".cache/environment-session-setup" / binding.session_id)
        self.command = {"schema": "deploy/environment-session-command/v1", "intent": raw,
            "source_inputs_sha256": binding.source_inputs_sha256,
            "choices": choices, "publications": selections}
        selection = document["controller_publication"]
        require(isinstance(selection, dict) and set(selection) == {"run_id", "source_revision"}
            and type(selection["run_id"]) is int and selection["run_id"] > 0
            and isinstance(selection["source_revision"], str)
            and re.fullmatch(r"[a-f0-9]{40}", selection["source_revision"]), "publication-invalid")
        publisher = module("session_setup_publication", self.root /
            "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/environment-session-controller-package-custody/publication.py").PUBLISHER
        contract = self.preparation.read_document(self.root,
            "infra/04.deploy/03.product/image/environment-session-controller/image-contract.yml")
        paths = contract["source_paths"]
        require(publisher.run(["git", "rev-parse", "HEAD"]) == selection["source_revision"], "source-revision-mismatch")
        publisher.run(["git", "diff", "--quiet", "HEAD", "--", *paths])
        require(not publisher.run(["git", "ls-files", "--others", "--exclude-standard", "--", *paths]), "source-uncommitted")
        b = publisher.binding
        pipeline = self.preparation.one(self.preparation.read_document(self.root,
            "infra/04.deploy/03.product/targets/kanbien-core-platform/40-package-custody/github-actions/pipeline-index.yml")["pipelines"],
            "id", b.pipeline, "pipeline")
        acquisition = pipeline["custody_acquisition"]
        publication = {"target": b.target, "account": b.account, "region": b.region,
            "candidate": contract["candidate_id"], "package": contract["id"], "program": contract["program_id"],
            "repository": b.repository, "repository_uri": b.uri,
            "repository_arn": "arn:aws:ecr:" + b.region + ":" + b.account + ":repository/" + b.repository,
            "pipeline": b.pipeline, "workflow": ".github/workflows/" + b.workflow,
            "source_repository": b.source_repository, "source_ref": publisher.source_selection()["acquisition"],
            "artifact_prefix": acquisition["artifact_prefix"], "receipt_member": acquisition["receipt_member"],
            "workflow_sha256": hashlib.sha256((self.root / ".github/workflows" / b.workflow).read_bytes()).hexdigest()}
        custody = module("session_setup_custody", self.root / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/acquire.py")
        checked = custody.acquire_custody(publication=publication, run_id=selection["run_id"],
            expected_source_revision=selection["source_revision"], aws_provider=self.provider)
        self.worker_image = b.uri + "@" + checked["receipt"]["image_digest"]
        names = publisher.run(["git", "ls-files", "-z", "--", *paths]).split("\0")
        self.source_files = tuple(self.root / name for name in names if name)
        self.source_artifact = self._source_artifact()
        self.custody = checked
        self.qualified = None
        self.ready = None

    def _source_artifact(self):
        require(bool(self.source_files) and all(path.is_file() and not path.is_symlink()
            and path.is_relative_to(self.root) for path in self.source_files), "source-unconfirmed")
        try:
            return "sha256:" + hashlib.sha256(OWNER.RESERVATIONS.canonical({
                str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.source_files})).hexdigest()
        except OSError:
            raise SetupFailure("source-unavailable") from None

    def _setup_gate(self, request, reservation, *, reviewed=None):
        """Only observed setup facts; never certify a future cleanup worker."""
        require(self._source_artifact() == self.source_artifact
            and NATIVE.operator_arn(self.provider, self.configuration["account"]) == self.operator,
            "setup-authority-unconfirmed")
        if self.custody is None:
            require(type(self) is PublicationStartup and self.source_qualification == self.source_artifact,
                "artifact-unconfirmed")
        else:
            receipt = self.custody["receipt"]
            require(receipt.get("verdict") == "qualified"
                and receipt.get("checks", {}).get("local_image_smoke") == "passed", "artifact-unconfirmed")
        try:
            book = self.realization.GateBook(self.realization_contract,
                {"infrastructure-controller-source": self.source_artifact},
                self.store.root / "realization" / hashlib.sha256(OWNER.RESERVATIONS.canonical(request)).hexdigest(),
                writer=OWNER.RESERVATIONS.write_exclusive,
                clock=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                component_check_id="session-setup-components")
            expected = {"infrastructure-controller-source", "infrastructure-operator", "infrastructure-inputs",
                "control-state-connection", "intent-connection", "resource-control-state", "attempt-store",
                "infrastructure-safe-reports", "infrastructure-reconciliation", "infrastructure-controller"}
            require(set(book.known) == expected, "realization-components-unsupported")
            require(self.store.read(reservation["phase"], request) == reservation, "reservation-unconfirmed")
            for component in sorted(expected):
                book.component(component)
            book.bind_plan("sha256:" + hashlib.sha256(OWNER.RESERVATIONS.canonical({
                "request": request, "operation_id": reservation["operation_id"],
                "source": self.source_artifact, "operator": self.operator})).hexdigest())
            for gate in ("source", "artifact", "semantic-integration", "live-read"):
                book.gate(gate)
            book.validate("live-read")
            if reviewed is not None:
                changes = reviewed["Changes"]
                book.gate("change-set")
                book.validate("change-set", len(changes), operation_class="create")
                checked = self.provider("cloudformation", "validate-template", TemplateBody=reviewed["_template"])
                template = OWNER.CF.template(reviewed["_template"])
                capabilities = ["CAPABILITY_NAMED_IAM"] if any(
                    row["Type"].startswith("AWS::IAM::") for row in template["Resources"].values()) else []
                parameters = checked.get("Parameters", [])
                require(checked.get("Capabilities", []) == capabilities
                    and not checked.get("DeclaredTransforms")
                    and isinstance(parameters, list) and len(parameters) == len(request["parameters"])
                    and all(isinstance(row, dict) for row in parameters)
                    and {row.get("ParameterKey") for row in parameters}
                        == set(request["parameters"]), "execution-preflight-unconfirmed")
                actions = ["cloudformation:CreateChangeSet", "cloudformation:ExecuteChangeSet"]
                simulated = self.provider("iam", "simulate-principal-policy", PolicySourceArn=self.operator,
                    ActionNames=actions, ResourceArns=[reviewed["StackId"]])
                rows = simulated.get("EvaluationResults", [])
                require(simulated.get("IsTruncated") is False and len(rows) == len(actions)
                    and {row.get("EvalActionName") for row in rows} == set(actions)
                    and all(row.get("EvalDecision") == "allowed" and not row.get("MissingContextValues")
                        and row.get("EvalResourceName") == reviewed["StackId"] for row in rows),
                    "execution-preflight-unconfirmed")
                book.gate("execution-preflight")
                book.validate("execution-preflight", len(changes), operation_class="create")
            return book
        except OWNER.RESERVATIONS.ReservationFailure:
            raise SetupFailure("realization-evidence-unavailable") from None
        except (self.realization.GATE.ContractFailure, self.realization.EvidenceFailure):
            raise SetupFailure("realization-unconfirmed") from None

    def _missing(self, operation, **arguments):
        try:
            return self.provider("cloudformation", operation, **arguments)
        except OWNER.SESSION_CLI.SessionProviderFailure as failure:
            if failure.code == "aws-resource-missing":
                return None
            raise

    def _completed_gate(self, request, reservation, count):
        """Link terminal readback to the original admission, never recertify it."""
        cache = self.store.root / "realization" / hashlib.sha256(OWNER.RESERVATIONS.canonical(request)).hexdigest()
        plan = "sha256:" + hashlib.sha256(OWNER.RESERVATIONS.canonical({"request": request,
            "operation_id": reservation["operation_id"], "source": self.source_artifact, "operator": self.operator})).hexdigest()
        try:
            complete = cache / "completed.json"
            OWNER.RESERVATIONS.no_symlinks(complete)
            if complete.exists():
                value = json.loads(complete.read_text())
                require(value.get("plan_sha256") == plan and value.get("operation_id") == reservation["operation_id"],
                    "execution-custody-unconfirmed")
                require(isinstance(value.get("evidence"), str) and re.fullmatch(
                    r"controlled-execution-[a-f0-9]{32}\.json", value["evidence"]), "execution-custody-unconfirmed")
                retained = cache / value["evidence"]
                OWNER.RESERVATIONS.no_symlinks(retained)
                require(hashlib.sha256(retained.read_bytes()).hexdigest() == value.get("evidence_sha256"),
                    "execution-custody-unconfirmed")
                return
            candidates = sorted(cache.glob("execution-preflight-*.json"))
            require(bool(candidates), "execution-admission-unconfirmed")
            OWNER.RESERVATIONS.no_symlinks(candidates[-1])
            admission = json.loads(candidates[-1].read_text())
            require(admission.get("plan_sha256") == plan and
                admission["facts"]["artifact_bindings"][0]["immutable_reference"] == self.source_artifact,
                "execution-admission-unconfirmed")
            book = self.realization.GateBook(self.realization_contract,
                {"infrastructure-controller-source": self.source_artifact}, cache,
                writer=OWNER.RESERVATIONS.write_exclusive,
                clock=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                component_check_id="session-setup-components")
            self.realization.GATE.validate_facts(admission["facts"], book.contract, book.identity, book.known, "execution-preflight")
            self.realization.GATE.validate_change_summary(admission["change_summary"], book.contract, book.identity, admission["facts"])
            book.facts, book.gates = admission["facts"], list(self.realization.GATE.GATE_ORDER[:6])
            book.components = {row["component_id"]: row["timestamp"] for row in book.facts["component_evidence"]}
            book.bind_plan(plan)
            book.gate("controlled-execution")
            evidence = book.validate("controlled-execution", count, operation_class="create")
            require(OWNER.RESERVATIONS.write_exclusive(complete, {"plan_sha256": plan,
                "operation_id": reservation["operation_id"], "evidence": evidence.name,
                "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest()}), "execution-custody-unconfirmed")
        except (OSError, ValueError, KeyError, TypeError, IndexError,
                OWNER.RESERVATIONS.ReservationFailure, self.realization.GATE.ContractFailure, self.realization.EvidenceFailure):
            raise SetupFailure("execution-evidence-unconfirmed") from None

    def _stack(self, stage, name, reference, parameters):
        """Only exact source-derived CREATE; never update or delete a stack."""
        require((stage, name, reference) in (
            ("records", self.control["records_stack"], self.control["records_template"]),
            ("control", self.control["stack"], self.control["template"])), "stack-selection-invalid")
        require(self.clock() < self.binding["expires_at"] and
            NATIVE.operator_arn(self.provider, self.configuration["account"]) == self.operator, "setup-authority-unconfirmed")
        source = OWNER.CF.template((self.root / reference).read_text())
        require(set(parameters) == set(source.get("Parameters", {}))
            and all(type(value) is str for value in parameters.values()), "parameters-invalid")
        template = OWNER.RESERVATIONS.canonical(source).decode()
        rows = [{"ParameterKey": key, "ParameterValue": value} for key, value in sorted(parameters.items())]
        request = {"stage": stage, "stack": name, "template_sha256": hashlib.sha256(template.encode()).hexdigest(),
                   "parameters": parameters, "source_artifact": self.source_artifact,
                   "realization_sha256": hashlib.sha256(OWNER.RESERVATIONS.canonical(self.realization_contract)).hexdigest()}
        change = name + "-create"
        def observe_stack(reservation):
            response = self._missing("describe-stacks", StackName=name)
            if response is None:
                return None
            stacks = response.get("Stacks")
            require(isinstance(stacks, list) and len(stacks) == 1, "stack-unconfirmed")
            stack = stacks[0]
            arn = stack.get("StackId")
            require(stack.get("StackName") == name and isinstance(arn, str) and
                arn.startswith("arn:aws:cloudformation:" + self.configuration["region"] + ":" +
                    self.configuration["account"] + ":stack/" + name + "/"), "stack-unconfirmed")
            if stack.get("StackStatus") in ("REVIEW_IN_PROGRESS", "CREATE_IN_PROGRESS"):
                return None
            require(stack.get("StackStatus") == "CREATE_COMPLETE"
                and OWNER.CHANGE_SETS.parameter_values(stack.get("Parameters")) == parameters, "stack-not-ready")
            actual = self.provider("cloudformation", "get-template", StackName=arn, TemplateStage="Original")
            require(OWNER.CF.templates_equal(source, actual.get("TemplateBody")), "stack-source-mismatch")
            if reservation is not None:
                events = self.provider("cloudformation", "describe-stack-events", StackName=arn)
                require(any(row.get("ResourceStatus") == "CREATE_COMPLETE" and
                    row.get("ResourceType") == "AWS::CloudFormation::Stack" for row in
                    OWNER.CHANGE_SETS.execution_events(events, reservation["operation_id"], arn)), "execution-unconfirmed")
                self._completed_gate(request, reservation, len(source["Resources"]))
            return stack
        executed = self.store.read("execute", request)
        current = observe_stack(executed)
        if current is not None:
            require(stage == "records" or executed is not None, "control-custody-unconfirmed")
            return current
        def observe_preparation(reservation):
            result = self._missing("describe-change-set", StackName=name, ChangeSetName=change)
            if result is None or result.get("Status") in ("CREATE_PENDING", "CREATE_IN_PROGRESS"):
                return None
            require(result.get("Status") == "CREATE_COMPLETE"
                and result.get("ChangeSetName") == change
                and result.get("StackName") == name and result.get("Description") == reservation["operation_id"]
                and OWNER.CHANGE_SETS.parameter_values(result.get("Parameters")) == parameters
                and result.get("Capabilities") == ["CAPABILITY_NAMED_IAM"], "change-set-unconfirmed")
            require(isinstance(result.get("StackId"), str) and result["StackId"].startswith(
                "arn:aws:cloudformation:" + self.configuration["region"] + ":" + self.configuration["account"]
                    + ":stack/" + name + "/"), "change-set-unconfirmed")
            changes = result.get("Changes")
            require(isinstance(changes, list) and len(changes) == len(source["Resources"])
                and {row.get("ResourceChange", {}).get("LogicalResourceId") for row in changes} == set(source["Resources"])
                and all(row.get("Type") == "Resource" and row["ResourceChange"].get("Action") == "Add"
                    and row["ResourceChange"].get("ResourceType") == source["Resources"][row["ResourceChange"]["LogicalResourceId"]]["Type"]
                    for row in changes), "change-set-effects-unconfirmed")
            actual = self.provider("cloudformation", "get-template", StackName=name, ChangeSetName=change, TemplateStage="Original")
            require(OWNER.CF.templates_equal(source, actual.get("TemplateBody")), "change-set-source-mismatch")
            return result
        def setup_send(service, operation, **arguments):
            # This private sender is not a generic optional-RoleARN API. Its
            # complete argument set must equal this source-bound operation.
            require(service == "cloudformation", "operation-prohibited")
            if operation == "create-change-set":
                expected = {"StackName": name, "ChangeSetName": change, "ChangeSetType": "CREATE",
                    "TemplateBody": template, "Parameters": rows, "Capabilities": ["CAPABILITY_NAMED_IAM"]}
                reserved = self.store.read("prepare", request)
                require(reserved is not None and arguments == {**expected,
                    "ClientToken": reserved["operation_id"], "Description": reserved["operation_id"]}, "operation-prohibited")
                self._setup_gate(request, reserved)
                # No secrets in the template/parameters; canonical operator was
                # proved above. Reuse the existing one-shot CLI invocation.
                parts = ["cloudformation", operation]
                for key, value in arguments.items():
                    flag = re.sub(r"(?<!^)(?=[A-Z][a-z])", "-", key).lower()
                    parts.extend(["--" + flag, json.dumps(value) if isinstance(value, list) else value])
                env = {**self.environment, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off",
                    "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true"}
                return OWNER.SESSION_CLI.CLI.invoke_json(["aws", *parts, "--profile", self.configuration["profile"],
                    "--region", self.configuration["region"], "--output", "json", "--no-cli-pager",
                    "--no-cli-auto-prompt", "--cli-connect-timeout", "10", "--cli-read-timeout", "20"],
                    timeout=35, empty_body="reject", object_only=True, environment=env)
            require(operation == "execute-change-set" and arguments == {"StackName": name,
                "ChangeSetName": change, "DisableRollback": True,
                "ClientRequestToken": self.store.read("execute", request)["operation_id"]}, "operation-prohibited")
            reviewed = observe_preparation(self.store.read("prepare", request))
            require(reviewed is not None and reviewed.get("ExecutionStatus") == "AVAILABLE", "change-set-unconfirmed")
            self._setup_gate(request, self.store.read("execute", request), reviewed={**reviewed, "_template": template})
            return self.provider(service, operation, **arguments)
        prepared = OWNER.CHANGE_SETS.prepare(setup_send, self.store, phase="prepare", request=request,
            arguments={"StackName": name, "ChangeSetName": change, "ChangeSetType": "CREATE", "TemplateBody": template,
                "Parameters": rows, "Capabilities": ["CAPABILITY_NAMED_IAM"]},
            precondition=lambda _: require(self._missing("describe-stacks", StackName=name) is None, "stack-already-exists"),
            observe=observe_preparation, passthrough=(SetupFailure,))
        if prepared is None:
            return None
        return OWNER.CHANGE_SETS.execute(setup_send, self.store, phase="execute", request=request,
            arguments={"StackName": name, "ChangeSetName": change, "DisableRollback": True},
            precondition=lambda _: require(observe_preparation(self.store.read("prepare", request)).get("ExecutionStatus") == "AVAILABLE", "change-set-unconfirmed"),
            observe=observe_stack, passthrough=(SetupFailure,))

    def advance(self):
        if self.ready is not None:
            return self.ready
        require(self.clock() < self.binding["expires_at"], "expired")
        if self._stack("records", self.control["records_stack"], self.control["records_template"],
                {"SetupOperatorArn": self.operator}) is None:
            return None
        storage = NATIVE.storage_snapshot(root=self.root, control=self.control, owner=OWNER, provider=self.provider,
            configuration=self.configuration, setup_operator=self.operator)
        records = OWNER.RECORDS.SessionRecords(bucket=storage["bucket"], key=self.control["record_key"],
            account=self.configuration["account"], region=self.configuration["region"], profile=self.configuration["profile"],
            environment=self.environment, binding=self.binding, clock=self.clock,
            guard=lambda action, binding: require(binding == self.binding and action in ("read", "read-child"), "storage-action-prohibited"))
        if not self.retire_predecessor(records):
            return None
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            info = zipfile.ZipInfo("session-input.json", date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100600 << 16
            archive.writestr(info, OWNER.RESERVATIONS.canonical(self.command))
        raw = stream.getvalue()
        key = "sources/" + hashlib.sha256(raw).hexdigest() + ".zip"
        _, fresh = self.store.reserve("upload", {"stage": "source", "key": key, "bytes": len(raw)})
        if fresh:
            require(NATIVE.operator_arn(self.provider, self.configuration["account"]) == self.operator, "setup-authority-unconfirmed")
            try:
                records._write_bytes(raw, key=key, child=True)
            except OWNER.RECORDS.CLI.CliFailure:
                pass
        try:
            actual, metadata = records._read_bytes(key=key)
        except OWNER.RECORDS.CLI.CliFailure as failure:
            if failure.code == "aws-resource-missing":
                return None
            raise
        require(actual == raw, "source-upload-unconfirmed")
        parameters = {"SessionId": self.binding["session_id"], "ResourceNamePrefix": "s-" + self.binding["session_id"][:19],
            "WorkerReady": "true", "SetupOperatorArn": self.operator, "Records": storage["bucket"],
            "SourceKey": key, "SourceVersion": metadata["VersionId"], "WorkerImage": self.worker_image,
            "ExpiresAt": datetime.fromtimestamp(self.binding["expires_at"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if self._stack("control", self.control["stack"], self.control["template"], parameters) is None:
            return None
        qualified = NATIVE.NativeControl(root=self.root, configuration=self.configuration, binding=self.binding,
            control=self.control, owner=OWNER, provider=self.provider)
        qualified.activate("requester")
        name = "expiry-" + self.binding["session_id"]
        request = {"stage": "expiry", "stateMachineArn": qualified.version, "name": name, "input": "{}"}
        _, fresh = self.store.reserve("arm", request)
        if fresh:
            try:
                self.provider("stepfunctions", "start-execution", **{key: value for key, value in request.items() if key != "stage"})
            except OWNER.SESSION_CLI.SessionProviderFailure:
                pass
        qualified.require_expiry()
        self.qualified = qualified
        self.records = records
        self.ready = NATIVE.new_assembly(root=self.root, document=self.command, environment=self.environment)
        return self.ready

    def finish(self):
        # Keep the setup identity, not a foreground role being deleted. The
        # permanent versioned records survive control-stack retirement.
        return self.retire(self.records, self.records.observe_existing()["document"])

    def retire_predecessor(self, records):
        """Close only a completed original controller before successor admission."""
        try:
            raw, _ = records._read_bytes()
        except OWNER.RECORDS.CLI.CliFailure as failure:
            if failure.code == "aws-resource-missing":
                return True
            raise
        document = json.loads(raw, object_pairs_hook=OWNER.RECORDS._duplicate_safe)
        if document.get("binding") == self.binding:
            return True
        require(isinstance(document.get("binding"), dict)
            and document["binding"].get("target") == self.binding["target"]
            and document["binding"].get("session_id", "")[:19] != self.binding["session_id"][:19], "predecessor-binding-invalid")
        old_binding = document["binding"]
        old = OWNER.RECORDS.SessionRecords(bucket=records.bucket, key=records.key,
            account=records.account, region=records.region, profile=records.profile, environment=self.environment,
            binding=old_binding, clock=self.clock,
            guard=lambda action, binding: require(binding == old_binding and action in ("read", "read-child"), "storage-action-prohibited"))
        checked = old.observe_existing()["document"]
        require(checked == document and old.observe_cleanup_completion() is not None, "predecessor-not-completed")
        return self.retire(old, checked)

    def retire(self, records, document):
        """Source-qualified operator closes old execution and deletes exact control."""
        require(document == records.observe_existing()["document"]
            and records.observe_cleanup_completion() is not None, "cleanup-not-completed")
        prefix = "s-" + document["binding"]["session_id"][:19]
        control = {**self.control, "stack": prefix + "-session-control"}
        stack = self._missing("describe-stacks", StackName=control["stack"])
        if stack is None:
            for suffix in ("foreground", "cleanup-worker", "cfn-create", "cfn-cleanup", "expiry-role"):
                try:
                    self.provider("iam", "get-role", RoleName=prefix + "-" + suffix)
                except OWNER.SESSION_CLI.SessionProviderFailure as failure:
                    require(failure.code == "aws-resource-missing", "retirement-observation-unconfirmed")
                    continue
                return False
            return True
        store = SetupStore(self.root / ".cache/environment-session-setup" / document["binding"]["session_id"])
        rows = stack.get("Stacks", [])
        require(len(rows) == 1 and rows[0].get("StackName") == control["stack"], "retirement-stack-unconfirmed")
        stack_id = rows[0].get("StackId")
        require(isinstance(stack_id, str) and stack_id.startswith("arn:aws:cloudformation:" + records.region + ":" + records.account
            + ":stack/" + control["stack"] + "/"), "retirement-stack-unconfirmed")
        request = {"stage": "retire", "stack_id": stack_id,
            "control_fingerprint": document["base"]["provider_facts"]["qualified-session-control/v1"]}
        reserved = store.read("delete", request)
        if rows[0].get("StackStatus") in ("DELETE_IN_PROGRESS", "DELETE_COMPLETE"):
            require(reserved is not None, "retirement-custody-unconfirmed")
            return False
        source = self.provider("cloudformation", "get-template", StackName=stack_id, TemplateStage="Original").get("TemplateBody")
        qualified = NATIVE.NativeControl(root=self.root, configuration=self.configuration, binding=document["binding"],
            control=control, owner=OWNER, provider=self.provider, _source=OWNER.CF.template(source),
            _original_fingerprint=request["control_fingerprint"])
        qualified.activate("requester")
        qualified.setup_provider = self.provider
        qualified.require_predecessor_stacks_deleted(document)
        for stage, value in (("expiry", "{}"), ("cleanup", '{"cleanup_now":true}')):
            execution = qualified.version.rsplit(":", 1)[0].replace(":stateMachine:", ":execution:") + ":" + stage + "-" + document["binding"]["session_id"]
            try:
                observed = self.provider("stepfunctions", "describe-execution", executionArn=execution)
            except OWNER.SESSION_CLI.SessionProviderFailure as failure:
                require(failure.code == "aws-resource-missing" and stage == "cleanup", "execution-unconfirmed")
                continue
            require(observed.get("executionArn") == execution and observed.get("stateMachineVersionArn") == qualified.version
                and observed.get("input") == value and observed.get("status") in
                    ("RUNNING", "SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"), "execution-unconfirmed")
            if observed["status"] == "RUNNING":
                _, fresh = store.reserve("stop", {"stage": stage, "execution": execution, "version": qualified.version})
                if fresh:
                    try:
                        self.provider("stepfunctions", "stop-execution", executionArn=execution,
                            error="SessionCleanupCompleted", cause="Application cleanup is retained and complete.")
                    except OWNER.SESSION_CLI.SessionProviderFailure:
                        pass
                return False
        builds = self.provider("codebuild", "list-builds-for-project", projectName=qualified.project["name"], sortOrder="ASCENDING")
        ids = builds.get("ids")
        require(isinstance(ids, list) and all(isinstance(value, str)
            and value.startswith(qualified.project["name"] + ":") for value in ids), "builds-unconfirmed")
        for offset in range(0, len(ids), 100):
            selected = ids[offset:offset + 100]
            result = self.provider("codebuild", "batch-get-builds", ids=selected)
            builds = result.get("builds")
            require(result.get("buildsNotFound", []) == [] and isinstance(builds, list)
                and len(builds) == len(selected) and {row.get("id") for row in builds} == set(selected)
                and all(row.get("projectName") == qualified.project["name"] for row in builds), "builds-unconfirmed")
            if not all(row.get("buildComplete") is True for row in builds):
                return False
        def send(service, operation, **arguments):
            retained = store.read("delete", request)
            require(service == "cloudformation" and operation == "delete-stack" and retained is not None
                and arguments == {"StackName": qualified.stack_id, "ClientRequestToken": retained["operation_id"]}
                and NATIVE.operator_arn(self.provider, records.account) == qualified.parameters["SetupOperatorArn"], "retirement-operation-prohibited")
            return OWNER.SESSION_CLI.CLI.invoke_json(["aws", "cloudformation", "delete-stack", "--stack-name", qualified.stack_id,
                "--client-request-token", retained["operation_id"], "--profile", self.configuration["profile"],
                "--region", records.region, "--output", "json", "--no-cli-pager", "--no-cli-auto-prompt",
                "--cli-connect-timeout", "10", "--cli-read-timeout", "20"], timeout=35,
                empty_body="empty-string", object_only=True,
                environment={**self.environment, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": "",
                    "AWS_CLI_AUTO_PROMPT": "off", "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true"})
        OWNER.CHANGE_SETS.delete(send, store, phase="delete", request=request,
            arguments={"StackName": qualified.stack_id},
            precondition=lambda _: require(records.observe_cleanup_completion() is not None, "cleanup-not-completed"),
            observe=lambda _: None)
        return False


class PublicationStartup(Startup):
    """Source-qualified registry bootstrap; never admits an application worker."""
    def __init__(self, *, root, environment):
        self.root, self.environment = Path(root), dict(environment)
        require(not self.environment.get("CODEBUILD_BUILD_ARN"), "target-invalid")
        self.preparation = module("session_publication_preparation", self.root /
            "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        self.configuration = self.preparation.load(self.root, "kanbien-core-platform", "entity-smoke")
        self.realization = module("session_publication_realization", self.root /
            "scripts/04.deploy/operational-realization-gate/evidence.py")
        self.realization_contract = self.preparation.read_document(self.root,
            "infra/04.deploy/03.product/image/environment-session-controller/setup-realization-contract.v2.yml")
        require(self.realization.GATE.validate_contract(self.realization_contract) ==
            "environment-session-setup-control", "realization-contract-unconfirmed")
        self.control = {"stack": "kanbien-environment-session-controller-publication", "template":
            "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/environment-session-controller-publication.yml"}
        # Both pair slots deliberately name this one fixed stack; inherited
        # application/records entry points cannot select a different resource.
        self.control.update(records_stack=self.control["stack"], records_template=self.control["template"])
        self.store = SetupStore(self.root / ".cache/environment-session-setup/publication")
        self.clock = lambda: int(datetime.now(timezone.utc).timestamp())
        self.binding = {"expires_at": self.clock() + 900}
        publisher = module("session_registry_publication", self.root /
            "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/environment-session-controller-package-custody/publication.py").PUBLISHER
        contract = self.preparation.read_document(self.root,
            "infra/04.deploy/03.product/image/environment-session-controller/image-contract.yml")
        paths = contract["source_paths"]
        publisher.run(["git", "diff", "--quiet", "HEAD", "--", *paths])
        require(not publisher.run(["git", "ls-files", "--others", "--exclude-standard", "--", *paths]), "source-uncommitted")
        names = publisher.run(["git", "ls-files", "-z", "--", *paths]).split("\0")
        self.source_files = tuple(self.root / name for name in names if name)
        self.source_artifact = self._source_artifact()
        # The ordinary private runner owns proof and trusted unchanged reuse.
        # No supplied receipt, fake image smoke or bootstrap publication cycle.
        try:
            result = subprocess.run(["bash", "scripts/repo/check-selection/script.sh", "--checks",
                "environment-session-controller", "environment-session-controller-package",
                "--execute-local", "--json"], cwd=self.root, env=self.environment,
                capture_output=True, timeout=180, check=False)
        except (OSError, subprocess.SubprocessError):
            raise SetupFailure("source-qualification-unconfirmed") from None
        require(result.returncode == 0 and self._source_artifact() == self.source_artifact,
            "source-qualification-unconfirmed")
        self.source_qualification, self.custody = self.source_artifact, None
        self.provider = OWNER.SESSION_CLI.SessionProvider(profile=self.configuration["profile"],
            region=self.configuration["region"], environment=self.environment)
        self.operator = NATIVE.operator_arn(self.provider, self.configuration["account"])

    def advance(self):
        return self._stack("control", self.control["stack"], self.control["template"],
            {"ExistingGitHubOidcProviderArn": "arn:aws:iam::337159794548:oidc-provider/token.actions.githubusercontent.com"})


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Create only the fixed controller registry and publishing role.")
    parser.add_argument("operation", choices=("publication",))
    args = parser.parse_args()
    try:
        startup = PublicationStartup(root=ROOT, environment=dict(os.environ))
        deadline = time.monotonic() + 600
        while startup.advance() is None:
            if time.monotonic() >= deadline:
                print(json.dumps({"status": "pending", "reason": "environment-session-publication-pending"}))
                raise SystemExit(2)
            time.sleep(5)
        print(json.dumps({"status": "completed", "stage": "publication-infrastructure"}))
    except Exception as failure:
        code = getattr(failure, "code", "environment-session-publication-unconfirmed")
        safe = code if re.fullmatch(r"[a-z][a-z0-9-]{1,100}", str(code)) else "environment-session-publication-unconfirmed"
        print(json.dumps({"status": "blocked", "reason": safe}))
        raise SystemExit(1)
