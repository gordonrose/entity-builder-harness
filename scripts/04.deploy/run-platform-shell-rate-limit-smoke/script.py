#!/usr/bin/env python3
"""Validate or run the fixed aggregate-only staging rate-limit proof."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib import error, request


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SAFE_HOSTNAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")


class RateLimitSmokeError(Exception):
    """Represent a safe-to-report policy or bounded-request failure."""


def parse_arguments() -> argparse.Namespace:
    """Allow only validation or the one fixed live proof, never caller-selected traffic."""

    parser = argparse.ArgumentParser(description="Validate or run the bounded Kanbien staging rate-limit proof.")
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no network request.")
    parser.add_argument("--execute", action="store_true", help="Perform the fixed public liveness requests after current-chat approval.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--timeout-seconds", type=int, default=10, help="Bound every fixed HTTP request to 1-30 seconds.")
    arguments = parser.parse_args()
    if arguments.validate == arguments.execute:
        parser.error("choose exactly one of --validate or --execute")
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    return arguments


def load_profile(path: Path) -> dict[str, Any]:
    """Load the reviewed target profile without a permissive fallback parser."""

    try:
        import yaml
    except ImportError as exception:
        raise RateLimitSmokeError("PyYAML is required for rate-limit-smoke policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            profile = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exception:
        raise RateLimitSmokeError("the target profile could not be read") from exception
    if not isinstance(profile, dict):
        raise RateLimitSmokeError("the target profile must be a YAML mapping")
    return profile


def mapping(value: Any, path: str) -> dict[str, Any]:
    """Require a profile mapping instead of assuming a missing policy default."""

    if not isinstance(value, dict):
        raise RateLimitSmokeError(f"the target profile must declare {path}")
    return value


def required_string(value: Any, path: str) -> str:
    """Require a non-empty string before using a profile value externally."""

    if not isinstance(value, str) or not value:
        raise RateLimitSmokeError(f"the target profile must declare {path}")
    return value


def resolve_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract the finite liveness-proof policy and reject scope expansion."""

    aws = mapping(profile.get("aws"), "aws")
    route53 = mapping(aws.get("route53"), "aws.route53")
    config = mapping(profile.get("config"), "config")
    environment = mapping(config.get("non_secret_env"), "config.non_secret_env")
    operations = mapping(profile.get("operations"), "operations")
    closure = mapping(operations.get("readiness_closure"), "operations.readiness_closure")
    rate_limit = mapping(closure.get("rate_limit_429"), "operations.readiness_closure.rate_limit_429")

    hostname = required_string(route53.get("hostname"), "aws.route53.hostname")
    if not SAFE_HOSTNAME.fullmatch(hostname) or not hostname.endswith(".kanbien.com"):
        raise RateLimitSmokeError("the rate-limit proof hostname is not an approved HTTPS DNS name")

    limit_raw = environment.get("PLATFORM_RATE_LIMIT_LIMIT")
    window_raw = environment.get("PLATFORM_RATE_LIMIT_WINDOW_MS")
    try:
        limit = int(limit_raw)
        window_ms = int(window_raw)
    except (TypeError, ValueError) as exception:
        raise RateLimitSmokeError("the target profile must declare integer rate-limit limit and window values") from exception
    if limit <= 0 or window_ms <= 0:
        raise RateLimitSmokeError("the target profile rate-limit values must be positive")

    expected = {
        "status": "source-defined-deployment-pending",
        "command": "npm run platform:shell:rate-limit-smoke",
        "request_bound": "fresh-fixed-window-declared-limit-plus-one-sequential-requests-stop-on-first-429",
        "fixed_window_alignment": "wait-for-next-window-boundary-and-return-inconclusive-on-rollover",
        "safe_result": "aggregate-counts-and-final-status-only",
        "request": {
            "method": "GET",
            "path": "/livez",
            "credentials": "none",
            "expected_allowed_status": 200,
            "expected_limited_status": 429,
            "slo_population_effect": "none-protected-capability-metrics-are-not-emitted-for-liveness",
        },
    }
    for key, value in expected.items():
        if rate_limit.get(key) != value:
            raise RateLimitSmokeError("the target profile rate-limit proof policy no longer matches the reviewed bounded shape")

    return {
        "hostname": hostname,
        "limit": limit,
        "window_ms": window_ms,
        "max_requests": limit + 1,
    }


def request_liveness(hostname: str, timeout_seconds: int) -> tuple[int, int]:
    """Make one fixed no-body public liveness request and retain only status and latency."""

    started = time.monotonic()
    bounded_request = request.Request(
        f"https://{hostname}/livez",
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with request.urlopen(bounded_request, timeout=timeout_seconds) as response:
            status = response.status
    except error.HTTPError as exception:
        status = exception.code
    except (error.URLError, TimeoutError) as exception:
        raise RateLimitSmokeError("the public liveness request did not complete") from exception
    return status, round((time.monotonic() - started) * 1000)


def fixed_window_started_at_ms(window_ms: int) -> int:
    """Return the current fixed-window boundary using the same epoch model as the adapter."""

    now_ms = int(time.time() * 1_000)
    return (now_ms // window_ms) * window_ms


def wait_for_next_fixed_window(window_ms: int) -> int:
    """Start only after a fresh window so earlier caller traffic cannot distort the proof."""

    current_window_started_at_ms = fixed_window_started_at_ms(window_ms)
    next_window_started_at_ms = current_window_started_at_ms + window_ms
    now_ms = int(time.time() * 1_000)
    time.sleep(max(0, next_window_started_at_ms - now_ms) / 1_000)
    while fixed_window_started_at_ms(window_ms) < next_window_started_at_ms:
        time.sleep(0.005)
    return next_window_started_at_ms


def emit_safe_result(result: str, **fields: int | str) -> None:
    """Emit aggregate-only proof facts; omit every response body, header, address, and identifier."""

    print(json.dumps({"rate_limit_smoke": result, **fields}, separators=(",", ":"), sort_keys=True))


def execute(policy: dict[str, Any], timeout_seconds: int) -> int:
    """Run the finite sequential proof and stop at the first bounded rate-limit response."""

    expected_window_started_at_ms = wait_for_next_fixed_window(policy["window_ms"])
    allowed_count = 0
    total_duration_ms = 0
    final_status = 0
    for request_number in range(1, policy["max_requests"] + 1):
        status, duration_ms = request_liveness(policy["hostname"], timeout_seconds)
        total_duration_ms += duration_ms
        final_status = status
        if fixed_window_started_at_ms(policy["window_ms"]) != expected_window_started_at_ms:
            emit_safe_result(
                "inconclusive-window-rolled-over",
                attempted_request_count=request_number,
                allowed_request_count=allowed_count,
                final_status=status,
                total_duration_ms=total_duration_ms,
            )
            return 1
        if status == 200:
            allowed_count += 1
            continue
        if status == 429:
            if allowed_count == 0:
                emit_safe_result(
                    "inconclusive-existing-window",
                    attempted_request_count=request_number,
                    allowed_request_count=allowed_count,
                    first_429_request=request_number,
                    final_status=status,
                    total_duration_ms=total_duration_ms,
                )
                return 1
            emit_safe_result(
                "passed",
                attempted_request_count=request_number,
                allowed_request_count=allowed_count,
                first_429_request=request_number,
                final_status=status,
                total_duration_ms=total_duration_ms,
            )
            return 0
        emit_safe_result(
            "unexpected-status",
            attempted_request_count=request_number,
            allowed_request_count=allowed_count,
            final_status=status,
            total_duration_ms=total_duration_ms,
        )
        return 1

    emit_safe_result(
        "missing-429",
        attempted_request_count=policy["max_requests"],
        allowed_request_count=allowed_count,
        final_status=final_status,
        total_duration_ms=total_duration_ms,
    )
    return 1


def main() -> int:
    """Validate policy or run the reviewed finite proof path."""

    arguments = parse_arguments()
    policy = resolve_policy(load_profile(Path(arguments.target_profile)))
    if arguments.validate:
        emit_safe_result("validated", max_request_count=policy["max_requests"])
        return 0
    return execute(policy, arguments.timeout_seconds)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RateLimitSmokeError as exception:
        print(f"rate-limit-smoke: {exception}", file=sys.stderr)
        raise SystemExit(1)
