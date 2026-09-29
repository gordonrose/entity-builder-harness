#!/usr/bin/env python3
"""Discover literal callers without executing source or asserting runtime behavior."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.caller-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind bounded workflow and package caller topology to safe fresh source digests.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import os
from pathlib import Path
import re
import shlex
import stat

from source_inventory import Collector, SourceFailure, canonical, checked_document, digest

MAX_BYTES = 2 * 1024 * 1024
MAX_GRAPH_NODES = 10000
MAX_CALL_DEPTH = 80
MAX_COMMANDS = 256
SAFE_PATH = re.compile(r"[A-Za-z0-9_./-]+\Z")
WORKFLOW_PATH = re.compile(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml\Z")
SCRIPT_NAME = re.compile(r"[A-Za-z0-9_:@./-]+\Z")
TOOL_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
SOURCE_ROOTS = {"scripts", "platform", "apps", "products", "packages", "infra", ".github", "tests", "fixtures"}
FORBIDDEN_PARTS = {".git", ".cache", "node_modules", "__pycache__"}
RESERVED = {"if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done",
            "case", "esac", "function", "select", "eval", "exec", "source", "command",
            "builtin", "env", "cd", "export", "set", "unset", "sh", "bash", "python", "python3", "node",
            "pushd", "popd", "dirs", "alias", "unalias", "hash", "enable", "declare", "typeset",
            "local", "readonly", "trap", "read", "readarray", "mapfile", "getopts", "shopt",
            "shift", "return", "break", "continue", "exit", "logout", "umask", "ulimit", "exec",
            "time", "coproc", "source"}


def safe_path(value):
    return (isinstance(value, str) and bool(SAFE_PATH.fullmatch(value))
            and not value.startswith("/")
            and all(part not in ("", ".", "..") for part in value.split("/")))


def commands(value):
    """Parse the entire bounded block before adding any invocation edges."""
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_BYTES:
        return None
    # Conservative by design, including metacharacters inside quoted strings.
    if any(character in value for character in "$`;|<>()\\{}*?[]~#\r"):
        return None
    parts = value.replace("&&", "\n").splitlines()
    if "&" in "".join(parts) or len(parts) > MAX_COMMANDS:
        return None
    if re.search(r"(?:^|&&)\s*(?:&&|$)", value):
        return None
    parsed = []
    for part in parts:
        if not part.strip():
            continue
        try:
            tokens = shlex.split(part, comments=False, posix=True)
        except ValueError:
            return None
        if not tokens:
            return None
        first = tokens[0]
        if first == "npm":
            if len(tokens) < 3 or tokens[1] != "run" or not SCRIPT_NAME.fullmatch(tokens[2]):
                # Package installation and other npm modes have implicit behavior.
                return None
            if len(tokens) > 3 and tokens[3] != "--":
                return None
            kind = "npm"
        elif first in {"bash", "node", "python", "python3"}:
            if len(tokens) < 2 or not safe_path(tokens[1]) or "/" not in tokens[1]:
                return None
            kind = "script"
        else:
            if not TOOL_NAME.fullmatch(first) or first in RESERVED:
                return None
            kind = "tool"
        parsed.append((kind, tokens))
    return parsed or None


class CallerCollector:
    def __init__(self, root):
        self.root = root
        self.reader = Collector(root)
        self.sources = {}
        self.nodes = {}
        self.edges = {}
        self.findings = set()
        self.raw = {}
        self.script_nodes = {}
        self.package_nodes = {}
        self.package_done = set()
        self.package = None
        self.package_source = None
        self.package_problem = None
        self.active = []
        self.script_active = []

    def issue(self, node_id, code):
        self.findings.add((code, node_id))
        if node_id in self.nodes:
            values = self.nodes[node_id]["issues"]
            if code not in values:
                values.append(code)
                values.sort()

    def node(self, source, kind, locator, detail, issues=()):
        node_id = digest(canonical([source["id"], kind, locator]))
        if node_id not in self.nodes and len(self.nodes) >= MAX_GRAPH_NODES:
            raise SourceFailure("caller-limit-exceeded")
        self.nodes.setdefault(node_id, {
            "id": node_id, "source_id": source["id"], "kind": kind,
            "locator_digest": digest(canonical(locator)),
            "detail_digest": digest(canonical(detail)), "issues": [],
        })
        for code in issues:
            self.issue(node_id, code)
        return node_id

    def edge(self, caller, callee, kind, call):
        call_digest = digest(canonical(call))
        edge_id = digest(canonical([caller, callee, kind, call_digest]))
        self.edges[edge_id] = {"id": edge_id, "caller_id": caller, "callee_id": callee,
                               "kind": kind, "call_digest": call_digest}

    def read(self, relative):
        if relative in self.raw:
            return self.raw[relative]
        code = None
        raw = b""
        if not safe_path(relative):
            code = "caller-path-unsafe"
        elif any(part in FORBIDDEN_PARTS for part in relative.split("/")):
            code = "caller-path-unsupported"
        else:
            try:
                fd = self.reader.open_relative(self.root / relative, os.O_RDONLY)
                with os.fdopen(fd, "rb") as stream:
                    metadata = os.fstat(stream.fileno())
                    if not stat.S_ISREG(metadata.st_mode):
                        code = "caller-source-type-unsupported"
                    elif metadata.st_size > MAX_BYTES:
                        code = "caller-limit-exceeded"
                    else:
                        raw = stream.read(MAX_BYTES + 1)
                        if len(raw) > MAX_BYTES:
                            raw, code = b"", "caller-limit-exceeded"
            except FileNotFoundError:
                code = "caller-path-missing"
            except (OSError, ValueError):
                code = "caller-path-unreadable"
        source_id = digest(relative.encode("utf-8", errors="surrogatepass"))
        source = {"id": source_id, "path": relative if safe_path(relative) else "unavailable", "digest": digest(raw)}
        self.sources[source_id] = source
        result = source, raw, code
        self.raw[relative] = result
        return result

    def configuration(self, relative, parent):
        # Presence itself is unsupported; never interpret npm configuration values.
        source, _raw, code = self.read(relative)
        target = self.node(source, "configuration", "configuration", source["digest"],
                           [code or "caller-context-unsupported"])
        self.edge(parent, target, "invokes", ["configuration", relative])

    def parse_document(self, source, raw, node_id, json_only=False):
        try:
            document = checked_document(raw, json_only=json_only)
            pending = [document]
            while pending:
                item = pending.pop()
                if isinstance(item, dict):
                    if "$tag" in item:
                        raise SourceFailure("caller-source-parse-failed")
                    pending.extend(item.values())
                elif isinstance(item, list):
                    pending.extend(item)
            return document
        except SourceFailure:
            self.issue(node_id, "caller-source-parse-failed")
            return None

    def package_script(self, name, hooks=True):
        if self.package_source is None:
            self.package_source, raw, code = self.read("package.json")
            self.package_problem = code
            if not code:
                try:
                    self.package = checked_document(raw, json_only=True)
                except SourceFailure:
                    self.package_problem = "caller-source-parse-failed"
            if not isinstance(self.package, dict) or not isinstance(self.package.get("scripts", {}), dict):
                self.package_problem = self.package_problem or "caller-package-shape-invalid"
                self.package = {"scripts": {}}
        script = self.package.get("scripts", {}).get(name)
        node_id = self.node(self.package_source, "package-command", ["scripts", name], script)
        self.package_nodes[name] = node_id
        if self.package_problem:
            self.issue(node_id, self.package_problem)
        if name in self.active:
            self.issue(node_id, "caller-cycle")
            return node_id
        if (name, hooks) in self.package_done:
            return node_id
        self.package_done.add((name, hooks))
        if len(self.active) >= MAX_CALL_DEPTH:
            self.issue(node_id, "caller-limit-exceeded")
            return node_id
        if not isinstance(script, str):
            self.issue(node_id, "caller-package-command-missing")
            return node_id
        config = self.root / ".npmrc"
        if config.exists() or config.is_symlink():
            self.issue(node_id, "caller-context-unsupported")
            self.configuration(".npmrc", node_id)
            return node_id
        self.active.append(name)
        try:
            # Automatic lifecycle hooks are invocations, not classification exclusions.
            if hooks:
                for prefix, edge_kind in (("pre", "npm-pre"), ("post", "npm-post")):
                    hook = prefix + name
                    if hook in self.package.get("scripts", {}):
                        hook_id = self.package_script(hook, hooks=False)
                        self.edge(node_id, hook_id, edge_kind, [prefix, name])
            self.block(node_id, self.package_source, ["scripts", name], script)
        finally:
            self.active.pop()
        return node_id

    def script(self, relative, interpreter="bash"):
        source, raw, code = self.read(relative)
        node_id = self.node(source, "script-entrypoint", "entrypoint", source["digest"], [code] if code else [])
        if node_id in self.script_active:
            self.issue(node_id, "caller-cycle")
            return node_id
        if len(self.script_active) >= MAX_CALL_DEPTH:
            self.issue(node_id, "caller-limit-exceeded")
            return node_id
        if (node_id, interpreter) in self.script_nodes:
            return node_id
        self.script_nodes[node_id, interpreter] = True
        if code:
            return node_id
        if relative.split("/")[0] not in SOURCE_ROOTS:
            self.issue(node_id, "caller-path-unsupported")
            return node_id
        # Follow only literal shell bodies and the exact established dispatch wrapper.
        try:
            text = raw.decode("utf-8")
        except UnicodeError:
            self.issue(node_id, "caller-source-parse-failed")
            return node_id
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        if interpreter == "bash" and relative.endswith(".sh") and len(lines) == 4 and lines[:3] == [
                "set -euo pipefail", 'ROOT="$(git rev-parse --show-toplevel)"', 'cd "$ROOT"']:
            match = re.fullmatch(r'exec python3(?: -B)? (?:"\$ROOT/([A-Za-z0-9_./-]+)"|([A-Za-z0-9_./-]+)) "\$@"', lines[3])
            if match:
                target = match.group(1) or match.group(2)
                if safe_path(target):
                    self.script_active.append(node_id)
                    try:
                        child = self.script(target, "python3")
                        self.edge(node_id, child, "invokes", ["python3", target, "forward-arguments"])
                    finally:
                        self.script_active.pop()
                    return node_id
        if interpreter == "bash" and relative.endswith(".sh"):
            if lines and lines[0] == "set -euo pipefail":
                lines = lines[1:]
            body = "\n".join(lines)
            if commands(body) is not None:
                self.script_active.append(node_id)
                try:
                    self.block(node_id, source, ["body"], body)
                finally:
                    self.script_active.pop()
                return node_id
        self.issue(node_id, "caller-script-body-unresolved")
        return node_id

    def block(self, caller, source, locator, value):
        parsed = commands(value)
        if parsed is None:
            self.issue(caller, "caller-opaque-command")
            return
        if any(kind == "npm" and len(tokens) > 3 for kind, tokens in parsed):
            self.issue(caller, "caller-arguments-unsupported")
            return
        for index, (kind, tokens) in enumerate(parsed):
            if kind == "npm":
                callee = self.package_script(tokens[2])
            elif kind == "script":
                callee = self.script(tokens[1], tokens[0])
            else:
                callee = self.node(source, "tool-command", locator + [index], tokens,
                                   ["caller-tool-behavior-unresolved"])
            self.edge(caller, callee, "invokes", [index, tokens])

    @staticmethod
    def unsupported_context(value):
        if not isinstance(value, dict):
            return True
        if any(key in value for key in ("defaults", "shell", "working-directory", "container", "services")):
            return True
        environment = value.get("env", {})
        if not isinstance(environment, dict):
            return True
        # These can alter invocation selection without changing the literal command.
        return any(str(key).lower().startswith(("npm_config_", "node_options", "node_path", "pythonpath", "pythonhome", "pythonstartup", "bash_env", "bash_func_", "path", "shellopts", "bashopts", "env", "ifs", "cdpath", "git_", "home", "xdg_config_home", "shell", "comspec")) for key in environment)

    def workflow(self, relative):
        source, raw, code = self.read(relative)
        root_id = self.node(source, "workflow", "workflow", source["digest"], [code] if code else [])
        if code:
            return root_id
        document = self.parse_document(source, raw, root_id)
        if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict) or not document["jobs"]:
            self.issue(root_id, "caller-workflow-shape-invalid")
            return root_id
        inherited_context = self.unsupported_context(document)
        if inherited_context:
            self.issue(root_id, "caller-context-unsupported")
        for job_name, job in document["jobs"].items():
            if not isinstance(job, dict):
                self.issue(root_id, "caller-workflow-shape-invalid")
                continue
            if "uses" in job:
                job_id = self.node(source, "workflow-step", ["jobs", job_name], job,
                                   ["caller-workflow-action-unresolved"])
                self.edge(root_id, job_id, "invokes", ["jobs", job_name])
            steps = job.get("steps", [])
            if not isinstance(steps, list) or not steps and "uses" not in job:
                self.issue(root_id, "caller-workflow-shape-invalid")
                continue
            job_context = inherited_context or self.unsupported_context(job)
            for index, step in enumerate(steps):
                locator = ["jobs", job_name, "steps", index]
                node_id = self.node(source, "workflow-step", locator, step)
                self.edge(root_id, node_id, "invokes", locator)
                if not isinstance(step, dict) or ("run" in step) == ("uses" in step):
                    self.issue(node_id, "caller-workflow-shape-invalid")
                elif "uses" in step:
                    self.issue(node_id, "caller-workflow-action-unresolved")
                elif job_context or self.unsupported_context(step):
                    self.issue(node_id, "caller-context-unsupported")
                else:
                    self.block(node_id, source, locator, step["run"])
        return root_id


def discover_callers(root: Path, workflow_path: str) -> dict:
    """Return a fresh, safe caller graph; findings never authorize execution."""
    root = Path(root).absolute()
    collector = CallerCollector(root)
    entry_path = workflow_path if isinstance(workflow_path, str) and WORKFLOW_PATH.fullmatch(workflow_path) and safe_path(workflow_path) else "unavailable"
    try:
        root_valid = not root.is_symlink() and root.resolve() == root and root.is_dir()
    except (OSError, RuntimeError):
        root_valid = False
    if not root_valid or entry_path == "unavailable":
        relative = entry_path
        source_id = digest(relative.encode())
        source = {"id": source_id, "path": relative, "digest": digest(b"")}
        collector.sources[source_id] = source
        entry_id = collector.node(source, "workflow", "workflow", source["digest"],
                                  ["caller-root-invalid" if not root_valid else "caller-entrypoint-invalid"])
    else:
        try:
            entry_id = collector.workflow(entry_path)
        except (SourceFailure, RecursionError):
            source, _raw, _code = collector.read(entry_path)
            entry_id = digest(canonical([source["id"], "workflow", "workflow"]))
            collector.issue(entry_id, "caller-limit-exceeded")
            # Limit failures can interrupt recursive discovery before a parent edge
            # is attached. Keep only the root-reachable partial graph; root remains
            # explicitly incomplete, so omitted descendants cannot become a pass.
            reached = {entry_id}
            pending = True
            while pending:
                before = len(reached)
                reached.update(edge["callee_id"] for edge in collector.edges.values()
                               if edge["caller_id"] in reached)
                pending = len(reached) != before
            collector.nodes = {key: value for key, value in collector.nodes.items() if key in reached}
            collector.edges = {key: value for key, value in collector.edges.items()
                               if value["caller_id"] in reached and value["callee_id"] in reached}
            collector.findings = {(code, subject) for code, subject in collector.findings if subject in reached}
            used_sources = {node["source_id"] for node in collector.nodes.values()}
            collector.sources = {key: value for key, value in collector.sources.items() if key in used_sources}
    dependency = Path(__file__).with_name("source_inventory.py")
    revision = digest(canonical([digest(Path(__file__).read_bytes()), digest(dependency.read_bytes())]))
    result = {
        "schema": "caller-inventory/v1", "collector_revision": revision,
        "entrypoint": {"path": entry_path, "node_id": entry_id},
        "sources": sorted(collector.sources.values(), key=lambda item: item["id"]),
        "nodes": sorted(collector.nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(collector.edges.values(), key=lambda item: item["id"]),
        "findings": [{"code": code, "subject_id": subject} for code, subject in sorted(collector.findings)],
    }
    result["graph_digest"] = digest(canonical(result))
    return result
