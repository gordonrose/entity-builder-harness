#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.compiler.local-check-cache
#   version: 2
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-31"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Retain successful local runner evidence inside private worktree Git metadata without accepting imported reports.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.compiler.check-selection
#     path: scripts/repo/check-selection/script.py
from __future__ import annotations
import hashlib
import copy
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import yaml

TOOLS = {'bash', 'python3', 'node', 'npm', 'typescript', 'openssl', 'git'}
NO_PRIOR_EVIDENCE = 'no-prior-successful-local-evidence'
INPUTS_CHANGED = 'verified-inputs-changed'
RUNTIME_CHANGED = 'runtime-identity-changed'
DEPENDENCY_CHANGED = 'dependency-proof-changed'
CONTRACT_CHANGED = 'verification-contract-changed'
KEY_CHANGED = 'evidence-key-changed'
CACHE_INVALIDATION_REASONS = frozenset({NO_PRIOR_EVIDENCE, INPUTS_CHANGED, RUNTIME_CHANGED, DEPENDENCY_CHANGED, CONTRACT_CHANGED, KEY_CHANGED})
LOCAL_CHECK_FAILURE_CODES = frozenset({
    'check-runtime-window-root-mismatch', 'node-installation-declaration-invalid',
    'node-installation-path-unsupported', 'node-installation-link-cycle',
    'node-installation-file-type-unsupported', 'node-installation-dependency-missing',
    'node-installation-package-bound-exceeded', 'node-installation-package-invalid',
    'node-installation-manifest-invalid', 'node-installation-package-identity-mismatch',
    'node-installation-dependencies-invalid', 'node-installation-peer-contract-invalid',
    'check-runtime-package-link-unsupported', 'check-runtime-package-file-invalid',
    'check-runtime-tools-unsupported', 'check-runtime-environment-invalid',
    'node-installation-declaration-missing', 'check-runtime-tool-missing',
    'check-runtime-tool-unavailable', 'check-runtime-pyyaml-unavailable',
    'local-cache-worktree-unavailable', 'local-cache-git-directory-invalid',
    'local-cache-symlink-forbidden', 'local-cache-owner-invalid',
    'local-cache-permissions-invalid', 'local-cache-name-invalid',
    'verification-execution-context-busy', 'verification-runner-identity-invalid',
    'verification-runner-not-live', 'verification-runner-identity-unavailable',
    'verification-execution-context-changed', 'reuse-worktree-symlink-forbidden',
    'reuse-worktree-repository-mismatch', 'reuse-worktree-not-registered',
})


class LocalCheckError(ValueError):
    """Owned failure context; the compatible private message is not disclosure."""
    def __init__(self, code: str, message: str | None = None, *, tool: str | None = None):
        super().__init__(code if message is None else message)
        self.code = code
        self.tool = tool


def local_check_diagnostic(error: BaseException) -> dict:
    if type(error) is not LocalCheckError:
        return {'detail': 'unclassified-runtime-failure'}
    code, tool = vars(error).get('code'), vars(error).get('tool')
    if type(code) is not str or code not in LOCAL_CHECK_FAILURE_CODES:
        return {'detail': 'unclassified-runtime-failure'}
    result = {'detail': code}
    if code in {'check-runtime-tool-missing', 'check-runtime-tool-unavailable'} and type(tool) is str and tool in TOOLS:
        result['tool'] = tool
    return result


def valid_node_package(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'(?:@[A-Za-z0-9_.-]+/)?[A-Za-z0-9_.-]+', value) is not None and all(part not in {'.', '..'} for part in value.split('/'))


class RuntimeIdentityWindow:
    """In-memory components for one runner-owned measurement window only.

    Never persisted or validated by timestamps. The runner clears this window
    together with full declaration identities at every freshness boundary.
    """
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.clear()

    def clear(self) -> None:
        self.tools: dict[tuple, dict] = {}
        self.node_trees: dict[tuple[str, str], tuple[dict, tuple[bytes, ...]]] = {}
        self.node_tree_bytes = 0

    def require_root(self, root: Path) -> None:
        if root.resolve() != self.root: raise LocalCheckError('check-runtime-window-root-mismatch')


def node_installation_identity(root: Path, packages: list[str], *, window: RuntimeIdentityWindow | None = None) -> dict:
    """Fingerprint declared installed packages and their actual Node resolution.

    Only in-repository installation/workspace targets are supported. Required
    missing packages, links outside that boundary, and cycles are explicit gaps.
    Optional dependency absence is an input too. No module code is imported.
    """
    root = root.resolve()
    if window is not None: window.require_root(root)
    if not isinstance(packages, list) or any(not valid_node_package(name) for name in packages) or len(packages) != len(set(packages)):
        raise LocalCheckError('node-installation-declaration-invalid')
    digest = hashlib.sha256()
    resolved_packages: set[str] = set()
    visited: set[tuple[str, str]] = set()
    recorded_frames: list[bytes] | None = None
    recorded_bytes = 0
    def frame(value: object, content: bytes = b'') -> None:
        nonlocal recorded_frames, recorded_bytes
        encoded = json.dumps(value, sort_keys=True).encode()
        chunk = str(len(encoded)).encode() + b':' + encoded + str(len(content)).encode() + b':' + content
        digest.update(chunk)
        if recorded_frames is not None:
            recorded_bytes += len(chunk)
            # Bound retained content, not correctness: large trees are simply
            # measured again. Replaying original frames preserves the digest.
            if window.node_tree_bytes + recorded_bytes <= 128 * 1024 * 1024: recorded_frames.append(chunk)
            else: recorded_frames = None
    def contained(path: Path) -> Path:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
            return resolved
        except (OSError, RuntimeError, ValueError):
            raise LocalCheckError('node-installation-path-unsupported') from None
    def walk(path: Path, label: str, ancestors: frozenset[Path]) -> None:
        resolved = contained(path)
        if path.is_symlink(): frame(['link', label, os.readlink(path), resolved.relative_to(root).as_posix()])
        info = resolved.stat()
        if stat.S_ISREG(info.st_mode): frame(['file', label, info.st_mode & 0o777], resolved.read_bytes())
        elif stat.S_ISDIR(info.st_mode):
            if resolved in ancestors: raise LocalCheckError('node-installation-link-cycle')
            frame(['directory', label, info.st_mode & 0o777])
            for child in sorted(resolved.iterdir()):
                if child.name not in {'node_modules', '.git'}: walk(child, label + '/' + child.name, ancestors | {resolved})
        else: raise LocalCheckError('node-installation-file-type-unsupported')
    def resolve_package(name: str, caller: Path) -> Path | None:
        # Node's ordinary node_modules walk, bounded at this repository. Both
        # logical and real package locations are retained for workspace links.
        for directory in (caller, *caller.parents):
            if not directory.is_relative_to(root): break
            if directory.name == 'node_modules': continue
            candidate = directory / 'node_modules' / name
            if candidate.exists() or candidate.is_symlink(): return candidate
        return None
    queue = [(name, root, True) for name in sorted(packages)]
    while queue:
        name, caller, required = queue.pop(0)
        package = resolve_package(name, caller)
        frame(['resolution', name, caller.relative_to(root).as_posix(), required, package.relative_to(root).as_posix() if package else None])
        if package is None:
            if required: raise LocalCheckError('node-installation-dependency-missing', 'node-installation-dependency-missing:' + name)
            continue
        real = contained(package)
        frame(['package-target', package.relative_to(root).as_posix(), real.relative_to(root).as_posix()])
        for parent in reversed((package, *package.parents)):
            if parent.is_relative_to(root) and parent.is_symlink():
                frame(['installation-link', parent.relative_to(root).as_posix(), os.readlink(parent), contained(parent).relative_to(root).as_posix()])
        identity = (name, package.relative_to(root).as_posix())
        if identity in visited: continue
        visited.add(identity)
        if len(visited) > 256: raise LocalCheckError('node-installation-package-bound-exceeded')
        if not real.is_dir(): raise LocalCheckError('node-installation-package-invalid', 'node-installation-package-invalid:' + name)
        tree_key = package.relative_to(root).as_posix()
        cache_key = (tree_key, real.relative_to(root).as_posix())
        cached_tree = window.node_trees.get(cache_key) if window is not None else None
        if cached_tree is not None:
            manifest, frames = cached_tree
        else:
            try:
                manifest_path = contained(real / 'package.json')
                manifest = json.loads(manifest_path.read_text())
            except (OSError, ValueError): raise LocalCheckError('node-installation-manifest-invalid', 'node-installation-manifest-invalid:' + name) from None
        if not isinstance(manifest, dict) or manifest.get('name') != name: raise LocalCheckError('node-installation-package-identity-mismatch', 'node-installation-package-identity-mismatch:' + name)
        if cached_tree is not None:
            for chunk in frames: digest.update(chunk)
        else:
            recorded_frames = [] if window is not None else None
            recorded_bytes = 0
            walk(package, tree_key, frozenset())
            if recorded_frames is not None:
                window.node_trees[cache_key] = (manifest, tuple(recorded_frames))
                window.node_tree_bytes += recorded_bytes
            recorded_frames = None
        resolved_packages.add(package.relative_to(root).as_posix())
        dependencies: dict[str, bool] = {}
        for field in ('dependencies', 'optionalDependencies', 'peerDependencies'):
            declarations = manifest.get(field, {})
            if not isinstance(declarations, dict) or any(not valid_node_package(key) or not isinstance(value, str) for key, value in declarations.items()): raise LocalCheckError('node-installation-dependencies-invalid', 'node-installation-dependencies-invalid:' + name)
            for dependency in sorted(declarations):
                mandatory = field != 'optionalDependencies'
                if field == 'peerDependencies':
                    peer_meta = manifest.get('peerDependenciesMeta', {})
                    if not isinstance(peer_meta, dict): raise LocalCheckError('node-installation-peer-contract-invalid', 'node-installation-peer-contract-invalid:' + name)
                    descriptor = peer_meta.get(dependency, {})
                    if not isinstance(descriptor, dict): raise LocalCheckError('node-installation-peer-contract-invalid', 'node-installation-peer-contract-invalid:' + name)
                    mandatory = descriptor.get('optional') is not True
                if field == 'optionalDependencies' or dependency not in dependencies: dependencies[dependency] = mandatory
                else: dependencies[dependency] = dependencies[dependency] or mandatory
        for dependency, mandatory in sorted(dependencies.items()):
            queue.append((dependency, real, mandatory))
            # Include logical resolution too, so workspace links retain the
            # dependencies reachable with Node's preserve-symlinks option.
            if package != real: queue.append((dependency, package, False))
    return {'digest': digest.hexdigest(), 'packages': sorted(resolved_packages)}


def tool_package_identity(package: Path) -> str:
    """Python package source/native modules; generated bytecode is not input."""
    package = package.resolve()
    digest = hashlib.sha256()
    for path in sorted(package.rglob('*')):
        if path.suffix not in {'.py', '.so', '.pyd', '.dll'} or '__pycache__' in path.parts: continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(package)
        except (OSError, RuntimeError, ValueError): raise LocalCheckError('check-runtime-package-link-unsupported') from None
        if not resolved.is_file(): raise LocalCheckError('check-runtime-package-file-invalid')
        content = resolved.read_bytes()
        label = [path.relative_to(package).as_posix(), resolved.stat().st_mode & 0o777, os.readlink(path) if path.is_symlink() else None, len(content)]
        digest.update(json.dumps(label).encode()); digest.update(content)
    return digest.hexdigest()


def runtime_identity(root: Path, declaration: dict, *, window: RuntimeIdentityWindow | None = None) -> dict:
    """Bounded declared tool/config/environment support, never arbitrary probe argv."""
    tools = declaration.get('tools', [])
    environment = declaration.get('environment', [])
    if not isinstance(tools, list) or not tools or any(value not in TOOLS for value in tools):
        raise LocalCheckError('check-runtime-tools-unsupported')
    if not isinstance(environment, list) or any(not isinstance(value, str) or not value.replace('_', '').isalnum() for value in environment):
        raise LocalCheckError('check-runtime-environment-invalid')
    node_packages = declaration.get('node_packages', [])
    if ('node' in tools and 'node_packages' not in declaration) or ('typescript' in tools and 'typescript' not in node_packages):
        raise LocalCheckError('node-installation-declaration-missing')
    if window is not None: window.require_root(root)
    result = {'tools': {}, 'node_installation': node_installation_identity(root, node_packages, window=window), 'environment': {key: hashlib.sha256(os.environ.get(key, '<unset>').encode()).hexdigest() for key in environment}}
    probe_environment = {key: value for key, value in os.environ.items() if key not in {'NODE_OPTIONS', 'NODE_PATH', 'PYTHONSTARTUP'}}
    for tool in sorted(set(tools)):
        executable = root / 'node_modules/.bin/tsc' if tool == 'typescript' else Path(shutil.which(tool) or '/missing-tool/' + tool)
        if not executable.is_file(): raise LocalCheckError('check-runtime-tool-missing', 'check-runtime-tool-missing:' + tool, tool=tool)
        resolved = executable.resolve()
        tool_key = (tool, str(executable), str(resolved), tuple(sorted(probe_environment.items())))
        if window is not None and tool_key in window.tools:
            result['tools'][tool] = copy.deepcopy(window.tools[tool_key])
            continue
        argv = [str(executable), 'version' if tool == 'openssl' else '--version']
        completed = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=15, env=probe_environment)
        if completed.returncode: raise LocalCheckError('check-runtime-tool-unavailable', 'check-runtime-tool-unavailable:' + tool, tool=tool)
        info = resolved.stat()
        # A repository-installed tool at the same relative location, with the
        # same bytes/mode/version and dependency closure, survives a worktree
        # transfer. External tools retain their absolute installation identity.
        tool_path = '$REPO/' + resolved.relative_to(root).as_posix() if resolved.is_relative_to(root) else str(resolved)
        identity = {'path': tool_path, 'version': completed.stdout.strip(), 'mode': info.st_mode & 0o777, 'digest': hashlib.sha256(resolved.read_bytes()).hexdigest()}
        if tool == 'python3':
            # Probe the interpreter actually selected by shell scripts, including its YAML installation.
            probe = subprocess.run([str(executable), '-c', 'import json,yaml; print(json.dumps([yaml.__version__,yaml.__file__]))'], cwd=root, capture_output=True, text=True, timeout=15, env=probe_environment)
            if probe.returncode: raise LocalCheckError('check-runtime-pyyaml-unavailable')
            version, module_path = json.loads(probe.stdout)
            package = Path(module_path).parent
            identity['pyyaml'] = {'version': version, 'path': str(package), 'digest': tool_package_identity(package)}
        result['tools'][tool] = identity
        if window is not None: window.tools[tool_key] = copy.deepcopy(identity)
    result['runner_python'] = {'executable': sys.executable, 'version': sys.version, 'yaml_version': yaml.__version__}
    return result


class LocalCache:
    """Trust same-user private Git metadata, never caller-supplied JSON paths.

    This is local acceleration, not a signed or portable acceptance receipt.
    A user able to edit their own Git metadata is inside this trust boundary.
    """
    def __init__(self, root: Path, *, create: bool = True):
        completed = subprocess.run(['git', '-C', str(root), 'rev-parse', '--absolute-git-dir'], capture_output=True, text=True)
        if completed.returncode: raise LocalCheckError('local-cache-worktree-unavailable')
        git_dir = Path(completed.stdout.strip())
        if not git_dir.is_absolute() or not git_dir.is_dir(): raise LocalCheckError('local-cache-git-directory-invalid')
        for path in (git_dir, *git_dir.parents):
            if path.is_symlink(): raise LocalCheckError('local-cache-symlink-forbidden')
        if git_dir.stat().st_uid != os.getuid(): raise LocalCheckError('local-cache-owner-invalid')
        self.directory = git_dir / 'agentic-local-checks'
        if self.directory.is_symlink(): raise LocalCheckError('local-cache-symlink-forbidden')
        if create:
            self.directory.mkdir(mode=0o700, exist_ok=True)
        info = self.directory.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise LocalCheckError('local-cache-permissions-invalid')
        self.worktree = str(root.resolve())

    def read(self, key: str) -> dict:
        path = self.directory / (key + '.json')
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, 'r') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 1048576: return {}
                value = json.load(stream)
            if not isinstance(value, dict) or value.get('schema') != 'repo/local-check-cache/v1' or value.get('worktree') != self.worktree: return {}
            if value.get('evidence_key') != key or value.get('stage') != 'local' or value.get('status') != 'passed' or value.get('exit_code') != 0: return {}
            payload = {field: value.get(field) for field in ('input_digest', 'argv', 'effects', 'stage', 'boundary', 'evidence_class', 'runtime_identity', 'parameters', 'applicability', 'catalog_entries', 'dependency_contracts', 'dependency_evidence_keys', 'review_bindings')}
            if hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest() != key: return {}
            return value
        except (OSError, ValueError): return {}

    def write(self, name: str, value: dict) -> Path:
        if name not in {'latest-report.json', 'preparation-report.json'} and not re.fullmatch(r'[0-9a-f]{64}\.json', name):
            raise LocalCheckError('local-cache-name-invalid')
        path = self.directory / name
        if path.is_symlink(): raise LocalCheckError('local-cache-symlink-forbidden')
        encoded = json.dumps(value, sort_keys=True).encode()
        try:
            existing = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(existing, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o077 and info.st_nlink == 1 and info.st_size == len(encoded) and stream.read() == encoded:
                    return path
        except FileNotFoundError:
            pass
        descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=self.directory)
        try:
            with os.fdopen(descriptor, 'w') as stream:
                stream.write(encoded.decode())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
        return path

    def save(self, item: dict) -> None:
        if item.get('stage') != 'local' or item.get('status') != 'passed' or item.get('exit_code') != 0: return
        self.write(item['evidence_key'] + '.json', {**item, 'schema': 'repo/local-check-cache/v1', 'worktree': self.worktree})

    def invalidation_reasons(self, item: dict) -> list[str]:
        """Explain a cache miss without treating a stale receipt as proof."""
        candidates: list[tuple[int, dict]] = []
        for path in self.directory.iterdir():
            if not re.fullmatch(r'[0-9a-f]{64}\.json', path.name):
                continue
            value = self.read(path.stem)
            if value and value.get('check_key') == item.get('check_key'):
                try:
                    candidates.append((path.stat().st_mtime_ns, value))
                except OSError:
                    continue
        if not candidates:
            return [NO_PRIOR_EVIDENCE]
        previous = max(candidates, key=lambda candidate: candidate[0])[1]
        reasons = []
        if previous.get('input_digest') != item.get('input_digest'):
            reasons.append(INPUTS_CHANGED)
        if previous.get('runtime_identity') != item.get('runtime_identity'):
            reasons.append(RUNTIME_CHANGED)
        if previous.get('dependency_evidence_keys') != item.get('dependency_evidence_keys'):
            reasons.append(DEPENDENCY_CHANGED)
        if any(previous.get(field) != item.get(field) for field in ('argv', 'effects', 'stage', 'boundary', 'evidence_class', 'runtime', 'parameters', 'applicability', 'catalog_entries', 'dependency_contracts', 'review_bindings')):
            reasons.append(CONTRACT_CHANGED)
        return reasons or [KEY_CHANGED]

    def save_report(self, report: dict) -> str:
        return str(self.write('latest-report.json', report))

    def save_preparation(self, value: dict) -> str:
        return str(self.write('preparation-report.json', {
            **value,
            'schema': 'repo/verification-preparation/v1',
            'worktree': self.worktree,
        }))

    def begin_execution(self, binding: dict, parent_token: str | None = None) -> dict | None:
        """Short-lived nested context, inside the existing same-user trust boundary."""
        preparation = self.read_preparation()
        previous = preparation.get('active_execution')
        if previous and not self.execution_live(previous): previous = None
        if previous and previous.get('token') != parent_token:
            raise LocalCheckError('verification-execution-context-busy')
        binding['runner'] = self.execution_identity(os.getpid())
        self.save_preparation({**preparation, 'checks': preparation.get('checks', []), 'active_execution': binding})
        return previous

    @staticmethod
    def execution_identity(pid: int) -> dict:
        # Linux runner identity includes process birth, so PID reuse is not proof.
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0: raise LocalCheckError('verification-runner-identity-invalid')
        try:
            fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(') ', 1)[1].split()
            if fields[0] == 'Z': raise LocalCheckError('verification-runner-not-live')
            return {'pid': pid, 'start_ticks': int(fields[19])}
        except (IndexError, ValueError): raise LocalCheckError('verification-runner-identity-unavailable') from None

    @classmethod
    def execution_live(cls, binding: dict) -> bool:
        try:
            expected = binding['runner']
            return isinstance(expected, dict) and cls.execution_identity(expected['pid']) == expected
        except (OSError, ValueError, KeyError, IndexError, TypeError): return False

    def end_execution(self, token: str, previous: dict | None) -> None:
        preparation = self.read_preparation()
        if preparation.get('active_execution', {}).get('token') != token:
            raise LocalCheckError('verification-execution-context-changed')
        preparation.pop('active_execution', None)
        if previous: preparation['active_execution'] = previous
        self.save_preparation(preparation)

    def read_preparation(self) -> dict:
        path = self.directory / 'preparation-report.json'
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(descriptor, 'r') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_nlink != 1 or info.st_size > 1048576:
                    return {}
                value = json.load(stream)
            if not isinstance(value, dict) or value.get('schema') != 'repo/verification-preparation/v1' or value.get('worktree') != self.worktree:
                return {}
            checks = value.get('checks')
            if not isinstance(checks, list) or any(not isinstance(item, dict) or not isinstance(item.get('check_id'), str) or not isinstance(item.get('evidence_key'), str) for item in checks):
                return {}
            return value
        except (OSError, ValueError):
            return {}

    def prepared_artifact(self, path: str, content: bytes, mode: int) -> bool:
        """A date rollover cannot revoke the exact bytes prepared by the owner."""
        records = self.read_preparation().get('lifecycle_inputs', {})
        record = records.get(path) if isinstance(records, dict) else None
        return isinstance(record, dict) and record.get('sha256') == hashlib.sha256(content).hexdigest() and record.get('mode') == mode

    @classmethod
    def registered_source(cls, root: Path, source: Path):
        """Resolve a same-repository registered cache, never a supplied report."""
        source = source.absolute()
        if any(path.is_symlink() for path in (source, *source.parents)):
            raise LocalCheckError('reuse-worktree-symlink-forbidden')
        def query(directory, *args):
            return subprocess.run(['git', '-C', str(directory), *args], check=True, capture_output=True, text=True).stdout.strip()
        if query(root, 'rev-parse', '--path-format=absolute', '--git-common-dir') != query(source, 'rev-parse', '--path-format=absolute', '--git-common-dir'):
            raise LocalCheckError('reuse-worktree-repository-mismatch')
        records = query(root, 'worktree', 'list', '--porcelain', '-z').split('\0')
        registered = {Path(record[9:]).resolve() for record in records if record.startswith('worktree ')}
        if source.resolve() not in registered:
            raise LocalCheckError('reuse-worktree-not-registered')
        return cls(source, create=False)

    def record_artifacts(self, records: dict) -> None:
        preparation = self.read_preparation()
        previous = preparation.get('lifecycle_inputs', {})
        if not isinstance(previous, dict): previous = {}
        self.save_preparation({**preparation, 'checks': preparation.get('checks', []), 'lifecycle_inputs': {**previous, **records}})
