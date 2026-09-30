"""Isolate local build tooling from the owned checkout and external services."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.local-build-sandbox
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Execute bounded build tooling in disposable filesystem and network namespaces.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.local-build-runner
#     path: scripts/04.deploy/operational-realization-gate/local_build.py

import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import tempfile

CONFIGURATIONS = (
    "platform/server/tsconfig.check.json", "platform/server/tsconfig.json",
    "platform/server/tsconfig.runtime-test.json", "platform/server/tsconfig.image.json",
    "products/kanbien-platform/tsconfig.check.json", "products/kanbien-platform/tsconfig.json",
    "products/kanbien-platform/tsconfig.runtime-test.json",
)
SOURCE_ROOTS = ("apps", "packages", "platform", "products", "infra/04.deploy/03.product/entrypoints")
SOURCE_FILES = ("package.json", "package-lock.json",
                "scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs",
                "scripts/04.deploy/build-platform-shell-image/workspace-runtime.mjs")
SUFFIXES = {".ts", ".tsx", ".js", ".mjs", ".cjs", ".json"}
PRIVATE = {".git", ".aws", ".ssh", ".codex", ".agents", "secrets", "credentials"}
MAX_SOURCE_FILES, MAX_SOURCE_BYTES = 10000, 128 * 1024 * 1024
MAX_FILE_BYTES = 4 * 1024 * 1024
POLICY = {"filesystem": "disposable-selected-sources", "network": "private-loopback-only",
          "environment": "explicit-allowlist", "timeout_seconds": 180,
          "source_checkout": "not-mounted", "authority": "none"}


class LocalBuildFailure(Exception):
    """Only fixed safe error codes cross the execution boundary."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def safe_path(value):
    return (isinstance(value, str) and len(value) <= 512
            and re.fullmatch(r"[A-Za-z0-9_./@+-]+", value) is not None
            and all(part not in {"", ".", ".."} for part in value.split("/")))


def source_manifest(root, destination=None):
    """Copy bounded selected build inputs, never ambient caches or private files."""
    root = Path(root).resolve(strict=True)
    names = list(SOURCE_FILES)
    for base in SOURCE_ROOTS:
        start = root / base
        if not start.is_dir() or start.is_symlink():
            raise LocalBuildFailure("local-build-source-root-invalid")
        if destination is not None:
            (Path(destination) / base).mkdir(parents=True, exist_ok=True)
        for directory, dirs, files in os.walk(start, followlinks=False):
            relative = Path(directory).relative_to(root)
            if len(relative.parts) > 40:
                raise LocalBuildFailure("local-build-source-limit")
            for child in dirs + files:
                item = Path(directory) / child
                if item.is_symlink():
                    raise LocalBuildFailure("local-build-source-link")
            dirs[:] = sorted(name for name in dirs if name not in PRIVATE | {"node_modules", ".cache"}
                              and not name.startswith("."))
            for name in sorted(files):
                if name == ".npmrc":
                    raise LocalBuildFailure("local-build-npm-config-unsupported")
                if not name.startswith(".") and Path(name).suffix in SUFFIXES:
                    names.append((relative / name).as_posix())
    for configuration in (root / ".npmrc",):
        if configuration.exists() or configuration.is_symlink():
            raise LocalBuildFailure("local-build-npm-config-unsupported")
    rows, total = [], 0
    if len(names) > MAX_SOURCE_FILES or len(set(names)) != len(names):
        raise LocalBuildFailure("local-build-source-limit")
    for name in sorted(names):
        if not safe_path(name):
            raise LocalBuildFailure("local-build-source-path-invalid")
        path = root / name
        if any((root / Path(*Path(name).parts[:index])).is_symlink()
               for index in range(1, len(Path(name).parts) + 1)):
            raise LocalBuildFailure("local-build-source-link")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE_BYTES:
                raise LocalBuildFailure("local-build-source-file-invalid")
            data = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
        if len(data) > MAX_FILE_BYTES or (before.st_size, before.st_mtime_ns, before.st_ino) != (
                after.st_size, after.st_mtime_ns, after.st_ino):
            raise LocalBuildFailure("local-build-source-changed")
        total += len(data)
        if total > MAX_SOURCE_BYTES:
            raise LocalBuildFailure("local-build-source-limit")
        rows.append({"path": name, "digest": digest(data), "bytes": len(data)})
        if destination is not None:
            output = Path(destination) / name
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(data)
    return rows


def _limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (150, 150))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024, 32 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))


class Sandbox:
    def __init__(self, toolchain, packages, evidence=None, writable=None):
        self.toolchain = Path(toolchain).resolve(strict=True)
        self.packages = Path(packages).resolve(strict=True)
        self.evidence = Path(evidence).resolve(strict=True) if evidence else None
        self.writable = writable

    def command(self, argv, cwd, env):
        cwd = Path(cwd).resolve(strict=True)
        runner = Path(__file__).resolve().parent
        translations = [(str(cwd), "/work"), (str(self.toolchain), "/toolchain"),
                        (str(self.packages), "/packages"), (str(runner), "/runner")]
        if self.evidence:
            translations.append((str(self.evidence), "/evidence"))
        translations.sort(key=lambda item: len(item[0]), reverse=True)

        def translate(value):
            for old, new in translations:
                value = value.replace(old, new)
            return value

        command = ["/usr/bin/bwrap", "--unshare-user", "--unshare-pid", "--unshare-net",
                   "--unshare-ipc", "--unshare-uts", "--die-with-parent", "--new-session",
                   "--cap-drop", "ALL", "--disable-userns"]
        for system in ("/usr", "/lib", "/lib64"):
            if Path(system).exists():
                command.extend(["--ro-bind", system, system])
        command.extend(["--symlink", "usr/bin", "/bin", "--symlink", "usr/sbin", "/sbin",
                        "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                        "--ro-bind", str(self.toolchain), "/toolchain",
                        "--ro-bind", str(self.packages), "/packages",
                        "--dir", "/runner", "--ro-bind", str(runner / "typescript_observer.mjs"),
                        "/runner/typescript_observer.mjs",
                        "--bind" if self.writable is None else "--ro-bind", str(cwd), "/work"])
        for relative in self.writable or ():
            if not safe_path(relative) or not relative.startswith(".cache/") and relative != ".cache":
                raise LocalBuildFailure("local-build-write-boundary-invalid")
            output = cwd / relative
            output.mkdir(parents=True, exist_ok=True)
            if output.resolve() != output:
                raise LocalBuildFailure("local-build-write-boundary-invalid")
            command.extend(["--bind", str(output), "/work/" + relative])
        if self.evidence:
            command.extend(["--bind", str(self.evidence), "/evidence"])
        clean = {"PATH": "/toolchain/bin:/usr/bin", "HOME": "/tmp/home", "TMPDIR": "/tmp",
                 "LANG": "C.UTF-8", "TZ": "UTC"}
        # The caller supplies installer-specific configuration, never inherited values.
        allowed = {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ", "CI", "NO_COLOR"}
        for key, value in env.items():
            if key not in allowed and not key.lower().startswith("npm_config_"):
                raise LocalBuildFailure("local-build-environment-unsupported")
            if not isinstance(value, str) or "\x00" in value or "\n" in value:
                raise LocalBuildFailure("local-build-environment-invalid")
            clean[key] = translate(value)
        command.append("--clearenv")
        for key, value in sorted(clean.items()):
            command.extend(["--setenv", key, value])
        command.extend(["--chdir", "/work", "--"] + [translate(str(item)) for item in argv])
        return command

    def __call__(self, argv, cwd, env):
        command = self.command(argv, cwd, env)
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            child = subprocess.Popen(command, env={"PATH": "/usr/bin:/bin"}, stdin=subprocess.DEVNULL,
                                     stdout=stdout, stderr=stderr, start_new_session=True, preexec_fn=_limits)
            try:
                child.wait(timeout=POLICY["timeout_seconds"])
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise LocalBuildFailure("local-build-timeout") from None
            stdout.seek(0)
            stderr.seek(0)
            out, err = stdout.read(8 * 1024 * 1024 + 1), stderr.read(8 * 1024 * 1024 + 1)
            if max(len(out), len(err)) > 8 * 1024 * 1024:
                raise LocalBuildFailure("local-build-output-limit")
            return {"returncode": child.returncode, "stdout": out, "stderr": err}
