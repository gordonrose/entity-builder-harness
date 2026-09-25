#!/usr/bin/env python3
"""Run one fixed, no-body, non-mutating write-admission diagnostic."""

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
EXPECTED_STATUS = 204
SOURCE_READY = "write-proof-failed-non-committing-admission-probe-source-ready-deployment-pending"
DEPLOYED_READY = "write-proof-failed-non-committing-admission-probe-deployed-pending-execution"


class AdmissionProbeError(Exception):
    """Represent a safe-to-report diagnostic failure without retaining credentials."""


def parse_arguments() -> argparse.Namespace:
    """Permit only offline policy validation or the one declared live diagnostic."""

    parser = argparse.ArgumentParser(
        description="Validate or run the bounded Kanbien staging persistence write-admission probe.",
    )
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS or HTTP call.")
    parser.add_argument("--execute", action="store_true", help="Perform the fixed no-body, non-mutating probe.")
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    return arguments


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a mapping at a documented target-profile path."""

    if not isinstance(value, dict):
        raise AdmissionProbeError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require a non-empty string before using target-owned policy input."""

    if not isinstance(value, str) or not value:
        raise AdmissionProbeError(f"the target profile must declare {path}")
    return value


def load_profile() -> dict[str, Any]:
    """Load the one reviewed staging profile; callers cannot select another target."""

    try:
        import yaml
    except ImportError as exception:
        raise AdmissionProbeError("PyYAML is required for admission-probe validation") from exception
    try:
        with Path(DEFAULT_PROFILE).open(encoding="utf-8") as handle:
            profile = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise AdmissionProbeError("the target profile could not be read") from exception
    if not isinstance(profile, dict):
        raise AdmissionProbeError("the target profile must be a YAML mapping")
    return profile


def parse_client_allowlist(value: Any) -> list[str]:
    """Require a finite exact JSON client allowlist, never a wildcard form."""

    try:
        allowlist = json.loads(required_string(value, "config.non_secret_env.PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS"))
    except json.JSONDecodeError as exception:
        raise AdmissionProbeError("the additional Cognito client allowlist must be valid JSON") from exception
    if not isinstance(allowlist, list) or any(not isinstance(client_id, str) or not client_id for client_id in allowlist):
        raise AdmissionProbeError("the additional Cognito client allowlist must contain explicit client IDs")
    return allowlist


def resolve_policy(profile: dict[str, Any]) -> dict[str, str]:
    """Extract and validate the narrow authenticated transport diagnostic policy."""

    cloud = mapping(profile.get("cloud"), "cloud")
    route53 = mapping(mapping(profile.get("aws"), "aws").get("route53"), "aws.route53")
    auth = mapping(profile.get("auth"), "auth")
    write_client = mapping(auth.get("persistence_write_test_client"), "auth.persistence_write_test_client")
    resource_server = mapping(write_client.get("resource_server"), "auth.persistence_write_test_client.resource_server")
    secret = mapping(write_client.get("secret"), "auth.persistence_write_test_client.secret")
    config = mapping(profile.get("config"), "config")
    non_secret_env = mapping(config.get("non_secret_env"), "config.non_secret_env")
    secret_refs = mapping(config.get("secret_refs"), "config.secret_refs")
    probe = mapping(write_client.get("admission_probe"), "auth.persistence_write_test_client.admission_probe")

    policy = {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "hostname": required_string(route53.get("hostname"), "aws.route53.hostname"),
        "token_url": required_string(mapping(auth.get("token_validation"), "auth.token_validation").get("token_url"), "auth.token_validation.token_url"),
        "status": required_string(write_client.get("status"), "auth.persistence_write_test_client.status"),
        "client_id": required_string(write_client.get("client_id"), "auth.persistence_write_test_client.client_id"),
        "secret_arn": required_string(write_client.get("secret_arn"), "auth.persistence_write_test_client.secret_arn"),
    }
    if policy["account_id"] != EXPECTED_ACCOUNT_ID or policy["region"] != "eu-west-1" or policy["hostname"] != "staging.platform.kanbien.com":
        raise AdmissionProbeError("the target profile does not match the reviewed staging admission-probe target")
    if policy["token_url"] != "https://kanbien-staging-platform-shell-337159794548.auth.eu-west-1.amazoncognito.com/oauth2/token":
        raise AdmissionProbeError("the target profile does not match the reviewed Cognito token endpoint")
    if write_client.get("name") != "platform-shell-staging-persistence-write-client" or write_client.get("type") != "confidential" or write_client.get("grant_type") != "client_credentials":
        raise AdmissionProbeError("the admission probe must retain the reviewed confidential machine client")
    if resource_server != {
        "identifier": "platform-shell",
        "name": "Platform Shell",
        "scope_name": "smoke.write",
        "scope": "platform-shell/smoke.write",
        "permission_mapping": "platform-smoke.persistence.work-item:create",
    }:
        raise AdmissionProbeError("the admission probe must retain the reviewed write-only scope")
    if secret != {
        "name": "kanbien/staging/platform-shell/cognito-persistence-write-client",
        "delivery": "bounded-persistence-smoke-only-not-ecs-task-environment",
        "value_format": "opaque-raw-string",
    }:
        raise AdmissionProbeError("the admission probe must retain the separately bounded secret policy")
    if not policy["secret_arn"].startswith("arn:aws:secretsmanager:eu-west-1:337159794548:secret:kanbien/staging/platform-shell/cognito-persistence-write-client-"):
        raise AdmissionProbeError("the admission-probe secret ARN must remain target scoped")
    expected_secret_reference = {
        "name": secret["name"],
        "arn": policy["secret_arn"],
        "delivery": secret["delivery"],
        "value_format": secret["value_format"],
    }
    if secret_refs.get("cognito_persistence_write_client_secret") != expected_secret_reference:
        raise AdmissionProbeError("the admission probe must retain the bounded target-owned secret reference")
    negative = mapping(auth.get("negative_test_client"), "auth.negative_test_client")
    negative_client_id = required_string(negative.get("client_id"), "auth.negative_test_client.client_id")
    if parse_client_allowlist(non_secret_env.get("PLATFORM_AUTH_COGNITO_ADDITIONAL_APP_CLIENT_IDS")) != [negative_client_id, policy["client_id"]]:
        raise AdmissionProbeError("the admission probe requires the exact deployed proof-client allowlist")

    base_probe = {
        "route": "POST /smoke/work-items/admission",
        "permission": "platform-smoke.persistence.work-item:create",
        "request_body": "none",
        "persistence_side_effects": "prohibited",
        "expected_http_status": 204,
        "output_policy": "status-and-safe-latency-only-no-token-secret-request-id-or-response-body",
    }
    if policy["status"] == SOURCE_READY:
        expected_probe = {
            **base_probe,
            "status": "source-ready-deployment-pending",
            "next_guard": "reviewed-service-deployment-and-health-before-one-execution",
        }
    elif policy["status"] == DEPLOYED_READY:
        expected_probe = {
            **base_probe,
            "status": "deployed-pending-one-execution",
            "next_guard": "one-execution-only-then-record-safe-result-before-any-fresh-persistence-write",
        }
    else:
        raise AdmissionProbeError("the admission probe is not in a governed lifecycle state")
    if probe != expected_probe:
        raise AdmissionProbeError("the admission probe must retain its fixed non-mutating policy")
    return policy


def aws_call(policy: dict[str, str], arguments: list[str]) -> str:
    """Perform one fixed AWS lookup and retain its output only in local memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    result = subprocess.run(
        ["aws", *arguments, "--profile", policy["aws_profile"], "--region", policy["region"]],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )
    if result.returncode != 0:
        raise AdmissionProbeError("the approved AWS lookup did not complete")
    return result.stdout


def verify_account(policy: dict[str, str]) -> None:
    """Fail closed if current credentials resolve outside the reviewed account."""

    try:
        identity = json.loads(aws_call(policy, ["sts", "get-caller-identity", "--output", "json"]))
    except json.JSONDecodeError as exception:
        raise AdmissionProbeError("the AWS account lookup returned an unexpected response") from exception
    if not isinstance(identity, dict) or identity.get("Account") != policy["account_id"]:
        raise AdmissionProbeError("the selected AWS identity is not the target account")


def load_secret(policy: dict[str, str]) -> str:
    """Read the declared secret only into memory; never print it."""

    secret = aws_call(policy, ["secretsmanager", "get-secret-value", "--secret-id", policy["secret_arn"], "--query", "SecretString", "--output", "text"]).rstrip("\r\n")
    if not secret or secret == "None":
        raise AdmissionProbeError("the declared persistence smoke client secret is unavailable")
    return secret


def acquire_token(policy: dict[str, str], secret: str) -> str:
    """Exchange the fixed write-only client secret for an in-memory token."""

    basic = base64.b64encode(f"{policy['client_id']}:{secret}".encode("utf-8")).decode("ascii")
    body = parse.urlencode({"grant_type": "client_credentials", "scope": "platform-shell/smoke.write"}).encode("ascii")
    token_request = request.Request(
        policy["token_url"],
        data=body,
        method="POST",
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    try:
        with request.urlopen(token_request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exception:
        raise AdmissionProbeError("admission-probe token acquisition failed") from exception
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise AdmissionProbeError("admission-probe token acquisition returned no access token")
    return token


def request_admission(policy: dict[str, str], token: str) -> tuple[int, int]:
    """Call precisely the fixed no-body route and retain only status and latency."""

    admission_request = request.Request(
        f"https://{policy['hostname']}/smoke/work-items/admission",
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    started = time.monotonic()
    try:
        with request.urlopen(admission_request, timeout=10) as response:
            status = response.status
    except error.HTTPError as exception:
        status = exception.code
    except (error.URLError, TimeoutError) as exception:
        raise AdmissionProbeError("the admission-probe request did not complete") from exception
    return status, round((time.monotonic() - started) * 1000)


def emit(result: str, status: int | None = None, duration_ms: int | None = None) -> None:
    """Emit safe aggregate facts only."""

    payload: dict[str, Any] = {"persistence_admission_probe": result}
    if status is not None:
        payload["http_status"] = status
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate or make exactly one policy-gated, non-mutating request."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile())
    if arguments.validate:
        emit("validated")
        return 0
    if policy["status"] != DEPLOYED_READY:
        raise AdmissionProbeError("the admission probe may run only after the reviewed service deployment is healthy")
    secret: str | None = None
    token: str | None = None
    try:
        verify_account(policy)
        secret = load_secret(policy)
        token = acquire_token(policy, secret)
        status, duration_ms = request_admission(policy, token)
    finally:
        secret = None
        token = None
    emit("passed" if status == EXPECTED_STATUS else "unexpected-status", status, duration_ms)
    return 0 if status == EXPECTED_STATUS else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AdmissionProbeError as exception:
        print(f"persistence-admission-probe: {exception}", file=sys.stderr)
        raise SystemExit(1)
