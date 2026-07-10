#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.report-artifact-retrieval-profile-coverage
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: retrieval
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Report deterministic retrieval-profile coverage for indexed artifact metadata without modifying files.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.plan.artifact-metadata-retrieval-profile-migration
#       path: .agentic/02.rag-rulebook/plans/artifact-metadata-retrieval-profile-migration.md
#     - id: rag-rulebook.script.report-artifact-retrieval-profile-coverage.readme
#       path: scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/README.md
#     - id: rag-rulebook.script.report-artifact-retrieval-profile-coverage.smoke-test
#       path: scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/smoke-test.sh
#     - id: rag-rulebook.evaluation.retrieval-profile-coverage.llm-audit-2026-07-10
#       path: .agentic/02.rag-rulebook/evaluations/retrieval-profile-coverage/2026-07-10-llm-audit.md

python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPORT_SCHEMA = "rag-rulebook/artifact-retrieval-profile-coverage-report/v1"
INDEX_GENERATOR = "scripts/01.harness/artifact-metadata/generate-index/script.sh"
REQUIRED_IDENTITY_FIELDS = ["id", "layer", "domain", "kind", "purpose", "disciplines", "portability", "used_by"]
README_KINDS = {
    "capability-readme",
    "corpus-readme",
    "layer-readme",
    "readme",
    "rulebook-readme",
    "script-domain-readme",
    "script-layer-readme",
    "skill-index",
    "source-material-readme",
    "source-projection-registry",
    "workflow-index",
}
KIND_CONTRACTS = {
    "checklist": ("review checklist", "checklist review expectations"),
    "corpus-gap": ("corpus coverage gap record", "corpus gap tracking expectations"),
    "doc": ("governed documentation artifact", "documentation accuracy expectations"),
    "example": ("worked example artifact", "example conformance expectations"),
    "index": ("artifact family index", "index navigation expectations"),
    "layer-ruleset": ("layer rule contract", "layer rule expectations"),
    "migration-plan": ("migration tracking plan", "migration progress expectations"),
    "plan": ("implementation or migration plan", "plan tracking expectations"),
    "prompt": ("reusable prompt contract", "prompt usage expectations"),
    "retirement-record": ("artifact retirement record", "retirement decision expectations"),
    "review-record": ("review evidence record", "review evidence expectations"),
    "rule-pack": ("governed rule pack", "rule pack expectations"),
    "ruleset": ("governed ruleset", "ruleset expectations"),
    "skill": ("reusable model procedure", "skill execution expectations"),
    "state": ("governed state record", "state tracking expectations"),
}


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
  report-artifact-retrieval-profile-coverage/script.sh --current [--json|--pretty]
  report-artifact-retrieval-profile-coverage/script.sh --index <path> [--json|--pretty]

Reads an agentic artifact metadata index and reports whether each indexed
artifact has enough deterministic metadata to derive retrieval-profile signals.
The command is read-only and does not inspect source bodies beyond the
metadata already captured in the index.
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--current", action="store_true")
    parser.add_argument("--index")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        print(usage(), end="")
        sys.exit(0)
    if args.current == bool(args.index):
        print("ERROR: choose exactly one input mode.", file=sys.stderr)
        print(usage(), end="", file=sys.stderr)
        sys.exit(2)
    return args


def repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else ROOT / path_obj


def run_current_index() -> dict[str, Any]:
    result = subprocess.run(
        ["bash", INDEX_GENERATOR, "--all", "--pretty", "--strict"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return load_json(result.stdout, "generated artifact metadata index")


def load_json(raw: str, label: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: {label} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"ERROR: {label} must be a JSON object.")
    return data


def load_index(args: argparse.Namespace) -> dict[str, Any]:
    if args.current:
        return run_current_index()
    return load_json(repo_path(args.index).read_text(encoding="utf-8"), f"artifact metadata index {args.index}")


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


def slug(value: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return cleaned or "unknown"


def words(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def used_by_paths(artifact: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for entry in list_of_dicts(artifact.get("used_by")):
        path = entry.get("path")
        if isinstance(path, str) and path not in paths:
            paths.append(path)
    return paths


def command_name(path: str) -> str:
    path_obj = Path(path)
    if path_obj.name in {"script.sh", "script.js", "script.mjs", "smoke-test.sh"} and path_obj.parent.name:
        return path_obj.parent.name
    return path_obj.stem


def infer_action_terms(artifact: dict[str, Any]) -> set[str]:
    path = str(artifact.get("path") or "")
    purpose = str(artifact.get("purpose") or "")
    artifact_id = str(artifact.get("id") or "")
    command = command_name(path)
    combined = words(" ".join([path, purpose, artifact_id, command]))

    aliases = {
        "check": {"check", "checks", "verify", "verifies", "audit", "audits"},
        "validate": {"validate", "validates", "validator", "validation"},
        "generate": {"generate", "generates", "generator", "emit", "emits", "create", "creates", "build", "builds"},
        "compile": {"compile", "compiles", "compiler"},
        "query": {"query", "queries"},
        "report": {"report", "reports"},
        "record": {"record", "records"},
        "serve": {"serve", "serves", "server", "service", "http"},
        "smoke-test": {"smoke", "test", "tests"},
        "deploy": {"deploy", "deployment"},
        "review": {"review", "reviews"},
        "rule": {"rule", "rules"},
        "index": {"index", "indexed", "indexing"},
        "chunk": {"chunk", "chunks", "chunking"},
    }

    terms: set[str] = set()
    for action, variants in aliases.items():
        if combined.intersection(variants):
            terms.add(action)
    return terms


def infer_roles(artifact: dict[str, Any], actions: set[str]) -> list[str]:
    roles: list[str] = []
    layer = str(artifact.get("layer") or "")
    domain = str(artifact.get("domain") or "")
    kind = str(artifact.get("kind") or "")
    status = str(artifact.get("status") or "")
    path = str(artifact.get("path") or "")

    add_unique(roles, f"layer.{layer}" if layer else "")
    add_unique(roles, f"domain.{slug(domain)}" if domain else "")
    add_unique(roles, f"kind.{slug(kind)}" if kind else "")
    add_unique(roles, f"status.{slug(status)}" if status else "")
    for discipline in list_of_strings(artifact.get("disciplines")):
        add_unique(roles, f"discipline.{slug(discipline)}")

    if kind == "script" or path.startswith("scripts/"):
        add_unique(roles, "artifact.script")
        for action in sorted(actions):
            add_unique(roles, f"script.{action}")
    elif kind:
        add_unique(roles, f"artifact.{slug(kind)}")

    if path.startswith(".github/workflows/"):
        add_unique(roles, "ci.workflow")
    if path.startswith("infra/"):
        add_unique(roles, "infra.artifact")
    if "/evaluations/" in path or kind == "evaluation-fixture":
        add_unique(roles, "retrieval.evaluation")
    if "recognition-source" in kind or "/recognition-sources/" in path:
        add_unique(roles, "retrieval.recognition-source")
    if "policy" in kind or "/policies/" in path:
        add_unique(roles, "retrieval.policy")
    if "schema" in kind or "/schemas/" in path:
        add_unique(roles, "contract.schema")
    return roles


def infer_answers(artifact: dict[str, Any], roles: list[str]) -> list[str]:
    answers: list[str] = []
    purpose = str(artifact.get("purpose") or "").strip()
    domain = str(artifact.get("domain") or "").strip()
    kind = str(artifact.get("kind") or "").strip()
    path = str(artifact.get("path") or "").strip()

    if purpose:
        add_unique(answers, purpose)
    if domain and kind:
        add_unique(answers, f"how {domain} {kind} artifacts are governed")
    if "artifact.script" in roles:
        add_unique(answers, f"how the {command_name(path)} command works")
    return answers


def infer_produces(artifact: dict[str, Any], actions: set[str]) -> list[str]:
    produces: list[str] = []
    kind = str(artifact.get("kind") or "")
    purpose = str(artifact.get("purpose") or "").lower()
    path = str(artifact.get("path") or "")
    command = command_name(path)

    if "generate" in actions:
        add_unique(produces, f"generated output from {command}")
    if "compile" in actions:
        add_unique(produces, f"compiled output from {command}")
    if "report" in actions:
        add_unique(produces, f"diagnostic report from {command}")
    if "query" in actions:
        add_unique(produces, "context packet or query result")
    if "record" in actions:
        add_unique(produces, "governed record")
    if "serve" in actions:
        add_unique(produces, f"service runtime from {command}")
    if "build" in words(purpose) or "runtime cache" in purpose:
        add_unique(produces, "runtime artifact")
    if kind in {"schema", "standard", "policy", "policy-dimension", "rule", "workflow", "guide"}:
        add_unique(produces, f"governed {kind} contract")
    if kind == "template":
        add_unique(produces, "reusable template contract")
    if kind == "config":
        add_unique(produces, "machine-readable configuration contract")
    if kind == "rubric":
        add_unique(produces, "review scoring rubric")
    if kind in README_KINDS:
        add_unique(produces, "governed navigation and ownership guide")
    if kind == "adr":
        add_unique(produces, "architecture decision record")
    if kind == "agent":
        add_unique(produces, "agent role contract")
    if kind == "recognition-source":
        add_unique(produces, "recognition vocabulary source")
    if kind == "source-material":
        add_unique(produces, "source coverage for rule derivation")
    contract = KIND_CONTRACTS.get(kind)
    if contract:
        add_unique(produces, contract[0])
    return produces


def infer_consumes(artifact: dict[str, Any], actions: set[str]) -> list[str]:
    consumes: list[str] = []
    path = str(artifact.get("path") or "")
    used_paths = used_by_paths(artifact)
    kind = str(artifact.get("kind") or "")

    if path.startswith("scripts/"):
        add_unique(consumes, "command-line arguments")
    if actions.intersection({"check", "validate", "generate", "compile", "report", "query", "serve"}):
        add_unique(consumes, "governed repo inputs")
    if "index" in actions:
        add_unique(consumes, "artifact or rulebook index inputs")
    if "chunk" in actions:
        add_unique(consumes, "indexed chunk candidates")
    if kind in {"rule", "policy-dimension", "workflow"}:
        add_unique(consumes, "agent request context")
    for used_path in used_paths[:5]:
        add_unique(consumes, f"referenced by {used_path}")
    return consumes


def infer_validates(artifact: dict[str, Any], actions: set[str]) -> list[str]:
    validates: list[str] = []
    kind = str(artifact.get("kind") or "")
    path = str(artifact.get("path") or "")
    command = command_name(path)

    if actions.intersection({"check", "validate", "smoke-test"}):
        add_unique(validates, f"{command} expectations")
    if "serve" in actions:
        add_unique(validates, "service request and runtime boundaries")
    if kind in {"schema", "standard"}:
        add_unique(validates, f"{kind} conformance")
    if kind == "template":
        add_unique(validates, "template instance expectations")
    if kind == "config":
        add_unique(validates, "configuration contract expectations")
    if kind == "rubric":
        add_unique(validates, "review scoring expectations")
    if kind in README_KINDS:
        add_unique(validates, "repository navigation and ownership expectations")
    if kind == "adr":
        add_unique(validates, "architecture decision rationale")
    if kind == "agent":
        add_unique(validates, "agent responsibility boundaries")
    if kind == "recognition-source":
        add_unique(validates, "recognition term mapping expectations")
    if kind == "source-material":
        add_unique(validates, "source-to-rule coverage expectations")
    contract = KIND_CONTRACTS.get(kind)
    if contract:
        add_unique(validates, contract[1])
    if kind == "evaluation-fixture":
        add_unique(validates, "retrieval selector behavior")
    return validates


def missing_identity_fields(artifact: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_IDENTITY_FIELDS:
        value = artifact.get(field)
        if field in {"disciplines", "used_by"}:
            if not isinstance(value, list) or not value:
                missing.append(field)
        elif field == "portability":
            if not isinstance(value, dict) or not value.get("class"):
                missing.append(field)
        elif not value:
            missing.append(field)
    return missing


def specific_roles(roles: list[str]) -> list[str]:
    generic_prefixes = ("layer.", "domain.", "kind.", "status.", "discipline.")
    return [role for role in roles if not role.startswith(generic_prefixes)]


def suggested_repairs(
    artifact: dict[str, Any],
    missing_identity: list[str],
    roles: list[str],
    produces: list[str],
    consumes: list[str],
    validates: list[str],
) -> list[dict[str, str]]:
    repairs: list[dict[str, str]] = []
    if missing_identity:
        repairs.append(
            {
                "source": "header",
                "reason": "Required identity metadata is missing: " + ", ".join(missing_identity),
            }
        )
    if not specific_roles(roles):
        repairs.append(
            {
                "source": "generator-rule",
                "reason": "No specific retrieval role can be inferred from kind, path, purpose, or action terms.",
            }
        )
    if not (produces or consumes or validates):
        repairs.append(
            {
                "source": "generator-rule",
                "reason": "No process capability can be inferred without reading the artifact body.",
            }
        )
    if str(artifact.get("kind") or "") == "script" and not artifact.get("effects"):
        repairs.append(
            {
                "source": "header",
                "reason": "Script artifact lacks explicit effects metadata.",
            }
        )
    if not repairs:
        repairs.append(
            {
                "source": "none",
                "reason": "Current metadata is sufficient for deterministic profile derivation.",
            }
        )
    return repairs


def classify(
    artifact: dict[str, Any],
    missing_identity: list[str],
    roles: list[str],
    produces: list[str],
    consumes: list[str],
    validates: list[str],
) -> tuple[str, float]:
    if artifact.get("status") == "deprecated":
        return "excluded", 0.2

    process_groups = sum(1 for group in [produces, consumes, validates, artifact.get("effects"), used_by_paths(artifact)] if group)
    has_specific_role = bool(specific_roles(roles))

    score = 0.25
    if not missing_identity:
        score += 0.2
    if has_specific_role:
        score += 0.15
    score += min(0.3, process_groups * 0.075)
    if dict_value(artifact.get("portability")).get("class"):
        score += 0.05
    confidence = round(min(score, 0.95), 3)

    if missing_identity:
        return "weak", confidence
    if has_specific_role and process_groups >= 3:
        return "strong", confidence
    if has_specific_role or process_groups >= 1:
        return "partial", confidence
    return "weak", confidence


def coverage_record(artifact: dict[str, Any]) -> dict[str, Any]:
    actions = infer_action_terms(artifact)
    roles = infer_roles(artifact, actions)
    answers = infer_answers(artifact, roles)
    produces = infer_produces(artifact, actions)
    consumes = infer_consumes(artifact, actions)
    validates = infer_validates(artifact, actions)
    missing_identity = missing_identity_fields(artifact)
    status, confidence = classify(artifact, missing_identity, roles, produces, consumes, validates)
    repairs = suggested_repairs(artifact, missing_identity, roles, produces, consumes, validates)
    if status == "partial" and all(repair.get("source") == "none" for repair in repairs):
        repairs = [
            {
                "source": "generator-rule",
                "reason": "Metadata is identity-safe, but deterministic profile derivation needs richer process-role rules for this artifact shape.",
            }
        ]

    return {
        "artifact_id": artifact.get("id") or artifact.get("provisional_id"),
        "path": artifact.get("path"),
        "layer": artifact.get("layer"),
        "domain": artifact.get("domain"),
        "kind": artifact.get("kind"),
        "status": artifact.get("status"),
        "purpose": artifact.get("purpose"),
        "coverage": status,
        "confidence": confidence,
        "retrieval_roles": roles,
        "specific_roles": specific_roles(roles),
        "answers_questions_about": answers,
        "produces": produces,
        "consumes": consumes,
        "validates": validates,
        "missing_signals": missing_identity,
        "repair_suggestions": repairs,
    }


def build_report(index: dict[str, Any]) -> dict[str, Any]:
    if index.get("schema") != "agentic-artifact-index/v1":
        raise SystemExit("ERROR: index schema must be agentic-artifact-index/v1.")

    artifacts = list_of_dicts(index.get("artifacts"))
    records = [coverage_record(artifact) for artifact in artifacts]
    status_counts = Counter(record["coverage"] for record in records)
    repair_counts = Counter(
        repair["source"]
        for record in records
        for repair in list_of_dicts(record.get("repair_suggestions"))
    )
    by_layer: dict[str, Counter[str]] = defaultdict(Counter)
    by_kind: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        by_layer[str(record.get("layer") or "unknown")][record["coverage"]] += 1
        by_kind[str(record.get("kind") or "unknown")][record["coverage"]] += 1

    return {
        "schema": REPORT_SCHEMA,
        "ok": True,
        "root": str(ROOT),
        "source_index": {
            "schema": index.get("schema"),
            "generated_at": index.get("generated_at"),
            "git_commit": index.get("git_commit"),
            "summary": index.get("summary"),
        },
        "counts": {
            "artifacts": len(records),
            "coverage": dict(sorted(status_counts.items())),
            "repair_sources": dict(sorted(repair_counts.items())),
            "by_layer": {layer: dict(sorted(counts.items())) for layer, counts in sorted(by_layer.items())},
            "top_kinds": {
                kind: dict(sorted(counts.items()))
                for kind, counts in sorted(by_kind.items(), key=lambda item: (-sum(item[1].values()), item[0]))[:20]
            },
        },
        "records": sorted(records, key=lambda item: (item["coverage"], str(item.get("path") or ""))),
    }


def print_text(report: dict[str, Any]) -> None:
    counts = report["counts"]
    print(f"Artifact retrieval profile coverage report: {counts['artifacts']} artifact(s).")
    print("Coverage:")
    for status, count in counts["coverage"].items():
        print(f"  - {status}: {count}")
    print("Repair sources:")
    for source, count in counts["repair_sources"].items():
        print(f"  - {source}: {count}")
    print("By layer:")
    for layer, layer_counts in counts["by_layer"].items():
        compact = ", ".join(f"{status}={count}" for status, count in layer_counts.items())
        print(f"  - {layer}: {compact}")

    attention = [
        record
        for record in report["records"]
        if record["coverage"] in {"weak", "partial"}
    ][:20]
    if attention:
        print("")
        print("First artifacts needing review:")
        for record in attention:
            repairs = "; ".join(
                f"{repair['source']}: {repair['reason']}"
                for repair in list_of_dicts(record.get("repair_suggestions"))
                if repair.get("source") != "none"
            )
            print(f"  - {record['coverage']} {record['confidence']}: {record['path']}")
            if repairs:
                print(f"    repair: {repairs}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    report = build_report(load_index(args))

    if args.json or args.pretty:
        indent = 2 if args.pretty else None
        print(json.dumps(report, indent=indent, sort_keys=True))
    else:
        print_text(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
