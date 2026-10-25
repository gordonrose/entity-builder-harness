#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: rag-rulebook.script.check-source-material-coverage.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-27"
#   updated_on: "2026-10-25"
#   layer: 02.rag-rulebook
#   domain: rulebook
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Prove global and exact-source coverage checks with isolated provenance and index/chunk failure fixtures.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: rag-rulebook.script.check-source-material-coverage
#       path: scripts/02.rag-rulebook/check-source-material-coverage/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 - "$TMP_DIR" "$PWD" <<'PY'
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import yaml

fixture = Path(sys.argv[1])
repo = Path(sys.argv[2])
checker = "scripts/02.rag-rulebook/check-source-material-coverage/script.sh"
subprocess.run(["git", "init", "--quiet", str(fixture)], check=True)

def write(path, text):
    target = fixture / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)

write(checker, (repo / checker).read_text())
source_a = "docs/02.rag-rulebook/source-material/selected.md"
source_b = "docs/02.rag-rulebook/source-material/unrelated.md"
rule_a = "docs/02.rag-rulebook/rules/selected.yml"
rule_b = "docs/02.rag-rulebook/rules/unrelated.yml"
workflow = ".agentic/02.rag-rulebook/workflows/derive-rules-from-source.md"
report_path = ".agentic/02.rag-rulebook/derivation-reports/fixture.yml"
write(source_a, "# Selected source\nLocal retrieval configuration.\n")
write(source_b, "# Unrelated source\nOther corpus knowledge.\n")
write(workflow, "# Fixture derivation workflow\n")
write(report_path, "schema: fixture\n")

def rule(source):
    return {
        "source_refs": [{"doc": source}],
        "source_derivation": {
            "provenance_version": "rag-rulebook/source-derivation-provenance/v1",
            "mode": "generated-projection", "generator": "fixture",
            "generator_version": "v1", "generated_at_utc": "2026-10-25T00:00:00Z",
            "derivation_workflow": workflow, "derivation_report": report_path,
            "source_material": [{"path": source, "sha256": hashlib.sha256((fixture/source).read_bytes()).hexdigest()}],
        },
    }

selected_rule = rule(source_a)
other_rule = rule(source_b)
write(rule_a, yaml.safe_dump(selected_rule))
write(rule_b, yaml.safe_dump(other_rule))

def generators(index_paths=(rule_a, rule_b), chunk_paths=(rule_a, rule_b)):
    # Control the generated boundaries independently to prove missing output fails.
    for name, payload in (
        ("generate-rulebook-index", {"artifacts": [{"current_path": p} for p in index_paths]}),
        ("generate-rulebook-chunks", {"chunks": [{"source_path": p} for p in chunk_paths]}),
    ):
        write(f"scripts/02.rag-rulebook/{name}/script.sh", "#!/usr/bin/env bash\ncat <<'JSON'\n" + json.dumps(payload) + "\nJSON\n")

generators()

def run(*args, expected=0):
    result = subprocess.run(["bash", checker, "--current", "--json", *args], cwd=fixture, text=True, capture_output=True)
    assert result.returncode == expected, (args, result.returncode, result.stdout, result.stderr)
    return json.loads(result.stdout) if result.stdout.strip() else result.stderr

def errors_contain(report, text):
    assert any(text in e for e in report["errors"]), report

all_report = run()
assert all_report["scope"] == {"mode": "all", "source": None}
assert all_report["counts"]["sources"] == 2
selected = run("--source", source_a)
assert selected["scope"] == {"mode": "source", "source": source_a}
assert [s["path"] for s in selected["sources"]] == [source_a]
assert selected["sources"][0]["indexed_rule_paths"] == [rule_a]
assert selected["sources"][0]["chunked_rule_paths"] == [rule_a]

# Unrelated stale provenance stays a global failure, while selected proof is valid.
write(source_b, (fixture/source_b).read_text()+"Changed source.\n")
errors_contain(run(expected=1), "hash is stale for " + source_b)
run("--source", source_a)
errors_contain(run("--source", source_b, expected=1), "hash is stale for " + source_b)
assert "existing canonical governed source" in run("--source", "missing.md", expected=2)
assert "at most once" in run("--source", source_a, "--source", source_a, expected=2)

orphan = "docs/02.rag-rulebook/source-material/orphan.md"
write(orphan, "# Uncovered source\n")
errors_contain(run("--source", orphan, expected=1), "no governed coverage outcome")
(fixture/orphan).unlink()

generators(index_paths=(rule_b,))
errors_contain(run("--source", source_a, expected=1), "not present in generated index")
generators(chunk_paths=(rule_b,))
errors_contain(run("--source", source_a, expected=1), "not present in generated chunks")
generators()

# Scoping never suppresses malformed global YAML or a selected rule's dependencies.
write(rule_b, "invalid: [\n")
errors_contain(run("--source", source_a, expected=1), "failed to parse as YAML")
write(rule_b, yaml.safe_dump(other_rule))
malformed_derivation = copy.deepcopy(other_rule)
malformed_derivation["source_derivation"]["mode"] = ""
write(rule_b, yaml.safe_dump(malformed_derivation))
errors_contain(run("--source", source_a, expected=1), "source_derivation.mode must be")
write(rule_b, yaml.safe_dump(other_rule))
cross_source_rule = copy.deepcopy(selected_rule)
cross_source_rule["source_derivation"]["source_material"].extend(other_rule["source_derivation"]["source_material"])
write(rule_a, yaml.safe_dump(cross_source_rule))
errors_contain(run("--source", source_a, expected=1), "hash is stale for " + source_b)
write(rule_a, yaml.safe_dump(selected_rule))
write(source_a, (fixture/source_a).read_text()+"Changed selected source.\n")
errors_contain(run("--source", source_a, expected=1), "hash is stale for " + source_a)
print("Source material coverage smoke test passed (global and exact-source proof).")
PY
