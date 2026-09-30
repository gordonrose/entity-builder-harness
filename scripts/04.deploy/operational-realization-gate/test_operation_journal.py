"""Contract rejection tests for bounded immutable local control records."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import operation_journal as c
import control_store_fixtures as f

class OperationJournalTests(unittest.TestCase):
    def reject(self, doc, name='operation-control'):
        with self.assertRaises(c.ControlFailure):c.validate(name,doc)

    def test_fixture_intent_valid(self):
        self.assertEqual(c.validate('operation-control',f.intent()),f.intent())

    def test_all_required_fields(self):
        for field in f.intent():
            with self.subTest(field=field):
                doc=f.intent();del doc[field];self.reject(doc)

    def test_closed_records_reject_commands_secrets_and_arbitrary_provider(self):
        for field in ('command','secret','stdout','provider_payload','authorized'):
            with self.subTest(field=field):
                doc=f.intent();doc[field]='fixture';self.reject(doc)
        doc=f.intent();doc['scopes'][0]['provider']='aws';self.reject(doc)

    def test_scope_identity_is_global_and_exact(self):
        first=f.intent();second=f.intent('another-operation',release='9')
        self.assertEqual(first['scopes'],second['scopes'])
        first['scopes'][0]['resource']='different-resource';self.reject(first)

    def test_scopes_unique_and_sorted(self):
        doc=f.intent(resources=('resource-one','resource-two'))
        c.validate('operation-control',doc)
        doc['scopes'].reverse();self.reject(doc)
        doc=f.intent();doc['scopes'].append(copy.deepcopy(doc['scopes'][0]));self.reject(doc)

    def test_bool_is_not_integer_policy(self):
        for field in ('lease_ms','operation_timeout_ms','call_timeout_ms','max_attempts','evidence_lifetime_ms'):
            with self.subTest(field=field):
                doc=f.intent();doc['policy'][field]=True;self.reject(doc)

    def test_budget_consistency(self):
        doc=f.intent();doc['policy']['lease_ms']=11000;self.reject(doc)
        doc=f.intent();doc['policy']['call_timeout_ms']=11000;self.reject(doc)

    def test_evidence_closed_bounded_and_typed(self):
        c.validate('operation-evidence',f.evidence(f.intent(),1))
        for field in ('command','stdout','credentials'):
            with self.subTest(field=field):
                doc=f.evidence(f.intent(),1);doc[field]='unsafe';self.reject(doc,'operation-evidence')
        for value in (True,-1,2,2**64):
            with self.subTest(count=value):
                doc=f.evidence(f.intent(),1);doc['counts']['effect_count']=value;self.reject(doc,'operation-evidence')

    def test_json_duplicates_nonfinite_and_oversize_rejected(self):
        for raw in (b'{"value":1,"value":2}',b'{"value":NaN}',b'{"value":Infinity}',b'x'*32769,b'\xff'):
            with self.subTest(raw=raw[:20]):
                with self.assertRaises(c.ControlFailure):c.decode(raw)

    def test_recursive_aliased_float_and_control_data_rejected(self):
        recursive={};recursive['self']=recursive
        shared={};alias={'one':shared,'two':shared}
        for value in (recursive,alias,{'value':1.5},{'value':'line\nbreak'},{'value':'x'*513}):
            with self.subTest(value=type(value)):
                with self.assertRaises(c.ControlFailure):c.canonical(value)

    def test_schema_missing_corrupt_open_and_duplicate_rejected(self):
        original=c.read_source(c.SCHEMA_DIR/'operation-control.schema.yml')
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'operation-control.schema.yml'
            with patch.object(c,'SCHEMA_DIR',Path(root)):
                self.reject(f.intent())
                for raw in (b'not-a-schema',original.replace(b'"additionalProperties": false',b'"additionalProperties": true',1),original+b'\n$schema: duplicate\n'):
                    path.write_bytes(raw);self.reject(f.intent())

    def test_schema_parent_and_leaf_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            real=Path(root)/'real';real.mkdir()
            target=real/'operation-control.schema.yml';target.write_bytes(c.read_source(c.SCHEMA_DIR/'operation-control.schema.yml'))
            link=Path(root)/'link';link.symlink_to(real,target_is_directory=True)
            with patch.object(c,'SCHEMA_DIR',link):self.reject(f.intent())
            target.unlink();target.symlink_to(c.SCHEMA_DIR/'operation-control.schema.yml')
            with patch.object(c,'SCHEMA_DIR',real):self.reject(f.intent())

if __name__=='__main__':unittest.main()
