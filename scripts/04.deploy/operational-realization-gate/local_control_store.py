"""Single-host restart/concurrency reference store; no provider execution authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.local-control-store
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise durable local intent, journal, fencing and immutable typed evidence through real transactions.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.control-store-conformance
#     path: scripts/04.deploy/operational-realization-gate/control_store_conformance.py
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import sqlite3
import stat
import time

import operation_journal as contract
from operation_journal import ControlFailure, fail

CAPABILITIES={'scope':'local-process-restart-conformance','single_host':True,'multi_host':False,
              'encrypted':False,'independently_authenticated':False,'authorized':False,
              'release_eligibility':'blocked','operation_authorization':'blocked'}
MAX_EVENTS=1000

class LocalControlStore:
    def __init__(self,directory,*,_clock=None):
        self._clock=_clock or (lambda:time.time_ns()//1000000)
        self.fd=None;self.db=None
        try:
            path=Path(directory).absolute()
            if '..' in path.parts:fail('store-path-invalid')
            fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            try:
                for part in path.parts[1:]:
                    following=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                    os.close(fd);fd=following
                info=os.fstat(fd)
                if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:fail('store-directory-not-private')
                self.fd=fd;fd=None
            finally:
                if fd is not None:os.close(fd)
            # Directory must already be privately owned. Do not create arbitrary caller paths.
            for name in ('control.sqlite3','control.sqlite3-wal','control.sqlite3-shm','control.sqlite3-journal'):
                try:info=os.stat(name,dir_fd=self.fd,follow_symlinks=False)
                except FileNotFoundError:continue
                if name in ('control.sqlite3-wal','control.sqlite3-shm'):fail('store-journal-mode-invalid')
                if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1
                        or stat.S_IMODE(info.st_mode)&0o077 or info.st_size>4096*4096+65536):fail('store-file-invalid')
            try:handle=os.open('control.sqlite3',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
            except FileExistsError:pass
            else:os.close(handle)
            self.db=sqlite3.connect('/proc/self/fd/'+str(self.fd)+'/control.sqlite3',timeout=1,isolation_level=None)
            self.db.row_factory=sqlite3.Row
            self.db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH,contract.MAX_BYTES+4096)
            self.db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH,16384)
            if self.db.execute('PRAGMA page_size').fetchone()[0]!=4096:fail('store-format-changed')
            mode=self.db.execute('PRAGMA journal_mode').fetchone()[0]
            if mode!='delete':fail('store-journal-mode-invalid')
            if self.db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]!='delete':fail('store-journal-mode-invalid')
            self.db.execute('PRAGMA synchronous=FULL')
            if self.db.execute('PRAGMA synchronous').fetchone()[0]!=2:fail('store-durability-invalid')
            self.db.execute('PRAGMA foreign_keys=ON')
            if self.db.execute('PRAGMA max_page_count=4096').fetchone()[0]>4096:fail('store-size-limit')
            self.db.executescript('''
              CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,digest TEXT NOT NULL UNIQUE,idempotency TEXT NOT NULL UNIQUE,
                document BLOB NOT NULL,state TEXT NOT NULL,attempt INTEGER NOT NULL,revision INTEGER NOT NULL,
                deadline INTEGER NOT NULL,owner TEXT,expires INTEGER NOT NULL,mode TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS scopes(id TEXT PRIMARY KEY,generation INTEGER NOT NULL,operation TEXT,owner TEXT,expires INTEGER NOT NULL);
              CREATE TABLE IF NOT EXISTS events(operation TEXT NOT NULL,sequence INTEGER NOT NULL,document BLOB NOT NULL,
                digest TEXT NOT NULL,PRIMARY KEY(operation,sequence),FOREIGN KEY(operation) REFERENCES operations(id));
              CREATE TABLE IF NOT EXISTS fence_history(scope TEXT NOT NULL,generation INTEGER NOT NULL,operation TEXT NOT NULL,sequence INTEGER NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(scope,generation),FOREIGN KEY(operation,sequence) REFERENCES events(operation,sequence));
              CREATE TABLE IF NOT EXISTS evidence(digest TEXT PRIMARY KEY,operation TEXT NOT NULL,document BLOB NOT NULL,
                FOREIGN KEY(operation) REFERENCES operations(id));
            ''')
            schema_binding={name:'sha256:'+hashlib.sha256(contract.read_source(contract.SCHEMA_DIR/(name+'.schema.yml'))).hexdigest()
                            for name in ('operation-control','operation-evidence','operation-journal')}
            for name in schema_binding:contract.load_schema(name)
            schema_digest=contract.digest(schema_binding)
            boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            with self._transaction() as now:
                for key,value in (('format','local-control-store/v1'),('schemas',schema_digest)):
                    existing=self.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
                    if existing is not None and existing['value']!=value:fail('store-format-changed')
                    self.db.execute('INSERT OR IGNORE INTO meta VALUES(?,?)',(key,value))
                row=self.db.execute("SELECT value FROM meta WHERE key='boot'").fetchone()
                if row is not None and row['value']!=boot:fail('store-boot-changed')
                self.db.execute("INSERT OR IGNORE INTO meta VALUES('boot',?)",(boot,))
        except ControlFailure:self.close();raise
        except (OSError,sqlite3.Error,ValueError):self.close();fail('store-unavailable')

    def close(self):
        if self.db is not None:self.db.close();self.db=None
        if self.fd is not None:os.close(self.fd);self.fd=None

    def __enter__(self):return self
    def __exit__(self,*unused):self.close()

    @contextmanager
    def _transaction(self):
        """Persist every valid observed clock, including rejected expired claims.

        An operation savepoint separates rejected work from the committed clock
        high-water mark. A failure must never let a later backward wall clock
        reactivate a lease already observed as expired. The host clock, boot,
        filesystem and same-UID process trust remain explicit assumptions.
        """
        if self.db is None:fail('store-unavailable')
        clock_saved = False
        try:
            self.db.execute('BEGIN IMMEDIATE')
            now=self._clock()
            if type(now) is not int or not 0<now<2**63-1-120000:fail('clock-invalid')
            row=self.db.execute("SELECT value FROM meta WHERE key='clock'").fetchone()
            if row is not None:
                try: previous=int(row['value'])
                except (ValueError,TypeError):fail('clock-invalid')
                if now<previous:fail('clock-regressed')
            self.db.execute("INSERT INTO meta VALUES('clock',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(str(now),))
            self.db.execute('SAVEPOINT operation_work')
            clock_saved = True
            yield now
            self.db.execute('RELEASE operation_work')
            self.db.execute('COMMIT')
        except BaseException as error:
            try:
                if self.db.in_transaction:
                    if clock_saved and isinstance(error,ControlFailure):
                        self.db.execute('ROLLBACK TO operation_work')
                        self.db.execute('RELEASE operation_work')
                        self.db.execute('COMMIT')
                    else:self.db.execute('ROLLBACK')
            except sqlite3.Error:
                if self.db.in_transaction:self.db.execute('ROLLBACK')
                fail('store-transaction-failed')
            if isinstance(error,sqlite3.Error):fail('store-transaction-failed')
            if isinstance(error,(TypeError,KeyError,ValueError,OverflowError)):fail('store-record-corrupt')
            raise

    def _row(self,operation,*,_check_scopes=True):
        contract.identifier(operation)
        row=self.db.execute('SELECT * FROM operations WHERE id=?',(operation,)).fetchone()
        if row is None:fail('operation-missing')
        intent=contract.decode(row['document']);contract.validate('operation-control',intent)
        if contract.digest(intent)!=row['digest']:fail('intent-corrupt')
        row=dict(row)
        if (row['state'] not in ('prepared','executing','observing','succeeded','failed','unknown','cleanup-verified','closed')
                or row['mode'] not in ('none','execute','reconcile')
                or any(type(row[key]) is not int or not 0<=row[key]<2**63-1 for key in ('attempt','deadline','expires'))
                or type(row['revision']) is not int or not -1<=row['revision']<=MAX_EVENTS
                or row['attempt']>intent['policy']['max_attempts']
                or row['idempotency']!=intent['idempotency_key']):fail('store-record-corrupt')
        if row['owner'] is not None:contract.owner(row['owner'])
        if row['revision']>=0:self._history(row,intent,check_scopes=_check_scopes)
        return row,intent

    def _scope_lineage(self,scope):
        """Tie even released fencing counters to the exact last claimed journal event."""
        latest=self.db.execute('SELECT * FROM fence_history WHERE scope=? ORDER BY generation DESC LIMIT 1',(scope['id'],)).fetchone()
        if latest is None or latest['generation']!=scope['generation']:fail('fence-corrupt')
        stored=self.db.execute('SELECT * FROM events WHERE operation=? AND sequence=?',(latest['operation'],latest['sequence'])).fetchone()
        if stored is None:fail('fence-corrupt')
        event=contract.decode(stored['document']);contract.validate('operation-journal',event)
        expected=contract.digest({k:v for k,v in event.items() if k!='event_digest'})
        if (expected!=latest['digest'] or expected!=stored['digest'] or expected!=event['event_digest']
                or event['event']!='claimed' or event['operation_id']!=latest['operation']
                or event['sequence']!=latest['sequence']
                or {'scope_id':scope['id'],'generation':scope['generation']} not in event['fences']):fail('fence-corrupt')
        # Validate the last operation's complete journal without recursively following scopes.
        prior,_=self._row(latest['operation'],_check_scopes=False)
        if scope['operation'] is None:
            if (scope['owner'] is not None or scope['expires']!=0 or prior['state']!='closed'
                    or prior['owner'] is not None or prior['expires']!=0):fail('fence-corrupt')
        elif (scope['operation']!=prior['id'] or prior['state']=='closed'
                or scope['owner']!=prior['owner'] or scope['expires']!=prior['expires']):fail('fence-corrupt')

    def _fences(self,intent):
        rows=[]
        for scope in intent['scopes']:
            row=self.db.execute('SELECT * FROM scopes WHERE id=?',(scope['scope_id'],)).fetchone()
            if row is None:fail('claim-invalid')
            if (type(row['generation']) is not int or not 1<=row['generation']<2**63-1
                    or type(row['expires']) is not int or not 0<=row['expires']<2**63-1):fail('store-record-corrupt')
            self._scope_lineage(row)
            rows.append(dict(row))
        return rows

    def _claim(self,claim,now):
        if type(claim) is not dict or set(claim)!={'operation_id','owner','mode','fences'}:fail('claim-invalid')
        contract.owner(claim['owner'])
        row,intent=self._row(claim['operation_id'])
        fences=self._fences(intent)
        expected=[{'scope_id':x['id'],'generation':x['generation']} for x in fences]
        if (contract.canonical(claim['fences'])!=contract.canonical(expected) or claim['mode']!=row['mode']
                or claim['owner']!=row['owner'] or row['expires']<=now
                or any(x['operation']!=row['id'] or x['owner']!=row['owner'] or x['expires']<=now for x in fences)):
            fail('claim-stale')
        return row,intent

    def _event(self,row,event,now,claim=None,evidence=None):
        sequence=row['revision']+1
        if sequence>MAX_EVENTS:fail('journal-limit')
        previous=self.db.execute('SELECT digest FROM events WHERE operation=? AND sequence=?',(row['id'],row['revision'])).fetchone()
        value={'schema':'operation-journal/v1','operation_id':row['id'],'sequence':sequence,'event':event,
               'state':row['state'],'attempt':row['attempt'],'owner':None if claim is None else claim['owner'],
               'fences':[] if claim is None else claim['fences'],'mode':'none' if claim is None else claim['mode'],
               'observed_at_ms':now,'lease_expires_at_ms':row['expires'],'deadline_at_ms':row['deadline'],'intent_digest':row['digest'],'evidence_digest':evidence,
               'previous_digest':None if previous is None else previous['digest']}
        value['event_digest']=contract.digest(value);contract.validate('operation-journal',value)
        self.db.execute('INSERT INTO events VALUES(?,?,?,?)',(row['id'],sequence,contract.canonical(value),value['event_digest']))
        self.db.execute('UPDATE operations SET state=?,attempt=?,revision=? WHERE id=?',(row['state'],row['attempt'],sequence,row['id']))
        return sequence

    def prepare(self,intent):
        contract.validate('operation-control',intent);digest=contract.digest(intent)
        with self._transaction() as now:
            existing=self.db.execute('SELECT * FROM operations WHERE id=? OR idempotency=?',(intent['operation_id'],intent['idempotency_key'])).fetchall()
            if existing:
                if len(existing)!=1 or existing[0]['id']!=intent['operation_id'] or existing[0]['digest']!=digest:fail('intent-conflict')
                self._row(intent['operation_id']);return digest
            if self.db.execute('SELECT count(*) FROM operations').fetchone()[0]>=1000:fail('operation-limit')
            self.db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (intent['operation_id'],digest,intent['idempotency_key'],contract.canonical(intent),'prepared',0,-1,
                 now+intent['policy']['operation_timeout_ms'],None,0,'none'))
            row,_=self._row(intent['operation_id']);self._event(row,'prepared',now)
        return digest

    def claim(self,operation,owner):
        contract.owner(owner)
        with self._transaction() as now:
            row,intent=self._row(operation)
            if row['state']=='closed':fail('operation-closed')
            mode='execute' if row['owner'] is None else 'reconcile'
            if now>=row['deadline']:mode='reconcile'
            fence=[]
            for scope in intent['scopes']:
                old=self.db.execute('SELECT * FROM scopes WHERE id=?',(scope['scope_id'],)).fetchone()
                if old is not None:self._scope_lineage(old)
                if old is not None and old['operation'] is not None:
                    if old['operation']!=operation:fail('scope-unresolved')
                    if old['expires']>now:fail('lease-held')
                    mode='reconcile'
                if old is not None and (type(old['generation']) is not int or not 1<=old['generation']<2**63-1
                                        or type(old['expires']) is not int or not 0<=old['expires']<2**63-1):fail('store-record-corrupt')
                generation=1 if old is None else old['generation']+1
                if generation>=2**63-1:fail('fence-exhausted')
                fence.append({'scope_id':scope['scope_id'],'generation':generation})
            expires=now+intent['policy']['lease_ms']
            if mode=='execute':expires=min(expires,row['deadline'])
            for item in fence:
                self.db.execute('INSERT INTO scopes VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET generation=excluded.generation,operation=excluded.operation,owner=excluded.owner,expires=excluded.expires',
                    (item['scope_id'],item['generation'],operation,owner,expires))
            self.db.execute('UPDATE operations SET owner=?,expires=?,mode=? WHERE id=?',(owner,expires,mode,operation))
            row.update(owner=owner,expires=expires,mode=mode)
            claim={'operation_id':operation,'owner':owner,'mode':mode,'fences':fence}
            if mode=='reconcile' and row['state'] not in ('succeeded','failed','cleanup-verified'):row['state']='unknown'
            sequence=self._event(row,'claimed',now,claim)
            event=self.db.execute('SELECT digest FROM events WHERE operation=? AND sequence=?',(operation,sequence)).fetchone()
            for item in fence:self.db.execute('INSERT INTO fence_history VALUES(?,?,?,?,?)',(item['scope_id'],item['generation'],operation,sequence,event['digest']))
            return claim

    def renew(self,claim,revision):
        if type(revision) is not int or revision<0:fail('revision-invalid')
        with self._transaction() as now:
            row,intent=self._claim(claim,now)
            if revision!=row['revision']:fail('revision-stale')
            expires=now+intent['policy']['lease_ms']
            if row['mode']=='execute':expires=min(expires,row['deadline'])
            if expires<=now:fail('operation-deadline')
            self.db.execute('UPDATE operations SET expires=? WHERE id=?',(expires,row['id']))
            self.db.execute('UPDATE scopes SET expires=? WHERE operation=?',(expires,row['id']))
            row['expires']=expires
            return self._event(row,'renewed',now,claim)

    def put_evidence(self,claim,evidence):
        contract.validate('operation-evidence',evidence);digest=contract.digest(evidence)
        with self._transaction() as now:
            row,intent=self._claim(claim,now)
            allowed={'fixture-effect':{'executing','observing','unknown'},
                     'fixture-absent':{'unknown'},'fixture-cleanup':{'succeeded','failed','cleanup-verified'}}
            if (row['state'] not in allowed[evidence['assertion']]
                    or evidence['assertion']=='fixture-absent' and claim['mode']!='reconcile'):fail('evidence-phase-invalid')
            current=self.db.execute('SELECT document FROM events WHERE operation=? AND sequence=?',(row['id'],row['revision'])).fetchone()
            lower=contract.decode(current['document'])['observed_at_ms']
            if (evidence['operation_id']!=row['id'] or evidence['release_digest']!=intent['release_digest']
                    or evidence['profile_digest']!=intent['profile_digest'] or evidence['subject_digest']!=intent['artifact_digest']
                    or evidence['attempt']!=row['attempt'] or evidence['observed_at_ms']>now
                    or evidence['observed_at_ms']<lower or evidence['observed_revision']!=row['revision']
                    or contract.canonical(evidence['fences'])!=contract.canonical(claim['fences'])
                    or evidence['expires_at_ms']<=now or evidence['expires_at_ms']<=evidence['observed_at_ms']
                    or evidence['expires_at_ms']-evidence['observed_at_ms']>intent['policy']['evidence_lifetime_ms']):fail('evidence-binding-invalid')
            old=self.db.execute('SELECT document FROM evidence WHERE digest=?',(digest,)).fetchone()
            if old is not None:
                if old['document']!=contract.canonical(evidence):fail('evidence-corrupt')
            else:self.db.execute('INSERT INTO evidence VALUES(?,?,?)',(digest,row['id'],contract.canonical(evidence)))
            self._event(row,'evidence-attached',now,claim,digest)
        return digest

    def _evidence(self,digest,row,now,*,fresh=True):
        if type(digest) is not str or not contract.DIGEST.fullmatch(digest):fail('evidence-missing')
        stored=self.db.execute('SELECT * FROM evidence WHERE digest=?',(digest,)).fetchone()
        if stored is None or stored['operation']!=row['id']:fail('evidence-missing')
        evidence=contract.decode(stored['document']);contract.validate('operation-evidence',evidence)
        if contract.digest(evidence)!=digest:fail('evidence-corrupt')
        expected=[{'scope_id':x['id'],'generation':x['generation']} for x in self._fences(contract.decode(row['document']))]
        if (evidence['expires_at_ms']<=now or evidence['attempt']!=row['attempt']
                or contract.canonical(evidence['fences'])!=contract.canonical(expected)):fail('evidence-stale')
        if fresh:
            latest=self.db.execute('SELECT document FROM events WHERE operation=? AND sequence=?',(row['id'],row['revision'])).fetchone()
            event=contract.decode(latest['document'])
            if (evidence['observed_revision']!=row['revision']-1 or event['event']!='evidence-attached'
                    or event['evidence_digest']!=digest):fail('evidence-stale')
        return evidence

    def read_evidence(self,operation,digest):
        with self._transaction() as now:
            row,intent=self._row(operation)
            if type(digest) is not str or not contract.DIGEST.fullmatch(digest):fail('evidence-missing')
            stored=self.db.execute('SELECT * FROM evidence WHERE digest=?',(digest,)).fetchone()
            if stored is None or stored['operation']!=operation:fail('evidence-missing')
            value=contract.decode(stored['document']);contract.validate('operation-evidence',value)
            if (contract.digest(value)!=digest or value['operation_id']!=operation
                    or value['release_digest']!=intent['release_digest']
                    or value['profile_digest']!=intent['profile_digest']
                    or value['subject_digest']!=intent['artifact_digest']):fail('evidence-corrupt')
            return value


    def advance(self,claim,revision,event,evidence_digest=None):
        if type(revision) is not int or revision<0:fail('revision-invalid')
        transitions={'effect-intent':({'prepared'},'executing'),'observed':({'executing'},'observing'),
                     'succeeded':({'observing'},'succeeded'),'failed':({'prepared','executing','observing'},'failed'),
                     'unknown':({'executing','observing'},'unknown'),
                     'reconciled-absent':({'unknown'},'prepared'),'reconciled-completed':({'unknown'},'observing'),
                     'cleanup-verified':({'succeeded','failed','cleanup-verified'},'cleanup-verified'),'closed':({'cleanup-verified'},'closed')}
        if type(event) is not str or event not in transitions:fail('transition-invalid')
        with self._transaction() as now:
            row,intent=self._claim(claim,now)
            if revision!=row['revision']:fail('revision-stale')
            before,after=transitions[event]
            if row['state'] not in before:fail('transition-invalid')
            if event=='effect-intent':
                if claim['mode']!='execute':fail('reconciliation-required')
                if now>=row['deadline'] or row['attempt']>=intent['policy']['max_attempts']:fail('operation-budget')
                row['attempt']+=1
            required={'succeeded':('fixture-effect',1),'reconciled-completed':('fixture-effect',1),
                      'reconciled-absent':('fixture-absent',0),'cleanup-verified':('fixture-cleanup',None)}
            if event.startswith('reconciled-') and claim['mode']!='reconcile':fail('reconciliation-required')
            if event in required:
                evidence=self._evidence(evidence_digest,row,now);assertion,count=required[event]
                if (evidence['assertion']!=assertion or evidence['verdict']!='passed'
                        or count is not None and evidence['counts']['effect_count']!=count
                        or event in ('cleanup-verified','reconciled-absent') and evidence['counts']['owned_resources']!=0):fail('evidence-incompatible')
            elif evidence_digest is not None:fail('evidence-unexpected')
            if event=='closed':
                cleanup=self.db.execute("SELECT document FROM events WHERE operation=? ORDER BY sequence DESC LIMIT 1001",(row['id'],)).fetchall()
                proof=None
                for item in cleanup:
                    recorded=contract.decode(item['document'])
                    if recorded['event']=='cleanup-verified':proof=recorded['evidence_digest'];break
                evidence=self._evidence(proof,row,now,fresh=False)
                if (evidence['assertion']!='fixture-cleanup' or evidence['verdict']!='passed'
                        or evidence['counts']['owned_resources']!=0):fail('evidence-incompatible')
            row['state']=after
            seq=self._event(row,event,now,claim,evidence_digest)
            # Reconciliation never implicitly returns execution permission. A subsequent claim remains reconciliation-only.
            if event=='closed':
                self.db.execute('UPDATE scopes SET operation=NULL,owner=NULL,expires=0 WHERE operation=?',(row['id'],))
                self.db.execute("UPDATE operations SET owner=NULL,expires=0,mode='none' WHERE id=?",(row['id'],))
            return seq

    def _history(self,row,intent,*,check_scopes=True):
        stored=self.db.execute('SELECT * FROM events WHERE operation=? ORDER BY sequence LIMIT ?',(row['id'],MAX_EVENTS+2)).fetchall()
        if len(stored)!=row['revision']+1 or len(stored)>MAX_EVENTS+1:fail('journal-corrupt')
        previous=None;events=[];last_time=0
        for index,item in enumerate(stored):
            event=contract.decode(item['document']);contract.validate('operation-journal',event)
            expected=contract.digest({k:v for k,v in event.items() if k!='event_digest'})
            if (item['sequence']!=index or event['sequence']!=index or event['previous_digest']!=previous
                    or event['event_digest']!=expected or item['digest']!=expected
                    or event['intent_digest']!=row['digest'] or event['operation_id']!=row['id']
                    or event['observed_at_ms']<last_time or event['deadline_at_ms']!=row['deadline']):fail('journal-corrupt')
            if event['evidence_digest'] is not None:
                evidence=self.db.execute('SELECT * FROM evidence WHERE digest=?',(event['evidence_digest'],)).fetchone()
                if evidence is None or evidence['operation']!=row['id']:fail('evidence-corrupt')
                content=contract.decode(evidence['document']);contract.validate('operation-evidence',content)
                if (contract.digest(content)!=event['evidence_digest'] or content['operation_id']!=row['id']
                        or content['release_digest']!=intent['release_digest']
                        or content['profile_digest']!=intent['profile_digest']
                        or content['subject_digest']!=intent['artifact_digest']):fail('evidence-corrupt')
            previous=expected;last_time=event['observed_at_ms'];events.append(event)
        if not events or events[-1]['state']!=row['state'] or events[-1]['attempt']!=row['attempt']:fail('journal-corrupt')
        if (events[0]['event']!='prepared' or events[0]['state']!='prepared'
                or row['deadline']!=events[0]['observed_at_ms']+intent['policy']['operation_timeout_ms']):fail('journal-corrupt')
        latest=events[-1]
        owner=None if row['state']=='closed' else latest['owner']
        mode='none' if row['state']=='closed' else latest['mode']
        expires=0 if row['state']=='closed' else latest['lease_expires_at_ms']
        if (row['owner']!=owner or row['mode']!=mode or row['expires']!=expires):fail('journal-corrupt')
        if owner is not None and check_scopes:
            actual=self._fences(intent)
            if (contract.canonical(latest['fences'])!=contract.canonical([{'scope_id':scope['id'],'generation':scope['generation']} for scope in actual])
                    or any(scope['operation']!=row['id'] or scope['owner']!=owner or scope['expires']!=expires for scope in actual)):
                fail('journal-corrupt')
        return events

    def read(self,operation):
        with self._transaction() as now:
            row,intent=self._row(operation)
            events=self._history(row,intent)
            return {'intent':intent,'intent_digest':row['digest'],'state':row['state'],'attempt':row['attempt'],
                    'revision':row['revision'],'mode':row['mode'],'journal':events,**CAPABILITIES}
