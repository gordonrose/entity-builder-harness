#!/usr/bin/env python3
"""Validate or run the fixed staging WAF, routing, ingress, and liveness proof."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
from urllib import error, request


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SAFE_HOSTNAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")


class IngressSmokeError(Exception):
    """Represent a safe-to-report policy or read-only inspection failure."""


def parse_arguments() -> argparse.Namespace:
    """Permit only no-network policy validation or the fixed read-only live inspection."""

    parser = argparse.ArgumentParser(description="Validate or run the bounded Kanbien staging ingress proof.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS or HTTP call.")
    parser.add_argument("--execute", action="store_true", help="Perform the fixed read-only inspection and liveness request.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable for fixed read-only inspections.")
    parser.add_argument("--aws-credential-source", choices=("target-profile", "environment"), default="target-profile", help="Use the declared AWS profile or explicitly configured environment credentials.")
    parser.add_argument("--timeout-seconds", type=int, default=10, help="Bound the fixed public liveness request to 1-30 seconds.")
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    return arguments


def load_profile(path: Path) -> dict[str, Any]:
    """Load the reviewed target profile with no permissive fallback parser."""

    try:
        import yaml
    except ImportError as exception:
        raise IngressSmokeError("PyYAML is required for ingress-smoke policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            profile = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise IngressSmokeError("the target profile could not be read") from exception
    if not isinstance(profile, dict):
        raise IngressSmokeError("the target profile must be a YAML mapping")
    return profile


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a reviewed mapping rather than silently accepting missing policy."""

    if not isinstance(value, dict):
        raise IngressSmokeError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require a non-empty string before passing a value to an AWS or HTTP client."""

    if not isinstance(value, str) or not value:
        raise IngressSmokeError(f"the target profile must declare {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, str | int]:
    """Extract exactly the identifiers and expected facts used by the finite proof."""

    cloud = mapping(profile.get("cloud"), "cloud")
    aws = mapping(profile.get("aws"), "aws")
    alb = mapping(aws.get("alb"), "aws.alb")
    route53 = mapping(aws.get("route53"), "aws.route53")
    security_groups = mapping(aws.get("security_groups"), "aws.security_groups")
    rate_limiting = mapping(profile.get("rate_limiting"), "rate_limiting")
    edge_protection = mapping(rate_limiting.get("edge_protection"), "rate_limiting.edge_protection")
    operations = mapping(profile.get("operations"), "operations")
    closure = mapping(operations.get("readiness_closure"), "operations.readiness_closure")
    ingress = mapping(closure.get("waf_and_routing"), "operations.readiness_closure.waf_and_routing")

    hostname = required_string(route53.get("hostname"), "aws.route53.hostname")
    if not SAFE_HOSTNAME.fullmatch(hostname) or not hostname.endswith(".kanbien.com"):
        raise IngressSmokeError("the ingress-proof hostname is not an approved HTTPS DNS name")
    policy: dict[str, str | int] = {
        "account_id": required_string(cloud.get("account_id"), "cloud.account_id"),
        "aws_profile": required_string(cloud.get("profile"), "cloud.profile"),
        "region": required_string(cloud.get("region"), "cloud.region"),
        "alb_arn": required_string(alb.get("arn"), "aws.alb.arn"),
        "listener_arn": required_string(alb.get("listener_https"), "aws.alb.listener_https"),
        "alb_security_group": required_string(security_groups.get("alb"), "aws.security_groups.alb"),
        "hostname": hostname,
        "host_rule_priority": alb.get("host_rule_priority"),
        "web_acl_name": required_string(edge_protection.get("web_acl_name"), "rate_limiting.edge_protection.web_acl_name"),
    }
    if policy["host_rule_priority"] != 20:
        raise IngressSmokeError("the ingress proof requires the reviewed listener priority 20")
    expected = {
        "status": "source-defined-deployment-pending",
        "command": "npm run platform:shell:ingress-smoke",
        "proof": "read-only-waf-association-and-listener-host-rule-inspection-plus-bounded-public-host-check",
        "request": {
            "method": "GET",
            "path": "/livez",
            "credentials": "none",
            "expected_http_status": 200,
            "output_policy": "safe-facts-only-no-response-body-address-or-provider-payload",
        },
    }
    for key, value in expected.items():
        if ingress.get(key) != value:
            raise IngressSmokeError("the target profile ingress proof policy no longer matches the reviewed bounded shape")
    return policy


def aws_arguments(policy: dict[str, str | int], credential_source: str) -> list[str]:
    """Select the only approved credential source without caller-provided profiles."""

    arguments = ["--region", str(policy["region"])]
    if credential_source == "target-profile":
        arguments.extend(["--profile", str(policy["aws_profile"])])
    return arguments


def run_aws(arguments: list[str], policy: dict[str, str | int], aws_cli: str, credential_source: str) -> dict[str, Any]:
    """Execute one fixed read-only AWS CLI call and retain raw provider output only in memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    if credential_source == "environment":
        environment.pop("AWS_PROFILE", None)
    result = subprocess.run([aws_cli, *arguments, *aws_arguments(policy, credential_source), "--output", "json"], check=False, capture_output=True, encoding="utf-8", env=environment)
    if result.returncode != 0:
        raise IngressSmokeError("the approved read-only AWS inspection did not complete")
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exception:
        raise IngressSmokeError("the AWS inspection returned an unexpected response") from exception
    if not isinstance(parsed, dict):
        raise IngressSmokeError("the AWS inspection response must be an object")
    return parsed


def verify_account(policy: dict[str, str | int], aws_cli: str, credential_source: str) -> None:
    """Fail closed if the selected read-only identity points at another AWS account."""

    identity = run_aws(["sts", "get-caller-identity"], policy, aws_cli, credential_source)
    if identity.get("Account") != policy["account_id"]:
        raise IngressSmokeError("the selected AWS identity is not the target account")


def verify_waf_association(policy: dict[str, str | int], aws_cli: str, credential_source: str) -> None:
    """Confirm the selected regional WAF is associated with only the reviewed shared ALB."""

    response = run_aws(["wafv2", "get-web-acl-for-resource", "--resource-arn", str(policy["alb_arn"])], policy, aws_cli, credential_source)
    web_acl = response.get("WebACL")
    if not isinstance(web_acl, dict) or web_acl.get("Name") != policy["web_acl_name"] or not isinstance(web_acl.get("ARN"), str) or not web_acl["ARN"]:
        raise IngressSmokeError("the reviewed host-scoped WAF association was not found")


def verify_host_rule(policy: dict[str, str | int], aws_cli: str, credential_source: str) -> None:
    """Confirm priority 20 still forwards only the reviewed host header route."""

    response = run_aws(["elbv2", "describe-rules", "--listener-arn", str(policy["listener_arn"])], policy, aws_cli, credential_source)
    rules = response.get("Rules")
    if not isinstance(rules, list):
        raise IngressSmokeError("the HTTPS listener inspection returned no rule list")
    matching = [rule for rule in rules if isinstance(rule, dict) and rule.get("Priority") == str(policy["host_rule_priority"])]
    if len(matching) != 1:
        raise IngressSmokeError("the reviewed listener priority does not resolve to exactly one host rule")
    conditions = matching[0].get("Conditions")
    actions = matching[0].get("Actions")
    has_host = any(
        isinstance(condition, dict)
        and condition.get("Field") == "host-header"
        and condition.get("HostHeaderConfig", {}).get("Values") == [policy["hostname"]]
        for condition in conditions if isinstance(conditions, list)
    )
    has_forward = any(isinstance(action, dict) and action.get("Type") == "forward" for action in actions if isinstance(actions, list))
    if not has_host or not has_forward:
        raise IngressSmokeError("the reviewed listener rule no longer forwards only the target hostname")


def verify_service_ingress(policy: dict[str, str | int], aws_cli: str, credential_source: str) -> None:
    """Confirm the server task group accepts only TCP 3000 from the reviewed ALB security group."""

    response = run_aws(["ec2", "describe-security-groups", "--filters", "Name=group-name,Values=kanbien-staging-platform-shell-service"], policy, aws_cli, credential_source)
    groups = response.get("SecurityGroups")
    if not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], dict):
        raise IngressSmokeError("the reviewed service security group was not found uniquely")
    ingress = groups[0].get("IpPermissions")
    if not isinstance(ingress, list) or len(ingress) != 1 or not isinstance(ingress[0], dict):
        raise IngressSmokeError("the service security group must have exactly one reviewed ingress rule")
    rule = ingress[0]
    pairs = rule.get("UserIdGroupPairs")
    group_ids = [pair.get("GroupId") for pair in pairs if isinstance(pair, dict)] if isinstance(pairs, list) else []
    if rule.get("IpProtocol") != "tcp" or rule.get("FromPort") != 3000 or rule.get("ToPort") != 3000 or group_ids != [policy["alb_security_group"]] or rule.get("IpRanges") or rule.get("Ipv6Ranges") or rule.get("PrefixListIds"):
        raise IngressSmokeError("the service security group no longer permits only ALB TCP 3000 ingress")


def request_liveness(policy: dict[str, str | int], timeout_seconds: int) -> tuple[int, int]:
    """Make one fixed public liveness request and discard every response byte."""

    started = time.monotonic()
    bounded_request = request.Request(f"https://{policy['hostname']}/livez", method="GET", headers={"Accept": "application/json"})
    try:
        with request.urlopen(bounded_request, timeout=timeout_seconds) as response:
            status = response.status
    except error.HTTPError as exception:
        status = exception.code
    except (error.URLError, TimeoutError) as exception:
        raise IngressSmokeError("the public liveness request did not complete") from exception
    return status, round((time.monotonic() - started) * 1000)


def emit_safe_result(result: str, **fields: int | str) -> None:
    """Emit only safe proof facts; never emit identifiers, headers, bodies, or provider data."""

    print(json.dumps({"ingress_smoke": result, **fields}, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate policy or perform the finite read-only proof."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile(Path(arguments.target_profile)))
    if arguments.validate:
        emit_safe_result("validated", host_rule_priority=policy["host_rule_priority"])
        return 0
    verify_account(policy, arguments.aws_cli, arguments.aws_credential_source)
    verify_waf_association(policy, arguments.aws_cli, arguments.aws_credential_source)
    verify_host_rule(policy, arguments.aws_cli, arguments.aws_credential_source)
    verify_service_ingress(policy, arguments.aws_cli, arguments.aws_credential_source)
    status, duration_ms = request_liveness(policy, arguments.timeout_seconds)
    emit_safe_result("passed" if status == 200 else "unexpected-status", http_status=status, duration_ms=duration_ms, host_rule_priority=policy["host_rule_priority"])
    return 0 if status == 200 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except IngressSmokeError as exception:
        print(f"ingress-smoke: {exception}", file=sys.stderr)
        raise SystemExit(1)
