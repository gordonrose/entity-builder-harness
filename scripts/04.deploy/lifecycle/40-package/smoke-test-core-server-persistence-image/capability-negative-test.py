#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.persistence-packaged-inactive-capability
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove a healthy assembled image with a loaded but disconnected readiness observer cannot pass enabled capability qualification.
#   portability: { class: internal, targets: [kanbien-core-platform] }
#   effects: [network, writes-files]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-core-server-persistence
#     path: .github/workflows/publish-kanbien-core-platform-core-server-persistence.yml
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PRELOAD='''const Module=require('module'),fs=require('fs'),original=Module._load;
Module._load=function(identifier,...args){const value=original.call(this,identifier,...args);
if(identifier==='@kanbien/platform-observability')return {...value,createPlatformReadinessObserver:()=>{fs.writeFileSync('/tmp/package-disconnected-observer','loaded');return {observe:async()=>({})};}};
return value;};
'''
DOCKER='''#!/usr/bin/env python3
import os,pathlib,subprocess,sys,time
args=sys.argv[1:];real=os.environ['PACKAGE_REAL_DOCKER']
intervene=args and args[0]=='run' and 'PLATFORM_OBSERVABILITY_METRICS_PROVIDER=cloudwatch-otel' in args
if intervene:args[1:1]=['-v',os.environ['PACKAGE_PRELOAD']+':/fixture-disconnect.cjs:ro','-e','NODE_OPTIONS=--require=/fixture-disconnect.cjs']
result=subprocess.run([real,*args]);
if result.returncode or not intervene:sys.exit(result.returncode)
name=args[args.index('--name')+1]
probe='const fs=require("fs");fetch("http://127.0.0.1:3000/livez").then(r=>process.exit(r.status===200&&fs.existsSync("/tmp/package-disconnected-observer")?0:1)).catch(()=>process.exit(1))'
for attempt in range(40):
 verified=subprocess.run([real,'exec',name,'/nodejs/bin/node','-e',probe],capture_output=True)
 if verified.returncode==0:pathlib.Path(os.environ['PACKAGE_INTERVENTION']).write_text('live-loaded-disconnected');sys.exit(0)
 time.sleep(.25)
sys.exit(91)
'''

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--image',required=True);parser.add_argument('--port',default='39458');args=parser.parse_args()
 real=shutil.which('docker')
 if not real:raise ValueError('docker-required')
 image=subprocess.check_output([real,'image','inspect',args.image,'--format','{{.Id}}'],text=True).strip()
 with tempfile.TemporaryDirectory(prefix='package-inactive-capability-') as directory:
  root=Path(directory);preload=root/'disconnect.cjs';preload.write_text(PRELOAD);binary=root/'docker';binary.write_text(DOCKER);binary.chmod(0o755);marker=root/'intervention'
  environment={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'PACKAGE_REAL_DOCKER':real,'PACKAGE_PRELOAD':str(preload),'PACKAGE_INTERVENTION':str(marker)}
  result=subprocess.run(['bash',str(Path(__file__).with_name('script.sh')),'--tag',image,'--port',args.port],env=environment,capture_output=True,text=True)
  cleanup=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{') and 'deploy/disposable-cleanup/v1' in line]
  if result.returncode!=1 or 'packaged-readiness-metric-ready-not-exported' not in result.stderr or not marker.exists() or marker.read_text()!='live-loaded-disconnected':raise ValueError('inactive-capability-negative-wrong-boundary')
  if not cleanup or cleanup[-1].get('verdict')!='passed' or cleanup[-1].get('effects_checked')!=5:raise ValueError('inactive-capability-cleanup-incomplete')
 print(json.dumps({'verdict':'passed','evidence_class':'container-qualification-negative','image_id':image,'injected_fault':'healthy-loaded-readiness-observer-disconnected','observed_rejection':'packaged-readiness-metric-ready-not-exported','cleanup':'all-five-effects-observed-absent'}));return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,subprocess.SubprocessError) as error:
  print(json.dumps({'verdict':'failed','code':str(error) if isinstance(error,ValueError) else 'negative-package-proof-unavailable'}));raise SystemExit(1)
