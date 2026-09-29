#!/usr/bin/env python3
"""Verify reviewed compositions cannot omit or forge discovered template edges."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.operational-realization-cloudformation-coverage
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reconcile independently discovered infrastructure references without granting provider authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(DIRECTORY))
from test_source_coverage import fixture_composition
import source_coverage as coverage
import source_inventory as discovery
import local_build


class CloudFormationCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cloudformation-coverage-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'package.json').write_text('{}')
        path = self.root/'infra/04.deploy/template.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'Parameters':{'Name':{'Type':'String'}},'Resources':{
            'Queue':{'Type':'AWS::SQS::Queue'},
            'Task':{'Type':'AWS::ECS::TaskDefinition','Properties':{'Family':{'Ref':'Name'},
                'ContainerDefinitions':[{'Name':'job','Image':'fixture','Command':['run']}],
                'TaskRoleArn':{'Fn::GetAtt':['Queue','Arn']}}}}}))
        self.inventory = discovery.discover(self.root)
        self.composition = fixture_composition(self.inventory)
        self.references = [row for row in self.inventory['observations'] if row['kind']=='infrastructure-reference']
        self.composition['infrastructure_references'] = [row['id'] for row in self.references]
        self.ledger = coverage.make_ledger(self.inventory)
        for entry in self.ledger['entries']:
            entry['review_status']='reviewed'

    def compile(self):
        return coverage.compile_coverage(self.inventory,self.composition,self.ledger,as_of='2026-09-29')

    def reseal(self):
        self.inventory['inventory_digest']=discovery.digest(discovery.canonical({key:value for key,value in self.inventory.items() if key!='inventory_digest'}))
        self.composition['inventory_digest']=self.inventory['inventory_digest']
        self.ledger['inventory_digest']=self.inventory['inventory_digest']

    def codes(self):
        return {row['code'] for row in self.compile()['findings']}

    def test_reviewed_reference_graph_is_source_covered_without_authority(self):
        result = self.compile()
        self.assertEqual(result['verdict'],'covered')
        self.assertFalse(result['authorized'])
        self.assertEqual(len(result['acceptance_obligations']),17)
        self.assertTrue(any(row['gate']=='iac-static-validation' for row in result['acceptance_obligations']))

    def test_missing_reference_review_blocks(self):
        self.composition.pop('infrastructure_references')
        self.assertIn('infrastructure-reference-undeclared',self.codes())

    def test_partial_reference_review_blocks(self):
        self.composition['infrastructure_references'].pop()
        self.assertIn('infrastructure-reference-undeclared',self.codes())

    def test_unknown_reference_review_blocks(self):
        self.composition['infrastructure_references'].append('sha256:'+'a'*64)
        self.assertIn('infrastructure-reference-unknown',self.codes())

    def test_duplicate_review_does_not_count_twice(self):
        self.composition['infrastructure_references'].append(self.references[0]['id'])
        with self.assertRaises(coverage.CoverageFailure):self.compile()

    def test_resource_target_requires_reviewed_resource(self):
        target = next(row['target_id'] for row in self.references if row['reference_kind']=='get-att')
        self.composition['resources'] = [row for row in self.composition['resources'] if target not in row['observation_ids']]
        self.assertIn('infrastructure-reference-resource-undeclared',self.codes())

    def test_unknown_target_cannot_pass_internal_compiler(self):
        self.references[0]['target_id']='sha256:'+'a'*64
        self.reseal()
        self.assertIn('infrastructure-reference-target-invalid',self.codes())

    def test_source_file_cannot_pose_as_reference_target(self):
        target=next(row['id'] for row in self.inventory['observations'] if row['kind']=='source-file')
        self.references[0]['target_id']=target
        self.reseal()
        self.assertIn('infrastructure-reference-target-invalid',self.codes())

    def test_getatt_cannot_target_a_parameter(self):
        reference=next(row for row in self.references if row['reference_kind']=='get-att')
        reference['target_id']=next(row['id'] for row in self.inventory['observations'] if row.get('symbol_kind')=='parameter')
        self.reseal()
        self.assertIn('infrastructure-reference-target-kind-invalid',self.codes())

    def test_reference_requires_target_and_relation(self):
        self.references[0].pop('target_id')
        with self.assertRaises(coverage.CoverageFailure):self.compile()

    def test_nonreference_cannot_smuggle_target(self):
        next(row for row in self.inventory['observations'] if row['kind']=='source-file')['target_id']=self.references[0]['target_id']
        with self.assertRaises(coverage.CoverageFailure):self.compile()

    def refresh_with_external_section(self, section, value):
        path=self.root/'infra/04.deploy/template.json'
        document=json.loads(path.read_text());document[section]=value;path.write_text(json.dumps(document))
        self.inventory=discovery.discover(self.root)
        self.composition=fixture_composition(self.inventory)
        self.composition['infrastructure_references']=[row['id'] for row in self.inventory['observations'] if row['kind']=='infrastructure-reference']
        self.ledger=coverage.make_ledger(self.inventory)
        for entry in self.ledger['entries']:entry['review_status']='reviewed'

    def test_review_cannot_waive_output_import_consumer(self):
        self.refresh_with_external_section('Outputs',{'Imported':{'Value':{'Fn::ImportValue':'external'}}})
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes())
        self.assertIn('dependency-consumer-unresolved',self.codes())

    def test_review_cannot_waive_condition_import_consumer(self):
        self.refresh_with_external_section('Conditions',{'Imported':{'Fn::Equals':[{'Fn::ImportValue':'external'},'yes']}})
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes())

    def test_review_cannot_waive_implicit_parameter_provider_dependency(self):
        self.refresh_with_external_section('Parameters',{'Name':{'Type':'AWS::SSM::Parameter::Value<String>'}})
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes())

    def test_helper_mutation_invalidates_actual_build_implementation_receipt(self):
        original=Path.read_bytes
        before=local_build.implementation_digest()
        def changed(path):
            value=original(path)
            return value+b'\n# helper changed\n' if path.name=='cloudformation_inventory.py' else value
        with patch.object(Path,'read_bytes',changed):after=local_build.implementation_digest()
        self.assertNotEqual(before,after)


if __name__=='__main__':
    unittest.main()
