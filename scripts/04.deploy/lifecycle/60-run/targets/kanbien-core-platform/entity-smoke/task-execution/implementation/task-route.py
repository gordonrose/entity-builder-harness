#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.task-plan.implementation
#   version: 5
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Plan and explicitly admit one initial preparation task using exact source/custody/deployed bindings, actual preflight receipts and durable no-replay controls.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).resolve().parents[2]
C = module("entity_smoke_task_route_common", DIRECTORY / "orchestration/commands/script.py")
BINDING = module("entity_smoke_task_route_binding", DIRECTORY / "task-execution/implementation/task-binding.py")
GRAPH = C.GRAPH
RUNNER = module("entity_smoke_task_route_runner", DIRECTORY / "task-execution/implementation/task-runner.py")
STEPS = module("entity_smoke_task_route_steps", DIRECTORY / "task-execution/implementation/task-steps.py")
FEATURE = module("entity_smoke_task_route_feature", DIRECTORY / "orchestration/implementation/feature-steps.py")
RECOVERY = module("entity_smoke_task_route_recovery", DIRECTORY / "recovery-and-replacement/recovery-state/recovery-steps.py")
CREDENTIAL = module("entity_smoke_task_route_credential", DIRECTORY / "controls-and-readiness/implementation/credential-steps.py")
COMPLETION = module("entity_smoke_task_route_completion", DIRECTORY / "task-execution/implementation/task-completion.py")
HISTORY = module("entity_smoke_task_route_history", DIRECTORY / "recovery-and-replacement/recovery-state/recovery-history.py")
ACCEPTANCE = module("entity_smoke_task_route_acceptance", DIRECTORY / "acceptance-evaluation/implementation/acceptance-steps.py")
IMAGE_REPAIR = module("entity_smoke_task_image_repair", DIRECTORY / "image-delivery-repair/implementation/image-delivery-repair.py")
RULE = C.ROOT / ".agentic/aws/standards/operational-realization-applicability.md"
# Share the actual read vocabulary with transport retry and safe diagnosis.
# Mutation admission remains exclusively in this route's guarded RunTask path.
READS = C.READS
EFFECTS = {
    "preflight": "read-only-connection-observation", "ready": "read-only-http-observation", "unready": "read-only-http-observation",
    "observe-permissions": "read-only-permission-observation", "observe-migration-state": "read-only-migration-observation",
    "read": "read-only-original-record-observation", "observe-create": "read-only-original-record-observation",
    "bootstrap": "fixed-role-and-schema-provisioning", "grant-runtime": "fixed-feature-dml-grants", "apply": "checksummed-feature-migration",
    "revoke-runtime": "fixed-runtime-login-revocation", "restore-runtime": "fixed-runtime-login-restoration",
    "permissions": "rolled-back-denial-probes", "collision": "rolled-back-collision-probe",
    "create": "new-labelled-synthetic-record", "lifecycle": "labelled-synthetic-lifecycle-exercise", "cleanup": "labelled-synthetic-logical-delete",
}


class TaskRouteFailure(Exception):
    def __init__(self, code, item=None):
        super().__init__(code)
        self.code, self.item = code, item


class CurrentTaskFailure(TaskRouteFailure):
    """Distinguish this invocation's task from failed prerequisite evidence."""
    def __init__(self, evidence):
        super().__init__(evidence.code)
        self.evidence = evidence


def require(value, code):
    if not value: raise TaskRouteFailure(code)


def dependencies():
    return SimpleNamespace(C=C, RUNNER=RUNNER, BINDING=BINDING, GRAPH=GRAPH, STEPS=STEPS, FEATURE=FEATURE, RECOVERY=RECOVERY, CREDENTIAL=CREDENTIAL, COMPLETION=COMPLETION, ACCEPTANCE=ACCEPTANCE, IMAGE_REPAIR=IMAGE_REPAIR, re=re, owned_stack=owned_stack, dependencies=dependencies)


class Provider(C.Provider):
    """Read-only until the owning approved route supplies one closed RunTask."""
    def __init__(self):
        super().__init__()
        self.task_capability = None

    def enable_task(self, request, store, key, guard):
        require(self.task_capability is None and self.effect == "not-started", "task-capability-already-used")
        RUNNER.CONTROL.validate_request(request)
        self.task_capability = (request, store, key, guard)

    def __call__(self, service, operation, **parameters):
        if (service, operation) == ("ecs", "run-task"):
            try:
                require(self.task_capability is not None, "task-provider-operation-prohibited")
                request, store, key, guard = self.task_capability
                reserved = store.read(key, request)
                require(reserved is not None, "task-submission-reservation-required")
                expected = {"cluster": C.RESOURCE.CLUSTER, "taskDefinition": request["definition"], "launchType": "FARGATE", "count": 1,
                            "networkConfiguration": {"awsvpcConfiguration": {"subnets": request["subnets"], "securityGroups": [request["security_group"]], "assignPublicIp": "DISABLED"}},
                            "overrides": RUNNER.CONTROL.overrides(request), "startedBy": reserved["operation_id"], "clientToken": reserved["operation_id"]}
                require(RUNNER.CONTROL.canonical(parameters) == RUNNER.CONTROL.canonical(expected), "task-submission-does-not-match-plan")
                guard()
            except Exception as failure:
                code = failure.code if isinstance(failure, (TaskRouteFailure, C.InfrastructureFailure, C.ALIGN.AlignmentFailure, C.GATE.ContractFailure, C.RESOURCE.ResourceFailure,
                                                            BINDING.BindingFailure, STEPS.StepFailure, FEATURE.FeatureStepFailure, CREDENTIAL.CredentialFailure, ACCEPTANCE.AcceptanceFailure, RUNNER.CONTROL.TaskFailure, RUNNER.EVIDENCE.EvidenceFailure, RUNNER.PREFLIGHT.PreflightFailure) + RECOVERY.failures()) else "task-submission-preflight-not-confirmed"
                recovery_item = RECOVERY.failure_item(failure)
                field = failure.field if isinstance(failure, BINDING.BindingFailure) else "prerequisite" if isinstance(failure, STEPS.PrerequisiteMissing) or recovery_item is not None else None
                item = failure.item if isinstance(failure, (BINDING.BindingFailure, STEPS.PrerequisiteMissing)) else recovery_item
                workload = failure.workload if isinstance(failure, BINDING.BindingFailure) else None
                if isinstance(failure, ACCEPTANCE.AcceptanceFailure):
                    field, item, workload = (failure.context.get(key) for key in ("field", "item", "affected_workload"))
                raise RUNNER.CONTROL.SubmissionNotStarted(code, field, item, workload) from None
            self.task_capability = None
            self.effect = "unknown-reconcile-only"
        else:
            require((service, operation) in READS, "task-provider-operation-prohibited")
        return self._invoke(service, operation, parameters)


def operator(provider, definition, roles):
    caller = provider("sts", "get-caller-identity")
    arn = caller.get("Arn") if isinstance(caller, dict) else None
    require(caller.get("Account") == C.ALIGN.ACCOUNT and isinstance(arn, str) and re.fullmatch(r"arn:aws:sts::" + C.ALIGN.ACCOUNT + r":assumed-role/[A-Za-z0-9+=,.@_-]+/[A-Za-z0-9+=,.@_-]+", arn) is not None, "task-operator-not-confirmed")
    name = arn.split("/")[1]
    value = provider("iam", "get-role", RoleName=name).get("Role")
    require(isinstance(value, dict) and value.get("RoleName") == name and isinstance(value.get("Arn"), str) and value["Arn"].startswith("arn:aws:iam::" + C.ALIGN.ACCOUNT + ":role/") and value["Arn"].endswith("/" + name), "task-operator-not-confirmed")
    for action, resources in (("ecs:RunTask", [definition]), ("iam:PassRole", roles)):
        require(C.operator_resources_allowed(provider, value["Arn"], action, resources, context=[
            {"ContextKeyName": "ecs:cluster", "ContextKeyValues": ["arn:aws:ecs:" + C.ALIGN.REGION + ":" + C.ALIGN.ACCOUNT + ":cluster/" + C.RESOURCE.CLUSTER], "ContextKeyType": "string"},
            {"ContextKeyName": "iam:PassedToService", "ContextKeyValues": ["ecs-tasks.amazonaws.com"], "ContextKeyType": "string"}]), "task-operator-policy-preflight-not-confirmed")
    return C.DEPLOY.fingerprint({"account": caller["Account"], "role": value["Arn"]})


def owned_stack(provider, binding, parameters, cache, *, delivery=None, rollback=False):
    if delivery is not None:
        selected = {**parameters, "ServerDesiredCount": "1"}
        checked = C.completed_deployment(provider, binding, selected, delivery, rollback=rollback)
        require(checked["cache"] == cache, "task-delivery-cache-mismatch")
        return selected, checked["resources"]
    retained = C.read_json(cache / "receipts/create.json")
    transition = C.TRANSITION.read(C, cache, binding)
    creation_binding = transition["plan"]["previous_binding"] if transition else binding
    require(isinstance(retained, dict) and set(retained) == {"schema", "binding", "result"} and retained.get("schema") == "deploy/entity-smoke-infrastructure-receipt/v1"
            and retained.get("binding") == creation_binding and isinstance(retained.get("result"), dict) and retained["result"].get("status") == "completed", "task-created-infrastructure-required")
    current = C.RESOURCE.only(provider("cloudformation", "describe-stacks", StackName=C.DEPLOY.STACK), "Stacks")
    C.DEPLOY.exact_stack(current, binding)
    rows = current.get("Parameters")
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), "task-infrastructure-not-confirmed")
    count = [row.get("ParameterValue") for row in rows if row.get("ParameterKey") == "ServerDesiredCount"]
    require(len(count) == 1 and count[0] in {"0", "1"}, "task-infrastructure-not-confirmed")
    selected = {**parameters, "ServerDesiredCount": count[0]}
    C.DEPLOY.parameters_for(binding, selected, count[0] == "1")
    creation = retained["result"].get("reservation")
    require(isinstance(creation, dict) and isinstance(creation.get("request"), dict), "task-creation-reservation-required")
    creation_request = creation["request"]
    expected_creation = C.DEPLOY.request(creation_binding, {**parameters, "ServerDesiredCount": "0", "SourceRevision": creation_binding["source_revision"], "ImageDigest": creation_binding["image_digest"]}, False)
    require(all(creation_request.get(key) == value for key, value in expected_creation.items()), "task-creation-reservation-mismatch")
    control_store = C.RESOURCE.ResourceStore(cache / "attempts")
    require(control_store.read("deploy-execute-create", creation_request) == creation, "task-creation-reservation-not-retained")
    actual = C.DEPLOY.deployed_stack(provider, binding, selected)
    require(actual.get("StackStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"}, "task-infrastructure-not-confirmed")
    response = provider("cloudformation", "list-stack-resources", StackName=actual["StackId"])
    resources = response.get("StackResourceSummaries") if isinstance(response, dict) else None
    require(isinstance(resources, list) and len(resources) == len(C.DEPLOY.RESOURCE_TYPES) and not response.get("NextToken")
            and all(isinstance(row, dict) and all(isinstance(row.get(key), str) and row[key] for key in ("LogicalResourceId", "ResourceType", "PhysicalResourceId")) for row in resources), "task-infrastructure-not-confirmed")
    observed = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]} for row in resources}
    expected_resources = transition["resources"] if transition else retained["result"]["facts"].get("resources")
    require(len(observed) == len(resources) and isinstance(retained["result"].get("facts"), dict) and expected_resources == observed
            and retained["result"]["facts"].get("stack_arn") == actual["StackId"], "task-infrastructure-lineage-not-confirmed")
    return selected, observed


def prepare(args, provider, *, retained_source_evidence=None):
    provider = BINDING.observation_scope(provider)
    proof_stage = STEPS.stage(args)
    receipt = C.ALIGN.read_receipt(args.receipt.absolute())
    if retained_source_evidence is None and proof_stage == "acceptance":
        retained_source_evidence = ACCEPTANCE.acceptance_owner().retained_source_evidence(args, receipt)
    C.ALIGN.source_preflight(receipt, **({"retained_source_evidence": retained_source_evidence} if retained_source_evidence is not None else {}))
    artifact = C.source_digest()
    if proof_stage == "activation": args.activation_generation = artifact
    alignment, parameters, _ = C.ALIGN.inspect(provider, receipt, C.now())
    binding = {**C.binding_for(receipt, alignment), "proof_label": args.proof_label}
    delivery = C.delivery_context(args, receipt, binding)
    rollback = proof_stage == "rollback"
    if rollback:
        binding, _ = C.rollback_selection(args, delivery, binding)
        parameters.update(ImageDigest=binding["image_digest"], SourceRevision=binding["source_revision"])
    cache = C.delivery_cache(args.proof_label, delivery)
    C.filesystem_preflight(cache)
    declaration = GRAPH.contract(args.workload, C.GATE, negative=CREDENTIAL.negative(args))
    artifacts = {item["id"]: artifact if item["id"] == GRAPH.CONTROLLER_SOURCE else binding["image_digest"] for item in declaration["artifacts"]}
    book = C.GateBook(artifact, cache / "task-realization", contract=declaration, artifact_bindings=artifacts)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration")
    selected, resources = owned_stack(provider, binding, parameters, cache, **({"delivery": delivery, "rollback": rollback} if delivery else {}))
    binding_snapshot = BINDING.DEPLOY.source()[1]
    checked = BINDING.inspect(provider, args.workload, selected, resources, binding_snapshot)
    callees = {"server": BINDING.inspect(provider, "server", selected, resources, binding_snapshot)} if args.workload == "verifier" else {}
    expected = BINDING.expected_task(args.workload, selected, resources, binding_snapshot)
    roles = [expected["executionRoleArn"], *([] if "taskRoleArn" not in expected else [expected["taskRoleArn"]])]
    actor = operator(provider, checked["definition"], roles)
    stage_suffix = "" if proof_stage == "baseline" else ":" + proof_stage
    if proof_stage == "activation": stage_suffix += ":" + artifact
    preflight_label = "entity-smoke-" + hashlib.sha256((args.proof_label + ":" + args.workload + ":" + args.operation + ":preflight" + stage_suffix).encode()).hexdigest()[:24]
    if delivery:
        preflight_label = C.delivery_preflight_label(delivery, proof_stage, args.workload, args.operation)
    else:
        preflight_label = IMAGE_REPAIR.recovery_label({"cache": cache, "binding": binding, "checked": checked}, args, preflight_label)
        preflight_label = C.TRANSITION.recovery_preflight(C, {"cache": cache, "binding": binding}, args, preflight_label)
    actual_operation = ("ready" if args.workload == "verifier" else "preflight") if args.phase == "preflight" else args.operation
    safe = {"schema": "deploy/entity-smoke-task-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "account": C.ALIGN.ACCOUNT, "region": C.ALIGN.REGION,
            "workload": args.workload, "phase": args.phase, "operation": actual_operation, "prepared_operation": args.operation, "proof_stage": proof_stage, "preflight_label": preflight_label,
            "database_effect": EFFECTS[actual_operation], "expected_record_digest": args.expected_digest,
            "binding": binding, "controller_sha256": artifact, "graph_sha256": C.DEPLOY.fingerprint(declaration),
            "parameters_sha256": C.DEPLOY.fingerprint(selected), "template_sha256": C.digest_file(C.DEPLOY.SOURCE), "preflight_rule_sha256": C.digest_file(RULE),
            "operator_sha256": actor, "task_definition_sha256": C.DEPLOY.fingerprint(checked["definition"]), "configuration_sha256": checked["configuration_sha256"],
            "roles_sha256": checked["roles_sha256"], "network_sha256": checked["network_sha256"], "callee_bindings_sha256": C.DEPLOY.fingerprint(callees), "package_custody_reference": receipt["receipt_reference"],
            "task_count": 1, "automatic_retry": False}
    if delivery: safe.update(schema="deploy/entity-smoke-task-plan/v2", delivery=delivery)
    declaration = C.yaml.safe_load((C.CONTRACT.parent / "declaration-contract.yml").read_text())
    deadlines = {row["id"].removeprefix("entity-smoke-"): row["completion"]["deadline_seconds"] for row in declaration["health_recovery"]["workloads"] if "completion" in row}
    context = {"report": {"plan": safe}, "book": book, "cache": cache, "binding": binding, "checked": checked,
               "parameters": selected, "resources": resources, "artifact": artifact, "custody": receipt, "callees": callees, "completion_deadlines": deadlines, "binding_snapshot": binding_snapshot,
               "retained_source_evidence": retained_source_evidence}
    if delivery: context["delivery"] = delivery
    STEPS.select_preflight(dependencies(), context, args, provider)
    # Missing prior work is visible in a plan, not manufactured as success.
    missing = None
    try: prerequisites = STEPS.prerequisites(dependencies(), context, args, provider)
    except STEPS.PrerequisiteMissing as failure:
        prerequisites, missing = None, failure.item
    custody = STEPS.prerequisite_custody(C, prerequisites) if delivery else prerequisites
    safe["prerequisites_sha256"] = None if prerequisites is None else C.DEPLOY.fingerprint(custody)
    safe["pending_prerequisite"] = missing
    safe["execution_route_available"] = (STEPS.selected(args) is not None or FEATURE.supported(args) or RECOVERY.supported(args) or CREDENTIAL.supported(args) or ACCEPTANCE.supported(args)) and prerequisites is not None
    context["prerequisites"] = prerequisites
    safe["request_sha256"] = C.DEPLOY.fingerprint(STEPS.request(dependencies(), context, args))
    if delivery and "preflight_renewal" in safe:
        STEPS.validate_renewal(dependencies(), safe, binding, delivery, args)
    selected_digest = C.DEPLOY.fingerprint(safe)
    book.bind_plan(selected_digest)
    # These are actual prepared source/artifact/configuration/permission/target
    # observations through gate five, not a claim that a task has run or that
    # database access, execution-preflight or business completion has passed.
    for identifier in book.known: book.component(identifier)
    book.gate("live-read"); book.gate("change-set"); evidence = book.validate("change-set", 1)
    report = {"verdict": "planned", "plan": safe, "plan_sha256": selected_digest, "realization_evidence": str(evidence.relative_to(C.ROOT)), "effect": "not-started"}
    context["report"] = report
    return context


def plan(args, provider):
    return prepare(args, provider)["report"]


def execute(args, provider):
    context = prepare(args, provider)
    report, book = context["report"], context["book"]
    safe = report["plan"]
    require(args.approved_plan == report["plan_sha256"], "task-approved-plan-mismatch")
    if not safe["execution_route_available"]:
        raise TaskRouteFailure("task-prerequisite-required", safe["pending_prerequisite"]) if safe["pending_prerequisite"] is not None else TaskRouteFailure("task-execution-prerequisites-not-connected")
    runner, deps = RUNNER, dependencies()
    step_path = STEPS.path(context, args)
    if context.get("delivery") and COMPLETION.path(step_path).is_file():
        packet = STEPS.observe_packet(deps, context, args, provider, historical=True)
        completion = COMPLETION.read(deps, context, args, step_path)
        provider.effect = "historical-task-completion-validated"
        return {"verdict": "completed", "plan_sha256": packet["plan_sha256"],
            "reconciliation_plan_sha256": report["plan_sha256"], "receipt": str(step_path.relative_to(C.ROOT)),
            "realization_evidence": completion["realization_evidence"], "effect": provider.effect, "reused": True}
    history = HISTORY.reconcile(deps, {**context, "provider": provider}, args)
    if history is not None:
        step_path = STEPS.path(context, args)
        packet, completion = C.read_json(step_path), C.read_json(COMPLETION.path(step_path))
        return {"verdict": "completed", "plan_sha256": packet["plan_sha256"],
                "reconciliation_plan_sha256": report["plan_sha256"], "receipt": str(step_path.relative_to(C.ROOT)),
                "realization_evidence": completion["realization_evidence"], "effect": provider.effect,
                "reused": True, "credential_history": str(history.relative_to(C.ROOT))}
    request = STEPS.request(deps, context, args)
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    key = STEPS.key(args, context.get("delivery"))
    previous = store.read(key, request)
    if not context.get("delivery"): C.TRANSITION.require_existing_attempt(C, args.proof_label, previous)
    negative = CREDENTIAL.negative(args)
    preflight = None
    if negative:
        try: runner.UNREADY.validate_launch(request, context["prerequisites"]["revocation"])
        except runner.UNREADY.UnreadyFailure as failure: raise TaskRouteFailure(failure.code) from None
    elif args.phase == "operation":
        if previous is None:
            probe_args = SimpleNamespace(**{**vars(args), "phase": "preflight"})
            packet = STEPS.observe_packet(deps, context, probe_args, provider, historical=True)
            require(packet is not None, "task-preflight-receipt-required")
            preflight = {"reservation": packet["reservation"], "receipt": packet["receipt"], "label": safe["preflight_label"]}
            runner.PREFLIGHT.require_receipt(request, packet["reservation"], packet["receipt"], expected_preflight_label=safe["preflight_label"], current_time=datetime.now(timezone.utc).isoformat(), required_after=context["prerequisites"]["required_after"])
        else:
            # Resume proves the original admission, never demands or relaunches
            # a new preflight merely because the old freshness window elapsed.
            runner.PREFLIGHT.read_admission(context["cache"] / "task-receipts", previous)
        book.gate("execution-preflight"); book.validate("execution-preflight", 1)
    else:
        runner.PREFLIGHT.validate_launch(request)

    def source_guard():
        require(C.source_digest() == context["artifact"] and C.digest_file(RULE) == safe["preflight_rule_sha256"]
                and C.DEPLOY.fingerprint(GRAPH.contract(args.workload, C.GATE, negative=negative)) == safe["graph_sha256"]
                and C.digest_file(C.ROOT / C.ALIGN.SCOPE) == context["binding"]["configuration_contract_sha256"], "task-source-changed-before-submission")
        if args.phase == "preflight" and "preflight_renewal" in safe:
            operation_args = SimpleNamespace(**{**vars(args), "phase": "operation"})
            operation_request = STEPS.request(deps, context, operation_args)
            require(store.read(STEPS.key(operation_args, context.get("delivery")), operation_request) is None,
                "preflight-renewal-operation-already-reserved")
    def guard():
        observed = BINDING.observation_scope(provider)
        source_guard()
        C.ALIGN.source_preflight(context["custody"], **({"retained_source_evidence": context["retained_source_evidence"]}
            if context.get("retained_source_evidence") is not None else {}))
        alignment, parameters, _ = C.ALIGN.inspect(observed, context["custody"], C.now())
        original_binding = {**C.binding_for(context["custody"], alignment), "proof_label": args.proof_label}
        current_binding = original_binding
        rollback = STEPS.stage(args) == "rollback"
        if rollback:
            current_binding, _ = C.rollback_selection(args, context["delivery"], original_binding)
            parameters.update(ImageDigest=current_binding["image_digest"], SourceRevision=current_binding["source_revision"])
        require(current_binding == context["binding"], "task-dependency-changed-before-submission")
        if context.get("delivery"):
            require(C.delivery_context(args, context["custody"], original_binding) == context["delivery"], "task-predecessor-changed-before-submission")
        selected, resources = owned_stack(observed, context["binding"], parameters, context["cache"], **({"delivery": context["delivery"], "rollback": rollback} if context.get("delivery") else {}))
        binding_snapshot = BINDING.DEPLOY.source()[1]
        require(selected == context["parameters"] and resources == context["resources"]
                and BINDING.inspect(observed, args.workload, selected, resources, binding_snapshot) == context["checked"], "task-target-changed-before-submission")
        require({name: BINDING.inspect(observed, name, selected, resources, binding_snapshot) for name in context["callees"]} == context["callees"], "task-callee-changed-before-submission")
        expected = BINDING.expected_task(args.workload, selected, resources, binding_snapshot)
        require(operator(observed, request["definition"], [expected["executionRoleArn"], *([] if "taskRoleArn" not in expected else [expected["taskRoleArn"]])]) == safe["operator_sha256"], "task-operator-changed-before-submission")
        require(STEPS.prerequisites(deps, {**context, "binding_snapshot": binding_snapshot}, args, observed) == context["prerequisites"], "task-prerequisites-changed-before-submission")
        book.validate("change-set" if args.phase == "preflight" or negative else "execution-preflight", 1)
        source_guard()
    if previous is None:
        # A failed read proves non-submission and must not consume the durable
        # attempt. After these fresh checks only local admission/reservation and
        # the immediate source/exact-payload guard precede the single RunTask.
        guard()
        provider.enable_task(request, store, key, source_guard)
    else: provider.effect = "original-operation-reconcile-only"
    def progress(value):
        print(json.dumps({"schema": "deploy/entity-smoke-task-progress/v1", "phase": value["phase"], "operation_id": value["operation_id"]}), file=C.os.sys.stderr, flush=True)
    try:
        completed = runner.run_owned_task(provider, store, key, request, context["cache"] / "task-receipts",
                                          required_after=context["prerequisites"]["required_after"], preflight=preflight,
                                          revocation=context["prerequisites"]["revocation"] if negative else None, on_progress=progress)
    except runner.EVIDENCE.TerminalTaskFailure as failure:
        raise CurrentTaskFailure(failure) from None
    reservation = store.read(key, request)
    try: RECOVERY.validate_result(args, completed["receipt"])
    except RECOVERY.RecoveryStepFailure:
        provider.effect = "terminal-task-observed-proof-not-confirmed"
        raise
    step_path = STEPS.retain(deps, context, args, reservation, completed["receipt"])
    # Historical runner reuse alone is not a current remote observation. Both
    # fresh and resumed completion must survive this actual task/log consumer.
    packet = STEPS.observe_packet(deps, context, args, provider, completion_required=False)
    if args.phase == "preflight" or negative: book.gate("execution-preflight")
    book.gate("controlled-execution")
    evidence = book.validate("controlled-execution", 1)
    COMPLETION.retain(deps, context, args, step_path, evidence)
    manifest = STEPS.manifest(deps, context, args, provider, context["prerequisites"], packet)
    provider.effect = "original-task-completion-observed"
    history = HISTORY.retain(deps, {**context, "provider": provider}, args)
    return {"verdict": "completed", "plan_sha256": report["plan_sha256"], "receipt": str(step_path.relative_to(C.ROOT)),
            "realization_evidence": str(evidence.relative_to(C.ROOT)), "effect": provider.effect, "reused": completed["reused"],
            **({"activation_prerequisites": str(manifest.relative_to(C.ROOT))} if manifest is not None else {}),
            **({"credential_history": str(history.relative_to(C.ROOT))} if history is not None else {})}


def parse(arguments=None):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.error = lambda _message: (_ for _ in ()).throw(TaskRouteFailure("task-arguments-invalid"))
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--proof-label", required=True)
    parser.add_argument("--workload", choices=tuple(GRAPH.ROOT_UNITS), required=True)
    parser.add_argument("--operation", required=True)
    parser.add_argument("--phase", choices=("preflight", "operation"), default="operation")
    parser.add_argument("--proof-stage", choices=("baseline", "activation", "server-replacement", "initial-recovery", "credential-recovery", "acceptance", "rollback"), default="baseline")
    parser.add_argument("--expected-digest")
    parser.add_argument("--expected-predecessor")
    parser.add_argument("--rollback-receipt", type=Path)
    parser.add_argument("--rollback-compatibility-id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-plan")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) is not None
            and args.operation in C.RESOURCE.CONTROL.OPERATIONS[args.workload][1] and args.operation in EFFECTS, "task-arguments-invalid")
    require(args.expected_digest is None or re.fullmatch(r"[a-f0-9]{64}", args.expected_digest) is not None, "task-arguments-invalid")
    require(args.expected_predecessor is None or re.fullmatch(r"release-[a-f0-9]{24}", args.expected_predecessor) is not None, "task-predecessor-invalid")
    STEPS.stage(args)
    require((args.proof_stage == "rollback" and args.expected_predecessor is not None and args.rollback_receipt is not None and args.rollback_compatibility_id is not None)
            or (args.proof_stage != "rollback" and args.rollback_receipt is None and args.rollback_compatibility_id is None), "task-rollback-selection-invalid")
    require(args.operation not in {"read", "cleanup", "collision"} or args.expected_digest is not None, "task-original-record-digest-required")
    require(args.proof_stage not in {"initial-recovery", "credential-recovery", "acceptance"} or args.expected_digest is not None, "task-original-record-digest-required")
    require(not args.execute or isinstance(args.approved_plan, str) and re.fullmatch(r"sha256:[a-f0-9]{64}", args.approved_plan) is not None, "task-approved-plan-required")
    require(args.execute or args.approved_plan is None, "task-arguments-invalid")
    return args


def main():
    context = {}
    provider = Provider()
    try:
        args = parse()
        context = {"workload": args.workload, "operation": args.operation, "phase": args.phase, "proof_stage": getattr(args, "proof_stage", "baseline"), "proof_label_sha256": hashlib.sha256(args.proof_label.encode()).hexdigest()}
        if args.validate_arguments:
            print(json.dumps({"schema": "deploy/command-arguments-report/v1", "verdict": "valid", "findings": []})); return 0
        result = execute(args, provider) if args.execute else plan(args, provider)
        print(json.dumps({"schema": "deploy/entity-smoke-task-report/v1", **result}, sort_keys=True)); return 0
    except Exception as failure:
        known = (IMAGE_REPAIR.C.InfrastructureFailure, IMAGE_REPAIR.C.RESOURCE.CONTROL.TaskFailure, TaskRouteFailure, BINDING.BindingFailure, STEPS.StepFailure, FEATURE.FeatureStepFailure, CREDENTIAL.CredentialFailure, HISTORY.HistoryFailure, ACCEPTANCE.AcceptanceFailure, RUNNER.RunnerFailure, RUNNER.CONTROL.TaskFailure, RUNNER.EVIDENCE.EvidenceFailure, RUNNER.PREFLIGHT.PreflightFailure,
                 C.InfrastructureFailure, C.RESOURCE.ResourceFailure, C.RESOURCE.CONTROL.TaskFailure, C.RESOURCE.EVIDENCE.EvidenceFailure, C.ALIGN.AlignmentFailure, C.GATE.ContractFailure) + RECOVERY.failures()
        condition = failure.code if isinstance(failure, known) else "task-boundary-not-confirmed"
        if isinstance(failure, C.InfrastructureFailure) and failure.provider_operation is not None:
            context["provider_operation"] = "/".join(failure.provider_operation)
        if isinstance(failure, BINDING.BindingFailure): context.update(field=failure.field, item=failure.item, affected_workload=failure.workload)
        if isinstance(failure, TaskRouteFailure) and failure.item is not None: context.update(item=failure.item)
        if isinstance(failure, ACCEPTANCE.AcceptanceFailure): context.update(failure.context)
        recovery_item = RECOVERY.failure_item(failure)
        if recovery_item is not None: context.update(field="prerequisite", item=recovery_item)
        if isinstance(failure, RUNNER.CONTROL.SubmissionNotStarted) and failure.field is not None:
            context.update(field=failure.field, item=failure.item)
            if failure.workload is not None: context.update(affected_workload=failure.workload)
        evidence = failure.evidence_reference if isinstance(failure, (C.InfrastructureFailure, ACCEPTANCE.AcceptanceFailure)) else None
        diagnostics = failure.diagnostics if isinstance(failure, ACCEPTANCE.AcceptanceFailure) else RUNNER.EVIDENCE.failure_report(failure) if isinstance(failure, RUNNER.EVIDENCE.EvidenceFailure) else C.RESOURCE.EVIDENCE.failure_report(failure) if isinstance(failure, C.RESOURCE.EVIDENCE.EvidenceFailure) else {}
        # A prerequisite may also have failed terminally. Only the owned runner
        # reports the current task here; prerequisite evidence stays blocked.
        terminal = failure.evidence.terminal if isinstance(failure, CurrentTaskFailure) else None
        if terminal is not None:
            diagnostics = RUNNER.EVIDENCE.failure_report(failure.evidence)
        print(json.dumps({"schema": "deploy/entity-smoke-task-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "failed" if terminal is not None else "blocked", "condition": condition, "context": context, "effect": provider.effect,
                          **({"terminal_failure": terminal} if terminal is not None else {}),
                          **diagnostics,
                          **({"evidence_reference": evidence} if evidence is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
