"""Offline immutable deployed revision and task-response binding regressions."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.relational-task-revision-binding
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines: [security, sre]
#   kind: test
#   purpose: Prevent mutable family resolution or conflicting provider observations from satisfying task completion.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.run-platform-shell-postgresql-relational-smoke.smoke-test
#     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/smoke-test.sh

from copy import deepcopy
import contextlib
import io
import sys
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('relational_revision_controller',Path(__file__).with_name('script.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
PREFIX='arn:aws:ecs:eu-west-1:337159794548:'
IMAGE='337159794548.dkr.ecr.eu-west-1.amazonaws.com/platform-shell@sha256:'+'a'*64
STACK='kanbien-staging-platform-shell-service'
STAGES=('bootstrap','migration','relay','worker','restore_verification')


def policy():
    return {'service_stack':STACK,'cluster':PREFIX+'cluster/kanbien-staging','task_wait_seconds':900,
            'families':{stage:'kanbien-staging-platform-relational-'+('restore-verify' if stage=='restore_verification' else stage) for stage in STAGES},
            'containers':{stage:'relational-'+('restore-verify' if stage=='restore_verification' else stage) for stage in STAGES},
            'labels':{stage:'fixed-'+stage for stage in STAGES}}


def arn(stage='bootstrap',revision=7):return PREFIX+'task-definition/'+policy()['families'][stage]+':'+str(revision)

def stack():
    return {'Stacks':[{'StackName':STACK,'StackId':'arn:aws:cloudformation:eu-west-1:337159794548:stack/'+STACK+'/12345678-1234-1234-1234-123456789abc',
                       'StackStatus':'UPDATE_COMPLETE','Outputs':[{'OutputKey':c.TASK_OUTPUTS[stage],'OutputValue':arn(stage)} for stage in STAGES],
                       'Parameters':[{'ParameterKey':'ImageUri','ParameterValue':IMAGE}]}]}


def definition(stage='bootstrap'):
    return {'taskDefinition':{'taskDefinitionArn':arn(stage),'family':policy()['families'][stage], 'revision':7,'status':'ACTIVE',
        'networkMode':'awsvpc','requiresCompatibilities':['FARGATE'],'containerDefinitions':[{'name':policy()['containers'][stage],
        'image':IMAGE,'command':deepcopy(c.TASK_COMMANDS[stage]),'essential':True,'portMappings':[]}]}}


def task(stage='bootstrap',status='STOPPED'):
    return {'taskArn':PREFIX+'task/kanbien-staging/'+'b'*32,'taskDefinitionArn':arn(stage),'clusterArn':policy()['cluster'],
            'startedBy':policy()['labels'][stage],'launchType':'FARGATE','lastStatus':status,
            'containers':[{'name':policy()['containers'][stage],'exitCode':0}]}


class Definitions(unittest.TestCase):
    def refuse_stack(self,value):
        with patch.object(c,'aws',return_value=value) as aws:
            with self.assertRaises(c.RelationalSmokeError) as caught:c.assert_task_definition('bootstrap',policy())
        self.assertEqual(aws.call_count,1);self.assertNotIn('arn:',str(caught.exception));self.assertNotIn(IMAGE,str(caught.exception))
    def refuse_definition(self,value):
        with patch.object(c,'aws',side_effect=[stack(),value]) as aws:
            with self.assertRaises(c.RelationalSmokeError) as caught:c.assert_task_definition('bootstrap',policy())
        self.assertEqual(aws.call_args.args[0],['ecs','describe-task-definition','--task-definition',arn()])
        self.assertNotIn('arn:',str(caught.exception))
    def test_every_fixed_stage_returns_exact_stack_revision(self):
        for stage in STAGES:
            with self.subTest(stage=stage),patch.object(c,'aws',side_effect=[stack(),definition(stage)]) as aws:
                self.assertEqual(c.assert_task_definition(stage,policy()),arn(stage))
                self.assertEqual(aws.call_args.args[0][-1],arn(stage))
                self.assertEqual(aws.call_args_list[0].args[0],['cloudformation','describe-stacks','--stack-name',STACK])
    def test_unknown_stage_never_reads_provider(self):
        with patch.object(c,'aws') as aws:
            with self.assertRaises(c.RelationalSmokeError):c.assert_task_definition('arbitrary',policy())
            aws.assert_not_called()
    def test_duplicate_unselected_output_is_also_refused(self):
        value=stack();value['Stacks'][0]['Outputs'].append(deepcopy(value['Stacks'][0]['Outputs'][1]));self.refuse_stack(value)
    def test_duplicate_unrelated_parameter_is_refused(self):
        value=stack();value['Stacks'][0]['Parameters'] += [{'ParameterKey':'Other','ParameterValue':'one'},{'ParameterKey':'Other','ParameterValue':'two'}];self.refuse_stack(value)
    def test_missing_selected_output(self):
        value=stack();value['Stacks'][0]['Outputs'].pop(0);self.refuse_stack(value)
    def test_more_than_one_stack(self):
        value=stack();value['Stacks'].append(deepcopy(value['Stacks'][0]));self.refuse_stack(value)
    def test_missing_definition(self):self.refuse_definition({})
    def test_duplicate_container(self):
        value=definition();value['taskDefinition']['containerDefinitions'].append(deepcopy(value['taskDefinition']['containerDefinitions'][0]));self.refuse_definition(value)
    def test_nonempty_entrypoint_refused(self):
        value=definition();value['taskDefinition']['containerDefinitions'][0]['entryPoint']=['/bin/sh','-c'];self.refuse_definition(value)
    def test_preflight_mode_cannot_substitute_effect_command(self):
        value=definition();value['taskDefinition']['containerDefinitions'][0]['command'].append('--preflight');self.refuse_definition(value)


def stack_mutation(name,change):
    def test(self):value=stack();change(value['Stacks'][0]);self.refuse_stack(value)
    setattr(Definitions,'test_stack_'+name,test)
for name,change in [
 ('wrong_name',lambda v:v.update(StackName='other')),
 ('wrong_account',lambda v:v.update(StackId=v['StackId'].replace('337159794548','111111111111'))),
 ('wrong_region',lambda v:v.update(StackId=v['StackId'].replace('eu-west-1','us-east-1'))),
 ('wrong_stack_id_name',lambda v:v.update(StackId=v['StackId'].replace(STACK,'other'))),
 ('missing_id',lambda v:v.pop('StackId')),
 ('malformed_id',lambda v:v.update(StackId='private-provider-canary')),
 ('in_progress',lambda v:v.update(StackStatus='UPDATE_IN_PROGRESS')),
 ('outputs_missing',lambda v:v.pop('Outputs')),
 ('outputs_malformed',lambda v:v.update(Outputs='private-provider-canary')),
 ('output_row_malformed',lambda v:v['Outputs'].append('private-provider-canary')),
 ('output_value_empty',lambda v:v['Outputs'][0].update(OutputValue='')),
 ('duplicate_selected_output',lambda v:v['Outputs'].append(deepcopy(v['Outputs'][0]))),
 ('wrong_task_account',lambda v:v['Outputs'][0].update(OutputValue=arn().replace('337159794548','111111111111'))),
 ('wrong_task_region',lambda v:v['Outputs'][0].update(OutputValue=arn().replace('eu-west-1','us-east-1'))),
 ('wrong_task_family',lambda v:v['Outputs'][0].update(OutputValue=arn('migration'))),
 ('unrevisioned_arn',lambda v:v['Outputs'][0].update(OutputValue=arn().rsplit(':',1)[0])),
 ('family_name',lambda v:v['Outputs'][0].update(OutputValue=policy()['families']['bootstrap'])),
 ('family_revision_short',lambda v:v['Outputs'][0].update(OutputValue=policy()['families']['bootstrap']+':7')),
 ('latest_revision',lambda v:v['Outputs'][0].update(OutputValue=arn().rsplit(':',1)[0]+':latest')),
 ('zero_revision',lambda v:v['Outputs'][0].update(OutputValue=arn(revision=0))),
 ('leading_zero_revision',lambda v:v['Outputs'][0].update(OutputValue=arn(revision='07'))),
 ('newline_revision',lambda v:v['Outputs'][0].update(OutputValue=arn()+'\n')),
 ('parameter_missing',lambda v:v.update(Parameters=[])),
 ('duplicate_image',lambda v:v['Parameters'].append(deepcopy(v['Parameters'][0]))),
 ('image_tag',lambda v:v['Parameters'][0].update(ParameterValue=IMAGE.split('@')[0]+':latest')),
 ('image_wrong_repository',lambda v:v['Parameters'][0].update(ParameterValue=IMAGE.replace('/platform-shell@','/other@'))),
 ('image_wrong_account',lambda v:v['Parameters'][0].update(ParameterValue=IMAGE.replace('337159794548','111111111111'))),
]:stack_mutation(name,change)


def definition_mutation(name,change):
    def test(self):value=definition();change(value['taskDefinition']);self.refuse_definition(value)
    setattr(Definitions,'test_definition_'+name,test)
for name,change in [
 ('wrong_returned_arn',lambda v:v.update(taskDefinitionArn=arn(revision=8))),
 ('missing_returned_arn',lambda v:v.pop('taskDefinitionArn')),
 ('wrong_family',lambda v:v.update(family=policy()['families']['migration'])),
 ('wrong_revision',lambda v:v.update(revision=8)),
 ('boolean_revision',lambda v:v.update(revision=True)),
 ('string_revision',lambda v:v.update(revision='7')),
 ('inactive',lambda v:v.update(status='INACTIVE')),
 ('wrong_network',lambda v:v.update(networkMode='host')),
 ('ec2',lambda v:v.update(requiresCompatibilities=['EC2'])),
 ('wrong_container',lambda v:v['containerDefinitions'][0].update(name='other')),
 ('wrong_command',lambda v:v['containerDefinitions'][0].update(command=['/tmp/other.js'])),
 ('wrong_image_digest',lambda v:v['containerDefinitions'][0].update(image=IMAGE[:-1]+'b')),
 ('tagged_image',lambda v:v['containerDefinitions'][0].update(image='private-provider-canary:latest')),
 ('port',lambda v:v['containerDefinitions'][0].update(portMappings=[{'containerPort':8080}])),
 ('not_essential',lambda v:v['containerDefinitions'][0].update(essential=False)),
]:definition_mutation(name,change)


class Execution(unittest.TestCase):
    def execute(self,launch=None,observations=None):
        calls=[];responses=list(observations or [{'tasks':[task()]}])
        def aws(arguments,policy):
            calls.append(arguments)
            if arguments[:2]==['cloudformation','describe-stacks']:return stack()
            if arguments[:2]==['ecs','describe-task-definition']:
                self.assertEqual(arguments[-1],arn());return definition()
            if arguments[:2]==['ecs','list-tasks']:return {'taskArns':[]}
            if arguments[:2]==['ecs','run-task']:
                # Simulate a new latest family revision appearing after inspection.
                selected=arguments[arguments.index('--task-definition')+1]
                self.assertEqual(selected,arn())
                current=task(status='PENDING')
                if selected==policy['families']['bootstrap']:current['taskDefinitionArn']=arn(revision=99)
                return launch if launch is not None else {'tasks':[current],'failures':[]}
            if arguments[:2]==['ecs','describe-tasks']:
                self.assertEqual(arguments[-1],task()['taskArn']);return responses.pop(0)
            self.fail('unexpected provider operation')
        with patch.object(c,'aws',side_effect=aws),patch.object(c.time,'sleep'):
            c.run_and_wait('bootstrap','fixed-network',policy())
        return calls
    def test_execution_uses_exact_revision_even_if_latest_changes(self):
        calls=self.execute()
        run=next(args for args in calls if args[:2]==['ecs','run-task'])
        self.assertEqual(run[run.index('--task-definition')+1],arn())
        self.assertEqual([args[-1] for args in calls if args[:2]==['ecs','list-tasks']],['RUNNING','STOPPED'])
    def test_running_then_stopped_rechecks_identity(self):
        calls=self.execute(observations=[{'tasks':[task(status='RUNNING')]},{'tasks':[task()]}])
        self.assertEqual(sum(args[:2]==['ecs','describe-tasks'] for args in calls),2)
    def test_launch_failure_refused(self):
        with self.assertRaises(c.RelationalSmokeError):self.execute(launch={'tasks':[task()],'failures':[{'reason':'private-provider-canary'}]})
    def test_poll_failure_refused(self):
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[task()],'failures':[{'reason':'private-provider-canary'}]}])
    def test_duplicate_terminal_container_refused(self):
        value=task();value['containers'].append(deepcopy(value['containers'][0]))
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
    def test_boolean_exit_zero_refused(self):
        value=task();value['containers'][0]['exitCode']=False
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
    def test_missing_terminal_container_refused(self):
        value=task();value.pop('containers')
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
    def test_wrong_terminal_container_refused(self):
        value=task();value['containers'][0]['name']='other'
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
    def test_failed_terminal_exit_refused(self):
        value=task();value['containers'][0]['exitCode']=1
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
    def test_ambiguous_tasks_refused(self):
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[task(),task()]}])
    def test_missing_task_refused(self):
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[]}])
    def test_fixed_environment_override_retains_exact_revision(self):
        with patch.object(c,'assert_task_definition',return_value=arn('restore_verification')),patch.object(c,'no_prior_label'),patch.object(c,'aws',side_effect=[{'tasks':[task('restore_verification',status='PENDING')]},{'tasks':[task('restore_verification')]}]) as aws:
            c.run_and_wait('restore_verification','fixed-network',policy(),[{'name':'RELATIONAL_RESTORE_HOST','value':'isolated-private-endpoint'}])
        args=aws.call_args_list[0].args[0]
        self.assertEqual(args[args.index('--task-definition')+1],arn('restore_verification'))
        self.assertIn('--overrides',args)


def identity_mutation(name,change):
    def launch(self):
        value=task(status='PENDING');change(value)
        with self.assertRaises(c.RelationalSmokeError) as caught:self.execute(launch={'tasks':[value]})
        self.assertNotIn('private-provider-canary',str(caught.exception))
    def poll(self):
        value=task();change(value)
        with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
    setattr(Execution,'test_launch_'+name,launch);setattr(Execution,'test_poll_'+name,poll)
for name,change in [
 ('wrong_revision',lambda v:v.update(taskDefinitionArn=arn(revision=99))),
 ('missing_revision',lambda v:v.pop('taskDefinitionArn')),
 ('wrong_cluster',lambda v:v.update(clusterArn=PREFIX+'cluster/other')),
 ('wrong_label',lambda v:v.update(startedBy='other')),
 ('wrong_launch_type',lambda v:v.update(launchType='EC2')),
 ('wrong_account',lambda v:v.update(taskArn=v['taskArn'].replace('337159794548','111111111111'))),
 ('wrong_region',lambda v:v.update(taskArn=v['taskArn'].replace('eu-west-1','us-east-1'))),
 ('wrong_cluster_arn',lambda v:v.update(taskArn=v['taskArn'].replace('/kanbien-staging/','/other/'))),
 ('malformed_task',lambda v:v.update(taskArn='private-provider-canary')),
]:identity_mutation(name,change)


def wrong_task_identity(self):
    value=task();value['taskArn']=value['taskArn'][:-1]+'c'
    with self.assertRaises(c.RelationalSmokeError):self.execute(observations=[{'tasks':[value]}])
Execution.test_poll_different_valid_task_identity=wrong_task_identity

class ExistingPublicBoundary(unittest.TestCase):
    def test_execution_modes_still_require_the_existing_approval(self):
        for mode in ('--execute','--execute-bootstrap-recovery','--execute-recovery-continuation','--diagnose-bootstrap-recovery'):
            with self.subTest(mode=mode),patch.object(sys,'argv',['script.py',mode]),contextlib.redirect_stderr(io.StringIO()),patch.object(c,'aws') as aws:
                with self.assertRaises(SystemExit) as caught:c.arguments()
                self.assertEqual(caught.exception.code,2);aws.assert_not_called()
    def test_binding_failure_remains_fixed_public_failure(self):
        output=io.StringIO()
        with patch.object(sys,'argv',['script.py','--execute','--approve-relational-stage6']),patch.object(c,'load_policy',return_value=policy()),patch.object(c,'execute',side_effect=c.RelationalSmokeError('private-provider-canary')),contextlib.redirect_stdout(output):
            self.assertEqual(c.main(),1)
        self.assertEqual(output.getvalue(),'{'+'"postgresql_relational_smoke":"failed"'+'}'+chr(10))


if __name__=='__main__':unittest.main()
