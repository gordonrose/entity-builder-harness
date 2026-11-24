#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.compiler.script-topology-inventory
#   version: 1
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.governance
#   disciplines: [architecture, sre]
#   kind: script
#   purpose: Project source-backed script ownership, role, callers, effects and migration disposition without creating a second registry.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.compiler.inventory-deploy-control
#     path: scripts/04.deploy/inventory-deploy-control/script.py

"""Read-only script topology projection for the existing delivery inventory."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


SCRIPT_SUFFIXES = frozenset({".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx"})
TEST_MARKERS = ("test", "smoke", "regression", "spec")
GENERIC_NAMES = frozenset({"script", "control", "steps", "route", "helper", "helpers", "utility", "utils"})
PHASES = frozenset({"00-target-alignment", "10-development", "20-build", "30-test", "40-package", "50-deploy", "60-run"})
ROLES = frozenset({"public command", "reusable capability implementation", "provider adapter", "target/workload binding", "test", "fixture", "obsolete or transitional machinery"})


def _module(root: Path):
    path = root / "scripts/01.harness/artifact-metadata/header_discovery.py"
    spec = importlib.util.spec_from_file_location("script_topology_header_discovery", path)
    if spec is None or spec.loader is None:
        raise ValueError("artifact-header-discovery-unavailable")
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    try:
        spec.loader.exec_module(value)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return value


def _tracked(root: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "scripts"], check=True, capture_output=True)
    return sorted(item.decode("utf-8", "surrogateescape") for item in result.stdout.split(b"\0") if item)


def _role(path: str) -> str:
    parts, name = path.split("/"), Path(path).stem.lower()
    if "fixtures" in parts or name.endswith(("-fixture", "_fixture")):
        return "fixture"
    if "tests" in parts or any(marker in name for marker in TEST_MARKERS):
        return "test"
    if any(part in {"retired", "transitional", "compatibility"} for part in parts) or name in {"source-transition", "image-delivery-repair"}:
        return "obsolete or transitional machinery"
    if "provider-adapters" in parts:
        return "provider adapter"
    if "targets" in parts:
        return "target/workload binding"
    if path.startswith("scripts/04.deploy/commands/") and Path(path).stem == "command":
        return "public command"
    if (len(parts) > 3 and parts[1] == "00.chat" and parts[2] == "command") or (len(parts) > 3 and parts[1] == "04.deploy" and parts[2].split("-", 1)[0] in {"run", "verify", "build", "provision", "assess", "reconcile", "render", "smoke", "validate"} and Path(path).name == "script.sh"):
        return "public command"
    return "reusable capability implementation"


def _scope(path: str, role: str) -> str:
    parts = path.split("/")
    if role == "provider adapter":
        return "provider-specific"
    if "targets" in parts:
        index = parts.index("targets")
        return "workload-specific" if len(parts) > index + 2 else "target-specific"
    return "shared"


def _phase(path: str) -> str | None:
    parts = path.split("/")
    try:
        index = parts.index("lifecycle")
    except ValueError:
        return None
    return parts[index + 1] if len(parts) > index + 1 and parts[index + 1] in PHASES else None


def _capability(path: str, metadata: dict) -> str:
    identifier = metadata.get("id") if isinstance(metadata, dict) else None
    if isinstance(identifier, str) and identifier:
        return identifier
    parts = path.split("/")
    for marker in ("targets", "provider-adapters", "lifecycle"):
        if marker in parts:
            index = parts.index(marker)
            tail = [part for part in parts[index + 1:-1] if part not in PHASES and part not in {"tests", "fixtures"}]
            if tail:
                return ".".join(tail)
    return Path(path).parent.name


def _destination(path: str, role: str, scope: str, capability: str, phase: str | None) -> str:
    suffix = Path(path).suffix
    objective = "unresolved-objective" if Path(path).stem in GENERIC_NAMES else Path(path).stem
    safe_capability = re.sub(r"[^a-z0-9]+", "-", capability.rsplit(".", 1)[-1].lower()).strip("-") or "capability"
    if not path.startswith("scripts/04.deploy/"):
        return path
    if role == "public command":
        return f"scripts/04.deploy/commands/{safe_capability}/command{suffix}"
    if role == "provider adapter" or "provider-adapters" in path.split("/"):
        parts = path.split("/")
        provider = parts[parts.index("provider-adapters") + 1] if len(parts) > parts.index("provider-adapters") + 1 else "provider"
        name = "implementation" + suffix if role == "provider adapter" else ("tests/" + Path(path).name if role == "test" else "fixtures/" + Path(path).name if role == "fixture" else Path(path).name)
        return f"scripts/04.deploy/shared/provider-adapters/{provider}/{safe_capability}/{objective}/{name}"
    stage = phase or "unassigned-phase"
    if scope in {"target-specific", "workload-specific"}:
        parts = path.split("/")
        index = parts.index("targets")
        target = parts[index + 1] if len(parts) > index + 1 else "target"
        workload = parts[index + 2] if len(parts) > index + 2 else "scope"
        root = f"scripts/04.deploy/lifecycle/{stage}/targets/{target}/{workload}/bindings/{safe_capability}/{objective}"
        name = "binding" + suffix if role == "target/workload binding" else ("tests/" if role == "test" else "fixtures/" if role == "fixture" else "") + Path(path).name
        return f"{root}/{name}"
    root = f"scripts/04.deploy/lifecycle/{stage}/capabilities/{safe_capability}/{objective}"
    name = "implementation" + suffix if role == "reusable capability implementation" else ("tests/" if role == "test" else "fixtures/" if role == "fixture" else "") + Path(path).name
    return f"{root}/{name}"


def _disposition(path: str, role: str, scope: str) -> str:
    if role == "obsolete or transitional machinery":
        return "remove"
    if not path.startswith("scripts/04.deploy/"):
        return "retain"
    if path.startswith("scripts/04.deploy/lifecycle/") and role == "reusable capability implementation":
        return "move"
    if role == "public command" and not path.startswith("scripts/04.deploy/commands/"):
        return "move"
    if role == "target/workload binding" and Path(path).stem in GENERIC_NAMES:
        return "merge"
    if scope == "provider-specific" and not path.startswith("scripts/04.deploy/shared/provider-adapters/"):
        return "move"
    return "retain"


def _metadata(root: Path, paths: list[str]):
    discovery = _module(root)
    result, findings = {}, []
    for path in paths:
        try:
            parsed = discovery.parse_header_text((root / path).read_text(encoding="utf-8"))
            value = parsed.get("agentic-artifact", parsed.get("agentic-script", {}))
            result[path] = value if isinstance(value, dict) else {}
        except (OSError, UnicodeError, discovery.HeaderError) as error:
            result[path] = {}
            findings.append({"code": "script-topology-metadata-unavailable", "path": path, "error": type(error).__name__})
    return result, findings


def report(root: Path) -> dict:
    root = root.resolve()
    tracked = _tracked(root)
    source_paths = [path for path in tracked if Path(path).suffix in SCRIPT_SUFFIXES]
    bodies = {path: (root / path).read_text(encoding="utf-8") for path in source_paths}
    metadata, findings = _metadata(root, source_paths)
    callers = defaultdict(set)
    for path, body in bodies.items():
        for candidate in source_paths:
            if candidate != path and candidate in body:
                callers[candidate].add(path)
    for path, value in metadata.items():
        used_by = value.get("used_by", []) if isinstance(value, dict) else []
        if isinstance(used_by, list):
            for item in used_by:
                if isinstance(item, dict) and isinstance(item.get("path"), str):
                    callers[path].add(item["path"])
    units = []
    duplicate_ids = defaultdict(list)
    for path in source_paths:
        value = metadata[path]
        role = _role(path)
        scope = _scope(path, role)
        phase = _phase(path)
        capability = _capability(path, value)
        if isinstance(value.get("id"), str):
            duplicate_ids[value["id"]].append(path)
        overlaps = []
        if Path(path).stem in GENERIC_NAMES:
            overlaps.append("generic-file-name")
        if role == "target/workload binding" and Path(path).stem in GENERIC_NAMES:
            overlaps.append("target-bound-generic-implementation")
        dependencies = sorted(callers[path])
        units.append({
            "current_path": path,
            "owner": value.get("id") if isinstance(value.get("id"), str) else capability,
            "owning_capability": capability,
            "role": role,
            "current_callers": dependencies,
            "effects": value.get("effects", []) if isinstance(value.get("effects", []), list) else [],
            "scope": scope,
            "overlap_candidates": overlaps,
            "proposed_destination": _destination(path, role, scope, capability, phase),
            "disposition": _disposition(path, role, scope),
            "migration_dependencies": dependencies,
            "source": {"artifact_id": value.get("id"), "phase": phase, "metadata_present": bool(value)},
        })
    for identifier, paths in duplicate_ids.items():
        if len(paths) > 1:
            for unit in units:
                if unit["source"]["artifact_id"] == identifier:
                    unit["overlap_candidates"].append("duplicate-artifact-id:" + identifier)
    inputs = [{"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()} for path in tracked]
    summary = {
        "tracked_paths": len(tracked),
        "script_sources": len(units),
        "supplementary_paths": len(tracked) - len(units),
        "roles": dict(sorted(Counter(unit["role"] for unit in units).items())),
        "dispositions": dict(sorted(Counter(unit["disposition"] for unit in units).items())),
    }
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    return {"schema": "deploy/script-topology-inventory/v1", "source_revision": revision, "source_state": "working-tree", "input_digest": hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(), "summary": summary, "units": units, "findings": findings,
            "limitations": ["This view classifies script source files and associates non-script paths through their containing families; it does not prove semantic equivalence or authorize a move.", "Dispositions are migration proposals. A path move still requires the artifact-path migration workflow and an approved capability slice."]}


def markdown(value: dict) -> str:
    summary = value["summary"]
    lines = ["# Script topology inventory", "", f"Revision: `{value['source_revision']}`; input digest: `{value['input_digest']}`.", "", f"{summary['script_sources']} script sources across {summary['tracked_paths']} tracked `scripts/` paths.", "", "| Role | Count |", "| --- | ---: |"]
    lines += [f"| {role} | {count} |" for role, count in summary["roles"].items()]
    lines += ["", "| Proposed disposition | Count |", "| --- | ---: |"]
    lines += [f"| {disposition} | {count} |" for disposition, count in summary["dispositions"].items()]
    lines += ["", "The JSON view contains every classified script source, its metadata-backed caller references, effects, proposed destination, disposition and migration dependencies. It is a planning observation, not a move authority."]
    return "\n".join(lines)
