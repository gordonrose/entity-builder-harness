#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.local-public-persistence-recovery
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise bounded local public-image recovery with controlled Docker and governed-command substitutes; never contact a real engine.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.core-server-persistence-image-payload-fixture
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/payload-fixture-test.sh
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[5]
DIRECTORY=Path('scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image')
WRAPPER=ROOT/DIRECTORY/'qualify-local-public-images.sh'
BUILD=Path('scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh')
SMOKE=DIRECTORY/'script.sh'
DOCKERFILE=Path('infra/04.deploy/03.product/image/core-server-persistence/Dockerfile')
CONTRACT=DOCKERFILE.with_name('image-contract.yml')
DIAGNOSTIC_CHECK=Path('scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-diagnostics-check.sh')
INTEGRATION_CHECK=Path('scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/postgresql-integration-check.sh')
INTEGRATION_RUNNER=Path('platform/adapters/aws/persistence/postgresql/tests/run-disposable-integration.mjs')
COUNT=0
FAKE_DOCKER='''import json,os,sys
from pathlib import Path
args=sys.argv[1:];original=os.environ['RECOVERY_ORIGINAL'];config=os.environ.get('DOCKER_CONFIG');isolated=config!=original
entry={'kind':'docker','args':args,'config':config,'isolated':isolated}
with open(os.environ['RECOVERY_EVENTS'],'a') as stream:stream.write(json.dumps(entry)+'\\n')
if args==['context','show']:print('default')
elif args[:2]==['context','inspect']:
 if os.environ.get('RECOVERY_CONTEXT_BAD'):print('[]')
 else:print(json.dumps([{'Name':args[2],'Endpoints':{'docker':{'Host':os.environ['RECOVERY_ENDPOINT']}}}]))
elif args==['info','--format','{{.ID}}']:
 if isolated:
  assert json.loads(Path(config,'config.json').read_text())=={'auths':{'https://index.docker.io/v1/':{},'gcr.io':{}}}
  assert Path(config).stat().st_mode & 0o777==0o700
  assert Path(config,'config.json').stat().st_mode & 0o777==0o600
  assert os.environ['DOCKER_HOST']==os.environ['RECOVERY_EXPECTED_ENDPOINT']
  allowed={'DOCKER_CONFIG','DOCKER_HOST','DOCKER_BUILDKIT','BUILDX_CONFIG','BUILDX_BUILDER'}
  assert not {key for key in os.environ if key.startswith(('DOCKER_','BUILDX_','BUILDKIT_'))}-allowed
  assert os.environ['BUILDX_CONFIG']==str(Path(config,'buildx')) and os.environ['BUILDX_BUILDER']=='default'
 mode=os.environ.get('RECOVERY_ENGINE_MODE','')
 if mode=='malformed':print('invalid identity with spaces')
 elif isolated and (mode=='mismatch' or mode=='after-build' and Path(os.environ['RECOVERY_BUILD_DONE']).exists()):print('other-engine-id')
 else:print('same-local-engine-id')
else:raise AssertionError('unexpected Docker action '+repr(args))
'''
FAKE_BASH='''import json,os,sys,time
from pathlib import Path
args=sys.argv[1:]
assert args[0]=='scripts/01.harness/run-governed-script.sh' and args[1]=='--approved-action'
command=args[2];stage='build' if command==os.environ['RECOVERY_BUILD'] else 'smoke'
assert command in {os.environ['RECOVERY_BUILD'],os.environ['RECOVERY_SMOKE']}
expected=['--tag','kanbien-core-server-persistence:test']+([] if stage=='build' else ['--port','39456'])
assert args[3:]==expected,args
config=Path(os.environ['DOCKER_CONFIG'])
assert str(config)!=os.environ['RECOVERY_ORIGINAL'] and json.loads((config/'config.json').read_text())=={'auths':{'https://index.docker.io/v1/':{},'gcr.io':{}}}
with open(os.environ['RECOVERY_EVENTS'],'a') as stream:stream.write(json.dumps({'kind':'stage','stage':stage,'argv':args,'config':str(config)})+'\\n')
if stage=='build':Path(os.environ['RECOVERY_BUILD_DONE']).touch()
if os.environ.get('RECOVERY_SLEEP')==stage:time.sleep(60)
if os.environ.get('RECOVERY_FAIL')==stage:raise SystemExit(42)
'''

def run_case(name,*,environment=None,arguments=None,mutate=None,expected=0,code=None,stages=None,terminate=False):
 global COUNT
 with tempfile.TemporaryDirectory(prefix='public-recovery-test-') as directory:
  fixture=Path(directory);binaries=fixture/'bin';binaries.mkdir();events=fixture/'events';events.touch()
  for relative in (BUILD,SMOKE,DOCKERFILE,CONTRACT,DIAGNOSTIC_CHECK,INTEGRATION_CHECK,INTEGRATION_RUNNER):
   path=fixture/relative;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,path)
  original=fixture/'original-docker';original.mkdir(mode=0o700);(original/'config.json').write_text('{"credsStore":"untouched-fixture-helper","auths":{"fixture.invalid":{"auth":"fixture-only"}}}\n');(original/'context').write_text('unchanged-context\n');original_files={p.name:(p.read_bytes(),stat.S_IMODE(p.stat().st_mode)) for p in original.iterdir()}
  for binary,text in [('git',"import os\nprint(os.environ['RECOVERY_ROOT'])\n"),('docker',FAKE_DOCKER),('bash',FAKE_BASH)]:
   path=binaries/binary;path.write_text('#!'+sys.executable+'\n'+text);path.chmod(0o755)
  endpoint='unix://'+str(fixture/'engine.sock')
  with socket.socket(socket.AF_UNIX) as bound:
   bound.bind(str(fixture/'engine.sock'))
   env={key:value for key,value in os.environ.items() if not key.startswith(('DOCKER_','BUILDX_','BUILDKIT_'))}
   env.update(PATH=str(binaries)+os.pathsep+os.environ['PATH'],DOCKER_CONFIG=str(original),RECOVERY_ORIGINAL=str(original),RECOVERY_EVENTS=str(events),RECOVERY_ROOT=str(fixture),RECOVERY_ENDPOINT=endpoint,RECOVERY_EXPECTED_ENDPOINT=endpoint,RECOVERY_BUILD=str(BUILD),RECOVERY_SMOKE=str(SMOKE),RECOVERY_BUILD_DONE=str(fixture/'built'),TMPDIR=str(fixture))
   for key,value in (environment or {}).items():env[key]=endpoint if value=='LOCAL_SOCKET' else value
   if mutate:mutate(fixture)
   argv=['/bin/bash',str(WRAPPER),*(arguments if arguments is not None else ['--tag','kanbien-core-server-persistence:test','--port','39456'])]
   if terminate:
    process=subprocess.Popen(argv,cwd=fixture,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    for _ in range(500):
     if any(item.get('kind')=='stage' for item in [json.loads(line) for line in events.read_text().splitlines()]):break
     if process.poll() is not None:raise AssertionError(process.communicate())
     time.sleep(.01)
    else:process.kill();raise AssertionError('fixture stage did not start')
    process.send_signal(signal.SIGTERM)
    try:stdout,stderr=process.communicate(timeout=15)
    except subprocess.TimeoutExpired:process.kill();process.communicate();raise
    status=process.returncode
   else:
    result=subprocess.run(argv,cwd=fixture,env=env,capture_output=True,text=True,timeout=15);stdout,stderr,status=result.stdout,result.stderr,result.returncode
  records=[json.loads(line) for line in events.read_text().splitlines()]
  assert status==expected,(name,status,stdout,stderr)
  assert 'Traceback' not in stderr,(name,stderr)
  if code:assert json.loads(stderr.strip().splitlines()[-1])['code']==code,(name,stderr)
  actual=[item['stage'] for item in records if item['kind']=='stage']
  assert actual==(stages if stages is not None else ['build','smoke'] if expected==0 else []),(name,actual)
  configs={item['config'] for item in records if item.get('config') and item['config']!=str(original)}
  assert all(not Path(path).exists() for path in configs),(name,configs)
  assert not list(fixture.glob('persistence-public-docker-*')),name
  assert original_files=={p.name:(p.read_bytes(),stat.S_IMODE(p.stat().st_mode)) for p in original.iterdir()},name
  if name.startswith(('remote','invalid-argument','owner-')):assert not any(item.get('args',[])[:1]==['info'] for item in records),(name,records)
  COUNT+=1

def replace(path,old,new):
 def mutate(root):
  file=root/path;source=file.read_text();assert old in source;file.write_text(source.replace(old,new))
 return mutate

run_case('default-local')
run_case('host-local',environment={'DOCKER_HOST':'LOCAL_SOCKET'})
run_case('explicit-context-precedence-and-cleared-selectors',environment={'DOCKER_CONTEXT':'selected-local','DOCKER_HOST':'tcp://foreign.invalid:2375','DOCKER_TLS_VERIFY':'1','DOCKER_CERT_PATH':'/fixture/never-read','DOCKER_API_VERSION':'old','DOCKER_CUSTOM_HEADERS':'fixture-only','BUILDX_BUILDER':'remote','BUILDX_CONFIG':'/fixture/never-read','BUILDKIT_HOST':'tcp://foreign.invalid:1234','BUILDKIT_SYNTAX':'private.invalid/frontend'})
run_case('remote-host',environment={'DOCKER_HOST':'tcp://foreign.invalid:2375'},expected=1,code='local-public-recovery-local-unix-endpoint-required')
run_case('remote-context',environment={'RECOVERY_ENDPOINT':'ssh://foreign.invalid'},expected=1,code='local-public-recovery-local-unix-endpoint-required')
run_case('context-malformed',environment={'RECOVERY_CONTEXT_BAD':'1'},expected=1,code='local-public-recovery-context-invalid')
run_case('engine-malformed',environment={'RECOVERY_ENGINE_MODE':'malformed'},expected=1,code='local-public-recovery-engine-identity-invalid')
run_case('engine-mismatch',environment={'RECOVERY_ENGINE_MODE':'mismatch'},expected=1,code='local-public-recovery-engine-mismatch')
run_case('engine-changed-after-build',environment={'RECOVERY_ENGINE_MODE':'after-build'},expected=1,code='local-public-recovery-engine-mismatch',stages=['build'])
for stage in ('build','smoke'):
 run_case('failed-'+stage,environment={'RECOVERY_FAIL':stage},expected=42,code='local-public-recovery-'+stage+'-failed',stages=['build'] if stage=='build' else ['build','smoke'])
run_case('signal-cleanup',environment={'RECOVERY_SLEEP':'build'},expected=143,code='local-public-recovery-interrupted',stages=['build'],terminate=True)
for arguments in (['--tag'],['--build-arg','anything'],['--tag','private.invalid/image:test','--port','39456'],['--tag','kanbien-core-server-persistence:test','--port','0'],['--tag','kanbien-core-server-persistence:test','--port','bad']):
 run_case('invalid-argument',arguments=arguments,expected=1,code='local-public-recovery-arguments-invalid')
for name,mutate in (
 ('private-nested-postgres',replace(INTEGRATION_RUNNER,'postgres:17.11-bookworm','private.invalid/postgres:17.11-bookworm')),
 ('changed-nested-integration-check',lambda root:(root/INTEGRATION_CHECK).write_text((root/INTEGRATION_CHECK).read_text()+'\n# unreviewed owner edit\n')),
 ('changed-nested-diagnostic-check',lambda root:(root/DIAGNOSTIC_CHECK).write_text((root/DIAGNOSTIC_CHECK).read_text()+'\n# unreviewed owner edit\n')),
 ('private-node',replace(DOCKERFILE,'node:22-bookworm-slim','private.invalid/node:22')),
 ('private-frontend',replace(DOCKERFILE,'docker/dockerfile:1.7','private.invalid/frontend:1.7')),
 ('private-postgres',replace(SMOKE,'postgres:16-bookworm','private.invalid/postgres:16-bookworm')),
 ('hidden-tag-comment',replace(SMOKE,'postgres:16-bookworm bash -ec','private.invalid/image bash -ec # "$TAG"')),
 ('extra-copy-image',replace(DOCKERFILE,'--from=build','--from=private.invalid/image')),
 ('lowercase-from',lambda root:(root/DOCKERFILE).write_text((root/DOCKERFILE).read_text()+'\n  from private.invalid/image\n')),
 ('lowercase-arg',lambda root:(root/DOCKERFILE).write_text((root/DOCKERFILE).read_text()+'\n  arg BUILD_NODE_IMAGE=private.invalid/image\n')),
 ('builder-private-override',replace(BUILD,'--build-arg "SOURCE_COMMIT_SHA=', '--build-arg BUILD_NODE_IMAGE=private.invalid/image --build-arg "SOURCE_COMMIT_SHA=')),
 ('builder-secret',replace(BUILD,'docker build --file','docker build --secret id=fixture --file')),
 ('malformed-contract',lambda root:(root/CONTRACT).write_text('runtime_base: []\n')),
):run_case('owner-'+name,mutate=mutate,expected=1,code='local-public-recovery-owner-review-required')
print(json.dumps({'schema':'deploy/local-public-recovery-test-report/v1','verdict':'passed','cases':COUNT,'evidence_class':'local-runtime-controlled','real_docker_calls':0,'stored_configuration':'unchanged','temporary_configuration_cleanup':'passed'}))
