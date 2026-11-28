#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.managed-handler-image-qualification
#   version: 2
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove fail-closed managed image qualification, configuration custody, cleanup and exact publication bindings without Docker or cloud calls.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-scheduling
#     path: .github/workflows/publish-kanbien-core-platform-scheduling.yml
import contextlib
import copy
import importlib.util
import io
import json
import subprocess
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[5]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
owner = load("managed_image_qualification", Path(__file__).with_name("qualification.py"))
publication = load("managed_publication", Path(__file__).with_name("publication.py"))
projection = load("managed_configuration", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py")
source_binding = load("package_source_binding", ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py")
PROGRAMS = ["kanbien-" + scope + "-scheduling-" + purpose for scope in ("core-server-persistence", "entity-smoke") for purpose in ("dispatch", "worker")]

def inspected(program):
    return {"Id": "sha256:" + "a" * 64, "Architecture": "amd64", "Os": "linux", "Size": 123456,
        "Config": {"Entrypoint": ["/lambda-entrypoint.sh"], "Cmd": ["handler.handler"], "User": "10001:10001", "WorkingDir": "/var/task",
            "Labels": {"org.kanbien.program": program, "org.opencontainers.image.revision": "b" * 40}, "Env": ["NODE_ENV=production"]}}

class DockerFixture:
    def __init__(self, program, fail=False, lost=False): self.program = program; self.calls = []; self.mode = None; self.fail = fail; self.lost = lost
    def __call__(self, argv, timeout=30):
        self.calls.append(argv)
        if argv[1:3] == ["image", "inspect"]: return json.dumps([inspected(self.program)])
        if argv[1] == "create":
            self.mode = argv[-1]
            if self.lost: raise owner.QualificationFailure("managed-image-command-failed")
            return "c" * 64
        if argv[1] == "start":
            if self.fail: raise owner.QualificationFailure("managed-image-command-failed")
            cases = owner.CASES["invalid" if self.mode == "invalid" else ("dispatch" if self.program.endswith("dispatch") else "worker")]
            return json.dumps({"schema": "deploy/managed-runtime-invocation/v1", "verdict": "passed", "program_id": self.program,
                "mode": self.mode, "cases": cases, "responses": len(cases), "runtime_interface": "official-aws-lambda-client"})
        if argv[1] == "ps": return "c" * 64
        if argv[1] == "rm": return "c" * 64
        raise AssertionError("unexpected command")

class QualificationTests(unittest.TestCase):
    def test_real_git_distinguishes_new_receipts_from_runtime_or_tracked_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                    "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args], check=True, capture_output=True, text=True)
            git("init", "--quiet")
            code = root / "platform/runtime.ts"; code.parent.mkdir(); code.write_text("export {};\n")
            git("add", "platform/runtime.ts"); git("commit", "--quiet", "-m", "fixture")
            self.assertTrue(source_binding.runtime_sources_clean(root))
            receipt = root / "infra/04.deploy/03.product/targets/example/20-scopes/application/30-release-evidence/proof-receipts/administration-observe-example.json"
            receipt.parent.mkdir(parents=True); receipt.write_text("{}")
            # This is classification only: empty JSON is NOT authenticated proof.
            self.assertTrue(source_binding.runtime_sources_clean(root))
            for relative in ("platform/new.ts", "infra/other.json", "infra/04.deploy/03.product/targets/example/20-scopes/application/30-release-evidence/accepted.json"):
                candidate = root / relative; candidate.parent.mkdir(parents=True, exist_ok=True); candidate.write_text("{}")
                self.assertFalse(source_binding.runtime_sources_clean(root)); candidate.unlink()
            code.write_text("export const changed = true;\n")
            self.assertFalse(source_binding.runtime_sources_clean(root)); code.write_text("export {};\n")
            link = receipt.with_name("administration-linked.json"); link.symlink_to(code)
            self.assertFalse(source_binding.runtime_sources_clean(root)); link.unlink()
            git("add", str(receipt.relative_to(root)))
            self.assertFalse(source_binding.runtime_sources_clean(root), "staged evidence is a tracked change")
            git("commit", "--quiet", "-m", "retained proof fixture")
            self.assertTrue(source_binding.runtime_sources_clean(root)); receipt.write_text('{"changed":true}')
            self.assertFalse(source_binding.runtime_sources_clean(root), "existing retained evidence cannot be edited")

    def test_source_observation_failure_and_malformed_records_are_not_clean(self):
        for output in ("?? missing-terminator", "\0", "?? ../outside.json\0", "?? platform/private-canary.ts\0"):
            with patch.object(source_binding.subprocess, "run", return_value=SimpleNamespace(stdout=output)):
                if output and not output.endswith("\0"):
                    with self.assertRaises(ValueError): source_binding.runtime_sources_clean(ROOT)
                else:
                    self.assertFalse(source_binding.runtime_sources_clean(ROOT))
        with patch.object(source_binding.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["git"], stderr="private-canary")):
            with self.assertRaises(subprocess.CalledProcessError): source_binding.runtime_sources_clean(ROOT)

    def test_all_declared_programs_use_real_runtime_command_and_owned_cleanup(self):
        for program in PROGRAMS:
            with self.subTest(program=program):
                run = DockerFixture(program); result = owner.qualify(program + ":qualification", program, run)
                self.assertEqual(result["verdict"], "passed"); self.assertEqual(result["image_bytes"], 123456)
                creates = [argv for argv in run.calls if argv[1] == "create"]
                self.assertEqual(len(creates), 2)
                for argv in creates:
                    self.assertIn("--read-only", argv); self.assertEqual(argv[argv.index("--network") + 1], "none")
                    self.assertEqual(argv[argv.index("--entrypoint") + 1], "/var/lang/bin/node")
                    self.assertIn("sha256:" + "a" * 64, argv)
                self.assertEqual([argv for argv in run.calls if argv[1] == "rm"], [["docker", "rm", "--force", "c" * 64]] * 2)

    def test_runtime_failure_and_lost_create_response_still_clean_owned_container(self):
        for lost in (False, True):
            run = DockerFixture(PROGRAMS[0], fail=True, lost=lost)
            with self.assertRaises(owner.QualificationFailure): owner.qualify("valid:image", PROGRAMS[0], run)
            self.assertEqual(run.calls[-1], ["docker", "rm", "--force", "c" * 64])
            self.assertEqual(any(argv[1] == "ps" for argv in run.calls), lost)

    def test_inspection_rejects_each_unsafe_boundary(self):
        base = inspected(PROGRAMS[0])
        changes = [lambda v: v.update(Config=None), lambda v: v["Config"].update(Labels=[]), lambda v: v.update(Architecture="arm64"),
            lambda v: v["Config"].update(Cmd=["node", "handler.js"]), lambda v: v["Config"].update(User="root"),
            lambda v: v["Config"].update(Env=["NODE_ENV=production", 42]), lambda v: v["Config"].update(Env=["NODE_ENV=production", "AWS_SECRET_ACCESS_KEY=private"]),
            lambda v: v["Config"]["Labels"].update({"org.kanbien.program": PROGRAMS[1]}), lambda v: v["Config"]["Labels"].update({"org.opencontainers.image.revision": "main"}), lambda v: v.update(Size=0)]
        for change in changes:
            value = copy.deepcopy(base); change(value)
            with self.assertRaises(owner.QualificationFailure): owner.inspect_image("valid:image", PROGRAMS[0], lambda *_: json.dumps([value]))

    def test_failed_runtime_command_preserves_only_closed_case_context(self):
        report = {"schema": "deploy/managed-runtime-invocation/v1", "verdict": "failed", "code": "managed-runtime-invocation-failed",
                  "program_id": PROGRAMS[1], "mode": "valid", "case": "malformed-record-retained"}
        variants = [(report, True), ({**report, "case": "completion"}, True), ({**report, "case": "initialization"}, True), ({**report, "case": "private-canary"}, False),
                    ({**report, "program_id": "private-canary"}, False), ({**report, "extra": "private-canary"}, False),
                    ({**report, "mode": "private-canary"}, False), ({**report, "case": "warm-deadline"}, False)]
        for value, accepted in variants:
            with self.subTest(value=value), patch.object(owner.subprocess, "run", return_value=SimpleNamespace(returncode=23, stdout="private-canary", stderr=json.dumps(value))):
                with self.assertRaises(owner.QualificationFailure) as raised:
                    owner.command(["docker", "start", "--attach", "c" * 64])
                self.assertEqual(raised.exception.code, "managed-image-command-failed")
                self.assertEqual(raised.exception.context, {key: value[key] for key in ("program_id", "mode", "case")} if accepted else None)
        run = DockerFixture(PROGRAMS[0])
        def wrong(argv, timeout=30):
            if argv[1] == "start":
                raise owner.QualificationFailure("managed-image-command-failed", {key: report[key] for key in ("program_id", "mode", "case")})
            return run(argv, timeout)
        with self.assertRaisesRegex(owner.QualificationFailure, "^managed-image-invocation-proof-invalid$"):
            owner.qualify("valid:image", PROGRAMS[0], wrong)
        self.assertEqual(run.calls[-1], ["docker", "rm", "--force", "c" * 64])
        with tempfile.TemporaryDirectory() as directory, patch.object(owner, "qualify", side_effect=owner.QualificationFailure("managed-image-command-failed", {key: report[key] for key in ("program_id", "mode", "case")})):
            output = io.StringIO(); path = Path(directory) / "report.json"
            with patch("sys.argv", ["qualification.py", "--image", "valid:image", "--program", PROGRAMS[1], "--report", str(path)]), contextlib.redirect_stdout(output):
                self.assertEqual(owner.main(), 1)
            self.assertEqual(json.loads(output.getvalue()), {"schema": "deploy/managed-runtime-qualification/v1", "verdict": "failed",
                "code": "managed-image-command-failed", "runtime_case": "malformed-record-retained", "runtime_mode": "valid"})
            self.assertFalse(path.exists())

    def test_partial_or_wrong_runtime_proof_cannot_pass(self):
        for value in ({}, {"verdict": "passed"}, {"schema": "deploy/managed-runtime-invocation/v1", "cases": ["configuration-rejection"], "verdict": "passed"}):
            with self.assertRaises(owner.QualificationFailure): owner.validate_result(value, PROGRAMS[0], "valid")

    def test_configuration_closure_and_scope_are_bound(self):
        source = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/scheduling.yml"
        base = projection.package_projection(source, "core-server-persistence.dispatch")
        self.assertNotEqual(base, projection.package_projection(source, "entity-smoke.dispatch"))
        self.assertNotEqual(base, projection.package_projection(source, "core-server-persistence.worker"))
        with tempfile.TemporaryDirectory(prefix="managed-projection-") as temporary:
            path = Path(temporary) / "source.yml"; doc = copy.deepcopy(base["template"])
            doc["Resources"]["DispatchRole"]["Properties"]["Policies"][0]["PolicyName"] = "changed"
            path.write_text(json.dumps(doc)); self.assertNotEqual(base, projection.package_projection(path, "core-server-persistence.dispatch"))
            doc["Resources"]["DispatchFunction"]["Properties"]["Environment"]["Variables"]["PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN"] = "private"
            path.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "^package-lambda-configuration-invalid$"): projection.package_projection(path, "core-server-persistence.dispatch")
            path.write_text("Resources: {}\nResources: {}\n")
            with self.assertRaises(ValueError): projection.package_projection(path, "core-server-persistence.dispatch")

    def test_contract_dockerfile_and_runtime_fixture_are_connected(self):
        contract = owner.read_contract(); docker = (owner.CONTRACT.parent / "Dockerfile").read_text()
        self.assertIn("ARG RUNTIME_NODE_IMAGE=" + contract["runtime_base"]["reference"], docker)
        self.assertIn("RUN dnf upgrade -y --releasever=2023.12.20261112 rpm rpm-libs && dnf clean all", docker)
        self.assertIn('CMD ["handler.handler"]', docker); self.assertIn("USER 10001:10001", docker)
        fixture = owner.FIXTURE.read_text(); self.assertIn('spawn("/lambda-entrypoint.sh", ["handler.handler"]', fixture)
        self.assertNotIn("import(\"/var/task/handler", fixture)
        with tempfile.TemporaryDirectory(prefix="managed-contract-") as temporary:
            path = Path(temporary) / "contract.yml"; contract["runtime"]["user"] = "root"; path.write_text(yaml.safe_dump(contract))
            with self.assertRaises(owner.QualificationFailure): owner.read_contract(path)

    def test_publication_keeps_existing_destinations_and_roles(self):
        for program in PROGRAMS:
            selected = publication.binding(program)
            entity = "entity-smoke" in program
            self.assertEqual(selected.role, "github-kanbien-core-platform-entity-smoke-publisher" if entity else "github-kanbien-core-platform-delivery")
            self.assertEqual(selected.repository, "kanbien-core-platform/entity-smoke" if entity else "kanbien-core-platform/core-server")
            self.assertEqual(selected.local_image, program + ":qualification")
            self.assertEqual(selected.workflow, "publish-kanbien-core-platform-scheduling.yml")
        with self.assertRaises(ValueError): publication.binding("arbitrary-program")

    def test_hosted_workflow_cannot_issue_custody_before_actual_runtime_proof(self):
        path = ROOT / ".github/workflows/publish-kanbien-core-platform-scheduling.yml"
        workflow = yaml.safe_load(path.read_text()); job = workflow["jobs"]["qualify-and-publish"]
        self.assertEqual(job["environment"], "kanbien-core-platform")
        rows = job["strategy"]["matrix"]["include"]
        self.assertEqual({row["program"] for row in rows}, set(PROGRAMS))
        for row in rows:
            selected = publication.binding(row["program"])
            self.assertEqual(row["role"], selected.role); self.assertEqual(row["repository"], selected.repository)
            self.assertEqual(row["scope"] + "." + row["purpose"], selected.configuration[0][2])
        steps = job["steps"]; names = [step.get("name") for step in steps]
        self.assertLess(names.index("Enforce protected main source"), names.index("Qualify declarations and actual candidate payload"))
        self.assertLess(names.index("Qualify declarations and actual candidate payload"), names.index("Prove fixed delivery read access"))
        self.assertLess(names.index("Publish immutable image"), names.index("Write and validate safe package-custody receipt"))
        proof = next(step["run"] for step in steps if step.get("id") == "qualification")
        self.assertLess(proof.index("build-managed-handler-image/qualification.py"), proof.index("package-custody-receipt/qualification.py record"))
        self.assertIn("--configuration-input scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/lambda-runtime-configuration.py", proof)
        self.assertIn("validate-delivery-access-contract/script.py", proof)
        self.assertFalse(any(step.get("continue-on-error") for step in steps))
        custody = next(step for step in steps if step.get("name") == "Write and validate safe package-custody receipt")
        self.assertEqual(custody["env"]["QUALIFICATION_OUTCOME"], "${{ steps.qualification.outcome }}")

    def test_selected_delivery_contracts_match_real_policy_and_workflow(self):
        base = ROOT / "scripts/04.deploy/lifecycle/40-package"
        normalizer = load("managed_delivery_policy", base / "provider-adapters/aws/iam-policy-coverage/script.py")
        validator = load("managed_delivery_access", base / "validate-delivery-access-contract/script.py")
        workflow = ROOT / ".github/workflows/publish-kanbien-core-platform-scheduling.yml"
        rows = yaml.safe_load(workflow.read_text())["jobs"]["qualify-and-publish"]["strategy"]["matrix"]["include"]
        target = ROOT / "infra/04.deploy/03.product/targets/kanbien-core-platform"
        selected = {row["pipeline"]: row for row in rows}
        self.assertEqual(set(selected), {"core-scheduling-package-custody", "entity-smoke-scheduling-package-custody"})
        for name in ("core-server", "core-server-persistence"):
            selected[name + "-package-custody"] = {"role": "github-kanbien-core-platform-delivery", "policy_template": "foundation.yml",
                "policy_role": "DeliveryRole", "workflow": "publish-kanbien-core-platform-" + name + ".yml"}
        for pipeline, row in selected.items():
            with self.subTest(pipeline=pipeline), tempfile.TemporaryDirectory(prefix="managed-access-") as temporary:
                workflow = ROOT / ".github/workflows" / row.get("workflow", "publish-kanbien-core-platform-scheduling.yml")
                contract = target / "40-package-custody/github-actions" / (pipeline + ".delivery-access.yml")
                declaration = yaml.safe_load(contract.read_text())
                template = target / "30-provider-realization/aws/cloudformation" / row["policy_template"]
                source = str(template.relative_to(ROOT)) + "#" + row["policy_role"]
                self.assertEqual(declaration["actor"], row["role"])
                self.assertEqual(declaration["provider_policy_source"], source)
                coverage = Path(temporary) / "coverage.json"
                arguments = SimpleNamespace(contract=contract, template=template, role_logical_id=row["policy_role"],
                    provider_policy_source=source, output=coverage)
                with patch.object(normalizer, "parse_args", return_value=arguments):
                    self.assertEqual(normalizer.main(), 0)
                arguments = SimpleNamespace(contract=contract, workflow=workflow, provider_policy_coverage=coverage, json=True)
                def validate():
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output), patch.object(validator, "parse_args", return_value=arguments):
                        status = validator.main()
                    return status, json.loads(output.getvalue())
                status, report = validate()
                self.assertEqual((status, report["findings"]), (0, []))
                missing = json.loads(coverage.read_text())
                missing["granted_actions"].remove("ecr:DescribeRepositories")
                coverage.write_text(json.dumps(missing))
                status, report = validate()
                self.assertEqual(status, 1)
                self.assertIn({"code": "delivery-action-provider-policy-missing"}, report["findings"])

if __name__ == "__main__": unittest.main()
