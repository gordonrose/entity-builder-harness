"""Owned real PostgreSQL qualification using the existing bounded Docker engine."""

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.dependency-effect-engine
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Run exact packaged commands against an isolated TLS PostgreSQL engine and independently inspect their effects.
#   portability: {class: internal, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.script.dependency-effects
#     path: scripts/04.deploy/operational-realization-gate/dependency_effects.py

import hashlib
import json
from pathlib import Path
import re
import secrets
import time
import uuid

import container_engine as containers
import dependency_effect_contracts as contracts
import dependency_preflight_contracts as preflight

HOST = 'release-control-postgresql'
LABEL = containers.OWNER_LABEL
DB_USER = '999:999'
DB_COMMAND = ['-euc', '''umask 077
cp /qualification/server.key /tmp/server.key
chmod 600 /tmp/server.key
cp /qualification/observer.pgpass /tmp/observer.pgpass
chmod 600 /tmp/observer.pgpass
cp /qualification/runtime.pgpass /tmp/runtime.pgpass
chmod 600 /tmp/runtime.pgpass
exec /usr/local/bin/docker-entrypoint.sh postgres -c unix_socket_directories=/tmp,/var/run/postgresql -c ssl=on -c ssl_cert_file=/qualification/server.crt -c ssl_key_file=/tmp/server.key -c hba_file=/qualification/pg_hba.conf -c log_statement=none -c log_connections=off
''']
STATE_SQL = """SELECT json_build_object(
 'roles', COALESCE((SELECT json_agg(json_build_object('name',rolname,'login',rolcanlogin,'elevated',rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls) ORDER BY rolname) FROM pg_roles WHERE rolname IN ('psmokemigrate','psmokeruntime')), '[]'::json),
 'memberships', COALESCE((SELECT json_agg(json_build_object('role',pg_get_userbyid(m.roleid),'member',pg_get_userbyid(m.member)) ORDER BY m.roleid,m.member) FROM pg_auth_members m WHERE pg_get_userbyid(m.member) IN ('psmokemigrate','psmokeruntime') OR pg_get_userbyid(m.roleid) IN ('psmokemigrate','psmokeruntime')), '[]'::json),
 'schema_owner', (SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='platform_smoke'),
 'tables', COALESCE((SELECT json_agg(json_build_object('name',c.relname,'owner',pg_get_userbyid(c.relowner),'runtime_dml',has_table_privilege('psmokeruntime',c.oid,'SELECT') AND has_table_privilege('psmokeruntime',c.oid,'INSERT') AND has_table_privilege('psmokeruntime',c.oid,'UPDATE') AND has_table_privilege('psmokeruntime',c.oid,'DELETE')) ORDER BY c.relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='platform_smoke' AND c.relkind='r'), '[]'::json),
 'columns', COALESCE((SELECT json_agg(json_build_object('table',c.relname,'position',a.attnum,'name',a.attname,'type',format_type(a.atttypid,a.atttypmod),'nullable',NOT a.attnotnull,'default',pg_get_expr(d.adbin,d.adrelid)) ORDER BY c.relname,a.attnum) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum WHERE n.nspname='platform_smoke' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped), '[]'::json),
 'constraints', COALESCE((SELECT json_agg(json_build_object('table',c.relname,'kind',k.contype,'definition',pg_get_constraintdef(k.oid)) ORDER BY c.relname,k.contype,pg_get_constraintdef(k.oid)) FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='platform_smoke'), '[]'::json),
 'runtime_schema_create', (SELECT has_schema_privilege('psmokeruntime',oid,'CREATE') FROM pg_namespace WHERE nspname='platform_smoke'),
 'runtime_database_create', CASE WHEN EXISTS(SELECT FROM pg_roles WHERE rolname='psmokeruntime') THEN has_database_privilege('psmokeruntime','platformsmoke','CREATE') ELSE NULL END,
 'migration_schema_create', (SELECT has_schema_privilege('psmokemigrate',oid,'CREATE') FROM pg_namespace WHERE nspname='platform_smoke')
)::text"""
HISTORY_SQL = '''SELECT COALESCE(json_agg(json_build_object('id',migration_id,'checksum',checksum,'tool_version',tool_version,'applied_at',applied_at) ORDER BY migration_id), '[]'::json)::text FROM platform_smoke.platform_migration_history'''
SQL = {
    'state': STATE_SQL,
    'history': HISTORY_SQL,
    'preflight-counts': "SELECT json_build_object(" + ','.join(
        "'" + name + "',(SELECT count(*) FROM platform_smoke." + name + ')'
        for name in preflight.TABLES) + " )::text",

    'version': "SELECT current_setting('server_version_num')",
    'tls': "SELECT ssl::text FROM pg_stat_ssl WHERE pid=pg_backend_pid()",
    'corrupt': "UPDATE platform_smoke.platform_migration_history SET checksum=repeat('0',64) WHERE migration_id='v0002_platform_smoke_work_item'",
    'runtime-denied': 'CREATE TABLE platform_smoke.forbidden_ddl (id integer)',
    **{action.lower() + '-' + right.lower(): action + ' ' + right + ' ON platform_smoke.platform_smoke_work_item ' + ('FROM' if action == 'REVOKE' else 'TO') + ' psmokeruntime'
       for action in ('REVOKE', 'GRANT') for right in ('SELECT', 'INSERT', 'UPDATE', 'DELETE')},
    'runtime-dml': "BEGIN; INSERT INTO platform_smoke.platform_smoke_work_item VALUES ('release-control-local-proof','accepted',1,CURRENT_TIMESTAMP); UPDATE platform_smoke.platform_smoke_work_item SET revision=2 WHERE id='release-control-local-proof'; DELETE FROM platform_smoke.platform_smoke_work_item WHERE id='release-control-local-proof'; ROLLBACK",
}


def fail(code):
    contracts.fail(code)


def image_digest(raw):
    if type(raw) is not str or not containers.IMAGE_PATTERN.fullmatch(raw):
        fail('dependency-image-invalid')
    return raw


def decode_environment(rows):
    result = {}
    if type(rows) is not list or len(rows) > 40:
        fail('environment-invalid')
    for row in rows:
        if type(row) is not str or len(row) > 16384 or '=' not in row:
            fail('environment-invalid')
        key, value = row.split('=', 1)
        if key in result:
            fail('environment-invalid')
        result[key] = value
    return result


class DependencyEngine(containers.Engine):
    """Uses the shared safe transport/ownership; ordinary no-network modes are unchanged."""

    def __init__(self, scratch, runner=None):
        super().__init__(scratch, runner)
        self.network = None
        self.specs = {}
        self.db = None
        self.run_id = uuid.uuid4().hex
        self.fixture = None
        self.authority = None
        self.credentials = {role: secrets.token_hex(24) for role in ('master', 'migration', 'runtime')}

    def dependency_identity(self, lock, *, acquire=False):
        contracts.validate_lock(lock)
        if acquire:
            self._call(['pull', '--platform', 'linux/amd64', lock['image']], timeout=900)
        raw = containers._one(self._call(['image', 'inspect', lock['image']]))
        known_refs = {lock['image'], lock['image'].removeprefix('docker.io/library/')}
        if (raw.get('Os') != 'linux' or raw.get('Architecture') != 'amd64'
                or raw.get('Id') not in {lock['config_digest'], lock['image'].split('@')[1]}
                or not (set(raw.get('RepoDigests', [])) & known_refs)):
            fail('dependency-image-mismatch')
        config = raw.get('Config')
        if type(config) is not dict:
            fail('dependency-image-invalid')
        self._images[raw['Id']] = {'environment': decode_environment(config.get('Env'))}
        return raw['Id']

    def prepare_certificates(self):
        self.fixture = self.private / 'dependency-inputs'
        self.authority = self.private / 'product-ca'
        self.fixture.mkdir(mode=0o755)
        self.authority.mkdir(mode=0o755)
        # Ancestor engine directory is mode0700. Only the owned DB sees private material.
        for name, data in [('master.password', self.credentials['master']),
                           ('observer.pgpass', '*:*:*:postgres:' + self.credentials['master']),
                           ('runtime.pgpass', '*:*:*:psmokeruntime:' + self.credentials['runtime']),
                           ('pg_hba.conf', 'local all all trust\nhostssl all all 0.0.0.0/0 scram-sha-256\nhostssl all all ::/0 scram-sha-256\n')]:
            path = self.fixture / name
            path.write_text(data + '\n')
            path.chmod(0o644)
        ca, key = self.fixture / 'ca.crt', self.fixture / 'ca.key'
        server_key, csr, cert = (self.fixture / name for name in ('server.key', 'server.csr', 'server.crt'))
        calls = [
            ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key), '-out', str(ca), '-days', '2', '-subj', '/CN=ReleaseControlDisposableCA'],
            ['req', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(server_key), '-out', str(csr), '-subj', '/CN=' + HOST, '-addext', 'subjectAltName=DNS:' + HOST],
            ['x509', '-req', '-in', str(csr), '-CA', str(ca), '-CAkey', str(key), '-CAcreateserial', '-out', str(cert), '-days', '2', '-copy_extensions', 'copy'],
        ]
        for args in calls:
            result = containers._bounded_runner(['/usr/bin/openssl', *args], cwd=self.private, env=self.env,
                                                 timeout=30, max_output=16384)
            if result.returncode:
                fail('fixture-certificate-failed')
        server_key.chmod(0o644)
        (self.authority / 'ca.crt').write_bytes(ca.read_bytes())
        (self.authority / 'ca.crt').chmod(0o644)
        return 'sha256:' + hashlib.sha256(ca.read_bytes()).hexdigest()

    def create_network(self):
        if self.network is not None:
            fail('network-already-owned')
        token = uuid.uuid4().hex
        self.network = {'name': 'release-control-dependency-' + token, 'token': token, 'id': None}
        raw = self._call(['network', 'create', '--internal', '--driver', 'bridge',
                          '--label', LABEL + '=' + token, self.network['name']], max_output=4096).decode('ascii').strip()
        if not containers.CONTAINER_PATTERN.fullmatch(raw):
            fail('network-id-invalid')
        self.network['id'] = raw
        self.inspect_network()

    def inspect_network(self):
        if self.network is None:
            fail('network-not-owned')
        value = containers._one(self._call(['network', 'inspect', self.network['name']], max_output=65536))
        if (value.get('Name') != self.network['name']
                or type(value.get('Id')) is not str or not containers.CONTAINER_PATTERN.fullmatch(value['Id'])
                or (self.network['id'] is not None and value.get('Id') != self.network['id'])
                or value.get('Labels', {}).get(LABEL) != self.network['token']
                or value.get('Internal') is not True or value.get('Driver') != 'bridge'
                or value.get('Scope') != 'local' or value.get('Ingress') is not False
                or type(value.get('Containers')) is not dict
                or not set(value['Containers']) <= {o['id'] for o in self._owned.values()}):
            fail('network-ownership-invalid')
        self.network['id'] = value['Id']
        return value

    def _create_bound(self, image_id, *, dependency=False, command=None, environment=None):
        self.inspect_network()
        token = uuid.uuid4().hex
        name = 'release-control-' + token
        user = DB_USER if dependency else containers.SETTINGS['user']
        entrypoint = ['/bin/bash'] if dependency else [containers.NODE]
        command = DB_COMMAND if dependency else command
        if not dependency and command not in [*contracts.COMMANDS.values(), *preflight.COMMANDS.values()]:
            fail('command-invalid')
        directory = self.fixture if dependency else self.authority
        destination = '/qualification' if dependency else '/run/release-control'
        if directory is None or directory.is_symlink() or not directory.is_dir() or directory.parent != self.private:
            fail('fixture-path-invalid')
        tmpfs = {'/tmp': 'rw,noexec,nosuid,nodev,size=16m,uid=' + user.split(':')[0]}
        if dependency:
            tmpfs.update({'/var/lib/postgresql/data': 'rw,noexec,nosuid,nodev,size=256m,uid=999',
                          '/var/run/postgresql': 'rw,noexec,nosuid,nodev,size=16m,uid=999'})
        envfile = self.private / (token + '.env')
        if type(environment) is not dict or any(type(k) is not str or type(v) is not str or '\n' in v or '\x00' in v for k,v in environment.items()):
            fail('environment-invalid')
        envfile.write_text(''.join(k + '=' + v + '\n' for k,v in sorted(environment.items())))
        envfile.chmod(0o600)
        args = ['create', '--name', name, '--label', LABEL + '=' + token,
                '--network', self.network['name'], '--read-only', '--user', user,
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--memory', '512m',
                '--memory-swap', '512m', '--cpus', '1', '--pids-limit', '128', '--ipc', 'none',
                '--restart', 'no', '--stop-timeout', '10', '--log-driver', 'none', '--no-healthcheck',
                '--entrypoint', entrypoint[0], '--env-file', str(envfile),
                '--mount', 'type=bind,source=' + str(directory) + ',target=' + destination + ',readonly']
        if dependency:
            args.extend(['--network-alias', HOST])
        for path, options in tmpfs.items():
            args.extend(['--tmpfs', path + ':' + options])
        args.extend([image_id, *command])
        self._owned[name] = {'token': token, 'image': image_id, 'id': None}
        self.specs[name] = {'image': image_id, 'entrypoint': entrypoint, 'command': command,
                            'user': user, 'tmpfs': tmpfs, 'source': str(directory), 'destination': destination,
                            'environment': {**self._images[image_id]['environment'], **environment}}
        try:
            raw = self._call(args, max_output=4096).decode('ascii').strip()
            if not containers.CONTAINER_PATTERN.fullmatch(raw):
                fail('container-id-invalid')
            self._owned[name]['id'] = raw
            self.inspect_bound(name, running=False)
        except (containers.EngineFailure, contracts.release.ReleaseFailure, UnicodeError, KeyboardInterrupt):
            # Cleanup is owned-only; failures remain visible to the orchestration finally block.
            raise
        return name

    def inspect_bound(self, name, *, running):
        self.inspect_network()
        value = self._container(name)
        spec = self.specs[name]
        config, host, state = value.get('Config', {}), value.get('HostConfig', {}), value.get('State', {})
        if (value.get('Image') != spec['image'] or config.get('Image') != spec['image']
                or config.get('Entrypoint') != spec['entrypoint'] or config.get('Cmd') != spec['command']
                or (spec['user'] == containers.SETTINGS['user'] and config.get('WorkingDir') != '/app')
                or config.get('User') != spec['user'] or decode_environment(config.get('Env')) != spec['environment']
                or host.get('NetworkMode') != self.network['name'] or host.get('ReadonlyRootfs') is not True
                or host.get('Privileged') is not False or host.get('CapDrop') != ['ALL'] or host.get('CapAdd')
                or host.get('SecurityOpt') != ['no-new-privileges'] or host.get('Memory') != 536870912
                or host.get('MemorySwap') != 536870912 or host.get('NanoCpus') != 1000000000
                or host.get('PidsLimit') != 128 or host.get('IpcMode') != 'none'
                or host.get('Binds') or host.get('PortBindings') or host.get('PublishAllPorts') is not False
                or host.get('Tmpfs') != spec['tmpfs'] or host.get('RestartPolicy', {}).get('Name') != 'no'
                or host.get('LogConfig', {}).get('Type') != 'none' or host.get('Devices') or host.get('DeviceRequests')
                or type(state.get('Running')) is not bool or (running is not None and state['Running'] is not running)
                or state.get('OOMKilled') is not False):
            fail('container-restriction-mismatch')
        mounts = value.get('Mounts')
        if (type(mounts) is not list or len(mounts) != 1 or mounts[0].get('Type') != 'bind'
                or mounts[0].get('Source') != spec['source'] or mounts[0].get('Destination') != spec['destination']
                or mounts[0].get('RW') is not False):
            fail('container-mount-mismatch')
        if set(value.get('NetworkSettings', {}).get('Networks', {})) != {self.network['name']}:
            fail('container-network-mismatch')
        return state

    def start_dependency(self, image_id):
        environment = {'PGDATA': '/var/lib/postgresql/data/pgdata', 'PGHOST': '/tmp',
                       'POSTGRES_DB': 'platformsmoke', 'POSTGRES_PASSWORD_FILE': '/qualification/master.password',
                       'POSTGRES_INITDB_ARGS': '--auth-local=trust --auth-host=scram-sha-256'}
        self.db = self._create_bound(image_id, dependency=True, environment=environment)
        self._call(['start', self._owned[self.db]['id']], max_output=4096)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.inspect_bound(self.db, running=None)['Running'] is not True:
                fail('dependency-start-failed')
            value = self._execute(['exec', '--user', DB_USER, self._owned[self.db]['id'],
                '/usr/lib/postgresql/17/bin/pg_isready', '-q', '-h', '/tmp', '-U', 'postgres', '-d', 'platformsmoke'],
                timeout=3, max_output=4096)
            if value.returncode == 0:
                # pg_isready can observe the temporary initialization server. Require TLS final listener.
                tls = self._execute(['exec', '--user', DB_USER, self._owned[self.db]['id'],
                    '/usr/lib/postgresql/17/bin/psql', '-XAt', '-v', 'ON_ERROR_STOP=1', '-h', '/tmp',
                    '-U', 'postgres', '-d', 'platformsmoke', '-c', "SELECT current_setting('ssl')"], timeout=3, max_output=4096)
                if tls.returncode == 0 and tls.stdout.strip() == b'on':
                    break
            time.sleep(0.2)
        else:
            fail('dependency-start-timeout')
        if self.sql('version').strip() != b'170011':
            fail('dependency-version-mismatch')

    def sql(self, operation, *, expected_failure=False):
        if operation not in SQL:
            fail('observer-operation-invalid')
        self.inspect_bound(self.db, running=True)
        runtime = operation in {'runtime-denied', 'runtime-dml'}
        tls = ['--env', 'PGPASSFILE=/tmp/runtime.pgpass', '--env', 'PGSSLMODE=verify-full',
               '--env', 'PGSSLROOTCERT=/qualification/ca.crt'] if runtime else []
        result = self._execute(['exec', '--user', DB_USER, *tls, self._owned[self.db]['id'],
            '/usr/lib/postgresql/17/bin/psql', '-XAt', '-v', 'ON_ERROR_STOP=1', '-v', 'VERBOSITY=sqlstate',
            '-h', HOST if runtime else '/tmp', '-U', 'psmokeruntime' if runtime else 'postgres',
            '-d', 'platformsmoke', '-c', SQL[operation]], timeout=15, max_output=16384)
        if (result.returncode != 0) != expected_failure:
            fail('observer-query-failed')
        if expected_failure and not re.search(rb'ERROR:\s+42501(?:\s|$)', result.stderr):
            fail('observer-failure-category-mismatch')
        self.inspect_bound(self.db, running=True)
        return result.stdout if not expected_failure else b''

    def verify_tls(self):
        self.inspect_bound(self.db, running=True)
        output = self._call(['exec', '--user', DB_USER, '--env', 'PGPASSFILE=/tmp/observer.pgpass',
            '--env', 'PGSSLMODE=verify-full', '--env', 'PGSSLROOTCERT=/qualification/ca.crt',
            self._owned[self.db]['id'], '/usr/lib/postgresql/17/bin/psql', '-XAt', '-v', 'ON_ERROR_STOP=1',
            '-h', HOST, '-U', 'postgres', '-d', 'platformsmoke', '-c', SQL['tls']], timeout=15, max_output=4096)
        if output.strip() != b'true':
            fail('tls-observation-failed')

    def snapshot(self):
        value = containers._json(self.sql('state'))
        wanted = {'roles', 'memberships', 'schema_owner', 'tables', 'runtime_schema_create', 'runtime_database_create', 'migration_schema_create', 'columns', 'constraints'}
        if type(value) is not dict or set(value) != wanted or type(value['tables']) is not list:
            fail('observer-output-invalid')
        value['history'] = containers._json(self.sql('history')) if any(t.get('name') == 'platform_migration_history' for t in value['tables']) else []
        return value

    def preflight_snapshot(self):
        state = self.snapshot()
        present = {row['name'] for row in state['tables']} & set(preflight.TABLES)
        if present and present != set(preflight.TABLES):
            fail('preflight-observer-tables-invalid')
        counts = containers._json(self.sql('preflight-counts')) if present else {}
        if (type(counts) is not dict or set(counts) != present
                or any(type(value) is not int or value < 0 for value in counts.values())):
            fail('preflight-observer-output-invalid')
        return {'state': state, 'row_counts': counts}

    def run_task(self, image_id, task, case, expected):
        if task not in contracts.COMMANDS or (case, task, expected) not in {
                row[:3] for row in contracts.CASES}:
            fail('command-invalid')
        return self._run_packaged(image_id, task, case, expected, preflight_mode=False)

    def run_preflight(self, image_id, task, case, expected):
        if task not in preflight.COMMANDS or (case, task, expected) not in {
                row[:3] for row in preflight.CASES}:
            fail('preflight-command-invalid')
        return self._run_packaged(image_id, task, case, expected, preflight_mode=True)

    def _run_packaged(self, image_id, task, case, expected, *, preflight_mode):
        attempt = uuid.uuid4().hex
        secret = lambda username, password: json.dumps({'username': username, 'password': password, 'host': HOST, 'port': 5432}, separators=(',', ':'))
        environment = {
            'RELATIONAL_TLS_CA_MODE': 'local-qualification-v1', 'RELATIONAL_LOCAL_QUALIFICATION_ID': attempt,
            'RELATIONAL_MASTER_SECRET_JSON': json.dumps({'username': 'postgres', 'password': self.credentials['master']}),
            'RELATIONAL_MIGRATION_SECRET_JSON': secret('psmokemigrate', self.credentials['migration']),
            'RELATIONAL_RUNTIME_SECRET_JSON': secret('psmokeruntime', self.credentials['runtime']),
            'RELATIONAL_CONFIG_JSON': json.dumps({'database': 'platformsmoke', 'schema': 'platform_smoke', 'tls': 'verify-full',
                'runtime_secret_arn': 'arn:aws:secretsmanager:eu-west-1:337159794548:secret:local-runtime',
                'migration_secret_arn': 'arn:aws:secretsmanager:eu-west-1:337159794548:secret:local-migration'}),
        }
        if case == 'bootstrap-binding-invalid':
            environment.pop('RELATIONAL_LOCAL_QUALIFICATION_ID')
        elif case == 'bootstrap-untrusted-ca':
            environment.pop('RELATIONAL_TLS_CA_MODE')
            environment.pop('RELATIONAL_LOCAL_QUALIFICATION_ID')
        elif case in {'bootstrap-bad-password', 'bootstrap-denied-identity'}:
            environment['RELATIONAL_MASTER_SECRET_JSON'] = json.dumps({'username': 'postgres', 'password': secrets.token_hex(24)})
        elif case in {'migration-denied', 'migration-denied-identity'}:
            environment['RELATIONAL_MIGRATION_SECRET_JSON'] = environment['RELATIONAL_RUNTIME_SECRET_JSON']
        if task in {'relay', 'worker'}:
            environment['RELATIONAL_SMOKE_QUEUE_URL'] = 'https://invalid.example/local-preflight-only'
        # Match each actual target task's least-privilege injection, including omissions.
        allowed = {'RELATIONAL_TLS_CA_MODE', 'RELATIONAL_LOCAL_QUALIFICATION_ID'} | (
            {'RELATIONAL_MASTER_SECRET_JSON', 'RELATIONAL_MIGRATION_SECRET_JSON', 'RELATIONAL_RUNTIME_SECRET_JSON'}
            if task == 'bootstrap' else ({'RELATIONAL_MIGRATION_SECRET_JSON', 'RELATIONAL_CONFIG_JSON'}
            if task == 'migration' else {'RELATIONAL_RUNTIME_SECRET_JSON', 'RELATIONAL_CONFIG_JSON', 'RELATIONAL_SMOKE_QUEUE_URL'}))
        environment = {key: value for key, value in environment.items() if key in allowed}
        started = time.monotonic()
        name = self._create_bound(image_id, command=(preflight.COMMANDS if preflight_mode else contracts.COMMANDS)[task], environment=environment)
        try:
            result = self._execute(['start', '--attach', self._owned[name]['id']], timeout=90, max_output=4096)
            state = self.inspect_bound(name, running=False)
            wanted_exit = 0 if expected in {'succeeded', 'passed'} else 1
            if result.returncode != wanted_exit or type(state.get('ExitCode')) is not int or state['ExitCode'] != wanted_exit:
                fail('task-outcome-mismatch')
            terminal = preflight.terminal(result.stdout, task, expected) if preflight_mode else contracts.terminal(result.stdout, task, expected, failure_category={
                'bootstrap-binding-invalid': 'bootstrap-input-validation-failure',
                'bootstrap-untrusted-ca': 'bootstrap-database-tls-failure',
                'bootstrap-bad-password': 'bootstrap-database-authentication-failure',
            }.get(case))
            return {'attempt_id': attempt, 'exit_code': wanted_exit, 'terminal_digest': terminal,
                    'elapsed_ms': int((time.monotonic() - started) * 1000)}
        finally:
            self._cleanup(name)
            self.specs.pop(name, None)

    def restore_checksum(self, expected):
        # SQL literal comes only from reviewed closed expectations, never task output.
        contracts.validate_expectations(expected)
        checksum = expected['migration_checksums']['v0002_platform_smoke_work_item']
        self.inspect_bound(self.db, running=True)
        self._call(['exec', '--user', DB_USER, self._owned[self.db]['id'],
            '/usr/lib/postgresql/17/bin/psql', '-XAt', '-v', 'ON_ERROR_STOP=1', '-h', '/tmp',
            '-U', 'postgres', '-d', 'platformsmoke', '-c',
            "UPDATE platform_smoke.platform_migration_history SET checksum='" + checksum + "' WHERE migration_id='v0002_platform_smoke_work_item'"],
            timeout=15, max_output=4096)

    def cleanup_all(self):
        failed = False
        for name in list(self._owned):
            try:
                self._cleanup(name)
            except (containers.EngineFailure, contracts.release.ReleaseFailure, KeyboardInterrupt):
                failed = True
        if self.network is not None:
            try:
                value = self.inspect_network()
                if value['Containers']:
                    fail('network-cleanup-failed')
                self._call(['network', 'rm', self.network['id']], max_output=4096)
                remaining = self._call(['network', 'ls', '--quiet', '--no-trunc', '--filter', 'id=' + self.network['id']], max_output=4096)
                if remaining.strip():
                    fail('network-cleanup-failed')
                self.network = None
            except (containers.EngineFailure, contracts.release.ReleaseFailure, KeyboardInterrupt):
                failed = True
        if failed or self._owned:
            fail('cleanup-failed')
