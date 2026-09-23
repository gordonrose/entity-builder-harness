#!/usr/bin/env python3
"""Provision the single, declared staging Cognito client used for a bounded 403 proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
EXPECTED_ACCOUNT_ID = "337159794548"


class NegativeAuthzProvisionError(Exception):
    """Represent a safe-to-report provisioning failure without provider detail."""


def parse_arguments() -> argparse.Namespace:
    """Accept only the fixed target profile and an explicit live-execution mode."""

    parser = argparse.ArgumentParser(
        description="Validate or provision the fixed Kanbien staging negative-authorization Cognito client."
    )
    parser.add_argument("--validate", action="store_true", help="Validate source policy only; make no AWS call.")
    parser.add_argument("--execute", action="store_true", help="Create the declared AWS resources after current-chat approval.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable for the fixed target operations.")
    arguments = parser.parse_args()
    if arguments.validate and arguments.execute:
        parser.error("--validate and --execute cannot be used together")
    if not arguments.validate and not arguments.execute:
        parser.error("--execute is required for a live provisioning operation")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    """Load target policy through PyYAML without permissive fallback parsing."""

    try:
        import yaml
    except ImportError as exception:
        raise NegativeAuthzProvisionError("PyYAML is required for negative authorization client policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise NegativeAuthzProvisionError("the target profile could not be read") from exception
    if not isinstance(value, dict):
        raise NegativeAuthzProvisionError("the target profile must be a YAML mapping")
    return value


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a declared mapping rather than introducing a permissive default."""

    if not isinstance(value, dict):
        raise NegativeAuthzProvisionError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require a non-empty target-owned string before it can become an AWS input."""

    if not isinstance(value, str) or not value:
        raise NegativeAuthzProvisionError(f"the target profile must declare {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, str]:
    """Extract and constrain the one declared negative-test client configuration."""

    cloud = mapping(profile.get("cloud"), "cloud")
    auth = mapping(profile.get("auth"), "auth")
    user_pool = mapping(auth.get("user_pool"), "auth.user_pool")
    negative_client = mapping(auth.get("negative_test_client"), "auth.negative_test_client")
    resource_server = mapping(negative_client.get("resource_server"), "auth.negative_test_client.resource_server")
    secret = mapping(negative_client.get("secret"), "auth.negative_test_client.secret")

    policy = {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "user_pool_id": required_string(user_pool.get("id"), "auth.user_pool.id"),
        "client_name": required_string(negative_client.get("name"), "auth.negative_test_client.name"),
        "resource_server_identifier": required_string(resource_server.get("identifier"), "auth.negative_test_client.resource_server.identifier"),
        "resource_server_name": required_string(resource_server.get("name"), "auth.negative_test_client.resource_server.name"),
        "scope_name": required_string(resource_server.get("scope_name"), "auth.negative_test_client.resource_server.scope_name"),
        "scope": required_string(resource_server.get("scope"), "auth.negative_test_client.resource_server.scope"),
        "secret_name": required_string(secret.get("name"), "auth.negative_test_client.secret.name"),
    }

    expected = {
        "account_id": EXPECTED_ACCOUNT_ID,
        "region": "eu-west-1",
        "client_name": "platform-shell-staging-negative-authz-client",
        "resource_server_identifier": "platform-shell-authz-probe",
        "resource_server_name": "Platform Shell Authorization Negative Probe",
        "scope_name": "deny",
        "scope": "platform-shell-authz-probe/deny",
        "secret_name": "kanbien/staging/platform-shell/cognito-negative-authz-client",
    }
    for key, value in expected.items():
        if policy[key] != value:
            raise NegativeAuthzProvisionError("the target profile does not match the reviewed negative authorization client policy")
    status = negative_client.get("status")
    if status not in {"pending-provisioning", "provisioned-pending-service-deployment", "deployed-pending-403-proof", "deployed-and-403-proven"}:
        raise NegativeAuthzProvisionError("the negative authorization client is not in a governed lifecycle state")
    if status != "pending-provisioning":
        client_id = negative_client.get("client_id")
        secret_arn = negative_client.get("secret_arn")
        if not isinstance(client_id, str) or not client_id:
            raise NegativeAuthzProvisionError("the provisioned negative authorization client must retain its client ID")
        if not isinstance(secret_arn, str) or not secret_arn.startswith("arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-negative-authz-client-"):
            raise NegativeAuthzProvisionError("the provisioned negative authorization client must retain its target-scoped secret ARN")
    if negative_client.get("type") != "confidential" or negative_client.get("grant_type") != "client_credentials":
        raise NegativeAuthzProvisionError("the negative authorization client must remain confidential and client-credentials-only")
    if negative_client.get("access_token_validity_minutes") != 5:
        raise NegativeAuthzProvisionError("the negative authorization client must retain the five-minute access-token lifetime")
    if negative_client.get("token_revocation") != "enabled" or negative_client.get("prevent_user_existence_errors") != "enabled":
        raise NegativeAuthzProvisionError("the negative authorization client must retain its reviewed Cognito hardening")
    if resource_server.get("permission_mapping") != "intentionally-unmapped":
        raise NegativeAuthzProvisionError("the negative authorization scope must remain intentionally unmapped")
    if secret.get("delivery") != "bounded-negative-authz-smoke-only-not-ecs-task-environment" or secret.get("value_format") != "opaque-raw-string":
        raise NegativeAuthzProvisionError("the negative authorization secret has an unsafe delivery policy")
    policy["status"] = status
    return policy


def aws_arguments(policy: dict[str, str]) -> list[str]:
    """Use only the AWS profile and region declared by the reviewed target."""

    return ["--profile", policy["aws_profile"], "--region", policy["region"]]


def run_aws(aws_cli: str, policy: dict[str, str], arguments: list[str]) -> str:
    """Run one fixed AWS command while retaining provider output in process memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run(
        [aws_cli, *arguments, *aws_arguments(policy)],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )
    if result.returncode != 0:
        raise NegativeAuthzProvisionError("an approved AWS operation did not complete")
    return result.stdout


def run_aws_json(aws_cli: str, policy: dict[str, str], arguments: list[str]) -> dict[str, Any]:
    """Parse an AWS response without printing provider payloads or credentials."""

    try:
        value = json.loads(run_aws(aws_cli, policy, [*arguments, "--output", "json"]))
    except json.JSONDecodeError as exception:
        raise NegativeAuthzProvisionError("an approved AWS operation returned an unexpected response") from exception
    if not isinstance(value, dict):
        raise NegativeAuthzProvisionError("an approved AWS operation returned an unexpected response")
    return value


def verify_account(aws_cli: str, policy: dict[str, str]) -> None:
    """Fail closed unless the selected SSO profile resolves to the reviewed account."""

    response = run_aws_json(aws_cli, policy, ["sts", "get-caller-identity"])
    if response.get("Account") != policy["account_id"]:
        raise NegativeAuthzProvisionError("the selected AWS identity is not the target account")


def require_absent(aws_cli: str, policy: dict[str, str]) -> None:
    """Prevent reuse, overwrite, or accidental mutation of any pre-existing identity resource."""

    resource_servers = run_aws_json(
        aws_cli,
        policy,
        ["cognito-idp", "list-resource-servers", "--user-pool-id", policy["user_pool_id"], "--max-results", "50"],
    ).get("ResourceServers", [])
    if any(isinstance(value, dict) and value.get("Identifier") == policy["resource_server_identifier"] for value in resource_servers):
        raise NegativeAuthzProvisionError("the declared negative authorization resource server already exists")

    clients = run_aws_json(
        aws_cli,
        policy,
        ["cognito-idp", "list-user-pool-clients", "--user-pool-id", policy["user_pool_id"], "--max-results", "50"],
    ).get("UserPoolClients", [])
    if any(isinstance(value, dict) and value.get("ClientName") == policy["client_name"] for value in clients):
        raise NegativeAuthzProvisionError("the declared negative authorization client already exists")

    secrets = run_aws_json(
        aws_cli,
        policy,
        ["secretsmanager", "list-secrets", "--filters", f"Key=name,Values={policy['secret_name']}"],
    ).get("SecretList", [])
    if any(isinstance(value, dict) and value.get("Name") == policy["secret_name"] for value in secrets):
        raise NegativeAuthzProvisionError("the declared negative authorization secret already exists")


def create_resources(aws_cli: str, policy: dict[str, str]) -> tuple[str, str]:
    """Create the reviewed resources and return only safe identifiers, rolling back on any failure."""

    resource_server_created = False
    client_id: str | None = None
    secret_created = False
    temporary_secret_path: str | None = None
    try:
        run_aws_json(
            aws_cli,
            policy,
            [
                "cognito-idp", "create-resource-server",
                "--user-pool-id", policy["user_pool_id"],
                "--identifier", policy["resource_server_identifier"],
                "--name", policy["resource_server_name"],
                "--scopes", f"ScopeName={policy['scope_name']},ScopeDescription=Deliberately unmapped negative authorization probe",
            ],
        )
        resource_server_created = True
        client = run_aws_json(
            aws_cli,
            policy,
            [
                "cognito-idp", "create-user-pool-client",
                "--user-pool-id", policy["user_pool_id"],
                "--client-name", policy["client_name"],
                "--generate-secret",
                "--allowed-o-auth-flows-user-pool-client",
                "--allowed-o-auth-flows", "client_credentials",
                "--allowed-o-auth-scopes", policy["scope"],
                "--access-token-validity", "5",
                "--token-validity-units", "AccessToken=minutes",
                "--enable-token-revocation",
                "--prevent-user-existence-errors", "ENABLED",
            ],
        )
        client_record = client.get("UserPoolClient")
        if not isinstance(client_record, dict) or not isinstance(client_record.get("ClientId"), str) or not isinstance(client_record.get("ClientSecret"), str):
            raise NegativeAuthzProvisionError("Cognito did not return a usable negative authorization client")
        client_id = client_record["ClientId"]
        descriptor, temporary_secret_path = tempfile.mkstemp(prefix="negative-authz-client-secret-", text=True)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(client_record["ClientSecret"])
        secret = run_aws_json(
            aws_cli,
            policy,
            [
                "secretsmanager", "create-secret",
                "--name", policy["secret_name"],
                "--secret-string", f"file://{temporary_secret_path}",
                "--tags",
                "Key=service,Value=platform-shell",
                "Key=environment,Value=staging",
                "Key=purpose,Value=negative-authz-proof",
            ],
        )
        secret_arn = secret.get("ARN")
        if not isinstance(secret_arn, str) or not secret_arn:
            raise NegativeAuthzProvisionError("Secrets Manager did not return a usable negative authorization secret reference")
        secret_created = True
        return client_id, secret_arn
    except Exception as exception:
        if secret_created:
            rollback_aws(aws_cli, policy, ["secretsmanager", "delete-secret", "--secret-id", policy["secret_name"], "--force-delete-without-recovery"])
        if client_id is not None:
            rollback_aws(aws_cli, policy, ["cognito-idp", "delete-user-pool-client", "--user-pool-id", policy["user_pool_id"], "--client-id", client_id])
        if resource_server_created:
            rollback_aws(aws_cli, policy, ["cognito-idp", "delete-resource-server", "--user-pool-id", policy["user_pool_id"], "--identifier", policy["resource_server_identifier"]])
        if isinstance(exception, NegativeAuthzProvisionError):
            raise
        raise NegativeAuthzProvisionError("the negative authorization client transaction did not complete") from exception
    finally:
        if temporary_secret_path is not None:
            Path(temporary_secret_path).unlink(missing_ok=True)


def rollback_aws(aws_cli: str, policy: dict[str, str], arguments: list[str]) -> None:
    """Best-effort rollback only resources created by the current failed transaction."""

    try:
        run_aws(aws_cli, policy, arguments)
    except NegativeAuthzProvisionError:
        pass


def emit(result: str, client_id: str | None = None, secret_arn: str | None = None) -> None:
    """Emit only the declared safe result facts, never an access token or secret value."""

    payload: dict[str, str] = {"negative_authz_client_provision": result}
    if client_id is not None:
        payload["client_id"] = client_id
    if secret_arn is not None:
        payload["secret_arn"] = secret_arn
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate policy or create exactly the one reviewed client, scope, and secret."""

    arguments = parse_arguments()
    policy = resolve_policy(load_yaml(Path(arguments.target_profile)))
    if arguments.validate:
        emit("validated")
        return 0
    if policy["status"] != "pending-provisioning":
        raise NegativeAuthzProvisionError("the negative authorization client is not pending provisioning")
    verify_account(arguments.aws_cli, policy)
    require_absent(arguments.aws_cli, policy)
    client_id, secret_arn = create_resources(arguments.aws_cli, policy)
    emit("created", client_id, secret_arn)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NegativeAuthzProvisionError as exception:
        print(f"negative-authz-client-provision: {exception}", file=sys.stderr)
        raise SystemExit(1)
