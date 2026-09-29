"""Offline positive and rejection tests for the isolated build toolchain."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-locked-toolchain
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject altered archives, dependency closures, unsafe paths and installation false success.
#   portability: {class: reusable, targets: [entity-builder]}
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch

import locked_toolchain as tool


def archive(rows, root="package"):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as output:
        for name, data, kind in rows:
            member = tarfile.TarInfo(root + "/" + name)
            member.type = kind
            member.mode = 0o755 if name.startswith("bin/") else 0o644
            if kind == tarfile.SYMTYPE:
                member.linkname = data.decode()
                output.addfile(member)
            elif kind == tarfile.REGTYPE:
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
            else:
                output.addfile(member)
    return buffer.getvalue()


class LockedToolchainTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="locked-toolchain-test-")
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.root = self.base / "source"
        self.root.mkdir()
        self.cache = self.base / "cache"
        self.cache.mkdir()
        (self.root / "apps/app").mkdir(parents=True)
        self.workspace = {"name": "@sample/app", "version": "0.0.0"}
        self.manifest = {"name": "fixture", "private": True, "workspaces": ["apps/*"],
                         "devDependencies": {"typescript": "5.9.3"}}
        self.files = {"package.json": json.dumps({"name": "typescript", "version": "5.9.3"}).encode(),
                      "bin/tsc": b"// compiler fixture\n", "bin/tsserver": b"// server fixture\n"}
        self.payload = archive([(name, data, tarfile.REGTYPE) for name, data in self.files.items()])
        self.integrity = "sha512-" + base64.b64encode(hashlib.sha512(self.payload).digest()).decode()
        self.external = {"version": "5.9.3", "integrity": self.integrity,
                         "resolved": "https://registry.npmjs.org/typescript/-/typescript-5.9.3.tgz"}
        self.lock = {"name": "fixture", "lockfileVersion": 3, "packages": {
            "": copy.deepcopy(self.manifest), "apps/app": copy.deepcopy(self.workspace),
            "node_modules/@sample/app": {"link": True, "resolved": "apps/app"},
            "node_modules/typescript": self.external}}
        self.contract = tool.load_toolchain()
        self.contract["dependencies"].update(external_packages=1, workspaces=1)
        self.save_project()
        self.closure = tool.inspect_project(self.root, self.contract)
        self.filename = hashlib.sha256(self.payload).hexdigest() + ".tgz"
        (self.cache / self.filename).write_bytes(self.payload)
        self.cache_manifest = {"package_lock_sha256": self.closure["lock_sha256"],
                               "packages": [{**self.closure["external"][0], "filename": self.filename}]}
        self.save_cache()
        self.toolchain = {"node": "/toolchain/bin/node", "npm_cli": "/toolchain/lib/npm-cli.js",
                          "contract_digest": "sha256:" + "a" * 64}

    def save_project(self):
        (self.root / "package.json").write_text(json.dumps(self.manifest))
        (self.root / "apps/app/package.json").write_text(json.dumps(self.workspace))
        raw = json.dumps(self.lock).encode()
        (self.root / "package-lock.json").write_bytes(raw)
        self.contract["dependencies"]["lock_sha256"] = hashlib.sha256(raw).hexdigest()

    def save_cache(self):
        (self.cache / "verified-artifacts.json").write_text(json.dumps(self.cache_manifest))

    def installed(self):
        module = self.root / "node_modules"
        (module / "typescript/bin").mkdir(parents=True)
        for name, data in self.files.items():
            (module / "typescript" / name).write_bytes(data)
        (module / "@sample").mkdir()
        (module / "@sample/app").symlink_to("../../apps/app")
        (module / ".bin").mkdir()
        for name in ("tsc", "tsserver"):
            (module / ".bin" / name).symlink_to("../typescript/bin/" + name)

    def verify(self):
        return tool.verify_installed(self.root, self.closure,
                                     tool.verify_package_cache(self.cache, self.closure))

    def test_versioned_contract_pins_node_npm_typescript_and_offline_policy(self):
        value = tool.load_toolchain()
        self.assertEqual(value["node"]["version"], "22.23.3")
        self.assertEqual(value["npm"]["version"], "10.9.9")
        self.assertEqual(value["typescript"]["version"], "5.9.3")
        self.assertEqual(value["policy"]["execution_network"], "disabled")

    def test_changed_tool_version_or_archive_source_fails(self):
        for section, key, value in [("node", "version", "22.22.1"), ("npm", "version", "9.2.0"),
                                    ("typescript", "version", "5.8.0"),
                                    ("node", "url", "https://example.invalid/node")]:
            changed = copy.deepcopy(self.contract)
            changed[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(tool.ToolchainFailure):
                tool.validate_contract(changed)

    def test_open_contract_and_unknown_schema_version_fail(self):
        for key, value in [("secret", "sensitive"), ("schema", "local-build-toolchain/v2")]:
            changed = copy.deepcopy(self.contract)
            changed[key] = value
            with self.assertRaisesRegex(tool.ToolchainFailure, "contract-invalid"):
                tool.validate_contract(changed)

    def test_schema_remote_reference_fails_before_validation(self):
        schema = tool.release.load_document(tool.SCHEMA, "test")
        schema["$ref"] = "https://example.invalid/schema"
        with patch.object(tool.release, "load_document", return_value=schema):
            with self.assertRaisesRegex(tool.ToolchainFailure, "schema-reference"):
                tool.validate_contract(self.contract)

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaisesRegex(tool.ToolchainFailure, "json-duplicate"):
            tool._json(b'{"value":1,"value":2}')

    def test_non_json_numbers_and_large_json_are_rejected(self):
        for raw in (b'{"value":NaN}', b" " * (tool.MAX_JSON + 1)):
            with self.assertRaises(tool.ToolchainFailure):
                tool._json(raw)

    def test_symlink_parent_and_fifo_reads_are_rejected(self):
        (self.base / "alias").symlink_to(self.root)
        with self.assertRaisesRegex(tool.ToolchainFailure, "file-unavailable"):
            tool._read(self.base / "alias/package.json")
        os.mkfifo(self.base / "fifo")
        with self.assertRaisesRegex(tool.ToolchainFailure, "file-invalid"):
            tool._read(self.base / "fifo")

    def test_supported_platform_and_minimum_glibc(self):
        tool.validate_platform("Linux", "x86_64", ("glibc", "2.28"))
        tool.validate_platform("Linux", "x86_64", ("glibc", "2.41"))

    def test_unsupported_platforms_are_rejected(self):
        for system, machine, libc in [("Darwin", "x86_64", ("glibc", "2.41")),
                                      ("Linux", "aarch64", ("glibc", "2.41")),
                                      ("Linux", "x86_64", ("musl", "2.41")),
                                      ("Linux", "x86_64", ("glibc", "2.27")),
                                      ("Linux", "x86_64", ("glibc", "unknown"))]:
            with self.assertRaisesRegex(tool.ToolchainFailure, "platform-unsupported"):
                tool.validate_platform(system, machine, libc)

    def test_complete_dependency_and_workspace_closure_is_bound(self):
        self.assertEqual(len(self.closure["external"]), 1)
        self.assertEqual(len(self.closure["links"]), 1)
        self.assertEqual(len(self.closure["bindings"]), 3)
        self.assertTrue(self.closure["closure_digest"].startswith("sha256:"))

    def test_modified_unreviewed_lock_is_rejected(self):
        (self.root / "package-lock.json").write_text("{}")
        with self.assertRaisesRegex(tool.ToolchainFailure, "dependency-lock-mismatch"):
            tool.inspect_project(self.root, self.contract)

    def test_manifest_lock_dependency_drift_is_rejected(self):
        self.manifest["devDependencies"]["typescript"] = "5.9.2"
        self.save_project()
        with self.assertRaisesRegex(tool.ToolchainFailure, "manifest-lock-mismatch"):
            tool.inspect_project(self.root, self.contract)

    def test_missing_and_extra_locked_dependency_fail(self):
        self.lock["packages"].pop("node_modules/typescript")
        self.save_project()
        with self.assertRaisesRegex(tool.ToolchainFailure, "dependency-count-mismatch"):
            tool.inspect_project(self.root, self.contract)

    def test_unsupported_dependency_urls_and_weak_hashes_fail(self):
        for field, value in [("resolved", "file:/tmp/package"), ("resolved", "https://evil.invalid/x"),
                              ("integrity", "sha1-abcdef"), ("integrity", "sha512-AAAA")]:
            original = self.external[field]
            self.external[field] = value
            self.save_project()
            with self.subTest(field=field), self.assertRaises(tool.ToolchainFailure):
                tool.inspect_project(self.root, self.contract)
            self.external[field] = original

    def test_dynamic_and_nested_dependency_layouts_fail(self):
        for name in ("node_modules/x/node_modules/y", "node_modules/../private"):
            self.lock["packages"][name] = self.lock["packages"].pop("node_modules/typescript")
            self.save_project()
            with self.assertRaises(tool.ToolchainFailure):
                tool.inspect_project(self.root, self.contract)
            self.lock["packages"]["node_modules/typescript"] = self.lock["packages"].pop(name)

    def test_install_script_and_platform_selective_lock_records_fail(self):
        for key, value in [("hasInstallScript", True), ("os", ["linux"]), ("inBundle", True)]:
            self.external[key] = value
            self.save_project()
            with self.assertRaisesRegex(tool.ToolchainFailure, "dependency-source-unsupported"):
                tool.inspect_project(self.root, self.contract)
            del self.external[key]

    def test_unreviewed_workspace_and_workspace_symlink_fail(self):
        (self.root / "apps/extra").mkdir()
        (self.root / "apps/extra/package.json").write_text('{}')
        with self.assertRaisesRegex(tool.ToolchainFailure, "workspace-membership-mismatch"):
            tool.inspect_project(self.root, self.contract)
        (self.root / "apps/escape").symlink_to(self.base)
        with self.assertRaisesRegex(tool.ToolchainFailure, "workspace-path-invalid"):
            tool.inspect_project(self.root, self.contract)

    def test_workspace_target_outside_root_and_wrong_name_fail(self):
        self.lock["packages"]["node_modules/@sample/app"]["resolved"] = "../outside"
        self.save_project()
        with self.assertRaisesRegex(tool.ToolchainFailure, "path-invalid"):
            tool.inspect_project(self.root, self.contract)

    def test_workspace_dependency_drift_and_lifecycle_scripts_fail(self):
        self.workspace["dependencies"] = {"unlocked": "1.0.0"}
        self.save_project()
        with self.assertRaisesRegex(tool.ToolchainFailure, "workspace-manifest-lock-mismatch"):
            tool.inspect_project(self.root, self.contract)
        self.workspace.pop("dependencies")
        self.workspace["scripts"] = {"prepare": "run-secret"}
        self.save_project()
        with self.assertRaisesRegex(tool.ToolchainFailure, "workspace-lifecycle-unsupported"):
            tool.inspect_project(self.root, self.contract)

    def test_project_npm_configuration_and_shrinkwrap_are_rejected(self):
        for name in (".npmrc", "npm-shrinkwrap.json"):
            path = self.root / name
            path.write_text("sensitive")
            with self.assertRaisesRegex(tool.ToolchainFailure, "project-configuration-unsupported"):
                tool.inspect_project(self.root, self.contract)
            path.unlink()

    def test_archive_safely_accepts_regular_files_and_legacy_package_root(self):
        payload = archive([("package.json", b"{}", tarfile.REGTYPE)], "node v22.20")
        opened, members, root = tool._archive(payload)
        self.addCleanup(opened.close)
        self.assertEqual(root, "node v22.20")
        self.assertEqual(len(members), 1)

    def test_archive_path_escape_and_duplicates_are_rejected(self):
        for names in [("../escape",), ("same", "same")]:
            payload = archive([(name, b"x", tarfile.REGTYPE) for name in names])
            with self.assertRaises(tool.ToolchainFailure):
                tool._archive(payload)

    def test_package_links_and_special_files_are_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE):
            with self.assertRaisesRegex(tool.ToolchainFailure, "archive-member-unsupported"):
                tool._archive(archive([("escape", b"../../secret", kind)]))

    def test_node_allows_only_three_reviewed_contained_links(self):
        payload = archive([("bin/npm", b"../lib/node_modules/npm/bin/npm-cli.js", tarfile.SYMTYPE)],
                          "node-v22.23.3-linux-x64")
        opened, _members, _root = tool._archive(payload, node=True)
        opened.close()
        for name, target in [("bin/npm", b"../../escape"), ("bin/extra", b"lib/extra")]:
            with self.assertRaisesRegex(tool.ToolchainFailure, "archive-link-invalid"):
                tool._archive(archive([(name, target, tarfile.SYMTYPE)],
                                      "node-v22.23.3-linux-x64"), node=True)

    def test_archive_count_and_expansion_limits_are_enforced(self):
        payload = archive([("a", b"hello", tarfile.REGTYPE), ("b", b"world", tarfile.REGTYPE)])
        for key in ("MAX_MEMBERS", "MAX_EXPANDED"):
            with patch.object(tool, key, 1), self.assertRaisesRegex(tool.ToolchainFailure, "archive-limit"):
                tool._archive(payload)

    def test_wrong_node_bytes_fail_before_destination_creation(self):
        (self.cache / self.contract["node"]["filename"]).write_bytes(b"untrusted")
        destination = self.base / "extraction"
        with patch.object(tool, "validate_platform"), self.assertRaisesRegex(tool.ToolchainFailure, "node-hash-mismatch"):
            tool.prepare_toolchain(self.cache, destination, self.contract)
        self.assertFalse(destination.exists())

    def test_package_bytes_and_identity_are_independently_verified(self):
        packages = tool.verify_package_cache(self.cache, self.closure)
        self.assertEqual(packages[0]["name"], "typescript")
        self.assertEqual(set(packages[0]["files"]), set(self.files))

    def test_tampered_package_bytes_fail(self):
        (self.cache / self.filename).write_bytes(self.payload + b"changed")
        with self.assertRaisesRegex(tool.ToolchainFailure, "cache-bytes-invalid"):
            tool.verify_package_cache(self.cache, self.closure)

    def test_cache_cannot_redirect_tarball_path(self):
        self.cache_manifest["packages"][0]["filename"] = "../secret"
        self.save_cache()
        with self.assertRaisesRegex(tool.ToolchainFailure, "cache-filename-invalid"):
            tool.verify_package_cache(self.cache, self.closure)

    def test_cache_missing_duplicate_or_wrong_lock_rejected(self):
        original = copy.deepcopy(self.cache_manifest)
        for mutate in (lambda m: m.update(packages=[]),
                       lambda m: m["packages"].append(copy.deepcopy(m["packages"][0])),
                       lambda m: m.update(package_lock_sha256="0" * 64)):
            self.cache_manifest = copy.deepcopy(original)
            mutate(self.cache_manifest)
            self.save_cache()
            with self.assertRaises(tool.ToolchainFailure):
                tool.verify_package_cache(self.cache, self.closure)

    def test_cache_cannot_change_verified_dependency_identity(self):
        self.cache_manifest["packages"][0]["version"] = "5.9.2"
        self.save_cache()
        with self.assertRaisesRegex(tool.ToolchainFailure, "cache-binding-mismatch"):
            tool.verify_package_cache(self.cache, self.closure)

    def test_exact_installed_files_and_workspace_links_pass(self):
        self.installed()
        receipt = self.verify()
        self.assertEqual(receipt["external_packages"], 1)
        self.assertEqual(receipt["workspace_links"], 1)

    def test_changed_installed_file_bytes_fail(self):
        self.installed()
        (self.root / "node_modules/typescript/bin/tsc").write_text("altered")
        with self.assertRaisesRegex(tool.ToolchainFailure, "installed-package-files-mismatch"):
            self.verify()

    def test_missing_and_extra_installed_package_fail(self):
        self.installed()
        (self.root / "node_modules/extra").mkdir()
        with self.assertRaisesRegex(tool.ToolchainFailure, "installed-closure-mismatch"):
            self.verify()

    def test_missing_and_extra_installed_file_fail(self):
        self.installed()
        (self.root / "node_modules/typescript/bin/extra").write_text("extra")
        with self.assertRaisesRegex(tool.ToolchainFailure, "installed-package-files-mismatch"):
            self.verify()

    def test_wrong_workspace_link_and_bin_link_fail(self):
        self.installed()
        path = self.root / "node_modules/@sample/app"
        path.unlink()
        path.symlink_to(self.base)
        with self.assertRaisesRegex(tool.ToolchainFailure, "installed-workspace-link-mismatch"):
            self.verify()

    def test_wrong_executable_shim_fails(self):
        self.installed()
        path = self.root / "node_modules/.bin/tsc"
        path.unlink()
        path.symlink_to("/bin/true")
        with self.assertRaisesRegex(tool.ToolchainFailure, "installed-bin-mismatch"):
            self.verify()

    def test_source_manifest_change_after_install_fails(self):
        self.installed()
        (self.root / "package.json").write_text("{}")
        with self.assertRaisesRegex(tool.ToolchainFailure, "source-manifest-changed"):
            self.verify()

    def test_environment_inherits_no_credentials_or_loader_configuration(self):
        with patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "sensitive", "NODE_OPTIONS": "--require evil",
                                     "npm_config_registry": "https://example.invalid"}):
            environment = tool.child_environment(self.root, self.toolchain)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        self.assertNotIn("NODE_OPTIONS", environment)
        self.assertEqual(environment["npm_config_registry"], "https://registry.npmjs.org/")
        self.assertEqual(environment["npm_config_offline"], "true")

    def test_offline_install_uses_pinned_tools_and_disabled_lifecycle(self):
        calls = []
        def execute(argv, cwd, env):
            calls.append(argv)
            self.assertEqual(cwd, self.root)
            self.assertEqual(env["npm_config_ignore_scripts"], "true")
            if "ci" in argv:
                self.installed()
            output = ""
            if argv == [self.toolchain["node"], "--version"]:
                output = "v22.23.3\n"
            elif argv[-1] == "--version":
                output = "Version 5.9.3\n" if "typescript" in argv[-2] else "10.9.9\n"
            return {"returncode": 0, "stdout": output}
        result = tool.install_dependencies(self.root, self.toolchain, self.cache, self.closure, execute)
        self.assertFalse(result["authorized"])
        self.assertEqual(len(calls), 5)
        installation = next(call for call in calls if "ci" in call)
        self.assertIn("--offline", installation)
        self.assertIn("--ignore-scripts", installation)
        self.assertIn("--include=optional", installation)

    def test_callback_command_failure_is_sanitized(self):
        def execute(*_args):
            return {"returncode": 73, "stdout": "sensitive", "stderr": "private"}
        with self.assertRaisesRegex(tool.ToolchainFailure, "^locked-toolchain-command-failed$"):
            tool.install_dependencies(self.root, self.toolchain, self.cache, self.closure, execute)

    def test_wrong_runtime_version_is_rejected(self):
        with self.assertRaisesRegex(tool.ToolchainFailure, "runtime-version-mismatch"):
            tool.install_dependencies(self.root, self.toolchain, self.cache, self.closure,
                                      lambda *_: {"returncode": 0, "stdout": "v22.22.1"})

    def test_existing_installation_is_never_removed_or_overwritten(self):
        self.installed()
        with self.assertRaisesRegex(tool.ToolchainFailure, "installation-destination-invalid"):
            tool.install_dependencies(self.root, self.toolchain, self.cache, self.closure,
                                      lambda *_: self.fail("must not execute"))
        self.assertTrue((self.root / "node_modules/typescript/bin/tsc").exists())

    def test_manifest_change_rejects_before_any_execution(self):
        (self.root / "package.json").write_text("{}")
        with self.assertRaisesRegex(tool.ToolchainFailure, "source-manifest-changed"):
            tool.install_dependencies(self.root, self.toolchain, self.cache, self.closure,
                                      lambda *_: self.fail("must not execute"))

    def download_response(self, payload=b"verified bytes", url="https://registry.npmjs.org/fixture.tgz"):
        response = io.BytesIO(payload)
        response.geturl = lambda: url
        return response

    def test_public_download_retries_only_bounded_transient_failures(self):
        opener = Mock()
        opener.open.side_effect = [OSError("private detail"), OSError("another detail"), self.download_response()]
        self.assertEqual(tool._download(opener, "https://registry.npmjs.org/fixture.tgz", 64), b"verified bytes")
        self.assertEqual(opener.open.call_count, 3)

    def test_public_download_exhaustion_has_safe_failure_and_exact_attempt_limit(self):
        opener = Mock()
        opener.open.side_effect = OSError("private detail")
        with self.assertRaisesRegex(tool.ToolchainFailure, "^locked-toolchain-download-failed$"):
            tool._download(opener, "https://registry.npmjs.org/fixture.tgz", 64)
        self.assertEqual(opener.open.call_count, 3)

    def test_public_download_does_not_retry_authentication_failure(self):
        opener = Mock()
        opener.open.side_effect = tool.urllib.error.HTTPError("https://registry.npmjs.org/fixture.tgz", 401,
                                                           "private detail", {}, None)
        with self.assertRaisesRegex(tool.ToolchainFailure, "download-failed"):
            tool._download(opener, "https://registry.npmjs.org/fixture.tgz", 64)
        self.assertEqual(opener.open.call_count, 1)

    def test_public_download_retries_rate_limit(self):
        opener = Mock()
        opener.open.side_effect = [tool.urllib.error.HTTPError("https://registry.npmjs.org/fixture.tgz", 429,
                                                            "rate limited", {}, None), self.download_response()]
        self.assertEqual(tool._download(opener, "https://registry.npmjs.org/fixture.tgz", 64), b"verified bytes")
        self.assertEqual(opener.open.call_count, 2)

    def test_public_download_rejects_redirect_and_oversize_without_retry(self):
        for response, code in [(self.download_response(url="https://unreviewed.invalid/"), "download-redirect"),
                               (self.download_response(b"x" * 65), "download-limit")]:
            opener = Mock()
            opener.open.return_value = response
            with self.assertRaisesRegex(tool.ToolchainFailure, code):
                tool._download(opener, "https://registry.npmjs.org/fixture.tgz", 64)
            self.assertEqual(opener.open.call_count, 1)

    def acquisition_fixture(self):
        contract = copy.deepcopy(self.contract)
        node = b"inert hash-verified node fixture"
        contract["node"]["sha256"] = hashlib.sha256(node).hexdigest()
        (self.cache / contract["node"]["filename"]).write_bytes(node)
        (self.cache / "verified-artifacts.json").unlink()
        return contract

    def test_public_acquisition_resumes_partial_cache_and_never_replaces_files(self):
        contract = self.acquisition_fixture()
        before = {path.name: (path.read_bytes(), path.stat().st_ino) for path in self.cache.iterdir()}
        with patch.object(tool, "validate_contract", return_value=contract), patch.object(tool, "_download") as fetch:
            result = tool.acquire_cache(self.root, self.cache, contract)
            fetch.assert_not_called()
        self.assertEqual(result["packages"], 1)
        self.assertFalse(result["authorized"])
        for name, expected in before.items():
            self.assertEqual(((self.cache / name).read_bytes(), (self.cache / name).stat().st_ino), expected)
        all_before = {path.name: (path.read_bytes(), path.stat().st_ino) for path in self.cache.iterdir()}
        with patch.object(tool, "validate_contract", return_value=contract), patch.object(tool, "_download") as fetch:
            self.assertEqual(tool.acquire_cache(self.root, self.cache, contract), result)
            fetch.assert_not_called()
        self.assertEqual({path.name: (path.read_bytes(), path.stat().st_ino) for path in self.cache.iterdir()}, all_before)

    def test_public_acquisition_refuses_altered_cached_bytes_before_network(self):
        contract = self.acquisition_fixture()
        altered = self.cache / self.filename
        altered.write_bytes(b"altered cached artifact")
        with patch.object(tool, "validate_contract", return_value=contract), patch.object(tool, "_download") as fetch:
            with self.assertRaisesRegex(tool.ToolchainFailure, "cache-bytes-invalid"):
                tool.acquire_cache(self.root, self.cache, contract)
            fetch.assert_not_called()
        self.assertEqual(altered.read_bytes(), b"altered cached artifact")

    def test_public_acquisition_refuses_altered_node_before_network(self):
        contract = self.acquisition_fixture()
        altered = self.cache / contract["node"]["filename"]
        altered.write_bytes(b"altered node archive")
        with patch.object(tool, "validate_contract", return_value=contract), patch.object(tool, "_download") as fetch:
            with self.assertRaisesRegex(tool.ToolchainFailure, "node-hash-mismatch"):
                tool.acquire_cache(self.root, self.cache, contract)
            fetch.assert_not_called()
        self.assertEqual(altered.read_bytes(), b"altered node archive")

    def test_public_acquisition_refuses_unrelated_files_and_symlink_cache(self):
        contract = self.acquisition_fixture()
        (self.cache / "unrelated.txt").write_text("untouched")
        with patch.object(tool, "validate_contract", return_value=contract), patch.object(tool, "_download") as fetch:
            with self.assertRaises(tool.ToolchainFailure):
                tool.acquire_cache(self.root, self.cache, contract)
            fetch.assert_not_called()
        link = self.base / "cache-alias"
        link.symlink_to(self.cache)
        with patch.object(tool, "validate_contract", return_value=contract), patch.object(tool, "_download") as fetch:
            with self.assertRaisesRegex(tool.ToolchainFailure, "cache-directory-invalid"):
                tool.acquire_cache(self.root, link, contract)
            fetch.assert_not_called()

    def test_cache_exclusive_write_refuses_existing_file_without_overwrite(self):
        path = self.cache / "existing"
        path.write_bytes(b"preserve")
        with self.assertRaisesRegex(tool.ToolchainFailure, "cache-write-failed"):
            tool._write_new(path, b"replacement")
        self.assertEqual(path.read_bytes(), b"preserve")

    def test_unexpected_public_input_error_does_not_expose_values(self):
        with self.assertRaisesRegex(tool.ToolchainFailure, "^locked-toolchain-input-invalid$"):
            tool.inspect_project(None, self.contract)


if __name__ == "__main__":
    unittest.main()
