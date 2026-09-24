#!/usr/bin/env python3
"""Run one bounded staging request that proves authorization denial, not authentication failure."""

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
EXPECTED_STATUS = 403


class NegativeAuthzSmokeError(Exception):
    """Represent a safe-to-report, redacted negative-authorization smoke failure."""


def parse_arguments() -> argparse.Namespace:
    """Permit only fixed offline validation or explicitly approved live execution."""

    parser = argparse.ArgumentParser(description="Validate or run the bounded Kanbien staging authorization-denial smoke.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS or HTTP call.")
    parser.add_argument("--execute", action="store_true", help="Perform the fixed request after current-chat approval.")
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
    """Read a YAML target profile and reject missing or malformed policy."""

    try:
        import yaml
    except ImportError as exception:
        raise NegativeAuthzSmokeError("PyYAML is required for negative authorization smoke validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise NegativeAuthzSmokeError("the target profile could not be read") from exception
    if not isinstance(value, dict):
        raise NegativeAuthzSmokeError("the target profile must be a YAML mapping")
    return value


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require an explicit mapping at one named profile path."""

    if not isinstance(value, dict):
        raise NegativeAuthzSmokeError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require a non-empty string before using a value as an external input."""

    if not isinstance(value, str) or not value:
        raise NegativeAuthzSmokeError(f"the target profile must declare {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, str]:
    """Extract the finite account, client, scope, route, and lifecycle proof policy."""

    cloud = mapping(profile.get("cloud"), "cloud")
    route53 = mapping(mapping(profile.get("aws"), "aws").get("route53"), "aws.route53")
    auth = mapping(profile.get("auth"), "auth")
    negative = mapping(auth.get("negative_test_client"), "auth.negative_test_client")
    persistence_write_client = mapping(auth.get("persistence_write_test_client"), "auth.persistence_write_test_client")
    resource_server = mapping(negative.get("resource_server"), "auth.negative_test_client.resource_server")
    token_validation = mapping(auth.get("token_validation"), "auth.token_validation")
    permissions = mapping(mapping(auth.get("permission_mapping"), "auth.permission_mapping").get("scope_permissions"), "auth.permission_mapping.scope_permissions")
    config = mapping(profile.get("config"), "config")
    non_secret_env = mapping(config.get("non_secret_env"), "config.non_secret_env")
    secret_ref = mapping(mapping(config.get("secret_refs"), "config.secret_refs").get("cognito_negative_authz_client_secret"), "config.secret_refs.cognito_negative_authz_client_secret")
    authorization_403 = mapping(mapping(mapping(profile.get("operations"), "operations").get("readiness_closure"), "operations.readiness_closure").get("authorization_403"), "operations.readiness_closure.authorization_403")

    policy = {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "hostname": required_string(route53.get("hostname"), "aws.route53.hostname"),
        "client_id": required_string(negative.get("client_id"), "auth.negative_test_client.client_id"),
        "secret_arn": required_string(negative.get("secret_arn"), "auth.negative_test_client.secret_arn"),
        "scope": required_string(resource_server.get("scope"), "auth.negative_test_client.resource_server.scope"),
        "token_url": required_string(token_validation.get("token_url"), "auth.token_validation.token_url"),
        "status": required_string(negative.get("status"), "auth.negative_test_client.status"),
    }
    expected = {
        "account_id": EXPECTED_ACCOUNT_ID,
        "region": "eu-west-1",
        "hostname": "staging.platform.kanbien.com",
        "scope": "platform-shell-authz-probe/deny",
        "token_url": "https://kanbien-staging-platform-shell-337159794548.auth.eu-west-1.amazoncognito.com/oauth2/token",
    }
    if any(policy[key] != value for key, value in expected.items()):
        raise NegativeAuthzSmokeError("the target profile does not match the reviewed negative authorization smoke policy")
    if policy["status"] not in {"provisioned-pending-service-deployment", "deployed-pending-403-proof", "deployed-and-403-proven"}:
        raise NegativeAuthzSmokeError("the negative authorization client is not in a governed proof lifecycle state")
    if negative.get("name") != "platform-shell-staging-negative-authz-client" or negative.get("grant_type") != "client_credentials":
        raise NegativeAuthzSmokeError("the negative authorization client must remain the declared machine client")
    if resource_server.get("permission_mapping") != "intentionally-unmapped" or policy["scope"] in permissions:
        raise NegativeAuthzSmokeError("the negative authorization scope must remain intentionally unmapped")
    if secret_ref != {"name": "kanbien/staging/platform-shell/cognito-negative-authz-client", "arn": policy["secret_arn"], "delivery": "bounded-negative-authz-smoke-only-not-ecs-task-environment", "value_format": "opaque-raw-string"}:
        raise NegativeAuthzSmokeError("the negative authorization secret reference must remain bounded and target-owned")
    try:
        additional_client_ids = json.loads(required_string(non_secret_env.get("PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS"), "config.non_secret_env.PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS"))
    except json.JSONDecodeError as exception:
        raise NegativeAuthzSmokeError("the additional Cognito client allowlist must be valid JSON") from exception
    persistence_status = persistence_write_client.get("status")
    if persistence_status not in {
        "pending-provisioning",
        "provisioned-pending-service-deployment",
        "deployed-pending-write-proof",
        "deployed-and-write-proven",
    }:
        raise NegativeAuthzSmokeError("the persistence-write client must remain in a governed lifecycle state")
    expected_client_ids = [policy["client_id"]]
    if persistence_status in {"deployed-pending-write-proof", "deployed-and-write-proven"}:
        expected_client_ids.append(required_string(persistence_write_client.get("client_id"), "auth.persistence_write_test_client.client_id"))
    if additional_client_ids != expected_client_ids:
        raise NegativeAuthzSmokeError("the additional Cognito client allowlist must contain exactly the deployed proof clients")
    if authorization_403.get("proof_command") != "npm run platform:shell:negative-authz-smoke" or authorization_403.get("safe_result") != "status-code-only-403":
        raise NegativeAuthzSmokeError("the readiness policy must retain the bounded negative authorization proof contract")
    return policy


def aws_call(policy: dict[str, str], aws_cli: str, arguments: list[str]) -> str:
    """Perform one profile- and region-scoped AWS call without surfacing provider output."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run([aws_cli, *arguments, "--profile", policy["aws_profile"], "--region", policy["region"]], check=False, capture_output=True, encoding="utf-8", env=environment)
    if result.returncode != 0:
        raise NegativeAuthzSmokeError("the approved AWS lookup did not complete")
    return result.stdout


def verify_account(policy: dict[str, str], aws_cli: str) -> None:
    """Fail closed when the selected profile is not the exact target account."""

    try:
        result = json.loads(aws_call(policy, aws_cli, ["sts", "get-caller-identity", "--output", "json"]))
    except json.JSONDecodeError as exception:
        raise NegativeAuthzSmokeError("the AWS account lookup returned an unexpected response") from exception
    if not isinstance(result, dict) or result.get("Account") != policy["account_id"]:
        raise NegativeAuthzSmokeError("the selected AWS identity is not the target account")


def load_secret(policy: dict[str, str], aws_cli: str) -> str:
    """Read the one named raw secret into process memory without printing it."""

    secret = aws_call(policy, aws_cli, ["secretsmanager", "get-secret-value", "--secret-id", policy["secret_arn"], "--query", "SecretString", "--output", "text"]).rstrip("\r\n")
    if not secret or secret == "None":
        raise NegativeAuthzSmokeError("the declared negative authorization client secret is unavailable")
    return secret


def acquire_token(policy: dict[str, str], secret: str, timeout_seconds: int) -> str:
    """Acquire an in-memory token using only the declared intentionally unmapped scope."""

    basic = base64.b64encode(f"{policy['client_id']}:{secret}".encode("utf-8")).decode("ascii")
    body = parse.urlencode({"grant_type": "client_credentials", "scope": policy["scope"]}).encode("ascii")
    token_request = request.Request(policy["token_url"], data=body, method="POST", headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
    try:
        with request.urlopen(token_request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exception:
        raise NegativeAuthzSmokeError("negative authorization token acquisition failed") from exception
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise NegativeAuthzSmokeError("negative authorization token acquisition returned no access token")
    return token


def request_route(policy: dict[str, str], token: str, timeout_seconds: int) -> tuple[int, int]:
    """Call exactly one fixed staging route and retain only safe result facts."""

    route_request = request.Request(f"https://{policy['hostname']}/smoke/negative-authz", method="GET", headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    started = time.monotonic()
    try:
        with request.urlopen(route_request, timeout=timeout_seconds) as response:
            status = response.status
    except error.HTTPError as exception:
        status = exception.code
    except (error.URLError, TimeoutError) as exception:
        raise NegativeAuthzSmokeError("the negative authorization request did not complete") from exception
    return status, round((time.monotonic() - started) * 1000)


def emit(result: str, status: int | None = None, duration_ms: int | None = None) -> None:
    """Emit only result, HTTP status, and rounded duration; never sensitive material."""

    payload: dict[str, Any] = {"negative_authz_smoke": result}
    if status is not None:
        payload["http_status"] = status
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate locally or perform the one post-deployment authorization denial request."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile(Path(arguments.target_profile)))
    if arguments.validate:
        emit("validated")
        return 0
    if policy["status"] != "deployed-pending-403-proof":
        raise NegativeAuthzSmokeError("the negative authorization proof may run only after the target deployment is recorded")
    secret: str | None = None
    token: str | None = None
    try:
        verify_account(policy, arguments.aws_cli)
        secret = load_secret(policy, arguments.aws_cli)
        token = acquire_token(policy, secret, arguments.timeout_seconds)
        status, duration_ms = request_route(policy, token, arguments.timeout_seconds)
    finally:
        secret = None
        token = None
    emit("passed" if status == EXPECTED_STATUS else "unexpected-status", status, duration_ms)
    return 0 if status == EXPECTED_STATUS else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NegativeAuthzSmokeError as exception:
        print(f"negative-authz-smoke: {exception}", file=sys.stderr)
        raise SystemExit(1)
