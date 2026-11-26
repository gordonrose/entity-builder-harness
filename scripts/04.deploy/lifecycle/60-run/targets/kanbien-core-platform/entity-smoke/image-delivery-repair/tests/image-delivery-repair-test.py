#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.image-delivery-repair
#   version: 2
#   status: draft
#   created_on: "2026-11-10"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove retired incident commands cannot execute and retained image-repair provenance remains strictly validated.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.target-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/entity-smoke/alignment-test.py
import copy
import contextlib
import io
import sys
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

if not __debug__: raise SystemExit("ENTITY_SMOKE_IMAGE_REPAIR_ASSERTIONS_DISABLED")
spec = importlib.util.spec_from_file_location("image_repair_fixture", (Path(__file__).resolve().parents[2] / "image-delivery-repair/implementation/image-delivery-repair.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
C = M.C
SOURCE = "8f76ed3480e85d60fb60f547f996628c8554504d"
BEFORE = C.DEPLOY.CF.template((C.ROOT / C.ALIGN.FOUNDATION).read_text())
# Reconstruct the exact pinned pre-repair fixture without requiring Git
# history in hosted shallow checkouts. This hash was independently obtained
# from SOURCE's original template, not from the reconstruction under test.
for endpoint in ("EcrApiEndpoint", "EcrDkrEndpoint"):
    statements = BEFORE["Resources"][endpoint]["Properties"]["PolicyDocument"]["Statement"]
    matches = [row for row in statements if row.get("Resource") == [
        {"Ref": "ExistingRepositoryArn"},
        {"Fn::Sub": "arn:aws:ecr:${AWS::Region}:${AWS::AccountId}:repository/kanbien-core-platform/entity-smoke"}]]
    assert len(matches) == 1
    matches[0]["Resource"] = {"Ref": "ExistingRepositoryArn"}
assert C.DEPLOY.fingerprint(BEFORE) == "sha256:aef24b28801c4ada9c405ec908d7c7151d12bb5f854d3734883f8da02b0b8997"
AFTER = C.ALIGN.repaired_foundation(BEFORE)
assert C.DEPLOY.CF.templates_equal(AFTER, (C.ROOT / C.ALIGN.FOUNDATION).read_text())


def fails(callback, code):
    try: callback()
    except Exception as failure: assert getattr(failure, "code", None) == code, (code, type(failure).__name__, str(failure))
    else: raise AssertionError(code)


for mutate in (lambda value: value["Resources"]["EcrApiEndpoint"]["Properties"].update(PrivateDnsEnabled=False),
               lambda value: value["Resources"]["EcrDkrEndpoint"]["Properties"]["PolicyDocument"]["Statement"][0].update(Resource="*"),
               lambda value: value.update(Description="unrelated-change")):
    changed = copy.deepcopy(AFTER); mutate(changed)
    with patch.object(C.ALIGN, "command", side_effect=lambda args: json.dumps(BEFORE if args[2].startswith(SOURCE + ":") else changed)):
        fails(lambda: C.ALIGN.foundation_sources(SOURCE, "b" * 40), "alignment-foundation-repair-invalid")



# Exercise the actual former CLI for all modes and malformed/absent arguments.
# Sentinel providers/retention fail even if constructed without a submission.
for argv in ([], ["--mode", "plan"], ["--mode", "review"], ["--mode", "execute"],
             ["--mode", "reconcile"], ["--receipt", "private-path-canary", "--unknown"]):
    output = io.StringIO()
    with patch.object(sys, "argv", [str(Path(M.__file__)), *argv]), \
         patch.object(C, "Provider", side_effect=AssertionError("provider constructed")) as provider, \
         patch.object(C, "read_json", side_effect=AssertionError("input read")) as read, \
         patch.object(C.RESOURCE, "write_exclusive", side_effect=AssertionError("evidence write")) as write, \
         contextlib.redirect_stdout(output):
        assert M.main() == 1
        provider.assert_not_called(); read.assert_not_called(); write.assert_not_called()
    assert json.loads(output.getvalue()) == {
        "schema": "deploy/entity-smoke-image-delivery-report/v1", "verdict": "blocked",
        "condition": "image-repair-executor-retired", "effect": "not-started"}
    assert "private-path-canary" not in output.getvalue()
for removed in ("run", "submit", "prepare", "current", "retain", "change_shape", "reviewed"):
    assert not hasattr(M, removed), removed

with tempfile.TemporaryDirectory(prefix="entity-image-recovery-") as temporary:
    root = Path(temporary)
    args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="bootstrap", proof_stage="baseline", phase="preflight")
    original = "entity-smoke-" + C.hashlib.sha256((M.LABEL + ":administration:bootstrap:preflight").encode()).hexdigest()[:24]
    binding = {"proof_label": M.LABEL, "source_revision": SOURCE, "image_digest": "sha256:" + "a" * 64,
               **{name: "sha256:" + "b" * 64 for name in ("configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")}}
    checked = {"definition": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-entity-smoke-administration:1", "security_group": "sg-" + "1" * 17, "subnets": ["subnet-" + "2" * 17]}
    context = {"cache": root / ".cache/entity-smoke-live" / M.LABEL, "binding": binding, "checked": checked}
    request = {**binding, **checked, "workload": "administration", "environment": {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}, "deadline_seconds": 90, "proof_label": original}
    reservation = {"schema": "deploy/entity-smoke-task-reservation/v1", "request": request, "request_sha256": C.hashlib.sha256(C.RESOURCE.CONTROL.canonical(request)).hexdigest(), "operation_id": M.FAILURE_ID, "reserved_at": "2026-11-10T19:11:29+00:00"}
    observation = {"reservation": reservation, "application_started": False, "task": {"stop_code": "TaskFailedToStart"}}
    observation_path = context["cache"] / "diagnostics" / ("startup-failed-" + M.FAILURE_ID + ".json")
    C.RESOURCE.write_exclusive(observation_path, observation)
    store = C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts")
    C.RESOURCE.write_exclusive(store.path_for("original", request), reservation)
    original_bytes = store.path_for("original", request).read_bytes()
    with patch.object(C, "ROOT", root), patch.object(M, "FAILURE_HASH", C.digest_file(observation_path)):
        plan, execution = {"fixture": "reviewed-plan"}, {"fixture": "executed-intent"}
        C.RESOURCE.write_exclusive(M.cache() / "plan.json", plan)
        C.RESOURCE.write_exclusive(M.cache() / "execute-intent.json", execution)
        fails(lambda: M.recovery_label(context, args, original), "infrastructure-input-unavailable")
        C.RESOURCE.write_exclusive(M.cache() / "receipt.json", {"schema": "deploy/entity-smoke-image-delivery-receipt/v1", "plan_sha256": M.fingerprint(plan), "execution_sha256": M.fingerprint(execution), "terminal_token_confirmed": True, "source_revision": SOURCE, "image_digest": binding["image_digest"]})
        recovery = M.recovery_label(context, args, original)
        acceptance_spec = importlib.util.spec_from_file_location("image_repair_acceptance_label_fixture", (Path(__file__).resolve().parents[2] / "acceptance-evaluation/implementation/acceptance-evidence.py"))
        acceptance = importlib.util.module_from_spec(acceptance_spec); acceptance_spec.loader.exec_module(acceptance)
        assert acceptance.preflight_label(binding, "baseline", "administration", "bootstrap") == recovery
        for stage, workload, operation in (("credential-recovery", "administration", "bootstrap"), ("baseline", "migration", "apply")):
            suffix = "" if stage == "baseline" else ":" + stage
            ordinary = "entity-smoke-" + C.hashlib.sha256((M.LABEL + ":" + workload + ":" + operation + ":preflight" + suffix).encode()).hexdigest()[:24]
            assert acceptance.preflight_label(binding, stage, workload, operation) == ordinary
        grant_original = "entity-smoke-" + C.hashlib.sha256((M.LABEL + ":administration:grant-runtime:preflight").encode()).hexdigest()[:24]
        grant_args = SimpleNamespace(proof_label=M.LABEL, workload="administration", operation="grant-runtime", proof_stage="baseline")
        assert acceptance.preflight_label(binding, "baseline", "administration", "grant-runtime") == C.TRANSITION.replacement_label({}, grant_args, grant_original)
        assert recovery != original and M.recovery_label(context, SimpleNamespace(**{**vars(args), "phase": "operation"}), original) == recovery
        assert store.path_for("recovery", {**request, "proof_label": recovery}) != store.path_for("original", request)
        assert store.path_for("original", request).read_bytes() == original_bytes
        fails(lambda: M.recovery_label({**context, "checked": {**checked, "security_group": "sg-" + "3" * 17}}, args, original), "image-repair-original-failure-mismatch")
        with patch.object(M, "FAILURE_HASH", "sha256:" + "0" * 64):
            fails(lambda: M.recovery_label(context, args, original), "image-repair-original-failure-changed")

print(json.dumps({"schema": "deploy/entity-smoke-image-repair-fixture/v1", "verdict": "passed", "provider_observation": False,
                  "checks": ["historical-two-policy-source-delta", "whole-template-preservation", "retired-cli-no-provider-or-evidence-effects", "historical-recovery-label", "original-reservation-preserved", "changed-binding-and-failure-rejected"]}))
