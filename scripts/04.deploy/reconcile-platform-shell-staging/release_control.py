#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.platform-shell-release-control
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines: [security, sre]
#   kind: script
#   purpose: Observe source-bound shell runtime and guard reviewed service mutations without replaying uncertain submissions.
#   portability: { class: internal, targets: [kanbien/staging] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.script.reconcile-platform-shell-staging
#     path: scripts/04.deploy/reconcile-platform-shell-staging/script.py
"""AWS shell adapter; qualification and succession remain in their existing owners."""
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import yaml

MODES={'runtime-alignment','service-update','service-rollback','service-operation-status'}
BASE=Path('infra/04.deploy/03.product/targets/kanbien/staging')


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


_TEMPLATES = module(Path(__file__).resolve().parents[3] / 'scripts/04.deploy/shared/provider-adapters/aws/cloudformation-template.py', 'aws_cloudformation_template')
template = _TEMPLATES.template
templates_equal = _TEMPLATES.templates_equal


def require(ok,reason):
    if not ok:raise ValueError(reason)


def unique(items,key,value):
    require(isinstance(items,list) and all(isinstance(i,dict) and key in i and value in i for i in items),'shell-provider-map-invalid')
    result={i[key]:i[value] for i in items};require(len(result)==len(items),'shell-provider-map-duplicate');return result


class Control:
    def __init__(self,owner,args,policy):
        self.owner,self.args,self.policy=owner,args,policy;self.root=owner.REPOSITORY_ROOT
        self.evidence=module(self.root/'scripts/04.deploy/verify-platform-shell-deploy-readiness/release_evidence.py','shell_release_evidence')
        self.response=module(self.root/'scripts/04.deploy/shared/provider-adapters/aws/response.py','shell_aws_response')
        self.manifest=yaml.safe_load(Path(args.deployment_manifest).read_text())
        self.evidence_class='simulated' if args.rehearsal_root else 'live'
        if args.rehearsal_root:require(Path(args.rehearsal_root).resolve()==self.root.resolve() and self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()),'shell-rehearsal-root-invalid')
        self.source,self.digest=self.evidence.identity(self.manifest)
        self.evidence.validate_candidate(self.manifest,root=self.root,evidence_class=self.evidence_class)
        image=self.manifest['artifacts']['image'];self.image=image['repository_uri']+'@'+self.digest
        require(image.get('deploy_uri',self.image)==self.image,'shell-release-image-reference-mismatch')
        self.profile=owner.load_yaml(Path(args.target_profile))
        self.stack_cache={};self.template_cache={};self.resources={}

    def aws(self,*command,mutation=False,absent=False):
        invocation=[self.args.aws_cli,*command,'--region',self.policy['region'],'--output','json']
        if self.args.aws_credential_source=='target-profile':invocation+=['--profile',self.policy['aws_profile']]
        try:result=subprocess.run(invocation,text=True,capture_output=True,timeout=self.args.timeout_seconds)
        except (OSError,subprocess.SubprocessError):raise ValueError('shell-operation-uncertain' if mutation else 'shell-observation-unavailable') from None
        if result.returncode:
            outcome=self.response.classify_error(command[0],command[1],result.stderr)
            if absent and outcome=='aws-resource-missing':return None
            raise ValueError('shell-operation-uncertain' if mutation else 'shell-observation-'+outcome)
        if mutation:return {}
        try:return json.loads(result.stdout)
        except json.JSONDecodeError:raise ValueError('shell-observation-malformed') from None

    def stack(self,name,*,fresh=True):
        if name not in self.stack_cache:
            value=self.aws('cloudformation','describe-stacks','--stack-name',name)
            stacks=value.get('Stacks');require(isinstance(stacks,list) and len(stacks)==1,'shell-stack-observation-invalid')
            item=stacks[0];require(item.get('StackName')==name,'shell-stack-identity-mismatch');self.stack_cache[name]=item
        value=self.stack_cache[name]
        require(value.get('StackStatus') in {'CREATE_COMPLETE','UPDATE_COMPLETE'},'shell-stack-not-stable')
        if fresh:
            drift=value.get('DriftInformation',{});require(drift.get('StackDriftStatus')=='IN_SYNC','shell-stack-drift-unproven')
            checked=datetime.fromisoformat(drift['LastCheckTimestamp'].replace('Z','+00:00'))
            age=(datetime.now(timezone.utc)-checked).total_seconds();require(-60<=age<=900,'shell-stack-drift-stale')
            modified=value.get('LastUpdatedTime',value.get('CreationTime'))
            require(isinstance(modified,str) and checked>=datetime.fromisoformat(modified.replace('Z','+00:00')),'shell-stack-drift-precedes-change')
        return value

    def sources(self):
        service=template((self.root/BASE/'cloudformation/service.yml').read_text())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'foundation.yml'
            result=subprocess.run(['bash',str(self.root/'scripts/04.deploy/render-platform-shell-foundation-template/script.sh'),'--output',str(path)],cwd=self.root,text=True,capture_output=True,timeout=30)
            require(result.returncode==0,'shell-foundation-render-failed');foundation=template(path.read_text())
        return {self.policy['service_stack']:service,self.policy['foundation_stack']:foundation}

    def source_alignment(self,*,service=True):
        self.template_cache=self.sources()
        for name,source in self.template_cache.items():
            if not service and name==self.policy['service_stack']:continue
            self.stack(name)
            live=self.aws('cloudformation','get-template','--stack-name',name,'--template-stage','Original')
            require(templates_equal(live.get('TemplateBody'),source),'shell-stack-template-mismatch')

    def physical(self,name,logical):
        key=(name,logical)
        if key not in self.resources:
            response=self.aws('cloudformation','describe-stack-resource','--stack-name',name,'--logical-resource-id',logical).get('StackResourceDetail',{})
            require(response.get('LogicalResourceId')==logical and isinstance(response.get('PhysicalResourceId'),str),'shell-resource-identity-unavailable')
            self.resources[key]=response['PhysicalResourceId']
        return self.resources[key]

    def resolve(self,value,name):
        if isinstance(value,list):return [self.resolve(i,name) for i in value]
        if not isinstance(value,dict):return value
        if set(value)=={'Ref'}:
            ref=value['Ref'];parameters=unique(self.stack(name,fresh=False).get('Parameters',[]),'ParameterKey','ParameterValue')
            pseudo={'AWS::Region':self.policy['region'],'AWS::AccountId':self.policy['account_id'],'AWS::Partition':'aws','AWS::StackName':name}
            if ref in parameters:
                result=parameters[ref]
                return int(result) if self.template_cache[name].get('Parameters',{}).get(ref,{}).get('Type')=='Number' else result
            return pseudo[ref] if ref in pseudo else self.physical(name,ref)
        if set(value)=={'Fn::Sub'}:
            raw=value['Fn::Sub'];require(isinstance(raw,str),'shell-template-substitution-unsupported')
            return re.sub(r'\$\{([^}]+)\}',lambda m:str(self.resolve({'Fn::GetAtt':m[1].split('.',1)} if '.' in m[1] else {'Ref':m[1]},name)),raw)
        if set(value)=={'Fn::ImportValue'}:
            export=self.resolve(value['Fn::ImportValue'],name);foundation=self.policy['foundation_stack']
            outputs=self.template_cache[foundation].get('Outputs',{})
            matches=[key for key,item in outputs.items() if 'Export' in item and self.resolve(item['Export']['Name'],foundation)==export]
            require(len(matches)==1,'shell-template-import-unresolved')
            return unique(self.stack(foundation,fresh=False).get('Outputs',[]),'OutputKey','OutputValue')[matches[0]]
        if set(value)=={'Fn::Split'}:
            sep,raw=self.resolve(value['Fn::Split'],name);return raw.split(sep)
        if set(value)=={'Fn::Select'}:
            index,items=self.resolve(value['Fn::Select'],name);return items[int(index)]
        if set(value)=={'Fn::Join'}:
            sep,items=self.resolve(value['Fn::Join'],name);return sep.join(str(i) for i in items)
        if set(value)=={'Fn::GetAtt'}:
            logical,attribute=value['Fn::GetAtt'];physical=self.physical(name,logical);kind=self.template_cache[name]['Resources'][logical]['Type']
            if kind=='AWS::RDS::DBInstance' and attribute=='MasterUserSecret.SecretArn':
                values=self.aws('rds','describe-db-instances','--db-instance-identifier',physical).get('DBInstances',[])
                require(len(values)==1 and values[0].get('DBInstanceIdentifier')==physical,'shell-database-identity-unavailable')
                secret=values[0].get('MasterUserSecret',{}).get('SecretArn')
                require(isinstance(secret,str) and secret.startswith('arn:aws:secretsmanager:'),'shell-secret-reference-unavailable')
                return secret
            if attribute=='Arn':
                if physical.startswith('arn:'):return physical
                base='arn:aws:{service}:'+self.policy['region']+':'+self.policy['account_id']+':'
                if kind=='AWS::DynamoDB::Table':return base.format(service='dynamodb')+'table/'+physical
                if kind=='AWS::SSM::Parameter':return base.format(service='ssm')+'parameter/'+physical.lstrip('/')
                if kind=='AWS::SQS::Queue':return base.format(service='sqs')+physical.rsplit('/',1)[-1]
                if kind=='AWS::IAM::Role':return 'arn:aws:iam::'+self.policy['account_id']+':role/'+physical
            raise ValueError('shell-template-attribute-unsupported')
        require(not any(key.startswith('Fn::') for key in value),'shell-template-intrinsic-unsupported')
        return {key:self.resolve(item,name) for key,item in value.items()}

    def permissions(self,role_arns):
        name=self.policy['foundation_stack'];roles=self.template_cache[name]['Resources'];observations={}
        for arn in role_arns:
            matches=[item['Properties'] for item in roles.values() if item['Type']=='AWS::IAM::Role' and item['Properties'].get('RoleName')==arn.rsplit('/',1)[-1]]
            require(len(matches)==1,'shell-role-source-unmapped');props=self.resolve(matches[0],name);role=props['RoleName']
            actual=self.aws('iam','get-role','--role-name',role).get('Role',{})
            require(actual.get('Arn')==arn and actual.get('AssumeRolePolicyDocument')==props['AssumeRolePolicyDocument'],'shell-role-trust-mismatch')
            require(actual.get('PermissionsBoundary',{}).get('PermissionsBoundaryArn')==props.get('PermissionsBoundary'),'shell-role-boundary-mismatch')
            attached=self.aws('iam','list-attached-role-policies','--role-name',role)
            require(not attached.get('IsTruncated') and {p['PolicyArn'] for p in attached.get('AttachedPolicies',[])}==set(props.get('ManagedPolicyArns',[])),'shell-role-managed-policy-mismatch')
            inline=self.aws('iam','list-role-policies','--role-name',role);expected={i['PolicyName']:i['PolicyDocument'] for i in props.get('Policies',[])}
            require(not inline.get('IsTruncated') and set(inline.get('PolicyNames',[]))==set(expected),'shell-role-inline-policy-mismatch')
            for key,document in expected.items():require(self.aws('iam','get-role-policy','--role-name',role,'--policy-name',key).get('PolicyDocument')==document,'shell-role-permission-mismatch')
            managed={}
            for policy_arn in sorted(set(props.get('ManagedPolicyArns',[]))|({props['PermissionsBoundary']} if props.get('PermissionsBoundary') else set())):
                policy=self.aws('iam','get-policy','--policy-arn',policy_arn).get('Policy',{})
                require(policy.get('Arn')==policy_arn and isinstance(policy.get('DefaultVersionId'),str),'shell-managed-policy-identity-unavailable')
                version=self.aws('iam','get-policy-version','--policy-arn',policy_arn,'--version-id',policy['DefaultVersionId']).get('PolicyVersion',{})
                require(version.get('VersionId')==policy['DefaultVersionId'] and version.get('IsDefaultVersion') is True and isinstance(version.get('Document'),dict),'shell-managed-policy-version-unavailable')
                managed[policy_arn]={'version':version['VersionId'],'document':version['Document']}
            observations[arn]={'trust':actual['AssumeRolePolicyDocument'],'inline':expected,'managed':managed,'boundary':props.get('PermissionsBoundary')}
        return 'sha256:'+hashlib.sha256(json.dumps(observations,sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def runtime(self):
        self.source_alignment();name=self.policy['service_stack'];source=self.template_cache[name]
        parameters=unique(self.stack(name).get('Parameters',[]),'ParameterKey','ParameterValue');require(parameters.get('ImageUri')==self.image,'shell-runtime-image-mismatch')
        roles=set();expected_definitions={}
        for logical,item in source['Resources'].items():
            if item['Type']!='AWS::ECS::TaskDefinition' or logical=='CandidatePreflightTaskDefinition':continue
            expected=self.resolve(item['Properties'],name);reference=self.physical(name,logical)
            payload=self.aws('ecs','describe-task-definition','--task-definition',reference,'--include','TAGS');live=payload.get('taskDefinition',{});live['tags']=payload.get('tags',[])
            require(live.get('taskDefinitionArn')==reference and live.get('status')=='ACTIVE','shell-task-definition-unavailable')
            self.match(expected,live);roles.update((live['taskRoleArn'],live['executionRoleArn']));expected_definitions[logical]=reference
        permission_identity=self.permissions(roles)
        for logical,item in source['Resources'].items():
            if item['Type']!='AWS::ECS::Service':continue
            props=self.resolve(item['Properties'],name);expected=expected_definitions[item['Properties']['TaskDefinition']['Ref']]
            response=self.aws('ecs','describe-services','--cluster',props['Cluster'],'--services',props['ServiceName'])
            services=response.get('services',[]);require(not response.get('failures') and len(services)==1,'shell-service-unavailable');service=services[0]
            require(service.get('taskDefinition')==expected and service.get('desiredCount')==props['DesiredCount'] and service.get('runningCount')==props['DesiredCount'] and service.get('pendingCount')==0,'shell-service-not-steady')
            deployments=service.get('deployments',[]);require(len(deployments)==1 and deployments[0].get('rolloutState')=='COMPLETED','shell-service-rollout-incomplete')
            require(service.get('networkConfiguration')==props['NetworkConfiguration'] or self.matches(props['NetworkConfiguration'],service.get('networkConfiguration',{})),'shell-service-network-mismatch')
            listed=self.aws('ecs','list-tasks','--cluster',props['Cluster'],'--service-name',props['ServiceName'],'--desired-status','RUNNING');arns=listed.get('taskArns')
            require(isinstance(arns,list) and len(arns)==props['DesiredCount'] and not listed.get('nextToken'),'shell-service-task-observation-incomplete')
            if arns:
                tasks=self.aws('ecs','describe-tasks','--cluster',props['Cluster'],'--tasks',*arns)
                require(not tasks.get('failures') and {i.get('taskArn') for i in tasks.get('tasks',[])}==set(arns),'shell-service-task-observation-incomplete')
                for task in tasks['tasks']:
                    require(task.get('taskDefinitionArn')==expected and task.get('lastStatus')=='RUNNING' and task.get('healthStatus')=='HEALTHY','shell-runtime-not-healthy')
                    app=[i for i in task.get('containers',[]) if i.get('image')==self.image]
                    require(len(app)==1 and app[0].get('imageDigest')==self.digest,'shell-runtime-digest-mismatch')
        return {'schema':self.evidence.OBSERVATION_SCHEMA,'target':self.evidence.TARGET,'scope':self.evidence.SCOPE,'checked_at':datetime.now(timezone.utc).isoformat(),'source_revision':self.source,'image_digest':self.digest,**{key:self.manifest['source'][key] for key in ('workflow_run_id','workflow_path','repository')},'verdict':'passed','evidence_class':self.evidence_class,'permission_state_sha256':permission_identity,'checks':{key:'passed' for key in self.evidence.CHECKS},'input_files':self.evidence.source_inputs(self.root)}

    @staticmethod
    def matches(expected,actual):
        if isinstance(expected,dict):return isinstance(actual,dict) and all(Control.matches(value,actual.get(key[0].lower()+key[1:])) for key,value in expected.items())
        if isinstance(expected,list):return isinstance(actual,list) and len(expected)==len(actual) and all(Control.matches(a,b) for a,b in zip(expected,actual))
        return expected==actual

    def match(self,expected,actual):
        require(self.matches(expected,actual),'shell-task-configuration-mismatch')
        for desired,live in zip(expected['ContainerDefinitions'],actual.get('containerDefinitions',[])):
            for field in ('Command','EntryPoint','Environment','Secrets','MountPoints','LinuxParameters'):
                if field not in desired:require(not live.get(field[0].lower()+field[1:]),'shell-task-configuration-addition')

    def predecessor(self):
        evidence=self.evidence.within(self.root,self.manifest['acceptance']['evidence_root']);succession=self.evidence.succession(self.root,self.evidence_class);state=succession.current(evidence)
        actual=state['release_id'] if state else 'none';require(actual==self.args.expected_predecessor,'shell-release-predecessor-changed')
        if actual!='none':
            require(self.args.current_deployment_manifest is not None,'shell-current-manifest-required')
            previous=yaml.safe_load(Path(self.args.current_deployment_manifest).read_text())
            require(self.evidence.validate_ready(previous,root=self.root,evidence_class=self.evidence_class)==actual,'shell-current-release-not-ready')
        if self.args.mode=='service-rollback':
            record,bound=succession.compatibility_record(evidence,self.args.rollback_compatibility_id);identity=bound['identity']
            require(identity['source_revision']==self.source and identity['image_digest']==self.digest and identity['workloads']==['platform-shell'],'shell-rollback-compatibility-mismatch')
            proof=record.get('proof_set',{}).get('runtime-alignment');require(isinstance(proof,dict),'shell-rollback-runtime-proof-missing')
            observed=self.evidence.observation(evidence/proof['path'],source=self.source,image=self.digest,publication=self.manifest['source'],root=self.root,evidence_class=self.evidence_class,fresh=False)
            require(observed['input_files']==self.evidence.source_inputs(self.root),'shell-rollback-inputs-changed')
            previous=yaml.safe_load(Path(self.args.current_deployment_manifest).read_text())
            current_observation=json.loads(self.evidence.within(self.root,previous['acceptance']['current_observation']).read_text())
            require(observed.get('permission_state_sha256')==current_observation.get('permission_state_sha256'),'shell-rollback-permission-identity-changed')
            require(identity['configuration_contract']['path']==self.evidence.CONFIGURATION.as_posix() and identity['permission_contract']['path']==self.evidence.PERMISSIONS.as_posix(),'shell-rollback-contract-mismatch')
        elif actual!='none':
            history,_=succession.history_record_for_id(evidence,actual)
            while history:
                require(history['release']['image_digest']!=self.digest,'shell-retained-image-requires-rollback')
                prior=history.get('predecessor');history=succession.history_record_for_id(evidence,prior)[0] if prior else None

    def operation(self):
        change=self.aws('cloudformation','describe-change-set','--stack-name',self.policy['service_stack'],'--change-set-name',self.args.service_change_set,absent=True)
        if change is None:return {'verdict':'uncertain','reason':'shell-change-set-absent-no-replay'}
        require(change.get('ChangeSetName')==self.args.service_change_set or change.get('ChangeSetId')==self.args.service_change_set,'shell-change-set-identity-mismatch')
        status=change.get('Status');execution=change.get('ExecutionStatus')
        if status in {'CREATE_PENDING','CREATE_IN_PROGRESS'} or execution=='EXECUTE_IN_PROGRESS':return {'verdict':'pending','reason':'shell-operation-pending'}
        if status=='FAILED' or execution=='OBSOLETE':return {'verdict':'failed','reason':'shell-operation-failed'}
        if execution=='EXECUTE_COMPLETE':
            stack=self.aws('cloudformation','describe-stacks','--stack-name',self.policy['service_stack']).get('Stacks',[])
            require(len(stack)==1,'shell-stack-observation-invalid')
            if str(stack[0].get('StackStatus','')).endswith('_IN_PROGRESS'):return {'verdict':'pending','reason':'shell-stack-operation-pending'}
            if stack[0].get('StackStatus') not in {'CREATE_COMPLETE','UPDATE_COMPLETE'}:return {'verdict':'failed','reason':'shell-stack-operation-failed'}
            observed=self.runtime();return {'verdict':'passed','reason':'shell-operation-runtime-verified','observation':observed}
        require(status=='CREATE_COMPLETE' and execution=='AVAILABLE','shell-change-set-not-executable')
        if self.args.mode=='service-operation-status':return {'verdict':'pending','reason':'shell-change-set-reviewed-not-executed'}
        self.predecessor()
        preflight=module(self.root/'scripts/04.deploy/run-platform-shell-candidate-execution-preflight/script.py','shell_candidate_preflight')
        try:qualified=preflight.realization_preflight(self.args.realization_facts,self.args.realization_change_summary)
        except preflight.CandidatePreflightError as error:raise ValueError(str(error)) from None
        require(qualified==self.digest,'shell-candidate-preflight-artifact-mismatch')
        self.source_alignment(service=False)
        current=self.aws('cloudformation','describe-stacks','--stack-name',self.policy['service_stack'],absent=True)
        expected_type='CREATE' if self.args.expected_predecessor=='none' else 'UPDATE'
        if expected_type=='CREATE':require(current is None or current.get('Stacks',[{}])[0].get('StackStatus')=='REVIEW_IN_PROGRESS','shell-first-release-stack-not-absent')
        else:
            self.stack(self.policy['service_stack']);require(templates_equal(self.aws('cloudformation','get-template','--stack-name',self.policy['service_stack'],'--template-stage','Original').get('TemplateBody'),self.template_cache[self.policy['service_stack']]),'shell-service-configuration-change-unqualified');self.owner.check_reconciliation_live_role_policy(self.args,self.policy)
        require(change.get('ChangeSetType')==expected_type,'shell-change-set-type-mismatch')
        proposed=unique(change.get('Parameters',[]),'ParameterKey','ParameterValue');require(proposed.get('ImageUri')==self.image,'shell-change-set-image-mismatch')
        source=self.template_cache[self.policy['service_stack']]
        desired=self.aws('cloudformation','get-template','--stack-name',self.policy['service_stack'],'--change-set-name',self.args.service_change_set,'--template-stage','Original')
        require(templates_equal(desired.get('TemplateBody'),source),'shell-change-set-template-mismatch')
        prior=unique(current['Stacks'][0].get('Parameters',[]),'ParameterKey','ParameterValue') if expected_type=='UPDATE' else {key:str(item['Default']) for key,item in source.get('Parameters',{}).items() if 'Default' in item}
        for key,value in proposed.items():
            if key=='ImageUri' or (key=='CandidateImageUri' and expected_type=='CREATE' and value==self.image):continue
            require(key in prior and value==prior[key],'shell-change-set-configuration-change-unqualified')
        require(set(proposed)==set(source['Parameters']),'shell-change-set-parameters-incomplete')
        allowed={key for key,item in source['Resources'].items() if item['Type'] in {'AWS::ECS::TaskDefinition','AWS::ECS::Service'}}
        changes=change.get('Changes');require(isinstance(changes,list) and changes and not change.get('NextToken'),'shell-change-set-observation-incomplete')
        for entry in changes:
            item=entry.get('ResourceChange',{});logical=item.get('LogicalResourceId')
            require(logical in source['Resources'],'shell-change-set-resource-unknown')
            if expected_type=='UPDATE':require(logical in allowed and item.get('Action')=='Modify' and (source['Resources'][logical]['Type']!='AWS::ECS::Service' or item.get('Replacement')=='False'),'shell-change-set-scope-unqualified')
            else:require(item.get('Action')=='Add','shell-change-set-first-release-invalid')
        if expected_type=='CREATE':self.stack_cache[self.policy['service_stack']]={'StackStatus':'CREATE_COMPLETE','Parameters':[{'ParameterKey':key,'ParameterValue':value} for key,value in proposed.items()]}
        roles=set()
        for item in source['Resources'].values():
            if item['Type']=='AWS::ECS::TaskDefinition':
                for key in ('TaskRoleArn','ExecutionRoleArn'):roles.add(self.resolve(item['Properties'][key],self.policy['service_stack']))
        permission_identity=self.permissions(roles)
        if expected_type=='UPDATE':
            baseline=yaml.safe_load(Path(self.args.current_deployment_manifest).read_text())
            observed=json.loads(self.evidence.within(self.root,baseline['acceptance']['current_observation']).read_text())
            require(observed.get('permission_state_sha256')==permission_identity,'shell-current-permission-identity-changed')
        self.owner.check_reconciliation_live_role_policy(self.args,self.policy)
        for _identifier,check in self.owner.artifact_bucket_checks(self.args,self.policy):check()
        self.owner.check_budget(self.args,self.policy)
        if expected_type=='UPDATE':
            # Re-read immediately before mutation: retained acceptance is not a
            # substitute for the provider's current immutable image identity.
            _,accepted_digest=self.evidence.identity(baseline)
            accepted_image=baseline['artifacts']['image']['repository_uri']+'@'+accepted_digest
            latest=self.aws('cloudformation','describe-stacks','--stack-name',self.policy['service_stack']).get('Stacks',[])
            require(len(latest)==1 and latest[0].get('StackName')==self.policy['service_stack'] and latest[0].get('StackStatus') in {'CREATE_COMPLETE','UPDATE_COMPLETE'},'shell-current-stack-not-stable')
            current_parameters=unique(latest[0].get('Parameters',[]),'ParameterKey','ParameterValue')
            require(current_parameters.get('ImageUri')==accepted_image,'shell-current-image-identity-changed')
        self.aws('cloudformation','execute-change-set','--stack-name',self.policy['service_stack'],'--change-set-name',self.args.service_change_set,'--client-request-token',change['ChangeSetId'].rsplit('/',1)[-1],mutation=True)
        return {'verdict':'pending','reason':'shell-operation-submitted-reconcile-required'}


def run(owner,args,policy):
    try:
        control=Control(owner,args,policy);owner.check_identity(args,policy)
        if args.mode=='runtime-alignment':
            observed=control.runtime();path=control.evidence.within(control.root,control.manifest['acceptance']['current_observation']);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(observed,sort_keys=True)+'\n')
            candidate=control.evidence.write_candidate(control.manifest,path,control.evidence.within(control.root,control.manifest['acceptance']['evidence_root']),root=control.root,evidence_class=control.evidence_class)
            report={'verdict':'passed','reason':'shell-runtime-aligned',**candidate}
        else:report=control.operation()
        report.update({'schema':owner.SAFE_SCHEMA,'target':'kanbien/staging','mode':args.mode});print(json.dumps(report,sort_keys=True));return 0 if report['verdict']=='passed' else 1
    except (ValueError,KeyError,TypeError,OSError,yaml.YAMLError,owner.ReconciliationError) as error:
        reason=str(error) if isinstance(error,(ValueError,owner.ReconciliationError)) and re.fullmatch(r'[a-z][a-z0-9-]+',str(error)) else 'shell-release-input-invalid'
        print(json.dumps({'schema':owner.SAFE_SCHEMA,'target':'kanbien/staging','mode':args.mode,'verdict':'uncertain' if 'uncertain' in reason or 'unavailable' in reason else 'blocked','reason':reason},sort_keys=True));return 1
