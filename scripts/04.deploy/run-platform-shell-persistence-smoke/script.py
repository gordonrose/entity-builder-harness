#!/usr/bin/env python3
"""Run one fixed, redacted persistence-work acceptance request after deployment."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib import error, parse, request


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
EXPECTED_ACCOUNT_ID = "337159794548"
EXPECTED_STATUS = 202
REQUEST_ID = "persistence-smoke-v1"


class PersistenceSmokeError(Exception):
    """Represent a safe-to-report failure without retaining credential or response data."""


def parse_arguments() -> argparse.Namespace:
    """Permit only offline policy validation or one explicitly selected live proof."""

    parser = argparse.ArgumentParser(description="Validate or run the bounded Kanbien staging persistence smoke.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS or HTTP call.")
    parser.add_argument("--execute", action="store_true", help="Perform the one fixed write after current-chat approval.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable for the declared secret lookup.")
    parser.add_argument("--timeout-seconds", type=int, default=10, help="Bound each live network call to 1-30 seconds.")
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    return arguments


def load_profile(path: Path) -> dict[str, Any]:
    """Read one YAML target profile and reject malformed policy rather than guessing."""

    try:
        import yaml
    except ImportError as exception:
        raise PersistenceSmokeError("PyYAML is required for persistence smoke validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise PersistenceSmokeError("the target profile could not be read") from exception
    if not isinstance(value, dict):
        raise PersistenceSmokeError("the target profile must be a YAML mapping")
    return value


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a named mapping instead of accepting absent policy defaults."""

    if not isinstance(value, dict):
        raise PersistenceSmokeError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require a non-empty string before it is used as a target-owned input."""

    if not isinstance(value, str) or not value:
        raise PersistenceSmokeError(f"the target profile must declare {path}")
    return value


def parse_client_allowlist(value: Any) -> list[str]:
    """Read the exact JSON client allowlist without accepting a wildcard-like shape."""

    try:
        parsed = json.loads(required_string(value, "config.non_secret_env.PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS"))
    except json.JSONDecodeError as exception:
        raise PersistenceSmokeError("the additional Cognito client allowlist must be valid JSON") from exception
    if not isinstance(parsed, list) or any(not isinstance(item, str) or not item for item in parsed):
        raise PersistenceSmokeError("the additional Cognito client allowlist must contain only explicit client IDs")
    return parsed


def resolve_policy(profile: dict[str, Any]) -> dict[str, str]:
    """Extract the finite write-client, route, and lifecycle policy for this proof."""

    cloud = mapping(profile.get("cloud"), "cloud")
    route53 = mapping(mapping(profile.get("aws"), "aws").get("route53"), "aws.route53")
    auth = mapping(profile.get("auth"), "auth")
    negative = mapping(auth.get("negative_test_client"), "auth.negative_test_client")
    write_client = mapping(auth.get("persistence_write_test_client"), "auth.persistence_write_test_client")
    resource_server = mapping(write_client.get("resource_server"), "auth.persistence_write_test_client.resource_server")
    secret = mapping(write_client.get("secret"), "auth.persistence_write_test_client.secret")
    declared_server = mapping(auth.get("resource_server"), "auth.resource_server")
    permissions = mapping(mapping(auth.get("permission_mapping"), "auth.permission_mapping").get("scope_permissions"), "auth.permission_mapping.scope_permissions")
    token_validation = mapping(auth.get("token_validation"), "auth.token_validation")
    config = mapping(profile.get("config"), "config")
    non_secret_env = mapping(config.get("non_secret_env"), "config.non_secret_env")
    secret_refs = mapping(config.get("secret_refs"), "config.secret_refs")

    policy = {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "hostname": required_string(route53.get("hostname"), "aws.route53.hostname"),
        "token_url": required_string(token_validation.get("token_url"), "auth.token_validation.token_url"),
        "status": required_string(write_client.get("status"), "auth.persistence_write_test_client.status"),
    }
    expected = {
        "account_id": EXPECTED_ACCOUNT_ID,
        "region": "eu-west-1",
        "hostname": "staging.platform.kanbien.com",
        "token_url": "https://kanbien-staging-platform-shell-337159794548.auth.eu-west-1.amazoncognito.com/oauth2/token",
    }
    if any(policy[key] != value for key, value in expected.items()):
        raise PersistenceSmokeError("the target profile does not match the reviewed persistence smoke target")
    if not policy["hostname"].endswith(".kanbien.com") or ":" in policy["hostname"] or "/" in policy["hostname"]:
        raise PersistenceSmokeError("the persistence smoke hostname is not an approved HTTPS DNS name")
    if not policy["token_url"].startswith("https://"):
        raise PersistenceSmokeError("the persistence smoke token endpoint must use HTTPS")

    if write_client.get("name") != "platform-shell-staging-persistence-write-client" or write_client.get("type") != "confidential" or write_client.get("grant_type") != "client_credentials":
        raise PersistenceSmokeError("the persistence smoke client must remain the declared confidential machine client")
    if write_client.get("access_token_validity_minutes") != 5 or write_client.get("token_revocation") != "enabled" or write_client.get("prevent_user_existence_errors") != "enabled":
        raise PersistenceSmokeError("the persistence smoke client must retain the reviewed Cognito hardening")
    if resource_server != {
        "identifier": "platform-shell",
        "name": "Platform Shell",
        "scope_name": "smoke.write",
        "scope": "platform-shell/smoke.write",
        "permission_mapping": "platform-smoke.persistence.work-item:create",
    }:
        raise PersistenceSmokeError("the persistence smoke client must retain the reviewed write-only scope")
    if secret != {
        "name": "kanbien/staging/platform-shell/cognito-persistence-write-client",
        "delivery": "bounded-persistence-smoke-only-not-ecs-task-environment",
        "value_format": "opaque-raw-string",
    }:
        raise PersistenceSmokeError("the persistence smoke secret must remain separately bounded")
    if declared_server != {
        "identifier": "platform-shell",
        "scopes": [
            {"name": "smoke.read", "maps_to_permission": "platform-smoke.smoke:read"},
            {"name": "smoke.write", "maps_to_permission": "platform-smoke.persistence.work-item:create"},
        ],
    }:
        raise PersistenceSmokeError("the resource server must retain only the reviewed read and write scope declarations")
    if permissions != {
        "platform-shell/smoke.read": ["platform-smoke.smoke:read"],
        "platform-shell/smoke.write": ["platform-smoke.persistence.work-item:create"],
    }:
        raise PersistenceSmokeError("the scope permissions must retain only the reviewed read and write mappings")

    negative_client_id = required_string(negative.get("client_id"), "auth.negative_test_client.client_id")
    allowlist = parse_client_allowlist(non_secret_env.get("PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS"))
    allowed_statuses = {
        "pending-provisioning",
        "provisioned-pending-service-deployment",
        "deployed-pending-write-proof",
        "write-proof-failed-non-committing-remediation-pending",
        "write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending",
        "deployed-and-write-proven",
    }
    if policy["status"] not in allowed_statuses:
        raise PersistenceSmokeError("the persistence smoke client is not in a governed lifecycle state")
    if policy["status"] == "pending-provisioning":
        if "client_id" in write_client or "secret_arn" in write_client:
            raise PersistenceSmokeError("the pending persistence smoke client must not record provisioned references")
        if allowlist != [negative_client_id] or "cognito_persistence_write_client_secret" in secret_refs:
            raise PersistenceSmokeError("the pending persistence smoke client must not yet be trusted by the public service")
        return policy

    policy["client_id"] = required_string(write_client.get("client_id"), "auth.persistence_write_test_client.client_id")
    policy["secret_arn"] = required_string(write_client.get("secret_arn"), "auth.persistence_write_test_client.secret_arn")
    if not policy["secret_arn"].startswith("arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-persistence-write-client-"):
        raise PersistenceSmokeError("the persistence smoke secret ARN must remain target scoped")
    expected_secret_ref = {
        "name": secret["name"],
        "arn": policy["secret_arn"],
        "delivery": secret["delivery"],
        "value_format": secret["value_format"],
    }
    if secret_refs.get("cognito_persistence_write_client_secret") != expected_secret_ref:
        raise PersistenceSmokeError("the persistence smoke secret reference must remain bounded and target owned")
    expected_allowlist = [negative_client_id]
    if policy["status"] in {"deployed-pending-write-proof", "write-proof-failed-non-committing-remediation-pending", "write-proof-failed-non-committing-remediation-deployed-fresh-approval-pending", "deployed-and-write-proven"}:
        expected_allowlist.append(policy["client_id"])
    if allowlist != expected_allowlist:
        raise PersistenceSmokeError("the service client allowlist does not match the write-client lifecycle boundary")
    return policy


def aws_call(policy: dict[str, str], aws_cli: str, arguments: list[str]) -> str:
    """Perform one fixed AWS lookup without surfacing provider output."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run([aws_cli, *arguments, "--profile", policy["aws_profile"], "--region", policy["region"]], check=False, capture_output=True, encoding="utf-8", env=environment)
    if result.returncode != 0:
        raise PersistenceSmokeError("the approved AWS lookup did not complete")
    return result.stdout


def verify_account(policy: dict[str, str], aws_cli: str) -> None:
    """Fail closed if the selected credentials resolve outside the reviewed account."""

    try:
        response = json.loads(aws_call(policy, aws_cli, ["sts", "get-caller-identity", "--output", "json"]))
    except json.JSONDecodeError as exception:
        raise PersistenceSmokeError("the AWS account lookup returned an unexpected response") from exception
    if not isinstance(response, dict) or response.get("Account") != policy["account_id"]:
        raise PersistenceSmokeError("the selected AWS identity is not the target account")


def load_secret(policy: dict[str, str], aws_cli: str) -> str:
    """Read only the declared raw secret into memory; never print it."""

    secret = aws_call(policy, aws_cli, ["secretsmanager", "get-secret-value", "--secret-id", policy["secret_arn"], "--query", "SecretString", "--output", "text"]).rstrip("\r\n")
    if not secret or secret == "None":
        raise PersistenceSmokeError("the declared persistence smoke client secret is unavailable")
    return secret


def acquire_token(policy: dict[str, str], secret: str, timeout_seconds: int) -> str:
    """Exchange only the declared write-client secret for an in-memory scoped token."""

    basic = base64.b64encode(f"{policy['client_id']}:{secret}".encode("utf-8")).decode("ascii")
    body = parse.urlencode({"grant_type": "client_credentials", "scope": "platform-shell/smoke.write"}).encode("ascii")
    token_request = request.Request(policy["token_url"], data=body, method="POST", headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        with request.urlopen(token_request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exception:
        raise PersistenceSmokeError("persistence smoke token acquisition failed") from exception
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise PersistenceSmokeError("persistence smoke token acquisition returned no access token")
    return token


def request_acceptance(policy: dict[str, str], token: str, timeout_seconds: int) -> tuple[int, int]:
    """Call exactly one fixed no-body acceptance route and retain only safe result facts."""

    acceptance_request = request.Request(
        f"https://{policy['hostname']}/smoke/work-items",
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "X-Request-Id": REQUEST_ID},
    )
    started = time.monotonic()
    try:
        with request.urlopen(acceptance_request, timeout=timeout_seconds) as response:
            status = response.status
    except error.HTTPError as exception:
        status = exception.code
    except (error.URLError, TimeoutError) as exception:
        raise PersistenceSmokeError("the persistence acceptance request did not complete") from exception
    return status, round((time.monotonic() - started) * 1000)


def emit(result: str, status: int | None = None, duration_ms: int | None = None) -> None:
    """Emit status and latency only; never emit tokens, secrets, request IDs, or bodies."""

    payload: dict[str, Any] = {"persistence_smoke": result}
    if status is not None:
        payload["http_status"] = status
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate source policy or perform the one post-deployment acceptance proof."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile(Path(arguments.target_profile)))
    if arguments.validate:
        emit("validated")
        return 0
    if policy["status"] != "deployed-pending-write-proof":
        raise PersistenceSmokeError("the persistence acceptance proof may run only after its reviewed service deployment")
    secret: str | None = None
    token: str | None = None
    try:
        verify_account(policy, arguments.aws_cli)
        secret = load_secret(policy, arguments.aws_cli)
        token = acquire_token(policy, secret, arguments.timeout_seconds)
        status, duration_ms = request_acceptance(policy, token, arguments.timeout_seconds)
    finally:
        secret = None
        token = None
    emit("passed" if status == EXPECTED_STATUS else "unexpected-status", status, duration_ms)
    return 0 if status == EXPECTED_STATUS else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PersistenceSmokeError as exception:
        print(f"persistence-smoke: {exception}", file=sys.stderr)
        raise SystemExit(1)
