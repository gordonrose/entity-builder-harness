#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.collector-image-metric-behavior
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove enabled OTLP-to-EMF behavior in the actual collector image using isolated loopback input and local stdout output.
#   portability: { class: internal, targets: [] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.test.collector-image-startup
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/qualify-image.sh
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import yaml

ROOT=Path(__file__).resolve().parents[7]
CONFIG=ROOT/'infra/04.deploy/03.product/image/core-server-persistence-observability-collector/collector-qualification-config.yml'
TARGET=ROOT/'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/core-server-persistence.yml'
CLEANUP=ROOT/'scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup.py'
METRIC='kanbien.core_server.postgresql_readiness'
DIMENSIONS={'target':'kanbien-core-platform','scope':'core-server-persistence','workload':'server','dependency':'postgresql','readiness':'ready'}
CLIENT=r'''
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const deadline=Date.now()+20000;let healthy=false;
 while(Date.now()<deadline){try{const response=await fetch('http://127.0.0.1:13133');if(response.ok){healthy=true;break;}}catch{}await sleep(100);}
 if(!healthy)throw Error('collector-health-unavailable');
 const attributes=Object.entries(JSON.parse(process.env.METRIC_DIMENSIONS)).map(([key,stringValue])=>({key,value:{stringValue}}));
 const sample={name:process.env.METRIC_NAME,unit:'1',gauge:{dataPoints:[{attributes,timeUnixNano:String(BigInt(Date.now())*1000000n),asDouble:1}]}};
 const unrelated={...sample,name:'qualification.unselected_metric'};
 const body={resourceMetrics:[{resource:{attributes:[]},scopeMetrics:[{scope:{name:'delivery-chain-qualification'},metrics:[sample,unrelated]}]}]};
 const response=await fetch('http://127.0.0.1:4318/v1/metrics',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
 if(!response.ok)throw Error('collector-otlp-input-rejected');
 const accepted=await response.json();if(accepted.partialSuccess?.rejectedDataPoints)throw Error('collector-otlp-input-partially-rejected');
 console.log(JSON.stringify({verdict:'accepted',points:2}));
})().catch(()=>{console.error('collector-local-input-failed');process.exit(1)});
'''


class Failure(Exception):pass


def command(args,*,timeout=45):
    try:result=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    except (OSError,subprocess.SubprocessError):raise Failure('collector-local-operation-unavailable') from None
    if result.returncode:raise Failure('collector-local-operation-failed')
    return result.stdout


def image_id(reference):
    identity=command(['docker','image','inspect',reference,'--format','{{.Id}}']).strip()
    if not re.fullmatch('sha256:[0-9a-f]{64}',identity):raise Failure('collector-image-identity-invalid')
    return identity


def configuration():
    class Loader(yaml.SafeLoader):pass
    def intrinsic(loader,tag,node):
        return loader.construct_scalar(node) if isinstance(node,yaml.ScalarNode) else loader.construct_sequence(node) if isinstance(node,yaml.SequenceNode) else loader.construct_mapping(node)
    Loader.add_multi_constructor('!',intrinsic)
    fixture=yaml.safe_load(CONFIG.read_text())
    raw=yaml.load(TARGET.read_text(),Loader=Loader)['Resources']['ObservabilityCollectorConfiguration']['Properties']['Value']
    target=yaml.safe_load(raw.replace('${AWS::Region}','eu-west-1').replace('${LogGroupName}','/aws/ecs/kanbien-core-platform'))
    for key in ('receivers','processors','exporters','extensions'):
        if fixture[key]!=target[key]:raise Failure('collector-target-qualification-config-mismatch')
    for key in ('extensions','pipelines'):
        if fixture['service'][key]!=target['service'][key]:raise Failure('collector-target-pipeline-mismatch')
    return fixture


def emf_events(logs):
    events=[]
    for line in logs.splitlines():
        try:value=json.loads(line)
        except ValueError:continue
        if isinstance(value,dict) and isinstance(value.get('_aws'),dict):events.append(value)
    return events


def metric_metadata(event):
    return [item for item in event.get('_aws',{}).get('CloudWatchMetrics',[]) if isinstance(item,dict) and any(metric.get('Name')==METRIC for metric in item.get('Metrics',[]) if isinstance(metric,dict))]


def exercise(identity,client,config,label,*,expect_selected):
    name='collector-metric-'+str(os.getpid())+'-'+label;client_name=name+'-client'
    # The shipped receiver/processors/EMF exporter composition is unchanged.
    # Only EMF's documented destination changes to stdout; network:none ensures
    # this qualification cannot contact metadata endpoints or cloud services.
    selected=copy.deepcopy(config);selected['exporters']['awsemf']['output_destination']='stdout'
    original=None;cleanup_error=None;events=[]
    try:
        command(['docker','run','--detach','--name',name,'--network','none','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=16m','--cap-drop','ALL','--security-opt','no-new-privileges','-e','AWS_EC2_METADATA_DISABLED=true','-e','AOT_CONFIG_CONTENT='+yaml.safe_dump(selected,sort_keys=False),identity])
        command(['docker','run','--rm','--name',client_name,'--network','container:'+name,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','-e','METRIC_NAME='+METRIC,'-e','METRIC_DIMENSIONS='+json.dumps(DIMENSIONS),client,'node','-e',CLIENT])
        # Keep the declared ten-second batch interval. An exporter flush must
        # occur before absence can establish the old-selector regression.
        deadline=time.monotonic()+16
        while time.monotonic()<deadline:
            logs=command(['docker','logs',name]);events=emf_events(logs)
            if any(metric_metadata(event) for event in events):break
            time.sleep(.5)
        matching=[event for event in events if metric_metadata(event)]
        if expect_selected:
            if not matching:raise Failure('collector-readiness-emf-not-emitted')
            for event in matching:
                metadata=metric_metadata(event)
                if event.get(METRIC)!=1 or any(event.get(key)!=value for key,value in DIMENSIONS.items()):raise Failure('collector-emf-value-or-dimensions-invalid')
                if any(item.get('Namespace')!='Kanbien/CorePlatform' or len(item.get('Dimensions',[]))!=1 or len(item.get('Dimensions',[[]])[0])!=len(DIMENSIONS) or set(item.get('Dimensions',[[]])[0])!=set(DIMENSIONS) for item in metadata):raise Failure('collector-emf-metric-declaration-invalid')
            if any(any(metric.get('Name')=='qualification.unselected_metric' for metric in item.get('Metrics',[])) for event in events for item in event.get('_aws',{}).get('CloudWatchMetrics',[])):raise Failure('collector-emf-unselected-metric-exported')
        elif matching:raise Failure('collector-negative-selector-unexpectedly-exported')
    except (Failure,KeyError,TypeError,ValueError) as error:original=error
    finally:
        result=subprocess.run([sys.executable,'-B',str(CLEANUP),'--container',client_name,'--container',name],cwd=ROOT,text=True,capture_output=True)
        if result.returncode:cleanup_error='collector-disposable-cleanup-incomplete'
    if original:
        if cleanup_error:print(json.dumps({'cleanup':cleanup_error}),file=sys.stderr)
        raise original
    if cleanup_error:raise Failure(cleanup_error)
    return {'scenario':label,'verdict':'passed','selected_emf_events':len([event for event in events if metric_metadata(event)])}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--image',default='kanbien-observability-collector:qualification');parser.add_argument('--client-image',default='node:22-bookworm-slim');parser.add_argument('--positive-only',action='store_true');args=parser.parse_args()
    identity=image_id(args.image)
    try: client=image_id(args.client_image)
    except Failure:
        # A clean CI runner may lack the public local-input fixture image. This
        # pull supplies test tooling only; the collector under test is never pulled.
        if args.client_image!='node:22-bookworm-slim': raise
        command(['docker','pull',args.client_image],timeout=180)
        client=image_id(args.client_image)
    config=configuration()
    checks=[exercise(identity,client,config,'enabled',expect_selected=True)]
    if not args.positive_only:
        broken=copy.deepcopy(config)
        broken['exporters']['awsemf']['metric_declarations'][0]['metric_name_selectors']=[r'^kanbien\\.core_server\\.postgresql_readiness$']
        checks.append(exercise(identity,client,broken,'escaped-selector-rejected',expect_selected=False))
    if image_id(args.image)!=identity:raise Failure('collector-image-changed-during-qualification')
    print(json.dumps({'schema':'deploy/collector-image-behavior/v1','verdict':'passed','evidence_class':'local-finished-image','image_id':identity,'client_image_id':client,'configuration_sha256':'sha256:'+hashlib.sha256(CONFIG.read_bytes()).hexdigest(),'checks':checks,'sink':'awsemf-stdout','network':'none','limits':['No live CloudWatch or provider authorization was exercised.']},sort_keys=True))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (Failure,OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({'schema':'deploy/collector-image-behavior/v1','verdict':'failed','code':str(error) if isinstance(error,Failure) else 'collector-behavior-input-invalid'},sort_keys=True));raise SystemExit(1)
