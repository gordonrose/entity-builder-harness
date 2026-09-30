"""Check safe local execution observations without admitting a release."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.local-build-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate compiler and runtime observations and immutable local result bindings.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.local-build-runner
#     path: scripts/04.deploy/operational-realization-gate/local_build.py

import re

import build_contracts
import release_compiler as release


# These are the selected repository build contracts, not caller-selected commands.
RUNTIME_LAYOUTS = {
    "platform/server/tsconfig.runtime-test.json": (
        ".cache/platform-server-runtime", "runtime-test-runner",
        "platform/server/tests/run-runtime-tests.mjs", "platform/server/tests"),
    "products/kanbien-platform/tsconfig.runtime-test.json": (
        ".cache/product-kanbien-platform-runtime", "runtime-test-runner",
        "products/kanbien-platform/tests/run-runtime-tests.mjs", "products/kanbien-platform/tests"),
    "platform/server/tsconfig.image.json": (
        ".cache/platform-shell-image-build", "image-shim-generator",
        "scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs", None),
}
CONFIGURATIONS = set(RUNTIME_LAYOUTS) | {
    "platform/server/tsconfig.check.json", "platform/server/tsconfig.json",
    "products/kanbien-platform/tsconfig.check.json", "products/kanbien-platform/tsconfig.json",
}


def checked_digest(document, field):
    if release.digest_document({key: value for key, value in document.items() if key != field}) != document[field]:
        raise release.ReleaseFailure("local-build-digest-invalid")


def safe_relative(path):
    return (isinstance(path, str) and re.fullmatch(r"[A-Za-z0-9_./@+-]+", path)
            and all(part not in {"", ".", ".."} for part in path.split("/")))


def unique_paths(rows):
    paths = [row["path"] for row in rows]
    if len(set(paths)) != len(paths) or any(not safe_relative(path) for path in paths):
        raise release.ReleaseFailure("local-build-path-invalid")
    return set(paths)


def observation(document):
    identity = document.get("schema") if isinstance(document, dict) else None
    if identity not in {"local-typescript-observation/v1", "local-typescript-emission-observation/v1"}:
        raise release.ReleaseFailure("local-build-observation-schema-invalid")
    build_contracts.validate_schema(identity.split("/")[0], document)
    checked_digest(document, "observation_digest")
    inputs, outputs = unique_paths(document["inputs"]), unique_paths(document["outputs"])
    if not safe_relative(document["configuration"]) or any(not path.startswith(".cache/") for path in outputs):
        raise release.ReleaseFailure("local-build-path-invalid")
    if inputs & outputs:
        raise release.ReleaseFailure("local-build-input-overwritten")
    if document["no_emit"] and outputs:
        raise release.ReleaseFailure("local-build-noemit-output")
    for row in document["inputs"]:
        if (row["kind"] == "dependency") != row["path"].startswith("node_modules/"):
            raise release.ReleaseFailure("local-build-input-kind-invalid")
    for row in document["resolutions"]:
        if not safe_relative(row["from"]) or (row["resolved_path"] is not None and not safe_relative(row["resolved_path"])):
            raise release.ReleaseFailure("local-build-path-invalid")
    for row in document["diagnostics"]:
        if row["path"] is not None and not safe_relative(row["path"]):
            raise release.ReleaseFailure("local-build-path-invalid")
    if document["verdict"] == "passed":
        if (document["node_version"] != "22.23.3" or document["typescript_version"] != "5.9.3"
                or document["findings"] or any(row["category"] == "error" for row in document["diagnostics"])
                or document["configuration"] not in inputs
                or "node_modules/typescript/lib/typescript.js" not in inputs
                or (not document["no_emit"] and (document["emit_skipped"] or not outputs))):
            raise release.ReleaseFailure("local-build-observation-inconsistent")
    elif not document["findings"] and not any(row["category"] == "error" for row in document["diagnostics"]):
        raise release.ReleaseFailure("local-build-observation-inconsistent")
    if identity == "local-typescript-emission-observation/v1":
        _emission_map(document)
    return document


def emission_kind(path):
    if re.search(r"\.d\.(?:ts|mts|cts)$", path):
        return "declaration"
    if path.endswith(".map"):
        return "source-map"
    if path.endswith(".tsbuildinfo"):
        return "build-info"
    if path.endswith((".js", ".mjs", ".cjs")):
        return "javascript"
    return "other"


def executable_source(path):
    return emission_kind(path) != "declaration" and re.search(r"\.(?:tsx?|mts|cts|jsx?|mjs|cjs)$", path) is not None


def _emission_map(document):
    inputs = {row["path"]: row for row in document["inputs"]}
    outputs = {row["path"]: row for row in document["outputs"]}
    entries = document["emission_map"]["entries"]
    paths = [entry["output_path"] for entry in entries]
    if paths != sorted(outputs) or len(set(paths)) != len(paths):
        raise release.ReleaseFailure("local-build-emission-membership-invalid")
    for entry in entries:
        origins = entry["source_paths"]
        if (origins != sorted(set(origins)) or any(path not in inputs for path in origins)
                or entry["kind"] != emission_kind(entry["output_path"])):
            raise release.ReleaseFailure("local-build-emission-source-invalid")
        if entry["kind"] == "javascript" and (not origins or any(not executable_source(path) for path in origins)):
            raise release.ReleaseFailure("local-build-emission-source-invalid")
    remainder = unique_paths(document["existing_remainder"])
    if (remainder & (set(inputs) | set(outputs)) or any(not path.startswith(".cache/") for path in remainder)
            or [row["path"] for row in document["existing_remainder"]] != sorted(remainder)
            or document["output_mode"] == "fresh-exclusive" and remainder):
        raise release.ReleaseFailure("local-build-existing-remainder-invalid")
    return document["emission_map"]


def emission_map_binding(document, require_commonjs=False):
    """Legacy observations remain readable but cannot establish emission proof."""
    observation(document)
    if document["schema"] != "local-typescript-emission-observation/v1":
        raise release.ReleaseFailure("local-build-emission-required")
    value = document["emission_map"]
    if require_commonjs and value["module_kind"] != "commonjs":
        raise release.ReleaseFailure("local-build-emission-module-unsupported")
    return value


def runtime_emission(document, source_path, output_root, *, source_digest, configuration):
    """Join a current source digest to one actual executable output; caller binds output bytes."""
    mapping = emission_map_binding(document, require_commonjs=True)
    if (document["verdict"] != "passed" or document["no_emit"] or document["emit_skipped"]
            or document["configuration"] != configuration
            or not safe_relative(source_path) or source_path.startswith(("node_modules/", ".cache/"))
            or not executable_source(source_path)
            or not safe_relative(output_root) or not output_root.startswith(".cache/")):
        raise release.ReleaseFailure("local-build-runtime-emission-invalid")
    source = next((row for row in document["inputs"] if row["path"] == source_path), None)
    if source is None or source["kind"] != "repository" or source["digest"] != source_digest:
        raise release.ReleaseFailure("local-build-runtime-emission-source-changed")
    matches = [row for row in mapping["entries"] if row["kind"] == "javascript" and source_path in row["source_paths"]]
    if (len(matches) != 1 or matches[0]["source_paths"] != [source_path]
            or not matches[0]["output_path"].startswith(output_root + "/")
            or not matches[0]["output_path"].endswith((".js", ".cjs"))):
        raise release.ReleaseFailure("local-build-runtime-emission-ambiguous")
    return next(dict(row) for row in document["outputs"] if row["path"] == matches[0]["output_path"])


def runtime(document):
    identity = document.get("schema") if isinstance(document, dict) else None
    if identity not in {"local-runtime-observation/v1", "local-workspace-runtime-observation/v1"}:
        raise release.ReleaseFailure("local-build-runtime-schema-invalid")
    build_contracts.validate_schema(identity.split("/")[0], document)
    if identity == "local-workspace-runtime-observation/v1":
        from package_exports import check_runtime
        check_runtime(document)
    checked_digest(document, "receipt_digest")
    layout = RUNTIME_LAYOUTS.get(document["configuration"])
    if (layout is None or document["kind"] != layout[1]
            or document["generator"]["path"] != layout[2]):
        raise release.ReleaseFailure("local-build-runtime-identity-invalid")
    paths = unique_paths(document["artifact_files"])
    if not paths or any(path.endswith((".ts", ".tsx", ".mts", ".cts")) for path in paths):
        raise release.ReleaseFailure("local-build-runtime-artifact-invalid")
    selected = document["selected_runtime_tests"]
    expected = sorted(path for path in paths if layout[3] is not None
                      and path.rsplit("/", 1)[0] == layout[3]
                      and path.endswith("-runtime.test.js"))
    if selected != expected:
        raise release.ReleaseFailure("local-build-runtime-membership-invalid")
    if document["kind"] == "runtime-test-runner":
        if not selected or document["executed_runner_count"] != 1:
            raise release.ReleaseFailure("local-build-runtime-membership-invalid")
    elif selected or document["executed_runner_count"] != 0:
        raise release.ReleaseFailure("local-build-runtime-membership-invalid")
    return document


def runtime_source_binding(document, source_manifest):
    """Bind the generator to the parent's freshly verified source snapshot.

    The compact public result contains a source digest, not the full manifest;
    this producer-side check supplies the otherwise unavailable source bytes.
    """
    runtime(document)
    for source in [document["generator"], *document.get("generator_helpers", [])]:
        rows = [row for row in source_manifest if row["path"] == source["path"]]
        if len(rows) != 1 or rows[0]["digest"] != source["digest"]:
            raise release.ReleaseFailure("local-build-runtime-generator-binding-invalid")
    return document


def runtime_compiler_binding(document, observed):
    if document["schema"] == "local-workspace-runtime-observation/v1":
        emission_map_binding(observed, require_commonjs=True)
        if (observed["output_mode"] != "fresh-exclusive"
                or document["workspace_exports"]["compiler_observation_digest"] != observed["observation_digest"]):
            raise release.ReleaseFailure("local-build-runtime-emission-binding-invalid")
    prefix = RUNTIME_LAYOUTS[document["configuration"]][0] + "/"
    compiled = sorted(({**row, "path": row["path"][len(prefix):]}
                       for row in observed["outputs"] if row["path"].startswith(prefix)),
                      key=lambda row: row["path"])
    if (not compiled or any(row["path"].startswith("node_modules/") for row in compiled)
            or release.digest_document(compiled) != document["compiler_artifact_digest"]):
        raise release.ReleaseFailure("local-build-runtime-compiler-binding-invalid")
    actual = {row["path"]: row for row in document["artifact_files"]}
    expected = {row["path"]: row for row in compiled}
    if document["schema"] == "local-workspace-runtime-observation/v1":
        generated_rows = document["workspace_exports"]["generated_files"]
        generated = {row["path"]: row for row in generated_rows}
        if (len(actual) != len(document["artifact_files"]) or len(generated) != len(generated_rows)
                or set(expected) & set(generated) or actual != {**expected, **generated}):
            raise release.ReleaseFailure("local-build-runtime-compiler-binding-invalid")
        return
    if (any(actual.get(path) != row for path, row in expected.items())
            or any(not path.startswith("node_modules/") for path in actual.keys() - expected.keys())):
        raise release.ReleaseFailure("local-build-runtime-compiler-binding-invalid")


def result(document):
    build_contracts.validate_schema("local-build-result", document)
    checked_digest(document, "result_digest")
    configurations = [row["configuration"] for row in document["builds"]]
    ids = [row["build_id"] for row in document["builds"]]
    if (not ids or len(set(ids)) != len(ids) or len(set(configurations)) != len(configurations)
            or any(configuration not in CONFIGURATIONS for configuration in configurations)):
        raise release.ReleaseFailure("local-build-identity-invalid")
    finding_codes = {row["code"] for row in document["findings"]}
    for row in document["builds"]:
        observation(row["observation"])
        if (row["observation"]["schema"] == "local-typescript-emission-observation/v1"
                and row["observation"]["output_mode"] != "fresh-exclusive"):
            raise release.ReleaseFailure("local-build-fresh-emission-required")
        if row["configuration"] != row["observation"]["configuration"]:
            raise release.ReleaseFailure("local-build-identity-invalid")
        if row["runtime"] is not None:
            runtime(row["runtime"])
            if (row["observation"]["schema"] == "local-typescript-emission-observation/v1"
                    and row["runtime"]["schema"] != "local-workspace-runtime-observation/v1"):
                raise release.ReleaseFailure("local-build-runtime-export-proof-required")
            if (row["runtime"]["configuration"] != row["configuration"]
                    or row["runtime"]["source_inventory_digest"] != document["build_inventory_digest"]
                    or row["runtime"]["dependency_tree_digest"] != document["toolchain"]["dependency_digest"]
                    or row["observation"]["verdict"] != "passed"):
                raise release.ReleaseFailure("local-build-runtime-binding-invalid")
            runtime_compiler_binding(row["runtime"], row["observation"])
        elif row["configuration"] in RUNTIME_LAYOUTS and row["observation"]["verdict"] == "passed":
            if document["verdict"] != "failed" or "local-build-runtime-failed" not in finding_codes:
                raise release.ReleaseFailure("local-build-runtime-missing")
    if document["verdict"] == "passed" and (document["findings"] or any(
            row["observation"]["verdict"] != "passed" for row in document["builds"])):
        raise release.ReleaseFailure("local-build-result-inconsistent")
    if document["verdict"] == "failed" and not document["findings"] and all(
            row["observation"]["verdict"] == "passed" for row in document["builds"]):
        raise release.ReleaseFailure("local-build-result-inconsistent")
    return document
