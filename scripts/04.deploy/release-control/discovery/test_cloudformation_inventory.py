#!/usr/bin/env python3
"""Mutation tests for source-bound CloudFormation references and composition."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.release-control-cloudformation-inventory
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject missing or hidden template dependencies and unsafe composition inputs.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.operational-realization-gate
#     path: scripts/04.deploy/operational-realization-gate/smoke-test.sh

from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from source_inventory import discover
from caller_inventory import discover_callers
from build_inventory import discover_builds
from operation_inventory import discover_operations

FIXTURES = Path(__file__).parents[2] / 'operational-realization-gate/fixtures/cloudformation-references'


class CloudFormationInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cloudformation-source-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put('package.json', {})

    def put(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value))
        return path

    def template(self, resources=None, **extra):
        doc = {'Resources': resources or {'Queue': {'Type': 'AWS::SQS::Queue'}}}
        doc.update(extra)
        self.put('infra/04.deploy/template.json', doc)
        return discover(self.root)

    def codes(self, result):
        return {row['code'] for row in result['findings']}

    def references(self, result):
        return [row for row in result['observations'] if row['kind'] == 'infrastructure-reference']

    def test_fixture_resolves_both_conditional_branches_and_safe_symbols(self):
        self.put('infra/04.deploy/template.yml', (FIXTURES/'template.yml').read_text())
        result = discover(self.root)
        self.assertEqual(result['findings'], [])
        refs = self.references(result)
        self.assertEqual(len(refs), 8)
        self.assertEqual(sum(row['reference_kind']=='get-att' for row in refs), 2)
        ids = {row['id'] for row in result['observations']}
        self.assertTrue(all(row['target_id'] in ids and row['subject_id'] in ids for row in refs))
        self.assertFalse(any(value in json.dumps(result) for value in ('Prefix','Primary','UseBackup','QueueName','AWS::Region')))

    def test_unknown_resource_reference_blocks(self):
        result=self.template({'Queue': {'Type':'AWS::SQS::Queue','Properties': {'QueueName': {'Ref':'Absent'}}}})
        self.assertIn('infrastructure-reference-unknown',self.codes(result))

    def test_missing_false_branch_is_still_blocking(self):
        result=self.template({'Queue': {'Type':'AWS::SQS::Queue','Properties': {'QueueName': {'Fn::If':['Enabled','ok',{'Ref':'Absent'}]}}}},Conditions={'Enabled':{'Fn::Equals':['yes','yes']}})
        self.assertIn('infrastructure-reference-unknown',self.codes(result))

    def test_missing_condition_blocks(self):
        result=self.template({'Queue': {'Type':'AWS::SQS::Queue','Condition':'Absent'}})
        self.assertIn('infrastructure-reference-unknown',self.codes(result))

    def test_unknown_getatt_blocks(self):
        result=self.template({'Queue': {'Type':'AWS::SQS::Queue','Properties':{'X':{'Fn::GetAtt':['Absent','Arn']}}}})
        self.assertIn('infrastructure-reference-unknown',self.codes(result))

    def test_known_resource_without_container_definitions_is_supported(self):
        self.assertEqual(self.template()['findings'],[])

    def test_task_still_requires_containers(self):
        result=self.template({'Task': {'Type':'AWS::ECS::TaskDefinition','Properties':{}}})
        self.assertIn('container-shape-invalid',self.codes(result))

    def test_native_executable_resource_stays_unsupported(self):
        result=self.template({'Function':{'Type':'AWS::Lambda::Function','Properties':{}}})
        self.assertIn('resource-type-unsupported',self.codes(result))
        resource=next(row for row in result['observations'] if row['kind']=='resource')
        self.assertIn('resource-type-unsupported',resource['issues'])

    def test_metadata_cannot_hide_bootstrap(self):
        result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Metadata':{'AWS::CloudFormation::Init':{}}}})
        self.assertIn('infrastructure-resource-behavior-unsupported',self.codes(result))

    def test_nested_stack_remains_unsupported(self):
        result=self.template({'Nested':{'Type':'AWS::CloudFormation::Stack','Properties':{}}})
        self.assertIn('resource-type-unsupported',self.codes(result))

    def test_unknown_intrinsic_and_macro_remain_blocked(self):
        for expression in ({'Fn::Future':['x']},{'Fn::Transform':{'Name':'macro'}}):
            with self.subTest(expression=expression):
                result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':expression}}})
                self.assertIn('infrastructure-intrinsic-unsupported',self.codes(result))

    def test_sub_variables_shadow_logical_names_and_bind_their_values(self):
        result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':{'Fn::Sub':['${Alias}-${!Literal}-${AWS::Region}',{'Alias':{'Ref':'Prefix'}}]}}}},Parameters={'Prefix':{'Type':'String'}})
        self.assertEqual(result['findings'],[])
        self.assertEqual(len(self.references(result)),2)

    def test_unused_sub_variable_cannot_hide_missing_dependency(self):
        result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':{'Fn::Sub':['literal',{'Alias':{'Ref':'Absent'}}]}}}})
        self.assertIn('infrastructure-reference-unknown',self.codes(result))

    def test_malformed_intrinsics_fail_closed(self):
        for expression in ({'Ref':[]},{'Fn::GetAtt':['Queue']},{'Fn::Sub':['text',[]]},
                           {'Fn::Join':['only']},{'Fn::If':['x','y']},{'Fn::Sub':'${broken'},
                           {'Fn::GetAtt':['Queue','']},{'Ref':'Queue','extra':'bad'}):
            with self.subTest(expression=expression):
                result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':expression}}})
                self.assertTrue(self.codes(result)&{'infrastructure-reference-shape-invalid','infrastructure-intrinsic-shape-invalid'})

    def test_resource_cycle_blocks(self):
        result=self.template({'One':{'Type':'AWS::SQS::Queue','DependsOn':'Two'},'Two':{'Type':'AWS::SQS::Queue','Properties':{'X':{'Ref':'One'}}}})
        self.assertIn('infrastructure-reference-cycle',self.codes(result))

    def test_condition_cycle_blocks(self):
        result=self.template(Conditions={'One':{'Condition':'Two'},'Two':{'Condition':'One'}})
        self.assertIn('infrastructure-reference-cycle',self.codes(result))

    def test_parameters_cannot_shadow_resources(self):
        result=self.template(Parameters={'Queue':{'Type':'String'}})
        self.assertIn('infrastructure-symbol-duplicate',self.codes(result))

    def test_findinmap_requires_declared_mapping(self):
        result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':{'Fn::FindInMap':['Missing','a','b']}}}})
        self.assertIn('infrastructure-reference-unknown',self.codes(result))

    def test_reference_change_changes_target_and_digest(self):
        doc={'One':{'Type':'AWS::SQS::Queue'},'Two':{'Type':'AWS::SQS::Queue'},'Use':{'Type':'AWS::IAM::Role','DependsOn':'One'}}
        first=self.template(doc);doc['Use']['DependsOn']='Two';second=self.template(doc)
        self.assertNotEqual(first['inventory_digest'],second['inventory_digest'])
        self.assertEqual(self.references(first)[0]['id'],self.references(second)[0]['id'])
        self.assertNotEqual(self.references(first)[0]['target_id'],self.references(second)[0]['target_id'])

    def composition(self):
        self.put('infra/04.deploy/foundation.yml', {'schema':'deploy/cloudformation-composition/v1','fragments':['base.yml','queue.yml','role.yml']})
        self.put('infra/04.deploy/base.yml', {'AWSTemplateFormatVersion':'2010-09-09','Description':'test','Parameters':{'Prefix':{'Type':'String'}},'Outputs':{'Result':{'Value':{'Ref':'Role'}}}})
        self.put('infra/04.deploy/queue.yml', {'Resources':{'Queue':{'Type':'AWS::SQS::Queue'}}})
        self.put('infra/04.deploy/role.yml', {'Resources':{'Role':{'Type':'AWS::IAM::Role','DependsOn':'Queue'}}})

    def test_cross_fragment_references_resolve_only_within_manifest(self):
        self.composition();result=discover(self.root)
        self.assertEqual(result['findings'],[])
        self.assertEqual(len(self.references(result)),2)

    def test_other_template_cannot_supply_missing_symbol(self):
        self.composition();self.put('infra/04.deploy/other.yml',{'Resources':{'Different':{'Type':'AWS::SQS::Queue','DependsOn':'Queue'}}})
        self.assertIn('infrastructure-reference-unknown',self.codes(discover(self.root)))

    def test_duplicate_fragment_symbols_block(self):
        self.composition();self.put('infra/04.deploy/role.yml',{'Resources':{'Queue':{'Type':'AWS::SQS::Queue'}}})
        self.assertIn('infrastructure-symbol-duplicate',self.codes(discover(self.root)))

    def test_fragment_change_invalidates_inventory(self):
        self.composition();before=discover(self.root);self.put('infra/04.deploy/queue.yml',{'Resources':{'Queue':{'Type':'AWS::SQS::Queue','Properties':{'MessageRetentionPeriod':60}}}})
        self.assertNotEqual(before['inventory_digest'],discover(self.root)['inventory_digest'])

    def test_manifest_rejects_duplicate_fragments(self):
        self.composition();self.put('infra/04.deploy/foundation.yml',{'schema':'deploy/cloudformation-composition/v1','fragments':['base.yml','base.yml']})
        self.assertIn('infrastructure-composition-invalid',self.codes(discover(self.root)))

    def test_manifest_rejects_escape_and_missing_paths(self):
        for path,code in (('../outside.yml','infrastructure-fragment-path-invalid'),('absent.yml','infrastructure-fragment-missing')):
            with self.subTest(path=path):
                self.put('infra/04.deploy/foundation.yml',{'schema':'deploy/cloudformation-composition/v1','fragments':[path]})
                self.assertIn(code,self.codes(discover(self.root)))

    def test_symlink_fragment_is_not_read(self):
        self.composition();outside=self.put('outside.yml','sensitive: DO-NOT-PRINT')
        target=self.root/'infra/04.deploy/role.yml';target.unlink();target.symlink_to(outside)
        result=discover(self.root);self.assertIn('source-symlink-unsupported',self.codes(result));self.assertIn('infrastructure-fragment-missing',self.codes(result));self.assertNotIn('DO-NOT-PRINT',json.dumps(result))

    def test_symlink_fragment_parent_is_not_read(self):
        outside=self.root/'outside';outside.mkdir();(outside/'part.yml').write_text('Resources: {}')
        self.put('infra/04.deploy/foundation.yml',{'schema':'deploy/cloudformation-composition/v1','fragments':['linked/part.yml']})
        (self.root/'infra/04.deploy/linked').symlink_to(outside,target_is_directory=True)
        result=discover(self.root);self.assertIn('source-symlink-unsupported',self.codes(result));self.assertIn('infrastructure-fragment-missing',self.codes(result))

    def test_source_alias_stays_rejected(self):
        self.put('infra/04.deploy/template.yml','Resources: &a {}\nOther: *a\n')
        self.assertIn('source-alias-unsupported',self.codes(discover(self.root)))

    def test_json_cannot_forge_internal_tag_representation(self):
        result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':{'$tag':'Ref','value':'Queue'}}}})
        self.assertIn('source-key-invalid',self.codes(result))

    def test_yaml_cannot_forge_internal_tag_representation(self):
        self.put('infra/04.deploy/template.yml','Resources: {Queue: {Type: "AWS::SQS::Queue", Properties: {X: {$tag: Ref, value: Queue}}}}')
        self.assertIn('source-key-invalid',self.codes(discover(self.root)))

    def test_resource_reference_in_condition_is_rejected(self):
        result=self.template(Conditions={'Invalid':{'Fn::Equals':[{'Ref':'Queue'},'value']}})
        self.assertIn('infrastructure-reference-context-invalid',self.codes(result))

    def test_resource_reference_in_parameter_default_is_rejected(self):
        result=self.template(Parameters={'Invalid':{'Type':'String','Default':{'Ref':'Queue'}}})
        self.assertIn('infrastructure-reference-context-invalid',self.codes(result))

    def test_reference_limit_cannot_produce_clear_partial_graph(self):
        import cloudformation_inventory
        with patch.object(cloudformation_inventory,'MAX_REFERENCES',0):
            result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{'X':{'Ref':'Name'}}}},Parameters={'Name':{'Type':'String'}})
        self.assertIn('infrastructure-reference-limit-exceeded',self.codes(result))

    def test_symbol_limit_cannot_produce_clear_partial_graph(self):
        import cloudformation_inventory
        with patch.object(cloudformation_inventory,'MAX_SYMBOLS',0):result=self.template()
        self.assertIn('infrastructure-reference-limit-exceeded',self.codes(result))

    def test_manifest_shared_fragment_is_rejected(self):
        self.composition()
        self.put('infra/04.deploy/another.yml',{'schema':'deploy/cloudformation-composition/v1','fragments':['base.yml','queue.yml','role.yml']})
        self.assertIn('infrastructure-fragment-shared',self.codes(discover(self.root)))

    def test_output_import_is_observed_and_consumer_unresolved(self):
        result=self.template(Outputs={'Imported':{'Value':{'Fn::ImportValue':'hidden-export'}}})
        deps=[row for row in result['observations'] if row['kind']=='external-dependency']
        self.assertEqual(len(deps),1)
        owner=next(row for row in result['observations'] if row['id']==deps[0]['subject_id'])
        self.assertEqual(owner['symbol_kind'],'output')
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))
        self.assertNotIn('hidden-export',json.dumps(result))

    def test_condition_import_is_observed_and_consumer_unresolved(self):
        result=self.template(Conditions={'Imported':{'Fn::Equals':[{'Fn::ImportValue':'hidden-export'},'yes']}})
        deps=[row for row in result['observations'] if row['kind']=='external-dependency']
        self.assertEqual(len(deps),1)
        owner=next(row for row in result['observations'] if row['id']==deps[0]['subject_id'])
        self.assertEqual(owner['symbol_kind'],'condition')
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_output_import_both_conditional_branches_are_observed(self):
        result=self.template(Conditions={'Selected':{'Fn::Equals':['yes','yes']}},Outputs={'Imported':{'Value':{'Fn::If':['Selected',{'Fn::ImportValue':'yes-export'},{'Fn::ImportValue':'no-export'}]}}})
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),2)
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_short_form_import_retains_output_owner(self):
        self.put('infra/04.deploy/template.yml','Resources: {Queue: {Type: "AWS::SQS::Queue"}}\nOutputs: {Imported: {Value: !ImportValue hidden-export}}\n')
        result=discover(self.root)
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),1)
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_resource_imports_keep_exact_legacy_locators_without_duplicates(self):
        from source_inventory import canonical,digest
        result=self.template({'Queue':{'Type':'AWS::SQS::Queue','Properties':{
            'One':{'Fn::If':['Selected',{'Fn::ImportValue':'first'},{'Fn::ImportValue':'second'}]},
            'Two':{'Fn::Sub':['${Local}',{'Local':{'Fn::ImportValue':'third'}}]}}}},Conditions={'Selected':{'Fn::Equals':['yes','yes']}})
        deps=[row for row in result['observations'] if row['kind']=='external-dependency']
        self.assertEqual(result['findings'],[])
        self.assertEqual(len(deps),3)
        source=next(row for row in result['sources'] if row['path']=='infra/04.deploy/template.json')
        locations=[['Resources','Queue','Properties','One','Fn::If',1],['Resources','Queue','Properties','One','Fn::If',2],['Resources','Queue','Properties','Two','Fn::Sub',1,'Local']]
        self.assertEqual({row['id'] for row in deps},{digest(canonical([source['id'],'external-dependency',loc])) for loc in locations})
        resource=next(row for row in result['observations'] if row['kind']=='resource')
        self.assertTrue(all(row['subject_id']==resource['id'] for row in deps))

    def test_short_form_nested_resource_imports_are_not_duplicated(self):
        self.put('infra/04.deploy/template.yml','Parameters: {Prefix: {Type: String}}\nResources:\n  Queue:\n    Type: AWS::SQS::Queue\n    Properties:\n      Name: !Join ["", [!ImportValue external, !Ref Prefix]]\n')
        result=discover(self.root)
        self.assertEqual(result['findings'],[])
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),1)

    def test_invalid_output_import_still_records_dependency(self):
        result=self.template(Outputs={'Imported':{'Value':{'Fn::ImportValue':[]}}})
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),1)
        self.assertIn('infrastructure-intrinsic-shape-invalid',self.codes(result))
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_import_in_unsupported_root_metadata_is_not_hidden(self):
        result=self.template(Metadata={'Value':{'Fn::ImportValue':'hidden'}})
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),1)
        self.assertIn('infrastructure-metadata-unsupported',self.codes(result))
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_dynamic_output_reference_has_explicit_unresolved_consumer(self):
        result=self.template(Outputs={'Imported':{'Value':'{{resolve:ssm:hidden:1}}'}})
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),1)
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_ssm_parameter_type_cannot_hide_provider_dependency(self):
        result=self.template(Parameters={'External':{'Type':'AWS::SSM::Parameter::Value<String>','Default':'/hidden/config'}})
        deps=[row for row in result['observations'] if row['kind']=='external-dependency']
        self.assertEqual(len(deps),1)
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))
        owner=next(row for row in result['observations'] if row['id']==deps[0]['subject_id'])
        self.assertEqual(owner['symbol_kind'],'parameter')
        self.assertNotIn('/hidden/config',json.dumps(result))

    def test_aws_resource_parameter_type_is_explicit_external_dependency(self):
        result=self.template(Parameters={'External':{'Type':'List<AWS::EC2::Subnet::Id>'}})
        self.assertEqual(sum(row['kind']=='external-dependency' for row in result['observations']),1)
        self.assertIn('infrastructure-external-consumer-unresolved',self.codes(result))

    def test_unknown_parameter_type_is_not_silently_covered(self):
        result=self.template(Parameters={'External':{'Type':'FutureProviderParameter'}})
        self.assertIn('infrastructure-parameter-type-unsupported',self.codes(result))

    def test_malformed_parameter_type_is_safe_blocked_inventory(self):
        result=self.template(Parameters={'External':{'Type':{'Unknown':'value'}}})
        self.assertIn('infrastructure-parameter-type-unsupported',self.codes(result))

    def test_helper_only_change_invalidates_all_collector_revisions(self):
        self.put('.github/workflows/check.yml',{'jobs':{'check':{'steps':[{'run':'npm run check'}]}}})
        self.put('package.json',{'scripts':{'check':'tsc -p platform/test/tsconfig.json'},'workspaces':[]})
        self.put('package-lock.json',{'lockfileVersion':3,'packages':{}})
        self.put('platform/test/tsconfig.json',{'compilerOptions':{'rootDir':'../..','outDir':'../../.cache/test','module':'CommonJS','moduleResolution':'Bundler','types':[]},'include':['src/**/*.ts']})
        self.put('platform/test/src/index.ts','export const value = 1;')
        calls=[lambda:discover(self.root),lambda:discover_callers(self.root,'.github/workflows/check.yml'),lambda:discover_operations(self.root,'.github/workflows/check.yml'),lambda:discover_builds(self.root,'.github/workflows/check.yml')]
        original=Path.read_bytes
        def changed(path):
            value=original(path)
            return value+b'\n# changed helper\n' if path.name=='cloudformation_inventory.py' else value
        for call in calls:
            before=call()
            with patch.object(Path,'read_bytes',changed):after=call()
            self.assertNotEqual(before['collector_revision'],after['collector_revision'])


if __name__ == '__main__':
    unittest.main()
