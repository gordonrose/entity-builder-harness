#!/usr/bin/env python3
"""Perform one deliberately narrow, redacted protected-route smoke request."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
from urllib import error, parse, request


class ControlledSmokeError(Exception):
    """Represent a safe-to-report controlled-smoke failure."""


SAFE_SYNTHETIC_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SMOKE_ID = "synthetic-read"
EXPECTED_SMOKE_STATUS = 200
TOKEN_TIMEOUT_SECONDS = 10


def parse_arguments() -> argparse.Namespace:
    """Accept only an offline validation mode or the fixed live-smoke inputs."""

    parser = argparse.ArgumentParser(
        description="Validate or run one redacted Kanbien staging protected-route smoke request."
    )
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS or HTTP call.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable for the read-only secret lookup.")
    parser.add_argument(
        "--aws-credential-source",
        choices=("target-profile", "environment"),
        default="target-profile",
        help="Use the declared local AWS profile or the runner's explicitly configured OIDC environment credentials.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=TOKEN_TIMEOUT_SECONDS, help="Bound each live network call to 1-30 seconds.")
    arguments = parser.parse_args()
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    """Load the target policy without falling back to unsafe ad-hoc parsing."""

    try:
        import yaml
    except ImportError as exception:
        raise ControlledSmokeError("PyYAML is required for controlled-smoke policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except OSError as exception:
        raise ControlledSmokeError("the target profile could not be read") from exception
    except yaml.YAMLError as exception:
        raise ControlledSmokeError("the target profile is not valid YAML") from exception
    if not isinstance(document, dict):
        raise ControlledSmokeError("the target profile must be a YAML mapping")
    return document


def mapping(value: Any, name: str) -> dict[str, Any]:
    """Require a named policy mapping rather than permitting missing defaults."""

    if not isinstance(value, dict):
        raise ControlledSmokeError(f"the target profile must declare {name}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, str]:
    """Extract only the fixed, reviewable values needed for this smoke path."""

    cloud = mapping(profile.get("cloud"), "cloud")
    aws = mapping(profile.get("aws"), "aws")
    route53 = mapping(aws.get("route53"), "aws.route53")
    auth = mapping(profile.get("auth"), "auth")
    app_client = mapping(auth.get("app_client"), "auth.app_client")
    token_validation = mapping(auth.get("token_validation"), "auth.token_validation")
    permission_mapping = mapping(auth.get("permission_mapping"), "auth.permission_mapping")
    scope_permissions = mapping(permission_mapping.get("scope_permissions"), "auth.permission_mapping.scope_permissions")
    config = mapping(profile.get("config"), "config")
    secret_refs = mapping(config.get("secret_refs"), "config.secret_refs")
    secret_ref = mapping(secret_refs.get("cognito_machine_client_secret"), "config.secret_refs.cognito_machine_client_secret")
    observability = mapping(profile.get("observability"), "observability")
    synthetic_checks = observability.get("synthetic_checks")

    if not isinstance(synthetic_checks, list) or len(synthetic_checks) != 1:
        raise ControlledSmokeError("the target profile must declare exactly one controlled synthetic check")
    synthetic = mapping(synthetic_checks[0], "observability.synthetic_checks[0]")
    synthetic_request = mapping(synthetic.get("request"), "observability.synthetic_checks[0].request")

    required_values = {
        "cloud.account_id": cloud.get("account_id"),
        "cloud.profile": cloud.get("profile"),
        "cloud.region": cloud.get("region"),
        "aws.route53.hostname": route53.get("hostname"),
        "auth.app_client.id": app_client.get("id"),
        "auth.token_validation.token_url": token_validation.get("token_url"),
        "secret ARN": secret_ref.get("arn"),
    }
    if any(not isinstance(value, str) or not value for value in required_values.values()):
        raise ControlledSmokeError("the target profile is missing a required controlled-smoke value")
    if secret_ref.get("value_format") != "opaque-raw-string":
        raise ControlledSmokeError("this command supports only a declared opaque raw client-secret value")
    if secret_ref.get("delivery") != "controlled-smoke-token-acquisition-only-not-ecs-task-environment":
        raise ControlledSmokeError("the declared secret is not restricted to controlled token acquisition")
    if synthetic.get("id") != "platform-smoke-protected-read":
        raise ControlledSmokeError("the target profile does not declare the approved protected-read synthetic check")
    if synthetic.get("command") != "npm run platform:shell:controlled-smoke":
        raise ControlledSmokeError("the synthetic check must name the governed controlled-smoke command")
    if synthetic_request.get("method") != "GET" or synthetic_request.get("route_pattern") != "/smoke/<safe-synthetic-id>" or synthetic_request.get("expected_http_status") != EXPECTED_SMOKE_STATUS:
        raise ControlledSmokeError("the synthetic check must remain the approved GET /smoke/<safe-synthetic-id> request")
    if synthetic.get("output_policy") != "status-and-safe-latency-only-no-token-secret-or-response-body":
        raise ControlledSmokeError("the synthetic check must retain its redacted output policy")

    matching_scopes = [
        scope
        for scope, permissions in scope_permissions.items()
        if isinstance(scope, str) and isinstance(permissions, list) and permissions == ["platform-smoke.smoke:read"]
    ]
    if len(matching_scopes) != 1:
        raise ControlledSmokeError("the target profile must map exactly one smoke-read scope to the smoke-read permission")

    hostname = route53["hostname"]
    if not hostname.endswith(".kanbien.com") or ":" in hostname or "/" in hostname:
        raise ControlledSmokeError("the controlled-smoke hostname is not an approved HTTPS DNS name")
    token_url = token_validation["token_url"]
    if not token_url.startswith("https://"):
        raise ControlledSmokeError("the controlled-smoke token endpoint must use HTTPS")

    return {
        "account_id": cloud["account_id"],
        "aws_profile": cloud["profile"],
        "region": cloud["region"],
        "hostname": hostname,
        "client_id": app_client["id"],
        "secret_arn": secret_ref["arn"],
        "token_url": token_url,
        "scope": matching_scopes[0],
    }


def aws_credential_arguments(policy: dict[str, str], credential_source: str) -> list[str]:
    """Select one explicit credential source without allowing arbitrary profile injection."""

    arguments = ["--region", policy["region"]]
    if credential_source == "target-profile":
        arguments.extend(["--profile", policy["aws_profile"]])
    return arguments


def run_aws(arguments: list[str], aws_cli: str, credential_source: str) -> str:
    """Run a read-only AWS CLI command while retaining all output locally."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    if credential_source == "environment":
        environment.pop("AWS_PROFILE", None)
    result = subprocess.run(
        [aws_cli, *arguments],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )
    if result.returncode != 0:
        raise ControlledSmokeError("the approved read-only AWS lookup did not complete")
    return result.stdout


def verify_account(policy: dict[str, str], aws_cli: str, credential_source: str) -> None:
    """Fail closed when the selected AWS CLI identity belongs to another account."""

    response = run_aws(
        [
            "sts",
            "get-caller-identity",
            *aws_credential_arguments(policy, credential_source),
            "--output",
            "json",
        ],
        aws_cli,
        credential_source,
    )
    try:
        account = json.loads(response).get("Account")
    except json.JSONDecodeError as exception:
        raise ControlledSmokeError("the AWS account lookup returned an unexpected response") from exception
    if account != policy["account_id"]:
        raise ControlledSmokeError("the selected AWS identity is not the target account")


def load_secret(policy: dict[str, str], aws_cli: str, credential_source: str) -> str:
    """Retrieve the opaque secret without emitting its value or provider error text."""

    secret = run_aws(
        [
            "secretsmanager",
            "get-secret-value",
            "--secret-id",
            policy["secret_arn"],
            *aws_credential_arguments(policy, credential_source),
            "--query",
            "SecretString",
            "--output",
            "text",
        ],
        aws_cli,
        credential_source,
    ).rstrip("\r\n")
    if not secret or secret == "None":
        raise ControlledSmokeError("the controlled client secret is unavailable")
    return secret


def acquire_token(policy: dict[str, str], secret: str, timeout_seconds: int) -> str:
    """Exchange the raw secret for one access token without logging either value."""

    credentials = f"{policy['client_id']}:{secret}".encode("utf-8")
    authorization = base64.b64encode(credentials).decode("ascii")
    payload = parse.urlencode({"grant_type": "client_credentials", "scope": policy["scope"]}).encode("ascii")
    token_request = request.Request(
        policy["token_url"],
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(token_request, timeout=timeout_seconds) as response:
            token_payload = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exception:
        raise ControlledSmokeError("controlled token acquisition failed") from exception
    token = token_payload.get("access_token") if isinstance(token_payload, dict) else None
    if not isinstance(token, str) or not token:
        raise ControlledSmokeError("controlled token acquisition returned no access token")
    return token


def request_protected_route(policy: dict[str, str], token: str, timeout_seconds: int) -> tuple[int, int]:
    """Call one fixed route and return only its HTTP status and rounded latency."""

    if not SAFE_SYNTHETIC_ID.fullmatch(SMOKE_ID):
        raise ControlledSmokeError("the fixed synthetic identifier is unsafe")
    endpoint = f"https://{policy['hostname']}/smoke/{SMOKE_ID}"
    smoke_request = request.Request(
        endpoint,
        method="GET",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    started = time.monotonic()
    try:
        with request.urlopen(smoke_request, timeout=timeout_seconds) as response:
            status = response.status
    except error.HTTPError as exception:
        status = exception.code
    except (error.URLError, TimeoutError) as exception:
        raise ControlledSmokeError("the protected smoke request did not complete") from exception
    elapsed_ms = round((time.monotonic() - started) * 1000)
    return status, elapsed_ms


def emit_safe_result(result: str, status: int | None = None, duration_ms: int | None = None) -> None:
    """Write the only permitted command output: result, status, and safe latency."""

    payload: dict[str, Any] = {"controlled_smoke": result}
    if status is not None:
        payload["http_status"] = status
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate locally or execute exactly one account-checked protected request."""

    arguments = parse_arguments()
    profile_path = Path(arguments.target_profile)
    policy = resolve_policy(load_yaml(profile_path))
    if arguments.validate:
        emit_safe_result("validated")
        return 0

    secret: str | None = None
    token: str | None = None
    try:
        verify_account(policy, arguments.aws_cli, arguments.aws_credential_source)
        secret = load_secret(policy, arguments.aws_cli, arguments.aws_credential_source)
        token = acquire_token(policy, secret, arguments.timeout_seconds)
        status, duration_ms = request_protected_route(policy, token, arguments.timeout_seconds)
    finally:
        secret = None
        token = None

    emit_safe_result("passed" if status == EXPECTED_SMOKE_STATUS else "unexpected-status", status, duration_ms)
    return 0 if status == EXPECTED_SMOKE_STATUS else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControlledSmokeError as exception:
        print(f"controlled-smoke: {exception}", file=sys.stderr)
        raise SystemExit(1)
