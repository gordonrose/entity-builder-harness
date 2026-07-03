<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.checklists.llm-workbench-public-beta
  version: 1
  status: active
  layer: 00.chat
  domain: portability
  disciplines:
  - agentic
  kind: checklist
  purpose: Check llm-workbench public-beta portability before committing related work.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.standards.llm-workbench-public-beta-contract
    path: .agentic/00.chat/standards/llm-workbench-public-beta-contract.md
  - id: chat.checklists.before-commit
    path: .agentic/00.chat/checklists/before-commit.md
-->
# llm-workbench Public-Beta Checklist

Use this before committing changes that touch public export, install/uninstall,
chat startup, assistant adapters, transcript metrics, cost metrics, public
templates, or portability validation.

## Contract

Read `.agentic/00.chat/standards/llm-workbench-public-beta-contract.md`.

Confirm the change preserves:

- no durable whole-chat `layer`, `mode`, or `workflow` classification
- standalone public export with self-consistent metadata
- no mandatory RAG/rulebook or Codex behavior in generic chat surfaces
- provider-neutral transcript and cost defaults
- safe blank and existing repo install/uninstall behavior
- thin assistant adapters
- CLI/code-assistant robustness, including JSON startup and executable-bit loss

## Temporary Eval

- A temporary eval or failing smoke case was written before the patch.
- The eval failed before the implementation.
- The implementation made the eval pass.
- Durable edge cases were promoted into the permanent portability suite.
- Temporary eval files were removed before closeout.

## Required Validation

Run:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/upstream/bootstrap-llm-workbench-repo/smoke-test.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/start-chat-session/smoke-test.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/record-chat-commit/smoke-test.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/command/package-scripts/smoke-test.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/command/dispatcher/smoke-test.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh
bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all
bash scripts/01.harness/check-governed-script-command-drift.sh
```

Also run:

```bash
bash scripts/01.harness/check-deterministic-process-drift.sh --paths <changed-governed-files>
bash -n <changed-shell-scripts-and-templates>
git diff --check
```

## Public Export Review

When export/install behavior changed:

- materialize the generated public workbench
- inspect the generated public top-level tree
- verify source-only trees are absent
- install into a blank repo
- install into an existing repo
- run `check-headers --all` in the generated public repo
- run `check-headers --all` in an installed target

## Closeout

Report:

- changed files summary
- exact validation commands run
- skipped checks and why
- whether temporary eval files remain
- whether changes are committed or still uncommitted
