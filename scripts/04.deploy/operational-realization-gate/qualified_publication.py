"""Bind a freshly qualified image to same-daemon publication; never grant authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.qualified-image-publication
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Preserve exact qualified image identity through the existing staging publisher without rebuilding.
#   portability: {class: internal, targets: [kanbien-staging]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.local-container
#     path: scripts/04.deploy/operational-realization-gate/local_container.py
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
import local_container as container
import local_container_contracts as contracts
import release_compiler as release
from jsonschema import Draft202012Validator
from source_inventory import canonical, digest, checked_document

SCHEMA = release.SCHEMA_DIR / 'qualified-image-handoff.schema.yml'
REGISTRY = '337159794548.dkr.ecr.eu-west-1.amazonaws.com/platform-shell'
BLOCKED = {'authorized': False, 'release_eligibility': 'blocked', 'operation_authorization': 'blocked'}
MAX_BYTES = 16 * 1024 * 1024


def fail(code):
    raise release.ReleaseFailure('qualified-publication-' + code)


def read(path, maximum=MAX_BYTES):
    path = Path(path).absolute()
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    descriptor = None
    try:
        for component in path.parts[1:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent); parent = child
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            descriptor = None
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                fail('input-invalid')
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
            if len(raw) > maximum or (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns) != (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                fail('input-changed')
            return raw
    except OSError:
        fail('input-unreadable')
    finally:
        if descriptor is not None: os.close(descriptor)
        os.close(parent)


def bindings():
    return {'handoff_runner_digest': digest(read(Path(__file__))), 'schema_digest': digest(read(SCHEMA))}


def seal(value):
    value = dict(value)
    value.pop('handoff_digest', None)
    value['handoff_digest'] = digest(canonical(value))
    return value


def validate(value):
    schema = release.load_document(SCHEMA)
    try: Draft202012Validator(schema).validate(value)
    except Exception: fail('handoff-invalid')
    if seal(value) != value: fail('handoff-invalid')
    artifact = value['artifact']
    if (artifact['manifest_digest'] == artifact['configuration_digest']
            or artifact['daemon_image_id'] not in {artifact['manifest_digest'], artifact['configuration_digest']}):
        fail('image-binding-invalid')
    if ((value['phase'] == 'local-ready' and value['published_digest'] is not None)
            or (value['phase'] == 'registry-matched' and value['published_digest'] != artifact['manifest_digest'])):
        fail('publication-binding-invalid')
    return value


def destination(root, scratch, output, *, existing):
    scratch = container.checked_scratch(root, scratch)
    output = Path(output)
    if not output.is_absolute() or output.parent != scratch or output.name in {'', '.', '..'} or output.is_symlink():
        fail('directory-invalid')
    if existing:
        if not output.is_dir() or output.resolve(strict=True) != output:
            fail('directory-invalid')
    elif output.exists(): fail('directory-exists')
    return output


def current_result(root, result):
    profiles = container.container_profiles.discover(root)
    production = container.container_payload.production_packages(container.read(root, 'package-lock.json'), container.locked_toolchain.inspect_project(root))
    contracts.validate_result(result, profiles, production)
    if (container.repository_head(root) != result['repository_head']
            or container.load_lock(root) != result['lock']
            or container.implementation_digest(root) != result['runner_digest']
            or digest(canonical(container.source_manifest(root))) != result['build']['source_digest']
            or container.local_build.implementation_digest() != result['build']['runner_digest']):
        fail('source-changed')
    return result


def observed_image(engine, result):
    image = engine.inspect_image(result['image']['image_id'])
    image = dict(image)
    image['environment'] = [{'name':key,'value':value} for key,value in sorted(image['environment'].items())]
    if image != result['image'] or engine.inventory(image['image_id']) != result['payload']['files']:
        fail('image-changed')


def create(root, scratch, output, result, engine):
    root = Path(root).resolve(strict=True)
    output = destination(root, scratch, output, existing=False)
    initial_bindings = bindings()
    current_result(root, result)
    observed_image(engine, result)
    identity = engine.build_identity(result['image']['image_id'])
    value = seal({'schema':'qualified-image-handoff/v1','scope':'same-host-qualified-image',
        'verdict':'matched','phase':'local-ready',**BLOCKED,'same_host_only':True,
        'registry':REGISTRY,'published_digest':None,'container_result_digest':result['result_digest'],
        'source_commit':result['repository_head'],'source_digest':result['build']['source_digest'],
        'container_runner_digest':result['runner_digest'],'recipe_digest':result['lock']['recipe_digest'],
        'lock_digest':result['lock_digest'],'artifact':identity,**initial_bindings})
    validate(value)
    if bindings() != initial_bindings: fail('source-changed')
    current_result(root, result)
    output.mkdir(mode=0o700)
    for name, document in [('container-result.json',result),('handoff.json',value)]:
        with (output/name).open('xb') as stream:
            stream.write(canonical(document)+b'\n')
        (output/name).chmod(0o600)
    return value


def verify_published(value, raw):
    # Exact ECR BatchGetImage response; preserve manifest string bytes, do not
    # hash AWS CLI's newline-terminated text rendering or a reserialized object.
    response = checked_document(raw, json_only=True)
    if not isinstance(response,dict) or response.get('failures') or not isinstance(response.get('images'),list) or len(response['images']) != 1:
        fail('registry-response-invalid')
    image = response['images'][0]
    expected = value['artifact']['manifest_digest']
    if (not isinstance(image,dict) or image.get('registryId') != REGISTRY.split('.')[0]
            or image.get('repositoryName') != 'platform-shell'
            or image.get('imageId',{}).get('imageDigest') != expected
            or not isinstance(image.get('imageManifest'),str)):
        fail('registry-identity-invalid')
    manifest_bytes = image['imageManifest'].encode('utf8')
    if digest(manifest_bytes) != expected: fail('registry-manifest-changed')
    manifest = checked_document(manifest_bytes, json_only=True)
    if (manifest.get('schemaVersion') != 2 or type(manifest.get('schemaVersion')) is not int
            or manifest.get('mediaType') not in {'application/vnd.oci.image.manifest.v1+json','application/vnd.docker.distribution.manifest.v2+json'}
            or manifest.get('config',{}).get('digest') != value['artifact']['configuration_digest']
            or not isinstance(manifest.get('layers'),list) or not manifest['layers']):
        fail('registry-configuration-changed')
    return validate(seal({**value,'phase':'registry-matched','published_digest':expected}))


def verify(root, scratch, output, published=None):
    root = Path(root).resolve(strict=True)
    output = destination(root, scratch, output, existing=True)
    before = {'handoff.json':read(output/'handoff.json'),'container-result.json':read(output/'container-result.json')}
    value = validate(checked_document(before['handoff.json'], json_only=True))
    result = checked_document(before['container-result.json'], json_only=True)
    if value['phase'] != 'local-ready' or any(value[key] != item for key,item in bindings().items()):
        fail('source-changed')
    current_result(root, result)
    expected = {'container_result_digest':result['result_digest'],'source_commit':result['repository_head'],
        'source_digest':result['build']['source_digest'],'container_runner_digest':result['runner_digest'],
        'recipe_digest':result['lock']['recipe_digest'],'lock_digest':result['lock_digest']}
    if any(value[key] != item for key,item in expected.items()) or value['artifact']['daemon_image_id'] != result['image']['image_id']:
        fail('receipt-binding-invalid')
    with tempfile.TemporaryDirectory(prefix='qualified-publication-check-',dir=scratch) as private:
        observed_image(container.container_engine.Engine(Path(private)),result)
    if published is not None: value = verify_published(value, read(published, 1024*1024))
    current_result(root,result)
    if any(read(output/name) != raw for name,raw in before.items()) or any(value[key] != item for key,item in bindings().items()):
        fail('input-changed')
    return validate(value)


def main(argv=None):
    try:
        argv = list(sys.argv[1:] if argv is None else argv)
        flags = [arg.split('=',1)[0] for arg in argv if arg.startswith('--')]
        if len(flags) != len(set(flags)): fail('arguments-invalid')
        parser = release.SafeParser(add_help=False,allow_abbrev=False)
        for flag in ('source-root','scratch-root','publication-directory'): parser.add_argument('--'+flag,required=True)
        parser.add_argument('--published-image')
        args = parser.parse_args(argv)
        output = verify(args.source_root,args.scratch_root,args.publication_directory,args.published_image)
        validate(output)
        if any(output[key] != item for key,item in bindings().items()): fail('source-changed')
        status = 0
    except Exception:
        output={'schema':'qualified-image-publication-error/v1','verdict':'blocked',**BLOCKED,
                'findings':[{'code':'qualified-publication-refused'}]}
        status=1
    print(json.dumps(output,sort_keys=True,separators=(',',':')))
    return status


if __name__ == '__main__': raise SystemExit(main())
