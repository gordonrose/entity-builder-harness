#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.provision-platform-shell-negative-authz-client.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally validate the negative authorization test-client provisioning policy without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/provision-platform-shell-negative-authz-client/script.py").read_text(encoding="utf-8"), "negative-authz-client-provision.py", "exec")'
result="$(bash scripts/04.deploy/provision-platform-shell-negative-authz-client/script.sh --validate)"
if [[ "$result" != '{"negative_authz_client_provision":"validated"}' ]]; then
  echo "ERROR: negative authorization client policy validation did not emit the safe expected result" >&2
  exit 1
fi

fake_root="$(mktemp -d)"
trap 'rm -rf "$fake_root"' EXIT
fake_aws="$fake_root/aws"
cat >"$fake_aws" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$1 $2" in
  "sts get-caller-identity")
    printf '%s\n' '{"Account":"337159794548"}'
    ;;
  "cognito-idp list-resource-servers")
    printf '%s\n' '{"ResourceServers":[]}'
    ;;
  "cognito-idp list-user-pool-clients")
    printf '%s\n' '{"UserPoolClients":[]}'
    ;;
  "secretsmanager list-secrets")
    printf '%s\n' '{"SecretList":[]}'
    ;;
  "cognito-idp create-resource-server")
    printf '%s\n' '{}'
    ;;
  "cognito-idp create-user-pool-client")
    printf '%s\n' '{"UserPoolClient":{"ClientId":"negative-client-id","ClientSecret":"test-secret-never-printed"}}'
    ;;
  "secretsmanager create-secret")
    for ((index = 1; index <= $#; index += 1)); do
      if [[ "${!index}" == "--secret-string" ]]; then
        next_index=$((index + 1))
        secret_file="${!next_index#file://}"
        [[ -s "$secret_file" && "$(stat -c '%a' "$secret_file")" == "600" ]]
        break
      fi
    done
    printf '%s\n' '{"ARN":"arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-negative-authz-client-test"}'
    ;;
  *)
    exit 64
    ;;
esac
EOF
chmod 700 "$fake_aws"

fixture="$fake_root/pending-target-profile.yml"
python3 - "$fixture" <<'PY'
from pathlib import Path
import sys
import yaml

source = Path("infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml")
target = Path(sys.argv[1])
profile = yaml.safe_load(source.read_text(encoding="utf-8"))
negative = profile["auth"]["negative_test_client"]
negative["status"] = "pending-provisioning"
negative.pop("client_id", None)
negative.pop("secret_arn", None)
target.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
PY

execution_result="$(bash scripts/04.deploy/provision-platform-shell-negative-authz-client/script.sh --execute --target-profile "$fixture" --aws-cli "$fake_aws")"
if [[ "$execution_result" != '{"client_id":"negative-client-id","negative_authz_client_provision":"created","secret_arn":"arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-negative-authz-client-test"}' ]]; then
  echo "ERROR: negative authorization client provisioner did not emit the safe expected result" >&2
  exit 1
fi

echo "Negative authorization test-client local validation passed."
