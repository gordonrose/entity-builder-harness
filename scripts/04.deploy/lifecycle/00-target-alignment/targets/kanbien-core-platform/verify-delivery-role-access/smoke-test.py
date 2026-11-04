#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.alignment-wrapper-diagnostics
#   version: 1
#   status: active
#   created_on: "2026-10-31"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: test
#   purpose: Prove fixed target wrapper arguments, exact child failure propagation and operation-specific ECR probe observations with local fake commands.
#   portability: {class: internal, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh
"""Execute the real four wrappers, never a provider or container command."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[7]
ALIGNMENT = Path('scripts/04.deploy/lifecycle/00-target-alignment')
TARGET = ALIGNMENT / 'targets/kanbien-core-platform'
ECR = ALIGNMENT / 'provider-adapters/aws/ecr-read-access/script.sh'
CANARY = 'synthetic-password-value-do-not-retain'
DIGEST = 'sha256:' + 'a' * 64


class TargetWrapperDiagnostics(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='target-wrapper-diagnostics-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for path in [ECR, *(TARGET / name / 'script.sh' for name in
                              ['validate-cost-condition', 'inspect-runtime-alignment', 'verify-delivery-role-access'])]:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        self.log = self.root / 'calls.jsonl'
        self.environment = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                            'WRAPPER_ROOT': str(self.root), 'WRAPPER_CALLS': str(self.log)}
        self.executable(self.bin / 'git', '#!/usr/bin/env bash\nprintf "%s\\n" "$WRAPPER_ROOT"\n')
        # Every ECR call is intercepted before the real PATH can be consulted.
        self.executable(self.bin / 'aws', '''#!/usr/bin/env python3
import json,os,sys
with open(os.environ['WRAPPER_CALLS'],'a') as out: out.write(json.dumps(sys.argv[1:])+'\\n')
status,message=json.loads(os.environ.get('WRAPPER_AWS_RESULTS','{}')).get(sys.argv[2],[0,''])
print(message,file=sys.stdout if status==0 else sys.stderr)
raise SystemExit(status)
''')

    def executable(self, path, source):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.sh' and source.startswith('#!/usr/bin/env python3\n'):
            source = '#!/usr/bin/env bash\npython3 - "$@" <<\'PY\'\n' + source.split('\n', 1)[1] + '\nPY\n'
        path.write_text(source, encoding='utf-8')
        path.chmod(0o755)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def run_script(self, path, *args, **environment):
        self.log.unlink(missing_ok=True)
        return subprocess.run(['bash', str(self.root / path), *args], cwd=self.root,
                              env={**self.environment, **environment}, capture_output=True, text=True, timeout=10)

    def test_ecr_probes_classify_the_actual_operation_not_error_prose(self):
        def error(code, operation):
            return f'An error occurred ({code}) when calling the {operation} operation: {CANARY}'
        cases = [
            ({}, 0, None, 3),
            ({'get-authorization-token': [0, CANARY]}, 0, None, 3),
            ({'describe-images': [9, error('ImageNotFoundException', 'DescribeImages')]}, 0, None, 3),
            ({'describe-image-scan-findings': [9, error('ScanNotFoundException', 'DescribeImageScanFindings')]}, 0, None, 3),
            ({'describe-image-scan-findings': [9, error('ImageNotFoundException', 'DescribeImageScanFindings')]}, 0, None, 3),
            ({'get-authorization-token': [9, error('ImageNotFoundException', 'GetAuthorizationToken')]}, 1, 'GET_AUTHORIZATION_TOKEN_PROBE_INCONCLUSIVE', 1),
            ({'describe-images': [9, error('ScanNotFoundException', 'DescribeImages')]}, 1, 'DESCRIBE_IMAGES_PROBE_INCONCLUSIVE', 2),
            ({'describe-images': [9, 'ImageNotFound ' + CANARY]}, 1, 'DESCRIBE_IMAGES_PROBE_INCONCLUSIVE', 2),
            ({'describe-images': [9, error('RepositoryNotFoundException', 'DescribeImages')]}, 1, 'DESCRIBE_IMAGES_PROBE_INCONCLUSIVE', 2),
            ({'describe-images': [9, error('ImageNotFoundException', 'DescribeImageScanFindings')]}, 1, 'DESCRIBE_IMAGES_PROBE_INCONCLUSIVE', 2),
            ({'describe-images': [9, error('AccessDeniedException', 'DescribeImages') + '\nImageNotFound']}, 1, 'DESCRIBE_IMAGES_DENIED', 2),
            ({'get-authorization-token': [9, error('ExpiredTokenException', 'GetAuthorizationToken')]}, 1, 'GET_AUTHORIZATION_TOKEN_DENIED', 1),
        ]
        for outcomes, status, code, count in cases:
            with self.subTest(outcomes=outcomes):
                result = self.run_script(TARGET / 'verify-delivery-role-access/script.sh',
                                         WRAPPER_AWS_RESULTS=json.dumps(outcomes))
                self.assertEqual(result.returncode, status, result.stderr)
                self.assertNotIn(CANARY, result.stdout + result.stderr)
                self.assertEqual(len(self.calls()), count)
                self.assertTrue(all(call[:1] == ['ecr'] for call in self.calls()))
                for call in self.calls()[1:]:
                    self.assertIn('kanbien-core-platform/core-server', call)
                    self.assertIn('sha256:' + '0' * 64, ' '.join(call))
                if code:
                    self.assertIn('DIAGNOSTIC_CODE=DELIVERY_ACCESS_' + code, result.stderr)
                else:
                    self.assertEqual(json.loads(result.stdout)['verdict'], 'passed')
        rejected = self.run_script(TARGET / 'verify-delivery-role-access/script.sh', '--repository', CANARY)
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(self.calls(), [])
        self.assertNotIn(CANARY, rejected.stdout + rejected.stderr)

    def test_cost_wrapper_preserves_two_distinct_evidence_routes_and_first_failure(self):
        child = ALIGNMENT / 'validate-provider-condition-evidence/script.sh'
        self.executable(self.root / child, '''#!/usr/bin/env python3
import json,os,sys
with open(os.environ['WRAPPER_CALLS'],'a') as out: out.write(json.dumps(sys.argv[1:])+'\\n')
first='target-cost-allocation-tag.yml' in sys.argv[2]
print(json.dumps({'verdict':'observed','code':'tag' if first else 'budget'}))
raise SystemExit(int(os.environ['WRAPPER_TAG_STATUS'] if first else os.environ['WRAPPER_BUDGET_STATUS']))
''')
        for first, second, status, count in [(0, 0, 0, 2), (17, 0, 17, 1), (0, 23, 23, 2)]:
            with self.subTest(first=first, second=second):
                result = self.run_script(TARGET / 'validate-cost-condition/script.sh', '--json',
                                         WRAPPER_TAG_STATUS=str(first), WRAPPER_BUDGET_STATUS=str(second))
                self.assertEqual(result.returncode, status, result.stderr)
                calls = self.calls()
                self.assertEqual(len(calls), count)
                for index, call in enumerate(calls):
                    expected = 'target-cost-allocation-tag.yml' if index == 0 else 'target-filtered-monthly-budget.yml'
                    self.assertTrue(call[1].endswith('/' + expected))
                    self.assertEqual(call[2:], ['--required-status', 'verified', '--required-status', 'waived-by-approved-exception', '--json'])

    def test_runtime_wrapper_reports_exact_argument_and_receipt_projection_failure(self):
        for option, code in [('--receipt', 'RECEIPT_ARGUMENT_MISSING'), ('--operation', 'OPERATION_ARGUMENT_MISSING')]:
            result = self.run_script(TARGET / 'inspect-runtime-alignment/script.sh', option)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr, 'DIAGNOSTIC_CODE=RUNTIME_ALIGNMENT_' + code + '\n')
            self.assertEqual(self.calls(), [])
        receipt = Path('scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh')
        for payload, code in [('{' + CANARY, 'JSON_INVALID'), ('{}', 'DIGEST_UNAVAILABLE'),
                              ('null', 'DIGEST_UNAVAILABLE'), (json.dumps(CANARY), 'DIGEST_UNAVAILABLE')]:
            source = '''#!/usr/bin/env python3
import json,os
with open(os.environ['WRAPPER_CALLS'],'a') as out: out.write(json.dumps(['receipt'])+'\\n')
print(PAYLOAD)
'''
            self.executable(self.root / receipt, source.replace('PAYLOAD', repr(payload)))
            result = self.run_script(TARGET / 'inspect-runtime-alignment/script.sh', '--receipt', 'qualified.json')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr, 'DIAGNOSTIC_CODE=RUNTIME_ALIGNMENT_RECEIPT_' + code + '\n')
            self.assertEqual(self.calls(), [['receipt']])
            self.assertNotIn(CANARY, result.stdout + result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_runtime_wrapper_retains_adapter_status_and_validates_returned_evidence(self):
        receipt = Path('scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh')
        adapter = ALIGNMENT / 'provider-adapters/aws/runtime-alignment/script.sh'
        validator = ALIGNMENT / 'validate-target-alignment/script.sh'
        child = '''#!/usr/bin/env python3
import json,os,sys
with open(os.environ['WRAPPER_CALLS'],'a') as out: out.write(json.dumps([ROLE,*sys.argv[1:]])+'\\n')
print(json.dumps({'image_digest':DIGEST,'verdict':'passed'}))
raise SystemExit(int(os.environ['WRAPPER_'+ROLE.upper()+'_STATUS']))
'''
        for path, role in [(receipt, 'receipt'), (adapter, 'adapter'), (validator, 'validator')]:
            self.executable(self.root / path, child.replace('ROLE', repr(role)).replace('DIGEST', repr(DIGEST)))
        for receipt_status, adapter_status, validator_status, expected, stages in [
            (0, 0, 0, 0, ['receipt', 'adapter', 'validator']),
            (17, 0, 0, 1, ['receipt']),
            (0, 23, 0, 23, ['receipt', 'adapter', 'validator']),
            (0, 23, 17, 1, ['receipt', 'adapter', 'validator']),
        ]:
            with self.subTest(stages=stages, adapter=adapter_status, validator=validator_status):
                result = self.run_script(TARGET / 'inspect-runtime-alignment/script.sh', '--receipt', 'qualified.json', '--operation', 'restore', '--json',
                                         WRAPPER_RECEIPT_STATUS=str(receipt_status), WRAPPER_ADAPTER_STATUS=str(adapter_status), WRAPPER_VALIDATOR_STATUS=str(validator_status))
                self.assertEqual(result.returncode, expected, result.stderr)
                calls = self.calls()
                self.assertEqual([call[0] for call in calls], stages)
                if 'adapter' in stages:
                    self.assertIn(DIGEST, calls[1])
                    self.assertEqual(calls[1][calls[1].index('--operation') + 1], 'restore')
                    self.assertEqual(calls[1][calls[1].index('--account-id') + 1], '337159794548')
                    self.assertIn('--evidence', calls[2])


if __name__ == '__main__':
    unittest.main(verbosity=2)
