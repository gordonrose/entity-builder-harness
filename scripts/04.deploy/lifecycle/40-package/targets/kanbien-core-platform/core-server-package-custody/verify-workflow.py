#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-package-custody.validation
#   version: 3
#   status: active
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Reject an unsafe target-bound package workflow before it can publish an image.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   created_on: "2026-10-20"
#   updated_on: "2026-10-26"
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-package-custody
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/script.sh
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "package-custody-receipt"))
from workflow_guard import job_steps, protected_step, publication_binding, record_command, custody_tail, scan_step
import importlib.util
provider_spec = importlib.util.spec_from_file_location("ecr_publication_contract", Path(__file__).resolve().parents[7] / "scripts/04.deploy/shared/provider-adapters/aws/ecr_publication_contract.py")
provider_contract = importlib.util.module_from_spec(provider_spec)
provider_spec.loader.exec_module(provider_contract)
publication_commands = provider_contract.publication_commands

EXPECTED = ".github/workflows/publish-kanbien-core-platform-core-server.yml"
REQUIRED = ("workflow_dispatch:", "environment: kanbien-core-platform", "id-token: write", "attestations: write", "refs/heads/main", "aws-actions/configure-aws-credentials@v4", "aws-actions/amazon-ecr-login@v2", "actions/attest@v4", "actions/upload-artifact@v4", "package-custody-receipt/script.sh", "core-server-package-custody/validate-delivery-access/script.sh", "targets/kanbien-core-platform/verify-delivery-role-access/script.sh", "bootstrap-runtime/release-contract/script.sh")
FORBIDDEN = ("aws cloudformation", "aws ecs", "aws lambda", "aws apprunner", "aws elasticbeanstalk", "aws route53", "terraform apply")

def qualification_route_valid(text):
 try:
  steps = job_steps(text, "publish-core-server")
  commands = [['bash', 'scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh', '--contract', 'infra/04.deploy/03.product/entrypoints/runnable-program-index.yml', '--json'], ['bash', 'scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/script.sh', '--json'], ['bash', 'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/script.sh', '--json'], ['bash', 'scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/validate-delivery-access/script.sh', '--json'], ['bash', 'scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/release-contract/script.sh', '--json'], ['bash', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh', '--tag', 'kanbien-core-server:publication']]
  commands.append(record_command("kanbien-core-server:publication", ['infra/04.deploy/03.product/image/core-server/image-contract.yml', 'scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-image/script.sh'], [('scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py', 'infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml', '*')]))
  index, _ = protected_step(steps, "Qualify the declared core-server candidate", commands)
  publication_binding(steps, index, "kanbien-core-server:publication", ("aws-actions/",), "$ECR_URI:$tag", publication_commands("kanbien-core-server:publication","core", [("scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecs-runtime-configuration.py", "infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/bootstrap-runtime.yml", "*")]))
  return custody_route_valid(steps,index)
 except (ValueError, TypeError, KeyError, AttributeError): return False

def custody_route_valid(steps, qualification_index):
 published_index,published=protected_step(steps,"Publish immutable image")
 if published.get("id")!="image":raise ValueError("publication-outcome-substituted")
 _,qualification=protected_step(steps,"Qualify the declared core-server candidate")
 access_index,access=protected_step(steps,"Prove fixed delivery read access",[["bash","scripts/04.deploy/lifecycle/00-target-alignment/targets/kanbien-core-platform/verify-delivery-role-access/script.sh"]])
 if qualification.get("id")!="qualification" or access.get("id")!="access" or not qualification_index < access_index < published_index:raise ValueError("qualification-access-outcome-invalid")
 scan_index=scan_step(steps,["python3","scripts/04.deploy/shared/provider-adapters/aws/ecr-scan.py","--repository","$ECR_REPOSITORY","--image-digest","${{ steps.image.outputs.digest }}","--report","$RUNNER_TEMP/ecr-scan.json"],"Require clean ECR scan")
 if scan_index<=published_index:raise ValueError("scan-precedes-publication")
 return custody_tail(steps,published_index=scan_index,target="kanbien-core-platform",environment="private-bootstrap",region="aws-eu-west-1",candidate="kanbien-core-server-candidate",contract="kanbien-core-server-image",program="kanbien-core-server",stem="core-server",artifact_name="kanbien-core-platform-package-custody-${{ github.run_id }}",qualification_outcome="${{ steps.qualification.outcome }}",scan_outcome="${{ steps.scan.outcome }}",scan_check="ecr_scan",provenance_name="Attest image provenance",attestation_name="Attest image SBOM",capture_name="Write and validate safe package-custody receipt",upload_name="Upload safe package-custody evidence",receipt_filename="package-custody-receipt.json",extra_artifacts=["${{ runner.temp }}/qualified-image.json","${{ runner.temp }}/ecr-scan.json"],registry_expression="${{ env.ECR_URI }}")

def main():
 p=argparse.ArgumentParser(add_help=False); p.add_argument("--workflow",default=EXPECTED); p.add_argument("--json",action="store_true"); a,x=p.parse_known_args()
 if x or a.workflow != EXPECTED: codes=("workflow-path-invalid",)
 else:
  try: text=Path(a.workflow).read_text(encoding="utf-8")
  except OSError: text=""; codes=("workflow-missing",)
  else:
   codes=tuple(code for code,ok in (("workflow-qualification-route-invalid",qualification_route_valid(text)),("workflow-requirement-missing",all(value in text for value in REQUIRED)),("workflow-trigger-not-manual",not re.search(r"^\s*(push|pull_request|schedule):",text,re.M)),("workflow-target-mutation-present",not any(value in text.lower() for value in FORBIDDEN))) if not ok)
 result={"schema":"deploy/package-workflow-validation/v1","target":"kanbien-core-platform","verdict":"passed" if not codes else "failed","findings":[{"code":code} for code in codes]}
 print(json.dumps(result,sort_keys=True)); return 0 if not codes else 1
if __name__ == "__main__": sys.exit(main())
