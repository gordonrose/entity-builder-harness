"""Reproduce source validation in a disposable, hash-locked Python environment.

This is installation/test tooling, outside the provider-neutral compiler core.
Its successful result is source validation only and never release authority.
"""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-clean-environment
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify locked dependencies in a disposable environment and run the canonical source checks.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files, network]
#   used_by:
#   - id: deploy.command.operational-realization-clean-environment
#     path: scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh

import argparse
import hashlib
import importlib.metadata
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import urllib.request
import venv


PYTHON_VERSION = (3, 14, 4)
EXPECTED_PACKAGES = frozenset({
    "pip", "pyyaml", "jsonschema", "attrs", "referencing", "rpds-py",
    "jsonschema-specifications", "typing-extensions",
})
PIP_FILENAME = "pip-25.2-py3-none-any.whl"
PIP_SHA256 = "6d67a2b4e7f14d8b31b8b52648866fa717f45a1eb70e83002f4331d07e953717"
PIP_URL = (
    "https://files.pythonhosted.org/packages/"
    "b7/3f/945ef7ab14dc4f9d7f40288d2df998d1837ee0888ec3659c813487572faa/"
    + PIP_FILENAME
)
LOCK_LINE = re.compile(
    r"([A-Za-z][A-Za-z0-9_-]*)==([0-9]+(?:\.[0-9]+)+) --hash=sha256:([0-9a-f]{64})"
)
MAX_WHEEL_BYTES = 10 * 1024 * 1024


class EnvironmentFailure(Exception):
    """A safe failure code, without raw environment or source values."""


def normalize_name(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def validate_runtime(implementation, version, system, machine, libc, free_threaded):
    if implementation != "CPython" or tuple(version) != PYTHON_VERSION:
        raise EnvironmentFailure("clean-environment-python-version-unsupported")
    if system != "Linux" or machine != "x86_64" or free_threaded:
        raise EnvironmentFailure("clean-environment-platform-unsupported")
    try:
        libc_version = tuple(int(x) for x in libc[1].split("."))
    except (TypeError, ValueError, IndexError):
        raise EnvironmentFailure("clean-environment-libc-unsupported") from None
    if libc[0] != "glibc" or libc_version < (2, 17):
        raise EnvironmentFailure("clean-environment-libc-unsupported")


def read_lock(path):
    data = path.read_text(encoding="utf-8")
    if len(data) > 32768:
        raise EnvironmentFailure("clean-environment-lock-invalid")
    result = {}
    for line in data.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = LOCK_LINE.fullmatch(line)
        if not match:
            raise EnvironmentFailure("clean-environment-lock-invalid")
        name, version, digest = match.groups()
        name = normalize_name(name)
        if name in result:
            raise EnvironmentFailure("clean-environment-lock-duplicate")
        result[name] = {"version": version, "sha256": digest}
    if result.keys() != EXPECTED_PACKAGES:
        raise EnvironmentFailure("clean-environment-lock-closure-invalid")
    if result["pip"] != {"version": "25.2", "sha256": PIP_SHA256}:
        raise EnvironmentFailure("clean-environment-bootstrap-binding-invalid")
    return result


def validate_requirements(path):
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    if lines != ["--require-hashes", "--only-binary=:all:", "-r requirements.lock"]:
        raise EnvironmentFailure("clean-environment-requirements-lock-mismatch")


def verify_wheel(payload, digest):
    if not payload or len(payload) > MAX_WHEEL_BYTES:
        raise EnvironmentFailure("clean-environment-wheel-size-invalid")
    if hashlib.sha256(payload).hexdigest() != digest:
        raise EnvironmentFailure("clean-environment-wheel-hash-mismatch")


def bootstrap_wheel(destination, wheelhouse=None):
    if wheelhouse is not None:
        try:
            with (wheelhouse / PIP_FILENAME).open("rb") as stream:
                payload = stream.read(MAX_WHEEL_BYTES + 1)
        except OSError:
            raise EnvironmentFailure("clean-environment-bootstrap-wheel-unavailable") from None
    else:
        try:
            with urllib.request.urlopen(PIP_URL, timeout=60) as response:
                payload = response.read(MAX_WHEEL_BYTES + 1)
        except OSError:
            raise EnvironmentFailure("clean-environment-bootstrap-download-failed") from None
    verify_wheel(payload, PIP_SHA256)
    path = destination / PIP_FILENAME
    path.write_bytes(payload)
    return path


def clean_child_environment(venv_bin, original):
    # No inherited installer/Python/npm switches can change isolation, target or command.
    result = {key: value for key, value in original.items()
              if not key.upper().startswith(("PIP_", "PYTHON", "NPM_CONFIG_", "BASH_FUNC_"))
              and key not in {"VIRTUAL_ENV", "CONDA_PREFIX", "NODE_OPTIONS", "NODE_PATH",
                             "BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS", "CDPATH", "GLOBIGNORE"}}
    result.update({
        "PATH": str(venv_bin) + os.pathsep + original.get("PATH", os.defpath),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    })
    return result


def install_command(python, bootstrap, lock, wheelhouse=None):
    command = [
        str(python), "-I", "-B", "-c",
        "import runpy,sys; sys.path.insert(0,sys.argv.pop(1)); "
        "runpy.run_module('pip',run_name='__main__')",
        str(bootstrap), "--isolated", "--disable-pip-version-check",
        "--no-cache-dir", "--require-virtualenv", "install",
        "--require-hashes", "--only-binary=:all:", "--no-compile",
        "--index-url", "https://pypi.org/simple", "-r", str(lock),
    ]
    if wheelhouse is not None:
        command.extend(["--no-index", "--find-links", str(wheelhouse)])
    return command


def verify_installed(lock, distributions, prefix, base_prefix):
    if Path(prefix).resolve() == Path(base_prefix).resolve():
        raise EnvironmentFailure("clean-environment-isolation-invalid")
    installed = {}
    for distribution in distributions:
        name = normalize_name(distribution.metadata["Name"])
        if name in installed:
            raise EnvironmentFailure("clean-environment-installed-duplicate")
        location = Path(distribution.locate_file("")).resolve()
        if not location.is_relative_to(Path(prefix).resolve()):
            raise EnvironmentFailure("clean-environment-isolation-invalid")
        installed[name] = distribution.version
    expected = {name: entry["version"] for name, entry in lock.items()}
    if installed != expected:
        raise EnvironmentFailure("clean-environment-installed-lock-mismatch")


def validate_npm_project(root):
    # Project npm configuration is outside this bounded clean-check contract.
    # Even a script-shell=/bin/true setting can otherwise skip all source checks.
    configuration = root / ".npmrc"
    if configuration.exists() or configuration.is_symlink():
        raise EnvironmentFailure("clean-environment-project-npm-config-unsupported")


def npm_check_command(root, temporary):
    validate_npm_project(root)
    # npm 9 rejects one file serving as both user and global config, including
    # /dev/null. Distinct empty files also make this deterministic on later npm.
    user_config = temporary / "npm-user.config"
    global_config = temporary / "npm-global.config"
    for configuration in (user_config, global_config):
        with configuration.open("x", encoding="utf-8"):
            pass
    return [
        "npm", "--script-shell=/bin/bash", "--ignore-scripts=false", "--if-present=false",
        "--workspaces=false", "--global=false", "--prefix=" + str(root),
        "--userconfig=" + str(user_config), "--globalconfig=" + str(global_config),
        "--cache=" + str(temporary / "npm-cache"), "run", "deployment:realization:check",
    ]


def run_validation(wheelhouse=None):
    validate_runtime(platform.python_implementation(), sys.version_info[:3],
                     platform.system(), platform.machine(), platform.libc_ver(),
                     bool(sysconfig.get_config_var("Py_GIL_DISABLED")))
    directory = Path(__file__).resolve().parent
    root = directory.parents[2]
    lock_path = directory / "requirements.lock"
    read_lock(lock_path)
    validate_requirements(directory / "requirements.txt")
    validate_npm_project(root)
    if wheelhouse is not None:
        wheelhouse = wheelhouse.resolve(strict=True)
        if not wheelhouse.is_dir():
            raise EnvironmentFailure("clean-environment-wheelhouse-invalid")
    if shutil.which("npm") is None:
        raise EnvironmentFailure("clean-environment-npm-unavailable")
    with tempfile.TemporaryDirectory(prefix="release-control-clean-") as temporary:
        temporary = Path(temporary)
        environment = temporary / "venv"
        venv.EnvBuilder(with_pip=False, system_site_packages=False).create(environment)
        python = environment / "bin" / "python3"
        child_env = clean_child_environment(environment / "bin", os.environ)
        bootstrap = bootstrap_wheel(temporary, wheelhouse)
        subprocess.run(install_command(python, bootstrap, lock_path, wheelhouse),
                       check=True, cwd=root, env=child_env)
        subprocess.run([str(python), "-I", "-B", str(Path(__file__).resolve()),
                        "--verify-installed"], check=True, cwd=root, env=child_env)
        subprocess.run([str(python), "-I", "-B", "-m", "pip", "--isolated", "--no-cache-dir", "check"],
                       check=True, cwd=root, env=child_env)
        print("Running canonical source validation in the locked environment.", flush=True)
        subprocess.run(npm_check_command(root, temporary),
                       check=True, cwd=root, env=child_env)
    print("Clean source validation passed. Release authorized: false.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--verify-installed", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.verify_installed:
            if args.wheelhouse is not None:
                raise EnvironmentFailure("clean-environment-arguments-invalid")
            lock = read_lock(Path(__file__).resolve().with_name("requirements.lock"))
            verify_installed(lock, importlib.metadata.distributions(), sys.prefix, sys.base_prefix)
            # Import the actual native/parser dependencies after exact location/version checks.
            __import__("yaml")
            __import__("jsonschema")
            __import__("rpds")
            print("Locked dependency installation verified; source checks have not run yet.")
        else:
            run_validation(args.wheelhouse)
    except EnvironmentFailure as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, ImportError, subprocess.CalledProcessError):
        print("clean-environment-verification-failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
