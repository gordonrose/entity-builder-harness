"""Run the pinned maintained Sigstore verifier offline, without ambient authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.artifact-verifier
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify signed attestation bundles using a pinned official CLI and trust root in a network-isolated process.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.artifact-admission
#     path: scripts/04.deploy/operational-realization-gate/artifact_admission.py

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import tarfile
import tempfile
import urllib.request

import build_contracts
import release_compiler as release

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'fixtures/artifact-admission'
MAX_INPUT = 8 * 1024 * 1024
MAX_OUTPUT = 8 * 1024 * 1024
TIMEOUT = 30
PROVENANCE = 'https://slsa.dev/provenance/v1'
SBOM = 'https://spdx.dev/Document'
SCAN = 'https://entity-builder.dev/release-control/artifact-scan/v1'
ISSUER = 'https://token.actions.githubusercontent.com'


class AdmissionFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def fail(code):
    raise AdmissionFailure(code)


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def json_bytes(data):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                fail('input-invalid')
            result[key] = value
        return result
    try:
        result = json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                            parse_constant=lambda ignored: fail('input-invalid'))
        release.bounded_json(result, max_nodes=100000)
        return result
    except (ValueError, UnicodeError, RecursionError, release.ReleaseFailure):
        fail('input-invalid')


def read_bytes(path, maximum=MAX_INPUT):
    """Open every path component through dirfds, excluding symlink-swap races."""
    directory = None
    try:
        path = Path(path).absolute()
        parts = path.parts[1:]
        if not parts or any(part in {'', '.', '..'} for part in parts):
            fail('artifact-unreadable')
        directory = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in parts[:-1]:
            next_directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                     dir_fd=directory)
            os.close(directory)
            directory = next_directory
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                fail('artifact-unreadable')
            data = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        if (len(data) > maximum or (before.st_ino, before.st_size, before.st_mtime_ns) !=
                (after.st_ino, after.st_size, after.st_mtime_ns)):
            fail('artifact-unreadable')
        return data
    except OSError:
        fail('artifact-unreadable')
    finally:
        if directory is not None:
            os.close(directory)


def load_lock():
    try:
        lock = json_bytes(read_bytes(ROOT / 'artifact-verifier.lock.json'))
        build_contracts.validate_schema('artifact-verifier-lock', lock)
        root = read_bytes(FIXTURES / 'trusted-root.jsonl')
        if digest(root) != lock['trusted_root_digest']:
            fail('verifier-integrity')
        return lock, root
    except release.ReleaseFailure:
        fail('schema-invalid')


def acquire(cache):
    """Explicit public acquisition only. Never overwrite an existing cache entry."""
    lock, _ = load_lock()
    cache = Path(cache).absolute()
    if any(part.is_symlink() for part in (cache, *cache.parents)):
        fail('tool-acquisition-failed')
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / 'gh'
    if dest.exists() or dest.is_symlink():
        checked_binary(cache)
        return lock
    try:
        with urllib.request.urlopen(lock['archive_url'], timeout=30) as stream:
            archive = stream.read(64 * 1024 * 1024 + 1)
        if len(archive) > 64 * 1024 * 1024 or digest(archive) != lock['archive_digest']:
            fail('verifier-integrity')
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
            matches = [member for member in tar.getmembers() if member.name == lock['member']]
            if len(matches) != 1 or not matches[0].isfile() or matches[0].size != lock['binary_bytes']:
                fail('verifier-integrity')
            data = tar.extractfile(matches[0]).read(lock['binary_bytes'] + 1)
        if len(data) != lock['binary_bytes'] or digest(data) != lock['binary_digest']:
            fail('verifier-integrity')
        with dest.open('xb') as stream:
            stream.write(data)
        dest.chmod(0o755)
        return lock
    except AdmissionFailure:
        raise
    except Exception:
        fail('tool-acquisition-failed')


def checked_binary(cache):
    lock, root = load_lock()
    try:
        data = read_bytes(Path(cache) / 'gh', 128 * 1024 * 1024)
    except AdmissionFailure:
        fail('verifier-unavailable')
    if len(data) != lock['binary_bytes'] or digest(data) != lock['binary_digest']:
        fail('verifier-integrity')
    return lock, root, data


def _limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT, TIMEOUT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT, MAX_OUTPUT))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))


def _run(command):
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     env={'PATH': '/usr/bin:/bin'}, start_new_session=True,
                                     preexec_fn=_limits)
        except OSError:
            fail('verifier-unavailable')
        try:
            child.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            fail('verifier-timeout')
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        stdout.seek(0); stderr.seek(0)
        out, err = stdout.read(MAX_OUTPUT + 1), stderr.read(MAX_OUTPUT + 1)
        if max(len(out), len(err)) >= MAX_OUTPUT:
            fail('verifier-output-limit')
        if child.returncode != 0:
            fail('verifier-failed')
        return out


def expected_identity(repository, ref, workflow, commit, subject_name, subject_digest, predicate):
    """This generic verifier is shared; the public admission policy fixes the target."""
    patterns = [(repository, r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+'),
                (ref, r'refs/(heads|tags)/[A-Za-z0-9_./-]+'),
                (workflow, r'\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml'),
                (commit, r'[0-9a-f]{40}'), (subject_digest, r'sha256:[0-9a-f]{64}')]
    if (any(type(value) is not str or not re.fullmatch(pattern, value) for value, pattern in patterns)
            or not isinstance(subject_name, str) or not 1 <= len(subject_name) <= 512
            or any(ord(char) < 32 for char in subject_name)
            or predicate not in {PROVENANCE, SBOM, SCAN}):
        fail('input-invalid')
    return {'repository': repository, 'ref': ref, 'workflow': workflow, 'commit': commit,
            'subject_name': subject_name, 'subject_digest': subject_digest, 'predicate': predicate}


def parse_verified(raw, expected):
    """Only call with fresh stdout from the pinned isolated verifier, never a file receipt."""
    try:
        rows = json_bytes(raw)
        if not isinstance(rows, list) or len(rows) != 1:
            fail('verifier-output-invalid')
        verified = rows[0]['verificationResult']
        certificate = verified['signature']['certificate']
        identity = 'https://github.com/' + expected['repository'] + '/' + expected['workflow'] + '@' + expected['ref']
        required = {'subjectAlternativeName': identity, 'issuer': ISSUER,
                    'sourceRepositoryURI': 'https://github.com/' + expected['repository'],
                    'sourceRepositoryDigest': expected['commit'], 'sourceRepositoryRef': expected['ref'],
                    'buildSignerURI': identity, 'buildSignerDigest': expected['commit'],
                    'buildConfigURI': identity, 'buildConfigDigest': expected['commit'],
                    'runnerEnvironment': 'github-hosted'}
        if any(certificate.get(key) != value for key, value in required.items()):
            fail('identity-mismatch')
        if not verified.get('verifiedTimestamps'):
            fail('verifier-output-invalid')
        statement = verified['statement']
        if (statement.get('_type') != 'https://in-toto.io/Statement/v1'
                or statement.get('predicateType') != expected['predicate']):
            fail('predicate-mismatch')
        subjects = statement.get('subject')
        if subjects != [{'name': expected['subject_name'], 'digest': {'sha256': expected['subject_digest'][7:]}}]:
            fail('subject-mismatch')
        if not isinstance(statement.get('predicate'), dict):
            fail('predicate-mismatch')
        return statement
    except AdmissionFailure:
        raise
    except (KeyError, TypeError, ValueError):
        fail('verifier-output-invalid')


def verify_bundle(cache, artifact, bundle, expected):
    """Cryptographically verify one signed statement against exact local artifact bytes."""
    if type(artifact) is not bytes or type(bundle) is not bytes or max(len(artifact), len(bundle)) > MAX_INPUT:
        fail('input-invalid')
    if digest(artifact) != expected['subject_digest']:
        fail('artifact-digest-mismatch')
    # Validate bounded JSON and refuse a list/JSONL collection before invoking crypto.
    if not isinstance(json_bytes(bundle), dict):
        fail('bundle-invalid')
    lock, trust_root, binary = checked_binary(cache)
    identity = 'https://github.com/' + expected['repository'] + '/' + expected['workflow'] + '@' + expected['ref']
    with tempfile.TemporaryDirectory(prefix='release-control-attestation-') as temporary:
        work = Path(temporary)
        for name, data in [('gh', binary), ('artifact', artifact), ('bundle.json', bundle), ('trusted-root.jsonl', trust_root)]:
            (work / name).write_bytes(data)
        (work / 'gh').chmod(0o500)
        command = ['/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net', '--unshare-ipc',
                   '--unshare-uts', '--die-with-parent', '--new-session', '--cap-drop', 'ALL', '--disable-userns',
                   '--ro-bind', str(work), '/work', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
                   '--clearenv', '--setenv', 'HOME', '/tmp/home', '--setenv', 'GH_CONFIG_DIR', '/tmp/gh',
                   '--setenv', 'GH_HOST', 'github.com', '--setenv', 'GH_PROMPT_DISABLED', '1',
                   '--setenv', 'GH_NO_UPDATE_NOTIFIER', '1', '--chdir', '/work', '--', '/work/gh',
                   'attestation', 'verify', '/work/artifact', '--bundle', '/work/bundle.json',
                   '--custom-trusted-root', '/work/trusted-root.jsonl', '--repo', expected['repository'],
                   '--cert-identity', identity, '--cert-oidc-issuer', ISSUER,
                   '--source-ref', expected['ref'], '--source-digest', expected['commit'],
                   '--signer-digest', expected['commit'], '--deny-self-hosted-runners',
                   '--predicate-type', expected['predicate'], '--format', 'json']
        return parse_verified(_run(command), expected)
