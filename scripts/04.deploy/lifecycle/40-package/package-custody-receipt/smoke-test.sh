#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.package-custody-receipt
#   version: 2
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove receipt validation accepts safe evidence and rejects mismatched or unsafe evidence.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.package-custody-receipt
#     path: scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
ROOT="$(git rev-parse --show-toplevel)"; SCRIPT="$ROOT/scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh"
TEMP="$(mktemp -d)"; trap 'rm -rf "$TEMP"' EXIT
python3 - "$TEMP/safe.json" <<'PY'
import json,sys
json.dump({"schema":"deploy/package-custody-receipt/v1","target":"example-target","environment_class":"private-bootstrap","provider_region_alias":"aws-eu-west-1","candidate_id":"example-candidate","package_contract_id":"example-image","program_id":"example-server","source_revision":"a"*40,"image_digest":"sha256:"+"b"*64,"release_identity":"source-a","checked_at":"2026-10-20T12:00:00Z","checks":{"runnable_program_contract":"passed","dependency_boundary":"passed","delivery_access_static":"passed","delivery_access_live":"passed","local_image_smoke":"passed","ecr_scan":"passed","sbom":"passed","provenance_attestation":"passed"},"verdict":"qualified","receipt_reference":"github-actions-run:12345"},open(sys.argv[1],"w"),sort_keys=True)
PY
ARGS=(--expected-target example-target --expected-candidate example-candidate --expected-package-contract example-image --expected-program example-server --json)
bash "$SCRIPT" --receipt "$TEMP/safe.json" "${ARGS[@]}" >/dev/null
python3 - "$TEMP/safe.json" "$TEMP/unsafe.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1])); v["receipt_reference"]="https://unsafe.example"; json.dump(v,open(sys.argv[2],"w"))
PY
if bash "$SCRIPT" --receipt "$TEMP/unsafe.json" "${ARGS[@]}" >/dev/null; then echo 'ERROR: unsafe receipt passed' >&2; exit 1; fi
echo 'Package-custody receipt tests passed.'
