"""Bounded, owned local Docker execution for unsigned container observations."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.container-engine
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Observe exact local container images using restricted owned containers and redacted failures.
#   portability: {class: internal, targets: []}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.script.local-container
#     path: scripts/04.deploy/operational-realization-gate/local_container.py

import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import tempfile
import time
import uuid

DOCKER = "/usr/bin/docker"
ENDPOINT = "unix:///var/run/docker.sock"
IMAGE_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
BASE_PATTERN = re.compile(r"gcr\.io/distroless/nodejs22-debian12@sha256:[0-9a-f]{64}")
CONTAINER_PATTERN = re.compile(r"[0-9a-f]{64}")
OWNER_LABEL = "io.agentic.release-control.run"
NODE = "/nodejs/bin/node"
SERVER_COMMAND = [".cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-server.main.js"]
MAX_OUTPUT = 8 * 1024 * 1024
JOB_COMMAND = ["jobs/task.cjs", "success"]
SETTINGS = {
    "network": "none", "read_only": True, "user": "65532:65532",
    "capabilities": "none", "no_new_privileges": True, "memory_bytes": 536870912,
    "cpus": 1, "pids_limit": 128, "tmpfs_bytes": 16777216,
    "published_ports": [], "host_mounts": [], "restart": "no",
    "environment": {"HOST": "127.0.0.1", "PORT": "3000",
                    "PLATFORM_SMOKE_APP_NAME": "Release Control Local Container"},
    "health_timeout_seconds": 25, "shutdown_timeout_seconds": 10,
}

HEALTH_PROBE = r"""
const http = require('node:http');
const wanted = [['/livez', 'live'], ['/readyz', 'ready']];
const deadline = Date.now() + 20000;
function request(path, status) {
  return new Promise(resolve => {
    const req = http.get({host:'127.0.0.1',port:3000,path,timeout:1000}, res => {
      let body = ''; let bytes = 0;
      res.on('data', chunk => { bytes += chunk.length; if(bytes > 4096) res.destroy(); else body += chunk; });
      res.on('end', () => { try { resolve(res.statusCode === 200 && JSON.parse(body).status === status); } catch { resolve(false); } });
      res.on('error', () => resolve(false));
    });
    req.on('timeout', () => req.destroy());
    req.on('error', () => resolve(false));
  });
}
(async () => {
  const rows = [];
  for (const [path, status] of wanted) {
    let good = false;
    while (Date.now() < deadline && !(good = await request(path,status))) await new Promise(resolve => setTimeout(resolve,200));
    if (!good) process.exit(1);
    rows.push({path,status:200,body_status:status});
  }
  process.stdout.write(JSON.stringify(rows));
})().catch(() => process.exit(1));
"""

INVENTORY_PROBE = r"""
const fs = require('node:fs'); const crypto = require('node:crypto');
const rows = []; let total = 0;
function walk(relative, depth) {
  if(depth > 40) throw Error();
  const path = '/app' + (relative ? '/' + relative : '');
  const info = fs.lstatSync(path);
  if(info.isSymbolicLink()) throw Error();
  if(info.isDirectory()) {
    for(const name of fs.readdirSync(path).sort()) {
      if(!/^[A-Za-z0-9_.@+-]+$/.test(name) || name === '.' || name === '..') throw Error();
      walk(relative ? relative + '/' + name : name, depth+1);
    }
  } else {
    if(!info.isFile() || info.size > 16777216 || rows.length >= 20000) throw Error();
    const bytes = fs.readFileSync(path); total += bytes.length;
    if(bytes.length !== info.size || total > 268435456) throw Error();
    rows.push({path:relative,digest:'sha256:' + crypto.createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length});
  }
}
try { walk('',0); rows.sort((a,b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0); process.stdout.write(JSON.stringify(rows)); } catch { process.exit(1); }
"""


class EngineFailure(Exception):
    """Public failures contain only a fixed category, never CLI diagnostics."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _fail(code):
    raise EngineFailure("local-container-" + code)


def _image(value):
    if not isinstance(value, str) or not IMAGE_PATTERN.fullmatch(value):
        _fail("image-id-invalid")
    return value


def _base(value):
    if not isinstance(value, str) or not BASE_PATTERN.fullmatch(value):
        _fail("base-reference-invalid")
    return value


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("engine-output-invalid")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: _fail("engine-output-invalid"))
    except (ValueError, UnicodeError, RecursionError, TypeError):
        _fail("engine-output-invalid")


def _one(raw):
    result = _json(raw)
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
        _fail("engine-output-invalid")
    return result[0]


def _bounded_runner(argv, *, cwd, env, timeout, max_output):
    """Never keep unbounded process output in memory or inherit terminal streams."""
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_output + 1, max_output + 1))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    with tempfile.TemporaryFile(dir=cwd) as output, tempfile.TemporaryFile(dir=cwd) as errors:
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=errors, start_new_session=True,
                                       preexec_fn=limits)
        except OSError:
            _fail("engine-unavailable")
        try:
            process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as failure:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            if isinstance(failure, KeyboardInterrupt):
                raise
            _fail("engine-timeout")
        output.seek(0)
        errors.seek(0)
        stdout = output.read(max_output + 1)
        stderr = errors.read(max_output + 1)
        if len(stdout) > max_output or len(stderr) > max_output:
            _fail("engine-output-limit")
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


class Engine:
    """No ambient Docker contexts, credentials, custom flags or external endpoints."""

    def __init__(self, scratch, runner=None):
        path = Path(scratch)
        if not path.is_absolute() or path.is_symlink() or not path.is_dir():
            _fail("scratch-invalid")
        self.scratch = path.resolve(strict=True)
        self.private = Path(tempfile.mkdtemp(prefix="container-engine-", dir=self.scratch))
        self.config = self.private / "docker-config"
        self.config.mkdir(mode=0o700)
        (self.config / "config.json").write_text("{}\n")
        (self.private / "home").mkdir(mode=0o700)
        self.env = {"PATH": "/usr/bin:/bin", "HOME": str(self.private / "home"),
                    "DOCKER_CONFIG": str(self.config), "DOCKER_BUILDKIT": "1", "LC_ALL": "C"}
        self.runner = runner or _bounded_runner
        self._approved = set()
        self._owned = {}
        self._images = {}
        self._build_identities = {}

    def invoke(self, args, *, timeout=30, max_output=MAX_OUTPUT):
        """Execute only argument vectors constructed by the reviewed methods below."""
        if (not isinstance(args, list) or not args or any(type(arg) is not str or '\x00' in arg for arg in args)
                or tuple(args) not in self._approved):
            _fail("engine-command-unsupported")
        if type(timeout) not in (int, float) or not 0 < timeout <= 900 or type(max_output) is not int or not 1 <= max_output <= MAX_OUTPUT:
            _fail("engine-bound-invalid")
        result = self._execute(args, timeout=timeout, max_output=max_output)
        if result.returncode != 0:
            _fail("engine-command-failed")
        return result.stdout

    def _execute(self, args, *, timeout, max_output):
        """Shared bounded transport; callers construct reviewed vectors internally."""
        try:
            result = self.runner([DOCKER, "--host", ENDPOINT, *args], cwd=self.private,
                                 env=dict(self.env), timeout=timeout, max_output=max_output)
        except EngineFailure:
            raise
        except subprocess.TimeoutExpired:
            _fail("engine-timeout")
        except (OSError, subprocess.SubprocessError):
            _fail("engine-unavailable")
        if (not isinstance(result, subprocess.CompletedProcess) or type(result.returncode) is not int
                or type(result.stdout) is not bytes or type(result.stderr) is not bytes):
            _fail("engine-output-invalid")
        if len(result.stdout) > max_output or len(result.stderr) > max_output:
            _fail("engine-output-limit")
        return result

    def _call(self, args, **kwargs):
        key = tuple(args)
        self._approved.add(key)
        try:
            return self.invoke(args, **kwargs)
        finally:
            self._approved.discard(key)

    def version(self):
        value = _json(self._call(["version", "--format", "{{json .}}"], max_output=65536))
        result = {}
        for source, destination in (("Client", "client"), ("Server", "server")):
            section = value.get(source) if isinstance(value, dict) else None
            version = section.get("Version") if isinstance(section, dict) else None
            if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
                _fail("engine-version-invalid")
            result[destination] = version
        return result

    def acquire(self, runtime_image):
        """Explicit public download step; never called by build or runtime checks."""
        self._call(["pull", "--platform", "linux/amd64", _base(runtime_image)], timeout=900)
        return self.base_identity(runtime_image)

    def base_identity(self, runtime_image):
        value = _one(self._call(["image", "inspect", _base(runtime_image)]))
        if value.get("Os") != "linux" or value.get("Architecture") != "amd64":
            _fail("image-platform-mismatch")
        digests = value.get("RepoDigests")
        if (not isinstance(digests, list) or runtime_image not in digests or len(digests) > 16
                or any(not isinstance(item, str) or not BASE_PATTERN.fullmatch(item) for item in digests)):
            _fail("base-identity-mismatch")
        return {"image_id": _image(value.get("Id")), "repo_digests": sorted(set(digests)),
                "os": "linux", "architecture": "amd64"}

    def inspect_image(self, image_id):
        return self._inspect_image(image_id, SERVER_COMMAND)

    def inspect_job_image(self, image_id):
        """Accept either existing reviewed image default, preserving its identity."""
        return self._inspect_image(image_id, JOB_COMMAND, allow_server=True)

    def _inspect_image(self, image_id, command, *, allow_server=False):
        image_id = _image(image_id)
        value = _one(self._call(["image", "inspect", image_id]))
        config, rootfs = value.get("Config"), value.get("RootFS")
        if value.get("Id") != image_id or not isinstance(config, dict) or not isinstance(rootfs, dict):
            _fail("image-identity-mismatch")
        if value.get("Os") != "linux" or value.get("Architecture") != "amd64":
            _fail("image-platform-mismatch")
        if allow_server and config.get("Cmd") == SERVER_COMMAND:
            command = SERVER_COMMAND
        if (config.get("Entrypoint") != [NODE] or config.get("Cmd") != command
                or config.get("WorkingDir") != "/app" or not isinstance(config.get("User"), str)
                or config.get("User") not in {"nonroot", "65532", "65532:65532"}):
            _fail("image-command-mismatch")
        environment = self._safe_environment(config.get("Env"))
        layers = rootfs.get("Layers")
        if rootfs.get("Type") != "layers" or not isinstance(layers, list) or not layers or len(layers) > 128:
            _fail("image-layers-invalid")
        for layer in layers:
            _image(layer)
        result = {"image_id": image_id, "os": "linux", "architecture": "amd64", "user": config["User"],
                  "working_dir": "/app", "entrypoint": [NODE], "command": list(command),
                  "environment": environment, "rootfs_layers": layers}
        self._images[image_id] = result
        return result

    @staticmethod
    def _safe_environment(values):
        fixed = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                 "SSL_CERT_FILE": "/etc/ssl/certs/ca-certificates.crt", "NODE_ENV": "production",
                 "HOST": "0.0.0.0", "PORT": "3000", "LANG": "C.UTF-8"}
        result = {}
        if not isinstance(values, list) or len(values) > 16:
            _fail("image-environment-invalid")
        for row in values:
            if not isinstance(row, str) or "=" not in row:
                _fail("image-environment-invalid")
            key, value = row.split("=", 1)
            if key in result:
                _fail("image-environment-invalid")
            if key == "PLATFORM_SOURCE_COMMIT_SHA":
                if not re.fullmatch(r"[0-9a-f]{40}", value):
                    _fail("image-environment-invalid")
            elif key not in fixed or value != fixed[key]:
                _fail("image-environment-invalid")
            result[key] = value
        if not {"NODE_ENV", "HOST", "PORT", "PLATFORM_SOURCE_COMMIT_SHA"} <= result.keys():
            _fail("image-environment-invalid")
        return dict(sorted(result.items()))

    def build(self, context, dockerfile, runtime_image, source_commit):
        return self._build(context, dockerfile, runtime_image, source_commit, job_fixture=False)

    def build_job_fixture(self, context, dockerfile, runtime_image, source_commit):
        """Build an untagged conformance fixture using the existing pinned base."""
        return self._build(context, dockerfile, runtime_image, source_commit, job_fixture=True)

    def _build(self, context, dockerfile, runtime_image, source_commit, *, job_fixture):
        context, dockerfile = Path(context), Path(dockerfile)
        if (not context.is_dir() or context.is_symlink() or not dockerfile.is_file() or dockerfile.is_symlink()
                or not context.resolve().is_relative_to(self.scratch)
                or not dockerfile.resolve().is_relative_to(context.resolve())):
            _fail("build-path-invalid")
        if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
            _fail("source-commit-invalid")
        runtime_image = _base(runtime_image)
        self.base_identity(runtime_image)  # Absence fails before the offline build command.
        build_key = "build-" + uuid.uuid4().hex
        iidfile = self.private / (build_key + ".iid")
        metadatafile = self.private / (build_key + ".metadata.json")
        build_args = [] if job_fixture else ["--build-arg", "PAYLOAD_STAGE=verified",
            "--label", "org.opencontainers.image.revision=" + source_commit,
            "--label", "org.opencontainers.image.source=entity-builder-harness"]
        self._call(["build", "--platform", "linux/amd64", "--network", "none", "--no-cache",
                    "--provenance=false", "--pull=false", "--iidfile", str(iidfile),
                    "--metadata-file", str(metadatafile), "--file", str(dockerfile.resolve()),
                    *build_args, "--build-arg", "RUNTIME_NODE_IMAGE=" + runtime_image,
                    "--build-arg", "SOURCE_COMMIT_SHA=" + source_commit, str(context.resolve())], timeout=900)
        metadata = _json(self._build_output(metadatafile, 65536, "build-metadata-invalid"))
        if not isinstance(metadata, dict):
            _fail("build-metadata-invalid")
        if "containerimage.digest" not in metadata:
            _fail("build-manifest-unavailable")
        manifest_id = _image(metadata["containerimage.digest"])
        descriptor = metadata.get("containerimage.descriptor")
        if descriptor is not None and (not isinstance(descriptor, dict) or descriptor.get("digest") != manifest_id):
            _fail("build-identity-mismatch")
        # Buildx removes the standalone configuration digest when the Docker
        # containerd store prefers the manifest digest. The manifest descriptor
        # still binds its configuration digest in an exact annotation.
        config_value = metadata.get("containerimage.config.digest")
        if config_value is None and isinstance(descriptor, dict):
            annotations = descriptor.get("annotations")
            if isinstance(annotations, dict):
                config_value = annotations.get("config.digest")
        if config_value is None:
            _fail("build-configuration-unavailable")
        config_id = _image(config_value)
        if (isinstance(descriptor, dict) and isinstance(descriptor.get("annotations"), dict)
                and "config.digest" in descriptor["annotations"]
                and descriptor["annotations"]["config.digest"] != config_id):
            _fail("build-identity-mismatch")
        try:
            iid_raw = self._build_output(iidfile, 256, "image-id-file-missing")
            iid_text = iid_raw.decode("ascii").strip()
        except UnicodeError:
            _fail("image-id-invalid")
        if not iid_text:
            _fail("image-id-empty")
        iid = _image(iid_text)
        if iid not in {manifest_id, config_id}:
            _fail("build-identity-mismatch")
        # Buildx iidfiles can contain configuration digests that Docker's containerd
        # store cannot address. Its bound manifest digest selects the exact image.
        try:
            image_id = self._inspect_image(manifest_id, JOB_COMMAND if job_fixture else SERVER_COMMAND)["image_id"]
        except EngineFailure as error:
            if str(error) not in {"local-container-engine-command-failed", "local-container-image-identity-mismatch"} or config_id == manifest_id:
                raise
            image_id = self._inspect_image(config_id, JOB_COMMAND if job_fixture else SERVER_COMMAND)["image_id"]
        self._build_identities[image_id] = {"daemon_image_id": image_id,
            "manifest_digest": manifest_id, "configuration_digest": config_id}
        return image_id

    def build_identity(self, image_id):
        image_id = _image(image_id)
        if image_id not in self._build_identities:
            _fail("build-identity-unavailable")
        return dict(self._build_identities[image_id])

    @staticmethod
    def _build_output(path, limit, code):
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                    _fail(code)
                raw = stream.read(limit + 1)
                after = os.fstat(stream.fileno())
            if (len(raw) > limit or (before.st_size, before.st_mtime_ns, before.st_ino)
                    != (after.st_size, after.st_mtime_ns, after.st_ino)):
                _fail(code)
            return raw
        except OSError:
            _fail(code)

    def _create_arguments(self, image_id, name, token, *, inventory=False, command=None,
                          environment=None, retain_fixture_terminal=False):
        """Shared isolation recipe; retained logs are for the exact inert recovery fixture only."""
        if (type(retain_fixture_terminal) is not bool or type(token) is not str
                or not re.fullmatch(r'[0-9a-f]{32}', token) or name != 'release-control-' + token):
            _fail('container-reservation-invalid')
        _image(image_id)
        args = ["create", "--pull=never", "--name", name, "--label", OWNER_LABEL + "=" + token, "--network", "none",
                "--read-only", "--user", SETTINGS["user"], "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "512m",
                "--memory-swap", "512m", "--cpus", "1", "--pids-limit", "128", "--ipc", "none",
                "--restart", "no", "--stop-timeout", "10", "--log-driver", "local" if retain_fixture_terminal else "none", "--no-healthcheck"]
        if retain_fixture_terminal:
            args.extend(["--log-opt", "max-size=16k", "--log-opt", "max-file=1", "--log-opt", "compress=false"])
        runtime_environment = SETTINGS["environment"] if environment is None else environment
        for key, value in runtime_environment.items():
            args.extend(["--env", key + "=" + value])
        if inventory:
            args.extend(["--entrypoint", NODE])
        args.append(image_id)
        if inventory:
            args.extend(["-e", INVENTORY_PROBE])
        elif command is not None:
            args.extend(command)
        return args

    def _create(self, image_id, *, inventory=False, command=None, environment=None):
        _image(image_id)
        token = uuid.uuid4().hex
        name = "release-control-" + token
        args = self._create_arguments(image_id, name, token, inventory=inventory,
                                      command=command, environment=environment)
        self._owned[name] = {"token": token, "image": image_id, "id": None}
        try:
            raw = self._call(args, max_output=4096).decode("ascii").strip()
            if not CONTAINER_PATTERN.fullmatch(raw):
                _fail("container-id-invalid")
            self._owned[name]["id"] = raw
            self._container(name)
        except (EngineFailure, UnicodeError, KeyboardInterrupt):
            self._cleanup(name)
            raise
        return name

    def _container(self, name):
        owned = self._owned.get(name)
        if not owned:
            _fail("container-not-owned")
        value = _one(self._call(["container", "inspect", name]))
        config = value.get("Config")
        if (not isinstance(config, dict) or not isinstance(config.get("Labels"), dict)
                or config["Labels"].get(OWNER_LABEL) != owned["token"]
                or value.get("Name") != "/" + name or not isinstance(value.get("Id"), str)
                or not CONTAINER_PATTERN.fullmatch(value["Id"])
                or (owned["id"] is not None and value["Id"] != owned["id"])):
            _fail("container-ownership-mismatch")
        owned["id"] = value["Id"]
        return value

    def _restrictions(self, value, image_id, *, running, inventory=False, command=None, environment=None, allow_oom=False):
        config, host, state = value.get("Config", {}), value.get("HostConfig", {}), value.get("State", {})
        if not all(isinstance(row, dict) for row in (config, host, state)):
            _fail("engine-output-invalid")
        if value.get("Image") != image_id or config.get("Image") != image_id:
            _fail("container-image-mismatch")
        wanted_command = ["-e", INVENTORY_PROBE] if inventory else (SERVER_COMMAND if command is None else command)
        if (config.get("Entrypoint") != [NODE] or config.get("Cmd") != wanted_command
                or config.get("WorkingDir") != "/app" or config.get("User") != SETTINGS["user"]):
            _fail("container-command-mismatch")
        if (host.get("NetworkMode") != "none" or host.get("ReadonlyRootfs") is not True
                or host.get("Privileged") is not False or host.get("CapDrop") != ["ALL"]
                or host.get("CapAdd") or host.get("SecurityOpt") != ["no-new-privileges"]
                or host.get("Memory") != SETTINGS["memory_bytes"] or host.get("MemorySwap") != SETTINGS["memory_bytes"]
                or host.get("NanoCpus") != 1000000000 or host.get("PidsLimit") != SETTINGS["pids_limit"]
                or host.get("Binds") or host.get("PortBindings") or value.get("Mounts")
                or not isinstance(host.get("RestartPolicy"), dict) or host["RestartPolicy"].get("Name") != "no"
                or host.get("IpcMode") != "none"
                or host.get("Tmpfs") != {"/tmp": "rw,noexec,nosuid,nodev,size=16m"}):
            _fail("container-restriction-mismatch")
        observed = config.get("Env")
        runtime_environment = SETTINGS["environment"] if environment is None else environment
        expected_env = {**self._images[image_id]["environment"], **runtime_environment}
        if (not isinstance(observed, list) or len(observed) != len(expected_env)
                or any(not isinstance(row, str) for row in observed) or sorted(observed) != sorted(key + "=" + value for key, value in expected_env.items())):
            _fail("container-environment-mismatch")
        if (type(state.get("Running")) is not bool or (running is not None and state["Running"] is not running)
                or type(state.get("OOMKilled")) is not bool or (not allow_oom and state["OOMKilled"] is not False)):
            _fail("container-state-mismatch")
        return state

    def _cleanup(self, name):
        value = self._container(name)  # Confirm the random name AND random label AND ID before removal.
        removed = self._call(["rm", "--force", value["Id"]], max_output=4096).strip()
        if removed != value["Id"].encode("ascii"):
            _fail("cleanup-failed")
        remaining = self._call(["container", "ls", "--all", "--quiet", "--no-trunc", "--filter", "id=" + value["Id"]], max_output=4096)
        if remaining.strip():
            _fail("cleanup-failed")
        self._owned.pop(name)
        return True

    def inventory(self, image_id):
        return self._inventory(image_id, job_fixture=False)

    def inventory_job(self, image_id):
        return self._inventory(image_id, job_fixture=True)

    def _inventory(self, image_id, *, job_fixture):
        (self.inspect_job_image if job_fixture else self.inspect_image)(image_id)
        name = self._create(image_id, inventory=True)
        try:
            self._restrictions(self._container(name), image_id, running=False, inventory=True)
            raw = self._call(["start", "--attach", self._owned[name]["id"]], timeout=120)
            value = self._container(name)
            state = self._restrictions(value, image_id, running=False, inventory=True)
            if type(state.get("ExitCode")) is not int or state["ExitCode"] != 0:
                _fail("inventory-execution-failed")
            return self._inventory_rows(_json(raw))
        finally:
            self._cleanup(name)

    @staticmethod
    def _inventory_rows(rows):
        if not isinstance(rows, list) or not rows or len(rows) > 20000:
            _fail("inventory-invalid")
        total, previous = 0, None
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"path", "digest", "bytes"}:
                _fail("inventory-invalid")
            path, size = row.get("path"), row.get("bytes")
            if (not isinstance(path, str) or len(path) > 512 or not re.fullmatch(r"[A-Za-z0-9_./@+-]+", path)
                    or any(part in {"", ".", ".."} for part in path.split("/"))
                    or (previous is not None and path <= previous)
                    or type(size) is not int or not 0 <= size <= 16777216):
                _fail("inventory-invalid")
            _image(row.get("digest"))
            total += size
            previous = path
        if total > 268435456:
            _fail("inventory-limit")
        return rows

    def run_job(self, profile, expected_files):
        """Observe a bound finite command; never infer business effects from exit zero."""
        import finite_job_contracts as contracts

        contracts.validate_profile(profile)
        started = time.monotonic()
        run_id = uuid.uuid4().hex
        profile_hash = contracts.profile_digest(profile)
        image_id = profile["artifact"]["image_id"]
        command = list(profile["execution"]["command"])
        environment = {"RELEASE_CONTROL_PROFILE_DIGEST": profile_hash,
                       "RELEASE_CONTROL_RUN_ID": run_id}
        before_owned = set(self._owned)
        observation = {"outcome": "unknown", "failure_code": "observation-unavailable",
                       "exit_code": None, "oom_killed": None, "terminal_digest": None,
                       "checks": [], "cleanup_verified": False, "elapsed_ms": 0}
        stage = "image"
        try:
            self.inspect_job_image(image_id)
            stage = "payload"
            expected_files = self._inventory_rows(expected_files)
            payload_digest = contracts.digest(expected_files)
            if payload_digest != profile["artifact"]["payload_digest"]:
                _fail("job-payload-mismatch")
            if any(row["path"].lower().endswith((".ts", ".tsx", ".mts", ".cts")) for row in expected_files):
                _fail("job-payload-mismatch")
            if self.inventory_job(image_id) != expected_files:
                _fail("job-payload-mismatch")
            stage = "command"
            if command[0] not in {row["path"] for row in expected_files}:
                _fail("job-command-mismatch")
            stage = "isolation"
            name = self._create(image_id, command=command, environment=environment)
            self._restrictions(self._container(name), image_id, running=False,
                               command=command, environment=environment)
            stage = "start"
            limits = profile["limits"]
            attached = self._execute(["start", "--attach", self._owned[name]["id"]],
                                     timeout=limits["timeout_seconds"], max_output=limits["output_bytes"])
            stage = "observation"
            state = self._restrictions(self._container(name), image_id, running=None,
                                       command=command, environment=environment, allow_oom=True)
            observation["oom_killed"] = state["OOMKilled"]
            if (state["Running"] or type(state.get("ExitCode")) is not int
                    or not 0 <= state["ExitCode"] <= 255):
                _fail("job-observation-unavailable")
            observation["exit_code"] = state["ExitCode"]
            if state["OOMKilled"]:
                observation.update(outcome="failed", failure_code="oom-killed")
            elif state["ExitCode"] != 0:
                observation.update(outcome="failed", failure_code="exit-nonzero")
            elif attached.returncode != 0:
                observation.update(outcome="failed", failure_code="start-failed")
            else:
                stage = "terminal"
                checks = contracts.evaluate_terminal(attached.stdout, profile, run_id)
                observation.update(outcome="completed", failure_code=None, checks=checks,
                                   terminal_digest=contracts.terminal_digest(profile, run_id, checks))
        except KeyboardInterrupt:
            observation.update(outcome="interrupted", failure_code="interrupted")
        except contracts.ReleaseFailure as failure:
            code = "output-limit" if failure.code == "finite-job-output-limit" else "terminal-invalid"
            observation.update(outcome="failed", failure_code=code)
        except EngineFailure as failure:
            code = failure.code.removeprefix("local-container-")
            if code == "engine-timeout":
                observation.update(outcome="timed-out", failure_code="deadline-exceeded")
            elif code == "engine-output-limit":
                observation.update(outcome="failed", failure_code="output-limit")
            elif code == "engine-unavailable":
                observation.update(outcome="unknown", failure_code="engine-unavailable")
            elif code == "cleanup-failed":
                observation.update(outcome="unknown", failure_code="cleanup-failed")
            elif stage == "observation" and code in {"engine-command-failed", "engine-output-invalid", "job-observation-unavailable"}:
                observation.update(outcome="unknown", failure_code="observation-unavailable")
            else:
                mapped = {"image": "image-mismatch", "payload": "payload-mismatch",
                          "command": "command-mismatch", "isolation": "isolation-mismatch",
                          "start": "start-failed", "observation": "isolation-mismatch",
                          "terminal": "terminal-invalid"}
                observation.update(outcome="failed", failure_code=mapped[stage])
        finally:
            cleaned = True
            for owned_name in sorted(set(self._owned) - before_owned):
                try:
                    self._cleanup(owned_name)
                except (EngineFailure, KeyboardInterrupt):
                    cleaned = False
            observation["cleanup_verified"] = cleaned and not (set(self._owned) - before_owned)
            if not observation["cleanup_verified"]:
                observation.update(outcome="unknown", failure_code="cleanup-failed")
            elif observation["failure_code"] == "cleanup-failed":
                observation.update(outcome="unknown", failure_code="observation-unavailable")
            if observation["outcome"] != "completed":
                observation.update(checks=[], terminal_digest=None)
            observation["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        return contracts.make_result(profile, run_id, observation)

    def run_server(self, image_id):
        image = self.inspect_image(image_id)
        name = self._create(image_id)
        try:
            self._restrictions(self._container(name), image_id, running=False)
            self._call(["start", self._owned[name]["id"]], max_output=4096)
            self._restrictions(self._container(name), image_id, running=True)
            checks = _json(self._call(["exec", self._owned[name]["id"], NODE, "-e", HEALTH_PROBE], timeout=25, max_output=4096))
            expected = [{"path": "/livez", "status": 200, "body_status": "live"},
                        {"path": "/readyz", "status": 200, "body_status": "ready"}]
            if checks != expected:
                _fail("health-evidence-invalid")
            self._restrictions(self._container(name), image_id, running=True)
            try:
                node_version = self._call(["exec", self._owned[name]["id"], NODE, "--version"], max_output=4096).decode("ascii").strip()
            except UnicodeError:
                _fail("runtime-version-invalid")
            if not re.fullmatch(r"v22\.[0-9]+\.[0-9]+", node_version):
                _fail("runtime-version-invalid")
            self._call(["stop", "--time", "10", self._owned[name]["id"]], timeout=20, max_output=4096)
            state = self._restrictions(self._container(name), image_id, running=False)
            if type(state.get("ExitCode")) is not int or state["ExitCode"] != 0:
                _fail("shutdown-failed")
            receipt = {"image_id": image_id, "entrypoint": image["entrypoint"], "command": image["command"],
                       "settings": json.loads(json.dumps(SETTINGS)), "checks": checks,
                       "shutdown": {"signal": "SIGTERM", "exit_code": 0, "oom_killed": False},
                       "node_version": node_version, "verdict": "passed"}
        finally:
            cleaned = self._cleanup(name)
        receipt["cleanup_verified"] = cleaned
        return receipt
