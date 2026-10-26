#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.platform-shell-relational-package
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Qualify actual packaged relational task commands with disposable TLS PostgreSQL and a local SQS protocol fixture.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.script.smoke-test-platform-shell-image
#     path: scripts/04.deploy/smoke-test-platform-shell-image/script.sh
"""Exercise the five actual packaged relational CLIs against disposable TLS PostgreSQL and a local SQS protocol fixture."""
import argparse
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

RESTORE_HOST='kanbien-staging-platform-relational-restore-proof-package.fixture.eu-west-1.rds.amazonaws.com'
QUEUE_FIXTURE=r'''
const http=require('http'),crypto=require('crypto'),{Pool}=require('pg'); let message, acknowledged=0;
const pool=new Pool({host:'postgres',port:5432,database:'platformsmoke',user:'fixture_root',password:'synthetic-root',ssl:{ca:require('fs').readFileSync('/fixture-ca.crt','utf8'),rejectUnauthorized:true}});
const md5=value=>crypto.createHash('md5').update(value).digest('hex');
http.createServer((req,res)=>{let body='';req.on('data',b=>body+=b);req.on('end',async()=>{
 try { const value=body?JSON.parse(body):{}; const operation=String(req.headers['x-amz-target']||'').split('.').pop(); let result={};
 if(operation==='SendMessage'){message=value.MessageBody;result={MessageId:'00000000-0000-4000-8000-000000000001',MD5OfMessageBody:md5(message)};}
 else if(operation==='ReceiveMessage'){result={Messages:message?[{MessageId:'00000000-0000-4000-8000-000000000001',ReceiptHandle:'synthetic-receipt',Body:message,MD5OfBody:md5(message),Attributes:{ApproximateReceiveCount:'1'}}]:[]};}
 else if(operation==='DeleteMessage'){if(value.ReceiptHandle!=='synthetic-receipt')throw Error();const proof=await pool.query("SELECT COUNT(*)::text AS count FROM platform_smoke.platform_processing WHERE state='completed' AND completion_outcome='succeeded' AND completed_at IS NOT NULL");if(proof.rows[0].count!=='1')throw Error();message=undefined;acknowledged++;}
 else if(req.url==='/proof'){result={acknowledged};}
 else {res.statusCode=400;result={__type:'InvalidAction'};}
 res.setHeader('Content-Type','application/x-amz-json-1.0');res.end(JSON.stringify(result));
 }catch{res.statusCode=400;res.end('{}');}
 });}).listen(9324,'0.0.0.0');
'''

def command(argv, *, input=None, check=True):
    result=subprocess.run(argv,input=input,capture_output=True,text=True,timeout=120)
    if check and result.returncode:raise RuntimeError('package-command-failed:'+argv[0]+':'+str(result.returncode))
    return result

def docker(*args,**kwargs):return command(['docker',*args],**kwargs)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image',required=True);args=parser.parse_args()
    if not re.fullmatch(r'(?:.+@)?sha256:[0-9a-f]{64}',args.image):raise RuntimeError('immutable-image-required')
    suffix=uuid.uuid4().hex[:12];network='shell-package-'+suffix;database=network+'-db';restored=network+'-restore';queue=network+'-queue';volume=network+'-cert'
    containers=[];network_created=False;volume_created=False;original=None
    with tempfile.TemporaryDirectory(prefix='shell-package-') as directory:
        root=Path(directory)
        try:
            command(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(root/'ca.key'),'-out',str(root/'ca.crt'),'-subj','/CN=package-ca','-days','1'])
            command(['openssl','req','-newkey','rsa:2048','-nodes','-keyout',str(root/'server.key'),'-out',str(root/'server.csr'),'-subj','/CN=postgres'])
            (root/'server.ext').write_text('subjectAltName=DNS:postgres,DNS:'+RESTORE_HOST+'\n')
            command(['openssl','x509','-req','-in',str(root/'server.csr'),'-CA',str(root/'ca.crt'),'-CAkey',str(root/'ca.key'),'-CAcreateserial','-out',str(root/'server.crt'),'-days','1','-extfile',str(root/'server.ext')])
            network_created=True;docker('network','create','--internal',network)
            volume_created=True;docker('volume','create',volume)
            containers.append(network+'-task')
            docker('run','--rm','--name',network+'-task','--user','root','-v',str(root)+':/source:ro','-v',volume+':/certs','postgres:16-bookworm','bash','-ec','cp /source/server.crt /source/server.key /certs/; chown 999:999 /certs/*; chmod 600 /certs/server.key')
            for name,alias in [(database,'postgres'),(restored,RESTORE_HOST)]:
                containers.append(name)
                docker('run','-d','--rm','--name',name,'--network',network,'--network-alias',alias,'-e','POSTGRES_DB=platformsmoke','-e','POSTGRES_USER=fixture_root','-e','POSTGRES_PASSWORD=synthetic-root','-v',volume+':/certs:ro','postgres:16-bookworm','postgres','-c','ssl=on','-c','ssl_cert_file=/certs/server.crt','-c','ssl_key_file=/certs/server.key')
                for attempt in range(40):
                    if docker('exec',name,'pg_isready','-U','fixture_root','-d','platformsmoke',check=False).returncode==0:break
                    time.sleep(.25)
                else:raise RuntimeError('disposable-database-unavailable')
            containers.append(queue)
            docker('run','-d','--rm','--name',queue,'--network',network,'--network-alias','queue','-v',str(root/'ca.crt')+':/fixture-ca.crt:ro','--entrypoint','/nodejs/bin/node',args.image,'-e',QUEUE_FIXTURE)
            # Credentials below are generated fixture strings, never target reads.
            config=json.dumps({'database':'platformsmoke','schema':'platform_smoke','tls':'verify-full','runtime_secret_arn':'arn:aws:secretsmanager:eu-west-1:337159794548:secret:synthetic-runtime','migration_secret_arn':'arn:aws:secretsmanager:eu-west-1:337159794548:secret:synthetic-migration'})
            env={'RELATIONAL_CONFIG_JSON':config,'RELATIONAL_MASTER_SECRET_JSON':json.dumps({'username':'fixture_root','password':'synthetic-root'}),'RELATIONAL_MIGRATION_SECRET_JSON':json.dumps({'username':'psmokemigrate','password':'synthetic-migration','host':'postgres','port':5432}),'RELATIONAL_RUNTIME_SECRET_JSON':json.dumps({'username':'psmokeruntime','password':'synthetic-runtime','host':'postgres','port':5432}),'RELATIONAL_SMOKE_QUEUE_URL':'http://queue:9324/123456789012/smoke','RELATIONAL_RESTORE_HOST':RESTORE_HOST,'AWS_ACCESS_KEY_ID':'synthetic','AWS_SECRET_ACCESS_KEY':'synthetic','AWS_EC2_METADATA_DISABLED':'true','AWS_ENDPOINT_URL_SQS':'http://queue:9324'}
            def task(entry,expected='succeeded',extra=None):
                options=['run','--rm','--name',network+'-task','--network',network,'--read-only','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=16m','--cap-drop','ALL','--security-opt','no-new-privileges','-v',str(root/'ca.crt')+':/app/assets/rds-eu-west-1-bundle.crt:ro']
                for key,value in {**env,**(extra or {})}.items():options+=['-e',key+'='+value]
                result=docker(*options,args.image,'.cache/platform-shell-image-build/infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-'+entry+'.main.js',check=False)
                if result.returncode!=(0 if expected=='succeeded' else 1) or '"outcome":"'+expected+'"' not in result.stdout:raise RuntimeError('packaged-'+entry+'-outcome-invalid')
                return result.stdout
            task('bootstrap');task('migration');task('migration')
            # A live connection with absent accepted data must not qualify restore.
            missing=task('restore-verify','failed',{'RELATIONAL_RESTORE_HOST':RESTORE_HOST,'RELATIONAL_RUNTIME_SECRET_JSON':json.dumps({'username':'fixture_root','password':'synthetic-root','host':'postgres','port':5432})})
            if 'restore-database-query-failure' not in missing:raise RuntimeError('empty-restore-negative-wrong-reason')
            task('relay')
            docker('exec',database,'psql','-U','fixture_root','-d','platformsmoke','-c','REVOKE INSERT, UPDATE ON platform_smoke.platform_processing FROM psmokeruntime')
            task('worker','failed')
            docker('exec',queue,'/nodejs/bin/node','-e','fetch("http://127.0.0.1:9324/proof").then(r=>r.json()).then(x=>process.exit(x.acknowledged===0?0:1))')
            docker('exec',database,'psql','-U','fixture_root','-d','platformsmoke','-c','GRANT INSERT, UPDATE ON platform_smoke.platform_processing TO psmokeruntime')
            task('worker')
            proof=docker('exec',queue,'/nodejs/bin/node','-e','fetch("http://127.0.0.1:9324/proof").then(r=>r.json()).then(x=>process.exit(x.acknowledged===1?0:1))')
            # Copy only this disposable database into the isolated restore target.
            dump=docker('exec',database,'pg_dumpall','-U','fixture_root','--clean','--if-exists').stdout
            docker('exec','-i',restored,'psql','-U','fixture_root','-d','postgres',input=dump)
            task('restore-verify')
            docker('exec',restored,'psql','-U','fixture_root','-d','platformsmoke','-c','DELETE FROM platform_smoke.platform_processing')
            failed=task('restore-verify','failed')
            if 'restore-processing-state-mismatch' not in failed:raise RuntimeError('incomplete-restore-negative-wrong-reason')

        except BaseException as error:
            original=error
        finally:
            adapter=Path(__file__).resolve().parents[1]/'shared/provider-adapters/docker/disposable-cleanup.py'
            spec=importlib.util.spec_from_file_location('docker_cleanup',adapter);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            effects=[('container',name) for name in reversed(containers)]
            if volume_created:effects.append(('volume',volume))
            if network_created:effects.append(('network',network))
            cleanup=module.cleanup(effects)
            if cleanup:
                print(json.dumps({'verdict':'failed','code':'package-cleanup-incomplete','effects':cleanup}))
                if original is None:original=RuntimeError('package-cleanup-incomplete')
            if original:raise original
    print(json.dumps({'verdict':'passed','evidence_class':'container-qualification','checks':['bootstrap','migration','migration-repeat','relay','worker-denied-no-ack','worker-retry-after-permission-repair','worker-ack-after-completion','isolated-restore','absent-schema-rejected','incomplete-processing-rejected'],'provider_fixture':'local-sqs-protocol-no-cloud-proof'}))
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (RuntimeError,subprocess.SubprocessError) as error:
        print(json.dumps({'verdict':'failed','code':str(error) if isinstance(error,RuntimeError) else 'package-command-unavailable'}));raise SystemExit(1)
