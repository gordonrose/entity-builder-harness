"""Bounded real inert-container recovery after private controller processes are killed."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.finite-recovery-conformance
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Demonstrate durable exact-image inert recovery across killed processes without qualifying product tasks.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py
from datetime import datetime,timezone
import json
import hashlib
import os
from pathlib import Path
import select
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

import container_engine
import finite_recovery_contracts as contract
from finite_recovery_controller import RecoveryController,make_intent
from finite_recovery_engine import RecoveryEngine
import local_container
from operation_actions import OperationActionStore,_bindings,binding_sources
import release_compiler

DIRECTORY=Path(__file__).resolve().parent
PHASES=('normal','intent-committed','create-reserved','create-effect','start-effect',
        'terminal-observed','cleanup-effect','cleanup-verified')
FIXTURE='scripts/04.deploy/operational-realization-gate/fixtures/finite-jobs/jobs/task.cjs'


def fail(code):contract.fail('conformance-'+code)
def now():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def qualified_image(root,image_id):
    """Trust the source-owned previously qualified full-image pin, never a caller image claim."""
    pin=contract.journal.decode(contract.journal.read_source(DIRECTORY/'finite-recovery-image.lock.json'))
    contract.validate('finite-recovery-image-lock',pin)
    fields={'schema','qualification_receipt','qualification_receipt_digest','qualified_source_revision',
            'image_id','payload_digest','recipe_digest','runtime_image','runtime_config_digest'}
    if (type(pin) is not dict or set(pin)!=fields or pin['schema']!='finite-recovery-image-lock/v1'
            or type(image_id) is not str or image_id!=pin['image_id']
            or not container_engine.IMAGE_PATTERN.fullmatch(image_id)):
        fail('image-not-qualified')
    path=pin['qualification_receipt']
    if (type(path) is not str or not path.startswith('docs/04.deploy/')
            or '..' in Path(path).parts or Path(path).is_absolute()):fail('qualification-pin-invalid')
    raw=contract.journal.read_source(Path(root)/path)
    if 'sha256:'+hashlib.sha256(raw).hexdigest()!=pin['qualification_receipt_digest']:
        fail('qualification-receipt-changed')
    receipt=json.loads(raw)
    artifact={key:pin[key] for key in ('image_id','payload_digest','recipe_digest','runtime_image','runtime_config_digest')}
    if (receipt.get('schema')!='finite-job-conformance-result/v1' or receipt.get('verdict')!='passed'
            or receipt.get('repository_head')!=pin['qualified_source_revision'] or receipt.get('artifact')!=artifact
            or any(receipt.get(key)!=value for key,value in contract.BLOCKED.items())):
        fail('qualification-receipt-invalid')
    recipe=contract.journal.read_source(Path(root)/'scripts/04.deploy/operational-realization-gate/fixtures/finite-jobs/Dockerfile')
    if ('sha256:'+hashlib.sha256(recipe).hexdigest()!=pin['recipe_digest']
            or contract.digest(contract.fixture_files())!=pin['payload_digest']):fail('qualification-source-changed')
    return pin


def _worker(work,phase):
    """Private child entry point; input is only the parent's bounded fixture attempt."""
    work=Path(work)
    attempt=contract.journal.decode(contract.journal.read_source(work/'attempt.json'))
    contract.validate_attempt(attempt)
    engine=RecoveryEngine(work)
    def checkpoint(actual):
        if actual!=phase:return
        owned=engine._owned.get(attempt['resource']['name'],{})
        marker={'phase':phase,'resource_id':owned.get('id')}
        sys.stdout.buffer.write(contract.journal.canonical(marker)+b'\n');sys.stdout.buffer.flush()
        while True:signal.pause()
    with OperationActionStore(work/'store') as store:
        controller=RecoveryController(store,engine,_checkpoint=checkpoint)
        controller.prepare(make_intent(attempt),attempt)
        controller.run(attempt['operation_id'],uuid.uuid4().hex)
    fail('checkpoint-missed')


def _interrupt(work,phase):
    source="import sys;sys.path.insert(0,sys.argv[1]);from finite_recovery_conformance import _worker;_worker(sys.argv[2],sys.argv[3])"
    # No ambient credentials, Docker context, arbitrary executable or command.
    with tempfile.TemporaryFile(dir=work) as errors:
        process=subprocess.Popen([sys.executable,'-B','-c',source,str(DIRECTORY),str(work),phase],
            cwd=DIRECTORY,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'},
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=errors,start_new_session=True)
        try:
            readable,_,_=select.select([process.stdout],[],[],20)
            if not readable:fail('checkpoint-deadline')
            raw=process.stdout.readline(4097)
            if not raw or len(raw)>4096:fail('checkpoint-invalid')
            marker=contract.journal.decode(raw)
            if (type(marker) is not dict or set(marker)!={'phase','resource_id'} or marker['phase']!=phase
                    or marker['resource_id'] is not None and (type(marker['resource_id']) is not str
                        or not container_engine.CONTAINER_PATTERN.fullmatch(marker['resource_id']))):fail('checkpoint-invalid')
            os.killpg(process.pid,signal.SIGKILL)
            if process.wait(timeout=5)!=-signal.SIGKILL:fail('child-not-interrupted')
            return marker
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            process.stdout.close()


def _resume(work,attempt):
    with OperationActionStore(work/'store') as store:
        current=store.read(attempt['operation_id'])
        expires=current['journal'][-1]['lease_expires_at_ms']
    remaining=(expires-time.time_ns()//1000000+50)/1000
    if remaining>4:fail('lease-bound-invalid')
    if remaining>0:time.sleep(remaining)
    with OperationActionStore(work/'store') as store:
        controller=RecoveryController(store,RecoveryEngine(work))
        return controller.run(attempt['operation_id'],uuid.uuid4().hex)


def _case_result(phase,result,marker):
    contract.validate('finite-recovery-result',result)
    expected='unknown' if phase=='create-reserved' else 'closed'
    terminal=phase not in ('create-reserved','create-effect')
    if (result['state']!=expected or result['cleanup_verified']!=(expected=='closed')
            or result['terminal_observed']!=terminal
            or result['action_counts']['create']!=1
            or result['action_counts']['start']!=(0 if phase in ('create-reserved','create-effect') else 1)
            or phase in ('create-effect','start-effect','terminal-observed') and marker['resource_id'] is None
            or marker['resource_id'] is not None and result['resource_id']!=marker['resource_id']):fail('case-failed')
    return {'case':phase,'controller_interrupted':phase!='normal','verdict':'passed',
            'recorded_resource_id':marker['resource_id'],'result':result}


def run(source_root,scratch_root,image_id):
    root=Path(source_root).resolve(strict=True)
    scratch=local_container.checked_scratch(root,scratch_root)
    qualified_image(root,image_id)
    if contract.journal.read_source(root/FIXTURE)!=contract.journal.read_source(DIRECTORY/'fixtures/finite-jobs/jobs/task.cjs'):
        fail('fixture-source-mismatch')
    revision=_bindings();started=now()
    work=Path(tempfile.mkdtemp(prefix='finite-recovery-',dir=scratch))
    # Preserve this exact implementation for safe diagnosis/recovery even if the
    # source draft advances. No existing database is migrated to new code.
    snapshot=work/'implementation'
    for source in binding_sources():
        destination=snapshot/'scripts/04.deploy/operational-realization-gate'/source.relative_to(DIRECTORY)
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
    for source in contract.journal.SCHEMA_DIR.glob('*.yml'):
        destination=snapshot/'infra/04.deploy/contracts/release-control/v1'/source.name
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
    executor=container_engine.Engine(work)
    engine=executor.version()
    # Re-observe actual immutable image metadata and payload, independent of any
    # historical receipt. Existing bounded inventory collector cleans its own probe.
    if executor.inspect_job_image(image_id)['command']!=['jobs/task.cjs','success']:fail('image-invalid')
    files=executor.inventory_job(image_id)
    if files!=contract.fixture_files():fail('payload-mismatch')
    cases=[]
    for phase in PHASES:
        case=work/phase;case.mkdir(mode=0o700);(case/'store').mkdir(mode=0o700)
        attempt=contract.make_attempt(image_id)
        (case/'attempt.json').write_bytes(contract.journal.canonical(attempt))
        marker={'phase':phase,'resource_id':None}
        if phase=='normal':
            with OperationActionStore(case/'store') as store:
                controller=RecoveryController(store,RecoveryEngine(case))
                controller.prepare(make_intent(attempt),attempt)
                result=controller.run(attempt['operation_id'],uuid.uuid4().hex)
        else:
            marker=_interrupt(case,phase)
            result=_resume(case,attempt)
            if phase!='create-reserved' and result['state'] in ('succeeded','failed','cleanup-verified'):
                # A consumed cleanup with a lost response is reconciled by a new
                # read-only lookup/claim; never recreate or restart the fixture.
                result=_resume(case,attempt)
        value=_case_result(phase,result,marker)
        # Independently query the exact name and, when known, exact ID. A closed
        # case or a never-dispatched create must leave no owned fixture behind.
        observed=RecoveryEngine(case).perform(attempt,'inspect',result['resource_id'])
        if observed['state']!='absent':fail('owned-resource-remains')
        (case/'result.json').write_bytes(contract.journal.canonical(value))
        cases.append(value)
    if _bindings()!=revision:fail('source-changed')
    result={'schema':'finite-recovery-conformance/v1','scope':'local-inert-process-recovery',
            'verdict':'passed','started_at':started,'completed_at':now(),'runner_digest':revision,
            'artifact':{'image_id':image_id,'payload_digest':contract.digest(files)},'payload_files':files,
            'engine':engine,'cases':cases,'semantic_verdict':'unverified','product_profile_updates':[],**contract.BLOCKED}
    result['result_digest']=contract.digest(result)
    validate_result(result)
    (work/'conformance-result.json').write_bytes(contract.journal.canonical(result))
    return result


def validate_result(result):
    contract.validate('finite-recovery-conformance',result)
    if [row['case'] for row in result['cases']]!=list(PHASES):fail('result-invalid')
    if result['artifact']['payload_digest']!=contract.digest(result['payload_files']):fail('result-invalid')
    for key in ('operation_id','attempt_digest'):
        if len({row['result'][key] for row in result['cases']})!=len(PHASES):fail('result-invalid')
    identities=[row['result']['resource_id'] for row in result['cases'] if row['result']['resource_id'] is not None]
    if len(identities)!=len(set(identities)):fail('result-invalid')
    try:
        dates=[datetime.strptime(result[key],'%Y-%m-%dT%H:%M:%SZ') for key in ('started_at','completed_at')]
        if dates[1]<dates[0]:fail('result-invalid')
    except (ValueError,TypeError):fail('result-invalid')
    for row in result['cases']:
        expected=_case_result(row['case'],row['result'],{'phase':row['case'],'resource_id':row['recorded_resource_id']})
        if expected!=row:fail('result-invalid')
    if result['result_digest']!=contract.digest({key:value for key,value in result.items() if key!='result_digest'}):fail('result-invalid')
    return result


def main(argv=None):
    try:
        argv=list(sys.argv[1:] if argv is None else argv)
        flags=[value.split('=',1)[0] for value in argv if value.startswith('--')]
        if len(flags)!=len(set(flags)):fail('arguments-invalid')
        parser=release_compiler.SafeParser(add_help=False,allow_abbrev=False)
        parser.add_argument('--source-root',required=True);parser.add_argument('--scratch-root',required=True)
        parser.add_argument('--image-id',required=True)
        args=parser.parse_args(argv)
        result=run(args.source_root,args.scratch_root,args.image_id)
        # Validate the public output boundary independently of the producer.
        validate_result(result)
        if result['runner_digest']!=_bindings():fail('source-changed')
        print(json.dumps(result,sort_keys=True,separators=(',',':')));return 0
    except Exception:
        print(json.dumps({'schema':'finite-recovery-error/v1','verdict':'failed',**contract.BLOCKED,
                          'findings':[{'code':'finite-recovery-conformance-failed'}]},sort_keys=True,separators=(',',':')))
        return 1

if __name__=='__main__':raise SystemExit(main())
