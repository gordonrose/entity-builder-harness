#!/usr/bin/env python3
"""Prepare direct local runtime exports by genuine read-only compiler re-emission."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operational-realization-package-exports-cli
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve direct runtime commands with fresh pinned-version emission checks without claiming dependency qualification.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.workspace-runtime-projection
#     path: scripts/04.deploy/build-platform-shell-image/workspace-runtime.mjs

import argparse
import json
import os
from pathlib import Path
import subprocess
import selectors
import signal
import stat
import time
import resource
import sys
import tempfile

sys.dont_write_bytecode = True


class InvalidArguments(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InvalidArguments() from None


def failure(code):
    return {'schema': 'package-export-error/v1', 'scope': 'workspace-export-preparation',
            'authorized': False, 'verdict': 'blocked', 'release_eligibility': 'blocked',
            'operation_authorization': 'blocked', 'findings': [{'code': code}]}


def invoking_node():
    # The direct helper was launched by the existing Node generator. Use that
    # running executable, not a caller-selected path or ambient replacement.
    parent = Path('/proc') / str(os.getppid())
    executable = (parent / 'exe').resolve(strict=True)
    if executable.name != 'node' or not executable.is_file():
        raise InvalidArguments()
    descriptor = os.open(parent / 'exe', os.O_RDONLY | os.O_CLOEXEC)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise InvalidArguments()
    return descriptor


def child_limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))


def bounded_run(command, root, descriptor, timeout=180):
    process = subprocess.Popen(command, cwd=root, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'TZ': 'UTC'},
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(descriptor,),
                               start_new_session=True, preexec_fn=child_limits)
    counts = {'stdout': 0, 'stderr': 0}
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, 'stdout')
    selector.register(process.stderr, selectors.EVENT_READ, 'stderr')
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError()
            for key, _mask in selector.select(min(remaining, 0.25)):
                data = os.read(key.fileobj.fileno(), 65536)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                counts[key.data] += len(data)
                if counts[key.data] > 65536:
                    raise RuntimeError()
        if process.wait(timeout=max(0.01, deadline - time.monotonic())) != 0 or counts['stderr']:
            raise RuntimeError()
    finally:
        selector.close()
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        process.stdout.close()
        process.stderr.close()


def read_observation(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 16 * 1024 * 1024:
            raise RuntimeError()
        raw = stream.read(16 * 1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
        if len(raw) > 16 * 1024 * 1024 or (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise RuntimeError()
    return raw


def prepare(root, configuration):
    import local_build_contracts as contracts
    import package_exports as exports
    from source_inventory import checked_document
    root = Path(root).absolute()
    if configuration not in contracts.RUNTIME_LAYOUTS or not root.is_dir():
        raise InvalidArguments()
    descriptor = invoking_node()
    try:
        # Versions are checked by the genuine observer. Dependency closure is
        # deliberately unqualified on this direct compatibility route.
        with tempfile.TemporaryDirectory(prefix='workspace-export-observer-') as temporary:
            receipt = Path(temporary) / 'observation.json'
            driver = Path(__file__).with_name('typescript_observer.mjs')
            bounded_run(['/proc/self/fd/' + str(descriptor), str(driver), '--root', str(root),
                         '--config', configuration, '--output', str(receipt), '--verify-existing-outputs'],
                        root, descriptor)
            observation = checked_document(read_observation(receipt), json_only=True)
            if observation.get('output_mode') != 'verify-existing':
                raise RuntimeError()
            projection, _receipt = exports.prepare_projection(root, observation, root)
            return projection, observation
    finally:
        os.close(descriptor)


def main(argv=None):
    try:
        arguments = list(sys.argv[1:] if argv is None else argv)
        flags = [arg.split('=', 1)[0] for arg in arguments if arg.startswith('--')]
        if len(flags) != len(set(flags)):
            raise InvalidArguments()
        parser = Parser(add_help=False, allow_abbrev=False)
        parser.add_argument('--prepare-existing', action='store_true', required=True)
        parser.add_argument('--source-root', required=True)
        parser.add_argument('--configuration', required=True)
        args = parser.parse_args(arguments)
        result, observation = prepare(args.source_root, args.configuration)
        import package_exports as exports
        if result.get('configuration') != args.configuration:
            raise RuntimeError()
        exports.validate_current_projection(result, args.source_root, observation)
        status = 0
    except InvalidArguments:
        result, status = failure('arguments-invalid'), 1
    except Exception:
        result, status = failure('package-export-preparation-failed'), 1
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
