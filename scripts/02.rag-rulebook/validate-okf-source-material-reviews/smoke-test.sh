#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.validate-okf-source-material-reviews.smoke-test
#   version: 2
#   status: active
#   created_on: "2026-06-29"
#   updated_on: "2026-10-26"
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#     - sre
#   kind: script
#   purpose: Smoke test the OKF source-material review validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.validate-okf-source-material-reviews
#       path: scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh

ROOT="$(git rev-parse --show-toplevel)"
python3 - "$ROOT/scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh" <<'PYTEST'
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

validator=Path(sys.argv[1])
roles=['architect','agentic-engineer','secops-engineer','senior-sre']
dimensions=['coverage','necessity','production_grade_gaps','execution_variables','human_readability','machine_readability','cost_optimization','security','performance','token_optimization']

def digest(raw):return hashlib.sha256(raw).hexdigest()

def accepted(identifier,source,raw):
    return {'schema':'rag-rulebook/okf-source-material-review/v1','review_id':identifier,'status':'accepted',
      'source_material':{'path':source,'corpus_id':'corpus.fixture','vertical':'fixture','source_state':'accepted','sha256':digest(raw),'target_rule_paths':[]},
      'threshold':{'passing_score':9.5,'required_roles':roles.copy(),'pass_rule':'every required reviewer score must be greater than 9.5 and no blocking gaps may remain'},
      'iterations':[{'iteration':1,'source_revision_summary':'Disposable synthetic review record; no repository source approval.',
        'reviewer_assessments':[{'role':role,'overall_score':9.6,'decision':'pass','blocking_gaps':[],'dimension_scores':{key:9.6 for key in dimensions},'recommendations':[]} for role in roles],
        'cross_review_summary':{'agreement':['fixture accepted'],'disagreement':[],'unresolved_blockers':[]},'recommendation_handling':{'applied':[],'rejected':[]},'rerun_required':False}],
      'final_decision':{'status':'accepted','summary':'Synthetic fixture only.','accepted_source_sha256':digest(raw),'accepted_at_utc':'2026-10-26T00:00:00Z','required_before_derivation':[]}}

with tempfile.TemporaryDirectory(prefix='okf-review-history-') as directory:
    root=Path(directory);subprocess.run(['git','init','-q',str(root)],check=True,capture_output=True)
    records=root/'.agentic/02.rag-rulebook/source-material-reviews';records.mkdir(parents=True)
    source=root/'docs/source.md';source.parent.mkdir();original=b'First reviewed source.\n';current=b'Second reviewed source.\n';source.write_bytes(current)
    historical=accepted('review.fixture.original','docs/source.md',original);latest=accepted('review.fixture.current','docs/source.md',current)
    first=records/'first.yml';second=records/'second.yml'
    def write(path,record):path.write_text(yaml.safe_dump(record,sort_keys=False))
    write(first,historical);write(second,latest);retained=first.read_bytes();checks=0
    def run(*args,expected=0,contains=None):
        global checks
        result=subprocess.run(['bash',str(validator),*args,'--json'],cwd=root,text=True,capture_output=True,timeout=15)
        assert result.returncode==expected,(args,result.returncode,result.stdout,result.stderr)
        report=json.loads(result.stdout)
        assert report['ok']==(expected==0),report
        if contains:assert any(contains in error for error in report['errors']),report
        checks+=1;return report
    report=run('--current');assert report['counts']['covered_sources']==1 and report['counts']['historical_records']==1
    old=next(item for item in report['records'] if item['path'].endswith('/first.yml'))
    new=next(item for item in report['records'] if item['path'].endswith('/second.yml'))
    assert old['integrity_valid'] and old['freshness']=='historical' and old['current_eligible'] is False
    assert new['integrity_valid'] and new['freshness']=='current' and new['current_eligible'] is True
    run('--record',str(second))
    run('--record',str(first),expected=1,contains='is stale')
    source.write_bytes(b'Unreviewed change.\n');run('--current',expected=1,contains='accepted-current-review-missing');source.write_bytes(current)
    source.unlink();run('--current',expected=1,contains='missing-source');run('--record',str(second),expected=1,contains='does not exist');source.write_bytes(current)
    # A valid current review never excuses forged or malformed historical proof.
    forged=copy.deepcopy(historical);forged['final_decision']['accepted_source_sha256']='f'*64;write(first,forged)
    report=run('--current',expected=1,contains='must match the recorded');assert report['sources'][0]['status']=='covered'
    first.write_bytes(retained)
    for label,edit,reason in [
      ('threshold',lambda record:record['iterations'][0]['reviewer_assessments'][0].update(overall_score=9.5),'must be greater than'),
      ('nan-score',lambda record:record['iterations'][0]['reviewer_assessments'][0].update(overall_score=float('nan')),'must be a number'),
      ('missing-role',lambda record:record['iterations'][0]['reviewer_assessments'].pop(),'missing required reviewer role'),
      ('unknown-schema',lambda record:record.update(schema='unknown'),'schema must be'),
      ('missing-sha',lambda record:record['source_material'].pop('sha256'),'requires source_material.sha256'),
      ('invalid-iteration',lambda record:record['iterations'][0].update(iteration='invalid'),'must be a positive integer'),
      ('unresolved',lambda record:record['iterations'][0]['cross_review_summary'].update(unresolved_blockers=['unresolved']),'unresolved blockers'),
      ('malformed-source',lambda record:record.update(source_material=['invalid']),'source_material must be an object'),
      ('superseded-forgery',lambda record:(record.update(status='superseded'),record['final_decision'].update(accepted_source_sha256='e'*64)),'must match the recorded')]:
        broken=copy.deepcopy(historical);edit(broken);write(first,broken);run('--current',expected=1,contains=reason);first.write_bytes(retained)
    first.write_text(first.read_text()+'status: accepted\n');run('--current',expected=1,contains='duplicate YAML mapping key');first.write_bytes(retained)
    duplicate=copy.deepcopy(latest);duplicate['review_id']=historical['review_id'];write(second,duplicate)
    run('--current',expected=1,contains='duplicate review_id');write(second,latest)
    unrelated=root/'docs/second-source.md';unrelated.write_bytes(b'Current second source.\n');third=records/'third.yml';write(third,accepted('review.fixture.unrelated','docs/second-source.md',b'Old second source.\n'))
    report=run('--current',expected=1,contains='docs/second-source.md: accepted-current-review-missing')
    assert report['counts']['covered_sources']==1 and report['counts']['sources']==2
    third.unlink();run('--current');assert first.read_bytes()==retained
    first.unlink();second.unlink();run('--current',expected=1,contains='no source-material review records discovered')
    print(json.dumps({'schema':'rag-rulebook/okf-source-review-history-test/v1','verdict':'passed','evidence_class':'simulated','cli_checks':checks}))
PYTEST
