#!/usr/bin/env python3
"""Independently inventory bounded source surfaces; never execute or qualify them."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.release-control.source-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Collect deterministic content-bound source observations without executing source or exposing values.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

import yaml

ROOTS = ["package.json", "apps", "products", "packages", "platform",
         "scripts/04.deploy", "infra/04.deploy", ".github/workflows"]
EXCLUDED = {"node_modules", ".git", ".cache", "build", "dist", "generated", "__pycache__", "tests", "fixtures"}
MAX_BYTES = 2 * 1024 * 1024
MAX_NODES = 100000
MAX_DEPTH = 40
SAFE_PATH = re.compile(r"[A-Za-z0-9_./-]+\Z")
SUPPORTED_RESOURCE_TYPES = {"AWS::ECS::TaskDefinition"}
CFN_TAGS = {"Ref", "Sub", "GetAtt", "Join", "ImportValue", "FindInMap", "Select", "Split",
            "If", "Equals", "Not", "And", "Or", "Condition", "Base64", "GetAZs", "Cidr", "Transform"}
CODE_SUFFIXES = {".sh", ".py", ".js", ".mjs", ".cjs", ".ts"}
UNKNOWN_CODE_SUFFIXES = {".bash", ".zsh", ".rb", ".pl", ".php", ".ps1", ".bat", ".cmd", ".exe", ".go", ".tf", ".hcl", ".bicep", ".cue", ".nix", ".sql", ".wasm", ".dockerfile"}


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


class SourceFailure(Exception):
    """Only a fixed diagnostic, never parser or source text."""


class SourceLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
            raise SourceFailure("source-alias-unsupported")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if type(key) is not str or key in result:
                raise SourceFailure("source-key-invalid")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


# Workflow 'on' is a string; only JSON boolean spellings receive boolean types.
SourceLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in values
          if tag not in {"tag:yaml.org,2002:bool", "tag:yaml.org,2002:timestamp"}]
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
SourceLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$", re.I), list("tTfF"))


def tagged(loader, tag, node):
    if tag not in CFN_TAGS:
        raise SourceFailure("source-tag-unsupported")
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node, deep=True)
    else:
        value = loader.construct_mapping(node, deep=True)
    return {"$tag": tag, "value": value}


SourceLoader.add_multi_constructor("!", tagged)


def checked_document(raw, json_only=False):
    def mapping(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise SourceFailure("source-key-invalid")
            value[key] = item
        return value
    try:
        result = (json.loads(raw.decode("utf-8"), object_pairs_hook=mapping)
                  if json_only else yaml.load(raw.decode("utf-8"), Loader=SourceLoader))
        stack = [(result, 0)]
        count = 0
        while stack:
            value, depth = stack.pop()
            count += 1
            if count > MAX_NODES or depth > MAX_DEPTH:
                raise SourceFailure("source-limit-exceeded")
            if type(value) is dict:
                stack.extend((item, depth + 1) for item in value.values())
            elif type(value) is list:
                stack.extend((item, depth + 1) for item in value)
            elif value is not None and type(value) not in (str, int, bool):
                raise SourceFailure("source-value-unsupported")
        return result
    except SourceFailure:
        raise
    except (ValueError, UnicodeError, yaml.YAMLError, RecursionError):
        raise SourceFailure("source-parse-failed") from None


class Collector:
    def __init__(self, root):
        self.root = root
        self.sources = {}
        self.observations = {}
        self.findings = set()

    def issue(self, source_id, code):
        self.findings.add((code, source_id))

    def observation(self, source, kind, locator, detail, parent=None, issues=()):
        observation_id = digest(canonical([source["id"], kind, locator]))
        self.observations[observation_id] = {
            "id": observation_id, "source_id": source["id"], "kind": kind,
            "locator_digest": digest(canonical(locator)), "subject_id": parent or observation_id,
            "detail_digest": digest(canonical(detail)), "issues": sorted(set(issues)),
        }
        for code in issues:
            self.issue(source["id"], code)
        return observation_id

    def add(self, relative, raw, problem=None):
        source_id = digest(relative.encode("utf-8", errors="surrogatepass"))
        safe = bool(SAFE_PATH.fullmatch(relative)) and all(part not in ("", ".", "..") for part in relative.split("/"))
        source = {"id": source_id, "path": relative if safe else "unavailable", "digest": digest(raw)}
        self.sources[source_id] = source
        issues = ([problem] if problem else []) + ([] if safe else ["source-path-unsafe"])
        self.observation(source, "source-file", "file", source["digest"], issues=issues)
        if issues:
            return
        path = Path(relative)
        suffix = path.suffix.lower()
        try:
            if path.name == "package.json":
                self.package(source, checked_document(raw, json_only=True), path)
            elif relative.startswith(".github/workflows/"):
                if suffix not in {".yml", ".yaml"}:
                    self.issue(source_id, "workflow-format-unsupported")
                else:
                    self.workflow(source, checked_document(raw))
            elif path.name == "Dockerfile" or path.name.startswith("Dockerfile.") and not path.name.endswith("dockerignore"):
                self.docker(source, raw.decode("utf-8"))
            elif relative.startswith("infra/04.deploy/") and suffix in {".yaml", ".yml", ".json"}:
                self.infrastructure(source, checked_document(raw, json_only=suffix == ".json"))
            if suffix in CODE_SUFFIXES and relative.startswith("scripts/04.deploy/"):
                self.observation(source, "script-entrypoint", "entrypoint", source["digest"], issues=["opaque-executable"])
            if (".main." in path.name and suffix in {".ts", ".js", ".mjs", ".py"}) or (relative.startswith("infra/04.deploy/") and suffix in CODE_SUFFIXES):
                self.observation(source, "source-entrypoint", "entrypoint", source["digest"], issues=["opaque-executable"])
            if suffix in UNKNOWN_CODE_SUFFIXES or raw.startswith(b"#!") and suffix not in CODE_SUFFIXES:
                self.issue(source_id, "executable-format-unsupported")
        except SourceFailure as failure:
            self.issue(source_id, str(failure))
        except (UnicodeError, ValueError, TypeError, RecursionError):
            self.issue(source_id, "source-parse-failed")

    def reference(self, source, base, value):
        if not isinstance(value, str) or not value.startswith("./") or any(ch in value for ch in "*${}"):
            self.issue(source["id"], "source-reference-unsupported")
            return
        target = base.parent / value
        if ".." in target.parts or target.is_absolute():
            self.issue(source["id"], "source-reference-outside-scope")
        elif any(part in EXCLUDED for part in target.parts):
            self.issue(source["id"], "excluded-source-reference")
        else:
            absolute = self.root / target
            # Inspect each parent: resolving an attacker-controlled symlink is forbidden.
            current = self.root
            for part in target.parts:
                current = current / part
                if current.is_symlink():
                    self.issue(source["id"], "source-symlink-unsupported")
                    return
            if not absolute.is_file():
                self.issue(source["id"], "source-reference-missing")
                return
            in_scope = target.as_posix() == "package.json" or any(
                target.as_posix().startswith(root + "/") for root in ROOTS if root != "package.json"
            )
            if not in_scope:
                self.issue(source["id"], "source-reference-outside-scope")
                return
            target_id = digest(target.as_posix().encode("utf-8"))
            if target_id not in self.sources:
                self.read(absolute, absolute.stat().st_size)
            # A declared export or binary can execute regardless of filename extension.
            self.issue(source["id"], "opaque-export-target")

    def package(self, source, document, path):
        if not isinstance(document, dict):
            raise SourceFailure("package-shape-invalid")
        scripts = document.get("scripts", {})
        if not isinstance(scripts, dict):
            raise SourceFailure("package-shape-invalid")
        for name, command in scripts.items():
            if not isinstance(command, str) or not command.strip():
                raise SourceFailure("package-command-invalid")
            self.observation(source, "package-command", ["scripts", name], command, issues=["opaque-executable"])
        for field, kind in [("exports", "package-export"), ("main", "package-export"),
                            ("module", "package-export"), ("browser", "package-export"),
                            ("imports", "package-export"), ("bin", "package-bin")]:
            if field not in document:
                continue
            def visit(value, locator):
                if isinstance(value, dict):
                    for key, item in value.items():
                        visit(item, locator + [key])
                elif isinstance(value, list):
                    for index, item in enumerate(value):
                        visit(item, locator + [index])
                elif isinstance(value, str):
                    self.observation(source, kind, locator, value)
                    self.reference(source, path, value)
                else:
                    raise SourceFailure("package-shape-invalid")
            visit(document[field], [field])
        workspaces = document.get("workspaces", [])
        if isinstance(workspaces, dict):
            workspaces = workspaces.get("packages", [])
        if not isinstance(workspaces, list) or any(not isinstance(item, str) for item in workspaces):
            raise SourceFailure("workspace-shape-invalid")
        for pattern in workspaces:
            if not re.fullmatch(r"(?:apps|products|packages|platform)(?:/[A-Za-z0-9_.-]+|/\*)*", pattern) or ".." in pattern.split("/"):
                self.issue(source["id"], "workspace-scope-unsupported")

    def workflow(self, source, document):
        if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
            raise SourceFailure("workflow-shape-invalid")
        for name, job in document["jobs"].items():
            if not isinstance(job, dict):
                raise SourceFailure("workflow-shape-invalid")
            if "uses" in job:
                self.observation(source, "workflow-step", ["jobs", name, "uses"], job, issues=["workflow-action-unresolved"])
            steps = job.get("steps", [])
            services = job.get("services", {})
            if not isinstance(steps, list) or not isinstance(services, dict):
                raise SourceFailure("workflow-shape-invalid")
            for index, step in enumerate(steps):
                if not isinstance(step, dict) or ("run" in step) == ("uses" in step):
                    raise SourceFailure("workflow-step-invalid")
                issues = ["opaque-executable"] if "run" in step else ["workflow-action-unresolved"]
                parent = self.observation(source, "workflow-step", ["jobs", name, "steps", index], step, issues=issues)
                self.env(source, step.get("env", {}), ["jobs", name, "steps", index, "env"], parent)
            for service, value in services.items():
                parent = self.observation(source, "workflow-service", ["jobs", name, "services", service], value)
                if not isinstance(value, dict):
                    raise SourceFailure("workflow-service-invalid")
                self.env(source, value.get("env", {}), ["jobs", name, "services", service, "env"], parent)
            self.env(source, job.get("env", {}), ["jobs", name, "env"], None)
            if "container" in job:
                self.observation(source, "workflow-service", ["jobs", name, "container"], job["container"])
        self.env(source, document.get("env", {}), ["env"], None)

    def env(self, source, value, locator, parent):
        if not isinstance(value, dict):
            raise SourceFailure("configuration-shape-invalid")
        for name, item in value.items():
            kind = "secret-binding" if isinstance(item, str) and re.search(r"\bsecrets\s*[.\[]", item) else "configuration-binding"
            self.observation(source, kind, locator + [name], {"name": name, "value": item}, parent)

    def docker(self, source, text):
        instructions = []
        pending = ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            pending += line[:-1] + " " if line.endswith("\\") else line
            if line.endswith("\\"):
                continue
            parts = pending.split(None, 1)
            if len(parts) != 2:
                raise SourceFailure("image-source-unsupported")
            if parts[0].upper() not in {"FROM", "ARG", "LABEL", "WORKDIR", "COPY", "ADD", "ENV", "EXPOSE", "USER", "RUN", "CMD", "ENTRYPOINT", "HEALTHCHECK", "ONBUILD", "SHELL", "STOPSIGNAL", "VOLUME", "MAINTAINER"}:
                raise SourceFailure("image-source-unsupported")
            instructions.append((parts[0].upper(), parts[1]))
            pending = ""
        if pending or not any(key == "FROM" for key, value in instructions):
            raise SourceFailure("image-source-unsupported")
        last_from = max(index for index, pair in enumerate(instructions) if pair[0] == "FROM")
        final = instructions[last_from:]
        if not any(key == "ENTRYPOINT" for key, value in final):
            self.issue(source["id"], "image-entrypoint-inherited")
        for index, (key, value) in enumerate(instructions):
            if key == "RUN":
                self.issue(source["id"], "opaque-image-build")
            if index < last_from:
                continue
            if key in {"ENTRYPOINT", "CMD"}:
                issues = []
                try:
                    command = json.loads(value)
                    if not isinstance(command, list) or not command or any(not isinstance(item, str) for item in command):
                        raise ValueError()
                except ValueError:
                    command = value
                    issues.append("image-command-unsupported")
                self.observation(source, "image-command", [key, index], command, issues=issues)
            elif key == "ENV":
                self.observation(source, "configuration-binding", [key, index], value)
            elif key in {"HEALTHCHECK", "ONBUILD", "SHELL"}:
                self.observation(source, "image-command", [key, index], value, issues=["image-command-unsupported"])

    def infrastructure(self, source, document):
        if not isinstance(document, dict):
            self.issue(source["id"], "infrastructure-shape-unsupported")
            return
        self.transforms(source, document)
        if "Resources" not in document:
            if any(key in document for key in ("services", "apiVersion", "ContainerDefinitions", "resource", "terraform")):
                self.issue(source["id"], "infrastructure-format-unsupported")
            return
        if not isinstance(document["Resources"], dict):
            raise SourceFailure("resource-shape-invalid")
        for name, resource in document["Resources"].items():
            if not isinstance(resource, dict) or not isinstance(resource.get("Type"), str):
                raise SourceFailure("resource-shape-invalid")
            issues = [] if resource["Type"] in SUPPORTED_RESOURCE_TYPES else ["resource-type-unsupported"]
            parent = self.observation(source, "resource", ["Resources", name], resource, issues=issues)
            self.dependencies(source, resource, ["Resources", name], parent)
            properties = resource.get("Properties", {})
            if not isinstance(properties, dict):
                raise SourceFailure("resource-shape-invalid")
            for key, value in properties.items():
                if key.endswith("RoleArn") or key in {"Role", "ExecutionRole", "TaskRole"}:
                    self.observation(source, "identity-binding", ["Resources", name, key], value, parent)
            containers = properties.get("ContainerDefinitions", [])
            if not isinstance(containers, list) or resource["Type"] in SUPPORTED_RESOURCE_TYPES and not containers:
                raise SourceFailure("container-shape-invalid")
            names = set()
            for index, container in enumerate(containers):
                if not isinstance(container, dict) or not isinstance(container.get("Name"), str) or container["Name"] in names:
                    raise SourceFailure("container-shape-invalid")
                names.add(container["Name"])
                locator = ["Resources", name, "ContainerDefinitions", index]
                container_issues = []
                if "Image" not in container or isinstance(container["Image"], str) and not container["Image"].strip():
                    container_issues.append("container-image-missing")
                elif not isinstance(container["Image"], str):
                    container_issues.append("container-image-unresolved")
                if not any(key in container for key in ("Command", "EntryPoint")):
                    container_issues.append("container-command-inherited")
                subject = self.observation(source, "container", locator, container, parent, issues=container_issues)
                for key in ("Command", "EntryPoint", "HealthCheck"):
                    if key in container:
                        command = container[key]
                        if key == "HealthCheck":
                            command = command.get("Command") if isinstance(command, dict) else None
                        issues = []
                        if not isinstance(command, list) or not command or any(not isinstance(item, str) or not item for item in command):
                            issues.append("container-command-unsupported")
                        self.observation(source, "command-binding", locator + [key], container[key], subject, issues=issues)
                for key, kind in [("Environment", "configuration-binding"), ("Secrets", "secret-binding")]:
                    values = container.get(key, [])
                    if not isinstance(values, list):
                        raise SourceFailure("binding-shape-invalid")
                    seen = set()
                    for position, binding in enumerate(values):
                        if not isinstance(binding, dict) or not isinstance(binding.get("Name"), str) or binding["Name"] in seen:
                            raise SourceFailure("binding-shape-invalid")
                        seen.add(binding["Name"])
                        if ("ValueFrom" if key == "Secrets" else "Value") not in binding:
                            raise SourceFailure("binding-shape-invalid")
                        self.observation(source, kind, locator + [key, position], binding, subject)

    def transforms(self, source, value):
        if isinstance(value, dict):
            if "Transform" in value or "Fn::Transform" in value or value.get("$tag") == "Transform":
                self.issue(source["id"], "infrastructure-transform-unsupported")
            for item in value.values():
                self.transforms(source, item)
        elif isinstance(value, list):
            for item in value:
                self.transforms(source, item)

    def dependencies(self, source, value, locator, parent):
        if isinstance(value, dict):
            if "Fn::ImportValue" in value or value.get("$tag") == "ImportValue":
                self.observation(source, "external-dependency", locator, value, parent)
            for key, item in value.items():
                self.dependencies(source, item, locator + [key], parent)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                self.dependencies(source, item, locator + [index], parent)

    def open_relative(self, path, flags):
        """Open every component relative to a directory descriptor, without following links."""
        descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            parts = path.relative_to(self.root).parts
            for index, part in enumerate(parts):
                options = flags if index == len(parts) - 1 else os.O_RDONLY | os.O_DIRECTORY
                next_descriptor = os.open(part, options | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = next_descriptor
            result, descriptor = descriptor, None
            return result
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def walk(self, directory, all_files):
        try:
            descriptor = self.open_relative(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                with os.scandir(descriptor) as scan:
                    entries = sorted([(entry.name, entry.stat(follow_symlinks=False)) for entry in scan], key=lambda item: item[0])
            finally:
                os.close(descriptor)
        except OSError:
            self.add(directory.relative_to(self.root).as_posix(), b"", "source-unreadable")
            return
        for name, metadata in entries:
            path = directory / name
            relative = path.relative_to(self.root).as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                self.add(relative, b"", "source-symlink-unsupported")
            elif stat.S_ISDIR(metadata.st_mode):
                if name in EXCLUDED:
                    # This is a versioned scope choice, never classification proof.
                    continue
                if not SAFE_PATH.fullmatch(relative):
                    self.add(relative, b"", "source-path-unsafe")
                else:
                    self.walk(path, all_files)
            elif stat.S_ISREG(metadata.st_mode):
                if all_files or name == "package.json" or re.search(r"\.main\.(?:ts|js|mjs|py)$", name):
                    self.read(path, metadata.st_size)
            else:
                self.add(relative, b"", "source-type-unsupported")

    def read(self, path, size):
        relative = path.relative_to(self.root).as_posix()
        if size > MAX_BYTES:
            self.add(relative, b"", "source-limit-exceeded")
            return
        try:
            # O_NOFOLLOW prevents a final-component link race from reading outside the root.
            fd = self.open_relative(path, os.O_RDONLY)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    self.add(relative, b"", "source-type-unsupported")
                    return
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                self.add(relative, b"", "source-limit-exceeded")
            else:
                self.add(relative, raw)
        except OSError:
            self.add(relative, b"", "source-unreadable")


def discover(root: Path) -> dict:
    """Return structural source observations and fixed unresolved findings only."""
    root = Path(root).absolute()
    collector = Collector(root)
    try:
        root_valid = not root.is_symlink() and root.resolve() == root and root.is_dir()
    except (OSError, RuntimeError):
        root_valid = False
    if not root_valid:
        collector.add("package.json", b"", "source-root-invalid")
    else:
        for name in ROOTS:
            path = root / name
            # Never traverse any link in a scope root's ancestors.
            current = root
            linked = False
            for part in Path(name).parts:
                current = current / part
                if current.is_symlink():
                    collector.add(name, b"", "source-symlink-unsupported")
                    linked = True
                    break
            if linked:
                continue
            if name == "package.json":
                if path.is_file():
                    collector.read(path, path.stat().st_size)
                else:
                    collector.add(name, b"", "package-root-missing")
            elif path.is_dir():
                collector.walk(path, name in {"scripts/04.deploy", "infra/04.deploy", ".github/workflows"})
            elif path.exists():
                collector.add(name, b"", "source-type-unsupported")
    result = {
        "schema": "source-inventory/v1", "collector_revision": digest(Path(__file__).read_bytes()),
        "scope": {"roots": ROOTS.copy(), "policy": "source-surface/v1"},
        "sources": sorted(collector.sources.values(), key=lambda item: item["id"]),
        "observations": sorted(collector.observations.values(), key=lambda item: item["id"]),
        "findings": [{"code": code, "source_id": source_id} for code, source_id in sorted(collector.findings)],
    }
    result["inventory_digest"] = digest(canonical(result))
    return result
