#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.compiler.local-check-cache
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
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

TOOLS = {'bash', 'python3', 'node', 'npm', 'typescript'}


def valid_node_package(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'(?:@[A-Za-z0-9_.-]+/)?[A-Za-z0-9_.-]+', value) is not None and all(part not in {'.', '..'} for part in value.split('/'))


def node_installation_identity(root: Path, packages: list[str]) -> dict:
    """Fingerprint declared installed packages and their actual Node resolution.

    Only in-repository installation/workspace targets are supported. Required
    missing packages, links outside that boundary, and cycles are explicit gaps.
    Optional dependency absence is an input too. No module code is imported.
    """
    root = root.resolve()
    if not isinstance(packages, list) or any(not valid_node_package(name) for name in packages) or len(packages) != len(set(packages)):
        raise ValueError('node-installation-declaration-invalid')
    digest = hashlib.sha256()
    resolved_packages: set[str] = set()
    visited: set[tuple[str, str]] = set()
    def frame(value: object, content: bytes = b'') -> None:
        encoded = json.dumps(value, sort_keys=True).encode()
        digest.update(str(len(encoded)).encode() + b':' + encoded + str(len(content)).encode() + b':' + content)
    def contained(path: Path) -> Path:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
            return resolved
        except (OSError, RuntimeError, ValueError):
            raise ValueError('node-installation-path-unsupported') from None
    def walk(path: Path, label: str, ancestors: frozenset[Path]) -> None:
        resolved = contained(path)
        if path.is_symlink(): frame(['link', label, os.readlink(path), resolved.relative_to(root).as_posix()])
        info = resolved.stat()
        if stat.S_ISREG(info.st_mode): frame(['file', label, info.st_mode & 0o777], resolved.read_bytes())
        elif stat.S_ISDIR(info.st_mode):
            if resolved in ancestors: raise ValueError('node-installation-link-cycle')
            frame(['directory', label, info.st_mode & 0o777])
            for child in sorted(resolved.iterdir()):
                if child.name not in {'node_modules', '.git'}: walk(child, label + '/' + child.name, ancestors | {resolved})
        else: raise ValueError('node-installation-file-type-unsupported')
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
            if required: raise ValueError('node-installation-dependency-missing:' + name)
            continue
        real = contained(package)
        frame(['package-target', package.relative_to(root).as_posix(), real.relative_to(root).as_posix()])
        for parent in reversed((package, *package.parents)):
            if parent.is_relative_to(root) and parent.is_symlink():
                frame(['installation-link', parent.relative_to(root).as_posix(), os.readlink(parent), contained(parent).relative_to(root).as_posix()])
        identity = (name, package.relative_to(root).as_posix())
        if identity in visited: continue
        visited.add(identity)
        if len(visited) > 256: raise ValueError('node-installation-package-bound-exceeded')
        if not real.is_dir(): raise ValueError('node-installation-package-invalid:' + name)
        try:
            manifest_path = contained(real / 'package.json')
            manifest = json.loads(manifest_path.read_text())
        except (OSError, ValueError): raise ValueError('node-installation-manifest-invalid:' + name) from None
        if not isinstance(manifest, dict) or manifest.get('name') != name: raise ValueError('node-installation-package-identity-mismatch:' + name)
        walk(package, package.relative_to(root).as_posix(), frozenset())
        resolved_packages.add(package.relative_to(root).as_posix())
        dependencies: dict[str, bool] = {}
        for field in ('dependencies', 'optionalDependencies', 'peerDependencies'):
            declarations = manifest.get(field, {})
            if not isinstance(declarations, dict) or any(not valid_node_package(key) or not isinstance(value, str) for key, value in declarations.items()): raise ValueError('node-installation-dependencies-invalid:' + name)
            for dependency in sorted(declarations):
                mandatory = field != 'optionalDependencies'
                if field == 'peerDependencies':
                    peer_meta = manifest.get('peerDependenciesMeta', {})
                    if not isinstance(peer_meta, dict): raise ValueError('node-installation-peer-contract-invalid:' + name)
                    descriptor = peer_meta.get(dependency, {})
                    if not isinstance(descriptor, dict): raise ValueError('node-installation-peer-contract-invalid:' + name)
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
        except (OSError, RuntimeError, ValueError): raise ValueError('check-runtime-package-link-unsupported') from None
        if not resolved.is_file(): raise ValueError('check-runtime-package-file-invalid')
        content = resolved.read_bytes()
        label = [path.relative_to(package).as_posix(), resolved.stat().st_mode & 0o777, os.readlink(path) if path.is_symlink() else None, len(content)]
        digest.update(json.dumps(label).encode()); digest.update(content)
    return digest.hexdigest()


def runtime_identity(root: Path, declaration: dict) -> dict:
    """Bounded declared tool/config/environment support, never arbitrary probe argv."""
    tools = declaration.get('tools', [])
    environment = declaration.get('environment', [])
    if not isinstance(tools, list) or not tools or any(value not in TOOLS for value in tools):
        raise ValueError('check-runtime-tools-unsupported')
    if not isinstance(environment, list) or any(not isinstance(value, str) or not value.replace('_', '').isalnum() for value in environment):
        raise ValueError('check-runtime-environment-invalid')
    node_packages = declaration.get('node_packages', [])
    if ('node' in tools and 'node_packages' not in declaration) or ('typescript' in tools and 'typescript' not in node_packages):
        raise ValueError('node-installation-declaration-missing')
    result = {'tools': {}, 'node_installation': node_installation_identity(root, node_packages), 'environment': {key: hashlib.sha256(os.environ.get(key, '<unset>').encode()).hexdigest() for key in environment}}
    probe_environment = {key: value for key, value in os.environ.items() if key not in {'NODE_OPTIONS', 'NODE_PATH', 'PYTHONSTARTUP'}}
    for tool in sorted(set(tools)):
        executable = root / 'node_modules/.bin/tsc' if tool == 'typescript' else Path(shutil.which(tool) or '/missing-tool/' + tool)
        if not executable.is_file(): raise ValueError('check-runtime-tool-missing:' + tool)
        resolved = executable.resolve()
        argv = [str(executable), '--version']
        completed = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=15, env=probe_environment)
        if completed.returncode: raise ValueError('check-runtime-tool-unavailable:' + tool)
        info = resolved.stat()
        identity = {'path': str(resolved), 'version': completed.stdout.strip(), 'mode': info.st_mode & 0o777, 'digest': hashlib.sha256(resolved.read_bytes()).hexdigest()}
        if tool == 'python3':
            # Probe the interpreter actually selected by shell scripts, including its YAML installation.
            probe = subprocess.run([str(executable), '-c', 'import json,yaml; print(json.dumps([yaml.__version__,yaml.__file__]))'], cwd=root, capture_output=True, text=True, timeout=15, env=probe_environment)
            if probe.returncode: raise ValueError('check-runtime-pyyaml-unavailable')
            version, module_path = json.loads(probe.stdout)
            package = Path(module_path).parent
            identity['pyyaml'] = {'version': version, 'path': str(package), 'digest': tool_package_identity(package)}
        result['tools'][tool] = identity
    result['runner_python'] = {'executable': sys.executable, 'version': sys.version, 'yaml_version': yaml.__version__}
    return result


class LocalCache:
    """Trust same-user private Git metadata, never caller-supplied JSON paths.

    This is local acceleration, not a signed or portable acceptance receipt.
    A user able to edit their own Git metadata is inside this trust boundary.
    """
    def __init__(self, root: Path):
        completed = subprocess.run(['git', '-C', str(root), 'rev-parse', '--absolute-git-dir'], capture_output=True, text=True)
        if completed.returncode: raise ValueError('local-cache-worktree-unavailable')
        git_dir = Path(completed.stdout.strip())
        if not git_dir.is_absolute() or not git_dir.is_dir(): raise ValueError('local-cache-git-directory-invalid')
        for path in (git_dir, *git_dir.parents):
            if path.is_symlink(): raise ValueError('local-cache-symlink-forbidden')
        if git_dir.stat().st_uid != os.getuid(): raise ValueError('local-cache-owner-invalid')
        self.directory = git_dir / 'agentic-local-checks'
        if self.directory.is_symlink(): raise ValueError('local-cache-symlink-forbidden')
        self.directory.mkdir(mode=0o700, exist_ok=True)
        info = self.directory.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('local-cache-permissions-invalid')
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
            return value
        except (OSError, ValueError): return {}

    def write(self, name: str, value: dict) -> Path:
        if name != 'latest-report.json' and not re.fullmatch(r'[0-9a-f]{64}\.json', name):
            raise ValueError('local-cache-name-invalid')
        path = self.directory / name
        if path.is_symlink(): raise ValueError('local-cache-symlink-forbidden')
        descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=self.directory)
        try:
            with os.fdopen(descriptor, 'w') as stream:
                json.dump(value, stream, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
        return path

    def save(self, item: dict) -> None:
        if item.get('stage') != 'local' or item.get('status') != 'passed' or item.get('exit_code') != 0: return
        self.write(item['evidence_key'] + '.json', {**item, 'schema': 'repo/local-check-cache/v1', 'worktree': self.worktree})

    def save_report(self, report: dict) -> str:
        return str(self.write('latest-report.json', report))
