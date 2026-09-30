"""Closed immutable local operation records; integrity does not imply authority."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.operation-journal
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate immutable intent and typed safe control records for local conformance.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.local-control-store
#     path: scripts/04.deploy/operational-realization-gate/local_control_store.py
import hashlib
from functools import lru_cache
import json
import os
import stat
from pathlib import Path
import re

import yaml
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).resolve().parents[3] / 'infra/04.deploy/contracts/release-control/v1'
SCHEMAS = {'operation-control','operation-journal','operation-evidence','control-store-conformance'}
MAX_BYTES = 32768
ID = re.compile(r'[a-z][a-z0-9-]{2,63}\Z')
DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
OWNER = re.compile(r'[0-9a-f]{32}\Z')

class ControlFailure(Exception):
    def __init__(self, code): self.code=code; super().__init__(code)

def fail(code): raise ControlFailure(code)

def canonical(value):
    pending=[(value,0)];seen=set();count=0
    while pending:
        item,depth=pending.pop();count+=1
        if depth>20 or count>2048: fail('record-limit')
        if type(item) in (dict,list):
            if id(item) in seen: fail('record-invalid')
            seen.add(id(item))
            if type(item) is dict:
                if any(type(k) is not str for k in item): fail('record-invalid')
                pending += [(v,depth+1) for kv in item.items() for v in kv]
            else: pending += [(v,depth+1) for v in item]
        elif type(item) is str:
            if len(item)>512 or any(ord(c)<32 for c in item): fail('record-invalid')
        elif type(item) is int:
            if abs(item)>2**63-1:fail('record-invalid')
        elif item is not None and type(item) is not bool: fail('record-invalid')
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    if len(raw)>MAX_BYTES:fail('record-limit')
    return raw

def digest(value):return 'sha256:'+hashlib.sha256(canonical(value)).hexdigest()

def decode(raw):
    if not isinstance(raw,(bytes,str)) or len(raw)>MAX_BYTES:fail('record-limit')
    def pairs(rows):
        d={}
        for k,v in rows:
            if k in d:fail('record-invalid')
            d[k]=v
        return d
    try:
        value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:fail('record-invalid'))
        canonical(value);return value
    except (ValueError,UnicodeError,RecursionError):fail('record-invalid')

def read_source(path, limit=65536):
    """Read a bounded regular file through componentwise no-follow descriptors."""
    try:
        path=Path(path).absolute()
        if '..' in path.parts:fail('source-invalid')
        parent=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            for part in path.parts[1:-1]:
                next_fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
                os.close(parent);parent=next_fd
            handle=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent)
            try:
                info=os.fstat(handle)
                if not stat.S_ISREG(info.st_mode) or info.st_size>limit:fail('source-invalid')
                chunks=[];size=0
                while True:
                    chunk=os.read(handle,min(8192,limit+1-size))
                    if not chunk:break
                    size+=len(chunk)
                    if size>limit:fail('source-invalid')
                    chunks.append(chunk)
                return b''.join(chunks)
            finally:os.close(handle)
        finally:os.close(parent)
    except ControlFailure:raise
    except OSError:fail('source-invalid')

def load_schema(name):
    if name not in SCHEMAS:fail('schema-invalid')
    return _parse_schema(name,read_source(SCHEMA_DIR/(name+'.schema.yml')))

@lru_cache(maxsize=8)
def _parse_schema(name,raw,version="v1"):
    if version not in ("v1","v2"):fail("schema-invalid")
    class UniqueLoader(yaml.SafeLoader):pass
    def mapping(loader,node,deep=False):
        result={}
        for key,value in node.value:
            k=loader.construct_object(key,deep=deep)
            if type(k) is not str or k in result:fail('schema-invalid')
            result[k]=loader.construct_object(value,deep=deep)
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,mapping)
    try:
        schema=yaml.load(raw,Loader=UniqueLoader)
        if (type(schema) is not dict or schema.get('$id')!='urn:release-control:'+name+':'+version
                or schema.get('$schema')!='https://json-schema.org/draft/2020-12/schema'
                or schema.get('properties',{}).get('schema')!={'const':name+'/'+version}):fail('schema-invalid')
        pending=[(schema,0)];seen=set();count=0
        while pending:
            part,depth=pending.pop();count+=1
            if depth>24 or count>4096:fail('schema-invalid')
            if type(part) in (dict,list):
                if id(part) in seen:fail('schema-invalid')
                seen.add(id(part))
            if type(part) is dict:
                if any(k in part for k in ('$ref','$dynamicRef','$recursiveRef')):fail('schema-invalid')
                if part.get('type')=='object' or 'properties' in part:
                    if (part.get('additionalProperties') is not False or part.get('type')!='object'
                            or set(part.get('required',[]))!=set(part.get('properties',{}))):fail('schema-invalid')
                pending.extend((v,depth+1) for v in part.values())
            elif type(part) is list:pending.extend((v,depth+1) for v in part)
        Draft202012Validator.check_schema(schema)
        return schema
    except ControlFailure:raise
    except Exception:fail('schema-invalid')

def validate(name,value):
    canonical(value)
    schema=load_schema(name)
    if next(Draft202012Validator(schema).iter_errors(value),None):fail('record-invalid')
    if name=='operation-control':
        ids=[row['scope_id'] for row in value['scopes']]
        if ids!=sorted(ids) or len(set(ids))!=len(ids):fail('scope-order-invalid')
        if any(row['scope_id']!=digest({k:v for k,v in row.items() if k!='scope_id'}) for row in value['scopes']):fail('scope-binding-invalid')
        policy=value['policy']
        if value['authority_policy_digest']!=digest(policy):fail('policy-binding-invalid')
        if max(policy['lease_ms'],policy['call_timeout_ms'])>policy['operation_timeout_ms']:fail('budget-invalid')
    return value

def identifier(value):
    if type(value) is not str or not ID.fullmatch(value):fail('identifier-invalid')
    return value

def owner(value):
    if type(value) is not str or not OWNER.fullmatch(value):fail('owner-invalid')
    return value
