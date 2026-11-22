#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.package-custody-receipt
#   version: 3
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove receipt validation accepts safe evidence and rejects mismatched or unsafe evidence.
#   portability: { class: internal, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh
#   created_on: "2026-10-20"
#   updated_on: "2026-11-22"
ROOT="$(git rev-parse --show-toplevel)"; SCRIPT="$ROOT/scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
TEMP="$(mktemp -d)"; trap 'rm -rf "$TEMP"' EXIT
python3 - "$TEMP/safe.json" <<'PY'
import json,sys
json.dump({"schema":"deploy/package-custody-receipt/v1","target":"example-target","environment_class":"private-bootstrap","provider_region_alias":"aws-eu-west-1","candidate_id":"example-candidate","package_contract_id":"example-image","program_id":"example-server","source_revision":"a"*40,"image_digest":"sha256:"+"b"*64,"release_identity":"source-a","checked_at":"2026-10-20T12:00:00Z","checks":{"runnable_program_contract":"passed","dependency_boundary":"passed","delivery_access_static":"passed","delivery_access_live":"passed","local_image_smoke":"passed","ecr_scan":"passed","sbom":"passed","provenance_attestation":"passed"},"verdict":"qualified","receipt_reference":"github-actions-run:12345"},open(sys.argv[1],"w"),sort_keys=True)
PY
ARGS=(--expected-target example-target --expected-candidate example-candidate --expected-package-contract example-image --expected-program example-server --json)
bash "$SCRIPT" --receipt "$TEMP/safe.json" "${ARGS[@]}" >/dev/null
python3 - "$TEMP/safe.json" "$TEMP/qualified.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); v.update(schema="deploy/package-custody-receipt/v2",local_qualification={"schema":"deploy/local-qualification/v1","target":"example-target","scope":"example-scope","source_revision":"a"*40,"checks":{"example-proof":{"input_digest":"c"*64,"evidence_key":"d"*64}}});json.dump(v,open(sys.argv[2],"w"),sort_keys=True)
PY
bash "$SCRIPT" --receipt "$TEMP/qualified.json" "${ARGS[@]}" >/dev/null
python3 - "$TEMP/qualified.json" "$TEMP/qualified-invalid.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]));v["local_qualification"]["source_revision"]="b"*40;json.dump(v,open(sys.argv[2],"w"),sort_keys=True)
PY
if bash "$SCRIPT" --receipt "$TEMP/qualified-invalid.json" "${ARGS[@]}" >/dev/null; then echo 'ERROR: mismatched local qualification passed' >&2; exit 1; fi
python3 - "$TEMP/safe.json" "$TEMP/portable-scan.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); v["checks"].pop("ecr_scan"); v["checks"]["vulnerability_scan"]="passed"; json.dump(v,open(sys.argv[2],"w"))
PY
bash "$SCRIPT" --receipt "$TEMP/portable-scan.json" "${ARGS[@]}" >/dev/null
python3 - "$TEMP/safe.json" "$TEMP/local-qualification.json" "$TEMP/extended.json" <<'PY'
import json,sys
safe=json.load(open(sys.argv[1]))
proof={"schema":"deploy/local-qualification/v1","target":"example-target","scope":"entity-smoke","source_revision":safe["source_revision"],"checks":{name:{"input_digest":str(index)*64,"evidence_key":str(index+3)*64} for index,name in enumerate(["entity-smoke-infrastructure-route","entity-smoke-composition-suite","secret-dependency-declaration-regression"],1)}}
json.dump(proof,open(sys.argv[2],"w"),sort_keys=True)
safe.update(schema="deploy/package-custody-receipt/v2",local_qualification=proof)
json.dump(safe,open(sys.argv[3],"w"),sort_keys=True)
PY
bash "$SCRIPT" --receipt "$TEMP/extended.json" "${ARGS[@]}" >/dev/null
python3 - "$TEMP/extended.json" "$TEMP/invalid-extended.json" <<'PY'
import json,sys
value=json.load(open(sys.argv[1]));value["local_qualification"]["source_revision"]="c"*40;json.dump(value,open(sys.argv[2],"w"))
PY
if bash "$SCRIPT" --receipt "$TEMP/invalid-extended.json" "${ARGS[@]}" >/dev/null; then echo 'ERROR: unbound local qualification passed' >&2; exit 1; fi
python3 - "$TEMP/safe.json" "$TEMP/two-scans.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); v["checks"]["vulnerability_scan"]="passed"; json.dump(v,open(sys.argv[2],"w"))
PY
if bash "$SCRIPT" --receipt "$TEMP/two-scans.json" "${ARGS[@]}" >/dev/null; then echo 'ERROR: receipt with two scanner claims passed' >&2; exit 1; fi
python3 - "$TEMP/safe.json" "$TEMP/unsafe.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); v["receipt_reference"]="https://unsafe.example"; json.dump(v,open(sys.argv[2],"w"))
PY
if bash "$SCRIPT" --receipt "$TEMP/unsafe.json" "${ARGS[@]}" >/dev/null; then echo 'ERROR: unsafe receipt passed' >&2; exit 1; fi
echo 'Package-custody receipt tests passed.'

python3 -B "$ROOT/scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification-test.py"

python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/docker/disposable-cleanup-test.py"

python3 -B "$ROOT/scripts/04.deploy/shared/provider-adapters/aws/ecr-scan-test.py"
