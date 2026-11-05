import { deepEqual, equal, throws } from 'node:assert/strict';
import { createDiagnosticRecord, defineDiagnostic } from '@kanbien/core/diagnostics';
import { bindPlatformDiagnosticContext, platformDiagnosticContext } from '../src/index';

const definition = defineDiagnostic({ code: 'fixture.configuration-invalid', version: 1,
  classification: { failureKind: 'configuration', failureSource: 'platform', severity: 'error', recovery: 'manual_investigation' },
  detail: { type: 'object', properties: { setting: { type: 'enum', values: ['database.port'] }, reason: { type: 'enum', values: ['missing'] } } },
} as const);
const record = createDiagnosticRecord(definition, { setting: 'database.port', reason: 'missing' });
if (!record.ok) throw new Error('fixture-invalid');
const context = { capability: 'persistence', operation: 'configure', stage: 'startup' as const };
const definitions = [definition];
const binding = bindPlatformDiagnosticContext(context, definitions);
const selected = binding.select(record.value);
deepEqual(selected, { record: record.value, context });
equal(Object.isFrozen(selected?.context), true);
context.operation = 'wrong-but-well-formed';
definitions.length = 0;
deepEqual(binding.select(record.value)?.context, { capability: 'persistence', operation: 'configure', stage: 'startup' });
throws(() => Object.assign(selected!.context, { stage: 'runtime' }));
equal(binding.select({ ...record.value, detail: { setting: 'database.schema', reason: 'missing' } }), undefined);
equal(binding.select({ ...record.value, detail: { setting: 'database.port', reason: 'synthetic-private-canary' } }), undefined);
equal(binding.select({ ...record.value, code: 'fixture.unregistered' }), undefined);
equal(binding.select({ ...record.value, definitionVersion: 2 }), undefined);
let getterReads = 0;
const accessor = Object.defineProperty({}, 'operation', { enumerable: true, get() { getterReads++; return 'synthetic-private-canary'; } });
for (const invalid of [undefined, {}, { capability: 'persistence', operation: 'configure' },
  { capability: 'persistence', operation: 'configure', stage: 'invented' },
  { capability: 'persistence', operation: 'configure', stage: 'startup', raw: 'synthetic-private-canary' }, accessor]) {
  equal(platformDiagnosticContext(invalid), undefined);
  throws(() => bindPlatformDiagnosticContext(invalid as never, [definition]), { message: 'PLATFORM_DIAGNOSTIC_CONTEXT_BINDING_INVALID' });
}
for (const invalid of [[], [definition, definition], Array(1), [null]]) {
  throws(() => bindPlatformDiagnosticContext({ capability: 'persistence', operation: 'configure', stage: 'startup' }, invalid as never), { message: 'PLATFORM_DIAGNOSTIC_CONTEXT_BINDING_INVALID' });
}
equal(getterReads, 0);
equal(JSON.stringify(selected).includes('synthetic-private-canary'), false);
console.log('Diagnostic context declaration, snapshot, allowed-record and attribution tests passed.');
