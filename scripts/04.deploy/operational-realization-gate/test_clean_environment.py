"""Offline regression checks for locked validation, isolation and failure propagation."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-clean-environment
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject changed artifacts, incomplete locks, unsupported runtimes and false clean-check success.
#   portability: {class: reusable, targets: [entity-builder]}
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import clean_environment as clean


DIRECTORY = Path(__file__).resolve().parent


class CleanEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="clean-environment-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.lock = self.root / "requirements.lock"
        self.original_lock = (DIRECTORY / "requirements.lock").read_text()
        self.lock.write_text(self.original_lock)

    def change_lock(self, before, after):
        self.lock.write_text(self.original_lock.replace(before, after))

    def test_lock_pins_complete_installer_and_runtime_dependency_closure(self):
        lock = clean.read_lock(self.lock)
        self.assertEqual(len(lock), 8)
        self.assertEqual(lock["pyyaml"]["version"], "6.0.3")
        self.assertEqual(lock["jsonschema"]["version"], "4.19.2")
        clean.validate_requirements(DIRECTORY / "requirements.txt")

    def test_missing_transitive_dependency_fails(self):
        self.lock.write_text("\n".join(
            line for line in self.original_lock.splitlines() if not line.startswith("attrs==")))
        with self.assertRaisesRegex(clean.EnvironmentFailure, "lock-closure-invalid"):
            clean.read_lock(self.lock)

    def test_duplicate_normalized_package_fails(self):
        self.lock.write_text(self.original_lock + "\nTYPING_EXTENSIONS==4.15.0 --hash=sha256:" + "0" * 64)
        with self.assertRaisesRegex(clean.EnvironmentFailure, "lock-duplicate"):
            clean.read_lock(self.lock)

    def test_unpinned_or_unhashed_requirement_fails(self):
        for bad_line in ("PyYAML>=6", "PyYAML==6.0.3", "PyYAML==6.0.3 --hash=md5:123",
                         "PyYAML==6.0.3; python_version > '3'"):
            with self.subTest(bad_line=bad_line):
                self.lock.write_text(self.original_lock + "\n" + bad_line)
                with self.assertRaisesRegex(clean.EnvironmentFailure, "lock-invalid"):
                    clean.read_lock(self.lock)

    def test_index_direct_url_and_recursive_requirements_are_rejected(self):
        for extra in ("--extra-index-url https://example.invalid", "-r other.txt",
                      "package @ https://example.invalid/package.whl", "--no-require-hashes"):
            with self.subTest(extra=extra):
                self.lock.write_text(self.original_lock + "\n" + extra)
                with self.assertRaisesRegex(clean.EnvironmentFailure, "lock-invalid"):
                    clean.read_lock(self.lock)

    def test_unreviewed_bootstrap_version_or_hash_fails(self):
        for before, after in (("pip==25.2", "pip==25.3"), (clean.PIP_SHA256, "0" * 64)):
            with self.subTest(before=before):
                self.change_lock(before, after)
                with self.assertRaisesRegex(clean.EnvironmentFailure, "bootstrap-binding-invalid"):
                    clean.read_lock(self.lock)

    def test_direct_requirement_escape_from_lock_fails(self):
        path = self.root / "requirements.txt"
        path.write_text("PyYAML==6.0.3\njsonschema==4.19.2\n")
        with self.assertRaisesRegex(clean.EnvironmentFailure, "requirements-lock-mismatch"):
            clean.validate_requirements(path)

    def test_declared_runtime_is_supported(self):
        clean.validate_runtime("CPython", (3, 14, 4), "Linux", "x86_64", ("glibc", "2.17"), False)

    def test_wrong_python_patch_and_implementation_fail(self):
        for implementation, version in (("CPython", (3, 14, 3)), ("CPython", (3, 13, 7)),
                                        ("PyPy", (3, 14, 4))):
            with self.subTest(implementation=implementation, version=version):
                with self.assertRaisesRegex(clean.EnvironmentFailure, "python-version-unsupported"):
                    clean.validate_runtime(implementation, version, "Linux", "x86_64", ("glibc", "2.17"), False)

    def test_unsupported_abi_platform_or_libc_fails(self):
        for system, machine, libc, threaded in (
            ("Darwin", "x86_64", ("glibc", "2.17"), False),
            ("Linux", "aarch64", ("glibc", "2.17"), False),
            ("Linux", "x86_64", ("musl", "1.2"), False),
            ("Linux", "x86_64", ("glibc", "2.16"), False),
            ("Linux", "x86_64", ("", ""), False),
            ("Linux", "x86_64", ("glibc", "2.17"), True),
        ):
            with self.subTest(system=system, machine=machine, libc=libc, threaded=threaded):
                with self.assertRaises(clean.EnvironmentFailure):
                    clean.validate_runtime("CPython", (3, 14, 4), system, machine, libc, threaded)

    def test_valid_artifact_hash_is_accepted_and_modified_bytes_fail(self):
        payload = b"test wheel bytes"
        digest = hashlib.sha256(payload).hexdigest()
        clean.verify_wheel(payload, digest)
        with self.assertRaisesRegex(clean.EnvironmentFailure, "wheel-hash-mismatch"):
            clean.verify_wheel(payload + b"tampered", digest)

    def test_empty_or_oversized_wheel_is_rejected(self):
        for payload in (b"", b"x" * (clean.MAX_WHEEL_BYTES + 1)):
            with self.assertRaisesRegex(clean.EnvironmentFailure, "wheel-size-invalid"):
                clean.verify_wheel(payload, hashlib.sha256(payload).hexdigest())

    def test_offline_bootstrap_never_falls_back_to_network(self):
        with patch.object(clean.urllib.request, "urlopen") as network:
            with self.assertRaisesRegex(clean.EnvironmentFailure, "bootstrap-wheel-unavailable"):
                clean.bootstrap_wheel(self.root, self.root)
            network.assert_not_called()

    def test_tampered_offline_bootstrap_is_not_copied_or_executed(self):
        wheelhouse = self.root / "wheelhouse"
        wheelhouse.mkdir()
        (wheelhouse / clean.PIP_FILENAME).write_bytes(b"tampered installer")
        with patch.object(clean.urllib.request, "urlopen") as network:
            with self.assertRaisesRegex(clean.EnvironmentFailure, "wheel-hash-mismatch"):
                clean.bootstrap_wheel(self.root, wheelhouse)
            network.assert_not_called()
        self.assertFalse((self.root / clean.PIP_FILENAME).exists())

    def test_hash_checked_offline_bootstrap_copies_only_verified_bytes(self):
        wheelhouse = self.root / "wheelhouse"
        wheelhouse.mkdir()
        payload = b"inert test wheel"
        (wheelhouse / clean.PIP_FILENAME).write_bytes(payload)
        with patch.object(clean, "PIP_SHA256", hashlib.sha256(payload).hexdigest()):
            result = clean.bootstrap_wheel(self.root, wheelhouse)
        self.assertEqual(result.read_bytes(), payload)

    def test_environment_cannot_inherit_installer_or_python_target_overrides(self):
        original = {"PATH": "/usr/bin", "PYTHONPATH": "/unreviewed", "PYTHONHOME": "/other",
                    "PIP_TARGET": "/global", "PIP_CONFIG_FILE": "/unreviewed",
                    "pip_extra_index_url": "https://example.invalid", "VIRTUAL_ENV": "/old",
                    "NODE_OPTIONS": "--require /other", "npm_config_ignore_scripts": "true",
                    "NODE_PATH": "/other", "BASH_ENV": "/other", "ENV": "/other",
                    "BASH_FUNC_npm%%": "() { return 0; }", "SHELLOPTS": "xtrace",
                    "NPM_CONFIG_SCRIPT_SHELL": "/other", "SHELL": "/bin/bash"}
        child = clean.clean_child_environment(Path("/new/bin"), original)
        self.assertEqual(child["PATH"], "/new/bin:/usr/bin")
        self.assertEqual(child["PIP_CONFIG_FILE"], clean.os.devnull)
        self.assertEqual(child["PYTHONNOUSERSITE"], "1")
        for key in original.keys() - {"PATH", "SHELL", "PIP_CONFIG_FILE"}:
            self.assertNotIn(key, child)
        self.assertEqual(original["PIP_TARGET"], "/global")

    def fake_distributions(self):
        location = self.root / "venv" / "lib" / "site-packages"
        return [SimpleNamespace(metadata={"Name": name}, version=row["version"],
                                locate_file=lambda value, p=location: p)
                for name, row in clean.read_lock(self.lock).items()]

    def test_exact_installed_closure_is_accepted_only_in_venv(self):
        clean.verify_installed(clean.read_lock(self.lock), self.fake_distributions(), self.root / "venv", "/base")
        with self.assertRaisesRegex(clean.EnvironmentFailure, "isolation-invalid"):
            clean.verify_installed(clean.read_lock(self.lock), self.fake_distributions(), "/base", "/base")

    def test_missing_extra_or_changed_installed_distribution_fails(self):
        for mutation in ("missing", "extra", "version", "duplicate"):
            distributions = self.fake_distributions()
            if mutation == "missing":
                distributions.pop()
            elif mutation == "extra":
                distributions.append(SimpleNamespace(metadata={"Name": "unreviewed"}, version="1.0",
                                                      locate_file=lambda value: self.root / "venv"))
            elif mutation == "version":
                distributions[0].version = "999.0"
            else:
                distributions.append(distributions[0])
            with self.subTest(mutation=mutation):
                with self.assertRaises(clean.EnvironmentFailure):
                    clean.verify_installed(clean.read_lock(self.lock), distributions, self.root / "venv", "/base")

    def test_system_site_package_leak_fails_even_if_versions_match(self):
        distributions = self.fake_distributions()
        distributions[0].locate_file = lambda value: Path("/usr/lib/python3/site-packages")
        with self.assertRaisesRegex(clean.EnvironmentFailure, "isolation-invalid"):
            clean.verify_installed(clean.read_lock(self.lock), distributions, self.root / "venv", "/base")

    def test_install_failure_never_runs_source_checks(self):
        with patch.object(clean, "validate_runtime"), patch.object(clean.venv, "EnvBuilder"), \
                patch.object(clean, "bootstrap_wheel", return_value=self.root / clean.PIP_FILENAME), \
                patch.object(clean.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "install")) as run, \
                patch.object(clean.shutil, "which", return_value="/usr/bin/npm"), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(clean.main([]), 1)
        self.assertEqual(run.call_count, 1)
        self.assertIn("--require-hashes", run.call_args.args[0])

    def test_canonical_validation_failure_propagates_without_success_message(self):
        output = io.StringIO()
        outcomes = [None, None, None, subprocess.CalledProcessError(1, "npm")]
        with patch.object(clean, "validate_runtime"), patch.object(clean.venv, "EnvBuilder"), \
                patch.object(clean, "bootstrap_wheel", return_value=self.root / clean.PIP_FILENAME), \
                patch.object(clean.subprocess, "run", side_effect=outcomes) as run, \
                patch.object(clean.shutil, "which", return_value="/usr/bin/npm"), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(clean.main([]), 1)
        self.assertEqual(run.call_args.args[0][-2:], ["run", "deployment:realization:check"])
        self.assertIn("--if-present=false", run.call_args.args[0])
        self.assertNotIn("Clean source validation passed", output.getvalue())

    def test_project_npm_configuration_and_dangling_symlink_are_rejected(self):
        configuration = self.root / ".npmrc"
        configuration.write_text("script-shell=/bin/true\n")
        with self.assertRaisesRegex(clean.EnvironmentFailure, "project-npm-config-unsupported"):
            clean.npm_check_command(self.root, self.root)
        configuration.unlink()
        configuration.symlink_to(self.root / "missing-config")
        with self.assertRaisesRegex(clean.EnvironmentFailure, "project-npm-config-unsupported"):
            clean.npm_check_command(self.root, self.root)

    def test_real_npm_cannot_skip_nested_failure_through_user_config_or_shell_startup(self):
        project = self.root / "project"
        project.mkdir()
        (project / "package.json").write_text(json.dumps({"name": "inert-validation-fixture",
            "scripts": {"deployment:realization:check": "npm run nested-check",
                        "nested-check": "bash -c 'exit 73'"}}))
        poison = self.root / "poisoned-user.config"
        poison.write_text("script-shell=/bin/true\nif-present=true\n")
        startup = self.root / "shell-startup"
        startup.write_text("exit 0\n")
        original = dict(clean.os.environ, npm_config_userconfig=str(poison), BASH_ENV=str(startup),
                        ENV=str(startup), npm_config_script_shell="/bin/true", npm_config_if_present="true")
        child = clean.clean_child_environment(self.root / "unused-venv-bin", original)
        result = subprocess.run(clean.npm_check_command(project, self.root), cwd=project, env=child,
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
        self.assertIn("nested-check", result.stdout)

    def test_real_npm_missing_canonical_script_is_failure(self):
        project = self.root / "project"
        project.mkdir()
        (project / "package.json").write_text('{"name":"inert-validation-fixture","scripts":{}}')
        child = clean.clean_child_environment(self.root / "unused-venv-bin", clean.os.environ)
        result = subprocess.run(clean.npm_check_command(project, self.root), cwd=project, env=child,
                                text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing script", result.stderr)

    def test_offline_install_disallows_indexes_and_source_builds(self):
        command = clean.install_command("python", "pip.whl", self.lock, self.root)
        for required in ("--no-index", "--require-hashes", "--only-binary=:all:", "--no-cache-dir", "--require-virtualenv"):
            self.assertIn(required, command)
        self.assertEqual(command[command.index("--find-links") + 1], str(self.root))

    def test_wrapper_rejects_conflicting_or_bypass_arguments_before_execution(self):
        for arguments in (("--python", "one", "--python", "two"), ("--python",), ("--skip-tests",),
                          ("--wheelhouse", "one", "--wheelhouse", "two")):
            with self.subTest(arguments=arguments):
                result = subprocess.run(["bash", str(DIRECTORY / "verify-clean-environment.sh"), *arguments],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn("clean-environment-arguments-invalid", result.stderr)


if __name__ == "__main__":
    unittest.main()
