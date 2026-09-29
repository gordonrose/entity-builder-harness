"""Qualify existing packaged bootstrap/migration against an independent real engine."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.dependency-effects
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify exact packaged command effects against disposable PostgreSQL while blocking provider and release authority.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.script.smoke-test-platform-shell-image
#     path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh

import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import dependency_effect_contracts as contracts
from dependency_effect_engine import DependencyEngine
import local_container
import container_profiles
from container_engine import EngineFailure
from locked_toolchain import ToolchainFailure
import release_compiler as release
from local_build_sandbox import LocalBuildFailure, canonical, digest, source_manifest

LOCK = 'scripts/04.deploy/operational-realization-gate/dependency-image.lock.json'
EXPECTATIONS = 'scripts/04.deploy/operational-realization-gate/fixtures/dependency-effects/expectations.json'

# Explicitly reviewed upstream message codes. New categories remain redacted
# until this public boundary is reviewed; safe-looking arbitrary messages do not
# become evidence merely because they use a known exception type.
BUILD_FAILURE_CODES = frozenset("""
container-payload-build-failed container-payload-certificate-invalid container-payload-closure-invalid
container-payload-copy-changed container-payload-destination-invalid
container-payload-export-binding-invalid container-payload-lock-invalid
container-payload-production-closure-empty container-payload-production-closure-incomplete
container-payload-production-flags-unsupported container-payload-production-package-missing
container-payload-production-source-fallback container-payload-runtime-invalid
container-payload-source-changed container-payload-source-fallback local-build-arguments-invalid
local-build-configuration-unsupported local-build-dependency-changed local-build-environment-invalid
local-build-environment-unsupported local-build-exit-observation-mismatch local-build-export-invalid
local-build-input-binding-invalid local-build-isolation-unavailable local-build-npm-config-unsupported
local-build-observation-duplicate-key local-build-output-changed local-build-output-limit
local-build-output-link local-build-output-membership-invalid local-build-scratch-invalid
local-build-scratch-memory-backed local-build-scratch-required local-build-selected-graph-changed
local-build-source-changed local-build-source-file-invalid local-build-source-limit local-build-source-link
local-build-source-path-invalid local-build-source-root-invalid local-build-timeout
local-build-write-boundary-invalid
""".split())
TOOLCHAIN_FAILURE_CODES = frozenset("""
locked-toolchain-acquisition-failed locked-toolchain-archive-duplicate locked-toolchain-archive-invalid
locked-toolchain-archive-limit locked-toolchain-archive-link-invalid
locked-toolchain-archive-member-unsupported locked-toolchain-archive-mode-unsupported
locked-toolchain-archive-root-invalid locked-toolchain-cache-binding-mismatch
locked-toolchain-cache-bytes-invalid locked-toolchain-cache-closure-mismatch
locked-toolchain-cache-directory-invalid locked-toolchain-cache-filename-invalid
locked-toolchain-cache-lock-mismatch locked-toolchain-cache-manifest-mismatch
locked-toolchain-cache-record-invalid locked-toolchain-cache-write-failed locked-toolchain-command-failed
locked-toolchain-contract-invalid locked-toolchain-dependency-closure-invalid
locked-toolchain-dependency-count-mismatch locked-toolchain-dependency-layout-unsupported
locked-toolchain-dependency-lock-mismatch locked-toolchain-dependency-lock-version
locked-toolchain-dependency-record-invalid locked-toolchain-dependency-source-unsupported
locked-toolchain-dependency-version-invalid locked-toolchain-download-failed locked-toolchain-download-limit
locked-toolchain-download-redirect locked-toolchain-execution-failed locked-toolchain-file-invalid
locked-toolchain-file-limit locked-toolchain-file-unavailable locked-toolchain-input-invalid
locked-toolchain-installation-destination-invalid locked-toolchain-installed-bin-mismatch
locked-toolchain-installed-closure-mismatch locked-toolchain-installed-layout-invalid
locked-toolchain-installed-package-files-mismatch locked-toolchain-installed-package-invalid
locked-toolchain-installed-package-link locked-toolchain-installed-verification-failed
locked-toolchain-installed-workspace-link-mismatch locked-toolchain-integrity-invalid
locked-toolchain-json-duplicate locked-toolchain-json-invalid locked-toolchain-json-limit
locked-toolchain-manifest-lock-mismatch locked-toolchain-node-extraction-failed
locked-toolchain-node-hash-mismatch locked-toolchain-npm-pin-mismatch locked-toolchain-package-hash-mismatch
locked-toolchain-package-identity-mismatch locked-toolchain-package-layout-invalid
locked-toolchain-package-manifest-invalid locked-toolchain-path-invalid
locked-toolchain-platform-unsupported locked-toolchain-project-configuration-unsupported
locked-toolchain-runtime-version-mismatch locked-toolchain-schema-invalid locked-toolchain-schema-open
locked-toolchain-schema-reference locked-toolchain-schema-version locked-toolchain-source-manifest-changed
locked-toolchain-typescript-pin-mismatch locked-toolchain-workspace-lifecycle-unsupported
locked-toolchain-workspace-limit locked-toolchain-workspace-link-invalid
locked-toolchain-workspace-link-mismatch locked-toolchain-workspace-lock-mismatch
locked-toolchain-workspace-manifest-invalid locked-toolchain-workspace-manifest-lock-mismatch
locked-toolchain-workspace-membership-mismatch locked-toolchain-workspace-path-invalid
locked-toolchain-workspace-pattern-unsupported
""".split())


def snapshot(root):
    paths = [LOCK, EXPECTATIONS, *('scripts/04.deploy/operational-realization-gate/' + name for name in
        ('dependency_effects.py', 'dependency_effect_engine.py', 'dependency_effect_contracts.py')),
        *('infra/04.deploy/contracts/release-control/v1/' + name + '.schema.yml' for name in contracts.SCHEMAS)]
    files = {name: local_container.read(root, name) for name in paths}
    for name in paths[2:]:
        folder = contracts.build_contracts.SCHEMA_DIR if name.endswith('.schema.yml') else DIRECTORY
        if files[name] != local_container.read(folder, Path(name).name):
            contracts.fail('source-changed')
    rows = [{'path': name, 'digest': digest(raw)} for name, raw in sorted(files.items())]
    rows.append({'path': 'existing-image-runner', 'digest': local_container.implementation_digest(root)})
    return files, digest(canonical(rows))


def empty_state(state):
    return state == {'roles': [], 'memberships': [], 'schema_owner': None, 'tables': [], 'runtime_schema_create': None,
                     'runtime_database_create': None, 'migration_schema_create': None, 'history': [], 'columns': [], 'constraints': []}


def bootstrap_state(state):
    return (type(state) is dict and state.get('roles') == [
        {'name': 'psmokemigrate', 'login': True, 'elevated': False},
        {'name': 'psmokeruntime', 'login': True, 'elevated': False}]
        and state.get('memberships') == [] and state.get('schema_owner') == 'psmokemigrate' and state.get('runtime_schema_create') is False
        and state.get('runtime_database_create') is False and state.get('migration_schema_create') is True)


def migration_state(state, expected):
    contracts.validate_expectations(expected)
    if (not bootstrap_state(state) or state['tables'] != [
            {'name': name, 'owner': 'psmokemigrate', 'runtime_dml': True} for name in expected['tables']]
            or state.get('columns') != expected['columns'] or state.get('constraints') != expected['constraints']
            or type(state['history']) is not list or len(state['history']) != 2):
        return False
    return all(type(row) is dict and set(row) == {'id', 'checksum', 'tool_version', 'applied_at'}
               and row['id'] == name and row['checksum'] == checksum and row['tool_version'] == 'stage6-staging'
               and type(row['applied_at']) is str and len(row['applied_at']) < 64
               for row, (name, checksum) in zip(state['history'], sorted(expected['migration_checksums'].items())))


def check_case(name, before, after, expected):
    good = False
    if name in {'bootstrap-binding-invalid', 'bootstrap-untrusted-ca', 'bootstrap-bad-password'}:
        good = empty_state(before) and empty_state(after)
    elif name == 'bootstrap':
        good = empty_state(before) and bootstrap_state(after) and after['tables'] == [] and after['history'] == []
    elif name == 'bootstrap-repeat':
        good = bootstrap_state(before) and before == after
    elif name == 'migration-denied':
        good = bootstrap_state(before) and bootstrap_state(after) and after['tables'] == [] and after['history'] == []
    elif name == 'migration':
        good = before['tables'] == [] and before['history'] == [] and migration_state(after, expected)
    elif name == 'migration-repeat':
        good = migration_state(before, expected) and before == after
    elif name == 'migration-checksum-mismatch':
        expected_corruption = json.loads(json.dumps(expected))
        expected_corruption['migration_checksums']['v0002_platform_smoke_work_item'] = '0' * 64
        good = migration_state(before, expected_corruption) and before == after
    if not good:
        contracts.fail('independent-effect-mismatch')


def profile(build, revision, lock, dependency_id, expected):
    return contracts.validate_profile({'schema': 'dependency-effect-profile/v1', 'scope': 'local-packaged-postgresql-effects',
        'repository_head': build['repository_head'], 'source_digest': build['build']['source_digest'],
        'build_result_digest': build['result_digest'], 'runner_digest': revision,
        'lock_digest': contracts.digest(lock), 'expectations_digest': contracts.digest(expected),
        'artifact': {'image_id': build['image']['image_id'], 'payload_digest': build['image_payload_digest']},
        'dependency': {'image': lock['image'], 'image_id': dependency_id, 'engine_version': lock['engine_version'],
                       'network': 'owned-internal', 'published_ports': [], 'tls': 'verify-full-local-ca'},
        'commands': contracts.COMMANDS, 'schema_digests': contracts.schema_digests()})


def run(root, scratch, package_cache):
    root = Path(root).resolve(strict=True)
    scratch = local_container.checked_scratch(root, scratch)
    files, revision = snapshot(root)
    lock = contracts.validate_lock(json.loads(files[LOCK]))
    expected = contracts.validate_expectations(json.loads(files[EXPECTATIONS]))
    # Dependency must already be pinned/acquired; do not spend a build before checking it.
    work = Path(tempfile.mkdtemp(prefix='dependency-effects-', dir=scratch))
    engine = DependencyEngine(work)
    try:
        dependency_id = engine.dependency_identity(lock)
        built = local_container.run(root, package_cache, scratch)
        bound_profile = profile(built, revision, lock, dependency_id, expected)
        image_id = bound_profile['artifact']['image_id']
        engine.inspect_image(image_id)
        if engine.inventory(image_id) != built['payload']['files']:
            contracts.fail('payload-mismatch')
        version = engine.version()
        certificate_digest = engine.prepare_certificates()
        engine.create_network()
        engine.start_dependency(dependency_id)
        engine.verify_tls()
        cases = []
        for name, task, outcome, assertions in contracts.CASES:
            if name == 'migration-checksum-mismatch':
                engine.sql('corrupt')
            before = engine.snapshot()
            execution = engine.run_task(image_id, task, name, outcome)
            after = engine.snapshot()
            check_case(name, before, after, expected)
            cases.append({'case': name, 'task': task, 'outcome': outcome, **execution,
                          'before_digest': contracts.digest(before), 'after_digest': contracts.digest(after),
                          'assertions': [{'id': item, 'verdict': 'passed'} for item in assertions]})
        engine.restore_checksum(expected)
        final_state = engine.snapshot()
        if not migration_state(final_state, expected):
            contracts.fail('independent-effect-mismatch')
        for privilege in ('select', 'insert', 'update', 'delete'):
            engine.sql('revoke-' + privilege)
            if migration_state(engine.snapshot(), expected):
                contracts.fail('grant-fault-not-detected')
            engine.sql('grant-' + privilege)
        engine.sql('runtime-denied', expected_failure=True)
        engine.sql('runtime-dml')
        if engine.snapshot() != final_state:
            contracts.fail('independent-effect-mismatch')
        if (snapshot(root)[1] != revision
                or digest(canonical(source_manifest(root))) != bound_profile['source_digest']
                or local_container.repository_head(root) != bound_profile['repository_head']
                or engine.inventory(image_id) != built['payload']['files']):
            contracts.fail('source-changed')
    finally:
        # Never report passed when any owned container/network cleanup is unknown.
        # On cleanup failure preserve the private directory for explicit recovery.
        engine.cleanup_all()
        shutil.rmtree(work)
    result = contracts.make_result(bound_profile, engine.run_id, cases, certificate_digest, version)
    # Retain the complete validated upstream receipt; a digest alone is not reviewable evidence.
    evidence = scratch / ('dependency-effect-evidence-' + engine.run_id)
    evidence.mkdir(mode=0o700)
    for name, document in (('build-result.json', built), ('effect-result.json', result)):
        with (evidence / name).open('xb') as stream:
            stream.write(canonical(document) + b'\n')
        (evidence / name).chmod(0o600)
    return result


def safe_failure_code(error):
    # Only reviewed exception contracts can carry public diagnostics. In
    # particular, arbitrary exceptions must never fall back to str(error).
    if type(error) is LocalBuildFailure:
        return str(error) if str(error) in BUILD_FAILURE_CODES else 'dependency-effect-verification-failed'
    elif type(error) is ToolchainFailure:
        return str(error) if str(error) in TOOLCHAIN_FAILURE_CODES else 'dependency-effect-verification-failed'
    elif type(error) in (EngineFailure, release.ReleaseFailure):
        code, prefix = error.code, r'(?:dependency-effect|local-container|container-profile)'
    else:
        return 'dependency-effect-verification-failed'
    if type(code) is str and len(code) <= 96 and re.fullmatch(prefix + r'-[a-z]+(?:-[a-z]+)*', code):
        return code
    return 'dependency-effect-verification-failed'


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        flags = [arg.split('=', 1)[0] for arg in argv if arg.startswith('--')]
        if len(flags) != len(set(flags)):
            contracts.fail('arguments-invalid')
        parser = release.SafeParser(add_help=False, allow_abbrev=False)
        parser.add_argument('--source-root', required=True)
        parser.add_argument('--scratch-root', required=True)
        parser.add_argument('--package-cache')
        parser.add_argument('--acquire-dependency', action='store_true')
        args = parser.parse_args(argv)
        if bool(args.package_cache) == args.acquire_dependency:
            contracts.fail('arguments-invalid')
        root = Path(args.source_root).resolve(strict=True)
        scratch = local_container.checked_scratch(root, args.scratch_root)
        if args.acquire_dependency:
            files, _ = snapshot(root)
            lock = contracts.validate_lock(json.loads(files[LOCK]))
            with tempfile.TemporaryDirectory(prefix='dependency-acquisition-', dir=scratch) as temporary:
                image_id = DependencyEngine(Path(temporary)).dependency_identity(lock, acquire=True)
            result = {'schema': 'dependency-effect-acquisition/v1', 'verdict': 'verified', **contracts.BLOCKED,
                      'image': lock['image'], 'image_id': image_id}
        else:
            result = run(root, scratch, args.package_cache)
        status = 0
    except (Exception, KeyboardInterrupt) as error:
        code = safe_failure_code(error)
        result = {'schema': 'dependency-effect-error/v1', 'verdict': 'failed', **contracts.BLOCKED, 'findings': [{'code': code}]}
        status = 1
    print(json.dumps(result, sort_keys=True))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
