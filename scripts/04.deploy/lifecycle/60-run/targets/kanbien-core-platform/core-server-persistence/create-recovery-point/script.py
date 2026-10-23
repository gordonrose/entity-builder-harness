#!/usr/bin/env python3
"""Create and reconcile one fixed encrypted recovery point for the candidate."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.create-persistence-recovery-point.impl
#   version: 1
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Create only the declared target recovery-point snapshot after proving the current candidate service is healthy.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.create-persistence-recovery-point
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/create-recovery-point/script.sh
#   effects: [aws-mutation]
from __future__ import annotations
import argparse, importlib.util, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[8]
DATABASE="kanbien-core-platform-persistence"
CLUSTER="kanbien-core-platform"; SERVICE="kanbien-core-platform-core-server-persistence"
PATTERN=re.compile(r"^kanbien-core-platform-persistence-recovery-[0-9]{8}$")
def load():
 p=ROOT/"scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/prepare-candidate/script.py"; s=importlib.util.spec_from_file_location("prepare",p); m=importlib.util.module_from_spec(s); assert s and s.loader; s.loader.exec_module(m); return m
def emit(verdict,*codes,facts=None):
 v={"schema":"deploy/persistence-recovery-point-report/v1","target":"kanbien-core-platform","scope":"core-server-persistence","verdict":verdict,"findings":[{"code":c} for c in codes]};
 if facts:v["facts"]=facts
 print(json.dumps(v,sort_keys=True)); return 0 if verdict=="available" else 1
def main():
 p=argparse.ArgumentParser(add_help=False); p.add_argument("--snapshot-id"); p.add_argument("--json",action="store_true"); a,u=p.parse_known_args()
 if u or not isinstance(a.snapshot_id,str) or not PATTERN.fullmatch(a.snapshot_id): return emit("blocked","persistence-recovery-point-arguments-invalid")
 m=load()
 if not m.live_budget()[0]: return emit("blocked","target-budget-live-configuration-invalid")
 ok,service,code=m.aws("ecs","describe-services","--cluster",CLUSTER,"--services",SERVICE); services=service.get("services",[]) if ok and isinstance(service,dict) else []
 if len(services)!=1 or not isinstance(services[0],dict) or services[0].get("desiredCount")!=1 or services[0].get("runningCount")!=1: return emit("blocked","persistence-recovery-point-service-not-healthy")
 ok,db,code=m.aws("rds","describe-db-instances","--db-instance-identifier",DATABASE); items=db.get("DBInstances",[]) if ok and isinstance(db,dict) else []; instance=items[0] if len(items)==1 else None
 if not isinstance(instance,dict) or instance.get("DBInstanceStatus")!="available" or instance.get("PubliclyAccessible") is not False or instance.get("StorageEncrypted") is not True: return emit("blocked",code if not ok else "persistence-recovery-point-source-not-healthy")
 ok,snapshot,code=m.aws("rds","describe-db-snapshots","--db-snapshot-identifier",a.snapshot_id)
 if not ok:
  if code!="aws-resource-missing": return emit("blocked",code)
  ok,_,code=m.aws("rds","create-db-snapshot","--db-instance-identifier",DATABASE,"--db-snapshot-identifier",a.snapshot_id)
  if not ok:return emit("blocked",code)
 result=subprocess.run(["aws","rds","wait","db-snapshot-available","--db-snapshot-identifier",a.snapshot_id,"--profile",m.PROFILE,"--region",m.REGION],capture_output=True,text=True)
 if result.returncode:return emit("blocked","persistence-recovery-point-not-available")
 ok,snapshot,code=m.aws("rds","describe-db-snapshots","--db-snapshot-identifier",a.snapshot_id); items=snapshot.get("DBSnapshots",[]) if ok and isinstance(snapshot,dict) else []; value=items[0] if len(items)==1 else None
 if not isinstance(value,dict) or value.get("Status")!="available" or value.get("Encrypted") is not True or value.get("DBInstanceIdentifier")!=DATABASE:return emit("blocked","persistence-recovery-point-invalid")
 return emit("available","persistence-recovery-point-created",facts={"snapshot":a.snapshot_id})
if __name__=="__main__":raise SystemExit(main())
