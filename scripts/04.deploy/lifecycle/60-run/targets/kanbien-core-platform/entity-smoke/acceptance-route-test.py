#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.acceptance-route
#   version: 4
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-21"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual offline route parsers and current-reference dispatch with explicit controlled validators, never fabricated live acceptance.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.test.entity-smoke.acceptance-controls.wrapper
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-control-test.sh
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
from contextlib import redirect_stdout
import copy
import hashlib
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import yaml

if not __debug__: raise SystemExit("ENTITY_SMOKE_ACCEPTANCE_ROUTE_ASSERTIONS_DISABLED")


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


DIRECTORY = Path(__file__).parent
STATE = module("entity_smoke_route_fixture_state", DIRECTORY / "acceptance-state.py")
K = STATE.K
ROOT = K.C.ROOT
R = module("entity_smoke_route_fixture_compiler", ROOT / "scripts/04.deploy/lifecycle/60-run/validate-acceptance-route/script.py")
G = module("entity_smoke_route_fixture_scope", ROOT / "scripts/04.deploy/lifecycle/60-run/promote-accepted-scope/script.py")
PROMOTE = module("entity_smoke_route_fixture_promotion", DIRECTORY / "acceptance-promote.py")


def rejection(call, owner, code):
    try: call()
    except owner as failure: assert getattr(failure, "code", str(failure)) == code, (str(failure), code)
    else: raise AssertionError("Expected acceptance-route rejection: " + code)


def report(call):
    output = io.StringIO()
    with redirect_stdout(output): status = call()
    return status, json.loads(output.getvalue()), output.getvalue()


def recovery_applicability_protocols():
    """Real isolated Git history, not simulated live recovery evidence."""
    A = K.A
    with tempfile.TemporaryDirectory(prefix="entity-smoke-applicability-") as temporary:
        root = Path(temporary)
        def git(*args):
            result = subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                                     *args], cwd=root, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        git("init", "--quiet")
        protected = root / "runtime"; protected.mkdir()
        source = protected / "adapter.ts"; source.write_text("original recovery boundary\n")
        feature = root / "feature.ts"; feature.write_text("first feature\n")
        config = root / "scope.yml"; config.write_text("runtime: {schema: feature}\nchange_impact: {inputs: [old]}\n")
        permission = root / "permissions.yml"; permission.write_text("roles: bounded\n")
        schema = root / "schema"; schema.mkdir(); (schema / "v1.sql").write_text("original schema\n")
        git("add", "."); git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture baseline")
        first = git("rev-parse", "HEAD")
        sha = lambda path: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        prior_rollback = {"source_revision": first, "configuration_contract_sha256": sha(config),
            "permission_contract_sha256": sha(permission), "dependency_incarnation_sha256": "sha256:" + "c" * 64}
        feature.write_text("changed feature behaviour needs fresh functional proof\n")
        config.write_text("# new metadata\nruntime: {schema: feature}\nchange_impact: {inputs: [new]}\n")
        git("add", "."); git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture feature update")
        second = git("rev-parse", "HEAD")
        candidate_rollback = {**prior_rollback, "source_revision": second, "configuration_contract_sha256": sha(config)}
        def reuse(candidate=candidate_rollback):
            return A.POLICY.rollback_applicability(prior_rollback, candidate, "scope.yml", "permissions.yml", ["schema"], root=root)
        applicable = reuse()
        assert applicable["schema"] == "deploy/accepted-rollback-applicability/v1"
        assert applicable["predecessor_configuration_sha256"] != applicable["configuration_sha256"]
        assert not any(k in applicable for k in ("accepted", "passed", "current_health", "approval"))
        rejection(lambda: A.POLICY.rollback_applicability(prior_rollback, candidate_rollback,
            "scope.yml", "permissions.yml", ["missing-schema"], root=root), A.POLICY.PolicyFailure,
            "acceptance-recovery-inputs-empty")
        for replacement, code in (({"configuration_contract_sha256": "sha256:" + "e" * 64}, "acceptance-rollback-contract-hash-mismatch"),
            ({"permission_contract_sha256": "sha256:" + "e" * 64}, "acceptance-rollback-contract-hash-mismatch"),
            ({"dependency_incarnation_sha256": "sha256:" + "e" * 64}, "acceptance-rollback-incarnation-changed"),
            ({"source_revision": "e" * 40}, "acceptance-rollback-contract-unavailable"),
            ({"source_revision": "--private-canary"}, "acceptance-rollback-source-invalid")):
            rejection(lambda: reuse({**candidate_rollback, **replacement}), A.POLICY.PolicyFailure, code)
        binding = {"source_revision": first, "configuration_contract_sha256": "sha256:" + "a" * 64,
                   "permission_contract_sha256": "sha256:" + "b" * 64, "dependency_incarnation_sha256": "sha256:" + "c" * 64,
                   "proof_label": "entity-smoke-" + "a" * 24, "record_digest": "d" * 64}
        candidate = {**binding, "source_revision": second}
        result = A.recovery_applicability(binding, candidate, ["runtime", "new-lockfile"], root=root)
        with patch.object(A.POLICY, "recovery_applicability", wraps=A.POLICY.recovery_applicability) as shared:
            assert A.recovery_applicability(binding, candidate, ["runtime", "new-lockfile"], root=root) == result
            assert shared.call_count == 1 and shared.call_args.kwargs['additional_bindings'] == ('proof_label', 'record_digest')
        assert result["predecessor_source"] == first and result["candidate_source"] == second
        assert result["input_paths"] == ["new-lockfile", "runtime"]
        requirements = A.POLICY.recovery_requirements(binding, candidate, ["runtime", "new-lockfile"],
            root=root, additional_bindings=("proof_label", "record_digest"))
        assert requirements["mode"] == "reuse" and requirements["changed_bindings"] == []
        # A new input, changed input and deletion must all invalidate retained
        # capability proof even though the deployment template did not change.
        for filename, content in (("new-lockfile", "new dependency"), ("runtime/adapter.ts", "changed adapter"), ("runtime/adapter.ts", None)):
            target = root / filename
            if content is None: target.unlink()
            else: target.write_text(content)
            git("add", "-A"); git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture protected change")
            changed = {**candidate, "source_revision": git("rev-parse", "HEAD")}
            rejection(lambda: A.recovery_applicability(binding, changed, ["runtime", "new-lockfile"], root=root),
                      A.EvidenceFailure, "acceptance-recovery-requalification-required")
            requirements = A.POLICY.recovery_requirements(binding, changed, ["runtime", "new-lockfile"],
                root=root, additional_bindings=("proof_label", "record_digest"))
            assert requirements["mode"] == "requalify"
            assert requirements["changed_bindings"] == ["recovery_inputs"]
            assert requirements["candidate_inputs_sha256"] != requirements["predecessor_inputs_sha256"]
            assert not any(key in requirements for key in ("passed", "accepted", "evidence", "approval"))
        for field in ("configuration_contract_sha256", "permission_contract_sha256"):
            requirements = A.POLICY.recovery_requirements(binding, {**candidate, field: "sha256:" + "e" * 64},
                ["runtime"], root=root, additional_bindings=("proof_label", "record_digest"))
            assert requirements["mode"] == "requalify" and requirements["changed_bindings"] == [field]
        for field in ("dependency_incarnation_sha256", "proof_label", "record_digest"):
            replacement = "sha256:" + "e" * 64 if field.endswith("sha256") else "different"
            rejection(lambda: A.POLICY.recovery_requirements(binding, {**candidate, field: replacement},
                ["runtime"], root=root, additional_bindings=("proof_label", "record_digest")),
                A.POLICY.PolicyFailure, "acceptance-recovery-binding-changed")
        for field in A.POLICY.BINDINGS:
            for invalid in (None, "", 42, [], "sha256:wrong"):
                rejection(lambda: A.POLICY.recovery_requirements(binding, {**candidate, field: invalid},
                    ["runtime"], root=root), A.POLICY.PolicyFailure, "acceptance-recovery-binding-invalid")
        for field in ("configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256", "proof_label", "record_digest"):
            rejection(lambda: A.recovery_applicability(binding, {**candidate, field: "changed"}, ["runtime"], root=root),
                      A.EvidenceFailure, "acceptance-recovery-binding-changed")
        for paths in ([], ["runtime", "runtime"], ["../runtime"], ["runtime/*"], [":(exclude)runtime"], [42]):
            rejection(lambda: A.recovery_input_paths(paths), A.EvidenceFailure, "acceptance-recovery-input-paths-invalid")
        rejection(lambda: A.recovery_input_tree(first, ["nonexistent"], root=root), A.EvidenceFailure, "acceptance-recovery-inputs-empty")
        rejection(lambda: A.recovery_input_tree("e" * 40, ["runtime"], root=root), A.EvidenceFailure, "acceptance-recovery-inputs-unavailable")
        rejection(lambda: A.recovery_input_tree("--private-canary", ["runtime"], root=root), A.EvidenceFailure, "acceptance-recovery-input-source-invalid")
        # Reuse is bound to immutable sources: present working-tree contents
        # cannot conceal a committed operational change or missing contract.
        for filename, content, code in (("scope.yml", "runtime: {schema: other}\n", "acceptance-rollback-fresh-compatibility-required"),
                ("scope.yml", "runtime: {schema: feature}\nruntime: {schema: feature}\n", "acceptance-rollback-configuration-invalid"),
                ("permissions.yml", "roles: broadened\n", "acceptance-rollback-fresh-compatibility-required"),
                ("schema/v2.sql", "new migration\n", "acceptance-rollback-fresh-compatibility-required"),
                ("schema/v1.sql", "changed schema\n", "acceptance-rollback-fresh-compatibility-required"),
                ("schema/v1.sql", None, "acceptance-rollback-fresh-compatibility-required"),
                ("scope.yml", None, "acceptance-rollback-contract-unavailable")):
            target = root / filename; original = target.read_bytes() if target.exists() else None
            if content is None: target.unlink()
            else: target.write_text(content)
            git("add", "-A"); git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture rollback boundary change")
            changed = {**candidate_rollback, "source_revision": git("rev-parse", "HEAD"),
                "configuration_contract_sha256": sha(config) if config.exists() else candidate_rollback["configuration_contract_sha256"],
                "permission_contract_sha256": sha(permission)}
            if original is None: target.unlink()
            else: target.write_bytes(original)
            rejection(lambda: reuse(changed), A.POLICY.PolicyFailure, code)
            git("add", "-A"); git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture restored boundary")


def candidate_construction_protocols():
    """Actual feature caller preserves its prior bytes without live collection."""
    recovery_namespace_protocols()
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    digest = lambda value: "sha256:" + hashlib.sha256(value).hexdigest()
    packet = {"binding": {"source_revision": "a" * 40, "image_digest": "sha256:" + "b" * 64,
              "configuration_contract_sha256": "sha256:" + "c" * 64, "permission_contract_sha256": "sha256:" + "d" * 64},
              "runtime": {"observed_at": "2026-11-15T10:00:00Z"}, "fixture": "not-live-proof"}
    identifiers = set()
    for changed in [None, "source_revision", "image_digest", "configuration_contract_sha256", "permission_contract_sha256", "proof"]:
        value = copy.deepcopy(packet)
        if changed == "proof": value["fixture"] = "changed-not-live-proof"
        elif changed is not None: value["binding"][changed] = "e" * 40 if changed == "source_revision" else "sha256:" + "e" * 64
        proof_bytes = canonical(value) + b"\n"
        proof_name = "entity-smoke-" + hashlib.sha256(canonical(value)).hexdigest() + ".json"
        proofs = {"entity-smoke-complete-proof": {"path": "proof-receipts/" + proof_name, "sha256": digest(proof_bytes)}}
        contracts = {"configuration_contract": {"path": str((K.C.CONTRACT.parent / "declaration-contract.yml").relative_to(ROOT)), "sha256": value["binding"]["configuration_contract_sha256"]},
                     "permission_contract": {"path": str(K.C.DEPLOY.SOURCE.relative_to(ROOT)), "sha256": value["binding"]["permission_contract_sha256"]}}
        identity = {"target": K.TARGET, "scope": K.SCOPE, "source_revision": value["binding"]["source_revision"],
                    "image_digest": value["binding"]["image_digest"], **contracts, "proof_set_sha256": digest(canonical(proofs))}
        identifier = "release-" + hashlib.sha256(canonical(identity)).hexdigest()[:24]
        expected = {"schema": "deploy/release-candidate/v1", "target": K.TARGET, "scope": K.SCOPE, "status": "verified", "evidence_class": "live",
                    "release": {"id": identifier, **{key: item for key, item in identity.items() if key not in {"target", "scope"}}},
                    "proof": {"accepted_at": value["runtime"]["observed_at"], "receipt_count": 1}, "proof_set": proofs}
        with patch.object(K.S, "candidate_document", wraps=K.S.candidate_document) as constructor:
            material = K.candidate_material(value)
            assert constructor.call_count == 1
        assert material["proof"] == (K.EVIDENCE_ROOT / "proof-receipts" / proof_name, proof_bytes)
        assert material["candidate"] == (K.EVIDENCE_ROOT / "release-candidates" / (identifier + ".yml"), yaml.safe_dump(expected, sort_keys=False).encode())
        identifiers.add(identifier)
    assert len(identifiers) == 6, "each changed source/image/contract/proof must change release identity"
    with patch.object(K, "TARGET", "renamed-target"), patch.object(K, "SCOPE", "renamed-workload"):
        renamed = K.candidate_material(packet)["document"]
        assert (renamed["target"], renamed["scope"]) == ("renamed-target", "renamed-workload")
        assert renamed["release"]["id"] not in identifiers
    with patch.object(K.S, "candidate_document", side_effect=K.S.SuccessionFailure("release-succession-candidate-proof-invalid")):
        rejection(lambda: K.candidate_material(packet), K.S.SuccessionFailure, "release-succession-candidate-proof-invalid")


def recovery_namespace_protocols():
    policy = K.A.POLICY
    prior = {"schema": "deploy/entity-smoke-task-step/v3", "proof": "independently-validated"}
    tree = {"packets": [prior, {"schema": ["wrong-type"], "unchanged": True}]}
    compact = policy.prerequisite_references(tree, {prior["schema"]}, K.A.digest)
    digest = K.A.digest(prior)
    assert compact["packets"][0] == {"schema": "deploy/proof-prerequisite-reference/v1", "packet_sha256": digest}
    assert compact["packets"][1] == tree["packets"][1] and tree["packets"][0] == prior
    policy.validate_prerequisite_references(compact, {digest})
    rejection(lambda: policy.validate_prerequisite_references(compact, set()), policy.PolicyFailure, "acceptance-task-prerequisite-mismatch")
    for malformed in ({"schema": "deploy/proof-prerequisite-reference/v1"},
                      {**compact["packets"][0], "extra": True},
                      {**compact["packets"][0], "packet_sha256": []}):
        rejection(lambda: policy.validate_prerequisite_references(malformed, {digest}), policy.PolicyFailure, "acceptance-task-prerequisite-mismatch")
    aggregate = module("recovery_namespace_fixture", DIRECTORY / "acceptance-aggregate-test.py")
    packet = aggregate.successor_fixture(K)
    original, delivery = packet["binding"], packet["delivery"]
    resource = K.C.RESOURCE.recovery_binding(original, delivery)
    assert resource["proof_label"] == original["proof_label"] and resource["record_digest"] == original["record_digest"]
    assert K.C.RESOURCE.resource_label(resource) == delivery["smoke_label"] != original["proof_label"]
    assert "recovery_id" not in original and K.C.RESOURCE.resource_label(original) == original["proof_label"]
    context = {"delivery": delivery, "restore_binding": resource,
        "cache": K.C.delivery_cache(original["proof_label"], delivery),
        "custody": {"receipt_reference": delivery["candidate"]["receipt_reference"]}}
    assert K.C.RESOURCE.recovery_namespace(K.C, context) == delivery
    for changed in (
        {**context, "cache": context["cache"].parent},
        {**context, "custody": {"receipt_reference": "github-actions-run:1"}},
        {**context, "restore_binding": original},
        {**context, "restore_binding": {**resource, "recovery_id": "0" * 64}},
    ):
        rejection(lambda: K.C.RESOURCE.recovery_namespace(K.C, changed), K.C.RESOURCE.ResourceFailure, "resource-delivery-binding-mismatch")
    stack, change, database = K.D.RESTORE.names(resource)
    assert K.D.RESTORE.names(original) != (stack, change, database)
    snapshot = {"binding": resource, "source_resource_id": "db-CONTROLLEDORIGINAL",
        "snapshot": "kanbien-core-platform-" + delivery["smoke_label"], "original_commit_observed_at": "2026-11-19T00:00:00Z"}
    K.C.RESOURCE.validate_request("create-recovery-point", snapshot)
    rejection(lambda: K.C.RESOURCE.validate_request("create-recovery-point", {**snapshot,
        "snapshot": "kanbien-core-platform-" + original["proof_label"]}), K.C.RESOURCE.ResourceFailure, "resource-request-invalid")
    request = {"binding": resource, "parameters_sha256": "sha256:" + "a" * 64, "template_sha256": "sha256:" + "b" * 64,
        "stack_arn": "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + stack + "/fixture",
        "change_set_arn": "arn:aws:cloudformation:eu-west-1:337159794548:changeSet/" + change + "/fixture"}
    K.C.RESOURCE.validate_request("execute-restore", request)
    rejection(lambda: K.C.RESOURCE.validate_request("execute-restore", {**request,
        "stack_arn": "arn:aws:cloudformation:eu-west-1:337159794548:stack/" + K.D.RESTORE.names(original)[0] + "/fixture"}), K.C.RESOURCE.ResourceFailure, "resource-request-invalid")
    for invalid in (None, "", "a" * 63, "../../source", 42):
        rejection(lambda: K.C.RESOURCE.validate_binding({**resource, "recovery_id": invalid}), K.C.RESOURCE.ResourceFailure, "resource-binding-invalid")


def successor_state_protocols():
    """Real local succession/history with explicitly controlled typed proof packets."""
    K, S = STATE.K, STATE.S
    with tempfile.TemporaryDirectory(prefix="entity-smoke-successor-state-") as temporary:
        base = Path(temporary)
        root = base / STATE.EVIDENCE_PATH
        with patch.object(S, "REPOSITORY_ROOT", base), patch.object(S, "EVIDENCE_CLASS", "simulated"), \
                patch.object(K, "EVIDENCE_ROOT", root), patch.object(K, "validate_packet", side_effect=lambda packet, **kw: packet):
            owner = STATE.State(base, rehearsal=True)
            first = {"schema": K.SCHEMA, "binding": {"source_revision": "a" * 40, "image_digest": "sha256:" + "a" * 64,
                "configuration_contract_sha256": "sha256:" + "b" * 64, "permission_contract_sha256": "sha256:" + "c" * 64,
                "dependency_incarnation_sha256": "sha256:" + "d" * 64, "proof_label": "entity-smoke-" + "a" * 24,
                "record_digest": "e" * 64}, "runtime": {"observed_at": "2026-11-15T12:00:00Z"},
                "fixture": "prevalidated-protocol-not-live-proof"}
            def retain(packet):
                material = K.candidate_material(packet)
                for path, payload in (material["proof"], material["candidate"]):
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
                return owner.candidate(material["candidate"][0], current_contracts=False)
            initial = retain(first)
            initial_id = S.release_id(initial["identity"])
            S.promote(root, target=K.TARGET, scope=K.SCOPE, identity=initial["identity"], source_path=initial["path"],
                      source_digest=initial["sha256"], expected_predecessor="none", legacy=False)
            assert owner.current()["reference"]["release_id"] == initial_id
            second = copy.deepcopy(first)
            second["schema"] = K.SUCCESSOR_SCHEMA
            second["binding"].update(source_revision="f" * 40, image_digest="sha256:" + "f" * 64)
            second["runtime"]["observed_at"] = "2026-11-15T12:01:00Z"
            second["delivery"] = {"expected_predecessor": initial_id, "predecessor": {"release_id": initial_id,
                **{key: initial["identity"][key] for key in ("source_revision", "image_digest", "proof_set_sha256")}}}
            second["predecessor"] = {"release_id": initial_id, "candidate_record": str(initial["path"].relative_to(root)),
                "candidate_sha256": initial["sha256"], "applicability": {"fixture": "source-comparison-tested-separately"}}
            successor = retain(second)
            legacy = copy.deepcopy(second)
            legacy["schema"] = K.LEGACY_SUCCESSOR_SCHEMA
            historical = retain(legacy)
            assert owner.candidate(historical["path"], current_contracts=False)["packet"] == legacy
            rejection(lambda: owner.candidate(historical["path"]), STATE.StateFailure,
                      "acceptance-current-migration-proof-required")
            successor_id = S.release_id(successor["identity"])
            assert successor_id != initial_id
            for mutate, code in (
                (lambda value: value["predecessor"].update(candidate_sha256="sha256:" + "0" * 64), "acceptance-state-predecessor-custody-mismatch"),
                (lambda value: value["delivery"]["predecessor"].update(image_digest="sha256:" + "0" * 64), "acceptance-state-predecessor-custody-mismatch"),
                (lambda value: value["binding"].update(record_digest="0" * 64), "acceptance-state-predecessor-binding-mismatch")):
                invalid = copy.deepcopy(second); mutate(invalid)
                rejection(lambda: retain(invalid), STATE.StateFailure, code)
            S.promote(root, target=K.TARGET, scope=K.SCOPE, identity=successor["identity"], source_path=successor["path"],
                      source_digest=successor["sha256"], expected_predecessor=initial_id, legacy=False)
            assert owner.current()["reference"]["release_id"] == successor_id
            verdict, selected = S.promote(root, target=K.TARGET, scope=K.SCOPE, identity=successor["identity"], source_path=successor["path"],
                source_digest=successor["sha256"], expected_predecessor=initial_id, legacy=False)
            assert verdict == "already-current" and selected == successor_id
            # Historical state reads neither reinterpret applicability against
            # today's Git checkout nor claim fresh provider health.
            with patch.object(K.A, "recovery_applicability", side_effect=AssertionError("historical Git lookup")):
                assert owner.current()["packet"] == second
            assert initial["path"].read_bytes() == S.rendered(initial["record"])


def promotion_protocols(base):
    """Actual promotion consumer, explicit prevalidated-candidate/source doubles."""
    P, K, S = PROMOTE, PROMOTE.K, PROMOTE.S
    root = base / "controlled-promotion-protocol-not-live-custody"; root.mkdir()
    (root / S.HISTORY_DIRECTORY).mkdir()
    now = datetime.now(timezone.utc)
    stamp = lambda seconds: (now + timedelta(seconds=seconds)).isoformat()
    packet = {"controller_sha256": "sha256:" + "a" * 64,
        "runtime": {"task": "controlled-runtime", "definition": "controlled-definition", "observed_at": stamp(-1),
                    "source_resource_id": "controlled-database", "database_name": "controlled"},
        "binding": {"image_digest": "sha256:" + "c" * 64},
        "controls": {"restore-cleanup": {"facts": {"observed_at": stamp(-10)}}},
        "tasks": {"final-read": {"operation": {"name": "final-read", "phase": "operation", "packet": {"receipt": {
            "task": {"created_at": stamp(-5), "stopped_at": stamp(-4)}, "collected_at": stamp(-3)}}}}}}
    identity = {"controlled": "not-a-live-release-identity"}
    identifier = S.release_id(identity)
    candidate = {"packet": packet, "identity": identity, "path": root / "candidate.yml", "sha256": "sha256:" + "b" * 64}
    calls = []
    class CheckedState:
        def __init__(self): self.root = root
        def candidate(self, path): calls.append("candidate"); return candidate
        def current(self): calls.append("checked-current"); return {"reference": {"release_id": identifier}}
    runtime = {"task": "controlled-runtime", "healthy": True, "database": "controlled-database"}
    def provider(service, operation, **kwargs):
        assert (service, operation) == ("rds", "describe-db-instances")
        return {"DBInstances": [{"DBInstanceStatus": "available", "DbiResourceId": runtime["database"], "DBName": "controlled"}]}
    def promote(*args, **values):
        calls.append("release-promotion"); assert values["expected_predecessor"] == "none"
        return "promoted", identifier
    def scope(*args, **values): calls.append("scope-promotion"); return {"verdict": "promoted"}
    args = SimpleNamespace(inputs=base / "controlled-input.yml", candidate_record=candidate["path"],
        scope_contract=K.C.CONTRACT.parent / "declaration-contract.yml", expected_predecessor="none")
    with patch.object(P.STATE, "State", CheckedState), patch.object(K, "resolve_inputs", return_value=SimpleNamespace(receipt=base / "receipt")), patch.object(K.C.ALIGN, "read_receipt", return_value={}), patch.object(K.C.ALIGN, "source_preflight"), patch.object(K, "retained_source_evidence", return_value=None), patch.object(K, "gather", side_effect=AssertionError("promotion must reuse retained proof")), patch.object(K.C.RESOURCE, "service", return_value={"runningCount": 1, "pendingCount": 0}), patch.object(K.C.RESOURCE, "running_service_tasks", side_effect=lambda provider: [runtime["task"]]), patch.object(K.C.RESOURCE, "task", side_effect=lambda *a: {"lastStatus": "RUNNING", "healthStatus": "HEALTHY" if runtime["healthy"] else "UNHEALTHY"}), patch.object(K.C, "source_digest", return_value=packet["controller_sha256"]), patch.object(K.C, "retained_controller", side_effect=lambda value, current: K.require(current == packet["controller_sha256"], "acceptance-promotion-candidate-changed")), patch.object(S, "current", return_value=None), patch.object(S, "promote", side_effect=promote), patch.object(K, "module", return_value=SimpleNamespace(promote=scope)):
        progress = {"effect": "not-started"}
        assert P.run(args, provider, progress)["current_readiness"] is False
        assert calls.count("release-promotion") == calls.count("scope-promotion") == 1
        calls.clear()
        with patch.object(K.C, "now", return_value=stamp(86400)):
            assert P.run(args, provider, {})["verdict"] == "accepted"
        assert calls.count("release-promotion") == 1
        calls.clear(); runtime["task"] = "different-current-task"
        rejection(lambda: P.run(args, provider, {}), K.CollectionFailure, "acceptance-promotion-candidate-not-current")
        assert "release-promotion" not in calls and "scope-promotion" not in calls
        runtime["task"] = "controlled-runtime"; runtime["healthy"] = False; calls.clear()
        rejection(lambda: P.run(args, provider, {}), K.CollectionFailure, "acceptance-promotion-candidate-not-current")
        assert "release-promotion" not in calls and "scope-promotion" not in calls
        runtime["healthy"] = True; calls.clear()
        runtime["database"] = "other-database"
        rejection(lambda: P.run(args, provider, {}), K.CollectionFailure, "acceptance-promotion-database-changed")
        assert "release-promotion" not in calls
        runtime["database"] = "controlled-database"
        with patch.object(K.C, "source_digest", return_value="sha256:" + "0" * 64):
            rejection(lambda: P.run(args, provider, {}), K.CollectionFailure, "acceptance-promotion-candidate-changed")
        assert "release-promotion" not in calls
        calls.clear()
        with patch.object(S, "current", return_value={"release_id": identifier}):
            result = P.run(args, object(), {})
            assert result["verdict"] == "retained" and result["current_readiness"] is False and "gather" not in calls
        calls.clear()
        history = root / S.HISTORY_DIRECTORY / (identifier + ".yml")
        history.write_text("controlled-interruption-protocol-not-accepted-evidence")
        with patch.object(S, "history_identity", return_value=(K.TARGET, K.SCOPE, identifier, None)):
            result = P.run(args, object(), {})
            assert result["verdict"] == "retained" and result["current_readiness"] is False and "gather" not in calls
        # Retain the original release effect if the later local index step fails.
        with patch.object(S, "history_identity", return_value=(K.TARGET, K.SCOPE, identifier, None)), patch.object(K, "module", return_value=SimpleNamespace(promote=lambda *args, **kw: (_ for _ in ()).throw(ValueError("scope-promotion-inventory-invalid")))):
            progress = {"effect": "not-started"}
            rejection(lambda: P.run(args, object(), progress), K.CollectionFailure, "scope-promotion-inventory-invalid")
            assert progress["effect"] == "accepted-reference-current-scope-transition-reconciliation-required"


def source_boundary_protocols(base):
    """Real Git/filesystem boundary; task/control/custody observers are doubles.

    All generated candidates remain in this disposable fixture, never the repo's
    live evidence directory and never an AWS acceptance result.
    """
    K = STATE.K
    M = K.C.ALIGN
    aggregate = module("entity_smoke_source_boundary_primitives", DIRECTORY / "acceptance-aggregate-test.py")
    root = base / "source-boundary-controlled-proof-not-live"
    root.mkdir()
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    def git(*arguments):
        result = subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull, "-c", "commit.gpgsign=false",
            "-c", "user.name=Controlled fixture", "-c", "user.email=fixture@example.invalid", *arguments],
            cwd=root, env=environment, capture_output=True, text=True, check=True)
        return result.stdout
    git("init", "--quiet", "--initial-branch", "main")
    (root / ".gitignore").write_text(".cache/\n")
    (root / "source.txt").write_text("original source\n")
    (root / "settings.yml").write_text("original: configuration\n")
    git("add", "--", ".gitignore", "source.txt", "settings.yml")
    git("commit", "--quiet", "-m", "controlled fixture source")
    revision = git("rev-parse", "HEAD").strip()
    # Construct one consistently bound release, including predecessor hashes;
    # this source-boundary fixture does not exercise historical transitions.
    packet = aggregate.fixture(K, source_revision=revision)
    packet["evidence_class"] = "live"  # Exercised envelope only; primitive owners below are controlled.
    packet["binding"]["permission_contract_sha256"] = K.C.digest_file(K.C.DEPLOY.SOURCE)
    custody = dict(packet["package"])
    args = SimpleNamespace(receipt=root / ".cache/controlled-custody.json", proof_label=packet["binding"]["proof_label"], expected_digest=packet["binding"]["record_digest"])
    cache = root / ".cache/entity-smoke-live" / args.proof_label
    evidence = root / K.EVIDENCE_ROOT.relative_to(ROOT)
    def command(arguments, timeout=30):
        if arguments[0] == "git": return git(*arguments[1:])
        assert any("declaration-coverage" in part or "inventory-deploy-control" in part for part in arguments)
        return json.dumps({"verdict": "covered", "findings": []})
    with patch.object(K.C, "ROOT", root), patch.object(M, "ROOT", root), patch.object(K, "EVIDENCE_ROOT", evidence), \
         patch.object(K.C, "CONTRACT", root / K.C.CONTRACT.relative_to(ROOT)), \
         patch.object(K.C.DEPLOY, "SOURCE", root / K.C.DEPLOY.SOURCE.relative_to(ROOT)), \
         patch.object(K.C, "source_digest", return_value=packet["controller_sha256"]), \
         patch.object(M, "command", side_effect=command), patch.object(M, "read_receipt", return_value=custody), \
         patch.object(K.A, "validate_task", side_effect=lambda value, *a, **kw: value), \
         patch.object(K, "validate_control", return_value=None):
        M.source_preflight(custody)
        assert K.retained_source_evidence(args, custody) is None
        observation = cache / "acceptance-observation.json"
        K.A.immutable_json(observation, packet)
        original_observation = observation.read_bytes()
        material = K.candidate_material(packet)
        proof, candidate = material["proof"][0], material["candidate"][0]
        # Crash after the real proof copy and before the real candidate copy.
        with patch.object(K.S, "immutable_write", side_effect=OSError("private-source-boundary-canary")):
            try: K.retain(packet, cache)
            except OSError: pass
            else: raise AssertionError("controlled interrupted copy did not fail")
        assert proof.is_file() and not candidate.exists()
        selection = K.retained_source_evidence(args, custody)
        rejection(lambda: M.source_preflight(custody), M.AlignmentFailure, "alignment-committed-source-required")
        M.source_preflight(custody, retained_source_evidence=selection)
        # Actual collection reconciliation finishes its copy without fresh AWS
        # observations, rewritten timestamps, or another task/control execution.
        with patch.object(K, "gather", side_effect=AssertionError("historical collection must not reobserve or execute")):
            marker, verdict = K.collect(args, object())
        assert verdict == "retained" and marker["scope_acceptance"] is marker["current_readiness"] is False
        assert candidate.is_file() and observation.read_bytes() == original_observation
        assert proof.read_bytes() == material["proof"][1] and candidate.read_bytes() == material["candidate"][1]
        rejection(lambda: M.source_preflight(custody), M.AlignmentFailure, "alignment-committed-source-required")
        M.source_preflight(custody, retained_source_evidence=K.retained_source_evidence(args, custody))
        # Real nested acceptance prerequisite -> committed-source guard, with
        # controlled restore work after that boundary (no AWS or acceptance).
        nested = K.T.ACCEPTANCE
        class SourceReached(Exception): pass
        def nested_source(values, provider, **options):
            M.source_preflight(custody, **{key: value for key, value in options.items() if key == "retained_source_evidence"})
            raise SourceReached()
        owner = SimpleNamespace(C=K.D.C, TASK=K.D.TASK, R=K.D.R, source=nested_source, known=lambda: (M.AlignmentFailure,))
        nested_args = K.selected_args(args, "acceptance", "verifier", "read")
        with patch.object(nested, "restore_owner", return_value=owner):
            try: nested.prerequisites(K.T.dependencies(), {"retained_source_evidence": selection}, nested_args, object())
            except SourceReached: pass
            else: raise AssertionError("nested source guard did not preserve generated allowance")
            with patch.object(K, "collect", side_effect=lambda *a: nested.prerequisites(K.T.dependencies(), {}, nested_args, object())), \
                 patch.object(sys, "argv", ["acceptance-route.py", "--receipt", str(args.receipt), "--proof-label", args.proof_label,
                     "--expected-digest", args.expected_digest, "--write-candidate"]):
                status, result, raw = report(K.main)
            assert status == 1 and result["condition"] == "alignment-committed-source-required"
            assert result["effect"] == "no-provider-mutation-no-scope-promotion" and "private-source-boundary-canary" not in raw
        # Keep every real source-guard link in the fresh gather path. Stop at
        # its first provider observer, after real Git validation has passed.
        class AfterSource(Exception): pass
        with patch.object(K.C, "local_checks", return_value=None), patch.object(M, "inspect", side_effect=AfterSource):
            try: K.gather(args, object())
            except AfterSource: pass
            else: raise AssertionError("fresh gather did not reach its controlled provider boundary")
        # Separately exercise the final real source recheck after controlled
        # target/task/control observations, so dropping either forwarding link
        # reintroduces the original dirty-proof rejection and fails this case.
        retained = packet["controls"]
        value = {"cache": cache, "custody": custody, "binding": {key: value for key, value in packet["binding"].items() if key != "record_digest"},
            "artifact": packet["controller_sha256"], "history": {"prerequisites": {"packets": retained}}, "snapshot": retained["snapshot"],
            "server": {"definition": packet["runtime"]["definition"]},
            "parameters": {"DatabaseResourceId": packet["runtime"]["source_resource_id"], "DatabaseName": packet["runtime"]["database_name"]}}
        cleanup = {"required_after": retained["restore-cleanup"]["facts"]["observed_at"],
            "reader": {"context": {"binding": packet["restored_binding"]}, "deployed": retained["restore-deployment"]}, "receipt": retained["restore-cleanup"]}
        (cache / "replacement-receipt.json").write_text(json.dumps(retained["server-replacement"]))
        running = {"taskArn": packet["runtime"]["task"], "createdAt": packet["runtime"]["created_at"], "startedAt": packet["runtime"]["started_at"], "lastStatus": "RUNNING", "healthStatus": "HEALTHY"}
        with patch.object(K.D, "source", return_value=value) as source_call, \
             patch.object(K.S, "recovery_policy", return_value={"policy": "stop-own-scope-workloads-preserve-data", "accepted_release_id": "none"}), \
             patch.object(K.D, "completed_cleanup", return_value=cleanup), patch.object(K, "task_proofs", return_value=packet["tasks"]), \
             patch.object(K, "control_proof", side_effect=lambda name, *a: retained[name]), \
             patch.object(K.C.RESOURCE, "service", return_value={"runningCount": 1, "pendingCount": 0}), \
             patch.object(K.C.RESOURCE, "running_service_tasks", return_value=[running["taskArn"]]), \
             patch.object(K.C.RESOURCE, "task", return_value=running), \
             patch.object(K.T.RECOVERY.STATE.STOP, "artifact_basis", return_value=packet["controller_basis"]), \
             patch.object(K.C, "now", return_value=packet["runtime"]["observed_at"]):
            fresh, returned_cache = K.gather(args, object())
        assert returned_cache == cache and fresh == packet
        assert source_call.call_args.kwargs == {"retained_source_evidence": selection}
        for path in (proof, candidate):
            original = path.read_bytes()
            for changed in (b"x" * len(original), original + b"\n"):
                path.write_bytes(changed)
                rejection(lambda: M.source_preflight(custody, retained_source_evidence=selection), M.AlignmentFailure, "alignment-retained-evidence-changed")
            path.write_bytes(original)
        for relative in ("source.txt", "settings.yml", "foreign\nprivate-source-boundary-canary.txt",
                         str((evidence / "proof-receipts" / ("entity-smoke-" + "f" * 64 + ".json")).relative_to(root)),
                         str((evidence / "release-candidates" / ("release-" + "f" * 24 + ".yml")).relative_to(root))):
            path = root / relative
            existed = path.exists()
            original = path.read_bytes() if existed else None
            path.write_text("unapproved change\n")
            rejection(lambda: M.source_preflight(custody, retained_source_evidence=selection), M.AlignmentFailure, "alignment-committed-source-required")
            if existed: path.write_bytes(original)
            else: path.unlink()
        git("add", "--", str(candidate.relative_to(root)))
        rejection(lambda: M.source_preflight(custody, retained_source_evidence=selection), M.AlignmentFailure, "alignment-committed-source-required")
        git("rm", "--cached", "--quiet", "--", str(candidate.relative_to(root)))
        original = proof.read_bytes()
        alternate = root / ".cache/controlled-proof.json"; alternate.write_bytes(original)
        proof.unlink(); proof.symlink_to(alternate)
        rejection(lambda: M.source_preflight(custody, retained_source_evidence=selection), M.AlignmentFailure, "alignment-retained-evidence-invalid")
        proof.unlink(); proof.write_bytes(original)
        for field, value in (("source_revision", "0" * 40), ("image_digest", "sha256:" + "0" * 64), ("receipt_reference", "wrong-receipt")):
            rejection(lambda: K.retained_source_evidence(args, {**custody, field: value}), K.CollectionFailure, "acceptance-source-evidence-binding-mismatch")
        with patch.object(K.C, "source_digest", return_value="sha256:" + "0" * 64), \
             patch.object(K.C, "retained_controller", side_effect=K.C.InfrastructureFailure("task-step-completion-artifacts-mismatch")):
            rejection(lambda: K.retained_source_evidence(args, custody), K.CollectionFailure, "acceptance-source-evidence-binding-mismatch")
        invalid = copy.deepcopy(selection)
        descriptor = next(iter(invalid["files"].values()))
        invalid["files"] = {"source.txt": descriptor, str(proof.relative_to(root)): descriptor}
        rejection(lambda: M.source_preflight(custody, retained_source_evidence=invalid), M.AlignmentFailure, "alignment-retained-evidence-invalid")
        observation.unlink()
        assert K.retained_source_evidence(args, custody) is None
        rejection(lambda: M.source_preflight(custody), M.AlignmentFailure, "alignment-committed-source-required")
        observation.write_bytes(original_observation)
        for payload, code in ((b"private-source-boundary-canary", "acceptance-collected-proof-unavailable"),
                              (b'{"native":"private-source-boundary-canary"}', "acceptance-collection-envelope-invalid")):
            observation.write_bytes(payload)
            rejection(lambda: K.retained_source_evidence(args, custody), K.CollectionFailure, code)
        observation.write_bytes(original_observation)
        # The selected safe cause reaches the actual public collector reporter.
        proof.write_bytes(b"x" * len(original))
        argv = ["acceptance-route.py", "--receipt", str(args.receipt), "--proof-label", args.proof_label, "--expected-digest", args.expected_digest, "--write-candidate"]
        with patch.object(sys, "argv", argv):
            status, result, raw = report(K.main)
        assert status == 1 and result["condition"] == "alignment-retained-evidence-changed" and "private-source-boundary-canary" not in raw
        proof.write_bytes(original)
        (root / "source.txt").write_text("different committed source\n")
        git("add", "--", "source.txt"); git("commit", "--quiet", "-m", "controlled different source")
        rejection(lambda: M.source_preflight(custody, retained_source_evidence=selection), M.AlignmentFailure, "alignment-source-checkpoint-mismatch")
    print(json.dumps({"schema": "deploy/entity-smoke-acceptance-source-fixture/v1", "verdict": "passed", "git_and_filesystem": "real-disposable-fixture",
        "proof_primitives": "controlled-not-live-evidence", "candidate_retention": "temporary-fixture-only", "aws_mutation": False}))


def accepted_rollback_protocols():
    """Real selector; explicit custody/comparison doubles, never live proof."""
    C = K.C
    predecessor = {"release_id": "release-" + "a" * 24, "source_revision": "b" * 40,
        "image_digest": "sha256:" + "c" * 64, "proof_set_sha256": "sha256:" + "d" * 64}
    receipt = {key: predecessor[key] for key in ("source_revision", "image_digest")}
    receipt.update(receipt_reference="github-actions-run:123", program_id="fixture-program", package_contract_id="fixture-package")
    accepted = {"reference": {"release_id": predecessor["release_id"]}, "identity": dict(predecessor),
        "packet": {"package": dict(receipt), "binding": {"fixture": "prior"}}, "sha256": "sha256:" + "e" * 64}
    owner = SimpleNamespace(State=lambda: SimpleNamespace(current=lambda: accepted), A=K.A, K=K)
    binding = {"source_revision": "f" * 40, "image_digest": "sha256:" + "0" * 64}
    args = SimpleNamespace(rollback_receipt=Path("/tmp/controlled-rollback-receipt.json"),
        rollback_compatibility_id="accepted-proof-" + "a" * 24)
    with patch.object(C, "module", return_value=owner), patch.object(C.ALIGN, "read_receipt", return_value=receipt), \
         patch.object(K.A.POLICY, "rollback_applicability", return_value={"comparison": "controlled"}) as compare:
        selected, metadata = C.rollback_selection(args, {"predecessor": predecessor}, binding)
        assert selected == {**binding, **{key: predecessor[key] for key in ("source_revision", "image_digest")}}
        assert metadata["compatibility_id"] == args.rollback_compatibility_id
        assert compare.call_args.args[:2] == (accepted["packet"]["binding"], binding)
        assert compare.call_args.args[2:4] == (C.ALIGN.SCOPE, str(C.DEPLOY.SOURCE.relative_to(C.ROOT)))
        expected = C.DEPLOY.fingerprint({"accepted_candidate_sha256": accepted["sha256"],
            "accepted_proof_set_sha256": predecessor["proof_set_sha256"], "applicability": {"comparison": "controlled"}})
        assert metadata["compatibility_sha256"] == expected
        for mapping, field, invalid in ((accepted["reference"], "release_id", "release-" + "9" * 24),
            (accepted["identity"], "proof_set_sha256", "sha256:" + "9" * 64),
            (receipt, "image_digest", "sha256:" + "9" * 64), (receipt, "receipt_reference", "github-actions-run:999"),
            (receipt, "program_id", "foreign-program")):
            original = mapping[field]; mapping[field] = invalid
            rejection(lambda: C.rollback_selection(args, {"predecessor": predecessor}, binding),
                C.InfrastructureFailure, "infrastructure-rollback-predecessor-mismatch")
            mapping[field] = original
        args.rollback_compatibility_id = "accepted-proof-" + "9" * 24
        rejection(lambda: C.rollback_selection(args, {"predecessor": predecessor}, binding), C.InfrastructureFailure, "infrastructure-rollback-predecessor-mismatch")
        args.rollback_compatibility_id = metadata["compatibility_id"]
        compare.side_effect = K.A.POLICY.PolicyFailure("acceptance-rollback-fresh-compatibility-required")
        rejection(lambda: C.rollback_selection(args, {"predecessor": predecessor}, binding), C.InfrastructureFailure, "acceptance-rollback-fresh-compatibility-required")
        owner.State = lambda: (_ for _ in ()).throw(STATE.StateFailure("acceptance-state-proof-hash-mismatch"))
        rejection(lambda: C.rollback_selection(args, {"predecessor": predecessor}, binding), C.InfrastructureFailure, "acceptance-state-proof-hash-mismatch")


def run():
    recovery_applicability_protocols()
    accepted_rollback_protocols()
    candidate_construction_protocols()
    successor_state_protocols()
    module("entity_smoke_route_aggregate_fixture", DIRECTORY / "acceptance-aggregate-test.py").run(K)
    contract = K.C.CONTRACT.parent / "declaration-contract.yml"
    assert R.inspect(contract)["verdict"] == "covered", "real offline parsers, not declared command existence"
    route, route_path = R.load_route(contract)
    schema = R.document(K.C.CONTRACT.parent / "acceptance-record-schema.yml")
    assert set(schema["composite_members"]["tasks"]) == set(K.A.TASKS)
    assert set(schema["composite_members"]["controls"]) == K.CONTROLS
    assert len(schema["composite_members"]["tasks"]) == len(K.A.TASKS) and len(schema["composite_members"]["controls"]) == len(K.CONTROLS)
    assert schema["required_proofs"] == list(route["proofs"]) == ["entity-smoke-complete-proof"]
    for field, value, expected in (("source", "unknown-source", "acceptance-route-record-source-unsupported"),
                                  ("path", "30-release-evidence/other.yml", "acceptance-route-current-reference-invalid"),
                                  ("schema", "deploy/accepted-release/v1", "acceptance-route-current-reference-invalid"),
                                  ("source", None, "acceptance-route-current-reference-selector-required")):
        invalid = copy.deepcopy(route)
        if value is None: invalid["accepted_record"].pop(field)
        else: invalid["accepted_record"][field] = value
        with patch.object(R, "load_route", return_value=(invalid, route_path)):
            observed = R.inspect(contract, probe_commands=False)
            assert expected in {item["code"] for item in observed["findings"]}
    args = K.parse(["--inputs", "/tmp/no-such-entity-smoke-manifest.json", "--write-candidate"])
    assert args.inputs is not None and args.receipt is None
    rejection(lambda: K.parse(["--inputs", "/tmp/manifest.json", "--write-candidate", "--retained-source-evidence", "private-cli-canary"]), K.CollectionFailure, "acceptance-arguments-invalid")
    rejection(lambda: K.parse(["--inputs", "/tmp/manifest.json", "--write-candidate", "--proof-label", "entity-smoke-" + "a" * 24]), K.CollectionFailure, "acceptance-arguments-invalid")
    # The actual CLI's offline branch must not read its nonexistent manifest.
    with patch.object(sys, "argv", ["acceptance-route.py", "--inputs", "/tmp/no-such-entity-smoke-manifest.json", "--write-candidate", "--validate-arguments"]), patch.object(K, "resolve_inputs", side_effect=AssertionError("offline manifest read")):
        status, observed, _ = report(K.main)
        assert status == 0 and observed["proof_contract"] == {key: value for key, value in route["proofs"]["entity-smoke-complete-proof"].items() if key not in {"command", "image_role"}}
    with tempfile.TemporaryDirectory(prefix="entity-smoke-acceptance-route-") as temporary:
        base = Path(temporary)
        promotion_protocols(base)
        source_boundary_protocols(base)
        receipt = base / "qualified.json"; receipt.write_text("{}")
        manifest = base / "inputs.yml"
        values = {"candidate_receipt": str(receipt), "proof_label": "entity-smoke-" + "a" * 24, "expected_digest": "b" * 64, "expected_predecessor": "none"}
        manifest.write_text(yaml.safe_dump({"schema": "deploy/acceptance-inputs/v1", "target": K.TARGET, "scope": K.SCOPE, "values": values}))
        resolved = K.resolve_inputs(K.parse(["--inputs", str(manifest), "--write-candidate"]))
        assert resolved.receipt == receipt and resolved.proof_label == values["proof_label"] and resolved.expected_digest == values["expected_digest"]
        manifest.write_text(yaml.safe_dump({"schema": "deploy/acceptance-inputs/v1", "target": K.TARGET, "scope": K.SCOPE, "values": {**values, "native": "private-manifest-canary"}}))
        rejection(lambda: K.resolve_inputs(K.parse(["--inputs", str(manifest), "--write-candidate"])), K.CollectionFailure, "acceptance-inputs-set-invalid")
        original_succession = STATE.S.REPOSITORY_ROOT, STATE.S.EVIDENCE_CLASS
        try:
            rejection(lambda: STATE.State(base), STATE.StateFailure, "acceptance-state-root-invalid")
            rejection(lambda: STATE.State(Path(tempfile.gettempdir()), rehearsal=True), STATE.StateFailure, "acceptance-state-rehearsal-root-invalid")
            owner = STATE.State(base / "state-reader-protocol", rehearsal=True)
            rejection(lambda: owner.current(), STATE.StateFailure, "acceptance-state-current-required")
            rejection(lambda: owner.candidate(owner.root / "release-candidates/release-" / "absent.yml"), STATE.StateFailure, "acceptance-state-record-unavailable")
            current = owner.root / STATE.S.CURRENT
            current.parent.mkdir(parents=True, exist_ok=True)
            source = base / "controlled-not-custody.yml"; source.write_text("controlled-read-only-symlink-check")
            current.symlink_to(source)
            rejection(lambda: owner.current(), K.C.RESOURCE.CONTROL.TaskFailure, "attempt-path-invalid")
            with patch.object(sys, "argv", ["acceptance-state.py", "--operation", "validate-current"]), patch.object(STATE, "State", return_value=owner):
                status, observed, raw = report(STATE.main)
                assert status == 1 and observed["condition"] == "attempt-path-invalid" and str(source) not in raw
        finally: STATE.S.REPOSITORY_ROOT, STATE.S.EVIDENCE_CLASS = original_succession
        # Exercise the real generic scope promoter, while its validator/inventory
        # dependencies are explicit controlled protocols, NOT target proof.
        scope = base / K.C.CONTRACT.parent.parent.relative_to(ROOT)
        declared = scope / "00-declaration/declaration-contract.yml"
        accepted = scope / "30-release-evidence/current-accepted-release.yml"
        index = scope.parent / "scope-index.yml"
        declared.parent.mkdir(parents=True); accepted.parent.mkdir(parents=True)
        declared.write_text(yaml.safe_dump({"target": K.TARGET, "scope": K.SCOPE}))
        accepted.write_text(yaml.safe_dump({"schema": "deploy/release-current-ref/v1", "target": K.TARGET, "scope": K.SCOPE, "status": "active"}))
        selection = {"schema": "deploy/scope-lifecycle-inventory/v1", "scopes": [{"id": K.SCOPE, "lifecycle": "candidate"}]}
        controlled_route = copy.deepcopy(route)
        controlled_route["accepted_record"]["schema_path"] = "unused-by-this-controlled-generic-protocol"
        actual_load, actual_inspect = R.load_route, R.inspect
        R.load_route = lambda path, root=ROOT: (controlled_route, route_path)
        R.inspect = lambda *values, **named: {"verdict": "covered"}
        state_report = {"verdict": "validated", "target": K.TARGET, "scope": K.SCOPE, "evidence_class": "simulated"}
        observed_calls = []
        def validator(argv, **named):
            observed_calls.append(list(argv))
            assert "--rehearsal-root" in argv and str(base) in argv
            return SimpleNamespace(returncode=0, stdout=json.dumps(state_report))
        try:
            with patch.object(G, "route_module", return_value=R), patch.object(G, "inventory_module", return_value=SimpleNamespace(inspect=lambda *args: {"verdict": "passed"})), patch.object(G.subprocess, "run", side_effect=validator):
                index.write_text(yaml.safe_dump(selection))
                assert G.promote(declared, base, write=True, simulation=True)["verdict"] == "promoted"
                assert yaml.safe_load(index.read_text())["scopes"] == [{"id": K.SCOPE, "lifecycle": "active"}]
                for field, invalid in (("target", "wrong-target"), ("scope", "wrong-scope"), ("evidence_class", "live")):
                    index.write_text(yaml.safe_dump(selection)); previous = index.read_bytes()
                    saved = state_report[field]; state_report[field] = invalid
                    rejection(lambda: G.promote(declared, base, write=True, simulation=True), ValueError, "scope-promotion-current-validation-mismatch")
                    state_report[field] = saved
                    assert index.read_bytes() == previous
                # The absent-selector legacy path keeps its existing semantics.
                controlled_route["accepted_record"].pop("source")
                controlled_route["accepted_record"]["schema"] = "deploy/accepted-release/v1"
                accepted.write_text(yaml.safe_dump({"schema": "deploy/accepted-release/v1", "target": K.TARGET, "scope": K.SCOPE, "status": "rehearsed", "evidence_class": "simulated"}))
                index.write_text(yaml.safe_dump(selection))
                assert G.promote(declared, base, write=True, simulation=True)["verdict"] == "promoted"
                assert len(observed_calls) == 5
        finally: R.load_route, R.inspect = actual_load, actual_inspect
    with patch.object(sys, "argv", ["acceptance-state.py", "--operation", "validate-current"]), patch.object(STATE, "State", side_effect=RuntimeError("private-current-custody-canary")):
        status, observed, raw = report(STATE.main)
        assert status == 1 and observed["condition"] == "acceptance-boundary-not-confirmed" and "private-current" not in raw
    base = ["--inputs", "/tmp/nonexistent-proof.yml", "--candidate-record", "/tmp/release.yml", "--scope-contract", str(contract), "--expected-predecessor", "none", "--write"]
    with patch.object(sys, "argv", ["acceptance-promote.py", *base, "--validate-arguments"]), patch.object(PROMOTE, "run", side_effect=AssertionError("offline promotion")):
        status, observed, _ = report(PROMOTE.main)
        assert status == 0 and observed["verdict"] == "valid"
    rejection(lambda: PROMOTE.parse(base[:-1]), PROMOTE.K.CollectionFailure, "acceptance-promotion-arguments-invalid")
    for file, argv, condition in (("collect-acceptance.sh", ["--inputs", "/tmp/missing.yml", "--write-candidate"], "acceptance-arguments-invalid"),
                                  ("acceptance-state.sh", ["--operation", "validate-current"], "acceptance-state-arguments-invalid"),
                                  ("promote-acceptance.sh", base, "acceptance-promotion-arguments-invalid")):
        observed = subprocess.run(["bash", str(DIRECTORY / file), *argv, "--private-wrapper-canary"], capture_output=True, text=True, timeout=15, cwd=ROOT)
        assert observed.returncode == 1 and json.loads(observed.stdout)["condition"] == condition
        assert "private-wrapper" not in observed.stdout + observed.stderr
    print(json.dumps({"schema": "deploy/entity-smoke-acceptance-route-fixture/v1", "verdict": "passed", "provider_observation": False,
        "cases": ["real-route-offline-parsers", "explicit-selector-schema-and-path", "exact-composite-members", "bounded-manifest-and-no-offline-read", "manifest-values-and-native-extra-rejection", "closed-state-roots-and-missing-custody", "actual-generic-current-reference-branch-controlled-validator", "wrong-target-scope-evidence-class-before-index-write", "legacy-selector-absent-compatibility", "state-main-canary-private", "explicit-local-write-and-offline-promotion", "promotion-consumer-controlled-fresh-success", "different-or-missing-current-proof-before-promotion", "source-drift-before-promotion", "already-current-and-original-history-reconcile-without-health-claim", "post-reference-scope-failure-preserves-known-effect", "all-three-real-wrapper-rejections-private"]}))


if __name__ == "__main__": run()
