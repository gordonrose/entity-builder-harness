"""Pinned local build tools; execution is delegated to a caller-owned sandbox.

Acquisition performs only fixed, hash-bound public downloads. Installation never
executes a subprocess itself and requires the no-network execution callback.
"""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-locked-toolchain
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify pinned Node and npm dependency bytes before isolated local compilation.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files, network]
#   used_by:
#   - id: deploy.script.local-build-runner
#     path: scripts/04.deploy/operational-realization-gate/local_build.py

import base64
import functools
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import tarfile
import urllib.error
import urllib.request

from jsonschema import Draft202012Validator
import release_compiler as release

DIRECTORY = Path(__file__).resolve().parent
SCHEMA = release.SCHEMA_DIR / "local-build-toolchain.schema.yml"
LOCK = DIRECTORY / "node-toolchain.lock.json"
MAX_JSON = 1024 * 1024
MAX_ARCHIVE = 80 * 1024 * 1024
MAX_PACKAGE = 30 * 1024 * 1024
MAX_EXPANDED = 300 * 1024 * 1024
MAX_MEMBERS = 20000
NAME = re.compile(r"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?")
HASH = re.compile(r"[0-9a-f]{64}")


class ToolchainFailure(Exception):
    """Only fixed, non-sensitive failure codes cross the public boundary."""


def safe_boundary(function):
    @functools.wraps(function)
    def invoke(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ToolchainFailure:
            raise
        except Exception:
            _fail("input-invalid")
    return invoke


def _fail(code):
    raise ToolchainFailure("locked-toolchain-" + code)


def _sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _digest(value):
    return "sha256:" + _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _read(path, limit=MAX_JSON):
    """Walk every parent through descriptors, refusing links and special files."""
    path = Path(os.path.abspath(path))
    descriptor = None
    try:
        descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        for part in path.parts[1:-1]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        following = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                            dir_fd=descriptor)
        os.close(descriptor)
        descriptor = following
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            _fail("file-invalid")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            value = stream.read(limit + 1)
        if len(value) > limit:
            _fail("file-limit")
        return value
    except OSError:
        _fail("file-unavailable")
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _json(payload):
    if not isinstance(payload, (bytes, str)) or len(payload) > MAX_JSON:
        _fail("json-limit")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                _fail("json-duplicate")
            result[key] = value
        return result
    try:
        value = json.loads(payload, object_pairs_hook=pairs,
                           parse_constant=lambda _: _fail("json-invalid"))
        release.bounded_json(value, max_nodes=100000)
        return value
    except ToolchainFailure:
        raise
    except Exception:
        _fail("json-invalid")


@safe_boundary
def validate_contract(contract):
    try:
        schema = release.load_document(SCHEMA, "toolchain-schema-unavailable")
        if (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
                or schema.get("$id") != "urn:release-control:local-build-toolchain:v1"):
            _fail("schema-version")
        pending = [schema]
        while pending:
            item = pending.pop()
            if isinstance(item, dict):
                if any(key in item for key in ("$ref", "$dynamicRef", "$recursiveRef")):
                    _fail("schema-reference")
                if item.get("type") == "object" or "properties" in item:
                    if (item.get("additionalProperties") is not False
                            or set(item.get("required", [])) != set(item.get("properties", {}))):
                        _fail("schema-open")
                pending.extend(item.values())
            elif isinstance(item, list):
                pending.extend(item)
        Draft202012Validator.check_schema(schema)
        if next(Draft202012Validator(schema).iter_errors(contract), None):
            _fail("contract-invalid")
        return contract
    except ToolchainFailure:
        raise
    except Exception:
        _fail("schema-invalid")


@safe_boundary
def load_toolchain(path=LOCK):
    return validate_contract(_json(_read(path)))


@safe_boundary
def validate_platform(system=None, machine=None, libc=None):
    system = platform.system() if system is None else system
    machine = platform.machine() if machine is None else machine
    libc = platform.libc_ver() if libc is None else libc
    try:
        if (system != "Linux" or machine != "x86_64" or libc[0] != "glibc"
                or tuple(int(part) for part in libc[1].split(".")) < (2, 28)):
            _fail("platform-unsupported")
    except (TypeError, ValueError, IndexError):
        _fail("platform-unsupported")


def _relative(value):
    if (not isinstance(value, str) or not value or len(value) > 400
            or any(ord(c) < 32 for c in value) or "\\" in value
            or value.startswith("/") or any(p in ("", ".", "..") for p in value.split("/"))):
        _fail("path-invalid")
    return value


def _integrity(value, payload=None):
    if not isinstance(value, str) or not value.startswith("sha512-"):
        _fail("integrity-invalid")
    try:
        raw = base64.b64decode(value[7:], validate=True)
    except Exception:
        _fail("integrity-invalid")
    if len(raw) != 64 or base64.b64encode(raw).decode() != value[7:]:
        _fail("integrity-invalid")
    if payload is not None and hashlib.sha512(payload).digest() != raw:
        _fail("package-hash-mismatch")


@safe_boundary
def inspect_project(root, contract=None):
    """Bind the reviewed flat npm closure and every workspace manifest."""
    contract = validate_contract(contract) if contract is not None else load_toolchain()
    root = Path(root)
    manifest_bytes, lock_bytes = _read(root / "package.json"), _read(root / "package-lock.json")
    if _sha(lock_bytes) != contract["dependencies"]["lock_sha256"]:
        _fail("dependency-lock-mismatch")
    manifest, lock = _json(manifest_bytes), _json(lock_bytes)
    if not isinstance(lock, dict) or lock.get("lockfileVersion") != 3:
        _fail("dependency-lock-version")
    packages = lock.get("packages")
    if not isinstance(packages, dict) or len(packages) > 2048 or "" not in packages:
        _fail("dependency-closure-invalid")
    workspace_patterns = manifest.get("workspaces")
    if (not isinstance(workspace_patterns, list) or not workspace_patterns
            or any(not isinstance(p, str) or not re.fullmatch(r"(?:[a-z0-9-]+/)+(?:\*/)*\*", p)
                   for p in workspace_patterns)):
        _fail("workspace-pattern-unsupported")
    for filename in (".npmrc", "npm-shrinkwrap.json"):
        if os.path.lexists(root / filename):
            _fail("project-configuration-unsupported")
    for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        if manifest.get(field, {}) != packages[""].get(field, {}):
            _fail("manifest-lock-mismatch")
    if workspace_patterns != packages[""].get("workspaces"):
        _fail("workspace-lock-mismatch")
    external, links, workspaces = [], [], []
    bindings = [{"path": "package.json", "sha256": _sha(manifest_bytes)},
                {"path": "package-lock.json", "sha256": _sha(lock_bytes)}]
    for location, entry in sorted(packages.items()):
        if not location:
            continue
        _relative(location)
        if not isinstance(entry, dict):
            _fail("dependency-record-invalid")
        if location.startswith("node_modules/"):
            name = location[len("node_modules/"):]
            if not NAME.fullmatch(name):
                _fail("dependency-layout-unsupported")
            if entry.get("link") is True:
                target = _relative(entry.get("resolved"))
                if set(entry) != {"resolved", "link"} or target.startswith("node_modules/"):
                    _fail("workspace-link-invalid")
                links.append({"path": location, "target": target, "name": name})
                continue
            version, url = entry.get("version"), entry.get("resolved")
            if not isinstance(version, str) or not VERSION.fullmatch(version):
                _fail("dependency-version-invalid")
            expected_url = "https://registry.npmjs.org/" + name + "/-/" + name.split("/")[-1] + "-" + version + ".tgz"
            if url != expected_url or any(entry.get(key) for key in ("inBundle", "hasInstallScript", "os", "cpu")):
                _fail("dependency-source-unsupported")
            _integrity(entry.get("integrity"))
            external.append({"path": location, "name": name, "version": version,
                             "url": url, "integrity": entry["integrity"]})
        else:
            source = _read(root / location / "package.json")
            actual = _json(source)
            if (not isinstance(actual, dict) or not NAME.fullmatch(actual.get("name", ""))
                    or actual.get("version") != entry.get("version")):
                _fail("workspace-manifest-invalid")
            for field in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                if actual.get(field, {}) != entry.get(field, {}):
                    _fail("workspace-manifest-lock-mismatch")
            if any(key in actual.get("scripts", {}) for key in
                   ("preinstall", "install", "postinstall", "prepare", "prepublish")):
                _fail("workspace-lifecycle-unsupported")
            if os.path.lexists(root / location / ".npmrc"):
                _fail("project-configuration-unsupported")
            workspaces.append({"path": location, "name": actual["name"]})
            bindings.append({"path": location + "/package.json", "sha256": _sha(source)})
    expected_workspaces = set()
    walked = 0
    for pattern in workspace_patterns:
        candidates = [root]
        for component in pattern.split("/"):
            following = []
            for directory in candidates:
                if directory.is_symlink():
                    _fail("workspace-path-invalid")
                entries = list(directory.iterdir()) if component == "*" else [directory / component]
                walked += len(entries)
                if walked > 4096:
                    _fail("workspace-limit")
                for candidate in entries:
                    if candidate.is_symlink():
                        _fail("workspace-path-invalid")
                    if candidate.is_dir():
                        following.append(candidate)
            candidates = following
        for candidate in candidates:
            if os.path.lexists(candidate / "package.json"):
                expected_workspaces.add(candidate.relative_to(root).as_posix())
    if expected_workspaces != {w["path"] for w in workspaces}:
        _fail("workspace-membership-mismatch")
    if ({(w["name"], w["path"]) for w in workspaces}
            != {(link["name"], link["target"]) for link in links}
            or len({w["name"] for w in workspaces}) != len(workspaces)):
        _fail("workspace-link-mismatch")
    if (len(external) != contract["dependencies"]["external_packages"]
            or len(workspaces) != contract["dependencies"]["workspaces"]):
        _fail("dependency-count-mismatch")
    ts = next((entry for entry in external if entry["name"] == "typescript"), None)
    if (ts is None or ts["version"] != contract["typescript"]["version"]
            or manifest.get("devDependencies", {}).get("typescript") != ts["version"]):
        _fail("typescript-pin-mismatch")
    result = {"lock_sha256": _sha(lock_bytes), "bindings": bindings,
              "external": external, "workspaces": workspaces, "links": links}
    result["closure_digest"] = _digest(result)
    return result


def _archive(payload, *, node=False):
    """Parse and bound all members before any extraction or package execution."""
    try:
        archive = tarfile.open(fileobj=io.BytesIO(payload), mode="r:*")
        members, names, total = [], set(), 0
        for member in archive:
            if len(members) >= MAX_MEMBERS:
                _fail("archive-limit")
            name = _relative(member.name.rstrip("/"))
            if name in names:
                _fail("archive-duplicate")
            names.add(name)
            total += member.size
            if total > MAX_EXPANDED or member.size < 0:
                _fail("archive-limit")
            if not (member.isfile() or member.isdir() or (node and member.issym())):
                _fail("archive-member-unsupported")
            if member.mode & 0o6000:
                _fail("archive-mode-unsupported")
            members.append(member)
        roots = {member.name.split("/")[0] for member in members}
        if len(roots) != 1:
            _fail("archive-root-invalid")
        root = next(iter(roots))
        if node and root != "node-v22.23.3-linux-x64":
            _fail("archive-root-invalid")
        for member in members:
            if member.issym():
                expected = {"bin/npm": "../lib/node_modules/npm/bin/npm-cli.js",
                            "bin/npx": "../lib/node_modules/npm/bin/npx-cli.js",
                            "bin/corepack": "../lib/node_modules/corepack/dist/corepack.js"}
                relative = member.name[len(root) + 1:]
                if relative not in expected or member.linkname != expected[relative]:
                    _fail("archive-link-invalid")
        return archive, members, root
    except ToolchainFailure:
        raise
    except Exception:
        _fail("archive-invalid")


@safe_boundary
def prepare_toolchain(cache_dir, destination, contract=None):
    contract = validate_contract(contract) if contract is not None else load_toolchain()
    validate_platform()
    payload = _read(Path(cache_dir) / contract["node"]["filename"], MAX_ARCHIVE)
    if _sha(payload) != contract["node"]["sha256"]:
        _fail("node-hash-mismatch")
    archive, members, archive_root = _archive(payload, node=True)
    destination = Path(destination)
    try:
        destination.mkdir(mode=0o700, parents=False, exist_ok=False)
        # Only the three fixed internal links above are accepted; data filtering
        # also rejects link traversal and strips ownership and unsafe mode bits.
        archive.extractall(destination, members=members, filter="data")
        bundle = destination / archive_root
        npm = _json(_read(bundle / "lib/node_modules/npm/package.json"))
        if npm.get("version") != contract["npm"]["version"]:
            _fail("npm-pin-mismatch")
        return {"bundle_root": str(bundle), "node": str(bundle / "bin/node"),
                "npm_cli": str(bundle / "lib/node_modules/npm/bin/npm-cli.js"),
                "node_sha256": _sha(_read(bundle / "bin/node", MAX_EXPANDED)),
                "contract_digest": _digest(contract)}
    except ToolchainFailure:
        raise
    except Exception:
        _fail("node-extraction-failed")
    finally:
        archive.close()


@safe_boundary
def verify_package_cache(cache_dir, closure):
    cache_dir = Path(cache_dir)
    manifest = _json(_read(cache_dir / "verified-artifacts.json"))
    if not isinstance(manifest, dict) or manifest.get("package_lock_sha256") != closure["lock_sha256"]:
        _fail("cache-lock-mismatch")
    rows = manifest.get("packages")
    if not isinstance(rows, list) or len(rows) != len(closure["external"]):
        _fail("cache-closure-mismatch")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("path") in indexed:
            _fail("cache-record-invalid")
        indexed[row.get("path")] = row
    if set(indexed) != {entry["path"] for entry in closure["external"]}:
        _fail("cache-closure-mismatch")
    result = []
    total = 0
    for entry in closure["external"]:
        row = indexed[entry["path"]]
        if any(row.get(key) != entry[key] for key in ("version", "url", "integrity")):
            _fail("cache-binding-mismatch")
        filename = row.get("filename")
        if not isinstance(filename, str) or not re.fullmatch(r"[0-9a-f]{64}\.tgz", filename):
            _fail("cache-filename-invalid")
        payload = _read(cache_dir / filename, MAX_PACKAGE)
        total += len(payload)
        if total > MAX_EXPANDED or _sha(payload) + ".tgz" != filename:
            _fail("cache-bytes-invalid")
        _integrity(entry["integrity"], payload)
        archive, members, archive_root = _archive(payload)
        files = {}
        try:
            for member in members:
                if member.isfile():
                    relative = member.name[len(archive_root) + 1:]
                    if not relative:
                        _fail("package-layout-invalid")
                    files[relative] = _sha(archive.extractfile(member).read())
            member = archive.getmember(archive_root + "/package.json")
            actual = _json(archive.extractfile(member).read(MAX_JSON + 1))
            if actual.get("name") != entry["name"] or actual.get("version") != entry["version"]:
                _fail("package-identity-mismatch")
        except ToolchainFailure:
            raise
        except Exception:
            _fail("package-manifest-invalid")
        finally:
            archive.close()
        result.append({**entry, "archive": str(cache_dir / filename), "files": files})
    return result


@safe_boundary
def child_environment(root, toolchain):
    """Build an allowlist from scratch; inherit no credentials or user settings."""
    base = Path(root) / ".release-control-toolchain"
    return {"PATH": str(Path(toolchain["node"]).parent) + ":/usr/bin:/bin",
            "HOME": str(base / "home"), "TMPDIR": str(base / "tmp"),
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
            "npm_config_userconfig": str(base / "user.npmrc"),
            "npm_config_globalconfig": str(base / "global.npmrc"),
            "npm_config_cache": str(base / "cache"),
            "npm_config_update_notifier": "false", "npm_config_audit": "false",
            "npm_config_fund": "false", "npm_config_ignore_scripts": "true",
            "npm_config_offline": "true", "npm_config_progress": "false",
            "npm_config_registry": "https://registry.npmjs.org/",
            "npm_config_script_shell": "/bin/false", "npm_config_engine_strict": "true"}


def _execute(execute, argv, root, environment, expected=None):
    try:
        response = execute(argv, Path(root), dict(environment))
        code = response.get("returncode") if isinstance(response, dict) else response.returncode
        stdout = response.get("stdout", "") if isinstance(response, dict) else response.stdout
        if code != 0:
            _fail("command-failed")
        if expected is not None:
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="strict")
            if stdout.strip() != expected:
                _fail("runtime-version-mismatch")
    except ToolchainFailure:
        raise
    except Exception:
        _fail("execution-failed")


@safe_boundary
def verify_installed(root, closure, packages):
    root = Path(root)
    found = set()
    module_root = root / "node_modules"
    try:
        for top in module_root.iterdir():
            if top.name in (".bin", ".package-lock.json"):
                continue
            if top.name.startswith("@"):
                if top.is_symlink() or not top.is_dir():
                    _fail("installed-layout-invalid")
                found.update(path.relative_to(root).as_posix() for path in top.iterdir())
            else:
                found.add(top.relative_to(root).as_posix())
        if found != {entry["path"] for entry in closure["external"] + closure["links"]}:
            _fail("installed-closure-mismatch")
        bin_root = module_root / ".bin"
        expected_bins = {"tsc": "../typescript/bin/tsc", "tsserver": "../typescript/bin/tsserver"}
        if bin_root.is_symlink() or {path.name for path in bin_root.iterdir()} != set(expected_bins):
            _fail("installed-bin-mismatch")
        for name, target in expected_bins.items():
            if not (bin_root / name).is_symlink() or os.readlink(bin_root / name) != target:
                _fail("installed-bin-mismatch")
        if (module_root / ".package-lock.json").is_symlink():
            _fail("installed-layout-invalid")
        for link in closure["links"]:
            path = root / link["path"]
            if not path.is_symlink() or path.resolve() != (root / link["target"]).resolve():
                _fail("installed-workspace-link-mismatch")
        installed = []
        for entry in packages:
            package_root = root / entry["path"]
            if package_root.is_symlink() or not package_root.is_dir():
                _fail("installed-package-invalid")
            files = {}
            for directory, directories, filenames in os.walk(package_root, followlinks=False):
                for name in directories:
                    if (Path(directory) / name).is_symlink():
                        _fail("installed-package-link")
                for name in filenames:
                    path = Path(directory) / name
                    relative = path.relative_to(package_root).as_posix()
                    if relative not in entry["files"]:
                        _fail("installed-package-files-mismatch")
                    files[relative] = _sha(_read(path, MAX_PACKAGE))
            if files != entry["files"]:
                _fail("installed-package-files-mismatch")
            installed.append({"path": entry["path"], "version": entry["version"],
                              "files_digest": _digest(files)})
        for binding in closure["bindings"]:
            if _sha(_read(root / binding["path"])) != binding["sha256"]:
                _fail("source-manifest-changed")
        return {"external_packages": len(packages), "workspace_links": len(closure["links"]),
                "installed_digest": _digest(installed), "closure_digest": closure["closure_digest"]}
    except ToolchainFailure:
        raise
    except Exception:
        _fail("installed-verification-failed")


@safe_boundary
def install_dependencies(root, toolchain, cache_dir, closure, execute):
    """Install solely through the parent's bounded no-network sandbox callback."""
    root = Path(root)
    if not callable(execute) or os.path.lexists(root / "node_modules"):
        _fail("installation-destination-invalid")
    for binding in closure["bindings"]:
        if _sha(_read(root / binding["path"])) != binding["sha256"]:
            _fail("source-manifest-changed")
    packages = verify_package_cache(cache_dir, closure)
    base = root / ".release-control-toolchain"
    try:
        base.mkdir(mode=0o700, exist_ok=False)
        for name in ("home", "tmp", "cache"):
            (base / name).mkdir(mode=0o700)
        for name in ("user.npmrc", "global.npmrc"):
            (base / name).write_text("")
    except OSError:
        _fail("installation-destination-invalid")
    environment = child_environment(root, toolchain)
    command = [toolchain["node"], toolchain["npm_cli"]]
    _execute(execute, [toolchain["node"], "--version"], root, environment, "v22.23.3")
    _execute(execute, command + ["--version"], root, environment, "10.9.9")
    _execute(execute, command + ["cache", "add"] + [entry["archive"] for entry in packages]
             + ["--ignore-scripts", "--offline", "--no-audit", "--no-fund"], root, environment)
    _execute(execute, command + ["ci", "--offline", "--ignore-scripts", "--no-audit", "--no-fund",
                                "--include=dev", "--include=optional", "--include=peer",
                                "--workspaces=true", "--include-workspace-root=true",
                                "--install-strategy=hoisted", "--strict-peer-deps"], root, environment)
    _execute(execute, [toolchain["node"], str(root / "node_modules/typescript/bin/tsc"), "--version"],
             root, environment, "Version 5.9.3")
    return {"schema": "local-build-installation/v1", "authorized": False,
            **verify_installed(root, closure, packages), "toolchain_digest": toolchain["contract_digest"]}


def _download(opener, url, limit):
    """Retry transient public transport failures without retrying untrusted bytes."""
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "release-control-locked-build/1"})
            with opener.open(request, timeout=30) as response:
                if response.geturl() != url:
                    _fail("download-redirect")
                payload = response.read(limit + 1)
            if not payload or len(payload) > limit:
                _fail("download-limit")
            return payload
        except urllib.error.HTTPError as error:
            if error.code not in {408, 429, 500, 502, 503, 504} or attempt == 2:
                _fail("download-failed")
        except (OSError, urllib.error.URLError):
            if attempt == 2:
                _fail("download-failed")


def _write_new(path, payload):
    """Never replace an existing cached artifact, including racing link creation."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
    except OSError:
        _fail("cache-write-failed")


@safe_boundary
def acquire_cache(root, destination, contract=None):
    """Explicit public acquisition, safely resuming verified existing cache bytes.

    Existing files are never replaced. Partial caches may be reused only when
    every artifact matches this exact lock; unrelated, altered or linked files
    fail before any download. Installation never invokes this network phase.
    """
    contract = validate_contract(contract) if contract is not None else load_toolchain()
    closure = inspect_project(root, contract)
    destination = Path(os.path.abspath(destination))
    try:
        if destination.parent.resolve(strict=True) != destination.parent:
            _fail("cache-directory-invalid")
        if os.path.lexists(destination):
            if destination.is_symlink() or not destination.is_dir():
                _fail("cache-directory-invalid")
        else:
            destination.mkdir(mode=0o700, exist_ok=False)
        expected = {entry["integrity"] for entry in closure["external"]}
        cached, total = {}, 0
        entries = list(destination.iterdir())
        if len(entries) > len(closure["external"]) + 2:
            _fail("cache-closure-mismatch")
        node_path = destination / contract["node"]["filename"]
        manifest_path = destination / "verified-artifacts.json"
        node_available = False
        for path in entries:
            if path == node_path:
                payload = _read(path, MAX_ARCHIVE)
                if _sha(payload) != contract["node"]["sha256"]:
                    _fail("node-hash-mismatch")
                node_available = True
            elif path == manifest_path:
                _json(_read(path))
            else:
                if not re.fullmatch(r"[0-9a-f]{64}\.tgz", path.name):
                    _fail("cache-filename-invalid")
                payload = _read(path, MAX_PACKAGE)
                total += len(payload)
                integrity = "sha512-" + base64.b64encode(hashlib.sha512(payload).digest()).decode()
                if (_sha(payload) + ".tgz" != path.name or integrity not in expected
                        or integrity in cached or total > MAX_EXPANDED):
                    _fail("cache-bytes-invalid")
                cached[integrity] = path.name
        if os.path.lexists(manifest_path):
            verify_package_cache(destination, closure)
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *_args, **_kwargs):
                _fail("download-redirect")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        if not node_available:
            node = _download(opener, contract["node"]["url"], MAX_ARCHIVE)
            if _sha(node) != contract["node"]["sha256"]:
                _fail("node-hash-mismatch")
            _write_new(node_path, node)
        rows = []
        for entry in closure["external"]:
            filename = cached.get(entry["integrity"])
            if filename is None:
                payload = _download(opener, entry["url"], MAX_PACKAGE)
                total += len(payload)
                if total > MAX_EXPANDED:
                    _fail("download-limit")
                _integrity(entry["integrity"], payload)
                filename = _sha(payload) + ".tgz"
                _write_new(destination / filename, payload)
                cached[entry["integrity"]] = filename
            rows.append({**entry, "filename": filename})
        manifest = {"schema": "release-control-public-dependency-cache/v1",
                    "package_lock_sha256": closure["lock_sha256"], "packages": rows}
        if os.path.lexists(manifest_path):
            if _json(_read(manifest_path)) != manifest:
                _fail("cache-manifest-mismatch")
        else:
            _write_new(manifest_path, (json.dumps(manifest, sort_keys=True) + "\n").encode())
        verify_package_cache(destination, closure)
        return {"packages": len(rows), "closure_digest": closure["closure_digest"], "authorized": False}
    except ToolchainFailure:
        raise
    except Exception:
        _fail("acquisition-failed")
