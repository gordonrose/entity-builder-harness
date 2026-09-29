#!/usr/bin/env python3
"""Bounded observations for selected TypeScript builds; never invokes tools."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.build-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind TypeScript invocations to config origins, workspace manifests, imports and bounded output predictions.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations
import os
from pathlib import Path, PurePosixPath
import re
import stat
from caller_inventory import CallerCollector, discover_callers, safe_path
from operation_inventory import OperationCollector, normalized, private_path
from source_inventory import SourceFailure, canonical, checked_document, digest

MAX_FILES = 4000
MAX_BYTES = 48 * 1024 * 1024
MAX_ROWS = 50000
MAX_DEPTH = 40
MAX_TOKENS = 200000
SOURCE_SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
SPECIFIER = re.compile(r"[A-Za-z0-9_@./*-]+\Z")
KNOWN_OPTIONS = {
    "composite", "declaration", "emitDeclarationOnly", "exactOptionalPropertyTypes",
    "module", "moduleResolution", "noEmitOnError", "noUncheckedIndexedAccess", "outDir",
    "rootDir", "strict", "target", "incremental", "noEmit", "baseUrl", "paths", "types",
    "skipLibCheck", "esModuleInterop", "forceConsistentCasingInFileNames",
    "allowSyntheticDefaultImports", "strictNullChecks", "noUnusedLocals", "noUnusedParameters",
}
TOKEN = re.compile(r'''/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[A-Za-z_$][\w$]*|[^\s]''')


def path_base(path):
    parent = str(PurePosixPath(path).parent)
    return "" if parent == "." else parent


def literal_imports(text):
    """A lexical subset, not TypeScript AST semantics; comments do not create imports."""
    tokens = []
    for match in TOKEN.finditer(text):
        token = match.group()
        if token.startswith(("/*", "//")):
            continue
        tokens.append(token)
        if len(tokens) > MAX_TOKENS:
            raise SourceFailure("build-limit-exceeded")
    found, dynamic, work = [], False, 0
    for index, token in enumerate(tokens):
        if token not in {"import", "export", "require"}:
            continue
        following = tokens[index + 1] if index + 1 < len(tokens) else ""
        position = None
        if token == "import" and following[:1] in {"'", '"'}:
            position = index + 1
        elif token in {"import", "require"} and following == "(":
            if index + 3 < len(tokens) and tokens[index + 2][:1] in {"'", '"'} and tokens[index + 3] == ")":
                position = index + 2
            else:
                dynamic = True
        elif token in {"import", "export"}:
            for offset in range(index + 1, len(tokens) - 1):
                work += 1
                if work > MAX_TOKENS * 2:
                    raise SourceFailure("build-limit-exceeded")
                if tokens[offset] == ";":
                    break
                if tokens[offset] == "from" and tokens[offset + 1][:1] in {"'", '"'}:
                    position = offset + 1
                    break
        if position is not None:
            value = tokens[position][1:-1]
            if "\\" in value:
                dynamic = True
            else:
                found.append((position, value))
    if "///" in text or re.search(r"\b(?:eval|Function)\s*\(", text):
        dynamic = True
    return sorted(set(found)), dynamic


class BuildCollector(OperationCollector):
    def __init__(self, root, graph):
        self.root, self.graph = root, graph
        self.reader = CallerCollector(root)
        self.sources = {row["id"]: dict(row) for row in graph["sources"]}
        self.raw = {}
        self.subjects = {node["id"]: node for node in graph["nodes"] if node["kind"] == "tool-command"}
        self.bindings, self.edges, self.builds = {}, {}, {}
        self.findings = set()
        self.total_bytes = 0
        self.visited, self.active = set(), set()
        self.workspace = {}
        self.workspace_sources = []

    def issue(self, build, code):
        self.findings.add((build, code))

    def bind(self, build, source, kind, locator, detail):
        if len(self.bindings) >= MAX_ROWS:
            raise SourceFailure("build-limit-exceeded")
        identity = digest(canonical([build, source["id"], kind, locator]))
        self.bindings[identity] = {
            "id": identity, "build_id": build, "source_id": source["id"], "kind": kind,
            "locator_digest": digest(canonical(locator)), "detail_digest": digest(canonical(detail)),
        }

    def edge(self, build, source, target, kind, detail):
        if len(self.edges) >= MAX_ROWS:
            raise SourceFailure("build-limit-exceeded")
        identity = digest(canonical([build, source["id"], target["id"], kind, detail]))
        self.edges[identity] = {"id": identity, "build_id": build,
            "from_source_id": source["id"], "to_source_id": target["id"], "kind": kind,
            "detail_digest": digest(canonical(detail))}

    def read(self, relative, build):
        if not safe_path(relative) or private_path(relative):
            self.issue(build, "build-path-unsafe")
            return None
        if len(relative) > 512:
            raise SourceFailure("build-limit-exceeded")
        if relative in self.raw:
            result = self.raw[relative]
            if result[2]:
                self.issue(build, "build-input-missing" if result[2] == "caller-path-missing" else "build-input-unreadable")
            return result
        if len(self.sources) >= MAX_FILES:
            raise SourceFailure("build-limit-exceeded")
        source, raw, problem = self.reader.read(relative)
        if problem == "caller-limit-exceeded":
            raise SourceFailure("build-limit-exceeded")
        previous = self.sources.get(source["id"])
        if previous is not None and previous != source:
            raise SourceFailure("build-source-stale")
        self.sources[source["id"]] = source
        self.total_bytes += len(raw)
        if self.total_bytes > MAX_BYTES:
            raise SourceFailure("build-limit-exceeded")
        if problem:
            self.issue(build, "build-input-missing" if problem == "caller-path-missing" else "build-input-unreadable")
        self.raw[relative] = source, raw, problem
        return self.raw[relative]

    def document(self, relative, build):
        result = self.read(relative, build)
        if result is None or result[2]:
            return None
        try:
            value = checked_document(result[1], json_only=True)
        except SourceFailure:
            self.issue(build, "build-document-invalid")
            return None
        if not isinstance(value, dict):
            self.issue(build, "build-document-invalid")
            return None
        return result[0], value

    def exists(self, relative, build):
        if not safe_path(relative) or private_path(relative):
            self.issue(build, "build-path-unsafe")
            return False
        try:
            fd = self.reader.reader.open_relative(self.root / relative, os.O_RDONLY)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    self.issue(build, "build-input-unreadable")
                    return False
            finally:
                os.close(fd)
            return True
        except FileNotFoundError:
            return False
        except (OSError, ValueError):
            self.issue(build, "build-input-unreadable")
            return False

    def members(self, build, pattern):
        try:
            return super().members(build, pattern)
        except SourceFailure:
            raise SourceFailure("build-limit-exceeded") from None

    def workspaces(self, build, parent):
        self.workspace, self.workspace_sources = {}, []
        package = self.document("package.json", build)
        lock = self.read("package-lock.json", build)
        if lock:
            self.edge(build, parent, lock[0], "package-lock", "root-lock")
        self.issue(build, "toolchain-installation-unproven")
        if not package:
            return
        source, document = package
        self.edge(build, parent, source, "workspace-root", "root-package")
        self.bind(build, source, "workspace-membership", "patterns", document.get("workspaces"))
        values = document.get("workspaces", [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            self.issue(build, "workspace-pattern-unsupported")
            return
        members = set()
        for value in values:
            pattern = normalized("", value)
            if pattern is None:
                self.issue(build, "workspace-pattern-unsupported")
                continue
            members.update(self.members(build, pattern.rstrip("/") + "/package.json"))
        self.bind(build, source, "workspace-membership", "manifests", sorted(members))
        workspaces = {}
        for member in sorted(members):
            result = self.document(member, build)
            if result is None:
                continue
            manifest, data = result
            self.edge(build, source, manifest, "workspace-manifest", member)
            self.bind(build, manifest, "workspace-manifest", "document", data)
            name = data.get("name")
            if not isinstance(name, str) or not re.fullmatch(r"(?:@[a-zA-Z0-9_.-]+/)?[a-zA-Z0-9_.-]+", name):
                self.issue(build, "workspace-name-invalid")
                continue
            workspaces.setdefault(name, []).append((manifest, data))
        for candidates in workspaces.values():
            if len(candidates) != 1:
                self.issue(build, "workspace-name-duplicate")
        self.workspace = workspaces
        self.workspace_sources = sorted({row[0]["id"] for rows in workspaces.values() for row in rows})

    def config(self, build, parent, relative, active=()):
        if len(active) > MAX_DEPTH:
            raise SourceFailure("build-limit-exceeded")
        if relative in active:
            self.issue(build, "config-inheritance-cycle")
            return {}, {}, {}
        result = self.document(relative, build)
        if result is None:
            return {}, {}, {}
        source, data = result
        self.edge(build, parent, source, "build-config" if not active else "config-extends", relative)
        self.bind(build, source, "typescript-config", "document", data)
        options, origins, fields = {}, {}, {}
        extends = data.get("extends")
        if extends is not None:
            target = normalized(path_base(relative), extends) if isinstance(extends, str) and extends.startswith(".") else None
            if target is None:
                self.issue(build, "config-extends-unsupported")
            else:
                if not PurePosixPath(target).suffix:
                    target += ".json"
                options, origins, fields = self.config(build, source, target, active + (relative,))
        options, origins, fields = dict(options), dict(origins), dict(fields)
        local = data.get("compilerOptions", {})
        if not isinstance(local, dict):
            self.issue(build, "build-config-invalid")
            local = {}
        for key, value in local.items():
            options[key], origins[key] = value, path_base(relative)
        for key in ("files", "include", "exclude"):
            if key in data:
                fields[key] = {"origin": path_base(relative), "value": data[key]}
        if set(data) - {"extends", "compilerOptions", "files", "include", "exclude", "$schema"}:
            self.issue(build, "config-field-unsupported")
        if set(options) - KNOWN_OPTIONS:
            self.issue(build, "compiler-option-unsupported")
        string_options = {"module", "moduleResolution", "target", "rootDir", "outDir", "baseUrl"}
        for key, value in options.items():
            if key in string_options and not isinstance(value, str):
                self.issue(build, "build-config-invalid")
            elif key == "types" and (not isinstance(value, list) or any(not isinstance(item, str) for item in value)):
                self.issue(build, "build-config-invalid")
            elif key == "paths" and not isinstance(value, dict):
                self.issue(build, "build-config-invalid")
            elif key in KNOWN_OPTIONS - string_options - {"types", "paths"} and not isinstance(value, bool):
                self.issue(build, "build-config-invalid")
        mappings = options.get("paths", {})
        if isinstance(mappings, dict):
            for pattern, values in mappings.items():
                if (not isinstance(pattern, str) or not SPECIFIER.fullmatch(pattern)
                        or pattern.count("*") > 1 or not isinstance(values, list) or not values
                        or any(not isinstance(value, str) or not value or value.count("*") > 1 for value in values)):
                    self.issue(build, "paths-mapping-unsupported")
        if "module" in options and str(options["module"]).lower() not in {"commonjs", "esnext", "es2022", "es2020", "es2015", "es6"}:
            self.issue(build, "compiler-mode-unsupported")
        if "moduleResolution" in options and str(options["moduleResolution"]).lower() not in {"bundler", "node10", "node", "node16", "nodenext"}:
            self.issue(build, "compiler-mode-unsupported")
        self.bind(build, source, "effective-config", "merged", [options, origins, fields])
        return options, origins, fields

    def option_path(self, build, options, origins, name):
        value = options.get(name)
        if not isinstance(value, str):
            self.issue(build, "build-path-option-unresolved")
            return None
        target = normalized(origins[name], value)
        if target is None or target and not safe_path(target):
            self.issue(build, "build-path-unsafe")
            return None
        return target

    def root_members(self, build, source, fields):
        roots = set()
        if "files" not in fields and "include" not in fields:
            self.issue(build, "build-default-membership-unresolved")
        excluded = set()
        if "exclude" in fields:
            entry = fields["exclude"]
            if not isinstance(entry["value"], list):
                self.issue(build, "build-config-invalid")
            else:
                for value in entry["value"]:
                    target = normalized(entry["origin"], value)
                    if target is None:
                        self.issue(build, "build-pattern-unsupported")
                    else:
                        excluded.update(self.members(build, target))
            self.issue(build, "exclude-semantics-unresolved")
        for field in ("files", "include"):
            if field not in fields:
                continue
            entry = fields[field]
            if not isinstance(entry["value"], list) or any(not isinstance(value, str) for value in entry["value"]):
                self.issue(build, "build-config-invalid")
                continue
            for index, value in enumerate(entry["value"]):
                target = normalized(entry["origin"], value)
                if target is None:
                    self.issue(build, "build-pattern-unsupported")
                    continue
                members = self.members(build, target)
                if field == "include":
                    members = [member for member in members if member not in excluded]
                self.bind(build, source, "build-membership", [field, index], [target, members])
                for member in members:
                    if member.endswith(SOURCE_SUFFIXES):
                        roots.add(member)
                    else:
                        self.issue(build, "build-source-extension-unsupported")
        if not roots:
            self.issue(build, "build-input-empty")
        return sorted(roots)

    def candidates(self, build, target):
        if target is None:
            self.issue(build, "build-path-unsafe")
            return []
        suffix = PurePosixPath(target).suffix
        if suffix == ".js":
            candidates = [target[:-3] + value for value in (".ts", ".tsx", ".d.ts", ".js")]
        elif suffix == ".mjs":
            candidates = [target[:-4] + value for value in (".mts", ".d.mts", ".mjs")]
        elif suffix == ".cjs":
            candidates = [target[:-4] + value for value in (".cts", ".d.cts", ".cjs")]
        elif suffix in SOURCE_SUFFIXES or suffix == ".json":
            candidates = [target]
        else:
            candidates = [target + value for value in (".ts", ".tsx", ".d.ts", ".js", "/index.ts", "/index.tsx", "/index.d.ts", "/index.js")]
        # Evaluate privacy on complete candidate paths. A literal "secrets"
        # basename may resolve to public source secrets.ts; a secrets/ directory
        # or dotenv candidate remains excluded before opening any descriptor.
        permitted = [candidate for candidate in candidates if safe_path(candidate) and not private_path(candidate)]
        if not permitted:
            self.issue(build, "build-path-unsafe")
        found = [candidate for candidate in permitted if self.exists(candidate, build)]
        if len(found) > 1:
            self.issue(build, "import-resolution-ambiguous")
        return found

    def alias_targets(self, build, specifier, options, origins):
        mappings = options.get("paths", {})
        if not isinstance(mappings, dict):
            self.issue(build, "paths-mapping-unsupported")
            return [], False
        matching = []
        for pattern, values in mappings.items():
            if not isinstance(pattern, str) or pattern.count("*") > 1 or not SPECIFIER.fullmatch(pattern):
                self.issue(build, "paths-mapping-unsupported")
                continue
            if "*" in pattern:
                prefix, suffix = pattern.split("*")
                if not specifier.startswith(prefix) or not specifier.endswith(suffix) or len(specifier) < len(prefix) + len(suffix):
                    continue
                capture = specifier[len(prefix):len(specifier)-len(suffix) if suffix else None]
                score = len(prefix)
            elif pattern == specifier:
                capture, score = "", 1000000
            else:
                continue
            matching.append((score, pattern, values, capture))
        if not matching:
            return [], False
        score = max(row[0] for row in matching)
        matching = [row for row in matching if row[0] == score]
        if len(matching) > 1:
            self.issue(build, "paths-mapping-ambiguous")
        base = self.option_path(build, options, origins, "baseUrl") if "baseUrl" in options else origins.get("paths", "")
        result = []
        for _score, pattern, values, capture in matching:
            if not isinstance(values, list) or not values or any(not isinstance(value, str) or value.count("*") > 1 for value in values):
                self.issue(build, "paths-mapping-unsupported")
                continue
            for value in values:
                target = normalized(base, value.replace("*", capture)) if base is not None else None
                result.extend(self.candidates(build, target))
        if len(set(result)) > 1:
            self.issue(build, "import-resolution-ambiguous")
        return sorted(set(result)), True

    def workspace_targets(self, build, source, specifier, options):
        parts = specifier.split("/")
        name = "/".join(parts[:2]) if specifier.startswith("@") else parts[0]
        subpath = "." if specifier == name else "./" + specifier[len(name) + 1:]
        candidates = self.workspace.get(name, [])
        if not candidates:
            self.issue(build, "external-import-unresolved")
            return []
        result = []
        for manifest, data in candidates:
            self.edge(build, source, manifest, "workspace-import", specifier)
            exports = data.get("exports")
            self.bind(build, manifest, "workspace-export", specifier, exports)
            mode = str(options.get("moduleResolution", "")).lower()
            if mode not in {"bundler", "node16", "nodenext"}:
                self.issue(build, "workspace-resolution-mode-unresolved")
                continue
            if mode != "bundler":
                self.issue(build, "workspace-conditions-unresolved")
            value = exports if isinstance(exports, str) and subpath == "." else exports.get(subpath) if isinstance(exports, dict) else None
            if not isinstance(value, str) or not value.startswith("./") or "*" in value:
                self.issue(build, "workspace-export-unsupported")
                continue
            target = normalized(path_base(manifest["path"]), value)
            if target is None or not target.startswith(path_base(manifest["path"]) + "/"):
                self.issue(build, "workspace-export-unsafe")
                continue
            result.extend(self.candidates(build, target))
        return sorted(set(result))

    def imports(self, build, source, raw, options, origins, depth=0):
        pair = build, source["id"]
        if pair in self.active:
            self.issue(build, "import-cycle-observed")
            return
        if pair in self.visited:
            return
        if depth > MAX_DEPTH:
            raise SourceFailure("build-limit-exceeded")
        self.visited.add(pair)
        self.active.add(pair)
        try:
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                self.issue(build, "build-source-format-unsupported")
                return
            imports, dynamic = literal_imports(text)
            if dynamic:
                self.issue(build, "dynamic-import-unresolved")
            for index, specifier in imports:
                self.bind(build, source, "literal-import", index, specifier)
                if specifier.startswith("node:"):
                    self.issue(build, "ambient-types-unresolved")
                    continue
                if not SPECIFIER.fullmatch(specifier) or "*" in specifier:
                    self.issue(build, "import-specifier-unsupported")
                    continue
                if specifier.startswith("."):
                    targets = self.candidates(build, normalized(path_base(source["path"]), specifier))
                    kind = "relative-import"
                else:
                    targets, matched = self.alias_targets(build, specifier, options, origins)
                    kind = "paths-import"
                    if not matched:
                        if "baseUrl" in options:
                            if specifier.startswith("@"):
                                # Scoped local directories are outside safe_path's grammar;
                                # retain this lookup uncertainty before workspace fallback.
                                self.issue(build, "scoped-baseurl-lookup-unresolved")
                            else:
                                base = self.option_path(build, options, origins, "baseUrl")
                                targets = self.candidates(build, normalized(base, specifier) if base is not None else None)
                                kind = "baseurl-import"
                        if not targets:
                            targets = self.workspace_targets(build, source, specifier, options)
                            kind = "workspace-source"
                self.bind(build, source, "import-candidates", index, targets)
                if not targets:
                    self.issue(build, "import-target-unresolved")
                for target in targets:
                    result = self.read(target, build)
                    if result is not None:
                        self.edge(build, source, result[0], kind, [index, specifier])
                        if not result[2]:
                            self.imports(build, result[0], result[1], options, origins, depth + 1)
        finally:
            self.active.remove(pair)

    def predictions(self, build, options, origins):
        no_emit = options.get("noEmit", False)
        declarations = options.get("emitDeclarationOnly", False)
        if not isinstance(no_emit, bool) or not isinstance(declarations, bool):
            self.issue(build, "build-config-invalid")
            return "unresolved", "unresolved", "", []
        allowed_findings = {"build-semantics-unresolved", "exact-artifact-unproven",
                            "toolchain-installation-unproven", "ambient-types-unresolved", "import-cycle-observed"}
        input_unresolved = any(owner == build and code not in allowed_findings for owner, code in self.findings)
        if no_emit:
            return "no-emit", "unresolved" if input_unresolved else "bounded", "", []
        root = self.option_path(build, options, origins, "rootDir")
        output = self.option_path(build, options, origins, "outDir")
        mode = "declarations" if declarations else "javascript"
        unresolved = root is None or output is None
        if output is not None and any(part in {".git", "node_modules", ".aws", ".codex", ".agents"} or part.startswith(".env") for part in output.split("/")):
            self.issue(build, "build-output-path-unsafe")
            output, unresolved = None, True
        if declarations and options.get("declaration") is not True:
            self.issue(build, "declaration-options-unresolved")
            unresolved = True
        if options.get("composite") or options.get("incremental"):
            self.issue(build, "incremental-output-unresolved")
            unresolved = True
        if set(options) - KNOWN_OPTIONS:
            unresolved = True
        outputs = []
        for candidate_build, source_id in sorted(self.visited):
            if candidate_build != build:
                continue
            path = self.sources[source_id]["path"]
            if path.endswith((".d.ts", ".d.mts", ".d.cts")):
                continue
            if not path.endswith(".ts"):
                self.issue(build, "emission-extension-unresolved")
                unresolved = True
                continue
            prefix = root + "/" if root else ""
            if root is None or not path.startswith(prefix):
                self.issue(build, "source-outside-rootdir")
                unresolved = True
                continue
            relative = path[len(prefix):-3]
            if declarations:
                outputs.append({"path": relative + ".d.ts", "source_id": source_id, "kind": "declaration"})
            else:
                kind = "runtime-test" if path.endswith("-runtime.test.ts") else "javascript"
                outputs.append({"path": relative + ".js", "source_id": source_id, "kind": kind})
                if options.get("declaration") is True:
                    outputs.append({"path": relative + ".d.ts", "source_id": source_id, "kind": "declaration"})
        paths = [row["path"] for row in outputs]
        if len(paths) != len(set(paths)):
            self.issue(build, "emission-path-collision")
            unresolved = True
        if input_unresolved:
            unresolved = True
        return mode, "unresolved" if unresolved else "bounded", output or "", sorted(outputs, key=lambda row: (row["path"], row["source_id"]))

    def collect(self):
        tokens = self.tool_tokens()
        if set(tokens) != set(self.subjects):
            raise SourceFailure("build-invocation-unresolved")
        for build, value in sorted(tokens.items()):
            if not value or len(value) != 3 or value[:2] != ["tsc", "-p"] or not safe_path(value[2]):
                raise SourceFailure("build-invocation-unsupported")
            node = self.subjects[build]
            parent = self.sources[node["source_id"]]
            config_id = digest(value[2].encode())
            invocation_ids = sorted(edge["id"] for edge in self.graph["edges"] if edge["callee_id"] == build)
            for edge in self.graph["edges"]:
                if edge["callee_id"] == build:
                    self.bind(build, parent, "invocation", edge["id"], edge)
            self.workspaces(build, parent)
            options, origins, fields = self.config(build, parent, value[2])
            config = self.sources.get(config_id, parent)
            roots = self.root_members(build, config, fields)
            root_ids = []
            for path in roots:
                result = self.read(path, build)
                if result is not None:
                    root_ids.append(result[0]["id"])
                    self.edge(build, config, result[0], "build-root", path)
                    if not result[2]:
                        self.imports(build, result[0], result[1], options, origins)
            self.issue(build, "build-semantics-unresolved")
            self.issue(build, "exact-artifact-unproven")
            if options.get("types") or "types" not in options:
                self.issue(build, "ambient-types-unresolved")
            mode, prediction, output, expected = self.predictions(build, options, origins)
            self.builds[build] = {
                "id": build, "source_id": parent["id"], "invocation_ids": invocation_ids,
                "config_source_id": config["id"], "effective_config_digest": digest(canonical([options, origins, fields])),
                "root_source_ids": sorted(set(root_ids)), "workspace_source_ids": list(self.workspace_sources),
                "output_mode": mode, "prediction_status": prediction, "output_root": output,
                "expected_outputs": expected,
            }
        if not self.builds:
            raise SourceFailure("build-scope-empty")


def discover_builds(root: Path, workflow_path: str, graph=None) -> dict:
    root = Path(root).absolute()
    fresh = discover_callers(root, workflow_path)
    if graph is not None and graph != fresh:
        raise SourceFailure("build-graph-stale")
    collector = BuildCollector(root, fresh)
    try:
        collector.collect()
    except RecursionError:
        raise SourceFailure("build-limit-exceeded") from None
    revision = digest(canonical([digest(Path(__file__).with_name(name).read_bytes()) for name in
        ("build_inventory.py", "operation_inventory.py", "caller_inventory.py", "source_inventory.py")]))
    result = {
        "schema": "source-build-inventory/v1", "graph_digest": fresh["graph_digest"], "collector_revision": revision,
        "sources": sorted(collector.sources.values(), key=lambda row: row["id"]),
        "builds": sorted(collector.builds.values(), key=lambda row: row["id"]),
        "bindings": sorted(collector.bindings.values(), key=lambda row: row["id"]),
        "edges": sorted(collector.edges.values(), key=lambda row: row["id"]),
        "findings": [{"build_id": build, "code": code} for build, code in sorted(collector.findings)],
    }
    result["inventory_digest"] = digest(canonical(result))
    return result
