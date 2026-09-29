"""Export the verified image build as a source-free production payload."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.container-payload
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Export only verified image compiler outputs, generated shims, production dependencies and the public trust bundle.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.local-container
#     path: scripts/04.deploy/operational-realization-gate/local_container.py

from pathlib import Path
import re
import ssl
import tempfile

import local_build
import local_runtime as runtime
from local_build_sandbox import LocalBuildFailure, canonical, digest, source_manifest
import locked_toolchain as tools

CONFIGURATION = "platform/server/tsconfig.image.json"
OUTPUT_ROOT = ".cache/platform-shell-image-build"
CERTIFICATE_SOURCE = "platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt"
CERTIFICATE_TARGET = "assets/rds-eu-west-1-bundle.crt"


def fail(code):
    raise LocalBuildFailure("container-payload-" + code)


def checked_destination(destination, scratch, root):
    destination, scratch, root = Path(destination), Path(scratch).resolve(strict=True), Path(root).resolve(strict=True)
    if (not destination.is_absolute() or destination.exists() or destination.is_symlink()
            or destination.parent.resolve(strict=True) != destination.parent
            or not destination.is_relative_to(scratch) or destination == scratch
            or destination.is_relative_to(root)):
        fail("destination-invalid")
    return destination


def certificate(root):
    """Read the one public input omitted from the compiler's source suffixes."""
    raw = runtime.read_generator(root, CERTIFICATE_SOURCE)
    pattern = rb"(?:-----BEGIN CERTIFICATE-----\n[A-Za-z0-9+/=\n]+-----END CERTIFICATE-----\n?\s*)+"
    if not re.fullmatch(pattern, raw) or len(raw) > 64 * 1024:
        fail("certificate-invalid")
    for block in re.findall(rb"-----BEGIN CERTIFICATE-----\n.*?-----END CERTIFICATE-----", raw, re.S):
        try:
            ssl.PEM_cert_to_DER_cert(block.decode("ascii"))
        except (ValueError, UnicodeError):
            fail("certificate-invalid")
    return raw


def production_packages(lock_bytes, closure):
    """Use the reviewed flat lock's production flags, never npm prune hooks.

    All installed production packages are retained, matching the existing
    image's repository-wide npm --omit=dev scope. This is not application-level
    tree shaking. Missing required/optional locked edges fail closed; an absent
    explicitly optional peer is the only omitted edge accepted.
    """
    lock = tools._json(lock_bytes)
    if type(lock) is not dict or lock.get("lockfileVersion") != 3 or type(lock.get("packages")) is not dict:
        fail("lock-invalid")
    entries = lock["packages"]
    external = closure.get("external")
    if type(external) is not list or len({row["path"] for row in external}) != len(external):
        fail("closure-invalid")
    retained = []
    for row in external:
        entry = entries.get(row["path"])
        if (type(entry) is not dict or entry.get("version") != row["version"]
                or type(entry.get("dev", False)) is not bool
                or type(entry.get("devOptional", False)) is not bool
                or entry.get("devOptional") or entry.get("link")):
            fail("production-flags-unsupported")
        if not entry.get("dev", False):
            if row["name"] == "typescript" or row["name"].startswith("@types/"):
                fail("production-source-fallback")
            retained.append({key: row[key] for key in ("path", "name", "version")})
    paths = {row["path"] for row in retained}
    def check_edges(entry, available):
        for field in ("dependencies", "optionalDependencies", "peerDependencies"):
            dependencies = entry.get(field, {})
            if type(dependencies) is not dict:
                fail("production-closure-incomplete")
            for name in dependencies:
                target = "node_modules/" + name
                if target in available:
                    continue
                optional = entry.get("peerDependenciesMeta", {}).get(name, {}).get("optional") is True
                if field == "peerDependencies" and optional and target not in entries:
                    continue
                fail("production-closure-incomplete")
    for row in retained:
        check_edges(entries[row["path"]], paths)
    # Workspace production declarations are roots of npm --omit=dev. A
    # dependency accidentally marked dev cannot disappear merely because no
    # retained external package happens to reference it.
    workspace_links = {path for path, entry in entries.items()
                       if path.startswith("node_modules/") and entry.get("link") is True}
    for path, entry in entries.items():
        if not path.startswith("node_modules/"):
            check_edges(entry, paths | workspace_links)
    if not retained:
        fail("production-closure-empty")
    return sorted(retained, key=lambda row: row["path"])


def select_files(exported, result, production, certificate_bytes):
    """Bind every exported byte to the completed build before production trim."""
    if result.get("verdict") != "passed" or len(result.get("builds", [])) != 1:
        fail("build-failed")
    build = result["builds"][0]
    receipt = build.get("runtime")
    if (build.get("configuration") != CONFIGURATION or type(receipt) is not dict
            or receipt.get("kind") != "image-shim-generator" or receipt.get("returncode") != 0):
        fail("runtime-invalid")
    artifact = {path[len(OUTPUT_ROOT) + 1:]: raw for path, raw in exported.items()
                if path.startswith(OUTPUT_ROOT + "/")}
    dependencies = {path: raw for path, raw in exported.items() if path.startswith("node_modules/")}
    if (len(artifact) + len(dependencies) != len(exported)
            or runtime.fingerprint(artifact) != receipt.get("artifact_files")
            or runtime.file_set_digest(dependencies) != receipt.get("copied_dependency_digest")):
        fail("export-binding-invalid")
    if any(runtime.source_fallback(path) for path in exported):
        fail("source-fallback")
    production_paths = {row["path"] for row in production}
    kept = {path: raw for path, raw in dependencies.items()
            if any(path.startswith(package + "/") for package in production_paths)}
    for package in production_paths:
        if package + "/package.json" not in kept:
            fail("production-package-missing")
    files = {**{OUTPUT_ROOT + "/" + path: raw for path, raw in artifact.items()}, **kept,
             CERTIFICATE_TARGET: certificate_bytes}
    excluded = runtime.fingerprint({path: raw for path, raw in dependencies.items() if path not in kept})
    return files, runtime.file_set_digest(kept), excluded


def prepare(root, package_cache, scratch_root, destination):
    """Build offline, validate all bindings, then exclusively create payload.

    The caller owns this new disposable destination and the final container
    process. No cached receipt or arbitrary artifact tree is accepted as proof.
    """
    root, scratch_root = Path(root).resolve(strict=True), Path(scratch_root).resolve(strict=True)
    destination = checked_destination(destination, scratch_root, root)
    certificate_bytes = certificate(root)
    lock_bytes = tools._read(root / "package-lock.json")
    closure = tools.inspect_project(root)
    production = production_packages(lock_bytes, closure)
    with tempfile.TemporaryDirectory(prefix="release-control-image-payload-", dir=scratch_root) as temporary:
        exported_root = Path(temporary) / "verified"
        result = local_build.run(root, package_cache, (CONFIGURATION,), scratch_root,
                                 artifact_export=exported_root)
        if result.get("verdict") != "passed":
            fail("build-failed")
        exported = runtime.artifacts.artifact_files(exported_root)
        files, dependency_digest, excluded = select_files(exported, result, production, certificate_bytes)
        if (tools._read(root / "package-lock.json") != lock_bytes or certificate(root) != certificate_bytes
                or digest(canonical(source_manifest(root))) != result["source_digest"]
                or local_build.implementation_digest() != result["runner_digest"]):
            fail("source-changed")
        manifest = runtime.fingerprint(files)
        destination = checked_destination(destination, scratch_root, root)
        destination.mkdir()
        runtime.write_files(destination, files)
        if runtime.fingerprint(runtime.artifacts.artifact_files(destination)) != manifest:
            fail("copy-changed")
        return {"build_result": result, "files": manifest, "payload_digest": digest(canonical(manifest)),
                "production_dependencies": production, "production_dependency_digest": dependency_digest,
                "excluded_dependency_files": excluded,
                "certificate": {"source_path": CERTIFICATE_SOURCE, "path": CERTIFICATE_TARGET,
                                "digest": digest(certificate_bytes), "bytes": len(certificate_bytes)}}
