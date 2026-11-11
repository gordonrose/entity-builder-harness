#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.task-plan.implementation
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-11"
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


DIRECTORY = Path(__file__).parent
C = module("entity_smoke_task_route_common", DIRECTORY / "script.py")
BINDING = module("entity_smoke_task_route_binding", DIRECTORY / "task-binding.py")
GRAPH = module("entity_smoke_task_route_graph", DIRECTORY / "task-graph.py")
RUNNER = module("entity_smoke_task_route_runner", DIRECTORY / "task-runner.py")
STEPS = module("entity_smoke_task_route_steps", DIRECTORY / "task-steps.py")
FEATURE = module("entity_smoke_task_route_feature", DIRECTORY / "feature-steps.py")
RECOVERY = module("entity_smoke_task_route_recovery", DIRECTORY / "recovery-steps.py")
CREDENTIAL = module("entity_smoke_task_route_credential", DIRECTORY / "credential-steps.py")
COMPLETION = module("entity_smoke_task_route_completion", DIRECTORY / "task-completion.py")
HISTORY = module("entity_smoke_task_route_history", DIRECTORY / "recovery-history.py")
ACCEPTANCE = module("entity_smoke_task_route_acceptance", DIRECTORY / "acceptance-steps.py")
IMAGE_REPAIR = module("entity_smoke_task_image_repair", DIRECTORY / "image-delivery-repair.py")
RULE = C.ROOT / ".agentic/aws/standards/operational-realization-applicability.md"
READS = C.READS | {("ecs", "describe-task-definition"), ("ecs", "list-services"), ("ec2", "describe-security-groups")} | {("iam", name) for name in ("list-role-policies", "list-attached-role-policies", "get-role-policy")}
READS |= {("rds", "describe-db-snapshots"), ("rds", "list-tags-for-resource")}
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


def owned_stack(provider, binding, parameters, cache):
    retained = C.read_json(cache / "receipts/create.json")
    require(isinstance(retained, dict) and set(retained) == {"schema", "binding", "result"} and retained.get("schema") == "deploy/entity-smoke-infrastructure-receipt/v1"
            and retained.get("binding") == binding and isinstance(retained.get("result"), dict) and retained["result"].get("status") == "completed", "task-created-infrastructure-required")
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
    expected_creation = C.DEPLOY.request(binding, {**parameters, "ServerDesiredCount": "0"}, False)
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
    require(len(observed) == len(resources) and isinstance(retained["result"].get("facts"), dict) and retained["result"]["facts"].get("resources") == observed
            and retained["result"]["facts"].get("stack_arn") == actual["StackId"], "task-infrastructure-lineage-not-confirmed")
    return selected, observed


def prepare(args, provider):
    proof_stage = STEPS.stage(args)
    receipt = C.ALIGN.read_receipt(args.receipt.absolute())
    C.ALIGN.source_preflight(receipt)
    C.local_checks()
    artifact = C.source_digest()
    cache = C.ROOT / ".cache/entity-smoke-live" / args.proof_label
    C.filesystem_preflight(cache)
    declaration = GRAPH.contract(args.workload, C.GATE, negative=CREDENTIAL.negative(args))
    artifacts = {item["id"]: artifact if item["id"] == GRAPH.CONTROLLER_SOURCE else receipt["image_digest"] for item in declaration["artifacts"]}
    book = C.GateBook(artifact, cache / "task-realization", contract=declaration, artifact_bindings=artifacts)
    book.gate("source"); book.gate("artifact"); book.gate("semantic-integration")
    alignment, parameters, _ = C.ALIGN.inspect(provider, receipt, C.now())
    binding = {**C.binding_for(receipt, alignment), "proof_label": args.proof_label}
    selected, resources = owned_stack(provider, binding, parameters, cache)
    binding_snapshot = BINDING.DEPLOY.source()[1]
    checked = BINDING.inspect(provider, args.workload, selected, resources, binding_snapshot)
    callees = {"server": BINDING.inspect(provider, "server", selected, resources, binding_snapshot)} if args.workload == "verifier" else {}
    expected = BINDING.expected_task(args.workload, selected, resources, binding_snapshot)
    roles = [expected["executionRoleArn"], *([] if "taskRoleArn" not in expected else [expected["taskRoleArn"]])]
    actor = operator(provider, checked["definition"], roles)
    stage_suffix = "" if proof_stage == "baseline" else ":" + proof_stage
    preflight_label = "entity-smoke-" + hashlib.sha256((args.proof_label + ":" + args.workload + ":" + args.operation + ":preflight" + stage_suffix).encode()).hexdigest()[:24]
    preflight_label = IMAGE_REPAIR.recovery_label({"cache": cache, "binding": binding, "checked": checked}, args, preflight_label)
    actual_operation = ("ready" if args.workload == "verifier" else "preflight") if args.phase == "preflight" else args.operation
    safe = {"schema": "deploy/entity-smoke-task-plan/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "account": C.ALIGN.ACCOUNT, "region": C.ALIGN.REGION,
            "workload": args.workload, "phase": args.phase, "operation": actual_operation, "prepared_operation": args.operation, "proof_stage": proof_stage, "preflight_label": preflight_label,
            "database_effect": EFFECTS[actual_operation], "expected_record_digest": args.expected_digest,
            "binding": binding, "controller_sha256": artifact, "graph_sha256": C.DEPLOY.fingerprint(declaration),
            "parameters_sha256": C.DEPLOY.fingerprint(selected), "template_sha256": C.digest_file(C.DEPLOY.SOURCE), "preflight_rule_sha256": C.digest_file(RULE),
            "operator_sha256": actor, "task_definition_sha256": C.DEPLOY.fingerprint(checked["definition"]), "configuration_sha256": checked["configuration_sha256"],
            "roles_sha256": checked["roles_sha256"], "network_sha256": checked["network_sha256"], "callee_bindings_sha256": C.DEPLOY.fingerprint(callees), "package_custody_reference": receipt["receipt_reference"],
            "task_count": 1, "automatic_retry": False}
    declaration = C.yaml.safe_load((C.CONTRACT.parent / "declaration-contract.yml").read_text())
    deadlines = {row["id"].removeprefix("entity-smoke-"): row["completion"]["deadline_seconds"] for row in declaration["health_recovery"]["workloads"] if "completion" in row}
    context = {"report": {"plan": safe}, "book": book, "cache": cache, "binding": binding, "checked": checked,
               "parameters": selected, "resources": resources, "artifact": artifact, "custody": receipt, "callees": callees, "completion_deadlines": deadlines, "binding_snapshot": binding_snapshot}
    # Missing prior work is visible in a plan, not manufactured as success.
    missing = None
    try: prerequisites = STEPS.prerequisites(dependencies(), context, args, provider)
    except STEPS.PrerequisiteMissing as failure:
        prerequisites, missing = None, failure.item
    safe["prerequisites_sha256"] = None if prerequisites is None else C.DEPLOY.fingerprint(prerequisites)
    safe["pending_prerequisite"] = missing
    safe["execution_route_available"] = (STEPS.selected(args) is not None or FEATURE.supported(args) or RECOVERY.supported(args) or CREDENTIAL.supported(args) or ACCEPTANCE.supported(args)) and prerequisites is not None
    context["prerequisites"] = prerequisites
    safe["request_sha256"] = C.DEPLOY.fingerprint(STEPS.request(dependencies(), context, args))
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
    request = STEPS.request(deps, context, args)
    store = runner.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    key = STEPS.key(args)
    previous = store.read(key, request)
    negative = CREDENTIAL.negative(args)
    preflight = None
    if negative:
        try: runner.UNREADY.validate_launch(request, context["prerequisites"]["revocation"])
        except runner.UNREADY.UnreadyFailure as failure: raise TaskRouteFailure(failure.code) from None
    elif args.phase == "operation":
        if previous is None:
            probe_args = SimpleNamespace(**{**vars(args), "phase": "preflight"})
            packet = STEPS.observe_packet(deps, context, probe_args, provider)
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

    def guard():
        require(C.source_digest() == context["artifact"] and C.digest_file(RULE) == safe["preflight_rule_sha256"]
                and C.DEPLOY.fingerprint(GRAPH.contract(args.workload, C.GATE, negative=negative)) == safe["graph_sha256"], "task-source-changed-before-submission")
        C.ALIGN.source_preflight(context["custody"])
        alignment, parameters, _ = C.ALIGN.inspect(provider, context["custody"], C.now())
        require({**C.binding_for(context["custody"], alignment), "proof_label": args.proof_label} == context["binding"], "task-dependency-changed-before-submission")
        selected, resources = owned_stack(provider, context["binding"], parameters, context["cache"])
        binding_snapshot = BINDING.DEPLOY.source()[1]
        require(selected == context["parameters"] and resources == context["resources"]
                and BINDING.inspect(provider, args.workload, selected, resources, binding_snapshot) == context["checked"], "task-target-changed-before-submission")
        require({name: BINDING.inspect(provider, name, selected, resources, binding_snapshot) for name in context["callees"]} == context["callees"], "task-callee-changed-before-submission")
        expected = BINDING.expected_task(args.workload, selected, resources, binding_snapshot)
        require(operator(provider, request["definition"], [expected["executionRoleArn"], *([] if "taskRoleArn" not in expected else [expected["taskRoleArn"]])]) == safe["operator_sha256"], "task-operator-changed-before-submission")
        require(STEPS.prerequisites(deps, {**context, "binding_snapshot": binding_snapshot}, args, provider) == context["prerequisites"], "task-prerequisites-changed-before-submission")
        book.validate("change-set" if args.phase == "preflight" or negative else "execution-preflight", 1)
        require(C.source_digest() == context["artifact"] and C.digest_file(RULE) == safe["preflight_rule_sha256"]
                and C.digest_file(C.ROOT / C.ALIGN.SCOPE) == context["binding"]["configuration_contract_sha256"], "task-source-changed-before-submission")
    if previous is None: provider.enable_task(request, store, key, guard)
    else: provider.effect = "original-operation-reconcile-only"
    def progress(value):
        print(json.dumps({"schema": "deploy/entity-smoke-task-progress/v1", "phase": value["phase"], "operation_id": value["operation_id"]}), file=C.os.sys.stderr, flush=True)
    completed = runner.run_owned_task(provider, store, key, request, context["cache"] / "task-receipts",
                                      required_after=context["prerequisites"]["required_after"], preflight=preflight,
                                      revocation=context["prerequisites"]["revocation"] if negative else None, on_progress=progress)
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
    history = HISTORY.retain(deps, {**context, "provider": provider}, args)
    provider.effect = "original-task-completion-observed"
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
    parser.add_argument("--proof-stage", choices=("baseline", "server-replacement", "initial-recovery", "credential-recovery", "acceptance"), default="baseline")
    parser.add_argument("--expected-digest")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--validate-arguments", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approved-plan")
    args = parser.parse_args(arguments)
    require(re.fullmatch(r"entity-smoke-[a-f0-9]{24}", args.proof_label) is not None
            and args.operation in C.RESOURCE.CONTROL.OPERATIONS[args.workload][1] and args.operation in EFFECTS, "task-arguments-invalid")
    require(args.expected_digest is None or re.fullmatch(r"[a-f0-9]{64}", args.expected_digest) is not None, "task-arguments-invalid")
    STEPS.stage(args)
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
        if isinstance(failure, BINDING.BindingFailure): context.update(field=failure.field, item=failure.item, affected_workload=failure.workload)
        if isinstance(failure, TaskRouteFailure) and failure.item is not None: context.update(item=failure.item)
        if isinstance(failure, ACCEPTANCE.AcceptanceFailure): context.update(failure.context)
        recovery_item = RECOVERY.failure_item(failure)
        if recovery_item is not None: context["item"] = recovery_item
        if isinstance(failure, RUNNER.CONTROL.SubmissionNotStarted) and failure.field is not None:
            context.update(field=failure.field, item=failure.item)
            if failure.workload is not None: context.update(affected_workload=failure.workload)
        evidence = failure.evidence_reference if isinstance(failure, (C.InfrastructureFailure, ACCEPTANCE.AcceptanceFailure)) else None
        diagnostics = failure.diagnostics if isinstance(failure, ACCEPTANCE.AcceptanceFailure) else RUNNER.EVIDENCE.failure_report(failure) if isinstance(failure, RUNNER.EVIDENCE.EvidenceFailure) else C.RESOURCE.EVIDENCE.failure_report(failure) if isinstance(failure, C.RESOURCE.EVIDENCE.EvidenceFailure) else {}
        print(json.dumps({"schema": "deploy/entity-smoke-task-report/v1", "target": C.RESOURCE.CLUSTER, "scope": "entity-smoke", "verdict": "blocked", "condition": condition, "context": context, "effect": provider.effect,
                          **diagnostics,
                          **({"evidence_reference": evidence} if evidence is not None else {})}, sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
