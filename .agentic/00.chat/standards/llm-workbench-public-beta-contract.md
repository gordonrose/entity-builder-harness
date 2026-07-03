<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.standards.llm-workbench-public-beta-contract
  version: 1
  status: active
  layer: 00.chat
  domain: portability
  disciplines:
  - agentic
  kind: standard
  purpose: Define the public-beta contract for standalone provider-neutral llm-workbench behavior.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.checklists.llm-workbench-public-beta
    path: .agentic/00.chat/checklists/llm-workbench-public-beta.md
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - id: chat.workflows.chat-upstream-reusable-lesson
    path: .agentic/00.chat/workflows/chat-upstream-reusable-lesson.md
-->
# llm-workbench Public-Beta Contract

## Definition Of Done

`llm-workbench` is a standalone, provider-neutral Git/Bash/npm chat harness for
blank or existing repos, with safe install/uninstall, assistant adapters, JSON
startup packets, and portable transcript metadata across common CLI and
code-assistant workflows.

Do not claim it works perfectly with every LLM assistant or every editor setup.
No repository can guarantee that every assistant will read and obey instruction
files.

## Core Invariants

### No Durable Chat Classification

- Do not reintroduce durable whole-chat `layer`, `mode`, or `workflow`
  classification metadata.
- Chat startup may record `chat_lifecycle_workflow` and context-packet
  continuity metadata.
- Prompt-level routing is local and optional: use the current user request,
  repo assistant instructions, and any repo-provided context router if one
  exists.
- Base chat startup must not require RAG/rulebook, classifier scripts, or
  source-specific routers.

### Public Export Is Standalone

Generated public exports and installed target repos must not contain source-only
wrapper trees, duplicate generated trees, upstream harness-maintenance trees, or
retired chat-classification scripts. The exact excluded paths are enforced by
the portability suite and summarized in the source-side acceptance matrix.

Public `.agentic` surfaces must not reference missing exported paths.
`check-headers --all` must pass in both the generated public workbench repo and
an installed target repo. When a public-exported directory is removed, remove or
sanitize any `used_by.path` references to it.

### No Source-Specific Rulebook Or Codex Defaults

- Generic chat startup, commit, docs, and assistant surfaces must not require
  mandatory RAG/rulebook runtime behavior.
- Do not hard-code `.agentic/02.rag-rulebook` or `scripts/02.rag-rulebook`
  into generic chat commit gates.
- Repos that need extra gates must use neutral optional extension hooks.
- Codex support may exist as an adapter, but Codex must not be the default
  transcript, startup, metrics, docs, or assistant assumption.

### Provider-Neutral Transcript And Cost Metrics

Core transcript metadata is neutral:

- `transcript_provider`
- `transcript_path`
- `transcript_bytes`
- `transcript_token_estimate`
- `transcript_source`

Codex transcript discovery is optional adapter behavior only. Missing transcript
metrics must not block portable/default operation unless strict mode is
explicitly enabled.

Chat pricing belongs to the chat metrics surface:

- `scripts/00.chat/metrics/data/chat-pricing.json`
- `scripts/00.chat/metrics/data/chat-pricing.schema.json`

Bundled pricing data is a local best-effort profile store, not a universal
source of truth. The default bundled profile must be provider-neutral and
unpriced unless a pricing profile is explicitly selected. Keep
`CHAT_COST_PRICING_FILE` and `CHAT_COST_PROFILE` as overrides.

### Safe Blank And Existing Repo Installs

`scripts/install.sh` must support `--dry-run`, `--apply`, and `--init-commit`.
Dry runs must not mutate the target repo. Apply mode must not overwrite user
files silently.

Existing `package.json` files are merged only for workbench-owned `chat:*`
scripts. Assistant instruction files are patched with managed blocks, not
overwritten. Install writes a manifest of created files, package-script changes,
and managed blocks. Uninstall removes only manifest-owned material.

`--init-commit` is only for repos with no existing `HEAD`. It stages only
manifest-owned install paths, never `git add -A`. In unborn repos with unrelated
pre-existing files, the install commit leaves unrelated files uncommitted.

### Thin Assistant Adapters

Public assistant surfaces may include:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.cursor/rules/llm-workbench.mdc`
- `LLM_WORKBENCH.md`

Adapters point to the same canonical chat lifecycle workflow. They do not
duplicate detailed policy or make provider-specific assumptions. They preserve
this rule:

```txt
For prompt-level routing, use the current user request, this repo's assistant instructions, and any repo-provided context router if one exists. Do not assign the whole chat a durable layer, mode, or workflow.
```

### CLI And Code-Assistant Robustness

- `chat:new` supports structured JSON output for code assistants:
  `npm run chat:new -- --json "task summary"`.
- Clipboard handoff is optional/fallback only.
- Do not rely on executable bits surviving zip extraction or Windows
  filesystems where avoidable.
- Dispatchers invoke shell scripts with Bash when appropriate instead of
  failing only because a script is not executable.
- Bash, Git, and Node assumptions are documented and tested across Linux,
  macOS, Windows, and WSL paths.

## Validation Contract

Before calling related work complete, run the permanent portability suite and
add tests for any newly discovered edge case:

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
bash scripts/01.harness/check-deterministic-process-drift.sh --paths <changed-governed-files>
bash -n <changed-shell-scripts-and-templates>
git diff --check
```

The portability suite must cover Codex, Claude-style, Mistral/manual, Copilot,
Cursor, and generic CLI assistant surfaces; Linux, macOS, Windows, and WSL
signals; blank unborn repos; existing repos with `package.json` and
`AGENTS.md`; conflicting package scripts; missing transcript providers; manual
transcript metrics; explicit pricing overrides; missing clipboard utilities;
JSON startup handoff; public export self-consistency; and installed target
self-consistency.

## Temporary Eval Loop

For each feature or patch:

1. Write a temporary eval or failing smoke case proving the desired behavior.
2. Implement the smallest change that should make the eval pass.
3. Run the eval.
4. Refine until it passes.
5. Promote durable edge cases into the permanent portability suite.
6. Remove temporary eval files before finishing.

## Public Export Boundary

When touching bootstrap/export logic, materialize the generated public
workbench, inspect its top-level tree, install it into blank and existing repos,
and run `check-headers --all` in both the generated public repo and installed
target.

Canonical public paths are:

- `.agentic/00.chat`
- `.agentic/shared`
- `docs`
- `scripts/00.chat`
- `scripts/01.harness`, only when required for portable checks and not
  dependent on an upstream harness-maintenance tree
- `package.json`
- `README.md`
- assistant adapter files
- install/uninstall scripts

## Documentation

When behavior changes, update public docs and templates: README, install docs,
workflow docs, assistant adapter templates, relevant script READMEs, and the
generated GitHub Actions workflow template when affected. Docs must match
behavior and avoid overclaiming.

## Closeout Evidence

Before reporting success, provide:

- changed files summary
- exact validation commands run
- skipped checks and why
- whether temporary eval files remain
- whether changes are committed or still uncommitted
