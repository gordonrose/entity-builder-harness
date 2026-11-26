#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.local-qualification.entity-smoke-proof
#   version: 2
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-25"
#   layer: 04.deploy
#   domain: deployment.qualification
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove current private qualification, cold execution, unchanged reuse and rejection of forged or stale report evidence.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.capability.local-qualification.entity-smoke-proof
#     path: scripts/04.deploy/lifecycle/20-build/capabilities/local-qualification/entity-smoke-proof/implementation.py
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).parents[1] / "implementation.py"
SPEC = importlib.util.spec_from_file_location("entity_smoke_local_qualification", SOURCE)
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
from test_support import FixtureSupport, write
from local_cache import LocalCache

with tempfile.TemporaryDirectory(prefix="qualification-handoff-") as directory:
    fixture = FixtureSupport()
    fixture.root = Path(directory)
    subprocess.run(["git", "init", "--quiet", directory], check=True)
    (fixture.root / "src").mkdir()
    (fixture.root / "src/main.ts").write_text("fixture source\n")
    fixture.catalog_path = fixture.root / "scripts/repo/check-selection/checks.yml"
    # Reuse generic fixture methods, not the real-target setUp tree.
    checks = {}
    for identity in sorted(M.REQUIRED_CHECKS):
        fixture.check_script(identity, ["writes-files"], "cat src/main.ts >/dev/null\necho " + identity + " >> counts\n")
        checks[identity] = {"argv": ["bash", "scripts/" + identity + ".sh"], "stage": "local", "boundary": "integration", "effects": ["writes-files"], "owner": "fixture." + identity, "evidence_class": "static", "scope_inputs": False, "inputs": ["src/main.ts", "scripts/" + identity + ".sh"], "runtime": {"tools": ["bash"], "environment": ["LANG"]}}
    write(fixture.catalog_path, {"schema": "repo/check-catalog/v1", "checks": checks, "repository_inputs": [{"inputs": ["src/main.ts"], "checks": sorted(checks)}]})
    cold = fixture.run_plan(checks=sorted(checks), task_paths=["src/main.ts"], execute=True, record_preparation=True)
    assert cold["verdict"] == "passed", cold["findings"]
    current = fixture.run_plan(checks=sorted(checks), task_paths=["src/main.ts"])
    cache = LocalCache(fixture.root, create=False)
    captured = M.capture(cold, current, cache)
    assert set(captured["checks"]) == M.REQUIRED_CHECKS
    warm = fixture.run_plan(checks=sorted(checks), task_paths=["src/main.ts"], execute=True)
    assert warm["verdict"] == "passed", warm["findings"]
    assert M.capture(warm, current, cache) == captured
    assert len((fixture.root / "counts").read_text().splitlines()) == 3
    assert cold["execution_summary"]["executed_check_ids"] == sorted(checks)
    assert warm["execution_summary"]["executed_check_ids"] == []
    assert warm["execution_summary"]["reused_check_ids"] == sorted(checks)
    # Continue the actual generated qualification through custody and its target reader.
    qualification = fixture.root / "qualification.json"
    qualification.write_text(json.dumps(captured))
    sbom = fixture.root / "sbom.json"; sbom.write_text('{"spdxVersion":"SPDX-2.3"}')
    custody = fixture.root / "custody.json"
    command = [sys.executable, "-B", str(M.ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/capture.py"), "--target", M.TARGET, "--environment-class", "private-feature-candidate", "--provider-region-alias", "aws-eu-west-1", "--candidate", "kanbien-entity-smoke-candidate", "--package-contract", "kanbien-entity-smoke-image", "--program", "kanbien-entity-smoke", "--scan-check", "ecr_scan", "--sbom", str(sbom), "--local-qualification", str(qualification), "--output", str(custody)]
    environment = {**os.environ, **{key: "success" for key in ["QUALIFICATION_OUTCOME", "ACCESS_OUTCOME", "PUBLICATION_OUTCOME", "SCAN_OUTCOME", "SBOM_OUTCOME", "PROVENANCE_OUTCOME", "SBOM_ATTESTATION_OUTCOME"]}, "GITHUB_SHA": cold["source_revision"], "GITHUB_RUN_ID": "123", "IMAGE_DIGEST": "sha256:" + "b" * 64}
    result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    binding_path = M.ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/bindings/local-qualification/entity-smoke-proof/binding.py"
    spec = importlib.util.spec_from_file_location("qualification_target_reader", binding_path)
    binding = importlib.util.module_from_spec(spec); spec.loader.exec_module(binding)
    assert binding.require_current(json.loads(custody.read_text())) == captured
    custody.unlink()
    rejected = subprocess.run(command, env={**environment, "GITHUB_SHA": "c" * 40}, capture_output=True, text=True, timeout=20)
    assert rejected.returncode == 1 and not custody.exists(), rejected.stdout
    for mutate in (lambda v: v.update(verdict="gap"), lambda v: v["checks"].pop(), lambda v: v["checks"].append(v["checks"][0]), lambda v: v["checks"][0].update(status="reused"), lambda v: v["checks"][0].update(stage="deploy"), lambda v: v.update(source_revision="b" * 40), lambda v: v["checks"][0].update(source_revision="b" * 40), lambda v: v["checks"][0].update(input_digest="f" * 64), lambda v: v["checks"][0].update(evidence_key="f" * 64)):
        invalid = copy.deepcopy(warm); mutate(invalid)
        try: M.capture(invalid, current, cache)
        except M.QualificationFailure: pass
        else: raise AssertionError("invalid selector evidence was admitted")
    proof = cache.directory / (warm["checks"][0]["evidence_key"] + ".json")
    saved = proof.read_bytes(); proof.unlink()
    try: M.capture(warm, current, cache)
    except M.QualificationFailure: pass
    else: raise AssertionError("uploaded JSON substituted for absent private proof")
    proof.write_bytes(saved); proof.chmod(0o600)
    (fixture.root / "src/main.ts").write_text("changed fixture source\n")
    changed = fixture.run_plan(checks=sorted(checks), task_paths=["src/main.ts"])
    try: M.capture(warm, changed, cache)
    except M.QualificationFailure: pass
    else: raise AssertionError("stale inputs admitted")
    fixture.check_script(sorted(checks)[0], ["writes-files"], "exit 7\n")
    failed = fixture.run_plan(checks=sorted(checks), task_paths=["src/main.ts"], execute=True)
    try: M.capture(failed, changed, cache)
    except M.QualificationFailure: pass
    else: raise AssertionError("failed child admitted")
    print(json.dumps({"verdict": "passed", "cold_commands": 3, "warm_commands": 0, "cold_seconds": cold["execution_summary"]["elapsed_seconds"], "warm_seconds": warm["execution_summary"]["elapsed_seconds"], "schema": "deploy/local-qualification-test/v1"}))
