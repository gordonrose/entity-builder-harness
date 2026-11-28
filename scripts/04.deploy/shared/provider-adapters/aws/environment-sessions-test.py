#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.aws.environment-sessions
#   version: 7
#   status: draft
#   created_on: "2026-11-27"
#   updated_on: "2026-11-28"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove real session admission and shared change-set handoffs through disposable controlled S3 and CloudFormation subprocesses.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.aws.runtime-alignment
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/smoke-test.sh
from copy import deepcopy
from dataclasses import replace
import hashlib
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OWNER = load("tested_environment_sessions", Path(__file__).with_name("environment_sessions.py"))
CUSTODY = load("session_custody_fixture", ROOT / "scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification-test.py")

# This is the only executable named aws on the child's PATH. No real provider
# process, network, credentials, installation or shell delegation is available.
FAKE = r'''
import base64, hashlib, importlib.util, json, os, pathlib, sys
args=sys.argv[1:]; service,operation=args[:2]
path=pathlib.Path(os.environ['SESSION_FIXTURE_STATE'])
snapshot=globals().get('fixture_state')
state=json.loads(path.read_text()) if snapshot is None else snapshot
def persist():
 if snapshot is None:path.write_text(json.dumps(state))
state['calls'].append([service,operation]);state.setdefault('argv',[]).append(args)
def option(name): return args[args.index(name)+1]
def finish(value=None,error=None):
 persist()
 if error:
  print('An error occurred ('+error+') when calling the Fixture operation: private-canary',file=sys.stderr);sys.exit(1)
 print(json.dumps(value));sys.exit(0)
def lost():
 persist();print('private-canary-lost-response');sys.exit(0)
def metadata(raw):
 return {'ContentLength':len(raw),'ContentRange':'bytes 0-'+str(len(raw)-1)+'/'+str(len(raw)),
         'ETag':'"etag-'+str(state['version'])+'"','VersionId':'version-'+str(state['version'])}
if service=='s3api':
 assert option('--expected-bucket-owner')==state['account']
 assert ('--profile' not in args or option('--profile')=='fixture') and option('--region')==state['region']
 assert os.environ['AWS_MAX_ATTEMPTS']=='1' and os.environ['AWS_PAGER']==''
 assert os.environ['AWS_IGNORE_CONFIGURED_ENDPOINT_URLS']=='true'
 key=option('--key')
 if key!=state.get('parent_key','targets/fixture.json'):
  assert key.startswith('session-children/')
  objects=state.setdefault('children',{});fault=state.get('child_fault')
  if fault in ('AccessDenied','ExpiredToken','Unknown404'):finish(error=fault)
  if operation=='put-object':
   assert option('--if-none-match')=='*' and '--if-match' not in args
   assert option('--content-type')=='application/octet-stream'
   body=pathlib.Path(option('--body'));assert body.stat().st_mode&0o777==0o600
   assert body.parent.stat().st_mode&0o777==0o700
   if key in objects or fault=='PreconditionFailed':finish(error='PreconditionFailed')
   raw=body.read_bytes();state['child_version']=state.get('child_version',0)+1
   version=state.get('child_version_id','child-version-'+str(state['child_version']))
   meta={'ETag':'"child-'+str(state['child_version'])+'"','VersionId':version}
   objects[key]={'latest':version,'versions':{version:{'body':base64.b64encode(raw).decode(),'metadata':meta}}}
   state.setdefault('child_history',[]).append([key,version])
   if fault=='lost-put':state['child_fault']=None;lost()
   if fault=='missing-put-version':meta=dict(meta);meta.pop('VersionId')
   if fault=='readback-version':meta={**meta,'VersionId':'not-the-stored-version'}
   finish(meta)
  if operation=='get-object':
   bound=int(option('--range').removeprefix('bytes=0-'));assert bound in (65536,1048576)
   if key not in objects:finish(error='NoSuchKey')
   version=option('--version-id') if '--version-id' in args else objects[key]['latest']
   if version not in objects[key]['versions']:finish(error='NoSuchVersion')
   record=objects[key]['versions'][version];raw=base64.b64decode(record['body'])
   meta={**record['metadata'],'ContentLength':len(raw),'ContentRange':'bytes 0-'+str(len(raw)-1)+'/'+str(len(raw))}
   if fault=='missing-version':meta.pop('VersionId')
   if fault=='wrong-version':meta['VersionId']='wrong-version'
   if fault=='long-version':meta['VersionId']='v'*1025
   if fault=='null-version':meta['VersionId']='null'
   if fault=='partial-range':meta['ContentRange']='bytes 0-'+str(len(raw)-1)+'/'+str(len(raw)+1)
   if fault=='wrong-length':meta['ContentLength']=False
   if fault=='corrupt-bytes':raw=bytes([raw[0]^1])+raw[1:]
   output=pathlib.Path(args[-1]);assert output.stat().st_mode&0o777==0o600
   assert output.parent.stat().st_mode&0o777==0o700
   output.write_bytes(raw[:bound+1]);finish(meta)
  raise AssertionError(operation)
 fault=state.get('fault')
 if operation=='get-object':
  assert option('--range')=='bytes=0-65536'
  if fault in ('AccessDenied','ExpiredToken','NoSuchBucket','Unknown404'):finish(error=fault)
  if state['raw'] is None:finish(error='NoSuchKey')
  raw=state['raw'].encode(); meta=metadata(raw)
  if fault=='missing-version':meta.pop('VersionId')
  if fault=='null-version':meta['VersionId']='null'
  if fault=='missing-etag':meta.pop('ETag')
  if fault=='partial-range':meta['ContentRange']='bytes 0-'+str(len(raw)-1)+'/'+str(len(raw)+1)
  if fault=='wrong-length':meta['ContentLength']=0
  output=pathlib.Path(args[-1]);assert output.stat().st_mode&0o777==0o600
  assert output.parent.stat().st_mode&0o777==0o700
  output.write_bytes(raw[:65537]);finish(meta)
 if operation=='put-object':
  body=pathlib.Path(option('--body'));assert body.stat().st_mode&0o777==0o600
  assert body.parent.stat().st_mode&0o777==0o700
  raw=body.read_text();json.loads(raw)
  if '--if-none-match' in args:
   assert option('--if-none-match')=='*'
   if state['raw'] is not None:finish(error='PreconditionFailed')
  else:
   if option('--if-match')!='"etag-'+str(state['version'])+'"':finish(error='PreconditionFailed')
  if fault=='conflict-seal':
   document=json.loads(state['raw']);document['state']='sealed';state['raw']=json.dumps(document)
   state['version']+=1;state['history'].append(state['raw']);state['fault']=None
   finish(error='PreconditionFailed')
  if fault in ('PreconditionFailed','ConditionalRequestConflict'):finish(error=fault)
  state['raw']=raw;state['version']+=1;state['history'].append(raw)
  if fault=='lost-put':state['fault']=None;lost()
  meta=metadata(raw.encode())
  if fault=='readback-version':meta['VersionId']='unconfirmed-version';state['fault']=None
  if fault=='missing-put-version':meta.pop('VersionId');state['fault']=None
  finish(meta)
 raise AssertionError(operation)
source=option('--cli-input-json');assert source.startswith('file://')
request_path=pathlib.Path(source[7:]);assert request_path.stat().st_mode&0o777==0o600
assert request_path.parent.stat().st_mode&0o777==0o700
assert ('--profile' not in args or option('--profile')=='fixture') and option('--region')==state['region']
assert option('--output')=='json' and option('--cli-connect-timeout')=='10' and option('--cli-read-timeout')=='20'
assert '--no-paginate' not in args and '--max-items' not in args and '--query' not in args
assert os.environ['AWS_MAX_ATTEMPTS']=='1' and os.environ['AWS_PAGER']==''
assert os.environ['AWS_CLI_AUTO_PROMPT']=='off' and os.environ['AWS_IGNORE_CONFIGURED_ENDPOINT_URLS']=='true'
submitted=json.loads(request_path.read_text());state.setdefault('transport_inputs',[]).append([service,operation,submitted])
native_key=json.dumps([service,operation,submitted],sort_keys=True,separators=(',',':'))
if native_key in state.get('native_replies',{}):
 reply=state['native_replies'][native_key]
 finish(reply.get('response'),error=reply.get('error'))
if state.get('transport_fault'):
 fault=state.pop('transport_fault');persist()
 if fault in ('AccessDenied','ExpiredToken'):finish(error=fault)
 sys.stdout.write({'empty':'','whitespace':' \n','malformed':'private-canary','array':'[]','next-token':'{"NextToken":"private-canary"}'}[fault]);sys.exit(0)
if service=='ecr':
 custody=json.loads(pathlib.Path(os.environ['CUSTODY_FIXTURE_STATE']).read_text())
 if operation=='describe-repositories':finish(custody['repositories'][submitted['repositoryNames'][0]])
 image=custody['images'][submitted['repositoryName']]
 if operation=='batch-get-image':
  assert submitted['imageIds']==[{'imageDigest':image['qualified']}]
  manifest={'mediaType':'application/vnd.oci.image.index.v1+json','manifests':[{'mediaType':'application/vnd.oci.image.manifest.v1+json','digest':image['runnable'],'platform':{'architecture':'amd64','os':'linux'}}]}
  finish({'images':[{'imageId':{'imageDigest':image['qualified']},'imageManifest':json.dumps(manifest)}]})
 if operation=='describe-image-scan-findings':
  assert option('--page-size')=='1' and 'maxResults' not in submitted
  finish({'repositoryName':submitted['repositoryName'],'imageId':submitted['imageId'],'imageScanStatus':{'status':'COMPLETE'},'imageScanFindings':{'findingSeverityCounts':image.get('severity',{})}})
 raise AssertionError(operation)
# Native objects derive from the fake provider's submitted template, parameter
# and allocation state; explicit native_replies above remain adverse overrides.
groups={};databases={};namespaces={};zones={};services={};clusters={};runtime_contexts={}
checked_runtime = state.get('checked_runtime',False)
if checked_runtime and service!='cloudformation':
 spec=importlib.util.spec_from_file_location('fixture_runtime_source',os.environ['SESSION_RUNTIME_OWNER'])
 runtime_source=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime_source)
def permission(p):
 result={key:p[key] for key in ('IpProtocol','FromPort','ToPort')}
 for key,collection,field in (('CidrIp','IpRanges','CidrIp'),('CidrIpv6','Ipv6Ranges','CidrIpv6'),('SourceSecurityGroupId','UserIdGroupPairs','GroupId'),('DestinationSecurityGroupId','UserIdGroupPairs','GroupId'),('DestinationPrefixListId','PrefixListIds','PrefixListId')):
  if key in p:result[collection]=[{field:p[key]}]
 return result
for stack_id,body in (state.get('templates',{}).items() if service!='cloudformation' else ()):
 resources=json.loads(body)['Resources'];parameters={row['ParameterKey']:row['ParameterValue'] for row in state['stacks'][stack_id]['Parameters']}
 allocated={row['LogicalResourceId']:row.get('PhysicalResourceId') for row in state.get('resources',{}).get(stack_id,[]) if row.get('PhysicalResourceId')}
 def value(item):
  if isinstance(item,dict) and set(item)=={'Ref'}:return parameters.get(item['Ref'],allocated.get(item['Ref']))
  return item
 context={name:{'type':row['Type'],'physical_id':allocated[name]} for name,row in resources.items() if name in allocated}
 attributes={}
 if checked_runtime:
  for name,row in resources.items():
   if row['Type']=='AWS::RDS::DBInstance' and name in allocated:
    attributes.update({(name,'Endpoint.Address'):state['outputs'][state['stacks'][stack_id]['StackName']]['PersistenceDatabaseEndpoint'],
     (name,'Endpoint.Port'):'5432',(name,'DbiResourceId'):'db-'+hashlib.sha256(allocated[name].encode()).hexdigest()[:24].upper()})
  for name,row in resources.items():
   if name in allocated and row['Type'] in ('AWS::IAM::Role','AWS::ECS::TaskDefinition'):
    runtime_contexts[allocated[name]]=(name,parameters,context,{'Resources':resources},attributes)
 for logical,resource in resources.items():
  if logical not in allocated:continue
  identity=allocated[logical];kind=resource['Type'];properties=resource.get('Properties',{})
  if kind in ('AWS::EC2::SecurityGroupIngress','AWS::EC2::SecurityGroupEgress'):
   p={key:value(item) for key,item in properties.items()};group=p['GroupId']
   target=groups.setdefault(group,{'GroupId':group,'IpPermissions':[],'IpPermissionsEgress':[]})
   target['IpPermissionsEgress' if kind.endswith('Egress') else 'IpPermissions'].append(permission(p))
  if checked_runtime and kind=='AWS::EC2::SecurityGroup':
   p=runtime_source.runtime_resolve(properties,parameters,context,'fixture',account=state['account'],region=state['region'])
   target=groups.setdefault(identity,{'GroupId':identity,'IpPermissions':[],'IpPermissionsEgress':[]})
   target.update(OwnerId=state['account'],VpcId=p['VpcId'])
   for field in ('SecurityGroupIngress','SecurityGroupEgress'):
    target['IpPermissions' if field.endswith('Ingress') else 'IpPermissionsEgress'].extend(permission(rule) for rule in p.get(field,[]))
  if kind=='AWS::RDS::DBInstance':databases[identity]={'DBInstanceIdentifier':identity,'DBInstanceArn':'arn:aws:rds:'+state['region']+':'+state['account']+':db:'+identity,'DbiResourceId':'db-'+hashlib.sha256(identity.encode()).hexdigest()[:24].upper(),'BackupRetentionPeriod':properties.get('BackupRetentionPeriod')}
  if checked_runtime and kind=='AWS::RDS::DBInstance':databases[identity].update(DBInstanceStatus='available',Endpoint={'Address':attributes[(logical,'Endpoint.Address')],'Port':5432})
  if kind=='AWS::ServiceDiscovery::PrivateDnsNamespace':
   zone='Z'+hashlib.sha256(identity.encode()).hexdigest()[:20].upper();name=parameters['ResourceNamePrefix']+'.internal'
   namespaces[identity]={'Id':identity,'Name':name,'Type':'DNS_PRIVATE','Properties':{'DnsProperties':{'HostedZoneId':zone}}}
   zones[zone]={'HostedZone':{'Id':'/hostedzone/'+zone,'Name':name+'.','Config':{'PrivateZone':True}},'VPCs':[{'VPCId':value(properties['Vpc']),'VPCRegion':state['region']}]}
  if kind=='AWS::ECS::Service':
   cluster=value(properties['Cluster']);services[identity]={'serviceArn':identity,'clusterArn':cluster,'status':'ACTIVE','desiredCount':0,'runningCount':0,'pendingCount':0}
   clusters[cluster]={'clusterArn':cluster,'clusterName':cluster.split('/')[-1],'status':'ACTIVE','runningTasksCount':0,'pendingTasksCount':0,'activeServicesCount':1,'registeredContainerInstancesCount':0}
if checked_runtime and (service=='iam' or service=='ecs' and operation=='describe-task-definition'):
 identity=submitted.get('RoleName',submitted.get('taskDefinition'))
 logical,parameters,context,template,attributes=runtime_contexts[identity]
 if service=='ecs':
  task=runtime_source.runtime_expected_task(logical,'fixture',parameters,context,template,account=state['account'],region=state['region'],_attributes=attributes)
  tags=task.pop('tags',None)
  assert ('include' in submitted)==(tags is not None)
  if tags is not None:assert submitted['include']==['TAGS']
  task.update(taskDefinitionArn=identity,revision=int(identity.rsplit(':',1)[1]),status='ACTIVE',compatibilities=['FARGATE'])
  finish({'taskDefinition':task,**({'tags':tags} if tags is not None else {})})
 properties=runtime_source.runtime_resolve(template['Resources'][logical]['Properties'],parameters,context,'fixture',account=state['account'],region=state['region'],_attributes=attributes)
 policies={row['PolicyName']:row['PolicyDocument'] for row in properties.get('Policies',[])}
 if operation=='get-role':finish({'Role':{'RoleName':identity,'Arn':'arn:aws:iam::'+state['account']+':role/'+identity,'Path':'/','AssumeRolePolicyDocument':properties['AssumeRolePolicyDocument'],**({'PermissionsBoundary':{'PermissionsBoundaryType':'Policy','PermissionsBoundaryArn':properties['PermissionsBoundary']}} if 'PermissionsBoundary' in properties else {})}})
 if operation=='list-role-policies':finish({'PolicyNames':list(policies),'IsTruncated':False})
 if operation=='list-attached-role-policies':finish({'AttachedPolicies':[],'IsTruncated':False})
 if operation=='get-role-policy':finish({**submitted,'PolicyDocument':policies[submitted['PolicyName']]})
 raise AssertionError(operation)
if service=='rds' and operation=='describe-db-instances':finish({'DBInstances':[databases[submitted['DBInstanceIdentifier']]] if submitted['DBInstanceIdentifier'] in databases else []})
if service=='rds' and operation=='describe-db-snapshots':finish({'DBSnapshots':[]})
if service=='rds' and operation=='describe-db-instance-automated-backups':finish({'DBInstanceAutomatedBackups':[]})
if service=='servicediscovery' and operation=='get-namespace':finish({'Namespace':namespaces[submitted['Id']]})
if service=='route53' and operation=='get-hosted-zone':finish(zones[submitted['Id']])
if service=='ecs' and operation=='describe-services':finish({'services':[services[submitted['services'][0]]],'failures':[]})
if service=='ecs' and operation=='describe-clusters':finish({'clusters':[clusters[submitted['clusters'][0]]],'failures':[]})
if service=='ec2':
 if operation=='describe-availability-zones':
  finish({'AvailabilityZones':[{'ZoneName':zone,'ZoneId':'euw2-az'+str(index+1),'RegionName':state['region'],
   'State':'available','ZoneType':'availability-zone'} for index,zone in enumerate(submitted['ZoneNames'])]})
 if operation=='describe-managed-prefix-lists':finish({'PrefixLists':[{'PrefixListId':'pl-0123456789abcdef0'}]})
 if operation=='describe-security-groups':finish({'SecurityGroups':[groups[submitted['GroupIds'][0]]] if submitted['GroupIds'][0] in groups else []})
 raise AssertionError(operation)
assert service=='cloudformation'
changes=state.setdefault('changes',{});stacks=state.setdefault('stacks',{})
name=submitted.get('ChangeSetName')
if operation=='describe-change-set':
 if name not in changes:finish(error='ChangeSetNotFoundException')
 finish({key:value for key,value in changes[name].items() if key!='fixture_role'})
if operation=='get-template':
 if name:
  selected=next((row for row in changes.values() if row['ChangeSetId']==name),None)
  if selected is None:finish(error='ChangeSetNotFoundException')
  assert selected['StackId']==submitted['StackName']
  finish({'TemplateBody':selected['fixture_template']})
 finish({'TemplateBody':state.get('templates',{}).get(submitted['StackName'])})
if operation=='list-stack-resources':
 if state.get('resources_fault'):finish(error=state['resources_fault'])
 finish({'StackResourceSummaries':state.get('resources',{}).get(submitted['StackName'],[]),
         **({'NextToken':state['resources_next_token']} if state.get('resources_next_token') else {})})
if operation=='describe-stacks':
 if submitted['StackName'] not in stacks:finish(error='ValidationError')
 finish({'Stacks':[stacks[submitted['StackName']]]})
if operation=='describe-stack-events':
 deletion=state.get('deletions',{}).get(submitted['StackName'])
 if deletion:
  if submitted['StackName'] in state.get('delete_events',{}):finish({'StackEvents':state['delete_events'][submitted['StackName']]})
  reserved=next(row for row in json.loads(state['raw'])['operations'].values() if row['operation_id']==deletion)
  finish({'StackEvents':[{'PhysicalResourceId':submitted['StackName'],'StackId':submitted['StackName'],
   'LogicalResourceId':reserved['request']['stack'],'ResourceType':'AWS::CloudFormation::Stack',
   'EventId':deletion+'-pending','Timestamp':reserved['reserved_at'],
   'ClientRequestToken':deletion,'ResourceStatus':'DELETE_IN_PROGRESS'}]})
 finish({'StackEvents':state.get('events',{}).get(submitted['StackName'],[]),
         **({'NextToken':state['events_next_token']} if state.get('events_next_token') else {})})
state['submissions'].append([operation,submitted])
document=json.loads(state['raw']);assert document['base'] and document['base_sha256']
assert any(row['operation_id']==submitted.get('ClientToken',submitted.get('ClientRequestToken')) for row in document['operations'].values())
if state.get('fault') in ('cf-AccessDenied','cf-ExpiredToken'):
 fault=state['fault'][3:];state['fault']=None;finish(error=fault)
if operation=='create-change-set':
 stack=submitted['StackName'];stack=stack.split('/')[1] if stack.startswith('arn:') else stack
 stack_id='arn:aws:cloudformation:'+state['region']+':'+state['account']+':stack/'+stack+'/11111111-2222-3333-4444-555555555555'
 current={row['ParameterKey']:row['ParameterValue'] for row in stacks.get(stack_id,{}).get('Parameters',[])}
 parameters=[{'ParameterKey':row['ParameterKey'],'ParameterValue':current[row['ParameterKey']] if row.get('UsePreviousValue') else row['ParameterValue']} for row in submitted['Parameters']]
 changes[name]={'ChangeSetName':name,'ChangeSetId':'arn:aws:cloudformation:'+state['region']+':'+state['account']+':changeSet/'+name+'/11111111-2222-3333-4444-555555555555',
                'StackId':stack_id,'StackName':stack,'Description':submitted['Description'],'Parameters':parameters,
                'Status':'CREATE_COMPLETE','ExecutionStatus':'AVAILABLE','fixture_type':submitted['ChangeSetType'],
                'Capabilities':submitted['Capabilities'],'fixture_template':submitted['TemplateBody'],'fixture_role':submitted['RoleARN'],
                'Changes':[{'ResourceChange':{'LogicalResourceId':key,'ResourceType':row['Type'],
                 'Action':'Add' if submitted['ChangeSetType']=='CREATE' else 'Modify'}} for key,row in json.loads(submitted['TemplateBody'])['Resources'].items()]}
 if submitted['ChangeSetType']=='UPDATE':
  old=json.loads(state['templates'][stack_id])['Resources'];new=json.loads(submitted['TemplateBody'])['Resources'];updates=[]
  for logical,resource in new.items():
   before=old.get(logical,{}).get('Properties',{});after=resource.get('Properties',{})
   fields=sorted(key for key in set(before)|set(after) if before.get(key)!=after.get(key))
   if fields:
    updates.append({'ResourceChange':{'LogicalResourceId':logical,'ResourceType':resource['Type'],'Action':'Modify',
     'Replacement':'False','Scope':['Properties'],'Details':[{'Target':{'Attribute':'Properties','Name':key,'RequiresRecreation':'Never'},
     'Evaluation':'Static','ChangeSource':'DirectModification'} for key in fields]}})
  changes[name]['Changes']=updates
 if submitted['ChangeSetType']=='CREATE':
  stacks[stack_id]={'StackId':stack_id,'StackName':stack,'StackStatus':'REVIEW_IN_PROGRESS','Parameters':parameters,'Outputs':[]}
 if state.get('attach_role_on_prepare'):stacks[stack_id]['RoleARN']=submitted['RoleARN']
 kind='creation' if submitted['ChangeSetType']=='CREATE' else 'prepare-discard' if name.endswith('-session-discard') else 'activation'
 assert kind+':'+stack in document['resolved']
 if kind=='creation':assert document['resolved'][kind+':'+stack]['inputs']['values']=={row['ParameterKey']:row['ParameterValue'] for row in parameters}
 if state.get('prepare_status'):
  changes[name].update(Status=state.pop('prepare_status'),ExecutionStatus='UNAVAILABLE',Changes=[])
if operation=='execute-change-set':
 assert submitted['DisableRollback'] is True and 'OnStackFailure' not in submitted
 assert all(row['request'].get('disable_rollback') is True for row in document['operations'].values() if row['phase']!='delete')
 change=changes[name];change['execution_token']=submitted['ClientRequestToken'];change['ExecutionStatus']='EXECUTE_COMPLETE'
 stack_id=change['StackId'];stack=change['StackName'];status=state.pop('execution_status',change['fixture_type']+'_COMPLETE')
 if status.endswith('_FAILED'):change['ExecutionStatus']='EXECUTE_FAILED'
 if status.endswith('_IN_PROGRESS'):change['ExecutionStatus']='EXECUTE_IN_PROGRESS'
 stacks[stack_id]={'StackId':stack_id,'StackName':stack,'StackStatus':status,'Parameters':change['Parameters'],
                  'RoleARN':change['fixture_role'],
                  'Outputs':[{'OutputKey':key,'OutputValue':value} for key,value in state['outputs'][stack].items()]}
 state.setdefault('templates',{})[stack_id]=change['fixture_template']
 state.setdefault('resources',{})[stack_id]=[{'LogicalResourceId':key,'ResourceType':row['Type'],
  'PhysicalResourceId':state.get('physical_ids',{}).get(stack,{}).get(key,
   'sg-'+hashlib.sha256(key.encode()).hexdigest()[:17] if row['Type']=='AWS::EC2::SecurityGroup' else
   'arn:aws:ecs:'+state['region']+':'+state['account']+':service/fixture/'+key if row['Type']=='AWS::ECS::Service' else
   'ns-'+hashlib.sha256(key.encode()).hexdigest()[:16] if row['Type']=='AWS::ServiceDiscovery::PrivateDnsNamespace' else 'fixture-'+key),'ResourceStatus':status} for key,row in json.loads(change['fixture_template'])['Resources'].items()]
 if 'partial_resources' in state:state['resources'][stack_id]=state['resources'][stack_id][:state.pop('partial_resources')]
 reserved=next(row for row in document['operations'].values() if row['operation_id']==submitted['ClientRequestToken'])
 state.setdefault('events',{}).setdefault(stack_id,[]).insert(0,{'PhysicalResourceId':stack_id,'StackId':stack_id,
  'LogicalResourceId':stack,'EventId':submitted['ClientRequestToken']+'-root','ResourceType':'AWS::CloudFormation::Stack',
  'ClientRequestToken':submitted['ClientRequestToken'],'ResourceStatus':status,'Timestamp':reserved['reserved_at']})
 for other in list(changes):
  if other!=name and changes[other]['StackId']==stack_id:del changes[other]
if operation=='delete-stack':
 state.setdefault('deletions',{})[submitted['StackName']]=submitted['ClientRequestToken']
 stacks[submitted['StackName']]['StackStatus']='DELETE_IN_PROGRESS'
if state.get('fault')=='lost-'+operation:state['fault']=None;lost()
assert operation in ('create-change-set','execute-change-set','delete-stack')
if operation in ('execute-change-set','delete-stack'):
 persist();sys.exit(0)
finish({'Id':'fixture-change-set'})
'''


class SessionHandoffTests(unittest.TestCase):
    def test_session_permission_fences_are_only_projected_and_never_overwrite_a_foreign_binding(self):
        control = self.entity_plan["control"]
        self.assertEqual(control["record_key"], "sessions/kanbien-core-platform/current.json")
        self.assertEqual(dict(self.entity_plan["binding"].source_inputs)[control["template"]],
                         hashlib.sha256((ROOT / control["template"]).read_bytes()).hexdigest())
        self.assertNotIn(control["stack"], self.entity_plan["stack_order"])
        for phase in ("projected_templates", "activation_templates", "discard_templates"):
            for reference, raw in self.entity_plan[phase]:
                original = self.preparation.read_document(ROOT, reference)
                for resource in original["Resources"].values():
                    self.assertFalse(any(row.get("Key") == self.preparation.SESSION_TAG
                        for row in resource.get("Properties", {}).get("Tags", [])))
                    self.assertNotIn("PermissionsBoundary", resource.get("Properties", {}))
                for resource in json.loads(raw)["Resources"].values():
                    if resource["Type"] in self.preparation.SESSION_TAGGED_TYPES:
                        self.assertEqual([row for row in resource["Properties"]["Tags"]
                            if row["Key"] == self.preparation.SESSION_TAG],
                            [{"Key": self.preparation.SESSION_TAG, "Value": self.session_document["session_id"]}])
                    if resource["Type"] == "AWS::IAM::Role":
                        self.assertEqual(resource["Properties"]["PermissionsBoundary"], {"Fn::Sub":
                            "arn:${AWS::Partition}:iam::${AWS::AccountId}:policy/s-"
                            + self.session_document["session_id"][:19] + "-workloads"})
        document = {"Resources": {"Owned": {"Type": "AWS::EC2::VPC", "Properties": {
            "Tags": [{"Key": self.preparation.SESSION_TAG, "Value": "f" * 32}]}}}}
        with self.assertRaises(self.preparation.InputFailure) as conflict:
            self.preparation.session_fences(document, "a" * 32)
        self.assertEqual(conflict.exception.code, "preparation-inputs-session-tag-conflict")
        self.assertEqual(document["Resources"]["Owned"]["Properties"]["Tags"][0]["Value"], "f" * 32)
        document = {"Resources": {"Owned": {"Type": "AWS::IAM::Role", "Properties": {
            "PermissionsBoundary": "arn:aws:iam::337159794548:policy/foreign"}}}}
        with self.assertRaises(self.preparation.InputFailure) as conflict:
            self.preparation.session_fences(document, "a" * 32)
        self.assertEqual(conflict.exception.code, "preparation-inputs-session-boundary-conflict")
        self.assertEqual(document["Resources"]["Owned"]["Properties"]["PermissionsBoundary"],
                         "arn:aws:iam::337159794548:policy/foreign")
        self.assertFalse(self.read()["calls"])

    def test_native_credential_chain_omits_profile_without_weakening_fixed_context(self):
        native = OWNER.SESSION_CLI
        environment = {**self.environment, "AWS_PROFILE": "unselected", "AWS_DEFAULT_PROFILE": "unselected"}
        provider = native.SessionProvider(profile=None, region=self.records.region, environment=environment)
        def capture(arguments, **options):
            self.assertNotIn("--profile", arguments)
            self.assertEqual(arguments[arguments.index("--region") + 1], self.records.region)
            self.assertNotIn("AWS_PROFILE", options["environment"])
            self.assertNotIn("AWS_DEFAULT_PROFILE", options["environment"])
            self.assertEqual(options["environment"]["AWS_MAX_ATTEMPTS"], "1")
            self.assertEqual(options["environment"]["AWS_IGNORE_CONFIGURED_ENDPOINT_URLS"], "true")
            return {"Vpcs": []}
        with patch.object(native.CLI, "invoke_json", side_effect=capture) as invoke:
            self.assertEqual(provider("ec2", "describe-vpcs", VpcIds=["vpc-0123456789abcdef0"]), {"Vpcs": []})
        self.assertEqual(invoke.call_count, 1)
        records = self.make_records(profile=None, environment=environment)
        self.assertNotIn("--profile", records._arguments("get-object"))
        self.assertNotIn("AWS_PROFILE", records._environment)
        self.assertNotIn("AWS_DEFAULT_PROFILE", records._environment)
        self.assertEqual(self.records._arguments("get-object")[self.records._arguments("get-object").index("--profile") + 1], "fixture")

    @contextlib.contextmanager
    def in_process_aws(self):
        """Reuse FAKE for controller proof; transport tests retain real processes."""
        process = subprocess.run
        program = compile(FAKE, str(self.root / "aws"), "exec")
        self._in_process_state = self.read()
        def invoke(arguments, **options):
            environment = options.get("env", {})
            if (Path(arguments[0]).name != "aws"
                    or environment.get("SESSION_FIXTURE_STATE") != str(self.state_path)):
                return process(arguments, **options)
            output, error = io.StringIO(), io.StringIO()
            status = 0
            with patch.object(sys, "argv", list(arguments)), patch.dict(os.environ, environment, clear=True), \
                    contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                try: exec(program, {"__name__": "__main__", "fixture_state": self._in_process_state})
                except SystemExit as result: status = result.code or 0
            return subprocess.CompletedProcess(arguments, status, output.getvalue(), error.getvalue())
        try:
            with patch.object(subprocess, "run", side_effect=invoke):
                yield
        finally:
            state = self._in_process_state
            del self._in_process_state
            self.write(state)

    @classmethod
    def setUpClass(cls):
        cls.preparation = load("tested_session_preparation", ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py")
        document = {"schema": "deploy/environment-session-intent/v1", "target": "kanbien-core-platform",
                    "scope": "core-server-persistence", "session_id": "a" * 32, "starts_at": 1000, "expires_at": 8200,
                    "environment_lifecycle": {"mode": "temporary", "data_retention": "discard", "max_duration_seconds": 7200}}
        cls.session_document = deepcopy(document)
        cls.plan = cls.preparation.load_session_plan(ROOT, document["target"], document["scope"], document, 1000, 7200)
        document = {**document, "scope": "entity-smoke"}
        cls.entity_plan = cls.preparation.load_session_plan(ROOT, document["target"], document["scope"], document, 1000, 7200)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="environment-session-test-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.state_path = self.root / "state.json"
        source = self.plan["source_configuration"]
        self.write({"raw": None, "version": 0, "history": [], "calls": [], "submissions": [],
                    "account": source["account"], "region": source["region"], "fault": None})
        fake = self.root / "aws"
        fake.write_text("#!" + sys.executable + "\n" + FAKE)
        fake.chmod(0o700)
        self.environment = {"PATH": str(self.root), "SESSION_FIXTURE_STATE": str(self.state_path),
                            "PYTHONDONTWRITEBYTECODE": "1",
                            "SESSION_RUNTIME_OWNER": str(ROOT / "scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py")}
        self.now = 1000
        self.source_root = ROOT
        self.guards, self.preflights = [], []
        self.select_plan(self.plan)

    def select_plan(self, plan):
        self.plan = plan
        source = plan["source_configuration"]
        binding = self.plan["binding"]
        self.binding = {key: getattr(binding.intent, key) for key in ("target", "scope", "session_id", "starts_at", "expires_at")}
        self.binding["source_inputs_sha256"] = binding.source_inputs_sha256
        self.records = self.make_records()
        self.adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=self.preflight)
        self.stack = self.plan["stack_order"][0]
        self.reference = dict(self.plan["stack_templates"])[self.stack]
        self.inputs = {"stack": self.stack, "template_reference": self.reference}
        self.active_inputs = {"stack": dict(self.plan["stack_names"])[binding.intent.scope],
                              "template_reference": source["template"]}
        self.choices = {"private-network/v1": {"vpc_cidr": "10.42.0.0/16", "subnet_one_cidr": "10.42.1.0/24",
                        "subnet_two_cidr": "10.42.2.0/24", "availability_zone_one": source["region"] + "a",
                        "availability_zone_two": source["region"] + "b"}}
        publications = {dict(rows)["pipeline"]: dict(rows) for _, rows in plan["publication_selections"]}
        self.publications = {pipeline: {"run_id": 123 + index, "source_revision": "a" * 40}
                             for index, pipeline in enumerate(sorted(publications))}
        self.custody = None
        for pipeline, publication in sorted(publications.items()):
            selected = self.publications[pipeline]
            if self.custody is None:
                self.custody = CUSTODY.CustodyAcquisitionFixture(Path(tempfile.mkdtemp(prefix="custody-", dir=self.root)), publication=publication,
                    source_revision=selected["source_revision"], run_id=selected["run_id"])
            else:
                self.custody.add(publication, **selected)
            if publication["workflow"].endswith("publish-kanbien-core-platform-entity-smoke.yml"):
                self.v2_receipt(selected["run_id"])
        prefix = "arn:aws:"
        suffix = ":" + source["region"] + ":" + source["account"] + ":"
        outputs = {"VpcId": "vpc-0123456789abcdef0", "VpcCidr": "10.42.0.0/16",
                   "PrivateSubnetIds": "subnet-0123456789abcdef0,subnet-1123456789abcdef0",
                   "ClusterArn": prefix + "ecs" + suffix + "cluster/fixture", "LogGroupName": "/aws/ecs/" + plan["resource_name_prefix"],
                   "TaskExecutionRoleArn": "arn:aws:iam::" + source["account"] + ":role/fixture",
                   "ServiceDiscoveryArn": prefix + "servicediscovery" + suffix + "service/srv-fixture",
                   "PersistenceDatabaseEndpoint": "fixture.cluster.eu-west-2.rds.amazonaws.com",
                   "PersistenceDatabaseResourceId": "db-ABCDEFGHIJKLMNOP", "NamespaceId": "ns-fixture",
                   "S3ArtifactPrefixListId": "pl-0123456789abcdef0"}
        state = self.read(); state["outputs"] = {}; state["physical_ids"] = {}
        for stack, reference in plan["stack_templates"]:
            template = json.loads(dict(plan["projected_templates"])[reference])
            names = template.get("Outputs", {})
            state["physical_ids"][stack] = {logical: "sg-" + hashlib.sha256((stack + logical).encode()).hexdigest()[:17]
                for logical, resource in template["Resources"].items() if resource["Type"] == "AWS::EC2::SecurityGroup"}
            state["outputs"][stack] = {key: outputs.get(key.removeprefix("Supplied"),
                "sg-0123456789abcdef0" if "SecurityGroupId" in key else
                prefix + "secretsmanager" + suffix + "secret:fixture-value" if key.endswith("SecretArn") else "fixture-value") for key in names}
            for key, output in names.items():
                value = output.get("Value")
                if isinstance(value, dict) and set(value) == {"Ref"} and value["Ref"] in state["physical_ids"][stack]:
                    state["outputs"][stack][key] = state["physical_ids"][stack][value["Ref"]]
        self.write(state)
        self.transport = OWNER.SESSION_CLI.SessionProvider(profile="fixture", region=source["region"],
            environment={**self.environment, "CUSTODY_FIXTURE_STATE": str(self.custody.state_path)})

    def v2_receipt(self, run_id, extra_checks=0):
        receipt = self.custody.receipts[run_id]
        names = ["entity-smoke-infrastructure-route", "entity-smoke-composition-suite", "secret-dependency-declaration-regression"]
        names.extend("bounded-extra-check-" + str(index) for index in range(extra_checks))
        receipt["schema"] = "deploy/package-custody-receipt/v2"
        receipt["local_qualification"] = {"schema": "deploy/local-qualification/v1", "target": receipt["target"],
            "scope": "entity-smoke", "source_revision": receipt["source_revision"],
            "checks": {name: {"input_digest": "b" * 64, "evidence_key": "c" * 64} for name in names}}
        self.custody.set_archive(run_id)

    def initialize(self, adapter=None):
        with patch.dict(os.environ, self.custody.environment):
            return (adapter or self.adapter).initialize(choices=deepcopy(self.choices), publications=deepcopy(self.publications))

    def create_graph(self):
        self.initialize()
        for stack in self.plan["stack_order"]:
            inputs = {"stack": stack, "template_reference": dict(self.plan["stack_templates"])[stack]}
            self.adapter.prepare("creation", **inputs)
            self.adapter.execute("creation", **inputs)

    def task_identities(self, *, native=False):
        state = self.read()
        fields = {"AWS::ECS::TaskDefinition": "Family"}
        if native: fields.update({"AWS::IAM::Role": "RoleName", "AWS::RDS::DBInstance": "DBInstanceIdentifier", "AWS::SecretsManager::Secret": "Name"})
        for stack, reference in self.plan["stack_templates"]:
            template = json.loads(dict(self.plan["projected_templates"])[reference])
            for name, resource in template["Resources"].items():
                field = fields.get(resource["Type"])
                if field is None or field not in resource.get("Properties", {}): continue
                identity = resource["Properties"][field]
                if isinstance(identity, dict): identity = identity["Fn::Sub"]
                self.assertNotIn("${", identity)
                if resource["Type"] == "AWS::ECS::TaskDefinition":
                    identity = f"arn:aws:ecs:{self.records.region}:{self.records.account}:task-definition/{identity}:1"
                if resource["Type"] == "AWS::SecretsManager::Secret":
                    identity = f"arn:aws:secretsmanager:{self.records.region}:{self.records.account}:secret:{identity}-Ab1234"
                state["physical_ids"][stack][name] = identity
                if resource["Type"] == "AWS::RDS::DBInstance":
                    state["outputs"][stack]["PersistenceDatabaseResourceId"] = "db-" + hashlib.sha256(identity.encode()).hexdigest()[:24].upper()
            for key, row in template.get("Outputs", {}).items():
                value = row["Value"]
                if isinstance(value, dict) and set(value) == {"Ref"} and value["Ref"] in state["physical_ids"][stack]:
                    state["outputs"][stack][key] = state["physical_ids"][stack][value["Ref"]]
        if native: state["checked_runtime"] = True
        self.write(state)

    def task_fixture(self, *, entity=False, created=False, authority=None, administration=False, renamed_container=False):
        if entity and not created: self.select_plan(self.entity_plan)
        selected = next(row for row in self.adapter._task_selections if
            row["kind"] == ("entity-smoke-baseline/v1" if entity else "ordered-commands/v1")
            and (row["selection"].get("workload") == ("administration" if administration else "verifier")
                 and row["selection"].get("phase") == ("operation" if administration else "preflight")
                 and (not administration or row["selection"]["operation"] == "bootstrap")
                 if entity else row["step"] == "migration"))
        row, stack = selected["selection"], selected["stack"]
        logical = row["task_definition_ref" if entity else "task_definition"]
        template = json.loads(dict(self.plan["projected_templates"])[dict(self.plan["stack_templates"])[stack]])
        properties = template["Resources"][logical]["Properties"]
        family = properties["Family"]
        if isinstance(family, dict): family = family["Fn::Sub"]
        definition = f"arn:aws:ecs:{self.records.region}:{self.records.account}:task-definition/{family}:1"
        if not created:
            self.task_identities()
        if not created: self.create_graph()
        view = self.adapter.runtime_view(stack=stack, required_outputs=[])
        runtime = {"schema": "deploy/aws-task-runtime/v1", "session_id": self.binding["session_id"],
            "source_plan_sha256": view["source_plan_sha256"],
            "binding_sha256": "sha256:" + OWNER._digest({key: view[key] for key in ("binding", "custody", "stack_id")}),
            "stack_id": view["stack_id"], "cluster_arn": view["parameters"]["ClusterArn"], "family": family,
            "container_name": properties["ContainerDefinitions"][0]["Name"],
            "log_group": view["parameters"]["LogGroupName"], "log_stream_prefix": "fixture"}
        if renamed_container: runtime["container_name"] = "source-selected-renamed-container"
        base = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform"
        if entity:
            control = load("session_entity_task_control", base / "entity-smoke/task-execution/implementation/task-control.py")
            operation = "ready" if row["workload"] == "verifier" else "preflight"
            if row["phase"] == "operation": operation = row["operation"]
            environment = {control.OPERATIONS[row["workload"]][0]: operation,
                           "ENTITY_SMOKE_PROOF_LABEL": row["label"], "ENTITY_SMOKE_EXPECTED_SOURCE": "a" * 40}
            request = {"runtime": runtime, "workload": row["workload"], "definition": definition,
                "image_digest": "sha256:" + "a" * 64, "source_revision": "a" * 40,
                **{key: "sha256:" + "b" * 64 for key in ("configuration_contract_sha256", "permission_contract_sha256", "dependency_incarnation_sha256")},
                "security_group": "sg-0123456789abcdef0", "subnets": ["subnet-0123456789abcdef0"],
                "environment": environment, "deadline_seconds": 90, "proof_label": row["label"]}
            def validate(value):
                control.validate_request(value["request"])
                return control.AttemptStore.validate_record(selected["step"], value["request"], value,
                    validate_time=lambda instant: control.AttemptStore.validate_time(None, instant))
            storage = self.adapter.task_storage(selected["component"], selected["step"], validate_record=validate,
                validate_receipt=lambda *_: None,
                record_selection=lambda value: {"workload": value["request"]["workload"],
                    "operation": value["request"]["environment"][control.OPERATIONS[value["request"]["workload"]][0]]},
                key_for_record=lambda key, value: store.path_for(key, value), before_submit=authority)
            store = control.AttemptStore(None, storage=storage)
            return selected, storage, request, lambda: store.reserve(selected["step"], request), control
        operations = load("session_persistence_tasks", base / "core-server-persistence/task-operations.py")
        receipts = load("session_persistence_receipts", base / "core-server-persistence/proof-receipts.py")
        mode = row["proof"]["operation"]
        binding = operations.BoundOperation(root=self.root, proof_type="migration", family=family,
            container="persistence-migration", selector="PERSISTENCE_MIGRATION_OPERATION", results={mode: row["proof"]["result_code"]},
            aws=lambda *_: self.fail("no task provider"), report=lambda *_: None, accept=None, receipts=receipts, runtime=runtime)
        request = {"runtime": runtime, "task_definition": definition, "network": "{}", "deadline_seconds": 60, "admission": None,
            "overrides": {"containerOverrides": [{"name": runtime["container_name"], "environment": [{"name": binding.selector, "value": mode}]}]}}
        def validate_receipt(label, raw, record):
            value = receipts._decode(raw, task_arn_prefix=binding.task_prefix(request))
            self.assertEqual(label, receipts._label(value))
            self.assertEqual((value["task"]["arn"], value["task"]["definition"], value["operation"]),
                             (record["task_arn"], definition, mode))
        storage = self.adapter.task_storage(selected["component"], selected["step"],
            validate_record=lambda value: binding.validate_record(value, mode), validate_receipt=validate_receipt,
            record_selection=lambda value: {"workload": "persistence-migration-task", "proof_type": binding.proof_type,
                "operation": next(item["value"] for item in value["request"]["overrides"]["containerOverrides"][0]["environment"]
                                  if item["name"] == binding.selector)}, before_submit=authority)
        binding.storage, binding.step_id = storage, selected["step"]
        reserve = lambda: operations.JOURNAL.reserve_retained(storage, selected["step"], schema=binding.schema, mode=mode,
            request=request, new_operation=False, expected=None, completed=binding.completion,
            validate_record=lambda value: binding.validate_record(value, mode))
        return selected, storage, request, reserve, binding

    def connected_runtime_fixture(self):
        self.select_plan(self.entity_plan)
        self.task_identities(native=True)
        self.create_graph()
        views = {}
        required = {"foundation": ["VerifierSecurityGroupId", "EndpointSecurityGroupId"],
                    "core-server-persistence": ["PersistenceDatabaseEndpoint", "PersistenceDatabaseResourceId"], "entity-smoke": []}
        for component, outputs in required.items():
            views[component] = self.adapter.runtime_view(stack=dict(self.plan["stack_names"])[component], required_outputs=outputs)
        base = ROOT / "scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform"
        entity = load("connected_entity_binding", base / "entity-smoke/task-execution/implementation/task-binding.py")
        persistence = load("connected_persistence_binding", base / "core-server-persistence/task-operations.py")
        declaration = self.preparation.read_document(ROOT, "infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/10-workload-binding/workload-binding.yml")
        return views, entity, persistence, declaration

    def test_runtime_view_connected_producers_feed_native_retained_consumers(self):
        views, entity, persistence, declaration = self.connected_runtime_fixture()
        entity_view, persistence_view = views["entity-smoke"], views["core-server-persistence"]
        checked_entity = entity.inspect(self.transport, "verifier", entity_view["parameters"], entity_view["resources"],
            entity_view["template"], runtime_view=entity_view)
        checked_persistence = persistence.checked_runtime(self.transport, view=persistence_view, workload_binding=declaration,
            workload="persistence-migration-task", related_views=(views["foundation"],))
        for is_entity, checked in ((True, checked_entity), (False, checked_persistence)):
            selected, storage, request, reserve, native = self.task_fixture(entity=is_entity, created=True)
            request["runtime"] = deepcopy(checked["runtime"])
            if is_entity:
                request.update({key: deepcopy(checked[key]) for key in ("definition", "security_group", "subnets")})
                request["configuration_contract_sha256"] = checked["configuration_sha256"]
                request["permission_contract_sha256"] = checked["roles_sha256"]
                self.assertEqual(native.runtime(request)["container_name"], checked["runtime"]["container_name"])
                self.assertEqual(native.overrides(request)["containerOverrides"][0]["name"], checked["runtime"]["container_name"])
            else:
                native.runtime = deepcopy(checked["runtime"])
                request["task_definition"] = checked["definition"]
                request["network"] = json.dumps({"awsvpcConfiguration": {"subnets": checked["subnets"],
                    "securityGroups": [checked["security_group"]], "assignPublicIp": "DISABLED"}})
                self.assertEqual(native.context(request), checked["runtime"])
            value, fresh = reserve(); self.assertIs(fresh, True)
            self.assertEqual(value["request"]["runtime"], checked["runtime"])
            self.assertEqual(checked["runtime"]["source_plan_sha256"], self.adapter._plan_sha256)
        calls = self.read()["transport_inputs"]
        self.assertTrue(all(any(row[:2] == ["iam", operation] for row in calls) for operation in
            ("get-role", "list-role-policies", "list-attached-role-policies", "get-role-policy")))
        self.assertTrue(any(row[:2] == ["ecs", "describe-task-definition"] and row[2].get("include") == ["TAGS"] for row in calls))
        self.assertFalse(any(row[:2] == ["ecs", "run-task"] for row in calls))
        self.assertNotIn("rds.amazonaws.com", json.dumps([checked_entity, checked_persistence]))

    def test_runtime_view_connected_producers_reject_foreign_and_unavailable_observations(self):
        views, entity, persistence, declaration = self.connected_runtime_fixture()
        view = views["entity-smoke"]
        def inspect():
            return entity.inspect(self.transport, "verifier", view["parameters"], view["resources"], view["template"], runtime_view=view)
        baseline = self.read()
        foreign = deepcopy(views["foundation"]); foreign["binding"]["session_id"] = "f" * 32
        with self.assertRaises(Exception) as failure:
            persistence.checked_runtime(self.transport, view=views["core-server-persistence"], workload_binding=declaration,
                workload="persistence-migration-task", related_views=(foreign,))
        self.assertEqual(failure.exception.code, "runtime-binding-invalid")
        self.assertEqual(self.read()["calls"], baseline["calls"])
        arn = view["resources"]["VerifierTaskDefinition"]["physical_id"]
        role = view["resources"]["VerifierExecutionRole"]["physical_id"]
        task_call = ["ecs", "describe-task-definition", {"taskDefinition": arn}]
        observed = self.transport(*task_call[:2], **task_call[2]); observed["taskDefinition"]["taskDefinitionArn"] = arn + "0"
        role_call = ["iam", "get-role", {"RoleName": role}]
        role_value = self.transport(*role_call[:2], **role_call[2]); role_value["Role"]["Arn"] += "-foreign"
        cases = [(task_call, {"response": observed}, "task-binding-definition-not-confirmed"),
                 (role_call, {"response": role_value}, "task-binding-role-not-confirmed"),
                 (role_call, {"error": "AccessDenied"}, "aws-access-denied"),
                 (role_call, {"error": "PrivateUnknownFailure"}, "aws-command-failed")]
        for call, reply, code in cases:
            state = deepcopy(baseline); state["native_replies"] = {json.dumps(call, sort_keys=True, separators=(",", ":")): reply}; self.write(state)
            with self.assertRaises(Exception) as failure: inspect()
            self.assertEqual(failure.exception.code, code)
            self.assertNotIn("private", str(failure.exception).lower())
            self.assertNotIn("canary", repr(vars(failure.exception)))
            self.assertEqual(self.read()["history"], baseline["history"])
            self.assertEqual(self.read()["submissions"], baseline["submissions"])
        self.write(baseline)
        for operation in ("get-role", "list-role-policies", "list-attached-role-policies", "get-role-policy"):
            parameters = {"RoleName": role}
            if operation == "get-role-policy": parameters["PolicyName"] = "closed-fixture-policy"
            for provider_error, expected in (("AccessDenied", "aws-access-denied"), ("PrivateUnknownFailure", "aws-command-failed")):
                state = self.read(); call = ["iam", operation, parameters]
                state["native_replies"] = {json.dumps(call, sort_keys=True, separators=(",", ":")): {"error": provider_error}}; self.write(state)
                with self.assertRaises(OWNER.SESSION_CLI.SessionProviderFailure) as failure:
                    self.transport("iam", operation, **parameters)
                self.assertEqual(failure.exception.code, expected)
                self.assertNotIn("canary", str(failure.exception))
            before = self.read()["calls"]
            with self.assertRaises(OWNER.SESSION_CLI.SessionProviderFailure) as failure:
                self.transport("iam", operation, **parameters, Unexpected="private-canary")
            self.assertEqual(failure.exception.code, "session-provider-arguments-invalid")
            self.assertEqual(self.read()["calls"], before)
        for include in ([], ["TAGS", "TAGS"], ["PRIVATE"]):
            before = self.read()["calls"]
            with self.assertRaises(OWNER.SESSION_CLI.SessionProviderFailure) as failure:
                self.transport("ecs", "describe-task-definition", taskDefinition=arn, include=include)
            self.assertEqual(failure.exception.code, "session-provider-arguments-invalid")
            self.assertEqual(self.read()["calls"], before)

    def test_task_state_actual_journal_receipt_and_expired_observation(self):
        selected, storage, request, reserve, binding = self.task_fixture(authority=lambda _: None)
        value, fresh = reserve(); self.assertIs(fresh, True)
        self.assertIs(storage.before_submit(selected["step"], value), True)
        arn = binding.task_prefix(request) + "e" * 32
        binding.remember_task(value, None, arn)
        self.now = 8201; self.adapter.seal()
        receipt = binding.receipts.make(proof_type="migration", operation="apply", task={"taskArn": arn,
            "taskDefinitionArn": request["task_definition"], "startedAt": "2026-11-27T12:00:00Z", "stoppedAt": "2026-11-27T12:00:01Z",
            "lastStatus": "STOPPED", "containers": [{"exitCode": 0}]}, image_digest="sha256:" + "a" * 64,
            result_code=selected["selection"]["proof"]["result_code"], context={"completion_deadline_seconds": 60, "completion_duration_seconds": 1},
            controller="controlled-fixture", collected_at="2026-11-27T12:00:02Z", task_arn_prefix=binding.task_prefix(request))
        reference = binding.receipts.retain(receipt, root=self.root, storage=storage, task_arn_prefix=binding.task_prefix(request))
        binding.remember(value, None, reference)
        self.assertEqual(binding.completion(value), receipt)
        self.assertEqual(reserve(), (value, False))
        self.assertEqual(storage.read_receipt(reference["path"]), binding.receipts._render(receipt))
        changed = deepcopy(receipt); changed["task"]["image_digest"] = "sha256:" + "b" * 64
        changed["integrity"]["payload_sha256"] = binding.receipts.digest({key: item for key, item in changed.items() if key != "integrity"})
        with self.assertRaises(binding.receipts.ReceiptError):
            binding.receipts.retain(changed, root=self.root, storage=storage, task_arn_prefix=binding.task_prefix(request))
        self.assertEqual(storage.read_receipt(reference["path"]), binding.receipts._render(receipt))
        self.failed(lambda: storage.compare_and_reserve(selected["step"], value, value), "session-task-successor-prohibited")
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 2 * len(self.plan["stack_order"]))

    def test_task_state_actual_entity_alias_and_runtime_substitution(self):
        selected, storage, request, reserve, control = self.task_fixture(entity=True)
        value, fresh = reserve(); self.assertIs(fresh, True)
        key = control.AttemptStore(None, storage=storage).path_for(selected["step"], request)
        self.assertEqual(storage.read(key), value)
        self.assertEqual(reserve(), (value, False))
        changed = deepcopy(value); changed["request"]["runtime"]["session_id"] = "0" * 32
        changed["request_sha256"] = hashlib.sha256(control.canonical(changed["request"])).hexdigest()
        self.failed(lambda: storage.create(key, changed), "session-task-runtime-mismatch")
        self.failed(lambda: storage.read("foreign.json"), "session-task-key-mismatch")
        self.failed(lambda: storage.before_submit(key, value), "session-task-admission-unconfirmed")
        self.assertEqual(storage.read(key), value)

    def test_task_state_native_selector_misdirection_and_proof_type_are_rejected(self):
        selected, storage, request, reserve, control = self.task_fixture(entity=True, administration=True)
        wrong = deepcopy(request)
        wrong["environment"][control.OPERATIONS["administration"][0]] = "revoke-runtime"
        wrong["environment"]["ENTITY_SMOKE_PROOF_LABEL"] = "bootstrap"
        self.assertEqual(control.validate_request(wrong), wrong)
        before = self.read()["history"]
        store = control.AttemptStore(None, storage=storage)
        value = store.make_record(selected["step"], wrong)
        self.failed(lambda: storage.create(store.path_for(selected["step"], wrong), value), "session-task-selection-mismatch")
        with self.assertRaises(control.TaskFailure): store.reserve(selected["step"], wrong)
        self.assertEqual(self.read()["history"], before)
        self.assertIsNone(storage.read(store.path_for(selected["step"], request)))

        selected, storage, request, reserve, binding = self.task_fixture(created=True, renamed_container=True)
        self.assertNotEqual(binding.container, request["runtime"]["container_name"])
        binding.proof_type = "administration"
        with self.assertRaisesRegex(Exception, "^operation-retention-not-confirmed$"): reserve()
        self.assertIsNone(storage.read(selected["step"]))
        binding.proof_type = "migration"
        journal = load("session_task_initial_record", ROOT / "scripts/04.deploy/shared/provider-adapters/aws/task_journal.py")
        prefilled = journal.new_record(binding.schema, "apply", deepcopy(request), None)
        prefilled["task_arn"] = binding.task_prefix(request) + "a" * 32
        prefilled = journal.with_integrity(prefilled)
        self.failed(lambda: storage.compare_and_reserve(selected["step"], None, prefilled), "session-task-initial-record-invalid")
        self.failed(lambda: storage.retain_task(selected["step"], None, prefilled["task_arn"]), "session-task-predecessor-mismatch")
        value, fresh = reserve(); self.assertIs(fresh, True)
        self.assertEqual(value["request"]["overrides"]["containerOverrides"][0]["name"], request["runtime"]["container_name"])

    def test_task_state_lost_parent_readback_is_nonfresh_and_missing_child_is_not_empty(self):
        selected, storage, request, reserve, binding = self.task_fixture()
        self.fault("lost-put")
        with self.assertRaisesRegex(Exception, "^operation-retention-not-confirmed$"): reserve()
        state = self.read(); document = json.loads(state["raw"])
        self.assertIsNotNone(document["task_state"])
        value, fresh = reserve(); self.assertIs(fresh, False)
        self.failed(lambda: storage.before_submit(selected["step"], value), "session-task-not-fresh")
        cold = self.adapter.task_storage(selected["component"], selected["step"], validate_record=storage.validate_record,
            validate_receipt=storage.validate_receipt, record_selection=storage.record_selection)
        self.assertEqual(cold.read(selected["step"]), value)
        self.failed(lambda: cold.before_submit(selected["step"], value), "session-task-not-fresh")
        foreign = deepcopy(storage._state()[1]); foreign["binding"]["session_id"] = "f" * 32
        foreign_reference = self.records._retain_child(OWNER.RESERVATIONS.canonical(foreign), max_bytes=OWNER.RECORDS.CHILD_LIMIT)
        foreign_state = self.read(); foreign_document = json.loads(foreign_state["raw"])
        foreign_document["task_state"] = foreign_reference; foreign_state["raw"] = json.dumps(foreign_document); self.write(foreign_state)
        self.failed(lambda: storage.read(selected["step"]), "session-task-state-invalid")
        self.write(state)
        reference = document["task_state"]
        del state["children"][self.records._child_key(reference["sha256"])]; self.write(state)
        self.failed(lambda: storage.read(selected["step"]), "session-child-unavailable:aws-resource-missing")

    def test_task_state_expiry_between_reserve_and_submit_and_maximum_reference_capacity(self):
        selected, storage, request, reserve, binding = self.task_fixture(authority=lambda _: self.fail("expired callback"))
        state = self.read(); state["child_version_id"] = "\\" * 1024; self.write(state)
        value, fresh = reserve(); self.assertIs(fresh, True)
        document = json.loads(self.read()["raw"])
        self.assertEqual(len(document["task_state"]["version_id"]), 1024)
        self.assertLessEqual(self.records._completion_size(document), OWNER.RECORDS.LIMIT)
        self.now = 8200
        self.failed(lambda: storage.before_submit(selected["step"], value), "session-task-admission-unconfirmed")
        self.assertEqual(reserve(), (value, False))

    def test_task_state_expiry_after_child_write_never_adopts_or_grants_freshness(self):
        selected, storage, request, reserve, binding = self.task_fixture()
        original_retain = self.records._retain_child
        before = self.read()["history"]
        def expires(raw, **options):
            result = original_retain(raw, **options)
            self.now = 8200
            return result
        with patch.object(self.records, "_retain_child", side_effect=expires):
            with self.assertRaisesRegex(Exception, "^operation-retention-not-confirmed$"): reserve()
        self.assertIsNone(storage.fresh)
        self.assertEqual(self.read()["history"], before)
        self.assertIsNone(storage.read(selected["step"]))
        self.assertGreater(len(self.read()["child_history"]), 0)

    def test_task_state_competing_same_and_different_slots_keep_only_cas_winner(self):
        selected, storage, request, reserve, binding = self.task_fixture(entity=True)
        key = binding.AttemptStore(None, storage=storage).path_for(selected["step"], request)
        winner = self.adapter.task_storage(selected["component"], selected["step"],
            validate_record=storage.validate_record, validate_receipt=storage.validate_receipt,
            record_selection=storage.record_selection, key_for_record=storage.key_for_record)
        winner_store = binding.AttemptStore(None, storage=winner)
        winner_reserve = lambda: winner_store.reserve(selected["step"], request)
        original_commit = storage._commit
        winning = []
        def race(prior, state, action):
            winning.append(winner_reserve())
            return original_commit(prior, state, action)
        with patch.object(storage, "_commit", side_effect=race):
            with self.assertRaisesRegex(binding.TaskFailure, "^attempt-reservation-unavailable$"): reserve()
        self.assertIs(winning[0][1], True)
        self.assertEqual(storage.read(key), winning[0][0])
        self.assertIsNone(storage.fresh)
        self.assertEqual(sum(slot is not None for slot in winner._state()[1]["slots"]), 1)

        second, other, other_request, other_reserve, native = self.task_fixture(created=True)
        value = winning[0][0]
        other_commit = other._commit
        def different_slot(prior, state, action):
            # A competing update to the first slot wins while this independent
            # empty slot has only orphan children, not a parent reservation.
            self.failed(lambda: winner.before_submit(key, value), "session-task-admission-unconfirmed")
            return other_commit(prior, state, action)
        with patch.object(other, "_commit", side_effect=different_slot):
            with self.assertRaisesRegex(Exception, "^operation-retention-not-confirmed$"): other_reserve()
        self.assertIsNone(other.fresh)
        self.assertIsNone(other.read(second["step"]))
        self.assertEqual(sum(slot is not None for slot in winner._state()[1]["slots"]), 1)
        self.assertEqual(storage.read(key), value)

    def make_adapter(self, plan, records, **callbacks):
        return OWNER.SessionOperations(plan, records, source_root=self.source_root,
                                       approved_max_duration_seconds=7200, **callbacks)

    def source_variant(self, change):
        copied = self.root / "source"
        for reference in self.plan["references"]:
            destination = copied / reference
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / reference).read_bytes())
        target = self.session_document["target"]
        base = "infra/04.deploy/03.product/targets/" + target
        reference = base + "/00-target/target-profile.yml"
        profile = self.preparation.read_document(copied, reference)
        change(profile, copied / base)
        (copied / reference).write_text(json.dumps(profile))
        document = deepcopy(self.session_document)
        self.source_root = copied
        return self.preparation.load_session_plan(copied, target, document["scope"], document, 1000, 7200)

    def read(self):
        if hasattr(self, "_in_process_state"):
            return deepcopy(self._in_process_state)
        return json.loads(self.state_path.read_text())

    def write(self, state):
        if hasattr(self, "_in_process_state"):
            self._in_process_state = deepcopy(state)
            return
        self.state_path.write_text(json.dumps(state))

    def fault(self, value):
        state = self.read(); state["fault"] = value; self.write(state)

    def make_records(self, **overrides):
        values = {"bucket": "session-fixture", "key": "targets/fixture.json",
                  "account": self.plan["source_configuration"]["account"],
                  "region": self.plan["source_configuration"]["region"], "profile": "fixture",
                  "environment": self.environment, "binding": self.binding, "guard": self.guard, "clock": lambda: self.now}
        return OWNER.RECORDS.SessionRecords(**{**values, **overrides})

    def guard(self, action, binding):
        self.assertEqual(binding, self.binding)
        self.guards.append(action)

    def preflight(self, context):
        self.assertEqual(context["binding"], self.binding)
        self.assertEqual(context["source_plan"]["source_configuration"]["target"], "kanbien-core-platform")
        self.assertEqual(context["source_plan"]["execution_status"], "not-admitted")
        self.preflights.append(context)

    def provider(self, service, operation, **arguments):
        return self.transport(service, operation, **arguments)

    def failed(self, callback, fragment):
        with self.assertRaises((OWNER.SessionOperationFailure, OWNER.RECORDS.SessionRecordFailure)) as raised:
            callback()
        self.assertIn(fragment, raised.exception.code)
        self.assertNotIn("canary", str(raised.exception))
        return raised.exception.code

    def delete_inputs(self, stack=None):
        stack = self.stack if stack is None else stack
        stack_id = ("arn:aws:cloudformation:" + self.records.region + ":" + self.records.account
                    + ":stack/" + stack + "/11111111-2222-3333-4444-555555555555")
        return {"stack": stack, "stack_id": stack_id}

    def native_cleanup_fixture(self, *, whole_graph=False, cleanup=True):
        if whole_graph:
            self.select_plan(self.entity_plan)
        stacks = self.plan["stack_order"] if whole_graph else (self.stack,)
        state = self.read(); state["physical_ids"] = {}; facts = {}
        context = self.records.region + ":" + self.records.account
        native_lists = {
            "AWS::EC2::VPC": ("vpc", "describe-vpcs", "VpcIds", "Vpcs", "VpcId", "InvalidVpcID.NotFound"),
            "AWS::EC2::Subnet": ("subnet", "describe-subnets", "SubnetIds", "Subnets", "SubnetId", "InvalidSubnetID.NotFound"),
            "AWS::EC2::RouteTable": ("rtb", "describe-route-tables", "RouteTableIds", "RouteTables", "RouteTableId", "InvalidRouteTableID.NotFound"),
            "AWS::EC2::VPCEndpoint": ("vpce", "describe-vpc-endpoints", "VpcEndpointIds", "VpcEndpoints", "VpcEndpointId", "InvalidVpcEndpointId.NotFound"),
            "AWS::EC2::SecurityGroup": ("sg", "describe-security-groups", "GroupIds", "SecurityGroups", "GroupId", "InvalidGroup.NotFound"),
        }
        for stack in stacks:
            state["physical_ids"][stack] = {}
            for logical, kind in self.adapter._resource_index(stack):
                suffix = str(len(facts) + 1).zfill(17); identity = "opaque-" + suffix
                call, response, missing = None, None, None
                if kind in native_lists:
                    prefix, operation, argument, collection, field, error = native_lists[kind]
                    identity = prefix + "-" + suffix
                    call = ["ec2", operation, {argument: [identity]}]
                    response, missing = {collection: [{field: identity}]}, {"error": error}
                elif kind == "AWS::EC2::SubnetRouteTableAssociation":
                    identity = "rtbassoc-" + suffix; route = "rtb-" + suffix
                    call = ["ec2", "describe-route-tables", {"Filters": [{"Name": "association.route-table-association-id", "Values": [identity]}]}]
                    response = {"RouteTables": [{"RouteTableId": route, "Associations": [{"RouteTableAssociationId": identity, "RouteTableId": route}]}]}
                    missing = {"response": {"RouteTables": []}}
                elif kind == "AWS::IAM::Role":
                    identity = "fixture-role-" + suffix
                    call = ["iam", "get-role", {"RoleName": identity}]
                    response, missing = {"Role": {"RoleName": identity}}, {"error": "NoSuchEntity"}
                elif kind in ("AWS::RDS::DBInstance", "AWS::RDS::DBSubnetGroup"):
                    database = kind.endswith("DBInstance"); identity = "fixture-database-" + suffix
                    field = "DBInstanceIdentifier" if database else "DBSubnetGroupName"
                    collection = "DBInstances" if database else "DBSubnetGroups"
                    call = ["rds", "describe-db-instances" if database else "describe-db-subnet-groups", {field: identity}]
                    response, missing = {collection: [{field: identity}]}, {"error": "DBInstanceNotFoundFault" if database else "DBSubnetGroupNotFoundFault"}
                elif kind == "AWS::SecretsManager::Secret":
                    identity = "arn:aws:secretsmanager:" + context + ":secret:fixture-" + suffix + "-AbCd12"
                    call = ["secretsmanager", "describe-secret", {"SecretId": identity}]
                    response, missing = {"ARN": identity, "DeletedDate": 2000, "Name": "private-canary-name"}, {"error": "ResourceNotFoundException"}
                elif kind in ("AWS::ServiceDiscovery::PrivateDnsNamespace", "AWS::ServiceDiscovery::Service"):
                    namespace = kind.endswith("PrivateDnsNamespace"); identity = ("ns-" if namespace else "srv-") + suffix
                    call = ["servicediscovery", "get-namespace" if namespace else "get-service", {"Id": identity}]
                    response, missing = {"Namespace" if namespace else "Service": {"Id": identity}}, {"error": "NamespaceNotFound" if namespace else "ServiceNotFound"}
                elif kind == "AWS::Logs::LogGroup":
                    identity = "/aws/ecs/f" + suffix
                    call = ["logs", "describe-log-groups", {"logGroupIdentifiers": [identity]}]
                    response, missing = {"logGroups": [{"logGroupName": identity}]}, {"response": {"logGroups": []}}
                elif kind == "AWS::ECS::Cluster":
                    identity = "fixture"  # CloudFormation Ref/physical ID is the name.
                    arn = "arn:aws:ecs:" + context + ":cluster/" + identity
                    call = ["ecs", "describe-clusters", {"clusters": [arn]}]
                    response = {"clusters": [{"clusterName": identity, "clusterArn": arn, "status": "ACTIVE"}], "failures": []}
                    missing = {"response": {"clusters": [], "failures": [{"arn": arn, "reason": "MISSING"}]}}
                elif kind == "AWS::ECS::TaskDefinition":
                    identity = "arn:aws:ecs:" + context + ":task-definition/fixture-" + suffix + ":1"
                    call = ["ecs", "describe-task-definition", {"taskDefinition": identity}]
                    response = {"taskDefinition": {"taskDefinitionArn": identity, "status": "INACTIVE"}}
                    missing = {"error": "ClientException"}  # Not a documented absence discriminator.
                elif kind == "AWS::ECS::Service":
                    identity = "arn:aws:ecs:" + context + ":service/fixture/" + logical
                state["physical_ids"][stack][logical] = identity
                facts[stack, logical] = {"kind": kind, "identity": identity, "call": call, "present": {"response": response}, "missing": missing}
        for stack in stacks:
            reference = dict(self.plan["stack_templates"])[stack]
            for key, output in json.loads(dict(self.plan["projected_templates"])[reference]).get("Outputs", {}).items():
                value = output.get("Value")
                if isinstance(value, dict) and set(value) == {"Ref"} and value["Ref"] in state["physical_ids"][stack]:
                    state["outputs"][stack][key] = state["physical_ids"][stack][value["Ref"]]
        self.write(state)
        if whole_graph:
            self.create_graph()
        else:
            self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        for fact in facts.values():
            if fact["kind"] in ("AWS::EC2::SecurityGroup", "AWS::RDS::DBInstance", "AWS::ServiceDiscovery::PrivateDnsNamespace"):
                service, operation, arguments = fact["call"]
                response = self.provider(service, operation, **arguments)
                if fact["kind"] != "AWS::EC2::SecurityGroup" or response["SecurityGroups"]:
                    fact["present"] = {"response": response}
                else:
                    fact["present"]["response"]["SecurityGroups"][0].update(IpPermissions=[], IpPermissionsEgress=[])
        state = self.read(); state["native_replies"] = {}
        for row in facts.values():
            if row["call"] is not None:
                state["native_replies"][json.dumps(row["call"], sort_keys=True, separators=(",", ":"))] = row["present"]
        self.write(state)
        if not cleanup:
            return facts
        self.adapter.seal()
        for stack in reversed(stacks):
            self.adapter.delete(**self.delete_inputs(stack))
        for stack in stacks:
            self.confirm_fixture_delete(stack)
        return facts

    def confirm_fixture_delete(self, stack):
        state = self.read(); identifier = self.delete_inputs(stack)["stack_id"]
        reservation = json.loads(state["raw"])["operations"]["delete:" + stack + ":delete"]
        state["stacks"][identifier]["StackStatus"] = "DELETE_COMPLETE"
        state.setdefault("delete_events", {})[identifier] = [{"StackId": identifier, "PhysicalResourceId": identifier,
            "LogicalResourceId": stack, "ResourceType": "AWS::CloudFormation::Stack", "ResourceStatus": "DELETE_COMPLETE",
            "ClientRequestToken": reservation["operation_id"], "EventId": reservation["operation_id"] + "-root", "Timestamp": reservation["reserved_at"]}]
        self.write(state)

    def test_delete_uses_exact_stack_arn_token_request_and_copied_callbacks(self):
        self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "session-record-unavailable")
        self.initialize()
        self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "admission-open")
        self.adapter.prepare("creation", **self.inputs)
        self.adapter.seal(); self.now = 8200
        def checked(context):
            self.preflight(context)
            self.assertEqual(set(context["request"]), {"kind", "stack", "stack_id", "template_reference",
                             "source_plan_sha256", "arguments_sha256", "base_sha256"})
            self.assertEqual(context["request"]["base_sha256"], json.loads(self.read()["raw"])["base_sha256"])
            self.assertEqual(context["request"]["arguments_sha256"], OWNER._digest(context["operation_arguments"]))
            context["operation_arguments"]["StackName"] = "private-canary"
            context["request"]["stack_id"] = "private-canary"
            context["reservation"]["operation_id"] = "private-canary"
        adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=checked)
        for stack in (self.stack,):
            inputs = self.delete_inputs(stack)
            outcome = adapter.delete(**inputs)
            reservation = json.loads(self.read()["raw"])["operations"]["delete:" + stack + ":delete"]
            self.assertEqual(outcome["status"], "pending")
            self.assertEqual(outcome["request_sha256"], reservation["request_sha256"])
            self.assertEqual(self.read()["submissions"][-1], ["delete-stack",
                {"StackName": inputs["stack_id"], "ClientRequestToken": reservation["operation_id"],
                 "RoleARN": self.plan["execution_roles"]["cleanup"]}])
            before = self.read()
            self.assertEqual(adapter.delete(**inputs), outcome)
            self.assertEqual(self.read()["history"], before["history"])
            self.assertEqual(self.read()["submissions"], before["submissions"])
        document = json.loads(self.read()["raw"])
        self.assertIn(self.stack, document["creation_custody"])
        self.assertEqual(document["state"], "deleting")
        self.assertEqual(set(document["operations"]), {"creation:" + self.stack + ":prepare", "delete:" + self.stack + ":delete"})
        # The fake provider returned genuinely empty stdout for every success.
        self.assertEqual(sum(row[0] == "delete-stack" for row in self.read()["submissions"]), 1)

    def test_delete_rejects_malformed_inputs_and_all_caller_overrides_before_remote_use(self):
        inputs = self.delete_inputs()
        for missing in inputs:
            self.failed(lambda: self.adapter.delete(**{key: value for key, value in inputs.items() if key != missing}), "operation-inputs-invalid")
        for key in ("RoleARN", "RetainResources", "DeletionMode", "DeploymentConfig", "ClientRequestToken",
                    "StackName", "template_reference", "parameters", "private-canary-key"):
            self.failed(lambda: self.adapter.delete(**{**inputs, key: "private-canary"}), "operation-inputs-invalid")
        for stack in (None, [], "", "private-canary", self.plan["source_configuration"]["stack"]):
            self.failed(lambda: self.adapter.delete(**{**inputs, "stack": stack}), "instance-selection-invalid")
        identifier = inputs["stack_id"]
        variants = (None, [], "", self.stack, identifier.rsplit("/", 1)[0], identifier + "/extra",
                    identifier + "\n", identifier + ":extra", identifier + "x" * 2048,
                    identifier.replace(self.records.account, "999999999999"),
                    identifier.replace(self.records.region, "us-west-2"), identifier.replace("arn:aws:", "arn:aws-cn:"),
                    identifier.replace(self.stack, "private-canary"), identifier.rsplit("/", 1)[0] + "/")
        for stack_id in variants:
            self.failed(lambda: self.adapter.delete(**{**inputs, "stack_id": stack_id}), "stack-identity-invalid")
        for observe in (None, True, [], "private-canary"):
            self.failed(lambda: self.adapter.delete(**{**inputs, "observe": observe}), "operation-inputs-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_delete_phase_namespace_rejects_cross_product_before_remote_use(self):
        for kind in ("creation", "activation", "prepare-discard", "delete"):
            storage = self.records.storage(kind)
            request = {"kind": kind, "stack": self.stack}
            reservations = OWNER._Reservations(storage, request)
            for phase in ("prepare", "execute", "delete"):
                allowed = phase == "delete" if kind == "delete" else phase in ("prepare", "execute")
                if allowed:
                    self.assertEqual(reservations.path_for(phase, request), self.stack + ":" + phase)
                else:
                    self.failed(lambda: reservations.path_for(phase, request), "request-mismatch")
                    self.failed(lambda: storage.read(self.stack + ":" + phase), "session-operation-invalid")
        for method in (self.adapter.prepare, self.adapter.execute):
            self.failed(lambda: method("delete", **self.inputs), "kind-unsupported")
        self.assertEqual(self.read()["calls"], [])

    def test_delete_denied_or_lost_submission_retains_original_attempt_without_replay(self):
        for fault, reason in (("cf-AccessDenied", "aws-access-denied"), ("cf-ExpiredToken", "aws-credentials-expired"),
                              ("lost-delete-stack", "aws-response-invalid")):
            state = self.read(); state.update(raw=None, version=0, history=[], calls=[], submissions=[], deletions={}, fault=None); self.write(state)
            self.now = 1000; self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.seal(); self.fault(fault)
            code = self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "delete-stack-submission-uncertain")
            self.assertEqual(code, "environment-session-operation-delete-stack-submission-uncertain:" + reason)
            self.now = 8200; before = self.read()
            with patch.object(OWNER, "_module", side_effect=AssertionError("no revalidation or acquisition")):
                adapter = self.make_adapter(self.plan, self.make_records(), provider=self.provider, preflight=lambda _: True)
                adapter.delete(**self.delete_inputs())
            self.assertEqual(self.read()["history"], before["history"])
            self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_delete_missing_source_retains_intent_and_cold_recovery_only_observes(self):
        plan = self.source_variant(lambda *_: None); self.select_plan(plan)
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.seal(); self.now = 8200
        inputs = self.delete_inputs()
        self.adapter.delete(**inputs)
        self.source_root.rename(self.root / "relocated-source")
        before = self.read()
        self.assertEqual(len(json.loads(before["raw"])["operations"]), 2)
        with patch.object(OWNER, "_module", side_effect=AssertionError("no source import")):
            cold = self.make_adapter(self.plan, self.make_records(), provider=self.provider, preflight=lambda _: True)
            self.assertEqual(cold.delete(**inputs)["status"], "pending")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        changed = {**inputs, "stack_id": inputs["stack_id"][:-1] + "6"}
        self.failed(lambda: cold.delete(**changed), "reservation-mismatch")

    def test_delete_real_recapture_rejects_changed_captured_inputs_before_preflight(self):
        self.initialize(); self.adapter.seal()
        for field in ("execution_parameters", "execution_output_sources", "execution_source_values", "publication_selections"):
            adapter = self.make_adapter({**self.plan, field: ()}, self.records, provider=self.provider, preflight=self.preflight)
            self.failed(lambda: adapter.delete(**self.delete_inputs()), "inputs-source-mismatch")
        self.assertEqual(json.loads(self.read()["raw"])["operations"], {})
        self.assertEqual(self.read()["submissions"], [])

    def test_delete_qualified_preflight_denial_keeps_reservation_and_no_submission(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.seal()
        adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: True)
        self.failed(lambda: adapter.delete(**self.delete_inputs()), "preflight-unconfirmed")
        before = self.read()
        self.adapter.delete(**self.delete_inputs())
        self.assertEqual(self.read()["history"], before["history"])
        self.assertFalse(any(row[0] == "delete-stack" for row in self.read()["submissions"]))

    def test_delete_malformed_or_failed_observation_never_replays_submission(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.seal()
        self.adapter.delete(**self.delete_inputs())
        state = self.read(); state["transport_fault"] = "malformed"; self.write(state)
        result = self.adapter.delete(**self.delete_inputs())
        self.assertEqual((result["status"], result["reason"]), ("unknown", "aws-response-invalid"))
        self.assertEqual(self.adapter.delete(**self.delete_inputs())["status"], "pending")
        self.assertEqual(sum(row[0] == "delete-stack" for row in self.read()["submissions"]), 1)

    def test_connected_creation_uses_shared_tokens_and_resumed_observation(self):
        original = deepcopy(self.plan)
        self.initialize()
        prepared = self.adapter.prepare("creation", **self.inputs)
        executed = self.adapter.execute("creation", **self.inputs)
        self.assertEqual(prepared["status"], "ready")
        self.assertEqual(self.adapter.prepare("creation", **self.inputs)["status"], "succeeded")
        self.assertEqual(self.adapter.execute("creation", **self.inputs), executed)
        submissions = self.read()["submissions"]
        operations = json.loads(self.read()["raw"])["operations"]
        preparation = operations["creation:" + self.stack + ":prepare"]
        execution = operations["creation:" + self.stack + ":execute"]
        self.assertEqual([row[0] for row in submissions], ["create-change-set", "execute-change-set"])
        self.assertEqual(submissions[0][1]["ClientToken"], preparation["operation_id"])
        self.assertEqual(submissions[0][1]["Description"], preparation["operation_id"])
        self.assertEqual(submissions[1][1]["ClientRequestToken"], execution["operation_id"])
        self.assertEqual(prepared["request_sha256"], preparation["request_sha256"])
        self.assertEqual(executed["request_sha256"], execution["request_sha256"])
        self.assertIs(submissions[1][1]["DisableRollback"], True)
        self.assertEqual(submissions[0][1]["ChangeSetType"], "CREATE")
        self.assertEqual(self.preflights[-1]["preparation"]["operation_id"], preparation["operation_id"])
        self.assertEqual(self.preflights[-1]["operation_arguments"], {key: value for key, value in submissions[0][1].items()
                                                                    if key not in {"ClientToken", "Description"}})
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 2)
        self.assertEqual(self.plan, original)

    def test_actual_reader_absent_prerequisites_rejects_incomplete_plan_before_remote_use(self):
        def omit(profile, _):
            profile["provider"]["foundation"].pop("instance_prerequisites")
        with self.assertRaisesRegex(self.preparation.InputFailure, "^preparation-inputs-session-execution-coverage-invalid$"):
            self.source_variant(omit)
        self.assertEqual(self.read()["calls"], [])

    def test_prerequisite_components_and_output_rows_fail_closed_before_remote_use(self):
        prerequisites, sources = self.plan["prerequisite_components"], self.plan["stack_parameter_sources"]
        consumer, parameter, producer, output = sources[0]
        variants = [("prerequisite_components", value) for value in
                    (list(prerequisites), prerequisites + prerequisites, ("",), (17,), ("foundation",), (self.binding["scope"],))]
        variants.extend(("stack_parameter_sources", value) for value in
                        ((), list(sources), sources + sources, (list(sources[0]), *sources[1:]),
                         ((consumer, parameter, producer), *sources[1:]),
                         ((consumer, parameter, producer, 17), *sources[1:]),
                         ((*sources[0][:3], ""), *sources[1:]),
                         ((self.stack, parameter, producer, output), *sources[1:]),
                         ((consumer, "private-canary", producer, output), *sources[1:]),
                         ((consumer, parameter, "private-canary", output), *sources[1:]),
                         ((consumer, parameter, consumer, output), *sources[1:]),
                         ((consumer, parameter, producer, "private-canary"), *sources[1:]),
                         (*sources, (consumer, parameter, producer, "AnotherOutput"))))
        for reserved in dict(dict(self.plan["creation_parameters"])[self.plan["source_configuration"]["foundation_template"]]):
            variants.append(("stack_parameter_sources", ((consumer, reserved, producer, output), *sources[1:])))
        for key, value in variants:
            with self.subTest(key=key):
                self.failed(lambda: self.make_adapter({**self.plan, key: value}, self.records,
                            provider=self.provider, preflight=self.preflight), "prerequisite-bindings-invalid")
        pairs = dict(self.plan["stack_templates"])
        for stack, section, name in ((consumer, "Parameters", parameter), (producer, "Outputs", output)):
            for value in (None, "private-canary", {"Description": "no-value"}, {"Value": None}):
                if section == "Parameters" and isinstance(value, dict):
                    continue  # Template schema validity remains with the captured-source reader.
                reference = pairs[stack]
                template = json.loads(dict(self.plan["projected_templates"])[reference])
                template[section][name] = value
                changed = tuple((key, OWNER.RESERVATIONS.canonical(template).decode() if key == reference else body)
                                for key, body in self.plan["projected_templates"])
                self.failed(lambda: self.make_adapter({**self.plan, "projected_templates": changed}, self.records,
                            provider=self.provider, preflight=self.preflight), "prerequisite-bindings-invalid")
        self.failed(lambda: self.make_adapter({**self.plan, "prerequisite_components": ("private-canary",)}, self.records,
                    provider=self.provider, preflight=self.preflight), "instance-stacks-invalid")
        for missing in ("prerequisite_components", "stack_parameter_sources"):
            plan = {key: value for key, value in self.plan.items() if key != missing}
            self.failed(lambda: self.make_adapter(plan, self.records,
                        provider=self.provider, preflight=self.preflight), "source-plan-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_discard_bindings_reject_incomplete_duplicate_unowned_and_mutable_maps(self):
        templates, parameters = self.plan["discard_templates"], self.plan["discard_parameters"]
        variants = []
        for key, rows in (("discard_templates", templates), ("discard_parameters", parameters)):
            variants.extend(({key: ()}, {key: rows[:-1]}, {key: rows + rows}, {key: list(rows)},
                             {key: (list(rows[0]), *rows[1:])},
                             {key: (*rows, ("private-canary", rows[0][1]))},
                             {key: ((17, rows[0][1]), *rows[1:])}))
        reference, rows = parameters[0]
        variants.extend(({"discard_templates": ((templates[0][0], {}), *templates[1:])},
                         {"discard_parameters": ((reference, list(rows)), *parameters[1:])},
                         {"discard_parameters": ((reference, rows + rows), *parameters[1:])}))
        for change in variants:
            with self.subTest(change=next(iter(change))):
                self.failed(lambda: self.make_adapter({**self.plan, **change}, self.records,
                            provider=self.provider, preflight=self.preflight), "discard-bindings-invalid")
        for missing in ("discard_templates", "discard_parameters"):
            plan = {key: value for key, value in self.plan.items() if key != missing}
            self.failed(lambda: self.make_adapter(plan, self.records,
                        provider=self.provider, preflight=self.preflight), "source-plan-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_public_operation_inputs_reject_overrides_and_missing_keys_without_disclosure(self):
        for phase in ("prepare", "execute"):
            for kind in ("creation", "activation", "prepare-discard"):
                for key in ("parameters", "cleanup_template", "TemplateBody", "RoleARN", "DisableRollback", "disable_rollback", "OnStackFailure", "private-canary-key"):
                    with self.subTest(phase=phase, kind=kind, key=key):
                        self.assertEqual(self.failed(lambda: getattr(self.adapter, phase)(kind, **{**self.inputs, key: "private-canary"}),
                                         "operation-inputs-invalid"), "environment-session-operation-operation-inputs-invalid")
                for missing in self.inputs:
                    with self.subTest(phase=phase, kind=kind, missing=missing):
                        inputs = {key: value for key, value in self.inputs.items() if key != missing}
                        self.failed(lambda: getattr(self.adapter, phase)(kind, **inputs), "operation-inputs-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_gate_receives_a_copy_not_mutation_access_to_submission(self):
        retained = self.initialize()
        retained["base"]["choices"].clear()
        def mutate(context):
            context["operation_arguments"]["StackName"] = "production"
            context["operation_arguments"]["TemplateBody"] = "{}"
            context["operation_arguments"]["Parameters"].clear()
            context["request"]["stack"] = "production"
            context["source_plan"]["resource_name_prefix"] = "production"
        adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=mutate)
        adapter.prepare("creation", **self.inputs)
        submitted = self.read()["submissions"][0][1]
        self.assertEqual(submitted["StackName"], self.stack)
        self.assertEqual(submitted["TemplateBody"], dict(self.plan["projected_templates"])[self.reference])
        self.assertTrue(submitted["Parameters"])
        self.assertTrue(json.loads(self.read()["raw"])["base"]["choices"])

    def test_failed_exact_preflight_retains_intent_without_submission_or_retry(self):
        self.initialize()
        adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: True)
        self.failed(lambda: adapter.prepare("creation", **self.inputs), "preflight-unconfirmed")
        self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(self.read()["submissions"], [])
        self.assertEqual(len(json.loads(self.read()["raw"])["operations"]), 1)

    def test_checked_plan_and_remote_identity_must_match(self):
        for overrides in ({"account": "999999999999"}, {"region": "us-west-2"},
                          {"binding": {**self.binding, "session_id": "b" * 32}}):
            with self.subTest(overrides=overrides):
                self.failed(lambda: self.make_adapter(self.plan, self.make_records(**overrides),
                                                            provider=self.provider, preflight=self.preflight), "remote-binding-mismatch")
        plan = deepcopy(self.plan)
        plan["binding"] = replace(plan["binding"], intent=replace(plan["binding"].intent,
            lifecycle=replace(plan["binding"].intent.lifecycle, mode="persistent", data_retention="preserve")))
        self.failed(lambda: self.make_adapter(plan, self.records, provider=self.provider, preflight=self.preflight), "temporary-discard-required")
        self.assertEqual(self.read()["calls"], [])

    def test_child_exact_versions_binary_bytes_and_orphans_preserve_parent_after_expiry(self):
        import base64
        self.initialize(); self.adapter.seal(); self.now = 8201
        before = self.read()
        state = self.read(); state["child_version_id"] = "+/=" * 341 + "v"; self.write(state)
        raw = b"\x00\xffopaque intent, not JSON"
        reference = self.records._retain_child(raw)
        self.assertEqual(set(reference), {"sha256", "version_id", "bytes"})
        self.assertEqual(reference, {"sha256": hashlib.sha256(raw).hexdigest(), "version_id": state["child_version_id"], "bytes": len(raw)})
        self.assertEqual(len(reference["version_id"]), 1024)
        expected_key = "session-children/" + hashlib.sha256(self.records.key.encode()).hexdigest() + "/" + self.binding["session_id"] + "/" + reference["sha256"]
        state = self.read(); self.assertEqual(set(state["children"]), {expected_key})
        child = state["children"][expected_key]
        child["latest"] = "unrelated-latest"
        child["versions"]["unrelated-latest"] = {"body": base64.b64encode(b"other bytes").decode(),
            "metadata": {"ETag": '"other"', "VersionId": "unrelated-latest"}}
        self.write(state)
        self.assertEqual(self.records._read_child(reference), raw)
        requested = self.read()["argv"][-1]
        self.assertEqual(requested[requested.index("--version-id") + 1], reference["version_id"])
        self.failed(lambda: self.records._observe_child(raw), "child-reference-mismatch")
        final = self.read()
        for field in ("raw", "version", "history", "submissions"):
            self.assertEqual(final[field], before[field])
        self.assertIn("retain-child", self.guards)
        self.assertIn("read-child", self.guards)

    def test_child_bounds_and_reference_substitution_fail_without_payload_interpretation(self):
        self.initialize()
        before = self.read()
        for limit in (True, None, "65536", 1, 1048577):
            for invoke in (lambda: self.records._retain_child(b"x", max_bytes=limit),
                           lambda: self.records._observe_child(b"x", max_bytes=limit),
                           lambda: self.records._read_child({}, max_bytes=limit)):
                self.failed(invoke, "child-limit-invalid")
        for raw in (None, "x", bytearray(b"x"), b"", b"x" * 65537):
            self.failed(lambda: self.records._retain_child(raw), "child-payload-invalid")
        self.assertEqual(self.read()["calls"], before["calls"])
        for size, limit in ((65536, 65536), (1048576, 1048576)):
            raw = b"x" * size
            reference = self.records._retain_child(raw, max_bytes=limit)
            self.assertEqual(self.records._read_child(reference, max_bytes=limit), raw)
        self.failed(lambda: self.records._retain_child(b"x" * 1048577, max_bytes=1048576), "child-payload-invalid")
        self.failed(lambda: self.records._read_child(reference), "child-reference-invalid")
        reference = self.records._retain_child(b"reference")
        for changed in ({**reference, "key": "private-canary"}, {**reference, "bytes": True},
                        {**reference, "version_id": "null"}, {**reference, "version_id": "v" * 1025},
                        {**reference, "version_id": "private-canary\n"}):
            calls = self.read()["calls"]
            self.failed(lambda: self.records._read_child(changed), "child-reference-invalid")
            self.assertEqual(self.read()["calls"], calls)
        self.failed(lambda: self.records._read_child({**reference, "bytes": 1}), "child-reference-mismatch")
        self.failed(lambda: self.records._read_child({**reference, "sha256": "f" * 64}), "child-unavailable")
        foreign = self.make_records(binding={**self.binding, "session_id": "different-session"}, guard=lambda *_: None)
        self.assertNotEqual(foreign._child_key(reference["sha256"]), self.records._child_key(reference["sha256"]))
        self.failed(lambda: foreign._read_child(reference), "binding-mismatch")
        self.assertEqual(self.read()["raw"], before["raw"])

    def test_child_lost_conflicting_writes_need_explicit_read_only_recovery(self):
        self.initialize(); initial = self.read()
        for fault, expected in (("lost-put", "session-child-retention-unconfirmed:aws-response-invalid"),
                ("missing-put-version", "session-child-retention-unconfirmed"),
                ("readback-version", "session-child-unavailable:aws-command-failed"),
                ("PreconditionFailed", "session-child-conflict")):
            with self.subTest(fault=fault):
                state = deepcopy(initial); state["child_fault"] = fault; self.write(state)
                self.assertEqual(self.failed(lambda: self.records._retain_child(b"retained"), "child-"), expected)
                failed = self.read()
                child_calls = [argv for argv in failed["argv"][len(initial["argv"]):]
                               if argv[argv.index("--key") + 1].startswith("session-children/")]
                self.assertEqual(sum(argv[1] == "put-object" for argv in child_calls), 1)
                if fault in ("lost-put", "PreconditionFailed", "missing-put-version"):
                    self.assertEqual(len(child_calls), 1)
                state = self.read(); state["child_fault"] = None; self.write(state)
                reference = self.records._observe_child(b"retained")
                if fault == "PreconditionFailed":
                    self.assertIsNone(reference)
                else:
                    self.assertEqual(self.records._read_child(reference), b"retained")
                    calls = len(self.read()["argv"])
                    self.failed(lambda: self.records._retain_child(b"retained"), "child-conflict")
                    self.assertEqual([argv[1] for argv in self.read()["argv"][calls:]], ["get-object", "put-object"])
                self.assertEqual(self.read().get("child_history", []), failed.get("child_history", []))
                for field in ("raw", "version", "history", "submissions"):
                    self.assertEqual(self.read()[field], initial[field])

    def test_child_reads_require_positive_parent_guard_and_exact_metadata(self):
        self.failed(lambda: self.records._observe_child(b"x"), "record-unavailable")
        self.assertNotIn("children", self.read())
        self.initialize(); reference = self.records._retain_child(b"checked")
        valid = self.read()
        for fault, expected in (("AccessDenied", "session-child-unavailable:aws-access-denied"),
                ("ExpiredToken", "session-child-unavailable:aws-credentials-expired"),
                ("Unknown404", "session-child-unavailable:aws-command-failed"),
                *[(value, "session-child-unconfirmed") for value in
                  ("missing-version", "wrong-version", "long-version", "null-version", "partial-range", "wrong-length")],
                ("corrupt-bytes", "session-child-reference-mismatch")):
            state = deepcopy(valid); state["child_fault"] = fault; self.write(state)
            self.assertEqual(self.failed(lambda: self.records._read_child(reference), "child-"), expected)
            for field in ("raw", "history", "child_history", "submissions"):
                self.assertEqual(self.read()[field], valid[field])
        state = deepcopy(valid); state["child_fault"] = "wrong-version"; self.write(state)
        self.assertEqual(self.failed(lambda: self.records._observe_child(b"checked"), "child-unavailable"),
                         "session-child-unavailable:aws-command-failed")
        self.assertEqual(self.read()["child_history"], valid["child_history"])
        self.write(valid)
        def refuse(action, binding):
            if action in ("read-child", "retain-child"):
                raise OSError("private-canary")
            self.guard(action, binding)
        self.records._guard = refuse
        for invoke in (lambda: self.records._read_child(reference), lambda: self.records._retain_child(b"new")):
            count = len(self.read()["argv"])
            self.failed(invoke, "protection-unconfirmed")
            self.assertEqual([argv[1] for argv in self.read()["argv"][count:]], ["get-object"])
        self.assertEqual(self.read()["history"], valid["history"])

    def test_observe_existing_is_read_only_versioned_current_and_copied(self):
        self.failed(self.records.observe_existing, "session-record-unavailable")
        self.assertEqual(self.read()["history"], [])
        self.assertIsNone(self.read()["raw"])
        self.initialize(); self.adapter.seal()
        self.now = 8200
        before = self.read()
        observed = self.records.observe_existing()
        self.assertEqual(observed["document"], json.loads(before["raw"]))
        self.assertEqual(observed["version_id"], "version-" + str(before["version"]))
        self.assertEqual(observed["observed_at"], 8200)
        observed["document"]["state"] = "open"
        observed["document"]["binding"]["expires_at"] = 99999
        self.assertEqual(self.read()["raw"], before["raw"])
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["calls"][len(before["calls"]):], [["s3api", "get-object"]])
        self.assertEqual(self.read()["submissions"], [])

    def test_observe_existing_rejects_foreign_binding_bad_clock_and_unknown_version(self):
        self.initialize()
        before = self.read()
        foreign = self.make_records(binding={**self.binding, "source_inputs_sha256": "f" * 64}, guard=lambda *_: None)
        self.failed(foreign.observe_existing, "session-binding-mismatch")
        for now in (True, -1, "8200"):
            self.now = now
            self.failed(self.records.observe_existing, "session-clock-invalid")
        self.now = 8200
        self.fault("missing-version")
        self.failed(self.records.observe_existing, "session-record-unconfirmed")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], [])

    def test_missing_or_invalid_explicit_source_context_fails_before_remote_use(self):
        valid = {"source_root": ROOT, "approved_max_duration_seconds": 7200}
        variants = [{key: value for key, value in valid.items() if key != missing} for missing in valid]
        variants.extend({**valid, "source_root": value} for value in
                        (None, [], "", "relative-path"))
        variants.extend({**valid, "approved_max_duration_seconds": value} for value in
                        (None, True, "7200", 0, -1, 7199))
        for context in variants:
            with self.subTest(context=context):
                self.failed(lambda: OWNER.SessionOperations(self.plan, self.records, provider=self.provider,
                            preflight=self.preflight, **context), "source-context-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_concurrent_seal_wins_without_replayed_admission(self):
        self.initialize()
        self.fault("conflict-seal")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "record-conflict")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "admission-closed")
        self.assertEqual(self.read()["submissions"], [])
        self.assertEqual(json.loads(self.read()["raw"])["operations"], {})

    def test_cloudformation_lost_responses_resume_observation_without_resubmission(self):
        self.initialize()
        for phase, operation in (("prepare", "create-change-set"), ("execute", "execute-change-set")):
            with self.subTest(phase=phase):
                self.fault("lost-" + operation)
                call = lambda: getattr(self.adapter, phase)("creation", **self.inputs)
                code = self.failed(call, "submission-uncertain")
                self.assertEqual(code, "environment-session-operation-" + operation + "-submission-uncertain:aws-response-invalid")
                call()
        self.assertEqual([row[0] for row in self.read()["submissions"]], ["create-change-set", "execute-change-set"])

    def test_malformed_duplicate_oversized_and_foreign_records_fail_closed(self):
        self.initialize()
        valid = self.read()["raw"]
        for raw in ("{", valid[:-1] + ',"state":"open"}', "x" * 65537,
                    valid.replace(self.binding["session_id"], "b" * 32), valid.replace('"open"', '"completed"')):
            with self.subTest(length=len(raw)):
                state = self.read(); state["raw"] = raw; self.write(state)
                self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "session-")
        self.assertEqual(self.read()["submissions"], [])

    def test_local_reservation_behavior_is_unchanged(self):
        class Local(OWNER.RESERVATIONS.ImmutableReservationStore):
            schema, operation_prefix = "fixture/local/v1", "fixture-"
            def path_for(self, phase, request): return self.root / (phase + ".json")
            def validate_time(self, value):
                if not isinstance(value, str): raise self.failure("time-invalid")
        local = Local(self.root / "local")
        first, fresh = local.reserve("prepare", {"intent": "one"})
        self.assertTrue(fresh)
        self.assertEqual(local.reserve("prepare", {"intent": "one"}), (first, False))
        self.assertEqual(stat.S_IMODE((self.root / "local/prepare.json").stat().st_mode), 0o600)
        with self.assertRaises(OWNER.RESERVATIONS.ReservationFailure):
            local.reserve("prepare", {"intent": "different"})
        self.assertEqual(self.read()["calls"], [])

    def test_observer_failure_cannot_be_reported_as_success_or_resubmitted(self):
        self.initialize()
        self.adapter.prepare("creation", **self.inputs)
        state = self.read(); state["transport_fault"] = "malformed"; self.write(state)
        result = self.adapter.prepare("creation", **self.inputs)
        self.assertEqual((result["status"], result["reason"]), ("unknown", "aws-response-invalid"))
        self.assertEqual(self.adapter.prepare("creation", **self.inputs)["status"], "ready")
        self.assertEqual(len(self.read()["submissions"]), 1)

    def test_malformed_public_selections_have_finite_diagnostics(self):
        self.failed(lambda: self.adapter.prepare([], **self.inputs), "kind-unsupported")
        for key in ("stack", "template_reference"):
            self.failed(lambda: self.adapter.prepare("creation", **{**self.inputs, key: []}), "instance-selection-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_missing_duplicate_or_crossed_plan_pairs_are_rejected(self):
        pairs = self.plan["stack_templates"]
        variants = ((), pairs + (pairs[0],), ((pairs[0][0], pairs[1][1]), (pairs[1][0], pairs[0][1])))
        for pairs in variants:
            with self.subTest(pairs=pairs):
                plan = {**self.plan, "stack_templates": pairs}
                self.failed(lambda: self.make_adapter(plan, self.records, provider=self.provider, preflight=self.preflight), "template-bindings-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_typed_provider_denial_is_preserved_without_replaying_intent(self):
        self.initialize()
        self.fault("cf-AccessDenied")
        code = self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "submission-uncertain")
        self.assertEqual(code, "environment-session-operation-create-change-set-submission-uncertain:aws-access-denied")
        observed = self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(observed["status"], "unknown")
        self.assertEqual(observed["reason"], "aws-resource-missing")
        self.assertEqual(len(self.read()["submissions"]), 1)


    def test_initialization_rejects_unreviewed_choices_and_publications_before_remote_use(self):
        valid = {"choices": self.choices, "publications": self.publications}
        for inputs in ({}, {**valid, "parameters": []}, {**valid, "receipt": "private-canary"},
                       {"choices": {}}, {**valid, "choices": {}}, {**valid, "publications": {}},
                       {**valid, "choices": {"private-network/v1": {**self.choices["private-network/v1"], "VpcId": "private-canary"}}}):
            self.failed(lambda: self.adapter.initialize(**inputs), "invalid")
        pipeline = next(iter(self.publications))
        for selected in ({"run_id": True, "source_revision": "a" * 40}, {"run_id": 0, "source_revision": "a" * 40},
                         {"run_id": 123, "source_revision": "A" * 40}, {"run_id": 123, "source_revision": "a" * 40, "url": "private-canary"}):
            self.failed(lambda: self.adapter.initialize(**{**valid, "publications": {pipeline: selected}}), "publications-invalid")
        self.assertEqual(self.read()["calls"], [])
        self.assertEqual(self.custody.calls(), [])

    def test_initialization_authenticates_distinct_publications_once_and_rejects_later_selection_drift(self):
        self.select_plan(self.entity_plan)
        first = self.initialize()
        self.assertEqual(len(first["base"]["packages"]), 2)
        self.assertEqual(first["base_sha256"], OWNER._digest(first["base"]))
        self.assertEqual(first["resolved"], {})
        self.assertEqual(first["operations"], {})
        self.assertEqual(len([call for call in self.custody.calls() if call[:2] == ["attestation", "verify"] and call[-1] != "--help"]), 2)
        for pipeline, package in first["base"]["packages"].items():
            self.assertEqual(package["receipt"]["source_revision"], self.publications[pipeline]["source_revision"])
            self.assertEqual(package["receipt"]["image_digest"], package["evidence"]["image_digest"])
            self.assertNotEqual(package["evidence"]["image_digest"], package["evidence"]["runnable_digest"])
        self.adapter.seal(); self.now = 8200
        before, calls = self.read(), self.custody.calls()
        with patch.object(OWNER, "_module", side_effect=AssertionError("must not acquire retained inputs")):
            cold = self.make_adapter(self.plan, self.make_records(), provider=lambda *_args, **_kw: self.fail("no provider resolution"), preflight=lambda _: True)
            self.assertEqual(self.initialize(cold)["base"], first["base"])
            for field in ("choices", "publications"):
                inputs = {"choices": deepcopy(self.choices), "publications": deepcopy(self.publications)}
                if field == "choices": inputs[field]["private-network/v1"]["vpc_cidr"] = "10.43.0.0/16"
                else: inputs[field][next(iter(inputs[field]))]["run_id"] += 100
                self.failed(lambda: cold.initialize(**inputs), "inputs-selection-mismatch")
        self.assertEqual(self.custody.calls(), calls)
        self.assertEqual(self.read()["history"], before["history"])

    def test_initialization_network_acquisition_clock_and_retention_fail_closed(self):
        valid = deepcopy(self.choices)
        for field, value, reason in (("vpc_cidr", "8.8.0.0/16", "cidr-not-private"),
                                    ("subnet_two_cidr", "10.42.1.0/24", "subnet-overlap"),
                                    ("subnet_two_cidr", "10.43.1.0/24", "subnet-containment-invalid"),
                                    ("availability_zone_two", self.choices["private-network/v1"]["availability_zone_one"], "zone-selection-invalid")):
            self.choices = deepcopy(valid); self.choices["private-network/v1"][field] = value
            self.assertEqual(self.failed(self.initialize, "foundation-"), "environment-session-operation-foundation-network-" + reason)
            self.assertEqual(self.read()["history"], [])
        self.choices = valid
        for now, reason in ((True, "clock-invalid"), (-1, "clock-invalid"), (999, "admission-closed"), (8200, "admission-closed")):
            self.now = now; self.failed(self.initialize, reason)
        self.now = 1000
        self.custody.state["fail"]["help"] = 1; self.custody.write()
        self.failed(self.initialize, "custody-acquisition-")
        self.assertEqual(self.read()["history"], [])
        self.custody.state["fail"].clear(); self.custody.write()
        self.fault("lost-put")
        self.failed(self.initialize, "session-retention-unconfirmed")
        prior, calls = self.read(), self.custody.calls()
        self.initialize()
        self.assertEqual(self.custody.calls(), calls)
        self.assertEqual(self.read()["history"], prior["history"])
        self.assertEqual(self.read()["submissions"], [])

    def test_complete_entity_graph_derives_every_parameter_and_preserves_stable_request_digests(self):
        self.select_plan(self.entity_plan)
        original = deepcopy(self.plan)
        self.create_graph()
        document = json.loads(self.read()["raw"])
        self.assertLessEqual(len(self.read()["raw"].encode()), 65536)
        self.assertEqual(len(document["resolved"]), len(self.plan["stack_order"]))
        rows = (*self.plan["stack_parameter_sources"], *self.plan["execution_output_sources"])
        for stack, reference in self.plan["stack_templates"]:
            entry = document["resolved"]["creation:" + stack]
            template = json.loads(dict(self.plan["projected_templates"])[reference])
            self.assertEqual(set(entry["inputs"]["values"]), set(template["Parameters"]))
            self.assertTrue(all(not row.get("NoEcho", False) for row in template["Parameters"].values()))
            self.assertEqual(entry["sha256"], OWNER._digest(entry["inputs"]))
            for consumer, parameter, producer, output in rows:
                if consumer == stack:
                    self.assertEqual(entry["inputs"]["values"][parameter], self.read()["outputs"][producer][output])
            for phase in ("prepare", "execute"):
                request = document["operations"]["creation:" + stack + ":" + phase]["request"]
                self.assertEqual(request["base_sha256"], document["base_sha256"])
                self.assertEqual(request["resolved_inputs_sha256"], entry["sha256"])
        for row in self.read()["history"]:
            retained = json.loads(row)
            self.assertEqual(retained["base_sha256"], document["base_sha256"])
            for key, reservation in retained["operations"].items():
                self.assertEqual(reservation, document["operations"][key])
        before = self.read()
        with patch.object(OWNER, "_module", side_effect=AssertionError("no acquisition or source recapture")):
            for stack, reference in self.plan["stack_templates"]:
                inputs = {"stack": stack, "template_reference": reference}
                self.adapter.prepare("creation", **inputs); self.adapter.execute("creation", **inputs)
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(self.plan, original)

    def test_output_lineage_rejects_foreign_missing_unready_and_ambiguous_observations(self):
        self.initialize()
        foundation = dict(self.plan["stack_names"])["foundation"]
        inputs = {"stack": foundation, "template_reference": dict(self.plan["stack_templates"])[foundation]}
        self.failed(lambda: self.adapter.prepare("creation", **inputs), "output-creation-required")
        self.adapter.prepare("creation", **self.inputs)
        self.failed(lambda: self.adapter.prepare("creation", **inputs), "output-creation-required")
        self.adapter.execute("creation", **self.inputs)
        valid = self.read(); name = self.stack + "-session-create"; stack_id = valid["changes"][name]["StackId"]
        # Original change-set identity was authenticated and retained before
        # execution; its later mutation/deletion is not a new ownership source.
        mutations = [lambda s: s.update(events_next_token="private-canary"),
                     lambda s: s["events"][stack_id][0].update(ClientRequestToken="private-canary"),
                     lambda s: s["events"][stack_id][0].update(ResourceType="AWS::EC2::VPC"),
                     lambda s: s["stacks"][stack_id].update(StackStatus="UPDATE_IN_PROGRESS"),
                     lambda s: s["stacks"][stack_id].update(StackId="private-canary"),
                     lambda s: s["stacks"][stack_id].update(Outputs=[]),
                     lambda s: s["stacks"][stack_id]["Outputs"].append(s["stacks"][stack_id]["Outputs"][0])]
        for mutate in mutations:
            state = deepcopy(valid); mutate(state); self.write(state)
            self.failed(lambda: self.adapter.prepare("creation", **inputs), "operation-")
            self.assertEqual(self.read()["history"], valid["history"])
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid)
        self.adapter.prepare("creation", **inputs)
        self.assertEqual(len(self.read()["submissions"]), 3)

    def test_update_preserves_every_noncontrol_value_and_rejects_unowned_drift(self):
        self.create_graph()
        inputs = self.active_inputs
        identifier = self.delete_inputs(inputs["stack"])["stack_id"]
        valid = self.read(); document = json.loads(valid["raw"])
        original = document["resolved"]["creation:" + inputs["stack"]]["inputs"]["values"]
        controls = dict(dict(self.plan["activation_parameters"])[inputs["template_reference"]])
        state = deepcopy(valid)
        key = next(key for key in original if key not in controls)
        next(row for row in state["stacks"][identifier]["Parameters"] if row["ParameterKey"] == key)["ParameterValue"] = "private-canary"
        self.write(state)
        self.failed(lambda: self.adapter.prepare("activation", **inputs), "deployed-inputs-drift")
        self.assertEqual(self.read()["history"], valid["history"])
        self.write(valid)
        prepared = self.adapter.prepare("activation", **inputs)
        submitted = self.read()["submissions"][-1][1]
        self.assertEqual(submitted["StackName"], identifier)
        self.assertEqual(submitted["Parameters"], OWNER.CHANGE_SETS.update_parameter_inputs(original, controls))
        self.assertEqual(submitted["TemplateBody"], dict(self.plan["activation_templates"])[inputs["template_reference"]])
        retained = json.loads(self.read()["raw"])["resolved"]["activation:" + inputs["stack"]]
        self.assertEqual(retained["inputs"], {"observed_values_sha256": OWNER._digest(original)})
        self.assertEqual(retained["sha256"], OWNER._digest(retained["inputs"]))
        before = self.read(); calls = self.custody.calls()
        with patch.object(self.adapter, "_resolve", side_effect=AssertionError("resolved only once")):
            self.adapter.execute("activation", **inputs)
            historical = self.adapter.prepare("activation", **inputs)
            self.assertEqual(historical["status"], "succeeded")
            self.assertEqual(historical["request_sha256"], prepared["request_sha256"])
        self.assertEqual(self.custody.calls(), calls)
        self.assertEqual(len(self.read()["history"]), len(before["history"]) + 2)

    def test_sealed_expired_discard_recaptures_source_and_retained_attempts_only_observe(self):
        plan = self.source_variant(lambda *_: None); self.select_plan(plan)
        self.create_graph(); self.adapter.seal(); self.now = 8200
        inputs = self.active_inputs
        self.adapter.prepare("prepare-discard", **inputs)
        submitted = self.read()["submissions"][-1][1]
        self.assertEqual(submitted["TemplateBody"], dict(plan["discard_templates"])[inputs["template_reference"]])
        self.source_root.rename(self.root / "relocated-source")
        self.failed(lambda: self.adapter.execute("prepare-discard", **inputs), "source-unavailable")
        before = self.read()
        with patch.object(OWNER, "_module", side_effect=AssertionError("cold recovery cannot import source or custody")):
            cold = self.make_adapter(self.plan, self.make_records(), provider=self.provider, preflight=lambda _: True)
            cold.prepare("prepare-discard", **inputs)
            self.assertEqual(cold.execute("prepare-discard", **inputs)["status"], "not-submitted")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_changed_source_blocks_fresh_cleanup_and_changed_plan_cannot_adopt_base(self):
        plan = self.source_variant(lambda *_: None); self.select_plan(plan)
        self.create_graph(); self.adapter.seal()
        reference = next(ref for ref in plan["references"] if ref.endswith("target-profile.yml"))
        path = self.source_root / reference
        path.write_bytes(path.read_bytes() + b"\n# changed source\n")
        before = self.read()
        self.failed(lambda: self.adapter.prepare("prepare-discard", **self.active_inputs), "session-plan-mismatch")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertTrue(any(key.startswith("prepare-discard:") for key in json.loads(self.read()["raw"])["operations"]))
        changed = self.make_adapter({**plan, "execution_source_values": ()}, self.records, provider=self.provider, preflight=self.preflight)
        self.failed(lambda: changed.prepare("creation", **self.inputs), "inputs-source-mismatch")

    def test_lost_resolved_retention_never_submits_but_positive_later_read_can_reserve_first_attempt(self):
        for fault in ("lost-put", "readback-version", "missing-put-version"):
            state = self.read(); state.update(raw=None, version=0, history=[], calls=[], submissions=[], changes={}, fault=None); self.write(state)
            self.initialize(); self.fault(fault)
            self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "retention-unconfirmed")
            document = json.loads(self.read()["raw"])
            self.assertTrue(document["resolved"])
            self.assertEqual(document["operations"], {})
            self.assertEqual(self.read()["submissions"], [])
            with patch.object(self.adapter, "_resolve", side_effect=AssertionError("never resolve retained entry")):
                self.adapter.prepare("creation", **self.inputs)
            self.assertEqual(len(self.read()["submissions"]), 1)

    def test_lost_reservation_never_replays_and_tampered_input_or_request_hashes_reject(self):
        self.initialize()
        fired = False
        def guard(action, binding):
            nonlocal fired
            self.guard(action, binding)
            if action == "reserve-creation" and not fired:
                self.fault("lost-put"); fired = True
        self.records._guard = guard
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "retention-unconfirmed")
        before = self.read()
        self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], [])
        valid = self.read()
        for field in ("base", "resolved", "operations"):
            state = deepcopy(valid); document = json.loads(state["raw"])
            if field == "base": document["base"]["choices"].clear()
            elif field == "resolved": next(iter(document[field].values()))["inputs"]["values"].clear()
            else: next(iter(document[field].values()))["operation_id"] = "private-canary"
            state["raw"] = json.dumps(document); self.write(state)
            self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "session-")

    def test_closed_admission_and_ambiguous_store_reads_never_acquire_or_mutate(self):
        self.initialize()
        valid = self.read(); calls = self.custody.calls()
        for fault in ("AccessDenied", "ExpiredToken", "NoSuchBucket", "Unknown404", "missing-version", "null-version",
                      "missing-etag", "partial-range", "wrong-length"):
            state = deepcopy(valid); state["fault"] = fault; self.write(state)
            self.failed(self.initialize, "session-record-")
            self.assertEqual(self.read()["history"], valid["history"])
        self.assertEqual(self.custody.calls(), calls)
        self.write(valid)
        prepared = self.adapter.prepare("creation", **self.inputs)
        self.now = 8200
        self.assertEqual(self.adapter.prepare("creation", **self.inputs), prepared)
        self.failed(lambda: self.adapter.execute("creation", **self.inputs), "admission-closed")
        self.failed(lambda: self.adapter.prepare("activation", **self.active_inputs), "admission-closed")
        self.adapter.seal()
        self.assertEqual(self.adapter.prepare("creation", **self.inputs), prepared)
        self.failed(lambda: self.adapter.prepare("prepare-discard", **self.inputs), "output-creation-required")
        self.assertEqual(len(self.read()["submissions"]), 1)

    def test_discard_after_activation_uses_retained_original_evidence_not_deleted_change_set(self):
        self.create_graph()
        inputs = self.active_inputs
        self.adapter.prepare("activation", **inputs); self.adapter.execute("activation", **inputs)
        self.assertNotIn(inputs["stack"] + "-session-create", self.read()["changes"])
        self.adapter.seal(); self.now = 8200
        valid = self.read()
        for field, value, reason in (("creation_event_id_sha256", "f" * 64, "output-retained-creation-mismatch"),
                                     ("creation_request_sha256", "f" * 64, "record-shape-invalid"),
                                     ("change_set_id_sha256", "private-canary", "record-shape-invalid")):
            state = deepcopy(valid); document = json.loads(state["raw"])
            document["creation_evidence"][inputs["stack"]][field] = value
            state["raw"] = json.dumps(document); self.write(state)
            self.failed(lambda: self.adapter.prepare("prepare-discard", **inputs), reason)
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        state = deepcopy(valid); document = json.loads(state["raw"])
        document["incarnations"][inputs["stack"]] = "private-canary"
        state["raw"] = json.dumps(document); self.write(state)
        self.failed(lambda: self.adapter.prepare("prepare-discard", **inputs), "record-shape-invalid")
        self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid)
        before = len(valid["calls"])
        self.adapter.prepare("prepare-discard", **inputs); self.adapter.execute("prepare-discard", **inputs)
        after = self.read()
        # Its own discard observer uses DescribeChangeSet; original creation is
        # absent, so a successful handoff could not have depended on that object.
        self.assertNotIn(inputs["stack"] + "-session-create", after["changes"])
        self.assertEqual(after["submissions"][-2][1]["TemplateBody"], dict(self.plan["discard_templates"])[inputs["template_reference"]])
        self.assertGreater(len(after["calls"]), before)
        controls = dict(dict(self.plan["discard_parameters"])[inputs["template_reference"]])
        values = OWNER.CHANGE_SETS.parameter_values(after["changes"][inputs["stack"] + "-session-discard"]["Parameters"])
        self.assertTrue(all(values[key] == value for key, value in controls.items()))

    def test_plan_phase_closure_production_identity_and_raw_parameters_remain_closed(self):
        reference = self.active_inputs["template_reference"]
        foundation = self.plan["source_configuration"]["foundation_template"]
        changed = dict(dict(self.plan["activation_parameters"])[reference]); changed["ResourceNamePrefix"] = "production"
        variants = ({"activation_templates": ()}, {"activation_templates": self.plan["activation_templates"] * 2},
                    {"activation_templates": (*self.plan["activation_templates"], (foundation, "{}"))},
                    {"activation_parameters": ((reference, tuple(changed.items())),)})
        for mutation in variants:
            self.failed(lambda: self.make_adapter({**self.plan, **mutation}, self.records, provider=self.provider, preflight=self.preflight),
                        "activation-bindings-invalid")
        for mutation, reason in (({"stack": self.plan["source_configuration"]["stack"]}, "instance-selection-invalid"),
                                 ({"template_reference": foundation}, "template-stack-mismatch"),
                                 ({"parameters": []}, "operation-inputs-invalid")):
            self.failed(lambda: self.adapter.prepare("creation", **{**self.inputs, **mutation}), reason)
        self.failed(lambda: self.adapter.prepare("activation", **self.inputs), "activation-selection-invalid")
        self.assertEqual(self.read()["calls"], [])

    def test_guard_and_conditional_conflicts_are_finite_without_retry(self):
        for guard in (lambda *_: True, lambda *_: (_ for _ in ()).throw(ValueError("private-canary"))):
            records = self.make_records(guard=guard)
            adapter = self.make_adapter(self.plan, records, provider=self.provider, preflight=self.preflight)
            self.failed(lambda: self.initialize(adapter), "session-protection-unconfirmed")
        self.assertEqual(self.read()["calls"], [])
        self.initialize()
        for fault in ("PreconditionFailed", "ConditionalRequestConflict"):
            before = self.read(); self.fault(fault)
            self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "record-conflict")
            calls = self.read()["calls"][len(before["calls"]):]
            self.assertEqual(sum(call == ["s3api", "put-object"] for call in calls), 1)
            self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], [])

    def test_unavailable_source_revalidator_retains_discard_intent_without_replay(self):
        self.create_graph(); self.adapter.seal()
        before = self.read()
        with patch.object(OWNER, "_module", side_effect=ValueError("private-canary")):
            self.failed(lambda: self.adapter.prepare("prepare-discard", **self.active_inputs), "source-revalidator-unavailable")
        retained = self.read()
        self.assertEqual(retained["submissions"], before["submissions"])
        with patch.object(OWNER, "_module", side_effect=AssertionError("retained observation only")):
            self.assertEqual(self.adapter.prepare("prepare-discard", **self.active_inputs)["status"], "not-submitted")
        self.assertEqual(self.read()["history"], retained["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_renamed_prerequisite_component_and_outputs_use_the_same_derived_handoff(self):
        def rename(profile, base):
            declared = profile["provider"]["foundation"]["instance_prerequisites"]
            row = declared.pop(next(iter(declared)))
            row["stack"] = self.session_document["target"] + "-isolated-supplier"
            path = base / row["template"]
            template = self.preparation.CF.template(path.read_text())
            for parameter, output in row["foundation_parameters"].items():
                template["Outputs"]["Supplied" + output] = template["Outputs"].pop(output)
                row["foundation_parameters"][parameter] = "Supplied" + output
            declared["isolated-supplier"] = row
            path.write_text(json.dumps(template))
        plan = self.source_variant(rename); self.select_plan(plan)
        self.create_graph()
        self.assertEqual(plan["prerequisite_components"], ("isolated-supplier",))
        supplier = dict(plan["stack_names"])["isolated-supplier"]
        document = json.loads(self.read()["raw"])
        for consumer, key, producer, output in plan["stack_parameter_sources"]:
            self.assertEqual(producer, supplier)
            self.assertTrue(output.startswith("Supplied"))
            self.assertEqual(document["resolved"]["creation:" + consumer]["inputs"]["values"][key], self.read()["outputs"][producer][output])
        before = self.read()
        for component, stack in plan["stack_names"]:
            reference = dict(plan["stack_templates"])[stack]
            template = json.loads(dict(plan["projected_templates"])[reference])
            selected = sorted(template.get("Outputs", {}))[:1]
            view = self.adapter.runtime_view(stack=stack, required_outputs=selected)
            self.assertEqual(set(view), {"schema", "binding", "source_plan_sha256", "account", "region", "component", "stack",
                "stack_id", "phase", "template_reference", "template", "parameters", "resources", "outputs", "custody", "observed_at"})
            self.assertEqual(view["schema"], "deploy/aws-session-runtime-view/v1")
            self.assertEqual((view["component"], view["stack"], view["phase"], view["template_reference"]),
                             (component, stack, "creation", reference))
            self.assertEqual(view["binding"], self.binding)
            self.assertEqual(view["source_plan_sha256"], self.adapter._plan_sha256)
            self.assertEqual((view["account"], view["region"]), (self.records.account, self.records.region))
            self.assertEqual(view["template"], template)
            self.assertEqual(view["parameters"], document["resolved"]["creation:" + stack]["inputs"]["values"])
            self.assertEqual(view["outputs"], {name: before["outputs"][stack][name] for name in selected})
            expected = {row["LogicalResourceId"]: {"type": row["ResourceType"], "physical_id": row["PhysicalResourceId"]}
                        for row in before["resources"][view["stack_id"]]}
            self.assertEqual(view["resources"], expected)
            self.assertEqual(view["custody"], json.loads(self.read()["raw"])["creation_custody"][stack])
            self.assertIs(type(view["observed_at"]), int)
            self.assertEqual(view["observed_at"], self.now)
            original = deepcopy(view)
            for field in ("binding", "template", "parameters", "resources", "outputs", "custody"):
                view[field].clear()
            self.assertEqual(self.adapter.runtime_view(stack=stack, required_outputs=tuple(selected)), original)
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.adapter.prepare("activation", **self.active_inputs)
        view = self.adapter.runtime_view(stack=self.active_inputs["stack"], required_outputs=[])
        self.assertEqual(view["phase"], "creation")  # A ready change set has not changed the stack.
        self.adapter.execute("activation", **self.active_inputs)
        view = self.adapter.runtime_view(stack=self.active_inputs["stack"], required_outputs=[])
        self.assertEqual(view["phase"], "activation")
        controls = dict(dict(plan["activation_parameters"])[self.active_inputs["template_reference"]])
        self.assertEqual({key: view["parameters"][key] for key in controls}, controls)
        self.assertEqual(view["template"], json.loads(dict(plan["activation_templates"])[self.active_inputs["template_reference"]]))
        self.adapter.seal(); self.now = 8201
        before = self.read()
        expired = self.adapter.runtime_view(stack=self.active_inputs["stack"], required_outputs=[])
        self.assertEqual((expired["phase"], expired["observed_at"]), ("activation", 8201))
        self.assertEqual(json.loads(self.read()["raw"])["state"], "sealed")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_update_and_discard_lost_responses_only_observe_retained_inputs_even_after_expiry(self):
        self.create_graph(); count = len(self.read()["submissions"])
        for kind in ("activation", "prepare-discard"):
            if kind == "prepare-discard": self.adapter.seal()
            for phase, operation in (("prepare", "create-change-set"), ("execute", "execute-change-set")):
                self.now = 1000; self.fault("lost-" + operation)
                self.failed(lambda: getattr(self.adapter, phase)(kind, **self.active_inputs), "submission-uncertain:aws-response-invalid")
                self.now = 8200; before = self.read()
                with patch.object(OWNER, "_module", side_effect=AssertionError("no source or acquisition import")), \
                     patch.object(self.adapter, "_resolve", side_effect=AssertionError("no repeated input resolution")):
                    self.assertEqual(getattr(self.adapter, phase)(kind, **self.active_inputs)["status"],
                                     "ready" if phase == "prepare" else "succeeded")
                recovered = self.read()
                self.assertEqual(json.loads(recovered["raw"])["operations"], json.loads(before["raw"])["operations"])
                getattr(self.adapter, phase)(kind, **self.active_inputs)
                self.assertEqual(self.read()["history"], recovered["history"])
                self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(len(self.read()["submissions"]), count + 4)

    def test_complete_entity_lifecycle_fits_one_bounded_record_without_changing_prior_intent(self):
        self.select_plan(self.entity_plan)
        attempted = []
        original_bytes = self.records._bytes
        def measured(document):
            if isinstance(document, dict) and document.get("schema") == OWNER.RECORDS.SCHEMA:
                attempted.append(len(OWNER.RESERVATIONS.canonical(document)))
            return original_bytes(document)
        try:
            with patch.object(self.records, "_bytes", side_effect=measured):
                state = self.read(); state["child_version_id"] = "\\" * 1024; self.write(state)
                selected, storage, request, reserve, binding = self.task_fixture(authority=lambda _: None)
                value, fresh = reserve(); self.assertIs(fresh, True)
                self.assertIs(storage.before_submit(selected["step"], value), True)
                binding.remember_task(value, None, binding.task_prefix(request) + "f" * 32)
                original = deepcopy(json.loads(self.read()["raw"])["operations"])
                for stack, reference in self.plan["stack_templates"]:
                    if reference in dict(self.plan["activation_templates"]):
                        inputs = {"stack": stack, "template_reference": reference}
                        self.adapter.prepare("activation", **inputs); self.adapter.execute("activation", **inputs)
                self.adapter.seal(); self.now = 8200
                for stack in reversed(self.plan["stack_order"]):
                    inputs = {"stack": stack, "template_reference": dict(self.plan["stack_templates"])[stack]}
                    if inputs["template_reference"] in dict(self.plan["activation_templates"]):
                        self.adapter.prepare("prepare-discard", **inputs); self.adapter.execute("prepare-discard", **inputs)
                for stack in reversed(self.plan["stack_order"]):
                    self.adapter.delete(**self.delete_inputs(stack))
                    self.confirm_fixture_delete(stack)
                    outcome = self.adapter.reconcile_operation(kind="delete", stack=stack, phase="delete")
                    self.assertEqual((outcome["status"], outcome["provider_status"]), ("succeeded", "DELETE_COMPLETE"))
        except (OWNER.SessionOperationFailure, OWNER.RECORDS.SessionRecordFailure) as failure:
            self.fail(f"whole-session retention failed: {failure.code}; largest attempted record={max(attempted, default=0)} bytes")
        state = self.read(); final = json.loads(state["raw"])
        receipts = [row["receipt"] for row in final["base"]["packages"].values()]
        self.assertEqual([len(row["local_qualification"]["checks"]) for row in receipts if "local_qualification" in row], [3])
        self.assertEqual(len(final["operations"]), 20)
        self.assertEqual(len(final["resolved"]), 8)
        self.assertEqual(sum(shape["resource_count"] for shape in final["base"]["cleanup_shapes"].values()), 120)
        self.assertEqual(sum(len(row["slots"]) for row in final["physical_resources"].values()), 120)
        self.assertEqual(storage.read(selected["step"]), value)
        self.assertEqual(len(final["task_state"]["version_id"]), 1024)
        self.assertTrue(all(OWNER.RECORDS.SHA.fullmatch(slot) for row in final["physical_resources"].values() for slot in row["slots"]))
        for raw in state["history"]:
            self.assertLessEqual(len(raw.encode()), OWNER.RECORDS.LIMIT)
            document = json.loads(raw)
            self.assertLessEqual(self.records._completion_size(document), OWNER.RECORDS.LIMIT)
            for key, reservation in document["operations"].items():
                self.assertEqual(reservation, final["operations"][key])
        self.assertTrue(all(final["operations"][key] == value for key, value in original.items()))
        self.__class__.maximum_retained_bytes = max(len(raw.encode()) for raw in state["history"])
        self.__class__.maximum_completion_bytes = max(self.records._completion_size(json.loads(raw)) for raw in state["history"])
        print("session capacity bytes: retained=" + str(self.maximum_retained_bytes)
              + " reserved-completion=" + str(self.maximum_completion_bytes))
        self.assertEqual([row[1]["StackName"] for row in state["submissions"] if row[0] == "delete-stack"],
                         [self.delete_inputs(stack)["stack_id"] for stack in reversed(self.plan["stack_order"])])
        self.assertEqual(final["base"]["execution_roles"], self.plan["execution_roles"])
        for operation, arguments in state["submissions"]:
            if operation == "execute-change-set":
                self.assertNotIn("RoleARN", arguments)
            else:
                cleanup = operation == "delete-stack" or arguments["ChangeSetName"].endswith("-session-discard")
                self.assertEqual(arguments["RoleARN"], final["base"]["execution_roles"]["cleanup" if cleanup else "creation"])
        # DeleteStack completion remains operation evidence, not proof of
        # physical resource absence, retained-data removal or cost savings.

    def test_large_valid_v2_receipt_rejects_before_initialization_can_spend_cleanup_capacity(self):
        self.select_plan(self.entity_plan)
        run_id = next(run for run, publication in self.custody.publications.items()
                      if publication["workflow"].endswith("publish-kanbien-core-platform-entity-smoke.yml"))
        self.v2_receipt(run_id, 290)
        self.assertEqual(self.failed(self.initialize, "cleanup-capacity-exceeded"), "session-cleanup-capacity-exceeded")
        self.assertEqual(self.read()["submissions"], [])
        self.assertIsNone(self.read()["raw"])
        self.assertEqual(self.read()["history"], [])

    def test_later_capacity_denial_preserves_every_earlier_stacks_cleanup(self):
        self.select_plan(self.entity_plan)
        run_id = next(run for run, publication in self.custody.publications.items()
                      if publication["workflow"].endswith("publish-kanbien-core-platform-entity-smoke.yml"))
        # Leave room to admit an earlier stack, but not the whole graph. The
        # exact rejection stack is not the contract; prior cleanup capacity is.
        self.v2_receipt(run_id, 100)
        self.initialize()
        admitted = []
        for stack in self.plan["stack_order"]:
            inputs = {"stack": stack, "template_reference": dict(self.plan["stack_templates"])[stack]}
            try:
                self.adapter.prepare("creation", **inputs)
                self.adapter.execute("creation", **inputs)
            except (OWNER.RECORDS.SessionRecordFailure, OWNER.SessionOperationFailure) as failure:
                self.assertTrue(failure.code.endswith("session-cleanup-capacity-exceeded"))
                break
            admitted.append(inputs)
        else:
            self.fail("fixture did not reach the next-stack capacity boundary")
        self.assertGreater(len(admitted), 0)
        original = deepcopy(json.loads(self.read()["raw"])["operations"])
        self.adapter.seal(); self.now = 8200
        for inputs in reversed(admitted):
            self.adapter.delete(**self.delete_inputs(inputs["stack"]))
        final = json.loads(self.read()["raw"])
        self.assertTrue(all(final["operations"][key] == value for key, value in original.items()))
        self.assertEqual(sum(row[0] == "delete-stack" for row in self.read()["submissions"]), len(admitted))
        for raw in self.read()["history"]:
            self.assertLessEqual(self.records._completion_size(json.loads(raw)), OWNER.RECORDS.LIMIT)

    def test_capacity_shapes_and_identity_bounds_are_enforced_and_custody_is_append_once(self):
        self.create_graph()
        valid = self.read(); document = json.loads(valid["raw"])
        stack = next(iter(document["creation_evidence"]))
        identity, proof = document["incarnations"][stack], document["creation_evidence"][stack]
        for changed in (identity + "x", identity[:identity.rindex("/") + 1] + "x" * 2048):
            self.failed(lambda: self.records.retain_ownership(stack, changed, proof), "ownership-mismatch")
        self.failed(lambda: self.records.retain_ownership(stack, identity, {**proof, "creation_event_id_sha256": "f" * 64}), "ownership-mismatch")
        self.assertEqual(self.read()["history"], valid["history"])
        mutations = [lambda d: d.update(schema="aws-temporary-session/v1"),
                     lambda d: d["incarnations"].update({stack: identity + "x" * 2048}),
                     lambda d: d["creation_evidence"][stack].update(change_set_id_sha256="a" * 65),
                     lambda d: next(iter(d["operations"].values())).update(operation_id="es-" + "a" * 33),
                     lambda d: next(iter(d["operations"].values())).update(reserved_at="2026-11-27T00:00:00.0000000+00:00")]
        for mutate in mutations:
            state = deepcopy(valid); changed = json.loads(state["raw"]); mutate(changed)
            state["raw"] = json.dumps(changed); self.write(state)
            self.failed(self.records.observe_existing, "session-")
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        state = deepcopy(valid); changed = json.loads(state["raw"])
        changed["base"]["cleanup_shapes"][stack]["discard"] = False
        changed["base_sha256"] = OWNER._digest(changed["base"])
        state["raw"] = json.dumps(changed); self.write(state)
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "record-shape-invalid")
        self.assertEqual(self.read()["submissions"], valid["submissions"])

    def test_concrete_transport_rejects_unknown_inputs_and_preserves_exact_bounded_serialization(self):
        owner = OWNER.SESSION_CLI
        calls = deepcopy(self.read()["calls"])
        variants = [("s3api", "put-object", {}), ("cloudformation", "delete-stack", {}),
                    ("cloudformation", "delete-stack", {"StackName": self.stack, "ClientRequestToken": "es-" + "a" * 32}),
                    ("cloudformation", "get-template", {"StackName": self.stack, "TemplateStage": "Processed"}),
                    ("cloudformation", "get-template", {"StackName": self.stack, "ChangeSetName": "fixture"}),
                    ("cloudformation", "get-template", {"StackName": self.stack, "TemplateStage": "Original", "RoleARN": "private-canary"}),
                    ("cloudformation", "list-stack-resources", {"StackName": self.stack, "NextToken": "private-canary"}),
                    ("cloudformation", "delete-stack", {"StackName": self.stack, "ClientRequestToken": "es-" + "a" * 32, "RoleARN": "private-canary"}),
                    ("ec2", "describe-availability-zones", {"ZoneNames": [] , "endpoint_url": "private-canary"}),
                    ("ecr", "describe-image-scan-findings", {"repositoryName": "fixture", "imageId": {}, "maxResults": True})]
        execute = {"StackName": self.stack, "ChangeSetName": "fixture", "ClientRequestToken": "es-" + "a" * 32}
        variants.extend((service, operation, arguments) for service, operation, arguments in (
            ("ec2", "describe-vpcs", {"VpcIds": []}),
            ("ec2", "describe-subnets", {"SubnetIds": ["subnet-0123456789abcdef0"], "NextToken": "private-canary"}),
            ("ec2", "describe-route-tables", {"Filters": [{"Name": "vpc-id", "Values": ["private-canary"]}]}),
            ("ec2", "describe-route-tables", {"Filters": [{"Name": "association.route-table-association-id", "Values": []}]}),
            ("rds", "describe-db-instances", {"DBInstanceIdentifier": "fixture", "Marker": "private-canary"}),
            ("rds", "describe-db-snapshots", {"SnapshotType": "shared", "IncludePublic": False, "IncludeShared": False}),
            ("rds", "describe-db-snapshots", {"SnapshotType": "manual", "IncludePublic": True, "IncludeShared": False}),
            ("rds", "describe-db-instance-automated-backups", {"DBInstanceIdentifier": "private-canary"}),
            ("route53", "get-hosted-zone", {"Id": "ZFIXTURE", "Marker": "private-canary"}),
            ("ecs", "describe-clusters", {"clusters": ["first", "second"]}),
            ("ecs", "describe-services", {"cluster": "fixture", "services": []}),
            ("logs", "describe-log-groups", {"logGroupIdentifiers": [1]})))
        variants.extend(("cloudformation", "execute-change-set", {**execute, **policy}) for policy in
                        ({}, {"DisableRollback": False}, {"DisableRollback": 1}, {"DisableRollback": "true"},
                         {"DisableRollback": True, "OnStackFailure": "private-canary"}))
        variants.append(("cloudformation", "execute-change-set", {**execute, "DisableRollback": True,
                         "RoleARN": self.plan["execution_roles"]["creation"]}))
        for service, operation, arguments in variants:
            with self.assertRaises(owner.SessionProviderFailure) as failure:
                self.transport(service, operation, **arguments)
            self.assertEqual(failure.exception.code, "session-provider-operation-unsupported" if service == "s3api"
                             else "session-provider-arguments-invalid")
            self.assertNotIn("canary", str(failure.exception))
        self.assertEqual(self.read()["calls"], calls)
        arguments = {"StackName": self.stack, "ChangeSetName": "fixture", "ChangeSetType": "CREATE", "TemplateBody": "",
                     "Parameters": [], "Capabilities": [], "ClientToken": "es-" + "a" * 32, "Description": "fixture",
                     "RoleARN": self.plan["execution_roles"]["creation"]}
        arguments["TemplateBody"] = "x" * (owner.MAX_INPUT_BYTES - len(OWNER.RESERVATIONS.canonical(arguments)))
        def inspected(command, **options):
            path = Path(command[command.index("--cli-input-json") + 1].removeprefix("file://"))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(len(path.read_bytes()), owner.MAX_INPUT_BYTES)
            self.assertEqual(json.loads(path.read_bytes()), arguments)
            self.assertEqual(options["timeout"], 35)
            self.assertEqual(options["empty_body"], "reject")
            self.assertEqual(options["environment"]["AWS_MAX_ATTEMPTS"], "1")
            self.assertEqual(command[command.index("--profile") + 1], "fixture")
            self.assertEqual(command[command.index("--region") + 1], self.records.region)
            return {}
        with patch.object(owner.CLI, "invoke_json", side_effect=inspected) as invoked:
            self.assertEqual(self.transport("cloudformation", "create-change-set", **arguments), {})
            arguments["TemplateBody"] += "x"
            with self.assertRaises(owner.SessionProviderFailure) as failure:
                self.transport("cloudformation", "create-change-set", **arguments)
            self.assertEqual(failure.exception.code, "session-provider-input-too-large")
            self.assertEqual(invoked.call_count, 1)
        self.assertEqual(self.read()["calls"], calls)

    def test_concrete_transport_response_policy_finite_causes_and_complete_ecr_handoff(self):
        owner = OWNER.SESSION_CLI
        for operation in ("execute-change-set", "delete-stack", "describe-stacks"):
            arguments = {"StackName": self.stack}
            if operation != "describe-stacks": arguments["ClientRequestToken"] = "es-" + "a" * 32
            if operation == "execute-change-set": arguments.update(ChangeSetName="fixture", DisableRollback=True)
            if operation == "delete-stack": arguments["RoleARN"] = self.plan["execution_roles"]["cleanup"]
            for fault in ("empty", "whitespace", "malformed", "array", "next-token", "AccessDenied", "ExpiredToken"):
                state = self.read(); state["transport_fault"] = fault; self.write(state)
                before = len(state["calls"])
                if fault == "empty" and operation != "describe-stacks":
                    self.assertEqual(self.transport("cloudformation", operation, **arguments), {})
                else:
                    with self.assertRaises(owner.SessionProviderFailure) as failure:
                        self.transport("cloudformation", operation, **arguments)
                    expected = {"AccessDenied": "aws-access-denied", "ExpiredToken": "aws-credentials-expired"}.get(fault, "aws-response-invalid")
                    self.assertEqual(failure.exception.code, expected)
                    self.assertNotIn("canary", str(failure.exception))
                self.assertEqual(len(self.read()["calls"]), before + 1)
        timeout = owner.CLI.subprocess.TimeoutExpired("private-canary", 35, output="private-canary", stderr="private-canary")
        with patch.object(owner.CLI.subprocess, "run", side_effect=timeout):
            with self.assertRaises(owner.SessionProviderFailure) as failure:
                self.transport("cloudformation", "describe-stacks", StackName=self.stack)
            self.assertEqual(failure.exception.code, "aws-command-timeout")
            self.assertNotIn("canary", str(failure.exception))
        self.initialize()
        calls = self.read()["calls"]
        self.assertTrue(all(["ecr", operation] in calls for operation in
                            ("describe-repositories", "batch-get-image", "describe-image-scan-findings")))
        self.assertEqual(self.custody.requests, [])
        scan = next(row for row in self.read()["argv"] if row[:2] == ["ecr", "describe-image-scan-findings"])
        self.assertEqual(scan[scan.index("--page-size") + 1], "1")
        self.assertNotIn("--max-items", scan)

    def test_concrete_transport_foundation_failure_retains_its_finite_cause(self):
        for fault, code in (("AccessDenied", "aws-access-denied"), ("ExpiredToken", "aws-credentials-expired"), ("malformed", "aws-response-invalid")):
            state = self.read(); state["transport_fault"] = fault; self.write(state)
            self.assertEqual(self.failed(self.initialize, "foundation-unconfirmed"),
                             "environment-session-operation-foundation-unconfirmed:" + code)
            self.assertEqual(self.read()["history"], [])
            self.assertEqual(self.read()["submissions"], [])

    def test_lost_original_custody_retention_denies_current_attempt_and_rebinds_positive_read(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        foundation = dict(self.plan["stack_names"])["foundation"]
        inputs = {"stack": foundation, "template_reference": dict(self.plan["stack_templates"])[foundation]}
        self.fault("lost-put")
        self.failed(lambda: self.adapter.prepare("creation", **inputs), "retention-unconfirmed")
        observed = self.read(); document = json.loads(observed["raw"])
        self.assertIn(self.stack, document["creation_evidence"])
        self.assertNotIn("creation:" + foundation, document["resolved"])
        self.assertEqual(len(observed["submissions"]), 2)
        proof = deepcopy(document["creation_evidence"][self.stack])
        self.adapter.prepare("creation", **inputs)
        self.assertEqual(json.loads(self.read()["raw"])["creation_evidence"][self.stack], proof)
        self.assertEqual(len(self.read()["submissions"]), 3)
        before = self.read()
        with patch.object(self.adapter, "_resolve", side_effect=AssertionError("retained request only observes")):
            self.adapter.prepare("creation", **inputs)
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_partial_uncertain_creation_keeps_space_for_maximum_supported_delete_identity(self):
        self.initialize(); self.fault("lost-create-change-set")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "submission-uncertain")
        document = json.loads(self.read()["raw"])
        self.assertEqual(document["creation_evidence"], {})
        prefix = "arn:aws:cloudformation:" + self.records.region + ":" + self.records.account + ":stack/" + self.stack + "/"
        identity = prefix + "x" * (2048 - len(prefix))
        self.assertTrue(self.records._stack_id(self.stack, identity))
        self.assertFalse(self.records._stack_id(self.stack, identity + "x"))
        state = self.read()
        change = next(iter(state["changes"].values()))
        previous = change["StackId"]
        change["StackId"] = identity
        state["stacks"][identity] = {**state["stacks"].pop(previous), "StackId": identity}
        self.write(state)
        self.adapter.seal(); self.now = 8200
        # Exact original provider change/template/resources establish custody;
        # this unexecuted placeholder has no successful functionality evidence.
        self.adapter.delete(stack=self.stack, stack_id=identity)
        final = json.loads(self.read()["raw"])
        self.assertEqual(final["incarnations"][self.stack], identity)
        self.assertEqual(final["operations"]["delete:" + self.stack + ":delete"]["request"]["stack_id"], identity)
        self.assertLessEqual(self.records._completion_size(final), OWNER.RECORDS.LIMIT)
        self.assertEqual(final["creation_evidence"], {})
        self.assertNotIn("prepare-discard:" + self.stack, final["resolved"])

    def test_original_custody_denies_foreign_template_parameters_resources_and_incomplete_reads(self):
        self.initialize(); self.fault("lost-create-change-set")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "submission-uncertain")
        self.adapter.seal()
        valid = self.read(); name = self.stack + "-session-create"; identifier = self.delete_inputs()["stack_id"]
        mutations = [
            (lambda s: s["changes"][name].update(Description="private-canary"), "output-creation-mismatch"),
            (lambda s: s["changes"][name].update(ChangeSetId="private-canary"), "output-creation-mismatch"),
            (lambda s: s["changes"][name].update(StackId=identifier[:-1] + "6"), "cleanup-observation-unavailable:aws-parameter-invalid"),
            (lambda s: s["changes"][name].update(fixture_template='{"private-canary":true}'), "custody-template-mismatch"),
            (lambda s: s["changes"][name].update(Parameters=[]), "output-creation-mismatch"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"].update(ResourceType="AWS::S3::Bucket"), "custody-resource-mismatch"),
            (lambda s: s["changes"][name]["Changes"].append(deepcopy(s["changes"][name]["Changes"][0])), "custody-resource-mismatch"),
            (lambda s: s["changes"][name].update(ImportExistingResources=True), "output-creation-mismatch"),
            (lambda s: s["changes"][name].update(IncludeNestedStacks=True), "output-creation-mismatch"),
            (lambda s: s.setdefault("resources", {}).update({identifier: [{"LogicalResourceId": "private-canary", "ResourceType": "AWS::S3::Bucket"}]}), "custody-resource-mismatch"),
            (lambda s: s.update(events_next_token="private-canary"), "aws-response-invalid"),
        ]
        for mutate, reason in mutations:
            state = deepcopy(valid); mutate(state); self.write(state)
            self.failed(lambda: self.adapter.delete(**self.delete_inputs()), reason)
            self.assertEqual(self.read()["submissions"], valid["submissions"])
            self.assertEqual(json.loads(self.read()["raw"])["state"], "sealed")
        self.write(valid)
        self.adapter.delete(**self.delete_inputs())
        document = json.loads(self.read()["raw"])
        self.assertTrue(document["creation_custody"])
        self.assertFalse(document["creation_evidence"])

    def test_terminal_partial_creation_has_custody_without_successful_output_or_absence(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs)
        state = self.read(); state.update(execution_status="CREATE_FAILED", partial_resources=1); self.write(state)
        self.assertEqual(self.adapter.execute("creation", **self.inputs)["status"], "failed")
        identifier = self.delete_inputs()["stack_id"]
        state = self.read()
        foundation = dict(self.plan["stack_names"])["foundation"]
        self.assertEqual(self.failed(lambda: self.adapter.prepare("creation", stack=foundation,
            template_reference=dict(self.plan["stack_templates"])[foundation]), "output-creation-unconfirmed"),
            "environment-session-operation-output-creation-unconfirmed")
        self.assertEqual(self.read()["submissions"], state["submissions"])
        self.adapter.seal()
        before = self.read()
        self.assertEqual(self.failed(lambda: self.adapter.prepare("prepare-discard", **self.inputs), "output-creation-unconfirmed"),
                         "environment-session-operation-output-creation-unconfirmed")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.adapter.delete(**self.delete_inputs())
        document = json.loads(self.read()["raw"])
        self.assertEqual(document["creation_evidence"], {})
        self.assertEqual(document["operation_outcomes"]["creation:" + self.stack + ":execute"]["status"], "CREATE_FAILED")
        self.assertEqual(document["state"], "deleting")
        slots = document["physical_resources"][self.stack]["slots"]
        self.assertEqual(sum(bool(OWNER.RECORDS.SHA.fullmatch(slot)) for slot in slots), 1)
        self.assertIn("unknown", slots)
        self.assertNotIn("never-allocated", slots)
        self.confirm_fixture_delete(self.stack); before = self.read()
        result = self.adapter.observe_resource_cleanup(stack=self.stack, stack_id=identifier)
        unknown = [row for row in result["resources"] if row.get("reason") == "environment-session-operation-physical-allocation-unknown"]
        self.assertEqual(len(unknown), slots.count("unknown"))
        self.assertTrue(all(row["status"] == "unknown" for row in unknown))
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_physical_discovery_is_monotonic_bounded_and_unchanged_reads_do_not_write(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        identifier = self.delete_inputs()["stack_id"]
        state = self.read(); rows = deepcopy(state["resources"][identifier])
        state["resources"][identifier] = [rows[0], {**rows[1], "PhysicalResourceId": ""}]
        self.write(state); self.adapter.seal()
        self.adapter._cleanup_readiness(self.stack, identifier)
        first = self.read(); document = json.loads(first["raw"])
        slots = document["physical_resources"][self.stack]["slots"]
        self.assertEqual(sum(bool(OWNER.RECORDS.SHA.fullmatch(slot)) for slot in slots), 1)
        self.assertNotIn("never-allocated", slots)
        maximum = self.records._completion_size(document)
        self.adapter._cleanup_readiness(self.stack, identifier)
        self.assertEqual(self.read()["history"], first["history"])
        state = self.read(); rows[1]["PhysicalResourceId"] = "private-canary-" + "x" * 70000
        state["resources"][identifier] = rows[:2]; self.write(state)
        self.assertEqual(self.failed(lambda: self.adapter.reconstruct_physical(stack=self.stack, stack_id=identifier),
            "physical-observation-unretained"), "environment-session-operation-physical-observation-unretained")
        self.adapter._cleanup_readiness(self.stack, identifier)
        discovered = self.read(); updated = json.loads(discovered["raw"])
        self.assertEqual(self.records._completion_size(updated), maximum)
        self.assertEqual(sum(bool(OWNER.RECORDS.SHA.fullmatch(slot)) for slot in updated["physical_resources"][self.stack]["slots"]), 2)
        self.assertNotIn("private-canary", discovered["raw"])
        state = self.read(); state["resources"][identifier] = []; self.write(state)
        self.adapter._cleanup_readiness(self.stack, identifier)
        self.assertEqual(self.read()["history"], discovered["history"])
        state = self.read(); state["resources"][identifier] = [{**rows[0], "PhysicalResourceId": "private-canary-replacement"}]
        self.write(state)
        self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "session-physical-identity-mismatch"),
                         "session-physical-identity-mismatch")
        self.assertEqual(self.read()["history"], discovered["history"])
        self.assertEqual(self.read()["submissions"], discovered["submissions"])
        state = self.read(); state["resources"][identifier] = rows[:2]; self.write(state)
        self.adapter.delete(**self.delete_inputs())
        self.assertLessEqual(len(self.read()["raw"].encode()), OWNER.RECORDS.LIMIT)

    def test_never_allocated_requires_sealed_unexecuted_original_custody(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs)
        identifier = self.delete_inputs()["stack_id"]
        document = self.records.observe_existing()["document"]
        _, custody, _, _, outcomes, physical = self.adapter._inspect_stack(self.stack, document)
        self.assertTrue(all(slot == "unknown" for slot in physical["slots"]))
        physical["slots"] = ["never-allocated"] * len(physical["slots"])
        before = self.read()
        self.assertEqual(self.failed(lambda: self.records.retain_ownership(self.stack, identifier,
            custody=custody, outcomes=outcomes, physical=physical), "session-physical-invalid"), "session-physical-invalid")
        self.assertEqual(self.read()["history"], before["history"])
        self.adapter.seal(); valid = self.read()
        logical, kind = self.adapter._resource_index(self.stack)[0]
        state = deepcopy(valid); state["resources"] = {identifier: [{"LogicalResourceId": logical,
            "ResourceType": kind, "PhysicalResourceId": "private-canary-allocated"}]}; self.write(state)
        self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "physical-allocation-contradiction"),
                         "environment-session-operation-physical-allocation-contradiction")
        self.assertEqual(self.read()["history"], valid["history"])
        self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid); self.adapter.delete(**self.delete_inputs())
        document = json.loads(self.read()["raw"])
        self.assertTrue(all(slot == "never-allocated" for slot in document["physical_resources"][self.stack]["slots"]))
        self.assertFalse(document["creation_evidence"])
        result = self.adapter.reconstruct_physical(stack=self.stack, stack_id=identifier)
        self.assertTrue(all(row["allocation"] == "never-allocated" and row["physical_id"] is None for row in result["resources"]))
        self.confirm_fixture_delete(self.stack); before = self.read()
        result = self.adapter.observe_resource_cleanup(stack=self.stack, stack_id=identifier)
        self.assertTrue(all(row["status"] == "never-allocated" and "reason" not in row for row in result["resources"]))
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertTrue(all(row[0] in ("s3api", "cloudformation") for row in self.read()["calls"][len(before["calls"]):]))

    def test_physical_reconstruction_uses_original_lineage_without_old_root_status_or_writes(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        self.adapter.seal(); self.adapter.delete(**self.delete_inputs())
        identifier = self.delete_inputs()["stack_id"]
        state = self.read(); state["stacks"] = {}; state["changes"] = {}; state["events"] = {}; self.write(state)
        valid = self.read(); preflights = len(self.preflights)
        with patch.object(self.adapter, "_inspect_stack", side_effect=AssertionError("old root status is not required")):
            result = self.adapter.reconstruct_physical(stack=self.stack, stack_id=identifier)
        self.assertEqual([(row["logical_id"], row["resource_type"]) for row in result["resources"]], list(self.adapter._resource_index(self.stack)))
        self.assertTrue(all(row["allocation"] == "allocated" and row["physical_id"] == "fixture-" + row["logical_id"] for row in result["resources"]))
        result["resources"][0]["physical_id"] = "private-canary"
        self.assertEqual(self.read()["history"], valid["history"])
        self.assertEqual(len(self.preflights), preflights)
        mutations = [
            (lambda s: s["resources"][identifier][0].update(PhysicalResourceId="private-canary"), "physical-identity-mismatch"),
            (lambda s: s["resources"][identifier][0].update(PhysicalResourceId=""), "physical-lineage-unavailable"),
            (lambda s: s["resources"][identifier][0].update(PhysicalResourceId=[]), "physical-identity-invalid"),
            (lambda s: s["resources"].update({identifier: []}), "physical-lineage-unavailable"),
            (lambda s: s["resources"][identifier][0].update(LogicalResourceId=["private-canary"]), "custody-resource-mismatch"),
            (lambda s: s["resources"][identifier][0].update(ResourceType="private-canary"), "custody-resource-mismatch"),
            (lambda s: s["resources"][identifier].append(deepcopy(s["resources"][identifier][0])), "custody-resource-mismatch"),
            (lambda s: s.update(resources_next_token="private-canary"), "physical-observation-unavailable:aws-response-invalid"),
            (lambda s: s.update(resources_fault="AccessDenied"), "physical-observation-unavailable:aws-access-denied"),
            (lambda s: s.update(resources_fault="ValidationError"), "physical-observation-unavailable:aws-parameter-invalid"),
        ]
        for mutate, reason in mutations:
            with self.subTest(reason=reason):
                state = deepcopy(valid); mutate(state); self.write(state)
                self.assertEqual(self.failed(lambda: self.adapter.reconstruct_physical(stack=self.stack, stack_id=identifier), reason),
                                 "environment-session-operation-" + reason)
                self.assertEqual(self.read()["history"], valid["history"])
                self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid)
        for extra in ({"physical_id": "private-canary"}, {"RoleARN": "private-canary"}):
            self.assertEqual(self.failed(lambda: self.adapter.reconstruct_physical(stack=self.stack, stack_id=identifier, **extra),
                "operation-inputs-invalid"), "environment-session-operation-operation-inputs-invalid")
        self.assertEqual(self.read()["calls"], valid["calls"])

    def test_physical_retention_loss_conflict_and_late_discovery_never_replay_delete(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        self.adapter.seal(); valid = self.read(); identifier = self.delete_inputs()["stack_id"]
        for fault, reason in (("PreconditionFailed", "session-record-conflict"), ("lost-put", "session-retention-unconfirmed:aws-response-invalid")):
            self.write(valid); self.fault(fault)
            self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), reason), reason)
            self.assertEqual(self.read()["submissions"], valid["submissions"])
            self.assertNotIn("delete:" + self.stack + ":delete", json.loads(self.read()["raw"])["operations"])
        # An independently positive read may use the retained manifest after a lost
        # acknowledgement; neither loss nor a later discovery authorizes replay.
        retained = self.read(); self.assertIn(self.stack, json.loads(retained["raw"])["physical_resources"])
        self.adapter.delete(**self.delete_inputs())
        self.assertEqual(len(self.read()["submissions"]), len(valid["submissions"]) + 1)
        self.write(valid)
        state = self.read(); rows = deepcopy(state["resources"][identifier]); state["resources"][identifier] = rows[:1]; self.write(state)
        readiness = self.adapter._cleanup_readiness
        count = []
        def discover(stack, stack_id):
            count.append(True)
            if len(count) == 2:
                state = self.read(); state["resources"][identifier] = rows[:2]; self.write(state)
            return readiness(stack, stack_id)
        with patch.object(self.adapter, "_cleanup_readiness", side_effect=discover):
            self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "reconciliation-changed"),
                             "environment-session-operation-reconciliation-changed")
        final = self.read(); document = json.loads(final["raw"])
        request = deepcopy(document["operations"]["delete:" + self.stack + ":delete"])
        self.assertEqual(final["submissions"], valid["submissions"])
        self.assertEqual(sum(bool(OWNER.RECORDS.SHA.fullmatch(slot)) for slot in document["physical_resources"][self.stack]["slots"]), 2)
        cold = OWNER.SessionOperations(self.plan, self.make_records(), source_root=self.root / "missing-source",
            approved_max_duration_seconds=7200, provider=self.provider, preflight=lambda context: self.fail("retained intent cannot re-admit"))
        with patch.object(cold, "_cleanup_readiness", side_effect=AssertionError("retained intent only observes")):
            cold.delete(**self.delete_inputs())
        self.assertEqual(self.read()["history"], final["history"])
        self.assertEqual(self.read()["submissions"], final["submissions"])
        self.assertEqual(json.loads(self.read()["raw"])["operations"]["delete:" + self.stack + ":delete"], request)

    def test_physical_source_shape_metadata_and_reservation_fingerprint_are_checked(self):
        self.initialize(); initialized = self.read()
        for field, value in (("resource_count", 1), ("resources_sha256", "f" * 64)):
            state = deepcopy(initialized); document = json.loads(state["raw"])
            document["base"]["cleanup_shapes"][self.stack][field] = value
            document["base_sha256"] = OWNER._digest(document["base"])
            state["raw"] = json.dumps(document); self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "inputs-cleanup-shape-mismatch"),
                             "environment-session-operation-inputs-cleanup-shape-mismatch")
            self.assertEqual(self.read()["history"], initialized["history"])
            self.assertEqual(self.read()["submissions"], [])
        self.write(initialized)
        self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs); self.adapter.seal()
        identifier = self.delete_inputs()["stack_id"]
        self.adapter._cleanup_readiness(self.stack, identifier)
        valid = self.read(); document = json.loads(valid["raw"])
        physical = document["physical_resources"][self.stack]
        for changed, reason in (({**physical, "stack_id_sha256": "f" * 64}, "session-physical-invalid"),
                ({**physical, "relationships": ["f" * 64]}, "session-physical-invalid"),
                ({**physical, "databases": ["f" * 64]}, "session-physical-invalid"),
                ({**physical, "namespaces": ["Z" * 33]}, "session-physical-invalid"),
                ({**physical, "slots": physical["slots"][:-1]}, "session-physical-invalid"),
                ({**physical, "slots": ["private-canary"] * len(physical["slots"])}, "session-physical-invalid"),
                ({**physical, "slots": ["never-allocated"] * len(physical["slots"])}, "session-physical-invalid"),
                ({**physical, "observation_sha256": "f" * 65}, "session-physical-invalid"),
                ({**physical, "observed_at": "2026-11-27T00:00:00.0000000+00:00"}, "session-reservation-time-invalid")):
            state = deepcopy(valid); edited = json.loads(state["raw"])
            edited["physical_resources"][self.stack] = changed; state["raw"] = json.dumps(edited); self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), reason), reason)
            self.assertEqual(self.read()["history"], valid["history"])
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid)
        request = OWNER.RECORDS.operation_request(document, "delete", self.stack,
            OWNER._digest(self.adapter._delete_arguments(document, identifier)), stack_id=identifier)
        for missing in (False, True):
            state = deepcopy(valid); current = json.loads(state["raw"])
            if missing:
                current["physical_resources"].clear()
            state["raw"] = json.dumps(current); self.write(state)
            store = OWNER._Reservations(self.records.storage("delete",
                reconciled_operations_sha256=OWNER.RECORDS.operations_sha256(current),
                physical_manifest_sha256="f" * 64), request)
            self.assertEqual(self.failed(lambda: store.reserve("delete", request), "session-physical-retention-required"),
                             "environment-session-operation-session-physical-retention-required")
            self.assertEqual(self.read()["history"], valid["history"])
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid)

    def test_native_cleanup_reads_complete_graph_without_confusing_inactive_or_scheduled_deletion(self):
        facts = self.native_cleanup_fixture(whole_graph=True)
        before = self.read(); preflights = len(self.preflights)
        reports = {}
        for stack in self.plan["stack_order"]:
            result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            self.assertEqual(set(result), {"resources"})
            for row in result["resources"]:
                fact = facts[stack, row["logical_id"]]; reports[stack, row["logical_id"]] = row
                expected = "inactive" if fact["kind"] == "AWS::ECS::TaskDefinition" else "present"
                self.assertEqual(row["status"], expected)
                self.assertEqual(set(row), {"logical_id", "resource_type", "status", *(["artifacts"] if fact["kind"] in ("AWS::RDS::DBInstance", "AWS::ServiceDiscovery::PrivateDnsNamespace") else [])})
                self.assertNotIn(fact["identity"], json.dumps(result))
            self.assertNotIn("private-canary", json.dumps(result))
        self.assertEqual(len(reports), 120)
        self.assertEqual(len({row["resource_type"] for row in reports.values()}), 18)
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(len(self.preflights), preflights)
        positive = self.read(); state = deepcopy(positive)
        for fact in facts.values():
            if fact["call"]:
                state["native_replies"][json.dumps(fact["call"], sort_keys=True, separators=(",", ":"))] = fact["missing"]
        self.write(state)
        for stack in self.plan["stack_order"]:
            result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            for row in result["resources"]:
                fact = facts[stack, row["logical_id"]]
                self.assertEqual(row["status"], "unknown" if fact["kind"] == "AWS::ECS::TaskDefinition" else "absent")
                if fact["kind"] == "AWS::ECS::TaskDefinition":
                    self.assertEqual(row["reason"], "environment-session-operation-cleanup-resource-observation-unavailable:aws-command-failed")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        # No completion, task quiescence, generated-log or database-backup claim.
        selected = {fact["kind"]: (key, fact) for key, fact in facts.items() if fact["call"]}
        variants = [
            ("AWS::ECS::Cluster", lambda r: r["clusters"][0].update(clusterArn="private-canary")),
            ("AWS::ECS::Cluster", lambda r: r["clusters"][0].update(clusterName="private-canary")),
            ("AWS::ECS::Cluster", lambda r: r.update(clusters=[], failures=[{"arn": "private-canary", "reason": "MISSING"}])),
            ("AWS::ECS::TaskDefinition", lambda r: r["taskDefinition"].update(taskDefinitionArn="private-canary")),
            ("AWS::SecretsManager::Secret", lambda r: r.update(ARN="private-canary")),
            ("AWS::ServiceDiscovery::Service", lambda r: r["Service"].update(Id="private-canary")),
            ("AWS::Logs::LogGroup", lambda r: r["logGroups"][0].update(logGroupName="private-canary")),
            ("AWS::RDS::DBInstance", lambda r: r["DBInstances"][0].update(DBInstanceIdentifier="private-canary")),
            ("AWS::EC2::SubnetRouteTableAssociation", lambda r: r["RouteTables"][0]["Associations"][0].update(RouteTableAssociationId="private-canary")),
        ]
        for field in ("runningTasksCount", "pendingTasksCount", "activeServicesCount", "registeredContainerInstancesCount"):
            variants.append(("AWS::ECS::Cluster", lambda r, field=field: r["clusters"][0].update(status="INACTIVE", **{field: 1})))
        for value in (-1, True, "private-canary"):
            variants.append(("AWS::ECS::Cluster", lambda r, value=value: r["clusters"][0].update(runningTasksCount=value)))
        for kind, mutate in variants:
            (stack, logical), fact = selected[kind]
            state = deepcopy(positive); key = json.dumps(fact["call"], sort_keys=True, separators=(",", ":"))
            mutate(state["native_replies"][key]["response"]); self.write(state)
            result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            row = next(row for row in result["resources"] if row["logical_id"] == logical)
            self.assertEqual(row["status"], "unknown")
            self.assertEqual(row["reason"], "environment-session-operation-cleanup-resource-response-invalid")
            self.assertNotIn("private-canary", json.dumps(result))
            self.assertEqual(self.read()["history"], positive["history"])
            self.assertEqual(self.read()["submissions"], positive["submissions"])
        for kind, reply, reason in (
                ("AWS::RDS::DBSubnetGroup", {"response": {"DBSubnetGroups": [], "Marker": "private-canary"}}, "aws-response-invalid"),
                ("AWS::EC2::SubnetRouteTableAssociation", {"error": "InvalidRouteTableID.NotFound"}, "aws-resource-missing")):
            (stack, logical), fact = selected[kind]
            state = deepcopy(positive); state["native_replies"][json.dumps(fact["call"], sort_keys=True, separators=(",", ":"))] = reply; self.write(state)
            result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            row = next(row for row in result["resources"] if row["logical_id"] == logical)
            self.assertEqual(row["status"], "unknown")
            self.assertEqual(row["reason"], "environment-session-operation-cleanup-resource-observation-unavailable:" + reason)
        (stack, logical), fact = selected["AWS::ECS::Cluster"]
        state = deepcopy(positive); reply = state["native_replies"][json.dumps(fact["call"], sort_keys=True, separators=(",", ":"))]["response"]
        reply["clusters"][0].update(status="INACTIVE", runningTasksCount=0, pendingTasksCount=0, activeServicesCount=0, registeredContainerInstancesCount=0)
        self.write(state)
        result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
        self.assertEqual(next(row for row in result["resources"] if row["logical_id"] == logical)["status"], "inactive")
        self.assertEqual(self.read()["history"], positive["history"])
        self.assertEqual(self.read()["submissions"], positive["submissions"])

    def test_late_identity_retention_after_delete_is_monotonic_and_never_replays(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        identifier = self.delete_inputs()["stack_id"]
        self.assertEqual(self.failed(lambda: self.adapter.retain_physical_observation(stack=self.stack, stack_id=identifier), "admission-open"),
                         "environment-session-operation-admission-open")
        state = self.read(); original = deepcopy(state["resources"][identifier]); state["resources"][identifier] = original[:1]; self.write(state)
        self.adapter.seal(); self.adapter.delete(**self.delete_inputs()); self.confirm_fixture_delete(self.stack)
        self.assertEqual(self.adapter.reconcile_operation(kind="delete", stack=self.stack, phase="delete")["status"], "succeeded")
        before = self.read(); intent = deepcopy(json.loads(before["raw"])["operations"])
        state = self.read(); state["resources"][identifier] = original; self.write(state)
        pending = self.read()
        for fault, reason in (("PreconditionFailed", "session-record-conflict"), ("lost-put", "session-retention-unconfirmed:aws-response-invalid")):
            self.write(pending); self.fault(fault)
            self.assertEqual(self.failed(lambda: self.adapter.retain_physical_observation(stack=self.stack, stack_id=identifier), reason), reason)
            self.assertEqual(self.read()["submissions"], before["submissions"])
        retained = self.read()
        cold = OWNER.SessionOperations(self.plan, self.make_records(), source_root=self.root / "missing-source",
            approved_max_duration_seconds=7200, provider=self.provider, preflight=lambda _: self.fail("no new admission"))
        with patch.object(OWNER, "_module", side_effect=AssertionError("no imports")):
            cold.retain_physical_observation(stack=self.stack, stack_id=identifier)
            cold.delete(**self.delete_inputs())
        self.assertEqual(self.read()["history"], retained["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(json.loads(self.read()["raw"])["operations"], intent)
        result = cold.reconstruct_physical(stack=self.stack, stack_id=identifier)
        self.assertTrue(all(row["allocation"] == "allocated" for row in result["resources"]))
        state = self.read(); state["resources"][identifier][0]["PhysicalResourceId"] = "private-canary"; self.write(state)
        self.assertEqual(self.failed(lambda: cold.retain_physical_observation(stack=self.stack, stack_id=identifier), "session-physical-identity-mismatch"),
                         "session-physical-identity-mismatch")
        self.assertEqual(self.read()["history"], retained["history"])

    def test_allocated_native_lineage_is_required_but_unproved_relationship_stays_unknown(self):
        facts = self.native_cleanup_fixture(whole_graph=True, cleanup=False)
        self.adapter.seal(); valid = self.read()
        target = self.plan["stack_order"][-1]
        selected = {fact["kind"]: (key, fact) for key, fact in facts.items() if fact["call"]}
        for kind, mutate, reason in (
                ("AWS::RDS::DBInstance", lambda r: r["DBInstances"][0].pop("DbiResourceId"), "cleanup-database-lineage-unconfirmed"),
                ("AWS::RDS::DBInstance", lambda r: r["DBInstances"][0].update(DbiResourceId="private-canary"), "cleanup-database-lineage-unconfirmed"),
                ("AWS::ServiceDiscovery::PrivateDnsNamespace", lambda r: r["Namespace"].update(Name="private-canary"), "cleanup-namespace-lineage-unconfirmed"),
                ("AWS::ServiceDiscovery::PrivateDnsNamespace", lambda r: r["Namespace"]["Properties"]["DnsProperties"].update(HostedZoneId="Z" * 33), "cleanup-namespace-lineage-unconfirmed")):
            _, fact = selected[kind]; state = deepcopy(valid)
            mutate(state["native_replies"][json.dumps(fact["call"], sort_keys=True, separators=(",", ":"))]["response"]); self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs(target)), reason), "environment-session-operation-" + reason)
            self.assertEqual(self.read()["submissions"], valid["submissions"])
            self.assertFalse(any(key.startswith("delete:") for key in json.loads(self.read()["raw"])["operations"]))
        # Corrupt only correspondence evidence, not physical stack ownership.
        state = deepcopy(valid)
        for fact in facts.values():
            if fact["kind"] == "AWS::EC2::SecurityGroup":
                key = json.dumps(fact["call"], sort_keys=True, separators=(",", ":"))
                state["native_replies"][key] = {"response": {"SecurityGroups": [{"GroupId": fact["identity"], "IpPermissions": [], "IpPermissionsEgress": []}]}}
        self.write(state)
        for stack in reversed(self.plan["stack_order"]):
            self.adapter.delete(**self.delete_inputs(stack)); self.confirm_fixture_delete(stack)
        final = self.read(); document = json.loads(final["raw"])
        self.assertTrue(any("unknown" in row["relationships"] for row in document["physical_resources"].values()))
        self.assertTrue(all(value != "unknown" for row in document["physical_resources"].values() for key in ("databases", "namespaces") for value in row[key]))
        for stack in self.plan["stack_order"]:
            report = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            for row in report["resources"]:
                if row["resource_type"] in ("AWS::EC2::SecurityGroupIngress", "AWS::EC2::SecurityGroupEgress"):
                    self.assertEqual(row["status"], "unknown")
                    self.assertEqual(row["reason"], "environment-session-operation-cleanup-relationship-unretained")
        self.assertEqual(self.read()["history"], final["history"])
        self.assertEqual(self.read()["submissions"], final["submissions"])
        for stack, physical in document["physical_resources"].items():
            for key in ("relationships", "databases", "namespaces"):
                if physical[key] and physical[key][0] != "unknown":
                    changed = deepcopy(physical); changed[key][0] = "ZOTHER" if key == "namespaces" else "f" * 64
                    self.assertEqual(self.failed(lambda: self.records.retain_ownership(stack, document["incarnations"][stack], physical=changed), "session-physical-identity-mismatch"), "session-physical-identity-mismatch")
        self.assertEqual(self.read()["history"], final["history"])

    def test_native_artifacts_use_immutable_lineage_and_exact_zone_without_false_absence(self):
        facts = self.native_cleanup_fixture(whole_graph=True)
        (stack, logical), fact = next((key, fact) for key, fact in facts.items() if fact["kind"] == "AWS::RDS::DBInstance")
        lineage = fact["present"]["response"]["DBInstances"][0]["DbiResourceId"]
        context = self.records.region + ":" + self.records.account
        call = ["rds", "describe-db-snapshots", {"SnapshotType": "manual", "IncludePublic": False, "IncludeShared": False}]
        key = json.dumps(call, sort_keys=True, separators=(",", ":")); before = self.read()
        matching = {"DBSnapshotArn": "arn:aws:rds:" + context + ":snapshot:private-canary", "DbiResourceId": lineage, "DBInstanceIdentifier": "different-name"}
        other = {"DBSnapshotArn": "arn:aws:rds:" + context + ":snapshot:other", "DbiResourceId": "db-OTHER", "DBInstanceIdentifier": fact["identity"]}
        def artifact():
            report = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            self.assertNotIn("private-canary", json.dumps(report))
            return next(row for row in report["resources"] if row["logical_id"] == logical)["artifacts"]
        state = deepcopy(before); state["native_replies"][key] = {"response": {"DBSnapshots": [matching, other]}}; self.write(state)
        observations = artifact()
        self.assertEqual(observations[0], {"kind": "manual-snapshots", "status": "present", "count": 1})
        self.assertEqual(observations[-1], {"kind": "cross-region-backups", "status": "unknown"})
        for reply, reason in (({"response": {"DBSnapshots": [matching, matching]}}, "environment-session-operation-cleanup-resource-response-invalid"),
                ({"response": {"DBSnapshots": [], "Marker": "private-canary"}}, "environment-session-operation-cleanup-resource-observation-unavailable:aws-response-invalid"),
                ({"error": "DBSnapshotNotFound"}, "environment-session-operation-cleanup-resource-observation-unavailable:aws-resource-missing")):
            state = deepcopy(before); state["native_replies"][key] = reply; self.write(state)
            self.assertEqual(artifact(), [{"kind": "database-artifacts", "status": "unknown", "reason": reason}])
        (stack, logical), fact = next((key, fact) for key, fact in facts.items() if fact["kind"] == "AWS::ServiceDiscovery::PrivateDnsNamespace")
        zone = fact["present"]["response"]["Namespace"]["Properties"]["DnsProperties"]["HostedZoneId"]
        key = json.dumps(["route53", "get-hosted-zone", {"Id": zone}], sort_keys=True, separators=(",", ":"))
        for reply, expected in (({"error": "NoSuchHostedZone"}, {"kind": "hosted-zone", "status": "absent"}),
                ({"response": {"HostedZone": {"Id": "private-canary", "Config": {"PrivateZone": True}}}},
                 {"kind": "hosted-zone", "status": "unknown", "reason": "environment-session-operation-cleanup-resource-response-invalid"})):
            state = deepcopy(before); state["native_replies"][key] = reply; self.write(state)
            self.assertEqual(artifact(), [expected])
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_cold_recovery_uses_positive_record_and_original_policy_without_writes(self):
        document = deepcopy(self.session_document)
        document["environment_lifecycle"]["max_duration_seconds"] = 9000
        plan = self.preparation.load_session_plan(ROOT, document["target"], document["scope"], document, 1000, 8000)
        self.select_plan(plan); self.initialize(); self.adapter.seal(); self.now = 8201
        before = self.read(); observed = self.records.observe_existing()
        self.assertEqual(observed["document"]["base"]["lifecycle_max_duration_seconds"], 9000)
        self.assertEqual(observed["document"]["base"]["execution_roles"], plan["execution_roles"])
        with patch.object(self.preparation, "load_session_plan", side_effect=AssertionError("no fresh admission")), \
             patch.object(OWNER, "_module", side_effect=AssertionError("no acquisition")):
            recovered = self.preparation.recover_session_plan(ROOT, observed["document"], observed["observed_at"], 8000)
            cold = OWNER.SessionOperations(recovered, self.make_records(), source_root=ROOT,
                approved_max_duration_seconds=8000, provider=self.provider, preflight=self.preflight)
            self.assertEqual(cold._plan_sha256, self.adapter._plan_sha256)
            self.assertEqual(cold._base(observed["document"]), observed["document"]["base"])
            self.assertEqual(cold._roles, plan["execution_roles"])
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertTrue(all(call == ["s3api", "get-object"] for call in self.read()["calls"][len(before["calls"]):]))

    def test_phase_roles_are_source_bound_closed_and_retained_once(self):
        roles = self.plan["execution_roles"]
        variants = (None, {}, {**roles, "other": "private-canary"},
            {**roles, "creation": "private-canary"},
            {**roles, "cleanup": roles["creation"].replace("cfn-create", "CFN-CREATE")},
            {**roles, "creation": roles["creation"].replace(self.records.account, "0" * 12)},
            {**roles, "creation": roles["creation"].replace("role/s-", "role/path/s-")},
            {**roles, "creation": roles["creation"] + "x" * 65})
        for value in variants:
            self.assertEqual(self.failed(lambda: self.make_adapter({**self.plan, "execution_roles": value}, self.records,
                provider=self.provider, preflight=self.preflight), "execution-roles-invalid"),
                "environment-session-operation-execution-roles-invalid")
        self.assertEqual(self.read()["calls"], [])
        self.initialize(); before = self.read(); document = json.loads(before["raw"])
        self.assertEqual(document["schema"], "aws-temporary-session/v10")
        self.assertEqual(document["base"]["execution_roles"], roles)
        self.assertEqual(self.preflights[0]["source_plan"]["execution_roles"], roles)
        changed = {**roles, "cleanup": roles["cleanup"] + "-changed"}
        adapter = self.make_adapter({**self.plan, "execution_roles": changed}, self.records,
                                    provider=self.provider, preflight=self.preflight)
        self.assertEqual(self.failed(lambda: self.initialize(adapter), "execution-roles-mismatch"),
                         "environment-session-operation-execution-roles-mismatch")
        for value in (None, {**roles, "cleanup": roles["creation"].replace("cfn-create", "CFN-CREATE")}):
            edited = deepcopy(document)
            if value is None: edited["base"].pop("execution_roles")
            else: edited["base"]["execution_roles"] = value
            edited["base_sha256"] = OWNER._digest(edited["base"])
            state = deepcopy(before); state["raw"] = json.dumps(edited); self.write(state)
            self.assertEqual(self.failed(self.records.observe_existing, "session-record-shape-invalid"), "session-record-shape-invalid")
        self.write(before)
        edited = deepcopy(document); edited["schema"] = "aws-temporary-session/v8"
        state = deepcopy(before); state["raw"] = json.dumps(edited); self.write(state)
        self.assertEqual(self.failed(self.records.observe_existing, "session-record-invalid"), "session-record-invalid")
        self.write(before)
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], [])

    def test_phase_role_readback_distinguishes_stable_runtime_from_prepared_cleanup(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        self.adapter.runtime_view(stack=self.stack, required_outputs=[])
        created = self.read(); identifier = self.delete_inputs()["stack_id"]
        for value in (None, [], "private-canary", self.plan["execution_roles"]["cleanup"]):
            state = deepcopy(created)
            if value is None: state["stacks"][identifier].pop("RoleARN")
            else: state["stacks"][identifier]["RoleARN"] = value
            self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]),
                "execution-role-unconfirmed"), "environment-session-operation-execution-role-unconfirmed")
            self.assertEqual(self.read()["history"], created["history"])
            self.assertEqual(self.read()["submissions"], created["submissions"])
        for attach in (False, True):
            self.write(deepcopy(created)); self.adapter.seal()
            state = self.read(); state["attach_role_on_prepare"] = attach; self.write(state)
            self.adapter.prepare("prepare-discard", **self.inputs)
            prepared = self.read()
            self.assertEqual(prepared["stacks"][identifier]["RoleARN"], self.plan["execution_roles"]["cleanup" if attach else "creation"])
            self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]),
                "runtime-phase-unready"), "environment-session-operation-runtime-phase-unready")
            self.assertEqual(self.read()["history"], prepared["history"])
            if attach:
                state = deepcopy(prepared); state["stacks"][identifier]["RoleARN"] = "private-canary"; self.write(state)
                self.assertEqual(self.failed(lambda: self.adapter.execute("prepare-discard", **self.inputs), "execution-role-unconfirmed"),
                                 "environment-session-operation-execution-role-unconfirmed")
                self.assertEqual(self.read()["submissions"], prepared["submissions"])
                self.write(prepared)
                admitted = []
                key = "prepare-discard:" + self.stack + ":execute"
                def change_role_after_readiness(context):
                    self.preflight(context)
                    if context["action"] == "prepare-discard-execute":
                        state = self.read()
                        retained = json.loads(state["raw"])["operations"][key]
                        self.assertEqual(retained, context["reservation"])
                        self.assertEqual(state["stacks"][identifier]["RoleARN"], self.plan["execution_roles"]["cleanup"])
                        admitted.append(deepcopy(retained))
                        state["stacks"][identifier]["RoleARN"] = "private-canary"
                        self.write(state)
                guarded = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=change_role_after_readiness)
                self.assertEqual(self.failed(lambda: guarded.execute("prepare-discard", **self.inputs), "execution-role-unconfirmed"),
                                 "environment-session-operation-execution-role-unconfirmed")
                self.assertEqual(len(admitted), 1)
                blocked = self.read(); document = json.loads(blocked["raw"])
                self.assertEqual(document["operations"][key], admitted[0])
                self.assertEqual(document["operation_outcomes"][key]["request_sha256"], admitted[0]["request_sha256"])
                self.assertEqual(document["operation_outcomes"][key]["status"], "not-submitted")
                self.assertEqual(blocked["submissions"], prepared["submissions"])
                self.assertEqual(guarded.execute("prepare-discard", **self.inputs)["status"], "not-submitted")
                self.assertEqual(len(admitted), 1)
                self.assertEqual(self.read()["history"], blocked["history"])
                self.assertEqual(self.read()["submissions"], blocked["submissions"])
                self.assertEqual(json.loads(self.read()["raw"])["operations"][key], admitted[0])
                self.write(prepared)
            self.assertEqual(self.adapter.delete(**self.delete_inputs())["status"], "pending")
            self.assertEqual(self.read()["submissions"][-1][1]["RoleARN"], self.plan["execution_roles"]["cleanup"])
        # A reservation denied before submission cannot authorize an attached
        # cleanup role: only a positively observed prepared change can do so.
        self.write(deepcopy(created)); self.adapter.seal()
        denied = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: True)
        self.failed(lambda: denied.prepare("prepare-discard", **self.inputs), "preflight-unconfirmed")
        state = self.read(); state["stacks"][identifier]["RoleARN"] = self.plan["execution_roles"]["cleanup"]; self.write(state)
        self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "execution-role-unconfirmed"),
                         "environment-session-operation-execution-role-unconfirmed")
        self.assertEqual(self.read()["submissions"], state["submissions"])

    def test_phase_role_missing_failed_readback_preserves_owned_cleanup_not_runtime(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs)
        state = self.read(); state["execution_status"] = "CREATE_FAILED"; self.write(state)
        self.adapter.execute("creation", **self.inputs)
        state = self.read(); identifier = self.delete_inputs()["stack_id"]
        state["stacks"][identifier].pop("RoleARN"); self.write(state)
        self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]), "output-creation-unconfirmed")
        self.adapter.seal(); before = self.read()
        state = deepcopy(before); state["stacks"][identifier]["RoleARN"] = "private-canary"; self.write(state)
        self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "execution-role-unconfirmed"),
                         "environment-session-operation-execution-role-unconfirmed")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.write(before)
        self.assertEqual(self.adapter.delete(**self.delete_inputs())["status"], "pending")
        self.assertEqual(self.read()["submissions"][-1][1]["RoleARN"], self.plan["execution_roles"]["cleanup"])

    def test_retained_native_incarnation_cannot_change_and_late_database_identity_does_not_invent_lineage(self):
        self.create_graph(); self.adapter.seal(); original = self.read()
        stack = self.active_inputs["stack"]; identifier = self.delete_inputs(stack)["stack_id"]
        self.adapter._cleanup_readiness(stack, identifier)
        retained = self.read()
        database = next(row for row in retained["resources"][identifier] if row["ResourceType"] == "AWS::RDS::DBInstance")
        foundation = dict(self.plan["stack_names"])["foundation"]
        foundation_id = self.delete_inputs(foundation)["stack_id"]
        namespace = next(row for row in retained["resources"][foundation_id] if row["ResourceType"] == "AWS::ServiceDiscovery::PrivateDnsNamespace")
        database_call = ["rds", "describe-db-instances", {"DBInstanceIdentifier": database["PhysicalResourceId"]}]
        namespace_call = ["servicediscovery", "get-namespace", {"Id": namespace["PhysicalResourceId"]}]
        for call, mutate in ((database_call, lambda r: r["DBInstances"][0].update(DbiResourceId="db-OTHER")),
                             (namespace_call, lambda r: r["Namespace"]["Properties"]["DnsProperties"].update(HostedZoneId="ZOTHER"))):
            self.write(retained); response = self.provider(call[0], call[1], **call[2]); mutate(response)
            state = self.read(); state.setdefault("native_replies", {})[json.dumps(call, sort_keys=True, separators=(",", ":"))] = {"response": response}; self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs(stack)), "cleanup-native-lineage-mismatch"),
                             "environment-session-operation-cleanup-native-lineage-mismatch")
            self.assertEqual(self.read()["history"], retained["history"])
            self.assertEqual(self.read()["submissions"], retained["submissions"])
        # Positive physical identity may arrive after deletion, but no new DB
        # native observation may invent the original immutable backup lineage.
        state = deepcopy(original)
        next(row for row in state["resources"][identifier] if row["LogicalResourceId"] == database["LogicalResourceId"]).pop("PhysicalResourceId")
        self.write(state)
        for owner in reversed(self.plan["stack_order"]):
            self.adapter.delete(**self.delete_inputs(owner)); self.confirm_fixture_delete(owner)
        before = self.read(); intent = deepcopy(json.loads(before["raw"])["operations"])
        state = self.read()
        next(row for row in state["resources"][identifier] if row["LogicalResourceId"] == database["LogicalResourceId"])['PhysicalResourceId'] = database["PhysicalResourceId"]
        self.write(state)
        self.adapter.retain_physical_observation(stack=stack, stack_id=identifier)
        document = json.loads(self.read()["raw"])
        self.assertEqual(document["physical_resources"][stack]["databases"], ["unknown"])
        self.assertEqual(document["operations"], intent)
        final = self.read()
        result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=identifier)
        row = next(row for row in result["resources"] if row["logical_id"] == database["LogicalResourceId"])
        self.assertEqual(row["artifacts"], [{"kind": "database-artifacts", "status": "unknown", "reason": "environment-session-operation-cleanup-artifact-lineage-unconfirmed"}])
        self.assertEqual(self.read()["history"], final["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        resources = json.loads(dict(self.plan["projected_templates"])[self.active_inputs["template_reference"]])["Resources"]
        physical = {row["LogicalResourceId"]: row["PhysicalResourceId"] for row in final["resources"][identifier] if row.get("PhysicalResourceId")}
        rule, definition = next((logical, resource) for logical, resource in resources.items()
            if resource["Type"] == "AWS::EC2::SecurityGroupIngress" and isinstance(resource["Properties"].get("SourceSecurityGroupId"), dict)
            and resource["Properties"]["GroupId"]["Ref"] in physical and resource["Properties"]["SourceSecurityGroupId"]["Ref"] in physical)
        target_group = physical[definition["Properties"]["GroupId"]["Ref"]]
        source_group = physical[definition["Properties"]["SourceSecurityGroupId"]["Ref"]]
        self.assertNotEqual(target_group, source_group)
        for group, expected in ((source_group, "present"), (target_group, "absent")):
            state = deepcopy(final)
            state.setdefault("native_replies", {})[json.dumps(["ec2", "describe-security-groups", {"GroupIds": [group]}], sort_keys=True, separators=(",", ":"))] = {"error": "InvalidGroup.NotFound"}
            self.write(state)
            report = self.adapter.observe_resource_cleanup(stack=stack, stack_id=identifier)
            self.assertEqual(next(row for row in report["resources"] if row["logical_id"] == rule)["status"], expected)
        service = next(logical for logical, resource in resources.items() if resource["Type"] == "AWS::ECS::Service")
        cluster = document["resolved"]["creation:" + stack]["inputs"]["values"]["ClusterArn"]
        state = deepcopy(final)
        state.setdefault("native_replies", {})[json.dumps(["ecs", "describe-services", {"cluster": cluster, "services": [physical[service]]}], sort_keys=True, separators=(",", ":"))] = {
            "response": {"services": [{"serviceArn": physical[service], "clusterArn": "private-canary", "status": "ACTIVE", "desiredCount": 0, "runningCount": 0, "pendingCount": 0}], "failures": []}}
        self.write(state)
        report = self.adapter.observe_resource_cleanup(stack=stack, stack_id=identifier)
        service_row = next(row for row in report["resources"] if row["logical_id"] == service)
        self.assertEqual(service_row["status"], "unknown")
        self.assertEqual(service_row["reason"], "environment-session-operation-cleanup-resource-response-invalid")
        self.assertNotIn("private-canary", json.dumps(report))
        self.assertEqual(self.read()["history"], final["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_native_cleanup_global_gate_requires_original_intent_exact_terminal_root_and_current_stack(self):
        self.native_cleanup_fixture()
        valid = self.read(); identifier = self.delete_inputs()["stack_id"]
        key = "delete:" + self.stack + ":delete"
        def missing_intent(state):
            document = json.loads(state["raw"]); document["operations"].pop(key); document["state"] = "sealed"
            state["raw"] = json.dumps(document)
        def changed_intent(state):
            document = json.loads(state["raw"]); request = document["operations"][key]["request"]
            request["arguments_sha256"] = "f" * 64; document["operations"][key]["request_sha256"] = OWNER._digest(request)
            state["raw"] = json.dumps(document)
        mutations = [
            (missing_intent, "cleanup-delete-required"), (changed_intent, "reservation-mismatch"),
            (lambda s: s["delete_events"][identifier][0].update(ClientRequestToken="private-canary"), "operation-terminal-unconfirmed"),
            (lambda s: s["delete_events"][identifier][0].update(PhysicalResourceId=identifier[:-1] + "6"), "operation-terminal-unconfirmed"),
            (lambda s: s["delete_events"][identifier][0].update(LogicalResourceId="private-canary"), "operation-event-invalid"),
            (lambda s: s["delete_events"][identifier][0].update(Timestamp="1970-01-01T00:00:00+00:00"), "operation-event-invalid"),
            (lambda s: s["delete_events"][identifier][0].update(ResourceStatus="DELETE_IN_PROGRESS"), "operation-terminal-unconfirmed"),
            (lambda s: s["delete_events"][identifier][0].update(ResourceStatus="DELETE_FAILED"), "cleanup-delete-unconfirmed"),
            (lambda s: s["stacks"][identifier].update(StackStatus="DELETE_IN_PROGRESS"), "cleanup-delete-unconfirmed"),
            (lambda s: s["stacks"][identifier].update(StackName="private-canary"), "cleanup-delete-observation-invalid"),
            (lambda s: s["stacks"].clear(), "cleanup-delete-observation-unavailable:aws-parameter-invalid"),
        ]
        for mutate, reason in mutations:
            state = deepcopy(valid); mutate(state); self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.observe_resource_cleanup(stack=self.stack, stack_id=identifier), reason),
                             "environment-session-operation-" + reason)
            after = self.read()
            self.assertEqual(after["history"], valid["history"])
            self.assertEqual(after["submissions"], valid["submissions"])
            self.assertTrue(all(row[0] in ("s3api", "cloudformation") for row in after["calls"][len(valid["calls"]):]))
        self.write(valid)
        self.assertEqual(self.failed(lambda: self.adapter.observe_resource_cleanup(stack=self.stack, stack_id=identifier, RoleARN="private-canary"),
            "operation-inputs-invalid"), "environment-session-operation-operation-inputs-invalid")
        self.assertEqual(self.read()["calls"], valid["calls"])

    def test_native_cleanup_malformed_denied_and_incomplete_observations_are_unknown_not_absent(self):
        facts = self.native_cleanup_fixture()
        (stack, logical), fact = next((key, value) for key, value in facts.items() if value["kind"] == "AWS::EC2::VPC")
        call = json.dumps(fact["call"], sort_keys=True, separators=(",", ":")); valid = self.read()
        variants = [
            ({"response": {}}, "cleanup-resource-response-invalid"),
            ({"response": {"Vpcs": {}}}, "cleanup-resource-response-invalid"),
            ({"response": {"Vpcs": [{"VpcId": "private-canary"}]}}, "cleanup-resource-response-invalid"),
            ({"response": {"Vpcs": [{"VpcId": fact["identity"]}] * 2}}, "cleanup-resource-response-invalid"),
            ({"response": {"Vpcs": [], "NextToken": "private-canary"}}, "cleanup-resource-observation-unavailable:aws-response-invalid"),
            ({"response": {"Vpcs": [], "Marker": "private-canary"}}, "cleanup-resource-observation-unavailable:aws-response-invalid"),
            ({"response": {"Vpcs": [], "IsTruncated": True}}, "cleanup-resource-observation-unavailable:aws-response-invalid"),
            ({"error": "AccessDenied"}, "cleanup-resource-observation-unavailable:aws-access-denied"),
            ({"error": "ExpiredToken"}, "cleanup-resource-observation-unavailable:aws-credentials-expired"),
            ({"error": "UnknownNotFound"}, "cleanup-resource-observation-unavailable:aws-command-failed"),
        ]
        for reply, reason in variants:
            state = deepcopy(valid); state["native_replies"][call] = reply; self.write(state)
            result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=self.delete_inputs(stack)["stack_id"])
            row = next(row for row in result["resources"] if row["logical_id"] == logical)
            self.assertEqual(row["status"], "unknown")
            self.assertEqual(row["reason"], "environment-session-operation-" + reason)
            self.assertNotIn("private-canary", json.dumps(result))
            self.assertEqual(self.read()["history"], valid["history"])
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        # A retained, source-indexed value must still be a valid native identity.
        state = deepcopy(valid); identifier = self.delete_inputs(stack)["stack_id"]
        state["resources"][identifier] = [{**row, "PhysicalResourceId": "private-canary"} if row["LogicalResourceId"] == logical else row for row in state["resources"][identifier]]
        document = json.loads(state["raw"]); position = [key for key, _ in self.adapter._resource_index(stack)].index(logical)
        document["physical_resources"][stack]["slots"][position] = OWNER._digest("private-canary")
        state["raw"] = json.dumps(document); self.write(state)
        result = self.adapter.observe_resource_cleanup(stack=stack, stack_id=identifier)
        row = next(row for row in result["resources"] if row["logical_id"] == logical)
        self.assertEqual(row["reason"], "environment-session-operation-cleanup-resource-identity-invalid")
        self.assertEqual(row["status"], "unknown")
        self.assertNotIn(["ec2", "describe-vpcs"], self.read()["calls"][len(valid["calls"]):])
        self.assertEqual(self.read()["history"], valid["history"])
        self.assertEqual(self.read()["submissions"], valid["submissions"])

    def test_unknown_late_and_failed_policy_events_block_deletion_without_cancelling_intent(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs); self.adapter.seal()
        valid = self.read(); identifier = self.delete_inputs()["stack_id"]
        mutations = [
            (lambda s: s["events"].update({identifier: []}), "operation-terminal-unconfirmed"),
            (lambda s: s["events"][identifier][0].update(ClientRequestToken="private-canary"), "operation-terminal-unconfirmed"),
            (lambda s: s["events"][identifier][0].update(Timestamp="1970-01-01T00:00:00+00:00"), "operation-event-invalid"),
            (lambda s: s["events"][identifier][0].update(Timestamp="9999-01-01T00:00:00+00:00"), "operation-event-invalid"),
            (lambda s: s["events"][identifier][0].update(ResourceStatus="CREATE_IN_PROGRESS"), "operation-terminal-unconfirmed"),
            (lambda s: s["events"][identifier][0].update(ResourceStatus="CREATE_FAILED"), "operation-retained-mismatch"),
            (lambda s: s["events"][identifier].append(deepcopy(s["events"][identifier][0])), "operation-event-invalid"),
        ]
        for mutate, reason in mutations:
            state = deepcopy(valid); mutate(state); self.write(state)
            self.failed(lambda: self.adapter.delete(**self.delete_inputs()), reason)
            self.assertEqual(self.read()["submissions"], valid["submissions"])
            self.assertEqual(json.loads(self.read()["raw"])["operation_outcomes"], json.loads(valid["raw"])["operation_outcomes"])

    def test_pre_provider_seal_retains_definite_not_submitted_and_never_reopens(self):
        self.initialize()
        def seal_during_gate(context):
            self.records.seal()
        adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=seal_during_gate)
        self.failed(lambda: adapter.prepare("creation", **self.inputs), "session-admission-closed")
        document = json.loads(self.read()["raw"])
        key = "creation:" + self.stack + ":prepare"
        outcome = document["operation_outcomes"][key]
        self.assertEqual(outcome["status"], "not-submitted")
        self.assertEqual(self.read()["submissions"], [])
        before = self.read()
        self.adapter.prepare("creation", **self.inputs)
        self.assertEqual(self.read()["history"], before["history"])
        self.failed(lambda: self.records.retain_outcome(key, {**outcome, "evidence_sha256": "f" * 64}), "outcome-mismatch")

    def test_reserved_but_unknown_sender_blocks_delete_and_retained_execution_cannot_replay(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs)
        document = json.loads(self.read()["raw"])
        request = document["operations"]["creation:" + self.stack + ":prepare"]["request"]
        store = OWNER._Reservations(self.records.storage("creation"), request)
        reservation, fresh = store.reserve("execute", request)
        self.assertTrue(fresh)
        self.adapter.seal()
        before = self.read()
        self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "operation-terminal-unconfirmed")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(json.loads(self.read()["raw"])["operation_outcomes"], json.loads(before["raw"])["operation_outcomes"])
        # A process interrupted between reservation and send cannot be labelled
        # cancelled. Recovery only invokes its observer, without resubmission.
        self.assertEqual(self.adapter.execute("creation", **self.inputs)["status"], "unknown")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(json.loads(self.read()["raw"])["operations"]["creation:" + self.stack + ":execute"]["operation_id"], reservation["operation_id"])

    def test_retained_custody_reconstructs_original_arguments_not_only_matching_saved_hashes(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        foundation = dict(self.plan["stack_names"])["foundation"]
        self.adapter.prepare("creation", stack=foundation, template_reference=dict(self.plan["stack_templates"])[foundation])
        self.adapter.seal()
        state = self.read(); document = json.loads(state["raw"])
        for phase in ("prepare", "execute"):
            key = "creation:" + self.stack + ":" + phase
            row = document["operations"][key]
            _, arguments = self.adapter._operation("creation", self.stack, self.reference, document,
                                                   document["resolved"]["creation:" + self.stack])
            arguments["RoleARN"] = document["base"]["execution_roles"]["cleanup"]
            row["request"]["arguments_sha256"] = OWNER._digest(arguments)
            row["request_sha256"] = OWNER._digest(row["request"])
            document["operation_outcomes"][key]["request_sha256"] = row["request_sha256"]
        for field in ("creation_custody", "creation_evidence"):
            document[field][self.stack]["creation_request_sha256"] = row["request_sha256"]
        state["raw"] = json.dumps(document); self.write(state)
        self.records.observe_existing()  # Internally matching hashes are not source authority.
        self.failed(lambda: self.adapter.prepare("prepare-discard", **self.inputs), "custody-reservation-mismatch")
        self.assertEqual(self.read()["history"], state["history"])
        self.assertEqual(self.read()["submissions"], state["submissions"])

    def test_noop_discard_and_atomic_delete_barrier_reject_a_competing_discard_reservation(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs); self.adapter.seal()
        self.assertTrue(OWNER.CF.templates_equal(dict(self.plan["projected_templates"])[self.reference], dict(self.plan["discard_templates"])[self.reference]))
        write = self.records._write
        competing = []
        def race(document, prior, action):
            if action == "reserve-delete" and not competing:
                competing.append(True)
                state = self.read(); state["prepare_status"] = "FAILED"; self.write(state)
                self.adapter.prepare("prepare-discard", **self.inputs)
            return write(document, prior, action)
        with patch.object(self.records, "_write", side_effect=race):
            self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "session-record-conflict")
        document = json.loads(self.read()["raw"])
        self.assertEqual(document["state"], "sealed")
        self.assertNotIn("delete:" + self.stack + ":delete", document["operations"])
        # The provider returned no-change FAILED before any success was retained.
        self.adapter.delete(**self.delete_inputs())
        before = self.read()
        self.failed(lambda: self.adapter.execute("prepare-discard", **self.inputs), "execution-not-ready:preparation-failed")
        self.adapter.seal()
        self.assertEqual(json.loads(self.read()["raw"])["state"], "deleting")
        self.adapter.prepare("prepare-discard", **self.inputs)
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_early_delete_preserves_discard_admission_and_failed_active_database_is_blocked(self):
        self.create_graph()
        self.adapter.prepare("activation", **self.active_inputs); self.adapter.execute("activation", **self.active_inputs)
        self.adapter.seal()
        before = self.read()
        self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs(self.active_inputs["stack"])), "discard-required"),
                         "environment-session-operation-discard-required")
        self.assertEqual(json.loads(self.read()["raw"])["state"], "sealed")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual({row["stack"]: row for row in self.adapter.reconcile_stops()}[self.active_inputs["stack"]]["status"], "stop-required")

    def test_failure_policy_is_native_immutable_and_provider_policy_cannot_replace_it(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs)
        self.adapter.seal(); valid = self.read()
        for version in (1, 2, 3, 4, 5, 6):
            state = deepcopy(valid); document = json.loads(state["raw"])
            document["schema"] = "aws-temporary-session/v" + str(version)
            state["raw"] = json.dumps(document); self.write(state)
            self.assertEqual(self.failed(self.records.observe_existing, "session-record-invalid"), "session-record-invalid")
            self.assertEqual(self.read()["history"], valid["history"])
        for policy in (None, False, 1, "private-canary"):
            state = deepcopy(valid); document = json.loads(state["raw"])
            for row in document["operations"].values():
                if policy is None:
                    row["request"].pop("disable_rollback")
                else:
                    row["request"]["disable_rollback"] = policy
                row["request_sha256"] = OWNER._digest(row["request"])
            state["raw"] = json.dumps(document); self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs()), "session-record-shape-invalid"),
                             "session-record-shape-invalid")
            self.assertEqual(self.read()["history"], valid["history"])
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        state = deepcopy(valid)
        state["changes"][self.stack + "-session-create"]["OnStackFailure"] = "DO_NOTHING"
        self.write(state)
        self.assertEqual(self.failed(lambda: self.adapter.execute("creation", **self.inputs), "operation-failure-policy-unconfirmed"),
                         "environment-session-operation-operation-failure-policy-unconfirmed")
        self.assertEqual(self.read()["history"], valid["history"])
        self.assertEqual(self.read()["submissions"], valid["submissions"])

    def test_failed_activation_only_admits_first_stop_and_never_successful_outputs(self):
        self.select_plan(self.entity_plan); self.initialize()
        for stack in self.plan["stack_order"][:-1]:
            inputs = {"stack": stack, "template_reference": dict(self.plan["stack_templates"])[stack]}
            self.adapter.prepare("creation", **inputs); self.adapter.execute("creation", **inputs)
        stack = self.plan["stack_order"][-2]
        inputs = {"stack": stack, "template_reference": dict(self.plan["stack_templates"])[stack]}
        self.adapter.prepare("activation", **inputs)
        state = self.read(); state["execution_status"] = "UPDATE_FAILED"; self.write(state)
        self.assertEqual(self.adapter.execute("activation", **inputs)["status"], "failed")
        identifier = self.delete_inputs(stack)["stack_id"]
        state = self.read()
        self.assertEqual(self.failed(lambda: self.adapter.prepare("creation", **self.active_inputs), "foundation-stack-not-ready"),
                         "environment-session-operation-foundation-stack-not-ready")
        self.assertEqual(self.read()["history"], state["history"])
        self.assertEqual(self.read()["submissions"], state["submissions"])
        self.adapter.seal(); before = self.read()
        self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs(stack)), "discard-required"),
                         "environment-session-operation-discard-required")
        self.assertEqual(json.loads(self.read()["raw"])["operations"], json.loads(before["raw"])["operations"])
        self.assertEqual(json.loads(self.read()["raw"])["state"], "sealed")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual({row["stack"]: row for row in self.adapter.reconcile_stops()}[stack]["status"], "stop-required")
        self.adapter.prepare("prepare-discard", **inputs)
        state = self.read(); state["execution_status"] = "UPDATE_FAILED"; self.write(state)
        self.assertEqual(self.adapter.execute("prepare-discard", **inputs)["status"], "failed")
        after = self.read(); document = json.loads(after["raw"])
        self.assertEqual(document["operation_outcomes"]["activation:" + stack + ":execute"]["status"], "UPDATE_FAILED")
        self.assertIn(stack, document["creation_evidence"])
        self.assertEqual(OWNER.CHANGE_SETS.parameter_values(after["stacks"][identifier]["Parameters"]),
                         document["resolved"]["creation:" + stack]["inputs"]["values"])
        self.source_root = self.root / "missing-source"
        cold = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: self.fail("retained preflight"))
        with patch.object(OWNER, "_module", side_effect=AssertionError("retained source import")):
            self.assertEqual(cold.execute("prepare-discard", **inputs)["status"], "failed")
        self.assertEqual(self.read()["history"], after["history"])
        self.assertEqual(self.read()["submissions"], after["submissions"])

    def test_discard_execution_reviews_exact_effects_before_send_and_retains_denial(self):
        self.create_graph(); inputs = self.active_inputs
        self.adapter.prepare("activation", **inputs); self.adapter.execute("activation", **inputs)
        self.adapter.seal(); self.adapter.prepare("prepare-discard", **inputs)
        valid = self.read(); name = inputs["stack"] + "-session-discard"
        identifier = self.delete_inputs(inputs["stack"])["stack_id"]
        changes = valid["changes"][name]["Changes"]
        self.assertTrue(changes)
        resources = json.loads(dict(self.plan["discard_templates"])[inputs["template_reference"]])["Resources"]
        unrelated = next(key for key in resources if key not in {row["ResourceChange"]["LogicalResourceId"] for row in changes})
        mutations = [
            (lambda s: s["changes"][name].update(OnStackFailure="private-canary"), "operation-failure-policy-unconfirmed"),
            (lambda s: s["changes"][name].update(Status=["private-canary"]), "output-creation-mismatch"),
            (lambda s: s["changes"][name].update(Status={"private-canary": True}), "output-creation-mismatch"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"].update(Action="Add"), "custody-resource-mismatch"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"].update(Replacement="True"), "custody-resource-mismatch"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"].update(LogicalResourceId=["private-canary"]), "custody-resource-mismatch"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"]["Details"][0].update(Evaluation="Dynamic"), "discard-change-invalid"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"]["Details"][0].update(CausingEntity="private-canary"), "discard-change-invalid"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"]["Details"][0]["Target"].update(Name="private-canary"), "discard-change-invalid"),
            (lambda s: s["changes"][name]["Changes"][0]["ResourceChange"]["Details"][0]["Target"].update(Name=["private-canary"]), "discard-change-invalid"),
            (lambda s: s["changes"][name].update(Changes=[]), "discard-change-invalid"),
            (lambda s: s["changes"][name]["Changes"].append({"ResourceChange": {
                "LogicalResourceId": unrelated, "ResourceType": resources[unrelated]["Type"], "Action": "Modify", "Replacement": "False"}}),
             "discard-change-invalid"),
            (lambda s: s["stacks"][identifier]["Parameters"][0].update(ParameterValue="private-canary"), "deployed-inputs-drift"),
            (lambda s: s["templates"].update({identifier: "{}"}), "custody-template-mismatch"),
            (lambda s: s["events"][identifier][0].update(ClientRequestToken="private-canary"), "operation-terminal-unconfirmed"),
            (lambda s: s.update(transport_fault="AccessDenied"), "execution-not-ready:aws-access-denied"),
        ]
        for mutate, reason in mutations:
            state = deepcopy(valid); mutate(state); self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.execute("prepare-discard", **inputs), reason),
                             "environment-session-operation-" + reason)
            denied = self.read(); document = json.loads(denied["raw"])
            self.assertEqual(denied["submissions"], valid["submissions"])
            self.assertEqual(document["state"], "sealed")
            self.assertNotIn("prepare-discard:" + inputs["stack"] + ":execute", document["operations"])
            self.assertEqual(self.read()["history"], denied["history"])
            self.assertEqual(self.read()["submissions"], valid["submissions"])
        self.write(valid)
        self.adapter.execute("prepare-discard", **inputs)
        self.assertEqual(len(self.read()["submissions"]), len(valid["submissions"]) + 1)

    def test_pending_preparation_does_not_consume_execution_and_ready_is_rechecked(self):
        self.initialize()
        inputs = {"kind": "creation", "stack": self.stack, "phase": "prepare"}
        self.assertEqual(self.adapter.reconcile_operation(**inputs)["status"], "unreserved")
        state = self.read(); state["prepare_status"] = "CREATE_IN_PROGRESS"; self.write(state)
        self.assertEqual(self.adapter.prepare("creation", **self.inputs)["status"], "pending")
        before = self.read()
        self.assertEqual(self.failed(lambda: self.adapter.execute("creation", **self.inputs), "execution-not-ready:preparation-pending"),
                         "environment-session-operation-execution-not-ready:preparation-pending")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertNotIn("creation:" + self.stack + ":execute", json.loads(self.read()["raw"])["operations"])
        state = self.read(); change = state["changes"][self.stack + "-session-create"]
        change.update(Status="CREATE_COMPLETE", ExecutionStatus="AVAILABLE")
        change["Changes"] = [{"ResourceChange": {"LogicalResourceId": logical, "ResourceType": resource["Type"], "Action": "Add"}}
                             for logical, resource in json.loads(change["fixture_template"])["Resources"].items()]
        self.write(state)
        ready = self.adapter.reconcile_operation(**inputs)
        self.assertEqual(ready["status"], "ready")
        before = self.read()
        self.assertEqual(self.adapter.reconcile_operation(**inputs), ready)
        self.assertEqual(self.read()["history"], before["history"])
        def changes_during_gate(context):
            if context["action"] == "creation-execute":
                state = self.read(); state["changes"][self.stack + "-session-create"]["ExecutionStatus"] = "OBSOLETE"; self.write(state)
        adapter = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=changes_during_gate)
        self.failed(lambda: adapter.execute("creation", **self.inputs), "execution-not-ready:preparation-unavailable")
        denied = self.read()
        self.assertEqual(denied["submissions"], before["submissions"])
        self.assertEqual(self.adapter.execute("creation", **self.inputs)["status"], "not-submitted")
        self.assertEqual(self.read()["history"], denied["history"])
        self.assertEqual(self.read()["submissions"], denied["submissions"])

    def test_lost_execution_observation_recovers_only_matching_events_and_retention(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs)
        self.fault("lost-execute-change-set")
        self.failed(lambda: self.adapter.execute("creation", **self.inputs), "submission-uncertain:aws-response-invalid")
        state = self.read(); identifier = self.delete_inputs()["stack_id"]
        events = deepcopy(state["events"][identifier]); state["events"][identifier] = []; self.write(state)
        before = self.read(); inputs = {"kind": "creation", "stack": self.stack, "phase": "execute"}
        self.assertEqual(self.adapter.reconcile_operation(**inputs)["reason"], "operation-event-unconfirmed")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        state = self.read(); state["events"][identifier] = events; state["fault"] = "lost-put"; self.write(state)
        self.failed(lambda: self.adapter.reconcile_operation(**inputs), "retention-unconfirmed")
        after = self.read(); self.now = 8201; self.source_root = self.root / "missing-source"
        cold = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: self.fail("no fresh preflight"))
        with patch.object(OWNER, "_module", side_effect=AssertionError("no source or package import")):
            self.assertEqual(cold.execute("creation", **self.inputs)["status"], "succeeded")
        self.assertEqual(self.read()["history"], after["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        state = self.read(); state["transport_fault"] = "ExpiredToken"; self.write(state)
        result = cold.reconcile_operation(**inputs)
        self.assertEqual((result["status"], result["reason"]), ("unknown", "aws-credentials-expired"))
        self.assertNotIn("private-canary", json.dumps(result))

    def test_stop_reconciliation_cannot_use_historical_creation_to_mask_pending_activation(self):
        self.create_graph(); self.adapter.prepare("activation", **self.active_inputs)
        state = self.read(); state["execution_status"] = "UPDATE_IN_PROGRESS"; self.write(state)
        self.assertEqual(self.adapter.execute("activation", **self.active_inputs)["status"], "pending")
        self.adapter.seal(); before = self.read()
        rows = self.adapter.reconcile_stops()
        self.assertEqual([row["stack"] for row in rows], list(reversed(self.plan["stack_order"])))
        self.assertEqual({row["stack"]: row for row in rows}[self.active_inputs["stack"]]["status"], "pending")
        self.assertEqual({row["stack"]: row for row in rows}[self.stack]["status"], "stopped")
        for stack in self.plan["stack_order"]:
            self.failed(lambda: self.adapter.delete(**self.delete_inputs(stack)), "operation-terminal-unconfirmed")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertFalse(any(key.startswith("delete:") for key in json.loads(self.read()["raw"])["operations"]))
        self.assertEqual(json.loads(self.read()["raw"])["state"], "sealed")

    def test_definite_not_submitted_operations_use_actual_stopped_state_without_replay(self):
        self.initialize(); initialized = self.read()
        for boundary in ("creation-prepare", "creation-execute", "prepare-discard-prepare", "prepare-discard-execute"):
            with self.subTest(boundary=boundary):
                self.write(deepcopy(initialized))
                denied = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: True)
                if boundary != "creation-prepare":
                    self.adapter.prepare("creation", **self.inputs)
                if boundary.startswith("prepare-discard"):
                    self.adapter.execute("creation", **self.inputs); self.adapter.seal()
                if boundary == "prepare-discard-execute":
                    self.adapter.prepare("prepare-discard", **self.inputs)
                kind, phase = boundary.rsplit("-", 1)
                self.assertEqual(self.failed(lambda: getattr(denied, phase)(kind, **self.inputs), "preflight-unconfirmed"),
                                 "environment-session-operation-preflight-unconfirmed")
                self.adapter.seal(); before = self.read()
                row = next(row for row in self.adapter.reconcile_stops() if row["stack"] == self.stack)
                self.assertEqual(row["status"], "not-started" if boundary == "creation-prepare" else
                                 "never-allocated" if boundary == "creation-execute" else "stopped")
                self.assertEqual(getattr(self.adapter, phase)(kind, **self.inputs)["status"], "not-submitted")
                self.assertEqual(self.read()["submissions"], before["submissions"])
                if boundary != "creation-prepare":
                    self.assertEqual(self.adapter.delete(**self.delete_inputs())["status"], "pending")
                    self.assertEqual(json.loads(self.read()["raw"])["state"], "deleting")

    def test_unsubmitted_activation_can_stop_but_consumed_needed_stop_stays_blocked(self):
        self.create_graph(); created = self.read()
        denied = self.make_adapter(self.plan, self.records, provider=self.provider, preflight=lambda _: True)
        self.adapter.prepare("activation", **self.active_inputs)
        self.failed(lambda: denied.execute("activation", **self.active_inputs), "preflight-unconfirmed")
        self.adapter.seal(); before = self.read()
        rows = self.adapter.reconcile_stops()
        self.assertTrue(all(row["status"] == "stopped" for row in rows))
        self.assertEqual(self.adapter.execute("activation", **self.active_inputs)["status"], "not-submitted")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.adapter.delete(**self.delete_inputs(self.active_inputs["stack"]))
        self.write(deepcopy(created))
        self.adapter.prepare("activation", **self.active_inputs); self.adapter.execute("activation", **self.active_inputs)
        self.adapter.seal()
        self.failed(lambda: denied.prepare("prepare-discard", **self.active_inputs), "preflight-unconfirmed")
        before = self.read(); rows = {row["stack"]: row for row in self.adapter.reconcile_stops()}
        self.assertEqual((rows[self.active_inputs["stack"]]["status"], rows[self.active_inputs["stack"]]["reason"]),
                         ("blocked", "stop-attempt-retained"))
        self.assertEqual(self.adapter.prepare("prepare-discard", **self.active_inputs)["status"], "not-submitted")
        self.failed(lambda: self.adapter.delete(**self.delete_inputs(self.stack)), "discard-required")
        self.assertEqual(self.read()["submissions"], before["submissions"])
        self.assertEqual(json.loads(self.read()["raw"])["state"], "sealed")

    def test_operation_reconciliation_rejects_external_outcomes_and_retention_conflict(self):
        self.assertEqual(self.failed(lambda: self.adapter.reconcile_stops(**{"private-canary": True}), "operation-inputs-invalid"),
                         "environment-session-operation-operation-inputs-invalid")
        for inputs in ({"kind": [], "stack": self.stack, "phase": "prepare"},
                       {"kind": "creation", "stack": self.stack, "phase": "delete"},
                       {"kind": "creation", "stack": self.stack, "phase": "prepare", "observe": "private-canary"}):
            self.failed(lambda: self.adapter.reconcile_operation(**inputs), "operation-")
        self.assertEqual(self.read()["calls"], [])
        self.initialize(); self.fault("lost-create-change-set")
        self.failed(lambda: self.adapter.prepare("creation", **self.inputs), "submission-uncertain")
        before = self.read(); self.fault("PreconditionFailed")
        self.assertEqual(self.failed(lambda: self.adapter.reconcile_operation(kind="creation", stack=self.stack, phase="prepare"), "session-record-conflict"),
                         "session-record-conflict")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def database_runtime_fixture(self):
        self.create_graph()
        stack = self.active_inputs["stack"]
        view = self.adapter.runtime_view(stack=stack, required_outputs=[])
        logical, resource = next((logical, resource) for logical, resource in view["resources"].items()
                                 if resource["type"] == "AWS::RDS::DBInstance")
        call = ["rds", "describe-db-instances", {"DBInstanceIdentifier": resource["physical_id"]}]
        response = self.provider(call[0], call[1], **call[2])
        return stack, logical, view, call, response

    def test_runtime_database_current_zero_accepts_optional_omission_without_cleanup_exclusion(self):
        stack, logical, view, call, response = self.database_runtime_fixture()
        database = response["DBInstances"][0]
        declared = view["template"]["Resources"][logical]["Properties"]["BackupRetentionPeriod"]
        self.assertIs(type(declared), int); self.assertEqual(declared, 0)
        self.assertIs(type(database["BackupRetentionPeriod"]), int); self.assertEqual(database["BackupRetentionPeriod"], 0)
        self.assertNotIn("PendingModifiedValues", database)
        self.assertNotIn("DBInstanceAutomatedBackupsReplications", database)
        baseline = self.read()
        self.assertEqual(json.loads(baseline["raw"])["physical_resources"][stack]["databases"], [OWNER._digest(database["DbiResourceId"])])
        key = json.dumps(call, sort_keys=True, separators=(",", ":"))
        for optional in ({}, {"PendingModifiedValues": {}}, {"PendingModifiedValues": {"BackupRetentionPeriod": 0}},
                         {"PendingModifiedValues": {"AllocatedStorage": 30}, "DBInstanceAutomatedBackupsReplications": []}):
            state = deepcopy(baseline)
            state["native_replies"] = {key: {"response": {"DBInstances": [{**database, **optional}]}}}; self.write(state)
            observed = self.adapter.runtime_view(stack=stack, required_outputs=[])
            self.assertEqual(set(observed), set(view))
            self.assertEqual(self.read()["history"], baseline["history"])
            self.assertEqual(self.read()["submissions"], baseline["submissions"])
        self.write(baseline)  # The default native response omits both optional fields.
        self.adapter.seal(); self.adapter.delete(**self.delete_inputs(stack)); self.confirm_fixture_delete(stack)
        before = self.read()
        report = self.adapter.observe_resource_cleanup(stack=stack, stack_id=view["stack_id"])
        row = next(row for row in report["resources"] if row["logical_id"] == logical)
        self.assertEqual(next(row for row in row["artifacts"] if row["kind"] == "cross-region-backups"),
                         {"kind": "cross-region-backups", "status": "unknown"})
        self.assertEqual({row["kind"] for row in row["artifacts"]},
                         {"manual-snapshots", "automated-snapshots", "awsbackup-snapshots", "automated-backups", "cross-region-backups"})
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

    def test_runtime_database_policy_rejections_do_not_veto_owned_deletion(self):
        stack, _, _, call, response = self.database_runtime_fixture()
        baseline = self.read(); key = json.dumps(call, sort_keys=True, separators=(",", ":"))
        cases = [("BackupRetentionPeriod", value, "runtime-database-retention-unconfirmed")
                 for value in (None, False, True, "0", 7)]
        cases += [("PendingModifiedValues", value, "runtime-database-pending-retention-unconfirmed")
                  for value in (None, [], {"BackupRetentionPeriod": True}, {"BackupRetentionPeriod": 1}, {"BackupRetentionPeriod": "0"})]
        cases += [("DBInstanceAutomatedBackupsReplications", value, "runtime-database-replication-unconfirmed")
                  for value in (None, {}, [{"DBInstanceAutomatedBackupsArn": "private-canary"}])]
        for field, value, reason in cases:
            with self.subTest(field=field, value=value):
                changed = deepcopy(response)
                if field == "BackupRetentionPeriod" and value is None:
                    changed["DBInstances"][0].pop(field)
                else:
                    changed["DBInstances"][0][field] = value
                state = deepcopy(baseline); state["native_replies"] = {key: {"response": changed}}; self.write(state)
                self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=stack, required_outputs=[]), reason),
                                 "environment-session-operation-" + reason)
                self.assertEqual(self.read()["history"], baseline["history"])
                self.assertEqual(self.read()["submissions"], baseline["submissions"])
                # Exactly the same native policy observation is harmless to
                # independent original-stack deletion and immutable lineage.
                self.adapter.seal(); self.adapter.delete(**self.delete_inputs(stack))
                final = self.read(); document = json.loads(final["raw"])
                self.assertEqual(len(final["submissions"]), len(baseline["submissions"]) + 1)
                self.assertEqual(final["submissions"][-1][0], "delete-stack")
                self.assertIn("delete:" + stack + ":delete", document["operations"])
                self.assertEqual(document["physical_resources"][stack]["databases"],
                                 json.loads(baseline["raw"])["physical_resources"][stack]["databases"])

    def test_runtime_database_identity_and_transport_rejections_remain_finite(self):
        stack, _, _, call, response = self.database_runtime_fixture()
        self.adapter.seal()
        self.adapter._cleanup_readiness(stack, self.delete_inputs(stack)["stack_id"])
        baseline = self.read(); key = json.dumps(call, sort_keys=True, separators=(",", ":"))
        database = response["DBInstances"][0]
        for field, value, reason in (
                ("DBInstanceIdentifier", "private-canary", "cleanup-database-lineage-unconfirmed"),
                ("DBInstanceArn", None, "cleanup-database-lineage-unconfirmed"),
                ("DBInstanceArn", database["DBInstanceArn"].replace(self.records.account, "000000000000"), "cleanup-database-lineage-unconfirmed"),
                ("DBInstanceArn", database["DBInstanceArn"].replace(self.records.region, "us-east-1"), "cleanup-database-lineage-unconfirmed"),
                ("DbiResourceId", "private-canary", "cleanup-database-lineage-unconfirmed"),
                ("DbiResourceId", "db-OTHER", "cleanup-native-lineage-mismatch")):
            with self.subTest(field=field, value=value):
                changed = deepcopy(response)
                if value is None: changed["DBInstances"][0].pop(field)
                else: changed["DBInstances"][0][field] = value
                state = deepcopy(baseline); state["native_replies"] = {key: {"response": changed}}; self.write(state)
                self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=stack, required_outputs=[]), reason),
                                 "environment-session-operation-" + reason)
                self.assertEqual(self.read()["history"], baseline["history"])
                self.adapter.seal(); before = self.read()
                self.assertEqual(self.failed(lambda: self.adapter.delete(**self.delete_inputs(stack)), reason),
                                 "environment-session-operation-" + reason)
                self.assertEqual(self.read()["submissions"], baseline["submissions"])
                self.assertEqual(self.read()["history"], before["history"])
        for error, reason in (("AccessDenied", "aws-access-denied"), ("UnexpectedPrivateFailure", "aws-command-failed")):
            state = deepcopy(baseline); state["native_replies"] = {key: {"error": error}}; self.write(state)
            self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=stack, required_outputs=[]),
                "runtime-observation-unavailable:" + reason), "environment-session-operation-runtime-observation-unavailable:" + reason)
            self.assertEqual(self.read()["history"], baseline["history"])
            self.assertEqual(self.read()["submissions"], baseline["submissions"])

    def test_runtime_view_closed_inputs_reject_before_remote_observation(self):
        output = next(iter(json.loads(dict(self.plan["projected_templates"])[self.reference])["Outputs"]))
        valid = {"stack": self.stack, "required_outputs": [output]}
        for inputs, reason in (({}, "operation-inputs-invalid"),
                               ({**valid, "template": "private-canary"}, "operation-inputs-invalid"),
                               ({**valid, "stack": []}, "instance-selection-invalid"),
                               ({**valid, "stack": "private-canary"}, "instance-selection-invalid"),
                               ({**valid, "required_outputs": output}, "runtime-output-selection-invalid"),
                               ({**valid, "required_outputs": [output, output]}, "runtime-output-selection-invalid"),
                               ({**valid, "required_outputs": [[]]}, "runtime-output-selection-invalid"),
                               ({**valid, "required_outputs": ["private-canary"]}, "runtime-output-selection-invalid")):
            self.assertEqual(self.failed(lambda: self.adapter.runtime_view(**inputs), reason),
                             "environment-session-operation-" + reason)
        self.assertEqual(self.read()["calls"], [])
        self.assertEqual(self.read()["history"], [])

    def test_runtime_view_rejects_current_substitution_and_unknown_resources(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        identifier = self.delete_inputs()["stack_id"]
        created = self.read()
        incomplete = deepcopy(created); incomplete["resources"][identifier][0].pop("PhysicalResourceId"); self.write(incomplete)
        self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]), "runtime-resources-unconfirmed"),
                         "environment-session-operation-runtime-resources-unconfirmed")
        self.assertEqual(self.read()["submissions"], created["submissions"])
        self.write(created)
        output = next(iter(created["outputs"][self.stack]))
        self.adapter.runtime_view(stack=self.stack, required_outputs=[output])
        valid = self.read()
        mutations = (
            (lambda s: s["stacks"][identifier].update(StackId="private-canary"), "environment-session-operation-output-stack-mismatch"),
            (lambda s: s["templates"].update({identifier: '{"private-canary":true}'}), "environment-session-operation-custody-template-mismatch"),
            (lambda s: s["stacks"][identifier]["Parameters"][0].update(ParameterValue="private-canary"), "environment-session-operation-deployed-inputs-drift"),
            (lambda s: s["resources"][identifier][0].update(PhysicalResourceId="private-canary"), "session-physical-identity-mismatch"),
            (lambda s: s["resources"][identifier][0].update(LogicalResourceId=[]), "environment-session-operation-custody-resource-mismatch"),
            (lambda s: s["stacks"][identifier].update(Outputs=[]), "environment-session-operation-foundation-outputs-missing"),
        )
        for mutate, reason in mutations:
            with self.subTest(reason=reason):
                state = deepcopy(valid); mutate(state); self.write(state)
                self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[output]), reason), reason)
                self.assertEqual(self.read()["history"], valid["history"])
                self.assertEqual(self.read()["submissions"], valid["submissions"])

    def test_runtime_view_retention_loss_conflict_and_concurrent_intent_return_no_view(self):
        self.initialize(); self.adapter.prepare("creation", **self.inputs); self.adapter.execute("creation", **self.inputs)
        before = self.read()
        self.fault("PreconditionFailed")
        self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]), "session-record-conflict"),
                         "session-record-conflict")
        self.assertEqual(self.read()["history"], before["history"])
        self.fault("lost-put")
        self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]), "session-retention-unconfirmed"),
                         "session-retention-unconfirmed:aws-response-invalid")
        retained = self.read()
        self.assertIn(self.stack, json.loads(retained["raw"])["physical_resources"])
        self.adapter.runtime_view(stack=self.stack, required_outputs=[])
        self.assertEqual(self.read()["history"], retained["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])
        for invalid_time in (True, -1, "private-canary"):
            self.now = invalid_time
            self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]), "session-clock-invalid"),
                             "session-clock-invalid")
        self.now = 1000
        self.assertEqual(self.read()["history"], retained["history"])
        reconstruct = self.adapter.reconstruct_physical
        def competing_intent(**inputs):
            result = reconstruct(**inputs)
            document = self.records.observe_existing()["document"]
            request = document["operations"]["creation:" + self.stack + ":prepare"]["request"]
            # Retained observation cannot reserve or replay this existing label.
            self.assertFalse(OWNER._Reservations(self.records.storage("creation"), request).reserve("execute", request)[1])
            foundation = dict(self.plan["stack_names"])["foundation"]
            self.adapter.prepare("creation", stack=foundation, template_reference=dict(self.plan["stack_templates"])[foundation])
            return result
        with patch.object(self.adapter, "reconstruct_physical", side_effect=competing_intent):
            self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.stack, required_outputs=[]), "reconciliation-changed"),
                             "environment-session-operation-reconciliation-changed")
        self.assertEqual(len(self.read()["submissions"]), len(before["submissions"]) + 1)

    def test_runtime_view_never_masks_pending_or_failed_activation(self):
        self.create_graph(); created = self.read()
        for status, reason in (("UPDATE_IN_PROGRESS", "environment-session-operation-operation-terminal-unconfirmed"),
                               ("UPDATE_FAILED", "environment-session-operation-foundation-stack-not-ready")):
            with self.subTest(status=status):
                self.write(deepcopy(created))
                self.adapter.prepare("activation", **self.active_inputs)
                state = self.read(); state["execution_status"] = status; self.write(state)
                self.adapter.execute("activation", **self.active_inputs)
                before = self.read()
                self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.active_inputs["stack"], required_outputs=[]), reason), reason)
                self.assertEqual(self.read()["history"], before["history"])
                self.assertEqual(self.read()["submissions"], before["submissions"])
        self.write(deepcopy(created))
        state = self.read(); state["prepare_status"] = "FAILED"; self.write(state)
        self.adapter.prepare("activation", **self.active_inputs)
        before = self.read()
        self.assertEqual(self.failed(lambda: self.adapter.runtime_view(stack=self.active_inputs["stack"], required_outputs=[]), "runtime-phase-unready"),
                         "environment-session-operation-runtime-phase-unready")
        self.assertEqual(self.read()["history"], before["history"])
        self.assertEqual(self.read()["submissions"], before["submissions"])

if __name__ == "__main__":
    unittest.main()
