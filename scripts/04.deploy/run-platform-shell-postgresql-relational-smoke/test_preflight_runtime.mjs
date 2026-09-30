// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.test.relational-task-preflight
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [security, sre]
//   kind: script
//   purpose: Exercise each fixed task preflight and reject writes, permissive checks, unsafe arguments and output.
//   portability: {class: internal, targets: [kanbien/staging]}
//   effects: [read-only]
//   used_by:
//   - id: deploy.script.run-platform-shell-postgresql-relational-smoke.readme
//     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/README.md
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
const require=createRequire(import.meta.url);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const ts=require(process.env.RELATIONAL_PREFLIGHT_TYPESCRIPT_ROOT ?? path.join(root,'node_modules/typescript'));
assert.equal(ts.version,'5.9.3');
const sources=path.join(root,'infra/04.deploy/03.product/entrypoints');
const code=new Map();
for(const name of ['task','bootstrap.main','migration.main','relay.main','worker.main','restore-verify.main']) {
 const value=ts.transpileModule(fs.readFileSync(path.join(sources,`kanbien-platform-postgresql-${name}.ts`),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,strict:true},reportDiagnostics:true});
 assert.deepEqual(value.diagnostics.filter(d=>d.category===ts.DiagnosticCategory.Error),[]);
 code.set(name,value.outputText);
}
const operations=['bootstrap','migration','relay','worker','restore-verify'];
const secret=(username)=>JSON.stringify({username,password:'secret-canary-never-output',host:'db.fixture.invalid',port:5432});
function harness(operation, options={}) {
 const queries=[]; const output=[]; let released=0; let closed=0; let connected=0; let effects=0; let created=0;
 const proc={argv:['node','entrypoint',...(options.args ?? ['--preflight'])],exitCode:undefined,env:{
  RELATIONAL_MASTER_SECRET_JSON:JSON.stringify({username:'referenceadmin',password:'secret-canary-never-output'}),
  RELATIONAL_MIGRATION_SECRET_JSON:secret('psmokemigrate'),RELATIONAL_RUNTIME_SECRET_JSON:secret('psmokeruntime'),
  RELATIONAL_CONFIG_JSON:JSON.stringify({database:'platformsmoke',schema:'platform_smoke',tls:'verify-full',runtime_secret_arn:'arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture-runtime',migration_secret_arn:'arn:aws:secretsmanager:eu-west-1:337159794548:secret:fixture-migration'}),
  RELATIONAL_SMOKE_QUEUE_URL:'queue-reference-canary',RELATIONAL_RESTORE_HOST:'kanbien-staging-platform-relational-restore-proof-fixture.host.eu-west-1.rds.amazonaws.com',...(options.env ?? {})}};
 const client={query:async statement=>{
  queries.push(statement);
  if(options.failQuery===queries.length) throw Error('provider-secret-canary');
  let row;
  if(statement.text==='BEGIN READ ONLY' || statement.text==='ROLLBACK') return {rows:[]};
  if(statement.text.includes(' AS identity_ok')) row={identity_ok:true,database_ok:true,read_only:true,engine_ok:true,tls_active:true};
  else if(statement.text.includes(' AS principal_authority')) row={principal_authority:true,schema_authority:true};
  else if(statement.text.includes(' AS least_privileged')) row={least_privileged:true,no_memberships:true};
  else if(statement.text.includes(' AS schema_access')) row={schema_access:true,schema_authority:operation==='migration',database_authority:operation==='migration',schema_owned:operation==='migration'};
  else if(statement.text.includes(' AS table_count')) row={table_count:operation==='restore-verify'?2:4,required_access:true};
  else throw Error('unrecognized-query');
  if(options.mutate) row=options.mutate({...row});
  return {rows:options.emptyRows?[]:[row]};
 },release(){released++;}};
 const pool={connect:async()=>{connected++; if(options.failConnect)throw Error('connection-secret-canary'); return client;},end:async()=>{closed++;},query:async()=>{effects++;throw Error('effect-execution-sentinel');}};
 const dependencies=new Proxy({}, {get(_target,name){if(name==='__esModule')return true;return ()=>{effects++;throw Error('effect-execution-sentinel');};}});
 function evaluate(name,req){
  const exp={}; const context=vm.createContext({exports:exp,require:req,process:proc,console:{log(value){output.push(JSON.parse(value));}},Buffer,setTimeout,clearTimeout});
  vm.runInContext(code.get(name),context,{timeout:1000});return exp;
 }
 const helper=evaluate('task',name=>{
  if(name==='node:fs')return {readFileSync(){if(options.failCa)throw Error('ca-canary');return '-----BEGIN CERTIFICATE-----\nfixture\n-----END CERTIFICATE-----';}};
  if(name==='@kanbien/platform-adapter-aws-persistence-postgresql')return {postgreSqlPersistenceConfiguration(value){assert.equal(value.tls.mode,'verify-full');return {ok:true,value};},createNodePostgreSqlConnectionPool(configuration,credentials){created++;assert.equal(configuration.tls.mode,'verify-full');assert.ok(credentials.certificateAuthority.startsWith('-----BEGIN CERTIFICATE-----'));return pool;}};
  throw Error('unexpected-helper-import');
 });
 const run=async()=>{evaluate(operation+'.main',name=>name==='./kanbien-platform-postgresql-task'?helper:dependencies);await new Promise(resolve=>setImmediate(resolve));};
 return {helper,proc,queries,output,pool,run,counts:()=>({released,closed,connected,effects,created})};
}
function assertReadOnly(h) {
 assert.equal(h.queries[0].text,'BEGIN READ ONLY');assert.equal(h.queries.at(-1).text,'ROLLBACK');
 assert.ok(h.queries.every(q=>q.text==='BEGIN READ ONLY'||q.text==='ROLLBACK'||q.text.startsWith('SELECT ')));
 assert.equal(h.counts().effects,0);assert.equal(h.counts().released,1);assert.equal(h.counts().closed,1);
}
for(const operation of operations) {
 test(`${operation} preflight enters actual helper before effects and emits disjoint safe result`,async()=>{
  const h=harness(operation);await h.run();assertReadOnly(h);assert.equal(h.proc.exitCode,undefined);
  assert.deepEqual(h.output,[{schema:'relational-task-preflight/v1',scope:'read-only-database-prerequisites',operation,verdict:'passed',authorized:false}]);
  assert.ok(!JSON.stringify(h.output).includes('canary'));
 });
 test(`${operation} preflight failure stays redacted and never enters effects`,async()=>{
  const h=harness(operation,{failQuery:2});await h.run();assertReadOnly(h);assert.equal(h.proc.exitCode,1);assert.equal(h.output[0].verdict,'failed');assert.ok(!JSON.stringify(h.output).includes('canary'));
 });
 test(`${operation} unknown combined arguments reject before credentials or pool`,async()=>{
  const h=harness(operation,{args:['--preflight','secret-canary-extra']});await h.run();assert.equal(h.counts().created,0);assert.equal(h.counts().effects,0);assert.equal(h.proc.exitCode,1);assert.equal(h.output[0].verdict,'failed');assert.ok(!JSON.stringify(h.output).includes('canary'));
 });
 test(`${operation} duplicate preflight flag rejects before pool`,async()=>{
  const h=harness(operation,{args:['--preflight','--preflight']});await h.run();assert.equal(h.counts().created,0);assert.equal(h.proc.exitCode,1);
 });
 test(`${operation} no argument preserves the existing effect path`,async()=>{
  const h=harness(operation,{args:[]});await h.run();assert.ok(h.counts().effects>0);assert.equal(h.output[0]?.schema,undefined);assert.equal(h.proc.exitCode,1);
 });
}
for(const field of ['identity_ok','database_ok','read_only','engine_ok','tls_active']) {
 test(`false ${field} blocks preflight`,async()=>{const h=harness('bootstrap',{mutate:r=>field in r?{...r,[field]:false}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
}
for(const field of ['principal_authority','schema_authority']) {
 test(`bootstrap missing ${field} blocks`,async()=>{const h=harness('bootstrap',{mutate:r=>field in r?{...r,[field]:false}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
}
for(const operation of ['migration','relay','worker','restore-verify']) {
 for(const field of ['least_privileged','no_memberships','schema_access']) {
  test(`${operation} false ${field} blocks`,async()=>{const h=harness(operation,{mutate:r=>field in r?{...r,[field]:false}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
 }
}
for(const field of ['schema_authority','schema_owned']) {
 test(`migration missing ${field} blocks`,async()=>{const h=harness('migration',{mutate:r=>field in r?{...r,[field]:false}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
}
for(const field of ['schema_authority','database_authority','schema_owned']) {
 test(`runtime unexpected ${field} blocks`,async()=>{const h=harness('worker',{mutate:r=>field in r?{...r,[field]:true}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
}
for(const value of [false,null,'true',1]) {
 test(`runtime privilege result ${String(value)} refuses non-true proof`,async()=>{const h=harness('worker',{mutate:r=>'required_access' in r?{...r,required_access:value}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
}
test('each required DML privilege is independently asserted rather than ANY privilege',async()=>{const h=harness('worker');await h.run();const sql=h.queries.find(q=>q.text.includes(' AS table_count')).text;for(const p of ['SELECT','INSERT','UPDATE','DELETE'])assert.ok(sql.includes(`c.oid, '${p}')`));assert.equal(sql.match(/ AND pg_catalog.has_table_privilege/g).length,3);});
test('restore requires only its two selected read tables and validated isolated host',async()=>{const h=harness('restore-verify');await h.run();const q=h.queries.find(q=>q.text.includes(' AS table_count'));assert.deepEqual(Array.from(q.values[0]),['platform_smoke_work_item','platform_outbox']);assert.ok(!q.text.includes("c.oid, 'INSERT')"));});
test('restore primary host cannot enter preflight',async()=>{const h=harness('restore-verify',{env:{RELATIONAL_RESTORE_HOST:'primary.fixture.invalid'}});await h.run();assert.equal(h.counts().connected,0);assert.equal(h.output[0].verdict,'failed');});
test('missing required table blocks instead of accepting matching subset',async()=>{const h=harness('worker',{mutate:r=>'table_count' in r?{...r,table_count:3}:r});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
test('rollback failure cannot yield a passed receipt',async()=>{const h=harness('bootstrap',{failQuery:4});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
test('failed connection yields safe failure without phantom release',async()=>{const h=harness('bootstrap',{failConnect:true});await h.run();assert.equal(h.output[0].verdict,'failed');assert.equal(h.counts().released,0);assert.equal(h.counts().closed,1);});
test('missing CA fails before database queries',async()=>{const h=harness('bootstrap',{failCa:true});await h.run();assert.equal(h.counts().connected,0);assert.equal(h.output[0].verdict,'failed');});
test('wrong runtime principal rejects before database connection',async()=>{const h=harness('worker',{env:{RELATIONAL_RUNTIME_SECRET_JSON:secret('referenceadmin')}});await h.run();assert.equal(h.counts().connected,0);assert.equal(h.output[0].verdict,'failed');});
test('empty catalog result blocks',async()=>{const h=harness('bootstrap',{emptyRows:true});await h.run();assertReadOnly(h);assert.equal(h.output[0].verdict,'failed');});
test('non-preflight extra arguments reject before effects',async()=>{const h=harness('bootstrap',{args:['--sql','secret-canary']});await h.run();assert.equal(h.counts().created,0);assert.equal(h.counts().effects,0);assert.equal(h.proc.exitCode,1);assert.ok(!JSON.stringify(h.output).includes('canary'));});

for(const [name,patch] of [
 ['migration principal',{RELATIONAL_MIGRATION_SECRET_JSON:secret('wrongprincipal')}],
 ['runtime principal',{RELATIONAL_RUNTIME_SECRET_JSON:secret('wrongprincipal')}],
 ['runtime host',{RELATIONAL_RUNTIME_SECRET_JSON:JSON.stringify({username:'psmokeruntime',password:'secret-canary',host:'other.fixture.invalid',port:5432})}],
 ['runtime port',{RELATIONAL_RUNTIME_SECRET_JSON:JSON.stringify({username:'psmokeruntime',password:'secret-canary',host:'db.fixture.invalid',port:5433})}],
])test(`bootstrap mismatched ${name} blocks before a connection`,async()=>{const h=harness('bootstrap',{env:patch});await h.run();assert.equal(h.counts().connected,0);assert.equal(h.output[0].verdict,'failed');assert.equal(h.counts().effects,0);});
