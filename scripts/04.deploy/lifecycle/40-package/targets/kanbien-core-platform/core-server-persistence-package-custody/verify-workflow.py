#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path

EXPECTED = ".github/workflows/publish-kanbien-core-platform-core-server-persistence.yml"
REQUIRED = ("workflow_dispatch:", "environment: kanbien-core-platform", "id-token: write", "attestations: write", "refs/heads/main", "aws-actions/configure-aws-credentials@v4", "aws-actions/amazon-ecr-login@v2", "actions/attest@v4", "actions/upload-artifact@v4", "package-custody-receipt/script.sh", "core-server-persistence-package-custody/validate-delivery-access/script.sh", "targets/kanbien-core-platform/verify-delivery-role-access/script.sh", "smoke-test-core-server-persistence-image/script.sh")
FORBIDDEN = ("aws cloudformation", "aws ecs", "aws lambda", "aws apprunner", "aws elasticbeanstalk", "aws route53", "terraform apply")
def main():
 p=argparse.ArgumentParser(add_help=False); p.add_argument("--workflow",default=EXPECTED); p.add_argument("--json",action="store_true"); a,x=p.parse_known_args()
 if x or a.workflow != EXPECTED: codes=("workflow-path-invalid",)
 else:
  try: text=Path(a.workflow).read_text(encoding="utf-8")
  except OSError: text=""; codes=("workflow-missing",)
  else: codes=tuple(code for code,ok in (("workflow-requirement-missing",all(value in text for value in REQUIRED)),("workflow-trigger-not-manual",not re.search(r"^\s*(push|pull_request|schedule):",text,re.M)),("workflow-target-mutation-present",not any(value in text.lower() for value in FORBIDDEN))) if not ok)
 result={"schema":"deploy/package-workflow-validation/v1","target":"kanbien-core-platform","verdict":"passed" if not codes else "failed","findings":[{"code":code} for code in codes]}
 print(json.dumps(result,sort_keys=True)); return 0 if not codes else 1
if __name__ == "__main__": sys.exit(main())
