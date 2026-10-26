#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.qualify-local-public-persistence-images
#   version: 2
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
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
    reviewed = {'scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh': '3831d15bd64161415c2262a69d4d66fdb3f101d11cbb0ba291be5496c437fda3', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh': 'faf4cb27f84d7e7e71aa818ff59f1efd94c62af4b5ec976265ab2be76ac13301', 'infra/04.deploy/03.product/image/core-server-persistence/Dockerfile': 'a9ef8f057231b695bde93f9058084f1c619f3ad23b652396afc9549b01d481dc', 'infra/04.deploy/03.product/image/core-server-persistence/image-contract.yml': '0c0730f20fdf4530f3eec2f1552f3bbc0faadc50f27d725d16459fbf3ac67003'}
    if package == 'core':
        reviewed = {'scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh': 'ff93bc6dfc355eba2f07ac042376bf2ea40371e8daf650d38226c8e2bbb2c644', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh': '0129e31693f2c15b4c4c3b172a94cf3696bdb6327d6b690fe0877b32711423a6', 'infra/04.deploy/03.product/image/core-server/Dockerfile': 'f764797f1a3f7a70e3904f5371bc9f2a7716c9bac0daf453840a488d348e2820', 'infra/04.deploy/03.product/image/core-server/image-contract.yml': '71e5efb910c80f449de0defdf80cb0310a7445d21a839b828f5ab56f94fbbb67'}
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
    postgres=re.findall(r' (postgres:[0-9]+-bookworm) (?:bash -ec|postgres -c) ',(root/(CORE_SMOKE if package == 'core' else SMOKE)).read_text())
    if package == 'persistence' and (len(postgres)!=2 or len(set(postgres))!=1): fail('local-public-recovery-test-image-not-public')

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
