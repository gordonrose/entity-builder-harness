#!/usr/bin/env python3
"""Verify restricted container execution without a daemon or network calls."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.container-engine-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise exact image identity, execution restrictions, bounded failure and owned cleanup decisions.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import container_engine as engine

IMAGE = "sha256:" + "a" * 64
BASE_ID = "sha256:" + "b" * 64
BASE = "gcr.io/distroless/nodejs22-debian12@sha256:" + "c" * 64
CID = "d" * 64
COMMIT = "e" * 40
ROWS = [{"path": ".cache/main.js", "digest": "sha256:" + "f" * 64, "bytes": 12}]


def image():
    return {"Id": IMAGE, "Os": "linux", "Architecture": "amd64",
            "Config": {"Entrypoint": [engine.NODE], "Cmd": list(engine.SERVER_COMMAND), "WorkingDir": "/app", "User": "nonroot",
                       "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "NODE_ENV=production",
                               "HOST=0.0.0.0", "PORT=3000", "PLATFORM_SOURCE_COMMIT_SHA=" + COMMIT]},
            "RootFS": {"Type": "layers", "Layers": ["sha256:" + "1" * 64]}}


class FakeDocker:
    def __init__(self):
        self.calls, self.snapshots = [], []
        self.image = image()
        self.container = None
        self.inventory = deepcopy(ROWS)
        self.health = [{"path": "/livez", "status": 200, "body_status": "live"},
                       {"path": "/readyz", "status": 200, "body_status": "ready"}]
        self.node_version = b"v22.23.3\n"
        self.exit_code = 0
        self.hook = None
        self.inspect_hook = None
        self.deleted = False
        self.build_iid = BASE_ID
        self.build_metadata = {"containerimage.digest": IMAGE, "containerimage.config.digest": BASE_ID,
                               "containerimage.descriptor": {"digest": IMAGE}}
        self.metadata_link = None

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        self.snapshots.append(kwargs)
        args = argv[3:]
        if self.hook:
            response = self.hook(args)
            if response is not None:
                return response
        data = b""
        if args[0] == "version":
            data = json.dumps({"Client": {"Version": "29.5.2"}, "Server": {"Version": "29.5.2"}}).encode()
        elif args[:2] == ["image", "inspect"]:
            value = {"Id": BASE_ID, "Os": "linux", "Architecture": "amd64", "RepoDigests": [BASE]} if args[2] == BASE else self.image
            data = json.dumps([value]).encode()
        elif args[0] == "build":
            Path(args[args.index("--iidfile") + 1]).write_text(self.build_iid + "\n")
            output = Path(args[args.index("--metadata-file") + 1])
            if self.metadata_link is not None:
                output.symlink_to(self.metadata_link)
            elif self.build_metadata is not None:
                output.write_bytes(self.build_metadata if isinstance(self.build_metadata, bytes) else json.dumps(self.build_metadata).encode())
        elif args[0] == "create":
            name = args[args.index("--name") + 1]
            label = args[args.index("--label") + 1].split("=", 1)
            config = deepcopy(self.image["Config"])
            config.update({"User": "65532:65532", "Image": IMAGE, "Labels": {label[0]: label[1]}})
            env = dict(item.split("=", 1) for item in config["Env"])
            env.update(engine.SETTINGS["environment"])
            config["Env"] = [key + "=" + value for key, value in env.items()]
            if "--entrypoint" in args:
                config["Cmd"] = ["-e", engine.INVENTORY_PROBE]
            self.container = {"Id": CID, "Name": "/" + name, "Image": IMAGE, "Config": config,
                              "HostConfig": {"NetworkMode": "none", "ReadonlyRootfs": True, "Privileged": False,
                                             "CapDrop": ["ALL"], "CapAdd": None, "SecurityOpt": ["no-new-privileges"],
                                             "Memory": 536870912, "MemorySwap": 536870912, "NanoCpus": 1000000000,
                                             "PidsLimit": 128, "Binds": None, "PortBindings": {}, "RestartPolicy": {"Name": "no"},
                                             "IpcMode": "none", "Tmpfs": {"/tmp": "rw,noexec,nosuid,nodev,size=16m"}},
                              "Mounts": [], "State": {"Running": False, "OOMKilled": False, "ExitCode": 0}}
            data = (CID + "\n").encode()
        elif args[:2] == ["container", "inspect"]:
            value = deepcopy(self.container)
            if self.inspect_hook:
                self.inspect_hook(value)
            data = json.dumps([value]).encode()
        elif args[0] == "start":
            if "--attach" in args:
                data = json.dumps(self.inventory).encode()
            else:
                self.container["State"]["Running"] = True
                data = (CID + "\n").encode()
        elif args[0] == "exec":
            data = self.node_version if args[-1] == "--version" else json.dumps(self.health).encode()
        elif args[0] == "stop":
            self.container["State"]["Running"] = False
            self.container["State"]["ExitCode"] = self.exit_code
        elif args[0] == "rm":
            self.deleted = True
            data = (CID + "\n").encode()
        elif args[:2] == ["container", "ls"]:
            data = b"" if self.deleted else CID.encode()
        elif args[0] != "pull":
            raise AssertionError("Unexpected fake Docker command: " + args[0])
        return subprocess.CompletedProcess(argv, 0, data, b"")


class ContainerEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="container-engine-test-")
        self.root = Path(self.temp.name)
        self.fake = FakeDocker()
        self.runner = engine.Engine(self.root, runner=self.fake)

    def tearDown(self):
        self.temp.cleanup()

    def fails(self, code, callback):
        with self.assertRaises(engine.EngineFailure) as caught:
            callback()
        self.assertEqual(caught.exception.code, "local-container-" + code)
        return caught.exception

    def test_engine_endpoint_and_environment_cannot_be_inherited(self):
        with patch.dict(os.environ, {"DOCKER_HOST": "ssh://remote", "DOCKER_CONTEXT": "other", "AWS_SECRET_ACCESS_KEY": "fixture-secret", "NODE_OPTIONS": "--bad"}):
            self.assertEqual(self.runner.version(), {"client": "29.5.2", "server": "29.5.2"})
        self.assertEqual(self.fake.calls[0][:3], ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"])
        actual = self.fake.snapshots[0]["env"]
        self.assertEqual(set(actual), {"PATH", "HOME", "DOCKER_CONFIG", "DOCKER_BUILDKIT", "LC_ALL"})
        self.assertEqual(Path(actual["DOCKER_CONFIG"]).joinpath("config.json").read_text(), "{}\n")
        self.assertNotIn("fixture-secret", json.dumps(actual))

    def test_scratch_requires_existing_absolute_directory(self):
        self.fails("scratch-invalid", lambda: engine.Engine("relative", runner=self.fake))
        self.fails("scratch-invalid", lambda: engine.Engine(self.root / "missing", runner=self.fake))
        (self.root / "link").symlink_to(self.root, target_is_directory=True)
        self.fails("scratch-invalid", lambda: engine.Engine(self.root / "link", runner=self.fake))

    def test_direct_arbitrary_invocations_rejected_before_runner(self):
        for args in (["system", "prune", "-a"], ["run", "--privileged", IMAGE], ["push", "remote"], ["rm", CID], ["--host", "ssh://host", "info"]):
            self.fails("engine-command-unsupported", lambda: self.runner.invoke(args))
        self.assertEqual(self.fake.calls, [])

    def test_explicit_acquisition_uses_pinned_public_reference(self):
        result = self.runner.acquire(BASE)
        self.assertEqual(result, {"image_id": BASE_ID, "repo_digests": [BASE], "os": "linux", "architecture": "amd64"})
        self.assertEqual(self.fake.calls[0][3:], ["pull", "--platform", "linux/amd64", BASE])

    def test_acquisition_rejects_mutable_or_other_registry_reference(self):
        for value in ("node:22", "gcr.io/distroless/nodejs22-debian12:nonroot", BASE + "x", BASE.replace("gcr.io", "registry.example")):
            self.fails("base-reference-invalid", lambda: self.runner.acquire(value))
        self.assertEqual(self.fake.calls, [])

    def test_base_missing_pinned_repo_digest_rejected(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, json.dumps([{"Id": BASE_ID, "Os": "linux", "Architecture": "amd64", "RepoDigests": []}]).encode(), b"")
        self.fails("base-identity-mismatch", lambda: self.runner.base_identity(BASE))

    def test_successful_inspect_returns_only_normalized_facts(self):
        self.fake.image["SecretUnexpectedTopLevel"] = "not-for-output"
        result = self.runner.inspect_image(IMAGE)
        self.assertEqual(result["image_id"], IMAGE)
        self.assertEqual(result["command"], engine.SERVER_COMMAND)
        self.assertNotIn("not-for-output", json.dumps(result))

    def test_mismatched_inspected_id_rejected(self):
        self.fake.image["Id"] = BASE_ID
        self.fails("image-identity-mismatch", lambda: self.runner.inspect_image(IMAGE))

    def test_mutable_image_name_rejected(self):
        self.fails("image-id-invalid", lambda: self.runner.inspect_image("platform-shell:local"))
        self.assertEqual(self.fake.calls, [])

    def test_image_platform_must_be_linux_amd64(self):
        self.fake.image["Architecture"] = "arm64"
        self.fails("image-platform-mismatch", lambda: self.runner.inspect_image(IMAGE))

    def test_image_command_must_be_actual_reviewed_default(self):
        self.fake.image["Config"]["Cmd"] = ["-e", "process.exit(0)"]
        self.fails("image-command-mismatch", lambda: self.runner.run_server(IMAGE))
        self.assertFalse(any(call[3] == "create" for call in self.fake.calls))

    def test_image_entrypoint_must_be_node(self):
        self.fake.image["Config"]["Entrypoint"] = ["/bin/sh", "-c"]
        self.fails("image-command-mismatch", lambda: self.runner.inspect_image(IMAGE))

    def test_root_image_user_rejected(self):
        self.fake.image["Config"]["User"] = "0"
        self.fails("image-command-mismatch", lambda: self.runner.inspect_image(IMAGE))

    def test_unknown_image_environment_never_leaks(self):
        self.fake.image["Config"]["Env"].append("AWS_SECRET_ACCESS_KEY=fixture-private-value")
        exc = self.fails("image-environment-invalid", lambda: self.runner.inspect_image(IMAGE))
        self.assertNotIn("fixture-private-value", str(exc))

    def test_duplicate_image_environment_rejected(self):
        self.fake.image["Config"]["Env"].append("PORT=3000")
        self.fails("image-environment-invalid", lambda: self.runner.inspect_image(IMAGE))

    def test_missing_source_revision_environment_rejected(self):
        self.fake.image["Config"]["Env"] = [row for row in self.fake.image["Config"]["Env"] if not row.startswith("PLATFORM_SOURCE_")]
        self.fails("image-environment-invalid", lambda: self.runner.inspect_image(IMAGE))

    def test_invalid_image_layers_rejected(self):
        self.fake.image["RootFS"]["Layers"] = []
        self.fails("image-layers-invalid", lambda: self.runner.inspect_image(IMAGE))

    def test_build_is_untagged_offline_pinned_verified_stage(self):
        context = self.root / "context"
        context.mkdir()
        dockerfile = context / "Dockerfile"
        dockerfile.write_text("fixture")
        self.assertEqual(self.runner.build(context, dockerfile, BASE, COMMIT), IMAGE)
        args = next(call[3:] for call in self.fake.calls if call[3] == "build")
        self.assertIn("PAYLOAD_STAGE=verified", args)
        self.assertIn("RUNTIME_NODE_IMAGE=" + BASE, args)
        self.assertIn("--no-cache", args)
        self.assertIn("--provenance=false", args)
        self.assertEqual(args[args.index("--network") + 1], "none")
        self.assertEqual(args[args.index("--platform") + 1], "linux/amd64")
        self.assertNotIn("--tag", args)
        self.assertFalse(any(call[3] == "pull" for call in self.fake.calls))

    def test_build_rejects_context_outside_owned_scratch(self):
        self.fails("build-path-invalid", lambda: self.runner.build(self.root.parent, self.root / "none", BASE, COMMIT))
        self.assertEqual(self.fake.calls, [])

    def test_build_rejects_unbound_source_revision(self):
        context = self.root / "context"
        context.mkdir()
        dockerfile = context / "Dockerfile"
        dockerfile.write_text("fixture")
        self.fails("source-commit-invalid", lambda: self.runner.build(context, dockerfile, BASE, "HEAD"))
        self.assertEqual(self.fake.calls, [])

    def test_missing_iidfile_never_counts_as_build_success(self):
        context = self.root / "context"
        context.mkdir()
        dockerfile = context / "Dockerfile"
        dockerfile.write_text("fixture")
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, b"", b"") if args[0] == "build" else None
        self.fails("image-id-invalid", lambda: self.runner.build(context, dockerfile, BASE, COMMIT))

    def test_runtime_executes_default_command_private_health_and_graceful_stop(self):
        receipt = self.runner.run_server(IMAGE)
        self.assertEqual(receipt["verdict"], "passed")
        self.assertTrue(receipt["cleanup_verified"])
        self.assertEqual(receipt["shutdown"], {"signal": "SIGTERM", "exit_code": 0, "oom_killed": False})
        self.assertEqual(receipt["node_version"], "v22.23.3")
        create = next(call[3:] for call in self.fake.calls if call[3] == "create")
        self.assertEqual(create[-1], IMAGE)
        self.assertNotIn("--entrypoint", create)
        self.assertNotIn("--publish", create)
        self.assertNotIn("--mount", create)
        self.assertNotIn("--volume", create)
        self.assertEqual(create[create.index("--network") + 1], "none")
        self.assertTrue(any(call[3:5] == ["stop", "--time"] for call in self.fake.calls))
        self.assertTrue(self.fake.deleted)

    def test_runtime_image_mismatch_rejected_and_owned_container_removed(self):
        self.fake.inspect_hook = lambda value: value.update(Image=BASE_ID)
        self.fails("container-image-mismatch", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_runtime_custom_command_rejected(self):
        self.fake.inspect_hook = lambda value: value["Config"].update(Cmd=["-e", "process.exit(0)"])
        self.fails("container-command-mismatch", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_runtime_privilege_drift_rejected(self):
        self.fake.inspect_hook = lambda value: value["HostConfig"].update(Privileged=True)
        self.fails("container-restriction-mismatch", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_runtime_host_network_rejected(self):
        self.fake.inspect_hook = lambda value: value["HostConfig"].update(NetworkMode="host")
        self.fails("container-restriction-mismatch", lambda: self.runner.run_server(IMAGE))

    def test_runtime_host_mount_rejected(self):
        self.fake.inspect_hook = lambda value: value["Mounts"].append({"Source": "/home/private"})
        self.fails("container-restriction-mismatch", lambda: self.runner.run_server(IMAGE))

    def test_runtime_env_drift_rejected(self):
        self.fake.inspect_hook = lambda value: value["Config"]["Env"].append("NODE_OPTIONS=--bad")
        self.fails("container-environment-mismatch", lambda: self.runner.run_server(IMAGE))

    def test_runtime_oom_is_failure(self):
        self.fake.inspect_hook = lambda value: value["State"].update(OOMKilled=True)
        self.fails("container-state-mismatch", lambda: self.runner.run_server(IMAGE))

    def test_partial_health_results_are_not_pass(self):
        self.fake.health = self.fake.health[:1]
        self.fails("health-evidence-invalid", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_skipped_health_result_is_not_pass(self):
        self.fake.health = {"verdict": "skipped", "reason": "missing-engine"}
        self.fails("health-evidence-invalid", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_health_timeout_fails_and_cleans_owned_container(self):
        def hook(args):
            if args[0] == "exec":
                raise engine.EngineFailure("local-container-engine-timeout")
        self.fake.hook = hook
        self.fails("engine-timeout", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_shutdown_forced_kill_is_failure(self):
        self.fake.exit_code = 137
        self.fails("shutdown-failed", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_ownership_mismatch_never_removes_container(self):
        self.fake.inspect_hook = lambda value: value["Config"]["Labels"].update({engine.OWNER_LABEL: "other-owner"})
        self.fails("container-ownership-mismatch", lambda: self.runner.run_server(IMAGE))
        self.assertFalse(self.fake.deleted)
        self.assertFalse(any(call[3] == "rm" for call in self.fake.calls))

    def test_failed_cleanup_prevents_pass(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 1, b"", b"fixture-private-diagnostic") if args[0] == "rm" else None
        self.fails("engine-command-failed", lambda: self.runner.run_server(IMAGE))

    def test_cleanup_checks_container_is_actually_absent(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, CID.encode(), b"") if args[:2] == ["container", "ls"] else None
        self.fails("cleanup-failed", lambda: self.runner.run_server(IMAGE))

    def test_inventory_uses_fixed_source_free_probe_and_owned_cleanup(self):
        self.assertEqual(self.runner.inventory(IMAGE), ROWS)
        create = next(call[3:] for call in self.fake.calls if call[3] == "create")
        self.assertEqual(create[-4:], [engine.NODE, IMAGE, "-e", engine.INVENTORY_PROBE])
        self.assertTrue(self.fake.deleted)

    def test_inventory_duplicate_path_rejected(self):
        self.fake.inventory.append(deepcopy(ROWS[0]))
        self.fails("inventory-invalid", lambda: self.runner.inventory(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_inventory_unsafe_relative_path_rejected(self):
        self.fake.inventory[0]["path"] = "../secret"
        self.fails("inventory-invalid", lambda: self.runner.inventory(IMAGE))

    def test_inventory_empty_or_unexecuted_output_rejected(self):
        self.fake.inventory = []
        self.fails("inventory-invalid", lambda: self.runner.inventory(IMAGE))

    def test_inventory_total_size_bounded(self):
        self.fake.inventory = [{"path": f"file-{index:03d}", "bytes": 16777216, "digest": ROWS[0]["digest"]} for index in range(17)]
        self.fails("inventory-limit", lambda: self.runner.inventory(IMAGE))

    def test_inventory_unknown_fields_rejected(self):
        self.fake.inventory[0]["raw_secret"] = "fixture-private"
        exc = self.fails("inventory-invalid", lambda: self.runner.inventory(IMAGE))
        self.assertNotIn("fixture-private", str(exc))

    def test_stderr_is_never_forwarded(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 1, b"private-stdout", b"private-stderr")
        exc = self.fails("engine-command-failed", self.runner.version)
        self.assertNotIn("private", str(exc))

    def test_missing_engine_fails_without_skip(self):
        def hook(args):
            raise FileNotFoundError("private-host-path")
        self.fake.hook = hook
        self.fails("engine-unavailable", self.runner.version)

    def test_output_bound_enforced_with_injected_runner(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, b"a" * 65537, b"")
        self.fails("engine-output-limit", self.runner.version)

    def test_duplicate_json_keys_rejected(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, b'{"Client":{},"Client":{}}', b"")
        self.fails("engine-output-invalid", self.runner.version)

    def test_invalid_runtime_version_rejected(self):
        self.fake.node_version = b"v99.1.0\n"
        self.fails("runtime-version-invalid", lambda: self.runner.run_server(IMAGE))
        self.assertTrue(self.fake.deleted)

    def test_nonfinite_json_rejected(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, b'{"Client":NaN}', b"")
        self.fails("engine-output-invalid", self.runner.version)

    def test_malformed_version_sections_rejected(self):
        self.fake.hook = lambda args: subprocess.CompletedProcess(args, 0, b'{"Client":[],"Server":null}', b"")
        self.fails("engine-version-invalid", self.runner.version)

    def test_boolean_exit_code_is_not_success(self):
        self.fake.exit_code = False
        self.fails("shutdown-failed", lambda: self.runner.run_server(IMAGE))

    def test_nonascii_runtime_version_is_redacted(self):
        self.fake.node_version = bytes([255])
        self.fails("runtime-version-invalid", lambda: self.runner.run_server(IMAGE))

    def test_real_bounded_process_captures_without_environment_inheritance(self):
        result = engine._bounded_runner([sys.executable, "-c", "print('bounded')"], cwd=self.root,
                                        env={"PATH": "/usr/bin:/bin"}, timeout=2, max_output=1024)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"bounded\n")

    def test_real_bounded_process_timeout_kills_process_group(self):
        self.fails("engine-timeout", lambda: engine._bounded_runner(
            [sys.executable, "-c", "import time; time.sleep(10)"], cwd=self.root,
            env={"PATH": "/usr/bin:/bin"}, timeout=1, max_output=1024))

    def test_real_bounded_process_rejects_excessive_output(self):
        self.fails("engine-output-limit", lambda: engine._bounded_runner(
            [sys.executable, "-c", "import os; os.write(1, b'x' * 65536)"], cwd=self.root,
            env={"PATH": "/usr/bin:/bin"}, timeout=2, max_output=1024))

    def build_fixture(self):
        context = self.root / "metadata-context"
        context.mkdir()
        dockerfile = context / "Dockerfile"
        dockerfile.write_text("fixture")
        return lambda: self.runner.build(context, dockerfile, BASE, COMMIT)

    def test_build_uses_manifest_when_config_iid_is_unaddressable(self):
        build = self.build_fixture()
        def hook(args):
            if args == ["image", "inspect", BASE_ID]:
                return subprocess.CompletedProcess(args, 1, b"", b"No such image")
        self.fake.hook = hook
        self.assertEqual(build(), IMAGE)
        self.assertFalse(any(call[3:] == ["image", "inspect", BASE_ID] for call in self.fake.calls))
        self.assertFalse(any("--tag" in call for call in self.fake.calls))

    def test_build_manifest_iid_is_also_bound(self):
        self.fake.build_iid = IMAGE
        self.assertEqual(self.build_fixture()(), IMAGE)

    def test_build_unrelated_iid_rejected(self):
        self.fake.build_iid = "sha256:" + "9" * 64
        self.fails("build-identity-mismatch", self.build_fixture())

    def test_build_missing_metadata_rejected(self):
        self.fake.build_metadata = None
        self.fails("build-metadata-invalid", self.build_fixture())

    def test_build_malformed_metadata_rejected(self):
        self.fake.build_metadata = b"not-json"
        self.fails("engine-output-invalid", self.build_fixture())

    def test_build_duplicate_metadata_keys_rejected(self):
        self.fake.build_metadata = ('{"containerimage.digest":"' + IMAGE + '","containerimage.digest":"' + IMAGE + '"}').encode()
        self.fails("engine-output-invalid", self.build_fixture())

    def test_build_metadata_symlink_rejected(self):
        target = self.root / "other-metadata.json"
        target.write_text(json.dumps(self.fake.build_metadata))
        self.fake.metadata_link = target
        self.fails("build-metadata-invalid", self.build_fixture())

    def test_build_oversized_metadata_rejected(self):
        self.fake.build_metadata = b" " * 65537
        self.fails("build-metadata-invalid", self.build_fixture())

    def test_build_descriptor_manifest_mismatch_rejected(self):
        self.fake.build_metadata["containerimage.descriptor"]["digest"] = BASE_ID
        self.fails("build-identity-mismatch", self.build_fixture())


if __name__ == "__main__":
    unittest.main()
