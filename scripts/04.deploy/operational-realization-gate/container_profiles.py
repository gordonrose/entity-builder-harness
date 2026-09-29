"""Discover content-bound command obligations without running target commands."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.container-profiles
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Account for the selected image and every declared task container as unqualified command obligations.
#   portability: {class: target-specific, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.container-profiles
#     path: scripts/04.deploy/operational-realization-gate/test_container_profiles.py

import hashlib
import json
import os
from pathlib import Path
import re
import stat

import yaml

import release_compiler as release


DOCKERFILE = "infra/04.deploy/03.product/image/Dockerfile"
TEMPLATE = "infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/service.yml"
PREFIX = ".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/"
SERVER = PREFIX + "kanbien-platform-server.main.js"
COMMAND_KINDS = {
    PREFIX + "kanbien-platform-server.main.js": "service",
    PREFIX + "kanbien-platform-worker.main.js": "service",
    PREFIX + "kanbien-platform-relay.main.js": "service",
    **{PREFIX + "kanbien-platform-postgresql-" + name + ".main.js": "finite-task"
       for name in ("bootstrap", "migration", "relay", "worker", "restore-verify")},
}
MAX_BYTES = 512 * 1024
MAX_NODES = 20000
MAX_DEPTH = 32
MAX_CONTAINERS = 128
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")
PATH = re.compile(r"[A-Za-z0-9_./@+-]+\Z")
IMAGE = re.compile(r"[a-z0-9][a-z0-9._:/-]*@sha256:([0-9a-f]{64})\Z")


def _fail(code="container-profile-declaration-invalid"):
    raise release.ReleaseFailure(code)


def _safe_path(value):
    return (type(value) is str and len(value) <= 1024 and PATH.fullmatch(value)
            and all(part not in {"", ".", ".."} for part in value.split("/")))


class _Loader(yaml.BaseLoader):
    """Keep CloudFormation expressions inert, with no aliases or duplicate keys."""

    def __init__(self, stream):
        super().__init__(stream)
        self.profile_nodes = 0
        self.profile_depth = 0

    def compose_node(self, parent, index):
        event = self.peek_event()
        tag = getattr(event, "tag", None)
        if tag is not None and tag.startswith("tag:") and tag not in {
                "tag:yaml.org,2002:map", "tag:yaml.org,2002:seq", "tag:yaml.org,2002:str"}:
            _fail("container-profile-tag-unsupported")
        if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
            _fail("container-profile-alias-unsupported")
        self.profile_nodes += 1
        self.profile_depth += 1
        if self.profile_nodes > MAX_NODES or self.profile_depth > MAX_DEPTH:
            _fail("container-profile-document-limit")
        try:
            return super().compose_node(parent, index)
        finally:
            self.profile_depth -= 1

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            _fail()
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if type(key) is not str or key in result or key == "<<":
                _fail("container-profile-key-invalid")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _intrinsic(loader, suffix, node):
    allowed = {"Ref", "Sub", "GetAtt", "Join", "Select", "Split", "FindInMap",
               "ImportValue", "If", "Equals", "And", "Or", "Not", "Condition",
               "Base64", "GetAZs", "Cidr", "Transform", "Length", "ToJsonString"}
    if suffix not in allowed:
        _fail("container-profile-tag-unsupported")
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        value = loader.construct_mapping(node)
    else:
        _fail()
    return {suffix if suffix in {"Ref", "Condition"} else "Fn::" + suffix: value}


_Loader.add_multi_constructor("!", _intrinsic)


def _read(root, relative):
    """Read a fixed descriptor using no-follow directory and file descriptors."""
    directory_fd = None
    file_fd = None
    try:
        directory_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parts = relative.split("/")
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                          dir_fd=directory_fd)
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            _fail("container-profile-source-unsafe")
        with os.fdopen(file_fd, "rb") as stream:
            file_fd = None
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            _fail("container-profile-document-limit")
        decoded = raw.decode("utf-8")
        if "\0" in decoded:
            _fail("container-profile-source-unsafe")
        return decoded, "sha256:" + hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError):
        _fail("container-profile-source-unreadable")
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _docker_command(text):
    """Read exec-form CMD in the final stage; HEALTHCHECK CMD is not a default."""
    instructions = []
    stage_count = 0
    pending = ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        line = pending + line
        pending = ""
        pieces = line.split(None, 1)
        if len(pieces) != 2:
            _fail("container-profile-dockerfile-unsupported")
        instruction, value = pieces[0].upper(), pieces[1]
        if instruction == "FROM":
            stage_count += 1
            instructions = []
        else:
            instructions.append((instruction, value))
    if pending or not stage_count:
        _fail("container-profile-dockerfile-unsupported")
    commands = [value for instruction, value in instructions if instruction == "CMD"]
    if len(commands) != 1:
        _fail("container-profile-docker-command-invalid")
    try:
        command = json.loads(commands[0])
    except (ValueError, RecursionError):
        _fail("container-profile-docker-command-invalid")
    if command != [SERVER]:
        _fail("container-profile-docker-command-unsupported")
    # Entrypoint changes alter the effective command; this collector supports
    # the reviewed inherited Node entrypoint or its explicit identical form.
    entries = [value for instruction, value in instructions if instruction == "ENTRYPOINT"]
    if entries:
        try:
            valid_entry = len(entries) == 1 and json.loads(entries[0]) == ["/nodejs/bin/node"]
        except (ValueError, RecursionError):
            valid_entry = False
        if not valid_entry:
            _fail("container-profile-docker-entrypoint-unsupported")
    return command


def _mapping(value):
    if type(value) is not dict:
        _fail()
    return value


def _product_command(container, default):
    if "EntryPoint" in container:
        _fail("container-profile-entrypoint-unsupported")
    if "WorkingDirectory" in container and container["WorkingDirectory"] != "/app":
        _fail("container-profile-working-directory-unsupported")
    command = container.get("Command", default)
    if (type(command) is not list or len(command) != 1 or not _safe_path(command[0])
            or command[0] not in COMMAND_KINDS):
        _fail("container-profile-command-unsupported")
    return list(command)


def discover(root):
    """Return every selected container obligation, always pending and source-bound.

    External-image commands are deliberately unresolved here: their empty
    command list means inherited/external, never an executed or passing task.
    AWS declarations retain their own rows even when they inherit image CMD.
    No environment or secret reference value is emitted.
    """
    try:
        root = Path(root).resolve(strict=True)
    except (OSError, ValueError, RuntimeError, TypeError):
        _fail("container-profile-source-unreadable")
    docker, docker_digest = _read(root, DOCKERFILE)
    template, template_digest = _read(root, TEMPLATE)
    default = _docker_command(docker)
    try:
        document = yaml.load(template, Loader=_Loader)
    except (yaml.YAMLError, RecursionError, ValueError):
        _fail("container-profile-document-invalid")
    resources = _mapping(_mapping(document).get("Resources"))
    rows = [{"id": "image-default", "command": default,
             "source_path": DOCKERFILE, "source_digest": docker_digest,
             "kind": "service", "status": "pending", "image_scope": "product",
             "reason": "local-runtime-unverified"}]
    task_count = 0
    for resource_id, resource in sorted(resources.items()):
        resource = _mapping(resource)
        resource_type = resource.get("Type")
        if type(resource_type) is not str:
            _fail("container-profile-resource-type-unsupported")
        if resource_type != "AWS::ECS::TaskDefinition":
            continue
        task_count += 1
        if not IDENTIFIER.fullmatch(resource_id):
            _fail("container-profile-identifier-invalid")
        properties = _mapping(resource.get("Properties"))
        containers = properties.get("ContainerDefinitions")
        if type(containers) is not list or not containers:
            _fail("container-profile-containers-unsupported")
        seen = set()
        for container in containers:
            container = _mapping(container)
            name = container.get("Name")
            if type(name) is not str or not IDENTIFIER.fullmatch(name) or name in seen:
                _fail("container-profile-identifier-invalid")
            seen.add(name)
            if "Image" not in container:
                _fail("container-profile-image-missing")
            image = container["Image"]
            product = image in ({"Ref": "ImageUri"}, {"Ref": "CandidateImageUri"})
            command = _product_command(container, default) if product else []
            identifier = "task-" + resource_id + "-" + name
            if len(identifier) > 160:
                _fail("container-profile-identifier-invalid")
            row = {"id": identifier, "command": command,
                   "source_path": TEMPLATE, "source_digest": template_digest,
                   "kind": COMMAND_KINDS[command[0]] if product else "service",
                   "status": "pending", "image_scope": "product" if product else "external",
                   "reason": "target-runtime-unqualified" if product else "unresolved-image"}
            if not product and type(image) is str and (match := IMAGE.fullmatch(image)):
                row["image_digest"] = "sha256:" + match[1]
                row["reason"] = "external-image-unqualified"
            rows.append(row)
            if len(rows) > MAX_CONTAINERS + 1:
                _fail("container-profile-document-limit")
    if not task_count or len({row["id"] for row in rows}) != len(rows):
        _fail("container-profile-coverage-invalid")
    return sorted(rows, key=lambda row: row["id"])


def require_payload(profiles, files):
    """Require every product command in the exact /app-relative payload manifest."""
    if type(profiles) is not list or not profiles or type(files) is not list:
        _fail("container-profile-payload-invalid")
    paths = set()
    for item in files:
        if type(item) is not dict or not _safe_path(item.get("path")) or item["path"] in paths:
            _fail("container-profile-payload-invalid")
        paths.add(item["path"])
    ids = set()
    for row in profiles:
        if (type(row) is not dict or type(row.get("id")) is not str or row["id"] in ids
                or row.get("image_scope") not in {"product", "external"}):
            _fail("container-profile-payload-invalid")
        ids.add(row["id"])
        command = row.get("command")
        if row["image_scope"] == "product":
            if (type(command) is not list or len(command) != 1 or not _safe_path(command[0])
                    or command[0] not in COMMAND_KINDS or command[0] not in paths):
                _fail("container-profile-command-missing")
        elif command != [] or row.get("status") != "pending":
            _fail("container-profile-payload-invalid")
    return profiles
