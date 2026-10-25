#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.check-source-projections.scoped-smoke-test
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 02.rag-rulebook
#   domain: validation
#   disciplines: [agentic, architecture]
#   kind: script
#   purpose: Prove scoped projection validation preserves selected content and global inventory checks.
#   portability: { class: reusable, targets: [llm-workbench, entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: rag-rulebook.script.check-source-projections
#     path: scripts/02.rag-rulebook/check-source-projections/script.sh

python3 - "$(git rev-parse --show-toplevel)/scripts/02.rag-rulebook/check-source-projections/script.sh" <<'PY'
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import yaml

checker = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="rag-projection-scope-") as temporary:
    root = Path(temporary)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    manifest_path = root / ".agentic/02.rag-rulebook/source-projections/v1.yml"
    manifest = {"schema": "rag-rulebook/source-projection-manifest/v1", "manifest_id": "fixture", "status": "active", "projection_sets": []}

    def write(path, data):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(data, sort_keys=False) if isinstance(data, dict) else data)

    for name in ("selected", "unrelated"):
        source = f"docs/02.rag-rulebook/source-material/{name}.md"
        rule = f"docs/02.rag-rulebook/rules/{name}.yml"
        report = f".agentic/02.rag-rulebook/derivation-reports/{name}.yml"
        write(source, f"# {name}\nGoverned {name} source.\n")
        write(rule, {"source_derivation": {"derivation_report": report, "source_material": [{"path": source, "sha256": hashlib.sha256((root / source).read_bytes()).hexdigest()}]}})
        write(report, {"schema": "rag-rulebook/source-to-rule-derivation-report/v1", "source_change": {"changed_paths": [source]}, "target": {"expected_rule_paths": [rule]}})
        manifest["projection_sets"].append({"id": name, "status": "active", "projection_mode": "manual-reviewed", "source_material": [{"path": source, "role": "primary"}], "target": {"corpus_id": "corpus.02.rag-rulebook", "owner_layer": "02.rag-rulebook"}, "expected_rule_paths": [rule], "derivation_reports": [report], "corpus_gap_paths": [], "expected_selector_evaluations": []})
    write(manifest_path, manifest)

    def run(selector=None, expected=True, error=None):
        argv = ["bash", str(checker), "--current", "--json"]
        if selector is not None:
            argv += ["--projection-set", selector]
        result = subprocess.run(argv, cwd=root, text=True, capture_output=True)
        report = json.loads(result.stdout)
        assert (result.returncode == 0) == expected, (argv, report, result.stderr)
        assert report["ok"] == expected
        if error:
            assert any(error in item for item in report["errors"]), report
        return report

    assert run()["validation_scope"]["all_content_checked"] is True
    scoped = run("selected")
    assert scoped["validation_scope"] == {"mode": "projection-set", "projection_set_ids": ["selected"], "global_manifest_inventory_checked": True, "all_content_checked": False}
    # An unrelated stale hash cannot be misreported as a globally passing corpus.
    write("docs/02.rag-rulebook/source-material/unrelated.md", "# changed unrelated source\n")
    run(expected=False, error="hash is stale")
    run("selected")
    # The selected source's stale hash still blocks scoped validation.
    selected_source = root / "docs/02.rag-rulebook/source-material/selected.md"
    original = selected_source.read_text()
    selected_source.write_text("# changed selected source\n")
    run("selected", expected=False, error="hash is stale")
    selected_source.write_text(original)
    run("unknown", expected=False, error="exactly one declared set")
    repeated = subprocess.run(["bash", str(checker), "--current", "--projection-set", "selected", "--projection-set", "unrelated"], cwd=root, text=True, capture_output=True)
    assert repeated.returncode == 2 and "at most once" in repeated.stderr
    changed = copy.deepcopy(manifest)
    changed["projection_sets"].append(copy.deepcopy(changed["projection_sets"][0]))
    write(manifest_path, changed)
    run("selected", expected=False, error="duplicate projection set id")
    changed = copy.deepcopy(manifest)
    changed["projection_sets"][0]["status"] = "planned"
    write(manifest_path, changed)
    run("selected", expected=False, error="must name an active set")
    write(manifest_path, manifest)
    write("docs/02.rag-rulebook/source-material/unowned.md", "# undeclared\n")
    run("selected", expected=False, error="not declared in active projection manifest")
    (root / "docs/02.rag-rulebook/source-material/unowned.md").unlink()
    selected_report = ".agentic/02.rag-rulebook/derivation-reports/selected.yml"
    write(selected_report, {"schema": "rag-rulebook/source-to-rule-derivation-report/v1", "source_change": {"changed_paths": []}, "target": {"expected_rule_paths": []}})
    run("selected", expected=False, error="does not mention projection source")
print("Scoped source projection regression passed: selected freshness/report proof and global inventory remain enforced.")
PY
