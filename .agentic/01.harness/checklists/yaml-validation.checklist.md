<!-- agentic-artifact:
owner: harness
kind: checklist
purpose: Provide YAML validation options for architecture rulebook artifacts.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/workflows/continue-rulebook.workflow.md
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
