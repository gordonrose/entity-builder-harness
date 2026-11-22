#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.local-qualification-binding
#   version: 1
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject any package receipt that lacks, changes, or misbinds entity-smoke local qualification evidence.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.binding.entity-smoke.local-qualification-proof
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/bindings/local-qualification/entity-smoke-proof/binding.py
import copy, importlib.util
from pathlib import Path
SOURCE = Path(__file__).parents[1] / "binding.py"
SPEC = importlib.util.spec_from_file_location("entity_smoke_local_qualification_binding", SOURCE)
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
receipt = {"schema": "deploy/package-custody-receipt/v2", "target": M.TARGET, "source_revision": "a" * 40, "local_qualification": {"schema": "deploy/local-qualification/v1", "target": M.TARGET, "scope": M.SCOPE, "source_revision": "a" * 40, "checks": {identity: {"input_digest": f"{index + 1:064x}", "evidence_key": f"{index + 4:064x}"} for index, identity in enumerate(sorted(M.REQUIRED_CHECKS))}}}
assert M.require_current(receipt) == receipt["local_qualification"]
for mutate in (lambda value: value.pop("local_qualification"), lambda value: value.update(target="other-target"), lambda value: value["local_qualification"].update(scope="other"), lambda value: value["local_qualification"].update(source_revision="b" * 40), lambda value: value["local_qualification"]["checks"].pop(next(iter(M.REQUIRED_CHECKS)),), lambda value: value["local_qualification"]["checks"][next(iter(M.REQUIRED_CHECKS))].update(input_digest="bad")):
    invalid = copy.deepcopy(receipt); mutate(invalid)
    try: M.require_current(invalid)
    except M.BindingFailure: pass
    else: raise AssertionError("invalid local qualification was admitted")
print("entity-smoke local qualification binding tests passed")
