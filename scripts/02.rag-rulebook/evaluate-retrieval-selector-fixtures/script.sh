#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.evaluate-retrieval-selector-fixtures
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Evaluate retrieval selector fixtures against generated context packets.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.standard.retrieval-selector-evaluations
#       path: .agentic/02.rag-rulebook/standards/retrieval-selector-evaluations.md
#     - id: rag-rulebook.script.evaluate-retrieval-selector-fixtures.readme
#       path: scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/README.md
#     - id: rag-rulebook.script.evaluate-retrieval-selector-fixtures.smoke-test
#       path: scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/smoke-test.sh

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: python3 yaml module is required for selector fixture evaluation.", file=sys.stderr)
    sys.exit(2)


EVALUATION_SCHEMA = "rag-rulebook/retrieval-selector-evaluation/v1"
DEFAULT_FIXTURE_ROOT = ".agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures"
CHUNK_GENERATOR_SCRIPT = "scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh"
SELECTOR_FIXTURE_SCRIPT = "scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh"


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return Path(result.stdout.strip())


ROOT = repo_root()


def usage() -> str:
    return """Usage:
  evaluate-retrieval-selector-fixtures/script.sh --current [--json]
  evaluate-retrieval-selector-fixtures/script.sh --fixture <path> [--fixture <path> ...] [--json]

Runs retrieval selector evaluation fixtures against generated selector packets.
The command is read-only.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--fixture", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.fixture):
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def list_fixtures(args: argparse.Namespace) -> list[Path]:
    if args.current:
        root = repo_path(DEFAULT_FIXTURE_ROOT)
        return sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml"))
    return [repo_path(path) for path in args.fixture]


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"fixture must contain a YAML object: {rel(path)}")
    return data


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def dict_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def run_current_chunks(chunks_path: Path) -> None:
    with chunks_path.open("w", encoding="utf-8") as handle:
        subprocess.run(
            ["bash", CHUNK_GENERATOR_SCRIPT, "--generate-current"],
            check=True,
            text=True,
            stdout=handle,
        )


def run_selector_fixture(fixture: dict[str, Any], chunks_path: Path) -> dict[str, Any]:
    input_data = dict_value(fixture.get("input"))
    session = dict_value(input_data.get("session"))
    command = [
        "bash",
        SELECTOR_FIXTURE_SCRIPT,
        "--chunks",
        str(chunks_path),
        "--request-text",
        str(input_data.get("request_text") or ""),
        "--session-id",
        str(session.get("id") or fixture.get("id") or "retrieval-selector-evaluation"),
        "--session-branch",
        str(session.get("branch") or "chat/retrieval-selector-evaluation"),
        "--session-worktree",
        str(session.get("worktree") or "/tmp/retrieval-selector-evaluation"),
        "--session-layer",
        str(session.get("layer") or "02.rag-rulebook"),
        "--session-mode",
        str(session.get("mode") or "implementation"),
        "--session-workflow",
        str(session.get("workflow") or ".agentic/02.rag-rulebook/workflows/default.md"),
        "--max-chunks",
        str(input_data.get("max_chunks") or 6),
    ]
    if session.get("trust_routing") is True:
        command.append("--trust-session-routing")
    if input_data.get("no_focused_paths") is True:
        command.append("--no-focused-paths")
    else:
        for path in list_of_strings(input_data.get("focused_paths")):
            command.extend(["--focused-path", path])
    result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
    packet = json.loads(result.stdout)
    if not isinstance(packet, dict):
        raise ValueError("selector fixture did not emit a JSON object")
    return packet


def packet_sets(packet: dict[str, Any]) -> dict[str, set[str]]:
    recognition_matches = recognition_source_matches(packet)
    trace_stages = selector_trace_stages(packet)
    return {
        "matched_corpora": {
            item.get("corpus_id")
            for item in packet.get("matched_corpora", [])
            if isinstance(item, dict) and isinstance(item.get("corpus_id"), str)
        },
        "selected_corpora": {
            item.get("corpus_id")
            for item in packet.get("selected_chunks", [])
            if isinstance(item, dict) and isinstance(item.get("corpus_id"), str)
        },
        "selected_content_kinds": {
            item.get("content_kind")
            for item in packet.get("selected_chunks", [])
            if isinstance(item, dict) and isinstance(item.get("content_kind"), str)
        },
        "selected_artifact_ids": {
            item.get("artifact_id")
            for item in packet.get("selected_chunks", [])
            if isinstance(item, dict) and isinstance(item.get("artifact_id"), str)
        },
        "selected_chunk_ids": {
            item.get("chunk_id")
            for item in packet.get("selected_chunks", [])
            if isinstance(item, dict) and isinstance(item.get("chunk_id"), str)
        },
        "selected_rule_ids": {
            rule_id
            for item in packet.get("selected_chunks", [])
            if isinstance(item, dict)
            for rule_id in list_of_strings(item.get("rule_ids"))
        },
        "gap_ids": {
            item.get("id")
            for item in packet.get("gaps", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        },
        "gap_evidence_chunk_ids": {
            chunk_id
            for item in packet.get("gaps", [])
            if isinstance(item, dict)
            for chunk_id in list_of_strings(item.get("required_evidence_chunk_ids"))
        },
        "gap_citation_ids": {
            citation_id
            for item in packet.get("gaps", [])
            if isinstance(item, dict)
            for citation_id in list_of_strings(item.get("citation_ids"))
        },
        "blocking_gap_ids": {
            item.get("id")
            for item in packet.get("gaps", [])
            if isinstance(item, dict) and item.get("blocking") is True and isinstance(item.get("id"), str)
        },
        "recognition_source_ids": {
            item.get("source_id")
            for item in recognition_matches
            if isinstance(item.get("source_id"), str)
        },
        "recognition_matched_inputs": {
            item.get("matched_input")
            for item in recognition_matches
            if isinstance(item.get("matched_input"), str)
        },
        "recognition_categories": {
            item.get("category")
            for item in recognition_matches
            if isinstance(item.get("category"), str)
        },
        "recognition_canonical_ids": {
            item.get("canonical_id")
            for item in recognition_matches
            if isinstance(item.get("canonical_id"), str)
        },
        "selector_trace_stage_ids": {
            item.get("stage_id")
            for item in trace_stages
            if isinstance(item.get("stage_id"), str)
        },
        "selector_trace_applied_stage_ids": {
            item.get("stage_id")
            for item in trace_stages
            if isinstance(item.get("stage_id"), str) and item.get("status") == "applied"
        },
    }


def require_contains(owner: str, actual: set[str], expected: list[str], errors: list[str]) -> None:
    for item in expected:
        if item not in actual:
            errors.append(f"{owner} missing required value: {item}")


def require_absent(owner: str, actual: set[str], banned: list[str], errors: list[str]) -> None:
    for item in banned:
        if item in actual:
            errors.append(f"{owner} contains banned value: {item}")


RECOGNITION_MATCH_KEYS = {
    "source_id",
    "term",
    "category",
    "canonical_id",
    "matched_input",
    "match_type",
}


def recognition_source_matches(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in packet.get("request", {}).get("recognition_source_matches", [])
        if isinstance(item, dict)
    ]


def selector_trace_stages(packet: dict[str, Any]) -> list[dict[str, Any]]:
    selector_trace = packet.get("selector_trace")
    if not isinstance(selector_trace, dict):
        return []
    return [
        item
        for item in selector_trace.get("stages", [])
        if isinstance(item, dict)
    ]


def match_spec_errors(owner: str, spec: dict[str, Any]) -> list[str]:
    errors = []
    unsupported = sorted(set(spec) - RECOGNITION_MATCH_KEYS)
    for key in unsupported:
        errors.append(f"{owner} has unsupported recognition match key: {key}")
    for key, value in spec.items():
        if key in RECOGNITION_MATCH_KEYS and not isinstance(value, str):
            errors.append(f"{owner}.{key} must be a string")
    return errors


def recognition_match_satisfies(match: dict[str, Any], spec: dict[str, Any]) -> bool:
    for key in RECOGNITION_MATCH_KEYS:
        if key in spec and match.get(key) != spec[key]:
            return False
    return True


def describe_match_spec(spec: dict[str, Any]) -> str:
    return ", ".join(f"{key}={spec[key]!r}" for key in sorted(spec) if key in RECOGNITION_MATCH_KEYS)


def require_recognition_matches(
    owner: str,
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    errors: list[str],
) -> None:
    for index, spec in enumerate(expected, start=1):
        spec_owner = f"{owner}[{index}]"
        errors.extend(match_spec_errors(spec_owner, spec))
        if any(key not in RECOGNITION_MATCH_KEYS for key in spec):
            continue
        if not any(recognition_match_satisfies(match, spec) for match in actual):
            errors.append(f"{spec_owner} missing required recognition match: {describe_match_spec(spec)}")


def require_no_recognition_matches(
    owner: str,
    actual: list[dict[str, Any]],
    banned: list[dict[str, Any]],
    errors: list[str],
) -> None:
    for index, spec in enumerate(banned, start=1):
        spec_owner = f"{owner}[{index}]"
        errors.extend(match_spec_errors(spec_owner, spec))
        if any(key not in RECOGNITION_MATCH_KEYS for key in spec):
            continue
        if any(recognition_match_satisfies(match, spec) for match in actual):
            errors.append(f"{spec_owner} contains banned recognition match: {describe_match_spec(spec)}")


def compare_routing(packet: dict[str, Any], expected: dict[str, Any], errors: list[str]) -> None:
    routing = dict_value(packet.get("routing"))
    for field, expected_value in expected.items():
        if routing.get(field) != expected_value:
            errors.append(f"routing.{field} expected {expected_value!r}, got {routing.get(field)!r}")


def compare_object_fields(owner: str, actual: dict[str, Any], expected: dict[str, Any], errors: list[str]) -> None:
    for field, expected_value in expected.items():
        actual_value = actual.get(field)
        if isinstance(expected_value, list):
            if not isinstance(actual_value, list):
                errors.append(f"{owner}.{field} expected a list, got {actual_value!r}")
                continue
            for item in expected_value:
                if item not in actual_value:
                    errors.append(f"{owner}.{field} missing required value: {item}")
        elif actual_value != expected_value:
            errors.append(f"{owner}.{field} expected {expected_value!r}, got {actual_value!r}")


def compare_confidence(packet: dict[str, Any], expected: dict[str, Any], errors: list[str]) -> None:
    confidence = dict_value(packet.get("confidence"))
    for key, value in expected.items():
        if key.startswith("max_"):
            field = key.removeprefix("max_")
            actual = confidence.get(field)
            if not isinstance(actual, (int, float)) or actual > value:
                errors.append(f"confidence.{field} expected <= {value}, got {actual}")
        if key.startswith("min_"):
            field = key.removeprefix("min_")
            actual = confidence.get(field)
            if not isinstance(actual, (int, float)) or actual < value:
                errors.append(f"confidence.{field} expected >= {value}, got {actual}")


def evaluate_fixture(path: Path, fixture: dict[str, Any], chunks_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    fixture_id = fixture.get("fixture_id") if isinstance(fixture.get("fixture_id"), str) else rel(path)

    if fixture.get("schema") != EVALUATION_SCHEMA:
        errors.append(f"schema must be {EVALUATION_SCHEMA}")
    if fixture.get("status") != "active":
        warnings.append(f"fixture status is not active: {fixture.get('status')}")
    if not dict_value(fixture.get("input")).get("request_text"):
        errors.append("input.request_text is required")
        return {
            "fixture_id": fixture_id,
            "path": rel(path),
            "ok": False,
            "errors": errors,
            "warnings": warnings,
        }

    try:
        packet = run_selector_fixture(fixture, chunks_path)
    except Exception as exc:
        errors.append(f"selector fixture command failed: {exc}")
        return {
            "fixture_id": fixture_id,
            "path": rel(path),
            "ok": False,
            "errors": errors,
            "warnings": warnings,
        }

    sets = packet_sets(packet)
    expected = dict_value(fixture.get("expected"))
    banned = dict_value(fixture.get("banned"))

    compare_routing(packet, dict_value(expected.get("routing")), errors)
    compare_object_fields("intent", dict_value(packet.get("intent")), dict_value(expected.get("intent")), errors)
    compare_object_fields(
        "action_authorization",
        dict_value(packet.get("action_authorization")),
        dict_value(expected.get("action_authorization")),
        errors,
    )
    require_contains(
        "matched_corpora",
        sets["matched_corpora"],
        list_of_strings(dict_value(expected.get("matched_corpora")).get("required")),
        errors,
    )
    require_absent(
        "matched_corpora",
        sets["matched_corpora"],
        list_of_strings(banned.get("matched_corpora")),
        errors,
    )
    require_contains(
        "selected_corpora",
        sets["selected_corpora"],
        list_of_strings(dict_value(expected.get("selected_corpora")).get("required")),
        errors,
    )
    require_absent(
        "selected_corpora",
        sets["selected_corpora"],
        list_of_strings(banned.get("selected_corpora")),
        errors,
    )
    require_contains(
        "selected_content_kinds",
        sets["selected_content_kinds"],
        list_of_strings(dict_value(expected.get("selected_content_kinds")).get("required")),
        errors,
    )

    recognition = dict_value(expected.get("recognition"))
    recognition_matches = recognition_source_matches(packet)
    require_contains(
        "recognition_source_ids",
        sets["recognition_source_ids"],
        list_of_strings(recognition.get("required_source_ids")),
        errors,
    )
    require_contains(
        "recognition_matched_inputs",
        sets["recognition_matched_inputs"],
        list_of_strings(recognition.get("required_matched_inputs")),
        errors,
    )
    require_absent(
        "recognition_matched_inputs",
        sets["recognition_matched_inputs"],
        list_of_strings(recognition.get("banned_matched_inputs")),
        errors,
    )
    require_contains(
        "recognition_categories",
        sets["recognition_categories"],
        list_of_strings(recognition.get("required_categories")),
        errors,
    )
    require_contains(
        "recognition_canonical_ids",
        sets["recognition_canonical_ids"],
        list_of_strings(recognition.get("required_canonical_ids")),
        errors,
    )
    require_recognition_matches(
        "recognition.required_matches",
        recognition_matches,
        list_of_dicts(recognition.get("required_matches")),
        errors,
    )
    require_no_recognition_matches(
        "banned.recognition_matches",
        recognition_matches,
        list_of_dicts(banned.get("recognition_matches")),
        errors,
    )

    selected_chunks = dict_value(expected.get("selected_chunks"))
    require_contains(
        "selected_artifact_ids",
        sets["selected_artifact_ids"],
        list_of_strings(selected_chunks.get("required_artifact_ids")),
        errors,
    )
    require_contains(
        "selected_chunk_ids",
        sets["selected_chunk_ids"],
        list_of_strings(selected_chunks.get("required_chunk_ids")),
        errors,
    )
    require_contains(
        "selected_rule_ids",
        sets["selected_rule_ids"],
        list_of_strings(selected_chunks.get("required_rule_ids")),
        errors,
    )

    selector_trace = dict_value(expected.get("selector_trace"))
    compare_object_fields(
        "selector_trace",
        dict_value(packet.get("selector_trace")),
        {key: value for key, value in selector_trace.items() if key in {"strategy_id"}},
        errors,
    )
    require_contains(
        "selector_trace.stage_ids",
        sets["selector_trace_stage_ids"],
        list_of_strings(selector_trace.get("required_stage_ids")),
        errors,
    )
    require_contains(
        "selector_trace.applied_stage_ids",
        sets["selector_trace_applied_stage_ids"],
        list_of_strings(selector_trace.get("required_applied_stage_ids")),
        errors,
    )

    gaps = dict_value(expected.get("gaps"))
    required_gaps = list_of_strings(gaps.get("required"))
    required_blocking_gaps = list_of_strings(gaps.get("blocking_required"))
    allowed_gaps = set(required_gaps + list_of_strings(gaps.get("allowed")))
    allowed_gaps.update(required_blocking_gaps)
    require_contains("gaps", sets["gap_ids"], required_gaps, errors)
    require_contains("blocking_gaps", sets["blocking_gap_ids"], required_blocking_gaps, errors)
    require_contains(
        "gap_evidence_chunk_ids",
        sets["gap_evidence_chunk_ids"],
        list_of_strings(gaps.get("required_evidence_chunk_ids")),
        errors,
    )
    require_contains(
        "gap_citation_ids",
        sets["gap_citation_ids"],
        list_of_strings(gaps.get("required_citation_ids")),
        errors,
    )
    if gaps.get("no_unexpected") is True:
        unexpected = sorted(sets["gap_ids"] - allowed_gaps)
        for gap_id in unexpected:
            errors.append(f"gaps contains unexpected value: {gap_id}")
    require_absent("blocking_gaps", sets["blocking_gap_ids"], list_of_strings(banned.get("blocking_gaps")), errors)
    require_absent("gaps", sets["gap_ids"], list_of_strings(banned.get("gaps")), errors)
    require_absent("selected_rule_ids", sets["selected_rule_ids"], list_of_strings(banned.get("selected_rule_ids")), errors)

    checks = dict_value(expected.get("required_checks"))
    min_checks = checks.get("min_count")
    if isinstance(min_checks, int) and len(packet.get("required_checks", [])) < min_checks:
        errors.append(f"required_checks expected at least {min_checks}, got {len(packet.get('required_checks', []))}")

    citations = dict_value(expected.get("citations"))
    min_citations = citations.get("min_count")
    if isinstance(min_citations, int) and len(packet.get("citations", [])) < min_citations:
        errors.append(f"citations expected at least {min_citations}, got {len(packet.get('citations', []))}")

    compare_confidence(packet, dict_value(expected.get("confidence")), errors)

    return {
        "fixture_id": fixture_id,
        "path": rel(path),
        "ok": not errors,
        "packet_id": packet.get("packet_id"),
        "routing": packet.get("routing"),
        "counts": {
            "matched_corpora": len(sets["matched_corpora"]),
            "selected_chunks": len(packet.get("selected_chunks", [])),
            "gaps": len(sets["gap_ids"]),
            "recognition_matches": len(packet.get("request", {}).get("recognition_source_matches", [])),
        },
        "errors": errors,
        "warnings": warnings,
    }


def print_human_report(report: dict[str, Any]) -> None:
    if report["ok"]:
        print(f"Retrieval selector evaluation fixtures passed: {report['counts']['passed']}/{report['counts']['fixtures']}")
    else:
        print(f"Retrieval selector evaluation fixtures failed: {report['counts']['failed']}/{report['counts']['fixtures']}")
    for item in report["fixtures"]:
        status = "ok" if item["ok"] else "failed"
        print(f"- {status}: {item['fixture_id']}")
        for error in item.get("errors", []):
            print(f"  ERROR: {error}")
        for warning in item.get("warnings", []):
            print(f"  WARN: {warning}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    fixtures = list_fixtures(args)
    if not fixtures:
        print("ERROR: no evaluation fixtures found.", file=sys.stderr)
        return 1

    results: list[dict[str, Any]] = []
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as chunks_handle:
        chunks_path = Path(chunks_handle.name)
        run_current_chunks(chunks_path)
        chunks_handle.flush()
        for path in fixtures:
            try:
                fixture = load_yaml(path)
                results.append(evaluate_fixture(path, fixture, chunks_path))
            except Exception as exc:
                results.append(
                    {
                        "fixture_id": rel(path),
                        "path": rel(path),
                        "ok": False,
                        "errors": [str(exc)],
                        "warnings": [],
                    }
                )

    passed = sum(1 for item in results if item["ok"])
    report = {
        "ok": passed == len(results),
        "schema": EVALUATION_SCHEMA,
        "counts": {
            "fixtures": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "fixtures": results,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
