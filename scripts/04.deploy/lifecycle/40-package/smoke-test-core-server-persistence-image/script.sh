#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.smoke-test-core-server-persistence-image
#   version: 1
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-24"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove the packaged persistence candidate against disposable TLS PostgreSQL without using a target credential or provider resource.
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

suffix="$$"; network="kanbien-persistence-smoke-${suffix}"; database="kanbien-persistence-db-${suffix}"; server="kanbien-persistence-server-${suffix}"; volume="kanbien-persistence-cert-${suffix}"; temporary="$(mktemp -d)"
cleanup() { docker rm -f "$server" "$database" >/dev/null 2>&1 || true; docker network rm "$network" >/dev/null 2>&1 || true; docker volume rm "$volume" >/dev/null 2>&1 || true; rm -rf "$temporary"; }
trap cleanup EXIT
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$temporary/ca.key" -out "$temporary/ca.crt" -subj '/CN=kanbien-persistence-smoke-ca' -days 1 >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -keyout "$temporary/server.key" -out "$temporary/server.csr" -subj '/CN=postgres' >/dev/null 2>&1
printf 'subjectAltName=DNS:postgres\n' > "$temporary/server.ext"
openssl x509 -req -in "$temporary/server.csr" -CA "$temporary/ca.crt" -CAkey "$temporary/ca.key" -CAcreateserial -out "$temporary/server.crt" -days 1 -extfile "$temporary/server.ext" >/dev/null 2>&1
docker network create "$network" >/dev/null; docker volume create "$volume" >/dev/null
docker run --rm --user root -v "$temporary:/source:ro" -v "$volume:/certs" postgres:16-bookworm bash -ec 'cp /source/server.crt /source/server.key /certs/; chown 999:999 /certs/server.crt /certs/server.key; chmod 600 /certs/server.key; chmod 644 /certs/server.crt' >/dev/null
docker run --detach --rm --name "$database" --network "$network" --network-alias postgres -e POSTGRES_DB=kanbienpersistence -e POSTGRES_USER=core_administrator -e POSTGRES_PASSWORD=administrator-password -v "$volume:/certs:ro" postgres:16-bookworm postgres -c ssl=on -c ssl_cert_file=/certs/server.crt -c ssl_key_file=/certs/server.key >/dev/null
# The image briefly accepts a connection while creating POSTGRES_DB, then
# restarts into its final server.  Do not start a proof against that transient
# bootstrap server: require the final startup plus a query of the named DB.
for attempt in $(seq 1 60); do
  ready_count="$(docker logs "$database" 2>&1 | grep -F -c 'database system is ready to accept connections' || true)"
  if [[ "$ready_count" -ge 2 ]] && docker exec -e PGPASSWORD=administrator-password "$database" psql -U core_administrator -d kanbienpersistence -Atqc 'SELECT 1' >/dev/null 2>&1; then break; fi
  [[ "$attempt" != 60 ]] || { echo 'ERROR: disposable-postgresql-unavailable' >&2; exit 1; }
  sleep 1
done
administrator='{"username":"core_administrator","password":"administrator-password"}'; migration='{"username":"core_schema_migration","password":"migration-password"}'; runtime='{"username":"core_runtime","password":"runtime-password"}'; administrator_reference='arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-administrator'; migration_reference='arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-migration'
common=(--network "$network" -v "$temporary/ca.crt:/app/assets/test-ca.crt:ro" -e PERSISTENCE_POSTGRES_HOST=postgres -e PERSISTENCE_POSTGRES_PORT=5432 -e PERSISTENCE_POSTGRES_DATABASE=kanbienpersistence -e PERSISTENCE_POSTGRES_SCHEMA=platform -e PERSISTENCE_POSTGRES_CA_PATH=/app/assets/test-ca.crt)
if ! administration_bootstrap_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1)"; then
  printf '%s\n' "$administration_bootstrap_output" >&2
  exit 1
fi
printf '%s\n' "$administration_bootstrap_output" | grep -F '"code":"PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED"' >/dev/null
if ! migration_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_MIGRATION_SECRET_REFERENCE=$migration_reference" "$TAG" artifacts/kanbien-core-server-persistence-migration.main.js 2>&1)"; then
  # The migration entrypoint intentionally emits a stable, secret-safe
  # verdict. Preserve that verdict for package diagnosis rather than hiding
  # it behind the shell's generic non-zero exit status.
  printf '%s\n' "$migration_output" >&2
  exit 1
fi
printf '%s\n' "$migration_output"
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e MIGRATION_PASSWORD=migration-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_schema_migration",password:process.env.MIGRATION_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); pool.query("CREATE ROLE migration_must_not_admin LOGIN").then(()=>{process.exitCode=1}).catch((error)=>{if(error.code!=="42501")process.exitCode=1}).finally(()=>pool.end());'
# A later structural migration creates this synthetic relation.  The runtime
# role must not inherit access merely because it is in the application schema.
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e MIGRATION_PASSWORD=migration-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_schema_migration",password:process.env.MIGRATION_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); pool.query("CREATE TABLE platform.future_ungranted_relation (id text PRIMARY KEY)").finally(()=>pool.end());'
if ! administration_grant_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=grant-runtime-application-access "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1)"; then
  printf '%s\n' "$administration_grant_output" >&2
  exit 1
fi
printf '%s\n' "$administration_grant_output" | grep -F '"code":"PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED"' >/dev/null
if ! administration_privilege_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=prove-effective-privilege "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1)"; then
  printf '%s\n' "$administration_privilege_output" >&2
  exit 1
fi
printf '%s\n' "$administration_privilege_output" | grep -F '"code":"PERSISTENCE_RUNTIME_PRIVILEGE_PROVEN"' >/dev/null
docker run --detach --rm --name "$server" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=package-smoke "$TAG" >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; const id = 'core-persistence-package-smoke-0001'; const fact = 'f'.repeat(64);
async function wait(path, predicate) { let error; for (let attempt = 0; attempt < 80; attempt += 1) { try { const response = await fetch(`${base}${path}`); const body = await response.json(); if (predicate(response, body)) return; error = new Error('unexpected-safe-response'); } catch (caught) { error = caught; } await new Promise((resolve) => setTimeout(resolve, 250)); } throw error || new Error('response-timeout'); }
await wait('/livez', (response, body) => response.status === 200 && body.status === 'live'); await wait('/readyz', (response, body) => response.status === 200 && body.status === 'ready');
const created = await fetch(`${base}/internal/persistence-acceptance`, { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({record_id:id, fact_digest:fact}) }); if (created.status !== 201 || (await created.json()).outcome !== 'created') throw new Error('persistence-create-not-confirmed');
const read = await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`); const body = await read.json(); if (read.status !== 200 || body?.record?.id !== id || body?.record?.factDigest !== fact) throw new Error('persistence-read-not-confirmed');
NODE
restore_digest="$(node -e 'process.stdout.write("f".repeat(64))')"
if ! restore_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_RESTORE_RUNTIME_CREDENTIALS=$runtime" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PERSISTENCE_ACCEPTANCE_RECORD_ID=core-persistence-package-smoke-0001 -e "PERSISTENCE_ACCEPTANCE_FACT_DIGEST=$restore_digest" "$TAG" artifacts/kanbien-core-server-persistence-restore-verifier.main.js 2>&1)"; then
  printf '%s\n' "$restore_output" >&2
  exit 1
fi
printf '%s\n' "$restore_output" | grep -F '"code":"KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED"' >/dev/null
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); pool.query("CREATE TABLE platform.runtime_must_not_create (id text)").then(()=>{process.exitCode=1}).catch((error)=>{if(error.code!=="42501")process.exitCode=1}).finally(()=>pool.end());'
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); const denied=async(sql)=>{try{await pool.query(sql);throw new Error("unexpected-success")}catch(error){if(error.message==="unexpected-success"||error.code!=="42501")throw error}};(async()=>{await denied("INSERT INTO platform.platform_migration_history (migration_id,checksum,tool_version) VALUES (\u0027runtime-must-not-write-history\u0027,\u00270\u0027,\u0027probe\u0027)");await denied("SELECT * FROM platform.platform_outbox");await denied("SELECT * FROM platform.future_ungranted_relation");await denied("CREATE ROLE runtime_must_not_admin LOGIN")})().catch(()=>{process.exitCode=1}).finally(()=>pool.end());'
runtime_rotated='{"username":"core_runtime","password":"runtime-rotated-password"}'; runtime_recovered='{"username":"core_runtime","password":"runtime-recovered-password"}'
if ! rotation_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime_rotated" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=rotate-runtime "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1)"; then printf '%s\n' "$rotation_output" >&2; exit 1; fi
printf '%s\n' "$rotation_output" | grep -F '"code":"PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED"' >/dev/null
# The old password must no longer create a new connection after rotation.
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); pool.query("SELECT 1").then(()=>{process.exitCode=1}).catch(()=>{}).finally(()=>pool.end());'
docker rm -f "$server" >/dev/null
docker run --detach --rm --name "$server" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime_rotated" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=package-smoke-rotated "$TAG" >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; for (let attempt = 0; attempt < 80; attempt += 1) { const response = await fetch(`${base}/readyz`).catch(() => undefined); if (response?.status === 200) process.exit(0); await new Promise((resolve) => setTimeout(resolve, 250)); } throw new Error('rotated-server-not-ready');
NODE
if ! revoke_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime_rotated" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=revoke-runtime "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1)"; then printf '%s\n' "$revoke_output" >&2; exit 1; fi
printf '%s\n' "$revoke_output" | grep -F '"code":"PERSISTENCE_RUNTIME_CREDENTIAL_REVOKED"' >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; let last = 'unreachable'; for (let attempt = 0; attempt < 80; attempt += 1) { const [live, ready] = await Promise.all([fetch(`${base}/livez`).catch(() => undefined), fetch(`${base}/readyz`).catch(() => undefined)]); last = `live-${live?.status ?? 'unreachable'}-ready-${ready?.status ?? 'unreachable'}`; if (live?.status === 200 && ready !== undefined && ready.status !== 200) process.exit(0); await new Promise((resolve) => setTimeout(resolve, 250)); } throw new Error(`revoked-server-did-not-remain-live-and-become-unready:${last}`);
NODE
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-rotated-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); pool.query("SELECT 1").then(()=>{process.exitCode=1}).catch(()=>{}).finally(()=>pool.end());'
if ! recovery_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime_recovered" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=rotate-runtime "$TAG" artifacts/kanbien-core-server-persistence-administration.main.js 2>&1)"; then printf '%s\n' "$recovery_output" >&2; exit 1; fi
printf '%s\n' "$recovery_output" | grep -F '"code":"PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED"' >/dev/null
docker rm -f "$server" >/dev/null
docker run --detach --rm --name "$server" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime_recovered" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=package-smoke-recovered "$TAG" >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; const id = 'core-persistence-package-smoke-0001'; const fact = 'f'.repeat(64); for (let attempt = 0; attempt < 80; attempt += 1) { const response = await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`).catch(() => undefined); const body = response === undefined ? undefined : await response.json().catch(() => undefined); if (response?.status === 200 && body?.record?.factDigest === fact) process.exit(0); await new Promise((resolve) => setTimeout(resolve, 250)); } throw new Error('recovered-server-could-not-read-original-record');
NODE
echo 'Core-server persistence image PostgreSQL/TLS/package smoke test passed.'
