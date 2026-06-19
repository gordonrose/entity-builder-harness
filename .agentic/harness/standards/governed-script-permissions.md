<!-- agentic-artifact:
owner: harness
kind: standard
purpose: Define persistent tool permission policy for governed repository scripts.
domain: governance
portability: llm-workbench-required
used_by:
  - scripts/shared/harness/run-governed-script.sh
  - scripts/shared/harness/smoke-test-governed-script-runner.sh
-->

# Governed Script Permissions

## Purpose

Use this standard when granting agent tools persistent permission to run
repository scripts without repeated manual approval prompts.

The goal is to reduce approval friction without turning a narrow governed
script path into broad shell access.

## Core Rule

Persistent vendor permission must target the governed script runner, not raw
`bash`.

Agents may be configured to run:

```bash
bash scripts/shared/harness/run-governed-script.sh <script> [args...]
```

Do not grant persistent approval for unrestricted shell commands such as
`bash`, `bash -c`, `bash -lc`, `sh`, `zsh`, or broad command prefixes that can
hide unrelated behavior.

## Ownership

- This standard owns the policy and approval classes.
- `scripts/shared/harness/run-governed-script.sh` owns deterministic
  enforcement.
- Vendor configuration owns only vendor-specific permission mechanics.
- Workflows still own when a class of action is approved for the current chat.

Vendor files must not duplicate this standard. They should point their tool's
permission system at the governed runner and leave policy meaning here.

## Approval Classes

### Always Runnable Checks

These scripts may run through the governed runner without a separate chat
approval when the current workflow allows inspection or validation.

Examples include deterministic read-only checks, classifiers, and reporting
helpers that do not stage, commit, push, delete, rewrite, clean, overwrite, or
otherwise mutate repository, branch, runtime, cloud, or data state.

### Approval-Sensitive Governed Actions

These scripts may run through the governed runner only after the current chat
contains explicit approval for the action class.

Examples include task staging, task commits, governed branch refresh,
promotion, cleanup, or any helper that mutates Git metadata or repository
files.

After the user approves the action class, agents should not ask for a second
confirmation for each downstream governed script unless the workflow, script,
or gate reaches a new stop condition.

## Agent-Facing Command Examples

Agent-facing harness artifacts must teach the command form agents are expected
to execute.

When a workflow, checklist, standard, prompt, template, or command handoff shows
an approval-sensitive governed script as an executable command, route it through
the governed runner:

```bash
bash scripts/shared/harness/run-governed-script.sh --approved-action <script> [args...]
```

`--approved-action` does not grant approval by itself. It only records that the
current workflow and current chat already contain explicit approval for that
action class.

Direct script calls are allowed inside implementation scripts, smoke tests,
fixture setup, and historical or explanatory prose when they are not active
instructions to an agent.

For repository bootstrap actions that would otherwise require broad persistent
approval such as `git clone`, prefer a narrowly scoped governed helper and route
it through the runner. For the reusable lesson upstream workbench, use:

```bash
bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh
```

### Never Persistent-Auto-Approved

These actions must not be granted persistent vendor auto-approval through the
governed runner:

- pushing to remotes
- deleting branches or worktrees outside a deterministic approved cleanup path
- rewriting history
- discarding, restoring, resetting, or overwriting work
- resolving conflicts by choosing a side or dropping content
- broad cleanup commands
- direct cloud, deployment, database, or data mutations
- commands that invoke arbitrary shell strings

If a future workflow needs one of these actions, govern it directly with a
specific workflow, script, gate, and approval boundary.

## Vendor Permission Surfaces

Use live vendor configuration only when the vendor reads and enforces it.

- Codex: project `.codex/rules/*.rules` may grant the runner prefix when the
  project `.codex` layer is trusted.
- Claude Code: project `.claude/settings.json` may grant the runner through a
  `permissions.allow` Bash rule.
- Mistral Vibe Code: project `.vibe/config.toml` may grant the runner through
  bash tool permission settings when the folder is trusted.

Do not create vendor markdown adapter files when they would only restate this
standard.

## Source Review

Vendor-specific claims in this standard were checked on 2026-06-19 against:

- OpenAI Codex manual sections for project config, hooks, permissions, and
  rules.
- Anthropic Claude Code docs for settings, permission rules, and hooks.
- Mistral Vibe Code docs for project config, trusted folders, and bash tool
  permissions.

Refresh these claims before changing vendor-derived requirements.
