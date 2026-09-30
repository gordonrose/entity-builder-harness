"""Real local subprocess conformance in a fresh owned directory; never execution authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.control-store-conformance
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove local restart, transaction, conflict and fencing invariants with actual subprocesses.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/script.py
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import sqlite3
import stat
import subprocess
import sys
import time
import uuid

# Isolated workers intentionally import only this fixed adjacent implementation.
if __name__=='__main__':sys.path.insert(0,str(Path(__file__).resolve().parent))
import operation_journal as c
from local_control_store import LocalControlStore, CAPABILITIES
import control_store_fixtures as f

RUNNERS=('operation_journal.py','local_control_store.py','control_store_fixtures.py','control_store_conformance.py',
         'control_store_cli.py','script.py','script.sh')
CASES=('intent-survives-process-kill','effect-and-evidence-survive-process-kill',
       'uncommitted-transaction-rolls-back','concurrent-claim-one-winner','concurrent-revision-one-winner',
       'expired-claim-fenced-to-reconciliation','unresolved-cross-release-conflict',
       'closed-scope-preserves-generation','rejected-expiry-persists-clock','evidence-content-required')
LIMITATIONS=('local-filesystem-only','single-host-and-boot','host-clock-trusted-backward-refused',
             'same-uid-processes-trusted','no-encryption-or-independent-authentication',
             'journal-hash-detects-corruption-only','no-host-reboot-or-power-loss-proof',
             'fixture-policy-only','no-provider-effects-or-durable-cloud-store',
             'fencing-does-not-cancel-inflight-provider-requests')

def bindings():
    directory=Path(__file__).resolve().parent
    runners={name:'sha256:'+hashlib.sha256(c.read_source(directory/name,262144)).hexdigest() for name in RUNNERS}
    schemas={name:'sha256:'+hashlib.sha256(c.read_source(c.SCHEMA_DIR/(name+'.schema.yml'))).hexdigest() for name in sorted(c.SCHEMAS)}
    for name in schemas:c.load_schema(name)
    return {'runner_digest':c.digest(runners),'schema_digests':schemas,'fixture_policy_digest':c.digest(f.intent()['policy'])}

def private_directory(root):
    """Create a unique 0700 child of an existing owned, non-writable-by-others root."""
    try:
        path=Path(root).absolute()
        if '..' in path.parts:c.fail('scratch-root-invalid')
        handle=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for part in path.parts[1:]:
                following=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=handle)
                os.close(handle);handle=following
            info=os.fstat(handle)
            if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o022:c.fail('scratch-root-invalid')
            name='control-store-conformance-'+uuid.uuid4().hex
            os.mkdir(name,0o700,dir_fd=handle)
            os.fsync(handle)
            return path/name
        finally:os.close(handle)
    except c.ControlFailure:raise
    except OSError:c.fail('scratch-root-invalid')

def _child(directory,action,owner=f.OWNER_A):
    if action not in ('intent','effect','transaction','claim','revision'):c.fail('worker-invalid')
    c.owner(owner)
    return subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--worker',action,str(directory),owner],
        cwd=directory,env={'PATH':os.defpath,'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1'},
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0)

def _line(child,timeout=15):
    data=bytearray();deadline=time.monotonic()+timeout
    with selectors.DefaultSelector() as selector:
        selector.register(child.stdout,selectors.EVENT_READ)
        while not data.endswith(b'\n'):
            if len(data)>1024 or time.monotonic()>=deadline:c.fail('worker-output-invalid')
            if not selector.select(max(0,deadline-time.monotonic())):c.fail('worker-timeout')
            part=os.read(child.stdout.fileno(),1)
            if not part:c.fail('worker-failed')
            data.extend(part)
    value=c.decode(bytes(data))
    if type(value) is not dict or set(value)!={'status'} or type(value['status']) is not str:c.fail('worker-output-invalid')
    return value['status']

def _stop(child):
    if child.poll() is None:child.kill()
    child.wait(timeout=5)
    for stream in (child.stdin,child.stdout):
        if stream is not None:stream.close()

def _ready(child):
    if _line(child)!='ready':c.fail('worker-failed')

def _crash(directory,action):
    child=_child(directory,action)
    try:
        _ready(child);child.kill()
        if child.wait(timeout=5)!=-signal.SIGKILL:c.fail('worker-not-killed')
    finally:_stop(child)

def _race(directory,action):
    children=[]
    try:
        children.append(_child(directory,action,f.OWNER_A))
        children.append(_child(directory,action,f.OWNER_B))
        for child in children:_ready(child)
        for child in children:child.stdin.write(b'go\n');child.stdin.flush()
        outcomes=[_line(child) for child in children]
        for child in children:
            if child.wait(timeout=5)!=0:c.fail('worker-failed')
        return sorted(outcomes)
    finally:
        for child in children:_stop(child)

def _expect(code,call,*args,**kwargs):
    try:call(*args,**kwargs)
    except c.ControlFailure as error:
        if error.code==code:return
        c.fail('conformance-unexpected-rejection')
    c.fail('conformance-false-accept')

def _renew(store,claim):
    return store.renew(claim,store.read(claim['operation_id'])['revision'])

def _next(store,claim,event,proof=None):
    return store.advance(claim,store.read(claim['operation_id'])['revision'],event,proof)

def _proof(store,claim,assertion='fixture-effect',*,now=f.NOW,effect=1):
    snapshot=store.read(claim['operation_id'])
    return store.put_evidence(claim,f.evidence(snapshot['intent'],snapshot['attempt'],assertion,
        now=now,effect=effect,revision=snapshot['revision'],fences=claim['fences']))

def _case(directory,name):
    """Return bounded observed facts, never raw subprocess logs or database paths."""
    document=f.intent();operation=document['operation_id']
    if name in ('intent-survives-process-kill','effect-and-evidence-survive-process-kill'):
        _crash(directory,'intent' if name.startswith('intent-') else 'effect')
        marker=directory/'effect.marker'
        with LocalControlStore(directory,_clock=lambda:f.NOW+1001) as store:
            snapshot=store.read(operation)
            if snapshot['state']!='executing' or snapshot['attempt']!=1:c.fail('conformance-state-invalid')
            if marker.exists()!=(name.startswith('effect-')):c.fail('conformance-effect-invalid')
            if marker.exists() and c.read_source(marker,64)!=b'fixture-effect/v1\n':c.fail('conformance-effect-invalid')
            evidence=[event['evidence_digest'] for event in snapshot['journal'] if event['evidence_digest']]
            expected=1 if marker.exists() else 0
            if len(evidence)!=expected:c.fail('conformance-evidence-invalid')
            for digest in evidence:
                if store.read_evidence(operation,digest)['counts']['effect_count']!=1:c.fail('conformance-effect-invalid')
            recovered=store.claim(operation,f.OWNER_B)
            if recovered['mode']!='reconcile' or store.read(operation)['state']!='unknown':c.fail('conformance-state-invalid')
        return {'subprocesses':1,'processes_killed':1,'accepted_claims':2,'rejected_actions':0,
                'persisted_effects':expected,'validated_evidence_documents':expected}
    with LocalControlStore(directory,_clock=lambda:f.NOW) as store:store.prepare(document)
    if name=='uncommitted-transaction-rolls-back':
        _crash(directory,'transaction')
        with LocalControlStore(directory,_clock=lambda:f.NOW) as store:
            if store.read(operation)['state']!='prepared':c.fail('conformance-state-invalid')
        return {'subprocesses':1,'processes_killed':1,'accepted_claims':0,'rejected_actions':0,'persisted_effects':0,'validated_evidence_documents':0}
    if name in ('concurrent-claim-one-winner','concurrent-revision-one-winner'):
        if name.startswith('concurrent-revision'):
            with LocalControlStore(directory,_clock=lambda:f.NOW) as store:store.claim(operation,f.OWNER_A)
        outcomes=_race(directory,'claim' if name.startswith('concurrent-claim') else 'revision')
        expected=['acquired','lease-held'] if name.startswith('concurrent-claim') else ['advanced','revision-stale']
        if outcomes!=sorted(expected):c.fail('conformance-race-invalid')
        with LocalControlStore(directory,_clock=lambda:f.NOW) as store:
            snapshot=store.read(operation)
            if snapshot['attempt']!=(1 if name.startswith('concurrent-revision') else 0):c.fail('conformance-state-invalid')
        return {'subprocesses':2,'processes_killed':0,'accepted_claims':1,'rejected_actions':1,'persisted_effects':0,'validated_evidence_documents':0}
    now=f.NOW;accepted=1;rejected=0;documents=0
    with LocalControlStore(directory,_clock=lambda:now) as store:
        claim=store.claim(operation,f.OWNER_A)
        if name=='expired-claim-fenced-to-reconciliation':
            _next(store,claim,'effect-intent');now+=1001
            recovered=store.claim(operation,f.OWNER_B);_expect('claim-stale',_renew,store,claim)
            proof=_proof(store,recovered,'fixture-absent',now=now,effect=0);_next(store,recovered,'reconciled-absent',proof)
            _expect('reconciliation-required',_next,store,recovered,'effect-intent');accepted=2;rejected=2;documents=1
        elif name=='unresolved-cross-release-conflict':
            _next(store,claim,'effect-intent');now+=1001
            other=f.intent('another-release',release='9');store.prepare(other)
            _expect('scope-unresolved',store.claim,other['operation_id'],f.OWNER_B);rejected=1
        elif name=='closed-scope-preserves-generation':
            _next(store,claim,'effect-intent');_next(store,claim,'observed')
            _next(store,claim,'succeeded',_proof(store,claim))
            _next(store,claim,'cleanup-verified',_proof(store,claim,'fixture-cleanup'));_next(store,claim,'closed')
            other=f.intent('another-release',release='9');store.prepare(other)
            newer=store.claim(other['operation_id'],f.OWNER_B)
            if newer['fences'][0]['generation']<=claim['fences'][0]['generation']:c.fail('conformance-fence-invalid')
            accepted=2;documents=2
        elif name=='rejected-expiry-persists-clock':
            now+=1001;_expect('claim-stale',_renew,store,claim);store.close();now-=1000
            _expect('clock-regressed',LocalControlStore,directory,_clock=lambda:now);rejected=2
        elif name=='evidence-content-required':
            _next(store,claim,'effect-intent');proof=_proof(store,claim)
            store.db.execute('DELETE FROM evidence WHERE digest=?',(proof,))
            _expect('evidence-corrupt',store.read,operation);rejected=1
        else:c.fail('case-invalid')
    return {'subprocesses':0,'processes_killed':0,'accepted_claims':accepted,'rejected_actions':rejected,'persisted_effects':0,'validated_evidence_documents':documents}

def conformance(scratch_root):
    before=bindings();directory=private_directory(scratch_root)
    cases=[]
    for name in CASES:
        child=directory/name;child.mkdir(mode=0o700)
        observation=_case(child,name)
        cases.append({'case':name,'verdict':'passed',**observation})
    if bindings()!=before:c.fail('source-changed')
    result={'schema':'control-store-conformance/v1','verdict':'passed',
            'scope':'local-process-restart-conformance','authorized':False,
            'release_eligibility':'blocked','operation_authorization':'blocked','qualification_verdict':'blocked',
            'observed_at_ms':time.time_ns()//1000000,
            'clock':'explicit-synthetic-timeline-on-one-host-boot','durability':'sqlite-delete-synchronous-full','sqlite_version':sqlite3.sqlite_version,
            'limitations':list(LIMITATIONS),'cases':cases,**before}
    result['result_digest']=c.digest(result)
    c.validate('control-store-conformance',result)
    return result

def _worker(action,directory,owner):
    if action not in ('intent','effect','transaction','claim','revision'):c.fail('worker-invalid')
    c.owner(owner);document=f.intent();operation=document['operation_id']
    with LocalControlStore(directory,_clock=lambda:f.NOW) as store:
        if action in ('intent','effect'):
            store.prepare(document);claim=store.claim(operation,owner);_next(store,claim,'effect-intent')
            if action=='effect':
                handle=os.open('effect.marker',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=store.fd)
                try:os.write(handle,b'fixture-effect/v1\n');os.fsync(handle)
                finally:os.close(handle)
                os.fsync(store.fd);_proof(store,claim)
        elif action=='transaction':
            store.db.execute('BEGIN IMMEDIATE');store.db.execute("UPDATE operations SET state='uncommitted-state'")
        print('{"status":"ready"}',flush=True)
        command=sys.stdin.readline(16)
        if action in ('intent','effect','transaction'):c.fail('worker-unexpected-resume')
        if command!='go\n':c.fail('worker-invalid')
        try:
            if action=='claim':store.claim(operation,owner);status='acquired'
            else:
                claim={'operation_id':operation,'owner':f.OWNER_A,'mode':'execute',
                       'fences':[{'scope_id':scope['scope_id'],'generation':1} for scope in document['scopes']]}
                store.advance(claim,1,'effect-intent');status='advanced'
        except c.ControlFailure as error:
            if error.code not in ('lease-held','revision-stale'):raise
            status=error.code
        print(json.dumps({'status':status},separators=(',',':')),flush=True)

if __name__=='__main__':
    try:
        if len(sys.argv)!=5 or sys.argv[1]!='--worker':c.fail('worker-invalid')
        _worker(sys.argv[2],sys.argv[3],sys.argv[4])
    except BaseException:
        # Internal workers emit no raw exception, command, path or database payload.
        print('{"status":"worker-failed"}',flush=True);sys.exit(1)
