#!/usr/bin/env python3
"""Observe bounded operation inputs without executing or qualifying source."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.operation-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind selected operations to observed arguments and source dependency surfaces while retaining unresolved semantics.
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

from caller_inventory import CallerCollector, commands, discover_callers, safe_path
from source_inventory import SourceFailure, canonical, checked_document, digest

MAX_FILES = 3000
MAX_DEPTH = 30
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_ROWS = 50000
ROOTS = {"scripts", "platform", "apps", "products", "packages", "infra", ".github", "tests", "fixtures", "docs"}
FORBIDDEN = {".git", ".cache", "node_modules", "__pycache__", ".venv", ".aws", ".codex", ".agents", ".env", "secrets", "secret", "credentials", "credential"}
CODE = {".js", ".mjs", ".cjs", ".ts", ".py", ".sh"}
# These identify observations, not a complete parser or proof that a reference executes.
JS_IMPORT = re.compile(r'''\b(?:import|export)\s+(?:type\s+)?(?:[^\n;]*?\s+from\s+)?["']([^"'\n]+)["']|\brequire\(\s*["']([^"'\n]+)["']\s*\)''')
ROOT_LITERAL = re.compile(r'''["']((?:scripts|platform|apps|products|packages|infra|\.github|docs|tests|fixtures)/[A-Za-z0-9_./-]+)["']''')
SHELL_CALL = re.compile(r"(?m)^\s*(?:bash|node|python3?|source)(?:\s+-n)?\s+([A-Za-z0-9_./-]+)")
PY_LOCAL = re.compile(r"(?m)^\s*(?:from\s+([.A-Za-z_][.A-Za-z0-9_]*)\s+import\b|import\s+([A-Za-z_][.A-Za-z0-9_]*))")


def private_path(value):
    return any(part in FORBIDDEN or part.startswith(".env.") or part.endswith((".pem", ".key", ".env")) for part in value.split("/"))


def normalized(base, value):
    """Normalize relative traversal lexically, never by following filesystem links."""
    if not isinstance(value, str) or not value or value.startswith("/") or not re.fullmatch(r"[A-Za-z0-9_./*-]+", value):
        return None
    parts = list(PurePosixPath(base).parts) if base else []
    for part in value.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


class OperationCollector:
    def __init__(self, root, graph):
        self.root = root
        self.graph = graph
        self.reader = CallerCollector(root)
        self.sources = {row["id"]: dict(row) for row in graph["sources"]}
        self.subjects = {}
        self.observations = {}
        self.dependencies = {}
        self.findings = set()
        self.visited = set()
        self.active = set()
        self.total_bytes = 0
        self.counted = set()
        for node in graph["nodes"]:
            kind = {"script-entrypoint": "script", "tool-command": "tool"}.get(node["kind"])
            if node["kind"] == "workflow-step" and "caller-workflow-action-unresolved" in node["issues"]:
                kind = "action"
            if kind:
                self.subjects[node["id"]] = {"id": node["id"], "kind": kind, "source_id": node["source_id"],
                    "detail_digest": node["detail_digest"], "invocation_ids": sorted(edge["id"] for edge in graph["edges"] if edge["callee_id"] == node["id"])}
                for code in node["issues"]:
                    self.issue(node["id"], code)
                self.issue(node["id"], {"script": "script-semantics-unresolved", "tool": "tool-semantics-unresolved", "action": "action-implementation-unresolved"}[kind])

    def issue(self, subject, code):
        self.findings.add((subject, code))

    def observation(self, subject, source, kind, locator, detail):
        if len(self.observations) >= MAX_ROWS:
            raise SourceFailure("operation-limit-exceeded")
        identity = digest(canonical([subject, source["id"], kind, locator]))
        self.observations[identity] = {"id": identity, "subject_id": subject, "source_id": source["id"], "kind": kind,
                                     "locator_digest": digest(canonical(locator)), "detail_digest": digest(canonical(detail))}

    def read(self, relative, subject):
        if not safe_path(relative) or relative.split("/")[0] not in ROOTS and relative not in {"package.json", "package-lock.json"}:
            self.issue(subject, "operation-path-unsafe")
            return None
        if private_path(relative):
            self.issue(subject, "generated-input-unresolved")
            return None
        if len(self.sources) >= MAX_FILES and digest(relative.encode()) not in self.sources:
            raise SourceFailure("operation-limit-exceeded")
        source, raw, problem = self.reader.read(relative)
        if problem == "caller-limit-exceeded":
            raise SourceFailure("operation-limit-exceeded")
        previous = self.sources.get(source["id"])
        if previous and previous != source:
            self.issue(subject, "operation-source-stale")
            return None
        self.sources[source["id"]] = source
        if source["id"] not in self.counted:
            self.counted.add(source["id"])
            self.total_bytes += len(raw)
        if self.total_bytes > MAX_TOTAL_BYTES:
            raise SourceFailure("operation-limit-exceeded")
        if problem:
            self.issue(subject, {"caller-path-missing": "operation-input-missing", "caller-limit-exceeded": "operation-limit-exceeded"}.get(problem, "operation-input-unreadable"))
        return source, raw, problem

    def dependency(self, subject, source, relative, kind, detail, depth, recurse=True):
        read = self.read(relative, subject)
        if read is None:
            return None
        target, raw, problem = read
        if len(self.dependencies) >= MAX_ROWS:
            raise SourceFailure("operation-limit-exceeded")
        identity = digest(canonical([subject, source["id"], target["id"], kind, detail]))
        self.dependencies[identity] = {"id": identity, "subject_id": subject, "from_source_id": source["id"],
                                      "to_source_id": target["id"], "kind": kind, "detail_digest": digest(canonical(detail))}
        if not problem and recurse:
            self.scan(subject, target, raw, depth + 1)
        return read

    def local_import(self, subject, source, specifier, index, depth):
        self.observation(subject, source, "literal-import", index, specifier)
        if not specifier.startswith("."):
            if not specifier.startswith("node:"):
                self.issue(subject, "external-import-unresolved")
            return
        target = normalized(str(PurePosixPath(source["path"]).parent), specifier)
        if target is None:
            self.issue(subject, "operation-path-unsafe")
            return
        if private_path(target):
            self.issue(subject, "generated-input-unresolved")
            return
        # TypeScript convention: .js module specifiers may refer to .ts source.
        candidates = [target]
        if target.endswith(".js") and source["path"].endswith(".ts"):
            candidates = [target[:-3] + ".ts", target]
        elif not PurePosixPath(target).suffix:
            candidates = [target + suffix for suffix in (".ts", ".js", ".mjs", "/index.ts", "/index.js")]
        found = []
        for candidate in candidates:
            try:
                fd = self.reader.reader.open_relative(self.root / candidate, os.O_RDONLY)
                with os.fdopen(fd, "rb") as stream:
                    if stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        found.append(candidate)
            except FileNotFoundError:
                pass
            except (OSError, ValueError):
                self.issue(subject, "operation-input-unreadable")
                return
        if len(found) > 1:
            self.issue(subject, "import-resolution-ambiguous")
        for candidate in found or candidates[:1]:
            self.dependency(subject, source, candidate, "literal-import", [index, specifier], depth)

    def scan(self, subject, source, raw, depth=0):
        pair = subject, source["id"]
        if pair in self.active:
            self.issue(subject, "operation-dependency-cycle")
            return
        if pair in self.visited:
            return
        if depth > MAX_DEPTH:
            raise SourceFailure("operation-limit-exceeded")
        self.visited.add(pair)
        self.active.add(pair)
        try:
            text = raw.decode("utf-8")
        except UnicodeError:
            self.issue(subject, "operation-source-format-unsupported")
            self.active.remove(pair)
            return
        suffix = PurePosixPath(source["path"]).suffix
        try:
            if suffix not in CODE:
                return
            self.issue(subject, "source-semantics-unresolved")
            if suffix in {".js", ".mjs", ".cjs", ".ts"}:
                for index, match in enumerate(JS_IMPORT.finditer(text)):
                    self.local_import(subject, source, match.group(1) or match.group(2), index, depth)
                if re.search(r"\b(?:import\s*\(|eval\s*\(|Function\s*\(|require\s*\(\s*[^\s'\"]|spawn|exec|readFile|readdir)", text):
                    self.issue(subject, "dynamic-input-unresolved")
            if suffix in {".py", ".sh"}:
                for index, match in enumerate(PY_LOCAL.finditer(text)):
                    name = match.group(1) or match.group(2)
                    self.observation(subject, source, "python-import", index, name)
                    target = normalized(str(PurePosixPath(source["path"]).parent), name.replace(".", "/") + ".py")
                    if target and (self.root / target).exists():
                        self.dependency(subject, source, target, "literal-import", ["python", index, name], depth)
                    else:
                        self.issue(subject, "python-import-resolution-unresolved")
            for index, match in enumerate(ROOT_LITERAL.finditer(text)):
                value = match.group(1)
                self.observation(subject, source, "literal-path-reference", index, value)
                self.dependency(subject, source, value, "literal-path-reference", index, depth)
            if suffix == ".sh":
                for index, match in enumerate(SHELL_CALL.finditer(text)):
                    value = match.group(1)
                    self.observation(subject, source, "script-call", index, match.group(0))
                    self.dependency(subject, source, value, "script-call", index, depth)
                if "$" in text or "<<" in text:
                    self.issue(subject, "dynamic-input-unresolved")
        finally:
            self.active.remove(pair)

    def members(self, subject, pattern):
        """Enumerate a limited glob grammar through no-follow directory descriptors."""
        if not pattern or any(char in pattern for char in "?[]{}\\") or any(part.count("**") and part != "**" for part in pattern.split("/")):
            self.issue(subject, "build-pattern-unsupported")
            return []
        parts = pattern.split("/")
        if private_path(pattern):
            self.issue(subject, "generated-input-unresolved")
            return []
        prefix = []
        for part in parts:
            if "*" in part:
                break
            prefix.append(part)
        if len(prefix) == len(parts):
            return [pattern]
        if not prefix or prefix[0] not in ROOTS:
            self.issue(subject, "build-pattern-unsupported")
            return []
        expression = ""
        for index, part in enumerate(parts):
            if part == "**":
                expression += "(?:[^/]+/)*"
            else:
                expression += re.escape(part).replace(r"\*", "[^/]*")
                if index < len(parts) - 1:
                    expression += "/"
        matcher = re.compile(expression + r"\Z")
        result = []
        pending = [("/".join(prefix), 0)]
        visited = 0
        while pending:
            directory, depth = pending.pop()
            visited += 1
            if depth > MAX_DEPTH or visited > MAX_FILES:
                raise SourceFailure("operation-limit-exceeded")
            try:
                descriptor = self.reader.reader.open_relative(self.root / directory, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    with os.scandir(descriptor) as scan:
                        entries = sorted((entry.name, entry.stat(follow_symlinks=False)) for entry in scan)
                finally:
                    os.close(descriptor)
            except (OSError, ValueError):
                self.issue(subject, "operation-input-unreadable")
                continue
            for name, metadata in entries:
                relative = directory + "/" + name
                if private_path(name):
                    self.issue(subject, "generated-input-unresolved")
                    continue
                if not safe_path(relative):
                    self.issue(subject, "operation-path-unsafe")
                elif stat.S_ISLNK(metadata.st_mode):
                    self.issue(subject, "operation-input-unreadable")
                elif stat.S_ISDIR(metadata.st_mode):
                    pending.append((relative, depth + 1))
                elif stat.S_ISREG(metadata.st_mode) and matcher.fullmatch(relative):
                    result.append(relative)
                    if len(result) > MAX_FILES:
                        raise SourceFailure("operation-limit-exceeded")
                elif not stat.S_ISREG(metadata.st_mode):
                    self.issue(subject, "operation-input-unreadable")
        return sorted(result)

    def config(self, subject, parent, relative, depth=0, active=()):
        if depth > MAX_DEPTH:
            raise SourceFailure("operation-limit-exceeded")
        if relative in active:
            self.issue(subject, "operation-dependency-cycle")
            return
        read = self.dependency(subject, parent, relative, "build-config" if not active else "config-extends", relative, depth, recurse=False)
        if not read or read[2]:
            return
        source, raw, _problem = read
        try:
            document = checked_document(raw, json_only=True)
        except SourceFailure:
            self.issue(subject, "build-config-invalid")
            return
        self.observation(subject, source, "typescript-config", "document", document)
        if not isinstance(document, dict):
            self.issue(subject, "build-config-invalid")
            return
        self.issue(subject, "build-semantics-unresolved")
        base = str(PurePosixPath(relative).parent)
        extends = document.get("extends")
        if extends is not None:
            target = normalized(base, extends) if isinstance(extends, str) and extends.startswith(".") else None
            if target:
                self.config(subject, source, target, depth + 1, active + (relative,))
            else:
                self.issue(subject, "build-config-unsupported")
        options = document.get("compilerOptions", {})
        if not isinstance(options, dict) or any(key in document for key in ("references", "exclude")) or isinstance(options, dict) and any(key in options for key in ("paths", "plugins", "typeRoots", "types", "baseUrl")):
            self.issue(subject, "build-resolution-unresolved")
        for field in ("files", "include"):
            values = document.get(field, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                self.issue(subject, "build-config-invalid")
                continue
            for index, value in enumerate(values):
                target = normalized(base, value)
                if not target:
                    self.issue(subject, "operation-path-unsafe")
                    continue
                members = self.members(subject, target)
                self.observation(subject, source, "build-membership", [field, index], [value, members])
                if not members:
                    self.issue(subject, "build-input-empty")
                for member in members:
                    self.dependency(subject, source, member, "build-input", [field, index, value], depth)
        if "files" not in document and "include" not in document:
            self.issue(subject, "build-default-membership-unresolved")

    def tool_tokens(self):
        """Recover only exact bounded blocks already represented in the caller graph."""
        result = {}
        for source in self.graph["sources"]:
            if source["path"] != "package.json" and not source["path"].startswith(".github/workflows/"):
                continue
            raw_source, raw, problem = self.reader.read(source["path"])
            if problem or raw_source != source:
                for subject in self.subjects:
                    self.issue(subject, "operation-source-stale")
                continue
            try:
                document = checked_document(raw, json_only=source["path"] == "package.json")
            except SourceFailure:
                continue
            blocks = []
            if source["path"] == "package.json":
                if isinstance(document, dict) and isinstance(document.get("scripts"), dict):
                    blocks = [(["scripts", key], value) for key, value in document["scripts"].items()]
            elif isinstance(document, dict) and isinstance(document.get("jobs"), dict):
                for name, job in document["jobs"].items():
                    if isinstance(job, dict) and isinstance(job.get("steps"), list):
                        blocks += [(["jobs", name, "steps", i], step["run"]) for i, step in enumerate(job["steps"]) if isinstance(step, dict) and "run" in step]
            for locator, value in blocks:
                parsed = commands(value)
                if parsed is None:
                    continue
                for index, (kind, tokens) in enumerate(parsed):
                    if kind == "tool":
                        node = digest(canonical([source["id"], "tool-command", locator + [index]]))
                        if node in self.subjects:
                            result[node] = tokens
        return result

    def collect(self):
        tokens = self.tool_tokens()
        for subject, binding in sorted(self.subjects.items()):
            source = self.sources[binding["source_id"]]
            for edge in self.graph["edges"]:
                if edge["callee_id"] == subject:
                    self.observation(subject, source, "invocation", edge["id"], [edge["caller_id"], edge["call_digest"], edge["kind"]])
            if binding["kind"] == "script":
                read = self.read(source["path"], subject)
                if read and not read[2]:
                    self.scan(subject, read[0], read[1])
            elif binding["kind"] == "tool":
                value = tokens.get(subject)
                self.observation(subject, source, "tool-arguments", "argv", value)
                if value and len(value) == 3 and value[:2] == ["tsc", "-p"] and safe_path(value[2]):
                    self.config(subject, source, value[2])
                else:
                    self.issue(subject, "tool-arguments-unsupported")
        return self


def discover_operations(root: Path, workflow_path: str, graph=None) -> dict:
    """Bind observed inputs; any internal graph argument must equal a fresh scan."""
    from action_observations import observe_actions
    root = Path(root).absolute()
    fresh_graph = discover_callers(root, workflow_path)
    if graph is not None and graph != fresh_graph:
        raise SourceFailure("operation-graph-stale")
    graph = fresh_graph
    collector = OperationCollector(root, graph)
    try:
        collector.collect()
    except RecursionError:
        raise SourceFailure("operation-limit-exceeded") from None
    observations, findings = observe_actions(root, workflow_path, graph)
    for row in observations:
        if row["subject_id"] in collector.subjects:
            collector.observations[row["id"]] = row
    for row in findings:
        if row["subject_id"] in collector.subjects:
            collector.issue(row["subject_id"], row["code"])
    revision = digest(canonical([digest(Path(__file__).with_name(name).read_bytes()) for name in
                               ("operation_inventory.py", "action_observations.py", "caller_inventory.py", "source_inventory.py", "cloudformation_inventory.py")]))
    result = {"schema": "source-operation-inventory/v1", "graph_digest": graph["graph_digest"], "collector_revision": revision,
              "sources": sorted(collector.sources.values(), key=lambda row: row["id"]),
              "subjects": sorted(collector.subjects.values(), key=lambda row: row["id"]),
              "observations": sorted(collector.observations.values(), key=lambda row: row["id"]),
              "dependencies": sorted(collector.dependencies.values(), key=lambda row: row["id"]),
              "findings": [{"subject_id": subject, "code": code} for subject, code in sorted(collector.findings)]}
    result["inventory_digest"] = digest(canonical(result))
    return result
