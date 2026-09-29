"""Validate unsigned local image evidence without granting deployment authority."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.local-container-contracts
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate exact payload and command bindings while keeping every target task and release authority blocked.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.local-container
#     path: scripts/04.deploy/operational-realization-gate/local_container.py

from copy import deepcopy
from datetime import datetime
import build_contracts
import local_build_contracts as builds
import release_compiler as release

PREFIX = '.cache/platform-shell-image-build/'
CERTIFICATE = 'assets/rds-eu-west-1-bundle.crt'
CONFIGURATION = 'platform/server/tsconfig.image.json'


def fail(code):
    raise release.ReleaseFailure('local-container-' + code)


def digest(value):
    return release.digest_document(value)


def promote_local_profile(profiles):
    rows = deepcopy(profiles)
    defaults = [row for row in rows if row['id'] == 'image-default']
    if len(defaults) != 1 or any(row['status'] != 'pending' for row in rows):
        fail('profile-inventory-invalid')
    defaults[0].update(status='local-health-passed', reason='local-health-verified')
    return rows


def validate_lock(document):
    build_contracts.validate_schema('local-container-lock', document)
    return document


def validate_result(document, expected_profiles, expected_production):
    """Expected profiles must come from the caller's fresh source collector.

    This validates local accounting, not authenticity. No saved-result authority
    or generic admission interface is supplied by this module.
    """
    build_contracts.validate_schema('local-container-result', document)
    builds.checked_digest(document, 'result_digest')
    validate_lock(document['lock'])
    if digest(document['lock']) != document['lock_digest']:
        fail('lock-binding-invalid')
    try:
        start = datetime.strptime(document['started_at'], '%Y-%m-%dT%H:%M:%SZ')
        end = datetime.strptime(document['completed_at'], '%Y-%m-%dT%H:%M:%SZ')
        if end < start:
            fail('time-invalid')
    except ValueError:
        fail('time-invalid')
    build, payload = document['build'], document['payload']
    builds.result(build)
    if (build['verdict'] != 'passed' or len(build['builds']) != 1
            or build['builds'][0]['configuration'] != CONFIGURATION):
        fail('build-binding-invalid')
    runtime = build['builds'][0]['runtime']
    if runtime is None or runtime['kind'] != 'image-shim-generator':
        fail('build-binding-invalid')
    paths = builds.unique_paths(payload['files'])
    if payload['files'] != sorted(payload['files'], key=lambda row: row['path']):
        fail('payload-order-invalid')
    if any(path.endswith(('.ts', '.tsx', '.mts', '.cts')) for path in paths):
        fail('payload-source-fallback')
    if (digest(payload['files']) != payload['payload_digest']
            or document['image_payload_digest'] != payload['payload_digest']):
        fail('payload-binding-invalid')
    compiled = [{**row, 'path': PREFIX + row['path']} for row in runtime['artifact_files']]
    selected = [row for row in payload['files'] if row['path'].startswith(PREFIX)]
    if sorted(compiled, key=lambda row: row['path']) != selected:
        fail('artifact-binding-invalid')
    production = payload['production_dependencies']
    if production != expected_production:
        fail('production-selection-invalid')
    package_paths = builds.unique_paths(production)
    if production != sorted(production, key=lambda row: row['path']):
        fail('dependency-order-invalid')
    for row in production:
        if (row['path'] != 'node_modules/' + row['name'] or row['name'] == 'typescript'
                or row['name'].startswith('@types/') or row['path'] + '/package.json' not in paths):
            fail('production-dependency-invalid')
    dependencies = [row for row in payload['files'] if row['path'].startswith('node_modules/')]
    if (any(not any(row['path'].startswith(package + '/') for package in package_paths)
            for row in dependencies) or digest(dependencies) != payload['production_dependency_digest']):
        fail('production-binding-invalid')
    excluded = payload['excluded_dependency_files']
    excluded_paths = builds.unique_paths(excluded)
    if (excluded != sorted(excluded, key=lambda row: row['path']) or excluded_paths & paths
            or any(not path.startswith('node_modules/') or path.endswith(('.ts', '.tsx', '.mts', '.cts'))
                   or any(path.startswith(package + '/') for package in package_paths) for path in excluded_paths)
            or digest(sorted(dependencies + excluded, key=lambda row: row['path'])) != runtime['copied_dependency_digest']):
        fail('dependency-build-binding-invalid')
    cert = payload['certificate']
    if ({'path': CERTIFICATE, 'digest': cert['digest'], 'bytes': cert['bytes']} not in payload['files']
            or set(paths) != {row['path'] for row in selected + dependencies} | {CERTIFICATE}):
        fail('payload-membership-invalid')
    base, image, execution = document['base'], document['image'], document['runtime']
    if (base['image_id'] not in {document['lock']['runtime_config_digest'], document['lock']['runtime_image'].split('@')[1]}
            or document['lock']['runtime_image'] not in base['repo_digests']):
        fail('base-binding-invalid')
    if (execution['image_id'] != image['image_id'] or execution['entrypoint'] != image['entrypoint']
            or execution['command'] != image['command']):
        fail('runtime-binding-invalid')
    env = {row['name']: row['value'] for row in image['environment']}
    fixed = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
             'SSL_CERT_FILE': '/etc/ssl/certs/ca-certificates.crt', 'LANG': 'C.UTF-8',
             'NODE_ENV': 'production', 'HOST': '0.0.0.0', 'PORT': '3000',
             'PLATFORM_SOURCE_COMMIT_SHA': document['repository_head']}
    if (len(env) != len(image['environment']) or any(value != fixed[name] for name, value in env.items())
            or not {'NODE_ENV', 'HOST', 'PORT', 'PLATFORM_SOURCE_COMMIT_SHA'} <= env.keys()):
        fail('environment-binding-invalid')
    if (document['profiles'] != promote_local_profile(expected_profiles)
            or document['profile_inventory_digest'] != digest(expected_profiles)):
        fail('profile-binding-invalid')
    default = next(row for row in document['profiles'] if row['id'] == 'image-default')
    if (default['command'] != image['command'] or default['image_scope'] != 'product'
            or default['kind'] != 'service' or default['source_path'] != document['lock']['recipe_path']
            or default['source_digest'] != document['lock']['recipe_digest']):
        fail('default-profile-invalid')
    for row in document['profiles']:
        if row['image_scope'] == 'product' and (len(row['command']) != 1 or row['command'][0] not in paths):
            fail('profile-command-missing')
    return document
