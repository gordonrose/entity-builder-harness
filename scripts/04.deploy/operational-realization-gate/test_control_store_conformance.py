"""Actual process crash/race acceptance plus bounded public receipt regressions."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import control_store_conformance as subject
import operation_journal as c

class ControlStoreConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.result=subject.conformance(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_real_subprocesses_crashes_and_races_pass(self):
        self.assertEqual([case['case'] for case in self.result['cases']],list(subject.CASES))
        self.assertEqual(sum(case['subprocesses'] for case in self.result['cases']),7)
        self.assertEqual(sum(case['processes_killed'] for case in self.result['cases']),3)
        self.assertTrue(all(case['verdict']=='passed' for case in self.result['cases']))
        cases={case['case']:case for case in self.result['cases']}
        self.assertEqual(cases['effect-and-evidence-survive-process-kill']['persisted_effects'],1)
        self.assertEqual(cases['effect-and-evidence-survive-process-kill']['validated_evidence_documents'],1)
        self.assertEqual(cases['concurrent-claim-one-winner']['accepted_claims'],1)
        self.assertEqual(cases['concurrent-claim-one-winner']['rejected_actions'],1)
        self.assertEqual(cases['concurrent-revision-one-winner']['rejected_actions'],1)

    def test_receipt_closed_and_all_authority_blocked(self):
        c.validate('control-store-conformance',self.result)
        self.assertIs(self.result['authorized'],False)
        self.assertEqual(self.result['release_eligibility'],'blocked')
        self.assertEqual(self.result['operation_authorization'],'blocked')
        self.assertEqual(self.result['qualification_verdict'],'blocked')
        self.assertEqual(c.digest({key:value for key,value in self.result.items() if key!='result_digest'}),self.result['result_digest'])
        raw=c.canonical(self.result)
        self.assertNotIn(str(self.tmp.name).encode(),raw)
        for field in ('stdout','stderr','command','token','database_path'):
            self.assertNotIn(('"'+field+'"').encode(),raw)

    def test_missing_duplicate_out_of_order_case_rejected(self):
        for action in ('missing','duplicate','reorder'):
            with self.subTest(action=action):
                result=copy.deepcopy(self.result)
                if action=='missing':result['cases'].pop()
                if action=='duplicate':result['cases'][1]=copy.deepcopy(result['cases'][0])
                if action=='reorder':result['cases'].reverse()
                with self.assertRaises(c.ControlFailure):c.validate('control-store-conformance',result)

    def test_exact_runner_schema_and_explicit_policy_bindings(self):
        binding=subject.bindings()
        self.assertEqual(self.result['runner_digest'],binding['runner_digest'])
        self.assertEqual(self.result['schema_digests'],binding['schema_digests'])
        for name,digest in binding['schema_digests'].items():
            self.assertEqual(digest,'sha256:'+hashlib.sha256(c.read_source(c.SCHEMA_DIR/(name+'.schema.yml'))).hexdigest())
        self.assertIn('control_store_conformance.py',subject.RUNNERS)
        self.assertIn('control_store_fixtures.py',subject.RUNNERS)

    def test_public_wrapper_bytes_are_bound(self):
        original=c.read_source
        before=subject.bindings()['runner_digest']
        for filename in ('control_store_cli.py','script.py','script.sh'):
            with self.subTest(filename=filename):
                self.assertIn(filename,subject.RUNNERS)
                def changed(path,*args,**kwargs):
                    raw=original(path,*args,**kwargs)
                    return raw+b'\n# wrapper binding mutation\n' if Path(path).name==filename else raw
                with patch.object(c,'read_source',side_effect=changed):
                    self.assertNotEqual(before,subject.bindings()['runner_digest'])

    def test_mutated_runner_binding_rejects_receipt(self):
        before=subject.bindings();after=copy.deepcopy(before);after['runner_digest']='sha256:'+'0'*64
        observations={case['case']:{key:value for key,value in case.items() if key not in ('case','verdict')} for case in self.result['cases']}
        with tempfile.TemporaryDirectory() as root,patch.object(subject,'bindings',side_effect=[before,after]),patch.object(subject,'_case',side_effect=lambda unused,name:observations[name]):
            with self.assertRaises(c.ControlFailure) as found:subject.conformance(root)
            self.assertEqual(found.exception.code,'source-changed')

    def test_unique_owned_store_directory_and_no_existing_data_overwrite(self):
        root=Path(self.tmp.name)
        sentinel=root/'preserved';sentinel.write_bytes(b'caller-data')
        first=subject.private_directory(root);second=subject.private_directory(root)
        self.assertNotEqual(first,second);self.assertEqual(first.stat().st_mode&0o777,0o700)
        self.assertEqual(sentinel.read_bytes(),b'caller-data')

    def test_missing_insecure_symlink_scratch_roots_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);insecure=root/'insecure';insecure.mkdir(mode=0o777);insecure.chmod(0o777)
            link=root/'link';link.symlink_to(root,target_is_directory=True)
            for candidate in (root/'missing',insecure,link):
                with self.subTest(path=candidate.name),self.assertRaises(c.ControlFailure) as found:subject.private_directory(candidate)
                self.assertEqual(found.exception.code,'scratch-root-invalid')

    def test_worker_selector_rejects_arbitrary_commands(self):
        with self.assertRaises(c.ControlFailure) as found:subject._child(Path(self.tmp.name),'arbitrary-command')
        self.assertEqual(found.exception.code,'worker-invalid')

    def test_second_spawn_failure_stops_first_child(self):
        first=object()
        with patch.object(subject,'_child',side_effect=[first,OSError('fixture-failure')]),patch.object(subject,'_stop') as stopped:
            with self.assertRaises(OSError):subject._race(Path(self.tmp.name),'claim')
            stopped.assert_called_once_with(first)

    def test_receipt_states_actual_delete_mode_and_runtime_version(self):
        self.assertEqual(self.result['durability'],'sqlite-delete-synchronous-full')
        self.assertEqual(self.result['sqlite_version'],subject.sqlite3.sqlite_version)

    def test_limitations_cannot_be_removed_or_replaced(self):
        for value in ([],['multi-host-supported']):
            result=copy.deepcopy(self.result);result['limitations']=value
            with self.assertRaises(c.ControlFailure):c.validate('control-store-conformance',result)

if __name__=='__main__':unittest.main()
