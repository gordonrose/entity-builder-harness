#!/usr/bin/env python3
"""Deterministically test the bounded segmented SLO calculation without AWS access."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
COMMAND_PATH = ROOT / "scripts/04.deploy/run-platform-shell-metric-coverage/script.py"
PROFILE_PATH = ROOT / "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SPECIFICATION = importlib.util.spec_from_file_location("metric_coverage_command", COMMAND_PATH)
if SPECIFICATION is None or SPECIFICATION.loader is None:
    raise SystemExit("ERROR: metric-coverage command could not be loaded")
COMMAND = importlib.util.module_from_spec(SPECIFICATION)
sys.modules[SPECIFICATION.name] = COMMAND
SPECIFICATION.loader.exec_module(COMMAND)


def fake_credentials(*_: Any) -> dict[str, str]:
    """Avoid exporting or retaining any real credentials during this local test."""

    return {"AccessKeyId": "test", "SecretAccessKey": "test"}


query_calls: list[tuple[str, object]] = []


def fake_promql_query(_: dict[str, Any], query: str, *arguments: Any) -> list[dict[str, Any]]:
    """Return fixed aggregate results for the reviewed counter and histogram queries."""

    evaluation_time = arguments[3]
    query_calls.append((query, evaluation_time))
    if "kanbien.platform.server.request.outcome" in query:
        return [{"value": [0, "100"]}]
    if "kanbien.platform.server.request.duration" in query:
        return [
            {"metric": {"le": "100"}, "value": [0, "99"]},
            {"metric": {"le": "200"}, "value": [0, "100"]},
            {"metric": {"le": "+Inf"}, "value": [0, "100"]},
        ]
    raise AssertionError("unexpected metric query")


policy = COMMAND.resolve_policy(COMMAND.load_yaml(PROFILE_PATH))
original_credentials = COMMAND.credentials
original_promql_query = COMMAND.promql_query
try:
    COMMAND.credentials = fake_credentials
    COMMAND.promql_query = fake_promql_query
    results = COMMAND.evaluate_slos(policy, "aws", "target-profile", 1)
finally:
    COMMAND.credentials = original_credentials
    COMMAND.promql_query = original_promql_query

expected_states = ["healthy", "healthy", "healthy"]
if [result["state"] for result in results] != expected_states:
    raise SystemExit("ERROR: segmented SLO evaluation did not return the expected healthy states")
if results[0].get("eligible_observations") != 2800:
    raise SystemExit("ERROR: segmented SLO evaluation did not aggregate all 28 eligible counter windows")
if len(query_calls) != 112:
    raise SystemExit("ERROR: segmented SLO evaluation did not issue the expected bounded query count")
if any("[1d]" not in query for query, _ in query_calls):
    raise SystemExit("ERROR: segmented SLO evaluation exceeded the live-proven one-day lookback")
if len({evaluation_time for _, evaluation_time in query_calls}) != 28:
    raise SystemExit("ERROR: segmented SLO evaluation did not reuse one shared set of segment boundaries")

invalid_policy = copy.deepcopy(policy)
invalid_policy["slos"][0]["rolling_window_days"] = 27
try:
    COMMAND.validate_slo_segment_policy(invalid_policy, *invalid_policy["slos"])
except COMMAND.MetricCoverageError:
    pass
else:
    raise SystemExit("ERROR: segmented SLO evaluation accepted a rolling window that is not an exact safe partition")

print("Platform-shell segmented SLO evaluation local test passed.")
