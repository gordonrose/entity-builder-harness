<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.check-corpus-root-changes.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: validation
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the governed corpus-root change detector for RAG/rulebook inputs.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.check-corpus-root-changes
  path: scripts/02.rag-rulebook/check-corpus-root-changes/script.sh
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# Check Corpus Root Changes

`script.sh` detects changed files under governed RAG/rulebook corpus roots and
verifies that risky changes have an explicit governance path.

## Why This Exists

Runtime freshness and source projection checks prove the current repository
state. They do not, by themselves, explain that a previously tracked source or
rule file was intentionally removed.

This checker fills that gap at commit time.

## Usage

Check current worktree changes against `HEAD`:

```bash
bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current
```

Machine-readable report:

```bash
bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --current --json
```

Smoke-test fixture mode:

```bash
bash scripts/02.rag-rulebook/check-corpus-root-changes/script.sh --changes-file <path>
```

The fixture file is tab-separated:

```text
D<TAB>docs/04.deploy/source-material/example.md
A<TAB>docs/04.deploy/rules/example.yml
R<TAB>old/path.md<TAB>new/path.md
```

## Checks

- deleted governed source/rule/projection artifacts require accepted retirement
  records
- renamed old paths require accepted retirement records
- active changed rule YAML files must be present in the generated rulebook
  index and generated chunk set
- changed source-material files require source-material coverage to remain
  valid

## Effects

This command is read-only. It does not stage files, delete files, generate
rules, or update retirement records.
