"""Isolation, ownership, observation and failure checks for real dependency execution."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.dependency-effect-engine
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: test
#   purpose: Reject dependency escape, wrong ownership, unbounded commands and cleanup uncertainty.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.script.operational-realization-gate.smoke-test
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dependency_effect_engine as e
import dependency_effect_contracts as c

D='sha256:'+'a'*64
ID='a'*64


def specification():
    return {'image':D,'entrypoint':[e.containers.NODE],'command':c.COMMANDS['bootstrap'],'user':'65532:65532',
            'tmpfs':{'/tmp':'rw,noexec,nosuid,nodev,size=16m,uid=65532'},'source':'/private/ca','destination':'/run/release-control',
            'environment':{'NODE_ENV':'production'}}


def inspection():
    spec=specification()
    return {'Image':D,'Config':{'Image':D,'Entrypoint':spec['entrypoint'],'Cmd':spec['command'],'User':spec['user'],
                             'WorkingDir':'/app','Env':['NODE_ENV=production']},
            'HostConfig':{'NetworkMode':'owned-network','ReadonlyRootfs':True,'Privileged':False,'CapDrop':['ALL'],
                          'CapAdd':None,'SecurityOpt':['no-new-privileges'],'Memory':536870912,'MemorySwap':536870912,
                          'NanoCpus':1000000000,'PidsLimit':128,'IpcMode':'none','Binds':None,'PortBindings':{},
                          'PublishAllPorts':False,'Tmpfs':spec['tmpfs'],'RestartPolicy':{'Name':'no'},
                          'LogConfig':{'Type':'none'},'Devices':[],'DeviceRequests':None},
            'State':{'Running':False,'OOMKilled':False,'ExitCode':0},
            'Mounts':[{'Type':'bind','Source':spec['source'],'Destination':spec['destination'],'RW':False}],
            'NetworkSettings':{'Networks':{'owned-network':{}}}}


class Engine(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.engine=e.DependencyEngine(Path(self.temporary.name))
        self.engine.network={'name':'owned-network','id':ID,'token':'b'*32}
        self.engine.specs['owned']=specification()
    def tearDown(self):self.temporary.cleanup()
    def check(self,value):
        with patch.object(self.engine,'inspect_network'),patch.object(self.engine,'_container',return_value=value):
            return self.engine.inspect_bound('owned',running=False)
    def test_valid_isolation(self):self.assertFalse(self.check(inspection())['Running'])
    def test_original_engine_defaults_unchanged(self):
        self.assertEqual(e.containers.SETTINGS['network'],'none')
        self.assertEqual(e.containers.SETTINGS['host_mounts'],[])
    def test_arbitrary_sql_refused_before_transport(self):
        with patch.object(self.engine,'_execute') as transport:
            with self.assertRaises(c.release.ReleaseFailure):self.engine.sql('DROP DATABASE production')
            transport.assert_not_called()
    def test_arbitrary_job_refused(self):
        with self.assertRaises(c.release.ReleaseFailure):self.engine.run_task(D,'shell','bootstrap','succeeded')
    def test_duplicate_environment_refused(self):
        with self.assertRaises(c.release.ReleaseFailure):e.decode_environment(['A=1','A=2'])
    def test_malformed_environment_refused(self):
        with self.assertRaises(c.release.ReleaseFailure):e.decode_environment(['password'])
    def test_dependency_wrong_version(self):
        value=json.loads((Path(__file__).resolve().parent/'dependency-image.lock.json').read_text())
        with patch.object(self.engine,'_call',return_value=json.dumps([{'Id':D,'Os':'linux','Architecture':'arm64'}]).encode()):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.dependency_identity(value)
    def test_unexpected_observer_failure_redacted(self):
        with patch.object(self.engine,'inspect_bound'),patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],1,b'',b'private')):
            self.engine.db='owned';self.engine._owned['owned']={'id':ID}
            with self.assertRaises(c.release.ReleaseFailure) as caught:self.engine.sql('state')
            self.assertNotIn('private',str(caught.exception))
    def test_expected_failure_must_fail(self):
        with patch.object(self.engine,'inspect_bound'),patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],0,b'',b'')):
            self.engine.db='owned';self.engine._owned['owned']={'id':ID}
            with self.assertRaises(c.release.ReleaseFailure):self.engine.sql('runtime-denied',expected_failure=True)
    def test_network_foreign_container_rejected(self):
        value={'Name':'owned-network','Id':ID,'Labels':{e.LABEL:'b'*32},'Internal':True,'Driver':'bridge',
               'Scope':'local','Ingress':False,'Containers':{'f'*64:{}}}
        with patch.object(self.engine,'_call',return_value=json.dumps([value]).encode()):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.inspect_network()
    def test_cleanup_refuses_unknown_owner(self):
        self.engine._owned['owned']={'id':ID}
        with patch.object(self.engine,'_cleanup',side_effect=e.containers.EngineFailure('local-container-container-ownership-mismatch')),patch.object(self.engine,'inspect_network',side_effect=c.release.ReleaseFailure('unknown')):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.cleanup_all()
    def test_grant_query_requires_each_privilege(self):
        # PostgreSQL comma-separated privileges mean ANY; each required privilege must be independent.
        self.assertNotIn("'SELECT,INSERT,UPDATE,DELETE'",e.STATE_SQL)
        for right in ['SELECT','INSERT','UPDATE','DELETE']:
            self.assertIn("has_table_privilege('psmokeruntime',c.oid,'"+right+"')",e.STATE_SQL)
    def test_product_working_directory(self):
        value=inspection();value['Config']['WorkingDir']='/tmp'
        with self.assertRaises(c.release.ReleaseFailure):self.check(value)
    def test_bad_tls_observation(self):
        self.engine.db='owned';self.engine._owned['owned']={'id':ID}
        with patch.object(self.engine,'inspect_bound'),patch.object(self.engine,'_call',return_value=b'false\n'):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.verify_tls()

    def test_lost_create_response_reconciles_owned_network_for_cleanup(self):
        self.engine.network['id']=None
        value={'Name':'owned-network','Id':ID,'Labels':{e.LABEL:'b'*32},'Internal':True,'Driver':'bridge',
               'Scope':'local','Ingress':False,'Containers':{}}
        with patch.object(self.engine,'_call',side_effect=[json.dumps([value]).encode(),b'owned-network',b'']):
            self.engine.cleanup_all()
        self.assertIsNone(self.engine.network)
    def test_lost_response_foreign_network_not_adopted(self):
        self.engine.network['id']=None
        value={'Name':'owned-network','Id':ID,'Labels':{e.LABEL:'wrong'},'Internal':True,'Driver':'bridge',
               'Scope':'local','Ingress':False,'Containers':{}}
        with patch.object(self.engine,'_call',return_value=json.dumps([value]).encode()):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.inspect_network()
        self.assertIsNone(self.engine.network['id'])
    def test_known_network_id_change_rejected(self):
        value={'Name':'owned-network','Id':'f'*64,'Labels':{e.LABEL:'b'*32},'Internal':True,'Driver':'bridge',
               'Scope':'local','Ingress':False,'Containers':{}}
        with patch.object(self.engine,'_call',return_value=json.dumps([value]).encode()):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.inspect_network()
    def test_observer_wrong_failure_is_not_permission_proof(self):
        self.engine.db='owned';self.engine._owned['owned']={'id':ID}
        with patch.object(self.engine,'inspect_bound'),patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],3,b'',b'ERROR: 42P01')):
            with self.assertRaises(c.release.ReleaseFailure):self.engine.sql('runtime-denied',expected_failure=True)
    def test_observer_permission_denial(self):
        self.engine.db='owned';self.engine._owned['owned']={'id':ID}
        with patch.object(self.engine,'inspect_bound'),patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],3,b'',b'ERROR: 42501\n')):
            self.assertEqual(self.engine.sql('runtime-denied',expected_failure=True),b'')
    def test_migration_has_no_bootstrap_or_runtime_credentials(self):
        self.engine._owned['owned']={'id':ID}
        terminal=json.dumps({'level':'info','message':'kanbien-platform.relational-smoke.migration_completed','fields':{'outcome':'succeeded'}}).encode()
        with patch.object(self.engine,'_create_bound',return_value='owned') as create,patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],0,terminal,b'')),patch.object(self.engine,'inspect_bound',return_value={'ExitCode':0}),patch.object(self.engine,'_cleanup'):
            self.engine.run_task(D,'migration','migration','succeeded')
        self.assertEqual(set(create.call_args.kwargs['environment']),{'RELATIONAL_MIGRATION_SECRET_JSON','RELATIONAL_CONFIG_JSON','RELATIONAL_TLS_CA_MODE','RELATIONAL_LOCAL_QUALIFICATION_ID'})
    def test_bootstrap_has_no_unneeded_configuration(self):
        self.engine._owned['owned']={'id':ID}
        terminal=json.dumps({'level':'info','message':'kanbien-platform.relational-smoke.bootstrap_completed','fields':{'outcome':'succeeded'}}).encode()
        with patch.object(self.engine,'_create_bound',return_value='owned') as create,patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],0,terminal,b'')),patch.object(self.engine,'inspect_bound',return_value={'ExitCode':0}),patch.object(self.engine,'_cleanup'):
            self.engine.run_task(D,'bootstrap','bootstrap','succeeded')
        self.assertEqual(set(create.call_args.kwargs['environment']),{'RELATIONAL_MASTER_SECRET_JSON','RELATIONAL_MIGRATION_SECRET_JSON','RELATIONAL_RUNTIME_SECRET_JSON','RELATIONAL_TLS_CA_MODE','RELATIONAL_LOCAL_QUALIFICATION_ID'})

    def test_runtime_sql_authenticates_runtime_over_verified_tls(self):
        self.engine.db='owned';self.engine._owned['owned']={'id':ID}
        with patch.object(self.engine,'inspect_bound'),patch.object(self.engine,'_execute',return_value=subprocess.CompletedProcess([],0,b'',b'')) as execute:
            self.engine.sql('runtime-dml')
        args=execute.call_args.args[0]
        self.assertIn('PGSSLMODE=verify-full',args)
        self.assertIn('PGPASSFILE=/tmp/runtime.pgpass',args)
        self.assertEqual(args[args.index('-h')+1],e.HOST)
        self.assertEqual(args[args.index('-U')+1],'psmokeruntime')
        self.assertNotIn('SET LOCAL ROLE',args[-1])

    def test_dependency_early_exit_is_start_failure(self):
        self.engine._owned['owned']={'id':ID}
        with patch.object(self.engine,'_create_bound',return_value='owned'),patch.object(self.engine,'_call',return_value=b''),patch.object(self.engine,'inspect_bound',return_value={'Running':False}):
            with self.assertRaises(c.release.ReleaseFailure) as caught:self.engine.start_dependency(D)
        self.assertEqual(caught.exception.code,'dependency-effect-dependency-start-failed')


def mutation(name,path,bad):
    def test(self):
        value=inspection();node=value
        for key in path[:-1]:node=node[key]
        node[path[-1]]=bad
        with self.assertRaises(c.release.ReleaseFailure):self.check(value)
    setattr(Engine,'test_reject_'+name,test)

for name,path,bad in [
 ('host_network',['HostConfig','NetworkMode'],'host'),('external_network',['HostConfig','NetworkMode'],'bridge'),
 ('privileged',['HostConfig','Privileged'],True),('root',['Config','User'],'0:0'),
 ('write_root',['HostConfig','ReadonlyRootfs'],False),('published_port',['HostConfig','PortBindings'],{'5432/tcp':[{'HostPort':'5432'}]}),
 ('docker_socket',['Mounts',0,'Source'],'/var/run/docker.sock'),('writable_mount',['Mounts',0,'RW'],True),
 ('mount_target',['Mounts',0,'Destination'],'/app'),('image',['Image'],'sha256:'+'b'*64),
 ('shell',['Config','Entrypoint'],['/bin/sh']),('env_secret',['Config','Env'],['NODE_ENV=production','AWS_ACCESS_KEY_ID=private']),
 ('restarted',['HostConfig','RestartPolicy','Name'],'always'),('logging',['HostConfig','LogConfig','Type'],'json-file'),
 ('unbounded_memory',['HostConfig','Memory'],0),('oom',['State','OOMKilled'],True),('still_running',['State','Running'],True),
 ('extra_network',['NetworkSettings','Networks'],{'owned-network':{},'bridge':{}}),
]:mutation(name,path,bad)

if __name__=='__main__':unittest.main()
