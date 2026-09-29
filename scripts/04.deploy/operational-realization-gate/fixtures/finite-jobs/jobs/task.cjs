// Inert execution-protocol fixture. This is never a product or database job.
'use strict';
const mode = process.argv[2];
const checks = [{id: 'fixture-calculation', verdict: 'passed'}];
if ([1, 2, 3, 4].reduce((a, b) => a + b, 0) !== 10) process.exit(9);
const result = {
  schema: 'finite-job-terminal/v1',
  run_id: process.env.RELEASE_CONTROL_RUN_ID,
  profile_digest: process.env.RELEASE_CONTROL_PROFILE_DIGEST,
  outcome: 'completed', checks
};
function emit(code = 0) {
  process.stdout.write(JSON.stringify(result), () => process.exit(code));
}
switch (mode) {
  case 'success': emit(); break;
  case 'stderr-success': process.stderr.write('FIXTURE_PRIVATE_DIAGNOSTIC'); emit(); break;
  case 'nonzero': emit(7); break;
  case 'missing': process.exit(0); break;
  case 'malformed': process.stdout.write('{invalid-fixture'); break;
  case 'wrong-run': result.run_id = '0'.repeat(32); emit(); break;
  case 'wrong-profile': result.profile_digest = 'sha256:' + '0'.repeat(64); emit(); break;
  case 'duplicate': process.stdout.write(JSON.stringify(result).replace('{', '{"schema":"finite-job-terminal/v1",')); break;
  case 'extra-field': result.private_diagnostic = 'FIXTURE_PRIVATE_DIAGNOSTIC'; emit(); break;
  case 'timeout': setInterval(() => {}, 1000); break;
  case 'excessive-output': process.stdout.write('X'.repeat(8192)); break;
  default: process.exit(8);
}
