"""Run the selected real builds using locked tools in disposable OS namespaces."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.local-build-runner
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind actual compiler and selected runtime results to verified source and dependency bytes.
#   portability: {class: internal, targets: []}
#   effects: [writes-files, network]
#   used_by:
#   - id: deploy.command.verify-local-build
#     path: scripts/04.deploy/operational-realization-gate/verify-local-build.sh

import json
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
sys.path.insert(0, str(DIRECTORY.parent / "release-control/discovery"))

import build_contracts
from build_inventory import discover_builds
import local_build_contracts as contracts
from local_build_sandbox import CONFIGURATIONS, LocalBuildFailure, POLICY, Sandbox, canonical, digest, source_manifest
import locked_toolchain as tools
import release_compiler as release

WORKFLOW = ".github/workflows/deploy-platform-shell-staging.yml"
RUNTIME_CONFIGS = {"platform/server/tsconfig.runtime-test.json", "platform/server/tsconfig.image.json",
                   "products/kanbien-platform/tsconfig.runtime-test.json"}


def unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise LocalBuildFailure("local-build-observation-duplicate-key")
        result[key] = value
    return result


def implementation_digest():
    names = ("local_build.py", "local_build_sandbox.py", "local_build_contracts.py",
             "locked_toolchain.py", "typescript_observer.mjs", "local_runtime.py", "node-toolchain.lock.json",
             "build_contracts.py", "release_compiler.py")
    rows = [{"path": name, "digest": digest((DIRECTORY / name).read_bytes())} for name in names]
    for path in sorted(release.SCHEMA_DIR.glob("local-*.schema.yml")):
        rows.append({"path": path.name, "digest": digest(path.read_bytes())})
    for name in ("build_inventory.py", "build_artifacts.py", "source_inventory.py", "caller_inventory.py",
                 "operation_inventory.py", "cloudformation_inventory.py"):
        rows.append({"path": name, "digest": digest((DIRECTORY.parent / "release-control/discovery" / name).read_bytes())})
    return digest(canonical(rows))


def dependency_manifest(root, packages):
    rows = []
    for entry in packages:
        for relative, expected in entry["files"].items():
            path = entry["path"] + "/" + relative
            data = tools._read(Path(root) / path, tools.MAX_PACKAGE)
            if digest(data) != "sha256:" + expected:
                raise LocalBuildFailure("local-build-dependency-changed")
            rows.append({"path": path, "digest": digest(data), "bytes": len(data)})
    return sorted(rows, key=lambda row: row["path"])


def check_observed_files(work, observed, manifest):
    known = {row["path"]: row for row in manifest}
    for row in observed["inputs"]:
        expected = known.get(row["path"])
        if expected is None or expected["digest"] != row["digest"] or expected["bytes"] != row["bytes"]:
            raise LocalBuildFailure("local-build-input-binding-invalid")
    for row in observed["outputs"]:
        data = tools._read(Path(work) / row["path"], tools.MAX_PACKAGE)
        if digest(data) != row["digest"] or len(data) != row["bytes"]:
            raise LocalBuildFailure("local-build-output-changed")
    actual = set()
    cache = Path(work) / ".cache"
    if cache.exists():
        for directory, dirs, files in os.walk(cache, followlinks=False):
            for name in dirs + files:
                path = Path(directory) / name
                if path.is_symlink():
                    raise LocalBuildFailure("local-build-output-link")
            actual.update((Path(directory) / name).relative_to(work).as_posix() for name in files)
    if actual != {row["path"] for row in observed["outputs"]}:
        raise LocalBuildFailure("local-build-output-membership-invalid")


def run(root, package_cache, selected=CONFIGURATIONS, scratch_root=None, artifact_export=None):
    root, package_cache = Path(root).resolve(strict=True), Path(package_cache).resolve(strict=True)
    if scratch_root is None:
        raise LocalBuildFailure("local-build-scratch-required")
    scratch_root = Path(scratch_root).resolve(strict=True)
    if not scratch_root.is_dir() or scratch_root == root or scratch_root.is_relative_to(root):
        raise LocalBuildFailure("local-build-scratch-invalid")
    # Select the most specific host mount; refuse memory-backed build storage.
    mounts = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, right = line.split(" - ", 1)
        mount = Path(left.split()[4].replace("\\040", " ").replace("\\134", "\\"))
        if scratch_root.is_relative_to(mount):
            mounts.append((len(mount.parts), right.split()[0]))
    if not mounts or max(mounts)[1] in {"tmpfs", "ramfs"}:
        raise LocalBuildFailure("local-build-scratch-memory-backed")
    if artifact_export is not None:
        artifact_export = Path(artifact_export)
        if (tuple(selected) != ("platform/server/tsconfig.image.json",)
                or not artifact_export.is_absolute() or artifact_export.exists() or artifact_export.is_symlink()
                or artifact_export.parent.resolve(strict=True) != artifact_export.parent
                or not artifact_export.is_relative_to(scratch_root)
                or artifact_export == scratch_root):
            raise LocalBuildFailure("local-build-export-invalid")
    # Runtime helpers use the same explicitly selected persistent scratch root.
    tempfile.tempdir = str(scratch_root)
    if not selected or any(value not in CONFIGURATIONS for value in selected) or len(set(selected)) != len(selected):
        raise LocalBuildFailure("local-build-configuration-unsupported")
    revision = implementation_digest()
    inventory = build_contracts.checked_inventory(discover_builds(root, WORKFLOW))
    sources = {row["id"]: row["path"] for row in inventory["sources"]}
    builds = {sources[row["config_source_id"]]: row for row in inventory["builds"]}
    if len(builds) != len(inventory["builds"]) or set(builds) != set(CONFIGURATIONS):
        raise LocalBuildFailure("local-build-selected-graph-changed")
    with tempfile.TemporaryDirectory(prefix="release-control-real-build-") as temporary:
        base = Path(temporary)
        master = base / "source"
        master.mkdir()
        manifest = source_manifest(root, master)
        if source_manifest(root) != manifest:
            raise LocalBuildFailure("local-build-source-changed")
        contract = tools.load_toolchain()
        closure = tools.inspect_project(master, contract)
        toolchain = tools.prepare_toolchain(package_cache, base / "tools", contract)
        packages = tools.verify_package_cache(package_cache, closure)
        evidence = base / "evidence"
        evidence.mkdir()
        executor = Sandbox(toolchain["bundle_root"], package_cache, evidence)
        # A failing isolation probe is a hard failure. There is no host fallback.
        if executor(["/usr/bin/true"], master, {})["returncode"] != 0:
            raise LocalBuildFailure("local-build-isolation-unavailable")
        tools.install_dependencies(master, toolchain, package_cache, closure, executor)
        executor = Sandbox(toolchain["bundle_root"], package_cache, evidence, writable=[".cache"])
        external = dependency_manifest(master, packages)
        dependency_digest = digest(canonical(external))
        result = {"schema": "local-build-result/v1", "scope": "locked-local-build", "authorized": False,
                  "release_eligibility": "blocked", "operation_authorization": "blocked",
                  "qualification_verdict": "blocked", "source_closure": "blocked", "verdict": "passed",
                  "source_digest": digest(canonical(manifest)), "build_inventory_digest": inventory["inventory_digest"],
                  "graph_digest": inventory["graph_digest"], "runner_digest": revision,
                  "toolchain": {"contract_digest": toolchain["contract_digest"], "node_version": "22.23.3",
                                "npm_version": "10.9.9", "typescript_version": "5.9.3",
                                "lock_digest": "sha256:" + closure["lock_sha256"], "dependency_digest": dependency_digest},
                  "sandbox": POLICY, "builds": [], "findings": []}
        for index, configuration in enumerate(selected):
            work = base / ("build-" + str(index))
            shutil.copytree(master, work, symlinks=True, ignore=shutil.ignore_patterns(".release-control-toolchain"))
            output = evidence / (str(index) + ".json")
            response = executor([toolchain["node"], "--max-old-space-size=512",
                                 str(DIRECTORY / "typescript_observer.mjs"), "--root", str(work),
                                 "--config", configuration, "--output", str(output)], work, {})
            observed = json.loads(tools._read(output, 16 * 1024 * 1024),
                                  object_pairs_hook=unique_pairs)
            contracts.observation(observed)
            if (response["returncode"] == 0) != (observed["verdict"] == "passed"):
                raise LocalBuildFailure("local-build-exit-observation-mismatch")
            check_observed_files(work, observed, manifest + external)
            if source_manifest(work) != manifest:
                raise LocalBuildFailure("local-build-source-changed")
            tools.verify_installed(work, closure, packages)
            runtime = None
            if observed["verdict"] == "passed" and configuration in RUNTIME_CONFIGS:
                from local_runtime import run_runtime
                runtime_closure = {"source_root": master, "node_path": toolchain["node"],
                                   "external_modules_root": work / "node_modules",
                                   "external_modules": closure["external"],
                                   "workspace_links": [row["path"] for row in closure["links"]],
                                   "external_files": external, "external_modules_digest": dependency_digest,
                                   "source_inventory_digest": inventory["inventory_digest"]}
                try:
                    runtime_executor = Sandbox(toolchain["bundle_root"], package_cache,
                                               writable=[builds[configuration]["output_root"] + "/node_modules"])
                    runtime = run_runtime(configuration, work, runtime_closure, runtime_executor,
                                          export_root=base / "verified-runtime" if artifact_export else None)
                    contracts.runtime_source_binding(runtime, manifest)
                except Exception as error:
                    runtime = None
                    reason = getattr(error, "code", str(error))
                    code = "local-build-" + reason if re.fullmatch(r"local-runtime-[a-z-]+", reason) else "local-build-runtime-failed"
                    result["findings"].append({"code": "local-build-runtime-failed"})
                    result["findings"].append({"code": code})
                check_observed_files(work, observed, manifest + external)
                tools.verify_installed(work, closure, packages)
            if observed["verdict"] != "passed":
                result["findings"].append({"code": "local-build-compiler-failed"})
            build = builds[configuration]
            expected = {build["output_root"].rstrip("/") + "/" + row["path"]
                        for row in build["expected_outputs"]} if build["output_root"] else set()
            actual = {row["path"] for row in observed["outputs"]}
            result["builds"].append({"build_id": build["id"], "configuration": configuration,
                                     "observation": observed, "runtime": runtime,
                                     "prediction_status": build["prediction_status"],
                                     "unpredicted_outputs": sorted(actual - expected),
                                     "unemitted_predictions": sorted(expected - actual)})
        if (source_manifest(root) != manifest or implementation_digest() != revision
                or discover_builds(root, WORKFLOW)["inventory_digest"] != inventory["inventory_digest"]):
            raise LocalBuildFailure("local-build-source-changed")
        result["findings"] = sorted({row["code"]: row for row in result["findings"]}.values(), key=lambda row: row["code"])
        result["verdict"] = "failed" if result["findings"] else "passed"
        result["result_digest"] = digest(canonical(result))
        checked = contracts.result(result)
        if artifact_export is not None and checked["verdict"] == "passed":
            from local_runtime import artifacts, write_files
            exported = artifacts.artifact_files(base / "verified-runtime")
            artifact_export.mkdir()
            write_files(artifact_export, exported)
        return checked


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        flags = [arg.split("=", 1)[0] for arg in argv if arg.startswith("--")]
        if len(flags) != len(set(flags)):
            raise LocalBuildFailure("local-build-arguments-invalid")
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument("--source-root", required=True)
        parser.add_argument("--package-cache")
        parser.add_argument("--acquire-cache")
        parser.add_argument("--configuration", choices=CONFIGURATIONS)
        parser.add_argument("--scratch-root")
        args = parser.parse_args(argv)
        if (bool(args.package_cache) == bool(args.acquire_cache)
                or (args.acquire_cache and (args.configuration or args.scratch_root))
                or (args.package_cache and not args.scratch_root)):
            raise LocalBuildFailure("local-build-arguments-invalid")
        if args.acquire_cache:
            tools.acquire_cache(Path(args.source_root), Path(args.acquire_cache))
            value = {"schema": "local-build-acquisition/v1", "authorized": False, "verdict": "verified"}
        else:
            value = run(args.source_root, args.package_cache,
                        (args.configuration,) if args.configuration else CONFIGURATIONS, args.scratch_root)
        status = 0 if value["verdict"] in {"passed", "verified"} else 1
    except Exception as error:
        if isinstance(error, LocalBuildFailure):
            code = str(error)
        elif isinstance(error, tools.ToolchainFailure):
            code = str(error)
        elif isinstance(error, release.ReleaseFailure):
            code = error.code
        else:
            code = "local-build-verification-failed"
        value = {"schema": "local-build-error/v1", "authorized": False, "verdict": "failed",
                 "release_eligibility": "blocked", "operation_authorization": "blocked", "findings": [{"code": code}]}
        status = 1
    print(json.dumps(value, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
