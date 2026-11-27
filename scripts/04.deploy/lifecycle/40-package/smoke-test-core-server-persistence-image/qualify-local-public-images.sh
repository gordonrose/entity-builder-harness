#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.qualify-local-public-persistence-images
#   version: 7
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Qualify the fixed core or persistence package on the same local engine with a credential-free temporary Docker configuration when its native public-image credential helper is unavailable.
#   portability: { class: internal, targets: [] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.smoke-test-core-server-persistence-image.readme
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/README.md
set -euo pipefail
exec python3 -B - "$@" <<'PY'
import json
import os
from pathlib import Path
import re
import signal
import runpy
import hashlib
import stat
import subprocess
import sys
import tempfile
import yaml

BUILD = 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh'
SMOKE = 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh'
CORE_BUILD = 'scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh'
CORE_SMOKE = 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh'
RUNNER = 'scripts/01.harness/run-governed-script.sh'
class RecoveryFailure(Exception):
    def __init__(self,code,status=1): super().__init__(code);self.status=status
child = None

def fail(code,status=1): raise RecoveryFailure(code,status)
def observe(argv, env=None):
    try: result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired): fail('local-public-recovery-observation-unavailable')
    if result.returncode: fail('local-public-recovery-observation-failed')
    return result.stdout.strip()

def public_owners(root, package):
    # This optional recovery is qualified only for these reviewed owner bytes.
    # Fail closed on owner changes instead of interpreting arbitrary shell or
    # Dockerfile forms; normal package qualification remains independent.
    reviewed = {'scripts/04.deploy/shared/postgresql-version.py': '6837e934b412cd5685f7f113ce9944915973b7d89800a9318a7cbe226f3769b0', 'scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py': '540ab0f0f779f7b875fe070f49c940b57910b9419f203d2b8a881964b9f19439', 'scripts/04.deploy/shared/safe-command-diagnostics.sh': '3eb4218560e177d67a3b7a8cb0353268fd4004b13d769d193ec879d86d9c4e9f', 'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh': '3d9deb1ff75484a8d87f0ac824281411579d7ba120b0162785b9908d98eab79f', 'scripts/04.deploy/lifecycle/40-package/build-candidate-image/operations.sh': 'e4df5baa63a0dee4f57ff622bb279b8eb1bde54bef5b0b018f2b9647877de247', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh': 'a0f0bf44211510fc3a2c08f1cb7ed6d45d6a026878b089c36906a985d993ae78', 'infra/04.deploy/03.product/image/core-server-persistence/Dockerfile': 'acd1b6d74a552f8700f296989a6003a3080439b6bed291636bfc3d00465c190c', 'infra/04.deploy/03.product/image/core-server-persistence/image-contract.yml': 'ffddd0714c16629b0abc52a3ac271c487766675783d4fdfde2ea4a1074031534', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh': '0a56d1d262ef1da4f768e0ad6d498dbd72775fe9bba1d2725942f0758aee1afe', 'platform/adapters/aws/persistence/postgresql/tests/run-disposable-integration.mjs': '967883d6c24052c22c2e31824d158f18dc5e08798f3ceea81be6769b34ae5edf', 'scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh': '386b30f8fd36a6a97dc5fbb23acaba5811f3e9a06a8d3bdd692e433d292da54c'}
    if package == 'core':
        reviewed = {'scripts/04.deploy/shared/safe-command-diagnostics.sh': '3eb4218560e177d67a3b7a8cb0353268fd4004b13d769d193ec879d86d9c4e9f', 'scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh': '7f040575557148fa17990a017940e541ff2129d7bc65943314b69b3562f9fe8a', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh': '0129e31693f2c15b4c4c3b172a94cf3696bdb6327d6b690fe0877b32711423a6', 'infra/04.deploy/03.product/image/core-server/Dockerfile': '4f86081536340c57ecf54d1ad942c6f982e75e699cdb0c7a2107b6675725e4ba', 'infra/04.deploy/03.product/image/core-server/image-contract.yml': '71e5efb910c80f449de0defdf80cb0310a7445d21a839b828f5ab56f94fbbb67'}
    for path, digest in reviewed.items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest:
            fail('local-public-recovery-owner-review-required')
    image_directory = 'core-server' if package == 'core' else 'core-server-persistence'
    image_root = root / 'infra/04.deploy/03.product/image' / image_directory
    dockerfile=(image_root/'Dockerfile').read_text()
    contract=yaml.safe_load((image_root/'image-contract.yml').read_text())
    syntax=re.findall(r'^# syntax=(\S+)$',dockerfile,re.M)
    build=re.findall(r'^ARG BUILD_NODE_IMAGE=(\S+)$',dockerfile,re.M)
    runtime=re.findall(r'^ARG RUNTIME_NODE_IMAGE=(\S+)$',dockerfile,re.M)
    base=contract.get('runtime_base') if isinstance(contract,dict) else None
    if len(syntax)!=1 or re.fullmatch(r'docker/dockerfile:[0-9]+(?:\.[0-9]+)*',syntax[0]) is None: fail('local-public-recovery-frontend-not-public')
    if len(build)!=1 or re.fullmatch(r'node:[0-9]+-bookworm-slim',build[0]) is None: fail('local-public-recovery-build-image-not-public')
    if len(runtime)!=1 or re.fullmatch(r'gcr\.io/distroless/nodejs[0-9]+-debian[0-9]+@sha256:[0-9a-f]{64}',runtime[0]) is None or not isinstance(base,dict) or runtime[0]!=base.get('reference'): fail('local-public-recovery-runtime-image-not-public')
    if package == 'persistence':
        # Reviewed shell reads this contract through the reviewed version helper.
        # Source hashes above retain the no-arbitrary-command recovery boundary.
        try: runpy.run_path(str(root / "scripts/04.deploy/shared/postgresql-version.py"))["configuration"](contract)
        except ValueError: fail("local-public-recovery-test-image-not-public")
        nested=(root/'platform/adapters/aws/persistence/postgresql/tests/run-disposable-integration.mjs').read_text()
        nested_images=re.findall(r'["\'](postgres:[^"\']+)["\']',nested)
        if nested_images!=['postgres:17.11-bookworm']: fail('local-public-recovery-test-image-not-public')

def endpoint():
    # Docker documents DOCKER_CONTEXT precedence over DOCKER_HOST. Inspect that
    # explicit context rather than assuming context show reflects environment.
    context=os.environ.get('DOCKER_CONTEXT')
    if context:
        if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',context) is None: fail('local-public-recovery-context-invalid')
    elif os.environ.get('DOCKER_HOST'):
        return local_socket(os.environ['DOCKER_HOST'])
    else: context=observe(['docker','context','show'])
    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',context or '') is None: fail('local-public-recovery-context-invalid')
    try:
        data=json.loads(observe(['docker','context','inspect',context]))
        if not isinstance(data,list) or len(data)!=1 or data[0].get('Name')!=context: fail('local-public-recovery-context-invalid')
        return local_socket(data[0]['Endpoints']['docker']['Host'])
    except (KeyError,TypeError,AttributeError,json.JSONDecodeError): fail('local-public-recovery-context-invalid')

def local_socket(value):
    if not isinstance(value,str) or re.fullmatch(r'unix:///[A-Za-z0-9._/-]+',value) is None or '..' in Path(value[7:]).parts: fail('local-public-recovery-local-unix-endpoint-required')
    path=Path(value[7:])
    if not stat.S_ISSOCK(path.stat().st_mode): fail('local-public-recovery-local-unix-socket-missing')
    return value

def engine(env=None):
    identity=observe(['docker','info','--format','{{.ID}}'],env)
    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:_.-]{5,127}',identity) is None: fail('local-public-recovery-engine-identity-invalid')
    return identity

def interrupt(signum,frame):
    # Never wait inside a signal handler while Popen.wait holds its lock.
    if child is not None:
        try: os.killpg(child.pid,signal.SIGTERM)
        except ProcessLookupError: pass
    fail('local-public-recovery-interrupted',128+signum)

def execute(argv,root,environment):
    global child
    child=subprocess.Popen(argv,cwd=root,env=environment,start_new_session=True)
    try: return child.wait()
    except RecoveryFailure:
        try: child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait()
        raise
    finally: child=None

def main():
    args=sys.argv[1:];package='persistence'
    if args[:1] == ['--package']:
        if len(args)<2 or args[1] not in {'core','persistence'}: fail('local-public-recovery-arguments-invalid')
        package=args[1];args=args[2:]
    prefix='kanbien-core-server' if package == 'core' else 'kanbien-core-server-persistence'
    tag=prefix+':local-public-recovery';port='39454' if package == 'core' else '39455'
    if args:
        if len(args)!=4 or args[0]!='--tag' or args[2]!='--port': fail('local-public-recovery-arguments-invalid')
        tag,port=args[1],args[3]
    if re.fullmatch(re.escape(prefix)+r':[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}',tag) is None or not re.fullmatch(r'[0-9]{1,5}',port) or not 1024<=int(port)<=65535: fail('local-public-recovery-arguments-invalid')
    root=Path(observe(['git','rev-parse','--show-toplevel']));public_owners(root,package)
    host=endpoint();before=engine()
    with tempfile.TemporaryDirectory(prefix='persistence-public-docker-') as directory:
        # Nonempty anonymous registry entries suppress Docker's automatic
        # native-helper discovery without copying or supplying credentials.
        config=Path(directory);config.chmod(0o700);(config/'config.json').write_text(json.dumps({'auths':{'https://index.docker.io/v1/':{},'gcr.io':{}}})+'\n');(config/'config.json').chmod(0o600)
        environment={key:value for key,value in os.environ.items() if not key.startswith(('DOCKER_','BUILDX_','BUILDKIT_'))}
        environment.update(DOCKER_CONFIG=str(config),DOCKER_HOST=host,DOCKER_BUILDKIT='1',BUILDX_CONFIG=str(config/'buildx'),BUILDX_BUILDER='default')
        if engine(environment)!=before: fail('local-public-recovery-engine-mismatch')
        print(json.dumps({'schema':'deploy/local-public-qualification-report/v1','verdict':'bound','code':'same-local-engine-anonymous-config','package':package,'stored_configuration':'untouched'}),flush=True)
        # The fixed core smoke owns its build, so invoke it once. Persistence
        # keeps its established separate build and finished-image smoke stages.
        stages = [('smoke',[CORE_SMOKE,'--tag',tag,'--port',port])] if package == 'core' else [('build',[BUILD,'--tag',tag]),('smoke',[SMOKE,'--tag',tag,'--port',port])]
        for stage,arguments in stages:
            code=execute(['bash',RUNNER,'--approved-action',*arguments],root,environment)
            if code: fail('local-public-recovery-'+stage+'-failed',code if code>0 else 128-code)
            if engine(environment)!=before: fail('local-public-recovery-engine-mismatch')
    print(json.dumps({'schema':'deploy/local-public-qualification-report/v1','verdict':'passed','code':'existing-build-and-smoke-passed','package':package,'evidence_class':'container-qualification','stored_configuration':'untouched'}));return 0

signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
try: result=main()
except (RecoveryFailure,OSError,ValueError,TypeError,yaml.YAMLError) as error:
    print(json.dumps({'schema':'deploy/local-public-qualification-report/v1','verdict':'blocked','code':str(error) if isinstance(error,RecoveryFailure) else 'local-public-recovery-input-unavailable','exit_code':getattr(error,'status',1)}),file=sys.stderr);result=getattr(error,'status',1)
raise SystemExit(result)
PY
