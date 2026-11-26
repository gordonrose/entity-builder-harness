#!/usr/bin/env python3
"""Evaluate only the declared Kanbien staging metric-coverage and SLO policy."""

from __future__ import annotations

import argparse
import datetime as datetime_module
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib import error, parse, request


class MetricCoverageError(Exception):
    """Represent one safe-to-report policy, credential, or query failure."""


DEFAULT_PROFILE = "infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml"
SAFE_IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,79}$")
SAFE_METRIC_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9._-]{0,199}$")
SAFE_LABEL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
SAFE_LABEL_VALUE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
SAFE_TOPIC_ARN = re.compile(r"^arn:aws:sns:([a-z0-9-]+):(\d{12}):([A-Za-z0-9_-]{1,256})$")
EXPECTED_COVERAGE_VERDICTS = ("observed", "missing", "query-failed", "notification-failed")
EXPECTED_NON_OBSERVED_CONFIDENCE = "insufficient-confidence"


def parse_arguments() -> argparse.Namespace:
    """Accept only the bounded local validation, coverage, and SLO operations."""

    parser = argparse.ArgumentParser(
        description="Validate or evaluate the declared Kanbien staging metric coverage and SLO policy."
    )
    parser.add_argument("--validate", action="store_true", help="Validate policy only; make no AWS, SNS, or HTTP call.")
    parser.add_argument("--mode", choices=("coverage", "slo"), default="coverage", help="Evaluate the reviewed metric-arrival check or the reviewed SLO calculations.")
    parser.add_argument("--coverage-target", choices=("server", "worker"), default="server", help="Select the fixed server SLO-coverage policy or the fixed worker-delivery observation policy.")
    parser.add_argument("--notify-on-non-observed", action="store_true", help="Publish one fixed safe SNS notification only when coverage is not observed.")
    parser.add_argument("--target-profile", default=DEFAULT_PROFILE, help="Path to the Kanbien staging target profile.")
    parser.add_argument("--aws-cli", default="aws", help="AWS CLI executable used only for credential export, identity verification, and fixed SNS publication.")
    parser.add_argument("--aws-credential-source", choices=("target-profile", "environment"), default="target-profile", help="Use the declared local AWS profile or explicitly configured OIDC environment credentials.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="Bound every live AWS, PromQL, and SNS call to 1-30 seconds.")
    arguments = parser.parse_args()
    if not 1 <= arguments.timeout_seconds <= 30:
        parser.error("--timeout-seconds must be between 1 and 30")
    if arguments.validate and arguments.notify_on_non_observed:
        parser.error("--validate cannot publish a notification")
    if arguments.mode != "coverage" and arguments.notify_on_non_observed:
        parser.error("--notify-on-non-observed is permitted only for --mode coverage")
    if arguments.coverage_target != "server" and arguments.mode == "slo":
        parser.error("--mode slo is currently defined only for the server coverage target")
    if arguments.coverage_target != "server" and arguments.notify_on_non_observed:
        parser.error("--notify-on-non-observed is currently defined only for the server coverage target")
    return arguments


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one target profile using the repository's fixed YAML parser dependency."""

    try:
        import yaml
    except ImportError as exception:
        raise MetricCoverageError("PyYAML is required for metric-coverage policy validation") from exception
    try:
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except OSError as exception:
        raise MetricCoverageError("the target profile could not be read") from exception
    except yaml.YAMLError as exception:
        raise MetricCoverageError("the target profile is not valid YAML") from exception
    if not isinstance(document, dict):
        raise MetricCoverageError("the target profile must be a YAML mapping")
    return document


def mapping(value: Any, name: str) -> dict[str, Any]:
    """Require a mapping rather than silently adopting an unsafe default."""

    if not isinstance(value, dict):
        raise MetricCoverageError(f"the target profile must declare {name}")
    return value


def string(value: Any, name: str) -> str:
    """Require one non-empty string policy value."""

    if not isinstance(value, str) or not value:
        raise MetricCoverageError(f"the target profile must declare {name}")
    return value


def integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    """Require one bounded integer policy value."""

    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise MetricCoverageError(f"the target profile must declare {name} between {minimum} and {maximum}")
    return value


def label_mapping(value: Any, name: str) -> dict[str, str]:
    """Validate the bounded static metric labels allowed in a PromQL selector."""

    document = mapping(value, name)
    if not document:
        raise MetricCoverageError(f"the target profile must declare non-empty {name}")
    labels: dict[str, str] = {}
    for label_name, label_value in document.items():
        if not isinstance(label_name, str) or not SAFE_LABEL_NAME.fullmatch(label_name):
            raise MetricCoverageError(f"the target profile contains an unsafe label name in {name}")
        if not isinstance(label_value, str) or not SAFE_LABEL_VALUE.fullmatch(label_value):
            raise MetricCoverageError(f"the target profile contains an unsafe label value in {name}")
        labels[label_name] = label_value
    return labels


def resolve_server_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract only fixed reviewed values needed to query the server metric-coverage policy."""

    cloud = mapping(profile.get("cloud"), "cloud")
    observability = mapping(profile.get("observability"), "observability")
    coverage = mapping(observability.get("metric_coverage"), "observability.metric_coverage")
    expected_metric = mapping(coverage.get("expected_metric"), "observability.metric_coverage.expected_metric")
    alert = mapping(coverage.get("alert"), "observability.metric_coverage.alert")
    slo_query = mapping(observability.get("slo_query"), "observability.slo_query")
    account_id = string(cloud.get("account_id"), "cloud.account_id")
    region = string(cloud.get("region"), "cloud.region")
    aws_profile = string(cloud.get("profile"), "cloud.profile")
    coverage_id = string(coverage.get("id"), "observability.metric_coverage.id")
    command = string(coverage.get("command"), "observability.metric_coverage.command")
    metric_name = string(expected_metric.get("instrument_name"), "observability.metric_coverage.expected_metric.instrument_name")
    topic_arn = string(alert.get("topic_arn"), "observability.metric_coverage.alert.topic_arn")
    subject = string(alert.get("subject"), "observability.metric_coverage.alert.subject")
    if not account_id.isdigit() or len(account_id) != 12:
        raise MetricCoverageError("the target profile account identifier is unsafe")
    if not SAFE_IDENTIFIER.fullmatch(region):
        raise MetricCoverageError("the target profile region is unsafe")
    if coverage_id != "platform-smoke-protected-read-metric-coverage":
        raise MetricCoverageError("the target profile does not declare the approved metric-coverage identity")
    if command != "npm run platform:shell:metric-coverage":
        raise MetricCoverageError("the target profile must name the governed metric-coverage command")
    if not SAFE_METRIC_NAME.fullmatch(metric_name):
        raise MetricCoverageError("the target profile metric name is unsafe")
    topic_match = SAFE_TOPIC_ARN.fullmatch(topic_arn)
    if topic_match is None or topic_match.group(1) != region or topic_match.group(2) != account_id:
        raise MetricCoverageError("the target profile alert topic is outside the selected account or region")
    if subject != "Kanbien staging platform-shell metric coverage":
        raise MetricCoverageError("the target profile must retain the fixed safe metric-coverage alert subject")
    required_labels = label_mapping(expected_metric.get("required_labels"), "observability.metric_coverage.expected_metric.required_labels")
    expected_labels = {
        "capability": "platform-smoke.smoke.read",
        "action": "read",
        "execution_context": "server",
        "http_method": "GET",
        "outcome": "succeeded",
    }
    if required_labels != expected_labels:
        raise MetricCoverageError("the target profile metric-coverage labels must remain the reviewed static capability facts")
    verdicts = coverage.get("verdicts")
    if verdicts != list(EXPECTED_COVERAGE_VERDICTS):
        raise MetricCoverageError("the target profile must retain the complete reviewed coverage verdict vocabulary")
    if coverage.get("non_observed_slo_confidence") != EXPECTED_NON_OBSERVED_CONFIDENCE:
        raise MetricCoverageError("the target profile must make every non-observed coverage verdict insufficient confidence")
    if coverage.get("output_policy") != "safe-verdict-and-aggregate-only-no-query-body-token-or-response-payload":
        raise MetricCoverageError("the target profile must retain the redacted metric-coverage output policy")
    if alert.get("delivery") != "sns-existing-target-owned-topic-only":
        raise MetricCoverageError("the target profile alert must remain scoped to the existing target-owned SNS topic")
    if alert.get("message_policy") != "fixed-safe-verdict-only-no-metric-response-or-request-data":
        raise MetricCoverageError("the target profile alert must retain its fixed safe message policy")
    query_window_seconds = integer(coverage.get("query_window_seconds"), "observability.metric_coverage.query_window_seconds", 300, 3600)
    rehearsal_isolation_wait_seconds = integer(coverage.get("rehearsal_isolation_wait_seconds"), "observability.metric_coverage.rehearsal_isolation_wait_seconds", 300, 3600)
    if rehearsal_isolation_wait_seconds != query_window_seconds:
        raise MetricCoverageError("the exporter-loss rehearsal isolation wait must equal the metric coverage query window")
    return {
        "coverage_target": "server",
        "account_id": account_id,
        "region": region,
        "aws_profile": aws_profile,
        "coverage_id": coverage_id,
        "metric_name": metric_name,
        "required_labels": required_labels,
        "query_window_seconds": query_window_seconds,
        "arrival_grace_seconds": integer(coverage.get("arrival_grace_seconds"), "observability.metric_coverage.arrival_grace_seconds", 60, 900),
        "rehearsal_isolation_wait_seconds": rehearsal_isolation_wait_seconds,
        "topic_arn": topic_arn,
        "alert_subject": subject,
        "slo_query_window_days": integer(slo_query.get("effective_max_increase_lookback_days"), "observability.slo_query.effective_max_increase_lookback_days", 1, 7),
        "slo_query_segment_count": integer(slo_query.get("rolling_window_segment_count"), "observability.slo_query.rolling_window_segment_count", 1, 28),
        "slos": parse_slos(observability.get("slos"), observability.get("metric_series")),
    }


def resolve_worker_policy(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract the separate fixed worker-delivery observation policy without creating a worker SLO or alert path."""

    cloud = mapping(profile.get("cloud"), "cloud")
    observability = mapping(profile.get("observability"), "observability")
    coverage = mapping(observability.get("worker_metric_coverage"), "observability.worker_metric_coverage")
    expected_metric = mapping(coverage.get("expected_metric"), "observability.worker_metric_coverage.expected_metric")
    account_id = string(cloud.get("account_id"), "cloud.account_id")
    region = string(cloud.get("region"), "cloud.region")
    aws_profile = string(cloud.get("profile"), "cloud.profile")
    coverage_id = string(coverage.get("id"), "observability.worker_metric_coverage.id")
    command = string(coverage.get("command"), "observability.worker_metric_coverage.command")
    metric_name = string(expected_metric.get("instrument_name"), "observability.worker_metric_coverage.expected_metric.instrument_name")
    if not account_id.isdigit() or len(account_id) != 12:
        raise MetricCoverageError("the target profile account identifier is unsafe")
    if not SAFE_IDENTIFIER.fullmatch(region):
        raise MetricCoverageError("the target profile region is unsafe")
    if coverage.get("status") not in ("source-defined-deployment-pending", "deployed-and-query-proven"):
        raise MetricCoverageError("the target profile worker metric observation must retain an approved evidence state")
    if coverage_id != "platform-smoke-rebuild-delivery-metric-observation":
        raise MetricCoverageError("the target profile does not declare the approved worker metric-observation identity")
    if command != "npm run platform:shell:metric-coverage -- --coverage-target worker":
        raise MetricCoverageError("the target profile must name the governed worker metric-observation command")
    if not SAFE_METRIC_NAME.fullmatch(metric_name) or metric_name != "kanbien.platform.worker.job.delivery":
        raise MetricCoverageError("the target profile worker metric name must remain the reviewed delivery counter")
    required_labels = label_mapping(expected_metric.get("required_labels"), "observability.worker_metric_coverage.expected_metric.required_labels")
    expected_labels = {
        "capability": "platform-smoke.smoke.rebuild",
        "action": "execute",
        "execution_context": "worker",
        "job_delivery_disposition": "succeeded",
        "outcome": "succeeded",
    }
    if required_labels != expected_labels:
        raise MetricCoverageError("the target profile worker metric-observation labels must remain the reviewed static delivery facts")
    if coverage.get("verdicts") != ["observed", "missing", "query-failed"]:
        raise MetricCoverageError("the target profile worker metric observation must retain the reviewed verdict vocabulary")
    if coverage.get("output_policy") != "safe-verdict-and-aggregate-only-no-query-body-token-or-response-payload":
        raise MetricCoverageError("the target profile worker metric observation must retain the redacted output policy")
    return {
        "coverage_target": "worker",
        "account_id": account_id,
        "region": region,
        "aws_profile": aws_profile,
        "coverage_id": coverage_id,
        "metric_name": metric_name,
        "required_labels": required_labels,
        "query_window_seconds": integer(coverage.get("query_window_seconds"), "observability.worker_metric_coverage.query_window_seconds", 300, 3600),
        "arrival_grace_seconds": integer(coverage.get("arrival_grace_seconds"), "observability.worker_metric_coverage.arrival_grace_seconds", 60, 900),
    }


def resolve_policy(profile: dict[str, Any], coverage_target: str = "server") -> dict[str, Any]:
    """Select one fixed target-owned policy; callers cannot supply a metric name, labels, or arbitrary query."""

    if coverage_target == "server":
        return resolve_server_policy(profile)
    if coverage_target == "worker":
        return resolve_worker_policy(profile)
    raise MetricCoverageError("the metric coverage target is not approved")


def parse_slos(raw_slos: Any, raw_metric_series: Any) -> list[dict[str, Any]]:
    """Validate the three reviewed smoke SLO declarations and their metric identities."""

    if not isinstance(raw_slos, list) or len(raw_slos) != 3:
        raise MetricCoverageError("the target profile must declare exactly three platform-smoke SLOs")
    if not isinstance(raw_metric_series, list):
        raise MetricCoverageError("the target profile must declare the reviewed platform-smoke metric series")
    raw_metric_series = [entry for entry in raw_metric_series if isinstance(entry, dict) and entry.get("runtime_target") == "server"]
    if len(raw_metric_series) != 2:
        raise MetricCoverageError("the target profile must declare exactly two reviewed server platform-smoke metric series")
    metric_names: dict[str, str] = {}
    for entry in raw_metric_series:
        document = mapping(entry, "observability.metric_series entry")
        metric_id = string(document.get("id"), "observability.metric_series.id")
        otel = mapping(document.get("otel"), "observability.metric_series.otel")
        instrument_name = string(otel.get("instrument_name"), "observability.metric_series.otel.instrument_name")
        if not SAFE_METRIC_NAME.fullmatch(instrument_name):
            raise MetricCoverageError("the target profile contains an unsafe SLO instrument name")
        metric_names[metric_id] = instrument_name
    expected_ids = {
        "platform-smoke-interactive-read-availability",
        "platform-smoke-interactive-read-latency-p95",
        "platform-smoke-interactive-read-latency-p99",
    }
    result: list[dict[str, Any]] = []
    for entry in raw_slos:
        document = mapping(entry, "observability.slos entry")
        slo_id = string(document.get("id"), "observability.slos.id")
        population = mapping(document.get("population"), "observability.slos.population")
        objective = mapping(document.get("objective"), "observability.slos.objective")
        confidence = mapping(document.get("confidence"), "observability.slos.confidence")
        metric_id = string(population.get("metric_series"), "observability.slos.population.metric_series")
        if metric_id not in metric_names:
            raise MetricCoverageError("an SLO references an undeclared metric series")
        labels = label_mapping(population.get("required_dimensions"), "observability.slos.population.required_dimensions")
        if labels != {"capability": "platform-smoke.smoke.read", "action": "read", "execution_context": "server", "http_method": "GET"} and labels != {"capability": "platform-smoke.smoke.read", "action": "read", "execution_context": "server", "http_method": "GET", "outcome": "succeeded"}:
            raise MetricCoverageError("an SLO contains an unreviewed target label set")
        result.append({
            "id": slo_id,
            "metric_name": metric_names[metric_id],
            "labels": labels,
            "objective": objective,
            "minimum_observations": integer(confidence.get("minimum_eligible_observations"), "observability.slos.confidence.minimum_eligible_observations", 1, 1000000),
            "rolling_window_days": integer(document.get("rolling_window_days"), "observability.slos.rolling_window_days", 1, 365),
        })
    if {entry["id"] for entry in result} != expected_ids:
        raise MetricCoverageError("the target profile must retain the reviewed availability, p95, and p99 SLO identities")
    return result


def aws_credential_arguments(policy: dict[str, Any], credential_source: str) -> list[str]:
    """Select only the declared profile or explicitly configured OIDC credentials."""

    arguments = ["--region", policy["region"]]
    if credential_source == "target-profile":
        arguments.extend(["--profile", policy["aws_profile"]])
    return arguments


def run_aws(arguments: list[str], aws_cli: str, credential_source: str, timeout_seconds: int) -> str:
    """Run a fixed AWS CLI operation while retaining all provider output in memory."""

    environment = os.environ.copy()
    environment["AWS_PAGER"] = ""
    environment["AWS_CLI_AUTO_PROMPT"] = "off"
    if credential_source == "environment":
        environment.pop("AWS_PROFILE", None)
    try:
        result = subprocess.run([aws_cli, *arguments], check=False, capture_output=True, encoding="utf-8", env=environment, timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as exception:
        raise MetricCoverageError("the approved AWS operation did not complete") from exception
    if result.returncode != 0:
        raise MetricCoverageError("the approved AWS operation did not complete")
    return result.stdout


def verify_account(policy: dict[str, Any], aws_cli: str, credential_source: str, timeout_seconds: int) -> None:
    """Fail closed when the selected identity is outside the declared target account."""

    response = run_aws(["sts", "get-caller-identity", *aws_credential_arguments(policy, credential_source), "--output", "json"], aws_cli, credential_source, timeout_seconds)
    try:
        account = json.loads(response).get("Account")
    except json.JSONDecodeError as exception:
        raise MetricCoverageError("the AWS account lookup returned an unexpected response") from exception
    if account != policy["account_id"]:
        raise MetricCoverageError("the selected AWS identity is not the target account")


def credentials(policy: dict[str, Any], aws_cli: str, credential_source: str, timeout_seconds: int) -> dict[str, str]:
    """Obtain short-lived credentials without emitting any credential material."""

    if credential_source == "environment":
        values = {
            "AccessKeyId": os.environ.get("AWS_ACCESS_KEY_ID", ""),
            "SecretAccessKey": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            "SessionToken": os.environ.get("AWS_SESSION_TOKEN", ""),
        }
    else:
        response = run_aws(["configure", "export-credentials", "--profile", policy["aws_profile"], "--format", "process"], aws_cli, credential_source, timeout_seconds)
        try:
            values = json.loads(response)
        except json.JSONDecodeError as exception:
            raise MetricCoverageError("the AWS credential export returned an unexpected response") from exception
    if not all(isinstance(values.get(key), str) and values[key] for key in ("AccessKeyId", "SecretAccessKey")):
        raise MetricCoverageError("short-lived AWS credentials are unavailable")
    return {key: value for key, value in values.items() if isinstance(value, str) and value}


def quoted(value: str) -> str:
    """Encode one SigV4 canonical query component using RFC 3986 escaping."""

    return parse.quote(value, safe="-_.~")


def signing_key(secret_access_key: str, date_stamp: str, region: str, service: str) -> bytes:
    """Derive the AWS Signature Version 4 request-signing key in memory only."""

    date_key = hmac.new(("AWS4" + secret_access_key).encode("utf-8"), date_stamp.encode("utf-8"), hashlib.sha256).digest()
    region_key = hmac.new(date_key, region.encode("utf-8"), hashlib.sha256).digest()
    service_key = hmac.new(region_key, service.encode("utf-8"), hashlib.sha256).digest()
    return hmac.new(service_key, b"aws4_request", hashlib.sha256).digest()


def promql_query(policy: dict[str, Any], query: str, aws_cli: str, credential_source: str, timeout_seconds: int, evaluation_time: datetime_module.datetime | None = None, active_credentials: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Run one signed native CloudWatch PromQL instant query and return no raw response text."""

    active_credentials = active_credentials or credentials(policy, aws_cli, credential_source, timeout_seconds)
    region = policy["region"]
    service = "monitoring"
    host = f"monitoring.{region}.amazonaws.com"
    canonical_uri = "/api/v1/query"
    query_parameters = [("query", query)]
    if evaluation_time is not None:
        query_parameters.append(("time", str(int(evaluation_time.timestamp()))))
    canonical_query = "&".join(f"{quoted(name)}={quoted(value)}" for name, value in sorted(query_parameters))
    now = datetime_module.datetime.now(datetime_module.UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    headers = {"host": host, "x-amz-date": amz_date}
    if active_credentials.get("SessionToken"):
        headers["x-amz-security-token"] = active_credentials["SessionToken"]
    canonical_headers = "".join(f"{name}:{headers[name]}\n" for name in sorted(headers))
    signed_headers = ";".join(sorted(headers))
    payload_hash = hashlib.sha256(b"").hexdigest()
    canonical_request = "\n".join(("GET", canonical_uri, canonical_query, canonical_headers, signed_headers, payload_hash))
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(("AWS4-HMAC-SHA256", amz_date, credential_scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()))
    signature = hmac.new(signing_key(active_credentials["SecretAccessKey"], date_stamp, region, service), string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers["Authorization"] = f"AWS4-HMAC-SHA256 Credential={active_credentials['AccessKeyId']}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    endpoint = f"https://{host}{canonical_uri}?{canonical_query}"
    try:
        with request.urlopen(request.Request(endpoint, method="GET", headers=headers), timeout=timeout_seconds) as response:
            document = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exception:
        raise MetricCoverageError(f"the approved CloudWatch PromQL query returned HTTP {exception.code}") from exception
    except (error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exception:
        raise MetricCoverageError("the approved CloudWatch PromQL query did not complete") from exception
    data = document.get("data") if isinstance(document, dict) else None
    result = data.get("result") if isinstance(data, dict) else None
    if document.get("status") != "success" or not isinstance(result, list):
        raise MetricCoverageError("the approved CloudWatch PromQL query returned an unexpected response")
    return [entry for entry in result if isinstance(entry, dict)]


def promql_selector(metric_name: str, labels: dict[str, str]) -> str:
    """Build a PromQL selector from an exact reviewed metric name and static labels."""

    quoted_labels = [f'__name__="{metric_name}"']
    quoted_labels.extend(f'{name}="{value}"' for name, value in sorted(labels.items()))
    return "{" + ",".join(quoted_labels) + "}"


def vector_number(result: list[dict[str, Any]]) -> float:
    """Read one aggregate vector value without returning labels or raw provider content."""

    if len(result) != 1:
        return 0.0
    value = result[0].get("value")
    if not isinstance(value, list) or len(value) != 2 or not isinstance(value[1], str):
        return 0.0
    try:
        number = float(value[1])
    except ValueError:
        return 0.0
    return number if number >= 0 else 0.0


def vector_bucket_counts(result: list[dict[str, Any]]) -> dict[float, float]:
    """Read one aggregated histogram bucket vector without retaining any non-bucket labels."""

    buckets: dict[float, float] = {}
    for entry in result:
        metric = entry.get("metric")
        value = entry.get("value")
        if not isinstance(metric, dict) or not isinstance(value, list) or len(value) != 2:
            continue
        upper_bound = metric.get("le")
        raw_count = value[1]
        if not isinstance(upper_bound, str) or not isinstance(raw_count, str):
            continue
        try:
            bound = float("inf") if upper_bound == "+Inf" else float(upper_bound)
            count = float(raw_count)
        except ValueError:
            continue
        if bound >= 0 and count >= 0:
            buckets[bound] = count
    return buckets


def coverage_query(policy: dict[str, Any]) -> str:
    """Ask whether the approved successful outcome counter advanced in the bounded window."""

    selector = promql_selector(policy["metric_name"], policy["required_labels"])
    return f"sum(increase({selector}[{policy['query_window_seconds']}s]))"


def coverage_verdict(policy: dict[str, Any], aws_cli: str, credential_source: str, timeout_seconds: int) -> str:
    """Classify the approved metric-arrival signal without claiming an SLO result."""

    try:
        result = promql_query(policy, coverage_query(policy), aws_cli, credential_source, timeout_seconds)
    except MetricCoverageError:
        return "query-failed"
    return "observed" if vector_number(result) > 0 else "missing"


def notify(policy: dict[str, Any], verdict: str, aws_cli: str, credential_source: str, timeout_seconds: int) -> bool:
    """Publish one fixed redacted coverage concern to the exact target-owned SNS topic."""

    message = json.dumps({"coverage_id": policy["coverage_id"], "verdict": verdict, "slo_confidence": EXPECTED_NON_OBSERVED_CONFIDENCE}, separators=(",", ":"), sort_keys=True)
    try:
        run_aws(["sns", "publish", "--topic-arn", policy["topic_arn"], "--subject", policy["alert_subject"], "--message", message, *aws_credential_arguments(policy, credential_source), "--output", "json"], aws_cli, credential_source, timeout_seconds)
    except MetricCoverageError:
        return False
    return True


def metric_name_by_slo(policy: dict[str, Any], slo_id: str) -> dict[str, Any]:
    """Resolve exactly one reviewed SLO declaration by its stable target-owned identity."""

    matches = [entry for entry in policy["slos"] if entry["id"] == slo_id]
    if len(matches) != 1:
        raise MetricCoverageError("the target profile does not declare one required SLO")
    return matches[0]


def evaluate_slos(policy: dict[str, Any], aws_cli: str, credential_source: str, timeout_seconds: int) -> list[dict[str, Any]]:
    """Calculate only the selected availability, p95, and p99 policy outcomes."""

    availability = metric_name_by_slo(policy, "platform-smoke-interactive-read-availability")
    p95 = metric_name_by_slo(policy, "platform-smoke-interactive-read-latency-p95")
    p99 = metric_name_by_slo(policy, "platform-smoke-interactive-read-latency-p99")
    validate_slo_segment_policy(policy, availability, p95, p99)
    success_labels = availability["labels"] | {"outcome": "succeeded"}
    eligible_selector = promql_selector(availability["metric_name"], availability["labels"]).replace('}', ',outcome=~"succeeded|failed"}')
    success_selector = promql_selector(availability["metric_name"], success_labels)
    try:
        active_credentials = credentials(policy, aws_cli, credential_source, timeout_seconds)
        evaluation_times = slo_evaluation_times(policy)
        eligible = segmented_counter_increase(policy, eligible_selector, aws_cli, credential_source, timeout_seconds, evaluation_times, active_credentials)
        successes = segmented_counter_increase(policy, success_selector, aws_cli, credential_source, timeout_seconds, evaluation_times, active_credentials)
        if eligible < availability["minimum_observations"]:
            return insufficient_confidence_results(availability, p95, p99, eligible)
        if successes > eligible:
            raise MetricCoverageError("the selected successful observations exceed the eligible observation population")
        availability_percent = (successes / eligible) * 100 if eligible else 0.0
        p95_value = histogram_percentile(policy, p95, 0.95, aws_cli, credential_source, timeout_seconds, evaluation_times, active_credentials)
        p99_value = histogram_percentile(policy, p99, 0.99, aws_cli, credential_source, timeout_seconds, evaluation_times, active_credentials)
    except MetricCoverageError:
        return query_failed_results(availability, p95, p99)
    return [
        {"id": availability["id"], "state": "healthy" if availability_percent >= availability["objective"].get("target_percent") else "breached", "eligible_observations": round(eligible, 3), "value_percent": round(availability_percent, 3)},
        percentile_result(p95, p95_value),
        percentile_result(p99, p99_value),
    ]


def histogram_percentile(policy: dict[str, Any], slo: dict[str, Any], percentile: float, aws_cli: str, credential_source: str, timeout_seconds: int, evaluation_times: list[datetime_module.datetime], active_credentials: dict[str, str]) -> float:
    """Calculate one selected percentile from buckets aggregated across bounded provider windows."""

    selector = promql_selector(slo["metric_name"], slo["labels"])
    bucket_totals: dict[float, float] = {}
    for evaluation_time in evaluation_times:
        query = f"sum by (le) (increase({selector}[{policy['slo_query_window_days']}d]))"
        buckets = vector_bucket_counts(promql_query(policy, query, aws_cli, credential_source, timeout_seconds, evaluation_time, active_credentials))
        for bound, count in buckets.items():
            bucket_totals[bound] = bucket_totals.get(bound, 0.0) + count
    return percentile_from_cumulative_buckets(bucket_totals, percentile)


def validate_slo_segment_policy(policy: dict[str, Any], *slos: dict[str, Any]) -> None:
    """Require a complete exact partition of the selected rolling SLO windows into provider-safe queries."""

    window_days = policy["slo_query_window_days"]
    segment_count = policy["slo_query_segment_count"]
    if any(slo["rolling_window_days"] != window_days * segment_count for slo in slos):
        raise MetricCoverageError("the target SLO window must be an exact partition of the provider-safe query windows")


def slo_evaluation_times(policy: dict[str, Any]) -> list[datetime_module.datetime]:
    """Create contiguous seven-day evaluation boundaries without requesting more than one provider-safe range at once."""

    now = datetime_module.datetime.now(datetime_module.UTC)
    return [now - datetime_module.timedelta(days=policy["slo_query_window_days"] * offset) for offset in range(policy["slo_query_segment_count"])]


def segmented_counter_increase(policy: dict[str, Any], selector: str, aws_cli: str, credential_source: str, timeout_seconds: int, evaluation_times: list[datetime_module.datetime], active_credentials: dict[str, str]) -> float:
    """Sum adjacent provider-safe counter increases to evaluate the full declared rolling window."""

    total = 0.0
    for evaluation_time in evaluation_times:
        query = f"sum(increase({selector}[{policy['slo_query_window_days']}d]))"
        total += vector_number(promql_query(policy, query, aws_cli, credential_source, timeout_seconds, evaluation_time, active_credentials))
    return total


def percentile_from_cumulative_buckets(buckets: dict[float, float], percentile: float) -> float:
    """Calculate a Prometheus-style percentile from merged cumulative histogram bucket counts."""

    if not buckets or float("inf") not in buckets or buckets[float("inf")] <= 0:
        raise MetricCoverageError("the selected histogram has no eligible bucket observations")
    rank = percentile * buckets[float("inf")]
    previous_bound = 0.0
    previous_count = 0.0
    for bound in sorted(buckets):
        count = buckets[bound]
        if count < previous_count:
            raise MetricCoverageError("the selected histogram bucket counts are not cumulative")
        if count >= rank:
            if bound == float("inf"):
                return previous_bound
            if count == previous_count:
                return bound
            return previous_bound + ((bound - previous_bound) * ((rank - previous_count) / (count - previous_count)))
        previous_bound = bound
        previous_count = count
    raise MetricCoverageError("the selected histogram has no terminal bucket")


def percentile_result(slo: dict[str, Any], value: float) -> dict[str, Any]:
    """Classify one evaluated percentile against its fixed target-profile maximum."""

    objective = slo["objective"]
    maximum = objective.get("maximum_ms")
    if not isinstance(maximum, int):
        raise MetricCoverageError("the target profile percentile objective is malformed")
    return {"id": slo["id"], "state": "healthy" if value <= maximum else "breached", "value_ms": round(value, 3), "maximum_ms": maximum}


def insufficient_confidence_results(availability: dict[str, Any], p95: dict[str, Any], p99: dict[str, Any], eligible: float) -> list[dict[str, Any]]:
    """Return explicit evidence insufficiency instead of inferring health from a small population."""

    return [
        {"id": availability["id"], "state": EXPECTED_NON_OBSERVED_CONFIDENCE, "eligible_observations": round(eligible, 3), "minimum_eligible_observations": availability["minimum_observations"]},
        {"id": p95["id"], "state": EXPECTED_NON_OBSERVED_CONFIDENCE, "minimum_eligible_observations": p95["minimum_observations"]},
        {"id": p99["id"], "state": EXPECTED_NON_OBSERVED_CONFIDENCE, "minimum_eligible_observations": p99["minimum_observations"]},
    ]


def query_failed_results(availability: dict[str, Any], p95: dict[str, Any], p99: dict[str, Any]) -> list[dict[str, Any]]:
    """Avoid declaring metric-query failures as either healthy or breached SLOs."""

    return [{"id": entry["id"], "state": EXPECTED_NON_OBSERVED_CONFIDENCE, "reason": "query-failed"} for entry in (availability, p95, p99)]


def emit(payload: dict[str, Any]) -> None:
    """Emit one bounded JSON result with no provider response, credential, or request content."""

    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))


def main() -> int:
    """Validate policy offline or run exactly one selected safe observation operation."""

    arguments = parse_arguments()
    policy = resolve_policy(load_yaml(Path(arguments.target_profile)), arguments.coverage_target)
    if arguments.validate:
        payload: dict[str, str] = {"platform_shell_metric_coverage": "validated"}
        if policy["coverage_target"] == "worker":
            payload["coverage_target"] = "worker"
        emit(payload)
        return 0
    verify_account(policy, arguments.aws_cli, arguments.aws_credential_source, arguments.timeout_seconds)
    if arguments.mode == "slo":
        results = evaluate_slos(policy, arguments.aws_cli, arguments.aws_credential_source, arguments.timeout_seconds)
        emit({"platform_shell_slos": results})
        return 0 if all(result["state"] != "insufficient-confidence" for result in results) else 1
    verdict = coverage_verdict(policy, arguments.aws_cli, arguments.aws_credential_source, arguments.timeout_seconds)
    if verdict != "observed" and arguments.notify_on_non_observed:
        verdict = verdict if notify(policy, verdict, arguments.aws_cli, arguments.aws_credential_source, arguments.timeout_seconds) else "notification-failed"
    if policy["coverage_target"] == "worker":
        emit({"metric_coverage": verdict, "worker_metric_observation": policy["coverage_id"]})
        return 0 if verdict == "observed" else 1
    confidence = "not-determined" if verdict == "observed" else EXPECTED_NON_OBSERVED_CONFIDENCE
    emit({"affected_slo_confidence": confidence, "metric_coverage": verdict})
    return 0 if verdict == "observed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MetricCoverageError as exception:
        print(f"metric-coverage: {exception}", file=sys.stderr)
        raise SystemExit(1)
