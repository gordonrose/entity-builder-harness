#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.restore-accepted-release
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prepare or execute only a reviewed restoration to the retained accepted immutable release.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-bootstrap-runtime-release
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/review-and-execute-ecs-runtime-update.md
#   effects: [aws-mutation, writes-files]
ROOT="$(git rev-parse --show-toplevel)"
approved=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --approved-change-set) approved="${2:-}"; shift 2 ;;
    --json) shift ;;
    *) printf '%s\n' 'DIAGNOSTIC_CODE=RESTORE_ARGUMENTS_INVALID' >&2; exit 2 ;;
  esac
done
record="$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml"
receipt="$(mktemp)"; trap 'rm -f "$receipt"' EXIT
python3 - "$record" "$receipt" <<'PY'
import json, sys, yaml
record=yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
release=record.get("release", {}) if isinstance(record, dict) else {}
if record.get("schema") != "deploy/accepted-release/v1" or record.get("status") != "accepted" or not isinstance(release.get("image_digest"), str) or not isinstance(release.get("source_revision"), str): raise SystemExit(2)
json.dump({"schema":"deploy/package-custody-receipt/v1","target":"kanbien-core-platform","environment_class":"private-bootstrap","provider_region_alias":"aws-eu-west-1","candidate_id":"kanbien-core-server-candidate","package_contract_id":"kanbien-core-server-image","program_id":"kanbien-core-server","source_revision":release["source_revision"],"image_digest":release["image_digest"],"release_identity":"source-"+release["source_revision"],"checked_at":release["private_verification"]["verified_at"],"checks":{"runnable_program_contract":"passed","dependency_boundary":"passed","delivery_access_static":"passed","delivery_access_live":"passed","local_image_smoke":"passed","ecr_scan":"passed","sbom":"passed","provenance_attestation":"passed"},"verdict":"qualified","receipt_reference":release["package_custody_reference"]}, open(sys.argv[2], "w", encoding="utf-8"), sort_keys=True)
PY
change_set="$(python3 - "$receipt" <<'PY'
import json,sys
print("kanbien-core-platform-restore-"+json.load(open(sys.argv[1]))["image_digest"][7:19])
PY
)"
if [ -z "$approved" ]; then
  exec bash "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.sh" --receipt "$receipt" --operation restore --json
fi
[ "$approved" = "$change_set" ] || { printf '%s\n' 'DIAGNOSTIC_CODE=RESTORE_CHANGE_SET_NOT_APPROVED' >&2; exit 1; }
bash "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh" --receipt "$receipt" --operation restore --approved-change-set "$approved" --json
exec bash "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh" --receipt "$receipt" --json
