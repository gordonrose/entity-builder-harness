#!/usr/bin/env python3
"""Provision the one deliberately separate Cognito client for the persistence smoke write."""

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
READ_SCOPE = {"ScopeName": "smoke.read", "ScopeDescription": "Read platform smoke app"}
WRITE_SCOPE = {"ScopeName": "smoke.write", "ScopeDescription": "Accept bounded platform smoke work item"}


class PersistenceWriteProvisionError(Exception):
    """Represent a safe-to-report failure without retaining AWS detail or secret material."""


def parse_arguments() -> argparse.Namespace:
    """Allow fixed validation or an explicit provision operation, never arbitrary Cognito input."""

    parser = argparse.ArgumentParser(description="Validate or provision the fixed Kanbien staging persistence-write Cognito client.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS call.")
    parser.add_argument("--execute", action="store_true", help="Provision the fixed client after current-chat approval.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable for the fixed target operations.")
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    """Load the reviewed target profile without permissive fallback parsing."""

    try:
        import yaml
    except ImportError as exception:
        raise PersistenceWriteProvisionError("PyYAML is required for persistence-write client policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise PersistenceWriteProvisionError("the target profile could not be read") from exception
    if not isinstance(value, dict):
        raise PersistenceWriteProvisionError("the target profile must be a YAML mapping")
    return value


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require one declared mapping instead of silently accepting absent policy."""

    if not isinstance(value, dict):
        raise PersistenceWriteProvisionError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require an explicit non-empty string before it can become an AWS argument."""

    if not isinstance(value, str) or not value:
        raise PersistenceWriteProvisionError(f"the target profile must declare {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, str]:
    """Extract only the finite, reviewed write-client policy from the target profile."""

    cloud = mapping(profile.get("cloud"), "cloud")
    auth = mapping(profile.get("auth"), "auth")
    user_pool = mapping(auth.get("user_pool"), "auth.user_pool")
    client = mapping(auth.get("persistence_write_test_client"), "auth.persistence_write_test_client")
    resource_server = mapping(client.get("resource_server"), "auth.persistence_write_test_client.resource_server")
    secret = mapping(client.get("secret"), "auth.persistence_write_test_client.secret")
    declared_server = mapping(auth.get("resource_server"), "auth.resource_server")
    permission_mapping = mapping(auth.get("permission_mapping"), "auth.permission_mapping")

    policy = {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "user_pool_id": required_string(user_pool.get("id"), "auth.user_pool.id"),
        "client_name": required_string(client.get("name"), "auth.persistence_write_test_client.name"),
        "resource_server_identifier": required_string(resource_server.get("identifier"), "auth.persistence_write_test_client.resource_server.identifier"),
        "resource_server_name": required_string(resource_server.get("name"), "auth.persistence_write_test_client.resource_server.name"),
        "scope_name": required_string(resource_server.get("scope_name"), "auth.persistence_write_test_client.resource_server.scope_name"),
        "scope": required_string(resource_server.get("scope"), "auth.persistence_write_test_client.resource_server.scope"),
        "secret_name": required_string(secret.get("name"), "auth.persistence_write_test_client.secret.name"),
        "status": required_string(client.get("status"), "auth.persistence_write_test_client.status"),
    }
    expected = {
        "account_id": EXPECTED_ACCOUNT_ID,
        "region": "eu-west-1",
        "client_name": "platform-shell-staging-persistence-write-client",
        "resource_server_identifier": "platform-shell",
        "resource_server_name": "Platform Shell",
        "scope_name": "smoke.write",
        "scope": "platform-shell/smoke.write",
        "secret_name": "kanbien/staging/platform-shell/cognito-persistence-write-client",
    }
    if any(policy[key] != value for key, value in expected.items()):
        raise PersistenceWriteProvisionError("the target profile does not match the reviewed persistence-write client policy")
    if client.get("type") != "confidential" or client.get("grant_type") != "client_credentials":
        raise PersistenceWriteProvisionError("the persistence-write client must remain confidential and client-credentials-only")
    if client.get("access_token_validity_minutes") != 5 or client.get("token_revocation") != "enabled" or client.get("prevent_user_existence_errors") != "enabled":
        raise PersistenceWriteProvisionError("the persistence-write client must retain the reviewed Cognito hardening")
    if resource_server.get("permission_mapping") != "platform-smoke.persistence.work-item:create":
        raise PersistenceWriteProvisionError("the persistence-write scope must map only to the reviewed app permission")
    if secret.get("delivery") != "bounded-persistence-smoke-only-not-ecs-task-environment" or secret.get("value_format") != "opaque-raw-string":
        raise PersistenceWriteProvisionError("the persistence-write secret has an unsafe delivery policy")
    if declared_server != {
        "identifier": "platform-shell",
        "scopes": [
            {"name": "smoke.read", "maps_to_permission": "platform-smoke.smoke:read"},
            {"name": "smoke.write", "maps_to_permission": "platform-smoke.persistence.work-item:create"},
        ],
    }:
        raise PersistenceWriteProvisionError("the target profile must declare only the reviewed platform-shell read and write scopes")
    if permission_mapping.get("scope_permissions") != {
        "platform-shell/smoke.read": ["platform-smoke.smoke:read"],
        "platform-shell/smoke.write": ["platform-smoke.persistence.work-item:create"],
    }:
        raise PersistenceWriteProvisionError("the target profile must map exactly the reviewed read and write scopes")
    if policy["status"] not in {"pending-provisioning", "provisioned-pending-service-deployment", "deployed-pending-write-proof", "write-proof-failed-non-committing-remediation-pending", "write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "write-proof-failed-non-committing-replacement-pre-server-diagnosis-pending", "write-proof-failed-non-committing-admission-probe-source-ready-deployment-pending", "write-proof-failed-non-committing-admission-probe-deployed-pending-execution", "write-proof-failed-non-committing-admission-probe-passed-fresh-acceptance-pending", "deployed-and-write-proven"}:
        raise PersistenceWriteProvisionError("the persistence-write client is not in a governed lifecycle state")
    if policy["status"] == "pending-provisioning":
        if "client_id" in client or "secret_arn" in client:
            raise PersistenceWriteProvisionError("the pending persistence-write client must not record provisioned references")
    else:
        policy["client_id"] = required_string(client.get("client_id"), "auth.persistence_write_test_client.client_id")
        policy["secret_arn"] = required_string(client.get("secret_arn"), "auth.persistence_write_test_client.secret_arn")
    return policy


def aws_arguments(policy: dict[str, str]) -> list[str]:
    """Use only the profile and region declared by the reviewed target policy."""

    return ["--profile", policy["aws_profile"], "--region", policy["region"]]


def run_aws(aws_cli: str, policy: dict[str, str], arguments: list[str]) -> str:
    """Run one fixed AWS CLI operation while keeping all provider output private."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run([aws_cli, *arguments, *aws_arguments(policy)], check=False, capture_output=True, encoding="utf-8", env=environment)
    if result.returncode != 0:
        raise PersistenceWriteProvisionError("an approved persistence-write client operation did not complete")
    return result.stdout


def run_aws_json(aws_cli: str, policy: dict[str, str], arguments: list[str]) -> dict[str, Any]:
    """Parse a provider response without printing its content or credential material."""

    try:
        value = json.loads(run_aws(aws_cli, policy, [*arguments, "--output", "json"]))
    except json.JSONDecodeError as exception:
        raise PersistenceWriteProvisionError("an approved persistence-write client operation returned an unexpected response") from exception
    if not isinstance(value, dict):
        raise PersistenceWriteProvisionError("an approved persistence-write client operation returned an unexpected response")
    return value


def verify_account(aws_cli: str, policy: dict[str, str]) -> None:
    """Fail closed unless the resolved AWS identity belongs to the reviewed account."""

    if run_aws_json(aws_cli, policy, ["sts", "get-caller-identity"]).get("Account") != policy["account_id"]:
        raise PersistenceWriteProvisionError("the selected AWS identity is not the target account")


def require_expected_starting_state(aws_cli: str, policy: dict[str, str]) -> None:
    """Require exact read-only starting state so execution cannot broaden an existing client or scope."""

    resource_server = run_aws_json(aws_cli, policy, [
        "cognito-idp", "describe-resource-server",
        "--user-pool-id", policy["user_pool_id"],
        "--identifier", policy["resource_server_identifier"],
    ]).get("ResourceServer")
    if not isinstance(resource_server, dict) or resource_server.get("Identifier") != policy["resource_server_identifier"] or resource_server.get("Name") != policy["resource_server_name"] or resource_server.get("Scopes") != [READ_SCOPE]:
        raise PersistenceWriteProvisionError("the existing resource server is not the reviewed read-only starting state")

    clients = run_aws_json(aws_cli, policy, [
        "cognito-idp", "list-user-pool-clients",
        "--user-pool-id", policy["user_pool_id"], "--max-results", "50",
    ]).get("UserPoolClients", [])
    if any(isinstance(value, dict) and value.get("ClientName") == policy["client_name"] for value in clients):
        raise PersistenceWriteProvisionError("the persistence-write client already exists")

    secrets = run_aws_json(aws_cli, policy, [
        "secretsmanager", "list-secrets",
        "--filters", f"Key=name,Values={policy['secret_name']}",
    ]).get("SecretList", [])
    if any(isinstance(value, dict) and value.get("Name") == policy["secret_name"] for value in secrets):
        raise PersistenceWriteProvisionError("the persistence-write client secret already exists")


def rollback_aws(aws_cli: str, policy: dict[str, str], arguments: list[str]) -> None:
    """Attempt rollback only for resources this invocation created or changed."""

    try:
        run_aws(aws_cli, policy, arguments)
    except PersistenceWriteProvisionError:
        pass


def create_resources(aws_cli: str, policy: dict[str, str]) -> tuple[str, str]:
    """Add one scope and one client atomically enough to avoid leaving broadened partial authority."""

    scope_added = False
    client_id: str | None = None
    secret_created = False
    temporary_secret_path: str | None = None
    try:
        run_aws_json(aws_cli, policy, [
            "cognito-idp", "update-resource-server",
            "--user-pool-id", policy["user_pool_id"],
            "--identifier", policy["resource_server_identifier"],
            "--name", policy["resource_server_name"],
            "--scopes",
            "ScopeName=smoke.read,ScopeDescription=Read platform smoke app",
            "ScopeName=smoke.write,ScopeDescription=Accept bounded platform smoke work item",
        ])
        scope_added = True
        client = run_aws_json(aws_cli, policy, [
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
        ])
        client_record = client.get("UserPoolClient")
        if not isinstance(client_record, dict) or not isinstance(client_record.get("ClientId"), str):
            raise PersistenceWriteProvisionError("Cognito did not return a usable persistence-write client")
        client_id = client_record["ClientId"]
        if not isinstance(client_record.get("ClientSecret"), str):
            raise PersistenceWriteProvisionError("Cognito did not return a usable persistence-write client")
        descriptor, temporary_secret_path = tempfile.mkstemp(prefix="persistence-write-client-secret-", text=True)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(client_record["ClientSecret"])
        secret = run_aws_json(aws_cli, policy, [
            "secretsmanager", "create-secret",
            "--name", policy["secret_name"],
            "--secret-string", f"file://{temporary_secret_path}",
            "--tags",
            "Key=service,Value=platform-shell",
            "Key=environment,Value=staging",
            "Key=purpose,Value=persistence-write-proof",
        ])
        secret_created = True
        secret_arn = secret.get("ARN")
        if not isinstance(secret_arn, str) or not secret_arn:
            raise PersistenceWriteProvisionError("Secrets Manager did not return a usable persistence-write secret reference")
        return client_id, secret_arn
    except Exception as exception:
        if secret_created:
            rollback_aws(aws_cli, policy, ["secretsmanager", "delete-secret", "--secret-id", policy["secret_name"], "--force-delete-without-recovery"])
        if client_id is not None:
            rollback_aws(aws_cli, policy, ["cognito-idp", "delete-user-pool-client", "--user-pool-id", policy["user_pool_id"], "--client-id", client_id])
        if scope_added:
            rollback_aws(aws_cli, policy, [
                "cognito-idp", "update-resource-server",
                "--user-pool-id", policy["user_pool_id"],
                "--identifier", policy["resource_server_identifier"],
                "--name", policy["resource_server_name"],
                "--scopes", "ScopeName=smoke.read,ScopeDescription=Read platform smoke app",
            ])
        if isinstance(exception, PersistenceWriteProvisionError):
            raise
        raise PersistenceWriteProvisionError("the persistence-write client transaction did not complete") from exception
    finally:
        if temporary_secret_path is not None:
            Path(temporary_secret_path).unlink(missing_ok=True)


def emit(result: str, client_id: str | None = None, secret_arn: str | None = None) -> None:
    """Emit only declared safe identifiers, never a client secret or provider response."""

    payload: dict[str, str] = {"persistence_write_client_provision": result}
    if client_id is not None:
        payload["client_id"] = client_id
    if secret_arn is not None:
        payload["secret_arn"] = secret_arn
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate local policy or provision exactly the reviewed scope, client, and secret."""

    arguments = parse_arguments()
    policy = resolve_policy(load_yaml(Path(arguments.target_profile)))
    if arguments.validate:
        emit("validated")
        return 0
    if policy["status"] != "pending-provisioning":
        raise PersistenceWriteProvisionError("the persistence-write client is not pending provisioning")
    verify_account(arguments.aws_cli, policy)
    require_expected_starting_state(arguments.aws_cli, policy)
    client_id, secret_arn = create_resources(arguments.aws_cli, policy)
    emit("created", client_id, secret_arn)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PersistenceWriteProvisionError as exception:
        print(f"persistence-write-client-provision: {exception}", file=sys.stderr)
        raise SystemExit(1)
