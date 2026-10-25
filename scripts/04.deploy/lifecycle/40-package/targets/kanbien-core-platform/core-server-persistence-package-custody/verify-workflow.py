#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys,shlex
import yaml
from pathlib import Path

EXPECTED = ".github/workflows/publish-kanbien-core-platform-core-server-persistence.yml"
REQUIRED = ("workflow_dispatch:", "environment: kanbien-core-platform", "id-token: write", "attestations: write", "refs/heads/main", "aws-actions/configure-aws-credentials@v4", "aws-actions/amazon-ecr-login@v2", "actions/attest@v4", "actions/upload-artifact@v4", "package-custody-receipt/script.sh", "core-server-persistence-package-custody/validate-delivery-access/script.sh", "targets/kanbien-core-platform/verify-delivery-role-access/script.sh", "smoke-test-core-server-persistence-image/script.sh")
FORBIDDEN = ("aws cloudformation", "aws ecs", "aws lambda", "aws apprunner", "aws elasticbeanstalk", "aws route53", "terraform apply")

BUILD = "scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh"
SMOKE = "scripts/04.deploy/lifecycle/40-package/smoke-test-core-server-persistence-image/script.sh"
QUALIFICATION = [
 ["bash", "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/script.sh", "--json"],
 ["bash", "scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/validate-delivery-access/script.sh", "--json"],
 ["bash", BUILD, "--tag", "kanbien-core-server-persistence:qualification"],
 ["bash", SMOKE, "--tag", "kanbien-core-server-persistence:qualification", "--port", "39455"],
]


# This provider-owned builder is deliberately a bounded shell contract. Require
# its executable preamble verbatim (comments/blank lines remain editorial), so
# a shell condition/function or failure suppression cannot hide a required gate.
BUILDER_PREAMBLE = r'''set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
TAG="entity-builder-harness/04.deploy/kanbien-core-server-persistence:local"
if [[ $# -eq 2 && "$1" == "--tag" && -n "$2" ]]; then TAG="$2"; elif [[ $# -ne 0 ]]; then printf '%s\n' 'Usage: script.sh [--tag <tag>]' >&2; exit 2; fi
bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/declaration-contract.yml --json
bash scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh --target-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes --json
bash scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.sh --contract infra/04.deploy/03.product/entrypoints/runnable-program-index.yml --json >/dev/null
bash scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh'''.splitlines()
DOCKER_BOUNDARY = "if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then printf '%s\\n' 'ERROR: Docker is required to qualify the persistence candidate image.' >&2; exit 1; fi"

def qualification_route_valid(text):
 """The fixed publication owner delegates nested checks once, before credentials."""
 try:
  workflow=yaml.safe_load(text)
  job=workflow["jobs"]["qualify-and-publish"]
  # The governed route uses the platform's fail-stop shell and repository cwd.
  # Inherited custom run defaults can silently remove those guarantees.
  if any(owner.get("defaults", {}) != {} for owner in (workflow,job)): return False
  steps=job["steps"]
  selected=[(i,step) for i,step in enumerate(steps) if step.get("name")=="Qualify declarations and actual candidate payload"]
  if len(selected)!=1: return False
  index,step=selected[0]
  if any(key in step for key in ("if","continue-on-error","shell","working-directory")): return False
  commands=[shlex.split(line) for line in step["run"].splitlines() if line.strip() and not line.lstrip().startswith("#")]
  if commands!=QUALIFICATION: return False
  provider_steps=[i for i,item in enumerate(steps) if str(item.get("uses","")).startswith("aws-actions/") or item.get("name")=="Publish immutable image"]
  if not provider_steps or min(provider_steps)<=index: return False
  # These declarations and integration checks belong to the builder and must
  # remain unconditional, before its first Docker availability/build boundary.
  builder=Path(BUILD).read_text(encoding="utf-8")
  executable=[line.strip() for line in builder.splitlines() if line.strip() and not line.lstrip().startswith("#")]
  return executable.count(DOCKER_BOUNDARY)==1 and executable[:executable.index(DOCKER_BOUNDARY)]==BUILDER_PREAMBLE
 except (OSError,UnicodeError,yaml.YAMLError,ValueError,TypeError,KeyError,AttributeError):
  return False

def main():
 p=argparse.ArgumentParser(add_help=False); p.add_argument("--workflow",default=EXPECTED); p.add_argument("--json",action="store_true"); a,x=p.parse_known_args()
 if x or a.workflow != EXPECTED: codes=("workflow-path-invalid",)
 else:
  try: text=Path(a.workflow).read_text(encoding="utf-8")
  except OSError: text=""; codes=("workflow-missing",)
  else: codes=tuple(code for code,ok in (("workflow-requirement-missing",all(value in text for value in REQUIRED)),("workflow-qualification-route-invalid",qualification_route_valid(text)),("workflow-trigger-not-manual",not re.search(r"^\s*(push|pull_request|schedule):",text,re.M)),("workflow-target-mutation-present",not any(value in text.lower() for value in FORBIDDEN))) if not ok)
 result={"schema":"deploy/package-workflow-validation/v1","target":"kanbien-core-platform","verdict":"passed" if not codes else "failed","findings":[{"code":code} for code in codes]}
 print(json.dumps(result,sort_keys=True)); return 0 if not codes else 1
if __name__ == "__main__": sys.exit(main())
