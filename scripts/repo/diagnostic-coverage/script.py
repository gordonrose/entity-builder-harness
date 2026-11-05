#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.diagnostics.coverage-compiler
#   version: 1
#   status: active
#   created_on: "2026-10-27"
#   updated_on: "2026-10-31"
#   layer: 06.shared
#   domain: diagnostics
#   disciplines: [architecture, security, sre, agentic]
#   kind: script
#   purpose: Discover ordinary executable code independently of deployment and prevent silent expansion of diagnostic debt.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: repo.diagnostics.coverage
#     path: scripts/repo/diagnostic-coverage/script.sh
"""Structural adoption gate, not a claim that source scanning proves semantics."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASELINE = "d94da2b9401d3abcf86618b5d497e9b93903490a"
REVIEWS = "scripts/repo/diagnostic-coverage/reviews.v1.json"
ROOTS = {"packages", "platform", "apps", "products", "scripts", "infra", "bin"}
EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".sh"}
DORMANT = ("scripts/02.rag-rulebook/", "infra/04.deploy/02.rag-rulebook/")
REVIEW_ERRORS = {"diagnostic-review-contract-invalid", "diagnostic-review-required-fields-invalid", "diagnostic-partial-review-debt-missing", "diagnostic-review-proof-reference-invalid", "diagnostic-review-check-unregistered", "diagnostic-adoption-proof-missing"}

def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout

def source_file(path: str) -> bool:
    parts = Path(path).parts
    name = Path(path).name
    return bool(parts) and Path(path).suffix in EXTENSIONS and not path.startswith(DORMANT) and not any(
        part in {"tests", "fixtures", "__tests__", "node_modules", "dist", "__pycache__"} for part in parts
    ) and not name.startswith(("test-", "test_")) and not any(token in name for token in (".test.", "-test.", "-tests.", "smoke-test", "runtime-test"))

def executable(path: str) -> bool:
    return source_file(path) and Path(path).parts[0] in ROOTS

def discover(root: Path) -> list[str]:
    paths = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    # Also discover source outside the conventional roots when a workspace adds a new location.
    workspaces = json.loads((root / "package.json").read_text())["workspaces"]
    extra_roots = [directory for pattern in workspaces for directory in root.glob(pattern) if directory.is_dir() and (directory / "package.json").is_file()]
    extra = {path for path in paths if path and source_file(path) and (root / path).exists()
             and any(path.startswith(directory.relative_to(root).as_posix() + "/") for directory in extra_roots) and not path.startswith(DORMANT)}
    return sorted({path for path in paths if path and executable(path) and (root / path).exists()} | extra)

def safe_file(root: Path, path: object) -> bool:
    return isinstance(path, str) and not Path(path).is_absolute() and ".." not in Path(path).parts and (root / path).is_file() and not (root / path).is_symlink() and (root / path).resolve().is_relative_to(root.resolve())

def review_document(document: object) -> list[dict]:
    """Pure semantic validation also supports deleted comparison-tree paths."""
    if not isinstance(document, dict) or document.get('schema') != 'repo/diagnostic-adoption/v1' or not isinstance(document.get('reviews'), list):
        raise ValueError('diagnostic-review-contract-invalid')
    seen = set()
    for review in document['reviews']:
        if not isinstance(review, dict) or not isinstance(review.get('owner'), str) or not review.get('owner') or not isinstance(review.get('reason'), str) or not review['reason'].strip() or review.get('status') not in {'adopted', 'partial', 'support'}:
            raise ValueError('diagnostic-review-required-fields-invalid')
        if review['status'] == 'partial' and (not isinstance(review.get('remaining_debt'), list) or not review['remaining_debt'] or any(not isinstance(debt, str) or not debt.strip() for debt in review['remaining_debt'])):
            raise ValueError('diagnostic-partial-review-debt-missing')
        if review['status'] == 'adopted' and (not review.get('definitions') or not isinstance(review.get('proof'), list) or set(review['proof']) != {'accuracy', 'disclosure', 'preservation', 'uncertainty'}):
            raise ValueError('diagnostic-adoption-proof-missing')
        for field in ('tests', 'checks', 'sources'):
            if not isinstance(review.get(field), list) or not review[field]: raise ValueError('diagnostic-review-required-fields-invalid')
        for source in review['sources']:
            if not isinstance(source, dict) or not isinstance(source.get('path'), str) or source['path'] in seen or not re.fullmatch(r'[0-9a-f]{64}', source.get('sha256', '')):
                raise ValueError('diagnostic-review-source-invalid')
            seen.add(source['path'])
        paths = [source['path'] for source in review['sources']] + review['tests'] + review.get('definitions', [])
        if any(not isinstance(path, str) or not path or Path(path).is_absolute() or '..' in Path(path).parts for path in paths) or any(not isinstance(check, str) or not check for check in review['checks']):
            raise ValueError('diagnostic-review-proof-reference-invalid')
    return document['reviews']

def review_bindings(root: Path) -> dict[str, list[dict]]:
    bindings = {}
    for review in review_document(json.loads((root / REVIEWS).read_text())):
        for check in review['checks']: bindings.setdefault(check, []).append(review)
    return {check: sorted(entries, key=lambda entry: json.dumps(entry, sort_keys=True)) for check, entries in bindings.items()}

def review_rules(root: Path, *, comparison_base: str = 'HEAD', ledger_changed: bool = False) -> list[dict[str, list[str]]]:
    """Selector consumes review-owned check identities, never arbitrary commands."""
    current = review_document(json.loads((root / REVIEWS).read_text()))
    # A verification owner can truthfully be both executable source and proof.
    # Preserve every dependency and its first occurrence without emitting an
    # invalid duplicate input to the selector.
    rules = [{"inputs": list(dict.fromkeys([source["path"] for source in review["sources"]] + review["tests"] + review.get('definitions', []))), "checks": review["checks"]} for review in current]
    if ledger_changed:
        # A valid tree with no ledger is first adoption, not an unreadable base.
        git(root, 'rev-parse', '--verify', comparison_base + '^{commit}')
        present = git(root, 'ls-tree', comparison_base, '--', REVIEWS).strip()
        before = review_document(json.loads(git(root, 'show', comparison_base + ':' + REVIEWS))) if present else []
        old = {source['path']: review for review in before for source in review['sources']}
        new = {source['path']: review for review in current for source in review['sources']}
        changed_checks = set()
        for path in set(old) | set(new):
            if old.get(path) != new.get(path):
                for review in (old.get(path), new.get(path)):
                    if review: changed_checks.update(review['checks'])
        if changed_checks: rules.append({'inputs': [REVIEWS], 'checks': sorted(changed_checks)})
    return rules

def proof_inputs(root: Path) -> list[str]:
    """Bind the actual source census, not unrelated immutable release evidence."""
    paths = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    manifests = [path for path in paths if path.endswith("/package.json") and safe_file(root, path) and not path.startswith(DORMANT)]
    return discover(root) + manifests

def validate(root: Path = ROOT) -> dict:
    findings: list[dict[str, str]] = []
    document = json.loads((root / REVIEWS).read_text())
    if document.get("schema") != "repo/diagnostic-adoption/v1" or document.get("baseline") != BASELINE:
        raise ValueError("diagnostic-review-contract-invalid")
    baseline = {}
    for record in git(root, "ls-tree", "-r", "-z", BASELINE).split(b"\0"):
        if record:
            meta, path = record.split(b"\t", 1)
            baseline[path.decode()] = meta.split()[2].decode()
    reviews: dict[str, dict] = {}
    import yaml
    catalog = yaml.safe_load((root / "scripts/repo/check-selection/checks.yml").read_text())["checks"]
    for review in review_document(document):
        if review.get("status") not in {"adopted", "partial", "support"} or not review.get("owner") or not review.get("reason") or not review.get("tests") or not review.get("checks"):
            raise ValueError("diagnostic-review-required-fields-invalid")
        if review["status"] == "partial" and not review.get("remaining_debt"):
            raise ValueError("diagnostic-partial-review-debt-missing")
        if not all(safe_file(root, path) for path in review["tests"] + review.get("definitions", [])):
            raise ValueError("diagnostic-review-proof-reference-invalid")
        if not all(check in catalog and catalog[check].get("stage") == "local" for check in review["checks"]):
            raise ValueError("diagnostic-review-check-unregistered")
        if review["status"] == "adopted" and (not review.get("definitions") or set(review.get("proof", [])) != {"accuracy", "disclosure", "preservation", "uncertainty"}):
            raise ValueError("diagnostic-adoption-proof-missing")
        for source in review["sources"]:
            path = source["path"]
            if path in reviews or not safe_file(root, path):
                findings.append({"code": "diagnostic-review-source-invalid", "path": path}); continue
            reviews[path] = review
            if hashlib.sha256((root / path).read_bytes()).hexdigest() != source.get("sha256"):
                findings.append({"code": "diagnostic-review-stale", "path": path})
    debt, adopted, partial = [], [], []
    discovered = discover(root)
    for path in discovered:
        if not safe_file(root, path):
            findings.append({"code": "diagnostic-source-boundary-invalid", "path": path}); continue
        if path in reviews:
            (adopted if reviews[path]["status"] == "adopted" else partial).append(path)
        elif baseline.get(path) == git(root, "hash-object", "--", path).decode().strip():
            debt.append(path)
        else:
            findings.append({"code": "diagnostic-new-or-changed-code-unreviewed", "path": path})
    for path in set(reviews) - set(discovered):
        findings.append({"code": "diagnostic-review-source-not-discovered", "path": path})
    return {"schema": "repo/diagnostic-coverage-report/v1", "verdict": "failed" if findings else "passed", "baseline": BASELINE,
            "counts": {"discovered": len(discovered), "adopted": len(adopted), "reviewed_partial_or_support": len(partial), "legacy_debt": len(debt)},
            "legacy_debt": debt, "findings": findings}

def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    try: report = validate()
    except Exception as error:
        code = str(error) if isinstance(error, ValueError) and str(error) in REVIEW_ERRORS else "diagnostic-coverage-input-unavailable-or-invalid"
        report = {"schema": "repo/diagnostic-coverage-report/v1", "verdict": "failed", "findings": [{"code": code}]}
    print(json.dumps(report, sort_keys=True))
    return int(report["verdict"] != "passed")

if __name__ == "__main__":
    raise SystemExit(main())
