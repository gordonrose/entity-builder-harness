#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.environment-sessions.aws
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Connect the session coordinator to existing AWS operations, retained verdicts and native workload consumers.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.environment-sessions
#     path: scripts/04.deploy/lifecycle/60-run/capabilities/environment-sessions/script.py
"""Concrete handoff to existing senders; live construction needs qualified guards.

The protected worker constructs its native task consumer and SessionOperations.
Neither an input document nor this assembly manufactures execution authority.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class TaskAssemblyFailure(Exception):
    def __init__(self, condition):
        self.code = "environment-session-task-" + condition
        super().__init__(self.code)


def require(condition, reason):
    if not condition:
        raise TaskAssemblyFailure(reason)


def operator_arn(provider, account):
    identity = provider("sts", "get-caller-identity")
    arn = identity.get("Arn")
    if isinstance(arn, str) and arn.startswith("arn:aws:sts::" + account + ":assumed-role/"):
        role = provider("iam", "get-role", RoleName=arn.split("/")[1]).get("Role", {})
        require(isinstance(identity.get("UserId"), str) and isinstance(role.get("RoleId"), str)
            and identity["UserId"].startswith(role["RoleId"] + ":"), "control-actor-unconfirmed")
        arn = role.get("Arn")
    require(identity.get("Account") == account and isinstance(arn, str)
        and re.fullmatch("arn:aws:iam::" + account + r":(?:role|user)/[A-Za-z0-9+=,.@_/-]+", arn), "control-actor-unconfirmed")
    return arn


def storage_snapshot(*, root, control, owner, provider, configuration, setup_operator):
    """Qualify the permanent store before any controller or source upload exists."""
    root = Path(root)
    account, region = configuration["account"], configuration["region"]
    bucket = "kanbien-session-records-" + account + "-" + region
    runtime = module("session_storage_runtime", root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
    source = owner.CF.template((root / control["records_template"]).read_text())
    response = provider("cloudformation", "describe-stacks", StackName=control["records_stack"])
    stacks = response.get("Stacks", [])
    require(len(stacks) == 1 and stacks[0].get("StackName") == control["records_stack"]
        and stacks[0].get("StackStatus") in ("CREATE_COMPLETE", "UPDATE_COMPLETE"), "control-storage-stack-unconfirmed")
    stack_id = stacks[0].get("StackId")
    require(isinstance(stack_id, str) and stack_id.startswith("arn:aws:cloudformation:" + region + ":" + account
        + ":stack/" + control["records_stack"] + "/") and stacks[0].get("Parameters") == [
            {"ParameterKey": "SetupOperatorArn", "ParameterValue": setup_operator}], "control-storage-stack-unconfirmed")
    actual = provider("cloudformation", "get-template", StackName=stack_id, TemplateStage="Original").get("TemplateBody")
    require(owner.CF.templates_equal(source, owner.CF.template(actual)), "control-storage-source-changed")
    rows = provider("cloudformation", "list-stack-resources", StackName=stack_id).get("StackResourceSummaries", [])
    require(len(rows) == len(source["Resources"]) and {row.get("LogicalResourceId"): row.get("ResourceType") for row in rows}
        == {key: row["Type"] for key, row in source["Resources"].items()}
        and next(row for row in rows if row["LogicalResourceId"] == "Records").get("PhysicalResourceId") == bucket,
        "control-storage-resources-unconfirmed")
    storage_resources = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows}
    expected = runtime.runtime_resolve(source["Resources"]["RecordsPolicy"]["Properties"]["PolicyDocument"],
        {"SetupOperatorArn": setup_operator, "Records": bucket}, storage_resources, "session-control",
        account=account, region=region, _attributes={("Records", "Arn"): "arn:aws:s3:::" + bucket})
    arguments = {"Bucket": bucket, "ExpectedBucketOwner": account}
    get = lambda operation: provider("s3api", operation, **arguments)
    require(get("get-bucket-versioning").get("Status") == "Enabled", "control-storage-unprotected")
    require(get("get-public-access-block").get("PublicAccessBlockConfiguration") == {
        "BlockPublicAcls": True, "IgnorePublicAcls": True, "BlockPublicPolicy": True, "RestrictPublicBuckets": True}, "control-storage-unprotected")
    require(get("get-bucket-ownership-controls").get("OwnershipControls", {}).get("Rules") == [{"ObjectOwnership": "BucketOwnerEnforced"}], "control-storage-unprotected")
    rules = get("get-bucket-encryption").get("ServerSideEncryptionConfiguration", {}).get("Rules")
    require(isinstance(rules, list) and len(rules) == 1 and rules[0].get("ServerSideEncryptionByDefault") == {"SSEAlgorithm": "AES256"}, "control-storage-unprotected")
    require(runtime.same(runtime.policy(get("get-bucket-policy").get("Policy"), "session-control"),
        runtime.policy(expected, "session-control")), "control-storage-policy-changed")
    fingerprint = hashlib.sha256(owner.RESERVATIONS.canonical({"stack": stack_id, "template": source,
        "operator": setup_operator, "bucket": bucket})).hexdigest()
    return {"bucket": bucket, "fingerprint": fingerprint}


class NativeControl:
    """Observe the protected setup once; no caller flag creates this context.

    Routine identities cannot change its IAM, project, source or bucket policy.
    Setup maintenance invalidates this snapshot and requires requalification.
    Each session owns its project and expiry; later sessions cannot retarget it.
    The existing operation owner separately checks original resource custody.
    """
    def __init__(self, *, root, configuration, binding, control, owner, provider, _source=None, _original_fingerprint=None):
        self.root = Path(root)
        self.configuration, self.binding, self.control = map(deepcopy, (configuration, binding, control))
        self.owner, self.provider, self.actor = owner, provider, None
        self.account, self.region = configuration["account"], configuration["region"]
        self.runtime = module("session_control_runtime", Path(root) / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")
        self._require((_source is None and _original_fingerprint is None)
            or isinstance(_source, dict) and isinstance(_original_fingerprint, str) and re.fullmatch(r"[a-f0-9]{64}", _original_fingerprint),
            "control-original-context-unconfirmed")
        source = owner.CF.template((Path(root) / control["template"]).read_text()) if _source is None else deepcopy(_source)
        response = provider("cloudformation", "describe-stacks", StackName=control["stack"])
        stacks = response.get("Stacks")
        self._require(isinstance(stacks, list) and len(stacks) == 1, "control-stack-unconfirmed")
        stack = stacks[0]
        self.stack_id = stack.get("StackId")
        self._require(stack.get("StackName") == control["stack"] and isinstance(self.stack_id, str)
            and self.stack_id.startswith("arn:aws:cloudformation:" + self.region + ":" + self.account + ":stack/" + control["stack"] + "/")
            and stack.get("StackStatus") in ("CREATE_COMPLETE", "UPDATE_COMPLETE"), "control-stack-unconfirmed")
        observed = provider("cloudformation", "get-template", StackName=self.stack_id, TemplateStage="Original").get("TemplateBody")
        observed = owner.CF.template(observed) if isinstance(observed, str) else observed
        self._require(owner.CF.templates_equal(source, observed), "control-source-changed")
        rows = stack.get("Parameters")
        self._require(isinstance(rows, list) and all(isinstance(row, dict) and set(row) == {"ParameterKey", "ParameterValue"}
            and isinstance(row["ParameterValue"], str) for row in rows)
            and len({row["ParameterKey"] for row in rows}) == len(rows), "control-parameters-invalid")
        self.parameters = {row["ParameterKey"]: row["ParameterValue"] for row in rows}
        self._require(set(self.parameters) == set(source["Parameters"]), "control-parameters-invalid")
        prefix = "s-" + binding["session_id"][:19]
        expected = {"SessionId": binding["session_id"], "ResourceNamePrefix": prefix, "WorkerReady": "true",
            "Records": "kanbien-session-records-" + self.account + "-" + self.region,
            "ExpiresAt": datetime.fromtimestamp(binding["expires_at"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        self._require(all(self.parameters.get(key) == value for key, value in expected.items())
            and re.fullmatch(r"sources/[a-f0-9]{64}\.zip", self.parameters["SourceKey"])
            and self.parameters["SourceVersion"] not in ("", "null")
            and re.fullmatch(r"[A-Za-z0-9./:_-]+@sha256:[a-f0-9]{64}", self.parameters["WorkerImage"]), "control-session-mismatch")
        rows = provider("cloudformation", "list-stack-resources", StackName=self.stack_id).get("StackResourceSummaries")
        self._require(isinstance(rows, list) and len({row.get("LogicalResourceId") for row in rows}) == len(rows), "control-resources-invalid")
        self.resources = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in rows}
        self._require(set(self.resources) == set(source["Resources"])
            and all(self.resources[key]["type"] == row["Type"] for key, row in source["Resources"].items()), "control-resources-invalid")
        self.source = source
        backup = provider("backup", "list-backup-plans", IncludeDeleted=False).get("BackupPlansList")
        self._require(isinstance(backup, list), "control-backup-policy-unconfirmed")
        self.no_backup_plans = backup == []
        parameters = {**self.parameters, **{key: row["physical_id"] for key, row in self.resources.items()}}
        self.bucket = parameters["Records"]
        attributes = {("Records", "Arn"): "arn:aws:s3:::" + self.bucket,
            ("WorkerLogs", "Arn"): "arn:aws:logs:" + self.region + ":" + self.account + ":log-group:" + parameters["WorkerLogs"] + ":*",
            ("Cleanup", "Arn"): "arn:aws:codebuild:" + self.region + ":" + self.account + ":project/" + parameters["Cleanup"]}
        self.resolve = lambda value: self.runtime.runtime_resolve(value, parameters, self.resources, "session-control",
            account=self.account, region=self.region, _attributes=attributes)
        # These immutable metadata reads are reused only inside this qualification.
        metadata = {}
        def native(service, operation, **arguments):
            key = (service, operation, json.dumps(arguments, sort_keys=True))
            if key not in metadata:
                metadata[key] = provider(service, operation, **arguments)
            return deepcopy(metadata[key])
        policies = {}
        policy_facts = {}
        for key, row in source["Resources"].items():
            if row["Type"] == "AWS::IAM::ManagedPolicy":
                arn = parameters[key]
                policies[arn] = self.resolve(row["Properties"]["PolicyDocument"])
                policy_facts[arn] = self.runtime.runtime_managed_policy(native, arn, policies[arn], "session-control")
        self.roles, role_facts, self.role_ids = {}, {}, {}
        for key, row in source["Resources"].items():
            if row["Type"] != "AWS::IAM::Role":
                continue
            properties = self.resolve(row["Properties"])
            attached = [parameters[name] for name, policy in source["Resources"].items()
                if policy["Type"] == "AWS::IAM::ManagedPolicy" and {"Ref": key} in policy["Properties"].get("Roles", [])]
            if attached:
                properties["ManagedPolicyArns"] = attached
            role_facts[key] = self.runtime.runtime_role(native, key, parameters, self.resources, "session-control",
                {"Resources": {key: {"Properties": properties}}}, account=self.account, region=self.region, _managed_policies=policies)
            actual = native("iam", "get-role", RoleName=parameters[key])["Role"]
            self._require(actual.get("MaxSessionDuration") == properties.get("MaxSessionDuration", 3600)
                and isinstance(actual.get("RoleId"), str), "control-role-unconfirmed")
            self.roles[key], self.role_ids[key] = actual["Arn"], actual["RoleId"]
        self.version = parameters["ExpiryVersion"]
        expiry = provider("stepfunctions", "describe-state-machine", stateMachineArn=self.version)
        definition = expiry.get("definition")
        try:
            definition = json.loads(definition, object_pairs_hook=owner.RECORDS._duplicate_safe)
        except (TypeError, ValueError, RecursionError):
            raise TaskAssemblyFailure("control-expiry-unconfirmed") from None
        self._require(expiry.get("type") == "STANDARD" and expiry.get("roleArn") == self.roles["ExpiryRole"]
            and owner.CF.templates_equal(definition, self.resolve(source["Resources"]["Expiry"]["Properties"]["Definition"])), "control-expiry-unconfirmed")
        self._storage()
        projects = provider("codebuild", "batch-get-projects", names=[parameters["Cleanup"]])
        self._require(projects.get("projectsNotFound", []) == [] and len(projects.get("projects", [])) == 1, "control-project-unconfirmed")
        self.project = projects["projects"][0]
        self.expected_project = self.resolve(source["Resources"]["Cleanup"]["Properties"])
        self._require(self.project.get("name") == self.expected_project["Name"]
            and self.project.get("arn") == attributes[("Cleanup", "Arn")], "control-project-unconfirmed")
        self._project_configuration(self.project)
        self.fingerprint = hashlib.sha256(json.dumps({"stack": self.stack_id, "parameters": self.parameters,
            "template": hashlib.sha256(owner.RESERVATIONS.canonical(source)).hexdigest(), "storage": self.storage_fingerprint,
            "roles": role_facts, "role_ids": self.role_ids, "policies": policy_facts}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self._require(_original_fingerprint is None or self.fingerprint == _original_fingerprint, "control-original-context-changed")

    def _require(self, condition, reason):
        if not condition:
            raise TaskAssemblyFailure(reason)

    def _storage(self):
        observed = storage_snapshot(root=self.root, control=self.control, owner=self.owner, provider=self.provider,
            configuration=self.configuration, setup_operator=self.parameters["SetupOperatorArn"])
        self._require(observed["bucket"] == self.bucket, "control-storage-stack-unconfirmed")
        self.storage_fingerprint = observed["fingerprint"]

    def _project_configuration(self, actual, *, build=False):
        expected = self.expected_project
        self._require(actual.get("serviceRole") == expected["ServiceRole"]
            and actual.get("sourceVersion") == expected["SourceVersion"], "control-worker-overridden")
        for field in ("source", "environment"):
            values = expected[field[:1].upper() + field[1:]]
            for key, value in values.items():
                native = "buildspec" if key == "BuildSpec" else key[:1].lower() + key[1:]
                self._require(actual.get(field, {}).get(native) == value, "control-worker-overridden")
        self._require(actual.get("environment", {}).get("environmentVariables", []) == []
            and actual.get("secondarySources", []) == [] and actual.get("secondaryArtifacts", []) == []
            and (actual.get("artifacts", {}).get("location") in (None, "") if build
                 else actual.get("artifacts", {}).get("type") == "NO_ARTIFACTS"), "control-worker-overridden")
        for native, source in (("timeoutInMinutes", "TimeoutInMinutes"), ("queuedTimeoutInMinutes", "QueuedTimeoutInMinutes")):
            self._require(actual.get(native) == expected[source], "control-worker-overridden")
        if not build:
            self._require(actual.get("concurrentBuildLimit") == expected["ConcurrentBuildLimit"]
                and actual.get("autoRetryLimit", 0) == expected["AutoRetryLimit"]
                and actual.get("projectVisibility") == expected["Visibility"], "control-worker-overridden")

    def activate(self, actor, *, provider=None, environment=None):
        self._require(actor in ("foreground", "worker", "requester"), "control-actor-invalid")
        provider = self.provider if provider is None else provider
        if actor == "requester":
            self._require(operator_arn(provider, self.account) == self.parameters["SetupOperatorArn"], "control-actor-unconfirmed")
            self.provider, self.actor = provider, actor
            return
        identity = provider("sts", "get-caller-identity")
        role = "ForegroundRole" if actor == "foreground" else "WorkerRole"
        name = self.roles[role].rsplit("/", 1)[-1]
        self._require(identity.get("Account") == self.account and isinstance(identity.get("Arn"), str)
            and identity["Arn"].startswith("arn:aws:sts::" + self.account + ":assumed-role/" + name + "/")
            and isinstance(identity.get("UserId"), str) and identity["UserId"].startswith(self.role_ids[role] + ":"), "control-actor-unconfirmed")
        if actor == "worker":
            arn = (environment or {}).get("CODEBUILD_BUILD_ARN")
            self._require(isinstance(arn, str) and arn.startswith(self.project["arn"].replace(":project/", ":build/") + ":"), "control-build-unconfirmed")
            response = provider("codebuild", "batch-get-builds", ids=[arn])
            self._require(response.get("buildsNotFound", []) == [] and len(response.get("builds", [])) == 1, "control-build-unconfirmed")
            build = response["builds"][0]
            self._require(build.get("arn") == arn and build.get("projectName") == self.expected_project["Name"]
                and build.get("buildStatus") == "IN_PROGRESS", "control-build-unconfirmed")
            self._project_configuration(build, build=True)
        self.provider, self.actor = provider, actor

    def guard(self, action, binding):
        self._require(self.actor in ("foreground", "worker", "requester") and binding == self.binding, "control-context-unconfirmed")

    def preflight(self, context):
        self.guard(context["action"], context["binding"])
        plan = context["source_plan"]
        self._require(plan.get("control") == self.control and plan["execution_roles"] == {
            "creation": self.roles["CreationRole"], "cleanup": self.roles["CleanupRole"]}, "control-plan-mismatch")
        allowed = {"seal", "stop-task", "prepare-discard-prepare", "prepare-discard-execute", "delete", "complete-cleanup"} if self.actor == "worker" else {
            "initialize", "seal", "creation-prepare", "creation-execute", "activation-prepare", "activation-execute", "task", "cleanup-worker-start"}
        if self.actor == "requester":
            allowed = {"seal", "cleanup-worker-start"}
        self._require(context["action"] in allowed, "control-action-prohibited")
        if context["action"] in {"initialize", "creation-prepare", "creation-execute", "activation-prepare", "activation-execute", "task"}:
            self.require_expiry()
        if context["action"] in {"initialize", "creation-prepare", "creation-execute", "activation-prepare", "activation-execute", "complete-cleanup"}:
            # Existing Backup selections need separate qualification; neither
            # app/CFN roles can create plans, snapshots or replication writers.
            self._require(self.no_backup_plans, "control-backup-policy-unqualified")

    def admit_successor(self, old, document):
        self._require(self.actor == "foreground" and callable(self.setup_provider), "control-successor-prohibited")
        self._require(document["binding"]["target"] == self.binding["target"]
            and document["binding"]["session_id"] != self.binding["session_id"], "control-successor-prohibited")
        self.require_predecessor_stacks_deleted(document)
        prefix = "s-" + document["binding"]["session_id"][:19]
        self._require(prefix != "s-" + self.binding["session_id"][:19], "control-successor-prohibited")
        def absent(service, operation, **arguments):
            try:
                self.setup_provider(service, operation, **arguments)
            except self.owner.SESSION_CLI.SessionProviderFailure as failure:
                self._require(failure.code == "aws-resource-missing", "control-predecessor-observation-unconfirmed")
                return
            raise TaskAssemblyFailure("control-predecessor-authority-remains")
        absent("cloudformation", "describe-stacks", StackName=prefix + "-session-control")
        for suffix in ("foreground", "cleanup-worker", "cfn-create", "cfn-cleanup", "expiry-role"):
            absent("iam", "get-role", RoleName=prefix + "-" + suffix)

    def require_predecessor_stacks_deleted(self, document):
        self._require(callable(self.setup_provider), "control-successor-prohibited")
        prefix = "s-" + document["binding"]["session_id"][:19]
        for stack, stack_id in document["incarnations"].items():
            self._require(stack.startswith(prefix + "-"), "control-predecessor-identity-unconfirmed")
            try:
                observed = self.setup_provider("cloudformation", "describe-stacks", StackName=stack_id).get("Stacks", [])
            except self.owner.SESSION_CLI.SessionProviderFailure as failure:
                self._require(failure.code == "aws-resource-missing", "control-predecessor-observation-unconfirmed")
                # Deleted stack history expires. Retained physical completion
                # plus removed control/creator roles still fences the lineage.
                continue
            self._require(len(observed) == 1 and observed[0].get("StackId") == stack_id
                and observed[0].get("StackStatus") == "DELETE_COMPLETE", "control-predecessor-stacks-remain")
            reservation = document["operations"].get("delete:" + stack + ":delete")
            self._require(reservation is not None, "control-predecessor-deletion-unconfirmed")
            events = self.setup_provider("cloudformation", "describe-stack-events", StackName=stack_id)
            roots = self.owner.CHANGE_SETS.execution_events(events, reservation["operation_id"], stack_id)
            self._require(any(row.get("ResourceStatus") == "DELETE_COMPLETE" and row.get("ResourceType") == "AWS::CloudFormation::Stack"
                and row.get("LogicalResourceId") == stack for row in roots), "control-predecessor-deletion-unconfirmed")

    def bind_network(self, operations, stack):
        rows = [row for row in operations._plan["stack_parameter_sources"] if row[0] == stack and row[1] == "VpcId"]
        if not rows:
            return {"status": "ready"}
        self._require(self.actor == "foreground" and callable(self.setup_provider) and len(rows) == 1,
            "control-network-binding-prohibited")
        self.require_expiry()
        operations.records.check_input_admission("creation")
        _, _, producer, output = rows[0]
        view = operations.runtime_view(stack=producer, required_outputs=[output])
        vpc = view["outputs"][output]
        self._require(isinstance(vpc, str) and re.fullmatch(r"vpc-[0-9a-f]{8}(?:[0-9a-f]{9})?", vpc),
            "control-network-binding-unconfirmed")
        arn = self.roles["CreationRole"]
        name = arn.rsplit("/", 1)[-1]
        def observed():
            actual = self.provider("iam", "get-role", RoleName=name).get("Role", {})
            self._require(actual.get("Arn") == arn and actual.get("RoleId") == self.role_ids["CreationRole"],
                "control-role-unconfirmed")
            tags = actual.get("Tags", [])
            self._require(isinstance(tags, list) and all(isinstance(row, dict) and set(row) == {"Key", "Value"}
                and isinstance(row["Key"], str) and isinstance(row["Value"], str) for row in tags)
                and len({row["Key"] for row in tags}) == len(tags), "control-network-binding-unconfirmed")
            current = dict((row["Key"], row["Value"]) for row in tags).get("kanbien:session-vpc-id")
            self._require(current in (None, vpc), "control-network-binding-conflict")
            return current == vpc
        if observed():
            return {"status": "ready"}
        fresh = operations.records.reserve_network_binding(operations._task_selections, {"RoleArn": arn, "VpcId": vpc})
        if fresh:
            # This explicit setup hook, not preflight, holds the trusted setup
            # identity. A retained intent never licenses a second submission.
            try:
                self.setup_provider("iam", "tag-role", RoleName=name, Tags=[{"Key": "kanbien:session-vpc-id", "Value": vpc}])
            except Exception:
                pass
        return {"status": "ready"} if observed() else {"status": "pending", "reason": "control-network-binding-unconfirmed"}

    def require_expiry(self):
        execution = self.version.rsplit(":", 1)[0].replace(":stateMachine:", ":execution:") + ":expiry-" + self.binding["session_id"]
        observed = self.provider("stepfunctions", "describe-execution", executionArn=execution)
        self._require(observed.get("executionArn") == execution and observed.get("stateMachineVersionArn") == self.version
            and observed.get("status") == "RUNNING" and observed.get("input") == "{}", "control-expiry-not-armed")


def _command_assembly(*, root, document, environment, operation):
    """Construct cleanup only from native ownership; never load an expired create plan.

    CodeBuild performs cleanup under the qualified worker identity. The trusted
    setup operator can request that same fixed worker, including after expiry,
    but does not receive a local resource-deletion route through this command.
    """
    if not (isinstance(document, dict) and set(document) == {"schema", "intent", "source_inputs_sha256", "choices", "publications"}
            and document["schema"] == "deploy/environment-session-command/v1"
            and isinstance(document["intent"], dict) and isinstance(document["source_inputs_sha256"], str)
            and re.fullmatch(r"[a-f0-9]{64}", document["source_inputs_sha256"])):
        raise TaskAssemblyFailure("command-input-invalid")
    if operation not in ("run", "cleanup"):
        raise TaskAssemblyFailure("command-operation-unsupported")
    root = Path(root)
    owner = module("session_command_operations", root / "scripts/04.deploy/shared/provider-adapters/aws/environment_sessions.py")
    preparation = module("session_command_preparation", root / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
    raw = document["intent"]
    if raw.get("target") != "kanbien-core-platform" or raw.get("scope") not in ("entity-smoke", "core-server-persistence"):
        raise TaskAssemblyFailure("command-target-unsupported")
    clock = lambda: int(datetime.now(timezone.utc).timestamp())
    session = preparation._session_reader()
    read = session.read if operation == "run" else session.read_existing
    intent = read(raw, target=raw["target"], scope=raw["scope"], now=clock(), approved_max_duration_seconds=7200)
    binding = {key: getattr(intent, key) for key in ("target", "scope", "session_id", "starts_at", "expires_at")}
    binding["source_inputs_sha256"] = document["source_inputs_sha256"]
    configuration = preparation.load(root, intent.target, intent.scope)
    base = "infra/04.deploy/03.product/targets/" + intent.target
    profile = preparation.read_document(root, base + "/00-target/target-profile.yml")
    control = preparation.session_control(root, base, profile, "s-" + intent.session_id[:19])
    worker = bool(environment.get("CODEBUILD_BUILD_ARN"))
    if worker and operation != "cleanup":
        raise TaskAssemblyFailure("command-worker-creation-prohibited")
    profile_name = None if worker else configuration["profile"]
    provider = owner.SESSION_CLI.SessionProvider(profile=profile_name, region=configuration["region"], environment=environment)
    qualified = NativeControl(root=root, configuration=configuration, binding=binding, control=control, owner=owner, provider=provider)
    qualified.activate("worker" if worker else "requester", environment=environment)
    qualified.setup_provider = provider if not worker else None
    if operation == "run":
        assumed = provider("sts", "assume-role", RoleArn=qualified.roles["ForegroundRole"],
            RoleSessionName="environment-session-" + intent.session_id, DurationSeconds=min(3600, max(900, intent.expires_at - clock())))
        credentials = assumed.get("Credentials")
        if not (isinstance(credentials, dict) and all(isinstance(credentials.get(key), str) and credentials[key]
                for key in ("AccessKeyId", "SecretAccessKey", "SessionToken"))):
            raise TaskAssemblyFailure("command-credentials-unconfirmed")
        # Native temporary credentials stay in process memory, never in the
        # input, archive, record, report or another persistent configuration.
        environment = {**environment, "AWS_ACCESS_KEY_ID": credentials["AccessKeyId"],
            "AWS_SECRET_ACCESS_KEY": credentials["SecretAccessKey"], "AWS_SESSION_TOKEN": credentials["SessionToken"]}
        environment.pop("AWS_PROFILE", None)
        environment.pop("AWS_DEFAULT_PROFILE", None)
        profile_name = None
        provider = owner.SESSION_CLI.SessionProvider(profile=None, region=configuration["region"], environment=environment)
        qualified.activate("foreground", provider=provider)
    def successor(old, document):
        try:
            return qualified.admit_successor(old, document)
        except TaskAssemblyFailure as failure:
            raise owner.RECORDS.SessionRecordFailure(failure.code) from None
    records = owner.RECORDS.SessionRecords(bucket=qualified.bucket, key=control["record_key"], account=configuration["account"],
        region=configuration["region"], profile=profile_name, environment=environment,
        binding=binding, guard=qualified.guard, clock=clock,
        successor=successor if operation == "run" else None)
    observed = records.observe_existing() if operation == "cleanup" else None
    plan = (preparation.recover_session_plan(root, observed["document"], observed["observed_at"], 7200) if observed is not None
            else preparation.load_session_plan(root, intent.target, intent.scope, raw, clock(), 7200))
    if plan["binding"].source_inputs_sha256 != binding["source_inputs_sha256"]:
        raise TaskAssemblyFailure("command-source-changed")
    operations = owner.SessionOperations(plan, records, provider=provider, preflight=qualified.preflight,
        source_root=root, approved_max_duration_seconds=7200,
        qualified_facts={"qualified-session-control/v1": qualified.fingerprint})
    if observed is not None:
        operations._base(observed["document"])
    choices, publications = document["choices"], document["publications"]
    if observed is not None and (choices != observed["document"]["base"]["choices"] or publications != observed["document"]["base"]["publications"]):
        raise TaskAssemblyFailure("command-selection-mismatch")
    def aws(*parts):
        selected_environment = {**environment, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off", "AWS_IGNORE_CONFIGURED_ENDPOINT_URLS": "true"}
        if profile_name is None:
            selected_environment.pop("AWS_PROFILE", None)
            selected_environment.pop("AWS_DEFAULT_PROFILE", None)
        try:
            value = owner.SESSION_CLI.CLI.invoke_json(["aws", *parts,
                *([] if profile_name is None else ["--profile", profile_name]), "--region", configuration["region"],
                "--output", "json", "--no-cli-pager", "--no-cli-auto-prompt", "--cli-connect-timeout", "10", "--cli-read-timeout", "20"],
                timeout=35, empty_body="reject", object_only=True,
                environment=selected_environment)
            return True, value, "ok"
        except owner.SESSION_CLI.CLI.CliFailure as failure:
            return False, None, failure.code
    tasks = NativeTasks(root=root, plan=plan, operations=operations, owner=owner, aws=aws)
    cleanup = None if worker else NativeCleanup(operations=operations, owner=owner, provider=provider, version_arn=qualified.version)
    return SessionAssembly(plan=plan, operations=operations, owner=owner, tasks=tasks, choices=choices, publications=publications, cleanup=cleanup, control=qualified)


def existing_assembly(*, root, document, environment):
    return _command_assembly(root=root, document=document, environment=environment, operation="cleanup")


def new_assembly(*, root, document, environment):
    return _command_assembly(root=root, document=document, environment=environment, operation="run")


class NativeTasks:
    """Use source-selected workload runners and their retained native journals."""
    def __init__(self, *, root, plan, operations, owner, aws):
        self.root, self.plan, self.operations = Path(root), deepcopy(plan), operations
        self.records, self.owner, self.aws = operations.records, owner, aws
        base = self.root / "scripts/04.deploy/lifecycle"
        self.preparation = module("controller_task_preparation", base / "00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        self.persistence = base / "60-run/targets/kanbien-core-platform/core-server-persistence"
        self.binding = module("controller_persistence_tasks", self.persistence / "task-operations.py")
        self.receipts = module("controller_persistence_receipts", self.persistence / "proof-receipts.py")
        self.native, self.last_result = {}, None
        self.current, self.last_failure = None, None
        self.entity = base / "60-run/targets/kanbien-core-platform/entity-smoke"
        self.entity_runner = module("controller_entity_runner", self.entity / "task-execution/implementation/task-runner.py")
        self.entity_binding = module("controller_entity_binding", self.entity / "task-execution/implementation/task-binding.py")
        self.entity_steps = module("controller_entity_steps", self.entity / "task-execution/implementation/task-steps.py")

    def _require(self, condition, reason):
        if not condition:
            raise TaskAssemblyFailure(reason)

    def _document(self, component, relative):
        target = self.records.binding["target"]
        reference = "infra/04.deploy/03.product/targets/" + target + "/20-scopes/" + component + "/" + relative
        binding = self.plan["binding"]
        captured = dict(binding["source_inputs"] if isinstance(binding, dict) else binding.source_inputs)
        raw = (self.root / reference).read_bytes()
        self._require(captured.get(reference) == hashlib.sha256(raw).hexdigest(), "source-changed")
        return self.preparation.read_document(self.root, reference, capture={reference: raw})

    def provider(self, service, operation, **arguments):
        if service == "ecs" and operation in {"run-task", "list-tasks", "describe-tasks", "stop-task"}:
            return self.binding.TASKS.cli_provider(self.aws)(service, operation, **arguments)
        if (service, operation) == ("logs", "get-log-events"):
            names = {"logGroupName": "log-group-name", "logStreamName": "log-stream-name",
                     "limit": "limit", "nextToken": "next-token"}
            self._require(set(arguments) in ({"logGroupName", "logStreamName", "startFromHead", "limit"},
                {"logGroupName", "logStreamName", "startFromHead", "limit", "nextToken"})
                and arguments["startFromHead"] is True and arguments["limit"] == 1000, "log-selection-invalid")
            command = [service, operation, "--start-from-head"]
            for key, value in arguments.items():
                if key != "startFromHead":
                    command.extend(["--" + names[key], str(value)])
            ok, response, code = self.aws(*command)
            if not ok:
                raise self.owner.SESSION_CLI.SessionProviderFailure(
                    code if code in self.owner.SESSION_CLI.FAILURE_CODES else "aws-command-failed")
            return response
        return self.operations._provider(service, operation, **arguments)

    def _entity_storage(self, component, selection):
        runner, control = self.entity_runner, self.entity_runner.CONTROL
        key = selection["key"]
        def validate(record):
            request = control.validate_request(record["request"])
            return control.AttemptStore.validate_record(key, request, record,
                validate_time=lambda instant: control.AttemptStore.validate_time(None, instant))
        def receipt(label, raw, record):
            self._require(label == runner.receipt_path(None, record["request"], record, storage=True), "receipt-binding-invalid")
            runner.EVIDENCE.validate_retained(json.loads(raw), record)
        storage = self.operations.task_storage(component, key, validate_record=validate,
            validate_receipt=receipt,
            record_selection=lambda record: {"workload": record["request"]["workload"],
                "operation": record["request"]["environment"][control.OPERATIONS[record["request"]["workload"]][0]]},
            key_for_record=lambda selected, request: store.path_for(selected, request),
            before_submit=lambda record: self.operations._admit("task", request=record))
        store = control.AttemptStore(None, storage=storage)
        return storage, store

    def _entity_packet(self, component, selection, *, optional=False):
        storage, _ = self._entity_storage(component, selection)
        record = storage.observe_selected()
        if record is None:
            self._require(optional, "prerequisite-unavailable")
            return None
        label = self.entity_runner.receipt_path(None, record["request"], record, storage=storage)
        receipt = self.entity_runner.read_receipt(label, record, storage=storage)
        self._require(receipt is not None, "prerequisite-unavailable")
        if selection["phase"] != "preflight":
            self.entity_runner.PREFLIGHT.read_admission(None, record, storage=storage)
        return {"reservation": record, "receipt": receipt, "label": selection["label"]}

    def _run_entity(self, component, selection, selected):
        runner = self.entity_runner
        steps = selected["steps"]
        index = steps.index(selection)
        packets = []
        for row in steps[:index]:
            if row["condition"] != "always":
                continue
            packets.append((row, self._entity_packet(component, row)))
        primary = next((packet for row, packet in packets
            if row["workload"] == "verifier" and row["operation"] == "create" and row["phase"] == "operation"), None)
        if selection["condition"] != "always":
            self._require(selection["condition"] == "original-create-terminal-observation"
                          and primary is not None, "condition-unconfirmed")
            return {"status": "skipped"}
        stack = dict(self.plan["stack_names"])[component]
        view = self.operations.runtime_view(stack=stack, required_outputs=[])
        checked = self.entity_binding.inspect(self.provider, selection["workload"], view["parameters"],
            view["resources"], view["template"], runtime_view=view)
        document = self.records.observe_existing()["document"]
        pipeline = dict(dict(self.plan["publication_selections"])[stack])["pipeline"]
        package = document["base"]["packages"][pipeline]["receipt"]
        captured = dict(self.plan["binding"]["source_inputs"] if isinstance(self.plan["binding"], dict)
                        else self.plan["binding"].source_inputs)
        scope = "infra/04.deploy/03.product/targets/" + self.records.binding["target"] + "/20-scopes/" + component
        declaration = self._document(component, "00-declaration/declaration-contract.yml")
        self._document(component, "10-workload-binding/workload-binding.yml")
        binding = {"source_revision": package["source_revision"], "image_digest": package["image_digest"],
            "configuration_contract_sha256": "sha256:" + captured[scope + "/00-declaration/declaration-contract.yml"],
            "permission_contract_sha256": "sha256:" + captured[view["template_reference"]],
            "dependency_incarnation_sha256": self.entity_binding.DEPLOY.fingerprint({
                "resource_id": view["parameters"]["DatabaseResourceId"], "database": view["parameters"]["DatabaseName"], "schema": "entity_smoke"})}
        deadlines = {row["id"].removeprefix("entity-smoke-"): row["completion"]["deadline_seconds"]
                     for row in declaration["health_recovery"]["workloads"] if "completion" in row}
        digest = None
        if selection["operation"] in {"collision", "read"}:
            self._require(primary is not None, "original-record-unavailable")
            digest = primary["receipt"]["result"]["record_digest"]
        args = SimpleNamespace(workload=selection["workload"], operation=selection["operation"],
            phase=selection["phase"], proof_label=selected["proof_label"], proof_stage="baseline", expected_digest=digest)
        context = {"binding": binding, "checked": checked, "completion_deadlines": deadlines,
                   "report": {"plan": {"preflight_label": selection["label"]}}}
        request = self.entity_steps.request(SimpleNamespace(RUNNER=runner), context, args)
        required_after = [document["operation_outcomes"]["creation:" + stack + ":execute"]["observed_at"]]
        if selection["activation"] == "after-activation":
            outcome = document["operation_outcomes"].get("activation:" + stack + ":execute")
            self._require(isinstance(outcome, dict) and outcome["status"] == "UPDATE_COMPLETE", "activation-unconfirmed")
            required_after.append(outcome["observed_at"])
        required_after.extend(packet["receipt"]["task"]["stopped_at"] for _, packet in packets)
        after = max(required_after, key=runner.EVIDENCE.timestamp)
        preflight = None
        if selection["phase"] != "preflight":
            preflight = next((packet for row, packet in packets if row["phase"] == "preflight"
                and (row["workload"], row["operation"]) == (selection["workload"], selection["operation"])), None)
            self._require(preflight is not None, "preflight-unavailable")
            # The probe itself must follow prerequisites; it is not its own prerequisite.
            phase_times = required_after[:2] if selection["activation"] == "after-activation" else required_after[:1]
            after = max([*phase_times, *(packet["receipt"]["task"]["stopped_at"] for _, packet in packets if packet is not preflight)],
                        key=runner.EVIDENCE.timestamp)
        storage, store = self._entity_storage(component, selection)
        submission_entered = False
        def provider(service, operation, **arguments):
            nonlocal submission_entered
            if (service, operation) == ("ecs", "run-task"):
                reservation = store.read(selection["key"], request)
                self._require(reservation is not None
                    and storage.before_submit(store.path_for(selection["key"], request), reservation) is True, "admission-unconfirmed")
                submission_entered = True
            return self.provider(service, operation, **arguments)
        try:
            result = runner.run_owned_task(provider, store, selection["key"], request, None,
                required_after=after, preflight=preflight, evidence_storage=storage)
        except Exception:
            if not submission_entered:
                try:
                    reservation = store.read(selection["key"], request)
                    if reservation is not None:
                        storage.reject_submission(store.path_for(selection["key"], request), reservation)
                except Exception:
                    # Retention uncertainty cannot become proof of no submission.
                    pass
            raise
        return {"status": "succeeded", "reused": result["reused"]}

    def _report(self, verdict, *codes, facts=None, stream=None):
        statuses = {"accepted": "succeeded", "failed": "failed", "pending": "pending", "uncertain": "unknown", "blocked": "blocked"}
        self._require(verdict in statuses, "report-invalid")
        self.last_result = {"status": statuses[verdict], "reasons": list(codes)}
        return 0 if verdict == "accepted" else 1

    def _ordered_binding(self, component, selection, runtime):
        proof, step = selection["proof"], selection["id"]
        kind, mode = proof["proof_type"], proof["operation"]
        self._require(kind in {"migration", "administration", "verifier"}, "proof-unsupported")
        if kind not in self.native:
            folder = {"migration": "run-migration", "administration": "run-administration", "verifier": "verify-candidate"}[kind]
            native = module("controller_native_" + kind, self.persistence / folder / "script.py")
            native.report = self._report
            self.native[kind] = native
        native = self.native[kind]
        selector = {"migration": "PERSISTENCE_MIGRATION_OPERATION", "administration": "PERSISTENCE_ADMINISTRATION_OPERATION", "verifier": "PERSISTENCE_VERIFIER_MODE"}[kind]
        if kind == "verifier":
            validate = lambda value: native.validate_operation(value, mode)
            prefix = native.task_prefix(native.runtime_context(runtime))
            bound = None
        else:
            bound = self.binding.BoundOperation(root=self.root, proof_type=kind, family=runtime["family"],
                container=runtime["container_name"], selector=selector, results={mode: proof["result_code"]},
                aws=self.aws, report=self._report,
                accept=native.accepted_completion if kind == "migration" else native.accept,
                receipts=self.receipts, runtime=runtime, step_id=step)
            validate = lambda value: bound.validate_record(value, mode)
            prefix = bound.task_prefix({"runtime": runtime})
        def validate_receipt(label, raw, record):
            receipt = self.receipts._decode(raw, task_arn_prefix=prefix)
            self._require(label == self.receipts._label(receipt)
                and receipt["proof_type"] == kind and receipt["operation"] == mode
                and receipt["task"]["arn"] == record["task_arn"]
                and receipt["task"]["definition"] == record["request"]["task_definition"], "receipt-binding-invalid")
        storage = self.operations.task_storage(component, step, validate_record=validate,
            validate_receipt=validate_receipt,
            record_selection=lambda value: {"workload": selection["workload"], "proof_type": kind, "operation": value["mode"]},
            before_submit=lambda record: self.operations._admit("task", request=record))
        if bound is not None:
            bound.storage = storage
        return native, bound, storage, selector

    def run(self, component, selection):
        self.current, self.last_result, self.last_failure = None, None, None
        selected = dict(self.plan["task_selections"]).get(component)
        self._require(selected is not None and selection in selected["steps"], "selection-invalid")
        self.current = {"component": component, "step": selection.get("id", selection.get("key"))}
        if selected["kind"] == "entity-smoke-baseline/v1":
            self.last_result = self._run_entity(component, selection, selected)
            return self.last_result
        self._require(selected["kind"] == "ordered-commands/v1", "consumer-unavailable")
        workload = self._document(component, "10-workload-binding/workload-binding.yml")
        declaration = self._document(component, "00-declaration/declaration-contract.yml")
        definition = next(row for row in workload["workloads"] if row["id"] == selection["workload"])
        stacks = dict(self.plan["stack_names"])
        template = json.loads(dict(self.plan["projected_templates"])[dict(self.plan["stack_templates"])[stacks[component]]])
        # Native role checks bind database attributes to their declared outputs.
        databases = {key for key, row in template["Resources"].items() if row["Type"] == "AWS::RDS::DBInstance"}
        required = []
        for name, row in template.get("Outputs", {}).items():
            value = row.get("Value")
            attribute = value.get("Fn::GetAtt") if isinstance(value, dict) else None
            parts = attribute.split(".", 1) if isinstance(attribute, str) else attribute
            if isinstance(parts, list) and len(parts) == 2 and parts[0] in databases:
                required.append(name)
        view = self.operations.runtime_view(stack=stacks[component], required_outputs=required)
        group = definition["security_group"]
        related = () if group["component"] == component else (self.operations.runtime_view(
            stack=stacks[group["component"]], required_outputs=[group["output"]]),)
        checked = self.binding.checked_runtime(self.provider, view=view, workload_binding=workload,
            workload=selection["workload"], related_views=related)
        runtime = checked["runtime"]
        proof = selection["proof"]
        rows = [row for row in declaration["health_recovery"]["workloads"] if row["id"] == proof["deadline_workload"]]
        self._require(len(rows) == 1, "deadline-invalid")
        seconds = rows[0]["completion"]["deadline_seconds"]
        self._require(type(seconds) is int and seconds > 0, "deadline-invalid")
        native, bound, storage, selector = self._ordered_binding(component, selection, runtime)
        network = json.dumps({"awsvpcConfiguration": {"subnets": checked["subnets"],
            "securityGroups": [checked["security_group"]], "assignPublicIp": "DISABLED"}}, separators=(",", ":"))
        environment = [{"name": selector, "value": proof["operation"]}]
        if bound is None:
            environment.extend([{"name": "PERSISTENCE_ACCEPTANCE_RECORD_ID", "value": native.RECORD_ID},
                                {"name": "PERSISTENCE_ACCEPTANCE_FACT", "value": native.FACT}])
        overrides = json.dumps({"containerOverrides": [{"name": runtime["container_name"],
            "environment": environment}]}, separators=(",", ":"))
        self.last_result = None
        if bound is None:
            native.execute_reserved(SimpleNamespace(mode=proof["operation"], expected_operation="none", new_operation=False),
                seconds, checked["definition"], network, overrides, runtime=runtime, provider=self.aws,
                storage=storage, step_id=selection["id"])
        else:
            bound.run(mode=proof["operation"], definition=checked["definition"], network=network,
                overrides=overrides, seconds=seconds)
        return self.last_result or {"status": "unknown", "reason": "environment-session-task-report-unavailable"}

    def _stop_owned(self, storage, record, task):
        runtime = record["request"]["runtime"]
        definition = record["request"].get("definition", record["request"].get("task_definition"))
        def exact(observed):
            self._require(observed.get("taskArn") == task.get("taskArn")
                and observed.get("taskDefinitionArn") == definition
                and observed.get("startedBy") == record["operation_id"], "identity-unconfirmed")
            return observed
        exact(task)
        if task.get("lastStatus") == "STOPPED":
            return True
        request = {"cluster": runtime["cluster_arn"], "task": task["taskArn"],
                   "definition": definition, "operation_id": record["operation_id"]}
        observed = self.binding.TASKS.replace_task(self.provider,
            SimpleNamespace(reserve=storage.reserve_stop), phase="cleanup-stop", request=request,
            cluster=request["cluster"], original=request["task"], reason=lambda _: "temporary-session-cleanup",
            precondition=lambda _: self.operations._admit("stop-task", request=request),
            observe=lambda _: self.binding.TASKS.describe_task(self.provider,
                cluster=request["cluster"], arn=request["task"], validate_task=exact))
        return observed.get("lastStatus") == "STOPPED"

    def reconcile(self):
        state = self.records.observe_task_state(self.operations._task_selections)
        for selection, slot in zip(state["selections"], state["slots"], strict=True):
            if slot is None:
                continue
            if selection["kind"] == "entity-smoke-baseline/v1":
                storage, _ = self._entity_storage(selection["component"], selection["selection"])
                record = storage.observe_selected()
                self._require(record is not None, "record-changed")
                if slot["admission"] == "not-submitted" or slot["admission"] is None and storage.close_unadmitted():
                    continue
                label = self.entity_runner.receipt_path(None, record["request"], record, storage=storage)
                if self.entity_runner.read_receipt(label, record, storage=storage) is not None:
                    continue
                _, task = self.entity_runner.CONTROL.reconcile_reserved(self.provider, record)
                if not self._stop_owned(storage, record, task):
                    return {"status": "pending", "reason": "environment-session-task-not-terminal"}
                continue
            record = json.loads(self.records._read_child(slot["current"]), object_pairs_hook=self.owner.RECORDS._duplicate_safe)
            self._require(selection["kind"] == "ordered-commands/v1", "consumer-unavailable")
            native, bound, storage, _ = self._ordered_binding(selection["component"], selection["selection"], record["request"]["runtime"])
            self._require(storage.read(selection["step"]) == record, "record-changed")
            if slot["admission"] == "not-submitted" or slot["admission"] is None and storage.close_unadmitted():
                continue
            proof = bound.completion(record) if bound is not None else native.retained_completion(record, storage=storage)
            if proof is not None:
                continue
            runtime = record["request"]["runtime"]
            def exact(task):
                self._require(task.get("taskDefinitionArn") == record["request"]["task_definition"]
                    and task.get("startedBy") == record["operation_id"]
                    and (record["task_arn"] is None or task.get("taskArn") == record["task_arn"]), "identity-unconfirmed")
                return task
            if record["task_arn"] is None:
                task = self.binding.TASKS.reconcile_task(self.provider, cluster=runtime["cluster_arn"],
                    definition=record["request"]["task_definition"], operation_id=record["operation_id"], validate_task=exact)
            else:
                task = self.binding.TASKS.describe_task(self.provider, cluster=runtime["cluster_arn"], arn=record["task_arn"], validate_task=exact)
            if not self._stop_owned(storage, record, task):
                return {"status": "pending", "reason": "environment-session-task-not-terminal"}
        return {"status": "ready"}

    def failure_code(self, failure):
        if isinstance(failure, TaskAssemblyFailure):
            return failure.code
        runner = self.entity_runner
        if isinstance(failure, (runner.RunnerFailure, runner.CONTROL.TaskFailure,
                runner.EVIDENCE.EvidenceFailure, runner.PREFLIGHT.PreflightFailure,
                self.entity_binding.BindingFailure, self.entity_steps.StepFailure)):
            if isinstance(failure, runner.EVIDENCE.EvidenceFailure):
                self.last_failure = runner.EVIDENCE.failure_report(failure)
            return failure.code
        return "environment-session-task-operation-unconfirmed"

    def report_context(self):
        return {**({"task": deepcopy(self.current)} if self.current is not None else {}),
                **({"diagnostics": deepcopy(self.last_failure)} if self.last_failure else {})}


class NativeCleanup:
    """Fixed worker handoff; construction still requires the qualified factory.

    The immutable functional report reserves this exact invocation before send.
    Cold workers observe it only; the separately armed expiry remains the fallback
    when a foreground worker dies between retaining its report and submission.
    """
    def __init__(self, *, operations, owner, provider, version_arn):
        self.operations, self.records, self.owner, self.provider = operations, operations.records, owner, provider
        base = "arn:aws:states:" + self.records.region + ":" + self.records.account
        machine = "s-" + self.records.binding["session_id"][:19] + "-expiry"
        if not (isinstance(version_arn, str) and re.fullmatch(re.escape(base + ":stateMachine:" + machine) + r":[1-9][0-9]*", version_arn)):
            raise TaskAssemblyFailure("cleanup-worker-binding-invalid")
        name = "cleanup-" + self.records.binding["session_id"]
        self.execution = base + ":execution:" + machine + ":" + name
        self.request = {"stateMachineArn": version_arn, "name": name, "input": '{"cleanup_now":true}'}

    def intent(self):
        return {"service": "stepfunctions", "operation": "start-execution", "arguments": deepcopy(self.request)}

    def advance(self, *, submit):
        completed = self.records.observe_cleanup_completion()
        if completed is not None:
            return completed
        if submit:
            self.operations._admit("cleanup-worker-start", arguments=self.request)
            try:
                response = self.provider("stepfunctions", "start-execution", **self.request)
                if response.get("executionArn") != self.execution:
                    raise TaskAssemblyFailure("cleanup-worker-binding-invalid")
            except self.owner.SESSION_CLI.SessionProviderFailure:
                # Observe the reserved execution after any transport uncertainty.
                pass
        try:
            observed = self.provider("stepfunctions", "describe-execution", executionArn=self.execution)
        except self.owner.SESSION_CLI.SessionProviderFailure:
            return {"status": "unknown", "reason": "cleanup-worker-start-unconfirmed", "execution": self.execution}
        if not (observed.get("executionArn") == self.execution
                and observed.get("stateMachineVersionArn") == self.request["stateMachineArn"]
                and observed.get("input") == self.request["input"]):
            raise TaskAssemblyFailure("cleanup-worker-binding-invalid")
        status = observed.get("status")
        if status == "RUNNING":
            return {"status": "pending", "reason": "cleanup-worker-running", "execution": self.execution}
        if status in ("SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED", "PENDING_REDRIVE"):
            # A successful hosting workflow is not physical-cleanup evidence.
            completed = self.records.observe_cleanup_completion()
            return completed or {"status": "blocked", "reason": "cleanup-worker-ended-without-completion", "execution": self.execution}
        raise TaskAssemblyFailure("cleanup-worker-observation-invalid")


class SessionAssembly:
    def __init__(self, *, plan, operations, owner, tasks, choices, publications, cleanup=None, control=None):
        self.plan = deepcopy(plan)
        self.operations, self.records, self.owner = operations, operations.records, owner
        self.tasks = tasks
        self.choices, self.publications = deepcopy(choices), deepcopy(publications)
        self.cleanup, self._fresh_cleanup = cleanup, False
        self.control = control

    def prepare_stack(self, stack):
        return {"status": "ready"} if self.control is None else self.control.bind_network(self.operations, stack)

    def initialize(self):
        return self.operations.initialize(choices=self.choices, publications=self.publications)

    def functional_result(self):
        document = self.records.observe_existing()["document"]
        report = self.records.read_report(self.operations._task_selections, "functional")
        if report is None:
            return document["functional_result"]
        result = report.get("functional")
        if not (isinstance(result, dict) and set(result) in ({"status"}, {"status", "reason"})
                and result["status"] in ("succeeded", "failed", "interrupted")
                and ("reason" not in result or isinstance(result["reason"], str) and 0 < len(result["reason"]) <= 256)):
            raise TaskAssemblyFailure("functional-report-invalid")
        if document["functional_result"] is not None and document["functional_result"]["status"] != result["status"]:
            raise TaskAssemblyFailure("functional-report-conflict")
        return deepcopy(result)

    def retain_functional(self, result):
        status = {"status": result["status"]}
        previous = self.records.read_report(self.operations._task_selections, "functional")
        if previous is not None:
            if previous["functional"]["status"] != status["status"]:
                raise TaskAssemblyFailure("functional-report-conflict")
        else:
            report = {"functional": deepcopy(result), **self.tasks.report_context()}
            if self.cleanup is not None:
                report["cleanup_invocation"] = self.cleanup.intent()
            if self.records.retain_report(self.operations._task_selections, "functional", report) is True:
                self._fresh_cleanup = self.cleanup is not None
        return self.records.retain_functional(status)

    def handoff_cleanup(self):
        if self.cleanup is None:
            return None
        report = self.records.read_report(self.operations._task_selections, "functional")
        if self._fresh_cleanup and (report is None or report.get("cleanup_invocation") != self.cleanup.intent()):
            raise TaskAssemblyFailure("cleanup-worker-intent-invalid")
        submit, self._fresh_cleanup = self._fresh_cleanup, False
        return self.cleanup.advance(submit=submit)

    def retain_cleanup(self, result):
        if self.cleanup is not None:
            # Only the actual worker retains the authoritative cleanup report.
            return
        report = {"status": "completed", "reference": result["reference"]} if result["status"] == "completed" else result
        self.records.retain_report(self.operations._task_selections, "cleanup", deepcopy(report))

    def run_task(self, component, selection):
        return self.tasks.run(component, selection)

    def reconcile_tasks(self):
        return self.tasks.reconcile()

    def complete_cleanup(self):
        return self.operations.complete_cleanup()

    def failure_code(self, failure):
        # Only the actual imported owners' exception types can supply reasons.
        # Unknown exceptions and attributes never become user-facing content.
        if isinstance(failure, (self.owner.SessionOperationFailure, self.owner.RECORDS.SessionRecordFailure)):
            return failure.code
        if isinstance(failure, self.owner.SESSION_CLI.SessionProviderFailure):
            return failure.code if failure.code in self.owner.SESSION_CLI.FAILURE_CODES else "aws-command-failed"
        return self.tasks.failure_code(failure)
