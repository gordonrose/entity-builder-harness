#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.entity-smoke.image-delivery-repair
#   version: 2
#   status: draft
#   created_on: "2026-11-10"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Read retained endpoint-repair provenance and reject the retired incident executor without provider effects.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.entity-smoke.task-plan.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route.py
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("entity_smoke_image_repair_common", Path(__file__).with_name("script.py"))
C = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(C)
LABEL = "entity-smoke-8f76ed3480e85d60fb60f547"
FAILURE_ID = "es-4a34dceff456486cb2a33666613d6949"
FAILURE_HASH = "sha256:da7e03014d1be5c02205da7b536cf9f1a109a4d3372a212229f299fb961dc69b"
# Actual completed bootstrap at checkpoint6ed1ce90, before the operator repair.
# This recognises only the original immutable documents, never arbitrary history.
BOOTSTRAP_CONTROLLER = "sha256:ae545968c53e005e223320e805967c95209b7a96d764257e3b537cb4adce9903"
BOOTSTRAP_COMPLETIONS = {
    "sha256:54e1f8035f6c1cf1404ce685193d0e5e141bee0856ee726afe239581f93c8cb3": "sha256:9c66ffe83e80692c301e98c7bd89b158c4b675e58c1e011eee7ebb3f48778c30",
    "sha256:c048875837a67e77371278a31ee77600e53f7b8633c1dffcfd51445576f916f4": "sha256:2e77bb18ed5b82574a04d69e4b4b5df522c5749edf4670c35bf104e78a2982f1",
}
require = C.require
fingerprint = C.DEPLOY.fingerprint


def completed_bootstrap_controller(packet, completion, current):
    if BOOTSTRAP_COMPLETIONS.get("sha256:" + C.TRANSITION.document(packet)) == "sha256:" + C.TRANSITION.document(completion):
        return BOOTSTRAP_CONTROLLER
    return C.TRANSITION.controller(packet, completion, current)


def cache(): return C.ROOT / ".cache/entity-smoke-live" / LABEL / "image-delivery-repair"


def recovery_label(context, args, original):
    if (args.proof_label, args.workload, args.operation, getattr(args, "proof_stage", "baseline")) != (LABEL, "administration", "bootstrap", "baseline"):
        return original
    # Exact observed failed attempt: this cannot become a caller-controlled retry.
    observation_path = context["cache"] / "diagnostics" / ("startup-failed-" + FAILURE_ID + ".json")
    require(C.digest_file(observation_path) == FAILURE_HASH, "image-repair-original-failure-changed")
    observed = C.read_json(observation_path)
    reservation = observed["reservation"]
    expected = {**context["binding"], "workload": "administration", "definition": context["checked"]["definition"],
                "security_group": context["checked"]["security_group"], "subnets": context["checked"]["subnets"],
                "environment": {"ENTITY_SMOKE_ADMINISTRATION_OPERATION": "preflight"}, "deadline_seconds": 90, "proof_label": original}
    require(reservation["operation_id"] == FAILURE_ID and reservation["request"] == expected
            and observed["application_started"] is False and observed["task"]["stop_code"] == "TaskFailedToStart", "image-repair-original-failure-mismatch")
    require(C.RESOURCE.CONTROL.AttemptStore(context["cache"] / "task-attempts").read("original-preflight", expected) == reservation, "image-repair-original-reservation-mismatch")
    plan, receipt = C.read_json(cache() / "plan.json"), C.read_json(cache() / "receipt.json")
    execution = C.read_json(cache() / "execute-intent.json")
    require(receipt.get("schema") == "deploy/entity-smoke-image-delivery-receipt/v1" and receipt.get("plan_sha256") == fingerprint(plan)
            and receipt.get("execution_sha256") == fingerprint(execution) and receipt.get("terminal_token_confirmed") is True
            and receipt.get("source_revision") == expected["source_revision"] and receipt.get("image_digest") == expected["image_digest"], "image-repair-successful-receipt-required")
    return "entity-smoke-" + C.hashlib.sha256((original + ":" + FAILURE_ID + ":image-delivery-recovery-1").encode()).hexdigest()[:24]


def main():
    # This completed incident is historical provenance, not a reusable repair
    # command. Do not parse supplied paths or construct a live provider here.
    print(json.dumps({"schema": "deploy/entity-smoke-image-delivery-report/v1",
                      "verdict": "blocked", "condition": "image-repair-executor-retired",
                      "effect": "not-started"}, sort_keys=True))
    return 1


if __name__ == "__main__": raise SystemExit(main())
