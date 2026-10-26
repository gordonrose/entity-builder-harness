#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.test.local-image-delivery-wiring
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 02.rag-rulebook
#   domain: runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Exercise actual local image wrapper ordering, packaged runtime selection and cleanup exit behavior with disposable process fixtures.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: rag-rulebook.script.run-local-service.smoke-test
#     path: scripts/02.rag-rulebook/run-local-service/smoke-test.sh
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
BUILDER=ROOT/'scripts/02.rag-rulebook/build-service-image/script.sh'
SMOKE=Path(__file__).with_name('script.sh')
DOCKER='''#!/usr/bin/env python3
import json,os,sys
from pathlib import Path
args=sys.argv[1:];root=Path(os.environ['RAG_WIRING_ROOT']);calls=root/'docker.jsonl'
with calls.open('a') as f:f.write(json.dumps(args)+'\\n')
state=root/'present'
if args[:2]==['image','inspect']:print('sha256:'+'a'*64);sys.exit(0)
if args[0]=='run':state.write_text('possible');sys.exit(int(os.environ['PRIMARY_EXIT']))
if args[0]=='exec' and any('image-source-hygiene/v1' in part for part in args):
 if os.environ['CACHE_VISIBLE']!='0':print('packaged host Python cache is present',file=sys.stderr)
 sys.exit(int(os.environ['CACHE_VISIBLE']))
if args[:2]==['container','inspect']:
 if state.exists():print('[{}]');sys.exit(0)
 print('Error response from daemon: No such container: '+args[-1],file=sys.stderr);sys.exit(1)
if args[:2]==['container','rm']:
 if os.environ['CLEANUP_FAIL']=='1':sys.exit(1)
 state.unlink(missing_ok=True)
sys.exit(0)
'''
with tempfile.TemporaryDirectory(prefix='rag-image-wiring-') as directory:
    root=Path(directory);checks=0
    python=root/'python3';python.write_text('#!/bin/bash\nif [[ "$*" == *"inventory-deploy-control/script.py"* ]]; then exit "${INVENTORY_EXIT}"; fi\nexec '+sys.executable+' "$@"\n');python.chmod(0o755)
    docker=root/'docker';docker.write_text(DOCKER);docker.chmod(0o755)
    node=root/'node';node.write_text('#!/bin/bash\ncat >/dev/null\nexit "${QUERY_EXIT}"\n');node.chmod(0o755)
    bash=root/'bash';bash.write_text('#!/bin/bash\nif [[ "${1:-}" == *"validate-container-boundaries/script.sh" ]]; then exit 0; fi\nexec /bin/bash "$@"\n');bash.chmod(0o755)
    environment={**os.environ,'PATH':str(root)+os.pathsep+os.environ['PATH'],'RAG_WIRING_ROOT':str(root),'DOCKER_CONFIG':str(root/'docker-config'),'INVENTORY_EXIT':'0','PRIMARY_EXIT':'0','QUERY_EXIT':'0','CLEANUP_FAIL':'0','CACHE_VISIBLE':'0'}
    result=subprocess.run(['/bin/bash',str(BUILDER)],cwd=ROOT,env={**environment,'INVENTORY_EXIT':'43'},text=True,capture_output=True)
    assert result.returncode==43 and not (root/'docker.jsonl').exists(),(result.stdout,result.stderr);checks+=1
    for primary,query,cleanup,cache,expected in [(0,0,0,0,0),(37,0,1,0,37),(0,29,1,0,29),(0,0,1,0,1),(0,0,0,46,46)]:
        existing_sentinels=set(SMOKE.parent.glob('.cache-sentinel.*'))
        (root/'docker.jsonl').unlink(missing_ok=True);(root/'present').unlink(missing_ok=True)
        result=subprocess.run(['/bin/bash',str(SMOKE)],cwd=ROOT,env={**environment,'PRIMARY_EXIT':str(primary),'QUERY_EXIT':str(query),'CLEANUP_FAIL':str(cleanup),'CACHE_VISIBLE':str(cache)},text=True,capture_output=True)
        assert result.returncode==expected,(primary,query,cleanup,cache,result.returncode,result.stdout,result.stderr)
        assert set(SMOKE.parent.glob('.cache-sentinel.*'))==existing_sentinels
        if cache:assert 'packaged host Python cache is present' in result.stderr
        calls=[json.loads(line) for line in (root/'docker.jsonl').read_text().splitlines()]
        selected=next(item for item in calls if item[0]=='run');assert '--volume' not in selected and 'RAG_RUNTIME_DIR=/app/.cache/02.rag-rulebook' in selected
        assert selected[-1]=='sha256:'+'a'*64
        assert any(item[:2]==['container','inspect'] for item in calls)
        if expected:assert 'image smoke test passed' not in result.stdout
        else:assert not (root/'present').exists()
        checks+=1
    # Real runtime-builder subprocess: stale generated references are refreshed
    # before validation, but an independent invalid curated source still fails.
    fixture=root/'source-closure';fixture.mkdir()
    missing=fixture/'stale-generated';missing.write_text('source excluded from packaged closure')
    paths=['generate-recognition-sources','validate-recognition-sources','validate-recognition-candidates','validate-retrieval-policy-pack','generate-rulebook-index','validate-rulebook-index','generate-rulebook-chunks','compile-retrieval-policy']
    for name in paths:
        path=fixture/'scripts/02.rag-rulebook'/name/'script.sh';path.parent.mkdir(parents=True)
        if name=='generate-recognition-sources':
            body='if [ "$1" = --write-all ]; then rm "$RAG_REPO_ROOT/stale-generated"; exit 0; fi\nif [ -f "$RAG_REPO_ROOT/stale-generated" ]; then echo "generated recognition source is stale"; exit 1; fi\n'
        elif name=='validate-recognition-sources':
            body='if [ -f "$RAG_REPO_ROOT/stale-generated" ]; then echo "missing-generated-evidence"; exit 47; fi\necho "curated-source-invalid"; exit 48\n'
        else:body='echo "{}"\n'
        path.write_text('#!/bin/bash\n'+body);path.chmod(0o755)
    result=subprocess.run(['/bin/bash',str(ROOT/'scripts/02.rag-rulebook/build-local-runtime/script.sh'),'--output-dir',str(fixture/'runtime')],cwd=ROOT,env={**os.environ,'RAG_REPO_ROOT':str(fixture)},capture_output=True,text=True)
    assert result.returncode==48 and 'curated-source-invalid' in result.stderr and not missing.exists(),(result.returncode,result.stdout,result.stderr)
    checks+=1
    print(json.dumps({'schema':'rag-rulebook/local-image-wiring-test/v1','verdict':'passed','evidence_class':'simulated','cli_checks':checks}))
