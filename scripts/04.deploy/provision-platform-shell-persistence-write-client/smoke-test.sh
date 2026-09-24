#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.provision-platform-shell-persistence-write-client.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally validate the persistence-write Cognito client provisioner without contacting AWS.
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

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/provision-platform-shell-persistence-write-client/script.py").read_text(encoding="utf-8"), "persistence-write-client-provision.py", "exec")'
result="$(bash scripts/04.deploy/provision-platform-shell-persistence-write-client/script.sh --validate)"
if [[ "$result" != '{"persistence_write_client_provision":"validated"}' ]]; then
  echo "ERROR: persistence-write client policy validation did not emit the safe expected result" >&2
  exit 1
fi

fake_root="$(mktemp -d)"
trap 'rm -rf "$fake_root"' EXIT
fake_aws="$fake_root/aws"
pending_profile="$fake_root/pending-provisioning-target-profile.yml"

# Model only the pre-provisioning lifecycle in the fake execution tests.  The
# checked-in staging profile may legitimately record an already-provisioned
# client, which the real command must refuse to create again.
python3 - "$ROOT/infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml" "$pending_profile" <<'PY'
from pathlib import Path
import sys
import yaml

source, destination = (Path(value) for value in sys.argv[1:])
profile = yaml.safe_load(source.read_text(encoding="utf-8"))
client = profile["auth"]["persistence_write_test_client"]
client["status"] = "pending-provisioning"
client.pop("client_id", None)
client.pop("secret_arn", None)
client.pop("provisioning_evidence", None)
profile["config"]["secret_refs"].pop("cognito_persistence_write_client_secret", None)
destination.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
PY
cat >"$fake_aws" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$1 $2" in
  "sts get-caller-identity")
    printf '%s\n' '{"Account":"337159794548"}'
    ;;
  "cognito-idp describe-resource-server")
    printf '%s\n' '{"ResourceServer":{"Identifier":"platform-shell","Name":"Platform Shell","Scopes":[{"ScopeName":"smoke.read","ScopeDescription":"Read platform smoke app"}]}}'
    ;;
  "cognito-idp list-user-pool-clients")
    printf '%s\n' '{"UserPoolClients":[]}'
    ;;
  "secretsmanager list-secrets")
    printf '%s\n' '{"SecretList":[]}'
    ;;
  "cognito-idp update-resource-server")
    printf '%s\n' '{}'
    ;;
  "cognito-idp create-user-pool-client")
    printf '%s\n' '{"UserPoolClient":{"ClientId":"persistence-write-client-id","ClientSecret":"test-secret-never-printed"}}'
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
    printf '%s\n' '{"ARN":"arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-persistence-write-client-test"}'
    ;;
  *)
    exit 64
    ;;
esac
EOF
chmod 700 "$fake_aws"

execution_result="$(bash scripts/04.deploy/provision-platform-shell-persistence-write-client/script.sh --execute --aws-cli "$fake_aws" --target-profile "$pending_profile")"
if [[ "$execution_result" != '{"client_id":"persistence-write-client-id","persistence_write_client_provision":"created","secret_arn":"arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-persistence-write-client-test"}' ]]; then
  echo "ERROR: persistence-write client provisioner did not emit the safe expected result" >&2
  exit 1
fi

rollback_aws="$fake_root/aws-rollback"
cat >"$rollback_aws" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

case "$1 $2" in
  "sts get-caller-identity")
    printf '%s\n' '{"Account":"337159794548"}'
    ;;
  "cognito-idp describe-resource-server")
    printf '%s\n' '{"ResourceServer":{"Identifier":"platform-shell","Name":"Platform Shell","Scopes":[{"ScopeName":"smoke.read","ScopeDescription":"Read platform smoke app"}]}}'
    ;;
  "cognito-idp list-user-pool-clients")
    printf '%s\n' '{"UserPoolClients":[]}'
    ;;
  "secretsmanager list-secrets")
    printf '%s\n' '{"SecretList":[]}'
    ;;
  "cognito-idp update-resource-server")
    printf '%s\n' '{}'
    ;;
  "cognito-idp create-user-pool-client")
    printf '%s\n' '{"UserPoolClient":{"ClientId":"rollback-client-id","ClientSecret":"test-secret-never-printed"}}'
    ;;
  "secretsmanager create-secret")
    printf '%s\n' '{}'
    ;;
  "secretsmanager delete-secret")
    touch "$(dirname "$0")/rollback-secret-deleted"
    printf '%s\n' '{}'
    ;;
  "cognito-idp delete-user-pool-client")
    touch "$(dirname "$0")/rollback-client-deleted"
    printf '%s\n' '{}'
    ;;
  *)
    exit 64
    ;;
esac
EOF
chmod 700 "$rollback_aws"

if bash scripts/04.deploy/provision-platform-shell-persistence-write-client/script.sh --execute --aws-cli "$rollback_aws" --target-profile "$pending_profile" >/dev/null 2>&1; then
  echo "ERROR: persistence-write client provisioner accepted a missing secret ARN" >&2
  exit 1
fi
if [[ ! -f "$fake_root/rollback-secret-deleted" || ! -f "$fake_root/rollback-client-deleted" ]]; then
  echo "ERROR: persistence-write client provisioner did not compensate its partial resources" >&2
  exit 1
fi

echo "Persistence-write client local validation passed."
