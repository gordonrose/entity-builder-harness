#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.smoke-test-core-server-persistence-image
#   version: 3
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the packaged persistence candidate against disposable TLS PostgreSQL with restricted administration and safe downstream-log inspection.
#   portability: { class: internal, targets: [] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.pipeline.kanbien-core-platform.core-server-persistence-package-custody
#     path: .github/workflows/publish-kanbien-core-platform-core-server-persistence.yml

ROOT="$(git rev-parse --show-toplevel)"
TAG="kanbien-core-server-persistence:qualification"
PORT="39455"
if [[ $# -eq 4 && "$1" == "--tag" && "$3" == "--port" ]]; then TAG="$2"; PORT="$4"; elif [[ $# -ne 0 ]]; then echo 'Usage: script.sh [--tag <image> --port <port>]' >&2; exit 2; fi
[[ "$PORT" =~ ^[0-9]+$ ]] || { echo 'ERROR: port-invalid' >&2; exit 2; }
command -v docker >/dev/null && docker info >/dev/null || { echo 'ERROR: Docker is required for persistence image qualification.' >&2; exit 1; }
command -v openssl >/dev/null || { echo 'ERROR: openssl is required for disposable TLS qualification.' >&2; exit 1; }

# Synthetic only. The test neither prints a captured program/log payload nor
# accepts missing server-log inspection. It uses normal PostgreSQL error
# logging: suppressing errors would not qualify this package.
ADMIN_PASSWORD='synthetic-admin-canary-1'
IAM_TOKEN='synthetic-local-iam-token-2'
REJECTED_PASSWORD='synthetic-rejected-admin-canary-3'
OLD_PASSWORD='synthetic-exposed-legacy-canary-4'
fail() { echo "ERROR: $1" >&2; exit 1; }
assert_safe_output() { local value="$1"; for marker in "$ADMIN_PASSWORD" "$IAM_TOKEN" "$REJECTED_PASSWORD" "$OLD_PASSWORD"; do [[ "$value" != *"$marker"* ]] || fail 'credential-canary-appeared-in-application-output'; done; }
assert_database_logs_safe() {
  for marker in "$ADMIN_PASSWORD" "$IAM_TOKEN" "$REJECTED_PASSWORD" "$OLD_PASSWORD"; do
    docker exec "$database" sh -ec 'if find /var/lib/postgresql/data/log -type f -exec grep -F -q -- "$1" {} +; then exit 1; fi' sh "$marker" || fail 'credential-canary-appeared-in-postgresql-server-log'
  done
  docker exec "$database" sh -ec 'if find /var/lib/postgresql/data/log -type f -exec grep -E -q "SCRAM-SHA-256\\$" {} +; then exit 1; fi' || fail 'credential-verifier-appeared-in-postgresql-server-log'
}
expect_code() { local expected="$1"; shift; local output; if ! output="$("$@" 2>&1)"; then assert_safe_output "$output"; local observed; observed="$(grep -oE '"code":"[A-Z0-9_]+' <<<"$output" | tail -1 | tr -d '"' || true)"; printf 'INFO: package-expected-result=%s\n' "$expected" >&2; [[ -z "$observed" ]] || printf 'INFO: package-safe-result=%s\n' "$observed" >&2; fail 'persistence-administration-or-workload-rejected'; fi; assert_safe_output "$output"; grep -F '"code":"'"$expected"'"' <<<"$output" >/dev/null || fail 'persistence-program-safe-result-code-mismatch'; }

suffix="$$"; network="kanbien-persistence-smoke-${suffix}"; database="kanbien-persistence-db-${suffix}"; server="kanbien-persistence-server-${suffix}"; volume="kanbien-persistence-cert-${suffix}"; temporary="$(mktemp -d)"
cleanup() { docker rm -f "$server" "$database" >/dev/null 2>&1 || true; docker network rm "$network" >/dev/null 2>&1 || true; docker volume rm "$volume" >/dev/null 2>&1 || true; rm -rf "$temporary"; }
trap cleanup EXIT
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$temporary/ca.key" -out "$temporary/ca.crt" -subj '/CN=kanbien-persistence-smoke-ca' -days 1 >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -keyout "$temporary/server.key" -out "$temporary/server.csr" -subj '/CN=postgres' >/dev/null 2>&1
printf 'subjectAltName=DNS:postgres\n' > "$temporary/server.ext"
openssl x509 -req -in "$temporary/server.csr" -CA "$temporary/ca.crt" -CAkey "$temporary/ca.key" -CAcreateserial -out "$temporary/server.crt" -days 1 -extfile "$temporary/server.ext" >/dev/null 2>&1
docker network create "$network" >/dev/null; docker volume create "$volume" >/dev/null
docker run --rm --user root -v "$temporary:/source:ro" -v "$volume:/certs" postgres:16-bookworm bash -ec 'cp /source/server.crt /source/server.key /certs/; chown 999:999 /certs/server.crt /certs/server.key; chmod 600 /certs/server.key; chmod 644 /certs/server.crt' >/dev/null
docker run --detach --rm --name "$database" --network "$network" --network-alias postgres -e POSTGRES_DB=kanbienpersistence -e POSTGRES_USER=fixture_root -e POSTGRES_PASSWORD="$ADMIN_PASSWORD" -v "$volume:/certs:ro" postgres:16-bookworm postgres -c ssl=on -c ssl_cert_file=/certs/server.crt -c ssl_key_file=/certs/server.key -c log_destination=stderr -c logging_collector=on -c log_directory=/var/lib/postgresql/data/log -c log_filename=postgresql.log -c log_min_error_statement=error >/dev/null
for attempt in $(seq 1 40); do docker exec -e PGPASSWORD="$ADMIN_PASSWORD" "$database" psql -X -v ON_ERROR_STOP=1 -U fixture_root -d kanbienpersistence -c 'SELECT 1' >/dev/null 2>&1 && break; [[ "$attempt" != 40 ]] || fail 'disposable-postgresql-unavailable'; sleep 1; done
# fixture_root is used only to approximate managed-RDS bootstrap. Every actual
# administration entrypoint invocation below uses core_administrator, a
# CREATEROLE identity with no superuser, createdb, replication or bypass-RLS
# privilege.  It also has only PostgreSQL's predefined pg_signal_backend
# capability: urgent revocation must terminate an already-established
# core_runtime session, but must not require superuser access.  This is a
# narrow local approximation of the governed RDS administration boundary; it
# does not prove RDS managed-role semantics or real IAM token validation.
docker exec -i -e PGPASSWORD="$ADMIN_PASSWORD" "$database" psql -v ON_ERROR_STOP=1 -U fixture_root -d kanbienpersistence <<SQL >/dev/null
CREATE ROLE rds_iam NOLOGIN;
CREATE ROLE core_administrator LOGIN CREATEROLE INHERIT;
CREATE ROLE core_rejected_administrator LOGIN CREATEROLE NOINHERIT;
CREATE ROLE core_schema_migration LOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE core_runtime LOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT CREATE ON DATABASE kanbienpersistence TO core_administrator, core_rejected_administrator;
GRANT pg_signal_backend TO core_administrator;
GRANT rds_iam TO core_administrator WITH ADMIN OPTION, INHERIT FALSE, SET TRUE;
GRANT core_schema_migration TO core_administrator WITH ADMIN OPTION, INHERIT FALSE, SET TRUE;
GRANT core_runtime TO core_administrator WITH ADMIN OPTION, INHERIT FALSE, SET TRUE;
SQL
# `psql` performs this client-side command without embedding a plaintext
# canary in a SQL statement. PostgreSQL receives a verifier only; the server
# log assertion below treats that verifier as sensitive too. These synthetic
# fixture credentials are not part of any application administration path.
set_fixture_credential() { local role="$1" value="$2"; printf '%s\n%s\n' "$value" "$value" | docker exec -i "$database" psql -X -U fixture_root -d kanbienpersistence -c "\\password $role" >/dev/null 2>&1; }
set_fixture_credential core_administrator "$ADMIN_PASSWORD"
set_fixture_credential core_rejected_administrator "$REJECTED_PASSWORD"
set_fixture_credential core_schema_migration "$IAM_TOKEN"
set_fixture_credential core_runtime "$IAM_TOKEN"
common=(--network "$network" -v "$temporary/ca.crt:/app/assets/test-ca.crt:ro" -e NODE_ENV=test -e PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN="$IAM_TOKEN" -e PERSISTENCE_POSTGRES_HOST=postgres -e PERSISTENCE_POSTGRES_PORT=5432 -e PERSISTENCE_POSTGRES_DATABASE=kanbienpersistence -e PERSISTENCE_POSTGRES_SCHEMA=platform -e PERSISTENCE_POSTGRES_IAM_REGION=eu-west-1 -e PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE=arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-ABCDEFGHIJKLMNOP/core_runtime -e PERSISTENCE_POSTGRES_CA_PATH=/app/assets/test-ca.crt)
administration_environment=( -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS={\"username\":\"core_administrator\",\"password\":\"${ADMIN_PASSWORD}\"}" -e PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-administrator -e PERSISTENCE_MIGRATION_DATABASE_USERNAME=core_schema_migration -e PERSISTENCE_RUNTIME_DATABASE_USERNAME=core_runtime )
run_administration() { docker run --rm "${common[@]}" "${administration_environment[@]}" -e "PERSISTENCE_ADMINISTRATION_OPERATION=$1" "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js; }
expect_code PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED run_administration bootstrap-identities
# A rejected live entrypoint path must be inspected too. The restricted
# administrator can connect but has no rds_iam ADMIN OPTION, so PostgreSQL
# rejects the actual GRANT command while normal server error logging remains on.
rejected_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS={\"username\":\"core_rejected_administrator\",\"password\":\"${REJECTED_PASSWORD}\"}" -e PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-rejected-administrator -e PERSISTENCE_MIGRATION_DATABASE_USERNAME=core_schema_migration -e PERSISTENCE_RUNTIME_DATABASE_USERNAME=core_runtime -e PERSISTENCE_ADMINISTRATION_OPERATION=confirm-runtime-iam-access "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1 || true)"
assert_safe_output "$rejected_output"
grep -F '"code":"PERSISTENCE_ADMINISTRATION_ACCESS_DENIED"' <<<"$rejected_output" >/dev/null || fail 'restricted-administration-rejection-not-confirmed'
expect_code PERSISTENCE_RUNTIME_IAM_ACCESS_CONFIRMED run_administration confirm-runtime-iam-access
expect_code PERSISTENCE_MIGRATION_APPLIED docker run --rm "${common[@]}" -e PERSISTENCE_MIGRATION_DATABASE_USERNAME=core_schema_migration "$TAG" artifacts/kanbien-core-server-persistence-migration.main.js
expect_code PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED run_administration grant-runtime-application-access
expect_code PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN run_administration prove-effective-privilege
docker run --detach --rm --name "$server" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e PERSISTENCE_RUNTIME_DATABASE_USERNAME=core_runtime -e PLATFORM_SOURCE_COMMIT_SHA=package-smoke "$TAG" >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; const id = 'core-persistence-package-smoke-0001'; const fact = 'f'.repeat(64);
async function wait(path, predicate) { let error; for (let attempt = 0; attempt < 80; attempt += 1) { try { const response = await fetch(`${base}${path}`); const body = await response.json(); if (predicate(response, body)) return; error = new Error('unexpected-safe-response'); } catch (caught) { error = caught; } await new Promise((resolve) => setTimeout(resolve, 250)); } throw error || new Error('response-timeout'); }
await wait('/livez', (response, body) => response.status === 200 && body.status === 'live'); await wait('/readyz', (response, body) => response.status === 200 && body.status === 'ready');
const created = await fetch(`${base}/internal/persistence-acceptance`, { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({record_id:id, fact_digest:fact}) }); if (created.status !== 201 || (await created.json()).outcome !== 'created') throw new Error('persistence-create-not-confirmed');
const read = await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`); const body = await read.json(); if (read.status !== 200 || body?.record?.id !== id || body?.record?.factDigest !== fact) throw new Error('persistence-read-not-confirmed');
NODE
restore_digest="$(node -e 'process.stdout.write("f".repeat(64))')"
expect_code KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED docker run --rm "${common[@]}" -e PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME=core_runtime -e PERSISTENCE_ACCEPTANCE_RECORD_ID=core-persistence-package-smoke-0001 -e "PERSISTENCE_ACCEPTANCE_FACT_DIGEST=$restore_digest" "$TAG" artifacts/kanbien-core-server-persistence-restore-verifier.main.js
# A synthetic legacy password is rejected on a new connection. It is only a
# local canary; the governed live proof checks the already-exposed target
# credential without putting its value in a report or shell output.
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e LEGACY_PASSWORD="$OLD_PASSWORD" "$TAG" -e 'const {Pool}=require("pg"),fs=require("fs");const p=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.LEGACY_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}});p.query("SELECT 1").then(()=>{process.exitCode=1}).catch((error)=>{if(error.code!=="28P01")process.exitCode=1}).finally(()=>p.end());' || fail 'legacy-password-new-connection-rejection-not-confirmed'
expect_code PERSISTENCE_RUNTIME_IAM_ACCESS_REVOKED run_administration revoke-runtime
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; let last = 'unreachable'; for (let attempt = 0; attempt < 80; attempt += 1) { const [live, ready] = await Promise.all([fetch(`${base}/livez`).catch(() => undefined), fetch(`${base}/readyz`).catch(() => undefined)]); last = `live-${live?.status ?? 'unreachable'}-ready-${ready?.status ?? 'unreachable'}`; if (live?.status === 200 && ready !== undefined && ready.status !== 200) process.exit(0); await new Promise((resolve) => setTimeout(resolve, 250)); } throw new Error(`revoked-server-did-not-remain-live-and-become-unready:${last}`);
NODE
expect_code PERSISTENCE_RUNTIME_IAM_ACCESS_RESTORED run_administration restore-runtime
docker rm -f "$server" >/dev/null
docker run --detach --rm --name "$server" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e PERSISTENCE_RUNTIME_DATABASE_USERNAME=core_runtime -e PLATFORM_SOURCE_COMMIT_SHA=package-smoke-recovered "$TAG" >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; const id = 'core-persistence-package-smoke-0001'; const fact = 'f'.repeat(64); for (let attempt = 0; attempt < 80; attempt += 1) { const response = await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`).catch(() => undefined); const body = response === undefined ? undefined : await response.json().catch(() => undefined); if (response?.status === 200 && body?.record?.factDigest === fact) process.exit(0); await new Promise((resolve) => setTimeout(resolve, 250)); } throw new Error('recovered-server-could-not-read-original-record');
NODE
server_output="$(docker logs "$server" 2>&1 || true)"; assert_safe_output "$server_output"; assert_database_logs_safe
echo 'Core-server persistence image PostgreSQL/TLS/package smoke test passed.'
