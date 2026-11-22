#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.local-qualification.entity-smoke-proof
#   version: 1
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.qualification
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject malformed, stale, non-local, or incomplete selector evidence before it can enter package custody.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.capability.local-qualification.entity-smoke-proof
#     path: scripts/04.deploy/lifecycle/20-build/capabilities/local-qualification/entity-smoke-proof/implementation.py
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).parents[1] / "implementation.py"
SPEC = importlib.util.spec_from_file_location("entity_smoke_local_qualification", SOURCE)
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)

def report():
    source = "a" * 40
    return {"schema": "repo/check-selection-report/v1", "stage": "local", "verdict": "passed", "findings": [], "source_revision": source,
            "checks": [{"check_id": identity, "status": "passed", "stage": "local", "source_revision": source, "evidence_source": "local-runner", "input_digest": f"{number + 1:064x}", "evidence_key": f"{number + 4:064x}"} for number, identity in enumerate(sorted(M.REQUIRED_CHECKS))]}

assert set(M.capture(report())["checks"]) == M.REQUIRED_CHECKS
for mutate in (lambda item: item.update(verdict="gap"), lambda item: item["checks"].pop(), lambda item: item["checks"][0].update(status="reused"), lambda item: item["checks"][0].update(stage="deploy"), lambda item: item["checks"][0].update(source_revision="b" * 40), lambda item: item["checks"][0].update(input_digest="bad")):
    invalid = report(); mutate(invalid)
    try: M.capture(invalid)
    except M.QualificationFailure: pass
    else: raise AssertionError("invalid selector evidence was admitted")
print("entity-smoke local qualification implementation tests passed")
