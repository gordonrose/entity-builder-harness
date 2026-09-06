#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.render-platform-shell-foundation-template
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - architecture
#   - sre
#   kind: script
#   purpose: Render the focused Kanbien platform-shell foundation source units into one deployable CloudFormation template.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - writes-files
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MANIFEST="infra/04.deploy/03.product/targets/kanbien/staging/cloudformation/foundation.yml"
OUTPUT=""

usage() {
  cat <<'EOF'
Usage:
  render-platform-shell-foundation-template/script.sh --output <path> [--manifest <path>]

Renders the source units named by the foundation composition manifest into one
CloudFormation template. The output is transient deployment input; edit the
focused source units, never a rendered file.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --manifest)
      MANIFEST="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$OUTPUT" ]; then
  echo "ERROR: --output is required" >&2
  usage >&2
  exit 2
fi

python3 - "$MANIFEST" "$OUTPUT" <<'PY'
from pathlib import Path
import os
import sys
import tempfile

try:
    import yaml
    from yaml.nodes import MappingNode, ScalarNode
except ImportError as error:
    raise SystemExit("ERROR: PyYAML is required. Install PyYAML==6.0.2 before rendering.") from error


manifest_path = Path(sys.argv[1]).resolve()
output_path = Path(sys.argv[2]).resolve()

if not manifest_path.is_file():
    raise SystemExit(f"ERROR: foundation composition manifest is missing: {manifest_path}")

with manifest_path.open(encoding="utf-8") as handle:
    manifest = yaml.safe_load(handle)

if not isinstance(manifest, dict) or manifest.get("schema") != "deploy/cloudformation-composition/v1":
    raise SystemExit("ERROR: foundation composition manifest must use schema deploy/cloudformation-composition/v1")

fragments = manifest.get("fragments")
if not isinstance(fragments, list) or not fragments or not all(isinstance(item, str) and item for item in fragments):
    raise SystemExit("ERROR: foundation composition manifest must declare a non-empty string fragments list")

source_root = manifest_path.parent.resolve()
section_names = ("Parameters", "Resources", "Outputs")
scalar_names = ("AWSTemplateFormatVersion", "Description")
merged_sections = {name: [] for name in section_names}
seen_section_entries = {name: set() for name in section_names}
scalars = {}


def fail(message):
    raise SystemExit(f"ERROR: {message}")


def mapping_entries(node, context):
    if not isinstance(node, MappingNode):
        fail(f"{context} must be a YAML mapping")
    entries = []
    for key_node, value_node in node.value:
        if not isinstance(key_node, ScalarNode):
            fail(f"{context} contains a non-scalar key")
        entries.append((key_node.value, key_node, value_node))
    return entries


for fragment_name in fragments:
    candidate = (source_root / fragment_name).resolve()
    try:
        candidate.relative_to(source_root)
    except ValueError:
        fail(f"fragment escapes the composition directory: {fragment_name}")
    if not candidate.is_file():
        fail(f"foundation fragment is missing: {fragment_name}")

    with candidate.open(encoding="utf-8") as handle:
        document = yaml.compose(handle)
    if document is None:
        fail(f"foundation fragment is empty: {fragment_name}")

    for key, _key_node, value_node in mapping_entries(document, f"fragment {fragment_name}"):
        if key in section_names:
            for entry_name, entry_key, entry_value in mapping_entries(value_node, f"{fragment_name}:{key}"):
                if entry_name in seen_section_entries[key]:
                    fail(f"duplicate {key} entry {entry_name} in {fragment_name}")
                seen_section_entries[key].add(entry_name)
                merged_sections[key].append((entry_key, entry_value))
        elif key in scalar_names:
            if key in scalars:
                fail(f"duplicate root template field {key} in {fragment_name}")
            scalars[key] = value_node
        else:
            fail(f"unsupported root template field {key} in {fragment_name}")

for required in scalar_names + section_names:
    if required in scalar_names and required not in scalars:
        fail(f"missing required root template field {required}")
    if required in section_names and not merged_sections[required]:
        fail(f"missing required {required} entries")

root_entries = []
for name in scalar_names:
    root_entries.append((ScalarNode(tag="tag:yaml.org,2002:str", value=name), scalars[name]))
for name in section_names:
    root_entries.append((
        ScalarNode(tag="tag:yaml.org,2002:str", value=name),
        MappingNode(tag="tag:yaml.org,2002:map", value=merged_sections[name]),
    ))

rendered = yaml.serialize(MappingNode(tag="tag:yaml.org,2002:map", value=root_entries), Dumper=yaml.Dumper)
header = "# Generated by scripts/04.deploy/render-platform-shell-foundation-template/script.sh.\n# Edit the focused source fragments, not this transient file.\n"

output_path.parent.mkdir(parents=True, exist_ok=True)
with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as temporary:
    temporary.write(header)
    temporary.write(rendered)
    temporary_path = Path(temporary.name)
os.replace(temporary_path, output_path)
print(f"Rendered foundation template: {output_path}")
PY
