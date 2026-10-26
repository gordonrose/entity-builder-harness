#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.docker.disposable-cleanup
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Remove declared disposable Docker effects and require observed absence without treating engine errors as absence.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.command.smoke-test-core-server-persistence-image
#     path: scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh
import argparse
import json
import re
import subprocess
import time


def invoke(args):
    try:return subprocess.run(['docker',*args],capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.SubprocessError):return None


def absent(kind,name,result):
    if result is None or result.returncode==0:return False
    messages={'container':'No such container: '+name,'network':'network '+name+' not found','volume':'get '+name+': no such volume'}
    return result.returncode==1 and result.stderr.strip()=='Error response from daemon: '+messages[kind]


def cleanup(resources):
    failures=[]
    for kind,name in resources:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,180}',name):
            failures.append({'kind':kind,'outcome':'name-invalid'});continue
        for attempt in range(3):
            before=invoke([kind,'inspect',name])
            if absent(kind,name,before):break
            if before is None or before.returncode:
                failures.append({'kind':kind,'outcome':'unobservable'});break
            invoke([kind,'rm',*(['--force'] if kind=='container' else []),name])
            after=invoke([kind,'inspect',name])
            if absent(kind,name,after):break
            if after is None or after.returncode:
                failures.append({'kind':kind,'outcome':'unobservable'});break
            if attempt==2:failures.append({'kind':kind,'outcome':'still-present'})
            else:time.sleep(.1)
    return failures


def main():
    parser=argparse.ArgumentParser()
    for kind in ['container','network','volume']:parser.add_argument('--'+kind,action='append',default=[])
    args=parser.parse_args();resources=[(kind,name) for kind in ['container','network','volume'] for name in getattr(args,kind)]
    failures=cleanup(resources)
    print(json.dumps({'schema':'deploy/disposable-cleanup/v1','verdict':'failed' if failures else 'passed','effects_checked':len(resources),'findings':failures},sort_keys=True))
    return 1 if failures else 0

if __name__=='__main__':raise SystemExit(main())
