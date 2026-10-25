#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.qualify-retained-persistence-rollback-image
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Qualify a retained persistence application image against corrected identities on disposable TLS PostgreSQL without replaying its historical migration.
#   portability: { class: internal, targets: [kanbien-core-platform] }
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.standard.retain-accepted-release-for-restoration
#     path: .agentic/04.deploy/60-run/standards/retain-accepted-release-for-restoration.md

# The support image creates the disposable schema and least-privilege roles.
# The retained image is then the only image used for server/verifier/restore
# execution. This is local compatibility proof; live proof must establish the
# exact retained ECR digest separately.
RETAINED_IMAGE=""; SUPPORT_IMAGE=""; PORT=39471
while [[ $# -gt 0 ]]; do
  case "$1" in
    --retained-image) RETAINED_IMAGE="${2-}"; shift 2 ;;
    --support-image) SUPPORT_IMAGE="${2-}"; shift 2 ;;
    --port) PORT="${2-}"; shift 2 ;;
    *) echo 'Usage: script.sh --retained-image <image> --support-image <image> [--port <port>]' >&2; exit 2 ;;
  esac
done
[[ -n "$RETAINED_IMAGE" && -n "$SUPPORT_IMAGE" && "$PORT" =~ ^[0-9]+$ ]] || { echo 'ERROR: retained-rollback-qualification-arguments-invalid' >&2; exit 2; }
command -v docker >/dev/null && docker info >/dev/null || { echo 'ERROR: Docker is required for retained rollback qualification.' >&2; exit 1; }
command -v openssl >/dev/null || { echo 'ERROR: openssl is required for retained rollback qualification.' >&2; exit 1; }
# A retained application image may predate the bounded administration program.
# The support image must not: it is the sole local/bootstrap authority for
# creating identities and applying/revoking grants. Fail before any disposable
# provider fixture is started so a missing published support artifact is an
# actionable package-custody failure, not a module-resolution traceback.
docker run --rm --entrypoint /nodejs/bin/node "$SUPPORT_IMAGE" -e 'if (!require("node:fs").existsSync("/app/artifacts/kanbien-core-server-persistence-administration.main.js")) process.exit(1)' >/dev/null 2>&1 || { echo 'ERROR: retained-rollback-support-image-administration-artifact-missing' >&2; exit 1; }

suffix="$$"; network="kanbien-retained-rollback-${suffix}"; database="kanbien-retained-rollback-db-${suffix}"; server="kanbien-retained-rollback-server-${suffix}"; volume="kanbien-retained-rollback-cert-${suffix}"; temporary="$(mktemp -d)"
cleanup() { docker rm -f "$server" "$database" >/dev/null 2>&1 || true; docker network rm "$network" >/dev/null 2>&1 || true; docker volume rm "$volume" >/dev/null 2>&1 || true; rm -rf "$temporary"; }
trap cleanup EXIT
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$temporary/ca.key" -out "$temporary/ca.crt" -subj '/CN=kanbien-retained-rollback-ca' -days 1 >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -keyout "$temporary/server.key" -out "$temporary/server.csr" -subj '/CN=postgres' >/dev/null 2>&1
printf 'subjectAltName=DNS:postgres\n' > "$temporary/server.ext"
openssl x509 -req -in "$temporary/server.csr" -CA "$temporary/ca.crt" -CAkey "$temporary/ca.key" -CAcreateserial -out "$temporary/server.crt" -days 1 -extfile "$temporary/server.ext" >/dev/null 2>&1
docker network create "$network" >/dev/null; docker volume create "$volume" >/dev/null
docker run --rm --user root -v "$temporary:/source:ro" -v "$volume:/certs" postgres:16-bookworm bash -ec 'cp /source/server.crt /source/server.key /certs/; chown 999:999 /certs/server.crt /certs/server.key; chmod 600 /certs/server.key; chmod 644 /certs/server.crt' >/dev/null
docker run --detach --rm --name "$database" --network "$network" --network-alias postgres -e POSTGRES_DB=kanbienpersistence -e POSTGRES_USER=core_administrator -e POSTGRES_PASSWORD=administrator-password -v "$volume:/certs:ro" postgres:16-bookworm postgres -c ssl=on -c ssl_cert_file=/certs/server.crt -c ssl_key_file=/certs/server.key >/dev/null
for attempt in $(seq 1 60); do
  if docker exec -e PGPASSWORD=administrator-password "$database" psql -U core_administrator -d kanbienpersistence -Atqc 'SELECT 1' >/dev/null 2>&1; then break; fi
  [[ "$attempt" != 60 ]] || { echo 'ERROR: retained-rollback-disposable-postgresql-unavailable' >&2; exit 1; }; sleep 1
done
administrator='{"username":"core_administrator","password":"administrator-password"}'; migration='{"username":"core_schema_migration","password":"migration-password"}'; runtime='{"username":"core_runtime","password":"runtime-password"}'; administrator_reference='arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-administrator'; migration_reference='arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-migration'; record_id='core-persistence-retained-rollback-compatibility-0001'; fact='retained-rollback-compatibility-fact'; fact_digest="$(printf '%s' "$fact" | sha256sum | cut -d ' ' -f 1)"
common=(--network "$network" -v "$temporary/ca.crt:/app/assets/test-ca.crt:ro" -e PERSISTENCE_POSTGRES_HOST=postgres -e PERSISTENCE_POSTGRES_PORT=5432 -e PERSISTENCE_POSTGRES_DATABASE=kanbienpersistence -e PERSISTENCE_POSTGRES_SCHEMA=platform -e PERSISTENCE_POSTGRES_CA_PATH=/app/assets/test-ca.crt)
# This is disposable setup by the corrected support surface, not a replay of a
# completed target migration. The retained image gets runtime credentials only.
docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" "$SUPPORT_IMAGE" artifacts/kanbien-core-server-persistence-administration.main.js | grep -F 'PERSISTENCE_ADMINISTRATION_IDENTITIES_BOOTSTRAPPED' >/dev/null
docker run --rm "${common[@]}" -e "PERSISTENCE_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_MIGRATION_SECRET_REFERENCE=$migration_reference" "$SUPPORT_IMAGE" artifacts/kanbien-core-server-persistence-migration.main.js | grep -F 'PERSISTENCE_MIGRATION_APPLIED' >/dev/null
docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=grant-runtime-application-access "$SUPPORT_IMAGE" artifacts/kanbien-core-server-persistence-administration.main.js | grep -F 'PERSISTENCE_RUNTIME_APPLICATION_ACCESS_GRANTED' >/dev/null
docker run --detach --rm --name "$server" --network-alias core-server-persistence.kanbien-core-platform.internal --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=8cd872e8b2326db2d8c5e3993ce09400cbd9f06f "$RETAINED_IMAGE" >/dev/null
PERSISTENCE_RECORD_ID="$record_id" PERSISTENCE_FACT="$fact" node - "$PORT" <<'NODE'
;(async()=>{const base=`http://127.0.0.1:${process.argv[2]}`, id=process.env.PERSISTENCE_RECORD_ID, fact=process.env.PERSISTENCE_FACT; const digest=require('node:crypto').createHash('sha256').update(fact).digest('hex');
async function wait(path,status){for(let i=0;i<80;i+=1){const r=await fetch(`${base}${path}`).catch(()=>undefined);if(r?.status===status)return;await new Promise(done=>setTimeout(done,250));}throw new Error(`retained-image-${path}-not-${status}`)}
await wait('/livez',200);await wait('/readyz',200);const created=await fetch(`${base}/internal/persistence-acceptance`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({record_id:id,fact_digest:digest})});if(created.status!==201)throw new Error('retained-image-write-not-confirmed');const read=await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`);if(read.status!==200||(await read.json())?.record?.factDigest!==digest)throw new Error('retained-image-read-not-confirmed');})().catch(error=>{console.error(error);process.exitCode=1});
NODE
docker run --rm --network "$network" -e KANBIEN_PRIVATE_PERSISTENCE_URL=http://core-server-persistence.kanbien-core-platform.internal:3000 -e PERSISTENCE_VERIFIER_MODE=read -e PERSISTENCE_ACCEPTANCE_RECORD_ID="$record_id" -e PERSISTENCE_ACCEPTANCE_FACT="$fact" "$RETAINED_IMAGE" artifacts/kanbien-core-server-persistence-verifier.main.js | grep -F 'KANBIEN_CORE_PERSISTENCE_RECORD_RETRIEVED' >/dev/null
docker run --rm "${common[@]}" -e "PERSISTENCE_RESTORE_RUNTIME_CREDENTIALS=$runtime" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PERSISTENCE_ACCEPTANCE_RECORD_ID="$record_id" -e PERSISTENCE_ACCEPTANCE_FACT_DIGEST="$fact_digest" "$RETAINED_IMAGE" artifacts/kanbien-core-server-persistence-restore-verifier.main.js | grep -F 'KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED' >/dev/null
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e MIGRATION_PASSWORD=migration-password "$SUPPORT_IMAGE" -e 'const{Pool}=require("pg"),fs=require("fs");const p=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_schema_migration",password:process.env.MIGRATION_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}});p.query("CREATE ROLE rollback_migration_must_not_admin LOGIN").then(()=>{throw new Error("unexpected-success")}).catch(e=>{if(e.message==="unexpected-success"||e.code!=="42501")throw e}).finally(()=>p.end());'
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-password "$SUPPORT_IMAGE" -e 'const{Pool}=require("pg"),fs=require("fs");const p=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}});Promise.all(["CREATE TABLE platform.rollback_must_not_create (id text)","INSERT INTO platform.platform_migration_history (migration_id,checksum,tool_version) VALUES (\u0027rollback-must-not-write\u0027,\u00270\u0027,\u0027proof\u0027)","CREATE ROLE rollback_must_not_admin LOGIN"].map(async sql=>{try{await p.query(sql);throw new Error("unexpected-success")}catch(e){if(e.message==="unexpected-success"||e.code!=="42501")throw e}})).catch(()=>process.exitCode=1).finally(()=>p.end());'
runtime_rotated='{"username":"core_runtime","password":"runtime-rotated-password"}'; runtime_recovered='{"username":"core_runtime","password":"runtime-recovered-password"}'
docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime_rotated" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=rotate-runtime "$SUPPORT_IMAGE" artifacts/kanbien-core-server-persistence-administration.main.js | grep -F 'PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED' >/dev/null
docker rm -f "$server" >/dev/null
docker run --detach --rm --name "$server" --network-alias core-server-persistence.kanbien-core-platform.internal --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime_rotated" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=8cd872e8b2326db2d8c5e3993ce09400cbd9f06f "$RETAINED_IMAGE" >/dev/null
PERSISTENCE_RECORD_ID="$record_id" node - "$PORT" <<'NODE'
;(async()=>{const base=`http://127.0.0.1:${process.argv[2]}`,id=process.env.PERSISTENCE_RECORD_ID;for(let i=0;i<80;i+=1){const ready=await fetch(`${base}/readyz`).catch(()=>undefined),read=await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`).catch(()=>undefined);if(ready?.status===200&&read?.status===200)return;await new Promise(done=>setTimeout(done,250));}throw new Error('retained-image-rotated-replacement-not-ready')})().catch(error=>{console.error(error);process.exitCode=1});
NODE
docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime_rotated" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=revoke-runtime "$SUPPORT_IMAGE" artifacts/kanbien-core-server-persistence-administration.main.js | grep -F 'PERSISTENCE_RUNTIME_CREDENTIAL_REVOKED' >/dev/null
node - "$PORT" <<'NODE'
;(async()=>{const base=`http://127.0.0.1:${process.argv[2]}`;for(let i=0;i<80;i+=1){const [live,ready]=await Promise.all([fetch(`${base}/livez`).catch(()=>undefined),fetch(`${base}/readyz`).catch(()=>undefined)]);if(live?.status===200&&ready&&ready.status!==200)return;await new Promise(done=>setTimeout(done,250));}throw new Error('retained-image-revocation-did-not-become-live-unready')})().catch(error=>{console.error(error);process.exitCode=1});
NODE
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-rotated-password "$SUPPORT_IMAGE" -e 'const{Pool}=require("pg"),fs=require("fs");const p=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}});p.query("SELECT 1").then(()=>{throw new Error("unexpected-success")}).catch(e=>{if(e.message==="unexpected-success"||e.code!=="28000")throw e}).finally(()=>p.end());'
docker run --rm "${common[@]}" -e "PERSISTENCE_ADMINISTRATOR_CREDENTIALS=$administrator" -e "PERSISTENCE_ADMINISTRATION_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_ADMINISTRATION_RUNTIME_CREDENTIALS=$runtime_recovered" -e "PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE=$administrator_reference" -e PERSISTENCE_ADMINISTRATION_OPERATION=rotate-runtime "$SUPPORT_IMAGE" artifacts/kanbien-core-server-persistence-administration.main.js | grep -F 'PERSISTENCE_RUNTIME_CREDENTIAL_ROTATED' >/dev/null
docker rm -f "$server" >/dev/null
docker run --detach --rm --name "$server" --network-alias core-server-persistence.kanbien-core-platform.internal --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime_recovered" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=8cd872e8b2326db2d8c5e3993ce09400cbd9f06f "$RETAINED_IMAGE" >/dev/null
PERSISTENCE_RECORD_ID="$record_id" node - "$PORT" <<'NODE'
;(async()=>{const base=`http://127.0.0.1:${process.argv[2]}`,id=process.env.PERSISTENCE_RECORD_ID;for(let i=0;i<80;i+=1){const ready=await fetch(`${base}/readyz`).catch(()=>undefined),read=await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`).catch(()=>undefined);if(ready?.status===200&&read?.status===200)return;await new Promise(done=>setTimeout(done,250));}throw new Error('retained-image-recovery-not-ready')})().catch(error=>{console.error(error);process.exitCode=1});
NODE
echo 'Retained persistence rollback image compatibility qualification passed.'

