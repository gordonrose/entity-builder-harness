#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.persistence-proof-applicability
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove restore-only retained-proof applicability fails closed outside its exact package and source boundaries.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.qualify-persistence-proof-applicability
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/qualify-proof-applicability/script.sh
#   effects: [read-only, writes-files]
ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/qualify-proof-applicability/script.py"
python3 -B - "$SCRIPT" <<'PY'
import importlib.util, json, shutil, tempfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("applicability", Path(__import__('sys').argv[1])); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module)
temporary=Path(tempfile.mkdtemp(prefix="persistence-proof-applicability-"))
try:
    module.ROOT=temporary
    module.PACKAGE_RECEIPTS=temporary/"package-receipts"; module.RECORDS=temporary/"records"
    old={"schema":"deploy/package-custody-receipt/v1","target":"kanbien-core-platform","candidate_id":"kanbien-core-server-persistence-candidate","package_contract_id":"kanbien-core-server-persistence-image","program_id":"kanbien-core-server-persistence","verdict":"qualified","source_revision":"a"*40,"image_digest":"sha256:"+"a"*64,"receipt_reference":"github-actions-run:1"}
    new={**old,"source_revision":"b"*40,"image_digest":"sha256:"+"b"*64,"receipt_reference":"github-actions-run:2"}
    old_identity={key:old[key] for key in module.PACKAGE_FIELDS}
    new_identity={key:new[key] for key in module.PACKAGE_FIELDS}
    with patch.object(module,"source_paths",return_value=["infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts"]), patch.object(module,"validate_package_receipt"):
        record=module.make((old_identity,old),(new_identity,new))
        assert module.validate(record,new_identity)==record
    wrong=json.loads(json.dumps(record)); wrong["reused_proofs"].append("isolated-restore"); wrong["integrity"]["payload_sha256"]=module.sha({key:value for key,value in wrong.items() if key!="integrity"})
    with patch.object(module,"source_paths",return_value=["infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.ts"]), patch.object(module,"validate_package_receipt"):
        try: module.validate(wrong,new_identity)
        except module.ApplicabilityError as error: assert str(error)=="persistence-proof-applicability-reused-proof-set-invalid"
        else: raise AssertionError("restore proof reuse passed")
    with patch.object(module,"source_paths",return_value=["infra/04.deploy/03.product/image/core-server-persistence/Dockerfile"]), patch.object(module,"validate_package_receipt"):
        try: module.make(({key:old[key] for key in module.PACKAGE_FIELDS},old),({key:new[key] for key in module.PACKAGE_FIELDS},new))
        except module.ApplicabilityError as error: assert str(error)=="persistence-proof-applicability-change-not-restore-only"
        else: raise AssertionError("Dockerfile change passed")
finally: shutil.rmtree(temporary)
print("persistence proof applicability checks passed")
PY
