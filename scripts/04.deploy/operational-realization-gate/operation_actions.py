"""Typed durable adapter attachments and consumed action reservations; no authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operation-actions
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Commit typed attempt identity and bounded action reservations before local adapter effects.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.finite-recovery-engine
#     path: scripts/04.deploy/operational-realization-gate/finite_recovery_engine.py
from copy import deepcopy
import hashlib
import ast
from functools import lru_cache
import sqlite3
from pathlib import Path

from jsonschema import Draft202012Validator
import operation_journal as contract
from operation_journal import fail
from local_control_store import LocalControlStore, CAPABILITIES
import finite_recovery_contracts as finite
import candidate_lifecycle as candidate

# Code registration only. There is no user-supplied validator/schema/command path.
REGISTERED={'finite-recovery-attempt/v1':finite,'candidate-lifecycle-attempt/v1':candidate}
MAX_ACTION_EVENTS=128
SCHEMA='operation-action-record'
AUTHORITY={'authorized':False,'release_eligibility':'blocked','operation_authorization':'blocked'}


def _schema():
    return contract._parse_schema(SCHEMA,contract.read_source(contract.SCHEMA_DIR/(SCHEMA+'.schema.yml')))


def _validate_record(value):
    contract.canonical(value)
    if next(Draft202012Validator(_schema()).iter_errors(value),None):fail('action-record-invalid')


@lru_cache(maxsize=128)
def _checked_attempt(raw,binding):
    value=contract.decode(raw)
    REGISTERED[value['schema']].validate_attempt(value)


@lru_cache(maxsize=512)
def _checked_observation(action,raw,attempt_raw,binding):
    attempt=contract.decode(attempt_raw)
    REGISTERED[attempt['schema']].validate_action_observation(action,contract.decode(raw),attempt)


def _registered(document):
    if type(document) is not dict or document.get('schema') not in REGISTERED:fail('attachment-type-unsupported')
    adapter=REGISTERED[document['schema']]
    _checked_attempt(contract.canonical(document),_bindings())
    limits=document['limits']['action_limits']
    if (type(limits) is not dict or not limits or len(limits)>16
            or any(type(value) is not int or not 1<=value<=32 for value in limits.values())):fail('action-policy-invalid')
    for name in limits:contract.identifier(name)
    return adapter


@lru_cache(maxsize=128)
def _local_imports(raw):
    try:tree=ast.parse(raw)
    except (SyntaxError,ValueError):fail('action-source-invalid')
    names=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):names.extend(item.name.split('.')[0] for item in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:names.append(node.module.split('.')[0])
    return tuple(names)


def binding_sources():
    """Actual local import closure, plus the fixed fixture payload; never unrelated tests."""
    directory=Path(__file__).resolve().parent
    pending=['operation_actions','finite_recovery_controller','finite_recovery_engine','finite_recovery_conformance']
    found={}
    while pending:
        name=pending.pop()
        if name in found:continue
        path=directory/(name+'.py')
        if not path.is_file():continue
        raw=contract.read_source(path,262144)
        found[name]=path
        pending.extend(_local_imports(raw))
    return [found[name] for name in sorted(found)]+[directory/'script.sh',directory/'fixtures/finite-jobs/jobs/task.cjs',directory/'finite-recovery-image.lock.json']


def _bindings():
    files=binding_sources()
    values={path.name:'sha256:'+hashlib.sha256(contract.read_source(path,262144)).hexdigest() for path in files}
    for name in (SCHEMA,*finite.SCHEMAS,*candidate.SCHEMAS,'finite-job-profile','finite-job-result','operation-control','operation-journal','operation-evidence'):
        values[name]='sha256:'+hashlib.sha256(contract.read_source(contract.SCHEMA_DIR/(name+'.schema.yml'))).hexdigest()
    return contract.digest(values)


class OperationActionStore(LocalControlStore):
    """Companion journal uses composite CAS; Unit A's accepted schema is unchanged."""
    def __init__(self,directory,*,_clock=None):
        # Existing Unit A stores are incompatible, never migrated in place.
        database=Path(directory)/'control.sqlite3'
        if database.exists() or database.is_symlink():
            raw=contract.read_source(database,4096*4096+65536)
            try:
                probe=sqlite3.connect(':memory:')
                try:
                    probe.deserialize(raw)
                    marker=probe.execute("SELECT value FROM meta WHERE key='action-store-kind'").fetchone()
                    if marker is None or marker[0]!='typed-operation-actions/v1':fail('action-store-format-required')
                    binding=probe.execute("SELECT value FROM meta WHERE key='action-schema-binding'").fetchone()
                    if binding is None or binding[0]!=_bindings():fail('action-store-format-changed')
                finally:probe.close()
            except sqlite3.Error:fail('action-store-unavailable')
        super().__init__(directory,_clock=_clock)
        try:
            _schema();binding=_bindings()
            self.db.executescript('''
              CREATE TABLE IF NOT EXISTS action_attachments(operation TEXT PRIMARY KEY,schema TEXT NOT NULL,digest TEXT NOT NULL,
                document BLOB NOT NULL,revision INTEGER NOT NULL,recovery_deadline INTEGER NOT NULL,
                FOREIGN KEY(operation) REFERENCES operations(id));
              CREATE TABLE IF NOT EXISTS action_events(operation TEXT NOT NULL,sequence INTEGER NOT NULL,digest TEXT NOT NULL,
                document BLOB NOT NULL,PRIMARY KEY(operation,sequence),FOREIGN KEY(operation) REFERENCES operations(id));
              CREATE TABLE IF NOT EXISTS action_observations(digest TEXT NOT NULL,operation TEXT NOT NULL,reservation TEXT NOT NULL,
                document BLOB NOT NULL,PRIMARY KEY(operation,reservation),FOREIGN KEY(operation) REFERENCES operations(id));
            ''')
            with self._transaction():
                self.db.execute("INSERT OR IGNORE INTO meta VALUES('action-store-kind','typed-operation-actions/v1')")
                old=self.db.execute("SELECT value FROM meta WHERE key='action-schema-binding'").fetchone()
                if old is not None and old['value']!=binding:fail('action-store-format-changed')
                self.db.execute("INSERT OR IGNORE INTO meta VALUES('action-schema-binding',?)",(binding,))
        except (OSError,sqlite3.Error,ValueError):
            self.close();fail('action-store-unavailable')
        except BaseException:
            self.close();raise

    def _bound(self,intent,attachment):
        adapter=_registered(attachment)
        if (intent['operation_id']!=attachment['operation_id']
                or intent['idempotency_key']!=contract.digest(attachment)
                or intent['profile_digest']!=contract.digest(attachment['profile'])
                or intent['artifact_digest']!=attachment['profile']['artifact']['image_id']):fail('attachment-binding-invalid')
        return adapter

    def _attachment(self,row,intent):
        current=self.db.execute("SELECT value FROM meta WHERE key='action-schema-binding'").fetchone()
        if current is None or current['value']!=_bindings():fail('action-store-format-changed')
        stored=self.db.execute('SELECT * FROM action_attachments WHERE operation=?',(row['id'],)).fetchone()
        if stored is None:fail('attachment-missing')
        value=contract.decode(stored['document']);adapter=self._bound(intent,value)
        if (stored['schema']!=value['schema'] or contract.digest(value)!=stored['digest']
                or type(stored['revision']) is not int or not 0<=stored['revision']<MAX_ACTION_EVENTS
                or stored['recovery_deadline']!=row['deadline']+value['limits']['recovery_timeout_ms']):fail('attachment-corrupt')
        return dict(stored),value,adapter

    def _append(self,row,attachment,event,now,*,claim=None,action=None,ordinal=0,reservation=None,observation=None,deadline=None):
        sequence=attachment['revision']+1
        if sequence>=MAX_ACTION_EVENTS:fail('action-journal-limit')
        previous=self.db.execute('SELECT digest FROM action_events WHERE operation=? AND sequence=?',(row['id'],attachment['revision'])).fetchone()
        value={'schema':SCHEMA+'/v1','operation_id':row['id'],'intent_digest':row['digest'],
               'attachment_type':attachment['schema'],'attachment_digest':attachment['digest'],
               'sequence':sequence,'event':event,'action':action,'ordinal':ordinal,
               'claim_digest':None if claim is None else contract.digest(claim),'operation_revision':row['revision'],
               'observed_at_ms':now,'deadline_ms':attachment['recovery_deadline'] if deadline is None else deadline,
               'reservation_digest':reservation,'observation_digest':observation,
               'previous_digest':None if previous is None else previous['digest'],**AUTHORITY}
        value['event_digest']=contract.digest(value);_validate_record(value)
        self.db.execute('INSERT INTO action_events VALUES(?,?,?,?)',(row['id'],sequence,value['event_digest'],contract.canonical(value)))
        self.db.execute('UPDATE action_attachments SET revision=? WHERE operation=?',(sequence,row['id']))
        return value

    def prepare_attempt(self,intent,attachment):
        contract.validate('operation-control',intent);self._bound(intent,attachment)
        intent_digest=contract.digest(intent);attachment_digest=contract.digest(attachment)
        with self._transaction() as now:
            existing=self.db.execute('SELECT * FROM operations WHERE id=? OR idempotency=?',(intent['operation_id'],intent['idempotency_key'])).fetchall()
            if existing:
                if len(existing)!=1 or existing[0]['id']!=intent['operation_id'] or existing[0]['digest']!=intent_digest:fail('intent-conflict')
                row,actual=self._row(intent['operation_id']);stored,value,_=self._attachment(row,actual)
                self._history_actions(row,actual,stored,value)
                if stored['digest']!=attachment_digest:fail('attachment-conflict')
                return intent_digest
            if self.db.execute('SELECT count(*) FROM operations').fetchone()[0]>=1000:fail('operation-limit')
            self.db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (intent['operation_id'],intent_digest,intent['idempotency_key'],contract.canonical(intent),'prepared',0,-1,
                 now+intent['policy']['operation_timeout_ms'],None,0,'none'))
            row,actual=self._row(intent['operation_id']);self._event(row,'prepared',now)
            row,actual=self._row(intent['operation_id'])
            deadline=row['deadline']+attachment['limits']['recovery_timeout_ms']
            self.db.execute('INSERT INTO action_attachments VALUES(?,?,?,?,?,?)',
                (row['id'],attachment['schema'],attachment_digest,contract.canonical(attachment),-1,deadline))
            attached={'schema':attachment['schema'],'digest':attachment_digest,'revision':-1,'recovery_deadline':deadline}
            self._append(row,attached,'attachment-bound',now)
        return intent_digest

    def read_attempt(self,operation):
        with self._transaction():
            row,intent=self._row(operation);stored,value,_=self._attachment(row,intent)
            self._history_actions(row,intent,stored,value)
            return value

    def _history_actions(self,row,intent,attachment,value):
        stored=self.db.execute('SELECT * FROM action_events WHERE operation=? ORDER BY sequence LIMIT ?',
                               (row['id'],MAX_ACTION_EVENTS+1)).fetchall()
        if len(stored)!=attachment['revision']+1 or not stored or len(stored)>MAX_ACTION_EVENTS:fail('action-journal-corrupt')
        previous=None;time=0;records=[];reservations={};observations=[];counts={name:0 for name in value['limits']['action_limits']}
        adapter=_registered(value);known_id=None;seen=set()
        for sequence,item in enumerate(stored):
            event=contract.decode(item['document']);_validate_record(event)
            expected=contract.digest({key:part for key,part in event.items() if key!='event_digest'})
            if (event['operation_id']!=row['id'] or event['intent_digest']!=row['digest']
                    or event['attachment_type']!=attachment['schema'] or event['attachment_digest']!=attachment['digest']
                    or event['sequence']!=sequence or item['sequence']!=sequence
                    or event['previous_digest']!=previous or event['event_digest']!=expected or item['digest']!=expected
                    or event['observed_at_ms']<time or event['operation_revision']>row['revision']
                    or event['deadline_ms']>attachment['recovery_deadline']):fail('action-journal-corrupt')
            if sequence==0:
                if (event['event']!='attachment-bound' or event['action'] is not None or event['ordinal']!=0
                        or event['claim_digest'] is not None or event['reservation_digest'] is not None
                        or event['observation_digest'] is not None or event['operation_revision']!=0
                        or event['deadline_ms']!=attachment['recovery_deadline']):fail('action-journal-corrupt')
            elif event['event']=='reserved':
                action=event['action']
                if action not in counts:fail('action-journal-corrupt')
                counts[action]+=1
                if (event['ordinal']!=counts[action] or counts[action]>value['limits']['action_limits'][action]
                        or event['claim_digest'] is None or event['reservation_digest'] is not None
                        or event['observation_digest'] is not None or event['deadline_ms']<=event['observed_at_ms']):fail('action-journal-corrupt')
                reservations[expected]=event
            elif event['event']=='observed':
                ticket=reservations.get(event['reservation_digest'])
                if (ticket is None or event['reservation_digest'] in seen or event['observation_digest'] is None
                        or event['action']!=ticket['action'] or event['ordinal']!=ticket['ordinal']
                        or event['claim_digest']!=ticket['claim_digest'] or event['deadline_ms']!=ticket['deadline_ms']
                        or event['observed_at_ms']>=event['deadline_ms']
                        or any(candidate['sequence']>ticket['sequence'] for candidate in reservations.values())):fail('action-journal-corrupt')
                proof=self.db.execute('SELECT * FROM action_observations WHERE operation=? AND reservation=? AND digest=?',(row['id'],event['reservation_digest'],event['observation_digest'])).fetchone()
                if proof is None or proof['operation']!=row['id'] or proof['reservation']!=event['reservation_digest']:fail('action-observation-missing')
                content=contract.decode(proof['document'])
                _checked_observation(event['action'],contract.canonical(content),contract.canonical(value),_bindings())
                if contract.digest(content)!=event['observation_digest']:fail('action-observation-corrupt')
                if content['resource_id'] is not None:
                    if known_id is not None and known_id!=content['resource_id']:fail('action-resource-changed')
                    known_id=content['resource_id']
                observations.append({'reservation_digest':event['reservation_digest'],'observation_digest':event['observation_digest'],'observation':content})
                seen.add(event['reservation_digest'])
            else:fail('action-journal-corrupt')
            previous=expected;time=event['observed_at_ms'];records.append(event)
        return {'records':records,'observations':observations,'counts':counts,'known_resource_id':known_id,
                'revision':{'operation':row['revision'],'actions':attachment['revision']},
                'recovery_deadline_ms':attachment['recovery_deadline'],**AUTHORITY}

    def read_actions(self,operation):
        with self._transaction():
            row,intent=self._row(operation);attachment,value,_=self._attachment(row,intent)
            return self._history_actions(row,intent,attachment,value)

    def _current(self,claim,revision,now):
        if (type(revision) is not dict or set(revision)!={'operation','actions'}
                or any(type(number) is not int or number<0 for number in revision.values())):fail('action-revision-invalid')
        row,intent=self._claim(claim,now);attachment,value,adapter=self._attachment(row,intent)
        history=self._history_actions(row,intent,attachment,value)
        if revision!=history['revision']:fail('action-revision-stale')
        return row,intent,attachment,value,adapter,history

    def reserve_action(self,claim,revision,action):
        contract.identifier(action)
        with self._transaction() as now:
            row,intent,attachment,value,adapter,history=self._current(claim,revision,now)
            if action not in history['counts']:fail('action-unsupported')
            if row['state']=='closed':fail('operation-closed')
            if history['counts'][action]>=value['limits']['action_limits'][action]:fail('action-budget-exhausted')
            if action in adapter.DISPATCH_ACTIONS:
                if claim['mode']!='execute' or row['state']!='executing':fail('action-reconciliation-only')
                terminal=row['deadline']
            else:terminal=attachment['recovery_deadline']
            if now>=terminal:fail('action-deadline')
            adapter.validate_action_preconditions(action,value,history,row['state'],claim['mode'])
            deadline=min(now+intent['policy']['call_timeout_ms'],row['expires'],terminal)
            if deadline<=now:fail('action-deadline')
            return self._append(row,attachment,'reserved',now,claim=claim,action=action,
                                ordinal=history['counts'][action]+1,deadline=deadline)

    def observe_action(self,claim,revision,ticket,observation):
        _validate_record(ticket)
        with self._transaction() as now:
            row,intent,attachment,value,adapter,history=self._current(claim,revision,now)
            actual=next((event for event in history['records'] if event['event_digest']==ticket['event_digest']),None)
            if (actual!=ticket or ticket['event']!='reserved' or ticket['claim_digest']!=contract.digest(claim)
                    or ticket['operation_revision']!=row['revision']
                    or any(item['reservation_digest']==ticket['event_digest'] for item in history['observations'])):fail('action-ticket-invalid')
            if any(event['event']=='reserved' and event['sequence']>ticket['sequence'] for event in history['records']):fail('action-ticket-stale')
            if now>=ticket['deadline_ms']:fail('action-deadline')
            adapter.validate_action_observation(ticket['action'],observation,value)
            known=history['known_resource_id']
            if known is not None and observation['resource_id'] is not None and known!=observation['resource_id']:fail('action-resource-changed')
            proof=contract.digest(observation)
            self.db.execute('INSERT INTO action_observations VALUES(?,?,?,?)',
                            (proof,row['id'],ticket['event_digest'],contract.canonical(observation)))
            return self._append(row,attachment,'observed',now,claim=claim,action=ticket['action'],ordinal=ticket['ordinal'],
                                reservation=ticket['event_digest'],observation=proof,deadline=ticket['deadline_ms'])

    def action_budget(self,claim,revision,ticket):
        """Revalidate CAS/lease immediately before transport; return total remaining milliseconds."""
        _validate_record(ticket)
        with self._transaction() as now:
            row,intent,attachment,value,adapter,history=self._current(claim,revision,now)
            if (history['records'][-1]!=ticket or ticket['event']!='reserved'
                    or ticket['claim_digest']!=contract.digest(claim) or ticket['operation_revision']!=row['revision']):
                fail('action-ticket-invalid')
            remaining=ticket['deadline_ms']-now
            if remaining<=0:fail('action-deadline')
            return remaining
