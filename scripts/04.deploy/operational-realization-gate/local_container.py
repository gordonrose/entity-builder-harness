"""Qualify the selected local image through existing build and smoke wrappers."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.local-container
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Bind fresh locked payload, exact local image and isolated server evidence while preserving pending target tasks.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [writes-files, network]
#   used_by:
#   - id: deploy.script.build-platform-shell-image
#     path: scripts/04.deploy/build-platform-shell-image/script.sh
#   - id: deploy.script.smoke-test-platform-shell-image
#     path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import container_engine
import container_payload
import container_profiles
import local_build
from local_build_sandbox import canonical, digest, source_manifest
import local_container_contracts as contracts
import local_runtime
import locked_toolchain
import release_compiler as release

LOCK = 'scripts/04.deploy/operational-realization-gate/container-image.lock.json'
WRAPPERS = ('scripts/04.deploy/build-platform-shell-image/script.sh',
            'scripts/04.deploy/smoke-test-platform-shell-image/script.sh')


def fail(code):
    raise container_engine.EngineFailure('local-container-' + code)


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def read(root, relative):
    # The existing no-follow reader rejects symlinks and private source paths.
    return local_runtime.read_generator(root, relative)


def load_lock(root):
    lock = contracts.validate_lock(locked_toolchain._json(read(root, LOCK)))
    if digest(read(root, lock['recipe_path'])) != lock['recipe_digest']:
        fail('recipe-changed')
    if read(root, lock['recipe_path']).lstrip().startswith(b'# syntax='):
        fail('external-frontend-unsupported')
    return lock


def implementation_digest(root):
    files = ['local_container.py', 'local_container_contracts.py', 'container_engine.py',
             'container_payload.py', 'container_profiles.py', 'container-image.lock.json',
             'qualified_publication.py']
    rows = [{'path': name, 'digest': digest(read(DIRECTORY, name))} for name in files]
    rows.extend({'path': path, 'digest': digest(read(root, path))} for path in WRAPPERS)
    rows.append({'path': 'locked-build-implementation', 'digest': local_build.implementation_digest()})
    return digest(canonical(rows))


def checked_scratch(root, scratch):
    path = Path(scratch)
    if not path.is_absolute() or path.is_symlink() or path.resolve(strict=True) != path or not path.is_dir():
        fail('scratch-invalid')
    if path == root or path.is_relative_to(root):
        fail('scratch-invalid')
    mounts = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left, right = line.split(' - ', 1)
        mount = Path(left.split()[4].replace('\\040', ' ').replace('\\134', '\\'))
        if path.is_relative_to(mount):
            mounts.append((len(mount.parts), right.split()[0]))
    if not mounts or max(mounts)[1] in {'tmpfs', 'ramfs'}:
        fail('scratch-memory-backed')
    return path


def repository_head(root):
    try:
        value = subprocess.check_output(['/usr/bin/git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'],
            env={'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1'}, stderr=subprocess.DEVNULL,
            timeout=10).decode('ascii').strip()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        fail('repository-head-unavailable')
    if not re.fullmatch(r'[0-9a-f]{40}', value):
        fail('repository-head-invalid')
    return value


def check_base(base, lock):
    if (base['image_id'] not in {lock['runtime_config_digest'], lock['runtime_image'].split('@')[1]} or lock['runtime_image'] not in base['repo_digests']
            or base['os'] != 'linux' or base['architecture'] != 'amd64'):
        fail('base-binding-invalid')


def run(root, package_cache, scratch, publication_directory=None):
    root = Path(root).resolve(strict=True)
    scratch = checked_scratch(root, scratch)
    if publication_directory is not None:
        import qualified_publication
        qualified_publication.destination(root, scratch, publication_directory, existing=False)
    lock = load_lock(root)
    revision = implementation_digest(root)
    profiles = container_profiles.discover(root)
    production = container_payload.production_packages(read(root, 'package-lock.json'), locked_toolchain.inspect_project(root))
    started = now()
    head = repository_head(root)
    with tempfile.TemporaryDirectory(prefix='release-control-image-', dir=scratch) as temporary:
        work = Path(temporary)
        executor = container_engine.Engine(work)
        engine_version = executor.version()
        base = executor.base_identity(lock['runtime_image'])
        check_base(base, lock)
        context = work / 'context'; context.mkdir()
        payload = container_payload.prepare(root, package_cache, scratch, context / 'payload')
        container_profiles.require_payload(profiles, payload['files'])
        recipe = read(root, lock['recipe_path'])
        (context / 'Dockerfile').write_bytes(recipe)
        cert_path = context / payload['certificate']['source_path']
        cert_path.parent.mkdir(parents=True)
        cert_path.write_bytes((context / 'payload' / payload['certificate']['path']).read_bytes())
        # Context contains only the verified payload, public certificate and exact recipe.
        context_before = local_runtime.fingerprint(local_runtime.artifacts.artifact_files(context))
        image_id = executor.build(context, context / 'Dockerfile', lock['runtime_image'], head)
        image = executor.inspect_image(image_id)
        observed = executor.inventory(image_id)
        if observed != payload['files']:
            fail('image-payload-mismatch')
        runtime = executor.run_server(image_id)
        if executor.inspect_image(image_id) != image:
            fail('image-changed')
        if local_runtime.fingerprint(local_runtime.artifacts.artifact_files(context)) != context_before:
            fail('context-changed')
        if (implementation_digest(root) != revision or load_lock(root) != lock
                or container_profiles.discover(root) != profiles
                or digest(canonical(source_manifest(root))) != payload['build_result']['source_digest']
                or digest(container_payload.certificate(root)) != payload['certificate']['digest']
                or repository_head(root) != head):
            fail('source-changed')
        image['environment'] = [{'name': key, 'value': value} for key, value in sorted(image['environment'].items())]
        build = payload.pop('build_result')
        result = {'schema': 'local-container-result/v1', 'scope': 'selected-local-container', 'verdict': 'passed',
                  'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked',
                  'qualification_verdict': 'blocked', 'source_closure': 'blocked', 'repository_head': head,
                  'started_at': started, 'completed_at': now(), 'runner_digest': revision,
                  'lock_digest': contracts.digest(lock), 'lock': lock, 'build': build, 'payload': payload,
                  'base': base, 'image': image, 'image_payload_digest': digest(canonical(observed)),
                  'engine': engine_version, 'runtime': runtime,
                  'profiles': contracts.promote_local_profile(profiles),
                  'profile_inventory_digest': digest(canonical(profiles))}
        result['result_digest'] = contracts.digest(result)
        result = contracts.validate_result(result, profiles, production)
        if publication_directory is not None:
            qualified_publication.create(root, scratch, publication_directory, result, executor)
        return result


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        flags = [arg.split('=', 1)[0] for arg in argv if arg.startswith('--')]
        if len(flags) != len(set(flags)):
            fail('arguments-invalid')
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument('--source-root', required=True)
        parser.add_argument('--scratch-root', required=True)
        parser.add_argument('--package-cache')
        parser.add_argument('--acquire-base', action='store_true')
        parser.add_argument('--publication-directory')
        args = parser.parse_args(argv)
        if bool(args.package_cache) == args.acquire_base or (args.acquire_base and args.publication_directory):
            fail('arguments-invalid')
        root = Path(args.source_root).resolve(strict=True)
        scratch = checked_scratch(root, args.scratch_root)
        if args.acquire_base:
            lock = load_lock(root)
            with tempfile.TemporaryDirectory(prefix='release-control-base-', dir=scratch) as temporary:
                base = container_engine.Engine(Path(temporary)).acquire(lock['runtime_image'])
                check_base(base, lock)
            result = {'schema': 'local-container-acquisition/v1', 'verdict': 'verified', 'authorized': False,
                      'runtime_image': lock['runtime_image'], 'image_id': base['image_id']}
        else:
            result = (run(root, args.package_cache, scratch, args.publication_directory)
                      if args.publication_directory is not None else run(root, args.package_cache, scratch))
        status = 0
    except Exception as error:
        code = getattr(error, 'code', str(error))
        if type(code) is not str or not re.fullmatch(r'(?:local-container|local-build|container-payload|container-profile|toolchain)-[a-z-]+', code):
            code = 'local-container-verification-failed'
        result = {'schema': 'local-container-error/v1', 'verdict': 'failed', 'authorized': False,
                  'release_eligibility': 'blocked', 'operation_authorization': 'blocked', 'findings': [{'code': code}]}
        status = 1
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
