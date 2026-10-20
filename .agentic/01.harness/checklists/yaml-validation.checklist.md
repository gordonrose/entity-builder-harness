<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.checklists.yaml-validation
version: 1
status: active
created_on: "2026-06-22"
updated_on: "2026-10-20"
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: checklist
purpose: Provide YAML validation options for architecture rulebook artifacts.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.workflows.continue-rulebook
  path: .agentic/01.harness/workflows/continue-rulebook.workflow.md
-->

# YAML Validation Checklist

Use a structured YAML parser, then report the validation method used.

```bash
python3 - path/to/file.yml <<'PY'
import yaml, sys
from pathlib import Path
for p in sys.argv[1:]:
    with open(p) as f:
        yaml.safe_load(f)
    print(f"OK: {p}")
PY
```

If PyYAML is unavailable, use Ruby, Node, `yq`, or another available parser.
