#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.smoke-test-core-server-persistence-image
#   version: 1
#   status: draft
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
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
docker run --detach --rm --name "$database" --network "$network" --network-alias postgres -e POSTGRES_DB=kanbienpersistence -e POSTGRES_USER=core_migration -e POSTGRES_PASSWORD=migration-password -v "$volume:/certs:ro" postgres:16-bookworm postgres -c ssl=on -c ssl_cert_file=/certs/server.crt -c ssl_key_file=/certs/server.key >/dev/null
for attempt in $(seq 1 40); do docker exec "$database" pg_isready -U core_migration -d kanbienpersistence >/dev/null 2>&1 && break; [[ "$attempt" != 40 ]] || { echo 'ERROR: disposable-postgresql-unavailable' >&2; exit 1; }; sleep 1; done
migration='{"username":"core_migration","password":"migration-password"}'; runtime='{"username":"core_runtime","password":"runtime-password"}'
common=(--network "$network" -v "$temporary/ca.crt:/app/assets/test-ca.crt:ro" -e PERSISTENCE_POSTGRES_HOST=postgres -e PERSISTENCE_POSTGRES_PORT=5432 -e PERSISTENCE_POSTGRES_DATABASE=kanbienpersistence -e PERSISTENCE_POSTGRES_SCHEMA=platform -e PERSISTENCE_POSTGRES_CA_PATH=/app/assets/test-ca.crt)
if ! migration_output="$(docker run --rm "${common[@]}" -e "PERSISTENCE_MIGRATION_CREDENTIALS=$migration" -e "PERSISTENCE_RUNTIME_BOOTSTRAP_CREDENTIALS=$runtime" -e PERSISTENCE_MIGRATION_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-migration "$TAG" artifacts/kanbien-core-server-persistence-migration.main.js 2>&1)"; then
  # The migration entrypoint intentionally emits a stable, secret-safe
  # verdict. Preserve that verdict for package diagnosis rather than hiding
  # it behind the shell's generic non-zero exit status.
  printf '%s\n' "$migration_output" >&2
  exit 1
fi
printf '%s\n' "$migration_output"
docker run --detach --rm --name "$server" --publish "127.0.0.1:${PORT}:3000" --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,size=16m --cap-drop ALL --security-opt no-new-privileges "${common[@]}" -e "PERSISTENCE_RUNTIME_CREDENTIALS=$runtime" -e PERSISTENCE_RUNTIME_SECRET_REFERENCE=arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-runtime -e PLATFORM_SOURCE_COMMIT_SHA=package-smoke "$TAG" >/dev/null
node - "$PORT" <<'NODE'
const base = `http://127.0.0.1:${process.argv[2]}`; const id = 'core-persistence-package-smoke-0001'; const fact = 'f'.repeat(64);
async function wait(path, predicate) { let error; for (let attempt = 0; attempt < 80; attempt += 1) { try { const response = await fetch(`${base}${path}`); const body = await response.json(); if (predicate(response, body)) return; error = new Error('unexpected-safe-response'); } catch (caught) { error = caught; } await new Promise((resolve) => setTimeout(resolve, 250)); } throw error || new Error('response-timeout'); }
await wait('/livez', (response, body) => response.status === 200 && body.status === 'live'); await wait('/readyz', (response, body) => response.status === 200 && body.status === 'ready');
const created = await fetch(`${base}/internal/persistence-acceptance`, { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({record_id:id, fact_digest:fact}) }); if (created.status !== 201 || (await created.json()).outcome !== 'created') throw new Error('persistence-create-not-confirmed');
const read = await fetch(`${base}/internal/persistence-acceptance?record_id=${id}`); const body = await read.json(); if (read.status !== 200 || body?.record?.id !== id || body?.record?.factDigest !== fact) throw new Error('persistence-read-not-confirmed');
NODE
docker run --rm --entrypoint /nodejs/bin/node "${common[@]}" -e NODE_PATH=/app/artifacts/node_modules -e RUNTIME_PASSWORD=runtime-password "$TAG" -e 'const {Pool}=require("pg"); const fs=require("fs"); const pool=new Pool({host:"postgres",port:5432,database:"kanbienpersistence",user:"core_runtime",password:process.env.RUNTIME_PASSWORD,ssl:{rejectUnauthorized:true,ca:fs.readFileSync("/app/assets/test-ca.crt","utf8"),servername:"postgres"}}); pool.query("CREATE TABLE platform.runtime_must_not_create (id text)").then(()=>{process.exitCode=1}).catch(()=>{}).finally(()=>pool.end());'
echo 'Core-server persistence image PostgreSQL/TLS/package smoke test passed.'
