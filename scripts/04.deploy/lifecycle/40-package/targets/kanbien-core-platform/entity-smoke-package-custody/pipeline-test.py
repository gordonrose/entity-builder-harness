#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.pipeline-registration
#   version: 2
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise the actual target pipeline checker without loosening existing publication identities, destinations or protected-source boundaries.
#   portability: {class: internal, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.entity-smoke.publication-contract
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/smoke-test.sh
import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import yaml

if not __debug__: raise SystemExit("ENTITY_SMOKE_PIPELINE_ASSERTIONS_DISABLED")
ROOT = Path(__file__).resolve().parents[7]
TARGET = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform"
INDEX = TARGET / "40-package-custody/github-actions/pipeline-index.yml"
SPEC = importlib.util.spec_from_file_location("entity_smoke_pipeline_target_checker", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
M.check_pipeline(TARGET)
catalogue = yaml.safe_load(INDEX.read_text())
original = M.mapping
current = copy.deepcopy(catalogue)
def supplied(path, _code):
    assert path == INDEX
    return current
M.mapping = supplied
def feature(): return next(item for item in current["pipelines"] if item["id"] == "entity-smoke-package-custody")
feature()["state"] = "active"
M.check_pipeline(TARGET)
negatives = [
    (lambda: feature().update(provider_identity="github-kanbien-core-platform-delivery"), "pipeline-record-invalid"),
    (lambda: feature().update(package_destination="kanbien-core-platform/core-server"), "pipeline-record-invalid"),
    (lambda: feature().update(permitted_source_ref="refs/heads/chat"), "pipeline-record-invalid"),
    (lambda: feature().update(approval="none"), "pipeline-record-invalid"),
    (lambda: feature().update(state="accepted"), "pipeline-record-invalid"),
    (lambda: feature().update(state=[]), "pipeline-record-invalid"),
    (lambda: feature().update(state={"private-provider-canary": True}), "pipeline-record-invalid"),
    (lambda: feature().update(state=True), "pipeline-record-invalid"),
    (lambda: feature().update(state=None), "pipeline-record-invalid"),
    (lambda: feature().update(used_by_scopes=["core-server-persistence"]), "pipeline-authority-invalid"),
    (lambda: feature().update(deployment_boundary="automatic-deployment"), "pipeline-authority-invalid"),
    (lambda: feature()["required_proofs"].remove("provenance-attestation"), "pipeline-authority-invalid"),
    (lambda: next(item for item in current["pipelines"] if item["id"] == "core-server-package-custody").update(state="candidate-not-live"), "pipeline-record-invalid"),
    (lambda: next(item for item in current["pipelines"] if item["id"] == "core-server-persistence-package-custody").update(package_destination="kanbien-core-platform/entity-smoke"), "pipeline-record-invalid"),
    (lambda: current["pipelines"].append(copy.deepcopy(feature())), "pipeline-record-missing"),
]
for change, code in negatives:
    current = copy.deepcopy(catalogue); change()
    try: M.check_pipeline(TARGET)
    except M.DeclarationFailure as failure:
        assert failure.codes == (code,), (failure.codes, code)
        assert "private-provider-canary" not in str(failure)
    else: raise AssertionError("expected closed pipeline rejection")
M.mapping = original

# Exercise the real final reporter too. Earlier declaration stages are explicit
# controlled protocols; the actual pipeline predicate and main report are real.
for invalid in ([], {"private-provider-canary": True}, True, None):
    current = copy.deepcopy(catalogue); feature()["state"] = invalid
    output = io.StringIO()
    args = SimpleNamespace(target_root=str(TARGET), rehearsal_root=None, validate_arguments=False)
    with patch.object(M, "parse_args", return_value=args), \
         patch.object(M, "mapping", side_effect=lambda path, code: current if path == INDEX else original(path, code)), \
         patch.object(M, "check_profile"), patch.object(M, "check_foundation"), \
         patch.object(M, "check_scope"), patch.object(M, "check_accepted_release"), \
         patch.object(M, "check_persistence_provider_identity_bindings") as later, redirect_stdout(output):
        assert M.main() == 1
        assert later.call_count == 0
    report = json.loads(output.getvalue())
    assert report["verdict"] == "failed" and report["findings"] == [{"code": "pipeline-record-invalid"}]
    assert "private-provider-canary" not in output.getvalue()
print(json.dumps({"schema": "deploy/entity-smoke-pipeline-fixture/v1", "verdict": "passed", "provider_observation": False, "negative_cases": len(negatives)}))
