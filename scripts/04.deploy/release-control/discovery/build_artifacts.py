#!/usr/bin/env python3
"""Bind a local artifact tree to bounded source predictions without executing it.

This is byte and membership accounting, not compiler provenance. A caller must
freshly discover the build inventory; saved manifests are never trusted inputs.
"""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.build-artifacts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind source-derived output and shim candidates to safe local artifact bytes without execution or authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat

from source_inventory import SourceFailure, canonical, checked_document, digest

MAX_FILES = 5000
MAX_DEPTH = 40
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
PRIVATE = {".git", ".aws", ".ssh", ".codex", ".agents", ".npmrc", ".pypirc", ".env",
           "secrets", "secret", "credentials", "credential"}
GENERATORS = {
    "scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs",
    "platform/server/tests/run-runtime-tests.mjs",
    "products/kanbien-platform/tests/run-runtime-tests.mjs",
}
CONFIG_GENERATORS = {
    "platform/server/tsconfig.image.json": "scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs",
    "platform/server/tsconfig.runtime-test.json": "platform/server/tests/run-runtime-tests.mjs",
    "products/kanbien-platform/tsconfig.runtime-test.json": "products/kanbien-platform/tests/run-runtime-tests.mjs",
}
# The exact, locally audited writePackageShim + relativeRequirePath helper text,
# common to the three selected generators. A changed helper is unsupported until
# reviewed. This identifies grammar support, not trusted build execution.
SHIM_HELPER_DIGEST = "sha256:203ce572761ab3e734fc959d89cac360c12b05f769ef6286de489c9973c28f12"
SHIM_SCAFFOLD_DIGESTS = {
    "sha256:b9807120d13d85ac92e1d9cd85999664d1a40cdcc96c9e63e45e7ad7e3159a73",
    "sha256:58b15eb0528810c6a82abf8e976a450786cd978764af32f56f0a3a7406253be1",
    "sha256:4c04088bddc8bdbc95df674fa1dd019a1ebdd19585b3f675154caf8509f58149",
}
CORE_SPREAD = '...Object.fromEntries(coreModules.map((moduleName) => [`./${moduleName}`, join(runtimeRoot, `packages/core/src/${moduleName}/index.js`)]))'
RUNTIME_SELECTION = '''const testFiles = readdirSync(testDirectory)
  .filter((fileName) => fileName.endsWith("-runtime.test.js"))
  .sort();'''


def safe_path(value):
    return (type(value) is str and len(value) <= 512 and bool(re.fullmatch(r"[A-Za-z0-9_./@+-]+", value))
            and all(part not in ("", ".", "..") for part in value.split("/")))


def private_path(value):
    return any(part.lower() in PRIVATE or part.lower().startswith(".env.")
               or part.lower().endswith((".pem", ".key", ".env", ".p12", ".pfx"))
               for part in value.split("/"))


def checked_path(value):
    if not safe_path(value) or private_path(value):
        raise SourceFailure("artifact-path-unsafe")
    return value


def open_root(value):
    """Open absolute root components through descriptors, never resolving links."""
    path = Path(os.path.abspath(value))
    if private_path(path.as_posix()):
        raise SourceFailure("artifact-path-unsafe")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            next_descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                      dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        result, descriptor = descriptor, None
        return result
    finally:
        if descriptor is not None:
            os.close(descriptor)


def signature(info):
    return info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def read_file(parent, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise SourceFailure("artifact-file-kind-unsupported")
        if before.st_size > MAX_FILE_BYTES:
            raise SourceFailure("artifact-limit-exceeded")
        raw = stream.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise SourceFailure("artifact-limit-exceeded")
        if signature(before) != signature(os.fstat(stream.fileno())):
            raise SourceFailure("artifact-changed-during-read")
    return raw


def read_relative(root_fd, relative):
    checked_path(relative)
    descriptor = os.dup(root_fd)
    try:
        parts = relative.split("/")
        for part in parts[:-1]:
            next_descriptor = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                      dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return read_file(descriptor, parts[-1])
    finally:
        os.close(descriptor)


def artifact_files(root):
    """Inspect a bounded tree; a hard boundary rejects the whole collection."""
    files = {}
    total = 0
    visited = 0

    def walk(descriptor, prefix, depth):
        nonlocal total, visited
        if depth > MAX_DEPTH:
            raise SourceFailure("artifact-limit-exceeded")
        before = os.fstat(descriptor)
        names = os.listdir(descriptor)
        visited += len(names)
        if visited > MAX_FILES:
            raise SourceFailure("artifact-limit-exceeded")
        for name in sorted(names):
            path = checked_path(prefix + name)
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                dir_fd=descriptor)
                try:
                    walk(child, path + "/", depth + 1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                raw = read_file(descriptor, name)
                total += len(raw)
                if total > MAX_TOTAL_BYTES:
                    raise SourceFailure("artifact-limit-exceeded")
                files[path] = raw
            else:
                raise SourceFailure("artifact-file-kind-unsupported")
        if signature(before) != signature(os.fstat(descriptor)):
            raise SourceFailure("artifact-changed-during-read")

    descriptor = open_root(root)
    try:
        walk(descriptor, "", 0)
    finally:
        os.close(descriptor)
    return files


def checked_sources(root, inventory):
    """Catch source-byte changes between fresh discovery and artifact inspection.

    This does not recollect new include members; the public caller must perform
    fresh inventory discovery immediately before this internal API is invoked.
    """
    source_rows = inventory.get("sources")
    if type(source_rows) is not list or len(source_rows) > MAX_FILES:
        raise SourceFailure("artifact-inventory-invalid")
    descriptor = open_root(root)
    sources, contents = {}, {}
    total = 0
    try:
        for row in source_rows:
            if type(row) is not dict or set(row) != {"id", "path", "digest"}:
                raise SourceFailure("artifact-inventory-invalid")
            path = checked_path(row["path"])
            if row["id"] != digest(path.encode()) or row["id"] in sources:
                raise SourceFailure("artifact-inventory-invalid")
            raw = read_relative(descriptor, path)
            total += len(raw)
            if total > MAX_TOTAL_BYTES:
                raise SourceFailure("artifact-limit-exceeded")
            if digest(raw) != row["digest"]:
                raise SourceFailure("artifact-source-stale")
            sources[row["id"]] = row
            contents[path] = raw
    finally:
        os.close(descriptor)
    return sources, contents


def literal_generator(raw):
    """Extract supported source candidates, never evaluate JavaScript.

    Calls are required at the start of a line, unique and literal. The helper is
    pinned to the reviewed text. The surrounding program is still opaque; this
    deliberately does not assert that running it produces these candidates.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        raise SourceFailure("artifact-generator-unsupported") from None
    roots = re.findall(r'^const runtimeRoot = "([A-Za-z0-9_./-]+)";$', text, re.M)
    helpers = text.split("function writePackageShim(")
    if len(roots) != 1 or len(helpers) != 2 or digest(("function writePackageShim(" + helpers[1]).strip().encode()) != SHIM_HELPER_DIGEST:
        raise SourceFailure("artifact-generator-unsupported")
    output_root = checked_path(roots[0])
    before = helpers[0]
    arrays = re.findall(r"const coreModules = \[([^\]]*)\];", before)
    if len(arrays) != 1 or not re.fullmatch(r'(?:\s*"[a-z][a-z0-9-]*"\s*,)*\s*', arrays[0]):
        raise SourceFailure("artifact-generator-unsupported")
    core = re.findall(r'"([a-z][a-z0-9-]*)"', arrays[0])
    if len(core) != len(set(core)):
        raise SourceFailure("artifact-generator-unsupported")
    calls = list(re.finditer(r'^writePackageShim\("(@[a-z0-9-]+/[a-z0-9-]+)", \{\n(.*?)^\}\);$', before, re.M | re.S))
    if not calls or len(calls) != before.count("writePackageShim("):
        raise SourceFailure("artifact-generator-unsupported")
    scaffold = re.sub(r'^//[^\n]*\n|^#![^\n]*\n', '', before, flags=re.M)
    scaffold = re.sub(r'^const runtimeRoot = "[A-Za-z0-9_./-]+";$', 'const runtimeRoot = ROOT;', scaffold, flags=re.M)
    scaffold = re.sub(r'const coreModules = \[[^\]]*\];', 'const coreModules = CORE;', scaffold)
    scaffold = re.sub(r'^writePackageShim\("(@[a-z0-9-]+/[a-z0-9-]+)", \{\n(.*?)^\}\);\n', '', scaffold, flags=re.M | re.S)
    scaffold = re.sub(r'\n+', '\n', scaffold).strip()
    if digest(scaffold.encode()) not in SHIM_SCAFFOLD_DIGESTS:
        raise SourceFailure("artifact-generator-unsupported")
    packages, generated, targets = set(), {}, []
    for match in calls:
        package, body = match.groups()
        if package in packages:
            raise SourceFailure("artifact-generator-unsupported")
        packages.add(package)
        entries = []
        for line in body.splitlines():
            line = line.strip()
            if line == CORE_SPREAD + ",":
                entries.extend(("./" + name, "packages/core/src/" + name + "/index.js") for name in core)
                continue
            entry = re.fullmatch(r'"(\.|\./[a-z][a-z0-9/-]*)": join\(runtimeRoot, "([A-Za-z0-9_./-]+\.js)"\),', line)
            if not entry:
                raise SourceFailure("artifact-generator-unsupported")
            entries.append(entry.groups())
        if len(entries) != len({entry[0] for entry in entries}):
            raise SourceFailure("artifact-generator-unsupported")
        package_root = "node_modules/" + package
        manifest = package_root + "/package.json"
        exports = {}
        for key, target in entries:
            checked_path(target)
            shim = package_root + "/" + ("index.js" if key == "." else key[2:] + "/index.js")
            checked_path(shim)
            relative = posixpath.relpath(target, posixpath.dirname(shim))
            if not relative.startswith("."):
                relative = "./" + relative
            generated[shim] = ("module.exports = require(" + json.dumps(relative) + ");\n").encode()
            exports[key] = "./index.js" if key == "." else key + "/index.js"
            targets.append({"manifest_path": manifest, "shim_path": shim, "target_path": target})
        generated[manifest] = (json.dumps({"name": package, "type": "commonjs", "exports": exports}, indent=2) + "\n").encode()
    test_dir = None
    if "const testDirectory" in before:
        test_dirs = re.findall(r'^const testDirectory = join\(runtimeRoot, "([A-Za-z0-9_./-]+)"\);$', before, re.M)
        if len(test_dirs) != 1 or RUNTIME_SELECTION not in before:
            raise SourceFailure("artifact-generator-unsupported")
        test_dir = checked_path(test_dirs[0])
    return output_root, generated, targets, test_dir


def manifest_targets(path, raw, files):
    """Reject unsafe or missing manifest entry targets without resolving modules."""
    result = []
    try:
        document = checked_document(raw, json_only=True)
    except SourceFailure:
        return ["artifact-manifest-invalid"]
    if type(document) is not dict:
        return ["artifact-manifest-invalid"]

    def inspect(value):
        if type(value) is dict:
            for item in value.values():
                inspect(item)
        elif type(value) is str:
            if not value.startswith("./") or not safe_path(value[2:]) or private_path(value[2:]):
                result.append("artifact-manifest-target-unsafe")
                return
            target = posixpath.join(posixpath.dirname(path), value[2:])
            if target.endswith((".ts", ".tsx", ".mts", ".cts")):
                result.append("artifact-source-fallback-forbidden")
            elif target not in files:
                result.append("artifact-manifest-target-missing")
        else:
            result.append("artifact-manifest-target-unsupported")
    for name in ("main", "exports", "module", "browser", "imports", "bin"):
        if name in document:
            inspect(document[name])
    return result


def bind_artifact(root, build_inventory, build_id, artifact_root):
    """Bind current artifact bytes to fresh source predictions; never qualify."""
    try:
        return _bind_artifact(root, build_inventory, build_id, artifact_root)
    except SourceFailure:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SourceFailure("artifact-input-unreadable") from None


def _bind_artifact(root, inventory, build_id, artifact_root):
    if (type(inventory) is not dict or inventory.get("schema") != "source-build-inventory/v1"
            or digest(canonical({key: value for key, value in inventory.items() if key != "inventory_digest"})) != inventory.get("inventory_digest")):
        raise SourceFailure("artifact-inventory-invalid")
    builds = inventory.get("builds")
    if type(builds) is not list or len(builds) != len({row["id"] for row in builds}):
        raise SourceFailure("artifact-inventory-invalid")
    matches = [row for row in builds if row["id"] == build_id]
    if len(matches) != 1:
        raise SourceFailure("artifact-build-unknown")
    build = matches[0]
    if build["output_mode"] == "no-emit":
        raise SourceFailure("artifact-no-emit-build")
    if build["output_mode"] not in {"javascript", "declarations"} or build["prediction_status"] != "bounded":
        raise SourceFailure("artifact-prediction-unresolved")
    checked_path(build["output_root"])
    sources, contents = checked_sources(root, inventory)
    mappings, expected, runtime_candidates = [], set(), set()
    for row in build["expected_outputs"]:
        if type(row) is not dict or set(row) != {"path", "source_id", "kind"}:
            raise SourceFailure("artifact-inventory-invalid")
        path = checked_path(row["path"])
        if row["source_id"] not in sources or path in expected or row["kind"] not in {"javascript", "declaration", "runtime-test"}:
            raise SourceFailure("artifact-inventory-invalid")
        suffixes = (".d.ts", ".d.mts", ".d.cts") if row["kind"] == "declaration" else (".js", ".mjs", ".cjs")
        if not path.endswith(suffixes):
            raise SourceFailure("artifact-inventory-invalid")
        expected.add(path)
        mappings.append(dict(row))
        if row["kind"] == "runtime-test":
            runtime_candidates.add(path)
    if not expected:
        raise SourceFailure("artifact-prediction-empty")

    generated, shim_targets, generator_sources, test_dirs, findings = {}, [], [], set(), set()
    config_path = sources.get(build.get("config_source_id"), {}).get("path")
    required_generator = CONFIG_GENERATORS.get(config_path)
    if required_generator and required_generator not in contents:
        findings.add("artifact-generator-source-missing")
    for path in sorted(GENERATORS & contents.keys()):
        raw = contents[path]
        source = sources[digest(path.encode())]
        # Any occurrence of the selected declared output root makes the source
        # relevant. Unsupported syntax must not silently erase its obligations.
        if path != required_generator and build["output_root"].encode() not in raw:
            continue
        generator_sources.append(dict(source))
        try:
            output_root, files, targets, test_dir = literal_generator(raw)
            if output_root != build["output_root"]:
                raise SourceFailure("artifact-generator-unsupported")
            if set(generated) & set(files):
                raise SourceFailure("artifact-generator-unsupported")
            generated.update(files)
            shim_targets.extend({**row, "generator_source_id": source["id"]} for row in targets)
            if test_dir:
                test_dirs.add(test_dir)
        except SourceFailure:
            findings.add("artifact-generator-unsupported")
    if set(generated) & expected:
        findings.add("artifact-output-collision")
    actual = artifact_files(artifact_root)
    full_expected = expected | set(generated)
    if full_expected - actual.keys():
        findings.add("artifact-output-missing")
    if actual.keys() - full_expected:
        findings.add("artifact-output-unexpected")
    for path, raw in generated.items():
        if path in actual and actual[path] != raw:
            findings.add("artifact-generated-bytes-mismatch")
    for target in shim_targets:
        if target["target_path"] not in expected or target["target_path"] not in actual:
            findings.add("artifact-shim-target-missing")
    for path, raw in actual.items():
        if PurePosixPath(path).name == "package.json":
            findings.update(manifest_targets(path, raw, actual))
        if path.endswith((".ts", ".tsx", ".mts", ".cts")) and not path.endswith((".d.ts", ".d.mts", ".d.cts")):
            findings.add("artifact-source-fallback-forbidden")
    runtime_tests = sorted(path for path in actual if path.endswith("-runtime.test.js")
                           and posixpath.dirname(path) in test_dirs)
    expected_tests = sorted(path for path in runtime_candidates if posixpath.dirname(path) in test_dirs)
    if runtime_tests != expected_tests:
        findings.add("artifact-runtime-membership-mismatch")
    if test_dirs and not expected_tests:
        findings.add("artifact-runtime-tests-empty")
    # Recheck observed source bytes after collection. Neither this nor the tree
    # read supplies a filesystem-wide atomic snapshot or a build attestation.
    checked_sources(root, inventory)
    result = {"schema": "source-build-artifact/v1", "scope": "build-artifact-accounting",
              "authorized": False, "source_closure": "blocked", "provenance": "unproven",
              "qualification_verdict": "blocked", "artifact_verdict": "incomplete" if findings else "complete",
              "binder_revision": digest(Path(__file__).read_bytes()),
              "inventory_digest": inventory["inventory_digest"], "build_id": build_id,
              "files": [{"path": path, "digest": digest(raw), "bytes": len(raw)} for path, raw in sorted(actual.items())],
              "mappings": sorted(mappings, key=lambda row: row["path"]),
              "generator_sources": generator_sources, "shim_targets": sorted(shim_targets, key=lambda row: row["shim_path"]),
              "runtime_tests": runtime_tests, "findings": sorted(findings)}
    result["artifact_digest"] = digest(canonical(result))
    return result
