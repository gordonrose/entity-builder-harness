#!/usr/bin/env python3
"""Observe selected runtime commands inside a caller-supplied isolated executor.

The public locked-build runner owns toolchain verification and filesystem/network
isolation. This internal helper has no process-launch capability of its own.
"""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-local-runtime
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Observe selected runtime runners against copied compiler outputs without repository source fallback.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "release-control/discovery"))
import build_artifacts as artifacts
import package_exports
from source_inventory import SourceFailure, canonical, checked_document, digest

CONFIGURATIONS = {
    "platform/server/tsconfig.runtime-test.json": (".cache/platform-server-runtime", "runtime-test-runner"),
    "products/kanbien-platform/tsconfig.runtime-test.json": (".cache/product-kanbien-platform-runtime", "runtime-test-runner"),
    "platform/server/tsconfig.image.json": (".cache/platform-shell-image-build", "image-shim-generator"),
}
MAX_DEPENDENCY_FILES = 30000
MAX_DEPENDENCY_BYTES = 256 * 1024 * 1024
MAX_DEPENDENCY_FILE_BYTES = 16 * 1024 * 1024
MAX_COMMAND_OUTPUT_BYTES = 1024 * 1024


def fingerprint(files):
    return [{"path": path, "digest": digest(raw), "bytes": len(raw)} for path, raw in sorted(files.items())]


def file_set_digest(files):
    return digest(canonical(fingerprint(files)))


def source_fallback(path):
    return path.endswith((".ts", ".tsx", ".mts", ".cts"))


def read_generator(source_root, path):
    fd = artifacts.open_root(source_root)
    try:
        return artifacts.read_relative(fd, path)
    finally:
        os.close(fd)


def dependency_files(closure):
    """Read only declared external package regular files, without following links.

    The parent verifies the complete installed lock closure. Regular file
    declarations additionally bind this copy to that exact
    verified tree; workspace links and package-manager .bin links are not copied.
    """
    packages = closure.get("external_modules")
    if type(packages) is not list or len(packages) > MAX_DEPENDENCY_FILES:
        raise SourceFailure("local-runtime-dependencies-invalid")
    workspaces = closure.get("workspace_links", [])
    if type(workspaces) is not list or any(type(path) is not str for path in workspaces):
        raise SourceFailure("local-runtime-dependencies-invalid")
    paths = []
    for package in packages:
        if type(package) is not dict or not {"path", "name", "version"} <= package.keys():
            raise SourceFailure("local-runtime-dependencies-invalid")
        path = package["path"]
        if not artifacts.safe_path(path) or not path.startswith("node_modules/") or artifacts.private_path(path):
            raise SourceFailure("local-runtime-dependencies-invalid")
        if path in paths or any(path == link or path.startswith(link + "/") for link in workspaces):
            raise SourceFailure("local-runtime-dependencies-invalid")
        paths.append(path)
    result = {}
    total = 0
    visited = 0

    def walk(descriptor, prefix, depth=0):
        nonlocal total, visited
        if depth > 40:
            raise SourceFailure("local-runtime-dependency-limit")
        before = os.fstat(descriptor)
        names = os.listdir(descriptor)
        visited += len(names)
        if visited > MAX_DEPENDENCY_FILES:
            raise SourceFailure("local-runtime-dependency-limit")
        for name in sorted(names):
            path = prefix + "/" + name
            artifacts.checked_path(path)
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
                try:
                    walk(child, path, depth + 1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                if source_fallback(path):
                    continue
                if info.st_size > MAX_DEPENDENCY_FILE_BYTES:
                    raise SourceFailure("local-runtime-dependency-limit")
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
                with os.fdopen(fd, "rb") as stream:
                    opened = os.fstat(stream.fileno())
                    if not stat.S_ISREG(opened.st_mode):
                        raise SourceFailure("local-runtime-dependency-kind")
                    raw = stream.read(MAX_DEPENDENCY_FILE_BYTES + 1)
                    if len(raw) > MAX_DEPENDENCY_FILE_BYTES or signature(opened) != signature(os.fstat(stream.fileno())):
                        raise SourceFailure("local-runtime-dependency-changed")
                total += len(raw)
                if total > MAX_DEPENDENCY_BYTES:
                    raise SourceFailure("local-runtime-dependency-limit")
                if path in result and result[path] != raw:
                    raise SourceFailure("local-runtime-dependency-changed")
                result[path] = raw
            else:
                raise SourceFailure("local-runtime-dependency-kind")
        if signature(before) != signature(os.fstat(descriptor)):
            raise SourceFailure("local-runtime-dependency-changed")

    root_fd = artifacts.open_root(closure["external_modules_root"])
    try:
        for path in sorted(paths):
            # TypeScript and type-only packages cannot be runtime dependencies of
            # the selected compiled payload. Omit their sources and executables.
            relative = path[len("node_modules/"):]
            if relative == "typescript" or relative.startswith("@types/"):
                continue
            descriptor = os.dup(root_fd)
            try:
                for part in relative.split("/"):
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
                    os.close(descriptor)
                    descriptor = child
                walk(descriptor, path)
            finally:
                os.close(descriptor)
    finally:
        os.close(root_fd)
    declared = closure.get("external_files")
    if type(declared) is not list or len(declared) > MAX_DEPENDENCY_FILES:
        raise SourceFailure("local-runtime-dependencies-invalid")
    for row in declared:
        if (type(row) is not dict or set(row) != {"path", "digest", "bytes"}
                or not artifacts.safe_path(row["path"]) or not row["path"].startswith("node_modules/")
                or type(row["digest"]) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", row["digest"])
                or type(row["bytes"]) is not int or row["bytes"] < 0):
            raise SourceFailure("local-runtime-dependencies-invalid")
    if digest(canonical(sorted(declared, key=lambda row: row["path"]))) != closure["external_modules_digest"]:
        raise SourceFailure("local-runtime-dependency-stale")
    indexed = {row["path"]: row for row in declared}
    runtime_packages = [path for path in paths if path != "node_modules/typescript" and not path.startswith("node_modules/@types/")]
    expected_paths = {path for path in indexed if not source_fallback(path)
                      and any(path.startswith(package + "/") for package in runtime_packages)}
    if (len(indexed) != len(declared) or set(result) != expected_paths
            or any(indexed.get(row["path"]) != row for row in fingerprint(result))):
        raise SourceFailure("local-runtime-dependency-stale")
    return result


def tree_members(root):
    """Check the whole disposable tree, including unexpected files outside output."""
    found = set()
    visited = 0

    def walk(descriptor, prefix, depth):
        nonlocal visited
        if depth > 40:
            raise SourceFailure("local-runtime-dependency-limit")
        for name in os.listdir(descriptor):
            visited += 1
            if visited > MAX_DEPENDENCY_FILES:
                raise SourceFailure("local-runtime-dependency-limit")
            path = artifacts.checked_path(prefix + name)
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
                try:
                    walk(child, path + "/", depth + 1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                found.add(path)
            else:
                raise SourceFailure("local-runtime-dependency-kind")

    descriptor = artifacts.open_root(root)
    try:
        walk(descriptor, "", 0)
    finally:
        os.close(descriptor)
    return found


def external_source_fallback(raw):
    document = checked_document(raw, json_only=True)
    if type(document) is not dict:
        raise SourceFailure("local-runtime-dependencies-invalid")

    def visit(value):
        if type(value) is str:
            return source_fallback(value)
        if type(value) is list:
            return any(visit(item) for item in value)
        if type(value) is dict:
            return any(visit(item) for key, item in value.items() if key not in {"types", "typings"})
        return False

    return any(visit(document.get(name)) for name in ("main", "exports", "imports"))


def signature(info):
    return info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def write_files(root, files):
    for path, raw in sorted(files.items()):
        artifacts.checked_path(path)
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)


def run_runtime(configuration, compiled_root, closure, execute, export_root=None):
    """Return a successful local observation or raise a fixed safe diagnostic.

    ``execute(argv, cwd, env)`` must enforce a source-free filesystem namespace,
    no network, a timeout, pinned Node and bounded output. It returns returncode,
    stdout bytes and stderr bytes. No caller-provided program name is accepted.
    """
    try:
        return _run_runtime(configuration, Path(compiled_root), closure, execute, export_root)
    except SourceFailure:
        raise
    except TimeoutError:
        raise SourceFailure("local-runtime-timeout") from None
    except Exception:
        raise SourceFailure("local-runtime-input-invalid") from None


def _run_runtime(configuration, compiled_root, closure, execute, export_root=None):
    if configuration not in CONFIGURATIONS:
        raise SourceFailure("local-runtime-configuration-unsupported")
    if export_root is not None:
        export_root = Path(export_root)
        if (configuration != "platform/server/tsconfig.image.json"
                or not export_root.is_absolute() or export_root.exists() or export_root.is_symlink()
                or export_root.parent.resolve(strict=True) != export_root.parent
                or export_root.is_relative_to(compiled_root.resolve())
                or export_root.is_relative_to(Path(closure["source_root"]).resolve())):
            raise SourceFailure("local-runtime-export-invalid")
    if type(closure) is not dict:
        raise SourceFailure("local-runtime-closure-invalid")
    for name in ("source_inventory_digest", "external_modules_digest"):
        if type(closure.get(name)) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", closure[name]):
            raise SourceFailure("local-runtime-closure-invalid")
    node = closure.get("node_path")
    if type(node) is not str or not Path(node).is_absolute() or Path(node).name != "node":
        raise SourceFailure("local-runtime-toolchain-invalid")
    output_root, kind = CONFIGURATIONS[configuration]
    generator_path = artifacts.CONFIG_GENERATORS[configuration]
    raw = read_generator(closure["source_root"], generator_path)
    maintained_root = Path(__file__).resolve().parents[3]
    if raw != read_generator(maintained_root, generator_path):
        raise SourceFailure("local-runtime-generator-unsupported")
    helper_path = package_exports.SHARED_HELPER
    helper_raw = read_generator(closure["source_root"], helper_path)
    if helper_raw != read_generator(maintained_root, helper_path):
        raise SourceFailure("local-runtime-helper-unsupported")
    observed = closure.get("compiler_observation")
    if not isinstance(observed, dict) or observed.get("output_mode") != "fresh-exclusive":
        raise SourceFailure("local-runtime-emission-required")
    projection, export_receipt = package_exports.prepare_projection(closure["source_root"], observed, compiled_root)
    if projection["configuration"] != configuration or projection["output_root"] != output_root:
        raise SourceFailure("local-runtime-projection-binding-invalid")
    generated = package_exports.generated_files(projection)
    test_dir = {"platform/server/tsconfig.runtime-test.json": "platform/server/tests",
                "products/kanbien-platform/tsconfig.runtime-test.json": "products/kanbien-platform/tests"}.get(configuration)
    projection_raw = canonical(projection) + b"\n"
    driver_raw = package_exports.driver_bytes(configuration)
    compiled = artifacts.artifact_files(compiled_root / output_root)
    if not compiled or any(source_fallback(path) or path.startswith("node_modules/") for path in compiled):
        raise SourceFailure("local-runtime-source-fallback")
    if set(compiled) & generated.keys() or any(row["output_path"] not in compiled for row in projection["entries"]):
        raise SourceFailure("local-runtime-shim-target-missing")
    selected = sorted(path for path in compiled if path.endswith("-runtime.test.js")
                      and str(Path(path).parent) == test_dir)
    if kind == "runtime-test-runner" and not selected:
        raise SourceFailure("local-runtime-tests-empty")
    dependencies = dependency_files(closure)
    # A package declaring an executable TypeScript entry would be a hidden
    # source fallback even after its .ts file was omitted from the copy.
    for path, content in dependencies.items():
        if path.endswith("/package.json"):
            if external_source_fallback(content):
                raise SourceFailure("local-runtime-source-fallback")
    with tempfile.TemporaryDirectory(prefix="release-control-runtime-") as temporary:
        runtime_root = Path(temporary)
        artifact_inputs = {output_root + "/" + path: content for path, content in compiled.items()}
        files = {**artifact_inputs, **dependencies, generator_path: raw, helper_path: helper_raw,
                 package_exports.PROJECTION_INPUT: projection_raw, package_exports.RUNTIME_DRIVER: driver_raw}
        if len(files) != len(artifact_inputs) + len(dependencies) + 4:
            raise SourceFailure("local-runtime-input-collision")
        write_files(runtime_root, files)
        # Keep a directory for an empty closure so post-execution checks need no
        # special source dependency fallback.
        (runtime_root / "node_modules").mkdir(exist_ok=True)
        environment = {"PATH": str(Path(node).parent), "HOME": str(runtime_root), "LANG": "C.UTF-8", "TZ": "UTC"}
        try:
            execution = execute([node, package_exports.RUNTIME_DRIVER], runtime_root, environment)
        except TimeoutError:
            raise SourceFailure("local-runtime-timeout") from None
        except Exception:
            raise SourceFailure("local-runtime-execution-failed") from None
        if (type(execution) is not dict or set(execution) != {"returncode", "stdout", "stderr"}
                or type(execution["returncode"]) is not int
                or type(execution["stdout"]) is not bytes or type(execution["stderr"]) is not bytes):
            raise SourceFailure("local-runtime-executor-result-invalid")
        if execution["returncode"] != 0:
            raise SourceFailure("local-runtime-command-failed")
        if len(execution["stdout"]) + len(execution["stderr"]) > MAX_COMMAND_OUTPUT_BYTES:
            raise SourceFailure("local-runtime-output-limit")
        actual = artifacts.artifact_files(runtime_root / output_root)
        expected = {**compiled, **generated}
        if actual != expected:
            raise SourceFailure("local-runtime-artifact-changed")
        if tree_members(runtime_root) != set(files) | {output_root + "/" + path for path in generated}:
            raise SourceFailure("local-runtime-unexpected-file")
        if (read_generator(runtime_root, helper_path) != helper_raw
                or read_generator(closure["source_root"], helper_path) != helper_raw
                or read_generator(runtime_root, package_exports.PROJECTION_INPUT) != projection_raw
                or read_generator(runtime_root, package_exports.RUNTIME_DRIVER) != driver_raw):
            raise SourceFailure("local-runtime-generator-changed")
        if read_generator(runtime_root, generator_path) != raw:
            raise SourceFailure("local-runtime-generator-changed")
        copied_closure = {**closure, "external_modules_root": runtime_root / "node_modules"}
        if dependency_files(copied_closure) != dependencies:
            raise SourceFailure("local-runtime-dependency-changed")
        if read_generator(closure["source_root"], generator_path) != raw:
            raise SourceFailure("local-runtime-source-changed")
        if artifacts.artifact_files(compiled_root / output_root) != compiled:
            raise SourceFailure("local-runtime-compiler-artifact-changed")
        if dependency_files(closure) != dependencies:
            raise SourceFailure("local-runtime-dependency-changed")
        result = {"schema": "local-workspace-runtime-observation/v1", "scope": "isolated-local-runtime",
                  "configuration": configuration, "kind": kind, "authorized": False,
                  "qualification_verdict": "blocked", "source_inventory_digest": closure["source_inventory_digest"],
                  "generator": {"path": generator_path, "digest": digest(raw)},
                  "generator_helpers": [{"path": helper_path, "digest": digest(helper_raw)}],
                  "projection_input_digest": digest(projection_raw), "execution_driver_digest": digest(driver_raw),
                  "workspace_exports": export_receipt,
                  "compiler_artifact_digest": file_set_digest(compiled),
                  "dependency_tree_digest": closure["external_modules_digest"],
                  "copied_dependency_digest": file_set_digest(dependencies),
                  "artifact_files": fingerprint(actual), "selected_runtime_tests": selected,
                  "executed_runner_count": 1 if kind == "runtime-test-runner" else 0,
                  "returncode": 0, "stdout_digest": digest(execution["stdout"]), "stderr_digest": digest(execution["stderr"])}
        result["receipt_digest"] = digest(canonical(result))
        package_exports.check_runtime(result)
        if export_root is not None:
            # Export only post-checked runtime bytes, never the generator or
            # repository sources. The parent withholds public export until its
            # source, dependency, schema and result checks have also passed.
            export_root.mkdir()
            write_files(export_root, {**dependencies, **{output_root + "/" + path: content
                                                       for path, content in actual.items()}})
        return result
