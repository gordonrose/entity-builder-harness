#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.scheduling-acceptance-proof
#   version: 1
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise additional scheduler proof custody through real scope collector and release identity boundaries without claiming unavailable live provenance.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.library.scheduling-acceptance-proof
#     path: scripts/04.deploy/lifecycle/60-run/release-succession/scheduling-proof.py
"""Controlled additional-proof integration, not complete HTTP or AWS acceptance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[5]
DIRECTORY = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


H = load("scheduling_proof_test_owner", DIRECTORY / "scheduling-proof.py")
S = load("scheduling_proof_test_succession", DIRECTORY / "script.py")
ROUTE = load("scheduling_proof_test_route", DIRECTORY.parent / "validate-acceptance-route/script.py")
CORE = load("scheduling_proof_test_core", DIRECTORY.parent / "targets/kanbien-core-platform/core-server-persistence/collect-acceptance-evidence/script.py")
ENTITY = load("scheduling_proof_test_entity", DIRECTORY.parent / "targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/implementation/acceptance-route.py")
CORE_READER = load("scheduling_proof_test_core_reader", DIRECTORY.parent / "targets/kanbien-core-platform/core-server-persistence/validate-accepted-release/script.py")
SOURCE, PRIMARY, TIME = "a" * 40, "sha256:" + "b" * 64, "2026-11-27T05:00:00Z"


def fixture(scope):
    subjects = H.selection(ROOT, "kanbien-core-platform", scope)
    custody = H.module(ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py", "scheduling_test_custody")
    components = {}
    for index, (role, selected) in enumerate(sorted(subjects.items())):
        components[role] = {"schema": custody.SCHEMA, "target": "kanbien-core-platform", "environment_class": "development",
            "provider_region_alias": "eu-west-1", **selected, "source_revision": SOURCE, "image_digest": "sha256:" + str(index + 1) * 64,
            "release_identity": "release-fixture", "checked_at": TIME, "checks": {key: "passed" for key in custody.BASE_CHECKS | {"ecr_scan"}},
            "verdict": "qualified", "receipt_reference": "github-actions-run:123"}
    runtime = {"schema": H.RUNTIME_SCHEMA, "evidence_class": "simulated", "target": "kanbien-core-platform", "scope": scope,
        "source_revision": SOURCE, "primary_image_digest": PRIMARY, "observed_at": TIME,
        "components": {role: {"program_id": receipt["program_id"], "image_digest": receipt["image_digest"],
            "version_arn": "arn:aws:lambda:eu-west-1:337159794548:function:fixture-" + role + ":1"} for role, receipt in components.items()},
        "observations": {name: {"controlled_operation": name, "receipt_sha256": "sha256:" + "c" * 64} for name in H.CASES}}
    return {"schema": H.SCHEMA, "profile": H.PROFILE, "target": "kanbien-core-platform", "scope": scope,
        "source_revision": SOURCE, "primary_image_digest": PRIMARY, "recorded_at": TIME, "components": components, "evidence": runtime}


def controlled_owner(root, evidence, expected, *, historical):
    # This fixture replaces only the production provenance validator. It cannot be
    # selected through production arguments and never accepts live evidence.
    assert expected["evidence_class"] == evidence["evidence_class"] == "simulated"
    assert evidence["observations"] == fixture(evidence["scope"])["evidence"]["observations"]


def validate(value, **options):
    return H.validate(value, root=ROOT, target="kanbien-core-platform", scope=value["scope"], source=SOURCE,
        primary_image=PRIMARY, observed_at=TIME, evidence_class="simulated", **options)


class SchedulingProofTests(unittest.TestCase):
    def test_production_owner_rejects_fabricated_proof(self):
        value = fixture("entity-smoke")
        with self.assertRaisesRegex(H.ProofFailure, "^scheduling-proof-provenance-not-confirmed$"):
            validate(value)

    def test_missing_production_reader_blocks_proof(self):
        value = fixture("entity-smoke")
        with patch.object(H, "module", return_value=SimpleNamespace()) as selected:
            with self.assertRaisesRegex(H.ProofFailure, "^scheduling-proof-owner-unavailable$"):
                H.owner_validate(ROOT, value["evidence"], {}, historical=False)
        selected.assert_called_once_with(H.IMPLEMENTATION_ROOT / H.OWNER, "scheduling_acceptance_evidence_owner")

    def test_missing_tampered_source_image_cases_and_freshness(self):
        mutations = [
            (lambda value: value["components"].pop("worker"), "components-incomplete"),
            (lambda value: value["components"]["worker"].update(source_revision="d" * 40), "component-source-mismatch"),
            (lambda value: value["components"]["worker"].update(program_id=value["components"]["dispatch"]["program_id"]), "component-custody-invalid"),
            (lambda value: value["evidence"]["components"]["worker"].update(image_digest="sha256:" + "f" * 64), "runtime-component-mismatch"),
            (lambda value: value["evidence"]["observations"].pop("failure-recovery"), "cases-incomplete"),
            (lambda value: value["evidence"]["observations"].update(cancellation=True), "cases-incomplete"),
            (lambda value: value["evidence"].update(evidence_class="live"), "evidence-class-mismatch"),
            (lambda value: value["evidence"].update(observed_at="2026-11-27T04:44:59Z"), "observation-stale"),
            (lambda value: value.update(scope="core-server-persistence"), "component-custody-invalid"),
        ]
        with patch.object(H, "owner_validate", side_effect=controlled_owner):
            for mutate, code in mutations:
                with self.subTest(code=code):
                    value = fixture("entity-smoke"); mutate(value)
                    with self.assertRaisesRegex(H.ProofFailure, "scheduling-proof-" + code): validate(value)

    def test_captured_identity_not_restamped_by_repeated_collection(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(H, "owner_validate", side_effect=controlled_owner):
            base, value = Path(directory), fixture("entity-smoke")
            paths = {}
            for role, receipt in value["components"].items():
                paths[role] = base / (role + ".json"); paths[role].write_bytes(H.canonical(receipt))
            proof = base / "proof.json"; proof.write_bytes(H.canonical(value["evidence"]))
            options = dict(root=ROOT, target="kanbien-core-platform", scope=value["scope"], source=SOURCE, primary_image=PRIMARY,
                proof=proof, packages=paths, evidence_class="simulated")
            self.assertEqual(H.collect(**options, observed_at=TIME), H.collect(**options, observed_at="2026-11-27T05:10:00Z"))
            with self.assertRaisesRegex(H.ProofFailure, "observation-stale"):
                H.collect(**options, observed_at="2026-11-27T05:15:01Z")

    def test_both_actual_scope_boundaries_require_profile_without_rewriting_http(self):
        core = {"release": {"source_revision": SOURCE, "image_digest": PRIMARY}, "acceptance": {"accepted_at": TIME}}
        entity = {"binding": {"source_revision": SOURCE, "image_digest": PRIMARY}}
        CORE.validate_scheduling(core); ENTITY.validate_scheduling(entity)
        with self.assertRaisesRegex(CORE.EvidenceFailure, "scheduling-proof-required"): CORE.validate_scheduling(core, required=True)
        with self.assertRaisesRegex(ENTITY.CollectionFailure, "scheduling-proof-required"): ENTITY.validate_scheduling(entity, required=True)
        with patch.object(H, "owner_validate", side_effect=controlled_owner), patch.object(CORE, "scheduling_module", return_value=H), patch.object(CORE, "EVIDENCE_CLASS", "simulated"), patch.object(ENTITY, "SCHEDULING", H):
            core["scheduling_qualification"] = fixture("core-server-persistence")
            entity["scheduling_qualification"] = fixture("entity-smoke")
            core["qualification_profile"] = entity["qualification_profile"] = H.PROFILE
            CORE.validate_scheduling(core, required=True)
            ENTITY.validate_scheduling(entity, required=True, evidence_class="simulated")
            self.assertEqual(core["release"]["image_digest"], PRIMARY)
            entity["scheduling_qualification"]["source_revision"] = "f" * 40
            with self.assertRaisesRegex(ENTITY.CollectionFailure, "identity-mismatch"):
                ENTITY.validate_scheduling(entity, evidence_class="simulated")

    def test_actual_core_candidate_hashes_all_components_and_rejects_retained_tamper(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(H, "owner_validate", side_effect=controlled_owner), patch.object(CORE, "EVIDENCE_ROOT", Path(directory)), patch.object(CORE, "EVIDENCE_CLASS", "simulated"):
            value = validate(fixture("core-server-persistence"))
            retained = H.retain(value, Path(directory), S)
            _, candidate = CORE.candidate_record({"source_revision": SOURCE, "image_digest": PRIMARY}, {}, TIME, retained)
            self.assertEqual(candidate["release"]["image_digest"], PRIMARY)
            self.assertEqual(set(candidate["proof_set"]), set(H.material(value)))
            reader = CORE.succession_module()
            reader.candidate_identity(candidate, Path(directory))
            retained["scheduling-worker-package"].write_text('{"tampered":true}')
            with self.assertRaisesRegex(reader.SuccessionFailure, "proof-receipt-mismatch"):
                reader.candidate_identity(candidate, Path(directory))

    def test_actual_entity_candidate_material_preserves_primary_and_three_extra_hashes(self):
        packet = {"binding": {"source_revision": SOURCE, "image_digest": PRIMARY,
            "configuration_contract_sha256": "sha256:" + "c" * 64, "permission_contract_sha256": "sha256:" + "d" * 64},
            "runtime": {"observed_at": TIME}, "scheduling_qualification": fixture("entity-smoke")}
        material = ENTITY.candidate_material(packet)
        candidate = material["document"]
        self.assertEqual(candidate["release"]["image_digest"], PRIMARY)
        self.assertEqual(set(candidate["proof_set"]), {"entity-smoke-complete-proof", *H.material(packet["scheduling_qualification"])})
        self.assertEqual(len(material["components"]), 3)
        self.assertNotEqual(candidate["release"]["id"], ENTITY.candidate_material({key: value for key, value in packet.items() if key != "scheduling_qualification"})["document"]["release"]["id"])

    def test_input_profile_is_explicit_closed_and_preserves_legacy_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            route_path = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/acceptance-route-contract.yml"
            route = yaml.safe_load(route_path.read_text())
            receipt = base / "receipt.json"; receipt.write_text("{}")
            original = {"schema": "deploy/acceptance-inputs/v1", "target": route["target"], "scope": route["scope"],
                "values": {"candidate_receipt": str(receipt), "proof_label": "entity-smoke-" + "a" * 24, "expected_digest": "b" * 64, "expected_predecessor": "none"}}
            path = base / "inputs.json"; path.write_text(json.dumps(original))
            self.assertEqual(set(ROUTE.input_values(path, route)), set(original["values"]))
            required = ["--inputs", str(path), "--write-candidate", "--require-qualification-profile", H.PROFILE]
            with patch.object(CORE, "aws", side_effect=AssertionError("profile guard precedes provider reads")), \
                 patch.object(ENTITY, "gather", side_effect=AssertionError("profile guard precedes provider reads")):
                with self.assertRaisesRegex(CORE.EvidenceFailure, "qualification-profile-required"):
                    CORE.parse_arguments(required)
                with self.assertRaisesRegex(ENTITY.CollectionFailure, "qualification-profile-required"):
                    ENTITY.resolve_inputs(ENTITY.parse(required))
                for selected_parser, failure_type in ((CORE.parse_arguments, CORE.EvidenceFailure), (ENTITY.parse, ENTITY.CollectionFailure)):
                    with self.assertRaisesRegex(failure_type, "qualification-profile-required"):
                        selected_parser(["--write-candidate", "--require-qualification-profile", H.PROFILE])
            selected = {**original, "qualification_profile": H.PROFILE}
            path.write_text(json.dumps(selected))
            with self.assertRaisesRegex(ValueError, "inputs-set-invalid"): ROUTE.input_values(path, route)
            selected["values"] = {**original["values"], "scheduling_receipt": str(receipt), "scheduling_packages": {role: str(receipt) for role in H.ROLES}}
            path.write_text(json.dumps(selected))
            self.assertEqual(set(ROUTE.input_values(path, route)), set(selected["values"]))
            with self.assertRaisesRegex(ENTITY.CollectionFailure, "acceptance-scheduling-successor-required"):
                ENTITY.resolve_inputs(ENTITY.parse(["--inputs", str(path), "--write-candidate"]))
            selected["values"]["expected_predecessor"] = "release-" + "c" * 24
            path.write_text(json.dumps(selected))
            args = ENTITY.resolve_inputs(ENTITY.parse(required))
            self.assertEqual(args.qualification_profile, H.PROFILE)
            self.assertEqual(set(args.scheduling_packages), H.ROLES)
            selected["qualification_profile"] = "caller-invented"; path.write_text(json.dumps(selected))
            with self.assertRaisesRegex(ValueError, "qualification-profile-invalid"): ROUTE.input_values(path, route)

    def test_reader_does_not_upgrade_old_http_record_and_safe_failure_excludes_canary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.yml"
            path.write_text(yaml.safe_dump({"schema": "deploy/persistence-accepted-release/v1", "status": "accepted"}))
            self.assertEqual(CORE_READER.validate(path, qualification_profile=H.PROFILE), ["scheduling-proof-required"])
            bad = Path(directory) / "private-canary.json"; bad.write_text('{"token":"secret-canary",')
            with self.assertRaises(H.ProofFailure) as caught: H.read(bad)
            self.assertEqual(caught.exception.code, "scheduling-proof-document-unavailable")
            self.assertNotIn("canary", str(caught.exception))

    def test_actual_core_reader_never_imports_code_from_receipt_data_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base, value = Path(directory), fixture("core-server-persistence")
            scope = "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/"
            for relative in (scope + "declaration-contract.yml", scope + "acceptance-route-contract.yml", "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml"):
                destination = base / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            canary = base / "replacement-code-executed"
            replacement = "from pathlib import Path\nPath(" + repr(str(canary)) + ").write_text('executed')\n"
            for relative, implementation in (
                ("scripts/04.deploy/lifecycle/40-package/package-custody-receipt/validate.py", "class Failure(Exception): pass\ndef validate(*arguments): return None\n"),
                (H.OWNER, "def validate_acceptance_evidence(evidence, **options): return evidence\n"),
            ):
                destination = base / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(replacement + implementation)
            record = base / "record.yml"
            record.write_text(yaml.safe_dump({"schema": "deploy/persistence-accepted-release/v1", "status": "rehearsed", "evidence_class": "simulated",
                "target": value["target"], "scope": value["scope"], "release": {"source_revision": SOURCE, "image_digest": PRIMARY},
                "qualification_profile": H.PROFILE, "scheduling_qualification": value}))
            self.assertEqual(CORE_READER.validate(record, root=base, evidence_class="simulated", qualification_profile=H.PROFILE), ["scheduling-proof-provenance-not-confirmed"])
            self.assertFalse(canary.exists())
            with patch.object(CORE_READER.importlib.util, "spec_from_file_location", side_effect=AssertionError("unexpected-code-import")):
                self.assertEqual(CORE_READER.validate(record, root=ROOT, evidence_class="simulated", qualification_profile=H.PROFILE), ["accepted-release-simulation-root-invalid"])
            self.assertFalse(canary.exists())

    def test_route_profile_rejects_malformed_duplicate_subjects_and_primary_alias(self):
        scope = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml"
        route_path = scope.parent / "acceptance-route-contract.yml"
        original_reader = ROUTE.document
        original = original_reader(route_path)
        cases = [
            (lambda value: value["qualification_profiles"][H.PROFILE]["inputs"].update(scheduling_receipt="wrong-type"), "acceptance-route-qualification-profile-invalid"),
            (lambda value: value["qualification_profiles"][H.PROFILE]["requirements"].update(worker="scheduling-dispatch-runtime-provider-proof"), "acceptance-route-qualification-subject-invalid"),
            (lambda value: value.update(program_id="kanbien-entity-smoke-scheduling-dispatch"), "acceptance-route-subject-mismatch"),
        ]
        for mutate, code in cases:
            with self.subTest(code=code):
                changed = copy.deepcopy(original); mutate(changed)
                with patch.object(ROUTE, "document", side_effect=lambda path: changed if path == route_path else original_reader(path)):
                    result = ROUTE.inspect(scope, ROOT, probe_commands=False)
                self.assertIn(code, [finding["code"] for finding in result["findings"]])

    def test_database_proof_selection_is_explicit_and_retained(self):
        route = yaml.safe_load((ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/acceptance-route-contract.yml").read_text())
        original = copy.deepcopy(route)
        self.assertIs(H.selected_route(route), route)
        selected = H.selected_route(route, H.PROFILE)
        self.assertEqual(route, original)
        self.assertEqual(selected["proofs"]["migration-applied-state"]["operation"], "observe-scheduling-state")
        self.assertEqual(selected["proofs"]["migration-applied-state"]["result_code"], "PERSISTENCE_SCHEDULING_STATE_CONFIRMED")
        self.assertEqual(selected["proofs"]["effective-privilege"], route["proofs"]["effective-privilege"])
        self.assertEqual(H.database_proof()["operation"], "observe-migration-state")
        self.assertEqual(ENTITY.A.tasks()["migration-state"][0], "initial-recovery")
        self.assertEqual(ENTITY.A.tasks(H.PROFILE)["migration-state"], ("scheduling-qualification", "administration", ("observe-scheduling-state",)))
        for record in ({"qualification_profile": H.PROFILE}, {"scheduling_qualification": fixture("entity-smoke")},
                       {"qualification_profile": H.PROFILE, "scheduling_qualification": {"profile": "invented"}}):
            with self.subTest(record=record), self.assertRaisesRegex(H.ProofFailure, "profile-proof-mismatch"):
                H.record_profile(record)
        self.assertIsNone(H.record_profile({}))

    def test_selected_collectors_require_the_profile_through_existing_wrappers(self):
        for scope in ("core-server-persistence", "entity-smoke"):
            with self.subTest(scope=scope):
                route = yaml.safe_load((ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes" / scope / "00-declaration/acceptance-route-contract.yml").read_text())
                original = copy.deepcopy(route)
                selected = H.selected_route(route, H.PROFILE)
                command = route["collector"]
                expected = [*route["commands"][command]["argv"], "--require-qualification-profile", H.PROFILE]
                self.assertEqual(selected["commands"][command]["argv"], expected)
                self.assertEqual(route, original)
                self.assertIs(H.selected_route(route), route)
                arguments = [value.replace("{acceptance_inputs}", "/missing/not-read-by-argument-validation.json") for value in expected]
                result = subprocess.run([*arguments, "--validate-arguments"], cwd=ROOT, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                for flag in (["--require-qualification-profile", H.PROFILE], ["--require-qualification-profile=other"]):
                    changed = copy.deepcopy(route)
                    changed["commands"][command]["argv"].extend(flag)
                    with self.assertRaisesRegex(H.ProofFailure, "profile-invalid"):
                        H.selected_route(changed, H.PROFILE)

    def test_selected_database_proof_rejects_malformed_references_before_probing(self):
        scope = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml"
        route_path = scope.parent / "acceptance-route-contract.yml"
        route = yaml.safe_load(route_path.read_text())
        command = route["proofs"]["migration-applied-state"]["command"]
        mutations = [
            lambda value: value.update(proofs=None),
            lambda value: value.update(proofs=[]),
            lambda value: value["proofs"].update({"migration-applied-state": None}),
            lambda value: value["proofs"].update({"migration-applied-state": []}),
            lambda value: value["proofs"]["migration-applied-state"].pop("command"),
            lambda value: value["proofs"]["migration-applied-state"].update(command=[]),
            lambda value: value["proofs"]["migration-applied-state"].update(command="unknown"),
            lambda value: value["commands"].update({command: None}),
            lambda value: value["commands"].update({command: []}),
            lambda value: value["commands"][command].pop("argv"),
            lambda value: value["commands"][command].update(argv="--operation observe-migration-state"),
            lambda value: value["commands"][command].update(argv=[]),
            lambda value: value["commands"][command].update(argv=["bash", None]),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                changed = copy.deepcopy(route); mutate(changed)
                self.assertIs(H.selected_route(changed), changed)
                with self.assertRaisesRegex(H.ProofFailure, "^scheduling-proof-profile-invalid$"):
                    H.selected_route(changed, H.PROFILE)
        changed = copy.deepcopy(route)
        changed["proofs"]["migration-applied-state"]["command"] = []
        read = ROUTE.document
        with patch.object(ROUTE, "document", side_effect=lambda path: changed if path == route_path else read(path)), \
             patch.object(ROUTE.subprocess, "run", side_effect=AssertionError("malformed proof executed a command")) as probe:
            report = ROUTE.inspect(scope, ROOT)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("acceptance-route-proof-binding-invalid", codes)
        self.assertNotIn("acceptance-route-contract-malformed", codes)
        probe.assert_not_called()

    def test_complete_database_observation_is_not_a_prefix_or_empty_work_claim(self):
        state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
                 "work_inventory": {"waiting_schedules": 3, "pending_outbox": 1, "active_processing": 2}}
        self.assertEqual(H.complete_database_state(state, manifest_sha256="a" * 64), state)
        self.assertEqual(ENTITY.A.database_result({"code": "PERSISTENCE_SCHEDULING_STATE_CONFIRMED", "database_state": state}, H.PROFILE,
                         manifest_sha256="a" * 64)["migration_count"], 7)
        for changed, reason in (({**state, "migration_count": 4}, "database-state-incomplete"),
                                ({**state, "manifest_sha256": "b" * 64}, "database-manifest-mismatch"),
                                ({"schema": "kanbien/scheduling-migration-prefix/v1"}, "database-state-invalid")):
            with self.subTest(reason=reason), self.assertRaisesRegex(H.ProofFailure, reason):
                H.complete_database_state(changed, manifest_sha256="a" * 64)
        with self.assertRaisesRegex(ENTITY.A.EvidenceFailure, "acceptance-migration-state-not-applied"):
            ENTITY.A.database_result({"code": "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"}, H.PROFILE)

    def test_scheduling_first_qualification_rejects_before_collection_or_provider(self):
        args = SimpleNamespace(qualification_profile=H.PROFILE, expected_predecessor=None)
        with patch.object(ENTITY, "current_predecessor", side_effect=AssertionError("must reject before custody lookup")):
            for call in (lambda: ENTITY.collection_cache(args), lambda: ENTITY.gather(args, object())):
                with self.assertRaisesRegex(ENTITY.CollectionFailure, "acceptance-scheduling-successor-required"): call()

    def test_actual_core_receipt_parser_selects_full_state_without_requery(self):
        receipts = CORE.receipt_module(); receipts.EVIDENCE_CLASS = "simulated"
        state = {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
                 "work_inventory": {"waiting_schedules": 0, "pending_outbox": 0, "active_processing": 0}}
        task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + "1" * 32,
            "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-administration:1",
            "startedAt": "2026-11-27T05:00:00Z", "stoppedAt": "2026-11-27T05:00:01Z", "lastStatus": "STOPPED", "containers": [{"exitCode": 0}]}
        required = {"migration-applied-state": ("administration", "kanbien-core-platform-persistence-administration", PRIMARY,
            "PERSISTENCE_SCHEDULING_STATE_CONFIRMED", "persistence-administration")}
        with tempfile.TemporaryDirectory() as temporary, patch.object(CORE, "EVIDENCE_CLASS", "simulated"), \
             patch.object(CORE, "aws", side_effect=AssertionError("historical receipt must not query AWS")):
            path = Path(temporary) / "proof.json"
            def retained(selected):
                value = receipts.make(proof_type="administration", operation="observe-scheduling-state", task=task,
                    image_digest=PRIMARY, result_code="PERSISTENCE_SCHEDULING_STATE_CONFIRMED",
                    context={"completion_deadline_seconds": 300, "completion_duration_seconds": 1, "database_state": selected},
                    controller="run-administration", collected_at="2026-11-27T05:00:02Z")
                path.write_text(json.dumps(value))
            retained(state)
            arguments = (["migration-applied-state=" + str(path)], required, {"persistence-administration": 300}, Path(temporary))
            self.assertEqual(set(CORE.parse_proof_receipts(*arguments, qualification_profile=H.PROFILE)), set(required))
            with self.assertRaisesRegex(CORE.EvidenceFailure, "proof-receipt-mismatch"):
                CORE.parse_proof_receipts(*arguments)
            retained({**state, "migration_count": 4})
            with self.assertRaisesRegex(CORE.EvidenceFailure, "database-state-incomplete"):
                CORE.parse_proof_receipts(*arguments, qualification_profile=H.PROFILE)

    def test_core_original_prefix_apply_and_full_state_lineage(self):
        receipts = CORE.receipt_module(); receipts.EVIDENCE_CLASS = "simulated"
        binding = {"source_revision": SOURCE, "image_digest": PRIMARY,
                   "dependency_incarnation_sha256": receipts.digest({"resource_id": "db-FIXED", "database": "kanbienpersistence", "schema": "platform"})}
        def proof(kind, operation, index, code, context):
            task = {"taskArn": "arn:aws:ecs:eu-west-1:337159794548:task/kanbien-core-platform/" + format(index, "032x"),
                "taskDefinitionArn": "arn:aws:ecs:eu-west-1:337159794548:task-definition/kanbien-core-platform-persistence-" + kind + ":1",
                "startedAt": "2026-11-27T05:00:0" + str(index) + "Z", "stoppedAt": "2026-11-27T05:00:0" + str(index) + "Z",
                "lastStatus": "STOPPED", "containers": [{"exitCode": 0}]}
            return receipts.make(proof_type=kind, operation=operation, task=task, image_digest=PRIMARY, result_code=code,
                context={"completion_deadline_seconds": 300, "completion_duration_seconds": 0, "scheduling_binding": binding, **context},
                controller="run-" + kind, collected_at=task["stoppedAt"])
        def reseal(value): value["integrity"]["payload_sha256"] = receipts.digest({key: item for key, item in value.items() if key != "integrity"})
        with tempfile.TemporaryDirectory() as temporary, patch.object(CORE, "EVIDENCE_CLASS", "simulated"), \
             patch.object(CORE, "aws", side_effect=AssertionError("historical lineage must not query AWS")):
            path = Path(temporary) / "full.json"
            for complete in (False, True):
                prefix_state = {"schema": "kanbien/scheduling-migration-prefix/v1", "manifest_sha256": "a" * 64,
                    "manifest_migration_count": 7, "minimum_applied_migrations": 2, "applied_migrations": 7 if complete else 2,
                    "applied_prefix_sha256": ("a" if complete else "b") * 64, "state": "complete" if complete else "partial"}
                prefix = proof("administration", "observe-scheduling-prefix", 1, "PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED", {"migration_prefix": prefix_state})
                archives = {"prefix": prefix}
                if not complete:
                    archives["apply"] = proof("migration", "apply", 2, "PERSISTENCE_MIGRATION_APPLIED", {"migration_profile": "scheduling",
                        "prefix_receipt_sha256": "sha256:" + hashlib.sha256(receipts.document_bytes(prefix)).hexdigest()})
                full = proof("administration", "observe-scheduling-state", 3, "PERSISTENCE_SCHEDULING_STATE_CONFIRMED",
                    {"database_state": {"schema": "kanbien/scheduling-database-state/v1", "manifest_sha256": "a" * 64, "migration_count": 7,
                        "work_inventory": {"waiting_schedules": 1, "pending_outbox": 1, "active_processing": 1}}})
                path.write_bytes(receipts.document_bytes(full))
                record = {"qualification_profile": H.PROFILE, "release": {"source_revision": SOURCE, "image_digest": PRIMARY},
                    "acceptance": {"accepted_at": "2026-11-27T05:00:04Z"}, "scheduling_migrations": archives,
                    "provider_observation": {"proofs": {"migration-applied-state": {"receipt": str(path)}}}}
                self.assertEqual(CORE.validate_scheduling_migrations(record, database={"source_resource_id": "db-FIXED"}), binding)
                mutations = [lambda value: value["scheduling_migrations"].clear(),
                    lambda value: value["release"].update(source_revision="f" * 40)]
                if not complete: mutations.append(lambda value: value["scheduling_migrations"].pop("apply"))
                for mutate in mutations:
                    changed = copy.deepcopy(record); mutate(changed)
                    with self.assertRaisesRegex(CORE.EvidenceFailure, "migration-lineage-invalid"):
                        CORE.validate_scheduling_migrations(changed)
                with self.assertRaisesRegex(CORE.EvidenceFailure, "migration-lineage-invalid"):
                    CORE.validate_scheduling_migrations(record, database={"source_resource_id": "db-CHANGED"})
                for field in ("manifest", "binding", "time", "definition"):
                    changed = copy.deepcopy(full)
                    if field == "manifest": changed["context"]["database_state"]["manifest_sha256"] = "f" * 64
                    elif field == "binding": changed["context"]["scheduling_binding"]["dependency_incarnation_sha256"] = "sha256:" + "f" * 64
                    elif field == "definition": changed["task"]["definition"] = changed["task"]["definition"].replace("persistence-administration", "foreign-administration")
                    else: changed["task"]["started_at"] = changed["task"]["stopped_at"] = "2026-11-27T05:00:00Z"
                    reseal(changed); path.write_bytes(receipts.document_bytes(changed))
                    with self.assertRaisesRegex(CORE.EvidenceFailure, "migration-lineage-invalid"):
                        CORE.validate_scheduling_migrations(record)


class ArchiveCodecTests(unittest.TestCase):
    """Controlled data only: the codec never establishes native or AWS proof."""
    def fixture(self, number=0):
        prerequisite = {"schema": "deploy/proof-prerequisite-reference/v1", "packet_sha256": "sha256:" + "a" * 64}
        graph = {"schema": "controlled-test-graph/v1", "definition": "x" * 4000}
        phase = {"graph": graph, "prerequisites": {"original": prerequisite}, "receipt": {"result": "accepted"}}
        return {"task": {"preflight": phase, "operation": {**phase, "number": number}},
            "preparation": {"state": phase, "grant": phase, "prove": phase}}

    def test_shared_parts_restore_exact_original_and_preserve_native_references(self):
        materials, consumed, originals = {}, set(), [self.fixture(index) for index in range(16)]
        roots = [H.pack_native_archive(value, materials) for value in originals]
        self.assertEqual(len(set(roots)), 16)
        self.assertLess(len(H.canonical(materials)), sum(len(H.canonical(value)) for value in originals) // 4)
        policy = H.module(DIRECTORY / "proof-policy.py", "archive_codec_existing_prerequisite_owner")
        for reference, original in zip(roots, originals):
            restored, used = H.unpack_native_archive(reference, materials)
            self.assertEqual(restored, original)
            self.assertEqual(H.canonical(restored), H.canonical(original))
            policy.validate_prerequisite_references(restored, {"sha256:" + "a" * 64})
            consumed.update(used)
        self.assertEqual(consumed, set(materials))
        self.assertTrue(any(value["kind"] == "archive-part" for value in materials.values()))
        # Neither source input nor checked stored parts are returned by alias.
        restored["task"]["preflight"]["receipt"]["result"] = "changed"
        self.assertEqual(H.unpack_native_archive(roots[-1], materials)[0], originals[-1])

    def test_closed_kinds_and_preparation_wrapper_share_parts_not_identity(self):
        materials, original = {}, self.fixture()
        roots = {kind: H.pack_archive(original, materials, kind=kind) for kind in H.ARCHIVE_KINDS}
        self.assertEqual(len(set(roots.values())), len(H.ARCHIVE_KINDS))
        for kind, reference in roots.items():
            self.assertEqual(H.unpack_archive(reference, materials, kind=kind)[0], original)
        self.assertEqual(H.pack_native_archive(original, materials, preparation=True), roots["preparation"])
        self.assertEqual(H.unpack_native_archive(roots["preparation"], materials, preparation=True)[0], original)
        with self.assertRaisesRegex(H.ProofFailure, "archive-kind-mismatch"):
            H.unpack_native_archive(roots["preparation"], materials)
        for kind in (None, [], "arbitrary"):
            with self.assertRaisesRegex(H.ProofFailure, "archive-kind-invalid"):
                H.pack_archive(original, materials, kind=kind)

    def test_codec_reference_collision_is_rejected_without_changing_table(self):
        materials = {}
        H.pack_native_archive(self.fixture(), materials)
        before = copy.deepcopy(materials)
        for reference in ({"schema": H.ARCHIVE_REFERENCE, "reference": "sha256:" + "f" * 64},
                {"schema": H.ARCHIVE_REFERENCE, "unexpected": "PRIVATE-CANARY"}):
            with self.assertRaisesRegex(H.ProofFailure, "archive-reference-collision") as failure:
                H.pack_native_archive({"nested": reference}, materials)
            self.assertNotIn("PRIVATE-CANARY", str(failure.exception))
            self.assertEqual(materials, before)

    def test_missing_tampered_wrong_kind_and_original_hash_are_rejected(self):
        materials = {}
        root = H.pack_native_archive(self.fixture(), materials)
        child = next(key for key, value in materials.items() if value["kind"] == "archive-part")
        missing = copy.deepcopy(materials); missing.pop(child)
        with self.assertRaisesRegex(H.ProofFailure, "archive-reference-missing"):
            H.unpack_native_archive(root, missing)
        tampered = copy.deepcopy(materials); tampered[child]["packet"]["extra"] = "PRIVATE-CANARY"
        with self.assertRaisesRegex(H.ProofFailure, "archive-material-mismatch") as failure:
            H.unpack_native_archive(root, tampered)
        self.assertNotIn("PRIVATE-CANARY", str(failure.exception))
        for mutation, code in ((lambda packet: packet.update(original_sha256="sha256:" + "0" * 64), "archive-original-mismatch"),
                (lambda packet: packet.update(extra=True), "archive-envelope-invalid"),
                (lambda packet: packet["value"].update(bad={"schema": H.ARCHIVE_REFERENCE, "reference": child, "extra": 1}), "archive-reference-invalid")):
            changed = copy.deepcopy(materials); entry = changed.pop(root); mutation(entry["packet"])
            selected = H.digest(entry); changed[selected] = entry
            with self.assertRaisesRegex(H.ProofFailure, code): H.unpack_native_archive(selected, changed)
        wrong = copy.deepcopy(materials); entry = wrong.pop(child); entry["kind"] = "phase"
        selected = H.digest(entry); wrong[selected] = entry
        envelope = wrong.pop(root)
        # Reference the wrong-kind root directly; no forged hash is necessary.
        envelope["packet"]["value"] = {"part": {"schema": H.ARCHIVE_REFERENCE, "reference": selected}}
        selected_root = H.digest(envelope); wrong[selected_root] = envelope
        with self.assertRaisesRegex(H.ProofFailure, "archive-kind-mismatch"):
            H.unpack_native_archive(selected_root, wrong)

    def test_cycles_depth_value_and_size_are_bounded_before_retention(self):
        cyclic = {}; cyclic["self"] = cyclic
        deep = {}
        for _ in range(65): deep = {"nested": deep}
        for value, code in ((cyclic, "archive-cycle"), (deep, "archive-complexity-limit"),
                ({"data": "x" * H.LIMIT}, "archive-expansion-limit"),
                ({"tuple": (1, 2)}, "archive-value-invalid"), ({1: "invalid"}, "archive-value-invalid")):
            materials = {}
            with self.assertRaisesRegex(H.ProofFailure, code): H.pack_native_archive(value, materials)
            self.assertEqual(materials, {})

    def test_compact_exponential_reference_expansion_is_bounded(self):
        materials = {}
        def retain(packet, kind="archive-part"):
            value = {"kind": kind, "packet": packet}; reference = H.digest(value)
            materials[reference] = value
            return reference
        reference = retain({"value": "x" * 2048})
        for _ in range(12):
            part = {"schema": H.ARCHIVE_REFERENCE, "reference": reference}
            reference = retain({"left": part, "right": part})
        root = retain({"schema": H.ARCHIVE_SCHEMA, "original_sha256": "sha256:" + "0" * 64,
            "value": {"part": {"schema": H.ARCHIVE_REFERENCE, "reference": reference}}}, "native")
        self.assertLess(len(H.canonical(materials)), 16384)
        with self.assertRaisesRegex(H.ProofFailure, "archive-expansion-limit"):
            H.unpack_native_archive(root, materials)

    def test_material_limits_and_unrelated_parts_are_visible_to_collector(self):
        materials = {}
        root = H.pack_native_archive(self.fixture(), materials)
        other = H.pack_archive({"unrelated": "proof"}, materials, kind="alert")
        _, consumed = H.unpack_native_archive(root, materials)
        self.assertNotIn(other, consumed)
        self.assertNotEqual(consumed, set(materials))
        before = copy.deepcopy(materials)
        with patch.object(H, "ARCHIVE_PART_LIMIT", len(materials)):
            with self.assertRaisesRegex(H.ProofFailure, "archive-material-limit"):
                H.pack_native_archive({"new": "part"}, materials)
        self.assertEqual(materials, before)
        with self.assertRaisesRegex(H.ProofFailure, "archive-material-limit"):
            H.pack_native_archive({}, {"large": {"kind": "alert", "packet": "x" * H.LIMIT}})


if __name__ == "__main__": unittest.main()
