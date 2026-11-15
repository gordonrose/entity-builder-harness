#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.check-selection.workspace-context
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-15"
#   layer: 06.shared
#   domain: validation
#   disciplines: [architecture, security]
#   kind: script
#   purpose: Bind existing package checks to declaration-derived inputs and reject changed discovery before reusing proof.
#   portability: {class: source-only, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: repo.compiler.check-selection
#     path: scripts/repo/check-selection/script.py

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

WRAPPER = 'scripts/repo/diagnostic-coverage/verify.sh'
PROJECTOR = 'scripts/repo/workspace-build/check-inputs.mjs'
OWNER = 'scripts/repo/check-selection/workspace_context.py'


def context_key(value):
    mode = 'inherit' if value['ignoreScripts'] is None else 'ignore' if value['ignoreScripts'] else 'hooks'
    return value['npmScript'] + '|' + mode


class WorkspaceContextError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _read(root: Path, argv: list[str], request: dict | None = None) -> dict:
    try:
        result = subprocess.run(argv, cwd=root, input=json.dumps(request) if request is not None else None,
                                capture_output=True, text=True, timeout=30, check=False)
        if len(result.stdout) > 2 * 1024 * 1024:
            raise WorkspaceContextError('workspace-context-response-invalid')
        value = json.loads(result.stdout)
        if result.returncode != 0 or not isinstance(value, dict):
            raise WorkspaceContextError('workspace-context-observation-failed')
        return value
    except WorkspaceContextError:
        raise
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        raise WorkspaceContextError('workspace-context-observation-unavailable') from None


def load(root: Path, checks: dict, safe_path) -> dict:
    """Only the existing wrapper owns unit-to-npm selection; no copied map."""
    bindings = {}
    for identity, check in checks.items():
        argv = check.get('argv') if isinstance(check, dict) else None
        if not isinstance(argv, list) or argv[:2] != ['bash', WRAPPER]:
            continue
        if len(argv) != 4 or argv[2] not in ('--unit', '--security-adapter'):
            # The no-argument aggregate has no package compiler of its own.
            if argv == ['bash', WRAPPER]:
                continue
            raise WorkspaceContextError('workspace-context-command-invalid')
        value = _read(root, ['bash', WRAPPER, '--describe-npm', *argv[2:]])
        if set(value) != {'npmScript', 'ignoreScripts'} or value['ignoreScripts'] is not None and type(value['ignoreScripts']) is not bool:
            raise WorkspaceContextError('workspace-context-response-invalid')
        name = value['npmScript']
        if name is None:
            continue
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:._-]*', name):
            raise WorkspaceContextError('workspace-context-response-invalid')
        bindings[identity] = value
    if not bindings:
        return {'checks': {}, 'discovery': []}
    unique = {context_key(value): value for value in bindings.values()}
    result = _read(root, ['node', PROJECTOR], {'scripts': [unique[key] for key in sorted(unique)]})
    if set(result) != {'contexts', 'discoveryInputs'} or not isinstance(result['contexts'], dict) or set(result['contexts']) != set(unique):
        raise WorkspaceContextError('workspace-context-response-invalid')
    def paths(value):
        return isinstance(value, list) and bool(value) and all(isinstance(path, str) and safe_path(path) for path in value) and len(set(value)) == len(value)
    if not paths(result['discoveryInputs']):
        raise WorkspaceContextError('workspace-context-response-invalid')
    contexts = {}
    for identity, binding in bindings.items():
        record = result['contexts'][context_key(binding)]
        if not isinstance(record, dict) or set(record) != {'references', 'nodePackages', 'ignoreScripts'} or type(record['ignoreScripts']) is not bool or not paths(record['references']):
            raise WorkspaceContextError('workspace-context-response-invalid')
        packages = record['nodePackages']
        if not isinstance(packages, list) or any(not isinstance(package, str) or not re.fullmatch(r'(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*', package) for package in packages) or len(set(packages)) != len(packages):
            raise WorkspaceContextError('workspace-context-response-invalid')
        if binding['ignoreScripts'] is not None and record['ignoreScripts'] != binding['ignoreScripts']:
            raise WorkspaceContextError('workspace-context-response-invalid')
        contexts[identity] = {'references': sorted(set(record['references']) | {OWNER, WRAPPER, PROJECTOR, '.npmrc'}),
                              'node_packages': packages, 'inherited_ignore_scripts': record['ignoreScripts'] if binding['ignoreScripts'] is None else None}
    return {'checks': contexts, 'discovery': result['discoveryInputs']}


def npm_ignore_scripts(root: Path) -> bool:
    try:
        result = subprocess.run(['npm', 'config', 'get', 'ignore-scripts'], cwd=root, capture_output=True,
                                text=True, timeout=10, check=False)
        if result.returncode != 0 or result.stdout.strip() not in ('true', 'false'):
            raise WorkspaceContextError('workspace-context-npm-config-unavailable')
        return result.stdout.strip() == 'true'
    except (OSError, UnicodeError, subprocess.SubprocessError):
        raise WorkspaceContextError('workspace-context-npm-config-unavailable') from None


def manifest_inventory(paths: list[str]) -> tuple[str, ...]:
    # Inventory names (not all source contents) detect newly added/removed
    # manifests before a fresh resolver run. Only declared discovery files'
    # contents enter the accompanying fingerprint.
    return tuple(sorted(path for path in paths if path == 'package.json' or path.endswith('/package.json')))
